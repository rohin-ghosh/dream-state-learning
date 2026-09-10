"""Hash-bound intake gate for changes to the research architecture.

The gate makes architecture deliberation durable and auditable.  It checks
schemas, identifiers, byte bindings, visibility coverage, and legal state
transitions.  It deliberately does *not* decide whether a proposal is good.
An adjudicator recommendation terminates at ``human_required``; only a separate
human-authored, evidence-bound ratification can release its declared scope.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from .io import atomic_write_json, load_json, sha256_file, utc_now


SCHEMA_DIR = Path(__file__).parent / "schemas"
SCHEMAS = {
    "architecture_change": SCHEMA_DIR / "architecture_change.schema.json",
    "architecture_interpretation": SCHEMA_DIR / "architecture_interpretation.schema.json",
    "architecture_critique": SCHEMA_DIR / "architecture_critique.schema.json",
    "architecture_consensus": SCHEMA_DIR / "architecture_consensus.schema.json",
    "architecture_human_ratification": SCHEMA_DIR / "architecture_human_ratification.schema.json",
}

SCOPE_PROPOSAL_FIELDS = {
    "schema_version",
    "change_id",
    "state",
    "human_ratification_required",
    "requested_scope",
    "forbidden_scope",
    "authorization_effect",
}


class IntakeError(RuntimeError):
    """A structural, provenance, or state-transition failure."""


def _typename(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    if isinstance(value, str):
        return "string"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    return type(value).__name__


def _resolve_ref(ref: str, root_schema: dict[str, Any]) -> dict[str, Any]:
    if not ref.startswith("#/"):
        raise IntakeError(f"unsupported schema reference: {ref}")
    node: Any = root_schema
    for raw in ref[2:].split("/"):
        key = raw.replace("~1", "/").replace("~0", "~")
        if not isinstance(node, dict) or key not in node:
            raise IntakeError(f"broken schema reference: {ref}")
        node = node[key]
    if not isinstance(node, dict):
        raise IntakeError(f"schema reference is not an object: {ref}")
    return node


def _validate_schema(
    value: Any,
    schema: dict[str, Any],
    root_schema: dict[str, Any],
    path: str = "$",
) -> list[str]:
    """Small strict Draft-2020 subset used by the four local schemas."""
    if "$ref" in schema:
        return _validate_schema(value, _resolve_ref(schema["$ref"], root_schema), root_schema, path)
    errors: list[str] = []
    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: expected constant {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: {value!r} is not one of {schema['enum']!r}")

    expected = schema.get("type")
    actual = _typename(value)
    if expected is not None:
        matches = actual == expected or (expected == "number" and actual in {"integer", "number"})
        if not matches:
            return [f"{path}: expected {expected}, got {actual}"]

    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            errors.append(f"{path}: string is shorter than {schema['minLength']}")
        if "pattern" in schema and re.fullmatch(schema["pattern"], value) is None:
            errors.append(f"{path}: does not match {schema['pattern']!r}")

    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            errors.append(f"{path}: needs at least {schema['minItems']} items")
        if schema.get("uniqueItems"):
            rendered = [json.dumps(item, sort_keys=True, separators=(",", ":")) for item in value]
            if len(rendered) != len(set(rendered)):
                errors.append(f"{path}: items must be unique")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                errors.extend(_validate_schema(item, item_schema, root_schema, f"{path}[{index}]"))

    if isinstance(value, dict):
        properties = schema.get("properties", {})
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{path}: missing required property {key!r}")
        if schema.get("additionalProperties") is False:
            for key in value:
                if key not in properties:
                    errors.append(f"{path}: additional property {key!r} is forbidden")
        for key, child in value.items():
            child_schema = properties.get(key)
            if isinstance(child_schema, dict):
                errors.extend(_validate_schema(child, child_schema, root_schema, f"{path}.{key}"))
    return errors


def _load_artifact(path: Path, artifact_type: str) -> dict[str, Any]:
    try:
        value = load_json(path)
    except BaseException as exc:
        raise IntakeError(f"cannot load {path}: {type(exc).__name__}: {exc}") from exc
    if not isinstance(value, dict):
        raise IntakeError(f"{path}: artifact must be a JSON object")
    schema = load_json(SCHEMAS[artifact_type])
    errors = _validate_schema(value, schema, schema)
    if errors:
        raise IntakeError("schema validation failed:\n- " + "\n- ".join(errors))
    return value


def _root_path(root: Path, relative: str) -> Path:
    if Path(relative).is_absolute():
        raise IntakeError(f"content path must be root-relative: {relative}")
    root = root.resolve()
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise IntakeError(f"content path escapes root: {relative}") from exc
    return candidate


def _verify_context_files(root: Path, artifact: dict[str, Any]) -> None:
    seen: set[str] = set()
    for entry in artifact.get("context_files", []):
        relative = entry["path"]
        if relative in seen:
            raise IntakeError(f"duplicate context file path: {relative}")
        seen.add(relative)
        path = _root_path(root, relative)
        if not path.is_file():
            raise IntakeError(f"context file is missing: {relative}")
        actual = sha256_file(path)
        if actual != entry["sha256"]:
            raise IntakeError(
                f"context hash mismatch for {relative}: expected {entry['sha256']}, got {actual}"
            )


def _canonical_scope_proposal_path(root: Path, change_id: str) -> Path:
    return _root_path(
        root, f"research_loop/changes/{change_id}/scope_proposal.json"
    )


def _validated_scope_proposal(root: Path, change_id: str) -> dict[str, Any] | None:
    """Return the canonical declared scope when this change has one.

    Legacy and external temporary intakes have no canonical proposal and retain
    their existing ratification behavior. A canonical proposal is a strict
    authority contract, not advisory metadata.
    """
    path = _canonical_scope_proposal_path(root, change_id)
    if not path.is_file():
        return None
    try:
        proposal = load_json(path)
    except BaseException as exc:
        raise IntakeError(
            f"cannot load canonical scope proposal for {change_id}: "
            f"{type(exc).__name__}: {exc}"
        ) from exc
    if not isinstance(proposal, dict):
        raise IntakeError("canonical scope proposal must be a JSON object")
    if set(proposal) != SCOPE_PROPOSAL_FIELDS:
        raise IntakeError(
            "canonical scope proposal keys mismatch: "
            f"expected={sorted(SCOPE_PROPOSAL_FIELDS)}, actual={sorted(proposal)}"
        )
    if type(proposal["schema_version"]) is not int or proposal["schema_version"] != 1:
        raise IntakeError("canonical scope proposal schema_version must be integer 1")
    if type(proposal["change_id"]) is not str or proposal["change_id"] != change_id:
        raise IntakeError("canonical scope proposal change_id does not match intake")
    if proposal["state"] != "proposal_only":
        raise IntakeError("canonical scope proposal state must be proposal_only")
    if proposal["human_ratification_required"] is not True:
        raise IntakeError("canonical scope proposal must require human ratification")
    if (
        type(proposal["authorization_effect"]) is not str
        or not proposal["authorization_effect"]
    ):
        raise IntakeError("canonical scope proposal authorization_effect must be non-empty text")
    for field, require_nonempty in (("requested_scope", True), ("forbidden_scope", False)):
        values = proposal[field]
        if not isinstance(values, list) or (require_nonempty and not values):
            raise IntakeError(f"canonical scope proposal {field} has invalid cardinality")
        if any(type(value) is not str or not value for value in values):
            raise IntakeError(f"canonical scope proposal {field} must contain non-empty strings")
        if len(values) != len(set(values)):
            raise IntakeError(f"canonical scope proposal {field} contains duplicates")
        if values != sorted(values):
            raise IntakeError(f"canonical scope proposal {field} must use deterministic sorted order")
    if set(proposal["requested_scope"]) & set(proposal["forbidden_scope"]):
        raise IntakeError("canonical scope proposal requested_scope overlaps forbidden_scope")
    return proposal


def _validate_scope_proposal_binding(
    root: Path, change_id: str, ratification: dict[str, Any]
) -> None:
    proposal = _validated_scope_proposal(root, change_id)
    if proposal is None:
        return
    if ratification["authorized_scope"] != proposal["requested_scope"]:
        raise IntakeError(
            "human ratification authorized_scope must exactly match canonical "
            "scope proposal requested_scope"
        )
    if ratification["forbidden_scope"] != proposal["forbidden_scope"]:
        raise IntakeError(
            "human ratification forbidden_scope must exactly match canonical "
            "scope proposal forbidden_scope"
        )


def _unique(items: list[dict[str, Any]], key: str, label: str) -> set[str]:
    values = [item[key] for item in items]
    if len(values) != len(set(values)):
        raise IntakeError(f"duplicate {label}: {values}")
    return set(values)


def validate_change(root: Path, path: Path) -> dict[str, Any]:
    change = _load_artifact(path, "architecture_change")
    _verify_context_files(root, change)
    graph = change["graph_delta"]
    if not graph["nodes"] and not graph["edges"]:
        raise IntakeError("graph_delta must change at least one node or edge")
    _unique(graph["nodes"], "node_id", "graph node id")
    _unique(graph["edges"], "edge_id", "graph edge id")
    _unique(change["loop_delta"]["loops"], "loop_id", "loop id")
    _unique(change["claim_delta"]["claims"], "claim_id", "claim id")
    test_ids = _unique(change["acceptance_tests"], "test_id", "acceptance test id")
    if not test_ids:
        raise IntakeError("at least one acceptance test is required")

    matrix = change["visibility_matrix"]
    expected = {
        (information_id, stage_id)
        for information_id in matrix["information_items"]
        for stage_id in matrix["stages"]
    }
    actual_list = [(cell["information_id"], cell["stage_id"]) for cell in matrix["cells"]]
    actual = set(actual_list)
    if len(actual_list) != len(actual):
        raise IntakeError("visibility_matrix has duplicate information/stage cells")
    unknown = actual - expected
    missing = expected - actual
    if unknown or missing:
        raise IntakeError(
            f"visibility_matrix must cover the exact cartesian product; "
            f"unknown={sorted(unknown)}, missing={sorted(missing)}"
        )
    return change


def validate_interpretation(
    root: Path,
    path: Path,
    change_path: Path,
) -> dict[str, Any]:
    change = validate_change(root, change_path)
    interpretation = _load_artifact(path, "architecture_interpretation")
    _verify_context_files(root, interpretation)
    if interpretation["change_id"] != change["change_id"]:
        raise IntakeError("interpretation change_id does not match proposal")
    mutable_state = (
        f"research_loop/changes/{interpretation['change_id']}/intake.state.json"
    )
    if any(entry["path"] == mutable_state for entry in interpretation["context_files"]):
        raise IntakeError("interpretation context may not include its mutable intake state")
    expected_hash = sha256_file(change_path)
    if interpretation["architecture_change_sha256"] != expected_hash:
        raise IntakeError("interpretation is not bound to the proposal bytes")
    expected_tests = {test["test_id"] for test in change["acceptance_tests"]}
    addressed = set(interpretation["acceptance_test_ids_addressed"])
    if addressed != expected_tests:
        raise IntakeError(
            f"interpretation must address every and only proposed acceptance test; "
            f"expected={sorted(expected_tests)}, actual={sorted(addressed)}"
        )
    _unique(interpretation["ambiguities"], "ambiguity_id", "ambiguity id")
    _unique(
        interpretation["disagreements_with_proposal"],
        "disagreement_id",
        "upstream disagreement id",
    )
    return interpretation


def validate_critique(
    root: Path,
    path: Path,
    change_path: Path,
    interpretation_paths: list[Path],
) -> dict[str, Any]:
    change = validate_change(root, change_path)
    interpretations = [
        validate_interpretation(root, interpretation_path, change_path)
        for interpretation_path in interpretation_paths
    ]
    if len(interpretations) < 2:
        raise IntakeError("cross-critique requires at least two independent interpretations")
    interpretation_ids = [item["interpretation_id"] for item in interpretations]
    if len(interpretation_ids) != len(set(interpretation_ids)):
        raise IntakeError("interpretation IDs must be unique before cross-critique")
    perspectives = [item["perspective"] for item in interpretations]
    if len(perspectives) != len(set(perspectives)):
        raise IntakeError("interpretation perspectives must be independent before cross-critique")
    critique = _load_artifact(path, "architecture_critique")
    _verify_context_files(root, critique)
    if critique["change_id"] != change["change_id"]:
        raise IntakeError("critique change_id does not match proposal")
    if critique["architecture_change_sha256"] != sha256_file(change_path):
        raise IntakeError("critique is not bound to the proposal bytes")
    expected_interpretations = {
        item["interpretation_id"]: sha256_file(interpretation_path)
        for item, interpretation_path in zip(interpretations, interpretation_paths)
    }
    declared_ids = [item["interpretation_id"] for item in critique["interpretation_hashes"]]
    if len(declared_ids) != len(set(declared_ids)):
        raise IntakeError("critique has duplicate interpretation hash bindings")
    declared_interpretations = {
        item["interpretation_id"]: item["sha256"]
        for item in critique["interpretation_hashes"]
    }
    if declared_interpretations != expected_interpretations:
        raise IntakeError("critique is not bound to every exact interpretation")
    test_ids = {test["test_id"] for test in change["acceptance_tests"]}
    reviewed = set(critique["reviewed_acceptance_test_ids"])
    if reviewed != test_ids:
        raise IntakeError("critique must review every and only proposed acceptance test")
    _unique(critique["concerns"], "concern_id", "critique concern id")
    for concern in critique["concerns"]:
        unknown = set(concern["acceptance_test_ids"]) - test_ids
        if unknown:
            raise IntakeError(
                f"concern {concern['concern_id']} references unknown tests: {sorted(unknown)}"
            )
    return critique


def validate_consensus(
    root: Path,
    path: Path,
    change_path: Path,
    interpretation_paths: list[Path],
    critique_path: Path,
) -> dict[str, Any]:
    change = validate_change(root, change_path)
    interpretations = [
        validate_interpretation(root, interpretation_path, change_path)
        for interpretation_path in interpretation_paths
    ]
    critique = validate_critique(root, critique_path, change_path, interpretation_paths)
    consensus = _load_artifact(path, "architecture_consensus")
    if consensus["change_id"] != change["change_id"]:
        raise IntakeError("consensus change_id does not match proposal")
    hash_bindings = {
        "architecture_change_sha256": sha256_file(change_path),
        "critique_sha256": sha256_file(critique_path),
    }
    for field, expected in hash_bindings.items():
        if consensus[field] != expected:
            raise IntakeError(f"consensus has stale or incorrect {field}")
    expected_interpretations = {
        interpretation["interpretation_id"]: sha256_file(interpretation_path)
        for interpretation, interpretation_path in zip(interpretations, interpretation_paths)
    }
    declared_ids = [item["interpretation_id"] for item in consensus["interpretation_hashes"]]
    if len(declared_ids) != len(set(declared_ids)):
        raise IntakeError("consensus has duplicate interpretation hash bindings")
    declared_interpretations = {
        item["interpretation_id"]: item["sha256"]
        for item in consensus["interpretation_hashes"]
    }
    if declared_interpretations != expected_interpretations:
        raise IntakeError("consensus has stale or incomplete interpretation hash bindings")

    disagreement_ids = _unique(consensus["disagreements"], "disagreement_id", "consensus disagreement id")
    test_ids = {test["test_id"] for test in change["acceptance_tests"]}
    for disagreement in consensus["disagreements"]:
        unknown = set(disagreement["resolution"]["acceptance_test_ids"]) - test_ids
        if unknown:
            raise IntakeError(
                f"resolution {disagreement['disagreement_id']} references unknown tests: {sorted(unknown)}"
            )

    expected_concerns = {item["concern_id"] for item in critique["concerns"]}
    actual_concerns = _unique(consensus["concern_dispositions"], "concern_id", "concern disposition id")
    if actual_concerns != expected_concerns:
        raise IntakeError("consensus must disposition every and only critique concern")
    concern_by_id = {item["concern_id"]: item for item in critique["concerns"]}
    for disposition in consensus["concern_dispositions"]:
        if concern_by_id[disposition["concern_id"]]["resolution_required"]:
            resolution_id = disposition["resolution_id"]
            if not resolution_id or resolution_id not in disagreement_ids:
                raise IntakeError(
                    f"required concern {disposition['concern_id']} lacks a valid resolution"
                )

    upstream_ids = [
        item["disagreement_id"]
        for interpretation in interpretations
        for item in interpretation["disagreements_with_proposal"]
    ]
    if len(upstream_ids) != len(set(upstream_ids)):
        raise IntakeError("upstream disagreement IDs must be globally unique")
    expected_upstream = set(upstream_ids)
    actual_upstream = _unique(
        consensus["upstream_disagreement_dispositions"],
        "disagreement_id",
        "upstream disagreement disposition id",
    )
    if actual_upstream != expected_upstream:
        raise IntakeError("consensus must disposition every and only interpretation disagreement")
    for disposition in consensus["upstream_disagreement_dispositions"]:
        resolution_id = disposition["resolution_id"]
        if not resolution_id or resolution_id not in disagreement_ids:
            raise IntakeError(
                f"upstream disagreement {disposition['disagreement_id']} lacks a valid resolution"
            )

    actual_tests = _unique(consensus["acceptance_test_dispositions"], "test_id", "test disposition id")
    if actual_tests != test_ids:
        raise IntakeError("consensus must disposition every and only proposed acceptance test")
    return consensus


def validate_human_ratification(
    root: Path,
    path: Path,
    consensus_path: Path,
    human_required_state_path: Path,
    change_id: str,
) -> dict[str, Any]:
    ratification = _load_artifact(path, "architecture_human_ratification")
    consensus = _load_artifact(consensus_path, "architecture_consensus")
    if ratification["change_id"] != change_id:
        raise IntakeError("human ratification change_id does not match intake")
    _validate_scope_proposal_binding(root, change_id, ratification)
    blockers = consensus_release_blockers(consensus)
    if blockers:
        raise IntakeError(
            "consensus is not releasable for implementation: " + "; ".join(blockers)
        )
    if ratification["consensus_sha256"] != sha256_file(consensus_path):
        raise IntakeError("human ratification is not bound to the exact consensus")
    if ratification["human_required_state_sha256"] != sha256_file(human_required_state_path):
        raise IntakeError("human ratification is not bound to the exact paused state")
    evidence = ratification["authorization_evidence"]
    evidence_path = _root_path(root, evidence["path"])
    if not evidence_path.is_file():
        raise IntakeError(f"human authorization evidence is missing: {evidence['path']}")
    if sha256_file(evidence_path) != evidence["sha256"]:
        raise IntakeError("human authorization evidence hash mismatch")
    try:
        evidence_text = evidence_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise IntakeError("human authorization evidence must be UTF-8 text") from exc
    if evidence["excerpt"] not in evidence_text:
        raise IntakeError("human authorization excerpt is absent from bound evidence")
    return ratification


def consensus_release_blockers(consensus: dict[str, Any]) -> list[str]:
    """Return model-deliberation states that forbid implementation release.

    Human authority is necessary but does not turn an explicit model ``rework``
    or ``reject`` into a passing technical gate.  A revised proposal must first
    produce a new hash-bound consensus.  This prevents an advocate or a later
    routing layer from smoothing over the critic's preserved verdict.
    """
    blockers: list[str] = []
    if consensus.get("recommendation") != "proceed_to_implementation":
        blockers.append(
            f"recommendation is {consensus.get('recommendation')!r}, not proceed_to_implementation"
        )
    unresolved = [
        item["disagreement_id"] for item in consensus.get("disagreements", [])
        if item["resolution"]["status"] != "resolved"
    ]
    if unresolved:
        blockers.append(f"unresolved disagreements={sorted(unresolved)}")
    unresolved_concerns = [
        item["concern_id"] for item in consensus.get("concern_dispositions", [])
        if item["status"] == "unresolved"
    ]
    if unresolved_concerns:
        blockers.append(f"unresolved concerns={sorted(unresolved_concerns)}")
    unresolved_upstream = [
        item["disagreement_id"]
        for item in consensus.get("upstream_disagreement_dispositions", [])
        if item["status"] == "unresolved"
    ]
    if unresolved_upstream:
        blockers.append(f"unresolved upstream disagreements={sorted(unresolved_upstream)}")
    invalid_tests = [
        item["test_id"]
        for item in consensus.get("acceptance_test_dispositions", [])
        if item["status"] == "removed"
        or (item["status"] == "modified" and not item["replacement_test_id"])
    ]
    if invalid_tests:
        blockers.append(
            "removed/underspecified acceptance tests=" + repr(sorted(invalid_tests))
        )
    return blockers


def _relative_artifact(root: Path, path: Path) -> str:
    root = root.resolve()
    path = path.resolve()
    try:
        return str(path.relative_to(root))
    except ValueError as exc:
        raise IntakeError(f"artifact is outside intake root: {path}") from exc


def _artifact_entry(root: Path, path: Path) -> dict[str, str]:
    return {"path": _relative_artifact(root, path), "sha256": sha256_file(path)}


def _new_state(root: Path, change_path: Path) -> dict[str, Any]:
    change = validate_change(root, change_path)
    return {
        "schema_version": 1,
        "change_id": change["change_id"],
        "phase": "collecting_interpretations",
        "human_required": True,
        "implementation_authorized": False,
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "artifacts": {"architecture_change": _artifact_entry(root, change_path)},
        "history": [
            {
                "at": utc_now(),
                "transition": "proposed->collecting_interpretations",
                "artifact_sha256": sha256_file(change_path),
            }
        ],
    }


def initialize_intake(root: Path, change_path: Path, state_path: Path) -> dict[str, Any]:
    if state_path.exists():
        raise IntakeError(f"state already exists: {state_path}")
    state = _new_state(root, change_path)
    atomic_write_json(state_path, state)
    return state


def _load_verified_state(root: Path, state_path: Path) -> dict[str, Any]:
    state = load_json(state_path)
    required = {
        "schema_version", "change_id", "phase", "human_required",
        "implementation_authorized", "artifacts", "history",
    }
    missing = required - set(state)
    if missing:
        raise IntakeError(f"state is missing fields: {sorted(missing)}")
    if state["schema_version"] != 1:
        raise IntakeError("state schema_version must be 1")
    phase_flags = {
        "collecting_interpretations": (True, False),
        "awaiting_consensus": (True, False),
        "human_required": (True, False),
        "human_approved": (False, True),
    }
    if state["phase"] not in phase_flags:
        raise IntakeError(f"unknown intake phase: {state['phase']!r}")
    expected_flags = phase_flags[state["phase"]]
    actual_flags = (state["human_required"], state["implementation_authorized"])
    if actual_flags != expected_flags:
        raise IntakeError(
            f"human/authorization flags do not match phase {state['phase']}: "
            f"expected={expected_flags}, actual={actual_flags}"
        )

    artifact_keys = set(state["artifacts"])
    interpretation_keys = {
        key for key in artifact_keys if key.startswith("architecture_interpretation:")
    }
    fixed_keys = artifact_keys - interpretation_keys
    required_fixed = {
        "collecting_interpretations": {"architecture_change"},
        "awaiting_consensus": {"architecture_change", "architecture_critique"},
        "human_required": {
            "architecture_change", "architecture_critique", "architecture_consensus",
        },
        "human_approved": {
            "architecture_change", "architecture_critique", "architecture_consensus",
            "architecture_human_ratification",
        },
    }[state["phase"]]
    minimum_interpretations = 0 if state["phase"] == "collecting_interpretations" else 2
    if fixed_keys != required_fixed or len(interpretation_keys) < minimum_interpretations:
        raise IntakeError(
            f"artifact set does not match phase {state['phase']}: "
            f"required_fixed={sorted(required_fixed)}, "
            f"minimum_interpretations={minimum_interpretations}, "
            f"actual={sorted(artifact_keys)}"
        )
    for artifact_key, entry in state["artifacts"].items():
        if not isinstance(entry, dict) or set(entry) != {"path", "sha256"}:
            raise IntakeError(f"malformed recorded artifact entry: {artifact_key}")
        artifact_path = _root_path(root, entry["path"])
        if not artifact_path.is_file():
            raise IntakeError(f"recorded artifact is missing: {entry['path']}")
        actual = sha256_file(artifact_path)
        if actual != entry["sha256"]:
            raise IntakeError(f"recorded artifact changed after transition: {entry['path']}")
        artifact_type = artifact_key.split(":", 1)[0]
        if artifact_type not in SCHEMAS:
            raise IntakeError(f"unknown recorded artifact type: {artifact_key}")
    return state


def _interpretation_paths(root: Path, state: dict[str, Any]) -> list[Path]:
    keys = sorted(
        key for key in state["artifacts"] if key.startswith("architecture_interpretation:")
    )
    return [_root_path(root, state["artifacts"][key]["path"]) for key in keys]


def _record(
    root: Path,
    state_path: Path,
    artifact_type: str,
    artifact_path: Path,
    expected_phase: str,
    next_phase: str,
    *,
    human_required: bool | None = None,
    implementation_authorized: bool | None = None,
) -> dict[str, Any]:
    state = _load_verified_state(root, state_path)
    source_state_sha256 = sha256_file(state_path)
    if state["phase"] != expected_phase:
        raise IntakeError(
            f"illegal intake transition: phase is {state['phase']}, expected {expected_phase}"
        )
    if artifact_type in state["artifacts"]:
        raise IntakeError(f"artifact already recorded: {artifact_type}")
    entry = _artifact_entry(root, artifact_path)
    state["artifacts"][artifact_type] = entry
    state["phase"] = next_phase
    if human_required is not None:
        state["human_required"] = human_required
    if implementation_authorized is not None:
        state["implementation_authorized"] = implementation_authorized
    state["updated_at"] = utc_now()
    state["history"].append(
        {
            "at": utc_now(),
            "transition": f"{expected_phase}->{next_phase}",
            "source_state_sha256": source_state_sha256,
            "artifact_sha256": entry["sha256"],
        }
    )
    atomic_write_json(state_path, state)
    return state


def record_interpretation(root: Path, state_path: Path, path: Path) -> dict[str, Any]:
    state = _load_verified_state(root, state_path)
    if state["phase"] != "collecting_interpretations":
        raise IntakeError(
            f"illegal intake transition: phase is {state['phase']}, "
            "expected collecting_interpretations"
        )
    change_path = _root_path(root, state["artifacts"]["architecture_change"]["path"])
    interpretation = validate_interpretation(root, path, change_path)
    prior = [
        validate_interpretation(root, prior_path, change_path)
        for prior_path in _interpretation_paths(root, state)
    ]
    if interpretation["interpretation_id"] in {item["interpretation_id"] for item in prior}:
        raise IntakeError(f"duplicate interpretation ID: {interpretation['interpretation_id']}")
    if interpretation["perspective"] in {item["perspective"] for item in prior}:
        raise IntakeError(f"duplicate interpretation perspective: {interpretation['perspective']}")
    return _record(
        root, state_path,
        f"architecture_interpretation:{interpretation['interpretation_id']}", path,
        "collecting_interpretations", "collecting_interpretations",
    )


def record_critique(root: Path, state_path: Path, path: Path) -> dict[str, Any]:
    state = _load_verified_state(root, state_path)
    if state["phase"] != "collecting_interpretations":
        raise IntakeError(
            f"illegal intake transition: phase is {state['phase']}, "
            "expected collecting_interpretations"
        )
    change_path = _root_path(root, state["artifacts"]["architecture_change"]["path"])
    interpretation_paths = _interpretation_paths(root, state)
    validate_critique(root, path, change_path, interpretation_paths)
    return _record(
        root, state_path, "architecture_critique", path,
        "collecting_interpretations", "awaiting_consensus",
    )


def record_consensus(root: Path, state_path: Path, path: Path) -> dict[str, Any]:
    state = _load_verified_state(root, state_path)
    if state["phase"] != "awaiting_consensus":
        raise IntakeError(
            f"illegal intake transition: phase is {state['phase']}, expected awaiting_consensus"
        )
    change_path = _root_path(root, state["artifacts"]["architecture_change"]["path"])
    interpretation_paths = _interpretation_paths(root, state)
    critique_path = _root_path(root, state["artifacts"]["architecture_critique"]["path"])
    validate_consensus(root, path, change_path, interpretation_paths, critique_path)
    return _record(
        root, state_path, "architecture_consensus", path,
        "awaiting_consensus", "human_required",
    )


def record_human_ratification(root: Path, state_path: Path, path: Path) -> dict[str, Any]:
    state = _load_verified_state(root, state_path)
    if state["phase"] != "human_required":
        raise IntakeError(
            f"illegal intake transition: phase is {state['phase']}, expected human_required"
        )
    consensus_path = _root_path(
        root, state["artifacts"]["architecture_consensus"]["path"]
    )
    validate_human_ratification(
        root, path, consensus_path, state_path, state["change_id"]
    )
    return _record(
        root, state_path, "architecture_human_ratification", path,
        "human_required", "human_approved",
        human_required=False, implementation_authorized=True,
    )


def validate_authorized_intake(root: Path, state_path: Path) -> dict[str, Any]:
    """Revalidate an approved intake chain from source bytes.

    ``_load_verified_state`` protects every recorded artifact hash.  This
    function additionally reconstructs and validates the complete proposal ->
    interpretations -> critique -> consensus -> human-ratification chain.  It
    is intended for execution preflights, not merely for displaying status.
    """
    state = _load_verified_state(root, state_path)
    if state["phase"] != "human_approved":
        raise IntakeError(
            f"architecture intake is not human_approved: {state['phase']}"
        )
    if state["human_required"] or not state["implementation_authorized"]:
        raise IntakeError("architecture intake does not authorize implementation")

    artifacts = state["artifacts"]
    change_path = _root_path(root, artifacts["architecture_change"]["path"])
    interpretation_paths = _interpretation_paths(root, state)
    critique_path = _root_path(root, artifacts["architecture_critique"]["path"])
    consensus_path = _root_path(root, artifacts["architecture_consensus"]["path"])
    ratification_path = _root_path(
        root, artifacts["architecture_human_ratification"]["path"]
    )

    change = validate_change(root, change_path)
    validate_consensus(
        root, consensus_path, change_path, interpretation_paths, critique_path
    )
    ratification = _load_artifact(
        ratification_path, "architecture_human_ratification"
    )
    consensus = _load_artifact(consensus_path, "architecture_consensus")
    blockers = consensus_release_blockers(consensus)
    if blockers:
        raise IntakeError(
            "approved intake contains a non-releasable consensus: "
            + "; ".join(blockers)
        )
    if ratification["change_id"] != state["change_id"]:
        raise IntakeError("human ratification change_id does not match intake")
    _validate_scope_proposal_binding(root, state["change_id"], ratification)
    if change["change_id"] != state["change_id"]:
        raise IntakeError("proposal change_id does not match intake")
    if ratification["consensus_sha256"] != sha256_file(consensus_path):
        raise IntakeError("human ratification is not bound to the exact consensus")

    transitions = [
        item for item in state["history"]
        if item.get("transition") == "human_required->human_approved"
    ]
    if len(transitions) != 1:
        raise IntakeError("approved intake needs exactly one human approval transition")
    transition = transitions[0]
    expected_source = transition.get("source_state_sha256")
    if expected_source != ratification["human_required_state_sha256"]:
        raise IntakeError("human ratification is not bound to the recorded paused state")
    if transition.get("artifact_sha256") != sha256_file(ratification_path):
        raise IntakeError("approval transition is not bound to the ratification bytes")

    evidence = ratification["authorization_evidence"]
    evidence_path = _root_path(root, evidence["path"])
    if not evidence_path.is_file():
        raise IntakeError(f"human authorization evidence is missing: {evidence['path']}")
    if sha256_file(evidence_path) != evidence["sha256"]:
        raise IntakeError("human authorization evidence hash mismatch")
    try:
        evidence_text = evidence_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise IntakeError("human authorization evidence must be UTF-8 text") from exc
    if evidence["excerpt"] not in evidence_text:
        raise IntakeError("human authorization excerpt is absent from bound evidence")

    return {
        "state": state,
        "change": change,
        "ratification": ratification,
        "paths": {
            "state": state_path,
            "change": change_path,
            "consensus": consensus_path,
            "ratification": ratification_path,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init")
    init.add_argument("--change", type=Path, required=True)
    init.add_argument("--state", type=Path, required=True)
    for name in ("interpret", "critique", "consensus", "ratify"):
        command = sub.add_parser(name)
        command.add_argument("--state", type=Path, required=True)
        command.add_argument("--artifact", type=Path, required=True)
    status = sub.add_parser("status")
    status.add_argument("--state", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        root = args.root.resolve()
        if args.command == "init":
            result = initialize_intake(root, args.change, args.state)
        elif args.command == "interpret":
            result = record_interpretation(root, args.state, args.artifact)
        elif args.command == "critique":
            result = record_critique(root, args.state, args.artifact)
        elif args.command == "consensus":
            result = record_consensus(root, args.state, args.artifact)
        elif args.command == "ratify":
            result = record_human_ratification(root, args.state, args.artifact)
        else:
            result = _load_verified_state(root, args.state)
    except BaseException as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}))
        return 1
    print(json.dumps({"ok": True, "state": result}, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
