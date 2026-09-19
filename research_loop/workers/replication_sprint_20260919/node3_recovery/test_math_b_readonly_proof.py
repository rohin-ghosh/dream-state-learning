import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

import math_b_readonly_proof as proof


class ReadOnlyProofTests(unittest.TestCase):
    def test_compute_presence_stops_before_journal_open(self):
        with self.assertRaisesRegex(ValueError, 'native_present'):
            proof.assert_no_compute(SimpleNamespace(returncode=0, stdout='123, GPU-device, python'))

    def test_failed_census_is_not_idle(self):
        with self.assertRaisesRegex(ValueError, 'census_must_succeed'):
            proof.assert_no_compute(SimpleNamespace(returncode=1, stdout=''))

    def test_empty_successful_census_is_idle(self):
        proof.assert_no_compute(SimpleNamespace(returncode=0, stdout='\n'))

    def test_readonly_wrapper_rejects_both_write_routes(self):
        journal = proof.readonly_class(object)()
        with self.assertRaisesRegex(ValueError, 'no_publication'):
            journal._publish(None, 'bad', {})
        with self.assertRaisesRegex(ValueError, 'no_record'):
            journal.record('BAD', {})

    def test_host_read_preserves_guest_path_validation(self):
        class BaseJournal:
            def __init__(self):
                self.root = Path('/host/raw/stream')
                self.inbox = self.root / 'inbox'

            def _scan(self):
                return self.inbox

        logical_inbox = Path('/original/guest/life/stream/inbox')
        journal = proof.readonly_class(BaseJournal, logical_inbox)()
        self.assertEqual(journal._scan(), logical_inbox)
        self.assertEqual(journal.root, Path('/host/raw/stream'))

    def test_default_mapping_never_changes_inbox(self):
        class BaseJournal:
            inbox = Path('/unchanged/inbox')

            def _scan(self):
                return self.inbox

        self.assertEqual(proof.readonly_class(BaseJournal)()._scan(), Path('/unchanged/inbox'))

    def test_unknown_source_is_not_ignored(self):
        with TemporaryDirectory() as root:
            source = Path(root).resolve()
            digest = lambda document: hashlib.sha256(json.dumps(document, sort_keys=True).encode()).hexdigest()
            expected = dict(source_pins={}, source_pins_sha256=digest({}))
            proof.verify_pins(source, expected, digest)
            (source / 'extra.py').write_text('pass\n')
            with self.assertRaisesRegex(ValueError, 'exact_source_closure'):
                proof.verify_pins(source, expected, digest)


if __name__ == '__main__':
    unittest.main()
