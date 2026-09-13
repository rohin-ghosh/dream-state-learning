"""Independent local CPU replay of fixed-lesson alignment; no lifecycle APIs."""
from __future__ import annotations

import argparse
import ast
from collections import Counter
import copy
import hashlib
import json
import math
from pathlib import Path
import sys
from types import ModuleType


SCHEMA = "astra_parenting_alignment_analysis_20260913_v1"
INPUT_SCHEMA = SCHEMA + "_inputs"
SCOPE = "astra_parenting_alignment_inference_20260913_v1"
PROTOCOL_PIN = "5c53d6aa850b3a3a409c255ab9b28ce3b090f7325f35688437e42a86b1cccce5"
CORE_PIN = "71311d3d9add1f485289c6ee6824ef758393193ee05bcc088674d12697b11010"
RUNNER_PIN = "712248f1fc86b026e68e9cfbc791d3b441c6ded53db82f7622f8f2cd2b8b8c2a"
NATIVE_PIN = "3c03304ee5309517ce34f91b121594f0070b37bfb14f31f429f915d8310cc20e"
ARMS = ("ALIGNED", "SWAPPED", "NO_PARENT")
ENDPOINTS = ("PROCESS_USE", "EXECUTED", "RECORD_FAITHFUL", "FULL_MATERIAL")
CAPS = dict(ALIGNED=36, SWAPPED=36, NO_PARENT=32)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def encoded(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def equal(left, right, message):
    require(encoded(left) == encoded(right), message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def count(value, expected=None):
    require(type(value) is int and value >= 0, "count must be an integer, not bool")
    require(expected is None or value == expected, "count disagreement")
    return value


def number(value):
    require(type(value) in (int, float) and math.isfinite(value) and value >= 0, "nonnegative finite number required")
    return value


def boolean(value):
    require(type(value) is bool, "typed Boolean required")
    return value


def read(path):
    def pairs(entries):
        result = {}
        for key, value in entries:
            require(key not in result, "duplicate JSON field")
            result[key] = value
        return result
    result = json.loads(Path(path).read_bytes(), object_pairs_hook=pairs)
    encoded(result)
    return result


def pinned(path, checksum):
    path = Path(path)
    require(path.is_absolute() and path.is_file() and not any(item.is_symlink() for item in (path, *path.parents)), "regular absolute nonsymlink file required")
    require(type(checksum) is str and len(checksum) == 64 and digest(path) == checksum, "file/source pin differs: " + path.name)
    return path


def record(binding):
    require(type(binding) is dict and set(binding) == {"path", "sha256"}, "closed file binding required")
    return read(pinned(binding["path"], binding["sha256"]))


def local(root, name):
    relative = Path(name)
    require(not relative.is_absolute() and ".." not in relative.parts, "relative mirror path required")
    return Path(root) / relative


def load_sources(module_dir, source_root, protocol_path):
    require(CORE_PIN is not None and RUNNER_PIN is not None, "core/runner final freeze pending")
    directory = Path(module_dir)
    core_path = pinned(directory / "astra_parenting_alignment_core_20260913.py", CORE_PIN)
    pinned(directory / "astra_parenting_alignment_run_20260913.py", RUNNER_PIN)
    pinned(protocol_path, PROTOCOL_PIN)
    core = ModuleType("alignment_analysis_frozen_core")
    core.__file__ = str(core_path)
    exec(compile(core_path.read_bytes(), str(core_path), "exec"), core.__dict__)
    deps = core.load_dependencies(source_root, protocol_path=protocol_path)
    path = pinned(directory / "astra_level1_real_record_run_20260913.py", NATIVE_PIN)
    nodes = [node for node in ast.parse(path.read_bytes()).body if isinstance(node, ast.FunctionDef) and node.name == "validate_response"]
    require(len(nodes) == 1, "frozen response validator missing")
    namespace = dict(require=require, math=math)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec"), namespace)
    return dict(core=core, deps=deps, validate_response=namespace["validate_response"])


def load_bundle(entry):
    require(set(entry) == {"seed", "root", "plan_sha256", "completion_sha256", "report", "collection", "claim", "holder_span"}, "seed entry fields differ")
    seed = count(entry["seed"])
    require(seed in (0, 1, 2), "original seed required")
    root = Path(entry["root"])
    plan = read(pinned(root / "plan.json", entry["plan_sha256"]))
    complete = read(pinned(root / "capture_complete.json", entry["completion_sha256"]))
    report, collection, claim = (record(entry[key]) for key in ("report", "collection", "claim"))
    require(Path(entry["report"]["path"]).parent == Path(entry["collection"]["path"]).parent, "collection/report directory differs")
    for path in (root / "controller_failure.json", root / "prepare_failure.json", Path(entry["report"]["path"]).parent / "collection_failure.json"):
        require(not path.exists(), "incomplete or failed native attempt")
    files = {}
    for name, checksum in plan["input_hashes"].items():
        path = pinned(local(root, name), checksum)
        if name.endswith(".json"):
            files[name] = read(path)
    for arm, inventory in complete["stages"].items():
        require(arm in ARMS, "unknown stage")
        for name, checksum in inventory.items():
            require("failure" not in name and (name.endswith(".json") or name in ("stdout.log", "stderr.log")), "failed/non-inference stage artifact")
            path = pinned(local(root, "run/"+arm+"/"+name), checksum)
            if name.endswith(".json"):
                files["run/"+arm+"/"+name] = read(path)
    for name in ("prepare_started.json", "prepare_done.json", "controller_started.json"):
        files[name] = read(root / name)
    holder = None
    if entry["holder_span"] is not None:
        binding = entry["holder_span"]
        require(set(binding) == {"start", "end", "start_field", "end_field"}, "closed holder span binding required")
        start, end = record(binding["start"]), record(binding["end"])
        start_time, end_time = number(start[binding["start_field"]]), number(end[binding["end_field"]])
        require(end_time >= start_time, "holder chronology differs")
        holder = dict(seconds=end_time-start_time, binding=binding,
                      scope="Explicitly supplied holder receipt fields; not GPU-active time.")
    return dict(entry=entry, plan=plan, complete=complete, report=report, collection=collection, claim=claim, files=files, holder_span=holder)


def tally(capture, tasks, core):
    arm = capture["arm"]
    rows, contacts = capture["records"], capture["contacts"]
    require(len(rows) == len(tasks) == 16, "all16 scheduled tasks required, including invalid/uncalled")
    equal([row["task_id"] for row in rows], [task["task_id"] for task in tasks], "task order/content substitution")
    require(len(contacts) == (0 if arm == "NO_PARENT" else 4), "scheduled contact denominator differs")
    for index, contact in enumerate(contacts):
        task_family = tasks[4*index]["family"]
        lesson = task_family if arm == "ALIGNED" else "C" if task_family == "P" else "P"
        require(contact["lesson"] == lesson and contact["block_index"] == index, "delivered lesson assignment differs")
        equal(contact["contact"]["raw"], core.LESSONS[lesson], "delivered lesson text differs")
        response = contact["restatement"]["response"]
        expected = core.score_restate(response["raw"], response["finish_reason"], lesson, contact["restatement"]["errors"])
        equal(contact["score"], expected, "restatement scored against wrong lesson or altered response")
    require(not contacts or Counter(contact["lesson"] for contact in contacts) == {"P": 2, "C": 2}, "lesson multiset differs")
    for row, task in zip(rows, tasks, strict=True):
        for key in ("task_index", "block_index", "family", "delivery", "variant", "address"):
            equal(row[key], task[key], "task strata/identity differs")
        for name in ENDPOINTS:
            boolean(row[name])
        wake = row["wake"]
        equal(row["wake_score"], core.score_wake(wake["response"]["raw"], wake["response"]["finish_reason"], task, wake["errors"]), "wake scorer disagreement")
        require(row["PROCESS_USE"] is row["wake_score"]["PROCESS_USE"] and row["EXECUTED"] is row["wake_score"]["action_valid"], "process/action denominator differs")
        if not row["EXECUTED"]:
            require(row["execution"] is None and row["record"] is None and row["record_score"] is None and
                    row["RECORD_FAITHFUL"] is False and row["FULL_MATERIAL"] is False, "invalid action fabricated a receipt or record")
        else:
            require(row["execution"] is not None and row["record"] is not None, "executed task missing record call")
            require(row["execution"]["receipt"]["receipt_id"] not in {receipt["receipt_id"] for receipt in task["public_receipts"]}, "public receipt substituted for own receipt")
            equal(row["FULL_MATERIAL"], row["PROCESS_USE"] and row["EXECUTED"] and row["RECORD_FAITHFUL"], "full material conjunction differs")
    masks = {name: [row[name] for row in rows] for name in ENDPOINTS}
    counts = {name: sum(mask) for name, mask in masks.items()}
    calls = [event for event in capture["events"] if event["kind"] == "call"]
    counts.update(RESTATE=sum(boolean(contact["score"]["content_correct"]) for contact in contacts) if contacts else None,
        restate_denominator=4 if contacts else None, contacts=len(contacts), opportunities=16,
        by_delivery={str(delivery): {name: sum(row[name] for row in rows if row["delivery"] == delivery) for name in ENDPOINTS} for delivery in (0, 1)},
        by_family={family: {name: sum(row[name] for row in rows if row["family"] == family) for name in ENDPOINTS} for family in ("P", "C")},
        by_family_delivery={family: {str(delivery): dict(denominator=4, **{name: sum(row[name] for row in rows if row["family"] == family and row["delivery"] == delivery) for name in ENDPOINTS}) for delivery in (0, 1)} for family in ("P", "C")},
        endpoint_masks=masks, restate_mask=[contact["score"]["content_correct"] for contact in contacts] if contacts else None,
        calls=len(calls), updates=0, fits=0, parent_model_calls=0, record_not_called=sum(row["record"] is None for row in rows),
        finishes=dict(Counter(str(event["response"].get("finish_reason", "MISSING")) for event in calls)),
        input_utf8_bytes=sum(len(message["content"].encode()) for event in calls for message in event["request"]["input_messages"]),
        output_utf8_bytes=sum(len(event["response"]["raw"].encode()) for event in calls if type(event["response"].get("raw")) is str),
        raw_unique={kind: len({event["response"]["raw"] for event in calls if event["request"]["kind"] == kind and type(event["response"].get("raw")) is str}) for kind in core.MAX_OUTPUT_TOKENS},
        token_costs="Native wrapper must report actual token counts; UTF8 bytes are not tokens.")
    equal(counts, capture["readout"], "independent denominator/mask/cost count differs")
    equal(counts, capture["summary"], "capture summary differs")
    return counts


def feasibility(cells):
    states = {f"perception_seed{seed}_{arm}" for seed in range(3) for arm in ARMS}
    require(set(cells) == states, "all three original roots and nine arms required")
    roots = []
    for seed in range(3):
        aligned, swapped, anchor = (cells[f"perception_seed{seed}_{arm}"] for arm in ARMS)
        roots.append(dict(seed=seed, restate=aligned["RESTATE"], aligned=aligned["PROCESS_USE"], swapped=swapped["PROCESS_USE"],
            no_parent=anchor["PROCESS_USE"], aligned_minus_swapped=aligned["PROCESS_USE"]-swapped["PROCESS_USE"],
            aligned_minus_no_parent=aligned["PROCESS_USE"]-anchor["PROCESS_USE"], first=aligned["by_delivery"]["0"]["PROCESS_USE"],
            second=aligned["by_delivery"]["1"]["PROCESS_USE"], full_material=aligned["FULL_MATERIAL"]))
    masks = dict(restatement=[row["restate"] >= 3 for row in roots], swapped_advantage=[row["aligned_minus_swapped"] >= 4 for row in roots],
        swapped_no_large_harm=[row["aligned_minus_swapped"] > -4 for row in roots], anchor_advantage=[row["aligned_minus_no_parent"] >= 2 for row in roots],
        anchor_no_large_harm=[row["aligned_minus_no_parent"] >= -2 for row in roots], repeated_activation=[row["second"] >= row["first"] for row in roots],
        faithful_material=[row["full_material"] >= 8 for row in roots])
    vector = {key: all(values) if key.endswith("no_large_harm") else sum(values) >= 2 for key, values in masks.items()}
    return dict(complete=True, roots=roots, vector=vector, root_masks=masks, feasibility_pass=all(vector.values()), fit_authorized=False, updates=0,
        interpretation="Immediate developmental feasibility only; correlated task counts, three root replication units; no writer adopted.")


def pair(left, right):
    equal([row["task_id"] for row in left], [row["task_id"] for row in right], "paired tasks differ")
    result = {}
    for endpoint in ENDPOINTS:
        groups = {key: [] for key in ("both", "neither", "aligned_only", "comparison_only")}
        for first, second in zip(left, right, strict=True):
            key = "both" if first[endpoint] and second[endpoint] else "aligned_only" if first[endpoint] else "comparison_only" if second[endpoint] else "neither"
            groups[key].append(first["task_id"])
        result[endpoint] = dict(denominator=16, counts={key: len(values) for key, values in groups.items()}, task_ids=groups,
            difference=len(groups["aligned_only"])-len(groups["comparison_only"]))
    return result


def details(capture):
    rows = capture["records"]
    scored = {"wake": [row["wake_score"] for row in rows], "record": [row["record_score"] for row in rows if row["record_score"] is not None]}
    return dict(formats={kind: dict(called=len(scores), format_valid=sum(score["format_valid"] for score in scores),
        canonical=sum(score["canonical_form"] for score in scores), valid_noncanonical=sum(score["format_valid"] and not score["canonical_form"] for score in scores),
        errors=dict(Counter(error for score in scores for error in score["errors"]))) for kind, scores in scored.items()},
        restatements=[dict(block_index=contact["block_index"], delivered_lesson=contact["lesson"], score=contact["score"], phrase_overlap=contact["phrase_overlap"]) for contact in capture["contacts"]],
        task_cells=[dict(task_id=row["task_id"], family=row["family"], delivery=row["delivery"], status=row["status"],
            endpoints={name: row[name] for name in ENDPOINTS}, public_note=row["wake_score"]["note"],
            record_source=row["record_score"]["source"] if row["record_score"] else None,
            own_event_fields=row["record_score"]["event_fields"] if row["record_score"] else None,
            own_receipt_id=row["execution"]["receipt"]["receipt_id"] if row["execution"] else None) for row in rows])


def rendered_join(native, messages, system):
    segment = "<|im_start|>system\n"+system+"<|im_end|>\n"
    require(native["actual_system_text"] == system and native["actual_system_segment"] == segment, "native system segment differs")
    require(all(set(message) == {"role", "content"} and message["role"] == "user" for message in messages), "unexpected conversation roles")
    expected = segment+"".join("<|im_start|>user\n"+message["content"]+"<|im_end|>\n" for message in messages)+"<|im_start|>assistant\n"
    equal(native["rendered_prompt"], expected, "rendered Qwen context contains extra/missing text")


def validate_arm(bundle, arm, apis, tasks):
    plan, files, complete = (bundle[key] for key in ("plan", "files", "complete"))
    core, deps = apis["core"], apis["deps"]
    seed = plan["seed"]
    directory = "run/"+arm+"/"
    capture, calls, closed, identity = (files[directory+name] for name in ("capture.json", "core_calls.json", "closed.json", "identity.json"))
    state = f"perception_seed{seed}_{arm}"
    producer = plan["producers"][str(seed)]
    route = dict(name="own_source_perception_seed"+str(seed), id=1, path=producer["adapter"])
    expected_identity = dict(scope=SCOPE, state=state, seed=seed, arm=arm, producer=producer, route=route,
        core=plan["specification"]["core"], model_files=plan["model_files"], engine=plan["engine"], params=plan["params"])
    equal(identity, expected_identity, "native original-parent/arm identity differs")
    equal(capture["binding"], identity, "capture/native identity splice")
    require(capture["state"] == state and capture["seed"] == seed and capture["arm"] == arm, "capture state differs")
    require(capture["native_identity_verified"] is False and capture["automatic_pass"] is False and capture["fit_authorized"] is False, "core flags promoted")
    count(capture["updates"], 0)
    audit = core.replay_validate(capture, deps)
    counts = tally(capture, tasks, core)
    events = [event for event in capture["events"] if event["kind"] == "call"]
    equal(calls, [dict(request=event["request"], response=event["response"]) for event in events], "core callback chronology/raw join differs")
    expected_kinds = dict(wake=16, record=counts["EXECUTED"])
    if arm != "NO_PARENT":
        expected_kinds["restate"] = 4
    expected_kinds = {key: value for key, value in expected_kinds.items() if value}
    require(16 <= len(calls) <= CAPS[arm], "missing/extra complete callbacks")
    equal(dict(Counter(call["request"]["kind"] for call in calls)), expected_kinds, "scheduled vs actual call counts differ")
    names = {"identity.json", "capture.json", "core_calls.json"} | {f"{index:02d}"+suffix for index in range(len(calls)) for suffix in (".request.json", ".response.json")}
    equal(closed["files"], {name: complete["stages"][arm][name] for name in sorted(names)}, "closed/completion file pins differ")
    require({name for name in complete["stages"][arm] if name.endswith((".request.json", ".response.json"))} == names-{"identity.json", "capture.json", "core_calls.json"}, "unexpected native callback inventory")
    require(closed["arm"] == arm and closed["state"] == state, "closed state differs")
    equal(closed["adapter_files_after"], producer["adapter_files"], "original adapter changed")
    started, ended = number(closed["started_monotonic"]), number(closed["ended_monotonic"])
    require(ended >= started, "capture chronology differs")
    previous = started
    responses = []
    for index, call in enumerate(calls):
        core_request = call["request"]
        request, response = (files[directory+f"{index:02d}"+suffix] for suffix in (".request.json", ".response.json"))
        kind = core_request["kind"]
        params = dict(plan["params"], max_tokens=core.MAX_OUTPUT_TOKENS[kind], temperature=core.TEMPERATURE[kind], seed=core.GENERATION_SEED)
        equal(request, dict(call_id=f"{index:02d}", core_request=core_request, messages=core_request["input_messages"], native=request["native"], params=params, lora_request=route), "native prompt/callback/route mismatch")
        system = files["preflight.json"]["static_prompts"]["lesson_P"]["actual_system_text"]
        rendered_join(request["native"], request["messages"], system)
        tokens = request["native"]["prompt_token_ids"]
        require(type(tokens) is list and tokens and all(type(token) is int and token >= 0 for token in tokens), "invalid native prefix tokens")
        require(len(tokens)+params["max_tokens"] <= plan["engine"]["max_model_len"], "recorded context exceeds bound")
        apis["validate_response"](request, response, route)
        require(previous <= response["started"] <= response["ended"] <= ended, "response clock/chronology differs")
        previous = response["ended"]
        equal(call["response"], dict(request_id=core_request["request_id"], state=state, raw=response["text"], finish_reason=response["finish_reason"]), "exact native raw response differs")
        responses.append(response)
    costs = dict(calls=len(calls), fits=0, updates=0, parent_model_calls=0, kind_counts=expected_kinds,
        prompt_tokens=sum(len(response["actual_prompt_token_ids"]) for response in responses), output_tokens=sum(len(response["output_token_ids"]) for response in responses),
        generation_seconds=sum(response["ended"]-response["started"] for response in responses))
    equal({key: closed[key] for key in costs}, costs, "closed token/time/call costs differ")
    for key in ("calls", "fits", "updates", "parent_model_calls", "prompt_tokens", "output_tokens"):
        count(closed[key], costs[key])
    return dict(capture=capture, audit=audit, counts=counts, costs=costs, details=details(capture), capture_seconds=ended-started)


def custody(bundle):
    plan, complete, files = (bundle[key] for key in ("plan", "complete", "files"))
    previous, identities = 0, []
    for arm in ARMS:
        directory = "run/"+arm+"/"
        launch, started, done, exited, released, closed = (files[directory+name] for name in ("launch.json", "started.json", "worker_done.json", "exit.json", "released.json", "closed.json"))
        identity = launch["identity"]
        equal(identity, exited["identity"], "exit process identity differs")
        equal(identity, released["identity"], "release process identity differs")
        require(identity["pid"] == identity["pgid"] == started["pid"] == started["pgid"] and count(identity["pid"]) > 0 and count(identity["start_ticks"]) > 0, "fresh process identity missing")
        expected_command = [plan["python"], "-B", plan["specification"]["runner_path"] if "runner_path" in plan["specification"] else "/tmp/astra_parenting_alignment_run_20260913.py",
            "worker", "--root", plan["root"], "--plan-sha256", bundle["entry"]["plan_sha256"], "--arm", arm, "--allow-gpu"]
        equal(launch["command"], expected_command, "launched command differs")
        require(all(receipt["arm"] == arm for receipt in (launch, started, done, released)), "stage identity differs")
        require(all(receipt["plan_sha256"] == bundle["entry"]["plan_sha256"] for receipt in (launch, started, done)), "launched plan differs")
        count(exited["returncode"], 0)
        require(released["group_absent"] is True and released["gpu_vacant"] is True, "release not attested")
        times = [previous, launch["monotonic"], started["monotonic"], closed["started_monotonic"], closed["ended_monotonic"], done["monotonic"], exited["monotonic"], released["monotonic"]]
        for value in times:
            number(value)
        equal(times, sorted(times), "cold state chronology differs")
        require(number(launch["time"]) <= number(started["time"]) <= number(released["time"]), "wall receipt chronology differs")
        previous = released["monotonic"]
        identities.append((identity["pid"], identity["start_ticks"]))
    require(len(set(identities)) == 3, "cold process identity reused")
    controller = files["controller_started.json"]
    equal(controller["plan_sha256"], bundle["entry"]["plan_sha256"], "controller plan differs")
    require(controller["seconds"] == 3600 and number(controller["deadline"])-number(controller["monotonic"]) == 3600 and previous <= controller["deadline"], "controller/release cap differs")
    require(number(complete["elapsed_seconds"]) <= 3600 and previous <= controller["monotonic"]+complete["elapsed_seconds"], "whole-controller accounting differs")


def reduce_seed(bundle, apis):
    entry, plan, report, complete, files = (bundle[key] for key in ("entry", "plan", "report", "complete", "files"))
    core, deps = apis["core"], apis["deps"]
    seed = count(entry["seed"])
    require(seed in (0, 1, 2), "original seed required")
    equal([plan["seed"], report["seed"], plan["specification"]["seed"]], [seed]*3, "root seed mismatch")
    require(plan["scope"] == report["scope"] == complete["scope"] == SCOPE, "scope mismatch")
    require(plan["self_sha256"] == plan["specification"]["runner_sha256"] == RUNNER_PIN, "frozen runner differs")
    require(plan["specification"]["core"]["sha256"] == CORE_PIN and plan["specification"]["protocol"]["sha256"] == PROTOCOL_PIN, "core/protocol binding differs")
    equal(report["source_bindings"], plan["specification"], "source/plan binding differs")
    require(report["plan_sha256"] == complete["plan_sha256"] == entry["plan_sha256"] and report["completion_sha256"] == entry["completion_sha256"], "plan/completion custody differs")
    equal(plan["arms"], list(ARMS), "missing arm")
    equal(plan["states"], [f"perception_seed{seed}_{arm}" for arm in ARMS], "state roster differs")
    equal(sorted(complete["stages"]), sorted(ARMS), "missing/extra completed stage")
    require(set(plan["producers"]) == {str(seed)}, "producer inventory differs")
    producer = plan["producers"][str(seed)]
    expected_parent = core.root_binding(seed)
    for key in ("learner_seed", "parent_plan_sha256", "adapter"):
        equal(producer[key], expected_parent[key], "non-original perception parent")
    equal(producer["adapter_files"]["adapter_model.safetensors"], expected_parent["adapter_model_sha256"], "original adapter tensor pin differs")
    equal(report["original_parent"], producer, "report parent differs")
    equal(plan["input_hashes"]["original_plan.json"], expected_parent["parent_plan_sha256"], "original source plan pin differs")
    for key in ("model", "model_files", "environment", "python", "python_sha256", "chat_template", "engine", "params"):
        equal(plan[key], files["original_plan.json"][key], "frozen original model/environment metadata differs")
    equal(files["spec.json"], plan["specification"], "spec snapshot differs")
    equal(plan["input_hashes"]["prior_task_ids.json"], plan["specification"]["prior_task_ids"]["sha256"], "prior namespace inventory differs")
    manifest = core.build_manifest(deps, prior_ids=files["prior_task_ids.json"])
    equal(files["manifest.json"], manifest, "source/task/prompt manifest replay differs")
    require(report["manifest_sha256"] == plan["input_hashes"]["manifest.json"], "manifest hash join differs")
    equal(report["preflight"], files["preflight.json"], "preflight receipt differs")
    preflight = files["preflight.json"]
    require(set(preflight["lesson_literal_tokens"]) == {"P", "C"}, "lesson token count inventory differs")
    for value in preflight["lesson_literal_tokens"].values():
        require(count(value) > 0, "positive lesson token count required")
    count(preflight["lesson_multiset_tokens_per_lesson_arm"], 2*sum(preflight["lesson_literal_tokens"].values()))
    require(preflight["equal_lesson_multiset"] is True, "lesson multiset mismatch")
    equal(preflight["individual_lesson_lengths_equal"], preflight["lesson_literal_tokens"]["P"] == preflight["lesson_literal_tokens"]["C"], "individual lesson token comparison differs")
    static = {"lesson_"+name: core.RESTATE_TEMPLATE.format(lesson=text) for name, text in core.LESSONS.items()}
    static.update({task["task_id"]: task["ordinary_prompt"] for task in manifest["schedules"][str(seed)]})
    require(set(preflight["static_prompts"]) == set(static), "preflight task prompt inventory differs")
    system = preflight["static_prompts"]["lesson_P"]["actual_system_text"]
    for name, text in static.items():
        rendered_join(preflight["static_prompts"][name], [dict(role="user", content=text)], system)
    require(report["native_capture_custody_checked"] is True and report["automatic_pass"] is False and report["fit_authorized"] is False and complete["collected"] is False, "custody/qualification differs")
    custody(bundle)
    arms = {arm: validate_arm(bundle, arm, apis, manifest["schedules"][str(seed)]) for arm in ARMS}
    equal(report["captures"], [arms[arm]["capture"] for arm in ARMS], "collected raw capture substitution")
    equal(report["replay_audits"], {arm: arms[arm]["audit"] for arm in ARMS}, "stored replay audit differs")
    equal(report["costs_per_arm"], {arm: arms[arm]["costs"] for arm in ARMS}, "per-arm costs differ")
    cells = {arms[arm]["capture"]["state"]: arms[arm]["counts"] for arm in ARMS}
    equal(report["summary"]["cells"], cells, "collected endpoint cells differ")
    equal(report["summary"]["gate"], core.threshold_vector(cells), "partial gate differs")
    require(report["summary"]["automatic_pass"] is False and report["summary"]["fit_authorized"] is False, "partial report promoted")
    costs = {key: sum(arms[arm]["costs"][key] for arm in ARMS) for key in ("calls", "fits", "updates", "parent_model_calls", "prompt_tokens", "output_tokens", "generation_seconds")}
    equal(report["costs"], costs, "total costs differ")
    for key in ("calls", "fits", "updates", "parent_model_calls"):
        count(complete[key], costs[key])
    require(costs["calls"] <= 104 and costs["fits"] == costs["updates"] == costs["parent_model_calls"] == 0, "inference-only budget differs")
    collection = bundle["collection"]
    require(set(collection) == {"alignment_report_sha256", "completion_sha256", "collection_seconds"}, "collection schema differs")
    require(collection["alignment_report_sha256"] == entry["report"]["sha256"] and collection["completion_sha256"] == entry["completion_sha256"], "once-collected report pin differs")
    require(number(collection["collection_seconds"]) <= 180, "collection bound exceeded")
    claim = bundle["claim"]
    require(set(claim) == {"plan_sha256", "out", "retry"} and claim["plan_sha256"] == entry["plan_sha256"] and claim["retry"] is False and
            Path(claim["out"]).is_absolute() and Path(claim["out"]).name == Path(entry["report"]["path"]).parent.name, "collection claim mismatch")
    require(files["prepare_done.json"]["plan_sha256"] == entry["plan_sha256"] and number(files["prepare_done.json"]["elapsed_seconds"]) <= 180, "preparation bound differs")
    equal(report["controller_seconds"], complete["elapsed_seconds"], "controller clock differs")
    return dict(seed=seed, cells=cells, arms={arm: {key: value for key, value in data.items() if key not in ("capture", "audit")} for arm, data in arms.items()},
        paired={arm: pair(arms["ALIGNED"]["capture"]["records"], arms[arm]["capture"]["records"]) for arm in ("SWAPPED", "NO_PARENT")},
        costs=costs, lesson_token_costs={key: preflight[key] for key in ("lesson_literal_tokens", "lesson_multiset_tokens_per_lesson_arm", "equal_lesson_multiset", "individual_lesson_lengths_equal")},
        spans=dict(prepare_seconds=files["prepare_done.json"]["elapsed_seconds"], controller_seconds=complete["elapsed_seconds"],
            collection_seconds=collection["collection_seconds"], holder_launch_through_collection=bundle["holder_span"]),
        input_pins=entry)


def reduce_cohort(bundles, apis):
    require(len(bundles) == 3 and all(type(bundle["entry"]["seed"]) is int for bundle in bundles) and sorted(bundle["entry"]["seed"] for bundle in bundles) == [0, 1, 2], "complete three original seeds required")
    seeds = [reduce_seed(bundle, apis) for bundle in sorted(bundles, key=lambda value: value["entry"]["seed"])]
    cells = {state: cell for seed in seeds for state, cell in seed["cells"].items()}
    gate = feasibility(cells)
    equal(gate, apis["core"].threshold_vector(cells), "independent protocol/core feasibility mismatch")
    totals = {key: sum(seed["costs"][key] for seed in seeds) for key in seeds[0]["costs"]}
    require(totals["calls"] <= 312 and totals["fits"] == totals["updates"] == 0, "campaign budget differs")
    return dict(schema=SCHEMA, seeds=seeds, feasibility=gate, total_costs=totals, automatic_pass=False, fit_authorized=False,
        limitations=["Three learner roots, not independent tasks; report absolute A/S/N and both paired contrasts, no pooled causal estimate.",
            "Immediate alignment of lesson-to-raw-restatement package; SWAPPED may interfere or help. No mediation, persistence, parenting amortization or H1/H2 claim.",
            "P-C-P-C for seeds0/2 and C-P-C-P for seed1 confounds order with learner; repetition strata do not establish learning or equal difficulty.",
            "Restatement correctness is a frozen lexical operation/scope screen against the delivered lesson, not semantic proof.",
            "Same task/lesson multiset does not match trajectories, raw restatements, output lengths or total tokens; NO_PARENT is not token matched.",
            "Recorded native prompt IDs/routes/custody are joined without tokenizer, hardware, model or tensor revalidation; raw CPU core/world/parser replay is not native replay.",
            "Generation/arm spans nest inside controller; prepare and collection are separate. Holder span is null if not supplied, never inferred as zero or GPU-active time.",
            "All16 slots include invalid/uncalled records; full material excludes RESTATE. Exposed DEV feasibility is not a writer authorization or automatic promotion."])


def markdown(report):
    lines = ["# Parenting alignment independent reduction", "", "| Seed | Arm | RESTATE /4 | PROCESS /16 | EXECUTED /16 | FAITHFUL /16 | FULL /16 | Calls |", "|---|---|---|---|---|---|---|---|"]
    for seed in report["seeds"]:
        for arm in ARMS:
            cell = seed["arms"][arm]["counts"]
            lines.append("| " + " | ".join(str(value) for value in (seed["seed"], arm, cell["RESTATE"] if cell["RESTATE"] is not None else "N/A", *[cell[key] for key in ENDPOINTS], cell["calls"])) + " |")
    lines += ["", "Feasibility vector: " + encoded(report["feasibility"]["vector"]), "", "Feasibility conjunction: " + str(report["feasibility"]["feasibility_pass"]), "", "Costs: " + encoded(report["total_costs"]), "", *["- "+value for value in report["limitations"]]]
    return "\n".join(lines)+"\n"


def run(manifest_path, manifest_sha256, out, module_dir, source_root, protocol_path):
    manifest = read(pinned(manifest_path, manifest_sha256))
    require(set(manifest) == {"schema", "seeds"} and manifest["schema"] == INPUT_SCHEMA, "closed manifest schema differs")
    out = Path(out).absolute()
    require(not out.exists(), "fresh write-once output required")
    for entry in manifest["seeds"]:
        for path in (Path(entry["root"]), Path(entry["report"]["path"]).parent):
            require(not out.resolve().is_relative_to(path.resolve()) and not path.resolve().is_relative_to(out.resolve()), "output overlaps preserved evidence")
    apis = load_sources(module_dir, source_root, protocol_path)
    result = reduce_cohort([load_bundle(entry) for entry in manifest["seeds"]], apis)
    result.update(manifest_sha256=manifest_sha256, reducer_sha256=digest(__file__), core_sha256=CORE_PIN, runner_sha256=RUNNER_PIN, protocol_sha256=PROTOCOL_PIN)
    out.mkdir()
    for name, text in (("analysis.json", json.dumps(result, sort_keys=True, indent=2, allow_nan=False)+"\n"), ("analysis.md", markdown(result))):
        with (out/name).open("x") as stream:
            stream.write(text)
    return {name: digest(out/name) for name in ("analysis.json", "analysis.md")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("manifest", "manifest-sha256", "out", "source-root", "protocol-path"):
        parser.add_argument("--"+name, required=True)
    parser.add_argument("--module-dir", default="/tmp")
    args = vars(parser.parse_args())
    args["manifest_path"] = args.pop("manifest")
    print(json.dumps(run(**args), sort_keys=True))


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    main()
