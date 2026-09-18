import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

from gpu import orch_r119_grid_final_lifecycle as lifecycle
from gpu import orch_r119_grid_final_parent as parent


def plan_for(branch='F4'):
    root, output = lifecycle.event_paths(branch)
    return dict(schema='R119_GRID_INDEPENDENT_FINAL_LIFECYCLE_V1', branch=branch,
        event=lifecycle.EVENT, root=str(root), output=str(output), morning_unix=lifecycle.MORNING,
        boundary_end_unix=lifecycle.BOUNDARY_END, evaluation_end_unix=lifecycle.EVAL_END,
        train_end_unix=lifecycle.TRAIN_END, hard_end_unix=lifecycle.HARD_END,
        native_call_cap=8, parent_call_cap=0, training_call_cap=0, optimizer_steps=0,
        lease_wall_extra_calls=0, parent_absent=True, readout_carry_access=False,
        shared_coordinator=False, old_final_retry=False, mailbox_era=lifecycle.BRANCHES[branch][0],
        predecessor=dict(pid=lifecycle.BRANCHES[branch][2]))


class ScopeTests(unittest.TestCase):
    def test_broker_cannot_move_before_real_release_resume_and_unlock(self):
        self.assertTrue(parent.ready_for_transfer(True, True, False, False, parent.MORNING+1))
        for released, resumed, lock, terminal, now in [
                (False, True, False, False, parent.MORNING+1),
                (True, False, False, False, parent.MORNING+1),
                (True, True, True, False, parent.MORNING+1),
                (True, True, False, True, parent.MORNING+1),
                (True, True, False, False, parent.MORNING-1),
                (True, True, False, False, parent.END)]:
            self.assertFalse(parent.ready_for_transfer(released, resumed, lock, terminal, now))

    def test_broker_keeps_low_short_episode_only_and_no_claim_replay(self):
        text = parent.source()
        self.assertIn(repr((parent.EVENT,)), text)
        self.assertIn(repr((parent.EVENT + '/LIFE_TERMINAL.json',)), text)
        self.assertIn('max_output_tokens=1024', text)
        self.assertIn("'low'", text)
        self.assertIn('EXISTING_CLAIM_NO_RETRY', text)
        self.assertIn('non_episode_cadence_skip_no_provider_call', text)
        compile(text, 'prospective_A4_custody', 'exec')

    def test_distinct_utc_clocks(self):
        from datetime import datetime, timezone
        self.assertEqual(datetime.fromtimestamp(lifecycle.MORNING, timezone.utc).isoformat(),
                         '2026-09-16T06:00:00+00:00')
        self.assertEqual(datetime.fromtimestamp(lifecycle.HARD_END, timezone.utc).isoformat(),
                         '2026-09-16T22:04:00+00:00')
        self.assertLess(lifecycle.EVAL_END, lifecycle.TRAIN_END)

    def test_both_exact_existing_mailbox_eras(self):
        for branch in lifecycle.BRANCHES:
            lifecycle.validate_scope(plan_for(branch))

    def test_no_extra_capture_parent_optimizer_or_old_retry(self):
        for key, value in [('native_call_cap', 16), ('parent_call_cap', 1), ('optimizer_steps', 1),
                           ('training_call_cap', 1), ('lease_wall_extra_calls', 8),
                           ('parent_absent', False), ('readout_carry_access', True),
                           ('shared_coordinator', True), ('old_final_retry', True),
                           ('morning_unix', 1789491600), ('hard_end_unix', lifecycle.HARD_END + 1)]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                plan = plan_for()
                plan[key] = value
                lifecycle.validate_scope(plan)

    def test_no_other_root_or_custody(self):
        for key, value in [('root', '/tmp/foreign'), ('mailbox_era', 'reset'),
                           ('predecessor', {'pid': 1})]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                plan = plan_for()
                plan[key] = value
                lifecycle.validate_scope(plan)

    def test_claim_is_irrevocable_even_without_responses(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            self.assertTrue(lifecycle.no_attempt(output))
            lifecycle.write(output / 'EVAL_CLAIM.json', {'status': 'STARTED'})
            self.assertFalse(lifecycle.no_attempt(output))
            with self.assertRaises(FileExistsError):
                lifecycle.write(output / 'EVAL_CLAIM.json', {})

    def test_no_signal_before_morning(self):
        with mock.patch.object(lifecycle.time, 'time', return_value=lifecycle.MORNING - 1), \
                mock.patch.object(lifecycle.os, 'pidfd_open') as opening, \
                self.assertRaisesRegex(ValueError, 'no_early_signal'):
            lifecycle.release_at_boundary(plan_for())
        opening.assert_not_called()

    def test_no_signal_on_changed_identity(self):
        with mock.patch.object(lifecycle.time, 'time', return_value=lifecycle.MORNING + 1), \
                mock.patch.object(lifecycle, 'same_process', return_value=False), \
                mock.patch.object(lifecycle.os, 'pidfd_open') as opening, \
                self.assertRaisesRegex(ValueError, 'custody_changed'):
            lifecycle.release_at_boundary(plan_for())
        opening.assert_not_called()

    def test_only_atomic_carry_rename_is_boundary_hint(self):
        def event(name, mask):
            payload = name + b'\0'
            return struct.pack('iIII', 1, mask, 0, len(payload)) + payload
        self.assertEqual(lifecycle.carry_events(event(b'CARRY.json', 0x80)), [b'CARRY.json'])
        self.assertEqual(lifecycle.carry_events(event(b'FINAL.json', 0x80)), [])
        self.assertEqual(lifecycle.carry_events(event(b'CARRY.json', 0x08)), [])


class BoundaryTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.rows = [dict(kind='NATIVE', number=601, cycle=12, split='TRAIN', attached_readout=False),
                     dict(kind='PARENT', number=42, cycle=12)]
        (self.root / 'LEDGER.jsonl').write_text('\n'.join(map(json.dumps, self.rows)) + '\n')
        self.carry = [dict(split='TRAIN', trace='prior own reflection')]
        lifecycle.write(self.root / 'CARRY.json', self.carry)
        lifecycle.write(self.root / 'cycles/0012/TRAIN_COMPLETE.json',
                        dict(outcomes=[{}, {}], optimizer_steps=0, carry=self.carry))
        lifecycle.write(self.root / 'calls/N00601.json', dict(status='COMPLETE'))

    def test_pending_parent_is_retained_not_replayed_or_forced(self):
        result = lifecycle.completed_boundary(self.root)
        self.assertEqual(result['next_cycle'], 13)
        self.assertEqual(result['counts'], {'NATIVE': 1, 'PARENT': 1})
        self.assertTrue(result['pending_parent_claims_preserved'])
        self.assertFalse((self.root / 'parent_received').exists())

    def test_started_next_cycle_cannot_discard_input(self):
        self.rows.append(dict(kind='NATIVE', number=602, cycle=13, split='TRAIN', attached_readout=False))
        (self.root / 'LEDGER.jsonl').write_text('\n'.join(map(json.dumps, self.rows)) + '\n')
        with self.assertRaisesRegex(ValueError, 'not_completed_cycle'):
            lifecycle.completed_boundary(self.root)

    def test_incomplete_call_rejected(self):
        (self.root / 'calls/N00601.json').write_text(json.dumps(dict(status='STARTED')))
        with self.assertRaisesRegex(ValueError, 'unfinished_model'):
            lifecycle.completed_boundary(self.root)

    def test_durable_carry_must_match_completed_cycle(self):
        (self.root / 'CARRY.json').write_text('[]')
        with self.assertRaisesRegex(ValueError, 'durable_carry'):
            lifecycle.completed_boundary(self.root)

    def test_held_cannot_be_adopted_as_training(self):
        self.rows[0]['split'] = 'FINAL'
        (self.root / 'LEDGER.jsonl').write_text('\n'.join(map(json.dumps, self.rows)) + '\n')
        with self.assertRaisesRegex(ValueError, 'no_eval'):
            lifecycle.completed_boundary(self.root)

    def run_cpu_actor(self, valid):
        carry = self.carry if valid else []
        temporary = self.root / 'next_carry.json'
        temporary.write_text(json.dumps(carry))
        code = ('import os,time; time.sleep(.4); '
                'os.replace(' + repr(str(temporary)) + ',' + repr(str(self.root / 'CARRY.json')) + '); '
                'time.sleep(10)')
        child = subprocess.Popen([sys.executable, '-c', code], stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL)
        self.addCleanup(lambda: child.kill() if child.poll() is None else None)
        plan = plan_for()
        plan['predecessor'] = lifecycle.process(child.pid)
        folder = self.root / 'event'
        with mock.patch.object(lifecycle, 'event_paths', return_value=(self.root, folder)), \
                mock.patch.object(lifecycle, 'MORNING', time.time()-1), \
                mock.patch.object(lifecycle, 'BOUNDARY_END', time.time()+1.5):
            if valid:
                result = lifecycle.release_at_boundary(plan)
                self.assertEqual(result['next_cycle'], 13)
                self.assertEqual(child.wait(timeout=1), -15)
                self.assertTrue((folder / 'RELEASED.json').exists())
            else:
                with self.assertRaisesRegex(ValueError, 'NO_COMPLETED_CYCLE'):
                    lifecycle.release_at_boundary(plan)
                self.assertIsNone(child.poll())
                state = Path(f'/proc/{child.pid}/stat').read_text().rpartition(') ')[2].split()[0]
                self.assertNotIn(state, ('T', 't'))
                self.assertFalse((folder / 'RELEASED.json').exists())
                child.terminate()
                child.wait(timeout=1)

    @unittest.skipUnless(hasattr(os, 'pidfd_open'), 'Linux pidfd required')
    def test_real_CPU_child_inotify_release_only_completed_cycle(self):
        self.run_cpu_actor(True)

    @unittest.skipUnless(hasattr(os, 'pidfd_open'), 'Linux pidfd required')
    def test_real_CPU_child_always_resumed_on_rejected_boundary(self):
        self.run_cpu_actor(False)


class NativeContractTests(unittest.TestCase):
    def test_evaluate_and_resume_are_distinct_cli_processes(self):
        source = Path(lifecycle.__file__).with_name('orch_r119_grid_final_native.py').read_text()
        import ast
        tree = ast.parse(source)
        bodies = {item.name: ast.get_source_segment(source, item) for item in tree.body
                  if isinstance(item, ast.FunctionDef)}
        self.assertNotIn('CARRY.json', bodies['evaluate'])
        self.assertNotIn('parent_queue', bodies['evaluate'])
        self.assertNotIn('EVAL_COMPLETE', bodies['resume'])
        self.assertNotIn('sealed_calls', bodies['resume'])
        self.assertNotIn('FINAL.json', bodies['resume'])
        self.assertIn("plan['mailbox_era']", bodies['resume'])
        self.assertIn("boundary['next_cycle']", bodies['resume'])

    def test_failed_capture_still_resumes_once(self):
        with tempfile.TemporaryDirectory() as directory:
            plan = plan_for()
            output = Path(directory)
            plan['output'] = str(output)
            lifecycle.write(output / 'PLAN.json', plan)
            calls = []
            child = mock.Mock()
            child.wait.return_value = 0

            def launch(unused_plan, mode, deadline, admission):
                calls.append(mode)
                if mode == 'evaluate':
                    raise ValueError('preserved_eval_failure')
                return child

            with mock.patch.object(lifecycle, 'validate'), \
                    mock.patch.object(lifecycle, 'same_process', return_value=True), \
                    mock.patch.object(lifecycle, 'process', return_value={'pid': 100}), \
                    mock.patch.object(lifecycle.time, 'time', side_effect=[lifecycle.MORNING-1] + [lifecycle.MORNING+1]*30), \
                    mock.patch.object(lifecycle, 'release_at_boundary'), \
                    mock.patch.object(lifecycle, 'fresh_scan'), \
                    mock.patch.object(lifecycle, 'launch', side_effect=launch), \
                    mock.patch.dict(lifecycle.os.environ, {'CUDA_VISIBLE_DEVICES': ''}):
                lifecycle.timer(plan)
            self.assertEqual(calls, ['evaluate', 'resume'])
            self.assertTrue((output / 'EVAL_ERROR.json').exists())
            self.assertTrue((output / 'LEASE_CUSTODY.json').exists())


if __name__ == '__main__':
    unittest.main()
