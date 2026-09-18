"""CPU-only custody preflight; no live journals, remote mutations or GPU use."""

import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

from gpu import orch_r155_kernel_parser_activate as activate


class CustodyTests(unittest.TestCase):
    def snapshot(self):
        return dict(process_inventory=dict(scanners=[], unreadable_pids=[]), errors=[],
                    campaign_state=dict(value=dict(phase='STOPPED')),
                    campaign_terminal=dict(value=dict(status='STOPPED')))

    def test_active_scanner_blocks_even_clean_metadata(self):
        snapshot = self.snapshot()
        snapshot['process_inventory']['scanners'] = [dict(pid=3754322)]
        self.assertEqual(activate.assess(snapshot)['status'], 'BLOCKED_CUSTODY')

    def test_no_inventory_is_admission(self):
        result = activate.assess(self.snapshot())
        self.assertEqual(result['status'], 'REQUIRES_LOCKED_HANDOFF')
        self.assertFalse(result['activation_authorized'])
        self.assertFalse(result['gpu_call_attempted'])

    def test_every_uncertain_campaign_phase_blocks(self):
        for phase in ('SERVICE_INTENT', 'PROBE_INTENT', 'BETWEEN_PHASES',
                      'FAILED_NO_RETRY', 'READY', 'INTENT', None):
            with self.subTest(phase=phase):
                snapshot = self.snapshot()
                snapshot['campaign_state']['value']['phase'] = phase
                self.assertEqual(activate.assess(snapshot)['status'], 'BLOCKED_CUSTODY')

    def test_unreadable_process_blocks(self):
        snapshot = self.snapshot()
        snapshot['process_inventory']['unreadable_pids'] = [123]
        self.assertIn('PROCESS_CUSTODY_INCOMPLETE', activate.assess(snapshot)['reasons'])

    def test_missing_terminal_and_metadata_block(self):
        snapshot = self.snapshot()
        del snapshot['campaign_terminal']
        snapshot['errors'] = ['missing']
        self.assertEqual(len(activate.assess(snapshot)['reasons']), 2)

    def test_module_and_script_scanners_detected(self):
        for command in ('gpu.orch_r148_kernel_service_campaign',
                        '/source/gpu/orch_r148_kernel_tool_service.py',
                        'gpu.orch_r140_pilot_tool_service',
                        'gpu.orch_r153_kernel_smoke'):
            with self.subTest(command=command):
                self.assertTrue(activate.scanner_modules(['python3', '-m', command]))
        self.assertFalse(activate.scanner_modules(['gpu.orch_r125_continual_native']))

    def test_proc_inventory_never_exposes_full_arguments(self):
        with tempfile.TemporaryDirectory() as temporary:
            process = Path(temporary) / '123'
            process.mkdir()
            (process / 'cmdline').write_bytes(
                b'python3\0-m\0gpu.orch_r148_kernel_tool_service\0private-argument\0')
            result = activate.process_inventory(Path(temporary))
            self.assertEqual(result['scanners'][0]['pid'], 123)
            self.assertNotIn('private-argument', json.dumps(result))

    def test_observation_missing_files_is_read_only_and_blocked(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            with patch.object(activate, 'process_inventory', return_value=dict(
                    scanners=[], unreadable_pids=[])):
                result = activate.observe(directory)
            self.assertEqual(result['assessment']['status'], 'BLOCKED_CUSTODY')
            self.assertEqual(list(directory.iterdir()), [])

    def test_metadata_omits_contents_not_on_allowlist(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'STATE.json'
            path.write_text(json.dumps(dict(phase='READY', raw='not for output')))
            result = activate.metadata(path, ('phase',))
            self.assertEqual(result['value'], dict(phase='READY'))
            self.assertNotIn('not for output', json.dumps(result))


class HandoffTests(unittest.TestCase):
    def state(self):
        service, campaign, _ = activate.modules()
        state = dict(schema=service.SCHEMA, phase='STOPPED', reason='WALL_LIMIT', next_index=40)
        state.update({key: 0 for key in campaign.COUNTERS})
        return state

    def test_clean_terminal_requires_exact_final_bindings(self):
        state = self.state()
        parent = dict(phase='STOPPED', service_state=state, observed_service_state=state)
        terminal = dict(status='WALL_LIMIT_NO_REPLAY', state=state)
        counters = activate.clean_terminal(parent, dict(status='STOPPED', state=parent), state, terminal)
        self.assertEqual(counters['calls'], 0)
        with self.assertRaisesRegex(ValueError, 'matching_clean_campaign'):
            activate.clean_terminal(parent, dict(status='FAILED_NO_RETRY', state=parent), state, terminal)

    def test_uncertain_intent_or_previous_call_refuses_handoff(self):
        for extra in (dict(phase='INTENT'), dict(pending_index=40),
                      dict(pending_response_sha256='a' * 64), dict(calls=1)):
            with self.subTest(extra=extra):
                state = dict(self.state(), **extra)
                parent = dict(phase='STOPPED', service_state=state, observed_service_state=state)
                with self.assertRaises(ValueError):
                    activate.clean_terminal(parent, dict(status='STOPPED', state=parent),
                        state, dict(status='WALL_LIMIT_NO_REPLAY', state=state))

    def test_future_origin_excludes_old_or_inflight_request(self):
        for kind in ('REQUEST', 'RESPONSE', 'SLEEP_REQUEST', 'UNKNOWN'):
            with self.subTest(kind=kind), self.assertRaisesRegex(ValueError, 'inflight'):
                activate.future_start(dict(index=100, kind=kind), 40)
        with self.assertRaisesRegex(ValueError, 'before_prior_cursor'):
            activate.future_start(dict(index=38, kind='UPDATE'), 40)
        self.assertEqual(activate.future_start(dict(index=100, kind='COMMITTED'), 40), 101)

    def test_preserves_counters_but_uses_new_future_cursor(self):
        previous = dict(self.state(), polls=6617, reads=3091900)
        seeded = dict(next_index=100, previous_sha256='future', phase='READY')
        result = activate.inherit_counters(seeded, previous)
        self.assertEqual(result['polls'], 6617)
        self.assertEqual(result['reads'], 3091900)
        self.assertEqual(result['next_index'], 100)
        self.assertEqual(result['previous_sha256'], 'future')
        self.assertNotIn('reason', result)
        self.assertEqual(seeded, dict(next_index=100, previous_sha256='future', phase='READY'))

    def test_cannot_clear_pending_state_by_reseeding(self):
        with self.assertRaisesRegex(ValueError, 'pending_state'):
            activate.inherit_counters({}, dict(self.state(), pending_index=40))

    def test_invalid_cpu_gate_never_calls_gpu(self):
        service, _, smoke = activate.modules()
        for observed in (time.time() - 1801, time.time() + 30):
            with self.subTest(observed=observed):
                gate = dict(schema='R155_ACTIVATION_CPU_V1', exit_code=0, source_pins={},
                            cpu_log='/tmp/log', cpu_log_sha256=service.sha(b'PASS'), observed_unix=observed)
                with patch.object(service.executor, 'trusted_path', side_effect=Path), \
                        patch.object(service, 'read', side_effect=[service.encoded(gate), b'PASS']), \
                        patch.object(activate, 'source_pins', return_value={}), \
                        patch.object(smoke, 'run') as gpu:
                    with self.assertRaisesRegex(ValueError, 'fresh_bound_CPU_gate'):
                        activate.activate(Path('/tmp/operator'))
                    gpu.assert_not_called()

    def test_worker_refuses_expired_gate_before_scanning(self):
        service, _, _ = activate.modules()
        config = dict(root=activate.ROOTS[0], code_policy=activate.POLICY)
        with patch.object(service, 'read', return_value=service.encoded(config)), \
                patch.object(service, 'validate_config'), \
                patch.object(service, 'limits', side_effect=ValueError('fresh_gate_required')), \
                patch.object(service, 'run') as run:
            with self.assertRaisesRegex(ValueError, 'fresh_gate_required'):
                activate.worker('/tmp/config')
            run.assert_not_called()

    def test_retired_kernel5_is_not_worker_target(self):
        service, _, _ = activate.modules()
        config = dict(root='/localhome/local-rohing/kernel_unparented/run1', code_policy=activate.POLICY)
        with patch.object(service, 'read', return_value=service.encoded(config)), \
                patch.object(service, 'run') as run:
            with self.assertRaisesRegex(ValueError, 'authorized_sidecar_roots'):
                activate.worker('/tmp/config')
            run.assert_not_called()

    def test_probe_permissions_and_umask_restore_on_failure(self):
        original = os.umask(0o077)
        try:
            with tempfile.TemporaryDirectory() as temporary:
                path = Path(temporary) / 'rootfs'
                with self.assertRaisesRegex(ValueError, 'probe_failure'):
                    with activate.probe_umask():
                        path.mkdir(mode=0o755)
                        self.assertEqual(path.stat().st_mode & 0o777, 0o755)
                        raise ValueError('probe_failure')
                self.assertEqual(os.umask(0o077), 0o077)
        finally:
            os.umask(original)

    def test_never_reconciles_unknown_or_child_intent(self):
        service, _, _ = activate.modules()
        with patch.object(service, 'read', return_value=b'{}'), \
                patch.object(service, 'lock_file') as lock, \
                patch.object(service, 'census') as census:
            with self.assertRaisesRegex(ValueError, 'exact_owned_preexec_failure'):
                activate.reconcile_preexec_failure(Path('/tmp/new'))
            lock.assert_not_called()
            census.assert_not_called()


if __name__ == '__main__':
    unittest.main()
