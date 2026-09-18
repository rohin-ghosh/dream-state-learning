import hashlib
import json
from pathlib import Path
import unittest


DIRECTORY = Path(__file__).resolve().parent


class ActualReceiptTests(unittest.TestCase):
    def setUp(self):
        self.observation = json.loads((DIRECTORY / 'OBSERVATION.json').read_bytes())
        self.expected = json.loads((DIRECTORY.parent /
            'candidate5_initial3_templates/INITIALIZER_METADATA_VERIFIED.json').read_bytes())

    def test_exact_initial_identity_without_payload_read(self):
        for arm, details in self.observation['arms'].items():
            metadata = details['initial_metadata']
            self.assertEqual(metadata['optimizer_steps'], 0)
            self.assertEqual(metadata['adapter_files'], self.expected['initial_adapter_files'])
            self.assertEqual(metadata['adapter_state_sha256'], self.expected['initial_adapter_state_sha256'])
            self.assertEqual(metadata['checkpoint_sha256'], self.expected['initial_checkpoint_sha256'])
            self.assertEqual(metadata['created_unix'], self.expected['initial_created_unix'])
            raw = (DIRECTORY / f'{arm}.initial.COMMIT.original.json').read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), details['initial_commit']['sha256'])

    def test_prospective_event_bounds_and_unasserted_coverage(self):
        freeze = 1789620776.0605557
        for details in self.observation['arms'].values():
            journal = details['journal']
            self.assertEqual(journal['status'], 'VERIFIED_RETAINED_PREFIX')
            self.assertTrue(journal['listing_stable'])
            self.assertTrue(journal['all_intents_paired'])
            self.assertFalse(details['coverage_complete'])
            self.assertFalse(journal['coverage_complete'])
            self.assertLess(freeze, details['initial_state_verified']['metadata']['observed_unix'])
            self.assertLess(freeze, journal['first_train_request']['started_unix'])
            self.assertLess(journal['first_train_request']['started_unix'], journal['first_train_response']['finished_unix'])
            self.assertLess(journal['first_train_response']['finished_unix'], self.observation['started_unix'])

    def test_authority_and_limits(self):
        self.assertEqual(self.observation['hostname'], '[REDACTED_HOST]')
        self.assertLess(self.observation['observed_unix'], self.observation['authority_read_end_unix'])
        self.assertLess(self.observation['bytes_read'], 256 * 1024 * 1024)
        self.assertLess(self.observation['returned_metadata_bytes'], 16 * 1024 * 1024)
        for name in ('source_written', 'adapter_payload_read', 'optimizer_rng_payload_read',
                     'held_contents_read', 'enrollment'):
            self.assertIs(self.observation[name], False)
        self.assertEqual(self.observation['gpu_calls'], 0)


if __name__ == '__main__':
    unittest.main()
