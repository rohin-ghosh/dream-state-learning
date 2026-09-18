import copy
import json
from pathlib import Path
import unittest

from direct_baseline import bind_draft, require_unpublished_results
from fallback_drafts_v1 import DRAFTS


HERE = Path(__file__).resolve().parent


class DirectBaselineTests(unittest.TestCase):
    def test_five_exact_actual_committed_sources(self):
        for physical, draft in DRAFTS.items():
            with self.subTest(physical=physical):
                directory = HERE / draft['source']
                receipt = json.loads((directory / 'RECEIPT.json').read_text())
                source = json.loads((directory / 'SOURCE.json').read_text())
                self.assertEqual(bind_draft(physical, receipt, source, draft)['record_index'], draft['record_index'])

    def test_never_control_or_already_published_replay(self):
        for physical in (0, 1, 2, 8):
            with self.subTest(physical=physical), self.assertRaisesRegex(ValueError, 'learning_lives'):
                bind_draft(physical, {}, {}, {})

    def test_known_prepublication_and_no_attempt_allowed(self):
        require_unpublished_results([])
        require_unpublished_results([dict(status='MISSING', error_type='HTTPError')])

    def test_published_or_inflight_refused(self):
        for status in ('PUBLISHED', 'IN_FLIGHT', None):
            with self.subTest(status=status), self.assertRaisesRegex(ValueError, 'successful_publication'):
                require_unpublished_results([dict(status=status)])

    def test_ambiguous_even_when_missing_refused(self):
        for field in ('sent_unix', 'inbox_publication', 'publication'):
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'uncertain_publication'):
                require_unpublished_results([dict(status='MISSING', **{field: None})])

    def test_changed_source_refused(self):
        draft = DRAFTS[3]
        directory = HERE / draft['source']
        receipt = json.loads((directory / 'RECEIPT.json').read_text())
        source = json.loads((directory / 'SOURCE.json').read_text())
        source['response_count'] += 1
        with self.assertRaisesRegex(ValueError, 'source_serialization'):
            bind_draft(3, receipt, source, draft)

    def test_invented_object_and_oversized_text_refused(self):
        draft = DRAFTS[3]
        directory = HERE / draft['source']
        receipt = json.loads((directory / 'RECEIPT.json').read_text())
        source = json.loads((directory / 'SOURCE.json').read_text())
        with self.assertRaisesRegex(ValueError, 'object_anchor'):
            bind_draft(3, receipt, source, dict(draft, anchor='NONEXISTENT_CPU_FIXTURE'))
        with self.assertRaisesRegex(ValueError, 'own_prose'):
            bind_draft(3, receipt, source, dict(draft, message=' '.join(['word'] * 91)))


if __name__ == '__main__':
    unittest.main(verbosity=2)
