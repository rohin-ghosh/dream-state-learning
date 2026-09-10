#!/usr/bin/env python3
"""Author the frozen PPC5r9 T02--T14 proposal-only fixture universe.

This is an authoring utility, not a fixture executor. It performs no model,
tokenizer, provider, trainer, environment, CPU-behavioral, or GPU operation.
Its output is a fully materialized normative JSON artifact: no axis,
applicability, count, mutation, result, or branch key is deferred to runtime.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = HERE / "ppc5r9_fixture_universe.json"
ARCH = "PPC5R9_PUBLIC_PATHWAY_CONSOLIDATION"
PROPOSAL = "PROPOSAL_ONLY"
SCHEMA_VERSION = 9

PREFIX = [
    "FIXTURE_SCHEMA_INVALID", "NONCANONICAL_BYTES", "SELF_HASH_MISMATCH",
    "REFERENCE_TARGET_MISSING", "REFERENCE_RUN_MISMATCH",
    "REFERENCE_TYPE_MISMATCH", "REFERENCE_ROLE_MISMATCH",
    "REFERENCE_ORDINAL_OR_CARDINALITY", "ORDER_OR_UNIQUENESS_INVALID",
]

LOCAL = {
    "PPC5R9_T02": ["DESIGN_LOCK_ANCESTRY", "ENTROPY_BINDING", "PARAMETER_DECODE", "PROPOSAL_ORDER", "ACCEPTANCE_FIRST_FAILURE", "RECIPIENT_DONOR_IDENTITY", "SEED_PREIMAGE", "D1A_CONTROL_MANIFEST", "NOMINEE_CAPACITY_ORDER", "OVERLAP_DERIVATION", "POINTWISE_SUPPORT_POWER"],
    "PPC5R9_T03": ["INTEGRITY", "PREDISPATCH_BUDGET", "MISSING_CALL", "TOKEN_LIMIT", "PARSE_ERROR", "LOGICAL_ALLOWANCE", "DOMAIN", "REFERENCE", "PREDICTION", "SCHEDULE", "PROVIDER_MISSING", "ENVIRONMENT_INVALID", "SUCCESS", "UNIQUE_CONTROLLER_ROW", "QUEUE_FINALIZATION", "TRANSITION_CAUSE", "DISPATCH_CLOSURE"],
    "PPC5R9_T04": ["DREAM_INPUT_BINDING", "DREAM_RENDER_OR_DEBIT", "DREAM_MISSING", "DREAM_PARSE", "DREAM_ID_ORDER_FOCUS_CAPACITY", "CONTEXT_DEPENDENCY", "CONTEXT_RENDER", "EMISSION_CAPABILITY", "DISPATCH_BINDING", "LIFE_MEMBERSHIP"],
    "PPC5R9_T05": ["SEMANTIC_TABLE", "FP32_FINITE", "RESPONSE_TOKEN_SEQUENCE", "HALF_EVEN_QUANTIZATION", "ARGMAX_TIEBREAK", "PROVIDER_MISSING", "PROVIDER_AUDIT", "DESCRIPTIVE_ISOLATION", "TYPED_REGISTRY"],
    "PPC5R9_T06": ["DESIGN_ANCESTRY", "LIFE_MEMBERSHIP_EQUALITY", "ORIGIN_ELIGIBILITY", "WRONG_LIFE_MATCH", "DERANGEMENT", "DOSE_OPPORTUNITY", "CONTROL_MANIFEST_CARDINALITY", "ARM_NEUTRAL_PROJECTION", "POINTWISE_POWER_BINDING"],
    "PPC5R9_T07": ["FINITE_WORLD", "PATH_ENUMERATION", "SOURCE_DISJOINTNESS", "SUBSET_ORACLE", "FULL_PATH_ORACLE", "ALTERNATE_PATH_ORACLE", "CUT", "TWIN", "SHAM", "PARITY", "RECURSIVE_REFERENCE_CLOSURE", "AUDIT_SPLIT", "VIEW_REPLAY_RETENTION", "VISIBILITY_EDGE_EQUALITY"],
    "PPC5R9_T08": ["ASSIGNMENT_AND_NONCE", "ROUTE_TARGET_MATCH", "PROVIDER_RESULT", "INTERVENTION_SELECTION", "RESTRICTED_PROJECTION", "EMISSION_EQUALITY", "QUEUE_EXCLUSIVITY", "SCHEDULE_COMMITMENT", "PUBLIC_VIEW_INFLUENCE", "DISPATCH_CLOSURE", "AUDIT_COMPLETENESS"],
    "PPC5R9_T09": ["RUN_INVALID", "CONSTRUCTION_FAIL", "MISSING_NO_RETRY", "ASSIGNED_POLICY_STATUS", "TERMINAL_NO_ACTION", "OBSERVED", "CONTEXT_POLICY_PROPAGATION", "ENDPOINT_LOCALITY", "DISPATCH_ANCESTRY"],
    "PPC5R9_T10": ["ROOT_POLICY_DEPENDENCY", "ROOT_STATUS", "WRITER_SANITIZATION", "CORPUS", "TRAINER", "VALIDATION", "PUBLICATION", "PROVIDER_CONTINUATION", "BEHAVIOR_CONTINUATION", "DISPATCH_BINDING", "RESOURCE_OWNERSHIP", "RESOURCE_CONSERVATION", "RESOURCE_NONADJUSTMENT", "QUALIFICATION_ADJACENCY"],
    "PPC5R9_T11": ["MEMBERSHIP_AND_AGGREGATE", "SAFETY_TEMPLATE", "MISSING_DOMINANCE", "CANONICAL_RATIONAL", "TAIL_ARITHMETIC", "CP_BRACKET", "STRICT_DIRECTION", "MISSINGNESS", "GATE_IUT", "ASSAY_MAX_P", "HOLM_FAMILY", "CLAIM_LITERAL", "CONDITIONAL_POWER", "POINTWISE_JOINT_POWER"],
    "PPC5R9_T12": ["VISIBILITY_PRODUCT_SHAPE", "VISIBILITY_CELL_VALUE", "CONCRETE_CAPABILITY_ROLE", "FORBIDDEN_TAINT", "SCHEMA_REF_RECURSION", "OBJECT_INVENTORY_EDGE", "VISIBILITY_EDGE", "THREE_WAY_EDGE_EQUALITY", "TYPED_REGISTRY", "TRANSITION_CAUSE", "DESIGN_ANCESTRY", "LIFE_AND_CONTROL_CLOSURE", "VIEW_REPLAY_RETENTION", "RESOURCE_AND_QUALIFICATION", "PREFLIGHT_DENIAL"],
    "PPC5R9_T13": ["NARROW_T01", "DESIGN_TEMPORAL_DAG", "POPULATED_LOCK", "FIXTURE_UNIVERSE_COMPLETENESS", "TEST_RESULT_ORDER", "TYPED_REGISTRIES", "LIFE_CONTROL_CLOSURE", "CLAIM_HOLM_BYTES", "SEALER_INDEPENDENCE", "FRESH_REVIEW", "ADVOCATE_NONOVERRIDE", "CONDITIONAL_POWER", "POINTWISE_JOINT_POWER", "PREFLIGHT_NO_PROCESS", "FORBIDDEN_FUTURE_INPUT", "AUTHORITY_TOPOLOGY"],
    "PPC5R9_T14": ["T02_T13_PREDECESSORS", "RUNTIME_INTEGRITY", "TRANSITION_AND_QUEUE_REPLAY", "AUDIT_SPLIT", "EMISSION_NONINTERFERENCE", "SEED_VIEW_DISPATCH_CLOSURE", "DREAM_SLEEP", "LIFE_OBSERVATION_GATE", "D1A_CONTROL_MANIFEST", "POINTWISE_POWER", "RESOURCE_OVERLAP_SCOPE", "CANDIDATE_DECISIONS", "QUALIFICATION_AND_FORBIDDEN_CLAIMS", "RELEASE_BYTES_FORBIDDEN", "REPLAY_INDEPENDENCE", "REPLAY_AGREEMENT", "SINGLE_FINAL_T14_EDGE"],
}

REGISTRY_KINDS = [
    "CONTROLLER_REGISTRY", "TRANSITION_CAUSE_REGISTRY", "STATUS_REGISTRY",
    "VISIBILITY_REGISTRY", "GATE_REGISTRY", "EVIDENCE_ROLE_REGISTRY",
    "DEPENDENCY_REGISTRY", "CLAIM_REGISTRY", "RESOURCE_REGISTRY",
    "OBJECT_INVENTORY_REGISTRY", "CONTRACT_SCHEMA_REGISTRY",
    "ALLOWED_DISPATCH_REGISTRY", "AUTHORITY_REGISTRY",
]

DISPATCH_BINDINGS = [
    "/model_dispatch_receipt/common_seed_entry_ref",
    "/model_dispatch_receipt/run_id",
    "/model_dispatch_receipt/recipient_life_id",
    "/model_dispatch_receipt/sample_ordinal",
    "/model_dispatch_receipt/step_ordinal",
    "/model_dispatch_receipt/call_role",
    "/model_dispatch_receipt/call_ordinal",
    "/model_dispatch_receipt/life_sample_ref",
    "/model_view/ledger_head_sha256",
    "/model_view/rendered_input_bytes",
    "/model_view/response_think_ingress_ref",
    "/model_dispatch_receipt/input_token_ids",
    "/model_dispatch_receipt/model_ref",
    "/model_dispatch_receipt/tokenizer_ref",
    "/model_dispatch_receipt/prompt_ref",
    "/model_dispatch_receipt/preflight_ref",
    "/model_dispatch_receipt/raw_output_ref",
    "/model_dispatch_receipt/output_token_ids",
    "/model_dispatch_receipt/status",
    "/model_dispatch_receipt/debit",
    "/model_dispatch_receipt/rendered_seed_uint64",
    "/controller_transition_receipt/self_hash",
    "/complete_run_manifest/model_dispatch_refs",
]

PRIVILEGED_FIELDS = ["condition", "source", "match_keys", "provider_scores", "nonce", "mapping"]

SCHEMA = json.loads((ROOT / "contracts.schema.json").read_text())
DEFS = SCHEMA["$defs"]
TYPE_TO_DEF = {
    body.get("properties", {}).get("artifact_type", {}).get("const"): name
    for name, body in DEFS.items()
    if isinstance(body, dict) and body.get("x-top-level-artifact")
}
EXISTING_ARTIFACT_FILES = {
    "ALLOWED_DISPATCH_REGISTRY": "allowed_dispatch_registry.json",
    "AUTHORITY_REGISTRY": "authority_registry.json",
    "CLAIM_REGISTRY": "claim_registry.json",
    "CONTRACT_SCHEMA_REGISTRY": "contract_schema_registry.json",
    "CONTROLLER_REGISTRY": "controller_registry.json",
    "DEPENDENCY_REGISTRY": "dependency_registry.json",
    "EVIDENCE_ROLE_REGISTRY": "evidence_role_registry.json",
    "GATE_REGISTRY": "gate_registry.json",
    "OBJECT_INVENTORY_REGISTRY": "object_inventory.json",
    "RESOURCE_REGISTRY": "resource_registry.json",
    "STATUS_REGISTRY": "status_registry.json",
    "TRANSITION_CAUSE_REGISTRY": "transition_cause_registry.json",
    "VISIBILITY_REGISTRY": "visibility_registry.json",
}
DESIGN_ARTIFACT_TYPES = {"PRE_ENTROPY_DESIGN_LOCK"}


def _merge_schema(left: dict, right: dict) -> dict:
    """Merge an object-level oneOf branch into its common object schema."""
    out = copy.deepcopy(left)
    out.pop("oneOf", None)
    out.pop("anyOf", None)
    for key, value in right.items():
        if key == "properties":
            out.setdefault("properties", {})
            for name, child in value.items():
                if name in out["properties"] and isinstance(out["properties"][name], dict) and isinstance(child, dict):
                    # A branch-local scalar/type constraint replaces the
                    # common alternative schema (e.g. symbol|null -> null).
                    # A branch containing only nested properties refines the
                    # common object/ref schema (controller counter tuples).
                    if set(child) & {"type", "const", "enum", "$ref", "oneOf", "anyOf"}:
                        out["properties"][name] = copy.deepcopy(child)
                    else:
                        merged = copy.deepcopy(out["properties"][name])
                        merged.update(copy.deepcopy(child))
                        out["properties"][name] = merged
                else:
                    out["properties"][name] = copy.deepcopy(child)
        elif key == "required":
            out[key] = list(dict.fromkeys(list(out.get(key, [])) + list(value)))
        else:
            out[key] = copy.deepcopy(value)
    return out


def _generation_schema(node: dict) -> dict:
    """Resolve refs and choose one non-null branch before field population."""
    node = resolve_schema(node)
    if not isinstance(node, dict):
        return node
    if "allOf" in node:
        out = {k: copy.deepcopy(v) for k, v in node.items() if k != "allOf"}
        for branch in node["allOf"]:
            out = _merge_schema(out, _generation_schema(branch))
        node = out
    if "oneOf" in node:
        branches = [b for b in node["oneOf"] if b.get("type") != "null"] or node["oneOf"]
        return _merge_schema(node, _generation_schema(branches[0]))
    if "anyOf" in node:
        branches = [b for b in node["anyOf"] if b.get("type") != "null"] or node["anyOf"]
        return _merge_schema(node, _generation_schema(branches[0]))
    return node


def schema_sample(node, depth=0, salt="root"):
    if depth > 24:
        raise ValueError("schema sample recursion limit")
    if "$ref" in node:
        ref = node["$ref"]
        if not ref.startswith("#/$defs/"):
            raise ValueError(f"nonlocal ref {ref}")
        return schema_sample(DEFS[ref.rsplit("/", 1)[-1]], depth + 1, salt)
    node = _generation_schema(node)
    if "const" in node:
        return copy.deepcopy(node["const"])
    if "enum" in node:
        return copy.deepcopy(node["enum"][0])
    typ = node.get("type")
    if typ == "object" or "properties" in node:
        props = node.get("properties", {})
        # Only required fields are populated. Object-level branch constraints
        # have already been merged, so GRANT/DENY, PASS/FAIL and missing/non-
        # missing variants cannot be accidentally combined.
        return {key: schema_sample(props[key], depth + 1, salt + "/" + key)
                for key in node.get("required", [])}
    if typ == "array":
        if "prefixItems" in node:
            return [schema_sample(x, depth + 1, salt + f"/{i}")
                    for i, x in enumerate(node["prefixItems"])]
        count = int(node.get("minItems", 0))
        if node.get("items") is False:
            return []
        return [schema_sample(node.get("items", {}), depth + 1, salt + f"/{i}")
                for i in range(count)]
    if typ == "integer":
        lower = int(node.get("minimum", 0))
        upper = node.get("maximum")
        room = 0 if upper is not None and lower >= upper else int(hashlib.sha256(salt.encode()).hexdigest()[:4], 16) % 2
        return lower + room
    if typ == "number":
        return int(node.get("minimum", 0))
    if typ == "boolean":
        return True
    if typ == "null":
        return None
    if typ == "string" or typ is None:
        pattern = node.get("pattern", "")
        if "0-9a-f" in pattern or node.get("minLength") == 64 == node.get("maxLength"):
            return hashlib.sha256(salt.encode()).hexdigest()
        if pattern.startswith("^[a-z]"):
            return "fixture_" + hashlib.sha256(salt.encode()).hexdigest()[:12]
        if pattern.startswith("^[a-z0-9]"):
            return "fixture-" + hashlib.sha256(salt.encode()).hexdigest()[:12]
        if pattern.startswith("^[A-Z]"):
            return "X_" + hashlib.sha256(salt.encode()).hexdigest()[:12].upper()
        if pattern.startswith("^RAW_"):
            return "RAW_FIXTURE"
        return "X"
    raise ValueError(f"unsupported schema node {node}")


def compute_self_hash(obj):
    body = copy.deepcopy(obj)
    body.pop("self_hash", None)
    raw = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    pre = (body["contract"] + "\0" + str(body["schema_version"]) + "\0" + body["artifact_type"] + "\0").encode() + raw + b"\n"
    return hashlib.sha256(pre).hexdigest()


def artifact_instance(artifact_type, salt="target", raw_role=None):
    if artifact_type in EXISTING_ARTIFACT_FILES:
        # Checked-in semantic registries are proposal artifacts. Copy their
        # exact bytes; never promote them merely to construct a fixture.
        return json.loads((ROOT / EXISTING_ARTIFACT_FILES[artifact_type]).read_text())
    if artifact_type == "RAW_BYTE_MANIFEST":
        role = raw_role or "RAW_FIXTURE_PAYLOAD"
        raw_schema = resolve_schema(DEFS[TYPE_TO_DEF[artifact_type]])
        branches = [branch for branch in raw_schema.get("oneOf", [])
                    if role in branch.get("properties", {}).get("raw_role", {}).get("enum", [])]
        if len(branches) != 1:
            raise ValueError(f"RAW_BYTE_MANIFEST role has {len(branches)} lifecycle branches: {role}")
        obj = schema_sample(branches[0], salt=salt)
    else:
        obj = schema_sample(DEFS[TYPE_TO_DEF[artifact_type]], salt=salt)
    if "lifecycle_state" in obj and artifact_type != "RAW_BYTE_MANIFEST":
        obj["lifecycle_state"] = (
            "PROPOSAL_ONLY" if artifact_type == "FIXTURE_GENERATOR_SPEC"
            else "RATIFIED_DESIGN" if artifact_type in DESIGN_ARTIFACT_TYPES
            else "EXECUTED"
        )
    if artifact_type == "RAW_BYTE_MANIFEST":
        payload = HERE / "fixture_payload.txt"
        obj.update({
            "raw_role": raw_role or "RAW_FIXTURE_PAYLOAD",
            "media_type": "text/plain",
            "relative_path": str(payload.relative_to(ROOT.parents[2])),
            "byte_length": payload.stat().st_size,
            "raw_sha256": h_file(payload),
        })
    if "self_hash" in obj:
        obj["self_hash"] = compute_self_hash(obj)
    return obj


def pointer_get(obj, pointer):
    cur = obj
    for token in pointer.strip("/").split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        cur = cur[int(token)] if isinstance(cur, list) else cur[token]
    return cur


def pointer_set(obj, pointer, value):
    tokens = pointer.strip("/").split("/")
    cur = obj
    for token in tokens[:-1]:
        token = token.replace("~1", "/").replace("~0", "~")
        cur = cur[int(token)] if isinstance(cur, list) else cur[token]
    final = tokens[-1].replace("~1", "/").replace("~0", "~")
    if isinstance(cur, list): cur[int(final)] = value
    else: cur[final] = value


def resolve_schema(node):
    while isinstance(node,dict) and "$ref" in node:
        ref=node["$ref"]
        if not ref.startswith("#/$defs/"): break
        base=copy.deepcopy(DEFS[ref.rsplit("/",1)[-1]])
        siblings={k:v for k,v in node.items() if k!="$ref"}
        if not siblings:
            node=base
        elif "oneOf" in base:
            common={k:v for k,v in base.items() if k!="oneOf"}
            node={**common,"oneOf":[_merge_schema(_merge_schema(common,b),siblings)
                                     for b in base["oneOf"]]}
        else:
            # Preserve a referenced schema's own alternatives; _merge_schema
            # is branch-oriented and intentionally drops them.
            saved_oneof=base.get("oneOf")
            node=_merge_schema(base,siblings)
            if saved_oneof is not None and "oneOf" not in siblings:
                node["oneOf"]=saved_oneof
    return node


def _schema_errors(value, node, path=""):
    """Small independent validator for every keyword used by this schema.

    It is deliberately local to proposal authoring: it does not execute a
    fixture or share code with either eventual fixture implementation.
    """
    if not isinstance(node, dict):
        return []
    if "$ref" in node:
        ref = node["$ref"]
        if not ref.startswith("#/$defs/"):
            return [f"{path}: nonlocal ref {ref}"]
        # JSON Schema draft 2020-12 applies $ref siblings conjunctively.
        # Do not merge sibling consts into every oneOf branch (which would
        # erase branch distinctions); validate the referenced definition
        # and the local refinement as two independent constraints.
        base = DEFS[ref.rsplit("/", 1)[-1]]
        siblings = {k: v for k, v in node.items() if k != "$ref"}
        return (_schema_errors(value, base, path) +
                (_schema_errors(value, siblings, path) if siblings else []))
    if "allOf" in node:
        errors = []
        common = {k: v for k, v in node.items() if k != "allOf"}
        errors += _schema_errors(value, common, path)
        for part in node["allOf"]:
            errors += _schema_errors(value, part, path)
        return errors
    if "oneOf" in node:
        matches = []
        for branch in node["oneOf"]:
            candidate = _merge_schema(node, branch)
            matches.append(not _schema_errors(value, candidate, path))
        if sum(matches) != 1:
            return [f"{path}: oneOf matched {sum(matches)} branches"]
        return []
    if "anyOf" in node:
        if not any(not _schema_errors(value, _merge_schema(node, branch), path)
                   for branch in node["anyOf"]):
            return [f"{path}: no anyOf branch matched"]
        return []
    errors = []
    if "const" in node and value != node["const"]:
        errors.append(f"{path}: {value!r} != const {node['const']!r}")
    if "enum" in node and value not in node["enum"]:
        errors.append(f"{path}: {value!r} outside enum")
    typ = node.get("type")
    valid_type = {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
        "null": value is None,
    }.get(typ, True)
    if not valid_type:
        return errors + [f"{path}: expected {typ}, got {type(value).__name__}"]
    if isinstance(value, dict):
        props = node.get("properties", {})
        missing = [name for name in node.get("required", []) if name not in value]
        errors += [f"{path}: missing {name}" for name in missing]
        if node.get("additionalProperties") is False:
            errors += [f"{path}: additional property {name}" for name in value if name not in props]
        for name, child in value.items():
            if name in props:
                errors += _schema_errors(child, props[name], path + "/" + name.replace("~", "~0").replace("/", "~1"))
    if isinstance(value, list):
        if len(value) < node.get("minItems", 0):
            errors.append(f"{path}: array below minItems")
        if "maxItems" in node and len(value) > node["maxItems"]:
            errors.append(f"{path}: array above maxItems")
        if node.get("uniqueItems") and len({json.dumps(x, sort_keys=True, separators=(",", ":")) for x in value}) != len(value):
            errors.append(f"{path}: array not unique")
        if "prefixItems" in node:
            for i, child in enumerate(value[:len(node["prefixItems"])]):
                errors += _schema_errors(child, node["prefixItems"][i], path + f"/{i}")
            if node.get("items") is False and len(value) > len(node["prefixItems"]):
                errors.append(f"{path}: additional tuple items")
        elif isinstance(node.get("items"), dict):
            for i, child in enumerate(value):
                errors += _schema_errors(child, node["items"], path + f"/{i}")
    if isinstance(value, str):
        if len(value) < node.get("minLength", 0):
            errors.append(f"{path}: string below minLength")
        if "maxLength" in node and len(value) > node["maxLength"]:
            errors.append(f"{path}: string above maxLength")
        if "pattern" in node and re.fullmatch(node["pattern"], value) is None:
            errors.append(f"{path}: pattern mismatch")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in node and value < node["minimum"]:
            errors.append(f"{path}: below minimum")
        if "maximum" in node and value > node["maximum"]:
            errors.append(f"{path}: above maximum")
    return errors


def validate_artifact(obj):
    artifact_type = obj.get("artifact_type")
    if artifact_type not in TYPE_TO_DEF:
        raise ValueError(f"unknown artifact type {artifact_type!r}")
    errors = _schema_errors(obj, DEFS[TYPE_TO_DEF[artifact_type]], "/target_artifact")
    if errors:
        raise ValueError(f"{artifact_type} schema invalid: {errors[:8]}")
    if obj.get("self_hash") != compute_self_hash(obj):
        raise ValueError(f"{artifact_type} self hash invalid")
    expected_lifecycle = (
        obj.get("lifecycle_state") if artifact_type == "RAW_BYTE_MANIFEST"
        else "PROPOSAL_ONLY" if artifact_type in EXISTING_ARTIFACT_FILES or artifact_type == "FIXTURE_GENERATOR_SPEC"
        else "RATIFIED_DESIGN" if artifact_type == "PRE_ENTROPY_DESIGN_LOCK"
        else "EXECUTED"
    )
    if "lifecycle_state" in obj and obj["lifecycle_state"] != expected_lifecycle:
        raise ValueError(f"{artifact_type}: lifecycle {obj['lifecycle_state']} != {expected_lifecycle}")


def _walk_artifact_refs(value, node, path=""):
    node = resolve_schema(node)
    if not isinstance(node, dict):
        return []
    if node.get("x-artifact-ref"):
        return [(path, value, node)]
    if isinstance(value, dict):
        props = node.get("properties", {})
        return [row for name, child in value.items() if name in props
                for row in _walk_artifact_refs(child, props[name], path + "/" + name)]
    if isinstance(value, list):
        if "prefixItems" in node:
            return [row for i, child in enumerate(value)
                    for row in _walk_artifact_refs(child, node["prefixItems"][i], path + f"/{i}")]
        item = node.get("items", {})
        return [row for i, child in enumerate(value)
                for row in _walk_artifact_refs(child, item, path + f"/{i}")]
    return []


def validate_bundle(bundle):
    """Validate target, companions, self hashes, and full typed ref closure."""
    if bundle.get("lifecycle_state") != "PROPOSAL_ONLY" or not bundle.get("reference_closure_complete"):
        raise ValueError("fixture bundle lifecycle/closure marker invalid")
    target = bundle["target_artifact"]
    if target["artifact_type"] != bundle["target_artifact_type"] or target["self_hash"] != bundle["target_artifact_self_hash"]:
        raise ValueError("fixture bundle target header mismatch")
    artifacts = [target]
    for row in bundle["companion_artifacts"]:
        obj = json.loads(row["canonical_json"])
        if cj(obj) != row["canonical_json"]:
            raise ValueError("noncanonical companion bytes")
        if obj["artifact_type"] != row["artifact_type"] or obj["self_hash"] != row["self_hash"]:
            raise ValueError("companion header mismatch")
        artifacts.append(obj)
    by_hash = {}
    for obj in artifacts:
        validate_artifact(obj)
        if obj["artifact_type"] == "RAW_BYTE_MANIFEST":
            raw_path = ROOT.parents[2] / obj["relative_path"]
            if not raw_path.is_file() or raw_path.stat().st_size != obj["byte_length"] or h_file(raw_path) != obj["raw_sha256"]:
                raise ValueError(f"RAW_BYTE_MANIFEST does not bind actual bytes: {obj['relative_path']}")
        if obj["self_hash"] in by_hash:
            raise ValueError("duplicate artifact self hash in mini-bundle")
        by_hash[obj["self_hash"]] = obj
    for obj in artifacts:
        schema = DEFS[TYPE_TO_DEF[obj["artifact_type"]]]
        for path, ref, ref_schema in _walk_artifact_refs(obj, schema):
            referred = by_hash.get(ref["self_hash"])
            if referred is None:
                raise ValueError(f"{obj['artifact_type']}{path}: missing reference target")
            if referred["artifact_type"] not in ref_schema["x-artifact-types"] or referred["artifact_type"] != ref["artifact_type"]:
                raise ValueError(f"{obj['artifact_type']}{path}: reference type mismatch")
            if "run_id" in ref and "run_id" in referred and ref["run_id"] != referred["run_id"]:
                raise ValueError(f"{obj['artifact_type']}{path}: reference run mismatch")
    return True


def complete_artifact(artifact_type, key, cache, constructing=None, raw_role=None):
    """Construct one closed reference-DAG node and all predecessors."""
    constructing = set() if constructing is None else constructing
    cache_key=(artifact_type,key)
    if cache_key in cache: return cache[cache_key]
    if cache_key in constructing:
        raise ValueError(f"artifact reference cycle: {cache_key}")
    constructing.add(cache_key)
    obj=artifact_instance(artifact_type, salt=f"{artifact_type}:{key}", raw_role=raw_role)
    if "run_id" in obj: obj["run_id"]="fixture_run"
    schema=DEFS[TYPE_TO_DEF[artifact_type]]

    def has_artifact_ref(node):
        if not isinstance(node,dict): return False
        if node.get("x-artifact-ref"): return True
        if "$ref" in node:
            ref=node["$ref"]
            return ref.startswith("#/$defs/") and has_artifact_ref(DEFS[ref.rsplit("/",1)[-1]])
        return any(has_artifact_ref(x) for key in ("oneOf","anyOf","allOf")
                   for x in node.get(key,[]))

    # Optional typed references that are named mutation targets must exist
    # in the before artifact and must be backed by a real companion.  Add
    # their non-null branch before filling the reference DAG.  Ordinary
    # optional scalar fields remain absent.
    generation_schema=_generation_schema(schema)
    for field,node in generation_schema.get("properties",{}).items():
        if field not in obj and has_artifact_ref(node):
            obj[field]=schema_sample(node,salt=f"{artifact_type}:{key}/{field}")

    def fill(value,node,path):
        node=resolve_schema(node)
        if not isinstance(node,dict): return value
        if node.get("x-artifact-ref"):
            target_type=node["x-artifact-types"][0]
            ref_role=node.get("x-role",node.get("properties",{}).get("role",{}).get("const","REFERENCE"))
            ref_ordinal=node.get("x-ordinal",node.get("properties",{}).get("ordinal",{}).get("const",0))
            target_key=f"{ref_role}:{ref_ordinal}"
            target=complete_artifact(target_type,target_key,cache,constructing,
                                     raw_role=ref_role if target_type=="RAW_BYTE_MANIFEST" else None)
            out=copy.deepcopy(value) if isinstance(value,dict) else schema_sample(node, salt=path)
            if "artifact_type" in out: out["artifact_type"]=target_type
            if "self_hash" in out: out["self_hash"]=target["self_hash"]
            if "run_id" in out: out["run_id"]=target.get("run_id","fixture_run")
            return out
        if isinstance(value,dict):
            props=node.get("properties",{})
            for k in list(value):
                if k in props: value[k]=fill(value[k],props[k],path+"/"+k)
            return value
        if isinstance(value,list):
            if "prefixItems" in node:
                return [fill(v,node["prefixItems"][i],path+f"/{i}") for i,v in enumerate(value)]
            item=node.get("items",{})
            return [fill(v,item,path+f"/{i}") for i,v in enumerate(value)]
        return value

    obj=fill(obj,schema,"/"+artifact_type)
    if "self_hash" in obj: obj["self_hash"]=compute_self_hash(obj)
    cache[cache_key]=obj
    constructing.remove(cache_key)
    return obj


_BUNDLE_CACHE={}
_BYTE_TABLE={}


def intern_canonical_bytes(text):
    digest=h_bytes(text.encode())
    prior=_BYTE_TABLE.setdefault(digest,text)
    if prior!=text:
        raise ValueError("SHA-256 collision in fixture byte table")
    return digest


def artifact_bundle(artifact_type):
    if artifact_type in _BUNDLE_CACHE:
        return copy.deepcopy(_BUNDLE_CACHE[artifact_type])
    cache={}
    target=complete_artifact(artifact_type,"TARGET",cache)
    companions=[]
    seen_hashes=set()
    for (typ,key),obj in sorted(cache.items(),key=lambda x:(x[0][0],x[0][1])):
        if typ==artifact_type and key=="TARGET": continue
        if obj["self_hash"] in seen_hashes: continue
        seen_hashes.add(obj["self_hash"])
        companions.append({"artifact_type":typ,"closure_key":key,"self_hash":obj["self_hash"],"canonical_json":cj(obj)})
    bundle = {"contract":"ppc5.fixture_mini_bundle.v9","schema_version":9,
              "lifecycle_state":"PROPOSAL_ONLY","target_artifact_type":artifact_type,
              "target_artifact":target,"target_artifact_self_hash":target["self_hash"],
              "companion_artifacts":companions,"reference_closure_complete":True}
    validate_bundle(bundle)
    _BUNDLE_CACHE[artifact_type]=bundle
    return copy.deepcopy(bundle)


def alternate_value(value):
    if isinstance(value, bool): return not value
    if isinstance(value, int): return value + 1
    if isinstance(value, str):
        if len(value) == 64 and all(c in "0123456789abcdef" for c in value): return ("1" if value[0] != "1" else "2") + value[1:]
        if value == "A": return "B"
        if value == "B": return "A"
        return value + "_MUTATED"
    if isinstance(value, list): return value + [copy.deepcopy(value[-1])] if value else ["MUTATED"]
    if value is None: return "MUTATED"
    if isinstance(value, dict):
        out = copy.deepcopy(value)
        key = sorted(out)[0]
        out[key] = alternate_value(out[key])
        return out
    raise ValueError(type(value))


def schema_at_pointer(artifact_type,pointer):
    node=DEFS[TYPE_TO_DEF[artifact_type]]
    for token in pointer.strip("/").split("/"):
        node=resolve_schema(node)
        if "oneOf" in node and "properties" not in node:
            choices=[x for x in node["oneOf"] if isinstance(x,dict) and ("properties" in x or x.get("type")!="null")]
            node=choices[0]
        if token.isdigit():
            i=int(token)
            node=node["prefixItems"][i] if "prefixItems" in node else node["items"]
        else:
            node=node["properties"][token]
    return resolve_schema(node)


def schema_alternate(value,node,salt="mutation"):
    if "enum" in node:
        alternatives=[x for x in node["enum"] if x!=value]
        if alternatives:
            pick=int(hashlib.sha256(salt.encode()).hexdigest()[:8],16)%len(alternatives)
            return copy.deepcopy(alternatives[pick]),True
        return alternate_value(value),False
    if "const" in node:
        return alternate_value(value),False
    typ=node.get("type")
    if typ=="boolean": return (not value),True
    if typ in ("integer","number"):
        lower=int(node.get("minimum",0)); upper=node.get("maximum")
        delta=1+int(hashlib.sha256(salt.encode()).hexdigest()[:4],16)%7
        candidate=value+delta
        if upper is not None and candidate>upper: candidate=value-delta
        if candidate<lower: candidate=lower if value!=lower else (lower+1 if upper is None or lower+1<=upper else value)
        return candidate, candidate>=lower and (upper is None or candidate<=upper)
    if typ=="string" or isinstance(value,str):
        pattern=node.get("pattern","")
        tag=hashlib.sha256(salt.encode()).hexdigest()[:8]
        if "0-9a-f" in pattern: return hashlib.sha256((value+salt).encode()).hexdigest(),True
        if pattern.startswith("^[a-z]"): return (value+"_"+tag)[:96],True
        if pattern.startswith("^[A-Z]"): return (value+"_MUTATED_"+tag.upper())[:128],True
        if pattern.startswith("^RAW_"): return "RAW_MUTATED",True
        return value+"_MUTATED",True
    # Compound fields are intentionally changed as one logical field. Their
    # schema validity is conservative: a duplicated array is valid only when
    # uniqueItems is not required.
    if isinstance(value,list):
        minimum=node.get("minItems",0)
        if len(value)>minimum:
            return copy.deepcopy(value[:-1]),True
        if node.get("maxItems") is None or len(value)<node["maxItems"]:
            item_schema=node.get("items",{})
            candidate=schema_sample(item_schema,salt=salt+"/array_append")
            if not node.get("uniqueItems") or candidate not in value:
                return copy.deepcopy(value)+[candidate],True
        return alternate_value(value),False
    if isinstance(value,dict): return alternate_value(value),False
    return alternate_value(value),False


def mutation_operation(mutation_id):
    for name in ("WRONG_TARGET","MISSING","OMIT","DUPLICATE","DUP","EXTRA","REORDER","ORDER","SWAP","STALE"):
        if name in mutation_id: return name
    return "REPLACE"


def operation_alternate(value,node,mutation_id):
    op=mutation_operation(mutation_id)
    idx=int(hashlib.sha256(mutation_id.encode()).hexdigest()[:8],16)
    if isinstance(value,list):
        if op=="OMIT" and value:
            return value[:idx%len(value)]+value[idx%len(value)+1:],True
        if op in {"DUP","DUPLICATE"} and value:
            at=idx%len(value); return value[:at+1]+[copy.deepcopy(value[at])]+value[at+1:],True
        if op in {"ORDER","REORDER","SWAP"} and len(value)>1:
            at=idx%(len(value)-1); out=copy.deepcopy(value);out[at],out[at+1]=out[at+1],out[at];return out,True
        if op=="EXTRA":
            item=node.get("items",{}) if isinstance(node,dict) else {}
            if not item and value:
                candidate=copy.deepcopy(value[-1])
                if isinstance(candidate,dict):
                    if "ordinal" in candidate: candidate["ordinal"]=max(x.get("ordinal",0) for x in value)+1
                    elif "row_key" in candidate: candidate["row_key"] += "_EXTRA"
                    elif "type" in candidate: candidate["type"] += "_EXTRA"
            else:
                candidate=schema_sample(item,salt=mutation_id+"/extra")
            return copy.deepcopy(value)+[candidate],True
    return schema_alternate(value,node,mutation_id)


def add_semantic_candidate(bundle,artifact_type):
    bundle["semantic_candidate"]={
        "candidate_shape_id":artifact_type+"_NONAUTHORITATIVE_FIXTURE_CANDIDATE_V1",
        "authoritative_artifact_type":artifact_type,
        "candidate_artifact_canonical_json":cj(bundle["target_artifact"]),
        "authority_conferred":False,
    }


def path_root_reference_candidate():
    inventory=json.loads((ROOT/"object_inventory.json").read_text())
    edges=[]
    for obj in inventory["objects"]:
        for binding in obj.get("reference_bindings",[]):
            edges.append({"source_type":obj["type"],**binding})
    frontier=["PATH_CONSTRUCTION_RECEIPT"]
    seen_types=set(frontier); relation=[]; seen_edges=set()
    while frontier:
        consumer=frontier.pop()
        for edge in edges:
            if edge["consumer_type"]!=consumer: continue
            key=cj(edge)
            if key not in seen_edges:
                seen_edges.add(key);relation.append(edge)
            if edge["source_type"] not in seen_types:
                seen_types.add(edge["source_type"]);frontier.append(edge["source_type"])
    relation.sort(key=lambda row:(row["consumer_type"],row["field_path"],row["source_type"],row["role"]))
    if len(relation)!=53:
        raise ValueError(f"PATH root closure changed: {len(relation)} != 53")
    return {"candidate_kind":"PATH_ROOT_TYPED_REFERENCE_RELATION",
            "root_types":["PATH_CONSTRUCTION_RECEIPT"],
            "edges":[{"ordinal":i,"present":True,"multiplicity":1,**row}
                     for i,row in enumerate(relation)]}


def _catalog_index(path):
    for token in reversed(path.strip("/").split("/")):
        if token.isdigit(): return int(token)
    return 0


def _flat_controller_pointer(index, field):
    controller=json.loads((ROOT/"controller_registry.json").read_text())
    flat=[(ri,xi) for ri,row in enumerate(controller["rows"])
          for xi,_ in enumerate(row["result_transitions"])]
    ri,xi=flat[index%len(flat)]
    return f"/rows/{ri}/result_transitions/{xi}/{field}"


def resolve_mutation_target(role, catalog_target, mutation_id):
    """Map every catalog dimension to an existing concrete artifact pointer.

    The catalog path is never decorative: row/edge/cell/binding ordinals are
    projected into the actual frozen target artifact.
    """
    idx=_catalog_index(catalog_target)
    if role=="MODEL_DISPATCH_BINDING" and catalog_target in DISPATCH_BINDINGS:
        head,*rest=catalog_target.strip("/").split("/")
        types={"model_dispatch_receipt":"MODEL_DISPATCH_RECEIPT","model_view":"MODEL_VIEW",
               "controller_transition_receipt":"CONTROLLER_TRANSITION_RECEIPT",
               "complete_run_manifest":"COMPLETE_RUN_MANIFEST"}
        return types[head],"/"+"/".join(rest)
    controller_field={"CONTROLLER_ROW_PRESENCE":"counter_output","CONTROLLER_ROW_CARDINALITY":"counter_output",
                      "CONTROLLER_SUCCESSOR":"next_phase","QUEUE_EFFECT":"result_specific_queue_effect",
                      "TERMINAL_ERROR_RULE":"counter_output"}
    if role in controller_field and catalog_target.startswith("/controller_registry/"):
        if "REMOVE" in mutation_id or "DUPLICATE" in mutation_id:
            controller=json.loads((ROOT/"controller_registry.json").read_text())
            flat=[(ri,xi) for ri,row in enumerate(controller["rows"])
                  for xi,_ in enumerate(row["result_transitions"])]
            ri,_=flat[idx%len(flat)]
            return "CONTROLLER_REGISTRY",f"/rows/{ri}/result_transitions"
        return "CONTROLLER_REGISTRY",_flat_controller_pointer(idx,controller_field[role])
    if role in {"VISIBILITY_CELL","VISIBILITY_ORDER","VISIBILITY_STAGE","VISIBILITY_ITEM","VISIBILITY_ROLE","FORBIDDEN_INFLUENCE"}:
        vis=json.loads((ROOT/"visibility_registry.json").read_text())
        if role=="VISIBILITY_ROLE": return "VISIBILITY_REGISTRY",f"/allowed_edges/{idx%len(vis['allowed_edges'])}/concrete_role"
        if role=="FORBIDDEN_INFLUENCE":
            denied=[i for i,row in enumerate(vis["cells"]) if row["visibility"]=="FORBIDDEN"]
            return "VISIBILITY_REGISTRY",f"/cells/{denied[idx%len(denied)]}/rationale"
        if role=="VISIBILITY_CELL" and mutation_operation(mutation_id) in {"OMIT","DUP","DUPLICATE","EXTRA"}:
            return "VISIBILITY_REGISTRY","/cells"
        if role=="VISIBILITY_ORDER": return "VISIBILITY_REGISTRY","/cells"
        field={"VISIBILITY_CELL":"rationale","VISIBILITY_STAGE":"stage_ordinal","VISIBILITY_ITEM":"information_ordinal"}[role]
        return "VISIBILITY_REGISTRY",f"/cells/{idx%len(vis['cells'])}/{field}"
    if role=="TYPED_REF_EDGE":
        inv=json.loads((ROOT/"object_inventory.json").read_text())
        flat=[(oi,bi) for oi,obj in enumerate(inv["objects"])
              for bi,_ in enumerate(obj.get("reference_bindings",[]))]
        oi,bi=flat[idx%len(flat)]
        if mutation_operation(mutation_id) in {"OMIT","DUP","DUPLICATE","EXTRA","ORDER","REORDER"}:
            return "OBJECT_INVENTORY_REGISTRY",f"/objects/{oi}/reference_bindings"
        field=("permitted_consumer_stages" if "WRONG_STAGE" in mutation_id else
               "field_path" if "WRONG_FIELD" in mutation_id else
               "role" if "WRONG_ROLE" in mutation_id else "consumer_type")
        return "OBJECT_INVENTORY_REGISTRY",f"/objects/{oi}/reference_bindings/{bi}/{field}"
    if role=="TYPED_REF" and catalog_target.startswith("/path/recursive_ref"):
        field=("present" if "MISSING" in mutation_id else
               "multiplicity" if "EXTRA" in mutation_id else
               "ordinal" if "REORDER" in mutation_id else "consumer_type")
        return "OBJECT_INVENTORY_REGISTRY",f"/edges/{idx%53}/{field}"
    if role=="OBJECT_TYPE":
        inv=json.loads((ROOT/"object_inventory.json").read_text())
        if mutation_operation(mutation_id) in {"OMIT","DUP","DUPLICATE","EXTRA"}:
            return "OBJECT_INVENTORY_REGISTRY","/objects"
        field="schema_ref" if "SCHEMA" in mutation_id else "type"
        return "OBJECT_INVENTORY_REGISTRY",f"/objects/{idx%len(inv['objects'])}/{field}"
    if role=="TYPED_REGISTRY" and catalog_target.startswith("/semantic_registry"):
        reg_type=REGISTRY_KINDS[(idx//6)%len(REGISTRY_KINDS)]
        variant=idx%6
        reg=json.loads((ROOT/EXISTING_ARTIFACT_FILES[reg_type]).read_text())
        pointer=("/run_id" if variant==0 and "run_id" in reg else
                 "/artifact_type" if variant==1 else
                 "/registry_kind" if variant==2 and "registry_kind" in reg else
                 "/rows" if variant in {3,4} and "rows" in reg else "/self_hash")
        return reg_type,pointer
    if role=="TRANSITION_CAUSE":
        rows=json.loads((ROOT/"transition_cause_registry.json").read_text())["rows"]
        return "TRANSITION_CAUSE_REGISTRY",f"/rows/{(idx//3)%len(rows)}/content_sha256"
    if role=="AUTHORITY_EDGE":
        rows=json.loads((ROOT/"authority_registry.json").read_text())["rows"]
        field="row_key" if "ALIAS" in mutation_id else "ordinal"
        return "AUTHORITY_REGISTRY",f"/rows/{idx%len(rows)}/{field}"
    artifact_type,pointer=TARGETS.get(role,("RAW_BYTE_MANIFEST","/raw_sha256"))
    return artifact_type,pointer


def typed_value_name(value):
    if value is None: return "NULL"
    if isinstance(value, bool): return "BOOLEAN"
    if isinstance(value, int): return "INTEGER"
    if isinstance(value, str): return "STRING"
    if isinstance(value, list): return "ARRAY"
    if isinstance(value, dict): return "OBJECT"
    raise ValueError(type(value))


TARGETS = {
    "PARAMETER_AXIS_VALUE": ("PRE_ENTROPY_DESIGN_LOCK", "/parameter_law_canonical_json"),
    "ENTROPY_SLICE_ROLE": ("ENTROPY_ACQUISITION_RECEIPT", "/slice_union_sha256"),
    "ACCEPTANCE_PREDICATE_RESULT": ("ACCEPTANCE_PREDICATE_RESULT", "/predicate_ordinal"),
    "PROPOSAL_BOUNDARY": ("PROPOSAL_TRACE_RECEIPT", "/proposal_ordinal"),
    "COMMON_SEED_ENTRY": ("COMMON_SEED_ENTRY_RECEIPT", "/seed_uint64"),
    "LIFE_IDENTITY": ("LIFE_SAMPLE_RECEIPT", "/sample_ordinal"),
    "POLICY_CAPACITY": ("PRE_ENTROPY_DESIGN_LOCK", "/capacities/calls"),
    "OVERLAP_DIMENSION": ("OVERLAP_CONSTRUCTION_RECEIPT", "/overlap_scope_canonical_json"),
    "TEMPORAL_EDGE": ("PRE_ENTROPY_DESIGN_LOCK", "/run_id"),
    "SAFETY_KEY": ("RESOLVED_D1A_SAFETY_TRIAL_REGISTRY", "/run_id"),
    "SUPPORT_POINT": ("COMPLETE_RUN_CONSTRUCTION_SUPPORT_POINT", "/support_ordinal"),
    "CONTROLLER_ROW_PRESENCE": ("CONTROLLER_REGISTRY", "/rows/0/result_transitions/0/counter_output"),
    "CONTROLLER_ROW_CARDINALITY": ("CONTROLLER_REGISTRY", "/reachable_state_count"),
    "CONTROLLER_SUCCESSOR": ("CONTROLLER_REGISTRY", "/rows/0/result_transitions/0/next_phase"),
    "QUEUE_EFFECT": ("CONTROLLER_REGISTRY", "/rows/0/result_transitions/0/result_specific_queue_effect"),
    "TERMINAL_ERROR_RULE": ("CONTROLLER_REGISTRY", "/rows/0/result_transitions/0/counter_output"),
    "QUEUE_FINALIZATION": ("QUEUE_FINALIZATION_RECEIPT", "/model_dispatch_count"),
    "MISSING_TRANSITION": ("CONTROLLER_TRANSITION_RECEIPT", "/counter_transition/before"),
    "TRANSITION_CAUSE": ("TRANSITION_CAUSE_REGISTRY", "/rows/0/content_sha256"),
    "MODEL_DISPATCH_BINDING": ("MODEL_DISPATCH_RECEIPT", "/call_ordinal"),
    "DREAM_BRANCH": ("OPERATION_RESULT_RECEIPT", "/result"),
    "CONTEXT_CELL": ("DEPENDENCY_DECISION_RECEIPT", "/claim_rendering"),
    "TYPED_REF": ("MODEL_VIEW", "/run_id"),
    "LIFE_MEMBERSHIP": ("LIFE_GATE_AGGREGATE", "/sample_ordinal"),
    "EMISSION_INFLUENCE": ("INTERVENTION_EMISSION_RECEIPT", "/emitted_public_bytes"),
    "DISPATCH_FIELD": ("MODEL_DISPATCH_RECEIPT", "/debit"),
    "PROVIDER_TABLE": ("PROVIDER_AUDIT_RECEIPT", "/provider_call_id"),
    "MOUNT_REF": ("MODEL_DISPATCH_RECEIPT", "/model_ref/self_hash"),
    "DESCRIPTIVE_PROVIDER": ("PROVIDER_AUDIT_RECEIPT", "/run_id"),
    "AUDIT_ROLE": ("PROVIDER_AUDIT_RECEIPT", "/run_id"),
    "TYPED_REGISTRY": ("STATUS_REGISTRY", "/rows/0/content_sha256"),
    "MATCH_DIMENSION": ("D1A_CONTROL_SET_RECEIPT", "/run_id"),
    "MATCH_INPUT": ("D1A_CONTROL_SET_RECEIPT", "/recipient_life_id"),
    "SOURCE_ROLE": ("D1A_CONTROL_SET_RECEIPT", "/sample_ordinal"),
    "DERANGEMENT_PROPERTY": ("D1A_CONTROL_SET_RECEIPT", "/run_id"),
    "MANIFEST_SHAPE": ("D1A_CONTROL_SET_MANIFEST", "/ordered_sample_ordinals"),
    "ANCESTRY": ("D1A_CONTROL_SET_MANIFEST", "/run_id"),
    "DOSE_PROPERTY": ("D1A_CONTROL_SET_RECEIPT", "/sample_ordinal"),
    "D1A_CONTROL_MANIFEST": ("D1A_CONTROL_SET_MANIFEST", "/run_id"),
    "PRIVILEGED_FIELD": ("PRIVILEGED_ROUTE_RECEIPT", "/match_keys_canonical_json"),
    "PATH_ORACLE": ("PATH_CONSTRUCTION_RECEIPT", "/path_suite_sha256"),
    "SOURCE_ID": ("PATH_CONSTRUCTION_RECEIPT", "/sample_ordinal"),
    "CUT_BYTES": ("SANITIZED_RESPONSE_PROJECTION", "/resolved_public_bytes"),
    "TWIN_PROPERTY": ("PATH_CONSTRUCTION_RECEIPT", "/path_suite_sha256"),
    "SHAM_PROPERTY": ("PATH_CONSTRUCTION_RECEIPT", "/path_suite_sha256"),
    "CLOSURE_PROOF": ("COMPLETE_MODEL_VIEW_MANIFEST", "/run_id"),
    "ROUTE_FIELD": ("PRIVILEGED_ROUTE_RECEIPT", "/route_mapping_canonical_json"),
    "OPAQUE_ALLOCATION": ("OPAQUE_LINEAGE_ALLOCATION_RECEIPT", "/opaque_commitment"),
    "EMISSION_FIELD": ("INTERVENTION_EMISSION_RECEIPT", "/emitted_public_bytes"),
    "SCHEDULE_FIELD": ("OPAQUE_LINEAGE_ALLOCATION_RECEIPT", "/run_id"),
    "RAW_RESULT": ("OPERATION_RESULT_RECEIPT", "/result"),
    "PROGRAM_CELL": ("OBSERVATION_RECEIPT", "/key"),
    "ROOT_STATUS": ("OPERATION_RESULT_RECEIPT", "/result"),
    "PIPELINE_STATE": ("COMPLETE_RUN_MANIFEST", "/run_id"),
    "RESOURCE_PROPERTY": ("RESOURCE_ACCOUNTING_RECEIPT", "/event_count"),
    "QUALIFICATION_BYTES": ("RESOURCE_ACCOUNTING_RECEIPT", "/resource_qualification"),
    "LIFE_GATE_AGGREGATE": ("LIFE_GATE_AGGREGATE", "/sample_ordinal"),
    "SAFETY_TEMPLATE": ("RESOLVED_D1A_SAFETY_TRIAL_REGISTRY", "/run_id"),
    "RATIONAL": ("COMPLETE_RUN_CONSTRUCTION_SUPPORT_POINT", "/support_ordinal"),
    "PAIRED_GATE": ("PAIRED_GATE_RESULT", "/run_id"),
    "SAFETY_GATE": ("OBSERVATION_RECEIPT", "/run_id"),
    "MISSINGNESS_GATE": ("ANALYSIS_BUNDLE", "/run_id"),
    "HOLM_FIELD": ("ANALYSIS_BUNDLE", "/holm_family/0"),
    "CLAIM_LITERAL": ("CLAIM_REGISTRY", "/rows/0/content_sha256"),
    "CONSTRUCTION_PROOF": ("CONDITIONAL_COMPLETE_RELEASE_POWER_RESULT", "/run_id"),
    "FORBIDDEN_POWER": ("JOINT_CONSTRUCTION_RELEASE_POWER_RECEIPT", "/run_id"),
    "VISIBILITY_CELL": ("VISIBILITY_REGISTRY", "/cells/0/rationale"),
    "VISIBILITY_ORDER": ("VISIBILITY_REGISTRY", "/cells/0/ordinal"),
    "VISIBILITY_STAGE": ("VISIBILITY_REGISTRY", "/cells/0/stage_ordinal"),
    "VISIBILITY_ITEM": ("VISIBILITY_REGISTRY", "/cells/0/information_ordinal"),
    "VISIBILITY_ROLE": ("VISIBILITY_REGISTRY", "/cells/0/concrete_role"),
    "FORBIDDEN_INFLUENCE": ("VISIBILITY_REGISTRY", "/cells/0/rationale"),
    "TYPED_REF_EDGE": ("OBJECT_INVENTORY_REGISTRY", "/objects/0/schema_ref"),
    "OBJECT_TYPE": ("OBJECT_INVENTORY_REGISTRY", "/objects/0/contract"),
    "DENIAL_BRANCH": ("T13_PREMODEL_TECHNICAL_GATE", "/run_id"),
    "CROSS_CONTRACT_CLOSURE": ("OBJECT_INVENTORY_REGISTRY", "/schema_raw_sha256"),
    "T01_EVIDENCE": ("GENERIC_T01_INTAKE_EVIDENCE", "/change_id"),
    "TEST_RESULT_VECTOR": ("T13_PREMODEL_TECHNICAL_GATE", "/run_id"),
    "TECHNICAL_CLOSURE": ("T13_PREMODEL_TECHNICAL_GATE", "/run_id"),
    "REVIEW_CLOSURE": ("REVIEW_RECEIPT", "/run_id"),
    "FORBIDDEN_INPUT": ("T13_PREMODEL_TECHNICAL_GATE", "/run_id"),
    "AUTHORITY_EDGE": ("AUTHORITY_REGISTRY", "/rows/0/content_sha256"),
    "PREDECESSOR_ROLE": ("COLD_REPLAY_RECEIPT", "/run_id"),
    "DREAM_SLEEP": ("COLD_REPLAY_RECEIPT", "/run_id"),
    "ANALYSIS_CLOSURE": ("COLD_REPLAY_RECEIPT", "/run_id"),
    "CANDIDATE_DECISION": ("CANDIDATE_DECISION_RECEIPT", "/run_id"),
    "RELEASE_FIELD": ("COLD_REPLAY_RECEIPT", "/replay_id"),
    "REPLAY_IDENTITY": ("COLD_REPLAY_RECEIPT", "/replay_id"),
}

TEST_INPUT_ARTIFACT = {
    "PPC5R9_T02":"PRE_ENTROPY_DESIGN_LOCK",
    "PPC5R9_T03":"CONTROLLER_REGISTRY",
    "PPC5R9_T04":"OPERATION_RESULT_RECEIPT",
    "PPC5R9_T05":"PROVIDER_AUDIT_RECEIPT",
    "PPC5R9_T06":"D1A_CONTROL_SET_MANIFEST",
    "PPC5R9_T07":"PATH_CONSTRUCTION_RECEIPT",
    "PPC5R9_T08":"PRIVILEGED_ROUTE_RECEIPT",
    "PPC5R9_T09":"STATUS_REGISTRY",
    "PPC5R9_T10":"COMPLETE_RUN_MANIFEST",
    "PPC5R9_T11":"ANALYSIS_BUNDLE",
    "PPC5R9_T12":"OBJECT_INVENTORY_REGISTRY",
    "PPC5R9_T13":"T13_PREMODEL_TECHNICAL_GATE",
    "PPC5R9_T14":"COLD_REPLAY_RECEIPT",
}


def cj(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"


def h_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def h_file(path: Path) -> str:
    return h_bytes(path.read_bytes())


def av(axis_id: str, ordinal: int, value_id: str, value, value_type: str | None = None) -> dict:
    if value_type is None:
        value_type = ("NULL" if value is None else "BOOLEAN" if isinstance(value, bool)
                      else "INTEGER" if isinstance(value, int) else "ARRAY" if isinstance(value,list)
                      else "OBJECT" if isinstance(value,dict) else "STRING")
    return {"axis_id": axis_id, "value_id": value_id, "value_ordinal": ordinal, "value_type": value_type, "value": value}


def pkey(test_id: str, suite_id: str, axes: list[dict], kind: str = "P") -> str:
    body = {"a": [[x["axis_id"], x["value_ordinal"], x["value_id"]] for x in axes], "k": kind, "s": suite_id, "t": test_id, "v": 1}
    return cj(body)


def nkey(test_id: str, base_key: str, mutation_id: str) -> str:
    return cj({"b": h_bytes(base_key.encode()), "k": "N", "m": mutation_id, "t": test_id, "v": 1})


def semantic_scenario(test_id: str, suite_id: str, axes: list[dict], payload=None) -> dict:
    """Concrete, closed micro-input derived solely from finite axis values.

    Every positive carries observations and an exact result, never merely a
    branch label.  T08 additionally freezes paired causal/noninterference
    worlds so emitted-byte influence is measured rather than asserted.
    """
    facts=[{"name":a["axis_id"],"ordinal":a["value_ordinal"],
            "value_type":a["value_type"],"value":copy.deepcopy(a["value"])}
           for a in axes]
    scenario={"scenario_contract":"ppc5.fixture_semantic_scenario.v9",
              "test_id":test_id,"suite_id":suite_id,
              "law_id":f"{test_id}_{suite_id}_RELATION_V1",
              "input_facts":facts,
              "subject":copy.deepcopy(payload) if payload is not None else
                         {"tokens":[str(a["value"]).split(":") for a in axes]}}
    if test_id=="PPC5R9_T08" and suite_id=="ROUTE":
        target,count=str(axes[0]["value"]).split(":")
        emitted={"ZERO":0,"ONE":1,"MULTI":2}[count]
        scenario["worlds"]=[
            {"world_id":"BEFORE","target_class":target,"emitted_public_records":0},
            {"world_id":"AFTER","target_class":target,"emitted_public_records":emitted},
        ]
    elif test_id=="PPC5R9_T08" and suite_id=="INFLUENCE_RELATION":
        changed=str(axes[0]["value"])
        permitted=changed=="EMITTED_PUBLIC_BYTES"
        scenario["worlds"]=[
            {"world_id":"BEFORE","changed_input":None,"emitted_public_bytes":"PUBLIC_BASE",
             "condition":"C0","source":"S0","match_keys":"K0","provider_scores":"P0","nonce":"N0","mapping":"M0"},
            {"world_id":"AFTER","changed_input":changed,
             "emitted_public_bytes":"PUBLIC_EMITTED" if permitted else "PUBLIC_BASE",
             "condition":"C1" if changed=="condition" else "C0",
             "source":"S1" if changed=="source" else "S0",
             "match_keys":"K1" if changed=="match_keys" else "K0",
             "provider_scores":"P1" if changed=="provider_scores" else "P0",
             "nonce":"N1" if changed=="nonce" else "N0",
             "mapping":"M1" if changed=="mapping" else "M0"},
        ]
    elif test_id=="PPC5R9_T08" and suite_id=="QUEUE_OUTCOME":
        row=axes[0]["value"]; route=row["queue_state"]
        scenario["worlds"]=[{"world_id":"QUEUE_INPUT","route_state":route,
                             "terminal_class":row["terminal_class"],
                             "slot_ids":["SLOT_0","SLOT_1"] if route=="TWO_OUTSTANDING" else ["SLOT_0"]}]
    scenario["input_relation_sha256"]=h_bytes(cj({"facts":facts,"subject":scenario["subject"],
                                                   "worlds":scenario.get("worlds",[])}).encode())
    return scenario


def derive_semantic_result(test_id: str, suite_id: str, axes: list[dict], scenario: dict) -> dict:
    """Reducer law kept outside executor-visible input bytes."""
    if test_id=="PPC5R9_T08" and suite_id=="ROUTE":
        target,count=str(axes[0]["value"]).split(":"); emitted={"ZERO":0,"ONE":1,"MULTI":2}[count]
        if target=="TARGET" and count=="ONE":
            outcome="INTERVENTION"
        elif target=="NON_TARGET" and count=="ZERO":
            outcome="OFF_PATH_AUTHENTIC_PASS_THROUGH"
        else:
            outcome="RUN_INVALID"
        return {"target_class":target,"emitted_public_records":emitted,
                "route_outcome":outcome,
                "public_continuation":outcome!="RUN_INVALID"}
    if test_id=="PPC5R9_T08" and suite_id=="INFLUENCE_RELATION":
        changed=str(axes[0]["value"]); permitted=changed=="EMITTED_PUBLIC_BYTES"
        return {"changed_input":changed,"public_output_changed":permitted,
                "influence_class":"PERMITTED" if permitted else "FORBIDDEN_NONINFLUENCE"}
    if test_id=="PPC5R9_T08" and suite_id=="QUEUE_OUTCOME":
        row=axes[0]["value"]; route=row["queue_state"]
        outcome=("FLUSHED" if route=="QUEUED" and row["terminal_class"]=="VALID" else
                 "DISCARDED" if route=="QUEUED" else
                 "ORDERED_DISCARD" if route=="TWO_OUTSTANDING" else "NONE")
        slots=([{"slot_id":"SLOT_0","effect":"DISCARD","effect_count":1},
                {"slot_id":"SLOT_1","effect":"DISCARD","effect_count":1}]
               if route=="TWO_OUTSTANDING" else
               [{"slot_id":"SLOT_0","effect":outcome,"effect_count":1}])
        return {"route_state":route,"terminal_effect":outcome,
                "slot_effects":slots,
                "queue_exactly_once":all(row["effect_count"]==1 for row in slots)}
    return {"relation_holds":True,"fact_count":len(axes),
            "subject_sha256":h_bytes(cj(scenario["subject"]).encode())}


def base_input(test_id: str, suite_id: str, axes: list[dict], branch_key: str,
               payload=None) -> dict:
    bundle=artifact_bundle(TEST_INPUT_ARTIFACT[test_id])
    bundle["fixture_case"]={"test_id":test_id,"suite_id":suite_id,"branch_key":branch_key,"axis_values":axes,"faults":[]}
    bundle["semantic_scenario"]=semantic_scenario(test_id,suite_id,axes,payload)
    return bundle


def output_bytes(test_id: str, branch_key: str, scenario: dict, derived_result: dict) -> str:
    return cj({"branch_key_sha256": h_bytes(branch_key.encode()), "decision": "PASS",
               "derived_result":derived_result,
               "input_relation_sha256":scenario["input_relation_sha256"],
               "law_id":scenario["law_id"],"test_id":test_id})


def add_positive(test: dict, suite: str, axes: list[dict], applicability: str, payload: dict | None = None) -> dict:
    axes=copy.deepcopy(axes)
    if payload is not None and len(axes)==1:
        axes[0]["value"]=copy.deepcopy(payload)
        axes[0]["value_type"]="OBJECT"
    key = pkey(test["test_id"], suite, axes)
    inp = base_input(test["test_id"], suite, axes, key, payload)
    if payload is not None:
        inp["subject"] = payload
    derived=derive_semantic_result(test["test_id"],suite,axes,inp["semantic_scenario"])
    out=output_bytes(test["test_id"],key,inp["semantic_scenario"],derived)
    row = {
        "ordinal": len(test["positive_cases"]), "branch_key": key,
        "branch_key_sha256": h_bytes(key.encode()), "suite_id": suite,
        "axis_values": axes, "applicability_rule": applicability,
        "input_sha256":intern_canonical_bytes(cj(inp)),
        "expected_output_canonical_json": out,
        "expected_output_sha256": h_bytes(out.encode()),
        "expected_first_failure": None,
        "_input_obj": inp,
    }
    test["positive_cases"].append(row)
    return row


def add_mutation(test: dict, base: dict, mutation_id: str, target: str, role: str,
                 failure: str, before=True, after=False, value_type="BOOLEAN",
                 rehash_roles: list[str] | None = None) -> None:
    artifact_type, actual_target = resolve_mutation_target(role,target,mutation_id)
    role_bases=test.setdefault("_mutation_base_by_artifact",{})
    if artifact_type in role_bases:
        base=test["positive_cases"][role_bases[artifact_type]]
    else:
        candidates=[base]+test["positive_cases"]
        chosen=next((row for row in candidates if row.get("_assigned_mutation_artifact_type") in (None,artifact_type)),None)
        if chosen is None:
            raise ValueError(f"{test['test_id']}: no positive base available for {artifact_type}")
        if chosen.get("_assigned_mutation_artifact_type") is None:
            replacement=artifact_bundle(artifact_type)
            if artifact_type in EXISTING_ARTIFACT_FILES:
                add_semantic_candidate(replacement,artifact_type)
            if test["test_id"]=="PPC5R9_T07" and role=="TYPED_REF":
                replacement["semantic_candidate"]["candidate_shape_id"]="PATH_ROOT_TYPED_REFERENCE_RELATION_V1"
                replacement["semantic_candidate"]["candidate_artifact_canonical_json"]=cj(path_root_reference_candidate())
            old=chosen["_input_obj"]
            replacement["fixture_case"]=copy.deepcopy(old["fixture_case"])
            replacement["semantic_scenario"]=copy.deepcopy(old["semantic_scenario"])
            if "subject" in old: replacement["subject"]=copy.deepcopy(old["subject"])
            chosen["_input_obj"]=replacement
            chosen["input_sha256"]=intern_canonical_bytes(cj(replacement))
            chosen["_assigned_mutation_artifact_type"]=artifact_type
        base=chosen
        role_bases[artifact_type]=test["positive_cases"].index(chosen)
    before_obj=copy.deepcopy(base["_input_obj"])
    candidate_mode="semantic_candidate" in before_obj
    candidate_before=(json.loads(before_obj["semantic_candidate"]["candidate_artifact_canonical_json"])
                      if candidate_mode else before_obj["target_artifact"])
    bundle_target=("/semantic_candidate/candidate_artifact_canonical_json" if candidate_mode
                   else "/target_artifact"+actual_target)
    actual_before=pointer_get(candidate_before,actual_target)
    target_schema=({"type":("boolean" if isinstance(actual_before,bool) else
                            "integer" if isinstance(actual_before,int) else
                            "string" if isinstance(actual_before,str) else
                            "array" if isinstance(actual_before,list) else "object")}
                   if candidate_mode and actual_target.startswith("/edges/")
                   else schema_at_pointer(artifact_type,actual_target))
    actual_after,_=operation_alternate(actual_before,target_schema,mutation_id)
    after_obj = copy.deepcopy(before_obj)
    candidate_after=copy.deepcopy(candidate_before)
    pointer_set(candidate_after,actual_target,actual_after)
    if candidate_mode:
        after_obj["semantic_candidate"]["candidate_artifact_canonical_json"]=cj(candidate_after)
    else:
        pointer_set(after_obj,bundle_target,actual_after)
    if not candidate_mode and actual_target != "/self_hash":
        after_obj["target_artifact"]["self_hash"] = compute_self_hash(after_obj["target_artifact"])
        after_obj["target_artifact_self_hash"] = after_obj["target_artifact"]["self_hash"]
    schema_errors=_schema_errors(after_obj["target_artifact"],DEFS[TYPE_TO_DEF[artifact_type]],"/target_artifact")
    after_schema_valid=not schema_errors
    expected_failure=failure
    if not after_schema_valid:
        expected_failure="FIXTURE_SCHEMA_INVALID"
    elif not candidate_mode and actual_target=="/self_hash":
        expected_failure="SELF_HASH_MISMATCH"
    elif not candidate_mode:
        ref_leaf=actual_target.rsplit("/",1)[-1]
        parent_schema=schema_at_pointer(artifact_type,actual_target.rsplit("/",1)[0]) if "/" in actual_target.strip("/") else {}
        if isinstance(parent_schema,dict) and parent_schema.get("x-artifact-ref"):
            expected_failure={"run_id":"REFERENCE_RUN_MISMATCH","artifact_type":"REFERENCE_TYPE_MISMATCH",
                              "role":"REFERENCE_ROLE_MISMATCH","ordinal":"REFERENCE_ORDINAL_OR_CARDINALITY",
                              "self_hash":"REFERENCE_TARGET_MISSING"}.get(ref_leaf,failure)
    # Assert the intended pre-validator route independently of the encoded
    # expectation. Schema-valid local mutations must preserve full closure;
    # reference and hash mutations intentionally fail that earlier layer.
    if not candidate_mode and expected_failure not in {"FIXTURE_SCHEMA_INVALID","SELF_HASH_MISMATCH","REFERENCE_TARGET_MISSING",
                                "REFERENCE_RUN_MISMATCH","REFERENCE_TYPE_MISMATCH","REFERENCE_ROLE_MISMATCH",
                                "REFERENCE_ORDINAL_OR_CARDINALITY"}:
        try:
            validate_bundle(after_obj)
        except ValueError as exc:
            message=str(exc)
            if "missing reference target" in message:
                expected_failure="REFERENCE_TARGET_MISSING"
            elif "reference run mismatch" in message:
                expected_failure="REFERENCE_RUN_MISMATCH"
            elif "reference type mismatch" in message:
                expected_failure="REFERENCE_TYPE_MISMATCH"
            else:
                raise
    before_bytes = cj(before_obj)
    after_bytes = cj(after_obj)
    key = nkey(test["test_id"], base["branch_key"], mutation_id)
    test["negative_mutations"].append({
        "ordinal": len(test["negative_mutations"]), "mutation_id": mutation_id,
        "branch_key": key, "branch_key_sha256": h_bytes(key.encode()),
        "base_positive_branch_key": base["branch_key"],
        "target_artifact_type": artifact_type,
        "catalog_semantic_dimension_path":target,
        "logical_target_json_pointer": actual_target,
        "carrier_json_pointer": bundle_target, "target_typed_role": role,
        "before_typed_value": {"value_type": typed_value_name(actual_before), "value": actual_before},
        "after_typed_value": {"value_type": typed_value_name(actual_after), "value": actual_after},
        "allowed_transitive_rehash_roles": rehash_roles or ([artifact_type] if actual_target != "/self_hash" else []),
        "before_input_sha256": intern_canonical_bytes(before_bytes),
        "after_input_sha256": intern_canonical_bytes(after_bytes),
        "logical_changed_json_pointers": [actual_target],
        "byte_changed_json_pointers": [bundle_target] + ([] if candidate_mode or actual_target == "/self_hash" else ["/target_artifact/self_hash","/target_artifact_self_hash"]),
        "mutation_operation":mutation_operation(mutation_id),
        "expected_output_canonical_json": None,
        "after_target_schema_valid":after_schema_valid,
        "mutation_validity_class":"SCHEMA_VALID_SEMANTIC_MUTATION" if after_schema_valid else "INTENTIONAL_SCHEMA_INVALID_MUTATION",
        "expected_first_failure": expected_failure,
    })


def add_mutation_group(test: dict, base: dict, prefix: str, count: int, failure: str,
                       target_prefix: str, role: str) -> None:
    for i in range(count):
        add_mutation(test, base, f"{prefix}_{i:04d}", f"{target_prefix}/{i}", role, failure)


def new_test(test_id: str, purpose: str, oracle: str) -> dict:
    return {
        "test_id": test_id, "purpose": purpose,
        "canonical_iteration_order": ["suite_ordinal", "axis_value_ordinals", "branch_kind", "mutation_ordinal"],
        "applicability_is_closed_table": True,
        "independent_oracle_algorithm": oracle,
        "positive_cases": [], "negative_mutations": [], "precedence_probes": [],
    }


def add_precedence(test: dict) -> None:
    failures = PREFIX + LOCAL[test["test_id"]]
    for i, (first, second) in enumerate(zip(failures, failures[1:])):
        axes = [av("EARLIER_FAILURE", i, first, first), av("LATER_FAILURE", i, second, second)]
        key = pkey(test["test_id"], "PRECEDENCE_PROBE", axes, "Q")
        inp = base_input(test["test_id"], "PRECEDENCE_PROBE", axes, key)
        inp["fixture_case"]["faults"] = [first, second]
        test["precedence_probes"].append({
            "ordinal": i, "branch_key": key, "branch_key_sha256": h_bytes(key.encode()),
            "suite_id": "PRECEDENCE_PROBE", "axis_values": axes,
            "input_sha256":intern_canonical_bytes(cj(inp)), "expected_output_canonical_json": None,
            "expected_first_failure": first,
        })


def source_rows():
    return {
        "controller": json.loads((ROOT / "controller_registry.json").read_text()),
        "inventory": json.loads((ROOT / "object_inventory.json").read_text()),
        "visibility": json.loads((ROOT / "visibility_registry.json").read_text()),
        "status": json.loads((ROOT / "status_contract.json").read_text()),
        "causes": json.loads((ROOT / "transition_cause_registry.json").read_text()),
        "claims": json.loads((ROOT / "claim_registry.json").read_text()),
        "resources": json.loads((ROOT / "resource_registry.json").read_text()),
        "authority": json.loads((ROOT / "authority_registry.json").read_text()),
        "dispatch": json.loads((ROOT / "allowed_dispatch_registry.json").read_text()),
    }


def build_tests(src: dict) -> list[dict]:
    tests = []

    # T02: all axes and suite applicability are literal.
    t = new_test("PPC5R9_T02", "generator, temporal ancestry, per-life controls, pointwise construction law", "finite Datalog least fixed point over literal extensional facts")
    params = [("PATH_LENGTH", [2, 3]), ("RECORD_CAPACITY", [0, 1, 2]), ("QUEUE_CAPACITY", [0, 1, 2])]
    for aid, vals in params:
        for i, val in enumerate(vals): add_positive(t, "PARAMETER_VALUE", [av(aid, i, f"{aid}_{val}", val)], "one row for each frozen finite parameter value")
    for i, val in enumerate(["GENERATOR", "RECIPIENT", "DONOR", "COMMON_SEED"]): add_positive(t, "ENTROPY_ROLE", [av("ENTROPY_ROLE", i, val, val)], "one row per disjoint entropy role")
    traces = ["ACCEPT"] + [f"FIRST_FAIL_P{i}" for i in range(5)] + ["EXHAUST_AT_LIMIT"]
    for i, val in enumerate(traces): add_positive(t, "PROPOSAL_TRACE", [av("TRACE_BRANCH", i, val, val)], "one row per accepted, first-failure, or exhaustion branch")
    for i, row in enumerate(src["dispatch"]["rows"]): add_positive(t, "COMMON_SEED_ENTRY", [av("CALL_ROLE_ORDINAL", i, row["row_key"], row["row_key"])], "one row per frozen dispatch seed entry", row)
    for i in range(2): add_positive(t, "LIFE_BUNDLE", [av("SAMPLE_ORDINAL", i, f"SAMPLE_{i}", i)], "two prospectively distinct life samples")
    for s in range(2):
        for k, kind in enumerate(["AUTHENTIC", "WRONG_LIFE", "BINDING_DERANGED"]): add_positive(t, "D1A_CONTROL_ORIGIN", [av("SAMPLE_ORDINAL", s, f"SAMPLE_{s}", s), av("CONTROL_KIND", k, kind, kind)], "every life has all three D1A origins")
    for p, pol in enumerate(["DREAM_TO_SLEEP", "RECENCY_TO_SLEEP", "HASH_PERMUTED_TO_SLEEP"]):
        for c, cap in enumerate(["ZERO", "ONE", "EQUAL_ELIGIBLE", "GREATER_THAN_ELIGIBLE"]): add_positive(t, "POLICY_CAPACITY", [av("ROOT_POLICY", p, pol, pol), av("CAPACITY_CLASS", c, cap, cap)], "complete 3x4 root-policy capacity table")
    for d, dim in enumerate(["ROW_COUNT", "TOKEN_COUNT", "BYTE_CLASS", "UPDATE_COUNT", "SUPPORT_HISTOGRAM"]):
        for r, rel in enumerate(["SAME", "DIFFERENT"]): add_positive(t, "OVERLAP", [av("OVERLAP_DIMENSION", d, dim, dim), av("RELATION", r, rel, rel)], "complete five-dimension same/different table")
    for i, val in enumerate(["SUCCESS", "PREDICATE_FAILURE", "EXHAUSTION"]): add_positive(t, "SUPPORT_POINT", [av("SUPPORT_BRANCH", i, val, val)], "one row per construction support branch")
    add_positive(t, "TEMPORAL_DAG", [av("CHAIN", 0, "DESIGN_ENTROPY_REALIZATION_SAFETY_RESOLUTION_POPULATED_LOCK", "DESIGN_ENTROPY_REALIZATION_SAFETY_RESOLUTION_POPULATED_LOCK")], "the sole permitted temporal chain")
    base = t["positive_cases"][0]
    groups = [
        ("PARAMETER_VALUE_OR_REF",8,"PARAMETER_DECODE","/pre_entropy_design_lock/parameter_law","PARAMETER_AXIS_VALUE"),
        ("ENTROPY_ROLE_TRIPLE",12,"ENTROPY_BINDING","/entropy_acquisition/role","ENTROPY_SLICE_ROLE"),
        ("ACCEPTANCE_PREDICATE_TRIPLE",15,"ACCEPTANCE_FIRST_FAILURE","/acceptance_predicate_result","ACCEPTANCE_PREDICATE_RESULT"),
        ("PROPOSAL_BOUNDARY",4,"PROPOSAL_ORDER","/proposal_trace/boundary","PROPOSAL_BOUNDARY"),
        ("SEED_BINDING_SEPTUPLE",56,"SEED_PREIMAGE","/common_seed_entry","COMMON_SEED_ENTRY"),
        ("LIFE_IDENTITY",10,"RECIPIENT_DONOR_IDENTITY","/life_sample/identity","LIFE_IDENTITY"),
        ("POLICY_CAPACITY",12,"NOMINEE_CAPACITY_ORDER","/root_policy/capacity","POLICY_CAPACITY"),
        ("OVERLAP_DERIVATION",25,"OVERLAP_DERIVATION","/overlap_construction","OVERLAP_DIMENSION"),
        ("TEMPORAL_EDGE",9,"DESIGN_LOCK_ANCESTRY","/temporal_dag/edge","TEMPORAL_EDGE"),
        ("SAFETY_REGISTRY",4,"D1A_CONTROL_MANIFEST","/resolved_safety_registry","SAFETY_KEY"),
        ("POINTWISE_SUPPORT",13,"POINTWISE_SUPPORT_POWER","/joint_power/support_point","SUPPORT_POINT"),
    ]
    for args in groups: add_mutation_group(t, base, args[0], args[1], args[2], args[3], args[4])
    add_precedence(t); tests.append(t)

    # T03.
    t = new_test("PPC5R9_T03", "total controller, error count three, queue finalization, causes, dispatch closure", "bounded SAT relation over literal state/result tuples")
    transition_cases=[]
    for ri,row in enumerate(src["controller"]["rows"]):
        for xi,tr in enumerate(row["result_transitions"]):
            transition_cases.append(add_positive(t,"REACHABLE_TRANSITION",[av("REACHABLE_STATE_KEY",ri,row["row_key"],row["row_key"]),av("RESULT_TRANSITION",xi,f"{tr['accepted_result']}_{tr['counter_input']}",f"{tr['accepted_result']}:{tr['counter_input']}")],"every registered reachable state/result transition",tr))
    queue_rows=[]
    terminal_tuples=sorted({(tr["terminal_reason"],tr["queue_input_class"],tr["result_specific_queue_effect"],tr["normalized_result"]) for row in src["controller"]["rows"] for tr in row["result_transitions"] if tr["terminal_intent"]})
    for i,(reason,qclass,effect,normalized) in enumerate(terminal_tuples):
        queue_rows.append(add_positive(t,"TERMINAL_QUEUE_FINALIZATION",[av("TERMINAL_TUPLE",i,f"{reason}:{qclass}:{effect}:{normalized}",f"{reason}:{qclass}:{effect}:{normalized}")],"every distinct registered terminal-reason/queue-input/effect/result tuple"))
    terminal_classes=sorted({tr["normalized_result"] for row in src["controller"]["rows"] for tr in row["result_transitions"] if tr["terminal_intent"]})
    for i,val in enumerate(terminal_classes): add_positive(t,"TERMINAL_REPLAY",[av("TERMINAL_CLASS",i,val,val)],"each terminal normalized-result class exactly once")
    for i,row in enumerate(src["causes"]["rows"]): add_positive(t,"TRANSITION_CAUSE",[av("CAUSE_KIND",i,row["cause"],row["cause"])],"all seven typed transition causes",row)
    for i,val in enumerate(src["controller"]["rows"][0]["first_failure_order"]): add_positive(t,"FIRST_FAILURE",[av("DISPATCH_FAILURE",i,val,val)],"all thirteen controller failures in frozen order")
    for i,b in enumerate(transition_cases):
        for j,(lab,path,role) in enumerate([("REMOVE","/present","CONTROLLER_ROW_PRESENCE"),("DUPLICATE","/multiplicity","CONTROLLER_ROW_CARDINALITY"),("WRONG_SUCCESSOR","/next_phase","CONTROLLER_SUCCESSOR"),("WRONG_EFFECT","/result_specific_queue_effect","QUEUE_EFFECT")]): add_mutation(t,b,f"TRANSITION_{i:03d}_{lab}",f"/controller_registry/rows/{i}{path}",role,"UNIQUE_CONTROLLER_ROW")
    eq2=[b for b in transition_cases if b["_input_obj"]["subject"].get("accepted_result")=="ERROR" and b["_input_obj"]["subject"].get("counter_input")==2]
    for i,b in enumerate(eq2):
        for lab,path in [("COUNT_NOT_THREE","/counter_output"),("QUEUES_WORK","/result_specific_queue_effect"),("TERMINALS_WITH_OUTSTANDING","/terminal_intent")]: add_mutation(t,b,f"EQ2_{i:02d}_{lab}",f"/controller_registry/error_eq2/{i}{path}","TERMINAL_ERROR_RULE","QUEUE_FINALIZATION")
    for i,b in enumerate(queue_rows):
        for lab in ["MISSING","DUPLICATE","WRONG_ORDER","UNCOVERED","REJECTED_EFFECT","ILLEGAL_EFFECT"]: add_mutation(t,b,f"QUEUE_{i:02d}_{lab}",f"/queue_finalization/{i}/{lab.lower()}","QUEUE_FINALIZATION","QUEUE_FINALIZATION")
    add_mutation_group(t,t["positive_cases"][0],"PHYSICAL_MISSING",60,"MISSING_CALL","/controller/missing_transition","MISSING_TRANSITION")
    add_mutation_group(t,t["positive_cases"][0],"CAUSE_ROLE_TYPE_CARDINALITY",21,"TRANSITION_CAUSE","/transition_cause_registry/rows","TRANSITION_CAUSE")
    for i,path in enumerate(DISPATCH_BINDINGS): add_mutation(t,t["positive_cases"][0],f"DISPATCH_BINDING_{i:02d}",path,"MODEL_DISPATCH_BINDING","DISPATCH_CLOSURE")
    add_precedence(t); tests.append(t)

    # Compact builder for T04--T14: positives remain semantic and literal;
    # all mutation dimensions are materialized below with exact counts.
    def semantic_test(test_id,purpose,oracle,suites,mutation_groups):
        tt=new_test(test_id,purpose,oracle)
        for suite,axis_id,values,rule in suites:
            for i,val in enumerate(values):
                payload=val if isinstance(val,dict) else None
                vid=val.get("row_key",val.get("type",f"ROW_{i}")) if isinstance(val,dict) else str(val)
                add_positive(tt,suite,[av(axis_id,i,vid,vid)],rule,payload)
        bb=tt["positive_cases"][0]
        for prefix,count,failure,target,role in mutation_groups: add_mutation_group(tt,bb,prefix,count,failure,target,role)
        add_precedence(tt); tests.append(tt); return tt

    dream_branches=["RAW_OK","RAW_EMPTY","RAW_MISSING","PARSE_INVALID","DUPLICATE_ID","UNKNOWN_ID","ORDER_INVALID","FOCUS_INVALID","CAPACITY_OVERFLOW","RENDER_MISMATCH"]
    context_cells=[f"{s}:{p}" for s in ["INSTALLED","EMPTY_PUBLICATION","ABSTAINED","INVALID","MISSING_NO_RETRY"] for p in ["AUTHENTIC_DREAM_CONTEXT","RECENCY_CONTEXT","PERMUTED_CONTEXT"]]
    t4=semantic_test("PPC5R9_T04","DREAM reduction/install, dependency, emission, dispatch, life membership","literal 5x3 truth table plus independent parser DFA",[
        ("DREAM_REDUCER","DREAM_BRANCH",dream_branches,"each raw/parser/id/order/focus/cardinality/render/missing branch"),
        ("CONTEXT_STATUS","CONTEXT_CELL",context_cells,"complete 5x3 context table"),
        ("TYPED_DEPENDENCY","CONTEXT_POLICY",["AUTHENTIC_DREAM_CONTEXT","RECENCY_CONTEXT","PERMUTED_CONTEXT"],"three exact context dependencies"),
        ("LIFE_AGGREGATE_MEMBERSHIP","MEMBERSHIP_CELL",["ONE_BOTH","ONE_MISSING","TWO_BOTH","TWO_MISSING"],"closed lower-unit/presence table"),
        ("EMISSION_METAMORPHIC","CHANGE_KIND",["EMITTED_PUBLIC_BYTES"]+PRIVILEGED_FIELDS,"one public influence and six privileged noninfluences"),
        ("MODEL_DISPATCH_CHAIN","CHAIN",["VALID_TYPED_SEED_LIFE_VIEW_CLOSURE"],"one valid chain"),
    ],[("DREAM_BRANCH",10,"DREAM_PARSE","/dream_reducer","DREAM_BRANCH"),("CONTEXT_CELL",45,"CONTEXT_DEPENDENCY","/context_status","CONTEXT_CELL"),("TYPED_CONTEXT_REF",12,"CONTEXT_DEPENDENCY","/context_refs","TYPED_REF"),("LIFE_MEMBERSHIP",7,"LIFE_MEMBERSHIP","/life_aggregate/membership","LIFE_MEMBERSHIP"),("EMISSION_INFLUENCE",7,"EMISSION_CAPABILITY","/emission/influence","EMISSION_INFLUENCE"),("RAW_RENDER_DEBIT_STATUS",5,"DREAM_RENDER_OR_DEBIT","/dream_dispatch","DISPATCH_FIELD"),("DISPATCH_BINDING",23,"DISPATCH_BINDING","/dispatch","MODEL_DISPATCH_BINDING")])

    provider_rows=["EMPTY_TABLE","SINGLETON","STRICT_WIN","EXACT_QUANTIZED_TIE","HALF_EVEN_POS_EVEN","HALF_EVEN_POS_ODD","HALF_EVEN_NEG_EVEN","HALF_EVEN_NEG_ODD","PROVIDER_MISSING"]
    descriptive=[f"{a}:{r}" for a in ["RAW_RAG","FULL_CONTEXT","EXPLICIT_GRAPH"] for r in ["FOUND","NOT_FOUND","PROVIDER_MISSING"]]+["FULL_CONTEXT_PREASSIGNMENT_RENDER_OVERFLOW"]
    t5=semantic_test("PPC5R9_T05","provider numerics, audit, descriptive isolation, thirteen registries","integer IEEE-754 decoder plus direct registry schema parser",[
        ("CAUSAL_NUMERIC","NUMERIC_CASE",provider_rows,"nine frozen numerical micros"),("CAUSAL_MOUNT","MOUNT_CLASS",["NULL_MOUNT","VALID_MOUNT"],"two mount classes"),("DESCRIPTIVE_PROVIDER","PROVIDER_CELL",descriptive,"ten descriptive provider rows"),("TYPED_REGISTRY","REGISTRY_KIND",REGISTRY_KINDS,"all thirteen typed registries")
    ],[("NUMERIC_TABLE",12,"SEMANTIC_TABLE","/provider/table","PROVIDER_TABLE"),("MOUNT",4,"TYPED_REGISTRY","/provider/mount","MOUNT_REF"),("DESCRIPTIVE_CAUSAL_FIELD",3,"DESCRIPTIVE_ISOLATION","/descriptive_provider","DESCRIPTIVE_PROVIDER"),("PROVIDER_AUDIT",2,"PROVIDER_AUDIT","/provider_audit","AUDIT_ROLE"),("REGISTRY_SEXTUPLE",78,"TYPED_REGISTRY","/semantic_registry","TYPED_REGISTRY")])

    taint=[f"{f}:{stage}" for f in PRIVILEGED_FIELDS for stage in ["WRITER","TRAINER"]]
    t6=semantic_test("PPC5R9_T06","per-life D1A controls, manifest, ancestry, non-taint","independent multiset joins and bipartite derangement",[
        ("PER_LIFE_CONTROL","CONTROL",[f"S{s}:{k}" for s in [0,1] for k in ["AUTHENTIC","WRONG_LIFE","BINDING_DERANGED"]],"six per-life control rows"),("MANIFEST_CLOSURE","CLOSURE",["TWO_LIVES_EQUAL_MEMBERSHIP"],"one manifest closure"),("ALLOWED_PROJECTION","STAGE",["PROVIDER","WRITER","TRAINER"],"three allowed projections"),("POINTWISE_POWER_BINDING","BINDING",["EXACT_CONTROL_MANIFEST"],"one power binding"),("PRE_ENTROPY_ANCESTRY","CHAIN",["VALID"],"one ancestry chain")
    ],[("WRONG_LIFE_DIMENSION",16,"WRONG_LIFE_MATCH","/d1a/wrong_life","MATCH_DIMENSION"),("FORBIDDEN_MATCH_INPUT",5,"WRONG_LIFE_MATCH","/d1a/forbidden_match","MATCH_INPUT"),("STERILE_SOURCE",7,"ORIGIN_ELIGIBILITY","/d1a/source","SOURCE_ROLE"),("DERANGEMENT_PRESERVATION",9,"DERANGEMENT","/d1a/derangement","DERANGEMENT_PROPERTY"),("PER_LIFE_MANIFEST",8,"LIFE_MEMBERSHIP_EQUALITY","/d1a/manifest/life","LIFE_MEMBERSHIP"),("MANIFEST_SHAPE",4,"CONTROL_MANIFEST_CARDINALITY","/d1a/manifest","MANIFEST_SHAPE"),("DESCENDANT_BACKREF",3,"DESIGN_ANCESTRY","/d1a/origin","ANCESTRY"),("DOSE_MISMATCH",4,"DOSE_OPPORTUNITY","/d1a/dose","DOSE_PROPERTY"),("POINTWISE_BINDING",1,"POINTWISE_POWER_BINDING","/joint_power/control_manifest_ref","D1A_CONTROL_MANIFEST"),("TEMPORAL",3,"DESIGN_ANCESTRY","/temporal","TEMPORAL_EDGE"),("PRIVILEGED_TAINT",len(taint),"ARM_NEUTRAL_PROJECTION","/taint","PRIVILEGED_FIELD")])

    proper=["L2_MASK_01","L2_MASK_10"]+[f"L3_MASK_{m:03b}" for m in range(1,7)]
    edge_art=[f"{e}:{k}" for e in ["p20","p21","p30","p31","p32"] for k in ["SOURCE","CUT","TWIN","SHAM","TWIN_PARITY","SHAM_PARITY"]]
    t7=semantic_test("PPC5R9_T07","finite paths, oracle, interventions, recursive references, visibility closure","adjacency-matrix powers and exhaustive bitmask truth tables",[
        ("FULL_PATH","L",["L2","L3"],"both selected full paths"),("PROPER_SUBSET","MASK",proper,"all eight nonempty proper masks"),("ALTERNATE_PATH","L",["L2_ALT","L3_ALT"],"both alternate paths"),("EDGE_ARTIFACT","EDGE_ARTIFACT",edge_art,"five selected edges by six artifacts"),("CLOSURE","CLOSURE_KIND",["ROUTE_PROVIDER_AUDIT_SPLIT","MODEL_VIEW_REPLAY_RETENTION","CONCRETE_VISIBILITY_ROLE","INVENTORY_EDGE_EQUALITY"],"four closure proofs")
    ],[("ORACLE_FLIP",12,"SUBSET_ORACLE","/path/oracle","PATH_ORACLE"),("SOURCE_ID_PREIMAGE",10,"SOURCE_DISJOINTNESS","/path/source","SOURCE_ID"),("CUT_BYTES",5,"CUT","/path/cut","CUT_BYTES"),("TWIN",15,"TWIN","/path/twin","TWIN_PROPERTY"),("SHAM",20,"SHAM","/path/sham","SHAM_PROPERTY"),("SOURCE_COLLISION",1,"SOURCE_DISJOINTNESS","/path/source_collision","SOURCE_ID"),("CLOSURE",4,"VISIBILITY_EDGE_EQUALITY","/path/closure","CLOSURE_PROOF"),
       # The 53-edge PATH_CONSTRUCTION_RECEIPT predecessor closure is a
       # frozen ordered relation.  Each operation addresses exactly one
       # edge and exactly one scalar fixture-candidate field; no role falls
       # through to a generic artifact pointer.
       ("REF_MISSING",53,"RECURSIVE_REFERENCE_CLOSURE","/path/recursive_ref","TYPED_REF"),
       ("REF_EXTRA",53,"RECURSIVE_REFERENCE_CLOSURE","/path/recursive_ref","TYPED_REF"),
       ("REF_REORDER",53,"RECURSIVE_REFERENCE_CLOSURE","/path/recursive_ref","TYPED_REF"),
       ("REF_WRONG_TARGET",53,"RECURSIVE_REFERENCE_CLOSURE","/path/recursive_ref","TYPED_REF")])

    route=["TARGET:ZERO","TARGET:ONE","TARGET:MULTI","NON_TARGET:ZERO"]
    t8=semantic_test("PPC5R9_T08","D1B route, emission causality, opacity, queue exact-once","four-row route table plus typed dependency reachability",[
        ("ROUTE","ROUTE_CELL",route,"four coherent route rows"),("INFLUENCE_RELATION","CHANGED_INPUT",["EMITTED_PUBLIC_BYTES"]+PRIVILEGED_FIELDS,"one permitted and six forbidden influences"),("QUEUE_OUTCOME","QUEUE_CELL",[
            {"row_key":"QUEUED_VALID","queue_state":"QUEUED","terminal_class":"VALID"},
            {"row_key":"QUEUED_INVALID","queue_state":"QUEUED","terminal_class":"INVALID"},
            {"row_key":"REJECTED","queue_state":"REJECTED","terminal_class":"REJECTED"},
            {"row_key":"TWO_OUTSTANDING_INVALID","queue_state":"TWO_OUTSTANDING","terminal_class":"INVALID"}],"four exact queue inputs with reducer-derived outcomes"),("OPAQUE_ALLOCATION","ALLOCATION",["FRESH_32_BYTE_DOMAIN_SEPARATED_SHA256"],"one allocation law"),("AUDIT_SPLIT","AUDIT_KIND",["ROUTE_LINEAGE","PROVIDER"],"two separate audits"),("DISPATCH_CLOSURE","CHAIN",["VALID"],"one dispatch chain")
    ],[("ROUTE",6,"ROUTE_TARGET_MATCH","/route","ROUTE_FIELD"),("FORBIDDEN_PROJECTION_FIELD",6,"RESTRICTED_PROJECTION","/projection","PRIVILEGED_FIELD"),("NONCE_COMMITMENT",5,"ASSIGNMENT_AND_NONCE","/allocation","OPAQUE_ALLOCATION"),("EMISSION",4,"EMISSION_EQUALITY","/emission","EMISSION_FIELD"),("AUDIT",6,"AUDIT_COMPLETENESS","/audit","AUDIT_ROLE"),("QUEUE",8,"QUEUE_EXCLUSIVITY","/queue","QUEUE_EFFECT"),("SCHEDULE",6,"SCHEDULE_COMMITMENT","/schedule","SCHEDULE_FIELD"),("DISPATCH_VIEW_BINDING",23,"DISPATCH_CLOSURE","/dispatch","MODEL_DISPATCH_BINDING")])

    raw=[]
    for rule in src["status"]["rules"]:
        raw.extend([f"{rule['rule_id']}:{x}" for x in rule["raw_results"]])
    program=[f"{s}:{p}:R{r}:{term}" for s in ["INSTALLED","EMPTY_PUBLICATION","ABSTAINED","INVALID","MISSING_NO_RETRY"] for p in ["AUTHENTIC_DREAM_CONTEXT","RECENCY_CONTEXT","PERMUTED_CONTEXT"] for r in ["ZERO","POSITIVE"] for term in ["ACTION","NO_ACTION"]]
    precedence=[f"{a}>{b}" for i,a in enumerate(src["status"]["precedence"]) for b in src["status"]["precedence"][i+1:]]
    t9=semantic_test("PPC5R9_T09","DREAM/context/status totality and endpoint-local missing dominance","closed 60-cell matrix plus all fifteen precedence comparisons",[
        ("DREAM_CONTEXT_PROGRAM","PROGRAM_CELL",program,"complete 5x3x2x2 program"),("STATUS_RULE","RAW_RESULT",raw,"all forty-three raw status inputs"),("STATUS_PRECEDENCE","STATUS_PAIR",precedence,"all fifteen unordered precedence pairs")
    ],[("STATUS_RAW_RESULT",43,"ASSIGNED_POLICY_STATUS","/status/raw_result","RAW_RESULT"),("PROGRAM_CELL",60,"CONTEXT_POLICY_PROPAGATION","/status/program_cell","PROGRAM_CELL"),("DISPATCH_BINDING",23,"DISPATCH_ANCESTRY","/dispatch","MODEL_DISPATCH_BINDING"),("DEPENDENCY_REF",12,"CONTEXT_POLICY_PROPAGATION","/context_dependency","TYPED_REF")])

    pipeline=[f"{root}:{stage}" for root in ["DREAM_TO_SLEEP","RECENCY_TO_SLEEP","HASH_PERMUTED_TO_SLEEP"] for stage in ["ROOT","WRITER","CORPUS","TRAINER","VALIDATION","PUBLICATION","PROVIDER","BEHAVIOR"]]
    root_status=[f"DREAM_TO_SLEEP:{s}" for s in ["INSTALLED","EMPTY_PUBLICATION","ABSTAINED","INVALID","MISSING_NO_RETRY"]]+[f"{r}:{s}" for r in ["RECENCY_TO_SLEEP","HASH_PERMUTED_TO_SLEEP"] for s in ["INSTALLED","EMPTY_PUBLICATION","ABSTAINED","INVALID"]]
    t10=semantic_test("PPC5R9_T10","D1D total pipeline and descriptive resource conservation","acyclic relational stage join plus integer resource conservation",[
        ("ROOT_STATUS","ROOT_STATUS",root_status,"thirteen applicable root/status rows"),("REACHABLE_D1D_PIPELINE","PIPELINE_STATE",pipeline,"twenty-four root-stage states"),("DISPATCH_CHAIN","ROOT_POLICY",["DREAM_TO_SLEEP","RECENCY_TO_SLEEP","HASH_PERMUTED_TO_SLEEP"],"three root dispatch chains"),("RESOURCE","RESOURCE_PROPERTY",["INCLUSIVE","MARGINAL","PHYSICAL_TOTAL","PERMUTATION_INVARIANCE","COMPONENTWISE_CONSERVATION"],"five resource properties"),("D1D_QUALIFICATION","RENDER",["EXACT_LITERAL_PLUS_ADJACENT_RESOURCE_SENTENCE_PLUS_FIXED_QUALIFICATION"],"one inseparable rendering")
    ],[("PIPELINE_ADJUSTMENT",24,"BEHAVIOR_CONTINUATION","/d1d/pipeline","PIPELINE_STATE"),("DISPATCH_BINDING",23,"DISPATCH_BINDING","/dispatch","MODEL_DISPATCH_BINDING"),("PRIVILEGED_INFLUENCE",6,"WRITER_SANITIZATION","/d1d/privileged","PRIVILEGED_FIELD"),("RESOURCE",6,"RESOURCE_CONSERVATION","/resource","RESOURCE_PROPERTY"),("ROOT_STATUS",13,"ROOT_STATUS","/d1d/root_status","ROOT_STATUS"),("QUALIFICATION",9,"QUALIFICATION_ADJACENCY","/claim/resource_qualification","QUALIFICATION_BYTES")])

    holm=[]
    import itertools
    for p in itertools.permutations(["D1A","D1B","D1C","D1D"]): holm.append(">".join(p))
    t11=semantic_test("PPC5R9_T11","life aggregates, exact inference/Holm, claims, pointwise power","integer binomial/rational arithmetic and direct pointwise dot product",[
        ("LIFE_GATE_AGGREGATE","AGGREGATE_CELL",[f"{n}:{s}" for n in [1,2] for s in ["COMPLETE","TREATMENT_MISSING","CONTROL_MISSING","INTEGRITY_CLEAN_NO_ACTION"]],"eight lower-unit/arm-state rows"),("PAIRED_BOUNDARY","DIFF",["BELOW_MARGIN","EQUAL_MARGIN","ABOVE_MARGIN","REQUIRED_ARM_MISSING"],"four paired boundaries"),("SAFETY","SAFETY_CELL",[f"{e}:{x}" for e in ["FALSE_SELECTION","NOT_FOUND"] for x in ["NO_EVENT","EVENT","MISSING_PROVIDER"]],"six safety cells"),("MISSINGNESS","COUNT_CLASS",["ZERO","INTERIOR_OR_EQUAL_CEILING","N"],"three missingness cases"),("CP_BRACKET","CP_CELL",[f"{d}:{c}" for d in ["LOWER","UPPER"] for c in ["ZERO","INTERIOR","N"]],"six CP brackets"),("IUT_CRITICAL_COUNT","IUT_CELL",[f"{g}:{c}" for g in ["PAIRED","SAFETY","MISSINGNESS"] for c in ["BELOW","AT","ABOVE"]],"nine critical-count cases"),("HOLM_PERMUTATION","ORDER",holm,"all 24 strict orders"),("HOLM_TIE","TIE",["FOUR_WAY_EXACT_TIE"],"one tie"),("HOLM_STOP","STOP",["0","1","2","3","NONE"],"five stop positions"),("CLAIM_BYTES","CLAIM_ID",[r["row_key"] for r in src["claims"]["rows"]],"five exact claim literals"),("CONSTRUCTION_PROOF","PROOF",["FINITE_SUPPORT","CONSERVATIVE_PARTITION"],"two construction proofs"),("POWER","POWER_CASE",["UNION_BOUND_POSITIVE","UNION_BOUND_FLOOR_ZERO","POINTWISE_ALL_SUCCESS","POINTWISE_MIXED_FAILURE","POINTWISE_UNCOVERED_ZERO","GLOBAL_PRODUCT_SUBSTITUTION_REJECTED"],"six power cases"),("SAFETY_TEMPLATE_RESOLUTION","RESOLUTION",["EXACT_TWO_LIFE_ONE_TO_ONE"],"one template resolution")
    ],[("AGGREGATE",9,"MEMBERSHIP_AND_AGGREGATE","/life_gate_aggregate","LIFE_GATE_AGGREGATE"),("SAFETY_TEMPLATE",5,"SAFETY_TEMPLATE","/safety_template","SAFETY_TEMPLATE"),("POINTWISE_SUPPORT",13,"POINTWISE_JOINT_POWER","/joint_power/support","SUPPORT_POINT"),("RATIONAL",6,"CANONICAL_RATIONAL","/analysis/rational","RATIONAL"),("PAIRED",4,"STRICT_DIRECTION","/paired_gate","PAIRED_GATE"),("SAFETY",4,"MISSING_DOMINANCE","/safety_gate","SAFETY_GATE"),("MISSINGNESS",3,"MISSINGNESS","/missingness_gate","MISSINGNESS_GATE"),("HOLM",8,"HOLM_FAMILY","/holm","HOLM_FIELD"),("CLAIM_LITERAL",10,"CLAIM_LITERAL","/claim_registry","CLAIM_LITERAL"),("CONSTRUCTION_PROOF",4,"CONDITIONAL_POWER","/construction_proof","CONSTRUCTION_PROOF"),("GLOBAL_POWER",1,"POINTWISE_JOINT_POWER","/joint_power/global_product","FORBIDDEN_POWER")])

    vis=src["visibility"]["cells"]
    edges=[]
    for obj in src["inventory"]["objects"]:
        for b in obj.get("reference_bindings",[]): edges.append({"source_type":obj["type"],**b})
    objs=src["inventory"]["objects"]
    t12=new_test("PPC5R9_T12","195 visibility cells, recursive schema/inventory edges, registries, causes, preflight denials","three independent event-walker/relational-parser/role-resolver algorithms")
    for i,row in enumerate(vis): add_positive(t12,"VISIBILITY_CELL",[av("VISIBILITY_CELL",i,f"{row['information_item']}:{row['consumer_stage']}",f"{row['information_item']}:{row['consumer_stage']}")],"literal 13x15 information-item-major product",row)
    for i,row in enumerate(edges): add_positive(t12,"TYPED_SCHEMA_EDGE",[av("EDGE_KEY",i,f"E{i:03d}",f"{row['source_type']}:{row['field_path']}:{row['consumer_type']}")],f"every one of {len(edges)} recursively resolved typed reference edges",row)
    for i,row in enumerate(objs): add_positive(t12,"OBJECT_TYPE",[av("OBJECT_TYPE",i,row["type"],row["type"])],f"all {len(objs)} top-level artifact types",row)
    for i,val in enumerate(REGISTRY_KINDS): add_positive(t12,"TYPED_REGISTRY",[av("REGISTRY_KIND",i,val,val)],"all thirteen semantic registries")
    for i,row in enumerate(src["causes"]["rows"]): add_positive(t12,"TRANSITION_CAUSE",[av("CAUSE_KIND",i,row["cause"],row["cause"])],"all seven causes",row)
    denials=["MISSING_AUTHORITY","STALE_AUTHORITY","WRONG_RUN","WRONG_TYPE","WRONG_ROLE","WRONG_ORDER","WRONG_CARDINALITY","UNALLOWED_DISPATCH"]
    for i,val in enumerate(denials): add_positive(t12,"PREFLIGHT_DENIAL",[av("DENIAL_BRANCH",i,val,val)],"eight no-process preflight denials")
    add_positive(t12,"THREE_WAY_EQUALITY",[av("PROOF",0,"SCHEMA_EQUALS_INVENTORY_EQUALS_ALLOWED_VISIBILITY_EDGES","SCHEMA_EQUALS_INVENTORY_EQUALS_ALLOWED_VISIBILITY_EDGES")],"one exact three-way set equality")
    base=t12["positive_cases"][0]
    add_mutation_group(t12,base,"VISIBILITY_OMIT",195,"VISIBILITY_PRODUCT_SHAPE","/visibility/cell","VISIBILITY_CELL")
    add_mutation_group(t12,base,"VISIBILITY_DUP",195,"VISIBILITY_PRODUCT_SHAPE","/visibility/cell","VISIBILITY_CELL")
    add_mutation_group(t12,base,"VISIBILITY_ADJACENT_SWAP",194,"VISIBILITY_PRODUCT_SHAPE","/visibility/order","VISIBILITY_ORDER")
    add_mutation_group(t12,base,"VISIBILITY_STALE_STAGE",15,"VISIBILITY_CELL_VALUE","/visibility/stage","VISIBILITY_STAGE")
    add_mutation_group(t12,base,"VISIBILITY_STALE_ITEM",13,"VISIBILITY_CELL_VALUE","/visibility/item","VISIBILITY_ITEM")
    add_mutation_group(t12,base,"VISIBILITY_WRONG_ALLOWED_ROLE",84,"CONCRETE_CAPABILITY_ROLE","/visibility/concrete_role","VISIBILITY_ROLE")
    add_mutation_group(t12,base,"VISIBILITY_FORBIDDEN_INFLUENCE",111,"FORBIDDEN_TAINT","/visibility/forbidden","FORBIDDEN_INFLUENCE")
    add_mutation_group(t12,base,"VISIBILITY_EXTRA",1,"VISIBILITY_PRODUCT_SHAPE","/visibility/extra","VISIBILITY_CELL")
    for prefix in ["EDGE_OMIT","EDGE_WRONG_STAGE","EDGE_WRONG_FIELD","EDGE_WRONG_ROLE","EDGE_STALE","EDGE_DUP","EDGE_ORDER"]: add_mutation_group(t12,base,prefix,len(edges),"SCHEMA_REF_RECURSION","/typed_edge","TYPED_REF_EDGE")
    for prefix in ["OBJECT_OMIT","OBJECT_DUP","OBJECT_WRONG_SCHEMA","OBJECT_STALE"]: add_mutation_group(t12,base,prefix,len(objs),"OBJECT_INVENTORY_EDGE","/object_inventory","OBJECT_TYPE")
    add_mutation_group(t12,base,"REGISTRY_SEXTUPLE",78,"TYPED_REGISTRY","/registry","TYPED_REGISTRY")
    add_mutation_group(t12,base,"CAUSE_TRIPLE",21,"TRANSITION_CAUSE","/cause","TRANSITION_CAUSE")
    add_mutation_group(t12,base,"PREFLIGHT_DENIAL",8,"PREFLIGHT_DENIAL","/preflight","DENIAL_BRANCH")
    add_mutation_group(t12,base,"CROSS_CONTRACT",7,"THREE_WAY_EDGE_EQUALITY","/cross_contract","CROSS_CONTRACT_CLOSURE")
    add_precedence(t12); tests.append(t12)

    # Authority is the exact current registry relation, not a legacy
    # hand-written edge-label shorthand.  Each row freezes identity,
    # ordinal, role/cardinality, consumer stages, and content hash.
    topology=src["authority"]["rows"]
    assert [row["ordinal"] for row in topology]==list(range(14))
    assert [row["row_key"] for row in topology]==src["authority"]["ordered_row_keys"]
    t13=semantic_test("PPC5R9_T13","last technical result before human ratification and PRE_MODEL authority","Kahn topological sort plus independently extracted T02-T12 vector",[
        ("FULL_TECHNICAL_PASS","PACKAGE",["VALID_PREMODEL_TECHNICAL_PACKAGE"],"one valid package"),("PREFLIGHT_DENIAL","DENIAL",denials,"eight no-process denials"),("AUTHORITY_TOPOLOGY_STAGE","AUTHORITY_STAGE",topology,"all exact 14 authority stages in registry order")
    ],[("NARROW_T01",7,"NARROW_T01","/generic_intake","T01_EVIDENCE"),("T02_T12_VECTOR",65,"TEST_RESULT_ORDER","/technical_package/test_results","TEST_RESULT_VECTOR"),("REGISTRY_SEXTUPLE",78,"TYPED_REGISTRIES","/technical_package/registries","TYPED_REGISTRY"),("TEMPORAL_DESIGN_EDGE",12,"DESIGN_TEMPORAL_DAG","/temporal/edge","TEMPORAL_EDGE"),("CLOSURE",12,"LIFE_CONTROL_CLOSURE","/technical_package/closure","TECHNICAL_CLOSURE"),("SEAL_REVIEW",8,"FRESH_REVIEW","/technical_package/review","REVIEW_CLOSURE"),("FORBIDDEN_FUTURE_INPUT",2,"FORBIDDEN_FUTURE_INPUT","/technical_package/future_input","FORBIDDEN_INPUT"),("AUTHORITY_ALIAS",14,"AUTHORITY_TOPOLOGY","/authority/stage","AUTHORITY_EDGE"),("AUTHORITY_BACKEDGE",14,"AUTHORITY_TOPOLOGY","/authority/stage","AUTHORITY_EDGE"),("DENIAL",8,"PREFLIGHT_NO_PROCESS","/preflight","DENIAL_BRANCH")])

    predecessor_roles=[f"PPC5R9_T{i:02d}_RESULT" for i in range(2,14)]+["PRE_ENTROPY_DESIGN_LOCK","ENTROPY_ACQUISITION","POPULATED_RUN_LOCK","STATIC_SEAL_PAIR","REVIEW_RECEIPT","ADVOCATE_RECEIPT","COMPLETE_RUN_MANIFEST","ANALYSIS_BUNDLE","D1A_CONTROL_SET_MANIFEST","COMPLETE_MODEL_VIEW_MANIFEST","ROUTE_LINEAGE_AUDIT","PROVIDER_AUDIT"]
    assert len(predecessor_roles)==24
    t14=semantic_test("PPC5R9_T14","two predecessor-only cold replays and one non-releasing final result","relational reconstruction plus independent identity-only reducer",[
        ("FULL_PREDECESSOR_REPLAY","FIXTURE",["ONE_FROZEN_MINI_RUN_CONTAINING_ALL_REQUIRED_BRANCHES"],"one complete predecessor-only mini-run")
    ],[("PREDECESSOR_ROLE_QUINTUPLE",120,"T02_T13_PREDECESSORS","/cold_replay/predecessor","PREDECESSOR_ROLE"),("CAUSE_TRIPLE",21,"TRANSITION_AND_QUEUE_REPLAY","/cold_replay/cause","TRANSITION_CAUSE"),("QUEUE",6,"TRANSITION_AND_QUEUE_REPLAY","/cold_replay/queue","QUEUE_EFFECT"),("AUDIT",6,"AUDIT_SPLIT","/cold_replay/audit","AUDIT_ROLE"),("INFLUENCE",7,"EMISSION_NONINTERFERENCE","/cold_replay/influence","INFLUENCE"),("DISPATCH_BINDING",23,"SEED_VIEW_DISPATCH_CLOSURE","/cold_replay/dispatch","MODEL_DISPATCH_BINDING"),("DREAM_SLEEP",5,"DREAM_SLEEP","/cold_replay/dream_sleep","DREAM_SLEEP"),("LIFE_ANALYSIS",8,"LIFE_OBSERVATION_GATE","/cold_replay/life_analysis","ANALYSIS_CLOSURE"),("CANDIDATE",15,"CANDIDATE_DECISIONS","/cold_replay/candidate","CANDIDATE_DECISION"),("QUALIFICATION",9,"QUALIFICATION_AND_FORBIDDEN_CLAIMS","/cold_replay/qualification","QUALIFICATION_BYTES"),("RELEASE_FORBIDDEN",4,"RELEASE_BYTES_FORBIDDEN","/cold_replay/release","RELEASE_FIELD"),("INDEPENDENCE",5,"REPLAY_INDEPENDENCE","/cold_replay/independence","REPLAY_IDENTITY")])

    # Literal expected counts. Any drift is an authoring error.
    expected={
        "PPC5R9_T02":(61,168,19), "PPC5R9_T03":(346,1469,25),
        "PPC5R9_T04":(40,109,18), "PPC5R9_T05":(34,99,17),
        "PPC5R9_T06":(12,72,17), "PPC5R9_T07":(46,279,22),
        "PPC5R9_T08":(19,64,19), "PPC5R9_T09":(118,138,17),
        "PPC5R9_T10":(46,81,22), "PPC5R9_T11":(80,67,22),
        "PPC5R9_T12":(671,3799,23), "PPC5R9_T13":(23,220,24),
        "PPC5R9_T14":(1,229,25),
    }
    for tt in tests:
        p,n,q=expected[tt["test_id"]]
        got=(len(tt["positive_cases"]),len(tt["negative_mutations"]),len(tt["precedence_probes"]))
        if got!=(p,n,q): raise AssertionError((tt["test_id"],got,(p,n,q)))
        for i,row in enumerate(tt["positive_cases"]): row["case_ordinal"]=i
        for i,row in enumerate(tt["negative_mutations"],p): row["case_ordinal"]=i
        for i,row in enumerate(tt["precedence_probes"],p+n): row["case_ordinal"]=i
        suite_order=[]
        for row in tt["positive_cases"]:
            if row["suite_id"] not in suite_order: suite_order.append(row["suite_id"])
        tt["suite_applicability_tables"]=[]
        for suite_ordinal,suite_id in enumerate(suite_order):
            rows=[r for r in tt["positive_cases"] if r["suite_id"]==suite_id]
            applicability=[{
                "row_ordinal":i,
                "axis_value_coordinates":[[v["axis_id"],v["value_ordinal"],v["value_id"]]
                                          for v in r["axis_values"]],
            } for i,r in enumerate(rows)]
            tt["suite_applicability_tables"].append({
                "suite_id":suite_id,"suite_ordinal":suite_ordinal,
                "positive_expected_result_law":"PASS_WITH_BRANCH_KEY_SHA256_AND_DERIVED_RELATION_V1",
                "row_count":len(rows),"rows":applicability,
                "ordered_rows_sha256":h_bytes(cj(applicability).encode())})
        positive_by_key={r["branch_key"]:r for r in tt["positive_cases"]}
        tt["mutation_applicability_table"]=[]
        for r in tt["negative_mutations"]:
            base=positive_by_key[r["base_positive_branch_key"]]
            tt["mutation_applicability_table"].append({
                "mutation_ordinal":r["ordinal"],"mutation_id":r["mutation_id"],
                "base_suite_id":base["suite_id"],
                "base_axis_value_coordinates":[[v["axis_id"],v["value_ordinal"],v["value_id"]]
                                               for v in base["axis_values"]],
                "carrier_json_pointer":r["carrier_json_pointer"],
                "logical_target_json_pointer":r["logical_target_json_pointer"],
                "target_typed_role":r["target_typed_role"],
                "before_input_sha256":r["before_input_sha256"],"after_input_sha256":r["after_input_sha256"],
                "expected_first_failure":r["expected_first_failure"]})
        tt["mutation_applicability_table_sha256"]=h_bytes(cj(tt["mutation_applicability_table"]).encode())
        tt["first_failure_order"]=PREFIX+LOCAL[tt["test_id"]]
        tt["counts"]={"P_positive":p,"N_one_field_mutations":n,"Q_precedence_probes":q,"logical_expected_count":p+n+q,"independent_executions_per_logical_case":2,"total_planned_executions":2*(p+n+q)}
        ordered=[]
        for group in [tt["positive_cases"],tt["negative_mutations"],tt["precedence_probes"]]:
            ordered.extend({"branch_key":r["branch_key"],"expected_output_canonical_json":r.get("expected_output_canonical_json"),"expected_first_failure":r["expected_first_failure"]} for r in group)
        tt["ordered_expected_vector_sha256"]=h_bytes(cj(ordered).encode())
        tt["branch_key_set_sha256"]=h_bytes(cj(sorted(r["branch_key"] for group in [tt["positive_cases"],tt["negative_mutations"],tt["precedence_probes"]] for r in group)).encode())
    return tests


def main():
    src=source_rows()
    tests=build_tests(src)
    source_files=["author_fixture_universe.py","expected_fixture_enumerator.py","materialized_fixture_extractor.py","independent_fixture_oracle.py","fixture_payload.txt"]
    # Content-address actual artifact inputs so every before/after byte string
    # is present exactly once rather than repeated thousands of times.
    artifact_byte_tables={}
    for test in tests:
        artifact_byte_table={}
        for row in test["positive_cases"]+test["precedence_probes"]:
            digest=row["input_sha256"]
            data=_BYTE_TABLE[digest]
            artifact_byte_table.setdefault(digest,data)
        for row in test["precedence_probes"]:
            row["faults"]=[row["expected_first_failure"],test["first_failure_order"][row["ordinal"]+1]]
        for row in test["negative_mutations"]:
            for side in ["before","after"]:
                digest=row[f"{side}_input_sha256"]
                data=_BYTE_TABLE[digest]
                artifact_byte_table.setdefault(digest,data)
        test["artifact_byte_table"]=[{"sha256":digest,"canonical_json":artifact_byte_table[digest]}
                                     for digest in sorted(artifact_byte_table)]
        test["artifact_byte_table_sha256"]=h_bytes(cj(test["artifact_byte_table"]).encode())
        artifact_byte_tables[test["test_id"]]=artifact_byte_table

    manifest_dir=HERE/"source_manifests"
    manifest_dir.mkdir(exist_ok=True)
    source_roles={
        "author_fixture_universe.py":"RAW_FIXTURE_GENERATOR_SOURCE",
        "expected_fixture_enumerator.py":"RAW_INDEPENDENT_EXPECTED_ENUMERATOR",
        "materialized_fixture_extractor.py":"RAW_INDEPENDENT_EXECUTED_SET_EXTRACTOR",
        "independent_fixture_oracle.py":"RAW_INDEPENDENT_FIXTURE_SET_ORACLE",
        "fixture_payload.txt":"RAW_FIXTURE_PAYLOAD",
    }
    manifests={}
    for name in source_files:
        path=HERE/name
        media_type="text/x-python" if path.suffix==".py" else "text/plain"
        obj={"contract":"ppc5.raw_byte_manifest.v9","schema_version":9,"artifact_type":"RAW_BYTE_MANIFEST","lifecycle_state":"PROPOSAL_ONLY","producer_role":"RAW_MANIFEST_BUILDER","raw_role":source_roles[name],"media_type":media_type,"relative_path":str(path.relative_to(ROOT.parents[2])),"byte_length":path.stat().st_size,"raw_sha256":h_file(path),"self_hash":"0"*64}
        obj["self_hash"]=compute_self_hash(obj)
        out=manifest_dir/(name+".manifest.json")
        out.write_text(cj(obj)); manifests[name]=obj

    spec_dir=HERE/"generator_specs"
    spec_dir.mkdir(exist_ok=True)
    spec_index=[]
    for test in tests:
        finite_axes=[]
        axis_seen={}
        # The finite axis universe is obtained from the authored positive
        # cases, while suite applicability stores coordinates only.  This
        # keeps the normative enumerator honest: it must resolve every
        # applicability coordinate through finite_axes and cannot copy a
        # materialized expected row.
        for row in test["positive_cases"]:
            for value in row["axis_values"]:
                axis_seen.setdefault(value["axis_id"],{})[(value["value_ordinal"],value["value_id"])]=value
        for ordinal,axis_id in enumerate(sorted(axis_seen)):
            vals=sorted(axis_seen[axis_id].values(),key=lambda x:(x["value_ordinal"],x["value_id"]))
            finite_axes.append({"axis_id":axis_id,"ordinal":ordinal,"finite_values":[cj(v) for v in vals]})
        expected=[]
        for row in test["positive_cases"]:
            expected.append({k:row[k] for k in ["branch_key","branch_key_sha256","ordinal","case_ordinal","suite_id","axis_values","applicability_rule","input_sha256","expected_output_canonical_json","expected_output_sha256","expected_first_failure"]})
        precedence=[]
        for row in test["precedence_probes"]:
            precedence.append({**row,"branch_key_sha256":row["branch_key_sha256"],"case_ordinal":row["case_ordinal"],"expected_output_sha256":None,"applicability_rule":"adjacent pair in the exact frozen first-failure order"})
        def ref(name,role):
            return {"artifact_type":"RAW_BYTE_MANIFEST","ordinal":0,"role":role,"self_hash":manifests[name]["self_hash"]}
        spec={
            "contract":"ppc5.fixture_generator_spec.v9","schema_version":9,"artifact_type":"FIXTURE_GENERATOR_SPEC","lifecycle_state":"PROPOSAL_ONLY","producer_role":"FIXTURE_SPEC_AUTHOR","architecture_id":ARCH,"test_id":test["test_id"],
            "generator_id":test["test_id"]+"_FROZEN_GENERATOR","generator_version":1,
            "generator_source_ref":ref("author_fixture_universe.py","RAW_FIXTURE_GENERATOR_SOURCE"),
            "expected_enumerator_ref":ref("expected_fixture_enumerator.py","RAW_INDEPENDENT_EXPECTED_ENUMERATOR"),
            "executed_set_extractor_ref":ref("materialized_fixture_extractor.py","RAW_INDEPENDENT_EXECUTED_SET_EXTRACTOR"),
            "independent_oracle_ref":ref("independent_fixture_oracle.py","RAW_INDEPENDENT_FIXTURE_SET_ORACLE"),
            "canonical_iteration_order":test["canonical_iteration_order"],"finite_axes":finite_axes,
            "suite_applicability_tables":test["suite_applicability_tables"],
            "applicability_and_exclusion_rules":["Only literal suite_applicability_tables rows are applicable.","Suites are a disjoint union and are never cross-multiplied.","No post-ratification code may define axes, rows, mutations, expected bytes, or failures."],
            "expected_positive_count":test["counts"]["P_positive"],
            "one_field_mutation_dimensions":sorted({r["target_typed_role"] for r in test["negative_mutations"]}),
            "expected_mutation_count":test["counts"]["N_one_field_mutations"],
            "expected_precedence_probe_count":test["counts"]["Q_precedence_probes"],
            "logical_expected_count":test["counts"]["logical_expected_count"],
            "total_planned_executions":test["counts"]["total_planned_executions"],
            "branch_key_encoding":"UTF8_CANONICAL_JSON_TYPED_AXIS_BRANCH_KEY_V1",
            "expected_branches":expected,"negative_mutations":test["negative_mutations"],"precedence_probes":precedence,
            "artifact_byte_table":test["artifact_byte_table"],"artifact_byte_table_sha256":test["artifact_byte_table_sha256"],
            "mutation_applicability_table":test["mutation_applicability_table"],"mutation_applicability_table_sha256":test["mutation_applicability_table_sha256"],
            "first_failure_order":test["first_failure_order"],"branch_key_set_sha256":test["branch_key_set_sha256"],"ordered_expected_vector_sha256":test["ordered_expected_vector_sha256"],
            "independent_oracle_algorithm":test["independent_oracle_algorithm"],
            "must_be_frozen_before_architecture_ratification":True,"post_ratification_code_may_define_normative_bytes":False,"self_hash":"0"*64,
        }
        spec["self_hash"]=compute_self_hash(spec)
        path=spec_dir/(test["test_id"]+".fixture_generator_spec.json")
        path.write_text(cj(spec))
        spec_index.append({"test_id":test["test_id"],"relative_path":str(path.relative_to(ROOT)),"self_hash":spec["self_hash"],"file_sha256":h_file(path),"counts":test["counts"],"branch_key_set_sha256":test["branch_key_set_sha256"],"ordered_expected_vector_sha256":test["ordered_expected_vector_sha256"]})

    artifact={
        "contract":"ppc5.fixture_universe.materialized.v9","schema_version":9,
        "artifact_type":"MATERIALIZED_FIXTURE_UNIVERSE","lifecycle_state":PROPOSAL,
        "producer_role":"FIXTURE_SPEC_AUTHOR","architecture_id":ARCH,
        "normative_status":"MUST_FREEZE_BEFORE_ARCHITECTURE_RATIFICATION",
        "forbidden_operations":["FIXTURE_EXECUTION","MODEL","TOKENIZER","EMBEDDING","TRAINER","CANARY","CPU_BEHAVIORAL","GPU","SCIENTIFIC_CLAIM","RELEASE"],
        "branch_key_encoding":"UTF8(canonical_json({a:[[axis_id,value_ordinal,value_id],...],k:'P|Q',s:suite_id,t:test_id,v:1})+LF); negatives use UTF8(canonical_json({b:SHA256(positive_branch_key_bytes),k:'N',m:mutation_id,t:test_id,v:1})+LF)",
        "canonical_json":"UTF-8 NFC strings, sorted object keys, compact separators, arrays in contract order, one trailing LF",
        "source_file_sha256":{name:h_file(HERE/name) for name in source_files},
        "bound_input_sha256":{name:h_file(ROOT/name) for name in ["contracts.schema.json","object_inventory.json","controller_registry.json","transition_cause_registry.json","visibility_registry.json","status_contract.json","claim_registry.json","resource_registry.json","authority_registry.json","allowed_dispatch_registry.json"]},
        "closed_constants":{"information_items":13,"stages":15,"visibility_cells":195,"visible_or_derived_cells":84,"forbidden_cells":111,"typed_reference_edges":len([binding for obj in src["inventory"]["objects"] for binding in obj.get("reference_bindings",[])]),"path_root_typed_reference_edges":53,"top_level_artifact_types":len(src["inventory"]["objects"]),"transition_causes":7,"controller_phase_rules":33,"controller_explicit_tuples":306,"controller_terminal_tuples":13,"controller_terminal_classes":7,"status_rules":10,"status_raw_results":43,"dream_statuses":5,"context_policies":3,"root_policies":3,"typed_semantic_registries":13,"Holm_claim_ids":4,"candidate_decision_literals":5,"path_lengths":[2,3],"dispatch_binding_fields":23,"privileged_fields":6,"preflight_denial_branches":8,"authority_stages":14,"T14_predecessor_roles":24},
        "fixture_spec_index":spec_index,
    }
    summary=[]
    for t in tests:
        summary.append({"test_id":t["test_id"],**t["counts"],"branch_key_set_sha256":t["branch_key_set_sha256"],"ordered_expected_vector_sha256":t["ordered_expected_vector_sha256"]})
    artifact["count_summary"]=summary
    artifact["total_counts"]={
        "P_positive":sum(x["P_positive"] for x in summary),
        "N_one_field_mutations":sum(x["N_one_field_mutations"] for x in summary),
        "Q_precedence_probes":sum(x["Q_precedence_probes"] for x in summary),
        "logical_expected_count":sum(x["logical_expected_count"] for x in summary),
        "total_planned_executions":sum(x["total_planned_executions"] for x in summary),
    }
    all_keys=[r["branch_key"] for t in tests for group in [t["positive_cases"],t["negative_mutations"],t["precedence_probes"]] for r in group]
    artifact["global_branch_key_set_sha256"]=h_bytes(cj(sorted(all_keys)).encode())
    artifact["global_ordered_branch_key_vector_sha256"]=h_bytes(cj(all_keys).encode())
    pre=cj(artifact).encode(); artifact["content_sha256_excluding_content_sha256"]=h_bytes(pre)
    OUT.write_text(cj(artifact))


if __name__=="__main__": main()
