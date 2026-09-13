"""Independent local source-event and capture-custody audit; no training export."""
import argparse
import collections
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import tarfile


ARCHIVE_SHA = "94e313ee069cc402eba18c515558ae649244b2036b17b430e4a5b29bd51698fb"
ROOT = "own_source_replay_capture_20260913_attempt1"
REPO = Path("/data/home/rohing/dream-state")
MATERIAL_SHA = "48c52b25ceb3edb719d2e5f958b63c58301fee90dd9df27277f54cabdc2b9cdb"
SUPPORTED = ("agreement", "contradicted_prediction", "absent_prediction")
FIELDS = ("try", "observed", "predicted", "relation")
ACTION = re.compile(r"ACT: TRY (-?\d+),(-?\d+),(-?\d+)")
OUTCOME = re.compile(r"the box says: (True|False) for \((-?\d+),(-?\d+),(-?\d+)\)")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def file_sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False,
                       separators=(",", ":"), allow_nan=False) + "\n").encode()


def strict_json(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "duplicate JSON key")
            result[key] = value
        return result

    def invalid(value):
        raise ValueError("nonfinite JSON: " + value)

    return json.loads(raw, object_pairs_hook=unique, parse_constant=invalid)


def source_hash(source):
    body = {key: value for key, value in source.items() if key != "source_id"}
    return sha(json.dumps(body, sort_keys=True, ensure_ascii=False,
                          allow_nan=False).encode())


def event_fields(event):
    lines = event["raw_response"].splitlines()
    actions = [(position, ACTION.fullmatch(line)) for position, line in enumerate(lines)
               if line.startswith("ACT:")]
    require(len(actions) == 1 and actions[0][1] is not None, "one strict comma TRY required")
    action_position, action = actions[0]
    priors = []
    for position, line in enumerate(lines):
        if position == action_position:
            continue
        match = re.fullmatch(r"PREDICT: ([TF])", line)
        require(match is not None and position < action_position,
                "unsupported or post-action prediction text")
        priors.append(match.group(1) == "T")
    triple = [int(value) for value in action.groups()]
    if event["raw_outcome"] is None:
        return None, "missing_outcome"
    outcome = OUTCOME.fullmatch(event["raw_outcome"])
    require(outcome is not None, "unsupported literal public outcome")
    if triple != [int(value) for value in outcome.groups()[1:]]:
        return None, "outcome_action_mismatch"
    if len(priors) > 1:
        return None, "ambiguous_prediction"
    observed = outcome.group(1) == "True"
    predicted = priors[0] if priors else None
    relation = "unavailable" if predicted is None else "matched" if predicted == observed else "mismatched"
    diagnosis = "absent_prediction" if predicted is None else "agreement" if predicted == observed else "contradicted_prediction"
    return dict(zip(FIELDS, (triple, observed, predicted, relation))), diagnosis


def source_fields(source):
    require(source_hash(source) == source["source_id"], "source content hash mismatch")
    events = source["events"]
    require(len(events) == 2 and [event["event_id"] for event in events] == ["e0", "e1"],
            "two chronological events required")
    require(source["selected_event_id"] == events[-1]["event_id"], "selected event is not last")
    return event_fields(events[-1])


def judge_raw(raw, finish_reason, expected):
    errors = []
    if finish_reason != "stop":
        errors.append("completion")
    try:
        parsed = strict_json(raw)
    except (ValueError, TypeError):
        return {"passed": False, "errors": errors + ["syntax"],
                "field_correct": {field: False for field in FIELDS}}
    if type(parsed) is not dict or set(parsed) != set(FIELDS):
        return {"passed": False, "errors": errors + ["four-field schema"],
                "field_correct": {field: False for field in FIELDS}}
    valid_types = {
        "try": type(parsed["try"]) is list and len(parsed["try"]) == 3 and
               all(type(value) is int for value in parsed["try"]),
        "observed": type(parsed["observed"]) is bool,
        "predicted": parsed["predicted"] is None or type(parsed["predicted"]) is bool,
        "relation": type(parsed["relation"]) is str,
    }
    correct = {field: valid_types[field] and type(parsed[field]) is type(expected[field]) and
               parsed[field] == expected[field] for field in FIELDS}
    errors.extend(field for field in FIELDS if not correct[field])
    return {"passed": not errors, "errors": errors, "field_correct": correct,
            "typed_content_sha256": sha(encoded(parsed)),
            "compact_sorted_bytes": raw == encoded(parsed).decode().removesuffix("\n")}


def safe_members(archive):
    result = {}
    for member in archive.getmembers():
        path = PurePosixPath(member.name)
        require(member.name and not path.is_absolute() and ".." not in path.parts and
                "\\" not in member.name and ":" not in member.name and
                all(ord(char) >= 32 for char in member.name), "unsafe archive path")
        key = str(path)
        require(key not in result, "duplicate/normalized archive name")
        require(member.isfile() or member.isdir(), "non-regular archive payload")
        require(not member.issparse(), "sparse archive payload")
        result[key] = member
    return result


class Capsule:
    def __init__(self, path, expected_sha):
        require(file_sha(path) == expected_sha, "archive SHA mismatch")
        with tarfile.open(path, "r:") as archive:
            members = safe_members(archive)
            self.member_count = len(members)
            require(sum(member.size for member in members.values()) < 32 * 1024 * 1024,
                    "capture too large")
            self.files = {name: archive.extractfile(member).read() for name, member in members.items()
                          if member.isfile()}
        self.hashes = {name: sha(raw) for name, raw in self.files.items()}

    def read(self, name):
        return strict_json(self.files[name])

    def inventory(self, prefix):
        return {name[len(prefix):]: checksum for name, checksum in self.hashes.items()
                if name.startswith(prefix)}


def original_material(archive_path, bundle, seed):
    prefix = f"localhome/local-rohing/astra_diagnostics/level1_perception_seed{seed}_20260913_attempt1/"
    provenance = bundle["provenance"]
    require(provenance["material_sha256"] == MATERIAL_SHA and
            provenance["material_member"] == prefix + "material.json" and
            provenance["plan_member"] == prefix + "plan.json", "original member binding")
    with tarfile.open(archive_path, "r:") as archive:
        members = safe_members(archive)
        payloads = {}
        for name in ("material.json", "plan.json"):
            member = members[prefix + name]
            require(member.isfile() and member.size < 4 * 1024 * 1024, "bounded original member")
            payloads[name] = archive.extractfile(member).read()
    require(sha(payloads["material.json"]) == MATERIAL_SHA, "original material hash")
    require(sha(payloads["plan.json"]) == provenance["plan_sha256"] ==
            bundle["producer"]["parent_plan_sha256"], "original parent plan hash")
    plan = strict_json(payloads["plan.json"])
    require(plan["skill"] == "perception" and plan["learner_seed"] == seed and
            plan["material_seed"] == 0, "original learner identity")
    return strict_json(payloads["material.json"])


def verify_selection(bundle, original):
    observations = bundle["training_observations"]
    require(len(observations) == len(original["training"]) == 96, "96 TRAIN denominator")
    original_rows = {row["row_id"]: row for row in original["training"]}
    require(len(original_rows) == 96, "duplicate original rows")
    diagnoses, strata, selected, source_ids = collections.Counter(), collections.Counter(), [], set()
    for row in observations:
        supplied = original_rows[row["row_id"]]
        require(row["source"] == supplied["source"] and row["input_messages"] == supplied["input_messages"],
                "original source/prompt byte-object join")
        source = row["source"]
        require(source["split"] == "train" and source["source_id"] == row["source_id"] and
                row["source_id"] not in source_ids, "TRAIN source identity/uniqueness")
        source_ids.add(row["source_id"])
        require(sha(encoded(row["input_messages"])) == row["input_sha256"], "prompt object hash")
        expected, diagnosis = source_fields(source)
        diagnoses[diagnosis] += 1
        require(diagnosis == row["diagnosis"] and (expected is not None) == row["source_admissible"],
                "independent source classification disagreement")
        earlier, _ = event_fields(source["events"][0])
        require(earlier is not None, "earlier public event invalid")
        skin = source["template_id"]
        require(re.fullmatch(r"train_[0-3]", skin) is not None, "TRAIN skin")
        choose = False
        if expected is not None:
            same = earlier["observed"] == expected["observed"]
            choose = same == ((int(skin[-1]) + SUPPORTED.index(diagnosis) + int(expected["observed"])) % 2 == 0)
            if choose:
                strata[(skin, diagnosis, expected["observed"])] += 1
        require(type(row["selected"]) is bool and row["selected"] == choose, "prospective selection differs")
        if choose:
            selected.append(row)
    require(diagnoses == {case: 16 for case in SUPPORTED +
                         ("missing_outcome", "outcome_action_mismatch", "ambiguous_prediction")},
            "96-case source population factorial")
    expected_strata = {(f"train_{skin}", case, outcome): 1 for skin in range(4)
                       for case in SUPPORTED for outcome in (False, True)}
    require(strata == expected_strata and len(selected) == 24, "24 selected factorial")
    requests = bundle["requests"]
    require([row["row_id"] for row in selected] == [request["row_id"] for request in requests],
            "selected request order/coverage")
    excluded = {row["row_id"] for panel in original["evaluation"].values() for row in panel}
    require(not excluded.intersection(request["row_id"] for request in requests), "held/canary source leak")
    require((bundle["source_population_denominator"], bundle["source_admissible"], bundle["requested"]) ==
            (96, 48, 24), "bundle source denominators")
    return selected


def verify_process(launch, started, released, seed, plan_sha, previous_end):
    identity = launch["identity"]
    require(all(type(identity[key]) is int and identity[key] > 0 for key in ("pid", "pgid", "start_ticks")),
            "process identity types")
    require(identity["pid"] == identity["pgid"] == started["pid"] == started["pgid"] and
            identity == released["identity"], "process identity join")
    require(launch["seed"] == started["seed"] == released["seed"] == seed and
            launch["plan_sha256"] == started["plan_sha256"] == plan_sha, "process seed/plan join")
    require(all(type(value) in (int, float) and math.isfinite(value) for value in
                (launch["started"], started["time"], released["ended"], released["elapsed_seconds"])),
            "process clocks finite")
    require(launch["started"] <= started["time"] <= released["ended"] and
            0 <= released["elapsed_seconds"] <= 900 and
            (previous_end is None or previous_end <= launch["started"]), "nonsequential process clocks")
    return identity


def verify_response(call, request, response, route, params):
    require(request == dict(call, params=params, lora_request=route), "native request/source/route join")
    require(response["lora_request"] == route, "response adapter route")
    native = call["native"]
    require(native["actual_system_text"] == "You are Qwen, created by Alibaba Cloud. You are a helpful assistant.",
            "unexpected system text")
    require(response["actual_prompt_token_ids"] == response["prompt_token_ids"] == native["prompt_token_ids"],
            "stored prompt-token join")
    require(response["rendered_prompt"] == native["rendered_prompt"] and
            response["actual_system_text"] == native["actual_system_text"] and
            response["actual_system_segment"] == native["actual_system_segment"], "stored rendered/system join")
    require(len(call["messages"]) == 1 and call["messages"][0]["role"] == "user", "original user-only request")
    rendered = native["actual_system_segment"] + "<|im_start|>user\n" + call["messages"][0]["content"] + "<|im_end|>\n<|im_start|>assistant\n"
    require(rendered == native["rendered_prompt"], "rendered prompt contains added/missing text")
    require(response["text"] == response["decoded_output"], "raw/decoded text mismatch")
    for key in ("actual_prompt_token_ids", "output_token_ids"):
        require(type(response[key]) is list and response[key] and
                all(type(token) is int and token >= 0 for token in response[key]), "invalid token inventory")
    require(len(response["output_token_ids"]) <= params["max_tokens"], "output exceeds cap")
    require(all(type(response[key]) in (int, float) and math.isfinite(response[key]) for key in ("started", "ended")) and
            response["ended"] >= response["started"], "invalid generation clock")


def audit(archive_path, original_archive, report_directory):
    capsule = Capsule(archive_path, ARCHIVE_SHA)
    read = capsule.read
    prefix = ROOT + "/"
    collected = ROOT + "_collected/"
    plan, complete = read(prefix + "plan.json"), read(prefix + "capture_complete.json")
    plan_sha, completion_sha = capsule.hashes[prefix + "plan.json"], capsule.hashes[prefix + "capture_complete.json"]
    report = read(collected + "replay_report.json")
    collection = read(collected + "collection.json")
    require(collection == {"completion_sha256": completion_sha,
                           "replay_report_sha256": capsule.hashes[collected + "replay_report.json"]}, "collection pins")
    require(report["completion_sha256"] == completion_sha and report["plan_sha256"] ==
            complete["plan_sha256"] == plan_sha, "report/completion plan binding")
    require(capsule.hashes[prefix + "spec.json"] == plan["spec_sha256"] and
            read(prefix + "spec.json") == plan["specification"], "specification binding")
    require(plan["limits"]["calls_total"] == 72 and plan["params"]["temperature"] == 0 and
            plan["params"]["max_tokens"] == 192 and plan["params"]["n"] == 1, "capture limits")
    require(set(plan["input_hashes"]) == {f"{kind}_seed{seed}.json" for seed in range(3) for kind in ("bundle", "calls")},
            "prepared input inventory")
    for name, checksum in plan["input_hashes"].items():
        require(capsule.hashes[prefix + name] == checksum, "prepared file hash " + name)
    for name, checksum in capsule.inventory(collected).items():
        require(file_sha(Path(report_directory) / name) == checksum, "VM copied report hash " + name)
    claim = read(ROOT + ".collection_claim.json")
    require(claim["plan_sha256"] == plan_sha and claim["retry"] is False and
            claim["out"] == plan["root"] + "_collected", "exclusive collection claim")
    exits = {name: read(ROOT + ".launcher/" + name + ".json")
             for name in ("controller_exit", "collector_exit", "exit")}
    require(all(value["returncode"] == 0 for value in exits.values()), "controller/collector/holder exit")
    require(exits["controller_exit"]["completed_unix"] <= exits["collector_exit"]["completed_unix"] <=
            exits["exit"]["completed_unix"], "collection follows controller")
    local_source_pins = {}
    for name in ("core", "native", "public", "lifecycle", "protocol"):
        binding = plan["specification"][name]
        local_path = (REPO / "research_notes/astra_memos/ASTRA_OWN_SOURCE_REPLAY_CAPTURE_2026-09-13.md"
                      if name == "protocol" else Path(binding["path"]))
        require(file_sha(local_path) == binding["sha256"], "frozen local source " + name)
        local_source_pins[name] = dict(binding, local_verified_path=str(local_path))
    runner = Path("/tmp/astra_own_source_replay_capture_20260913.py")
    require(file_sha(runner) == plan["self_sha256"], "frozen capture runner bytes")
    local_source_pins["capture_runner"] = {"path": str(runner), "sha256": file_sha(runner)}
    totals = collections.Counter()
    seeds, global_sources, global_raw, global_content, response_by_seed = [], set(), collections.Counter(), collections.Counter(), []
    previous_end, process_ids = None, []
    for seed in range(3):
        stage = prefix + f"run/seed{seed}/"
        require(capsule.inventory(stage) == complete["stages"][str(seed)], "stage full-file inventory")
        bundle = read(prefix + f"bundle_seed{seed}.json")
        original = original_material(original_archive, bundle, seed)
        selected = verify_selection(bundle, original)
        producer = bundle["producer"]
        require(producer == plan["producers"][str(seed)] and producer["learner_seed"] == seed and
                bundle["producer_sha256"] == sha(encoded(producer)), "producer identity")
        require(producer["model"] == plan["model"] and producer["model_files"] == plan["model_files"], "base manifest join")
        route = {"id": 1, "name": f"own_source_perception_seed{seed}", "path": producer["adapter"]}
        require(producer["adapter"].endswith(f"level1_perception_seed{seed}_20260913_attempt1/run/fit/adapter"), "original-parent route")
        identity = read(stage + "identity.json")
        require(identity["producer"] == producer and identity["producer_sha256"] == bundle["producer_sha256"] and
                identity["lora_request"] == route and identity["engine"] == plan["engine"] and
                identity["params"] == plan["params"] and identity["model_files"] == plan["model_files"], "native identity manifest join")
        launch, started, released, closed = [read(stage + name + ".json") for name in ("launch", "started", "released", "closed")]
        process = verify_process(launch, started, released, seed, plan_sha, previous_end)
        require(launch["command"] == [plan["python"], "-B", str(runner), "worker", "--root", plan["root"],
                                      "--plan-sha256", plan_sha, "--seed", str(seed), "--allow-gpu"], "archived worker command")
        previous_end = released["ended"]
        process_ids.append(process["pid"])
        require(closed["calls"] == 24 and closed["fits"] == closed["updates"] == closed["teacher_calls"] == 0 and
                closed["adapter_files_after"] == producer["adapter_files"], "closed no-fit/adapter manifest")
        expected_names = {"identity.json"} | {f"train_{index:02d}.{kind}.json" for index in range(24) for kind in ("request", "response")}
        require(set(closed["files"]) == expected_names, "closed 72-call file coverage")
        for name, checksum in closed["files"].items():
            require(capsule.hashes[stage + name] == checksum, "closed file hash")
        admission_name = f"seed{seed}_admission.json"
        admission = read(collected + admission_name)
        require(report["seed_reports"][str(seed)] == {"path": admission_name, "sha256": capsule.hashes[collected + admission_name]}, "admission report hash")
        require(admission["bundle_sha256"] == sha(encoded(bundle)) and admission["producer"] == producer,
                "admission bundle binding")
        accepted = {row["request_id"]: row for row in admission["admitted"]}
        captured = {row["response"]["request_id"]: row for row in admission["responses"]}
        require(len(accepted) == len(captured) == 24 and not admission["rejected"] and not admission["missing_request_ids"], "reported complete admission")
        calls = read(prefix + f"calls_seed{seed}.json")
        require(len(calls) == 24, "prepared 24 calls")
        rows, raw_counts, content_counts, field_counts, signature_counts = [], collections.Counter(), collections.Counter(), collections.Counter(), collections.Counter()
        triples, earlier_outcome_differences = set(), 0
        costs = collections.Counter()
        for index, (call, observation, core_request) in enumerate(zip(calls, selected, bundle["requests"])):
            require(call["call_id"] == f"train_{index:02d}" and call["core_request"] == core_request and
                    call["messages"] == observation["input_messages"] == core_request["input_messages"], "call/source order")
            require(core_request["input_sha256"] == observation["input_sha256"] and core_request["source_split"] == "train" and
                    core_request["producer_sha256"] == bundle["producer_sha256"] and core_request["source_id"] == observation["source_id"], "core request pins")
            require(core_request["request_id"] == sha(encoded({key: value for key, value in core_request.items() if key != "request_id"})), "request self hash")
            request = read(stage + call["call_id"] + ".request.json")
            response = read(stage + call["call_id"] + ".response.json")
            verify_response(call, request, response, route, plan["params"])
            expected, diagnosis = source_fields(observation["source"])
            earlier, _ = event_fields(observation["source"]["events"][0])
            triples.add(tuple(expected["try"]))
            earlier_outcome_differences += earlier["observed"] != expected["observed"]
            result = judge_raw(response["text"], response["finish_reason"], expected)
            source_id, request_id = observation["source_id"], core_request["request_id"]
            admitted = accepted[request_id]
            supplied = {"finish_reason": response["finish_reason"], "input_sha256": core_request["input_sha256"],
                        "producer_sha256": bundle["producer_sha256"], "raw": response["text"], "request_id": request_id}
            require(captured[request_id]["response"] == supplied and captured[request_id]["response_sha256"] == sha(encoded(supplied)), "copied native response join")
            target_hash = sha(response["text"].encode())
            require(admitted["raw_target"] == response["text"] and admitted["target_sha256"] ==
                    captured[request_id]["raw_sha256"] == target_hash and admitted["source"] == observation["source"] and
                    admitted["input_messages"] == core_request["input_messages"] and admitted["row_id"] == observation["row_id"] and
                    admitted["producer_sha256"] == bundle["producer_sha256"], "unchanged admitted raw target/source")
            proof = admitted["source_proof"]
            require(proof["original_source_id"] == source_id and proof["original_train_row_id"] == observation["row_id"] and
                    proof["input_sha256"] == core_request["input_sha256"] and
                    proof["supplied_response_sha256"] == sha(encoded(supplied)) and
                    proof["target_origin"] == "SUPPLIED_RAW_CHILD_RESPONSE_ONLY", "admission source proof")
            rows.append({"row_id": observation["row_id"], "source_id": source_id, "request_id": request_id,
                         "diagnosis": diagnosis, "selected_event_id": "e1", "raw_target_sha256": target_hash,
                         "request_file_sha256": capsule.hashes[stage + call["call_id"] + ".request.json"],
                         "response_file_sha256": capsule.hashes[stage + call["call_id"] + ".response.json"],
                         **result})
            field_counts.update({field: int(correct) for field, correct in result["field_correct"].items()})
            raw_counts[target_hash] += 1
            content_counts[result.get("typed_content_sha256", "invalid")] += 1
            signature_counts[str((expected["observed"], expected["predicted"], expected["relation"]))] += 1
            global_sources.add(source_id)
            costs.update(calls=1, prompt_tokens=len(response["actual_prompt_token_ids"]),
                         output_tokens=len(response["output_token_ids"]), generation_seconds=response["ended"] - response["started"])
        for key in ("calls", "prompt_tokens", "output_tokens", "generation_seconds"):
            require(math.isclose(costs[key], closed[key], rel_tol=0, abs_tol=1e-8), "independent cost sum")
        require(all(row["passed"] for row in rows), "independent four-field audit rejects native admission")
        require(report["counts"][str(seed)]["admitted"] == admission["admitted_count"] == len(rows), "independent admission count")
        require((admission["requested_denominator"], admission["source_admissible_denominator"], admission["source_population_denominator"]) == (24, 48, 96), "admission denominators")
        totals.update(costs)
        global_raw.update(raw_counts)
        global_content.update(content_counts)
        response_by_seed.append({row["source_id"]: row["raw_target_sha256"] for row in rows})
        seeds.append({"seed": seed, "source_population": 96, "source_supported": 48, "requested": 24,
                      "independent_passes": len(rows), "unique_sources": len({row["source_id"] for row in rows}),
                      "unique_raw_targets": len(raw_counts), "unique_typed_records": len(content_counts),
                      "unique_selected_triples": len(triples), "earlier_outcome_differs": earlier_outcome_differences,
                      "raw_target_multiplicities": dict(raw_counts), "non_triple_field_patterns": dict(signature_counts),
                      "field_correct": dict(field_counts), "compact_sorted_outputs": sum(row["compact_sorted_bytes"] for row in rows),
                      "costs": dict(costs), "process": dict(process, launch_unix=launch["started"], release_unix=released["ended"]),
                      "adapter_route": route, "adapter_weight_sha256_reported": producer["adapter_files"]["adapter_model.safetensors"],
                      "original_material_sha256": MATERIAL_SHA, "original_plan_sha256": producer["parent_plan_sha256"],
                      "rows": rows})
    require(len(set(process_ids)) == 3 and previous_end <= exits["controller_exit"]["completed_unix"], "three processes finish before controller")
    require(complete["calls"] == totals["calls"] == 72 and complete["fits"] == complete["updates"] == complete["teacher_calls"] == 0, "total no-fit capture accounting")
    for key in totals:
        require(math.isclose(totals[key], report["costs"][key], rel_tol=0, abs_tol=1e-8), "report total cost")
    require(complete["elapsed_seconds"] == report["costs"]["controller_seconds"], "controller elapsed join")
    return {"status": "PASS_INDEPENDENT_RAW_SOURCE_AND_LOCAL_CUSTODY", "training_export_ready": False,
            "fit_or_replay_adoption_authorized": False, "archive": {"path": str(archive_path), "sha256": ARCHIVE_SHA,
            "members": capsule.member_count, "regular_files": len(capsule.files)}, "member_sha256": capsule.hashes,
            "plan_sha256": plan_sha, "completion_sha256": completion_sha,
            "replay_report_sha256": capsule.hashes[collected + "replay_report.json"],
            "local_source_pins_verified_not_executed": local_source_pins, "seeds": seeds,
            "costs": dict(totals, fits=0, updates=0, teacher_calls=0, controller_seconds=complete["elapsed_seconds"]),
            "unique_sources_across_seeds": len(global_sources), "unique_raw_targets_across_seeds": len(global_raw),
            "unique_typed_records_across_seeds": len(global_content), "raw_target_multiplicities_across_seeds": dict(global_raw),
            "same_source_raw_identity_vs_seed0": {str(seed): sum(value == response_by_seed[0].get(source) for source, value in mapping.items())
                                                   for seed, mapping in enumerate(response_by_seed)},
            "controller_collector_holder_exits": exits, "reported_gpu_uuid": plan["gpu_uuid"],
            "reported_boot_id": plan["specification"]["expected_boot_id"],
            "limitations": ["Independent strict parser for this frozen transcript grammar; no original core judge/reducer/collector imported or executed.",
                            "Original material and parent-plan member hashes verified from a separate local archive; its whole-archive hash and adapter/base-weight bytes were not rehashed.",
                            "Three process identities and sequential release timestamps are wrapper receipts; no archived raw GPU-vacancy query or per-worker exit-status receipt, and no live vacancy check.",
                            "Controller/collector/holder rc0 receipts and successful closed manifests complement releases; a finally-path release alone cannot prove worker success.",
                            "Rendered prompt, stored token IDs and routes are joined, not newly tokenized/decoded or independently authenticated model execution/interpreter/hardware identity.",
                            "24 selected sources out of48supported/96TRAIN per seed;48unsupported and24unselected supported sources are not tested, nor held/canary performance.",
                            "Repeated externally authored TRAIN observations already in birth training, not fresh autonomous world execution or new independent facts across three learners.",
                            "Once-collection claims and copied report bytes are verified; no proof of absence of unarchived calls/collections.",
                            "No records normalized/exported as training data; no fit, replay mix, retention repair, H1/H2 or mechanism promotion follows."]}


def markdown(result, script_hash, json_hash):
    lines = ["# Independent own-source capture audit — EDITSTOP", "", "**" + result["status"] + "**", "",
             "Independent source-event parsing, not another collection. All original bytes remain untouched; no training-data export.", "",
             "| Seed | Correct/requested | Supported/TRAIN | Unique sources/raw/typed | Per-field try/observed/prior/relation | Worker PID/start ticks |",
             "| --- | --- | --- | --- | --- | --- |"]
    for seed in result["seeds"]:
        counts = "/".join(str(seed["field_correct"][field]) for field in FIELDS)
        lines.append(f"| {seed['seed']} | {seed['independent_passes']}/24 | 48/96 | {seed['unique_sources']}/{seed['unique_raw_targets']}/{seed['unique_typed_records']} | {counts} | {seed['process']['pid']}/{seed['process']['start_ticks']} |")
    costs = result["costs"]
    lines += ["", f"Exactly {costs['calls']} saved request/response pairs; 0 fits/updates/parent calls. Controller {costs['controller_seconds']:.6f}s; summed generation {costs['generation_seconds']:.6f}s; {costs['prompt_tokens']} prompt and {costs['output_tokens']} output tokens. These clocks are not active GPU time.", "",
              f"Across three seeds: {result['unique_sources_across_seeds']} distinct selected sources, {result['unique_raw_targets_across_seeds']} raw targets, {result['unique_typed_records_across_seeds']} typed records. Same-source byte identity versus seed0: {result['same_source_raw_identity_vs_seed0']}. Multiplicities and non-triple field patterns are in JSON; shared sources do not become72independent facts.", "",
              "Each seed has24distinct selected triples. The six observed/prior/relation patterns each occur4times; every raw target repeats3times across learners. Earlier and last outcomes differ on12/24selected sources per seed; agreement of outcomes on the other12 does not substitute for checking the selected TRY.", "",
              "## Independent checks", "",
              "Rehashed the bounded capture and all regular members; matched full stage/closed inventories, original material/parent-plan member pins, all96source classifications and the fixed24selection. Selected last e1 from two chronological events, parsed its comma-separated TRY, matched the outcome's own triple, and derived the prior only from explicit pre-action PREDICT lines (null if absent). Compared every output field with strict JSON/types, including bool-versus-int rejection. No original source judge or expected-answer target is used to decide correctness.", "",
              "Joined72prepared/native requests, rendered system/user bytes, recorded token IDs, routes, raw/decoded text, admission raw hashes/source proofs and copied reports. Verified three distinct sequential process groups and release identities; controller, collector and holder rc0 receipts. Frozen source files were hashed, not imported. Capture source code writes release from finally: see limitations.", "",
              "## Exact evidence hashes", "",
              f"- Archive `{result['archive']['path']}`: `{ARCHIVE_SHA}`; {result['archive']['members']} members/{result['archive']['regular_files']} regular files.",
              f"- Plan: `{result['plan_sha256']}`.", f"- Completion: `{result['completion_sha256']}`.",
              f"- Native replay report: `{result['replay_report_sha256']}`.", f"- Audit script: `{script_hash}`.",
              f"- Audit JSON: `{json_hash}`.", "- Every regular-file hash and seed admission/collection hashes are in the JSON member inventory.", "",
              "## Limitations", ""]
    lines.extend("- " + limitation for limitation in result["limitations"])
    lines += ["", "## Local reproduction commands", "",
              "`PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s /tmp -p test_astra_own_source_capture_audit_20260913.py -v`", "",
              "`python3 -B /tmp/astra_own_source_capture_audit_20260913.py --out-json /tmp/astra_own_source_capture_audit_recheck.json --out-md /tmp/astra_own_source_capture_audit_recheck.md`", "",
              "The audit refuses existing output paths. These commands read existing local evidence; neither collects nor executes native code.", "",
              "Main's separate replay-repair predeclaration963aa528 is not audited or authorized by this capture check; no repair fit/outcome was inspected. Manuscript remains EDITSTOP.", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=REPO / "gpu_artifacts_local" / ROOT / "evidence.tar")
    parser.add_argument("--original-archive", type=Path, default=REPO / "gpu_artifacts_local/level1_second_roster_20260913/node2_second_perception.tar")
    parser.add_argument("--report-directory", type=Path, default=Path("/tmp") / (ROOT + "_collected"))
    parser.add_argument("--out-json", type=Path, default=Path("/tmp/astra_own_source_capture_audit_20260913.json"))
    parser.add_argument("--out-md", type=Path, default=Path("/tmp/astra_own_source_capture_audit_20260913.md"))
    args = parser.parse_args()
    require(args.out_json != args.out_md and not args.out_json.exists() and not args.out_md.exists() and
            not args.out_json.is_symlink() and not args.out_md.is_symlink(), "exclusive new audit outputs required")
    result = audit(args.archive, args.original_archive, args.report_directory)
    result["audit_script_sha256"] = file_sha(__file__)
    result["command_scope"] = "Local stdlib only; no repo writes, native, network, collector or target export."
    raw = encoded(result)
    text = markdown(result, result["audit_script_sha256"], sha(raw))
    with args.out_json.open("xb") as stream:
        stream.write(raw)
    with args.out_md.open("x") as stream:
        stream.write(text)
    print(result["status"], "calls=72 fits=0 updates=0")
    print("JSON_SHA256", sha(raw))
    print("MD_SHA256", sha(text.encode()))


if __name__ == "__main__":
    main()
