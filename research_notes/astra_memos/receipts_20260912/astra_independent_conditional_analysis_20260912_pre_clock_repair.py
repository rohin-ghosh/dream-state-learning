"""Offline raw-receipt analysis, not tokenizer/logit verification or a science gate."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys


STATES = ("OFF", "AUTH", "DERANGED")
MAPS = ("AUTH", "DERANGED")
OPERATIONS = ("PROSPECT", "REVISE")
ORDER = tuple(f"{state}_{phase}" for state in STATES for phase in ("generate", "score"))
ASSAY = "conditional-dual-map-fixed-endpoints-v2-20260912"
CONTRAST = "dual-map-belief-endpoints-v2"
MANIFEST_SHA = "5a26f0da17d53518aa00c80bce3bfbfbe76ef61e65ea5ebc781f797dd33190a6"
CANDIDATE_SHA = "5d1644b90ff7621ee121aba65be7dd7cae7f15168f5a3c3a09a1bc9aa9a7af8c"
PREFIX = "astra_diagnostics/astra_conditional_behavior_20260912_attempt2/readouts_root0_attempt1"
MANIFEST_PATH = "/tmp/astra_conditional_readout_manifest_root0_20260912.json"
CANDIDATE_PATH = "/tmp/astra_conditional_native_preps_20260912/astra_diagnostics/astra_conditional_behavior_20260912_attempt2/material/candidate.json"
COPY_ACTIONS = ("-sroa", "-simplifycfg", "-instcombine", "-licm", "-loop-unroll", "-adce", "-bdce", "-argpromotion")
COST_KEYS = ("requests", "native_input_tokens", "native_output_tokens", "output_token_ceiling",
             "candidate_forwards", "scored_target_tokens", "padded_forward_tokens", "call_seconds")
BOOL_METRICS = ("strict_surface", "auth_joint_semantic", "own_map_joint_semantic",
                "auth_strict_joint", "own_map_strict_joint")
FLIPS = {"goal": ("PREDICT_ACTION", "PREDICT_OUTCOME", "ACT"), "belief": ("PREDICT_ACTION", "ACT"),
         "outcome": ("COMPARE", "POLICY", "NEXT"), "prior_action": ("NEXT",)}
LIMITS = [
    "Independent arithmetic/parsing over stored raw receipts; no existing reducer is imported or executed.",
    "Cannot independently recompute logits, native tokenization, EOS identity, causal forwards, or token-ID decoding.",
    "Complete-candidate sums use stored per-token logprob scalars, including the stored final EOS position; no length normalization.",
    "Text/ID correspondence and numerical logprobs remain dependent on the original capture and Main's custody checks.",
    "PROSPECT maps share 16 twins; REVISE's reversed effects are exact negatives, not independent replications.",
    "OFF is shared across comparisons. Technical PARTIAL is not scientific zero; absent denominators stay absent.",
    "No L1, H1, Q0, confirmation, clean-lineage or composition verdict. Composition is UNTRAINED_FUTURE_ASSAY.",
    "Local hashes establish byte consistency, not provenance truth, current GPU vacancy or lease authority.",
]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def encoded(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n").encode()


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def value_hash(value):
    return sha(encoded(value))


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def decode(payload):
    def invalid(value):
        raise ValueError(f"nonfinite JSON constant: {value}")
    return json.loads(payload, object_pairs_hook=unique_object, parse_constant=invalid)


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def same(expected, actual, label):
    if isinstance(expected, dict):
        require(isinstance(actual, dict), f"{label}: not an object")
        for key, value in expected.items():
            require(key in actual, f"{label}: missing {key}")
            same(value, actual[key], f"{label}.{key}")
    elif isinstance(expected, list):
        require(isinstance(actual, list) and len(expected) == len(actual), f"{label}: list length differs")
        for index, (left, right) in enumerate(zip(expected, actual)):
            same(left, right, f"{label}[{index}]")
    elif type(expected) is float:
        require(finite(actual) and math.isclose(expected, actual, rel_tol=0, abs_tol=1e-8), f"{label}: number differs")
    else:
        require(type(expected) is type(actual) and expected == actual, f"{label}: value differs")


class Snapshot:
    def __init__(self, files, issues=()):
        self.files = files
        self.issues = list(issues)

    def read(self, name):
        require(name in self.files, f"missing evidence: {name}")
        return decode(self.files[name])

    def digest(self, name):
        require(name in self.files, f"missing evidence: {name}")
        return sha(self.files[name])


def check(report, label, operation):
    try:
        return operation()
    except (ValueError, KeyError, TypeError, IndexError, OverflowError) as error:
        report["issues"].append(f"{label}: {type(error).__name__}: {error}")
        return None


def targets(case, assigned_map):
    inputs = case["inputs"]
    if case["operation"] == "PROSPECT":
        eligible = [action for action in inputs["actions"]
                    if (inputs["belief"][action] == inputs["goal"]) == (assigned_map == "AUTH")]
        require(len(eligible) == 1, "nonunique consequence-relative target")
        action = eligible[0]
        return {"PREDICT_ACTION": action, "PREDICT_OUTCOME": inputs["belief"][action], "ACT": action}
    require(case["operation"] == "REVISE", "unknown operation")
    keep = (inputs["expected"] == inputs["observed"]) == (assigned_map == "AUTH")
    action = inputs["prior_action"] if keep else next(action for action in inputs["actions"] if action != inputs["prior_action"])
    return {"COMPARE": "MATCH" if keep else "MISMATCH", "POLICY": "KEEP" if keep else "SWITCH", "NEXT": action}


def target_text(case, assigned_map):
    fields = targets(case, assigned_map)
    if case["operation"] == "PROSPECT":
        return f"PREDICT: {fields['PREDICT_ACTION']} -> {fields['PREDICT_OUTCOME']}\nACT: {fields['ACT']}"
    return f"COMPARE: {fields['COMPARE']}\nPOLICY: {fields['POLICY']}\nNEXT: {fields['NEXT']}"


def score_text(case, text, assigned_map):
    require(isinstance(text, str), "raw text missing")
    actions = "|".join(map(re.escape, case["inputs"]["actions"]))
    outcomes = "|".join(map(re.escape, case["inputs"]["outcomes"]))
    if case["operation"] == "PROSPECT":
        strict = rf"PREDICT: ({actions}) -> ({outcomes})\nACT: ({actions})"
        patterns = {"PREDICT": (rf"({actions})[ \t\r]*->[ \t\r]*({outcomes})", ("PREDICT_ACTION", "PREDICT_OUTCOME")),
                    "ACT": (rf"({actions})", ("ACT",))}
    else:
        strict = rf"COMPARE: (MATCH|MISMATCH)\nPOLICY: (KEEP|SWITCH)\nNEXT: ({actions})"
        patterns = {"COMPARE": ("(MATCH|MISMATCH)", ("COMPARE",)), "POLICY": ("(KEEP|SWITCH)", ("POLICY",)),
                    "NEXT": (rf"({actions})", ("NEXT",))}
    seen, fields = Counter(), {}
    for line in text.split("\n"):
        if re.fullmatch(r"[ \t\r]*", line):
            continue
        label = re.fullmatch(r"[ \t\r]*([A-Z]+):[ \t\r]*(.*?)[ \t\r]*", line)
        if not label or label[1] not in patterns:
            fields = {}
            break
        expression, keys = patterns[label[1]]
        match = re.fullmatch(expression, label[2])
        if not match:
            fields = {}
            break
        seen[label[1]] += 1
        for key, value in zip(keys, match.groups()):
            if seen[label[1]] == 1:
                fields[key] = value
            else:
                fields.pop(key, None)
    auth = {key: fields.get(key) == value for key, value in targets(case, "AUTH").items()}
    own = {key: fields.get(key) == value for key, value in targets(case, assigned_map).items()}
    surface = re.fullmatch(strict, text) is not None
    return dict(case_id=case["id"], raw_text=text, fields=fields, strict_surface=surface,
                auth_fields=auth, own_map_fields=own, auth_joint_semantic=all(auth.values()),
                own_map_joint_semantic=all(own.values()), auth_strict_joint=surface and all(auth.values()),
                own_map_strict_joint=surface and all(own.values()))


def counts(rows):
    result = dict(total=len(rows), **{key: sum(row[key] for row in rows) for key in BOOL_METRICS})
    for field in ("auth_fields", "own_map_fields"):
        result[field] = {key: sum(row[field][key] for row in rows) for key in (rows[0][field] if rows else ())}
    return result


def primary(candidate, outputs, split, assigned_map):
    cases = candidate["train"][assigned_map] if split == "train" else candidate["dev"]
    rows = {case["id"]: score_text(case, outputs[case["id"]], assigned_map)
            for case in cases if case["id"] in outputs}
    operations, strata = {}, {}
    for operation in OPERATIONS:
        selected = [case for case in cases if case["operation"] == operation and case["id"] in rows]
        operations[operation] = counts([rows[case["id"]] for case in selected])
        groups = defaultdict(list)
        for case in selected:
            inputs, auth = case["inputs"], targets(case, "AUTH")
            action = auth["ACT"] if operation == "PROSPECT" else auth["NEXT"]
            values = dict(action=action, outcome=inputs["goal"] if operation == "PROSPECT" else inputs["observed"],
                          template=str(case["template"]), card_order=",".join(inputs["action_order"]),
                          target_position=str(inputs["action_order"].index(action)))
            if operation == "REVISE":
                values.update(branch=auth["COMPARE"], prior_action=inputs["prior_action"])
            else:
                values["belief"] = str(case["factors"]["belief"])
            for key, value in values.items():
                groups[f"{key}/{value}"].append(rows[case["id"]])
        strata[operation] = {key: counts(group) for key, group in groups.items()}
    twins, missing_twins = {}, {}
    for family, pairs in candidate["twins"][split].items():
        entries, missing = [], []
        for first_id, second_id in pairs:
            if first_id not in rows or second_id not in rows:
                missing.append([first_id, second_id])
                continue
            first, second = rows[first_id], rows[second_id]
            flips = all(key in first["fields"] and key in second["fields"] and first["fields"][key] != second["fields"][key]
                        for key in FLIPS[family])
            auth = flips and first["auth_joint_semantic"] and second["auth_joint_semantic"]
            own = flips and first["own_map_joint_semantic"] and second["own_map_joint_semantic"]
            strict = first["strict_surface"] and second["strict_surface"]
            entries.append(dict(case_ids=[first_id, second_id], full_required_flip=flips,
                                auth_semantic_pass=auth, own_map_semantic_pass=own,
                                auth_strict_pass=auth and strict, own_map_strict_pass=own and strict))
        twins[family] = dict(total=len(entries), rows=entries,
                            **{key + "es": sum(row[key] for row in entries) for key in
                               ("auth_semantic_pass", "own_map_semantic_pass", "auth_strict_pass", "own_map_strict_pass")})
        missing_twins[family] = missing
    return dict(rows=list(rows.values()), operations=operations, per_stratum=strata, twins=twins), missing_twins


def control_result(controls, outputs):
    rows = []
    for case in controls:
        if case["id"] not in outputs:
            continue
        text = outputs[case["id"]]
        exact = text in (f"ACT: {case['expected']}", f"ACT: {case['expected']}\n")
        if case["family"] == "addition":
            lines = [line for line in text.splitlines() if re.match(r"^[ \t]*ACT\b", line)]
            match = re.fullmatch(r"[ \t]*ACT:[ \t]*([+-]?[0-9]+)[ \t]*", lines[0]) if len(lines) == 1 else None
            valid = match is not None
            correct = valid and int(match[1]) == case["expected"]
        else:
            match = re.fullmatch(r"ACT: (-[a-z0-9]+)\n?", text)
            valid = match is not None and match[1] in COPY_ACTIONS
            correct = exact
        rows.append(dict(case_id=case["id"], family=case["family"], prompt=case["context"], raw_text=text,
                         valid=valid, correct=correct, exact=exact,
                         tag_spill=bool(re.search(r"\b(?:PREDICT|COMPARE|POLICY|NEXT)\s*:", text))))
    families = {}
    for family in ("addition", "copy"):
        selected = [row for row in rows if row["family"] == family]
        groups = defaultdict(list)
        expected_groups = Counter(case["context"] for case in controls if case["family"] == family)
        for row in selected:
            groups[row["prompt"]].append(row)
        families[family] = dict(total=len(selected), unique_prompts=len(groups),
            **{key: sum(row[key] for row in selected) for key in ("valid", "correct", "exact", "tag_spill")},
            unique_all_correct=sum(len(group) == expected_groups[prompt] and all(row["correct"] for row in group)
                                   for prompt, group in groups.items()),
            unique_any_spill=sum(any(row["tag_spill"] for row in group) for group in groups.values()))
    return dict(rows=rows, families=families)


def generation_result(candidate, controls, outputs):
    panels, missing = {}, {}
    for split in ("train", "dev"):
        panels[split], missing[split] = {}, {}
        for assigned_map in MAPS:
            panels[split][assigned_map], missing[split][assigned_map] = primary(candidate, outputs, split, assigned_map)
    return dict(primary=panels, controls=control_result(controls, outputs), actual_generations=len(outputs)), missing


def registry(candidate):
    cases = {case["id"]: case for case in candidate["dev"]}
    result = {}
    for operation, family in (("PROSPECT", "belief"), ("REVISE", "outcome")):
        pairs = candidate["twins"]["dev"][family]
        require(len(pairs) == 16, "primary family must have 16 twins")
        for endpoints in pairs:
            require(len(endpoints) == 2 and endpoints[0] != endpoints[1], "invalid twin endpoints")
            choices = [dict(candidate_id=f"{assigned_map}_X{index}", text=target_text(cases[case_id], assigned_map),
                            source_case_id=case_id, source_map=assigned_map)
                       for assigned_map in (MAPS if operation == "PROSPECT" else ("AUTH",))
                       for index, case_id in enumerate(endpoints)]
            require(len({choice["text"] for choice in choices}) == (4 if operation == "PROSPECT" else 2), "distinct fixed strings required")
            pair_ids = {assigned_map: [next(choice["candidate_id"] for choice in choices
                                                  if choice["text"] == target_text(cases[case_id], assigned_map))
                                      for case_id in endpoints] for assigned_map in MAPS}
            if operation == "REVISE":
                require(pair_ids["AUTH"] == pair_ids["DERANGED"][::-1], "REVISE targets do not genuinely swap")
            for case_id in endpoints:
                require(case_id not in result and cases[case_id]["operation"] == operation, "duplicate/mistyped primary endpoint")
                result[case_id] = dict(choices=choices, candidate_pairs=pair_ids)
    require(set(result) == set(cases), "primary twins do not partition dev")
    return result


def odds(log_odds):
    if log_odds > 709:
        return dict(log_odds_nats=log_odds, odds_ratio=None, ratio_note="overflow; signed log odds retained")
    ratio = math.exp(log_odds)
    return dict(log_odds_nats=log_odds, odds_ratio=ratio,
                ratio_note="floating underflow; signed log odds retained" if ratio == 0 else None)


def interactions(candidate, records):
    registered = registry(candidate)
    operations, comparison = {}, {}
    for operation, family in (("PROSPECT", "belief"), ("REVISE", "outcome")):
        rows, compact, missing = [], [], []
        for first, second in candidate["twins"]["dev"][family]:
            identifiers = registered[first]["candidate_pairs"]
            maps, oriented = {}, {}
            for assigned_map, (first_target, second_target) in identifiers.items():
                endpoints = []
                for index, case_id in enumerate((first, second)):
                    values = records.get(case_id)
                    if values is None:
                        endpoints.append(None)
                        continue
                    difference = values[first_target] - values[second_target]
                    endpoints.append(dict(case_id=case_id, fixed_A=first_target, fixed_B=second_target,
                        logprob_A=values[first_target], logprob_B=values[second_target],
                        fixed_A_over_B=odds(difference), own_target_over_other=odds(difference if index == 0 else -difference)))
                interaction = (endpoints[0]["fixed_A_over_B"]["log_odds_nats"] -
                               endpoints[1]["fixed_A_over_B"]["log_odds_nats"]) if all(endpoints) else None
                if interaction is not None and not finite(interaction):
                    interaction = None
                oriented[assigned_map] = interaction
                maps[assigned_map] = dict(endpoints=endpoints, interaction_nats=interaction)
            complete = all(value is not None for value in oriented.values())
            rows.append(dict(case_ids=[first, second], candidate_pairs=identifiers, maps=maps, complete=complete))
            if complete:
                compact.append(dict(case_ids=[first, second], candidate_pairs=identifiers, oriented_nats=oriented))
            else:
                missing.append([first, second])
        means = {assigned_map: (sum(row["oriented_nats"][assigned_map] / 16 for row in compact) if len(compact) == 16 else None)
                 for assigned_map in MAPS}
        operations[operation] = dict(family=family, registered_twins=16, complete_twins=len(compact),
            missing_twins=missing, pairs=rows, mean_nats=means,
            negated_maps_not_independent=operation == "REVISE", maps_do_not_double_denominator=True)
        if len(compact) == 16:
            comparison[operation] = dict(family=family, total=16, pairs=compact,
                map_oriented={assigned_map: dict(mean_nats=means[assigned_map], at_least_one_nat=means[assigned_map] >= 1)
                              for assigned_map in MAPS})
    return dict(operations=operations, candidate_logprob_sums=records, scored_cases=len(records),
                candidate_forwards=sum(len(values) for values in records.values())), comparison


def validate_candidate(candidate):
    require(candidate["root"] == 0 and candidate["spellings"] == dict(actions=["dax", "wug"], outcomes=["fep", "nup"]), "root/spellings differ")
    require(candidate["composition"]["status"] == "UNTRAINED_FUTURE_ASSAY" and candidate["composition"]["trained_chain_rows"] == 0,
            "composition boundary changed")
    for split, cases, expected in (("train", candidate["train"]["AUTH"], 64), ("dev", candidate["dev"], 32)):
        require(len({case["id"] for case in cases}) == len(cases) == 2 * expected, "case denominator/identity differs")
        require(Counter(case["operation"] for case in cases) == dict.fromkeys(OPERATIONS, expected), "operation denominator differs")
        require(all(case["split"] == split for case in cases), "case split differs")
    require([case["id"] for case in candidate["train"]["AUTH"]] == [case["id"] for case in candidate["train"]["DERANGED"]], "training map identities differ")
    for assigned_map in MAPS:
        for case in candidate["train"][assigned_map]:
            require(case["response"] == target_text(case, assigned_map), "training target differs from independent rule")
    registry(candidate)


def token_ids(values, label, nonempty=False):
    require(isinstance(values, list) and all(type(value) is int and value >= 0 for value in values), f"{label}: invalid stored token IDs")
    require(not nonempty or values, f"{label}: empty IDs")


def raw_call(plan, request, index, sent, received, registered, previous_end):
    same(request, sent["request"], "raw request")
    require(request == sent["request"] and sent["identity"] == plan["identity"], "request/backend identity differs")
    response = received["response"]
    require(sent["prompt_sha256"] == value_hash(request["prompt"]) and received["response_sha256"] == value_hash(response), "raw seals differ")
    start, end = sent["started"], received["ended"]
    require(finite(start) and finite(end) and 0 <= previous_end <= start <= end and end - start <= 120, "call order/time cap differs")
    cost = dict.fromkeys(COST_KEYS, 0)
    cost.update(requests=1, call_seconds=end - start)
    if plan["phase"] == "generate":
        require(isinstance(response["text"], str), "generation text missing")
        for field in ("prompt_token_ids", "output_token_ids"):
            token_ids(response[field], field, field == "prompt_token_ids")
        native = plan["native_inputs"][index]
        same({key: native[key] for key in ("prompt_token_ids", "rendered_prompt")}, response, "native stored input")
        require(native["call_id"] == request["call_id"] and isinstance(response["rendered_prompt"], str), "native input ID differs")
        require(len(response["output_token_ids"]) <= 64 and len(response["prompt_token_ids"]) + 64 <= 16384, "generation token cap exceeded")
        cost.update(native_input_tokens=len(response["prompt_token_ids"]), native_output_tokens=len(response["output_token_ids"]), output_token_ceiling=64)
        return response["text"], cost, end
    choices = request["candidates"]
    expected = registered[request["case_id"]]
    require(len(choices) == len(expected["choices"]), "four PROSPECT / two REVISE complete candidates required")
    same(expected["choices"], choices, "candidate fixed strings")
    require(request["candidate_pairs"] == expected["candidate_pairs"], "fixed endpoint orientation changed")
    prefix = request["payload"]["prompt_input_ids"]
    token_ids(prefix, "prefix", True)
    require(isinstance(request["rendered_prompt"], str), "missing rendered input")
    values = response["token_logprobs"]
    require(isinstance(values, list) and len(values) == len(choices), "missing candidate logprob sequence")
    records, eos_ids = {}, set()
    for choice, scores in zip(choices, values):
        target = choice["response_ids"]
        token_ids(target, "complete target", True)
        token_ids(choice["input_ids"], "causal concatenation", True)
        require(len(target) >= 2 and choice["input_ids"] == prefix + target and
                choice["labels"] == [-100] * len(prefix) + target and len(choice["input_ids"]) <= 16384,
                "stored causal boundary/mask/cap differs")
        eos_ids.add(target[-1])
        require(target[-1] not in target[:-1], "stored EOS repeated inside target")
        require(isinstance(scores, list) and len(scores) == len(target) and all(finite(value) and value <= 0 for value in scores),
                "incomplete/nonfinite/positive token logprob")
        total = sum(scores)
        require(finite(total), "nonfinite complete-candidate sum")
        records[choice["candidate_id"]] = total
        cost["native_input_tokens"] += len(choice["input_ids"])
        cost["scored_target_tokens"] += len(target)
    require(len(eos_ids) == 1 and sum(math.exp(value) for value in records.values()) <= 1 + 1e-6, "EOS consistency or candidate mass differs")
    cost["candidate_forwards"] = len(choices)
    cost["padded_forward_tokens"] = sum(2 * max(len(choice["input_ids"]) for choice in choices[offset:offset + 2])
                                         for offset in range(0, len(choices), 2))
    return records, cost, end


def plan_panel(plan, candidate, state, phase):
    require((plan["state"], plan["phase"]) == (state, phase), "plan state/phase differs")
    require(plan["worker_seconds"] == 600, "worker allowance changed")
    require(plan["candidate_sha256"] == value_hash(candidate), "canonical candidate digest differs")
    controls = plan["controls"]
    require(Counter(case["family"] for case in controls) == {"addition": 16, "copy": 16} and len({case["id"] for case in controls}) == 32, "control denominator differs")
    copies = Counter(case["context"] for case in controls if case["family"] == "copy")
    require(len(copies) == 8 and set(copies.values()) == {2}, "copy prompt replication differs")
    panel = ([(case, "train") for case in candidate["train"]["AUTH"]] + [(case, "dev") for case in candidate["dev"]] +
             [(case, "control") for case in controls]) if phase == "generate" else [(case, "score") for case in candidate["dev"]]
    requests = plan["requests"]
    require(len(requests) == len(panel) and len({row["case_id"] for row in requests}) == len(panel), "request panel denominator/IDs differ")
    if phase == "score":
        require(plan["assay_version"] == ASSAY and plan["prospect_contrast"] == CONTRAST, "frozen scoring amendment differs")
    else:
        require(len(plan["native_inputs"]) == 224, "native generation input panel differs")
    for index, (request, (case, role)) in enumerate(zip(requests, panel)):
        require(request["call_id"] == f"{index:04d}" and request["case_id"] == case["id"] and
                request["prompt"] == case["context"] and request["role"] == role and request["arm"] == state, "registered request order/context differs")
        if phase == "generate":
            require(request["split"] == role and request["max_tokens"] == 64 and request["temperature"] == 0.0 and
                    request["seed"] == 20260912, "generation settings changed")
        else:
            require(request["operation"] == case["operation"] and request["assay_version"] == ASSAY, "request assay/operation differs")
    return requests


def analyze_phase(snapshot, manifest_row, manifest, candidate, terminal):
    state, phase = manifest_row["state"], manifest_row["phase"]
    name = f"{state}_{phase}"
    report = dict(state=state, phase=phase, complete=False, issues=[], observed_valid_calls=0,
                  expected_calls=224 if phase == "generate" else 64, observed_cost=dict.fromkeys(COST_KEYS, 0),
                  cost=None, result=None, missing_calls=[], stored_crosscheck="NOT_AVAILABLE")
    plan = check(report, "plan", lambda: snapshot.read(f"{name}/plan.json"))
    if plan is None:
        return report, None
    check(report, "plan binding", lambda: require(snapshot.digest(f"{name}/plan.json") == manifest_row["plan_sha256"] ==
        snapshot.read(f"{name}/plan.sha256.json")["sha256"], "phase plan hash differs"))
    check(report, "shared bindings", lambda: same({key: manifest[key] for key in ("source_hashes", "model_files", "material_inventory", "device")}, plan, "plan/manifest"))
    requests = check(report, "panel", lambda: plan_panel(plan, candidate, state, phase))
    if requests is None:
        return report, plan
    data = f"{name}/run/data"
    check(report, "capture inventory", lambda: require(snapshot.read(f"{data}/manifest.json")["files"] ==
        {path[len(data) + 1:]: sha(payload) for path, payload in snapshot.files.items() if path.startswith(data + "/") and path != f"{data}/manifest.json"},
        "capture file/hash inventory differs"))
    check(report, "capture identity", lambda: same(dict(backend=plan["identity"], model_files=plan["model_files"], adapter_files=plan["adapter_files"]),
        snapshot.read(f"{data}/identity.json"), "capture identity"))
    check(report, "cleanup", lambda: require(snapshot.read(f"{data}/backend.cleanup.json")["closed"] is True and f"{data}/failure.json" not in snapshot.files,
        "capture failed or cleanup missing"))
    expected_files = {f"{data}/calls/{row['call_id']}{suffix}" for row in requests for suffix in (".request.json", ".response.json")}
    extra = set(path for path in snapshot.files if path.startswith(f"{data}/calls/")) - expected_files
    if extra:
        report["issues"].append(f"unregistered raw files: {sorted(extra)}")
    records, last_end, usage = {}, 0, {}
    registered = registry(candidate)
    for index, request in enumerate(requests):
        stem = f"{data}/calls/{request['call_id']}"
        call = check(report, request["call_id"], lambda: raw_call(plan, request, index, snapshot.read(stem + ".request.json"),
            snapshot.read(stem + ".response.json"), registered, last_end))
        if call is None:
            report["missing_calls"].append(request["call_id"])
            continue
        result, cost, last_end = call
        records[request["case_id"]] = result
        for key in COST_KEYS:
            report["observed_cost"][key] += cost[key]
        if phase == "generate":
            values = {key: cost[key] for key in ("requests", "native_input_tokens", "native_output_tokens", "output_token_ceiling")}
            values["generation_seconds"] = cost["call_seconds"]
            role = usage.setdefault(request["role"], dict.fromkeys(values, 0))
            arm = role.setdefault("by_arm", {}).setdefault(state, dict.fromkeys(values, 0))
            for key, value in values.items():
                role[key] += value
                arm[key] += value
    report["observed_valid_calls"] = len(records)
    if phase == "generate":
        report["result"], report["missing_generation_twins"] = generation_result(candidate, plan["controls"], records)
        report["generation_coverage"] = {}
        for split in ("train", "dev"):
            cases = candidate["train"]["AUTH"] if split == "train" else candidate["dev"]
            report["generation_coverage"][split] = {}
            for operation in OPERATIONS:
                registered_ids = [case["id"] for case in cases if case["operation"] == operation]
                missing = [case_id for case_id in registered_ids if case_id not in records]
                report["generation_coverage"][split][operation] = dict(registered_denominator=len(registered_ids),
                    observed_denominator=len(registered_ids) - len(missing), missing_case_ids=missing,
                    complete_cell=not missing, scientific_rate=None,
                    note="Counts describe observed raw rows only; missing rows are not failures or scientific zeros.")
        report["generation_coverage"]["control"] = {family: dict(registered_denominator=16,
            observed_denominator=report["result"]["controls"]["families"][family]["total"],
            complete_cell=report["result"]["controls"]["families"][family]["total"] == 16)
            for family in ("addition", "copy")}
        projection = dict(report["result"], shared_off=state == "OFF", own_map=state if state != "OFF" else None)
        projection["controls"] = dict(projection["controls"], copied_prompt_executions=16, unique_copy_prompts=8)
        check(report, "usage", lambda: same(usage, snapshot.read(f"{data}/usage.json"), "raw/stored generation usage"))
    else:
        report["result"], operations = interactions(candidate, records)
        if len(records) == 64 and len(operations) != 2:
            report["issues"].append("nonfinite interaction; full-family aggregate unavailable")
        projection = dict(operations=operations, candidate_logprob_sums=records, scored_cases=len(records),
                          candidate_forwards=report["result"]["candidate_forwards"], assay_version=ASSAY, prospect_contrast=CONTRAST)
    if len(records) == len(requests):
        report["cost"] = dict(report["observed_cost"])
    def receipts():
        attempt = snapshot.read(f"controller/phases/{name}.json")
        require(attempt in terminal["attempts"] and attempt["name"] == name and attempt["root"] == manifest_row["root"] and
                attempt["plan_sha256"] == manifest_row["plan_sha256"], "attempt/terminal binding differs")
        receipt = snapshot.read(f"{name}/run/worker/supervision.json")
        require(receipt == attempt["supervision"] == terminal["supervision"][name], "supervision binding differs")
        require(all(receipt.get(key) is True for key in ("ok", "reservation_release_verified", "owned_group_empty", "gpu_processes_absent")) and
                receipt["returncode"] == 0 and receipt.get("error") is None and receipt["device"] == plan["device"] and
                finite(receipt["reserved_seconds"]) and receipt["reserved_seconds"] >= 0, "worker supervision incomplete")
        process = snapshot.read(f"{name}/run/worker/process.json")
        require(process == attempt["process"] and finite(process["timeout"]) and 0 < process["timeout"] <= 600, "worker/process bound differs")
        snapshot.read(f"{data}/backend.ready.json")
        reduction = attempt["reduction"]
        same(dict(complete=True, status="COMPLETE_PHASE", state=state, phase=phase, root=manifest_row["root"],
                  plan_sha256=manifest_row["plan_sha256"], reserved_seconds=receipt["reserved_seconds"]), reduction, "reduction identity")
        same({key: plan[key] for key in ("material_inventory", "source_hashes", "model_files", "adapter_files", "assay_version", "resource_budget")}, reduction, "reduction contract")
        require(report["cost"] is not None, "incomplete raw calls cannot cross-check complete reduction")
        require(set(reduction["cost"]) == set(COST_KEYS), "stored cost keys differ")
        require(report["cost"]["call_seconds"] <= receipt["reserved_seconds"] + 1e-6, "call window exceeds worker reservation")
        same(report["cost"], reduction["cost"], "raw/stored cost")
        same(projection, reduction["result"], "independent/stored result")
        report["stored_crosscheck"] = "MATCH"
        report["reserved_seconds"] = receipt["reserved_seconds"]
    check(report, "stored reduction", receipts)
    report["complete"] = not report["issues"] and len(records) == report["expected_calls"]
    report["raw_panel_complete"] = len(records) == report["expected_calls"]
    report["interpretation"] = ("All expected raw rows available; consult issues and root completeness before interpretation."
                                if report["raw_panel_complete"] else
                                "Observed subset only. Missing/invalid technical evidence is not a scientific failure or zero.")
    return report, plan


def comparisons(phases):
    result = {}
    off = phases["OFF_generate"]["result"]
    for state in MAPS:
        actual = phases[f"{state}_generate"]["result"]
        row = dict(auth_minus_off_semantic={operation: (actual["primary"]["dev"]["AUTH"]["operations"][operation]["auth_joint_semantic"] -
            off["primary"]["dev"]["AUTH"]["operations"][operation]["auth_joint_semantic"]) / 32 for operation in OPERATIONS}, controls={})
        for family in ("addition", "copy"):
            row["controls"][family] = {key: dict(delta_count=actual["controls"]["families"][family][key] - off["controls"]["families"][family][key],
                denominator=16, no_more_than_point05_loss=actual["controls"]["families"][family][key] >= off["controls"]["families"][family][key])
                for key in ("valid", "correct", "exact")}
        row["copy_unique"] = dict(denominator=8, delta_all_correct=actual["controls"]["families"]["copy"]["unique_all_correct"] -
                                 off["controls"]["families"]["copy"]["unique_all_correct"])
        row["spill"] = {family: dict(total=16, maximum=0, actual=actual["controls"]["families"][family]["tag_spill"],
            within_point05=actual["controls"]["families"][family]["tag_spill"] == 0) for family in ("addition", "copy")}
        result[state] = row
    return result


def analyze(snapshot, manifest, candidate, validation):
    validate_candidate(candidate)
    terminal = snapshot.read("controller/terminal.json")
    require(terminal.get("status") in ("COMPLETE", "PARTIAL"), "not a terminal capsule; no analysis output authorized")
    report = dict(schema="astra-independent-conditional-analysis-v1", status="TECHNICAL_PARTIAL", complete=False,
        terminal_status=terminal["status"], issues=list(snapshot.issues), phases={}, cost=None, comparisons=None,
        signed_interaction_deltas={}, supplies_l1_verdict=False, supplies_h1_verdict=False,
        composition="UNTRAINED_FUTURE_ASSAY", limits=LIMITS, candidate_sha256=value_hash(candidate))
    report["observed_cost_note"] = "Only successfully validated raw calls are counted; on PARTIAL this is an observed subtotal, not total spend."
    check(report, "frozen manifest", lambda: require(manifest["assay_version"] == ASSAY and
        [f"{row['state']}_{row['phase']}" for row in manifest["phases"]] == list(ORDER) and
        manifest["generation_calls"] == 672 and manifest["candidate_forwards"] == 576, "manifest workload/order differs"))
    plans = {}
    for state in STATES:
        for phase in ("generate", "score"):
            name = f"{state}_{phase}"
            rows = [row for row in manifest["phases"] if (row["state"], row["phase"]) == (state, phase)]
            if len(rows) != 1:
                report["phases"][name] = dict(complete=False, issues=["missing/duplicate manifest phase"], cost=None, result=None)
                continue
            report["phases"][name], plans[name] = analyze_phase(snapshot, rows[0], manifest, candidate, terminal)
    phases = report["phases"]
    def shared():
        reference = plans["OFF_generate"]
        require(set(plans) == set(ORDER) and all(plans.values()), "missing phase plan")
        keys = ("device", "model", "model_files", "material", "material_inventory", "material_manifest_sha256", "candidate_sha256", "source_hashes", "controls", "worker_seconds", "resource_budget", "lease_end")
        for plan in plans.values():
            same({key: reference[key] for key in keys}, plan, "cross-phase contract")
        require(reference["adapter"] is None and reference["adapter_files"] == {}, "OFF has adapter")
        for state in STATES:
            same({key: plans[f"{state}_generate"][key] for key in ("adapter", "adapter_files")}, plans[f"{state}_score"], "state gen/score adapter")
        require(plans["AUTH_generate"]["adapter"] != plans["DERANGED_generate"]["adapter"] and
                all(plans[f"{state}_generate"]["adapter_files"] for state in MAPS), "trained adapter identities invalid")
        reference_requests = reference["requests"]
        for state in MAPS:
            for left, right in zip(reference_requests, plans[f"{state}_generate"]["requests"]):
                require({key: value for key, value in left.items() if key != "arm"} ==
                        {key: value for key, value in right.items() if key != "arm"}, "state generation panel differs")
            require(reference["native_inputs"] == plans[f"{state}_generate"]["native_inputs"], "state native generation prefixes differ")
            for left, right in zip(plans["OFF_score"]["requests"], plans[f"{state}_score"]["requests"]):
                require({key: value for key, value in left.items() if key != "arm"} ==
                        {key: value for key, value in right.items() if key != "arm"}, "state score strings/IDs/prefixes differ")
        dev_requests = {row["case_id"]: native for row, native in zip(reference_requests, reference["native_inputs"]) if row["split"] == "dev"}
        for request in plans["OFF_score"]["requests"]:
            native = dev_requests[request["case_id"]]
            require(request["rendered_prompt"] == native["rendered_prompt"] and
                    request["payload"]["prompt_input_ids"] == native["prompt_token_ids"], "gen/score input-only prefixes differ")
        by_case = {request["case_id"]: request for request in plans["OFF_score"]["requests"]}
        eos = set()
        for family in ("belief", "outcome"):
            for first, second in candidate["twins"]["dev"][family]:
                left, right = by_case[first]["candidates"], by_case[second]["candidates"]
                require([choice["response_ids"] for choice in left] == [choice["response_ids"] for choice in right], "fixed candidate token IDs differ between endpoints")
                eos.update(choice["response_ids"][-1] for choice in left)
        require(len(eos) == 1, "stored EOS IDs disagree across scoring requests")
    check(report, "shared evidence", shared)
    report["observed_cost"] = {key: sum(phase.get("observed_cost", {}).get(key, 0) for phase in phases.values()) for key in COST_KEYS}
    if all(phase.get("cost") is not None for phase in phases.values()):
        report["cost"] = {key: sum(phase["cost"][key] for phase in phases.values()) for key in COST_KEYS}
    if all(phases[f"{state}_generate"]["complete"] for state in STATES):
        report["comparisons"] = comparisons(phases)
    for state in MAPS:
        differences = report["signed_interaction_deltas"][state] = {}
        for operation in OPERATIONS:
            differences[operation] = {}
            for assigned_map in MAPS:
                actual, off = phases[f"{state}_score"].get("result"), phases["OFF_score"].get("result")
                actual_mean = actual["operations"][operation]["mean_nats"][assigned_map] if actual else None
                off_mean = off["operations"][operation]["mean_nats"][assigned_map] if off else None
                differences[operation][assigned_map] = actual_mean - off_mean if actual_mean is not None and off_mean is not None else None
    def summary_check():
        summary = snapshot.read("controller/summary.json")
        require(summary == terminal["summary"], "terminal/stored summary differs")
        require(all(phase["complete"] for phase in phases.values()), "summary cannot assert COMPLETE with missing/invalid phases")
        require(len(summary["reductions"]) == 6 and summary["reductions"] ==
            [snapshot.read(f"controller/phases/{name}.json")["reduction"] for name in ORDER], "summary reduction binding differs")
        same(dict(status="COMPLETE_ROOT0_READOUT_NOT_L1_VERDICT", complete=True, actual_generation_calls=672, actual_scoring_requests=192, candidate_forwards=576,
                  assay_version=ASSAY, cost=report["cost"], comparisons=report["comparisons"], supplies_l1_verdict=False), summary, "summary independent cross-check")
        require(report["cost"]["requests"] == 864 and report["cost"]["candidate_forwards"] == 576 and report["cost"]["output_token_ceiling"] == 43008,
                "aggregate raw count/cap differs")
        same(float(sum(phase["reserved_seconds"] for phase in phases.values())), summary["readout_reserved_seconds"], "worker reservation total")
        report["summary_crosscheck"] = "MATCH"
    report["summary_crosscheck"] = "NOT_AVAILABLE"
    check(report, "summary", summary_check)
    def caps():
        release = snapshot.read("controller/main_release.json")
        require(release["full_release"] is True and release["controller_absent"] is True and
                release["terminal_sha256"] == snapshot.digest("controller/terminal.json") and
                release["xml_sha256"] == snapshot.digest("controller/main_release.xml"), "Main terminal/release binding missing")
        require(terminal["status"] == validation["terminal_status"] == release["terminal_status"], "collector terminal status differs")
        require(validation["technical_complete"] is (terminal["status"] == "COMPLETE"), "collector completeness differs")
        for key in ("reserved_seconds", "worker_reserved_seconds", "started", "ended"):
            require(finite(terminal[key]) and terminal[key] >= 0, "invalid terminal time")
        same(dict(controller_seconds=4500, external_collection_margin_seconds=300, total_ceiling_seconds=5400,
                  prior_fit_full_reservation_seconds=manifest["prior_fit_full_reservation_seconds"]), terminal, "terminal caps")
        require(terminal["ended"] >= terminal["started"] and terminal["reserved_seconds"] <= 4500, "controller time cap exceeded")
        require(terminal["worker_reserved_seconds"] <= terminal["reserved_seconds"] + 1e-6, "nested worker reservations exceed controller")
        require(all(finite(receipt["reserved_seconds"]) and receipt["reserved_seconds"] >= 0 for receipt in terminal["supervision"].values()), "worker time invalid")
        same(float(sum(receipt["reserved_seconds"] for receipt in terminal["supervision"].values())), terminal["worker_reserved_seconds"], "worker sum")
        full = validation["launch_to_collection_seconds"]
        prior = manifest["prior_fit_full_reservation_seconds"]
        require(finite(full) and full >= 0 and finite(prior) and prior >= 0, "invalid reservation accounting")
        require(full >= terminal["reserved_seconds"], "full launch-to-collection window shorter than controller")
        same(float(prior + full), validation["conservative_total_seconds"], "fit plus full collection window")
        require(prior + full <= 5400 and finite(validation["collection_seconds"]) and 0 <= validation["collection_seconds"] <= 300 and
                finite(validation["terminal_to_collection_seconds"]) and 0 <= validation["terminal_to_collection_seconds"] <= 300 and
                validation["postterminal_margin_met"] is True, "total/collection cap exceeded")
        report["caps"] = dict(controller_seconds=terminal["reserved_seconds"], controller_cap=4500,
            worker_reserved_seconds=terminal["worker_reserved_seconds"], prior_fit_seconds=prior,
            launch_to_collection_seconds=full, conservative_total_seconds=prior + full, total_cap=5400,
            collection_seconds=validation["collection_seconds"], collection_cap=300,
            note="Worker/call/controller windows are nested, not additive. No independent clock or current GPU check.")
    check(report, "caps and Main collection", caps)
    check(report, "terminal completeness", lambda: require(terminal["status"] == "COMPLETE" and terminal["completed_phases"] == 6 and
        terminal["release_verified"] is True and terminal["deadline_met"] is True and terminal["error"] is None and
        not terminal["unaccounted_processes"] and len(terminal["supervision"]) == 6 and
        [attempt["name"] for attempt in terminal["attempts"]] == list(ORDER), "PARTIAL/missing terminal phase or release evidence"))
    report["complete"] = not report["issues"] and all(phase["complete"] for phase in phases.values())
    if report["complete"]:
        report["status"] = "COMPLETE_INDEPENDENT_RAW_REDUCTION_NOT_SCIENTIFIC_VERDICT"
    report["complete_assertion_refused"] = terminal["status"] == "COMPLETE" and not report["complete"]
    return report


def local_bytes(path, limit=32 * 1024 * 1024):
    path = Path(os.path.abspath(path))
    for part in (path, *path.parents):
        require(not part.is_symlink(), f"symlink refused: {part}")
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, "rb") as stream:
        info = os.fstat(stream.fileno())
        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_size <= limit, "unsafe/oversized evidence file")
        payload = stream.read(limit + 1)
        require(len(payload) <= limit, "evidence size limit exceeded")
        return payload


def load_snapshot(extraction, validation):
    root = Path(os.path.abspath(extraction))
    require(root.is_dir() and not root.is_symlink(), "safe extracted directory required, not an archive")
    files, issues, size = {}, [], 0
    require(isinstance(validation["files"], dict) and 0 < len(validation["files"]) <= 10000, "invalid collector inventory")
    for marker in ("controller/terminal.json", "controller/main_release.json"):
        name = f"{PREFIX}/{marker}"
        require(name in validation["files"], "not a Main-collected terminal capsule")
        payload = local_bytes(root / name)
        require(sha(payload) == validation["files"][name], "terminal/collection marker hash differs")
        value = decode(payload)
        if marker.endswith("terminal.json"):
            require(value.get("status") in ("COMPLETE", "PARTIAL") and value["status"] == validation["terminal_status"], "nonterminal input refused before raw reads")
        else:
            require(value.get("controller_absent") is True and value.get("full_release") is True, "Main collection/release marker missing")
    for name, digest in validation["files"].items():
        path = PurePosixPath(name)
        require(not path.is_absolute() and path.as_posix() == name and ".." not in path.parts and name.startswith(PREFIX + "/"), "unsafe/out-of-scope capsule member")
        require(not any(part in (".git", "__pycache__") for part in path.parts) and path.suffix not in (".bin", ".safetensors", ".pt", ".pth", ".pyc"), "model/binary member refused")
        require(isinstance(digest, str) and re.fullmatch("[0-9a-f]{64}", digest), "invalid inventory digest")
        short = name[len(PREFIX) + 1:]
        try:
            payload = local_bytes(root / name)
            size += len(payload)
            require(size <= 256 * 1024 * 1024, "capsule metadata exceeds 256 MiB")
            if sha(payload) != digest:
                issues.append(f"collector hash mismatch: {short}")
            files[short] = payload
        except OSError as error:
            issues.append(f"missing/unreadable collector member: {short}: {error}")
    return Snapshot(files, issues)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("extraction", help="Main's safe extracted archive directory, containing astra_diagnostics/")
    parser.add_argument("--validation", required=True, help="Main collector .tgz.validation.json")
    parser.add_argument("--output", required=True, help="NEW JSON path outside all evidence directories")
    parser.add_argument("--manifest", default=MANIFEST_PATH)
    parser.add_argument("--candidate", default=CANDIDATE_PATH)
    parser.add_argument("--terminal-data", action="store_true", help="Main affirms this is terminal, safely extracted local data, not live outcomes")
    args = parser.parse_args(argv)
    try:
        require(args.terminal_data, "Main must affirm --terminal-data; no live data access")
        manifest_bytes, candidate_bytes = local_bytes(args.manifest), local_bytes(args.candidate)
        require(sha(manifest_bytes) == MANIFEST_SHA and sha(candidate_bytes) == CANDIDATE_SHA, "frozen manifest/candidate bytes differ")
        validation_bytes = local_bytes(args.validation)
        validation = decode(validation_bytes)
        require(validation["manifest_sha256"] == MANIFEST_SHA and validation["terminal_status"] in ("COMPLETE", "PARTIAL"), "collector terminal binding missing")
        snapshot = load_snapshot(args.extraction, validation)
        require(snapshot.digest("manifest.json") == MANIFEST_SHA, "extracted manifest pin differs")
        result = analyze(snapshot, decode(manifest_bytes), decode(candidate_bytes), validation)
        result["bindings"] = dict(manifest_sha256=MANIFEST_SHA, candidate_file_sha256=CANDIDATE_SHA,
            validation_sha256=sha(validation_bytes), input_file_hashes={name: sha(payload) for name, payload in snapshot.files.items()},
            analysis_script_sha256=sha(local_bytes(__file__)))
        output = Path(os.path.abspath(args.output))
        require(output.suffix == ".json" and not output.exists() and not output.is_symlink(), "output must be a NEW JSON file")
        protected = [Path(os.path.abspath(args.extraction)), Path(args.candidate).absolute().parent,
                     Path(__file__).absolute().parent / "astra_independent_conditional_analysis_20260912.py"]
        require(all(output != path and path not in output.parents for path in protected), "output overlaps evidence/code")
        require(all(not part.is_symlink() for part in output.parents), "symlink output parent refused")
        payload = encoded(result)
        with output.open("xb") as stream:
            stream.write(payload)
        print(json.dumps(dict(output=str(output), status=result["status"], complete=result["complete"])))
        return 0 if result["complete"] else 2
    except (OSError, ValueError, KeyError, TypeError, IndexError) as error:
        print(f"REFUSED: {type(error).__name__}: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
