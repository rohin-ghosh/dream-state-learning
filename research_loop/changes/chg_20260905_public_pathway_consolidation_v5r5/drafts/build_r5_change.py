"""Generate the PPC5r5 architecture-change proposal from the r4 graph.

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
        return value.replace("PPC5R4", "PPC5R5").replace("PPC5r4", "PPC5r5")
    if isinstance(value, list):
        return [replace_strings(item) for item in value]
    if isinstance(value, dict):
        return {key: replace_strings(item) for key, item in value.items()}
    return value


change = replace_strings(copy.deepcopy(json.loads(OLD.read_text())))
change.update(
    {
        "change_id": "chg_20260905_public_pathway_consolidation_v5r5",
        "title": "Public Pathway Consolidation v5r5: closed typed generator-population instrument",
        "summary": (
            "A closed, typed, generator-population causal instrument for supported "
            "candidate selection, observable every-edge interleaved-response dependence, "
            "frozen DREAM context-policy value, and the total policy effect of "
            "DREAM-guided evidence-to-READ training. It resolves PPC5r4's twelve "
            "blocking contract defects with one transition DAG, an accepted-constructible "
            "IID life law, per-edge proofs, condition-free runtime projections, exact "
            "rational inference and power, derived acceptance, stage-specific authority, "
            "and an acyclic decision-to-release chain."
        ),
        "system_thesis": (
            "Experience Models should ultimately convert verified lived experience into "
            "prospective cognition. PPC5r5 does not test that flywheel. It tests four "
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
    f"{ROOT.relative_to(REPO)}/human_directive.txt": "Verbatim direction and bounded r4-resolution provenance.",
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
    f"{ROOT.relative_to(REPO)}/test_contract.json": "Executable T01-T14 stage and coverage obligations.",
    f"{ROOT.relative_to(REPO)}/drafts/build_r5_contract_schema.py": "Nonnormative deterministic generator for repetitive schema, inventory, and controller bytes.",
    "research_loop/changes/chg_20260905_public_pathway_consolidation_v5r4/consensus.json": "Binding PPC5r4 rework consensus and twelve-blocker provenance only; no inherited authority.",
    "research_notes/52_public_pathway_consolidation_mechanism.md": "Scientific mechanism framing and assay-to-thesis boundary provenance.",
}
change["context_files"] = [
    {"path": path, "sha256": sha256(path), "purpose": purpose}
    for path, purpose in purposes.items()
]

# The r5 closure adds one explicit contract-union node without altering the
# already-adjudicated four-assay scientific graph.
change["graph_delta"]["nodes"].append(
    {
        "operation": "add",
        "node_id": "CLOSED_TYPED_CONTRACT_UNION",
        "before": "generic or unreachable semantic payload definitions",
        "after": (
            "Eighty-five inventoried top-level object types with inline closed fields, "
            "aligned self hashes, exact role registries at authority boundaries, and no "
            "generic semantic payload reference."
        ),
        "rationale": "Makes proposal semantics executable and independently replayable.",
    }
)

change["human_boundary"] = {
    "required": True,
    "decision_owner": "Rohin",
    "decision_question": (
        "If fresh PPC5r5 interpretations, cross-critique, and consensus recommend proceed "
        "with no unresolved concern, do you ratify these exact proposal bytes and only the "
        "isolated deterministic CPU/no-model implementation and dual-static-seal scope in "
        "scope_proposal.json, while leaving every model, tokenizer, embedding, trainer, "
        "behavioral, canary, GPU, and scientific action forbidden until a separate exact "
        "run-lock ratification?"
    ),
    "forbidden_before_approval": [
        "PPC5r5-specific implementation or fixture execution",
        "static sealer execution",
        "model tokenizer or embedding dispatch",
        "LoRA training",
        "behavioral or canary execution",
        "GPU work",
        "scientific claim",
    ],
}

for test in change["acceptance_tests"]:
    test_id = test["test_id"]
    suffix = test_id.rsplit("_", 1)[1]
    test["evidence_artifact"] = f"ppc5r5_{suffix.lower()}_coverage_receipt.json"
    if suffix == "T01":
        test["setup"] = (
            "Generic pre-ratification intake validates every normative source hash, schema "
            "parse, context binding, state edge, scope, and human-evidence shape; no PPC5r5 "
            "implementation or sealer is present."
        )
        test["expected"] = (
            "The already-authorized generic intake implementation emits the exact expected "
            "bytes or typed failure for every enumerated mutation."
        )
        test["required_before"] = "implementation"
    elif suffix == "T14":
        test["required_before"] = "scientific_claim"
    else:
        # architecture_change.schema.json has the older coarse label gpu_run;
        # test_contract.json and authority_contract.json narrow this to PRE_MODEL.
        test["required_before"] = "gpu_run"
        if suffix != "T13":
            test["expected"] = (
                "Two independent post-ratification CPU/no-model implementations produce "
                "byte-identical canonical outputs or the same exact typed failure over the "
                "complete fixture universe before any model-related dispatch."
            )

OUT.write_text(json.dumps(change, indent=2, ensure_ascii=False) + "\n")
print(f"wrote {OUT}")

