"""Authored same-task DEV pairs; no fitting, model calls, or write export."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from types import ModuleType


SCHEMA = "astra_level1_prediction_transfer_v1"
ORIGINAL_MATERIAL_PATH = (
    Path(__file__).resolve().parents[1]
    / "research_notes/astra_memos/receipts_20260912/astra_level1_prediction_goal_material_20260913.py"
)
ORIGINAL_MATERIAL_SHA256 = "3da282322f65525271a48b628b30ecdc8a2fba6ba6ba84d8cf1f3e65ad6d6433"
MAX_NEW_TOKENS = 192
VIEWS = ("FULL", "MINIMAL")
CASE_TYPES = ("supported_true", "supported_false", "missing", "conflicting")
SITUATIONS = (
    "At a parcel depot, a console has queued a future routing command.",
    "At a water-testing bench, a console has queued a future sampling command.",
    "At a library return station, a console has queued a future sorting command.",
    "At a greenhouse panel, a console has queued a future ventilation command.",
    "At a museum entrance, a console has queued a future access command.",
    "At a print dispatch desk, a console has queued a future scheduling command.",
)
MINIMAL_SEMANTICS = (
    "A public card entry assigns a Boolean output to its exact action. "
    "Unlisted actions have unknown output; disagreeing entries remain unresolved. "
    "No relationship between different actions is specified."
)
MINIMAL_CONTRACT = (
    'Return one compact JSON object with keys in this order: "decision","prediction","reason".\n'
    'Allowed values: decision: "predict" or "abstain"; prediction: true, false or null; '
    'reason: "public_evidence" or "insufficient_evidence".\n'
    "Report what follows from the supplied facts alone"
)


class MaterialIntegrityError(ValueError):
    """The frozen dependency or evaluator row does not match its binding."""


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _sha(value):
    return hashlib.sha256(_json(value).encode("utf-8")).hexdigest()


def _load_frozen(original_material_path):
    path = Path(original_material_path)
    source_bytes = path.read_bytes()
    if hashlib.sha256(source_bytes).hexdigest() != ORIGINAL_MATERIAL_SHA256:
        raise MaterialIntegrityError("original material SHA256 mismatch")
    frozen_api = ModuleType("astra_pinned_prediction_goal_material")
    frozen_api.__file__ = str(path)
    exec(compile(source_bytes, str(path), "exec"), frozen_api.__dict__)
    return frozen_api


def _actions(case_index):
    return [
        [50001 + 137 * case_index + 11 * slot,
         (1 if (case_index + slot) % 2 else -1) * (70003 + 83 * case_index + 7 * slot),
         90001 - 61 * case_index - 13 * slot]
        for slot in range(6)
    ]


def _sources():
    for group_index, situation in enumerate(SITUATIONS):
        for position in range(4):
            case_index = 4 * group_index + position
            case = CASE_TYPES[(position + group_index) % 4]
            actions = _actions(case_index)
            selected, earlier = actions[:2]
            card = [
                {"action": actions[2], "outcome": bool((group_index + position) % 2)},
                {"action": actions[3], "outcome": bool((group_index + position + 1) % 2)},
            ]
            if group_index % 2:
                card.append({"action": actions[4], "outcome": bool(position % 2)})
            if case.startswith("supported_"):
                outcome = case == "supported_true"
                card.insert((group_index + position) % (len(card) + 1),
                            {"action": selected, "outcome": outcome})
                if group_index % 3 == 2:
                    card.append({"action": list(selected), "outcome": outcome})
            elif case == "conflicting":
                card.insert(0, {"action": selected, "outcome": False})
                card.append({"action": list(selected), "outcome": True})
            if (group_index + position) % 2:
                card.reverse()
            source_id = f"prediction_transfer:dev:case_{case_index:02d}"
            yield {
                "task": "prediction",
                "split": "dev",
                "situation_id": source_id,
                "source_id": source_id,
                "source_group_id": f"prediction_transfer:authored_group:{group_index:02d}",
                "parent_source_ids": [],
                "origin": "AUTHOR_SUPPLIED_PUBLIC_FACTS",
                "ancestry": "Fresh authored situation; shared construction group, not child experience.",
                "case": case,
                "situation": situation,
                "public_facts": {
                    "belief_card": card,
                    "selected_action": selected,
                    "earlier_action": earlier,
                    "earlier_prediction": bool(group_index % 2),
                    "earlier_outcome": bool((group_index // 2 + position) % 2),
                },
            }


def _prompts(frozen_api, source):
    evidence, instruction = frozen_api._render(source)
    full = source["situation"] + "\nPublic task record:\n" + evidence + "\n" + instruction
    facts = source["public_facts"]
    minimal_lines = [
        source["situation"],
        MINIMAL_SEMANTICS,
        "The selected action is a future request; no execution result for it has been observed.",
        "Earlier, different action: " + frozen_api._try(facts["earlier_action"]),
        "Earlier explicit prediction: " + str(facts["earlier_prediction"]),
        "Earlier public outcome: " + str(facts["earlier_outcome"]),
        "Public belief card:",
    ]
    minimal_lines.extend(frozen_api._try(entry["action"]) + " -> " + str(entry["outcome"])
                         for entry in facts["belief_card"])
    minimal_lines.extend(("Selected next action: " + frozen_api._try(facts["selected_action"]),
                          MINIMAL_CONTRACT))
    return {"FULL": full, "MINIMAL": "\n".join(minimal_lines)}


def _rows(frozen_api):
    rows = []
    for source in _sources():
        expected = frozen_api._expected(source)
        prompts = _prompts(frozen_api, source)
        for view in VIEWS:
            rows.append({
                "row_id": source["source_id"] + ":" + view,
                "case_id": source["source_id"],
                "case": source["case"],
                "view": view,
                "source": copy.deepcopy(source),
                "expected": copy.deepcopy(expected),
                "raw_target": _json(expected),
                "prompt": prompts[view],
                "input_messages": [{"role": "user", "content": prompts[view]}],
                "max_new_tokens": MAX_NEW_TOKENS,
                "source_sha256": _sha(source),
                "original_material_sha256": ORIGINAL_MATERIAL_SHA256,
            })
    return rows


def _triples(source):
    facts = source["public_facts"]
    return {tuple(facts["selected_action"]), tuple(facts["earlier_action"])} | {
        tuple(entry["action"]) for entry in facts["belief_card"]
    }


def _disjointness(frozen_api, sources):
    old_data = frozen_api.build_dataset("prediction", seed=0)
    previous = {"train": old_data["training"], "held": old_data["evaluation"]["held"]}
    if {split: len(rows) for split, rows in previous.items()} != {"train": 96, "held": 48}:
        raise MaterialIntegrityError("unexpected original prediction denominators")
    new_triples = set().union(*(_triples(source) for source in sources))
    prior = {}
    for split, rows in previous.items():
        triples = set().union(*(_triples(row["source"]) for row in rows))
        overlap = sorted(triples & new_triples)
        if overlap:
            raise MaterialIntegrityError("new action triples overlap original " + split)
        prior[split] = {
            "source_count": len(rows),
            "source_ids": [row["source"]["situation_id"] for row in rows],
            "action_triples": [list(triple) for triple in sorted(triples)],
            "action_triples_sha256": _sha(sorted(triples)),
            "overlap": overlap,
        }
    cases = [{"source_id": source["source_id"],
              "source_group_id": source["source_group_id"],
              "action_triples": [list(triple) for triple in sorted(_triples(source))]}
             for source in sources]
    if sum(len(case["action_triples"]) for case in cases) != len(new_triples):
        raise MaterialIntegrityError("action triple shared between new cases")
    return {
        "scope": "Every selected, earlier and card action in prediction seed0 train96/held48.",
        "original_rowset_sha256": old_data["provenance"]["rowset_sha256"],
        "original": prior,
        "new_cases": cases,
        "new_unique_action_triples": len(new_triples),
        "new_action_triples_sha256": _sha(sorted(new_triples)),
        "cross_case_overlap": [],
        "passed": True,
    }


def build_material(*, original_material_path=ORIGINAL_MATERIAL_PATH):
    """Return JSON-compatible evaluator material, never a training/write export."""
    frozen_api = _load_frozen(original_material_path)
    sources = list(_sources())
    material = {
        "schema": SCHEMA,
        "qualification": "AUTHORED_SAME_TASK_DEV_SCAFFOLD_WITHDRAWAL_ONLY",
        "max_new_tokens": MAX_NEW_TOKENS,
        "case_count": 24,
        "row_count": 48,
        "case_counts": {case: 6 for case in CASE_TYPES},
        "views": list(VIEWS),
        "original_material": {
            "path": str(original_material_path),
            "sha256": ORIGINAL_MATERIAL_SHA256,
            "schema": frozen_api.SCHEMA,
            "scoring_version": frozen_api.SCORING_VERSION,
            "skill": "prediction",
            "seed": 0,
        },
        "provenance": {
            "origin": "AUTHOR_SUPPLIED_PUBLIC_FACTS",
            "selection": "Fixed 24-case enumeration; no model outputs, sampling or outcome selection.",
            "authored_groups": 6,
            "model_outputs_used": False,
            "training_or_write_export": False,
            "paired_views_are_independent": False,
            "limits": [
                "Same-task DEV distribution and scaffold withdrawal, not a new task family.",
                "Authored sibling groups are disclosed, not independent world laws or learner lives.",
                "No fits, native calls, parented experience, H1/P1 or parenting qualification.",
                "Public card semantics are unchanged; MINIMAL omits the decision-to-label algorithm.",
                "Expected values and raw targets are evaluator-only, never part of input_messages.",
                "The runner enforces the fixed 192-token generation cap; no tokenizer is executed here.",
            ],
        },
        "scoring": {
            "function": "original.score_row",
            "primary_pass": "content_correct",
            "strict": "content_correct and exact canonical bytes",
            "bridge": "Validate the authored paired row first; build an evaluator-only original-skin0 "
                      "integrity carrier from the identical source; pass raw/finish unchanged to score_row. "
                      "The carrier is not the model prompt and is never exported in input_messages.",
        },
        "disjointness_audit": _disjointness(frozen_api, sources),
        "rows": _rows(frozen_api),
    }
    material["material_sha256"] = _sha(material)
    return material


def score_response(row, raw, finish_reason, *, original_material_path=ORIGINAL_MATERIAL_PATH):
    """Use frozen content/format scoring; malformed evaluator rows raise, not score zero."""
    frozen_api = _load_frozen(original_material_path)
    if type(row) is not dict:
        raise MaterialIntegrityError("row must be an authored transfer row")
    candidates = {candidate["row_id"]: candidate for candidate in _rows(frozen_api)}
    try:
        canonical_row = candidates[row["row_id"]]
        matches = _json(row) == _json(canonical_row)
    except (KeyError, TypeError, ValueError, RecursionError):
        matches = False
    if not matches:
        raise MaterialIntegrityError("authored transfer row integrity mismatch")
    scoring_row = frozen_api._row(copy.deepcopy(canonical_row["source"]), 0)
    return frozen_api.score_row(scoring_row, raw, finish_reason)
