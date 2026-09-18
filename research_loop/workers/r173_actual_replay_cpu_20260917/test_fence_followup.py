"""Local fence regressions only; never reruns the consumed receiving candidate."""

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


OWNED = Path(__file__).resolve().parent
specification = importlib.util.spec_from_file_location('r173_fence_followup', OWNED / 'fence_followup.py')
followup = importlib.util.module_from_spec(specification)
specification.loader.exec_module(followup)


class CpuFenceFollowupTests(unittest.TestCase):
    def fence(self):
        return followup.CpuFixtureFence(Path('/candidate'), {})

    def test_exact_ancestor_directory_walk_allowed_not_regular_root_read(self):
        fence = self.fence()
        fence.audit('open', ('/', None, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC))
        self.assertFalse(fence.denied)
        with self.assertRaisesRegex(PermissionError, 'read_outside_candidate'):
            fence.audit('open', ('/', None, os.O_RDONLY))

    def test_directory_walk_is_not_permission_to_enumerate_ancestors(self):
        for event in ('os.listdir', 'os.scandir'):
            with self.subTest(event=event), self.assertRaises(PermissionError):
                self.fence().audit(event, ('/',))

    def test_null_sink_open_allowed_but_permission_changes_still_denied(self):
        fence = self.fence()
        fence.audit('open', ('/dev/null', 'r+b', os.O_RDWR))
        self.assertFalse(fence.denied)
        with self.assertRaises(PermissionError):
            fence.audit('os.chmod', ('/dev/null', 0o600, -1))
        with self.assertRaises(PermissionError):
            fence.audit('os.truncate', ('/dev/null', 0))

    def test_resolved_own_process_maps_allowed_not_foreign_pid_maps(self):
        fence = self.fence()
        fence.check_file(Path('/proc/self/maps').resolve(), False)
        foreign_pid = 1 if os.getpid() != 1 else 2
        with self.assertRaises(PermissionError):
            fence.check_file(Path('/proc') / str(foreign_pid) / 'maps', False)

    def test_no_life_or_evaluator_file_read_no_GPU_device_or_source_write(self):
        for filename, flags in [('/localhome/local-rohing/live/stream/record.json', os.O_RDONLY),
                                ('/localhome/local-rohing/evaluation/sealed.json', os.O_RDONLY),
                                ('/dev/nvidia0', os.O_RDONLY),
                                ('/candidate/source/gpu/code.py', os.O_WRONLY)]:
            with self.subTest(filename=filename), self.assertRaises(PermissionError):
                self.fence().audit('open', (filename, None, flags))

    def test_subprocess_network_and_signals_still_fail_closed(self):
        for event in ('subprocess.Popen', 'os.fork', 'os.kill', 'os.killpg', 'socket.connect'):
            fence = self.fence()
            with self.subTest(event=event), self.assertRaises(PermissionError):
                fence.audit(event, ())
            self.assertEqual(len(fence.denied), 1)

    def test_exact_frozen_replay_read_bound_and_null_probe_in_local_child(self):
        with tempfile.TemporaryDirectory() as directory:
            scratch = Path(directory).resolve()
            (scratch / 'tmp').mkdir()
            document = dict(scope='R173_LOCAL_FENCE_REGRESSION_NOT_RECEIVING_PROOF')
            raw = followup.attempted.encoded(document)
            bound = scratch / 'tmp/BOUND.json'
            bound.write_bytes(raw)
            helper = OWNED.parents[2] / 'gpu/orch_r168_targeted_replay.py'
            program = '''
import hashlib, importlib.util, json, pathlib
specification = importlib.util.spec_from_file_location('repair', __FOLLOWUP__)
repair = importlib.util.module_from_spec(specification)
specification.loader.exec_module(repair)
helper = pathlib.Path(__HELPER__)
assert hashlib.sha256(helper.read_bytes()).hexdigest() == repair.attempted.HELPERS['gpu/orch_r168_targeted_replay.py']
specification = importlib.util.spec_from_file_location('frozen_replay', helper)
replay = importlib.util.module_from_spec(specification)
specification.loader.exec_module(replay)
fence = repair.CpuFixtureFence(pathlib.Path(__SCRATCH__), {})
fence.install()
document = replay.read_bound(__REFERENCE__)
with open('/dev/null', 'r+b') as stream:
    assert stream.write(b'CPU_fixture_probe') == 17
    assert stream.read(1) == b''
with open('/proc/self/maps', 'rb') as stream:
    assert len(stream.read(32)) == 32
assert not fence.denied
print(json.dumps(dict(document=document, denied=fence.denied, candidate_rerun=False)))
'''
            for placeholder, value in {
                '__FOLLOWUP__': str(OWNED / 'fence_followup.py'), '__HELPER__': str(helper),
                '__SCRATCH__': str(scratch),
                '__REFERENCE__': dict(path=str(bound), sha256=followup.attempted.sha(raw)),
            }.items():
                program = program.replace(placeholder, repr(value))
            result = subprocess.run([sys.executable, '-I', '-B', '-c', program],
                                    capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            observation = json.loads(result.stdout)
            self.assertEqual(observation['document'], document)
            self.assertEqual(observation['denied'], [])
            self.assertFalse(observation['candidate_rerun'])


if __name__ == '__main__':
    unittest.main()
