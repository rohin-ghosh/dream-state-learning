from copy import deepcopy
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

from gpu import orch_math_feedback_uptake_r118_final_drain as drain


io = drain.io


class BoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.root = self.directory/'lane1'
        self.common = self.directory/'common'
        self.cycle = self.root/'cycle010'
        self.ids = ['train0', 'train1']
        self.plan = dict(root=str(self.root), native=dict(pid=123), branch='F2')
        self.history = [dict(actor='child', text='Recorded unsuccessful attempt')]
        io.write(self.cycle/'TRAIN_EXPERIENCE.json', self.history)
        io.write(self.cycle/'BOUNDARY.json', dict(own_reflection=dict(actor='child', text='Own reflection'),
            source_history_sha256=io.digest(self.history)))
        paths = []
        for number, phase in enumerate(drain.PHASES, 1):
            request = self.cycle/f'CALL_{number:04d}.request.json'
            io.write(request, dict(phase=phase))
            call = self.cycle/f'CALL_{number:04d}.json'
            io.write(call, dict(status='COMPLETE', phase=phase, task_id=self.ids[0 if number <= 2 else 1],
                split='TRAIN', request_sha256=io.sha(request), shared_generation=0, shared_checkpoint_sha256='a'*64))
            paths.append(call)
            io.write(self.root/f'reservations/native_{number:04d}.json', dict(kind='native', first=number, count=1))
            identifier = f'C010_parent_{number}'
            io.write(self.root/f'reservations/parent_{number:04d}.json',
                dict(kind='parent', first=number, count=1, metadata=dict(id=identifier)))
            parent_request = self.root/'parent_queue'/(identifier+'.request.json')
            io.write(parent_request, dict(id=identifier))
            archive = self.root/'parent_transcripts'/identifier
            io.write(archive/'transcript.json', dict(status='MISSING', preserved=True))
            io.write(self.root/'parent_queue'/(identifier+'.response.json'), dict(status='MISSING',
                transcript_receipt=dict(remote_root=str(archive), files={'transcript.json':io.sha(archive/'transcript.json')})))
            io.write(self.root/'delivered'/(identifier+'.json'),
                dict(id=identifier, status='MISSING', request_sha256=io.digest(io.read(parent_request))))
        submission = self.common/'generation_000000/F2.json'
        io.write(submission, dict(branch='F2', generation=0, episode_ids=self.ids,
            rows=[dict(source_call_sha256=io.sha(path)) for path in paths]))
        io.write(self.cycle/'TRAIN_COMPLETE.json', dict(submission=io.ref(submission), shared_generation=0,
            shared_checkpoint_sha256='a'*64))
        io.write(self.root/'COUNTERS.json', dict(native=6, parent=6))
        io.write(self.root/'LATEST_PARENT.json', dict(status='MISSING'))
        io.write(self.common/'STATE.json', dict(config_sha256=io.COMMON_SHA, generation=0, checkpoint=dict(path_sha256='a'*64)))
        common = patch.object(io, 'COMMON', self.common)
        children = patch.object(drain, 'live_children', return_value=[])
        common.start()
        children.start()
        self.addCleanup(common.stop)
        self.addCleanup(children.stop)

    def rewrite(self, path, function):
        document = io.read(path)
        function(document)
        path.write_text(io.json.dumps(document))

    def test_actual_accepted_collection_carry_all_charges_and_missing_parents_preserved(self):
        value = drain.snapshot(self.plan)
        self.assertEqual(value['kind'], 'COMPLETE_COLLECTION_ACCEPTED_WAITING_FOR_SHARED_CHECKPOINT')
        self.assertEqual(value['counters'], dict(native=6, parent=6))
        self.assertEqual(value['episode_ids'], self.ids)
        self.assertIn('cycle010/BOUNDARY.json', value['preserved_files'])
        self.assertEqual(value['parent_wait_inflight'], 0)
        drain.verify_snapshot(self.plan, value)

    def test_actual_next_cycle_started_is_not_a_boundary(self):
        io.write(self.root/'cycle011/SHARED_BEFORE.json', dict(started=True))
        self.assertIsNone(drain.snapshot(self.plan))

    def test_child_readout_inflight_does_not_admit(self):
        with patch.object(drain, 'live_children', return_value=[55]):
            self.assertIsNone(drain.snapshot(self.plan))

    def test_checkpoint_reload_transition_waits_for_full_readout(self):
        self.rewrite(self.common/'STATE.json', lambda value: value.update(generation=1))
        self.assertIsNone(drain.snapshot(self.plan))

    def test_partial_sleep_or_DEV_never_admits(self):
        io.write(self.cycle/'SHARED_SLEEP.json', dict(status='COMPLETE'))
        self.assertIsNone(drain.snapshot(self.plan))

    def test_complete_checkpoint_DEV_boundary_allowed(self):
        self.rewrite(self.common/'STATE.json', lambda value: value.update(generation=1))
        checkpoint = dict(path_sha256='b'*64)
        io.write(self.cycle/'SHARED_SLEEP.json', dict(status='COMPLETE', publication=checkpoint))
        io.write(self.common/'generation_000000/sleep/COMPLETE.json',
                 dict(state=dict(generation=1, checkpoint=checkpoint), same_optimizer=True))
        readout = self.root/'readouts/cycle_010'
        for number in range(7, 27):
            io.write(readout/f'CALL_{number:04d}.json', dict(status='COMPLETE'))
        io.write(self.root/'reservations/native_0007.json', dict(kind='native', first=7, count=20))
        self.rewrite(self.root/'COUNTERS.json', lambda value: value.update(native=26))
        io.write(self.cycle/'COMPLETE.json', dict(counters=dict(native=26, parent=6), shared_generation=1))
        for name in ('AFTER.json', 'MOUNTED_FINAL.json'):
            io.write(readout/name, {})
        io.write(readout/'COMPLETE.json', dict(actual_native=20, shared_generation=1))
        value = drain.snapshot(self.plan)
        self.assertEqual(value['kind'], 'COMPLETE_SHARED_CHECKPOINT_AND_FRESH_DEV_CYCLE')
        self.assertEqual(value['counters']['native'], 26)

    def test_unfinished_or_late_provider_waits(self):
        (self.root/'parent_queue/C010_parent_6.response.json').unlink()
        self.assertIsNone(drain.snapshot(self.plan))

    def test_no_legacy_morning_final_attempt_allowed(self):
        io.write(self.root/'shared_readout_bindings/morning_final_000.json', {})
        self.assertIsNone(drain.snapshot(self.plan))

    def test_historical_sleep0_is_not_morning_replay(self):
        io.write(self.root/'sealed/sleep0_final_000/COMPLETE.json', {})
        self.assertIsNotNone(drain.snapshot(self.plan))

    def test_post_snapshot_charge_or_carry_mutation_rejected(self):
        value = drain.snapshot(self.plan)
        self.rewrite(self.cycle/'BOUNDARY.json', lambda document: document.update(own_reflection='changed'))
        with self.assertRaisesRegex(ValueError, 'preserved_source_or_carry_changed'):
            drain.verify_snapshot(self.plan, value)

    def test_partial_json_while_native_writes_resumes_not_terminal(self):
        (self.cycle/'TRAIN_COMPLETE.json').write_text('{')
        self.assertIsNone(drain.safe_snapshot(self.plan))


class SignalTests(unittest.TestCase):
    def setUp(self):
        self.plan = dict(native=dict(pid=21, uid=os.getuid()), guard=dict(pid=20, uid=os.getuid()), output='/synthetic')

    def test_no_signal_or_pidfd_before_future_window(self):
        with patch.object(os, 'pidfd_open') as opened, patch.object(signal, 'pidfd_send_signal') as sent:
            with self.assertRaisesRegex(ValueError, 'future_drain_clock_gate'):
                drain.held_release(self.plan, Mock(), clock=lambda:drain.START-1)
        opened.assert_not_called()
        sent.assert_not_called()

    def test_no_signal_after_last_safe_attempt(self):
        with patch.object(signal, 'pidfd_send_signal') as sent:
            with self.assertRaises(ValueError):
                drain.held_release(self.plan, Mock(), clock=lambda:drain.LAST_ATTEMPT)
        sent.assert_not_called()

    def test_old_CPU_timer_is_not_signalled_now_either(self):
        with patch.object(signal, 'pidfd_send_signal') as sent, patch.object(os, 'pidfd_open') as opened:
            with self.assertRaisesRegex(ValueError, 'future_drain_clock_gate'):
                drain.retire_timer({}, clock=lambda:drain.START-1)
        sent.assert_not_called()
        opened.assert_not_called()

    def test_PID_reuse_or_exec_drift_blocks_before_signal(self):
        with patch.object(drain, 'identity', return_value=dict(pid=20, uid=-1)), \
                patch.object(signal, 'pidfd_send_signal') as sent:
            with self.assertRaisesRegex(ValueError, 'exact_own_process'):
                drain.held_release(self.plan, Mock(), clock=lambda:drain.START)
        sent.assert_not_called()

    def test_failed_held_recheck_resumes_both_and_never_terminates(self):
        def expected(pid):
            return self.plan['guard' if pid==20 else 'native']
        with patch.object(drain, 'identity', side_effect=expected), patch.object(os, 'pidfd_open', side_effect=[100, 101]), \
                patch.object(os, 'close'), patch.object(drain.pinned, 'process_state', return_value='T'), \
                patch.object(signal, 'pidfd_send_signal') as sent:
            self.assertIsNone(drain.held_release(self.plan, lambda:None, clock=lambda:drain.START))
        self.assertEqual(sorted(call.args for call in sent.call_args_list), sorted([
            (100, signal.SIGSTOP), (101, signal.SIGSTOP), (100, signal.SIGCONT), (101, signal.SIGCONT)]))

    def test_exception_during_hold_resumes_both(self):
        def expected(pid):
            return self.plan['guard' if pid==20 else 'native']
        with patch.object(drain, 'identity', side_effect=expected), patch.object(os, 'pidfd_open', side_effect=[100, 101]), \
                patch.object(os, 'close'), patch.object(drain.pinned, 'process_state', return_value='T'), \
                patch.object(signal, 'pidfd_send_signal') as sent:
            with self.assertRaisesRegex(RuntimeError, 'synthetic_inspection'):
                drain.held_release(self.plan, Mock(side_effect=RuntimeError('synthetic_inspection')), clock=lambda:drain.START)
        self.assertEqual(sum(call.args[1] == signal.SIGCONT for call in sent.call_args_list), 2)
        self.assertFalse(any(call.args[1] in (signal.SIGTERM, signal.SIGKILL) for call in sent.call_args_list))

    def test_real_pidfds_leave_foreign_sentinel_untouched(self):
        with tempfile.TemporaryDirectory() as temporary:
            children = [subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)']) for unused in range(3)]
            try:
                time.sleep(.05)
                plan = dict(guard=drain.identity(children[0].pid), native=drain.identity(children[1].pid), output=temporary)
                snapshot = dict(kind='SYNTHETIC_CPU_BOUNDARY')
                result = drain.held_release(plan, lambda:snapshot, clock=lambda:drain.START)
                self.assertEqual(result, snapshot)
                self.assertIsNotNone(children[0].poll())
                self.assertIsNotNone(children[1].poll())
                self.assertIsNone(children[2].poll())
            finally:
                for child in children:
                    if child.poll() is None:
                        child.terminate()
                    child.wait(timeout=5)


if __name__ == '__main__':
    unittest.main()
