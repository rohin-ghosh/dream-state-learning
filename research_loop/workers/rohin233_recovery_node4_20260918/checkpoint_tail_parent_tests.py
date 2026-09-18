"""Synthetic CPU receiving checks; no live observer, parent, or journal writes."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import checkpoint_tail_parent_binding as binding_module
from checkpoint_tail_parent_binding import (COMPLETE_INDEX, COMPLETE_SHA, CONTROL, JOURNAL,
    OPTIMIZER_STEPS, ORIGINAL_SOURCE, ROOT, STATE_SHA, WALL, observe, source_pins, verify_documents)
from checkpoint_tail_parent_continue import validate_inputs
from checkpoint_tail_parent_prepare import proposed_config


class CheckpointTailParentTests(unittest.TestCase):
    def documents(self):
        source = str(CONTROL.parent / 'source')
        actual = dict(pid=92001, start_ticks='123456', uid=2524, cwd=source,
            argv=['python', '-B', '-m', 'gpu.orch_r125_continual_guard', 'native', '--config', str(CONTROL / 'GUARD.json')],
            cgroup='synthetic-only')
        authorization = dict(previous_stream_sha256=STATE_SHA, new_deadline_unix=WALL)
        plan = dict(root=ROOT, source_root=source, hard_end_unix=WALL,
            authorized_wall_extension=authorization,
            checkpoint_tail_recovery=dict(policy='R233_PINNED_COMPLETE_TAIL_V1',
                root=str(Path(ROOT) / 'stream'), journal_id=JOURNAL,
                complete_index=COMPLETE_INDEX, complete_sha256=COMPLETE_SHA))
        binding = dict(status='LOADED', root=ROOT, guard_path=str(CONTROL / 'GUARD.json'),
            hard_end_unix=WALL, identity=deepcopy(actual), native=dict(pid=92001, start_ticks='123456'),
            plan_sha256='plan', loaded=dict(index=11505, sha256='load'), wall_extended=dict(index=11504, sha256='wall'))
        loaded = dict(journal_id=JOURNAL, index=11505, sha256='load', kind='LOADED',
            document=dict(pid=92001, resume=True, optimizer_steps=OPTIMIZER_STEPS))
        wall = dict(journal_id=JOURNAL, index=11504, sha256='wall', kind='WALL_EXTENDED',
            document=dict(plan_sha256='plan', authorization=authorization))
        return binding, plan, actual, loaded, wall

    def test_actual_new_incarnation_and_wall_accepted(self):
        verify_documents(*self.documents(), WALL - 3600)

    def test_pid_reuse_or_old_control_rejected(self):
        for change in ('start', 'pid', 'control', 'source', 'uid'):
            with self.subTest(change=change):
                binding, plan, actual, loaded, wall = self.documents()
                if change == 'start':
                    actual['start_ticks'] = 'reused'
                elif change == 'pid':
                    actual['pid'] = 829798
                elif change == 'control':
                    actual['argv'][-1] = binding_module.ORIGINAL_GUARD
                elif change == 'source':
                    actual['cwd'] = ORIGINAL_SOURCE
                else:
                    actual['uid'] = 0
                with self.assertRaises(ValueError):
                    verify_documents(binding, plan, actual, loaded, wall, WALL - 3600)

    def test_unbound_or_wrong_loaded_receipt_rejected(self):
        for change in ('optimizer', 'resume', 'pid', 'journal', 'hash', 'pending'):
            with self.subTest(change=change):
                binding, plan, actual, loaded, wall = self.documents()
                if change == 'optimizer':
                    loaded['document']['optimizer_steps'] -= 1
                elif change == 'resume':
                    loaded['document']['resume'] = False
                elif change == 'pid':
                    loaded['document']['pid'] = 829798
                elif change == 'journal':
                    loaded['journal_id'] = 'different'
                elif change == 'hash':
                    loaded['sha256'] = 'different'
                else:
                    binding['status'] = 'DISPATCHED'
                with self.assertRaises(ValueError):
                    verify_documents(binding, plan, actual, loaded, wall, WALL - 3600)

    def test_stale_boundary_wrong_plan_and_wall_rejected(self):
        for change in ('anchor', 'source_state', 'plan', 'wall', 'ordering', 'expired'):
            with self.subTest(change=change):
                binding, plan, actual, loaded, wall = deepcopy(self.documents())
                now = WALL - 1
                if change == 'anchor':
                    plan['checkpoint_tail_recovery']['complete_index'] -= 1
                elif change == 'source_state':
                    wall['document']['authorization']['previous_stream_sha256'] = 'different'
                elif change == 'plan':
                    wall['document']['plan_sha256'] = 'different'
                elif change == 'wall':
                    plan['hard_end_unix'] -= 1
                elif change == 'ordering':
                    wall['index'] = loaded['index'] + 1
                else:
                    now = WALL
                with self.assertRaises(ValueError):
                    verify_documents(binding, plan, actual, loaded, wall, now)

    def test_pending_observation_never_becomes_ready_or_starts_parent(self):
        unused, plan, actual, loaded, wall = self.documents()
        guard = dict(plan_sha256='plan', source_pins={'module.py': 'hash'})
        anchor = dict(sha256=COMPLETE_SHA, kind='SLEEP_COMPLETE',
            document=dict(resume_state=dict(sha256=STATE_SHA)))
        suffix = dict(sha256=binding_module.SUFFIX_SHA, kind='R184_LEARN_COMPLETE', previous_sha256=COMPLETE_SHA)
        with patch.object(binding_module, 'control_documents', return_value=(guard, plan)), \
                patch.object(binding_module, 'identity', return_value=actual), \
                patch.object(binding_module, 'read_record', side_effect=[anchor, suffix]), \
                patch.object(binding_module.Path, 'exists', return_value=False), \
                patch.object(binding_module, 'sha', side_effect=['guard', 'plan']), \
                patch.object(binding_module, 'read', return_value=guard), \
                patch.object(binding_module.time, 'time', return_value=WALL - 1):
            result = observe(actual['pid'], actual['start_ticks'], 'guard')
        self.assertEqual(result['status'], 'PENDING_ACTUAL_LOAD')
        self.assertEqual(result['native_signals'], [])
        self.assertEqual(result['journal_writes'], 0)
        self.assertFalse(result['parent_started'])
        self.assertNotIn('loaded', result)

    def test_original_parent_view_and_cursor_preserved(self):
        binding = self.documents()[0]
        old = dict(root=ROOT, source_root=ORIGINAL_SOURCE, hard_end_unix=WALL - 86400,
            start_after_response_count=289, cadence_responses=1, parent_style='unchanged',
            reading_classifier_source=ORIGINAL_SOURCE, existing_parent_lock='/synthetic/original-lock')
        new = proposed_config(old, binding, '/synthetic/binding.json', 'bound', 777, 'predecessor')
        self.assertEqual(new['start_after_response_count'], 777)
        for key in ('source_root', 'root', 'cadence_responses', 'parent_style', 'reading_classifier_source', 'existing_parent_lock'):
            self.assertEqual(new[key], old[key])
        self.assertEqual(new['hard_end_unix'], WALL)
        pending = dict(binding, status='PENDING_ACTUAL_LOAD')
        with self.assertRaisesRegex(ValueError, 'actual_new_C2_LOADED'):
            proposed_config(old, pending, '/synthetic/binding.json', 'bound', 777, 'predecessor')

    def test_source_pins_reject_mutation_and_outside_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'module.py'
            path.write_text('synthetic')
            pins = {'module.py': hashlib.sha256(path.read_bytes()).hexdigest()}
            source_pins(directory, pins)
            path.write_text('changed')
            with self.assertRaisesRegex(ValueError, 'exact_bound_source_bytes'):
                source_pins(directory, pins)
            with self.assertRaisesRegex(ValueError, 'relative_source_pin'):
                source_pins(directory, {'../module.py': 'hash'})

    def test_parent_wrapper_rejects_changed_behavior_and_output_reuse(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            old = dict(root=ROOT, source_root=ORIGINAL_SOURCE, hard_end_unix=WALL - 86400,
                start_after_response_count=289, cadence_responses=1)
            proposed = dict(old, hard_end_unix=WALL)
            (root / 'old.json').write_text(json.dumps(old))
            (root / 'new.json').write_text(json.dumps(proposed))
            manifest = dict(local_source_sha256={}, config_path=str(root / 'new.json'),
                predecessor_config_path=str(root / 'old.json'), output=str(root / 'run'))
            self.assertEqual(validate_inputs(manifest), proposed)
            (root / 'run').mkdir()
            with self.assertRaisesRegex(ValueError, 'no_reuse_of_parent_output'):
                validate_inputs(manifest)
            proposed['cadence_responses'] = 2
            (root / 'new.json').write_text(json.dumps(proposed))
            with self.assertRaisesRegex(ValueError, 'behavior_and_sources_unchanged'):
                validate_inputs(manifest)


if __name__ == '__main__':
    unittest.main(verbosity=2)
