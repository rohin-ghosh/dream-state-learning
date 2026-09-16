import copy
import inspect
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from gpu import orch_r139_grid_timer_custody as subject
from gpu import orch_r139_grid_astra_handoff as handoff
from gpu import orch_r119_grid_final_lifecycle as legacy


def identity(pid):
    return dict(pid=pid, uid=os.getuid(), start_ticks=str(pid), boot_id='fixture', command_sha256='a' * 64)


class Fixture(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.output = self.root / 'timer'
        self.output.mkdir()
        self.addCleanup(patch.stopall)
        patch.object(subject, 'OUTPUT', self.output).start()
        patch.object(subject, 'ROOT', self.root).start()
        self.source = self.root / 'source.py'
        self.source.write_text('fixture')
        self.plan = dict(root=str(self.root), output=str(self.output), controller_source=subject.ref(self.source),
            handoff_source=subject.ref(self.source), native_source=subject.ref(self.source),
            checkpoint=dict(path='checkpoint', sha256='c' * 64), predecessor=identity(100),
            initial_successor_receipt=str(self.root / 'initial.json'),
            morning_successor_receipt=str(self.root / 'resumed.json'),
            approved_intake='existing_ratification', requested_scope='Level1',
            old_final_plan=dict(path='old_plan', sha256='d' * 64),
            old_timers={'old_morning_timer': identity(201), 'old_wall_timer': identity(202)})
        self.old = dict(output=str(self.root / 'final'), predecessor=identity(100), mailbox_era='independent_r119_v1')
        Path(self.old['output']).mkdir()
        self.live = set()
        self.legacy = SimpleNamespace(**vars(legacy))
        self.legacy.same_process = lambda expected: expected['pid'] in self.live
        self.legacy.process = lambda pid: identity(pid)

    def write(self, path, value):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))
        return subject.ref(path)

    def actor(self, role, pid, restored=True):
        with patch.object(self.legacy, 'process', return_value=identity(pid)):
            record = subject.actor_record(self.plan, self.legacy, role)
        self.write(self.output / (role.upper() + '_ACTOR.json'), record)
        if role != 'evaluate' and restored:
            key = 'initial_successor_receipt' if role == 'initial' else 'morning_successor_receipt'
            self.write(self.plan[key], dict(identity=identity(pid), checkpoint=self.plan['checkpoint'],
                parent_model=subject.ASTRA, parent_segment=subject.ERA, counter_reset=False))
        return record

    def publication(self):
        return dict(authorized=True, published_by='Main', timer_plan={'sha256': 'pinned'},
            controller_source=self.plan['controller_source'], actions=subject.ACTIONS,
            approved_intake=self.plan['approved_intake'], requested_scope=self.plan['requested_scope'],
            not_before_unix=10, hard_end_unix=subject.HARD_END)


class PublicationTests(Fixture):
    def test_only_exact_Main_publication(self):
        receipt = self.publication()
        subject.authorize(self.plan, receipt, {'sha256': 'pinned'}, 11)
        for key, value in [('authorized', False), ('published_by', 'sidecar'), ('actions', []),
                           ('timer_plan', {}), ('controller_source', {}), ('not_before_unix', 12),
                           ('requested_scope', 'Level2'), ('hard_end_unix', subject.HARD_END + 1)]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                subject.authorize(self.plan, dict(receipt, **{key: value}), {'sha256': 'pinned'}, 11)
        with self.assertRaises(ValueError):
            subject.authorize(self.plan, receipt, {'sha256': 'pinned'}, subject.HARD_END)

    def test_cli_cannot_signal_or_launch_without_publication(self):
        path = self.output / 'plan.json'
        self.write(path, self.plan)
        for mode in ('arm', 'morning', 'initial-resume', 'evaluate', 'resume'):
            with (patch.object(subject, 'validate', return_value=(None, self.legacy, self.old)),
                  patch.object(subject, 'signal_exact', side_effect=AssertionError('no_signals')),
                  patch.object(subject.subprocess, 'Popen', side_effect=AssertionError('no_launch')),
                  patch.object(subject.sys, 'argv', ['timer', mode, '--expected-self-sha256', subject.sha(subject.__file__),
                      '--plan', str(path), '--plan-sha256', subject.sha(path)])):
                with self.subTest(mode=mode), self.assertRaisesRegex(ValueError, 'Main_publication'):
                    subject.main()

    def test_receipt_matches_frozen_consumer_contract(self):
        self.plan['initial_successor_receipt'] = str(self.root / handoff.ERA / 'RESUMED.json')
        timers = subject.custody_receipt(self.plan, identity(200), {'publication': 'hash'})
        frozen = dict(references={'old_final_plan': self.plan['old_final_plan'], 'budget': {}}, cumulative_caps={'PARENT': 9})
        self.live.add(200)
        def checked(value):
            return timers if value == {'timer': 'hash'} else {'prospective_caps': {'PARENT': 9}}
        with (patch.object(handoff, 'custody', return_value=self.legacy), patch.object(handoff, 'ROOT', self.root),
              patch.object(handoff, 'checked', side_effect=checked)):
            self.assertIs(handoff.validate_native(frozen, {'timer_custody': {'timer': 'hash'}}), self.legacy)

    def test_fixed_eight_and_distinct_clocks(self):
        receipt = subject.custody_receipt(self.plan, identity(200), {})
        self.assertEqual((receipt['morning_unix'], receipt['train_end_unix'], receipt['hard_end_unix']),
                         (1789538400, 1789596120, 1789596240))
        self.assertEqual(receipt['existing_FINAL_quota'], 8)
        self.assertEqual(receipt['additional_FINAL_calls'], 0)
        self.assertFalse(receipt['sealed_inputs_to_parent'])
        self.assertTrue(receipt['resume_preserves_R139_parent_binding'])


class ActorTests(Fixture):
    def test_actual_current_PID_moves_only_after_restored_receipt(self):
        self.actor('initial', 301)
        self.live.add(301)
        self.assertEqual(subject.current_native(self.plan, self.legacy)['identity'], identity(301))
        self.actor('resume', 302, restored=False)
        self.assertEqual(subject.current_native(self.plan, self.legacy)['identity'], identity(301))
        self.actor('resume', 302)
        self.live = {302}
        self.assertEqual(subject.current_native(self.plan, self.legacy)['identity'], identity(302))

    def test_duplicate_or_original_live_actor_fails_closed(self):
        self.actor('initial', 301)
        self.actor('resume', 302)
        for live in ({301, 302}, {100, 301}, set()):
            self.live = live
            with self.assertRaises(ValueError):
                subject.current_native(self.plan, self.legacy)

    def test_reused_PID_or_false_provider_is_rejected(self):
        self.actor('initial', 301)
        self.live.add(301)
        path = Path(self.plan['initial_successor_receipt'])
        document = subject.read(path)
        for key, value in [('identity', dict(identity(301), start_ticks='different')),
                           ('parent_model', 'claude-fable-5-1'), ('counter_reset', True)]:
            self.write(path, dict(document, **{key: value}))
            with self.assertRaises(ValueError):
                subject.current_native(self.plan, self.legacy)

    def test_changed_source_disables_current_callback(self):
        self.actor('initial', 301)
        self.live.add(301)
        self.source.write_text('changed')
        with self.assertRaisesRegex(ValueError, 'source_identity'):
            subject.current_native(self.plan, self.legacy)

    def test_wall_tracks_loading_evaluation_and_both_successors(self):
        for role, pid in [('initial', 301), ('evaluate', 302), ('resume', 303)]:
            self.actor(role, pid, restored=False)
        self.assertEqual([item['pid'] for item in subject.wall_targets(self.plan, self.legacy)], [100, 301, 302, 303])

    def test_registration_once_before_any_model_load(self):
        subject.register(self.plan, self.legacy, 'initial')
        with self.assertRaises(FileExistsError):
            subject.register(self.plan, self.legacy, 'initial')
        self.assertFalse(subject.read(self.output / 'INITIAL_ACTOR.json')['parent_absent'])
        subject.register(self.plan, self.legacy, 'evaluate')
        self.assertTrue(subject.read(self.output / 'EVALUATE_ACTOR.json')['parent_absent'])

    def test_only_predecessor_changes_in_final_plan(self):
        self.actor('initial', 301)
        self.live.add(301)
        before = copy.deepcopy(self.old)
        result, actor = subject.derived_plan(self.plan, self.legacy, self.old)
        self.assertEqual(result, dict(before, predecessor=identity(301)))
        self.assertEqual(self.old, before)


class BoundaryTests(Fixture):
    def test_wall_keeps_all_cached_owned_targets_if_one_signal_fails(self):
        self.output.rmdir()
        self.live = {100, 201, 202, 301, 302}
        clock = iter([subject.MORNING - 60, subject.MORNING - 60, subject.HARD_END + 1, subject.HARD_END + 1])
        signals = []
        def send(old, expected, signum):
            signals.append((expected['pid'], signum))
            if expected['pid'] == 301:
                raise ValueError('synthetic_signal_failure')
        with (patch.object(subject, 'validate', return_value=(handoff, self.legacy, self.old)),
              patch.object(subject, 'signal_exact', side_effect=send),
              patch.object(subject, 'wall_targets', return_value=[identity(100), identity(301), identity(302)]),
              patch.object(subject.time, 'time', side_effect=lambda: next(clock, subject.HARD_END + 1)),
              patch.dict(os.environ, CUDA_VISIBLE_DEVICES=''),
              patch.object(subject.subprocess, 'Popen', side_effect=AssertionError('no_model_launch'))):
            subject.arm(self.plan, self.source, self.source)
        self.assertEqual(signals, [(201, subject.signal.SIGTERM), (202, subject.signal.SIGTERM),
            (100, subject.signal.SIGKILL), (301, subject.signal.SIGKILL), (302, subject.signal.SIGKILL)])
        self.assertEqual(len(subject.read(self.output / 'WALL_DISPOSITION.json')['failures']), 1)

    def test_partial_retirement_does_not_publish_false_armed_receipt(self):
        self.output.rmdir()
        self.live = {100, 201, 202}
        clock = iter([subject.MORNING - 60, subject.HARD_END + 1])
        signals = []
        def send(old, expected, signum):
            signals.append((expected['pid'], signum))
            if expected['pid'] == 202:
                raise ValueError('synthetic_retirement_failure')
        with (patch.object(subject, 'validate', return_value=(handoff, self.legacy, self.old)),
              patch.object(subject, 'signal_exact', side_effect=send),
              patch.object(subject.time, 'time', side_effect=lambda: next(clock, subject.HARD_END + 1)),
              patch.dict(os.environ, CUDA_VISIBLE_DEVICES=''),
              patch.object(subject.subprocess, 'Popen', side_effect=AssertionError('no_launch'))):
            subject.arm(self.plan, self.source, self.source)
        self.assertFalse((self.output / 'ARMED.json').exists())
        self.assertTrue((self.output / 'ARM_FAILED.json').exists())
        self.assertIn((100, subject.signal.SIGKILL), signals)

    def test_no_signal_on_PID_reuse_or_wrong_owner(self):
        with patch.object(subject.os, 'pidfd_open', side_effect=AssertionError('must_not_open')):
            with self.assertRaises(ValueError):
                subject.signal_exact(self.legacy, identity(301), subject.signal.SIGTERM)
            self.live.add(301)
            with self.assertRaises(ValueError):
                subject.signal_exact(self.legacy, dict(identity(301), uid=os.getuid() + 1), subject.signal.SIGTERM)

    def test_pidfd_rechecks_identity_and_waits_for_exact_exit(self):
        self.live.add(301)
        with (patch.object(subject.os, 'pidfd_open', return_value=99), patch.object(subject.os, 'close') as close,
              patch.object(subject.signal, 'pidfd_send_signal') as send,
              patch.object(subject.select, 'select', return_value=([99], [], []))):
            subject.signal_exact(self.legacy, identity(301), subject.signal.SIGTERM)
            send.assert_called_once_with(99, subject.signal.SIGTERM)
            close.assert_called_once_with(99)

    def test_prior_FINAL_claim_never_releases_or_retries(self):
        self.write(Path(self.old['output']) / 'EVAL_CLAIM.json', {'attempted': True})
        with (patch.object(subject, 'validate', return_value=(handoff, self.legacy, self.old)),
              patch.object(subject, 'live_custody'), patch.dict(os.environ, CUDA_VISIBLE_DEVICES=''),
              patch.object(subject.time, 'time', return_value=subject.MORNING),
              patch.object(subject, 'derived_plan', side_effect=AssertionError('no_release'))):
            with self.assertRaisesRegex(ValueError, 'prior_FINAL'):
                subject.morning(self.plan, self.source, self.source)

    def test_morning_uses_actual_actor_and_resumes_once_after_failed_capture(self):
        self.actor('initial', 301)
        self.live.add(301)
        self.legacy.fresh_scan = Mock(return_value={})
        release = Mock()
        launches = []
        def launch(plan, old_legacy, old_plan, mode, admission, plan_path, publication_path):
            launches.append(mode)
            return SimpleNamespace(wait=lambda: 1 if mode == 'evaluate' else 0)
        with (patch.object(subject, 'validate', return_value=(handoff, self.legacy, self.old)),
              patch.object(subject, 'live_custody'), patch.object(subject, 'bind', return_value=release),
              patch.object(subject, 'launch_phase', side_effect=launch), patch.dict(os.environ, CUDA_VISIBLE_DEVICES=''),
              patch.object(subject.time, 'time', return_value=subject.MORNING)):
            subject.morning(self.plan, self.source, self.source)
        self.assertEqual(release.call_args.args[0]['predecessor'], identity(301))
        self.assertEqual(launches, ['evaluate', 'resume'])
        self.assertEqual(subject.read(self.output / 'EVAL_EXIT.json')['exit_code'], 1)

    def test_existing_real_release_seam_has_no_early_signals(self):
        release = subject.bind(legacy.release_at_boundary, same_process=lambda expected: True)
        with (patch.object(subject.time, 'time', return_value=subject.MORNING - 1),
              patch.object(subject.signal, 'pidfd_send_signal', side_effect=AssertionError('no_signals'))):
            with self.assertRaisesRegex(ValueError, 'no_early_signal'):
                release({'predecessor': identity(301)})


class NativeBindingTests(Fixture):
    def test_reuses_exact_FINAL_and_resume_code_without_mutating_frozen_sources(self):
        from gpu import orch_r119_grid_final_native as native
        self.actor('initial', 301)
        boundary_ref = self.write(self.root / 'boundary.json', dict(cycle=7, next_cycle=8, after_parent=319, first_new_parent=320))
        initial_path = Path(self.plan['initial_successor_receipt'])
        self.write(initial_path, dict(subject.read(initial_path), boundary=boundary_ref))
        frozen_native = Path(native.__file__).resolve()
        self.plan['native_source'] = subject.ref(frozen_native)
        record = subject.read(self.output / 'INITIAL_ACTOR.json')
        self.write(self.output / 'INITIAL_ACTOR.json', dict(record, native_source=self.plan['native_source']))
        factory = Mock(return_value='original_factory')
        prior = SimpleNamespace(mailbox=SimpleNamespace(life_class=factory))
        config = dict(life_id='F4_FABLE', parent_model='claude-fable-5-1')
        self.legacy.validate = Mock(return_value=(prior, object(), config, {}))
        hashes = {path: subject.sha(path) for path in [frozen_native, Path(handoff.__file__)]}
        derived = dict(self.old, predecessor=identity(301))
        def load(path, name):
            return handoff if name == 'r139_timer_resume_binding' else native
        with patch.object(subject, 'load', side_effect=load):
            callbacks = subject.adapted_native(self.plan, self.legacy, self.old, derived)
        for mode in ('evaluate', 'resume'):
            self.assertIs(callbacks[mode].__code__, getattr(native, mode).__code__)
        view = callbacks['resume'].__globals__['custody']
        new_prior, grid, new_config, checkpoint = view.validate(derived)
        self.assertEqual(new_config['parent_model'], subject.ASTRA)
        self.assertEqual(config['parent_model'], 'claude-fable-5-1')
        new_prior.mailbox.life_class(grid, 'independent_r119_v1')
        factory.assert_called_once_with(grid, 'independent_r119_v1', first_parent=320)
        self.assertEqual({path: subject.sha(path) for path in hashes}, hashes)
        self.assertIs(prior.mailbox.life_class, factory)
        view.write(Path(self.old['output']) / 'RESUMED.json', {'counter_reset': False})
        self.assertEqual(subject.read(Path(self.old['output']) / 'RESUMED.json')['parent_model'], subject.ASTRA)

    def test_original_FINAL_empty_context_and_quota_seam_retained(self):
        from gpu import orch_r119_grid_final_native as native
        source = inspect.getsource(native.evaluate)
        self.assertIn('context=native.StageContext()', source)
        self.assertIn("len(tasks) == 8", source)
        self.assertIn('engine.batch(messages, 2048)', source)
        self.assertNotIn('CARRY.json', source)
        self.assertNotIn('parent_queue', source)
        self.assertNotIn('while ', source)
        self.assertIn('no_duplicate_capture', source)

    def test_no_model_or_GPU_import_in_timer_entrypoint(self):
        source = Path(subject.__file__).read_text()
        for forbidden in ('import torch', 'import peft', 'import requests', 'import openai', 'eval(', 'exec('):
            self.assertNotIn(forbidden, source)

    def test_duplicate_json_and_symlink_rejected(self):
        path = self.root / 'duplicate.json'
        path.write_text('{"authorized": false, "authorized": true}')
        with self.assertRaisesRegex(ValueError, 'duplicate_key'):
            subject.read(path)
        linked = self.root / 'linked.json'
        linked.symlink_to(path)
        with self.assertRaises(ValueError):
            subject.read(linked)


if __name__ == '__main__':
    unittest.main()
