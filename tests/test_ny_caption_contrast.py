import json
from pathlib import Path
import tempfile
import unittest

from gpu.ny_caption_contrast import TYPES, choose_contests, make_cases, summarize
from gpu import ny_caption_data as data
from gpu.ny_caption_scalar_judge import MODEL_ID, REVISION, export_runtime, read_config, relative_position


class ContrastTests(unittest.TestCase):
    def rows(self):
        return [dict(contest_id=contest, scene='An empty room.', scene_group_sha256=contest,
                     caption=f'These are synthetic words number {rank} in {contest}', published_rank=rank)
                for contest in ('alpha', 'beta') for rank in range(1, 31)]

    def test_reproducible_all_contrasts_no_raw_ids_in_public_identity(self):
        cases = make_cases(self.rows())
        self.assertEqual(cases, make_cases(self.rows()))
        self.assertEqual(len(cases), 60)
        self.assertEqual({row['kind'] for row in cases}, set(TYPES))
        self.assertTrue(all(row['contest'] not in ('alpha', 'beta') for row in cases))
        self.assertTrue(all(row['contrast_published_rank'] > row['good_published_rank']
                            for row in cases if row['kind'] == 'mid_tier'))

    def test_whole_groups_and_no_training_contests(self):
        manifest = dict(pools=dict(judge_dev=['a', 'b', 'c', 'd'], judge_train=['fit']),
                        scene_groups=[['a', 'b'], ['c', 'd'], ['fit']])
        self.assertIn(set(choose_contests(manifest, 2, 207)), ({'a', 'b'}, {'c', 'd'}))
        self.assertEqual(set(choose_contests(manifest, 2, 207, ['c', 'd'])), {'c', 'd'})
        with self.assertRaises(ValueError):
            choose_contests(manifest, 2, 207, ['fit'])
        manifest['pools']['judge_train'].append('a')
        with self.assertRaises(ValueError):
            choose_contests(manifest, 2, 207)

    def test_keeps_ties_failures_and_unscored_opportunities(self):
        records = [dict(contest='anonymous', kind='nonsense', status='SCORED', good_score=score,
                        contrast_score=1) for score in (2, 1, 0)]
        records.append(dict(contest='anonymous', kind='nonsense', status='SKIPPED_OVERLENGTH'))
        report = summarize(records)['by_type']['nonsense']
        self.assertEqual((report['opportunities'], report['wins'], report['ties'], report['losses']), (4, 1, 1, 1))
        self.assertEqual(report['tie_half_accuracy'], 0.5)
        self.assertEqual(report['skipped'], 1)

    def test_relative_rank_is_not_probability_and_ties_do_not_pass(self):
        result = relative_position(-1, [-4, -3, -2], 1)
        self.assertTrue(result['accepted'])
        self.assertEqual(result['raw_score'], -1)
        self.assertNotIn('q', result)
        self.assertFalse(relative_position(-2, [-4, -3, -2], 1)['accepted'])

    def test_same_scene_cross_contest_is_not_negative(self):
        rows = self.rows()
        for row in rows:
            row['scene_group_sha256'] = 'shared'
        with self.assertRaises(ValueError):
            make_cases(rows)

    def test_scalar_export_no_tau_or_private_panel_dependency(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            adapter = root / 'original'
            adapter.mkdir()
            references = {name: data.private_write(adapter / name, content) for name, content in
                          (('adapter_config.json', b'{}'), ('adapter_model.safetensors', b'synthetic-test-only'))}
            base = data.private_write(root / 'base.json', dict(model_id=MODEL_ID, revision=REVISION, root=str(root)))
            source = data.private_write(root / 'judge.json', dict(schema='NY_BT_SCALAR_JUDGE_CONFIG_V1',
                base_model=base, adapter=references, selected_adapter_root=str(adapter),
                config=dict(max_length=512), tau=dict(threshold=None), private_panel='must-not-export'))
            exported = export_runtime(source['path'], root / 'export')
            config, _, _ = read_config(exported['path'])
            self.assertNotIn('private_panel', json.dumps(config))
            self.assertNotIn('tau', config)
            self.assertFalse(config['tau_required'])
            (Path(config['selected_adapter_root']) / 'adapter_model.safetensors').write_bytes(b'changed')
            with self.assertRaises(ValueError):
                read_config(exported['path'])


if __name__ == '__main__':
    unittest.main()
