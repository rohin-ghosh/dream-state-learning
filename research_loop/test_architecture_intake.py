from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path

from research_loop.architecture_intake import (
    IntakeError,
    initialize_intake,
    record_consensus,
    record_critique,
    record_human_ratification,
    record_interpretation,
    validate_change,
    validate_consensus,
)
from research_loop.io import load_json, sha256_file


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def _base(root: Path) -> tuple[Path, dict, dict, dict, dict]:
    context = root / "context.md"
    context.write_text("dream -> memory -> think\n", encoding="utf-8")
    context_ref = {
        "path": "context.md",
        "sha256": sha256_file(context),
        "purpose": "system thesis",
    }
    change = {
        "schema_version": 1,
        "artifact_type": "architecture_change",
        "change_id": "recurrent-dream-1",
        "title": "Recurrent local memory growth",
        "summary": "Let later dreams connect thinker traces to existing memories.",
        "system_thesis": "Intelligence is credited to the complete dream-memory-think loop.",
        "state": "proposed",
        "context_files": [context_ref],
        "graph_delta": {
            "nodes": [
                {
                    "operation": "add",
                    "node_id": "thinker_trace",
                    "before": "",
                    "after": "Temporary goal-conditioned path trace.",
                    "rationale": "A later dream can consolidate a useful attempted path.",
                }
            ],
            "edges": [
                {
                    "operation": "add",
                    "edge_id": "trace_to_dream",
                    "from": "thinker_trace",
                    "to": "dreamer",
                    "before": "",
                    "after": "Eligible only after the outcome is observed.",
                    "rationale": "Supports iterative convergence without answer leakage.",
                }
            ],
        },
        "loop_delta": {
            "loops": [
                {
                    "operation": "modify",
                    "loop_id": "life_loop",
                    "before": "experience -> dream -> think",
                    "after": "experience -> dream -> think -> outcome -> later dream",
                    "trigger": "an episode outcome commits",
                    "reads": ["episodic memory", "prior dream nodes", "thinker trace"],
                    "writes": ["provisional local memory edge"],
                    "stop_condition": "fixed budget or no novel supported local edge",
                    "rationale": "The complete organism can approach structure over iterations.",
                }
            ]
        },
        "claim_delta": {
            "claims": [
                {
                    "operation": "modify",
                    "claim_id": "whole-organism-generalization",
                    "before": "The dreamer independently discovers parent structures.",
                    "after": "The complete loop can construct useful counterfactual paths.",
                    "evidence_needed": "Ablations over recurrent dream, memory substrate, and thinker.",
                    "headline_eligible": False,
                }
            ]
        },
        "visibility_matrix": {
            "information_items": ["lived_rows", "hidden_answer"],
            "stages": ["dream", "think"],
            "cells": [
                {"information_id": "lived_rows", "stage_id": "dream", "visibility": "visible", "reason": "Dreams operate over lived experience."},
                {"information_id": "lived_rows", "stage_id": "think", "visibility": "derived_only", "reason": "Think reads only through the frozen memory interface."},
                {"information_id": "hidden_answer", "stage_id": "dream", "visibility": "forbidden", "reason": "Prevents answer-conditioned memories."},
                {"information_id": "hidden_answer", "stage_id": "think", "visibility": "hidden", "reason": "It is the evaluation target."},
            ],
        },
        "acceptance_tests": [
            {
                "test_id": "no-hidden-answer",
                "kind": "invariant",
                "setup": "Trace every prompt and memory write.",
                "expected": "No hidden answer appears before scoring.",
                "falsifies": "Any pre-score hidden-answer visibility invalidates the run.",
                "evidence_artifact": "visibility_audit.json",
                "required_before": "gpu_run",
            }
        ],
        "human_boundary": {
            "required": True,
            "decision_owner": "principal investigator",
            "decision_question": "Does this factorization test the intended organism?",
            "forbidden_before_approval": ["edit science runner", "launch GPU experiment"],
        },
    }
    change_path = root / "change.json"
    _write(change_path, change)
    interpretation = {
        "schema_version": 1,
        "artifact_type": "architecture_interpretation",
        "interpretation_id": "systems-1",
        "change_id": change["change_id"],
        "perspective": "systems",
        "state": "interpreted",
        "architecture_change_sha256": sha256_file(change_path),
        "context_files": [context_ref],
        "system_thesis_interpretation": "The organism, not one module, owns generalization.",
        "graph_delta_interpretation": "A thinker trace becomes eligible evidence for later local dreaming.",
        "loop_delta_interpretation": "Feedback happens only after a committed outcome.",
        "claim_delta_interpretation": "The claim is weakened from dream-only discovery to whole-loop behavior.",
        "visibility_matrix_interpretation": "The target remains inaccessible before scoring.",
        "acceptance_test_ids_addressed": ["no-hidden-answer"],
        "acceptance_test_interpretation": "The trace audit is a pre-run invariant.",
        "assumptions": ["Thinker traces contain no scorer output."],
        "ambiguities": [
            {"ambiguity_id": "a1", "question": "Which trace fields persist?", "impact": "May change leakage risk."}
        ],
        "disagreements_with_proposal": [
            {
                "disagreement_id": "u1",
                "statement": "Novelty is not a safe self-check criterion.",
                "rationale": "It can reward unsupported elaboration.",
                "proposed_resolution": "Use it only for scheduling and never truth gating.",
            }
        ],
        "human_boundary": {"required": True, "open_questions": ["Is outcome feedback sufficient?"]},
    }
    interpretation_path = root / "interpretation.json"
    _write(interpretation_path, interpretation)
    benchmark_interpretation = copy.deepcopy(interpretation)
    benchmark_interpretation.update(
        {
            "interpretation_id": "benchmark-1",
            "perspective": "benchmark",
            "system_thesis_interpretation": "The paired benchmark must require the recurrent organism.",
            "graph_delta_interpretation": "The graph path must be necessary under shortcut audits.",
            "loop_delta_interpretation": "Outcome-separated recurrence must beat fixed-window controls.",
            "claim_delta_interpretation": "Only an end-to-end delta supports an online-learning claim.",
            "visibility_matrix_interpretation": "Paired worlds must remain indistinguishable without the bridge.",
            "disagreements_with_proposal": [
                {
                    "disagreement_id": "u2",
                    "statement": "The proposed invariant alone is insufficient.",
                    "rationale": "It checks leakage but not pathway necessity.",
                    "proposed_resolution": "Add bridge-removal and shuffled-memory ablations.",
                }
            ],
        }
    )
    benchmark_path = root / "benchmark-interpretation.json"
    _write(benchmark_path, benchmark_interpretation)
    critique = {
        "schema_version": 1,
        "artifact_type": "architecture_critique",
        "critique_id": "reviewer-1",
        "change_id": change["change_id"],
        "state": "critiqued",
        "architecture_change_sha256": sha256_file(change_path),
        "interpretation_hashes": [
            {"interpretation_id": "systems-1", "sha256": sha256_file(interpretation_path)},
            {"interpretation_id": "benchmark-1", "sha256": sha256_file(benchmark_path)},
        ],
        "context_files": [context_ref],
        "strongest_case": "Delayed feedback can join useful paths without demanding one-shot discovery.",
        "reviewed_acceptance_test_ids": ["no-hidden-answer"],
        "concerns": [
            {
                "concern_id": "c1",
                "category": "visibility_leak",
                "severity": "blocking",
                "statement": "A thinker trace may encode the gold answer indirectly.",
                "evidence": "The proposal does not yet define a trace field whitelist.",
                "acceptance_test_ids": ["no-hidden-answer"],
                "resolution_required": True,
            }
        ],
        "visibility_failures": ["Thinker trace is not yet decomposed into fields."],
        "missing_acceptance_tests": ["Ablate post-think dreaming."],
        "human_questions": ["Should failed and successful traces both be eligible?"],
    }
    critique_path = root / "critique.json"
    _write(critique_path, critique)
    consensus = {
        "schema_version": 1,
        "artifact_type": "architecture_consensus",
        "consensus_id": "adjudication-1",
        "change_id": change["change_id"],
        "state": "human_required",
        "architecture_change_sha256": sha256_file(change_path),
        "interpretation_hashes": [
            {"interpretation_id": "systems-1", "sha256": sha256_file(interpretation_path)},
            {"interpretation_id": "benchmark-1", "sha256": sha256_file(benchmark_path)},
        ],
        "critique_sha256": sha256_file(critique_path),
        "recommendation": "proceed_to_implementation",
        "agreements": ["Generalization must be attributed to the full loop."],
        "disagreements": [
            {
                "disagreement_id": "r1",
                "sources": ["systems", "reviewer"],
                "issue": "Whether raw thinker traces may become dream inputs.",
                "positions": [
                    {"actor": "systems", "position": "Permit outcome-bound traces."},
                    {"actor": "reviewer", "position": "Whitelist trace fields first."},
                ],
                "resolution": {
                    "status": "resolved",
                    "rationale": "A field whitelist makes the permission falsifiable.",
                    "selected_position": "Permit only whitelisted, pre-score trace fields.",
                    "required_change": "Specify and audit a trace field whitelist.",
                    "acceptance_test_ids": ["no-hidden-answer"],
                },
            }
        ],
        "concern_dispositions": [
            {
                "concern_id": "c1",
                "status": "accepted",
                "rationale": "Indirect answer visibility is a real blocker.",
                "resolution_id": "r1",
                "required_change": "Add a trace field whitelist.",
            }
        ],
        "upstream_disagreement_dispositions": [
            {
                "disagreement_id": "u1",
                "status": "accepted",
                "rationale": "Novelty must not be treated as truth.",
                "resolution_id": "r1",
            },
            {
                "disagreement_id": "u2",
                "status": "accepted",
                "rationale": "Pathway necessity needs a separate ablation.",
                "resolution_id": "r1",
            }
        ],
        "acceptance_test_dispositions": [
            {
                "test_id": "no-hidden-answer",
                "status": "retained",
                "rationale": "It guards the primary leakage path.",
                "replacement_test_id": "",
            }
        ],
        "human_decision": {
            "required": True,
            "status": "pending",
            "questions": ["Approve the field-whitelisted version for implementation?"],
            "implementation_forbidden": True,
        },
    }
    consensus_path = root / "consensus.json"
    _write(consensus_path, consensus)
    return change_path, interpretation, critique, consensus, {
        "interpretation": interpretation_path,
        "benchmark_interpretation": benchmark_path,
        "critique": critique_path,
        "consensus": consensus_path,
    }


def _record_two_interpretations(root: Path, state_path: Path, paths: dict[str, Path]) -> None:
    record_interpretation(root, state_path, paths["interpretation"])
    record_interpretation(root, state_path, paths["benchmark_interpretation"])


def _advance_to_human(root: Path, state_path: Path, paths: dict[str, Path]) -> None:
    _record_two_interpretations(root, state_path, paths)
    record_critique(root, state_path, paths["critique"])
    record_consensus(root, state_path, paths["consensus"])


def _ratification(root: Path, state_path: Path, consensus_path: Path) -> Path:
    evidence_path = root / "human-approval.txt"
    evidence_path.write_text(
        "Rohin authorizes implementation after the architecture intake.\n",
        encoding="utf-8",
    )
    artifact = {
        "schema_version": 1,
        "artifact_type": "architecture_human_ratification",
        "ratification_id": "rohin-approval-1",
        "change_id": "recurrent-dream-1",
        "state": "human_approved",
        "consensus_sha256": sha256_file(consensus_path),
        "human_required_state_sha256": sha256_file(state_path),
        "ratifier": "Rohin Ghosh",
        "authority_statement": "Principal investigator and project owner.",
        "decision_statement": "Implement the ratified architecture delta and its acceptance tests.",
        "decided_at": "2026-08-31T20:00:00-07:00",
        "authorized_scope": ["CPU acceptance tests", "architecture delta implementation"],
        "forbidden_scope": ["unapproved GPU run", "unreviewed scientific claim"],
        "authorization_evidence": {
            "path": "human-approval.txt",
            "sha256": sha256_file(evidence_path),
            "excerpt": "authorizes implementation",
        },
        "implementation_authorized": True,
    }
    path = root / "ratification.json"
    _write(path, artifact)
    return path


def _canonical_scope_proposal(root: Path) -> Path:
    path = root / "research_loop" / "changes" / "recurrent-dream-1" / "scope_proposal.json"
    _write(
        path,
        {
            "schema_version": 1,
            "change_id": "recurrent-dream-1",
            "state": "proposal_only",
            "human_ratification_required": True,
            "requested_scope": ["CPU acceptance tests", "architecture delta implementation"],
            "forbidden_scope": ["unapproved GPU run", "unreviewed scientific claim"],
            "authorization_effect": "None before exact human ratification.",
        },
    )
    return path


def test_happy_path_stops_at_human_required_even_when_recommendation_is_proceed() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        change_path, _, _, _, paths = _base(root)
        state_path = root / "state.json"
        initialize_intake(root, change_path, state_path)
        _record_two_interpretations(root, state_path, paths)
        record_critique(root, state_path, paths["critique"])
        final = record_consensus(root, state_path, paths["consensus"])
        assert final["phase"] == "human_required"
        assert final["human_required"] is True
        assert final["implementation_authorized"] is False


def test_exact_human_ratification_releases_only_the_authorized_transition() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        change_path, _, _, _, paths = _base(root)
        state_path = root / "state.json"
        initialize_intake(root, change_path, state_path)
        _advance_to_human(root, state_path, paths)
        ratification_path = _ratification(root, state_path, paths["consensus"])
        final = record_human_ratification(root, state_path, ratification_path)
        assert final["phase"] == "human_approved"
        assert final["human_required"] is False
        assert final["implementation_authorized"] is True


def test_canonical_scope_proposal_requires_exact_ratification_scopes() -> None:
    mutations = {
        "authorized_extra": lambda value: value["authorized_scope"].append("extra scope"),
        "authorized_omitted": lambda value: value.__setitem__("authorized_scope", value["authorized_scope"][:1]),
        "authorized_reordered": lambda value: value.__setitem__("authorized_scope", list(reversed(value["authorized_scope"]))),
        "forbidden_extra": lambda value: value["forbidden_scope"].append("extra forbidden scope"),
        "forbidden_omitted": lambda value: value.__setitem__("forbidden_scope", value["forbidden_scope"][:1]),
        "forbidden_reordered": lambda value: value.__setitem__("forbidden_scope", list(reversed(value["forbidden_scope"]))),
    }
    for name, mutate in mutations.items():
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            change_path, _, _, _, paths = _base(root)
            _canonical_scope_proposal(root)
            state_path = root / "state.json"
            initialize_intake(root, change_path, state_path)
            _advance_to_human(root, state_path, paths)
            ratification_path = _ratification(root, state_path, paths["consensus"])
            ratification = load_json(ratification_path)
            mutate(ratification)
            _write(ratification_path, ratification)
            try:
                record_human_ratification(root, state_path, ratification_path)
            except IntakeError as exc:
                assert "scope proposal" in str(exc), name
            else:
                raise AssertionError(f"scope mismatch was accepted: {name}")
            assert load_json(state_path)["phase"] == "human_required"

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        change_path, _, _, _, paths = _base(root)
        _canonical_scope_proposal(root)
        state_path = root / "state.json"
        initialize_intake(root, change_path, state_path)
        _advance_to_human(root, state_path, paths)
        ratification_path = _ratification(root, state_path, paths["consensus"])
        final = record_human_ratification(root, state_path, ratification_path)
        assert final["phase"] == "human_approved"


def test_canonical_scope_proposal_must_have_exact_shape_and_identity() -> None:
    mutations = {
        "missing_field": lambda value: value.pop("authorization_effect"),
        "wrong_type": lambda value: value.__setitem__("requested_scope", "not-a-list"),
        "wrong_change": lambda value: value.__setitem__("change_id", "other-change"),
        "wrong_state": lambda value: value.__setitem__("state", "human_approved"),
    }
    for name, mutate in mutations.items():
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            change_path, _, _, _, paths = _base(root)
            scope_path = _canonical_scope_proposal(root)
            proposal = load_json(scope_path)
            mutate(proposal)
            _write(scope_path, proposal)
            state_path = root / "state.json"
            initialize_intake(root, change_path, state_path)
            _advance_to_human(root, state_path, paths)
            ratification_path = _ratification(root, state_path, paths["consensus"])
            try:
                record_human_ratification(root, state_path, ratification_path)
            except IntakeError as exc:
                assert "canonical scope proposal" in str(exc), name
            else:
                raise AssertionError(f"malformed scope proposal was accepted: {name}")


def test_interpretation_context_rejects_its_mutable_intake_state() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        change_path, interpretation, _, _, paths = _base(root)
        state_path = root / "state.json"
        initialize_intake(root, change_path, state_path)
        mutable_state = root / "research_loop" / "changes" / "recurrent-dream-1" / "intake.state.json"
        _write(mutable_state, {"mutable": True})
        interpretation["context_files"].append(
            {
                "path": "research_loop/changes/recurrent-dream-1/intake.state.json",
                "sha256": sha256_file(mutable_state),
                "purpose": "must not be interpretation context",
            }
        )
        _write(paths["interpretation"], interpretation)
        try:
            record_interpretation(root, state_path, paths["interpretation"])
        except IntakeError as exc:
            assert "mutable intake state" in str(exc)
        else:
            raise AssertionError("interpretation accepted its mutable intake state")


def test_ratification_rejects_stale_consensus_state_and_evidence() -> None:
    mutations = (
        "consensus_sha256", "human_required_state_sha256", "evidence", "excerpt",
    )
    for mutation in mutations:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            change_path, _, _, _, paths = _base(root)
            state_path = root / "state.json"
            initialize_intake(root, change_path, state_path)
            _advance_to_human(root, state_path, paths)
            ratification_path = _ratification(root, state_path, paths["consensus"])
            ratification = load_json(ratification_path)
            if mutation == "evidence":
                (root / "human-approval.txt").write_text("forged\n", encoding="utf-8")
            elif mutation == "excerpt":
                ratification["authorization_evidence"]["excerpt"] = "not present"
                _write(ratification_path, ratification)
            else:
                ratification[mutation] = "0" * 64
                _write(ratification_path, ratification)
            try:
                record_human_ratification(root, state_path, ratification_path)
            except IntakeError as exc:
                assert (
                    "not bound" in str(exc)
                    or "hash mismatch" in str(exc)
                    or "excerpt is absent" in str(exc)
                )
            else:
                raise AssertionError(f"stale human ratification accepted: {mutation}")


def test_cross_critique_requires_two_distinct_interpretation_perspectives() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        change_path, _, _, _, paths = _base(root)
        state_path = root / "state.json"
        initialize_intake(root, change_path, state_path)
        record_interpretation(root, state_path, paths["interpretation"])
        try:
            record_critique(root, state_path, paths["critique"])
        except IntakeError as exc:
            assert "at least two independent interpretations" in str(exc)
        else:
            raise AssertionError("one interpretation reached cross-critique")

        duplicate = load_json(paths["benchmark_interpretation"])
        duplicate["perspective"] = "systems"
        _write(paths["benchmark_interpretation"], duplicate)
        try:
            record_interpretation(root, state_path, paths["benchmark_interpretation"])
        except IntakeError as exc:
            assert "duplicate interpretation perspective" in str(exc)
        else:
            raise AssertionError("duplicate interpretation perspective was accepted")


def test_cross_critique_and_consensus_cannot_drop_an_interpretation() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        change_path, _, critique, consensus, paths = _base(root)
        state_path = root / "state.json"
        initialize_intake(root, change_path, state_path)
        _record_two_interpretations(root, state_path, paths)

        critique["interpretation_hashes"][1] = copy.deepcopy(
            critique["interpretation_hashes"][0]
        )
        _write(paths["critique"], critique)
        try:
            record_critique(root, state_path, paths["critique"])
        except IntakeError as exc:
            assert "duplicate interpretation hash bindings" in str(exc)
        else:
            raise AssertionError("cross-critique dropped an independent interpretation")

        _, _, _, consensus, paths = _base(root)
        consensus["upstream_disagreement_dispositions"] = [
            consensus["upstream_disagreement_dispositions"][0]
        ]
        _write(paths["consensus"], consensus)
        try:
            validate_consensus(
                root, paths["consensus"], change_path,
                [paths["interpretation"], paths["benchmark_interpretation"]],
                paths["critique"],
            )
        except IntakeError as exc:
            assert "every and only interpretation disagreement" in str(exc)
        else:
            raise AssertionError("consensus dropped an interpretation disagreement")


def test_missing_graph_delta_is_rejected_by_schema() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        change_path, *_ = _base(root)
        change = load_json(change_path)
        del change["graph_delta"]
        _write(change_path, change)
        try:
            validate_change(root, change_path)
        except IntakeError as exc:
            assert "graph_delta" in str(exc)
        else:
            raise AssertionError("proposal without graph_delta was accepted")


def test_visibility_matrix_must_be_complete_and_nonduplicated() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        change_path, *_ = _base(root)
        change = load_json(change_path)
        change["visibility_matrix"]["cells"].pop()
        _write(change_path, change)
        try:
            validate_change(root, change_path)
        except IntakeError as exc:
            assert "cartesian product" in str(exc)
        else:
            raise AssertionError("incomplete visibility matrix was accepted")

        _, _, _, _, _ = _base(root)
        change = load_json(change_path)
        change["visibility_matrix"]["cells"].append(
            copy.deepcopy(change["visibility_matrix"]["cells"][0])
        )
        _write(change_path, change)
        try:
            validate_change(root, change_path)
        except IntakeError as exc:
            assert "duplicate" in str(exc)
        else:
            raise AssertionError("duplicate visibility cell was accepted")


def test_context_hash_mismatch_and_root_escape_are_rejected() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        change_path, *_ = _base(root)
        (root / "context.md").write_text("changed\n", encoding="utf-8")
        try:
            validate_change(root, change_path)
        except IntakeError as exc:
            assert "context hash mismatch" in str(exc)
        else:
            raise AssertionError("stale context hash was accepted")

        change_path, *_ = _base(root)
        change = load_json(change_path)
        change["context_files"][0]["path"] = "../outside.md"
        _write(change_path, change)
        try:
            validate_change(root, change_path)
        except IntakeError as exc:
            assert "escapes root" in str(exc)
        else:
            raise AssertionError("root escape was accepted")


def test_cannot_skip_interpretation_or_modify_prior_artifact() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        change_path, _, _, _, paths = _base(root)
        state_path = root / "state.json"
        initialize_intake(root, change_path, state_path)
        try:
            record_critique(root, state_path, paths["critique"])
        except IntakeError as exc:
            assert "at least two independent interpretations" in str(exc)
        else:
            raise AssertionError("critique skipped the interpretation phase")

        change = load_json(change_path)
        change["summary"] = "mutated after intake"
        _write(change_path, change)
        try:
            record_interpretation(root, state_path, paths["interpretation"])
        except IntakeError as exc:
            assert "changed after transition" in str(exc)
        else:
            raise AssertionError("mutated proposal remained valid")


def test_state_cannot_forge_phase_or_artifact_set() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        change_path, _, _, _, paths = _base(root)
        state_path = root / "state.json"
        initialize_intake(root, change_path, state_path)
        state = load_json(state_path)
        state["phase"] = "awaiting_consensus"
        _write(state_path, state)
        try:
            record_critique(root, state_path, paths["critique"])
        except IntakeError as exc:
            assert "artifact set does not match phase" in str(exc)
        else:
            raise AssertionError("forged state phase was accepted")


def test_wrong_source_hash_and_unaddressed_acceptance_test_are_rejected() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        change_path, interpretation, _, _, paths = _base(root)
        state_path = root / "state.json"
        initialize_intake(root, change_path, state_path)
        interpretation["architecture_change_sha256"] = "0" * 64
        _write(paths["interpretation"], interpretation)
        try:
            record_interpretation(root, state_path, paths["interpretation"])
        except IntakeError as exc:
            assert "not bound" in str(exc)
        else:
            raise AssertionError("wrong architecture hash was accepted")

        _, interpretation, _, _, paths = _base(root)
        interpretation["acceptance_test_ids_addressed"] = ["invented-test"]
        _write(paths["interpretation"], interpretation)
        try:
            record_interpretation(root, state_path, paths["interpretation"])
        except IntakeError as exc:
            assert "every and only" in str(exc)
        else:
            raise AssertionError("unaddressed acceptance test was accepted")


def test_consensus_cannot_drop_concern_or_resolution() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        change_path, _, _, consensus, paths = _base(root)
        consensus["concern_dispositions"] = []
        _write(paths["consensus"], consensus)
        try:
            validate_consensus(
                root, paths["consensus"], change_path,
                [paths["interpretation"], paths["benchmark_interpretation"]],
                paths["critique"],
            )
        except IntakeError as exc:
            assert "at least 1 items" in str(exc)
        else:
            raise AssertionError("consensus dropped a blocking concern")

        _, _, _, consensus, paths = _base(root)
        consensus["concern_dispositions"][0]["resolution_id"] = ""
        _write(paths["consensus"], consensus)
        try:
            validate_consensus(
                root, change_path=change_path, path=paths["consensus"],
                interpretation_paths=[
                    paths["interpretation"], paths["benchmark_interpretation"]
                ],
                critique_path=paths["critique"],
            )
        except IntakeError as exc:
            assert "lacks a valid resolution" in str(exc)
        else:
            raise AssertionError("unresolved required concern was accepted")


def test_consensus_cannot_claim_accepted_or_authorize_implementation() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        change_path, _, _, consensus, paths = _base(root)
        consensus["state"] = "accepted"
        consensus["human_decision"]["implementation_forbidden"] = False
        _write(paths["consensus"], consensus)
        try:
            validate_consensus(
                root, paths["consensus"], change_path,
                [paths["interpretation"], paths["benchmark_interpretation"]],
                paths["critique"],
            )
        except IntakeError as exc:
            assert "human_required" in str(exc) or "constant" in str(exc)
        else:
            raise AssertionError("autonomous implementation authorization was accepted")
