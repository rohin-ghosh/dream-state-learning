"""Local byte-bound CPU replay of the fixed three post-memory pairs; no native calls."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import tarfile
from types import ModuleType

ARCHIVE_PIN = "a94ce39aabcc8eec321d3fdb149515714bb4d79040efdf491c1ae44397ff2548"
CORE_PIN = "030c97c57a962a74a5b97bd66550096dedc2bab288d690b2c89808d2ec84474b"
RUNNER_PIN = "c8ca3444c604aebbf5cd0b134f98a86cf79c3521332fff841e371a9986c41942"
PROJECTOR_PIN = "2c5538f5b63cbb4e592f40822561b4d62595ab3c9d7d193f084b91f9a064e8ef"
SCORE_PINS = (
    "55efbfae43cf3f3e00a2d5ee5032c476090beb4ae0faf7e9acb1cbad29220e84",
    "b735953ec0b45b877f26618a1b2df4deac207720932cd507e326298aa96cb63a",
    "a29de891d9eb3e966ae8d0ad24da3c2c36e764d34bc9154b076d92d8fb59e6ef",
)
MEMORY_PINS = (
    "b56a0caa16259e29860efa284d283610ab9bfa9064c64f121fe7cc34266b72bf",
    "5fe7638aa86e718b36ea00f9a97b9e36acbed4b464c968737acbc86447c71979",
    "a0182417e86e85ab6a874c7e98d77fd5952e2bb036fe1a2e35d6e7289ecb0cef",
)
METRICS = ("production_eligible", "content_correct", "strict_canonical")
ARMS = ("WRITE", "LR0")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def file_sha(path):
    with open(path, "rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def equal(actual, expected, message):
    require(canonical(actual) == canonical(expected), message)


def unique(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key")
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError("nonfinite JSON constant: " + value)


def finite_tree(value):
    if type(value) is float:
        require(math.isfinite(value), "nonfinite JSON number")
    elif type(value) is dict:
        for child in value.values():
            finite_tree(child)
    elif type(value) is list:
        for child in value:
            finite_tree(child)


def decode(raw):
    result = json.loads(raw, object_pairs_hook=unique, parse_constant=reject_constant)
    finite_tree(result)
    return result


def load_module(path, pin):
    raw = Path(path).read_bytes()
    require(sha(raw) == pin, "local source pin mismatch: " + str(path))
    module = ModuleType(Path(path).stem)
    exec(compile(raw, str(path), "exec"), module.__dict__)
    return module


class Archive:
    def __init__(self, path, pin=None):
        if pin:
            require(file_sha(path) == pin, "archive pin mismatch")
        self.handle = tarfile.open(path, "r:")
        self.members = {}
        try:
            for member in self.handle.getmembers():
                name = member.name.rstrip("/")
                require(name not in self.members, "duplicate archive member")
                require(not PurePosixPath(name).is_absolute() and ".." not in PurePosixPath(name).parts,
                        "unsafe archive member")
                self.members[name] = member
        except Exception:
            self.handle.close()
            raise

    def raw(self, name, pin=None):
        member = self.members[name]
        require(member.isfile() and member.size < 32_000_000 and name.endswith(".json"),
                "only bounded JSON evidence may be read")
        raw = self.handle.extractfile(member).read()
        require(pin is None or sha(raw) == pin, "member pin mismatch: " + name)
        return raw

    def read(self, name, pin=None):
        return decode(self.raw(name, pin))

    def close(self):
        self.handle.close()


def triple(value):
    if type(value) is list and len(value) == 3 and all(type(part) is int for part in value):
        return tuple(value)
    return None


def bank(dataset):
    rows = dataset["rows"]
    require(len({row["row_id"] for row in rows}) == len(rows), "duplicate admitted row")
    targets, triples = {}, {}
    for row in rows:
        require(type(row["raw_target"]) is str and sha(row["raw_target"].encode()) == row["target_sha256"],
                "target byte pin mismatch")
        parsed = decode(row["raw_target"])
        values = triple(parsed.get("try"))
        require(values is not None, "invalid training triple")
        targets.setdefault(row["target_sha256"], []).append(row["row_id"])
        triples.setdefault(values, []).append(row["row_id"])
    return targets, triples


def reduce_capture(capture, dataset, core, dependencies):
    audit = core.audit_capture(capture, dependencies=dependencies)
    equal(capture["contract"], core.contract(dependencies), "contract differs")
    targets, triples = bank(dataset)
    semantic_targets = {}
    for target in dataset["rows"]:
        semantic_targets.setdefault(canonical(decode(target["raw_target"])), []).append(target["row_id"])
    ledger = []
    for episode in capture["episodes"]:
        for turn in episode["turns"]:
            execution, score = turn["execution"], turn["score"]
            raw_wake = turn["wake"]["response"]["raw"]
            raw_record = turn["record"]["response"]["raw"] if turn["record"] else None
            action_values = triple(execution["values"]) if execution else None
            record_values = triple(score["parsed"].get("try")) if score and type(score["parsed"]) is dict else None
            target_hash = sha(raw_record.encode()) if raw_record is not None else None
            row = dict(episode_id=episode["episode_id"], tick=turn["tick"], cue=episode["cue_stratum"],
                       slot=f'{episode["episode_id"]}#t{turn["tick"]}', status=turn["status"],
                       wake_raw=raw_wake, wake_finish=turn["wake"]["response"]["finish_reason"],
                       errors=turn["errors"], execution=execution, score=score, record_raw=raw_record,
                       record_sha256=target_hash, executed=execution is not None, record_called=turn["record"] is not None,
                       action_training_match=action_values in triples if execution else None,
                       action_example_match=action_values == (2, 5, 9) if execution else None,
                       action_matching_rows=triples.get(action_values, []),
                       record_training_triple_match=record_values in triples if record_values else None,
                       record_matching_rows=triples.get(record_values, []),
                       target_byte_match=target_hash in targets if raw_record is not None else None,
                       target_matching_rows=targets.get(target_hash, []),
                       typed_target_match=canonical(score["parsed"]) in semantic_targets if score and score["parsed"] is not None else None,
                       typed_target_matching_rows=semantic_targets.get(canonical(score["parsed"]), []) if score else [],
                       record_request=turn["record"]["request"] if turn["record"] else None,
                       wake_request=turn["wake"]["request"])
            for metric in METRICS:
                row[metric] = score[metric] if score else None
            row["invalid_space_separated_try"] = not row["executed"] and bool(
                re.search(r"(?m)^ACT:\s*TRY\s+-?\d+\s+-?\d+\s+-?\d+\s*$", raw_wake))
            ledger.append(row)
    require(len(ledger) == 16 and len({row["slot"] for row in ledger}) == 16, "missing/duplicate scheduled slot")
    groups = {"all": ledger}
    for cue in ("example_present", "example_absent"):
        groups[cue] = [row for row in ledger if row["cue"] == cue]
        require(len(groups[cue]) == 8, "cue denominator differs")
        for tick in (1, 2):
            groups[f"{cue}/turn{tick}"] = [row for row in groups[cue] if row["tick"] == tick]
            require(len(groups[f"{cue}/turn{tick}"]) == 4, "cue/turn denominator differs")
    for tick in (1, 2):
        groups[f"turn{tick}"] = [row for row in ledger if row["tick"] == tick]
    groups["nontraining_nonexample_actions"] = [row for row in ledger if row["executed"] and
                                               not row["action_training_match"] and not row["action_example_match"]]
    return dict(audit=audit, summary=capture["summary"], rows=ledger,
                groups={name: summarize(rows) for name, rows in groups.items()})


def summarize(rows):
    result = dict(slots=len(rows), executions=sum(row["executed"] for row in rows),
                  record_calls=sum(row["record_called"] for row in rows))
    for metric in METRICS:
        numerator = sum(row[metric] is True for row in rows)
        result[metric] = dict(count=numerator, over_slots=numerator / len(rows) if rows else None,
                             over_records=numerator / result["record_calls"] if result["record_calls"] else None)
    for flag in ("action_training_match", "action_example_match", "record_training_triple_match", "target_byte_match", "typed_target_match"):
        result[flag] = dict(matches=sum(row[flag] is True for row in rows),
                            assessed=sum(row[flag] is not None for row in rows))
    result["target_match_by_eligibility"] = dict(Counter(
        f'{"match" if row["target_byte_match"] else "nonmatch"}/{"eligible" if row["production_eligible"] else "rejected"}'
        for row in rows if row["record_called"]))
    result["invalid_wake_reasons"] = dict(Counter(error for row in rows if not row["executed"] for error in row["errors"]))
    result["space_separated_invalid"] = sum(row["invalid_space_separated_try"] for row in rows)
    result["wake_finish"] = dict(Counter(row["wake_finish"] for row in rows))
    result["record_errors"] = dict(Counter(error for row in rows if row["score"] for error in row["score"]["production_errors"]))
    result["record_formats"] = dict(Counter(row["score"]["format"] for row in rows if row["score"]))
    result["typed_target_match_by_eligibility"] = dict(Counter(
        f'{"match" if row["typed_target_match"] else "nonmatch"}/{"eligible" if row["production_eligible"] else "rejected"}'
        for row in rows if row["record_called"]))
    result["field_correct"] = {field: sum(row["score"] is not None and row["score"]["field_correct"][field] is True for row in rows)
                               for field in ("try", "observed", "predicted", "relation")}
    result["executed_triples"] = dict(Counter(canonical(row["execution"]["values"]) for row in rows if row["executed"]))
    return result


def paired(write, control):
    require([row["slot"] for row in write] == [row["slot"] for row in control], "paired initial schedule differs")
    result = {}
    for metric in METRICS:
        groups = {name: [] for name in ("WRITE_only", "LR0_only", "both", "neither")}
        for first, second in zip(write, control):
            require(first["cue"] == second["cue"], "paired cue differs")
            left, right = first[metric] is True, second[metric] is True
            group = "both" if left and right else "WRITE_only" if left else "LR0_only" if right else "neither"
            groups[group].append(first["slot"])
        result[metric] = groups
    result["experience"] = [dict(slot=first["slot"], cue=first["cue"], tick=first["tick"],
        same_wake_prompt=first["wake_request"]["input_messages"] == second["wake_request"]["input_messages"],
        same_raw_wake=first["wake_raw"] == second["wake_raw"],
        same_executed_facts=({key: first["execution"][key] for key in ("values", "observed", "predicted")} ==
                             {key: second["execution"][key] for key in ("values", "observed", "predicted")})
                            if first["executed"] and second["executed"] else None)
        for first, second in zip(write, control)]
    return result


def native_bytes(archive, directory, capture, plan, score, arm):
    identity = archive.read(directory + "/identity.json")
    equal(capture["binding"], dict(kind="pinned_native_capture", identity=identity), "capture identity differs")
    for key, expected in dict(core_state=f'perception_seed{plan["seed"]}_{arm}', seed=plan["seed"], state=arm,
                              adapter_files=plan["adapters"][arm], lora_request=plan["routes"][arm],
                              model_files=plan["model_files"], core=score["core"], memory=score["memory"],
                              params=plan["params"], engine=plan["engine"], model=plan["model"]).items():
        equal(identity[key], expected, "native identity field differs: " + key)
    closed = archive.read(directory + "/closed.json")
    for name, pin in closed["files"].items():
        archive.raw(directory + "/" + name, pin)
    calls = [event for event in capture["events"] if event["kind"] == "call"]
    expected_names = {"identity.json", "formation.json"} | {
        f"{index:02d}{suffix}" for index in range(len(calls)) for suffix in (".request.json", ".response.json")}
    equal(sorted(closed["files"]), sorted(expected_names), "raw file inventory differs")
    costs = dict(calls=len(calls), wake_calls=0, record_calls=0, fits=0, updates=0,
                 prompt_tokens=0, output_tokens=0, generation_seconds=0.0)
    for index, event in enumerate(calls):
        request = archive.read(f"{directory}/{index:02d}.request.json")
        response = archive.read(f"{directory}/{index:02d}.response.json")
        core_request = event["request"]
        equal(request["core_request"], core_request, "request source join differs")
        equal(request["messages"], core_request["input_messages"], "message bytes differ")
        equal(request["call_id"], f"{index:02d}", "call order differs")
        for supplied in (request["lora_request"], response["lora_request"]):
            equal(supplied, identity["lora_request"], "adapter route differs")
        equal(request["params"], dict(plan["params"], max_tokens=core_request["max_output_tokens"]), "sampling differs")
        for key, value in request["native"].items():
            equal(response[key], value, "native prompt metadata differs")
        equal(response["actual_prompt_token_ids"], request["native"]["prompt_token_ids"], "prompt token prefix differs")
        tokens = response["output_token_ids"]
        cap = core_request["max_output_tokens"]
        require(type(tokens) is list and 0 < len(tokens) <= cap and all(type(token) is int and token >= 0 for token in tokens), "bad output tokens")
        require(all(type(token) is int and token >= 0 for token in response["actual_prompt_token_ids"]), "bad prompt tokens")
        require(len(response["actual_prompt_token_ids"]) + cap <= plan["engine"]["max_model_len"], "context cap differs")
        require(type(response["text"]) is str and response["text"] == response["decoded_output"], "output byte join differs")
        require(response["finish_reason"] in ("stop", "length") and
                (response["finish_reason"] != "length" or len(tokens) == cap), "finish/cap differs")
        equal(event["response"], dict(request_id=core_request["request_id"], state=capture["state"],
              raw=response["text"], finish_reason=response["finish_reason"], native_response=response), "native/event response join differs")
        require(all(type(response[key]) in (float, int) and math.isfinite(response[key]) for key in ("started", "ended")) and
                response["ended"] >= response["started"], "bad timing")
        costs[core_request["kind"] + "_calls"] += 1
        costs["prompt_tokens"] += len(response["actual_prompt_token_ids"])
        costs["output_tokens"] += len(tokens)
        costs["generation_seconds"] += response["ended"] - response["started"]
    equal({key: closed[key] for key in costs}, costs, "closed costs disagree")
    equal(score["costs"][arm], costs, "report costs disagree")
    return costs


def analyze(post, memory, scores_dir, source_root):
    core = load_module("/tmp/astra_post_memory_formation_core_20260913.py", CORE_PIN)
    projector = load_module("/tmp/astra_real_record_memory_core_20260913.py", PROJECTOR_PIN)
    require(file_sha("/tmp/astra_post_memory_formation_run_20260913.py") == RUNNER_PIN, "runner pin differs")
    dependencies = core.load_dependencies(source_root)
    results = []
    for seed in range(3):
        root = f"post_memory_formation_seed{seed}_20260913_attempt1"
        memory_root = f"real_record_memory_seed{seed}_20260913_attempt1"
        raw = (Path(scores_dir) / (root + "_collected") / "scores.json").read_bytes()
        require(sha(raw) == SCORE_PINS[seed], "supplied score pin mismatch")
        equal(post.read(root + "_collected/scores.json", SCORE_PINS[seed]), decode(raw), "archive/external score differs")
        score = decode(raw)
        equal(score["seed"], seed, "seed mismatch")
        collection = post.read(root + "_collected/collection.json")
        equal(collection, dict(scores_sha256=SCORE_PINS[seed], completion_sha256=score["completion_sha256"]), "collection mismatch")
        plan = post.read(root + "/plan.json", score["plan_sha256"])
        complete = post.read(root + "/capture_complete.json", score["completion_sha256"])
        equal(plan["seed"], seed, "plan seed mismatch")
        require(Path(plan["root"]).name == root, "root identity mismatch")
        equal(plan["self_sha256"], RUNNER_PIN, "runner binding mismatch")
        equal(score["core"]["sha256"], CORE_PIN, "core binding mismatch")
        for key in ("memory", "core"):
            equal(score[key], plan["specification"][key], "spec binding mismatch")
        for key, plan_key in (("adapter_files", "adapters"), ("routes", "routes"), ("model_files", "model_files")):
            equal(score[key], plan[plan_key], "plan/report identity mismatch")
        equal(complete["plan_sha256"], score["plan_sha256"], "completion/plan mismatch")
        for key in ("fits", "updates"):
            equal(score[key], 0, "unexpected new fit/update")
            equal(complete[key], 0, "unexpected completion fit/update")
        memory_binding = score["memory"]
        require(Path(memory_binding["root"]).name == memory_root, "wrong memory root")
        equal(memory_binding["scores"]["sha256"], MEMORY_PINS[seed], "wrong memory scores pin")
        memory_score = memory.read(memory_root + "_collected/scores.json", MEMORY_PINS[seed])
        memory_collection = memory.read(memory_root + "_collected/collection.json", memory_binding["collection"]["sha256"])
        equal(memory_collection["scores_sha256"], MEMORY_PINS[seed], "memory collection score join")
        memory_plan = memory.read(memory_root + "/plan.json", memory_binding["plan_sha256"])
        memory_complete = memory.read(memory_root + "/capture_complete.json", memory_binding["completion_sha256"])
        equal(memory_score["seed"], seed, "memory seed mismatch")
        equal(memory_complete["plan_sha256"], memory_binding["plan_sha256"], "memory plan completion join")
        equal(memory_score["plan_sha256"], memory_binding["plan_sha256"], "memory score plan join")
        equal(memory_score["completion_sha256"], memory_binding["completion_sha256"], "memory score completion join")
        equal(memory_plan["specification"]["memory"]["sha256"], PROJECTOR_PIN, "projector binding mismatch")
        dataset = memory.read(memory_root + "/dataset.json", memory_plan["input_hashes"]["dataset.json"])
        original_capture = memory.read(memory_root + "/capture.json", memory_plan["input_hashes"]["capture.json"])
        equal(projector.project_capture(original_capture, source_root=source_root), dataset, "admitted bank differs from original source replay")
        equal(len(dataset["rows"]), (14, 8, 8)[seed], "admission denominator mismatch")
        captures, arms = [], {}
        for arm in ARMS:
            adapter_inventory = {name.removeprefix("adapter/"): pin
                                 for name, pin in memory_complete["stages"][arm + "_fit"].items()
                                 if name.startswith("adapter/")}
            equal(plan["adapters"][arm], adapter_inventory, "upstream completed adapter inventory differs")
            equal(plan["routes"][arm]["path"], memory_binding["root"] + "/run/" + arm + "_fit/adapter",
                  "route is not the bound completed memory adapter")
            directory = root + "/run/" + arm
            for name, pin in complete["stages"][arm].items():
                if name.endswith(".json"):
                    post.raw(directory + "/" + name, pin)
            capture = post.read(directory + "/formation.json")
            equal(capture["state"], f"perception_seed{seed}_{arm}", "wrong captured state")
            equal(plan["core_contract"], core.contract(dependencies), "plan core contract differs")
            arms[arm] = reduce_capture(capture, dataset, core, dependencies)
            arms[arm]["costs"] = native_bytes(post, directory, capture, plan, score, arm)
            captures.append(capture)
        equal(core.compare_states(captures, dependencies=dependencies), score["comparison"], "reported comparison differs from replay")
        calls = sum(arms[arm]["costs"]["calls"] for arm in ARMS)
        equal(calls, score["calls"], "score call total differs")
        equal(calls, complete["calls"], "completion call total differs")
        equal(score["controller_elapsed_seconds"], complete["elapsed_seconds"], "controller time differs")
        groups = {}
        for name in arms["WRITE"]["groups"]:
            if name == "nontraining_nonexample_actions":
                continue
            def selected(row):
                return name == "all" or name == row["cue"] or name == f'turn{row["tick"]}' or name == f'{row["cue"]}/turn{row["tick"]}'
            groups[name] = paired([row for row in arms["WRITE"]["rows"] if selected(row)],
                                  [row for row in arms["LR0"]["rows"] if selected(row)])
        targets, triples = bank(dataset)
        results.append(dict(seed=seed, score_sha256=SCORE_PINS[seed], plan_sha256=score["plan_sha256"],
            completion_sha256=score["completion_sha256"], memory_score_sha256=MEMORY_PINS[seed],
            dataset_sha256=memory_plan["input_hashes"]["dataset.json"], memory_plan_sha256=memory_binding["plan_sha256"],
            bank=dict(admitted=len(dataset["rows"]), distinct_targets=len(targets), distinct_triples=len(triples),
                      triples=[list(values) for values in triples]), arms=arms, paired=groups,
            prior_memory=dict(totals=memory_score["summary"]["totals"],
                              original_retention=memory_score["summary"]["original_retention"]),
            controller_elapsed_seconds=score["controller_elapsed_seconds"]))
    return dict(schema="astra_post_memory_local_raw_audit_20260913_v1", archive_sha256=ARCHIVE_PIN,
                core_sha256=CORE_PIN, projector_sha256=PROJECTOR_PIN, dependencies=dependencies.manifest,
                seeds=results, automatic_pass=False, native_recollection=False,
                qualification="Local replay and byte joins only; matched initial tasks, not identical experiences; descriptive paired learning, not strong H1.")


def markdown(report):
    lines = ["# Post-memory formation: local raw audit — 2026-09-13", "",
             "Pinned archive, all six captures and all three admitted banks replayed locally with frozen cores. "
             "Request/response bytes, source-execution joins, routes and token/call accounting agree. No native calls, model/tokenizer loads or recollection.", "",
             "|Seed|Arm|Eligible /16 (of 8 records)|Content|Canonical strict|Action training/example matches|Exact old-target bytes|Record training-triple matches|",
             "|---|---|---|---|---|---|---|---|"]
    for seed in report["seeds"]:
        for arm in ARMS:
            group = seed["arms"][arm]["groups"]["all"]
            lines.append(f'|{seed["seed"]}|{arm}|{group["production_eligible"]["count"]}/16|{group["content_correct"]["count"]}|'
                         f'{group["strict_canonical"]["count"]}|{group["action_training_match"]["matches"]}/{group["action_example_match"]["matches"]}|'
                         f'{group["target_byte_match"]["matches"]}|{group["record_training_triple_match"]["matches"]}|')
    lines += ["", "## Raw failures, copying and coverage"]
    for seed in report["seeds"]:
        number = seed["seed"]
        lines.append(f'\n### Seed {number} — {seed["bank"]["admitted"]} admitted rows; '
                     f'{seed["bank"]["distinct_targets"]} distinct targets, {seed["bank"]["distinct_triples"]} distinct triples')
        for arm in ARMS:
            entry = seed["arms"][arm]
            group = entry["groups"]["all"]
            unseen = entry["groups"]["nontraining_nonexample_actions"]
            lines.append(f'- {arm}: executed triples {canonical(group["executed_triples"])}; target match × source eligibility '
                         f'{canonical(group["target_match_by_eligibility"])}. Non-training/non-example executions '
                         f'{unseen["executions"]}, eligible {unseen["production_eligible"]["count"]}; '
                         + ('untested.' if unseen["executions"] == 0 else 'descriptive within reached subset.'))
            lines.append(f'- {arm} typed full-target match × source eligibility (format ignored, no value repair): '
                         f'{canonical(group["typed_target_match_by_eligibility"])}; correct fields {canonical(group["field_correct"])}.')
            lines.append(f'- {arm} invalid-wake reasons: {canonical(group["invalid_wake_reasons"])}; '
                         f'space-separated TRY raw patterns {group["space_separated_invalid"]}; finish reasons {canonical(group["wake_finish"])}. '
                         f'Record errors: {canonical(group["record_errors"])}; formats {canonical(group["record_formats"])}.')
            examples = sorted({row["wake_raw"] for row in entry["rows"] if not row["executed"]})
            lines.append(f'- {arm} distinct invalid raw wakes (JSON-escaped, no repair): {canonical(examples)}')
        pair = seed["paired"]["all"]["production_eligible"]
        lines.append(f'- Paired production WRITE-only/LR0-only/both/neither: '
                     f'{len(pair["WRITE_only"])}/{len(pair["LR0_only"])}/{len(pair["both"])}/{len(pair["neither"])}. '
                     f'WRITE-only slots: {canonical(pair["WRITE_only"])}; LR0-only: {canonical(pair["LR0_only"])}.')
        for cue in ("example_present", "example_absent"):
            for tick in (1, 2):
                group_name = f"{cue}/turn{tick}"
                counts = [seed["arms"][arm]["groups"][group_name]["production_eligible"]["count"] for arm in ARMS]
                lines.append(f'- {group_name}: WRITE {counts[0]}/4, LR0 {counts[1]}/4.')
        for arm in ARMS:
            cost = seed["arms"][arm]["costs"]
            lines.append(f'- {arm} costs: {cost["calls"]} calls, {cost["prompt_tokens"]} prompt + {cost["output_tokens"]} output tokens; '
                         f'{cost["generation_seconds"]:.3f}s generation, zero fits/updates.')
        regression = seed["prior_memory"]["original_retention"]["WRITE"]["held"]["regressed"]
        lines.append(f'- Pair controller elapsed {seed["controller_elapsed_seconds"]:.3f}s. Prior WRITE held regressions: {len(regression)}/48; not erased by this endpoint.')
        errors = [dict(slot=row["slot"], action=row["execution"]["values"], prior=row["execution"]["predicted"],
                       raw_record=row["record_raw"], errors=row["score"]["production_errors"])
                  for row in seed["arms"]["LR0"]["rows"] if row["record_called"] and not row["production_eligible"]]
        lines.append(f'- LR0 rejected record raw evidence: {canonical(errors)}')
        experience = seed["paired"]["all"]["experience"]
        lines.append(f'- Among jointly executed slots, identical action/outcome/prior: '
                     f'{sum(row["same_executed_facts"] is True for row in experience)}/'
                     f'{sum(row["same_executed_facts"] is not None for row in experience)}; identical first-/second-turn wake prompts: '
                     f'{sum(row["same_wake_prompt"] for row in experience if row["tick"] == 1)}/8 and '
                     f'{sum(row["same_wake_prompt"] for row in experience if row["tick"] == 2)}/8.')
    lines += ["", "## Interpretation and limits",
              "- Each arm has 8 example-present and 8 example-absent opportunities, with 4 per cue × turn. Uncalled records remain missing; conditional record rates are N/A when no records were called.",
              "- Execution triples and output target/triple overlap are separate diagnostics. Repetition is not causal proof of retrieval. A byte-identical old target can still agree with a new source when facts coincide; that does not distinguish recall from reconstruction.",
              "- Fresh task IDs do not ensure fresh triples. Record prompts expose current executed facts. Non-training/non-example execution coverage, rather than task-ID novelty, bounds the fidelity evidence.",
              "- Cue assignment is fixed by episode ID, not randomized. Any cue-associated failure is observational; exact syntax errors are independently reproducible, but their causal origin is not identified.",
              "- WRITE/LR0 share initial tasks and schedule, not necessarily action, outcome, prior or second-turn history. Full paired rows, field scores, raw outputs and source requests are in JSON. Repeated triples/turns are not independent learners; only three learner pairs.",
              "- Prior memory acquisition coexists with held regressions 3/11/31 and intact canaries. No stable-substrate, strong H1, H2, recursive-learning or automatic-pass claim.",
              "- Local byte joins reuse archived native token/route attestations, not new tokenization, model execution or independent hardware-identity checks. No future launch decision is made here."]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--post-archive", required=True)
    parser.add_argument("--memory-archive", required=True)
    parser.add_argument("--scores-dir", required=True)
    parser.add_argument("--source-root", default="/tmp/astra_level1_real_record_source_20260913_attempt1")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    require(not Path(args.out).exists(), "output already exists")
    post = Archive(args.post_archive, ARCHIVE_PIN)
    memory = Archive(args.memory_archive)
    try:
        report = analyze(post, memory, args.scores_dir, args.source_root)
    finally:
        post.close()
        memory.close()
    output = Path(args.out)
    output.mkdir()
    with (output / "analysis.json").open("x") as stream:
        stream.write(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n")
    with (output / "analysis.md").open("x") as stream:
        stream.write(markdown(report))
    print(canonical({name: file_sha(output / name) for name in ("analysis.json", "analysis.md")}))


if __name__ == "__main__":
    main()
