"""Offline, deterministic analysis of the dream-ladder v5 artifacts.

This module deliberately does not run a model, access a GPU, or mutate a
run.  The runner writes the nested curve already, but this reader recomputes
the headline counts from the per-target audit and refuses to summarize an
artifact whose accounting/provenance contract is incomplete.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence


EXPECTED_K = 6
EXPECTED_SAMPLES = 4
EXPECTED_MATCHED_COMPUTE = False
CONDITION_ID = "task_family_scaffolded_public_evidence_exact_gate_ceiling"
UNSAFE_LABEL_RE = re.compile(r"parent[ _-]?exact|offline[ _-]?parent", re.I)


class V5AnalysisError(ValueError):
    """Raised when an artifact cannot be safely analyzed."""

    def __init__(self, errors: Sequence[str]):
        self.errors = list(errors)
        super().__init__("; ".join(self.errors))


def _is_map(value: Any) -> bool:
    return isinstance(value, Mapping)


def _int(value: Any, name: str, errors: list[str], *, minimum: int = 0) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        errors.append(f"{name} must be an integer >= {minimum}")
        return None
    return value


def _ratio(numerator: int, denominator: int) -> dict[str, Any]:
    return {
        "numerator": numerator,
        "denominator": denominator,
        "value": (numerator / denominator) if denominator else None,
    }


def _unsafe_labels(value: Any, path: str = "$") -> list[str]:
    """Find labels that would expose an unsafe parent-exact claim.

    Raw prose is not inspected: a model may mention words in an unrelated
    sentence, while a machine-readable field named ``parent_exact`` is an
    actual claim label and must stop the analysis.
    """
    found: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            if UNSAFE_LABEL_RE.search(key_text):
                found.append(f"{path}.{key_text}")
            if isinstance(child, str) and UNSAFE_LABEL_RE.search(child):
                # Status/metadata labels are unsafe; free-form raw text is not.
                if key_text.lower() not in {"raw", "text", "prompt", "answer"}:
                    found.append(f"{path}.{key_text}")
            found.extend(_unsafe_labels(child, f"{path}.{key_text}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(_unsafe_labels(child, f"{path}[{index}]"))
    return found


def _load(path: str | Path) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not _is_map(value):
        raise V5AnalysisError([f"{path}: top-level JSON value is not an object"])
    return dict(value)


def _validate_condition(dream: Mapping[str, Any], errors: list[str]) -> dict[str, Any]:
    condition = dream.get("condition")
    if not _is_map(condition):
        errors.append("dream artifact is missing condition metadata")
        return {}
    expected = {
        "id": CONDITION_ID,
        "headline_eligible": False,
        "task_family_scaffold": True,
        "public_evidence_exact_gate": True,
        "offline_truth_in_cognition": False,
        "contradicted_fallback_retention": "legacy_ablation_only",
    }
    for key, wanted in expected.items():
        if condition.get(key) != wanted:
            errors.append(f"condition.{key} must equal {wanted!r}")
    return dict(condition)


def _validate_compute(dream: Mapping[str, Any], errors: list[str]) -> dict[str, Any]:
    compute = dream.get("compute")
    if not _is_map(compute):
        errors.append("dream artifact is missing compute metadata")
        return {}
    expected = {
        "k_per_target_per_sample": EXPECTED_K,
        "samples": EXPECTED_SAMPLES,
        "candidate_ceiling_per_target": EXPECTED_K * EXPECTED_SAMPLES,
        "matched_compute_to_v4": EXPECTED_MATCHED_COMPUTE,
    }
    for key, wanted in expected.items():
        if compute.get(key) != wanted:
            errors.append(f"compute.{key} must equal {wanted!r}")
    if "samples" in dream and dream.get("samples") != EXPECTED_SAMPLES:
        errors.append("dream.samples must equal four")
    return dict(compute)


def _validate_generation_provenance(dream: Mapping[str, Any], errors: list[str]) -> list[dict[str, Any]]:
    audit = dream.get("audit")
    if not _is_map(audit):
        errors.append("dream artifact is missing audit provenance")
        return []
    raw = audit.get("raw")
    if not isinstance(raw, list) or not raw:
        errors.append("dream audit.raw is missing or empty")
        return []
    records: list[dict[str, Any]] = []
    for index, record in enumerate(raw):
        if not _is_map(record):
            errors.append(f"audit.raw[{index}] is not an object")
            continue
        missing = [key for key in ("stage", "text", "prompt_tokens", "output_tokens")
                   if key not in record]
        if missing:
            errors.append(f"audit.raw[{index}] missing provenance fields: {missing}")
            continue
        if not isinstance(record["stage"], str) or not isinstance(record["text"], str):
            errors.append(f"audit.raw[{index}] is missing a raw completion")
        for key in ("prompt_tokens", "output_tokens", "original_prompt_tokens"):
            if key in record:
                _int(record[key], f"audit.raw[{index}].{key}", errors)
        if "prompt_truncated" not in record or not isinstance(record["prompt_truncated"], bool):
            errors.append(f"audit.raw[{index}].prompt_truncated is missing or not boolean")
        source = record.get("token_count_source", record.get("source"))
        if source != "model_token_ids":
            errors.append(f"audit.raw[{index}] lacks model-token provenance")
        records.append(dict(record))
    return records


def _validate_evidence(dream: Mapping[str, Any], hypotheses: list[Mapping[str, Any]], errors: list[str]) -> None:
    audit = dream.get("audit")
    evidence = audit.get("role_discovery_evidence") if _is_map(audit) else None
    if not _is_map(evidence):
        errors.append("missing role-discovery provenance record")
    else:
        if evidence.get("policy") != "ordinary_source_lands_only":
            errors.append("role-discovery provenance has unsafe/missing evidence policy")
        for key in ("allowed_lands", "allowed_evidence_ids", "excluded_target_lands", "excluded_target_evidence_ids"):
            if not isinstance(evidence.get(key), list):
                errors.append(f"role-discovery provenance missing {key}")
    if not hypotheses:
        errors.append("dream artifact has no target hypothesis records")
    for index, hypothesis in enumerate(hypotheses):
        records = hypothesis.get("blind_comparison_evidence")
        if not isinstance(records, list) or not records:
            errors.append(f"hypotheses[{index}] missing blind-comparison provenance records")
            continue
        for row_index, row in enumerate(records):
            if not _is_map(row) or any(not isinstance(row.get(k), str) or not row.get(k)
                                       for k in ("evidence_id", "entity", "land", "observed_token")):
                errors.append(f"hypotheses[{index}].blind_comparison_evidence[{row_index}] is incomplete")


def _sample_index(stage: str) -> int | None:
    match = re.search(r":s(\d+)$", stage)
    return int(match.group(1)) if match else None


def _records_at(records: Sequence[Mapping[str, Any]], prefix: int, kind: str) -> list[Mapping[str, Any]]:
    out = []
    for record in records:
        stage = str(record.get("stage", ""))
        if kind == "recipe" and stage == "recipes":
            out.append(record)
        elif kind == "roles" and stage.startswith("roles:s"):
            sample = _sample_index(stage)
            if sample is not None and sample < prefix:
                out.append(record)
        elif kind == "parents" and stage.startswith("parents:"):
            sample = _sample_index(stage)
            if sample is not None and sample < prefix:
                out.append(record)
    return out


def _keys(rows: Any) -> set[tuple[str, ...]]:
    if not isinstance(rows, list):
        return set()
    out: set[tuple[str, ...]] = set()
    for row in rows:
        if _is_map(row) and isinstance(row.get("parents"), list):
            out.add(tuple(str(x) for x in row["parents"]))
    return out


def _target_prefix_metrics(hypotheses: Sequence[Mapping[str, Any]], target_views: Sequence[Mapping[str, Any]], prefix: int, errors: list[str]) -> dict[str, Any]:
    parent = {
        "raw_candidate_lines": 0,
        "overflow_candidate_lines": 0,
        "emitted_candidate_lines": 0,
        "parsed_candidate_lines": 0,
        "malformed_candidate_lines": 0,
        "unique_proposed": 0,
        "unique_proposed_true": 0,
        "targets_with_true_proposed": 0,
        "supported": 0,
        "supported_true": 0,
        "retained_total": 0,
        "retained_true": 0,
        "by_target": [],
    }
    for target_index, hypothesis in enumerate(hypotheses):
        target = hypothesis.get("target", f"target_{target_index}")
        view = target_views[target_index] if target_index < len(target_views) else {}
        truth = view.get("truth")
        if not isinstance(truth, list) or not truth:
            # Truth is a scoring key; it is not emitted in the result.
            errors.append(f"hypotheses[{target_index}] missing non-empty scoring truth")
            truth_key: tuple[str, ...] = ()
        else:
            truth_key = tuple(str(x) for x in truth)
        raw = [x for x in hypothesis.get("raw_candidates", [])
               if _is_map(x) and isinstance(x.get("sample"), int) and x["sample"] < prefix]
        overflow = [x for x in hypothesis.get("overflow_candidates", [])
                    if _is_map(x) and isinstance(x.get("sample"), int) and x["sample"] < prefix]
        malformed = [x for x in hypothesis.get("malformed_candidates", [])
                     if _is_map(x) and isinstance(x.get("sample"), int) and x["sample"] < prefix]
        scored_all = [x for x in hypothesis.get("scored", [])
                      if _is_map(x) and isinstance(x.get("sample"), int) and x["sample"] < prefix]
        for sample in range(prefix):
            eligible_sample = [x for x in hypothesis.get("raw_candidates", [])
                               if _is_map(x) and x.get("sample") == sample]
            if len(eligible_sample) > EXPECTED_K:
                errors.append(f"target {target} sample {sample} exceeds k candidate budget")
            if any(x.get("eligible") is not True for x in eligible_sample):
                errors.append(f"target {target} has an eligible candidate marked ineligible")
        overflow_all = [x for x in hypothesis.get("overflow_candidates", [])
                        if _is_map(x) and isinstance(x.get("sample"), int) and x["sample"] < prefix]
        if any(x.get("eligible") is not False or x.get("reason") != "over_candidate_budget"
               for x in overflow_all):
            errors.append(f"target {target} has invalid overflow candidate provenance")
        proposed = _keys([x for x in hypothesis.get("scored", [])
                          if _is_map(x) and isinstance(x.get("sample"), int) and x["sample"] < prefix])
        # The runner places per-target views in each sample_curve row.  They
        # are the authoritative append-only sets (including status upgrades).
        proposed = _keys(view.get("proposed"))
        supported_keys = _keys(view.get("supported"))
        retained_keys = _keys(view.get("retained"))
        if not view:
            errors.append(f"sample prefix {prefix} is missing by-target accounting")
        if view:
            for key, wanted in (("raw_lines", len(raw)), ("overflow_lines", len(overflow)),
                                ("emitted_candidate_lines", len(raw) + len(overflow)),
                                ("parsed", len(scored_all)), ("malformed", len(malformed))):
                if view.get(key) != wanted:
                    errors.append(f"prefix {prefix} target {target} {key} does not match audit")
        unique_true = int(bool(truth_key and truth_key in proposed))
        supported_true = int(bool(truth_key and truth_key in supported_keys))
        retained_true = int(bool(truth_key and truth_key in retained_keys))
        parent["raw_candidate_lines"] += len(raw)
        parent["overflow_candidate_lines"] += len(overflow)
        parent["emitted_candidate_lines"] += len(raw) + len(overflow)
        parent["parsed_candidate_lines"] += len(scored_all)
        parent["malformed_candidate_lines"] += len(malformed)
        parent["unique_proposed"] += len(proposed)
        parent["unique_proposed_true"] += unique_true
        parent["targets_with_true_proposed"] += unique_true
        parent["supported"] += len(supported_keys)
        parent["supported_true"] += supported_true
        parent["retained_total"] += len(retained_keys)
        parent["retained_true"] += retained_true
        parent["by_target"].append({
            "target": target,
            "raw_candidate_lines": len(raw),
            "overflow_candidate_lines": len(overflow),
            "proposed_count": len(proposed),
            "supported_count": len(supported_keys),
            "retained_total": len(retained_keys),
        })
    return parent


def _validate_prefixes(dream: Mapping[str, Any], records: list[dict[str, Any]], hypotheses: list[Mapping[str, Any]], compute: Mapping[str, Any], errors: list[str], role_truth_count: int | None = None) -> list[dict[str, Any]]:
    curve = dream.get("sample_curve")
    if not isinstance(curve, list) or len(curve) != EXPECTED_SAMPLES:
        errors.append("sample_curve must contain exactly four prefixes")
        return []
    if [row.get("samples") if _is_map(row) else None for row in curve] != [1, 2, 3, 4]:
        errors.append("sample_curve prefixes must be nested samples 1, 2, 3, 4")
    outputs: list[dict[str, Any]] = []
    previous: dict[str, int] | None = None
    previous_sets: dict[str, set[tuple[str, ...]]] = {}
    roles_obj = dream.get("roles") if _is_map(dream.get("roles")) else {}
    audit_obj = dream.get("audit") if _is_map(dream.get("audit")) else {}
    role_truth = set()
    for source in (roles_obj, audit_obj):
        if isinstance(source.get("truth"), list):
            role_truth = {tuple(x) for x in source["truth"] if isinstance(x, list)}
        if isinstance(source.get("roles_truth"), list):
            role_truth = {tuple(x) for x in source["roles_truth"] if isinstance(x, list)}
    if role_truth and role_truth_count is not None and len(role_truth) != role_truth_count:
        errors.append("explicit role truth denominator disagrees with offline truth records")
    role_denominator = len(role_truth) if role_truth else role_truth_count
    if not role_denominator:
        errors.append("role truth denominator is missing; pass explicit offline role truth count")
    for index, row in enumerate(curve):
        if not _is_map(row):
            errors.append(f"sample_curve[{index}] is not an object")
            continue
        prefix = index + 1
        budget = row.get("budget")
        if not _is_map(budget):
            errors.append(f"sample_curve[{index}] missing budget")
            budget = {}
        for key, wanted in (("k_per_target_per_sample", EXPECTED_K),
                            ("candidate_ceiling_per_target", EXPECTED_K * prefix),
                            ("matched_compute_to_v4", EXPECTED_MATCHED_COMPUTE)):
            if budget.get(key) != wanted:
                errors.append(f"sample_curve[{index}].budget.{key} mismatch")
        if budget.get("samples") not in (None, prefix):
            errors.append(f"sample_curve[{index}].budget.samples mismatch")
        parent_meta = row.get("parents")
        if not _is_map(parent_meta):
            errors.append(f"sample_curve[{index}] missing parents accounting")
            parent_meta = {}
        target_views = parent_meta.get("by_target") if isinstance(parent_meta.get("by_target"), list) else []
        if len(target_views) != len(hypotheses):
            errors.append(f"sample_curve[{index}].parents.by_target length mismatch")
        for target_index, hypothesis in enumerate(hypotheses):
            if target_index < len(target_views) and _is_map(target_views[target_index]):
                if target_views[target_index].get("target") != hypothesis.get("target"):
                    errors.append(f"sample_curve[{index}] target ordering mismatch")
        metrics = _target_prefix_metrics(hypotheses, target_views, prefix, errors)
        generation_records = (_records_at(records, prefix, "recipe")
                              + _records_at(records, prefix, "roles")
                              + _records_at(records, prefix, "parents"))
        generation_expected = {
            "generation_calls": len(generation_records),
            "prompt_tokens": sum(r.get("prompt_tokens", 0) for r in generation_records),
            "output_tokens": sum(r.get("output_tokens", 0) for r in generation_records),
        }
        for key, wanted in generation_expected.items():
            if budget.get(key) != wanted:
                errors.append(f"sample_curve[{index}].budget.{key} does not match raw generation provenance")
        field_pairs = {
            "raw_lines_total": metrics["raw_candidate_lines"],
            "overflow_lines_total": metrics["overflow_candidate_lines"],
            "emitted_candidate_lines_total": metrics["emitted_candidate_lines"],
            "parsed_total": metrics["parsed_candidate_lines"],
            "malformed_total": metrics["malformed_candidate_lines"],
            "unique_proposed_total": metrics["unique_proposed"],
            "unique_proposed_true": metrics["unique_proposed_true"],
            "targets_with_true_proposed": metrics["targets_with_true_proposed"],
            "supported_total": metrics["supported"],
            "supported_true": metrics["supported_true"],
            "retained_total": metrics["retained_total"],
            "retained_true": metrics["retained_true"],
        }
        for key, wanted in field_pairs.items():
            if parent_meta.get(key) != wanted:
                errors.append(f"sample_curve[{index}].parents.{key} does not match audited records")
        role_meta = row.get("roles")
        if not _is_map(role_meta):
            errors.append(f"sample_curve[{index}] missing roles accounting")
            role_meta = {}
        role_rows = [r for r in (dream.get("roles", {}) or {}).get("proposals", [])
                     if _is_map(r) and isinstance(r.get("sample"), int) and r["sample"] < prefix]
        parsed_pairs = {tuple(r.get("pair", [])) for r in role_rows if r.get("parsed") is True and isinstance(r.get("pair"), list)}
        accepted_pairs = {tuple(r.get("pair", [])) for r in role_rows if r.get("parsed") is True and r.get("public_check") is True and isinstance(r.get("pair"), list)}
        role_field_pairs = {
            "raw_lines_total": len(role_rows),
            "parsed_total": sum(r.get("parsed") is True for r in role_rows),
            "malformed_total": sum(r.get("parsed") is not True for r in role_rows),
            "unique_proposed_total": len(parsed_pairs),
            "accepted_total": len(accepted_pairs),
        }
        for key, wanted in role_field_pairs.items():
            if role_meta.get(key) != wanted:
                errors.append(f"sample_curve[{index}].roles.{key} does not match role proposals")
        # Existing v5 artifacts carry the offline role truth in sample_curve.
        role_true = role_meta.get("accepted_true")
        role_total = role_meta.get("accepted_total")
        if not isinstance(role_true, int) or not isinstance(role_total, int):
            errors.append(f"sample_curve[{index}].roles lacks raw accepted numerators")
            role_true = sum(pair in role_truth for pair in accepted_pairs)
            role_total = len(accepted_pairs)
        role_report = {
            "proposed": _ratio(int(role_meta.get("unique_proposed_true", 0)), int(role_meta.get("unique_proposed_total", len(parsed_pairs)))),
            "precision": _ratio(role_true, role_total),
            "recall": _ratio(role_true, role_denominator or 0),
            "accepted": {"true": role_true, "total": role_total},
            "truth_denominator": role_denominator,
        }
        # Prefix monotonicity is a hard contract, including retained claims.
        current_counts = {
            "raw_candidate_lines": metrics["raw_candidate_lines"],
            "overflow_candidate_lines": metrics["overflow_candidate_lines"],
            "unique_proposed": metrics["unique_proposed"],
            "supported": metrics["supported"],
            "retained_total": metrics["retained_total"],
            "retained_true": metrics["retained_true"],
        }
        if previous is not None:
            for key, value in current_counts.items():
                if value < previous[key]:
                    errors.append(f"sample_curve is not nested: {key} decreases at prefix {prefix}")
        previous = current_counts
        # Canonical parent sets, supported sets, and retained sets must be
        # genuinely nested, not merely monotonic in their aggregate counts.
        for name, rows in (("proposed", [v for v in target_views for v in (v.get("proposed", []) if _is_map(v) else [])]),
                           ("supported", [v for v in target_views for v in (v.get("supported", []) if _is_map(v) else [])]),
                           ("retained", [v for v in target_views for v in (v.get("retained", []) if _is_map(v) else [])])):
            current_set = _keys(rows)
            if name in previous_sets and not previous_sets[name] <= current_set:
                errors.append(f"sample_curve is not nested: {name} set shrinks at prefix {prefix}")
            previous_sets[name] = current_set
        outputs.append({
            "prefix": prefix,
            "candidate_counts": {
                "actual": metrics["raw_candidate_lines"],
                "overflow": metrics["overflow_candidate_lines"],
                "emitted": metrics["emitted_candidate_lines"],
                "parsed": metrics["parsed_candidate_lines"],
                "malformed": metrics["malformed_candidate_lines"],
            },
            "target_proposal_recall": _ratio(metrics["targets_with_true_proposed"], len(hypotheses)),
            "supported_precision": _ratio(metrics["supported_true"], metrics["supported"]),
            "retained": {
                "true": metrics["retained_true"],
                "total": metrics["retained_total"],
                "false_contamination": _ratio(metrics["retained_total"] - metrics["retained_true"], metrics["retained_total"]),
            },
            "roles": role_report,
            "budget": dict(budget),
        })
    return outputs


def _validate_thinker(thinker: Mapping[str, Any], errors: list[str]) -> dict[str, Any]:
    calls = thinker.get("calls")
    traces = thinker.get("traces")
    if not isinstance(calls, list) or not calls:
        errors.append("thinker artifact is missing calls with raw completions")
        calls = []
    for index, call in enumerate(calls):
        if not _is_map(call) or not isinstance(call.get("raw_completion"), str):
            errors.append(f"thinker.calls[{index}] is missing raw_completion")
            continue
        for key in ("prompt_tokens", "output_tokens"):
            _int(call.get(key), f"thinker.calls[{index}].{key}", errors)
        if call.get("token_count_source", "model_token_ids") != "model_token_ids":
            errors.append(f"thinker.calls[{index}] lacks model-token provenance")
    if not isinstance(traces, list) or not traces:
        errors.append("thinker artifact is missing traces")
        traces = []
    by_depth: dict[str, dict[str, int]] = {}
    for index, trace in enumerate(traces):
        if not _is_map(trace):
            errors.append(f"thinker.traces[{index}] is not an object")
            continue
        depth = str(trace.get("depth", ""))
        match = re.fullmatch(r"D([0-3])(?:blend)?", depth, re.I)
        if not match:
            errors.append(f"thinker.traces[{index}] has invalid depth")
            continue
        depth = f"D{match.group(1)}"
        if not isinstance(trace.get("ok"), bool):
            errors.append(f"thinker.traces[{index}].ok is missing or not boolean")
            continue
        row = by_depth.setdefault(depth, {"correct": 0, "total": 0, "malformed": 0})
        row["total"] += 1
        row["correct"] += int(trace["ok"])
        row["malformed"] += int(bool(trace.get("malformed")))
    budget = thinker.get("budget")
    if not _is_map(budget):
        errors.append("thinker artifact is missing budget metadata")
        budget = {}
    thinker_calls = [c for c in calls if _is_map(c) and c.get("kind") == "thinker"]
    memory_calls = [c for c in calls if _is_map(c) and c.get("kind") == "memory_model_read"]
    def is_memory_operation(op: Any) -> bool:
        if not isinstance(op, (list, tuple)) or not op:
            return False
        # The runtime prices a repeated query before the repeat guard fires,
        # and it also prices a final-budget MEMORY request even though that
        # request is not served.  Both remain memory-query operations in the
        # frozen artifact and must be reconstructed from their explicit trace
        # records rather than silently discarded by the analyzer.
        return (
            op[0] in {"MEMORY", "REPEAT"}
            or (op[0] == "BUDGET_EXHAUSTED_WITHOUT_ANSWER"
                and len(op) > 1 and op[1] == "MEMORY")
        )

    memory_ops = sum(
        sum(1 for op in (t.get("trace") or []) if is_memory_operation(op))
        for t in traces if _is_map(t)
    )
    derived = {
        "thinker_generation_calls": len(thinker_calls),
        "memory_query_operations": memory_ops,
        "memory_model_generation_calls": len(memory_calls),
        "thinker_prompt_tokens": sum(c.get("prompt_tokens", 0) for c in thinker_calls),
        "thinker_output_tokens": sum(c.get("output_tokens", 0) for c in thinker_calls),
        "memory_prompt_tokens": sum(c.get("prompt_tokens", 0) for c in memory_calls),
        "memory_output_tokens": sum(c.get("output_tokens", 0) for c in memory_calls),
    }
    for key, value in derived.items():
        if key in budget and budget[key] != value:
            errors.append(f"thinker.budget.{key} does not match raw calls")
    depths = {}
    for depth, row in sorted(by_depth.items()):
        depths[depth] = {**row, "accuracy": _ratio(row["correct"], row["total"])}
    return {"depths": depths, "budget": {**dict(budget), **derived}}


def analyze_v5(dream: Mapping[str, Any], thinker: Mapping[str, Any], role_truth_count: int | None = None) -> dict[str, Any]:
    """Validate and summarize two loaded v5 artifacts.

    Raises :class:`V5AnalysisError` on any contract violation.  No result is
    returned for a partial or unsafe artifact, which is the fail-closed rule.
    """
    if not _is_map(dream) or not _is_map(thinker):
        raise V5AnalysisError(["dream and thinker artifacts must be JSON objects"])
    errors: list[str] = []
    if role_truth_count is not None and (
        isinstance(role_truth_count, bool)
        or not isinstance(role_truth_count, int)
        or role_truth_count <= 0
    ):
        errors.append("role_truth_count must be a positive integer")
    unsafe = _unsafe_labels(dream)
    unsafe.extend(_unsafe_labels(thinker, "thinker"))
    if unsafe:
        errors.append("unsafe parent-exact labels present: " + ", ".join(sorted(set(unsafe))))
    condition = _validate_condition(dream, errors)
    compute = _validate_compute(dream, errors)
    records = _validate_generation_provenance(dream, errors)
    hypotheses = dream.get("hypotheses")
    if not isinstance(hypotheses, list):
        hypotheses = []
        errors.append("dream artifact is missing hypotheses")
    _validate_evidence(dream, hypotheses, errors)
    prefixes = _validate_prefixes(dream, records, hypotheses, compute, errors, role_truth_count)
    downstream = _validate_thinker(thinker, errors)
    if errors:
        raise V5AnalysisError(errors)
    warnings = [
        "condition is headline-ineligible and is reported as a ceiling/reference diagnostic",
        "matched_compute_to_v4=false; budgets are not compute-matched to v4",
    ]
    if any(row["candidate_counts"]["overflow"] for row in prefixes):
        warnings.append("overflow candidate lines are disclosed and receive no credit")
    if any(row["retained"]["false_contamination"]["numerator"] for row in prefixes):
        warnings.append("retained claims include false/contaminated claims")
    if not downstream["depths"]:
        warnings.append("thinker artifact contains no D0-D3 traces")
    return {
        "schema_version": 1,
        "valid": True,
        "condition": condition,
        "compute": compute,
        "prefixes": prefixes,
        "downstream": downstream,
        "warnings": warnings,
    }


def analyze_paths(dream_path: str | Path, thinker_path: str | Path, role_truth_count: int | None = None) -> dict[str, Any]:
    return analyze_v5(_load(dream_path), _load(thinker_path), role_truth_count)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dreamladder", help="dreamladder v5 JSON artifact")
    parser.add_argument("thinker", help="thinker JSON artifact")
    parser.add_argument("--role-truth-count", type=int,
                        help="trusted offline role-truth denominator when artifact omits role truth")
    parser.add_argument("--out", help="optional descriptive JSON output path")
    args = parser.parse_args(argv)
    try:
        result = analyze_paths(args.dreamladder, args.thinker, args.role_truth_count)
        code = 0
    except (OSError, json.JSONDecodeError, V5AnalysisError) as exc:
        result = {"schema_version": 1, "valid": False, "errors": list(getattr(exc, "errors", [str(exc)])), "warnings": []}
        code = 2
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        Path(args.out).write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return code


if __name__ == "__main__":
    sys.exit(main())
