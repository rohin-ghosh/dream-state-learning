"""Experiment-wide bijection between scheduled and physical model calls.

The recurrent scheduler may execute a shared prefix once and attribute it to
several experimental arms.  This ledger keeps *physical execution* separate
from *arm attribution*: every scheduled physical slot is consumed exactly
once, while one slot may contribute cost to several declared arms.  Dynamic
model-call bytes remain in the provider/operation ledgers; this layer binds
their immutable artifact hashes to the predeclared experiment schedule.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any, Literal, Mapping, Sequence


SCHEMA_VERSION = "experiment-call-ledger-v1.0"
_HASH = re.compile(r"[0-9a-f]{64}")
_ARM = re.compile(r"[a-z][a-z0-9_]{0,63}")
_STAGE = re.compile(r"[A-Z][A-Z0-9_]{0,63}")
_OWNER = re.compile(r"[a-z][a-z0-9_.:-]{0,127}")


class ExperimentLedgerError(ValueError):
    """Raised when schedule, execution, or attribution is not bijective."""


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _require_hash(value: Any, path: str) -> None:
    if not isinstance(value, str) or _HASH.fullmatch(value) is None:
        raise ExperimentLedgerError(f"{path} must be one lowercase SHA-256 digest")


@dataclass(frozen=True)
class ScheduledPhysicalCall:
    """One predeclared physical invocation and its cost attribution."""

    slot_id: str
    call_id: str
    run_id: str
    life_id: str
    physical_owner: str
    attributed_arms: tuple[str, ...]
    stage: str
    round_index: int
    call_index: int
    config_sha256: str

    @classmethod
    def create(
        cls, *, run_id: str, life_id: str, physical_owner: str,
        attributed_arms: Sequence[str], stage: str, round_index: int,
        call_index: int, config_sha256: str,
    ) -> "ScheduledPhysicalCall":
        arms = tuple(sorted(attributed_arms))
        material = {
            "run_id": run_id, "life_id": life_id,
            "physical_owner": physical_owner, "attributed_arms": list(arms),
            "stage": stage, "round_index": round_index,
            "call_index": call_index, "config_sha256": config_sha256,
        }
        slot_id = _sha256_json({"slot": material})
        call_id = _sha256_json({"physical_call": slot_id})
        result = cls(
            slot_id=slot_id, call_id=call_id, run_id=run_id, life_id=life_id,
            physical_owner=physical_owner, attributed_arms=arms, stage=stage,
            round_index=round_index, call_index=call_index,
            config_sha256=config_sha256,
        )
        result.validate()
        return result

    def validate(self) -> None:
        for name in ("slot_id", "call_id", "run_id", "life_id", "config_sha256"):
            _require_hash(getattr(self, name), f"slot.{name}")
        if not isinstance(self.physical_owner, str) or \
                _OWNER.fullmatch(self.physical_owner) is None:
            raise ExperimentLedgerError("slot.physical_owner is invalid")
        if not self.attributed_arms or tuple(sorted(set(self.attributed_arms))) != \
                self.attributed_arms or any(_ARM.fullmatch(item) is None
                                             for item in self.attributed_arms):
            raise ExperimentLedgerError(
                "slot.attributed_arms must be a sorted unique non-empty arm tuple"
            )
        if not isinstance(self.stage, str) or _STAGE.fullmatch(self.stage) is None:
            raise ExperimentLedgerError("slot.stage is invalid")
        for name in ("round_index", "call_index"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ExperimentLedgerError(f"slot.{name} must be non-negative")
        material = {
            "run_id": self.run_id, "life_id": self.life_id,
            "physical_owner": self.physical_owner,
            "attributed_arms": list(self.attributed_arms), "stage": self.stage,
            "round_index": self.round_index, "call_index": self.call_index,
            "config_sha256": self.config_sha256,
        }
        if self.slot_id != _sha256_json({"slot": material}):
            raise ExperimentLedgerError("slot_id does not bind the schedule material")
        if self.call_id != _sha256_json({"physical_call": self.slot_id}):
            raise ExperimentLedgerError("call_id does not bind the physical slot")


@dataclass(frozen=True)
class ObservedPhysicalCall:
    """Immutable result binding for one scheduled provider invocation."""

    slot_id: str
    call_id: str
    provider_artifact_sha256: str
    parser_outcome: Literal["PARSED", "REJECTED", "ERROR"]
    parser_artifact_sha256: str
    admission_outcome: Literal["ADMITTED", "REJECTED", "NOT_APPLICABLE"]
    admitted_artifact_sha256: str | None

    def validate(self) -> None:
        for name in (
            "slot_id", "call_id", "provider_artifact_sha256",
            "parser_artifact_sha256",
        ):
            _require_hash(getattr(self, name), f"observation.{name}")
        if self.parser_outcome not in {"PARSED", "REJECTED", "ERROR"}:
            raise ExperimentLedgerError("observation.parser_outcome is invalid")
        if self.admission_outcome not in {"ADMITTED", "REJECTED", "NOT_APPLICABLE"}:
            raise ExperimentLedgerError("observation.admission_outcome is invalid")
        if self.parser_outcome == "PARSED":
            if self.admission_outcome == "NOT_APPLICABLE":
                raise ExperimentLedgerError("parsed output requires an admission outcome")
        elif self.admission_outcome != "NOT_APPLICABLE":
            raise ExperimentLedgerError("unparsed output cannot have an admission decision")
        if self.admission_outcome == "ADMITTED":
            _require_hash(
                self.admitted_artifact_sha256,
                "observation.admitted_artifact_sha256",
            )
        elif self.admitted_artifact_sha256 is not None:
            raise ExperimentLedgerError(
                "only an admitted call may carry admitted_artifact_sha256"
            )


@dataclass(frozen=True)
class ImmutableExperimentCallLedger:
    """Append-only schedule/execution ledger with matched-arm validation."""

    run_id: str
    slots: tuple[ScheduledPhysicalCall, ...]
    observations: tuple[ObservedPhysicalCall, ...] = ()
    schema_version: str = SCHEMA_VERSION

    def validate(self, *, require_complete: bool = False) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ExperimentLedgerError("experiment ledger schema mismatch")
        _require_hash(self.run_id, "ledger.run_id")
        if not self.slots:
            raise ExperimentLedgerError("experiment ledger needs scheduled slots")
        for slot in self.slots:
            slot.validate()
            if slot.run_id != self.run_id:
                raise ExperimentLedgerError("scheduled slot crossed experiment run")
        slot_ids = [item.slot_id for item in self.slots]
        call_ids = [item.call_id for item in self.slots]
        if len(slot_ids) != len(set(slot_ids)) or len(call_ids) != len(set(call_ids)):
            raise ExperimentLedgerError("scheduled physical slots/calls must be unique")
        by_slot = {item.slot_id: item for item in self.slots}
        observed_slots: set[str] = set()
        observed_calls: set[str] = set()
        for observation in self.observations:
            observation.validate()
            slot = by_slot.get(observation.slot_id)
            if slot is None or slot.call_id != observation.call_id:
                raise ExperimentLedgerError("observation does not bind a scheduled slot")
            if observation.slot_id in observed_slots or observation.call_id in observed_calls:
                raise ExperimentLedgerError("one physical call was observed more than once")
            observed_slots.add(observation.slot_id)
            observed_calls.add(observation.call_id)
        if require_complete and observed_slots != set(slot_ids):
            missing = sorted(set(slot_ids) - observed_slots)
            raise ExperimentLedgerError(
                f"experiment call ledger is incomplete; missing={missing}"
            )

    def append(self, observation: ObservedPhysicalCall) -> "ImmutableExperimentCallLedger":
        self.validate()
        candidate = ImmutableExperimentCallLedger(
            run_id=self.run_id, slots=self.slots,
            observations=(*self.observations, observation),
        )
        candidate.validate()
        return candidate

    def assert_complete(self) -> None:
        self.validate(require_complete=True)

    def assert_matched_arm_envelopes(self, arms: Sequence[str]) -> None:
        """Require identical scheduled stage/round/config envelopes per life."""

        self.validate()
        expected_arms = tuple(sorted(set(arms)))
        if not expected_arms or any(_ARM.fullmatch(item) is None for item in expected_arms):
            raise ExperimentLedgerError("matched arms are invalid")
        life_ids = sorted({item.life_id for item in self.slots})
        for life_id in life_ids:
            envelopes: dict[str, list[tuple[str, int, str]]] = {
                arm: [] for arm in expected_arms
            }
            for slot in self.slots:
                if slot.life_id != life_id:
                    continue
                for arm in slot.attributed_arms:
                    if arm in envelopes:
                        envelopes[arm].append(
                            (slot.stage, slot.round_index, slot.config_sha256)
                        )
            normalized = {
                arm: tuple(sorted(values)) for arm, values in envelopes.items()
            }
            reference = normalized[expected_arms[0]]
            if any(value != reference for value in normalized.values()):
                raise ExperimentLedgerError(
                    f"matched arm call envelopes differ for life {life_id}"
                )

    def summary(self) -> Mapping[str, Any]:
        self.validate()
        arms = sorted({arm for slot in self.slots for arm in slot.attributed_arms})
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "physical_scheduled": len(self.slots),
            "physical_observed": len(self.observations),
            "attributed_calls_by_arm": {
                arm: sum(arm in slot.attributed_arms for slot in self.slots)
                for arm in arms
            },
            "complete": len(self.observations) == len(self.slots),
        }
