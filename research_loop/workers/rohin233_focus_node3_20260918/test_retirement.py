import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import retirement


class RetirementTests(unittest.TestCase):
    def test_protected_and_obsolete_disjoint(self):
        self.assertFalse(set(retirement.PROTECTED) & set(retirement.OBSOLETE))

    def test_descendants_never_match_old_substrings(self):
        root = Path('/fixture')
        for name in retirement.PROTECTED:
            process = dict(args=['python', 'native', '--config', str(root / name / 'control/GUARD.json')], cwd='/')
            self.assertEqual(retirement.exact_lives(root, process), {name})

    def test_shared_root_or_text_not_identity(self):
        process = dict(args=['python', '--root', '/fixture', 'p32', 'note /fixture/lr3/raw'], cwd='/tmp')
        self.assertEqual(retirement.exact_lives(Path('/fixture'), process), set())

    def test_prefix_collision_rejected(self):
        process = dict(args=['/fixture/p32_extra/GUARD.json', '/fixture-other/p32/GUARD.json'], cwd='/')
        self.assertEqual(retirement.exact_lives(Path('/fixture'), process), set())

    def test_inaccessible_cwd_still_binds_exact_guard(self):
        process = dict(args=['python', 'native', '--config', '/fixture/r213_math_a/control/GUARD.json'], cwd='')
        self.assertEqual(retirement.exact_lives(Path('/fixture'), process), {'r213_math_a'})

    def test_native_not_timeout_or_systemd_wrapper(self):
        native = ['/venv/bin/python', '-B', '-m', 'gpu.runtime', 'native', '--config', 'GUARD.json']
        self.assertTrue(retirement.is_native(dict(args=native)))
        for wrapper in (['timeout', '5s'], ['sudo', 'systemd-run'], ['python', 'controller.py']):
            self.assertFalse(retirement.is_native(dict(args=wrapper + native)))

    def test_mixed_roots_and_protected_cannot_signal(self):
        for lives in (['p32', 'r213_math_a'], ['r213_math_a']):
            with patch('retirement.os.pidfd_open') as opened:
                with self.assertRaises(ValueError):
                    retirement.terminate(Path('/fixture'), dict(lives=lives), 'p32')
                opened.assert_not_called()

    def test_pid_reuse_refused(self):
        expected = dict(lives=['p32'], pid=1, start_ticks='10', command_sha256='original')
        current = dict(start_ticks='11', command_sha256='original', args=['/fixture/p32/GUARD.json'], cwd='/')
        with patch('retirement.os.pidfd_open', return_value=8), patch('retirement.os.close'), \
                patch('retirement.identity', return_value=current), patch('retirement.signal.pidfd_send_signal') as send:
            with self.assertRaises(ValueError):
                retirement.terminate(Path('/fixture'), expected, 'p32')
            send.assert_not_called()

    def test_coherent_checkpoint_and_modified_state(self):
        with tempfile.TemporaryDirectory() as directory:
            arm = Path(directory)
            checkpoint = arm / 'raw/checkpoints/sleep_000051'
            (checkpoint / 'adapter').mkdir(parents=True)
            (checkpoint / 'optimizer_rng.pt').write_bytes(b'synthetic optimizer and RNG')
            (checkpoint / 'adapter/model.bin').write_bytes(b'synthetic adapter')
            state_sha = retirement.sha(checkpoint / 'optimizer_rng.pt')
            data = dict(checkpoint_sha256=dict(adapter='a' * 64, optimizer=state_sha, rng=state_sha),
                adapter_files={'model.bin': retirement.sha(checkpoint / 'adapter/model.bin')})
            (checkpoint / 'COMMIT.json').write_text(json.dumps(data))
            self.assertTrue(retirement.verified_checkpoint(arm)['all_file_hashes_verified'])
            (checkpoint / 'optimizer_rng.pt').write_bytes(b'changed')
            self.assertIsNone(retirement.verified_checkpoint(arm))

    def test_record_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'record.json'
            payload = dict(document={}, index=1, kind='LOADED')
            payload['sha256'] = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
            path.write_text(json.dumps(payload))
            self.assertEqual(retirement.record(path)['index'], 1)
            payload['index'] = 2
            path.write_text(json.dumps(payload))
            with self.assertRaises(ValueError):
                retirement.record(path)


if __name__ == '__main__':
    unittest.main()
