import importlib.util
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import Mock, patch


SPEC = importlib.util.spec_from_file_location('phase', Path(__file__).with_name('c2_math_bridge_phase.py'))
phase = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(phase)


OLD_SERVER = '''import os,socket,sys,time
server=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
server.bind(sys.argv[1]);server.listen(8)
while True:
 channel,address=server.accept()
 with channel:
  text=channel.recv(100)
  time.sleep(.25)
  channel.sendall(b'old:'+text)
'''


class BridgePhaseTests(unittest.TestCase):
    def test_previous_and_unknown_attempts_never_replayed(self):
        provider = Mock(side_effect=RuntimeError('unknown'))
        origin = dict(kind='TRAIN_CHILD_RESPONSE', record_index=5400, record_sha256='a' * 64)
        config = dict(raw_root='fixture', journal_id='fixture', gate_sha256='fixture', gate_root='fixture')
        seen = set()
        with self.assertRaises(RuntimeError):
            phase.dispatch(config, origin, seen, provider)
        with self.assertRaisesRegex(ValueError, 'never_redispatched'):
            phase.dispatch(config, origin, seen, provider)
        self.assertEqual(provider.call_count, 1)

    def test_historical_window_refused(self):
        provider = Mock()
        with self.assertRaisesRegex(ValueError, 'prospective'):
            phase.dispatch({}, dict(kind='TRAIN_CHILD_RESPONSE', record_index=5337, record_sha256='a'), set(), provider)
        provider.assert_not_called()

    def test_real_outcome_not_repaired(self):
        provider = Mock(return_value=dict(status='PUBLISHED', result_status='PROCESS_FAILED', result={'stderr': 'SyntaxError'}))
        config = dict(raw_root='fixture', journal_id='fixture', gate_sha256='fixture', gate_root='fixture')
        outcome = phase.dispatch(config, dict(kind='TRAIN_CHILD_RESPONSE', record_index=5400, record_sha256='a'), set(), provider)
        self.assertEqual(outcome, dict(status='PUBLISHED', result_status='PROCESS_FAILED'))

    def test_scope_refuses_frozen_copy(self):
        with self.assertRaisesRegex(ValueError, 'original_C2_only'):
            phase.preflight(dict(phase=phase.PHASE, raw_root='/frozen'))

    def test_exact_pid_identity_required(self):
        owner = phase.identity(os.getpid())
        owner['start'] += 1
        with self.assertRaisesRegex(ValueError, 'identity_changed'):
            phase.verify_identity(owner)

    def test_wrong_socket_inode_never_changes_route(self):
        with tempfile.TemporaryDirectory() as directory:
            endpoint = Path(directory) / 'live.sock'
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as original:
                original.bind(str(endpoint))
                before = endpoint.stat()
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as replacement:
                    with self.assertRaisesRegex(ValueError, 'original_socket_changed'):
                        phase.replace_listener(replacement, Path(directory) / 'next.sock', endpoint,
                                               (before.st_dev, before.st_ino + 1))
                self.assertEqual(endpoint.stat().st_ino, before.st_ino)

    def test_busy_cpu_lock_never_signals(self):
        with tempfile.TemporaryDirectory() as directory:
            lock = Path(directory) / 'OWNER.lock'
            lock.touch(mode=0o600)
            with patch.object(phase, 'listener_state', return_value=True), \
                    patch.object(phase.fcntl, 'flock', side_effect=BlockingIOError), \
                    patch.object(phase.os, 'pidfd_open') as pidfd:
                with self.assertRaises(BlockingIOError):
                    phase.drain_and_retire(phase.identity(os.getpid()), 1, lock, directory)
                pidfd.assert_not_called()

    def test_socket_swap_preserves_inflight_queued_and_next_request(self):
        with tempfile.TemporaryDirectory(prefix='c2-cutover-') as directory:
            root = Path(directory)
            endpoint, temporary = root / 'live.sock', root / 'next.sock'
            lock = root / 'OWNER.lock'
            lock.touch(mode=0o600)
            receipts = root / 'receipts'
            receipts.mkdir()
            old = subprocess.Popen([sys.executable, '-c', OLD_SERVER, str(endpoint)])
            channels = []
            try:
                deadline = time.monotonic() + 5
                while not endpoint.exists():
                    self.assertLess(time.monotonic(), deadline)
                    time.sleep(.01)
                owner = phase.identity(old.pid)
                socket_inode = int(next(os.readlink(path) for path in (Path('/proc') / str(old.pid) / 'fd').iterdir()
                                        if os.readlink(path).startswith('socket:'))[8:-1])
                initial = endpoint.stat()
                for text in (b'inflight', b'queued'):
                    channel = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                    channel.settimeout(5)
                    channel.connect(str(endpoint))
                    channel.sendall(text)
                    channels.append(channel)
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as replacement:
                    phase.replace_listener(replacement, temporary, endpoint, (initial.st_dev, initial.st_ino))
                    next_call = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                    next_call.settimeout(5)
                    channels.append(next_call)
                    next_call.connect(str(endpoint))
                    next_call.sendall(b'next')
                    phase.drain_and_retire(owner, socket_inode, lock, receipts, timeout=5)
                    self.assertEqual(channels[0].recv(100), b'old:inflight')
                    self.assertEqual(channels[1].recv(100), b'old:queued')
                    received, unused_address = replacement.accept()
                    with received:
                        self.assertEqual(received.recv(100), b'next')
                        received.sendall(b'new:next')
                    self.assertEqual(next_call.recv(100), b'new:next')
                    self.assertEqual(old.wait(timeout=2), -15)
                    self.assertEqual(len(list(receipts.glob('OLD_BRIDGE_EXITED*'))), 1)
            finally:
                for channel in channels:
                    channel.close()
                if old.poll() is None:
                    old.terminate()
                old.wait(timeout=3)


if __name__ == '__main__':
    unittest.main()
