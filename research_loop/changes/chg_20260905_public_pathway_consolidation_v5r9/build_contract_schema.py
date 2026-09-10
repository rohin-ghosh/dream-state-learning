#!/usr/bin/env python3
"""Generate the compact PPC5r9 proposal contract schema and object inventory.

This tool is nonnormative proposal-authoring machinery.  It does not authorize
or execute fixtures, models, training, behavioral runs, GPU work, claims, or
release.  Only the generated JSON bytes can become proposed contract bytes,
and they remain proposal-only until the repository's architecture process is
completed and a human ratifies the exact successor scope.

The generator intentionally uses only Python's standard library.  It checks
the frozen r8 rework-consensus hash, recursively resolves local schema refs,
derives inventory consumer edges from the completed schema (rather than from
the producer table), rejects semantic uses of raw-byte manifests, and emits
sorted, stable UTF-8 JSON.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
R8 = ROOT.parent / "chg_20260905_public_pathway_consolidation_v5r8"
R8_CONSENSUS = R8 / "consensus.json"
R8_CONSENSUS_SHA256 = "b56561fa6903a5ac48fa9c2fda09522e7747e37bd3a270ddb17b762b6750bdca"
R8_VISIBILITY = R8 / "visibility_contract.json"
R8_VISIBILITY_SHA256 = "17d09a01bf30be79632fc311ed7d3a18a7c68b06e538fed61f30fc18fa51c142"
SCHEMA_PATH = ROOT / "contracts.schema.json"
INVENTORY_PATH = ROOT / "object_inventory.json"
SCHEMA_ID = "ppc5r9-contracts.schema.json"
SCHEMA_VERSION = 9
ARCHITECTURE_ID = "PPC5R9_PUBLIC_PATHWAY_CONSOLIDATION"
GENERIC_RATIFICATION_SCHEMA_PATH = (
    "research_loop/schemas/architecture_human_ratification.schema.json"
)
GENERIC_RATIFICATION_SCHEMA_SHA256 = (
    "9aac347cac5ca427d65c7617c39314bb8fd821919043867e3781a03153b3d58b"
)

CANONICAL_JSON = (
    "UTF-8, NFC strings, lexicographically sorted object keys, compact "
    "separators, finite integer/rational numbers only, and one trailing LF; "
    "arrays retain contract order"
)
SELF_HASH_ALGORITHM = (
    "SHA256(contract_utf8 || NUL || schema_version_ascii || NUL || "
    "artifact_type_ascii || NUL || canonical_json(object_without_self_hash) "
    "|| LF); self_hash is excluded from its own preimage"
)
FIXED_QUALIFICATION = (
    "Results concern the accepted-constructible recipient-bundle law of the "
    "exact locked PPC5 generator and its target-informed constructed benchmark. "
    "They establish neither novelty, zero-overlap generalization, naturalistic "
    "path structure, private reasoning, nor an end-to-end continual-learning "
    "mechanism."
)
RESOURCE_QUALIFICATION = (
    "Resource consequences are mandatory descriptive downstream costs only; "
    "they are not efficacy components, covariates, mediators for adjustment, "
    "stratifiers, release gates, or grounds to rescue a failed causal endpoint."
)

# Lifecycle is fixed by artifact class, not caller-selected.  The checked-in
# semantic registries and fixture specifications remain immutable proposal
# bytes; the design lock is created only after architecture ratification; all
# receipts/results are executed evidence.  RAW_BYTE_MANIFEST is the sole
# intentionally mixed carrier because it names both checked-in proposal source
# bytes and later runtime blobs, while never conveying semantic authority.
PROPOSAL_ONLY_TYPES = {
    "CONTROLLER_REGISTRY", "TRANSITION_CAUSE_REGISTRY", "STATUS_REGISTRY",
    "VISIBILITY_REGISTRY", "GATE_REGISTRY", "EVIDENCE_ROLE_REGISTRY",
    "DEPENDENCY_REGISTRY", "CLAIM_REGISTRY", "RESOURCE_REGISTRY",
    "OBJECT_INVENTORY_REGISTRY", "CONTRACT_SCHEMA_REGISTRY",
    "ALLOWED_DISPATCH_REGISTRY", "AUTHORITY_REGISTRY",
    "FIXTURE_GENERATOR_SPEC",
}
RATIFIED_DESIGN_TYPES = {"PRE_ENTROPY_DESIGN_LOCK"}

# RAW manifests carry bytes, never semantic authority, but their own temporal
# class must still be exact.  Proposal sources are frozen before architecture
# ratification; ratified-design sources are architecture-bound; generic intake
# and architecture-ratification evidence are executed but not run-bound; all
# remaining raw products are produced for one exact run.
RAW_PROPOSAL_ROLES = {
    "RAW_FROZEN_CONSENSUS",
    "RAW_SCHEMA_EDGE_EXTRACTOR",
    "RAW_INVENTORY_EDGE_EXTRACTOR",
    "RAW_VISIBILITY_EDGE_EXTRACTOR",
    "RAW_CONTRACT_SCHEMA",
    "RAW_FIXTURE_GENERATOR_SOURCE",
    "RAW_INDEPENDENT_EXPECTED_ENUMERATOR",
    "RAW_INDEPENDENT_EXECUTED_SET_EXTRACTOR",
    "RAW_INDEPENDENT_FIXTURE_SET_ORACLE",
    "RAW_FIXTURE_PAYLOAD",
}
RAW_RATIFIED_DESIGN_ROLES = {
    "RAW_GENERATOR_SOURCE",
    "RAW_ENTROPY_SOURCE_SPEC",
}
RAW_ARCHITECTURE_EXECUTED_ROLES = {
    "RAW_GENERIC_INTAKE_STATE",
    "RAW_GENERIC_ARCHITECTURE_HUMAN_RATIFICATION",
}
RAW_RUN_EXECUTED_ROLES = {
    "RAW_ENTROPY_BYTES",
    "RAW_CONTROL_CORPUS",
    "RAW_PROVIDER_TRACE",
    "RAW_MODEL_BYTES",
    "RAW_TOKENIZER_BYTES",
    "RAW_PROMPT_BYTES",
    "RAW_MODEL_OUTPUT",
    "RAW_FIXTURE_EXECUTOR_IMPLEMENTATION",
    "RAW_SEALER_IMPLEMENTATION",
    "RAW_CONSTRUCTION_OUTPUTS",
    "RAW_REVIEWER_CONTEXT",
    "RAW_REVIEW_IMPLEMENTATION",
    "RAW_ADVOCATE_CONTEXT",
    "RAW_HUMAN_RUN_RATIFICATION_EVIDENCE",
    "RAW_COLD_REPLAY_IMPLEMENTATION",
}
RAW_ROLES = (
    RAW_PROPOSAL_ROLES
    | RAW_RATIFIED_DESIGN_ROLES
    | RAW_ARCHITECTURE_EXECUTED_ROLES
    | RAW_RUN_EXECUTED_ROLES
)

VISIBILITY_SOURCE_FIELDS = {
    "PUBLIC_STATE": ("PUBLIC_STATE_SNAPSHOT", "public_view_body"),
    "SEMANTIC_CANDIDATES": ("DECODED_PROPOSAL", "semantic_candidates_canonical_json"),
    "HIDDEN_TRUTH": ("DECODED_PROPOSAL", "hidden_truth_canonical_json"),
    "PROBE_FUTURE_DATA": ("DECODED_PROPOSAL", "quarantined_probe_future_data_sha256"),
    "RESOLVED_RESPONSE_BYTES": ("PRIVILEGED_ROUTE_RECEIPT", "resolved_candidate_public_bytes"),
    "PRIVATE_ELIGIBILITY": ("ACCEPTANCE_PREDICATE_RESULT", "passed"),
    "INERT_ASSIGNMENT": ("PRE_ENTROPY_DESIGN_LOCK", "dispatch_plan_canonical_json"),
    "ACTIVE_ARTIFACT": ("RAW_BYTE_MANIFEST", "raw_sha256"),
    "LOSS_ROWS": ("D1A_CONTROL_SET_RECEIPT", "ordered_arms"),
    "ENDPOINT_TRUTH": ("OBSERVATION_RECEIPT", "value"),
    "CLAIM_TEXT": ("CLAIM_REGISTRY", "claim_renderings"),
    "LOW_ENTROPY_MATCH_HASHES": ("PRIVILEGED_ROUTE_RECEIPT", "match_keys_canonical_json"),
    "OVERLAP_AND_SCOPE": ("OVERLAP_CONSTRUCTION_RECEIPT", "overlap_scope_canonical_json"),
}

VISIBILITY_OUTPUT_FIELDS = {
    stage: ("VISIBILITY_ACCESS_RECEIPT", "projected_value_canonical_json")
    for stage in (
        "BENCHMARK_CONSTRUCTION", "TWIN_SHAM_CONSTRUCTION",
        "ASSIGNMENT_RUN_LOCK_STATIC_SEAL", "PRIVILEGED_INTERVENTION_ROUTER",
        "THINK", "READ_PROVIDER", "RESPONSE_INTERVENTION", "DREAM",
        "EVIDENCE_GATE", "WRITER", "TRAINER_VALIDATOR_PUBLICATION",
        "REDUCER", "CANDIDATE_DECISION", "CLAIM_RELEASE", "AUDIT",
    )
}


def visibility_source_field(information_item: str, stage: str) -> tuple[str, str]:
    """Return a causally prior source for an allowed stage ingress.

    The old proposal mapped every information class to one convenient field,
    which created temporal back-edges (for example a later MODEL_VIEW feeding
    benchmark construction).  Stage-specific sources keep construction-time
    oracle inputs separate from runtime observations and release-time values.
    """
    if information_item == "PUBLIC_STATE" and stage in {
        "BENCHMARK_CONSTRUCTION", "TWIN_SHAM_CONSTRUCTION",
        "ASSIGNMENT_RUN_LOCK_STATIC_SEAL",
    }:
        return "DECODED_PROPOSAL", "public_state_template_canonical_json"
    if information_item == "RESOLVED_RESPONSE_BYTES":
        if stage == "TWIN_SHAM_CONSTRUCTION":
            return "DECODED_PROPOSAL", "semantic_candidates_canonical_json"
        if stage in {"ASSIGNMENT_RUN_LOCK_STATIC_SEAL",
                     "PRIVILEGED_INTERVENTION_ROUTER"}:
            return "PATH_CONSTRUCTION_RECEIPT", "resolved_response_candidates_canonical_json"
        if stage == "RESPONSE_INTERVENTION":
            return "PRIVILEGED_ROUTE_RECEIPT", "resolved_candidate_public_bytes"
        return "INTERVENTION_EMISSION_RECEIPT", "emitted_public_bytes"
    if information_item == "ENDPOINT_TRUTH" and stage in {
        "BENCHMARK_CONSTRUCTION", "TWIN_SHAM_CONSTRUCTION",
        "ASSIGNMENT_RUN_LOCK_STATIC_SEAL",
    }:
        return "DECODED_PROPOSAL", "hidden_truth_canonical_json"
    if information_item == "LOW_ENTROPY_MATCH_HASHES" and stage in {
        "TWIN_SHAM_CONSTRUCTION", "ASSIGNMENT_RUN_LOCK_STATIC_SEAL",
    }:
        return "PATH_CONSTRUCTION_RECEIPT", "low_entropy_match_keys_canonical_json"
    if information_item == "OVERLAP_AND_SCOPE" and stage in {
        "BENCHMARK_CONSTRUCTION", "TWIN_SHAM_CONSTRUCTION",
        "ASSIGNMENT_RUN_LOCK_STATIC_SEAL",
    }:
        return "PRE_ENTROPY_DESIGN_LOCK", "parameter_law_canonical_json"
    return VISIBILITY_SOURCE_FIELDS[information_item]

CLAIM_TEXTS = {
    "PPC5_D1A_SUPPORTED_SELECTION": (
        "On independently sampled recipient lives from the accepted-constructible "
        "recipient-bundle law of the exact locked PPC5 generator, the evidence-gated "
        "READ-LoRA exceeded each registered paired supported-selection margin with "
        "probability above its locked threshold against adapter-off, an exactly "
        "dose/opportunity-matched wrong-life adapter, and an exactly dose-matched "
        "binding derangement, while passing recipient-life false-selection and "
        "NOT_FOUND safety ceilings. This is external complete-table candidate-conditioned "
        "selection, not closed-book storage."
    ),
    "PPC5_D1B_OBSERVABLE_EDGE_DEPENDENCE": (
        "On independently sampled decisive-path recipient lives from the "
        "accepted-constructible recipient-bundle law of the exact locked PPC5 "
        "generator, authentic interleaved use exceeded every registered edge-specific "
        "CUT and TWIN margin and both timing-control margins with probability above "
        "their locked thresholds, while every edge-specific oracle-preserving SHAM "
        "remained noninferior by its registered population criterion. This is observable "
        "public behavioral response dependence, not access to private cognition."
    ),
    "PPC5_D1C_DREAM_CONTEXT_POLICY": (
        "On independently sampled recipient lives from the accepted-constructible "
        "recipient-bundle law of the exact locked PPC5 generator, assignment to the "
        "shared frozen-model DREAM-selected reversible context exceeded each registered "
        "paired action margin with probability above its locked threshold against total "
        "recency and recipient-local hash-permuted context policies, inclusive of context "
        "cardinality, order, focus, prompt-token, failure, abstention, and no-view "
        "consequences."
    ),
    "PPC5_D1D_DREAM_TO_SLEEP_TOTAL_POLICY": (
        "On independently sampled recipient lives from the accepted-constructible "
        "recipient-bundle law of the exact locked PPC5 generator, DREAM_TO_SLEEP "
        "assignment exceeded each registered paired supported-selection and action "
        "margin with probability above its locked threshold against total recency and "
        "hash-permuted root policies, inclusive of policy-induced evidence dose, "
        "training, publication, inference, failure, and resource consequences and "
        "without post-treatment dose adjustment."
    ),
    "PPC5_NONMEDIATIONAL_FOUR_ASSAY_INTERSECTION": (
        "All four separately identified PPC5 assays passed over the "
        "accepted-constructible recipient-bundle law of the exact locked generator: "
        "supported complete-table selection, observable every-edge interleaved-response "
        "dependence, frozen DREAM context-policy value, and DREAM_TO_SLEEP total-policy "
        "value. This is a non-mediational four-assay intersection, not an end-to-end "
        "learning mechanism."
    ),
}

H = {"$ref": "#/$defs/hash"}
ID = {"$ref": "#/$defs/id"}
SYM = {"$ref": "#/$defs/symbol"}
RAT = {"$ref": "#/$defs/rational"}
PROB = {"$ref": "#/$defs/probability"}
BYTES = {"$ref": "#/$defs/nonempty_string"}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stable_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def pretty_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")


def self_hash(value: dict[str, Any]) -> str:
    preimage = copy.deepcopy(value)
    preimage.pop("self_hash", None)
    prefix = (
        value["contract"].encode("utf-8")
        + b"\x00"
        + str(value["schema_version"]).encode("ascii")
        + b"\x00"
        + value["artifact_type"].encode("ascii")
        + b"\x00"
    )
    return sha256_bytes(prefix + stable_bytes(preimage))


def arr(items: dict[str, Any], minimum: int = 0, maximum: int | None = None,
        *, unique: bool = False) -> dict[str, Any]:
    result: dict[str, Any] = {"type": "array", "items": items, "minItems": minimum}
    if maximum is not None:
        result["maxItems"] = maximum
    if unique:
        result["uniqueItems"] = True
    return result


def tuple_of(*items: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "array",
        "prefixItems": list(items),
        "items": False,
        "minItems": len(items),
        "maxItems": len(items),
    }


def enum(*values: Any) -> dict[str, Any]:
    return {"enum": list(values)}


def integer(minimum: int = 0, maximum: int | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"type": "integer", "minimum": minimum}
    if maximum is not None:
        result["maximum"] = maximum
    return result


def closed(properties: dict[str, Any], required: list[str] | None = None,
           **keywords: Any) -> dict[str, Any]:
    result = {
        "type": "object",
        "additionalProperties": False,
        "required": required if required is not None else list(properties),
        "properties": properties,
    }
    result.update(keywords)
    return result


def nullable(schema: dict[str, Any]) -> dict[str, Any]:
    return {"oneOf": [schema, {"type": "null"}]}


def artifact_ref(role: str, targets: str | list[str], consumer_stage: str,
                 ordinal: int | str = 0, cardinality: str = "ONE",
                 *, run_bound: bool = True) -> dict[str, Any]:
    target_list = [targets] if isinstance(targets, str) else list(targets)
    ordinal_schema = {"const": ordinal} if isinstance(ordinal, int) else integer()
    properties: dict[str, Any] = {
        "role": {"const": role},
        "ordinal": ordinal_schema,
        "artifact_type": (
            {"const": target_list[0]} if len(target_list) == 1 else enum(*target_list)
        ),
        "self_hash": H,
    }
    if run_bound:
        properties = {"run_id": ID, **properties}
    result = closed(properties)
    result.update({
        "x-artifact-ref": True,
        "x-artifact-types": target_list,
        "x-role": role,
        "x-consumer-stage": consumer_stage,
        "x-ordinal": ordinal,
        "x-cardinality": cardinality,
    })
    return result


def refs(role: str, targets: str | list[str], stage: str, *, minimum: int = 1,
         maximum: int | None = None, run_bound: bool = True) -> dict[str, Any]:
    return arr(
        artifact_ref(role, targets, stage, "VARIABLE", "ORDERED_EXACT", run_bound=run_bound),
        minimum,
        maximum,
    )


def top(artifact_type: str, producer_role: str, fields: dict[str, Any],
        *, contract: str | None = None, one_of: list[dict[str, Any]] | None = None,
        description: str = "") -> dict[str, Any]:
    contract_value = contract or f"ppc5.{artifact_type.lower()}.v9"
    if artifact_type == "RAW_BYTE_MANIFEST":
        lifecycle_schema = enum("PROPOSAL_ONLY", "RATIFIED_DESIGN", "EXECUTED")
    elif artifact_type in PROPOSAL_ONLY_TYPES:
        lifecycle_schema = {"const": "PROPOSAL_ONLY"}
    elif artifact_type in RATIFIED_DESIGN_TYPES:
        lifecycle_schema = {"const": "RATIFIED_DESIGN"}
    else:
        lifecycle_schema = {"const": "EXECUTED"}
    properties = {
        "contract": {"const": contract_value},
        "schema_version": {"const": SCHEMA_VERSION},
        "artifact_type": {"const": artifact_type},
        # The schema is authored while the architecture is proposal-only, but
        # it also validates later hash-bound runtime receipts.  Do not force a
        # runtime GRANT receipt to claim that it is itself only a proposal.
        "lifecycle_state": lifecycle_schema,
        "producer_role": {"const": producer_role},
        **fields,
        "self_hash": H,
    }
    result = closed(properties, oneOf=one_of) if one_of else closed(properties)
    result["x-top-level-artifact"] = True
    result["x-self-hash-field"] = "self_hash"
    result["x-self-hash-algorithm"] = SELF_HASH_ALGORITHM
    result["description"] = description or (
        f"Closed {artifact_type} object. Authority is conveyed only by the exact "
        "ratification and reducer chain, never by schema validity alone."
    )
    return result


def raw_ref(role: str, stage: str, ordinal: int | str = 0,
            cardinality: str = "ONE", *, run_bound: bool = False) -> dict[str, Any]:
    if not role.startswith("RAW_"):
        raise ValueError(f"raw byte role must start RAW_: {role}")
    return artifact_ref(role, "RAW_BYTE_MANIFEST", stage, ordinal, cardinality,
                        run_bound=run_bound)


def build_visibility_catalog() -> tuple[list[str], list[str], list[dict[str, Any]], list[dict[str, Any]]]:
    """Turn the 195-cell r8 product into closed r9 cell/edge constants.

    The 83 previously allowed cells receive concrete source/output field paths.
    R07 changes RESOLVED_RESPONSE_BYTES/THINK from forbidden to DERIVED_ONLY,
    yielding 84 concrete r9 edges while retaining the same 13-by-15 product.
    """
    raw = R8_VISIBILITY.read_bytes()
    if sha256_bytes(raw) != R8_VISIBILITY_SHA256:
        raise ValueError("frozen r8 visibility hash mismatch")
    source = json.loads(raw)
    information_items = source["information_items"]
    stages = source["stages"]
    if len(information_items) != 13 or len(stages) != 15:
        raise ValueError("r8 visibility axes are not the frozen 13-by-15 product")

    by_key = {(cell["information_item"], cell["stage"]): cell for cell in source["cells"]}
    cells: list[dict[str, Any]] = []
    allowed_edges: list[dict[str, Any]] = []
    for information_ordinal, information_item in enumerate(information_items):
        for stage_ordinal, stage in enumerate(stages):
            prior = by_key[(information_item, stage)]
            visibility = prior["visibility"].upper()
            rationale = prior["rationale"]
            if information_item == "RESOLVED_RESPONSE_BYTES" and stage == "THINK":
                visibility = "DERIVED_ONLY"
                rationale = "sole emitted-public-byte path into public_view_body.last_read and MODEL_VIEW"

            if visibility == "FORBIDDEN":
                cell = {
                    "information_item": information_item,
                    "information_ordinal": information_ordinal,
                    "consumer_stage": stage,
                    "stage_ordinal": stage_ordinal,
                    "visibility": "FORBIDDEN",
                    "rationale": rationale,
                    "source_type": None,
                    "source_field_path": None,
                    "projection_algorithm": None,
                    "output_type": None,
                    "output_field_path": None,
                    "concrete_role": None,
                    "ordinal": None,
                    "cardinality": None,
                }
            else:
                source_type, source_field = visibility_source_field(information_item, stage)
                output_type, output_field = VISIBILITY_OUTPUT_FIELDS[stage]
                role = f"PROJECT_{information_item}_TO_{stage}"
                if source_type == "RAW_BYTE_MANIFEST":
                    role = "RAW_" + role
                algorithm = f"PROJECT_{information_item}_TO_{stage}_V1"
                if information_item == "RESOLVED_RESPONSE_BYTES" and stage == "THINK":
                    source_type = "INTERVENTION_EMISSION_RECEIPT"
                    source_field = "emitted_public_bytes"
                    role = "INTERVENTION_EMISSION_TO_PUBLIC_VIEW"
                    algorithm = "EMITTED_PUBLIC_BYTES_TO_LAST_READ_TO_MODEL_VIEW_V1"
                cell = {
                    "information_item": information_item,
                    "information_ordinal": information_ordinal,
                    "consumer_stage": stage,
                    "stage_ordinal": stage_ordinal,
                    "visibility": visibility,
                    "rationale": rationale,
                    "source_type": source_type,
                    "source_field_path": source_field,
                    "projection_algorithm": algorithm,
                    "output_type": output_type,
                    "output_field_path": output_field,
                    "concrete_role": role,
                    "ordinal": len(allowed_edges),
                    "cardinality": "ONE",
                }
                allowed_edges.append(copy.deepcopy(cell))
            cells.append(cell)

    if len(cells) != 195 or len(allowed_edges) != 84:
        raise ValueError("r9 visibility closure must have 195 cells and 84 allowed edges")
    return information_items, stages, cells, allowed_edges


defs: dict[str, Any] = {
    "hash": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
    "id": {"type": "string", "pattern": "^[a-z][a-z0-9_-]{2,95}$"},
    "symbol": {"type": "string", "pattern": "^[A-Z][A-Z0-9_]{0,127}$"},
    "nonempty_string": {"type": "string", "minLength": 1},
    "rational": closed({
        "numerator": {"type": "integer"},
        "denominator": integer(1),
        "reduced": {"const": True},
    }),
    "probability": closed({
        "numerator": integer(),
        "denominator": integer(1),
        "reduced": {"const": True},
        "within_unit_interval": {"const": True},
    }),
    "budget": closed({
        "calls": integer(),
        "reads": integer(),
        "actions": integer(),
        "input_tokens": integer(),
        "output_tokens": integer(),
    }),
    "entropy_slice": closed({
        "domain": SYM,
        "ordinal": integer(),
        "offset_bytes": integer(),
        "length_bytes": integer(1),
        "slice_sha256": H,
    }),
    "gate_membership_template": closed({
        "assay_id": enum("D1A", "D1B", "D1C", "D1D"),
        "gate_id": SYM,
        "sample_ordinal": integer(),
        "endpoint_id": SYM,
        "ordered_lower_unit_ordinals": arr(integer(), 1, unique=True),
        "treatment_condition_role": SYM,
        "control_condition_role": SYM,
    }),
    "safety_key_template": closed({
        "sample_ordinal": integer(),
        "arm_role": enum("FALSE_SELECTION", "NOT_FOUND"),
        "endpoint_id": SYM,
        "lower_unit_ordinal": integer(),
    }),
    "resolved_safety_key": closed({
        "sample_ordinal": integer(),
        "recipient_life_id": ID,
        "arm_role": enum("FALSE_SELECTION", "NOT_FOUND"),
        "endpoint_id": SYM,
        "lower_unit_id": ID,
        "observation_key_sha256": H,
    }),
    "control_arm": closed({
        "role": enum("AUTHENTIC", "WRONG_LIFE", "BINDING_DERANGED"),
        "corpus_ref": raw_ref("RAW_CONTROL_CORPUS", "D1A_CONTROL_CONSTRUCTION", "VARIABLE", run_bound=True),
        "corpus_sha256": H,
        "dose_vector_sha256": H,
        "request_multiset_sha256": H,
        "response_multiset_sha256": H,
    }),
    "public_view_body": closed({
        "assay_id": enum("D1A", "D1B", "D1C", "D1D"),
        "recipient_life_id": ID,
        "sample_ordinal": integer(),
        "step_ordinal": integer(),
        "phase": SYM,
        "last_read": nullable(BYTES),
        "last_read_sha256": nullable(H),
        "consecutive_error_count": integer(0, 3),
        "terminal": {"type": "boolean"},
        "remaining_budget": {"$ref": "#/$defs/budget"},
    }),
    "counter_transition": {
        "oneOf": [
            closed({"result_class": {"const": "SUCCESS"}, "before": {"const": before},
                    "public_after": {"const": 0}, "private_after": {"const": 0}})
            for before in range(3)
        ] + [
            closed({"result_class": {"const": "MISSING"}, "before": {"const": before},
                    "public_after": {"const": before}, "private_after": {"const": before}})
            for before in range(3)
        ] + [
            closed({"result_class": {"const": "ERROR"}, "before": {"const": before},
                    "public_after": {"const": before + 1}, "private_after": {"const": before + 1}})
            for before in range(3)
        ],
    },
    "observation_key": closed({
        "assay_id": enum("D1A", "D1B", "D1C", "D1D"),
        "gate_id": SYM,
        "sample_ordinal": integer(),
        "recipient_life_id": ID,
        "condition_role": SYM,
        "endpoint_id": SYM,
        "lower_unit_id": ID,
        "observation_ordinal": integer(),
    }),
    "visibility_edge": {
        "oneOf": [
            closed({
                "information_item": SYM,
                "information_ordinal": integer(),
                "consumer_stage": SYM,
                "stage_ordinal": integer(),
                "visibility": {"const": "FORBIDDEN"},
                "rationale": BYTES,
                "source_type": {"type": "null"},
                "source_field_path": {"type": "null"},
                "projection_algorithm": {"type": "null"},
                "output_type": {"type": "null"},
                "output_field_path": {"type": "null"},
                "concrete_role": {"type": "null"},
                "ordinal": {"type": "null"},
                "cardinality": {"type": "null"},
            }),
            closed({
                "information_item": SYM,
                "information_ordinal": integer(),
                "consumer_stage": SYM,
                "stage_ordinal": integer(),
                "visibility": enum("VISIBLE", "DERIVED_ONLY"),
                "rationale": BYTES,
                "source_type": SYM,
                "source_field_path": BYTES,
                "projection_algorithm": SYM,
                "output_type": SYM,
                "output_field_path": BYTES,
                "concrete_role": SYM,
                "ordinal": integer(),
                "cardinality": enum("ONE", "ORDERED_EXACT"),
            }),
        ]
    },
    "registry_row": closed({
        "row_key": SYM,
        "ordinal": integer(),
        "role": SYM,
        "cardinality": enum("ONE", "OPTIONAL_ONE", "ORDERED_EXACT"),
        "producer_role": SYM,
        "consumer_stages": arr(SYM, 1, unique=True),
        "content_sha256": H,
    }),
    "controller_result_transition": closed({
        "accepted_result": SYM,
        "counter_input": integer(0, 2),
        "counter_output": integer(0, 3),
        "queue_input_class": enum("EMPTY", "NONEMPTY"),
        "queue_output_rule": enum("PRESERVE", "SET_NONEMPTY", "DECREMENT_ONE", "FINALIZE_ALL_TO_EMPTY"),
        "normalized_result": SYM,
        "next_phase": SYM,
        "next_index_rule": enum("NONE", "INCREMENT", "ZERO"),
        "terminal_reason": nullable(SYM),
        "consume_call": {"type": "boolean"},
        "advance_once": {"type": "boolean"},
        "retry_allowed": {"const": False},
        "endpoint_effect": SYM,
        "terminal_intent": {"type": "boolean"},
        "result_specific_queue_effect": enum("NONE", "ENQUEUE", "FLUSH", "FINALIZE_QUEUE"),
    }),
    "controller_row": closed({
        "row_key": SYM,
        "assay_id": enum("D1A", "D1B", "D1C", "D1D"),
        "program": SYM,
        "phase_family": SYM,
        "phase_index_relation": enum("LESS_THAN_BOUND", "AT_BOUNDARY", "UNINDEXED"),
        "bound_symbol": nullable(SYM),
        "index_increment": integer(),
        "boundary_phase": SYM,
        "guard": SYM,
        "dispatch_kind": enum("MODEL", "PROVIDER", "CONTROLLER", "ENVIRONMENT", "NO_MODEL_FINALIZER"),
        "required_operation": SYM,
        "input_debit": {"$ref": "#/$defs/budget"},
        "declared_queue_operation": enum("NONE", "QUEUE", "FLUSH", "DISCARD", "EXECUTE_COMMIT"),
        "queue_precondition": enum("NONE_REQUIRED", "CURRENT_SLOT_QUEUED", "OUTSTANDING_SET_MAY_EXIST"),
        "result_transitions": arr({"$ref": "#/$defs/controller_result_transition"}, 1),
        "first_failure_order": tuple_of(*[{"const": item} for item in (
            "INTEGRITY", "PREDISPATCH_BUDGET", "MISSING_CALL", "TOKEN_LIMIT",
            "PARSE_ERROR", "LOGICAL_ALLOWANCE", "DOMAIN", "REFERENCE",
            "PREDICTION", "SCHEDULE", "PROVIDER_MISSING", "ENVIRONMENT_INVALID",
            "SUCCESS",
        )]),
    }),
    "transition_cause_row": closed({
        "cause": enum("MODEL_DISPATCH", "DIRECT_PROVIDER", "CONTROLLER_PHASE", "QUEUE_FLUSH",
                      "QUEUE_DISCARD", "COMMITTED_ACTION", "HARNESS_TERMINAL"),
        "ordinal": integer(),
        "ordered_lineage_roles": arr(SYM, 1, unique=True),
        "content_sha256": H,
    }),
    "fixture_axis": closed({
        "axis_id": SYM,
        "ordinal": integer(),
        "finite_values": arr(BYTES, 1, unique=True),
    }),
    "fixture_expected_branch": closed({
        "branch_key": BYTES,
        "branch_key_sha256": H,
        "ordinal": integer(),
        "case_ordinal": integer(),
        "applicability_rule": BYTES,
        "input_canonical_json": BYTES,
        "expected_output_canonical_json": nullable(BYTES),
        "expected_output_sha256": nullable(H),
        "expected_first_failure": nullable(SYM),
    }),
    "fixture_typed_value": {
        "oneOf": [
            closed({"value_type": {"const": "BOOLEAN"}, "value": {"type": "boolean"}}),
            closed({"value_type": {"const": "INTEGER"}, "value": {"type": "integer"}}),
            closed({"value_type": {"const": "STRING"}, "value": {"type": "string"}}),
            closed({"value_type": {"const": "NULL"}, "value": {"type": "null"}}),
            closed({"value_type": {"const": "OBJECT"}, "value": {"type": "object"}}),
            closed({"value_type": {"const": "ARRAY"}, "value": {"type": "array"}}),
        ]
    },
    "fixture_one_field_mutation": closed({
        "ordinal": integer(),
        "case_ordinal": integer(),
        "mutation_id": SYM,
        "branch_key": BYTES,
        "branch_key_sha256": H,
        "base_positive_branch_key": BYTES,
        "target_json_pointer": BYTES,
        "target_typed_role": SYM,
        "before_typed_value": {"$ref": "#/$defs/fixture_typed_value"},
        "after_typed_value": {"$ref": "#/$defs/fixture_typed_value"},
        "allowed_transitive_rehash_roles": arr(SYM, unique=True),
        "before_input_canonical_json": BYTES,
        "after_input_canonical_json": BYTES,
        "expected_output_canonical_json": {"type": "null"},
        "expected_first_failure": SYM,
    }),
    "inventory_binding": closed({
        "consumer_type": SYM,
        "consumer_stage": SYM,
        "field_path": BYTES,
        "role": SYM,
        "ordinal": {"oneOf": [integer(), {"const": "VARIABLE"}]},
        "cardinality": enum("ONE", "OPTIONAL_ONE", "ORDERED_EXACT"),
    }),
    "inventory_object": closed({
        "type": SYM,
        "schema_ref": BYTES,
        "contract": BYTES,
        "producer_role": SYM,
        "permitted_consumer_stages": arr(SYM, 0, unique=True),
        "reference_bindings": arr({"$ref": "#/$defs/inventory_binding"}),
        "visibility_bindings": arr({"$ref": "#/$defs/visibility_edge"}),
        "self_hash_field": {"const": "self_hash"},
        "payload_mode": enum("INLINE_CLOSED_FIELDS", "RAW_BYTES_ONLY"),
    }),
}


PRODUCERS: dict[str, str] = {}


def add(name: str, producer: str, fields: dict[str, Any], **kwargs: Any) -> None:
    if name in PRODUCERS:
        raise ValueError(f"duplicate top-level artifact {name}")
    PRODUCERS[name] = producer
    defs[name.lower()] = top(name, producer, fields, **kwargs)


# Raw bytes are deliberately the only untyped payload carrier.  Its roles are
# syntactically RAW_* and it never stands in for a semantic registry/receipt.
add("RAW_BYTE_MANIFEST", "RAW_MANIFEST_BUILDER", {
    "raw_role": {"type": "string", "pattern": "^RAW_[A-Z0-9_]+$"},
    "media_type": BYTES,
    "relative_path": {"type": "string", "pattern": "^(?!/)(?!.*(?:^|/)\\.\\.(?:/|$)).+$"},
    "byte_length": integer(),
    "raw_sha256": H,
}, description="Manifest for a genuinely raw blob; it carries no semantic authority by itself.")

# Replace the generic mixed-lifecycle shell with an exact closed branch per
# temporal raw-role class.  Root properties exist only for deterministic
# schema/inventory introspection; each oneOf branch is the validating closed
# object.  In particular, proposal/design/architecture evidence cannot carry a
# run_id, while every runtime raw product must carry one.
_raw_common_properties = {
    "contract": {"const": "ppc5.raw_byte_manifest.v9"},
    "schema_version": {"const": SCHEMA_VERSION},
    "artifact_type": {"const": "RAW_BYTE_MANIFEST"},
    "producer_role": {"const": "RAW_MANIFEST_BUILDER"},
    "media_type": BYTES,
    "relative_path": {"type": "string", "pattern": "^(?!/)(?!.*(?:^|/)\\.\\.(?:/|$)).+$"},
    "byte_length": integer(),
    "raw_sha256": H,
    "self_hash": H,
}


def _raw_manifest_branch(lifecycle: str, roles: set[str], *, run_bound: bool) -> dict[str, Any]:
    properties = {
        **_raw_common_properties,
        "lifecycle_state": {"const": lifecycle},
        "raw_role": enum(*sorted(roles)),
    }
    if run_bound:
        properties = {**properties, "run_id": ID}
    return closed(properties)


defs["raw_byte_manifest"] = {
    "type": "object",
    "properties": {
        **_raw_common_properties,
        "lifecycle_state": enum("PROPOSAL_ONLY", "RATIFIED_DESIGN", "EXECUTED"),
        "raw_role": enum(*sorted(RAW_ROLES)),
        "run_id": ID,
    },
    "oneOf": [
        _raw_manifest_branch("PROPOSAL_ONLY", RAW_PROPOSAL_ROLES, run_bound=False),
        _raw_manifest_branch("RATIFIED_DESIGN", RAW_RATIFIED_DESIGN_ROLES, run_bound=False),
        _raw_manifest_branch("EXECUTED", RAW_ARCHITECTURE_EXECUTED_ROLES, run_bound=False),
        _raw_manifest_branch("EXECUTED", RAW_RUN_EXECUTED_ROLES, run_bound=True),
    ],
    "x-top-level-artifact": True,
    "x-self-hash-field": "self_hash",
    "x-self-hash-algorithm": SELF_HASH_ALGORITHM,
    "description": (
        "Closed role/lifecycle/run-class manifest for genuinely raw bytes; "
        "it carries no semantic authority by itself."
    ),
}


# A RAW manifest can locate the repository's generic human-ratification bytes,
# but cannot itself convey their meaning.  This typed binding is the semantic
# bridge: a CPU parser validates the exact external schema, records every
# authority-bearing field, and proves that the parsed content hashes to the
# referenced raw bytes.  The PPC architecture receipt below consumes this
# object and requires field-for-field equality rather than self-attesting to a
# human decision beside an opaque hash.
external_ratification_id = {
    "type": "string", "pattern": "^[a-z0-9][a-z0-9._-]*$"
}
external_ratification_scope = arr(BYTES, 1, unique=True)
add("GENERIC_ARCHITECTURE_HUMAN_RATIFICATION_BINDING",
    "GENERIC_RATIFICATION_SCHEMA_VALIDATOR", {
    "architecture_id": {"const": ARCHITECTURE_ID},
    "external_schema_relative_path": {"const": GENERIC_RATIFICATION_SCHEMA_PATH},
    "external_schema_sha256": {"const": GENERIC_RATIFICATION_SCHEMA_SHA256},
    "generic_ratification_ref": raw_ref(
        "RAW_GENERIC_ARCHITECTURE_HUMAN_RATIFICATION",
        "GENERIC_RATIFICATION_BINDING", run_bound=False),
    "generic_ratification_raw_sha256": H,
    "schema_version_external": {"const": 1},
    "artifact_type_external": {"const": "architecture_human_ratification"},
    "ratification_id": external_ratification_id,
    "change_id": {"const": "chg_20260905_public_pathway_consolidation_v5r9"},
    "state": {"const": "human_approved"},
    "consensus_sha256": H,
    "human_required_state_sha256": H,
    "ratifier": BYTES,
    "authority_statement": BYTES,
    "decision_statement": BYTES,
    "decided_at": BYTES,
    "authorized_scope": external_ratification_scope,
    "forbidden_scope": arr(BYTES, unique=True),
    "authorization_evidence": closed({
        "path": BYTES,
        "sha256": H,
        "excerpt": BYTES,
    }),
    "implementation_authorized": {"const": True},
    "raw_bytes_validate_against_external_schema": {"const": True},
    "parsed_fields_equal_raw_bytes": {"const": True},
})


# R03: human architecture ratification precedes the exact design lock.  This
# receipt authorizes only CPU/no-model implementation of the ratified proposal;
# it can never authorize a model call, training, behavioral execution, GPU use,
# or a scientific claim.
add("ARCHITECTURE_RATIFICATION_RECEIPT", "HUMAN_ARCHITECTURE_RATIFIER", {
    "architecture_id": {"const": ARCHITECTURE_ID},
    "ratification_id": ID,
    "change_id": {"const": "chg_20260905_public_pathway_consolidation_v5r9"},
    "state": {"const": "human_approved"},
    "generic_intake_state_sha256": H,
    "human_required_state_sha256": H,
    "architecture_change_sha256": H,
    "interpretation_sha256s": tuple_of(H, H),
    "critique_sha256": H,
    "consensus_sha256": H,
    "proposal_bundle_sha256": H,
    "exact_proposal_bytes_sha256": H,
    "ratifier": BYTES,
    "authority_statement": BYTES,
    "decision_statement": BYTES,
    "decided_at": BYTES,
    "frozen_consensus_ref": raw_ref("RAW_FROZEN_CONSENSUS", "ARCHITECTURE_RATIFICATION",
                                     run_bound=False),
    "generic_ratification_binding_ref": artifact_ref(
        "GENERIC_ARCHITECTURE_HUMAN_RATIFICATION_BINDING",
        "GENERIC_ARCHITECTURE_HUMAN_RATIFICATION_BINDING",
        "ARCHITECTURE_RATIFICATION", run_bound=False),
    "generic_ratification_field_equality": {"const": True},
    "authorization_evidence": closed({
        "path": BYTES,
        "sha256": H,
        "excerpt": BYTES,
    }),
    "decision": {"const": "RATIFIED"},
    "implementation_authorized": {"const": True},
    "authorized_scope": {"const": [
        "AUTHOR_EXACT_RATIFIED_PPC5R9_CPU_NO_MODEL_IMPLEMENTATION",
        "EXECUTE_EXACT_RATIFIED_PPC5R9_PREMODEL_CPU_CONFORMANCE",
    ]},
    "forbidden_scope": {"const": [
        "MODEL_OR_TOKENIZER_OR_EMBEDDING_EXECUTION",
        "TRAINING_OR_BEHAVIORAL_OR_GPU_EXECUTION",
        "SCIENTIFIC_CLAIM_OR_RELEASE",
        "ANY_CHANGE_TO_RATIFIED_ARCHITECTURE_FIXTURES_OR_SCOPE",
    ]},
    "model_execution_reachable": {"const": False},
}, one_of=[
    {"properties": {"lifecycle_state": {"const": "EXECUTED"}}},
])


# R03: temporal design/entropy/realization/safety/populated-lock chain.
add("PRE_ENTROPY_DESIGN_LOCK", "DESIGN_LOCK_BUILDER", {
    "architecture_id": {"const": ARCHITECTURE_ID},
    "run_id": ID,
    "architecture_ratification_ref": artifact_ref(
        "ARCHITECTURE_RATIFICATION", "ARCHITECTURE_RATIFICATION_RECEIPT",
        "RUN_DESIGN", run_bound=False),
    "generator_source_ref": raw_ref("RAW_GENERATOR_SOURCE", "RUN_DESIGN", run_bound=False),
    "generator_law_sha256": H,
    "entropy_source_spec_ref": raw_ref("RAW_ENTROPY_SOURCE_SPEC", "RUN_DESIGN",
                                        run_bound=False),
    "parameter_law_canonical_json": BYTES,
    "proposal_limit": integer(1),
    "sample_size_n": integer(1),
    "gate_membership_templates": arr({"$ref": "#/$defs/gate_membership_template"}, 1),
    "stable_d1b_gate_keys": arr(SYM, 1, unique=True),
    "safety_key_templates": arr({"$ref": "#/$defs/safety_key_template"}, 1),
    "margins": arr(RAT, 1),
    "pi0": PROB,
    "safety_ceilings": arr(PROB, 2),
    "alpha": PROB,
    "cp_decimal_scale": integer(1),
    "capacities": {"$ref": "#/$defs/budget"},
    "call_schedule_canonical_json": BYTES,
    "seed_domains": arr(SYM, 1, unique=True),
    "dispatch_plan_canonical_json": BYTES,
    "fixture_spec_refs": refs("FIXTURE_SPEC", "FIXTURE_GENERATOR_SPEC", "RUN_DESIGN", minimum=13,
                              maximum=13, run_bound=False),
    "semantic_registry_refs": {"$ref": "#/$defs/semantic_registry_refs"},
})

add("ENTROPY_ACQUISITION_RECEIPT", "ENTROPY_ACQUIRER", {
    "run_id": ID,
    "design_lock_ref": artifact_ref("PRE_ENTROPY_DESIGN_LOCK", "PRE_ENTROPY_DESIGN_LOCK",
                                    "ENTROPY_ACQUISITION"),
    "raw_entropy_ref": raw_ref("RAW_ENTROPY_BYTES", "ENTROPY_ACQUISITION", run_bound=True),
    "ordered_disjoint_slices": arr({"$ref": "#/$defs/entropy_slice"}, 1),
    "slice_union_sha256": H,
    "acquired_before_decode_sequence": integer(),
})

for object_type, producer, payload_field in (
    ("RECIPIENT_BUNDLE", "PROPOSAL_DECODER", "recipient_bundle_canonical_json"),
    ("DONOR_BUNDLE", "PROPOSAL_DECODER", "donor_bundle_canonical_json"),
    ("DECODED_PROPOSAL", "PROPOSAL_DECODER", "decoded_proposal_canonical_json"),
):
    add(object_type, producer, {
        "run_id": ID,
        "proposal_ordinal": integer(),
        "design_lock_ref": artifact_ref("PRE_ENTROPY_DESIGN_LOCK", "PRE_ENTROPY_DESIGN_LOCK",
                                        "PROPOSAL_DECODING"),
        "entropy_receipt_ref": artifact_ref("ENTROPY_ACQUISITION", "ENTROPY_ACQUISITION_RECEIPT",
                                            "PROPOSAL_DECODING"),
        "entropy_slice_domain": SYM,
        payload_field: BYTES,
        "content_sha256": H,
    })

# The decoded proposal is the closed privileged construction carrier for the
# four benchmark-only information classes used by the visibility registry.
decoded_properties = defs["decoded_proposal"]["properties"]
decoded_properties.update({
    "public_state_template_canonical_json": BYTES,
    "semantic_candidates_canonical_json": BYTES,
    "hidden_truth_canonical_json": BYTES,
    "quarantined_probe_future_data_sha256": H,
})
defs["decoded_proposal"]["required"].extend([
    "public_state_template_canonical_json",
    "semantic_candidates_canonical_json",
    "hidden_truth_canonical_json",
    "quarantined_probe_future_data_sha256",
])

add("ACCEPTANCE_PREDICATE_RESULT", "ACCEPTANCE_REDUCER", {
    "run_id": ID,
    "proposal_ordinal": integer(),
    "predicate_ordinal": integer(),
    "predicate_id": SYM,
    "decoded_proposal_ref": artifact_ref("DECODED_PROPOSAL", "DECODED_PROPOSAL",
                                         "BENCHMARK_CONSTRUCTION"),
    "passed": {"type": "boolean"},
    "first_failure_code": nullable(SYM),
})

add("FIRST_FAILURE_OR_EXHAUSTION_RECEIPT", "ACCEPTANCE_REDUCER", {
    "run_id": ID,
    "proposal_ordinal": integer(),
    "proposal_limit": integer(1),
    "predicate_result_refs": refs("ACCEPTANCE_PREDICATE_RESULT", "ACCEPTANCE_PREDICATE_RESULT",
                                  "BENCHMARK_CONSTRUCTION"),
    "outcome": enum("ACCEPTED", "FIRST_FAILURE", "EXHAUSTED"),
    "first_failure_code": nullable(SYM),
    "no_redraw_after_acceptance": {"const": True},
})

add("PROPOSAL_TRACE_RECEIPT", "PROPOSAL_TRACE_REDUCER", {
    "run_id": ID,
    "proposal_ordinal": integer(),
    "design_lock_ref": artifact_ref("PRE_ENTROPY_DESIGN_LOCK", "PRE_ENTROPY_DESIGN_LOCK",
                                    "BENCHMARK_CONSTRUCTION"),
    "entropy_receipt_ref": artifact_ref("ENTROPY_ACQUISITION", "ENTROPY_ACQUISITION_RECEIPT",
                                        "BENCHMARK_CONSTRUCTION"),
    "recipient_bundle_ref": artifact_ref("RECIPIENT_BUNDLE", "RECIPIENT_BUNDLE",
                                         "BENCHMARK_CONSTRUCTION"),
    "donor_bundle_ref": artifact_ref("DONOR_BUNDLE", "DONOR_BUNDLE", "BENCHMARK_CONSTRUCTION"),
    "decoded_proposal_ref": artifact_ref("DECODED_PROPOSAL", "DECODED_PROPOSAL",
                                         "BENCHMARK_CONSTRUCTION"),
    "predicate_result_refs": refs("ACCEPTANCE_PREDICATE_RESULT", "ACCEPTANCE_PREDICATE_RESULT",
                                  "BENCHMARK_CONSTRUCTION"),
    "first_failure_or_exhaustion_ref": artifact_ref(
        "FIRST_FAILURE_OR_EXHAUSTION", "FIRST_FAILURE_OR_EXHAUSTION_RECEIPT",
        "BENCHMARK_CONSTRUCTION"
    ),
    "accepted": {"type": "boolean"},
})

add("COMMON_SEED_BUNDLE", "SEED_ASSIGNER", {
    "run_id": ID,
    "sample_ordinal": integer(),
    "recipient_life_id": ID,
    "design_lock_ref": artifact_ref("PRE_ENTROPY_DESIGN_LOCK", "PRE_ENTROPY_DESIGN_LOCK",
                                    "SEED_ASSIGNMENT"),
    "entropy_receipt_ref": artifact_ref("ENTROPY_ACQUISITION", "ENTROPY_ACQUISITION_RECEIPT",
                                        "SEED_ASSIGNMENT"),
    "seed_derivation_algorithm": {"const": "DOMAIN_SEPARATED_SHA256_TO_UINT64_V1"},
    "ordered_entry_keys": arr(BYTES, 1, unique=True),
})

add("LIFE_SAMPLE_RECEIPT", "LIFE_SAMPLER", {
    "run_id": ID,
    "sample_ordinal": integer(),
    "recipient_life_id": ID,
    "status": {"const": "ACCEPTED"},
    "design_lock_ref": artifact_ref("PRE_ENTROPY_DESIGN_LOCK", "PRE_ENTROPY_DESIGN_LOCK",
                                    "LIFE_SAMPLING"),
    "entropy_receipt_ref": artifact_ref("ENTROPY_ACQUISITION", "ENTROPY_ACQUISITION_RECEIPT",
                                        "LIFE_SAMPLING"),
    "proposal_trace_ref": artifact_ref("PROPOSAL_TRACE", "PROPOSAL_TRACE_RECEIPT", "LIFE_SAMPLING"),
    "recipient_bundle_ref": artifact_ref("RECIPIENT_BUNDLE", "RECIPIENT_BUNDLE", "LIFE_SAMPLING"),
    "donor_bundle_ref": artifact_ref("DONOR_BUNDLE", "DONOR_BUNDLE", "LIFE_SAMPLING"),
    "common_seed_bundle_ref": artifact_ref("COMMON_SEED_BUNDLE", "COMMON_SEED_BUNDLE", "LIFE_SAMPLING"),
    "ordered_gate_ids": arr(SYM, 1, unique=True),
    "ordered_lower_unit_ids": arr(ID, 1, unique=True),
})

add("PUBLIC_STATE_SNAPSHOT", "PUBLIC_STATE_SNAPSHOT_BUILDER", {
    "run_id": ID,
    "recipient_life_id": ID,
    "sample_ordinal": integer(),
    "step_ordinal": integer(),
    "life_sample_ref": artifact_ref(
        "LIFE_SAMPLE", "LIFE_SAMPLE_RECEIPT", "PUBLIC_STATE_SNAPSHOT"),
    "prior_emission_ref": nullable(artifact_ref(
        "INTERVENTION_EMISSION", "INTERVENTION_EMISSION_RECEIPT",
        "PUBLIC_STATE_SNAPSHOT", cardinality="OPTIONAL_ONE")),
    "public_view_body": {"$ref": "#/$defs/public_view_body"},
    "causally_prior_ledger_head_sha256": H,
})

add("COMMON_SEED_ENTRY_RECEIPT", "SEED_ASSIGNER", {
    "run_id": ID,
    "recipient_life_id": ID,
    "sample_ordinal": integer(),
    "call_role": SYM,
    "call_ordinal": integer(),
    "seed_uint64": integer(0, 18446744073709551615),
    "parent_seed_bundle_ref": artifact_ref("COMMON_SEED_BUNDLE", "COMMON_SEED_BUNDLE",
                                           "SEED_ASSIGNMENT"),
    "life_sample_ref": artifact_ref("LIFE_SAMPLE", "LIFE_SAMPLE_RECEIPT", "SEED_ASSIGNMENT"),
    "derivation_input_sha256": H,
})

add("RESOLVED_D1A_SAFETY_TRIAL_REGISTRY", "SAFETY_KEY_RESOLVER", {
    "run_id": ID,
    "design_lock_ref": artifact_ref("PRE_ENTROPY_DESIGN_LOCK", "PRE_ENTROPY_DESIGN_LOCK",
                                    "SAFETY_KEY_RESOLUTION"),
    "life_sample_refs": refs("LIFE_SAMPLE", "LIFE_SAMPLE_RECEIPT", "SAFETY_KEY_RESOLUTION"),
    "resolved_keys": arr({"$ref": "#/$defs/resolved_safety_key"}, 2),
    "resolution_algorithm": {"const": "ORDINAL_TEMPLATE_TO_REALIZED_ID_BIJECTION_V1"},
    "selection_inputs": tuple_of(
        {"const": "SAMPLE_ORDINAL"}, {"const": "ARM_ROLE"},
        {"const": "ENDPOINT_ID"}, {"const": "LOWER_UNIT_ORDINAL"}
    ),
    "outcome_or_content_inputs_forbidden": {"const": True},
    "template_resolution_is_bijective": {"const": True},
})


# R11: one D1A control object per life plus one exact manifest.
add("D1A_CONTROL_SET_RECEIPT", "D1A_CONTROL_BUILDER", {
    "run_id": ID,
    "sample_ordinal": integer(),
    "recipient_life_id": ID,
    "life_sample_ref": artifact_ref("LIFE_SAMPLE", "LIFE_SAMPLE_RECEIPT", "D1A_CONTROL_CONSTRUCTION"),
    "design_lock_ref": artifact_ref("PRE_ENTROPY_DESIGN_LOCK", "PRE_ENTROPY_DESIGN_LOCK",
                                    "D1A_CONTROL_CONSTRUCTION"),
    "membership_template_sha256": H,
    "ordered_arms": tuple_of(
        {"allOf": [{"$ref": "#/$defs/control_arm"}, {"properties": {"role": {"const": "AUTHENTIC"}}}]},
        {"allOf": [{"$ref": "#/$defs/control_arm"}, {"properties": {"role": {"const": "WRONG_LIFE"}}}]},
        {"allOf": [{"$ref": "#/$defs/control_arm"}, {"properties": {"role": {"const": "BINDING_DERANGED"}}}]},
    ),
    "wrong_life_match_proof_sha256": H,
    "binding_derangement_proof_sha256": H,
    "dose_opportunity_match_proof_sha256": H,
    "recipient_donor_exclusion_verified": {"const": True},
    "replacement_forbidden": {"const": True},
})

add("D1A_CONTROL_SET_MANIFEST", "D1A_CONTROL_MANIFEST_REDUCER", {
    "run_id": ID,
    "design_lock_ref": artifact_ref("PRE_ENTROPY_DESIGN_LOCK", "PRE_ENTROPY_DESIGN_LOCK",
                                    "D1A_CONTROL_MANIFEST"),
    "life_sample_refs": refs("D1A_LIFE_SAMPLE", "LIFE_SAMPLE_RECEIPT", "D1A_CONTROL_MANIFEST"),
    "control_set_refs": refs("D1A_CONTROL_SET", "D1A_CONTROL_SET_RECEIPT", "D1A_CONTROL_MANIFEST"),
    "ordered_sample_ordinals": arr(integer(), 1, unique=True),
    "membership_and_sample_set_equality": {"const": True},
    "one_control_set_per_d1a_life": {"const": True},
    "duplicate_recipient_or_donor_substitution_forbidden": {"const": True},
})


# R05/R06: semantic registries are distinct typed objects.  Shared row shapes
# reduce boilerplate without merging their artifact identities.
SEMANTIC_REGISTRIES = (
    "CONTROLLER_REGISTRY", "TRANSITION_CAUSE_REGISTRY", "STATUS_REGISTRY",
    "VISIBILITY_REGISTRY", "GATE_REGISTRY", "EVIDENCE_ROLE_REGISTRY",
    "DEPENDENCY_REGISTRY", "CLAIM_REGISTRY", "RESOURCE_REGISTRY",
    "OBJECT_INVENTORY_REGISTRY", "CONTRACT_SCHEMA_REGISTRY",
    "ALLOWED_DISPATCH_REGISTRY", "AUTHORITY_REGISTRY",
)

defs["semantic_registry_refs"] = closed({
    name.lower() + "_ref": artifact_ref(name, name, "SEMANTIC_REGISTRY_BINDING", run_bound=False)
    for name in SEMANTIC_REGISTRIES
})

add("CONTROLLER_REGISTRY", "CONTROLLER_REGISTRY_AUTHOR", {
    "architecture_id": {"const": ARCHITECTURE_ID},
    "terminal_error_count": {"const": 3},
    "dispatch_input_counts": tuple_of({"const": 0}, {"const": 1}, {"const": 2}),
    "queue_effect_is_result_specific": {"const": True},
    "rows": arr({"$ref": "#/$defs/controller_row"}, 1),
    "reachable_state_universe_sha256": H,
    "reachable_state_count": integer(1),
    "phase_rule_count": integer(1),
    "reachable_state_definition": {
        "const": "ONE_ROW_X_ONE_EXPLICIT_COUNTER_INPUT_X_ONE_ACCEPTED_RESULT_X_ONE_REACHABLE_QUEUE_CLASS"
    },
    "zero_or_multiple_transition_matches_rejected": {"const": True},
})

add("TRANSITION_CAUSE_REGISTRY", "TRANSITION_CAUSE_REGISTRY_AUTHOR", {
    "architecture_id": {"const": ARCHITECTURE_ID},
    "rows": arr({"$ref": "#/$defs/transition_cause_row"}, 7, 7),
    "cause_order": tuple_of(*[{"const": value} for value in (
        "MODEL_DISPATCH", "DIRECT_PROVIDER", "CONTROLLER_PHASE", "QUEUE_FLUSH",
        "QUEUE_DISCARD", "COMMITTED_ACTION", "HARNESS_TERMINAL",
    )]),
    "exact_cardinality": {"const": True},
})

(
    VISIBILITY_INFORMATION_ITEMS,
    VISIBILITY_STAGES,
    VISIBILITY_CELLS,
    VISIBILITY_ALLOWED_EDGES,
) = build_visibility_catalog()

visibility_access_variants: list[dict[str, Any]] = []
for edge in VISIBILITY_ALLOWED_EDGES:
    source_is_run_bound = edge["source_type"] != "CLAIM_REGISTRY"
    visibility_access_variants.append({
        "properties": {
            "edge_ordinal": {"const": edge["ordinal"]},
            "information_item": {"const": edge["information_item"]},
            "information_ordinal": {"const": edge["information_ordinal"]},
            "consumer_stage": {"const": edge["consumer_stage"]},
            "stage_ordinal": {"const": edge["stage_ordinal"]},
            "visibility": {"const": edge["visibility"]},
            "rationale": {"const": edge["rationale"]},
            "concrete_role": {"const": edge["concrete_role"]},
            "source_ref": artifact_ref(
                edge["concrete_role"], edge["source_type"],
                "VISIBILITY_STAGE_INGRESS", edge["ordinal"],
                run_bound=source_is_run_bound),
            "source_binding_class": {
                "const": "SAME_RUN" if source_is_run_bound else "ARCHITECTURE_BOUND"
            },
            "source_type": {"const": edge["source_type"]},
            "source_field_path": {"const": edge["source_field_path"]},
            "projection_algorithm": {"const": edge["projection_algorithm"]},
            "output_type": {"const": "VISIBILITY_ACCESS_RECEIPT"},
            "output_field_path": {"const": "projected_value_canonical_json"},
            "cardinality": {"const": "ONE"},
        }
    })

add("VISIBILITY_ACCESS_RECEIPT", "VISIBILITY_STAGE_INGRESS_BUILDER", {
    "run_id": ID,
    "edge_ordinal": integer(0, 83),
    "information_item": enum(*VISIBILITY_INFORMATION_ITEMS),
    "information_ordinal": integer(0, len(VISIBILITY_INFORMATION_ITEMS) - 1),
    "consumer_stage": enum(*VISIBILITY_STAGES),
    "stage_ordinal": integer(0, len(VISIBILITY_STAGES) - 1),
    "visibility": enum("VISIBLE", "DERIVED_ONLY"),
    "rationale": BYTES,
    "concrete_role": SYM,
    # Each oneOf branch below closes this generic required field to one typed
    # source artifact reference.  It is deliberately not a catalog-only
    # annotation: this receipt is the stage ingress object.
    "source_ref": {"type": "object"},
    "source_binding_class": enum("SAME_RUN", "ARCHITECTURE_BOUND"),
    "source_type": SYM,
    "source_field_path": BYTES,
    "source_value_sha256": H,
    "projection_algorithm": SYM,
    "projected_value_canonical_json": BYTES,
    "projected_value_sha256": H,
    "output_type": {"const": "VISIBILITY_ACCESS_RECEIPT"},
    "output_field_path": {"const": "projected_value_canonical_json"},
    "cardinality": {"const": "ONE"},
    "pure_deterministic_projection_verified": {"const": True},
    "undeclared_source_fields_absent": {"const": True},
}, one_of=visibility_access_variants, description=(
    "Concrete stage-ingress receipt. Each branch consumes one exact typed source field and "
    "carries the visible or pure-derived bytes delivered to the named consumer stage."
))

add("VISIBILITY_REGISTRY", "VISIBILITY_REGISTRY_AUTHOR", {
    "architecture_id": {"const": ARCHITECTURE_ID},
    "information_item_order": {"const": VISIBILITY_INFORMATION_ITEMS},
    "stage_order": {"const": VISIBILITY_STAGES},
    "cells": {"const": VISIBILITY_CELLS},
    "allowed_edges": {"const": VISIBILITY_ALLOWED_EDGES},
    "allowed_edge_count": {"const": 84},
    "r8_preexisting_allowed_edge_count": {"const": 83},
    "sole_emission_to_think_role": {"const": "INTERVENTION_EMISSION_TO_PUBLIC_VIEW"},
    "schema_edge_extractor_ref": raw_ref("RAW_SCHEMA_EDGE_EXTRACTOR", "VISIBILITY_AUDIT",
                                          run_bound=False),
    "inventory_edge_extractor_ref": raw_ref("RAW_INVENTORY_EDGE_EXTRACTOR", "VISIBILITY_AUDIT",
                                             run_bound=False),
    "visibility_edge_extractor_ref": raw_ref("RAW_VISIBILITY_EDGE_EXTRACTOR", "VISIBILITY_AUDIT",
                                              run_bound=False),
    "audit_only_exclusions": arr(BYTES),
})

for registry_name in (
    "STATUS_REGISTRY", "GATE_REGISTRY", "EVIDENCE_ROLE_REGISTRY", "DEPENDENCY_REGISTRY",
    "CLAIM_REGISTRY", "RESOURCE_REGISTRY", "ALLOWED_DISPATCH_REGISTRY", "AUTHORITY_REGISTRY",
):
    add(registry_name, registry_name + "_AUTHOR", {
        "architecture_id": {"const": ARCHITECTURE_ID},
        "registry_kind": {"const": registry_name},
        "ordered_row_keys": arr(SYM, 1, unique=True),
        "rows": arr({"$ref": "#/$defs/registry_row"}, 1),
        "row_key_set_equality": {"const": True},
    })

# Exact claim renderings, rather than an opaque claim-map blob, are part of the
# typed CLAIM_REGISTRY surface and can be the source of concrete visibility edges.
claim_registry_properties = defs["claim_registry"]["properties"]
claim_registry_properties["claim_renderings"] = tuple_of(
    *[{"$ref": "#/$defs/claim_rendering"} for _ in CLAIM_TEXTS]
)
defs["claim_registry"]["required"].append("claim_renderings")

add("CONTRACT_SCHEMA_REGISTRY", "CONTRACT_SCHEMA_EXTRACTOR", {
    "architecture_id": {"const": ARCHITECTURE_ID},
    "registry_kind": {"const": "CONTRACT_SCHEMA_REGISTRY"},
    "raw_schema_ref": raw_ref("RAW_CONTRACT_SCHEMA", "STATIC_AUDIT", run_bound=False),
    "schema_id": {"const": SCHEMA_ID},
    "top_level_artifact_types": arr(SYM, 1, unique=True),
    "local_refs_recursively_closed": {"const": True},
    "unknown_type_policy": {"const": "REJECT"},
})

# The checked-in object_inventory.json is itself an instance of this type.
add("OBJECT_INVENTORY_REGISTRY", "INVENTORY_EXTRACTOR", {
    "architecture_id": {"const": ARCHITECTURE_ID},
    "closed_world": {"const": True},
    "unknown_type_policy": {"const": "REJECT"},
    "canonical_json": {"const": CANONICAL_JSON},
    "self_hash_algorithm": {"const": SELF_HASH_ALGORITHM},
    "schema_bundle": {"const": SCHEMA_ID},
    "schema_raw_sha256": H,
    "generator": {"const": "build_contract_schema.py"},
    "generator_raw_sha256": H,
    "source_consensus_sha256": {"const": R8_CONSENSUS_SHA256},
    "objects": arr({"$ref": "#/$defs/inventory_object"}, 1),
})


# The populated lock binds realized layers and exact registry types; raw byte
# manifests are never used as a registry substitute.
add("POPULATED_RUN_LOCK", "RUN_LOCK_REDUCER", {
    "run_id": ID,
    "design_lock_ref": artifact_ref("PRE_ENTROPY_DESIGN_LOCK", "PRE_ENTROPY_DESIGN_LOCK", "RUN_LOCK"),
    "entropy_receipt_ref": artifact_ref("ENTROPY_ACQUISITION", "ENTROPY_ACQUISITION_RECEIPT", "RUN_LOCK"),
    "proposal_trace_refs": refs("PROPOSAL_TRACE", "PROPOSAL_TRACE_RECEIPT", "RUN_LOCK"),
    "life_sample_refs": refs("LIFE_SAMPLE", "LIFE_SAMPLE_RECEIPT", "RUN_LOCK"),
    "resolved_safety_registry_ref": artifact_ref(
        "RESOLVED_D1A_SAFETY_TRIAL_REGISTRY", "RESOLVED_D1A_SAFETY_TRIAL_REGISTRY", "RUN_LOCK"
    ),
    "d1a_control_manifest_ref": artifact_ref("D1A_CONTROL_SET_MANIFEST", "D1A_CONTROL_SET_MANIFEST",
                                             "RUN_LOCK"),
    "common_seed_bundle_refs": refs("COMMON_SEED_BUNDLE", "COMMON_SEED_BUNDLE", "RUN_LOCK"),
    "common_seed_entry_refs": refs("COMMON_SEED_ENTRY", "COMMON_SEED_ENTRY_RECEIPT", "RUN_LOCK"),
    "semantic_registry_refs": {"$ref": "#/$defs/semantic_registry_refs"},
    "sample_ordinals_equal_design_membership": {"const": True},
    "safety_templates_equal_resolved_keys": {"const": True},
    "control_manifest_equal_d1a_membership": {"const": True},
    "seed_entries_equal_dispatch_plan": {"const": True},
    "implicit_defaults_forbidden": {"const": True},
})


# R07/R08: privileged route, sanitized projection, public emission, and typed
# seed/life/view/dispatch ancestry.  The controller never receives the route or
# projection types; its only response-completion capability is emission.
add("OPAQUE_LINEAGE_ALLOCATION_RECEIPT", "PRIVILEGED_NONCE_ALLOCATOR", {
    "run_id": ID,
    "opaque_instance_id": ID,
    "entropy_receipt_ref": artifact_ref("ENTROPY_ACQUISITION", "ENTROPY_ACQUISITION_RECEIPT",
                                        "PRIVILEGED_ROUTING"),
    "entropy_slice_domain": {"const": "OPAQUE_LINEAGE_NONCE"},
    "entropy_slice_ordinal": integer(),
    "nonce_bytes_hex": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
    "canonical_preimage": BYTES,
    "commitment_algorithm": {"const": "SHA256(PPC5R9_OPAQUE_LINEAGE_V1 || NUL || CANONICAL_PREIMAGE)"},
    "opaque_commitment": H,
})

add("PRIVILEGED_ROUTE_RECEIPT", "PRIVILEGED_ROUTE_RESOLVER", {
    "run_id": ID,
    "opaque_instance_id": ID,
    "lineage_allocation_ref": artifact_ref("OPAQUE_LINEAGE_ALLOCATION", "OPAQUE_LINEAGE_ALLOCATION_RECEIPT",
                                           "PRIVILEGED_ROUTING"),
    "condition_semantics": BYTES,
    "source_identity": ID,
    "match_keys_canonical_json": BYTES,
    "provider_scores_canonical_json": BYTES,
    "route_mapping_canonical_json": BYTES,
    "resolved_candidate_public_bytes": BYTES,
})

add("SANITIZED_RESPONSE_PROJECTION", "SANITIZED_PROJECTION_BUILDER", {
    "run_id": ID,
    "opaque_instance_id": ID,
    # No reference or capability to the privileged route crosses this
    # boundary.  Equality/provenance is established by the separate privileged
    # and public audit receipts via the shared opaque commitment.
    "opaque_commitment": H,
    "resolved_public_bytes": BYTES,
    "input_length_class": SYM,
    "output_length_class": SYM,
    "debit_class": SYM,
    "condition_route_source_match_score_nonce_mapping_absent": {"const": True},
})

add("INTERVENTION_EMISSION_RECEIPT", "PUBLIC_EMITTER", {
    "run_id": ID,
    "opaque_instance_id": ID,
    "projection_ref": artifact_ref("SANITIZED_RESPONSE_PROJECTION", "SANITIZED_RESPONSE_PROJECTION",
                                   "PUBLIC_EMISSION"),
    "opaque_commitment": H,
    "emitted_public_bytes": BYTES,
    "emitted_public_bytes_sha256": H,
    "emitted_byte_equality_to_projection": {"const": True},
    "privileged_metadata_absent": {"const": True},
})

add("ROUTE_LINEAGE_AUDIT_RECEIPT", "PRIVILEGED_AUDITOR", {
    "run_id": ID,
    "route_ref": artifact_ref("PRIVILEGED_ROUTE", "PRIVILEGED_ROUTE_RECEIPT", "PRIVILEGED_AUDIT"),
    "lineage_allocation_ref": artifact_ref("OPAQUE_LINEAGE_ALLOCATION", "OPAQUE_LINEAGE_ALLOCATION_RECEIPT",
                                           "PRIVILEGED_AUDIT"),
    "projection_ref": artifact_ref("SANITIZED_RESPONSE_PROJECTION",
                                    "SANITIZED_RESPONSE_PROJECTION", "PRIVILEGED_AUDIT"),
    "opaque_instance_id_equality": {"const": True},
    "opaque_commitment_equality": {"const": True},
    "resolved_public_bytes_equality": {"const": True},
    "projection_privileged_reference_absent": {"const": True},
    "route_lineage_complete": {"const": True},
})

add("PROVIDER_AUDIT_RECEIPT", "PROVIDER_AUDITOR", {
    "run_id": ID,
    "provider_call_id": ID,
    "opaque_instance_id": ID,
    "raw_provider_trace_ref": raw_ref("RAW_PROVIDER_TRACE", "PROVIDER_AUDIT", run_bound=True),
    "public_result_sha256": H,
    "debit_class": SYM,
    "provider_call_complete": {"const": True},
})

add("MODEL_VIEW", "MODEL_VIEW_RENDERER", {
    "run_id": ID,
    "recipient_life_id": ID,
    "sample_ordinal": integer(),
    "step_ordinal": integer(),
    "call_role": SYM,
    "call_ordinal": integer(),
    "life_sample_ref": artifact_ref("LIFE_SAMPLE", "LIFE_SAMPLE_RECEIPT", "MODEL_VIEW_RENDER"),
    "public_state_snapshot_ref": artifact_ref(
        "PUBLIC_STATE_SNAPSHOT", "PUBLIC_STATE_SNAPSHOT", "MODEL_VIEW_RENDER"),
    "response_think_ingress_ref": nullable(artifact_ref(
        "INTERVENTION_EMISSION_TO_PUBLIC_VIEW", "VISIBILITY_ACCESS_RECEIPT",
        "MODEL_VIEW_RENDER", cardinality="OPTIONAL_ONE")),
    "public_view_body": {"$ref": "#/$defs/public_view_body"},
    "public_view_body_equals_snapshot_plus_optional_emission": {"const": True},
    "ledger_head_sha256": H,
    "rendered_input_bytes": BYTES,
    "rendered_input_sha256": H,
    "emission_to_last_read_to_model_view_only": {"const": True},
})

add("DISPATCH_PREFLIGHT_RECEIPT", "DISPATCH_PREFLIGHT_REDUCER", {
    "run_id": ID,
    "recipient_life_id": ID,
    "sample_ordinal": integer(),
    "step_ordinal": integer(),
    "call_role": SYM,
    "call_ordinal": integer(),
    "pre_model_authority_ref": artifact_ref(
        "PRE_MODEL_AUTHORITY", "PRE_MODEL_AUTHORITY_RECEIPT",
        "DISPATCH_PREFLIGHT"),
    "allowed_dispatch_registry_ref": artifact_ref(
        "ALLOWED_DISPATCH_REGISTRY", "ALLOWED_DISPATCH_REGISTRY",
        "DISPATCH_PREFLIGHT", run_bound=False),
    "dispatch_registry_entry_ordinal": integer(),
    "dispatch_registry_entry_canonical_json": BYTES,
    "exact_run_package_sha256": H,
    "model_sha256": H,
    "adapter_sha256": nullable(H),
    "tokenizer_sha256": H,
    "prompt_sha256": H,
    "data_sha256": H,
    "seed_entry_sha256": H,
    "model_view_sha256": H,
    "all_immediate_hashes_equal_allowed_dispatch_entry": {"type": "boolean"},
    "premodel_chain_recomputed_and_granted": {"type": "boolean"},
    "stale_missing_duplicate_wrong_run_type_role_order_or_cardinality_absent": {
        "type": "boolean"
    },
    "decision": enum("PERMIT", "DENY"),
    "process_started": {"type": "boolean"},
    "denial_reason": nullable(SYM),
}, one_of=[
    {"properties": {
        "decision": {"const": "PERMIT"},
        "all_immediate_hashes_equal_allowed_dispatch_entry": {"const": True},
        "premodel_chain_recomputed_and_granted": {"const": True},
        "stale_missing_duplicate_wrong_run_type_role_order_or_cardinality_absent": {"const": True},
        "process_started": {"const": True},
        "denial_reason": {"type": "null"},
    }},
    {"properties": {
        "decision": {"const": "DENY"},
        "process_started": {"const": False},
    }},
])

add("MODEL_DISPATCH_RECEIPT", "MODEL_DISPATCHER", {
    "run_id": ID,
    "recipient_life_id": ID,
    "sample_ordinal": integer(),
    "step_ordinal": integer(),
    "call_role": SYM,
    "call_ordinal": integer(),
    "life_sample_ref": artifact_ref("LIFE_SAMPLE", "LIFE_SAMPLE_RECEIPT", "MODEL_DISPATCH"),
    "common_seed_entry_ref": artifact_ref("COMMON_SEED_ENTRY", "COMMON_SEED_ENTRY_RECEIPT",
                                          "MODEL_DISPATCH"),
    "model_view_ref": artifact_ref("MODEL_VIEW", "MODEL_VIEW", "MODEL_DISPATCH"),
    "preflight_ref": artifact_ref(
        "DISPATCH_PREFLIGHT_PERMIT", "DISPATCH_PREFLIGHT_RECEIPT",
        "MODEL_DISPATCH"),
    "preflight_decision_verified_permit": {"const": True},
    "model_ref": raw_ref("RAW_MODEL_BYTES", "MODEL_DISPATCH", run_bound=True),
    "tokenizer_ref": raw_ref("RAW_TOKENIZER_BYTES", "MODEL_DISPATCH", run_bound=True),
    "prompt_ref": raw_ref("RAW_PROMPT_BYTES", "MODEL_DISPATCH", run_bound=True),
    "rendered_seed_uint64": integer(0, 18446744073709551615),
    "seed_equals_entry": {"const": True},
    "raw_output_ref": raw_ref("RAW_MODEL_OUTPUT", "MODEL_DISPATCH", run_bound=True),
    "input_token_ids": arr(integer()),
    "output_token_ids": arr(integer()),
    "status": enum("RETURNED", "MODEL_MISSING_NO_RETRY", "TOKEN_LIMIT", "PARSE_ERROR"),
    "debit": {"$ref": "#/$defs/budget"},
})

add("COMPLETE_MODEL_VIEW_MANIFEST", "MODEL_VIEW_MANIFEST_REDUCER", {
    "run_id": ID,
    "public_state_snapshot_refs": refs(
        "PUBLIC_STATE_SNAPSHOT", "PUBLIC_STATE_SNAPSHOT", "REPLAY_RETENTION"),
    "visibility_access_refs": refs(
        "VISIBILITY_ACCESS", "VISIBILITY_ACCESS_RECEIPT", "REPLAY_RETENTION"),
    "model_view_refs": refs("MODEL_VIEW", "MODEL_VIEW", "REPLAY_RETENTION"),
    "model_dispatch_refs": refs("MODEL_DISPATCH", "MODEL_DISPATCH_RECEIPT", "REPLAY_RETENTION"),
    "canonical_order": tuple_of(
        {"const": "RUN_ID"}, {"const": "RECIPIENT_LIFE_ID"}, {"const": "SAMPLE_ORDINAL"},
        {"const": "STEP_ORDINAL"}, {"const": "CALL_ROLE"}, {"const": "CALL_ORDINAL"}
    ),
    "view_set_equals_all_dispatch_view_refs": {"const": True},
    "every_model_view_input_is_authorized_by_visibility_access": {"const": True},
})


# R01: result-specific queue behavior and typed no-model finalization.
add("OPERATION_RESULT_RECEIPT", "OPERATION_RESULT_NORMALIZER", {
    "run_id": ID,
    "dispatch_ref": artifact_ref("MODEL_DISPATCH", "MODEL_DISPATCH_RECEIPT", "CONTROLLER"),
    "result": SYM,
    "result_class": enum("SUCCESS", "MISSING", "ERROR"),
    "canonical_result_bytes": BYTES,
})

transition_cases: list[dict[str, Any]] = []
for before in range(3):
    transition_cases.append({
        "properties": {
            "counter_transition": {"properties": {"result_class": {"const": "SUCCESS"},
                                                       "before": {"const": before},
                                                       "public_after": {"const": 0},
                                                       "private_after": {"const": 0}}},
            "normalized_result": SYM,
        }
    })
    transition_cases.append({
        "properties": {
            "counter_transition": {"properties": {"result_class": {"const": "MISSING"},
                                                       "before": {"const": before},
                                                       "public_after": {"const": before},
                                                       "private_after": {"const": before}}},
            "result_specific_queue_effect": {"enum": ["NONE", "FLUSH", "FINALIZE_QUEUE"]},
        }
    })
    error_properties: dict[str, Any] = {
        "counter_transition": {"properties": {"result_class": {"const": "ERROR"},
                                                   "before": {"const": before},
                                                   "public_after": {"const": before + 1},
                                                   "private_after": {"const": before + 1}}},
        "result_specific_queue_effect": {"enum": ["NONE", "FINALIZE_QUEUE"]},
    }
    if before == 2:
        error_properties.update({
            "normalized_result": {"const": "ERROR_LIMIT"},
            "terminal_intent": {"const": True},
        })
    transition_cases.append({"properties": error_properties})

add("CONTROLLER_TRANSITION_RECEIPT", "CONTROLLER_REDUCER", {
    "run_id": ID,
    "controller_registry_ref": artifact_ref("CONTROLLER_REGISTRY", "CONTROLLER_REGISTRY", "CONTROLLER",
                                             run_bound=False),
    "operation_result_ref": artifact_ref("OPERATION_RESULT", "OPERATION_RESULT_RECEIPT", "CONTROLLER"),
    "emission_completion_ref": nullable(artifact_ref(
        "INTERVENTION_EMISSION", "INTERVENTION_EMISSION_RECEIPT", "CONTROLLER",
        cardinality="OPTIONAL_ONE"
    )),
    "matched_row_key": SYM,
    "counter_transition": {"$ref": "#/$defs/counter_transition"},
    "normalized_result": SYM,
    "next_phase": SYM,
    "terminal_intent": {"type": "boolean"},
    "outstanding_queued_slot_count": integer(),
    "result_specific_queue_effect": enum("NONE", "ENQUEUE", "FLUSH", "FINALIZE_QUEUE"),
    "controller_has_route_or_projection_access": {"const": False},
}, one_of=transition_cases)

add("QUEUE_SLOT_RECEIPT", "QUEUE_MANAGER", {
    "run_id": ID,
    "slot_ordinal": integer(),
    "state": enum("QUEUED", "FLUSHED", "DISCARDED", "REJECTED"),
    "controller_transition_ref": artifact_ref("CONTROLLER_TRANSITION", "CONTROLLER_TRANSITION_RECEIPT",
                                              "QUEUE_MANAGER"),
    "queued_request_sha256": nullable(H),
    "opaque_commitment": nullable(H),
})

add("QUEUE_EFFECT_RECEIPT", "QUEUE_MANAGER", {
    "run_id": ID,
    "slot_ordinal": integer(),
    "effect": enum("FLUSHED", "DISCARDED"),
    "queued_slot_ref": artifact_ref("QUEUED_SLOT", "QUEUE_SLOT_RECEIPT", "QUEUE_MANAGER"),
    "controller_transition_ref": artifact_ref("CONTROLLER_TRANSITION", "CONTROLLER_TRANSITION_RECEIPT",
                                              "QUEUE_MANAGER"),
    "emission_ref": nullable(artifact_ref("INTERVENTION_EMISSION", "INTERVENTION_EMISSION_RECEIPT",
                                          "QUEUE_MANAGER", cardinality="OPTIONAL_ONE")),
    "discard_reason": nullable(SYM),
})

add("QUEUE_FINALIZATION_RECEIPT", "NO_MODEL_QUEUE_FINALIZER", {
    "run_id": ID,
    "phase": {"const": "FINALIZE_QUEUE"},
    "terminal_transition_ref": artifact_ref("TERMINAL_INTENT", "CONTROLLER_TRANSITION_RECEIPT",
                                            "QUEUE_FINALIZER"),
    "outstanding_slot_refs": refs("OUTSTANDING_QUEUED_SLOT", "QUEUE_SLOT_RECEIPT", "QUEUE_FINALIZER"),
    "discard_effect_refs": refs("QUEUE_DISCARD", "QUEUE_EFFECT_RECEIPT", "QUEUE_FINALIZER"),
    "ordered_slot_set_equality": {"const": True},
    "all_effects_are_discard": {"const": True},
    "flushed_or_discarded_untouched": {"const": True},
    "rejected_slots_receive_no_effect": {"const": True},
    "model_dispatch_count": {"const": 0},
})

add("HARNESS_TERMINAL_RECEIPT", "HARNESS_TERMINALIZER", {
    "run_id": ID,
    "terminal_transition_ref": artifact_ref("TERMINAL_INTENT", "CONTROLLER_TRANSITION_RECEIPT",
                                            "HARNESS_TERMINAL"),
    "queue_finalization_ref": nullable(artifact_ref(
        "QUEUE_FINALIZATION", "QUEUE_FINALIZATION_RECEIPT", "HARNESS_TERMINAL",
        cardinality="OPTIONAL_ONE"
    )),
    "terminal_reason": SYM,
    "public_consecutive_error_count": integer(0, 3),
    "private_consecutive_error_count": integer(0, 3),
    "outstanding_queue_count": {"const": 0},
    "harness_terminal_transition_count": {"const": 1},
})


# R10: observations reduce completely within each life before N is counted.
add("OBSERVATION_RECEIPT", "OBSERVATION_RECORDER", {
    "run_id": ID,
    "key": {"$ref": "#/$defs/observation_key"},
    "life_sample_ref": artifact_ref("LIFE_SAMPLE", "LIFE_SAMPLE_RECEIPT", "OBSERVATION"),
    "condition_role": SYM,
    "value": nullable(RAT),
    "missing_event": nullable(SYM),
    "integrity_blocker": nullable(SYM),
})

add("LOWER_UNIT_COVERAGE_RECEIPT", "COVERAGE_REDUCER", {
    "run_id": ID,
    "gate_id": SYM,
    "sample_ordinal": integer(),
    "expected_lower_unit_ids": arr(ID, 1, unique=True),
    "treatment_observation_refs": refs("TREATMENT_OBSERVATION", "OBSERVATION_RECEIPT", "LIFE_REDUCER"),
    "control_observation_refs": refs("CONTROL_OBSERVATION", "OBSERVATION_RECEIPT", "LIFE_REDUCER"),
    "both_arm_key_sets_equal_expected": {"type": "boolean"},
    "first_failure": nullable(SYM),
})

add("LIFE_GATE_AGGREGATE", "LIFE_GATE_REDUCER", {
    "run_id": ID,
    "generator_law_sha256": H,
    "design_lock_ref": artifact_ref("PRE_ENTROPY_DESIGN_LOCK", "PRE_ENTROPY_DESIGN_LOCK",
                                    "LIFE_REDUCER"),
    "life_sample_ref": artifact_ref("LIFE_SAMPLE", "LIFE_SAMPLE_RECEIPT", "LIFE_REDUCER"),
    "gate_id": SYM,
    "sample_ordinal": integer(),
    "recipient_life_id": ID,
    "endpoint_id": SYM,
    "expected_ordered_lower_unit_ids": arr(ID, 1, unique=True),
    "treatment_condition_role": SYM,
    "control_condition_role": SYM,
    "treatment_observation_refs": refs("TREATMENT_OBSERVATION", "OBSERVATION_RECEIPT", "LIFE_REDUCER"),
    "control_observation_refs": refs("CONTROL_OBSERVATION", "OBSERVATION_RECEIPT", "LIFE_REDUCER"),
    "coverage_receipt_ref": artifact_ref("LOWER_UNIT_COVERAGE", "LOWER_UNIT_COVERAGE_RECEIPT",
                                         "LIFE_REDUCER"),
    "reduction_algorithm": {"const": "EQUAL_WEIGHT_COMPLETE_WITHIN_LIFE_V1"},
    "treatment_aggregate": nullable(RAT),
    "control_aggregate": nullable(RAT),
    "paired_difference": nullable(RAT),
    "z_i": enum(0, 1),
    "missing": {"type": "boolean"},
    "first_failure": nullable(SYM),
}, one_of=[
    {"properties": {"missing": {"const": True}, "treatment_aggregate": {"type": "null"},
                    "control_aggregate": {"type": "null"}, "paired_difference": {"type": "null"},
                    "z_i": {"const": 0}}},
    {"properties": {"missing": {"const": False}, "treatment_aggregate": RAT,
                    "control_aggregate": RAT, "paired_difference": RAT, "first_failure": {"type": "null"}}},
])

add("PAIRED_GATE_RESULT", "PAIRED_GATE_REDUCER", {
    "run_id": ID,
    "gate_id": SYM,
    "assay_id": enum("D1A", "D1B", "D1C", "D1D"),
    "life_gate_aggregate_refs": refs("LIFE_GATE_AGGREGATE", "LIFE_GATE_AGGREGATE", "GATE_REDUCER"),
    "ordered_distinct_sample_ordinals": arr(integer(), 1, unique=True),
    "n": integer(1),
    "n_definition": {"const": "COUNT_DISTINCT_PROSPECTIVELY_ASSIGNED_LIFE_GATE_AGGREGATES"},
    "raw_rows_calls_items_edges_never_increment_n": {"const": True},
    "success_count": integer(),
    "decision": enum("PASS", "FAIL", "BLOCKED"),
    "first_failure": nullable(SYM),
})

add("RESOURCE_ACCOUNTING_RECEIPT", "RESOURCE_REDUCER", {
    "run_id": ID,
    "event_count": integer(),
    "resource_totals_canonical_json": BYTES,
    "claim_role": {"const": "MANDATORY_DESCRIPTIVE_DOWNSTREAM_COSTS_ONLY"},
    "used_as_efficacy_component": {"const": False},
    "used_for_adjustment_conditioning_stratification_or_mediation": {"const": False},
    "used_to_rescue_failed_endpoint": {"const": False},
    "resource_qualification": {"const": RESOURCE_QUALIFICATION},
    "resource_qualification_sha256": {"const": sha256_bytes(RESOURCE_QUALIFICATION.encode("utf-8"))},
})

add("COMPLETE_RUN_MANIFEST", "RUN_MANIFEST_REDUCER", {
    "run_id": ID,
    "populated_run_lock_ref": artifact_ref("POPULATED_RUN_LOCK", "POPULATED_RUN_LOCK", "RUN_MANIFEST"),
    "pre_model_authority_ref": artifact_ref("PRE_MODEL_AUTHORITY", "PRE_MODEL_AUTHORITY_RECEIPT", "RUN_MANIFEST"),
    "life_sample_refs": refs("LIFE_SAMPLE", "LIFE_SAMPLE_RECEIPT", "RUN_MANIFEST"),
    "d1a_control_manifest_ref": artifact_ref("D1A_CONTROL_SET_MANIFEST", "D1A_CONTROL_SET_MANIFEST",
                                             "RUN_MANIFEST"),
    "common_seed_entry_refs": refs("COMMON_SEED_ENTRY", "COMMON_SEED_ENTRY_RECEIPT", "RUN_MANIFEST"),
    "model_view_manifest_ref": artifact_ref("COMPLETE_MODEL_VIEW_MANIFEST", "COMPLETE_MODEL_VIEW_MANIFEST",
                                             "RUN_MANIFEST"),
    "model_dispatch_refs": refs("MODEL_DISPATCH", "MODEL_DISPATCH_RECEIPT", "RUN_MANIFEST"),
    "emission_refs": refs("INTERVENTION_EMISSION", "INTERVENTION_EMISSION_RECEIPT", "RUN_MANIFEST"),
    "route_lineage_audit_refs": refs("ROUTE_LINEAGE_AUDIT", "ROUTE_LINEAGE_AUDIT_RECEIPT",
                                     "RUN_MANIFEST"),
    "provider_audit_refs": refs("PROVIDER_AUDIT", "PROVIDER_AUDIT_RECEIPT", "RUN_MANIFEST"),
    "controller_transition_refs": refs("CONTROLLER_TRANSITION", "CONTROLLER_TRANSITION_RECEIPT",
                                       "RUN_MANIFEST"),
    "queue_slot_refs": refs("QUEUE_SLOT", "QUEUE_SLOT_RECEIPT", "RUN_MANIFEST"),
    "queue_effect_refs": refs("QUEUE_EFFECT", "QUEUE_EFFECT_RECEIPT", "RUN_MANIFEST", minimum=0),
    "queue_finalization_refs": refs("QUEUE_FINALIZATION", "QUEUE_FINALIZATION_RECEIPT", "RUN_MANIFEST",
                                    minimum=0),
    "terminal_refs": refs("HARNESS_TERMINAL", "HARNESS_TERMINAL_RECEIPT", "RUN_MANIFEST"),
    "life_gate_aggregate_refs": refs("LIFE_GATE_AGGREGATE", "LIFE_GATE_AGGREGATE", "RUN_MANIFEST"),
    "paired_gate_result_refs": refs("PAIRED_GATE_RESULT", "PAIRED_GATE_RESULT", "RUN_MANIFEST"),
    "all_manifest_set_equalities_verified": {"const": True},
})

add("RUNTIME_INTEGRITY_RECEIPT", "RUNTIME_INTEGRITY_REDUCER", {
    "run_id": ID,
    "pre_model_authority_ref": artifact_ref(
        "PRE_MODEL_AUTHORITY", "PRE_MODEL_AUTHORITY_RECEIPT",
        "RUNTIME_INTEGRITY"),
    "allowed_dispatch_registry_ref": artifact_ref(
        "ALLOWED_DISPATCH_REGISTRY", "ALLOWED_DISPATCH_REGISTRY",
        "RUNTIME_INTEGRITY", run_bound=False),
    "preflight_refs": refs(
        "DISPATCH_PREFLIGHT", "DISPATCH_PREFLIGHT_RECEIPT",
        "RUNTIME_INTEGRITY"),
    "complete_run_manifest_ref": artifact_ref(
        "COMPLETE_RUN_MANIFEST", "COMPLETE_RUN_MANIFEST",
        "RUNTIME_INTEGRITY"),
    "model_view_manifest_ref": artifact_ref(
        "COMPLETE_MODEL_VIEW_MANIFEST", "COMPLETE_MODEL_VIEW_MANIFEST",
        "RUNTIME_INTEGRITY"),
    "route_lineage_audit_refs": refs(
        "ROUTE_LINEAGE_AUDIT", "ROUTE_LINEAGE_AUDIT_RECEIPT",
        "RUNTIME_INTEGRITY"),
    "provider_audit_refs": refs(
        "PROVIDER_AUDIT", "PROVIDER_AUDIT_RECEIPT", "RUNTIME_INTEGRITY"),
    "every_dispatch_has_exactly_one_prior_permit_preflight": {"const": True},
    "every_denial_started_no_process": {"const": True},
    "dispatch_view_seed_life_hash_closure": {"const": True},
    "complete_manifest_and_audit_set_equality": {"const": True},
    "status": enum("PASS", "FAIL"),
    "first_failure": nullable(SYM),
}, one_of=[
    {"properties": {"status": {"const": "PASS"},
                    "first_failure": {"type": "null"}}},
    {"properties": {"status": {"const": "FAIL"}}},
])


# R12: pointwise complete-run support and exact unconditional lower bound.
add("PATH_CONSTRUCTION_RECEIPT", "PATH_CONSTRUCTOR", {
    "run_id": ID,
    "sample_ordinal": integer(),
    "life_sample_ref": artifact_ref("LIFE_SAMPLE", "LIFE_SAMPLE_RECEIPT", "PATH_CONSTRUCTION"),
    "path_suite_sha256": H,
    "resolved_response_candidates_canonical_json": BYTES,
    "low_entropy_match_keys_canonical_json": BYTES,
    "every_edge_cut_twin_sham_complete": {"const": True},
})

add("OVERLAP_CONSTRUCTION_RECEIPT", "OVERLAP_REDUCER", {
    "run_id": ID,
    "life_sample_refs": refs("LIFE_SAMPLE", "LIFE_SAMPLE_RECEIPT", "OVERLAP_CONSTRUCTION"),
    "overlap_scope_canonical_json": BYTES,
    "accepted_constructible_population_only": {"const": True},
})

add("CONDITIONAL_COMPLETE_RELEASE_POWER_RESULT", "CONDITIONAL_POWER_REDUCER", {
    "run_id": ID,
    "construction_identity_sha256": H,
    "design_lock_ref": artifact_ref("PRE_ENTROPY_DESIGN_LOCK", "PRE_ENTROPY_DESIGN_LOCK",
                                    "CONDITIONAL_POWER"),
    "d1a_control_manifest_ref": artifact_ref("D1A_CONTROL_SET_MANIFEST", "D1A_CONTROL_SET_MANIFEST",
                                             "CONDITIONAL_POWER"),
    "life_membership_sha256": H,
    "gate_configuration_sha256": H,
    "holm_family": tuple_of(*[{"const": value} for value in (
        "PPC5_D1A_SUPPORTED_SELECTION", "PPC5_D1B_OBSERVABLE_EDGE_DEPENDENCE",
        "PPC5_D1C_DREAM_CONTEXT_POLICY", "PPC5_D1D_DREAM_TO_SLEEP_TOTAL_POLICY",
    )]),
    "conditional_complete_release_lower_bound": PROB,
    "exact_reduced_rational_arithmetic": {"const": True},
})

add("COMPLETE_RUN_CONSTRUCTION_SUPPORT_POINT", "CONSTRUCTION_SUPPORT_ENUMERATOR", {
    "run_id": ID,
    "support_ordinal": integer(),
    "design_lock_ref": artifact_ref("PRE_ENTROPY_DESIGN_LOCK", "PRE_ENTROPY_DESIGN_LOCK",
                                    "JOINT_POWER"),
    "recipient_bundle_refs": refs("RECIPIENT_BUNDLE", "RECIPIENT_BUNDLE", "JOINT_POWER"),
    "donor_bundle_refs": refs("DONOR_BUNDLE", "DONOR_BUNDLE", "JOINT_POWER"),
    "decoded_proposal_refs": refs("DECODED_PROPOSAL", "DECODED_PROPOSAL", "JOINT_POWER"),
    "predicate_result_refs": refs("ACCEPTANCE_PREDICATE_RESULT", "ACCEPTANCE_PREDICATE_RESULT",
                                  "JOINT_POWER"),
    "first_failure_or_exhaustion_refs": refs(
        "FIRST_FAILURE_OR_EXHAUSTION", "FIRST_FAILURE_OR_EXHAUSTION_RECEIPT", "JOINT_POWER"
    ),
    "path_construction_refs": refs("PATH_CONSTRUCTION", "PATH_CONSTRUCTION_RECEIPT", "JOINT_POWER"),
    "d1a_control_manifest_ref": artifact_ref("D1A_CONTROL_SET_MANIFEST", "D1A_CONTROL_SET_MANIFEST",
                                             "JOINT_POWER"),
    "overlap_construction_ref": artifact_ref("OVERLAP_CONSTRUCTION", "OVERLAP_CONSTRUCTION_RECEIPT",
                                             "JOINT_POWER"),
    "static_seal_pair_ref": artifact_ref("STATIC_SEAL_PAIR", "STATIC_SEAL_PAIR_RECEIPT", "JOINT_POWER"),
    "all_n_sample_ordinals_present": {"const": True},
    "proposal_traces_bounded_by_locked_limit": {"const": True},
    "exact_mass": PROB,
    "construction_succeeds": {"type": "boolean"},
    "conditional_power_ref": nullable(artifact_ref(
        "CONDITIONAL_COMPLETE_RELEASE_POWER", "CONDITIONAL_COMPLETE_RELEASE_POWER_RESULT", "JOINT_POWER",
        cardinality="OPTIONAL_ONE"
    )),
    "failed_point_contribution": PROB,
}, one_of=[
    {"properties": {"construction_succeeds": {"const": True},
                    "conditional_power_ref": artifact_ref(
                        "CONDITIONAL_COMPLETE_RELEASE_POWER", "CONDITIONAL_COMPLETE_RELEASE_POWER_RESULT",
                        "JOINT_POWER"
                    )}},
    {"properties": {"construction_succeeds": {"const": False},
                    "conditional_power_ref": {"type": "null"},
                    "failed_point_contribution": {"const": {
                        "numerator": 0, "denominator": 1, "reduced": True,
                        "within_unit_interval": True,
                    }}}},
])

add("JOINT_CONSTRUCTION_RELEASE_POWER_RECEIPT", "JOINT_POWER_REDUCER", {
    "run_id": ID,
    "design_lock_ref": artifact_ref("PRE_ENTROPY_DESIGN_LOCK", "PRE_ENTROPY_DESIGN_LOCK",
                                    "JOINT_POWER"),
    "support_point_refs": refs("COMPLETE_RUN_SUPPORT_POINT", "COMPLETE_RUN_CONSTRUCTION_SUPPORT_POINT",
                               "JOINT_POWER"),
    "proof_mode": enum("FINITE_EXACT", "CONSERVATIVE_PARTITION"),
    "covered_mass": PROB,
    "uncovered_mass": PROB,
    "uncovered_mass_contribution": {"const": {
        "numerator": 0, "denominator": 1, "reduced": True, "within_unit_interval": True,
    }},
    "joint_lower_bound": PROB,
    "calculation": {"const": "SUM_MASS_TIMES_SUCCESS_INDICATOR_TIMES_POINTWISE_CONDITIONAL_POWER"},
    "global_realized_power_substitution_forbidden": {"const": True},
    "independence_product_authority_forbidden": {"const": True},
    "exact_reduced_rational_arithmetic": {"const": True},
})

add("ANALYSIS_BUNDLE", "ANALYSIS_REDUCER", {
    "run_id": ID,
    "complete_run_manifest_ref": artifact_ref("COMPLETE_RUN_MANIFEST", "COMPLETE_RUN_MANIFEST", "ANALYSIS"),
    "life_gate_aggregate_refs": refs("LIFE_GATE_AGGREGATE", "LIFE_GATE_AGGREGATE", "ANALYSIS"),
    "paired_gate_result_refs": refs("PAIRED_GATE_RESULT", "PAIRED_GATE_RESULT", "ANALYSIS"),
    "resolved_safety_registry_ref": artifact_ref(
        "RESOLVED_D1A_SAFETY_TRIAL_REGISTRY", "RESOLVED_D1A_SAFETY_TRIAL_REGISTRY", "ANALYSIS"
    ),
    "d1a_control_manifest_ref": artifact_ref("D1A_CONTROL_SET_MANIFEST", "D1A_CONTROL_SET_MANIFEST",
                                             "ANALYSIS"),
    "joint_power_ref": artifact_ref("JOINT_CONSTRUCTION_RELEASE_POWER", "JOINT_CONSTRUCTION_RELEASE_POWER_RECEIPT",
                                    "ANALYSIS"),
    "resource_accounting_ref": artifact_ref("RESOURCE_ACCOUNTING", "RESOURCE_ACCOUNTING_RECEIPT", "ANALYSIS"),
    "holm_family": tuple_of(*[{"const": value} for value in (
        "PPC5_D1A_SUPPORTED_SELECTION", "PPC5_D1B_OBSERVABLE_EDGE_DEPENDENCE",
        "PPC5_D1C_DREAM_CONTEXT_POLICY", "PPC5_D1D_DREAM_TO_SLEEP_TOTAL_POLICY",
    )]),
    "intersection_adds_hypothesis": {"const": False},
    "n_is_life_count_only": {"const": True},
})


def claim_rendering_schema() -> dict[str, Any]:
    variants: list[dict[str, Any]] = []
    for claim_id, text in CLAIM_TEXTS.items():
        segments = [text, FIXED_QUALIFICATION]
        resource_hash: dict[str, Any] = {"type": "null"}
        resource_value: dict[str, Any] = {"type": "null"}
        if claim_id == "PPC5_D1D_DREAM_TO_SLEEP_TOTAL_POLICY":
            # The resource qualification must be literally adjacent to the
            # D1D claim and precede the shared/global qualification.
            segments = [text, RESOURCE_QUALIFICATION, FIXED_QUALIFICATION]
            resource_hash = {"const": sha256_bytes(RESOURCE_QUALIFICATION.encode("utf-8"))}
            resource_value = {"const": RESOURCE_QUALIFICATION}
        variants.append(closed({
            "claim_id": {"const": claim_id},
            "release_text": {"const": text},
            "release_text_sha256": {"const": sha256_bytes(text.encode("utf-8"))},
            "fixed_qualification": {"const": FIXED_QUALIFICATION},
            "fixed_qualification_sha256": {"const": sha256_bytes(FIXED_QUALIFICATION.encode("utf-8"))},
            "resource_qualification": resource_value,
            "resource_qualification_sha256": resource_hash,
            "ordered_inseparable_segments": tuple_of(*[{"const": segment} for segment in segments]),
        }))
    return {"oneOf": variants}


defs["claim_rendering"] = claim_rendering_schema()

add("CANDIDATE_DECISION_RECEIPT", "CANDIDATE_DECISION_REDUCER", {
    "run_id": ID,
    "analysis_bundle_ref": artifact_ref("ANALYSIS_BUNDLE", "ANALYSIS_BUNDLE", "CANDIDATE_DECISION"),
    "claim_registry_ref": artifact_ref("CLAIM_REGISTRY", "CLAIM_REGISTRY", "CANDIDATE_DECISION",
                                       run_bound=False),
    "claim_rendering": {"$ref": "#/$defs/claim_rendering"},
    "statistical_gate_ids": arr(SYM, 1, unique=True),
    "decision": enum("CANDIDATE", "BLOCKED"),
    "first_blocker": nullable(SYM),
    "d1d_gate_ids_if_applicable": tuple_of(
        {"const": "CORRECT_SUPPORTED_SELECTION"}, {"const": "NORMALIZED_ACTION_VALUE"}
    ),
    "resource_adjustment_or_rescue_forbidden": {"const": True},
})

add("DEPENDENCY_DECISION_RECEIPT", "DEPENDENCY_REDUCER", {
    "run_id": ID,
    "candidate_decision_ref": artifact_ref(
        "CANDIDATE_DECISION", "CANDIDATE_DECISION_RECEIPT",
        "DEPENDENCY_DECISION"),
    "dependency_registry_ref": artifact_ref(
        "DEPENDENCY_REGISTRY", "DEPENDENCY_REGISTRY",
        "DEPENDENCY_DECISION", run_bound=False),
    "dependency_candidate_refs": refs(
        "DEPENDENCY_CANDIDATE", "CANDIDATE_DECISION_RECEIPT",
        "DEPENDENCY_DECISION", minimum=0, maximum=4),
    "claim_rendering": {"$ref": "#/$defs/claim_rendering"},
    "rendering_equals_candidate": {"type": "boolean"},
    "required_dependency_set_exact": {"type": "boolean"},
    "all_required_dependencies_candidate": {"type": "boolean"},
    "resource_adjustment_or_rescue_detected": {"const": False},
    "decision": enum("PASS", "BLOCKED"),
    "first_blocker": nullable(SYM),
}, one_of=[
    {"properties": {
        "decision": {"const": "PASS"},
        "rendering_equals_candidate": {"const": True},
        "required_dependency_set_exact": {"const": True},
        "all_required_dependencies_candidate": {"const": True},
        "first_blocker": {"type": "null"},
    }},
    {"properties": {"decision": {"const": "BLOCKED"}}},
])


# R04: fixture bytes are specified before ratification; later code may only
# materialize the frozen universe.  T01 is intentionally a different, generic
# persisted-state evidence object (R02).
add("FIXTURE_GENERATOR_SPEC", "FIXTURE_SPEC_AUTHOR", {
    "architecture_id": {"const": ARCHITECTURE_ID},
    "test_id": enum(*[f"PPC5R9_T{i:02d}" for i in range(2, 15)]),
    "generator_id": SYM,
    "generator_version": integer(1),
    "generator_source_ref": raw_ref("RAW_FIXTURE_GENERATOR_SOURCE", "FIXTURE_SPEC",
                                      run_bound=False),
    "canonical_iteration_order": arr(SYM, 1, unique=True),
    "finite_axes": arr({"$ref": "#/$defs/fixture_axis"}, 1),
    "applicability_and_exclusion_rules": arr(BYTES, 1),
    "expected_positive_count": integer(),
    "one_field_mutation_dimensions": arr(SYM, 1, unique=True),
    "expected_mutation_count": integer(),
    "expected_precedence_probe_count": integer(),
    "logical_expected_count": integer(1),
    "total_planned_executions": integer(2),
    "branch_key_encoding": {"const": "UTF8_CANONICAL_JSON_TYPED_AXIS_BRANCH_KEY_V1"},
    "expected_branches": arr({"$ref": "#/$defs/fixture_expected_branch"}, 1),
    "negative_mutations": arr({"$ref": "#/$defs/fixture_one_field_mutation"}),
    "precedence_probes": arr({"$ref": "#/$defs/fixture_expected_branch"}),
    "branch_key_set_sha256": H,
    "ordered_expected_vector_sha256": H,
    "expected_enumerator_ref": raw_ref("RAW_INDEPENDENT_EXPECTED_ENUMERATOR", "FIXTURE_SPEC",
                                        run_bound=False),
    "executed_set_extractor_ref": raw_ref("RAW_INDEPENDENT_EXECUTED_SET_EXTRACTOR", "FIXTURE_SPEC",
                                           run_bound=False),
    "must_be_frozen_before_architecture_ratification": {"const": True},
    "post_ratification_code_may_define_normative_bytes": {"const": False},
})

add("FIXTURE_CASE_RESULT", "FIXTURE_EXECUTOR", {
    "run_id": ID,
    "executor_id": enum("A", "B"),
    "executor_implementation_ref": raw_ref("RAW_FIXTURE_EXECUTOR_IMPLEMENTATION",
                                             "FIXTURE_EXECUTION", run_bound=True),
    "fixture_spec_ref": artifact_ref("FIXTURE_SPEC", "FIXTURE_GENERATOR_SPEC", "FIXTURE_EXECUTION",
                                     run_bound=False),
    "test_id": enum(*[f"PPC5R9_T{i:02d}" for i in range(2, 15)]),
    "case_ordinal": integer(),
    "branch_key": BYTES,
    "input_canonical_json": BYTES,
    "actual_output_canonical_json": nullable(BYTES),
    "actual_first_failure": nullable(SYM),
    "matched_frozen_expectation": {"type": "boolean"},
})

add("FIXTURE_EXECUTION_MANIFEST", "FIXTURE_EXECUTOR", {
    "run_id": ID,
    "executor_id": enum("A", "B"),
    "executor_implementation_ref": raw_ref("RAW_FIXTURE_EXECUTOR_IMPLEMENTATION",
                                             "FIXTURE_EXECUTION", run_bound=True),
    "fixture_spec_ref": artifact_ref("FIXTURE_SPEC", "FIXTURE_GENERATOR_SPEC",
                                     "FIXTURE_EXECUTION", run_bound=False),
    "ordered_case_result_refs": refs("FIXTURE_CASE_RESULT", "FIXTURE_CASE_RESULT",
                                      "FIXTURE_EXECUTION"),
    "ordered_result_vector_sha256": H,
    "branch_key_set_sha256": H,
    "case_count": integer(1),
    "complete_frozen_set": {"const": True},
})

add("FIXTURE_SET_EQUALITY_RECEIPT", "INDEPENDENT_FIXTURE_ORACLE", {
    "run_id": ID,
    "fixture_spec_ref": artifact_ref("FIXTURE_SPEC", "FIXTURE_GENERATOR_SPEC", "TEST_REDUCER",
                                     run_bound=False),
    "executor_a_manifest_ref": artifact_ref("FIXTURE_EXECUTION_MANIFEST_A",
                                              "FIXTURE_EXECUTION_MANIFEST", "TEST_REDUCER"),
    "executor_b_manifest_ref": artifact_ref("FIXTURE_EXECUTION_MANIFEST_B",
                                              "FIXTURE_EXECUTION_MANIFEST", "TEST_REDUCER"),
    "executor_sources_distinct": {"const": True},
    "executor_a_id": {"const": "A"},
    "executor_b_id": {"const": "B"},
    "normative_expected_set_sha256": H,
    "materialized_executed_set_sha256": H,
    "executor_a_result_vector_sha256": H,
    "executor_b_result_vector_sha256": H,
    "expected_count": integer(),
    "executed_count": integer(),
    "missing_count": {"const": 0},
    "extra_count": {"const": 0},
    "duplicate_count": {"const": 0},
    "reordered_count": {"const": 0},
    "mismatched_count": {"const": 0},
    "byte_set_equal": {"const": True},
})

add("TEST_RESULT", "TEST_REDUCER", {
    "run_id": ID,
    "test_id": enum(*[f"PPC5R9_T{i:02d}" for i in range(2, 13)]),
    "populated_run_lock_ref": artifact_ref("POPULATED_RUN_LOCK", "POPULATED_RUN_LOCK", "TEST_REDUCER"),
    "fixture_spec_ref": artifact_ref("FIXTURE_SPEC", "FIXTURE_GENERATOR_SPEC", "TEST_REDUCER",
                                     run_bound=False),
    "set_equality_ref": artifact_ref("FIXTURE_SET_EQUALITY", "FIXTURE_SET_EQUALITY_RECEIPT",
                                     "TEST_REDUCER"),
    "executor_a_manifest_ref": artifact_ref("FIXTURE_EXECUTION_MANIFEST_A",
                                              "FIXTURE_EXECUTION_MANIFEST", "TEST_REDUCER"),
    "executor_b_manifest_ref": artifact_ref("FIXTURE_EXECUTION_MANIFEST_B",
                                              "FIXTURE_EXECUTION_MANIFEST", "TEST_REDUCER"),
    "status": enum("PASS", "FAIL"),
    "first_failure": nullable(SYM),
})

add("CONFORMANCE_RECEIPT", "CONFORMANCE_REDUCER", {
    "run_id": ID,
    "populated_run_lock_ref": artifact_ref(
        "POPULATED_RUN_LOCK", "POPULATED_RUN_LOCK", "CPU_CONFORMANCE"),
    "fixture_spec_refs": refs(
        "FIXTURE_SPEC", "FIXTURE_GENERATOR_SPEC", "CPU_CONFORMANCE",
        minimum=13, maximum=13, run_bound=False),
    "t02_t12_result_refs": refs(
        "PREMODEL_TEST_RESULT", "TEST_RESULT", "CPU_CONFORMANCE",
        minimum=11, maximum=11),
    "exact_test_ids": tuple_of(*[
        {"const": f"PPC5R9_T{i:02d}"} for i in range(2, 13)
    ]),
    "all_fixture_specs_frozen_before_architecture_ratification": {"const": True},
    "all_test_results_consume_two_source_distinct_executor_manifests": {"const": True},
    "schema_registry_inventory_visibility_exact_closure": {"const": True},
    "status": enum("PASS", "FAIL"),
    "first_failure": nullable(SYM),
}, one_of=[
    {"properties": {"status": {"const": "PASS"},
                    "first_failure": {"type": "null"}}},
    {"properties": {"status": {"const": "FAIL"}}},
])


# Static seals, generic T01 evidence, review, and the acyclic T13 -> human ->
# premodel authority path (R02/R09).
add("STATIC_SEAL_RECEIPT", "STATIC_SEALER", {
    "run_id": ID,
    "sealer_id": enum("A", "B"),
    "sealer_implementation_ref": raw_ref("RAW_SEALER_IMPLEMENTATION", "STATIC_SEAL", run_bound=True),
    "populated_run_lock_ref": artifact_ref("POPULATED_RUN_LOCK", "POPULATED_RUN_LOCK", "STATIC_SEAL"),
    "semantic_registry_refs": {"$ref": "#/$defs/semantic_registry_refs"},
    "d1a_control_manifest_ref": artifact_ref("D1A_CONTROL_SET_MANIFEST", "D1A_CONTROL_SET_MANIFEST",
                                             "STATIC_SEAL"),
    "construction_outputs_ref": raw_ref("RAW_CONSTRUCTION_OUTPUTS", "STATIC_SEAL", run_bound=True),
    "decision": enum("PASS", "FAIL"),
    "first_failure": nullable(SYM),
})

add("STATIC_SEAL_PAIR_RECEIPT", "STATIC_SEAL_PAIR_REDUCER", {
    "run_id": ID,
    "seal_refs": tuple_of(
        artifact_ref("STATIC_SEAL_A", "STATIC_SEAL_RECEIPT", "STATIC_SEAL_PAIR", 0),
        artifact_ref("STATIC_SEAL_B", "STATIC_SEAL_RECEIPT", "STATIC_SEAL_PAIR", 1),
    ),
    "distinct_implementation_sha256s": tuple_of(H, H),
    "independence_basis_canonical_json": BYTES,
    "both_pass": {"const": True},
})

add("GENERIC_T01_INTAKE_EVIDENCE", "GENERIC_INTAKE_STATE_VALIDATOR", {
    "architecture_id": {"const": ARCHITECTURE_ID},
    "intake_state_ref": raw_ref("RAW_GENERIC_INTAKE_STATE", "T01_GENERIC_EVIDENCE",
                                  run_bound=False),
    "change_id": ID,
    "phase": {"const": "human_required"},
    "human_required": {"const": True},
    "implementation_authorized": {"const": False},
    "required_artifact_roles_once": tuple_of(*[{"const": value} for value in (
        "ARCHITECTURE_CHANGE", "INTERPRETATION_SYSTEMS", "INTERPRETATION_SCIENCE",
        "CRITIQUE", "CONSENSUS",
    )]),
    "awaiting_consensus_to_human_required_count": {"const": 1},
    "predecessor_source_state_sha256": H,
    "consensus_artifact_sha256": H,
    "forbidden_artifact_keys_absent": tuple_of(
        {"const": "ARCHITECTURE_HUMAN_RATIFICATION"}, {"const": "PPC_FIXTURE"},
        {"const": "PPC_TEST_RESULT"}, {"const": "PPC_IMPLEMENTATION"},
        {"const": "PPC_SEALER"},
    ),
    "unpersisted_claims_not_attested": tuple_of(
        {"const": "ARGV"}, {"const": "PROCESS_EXIT_CODE"}, {"const": "STDOUT_BYTES"},
        {"const": "DELIBERATION_RUNNER_CLI_TRANSCRIPT"},
    ),
})

add("REVIEW_RECEIPT", "FRESH_INDEPENDENT_REVIEWER", {
    "run_id": ID,
    "populated_run_lock_ref": artifact_ref("POPULATED_RUN_LOCK", "POPULATED_RUN_LOCK", "INDEPENDENT_REVIEW"),
    "conformance_ref": artifact_ref(
        "CPU_CONFORMANCE", "CONFORMANCE_RECEIPT", "INDEPENDENT_REVIEW"),
    "static_seal_pair_ref": artifact_ref(
        "STATIC_SEAL_PAIR", "STATIC_SEAL_PAIR_RECEIPT", "INDEPENDENT_REVIEW"),
    "reviewer_context_ref": raw_ref("RAW_REVIEWER_CONTEXT", "INDEPENDENT_REVIEW", run_bound=True),
    "review_implementation_ref": raw_ref("RAW_REVIEW_IMPLEMENTATION", "INDEPENDENT_REVIEW", run_bound=True),
    "reviewed_implementation_bundle_sha256": H,
    "reviewed_technical_package_sha256": H,
    "conformance_status_verified_pass": {"type": "boolean"},
    "static_seal_pair_verified_pass": {"type": "boolean"},
    "decision": enum("PASS", "REWORK", "REJECT"),
    "first_failure": nullable(SYM),
}, one_of=[
    {"properties": {
        "decision": {"const": "PASS"},
        "conformance_status_verified_pass": {"const": True},
        "static_seal_pair_verified_pass": {"const": True},
        "first_failure": {"type": "null"},
    }},
    {"properties": {"decision": {"enum": ["REWORK", "REJECT"]}}},
])

add("ADVOCATE_RECEIPT", "AUTHOR_SIDE_ADVOCATE", {
    "run_id": ID,
    "review_ref": artifact_ref("INDEPENDENT_REVIEW", "REVIEW_RECEIPT", "ADVOCATE"),
    "advocate_context_ref": raw_ref("RAW_ADVOCATE_CONTEXT", "ADVOCATE", run_bound=True),
    "position": enum("SUPPORT", "REPAIR_REQUEST", "NO_POSITION"),
    "can_override_review": {"const": False},
})

add("T13_PREMODEL_TECHNICAL_GATE", "T13_TECHNICAL_REDUCER", {
    "run_id": ID,
    "test_id": {"const": "PPC5R9_T13"},
    "t01_evidence_ref": artifact_ref("GENERIC_T01_INTAKE_EVIDENCE", "GENERIC_T01_INTAKE_EVIDENCE",
                                     "T13", run_bound=False),
    "fixture_spec_ref": artifact_ref("FIXTURE_SPEC", "FIXTURE_GENERATOR_SPEC", "T13", run_bound=False),
    "fixture_set_equality_ref": artifact_ref(
        "T13_FIXTURE_SET_EQUALITY", "FIXTURE_SET_EQUALITY_RECEIPT", "T13"),
    "fixture_executor_a_manifest_ref": artifact_ref(
        "T13_FIXTURE_EXECUTION_MANIFEST_A", "FIXTURE_EXECUTION_MANIFEST", "T13"),
    "fixture_executor_b_manifest_ref": artifact_ref(
        "T13_FIXTURE_EXECUTION_MANIFEST_B", "FIXTURE_EXECUTION_MANIFEST", "T13"),
    "populated_run_lock_ref": artifact_ref("POPULATED_RUN_LOCK", "POPULATED_RUN_LOCK", "T13"),
    "conformance_ref": artifact_ref(
        "CPU_CONFORMANCE", "CONFORMANCE_RECEIPT", "T13"),
    "static_seal_pair_ref": artifact_ref("STATIC_SEAL_PAIR", "STATIC_SEAL_PAIR_RECEIPT", "T13"),
    "review_ref": artifact_ref("INDEPENDENT_REVIEW", "REVIEW_RECEIPT", "T13"),
    "advocate_ref": artifact_ref("NON_OVERRIDING_ADVOCATE", "ADVOCATE_RECEIPT", "T13"),
    "conditional_power_refs": refs("CONDITIONAL_COMPLETE_RELEASE_POWER",
                                   "CONDITIONAL_COMPLETE_RELEASE_POWER_RESULT", "T13"),
    "joint_power_ref": artifact_ref("JOINT_CONSTRUCTION_RELEASE_POWER",
                                    "JOINT_CONSTRUCTION_RELEASE_POWER_RECEIPT", "T13"),
    "topology_check": {"const": "ACYCLIC_EXACT_HASH_REFERENCE_DAG"},
    "preflight_denials_complete": {"const": True},
    "fixture_conformance_verified_pass": {"type": "boolean"},
    "conformance_status_verified_pass": {"type": "boolean"},
    "static_seal_pair_verified_pass": {"type": "boolean"},
    "review_decision_verified_pass": {"type": "boolean"},
    "advocate_nonoverride_verified": {"type": "boolean"},
    "power_requirements_verified": {"type": "boolean"},
    "status": enum("PASS", "FAIL"),
    "first_failure": nullable(SYM),
}, one_of=[
    {"properties": {
        "status": {"const": "PASS"},
        "fixture_conformance_verified_pass": {"const": True},
        "conformance_status_verified_pass": {"const": True},
        "static_seal_pair_verified_pass": {"const": True},
        "review_decision_verified_pass": {"const": True},
        "advocate_nonoverride_verified": {"const": True},
        "power_requirements_verified": {"const": True},
        "first_failure": {"type": "null"},
    }},
    {"properties": {"status": {"const": "FAIL"}}},
], description=(
    "Last technical PRE_MODEL_EXECUTION gate. Closed fields intentionally contain no human-run "
    "ratification or PRE_MODEL_AUTHORITY predecessor."
))

add("HUMAN_RUN_RATIFICATION_RECEIPT", "HUMAN_RUN_RATIFIER", {
    "run_id": ID,
    "t13_ref": artifact_ref("T13_PREMODEL_TECHNICAL_GATE", "T13_PREMODEL_TECHNICAL_GATE",
                            "HUMAN_RUN_RATIFICATION"),
    "populated_run_lock_ref": artifact_ref("POPULATED_RUN_LOCK", "POPULATED_RUN_LOCK",
                                           "HUMAN_RUN_RATIFICATION"),
    "static_seal_pair_ref": artifact_ref("STATIC_SEAL_PAIR", "STATIC_SEAL_PAIR_RECEIPT",
                                         "HUMAN_RUN_RATIFICATION"),
    "joint_power_ref": artifact_ref("JOINT_CONSTRUCTION_RELEASE_POWER",
                                    "JOINT_CONSTRUCTION_RELEASE_POWER_RECEIPT", "HUMAN_RUN_RATIFICATION"),
    "t13_status_verified_pass": {"const": True},
    "human_evidence_ref": raw_ref("RAW_HUMAN_RUN_RATIFICATION_EVIDENCE", "HUMAN_RUN_RATIFICATION",
                                  run_bound=True),
    "exact_human_evidence_excerpt": BYTES,
    "exact_run_package_sha256": H,
    "decision": {"const": "RATIFIED"},
    "authorized_scope": {"const": "EXACT_HASH_BOUND_MODEL_RUN_ONLY"},
    "forbidden_scope": {
        "const": "ANY_OTHER_RUN_PARAMETER_MODEL_ADAPTER_PROMPT_DATA_SEED_OR_DISPATCH"
    },
    "model_execution_reachable": {"const": False},
}, one_of=[
    {"properties": {"lifecycle_state": {"const": "EXECUTED"}}},
])

add("PRE_MODEL_AUTHORITY_RECEIPT", "PREMODEL_AUTHORITY_REDUCER", {
    "run_id": ID,
    "stage": {"const": "PRE_MODEL_EXECUTION"},
    "t13_ref": artifact_ref("T13_PREMODEL_TECHNICAL_GATE", "T13_PREMODEL_TECHNICAL_GATE",
                            "PREMODEL_AUTHORITY"),
    "human_run_ratification_ref": artifact_ref("HUMAN_RUN_RATIFICATION",
                                               "HUMAN_RUN_RATIFICATION_RECEIPT", "PREMODEL_AUTHORITY"),
    "allowed_dispatch_registry_ref": artifact_ref(
        "ALLOWED_DISPATCH_REGISTRY", "ALLOWED_DISPATCH_REGISTRY",
        "PREMODEL_AUTHORITY", run_bound=False),
    "exact_run_package_sha256": H,
    "human_run_package_hash_equality": {"const": True},
    "t13_status_verified_pass": {"type": "boolean"},
    "human_run_ratification_verified": {"type": "boolean"},
    "authorized_scope": {"const": "EXACT_HASH_BOUND_MODEL_RUN_ONLY"},
    "decision": enum("GRANT", "DENY"),
    "model_execution_reachable": {"type": "boolean"},
    "denial_reason": nullable(SYM),
}, one_of=[
    {"properties": {"lifecycle_state": {"const": "EXECUTED"},
                    "decision": {"const": "GRANT"}, "model_execution_reachable": {"const": True},
                    "t13_status_verified_pass": {"const": True},
                    "human_run_ratification_verified": {"const": True},
                    "denial_reason": {"type": "null"}}},
    {"properties": {"lifecycle_state": {"const": "EXECUTED"},
                    "decision": {"const": "DENY"}, "model_execution_reachable": {"const": False}}},
])


# R09: exactly two independent predecessor-only replays -> one T14 -> one
# preclaim edge -> release.  Replay and T14 schemas cannot consume release.
add("COLD_REPLAY_RECEIPT", "COLD_REPLAY_EXECUTOR", {
    "run_id": ID,
    "replay_id": enum("A", "B"),
    "replay_implementation_ref": raw_ref("RAW_COLD_REPLAY_IMPLEMENTATION", "COLD_REPLAY", run_bound=True),
    "complete_run_manifest_ref": artifact_ref("COMPLETE_RUN_MANIFEST", "COMPLETE_RUN_MANIFEST", "COLD_REPLAY"),
    "model_view_manifest_ref": artifact_ref("COMPLETE_MODEL_VIEW_MANIFEST", "COMPLETE_MODEL_VIEW_MANIFEST",
                                             "COLD_REPLAY"),
    "d1a_control_manifest_ref": artifact_ref("D1A_CONTROL_SET_MANIFEST", "D1A_CONTROL_SET_MANIFEST",
                                             "COLD_REPLAY"),
    "analysis_bundle_ref": artifact_ref("ANALYSIS_BUNDLE", "ANALYSIS_BUNDLE", "COLD_REPLAY"),
    "runtime_integrity_ref": artifact_ref(
        "RUNTIME_INTEGRITY", "RUNTIME_INTEGRITY_RECEIPT", "COLD_REPLAY"),
    "candidate_decision_refs": refs("CANDIDATE_DECISION", "CANDIDATE_DECISION_RECEIPT", "COLD_REPLAY"),
    "dependency_decision_refs": refs("DEPENDENCY_DECISION", "DEPENDENCY_DECISION_RECEIPT", "COLD_REPLAY"),
    "route_lineage_audit_refs": refs("ROUTE_LINEAGE_AUDIT", "ROUTE_LINEAGE_AUDIT_RECEIPT",
                                     "COLD_REPLAY"),
    "provider_audit_refs": refs("PROVIDER_AUDIT", "PROVIDER_AUDIT_RECEIPT", "COLD_REPLAY"),
    "joint_power_ref": artifact_ref("JOINT_CONSTRUCTION_RELEASE_POWER",
                                    "JOINT_CONSTRUCTION_RELEASE_POWER_RECEIPT", "COLD_REPLAY"),
    "seed_view_dispatch_state_ledger_io_debit_transition_closure": {"const": True},
    "life_aggregate_and_control_closure": {"const": True},
    "candidate_boundary_and_resource_qualification_closure": {"const": True},
    "runtime_integrity_status_verified_pass": {"type": "boolean"},
    "release_bytes_consumed": {"const": False},
    "decision": enum("PASS", "FAIL"),
    "first_failure": nullable(SYM),
}, one_of=[
    {"properties": {"decision": {"const": "PASS"},
                    "runtime_integrity_status_verified_pass": {"const": True},
                    "first_failure": {"type": "null"}}},
    {"properties": {"decision": {"const": "FAIL"}}},
])

add("T14_FINAL_REPLAY_RESULT", "T14_REPLAY_REDUCER", {
    "run_id": ID,
    "test_id": {"const": "PPC5R9_T14"},
    "fixture_spec_ref": artifact_ref("FIXTURE_SPEC", "FIXTURE_GENERATOR_SPEC", "T14", run_bound=False),
    "fixture_set_equality_ref": artifact_ref(
        "T14_FIXTURE_SET_EQUALITY", "FIXTURE_SET_EQUALITY_RECEIPT", "T14"),
    "fixture_executor_a_manifest_ref": artifact_ref(
        "T14_FIXTURE_EXECUTION_MANIFEST_A", "FIXTURE_EXECUTION_MANIFEST", "T14"),
    "fixture_executor_b_manifest_ref": artifact_ref(
        "T14_FIXTURE_EXECUTION_MANIFEST_B", "FIXTURE_EXECUTION_MANIFEST", "T14"),
    "cold_replay_refs": tuple_of(
        artifact_ref("COLD_REPLAY_A", "COLD_REPLAY_RECEIPT", "T14", 0),
        artifact_ref("COLD_REPLAY_B", "COLD_REPLAY_RECEIPT", "T14", 1),
    ),
    "distinct_implementation_sha256s": tuple_of(H, H),
    "independence_verified": {"const": True},
    "predecessor_only": {"const": True},
    "release_bytes_consumed": {"const": False},
    "both_replays_pass": {"type": "boolean"},
    "shared_runtime_integrity_pass": {"type": "boolean"},
    "fixture_conformance_verified_pass": {"type": "boolean"},
    "status": enum("PASS", "FAIL"),
    "first_failure": nullable(SYM),
}, one_of=[
    {"properties": {"status": {"const": "PASS"},
                    "both_replays_pass": {"const": True},
                    "shared_runtime_integrity_pass": {"const": True},
                    "fixture_conformance_verified_pass": {"const": True},
                    "first_failure": {"type": "null"}}},
    {"properties": {"status": {"const": "FAIL"}}},
])

add("PRECLAIM_AUTHORITY_RECEIPT", "PRECLAIM_AUTHORITY_REDUCER", {
    "run_id": ID,
    "stage": {"const": "PRECLAIM"},
    "final_t14_result_ref": artifact_ref("FINAL_T14_RESULT", "T14_FINAL_REPLAY_RESULT", "PRECLAIM_AUTHORITY"),
    "analysis_bundle_ref": artifact_ref("ANALYSIS_BUNDLE", "ANALYSIS_BUNDLE", "PRECLAIM_AUTHORITY"),
    "runtime_integrity_ref": artifact_ref(
        "RUNTIME_INTEGRITY", "RUNTIME_INTEGRITY_RECEIPT",
        "PRECLAIM_AUTHORITY"),
    "candidate_decision_refs": refs("CANDIDATE_DECISION", "CANDIDATE_DECISION_RECEIPT",
                                    "PRECLAIM_AUTHORITY", minimum=5, maximum=5),
    "dependency_decision_refs": refs("DEPENDENCY_DECISION", "DEPENDENCY_DECISION_RECEIPT",
                                     "PRECLAIM_AUTHORITY", minimum=5, maximum=5),
    "authority_registry_ref": artifact_ref("AUTHORITY_REGISTRY", "AUTHORITY_REGISTRY",
                                           "PRECLAIM_AUTHORITY", run_bound=False),
    "topological_validation": {"const": "EXACT_HASH_DAG_NO_ALIAS_NO_BACK_EDGE"},
    "final_t14_reference_count": {"const": 1},
    "final_t14_status_pass": {"type": "boolean"},
    "runtime_integrity_status_pass": {"type": "boolean"},
    "all_five_candidate_decisions_eligible": {"type": "boolean"},
    "all_five_dependency_decisions_pass": {"type": "boolean"},
    "decision": enum("GRANT", "DENY"),
    "claim_release_reachable": {"type": "boolean"},
    "denial_reason": nullable(SYM),
}, one_of=[
    {"properties": {"decision": {"const": "GRANT"}, "claim_release_reachable": {"const": True},
                    "final_t14_status_pass": {"const": True},
                    "runtime_integrity_status_pass": {"const": True},
                    "all_five_candidate_decisions_eligible": {"const": True},
                    "all_five_dependency_decisions_pass": {"const": True},
                    "denial_reason": {"type": "null"}}},
    {"properties": {"decision": {"const": "DENY"}, "claim_release_reachable": {"const": False}}},
])

add("CLAIM_RELEASE_PACKAGE", "CLAIM_RELEASE_REDUCER", {
    "run_id": ID,
    "preclaim_authority_ref": artifact_ref("PRECLAIM_AUTHORITY", "PRECLAIM_AUTHORITY_RECEIPT",
                                           "CLAIM_RELEASE"),
    "candidate_decision_ref": artifact_ref("CANDIDATE_DECISION", "CANDIDATE_DECISION_RECEIPT",
                                           "CLAIM_RELEASE"),
    "dependency_decision_ref": artifact_ref("DEPENDENCY_DECISION", "DEPENDENCY_DECISION_RECEIPT",
                                            "CLAIM_RELEASE"),
    "preclaim_decision_verified_grant": {"type": "boolean"},
    "candidate_decision_verified_candidate": {"type": "boolean"},
    "dependency_decision_verified_pass": {"type": "boolean"},
    "claim_rendering": {"$ref": "#/$defs/claim_rendering"},
    "rendering_equals_candidate_and_dependency": {"type": "boolean"},
    "status": enum("RELEASED", "BLOCKED"),
    "first_blocker": nullable(SYM),
    "forbidden_claims": arr(BYTES),
}, one_of=[
    {"properties": {
        "status": {"const": "RELEASED"},
        "preclaim_decision_verified_grant": {"const": True},
        "candidate_decision_verified_candidate": {"const": True},
        "dependency_decision_verified_pass": {"const": True},
        "rendering_equals_candidate_and_dependency": {"const": True},
        "first_blocker": {"type": "null"},
    }},
    {"properties": {"status": {"const": "BLOCKED"}}},
])

add("CLAIM_EXPORT_RECEIPT", "CLAIM_EXPORTER", {
    "run_id": ID,
    "claim_release_ref": artifact_ref(
        "RELEASED_CLAIM_PACKAGE", "CLAIM_RELEASE_PACKAGE", "CLAIM_EXPORT"),
    "release_status_verified_released": {"const": True},
    "claim_rendering": {"$ref": "#/$defs/claim_rendering"},
    "exported_bytes": BYTES,
    "exported_bytes_equal_release_rendering": {"const": True},
    "status": {"const": "EXPORTED"},
})

add("CLAIM_AUDIT_RECEIPT", "CLAIM_AUDITOR", {
    "run_id": ID,
    "claim_release_ref": artifact_ref(
        "RELEASED_CLAIM_PACKAGE", "CLAIM_RELEASE_PACKAGE", "CLAIM_AUDIT"),
    "claim_export_ref": artifact_ref(
        "CLAIM_EXPORT", "CLAIM_EXPORT_RECEIPT", "CLAIM_AUDIT"),
    "claim_rendering": {"$ref": "#/$defs/claim_rendering"},
    "release_export_rendering_equal": {"type": "boolean"},
    "audit_rendering_equal_release_and_export": {"type": "boolean"},
    "authority_conferred": {"const": False},
    "decision": enum("PASS", "FAIL"),
    "first_failure": nullable(SYM),
}, one_of=[
    {"properties": {"decision": {"const": "PASS"},
                    "release_export_rendering_equal": {"const": True},
                    "audit_rendering_equal_release_and_export": {"const": True},
                    "first_failure": {"type": "null"}}},
    {"properties": {"decision": {"const": "FAIL"}}},
])


TOP_LEVEL_NAMES = tuple(PRODUCERS)


def build_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": SCHEMA_ID,
        "title": "PPC5r9 compact proposal-only contract union",
        "description": (
            "Successor proposal schema implementing the structural R01-R13 repairs from the "
            "frozen r8 REWORK consensus. Validation never implies ratification or authority."
        ),
        "x-proposal-only": True,
        "x-nonnormative-generator": "build_contract_schema.py",
        "x-source-consensus-sha256": R8_CONSENSUS_SHA256,
        "x-self-hash-convention": SELF_HASH_ALGORITHM,
        "x-visibility-edge-catalog": VISIBILITY_ALLOWED_EDGES,
        "oneOf": [{"$ref": f"#/$defs/{name.lower()}"} for name in TOP_LEVEL_NAMES],
        "$defs": defs,
    }


def resolve_local_ref(schema: dict[str, Any], ref: str) -> Any:
    if not ref.startswith("#/$defs/"):
        raise ValueError(f"nonlocal or unsupported schema ref: {ref}")
    name = ref.removeprefix("#/$defs/")
    if name not in schema["$defs"]:
        raise ValueError(f"missing local schema ref target: {ref}")
    return schema["$defs"][name]


def all_local_refs(schema: dict[str, Any]) -> list[str]:
    found: list[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            if "$ref" in node:
                found.append(node["$ref"])
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(schema)
    return found


def collect_artifact_edges(schema: dict[str, Any], top_name: str) -> list[dict[str, Any]]:
    """Independently extract typed refs by recursively traversing local $defs."""
    edges: list[dict[str, Any]] = []

    def walk(node: Any, path: str, stack: tuple[str, ...]) -> None:
        if isinstance(node, list):
            for index, value in enumerate(node):
                walk(value, f"{path}/{index}", stack)
            return
        if not isinstance(node, dict):
            return
        if node.get("x-artifact-ref") is True:
            for target in node["x-artifact-types"]:
                edges.append({
                    "target_type": target,
                    "consumer_type": top_name,
                    "consumer_stage": node["x-consumer-stage"],
                    "field_path": path or "/",
                    "role": node["x-role"],
                    "ordinal": node["x-ordinal"],
                    "cardinality": node["x-cardinality"],
                })
            return
        if "$ref" in node:
            ref = node["$ref"]
            if ref in stack:
                raise ValueError(f"local schema ref cycle while inventorying {top_name}: {ref}")
            walk(resolve_local_ref(schema, ref), path + f"->$ref({ref})", stack + (ref,))
            # JSON Schema siblings of $ref remain active in draft 2020-12.
            for key, value in node.items():
                if key != "$ref":
                    walk(value, path + "/" + key, stack)
            return
        for key, value in node.items():
            if key.startswith("x-"):
                continue
            walk(value, path + "/" + key, stack)

    walk(schema["$defs"][top_name.lower()], "", ())
    # The same ref may be reached through a schema oneOf and a shared property.
    unique = {json.dumps(edge, sort_keys=True, separators=(",", ":")): edge for edge in edges}
    return [unique[key] for key in sorted(unique)]


def schema_at_field_path(schema: dict[str, Any], artifact_type: str, field_path: str) -> dict[str, Any]:
    """Resolve a dotted top-level property path used by a visibility edge."""
    if artifact_type not in PRODUCERS:
        raise ValueError(f"visibility edge names uninventoried type {artifact_type}")
    node: dict[str, Any] = schema["$defs"][artifact_type.lower()]
    for component in field_path.split("."):
        while "$ref" in node:
            node = resolve_local_ref(schema, node["$ref"])
        properties = node.get("properties", {})
        if component not in properties:
            raise ValueError(f"visibility field path absent: {artifact_type}.{field_path}")
        node = properties[component]
    return node


def collect_visibility_access_edges(schema: dict[str, Any]) -> list[dict[str, Any]]:
    """Derive visibility edges from the executable ingress-receipt branches.

    This intentionally does not read x-visibility-edge-catalog or the
    VISIBILITY_REGISTRY constants.  It is used only to materialize the object
    inventory's independently extractable representation of actual typed
    ingress contracts.
    """
    receipt = schema["$defs"]["visibility_access_receipt"]
    rows: list[dict[str, Any]] = []
    for branch in receipt["oneOf"]:
        props = branch["properties"]
        source_ref = props["source_ref"]
        if source_ref["x-role"] != props["concrete_role"]["const"]:
            raise ValueError("visibility ingress role differs from typed source ref")
        if source_ref["x-artifact-types"] != [props["source_type"]["const"]]:
            raise ValueError("visibility ingress source type differs from typed source ref")
        rows.append({
            "information_item": props["information_item"]["const"],
            "information_ordinal": props["information_ordinal"]["const"],
            "consumer_stage": props["consumer_stage"]["const"],
            "stage_ordinal": props["stage_ordinal"]["const"],
            "visibility": props["visibility"]["const"],
            "rationale": next(
                edge["rationale"] for edge in VISIBILITY_ALLOWED_EDGES
                if edge["ordinal"] == props["edge_ordinal"]["const"]
            ),
            "source_type": props["source_type"]["const"],
            "source_field_path": props["source_field_path"]["const"],
            "projection_algorithm": props["projection_algorithm"]["const"],
            "output_type": props["output_type"]["const"],
            "output_field_path": props["output_field_path"]["const"],
            "concrete_role": props["concrete_role"]["const"],
            "ordinal": props["edge_ordinal"]["const"],
            "cardinality": props["cardinality"]["const"],
        })
    rows.sort(key=lambda edge: edge["ordinal"])
    return rows


def build_inventory(schema: dict[str, Any], schema_bytes: bytes,
                    generator_bytes: bytes) -> dict[str, Any]:
    inbound: dict[str, list[dict[str, Any]]] = {name: [] for name in TOP_LEVEL_NAMES}
    for consumer in TOP_LEVEL_NAMES:
        for edge in collect_artifact_edges(schema, consumer):
            target = edge.pop("target_type")
            if target not in inbound:
                raise ValueError(f"typed ref from {consumer} targets uninventoried type {target}")
            inbound[target].append(edge)

    visibility_ingress_edges = collect_visibility_access_edges(schema)
    objects = []
    for name in sorted(TOP_LEVEL_NAMES):
        top_schema = schema["$defs"][name.lower()]
        bindings = sorted(
            inbound[name],
            key=lambda item: (
                item["consumer_stage"], item["consumer_type"], item["role"],
                str(item["ordinal"]), item["field_path"],
            ),
        )
        objects.append({
            "type": name,
            "schema_ref": f"{SCHEMA_ID}#/$defs/{name.lower()}",
            "contract": top_schema["properties"]["contract"]["const"],
            "producer_role": PRODUCERS[name],
            "permitted_consumer_stages": sorted({item["consumer_stage"] for item in bindings}),
            "reference_bindings": bindings,
            # These rows are derived from the executable VISIBILITY_ACCESS
            # oneOf branches, never copied from the registry/catalog.
            "visibility_bindings": [
                copy.deepcopy(edge)
                for edge in visibility_ingress_edges
                if edge["output_type"] == name
            ],
            "self_hash_field": "self_hash",
            "payload_mode": "RAW_BYTES_ONLY" if name == "RAW_BYTE_MANIFEST" else "INLINE_CLOSED_FIELDS",
        })

    inventory = {
        "contract": "ppc5.object_inventory_registry.v9",
        "schema_version": SCHEMA_VERSION,
        "artifact_type": "OBJECT_INVENTORY_REGISTRY",
        "lifecycle_state": "PROPOSAL_ONLY",
        "producer_role": "INVENTORY_EXTRACTOR",
        "architecture_id": ARCHITECTURE_ID,
        "closed_world": True,
        "unknown_type_policy": "REJECT",
        "canonical_json": CANONICAL_JSON,
        "self_hash_algorithm": SELF_HASH_ALGORITHM,
        "schema_bundle": SCHEMA_ID,
        "schema_raw_sha256": sha256_bytes(schema_bytes),
        "generator": "build_contract_schema.py",
        "generator_raw_sha256": sha256_bytes(generator_bytes),
        "source_consensus_sha256": R8_CONSENSUS_SHA256,
        "objects": objects,
    }
    inventory["self_hash"] = self_hash(inventory)
    return inventory


def static_checks(schema: dict[str, Any], inventory: dict[str, Any]) -> None:
    for ref in all_local_refs(schema):
        resolve_local_ref(schema, ref)

    union_targets = [item["$ref"].removeprefix("#/$defs/").upper() for item in schema["oneOf"]]
    if union_targets != list(TOP_LEVEL_NAMES):
        raise ValueError("top-level schema union is not the declared artifact order")
    if len(set(TOP_LEVEL_NAMES)) != len(TOP_LEVEL_NAMES):
        raise ValueError("duplicate top-level artifact type")

    inventory_types = [item["type"] for item in inventory["objects"]]
    if inventory_types != sorted(TOP_LEVEL_NAMES):
        raise ValueError("inventory type set/order differs from schema top-level union")
    if inventory["self_hash"] != self_hash(inventory):
        raise ValueError("object inventory self-hash mismatch")

    semantic_types = set(SEMANTIC_REGISTRIES)
    for consumer in TOP_LEVEL_NAMES:
        for edge in collect_artifact_edges(schema, consumer):
            if edge["target_type"] == "RAW_BYTE_MANIFEST" and not edge["role"].startswith("RAW_"):
                raise ValueError(f"semantic-looking raw manifest role: {consumer}/{edge['role']}")
            if edge["target_type"] == "RAW_BYTE_MANIFEST" and edge["role"] in semantic_types:
                raise ValueError(f"semantic registry routed through raw bytes: {consumer}/{edge['role']}")

    # R09 negative closure: no release or postclaim type may be an input to a
    # replay or T14, and preclaim has exactly one final-T14 reference.
    forbidden_replay_targets = {"PRECLAIM_AUTHORITY_RECEIPT", "CLAIM_RELEASE_PACKAGE",
                                "CLAIM_EXPORT_RECEIPT", "CLAIM_AUDIT_RECEIPT"}
    for consumer in ("COLD_REPLAY_RECEIPT", "T14_FINAL_REPLAY_RESULT"):
        targets = {edge["target_type"] for edge in collect_artifact_edges(schema, consumer)}
        if targets & forbidden_replay_targets:
            raise ValueError(f"{consumer} has forbidden release/postclaim ancestry")
    final_t14_edges = [
        edge for edge in collect_artifact_edges(schema, "PRECLAIM_AUTHORITY_RECEIPT")
        if edge["target_type"] == "T14_FINAL_REPLAY_RESULT"
    ]
    if len(final_t14_edges) != 1:
        raise ValueError("PRECLAIM_AUTHORITY_RECEIPT must contain exactly one final-T14 edge")

    test_targets = {edge["target_type"] for edge in collect_artifact_edges(schema, "TEST_RESULT")}
    if "POPULATED_RUN_LOCK" not in test_targets:
        raise ValueError("T02-T12 results do not descend from POPULATED_RUN_LOCK")
    t13_targets = {edge["target_type"] for edge in collect_artifact_edges(schema,
                                                                          "T13_PREMODEL_TECHNICAL_GATE")}
    if not {"POPULATED_RUN_LOCK", "CONFORMANCE_RECEIPT"}.issubset(t13_targets):
        raise ValueError("T13 lacks populated-lock or CPU-conformance ancestry")
    conformance_targets = {
        edge["target_type"]
        for edge in collect_artifact_edges(schema, "CONFORMANCE_RECEIPT")
    }
    if not {"POPULATED_RUN_LOCK", "FIXTURE_GENERATOR_SPEC", "TEST_RESULT"}.issubset(
            conformance_targets):
        raise ValueError("CPU conformance lacks exact lock, fixtures, or T02-T12 results")
    forbidden_t13_targets = {"HUMAN_RUN_RATIFICATION_RECEIPT", "PRE_MODEL_AUTHORITY_RECEIPT"}
    if t13_targets & forbidden_t13_targets:
        raise ValueError("T13 has a forbidden ratification/authority back edge")

    dispatch_targets = {
        edge["target_type"]
        for edge in collect_artifact_edges(schema, "MODEL_DISPATCH_RECEIPT")
    }
    if "DISPATCH_PREFLIGHT_RECEIPT" not in dispatch_targets:
        raise ValueError("model dispatch lacks a typed prior preflight permit")
    runtime_targets = {
        edge["target_type"]
        for edge in collect_artifact_edges(schema, "RUNTIME_INTEGRITY_RECEIPT")
    }
    if not {"PRE_MODEL_AUTHORITY_RECEIPT", "DISPATCH_PREFLIGHT_RECEIPT",
            "COMPLETE_RUN_MANIFEST", "COMPLETE_MODEL_VIEW_MANIFEST"}.issubset(runtime_targets):
        raise ValueError("runtime integrity lacks authority/preflight/run/view closure")
    replay_targets = {
        edge["target_type"]
        for edge in collect_artifact_edges(schema, "COLD_REPLAY_RECEIPT")
    }
    if "RUNTIME_INTEGRITY_RECEIPT" not in replay_targets:
        raise ValueError("cold replay lacks runtime-integrity ancestry")

    ratification_targets = {
        edge["target_type"]
        for edge in collect_artifact_edges(schema, "ARCHITECTURE_RATIFICATION_RECEIPT")
    }
    if "GENERIC_ARCHITECTURE_HUMAN_RATIFICATION_BINDING" not in ratification_targets:
        raise ValueError("architecture receipt does not consume typed generic human authority")

    export_targets = {
        edge["target_type"]
        for edge in collect_artifact_edges(schema, "CLAIM_EXPORT_RECEIPT")
    }
    audit_targets = {
        edge["target_type"]
        for edge in collect_artifact_edges(schema, "CLAIM_AUDIT_RECEIPT")
    }
    if export_targets != {"CLAIM_RELEASE_PACKAGE"}:
        raise ValueError("claim export must consume only a released claim package")
    if not {"CLAIM_RELEASE_PACKAGE", "CLAIM_EXPORT_RECEIPT"}.issubset(audit_targets):
        raise ValueError("claim audit must be downstream of release and export")
    if "CANDIDATE_DECISION_RECEIPT" in export_targets | audit_targets:
        raise ValueError("candidate decision bypasses preclaim/release authority")

    # R07 negative closure: controller consumes emission, never privileged route
    # or sanitized projection.
    controller_targets = {
        edge["target_type"] for edge in collect_artifact_edges(schema, "CONTROLLER_TRANSITION_RECEIPT")
    }
    if controller_targets & {"PRIVILEGED_ROUTE_RECEIPT", "SANITIZED_RESPONSE_PROJECTION"}:
        raise ValueError("controller has forbidden privileged route/projection capability")
    if "INTERVENTION_EMISSION_RECEIPT" not in controller_targets:
        raise ValueError("controller lacks typed public-emission completion input")

    # R06/R07 visibility closure: all 83 inherited allowed cells plus the one
    # repaired response/THINK cell name real fields and unique concrete roles.
    catalog = schema["x-visibility-edge-catalog"]
    if len(catalog) != 84 or len({edge["concrete_role"] for edge in catalog}) != 84:
        raise ValueError("visibility allowed-edge catalog is not closed and role-unique")
    for edge in catalog:
        schema_at_field_path(schema, edge["source_type"], edge["source_field_path"])
        schema_at_field_path(schema, edge["output_type"], edge["output_field_path"])
        if edge["source_type"] == edge["output_type"]:
            raise ValueError("visibility ingress contains a self-edge")
    ingress_catalog = collect_visibility_access_edges(schema)
    if ingress_catalog != catalog:
        raise ValueError("typed visibility ingress branches differ from registry catalog")
    response_think = [
        edge for edge in catalog
        if edge["information_item"] == "RESOLVED_RESPONSE_BYTES" and edge["consumer_stage"] == "THINK"
    ]
    if response_think != [{
        "information_item": "RESOLVED_RESPONSE_BYTES",
        "information_ordinal": VISIBILITY_INFORMATION_ITEMS.index("RESOLVED_RESPONSE_BYTES"),
        "consumer_stage": "THINK",
        "stage_ordinal": VISIBILITY_STAGES.index("THINK"),
        "visibility": "DERIVED_ONLY",
        "rationale": "sole emitted-public-byte path into public_view_body.last_read and MODEL_VIEW",
        "source_type": "INTERVENTION_EMISSION_RECEIPT",
        "source_field_path": "emitted_public_bytes",
        "projection_algorithm": "EMITTED_PUBLIC_BYTES_TO_LAST_READ_TO_MODEL_VIEW_V1",
        "output_type": "VISIBILITY_ACCESS_RECEIPT",
        "output_field_path": "projected_value_canonical_json",
        "concrete_role": "INTERVENTION_EMISSION_TO_PUBLIC_VIEW",
        "ordinal": response_think[0]["ordinal"] if response_think else -1,
        "cardinality": "ONE",
    }]:
        raise ValueError("RESOLVED_RESPONSE_BYTES/THINK is not the sole emission-to-public-view edge")
    inventory_catalog = sorted(
        [edge for artifact in inventory["objects"] for edge in artifact["visibility_bindings"]],
        key=lambda edge: edge["ordinal"],
    )
    if inventory_catalog != catalog:
        raise ValueError("inventory visibility bindings do not exactly equal the schema catalog")

    # R13 literal/hash are present in the reusable rendering schema, with the
    # D1D-specific resource qualification directly adjacent to the claim.
    serialized_claim_schema = json.dumps(defs["claim_rendering"], ensure_ascii=False, sort_keys=True)
    for required in (CLAIM_TEXTS["PPC5_D1D_DREAM_TO_SLEEP_TOTAL_POLICY"], FIXED_QUALIFICATION,
                     RESOURCE_QUALIFICATION, sha256_bytes(RESOURCE_QUALIFICATION.encode("utf-8"))):
        if required not in serialized_claim_schema:
            raise ValueError("D1D inseparable rendering is incomplete")
    d1d_variant = next(
        variant
        for variant in defs["claim_rendering"]["oneOf"]
        if variant["properties"]["claim_id"].get("const")
        == "PPC5_D1D_DREAM_TO_SLEEP_TOTAL_POLICY"
    )
    segment_constants = [
        item["const"]
        for item in d1d_variant["properties"]["ordered_inseparable_segments"]["prefixItems"]
    ]
    if segment_constants != [
        CLAIM_TEXTS["PPC5_D1D_DREAM_TO_SLEEP_TOTAL_POLICY"],
        RESOURCE_QUALIFICATION,
        FIXED_QUALIFICATION,
    ]:
        raise ValueError("D1D resource qualification is not adjacent to the claim")


def validate_with_jsonschema(schema: dict[str, Any], inventory: dict[str, Any]) -> str:
    try:
        import jsonschema  # type: ignore
    except ImportError:
        return "jsonschema package unavailable; structural checks passed"
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema).validate(inventory)
    return "Draft 2020-12 schema and generated inventory instance validated"


def generate(check_only: bool) -> tuple[int, str]:
    consensus_bytes = R8_CONSENSUS.read_bytes()
    if sha256_bytes(consensus_bytes) != R8_CONSENSUS_SHA256:
        raise SystemExit("frozen r8 consensus hash mismatch; refusing successor generation")

    schema = build_schema()
    schema_bytes = pretty_bytes(schema)
    generator_bytes = Path(__file__).read_bytes()
    inventory = build_inventory(schema, schema_bytes, generator_bytes)
    static_checks(schema, inventory)
    validation = validate_with_jsonschema(schema, inventory)
    inventory_bytes = pretty_bytes(inventory)

    outputs = ((SCHEMA_PATH, schema_bytes), (INVENTORY_PATH, inventory_bytes))
    if check_only:
        stale = [str(path) for path, data in outputs if not path.exists() or path.read_bytes() != data]
        if stale:
            raise SystemExit("generated outputs are stale: " + ", ".join(stale))
    else:
        for path, data in outputs:
            path.write_bytes(data)

    return len(TOP_LEVEL_NAMES), validation


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify checked-in outputs without writing")
    args = parser.parse_args()
    count, validation = generate(args.check)
    action = "verified" if args.check else "wrote"
    print(f"{action} {SCHEMA_PATH.name} and {INVENTORY_PATH.name}: {count} top-level artifact types")
    print(validation)
    print("proposal-only: no fixtures, models, training, behavioral runs, GPU work, claims, or release executed")


if __name__ == "__main__":
    main()
