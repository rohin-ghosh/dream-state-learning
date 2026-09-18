"""Finite TRAIN mix, scene binding, exact batch proportions and AdamW/RNG restoration."""

import copy
import random
import unittest
from unittest.mock import patch

from r210_mixed_train import MixedPairStream, partition, restore_optimizer_rng


class Tokenizer:
    def __call__(self, text, **unused):
        return {'input_ids': list(range(len(text.split())))}


def fixture():
    return [dict(contest_id=contest, scene=f'scene {contest//2}', scene_group_sha256=f'group{contest//2}',
        caption=f'caption {contest} rating {rating}', caption_family_sha256=f'{contest}-{rating}',
        votes=50, mean=rating) for contest in range(180) for rating in range(1, 6)]


class MixTests(unittest.TestCase):
    def make(self):
        return MixedPairStream(fixture(), Tokenizer(), dict(seed=177, max_length=512, vote_cap=100))

    def test_exact_mix_on_global_and_every_local_rank(self):
        batch = self.make().batch()
        for rank in range(4):
            local = partition(batch, rank)
            self.assertEqual(sum(pair['pair_type']=='CROSSED_SCENE_ASSUMPTION' for pair in local), 4)
            self.assertEqual(len(local), 16)

    def test_donor_strong_distinct_group_presented_in_recipient_scene(self):
        for pair in self.make().batch():
            if pair['pair_type'] == 'CROSSED_SCENE_ASSUMPTION':
                self.assertNotEqual(pair['left']['scene_group_sha256'], pair['right']['scene_group_sha256'])
                self.assertEqual(pair['left']['scene'], pair['right']['scene'])
                self.assertEqual(pair['right']['mean'], 5)
                self.assertEqual(pair['left']['mean'], 5)
                self.assertEqual(pair['winner'], 1)
            else:
                self.assertEqual(pair['left']['contest_id'], pair['right']['contest_id'])

    def test_pair_rng_resume_exact_and_input_rows_unchanged(self):
        first = self.make()
        original = copy.deepcopy(first.groups)
        first.batch()
        state = first.schedule.getstate()
        resumed = self.make()
        resumed.schedule.setstate(state)
        self.assertEqual(first.batch(), resumed.batch())
        self.assertEqual(first.groups, original)

    def test_presented_scene_is_part_of_token_eligibility_cache(self):
        stream = self.make()
        row = fixture()[0]
        self.assertTrue(stream.eligible(row))
        self.assertFalse(stream.eligible(dict(row, scene='long ' * 600)))

    def test_exact_AdamW_and_rng_restore_on_CPU(self):
        try:
            import torch
        except ImportError:
            self.skipTest('real Torch CPU validation required on receiving host')
        model = torch.nn.Linear(2, 1)
        optimizer = torch.optim.AdamW(model.parameters(), lr=3e-5)
        for unused in range(3):
            optimizer.zero_grad()
            model(torch.ones(2)).sum().backward()
            optimizer.step()
        schedule = self.make()
        payload = dict(optimizer=copy.deepcopy(optimizer.state_dict()), completed_updates=3,
            global_pair_cursor=192, pair_proposals=195, pair_rng_state=schedule.schedule.getstate(),
            python_rng=random.getstate(), torch_rng=torch.get_rng_state(), cuda_rng=torch.zeros(8, dtype=torch.uint8))
        restored = torch.optim.AdamW(model.parameters(), lr=3e-5)
        with patch.object(torch.cuda, 'set_rng_state') as cuda:
            self.assertEqual(restore_optimizer_rng(model, restored, schedule, payload, 2, torch), 3)
        self.assertEqual(schedule.consumed, 192)
        self.assertEqual(schedule.proposed, 195)
        cuda.assert_called_once()
        self.assertTrue(torch.equal(torch.get_rng_state(), payload['torch_rng']))
        for before, after in zip(optimizer.state.values(), restored.state.values()):
            self.assertTrue(torch.equal(before['exp_avg'], after['exp_avg']))
            self.assertTrue(torch.equal(before['exp_avg_sq'], after['exp_avg_sq']))
        self.assertFalse(torch.cuda.is_initialized())


if __name__ == '__main__':
    unittest.main()
