"""Frozen CPU-only authored material; not child SLEEP or a native runner."""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import re
from types import ModuleType


SCHEMA = "astra_contrastive_perception_material_20260913_v1"
ROOT = Path("/data/home/rohing/dream-state")
PINS = {
    "organism_v6/birth_skill_corpus.py": "078ceba07141b5f6fb2159a12e21f1eccc0901ba9f51f52d1793d988927812f6",
    "organism_v6/rulegame_parenting_diagnostic.py": "e6055da48b2c6fa1bd294c9d991e07f32f05dc6630fe8973373977bdfe977526",
}
REUSE = {
    "research_notes/astra_memos/receipts_20260912/astra_perception_fit_run_20260913.py": "f62da57d1a66cd287b72ac8ad8b8724601062813653a63d3dcd6cd8a3b69cd51",
    "organism_v6/train_adapter_v3.py": "7bbf165fcb4b8ae3a1180328bcd19f57382c30516daddc95fd61e8a2c749fad7",
}
ORDER_SEED = 20260913
HELD_SEED = 2026091333
FIELDS = ("try", "observed", "predicted", "relation")
TEMPLATES = {
    "ledger": "Public ledger\n{events}",
    "cards": "Public case cards\n{events}",
    "boundary": "These are independent hypothetical boxes, not repeated trials of one world. Selected box is the response subject; companion box is practice context only.",
    "plain": "Enumerate each box independently. Read its action, observation, prior prediction, and relation as one record.",
    "contrastive": "Compare the boxes field by field. Notice the same action and prior prediction, the opposite observations, and how the relation follows from each observation versus prediction.",
    "D1": "Archive ledger: an earlier result is a distractor. Select only the last event.\n{events}",
    "D2": "Chronological case file: preserve the final TRY's own observation and preceding prediction, not the earlier event's outcome.\n{events}",
    "addition": "Compute {left} + {right}. Reply with only the base-10 integer, no explanation or surrounding whitespace.",
    "copy": "Copy exactly the text between <copy> and </copy>. Reply with that text only, no surrounding whitespace.\n<copy>{text}</copy>",
}


def encoded(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False,
                       separators=(",", ":")) + "\n").encode("utf-8")


def digest(value):
    return hashlib.sha256(value).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load_corpus(root=ROOT):
    root = Path(root).resolve()
    for relative, expected in PINS.items():
        require(digest((root / relative).read_bytes()) == expected, "source pin mismatch: " + relative)
    path = root / "organism_v6/birth_skill_corpus.py"
    module = ModuleType("frozen_material_corpus")
    module.__file__ = str(path)
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    return module


def hashed_number(domain, *coordinates):
    return int(digest(encoded([SCHEMA, HELD_SEED, domain, *coordinates])), 16)


def held_triples(corpus):
    excluded = {tuple(triple) for triples in corpus.SITUATIONS.values() for triple in triples}
    excluded.add((20, 21, 22))
    result = []
    for situation in range(2):
        for nonce in range(1000):
            triple = tuple(hashed_number("heldout", situation, coordinate, nonce) % 61 - 30
                           for coordinate in range(3))
            if triple not in excluded:
                result.append(triple)
                excluded.add(triple)
                break
        else:
            raise ValueError("heldout rejection budget exhausted")
    return result


def event_text(source):
    return "\n\n".join("Event {event_id}\n{raw_response}\n[OUTCOME] {raw_outcome}".format(**event)
                       for event in source["events"])


def facts(corpus, selected, companion):
    result = []
    for label, source in (("Selected", selected), ("Companion", companion)):
        assessment = corpus.assess_source(source)
        require(assessment["admissible"], "unsupported source")
        for field in FIELDS:
            result.append({"box": label, "field": field, "value": assessment["proof"][field]["value"]})
    return result


def note_lines(inventory, arm):
    cells = inventory if arm == "plain" else sorted(inventory, key=lambda cell: (FIELDS.index(cell["field"]), cell["box"] == "Companion"))
    return [cell["box"] + "." + cell["field"] + " = " + json.dumps(cell["value"], separators=(",", ":"))
            for cell in cells]


def set_prompt(corpus, row, prompt):
    row["input_messages"] = [{"role": "user", "content": prompt}]
    row["input_sha256"] = corpus._hash(row["input_messages"])


def costs(row):
    text = row["input_messages"][0]["content"]
    return {"context_utf8_bytes": len(text.encode()), "context_characters": len(text),
            "context_tokens": None, "assistant_tokens_including_eos": None}


def build_dataset(corpus):
    train = corpus.build_slice("perception", split="train", system_anchor=None, seed=ORDER_SEED)
    dev = corpus.build_slice("perception", split="dev", system_anchor=None, seed=ORDER_SEED)
    arms = {"plain": [], "contrastive": []}
    instruction = corpus._interface().record_instruction("interaction_v3")
    for order, original in enumerate(train["rows"]):
        selected = original["source"]
        selected_execution = corpus.assess_source(selected)["execution"]
        candidates = [row["source"] for row in train["rows"]
                      if row["source"]["situation_index"] == selected["situation_index"]
                      and row["source_proof"]["predicted"]["value"] is selected_execution["predicted"]
                      and row["source_proof"]["observed"]["value"] is not selected_execution["observed"]]
        require(len(candidates) == 1, "companion pairing must be unique")
        companion = candidates[0]
        inventory = facts(corpus, selected, companion)
        skin = ("ledger", "cards")[selected["situation_index"]]
        transcripts = "Selected box\n" + event_text(selected) + "\n\nCompanion box\n" + event_text(companion)
        for arm in arms:
            row = copy.deepcopy(original)
            lines = note_lines(inventory, arm)
            prompt = "\n\n".join([TEMPLATES["boundary"], TEMPLATES[skin].format(events=transcripts),
                                    TEMPLATES[arm] + "\n" + "\n".join(lines),
                                    "Respond only for the selected box.\n" + instruction])
            set_prompt(corpus, row, prompt)
            row["material"] = {"group": original["row_id"], "order": order, "skin": skin,
                               "companion_source": copy.deepcopy(companion),
                               "fact_inventory": copy.deepcopy(inventory), "note_lines": lines,
                               "source_transcripts_sha256": digest(transcripts.encode()),
                               "costs": costs(row)}
            arms[arm].append(row)
    panels = {"D1": [], "D2": [], "C-record": copy.deepcopy(dev["rows"]), "C-general": []}
    triples = held_triples(corpus)
    for original in dev["rows"]:
        source = copy.deepcopy(original["source"])
        values = ",".join(map(str, triples[source["situation_index"]]))
        predicted = original["source_proof"]["predicted"]["value"]
        observed = original["source_proof"]["observed"]["value"]
        source["events"][-1]["raw_response"] = (("PREDICT: " + ("T" if predicted else "F") + "\n") if predicted is not None else "") + "ACT: TRY " + values
        source["events"][-1]["raw_outcome"] = f"the box says: {observed} for ({values})"
        source["events"][0]["raw_outcome"] = f"the box says: {not observed} for (20,21,22)"
        source["derivation"] = {"parent_source_id": original["source"]["source_id"],
                                "operation": "fresh_triple_and_conflicting_earlier_observation",
                                "seed": HELD_SEED, "no_hidden_rule": True}
        corpus._identify(source)
        for panel in ("D1", "D2"):
            row = corpus._row("perception", copy.deepcopy(source), None)
            set_prompt(corpus, row, TEMPLATES[panel].format(events=event_text(source)) + "\n" + instruction)
            panels[panel].append(row)
    for panel in ("D1", "D2"):
        panels[panel].sort(key=lambda row: corpus._hash([ORDER_SEED, row["row_id"]]))
    for index in range(6):
        left = hashed_number("general-add", index, "left") % 900 + 100
        right = hashed_number("general-add", index, "right") % 900 + 100
        text = "".join("abcdefghjkmnpqrstuvwxyz23456789"[hashed_number("general-copy", index, position) % 29]
                       for position in range(10))
        for kind, prompt, target, evidence in (
            ("addition", TEMPLATES["addition"].format(left=left, right=right), str(left + right), {"left": left, "right": right}),
            ("copy", TEMPLATES["copy"].format(text=text), text, {"text": text}),
        ):
            row = {"row_id": f"general:{kind}:{index}", "skill": kind, "raw_target": target,
                   "target_sha256": digest(target.encode()), "evaluation_only": True, "evidence": evidence}
            set_prompt(corpus, row, prompt)
            panels["C-general"].append(row)
    for plain, contrast in zip(arms["plain"], arms["contrastive"]):
        require(plain["raw_target"] == contrast["raw_target"], "target mismatch")
        require(plain["source"] == contrast["source"], "selected source mismatch")
        require(plain["material"]["fact_inventory"] == contrast["material"]["fact_inventory"], "fact mismatch")
        require(Counter(plain["material"]["note_lines"]) == Counter(contrast["material"]["note_lines"]), "note multiplicity mismatch")
    require(all(len(rows) == 12 for rows in [*arms.values(), *panels.values()]), "panel size mismatch")
    return {
        "schema": SCHEMA, "qualification": "AUTHOR_SOURCED_LEVEL0_1_MATERIAL_HYPOTHESIS_NOT_CHILD_SLEEP_NOT_L2",
        "provenance": {"sources": copy.deepcopy(PINS), "native_reuse_not_executed": copy.deepcopy(REUSE),
                       "generator_sha256": digest(Path(__file__).read_bytes()),
                       "templates": copy.deepcopy(TEMPLATES), "templates_sha256": digest(encoded(TEMPLATES)),
                       "interface": copy.deepcopy(corpus._interface().source_manifest),
                       "order_seed": ORDER_SEED, "held_seed": HELD_SEED,
                       "original_train_rows_sha256": digest(encoded(train["rows"])),
                       "exposed_dev_rows_sha256": digest(encoded(dev["rows"])),
                       "held_triples": triples,
                       "filter": "literal six-case factorial; unique opposite-outcome same-prediction companion; held SHA256 mod61-30 rejection of train/dev/earlier/duplicate triples; no outcome selection"},
        "training": arms, "evaluation": panels,
        "recipe_only_not_executed": {"rank": 8, "alpha": 16, "dropout": 0.05, "learning_rate": 0.0001,
                                     "learner_seed": 0, "batch_size": 4, "epochs": 4, "max_length": 1024,
                                     "packing": False, "gradient_accumulation": 1, "fits": 2, "updates_per_fit": 12,
                                     "presentations_per_fit": 48, "generation_calls": 144,
                                     "supervision": "unchanged raw_target plus native EOS only; all context masked; no truncation",
                                     "ordering": "identical arm-neutral row_id groups and initial order; same seeded epoch shuffling",
                                     "inference": "reuse pinned perception PARAMS/ENGINE without alteration; temperature0/samplingseed0/max_tokens192"},
        "costs": {arm: {"context_utf8_bytes": sum(row["material"]["costs"]["context_utf8_bytes"] for row in rows),
                         "context_tokens": None} for arm, rows in arms.items()},
        "limitations": ["No tokenizer/model/native execution; equal output supervision is a byte/EOS contract pending native mask/ID verification.",
                        "Context costs differ; no compute-equivalence claim, renderer search, or exact input length gate.",
                        "D1/D2 are 24 renderings of 12 fresh cases, not 24 independent situations; only two fresh triples.",
                        "C-record is exact exposed DEV12, not a held-out semantic success panel.",
                        "TRAIN contains reciprocal pairing: every selected source also appears as a companion, equally in both arms.",
                        "One seed and authored material cannot establish a mechanism fix, child learning, G1/H1/H2, or original endpoint promotion."],
        "screen": {"held_min": 20, "each_skin_min": 9, "advantage_over_each_control": 4,
                   "off_ceiling": 21, "no_harm": "retain every OFF-correct item in both canaries"},
    }


def score_row(corpus, row, raw, finish_reason="stop"):
    result = {"raw": raw, "raw_sha256": digest(raw.encode()) if isinstance(raw, str) else None,
              "strict_pass": False, "syntax_errors": [], "schema_errors": [], "source_errors": [],
              "finish_reason": finish_reason, "completion_errors": [],
              "field_correct": {field: None for field in FIELDS} if row["skill"] == "perception" else {}}
    if finish_reason != "stop":
        result["completion_errors"] = ["nonterminal_or_truncated_or_failed_completion"]
        return result
    if not isinstance(raw, str):
        result["syntax_errors"] = ["missing_or_nontext_response"]
        return result
    if row["skill"] != "perception":
        target = (str(row["evidence"]["left"] + row["evidence"]["right"])
                  if row["skill"] == "addition" else row["evidence"]["text"])
        result["strict_pass"] = raw == target
        if raw != target:
            if raw.strip() == target:
                result["syntax_errors"] = ["surrounding_whitespace"]
            elif row["skill"] == "addition" and not re.fullmatch(r"-?(0|[1-9][0-9]*)", raw):
                result["syntax_errors"] = ["not_bare_integer"]
            else:
                result["source_errors"] = ["arithmetic_value" if row["skill"] == "addition" else "copy_bytes"]
        return result
    strict = corpus.score_response(row, raw)
    result["strict_pass"] = strict["passed"]
    result["strict_failures"] = strict.get("failures", [])
    try:
        record = corpus._interface().decode(raw)
    except (ValueError, TypeError) as error:
        result["syntax_errors"] = [str(error)]
        return result
    if type(record) is not dict or set(record) != set(FIELDS):
        result["schema_errors"] = ["exact_four_field_object_required"]
        return result
    checks = {"try": type(record["try"]) is list and len(record["try"]) == 3 and all(type(value) is int for value in record["try"]),
              "observed": type(record["observed"]) is bool,
              "predicted": record["predicted"] is None or type(record["predicted"]) is bool,
              "relation": type(record["relation"]) is str and record["relation"] in ("matched", "mismatched", "unavailable")}
    for field, valid in checks.items():
        if not valid:
            result["schema_errors"].append(field + ":invalid_type_or_domain")
    if result["schema_errors"]:
        return result
    assessment = corpus.assess_source(row["source"])
    for field in FIELDS:
        correct = record[field] == assessment["proof"][field]["value"]
        result["field_correct"][field] = correct
        if not correct:
            result["source_errors"].append(field)
    return result


def score_dataset(corpus, dataset, responses):
    require(encoded(dataset) == encoded(build_dataset(corpus)), "dataset differs from frozen generator")
    require(type(responses) is dict and set(responses) == {"OFF", "plain", "contrastive"}, "responses require OFF/plain/contrastive maps")
    cases = {panel + "/" + row["row_id"]: row for panel, rows in dataset["evaluation"].items() for row in rows}
    states = {}
    for state, outputs in responses.items():
        require(type(outputs) is dict and not (set(outputs) - set(cases)), "unknown response IDs or nonobject outputs")
        require(all(type(value) is dict and set(value) == {"raw", "finish_reason"}
                    and (value["raw"] is None or isinstance(value["raw"], str))
                    and value["finish_reason"] in ("stop", "length", "error")
                    for value in outputs.values()), "responses require raw/finish_reason envelopes")
        scores = {key: score_row(corpus, row, outputs.get(key, {}).get("raw"),
                                outputs.get(key, {}).get("finish_reason", "missing")) for key, row in cases.items()}
        totals = {panel: sum(score["strict_pass"] for key, score in scores.items() if key.startswith(panel + "/"))
                  for panel in dataset["evaluation"]}
        states[state] = {"items": scores, "totals": totals,
                         "complete": set(outputs) == set(cases) and all(isinstance(value["raw"], str)
                                                                      and value["finish_reason"] == "stop" for value in outputs.values())}
    held = {state: entry["totals"]["D1"] + entry["totals"]["D2"] for state, entry in states.items()}
    regression = [key for key in cases if key.startswith("C-") and states["OFF"]["items"][key]["strict_pass"]
                  and not states["contrastive"]["items"][key]["strict_pass"]]
    complete = all(entry["complete"] for entry in states.values())
    screen = dataset["screen"]
    passed = (complete and held["OFF"] < screen["off_ceiling"] and held["contrastive"] >= screen["held_min"]
              and all(states["contrastive"]["totals"][panel] >= screen["each_skin_min"] for panel in ("D1", "D2"))
              and all(held["contrastive"] - held[control] >= screen["advantage_over_each_control"] for control in ("OFF", "plain"))
              and not regression)
    paired = {}
    for control in ("OFF", "plain"):
        paired[control] = {"wins": [], "losses": []}
        for key in cases:
            if key.startswith(("D1/", "D2/")):
                treatment = states["contrastive"]["items"][key]["strict_pass"]
                baseline = states[control]["items"][key]["strict_pass"]
                if treatment != baseline:
                    paired[control]["wins" if treatment else "losses"].append(key)
    return {"dataset_sha256": digest(encoded(dataset)), "states": states, "held_totals": held,
            "complete": complete, "paired_held": paired, "canary_regressions": regression,
            "ceiling_limited": held["OFF"] >= screen["off_ceiling"], "exploratory_screen_pass": passed,
            "qualification": "authored material screen only; syntax versus field errors must be interpreted separately"}


def write_new(path, value, root=ROOT):
    path = Path(path).resolve()
    require(not path.is_relative_to(Path(root).resolve()), "no repository outputs")
    with path.open("xb") as stream:
        stream.write(encoded(value))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=ROOT)
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build")
    build.add_argument("--output", type=Path, required=True)
    score = commands.add_parser("score")
    score.add_argument("--dataset", type=Path, required=True)
    score.add_argument("--responses", type=Path, required=True)
    score.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    corpus = load_corpus(args.source_root)
    if args.command == "build":
        result = build_dataset(corpus)
    else:
        result = score_dataset(corpus, json.loads(args.dataset.read_text(), object_pairs_hook=corpus._interface().unique_object),
                               json.loads(args.responses.read_text(), object_pairs_hook=corpus._interface().unique_object))
    write_new(args.output, result, args.source_root)
    print(json.dumps({"output": str(args.output), "sha256": digest(encoded(result)), "native_executed": False}))


if __name__ == "__main__":
    main()
