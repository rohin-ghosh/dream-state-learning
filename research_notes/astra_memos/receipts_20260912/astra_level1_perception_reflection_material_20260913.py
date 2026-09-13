"""Independent authored perception and diagnosis/procedure screens, CPU only."""
from __future__ import annotations

import argparse
import ast
from collections import Counter
import copy
import hashlib
import json
import os
from pathlib import Path
import re
from types import ModuleType


SCHEMA = "astra_level1_perception_reflection_material_20260913_v1"
QUALIFICATION = "AUTHORED_LEVEL1_SCREEN_NOT_CHILD_SLEEP_NOT_FULL_SELF_REFLECTION_NOT_RECURSIVE_LEARNING"
SKILLS = ("perception", "self_reflection")
ROOT = Path("/data/home/rohing/dream-state")
SOURCE_ROOT = Path(os.environ.get("ASTRA_LEVEL1_SOURCE_ROOT", str(ROOT))).resolve()
DATA_SEED = 2026091336
PINS = {
    "organism_v6/birth_skill_corpus.py": "078ceba07141b5f6fb2159a12e21f1eccc0901ba9f51f52d1793d988927812f6",
    "organism_v6/rulegame_parenting_diagnostic.py": "e6055da48b2c6fa1bd294c9d991e07f32f05dc6630fe8973373977bdfe977526",
    "organism_v6/birth_reflection_probe.py": "b69dfe4ab39e60fab826e67758d21e708c87d538f3fcd2b8a579bb778b0ace80",
}
CASES = ("agreement", "contradicted_prediction", "absent_prediction", "ambiguous_prediction", "missing_outcome", "outcome_action_mismatch")
POLICY = {
    "agreement": "record_agreement_then_test_new_case",
    "contradicted_prediction": "record_observation_then_retest_prediction",
    "absent_prediction": "leave_prior_null_predict_before_next_try",
    "ambiguous_prediction": "withhold_record_make_one_prior_prediction",
    "missing_outcome": "withhold_record_obtain_selected_outcome",
    "outcome_action_mismatch": "withhold_record_obtain_action_matched_outcome",
}
TRAIN_SKINS = (
    "Chronological public notebook\n{events}\nThe selected execution is the final event e1.",
    "Independent hypothetical box: evidence card\n{events}\nUse only the last TRY and its own returned result.",
    "Two-entry trial ledger\n{events}\nEarlier information is context; e1 is the selected final execution.",
    "Local observation transcript\n{events}\nReport about the last executed TRY, not the first.",
)
HELD_SKINS = (
    "Archived trial history, oldest first\n{events}\nReview e1, the final public execution.",
    "Case chronology\n{events}\nSelect the last action and the result supplied for that action.",
    "Execution audit page\n{events}\nThe previous event must not replace the final event's evidence.",
    "Public evidence file\n{events}\nOnly the second and final execution e1 is under review.",
)
PERCEPTION_TASK = (
    'Produce the selected public record with exactly keys "try", "observed", "predicted", "relation". '
    'try is its three integers; observed is its supplied Boolean outcome; predicted is its single explicit prior PREDICT Boolean or null if absent. '
    'relation is "matched" for equal prediction/outcome, "mismatched" for unequal, or "unavailable" if prediction is absent. '
    'Do not invent a prior prediction from an outcome. If evidence cannot support that record, instead emit ONLY the author-screen object '
    '{"abstain":true,"reason":REASON}, where REASON is "missing_outcome", "outcome_action_mismatch", or "ambiguous_prediction". '
    'Check missing or foreign-action outcome before ambiguous/conflicting prior prediction. '
    'A screen abstention is not a production record. Return only JSON; do not infer a hidden rule or borrow the earlier event.'
)
REFLECTION_TASK = (
    'AUTHOR-SCREEN: diagnose the selected source and choose the warranted next procedure under the policy below. '
    'This is a structured behavioral proxy, not free-text thoughts or full self-reflection. '
    'Return only JSON with exactly "diagnosis", "next_action", "evidence". Evidence has exactly "try", "observed", "predicted". '
    'try is the selected integer triple; observed is null if no action-matched outcome is supplied; predicted is null if absent or ambiguous. '
    'Diagnose missing_outcome or outcome_action_mismatch before ambiguous_prediction; otherwise use absent_prediction, agreement, or contradicted_prediction. '
    'Never infer a hidden rule from one event. No procedure claims that later action was executed. Fixed authored procedure policy:\n' +
    '\n'.join(diagnosis + ' -> ' + action for diagnosis, action in POLICY.items())
)


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":"))


def encoded(value):
    return (canonical(value) + "\n").encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load_sources():
    for relative, expected in PINS.items():
        require(sha((SOURCE_ROOT / relative).read_bytes()) == expected, "source pin mismatch: " + relative)
    path = SOURCE_ROOT / "organism_v6/birth_skill_corpus.py"
    helper = ModuleType("frozen_perception_reflection_corpus")
    helper.__file__ = str(path)
    exec(compile(path.read_bytes(), str(path), "exec"), helper.__dict__)
    tree = ast.parse((SOURCE_ROOT / "organism_v6/birth_reflection_probe.py").read_text())
    reference = {node.targets[0].id: ast.literal_eval(node.value) for node in tree.body
                 if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
                 and node.targets[0].id in ("PROCEDURES", "APPLICATION_TRIPLES", "DISTRACTOR_TRIPLES")}
    require(set(reference) == {"PROCEDURES", "APPLICATION_TRIPLES", "DISTRACTOR_TRIPLES"}, "reflection reference changed")
    return helper, reference


def number(*parts):
    return int(sha(encoded([SCHEMA, DATA_SEED, *parts])), 16)


def fresh_triple(used, *parts):
    for nonce in range(1000):
        values = tuple(number(*parts, coordinate, nonce) % 2001 - 1000 for coordinate in range(3))
        if values not in used:
            used.add(values)
            return values
    raise ValueError("bounded source generation exhausted")


def public_event(event_id, values, predicted, observed):
    triple = ",".join(map(str, values))
    return {"event_id": event_id,
            "raw_response": ("" if predicted is None else "PREDICT: " + ("T" if predicted else "F") + "\n") + "ACT: TRY " + triple,
            "raw_outcome": f"the box says: {observed} for ({triple})"}


def evidence(source, helper):
    require(source["origin"] == helper.ORIGIN, "author-sourced evidence required")
    require(source["source_id"] == helper._identify(copy.deepcopy(source))["source_id"], "source identity mismatch")
    require(len(source["events"]) == 2 and len({entry["event_id"] for entry in source["events"]}) == 2, "two unique chronological events required")
    selected = source["events"][-1]
    require(selected["event_id"] == source["selected_event_id"], "selected event must be final")
    action = helper._interface().parse_action(selected["raw_response"], "interaction_v3")
    require(action["kind"] == "try", "selected action must be TRY")
    outcome = selected["raw_outcome"]
    match = re.fullmatch(r"the box says: (True|False) for \((-?[0-9]+),(-?[0-9]+),(-?[0-9]+)\)", outcome) if isinstance(outcome, str) else None
    require(outcome is None or match is not None, "outcome outside declared authored source grammar")
    matched_action = match is not None and [int(value) for value in match.groups()[1:]] == action["values"]
    observed = match.group(1) == "True" if matched_action else None
    predicted = None if action["prediction_ambiguous"] else action["predicted"]
    if outcome is None:
        diagnosis = "missing_outcome"
    elif not matched_action:
        diagnosis = "outcome_action_mismatch"
    elif action["prediction_ambiguous"]:
        diagnosis = "ambiguous_prediction"
    elif predicted is None:
        diagnosis = "absent_prediction"
    else:
        diagnosis = "agreement" if predicted == observed else "contradicted_prediction"
    return {"try": action["values"], "observed": observed, "predicted": predicted}, diagnosis


def expected(source, skill, helper=None):
    if skill in ("addition", "copy"):
        require(source["source_id"] == sha(encoded({key: value for key, value in source.items() if key != "source_id"})), "canary identity mismatch")
        return str(source["left"] + source["right"]) if skill == "addition" else source["text"]
    fields, diagnosis = evidence(source, helper)
    if skill == "self_reflection":
        return {"diagnosis": diagnosis, "next_action": POLICY[diagnosis], "evidence": fields}
    require(skill == "perception", "unknown skill")
    if diagnosis in CASES[3:]:
        return {"abstain": True, "reason": diagnosis}
    assessment = helper.assess_source(source)
    require(assessment["admissible"], "record source assessment disagreement")
    return {field: copy.deepcopy(assessment["proof"][field]["value"]) for field in ("try", "observed", "predicted", "relation")}


def make_row(source, skill, skin, helper):
    fields, diagnosis = evidence(source, helper)
    events = "\n\n".join("Event " + entry["event_id"] + "\n" + entry["raw_response"] + "\n[OUTCOME] " +
                             ("[No public outcome supplied]" if entry["raw_outcome"] is None else entry["raw_outcome"])
                             for entry in source["events"])
    messages = [{"role": "user", "content": skin.format(events=events) + "\n\n" + (PERCEPTION_TASK if skill == "perception" else REFLECTION_TASK)}]
    target = canonical(expected(source, skill, helper))
    return {"row_id": skill + ":" + source["source_id"], "skill": skill, "input_messages": messages,
            "raw_target": target, "target_sha256": sha(target.encode()), "source": source,
            "source_proof": {"source_id": source["source_id"], "selected_event": copy.deepcopy(source["events"][-1]),
                             "public_fields": fields, "diagnosis": diagnosis, "input_sha256": sha(encoded(messages)),
                             "derivation": "selected public event and explicit availability only; reflection action is an authored policy choice, not evidence of execution"}}


def build_rows(skill, helper, reference):
    used = {tuple(triple) for triples in helper.SITUATIONS.values() for triple in triples} | {(20, 21, 22)}
    used.update(tuple(triple) for name in ("APPLICATION_TRIPLES", "DISTRACTOR_TRIPLES") for triple in reference[name])
    result = {}
    for split, repetitions, skins in (("train", 4, TRAIN_SKINS), ("held", 2, HELD_SKINS)):
        rows = []
        for skin_index, skin in enumerate(skins):
            for case in CASES:
                for index in range(repetitions):
                    key = (skill, split, skin_index, case, index)
                    values = fresh_triple(used, *key, "selected")
                    earlier_values = fresh_triple(used, *key, "earlier")
                    observed = bool(index % 2)
                    same_earlier = bool(index // 2) if split == "train" else bool((skin_index + index) % 2)
                    predicted = None if case == "absent_prediction" else observed if case == "agreement" else not observed
                    earlier = public_event("e0", earlier_values, not observed, observed if same_earlier else not observed)
                    selected = public_event("e1", values, predicted, observed)
                    if case == "ambiguous_prediction":
                        selected["raw_response"] = "PREDICT: T\nPREDICT: F\nACT: TRY " + ",".join(map(str, values))
                    elif case == "missing_outcome":
                        selected["raw_outcome"] = None
                    elif case == "outcome_action_mismatch":
                        selected["raw_outcome"] = earlier["raw_outcome"]
                    source = {"origin": helper.ORIGIN, "split": split, "template_id": f"{split}_{skin_index}",
                              "selected_event_id": "e1", "events": [earlier, selected]}
                    helper._identify(source)
                    row = make_row(source, skill, skin, helper)
                    require(row["source_proof"]["diagnosis"] == case, "source construction category mismatch")
                    rows.append(row)
        result[split] = rows
    return result


def canaries():
    rows = []
    alphabet = "abcdefghjkmnpqrstuvwxyz23456789"
    for index in range(6):
        for kind in ("addition", "copy"):
            if kind == "addition":
                source = {"origin": "AUTHOR_SOURCED_PRESERVATION_ONLY", "left": number("canary-add", index, 0) % 900 + 100,
                          "right": number("canary-add", index, 1) % 900 + 100}
                prompt = f"Compute {source['left']} + {source['right']}. Reply only with the base-10 integer, no surrounding whitespace."
            else:
                source = {"origin": "AUTHOR_SOURCED_PRESERVATION_ONLY",
                          "text": "".join(alphabet[number("canary-copy", index, position) % len(alphabet)] for position in range(10))}
                prompt = "Copy exactly the text inside <copy>. Reply only with that text, no surrounding whitespace.\n<copy>" + source["text"] + "</copy>"
            source["source_id"] = sha(encoded(source))
            target = expected(source, kind)
            messages = [{"role": "user", "content": prompt}]
            rows.append({"row_id": "canary:" + source["source_id"], "skill": kind, "input_messages": messages,
                         "raw_target": target, "target_sha256": sha(target.encode()), "source": source,
                         "source_proof": {"source_id": source["source_id"], "input_sha256": sha(encoded(messages)), "derivation": kind}})
    return rows


def build_dataset(skill, seed=0):
    require(skill in SKILLS, "skill must be perception or self_reflection")
    require(type(seed) is int and 0 <= seed < 2**32, "seed must be a nonnegative 32-bit integer, not bool")
    helper, reference = load_sources()
    rows = build_rows(skill, helper, reference)
    inventory = {}
    for split, items in rows.items():
        items.sort(key=lambda row: sha(encoded([seed, row["row_id"]])))
        inventory[split] = {"rows": len(items), "distinct_sources": len({row["source"]["source_id"] for row in items}),
                            "distinct_selected_triples": len({tuple(row["source_proof"]["public_fields"]["try"]) for row in items}),
                            "rows_per_skin": dict(Counter(row["source"]["template_id"] for row in items)),
                            "diagnosis_counts": dict(Counter(row["source_proof"]["diagnosis"] for row in items))}
        require(inventory[split]["rows"] == inventory[split]["distinct_sources"] == inventory[split]["distinct_selected_triples"], "source reuse forbidden")
        require(inventory[split]["diagnosis_counts"] == {case: 16 if split == "train" else 8 for case in CASES}, "case balance failed")
    return {"schema": SCHEMA, "qualification": QUALIFICATION,
            "provenance": {"skill": skill, "generator_sha256": sha(Path(__file__).read_bytes()), "source_pins": copy.deepcopy(PINS),
                           "source_seed": DATA_SEED, "order_seed": seed, "seed_scope": "order only; stable source and target content",
                           "templates": {"train": list(TRAIN_SKINS), "held": list(HELD_SKINS), "perception": PERCEPTION_TASK,
                                         "reflection": REFLECTION_TASK, "policy": copy.deepcopy(POLICY)},
                           "reference_reflection_procedures": reference["PROCEDURES"],
                           "parser_interface": copy.deepcopy(helper._interface().source_manifest), "source_inventory": inventory,
                           "selection": "4skins x6cases x4train/2held; full fixed selection; unique SHA256 triples with bounded rejection; no hidden outcomes or model outputs",
                           "grouping": "one distinct source per row_id; no repeated situation across skins; canaries shared across the two skills",
                           "supervision": "raw_target plus native assistant EOS; all prompt context masked; no truncation; native verification pending",
                           "context_tokens": None, "native_executed": False,
                           "claim_limits": ["Perception supported records retain actual four-field production grammar; author-screen abstentions are not compiler records.",
                                            "Self-reflection is source-diagnosis/procedure-choice classification with evidence, NOT full reflection, mental truth, or executed learning action.",
                                            "Raw36 criterion is future raw experiential field/admission properties versus base, not recursive or closed-loop learning.",
                                            "No compiler/admission wrapper, model outputs, native recipe, or child SLEEP is implemented."]},
            "training": rows["train"], "evaluation": {"held": rows["held"], "canary": canaries()}}


def schema_errors(response, skill):
    errors = []
    if type(response) is not dict:
        return ["JSON_object_required"]
    def check_fields(value, keys, prefix=""):
        if type(value) is not dict or set(value) != set(keys):
            errors.append(prefix + "exact_keys_required")
            return False
        return True
    def check_evidence(value, nullable_observed, prefix=""):
        if not check_fields(value, ("try", "observed", "predicted"), prefix):
            return
        if type(value["try"]) is not list or len(value["try"]) != 3 or any(type(item) is not int for item in value["try"]):
            errors.append(prefix + "try:integer_triple_required")
        if type(value["observed"]) is not bool and not (nullable_observed and value["observed"] is None):
            errors.append(prefix + "observed:boolean_required")
        if value["predicted"] is not None and type(value["predicted"]) is not bool:
            errors.append(prefix + "predicted:boolean_or_null_required")
    if skill == "self_reflection":
        if check_fields(response, ("diagnosis", "next_action", "evidence")):
            if type(response["diagnosis"]) is not str or response["diagnosis"] not in POLICY:
                errors.append("diagnosis:invalid_domain")
            if type(response["next_action"]) is not str or response["next_action"] not in POLICY.values():
                errors.append("next_action:invalid_domain")
            check_evidence(response["evidence"], True, "evidence.")
    elif "abstain" in response:
        if check_fields(response, ("abstain", "reason")):
            if type(response["abstain"]) is not bool or response["abstain"] is not True:
                errors.append("abstain:true_boolean_required")
            if type(response["reason"]) is not str or response["reason"] not in CASES[3:]:
                errors.append("reason:invalid_domain")
    elif check_fields(response, ("try", "observed", "predicted", "relation")):
        check_evidence({key: response[key] for key in ("try", "observed", "predicted")}, False)
        if type(response["relation"]) is not str or response["relation"] not in ("matched", "mismatched", "unavailable"):
            errors.append("relation:invalid_domain")
    return errors


def leaf_values(value, prefix=""):
    if type(value) is dict:
        return {path: item for key, child in value.items() for path, item in leaf_values(child, prefix + key + ".").items()}
    return {prefix[:-1]: value}


def score_row(row, raw, finish_reason):
    helper = load_sources()[0] if row["skill"] in SKILLS else None
    target = expected(row["source"], row["skill"], helper)
    target_text = canonical(target) if isinstance(target, dict) else target
    require(row["raw_target"] == target_text and row["target_sha256"] == sha(target_text.encode()), "target/provenance mismatch")
    proof = row["source_proof"]
    require(proof["source_id"] == row["source"]["source_id"] and proof["input_sha256"] == sha(encoded(row["input_messages"])), "proof/input mismatch")
    if helper:
        fields, diagnosis = evidence(row["source"], helper)
        require(proof["public_fields"] == fields and proof["diagnosis"] == diagnosis and proof["selected_event"] == row["source"]["events"][-1], "source proof mismatch")
    target_fields = leaf_values(target) if type(target) is dict else {}
    result = {"passed": False, "content_correct": False, "strict": False, "strict_pass": False, "format": "unparseable",
              "raw": raw, "raw_sha256": sha(raw.encode()) if isinstance(raw, str) else None, "finish_reason": finish_reason,
              "syntax_errors": [], "schema_errors": [], "source_errors": [], "completion_errors": [],
              "field_correct": {field: None for field in target_fields}, "qualification": QUALIFICATION}
    if finish_reason != "stop":
        result["completion_errors"] = ["missing_failed_or_truncated_completion"]
    if not isinstance(raw, str):
        result["syntax_errors"] = ["response_not_text"]
        return result
    if row["skill"] == "copy":
        result["format"] = "exact" if raw == target else "unparseable"
        result["passed"] = result["content_correct"] = result["strict"] = result["strict_pass"] = raw == target and finish_reason == "stop"
        if raw != target:
            result["source_errors"] = ["nonexact_copy"]
        return result
    text = raw.strip()
    fence = re.fullmatch(r"```(?:json)?[ \t]*\r?\n([\s\S]*?)\r?\n```", text)
    if fence:
        text = fence.group(1)
    try:
        response = (helper or load_sources()[0])._interface().decode(text)
    except (ValueError, TypeError) as error:
        result["syntax_errors"] = [str(error)]
        return result
    result["format"] = "fenced" if fence else "exact" if raw == canonical(response) else "json_noncanonical"
    if row["skill"] == "addition":
        if type(response) is not int:
            result["schema_errors"] = ["integer_required_no_type_coercion"]
        elif response != int(target):
            result["source_errors"] = ["arithmetic_value"]
    else:
        result["schema_errors"] = schema_errors(response, row["skill"])
        if not result["schema_errors"]:
            response_fields = leaf_values(response)
            if set(response_fields) != set(target_fields):
                result["source_errors"] = ["output_variant"]
            else:
                for field, value in target_fields.items():
                    correct = response_fields[field] == value
                    result["field_correct"][field] = correct
                    if not correct:
                        result["source_errors"].append(field)
    result["passed"] = result["content_correct"] = not (result["schema_errors"] or result["source_errors"]) and finish_reason == "stop"
    result["strict"] = result["strict_pass"] = result["content_correct"] and raw == target_text
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill", choices=SKILLS, required=True)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    target = args.output.resolve()
    require(not target.is_relative_to(ROOT.resolve()) and not target.is_relative_to(SOURCE_ROOT), "no repository/source output")
    payload = encoded(build_dataset(args.skill, args.seed))
    with target.open("xb") as stream:
        stream.write(payload)
    print(canonical({"path": str(target), "sha256": sha(payload), "native_executed": False}))


if __name__ == "__main__":
    main()
