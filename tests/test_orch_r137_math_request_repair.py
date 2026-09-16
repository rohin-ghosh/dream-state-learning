import ast
from copy import deepcopy
import hashlib
import inspect
import json
from pathlib import Path
import re
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from gpu import orch_r137_math_request_repair as repair


class FutureOnlyTests(unittest.TestCase):
    def setUp(self):
        self.epoch = dict(observed_unix=100, parent_high_water=10, historical_ids=['old'])
        self.row = dict(id='R121_C000038_E0_experience', reservation=dict(first=11, count=1, reserved_unix=101),
            response=False, partial=False, claim=False, delivered=False)

    def test_fresh_only(self):
        self.assertTrue(repair.eligible(self.row, self.epoch))

    def test_every_prior_disposition_excluded(self):
        for key in ('response', 'partial', 'claim', 'delivered'):
            with self.subTest(key=key):
                self.assertFalse(repair.eligible(dict(self.row, **{key: True}), self.epoch))

    def test_historical_id_cannot_be_renumbered(self):
        self.assertFalse(repair.eligible(dict(self.row, id='old'), self.epoch))

    def test_counter_and_time_boundaries_both_strict(self):
        for first, stamp in [(10, 101), (11, 100), (9, 99)]:
            with self.subTest(first=first, stamp=stamp):
                row = dict(self.row, reservation=dict(first=first, reserved_unix=stamp, count=1))
                self.assertFalse(repair.eligible(row, self.epoch))

    def test_unreserved_never_claimed(self):
        self.assertFalse(repair.eligible(dict(self.row, reservation=None), self.epoch))

    def test_non_native_request_fails_closed(self):
        with self.assertRaisesRegex(ValueError, 'exact_native_request'):
            repair.eligible(dict(self.row, id='old_request_replayed'), self.epoch)

    def test_batch_reservation_fails_closed(self):
        self.row['reservation']['count'] = 2
        with self.assertRaisesRegex(ValueError, 'one_native'):
            repair.eligible(self.row, self.epoch)

    def test_data_only_staging(self):
        with self.assertRaisesRegex(ValueError, 'data_only'):
            repair.stage_path(Path('/tmp/not-data'))

    def test_preserves_existing_wrapper_routing_location(self):
        for function in (repair.check, repair.retire, repair.serve):
            with self.subTest(function=function.__name__):
                source = inspect.getsource(function)
                self.assertNotIn("snapshot(path/'source')", source)
                self.assertIn('snapshot(OLD)', source)


class FrozenBackportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = repair.OLD/'gpu/orch_r110_claude_broker.py'
        if not path.exists():
            raise unittest.SkipTest('exact frozen A2 dependency not installed')
        assert repair.sha(path) == repair.PINS['gpu/orch_r110_claude_broker.py']
        cls.original = path.read_text()
        cls.patched = repair.repair_source(cls.original)

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        template = 'GAME [GAME]; STYLE [STYLE]; NUDGE [NUDGING]; FOCUS [FOCUS]'
        values = dict(require=repair.require, re=re, Path=Path, json=json, hashlib=hashlib,
            deepcopy=deepcopy, digest=repair.digest, sha=repair.sha, loads=json.loads,
            fixed_parent_template=lambda: template, PACKET_CAP=100000,
            SYSTEM_CONTRACT='EXACT FROZEN CONTRACT', BATTLEPLAN=self.root/'battleplan',
            FALLBACK_PARENT_FIELDS={})
        values['BATTLEPLAN'].write_text('fixture')
        tree = ast.parse(self.patched)
        functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)
            and node.name in ('render_parent_prompt', 'head_binding', 'build_system')]
        exec(compile(ast.Module(body=functions, type_ignores=[]), 'frozen-backport', 'exec'), values)
        self.functions = SimpleNamespace(**values)
        self.fields = dict(GAME='math', STYLE='supportive', NUDGING='check', FOCUS='notice',
            REFLECTION=dict(mode='long', max_new_tokens=3072))
        self.prompt = self.root/'F2.md'
        self.prompt.write_text(self.functions.render_parent_prompt(self.fields))
        self.principles = self.root/'principles'
        self.principles.write_text('original principles')
        self.config = dict(branch='F2', principles_sha256=repair.sha(self.principles))
        self.transcript = dict(game='math', cycle=38, episode=0, phase='experience', events=[])

    def settings(self, note, stale=False):
        fields = dict(self.fields, NEXT_GUIDANCE=note)
        self.prompt.with_suffix('.fields.json').write_text(json.dumps(dict(schema='ORCH_R114_HEAD_FIELDS_V1',
            prompt_sha256='0'*64 if stale else repair.sha(self.prompt), fields=fields)))

    def build(self):
        return self.functions.build_system(self.transcript, self.config, self.root, self.principles)

    def test_only_two_function_bodies_change(self):
        def bodies(text):
            return {node.name:ast.dump(node) for node in ast.parse(text).body if isinstance(node, ast.FunctionDef)}
        before, after = bodies(self.original), bodies(self.patched)
        self.assertEqual({name for name in before if before[name] != after[name]}, {'render_parent_prompt', 'build_system'})

    def test_wrong_source_or_second_patch_rejected(self):
        for source in ('unrelated', self.patched):
            with self.subTest(source_length=len(source)):
                with self.assertRaisesRegex(ValueError, 'exact_frozen_patch_site'):
                    repair.repair_source(source)

    def test_legacy_prompt_unchanged(self):
        self.assertEqual(self.functions.render_parent_prompt(self.fields),
            self.functions.render_parent_prompt(dict(self.fields, NEXT_GUIDANCE='new note')))

    def test_note_included_exactly_and_hashed_before_unchanged_contract(self):
        self.settings('new note')
        system, prompt, binding = self.build()
        self.assertIn('\n\nASYNCHRONOUS HEAD NEXT_GUIDANCE:\nnew note\n\nEXACT FROZEN CONTRACT', system)
        self.assertEqual(prompt, self.prompt.read_bytes())
        self.assertEqual(binding['next_guidance_sha256'], hashlib.sha256(b'new note').hexdigest())
        self.assertEqual(binding['system_sha256'], hashlib.sha256(system.encode()).hexdigest())
        policy = system.split('\n\nTRAIN TRANSCRIPT:')[0]
        self.assertEqual(binding['parent_policy_sha256'], hashlib.sha256(policy.encode()).hexdigest())
        self.assertFalse(binding['head_waited'])

    def test_stale_note_not_used(self):
        self.settings('stale note', stale=True)
        system, unused, binding = self.build()
        self.assertNotIn('stale note', system)
        self.assertEqual(binding['head_settings']['status'], 'SETTINGS_MISMATCH_REPORT_ONLY')

    def test_empty_or_absent_note_preserves_system(self):
        original, unused, unused_binding = self.build()
        self.settings('')
        self.assertEqual(self.build()[0], original)

    def test_note_validation_utf8_and_type(self):
        for value in ('x'*1025, '\u00e9'*513, 1, None):
            with self.subTest(kind=type(value).__name__):
                with self.assertRaisesRegex(ValueError, 'bounded_next_guidance'):
                    self.functions.render_parent_prompt(dict(self.fields, NEXT_GUIDANCE=value))
        self.functions.render_parent_prompt(dict(self.fields, NEXT_GUIDANCE='\u00e9'*512))

    def test_unknown_fields_still_rejected(self):
        with self.assertRaisesRegex(ValueError, 'head_fields_keys'):
            self.functions.render_parent_prompt(dict(self.fields, UNKNOWN='no'))

    def test_old_reflection_validation_retained(self):
        with self.assertRaisesRegex(ValueError, 'reflection_request_bounds'):
            self.functions.render_parent_prompt(dict(self.fields, REFLECTION=dict(mode='bad', max_new_tokens=1)))

    def test_full_system_limit_not_cropped(self):
        self.settings('valid note')
        self.functions.build_system.__globals__['PACKET_CAP'] = 1
        with self.assertRaisesRegex(ValueError, 'bounded_parent_prompt'):
            self.build()


class DataPacketTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        values = {}
        exec("def frozen(request, directory, deadline, *, marker):\n"
             "    shared.require(False, 'bounded_tmp_only')\n"
             "    shared.require(marker, 'unchanged_other_check')\n"
             "    return tomllib.loads(request)\n", values)
        self.settings = Mock(return_value={'model': 'unchanged', 'effort': 'low'})
        self.active = SimpleNamespace(base=SimpleNamespace(require=repair.require),
            delivery=SimpleNamespace(astra_evaluate=values['frozen']), low_settings=self.settings)

    def test_data_bound_delegation_once(self):
        result = repair.data_evaluator(self.active, self.root)('settings', self.root/'call', 9, marker=True)
        self.assertEqual(result['effort'], 'low')
        self.settings.assert_called_once_with('settings')

    def test_wrong_packet_directory_rejected_before_delegate(self):
        with self.assertRaisesRegex(ValueError, 'only_private_data_packets'):
            repair.data_evaluator(self.active, self.root)('settings', Path('/tmp/outside'), 9, marker=True)
        self.settings.assert_not_called()

    def test_other_validation_not_weakened(self):
        with self.assertRaisesRegex(ValueError, 'unchanged_other_check'):
            repair.data_evaluator(self.active, self.root)('settings', self.root/'call', 9, marker=False)
        self.settings.assert_not_called()


class RetirementTests(unittest.TestCase):
    def test_already_absent_lock_is_success(self):
        store = Mock()
        store.shell.return_value.returncode = 0
        repair.release_runner_lock(store)
        command = store.shell.call_args.args[0]
        self.assertIn('test ! -e ', command)
        self.assertIn('test ! -L ', command)
        self.assertIn('; then :; else rmdir ', command)
        self.assertNotIn('rm -', command)

    def test_nonempty_or_invalid_lock_fails_closed(self):
        store = Mock()
        store.shell.return_value.returncode = 1
        with self.assertRaisesRegex(ValueError, 'only_empty_or_already_absent'):
            repair.release_runner_lock(store)

    def test_inflight_check_resumes_exact_old_broker_without_termination(self):
        identity = dict(pid=1234, start_ticks='567', command_sha256='a'*64)
        with patch.object(repair, 'verify', return_value=(Mock(), {})), \
                patch.object(repair, 'authorize'), patch.object(repair, 'read', return_value={'identity': identity}), \
                patch.object(repair.os, 'pidfd_open', return_value=99), \
                patch.object(repair, 'process_identity', return_value=identity), \
                patch.object(repair, 'process_activity', return_value={'state': 'T'}), \
                patch.object(repair, 'check', side_effect=ValueError('inflight')), \
                patch.object(repair.signal, 'pidfd_send_signal') as send, patch.object(repair.os, 'close'):
            with self.assertRaisesRegex(ValueError, 'inflight'):
                repair.retire(Path('/unused'), 'hash', Path('/unused/go'))
        self.assertEqual([call.args for call in send.call_args_list],
            [(99, repair.signal.SIGSTOP), (99, repair.signal.SIGCONT)])

    def test_reused_pid_never_signalled(self):
        identity = dict(pid=1234, start_ticks='567', command_sha256='a'*64)
        with patch.object(repair, 'verify', return_value=(Mock(), {})), \
                patch.object(repair, 'authorize'), patch.object(repair, 'read', return_value={'identity': identity}), \
                patch.object(repair.os, 'pidfd_open', return_value=99), \
                patch.object(repair, 'process_identity', return_value=dict(identity, start_ticks='568')), \
                patch.object(repair.signal, 'pidfd_send_signal') as send, patch.object(repair.os, 'close'):
            with self.assertRaisesRegex(ValueError, 'exact_broker_before_stop'):
                repair.retire(Path('/unused'), 'hash', Path('/unused/go'))
        send.assert_not_called()


if __name__ == '__main__':
    unittest.main()
