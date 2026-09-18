import hashlib
import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parent


class PublicationReceiptTests(unittest.TestCase):
    def setUp(self):
        self.receipt = json.loads((ROOT / 'RECEIPTS.json').read_bytes())
        self.act = json.loads((ROOT / 'FIRST_FUTURE_ACT.json').read_bytes())

    def test_eight_actual_loaded_identities(self):
        arms = self.receipt['arms']
        self.assertEqual({arm['physical_gpu'] for arm in arms}, set(range(8)))
        self.assertEqual(len({arm['life'] for arm in arms}), 8)
        self.assertEqual(len({arm['LOADED']['native_pid'] for arm in arms}), 8)
        self.assertTrue(all(arm['LOADED']['currently_live'] for arm in arms))
        self.assertEqual((self.receipt['caption_live_loaded'], self.receipt['math_live_loaded']), (5, 3))
        self.assertTrue(all(re.fullmatch('[0-9a-f]{64}', arm['LOADED']['record_sha256']) for arm in arms))

    def test_completed_sleep_sources_masks_and_accounting(self):
        for arm in self.receipt['arms']:
            with self.subTest(gpu=arm['physical_gpu']):
                sleep = arm['latest_completed_sleep']
                document = sleep['SLEEP_COMPLETE']['document']
                self.assertEqual(document['status'], 'COMPLETE')
                self.assertGreater(sleep['SLEEP_COMPLETE']['index'], arm['LOADED']['index'])
                self.assertLess(sleep['SLEEP_REQUEST']['index'], sleep['SLEEP_RECIPE']['index'])
                self.assertLess(sleep['SLEEP_RECIPE']['index'], sleep['SLEEP_COMPLETE']['index'])
                self.assertTrue(sleep['all_candidates_source_bound'])
                self.assertTrue(sleep['candidate_order_matches_complete'])
                self.assertEqual(document['optimizer_steps'], sum(document['presentations'].values()))
                self.assertEqual(len(sleep['candidates']), sleep['SLEEP_RECIPE']['document']['new_rows'])
                for row in sleep['candidates']:
                    self.assertEqual((row['actor'], row['split']), ('child', 'TRAIN'))
                    self.assertFalse(row['prefix_loss'])
                    self.assertTrue(row['target_loss'])
                    self.assertTrue(row['response_raw_exact_match'])

    def test_caption_no_selectors_is_not_explicit_policy_adoption(self):
        captions = [arm for arm in self.receipt['arms'] if arm['role'].startswith('caption')]
        self.assertEqual(sum(len(arm['latest_completed_sleep']['candidates']) for arm in captions), 17)
        self.assertEqual(sum(arm['latest_completed_sleep']['SLEEP_COMPLETE']['document']['optimizer_steps']
            for arm in captions), 272)
        for arm in self.receipt['arms']:
            self.assertIsNone(arm['active_policy']['plan_learn_row_policy'])
            self.assertIsNone(arm['active_policy']['driver_learn_row_policy'])
            self.assertEqual(arm['default_scaffold_rule']['rejection_reasons'], ['journal_scaffolding_target'])
            self.assertTrue(arm['default_scaffold_rule']['synthetic_only'])
        for arm in captions:
            self.assertEqual(arm['active_policy']['plan_selectors'], {})
            self.assertEqual(arm['active_policy']['driver_selectors'], {})
            self.assertEqual(arm['latest_completed_sleep']['excluded_rows'], [])
            self.assertTrue(arm['latest_completed_sleep']['every_candidate_presented'])
        control = next(arm for arm in captions if arm['physical_gpu'] == 7)
        self.assertEqual(control['new_parent_message_count'], 0)

    def test_future_actual_act_not_cached_score_or_salvage(self):
        self.assertEqual((self.act['newly_evaluated_count'], self.act['cached_count'],
            self.act['accepted_count']), (3, 0, 0))
        self.assertEqual(self.act['origin']['record_index'], 113)
        self.assertEqual(self.act['ACT']['index'], 116)
        self.assertTrue(all(result['ok'] and result['replayed'] is False for result in self.act['results']))
        for source in self.act['caption_sources']:
            self.assertEqual(source['stage'], 'ACT')
            self.assertEqual(source['origin'], self.act['origin'])
            self.assertTrue(source['exact_source_span_sha256_verified'])
        self.assertFalse(self.act['historical_resubmission'])
        self.assertFalse(self.act['source_transport']['child_network_access'])

    def test_no_private_text_addresses_credentials_or_host_paths(self):
        forbidden_keys = {'target', 'text', 'prefix', 'token_ids', 'messages', 'prompt',
            'birth_prompt', 'environment_facts', 'adapter_path', 'optimizer_rng_path', 'source_life_root'}

        def inspect(value):
            if isinstance(value, dict):
                self.assertFalse(forbidden_keys.intersection(value))
                for child in value.values():
                    inspect(child)
            elif isinstance(value, list):
                for child in value:
                    inspect(child)

        inspect(self.receipt)
        inspect(self.act)
        for path in ROOT.iterdir():
            if path.suffix not in ('.json', '.md'):
                continue
            text = path.read_text()
            self.assertNotRegex(text, r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
            self.assertNotRegex(text, r'\bipp\d[-_][A-Za-z0-9_-]+')
            self.assertNotRegex(text, r'/localhome/|/data/home/|BEGIN [A-Z ]*PRIVATE KEY|ssh-rsa |Bearer ')
        self.assertLess((ROOT / 'RECEIPTS.json').stat().st_size, 131072)

    def test_manifest_matches_exact_published_files(self):
        manifest = json.loads((ROOT / 'MANIFEST.json').read_bytes())
        for filename, expected in manifest['files'].items():
            self.assertEqual(hashlib.sha256((ROOT / filename).read_bytes()).hexdigest(), expected)


if __name__ == '__main__':
    unittest.main()
