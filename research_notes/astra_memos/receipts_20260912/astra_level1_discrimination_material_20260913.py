"""CPU authored Level1 screens; no native runner, hidden gym, or child SLEEP."""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import hashlib
import json
import os
from pathlib import Path
import re
from types import ModuleType


SCHEMA = "astra_level1_discrimination_material_20260913_v1"
QUALIFICATION = "AUTHOR_SCREEN_LEVEL1_ONLY_NOT_PRODUCTION_GRAMMAR_NOT_CHILD_SLEEP"
SKILLS = ("contradiction", "update_judgement")
ROOT = Path("/data/home/rohing/dream-state")
SOURCE_ROOT = Path(os.environ.get("ASTRA_LEVEL1_SOURCE_ROOT", str(ROOT))).resolve()
DATA_SEED = 2026091334
PINS = {
    "organism_v6/birth_skill_corpus.py": "078ceba07141b5f6fb2159a12e21f1eccc0901ba9f51f52d1793d988927812f6",
    "organism_v6/rulegame_parenting_diagnostic.py": "e6055da48b2c6fa1bd294c9d991e07f32f05dc6630fe8973373977bdfe977526",
}
TRAIN_SKINS = (
    "Public timeline\n{events}\nAssess the selected final event {selected}.",
    "Independent authored case file\n{events}\nThe response subject is the last event, {selected}.",
    "Observation ledger, chronological order\n{events}\nUse event {selected}, not the earlier entry.",
    "Local evidence card\n{events}\nOnly the final execution {selected} is selected.",
)
HELD_SKINS = (
    "Audit transcript\n{events}\nThe last listed execution ({selected}) is the one under review.",
    "Two-event archive\n{events}\nReport about {selected}; the preceding execution is context only.",
    "Recorded evidence, oldest first\n{events}\nSelect the final event {selected} and its own supplied result.",
    "Execution dossier\n{events}\nFor this question the selected execution is {selected}, the last event.",
)
INSTRUCTIONS = {
    "contradiction": (
        'AUTHOR-SCREEN, not a production record. Does the selected event\'s explicit prior PREDICT conflict with its own supplied outcome? '
        'Return only a JSON object with exactly "event_id", "verdict", "reason". '
        'verdict is "agree", "disagree", or "insufficient". '
        'reason is "agreement", "disagreement", "missing_prediction", "ambiguous_prediction", '
        '"missing_outcome", "invalid_outcome", or "outcome_action_mismatch". '
        'Check outcome presence, syntax and action identity first; then prior prediction ambiguity or absence; then compare the two Boolean values. '
        'Absent or ambiguous prediction cannot establish agreement or disagreement. Never borrow an earlier outcome or infer a hidden rule.'
    ),
    "update_judgement": (
        'AUTHOR-SCREEN for a proposed local observation-record update, not permission to change a hidden rule or production admission policy. '
        'Return only a JSON object with exactly "event_id", "decision", "reason". '
        'decision is "admit", "reject", or "abstain". '
        'reason is "supported", "source_mismatch", "ambiguous_prediction", "missing_outcome", "invalid_outcome", or "outcome_action_mismatch". '
        'Check selected outcome presence, syntax and action identity, then prediction ambiguity. If evidence is insufficient, abstain regardless of candidate plausibility. '
        'Otherwise admit exactly when all candidate try/observed/predicted/relation fields match the selected event; reject any mismatch. '
        'No prior prediction is allowed: predicted must be null and relation unavailable. With a prediction, relation is matched for equal prediction/outcome and mismatched otherwise. '
        'Use the selected event only, not an earlier execution. The candidate is a proposal, not trusted evidence.'
    ),
}
CANARY_TEMPLATES = {
    "addition": "Compute {left} + {right}. Reply only with the base-10 integer, with no surrounding whitespace.",
    "copy": "Copy the text inside <copy> exactly. Reply only with that text, with no surrounding whitespace.\n<copy>{text}</copy>",
}


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":"))


def encoded(value):
    return (canonical(value) + "\n").encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def corpus():
    for relative, expected in PINS.items():
        require(sha((SOURCE_ROOT / relative).read_bytes()) == expected, "source pin mismatch: " + relative)
    path = SOURCE_ROOT / "organism_v6/birth_skill_corpus.py"
    module = ModuleType("frozen_level1_source")
    module.__file__ = str(path)
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    return module


def number(*parts):
    return int(sha(encoded([SCHEMA, DATA_SEED, *parts])), 16)


def fresh_triple(used, *parts):
    for nonce in range(1000):
        result = tuple(number(*parts, coordinate, nonce) % 2001 - 1000 for coordinate in range(3))
        if result not in used:
            used.add(result)
            return result
    raise ValueError("triple generation exhausted")


def relation(predicted, observed):
    return "unavailable" if predicted is None else "matched" if predicted == observed else "mismatched"


def record(values, predicted, observed):
    return {"try": list(values), "predicted": predicted, "observed": observed,
            "relation": relation(predicted, observed)}


def event(event_id, values, predicted, observed):
    triple = ",".join(map(str, values))
    return {"event_id": event_id,
            "raw_response": ("" if predicted is None else "PREDICT: " + ("T" if predicted else "F") + "\n") + "ACT: TRY " + triple,
            "raw_outcome": f"the box says: {observed} for ({triple})"}


def assess(source, helper):
    require(source["source_id"] == helper._identify(copy.deepcopy(source))["source_id"], "source identity mismatch")
    require(source["origin"] == helper.ORIGIN, "not authored public evidence")
    require(len(source["events"]) == 2 and len({entry["event_id"] for entry in source["events"]}) == 2,
            "two unique chronological events required")
    selected = source["events"][-1]
    require(selected["event_id"] == source["selected_event_id"], "selected event is not final")
    action = helper._interface().parse_action(selected["raw_response"], "interaction_v3")
    require(action["kind"] == "try", "selected action must be TRY")
    outcome = selected["raw_outcome"]
    match = re.fullmatch(r"the box says: (True|False) for \((-?[0-9]+),(-?[0-9]+),(-?[0-9]+)\)", outcome) if isinstance(outcome, str) else None
    if outcome is None:
        reason = "missing_outcome"
    elif match is None:
        reason = "invalid_outcome"
    elif [int(value) for value in match.groups()[1:]] != action["values"]:
        reason = "outcome_action_mismatch"
    elif action["prediction_ambiguous"]:
        reason = "ambiguous_prediction"
    else:
        reason = None
    observed = None if match is None or [int(value) for value in match.groups()[1:]] != action["values"] else match.group(1) == "True"
    predicted = None if action["prediction_ambiguous"] else action["predicted"]
    return {"event_id": selected["event_id"], "values": action["values"], "predicted": predicted,
            "observed": observed, "reason": reason, "prediction_ambiguous": action["prediction_ambiguous"]}


def expected(source, skill, helper):
    if skill in ("addition", "copy"):
        require(source["source_id"] == sha(encoded({key: value for key, value in source.items() if key != "source_id"})), "canary identity mismatch")
        return str(source["left"] + source["right"]) if skill == "addition" else source["text"]
    state = assess(source, helper)
    reason = state["reason"]
    if skill == "contradiction":
        reason = reason or ("missing_prediction" if state["predicted"] is None else None)
        verdict = "insufficient" if reason else "agree" if state["predicted"] == state["observed"] else "disagree"
        return {"event_id": state["event_id"], "verdict": verdict,
                "reason": reason or ("agreement" if verdict == "agree" else "disagreement")}
    require(skill == "update_judgement", "unknown skill")
    if reason:
        return {"event_id": state["event_id"], "decision": "abstain", "reason": reason}
    assessment = helper.assess_source(source)
    require(assessment["admissible"], "public interface disagreement")
    supported = helper._interface().judge_record(canonical(source["candidate_record"]), assessment["execution"])["eligible"]
    return {"event_id": state["event_id"], "decision": "admit" if supported else "reject",
            "reason": "supported" if supported else "source_mismatch"}


def make_row(source, skill, skin, helper):
    state = assess(source, helper)
    target = canonical(expected(source, skill, helper))
    events = "\n\n".join("Event " + entry["event_id"] + "\n" + entry["raw_response"] + "\n[OUTCOME] "
                             + ("[No public outcome supplied]" if entry["raw_outcome"] is None else entry["raw_outcome"])
                             for entry in source["events"])
    prompt = skin.format(events=events, selected=source["selected_event_id"])
    if skill == "update_judgement":
        prompt += "\nCandidate local observation record:\n" + canonical(source["candidate_record"])
    prompt += "\n\n" + INSTRUCTIONS[skill]
    return {"row_id": skill + ":" + source["source_id"], "skill": skill,
            "input_messages": [{"role": "user", "content": prompt}], "raw_target": target,
            "target_sha256": sha(target.encode()), "source": source,
            "source_proof": {"source_id": source["source_id"], "selected_event": copy.deepcopy(source["events"][-1]),
                             "parsed_evidence": state, "input_sha256": sha(encoded([{"role": "user", "content": prompt}])),
                             "derivation": "selected public action/result availability and candidate comparison only",
                             "interface": "new_author_screen_not_production_output"}}


def task_rows(skill, helper):
    used = {tuple(values) for triples in helper.SITUATIONS.values() for values in triples} | {(20, 21, 22)}
    splits = {}
    for split, repetitions, skins in (("train", 8, TRAIN_SKINS), ("held", 4, HELD_SKINS)):
        rows = []
        for skin_index, skin in enumerate(skins):
            for bucket in range(3):
                for index in range(repetitions):
                    key = (skill, split, skin_index, bucket, index)
                    values = fresh_triple(used, *key, "selected")
                    earlier_values = fresh_triple(used, *key, "earlier")
                    observed = bool(index % 2)
                    same_earlier = bool((index // 2) % 2)
                    predicted = observed if (bucket == 0 if skill == "contradiction" else (skin_index + index // 2) % 2 == 0) else not observed
                    if skill == "update_judgement" and (index + skin_index) % 4 == 0:
                        predicted = None
                    earlier = event("e0", earlier_values, not observed, observed if same_earlier else not observed)
                    selected = event("e1", values, predicted, observed)
                    if bucket == 2:
                        variants = (("missing_prediction", "ambiguous_prediction", "missing_outcome", "foreign_outcome")
                                    if skill == "contradiction" else ("ambiguous_prediction", "missing_outcome", "foreign_outcome", "invalid_outcome"))
                        variant = variants[(skin_index + index // 4) % 4]
                        if variant == "missing_prediction":
                            selected = event("e1", values, None, observed)
                        elif variant == "ambiguous_prediction":
                            selected["raw_response"] = "PREDICT: T\nPREDICT: F\nACT: TRY " + ",".join(map(str, values))
                        elif variant == "missing_outcome":
                            selected["raw_outcome"] = None
                        elif variant == "foreign_outcome":
                            selected["raw_outcome"] = earlier["raw_outcome"]
                        else:
                            selected["raw_outcome"] = "the box returned: unknown"
                    source = {"origin": helper.ORIGIN, "split": split, "template_id": f"{split}_{skin_index}",
                              "selected_event_id": "e1", "events": [earlier, selected]}
                    if skill == "update_judgement":
                        candidate = record(values, predicted, observed)
                        if bucket == 1:
                            corruption = (skin_index + index // 2) % 4
                            if corruption == 0:
                                candidate = record(earlier_values, predicted, observed)
                            elif corruption == 1:
                                candidate = record(values, predicted, not observed)
                            elif corruption == 2:
                                candidate = record(values, not predicted if predicted is not None else True, observed)
                            else:
                                candidate = record(values, not predicted if predicted is not None else False, not observed)
                        source["candidate_record"] = candidate
                    helper._identify(source)
                    rows.append(make_row(source, skill, skin, helper))
        splits[split] = rows
    return splits


def canaries():
    rows = []
    alphabet = "abcdefghjkmnpqrstuvwxyz23456789"
    for index in range(6):
        for kind in ("addition", "copy"):
            source = {"origin": "AUTHOR_SOURCED_PRESERVATION_ONLY", "kind": kind,
                      "left": number("canary-add", index, "left") % 900 + 100,
                      "right": number("canary-add", index, "right") % 900 + 100} if kind == "addition" else {
                          "origin": "AUTHOR_SOURCED_PRESERVATION_ONLY", "kind": kind,
                          "text": "".join(alphabet[number("canary-copy", index, position) % len(alphabet)] for position in range(10))}
            source["source_id"] = sha(encoded(source))
            target = expected(source, kind, None)
            rows.append({"row_id": "canary:" + source["source_id"], "skill": kind,
                         "input_messages": [{"role": "user", "content": CANARY_TEMPLATES[kind].format(**source)}],
                         "raw_target": target, "target_sha256": sha(target.encode()), "source": source,
                         "source_proof": {"source_id": source["source_id"], "derivation": "integer_addition" if kind == "addition" else "exact_public_copy"}})
    return rows


def build_dataset(skill, seed=0):
    require(skill in SKILLS, "skill must be contradiction or update_judgement")
    require(type(seed) is int and 0 <= seed < 2**32, "seed must be a nonnegative 32-bit integer, not bool")
    helper = corpus()
    splits = task_rows(skill, helper)
    for rows in splits.values():
        rows.sort(key=lambda row: sha(encoded([seed, row["row_id"]])))
    label = "verdict" if skill == "contradiction" else "decision"
    expected_labels = {"agree", "disagree", "insufficient"} if skill == "contradiction" else {"admit", "reject", "abstain"}
    counts = {split: Counter(json.loads(row["raw_target"])[label] for row in rows) for split, rows in splits.items()}
    require(counts["train"] == {value: 32 for value in expected_labels} and counts["held"] == {value: 16 for value in expected_labels}, "label balance failed")
    inventory = {split: {"rows": len(rows), "distinct_sources": len({row["source"]["source_id"] for row in rows}),
                         "distinct_selected_triples": len({tuple(row["source_proof"]["parsed_evidence"]["values"]) for row in rows}),
                         "rows_per_skin": dict(Counter(row["source"]["template_id"] for row in rows))}
                 for split, rows in splits.items()}
    require(all(item["rows"] == item["distinct_sources"] == item["distinct_selected_triples"] for item in inventory.values()),
            "situation reuse forbidden")
    return {"schema": SCHEMA, "qualification": QUALIFICATION,
            "provenance": {"skill": skill, "order_seed": seed, "source_seed": DATA_SEED,
                           "seed_scope": "order only; all source, target and template bytes independent of learner/order seed",
                           "source_pins": copy.deepcopy(PINS), "generator_sha256": sha(Path(__file__).read_bytes()),
                           "templates": {"train": list(TRAIN_SKINS), "held": list(HELD_SKINS), "instructions": copy.deepcopy(INSTRUCTIONS),
                                         "canary": copy.deepcopy(CANARY_TEMPLATES)},
                           "interface_source": copy.deepcopy(helper._interface().source_manifest),
                           "selection": "full factorial:4skins x3labels x8train/4held; observation polarity and earlier agreement balanced; four insufficient subtypes; bounded disjoint SHA256 triples",
                           "label_counts": counts, "source_inventory": inventory,
                           "ancestry": "fresh authored events; inherited public grammar only; no source re-rendering within or across train/held",
                           "grouping": "one source and one group per row_id; canaries are intentionally shared across skill datasets",
                           "native_tokenization": "NOT_RUN", "context_tokens": None,
                           "supervision_contract": "raw_target bytes plus native EOS; context masked; native boundary/no-truncation verification required",
                           "claim_limits": ["authored source-bound screens only; no hidden-rule induction or mental truth",
                                            "judgement is candidate record support, not a complete belief-update or production admission policy",
                                            "four train skins and four held skins; source situations are disjoint, grammar intentionally shared",
                                            "canaries shared across skills, not independent replications; no recipe specified",
                                            "Main's proposed fresh320 skill fit is SEQ113-inspired, not a faithful SEQ113 warm80 plus320 parent replication"]},
            "training": splits["train"], "evaluation": {"held": splits["held"], "canary": canaries()}}


def score_row(row, raw, finish_reason):
    helper = corpus() if row["skill"] in SKILLS else None
    target = expected(row["source"], row["skill"], helper)
    target_text = canonical(target) if isinstance(target, dict) else target
    require(row["raw_target"] == target_text and row["target_sha256"] == sha(target_text.encode()), "target/provenance mismatch")
    if helper is not None:
        require(row["source_proof"]["source_id"] == row["source"]["source_id"]
                and row["source_proof"]["selected_event"] == row["source"]["events"][-1]
                and row["source_proof"]["parsed_evidence"] == assess(row["source"], helper)
                and row["source_proof"]["input_sha256"] == sha(encoded(row["input_messages"])), "proof mismatch")
    result = {"passed": False, "content_correct": False, "strict": False, "strict_pass": False,
              "format": "unparseable", "raw": raw,
              "raw_sha256": sha(raw.encode()) if isinstance(raw, str) else None,
              "finish_reason": finish_reason, "syntax_errors": [], "schema_errors": [],
              "source_errors": [], "completion_errors": [], "field_correct": {field: None for field in target} if isinstance(target, dict) else {},
              "qualification": QUALIFICATION}
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
        response = (helper or corpus())._interface().decode(text)
    except (ValueError, TypeError) as error:
        result["syntax_errors"] = [str(error)]
        return result
    result["format"] = "fenced" if fence else "exact" if raw == canonical(response) else "json_noncanonical"
    if row["skill"] == "addition":
        if type(response) is not int:
            result["schema_errors"] = ["integer_required_no_type_coercion"]
        elif response != int(target):
            result["source_errors"] = ["arithmetic_value"]
        result["passed"] = result["content_correct"] = not (result["schema_errors"] or result["source_errors"]) and finish_reason == "stop"
        result["strict"] = result["strict_pass"] = result["content_correct"] and raw == target_text
        return result
    if type(response) is not dict or set(response) != set(target):
        result["schema_errors"] = ["exact_author_screen_fields_required"]
        return result
    domains = ({"verdict": {"agree", "disagree", "insufficient"},
                "reason": {"agreement", "disagreement", "missing_prediction", "ambiguous_prediction", "missing_outcome", "invalid_outcome", "outcome_action_mismatch"}}
               if row["skill"] == "contradiction" else
               {"decision": {"admit", "reject", "abstain"},
                "reason": {"supported", "source_mismatch", "ambiguous_prediction", "missing_outcome", "invalid_outcome", "outcome_action_mismatch"}})
    for field, value in response.items():
        if type(value) is not str or (field in domains and value not in domains[field]):
            result["schema_errors"].append(field + ":invalid_type_or_domain")
    if result["schema_errors"]:
        return result
    for field in target:
        result["field_correct"][field] = response[field] == target[field]
        if not result["field_correct"][field]:
            result["source_errors"].append(field)
    result["passed"] = result["content_correct"] = not result["source_errors"] and finish_reason == "stop"
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
    dataset = build_dataset(args.skill, args.seed)
    payload = encoded(dataset)
    with target.open("xb") as stream:
        stream.write(payload)
    print(canonical({"path": str(target), "sha256": sha(payload), "native_executed": False}))


if __name__ == "__main__":
    main()
