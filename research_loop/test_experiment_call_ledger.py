"""Adversarial tests for experiment-wide physical-call accounting."""

from __future__ import annotations

from dataclasses import replace
import hashlib

from .experiment_call_ledger import (
    ExperimentLedgerError,
    ImmutableExperimentCallLedger,
    ObservedPhysicalCall,
    ScheduledPhysicalCall,
)


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


ARMS = ("agenda_feedback", "matched_distractor", "no_feedback")


def _slots(*, unequal: bool = False):
    run_id = _hash("run")
    life_id = _hash("life")
    result = []
    # One physical prefix is attributed to every arm.
    for index, stage in enumerate(("WAKE", "THINK")):
        result.append(ScheduledPhysicalCall.create(
            run_id=run_id, life_id=life_id, physical_owner="shared_prefix",
            attributed_arms=ARMS, stage=stage, round_index=0,
            call_index=index, config_sha256=_hash(f"config-{stage}"),
        ))
    for arm_index, arm in enumerate(ARMS):
        for offset, stage in enumerate(("RETURN_SLEEP", "THINK")):
            config = _hash(f"config-{stage}")
            if unequal and arm == "agenda_feedback" and stage == "THINK":
                config = _hash("different-think-config")
            result.append(ScheduledPhysicalCall.create(
                run_id=run_id, life_id=life_id, physical_owner=arm,
                attributed_arms=(arm,), stage=stage, round_index=1,
                call_index=2 + arm_index * 2 + offset, config_sha256=config,
            ))
    return run_id, tuple(result)


def _observation(slot, *, admitted=True):
    return ObservedPhysicalCall(
        slot_id=slot.slot_id, call_id=slot.call_id,
        provider_artifact_sha256=_hash(f"provider-{slot.call_id}"),
        parser_outcome="PARSED", parser_artifact_sha256=_hash(
            f"parser-{slot.call_id}"
        ),
        admission_outcome="ADMITTED" if admitted else "REJECTED",
        admitted_artifact_sha256=(
            _hash(f"admitted-{slot.call_id}") if admitted else None
        ),
    )


def _assert_rejected(fragment, function):
    try:
        function()
    except ExperimentLedgerError as exc:
        assert fragment in str(exc), str(exc)
    else:
        raise AssertionError(f"expected ledger rejection: {fragment}")


def test_shared_prefix_is_one_physical_call_sequence_but_attributed_to_all_arms():
    run_id, slots = _slots()
    ledger = ImmutableExperimentCallLedger(run_id, slots)
    ledger.assert_matched_arm_envelopes(ARMS)
    for slot in slots:
        ledger = ledger.append(_observation(slot))
    ledger.assert_complete()
    summary = ledger.summary()
    assert summary["physical_scheduled"] == 8
    assert summary["physical_observed"] == 8
    assert summary["attributed_calls_by_arm"] == {
        "agenda_feedback": 4,
        "matched_distractor": 4,
        "no_feedback": 4,
    }
    assert summary["complete"] is True


def test_missing_duplicate_unplanned_and_wrong_call_bindings_fail_closed():
    run_id, slots = _slots()
    ledger = ImmutableExperimentCallLedger(run_id, slots)
    ledger = ledger.append(_observation(slots[0]))
    _assert_rejected("incomplete", ledger.assert_complete)
    _assert_rejected(
        "observed more than once",
        lambda: ledger.append(_observation(slots[0])),
    )
    foreign = replace(
        _observation(slots[1]), slot_id=_hash("foreign-slot"),
    )
    _assert_rejected(
        "does not bind a scheduled slot", lambda: ledger.append(foreign),
    )
    wrong_call = replace(
        _observation(slots[1]), call_id=slots[0].call_id,
    )
    _assert_rejected(
        "does not bind a scheduled slot", lambda: ledger.append(wrong_call),
    )


def test_matched_arm_envelope_rejects_decoding_or_budget_differences():
    run_id, slots = _slots(unequal=True)
    ledger = ImmutableExperimentCallLedger(run_id, slots)
    _assert_rejected(
        "matched arm call envelopes differ",
        lambda: ledger.assert_matched_arm_envelopes(ARMS),
    )


def test_slot_hashes_and_run_scope_cannot_be_rewritten():
    run_id, slots = _slots()
    _assert_rejected(
        "slot_id does not bind",
        lambda: replace(slots[0], physical_owner="different-owner").validate(),
    )
    _assert_rejected(
        "crossed experiment run",
        lambda: ImmutableExperimentCallLedger(_hash("other-run"), slots).validate(),
    )


def test_parser_and_admission_states_are_consistent():
    _, slots = _slots()
    parsed = _observation(slots[0])
    _assert_rejected(
        "parsed output requires",
        lambda: replace(parsed, admission_outcome="NOT_APPLICABLE",
                        admitted_artifact_sha256=None).validate(),
    )
    _assert_rejected(
        "unparsed output cannot",
        lambda: replace(parsed, parser_outcome="REJECTED").validate(),
    )
    _assert_rejected(
        "only an admitted call",
        lambda: replace(parsed, admission_outcome="REJECTED").validate(),
    )
