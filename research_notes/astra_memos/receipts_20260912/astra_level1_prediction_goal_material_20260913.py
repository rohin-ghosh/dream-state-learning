"""Bounded authored Level1 fixtures. No repo imports, model calls, or execution.

Prediction means a prospective consequence under a supplied public belief card;
goal completion means all stated conditions have publicly verified evidence.
These are development screens, not child SLEEP, native protocol, or H1/P1 tests.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import re


SKILLS = ("prediction", "goal_completion")
SCHEMA = "astra_authored_level1_prediction_goal_v1"
SCORING_VERSION = "typed_content_and_format_v2_raw35"
QUALIFICATION = "AUTHOR_LEVEL1_SCREEN_ONLY_NOT_CHILD_SLEEP_NOT_H1_NOT_P1"
SKINS = (
    "Classroom exercise. Read the public task evidence below.\n{evidence}\n{instruction}",
    "Work from this supplied classroom record only.\n{evidence}\nYour response contract: {instruction}",
    "Public situation for your next decision:\n{evidence}\nDecide from those facts. {instruction}",
    "Review the stated task and permitted evidence.\n{evidence}\nReturn your decision now. {instruction}",
)
REFERENCES = (
    "research_notes/THESIS_RAW_ROHIN_2026-09-11.md:337 (raw message 34)",
    "research_notes/THESIS_RAW_ROHIN_2026-09-11.md:343 (raw message 35; future Level1 scoring only)",
    "research_loop/COORDINATION.md:9948 (2026-09-13T07:16Z steer)",
    "organism_v6/birth_skill_corpus.py (public event fidelity and source proofs)",
    "research_notes/00_THESIS.md (state + goal, evidence and claim boundaries)",
    "research_notes/analysis/2026-09-12_behavior_memory_bridge_and_level1_intertwining_protocol.md:77 (public belief-card PROSPECT)",
    "organism_v6/curriculum/01_you_learn_from_surprises.md (predict before acting)",
    "organism_v6/curriculum/11_mind_the_clock_judge_yourself.md (evidence, not mood)",
)
LIMITATIONS = (
    "Authored facts, not learner experience or engine-verified scientific outcomes.",
    "One skin per distinct fact situation; authored sibling groups are disclosed, not statistically independent world laws.",
    "Shared task grammar and four fixed skins across splits; held situations are disjoint, not unseen task families.",
    "Prediction is consequence lookup under explicit local facts, not induction of a hidden rule or calibrated probabilities.",
    "Abstention is this screen's JSON contract only; it does not change native play or record grammar.",
    "Goal completion is verification/continue discrimination, not goal invention, planning, action execution, or successful recovery.",
    "Typed fixture-content agreement and canonical format are scored separately, not semantic reasoning; reason is a declared fixture label. Canaries are narrow arithmetic/copy checks.",
    "No evidence yet of learning gain, withdrawal persistence, transfer, H1/P1 qualification, or Level2 competence.",
)


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _triple(base, offset):
    return [base + offset, -base - offset - 1, base + offset + 3]


def _try(action):
    return "TRY " + ",".join(map(str, action))


def _expected(source):
    facts = source["public_facts"]
    if source["task"] == "prediction":
        matches = [entry["outcome"] for entry in facts["belief_card"]
                   if entry["action"] == facts["selected_action"]]
        if not matches or len(set(matches)) != 1:
            return {"decision": "abstain", "prediction": None, "reason": "insufficient_evidence"}
        return {"decision": "predict", "prediction": matches[0], "reason": "public_evidence"}
    if source["task"] == "goal_completion":
        for requirement in facts["goal"]:
            observed = [entry["outcome"] for entry in facts["verified_state"]
                        if entry["action"] == requirement["action"]]
            if not observed or any(value != requirement["outcome"] for value in observed):
                return {"decision": "continue", "goal_complete": False}
        return {"decision": "complete", "goal_complete": True}
    if source["task"] == "arithmetic":
        return {"answer": facts["left"] + facts["right"]}
    if source["task"] == "copy":
        return {"answer": facts["text"]}
    raise ValueError("unknown source task")


def _render(source):
    facts = source["public_facts"]
    task = source["task"]
    if task == "prediction":
        lines = [
            "Predict BEFORE the selected action is executed; its outcome has not been returned.",
            "This public belief card applies to this exercise: a listed action returns its listed Boolean value.",
            "An unlisted action has unknown output. Conflicting entries are unresolved: abstain.",
            "No rule connecting different actions is supplied; historical outcomes and predictions cannot fill gaps.",
            "Earlier, different action: " + _try(facts["earlier_action"]),
            "Earlier explicit prediction: " + str(facts["earlier_prediction"]),
            "Earlier public outcome: " + str(facts["earlier_outcome"]),
            "Public belief card:",
        ]
        lines += [_try(entry["action"]) + " -> " + str(entry["outcome"]) for entry in facts["belief_card"]]
        lines.append("Selected next action: " + _try(facts["selected_action"]))
        instruction = ('Use exactly one compact JSON object, keys in this order: '
                       '"decision","prediction","reason". For uniquely supported output use decision '
                       '"predict", prediction true or false, reason "public_evidence". Otherwise use '
                       'decision "abstain", prediction null, reason "insufficient_evidence". No other text.')
        return "\n".join(lines), instruction
    if task == "goal_completion":
        lines = [
            "The stated goal requires ALL the following action outcomes in the CURRENT verified state:",
        ]
        lines += [_try(entry["action"]) + " must return " + str(entry["outcome"]) for entry in facts["goal"]]
        lines += [
            "Complete only when every required outcome is publicly verified for that exact action.",
            "Missing, conflicting, or contrary evidence means continue, not complete. A claim is not verification.",
            "Earlier different-action public outcome: " + _try(facts["earlier_action"]) + " -> " + str(facts["earlier_outcome"]),
            "Unverified learner claim: " + facts["learner_claim"],
            "CURRENT verified state (all available observations):",
        ]
        lines += [_try(entry["action"]) + " -> " + str(entry["outcome"]) for entry in facts["verified_state"]]
        instruction = ('Use exactly one compact JSON object, keys in this order: "decision","goal_complete". '
                       'Use decision "complete" and goal_complete true only if the goal is verified; '
                       'otherwise decision "continue" and goal_complete false. No other text.')
        return "\n".join(lines), instruction
    if task == "arithmetic":
        return f'Calculate {facts["left"]} + ({facts["right"]}).', 'Return compact JSON {"answer":INTEGER}, no other text.'
    return "Copy this exact text: " + facts["text"], 'Return compact JSON {"answer":"EXACT TEXT"}, no other text.'


def _source(task, split, situation, facts, case, group=None):
    return {"task": task, "split": split, "situation_id": f"{task}:{split}:{situation}",
            "source_group_id": f"{task}:{split}:group:{situation if group is None else group}",
            "parent_source_ids": [], "ancestry": "authored_sibling_group; no reused source or model generation",
            "origin": "AUTHOR_SUPPLIED_PUBLIC_FACTS", "case": case, "public_facts": facts}


def _prediction_sources(split):
    family_count = 32 if split == "train" else 16
    for family in range(family_count):
        earlier_outcome = bool(family % 2)
        earlier_prediction = bool((family // 2) % 2)
        variant = (family // 4) % 2 if split == "train" else (family % 2)
        for outcome_index, outcome in enumerate((False, True, None)):
            base = (100 if split == "train" else 10000) + 60 * family + 20 * outcome_index
            selected = _triple(base, 0)
            other = _triple(base, 5)
            if outcome is None:
                card = ([{"action": other, "outcome": False}, {"action": _triple(base, 7), "outcome": True}]
                        if variant == 0 else [{"action": selected, "outcome": False}, {"action": selected, "outcome": True}])
                case = "missing_evidence" if variant == 0 else "conflicting_evidence"
            else:
                card = [{"action": selected, "outcome": outcome}, {"action": other, "outcome": not outcome}]
                case = "uniquely_supported_card"
            if variant:
                card.reverse()
            facts = {"selected_action": selected, "belief_card": card,
                     "earlier_action": _triple(base, 9), "earlier_outcome": earlier_outcome,
                     "earlier_prediction": earlier_prediction}
            source = _source("prediction", split, f"{family}:{outcome}", facts, case, group=family)
            source["skin_id"] = family // (8 if split == "train" else 4)
            yield source


def _goal_sources(split):
    earlier_values = (False, True) if split == "train" else (None,)
    for family, (complete, desired, earlier, variant, profile) in enumerate(itertools.product(
            (False, True), (False, True), earlier_values, range(3), range(4))):
        base = (20000 if split == "train" else 40000) + 20 * family
        earlier = bool(variant % 2) if earlier is None else earlier
        if split == "held" and variant == 2:
            earlier = desired
        selected, second, distractor = (_triple(base, offset) for offset in (0, 5, 9))
        goal = [{"action": selected, "outcome": desired}]
        state = [{"action": selected, "outcome": desired if complete else not desired}]
        if variant == 1:
            goal.append({"action": second, "outcome": not desired})
            state = [{"action": selected, "outcome": desired},
                     {"action": second, "outcome": not desired if complete else desired}]
            if profile >= 2:
                goal.append({"action": _triple(base, 12), "outcome": bool(profile % 2)})
                state.insert(0, {"action": _triple(base, 12), "outcome": bool(profile % 2)})
        if variant == 0 and profile >= 2:
            state.append({"action": selected, "outcome": desired})
        if variant == 2:
            state = [{"action": selected, "outcome": desired}] if complete else []
        state.append({"action": distractor, "outcome": earlier})
        if profile % 2:
            state.append({"action": _triple(base, 15), "outcome": not earlier})
        if profile >= 2:
            state.reverse()
        claim_finished = earlier if profile % 2 == 0 else not earlier
        facts = {"goal": goal, "verified_state": state, "earlier_action": distractor,
                 "earlier_outcome": earlier, "learner_claim": "I have finished." if claim_finished else "I am not finished."}
        case = ("single_requirement", "all_requirements", "claim_requires_verification")[variant]
        source = _source("goal_completion", split, str(family), facts, case, group=family // 4)
        source["skin_id"] = profile
        yield source


def _proof(source):
    facts = source["public_facts"]
    proof = {"public_facts_sha256": _sha(_json(facts)), "source_sha256": _sha(_json(source)),
             "author_rule": "Apply only the public response contract to supplied facts.",
             "expected": _expected(source), "visibility": "Metadata/proof excluded from input_messages."}
    if source["task"] == "prediction":
        proof["support_paths"] = [f"public_facts.belief_card[{index}]" for index, entry in enumerate(facts["belief_card"])
                                  if entry["action"] == facts["selected_action"]]
        proof["query_path"] = "public_facts.selected_action"
    elif source["task"] == "goal_completion":
        proof["requirements"] = [{"goal_path": f"public_facts.goal[{index}]",
                                  "observation_paths": [f"public_facts.verified_state[{position}]"
                                                        for position, entry in enumerate(facts["verified_state"])
                                                        if entry["action"] == requirement["action"]]}
                                 for index, requirement in enumerate(facts["goal"])]
    else:
        proof["support_paths"] = ["public_facts"]
    return proof


def _row(source, skin):
    evidence, instruction = _render(source)
    raw_target = _json(_expected(source))
    return {"row_id": f'{source["situation_id"]}:skin{skin}',
            "input_messages": [{"role": "user", "content": SKINS[skin].format(evidence=evidence, instruction=instruction)}],
            "raw_target": raw_target, "target_sha256": _sha(raw_target),
            "source": dict(source, skin_id=skin), "source_proof": _proof(dict(source, skin_id=skin))}


def _canaries():
    pairs = ((17, 26), (-12, 7), (48, -19), (0, -31), (-14, -23), (105, 16))
    strings = ("maple-07", "TRUE is text", "qR_92-z", "0051", "continue? no", "goal=blue;state=amber")
    rows = []
    for index, (left, right) in enumerate(pairs):
        rows.append(_row(_source("arithmetic", "canary", str(index), {"left": left, "right": right}, "preservation"), index % 4))
    for index, text in enumerate(strings):
        rows.append(_row(_source("copy", "canary", str(index), {"text": text}, "preservation"), index % 4))
    return rows


def build_dataset(skill, seed=0):
    """Return independent mutable data. Seed changes ordering only, never labels."""
    if skill not in SKILLS:
        raise ValueError(f"skill must be one of {SKILLS}")
    if type(seed) is not int:
        raise ValueError("seed must be an integer, not bool")
    factory = _prediction_sources if skill == "prediction" else _goal_sources
    training = [_row(source, source["skin_id"]) for source in factory("train")]
    held = [_row(source, source["skin_id"]) for source in factory("held")]
    canary = _canaries()
    for rows in (training, held, canary):
        rows.sort(key=lambda row: _sha(_json([seed, row["row_id"]])))
    return {"schema": SCHEMA, "qualification": QUALIFICATION,
            "provenance": {"skill": skill, "seed": seed, "seed_effect": "ordering_only",
                           "scoring_version": SCORING_VERSION, "primary_pass": "content_correct",
                           "origin": "PURE_AUTHORED_LEVEL1", "date": "2026-09-13",
                           "references": list(REFERENCES), "skins": list(SKINS),
                           "selection": "Fixed factorial enumeration; no model outputs, tuning, sampling or remote data.",
                           "source_situations": {"train": 96, "held": 48},
                           "skin_counts": {"train": [24, 24, 24, 24], "held": [12, 12, 12, 12]},
                           "ancestry": "Each situation rendered once; shared construction groups are in source_group_id; no parent source reused.",
                           "recipe_boundary": "No recipe implemented. Fresh 320-skill fit is recipe-inspired, not faithful SEQ113 warm80+320parents/mixed2memory+2arithmetic replication.",
                           "limitations": list(LIMITATIONS),
                           "rowset_sha256": _sha(_json([training, held, canary]))},
            "training": training, "evaluation": {"held": held, "canary": canary}}


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError("nonfinite JSON constant: " + value)


def score_row(row, raw, finish_reason):
    """Primary passed == content_correct; strict additionally requires exact bytes.

    Content accepts JSON whitespace/key order and one enclosing json/plain fence.
    Both passes require stop termination and row integrity. No key/type/value
    repair occurs. Reason is a declared fixture label, not evaluated reasoning.
    Format classifies parsed serialization independently of content correctness.
    errors are content failures; strict_errors additionally records format failure.
    raw is returned untouched. This scorer is for future Level1 runs only.
    """
    errors = []
    parsed = None
    typed_match = False
    format_kind = "unparseable"
    try:
        expected = _expected(row["source"])
        target = _json(expected)
        evidence, instruction = _render(row["source"])
        messages = [{"role": "user", "content": SKINS[row["source"]["skin_id"]].format(evidence=evidence, instruction=instruction)}]
        if (row["raw_target"] != target or row["target_sha256"] != _sha(target)
                or row["source_proof"] != _proof(row["source"]) or row["input_messages"] != messages):
            errors.append("row_integrity_error")
    except (KeyError, TypeError, ValueError, IndexError):
        errors.append("row_integrity_error")
        expected, target = None, None
    if finish_reason != "stop":
        errors.append("finish_reason_not_stop")
    if not isinstance(raw, str):
        errors.append("response_not_text")
    else:
        candidate = raw.strip(" \t\r\n")
        fence = re.fullmatch(r"```(?:json)?[ \t]*\r?\n([\s\S]*?)\r?\n```", candidate)
        if fence is not None:
            candidate = fence.group(1)
        try:
            parsed = json.loads(candidate, object_pairs_hook=_unique_object, parse_constant=_reject_constant)
            canonical = _json(parsed)
        except (ValueError, RecursionError):
            errors.append("invalid_json")
        else:
            format_kind = "fenced" if fence is not None else "exact" if raw == canonical else "json_noncanonical"
            if not isinstance(parsed, dict):
                errors.append("response_not_object")
            elif expected is not None:
                if set(parsed) != set(expected):
                    errors.append("wrong_fields")
                elif any(type(parsed[key]) is not type(value) for key, value in expected.items()):
                    errors.append("wrong_types")
                elif parsed != expected:
                    errors.append("wrong_values")
                else:
                    typed_match = True
    content_correct = typed_match and not errors
    strict = content_correct and raw == target
    strict_errors = list(errors)
    if format_kind != "exact":
        strict_errors.append("not_exact_canonical_format")
    return {"passed": content_correct, "strict": strict, "content_correct": content_correct,
            "format": format_kind, "errors": errors, "strict_errors": strict_errors,
            "raw": raw, "parsed": parsed, "finish_reason": finish_reason,
            "score_kind": "typed_authored_fixture_content_not_reasoning",
            "scoring_version": SCORING_VERSION}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill", choices=SKILLS)
    parser.add_argument("--seed", type=int, default=0)
    arguments = parser.parse_args()
    print(_json(build_dataset(arguments.skill, arguments.seed)))
