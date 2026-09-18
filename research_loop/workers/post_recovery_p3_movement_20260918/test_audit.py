import copy
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('post_recovery_p3_movement_audit', HERE / 'audit.py')
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


class MovementCaptureTests(unittest.TestCase):
    def setUp(self):
        self.binding = dict(journal_id='same-journal', loaded_sha256='actual-load', loaded_index=10,
            source='/fixture/root/retry/source')
        self.prior = dict(journal_id='same-journal', loaded_sha256='actual-load',
            through=dict(index=11, sha256='eleven'), records=[dict(index=11)], caught_up=True)
        self.next_row = dict(index=12, sha256='twelve', previous_sha256='eleven', journal_id='same-journal')
        self.chunk = dict(journal_id='same-journal', continuity=[self.next_row],
            records=[dict(index=12)], head=self.next_row, through=self.next_row,
            coverage_start=12, bytes_read=100, observed_unix=1)

    def test_contiguous_append_preserves_input(self):
        prior, chunk = copy.deepcopy(self.prior), copy.deepcopy(self.chunk)
        result = audit.extend(self.prior, self.chunk, self.binding)
        self.assertEqual([11, 12], [row['index'] for row in result['records']])
        self.assertTrue(result['caught_up'])
        self.assertEqual(prior, self.prior)
        self.assertEqual(chunk, self.chunk)

    def test_refuses_journal_change(self):
        for target in ('prior', 'chunk', 'row'):
            with self.subTest(target=target):
                prior, chunk = copy.deepcopy(self.prior), copy.deepcopy(self.chunk)
                selected = prior if target == 'prior' else chunk if target == 'chunk' else chunk['continuity'][0]
                selected['journal_id'] = 'different-journal'
                with self.assertRaisesRegex(ValueError, 'same_original_journal'):
                    audit.extend(prior, chunk, self.binding)

    def test_refuses_wrong_actual_load(self):
        self.prior['loaded_sha256'] = 'old-failed-load'
        with self.assertRaisesRegex(ValueError, 'same_actual_LOAD'):
            audit.extend(self.prior, self.chunk, self.binding)

    def test_refuses_gap_and_wrong_previous_hash(self):
        for key, value in (('index', 13), ('previous_sha256', 'wrong')):
            with self.subTest(key=key):
                chunk = copy.deepcopy(self.chunk)
                chunk['continuity'][0][key] = value
                with self.assertRaisesRegex(ValueError, 'contiguous_authenticated'):
                    audit.extend(self.prior, chunk, self.binding)

    def test_empty_window_keeps_existing_head(self):
        self.chunk.update(continuity=[], records=[], head=self.prior['through'])
        result = audit.extend(self.prior, self.chunk, self.binding)
        self.assertTrue(result['caught_up'])
        self.assertEqual(self.prior['records'], result['records'])

    def test_partial_window_not_reported_caught_up(self):
        self.chunk['head'] = dict(index=13, sha256='thirteen')
        self.assertFalse(audit.extend(self.prior, self.chunk, self.binding)['caught_up'])

    def test_only_post_load_act_frames_maximum_ten(self):
        frames = [dict(stage='ACT', request=dict(index=index)) for index in range(1, 25)]
        frames.append(dict(stage='THINK', request=dict(index=25)))
        with patch.object(audit, 'load_module', return_value=SimpleNamespace(frames=lambda value: frames)):
            result = audit.selected_frames({}, 10)
        self.assertEqual(list(range(15, 25)), [frame['request']['index'] for frame in result])

    def test_capture_retains_input_digest_when_cache_is_baseline(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            cache = directory / 'EVIDENCE.private.json'
            cache.write_text(json.dumps(self.prior))
            original_sha = audit.sha(cache)
            (directory / 'P3_RETRY_BINDING.json').write_text(json.dumps(self.binding))
            (directory / 'reader.py').write_text('pass\n')
            result = SimpleNamespace(stdout=json.dumps(self.chunk))
            with patch.object(audit, 'HERE', directory), patch.object(audit, 'RECOVERY', directory), \
                    patch.object(audit, 'AUDIT', directory), patch.object(audit, 'selected_frames', return_value=[]), \
                    patch.object(audit.subprocess, 'run', return_value=result) as remote, patch('builtins.print'):
                audit.capture()
            public = json.loads((directory / 'CAPTURE.json').read_text())
            self.assertEqual(original_sha, public['baseline_cache_sha256'])
            self.assertNotEqual(original_sha, public['capture_sha256'])
            self.assertEqual(0, public['remote_writes'])
            self.assertEqual(0, public['publications'])
            self.assertEqual(['python3 -B -'], remote.call_args.args[0][-1:])
            self.assertIn('endpoint.configure()', remote.call_args.kwargs['input'])


if __name__ == '__main__':
    unittest.main()
