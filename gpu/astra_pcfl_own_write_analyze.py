"""Offline descriptive paired READ reduction; no tokenizer/model or release calls."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gpu import astra_pcfl_own_write_command as command
from gpu import astra_pcfl_own_write_outer as outer
from gpu.astra_pcfl_zero_fit_analyze import Archive, same

native, core, own, readout = command.native, command.core, command.train_api, command.readout_api
require, digest, canonical = native.require, native.digest, native.canonical
STAGES = ("formation", "fit", "readout_AUTH_WRITE", "readout_NO_WRITE_C0")
LIMITS = ("Controlled curriculum record task and own-record cold address-to-block reproduction only, "
          "one life/root/fit/initialization. Preselected already-admitted EVENT pair handles are requested publicly; "
          "no autonomy or discovery claim. Formation format scaffolding is external format assistance. "
          "W8 holds out the wrapper, not facts or addresses; W0-W7 are repeated trained-surface diagnostics. "
          "No selectivity, preservation or generalization claim. One seed; no causal claim or significance. "
          "NO_WRITE_C0 is not compute-matched to AUTH_WRITE. Deterministic service is an "
          "authentic-target reference, not a model arm. No general pass, learning, H1/H2, "
          "C11, generality or full-assay qualification. Stage completion is not outer "
          "finalization; outer release is audited from archived receipts only. Tokens are cross-receipt checks, not "
          "independent tokenizer replay. All costs are elapsed intervals, not GPU-active time.")


def sealed(value):
    own._unseal(value, value["sha256"])
    return value


def interval(start, end):
    native.number(start)
    native.number(end)
    require(end >= start, "reversed elapsed interval")
    return end - start


def files(archive, prefix, exclude=()):
    return {name[len(prefix):]: entry["sha256"] for name, entry in archive.inventory.items()
            if name.startswith(prefix) and name[len(prefix):] not in exclude}


def stage(archive, manifest, name, checksum, manifest_checksum):
    native.sha(checksum)
    same(archive.inventory[name + "/completed.json"]["sha256"], checksum, "independent completion pin")
    receipt = sealed(archive.read(name + "/completed.json"))
    same([receipt[key] for key in ("schema", "status", "manifest_sha256", "stage", "outer_release_required", "gpu_released")],
         [command.SCHEMA + "/completed", "COMPLETE", manifest["sha256"], name, True, False], "stage completion")
    same(files(archive, name + "/", ("completed.json",)), receipt["files"], "stage inventory")
    require(not any("failure" in part or "failed" in part or "error" in part
                    for filename in receipt["files"] for part in Path(filename).parts), "failed stage evidence")
    elapsed = interval(receipt["started"], receipt["ended"])
    same(elapsed, receipt["elapsed_seconds"], "stage elapsed")
    require(elapsed <= manifest["stage_seconds"] and receipt["ended"] <= manifest["spec"]["expires_monotonic"], "stage deadline")
    same(archive.read(name + "/entry.json"), {"manifest_file_sha256": manifest_checksum,
         "stage": name, "started": receipt["started"], "kind": "NATIVE"}, "stage entry")
    same([receipt[key] for key in ("calls", "fits", "updates")],
         [20, 0, 0] if name == "formation" else [0, 1, 200] if name == "fit" else [153, 0, 0], "fixed stage counts")
    return receipt


def release(archive, manifest, name, pin, manifest_checksum):
    evidence = Archive(pin["outer_path"])
    same(evidence.inventory["collection.json"]["sha256"], pin["collection_sha256"], "outer collection pin")
    collection = evidence.read("collection.json")
    stage_name, arm = ("readout", name[len("readout_"):]) if name.startswith("readout_") else (name, None)
    same([collection[key] for key in ("schema", "status", "stage", "arm", "manifest_file_sha256", "errors", "returncode", "generation_retries")],
         [outer.SCHEMA + "/collection", "COMPLETED", stage_name, arm, manifest_checksum, [], 0, 0], "outer completion")
    same({key: value for key, value in evidence.inventory.items() if key != "collection.json"}, collection["files"], "outer inventory")
    same(collection["outer_source_sha256"], command.file_hash(outer.__file__), "outer source")
    context, binding = evidence.read("context.json"), evidence.read("binding.json")
    same([context[key] for key in ("schema", "stage", "arm", "manifest_file_sha256", "allocation_file_sha256", "outer_source_sha256")],
         [outer.SCHEMA, stage_name, arm, manifest_checksum, collection["allocation_file_sha256"], collection["outer_source_sha256"]], "outer context")
    same(evidence.inventory["allocation.input.json"]["sha256"], collection["allocation_file_sha256"], "allocation snapshot")
    allocation = evidence.read("allocation.input.json")
    same(allocation["gpu_uuid"], manifest["spec"]["gpu_uuid"], "allocation GPU")
    same(binding["stage_dir"], str(Path(manifest["root"]) / name), "outer original stage path")
    same(binding["helper_sha256"], command.file_hash(outer.lifecycle.__file__), "outer helper source")
    same(collection["stage_completed_file_sha256"], pin["completed_sha256"], "outer/stage pin")
    same(evidence.inventory["stage_completed.json"]["sha256"], pin["completed_sha256"], "outer stage copy")
    same(evidence.inventory["manifest.input.json"]["sha256"], manifest_checksum, "outer manifest copy")
    same({key[len(name) + 1:]: value for key, value in archive.inventory.items() if key.startswith(name + "/")},
         collection["stage_inventory"], "outer captured stage inventory")
    for key, value in collection["observations"].items():
        same(evidence.read(key + ".json")["value"], value, "outer observation join")
    observations = collection["observations"]
    same(observations["worker_release"]["identity"], collection["worker_identity"], "released worker")
    require(observations["worker_release"]["owned_group_released"] is True, "worker release absent")
    for phase in ("pre", "post"):
        require(observations[phase + "_queue"]["matched"] is True, "queue release mismatch")
        same([observations[phase + "_gpu"][key] for key in ("empty", "gpu_uuid")], [True, manifest["spec"]["gpu_uuid"]], "GPU release")
        same([observations[phase + "_cvd"][key] for key in ("clear", "owners", "unresolved")], [True, [], []], "CVD release")
    worker = evidence.read("worker_exit.json")
    same([worker["returncode"], worker["identity"]], [0, collection["worker_identity"]], "worker exit identity")
    same(evidence.read("worker_start.json")["identity"], collection["worker_identity"], "worker start identity")
    native.number(collection["elapsed_seconds"])
    same(evidence.snapshot(), evidence.inventory, "outer archive changed")
    return {"collection_sha256": pin["collection_sha256"], "worker_identity": collection["worker_identity"],
            "outer_elapsed_seconds": collection["elapsed_seconds"], "archived_release_verified": True}


def training(archive, manifest, completion):
    fitted = archive.read("fit/write/fit.json")
    own.validate_fit(fitted)
    same(fitted["binding"], {**manifest["binding"], "learning_rate": 3e-5}, "fit binding")
    same(fitted["schedule"], manifest["schedule"], "predeclared schedule")
    report = archive.read("formation/records/formation.json")
    same(fitted["report"], report, "authentic formation report")
    config = archive.read("formation/formation_config.json")
    same(fitted["config"], config, "formation config")
    same([report["link_pair_policy"], config["link_pair_policy"]],
         [command.formation_api.LINK_PAIR_POLICY] * 2, "public preselected pair policy")
    same(archive.read("formation/records/config.json"), config, "recorded formation config")
    same(config["planner"], manifest["formation_template"]["planner"], "formation planner")
    template = manifest["formation_template"]
    same(config["actor_config"], {**template["actor_config"], "deadline": config["actor_config"]["deadline"]}, "formation template settings")
    same(config["limits"], {**template["limits"], "deadline": config["actor_config"]["deadline"]}, "formation limits")
    same(config["seed"], template["seed"], "formation seed")
    same(config["actor_config"]["source_files"], manifest["sources"], "formation sources")
    for name, receipt in fitted["native_receipts"].items():
        same(archive.read("formation/actor/" + name + ".json"), receipt, "formation lifecycle join")
    same(archive.read("formation/actor_close.json"), fitted["native_receipts"]["close"], "formation close")
    require(archive.read("formation/shutdown.json")["shutdown_returned"] is True, "formation shutdown")
    for index, slot in enumerate(report["slots"]):
        attempt = slot["attempt"]
        same(archive.read(f"formation/records/call_{index:02}.attempt.json"), attempt, "formation attempt")
        same(archive.read(f"formation/records/call_{index:02}.request.json"),
             {key: attempt[key] for key in ("request", "limits")}, "formation request")
        for name, capture in attempt["capture"]["files"].items():
            same(archive.inventory["formation/actor/" + name]["sha256"], capture["sha256"], "native captured file bytes")
    encoded = sealed(archive.read("fit/write/encoding.json"))
    same(encoded["fit_sha256"], fitted["sha256"], "encoded fit")
    same(encoded["epochs"], manifest["schedule"]["epochs"], "encoded schedule")
    receipt = archive.read("fit/write/completed.json")
    same(digest(receipt), completion["writer_receipt_sha256"], "writer completion link")
    same(files(archive, "fit/write/", ("completed.json",)), receipt["files"], "writer inventory")
    same([receipt[key] for key in ("status", "fit_sha256", "encoding_sha256", "updates", "presentations", "training_forwards", "objective", "layout")],
         ["COMPLETE", fitted["sha256"], encoded["sha256"], 200, 800, 800, own.writer.OBJECTIVE, own.writer.LAYOUT], "writer completion")
    same(receipt["initial"], archive.read("fit/write/initial.json"), "initial state")
    for states in (receipt["initial"], receipt["final"]):
        for key in ("lora", "optimizer"):
            native.sha(states[key])
    update_path = archive.root / "fit/write/updates.jsonl"
    updates = [command.formation_api._decode_json(line) for line in update_path.read_text().splitlines()]
    require(len(updates) == 200, "exactly 200 recorded updates")
    lookup = {(item["slot"], item["view"]): item for item in encoded["items"]}
    require(len(lookup) == len(encoded["items"]) == 160, "exact160 unique training encodings")
    for slot in manifest["schedule"]["corpus"]["slots"]:
        query = report["writer_payload"]["queries"][slot["request"]]
        for view in range(8):
            same([lookup[(slot["id"], view)][key] for key in ("target_sha256", "source_sha256")],
                 [query["target_sha256"], query["source_sha256"]], "encoded authentic target/source")
    for index, update in enumerate(updates):
        epoch, batch = divmod(index, 40)
        items = encoded["epochs"][epoch][batch]
        same([update[key] for key in ("update", "epoch", "batch", "items", "source_sha256")],
             [index + 1, epoch, batch, items, [lookup[tuple(pair)]["source_sha256"] for pair in items]], "update schedule/lineage")
        for key in ("loss", "pre_clip_norm", "post_clip_norm"):
            native.number(update[key])
    adapter = archive.read("fit/adapter.json")
    same(adapter["path"], str(Path(manifest["root"]) / "fit/write/adapter"), "checkpoint path identity")
    inventory = {name[len("fit/write/adapter/"):]: entry for name, entry in archive.inventory.items()
                 if name.startswith("fit/write/adapter/")}
    same(adapter["files"], inventory, "checkpoint byte inventory")
    require({"adapter_config.json", "adapter_model.safetensors"} <= set(inventory)
            <= {"adapter_config.json", "adapter_model.safetensors", "README.md"}, "checkpoint files")
    metadata = archive.read("fit/write/adapter/adapter_config.json")
    same([metadata[key] for key in ("r", "lora_alpha", "lora_dropout", "peft_type")], [8, 16, .05, "LORA"], "rank8 checkpoint")
    return fitted, receipt, adapter


def arm_rows(archive, manifest, completion, arm, adapter, queries, measurements):
    prefix = "readout_" + arm + "/"
    settings = archive.read(prefix + "readout_config.json")
    expected = command._readout_config(manifest, arm, adapter,
        Path(manifest["root"]) / ("readout_" + arm) / "actor", min(manifest["spec"]["expires_monotonic"], completion["started"] + command.STAGE_SECONDS))
    same(settings, expected, "cold readout config")
    same(archive.read(prefix + "actor/config.json"), settings, "actor config")
    route = readout.route_identity(settings)
    identity = archive.read(prefix + "actor/identity.json")
    same([identity["kind"], identity["config_sha256"]], ["NATIVE_OWN_WRITE_READOUT", digest(settings)], "native readout identity")
    witness = identity["identity"]
    same([witness[key] for key in ("route", "engine", "adapter", "roster_sha256", "shutdown_binding")],
         [route, settings["engine"], adapter, manifest["roster_sha256"], settings["shutdown_binding"]], "readout witness")
    base = witness["base_identity"]
    for key in ("model_files",):
        same(base[key], manifest["binding"]["environment"][key], "cold base identity")
    same([base[key] for key in ("repository", "revision", "model_binding_sha256", "environment", "gpu_uuid_expected", "clean_lineage_certified")],
         [native.MODEL_NAME, native.REVISION, settings["model_binding"]["sha256"], settings["environment"], settings["gpu_uuid"], False], "frozen base witness")
    same(base["source_files"], manifest["sources"], "readout source identity")
    load = archive.read(prefix + "actor/load.json")
    close = archive.read(prefix + "actor/close.json")
    same(archive.read(prefix + "actor_close.json"), close, "readout close join")
    for record in (load, close):
        same([record["kind"], record["route"]], ["NATIVE_OWN_WRITE_READOUT", route], "cold lifecycle route")
    same([close[key] for key in ("failed", "error_type", "budget_exceeded", "calls_consumed", "planned_calls")],
         [False, None, False, 153, 153], "complete cold lifecycle")
    require(close["shutdown"]["shutdown_returned"] is True, "readout shutdown failed")
    scores = archive.read(prefix + "scores.json")
    same([scores[key] for key in ("arm", "roster_sha256", "denominator")], [arm, manifest["roster_sha256"], 153], "score roster")
    require(len(scores["results"]) == 153, "missing score rows")
    rows, generation_seconds, operation_seconds = [], 0., 0.
    for index, row in enumerate(manifest["roster"]):
        name = prefix + f"actor/call_{index:04}."
        request, render, captured, wrapped = [archive.read(name + suffix + ".json") for suffix in ("request", "render", "raw", "response")]
        response = archive.read(prefix + row["id"].replace("/", "_") + ".json")
        same(wrapped["response"], response, "raw response join")
        for record in (request, render, captured, response):
            same(record["route"], route, "per-call checkpoint route")
        same([request[key] for key in ("request", "row", "messages", "roster_sha256")],
             [{"id": row["id"]}, row, readout.public_messages(row), manifest["roster_sha256"]], "source-withdrawn request")
        raw = captured["raw"]
        same(captured["kind"], "NATIVE_OWN_WRITE_READOUT", "native raw required")
        same(raw["route"], route, "actual output route")
        same(raw["prompt_token_ids"], render["prompt_token_ids"], "prompt token join")
        same(measurements[row["id"]], {"text": render["rendered_prompt"], "token_ids": render["prompt_token_ids"]}, "predeclared per-address render/token surface")
        same(render["sampling"], {**native.SAMPLING, "seed": row["seed"], "max_tokens": row["output_tokens"]}, "sampling")
        prompt_ids, output_ids = native.token_ids(raw["prompt_token_ids"]), native.token_ids(raw["output_token_ids"])
        require(len(output_ids) <= row["output_tokens"] and len(prompt_ids) <= settings["max_input_tokens"], "token cap")
        text = raw["text"]
        require(type(text) is str and raw["finish_reason"] in ("stop", "length"), "raw/termination")
        same([response[key] for key in ("id", "request_sha256", "roster_sha256", "text", "prompt_tokens", "output_tokens", "finish_reason", "stop_reason", "truncated")],
             [row["id"], digest({"id": row["id"]}), manifest["roster_sha256"], text, len(prompt_ids), len(output_ids), raw["finish_reason"], raw["stop_reason"], raw["finish_reason"] == "length"], "response bytes/tokens")
        same([wrapped["raw_hex"], wrapped["raw_utf8_sha256"]], [text.encode("utf-8").hex(), native.text_hash(text)], "exact UTF8")
        target = queries[row["request"]]["target"]
        score = core.score_memory_response(text, target)
        stop = raw["finish_reason"] == "stop"
        same(scores["results"][index], {"id": row["id"], "request": row["request"], "view": row["view"], "raw": text,
             "finish_reason": raw["finish_reason"], "score": score, "strict_stop": stop and score["strict"], "semantic_stop": stop and score["semantic"]}, "unchanged raw scorer")
        require(load["ready_at"] <= captured["generation_started"] <= captured["generation_ended"] <= completion["ended"], "cold generation clocks")
        generation_seconds += interval(captured["generation_started"], captured["generation_ended"])
        native.number(response["device_seconds"])
        operation_seconds += response["device_seconds"]
        rows.append({"raw": text, "raw_utf8_sha256": wrapped["raw_utf8_sha256"], "exact_bytes": score["strict"],
                     "exact_stop": stop and score["strict"], "semantic": score["semantic"], "semantic_stop": stop and score["semantic"],
                     "refusal": score["refusal"], "usable_false_row": score["usable_false_row"],
                     "finish_reason": raw["finish_reason"], "truncated": not stop,
                     "prompt_tokens": len(prompt_ids), "output_tokens": len(output_ids)})
    native.number(close["elapsed_actor_seconds"])
    require(completion["started"] <= load["model_load_started"] <= load["ready_at"] <= completion["ended"] and
            generation_seconds <= operation_seconds <= close["elapsed_actor_seconds"] <= completion["elapsed_seconds"], "recorded cost intervals inconsistent")
    return rows, {"stage_elapsed_seconds": completion["elapsed_seconds"], "actor_operation_elapsed_seconds": close["elapsed_actor_seconds"],
                  "model_load_elapsed_seconds": interval(load["model_load_started"], load["ready_at"]),
                  "generation_wall_seconds_sum": generation_seconds, "response_operation_seconds_sum": operation_seconds}


def endpoints(pairs, service):
    require(len(pairs) == 153, "both complete 153-call arms required")
    vectors = {}
    for view in range(9):
        selected = [pair for pair in pairs if pair["view"] == view]
        require(len(selected) == 17 and len({pair["request"] for pair in selected}) == 17, "fixed17 ordered addresses")
        vectors[f"W{view}"] = {"role": "PRIMARY_HELD_WRAPPER_SAME_TRAINED_ADDRESSES" if view == 8 else "REPEATED_TRAINED_SURFACE_DIAGNOSTIC",
            "addresses": [pair["request"] for pair in selected], "ids": [pair["id"] for pair in selected],
            "arms": {arm: {metric: [int(pair["arms"][arm][source]) for pair in selected]
                     for metric, source in (("strict_stop", "exact_stop"), ("semantic_stop", "semantic_stop"), ("semantic", "semantic"))}
                     for arm in readout.ARMS}}
    selected = [pair for pair in pairs if pair["view"] == 8]
    target_service = {item["request"]: item["raw"] for item in service["items"]}
    service_vector = [int(target_service[pair["request"]] == pair["target"]) for pair in selected]
    require(len(target_service) == 17, "exact17 service addresses")
    primary = vectors["W8"]
    auth, baseline = [primary["arms"][arm]["strict_stop"] for arm in ("AUTH_WRITE", "NO_WRITE_C0")]
    differences = [written - unwritten for written, unwritten in zip(auth, baseline)]
    checks = {"service_17_of_17": sum(service_vector) == 17, "AUTH_at_least_15": sum(auth) >= 15,
              "C0_at_most_2": sum(baseline) <= 2, "paired_difference_at_least_13": sum(differences) >= 13}
    split = {}
    for kind, expected in (("EVENT", 8), ("EVENTS_AT", 6), ("LINKS_FROM", 3)):
        indices = [index for index, pair in enumerate(selected) if pair["query_kind"] == kind]
        require(len(indices) == expected, "fixed W8 query-kind denominator")
        split[kind] = {"addresses": [primary["addresses"][index] for index in indices],
            "arms": {arm: {metric: [values[index] for index in indices] for metric, values in metrics.items()}
                     for arm, metrics in primary["arms"].items()}}
    return {"label": "SCOPED_OWN_WRITE_ACQUISITION_PASS" if all(checks.values()) else "SCOPED_OWN_WRITE_ACQUISITION_FAIL",
            "thresholds": {"service_exact": 17, "AUTH_minimum": 15, "C0_maximum": 2, "paired_difference_minimum": 13},
            "denominator": 17, "checks": checks, "service_strict_vector": service_vector,
            "AUTH_strict_stop": sum(auth), "C0_strict_stop": sum(baseline), "paired_difference": sum(differences),
            "paired_difference_vector": differences, "W8_by_query_kind": split, "ordered_vectors": vectors}


def analyze(root, manifest_sha256, completion_hashes):
    archive = Archive(root)
    native.sha(manifest_sha256)
    same(archive.inventory["manifest.json"]["sha256"], manifest_sha256, "independent manifest pin")
    manifest = sealed(archive.read("manifest.json"))
    same([manifest["schema"], manifest["kind"], manifest["stage_seconds"]], [command.SCHEMA + "/manifest", "OFFLINE_PREPARATION", command.STAGE_SECONDS], "manifest scope")
    require(archive.root != Path(manifest["root"]), "relocated archive required, not live outputs")
    same(manifest["sources"], command.source_files(), "loaded source snapshot differs")
    require(set(completion_hashes) == set(STAGES), "four independent completion pins required")
    require(set(manifest["input_files"]) == {"spec.json", "measurements.json"}, "complete prepared inputs")
    for name, checksum in manifest["input_files"].items():
        require(name in ("spec.json", "measurements.json"), "prepared input name")
        same(archive.inventory[name]["sha256"], checksum, "prepared input pin")
    same(archive.read("spec.json"), manifest["spec"], "spec join")
    same(archive.inventory["spec.json"]["sha256"], manifest["spec_input"]["sha256"], "spec byte pin")
    completions, releases = {}, {}
    for name in STAGES:
        pin = completion_hashes[name]
        require(set(pin) == {"completed_sha256", "outer_path", "collection_sha256"}, "stage pin fields")
        completions[name] = stage(archive, manifest, name, pin["completed_sha256"], manifest_sha256)
        releases[name] = release(archive, manifest, name, pin, manifest_sha256)
    for name, prior in (("fit", "formation"), ("readout_AUTH_WRITE", "fit"), ("readout_NO_WRITE_C0", "formation")):
        require(completions[name]["started"] >= completions[prior]["ended"], "stage dependency clock")
    fitted, fit_receipt, adapter = training(archive, manifest, completions["fit"])
    report, queries = fitted["report"], fitted["report"]["writer_payload"]["queries"]
    same(completions["formation"]["report_sha256"], report["sha256"], "formation completion link")
    same(manifest["roster"], command._roster(fitted["config"]["planner"]), "exact fixed 153 READ roster")
    same(manifest["roster_sha256"], digest(manifest["roster"]), "roster seal")
    service = {"kind": "DETERMINISTIC_SERVICE_NOT_MODEL", "calls": 0,
               "items": [core.read_query(queries, request) for request in sorted(queries)]}
    same(archive.read("formation/exact_child_service.json"), service, "authentic deterministic service")
    measurements = sealed(archive.read("measurements.json"))["measurements"]
    require(len(measurements) >= 40 + 153, "missing predeclared READ measurements")
    surfaces = {row["id"]: measurements[40 + index] for index, row in enumerate(manifest["roster"])}
    arms, costs = {}, {}
    for arm in readout.ARMS:
        arms[arm], costs[arm] = arm_rows(archive, manifest, completions["readout_" + arm], arm,
                                       adapter if arm == "AUTH_WRITE" else None, queries, surfaces)
    buckets, pairs = defaultdict(lambda: defaultdict(int)), []
    for index, row in enumerate(manifest["roster"]):
        kind = core.parse_read(row["request"])[0]
        pair = {arm: arms[arm][index] for arm in readout.ARMS}
        changed = pair["AUTH_WRITE"]["raw"] != pair["NO_WRITE_C0"]["raw"]
        pairs.append({**row, "query_kind": kind, "target": queries[row["request"]]["target"], "changed_response": changed, "arms": pair})
        for key in ("all", f"W{row['view']}", kind, f"W{row['view']}/{kind}"):
            bucket = buckets[key]
            bucket["denominator"] += 1
            bucket["changed_responses"] += changed
            for arm, result in pair.items():
                for metric in ("exact_bytes", "exact_stop", "semantic", "semantic_stop", "refusal", "usable_false_row", "truncated", "prompt_tokens", "output_tokens"):
                    bucket[arm + "/" + metric] += result[metric]
                bucket[arm + "/finish_" + result["finish_reason"]] += 1
    same(archive.snapshot(), archive.inventory, "archive changed during analysis")
    scaffold = report.get("format_scaffold")
    return {"schema": "pcfl.own_write.analysis.v1", "label": "FORMAT_SCAFFOLDED_DESCRIPTIVE_ONLY" if scaffold else "DESCRIPTIVE_ONLY",
            "claim_boundary": "Controlled curriculum record task; own-record cold address-to-block reproduction only",
            "formation_policy": fitted["config"]["policy"], "link_pair_policy": report["link_pair_policy"],
            "format_scaffold": scaffold, "external_format_assistance": scaffold is not None, "limits": LIMITS,
            "archived_outer_release": releases, "endpoint": endpoints(pairs, service),
            "experimental_units": {"child_rows": 12, "address_blocks": 17, "scheduled_blocks": 20,
                 "unique_encodings": 160, "presentations": 800, "updates": 200, "fitted_lives": 1, "roots": 1, "initializations": 1},
            "authentic_child_rows": report["writer_payload"]["rows"], "scheduled_blocks": manifest["schedule"]["corpus"]["slots"],
            "manifest_file_sha256": manifest_sha256, "completion_file_sha256": completion_hashes,
            "archive_inventory_sha256": digest(archive.inventory), "analyzer_sha256": command.file_hash(__file__),
            "strata": {name: dict(values) for name, values in buckets.items()}, "pairs": pairs, "deterministic_service": service,
            "costs_not_gpu_active": {**costs, "formation_stage_elapsed_seconds": completions["formation"]["elapsed_seconds"],
                                      "fit_stage_elapsed_seconds": completions["fit"]["elapsed_seconds"]},
            "fit": {"updates": fit_receipt["updates"], "initial": fit_receipt["initial"], "final": fit_receipt["final"],
                    "base_state_sha256": fitted["binding"]["base_state_sha256"], "formation_report_sha256": report["sha256"],
                    "config_sha256": fitted["config_sha256"], "encoding_sha256": fit_receipt["encoding_sha256"],
                    "fit_sha256": fitted["sha256"], "checkpoint": adapter}}


def markdown(result):
    lines = ["# Own-write scoped archive reduction", "", result["label"], "",
             "External format assistance during formation: " + str(result["external_format_assistance"]), "", result["limits"], "",
             "Formation policy: " + result["formation_policy"], "Pair policy: " + result["link_pair_policy"], "",
             "## Predeclared W8 endpoint and all ordered vectors", "", "```json", json.dumps(result["endpoint"], indent=2), "```", "",
             "| Stratum | N | AUTH exact bytes / stop | C0 exact bytes / stop | Changed strings |",
             "| --- | ---: | ---: | ---: | ---: |"]
    for name, values in result["strata"].items():
        lines.append(f"| {name} | {values['denominator']} | {values['AUTH_WRITE/exact_bytes']} / {values['AUTH_WRITE/exact_stop']} | "
                     f"{values['NO_WRITE_C0/exact_bytes']} / {values['NO_WRITE_C0/exact_stop']} | {values['changed_responses']} |")
    lines.extend(["", "## Fit and costs (not GPU-active)", "", "```json",
                  json.dumps({"fit": result["fit"], "costs": result["costs_not_gpu_active"], "totals": result["strata"]["all"]}, indent=2), "```", ""])
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("archive", "manifest-sha256", "completion-pins", "output"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args(argv)
    out, root = Path(args.output).absolute(), Path(args.archive).absolute()
    require(not out.exists() and not out.is_symlink() and out.parent.resolve() == out.parent
            and not out.is_relative_to(root), "fresh output outside archive required")
    pins = command.read(args.completion_pins)
    require(all(not out.is_relative_to(Path(pin["outer_path"]).absolute()) for pin in pins.values()), "output overlaps outer archive")
    result = analyze(root, args.manifest_sha256, pins)
    encoded, rendered = canonical(result) + b"\n", markdown(result)
    out.mkdir(parents=False)
    (out / "analysis.json").write_bytes(encoded)
    (out / "analysis.md").write_text(rendered)


if __name__ == "__main__":
    main()
