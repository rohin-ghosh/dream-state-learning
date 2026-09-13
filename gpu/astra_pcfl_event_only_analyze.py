"""Offline fixed-prefix EVENT-only paired reduction; never collect or load models."""

import argparse
from collections import defaultdict
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gpu import astra_pcfl_event_only_command as command
from gpu import astra_pcfl_event_only_outer as outer
from gpu import astra_pcfl_own_write_analyze as shared
from gpu.astra_pcfl_zero_fit_analyze import Archive, same

event, prefix, native, core, readout = command.event, command.prefix, command.native, command.core, command.readout_api
require, canonical, digest = native.require, native.canonical, native.digest
interval, files = shared.interval, shared.files
SCHEMA = "pcfl.event_only.analysis.v1"
STAGES = ("fit", "readout_AUTH_WRITE", "readout_NO_WRITE_C0")
ARMS = ("AUTH_WRITE", "NO_WRITE_C0")
INPUTS = {"spec.json", "import.json", "fit.json", "tokenizer.json", "encoding.json", "identity.json", "read_measurements.json", "service.json"}
LIMITS = ("Separate post-failure developmental EVENT-prefix acquisition, not repaired full-bank completion. "
          "One named source life/root, one fit/initialization, eight child EVENTs and fourteen addresses; "
          "56 readout calls are repeated measurements, not 56 independent experiences. W8 holds out only "
          "the wrapper, not facts or addresses; W0 is descriptive trained-surface readout. Original format "
          "scaffolding assisted syntax, not semantics; no syntax-learning claim. NO_WRITE_C0 is not "
          "compute-matched. No LINK/route, retention, generalization, H1/H2 or full-assay qualification, "
          "automatic promotion, rerun or old17-query threshold. Tokenizer and native custody are archived "
          "receipt checks, not new tokenization or live GPU verification. Timings are elapsed intervals, "
          "not GPU-active time. Original FAILED/rc1/17 calls remain historical, not new-stage failure.")


def sealed(value):
    prefix.unseal(value, value["sha256"])
    return value


def source_binding(sources):
    def relative(values):
        anchors = [Path(name) for name in values if Path(name).name == "astra_pcfl_event_only_command.py"]
        require(len(anchors) == 1, "unique source-root anchor")
        root = anchors[0].parents[1]
        result = {}
        for name, checksum in values.items():
            path = Path(name)
            require(path.is_absolute() and ".." not in path.parts and path.is_relative_to(root), "source outside explicit repository root")
            native.sha(checksum)
            result[path.relative_to(root).as_posix()] = checksum
        return str(root), result
    original, declared = relative(sources)
    local, loaded = relative(command.source_files())
    same(declared, loaded, "repository-relative source byte pins differ")
    return {"original_source_root": original, "local_source_root": local, "relative_file_sha256": declared,
            "method": "EXPLICIT_REPOSITORY_RELATIVE_BYTES_NOT_ORIGINAL_V3_REPLAY"}


def stage(archive, manifest, name, pin, manifest_hash):
    same(archive.inventory[name + "/completed.json"]["sha256"], pin, "stage completion FILE pin")
    receipt = sealed(archive.read(name + "/completed.json"))
    same([receipt[key] for key in ("schema", "status", "manifest_sha256", "stage", "kind", "outer_release_required", "gpu_released",
                                  "full_contract_released", "original_status", "original_returncode")],
         [command.SCHEMA + "/completed", "COMPLETE", manifest["sha256"], name, "NATIVE", True, False, False, "FORMATION_FAILED", 1], "stage scope")
    same(files(archive, name + "/", ("completed.json",)), receipt["files"], "stage inventory")
    require(not any(Path(filename).name in ("failure.json", "failed.json") for filename in receipt["files"]), "failed new stage")
    elapsed = interval(receipt["started"], receipt["ended"])
    same(elapsed, receipt["elapsed_seconds"], "stage elapsed")
    require(elapsed <= command.TOTAL_SECONDS - command.CLEANUP_SECONDS and receipt["ended"] <= manifest["spec"]["expires_monotonic"], "worker cap")
    same(archive.read(name + "/entry.json"), {"manifest_file_sha256": manifest_hash, "stage": name, "started": receipt["started"], "kind": "NATIVE"}, "stage entry")
    same([receipt[key] for key in ("calls", "fits", "updates")], [0, 1, 200] if name == "fit" else [28, 0, 0], "stage counts")
    return receipt


def release(archive, manifest, name, pin, manifest_hash):
    evidence = Archive(pin["outer_path"])
    same(evidence.inventory["collection.json"]["sha256"], pin["collection_sha256"], "collection FILE pin")
    collection = evidence.read("collection.json")
    stage_name, arm = ("readout", name[len("readout_"):]) if name.startswith("readout_") else (name, None)
    same([collection[key] for key in ("schema", "status", "stage", "arm", "manifest_file_sha256", "errors", "returncode", "generation_retries")],
         [outer.SCHEMA + "/collection", "COMPLETED", stage_name, arm, manifest_hash, [], 0, 0], "outer completion")
    same({key: value for key, value in evidence.inventory.items() if key != "collection.json"}, collection["files"], "outer inventory")
    same(collection["outer_source_sha256"], command.file_hash(outer.__file__), "outer source pin")
    context, binding, allocation = [evidence.read(filename) for filename in ("context.json", "binding.json", "allocation.input.json")]
    same([context[key] for key in ("schema", "stage", "arm", "manifest_file_sha256", "allocation_file_sha256", "outer_source_sha256")],
         [outer.SCHEMA, stage_name, arm, manifest_hash, collection["allocation_file_sha256"], collection["outer_source_sha256"]], "outer context")
    same(evidence.inventory["allocation.input.json"]["sha256"], collection["allocation_file_sha256"], "allocation snapshot")
    same([allocation["gpu_uuid"], allocation["boot_id"]], [manifest["spec"]["gpu_uuid"], manifest["spec"]["boot_id"]], "allocation GPU/boot")
    same(binding["stage_dir"], str(Path(manifest["root"]) / name), "original stage path")
    same(binding["helper_sha256"], command.file_hash(outer.lifecycle.__file__), "lifecycle helper pin")
    same([collection["stage_completed_file_sha256"], evidence.inventory["stage_completed.json"]["sha256"]], [pin["completed_sha256"]] * 2, "outer stage copy")
    same(evidence.inventory["manifest.input.json"]["sha256"], manifest_hash, "outer manifest copy")
    same({key[len(name) + 1:]: value for key, value in archive.inventory.items() if key.startswith(name + "/")}, collection["stage_inventory"], "outer captured stage inventory")
    observations = collection["observations"]
    require(set(observations) >= {"worker_release", "worker_wait", "pre_queue", "post_queue", "pre_gpu", "post_gpu", "pre_cvd", "post_cvd"}, "release observations missing")
    for key, value in observations.items():
        record = evidence.read(key + ".json")
        same(record["value"], value, "observation byte join")
        interval(record["started_monotonic"], record["ended_monotonic"])
    identity = collection["worker_identity"]
    outer.lifecycle._identity_schema(identity)
    same(identity["boot_id"], allocation["boot_id"], "worker boot")
    same(identity["uid"], allocation["uid"], "worker UID")
    same([identity["pgid"], identity["sid"]], [identity["pid"]] * 2, "new-session process group")
    same(observations["worker_release"]["identity"], identity, "released worker identity")
    require(observations["worker_release"]["owned_group_released"] is True, "worker group not released")
    same(observations["worker_wait"], 0, "worker wait rc")
    for phase in ("pre", "post"):
        require(observations[phase + "_queue"]["matched"] is True, "queue reservation mismatch")
        same([observations[phase + "_gpu"][key] for key in ("empty", "gpu_uuid")], [True, allocation["gpu_uuid"]], "GPU vacancy")
        same([observations[phase + "_cvd"][key] for key in ("clear", "owners", "unresolved")], [True, [], []], "remaining CVD owner/unresolved process")
    worker, start = evidence.read("worker_exit.json"), evidence.read("worker_start.json")
    same([worker["returncode"], worker["signal"], worker["identity"], start["identity"]], [0, None, identity, identity], "worker start/exit")
    completed = archive.read(name + "/completed.json")
    deadline, entry = binding["deadline_monotonic"], context["entry_monotonic"]
    require(entry <= start["spawn_started_monotonic"] <= completed["started"] <= completed["ended"] <= binding["worker_deadline_monotonic"] <= deadline, "same-host stage/outer clocks")
    require(deadline - binding["worker_deadline_monotonic"] == command.CLEANUP_SECONDS, "cleanup margin")
    native.number(collection["elapsed_seconds"])
    require(worker["ended_monotonic"] >= completed["ended"] and worker["ended_monotonic"] <= entry + collection["elapsed_seconds"] <= deadline <= entry + command.TOTAL_SECONDS, "release-inclusive cap")
    group_released = evidence.read("worker_release.json")["ended_monotonic"]
    for phase in ("pre", "post"):
        for resource in ("queue", "gpu", "cvd"):
            record = evidence.read(phase + "_" + resource + ".json")
            require(entry <= record["started_monotonic"] <= record["ended_monotonic"] <= entry + collection["elapsed_seconds"], "resource observation outside outer interval")
            require(record["ended_monotonic"] <= start["spawn_started_monotonic"] if phase == "pre" else
                    record["started_monotonic"] >= group_released, "resource/worker release ordering")
    same(evidence.snapshot(), evidence.inventory, "outer archive changed")
    return {"collection_sha256": pin["collection_sha256"], "worker_identity": identity,
            "outer_elapsed_seconds": collection["elapsed_seconds"], "archived_release_verified": True,
            "post_cvd": observations["post_cvd"], "post_queue": observations["post_queue"],
            "worker_deadline_monotonic": binding["worker_deadline_monotonic"]}


def training(archive, fitted, completion, manifest):
    same(archive.read("fit/write/fit.json"), fitted, "executed fit differs from prepared fit")
    encoded = sealed(archive.read("fit/write/encoding.json"))
    same(encoded, archive.read("encoding.json"), "prepared/executed encoding")
    same([encoded["sha256"], encoded["fit_sha256"], encoded["epochs"]], [manifest["encoding_sha256"], fitted["sha256"], fitted["schedule"]["epochs"]], "encoding seals/schedule")
    same(archive.read("fit/write/event_only_scope_report.json"), event.validate_fit(fitted), "scoped writer validation")
    receipt = archive.read("fit/write/completed.json")
    same(digest(receipt), completion["writer_receipt_sha256"], "writer completion link")
    same(files(archive, "fit/write/", ("completed.json",)), receipt["files"], "writer inventory")
    same([receipt[key] for key in ("status", "fit_sha256", "encoding_sha256", "updates", "presentations", "training_forwards", "objective", "layout", "native_custody_verified")],
         ["COMPLETE", fitted["sha256"], encoded["sha256"], 200, 800, 800, event.writer.OBJECTIVE, event.writer.LAYOUT, False], "LOW200 completion")
    same(receipt["initial"], archive.read("fit/write/initial.json"), "fresh initial state receipt")
    for states in (receipt["initial"], receipt["final"]):
        for key in ("lora", "optimizer"):
            native.sha(states[key])
    lookup = {(item["slot"], item["view"]): item for item in encoded["items"]}
    require(len(lookup) == len(encoded["items"]) == 160, "160 unique encodings")
    for slot in fitted["schedule"]["corpus"]["slots"]:
        query = fitted["imported"]["queries"][slot["request"]]
        for view in range(8):
            item = lookup[(slot["id"], view)]
            same([item[key] for key in ("target_sha256", "source_sha256")], [query["target_sha256"], query["source_sha256"]], "encoded child source/target")
            payload = item["encoded"]
            tokens = native.token_ids(payload["ids"])
            labels = payload["labels"]
            require(len(tokens) == len(labels) <= 512 and tokens and type(labels[-1]) is int and labels[-1] == tokens[-1], "bounded target/EOS mask")
            same([payload["context_dropped"], payload["target_dropped"]], [0, 0], "no truncation")
            split = next((index for index, label in enumerate(labels) if label != -100), None)
            require(split is not None and split > 0 and all(type(label) is int for label in labels), "context/target labels")
            same(labels, [-100] * split + tokens[split:], "response-only contiguous target/EOS mask")
            same(payload["n_target"], len(tokens) - split, "target count")
    lines = (archive.root / "fit/write/updates.jsonl").read_text().splitlines()
    updates = [command.own.formation_api._decode_json(line) for line in lines]
    require(len(updates) == 200, "all 200 updates required")
    for index, update in enumerate(updates):
        epoch, batch = divmod(index, 40)
        items = encoded["epochs"][epoch][batch]
        same([update[key] for key in ("update", "epoch", "batch", "items", "source_sha256")],
             [index + 1, epoch, batch, items, [lookup[tuple(pair)]["source_sha256"] for pair in items]], "update schedule/lineage")
        same(update["supervised_tokens"], sum(lookup[tuple(pair)]["encoded"]["n_target"] for pair in items), "update token denominator")
        for key in ("loss", "pre_clip_norm", "post_clip_norm"):
            native.number(update[key])
        require(update["post_clip_norm"] <= 1.00001, "post-clip norm")
        for key in ("rng_before", "rng_after"):
            native.sha(update[key])
    adapter = archive.read("fit/adapter.json")
    same(adapter["path"], str(Path(manifest["root"]) / "fit/write/adapter"), "original checkpoint path")
    inventory = {name[len("fit/write/adapter/"):]: entry for name, entry in archive.inventory.items() if name.startswith("fit/write/adapter/")}
    same(adapter["files"], inventory, "checkpoint byte inventory")
    require({"adapter_config.json", "adapter_model.safetensors"} <= set(inventory) <= {"adapter_config.json", "adapter_model.safetensors", "README.md"}, "checkpoint files")
    metadata = archive.read("fit/write/adapter/adapter_config.json")
    same([metadata[key] for key in ("r", "lora_alpha", "lora_dropout", "peft_type")], [8, 16, .05, "LORA"], "rank8 checkpoint")
    return receipt, adapter, {"last_loss": updates[-1]["loss"], "first_loss": updates[0]["loss"],
        "supervised_tokens": sum(row["supervised_tokens"] for row in updates),
        "maximum_pre_clip_norm": max(row["pre_clip_norm"] for row in updates), "maximum_post_clip_norm": max(row["post_clip_norm"] for row in updates)}


def arm_rows(archive, manifest, fitted, completion, arm, adapter, surfaces, released):
    directory = "readout_" + arm + "/"
    settings = archive.read(directory + "readout_config.json")
    same(settings, command._readout_config(manifest, arm, adapter, Path(manifest["root"]) / ("readout_" + arm) / "actor", settings["deadline"]), "cold readout config")
    same(settings["deadline"], released["worker_deadline_monotonic"], "readout/outer deadline")
    require(completion["ended"] <= settings["deadline"] <= min(manifest["spec"]["expires_monotonic"], completion["started"] + command.TOTAL_SECONDS - command.CLEANUP_SECONDS), "readout deadline cap")
    same(archive.read(directory + "actor/config.json"), settings, "actor config")
    route = readout.route_identity(settings)
    identity = archive.read(directory + "actor/identity.json")
    same([identity["kind"], identity["config_sha256"], identity["pid"]], ["NATIVE_OWN_WRITE_READOUT", digest(settings), released["worker_identity"]["pid"]], "cold worker identity")
    witness = identity["identity"]
    same([witness[key] for key in ("route", "engine", "adapter", "roster_sha256", "shutdown_binding")],
         [route, settings["engine"], adapter, manifest["roster_sha256"], settings["shutdown_binding"]], "readout witness")
    base = witness["base_identity"]
    same(base, {key: value for key, value in archive.read("identity.json").items() if key not in ("mount", "lora_request")}, "prepare/cold base identity")
    same(base["model_files"], fitted["binding"]["environment"]["model_files"], "cold original base files")
    same([base[key] for key in ("repository", "revision", "model_binding_sha256", "environment", "gpu_uuid_expected", "clean_lineage_certified", "source_files")],
         [native.MODEL_NAME, native.REVISION, settings["model_binding"]["sha256"], settings["environment"], settings["gpu_uuid"], False, settings["source_files"]], "base/route/source identity")
    load, close = archive.read(directory + "actor/load.json"), archive.read(directory + "actor/close.json")
    same(archive.read(directory + "actor_close.json"), close, "close copy")
    for record in (load, close):
        same([record["kind"], record["route"]], ["NATIVE_OWN_WRITE_READOUT", route], "cold lifecycle")
    same([close[key] for key in ("failed", "error_type", "budget_exceeded", "calls_consumed", "planned_calls")], [False, None, False, 28, 28], "complete cold lifecycle")
    same([close["shutdown"]["shutdown_returned"], close["shutdown"]["source"]], [True, settings["shutdown_binding"]], "explicit shutdown")
    same(archive.read(directory + "custody.json"), {"kind": "NATIVE_OWN_WRITE_READOUT", "calls": 28, "route": route, "identity_sha256": digest(identity), "outer_release_required": True}, "command custody")
    scores = archive.read(directory + "scores.json")
    same([scores["arm"], scores["denominator"], scores["endpoint"], scores["paired_endpoint"]], [arm, 28, event.ENDPOINT, "REQUIRES_BOTH_RELEASED_ARMS_NOT_INFERRED_HERE"], "score scope")
    require(len(scores["results"]) == 28, "all read rows required")
    expected_actor_files = {"config.json", "identity.json", "load.json", "close.json"}
    expected_actor_files.update(f"call_{index:04d}.{suffix}.json" for index in range(28) for suffix in ("request", "render", "raw", "response"))
    same(sorted(files(archive, directory + "actor/")), sorted(expected_actor_files), "exact28 actor call inventory; no retry/error extras")
    rows, generation_seconds, operation_seconds = [], 0., 0.
    prior_end = load["ready_at"]
    for index, row in enumerate(manifest["roster"]):
        name = directory + f"actor/call_{index:04d}."
        request, render, captured, wrapped = [archive.read(name + suffix + ".json") for suffix in ("request", "render", "raw", "response")]
        response = archive.read(directory + row["id"].replace("/", "_") + ".json")
        same(wrapped["response"], response, "exact response copy")
        for record in (request, render, captured, response):
            same(record["route"], route, "per-call checkpoint route")
        same([request[key] for key in ("request", "row", "messages", "roster_sha256")],
             [{"id": row["id"]}, row, readout.public_messages(row), manifest["roster_sha256"]], "source-withdrawn exact query")
        raw = captured["raw"]
        same([captured["kind"], raw["route"], raw["prompt_token_ids"]], ["NATIVE_OWN_WRITE_READOUT", route, render["prompt_token_ids"]], "native raw/route/tokens")
        prompt_ids, output_ids = native.token_ids(raw["prompt_token_ids"]), native.token_ids(raw["output_token_ids"])
        same(surfaces[row["id"]], {"id": row["id"], "prompt_sha256": native.text_hash(render["rendered_prompt"]), "input_tokens": len(prompt_ids)}, "prepared READ surface hash/count")
        same(render["sampling"], {**native.SAMPLING, "seed": row["seed"], "max_tokens": row["output_tokens"]}, "unconstrained READ sampling")
        require(prompt_ids and len(output_ids) <= row["output_tokens"] and len(prompt_ids) <= settings["max_input_tokens"], "token caps")
        text, finish = raw["text"], raw["finish_reason"]
        require(type(text) is str and finish in ("stop", "length"), "raw termination")
        same([response[key] for key in ("id", "request_sha256", "roster_sha256", "text", "prompt_tokens", "output_tokens", "finish_reason", "stop_reason", "truncated")],
             [row["id"], digest({"id": row["id"]}), manifest["roster_sha256"], text, len(prompt_ids), len(output_ids), finish, raw["stop_reason"], finish == "length"], "raw response fields")
        same([wrapped["raw_hex"], wrapped["raw_utf8_sha256"]], [text.encode().hex(), native.text_hash(text)], "unchanged UTF8")
        score = core.score_memory_response(text, fitted["imported"]["queries"][row["request"]]["target"])
        stop = finish == "stop"
        same(scores["results"][index], {"id": row["id"], "request": row["request"], "view": row["view"], "raw": text,
             "finish_reason": finish, "score": score, "strict_stop": stop and score["strict"], "semantic_stop": stop and score["semantic"]}, "unchanged scorer")
        require(prior_end <= captured["generation_started"] <= captured["generation_ended"] <= completion["ended"], "generation chronology")
        prior_end = captured["generation_ended"]
        generation_seconds += interval(captured["generation_started"], captured["generation_ended"])
        native.number(response["device_seconds"])
        operation_seconds += response["device_seconds"]
        rows.append({"raw": text, "raw_utf8_sha256": wrapped["raw_utf8_sha256"], "score": score,
                     "exact_bytes": score["strict"], "exact_stop": stop and score["strict"], "semantic_stop": stop and score["semantic"],
                     "finish_reason": finish, "prompt_tokens": len(prompt_ids), "output_tokens": len(output_ids),
                     "errors": ([] if stop else ["non_stop_finish"]) + ([] if score["strict"] else ["strict_raw_mismatch"])})
    counts = {str(view): {"denominator": 14, "strict_stop": sum(row["exact_stop"] for item, row in zip(manifest["roster"], rows) if item["view"] == view),
                         "semantic_stop": sum(row["semantic_stop"] for item, row in zip(manifest["roster"], rows) if item["view"] == view)} for view in (0, 8)}
    same(scores["by_view"], counts, "readout aggregate crosscheck")
    same([completion["arm"], completion["by_view"]], [arm, counts], "stage aggregate join")
    native.number(close["elapsed_actor_seconds"])
    require(completion["started"] <= load["model_load_started"] <= load["ready_at"] <= completion["ended"] and generation_seconds <= operation_seconds <= close["elapsed_actor_seconds"] <= completion["elapsed_seconds"], "cold inclusive cost intervals")
    return rows, {"stage_elapsed_seconds": completion["elapsed_seconds"], "actor_operation_elapsed_seconds": close["elapsed_actor_seconds"],
                  "model_load_elapsed_seconds": interval(load["model_load_started"], load["ready_at"]),
                  "generation_wall_seconds_sum": generation_seconds, "response_operation_seconds_sum": operation_seconds}


def endpoints(pairs, service):
    require(len(pairs) == 28, "both complete28-call arms required")
    vectors = {}
    for view in (0, 8):
        selected = [pair for pair in pairs if type(pair["view"]) is int and pair["view"] == view]
        require(len(selected) == 14 and len({pair["request"] for pair in selected}) == 14, "14 distinct addresses per view")
        require(all(set(pair["arms"]) == set(ARMS) for pair in selected), "missing arm is not zero")
        for pair in selected:
            for arm in ARMS:
                require(type(pair["arms"][arm]["exact_stop"]) is bool, "strict_stop must be boolean")
        vectors[f"W{view}"] = {"role": "PRIMARY_HELD_WRAPPER_SAME_ADDRESSES" if view == 8 else "DESCRIPTIVE_TRAINED_SURFACE",
            "addresses": [pair["request"] for pair in selected], "ids": [pair["id"] for pair in selected],
            "arms": {arm: {"strict_stop": [int(pair["arms"][arm]["exact_stop"]) for pair in selected],
                "strict_bytes": [int(pair["arms"][arm]["exact_bytes"]) for pair in selected],
                "semantic": [int(pair["arms"][arm]["score"]["semantic"]) for pair in selected],
                "semantic_stop": [int(pair["arms"][arm]["semantic_stop"]) for pair in selected],
                "raw": [pair["arms"][arm]["raw"] for pair in selected],
                "finish_reason": [pair["arms"][arm]["finish_reason"] for pair in selected],
                "errors": [pair["arms"][arm]["errors"] for pair in selected]} for arm in ARMS}}
    same(vectors["W0"]["addresses"], vectors["W8"]["addresses"], "same ordered addresses across views")
    selected = [pair for pair in pairs if pair["view"] == 8]
    service_rows = {row["request"]: row["response"]["raw"] for row in service["results"]}
    require(len(service_rows) == len(service["results"]) == 14, "service14 distinct addresses")
    same(sorted(service_rows), sorted(vectors["W8"]["addresses"]), "service address coverage")
    service_vector = [int(service_rows[pair["request"]] == pair["target"]) for pair in selected]
    auth, baseline = [vectors["W8"]["arms"][arm]["strict_stop"] for arm in ARMS]
    differences = [written - unwritten for written, unwritten in zip(auth, baseline)]
    checks = {"service_14_of_14": sum(service_vector) == 14, "AUTH_at_least_13": sum(auth) >= 13,
              "C0_at_most_1": sum(baseline) <= 1, "paired_difference_at_least_12": sum(differences) >= 12}
    split = {}
    for kind, count in (("EVENT", 8), ("EVENTS_AT", 6)):
        indices = [index for index, pair in enumerate(selected) if pair["query_kind"] == kind]
        require(len(indices) == count, "EVENT-only query-kind denominator")
        split[kind] = {"denominator": count, "addresses": [selected[index]["request"] for index in indices],
                       "arms": {arm: [vectors["W8"]["arms"][arm]["strict_stop"][index] for index in indices] for arm in ARMS}}
    return {"label": "SCOPED_EVENT_PREFIX_ACQUISITION_PASS" if all(checks.values()) else "SCOPED_EVENT_PREFIX_ACQUISITION_FAIL",
            "thresholds": event.ENDPOINT, "denominator": 14, "checks": checks, "service_strict_vector": service_vector,
            "AUTH_strict_stop": sum(auth), "C0_strict_stop": sum(baseline), "paired_difference": sum(differences),
            "paired_difference_vector": differences, "ordered_vectors": vectors, "W8_by_query_kind": split}


def analyze(root, manifest_sha256, stage_pins):
    archive = Archive(root)
    native.sha(manifest_sha256)
    same(archive.inventory["manifest.json"]["sha256"], manifest_sha256, "manifest FILE pin")
    manifest = sealed(archive.read("manifest.json"))
    same([manifest[key] for key in ("schema", "kind", "total_seconds", "cleanup_seconds", "full_contract_released", "original_status", "original_returncode", "endpoint")],
         [command.SCHEMA + "/manifest", "OFFLINE_PREPARATION", 1800, 60, False, "FORMATION_FAILED", 1, event.ENDPOINT], "separate scope")
    require(archive.root != Path(manifest["root"]), "offline relocated archive, not live output")
    sources = source_binding(manifest["sources"])
    same(manifest["sources"], manifest["spec"]["source_files"], "source spec join")
    settings, spec = manifest["actor_template"], manifest["spec"]
    actor_sources = dict(spec["source_files"])
    for key in ("archive", "replay_receipt", "base_state_receipt", "authority", "shutdown_binding"):
        actor_sources[spec[key]["path"]] = spec[key]["sha256"]
    same([settings[key] for key in ("model_path", "model_binding", "environment", "gpu_uuid", "source_files", "max_calls", "max_input_tokens", "max_output_tokens")],
         [spec["model_path"], spec["model_binding"], spec["environment"]["native"], spec["gpu_uuid"], actor_sources, 28, 14336, 2048], "prepared actor/prefix/spec binding")
    same(spec["archive"]["sha256"], prefix.ARCHIVE_SHA256, "selected historical source archive")
    same(sorted(manifest["input_files"]), sorted(INPUTS), "prepared inputs")
    for name, checksum in manifest["input_files"].items():
        same(archive.inventory[name]["sha256"], checksum, "prepared FILE pin")
    same(archive.read("spec.json"), manifest["spec"], "spec copy")
    same(archive.inventory["spec.json"]["sha256"], manifest["spec_file_sha256"], "spec FILE pin")
    fitted = archive.read("fit.json")
    event.validate_fit(fitted)
    imported = archive.read("import.json")
    same([fitted["imported"], fitted["sha256"], imported["sha256"]], [imported, manifest["fit_sha256"], manifest["import_sha256"]], "fixed import fit join")
    same(fitted["binding"]["authority_sha256"], manifest["spec"]["authority"]["sha256"], "scope/fit authority")
    same(manifest["spec"]["authority"]["sha256"], command.file_hash(command.SCOPE), "current exact scope bytes")
    same([manifest["roster"], manifest["roster_sha256"]], [event.read_roster(imported), digest(event.read_roster(imported))], "exact W0/W8 roster")
    token = sealed(archive.read("tokenizer.json"))
    original_token = fitted["binding"]["tokenizer_receipt"]
    same(token, prefix.seal({"schema": prefix.SCHEMA + "/tokenizer", "import_sha256": imported["sha256"], "status": "EVENT_PREFIX_TOKENIZER_VERIFIED",
         "calls_checked": 16, "model_calls": 0, "tokenizer_files": original_token["files"], "chat_template_sha256": original_token["chat_template_sha256"], "full_contract_released": False}), "tokenizer qualification receipt")
    same(token["sha256"], manifest["tokenizer_sha256"], "tokenizer receipt seal")
    require(type(stage_pins) is dict and set(stage_pins) == set(STAGES), "all three stage pins required; missing arms unavailable")
    completions, releases = {}, {}
    for name in STAGES:
        pin = stage_pins[name]
        require(set(pin) == {"completed_sha256", "outer_path", "collection_sha256"}, "stage pin fields")
        completions[name] = stage(archive, manifest, name, pin["completed_sha256"], manifest_sha256)
        releases[name] = release(archive, manifest, name, pin, manifest_sha256)
    require(completions["readout_AUTH_WRITE"]["started"] >= completions["fit"]["ended"], "AUTH must follow fit")
    require(len({(item["worker_identity"]["pid"], item["worker_identity"]["start_ticks"], item["worker_identity"]["boot_id"]) for item in releases.values()}) == 3, "fresh distinct fit/readout processes")
    receipt, adapter, numerical = training(archive, fitted, completions["fit"], manifest)
    queries = imported["queries"]
    service = {"kind": "DETERMINISTIC_SERVICE_NOT_MODEL", "calls": 0, "denominator": 14, "exact": 14,
               "results": [{"request": request, "response": core.read_query(queries, request)} for request in sorted(queries)]}
    same(archive.read("service.json"), service, "authentic exact service14")
    measured = archive.read("read_measurements.json")
    same([row["id"] for row in measured], [row["id"] for row in manifest["roster"]], "prepared READ measurement order")
    surfaces = {row["id"]: row for row in measured}
    arms, costs = {}, {}
    for arm in ARMS:
        arms[arm], costs[arm] = arm_rows(archive, manifest, fitted, completions["readout_" + arm], arm,
            adapter if arm == "AUTH_WRITE" else None, surfaces, releases["readout_" + arm])
    pairs, buckets = [], defaultdict(lambda: defaultdict(int))
    for index, row in enumerate(manifest["roster"]):
        kind = core.parse_read(row["request"])[0]
        pair = {arm: arms[arm][index] for arm in ARMS}
        changed = pair[ARMS[0]]["raw"] != pair[ARMS[1]]["raw"]
        pairs.append({**row, "query_kind": kind, "target": queries[row["request"]]["target"], "changed_response": changed, "arms": pair})
        for key in ("all", f"W{row['view']}", kind, f"W{row['view']}/{kind}"):
            bucket = buckets[key]
            bucket["denominator"] += 1
            bucket["changed_responses"] += changed
            for arm, result in pair.items():
                for metric in ("exact_bytes", "exact_stop", "semantic_stop", "prompt_tokens", "output_tokens"):
                    bucket[arm + "/" + metric] += result[metric]
                bucket[arm + "/finish_" + result["finish_reason"]] += 1
    same(archive.snapshot(), archive.inventory, "archive changed during reduction")
    return {"schema": SCHEMA, "label": "SEPARATE_FORMAT_SCAFFOLDED_EVENT_PREFIX_ONLY", "limits": LIMITS,
            "endpoint": endpoints(pairs, service), "pairs": pairs, "strata": {key: dict(value) for key, value in buckets.items()},
            "deterministic_service": service, "format_scaffold": imported["format_scaffold"],
            "experimental_units": {"source_lives": 1, "roots": 1, "fits": 1, "initializations": 1, "child_EVENTs": 8,
                "address_blocks": 14, "scheduled_blocks": 20, "encodings": 160, "presentations": 800, "updates": 200,
                "readout_calls": 56, "independent_56_experiences": False},
            "historical_prefix": {"import_sha256": imported["sha256"], "archive_sha256": imported["evidence"]["archive_sha256"],
                "replay_receipt_sha256": imported["replay_receipt_sha256"], "original_status": imported["original_status"],
                "original_returncode": imported["original_returncode"], "original_calls": imported["original_calls"], "fits": 0, "updates": 0},
            "archived_outer_release": releases, "source_binding": sources, "manifest_file_sha256": manifest_sha256,
            "stage_pins": stage_pins, "archive_inventory_sha256": digest(archive.inventory), "analyzer_sha256": command.file_hash(__file__),
            "reused_analyzer_sources": {module: command.file_hash(sys.modules[module].__file__) for module in (shared.__name__, Archive.__module__)},
            "costs_not_gpu_active": {"fit_stage_elapsed_seconds": completions["fit"]["elapsed_seconds"], "readout": costs,
                "outer_elapsed_seconds_sum": sum(row["outer_elapsed_seconds"] for row in releases.values()),
                "historical_formation_calls": 17, "new_formation_calls": 0, "new_readout_calls": 56},
            "fit": {"fit_sha256": fitted["sha256"], "encoding_sha256": receipt["encoding_sha256"],
                "base_state_sha256": fitted["binding"]["base_state_sha256"], "initial": receipt["initial"], "final": receipt["final"],
                "checkpoint": adapter, **numerical}, "full_contract_released": False, "automatic_promotion": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("archive", "manifest-sha256", "stage-pins", "output"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args(argv)
    pins = command.read(args.stage_pins)
    out = Path(args.output).absolute()
    protected = [Path(args.archive).absolute(), Path(args.stage_pins).absolute(), Path(__file__).resolve().parents[1]]
    protected.extend(Path(pin["outer_path"]).absolute() for pin in pins.values())
    require(not out.exists() and not out.is_symlink() and out.parent.resolve() == out.parent and
            all(not out.is_relative_to(path) and not path.is_relative_to(out) for path in protected), "fresh output outside inputs/source required")
    result = analyze(args.archive, args.manifest_sha256, pins)
    out.mkdir(parents=False)
    (out / "analysis.json").write_bytes(canonical(result) + b"\n")
    (out / "analysis.md").write_text("# EVENT-prefix acquisition reduction\n\n" + LIMITS + "\n\n```json\n" + json.dumps(result["endpoint"], indent=2) + "\n```\n")


if __name__ == "__main__":
    main()
