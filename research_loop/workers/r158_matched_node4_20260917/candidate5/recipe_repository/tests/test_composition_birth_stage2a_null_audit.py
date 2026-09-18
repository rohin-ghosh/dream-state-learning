"""Complete null execution over explicitly synthetic held fixtures only."""

from dataclasses import replace
import unittest

from organism_v6 import composition_birth_stage2a_held as held
from organism_v6 import composition_birth_stage2a_nulls as nulls
from organism_v6 import composition_birth_stage2a_null_audit as source
from tests.test_composition_birth_stage2a_held import fixtures


class NullAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.interventions = held.build_intervention_panel(role_tokens_by_world=fixtures("dose_intervention"))
        cls.chains = held.build_chain_panel(role_tokens_by_world=fixtures("dose_chain"))
        cls.result = source.audit_nulls(
            cls.interventions, cls.chains, count_context=lambda prefix: 1,
            count_action=lambda action: 1, counter_provenance="synthetic-unit-count-not-tokenizer",
            master=b"synthetic-null-audit-only",
        )

    def test_complete_one_turn_roster_and_counts(self):
        self.assertEqual(len(self.result.one_turn), 45)
        self.assertEqual(tuple(result.names for result in self.result.one_turn),
                         tuple((name,) for name in nulls.NULL_NAMES) + nulls.NULL_PAIRS)
        for result in self.result.one_turn:
            self.assertEqual(len(result.pairs), 32)
            self.assertEqual(tuple(pair.world for pair in result.pairs),
                             tuple(pair.world for pair in self.interventions))
            expected = dict.fromkeys(held.TRANSITIONS, 0)
            for pair in result.pairs:
                self.assertEqual(len(pair.actions), 2)
                self.assertTrue(all(type(action) is bytes for action in pair.actions))
                expected[pair.world.split("_")[0]] += int(pair.score.pair_both_correct)
            self.assertEqual(result.pair_both_counts, tuple(expected.items()))
            self.assertEqual(result.within_bound, all(count <= 4 for count in expected.values()))

    def test_complete_schedule_traces_and_fixed_denominators(self):
        self.assertEqual(tuple(result.name for result in self.result.schedules), nulls.SCHEDULE_NAMES)
        for result in self.result.schedules:
            self.assertEqual(len(result.worlds), 16)
            self.assertEqual(sum(len(world.runs) for world in result.worlds), 32)
            self.assertEqual(sum(len(run.calls) for world in result.worlds for run in world.runs), 32 * 29)
            self.assertEqual(result.whole_chain_count,
                             sum(member.whole_chain_success for world in result.worlds
                                 for member in world.score.members))
            self.assertEqual(result.twin_both_count, sum(world.score.pair_both_correct for world in result.worlds))
            self.assertEqual(result.within_bound,
                             result.whole_chain_count <= 16 and result.twin_both_count <= 8)

    def test_thresholds_never_open_science_gates(self):
        self.assertEqual(self.result.thresholds_passed,
                         all(result.within_bound for result in self.result.one_turn + self.result.schedules))
        self.assertEqual(self.result.status, "PARTIAL_SOURCE_ONLY")
        self.assertFalse(any(source.SCIENCE_GATES.values()))
        self.assertEqual(self.result.counter_provenance, "synthetic-unit-count-not-tokenizer")

    def test_missing_duplicate_or_reordered_panel_rejected(self):
        for panel in (self.interventions[:-1], self.interventions[::-1],
                      self.interventions[:1] + self.interventions[:-1]):
            with self.assertRaisesRegex(ValueError, "complete_ordered_intervention"):
                source.audit_one_turn(panel)
        for panel in (self.chains[:-1], self.chains[::-1]):
            with self.assertRaisesRegex(ValueError, "complete_ordered_chain"):
                source.audit_schedules(panel, count_context=lambda prefix: 1, count_action=lambda action: 1,
                                       counter_provenance="synthetic", master=b"fixture")

    def test_flipped_members_rejected_before_ranking(self):
        pair = replace(self.interventions[0], members=self.interventions[0].members[::-1])
        with self.assertRaisesRegex(ValueError, "inconsistent_intervention_members"):
            source.audit_one_turn((pair,) + self.interventions[1:])


if __name__ == "__main__":
    unittest.main()
