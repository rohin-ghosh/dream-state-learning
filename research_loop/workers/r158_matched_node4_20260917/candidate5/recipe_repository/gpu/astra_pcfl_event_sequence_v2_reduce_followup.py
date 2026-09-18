"""Offline final EVENT-sequence-v2 reduction; never launches, repairs or promotes.

Non-material evidence-validation repair. The raw state/custody checks are copied
from acquisition.state_result, with explicit measured-A200 descendant validation.
No parent check is disabled or monkeypatched. File pins refer to preserved source
paths, not the reducer's current checkout. NATIVE remains a recorded evidence
kind, not an independent native attestation. CLI accepts a pinned request with
exactly three {manifest, completed} followups (seeds 0/1/2, one shared bank).
The request has schema SCHEMA + "/request" and a "followups" list; each entry
contains two closed {"path": absolute_path, "sha256": file_hash} pins.
Run: python3 -m gpu.astra_pcfl_event_sequence_v2_reduce_followup
     --request /absolute/request.json --request-sha256 FILE_SHA256
"""

import argparse
import ast
from dataclasses import asdict
import json
from pathlib import Path

from gpu import astra_pcfl_event_sequence_v2_acquisition as acquisition
from gpu import astra_pcfl_event_sequence_v2_followup as operator
from gpu import astra_pcfl_event_sequence_fit as fit_helpers

sequence, reader = acquisition.sequence, acquisition.reader
prefix, native = acquisition.prefix, acquisition.native
require, same, digest = acquisition.require, acquisition.same, acquisition.digest
read, sealed, pinned = acquisition.read, acquisition.sealed, acquisition.pinned
fields, inventory, file_hash = acquisition.fields, acquisition.inventory, acquisition.file_hash
release = acquisition.release
OUTER_SCHEMA, READOUT_SCHEMA, FIT_SCHEMA = acquisition.OUTER_SCHEMA, acquisition.READOUT_SCHEMA, acquisition.FIT_SCHEMA
SCHEMA = "pcfl.event_sequence.v2.reduce_followup.v1"
IDENTITY = ("material", "model_path", "model_binding", "base_state_receipt", "learner_seed", "gpu_uuid", "environment")
REPAIR_SCOPE = "warm_receipt_and_predecessor_validation_only"
PROSPECTIVE_SCOPE = "warm_receipt_and_readonly_predecessor_split"
COLLECTOR_ERRORS = [{"error": "warm start: output must be fresh", "phase": "stage_evidence", "type": "ValueError"}]
PREWORKER_READOUT_ERRORS = [
    {"error": "resource not released/matched", "phase": "pre_cvd", "type": "ValueError"},
    {"error": "preflight failed", "phase": "controller", "type": "ActorError"},
]
MAX_PHYSICAL_WORK = dict(fits=20, updates=6400, presentations=25600, readout_calls=288)


def file_pin(path):
    return {"path": str(path), "sha256": file_hash(path)}


def verify_pin(pin):
    require(type(pin) is dict and set(pin) == {"path", "sha256"}, "closed file pin required")
    require(type(pin["path"]) is str, "file path required")
    path = Path(pin["path"])
    require(path.is_absolute() and path.resolve() == path and path.is_file(), "absolute unaliased file pin required")
    native.sha(pin["sha256"])
    same(file_hash(path), pin["sha256"], "bound file/source hash differs")


def provenance(value):
    if isinstance(value, dict):
        if set(value) == {"path", "sha256"}:
            verify_pin(value)
        else:
            for child in value.values():
                provenance(child)
    elif isinstance(value, list):
        for child in value:
            provenance(child)


def original_sources(sources, repair):
    for path, checksum in sources.items():
        verify_pin({"path": path, "sha256": checksum})
    result = dict(sources)
    if repair is not None:
        outer_key = "outer_replacement" if repair["scope"] == PROSPECTIVE_SCOPE else "outer_relocated"
        for original, replacement in ((repair["original"], repair["replacement"]),
                                      (repair["outer_original"], repair[outer_key])):
            if original == repair["original"] or replacement["path"] in result:
                require(original["path"] not in result, "ambiguous repaired runtime source")
                same(result.pop(replacement["path"]), replacement["sha256"], "repaired runtime source hash")
                result[original["path"]] = original["sha256"]
    return result


def repair_scope(original, replacement, scope):
    if scope == PROSPECTIVE_SCOPE:
        operator.validate_repair(original, replacement)
        return
    require(scope in ("validate_warm_tensors_only", REPAIR_SCOPE), "known validation-only repair scope")
    allowed = {"validate_warm_tensors"} | ({"validate_predecessor"} if scope == REPAIR_SCOPE else set())
    trees = [ast.parse(Path(path).read_bytes()) for path in (original, replacement)]
    for tree in trees:
        functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in allowed]
        require(sorted(node.name for node in functions) == sorted(allowed), "exact scoped validator functions required")
        for function in functions:
            function.body = [ast.Pass()]
    same(ast.dump(trees[0]), ast.dump(trees[1]), "repair changed code outside declared validators")


def runtime_cold(plan, cold):
    repair = plan.get("repair")
    runtime = pinned(plan["runtime_c0_inputs"]) if "runtime_c0_inputs" in plan else cold
    if repair is not None:
        require("runtime_c0_inputs" in plan, "repaired runtime C0 pin required")
        provenance(repair)
        same(pinned(repair["receipt"]), {key: value for key, value in repair.items() if key != "receipt"}, "repair receipt drift")
        fields(repair, {"schema": "pcfl.event_sequence.v2.warm_repair.v1",
            "source_root": plan["source_root"], "original_root": str(Path(repair["original"]["path"]).parents[1])}, "repair scope/root")
        outer_key = "outer_replacement" if repair["scope"] == PROSPECTIVE_SCOPE else "outer_relocated"
        for key, name, root in (("original", "astra_pcfl_event_sequence_v2_fit.py", repair["original_root"]),
                               ("replacement", "astra_pcfl_event_sequence_v2_fit.py", repair["source_root"]),
                               ("outer_original", "astra_pcfl_event_sequence_v2_outer.py", repair["original_root"]),
                               (outer_key, "astra_pcfl_event_sequence_v2_outer.py", repair["source_root"])):
            same(repair[key]["path"], str(Path(root) / "gpu" / name), "repair source path")
        repair_scope(repair["original"]["path"], repair["replacement"]["path"], repair["scope"])
        if repair["scope"] == PROSPECTIVE_SCOPE:
            operator.validate_repair(repair["outer_original"]["path"], repair[outer_key]["path"], outer=True)
        else:
            same(repair["outer_original"]["sha256"], repair[outer_key]["sha256"], "relocated outer must be byte-identical")
    same({**runtime, "source_files": original_sources(runtime["source_files"], repair)}, cold, "only approved runtime C0 source delta")
    return runtime


def runtime_allocation(plan):
    original_pin = plan["entry"]["allocation"]
    repair = plan.get("repair")
    if repair is None or repair["scope"] != PROSPECTIVE_SCOPE:
        runtime_pin = plan.get("runtime_allocation", original_pin)
        same(pinned(runtime_pin), pinned(original_pin), "unexpected runtime allocation delta")
        return runtime_pin
    runtime_pin = plan["runtime_allocation"]
    original, runtime = pinned(original_pin), pinned(runtime_pin)
    same({**runtime, "outer_sha256": original["outer_sha256"]}, original, "runtime allocation may change only outer source")
    same(runtime["outer_sha256"], repair["outer_replacement"]["sha256"], "runtime allocation patched outer binding")
    return runtime_pin


def prior_failure_evidence(plan, *, expected_kind="NATIVE", seen=()):
    require("manual_continuation" not in plan, "terminal no-resume: manual continuation is inadmissible")
    zero_work = dict(fits=0, updates=0, presentations=0, readout_calls=0)
    pin = plan.get("prior_failure")
    if pin is None:
        same(plan.get("prior_failed_work", zero_work), zero_work, "failed work needs bound failure evidence")
        return None
    require(pin["path"] not in seen and len(seen) < 16, "cyclic or unbounded prior failure chain")
    stopped = pinned(pin)
    root = Path(pin["path"]).parent
    same(pin["path"], str(root / "stopped.json"), "prior failure filename")
    manifest_pins = [binding for binding in plan["pins"] if binding["path"] == str(root / "manifest.json")]
    require(bool(manifest_pins) and all(binding == manifest_pins[0] for binding in manifest_pins)
            and pin in plan["pins"], "bound prior failure and manifest required")
    previous = pinned(manifest_pins[0])
    fields(previous, {name: plan[name] for name in ("entry", "seed", "originals")}, "prior failure ancestry")
    same(previous["root"], str(root), "prior failure manifest root")
    readout_failure = stopped["stage"] == "readout"
    fields(stopped, {"status": "STOPPED", "phase": "B200_NEW_DOSE", "stage": "readout" if readout_failure else "fit"},
           "only diagnosed first-fit or preworker-reader failure")
    require(len(stopped["results"]) == (2 if readout_failure else 1), "prior failure may have executed later stages")
    collection_pin = stopped["results"][0]["collection"]
    require(collection_pin in plan["pins"], "bound prior collection required")
    same(collection_pin["path"], str(root / "runs/B200_NEW_DOSE_fit_outer/collection.json"), "failed stage path")
    collection = sealed(pinned(collection_pin))
    fields(collection, {"schema": OUTER_SCHEMA + "/collection", "phase": "B200_NEW_DOSE", "status": "COMPLETED" if readout_failure else "FAILED",
                        "retries": 0}, "failed first-stage collection required")
    failed_root = Path(collection_pin["path"]).parent
    observed = inventory(failed_root)
    same({name: value for name, value in observed.items() if name != "collection.json"}, collection["files"], "failed attempt inventory")
    preworker = collection["worker_identity"] is None
    work, partial, failed_readout = zero_work, None, None
    if readout_failure:
        prior_inventory = inventory(root)
        same(plan["seed"], 0, "readout-preworker failure is seed0 attempt5 only")
        require(plan.get("prior_failure_kind", "readout-preworker") == "readout-preworker", "explicit readout-preworker failure kind")
        require("manual_continuation" not in previous and not (root / "completed.json").exists(), "terminal stopped controller required")
        fields(stopped, {"no_automatic_retry": True, "error": "failed/unreleased stage; no retry"}, "terminal readout stop reason")
        fields(previous, {name: plan[name] for name in ("source_root", "phases", "counts", "gpu")}, "excluded attempt runtime/topology")
        same(previous.get("repair"), plan.get("repair"), "excluded attempt repair identity")
        same(sorted(path.name for path in (root / "runs").iterdir()),
             ["B200_NEW_DOSE_fit_outer", "B200_NEW_DOSE_readout_outer"], "excluded attempt has later stage artifacts")
        same(read(root / "started.json")["manifest"], manifest_pins[0], "excluded attempt started manifest")
        fit_row, read_row = stopped["results"]
        same(fit_row, {"phase": "B200_NEW_DOSE", "stage": "fit", "inputs": previous["fit_inputs"][0], "collection": collection_pin},
             "excluded completed fit row")
        require(set(read_row) == {"phase", "stage", "inputs", "collection"}, "closed excluded reader row")
        fields(read_row, {"phase": "B200_NEW_DOSE", "stage": "readout"}, "excluded reader row identity")
        same(read_row["inputs"]["path"], str(root / "inputs/B200_NEW_DOSE_readout_inputs.json"), "excluded reader input path")
        same(read_row["collection"]["path"], str(root / "runs/B200_NEW_DOSE_readout_outer/collection.json"), "excluded reader path")
        require(read_row["collection"] in plan["pins"], "bound excluded reader required")
        inputs = pinned(fit_row["inputs"])
        same(inputs["acquisition_receipt"], previous["acquisition_request"], "excluded fit acquisition pin")
        same(pinned(previous["acquisition_request"]), pinned(plan["acquisition_request"]), "excluded acquisition collections")
        same({**inputs, "acquisition_receipt": plan["acquisition_request"]}, pinned(plan["fit_inputs"][0]), "excluded fit input/source identity")
        material = pinned(plan["entry"]["material"])
        acquired = acquisition.validate(previous["acquisition_request"], material, inputs, expected_kind=expected_kind)
        same(acquired, sealed(pinned(previous["acquisition_receipt"])), "excluded fit raw acquisition receipt")
        require(acquired["observed_gate"] is True, "excluded fit requires raw acquisition pass")
        allocation_pin = previous.get("runtime_allocation", previous["entry"]["allocation"])
        same(pinned(allocation_pin), pinned(plan.get("runtime_allocation", plan["entry"]["allocation"])), "excluded allocation identity")
        fit = fit_result(collection_pin, "B200_NEW_DOSE", fit_row["inputs"], allocation_pin,
                         material, expected_kind, acquired["a200_fit_receipt"])
        same(pinned(fit["receipt"])["acquisition_validation"], acquired, "excluded completed fit acquisition validation")
        cold = pinned(previous["runtime_c0_inputs"])
        same(cold, pinned(plan["runtime_c0_inputs"]), "excluded C0/source identity")
        failed_readout = preworker_readout_evidence(read_row["collection"], read_row["inputs"], allocation_pin,
                                                   {**cold, "fit_receipt": fit["receipt"]})
        require(collection["elapsed_seconds"] + failed_readout["elapsed_seconds"] <= stopped["elapsed_seconds"],
                "excluded attempt elapsed must include fit and failed reader")
        work = dict(fits=1, updates=200, presentations=800, readout_calls=0)
        partial = {"failure_kind": "readout-preworker", "collection_status": "COMPLETED", "worker_status": "COMPLETE",
                   "checkpoint_eligible": False, "readout_eligible": False, "excluded_from_primary": True,
                   "exclusion_reason": "terminal_controller_no_resume", "excluded_completed_fit": fit}
        provenance(previous)
    elif preworker:
        require(previous.get("prior_failure") is None, "preworker must terminate failure ancestry")
        fields(collection, {"returncode": None, "stage_inventory": {}}, "prior attempt may have executed a worker")
        require(not any(Path(name).name in ("worker_start.json", "worker_exit.json") or name.startswith(("fit/", "readout/"))
                        for name in observed), "prior attempt has worker evidence")
        same(previous["source_root"], plan["source_root"], "preworker failure source ancestry")
    else:
        require(collection["returncode"] in (0, 1) and collection["gpu_released"] is True,
                "prior attempt may have executed a worker without diagnosed release")
        require(previous.get("repair") is not None and plan.get("repair") is not None, "failed warm repair ancestry required")
        same(previous["repair"]["original"], plan["repair"]["original"], "failed warm repair original source")
        stage = failed_root / "fit"
        collector_failure = collection["returncode"] == 0
        require(not (failed_root / "readout").exists(), "failed attempt must have no readout")
        train_pin = file_pin(stage / "checkpoint/train_manifest.json")
        if collector_failure:
            same(plan["seed"], 0, "collector failure is seed0 attempt4 only")
            same(collection["errors"], COLLECTOR_ERRORS, "only diagnosed collector freshness failure supported")
            fields(collection, {"full_contract_released": False, "automatic_promotion": False}, "failed collector cannot promote")
            same(read(failed_root / "failure.json"), {"errors": COLLECTOR_ERRORS}, "collector failure record")
            require(not (stage / "failure.json").exists(), "collector failure cannot conceal failed worker")
            same(collection["completed_sha256"], None, "failed outer never qualified worker")
            same(observed["fit_completed.json"], observed["fit/completed.json"], "failed collector worker snapshot")
            for name in ("worker_release", "post_queue", "post_gpu", "post_cvd"):
                same(read(failed_root / (name + ".json"))["value"], collection["observations"][name], "failed collector raw release observation")
            fields(collection["observations"]["post_queue"], {"matched": True}, "failed collector queue release")
            fields(collection["observations"]["post_gpu"], {"empty": True}, "failed collector GPU release")
            fields(collection["observations"]["post_cvd"], {"clear": True, "owners": [], "unresolved": []}, "failed collector CVD release")
            failure_pin = file_pin(failed_root / "failure.json")
        else:
            require(not (stage / "completed.json").exists(), "failed worker checkpoint is ineligible")
            failure_pin = file_pin(stage / "failure.json")
            require(failure_pin in plan["pins"] and train_pin in plan["pins"], "bound failed fit and training manifest required")
            same(pinned(failure_pin), {"kind": expected_kind, "message": "full parent tensor coverage differs",
                "partial_checkpoint_not_eligible": True, "phase": "B200_NEW_DOSE", "status": "FAILED", "type": "ActorError"},
                "only diagnosed warm-prefix validation failure supported")
        same(inventory(stage), collection["stage_inventory"], "failed fit stage inventory")
        fields(read(failed_root / "worker_exit.json"), {"identity": collection["worker_identity"], "returncode": collection["returncode"]}, "failed worker exit")
        fields(collection["observations"]["worker_release"], {"identity": collection["worker_identity"],
               "owned_group_released": True}, "failed worker release")
        inputs = pinned(collection["inputs"])
        same(collection["inputs"], previous["fit_inputs"][0], "failed planned fit input")
        same(read(failed_root / "inputs.input.json"), inputs, "failed fit input snapshot")
        outer_identity(collection, inputs, previous.get("runtime_allocation", plan["entry"]["allocation"]))
        if collector_failure:
            same(collection["observations"]["post_gpu"]["gpu_uuid"], inputs["gpu_uuid"], "failed collector GPU identity")
        expected_inputs = pinned(plan["entry"]["fit_inputs"])
        fields(inputs, {name: expected_inputs[name] for name in IDENTITY}, "failed fit identity")
        parent_pin = pinned(previous["acquisition_receipt"])["a200_fit_receipt"]
        same(inputs["predecessor"], parent_pin, "failed fit measured parent")
        material = pinned(plan["entry"]["material"])
        selected = material["phases"]["B200_NEW_DOSE"]
        manifest = pinned(train_pin)
        config = sequence.training_config("B200_NEW_DOSE", inputs["model_path"], learner_seed=plan["seed"], device=manifest["config"]["device"])
        fit_helpers._completion(manifest, config, selected, file_hash(stage / "corpus.json"))
        same(read(stage / "corpus.json"), selected["items"], "failed fit registered corpus")
        same(manifest["warm_start"]["parent_path"], pinned(parent_pin)["checkpoint"], "failed fit parent checkpoint")
        work = dict(fits=1, updates=200, presentations=800, readout_calls=0)
        partial = {"failure": failure_pin, "train_manifest": train_pin, "checkpoint_eligible": False,
                   "checkpoint_inventory": inventory(stage / "checkpoint"), "collection_status": "FAILED",
                   "failure_kind": "collector-freshness-validation" if collector_failure else "warm-prefix-validation"}
        if collector_failure:
            worker_pin = file_pin(stage / "completed.json")
            worker = check_fit(worker_pin, "B200_NEW_DOSE", material, inputs, expected_kind, parent_pin)
            same(worker["inputs"], collection["inputs"], "failed collector completed worker input")
            partial["completed_worker"] = worker_pin
            partial["worker_status"] = worker["status"]
            partial["readout_eligible"] = False
    for value in (stopped["elapsed_seconds"], collection["elapsed_seconds"]):
        native.number(value)
    require(0 <= collection["elapsed_seconds"] <= stopped["elapsed_seconds"] <= 7200, "invalid prior failure cost")
    earlier = prior_failure_evidence(previous, expected_kind=expected_kind, seen=(*seen, pin["path"]))
    if not preworker:
        require(earlier is not None, "missing failed-attempt ancestry")
        if readout_failure:
            require(not earlier["recorded_preworker_only"] and earlier["partial_fit"]["failure_kind"] == "collector-freshness-validation",
                    "readout-preworker attempt must follow diagnosed collector failure")
        elif collector_failure:
            require(not earlier["recorded_preworker_only"] and earlier["partial_fit"]["failure_kind"] == "warm-prefix-validation",
                    "collector attempt must follow diagnosed warm-prefix failure")
        else:
            require(earlier["recorded_preworker_only"], "warm-prefix attempt must follow preworker failure")
    earlier_seconds = 0 if earlier is None else earlier["elapsed_seconds"]
    original_seconds = sum(pinned(original)["elapsed_seconds"] for original in plan["originals"])
    same(previous["initial_outer_seconds"], original_seconds + earlier_seconds, "earlier failed time cannot be erased")
    cumulative_work = {key: work[key] + (0 if earlier is None else earlier["cumulative_failed_work"][key]) for key in zero_work}
    same(plan.get("prior_failed_work", zero_work), cumulative_work, "recorded failed work differs from artifacts")
    if readout_failure:
        same(inventory(root), prior_inventory, "excluded attempt changed while reducing")
    return {"stopped": pin, "manifest": manifest_pins[0], "collection": collection_pin,
            "attempt_elapsed_seconds": stopped["elapsed_seconds"], "elapsed_seconds": stopped["elapsed_seconds"] + earlier_seconds,
            "recorded_preworker_only": preworker, "failed_work": work, "cumulative_failed_work": cumulative_work,
            "partial_fit": partial, "failed_readout": failed_readout, "earlier_failure": earlier}


def check_fit(pin, phase, material, expected_inputs, kind, measured_parent=None):
    receipt = sealed(pinned(pin))
    root, spec, selected = Path(pin["path"]).parent, material["spec"], material["phases"][phase]
    require(Path(pin["path"]).name == "completed.json", "fit completion filename")
    parent_phase, updates = sequence.PHASES[phase]
    fields(receipt, {"schema": FIT_SCHEMA + "/completed", "status": "COMPLETE", "kind": kind, "phase": phase,
        "learner_seed": spec["learner_seed"], "updates": updates, "material_sha256": expected_inputs["material"]["sha256"],
        "spec_sha256": spec["sha256"], "export_sha256": material["sha256"], "items_sha256": selected["items_sha256"],
        "encoding_sha256": selected["encoding_sha256"], "import_sha256": spec["import_sha256"],
        "base_unchanged": True, "nonfinite_batches": 0, "model_binding": expected_inputs["model_binding"],
        "base_state_receipt": expected_inputs["base_state_receipt"], "parent_phase": parent_phase,
        "gpu_released": False, "outer_release_required": True, "automatic_promotion": False,
        "full_contract_released": False, "original_status": "FORMATION_FAILED"}, "matching fit completion")
    before = inventory(root)
    require(not any(Path(name).name in ("failure.json", "collection_failure.json") for name in before), "failed fit")
    same({name: entry["sha256"] for name, entry in before.items() if name != "completed.json"}, receipt["files"], "fit file drift")
    same(receipt["checkpoint"], str(root / "checkpoint"), "fit checkpoint path")
    captured = pinned(receipt["inputs"])
    same(captured["schema"], FIT_SCHEMA + "/inputs", "fit inputs schema")
    fields(captured, {name: expected_inputs[name] for name in IDENTITY}, "fit/readout identity")
    provenance(captured)
    for path, checksum in spec["sources"].items():
        same(captured["source_files"][path], checksum, "material/fit source identity")
    config = sequence.training_config(phase, captured["model_path"], learner_seed=spec["learner_seed"],
                                      device=read(root / "config.json")["device"])
    same(read(root / "config.json"), asdict(config), "saved phase config")
    manifest = read(root / "checkpoint/train_manifest.json")
    fit_helpers._completion(manifest, config, selected, file_hash(root / "corpus.json"))
    same(read(root / "corpus.json"), selected["items"], "registered phase corpus")
    same(manifest.get("warm_start"), receipt["warm_start"], "warm initialization receipt differs")
    if parent_phase is None:
        require(receipt["predecessor"] is None and captured.get("predecessor") is None
                and receipt["warm_start"] is None, "cold phase requires clean C0 parent")
    else:
        require(measured_parent is not None, "measured A200 parent required")
        same(receipt["predecessor"], measured_parent, "warm parent differs from measured A200")
        same(captured["predecessor"], measured_parent, "fit input parent differs")
        parent = check_fit(measured_parent, "A200", material, captured, kind)
        warm = receipt["warm_start"]
        fields(warm, {"parent_path": parent["checkpoint"], "initialized_loaded_state_check": True,
            "base_frozen": True, "adapter_count": 1, "parent_unchanged": True,
            "optimizer_initialization": "fresh_per_write", "optimizer_state_restored": False,
            "optimizer_initial_state_entries": 0, "optimizer_state_saved": False,
            "phase_steps": updates, "cumulative_steps": 200 + updates}, "warm parent/optimizer binding")
        parent_files = {name: entry["sha256"] for name, entry in inventory(Path(parent["checkpoint"])).items()}
        same(warm["parent_files"], parent_files, "warm parent checkpoint inventory")
        same(warm["parent_files_after"], parent_files, "warm parent changed")
        trainable = receipt["trainable_names"]
        require(bool(trainable) and all(name.endswith((".lora_A.default.weight", ".lora_B.default.weight"))
                                       for name in trainable), "LoRA-only trainability")
        def canonical_name(name):
            return name.removeprefix("base_model.model.").replace(".default.weight", ".weight")

        trainable_names = {canonical_name(name) for name in trainable}
        source_names = {canonical_name(name): name for name in warm["source_state"]}
        require(len(trainable_names) == len(trainable) and len(source_names) == len(warm["source_state"]), "ambiguous wrapper tensor names")
        same(sorted(source_names), sorted(trainable_names), "warm source tensor coverage")
        tensor_names = set(source_names.values())
        same(sorted(warm["initialized_state"]), sorted(tensor_names), "warm initialized tensor coverage")
        conversions = {}
        for name in tensor_names:
            source, initialized = warm["source_state"][name], warm["initialized_state"][name]
            native.sha(source["sha256"])
            native.sha(initialized["sha256"])
            same(source["shape"], initialized["shape"], "warm tensor shape drift")
            if source["dtype"] == initialized["dtype"]:
                same(source, initialized, "warm tensor initialization drift")
            else:
                conversions[name] = {"source": source["dtype"], "initialized": initialized["dtype"]}
        same(warm["dtype_conversions"], conversions, "warm dtype conversion coverage")
    same(inventory(root), before, "fit changed while reducing")
    return receipt


def fit_release(root, state, checksum):
    same(file_hash(root / "collection.json"), checksum, "collection FILE pin")
    collection = sealed(read(root / "collection.json"))
    fields(collection, {"schema": OUTER_SCHEMA + "/collection", "phase": state, "status": "COMPLETED",
        "errors": [], "returncode": 0, "gpu_released": True, "retries": 0, "automatic_promotion": False,
        "full_contract_released": False, "original_status": "FORMATION_FAILED"}, "outer completion/release")
    observed = inventory(root)
    same({name: value for name, value in observed.items() if name != "collection.json"}, collection["files"], "outer inventory")
    require(not any(Path(name).name in ("failure.json", "collection_failure.json") for name in observed), "failed archive")
    same(inventory(root / "fit"), collection["stage_inventory"], "fit inventory")
    same(observed["fit_completed.json"], observed["fit/completed.json"], "outer completion snapshot")
    same(observed["inputs.input.json"]["sha256"], collection["inputs"]["sha256"], "outer input FILE pin")
    same(observed["allocation.input.json"]["sha256"], collection["allocation_file_sha256"], "allocation FILE pin")
    inputs, allocation, binding = (read(root / name) for name in ("inputs.input.json", "allocation.input.json", "binding.json"))
    context = read(root / "context.json")
    fields(context, {"schema": OUTER_SCHEMA, "phase": state, "inputs": collection["inputs"],
                    "outer_source_sha256": collection["outer_source_sha256"]}, "outer context")
    identity, observations = collection["worker_identity"], collection["observations"]
    same([identity["uid"], identity["boot_id"], identity["pgid"], identity["sid"]],
         [allocation["uid"], allocation["boot_id"], identity["pid"], identity["pid"]], "owned process identity")
    same(observations["worker_wait"], 0, "worker wait")
    fields(observations["worker_release"], {"identity": identity, "owned_group_released": True}, "worker group release")
    fields(read(root / "worker_exit.json"), {"identity": identity, "pid": identity["pid"], "returncode": 0, "signal": None}, "worker exit")
    same(read(root / "worker_start.json")["identity"], identity, "worker start")
    for name, value in observations.items():
        record = read(root / (name + ".json"))
        same(record["value"], value, "outer observation join")
        require(context["entry_monotonic"] <= record["started_monotonic"] <= record["ended_monotonic"]
                <= context["entry_monotonic"] + collection["elapsed_seconds"] <= binding["deadline_monotonic"], "outer elapsed bounds")
    for when in ("pre", "post"):
        require(observations[when + "_queue"]["matched"] is True, "queue mismatch")
        fields(observations[when + "_gpu"], {"empty": True, "gpu_uuid": inputs["gpu_uuid"]}, "GPU not vacant")
        fields(observations[when + "_cvd"], {"clear": True, "owners": [], "unresolved": []}, "CVD not released")
    return collection, inputs, binding, observed


def state_result(root, state, checksum, material, material_hash, expected_kind, *, measured_parent=None):
    collection, inputs, binding, before = release(root, state, checksum)
    same(inputs["schema"], READOUT_SCHEMA + "/inputs", "v2 readout inputs required")
    pinned(collection["inputs"])
    for name in ("material", "model_binding", "base_state_receipt"):
        pinned(inputs[name])
    stage, spec = root / "readout", material["spec"]
    completed, settings = sealed(read(stage / "completed.json")), read(stage / "readout_config.json")
    same(completed["sha256"], collection["completed_sha256"], "outer/readout seal")
    fields(completed, {"schema": READOUT_SCHEMA + "/completed", "status": "COMPLETE", "kind": expected_kind, "state": state,
        "inputs": collection["inputs"], "material_sha256": material_hash, "spec_sha256": spec["sha256"], "import_sha256": spec["import_sha256"],
        "learner_seed": spec["learner_seed"], "calls": 16, "fits": 0, "updates": 0, "gpu_released": False, "outer_release_required": True,
        "full_contract_released": False, "automatic_promotion": False}, "readout completion")
    same(completed["files"], {name: entry["sha256"] for name, entry in collection["stage_inventory"].items() if name != "completed.json"}, "worker inventory")
    same(read(stage / "inputs.json"), inputs, "input copy")
    same(inputs["material"]["sha256"], material_hash, "same material file")
    for path, source_hash in spec["sources"].items():
        same(inputs["source_files"][path], source_hash, "material/worker source bytes")
    for name in ("model_path", "model_binding", "source_files", "gpu_uuid", "shutdown_binding"):
        same(settings[name], inputs[name], "settings/input join")
    fields(settings, {"schema": reader.SCHEMA, "roster": spec["roster"], "roster_sha256": spec["roster_sha256"],
        "environment": inputs["environment"]["native"], "engine": reader.ENGINE, "max_calls": 16, "max_output_tokens": 2048,
        "max_input_tokens": 14336, "deadline": binding["worker_deadline_monotonic"],
        "tokenizer_files": material["tokenizer_receipt"]["tokenizer_files"], "chat_template_sha256": material["tokenizer_receipt"]["chat_template_sha256"],
        "arm": "NO_WRITE_C0" if state == "NO_WRITE" else "AUTH_WRITE"}, "frozen reader settings")
    same(Path(settings["output_dir"]).parent.as_posix(), binding["argv"][binding["argv"].index("--output") + 1], "original output binding")
    fit_receipt = None
    same(completed["fit_receipt"], inputs.get("fit_receipt"), "fit receipt pin")
    if state == "NO_WRITE":
        require(inputs.get("fit_receipt") is None and settings["adapter"] is None
                and not any(name.startswith("adapter/") or name == "adapter_projection.json" for name in completed["files"]), "NO_WRITE must not mount fit")
    else:
        phase = sequence.READ_STATES[state]
        fit_receipt = check_fit(inputs["fit_receipt"], phase, material, inputs, expected_kind, measured_parent)
        fit_root = Path(inputs["fit_receipt"]["path"]).parent
        fit_inventory = inventory(fit_root)
        adapter_files = {name.removeprefix("checkpoint/"): entry for name, entry in fit_inventory.items()
                         if name in ("checkpoint/adapter_config.json", "checkpoint/adapter_model.safetensors", "checkpoint/README.md")}
        require({"adapter_config.json", "adapter_model.safetensors"} <= set(adapter_files), "complete safetensors adapter required")
        same(settings["adapter"], {"name": "pcfl-own-write", "id": 1, "path": str(stage / "adapter"), "files": adapter_files}, "exact phase adapter route")
        same({name.removeprefix("adapter/"): entry for name, entry in collection["stage_inventory"].items()
              if name.startswith("adapter/")}, adapter_files, "exact adapter mount inventory")
        for name, entry in settings["adapter"]["files"].items():
            same(collection["stage_inventory"]["adapter/" + name], entry, "mount copy file identity")
            same(entry["sha256"], fit_receipt["files"]["checkpoint/" + name], "original checkpoint bytes")
        same(read(stage / "adapter_projection.json"), {"kind": "BYTE_IDENTICAL_MOUNT_COPY_NO_TRAINING",
             "source_checkpoint": fit_receipt["checkpoint"], "adapter": settings["adapter"]}, "adapter projection")
    responses = [read(stage / f"response_{index:04d}.json") for index in range(16)]
    actor = stage / "actor"
    identity, load, close, custody = (read(path) for path in (actor / "identity.json", actor / "load.json", actor / "close.json", stage / "custody.json"))
    route = reader.route_identity(settings)
    same(read(actor / "config.json"), settings, "actor config")
    same([identity["pid"], identity["config_sha256"], custody["identity_sha256"]],
         [collection["worker_identity"]["pid"], digest(settings), digest(identity)], "native identity seal")
    for value in (identity, load, close, custody):
        same(value["kind"], ("NATIVE_OWN_WRITE_READOUT" if expected_kind == "NATIVE" else "INJECTED_CPU_TEST"), "native actor kind")
    for value in (completed["route"], identity["identity"]["route"], load["route"], close["route"], custody["route"]):
        same(value, route, "actual loaded route")
    same(close, read(stage / "actor_close.json"), "close copy")
    fields(close, {"calls_consumed": 16, "planned_calls": 16, "failed": False, "budget_exceeded": False, "error_type": None}, "complete reader close")
    same([close["shutdown"]["shutdown_returned"], close["shutdown"]["source"], load["shutdown"]["source"], custody["calls"]],
         [True, inputs["shutdown_binding"], inputs["shutdown_binding"], 16], "shutdown and calls")
    captures = []
    scores, recomputed, totals, generation = read(stage / "scores.json"), [], {"prompt": 0, "output": 0}, 0.0
    fields(scores, {"state": state, "denominator": 16, "pass_threshold": None}, "fixed score endpoint")
    require(len(scores["results"]) == len(list(stage.glob("response_*.json"))) == 16, "exact capture count")
    for suffix in ("raw", "response", "request", "render"):
        require(len(list(actor.glob("call_*." + suffix + ".json"))) == 16, "exact actor capture count")
    for index, (row, response) in enumerate(zip(spec["roster"], responses)):
        raw, returned, request, render = (read(actor / f"call_{index:04d}{suffix}.json") for suffix in (".raw", ".response", ".request", ".render"))
        same([raw["kind"], raw["route"], raw["raw"]["route"], response["route"], render["route"]], [("NATIVE_OWN_WRITE_READOUT" if expected_kind == "NATIVE" else "INJECTED_CPU_TEST"), route, route, route, route], "raw route")
        same([request["row"], request["request"], request["messages"], response["id"], response["request_sha256"], response["roster_sha256"]],
             [row, {"id": row["id"]}, reader.public_messages(row), row["id"], digest({"id": row["id"]}), spec["roster_sha256"]], "ordered request")
        same([returned["response"], returned["raw_hex"], returned["raw_utf8_sha256"]], [response, response["text"].encode().hex(), native.text_hash(response["text"])], "raw response bytes")
        for name in ("text", "finish_reason", "stop_reason"):
            same(raw["raw"][name], response[name], "raw/returned join")
        require(response["finish_reason"] in ("stop", "length"), "termination kind")
        same(raw["raw"]["prompt_token_ids"], render["prompt_token_ids"], "prompt token join")
        same(render["sampling"], {**native.SAMPLING, "seed": row["seed"], "max_tokens": 2048}, "frozen sampling")
        require(load["model_load_started"] <= load["ready_at"] <= raw["generation_started"] <= raw["generation_ended"] <= settings["deadline"], "cold timing")
        generation += raw["generation_ended"] - raw["generation_started"]
        for name, cap in (("prompt", 14336), ("output", 2048)):
            count = len(native.token_ids(raw["raw"][name + "_token_ids"]))
            require(response[name + "_tokens"] == count <= cap, "actual token counts")
            totals[name] += count
        record = spec["records"][index % 8]
        score = sequence.core.score_memory_response(response["text"], record["target"])
        result = {"id": row["id"], "request": row["request"], "view": row["view"], "bank": record["bank"], "record": record["index"],
            "raw": response["text"], "target_sha256": native.text_hash(record["target"]), "finish_reason": response["finish_reason"],
            "prompt_tokens": response["prompt_tokens"], "output_tokens": response["output_tokens"], "score": score,
            "strict_stop": response["finish_reason"] == "stop" and score["strict"]}
        same(scores["results"][index], result, "recorded score differs from raw recomputation")
        recomputed.append(result)
        captures.append({"id": row["id"], "raw_capture": file_pin(actor / f"call_{index:04d}.raw.json"),
                         "prompt_token_ids": raw["raw"]["prompt_token_ids"],
                         "output_token_ids": raw["raw"]["output_token_ids"],
                         "stop_reason": response["stop_reason"]})
    panels = {f"W{view}": {bank: {"denominator": 4, "ids": [row["id"] for row in recomputed if row["view"] == view and row["bank"] == bank],
        "strict_stop": [row["strict_stop"] for row in recomputed if row["view"] == view and row["bank"] == bank],
        "correct": sum(row["strict_stop"] for row in recomputed if row["view"] == view and row["bank"] == bank)} for bank in ("A", "B")} for view in (0, 8)}
    same([scores["panels"], completed["panels"], completed["tokens"], completed["truncated"]],
         [panels, panels, totals, sum(row["finish_reason"] == "length" for row in recomputed)], "recomputed totals")
    times = {"model_load": load["ready_at"] - load["model_load_started"], "generation_calls": generation, "actor_operations": close["elapsed_actor_seconds"]}
    same(custody["elapsed_seconds"], times, "custody elapsed")
    fields(completed["elapsed_seconds"], times, "readout elapsed")
    for value in completed["elapsed_seconds"].values():
        native.number(value)
        require(0 <= value <= collection["elapsed_seconds"], "cost outside outer bound")
    same(inventory(root), before, "archive changed while reducing")
    if fit_receipt is not None:
        same(inventory(fit_root), fit_inventory, "fit changed while reducing")
    return {"denominator": 16, "results": recomputed, "captures": captures,
            "strict_stop": [row["strict_stop"] for row in recomputed], "panels": panels, "tokens": totals, "truncated": completed["truncated"],
            "elapsed_seconds": {**completed["elapsed_seconds"], "outer_release_inclusive": collection["elapsed_seconds"]},
            "fit": None if fit_receipt is None else {"updates": fit_receipt["updates"], "checkpoint": fit_receipt["checkpoint"],
                "adapter_files": settings["adapter"]["files"]},
            "collection_file_sha256": checksum, "readout_sha256": completed["sha256"], "fit_receipt": inputs.get("fit_receipt")}, inputs, fit_receipt, collection


def outer_identity(collection, inputs, allocation_pin):
    allocation = pinned(allocation_pin)
    fields(collection, {"allocation_file_sha256": allocation_pin["sha256"],
                        "outer_source_sha256": allocation["outer_sha256"]}, "outer allocation/source identity")
    same(inputs["gpu_uuid"], allocation["gpu_uuid"], "outer GPU identity")
    native.number(collection["elapsed_seconds"])
    require(0 <= collection["elapsed_seconds"] <= 1800, "bounded outer elapsed required")


def fit_result(collection_pin, phase, inputs_pin, allocation_pin, material, kind, parent):
    verify_pin(collection_pin)
    root = Path(collection_pin["path"]).parent
    require(Path(collection_pin["path"]).name == "collection.json", "fit outer collection filename")
    collection, inputs, _, before = fit_release(root, phase, collection_pin["sha256"])
    same(collection["inputs"], inputs_pin, "fit outer input pin")
    same(inputs, pinned(inputs_pin), "fit outer input snapshot")
    outer_identity(collection, inputs, allocation_pin)
    receipt_pin = file_pin(root / "fit/completed.json")
    receipt = check_fit(receipt_pin, phase, material, inputs, kind, parent)
    same(receipt["inputs"], inputs_pin, "fit completion input pin")
    same(receipt["sha256"], collection["completed_sha256"], "outer/fit completion seal")
    same(receipt["files"], {name: entry["sha256"] for name, entry in collection["stage_inventory"].items()
                            if name != "completed.json"}, "outer/fit file inventory")
    for elapsed in receipt["elapsed_seconds"].values():
        native.number(elapsed)
        require(0 <= elapsed <= collection["elapsed_seconds"], "fit elapsed outside outer bound")
    same(inventory(root), before, "fit archive changed while reducing")
    return {"collection": collection_pin, "collection_status": collection["status"],
            "receipt": receipt_pin, "phase": phase,
            "updates": receipt["updates"], "presentations": material["phases"][phase]["presentations"],
            "parent_phase": receipt["parent_phase"], "predecessor": receipt["predecessor"],
            "warm_start": receipt["warm_start"], "checkpoint": receipt["checkpoint"],
            "checkpoint_inventory": inventory(Path(receipt["checkpoint"])),
            "fit_inventory": collection["stage_inventory"], "outer_inventory": collection["files"],
            "gpu_released": collection["gpu_released"], "release_observations": collection["observations"],
            "elapsed_seconds": {**receipt["elapsed_seconds"], "outer_release_inclusive": collection["elapsed_seconds"]}}


def preworker_readout_evidence(collection_pin, inputs_pin, allocation_pin, expected_inputs):
    """Account for the diagnosed failed reader only; never qualify a checkpoint."""
    provenance([collection_pin, inputs_pin, allocation_pin])
    failed = sealed(pinned(collection_pin))
    root = Path(collection_pin["path"]).parent
    observed = inventory(root)
    fields(failed, {"schema": OUTER_SCHEMA + "/collection", "stage": "readout", "state": "B200_NEW_DOSE",
        "status": "FAILED", "errors": PREWORKER_READOUT_ERRORS, "worker_identity": None, "returncode": None,
        "stage_inventory": {}, "completed_sha256": None, "gpu_released": False, "retries": 0,
        "automatic_promotion": False, "full_contract_released": False}, "excluded reader must fail only preworker CVD")
    same({name: value for name, value in observed.items() if name != "collection.json"}, failed["files"], "failed reader inventory")
    expected_files = {"context.json", "inputs.input.json", "allocation.input.json", "binding.json", "pre_queue.json",
                      "pre_gpu.json", "pre_cvd.json", "failure.json", "collection.json"}
    same(sorted(path.name for path in root.iterdir()), sorted(expected_files), "failed reader has worker or unexpected stage bytes")
    same(read(root / "failure.json"), {"errors": PREWORKER_READOUT_ERRORS}, "failed reader error record")
    same(failed["inputs"], inputs_pin, "failed reader input pin")
    inputs = pinned(inputs_pin)
    same(inputs, expected_inputs, "failed reader exact excluded checkpoint/input")
    provenance(inputs)
    for path, checksum in inputs["source_files"].items():
        verify_pin({"path": path, "sha256": checksum})
    same(read(root / "inputs.input.json"), inputs, "failed reader input snapshot")
    same(observed["inputs.input.json"]["sha256"], inputs_pin["sha256"], "failed reader input bytes")
    same(observed["allocation.input.json"]["sha256"], allocation_pin["sha256"], "failed reader allocation bytes")
    outer_identity(failed, inputs, allocation_pin)
    context, binding = read(root / "context.json"), read(root / "binding.json")
    fields(context, {"schema": OUTER_SCHEMA, "stage": "readout", "state": "B200_NEW_DOSE", "inputs": inputs_pin,
                    "outer_source_sha256": failed["outer_source_sha256"]}, "failed reader context")
    observations = failed["observations"]
    same(sorted(observations), ["pre_cvd", "pre_gpu", "pre_queue"], "failed reader has worker observations")
    for name, value in observations.items():
        record = read(root / (name + ".json"))
        same(record["value"], value, "failed reader raw observation join")
        require(context["entry_monotonic"] <= record["started_monotonic"] <= record["ended_monotonic"]
                <= context["entry_monotonic"] + failed["elapsed_seconds"] <= binding["deadline_monotonic"], "failed reader elapsed bounds")
    fields(observations["pre_queue"], {"matched": True}, "excluded reader queue identity")
    fields(observations["pre_gpu"], {"empty": True, "gpu_uuid": inputs["gpu_uuid"]}, "excluded reader GPU identity")
    cvd = observations["pre_cvd"]
    fields(cvd, {"clear": False, "owners": [], "unexpected": [], "reservation_check_status": "BLOCKED"}, "unreadable transient CVD only")
    require(len(cvd["unresolved"]) == 1, "one unreadable transient PID required")
    unresolved = cvd["unresolved"][0]
    require(type(unresolved["pid"]) is int and unresolved["pid"] > 0 and unresolved["error_type"] == "PermissionError"
            and f"/proc/{unresolved['pid']}/environ" in unresolved["error"], "unreadable transient environment required")
    same(inventory(root), observed, "failed reader changed while reducing")
    return {"collection": collection_pin, "collection_status": "FAILED", "inputs": inputs_pin, "inventory": observed,
            "readout_calls": 0, "elapsed_seconds": failed["elapsed_seconds"], "checkpoint_eligible": False, "readout_eligible": False}


def contrasts(states, control):
    result = {}
    for view in ("W0", "W8"):
        result[view] = {}
        for bank, endpoint in (("A", "retention"), ("B", "acquisition")):
            replay, comparison = states["REPLAY400"]["panels"][view][bank], states[control]["panels"][view][bank]
            same(replay["ids"], comparison["ids"], "paired record identity")
            same([replay["denominator"], comparison["denominator"]], [4, 4], "paired denominators")
            delta = [int(left) - int(right) for left, right in zip(replay["strict_stop"], comparison["strict_stop"])]
            result[view][bank] = {"endpoint": endpoint, "ids": replay["ids"], "denominator": 4,
                "replay_strict_stop": replay["strict_stop"], "control_strict_stop": comparison["strict_stop"],
                "paired_delta": delta, "correct_difference": sum(delta), "rate_difference": sum(delta) / 4}
    return result


def physical_work(failed_work):
    return {"fits": 5 + failed_work["fits"], "updates": 1800 + failed_work["updates"],
            "presentations": 7200 + failed_work["presentations"], "readout_calls": 96 + failed_work["readout_calls"]}


def _reduce_followup(manifest_pin, completed_pin, expected_kind):
    require(expected_kind in ("NATIVE", "INJECTED_CPU_TEST"), "explicit supported evidence kind")
    plan, completed = pinned(manifest_pin), pinned(completed_pin)
    require("manual_continuation" not in plan and "manual_continuation" not in completed,
            "terminal no-resume: manual continuation is inadmissible")
    require(plan.get("recovered_b200") is None and plan.get("recovery_elapsed_seconds", 0) == 0, "FAILED outer recovery is inadmissible")
    fields(plan, {"schema": operator.SCHEMA, "status": "READY", "phases": list(operator.PHASES),
                  "counts": operator.COUNTS, "automatic_promotion": False, "no_automatic_retry": True}, "fixed followup plan")
    sequence._seed(plan["seed"])
    root = Path(plan["root"])
    same(manifest_pin["path"], str(root / "manifest.json"), "operator manifest path")
    same(completed_pin["path"], str(root / "completed.json"), "operator completion path")
    before = inventory(root)
    require("stopped.json" not in before, "stopped followup cannot be reduced")
    fields(completed, {"status": "CAPTURED_NOT_PROMOTED", "automatic_promotion": False}, "followup completion")
    require(len(plan["fit_inputs"]) == 4 and len(plan["originals"]) == 3, "four fits and three initial collections required")
    require(len(completed["results"]) == 8, "all four fit/readout branches required")
    same([[result["phase"], result["stage"]] for result in completed["results"]],
         [[phase, stage] for phase in operator.PHASES for stage in ("fit", "readout")], "ordered four-branch completion")
    provenance(plan)
    provenance(completed)
    entry = plan["entry"]
    material, trained, cold = (pinned(entry[name]) for name in ("material", "fit_inputs", "c0_inputs"))
    spec = acquisition.material_check(material, expected_kind)
    fields(trained, {"material": entry["material"], "learner_seed": plan["seed"], "predecessor": None}, "initial fit identity")
    fields(cold, {name: trained[name] for name in IDENTITY}, "initial readout identity")
    runtime = runtime_cold(plan, cold)
    allocation_pin = runtime_allocation(plan)
    failure = prior_failure_evidence(plan, expected_kind=expected_kind)
    same([entry["seed"], spec["learner_seed"]], [plan["seed"]] * 2, "learner seed identity")
    same(entry["spec_sha256"], spec["sha256"], "entry spec identity")
    same([entry["gpu"], pinned(entry["allocation"])["gpu_index"]], [plan["gpu"]] * 2, "allocation GPU index")
    request = pinned(plan["acquisition_request"])
    same(request, {"schema": acquisition.SCHEMA + "/request", "no_write_collection": plan["originals"][1],
                   "a200_collection": plan["originals"][2]}, "original acquisition collections")
    acquired = acquisition.validate(plan["acquisition_request"], material, trained, expected_kind=expected_kind)
    same(acquired, sealed(pinned(plan["acquisition_receipt"])), "recorded acquisition receipt drift")
    require(acquired["observed_gate"] is True, "acquisition failed; no descendant rescue")
    measured_parent = acquired["a200_fit_receipt"]
    fits = {"A200": fit_result(plan["originals"][0], "A200", entry["fit_inputs"], entry["allocation"],
                               material, expected_kind, None)}
    same(fits["A200"]["receipt"], measured_parent, "initial fit differs from measured A200")
    states, runtime_sources = {}, {}
    initial_elapsed = fits["A200"]["elapsed_seconds"]["outer_release_inclusive"]
    all_states = [("NO_WRITE", plan["originals"][1], None), ("A200", plan["originals"][2], None)]
    for index, phase in enumerate(operator.PHASES):
        fit_row, read_row = completed["results"][2 * index:2 * index + 2]
        for row in (fit_row, read_row):
            require("recovery" not in row, "FAILED outer recovery is inadmissible")
            require(set(row) == {"phase", "stage", "inputs", "collection"}, "closed fresh stage row; no carried primary")
            same(row["collection"]["path"], str(root / f"runs/{phase}_{row['stage']}_outer/collection.json"),
                 "operator stage collection path")
        same(fit_row["inputs"], plan["fit_inputs"][index], "planned fit input pin")
        fit_inputs = pinned(fit_row["inputs"])
        fields(fit_inputs, {name: trained[name] for name in IDENTITY}, "matched descendant fit identity")
        same(fit_inputs["acquisition_receipt"], plan["acquisition_request"], "descendant acquisition binding")
        parent = None if phase == "CLEAN_CUM600" else measured_parent
        same(fit_inputs["predecessor"], parent, "planned exact warm/cold parent")
        same({**fit_inputs, "source_files": original_sources(fit_inputs["source_files"], plan.get("repair"))},
             {**trained, "predecessor": parent, "acquisition_receipt": plan["acquisition_request"]}, "only approved fit input deltas")
        if "fit" in runtime_sources:
            same(fit_inputs["source_files"], runtime_sources["fit"], "descendant fit runtime differs")
        runtime_sources["fit"] = fit_inputs["source_files"]
        fits[phase] = fit_result(fit_row["collection"], phase, fit_row["inputs"], allocation_pin,
                                 material, expected_kind, parent)
        receipt = pinned(fits[phase]["receipt"])
        same(receipt["acquisition_validation"], acquired, "fit acquisition receipt drift")
        read_inputs = pinned(read_row["inputs"])
        same(read_inputs["fit_receipt"], fits[phase]["receipt"], "readout must use exact branch fit")
        all_states.append((phase, read_row["collection"], read_row["inputs"]))
    for state, collection_pin, expected_input_pin in all_states:
        require(Path(collection_pin["path"]).name == "collection.json", "readout collection filename")
        result, captured, _, collection = state_result(Path(collection_pin["path"]).parent, state,
            collection_pin["sha256"], material, entry["material"]["sha256"], expected_kind, measured_parent=measured_parent)
        fields(captured, {name: cold[name] for name in IDENTITY}, "matched readout identity")
        fields(captured, {name: cold[name] for name in ("archive", "replay_receipt", "shutdown_binding")}, "readout provenance identity")
        outer_identity(collection, captured, entry["allocation"] if expected_input_pin is None else allocation_pin)
        if expected_input_pin is not None:
            same(collection["inputs"], expected_input_pin, "operator readout input pin")
            same(captured, {**runtime, "fit_receipt": fits[state]["receipt"]}, "runtime C0/readout exact input join")
            if "readout" in runtime_sources:
                same(captured["source_files"], runtime_sources["readout"], "descendant readout runtime differs")
            runtime_sources["readout"] = captured["source_files"]
        else:
            same(captured, {**cold, "fit_receipt": None if state == "NO_WRITE" else measured_parent}, "original readout input")
            initial_elapsed += collection["elapsed_seconds"]
        states[state] = {**result, "collection": collection_pin, "inputs": collection["inputs"],
                         "gpu_released": collection["gpu_released"], "release_observations": collection["observations"],
                         "readout_inventory": collection["stage_inventory"]}
    failure_elapsed = 0 if failure is None else failure["elapsed_seconds"]
    failed_work = dict(fits=0, updates=0, presentations=0, readout_calls=0) if failure is None else failure["cumulative_failed_work"]
    same(initial_elapsed + failure_elapsed, plan["initial_outer_seconds"], "initial and prior-failure elapsed accounting")
    same(plan["remaining_seconds"], 7200 - plan["initial_outer_seconds"], "remaining budget accounting")
    native.number(completed["elapsed_seconds"])
    require(0 <= completed["elapsed_seconds"] <= plan["remaining_seconds"], "followup elapsed budget")
    contrasts_by_control = {"REPLAY400-" + control: contrasts(states, control)
                            for control in ("B200_NEW_DOSE", "B400_FIXED_WORK")}
    provenance(plan)
    provenance(completed)
    same(inventory(root), before, "followup changed while reducing")
    return prefix.seal({"schema": SCHEMA + "/seed", "status": "VALIDATED_NOT_PROMOTED", "kind": expected_kind,
        "learner_seed": plan["seed"], "manifest": manifest_pin, "completed": completed_pin,
        "material": entry["material"], "spec_sha256": spec["sha256"], "acquisition_receipt": plan["acquisition_receipt"],
        "bank_identity": {"import_sha256": spec["import_sha256"], "records_sha256": digest(spec["records"]),
                          "roster_sha256": spec["roster_sha256"], "tokenizer_receipt": material["tokenizer_receipt"]},
        "model_identity": {name: trained[name] for name in ("model_path", "model_binding", "base_state_receipt")},
        "runtime_sources": runtime_sources, "counts": operator.COUNTS, "states": states, "fits": fits,
        "runtime_c0_inputs": plan.get("runtime_c0_inputs"), "repair": plan.get("repair"), "prior_failure": failure,
        "runtime_allocation": allocation_pin,
        "prior_failed_work": failed_work,
        "total_physical_work": physical_work(failed_work),
        "elapsed_seconds": {"initial_collections": initial_elapsed, "prior_failure": failure_elapsed,
                            "followup": completed["elapsed_seconds"],
                            "total": initial_elapsed + failure_elapsed + completed["elapsed_seconds"]},
        "paired_contrasts": contrasts_by_control,
        "phase_boundary_descriptive": {"contrast": "REPLAY400-CLEAN_CUM600", "panels": contrasts(states, "CLEAN_CUM600"),
            "interpretation": "Descriptive only: checkpoint/reload plus fresh optimizer/dropout reset versus clean cumulative training."},
        "automatic_promotion": False, "full_contract_released": False, "limits": sequence.LIMITS})


def reduce_followup(manifest_pin, completed_pin, *, expected_kind="NATIVE"):
    """Validate one complete seed, without pretending it is a three-seed final."""
    try:
        return _reduce_followup(manifest_pin, completed_pin, expected_kind)
    except (KeyError, TypeError, IndexError, OSError) as error:
        raise ValueError("missing or malformed followup evidence: " + str(error)) from error


def reduce(request_pin, *, expected_kind="NATIVE"):
    """Require all three learners and all branches; never pool independent banks."""
    request = pinned(request_pin)
    require(type(request) is dict and set(request) == {"schema", "followups"}, "closed final reduction request")
    same(request["schema"], SCHEMA + "/request", "final request schema")
    require(type(request["followups"]) is list and len(request["followups"]) == 3, "exactly three same-bank learners required")
    results = []
    for entry in request["followups"]:
        require(type(entry) is dict and set(entry) == {"manifest", "completed"}, "closed followup pins")
        results.append(reduce_followup(entry["manifest"], entry["completed"], expected_kind=expected_kind))
    results.sort(key=lambda result: result["learner_seed"])
    same([result["learner_seed"] for result in results], [0, 1, 2], "exact learner seeds 0/1/2 required")
    for result in results[1:]:
        same(result["bank_identity"], results[0]["bank_identity"], "three seeds must share the same bank")
        same(result["model_identity"], results[0]["model_identity"], "three seeds must share the same model/base")
    pooled = {}
    for label in (*results[0]["paired_contrasts"], "REPLAY400-CLEAN_CUM600"):
        panels = {}
        for view in ("W0", "W8"):
            panels[view] = {}
            for bank in ("A", "B"):
                rows = [(result["phase_boundary_descriptive"]["panels"] if label.endswith("CLEAN_CUM600")
                         else result["paired_contrasts"][label])[view][bank] for result in results]
                delta = [value for row in rows for value in row["paired_delta"]]
                panels[view][bank] = {"denominator": 12, "unique_records": 4, "learners": 3,
                    "seed_order": [0, 1, 2], "paired_delta": delta,
                    "correct_difference": sum(delta), "rate_difference": sum(delta) / 12}
        pooled[label] = {"descriptive_only": label.endswith("CLEAN_CUM600"), "panels": panels}
    same(pinned(request_pin), request, "final request changed while reducing")
    provenance(request)
    total_work = {key: sum(result["total_physical_work"][key] for result in results) for key in MAX_PHYSICAL_WORK}
    require(all(total_work[key] <= maximum for key, maximum in MAX_PHYSICAL_WORK.items()), "prospective assay physical-work cap exceeded")
    return prefix.seal({"schema": SCHEMA + "/receipt", "status": "VALIDATED_NOT_PROMOTED", "kind": expected_kind,
        "request": request_pin, "learner_seeds": [0, 1, 2], "independent_banks": 1,
        "unique_events": 8, "seeds": results, "descriptive_paired_summary": pooled,
        "total_physical_work": total_work,
        "prior_failed_work": {key: sum(result["prior_failed_work"][key] for result in results)
                              for key in results[0]["prior_failed_work"]},
        "elapsed_seconds": {key: sum(result["elapsed_seconds"][key] for result in results)
                            for key in results[0]["elapsed_seconds"]},
        "automatic_promotion": False, "full_contract_released": False, "limits": sequence.LIMITS,
        "interpretation": "Three learner seeds on the same exposed DEV bank, not independent banks. "
            "W0 diagnostic; W8 exposed DEV. B200 matches B dose, B400 matches work, neither is a pure causal replay control. "
            "No significance, generalization, or general G3/H1/H2 claims. Raw file/custody validation is not native attestation; "
            "warm tensor receipts and checkpoint bytes are joined, not a re-execution of training or dtype conversion."})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", required=True)
    parser.add_argument("--request-sha256", required=True)
    parser.add_argument("--expected-kind", choices=("NATIVE", "INJECTED_CPU_TEST"), default="NATIVE")
    args = parser.parse_args()
    result = reduce({"path": args.request, "sha256": args.request_sha256}, expected_kind=args.expected_kind)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
