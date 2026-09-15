"""Partial-batch reduction keeps the original prospective world gate."""

from copy import deepcopy
import unittest

from gpu.orch_terse_breadth_partial import summarize


def readout():
    panels = []
    for condition in ('OWN_TEXT', 'UNAVAILABLE'):
        for index, correct in enumerate([0, 1] + [2] * 30):
            panels.append(dict(split='PROBE', condition=condition, master=str(index),
                               summary=dict(paired=dict(correct=correct, denominator=2),
                                            individual=dict(correct=2 * correct, denominator=4))))
    recall = dict(correct=16, denominator=16)
    graph = dict(OWN_TEXT=dict(correct=4, denominator=4))
    return dict(status='COMPLETE', model_calls=1728, summary=dict(panels=panels,
                primary=dict(correct=61, denominator=64, goals=122, goal_denominator=128),
                old_recall={'0': deepcopy(recall), '8': deepcopy(recall)},
                held_audit=dict(overall=deepcopy(recall)), taught_graph=deepcopy(graph),
                previous_fresh_graph=deepcopy(graph), engineering_target_met=False,
                checks=dict(old_w0=True, old_w8=True, audit=True, taught=True,
                            previous_fresh=True, pairs=True, every_world=False)))


class PartialReductionTests(unittest.TestCase):
    def test_high_aggregate_does_not_override_missing_world(self):
        reduced = summarize(readout())
        self.assertEqual(reduced['conditions']['OWN_TEXT']['covered_worlds'], 31)
        self.assertFalse(reduced['engineering_target_met'])

    def test_missing_world_is_not_dropped_from_denominator(self):
        result = readout()
        result['summary']['panels'].pop()
        with self.assertRaisesRegex(ValueError, 'full_32_world'):
            summarize(result)

    def test_cannot_trust_stale_passing_gate(self):
        result = readout()
        result['summary']['engineering_target_met'] = True
        with self.assertRaisesRegex(ValueError, 'gate_reduction_drift'):
            summarize(result)

    def test_nonterminal_readout_is_not_reduced(self):
        result = readout()
        result['status'] = 'RUNNING'
        with self.assertRaisesRegex(ValueError, 'nonterminal_readout'):
            summarize(result)


if __name__ == '__main__':
    unittest.main()
