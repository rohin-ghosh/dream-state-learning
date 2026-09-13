"""Authored public repetition/meta-reflection decisions, not actual learning.

The exact local classroom contract was recorded in the matching handoff before
implementation. Infrastructure is copied from the frozen prediction/goal module;
there is no runtime dependency on that module and no model/native/GPU access.
"""
from __future__ import annotations

import hashlib
import json
import re

SKILLS = ("repetition", "meta_reflection")
SCHEMA = "astra_authored_level1_repetition_meta_v1"
SCORING_VERSION = "typed_content_and_format_v2_raw35"
QUALIFICATION = "AUTHOR_VISIBLE_DECISION_SCREEN_NOT_ADULT_LEARNING_NOT_INTERNALIZATION_NOT_H1_NOT_P1"
INFRASTRUCTURE_SHA256 = "3da282322f65525271a48b628b30ecdc8a2fba6ba6ba84d8cf1f3e65ad6d6433"
REFERENCES = (
    "research_notes/THESIS_RAW_ROHIN_2026-09-11.md:337 (raw34 granular skills)",
    "research_notes/THESIS_RAW_ROHIN_2026-09-11.md:343 (raw35 separate content/format)",
    "organism_v6/curriculum/05_replay_what_matters.md",
    "organism_v6/curriculum/07_scope_your_memories.md",
    "organism_v6/curriculum/11_mind_the_clock_judge_yourself.md",
    "organism_v6/PARENTING_MENU.md",
    "research_notes/00_THESIS.md",
)
REPETITION_POLICY = (
    "Judge only the nominated prior record under this local review policy. "
    "Skip as irrelevant if its task is outside current_goal_tasks. Otherwise skip as "
    "budget_exhausted if review_cost exceeds remaining_budget. Otherwise rehearse as "
    "important if its task is in important_tasks. Otherwise rehearse as unresolved "
    "if prediction differs from verified_outcome and resolution_verified is false. "
    "Otherwise skip as settled. Apply this order, including importance before unresolved. "
    "Repetition count alone is not new evidence and does not decide relevance. Rehearsal "
    "does not change independent_support: report that supplied count unchanged."
)
META_POLICY = (
    "Classify only the public trace pattern, not an internal mental state or causal mechanism. "
    "Use this local priority table: (1) no verified_after: insufficient_evidence / "
    "collect_verified_after_trace. (2) Before/after assessment_id or total differs: "
    "incomparable_checks / rerun_matched_check. (3) practiced_target differs from "
    "verified_correct_target: incorrect_practice_targets / correct_targets_then_retest. "
    "(4) Practiced-example correct count improves but new-example correct count does not: "
    "practice_only_gain / vary_examples_and_test_new. (5) A same-ID, same-total delayed "
    "check has fewer correct answers than its immediate check: retention_loss / "
    "spaced_rehearsal_and_delayed_check. (6) Otherwise no new-example improvement after "
    "at least one strategy repetition: no_progress / switch_to_contrastive_practice. "
    "(7) Otherwise insufficient_evidence / collect_verified_after_trace. "
    "The counts are verified public checks within this authored scenario; a learner's "
    "self-report or unrelated earlier result cannot override them. Choose the next "
    "action only; do not claim it has been run or proved effective."
)
DIAGNOSES = (
    ("practice_only_gain", "vary_examples_and_test_new"),
    ("retention_loss", "spaced_rehearsal_and_delayed_check"),
    ("no_progress", "switch_to_contrastive_practice"),
    ("incorrect_practice_targets", "correct_targets_then_retest"),
    ("incomparable_checks", "rerun_matched_check"),
    ("insufficient_evidence", "collect_verified_after_trace"),
)
LIMITATIONS = (
    "Local visible policy compliance, not actual rehearsal, adult learning, internalization, child SLEEP or H1/P1 qualification.",
    "Authored verified facts are vignette facts, not engine executions or real measured learning gains.",
    "Meta diagnoses are public trace-pattern labels, not causal diagnoses or truth about hidden thoughts or emotions.",
    "Prescribed next actions are warranted by the declared policy, not experimentally proved effective.",
    "Repetition nominates one record; it does not solve global multi-record allocation or actually update support or memory.",
    "Source facts/IDs are disjoint across splits; policies, skins and authored case families are shared.",
    "Sibling groups expose construction ancestry; 96 source situations are not 96 independent learning mechanisms.",
    "passed is typed fixture-content agreement with stop termination; reason/diagnosis are declared labels, not semantic reasoning correctness.",
    "Canaries are narrow arithmetic/copy checks; no learned gain, general preservation, transfer or persistence is claimed.",
)

SKINS = (
    "Classroom exercise. Read the public task evidence below.\n{evidence}\n{instruction}",
    "Work from this supplied classroom record only.\n{evidence}\nYour response contract: {instruction}",
    "Public situation for your next decision:\n{evidence}\nDecide from those facts. {instruction}",
    "Review the stated task and permitted evidence.\n{evidence}\nReturn your decision now. {instruction}",
)

def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)

def _sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def _source(task, split, situation, facts, case, group=None):
    return {"task": task, "split": split, "situation_id": f"{task}:{split}:{situation}",
            "source_group_id": f"{task}:{split}:group:{situation if group is None else group}",
            "parent_source_ids": [], "ancestry": "authored_sibling_group; no reused source or model generation",
            "origin": "AUTHOR_SUPPLIED_PUBLIC_FACTS", "case": case, "public_facts": facts}

def _row(source, skin):
    evidence, instruction = _render(source)
    raw_target = _json(_expected(source))
    return {"row_id": f'{source["situation_id"]}:skin{skin}',
            "input_messages": [{"role": "user", "content": SKINS[skin].format(evidence=evidence, instruction=instruction)}],
            "raw_target": raw_target, "target_sha256": _sha(raw_target),
            "source": dict(source, skin_id=skin), "source_proof": _proof(dict(source, skin_id=skin))}

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


def _expected(source):
    facts = source["public_facts"]
    task = source["task"]
    if task == "repetition":
        record = facts["nominated_record"]
        decision = "skip"
        if record["task"] not in facts["current_goal_tasks"]:
            reason = "irrelevant"
        elif record["review_cost"] > facts["remaining_budget"]:
            reason = "budget_exhausted"
        elif record["task"] in facts["important_tasks"]:
            decision, reason = "rehearse", "important"
        elif record["prediction"] != record["verified_outcome"] and not record["resolution_verified"]:
            decision, reason = "rehearse", "unresolved"
        else:
            reason = "settled"
        return {"decision": decision, "independent_support_after": record["independent_support"], "reason": reason}
    if task == "meta_reflection":
        before, after = facts["verified_before"], facts["verified_after"]
        immediate, delayed = facts["immediate_check"], facts["delayed_check"]
        label = 5
        if after is None:
            label = 5
        elif before["assessment_id"] != after["assessment_id"] or before["total"] != after["total"]:
            label = 4
        elif facts["practiced_target"] != facts["verified_correct_target"]:
            label = 3
        elif after["practiced_correct"] > before["practiced_correct"] and after["new_correct"] <= before["new_correct"]:
            label = 0
        elif (immediate["assessment_id"] == delayed["assessment_id"] and immediate["total"] == delayed["total"]
              and delayed["correct"] < immediate["correct"]):
            label = 1
        elif after["new_correct"] <= before["new_correct"] and facts["strategy_repetitions"] > 0:
            label = 2
        return dict(zip(("diagnosis", "next_action"), DIAGNOSES[label]))
    if task == "arithmetic":
        return {"answer": facts["left"] + facts["right"]}
    if task == "copy":
        return {"answer": facts["text"]}
    raise ValueError("unknown task")


def _render(source):
    facts = source["public_facts"]
    task = source["task"]
    if task == "repetition":
        return (REPETITION_POLICY + "\nSupplied public record and budget:\n" + _json(facts),
                'Return compact JSON with keys in this order: "decision","independent_support_after","reason". '
                'Use a string decision, integer support count, and string policy reason. No other text.')
    if task == "meta_reflection":
        return (META_POLICY + "\nSupplied public learning-strategy trace:\n" + _json(facts),
                'Return compact JSON with keys in this order: "diagnosis","next_action", both strings from the policy. No other text.')
    if task == "arithmetic":
        return f'Calculate {facts["left"]} + ({facts["right"]}).', 'Return compact JSON {"answer":INTEGER}, no other text.'
    return "Copy this exact text: " + facts["text"], 'Return compact JSON {"answer":"EXACT TEXT"}, no other text.'


def _proof(source):
    facts = source["public_facts"]
    task = source["task"]
    paths = (["current_goal_tasks", "important_tasks", "remaining_budget", "nominated_record"] if task == "repetition" else
             ["verified_before", "verified_after", "practiced_target", "verified_correct_target", "strategy_repetitions", "immediate_check", "delayed_check"] if task == "meta_reflection" else list(facts))
    return {"public_facts_sha256": _sha(_json(facts)), "source_sha256": _sha(_json(source)),
            "expected": _expected(source), "support_paths": ["public_facts." + key for key in paths],
            "author_rule": "Apply the supplied local decision policy; no hidden-state truth or claimed learning effect.",
            "visibility": "Source IDs, case metadata and proof excluded from input_messages."}


def _repetition_sources(split):
    count = 16 if split == "train" else 8
    for profile in range(count):
        for case in range(6):
            identifier = "record-" + _sha(_json(["repetition", split, profile, case]))[:16]
            task_name = identifier + "-task"
            outcome = bool((profile // 2) % 2)
            mismatch = case in (1, 2) or (case in (3, 5) and profile % 2 == 0) or (case == 4 and profile % 2 == 1)
            cost = 1 + profile % 3
            facts = {
                "current_goal_tasks": [task_name if case != 3 else identifier + "-other-task"],
                "important_tasks": [task_name] if case in (0, 2, 5) else [],
                "remaining_budget": cost - 1 if case == 5 else cost + profile % 2,
                "earlier_unrelated_public_outcome": bool(profile % 2),
                "nominated_record": {"record_id": identifier, "task": task_name,
                    "action": [70000 + profile * 60 + case * 5 + (0 if split == "train" else 10000), -9, 13],
                    "prediction": not outcome if mismatch else outcome, "verified_outcome": outcome,
                    "resolution_verified": True if case == 4 else False if mismatch else bool(profile % 2),
                    "review_cost": cost, "times_rehearsed": 2 + profile * 3,
                    "independent_support": 1 + profile % 4},
            }
            source = _source("repetition", split, identifier, facts, f"replay_pattern_{case}", group=profile)
            source["skin_id"] = profile // (4 if split == "train" else 2)
            yield source


def _meta_sources(split):
    count = 16 if split == "train" else 8
    for profile in range(count):
        for case in range(6):
            identifier = "check-" + _sha(_json(["meta_reflection", split, profile, case]))[:16]
            practice_before = 2 + profile % 3
            new_before = 1 + (profile // 2) % 3
            before = {"assessment_id": identifier + "-assessment", "total": 12,
                      "practiced_correct": practice_before, "new_correct": new_before}
            after = dict(before)
            if case == 0:
                after["practiced_correct"] += 3
            if case == 4:
                if profile % 2:
                    after["assessment_id"] = identifier + "-different-assessment"
                else:
                    after["total"] = 15
                after["new_correct"] += profile % 3
            immediate = {"assessment_id": identifier + "-retention", "total": 12, "correct": 8 + profile % 3}
            delayed = dict(immediate, correct=immediate["correct"] - (4 if case == 1 else 0))
            correct_target = bool((profile // 2) % 2)
            facts = {"strategy": "reread_same_notes" if profile % 2 else "repeat_same_examples",
                     "strategy_repetitions": 2 + profile % 5,
                     "learner_self_report": "I learned it." if profile % 2 else "I did not learn it.",
                     "earlier_unrelated_public_outcome": bool(profile % 2),
                     "practice_action": [90000 + profile * 60 + case * 5 + (0 if split == "train" else 10000), -17, 29],
                     "verified_correct_target": correct_target,
                     "practiced_target": not correct_target if case == 3 else correct_target,
                     "verified_before": before, "verified_after": None if case == 5 else after,
                     "immediate_check": immediate, "delayed_check": delayed}
            source = _source("meta_reflection", split, identifier, facts, f"strategy_pattern_{case}", group=profile)
            source["skin_id"] = profile // (4 if split == "train" else 2)
            yield source


def _canaries():
    pairs = ((23, 38), (-27, 16), (61, -28), (0, -47), (-18, -36), (204, 37))
    strings = ("cedar-19", "FALSE stays text", "mK_83-v", "0097", "rehearse? wait", "trace=gold;check=violet")
    sources = [_source("arithmetic", "canary", f"repetition-meta-{index}", {"left": left, "right": right}, "preservation")
               for index, (left, right) in enumerate(pairs)]
    sources += [_source("copy", "canary", f"repetition-meta-{index}", {"text": text}, "preservation")
                for index, text in enumerate(strings)]
    return [_row(source, index % 4) for index, source in enumerate(sources)]


def build_dataset(skill, seed=0):
    if skill not in SKILLS:
        raise ValueError(f"skill must be one of {SKILLS}")
    if type(seed) is not int:
        raise ValueError("seed must be an integer, not bool")
    factory = _repetition_sources if skill == "repetition" else _meta_sources
    training = [_row(source, source["skin_id"]) for source in factory("train")]
    held = [_row(source, source["skin_id"]) for source in factory("held")]
    canary = _canaries()
    for rows in (training, held, canary):
        rows.sort(key=lambda row: _sha(_json([seed, row["row_id"]])))
    return {"schema": SCHEMA, "qualification": QUALIFICATION,
            "provenance": {"skill": skill, "seed": seed, "seed_effect": "ordering_only",
                "date": "2026-09-13", "origin": "PURE_AUTHORED_VISIBLE_DECISIONS",
                "scoring_version": SCORING_VERSION, "primary_pass": "content_correct",
                "references": list(REFERENCES), "skins": list(SKINS),
                "local_policy": REPETITION_POLICY if skill == "repetition" else META_POLICY,
                "infrastructure_source_sha256": INFRASTRUCTURE_SHA256,
                "infrastructure_reuse": "Copied helpers/scorer/row packager; no runtime dependency; new source cases and canaries.",
                "source_situations": {"train": 96, "held": 48},
                "source_groups": {"train": 16, "held": 8},
                "skin_counts": {"train": [24] * 4, "held": [12] * 4},
                "selection": "Fixed six-case factorial enumeration; one skin per source; seed orders only; no model-output tuning.",
                "limitations": list(LIMITATIONS),
                "rowset_sha256": _sha(_json([training, held, canary]))},
            "training": training, "evaluation": {"held": held, "canary": canary}}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill", choices=SKILLS)
    parser.add_argument("--seed", type=int, default=0)
    arguments = parser.parse_args()
    print(_json(build_dataset(arguments.skill, arguments.seed)))
