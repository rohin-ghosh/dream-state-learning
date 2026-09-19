import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

from prepare_epoch4 import CHANGES, HERE, LIVES, PEER_PINS, peer_bytes, prepare
from prefix_ports import proposed


class Epoch4PreparationTests(unittest.TestCase):
    def test_exact_sealed_both_arm_closure_delta_and_preserved_deadline(self):
        peer = peer_bytes()
        for life in LIVES:
            old = HERE / 'prepared_epoch3_v1' / life / 'epoch3'
            epoch = HERE / 'prepared_epoch4_v1' / life / 'epoch4'
            receipt = json.loads((epoch / 'EPOCH4_SOURCE.json').read_bytes())
            ports, changes = proposed(old / 'source', peer['checkpoint_tail_runtime.candidate.py'], peer['immutable_prefix_proof.py'])
            self.assertEqual(set(changes), CHANGES)
            self.assertEqual(changes, receipt['epoch3_to_epoch4_delta'])
            actual = {str(path.relative_to(epoch / 'source')): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in (epoch / 'source').rglob('*.py')}
            self.assertEqual(len(actual), 211)
            self.assertEqual(actual, receipt['new_source_pins'])
            for name, content in ports.items():
                self.assertEqual((epoch / 'source' / name).read_bytes(), content)
            self.assertEqual(receipt['deadline_unix'], 1790791200)
            self.assertFalse(receipt['actual_namespace_route_tested'])
            self.assertFalse(receipt['admission_granted'])
            self.assertFalse(any(path.stat().st_mode & 0o222 for path in (epoch / 'source').rglob('*')))

    def test_only_canonical_v4_ABI_and_original_native_validation(self):
        source = HERE / 'prepared_epoch4_v1/curriculum_learner/epoch4/source'
        runtime = (source / 'gpu/pair_retention_runtime.py').read_text()
        self.assertIn('prefix_admission=prefix_admission', runtime)
        self.assertNotIn('NamespaceAdmission', runtime)
        self.assertNotIn('original_admission=', runtime)
        native = (source / 'gpu/r205_runtime.py').read_text()
        self.assertLess(native.index('config, plan = guard.validate(args.config)'), native.index('with admitted_prefix('))
        self.assertIn('fresh_privileged_admission', native)
        self.assertEqual(hashlib.sha256((source / 'gpu/immutable_prefix_proof.py').read_bytes()).hexdigest(),
            PEER_PINS['immutable_prefix_proof.py'])

    def test_preserved_epoch_or_outside_scope_output_refuses(self):
        for output in (HERE / 'prepared_epoch4_v1', HERE / 'prepared_epoch3_v1', Path('/tmp/forbidden-epoch4')):
            with self.assertRaisesRegex(ValueError, 'new_local_worker_epoch4_output_only'):
                prepare(output)

    def test_node_CPU_helper_is_standalone_without_repo_on_pythonpath(self):
        source = HERE / 'prepared_epoch4_v1/curriculum_learner/epoch4/source'
        for filename in ('cpu_probe_prefix.py', 'prefix_source_checks.py'):
            result = subprocess.run([sys.executable, '-B', str(HERE / filename), '--help'], cwd='/tmp',
                env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES='', PYTHONPATH=str(source)),
                capture_output=True, text=True, timeout=10, close_fds=True)
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
