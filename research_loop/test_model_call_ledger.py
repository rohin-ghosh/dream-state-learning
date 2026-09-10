"""Plain CPU adversarial tests for the immutable model-call ledger."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace

from .model_call_ledger import (
    ABSENT_HASH,
    CallMaterials,
    DecodingConfig,
    ImmutableModelCallLedger,
    LedgerError,
    TokenAccounting,
    build_record,
    record_from_mapping,
    record_to_mapping,
)


def _hash(label: str) -> str:
    import hashlib
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def _materials(suffix: str = "") -> CallMaterials:
    return CallMaterials(
        prompt=f"system prompt {suffix}".encode(),
        prompt_template=b"system prompt {scope}",
        input_payload=f'{{"scope":"{suffix}"}}'.encode(),
        raw_output=f'{{"op":"PASS","suffix":"{suffix}"}}'.encode(),
    )


def _tokens(supplied: int = 4, generated: int = 2) -> TokenAccounting:
    return TokenAccounting(
        mode="EXACT_COUNTS", provenance="PROVIDER_RESPONSE",
        tokenizer_id="provider-tokenizer", tokenizer_revision="rev-1",
        supplied_token_ids=None, generated_token_ids=None,
        supplied_token_count=supplied, generated_token_count=generated,
    )


def _record(
    label: str = "a", *, life: str = "life-a", arm: str = "agenda_feedback",
    round_index: int = 0, stage: str = "THINK", call_index: int = 0,
    reset: str = "reset-a", parser_outcome: str = "PARSED",
    parser_error: str | None = None, supplied: int = 4,
):
    materials = _materials(label)
    return build_record(
        materials=materials,
        call_id=_hash(f"call-{label}-{life}-{arm}-{round_index}-{stage}-{call_index}"),
        run_id=_hash("run"), life_id=_hash(life), arm=arm,
        round_index=round_index, stage=stage, call_index=call_index,
        model_visible_scope_id=_hash(f"visible-{label}-{life}-{arm}"),
        provider="provider", model="model", model_revision="revision-1",
        raw_output_artifact_path=f"raw/{label}.json",
        parser_id="typed-operation-parser", parser_version="1",
        parser_outcome=parser_outcome, parser_error=parser_error,
        token_accounting=_tokens(supplied=supplied), decoding_seed=7,
        decoding_config=DecodingConfig(
            temperature=0.0, top_p=1.0, max_output_tokens=64,
            stop_sequences=("</operation>",),
        ),
        started_at="2026-08-31T12:00:00.000000Z",
        ended_at="2026-08-31T12:00:01.000000Z",
        reset_instance_id=_hash(reset), checkpoint_hash=_hash("checkpoint"),
        goal_hash=_hash("goal"), vocabulary_hash=ABSENT_HASH,
    ), materials


def _assert_raises(expected: type[Exception], fragment: str, fn) -> None:
    try:
        fn()
    except expected as exc:
        assert fragment in str(exc), str(exc)
    else:
        raise AssertionError(f"expected {expected.__name__}: {fragment}")


def test_append_is_persistent_atomic_and_record_is_frozen():
    record, materials = _record()
    empty = ImmutableModelCallLedger()
    appended = empty.append(record, materials)
    assert empty.records == ()
    assert appended.records == (record,)
    _assert_raises(
        FrozenInstanceError, "cannot assign",
        lambda: setattr(record, "arm", "no_feedback"),
    )
    damaged = replace(record, prompt_hash="0" * 64, call_id=_hash("damaged"))
    _assert_raises(LedgerError, "does not match supplied exact bytes",
                   lambda: appended.append(damaged, materials))
    assert appended.records == (record,)


def test_strict_mapping_rejects_latent_answer_scorer_and_unknown_fields():
    record, _ = _record()
    value = record_to_mapping(record)
    for field in ("latent_bit", "answer_valve_id", "scorer_truth", "private_goal"):
        damaged = {**value, field: "taint"}
        _assert_raises(LedgerError, "forbidden",
                       lambda damaged=damaged: record_from_mapping(damaged))
    _assert_raises(
        LedgerError, "exact fields",
        lambda: record_from_mapping({key: item for key, item in value.items()
                                     if key != "raw_output_hash"}),
    )


def test_opaque_visible_scope_rejects_seed_and_latent_role_names():
    record, _ = _record()
    _assert_raises(
        LedgerError, "lowercase SHA-256",
        lambda: replace(record, model_visible_scope_id="seed0-bit1").validate(),
    )


def test_duplicate_call_id_and_position_are_rejected_without_overwrite():
    first, materials = _record("one")
    ledger = ImmutableModelCallLedger().append(first, materials)
    duplicate_id, duplicate_materials = _record("two", call_index=1)
    duplicate_id = replace(duplicate_id, call_id=first.call_id)
    _assert_raises(LedgerError, "duplicate model call_id",
                   lambda: ledger.append(duplicate_id, duplicate_materials))
    same_position, same_materials = _record("three")
    _assert_raises(LedgerError, "duplicate model call position",
                   lambda: ledger.append(same_position, same_materials))
    assert ledger.records == (first,)


def test_missing_raw_output_and_inconsistent_material_hash_fail_closed():
    record, materials = _record()
    missing = CallMaterials(
        materials.prompt, materials.prompt_template, materials.input_payload, None  # type: ignore[arg-type]
    )
    _assert_raises(LedgerError, "materials.raw_output must be exact bytes",
                   lambda: ImmutableModelCallLedger().append(record, missing))
    altered = CallMaterials(
        materials.prompt, materials.prompt_template, materials.input_payload,
        b"different raw output",
    )
    _assert_raises(LedgerError, "raw_output_hash does not match",
                   lambda: ImmutableModelCallLedger().append(record, altered))


def test_parser_failure_is_recorded_but_requires_an_error_message():
    failed, materials = _record(
        "failure", parser_outcome="ERROR", parser_error="invalid operation JSON",
    )
    ledger = ImmutableModelCallLedger().append(failed, materials)
    summary = ledger.arm_summaries()[0]
    assert summary.error_calls == 1 and summary.parsed_calls == 0
    parsed_with_error = replace(failed, call_id=_hash("parsed"), parser_outcome="PARSED")
    _assert_raises(LedgerError, "cannot carry parser_error", parsed_with_error.validate)
    error_without_message = replace(failed, call_id=_hash("empty"), parser_error=None)
    _assert_raises(LedgerError, "requires a bounded parser_error",
                   error_without_message.validate)


def test_reset_instance_cannot_cross_lives_arms_or_rounds():
    first, first_materials = _record("one", reset="shared")
    ledger = ImmutableModelCallLedger().append(first, first_materials)
    for label, kwargs in (
        ("other-life", {"life": "life-b"}),
        ("other-arm", {"arm": "no_feedback"}),
        ("other-round", {"round_index": 1}),
    ):
        candidate, materials = _record(label, reset="shared", **kwargs)
        _assert_raises(
            LedgerError, "reset_instance_id reused across life/arm/round scope",
            lambda candidate=candidate, materials=materials: ledger.append(candidate, materials),
        )
    second, second_materials = _record(
        "same-scope", reset="shared", call_index=1,
    )
    shared = ledger.append(second, second_materials)
    shared.assert_reset_isolation()
    _assert_raises(LedgerError, "per-call reset assertion failed",
                   lambda: shared.assert_reset_isolation(require_per_call_reset=True))


def test_token_ids_and_exact_counts_are_consistent_and_provenanced():
    record, _ = _record()
    invalid_ids = TokenAccounting(
        mode="TOKEN_IDS", provenance="LOCAL_TOKENIZER",
        tokenizer_id="tok", tokenizer_revision="r1",
        supplied_token_ids=(1, 2), generated_token_ids=(3,),
        supplied_token_count=3, generated_token_count=1,
    )
    _assert_raises(LedgerError, "lengths do not match",
                   lambda: replace(record, token_accounting=invalid_ids).validate())
    invalid_counts = replace(
        record.token_accounting, supplied_token_ids=(1,), mode="EXACT_COUNTS"
    )
    _assert_raises(LedgerError, "must not include token ID arrays",
                   lambda: replace(record, token_accounting=invalid_counts).validate())


def test_private_taint_is_rejected_from_inputs_but_not_independent_output():
    marker = "PRIVATE_ANSWER_SENTINEL"
    record, materials = _record()
    tainted = CallMaterials(
        materials.prompt + marker.encode(), materials.prompt_template,
        materials.input_payload, materials.raw_output,
    )
    tainted_record = replace(record, prompt_hash=_hash("placeholder"))
    _assert_raises(
        LedgerError, "private/scorer marker",
        lambda: ImmutableModelCallLedger().append(
            tainted_record, tainted, forbidden_input_markers=(marker,),
        ),
    )
    output = CallMaterials(
        materials.prompt, materials.prompt_template, materials.input_payload,
        materials.raw_output + marker.encode(),
    )
    independent = build_record(
        materials=output, call_id=_hash("independent-output"), run_id=record.run_id,
        life_id=record.life_id, arm=record.arm, round_index=record.round_index,
        stage=record.stage, call_index=record.call_index,
        model_visible_scope_id=record.model_visible_scope_id,
        provider=record.provider, model=record.model,
        model_revision=record.model_revision, raw_output_artifact_path=None,
        parser_id=record.parser_id, parser_version=record.parser_version,
        parser_outcome="PARSED", parser_error=None,
        token_accounting=record.token_accounting, decoding_seed=record.decoding_seed,
        decoding_config=record.decoding_config, started_at=record.started_at,
        ended_at=record.ended_at, reset_instance_id=record.reset_instance_id,
        checkpoint_hash=record.checkpoint_hash, goal_hash=record.goal_hash,
        vocabulary_hash=record.vocabulary_hash,
    )
    ImmutableModelCallLedger().append(
        independent, output, forbidden_input_markers=(marker,),
    )


def test_matched_arm_summaries_enforce_schedule_model_decoding_and_input_tokens():
    ledger = ImmutableModelCallLedger()
    for arm in ("no_feedback", "agenda_feedback"):
        for index in (0, 1):
            record, materials = _record(
                f"{arm}-{index}", arm=arm, call_index=index,
                reset=f"{arm}-reset-{index}",
            )
            ledger = ledger.append(record, materials)
    summaries = ledger.assert_matched_arms(("no_feedback", "agenda_feedback"))
    assert len(summaries) == 2
    damaged, materials = _record(
        "agenda-extra", arm="agenda_feedback", call_index=2,
        reset="agenda-extra",
    )
    unbalanced = ledger.append(damaged, materials)
    _assert_raises(LedgerError, "call_count differs",
                   lambda: unbalanced.assert_matched_arms(
                       ("no_feedback", "agenda_feedback")))


def test_matched_arm_summaries_reject_unequal_supplied_token_exposure():
    left, left_materials = _record("left", arm="no_feedback", reset="left")
    right, right_materials = _record(
        "right", arm="agenda_feedback", reset="right", supplied=5,
    )
    ledger = ImmutableModelCallLedger().append(left, left_materials)
    ledger = ledger.append(right, right_materials)
    _assert_raises(LedgerError, "supplied token exposure differs",
                   lambda: ledger.assert_matched_arms(
                       ("no_feedback", "agenda_feedback")))
    assert len(ledger.assert_matched_arms(
        ("no_feedback", "agenda_feedback"), require_supplied_token_match=False,
    )) == 2

