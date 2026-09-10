"""Generate the PPC5r7 architecture-change proposal from the r4 graph.

This is proposal-generation tooling only. It performs no PPC implementation,
model, tokenizer, trainer, behavioral, canary, or GPU work.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[4]
ROOT = Path(__file__).resolve().parents[1]
OLD = REPO / "research_loop/changes/chg_20260905_public_pathway_consolidation_v5r4/change.json"
OUT = ROOT / "change.json"


def sha256(path: str) -> str:
    return hashlib.sha256((REPO / path).read_bytes()).hexdigest()


def replace_strings(value):
    if isinstance(value, str):
        return value.replace("PPC5R4", "PPC5R7").replace("PPC5r4", "PPC5r7")
    if isinstance(value, list):
        return [replace_strings(item) for item in value]
    if isinstance(value, dict):
        return {key: replace_strings(item) for key, item in value.items()}
    return value


change = replace_strings(copy.deepcopy(json.loads(OLD.read_text())))
change.update(
    {
        "change_id": "chg_20260905_public_pathway_consolidation_v5r7",
        "title": "Public Pathway Consolidation v5r7: closed typed generator-population instrument",
        "summary": (
            "A closed, typed, generator-population causal instrument for supported "
            "candidate selection, observable every-edge interleaved-response dependence, "
            "frozen DREAM context-policy value, and the total policy effect of "
            "DREAM-guided evidence-to-READ training. It resolves PPC5r6's seventeen "
            "blocking contract defects with one transition DAG, an accepted-constructible "
            "IID life law, per-edge proofs, condition-free runtime projections, exact "
            "rational inference and power, derived acceptance, stage-specific authority, "
            "and an acyclic decision-to-release chain."
        ),
        "system_thesis": (
            "Experience Models should ultimately convert verified lived experience into "
            "prospective cognition. PPC5r7 does not test that flywheel. It tests four "
            "separately identified prerequisites while freezing THINK, DREAM, and ACT and "
            "restricting learning to READ candidate scoring. Success is only a qualified "
            "non-mediational intersection over the accepted, constructible locked-generator "
            "population; learned cognition, continual improvement, compression, parenting, "
            "populations, inheritance, and scaling remain later hypotheses."
        ),
        "state": "proposed",
    }
)

purposes = {
    "AGENTS.md": "Controlling research workflow contract.",
    "research_loop/architecture_intake.py": "Hash-bound intake and authority validator.",
    "research_loop/io.py": "Transitive canonical IO dependency.",
    "research_loop/schemas/architecture_change.schema.json": "Proposal schema.",
    "research_loop/schemas/architecture_interpretation.schema.json": "Interpretation schema.",
    "research_loop/schemas/architecture_critique.schema.json": "Critique schema.",
    "research_loop/schemas/architecture_consensus.schema.json": "Consensus schema.",
    "research_loop/schemas/architecture_human_ratification.schema.json": "Human ratification schema.",
    f"{ROOT.relative_to(REPO)}/human_directive.txt": "Verbatim direction and binding r6-rework provenance.",
    f"{ROOT.relative_to(REPO)}/scope_proposal.json": "Exact proposal-only scope.",
    f"{ROOT.relative_to(REPO)}/protocol.md": "Standalone scientific question, estimand, construction law, and boundaries.",
    f"{ROOT.relative_to(REPO)}/machine_contract.md": "Total public machine, provider, path, DREAM, and SLEEP algorithms.",
    f"{ROOT.relative_to(REPO)}/semantic_validators.md": "Pure cross-field, exact-statistical, and acyclic-DAG validators.",
    f"{ROOT.relative_to(REPO)}/assay_contract.json": "Assay populations, freeze matrix, controls, and accepted-constructible generator law.",
    f"{ROOT.relative_to(REPO)}/analysis_contract.json": "Exact paired, safety, missingness, Holm, and conditional power algorithms.",
    f"{ROOT.relative_to(REPO)}/status_contract.json": "Total status-to-endpoint and shared-DREAM dependency mapping.",
    f"{ROOT.relative_to(REPO)}/visibility_contract.json": "Complete information-flow matrix.",
    f"{ROOT.relative_to(REPO)}/authority_contract.json": "Stage-specific, role-closed authority and release DAG.",
    f"{ROOT.relative_to(REPO)}/claim_dependency_map.json": "Literal candidate-decision, T14, authority, and release map.",
    f"{ROOT.relative_to(REPO)}/object_inventory.json": "Closed durable-artifact inventory.",
    f"{ROOT.relative_to(REPO)}/contracts.schema.json": "Closed typed schemas for every inventoried artifact.",
    f"{ROOT.relative_to(REPO)}/controller_registry.json": "Hash-bound total D1A-D1D controller rows and vocabulary.",
    f"{ROOT.relative_to(REPO)}/transition_cause_registry.json": "Hash-bound exact seven-branch transition lineage registry.",
    f"{ROOT.relative_to(REPO)}/test_contract.json": "Executable T01-T14 stage and coverage obligations.",
    f"{ROOT.relative_to(REPO)}/drafts/build_r7_contract_schema.py": "Nonnormative deterministic generator for repetitive schema, inventory, and controller bytes.",
    f"{ROOT.relative_to(REPO)}/drafts/build_r7_change.py": "Nonnormative deterministic proposal generator.",
    "research_loop/changes/chg_20260905_public_pathway_consolidation_v5r4/consensus.json": "Earlier PPC5r4 rework provenance only; no inherited authority.",
    "research_loop/changes/chg_20260905_public_pathway_consolidation_v5r6/consensus.json": "Immediate binding PPC5r6 rework consensus and seventeen exact successor obligations; no inherited authority.",
    "research_notes/52_public_pathway_consolidation_mechanism.md": "Scientific mechanism framing and assay-to-thesis boundary provenance.",
}
change["context_files"] = [
    {"path": path, "sha256": sha256(path), "purpose": purpose}
    for path, purpose in purposes.items()
]

# The r6 closure adds explicit contract and release nodes without altering the
# already-adjudicated four-assay scientific graph.
object_count = len(json.loads((ROOT / "object_inventory.json").read_text())["objects"])
change["graph_delta"]["nodes"].append(
    {
        "operation": "add",
        "node_id": "CLOSED_TYPED_CONTRACT_UNION",
        "before": "generic or unreachable semantic payload definitions",
        "after": (
            f"{object_count} inventoried top-level object types with inline closed fields, "
            "aligned self hashes, exact role registries at authority boundaries, and no "
            "generic semantic payload reference."
        ),
        "rationale": "Makes proposal semantics executable and independently replayable.",
    }
)
change["graph_delta"]["nodes"].extend([
    {
        "operation": "add", "node_id": "CANDIDATE_DECISION",
        "before": "claim literals emitted by the statistical reducer",
        "after": "claim-blind reducer output followed by one registered literal-only projection",
        "rationale": "Preserves runtime claim blindness while producing auditable candidate decisions.",
    },
    {
        "operation": "add", "node_id": "T14_AUTHORITY_RELEASE_DAG",
        "before": "ambiguous or cyclic replay/result/release ancestry",
        "after": "two predecessor-only cold replays -> one T14 result -> preclaim authority -> release -> optional audit",
        "rationale": "Makes scientific release acyclic and independently replayable.",
    },
])
change["graph_delta"]["edges"].extend([
    {"operation": "add", "edge_id": "REDUCER_TO_CANDIDATE_DECISION", "from": "LIFE_LEVEL_REDUCER", "to": "CANDIDATE_DECISION", "before": "", "after": "Project registered literals only after claim-blind reduction.", "rationale": "Separates statistical decisions from claim text."},
    {"operation": "add", "edge_id": "CANDIDATE_TO_T14_RELEASE", "from": "CANDIDATE_DECISION", "to": "T14_AUTHORITY_RELEASE_DAG", "before": "", "after": "Replay validates candidate decisions before authority and release.", "rationale": "Enforces acyclic scientific release."},
])

# The primary reducer is claim-blind and precedes both cold replays.  It can
# never depend on T14, authority, or release.
for loop in change["loop_delta"]["loops"]:
    if loop["loop_id"] == "EXACT_GENERATOR_POPULATION_REDUCTION":
        loop["trigger"] = "Every prospectively locked endpoint has exactly one typed observation or endpoint-local blocker."
        loop["reads"] = [
            "sealed typed observation membership",
            "typed endpoint outcomes and D1A safety trials",
            "locked margins, null thresholds, ceilings, alpha, and power floor",
        ]
        loop["writes"] = [
            "paired, safety, missingness, assay, Holm, and power receipts",
            "overlap and resource summaries",
            "one claim-blind reducer-output manifest",
        ]
        loop["stop_condition"] = "Emit only claim-blind primary reduction; candidate decisions, T14, authority, and release remain downstream."

# The standalone visibility contract is normative.  Convert its compact matrix
# to the architecture-change schema's exact cell representation.
visibility = json.loads((ROOT / "visibility_contract.json").read_text())
cells = []
for information_id in visibility["information_items"]:
    for stage_id in visibility["stages"]:
        encoded = visibility["matrix"][information_id][stage_id]
        level, reason = encoded.split(":", 1) if ":" in encoded else (encoded, "")
        if not reason.strip():
            reason = {
                "forbidden": "No dependency or influence is permitted.",
                "hidden": "Privileged routing only; absent from serialized ingress and egress.",
                "visible": "Named fields are present directly in the stage ingress.",
                "derived_only": "Only the named allowlisted pure projection may enter.",
            }[level.strip()]
        cells.append({"information_id": information_id, "stage_id": stage_id,
                      "visibility": level.strip(), "reason": reason.strip()})
change["visibility_matrix"] = {
    "stages": visibility["stages"],
    "information_items": visibility["information_items"],
    "cells": cells,
}

# Release literals have one source of truth: the frozen r7 claim map.
claim_map = json.loads((ROOT / "claim_dependency_map.json").read_text())
claim_rows = [*claim_map["claims"], claim_map["intersection"]]
change["claim_delta"] = {
    "claims": [
        {
            "operation": "add",
            "claim_id": row["claim_id"],
            "before": "",
            "after": row["release_text"],
            "evidence_needed": (
                "Exact generic T01 intake history, passing typed T02-T14 evidence, "
                "the registered dependency map, final T14 result, and preclaim authority."
            ),
            "headline_eligible": row["claim_id"] == claim_map["intersection"]["claim_id"],
        }
        for row in claim_rows
    ]
}

change["human_boundary"] = {
    "required": True,
    "decision_owner": "Rohin",
    "decision_question": (
        "If fresh PPC5r7 interpretations, cross-critique, and consensus recommend proceed "
        "with no unresolved concern, do you ratify these exact proposal bytes and only the "
        "isolated deterministic CPU/no-model implementation and dual-static-seal scope in "
        "scope_proposal.json, while leaving every model, tokenizer, embedding, trainer, "
        "behavioral, canary, GPU, and scientific action forbidden until a separate exact "
        "run-lock ratification?"
    ),
    "forbidden_before_approval": [
        "PPC5r7-specific implementation or fixture execution",
        "static sealer execution",
        "model tokenizer or embedding dispatch",
        "LoRA training",
        "behavioral or canary execution",
        "GPU work",
        "scientific claim",
    ],
}

test_contract = json.loads((ROOT / "test_contract.json").read_text())
test_obligations = {row["test_id"]: row for row in test_contract["tests"]}
for test in change["acceptance_tests"]:
    test_id = test["test_id"]
    suffix = test_id.rsplit("_", 1)[1]
    obligation = test_obligations[test_id]
    test["setup"] = obligation["coverage"]
    test["falsifies"] = f"Failure of the complete {test_id} obligation."
    test["evidence_artifact"] = f"ppc5r7_{suffix.lower()}_coverage_receipt.json"
    if suffix == "T01":
        test["evidence_artifact"] = "intake.state.json"
        test["expected"] = (
            "The actual generic consensus lifecycle moves awaiting_consensus to human_required "
            "with ok=true, implementation_authorized=false, and no PPC fixture, TEST_RESULT, "
            "implementation, sealer, model, or GPU ancestor."
        )
        test["required_before"] = "implementation"
    elif suffix == "T14":
        test["required_before"] = "scientific_claim"
        test["expected"] = (
            "Two independent predecessor-only cold replays agree with the five candidate "
            "decisions and emit release_bytes_consumed=false; one final T14 result is then "
            "derived without consuming preclaim authority or release bytes."
        )
    else:
        test["required_before"] = "model_execution"
        test["expected"] = (
            "Two independent post-ratification CPU/no-model implementations produce "
            "byte-identical canonical outputs or the same exact first-failure code over "
            "every materialized branch key before any model-related dispatch."
        )

OUT.write_text(json.dumps(change, indent=2, ensure_ascii=False) + "\n")
print(f"wrote {OUT}")
