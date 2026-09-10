"""Compact replayable Stage-A target and necessity certificates."""

from __future__ import annotations

import hashlib
from typing import Any, Iterable

from .canonical import canonical_bytes
from .world import Action, TargetSpec, execute, target_public_record


def truth_object(spec: TargetSpec) -> dict[str, Any]:
    return {
        "exchanger": spec.exchanger,
        "forbidden_mask": spec.forbidden_mask,
        "necessity_mask": spec.necessity_mask,
        "provenance": list(spec.provenance),
        "transforms": list(spec.transforms),
        "valve_truth": spec.valve_truth,
    }


def make_certificate(spec: TargetSpec, actions: Iterable[Action]) -> dict[str, Any]:
    plan = tuple(actions)
    if spec.handles is None:
        raise ValueError("certificate requires injected target handles")
    trace = execute(spec, plan)
    transcript = [
        {
            "action": action.public_record(spec.handles),
            "failure_kind": transition.state.failure,
            "result_code": transition.result_code,
            "success": transition.state.success,
            "text": transition.text,
        }
        for action, transition in zip(plan, trace)
    ]
    body = {
        "plan": [action.public_record(spec.handles) for action in plan],
        "target_sha256": hashlib.sha256(
            canonical_bytes(target_public_record(spec))
        ).hexdigest(),
        "transcript": transcript,
        "truth_sha256": hashlib.sha256(canonical_bytes(truth_object(spec))).hexdigest(),
    }
    return {**body, "root_sha256": hashlib.sha256(canonical_bytes(body)).hexdigest()}


def replay_certificate(spec: TargetSpec, certificate: dict[str, Any]) -> bool:
    """Re-execute bytes and truth; never accept a stored root by itself."""

    if spec.handles is None:
        return False
    try:
        from .world import resolve_public_action

        plan = tuple(resolve_public_action(spec, record) for record in certificate["plan"])
    except (KeyError, TypeError, ValueError):
        return False
    rebuilt = make_certificate(spec, plan)
    return rebuilt == certificate
