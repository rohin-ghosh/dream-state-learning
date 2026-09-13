"""Author-sourced DEVELOPMENT fixtures, not teacher generations or L2 evidence.

Only one explicitly selected skill/split is built at a time. Nothing here fits,
generates with a model, evaluates a hidden rule, or launches a native runner.
Record abstention has no spelling in the public record grammar: those judgement
fixtures deliberately have no training target. Main must review before use.
"""
from __future__ import annotations

import ast
from collections import Counter, defaultdict
import copy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re
from types import SimpleNamespace


SCHEMA = "birth_skill_corpus_v2_development_v1"
ORIGIN = "AUTHOR_SOURCED_DEVELOPMENT_ONLY"
SKILLS = ("perception", "reflection", "judgement")
SEED = 20260913
SITUATIONS = {
    "train": ((-4, 1, 7), (2, -5, 9)),
    "dev": ((11, -8, 3), (-6, 12, 5)),
}
EARLIER_PUBLIC_OUTCOMES = (False, True)
PUBLIC_CASES = (
    ("matched_true", "T", True),
    ("matched_false", "F", False),
    ("mismatched_true", "F", True),
    ("mismatched_false", "T", False),
    ("unavailable_true", None, True),
    ("unavailable_false", None, False),
)
TEMPLATES = {
    "train": "Supplied public situation:\n{events}\nUse only the final executed TRY and its supplied result.",
    "dev": "An earlier event is context, not the selected observation.\n{events}\nRecord the final event, not the earlier result or prediction.",
}
PUBLIC_CORRECTION = (
    "Distinguish an earlier explicit prediction from the returned outcome. "
    "In future records, compare them when a prediction exists, preserve the "
    "outcome even on a discrepancy, and leave an absent prediction null; "
    "do not infer a hidden rule from this one event."
)
LIMITATIONS = {
    "perception": "Public-record fidelity only; not perception outside this interface.",
    "reflection": "Author-supported free-prose restatement; exact fixture scoring is not semantic or spontaneous-reflection evidence.",
    "judgement": "No native record-abstention syntax. Negative fixtures have raw_target=null and no native score. Never export only the positive rows as a balanced judgement corpus.",
}


def _json(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False)


def _hash(value):
    return hashlib.sha256(_json(value).encode()).hexdigest()


@lru_cache(maxsize=1)
def _interface():
    """Load only public parser/record definitions, without runner imports."""
    path = Path(__file__).with_name("rulegame_parenting_diagnostic.py")
    text = path.read_text()
    constants = {"PROTOCOLS", "RECORD", "RELATION_DEFINITION"}
    functions = {"require", "unique_object", "decode", "parse_action", "judge_record", "record_instruction"}
    namespace = {"json": json, "re": re}
    selected = []
    spans = {}
    for node in ast.parse(text).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id in constants:
                namespace[target.id] = ast.literal_eval(node.value)
                spans[target.id] = ast.get_source_segment(text, node)
        if isinstance(node, ast.FunctionDef) and node.name in functions:
            selected.append(node)
            spans[node.name] = ast.get_source_segment(text, node)
    if set(spans) != constants | functions:
        raise ValueError("public parser interface changed")
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(path), "exec"), namespace)
    namespace["source_manifest"] = {
        "path": "organism_v6/rulegame_parenting_diagnostic.py",
        "selected_definitions_sha256": _hash(spans),
        "definitions": {name: hashlib.sha256(span.encode()).hexdigest() for name, span in sorted(spans.items())},
    }
    return SimpleNamespace(**namespace)


def _identify(source):
    source["source_id"] = _hash({key: value for key, value in source.items() if key != "source_id"})
    return source


def public_sources(split):
    """Literal split, complete six-case factorial per independently authored box.

    Outcomes are supplied in PUBLIC_CASES, never computed from triple features.
    Opposite outcomes for one triple belong to different hypothetical boxes.
    """
    if split not in SITUATIONS:
        raise ValueError("split must be literal train or dev")
    sources = []
    for situation_index, triple in enumerate(SITUATIONS[split]):
        values = ",".join(map(str, triple))
        for case, prediction, observed in PUBLIC_CASES:
            output = (f"PREDICT: {prediction}\n" if prediction is not None else "") + f"ACT: TRY {values}"
            events = []
            if split == "dev":
                events.append({
                    "event_id": "e0", "raw_response": "ACT: TRY 20,21,22",
                    "raw_outcome": f"the box says: {EARLIER_PUBLIC_OUTCOMES[situation_index]} for (20,21,22)",
                })
            event_id = f"e{len(events)}"
            events.append({"event_id": event_id, "raw_response": output,
                           "raw_outcome": f"the box says: {observed} for ({values})"})
            sources.append(_identify({
                "origin": ORIGIN, "split": split, "template_id": split,
                "situation_index": situation_index, "case": case,
                "selected_event_id": event_id, "events": events,
            }))
    return sources


def assess_source(source):
    """Derive admissibility and field proofs solely from supplied public bytes."""
    interface = _interface()
    if source.get("origin") != ORIGIN:
        raise ValueError("only author-sourced development fixtures are accepted")
    if source.get("source_id") != _identify(copy.deepcopy(source))["source_id"]:
        raise ValueError("source hash mismatch")
    events = source["events"]
    if not events or len({event["event_id"] for event in events}) != len(events):
        raise ValueError("empty or duplicate public events")
    event = events[-1]
    if event["event_id"] != source["selected_event_id"]:
        raise ValueError("selected event must be the final public execution")
    base = {"source_id": source["source_id"], "event_id": event["event_id"]}
    proof = {
        "try": dict(base, field="raw_response", raw=event["raw_response"]),
        "predicted": dict(base, field="raw_response", raw=event["raw_response"],
                          rule="Only an unambiguous literal PREDICT: T/F before ACT counts; absence is null."),
        "observed": dict(base, field="raw_outcome", raw=event["raw_outcome"]),
        "relation": dict(base, fields=["raw_response", "raw_outcome"], rule=interface.RELATION_DEFINITION),
    }
    reasons = []
    try:
        action = interface.parse_action(event["raw_response"], "interaction_v3")
    except (ValueError, TypeError):
        return dict(admissible=False, reasons=["invalid_public_action"], execution=None, proof=proof)
    if action["kind"] != "try":
        return dict(admissible=False, reasons=["not_a_public_try"], execution=None, proof=proof)
    if action["prediction_ambiguous"]:
        reasons.append("ambiguous_public_prediction")
    outcome = event["raw_outcome"]
    match = re.fullmatch(r"the box says: (True|False) for \((-?[0-9]+),(-?[0-9]+),(-?[0-9]+)\)", outcome) if isinstance(outcome, str) else None
    if match is None:
        reasons.append("missing_or_invalid_public_outcome")
    elif [int(value) for value in match.groups()[1:]] != action["values"]:
        reasons.append("public_outcome_action_mismatch")
    if reasons:
        return dict(admissible=False, reasons=reasons, execution=None, proof=proof)
    execution = dict(action, observed=match.group(1) == "True")
    for field, key in (("try", "values"), ("predicted", "predicted"), ("observed", "observed")):
        proof[field]["value"] = execution[key]
    proof["relation"]["value"] = ("unavailable" if execution["predicted"] is None else
                                  "matched" if execution["predicted"] == execution["observed"] else "mismatched")
    return dict(admissible=True, reasons=[], execution=execution, proof=proof)


def _with_insufficient_evidence(source):
    result = copy.deepcopy(source)
    event = result["events"][-1]
    if source["situation_index"] == 0:
        lines = event["raw_response"].splitlines()
        additional = "PREDICT: F" if lines[0] == "PREDICT: T" else "PREDICT: T"
        if len(lines) == 1:
            additional = "PREDICT: uncertain"
        event["raw_response"] = "\n".join(lines[:-1] + [additional, lines[-1]])
        operation = "supply_ambiguous_prior_prediction"
    else:
        outcome = event["raw_outcome"].split(" for ")[0]
        event["raw_outcome"] = outcome + " for (30,31,32)"
        operation = "supply_outcome_for_different_action"
    result["derivation"] = {"parent_source_id": source["source_id"], "operation": operation}
    return _identify(result)


def _transcript(source):
    blocks = []
    for event in source["events"]:
        outcome = event["raw_outcome"] if event["raw_outcome"] is not None else "[No public outcome supplied]"
        blocks.append(f"Event {event['event_id']}\n{event['raw_response']}\n[OUTCOME] {outcome}")
    return TEMPLATES[source["template_id"]].format(events="\n\n".join(blocks))


def _reflection(assessment):
    execution = assessment["execution"]
    values = ",".join(map(str, execution["values"]))
    observed, predicted = execution["observed"], execution["predicted"]
    relation = assessment["proof"]["relation"]["value"]
    if predicted is None:
        first = f"No explicit prediction preceded TRY {values}; its supplied outcome was {observed}, so the relation is unavailable."
        second = "For later records, I should leave an absent prediction null rather than invent one; an observation is not a prior prediction."
    else:
        first = f"For TRY {values}, I predicted {predicted} and the supplied outcome was {observed}, so the prediction {relation}."
        second = ("For later records, I should preserve the returned outcome instead of copying a contradicted prediction; this event does not establish a hidden rule."
                  if relation == "mismatched" else
                  "For later records, I should compare the explicit prediction with the returned outcome; one agreement does not establish a hidden rule.")
    return first + " " + second


def _row(skill, source, system_anchor):
    assessment = assess_source(source)
    prompt = _transcript(source)
    target = None
    proof = copy.deepcopy(assessment["proof"])
    if skill == "reflection":
        prompt = "Your parent said:\n" + prompt + "\n" + PUBLIC_CORRECTION + "\nRestate that message in your own words in 2-3 sentences."
        target = _reflection(assessment)
        proof["reusable_procedure"] = {"source": "author_supplied_parent_message", "raw": PUBLIC_CORRECTION,
                                       "sha256": hashlib.sha256(PUBLIC_CORRECTION.encode()).hexdigest()}
    else:
        prompt += "\n" + _interface().record_instruction("interaction_v3")
        if assessment["admissible"]:
            target = _json({field: assessment["proof"][field]["value"] for field in ("try", "observed", "predicted", "relation")})
    messages = ([{"role": "system", "content": system_anchor}] if system_anchor is not None else [])
    messages.append({"role": "user", "content": prompt})
    return {
        "row_id": f"{skill}:{source['source_id']}", "skill": skill,
        "source": source, "source_proof": proof, "input_messages": messages,
        "raw_target": target, "target_sha256": None if target is None else hashlib.sha256(target.encode()).hexdigest(),
        "input_sha256": _hash(messages), "source_admissible": assessment["admissible"],
        "admissibility_reasons": assessment["reasons"],
        "response_role": "restate" if skill == "reflection" else "record",
        "target_status": "AUTHOR_SUPPORTED_TARGET" if target is not None else "UNEXPRESSIBLE_NATIVE_ABSTENTION",
    }


def audit_rows(rows):
    """Check matched semantic coverage, input collisions, and simple shortcuts."""
    input_targets = defaultdict(set)
    groups = defaultdict(list)
    for row in rows:
        input_targets[row["input_sha256"]].add(row["raw_target"])
        if "derivation" not in row["source"]:
            source = row["source"]
            groups[(source["template_id"], source["situation_index"])].append(row)
    collisions = sum(len(targets) > 1 for targets in input_targets.values())
    balanced = bool(groups)
    for group in groups.values():
        records = [assess_source(row["source"])["proof"] for row in group]
        balanced &= Counter(record["observed"]["value"] for record in records) == {True: 3, False: 3}
        balanced &= Counter(record["predicted"]["value"] for record in records) == {True: 2, False: 2, None: 2}
        balanced &= Counter(record["relation"]["value"] for record in records) == {"matched": 2, "mismatched": 2, "unavailable": 2}
    originals = Counter(row["source"]["source_id"] for row in rows if "derivation" not in row["source"])
    negative_parents = Counter(row["source"]["derivation"]["parent_source_id"] for row in rows if "derivation" in row["source"])
    paired = negative_parents == originals if any(row["skill"] == "judgement" for row in rows) else not negative_parents
    return {"input_target_collisions": collisions, "balanced_per_template_and_triple": bool(balanced),
            "duplicate_inputs": len(rows) - len(input_targets),
            "judgement_pairing_complete": paired,
            "shortcut_scope": "Outcome, relation and prediction cannot be inferred from triple or template alone. No universal shortcut guarantee.",
            "admissibility_counts": dict(Counter(str(row["source_admissible"]).lower() for row in rows))}


def build_slice(skill, *, split, system_anchor, seed=SEED):
    """Build input/target/proof rows; there is deliberately no mixture default.

    system_anchor must be explicitly supplied as exact text or explicitly None.
    A None raw_target is NOT a null/empty-string assistant training response.
    """
    if skill not in SKILLS:
        raise ValueError("choose exactly one named skill slice")
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    if system_anchor is not None and (not isinstance(system_anchor, str) or not system_anchor.strip()):
        raise ValueError("anchor must be nonblank supplied text or None")
    sources = public_sources(split)
    if skill == "judgement":
        sources += [_with_insufficient_evidence(source) for source in list(sources)]
    rows = [_row(skill, source, system_anchor) for source in sources]
    rows.sort(key=lambda row: _hash([seed, row["row_id"]]))
    audit = audit_rows(rows)
    if audit["input_target_collisions"] or audit["duplicate_inputs"] or not audit["balanced_per_template_and_triple"] or not audit["judgement_pairing_complete"]:
        raise ValueError("corpus collision or semantic balance failure")
    manifest = {
        "schema": SCHEMA, "origin": ORIGIN, "skill": skill, "split": split, "order_seed": seed,
        "anchor_variant": "absent" if system_anchor is None else "supplied",
        "system_anchor": system_anchor, "system_anchor_sha256": None if system_anchor is None else hashlib.sha256(system_anchor.encode()).hexdigest(),
        "literal_split_situations": SITUATIONS, "public_case_table": PUBLIC_CASES,
        "earlier_public_outcomes": EARLIER_PUBLIC_OUTCOMES,
        "template_manifest": TEMPLATES, "parent_message": PUBLIC_CORRECTION if skill == "reflection" else None,
        "interface": _interface().source_manifest, "row_count": len(rows),
        "target_count": sum(row["raw_target"] is not None for row in rows),
        "source_manifest": [{"row_id": row["row_id"], "source_sha256": row["source"]["source_id"],
                             "input_sha256": row["input_sha256"], "target_sha256": row["target_sha256"]} for row in rows],
        "rows_sha256": _hash(rows), "audit": audit,
        "native_use_status": "MAIN_REVIEW_REQUIRED", "training_export_ready": False,
        "qualification": "PUBLIC_SITUATION_DEVELOPMENT_PROBES_ONLY_NOT_L2",
        "persistence": "Absent-input pairing is not evidence of post-training withdrawal persistence.",
        "limitation": LIMITATIONS[skill],
    }
    return {"manifest": copy.deepcopy(manifest), "rows": rows}


def build_variants(skill, *, split, system_anchor, seed=SEED):
    if not isinstance(system_anchor, str) or not system_anchor.strip():
        raise ValueError("provide the exact nonblank anchor hypothesis")
    return {"supplied": build_slice(skill, split=split, system_anchor=system_anchor, seed=seed),
            "absent": build_slice(skill, split=split, system_anchor=None, seed=seed)}


def audit_split_pair(train, dev):
    if train["manifest"]["split"] != "train" or dev["manifest"]["split"] != "dev":
        raise ValueError("literal train then dev required")
    if train["manifest"]["skill"] != dev["manifest"]["skill"]:
        raise ValueError("compare the same skill")
    overlaps = {}
    for field in ("row_id", "input_sha256", "raw_target"):
        left = {row[field] for row in train["rows"] if row[field] is not None}
        right = {row[field] for row in dev["rows"] if row[field] is not None}
        overlaps[field] = len(left & right)
    triples = []
    selected_events = []
    for built in (train, dev):
        events = [row["source"]["events"][-1] for row in built["rows"]]
        triples.append({tuple(_interface().parse_action(event["raw_response"], "interaction_v3")["values"]) for event in events})
        selected_events.append({_hash([event["raw_response"], event["raw_outcome"]]) for event in events})
    overlaps["selected_triples"] = len(triples[0] & triples[1])
    overlaps["selected_event_bytes"] = len(selected_events[0] & selected_events[1])
    return {"overlaps": overlaps, "disjoint": not any(overlaps.values()),
            "boundary": "Authored source/template holdout only; shared public grammar and semantic cases are intentional."}


def score_response(row, raw_response):
    """CPU public-record scorer; prose has exact-fixture scoring only."""
    assessment = assess_source(row["source"])
    if not assessment["admissible"]:
        return {"passed": None, "score_kind": "unsupported_native_abstention", "reasons": assessment["reasons"]}
    if row["skill"] == "reflection":
        return {"passed": raw_response == _reflection(assessment), "score_kind": "exact_authored_restatement_only"}
    if not isinstance(raw_response, str):
        return {"passed": False, "score_kind": "public_record_parser", "failures": ["response must be raw text"]}
    result = _interface().judge_record(raw_response, assessment["execution"])
    return {"passed": result["eligible"], "score_kind": "public_record_parser", "failures": result["failures"]}
