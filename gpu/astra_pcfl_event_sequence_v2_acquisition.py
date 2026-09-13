"""Offline bound v2 acquisition check, not a C11 guard or native attestation.

validate(acquisition_pin, material, inputs, *, expected_kind="NATIVE") rereads
pinned NO_WRITE/A200 collections and recomputes every raw strict-stop score.
Requests use SCHEMA + "/request" and only the two collection file pins.
CPU fixtures require INJECTED_CPU_TEST explicitly. No model launch, answer
repair, evidence writes, or automatic promotion.
"""

import hashlib
from pathlib import Path

from organism_v6 import pcfl_event_sequence_v2 as sequence
from gpu import astra_pcfl_own_write_readout as reader

prefix, native = sequence.prefix, reader.native
require, same, digest = prefix.require, prefix.same, prefix.digest
SCHEMA = "pcfl.event_sequence.acquisition.v2"
OUTER_SCHEMA = "pcfl.event_sequence.outer.v2"
READOUT_SCHEMA = "pcfl.event_sequence.readout.v2"
FIT_SCHEMA = "pcfl.event_sequence.fit.v2"


def file_hash(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return prefix._json(prefix._record(Path(path).read_bytes()))


def sealed(value):
    prefix.unseal(value, value["sha256"])
    return value


def inventory(root):
    require(root.is_dir() and not root.is_symlink(), "regular archive directory required")
    result = {}
    for path in sorted(root.rglob("*")):
        require(not path.is_symlink() and (path.is_file() or path.is_dir()), "nonregular archive member")
        if path.is_file():
            result[path.relative_to(root).as_posix()] = {"size": path.stat().st_size, "sha256": file_hash(path)}
    return result


def pinned(pin):
    require(type(pin) is dict and set(pin) == {"path", "sha256"}, "closed file pin; no caller Boolean")
    require(type(pin["path"]) is str, "file path required")
    path = Path(pin["path"])
    require(path.is_absolute() and path.resolve() == path and path.is_file(), "absolute unaliased file pin required")
    native.sha(pin["sha256"])
    same(file_hash(path), pin["sha256"], "bound file hash differs")
    return read(path)


def fields(value, expected, label):
    same({key: value[key] for key in expected}, expected, label)


def material_check(material, expected_kind):
    sealed(material)
    fields(material, {"schema": sequence.SCHEMA + "/export", "status": "TOKENIZED_MATERIAL_NOT_EXECUTED",
                      "full_contract_released": False, "automatic_promotion": False}, "material scope")
    spec = sealed(material["spec"])
    same(spec["schema"], sequence.SCHEMA, "v2 spec required")
    sequence._seed(spec["learner_seed"])
    require(len(spec["records"]) == 8 and spec["historical"]["original_status"] == "FORMATION_FAILED", "fixed failed-formation bank")
    for index, record in enumerate(spec["records"]):
        same([record["index"], record["bank"], record["call_index"]], [index, "A" if index < 4 else "B", 2 * index + 1], "chronological A4/B4")
        same(record["target"], record["row"]["raw"], "exact admitted target")
        same(sequence.core.parse_event_line(record["target"]), record["row"]["fields"], "EVENT fields")
        same(record["request"], "READ EVENT " + record["row"]["fields"]["event"], "singleton address")
        fields(record["generation"], {"raw": record["target"], "sha256": native.text_hash(record["target"]), "origin": "CHILD_NATIVE" if expected_kind == "NATIVE" else "SYNTHETIC_NOT_NATIVE"}, "native source bytes")
    expected = [{"id": f"event-sequence-v2/W{view}/{index:02}", "request": record["request"], "view": view, "seed": 0, "output_tokens": 2048}
                for view in (0, 8) for index, record in enumerate(spec["records"])]
    same(spec["roster"], expected, "ordered sixteen-call roster")
    same(spec["roster_sha256"], digest(expected), "roster seal")
    for name, phase in material["phases"].items():
        sealed(phase)
        same(phase["items_sha256"], digest(phase["items"]), "material item hash")
        same([phase["parent_phase"], phase["updates"]], list(sequence.PHASES[name]), "fixed phase recipe")
    require(set(material["phases"]) == set(sequence.PHASES), "declared phases")
    return spec


def release(root, state, checksum):
    same(file_hash(root / "collection.json"), checksum, "collection FILE pin")
    collection = sealed(read(root / "collection.json"))
    fields(collection, {"schema": OUTER_SCHEMA + "/collection", "stage": "readout", "state": state, "status": "COMPLETED",
        "errors": [], "returncode": 0, "gpu_released": True, "retries": 0, "automatic_promotion": False,
        "full_contract_released": False, "original_status": "FORMATION_FAILED"}, "outer completion/release")
    observed = inventory(root)
    same({name: value for name, value in observed.items() if name != "collection.json"}, collection["files"], "outer inventory")
    require(not any(Path(name).name in ("failure.json", "collection_failure.json") for name in observed), "failed archive")
    same(inventory(root / "readout"), collection["stage_inventory"], "readout inventory")
    same(observed["readout_completed.json"], observed["readout/completed.json"], "outer completion snapshot")
    same(observed["inputs.input.json"]["sha256"], collection["inputs"]["sha256"], "outer input FILE pin")
    same(observed["allocation.input.json"]["sha256"], collection["allocation_file_sha256"], "allocation FILE pin")
    inputs, allocation, binding = (read(root / name) for name in ("inputs.input.json", "allocation.input.json", "binding.json"))
    context = read(root / "context.json")
    fields(context, {"schema": OUTER_SCHEMA, "stage": "readout", "state": state, "inputs": collection["inputs"],
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


def state_result(root, state, checksum, material, material_hash, expected_kind):
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
        fit_receipt = sealed(pinned(inputs["fit_receipt"]))
        phase = sequence.READ_STATES[state]
        fields(fit_receipt, {"schema": FIT_SCHEMA + "/completed", "status": "COMPLETE", "kind": expected_kind, "phase": phase,
            "learner_seed": spec["learner_seed"], "updates": sequence.PHASES[phase][1], "material_sha256": material_hash, "spec_sha256": spec["sha256"],
            "export_sha256": material["sha256"], "items_sha256": material["phases"][phase]["items_sha256"],
            "encoding_sha256": material["phases"][phase]["encoding_sha256"],
            "import_sha256": spec["import_sha256"], "base_unchanged": True, "nonfinite_batches": 0,
            "model_binding": inputs["model_binding"], "base_state_receipt": inputs["base_state_receipt"]}, "matching fit completion")
        fit_root = Path(inputs["fit_receipt"]["path"]).parent
        require(Path(inputs["fit_receipt"]["path"]).name == "completed.json", "fit completion filename")
        fit_inventory = inventory(fit_root)
        require(not any(Path(name).name in ("failure.json", "collection_failure.json") for name in fit_inventory), "failed fit")
        same({name: entry["sha256"] for name, entry in fit_inventory.items() if name != "completed.json"},
             fit_receipt["files"], "fit file drift")
        same(fit_receipt["checkpoint"], str(fit_root / "checkpoint"), "fit checkpoint path")
        same(read(fit_root / "config.json")["seed"], spec["learner_seed"], "saved fit seed")
        same(read(fit_root / "checkpoint/train_manifest.json")["config"]["seed"], spec["learner_seed"], "manifest fit seed")
        require(fit_receipt.get("predecessor") is None and fit_receipt.get("parent_phase") is None, "A200 clean C0 parent required")
        adapter_files = {name.removeprefix("checkpoint/"): entry for name, entry in fit_inventory.items()
                         if name in ("checkpoint/adapter_config.json", "checkpoint/adapter_model.safetensors", "checkpoint/README.md")}
        require({"adapter_config.json", "adapter_model.safetensors"} <= set(adapter_files), "complete safetensors adapter required")
        same(settings["adapter"], {"name": "pcfl-own-write", "id": 1, "path": str(stage / "adapter"), "files": adapter_files}, "A200 adapter route")
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
    return {"denominator": 16, "panels": panels, "tokens": totals, "truncated": completed["truncated"],
            "elapsed_seconds": {**completed["elapsed_seconds"], "outer_release_inclusive": collection["elapsed_seconds"]},
            "fit": None if fit_receipt is None else {"updates": fit_receipt["updates"], "checkpoint": fit_receipt["checkpoint"],
                "adapter_files": settings["adapter"]["files"]},
            "collection_file_sha256": checksum, "readout_sha256": completed["sha256"], "fit_receipt": inputs.get("fit_receipt")}, inputs, fit_receipt, collection


def validate_collections(request, material, inputs, *, expected_kind="NATIVE"):
    """Validate raw collections; a false observed gate is evidence, not permission."""
    require(expected_kind in ("NATIVE", "INJECTED_CPU_TEST"), "explicit supported evidence kind")
    require(type(request) is dict and set(request) == {"schema", "no_write_collection", "a200_collection"},
            "closed acquisition request; no caller Boolean or scores")
    same(request["schema"], SCHEMA + "/request", "v2 acquisition request required")
    require(type(inputs) is dict and not any(key in inputs for key in ("acquisition_passed", "callerBoolean", "gate_passed")),
            "no caller Boolean acquisition assertion")
    expected = {name: inputs[name] for name in ("material", "model_binding", "base_state_receipt")}
    values = {name: pinned(pin) for name, pin in expected.items()}
    same(material, values["material"], "expected material file differs")
    material_check(material, expected_kind)
    fields(values["base_state_receipt"], {"schema": "pcfl.own_write.cpu_base_state.v1", "status": "COMPLETE",
                  "model_binding_sha256": expected["model_binding"]["sha256"]}, "base/model binding")
    results, common = {}, None
    for state, key in (("NO_WRITE", "no_write_collection"), ("A200", "a200_collection")):
        pin = request[key]
        pinned(pin)
        require(Path(pin["path"]).name == "collection.json", "outer collection filename required")
        result, captured, _, collection = state_result(Path(pin["path"]).parent, state, pin["sha256"],
            material, expected["material"]["sha256"], expected_kind)
        same({name: captured[name] for name in expected}, expected, "exact expected material/model/base pins")
        for name in ("model_path", "learner_seed"):
            if name in inputs:
                same(inputs[name], material["spec"]["learner_seed"] if name == "learner_seed" else captured[name], "expected " + name)
        identity = {name: captured[name] for name in ("model_path", "model_binding", "base_state_receipt", "source_files", "environment", "shutdown_binding")}
        identity["outer_source_sha256"] = collection["outer_source_sha256"]
        if common is not None:
            same(identity, common, "state source/base identity differs")
        common, results[state] = identity, result
    observed = all(results[state]["panels"]["W8"][bank]["correct"] == count
                   for state, bank, count in (("NO_WRITE", "A", 0), ("NO_WRITE", "B", 0), ("A200", "A", 4), ("A200", "B", 0)))
    for pin in (*expected.values(), request["no_write_collection"], request["a200_collection"]):
        pinned(pin)
    pinned(results["A200"]["fit_receipt"])
    return prefix.seal({"schema": SCHEMA + "/receipt", "status": "VALIDATED", "kind": expected_kind,
        "request": request, **expected, "spec_sha256": material["spec"]["sha256"],
        "import_sha256": material["spec"]["import_sha256"], "learner_seed": material["spec"]["learner_seed"],
        "bindings": common, "states": results, "a200_fit_receipt": results["A200"]["fit_receipt"],
        "observed_gate": observed, "automatic_promotion": False, "full_contract_released": False,
        "limits": sequence.LIMITS, "interpretation": "Bound raw strict-stop acquisition only; not a C11 guard or native attestation. W8 is exposed DEV; W0 diagnostic retained. No answer repair. No automatic promotion."})


def validate(acquisition_pin, material, inputs, *, expected_kind="NATIVE"):
    """Validate a file-pinned request; preserve its original pin in the seal."""
    request = pinned(acquisition_pin)
    result = validate_collections(request, material, inputs, expected_kind=expected_kind)
    same(pinned(acquisition_pin), request, "acquisition request changed during validation")
    result.pop("sha256")
    return prefix.seal({**result, "acquisition_pin": acquisition_pin})
