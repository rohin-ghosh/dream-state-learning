import copy
import unittest

from epoch import ADAPTER_SHA, DEADLINE, bound_result, digest, require_config, rescore_panels


class FakeScorer:
    def score(self, rows):
        return [float(index) for index, row in enumerate(rows)]


class EpochTests(unittest.TestCase):
    def config(self):
        return dict(deadline_unix=DEADLINE, parent_tokens=0, source_context_loaded=False,
            training_updates=0, judge_rank=8, judge_step=15625, adapter_sha256=ADAPTER_SHA,
            token_budget=6144, seeds=[23201, 23202], scenes=3, player_physical=2, judge_physical=7)

    def panels(self):
        return [dict(selected=[dict(scene=str(scene), caption=str(index)) for index in range(64)],
            scores=[-999.0] * 64) for scene in range(3)]

    def test_new_epoch_rescores_same_strings_without_modifying_old_scores(self):
        original = self.panels()
        before = copy.deepcopy(original)
        panels, receipts = rescore_panels(original, FakeScorer())
        self.assertEqual(original, before)
        self.assertEqual(panels['0'][63], 63.0)
        self.assertEqual(receipts[0]['selected'], original[0]['selected'])

    def test_incomplete_or_mixed_panel_is_not_used(self):
        for change in ('short', 'mixed', 'duplicate'):
            rows = self.panels()
            if change == 'short':
                rows[0]['selected'].pop()
            elif change == 'mixed':
                rows[0]['selected'][1]['scene'] = 'different'
            else:
                rows[1] = rows[0]
            with self.assertRaises(ValueError):
                rescore_panels(rows, FakeScorer())

    def test_scoring_epoch_cannot_be_silently_mixed(self):
        request = dict(identity='source24', raw='caption')
        reply = dict(request_sha256=digest(request), judge_epoch_sha256='adopted')
        self.assertEqual(bound_result(request, reply, 'adopted'), reply)
        for change in (dict(judge_epoch_sha256='widegap'), dict(request_sha256='other')):
            with self.assertRaises(ValueError):
                bound_result(request, dict(reply, **change), 'adopted')

    def test_no_parent_training_budget_or_lease_drift(self):
        require_config(self.config(), DEADLINE - 60)
        for change in (dict(parent_tokens=1), dict(source_context_loaded=True), dict(training_updates=1),
                dict(judge_step=6250), dict(adapter_sha256='other'), dict(token_budget=6143),
                dict(seeds=[23201]), dict(player_physical=0), dict(deadline_unix=DEADLINE + 1)):
            with self.assertRaises(ValueError):
                require_config(dict(self.config(), **change), DEADLINE - 60)
        with self.assertRaises(ValueError):
            require_config(self.config(), DEADLINE)


if __name__ == '__main__':
    unittest.main()
