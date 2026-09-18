"""Focused pre-GPU arithmetic, disjoint batches and assigned-minor checks."""

import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ddp_pilot import all_pair_target, measured_eta, partition, macro_spearman
from four_gpu_admission import command


class PilotTests(unittest.TestCase):
    def test_all_pairs_keep_small_gaps_low_votes_and_ties(self):
        left = dict(contest_id=1, caption_family_sha256='a', votes=2, mean=1.01)
        right = dict(contest_id=1, caption_family_sha256='b', votes=3, mean=1.0)
        self.assertEqual(all_pair_target(left, right)['winner'], 1)
        self.assertGreater(all_pair_target(left, right)['reliability'], 0)
        self.assertEqual(all_pair_target(dict(left, mean=1.0), right)['winner'], 0.5)

    def test_spearman_selects_mean_order_not_vote_mass_or_q(self):
        def ranks(values):
            return [sorted(values).index(value) + 1 for value in values]
        self.assertEqual(macro_spearman([(1, 1, 1), (1, 2, 2), (1, 3, 3)], ranks), 1)
        self.assertEqual(macro_spearman([(1, 1, 3), (1, 2, 2), (1, 3, 1)], ranks), -1)

    def test_disjoint_rank_batches_reconstruct_global_batch(self):
        batch = list(range(64))
        self.assertEqual([item for rank in range(4) for item in partition(batch, rank)], batch)

    def test_partial_or_fifth_rank_fails(self):
        with self.assertRaises(ValueError):
            partition(list(range(63)), 0)
        with self.assertRaises(ValueError):
            partition(list(range(64)), 4)

    def test_eta_requires_actual_five_minutes(self):
        with self.assertRaises(ValueError):
            measured_eta(64, 299, 1000)
        receipt = measured_eta(9600, 300, 1000)
        self.assertEqual(receipt['aggregate_pairs_per_second'], 32)
        self.assertEqual(receipt['fitting_remaining_seconds'], 990400 / 32)
        self.assertIsNone(receipt['selection_additional_seconds'])

    def test_only_assigned_devices_are_allowed(self):
        config = dict(unit_prefix='test-', physical=[0, 1, 2, 3], uid=2524, gid=2524, device_uuids=['GPU-a', 'GPU-b', 'GPU-c', 'GPU-d'], python='/python')
        arguments = command(Path('/private'), config)
        self.assertTrue(all('--property=DeviceAllow=/dev/nvidia' + str(minor) + ' rw' in arguments for minor in range(4)))
        self.assertTrue(all('--property=DeviceAllow=/dev/nvidia' + str(minor) + ' rw' not in arguments for minor in range(4, 8)))
        self.assertIn('--nproc-per-node=4', arguments)
        self.assertIn('CUDA_VISIBLE_DEVICES=GPU-a,GPU-b,GPU-c,GPU-d', arguments)
        self.assertIn('NCCL_P2P_DISABLE=1', arguments)
        self.assertIn('NCCL_CUMEM_HOST_ENABLE=0', arguments)
        self.assertIn('NCCL_SOCKET_IFNAME=lo', arguments)


if __name__ == '__main__':
    unittest.main()
