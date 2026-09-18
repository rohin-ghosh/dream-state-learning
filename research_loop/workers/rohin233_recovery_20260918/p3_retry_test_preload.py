import copy
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import sys
import tempfile
import time
import types
import unittest
from unittest.mock import patch

import p3_retry_observe as observer
import p3_retry_preload_endpoint as endpoint
from p3_retry_preload_endpoint import validate_preload


class PreloadGuardTests(unittest.TestCase):
    def setUp(self):
        self.actual = dict(pid=699464, start_ticks='33078516', source=str(observer.SOURCE),
            guard_argument_present=True, state='R')
        self.head = dict(index=5315, sha256='head', kind='R233_P3_RECOVERED_BOUNDARY', journal_id=observer.JOURNAL_ID)
        self.appended = dict(index=5315, sha256='head')
        self.recovery = dict(old_head_index=5314)

    def test_exact_preload_native_and_preserved_head_accepted(self):
        validate_preload(self.actual, self.head, self.appended, self.recovery)

    def test_old_or_reused_pid_source_and_guard_rejected(self):
        for key, value in (('pid', 598987), ('start_ticks', 'old'), ('source', '/wrong'),
                ('guard_argument_present', False), ('state', 'Z')):
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_preload(dict(self.actual, **{key: value}), self.head, self.appended, self.recovery)

    def test_LOAD_or_changed_head_never_called_preload(self):
        for key, value in (('kind', 'LOADED'), ('index', 5316), ('sha256', 'other'), ('journal_id', 'other')):
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_preload(self.actual, dict(self.head, **{key: value}), self.appended, self.recovery)

    def test_guard_does_not_mutate_inputs(self):
        before = copy.deepcopy((self.actual, self.head, self.appended, self.recovery))
        validate_preload(self.actual, self.head, self.appended, self.recovery)
        self.assertEqual(before, (self.actual, self.head, self.appended, self.recovery))

    def test_dead_native_rejected(self):
        with self.assertRaises(ValueError):
            validate_preload(None, self.head, self.appended, self.recovery)

    def test_read_resume_cannot_duplicate_a_provider_attempt(self):
        source = Path(__file__).with_name('p3_retry_preload_parent.py').read_text()
        self.assertIn("not (HERE / 'P3_RETRY_PRELOAD_SOURCE.json').exists()", source)
        self.assertIn("not (HERE / 'P3_RETRY_PRELOAD_RESULT.json').exists()", source)
        self.assertIn('range(64)', source)
        self.assertIn("time.time() < deadline, 'bounded_preload_snapshot_deadline'", source)

    def test_same_console_API_one_publication_and_no_automatic_retry(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'r210').mkdir()
            (root / 'cpu').mkdir()
            authority = {'exact': 'authenticated'}
            request = dict(mode=endpoint.MODE, physical=3, op='publish',
                deadline_unix=time.time() + 120, authority=authority, message='Astra: One prompt.')
            calls = []

            def publish(*arguments):
                calls.append(arguments)
                return dict(id='inbox', sha256='checksum')

            console = types.ModuleType('gpu.orch_r127_pilot_console')
            console.publish_parent = publish
            with patch.object(observer, 'ROOT', root), patch.object(observer, 'CPU', root / 'cpu'), \
                    patch.object(endpoint, 'verified', return_value=(None, authority)), \
                    patch.dict(sys.modules, {'gpu.orch_r127_pilot_console': console}):
                with patch('sys.stdin', io.StringIO(json.dumps(request))), redirect_stdout(io.StringIO()):
                    endpoint.main()
                self.assertEqual(calls, [(str(root / 'life'), 'Astra', request['message'])])
                receipt = observer.read(root / 'cpu/P3_RETRY_PRELOAD_PUBLISHED.json')
                self.assertTrue(receipt['queued_not_rendered'])
                with patch('sys.stdin', io.StringIO(json.dumps(request))), self.assertRaises(ValueError):
                    endpoint.main()
                self.assertEqual(len(calls), 1)

    def test_changed_identity_inside_lock_does_not_publish(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'r210').mkdir()
            authority = {'exact': 'before'}
            request = dict(mode=endpoint.MODE, physical=3, op='publish',
                deadline_unix=time.time() + 120, authority=authority, message='Astra: One prompt.')
            with patch.object(observer, 'ROOT', root), \
                    patch.object(endpoint, 'verified', side_effect=[(None, authority), (None, {'exact': 'changed'})]), \
                    patch('sys.stdin', io.StringIO(json.dumps(request))), self.assertRaises(ValueError):
                endpoint.main()
            self.assertFalse((root / 'r210/P3_RETRY_PRELOAD_PUBLISH_ATTEMPT.json').exists())


if __name__ == '__main__':
    unittest.main()
