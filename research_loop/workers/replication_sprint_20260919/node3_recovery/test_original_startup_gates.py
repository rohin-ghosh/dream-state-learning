import importlib.util
import json
import os
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

from gpu.orch_r125_stream_journal import _digest
from organism_v6.orch_r124_train_history import WORKING_STATE_SCHEMA


HERE = Path(__file__).resolve().parent
WORKERS = HERE.parent.parent
REFERENCE = WORKERS / 'post_recovery_node2_caption_20260919' / 'prepared_v2' / 'source' / 'gpu'


def load_reference(name):
    specification = importlib.util.spec_from_file_location(name, REFERENCE / f'{name}.py')
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


class OriginalStartupGateTests(unittest.TestCase):
    def setUp(self):
        self.startup = load_reference('caption_tail_runtime')
        self.tail = load_reference('checkpoint_tail_runtime')

    def clean_journal(self):
        working = dict(schema=WORKING_STATE_SCHEMA, revision=0, entries=[])
        checkpoint = dict(checkpoint_sha256=dict(adapter='a', optimizer='b', rng='b'))
        saved = dict(state=dict(pending=None, deadline_unix=1790272800,
            history=dict(working_state=working), sleep_receipts=[{}],
            model_state_sha256=_digest(checkpoint['checkpoint_sha256'])))
        complete = dict(document=dict(resume_state=saved, cycle=1, checkpoint=checkpoint))
        learn = dict(document=dict(cycle=1, checkpoint=checkpoint, working_state=working,
            state_revision=0), kind='R184_LEARN_COMPLETE')
        state = dict(request=None, response=None, sleep_request=None,
            latest=dict(document=saved), index=12)
        journal = SimpleNamespace(_state=state, _records_fd=0,
            _read_json=lambda directory, name: complete if name == f'{10:020d}.json' else learn)
        return journal, dict(complete_index=10), saved

    def test_original_resolved_complete_gate_still_accepts_exact_boundary(self):
        journal, selection, unused = self.clean_journal()
        self.startup.verify_startup(journal, selection, 1790272800)

    def test_original_gate_rejects_pending_generation(self):
        journal, selection, unused = self.clean_journal()
        journal._state['request'] = dict(pending_generation=True)
        with self.assertRaisesRegex(ValueError, 'caption_exact_resolved_state_same_deadline'):
            self.startup.verify_startup(journal, selection, 1790272800)

    def test_original_gate_rejects_pending_sleep(self):
        journal, selection, unused = self.clean_journal()
        journal._state['sleep_request'] = dict(pending_sleep=True)
        with self.assertRaisesRegex(ValueError, 'caption_exact_resolved_state_same_deadline'):
            self.startup.verify_startup(journal, selection, 1790272800)

    def test_zero_byte_partial_is_not_silently_skipped(self):
        with tempfile.TemporaryDirectory(prefix='cpu-journal-', dir=HERE) as directory:
            root = Path(directory)
            records = root / 'records'
            records.mkdir()
            (records / f'{1:020d}.intent.json.partial').touch()
            manifest = dict(schema='R125_STREAM_JOURNAL_V1', journal_id='1' * 32)
            (root / 'JOURNAL.json').write_text(json.dumps(manifest))
            root_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
            records_fd = os.open(records, os.O_RDONLY | os.O_DIRECTORY)
            try:
                journal = SimpleNamespace(root=root, _manifest=manifest,
                    _root_fd=root_fd, _records_fd=records_fd, _ensure_open=lambda: None,
                    _read_json=lambda descriptor, name: manifest)
                selection = dict(policy=self.tail.POLICY, root=str(root),
                    journal_id=manifest['journal_id'], complete_index=0,
                    complete_sha256='2' * 64, life_id='test', max_tail_records=10,
                    max_tail_bytes=4096, persist_complete_anchors=False, sidecars=[])
                with self.assertRaisesRegex(ValueError, 'incomplete_or_unexpected_journal_tail'):
                    self.tail.scan(journal, selection)
            finally:
                os.close(root_fd)
                os.close(records_fd)


if __name__ == '__main__':
    unittest.main()
