"""Offline descriptive sequence reduction; no model, tokenizer, or lifecycle calls."""

import argparse
import hashlib
from pathlib import Path

from gpu import astra_pcfl_event_sequence_readout as readout
from gpu import astra_pcfl_event_sequence_outer as outer


sequence, prefix, native = readout.sequence, readout.prefix, readout.native
require, same, digest = prefix.require, prefix.same, prefix.digest
SCHEMA = "pcfl.event_sequence.analysis.v1"


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


def pinned(pin, remap=None):
    require(set(pin) == {"path", "sha256"}, "closed file pin")
    original = Path(pin["path"])
    require(original.is_absolute() and ".." not in original.parts, "absolute original path")
    matches = [(Path(source), Path(local)) for source, local in (remap or {}).items() if original.is_relative_to(Path(source))]
    if matches:
        source, local = max(matches, key=lambda pair: len(pair[0].parts))
        require(source.is_absolute() and local.is_absolute() and ".." not in local.parts, "explicit absolute remap")
        original = local / original.relative_to(source)
    same(file_hash(original), pin["sha256"], "bound file hash differs")
    return read(original)


def fields(value, expected, label):
    same({key: value[key] for key in expected}, expected, label)


def material_check(material):
    sealed(material)
    fields(material, {"schema": sequence.SCHEMA + "/export", "status": "TOKENIZED_MATERIAL_NOT_EXECUTED",
                      "full_contract_released": False, "automatic_promotion": False}, "material scope")
    spec = sealed(material["spec"])
    require(len(spec["records"]) == 8 and spec["historical"]["original_status"] == "FORMATION_FAILED", "fixed failed-formation bank")
    for index, record in enumerate(spec["records"]):
        same([record["index"], record["bank"], record["call_index"]], [index, "A" if index < 4 else "B", 2 * index + 1], "chronological A4/B4")
        same(record["target"], record["row"]["raw"], "exact admitted target")
        same(sequence.core.parse_event_line(record["target"]), record["row"]["fields"], "EVENT fields")
        same(record["request"], "READ EVENT " + record["row"]["fields"]["event"], "singleton address")
        fields(record["generation"], {"raw": record["target"], "sha256": native.text_hash(record["target"]), "origin": "CHILD_NATIVE"}, "native source bytes")
    expected = [{"id": f"event-sequence/W{view}/{index:02}", "request": record["request"], "view": view, "seed": 0, "output_tokens": 2048}
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
    fields(collection, {"schema": outer.SCHEMA + "/collection", "stage": "readout", "state": state, "status": "COMPLETED",
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
    fields(context, {"schema": outer.SCHEMA, "stage": "readout", "state": state, "inputs": collection["inputs"],
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


def state_result(root, state, checksum, material, material_hash, remap):
    collection, inputs, binding, before = release(root, state, checksum)
    stage, spec = root / "readout", material["spec"]
    completed, settings = sealed(read(stage / "completed.json")), read(stage / "readout_config.json")
    same(completed["sha256"], collection["completed_sha256"], "outer/readout seal")
    fields(completed, {"schema": readout.SCHEMA + "/completed", "status": "COMPLETE", "kind": "NATIVE", "state": state,
        "inputs": collection["inputs"], "material_sha256": material_hash, "spec_sha256": spec["sha256"], "import_sha256": spec["import_sha256"],
        "calls": 16, "fits": 0, "updates": 0, "gpu_released": False, "outer_release_required": True,
        "full_contract_released": False, "automatic_promotion": False}, "readout completion")
    same(completed["files"], {name: entry["sha256"] for name, entry in collection["stage_inventory"].items() if name != "completed.json"}, "worker inventory")
    same(read(stage / "inputs.json"), inputs, "input copy")
    same(inputs["material"]["sha256"], material_hash, "same material file")
    for path, source_hash in spec["sources"].items():
        same(inputs["source_files"][path], source_hash, "material/worker source bytes")
    for name in ("model_path", "model_binding", "source_files", "gpu_uuid", "shutdown_binding"):
        same(settings[name], inputs[name], "settings/input join")
    fields(settings, {"schema": readout.reader.SCHEMA, "roster": spec["roster"], "roster_sha256": spec["roster_sha256"],
        "environment": inputs["environment"]["native"], "engine": readout.reader.ENGINE, "max_calls": 16, "max_output_tokens": 2048,
        "max_input_tokens": 14336, "deadline": binding["worker_deadline_monotonic"],
        "tokenizer_files": material["tokenizer_receipt"]["tokenizer_files"], "chat_template_sha256": material["tokenizer_receipt"]["chat_template_sha256"],
        "arm": "NO_WRITE_C0" if state == "NO_WRITE" else "AUTH_WRITE"}, "frozen reader settings")
    same(Path(settings["output_dir"]).parent.as_posix(), binding["argv"][binding["argv"].index("--output") + 1], "original output binding")
    fit_receipt = None
    same(completed["fit_receipt"], inputs.get("fit_receipt"), "fit receipt pin")
    if state == "NO_WRITE":
        require(inputs.get("fit_receipt") is None and settings["adapter"] is None
                and not any(name.startswith("adapter/") for name in completed["files"]), "NO_WRITE must not mount fit")
    else:
        fit_receipt = sealed(pinned(inputs["fit_receipt"], remap))
        phase = sequence.READ_STATES[state]
        fields(fit_receipt, {"schema": readout.fit.SCHEMA + "/completed", "status": "COMPLETE", "kind": "NATIVE", "phase": phase,
            "updates": sequence.PHASES[phase][1], "material_sha256": material_hash, "spec_sha256": spec["sha256"],
            "export_sha256": material["sha256"], "items_sha256": material["phases"][phase]["items_sha256"],
            "encoding_sha256": material["phases"][phase]["encoding_sha256"],
            "import_sha256": spec["import_sha256"], "base_unchanged": True, "nonfinite_batches": 0,
            "model_binding": inputs["model_binding"], "base_state_receipt": inputs["base_state_receipt"]}, "matching fit completion")
        for name, entry in settings["adapter"]["files"].items():
            same(collection["stage_inventory"]["adapter/" + name], entry, "mount copy file identity")
            same(entry["sha256"], fit_receipt["files"]["checkpoint/" + name], "original checkpoint bytes")
        same(read(stage / "adapter_projection.json"), {"kind": "BYTE_IDENTICAL_MOUNT_COPY_NO_TRAINING",
             "source_checkpoint": fit_receipt["checkpoint"], "adapter": settings["adapter"]}, "adapter projection")
    responses = [read(stage / f"response_{index:04d}.json") for index in range(16)]
    actor = stage / "actor"
    identity, load, close, custody = (read(path) for path in (actor / "identity.json", actor / "load.json", actor / "close.json", stage / "custody.json"))
    route = readout.reader.route_identity(settings)
    same(read(actor / "config.json"), settings, "actor config")
    same([identity["pid"], identity["config_sha256"], custody["identity_sha256"]],
         [collection["worker_identity"]["pid"], digest(settings), digest(identity)], "native identity seal")
    for value in (identity, load, close, custody):
        same(value["kind"], "NATIVE_OWN_WRITE_READOUT", "native actor kind")
    for value in (completed["route"], identity["identity"]["route"], load["route"], close["route"], custody["route"]):
        same(value, route, "actual loaded route")
    same(close, read(stage / "actor_close.json"), "close copy")
    fields(close, {"calls_consumed": 16, "planned_calls": 16, "failed": False, "budget_exceeded": False, "error_type": None}, "complete reader close")
    same([close["shutdown"]["shutdown_returned"], close["shutdown"]["source"], load["shutdown"]["source"], custody["calls"]],
         [True, inputs["shutdown_binding"], inputs["shutdown_binding"], 16], "shutdown and calls")
    scores, recomputed, totals, generation = read(stage / "scores.json"), [], {"prompt": 0, "output": 0}, 0.0
    fields(scores, {"state": state, "denominator": 16, "pass_threshold": None}, "fixed score endpoint")
    require(len(scores["results"]) == len(list(actor.glob("call_*.raw.json"))) == len(list(stage.glob("response_*.json"))) == 16, "exact capture count")
    for index, (row, response) in enumerate(zip(spec["roster"], responses)):
        raw, returned, request, render = (read(actor / f"call_{index:04d}{suffix}.json") for suffix in (".raw", ".response", ".request", ".render"))
        same([raw["kind"], raw["route"], raw["raw"]["route"], response["route"], render["route"]], ["NATIVE_OWN_WRITE_READOUT", route, route, route, route], "raw route")
        same([request["row"], request["request"], request["messages"], response["id"], response["request_sha256"], response["roster_sha256"]],
             [row, {"id": row["id"]}, readout.reader.public_messages(row), row["id"], digest({"id": row["id"]}), spec["roster_sha256"]], "ordered request")
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
        require(value <= collection["elapsed_seconds"], "cost outside outer bound")
    same(inventory(root), before, "archive changed while reducing")
    return {"panels": panels, "tokens": totals, "truncated": completed["truncated"],
            "elapsed_seconds": {**completed["elapsed_seconds"], "outer_release_inclusive": collection["elapsed_seconds"]},
            "fit": None if fit_receipt is None else {"updates": fit_receipt["updates"], "checkpoint": fit_receipt["checkpoint"],
                "adapter_files": settings["adapter"]["files"]},
            "collection_file_sha256": checksum, "readout_sha256": completed["sha256"], "fit_receipt": inputs.get("fit_receipt")}, inputs, fit_receipt, collection


def transitions(before, after, retention=False):
    kept = sum(first and second for first, second in zip(before, after))
    return {"pre_correct": sum(before), "post_correct": sum(after), "kept": kept,
            "lost": sum(first and not second for first, second in zip(before, after)),
            "gained": sum(not first and second for first, second in zip(before, after)),
            "retention_fraction": kept / sum(before) if retention and any(before) else None}


def analyze(material_pin, states, *, remap=None):
    require({"NO_WRITE", "S_A"} <= set(states) <= set(sequence.READ_STATES), "NO_WRITE and S_A required; only declared states")
    material = pinned(material_pin)
    material_check(material)
    results, common, fits = {}, None, {}
    for state in sequence.READ_STATES:
        if state not in states:
            continue
        entry = states[state]
        result, inputs, fit_receipt, collection = state_result(Path(entry["outer"]), state, entry["collection_sha256"], material, material_pin["sha256"], remap)
        identity = {key: inputs[key] for key in ("model_path", "model_binding", "base_state_receipt", "source_files", "environment", "shutdown_binding")}
        identity["outer_source_sha256"] = collection["outer_source_sha256"]
        if common is not None:
            same(identity, common, "state source/base identity differs")
        common, results[state], fits[state] = identity, result, fit_receipt
    comparisons = {}
    for state in results:
        if state == "NO_WRITE":
            continue
        prior = "NO_WRITE" if state == "S_A" else "S_A"
        sequential = state in ("SEQ_REPLAY", "SEQ_NEW_ONLY")
        if sequential:
            same(fits[state]["predecessor"], results["S_A"]["fit_receipt"], "must continue the measured S_A checkpoint")
        comparisons[state] = {"against": prior, "same_adapter_continuation": sequential,
            "panels": {view: {bank: transitions(results[prior]["panels"][view][bank]["strict_stop"], results[state]["panels"][view][bank]["strict_stop"], sequential and bank == "A")
                              for bank in ("A", "B")} for view in ("W0", "W8")}}
    return prefix.seal({"schema": SCHEMA, "status": "DESCRIPTIVE_ONLY", "material": material_pin, "spec_sha256": material["spec"]["sha256"],
        "bindings": common, "states": results, "missing_states": [state for state in sequence.READ_STATES if state not in states],
        "sa_pre_correct_A": {view: results["S_A"]["panels"][view]["A"]["correct"] for view in ("W0", "W8")},
        "comparisons": comparisons, "pass_threshold": None, "limits": sequence.LIMITS,
        "interpretation": "Raw exact+stop vectors; W0 trained-surface diagnostic, W8 exposed-DEV wrapper. S_A acquisition versus NO_WRITE; retention only for measured S_A descendants. Fresh-control overlap is not retention; zero pre-correct yields null. NO_WRITE is not compute-matched. One bank/seed, no significance or general G3.",
        "time_basis": "elapsed wall intervals, not GPU active time", "full_contract_released": False, "automatic_promotion": False})


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("request", "request-sha256", "output"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args(argv)
    request = pinned({"path": str(Path(args.request).absolute()), "sha256": args.request_sha256})
    result = analyze(request["material"], request["states"], remap=request.get("remap"))
    output = Path(args.output).resolve()
    require(all(not output.is_relative_to(Path(state["outer"]).resolve()) for state in request["states"].values()), "output must be outside evidence")
    output.mkdir(exist_ok=False)
    readout.write(output / "analysis.json", result)
    lines = ["# EVENT sequence descriptive comparison", "", result["interpretation"], "", "Missing states: " + ", ".join(result["missing_states"]), ""]
    lines.append("S_A pre-correct A (future retention denominator): " + str(result["sa_pre_correct_A"]) + ". Zero means retention undefined.")
    for state, summary in result["states"].items():
        lines.append("- " + state + ": " + "; ".join(f"{view} {bank} {panel['correct']}/4" for view, banks in summary["panels"].items() for bank, panel in banks.items()))
    (output / "analysis.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
