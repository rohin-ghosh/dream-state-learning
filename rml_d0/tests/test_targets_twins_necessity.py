from __future__ import annotations

import unittest
from dataclasses import replace

from rml_d0.certificates import make_certificate, replay_certificate
from rml_d0.planner import quotient_deletion_witnesses
from rml_d0.rng import handle_metamorphic_goldens
from rml_d0.targets import (
    bridge_goldens,
    j_cut_goldens,
    make_target,
    p_four_way_golden,
    target_goldens,
    validate_bridge_rows,
    validate_p_completion,
)
from rml_d0.world import canonical_plan, useful_pairs


class TargetTwinNecessityTests(unittest.TestCase):
    def test_all_targets_and_j_cuts(self) -> None:
        rows, _ = target_goldens()
        self.assertEqual(len(rows), 16)
        self.assertEqual(sum(len(row["sides"]) for row in rows), 32)
        self.assertTrue(all(side["minimum_depth"] == 9 for row in rows for side in row["sides"]))
        self.assertTrue(all(side["shortest_tie_count"] == 12 for row in rows for side in row["sides"]))
        j_rows, _ = j_cut_goldens()
        self.assertEqual(len(j_rows), 16)
        self.assertTrue(all(len(row["variants"]) == 4 for row in j_rows))

    def test_bridges_p_handles_and_certificates(self) -> None:
        bridges = bridge_goldens()
        self.assertTrue(validate_bridge_rows(bridges))
        self.assertTrue(validate_p_completion(p_four_way_golden()))
        meta = handle_metamorphic_goldens()
        self.assertTrue(meta["metadata_permutation_same_sequence"])
        spec = make_target(0, 0)
        self.assertIs(spec.handles, spec.twin().handles)
        pair = next(iter(useful_pairs(spec)))
        certificate = make_certificate(spec, canonical_plan(pair, spec.valve_truth))
        self.assertTrue(replay_certificate(spec, certificate))
        self.assertFalse(replay_certificate(replace(spec, exchanger=spec.exchanger ^ 1), certificate))

    def test_all_quotient_deletion_observables(self) -> None:
        witnesses = quotient_deletion_witnesses(make_target(0, 0))
        self.assertEqual(len(witnesses), 9)
        self.assertTrue(all(row["observable_bytes_differ"] for row in witnesses))


if __name__ == "__main__":
    unittest.main()
