from __future__ import annotations

import unittest

from rml_d0.schema_reference import schema_chronology_golden
from rml_d0.source import (
    balance_action_only_masses,
    complete_be_goldens,
    validate_balance_source,
    validate_complete_be,
)
from rml_d0.targets import source_count_golden, valve_balance_goldens


class SourceScheduleTests(unittest.TestCase):
    def test_literal_expansion_complete_be_and_counts(self) -> None:
        source = complete_be_goldens()
        self.assertTrue(validate_balance_source(source, balance_action_only_masses(0)))
        self.assertEqual(source["literal_event_counts"], [123, 250, 500, 996])
        self.assertEqual([row["mu"] for row in source["all_mu_complete_be"]], [0, 1, 2, 3])
        self.assertTrue(all(row["be_equal"] for row in source["all_mu_complete_be"]))
        self.assertTrue(source["bridge_distinct_across_trials"])
        self.assertTrue(all(row["shared_within_trial"] for row in source["bridge_shared_within_trial"]))

    def test_two_mode_mutant_is_rejected(self) -> None:
        mutant = validate_complete_be(2)
        self.assertEqual(mutant["literal_event_counts"], [123, 248, 496, 990])
        self.assertEqual(balance_action_only_masses(0, 2), [6, 6, 0, 0])
        self.assertFalse(validate_balance_source(mutant, balance_action_only_masses(0, 2)))

    def test_symbolic_counts_balance_and_schema_chronology(self) -> None:
        self.assertEqual(
            source_count_golden()["cumulative_mappings"], [36, 71, 142, 285]
        )
        self.assertEqual(valve_balance_goldens()["action_only_integer_masses"], [6] * 4)
        chronology = schema_chronology_golden()
        self.assertEqual(chronology["status_append_new"], [5, 11, 23])
        self.assertEqual(chronology["commitment_prediction_counts_by_channel"], [3, 3, 6, 6, 12, 12])
        self.assertTrue(chronology["normative_order_verified"])


if __name__ == "__main__":
    unittest.main()
