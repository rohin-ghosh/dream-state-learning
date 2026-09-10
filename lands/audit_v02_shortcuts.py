"""CPU-only target-output shortcut audit for Semantic World v0.2.

This module deliberately does not change the v0.2 generator.  It treats the
target observations as public features and the withheld goal answer as an
offline audit label, then measures whether either of these shortcuts is a
deterministic decoder:

* the sorted pair of visible target outcomes; or
* one visible ``(role, outcome)`` at a time.

``role`` here is the role of the *visible anchor animal*.  All three anchors
are publicly calibrated in every source land, so this equivalence class is
recoverable from the lifetime.  The hidden target role, parents, and goal
answer are never included in a shortcut key.

The audit is intentionally stricter than ordinary train/test evaluation.  A
future instrument is considered shortcut-safe only when every observed key
has both repeated support and at least two different withheld labels.  A
singleton key therefore fails closed rather than being mistaken for evidence
of ambiguity.
"""

from __future__ import annotations

from argparse import ArgumentParser
from collections import defaultdict
from dataclasses import asdict, dataclass
import json
from typing import Iterable, Mapping, Sequence

from .model import WorldConfig
from .skins import all_skin_names
from .v02 import SemanticWorldV02, TARGET_LAND_IDS


@dataclass(frozen=True)
class PublicTargetFeatures:
    """Features available before revealing a target's withheld answer."""

    seed: int
    skin: str
    goal_id: str
    visible_outcomes: tuple[str, str]
    visible_role_outcomes: tuple[tuple[int, str], tuple[int, str]]

    @property
    def sorted_outcome_key(self) -> tuple[str, str]:
        return tuple(sorted(self.visible_outcomes))  # type: ignore[return-value]


@dataclass(frozen=True)
class OfflineShortcutCase:
    """One public feature record plus its audit-only withheld label."""

    public: PublicTargetFeatures
    offline_answer: str


@dataclass(frozen=True)
class KeyDeterminismReport:
    n_keys: int
    n_occurrences: int
    n_deterministic_keys: int
    n_ambiguous_keys: int
    n_deterministically_decoded_occurrences: int
    min_occurrences_per_key: int
    min_labels_per_key: int
    max_labels_per_key: int

    @property
    def deterministically_decoded_fraction(self) -> float:
        if self.n_occurrences == 0:
            return 0.0
        return self.n_deterministically_decoded_occurrences / self.n_occurrences

    def to_dict(self) -> dict[str, object]:
        result = asdict(self)
        result["deterministically_decoded_fraction"] = (
            self.deterministically_decoded_fraction
        )
        return result


@dataclass(frozen=True)
class SkinShortcutReport:
    skin: str
    n_targets: int
    pair: KeyDeterminismReport
    single_visible_role: KeyDeterminismReport
    n_targets_decoded_from_pair: int
    n_targets_decoded_from_every_single_visible_role: int
    ambiguity_safety_passed: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "skin": self.skin,
            "n_targets": self.n_targets,
            "pair": self.pair.to_dict(),
            "single_visible_role": self.single_visible_role.to_dict(),
            "n_targets_decoded_from_pair": self.n_targets_decoded_from_pair,
            "n_targets_decoded_from_every_single_visible_role": (
                self.n_targets_decoded_from_every_single_visible_role
            ),
            "ambiguity_safety_passed": self.ambiguity_safety_passed,
        }


@dataclass(frozen=True)
class TargetShortcutAudit:
    seeds: tuple[int, ...]
    skins: tuple[str, ...]
    by_skin: Mapping[str, SkinShortcutReport]
    ambiguity_safety_passed: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": "lands-v0.2-target-shortcut-audit-v1",
            "seeds": list(self.seeds),
            "skins": list(self.skins),
            "by_skin": {
                skin: report.to_dict() for skin, report in self.by_skin.items()
            },
            "ambiguity_safety_passed": self.ambiguity_safety_passed,
        }


def collect_offline_cases(
    seeds: Iterable[int],
    skin: str,
) -> tuple[OfflineShortcutCase, ...]:
    """Build separated public-feature/offline-label records.

    No rendered question, hidden-role identifier, target-parent set, or answer
    is included in :class:`PublicTargetFeatures`.  Internal roles are consulted
    only for the two *observed anchor animals*, whose complete calibration is
    already public in the v0.2 lifetime.
    """

    cases: list[OfflineShortcutCase] = []
    for seed in seeds:
        world = SemanticWorldV02(WorldConfig(seed=seed))
        goals_by_land = {goal.land_id: goal for goal in world.goals}
        observations_by_land = {
            land_id: tuple(
                observation
                for observation in world.blend_observations
                if observation.land_id == land_id
            )
            for land_id in TARGET_LAND_IDS
        }
        for land_id in TARGET_LAND_IDS:
            goal = goals_by_land[land_id]
            visible = observations_by_land[land_id]
            if len(visible) != 2:
                raise ValueError(
                    f"{seed}/{land_id}: expected two visible target outcomes, "
                    f"found {len(visible)}"
                )
            role_outcomes = tuple(
                sorted(
                    (
                        world.base.animal_roles[observation.animal_id],
                        world.ratio_surface(observation.ratio, skin),
                    )
                    for observation in visible
                )
            )
            cases.append(
                OfflineShortcutCase(
                    public=PublicTargetFeatures(
                        seed=seed,
                        skin=skin,
                        goal_id=goal.id,
                        visible_outcomes=tuple(
                            world.ratio_surface(observation.ratio, skin)
                            for observation in visible
                        ),  # type: ignore[arg-type]
                        visible_role_outcomes=role_outcomes,  # type: ignore[arg-type]
                    ),
                    offline_answer=world.ratio_surface(goal.answer_ratio, skin),
                )
            )
    return tuple(cases)


def _determinism_report(
    keys_and_labels: Sequence[tuple[object, str]],
) -> KeyDeterminismReport:
    labels_by_key: dict[object, set[str]] = defaultdict(set)
    occurrences_by_key: dict[object, int] = defaultdict(int)
    for key, label in keys_and_labels:
        labels_by_key[key].add(label)
        occurrences_by_key[key] += 1
    if not labels_by_key:
        raise ValueError("shortcut audit needs at least one example")
    deterministic_keys = {
        key for key, labels in labels_by_key.items() if len(labels) == 1
    }
    return KeyDeterminismReport(
        n_keys=len(labels_by_key),
        n_occurrences=len(keys_and_labels),
        n_deterministic_keys=len(deterministic_keys),
        n_ambiguous_keys=len(labels_by_key) - len(deterministic_keys),
        n_deterministically_decoded_occurrences=sum(
            occurrences_by_key[key] for key in deterministic_keys
        ),
        min_occurrences_per_key=min(occurrences_by_key.values()),
        min_labels_per_key=min(len(labels) for labels in labels_by_key.values()),
        max_labels_per_key=max(len(labels) for labels in labels_by_key.values()),
    )


def passes_ambiguity_safety(
    report: KeyDeterminismReport,
    *,
    min_occurrences_per_key: int = 2,
    min_labels_per_key: int = 2,
) -> bool:
    """Hard future-game gate: every possible shortcut key must collide.

    Requiring repeated observations prevents a key seen only once from passing
    merely because the audit has not sampled its counterexample yet.
    """

    return (
        report.min_occurrences_per_key >= min_occurrences_per_key
        and report.min_labels_per_key >= min_labels_per_key
        and report.n_deterministic_keys == 0
    )


def _audit_skin(cases: Sequence[OfflineShortcutCase], skin: str) -> SkinShortcutReport:
    pair_rows = [
        (case.public.sorted_outcome_key, case.offline_answer) for case in cases
    ]
    single_rows = [
        (role_outcome, case.offline_answer)
        for case in cases
        for role_outcome in case.public.visible_role_outcomes
    ]
    pair = _determinism_report(pair_rows)
    single = _determinism_report(single_rows)

    pair_labels: dict[object, set[str]] = defaultdict(set)
    single_labels: dict[object, set[str]] = defaultdict(set)
    for key, label in pair_rows:
        pair_labels[key].add(label)
    for key, label in single_rows:
        single_labels[key].add(label)

    return SkinShortcutReport(
        skin=skin,
        n_targets=len(cases),
        n_targets_decoded_from_pair=sum(
            len(pair_labels[case.public.sorted_outcome_key]) == 1 for case in cases
        ),
        n_targets_decoded_from_every_single_visible_role=sum(
            all(
                len(single_labels[key]) == 1
                for key in case.public.visible_role_outcomes
            )
            for case in cases
        ),
        pair=pair,
        single_visible_role=single,
        ambiguity_safety_passed=(
            passes_ambiguity_safety(pair) and passes_ambiguity_safety(single)
        ),
    )


def audit_target_output_shortcuts(
    seeds: Iterable[int],
    skins: Iterable[str] = all_skin_names(),
) -> TargetShortcutAudit:
    """Audit target-only deterministic decoders across seeds and skins."""

    seed_tuple = tuple(seeds)
    skin_tuple = tuple(skins)
    if not seed_tuple:
        raise ValueError("seeds must not be empty")
    if len(set(seed_tuple)) != len(seed_tuple):
        raise ValueError("seeds must be unique")
    known_skins = set(all_skin_names())
    unknown_skins = set(skin_tuple) - known_skins
    if unknown_skins:
        raise ValueError(f"unknown skins: {sorted(unknown_skins)}")
    reports = {
        skin: _audit_skin(collect_offline_cases(seed_tuple, skin), skin)
        for skin in skin_tuple
    }
    return TargetShortcutAudit(
        seeds=seed_tuple,
        skins=skin_tuple,
        by_skin=reports,
        ambiguity_safety_passed=all(
            report.ambiguity_safety_passed for report in reports.values()
        ),
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--seed-start", type=int, default=1)
    parser.add_argument("--seed-stop", type=int, default=101)
    parser.add_argument(
        "--skin",
        action="append",
        choices=all_skin_names(),
        dest="skins",
        help="repeat to select skins; defaults to all",
    )
    args = parser.parse_args(argv)
    report = audit_target_output_shortcuts(
        range(args.seed_start, args.seed_stop),
        tuple(args.skins) if args.skins else all_skin_names(),
    )
    print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    return 0 if report.ambiguity_safety_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
