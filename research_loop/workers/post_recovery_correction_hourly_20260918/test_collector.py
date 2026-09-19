import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import collector


class CollectorTests(unittest.TestCase):
    def test_hour_boundary_strictly_future(self):
        self.assertEqual(collector.next_hour(3600), 7200)
        self.assertEqual(collector.next_hour(7199.9), 7200)

    def test_unknown_is_not_zero(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(collector, 'HERE', Path(directory)):
            row = collector.one(dict(label='unknown'))
        self.assertIsNone(row['highest_verified_level'])
        self.assertFalse(row['native_identity_verified'])
        self.assertEqual(row['new_semantic_judgments'], 0)

    def test_expired_source_never_ssh(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(collector, 'HERE', Path(directory)), patch.object(collector, 'remote') as remote:
            row = collector.one(dict(label='expired', binding=dict(until_unix=0)))
        remote.assert_not_called()
        self.assertEqual(row['status'], 'SOURCE_HORIZON_ELAPSED_NO_REMOTE_READ')
        self.assertEqual(row['historical_reference_scope'], 'LOCAL_FROZEN_CACHE_ONLY')

    def test_changed_frozen_history_rejected(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(collector, 'HERE', Path(directory)):
            folder = Path(directory) / 'private/history/changed'
            folder.mkdir(parents=True)
            folder.joinpath('ANNOTATIONS.json').write_text('[]')
            folder.joinpath('PINS.json').write_text(json.dumps({'ANNOTATIONS.json': 'wrong'}))
            with self.assertRaisesRegex(ValueError, 'immutable_imported'):
                collector.history('changed')

    def test_source_changed_before_any_remote_read(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(collector, 'HERE', Path(directory)), patch.object(collector, 'remote') as remote:
            Path(directory, 'collector.py').write_text('changed')
            with self.assertRaisesRegex(ValueError, 'frozen_observer_source'):
                collector.run_once(dict(source_pins={'collector.py': 'wrong'}, entries=[]))
        remote.assert_not_called()

    def test_singleton_lock_excludes_second_descriptor(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'lock'
            with path.open('a') as first, path.open('r') as second:
                fcntl.flock(first, fcntl.LOCK_EX | fcntl.LOCK_NB)
                with self.assertRaises(BlockingIOError):
                    fcntl.flock(second, fcntl.LOCK_EX | fcntl.LOCK_NB)

    def test_loading_contract_does_not_shadow_existing_audit(self):
        code = "import sys,types; sentinel=types.ModuleType('audit'); sys.modules['audit']=sentinel; import collector; assert sys.modules['audit'] is sentinel"
        subprocess.run([sys.executable, '-B', '-c', code], cwd=collector.HERE, check=True)

    def test_wrong_remote_identity_rejected_before_journal(self):
        namespace = {}
        exec((collector.CONTRACT / 'reader.py').read_text() + '\n' + (collector.HERE / 'remote.py').read_text(), namespace)
        target = dict(pid=os.getpid(), start_ticks='-1', source='not-matching', guard_sha256='wrong')
        with self.assertRaisesRegex(ValueError, 'exact_source_process'):
            namespace['identity'](target)

    def test_wrong_loaded_rejected(self):
        namespace = {}
        exec((collector.CONTRACT / 'reader.py').read_text() + '\n' + (collector.HERE / 'remote.py').read_text(), namespace)
        namespace['identity'] = lambda target: {'pid': 9}
        namespace['verified'] = lambda *args: (dict(kind='LOADED', sha256='wrong', document={'pid': 9}), {})
        with self.assertRaisesRegex(ValueError, 'actual_current_LOAD'):
            namespace['inspect'](dict(until_unix=9999999999, root='/unused', loaded_index=4,
                journal_id='life', loaded_sha256='expected', pid=9), [])

    def test_fresh_outputs_do_not_promote_semantic_level(self):
        with patch.dict(sys.modules, {'audit': collector.audit}):
            fixtures = collector.load('isolated_original_fixture', collector.CONTRACT / 'test_audit.py')
        evidence, annotation = fixtures.fixture()
        evidence.update(head=dict(index=40), bytes_read=10)
        captured = dict(evidence=evidence, identity=dict(pid=9, start_ticks='10'))
        target = dict(until_unix=9999999999, owner_receipt_sha256='owner', journal_id='life', pid=9,
            start_ticks='10', source='/synthetic/source', root='/synthetic/life', guard_sha256='guard',
            loaded_index=1, loaded_sha256='loaded', boot_id='boot', source_manifest_sha256='manifest')
        with tempfile.TemporaryDirectory() as directory, patch.object(collector, 'HERE', Path(directory)), patch.object(collector, 'remote', return_value=captured):
            row = collector.one(dict(label='fresh', binding=target))
        self.assertEqual(row['status'], 'ACTUAL_BOUNDED_COLLECTION_COMPLETE')
        self.assertEqual(row['current_window']['actual_committed_ACTs'], 2)
        self.assertIsNone(row['highest_verified_level'])
        self.assertIsNone(row['current_window_semantic_level'])
        self.assertEqual(row['new_semantic_judgments'], 0)

    def test_historical_source_mismatch_rejected(self):
        namespace = {}
        exec((collector.CONTRACT / 'reader.py').read_text() + '\n' + (collector.HERE / 'remote.py').read_text(), namespace)
        namespace['identity'] = lambda target: {'pid': 9}
        def verified(path, journal):
            if int(path.stem) == 4:
                return dict(kind='LOADED', sha256='expected', document={'pid': 9}), {}
            return dict(kind='RESPONSE', sha256='changed'), {}
        namespace['verified'] = verified
        with self.assertRaisesRegex(ValueError, 'original_annotation_record_changed'):
            namespace['inspect'](dict(until_unix=9999999999, root='/unused', loaded_index=4,
                journal_id='life', loaded_sha256='expected', pid=9),
                [dict(index=3, kind='RESPONSE', sha256='original')])


if __name__ == '__main__':
    unittest.main()
