"""Deterministic Stage-A schema chronology and immutable hash-chain microcase."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

from .canonical import canonical_bytes


@dataclass(frozen=True)
class Seal:
    kind: str
    ordinal: int
    payload_sha256: str
    predecessor_sha256: str
    seal_sha256: str


class SealChain:
    def __init__(self) -> None:
        self._seals: list[Seal] = []

    def append(self, kind: str, payload: Any) -> Seal:
        predecessor = self._seals[-1].seal_sha256 if self._seals else "0" * 64
        ordinal = len(self._seals)
        payload_hash = hashlib.sha256(canonical_bytes(payload)).hexdigest()
        body = {
            "kind": kind,
            "ordinal": ordinal,
            "payload_sha256": payload_hash,
            "predecessor_sha256": predecessor,
        }
        seal = Seal(
            kind,
            ordinal,
            payload_hash,
            predecessor,
            hashlib.sha256(canonical_bytes(body)).hexdigest(),
        )
        self._seals.append(seal)
        return seal

    @property
    def seals(self) -> tuple[Seal, ...]:
        return tuple(self._seals)


def schema_chronology_golden() -> dict[str, Any]:
    chain = SealChain()
    commitment_bytes: dict[str, bytes] = {}
    commitment_objects: dict[str, dict[str, Any]] = {}
    commitment_predictions: dict[str, list[dict[str, Any]]] = {}
    status_by_commitment: dict[str, list[dict[str, Any]]] = {}
    statuses_new: list[int] = []
    status_total = 0
    prediction_counts = (3, 6, 12)
    boundary_orders: list[dict[str, Any]] = []

    chain.append("SOURCE_PREFIX", {"cut": "K0", "public_event_count": 123})
    for boundary, prediction_count in enumerate(prediction_counts):
        next_cut = f"K{boundary + 1}"
        modules = [
            {
                "descriptor": "D11" if index == prediction_count - 1 else ("D00", "D01", "D10", "D11")[index % 4],
                "module_handle": f"MF{boundary + 1:02X}{index:010X}",
                "sparse_v": index == prediction_count - 1,
            }
            for index in range(prediction_count)
        ]
        schedule = {
            "cut": f"K{boundary}",
            "module_records": modules,
            "next_cut": next_cut,
            "prediction_slots": prediction_count * 2,
        }
        schedule_seal = chain.append("NEXT_ERA_SCHEDULE", schedule)

        commitments: list[dict[str, Any]] = []
        for channel in ("C", "V"):
            commitment_id = f"SCHEMA_{channel}_K{boundary}"
            predictions = [
                {
                    "descriptor": module["descriptor"],
                    "family_handle": f"{channel}F{boundary + 1:02X}{index:010X}",
                    "module_handle": module["module_handle"],
                    "predicted_output": index % 4,
                    "prediction_id": f"PRED_{channel}_K{boundary}_{index}",
                }
                for index, module in enumerate(modules)
            ]
            commitment = {
                "channel": channel,
                "commitment_id": commitment_id,
                "cut": f"K{boundary}",
                "law_atom": f"AFFINE_{channel}_UNIQUE",
                "predictions": predictions,
                "proposal_ordinal": boundary * 2 + (channel == "V"),
                "public_root_event_handles": [f"EV{boundary:02X}{channel == 'V':01X}000000000"],
                "status": "SEALED",
            }
            commitment_seal = chain.append("SCHEMA_COMMITMENT", commitment)
            commitments.append(commitment)
            encoded = canonical_bytes(commitment)
            commitment_bytes[commitment_id] = encoded
            commitment_objects[commitment_id] = commitment
            commitment_predictions[commitment_id] = predictions
            status_by_commitment[commitment_id] = []

        confirming_seal = chain.append(
            "CONFIRMING_SOURCE_EVENTS",
            {"cut": next_cut, "scheduled_modules": prediction_count},
        )
        appended = 0
        status_ordinals: list[int] = []
        for commitment in commitments:
            channel = commitment["channel"]
            for index, prediction in enumerate(commitment["predictions"]):
                if channel == "V" and modules[index]["sparse_v"]:
                    continue
                status = {
                    "append_ordinal": status_total + appended,
                    "commitment_id": commitment["commitment_id"],
                    "comparison": "MATCH",
                    "outcome_event_handle": f"EV{boundary + 1:02X}{index:010X}",
                    "prediction_id": prediction["prediction_id"],
                    "status": "APPENDED",
                }
                status_ordinals.append(chain.append("SCHEMA_STATUS_APPEND", status).ordinal)
                status_by_commitment[commitment["commitment_id"]].append(status)
                appended += 1
        status_total += appended
        statuses_new.append(appended)

        v_commitment = commitments[1]
        v_status = status_by_commitment[v_commitment["commitment_id"]]
        supported_modules = {
            next(
                prediction["module_handle"]
                for prediction in v_commitment["predictions"]
                if prediction["prediction_id"] == status["prediction_id"]
            )
            for status in v_status
            if status["comparison"] == "MATCH"
        }
        sparse_prediction = v_commitment["predictions"][-1]
        sparse_has_status = any(
            status["prediction_id"] == sparse_prediction["prediction_id"]
            for status in v_status
        )
        if len(supported_modules) < 2 or sparse_has_status:
            raise AssertionError("prospective V support/holdout rule failed")
        descriptor_seal = chain.append(
            "P_TARGET_DESCRIPTOR",
            {
                "cut": next_cut,
                "heldout_prediction_id": sparse_prediction["prediction_id"],
                "other_local_mapping_outcomes": 11,
            },
        )
        public_seal = chain.append("P_TARGET_PUBLIC", {"cut": next_cut, "target_ordinal": 0})
        evaluation_seal = chain.append("EVALUATION_CLONE", {"cut": next_cut, "read_only": True})
        boundary_orders.append(
            {
                "commitments": [
                    seal.ordinal
                    for seal in chain.seals
                    if seal.kind == "SCHEMA_COMMITMENT"
                ][-2:],
                "confirming": confirming_seal.ordinal,
                "evaluation": evaluation_seal.ordinal,
                "p_descriptor": descriptor_seal.ordinal,
                "p_public": public_seal.ordinal,
                "schedule": schedule_seal.ordinal,
                "statuses": status_ordinals,
            }
        )
        chain.append(
            "SOURCE_PREFIX",
            {
                "cut": next_cut,
                "public_event_count": (250, 500, 996)[boundary],
            },
        )

    if statuses_new != [5, 11, 23] or status_total != 39:
        raise AssertionError("schema status append counts changed")
    if any(
        canonical_bytes(commitment_objects[commitment_id]) != encoded
        for commitment_id, encoded in commitment_bytes.items()
    ):
        raise AssertionError("commitment bytes mutated")
    # Recompute the entire chain from its public seal fields.
    for index, seal in enumerate(chain.seals):
        predecessor = chain.seals[index - 1].seal_sha256 if index else "0" * 64
        body = {
            "kind": seal.kind,
            "ordinal": seal.ordinal,
            "payload_sha256": seal.payload_sha256,
            "predecessor_sha256": predecessor,
        }
        if seal.predecessor_sha256 != predecessor or seal.seal_sha256 != hashlib.sha256(canonical_bytes(body)).hexdigest():
            raise AssertionError("schema seal chain replay failed")
    for order in boundary_orders:
        if not (
            order["schedule"] < min(order["commitments"])
            < max(order["commitments"]) < order["confirming"]
            < min(order["statuses"]) <= max(order["statuses"])
            < order["p_descriptor"] < order["p_public"] < order["evaluation"]
        ):
            raise AssertionError("schedule was not sealed before commitment")
    return {
        "commitment_count": 6,
        "commitment_prediction_counts_by_channel": [3, 3, 6, 6, 12, 12],
        "final_chain_sha256": chain.seals[-1].seal_sha256,
        "next_era_schedule_count": 3,
        "normative_order_verified": True,
        "p_holdout_count": 3,
        "prospective_support_verified": True,
        "seal_count": len(chain.seals),
        "status_append_cumulative": [5, 16, 39],
        "status_append_new": statuses_new,
    }
