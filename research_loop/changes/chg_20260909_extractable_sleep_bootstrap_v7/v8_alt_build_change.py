"""Build an isolated, proposal-only V8 architecture-change candidate.

This builder performs model-free assembly and validation only.  It neither
mutates architecture intake state nor executes models, tokenizers, data,
benchmarks, writers, adapters, checkpoints, CPU/GPU science, claims, release,
or transfer actions.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUTPUT = HERE / "v8_alt_change.json"

INPUTS = {
    "AGENTS.md": "1e3c413f3adbf172c409bc642bbf8242a736b0209461b6a7f81203450772f54e",
    "research_loop/changes/chg_20260909_extractable_sleep_bootstrap_v7/v8_blocker_resolution.md": "ba986cf1b4df614c76e7a21b138f2dd5c1e3b24e023fe59b7e2749cae511bd33",
    "research_loop/changes/chg_20260909_extractable_sleep_bootstrap_v7/v8_integration_requirements.json": "2f8d55096784e33a7a880ac1cf6252f29e613e0ad729ceb5d06499d10a899f6c",
    "research_loop/changes/chg_20260909_extractable_sleep_bootstrap_v7/v8_scientific_core.json": "dc61df6c3947b3ef8a593d3b7ced928d8ceb5070454eb6c1271f0df9f258971d",
    "research_loop/changes/chg_20260909_extractable_sleep_bootstrap_v7/v8_systems_core.json": "cabeb07a18690c10a843f7eacb527d16ed6f5757fba69e78b76f9bf2a0a47c5e",
    "research_loop/changes/chg_20260909_extractable_sleep_bootstrap_v7/change.json": "d69ac7b3207b4eec18af552d968b7a396aa5b39a6bc6290072d14b3812e0cfc9",
    "research_loop/schemas/architecture_change.schema.json": "740356111243a4e55d018243a29f0da89e5cdddd6c9410c5ca0cf766665802d6",
}

PURPOSES = {
    "AGENTS.md": "Binding research-agent operating contract.",
    "research_loop/changes/chg_20260909_extractable_sleep_bootstrap_v7/v8_blocker_resolution.md": "Verbatim V8 directive and blocker resolution; proposal authority only.",
    "research_loop/changes/chg_20260909_extractable_sleep_bootstrap_v7/v8_integration_requirements.json": "Canonical V8 identities, cardinalities, phase consumers, and integration assertions.",
    "research_loop/changes/chg_20260909_extractable_sleep_bootstrap_v7/v8_scientific_core.json": "Exact prospective causal, estimand, label, firewall, and claim core.",
    "research_loop/changes/chg_20260909_extractable_sleep_bootstrap_v7/v8_systems_core.json": "Exact canonical registry, finite DAG, phase lattice, atomicity, and visibility core.",
    "research_loop/changes/chg_20260909_extractable_sleep_bootstrap_v7/change.json": "Complete V7 predecessor graph, loops, and claims preserved except for explicit V8 repairs.",
    "research_loop/schemas/architecture_change.schema.json": "Strict schema used by architecture_intake.validate_change.",
}

REQUIRED_BEFORE = {
    "STATIC_SCHEMA": "implementation",
    "G0_FAKE_RUNTIME": "implementation",
    "G1_IMPLEMENTATION_REVIEW": "model_execution",
    "G2_CPU_DOMAIN": "gpu_run",
    "G3_GPU_SCIENCE": "scientific_claim",
    "G4_CLAIM": "scientific_claim",
}

TEST_KIND = {
    "STATIC_SCHEMA": "invariant",
    "G0_FAKE_RUNTIME": "unit",
    "G1_IMPLEMENTATION_REVIEW": "independent_review",
    "G2_CPU_DOMAIN": "end_to_end",
    "G3_GPU_SCIENCE": "ablation",
    "G4_CLAIM": "independent_review",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(relative: str) -> dict[str, Any]:
    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for key, value in pairs:
            if key in out:
                raise ValueError(f"duplicate JSON key {key!r} in {relative}")
            out[key] = value
        return out

    with (ROOT / relative).open("r", encoding="utf-8") as handle:
        value = json.load(handle, object_pairs_hook=reject_duplicates)
    if not isinstance(value, dict):
        raise ValueError(f"{relative} is not a JSON object")
    return value


def compact(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def check_input_hashes() -> None:
    for relative, expected in INPUTS.items():
        actual = sha256(ROOT / relative)
        if actual != expected:
            raise ValueError(
                f"bound input mismatch for {relative}: expected={expected}, actual={actual}"
            )


def validate_phase_lattice(
    integration: dict[str, Any], science: dict[str, Any], systems: dict[str, Any]
) -> tuple[list[str], list[str], dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    contract = integration["phase_row_contract"]
    families = contract["family_ids_in_order"]
    phase_profiles = contract["phase_profiles_in_order"]
    phases = [profile["phase_id"] for profile in phase_profiles]
    expected_rows = [f"V8_ROW__{family}__{phase}" for family in families for phase in phases]
    expected_receipts = [
        f"R_{family}__{phase}__PASS" for family in families for phase in phases
    ]

    if len(families) != 21 or len(set(families)) != 21:
        raise ValueError("integration family identity/cardinality mismatch")
    if len(phases) != 6 or len(set(phases)) != 6:
        raise ValueError("integration phase identity/cardinality mismatch")
    if len(expected_rows) != 126 or len(set(expected_rows)) != 126:
        raise ValueError("derived row identity/cardinality mismatch")
    if len(expected_receipts) != 126 or len(set(expected_receipts)) != 126:
        raise ValueError("derived receipt identity/cardinality mismatch")

    system_rows = systems["acceptance_lattice"]["rows"]
    science_rows = science["acceptance_obligation_contract"]["phase_rows"]
    if [row["row_id"] for row in system_rows] != expected_rows:
        raise ValueError("systems-core row identities/order do not equal integration contract")
    if [row["receipt_id"] for row in system_rows] != expected_receipts:
        raise ValueError("systems-core receipt identities/order do not equal integration contract")
    if [row["row_id"] for row in science_rows] != expected_rows:
        raise ValueError("scientific-core row identities/order do not equal integration contract")
    if [row["receipt_id"] for row in science_rows] != expected_receipts:
        raise ValueError("scientific-core receipt identities/order do not equal integration contract")

    system_families = [
        family["test_id"] for family in systems["acceptance_lattice"]["families"]
    ]
    science_families = [
        family["family_id"]
        for family in science["acceptance_obligation_contract"]["families"]
    ]
    obligation_families = [
        family["family_id"] for family in integration["acceptance_family_obligations"]
    ]
    if system_families != families or science_families != families or obligation_families != families:
        raise ValueError("acceptance-family equality/order mismatch")

    profile_by_phase = {profile["phase_id"]: profile for profile in phase_profiles}
    system_profiles = {
        profile["phase_id"]: profile
        for profile in systems["acceptance_lattice"]["phase_specs"]
    }
    science_profiles = {
        profile["phase_id"]: profile
        for profile in science["acceptance_obligation_contract"]["phase_profiles"]
    }
    comparable = (
        "producer_action_id",
        "required_nonempty_root_fields",
        "exact_first_downstream_consumer_action_ids",
    )
    for phase in phases:
        if phase not in REQUIRED_BEFORE or phase not in TEST_KIND:
            raise ValueError(f"phase lacks top-level schema mapping: {phase}")
        for key in comparable:
            expected = profile_by_phase[phase][key]
            if system_profiles[phase][key] != expected or science_profiles[phase][key] != expected:
                raise ValueError(f"phase profile mismatch: phase={phase}, field={key}")

    actions = systems["finite_action_dag"]["control_actions"]
    action_by_id = {action["action_id"]: action for action in actions}
    if len(action_by_id) != len(actions):
        raise ValueError("duplicate systems-core action ID")
    action_ids = set(action_by_id)
    first_consumer_map = systems["finite_action_dag"]["first_consumer_map"]
    required_identity_groups = integration["required_v8_object_identities"]
    for group in (
        "phase_producer_action_ids",
        "phase_boundary_action_ids",
        "candidate_and_reporting_action_ids",
        "release_chain_action_ids_in_order",
    ):
        missing_actions = set(required_identity_groups[group]) - action_ids
        if missing_actions:
            raise ValueError(f"required action IDs absent from systems DAG: {sorted(missing_actions)}")
    if systems["integration_contract"]["required_v8_object_identities"] != required_identity_groups:
        raise ValueError("systems-core required object identities do not equal integration contract")
    for phase, profile in profile_by_phase.items():
        if first_consumer_map.get(phase) != profile["exact_first_downstream_consumer_action_ids"]:
            raise ValueError(f"finite DAG first-consumer map mismatch: {phase}")
        producer = action_by_id.get(profile["producer_action_id"])
        manifest_id = f"V8_PHASE_MANIFEST__{phase}"
        if producer is None or manifest_id not in producer["produces_receipt_ids"]:
            raise ValueError(f"phase producer does not produce exact manifest: {phase}")
        for consumer_id in profile["exact_first_downstream_consumer_action_ids"]:
            consumer = action_by_id.get(consumer_id)
            if consumer is None:
                raise ValueError(f"unregistered exact first consumer: {consumer_id}")
            if manifest_id not in consumer["prerequisite_receipt_ids"]:
                raise ValueError(
                    f"consumer {consumer_id} does not directly require {manifest_id}"
                )
            if producer["topological_rank"] >= consumer["topological_rank"]:
                raise ValueError(f"phase producer does not precede consumer: {phase}")

    for system_row, science_row in zip(system_rows, science_rows):
        phase = system_row["phase_id"]
        profile = profile_by_phase[phase]
        exact = {
            "row_id": system_row["row_id"],
            "receipt_id": system_row["receipt_id"],
            "family_id": system_row["family_id"],
            "phase_id": phase,
            "producer_action_id": system_row["producer_action_id"],
            "exact_first_downstream_consumer_action_ids": system_row[
                "exact_first_downstream_consumer_action_ids"
            ],
        }
        for key, value in exact.items():
            if science_row[key] != value:
                raise ValueError(
                    f"scientific/systems row mismatch: {system_row['row_id']} field={key}"
                )
        if system_row["producer_action_id"] != profile["producer_action_id"]:
            raise ValueError(f"wrong row producer: {system_row['row_id']}")
        if (
            system_row["exact_first_downstream_consumer_action_ids"]
            != profile["exact_first_downstream_consumer_action_ids"]
        ):
            raise ValueError(f"wrong row first consumer: {system_row['row_id']}")

    manifests = systems["acceptance_lattice"]["phase_manifests"]
    manifest_by_phase = {manifest["phase_id"]: manifest for manifest in manifests}
    if len(manifest_by_phase) != 6:
        raise ValueError("phase manifest cardinality mismatch")
    for phase in phases:
        manifest = manifest_by_phase[phase]
        selected = [row for row in system_rows if row["phase_id"] == phase]
        if manifest["row_count"] != 21 or len(selected) != 21:
            raise ValueError(f"phase row count mismatch: {phase}")
        if manifest["expected_row_ids"] != [row["row_id"] for row in selected]:
            raise ValueError(f"manifest row equality mismatch: {phase}")
        if manifest["expected_receipt_ids"] != [row["receipt_id"] for row in selected]:
            raise ValueError(f"manifest receipt equality mismatch: {phase}")
        if manifest["producer_action_ids"] != [profile_by_phase[phase]["producer_action_id"]]:
            raise ValueError(f"manifest producer equality mismatch: {phase}")
        if (
            manifest["first_consumer_action_ids"]
            != profile_by_phase[phase]["exact_first_downstream_consumer_action_ids"]
        ):
            raise ValueError(f"manifest consumer equality mismatch: {phase}")

    return expected_rows, expected_receipts, profile_by_phase, action_by_id


def build_acceptance_tests(
    integration: dict[str, Any],
    science: dict[str, Any],
    systems: dict[str, Any],
    expected_rows: list[str],
    expected_receipts: list[str],
) -> list[dict[str, Any]]:
    obligations = {
        item["family_id"]: item["must_falsify"]
        for item in integration["acceptance_family_obligations"]
    }
    families = {
        item["family_id"]: item
        for item in science["acceptance_obligation_contract"]["families"]
    }
    tests: list[dict[str, Any]] = []
    for row in systems["acceptance_lattice"]["rows"]:
        phase = row["phase_id"]
        manifest_id = f"V8_PHASE_MANIFEST__{phase}"
        binding = {
            "artifact_class": "ACCEPTANCE_TEST_PHASE_ROW_RECEIPT",
            "row_id": row["row_id"],
            "receipt_id": row["receipt_id"],
            "family_id": row["family_id"],
            "phase_id": phase,
            "v8_change_root_slot": row["v8_change_root_slot"],
            "registry_root_slot": row["registry_root_slot"],
            "action_dag_root_slot": row["action_dag_root_slot"],
            "subject_root_slots": row["subject_root_slots"],
            "input_root_slots": row["input_root_slots"],
            "fixture_root_slots": row["fixture_root_slots"],
            "implementation_root_slots": row["implementation_root_slots"],
            "result_root_slots": row["result_root_slots"],
            "pass_fail_required_enum": row["pass_fail_required_enum"],
            "producer_action_id": row["producer_action_id"],
            "reviewer_identity_requirement": row["reviewer_identity_requirement"],
            "review_root_requirement": row["review_root_requirement"],
            "expiry_policy": row["expiry_policy"],
            "replay_policy": row["replay_policy"],
            "required_typed_evidence_types": row["required_typed_evidence_types"],
            "prospective_state": row["prospective_state"],
            "exact_first_downstream_consumer_action_ids": row[
                "exact_first_downstream_consumer_action_ids"
            ],
        }
        tests.append(
            {
                "test_id": row["row_id"],
                "kind": TEST_KIND[phase],
                "setup": (
                    families[row["family_id"]]["requirement"]
                    + " Exact prospective row binding: "
                    + compact(binding)
                ),
                "expected": (
                    f"Future producer {row['producer_action_id']} may issue only receipt "
                    f"{row['receipt_id']} under ACCEPTANCE_TEST_PHASE_ROW_RECEIPT_V1; "
                    f"{manifest_id} must equality-bind all and only its 21 canonical child "
                    "receipts before exactly the listed first-consumer actions. This proposal "
                    "asserts no pass and produces no receipt."
                ),
                "falsifies": (
                    obligations[row["family_id"]]
                    + " Also falsifies any missing, duplicate, extra, aliased, stale, failed, "
                    "wrong-phase/root/producer/reviewer/consumer, expired, or replayed row."
                ),
                "evidence_artifact": compact(
                    {
                        "prospective_receipt_id": row["receipt_id"],
                        "phase_manifest_id": manifest_id,
                        "state": "UNPRODUCED_UNEVALUATED",
                    }
                ),
                "required_before": REQUIRED_BEFORE[phase],
            }
        )

    if [test["test_id"] for test in tests] != expected_rows:
        raise ValueError("top-level tests do not exactly materialize canonical row IDs")
    encoded_receipts = [
        json.loads(test["evidence_artifact"])["prospective_receipt_id"] for test in tests
    ]
    if encoded_receipts != expected_receipts:
        raise ValueError("top-level tests do not exactly materialize canonical receipt IDs")
    expected_counts = {
        "implementation": 42,
        "model_execution": 21,
        "gpu_run": 21,
        "scientific_claim": 42,
    }
    if Counter(test["required_before"] for test in tests) != expected_counts:
        raise ValueError("phase-correct required_before distribution mismatch")
    return tests


def make_visibility(
    systems: dict[str, Any], action_by_id: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    registry = systems["canonical_registry_source"]
    lattice = systems["acceptance_lattice"]
    actions = systems["finite_action_dag"]["control_actions"]
    # The systems core's observer sentence requires every registered principal,
    # every registered source, and the declared external human observer.  The
    # union is necessary because some source principals also own DAG actions.
    stages = list(
        dict.fromkeys(
            list(registry["registered_principals"])
            + [source["source_id"] for source in registry["registered_sources"]]
            + ["EXTERNAL_HUMAN_OBSERVER"]
        )
    )
    if len(stages) != len(set(stages)):
        raise ValueError("duplicate visibility principal")
    unresolved_action_principals = {action["principal_id"] for action in actions} - set(stages)
    if unresolved_action_principals:
        raise ValueError(
            f"action principals absent from principal/source observer union: {sorted(unresolved_action_principals)}"
        )

    base: set[str] = set(stages)
    base.update(source["source_id"] for source in registry["registered_sources"])
    base.update(item["lifetime_id"] for item in registry["lifetime_classes"])
    for operation in registry["operations"]:
        base.update(
            [
                operation["operation"],
                operation["request_schema_id"],
                operation["result_schema_id"],
            ]
        )
    for artifact in registry["artifact_definitions"]:
        base.update([artifact["artifact_class"], artifact["payload_schema_id"]])
    artifact_classes = [artifact["artifact_class"] for artifact in registry["artifact_definitions"]]
    if len(artifact_classes) != len(set(artifact_classes)):
        raise ValueError("duplicate canonical artifact class")
    base.update(item["schema_id"] for item in registry["schema_definitions"])
    base.update(family["test_id"] for family in lattice["families"])
    base.update(row["row_id"] for row in lattice["rows"])
    base.update(row["receipt_id"] for row in lattice["rows"])
    base.update(manifest["manifest_id"] for manifest in lattice["phase_manifests"])
    base.update(f"ACTION_KIND__{kind}" for kind in systems["finite_action_dag"]["protected_action_kinds"])

    generated_capabilities: dict[str, str] = {}
    receipt_producer_action: dict[str, str] = {}
    for action in actions:
        base.add(action["action_id"])
        base.update(action["prerequisite_receipt_ids"])
        base.update(action["produces_receipt_ids"])
        for receipt in action["produces_receipt_ids"]:
            prior = receipt_producer_action.setdefault(receipt, action["action_id"])
            if prior != action["action_id"] and action_by_id[prior]["principal_id"] != action["principal_id"]:
                raise ValueError(f"receipt has conflicting action principals: {receipt}")
        for receipt in action["prerequisite_receipt_ids"]:
            capability = f"CAPABILITY__{action['action_id']}__CONSUME__{receipt}"
            generated_capabilities[capability] = action["principal_id"]
            base.add(capability)
        for receipt in action["produces_receipt_ids"]:
            capability = f"CAPABILITY__{action['action_id']}__PRODUCE__{receipt}"
            generated_capabilities[capability] = action["principal_id"]
            base.add(capability)

    phase_manifest_ids = {manifest["manifest_id"] for manifest in lattice["phase_manifests"]}
    referenced_action_products = {
        receipt
        for action in actions
        for field in ("prerequisite_receipt_ids", "produces_receipt_ids")
        for receipt in action[field]
    }
    unresolved_products = referenced_action_products - set(artifact_classes) - phase_manifest_ids
    if unresolved_products:
        raise ValueError(f"unregistered action product: {sorted(unresolved_products)}")

    generated_bridges: dict[str, str] = {}
    for action in actions:
        for receipt in action["prerequisite_receipt_ids"]:
            producer_action = receipt_producer_action.get(receipt)
            if producer_action is None:
                continue
            bridge = f"BRIDGE__{producer_action}__TO__{action['action_id']}__{receipt}"
            generated_bridges[bridge] = action["principal_id"]
            base.add(bridge)

    channels = systems["visibility"]["channels"]
    if channels != ["value", "count", "order", "timing", "cache", "retry", "error"]:
        raise ValueError("visibility channel vocabulary/order mismatch")
    information_items = [
        f"UNIVERSE__{item}__{channel}" for item in sorted(base) for channel in channels
    ]
    if len(information_items) != len(set(information_items)):
        raise ValueError("duplicate channelized universe item")

    roles: dict[tuple[str, str], set[str]] = defaultdict(set)

    def grant(principal: str, item: str, role: str) -> None:
        if principal not in stages:
            return
        if item not in base:
            raise ValueError(f"visibility grant references unknown item: {item}")
        roles[(principal, item)].add(role)

    for principal in stages:
        grant(principal, principal, "NARROW_OBSERVER")
    for source in registry["registered_sources"]:
        grant(source["source_id"], source["source_id"], "PRODUCER")
    for item in registry["lifetime_classes"]:
        grant("G0_REGISTRY_GENERATOR", item["lifetime_id"], "PRODUCER")
    for operation in registry["operations"]:
        grant("G0_REGISTRY_GENERATOR", operation["operation"], "PRODUCER")
        grant("G0_REGISTRY_GENERATOR", operation["request_schema_id"], "PRODUCER")
        grant("G0_REGISTRY_GENERATOR", operation["result_schema_id"], "PRODUCER")
    for artifact in registry["artifact_definitions"]:
        grant(artifact["sole_producer_id"], artifact["artifact_class"], "PRODUCER")
        grant("G0_REGISTRY_GENERATOR", artifact["payload_schema_id"], "PRODUCER")
    for schema in registry["schema_definitions"]:
        grant("G0_REGISTRY_GENERATOR", schema["schema_id"], "PRODUCER")
    for family in lattice["families"]:
        grant("G0_PHASE_RECEIPT_LEDGER", family["test_id"], "NARROW_OBSERVER")
    for row in lattice["rows"]:
        producer_principal = action_by_id[row["producer_action_id"]]["principal_id"]
        grant(producer_principal, row["row_id"], "PRODUCER")
        grant(producer_principal, row["receipt_id"], "PRODUCER")
    for action in actions:
        principal = action["principal_id"]
        grant(principal, action["action_id"], "PRODUCER")
        for receipt in action["prerequisite_receipt_ids"]:
            grant(principal, receipt, "CONSUMER")
        for receipt in action["produces_receipt_ids"]:
            grant(principal, receipt, "PRODUCER")
    for capability, principal in generated_capabilities.items():
        grant(principal, capability, "CONSUMER")
    for bridge, principal in generated_bridges.items():
        grant(principal, bridge, "CONSUMER")

    for capability, principal in generated_capabilities.items():
        visible = [stage for stage in stages if roles.get((stage, capability))]
        if visible != [principal]:
            raise ValueError(f"capability does not have exactly one visible consumer: {capability}")

    cells: list[dict[str, str]] = []
    role_order = ("PRODUCER", "CONSUMER", "NARROW_OBSERVER")
    for item in sorted(base):
        for channel in channels:
            information_id = f"UNIVERSE__{item}__{channel}"
            for stage in stages:
                exact_roles = roles.get((stage, item), set()) if channel == "value" else set()
                role = next((candidate for candidate in role_order if candidate in exact_roles), None)
                if role is None:
                    visibility = "forbidden"
                    reason = "FORBIDDEN: no exact edge; direct and derived channel access denied."
                else:
                    visibility = "visible"
                    reason = f"{role}: exact system-core identity or edge."
                cells.append(
                    {
                        "information_id": information_id,
                        "stage_id": stage,
                        "visibility": visibility,
                        "reason": reason,
                    }
                )

    expected_cell_count = len(information_items) * len(stages)
    if len(cells) != expected_cell_count:
        raise ValueError("visibility matrix cardinality mismatch")
    if len({(cell["information_id"], cell["stage_id"]) for cell in cells}) != len(cells):
        raise ValueError("visibility matrix pair duplication")
    return {
        "information_items": information_items,
        "stages": stages,
        "cells": cells,
    }


def sanitize_v7_text(text: str) -> str:
    replacements = {
        "Teachability T": "The T feedback-to-child-computation rendering",
        "learning-readiness": "the complete T-versus-D rendering contrast",
        "Child receptivity": "Immediate selective-advice-use and entry competence",
        "R_MATCHED_SOLO_RESOURCE_OPPORTUNITY_FROZEN": "MATCHED_SOLO_RESOURCE_OPPORTUNITY_RECEIPT",
        "9c44fe870c56f3009b08512d48175c50a1378beeeebc378a7cfff2e89548c94d": INPUTS[
            "research_loop/changes/chg_20260909_extractable_sleep_bootstrap_v7/v8_systems_core.json"
        ],
        "d176787d89784b54ed0fa65e47d0f08521835d49d4486c9e317e08ce64e3e6ca": INPUTS[
            "research_loop/changes/chg_20260909_extractable_sleep_bootstrap_v7/v8_systems_core.json"
        ],
        "defines 98 single-consumer capabilities, 53 artifact classes, 63 explicit bridges": "canonically defines generated single-consumer capabilities and bridges from 146 artifact classes and 29 control actions",
        "gates 44 actions": "defines 29 explicit control actions and a sealed finite per-invocation expansion",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def build_graph(
    v7: dict[str, Any], visibility: dict[str, Any], systems: dict[str, Any]
) -> dict[str, list[dict[str, Any]]]:
    nodes: list[dict[str, Any]] = []
    for inherited in v7["graph_delta"]["nodes"]:
        after = sanitize_v7_text(inherited["after"])
        nodes.append(
            {
                "operation": "modify",
                "node_id": inherited["node_id"],
                "before": inherited["after"],
                "after": after
                + " V8 preserves this node under the exact bound scientific and systems cores.",
                "rationale": "Preserve the V7 topology while binding the V8 blocker repairs and narrow labels.",
            }
        )

    nodes.extend(
        [
            {
                "operation": "add",
                "node_id": "V8_CANONICAL_SCIENTIFIC_CORE",
                "before": "",
                "after": (
                    "The exact bound scientific-core bytes are authoritative for the three-function "
                    "organism, D/T by absent/fixed primary design, separate M0 diagnostic and adaptive "
                    "extension, Delta_R/Delta_F/Delta_E, waking-only repetition, deferred contracts, "
                    "entry/headroom gates, claim ladder, and nonmechanistic labels."
                ),
                "rationale": "No generated summary may widen the causal object or claim vocabulary.",
            },
            {
                "operation": "add",
                "node_id": "V8_CANONICAL_SYSTEMS_CORE",
                "before": "",
                "after": (
                    "The exact bound systems-core bytes are the single source for registry objects, "
                    "producer/lifetime/schema closure, finite action instances, atomic candidate closure, "
                    "PROMOTE_CAS_ATOMIC, split evaluation, release ordering, phase rows, and visibility."
                ),
                "rationale": "Regeneration replaces hand-patched V7 registry and DAG products.",
            },
            {
                "operation": "add",
                "node_id": "V8_ACCEPTANCE_PHASE_LATTICE",
                "before": "V7 exposed only 21 top-level family tests.",
                "after": (
                    "Exactly 126 unique prospective rows and receipts instantiate 21 inherited families "
                    "across STATIC_SCHEMA, G0_FAKE_RUNTIME, G1_IMPLEMENTATION_REVIEW, G2_CPU_DOMAIN, "
                    "G3_GPU_SCIENCE, and G4_CLAIM. Six manifests equality-bind 21 child receipts each "
                    "before their exact registered first consumers."
                ),
                "rationale": "Phase evidence must be constructible, test-specific, and nonaliased.",
            },
            {
                "operation": "add",
                "node_id": "WHOLE_SYSTEM_VISIBILITY_MANIFEST",
                "before": "V7 visibility did not cover the complete systems universe or covert channels.",
                "after": (
                    f"This proposal materializes {len(visibility['information_items'])} channelized "
                    f"information identities by {len(visibility['stages'])} exact registered principals "
                    f"for {len(visibility['cells'])} unique cells. The base universe is regenerated from "
                    "actual registry, schema, operation, artifact, action, row, receipt, manifest, "
                    "capability, bridge, and protected-action-kind identities in the bound systems core."
                ),
                "rationale": "Every value/count/order/timing/cache/retry/error pair is explicit and defaults closed.",
            },
        ]
    )

    edges: list[dict[str, Any]] = []
    for inherited in v7["graph_delta"]["edges"]:
        edges.append(
            {
                "operation": "modify",
                "edge_id": inherited["edge_id"],
                "from": inherited["from"],
                "to": inherited["to"],
                "before": inherited["after"],
                "after": sanitize_v7_text(inherited["after"])
                + " The exact V8 registry, finite DAG, and visibility cells govern this edge.",
                "rationale": "Preserve the V7 causal edge while closing V8 producer, phase, and channel obligations.",
            }
        )
    edges.extend(
        [
            {
                "operation": "add",
                "edge_id": "V8_SCIENCE_TO_SYSTEMS_EQUALITY",
                "from": "V8_CANONICAL_SCIENTIFIC_CORE",
                "to": "V8_CANONICAL_SYSTEMS_CORE",
                "before": "",
                "after": "Family, phase, row, receipt, producer, and first-consumer identities must match exactly; no alias or prose-only prerequisite is accepted.",
                "rationale": "Scientific obligations and executable gates must name identical objects.",
            },
            {
                "operation": "add",
                "edge_id": "V8_SYSTEMS_TO_VISIBILITY_CARTESIAN_PRODUCT",
                "from": "V8_CANONICAL_SYSTEMS_CORE",
                "to": "WHOLE_SYSTEM_VISIBILITY_MANIFEST",
                "before": "",
                "after": "Registry and finite-DAG IDs deterministically generate the channelized information universe and its exact principal Cartesian product.",
                "rationale": "No ambient object, action, result, or covert channel remains outside the matrix.",
            },
            {
                "operation": "add",
                "edge_id": "V8_PHASE_MANIFESTS_TO_EXACT_FIRST_CONSUMERS",
                "from": "V8_ACCEPTANCE_PHASE_LATTICE",
                "to": "FIRST_AFFECTED_ACTION_REGISTRY",
                "before": "",
                "after": "Each phase producer precedes and produces the exact manifest directly required by every and only declared first-consumer action.",
                "rationale": "Dynamic evidence is never demanded before its producer exists.",
            },
        ]
    )
    if len({node["node_id"] for node in nodes}) != len(nodes):
        raise ValueError("duplicate graph node ID")
    if len({edge["edge_id"] for edge in edges}) != len(edges):
        raise ValueError("duplicate graph edge ID")
    return {"nodes": nodes, "edges": edges}


def build_loops(
    v7: dict[str, Any], systems: dict[str, Any]
) -> dict[str, list[dict[str, Any]]]:
    io_by_loop = {
        "SLEEP_COMPILE_WRITE_COMMIT": (
            [
                "CHILD_GROUNDED_TRACE",
                "PUBLIC_OBSERVATION",
                "FROZEN_SUPPORT_RESOLVER_CONTRACT",
                "FROZEN_CUMULATIVE_COVERAGE_DOSE_CONTRACT",
                "FROZEN_SLEEP_WRITER_CONTRACT",
                "IMMUTABLE_BIRTH_ARTIFACT",
                "ZERO_EFFECTIVE_DELTA_INITIALIZER",
                "ACTION_INSTANCE_MANIFEST",
            ],
            [
                "ELIGIBLE_CHILD_LIFE_EVIDENCE",
                "CANDIDATE_CONSTRUCTION_TRACE",
                "CANDIDATE_CLOSURE_MANIFEST",
                "SEALED_CANDIDATE_DESCRIPTOR",
            ],
        ),
        "BOOTSTRAP_BUILD_AND_BIRTH": (
            ["STATIC_BOOTSTRAP_SPEC", "FROZEN_M0", "FROZEN_BOOTSTRAP_RENDERING_CONTROL_CONTRACT"],
            ["PAIRED_BOOTSTRAP_CORPUS", "IMMUTABLE_BIRTH_ARTIFACT", "BOOTSTRAP_AUDIT_RECEIPT"],
        ),
        "PARENT_REPETITION_AND_FADE": (
            [
                "FIXED_LESSON_TABLE",
                "FIXED_SCHEDULE_CURSOR",
                "ADAPTIVE_PARENT_POLICY_CONTRACT",
                "REPETITION_ENACTMENT_CONTRACT",
                "PUBLIC_OBSERVATION",
            ],
            [
                "FIXED_LIVE_PARENT_MESSAGE",
                "FIXED_PARENT_AUDIT_EVENT",
                "ADAPTIVE_LIVE_PARENT_MESSAGE",
                "ADAPTIVE_PARENT_AUDIT_EVENT",
                "CHILD_GROUNDED_TRACE",
            ],
        ),
        "SLEEP_CADENCE_EVALUATION": (
            ["ACTION_INSTANCE_MANIFEST", "ACTIVE_WEIGHT_ARTIFACT", "PUBLIC_OBSERVATION", "FROZEN_SCIENTIFIC_ANALYSIS_PACKET"],
            ["EXAM_TRANSCRIPT", "SCIENTIFIC_SCORE_RECORD", "SCIENTIFIC_REPORT"],
        ),
        "CANDIDATE_PRESERVATION_AND_PROMOTION": (
            ["CANDIDATE_CLOSURE_MANIFEST", "STAGED_CANDIDATE_DESCRIPTOR", "FROZEN_PRESERVATION_PANEL", "PROMOTION_VERDICT"],
            ["PRESERVATION_EVIDENCE", "PROMOTION_TRANSACTION_RECEIPT", "PROMOTE_CAS_RESULT"],
        ),
        "DISPOSABLE_SCIENTIFIC_EVALUATION": (
            ["PUBLIC_OBSERVATION", "ACTIVE_WEIGHT_ARTIFACT", "HIDDEN_EVALUATION_TRUTH", "FROZEN_SCIENTIFIC_ANALYSIS_PACKET"],
            ["EXAM_TRANSCRIPT", "SCIENTIFIC_SCORE_RECORD", "SCIENTIFIC_REPORT", "REPORT_BINDING_RECEIPT"],
        ),
        "AUDIT_EXTERNAL_AUTHORITY_AND_RELEASE": (
            [
                "DECLARED_DEPENDENCY_MANIFEST",
                "DISPATCHER_MANIFEST",
                "SUPPORT_TAINT_RECEIPT",
                "CONSTRUCTOR_TAINT_RECEIPT",
                "EXTERNAL_HUMAN_AUTHORIZATION",
                "RELEASE_TARGET_ARTIFACT",
            ],
            ["BLINDNESS_AUDIT_ATTESTATION", "LINEAGE_AUDIT_ATTESTATION", "AUTHORITY_VERDICT", "RELEASE_RECEIPT"],
        ),
    }
    loops: list[dict[str, Any]] = []
    for inherited in v7["loop_delta"]["loops"]:
        reads, writes = io_by_loop[inherited["loop_id"]]
        loops.append(
            {
                "operation": "modify",
                "loop_id": inherited["loop_id"],
                "before": inherited["after"],
                "after": sanitize_v7_text(inherited["after"])
                + " V8 binds every invocation to the finite action manifest, exact phase receipts, and canonical registry.",
                "trigger": sanitize_v7_text(inherited["trigger"]),
                "reads": reads,
                "writes": writes,
                "stop_condition": sanitize_v7_text(inherited["stop_condition"]),
                "rationale": sanitize_v7_text(inherited["rationale"]),
            }
        )
    registered_artifacts = {
        artifact["artifact_class"]
        for artifact in systems["canonical_registry_source"]["artifact_definitions"]
    }
    loop_references = {
        reference for loop in loops for field in ("reads", "writes") for reference in loop[field]
    }
    if not loop_references <= registered_artifacts:
        raise ValueError(
            f"loop references absent from systems registry: {sorted(loop_references - registered_artifacts)}"
        )
    return {"loops": loops}


def build_claims() -> dict[str, list[dict[str, Any]]]:
    return {
        "claims": [
            {
                "operation": "retire",
                "claim_id": "C_V1_NATIVE_WRITER_CERTIFIED",
                "before": "R2 and the write swarm certify the intended native response-masked writer.",
                "after": "Old-writer and dose-confounded observations remain exploratory and confer no V8 credit.",
                "evidence_needed": "No successor credit; retain the prior audit record only.",
                "headline_eligible": False,
            },
            {
                "operation": "modify",
                "claim_id": "C_EXPERIENCE_EXTRACTABLE_AND_USABLE",
                "before": "V7 proposed a conditional extraction-and-use claim.",
                "after": "Only after joint powered evidence, personal SLEEP may be described as making the child's eligible grounded experience extractable and usable within the frozen task-and-cue scope.",
                "evidence_needed": "Powered source fit, held-out extraction, fresh homologous native action without textual retrieval, adapter-off, deranged, wrong-life, replay/filler, provenance, preservation, interface, contamination, intervals, multiplicity, missingness, and safety evidence plus G4 authority.",
                "headline_eligible": True,
            },
            {
                "operation": "retire",
                "claim_id": "C_BOOTSTRAP_IMMEDIATE_RECEPTIVITY",
                "before": "V7 used an immediate-receptivity claim identifier and conditional conferred language.",
                "after": "Retired in favor of the complete-rendering, nonmechanistic Delta_R claim identifier.",
                "evidence_needed": "No evidence can rescue the overbroad identifier; use the separately added narrow successor claim.",
                "headline_eligible": False,
            },
            {
                "operation": "add",
                "claim_id": "C_BOOTSTRAP_IMMEDIATE_SELECTIVE_ADVICE_USE_INTERACTION",
                "before": "",
                "after": "Only after powered Delta_R evidence, report that the complete T rendering changes the immediate correct-versus-none advice effect relative to the complete D rendering. No intrinsic mechanism is identified.",
                "evidence_needed": "Powered independent roots; disposable D/T correct, none, irrelevant, and wrong advice clones before personal SLEEP; separate D/T/M0 competence, nondamage, ceiling, headroom, equivalence/noninferiority gates; intervals, multiplicity, missingness, safety, and G4 authority.",
                "headline_eligible": False,
            },
            {
                "operation": "retire",
                "claim_id": "C_BOOTSTRAP_FIXED_CURRICULUM_DEVELOPMENTAL_AUC_INTERACTION",
                "before": "V7 used a fixed-curriculum developmental-AUC claim identifier.",
                "after": "Retired in favor of the exact birth-by-fixed-parent total-regime label.",
                "evidence_needed": "No successor credit under this identifier; use the separately added Delta_F claim.",
                "headline_eligible": False,
            },
            {
                "operation": "add",
                "claim_id": "C_BOOTSTRAP_FIXED_TOTAL_REGIME_INTERACTION",
                "before": "",
                "after": "Only after powered Delta_F evidence, report a birth-by-fixed-parent total-regime interaction over the entry-normalized developmental performance curve; do not call it parenting alone, a repetition effect, mediation, or intrinsic learning rate.",
                "evidence_needed": "Powered D/T by absent/fixed independent-root factorial; ages 0,8,16,24,32; exogenous messages at 1,9,17,25; matched opportunity; raw curves; capacity ITT; intervals, multiplicity, missingness, safety, and G4 authority.",
                "headline_eligible": False,
            },
            {
                "operation": "retire",
                "claim_id": "C_BOOTSTRAP_ADAPTIVE_PACKAGE_DEVELOPMENTAL_AUC_INTERACTION",
                "before": "V7 used an adaptive-package developmental-AUC claim identifier.",
                "after": "Retired in favor of the exact separately randomized birth-by-adaptive-parent total-regime label.",
                "evidence_needed": "No successor credit under this identifier; use the separately added Delta_E claim.",
                "headline_eligible": False,
            },
            {
                "operation": "add",
                "claim_id": "C_BOOTSTRAP_ADAPTIVE_TOTAL_REGIME_INTERACTION",
                "before": "",
                "after": "Only after separately powered Delta_E evidence, report a birth-by-adaptive-parent total-regime interaction over the entry-normalized developmental performance curve; do not pool it with the fixed factorial or claim parenting alone, repetition efficacy, mediation, or intrinsic learning rate.",
                "evidence_needed": "Separately randomized D/T by absent/adaptive roots under the frozen policy, matched opportunity, complete effort/information records, raw curves, capacity ITT, intervals, multiplicity, missingness, safety, and G4 authority.",
                "headline_eligible": False,
            },
            {
                "operation": "modify",
                "claim_id": "C_SLEEP_CADENCE_TOTAL_PACKAGE",
                "before": "V7 proposed a cadence total-package claim.",
                "after": "Only after powered prospective K4/K1 evidence, report a randomized SLEEP-cadence lifetime total-package contrast; any standardized terminal rewrite is descriptive only.",
                "evidence_needed": "Prospectively randomized roots, matched total opportunity, finite coverage and capacity ITT, per-event fresh-from-birth construction, disposable checkpoint exams, intervals, multiplicity, missingness, safety, and G4 authority.",
                "headline_eligible": False,
            },
        ]
    }


def build_change() -> dict[str, Any]:
    check_input_hashes()
    integration = load_json(
        "research_loop/changes/chg_20260909_extractable_sleep_bootstrap_v7/v8_integration_requirements.json"
    )
    science = load_json(
        "research_loop/changes/chg_20260909_extractable_sleep_bootstrap_v7/v8_scientific_core.json"
    )
    systems = load_json(
        "research_loop/changes/chg_20260909_extractable_sleep_bootstrap_v7/v8_systems_core.json"
    )
    v7 = load_json("research_loop/changes/chg_20260909_extractable_sleep_bootstrap_v7/change.json")
    expected_rows, expected_receipts, _, action_by_id = validate_phase_lattice(
        integration, science, systems
    )
    visibility = make_visibility(systems, action_by_id)
    tests = build_acceptance_tests(
        integration, science, systems, expected_rows, expected_receipts
    )
    graph = build_graph(v7, visibility, systems)
    forbidden = integration["authority_boundary"]["forbidden_now"]
    if len(forbidden) != len(set(forbidden)):
        raise ValueError("duplicate forbidden authority boundary item")

    return {
        "schema_version": 1,
        "artifact_type": "architecture_change",
        "change_id": "chg_20260909_extractable_sleep_bootstrap_v8",
        "title": "Extractable SLEEP and target-blind birth bootstrap v8",
        "summary": (
            "Proposal only: preserve the three-function child and waking parenting route while "
            "regenerating a producer-closed finite laboratory system, exact 126-row phase lattice, "
            "atomic candidate closure/CAS promotion, split science and release chains, and a "
            "whole-system channelized visibility matrix. All dynamic rows and results are prospective, "
            "unproduced, and unevaluated; deferred science remains unfilled."
        ),
        "system_thesis": (
            "The child has exactly THINK, DREAM, and SLEEP. Parenting and repetition act only through "
            "waking child context, child thought/action, public outcome, complete committed child trace, "
            "independent eligibility, and later noncreative personal SLEEP. The primary experiment is "
            "D/T by absent/fixed, M0 is diagnostic only, the adaptive extension is separately randomized, "
            "and the only formal estimands are Delta_R, Delta_F, and Delta_E under their complete-regime labels."
        ),
        "state": "proposed",
        "context_files": [
            {"path": path, "sha256": digest, "purpose": PURPOSES[path]}
            for path, digest in INPUTS.items()
        ],
        "graph_delta": graph,
        "loop_delta": build_loops(v7, systems),
        "claim_delta": build_claims(),
        "visibility_matrix": visibility,
        "acceptance_tests": tests,
        "human_boundary": {
            "required": True,
            "decision_owner": "Rohin Ghosh",
            "decision_question": (
                "After at least two fresh-context independent interpretations, adversarial critique, "
                "and adjudicated consensus dispose every exact V8 concern, inherited disagreement, "
                "visibility failure, and all 126 row IDs with recommendation=adopt, does Rohin ratify "
                "only these exact proposal bytes and scope?"
            ),
            "forbidden_before_approval": forbidden,
        },
    }


def write_and_validate(change: dict[str, Any]) -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".v8_alt_change.", suffix=".json", dir=OUTPUT.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(change, handle, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, OUTPUT)
    finally:
        if temporary.exists():
            temporary.unlink()

    sys.path.insert(0, str(ROOT))
    from research_loop.architecture_intake import validate_change

    validated = validate_change(ROOT, OUTPUT)
    if len(validated["acceptance_tests"]) != 126:
        raise ValueError("validated output does not contain exactly 126 top-level tests")


def main() -> None:
    change = build_change()
    write_and_validate(change)
    counts = Counter(test["required_before"] for test in change["acceptance_tests"])
    print(
        compact(
            {
                "output": str(OUTPUT.relative_to(ROOT)),
                "sha256": sha256(OUTPUT),
                "tests": len(change["acceptance_tests"]),
                "required_before": dict(sorted(counts.items())),
                "visibility_information_items": len(change["visibility_matrix"]["information_items"]),
                "visibility_stages": len(change["visibility_matrix"]["stages"]),
                "visibility_cells": len(change["visibility_matrix"]["cells"]),
                "architecture_intake_validate_change": "pass",
                "mismatches": [],
            }
        )
    )


if __name__ == "__main__":
    main()
