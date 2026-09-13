"""Frozen authored CPU reflection fixtures; no model, fit, or promotion."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import copy
import hashlib
import json
from pathlib import Path

from organism_v6 import birth_skill_corpus as corpus


SCHEMA = "birth_reflection_probe_v1"
GENERIC_SYSTEM = "You are a helpful assistant."
PARENT_CONDITIONS = ("present", "withdrawn")
RESTATEMENT_TASK = "Summarize the selected public event and state a reusable recording procedure in 2-3 sentences."
RESTATEMENT_PROMPT_TRANSFORM = "nondeictic_event_procedure_v1"
HISTORICAL_RESTATEMENT_TASK = "Restate that message in your own words in 2-3 sentences."
HISTORICAL_PARENT_FRAMING = "Your parent said:\n"
APPLICATION_TASK = (
    "Choose the source-supported correction procedure for the final executed TRY. "
    "The earlier event is context, not the selected execution. "
    "Reply with exactly A or B, with no whitespace, punctuation or explanation."
)
APPLICATION_TRIPLES = ((31, -17, 8), (-23, 19, 6))
DISTRACTOR_TRIPLES = ((41, 42, 43), (-31, -32, -33))
APPLICATION_CASES = (
    ("matched_true", "T", True),
    ("matched_false", "F", False),
    ("mismatched_true", "F", True),
    ("mismatched_false", "T", False),
    ("unavailable_true", None, True),
    ("unavailable_false", None, False),
)
FIRST_BOX_LABELS = ("A", "B", "B", "A", "A", "B")
PROCEDURES = {
    "matched": "Compare prediction and outcome as an agreement without inferring a hidden rule.",
    "mismatched": "Preserve the returned outcome despite the contradicted prediction without inferring a hidden rule.",
    "unavailable": "Leave the absent prior prediction null rather than inventing one from the outcome.",
}
SOURCE_PINS = {
    "birth_skill_corpus.py": "078ceba07141b5f6fb2159a12e21f1eccc0901ba9f51f52d1793d988927812f6",
    "rulegame_parenting_diagnostic.py": "e6055da48b2c6fa1bd294c9d991e07f32f05dc6630fe8973373977bdfe977526",
}
MASK_CONTRACT = {
    "input_messages": "context only; all rendered prompt tokens masked",
    "response_target": "entire assistant response supervised, not a suffix or selected words",
    "eos": "native runner appends exactly one supervised assistant EOS after response_target",
    "eos_in_response_target": False,
    "chat_template": "native runner renders explicit system/user messages and assistant prefix once",
    "truncation": "forbidden; native runner must verify zero prompt/target loss",
    "native_tokenization_verified": False,
}


def _json(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False)


def _digest(value):
    return hashlib.sha256(_json(value).encode()).hexdigest()


def _text_hash(text):
    return hashlib.sha256(text.encode()).hexdigest()


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def verify_sources():
    actual = {}
    for name, expected in SOURCE_PINS.items():
        actual[name] = hashlib.sha256(Path(corpus.__file__).with_name(name).read_bytes()).hexdigest()
        _require(actual[name] == expected, f"historical source pin mismatch: {name}")
    return actual


def withdraw_parent_correction(user_text):
    _require(isinstance(user_text, str), "user text must be a string")
    marker = "\n" + corpus.PUBLIC_CORRECTION + "\n"
    _require(user_text.count(corpus.PUBLIC_CORRECTION) == 1 and user_text.count(marker) == 1,
             "exactly one standalone PUBLIC_CORRECTION is required")
    return user_text.replace(marker, "\n", 1)


def _messages(present_user, parent_condition):
    _require(parent_condition in PARENT_CONDITIONS, "explicit present or withdrawn condition required")
    withdrawn = withdraw_parent_correction(present_user)
    user = present_user if parent_condition == "present" else withdrawn
    return [{"role": "system", "content": GENERIC_SYSTEM}, {"role": "user", "content": user}]


def _row(panel, split, parent_condition, source, proof, messages, target, **extra):
    return {
        "row_id": f"{panel}:{source['source_id']}",
        "panel": panel,
        "split": split,
        "parent_condition": parent_condition,
        "source": copy.deepcopy(source),
        "source_proof": copy.deepcopy(proof),
        "input_messages": messages,
        "response_target": target,
        "input_sha256": _digest(messages),
        "target_sha256": _text_hash(target),
        **extra,
    }


def _restatement_rows(split, parent_condition):
    built = corpus.build_slice("reflection", split=split, system_anchor=GENERIC_SYSTEM)
    rows = []
    for original in built["rows"]:
        original_user = original["input_messages"][-1]["content"]
        _require(original_user.startswith(HISTORICAL_PARENT_FRAMING)
                 and original_user.endswith("\n" + HISTORICAL_RESTATEMENT_TASK),
                 "historical restatement framing/task drift")
        present_user = (original_user[len(HISTORICAL_PARENT_FRAMING):-len(HISTORICAL_RESTATEMENT_TASK)]
                        + RESTATEMENT_TASK)
        messages = _messages(present_user, parent_condition)
        rows.append(_row(
            "restatement", split, parent_condition, original["source"], original["source_proof"],
            messages, original["raw_target"], historical_row_id=original["row_id"],
            score_kind="exact_authored_restatement_only",
        ))
    return rows


def _event(event_id, triple, prediction, observed):
    values = ",".join(map(str, triple))
    prediction_line = "" if prediction is None else f"PREDICT: {prediction}\n"
    return {
        "event_id": event_id,
        "raw_response": prediction_line + f"ACT: TRY {values}",
        "raw_outcome": f"the box says: {observed} for ({values})",
    }


def _application_source(box, case):
    name, prediction, observed = case
    source = {
        "origin": corpus.ORIGIN,
        "split": "application_dev",
        "template_id": "procedure_application_v1",
        "situation_index": box,
        "case": name,
        "selected_event_id": "e1",
        "events": [
            _event("e0", DISTRACTOR_TRIPLES[box], "F" if observed else "T", not observed),
            _event("e1", APPLICATION_TRIPLES[box], prediction, observed),
        ],
    }
    return corpus._identify(source)


def _relation(predicted, observed):
    return "unavailable" if predicted is None else "matched" if predicted == observed else "mismatched"


def _claim(assessment):
    claim = {field: copy.deepcopy(assessment["proof"][field]["value"])
             for field in ("try", "observed", "predicted", "relation")}
    claim["procedure"] = PROCEDURES[claim["relation"]]
    return claim


def _foil(claim, box):
    foil = copy.deepcopy(claim)
    if claim["predicted"] is None:
        foil["predicted"] = claim["observed"]
    elif box == 0:
        foil["predicted"] = not claim["predicted"]
    else:
        foil["observed"] = not claim["observed"]
    foil["relation"] = _relation(foil["predicted"], foil["observed"])
    foil["procedure"] = PROCEDURES[foil["relation"]]
    return foil


def _render_choice(claim):
    values = ",".join(map(str, claim["try"]))
    prediction = "not supplied" if claim["predicted"] is None else str(claim["predicted"])
    return (
        f"For the final TRY {values}, retain outcome {claim['observed']} and prior prediction "
        f"{prediction}; their relation is {claim['relation']}. For later notes: {claim['procedure']}"
    )


def semantic_choice_proof(source, choices):
    assessment = corpus.assess_source(source)
    _require(assessment["admissible"], "application source must be publicly admissible")
    _require(isinstance(choices, dict) and set(choices) == {"A", "B"}, "exact A/B choice pair required")
    expected = _claim(assessment)
    verdicts = {}
    for label, choice in choices.items():
        _require(isinstance(choice, dict) and set(choice) == set(expected), "choice claim schema mismatch")
        mismatches = [field for field in expected if _json(choice[field]) != _json(expected[field])]
        verdicts[label] = {"supported": not mismatches, "mismatched_fields": mismatches}
    supported = [label for label in ("A", "B") if verdicts[label]["supported"]]
    _require(len(supported) == 1, "exactly one choice must be supported by public source")
    return {
        "source_fields": copy.deepcopy(assessment["proof"]),
        "procedure_origin": "AUTHOR_SOURCED_DEVELOPMENT_ONLY",
        "public_correction_sha256": _text_hash(corpus.PUBLIC_CORRECTION),
        "options": verdicts,
        "supported_choice": supported[0],
        "scope": "structured frozen option proof, not semantic scoring of generated prose",
    }


def _application_rows(parent_condition):
    rows = []
    for box in range(2):
        for case_index, case in enumerate(APPLICATION_CASES):
            source = _application_source(box, case)
            correct = _claim(corpus.assess_source(source))
            label = FIRST_BOX_LABELS[case_index]
            if box == 1:
                label = "B" if label == "A" else "A"
            other = "B" if label == "A" else "A"
            choices = {label: correct, other: _foil(correct, box)}
            proof = semantic_choice_proof(source, choices)
            option_texts = {key: _render_choice(choices[key]) for key in ("A", "B")}
            events = "\n\n".join(
                f"Event {event['event_id']}\n{event['raw_response']}\n[OUTCOME] {event['raw_outcome']}"
                for event in source["events"]
            )
            present_user = (
                "Public procedure application:\n" + events + "\n" + corpus.PUBLIC_CORRECTION + "\n"
                + APPLICATION_TASK + "\nA: " + option_texts["A"] + "\nB: " + option_texts["B"]
            )
            rows.append(_row(
                "application", "dev", parent_condition, source, proof,
                _messages(present_user, parent_condition), proof["supported_choice"],
                choices=choices, option_texts=option_texts, score_kind="strict_application_choice",
            ))
    return sorted(rows, key=lambda row: _digest([corpus.SEED, row["row_id"]]))


def _baseline(rows, features):
    groups = defaultdict(Counter)
    for row in rows:
        source = row["source"]
        assessment = corpus.assess_source(source)
        values = {
            "case": source["case"],
            "triple": assessment["execution"]["values"],
            "prediction": assessment["execution"]["predicted"],
            "outcome": assessment["execution"]["observed"],
            "relation": assessment["proof"]["relation"]["value"],
        }
        groups[_json([values[field] for field in features])][row["response_target"]] += 1
    correct = sum(max(counts.values()) for counts in groups.values())
    return {"correct": correct, "total": len(rows), "accuracy": correct / len(rows)}


def _application_audit(rows):
    _require(len(rows) == 12, "application panel must contain exactly twelve rows")
    _require(len({row["row_id"] for row in rows}) == 12, "duplicate application row")
    _require(len({row["input_sha256"] for row in rows}) == 12, "duplicate application input")
    counts = dict(Counter(row["response_target"] for row in rows))
    _require(counts == {"A": 6, "B": 6}, "application answer-order imbalance")
    baselines = {name: _baseline(rows, () if name == "constant" else (name,))
                 for name in ("constant", "case", "triple", "prediction", "outcome", "relation")}
    _require(all(result["correct"] == 6 for result in baselines.values()), "single-factor label shortcut")
    baselines["case_and_triple_memorization"] = _baseline(rows, ("case", "triple"))
    baselines["triple_and_prediction"] = _baseline(rows, ("triple", "prediction"))
    baselines["triple_and_outcome"] = _baseline(rows, ("triple", "outcome"))
    baselines["triple_and_relation"] = _baseline(rows, ("triple", "relation"))
    choice_groups = defaultdict(Counter)
    for row in rows:
        choice_groups[_json(row["option_texts"])][row["response_target"]] += 1
    choice_correct = sum(max(counts.values()) for counts in choice_groups.values())
    baselines["ordered_choices_without_event"] = {
        "correct": choice_correct, "total": len(rows), "accuracy": choice_correct / len(rows),
    }
    earlier_sources = corpus.public_sources("train") + corpus.public_sources("dev")
    historical_events = {corpus._hash([event["raw_response"], event["raw_outcome"]])
                         for source in earlier_sources for event in source["events"]}
    historical_triples = {tuple(corpus._interface().parse_action(event["raw_response"], "interaction_v3")["values"])
                          for source in earlier_sources for event in source["events"]}
    application_events = {corpus._hash([event["raw_response"], event["raw_outcome"]])
                          for row in rows for event in row["source"]["events"]}
    application_triples = {tuple(corpus._interface().parse_action(event["raw_response"], "interaction_v3")["values"])
                           for row in rows for event in row["source"]["events"]}
    _require(not historical_events & application_events, "application event overlaps historical split")
    _require(not historical_triples & application_triples, "application triple overlaps historical split")
    return {
        "choice_counts": counts,
        "case_counts": dict(Counter(row["source"]["case"] for row in rows)),
        "single_factor_and_memorization_baselines": baselines,
        "historical_event_overlap": 0,
        "historical_triple_overlap": 0,
        "scope": "in-sample label lookup baselines only; composite and option-only shortcuts remain; combined case/triple memorizes 12/12; no universal shortcut or semantic-generalization guarantee",
    }


def build_panel(panel, *, split, parent_condition):
    sources = verify_sources()
    _require(panel in ("restatement", "application"), "choose exactly one panel")
    _require(split in ("train", "dev"), "literal train or dev split required")
    _require(parent_condition in PARENT_CONDITIONS, "explicit present or withdrawn condition required")
    _require(panel != "application" or split == "dev", "application panel is DEV only, never training")
    rows = (_restatement_rows(split, parent_condition) if panel == "restatement"
            else _application_rows(parent_condition))
    audit = (_application_audit(rows) if panel == "application" else {
        "historical_targets_preserved": True,
        "historical_prompt_bytes_preserved": False,
        "prompt_transform": RESTATEMENT_PROMPT_TRANSFORM,
        "identical_across_parent_conditions": "remove parent framing and replace deictic task; preserve public event bytes",
        "historical_split_audit": corpus.audit_split_pair(
            corpus.build_slice("reflection", split="train", system_anchor=GENERIC_SYSTEM),
            corpus.build_slice("reflection", split="dev", system_anchor=GENERIC_SYSTEM),
        ),
    })
    return {
        "schema": SCHEMA,
        "manifest": {
            "origin": corpus.ORIGIN,
            "panel": panel,
            "split": split,
            "parent_condition": parent_condition,
            "generic_system": GENERIC_SYSTEM,
            "parent_correction_sha256": _text_hash(corpus.PUBLIC_CORRECTION),
            "historical_source_sha256": sources,
            "order_seed": corpus.SEED,
            "row_count": len(rows),
            "rows_sha256": _digest(rows),
            "audit": audit,
            "training_export_allowed": panel == "restatement" and split == "train",
            "native_ready": False,
            "scientific_claim": False,
            "auto_promotion": False,
            "curriculum": "authored public fixtures, not teacher generations, child experience or clean ancestry",
            "claim_limit": "development restatement/near-transfer only; no persistence, L2 or H1/H2 qualification",
        },
        "rows": rows,
    }


def validate_panel(built):
    _require(isinstance(built, dict) and isinstance(built.get("manifest"), dict), "panel schema missing")
    manifest = built["manifest"]
    expected = build_panel(manifest.get("panel"), split=manifest.get("split"),
                           parent_condition=manifest.get("parent_condition"))
    _require(_json(built) == _json(expected), "panel integrity mismatch against frozen construction")
    return expected


def _validate_row(row):
    _require(isinstance(row, dict), "row must be an object")
    built = build_panel(row.get("panel"), split=row.get("split"), parent_condition=row.get("parent_condition"))
    matches = [candidate for candidate in built["rows"] if candidate["row_id"] == row.get("row_id")]
    _require(len(matches) == 1 and _json(matches[0]) == _json(row), "row integrity mismatch")


def export_training(built):
    built = validate_panel(built)
    _require(built["manifest"]["training_export_allowed"], "only historical restatement TRAIN may enter training")
    records = [{"input_messages": copy.deepcopy(row["input_messages"]), "response_target": row["response_target"]}
               for row in built["rows"]]
    return {
        "schema": SCHEMA + "/training_export",
        "records": records,
        "report": {
            "panel_manifest": built["manifest"],
            "record_count": len(records),
            "application_rows": 0,
            "dev_rows": 0,
            "records_sha256": _digest(records),
            "row_ids_in_order": [row["row_id"] for row in built["rows"]],
            "targets_sha256": _digest([row["response_target"] for row in built["rows"]]),
            "target_utf8_bytes": sum(len(row["response_target"].encode()) for row in built["rows"]),
            "mask_contract": copy.deepcopy(MASK_CONTRACT),
            "six_model_readout_cells": "not constructed or executed; native runner responsibility",
        },
    }


def export_development(built):
    built = validate_panel(built)
    _require(built["manifest"]["split"] == "dev", "development export requires DEV")
    return {
        "schema": SCHEMA + "/development_export",
        "requests": [{"input_messages": copy.deepcopy(row["input_messages"])} for row in built["rows"]],
        "scoring_rows": built["rows"],
        "report": {
            "panel_manifest": built["manifest"],
            "row_ids_in_order": [row["row_id"] for row in built["rows"]],
            "scoring_rows_are_model_input": False,
            "training_allowed": False,
        },
    }


def score_response(row, raw_response):
    _validate_row(row)
    if row["panel"] == "application":
        syntax_valid = type(raw_response) is str and raw_response in ("A", "B")
        passed = syntax_valid and raw_response == row["response_target"]
        return {
            "score_kind": "strict_application_choice",
            "syntax_valid": syntax_valid,
            "passed": passed,
            "failure": None if passed else "wrong_choice" if syntax_valid else "invalid_choice_syntax",
            "raw_response": raw_response,
        }
    original = {"source": row["source"], "skill": "reflection"}
    result = corpus.score_response(original, raw_response)
    return {**result, "raw_response": raw_response, "semantic_prose_score": None}


def score_panel(built, responses):
    built = validate_panel(built)
    expected_ids = {row["row_id"] for row in built["rows"]}
    _require(isinstance(responses, dict) and set(responses) == expected_ids,
             "complete exact response inventory required; preserve partials outside reducer")
    results = [{"row_id": row["row_id"], **score_response(row, responses[row["row_id"]])}
               for row in built["rows"]]
    return {
        "schema": SCHEMA + "/scores",
        "panel": built["manifest"]["panel"],
        "parent_condition": built["manifest"]["parent_condition"],
        "passed_count": sum(result["passed"] for result in results),
        "total": len(results),
        "results": results,
        "scientific_claim": False,
        "auto_promotion": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("training", "development"))
    parser.add_argument("--panel", required=True, choices=("restatement", "application"))
    parser.add_argument("--parent", required=True, choices=PARENT_CONDITIONS)
    args = parser.parse_args(argv)
    try:
        built = build_panel(args.panel, split="train" if args.mode == "training" else "dev",
                            parent_condition=args.parent)
        exported = export_training(built) if args.mode == "training" else export_development(built)
    except ValueError as error:
        parser.error(str(error))
    print(_json(exported))


if __name__ == "__main__":
    main()
