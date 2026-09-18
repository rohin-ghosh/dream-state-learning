import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import p3_continued_observe as observer


class ContinuedObservationTests(unittest.TestCase):
    def test_dispatch_never_counts_as_loaded(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            control = root / 'control'
            records = root / 'life/stream/records'
            control.mkdir()
            records.mkdir(parents=True)
            complete = root / 'complete.json'
            complete.write_text(json.dumps(dict(index=9)))
            recovery = dict(journal_id='same', old_head_index=10,
                preserved_tail_record_count=1, complete_path=str(complete))
            (control / 'RECOVERY.json').write_text(json.dumps(recovery))
            (control / 'DISPATCHING.json').write_text('{}')
            with patch.object(observer, 'ROOT', root), patch.object(observer, 'CONTROL', control):
                evidence = observer.observe()
            self.assertEqual(evidence['status'], 'DISPATCHED_LOAD_PENDING')
            self.assertIsNone(evidence['actual_deadline_utc'])
            self.assertIsNone(evidence['binding'])


if __name__ == '__main__':
    unittest.main()
