"""Post-action CPU regression: synthetic secrets, no real provider calls or GPU starts."""

import ast
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from research_loop.workers.rohin179_credentials_20260917 import credentials, resume_helpers


class CredentialsTests(unittest.TestCase):
    def setUp(self):
        scratch = credentials.ROOT / 'cpu_scratch'
        scratch.mkdir(exist_ok=True)
        temporary = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def test_current_key_parse_stays_private_and_does_not_execute_shell(self):
        source = self.root / 'fixture.env'
        source.write_text("export NVIDIA_API_KEY='synthetic-private-value-not-a-real-key'\n")
        self.assertEqual(credentials.current_key(source), b'synthetic-private-value-not-a-real-key')

    def test_ambiguous_key_source_fails_without_echoing_input(self):
        source = self.root / 'fixture.env'
        source.write_text('NVIDIA_API_KEY=synthetic-one\nNVIDIA_API_KEY=synthetic-two\n')
        with self.assertRaisesRegex(ValueError, '^PRIVATE_CURRENT_CREDENTIAL_MISSING_OR_AMBIGUOUS$'):
            credentials.current_key(source)

    def test_symlinked_private_source_rejected(self):
        source = self.root / 'fixture.env'
        source.write_text('NVIDIA_API_KEY=synthetic-one\n')
        link = self.root / 'link.env'
        link.symlink_to(source)
        with self.assertRaises(OSError):
            credentials.current_key(link)

    def fixture_status(self, arguments, value, current):
        identity = dict(pid=123, uid=456, start_ticks='789', ppid=1, state='S')
        with patch.object(credentials, 'identity', return_value=identity), \
             patch.object(credentials, 'private_arguments', return_value=arguments), \
             patch.object(credentials, 'private_environment', return_value={credentials.KEY_NAME: value}):
            return credentials.status(123, current)

    def test_public_status_has_booleans_not_keys_or_environment(self):
        previous = b'synthetic-previous-private-key'
        current = b'synthetic-current-private-key'
        result = self.fixture_status(['python3', '-m', 'gpu.orch_r153_community_service',
            '--config', '/tmp/config.json', '--api-key', previous.decode()], previous, current)
        self.assertFalse(result['key_is_current'])
        self.assertNotIn(previous.decode(), json.dumps(result))
        self.assertNotIn(current.decode(), json.dumps(result))
        self.assertEqual(result['config_paths'], [dict(option='--config', path='/tmp/config.json')])

    def test_credential_bearing_configuration_path_is_redacted(self):
        key = b'synthetic-private-key'
        result = self.fixture_status(['python3', '--config', '/tmp/synthetic-private-key.json'], key, key)
        self.assertTrue(result['key_is_current'])
        self.assertEqual(result['config_paths'], [])
        self.assertNotIn(key.decode(), json.dumps(result))

    def test_learner_is_not_a_restart_target(self):
        result = self.fixture_status(['python3', '-m', 'gpu.orch_r125_continual_native'],
                                     b'synthetic-old-key', b'synthetic-current-key')
        self.assertFalse(result['restart_target'])

    def test_receipts_cannot_overwrite_prior_evidence(self):
        path = self.root / 'receipt.json'
        credentials.write_once(path, dict(key_is_current=True))
        self.assertEqual(path.stat().st_mode & 0o777, 0o400)
        with self.assertRaises(FileExistsError):
            credentials.write_once(path, dict(key_is_current=False))

    def function_source(self, path, name):
        text = Path(path).read_text()
        function = next(node for node in ast.parse(text).body if isinstance(node, ast.FunctionDef) and node.name == name)
        return ast.get_source_segment(text, function)

    def test_math_resume_preserves_job_loop_and_old_READY(self):
        source = self.function_source('gpu/orch_math_feedback_uptake_r122_broker.py', 'serve')
        revised = resume_helpers.math_source(source)
        self.assertEqual(source[source.index('        while time.time()'):],
                         revised[revised.index('        while time.time()'):])
        self.assertIn("test -d ", revised)
        self.assertNotIn("shared.write(service / 'READY.json'", revised)
        self.assertNotIn("copy(service / 'READY.json'", revised)
        compile(revised, 'math-resume-cpu-test', 'exec')

    def test_route_resume_preserves_request_loop(self):
        source = self.function_source('/tmp/orch_r118_node1_route_source/gpu/orch_r109_route_broker.py', 'serve')
        revised = resume_helpers.route_source(source)
        self.assertEqual(source[source.index('    receipts.mkdir'):], revised[revised.index('    receipts.mkdir'):])
        self.assertIn('buffer.is_dir()', revised)
        compile(revised, 'route-resume-cpu-test', 'exec')

    def test_grid_resume_keeps_disk_floor_and_request_claim_safety(self):
        source = self.function_source('/tmp/orch_r118_node3_6_grid_recovery_broker_source_20260915_v1/gpu/orch_r110_claude_broker.py', 'serve')
        revised = resume_helpers.grid_source(source)
        self.assertEqual(source[source.index('    buffer = Path'):], revised[revised.index('    buffer = Path'):])
        self.assertIn("shutil.disk_usage('/').free >= 10 * 1024 ** 3", revised)
        compile(revised, 'grid-resume-cpu-test', 'exec')

    def test_bootstrap_mismatch_fails_closed(self):
        for source in ('no_matching_bootstrap', 'buffer.mkdir(exist_ok=False)\nbuffer.mkdir(exist_ok=False)'):
            with self.assertRaisesRegex(ValueError, 'EXACT_EXISTING_BOOTSTRAP_REQUIRED'):
                resume_helpers.route_source(source)


if __name__ == '__main__':
    unittest.main()
