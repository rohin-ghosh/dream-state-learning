"""Synthetic terminal-summary tests; not native scientific results."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from gpu import orch_terse_breadth_watch as watch


class WatchTests(unittest.TestCase):
    def fixture(self, root):
        for host, unused_wrapper, lanes in watch.HOSTS:
            for lane in lanes:
                seed, dose = ((7801, 4), (7802, 4), (7801, 16))[lane // 2]
                for phase in ('train', 'after') + (('baseline',) if lane == 0 else ()):
                    directory = root / f'terminal_{host}' / f'{phase}{lane}'
                    directory.mkdir(parents=True)
                    state = f'state{lane}'
                    data = dict(status='COMPLETE', batch_sha256='batch', seed=seed, trajectory_presentations=dose,
                        frozen_base_unchanged=True, pid=lane + (10 if phase == 'train' else 100),
                        adapter_state_after=state, loaded_adapter_state_sha256=state,
                        row_presentations=[dose], reference_supervised_tokens=80 * dose)
                    if phase != 'train':
                        score = 1 if phase == 'baseline' or lane % 2 else 60
                        data['summary'] = dict(primary=dict(correct=score, goals=2 * score), checks=dict(every_world=True),
                            engineering_target_met=True, deterministic_first_port=[dict(summary=dict(paired=dict(correct=0)))])
                    (directory / 'RESULT.json').write_text(json.dumps(data))

    def test_two_seeds_and_dose_report_not_promotion(self):
        with TemporaryDirectory() as temporary, patch.object(watch, 'LOCAL', Path(temporary)):
            self.fixture(Path(temporary))
            report = watch.reduce_terminal({})
            self.assertEqual(report['conclusion'], 'TWO_SEED_FOUR_DOSE_SURVIVAL_AUTHOR_ONLY')
            self.assertEqual([(pair['seed'], pair['dose']) for pair in report['pairs']], [(7801, 4), (7802, 4), (7801, 16)])
            self.assertFalse(report['promotion'])
            self.assertFalse(report['reader_verified'])
            self.assertEqual(report['old266_gate'], 'FAIL_UNCHANGED')

    def test_one_world_failure_blocks_conjunction(self):
        with TemporaryDirectory() as temporary, patch.object(watch, 'LOCAL', Path(temporary)):
            root = Path(temporary)
            self.fixture(root)
            path = root / 'terminal_a100/after2/RESULT.json'
            data = json.loads(path.read_text())
            data['summary']['engineering_target_met'] = False
            data['summary']['checks']['every_world'] = False
            path.write_text(json.dumps(data))
            report = watch.reduce_terminal({})
            self.assertEqual(report['conclusion'], 'FOUR_DOSE_BREADTH_CONJUNCTION_NOT_REPLICATED')
            self.assertEqual(len(report['pairs']), 3)

    def test_missing_artifact_is_not_clean_null(self):
        with TemporaryDirectory() as temporary, patch.object(watch, 'LOCAL', Path(temporary)):
            self.fixture(Path(temporary))
            path = Path(temporary) / 'terminal_node3/after5/RESULT.json'
            path.rename(path.with_name('PRESERVED_RESULT.json'))
            report = watch.reduce_terminal({})
            self.assertEqual(report['conclusion'], 'INCOMPLETE_NATIVE_EVIDENCE')
            self.assertTrue(report['failures'])
            self.assertNotIn('pairs', report)


if __name__ == '__main__':
    unittest.main()
