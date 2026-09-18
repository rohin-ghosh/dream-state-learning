import unittest
import json
from pathlib import Path
import tempfile

from deadline_resume import boundary, deadline_plan, digest


class DeadlineTests(unittest.TestCase):
    def test_only_authorized_deadline_changes_not_policy(self):
        old = dict(hard_end_unix=100, lease_end_unix=200, root='/same/life',
            think_act_learn=dict(language_target_policy='same', decoder='same'), optimizer='same')
        result = deadline_plan(old, 'a' * 64, 1000, 22600)
        self.assertEqual(result['think_act_learn'], old['think_act_learn'])
        self.assertEqual(old['hard_end_unix'], 100)
        self.assertEqual(result['authorized_wall_extension']['previous_stream_sha256'], 'a' * 64)

    def test_wrong_margin_and_shorter_wall_rejected(self):
        old = dict(hard_end_unix=100, lease_end_unix=200)
        for wall, ceiling in ((99, 21699), (1000, 2000)):
            with self.assertRaises(ValueError):
                deadline_plan(old, 'a' * 64, wall, ceiling)


class BoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.records = self.root / 'stream/records'
        self.records.mkdir(parents=True)
        state = dict(pending=None, sleep_frontier=1, rows=[dict(own=True)])
        self.saved = dict(state=state, sha256=digest(state))

    def put(self, index, kind, document):
        row = dict(index=index, kind=kind, journal_id='same-journal', document=document)
        row['sha256'] = digest(row)
        (self.records / f'{index:020d}.json').write_text(json.dumps(row, sort_keys=True))

    def test_inbox_tail_keeps_current_complete(self):
        self.put(0, 'SLEEP_COMPLETE', dict(resume_state=self.saved))
        self.put(1, 'R184_LEARN_COMPLETE', {})
        self.put(2, 'INBOX', {})
        complete, saved, tail = boundary(self.root, 'same-journal')
        self.assertEqual(complete['index'], 0)
        self.assertEqual(saved, self.saved)
        self.assertEqual(len(tail), 2)

    def test_postboundary_request_prevents_exit_or_rollback(self):
        self.put(0, 'SLEEP_COMPLETE', dict(resume_state=self.saved))
        self.put(1, 'REQUEST', {})
        with self.assertRaisesRegex(ValueError, 'no_post_COMPLETE'):
            boundary(self.root, 'same-journal')

    def test_always_latest_complete_not_earlier(self):
        self.put(0, 'SLEEP_COMPLETE', dict(resume_state=self.saved))
        self.put(1, 'REQUEST', {})
        self.put(2, 'SLEEP_COMPLETE', dict(resume_state=self.saved))
        complete, unused_saved, unused_tail = boundary(self.root, 'same-journal')
        self.assertEqual(complete['index'], 2)


if __name__ == '__main__':
    unittest.main()
