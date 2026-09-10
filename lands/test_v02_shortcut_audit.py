"""Focused regression tests for Semantic World v0.2 target shortcuts."""

from __future__ import annotations

from dataclasses import fields

from lands.audit_v02_shortcuts import (
    PublicTargetFeatures,
    audit_target_output_shortcuts,
    collect_offline_cases,
    passes_ambiguity_safety,
)


SKINS = ("aligned", "neutral", "conflicting")


def test_current_v02_is_unsafe_across_100_seeds_in_every_skin():
    report = audit_target_output_shortcuts(range(1, 101), SKINS)

    assert not report.ambiguity_safety_passed
    for skin in SKINS:
        skin_report = report.by_skin[skin]
        assert skin_report.n_targets == 1200
        assert skin_report.n_targets_decoded_from_pair == 1200
        assert (
            skin_report.n_targets_decoded_from_every_single_visible_role == 1200
        )
        assert skin_report.pair.n_occurrences == 1200
        assert skin_report.pair.n_deterministically_decoded_occurrences == 1200
        assert skin_report.pair.n_ambiguous_keys == 0
        assert skin_report.single_visible_role.n_occurrences == 2400
        assert (
            skin_report.single_visible_role.n_deterministically_decoded_occurrences
            == 2400
        )
        assert skin_report.single_visible_role.n_ambiguous_keys == 0
        assert not passes_ambiguity_safety(skin_report.pair)
        assert not passes_ambiguity_safety(skin_report.single_visible_role)


def test_public_features_exclude_every_offline_or_hidden_field():
    cases = collect_offline_cases((7,), "aligned")
    assert len(cases) == 12
    public_field_names = {field.name for field in fields(PublicTargetFeatures)}
    assert public_field_names == {
        "seed",
        "skin",
        "goal_id",
        "visible_outcomes",
        "visible_role_outcomes",
    }
    assert not any(
        forbidden in name
        for name in public_field_names
        for forbidden in ("answer", "hidden", "parent")
    )
    for case in cases:
        assert case.offline_answer not in case.public.visible_outcomes
        assert case.offline_answer not in {
            outcome for _, outcome in case.public.visible_role_outcomes
        }


def test_audit_is_configurable_and_serializable():
    report = audit_target_output_shortcuts((3, 9), ("neutral",))
    payload = report.to_dict()
    assert payload["seeds"] == [3, 9]
    assert payload["skins"] == ["neutral"]
    assert payload["by_skin"]["neutral"]["n_targets"] == 24
    assert payload["by_skin"]["neutral"]["ambiguity_safety_passed"] is False
