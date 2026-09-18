import json
from pathlib import Path
import shlex
import sys
import types
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import receiving_parent as receiver


def validator_fixture(config):
    if config['node'] not in ('ovx2', 'a40r', 'ovx3', 'a100'):
        raise ValueError('known_wrapper_only')
    if config['metadata'] != 'strict':
        raise ValueError('unchanged_metadata_validator')
    return config


class ReceivingParentTests(unittest.TestCase):
    def binding(self):
        return dict(target_node='node2', ssh_wrapper='gpu/ovx_ssh.sh', host='receiver-host',
            root='/receiver/root', source_root='/receiver/source')

    def test_console_is_explicit_rohin_and_follow_readonly(self):
        commands = receiver.console_commands(self.binding())
        follow = shlex.split(shlex.split(commands['follow'])[-1])
        publish = shlex.split(shlex.split(commands['rohin_publish'])[-1])
        self.assertIn('--follow', follow)
        self.assertIn('gpu.orch_r127_pilot_console', publish)
        self.assertEqual(publish[publish.index('--speaker') + 1], 'Rohin')
        self.assertEqual(publish[publish.index('--root') + 1], '/receiver/root')
        self.assertNotIn('ovx2', commands['rohin_publish'])

    def test_fresh_snapshot_routes_only_receiver_and_rebuilds_cursor(self):
        calls = []

        def runner(command, **kwargs):
            calls.append((command, kwargs['input']))
            state = dict(request_count=200, response_count=200, delivered={})
            return types.SimpleNamespace(returncode=0, stdout=json.dumps(dict(snapshot=state, cursor={'next': 5})))

        poll = receiver.make_poll(4, self.binding(), runner)
        with patch.object(receiver, 'rebase', side_effect=lambda physical, state: state):
            poll(4, {'stale': True})
            poll(4, {'fresh': True})
        self.assertEqual(calls[0][0][1], str(receiver.base.REPO / 'gpu/ovx_ssh.sh'))
        self.assertIn("root='/receiver/root'\n", calls[0][1])
        self.assertIn('cursor=None\n', calls[0][1])
        self.assertIn("cursor={'fresh': True}\n", calls[1][1])
        self.assertIn("socket.gethostname()=='receiver-host'", calls[0][1])

    def test_rejects_old_wrapper_before_call(self):
        binding = dict(self.binding(), ssh_wrapper='gpu/ovx2_ssh.sh')
        with patch.object(receiver.subprocess, 'run') as run:
            with self.assertRaisesRegex(ValueError, 'receiver_wrapper_only'):
                receiver.remote(binding, '')
            run.assert_not_called()

    def test_rejects_wrong_life(self):
        poll = receiver.make_poll(4, self.binding())
        with self.assertRaisesRegex(ValueError, 'single_life_receiver'):
            poll(1)

    def test_final_rollback_adds_only_observed_lifetime_offsets(self):
        original = dict(request_count=200, response_count=199,
            delivered={'before': dict(record_index=5000, request_count=80),
                'after': dict(record_index=6000, request_count=190)})
        result = receiver.rebase(7, original)
        self.assertEqual(result['request_count'], 203)
        self.assertEqual(result['response_count'], 202)
        self.assertEqual(result['delivered']['before']['request_count'], 80)
        self.assertEqual(result['delivered']['after']['request_count'], 193)
        self.assertEqual(original['request_count'], 200)

    def test_both_explicit_rollback_offsets_preserved(self):
        result = receiver.rebase(1, dict(request_count=200, response_count=199, delivered={}))
        self.assertEqual(result['request_count'], 206)
        self.assertEqual(result['response_count'], 205)

    def test_boundary_complete_has_no_new_offset(self):
        result = receiver.rebase(4, dict(request_count=200, response_count=199, delivered={}))
        self.assertEqual(result['request_count'], 200)

    def test_no_started_claim_before_owner_loaded(self):
        handoff = dict(status='LOADING', source_original_physical=4)
        with patch.object(receiver.base, 'read', return_value=handoff), patch.object(receiver, 'verify') as verify:
            with self.assertRaisesRegex(ValueError, 'actual_owner_loaded_handoff'):
                receiver.prepare(4, '/unused')
            verify.assert_not_called()

    def test_allowlist_repair_keeps_exact_route_and_strict_metadata(self):
        expected = dict(node='ovx', root='/receiver/root', source_root='/receiver/source', hard_end_unix=42, metadata='strict')
        validate = receiver.receiver_validator(validator_fixture, expected)
        self.assertEqual(validate(expected), expected)
        with self.assertRaisesRegex(ValueError, 'unchanged_metadata_validator'):
            validate(dict(expected, metadata='relaxed'))
        with self.assertRaisesRegex(ValueError, 'exact_receiver_configuration'):
            validate(dict(expected, node='ovx2'))


if __name__ == '__main__':
    unittest.main()
