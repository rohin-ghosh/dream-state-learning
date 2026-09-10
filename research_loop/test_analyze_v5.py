from __future__ import annotations

from copy import deepcopy

from research_loop.analyze_v5 import V5AnalysisError, analyze_v5


def _generation(stage: str, value: int = 10) -> dict:
    return {
        "stage": stage,
        "seed": 1,
        "prompt_tokens": value,
        "output_tokens": 2,
        "original_prompt_tokens": value,
        "prompt_truncated": False,
        "token_count_source": "model_token_ids",
        "text": f"raw completion for {stage}",
    }


def _claim(parents: list[str], sample: int, *, hits: int = 2) -> dict:
    return {
        "parents": parents,
        "first_sample": sample,
        "hits": hits,
        "n_public_observations": 2,
    }


def fixture_pair() -> tuple[dict, dict]:
    raw_candidates = []
    overflow_candidates = []
    scored = []
    for sample in range(4):
        parents = ["A", "B"] if sample >= 1 else ["A", "C"]
        raw_candidates.append({"sample": sample, "eligible": True, "raw": "candidate"})
        scored.append({"parents": parents, "sample": sample, "hits": 2 if sample >= 1 else 1, "n_obs": 2})
    overflow_candidates.append({"sample": 0, "eligible": False, "reason": "over_candidate_budget"})
    views = []
    for prefix in range(1, 5):
        wrong = _claim(["A", "C"], 0, hits=1)
        good = _claim(["A", "B"], 1)
        proposed = [wrong] + ([good] if prefix >= 2 else [])
        supported = [good] if prefix >= 2 else []
        retained = [dict(wrong, status="contradicted")] + ([dict(good, status="supported")] if prefix >= 2 else [])
        views.append({
            "samples": prefix,
            "raw_lines": prefix,
            "overflow_lines": 1,
            "emitted_candidate_lines": prefix + 1,
            "parsed": prefix,
            "malformed": 0,
            "proposed": proposed,
            "supported": supported,
            "one_mismatch": [wrong],
            "retained": retained,
        })

    hypotheses = [{
        "target": "T",
        "blind_comparison_evidence": [{
            "evidence_id": "target_obs_0", "entity": "fox", "land": "T", "observed_token": "red"
        }],
        "raw_candidates": raw_candidates,
        "overflow_candidates": overflow_candidates,
        "malformed_candidates": [],
        "scored": scored,
    }]
    raw = [_generation("recipes")]
    raw.extend(_generation(f"roles:s{i}") for i in range(4))
    raw.extend(_generation(f"parents:T:s{i}") for i in range(4))
    curve = []
    for prefix, view in enumerate(views, 1):
        parent = {
            "raw_lines_total": prefix,
            "overflow_lines_total": 1,
            "emitted_candidate_lines_total": prefix + 1,
            "parsed_total": prefix,
            "malformed_total": 0,
            "unique_proposed_total": 1 + (prefix >= 2),
            "unique_proposed_true": int(prefix >= 2),
            "targets_with_true_proposed": int(prefix >= 2),
            "supported_total": int(prefix >= 2),
            "supported_true": int(prefix >= 2),
            "retained_total": 1 + (prefix >= 2),
            "retained_true": int(prefix >= 2),
            "by_target": [{"target": "T", "truth": ["A", "B"], **view}],
        }
        roles = {
            "raw_lines_total": prefix,
            "parsed_total": prefix,
            "malformed_total": 0,
            "unique_proposed_total": 1,
            "unique_proposed_true": 1,
            "accepted_total": 1,
            "accepted_true": 1,
        }
        generation_records = raw[: 1 + prefix + prefix]
        curve.append({
            "samples": prefix,
            "parents": parent,
            "roles": roles,
            "budget": {
                "samples": prefix,
                "k_per_target_per_sample": 6,
                "candidate_ceiling_per_target": 6 * prefix,
                "matched_compute_to_v4": False,
                "generation_calls": len(generation_records),
                "prompt_tokens": sum(x["prompt_tokens"] for x in generation_records),
                "output_tokens": sum(x["output_tokens"] for x in generation_records),
            },
        })
    dream = {
        "condition": {
            "id": "task_family_scaffolded_public_evidence_exact_gate_ceiling",
            "headline_eligible": False,
            "task_family_scaffold": True,
            "public_evidence_exact_gate": True,
            "contradicted_fallback_retention": "legacy_ablation_only",
            "offline_truth_in_cognition": False,
        },
        "compute": {"k_per_target_per_sample": 6, "samples": 4,
                    "candidate_ceiling_per_target": 24, "matched_compute_to_v4": False},
        "hypotheses": hypotheses,
        "roles": {"truth": [["cat", "dog"]], "proposals": [
            {"sample": i, "parsed": True, "pair": ["cat", "dog"], "public_check": True}
            for i in range(4)
        ]},
        "audit": {
            "raw": raw,
            "role_discovery_evidence": {
                "policy": "ordinary_source_lands_only", "allowed_lands": ["A", "B", "C"],
                "allowed_evidence_ids": ["source_0"], "excluded_target_lands": ["T"],
                "excluded_target_evidence_ids": ["target_obs_0"],
            },
        },
        "sample_curve": curve,
        "role_recall": 1.0,
    }
    thinker_calls = [
        {"kind": "thinker", "goal": "g0", "prompt_tokens": 3, "output_tokens": 1,
         "token_count_source": "model_token_ids", "raw_completion": "ANSWER: red"},
        {"kind": "memory_model_read", "goal": "g0", "prompt_tokens": 4, "output_tokens": 2,
         "token_count_source": "model_token_ids", "raw_completion": "MEMORY: result"},
    ]
    thinker = {
        "budget": {"thinker_generation_calls": 1, "memory_query_operations": 1,
                   "memory_model_generation_calls": 1, "thinker_prompt_tokens": 3,
                   "thinker_output_tokens": 1, "memory_prompt_tokens": 4,
                   "memory_output_tokens": 2},
        "calls": thinker_calls,
        "traces": [{"goal": "g0", "depth": "D0", "trace": [["MEMORY", "x", "y"], ["ANSWER", "red", ""]],
                    "final": "red", "malformed": False, "ok": True}],
    }
    return dream, thinker


def test_nested_analysis_preserves_raw_numerators_and_downstream_depths():
    dream, thinker = fixture_pair()
    result = analyze_v5(dream, thinker)
    assert [x["prefix"] for x in result["prefixes"]] == [1, 2, 3, 4]
    assert result["prefixes"][0]["candidate_counts"]["actual"] == 1
    assert result["prefixes"][0]["candidate_counts"]["overflow"] == 1
    assert result["prefixes"][1]["target_proposal_recall"] == {"numerator": 1, "denominator": 1, "value": 1.0}
    assert result["prefixes"][3]["supported_precision"]["numerator"] == 1
    assert result["prefixes"][0]["retained"]["false_contamination"]["numerator"] == 1
    assert result["downstream"]["depths"]["D0"]["accuracy"]["numerator"] == 1


def test_contract_failures_are_fail_closed():
    mutations = [
        lambda d, t: d["compute"].update(samples=3),
        lambda d, t: d["sample_curve"][2]["parents"].update(retained_total=0),
        lambda d, t: d["hypotheses"][0]["blind_comparison_evidence"].clear(),
        lambda d, t: d["audit"]["raw"][0].pop("text"),
        lambda d, t: t["calls"][0].pop("raw_completion"),
        lambda d, t: d["condition"].update(retained_parent_exact=True),
    ]
    for mutation in mutations:
        dream, thinker = fixture_pair()
        mutation(dream, thinker)
        try:
            analyze_v5(dream, thinker)
        except V5AnalysisError:
            continue
        raise AssertionError("invalid artifact was accepted")


def test_zero_role_recall_accepts_explicit_offline_denominator():
    dream, thinker = fixture_pair()
    dream["roles"].pop("truth")
    dream.pop("role_recall")
    for row in dream["sample_curve"]:
        row["roles"]["accepted_true"] = 0
    result = analyze_v5(dream, thinker, role_truth_count=30)
    assert result["prefixes"][-1]["roles"]["recall"] == {
        "numerator": 0, "denominator": 30, "value": 0.0
    }


def test_missing_role_truth_denominator_fails_closed_even_at_zero_recall():
    dream, thinker = fixture_pair()
    dream["roles"].pop("truth")
    dream.pop("role_recall")
    for row in dream["sample_curve"]:
        row["roles"]["accepted_true"] = 0
    try:
        analyze_v5(dream, thinker)
    except V5AnalysisError as exc:
        assert any("role truth denominator" in error for error in exc.errors)
    else:
        raise AssertionError("zero-recall artifact without denominator was accepted")


def test_repeated_memory_query_is_priced_as_an_operation():
    dream, thinker = fixture_pair()
    thinker["traces"][0]["trace"].insert(1, ["REPEAT", "x", ""])
    thinker["budget"]["memory_query_operations"] = 2
    result = analyze_v5(dream, thinker)
    assert result["downstream"]["budget"]["memory_query_operations"] == 2
