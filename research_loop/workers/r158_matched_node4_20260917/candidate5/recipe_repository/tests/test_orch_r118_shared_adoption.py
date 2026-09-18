import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from gpu import orch_r118_shared_adoption as adoption


class SharedAdoptionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.common = self.root / 'shared'
        self.entries = {}
        for branch in adoption.shared.BRANCHES:
            root = self.root / branch
            source = root / 'source'
            source.mkdir(parents=True)
            module = adoption.MODULES[branch]
            module_path = module.replace('.', '/') + '.py'
            target = source / module_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text('pass\n')
            coordinator = source / 'gpu/orch_r116_shared_learner.py'
            coordinator.write_bytes(Path(adoption.shared.__file__).read_bytes())
            files = {name: adoption.shared.sha(source / name) for name in
                     (module_path, 'gpu/orch_r116_shared_learner.py')}
            tests = root / 'CPU.json'
            adoption.shared.write(tests, dict(passed=True, cuda_initialized=False, source_files=files))
            ready = dict(schema='R116_SHARED_CLIENT_READY_V2' if branch in ('F1', 'A1') else
                         'R116_SHARED_CLIENT_READY_V1', branch=branch, root=str(root),
                successor_source=str(source), source_files=files, common_root=str(self.common),
                command_module=module, ready_for_initialization=True, active_shared_client=False,
                optimizer_owner='F1', original_counters_preserved=True, empty_successor_cursor_resume=True,
                train_ids=[branch + '_one', branch + '_two'], excluded_ids=[branch + '_DEV', branch + '_FINAL'],
                tests_receipt=adoption.reference(tests), inherited_bounds=dict(cycles=43, hard_end_unix=1234))
            path = root / 'SHARED_CLIENT_READY.json'
            adoption.shared.write(path, ready)
            self.entries[branch] = adoption.reference(path)
        checkpoint = self.root / 'CHECKPOINT.json'
        optimizer = self.root / 'optimizer_rng.pt'
        checkpoint.write_text('{}')
        optimizer.write_bytes(b'test-only optimizer placeholder')
        self.current = dict(checkpoint=dict(path=str(checkpoint), path_sha256=adoption.shared.sha(checkpoint),
            optimizer_path=str(optimizer), optimizer_path_sha256=adoption.shared.sha(optimizer)),
            prior_metrics=dict(optimizer_steps=382, child_token_exposures=26505, anchor_token_exposures=None),
            initial_history={'F1': []}, source_receipts=[], no_lifetime_reset=True)
        self.current['initial_history']['F1'].append(self.history_row())
        branches = {}
        for branch in adoption.shared.BRANCHES:
            root = self.root / branch
            release = root / 'RELEASED.json'
            adoption.shared.write(release, dict(status='RELEASED', root=str(root)))
            state = root / 'CARRY.json'
            state.write_text('{}')
            branches[branch] = dict(root=str(root), bounds=dict(cycles=43, hard_end_unix=1234),
                release=adoption.reference(release), predecessors=[dict(pid=1000000000)],
                preserved_files={'CARRY.json': adoption.shared.sha(state)}, next_cycle=4)
        self.handoff_path = self.root / 'HANDOFF.json'
        self.handoff = dict(schema='R118_SHARED_HANDOFF_V1', readiness=self.entries, branches=branches,
                            latest_F1_checkpoint=self.current['checkpoint'])
        adoption.shared.write(self.handoff_path, self.handoff)

    def history_row(self):
        messages = [dict(role='user', content='Public task and environment feedback')]
        response = dict(raw='A recorded learner continuation', token_ids=[3, 4], prompt_tokens=12,
                        messages=messages, terminal=True, truncated=False)
        hashed = adoption.shared.replay.history_policy.digest(messages)
        path = self.root / 'F1/call.json'
        adoption.shared.write(path, dict(phase='reflection', split='TRAIN', task_id='F1_one',
            messages=messages, messages_sha256=hashed, response=response))
        return dict(replay_mode=adoption.shared.replay.MODE, student_prefix=messages,
            source_prompt_sha256=hashed, source_prompt_tokens=12, target=response['raw'],
            target_sha256=adoption.shared.replay.history_policy.text_sha(response['raw']),
            source_generated_token_ids=[3, 4], append_eos=True, continuation_only=False,
            source_call_path=str(path), source_call_sha256=adoption.shared.sha(path), episode_id='F1_one')

    def change_ready(self, branch, **changes):
        path = Path(self.entries[branch]['path'])
        value = adoption.shared.read(path)
        value.update(changes)
        path.write_text(json.dumps(value))
        self.entries[branch] = adoption.reference(path)

    def handoff_binding(self):
        self.handoff_path.write_text(json.dumps(self.handoff))
        return adoption.reference(self.handoff_path)

    def adopt(self):
        with patch.object(adoption.route, 'adoption_inputs', return_value=copy.deepcopy(self.current)):
            return adoption.adopt(self.entries, self.common, self.handoff_binding())

    def test_eight_runnable_without_starting_or_initializing(self):
        result = adoption.readiness(self.entries, self.common)
        self.assertEqual(set(result['branch_specs']), set(adoption.shared.BRANCHES))
        self.assertFalse(result['active'])
        self.assertFalse(self.common.exists())

    def test_helper_only_readiness_rejected(self):
        self.change_ready('F2', command_module='gpu.orch_math_feedback_uptake_r117_shared')
        with self.assertRaisesRegex(ValueError, 'runnable_successor_not_client_helper'):
            adoption.readiness(self.entries, self.common)

    def test_old_route_v1_readiness_rejected(self):
        self.change_ready('F1', schema='R116_SHARED_CLIENT_READY_V1')
        with self.assertRaisesRegex(ValueError, 'route_v2'):
            adoption.readiness(self.entries, self.common)

    def test_not_all_eight_rejected(self):
        self.entries.pop('A4')
        with self.assertRaisesRegex(ValueError, 'all_eight'):
            adoption.readiness(self.entries, self.common)

    def test_tampered_readiness_rejected(self):
        Path(self.entries['F4']['path']).write_text('{}')
        with self.assertRaisesRegex(ValueError, 'artifact_binding'):
            adoption.readiness(self.entries, self.common)

    def test_changed_source_rejected(self):
        (self.root / 'F3/source/gpu/orch_r108_code_parent_r116_shared_run.py').write_text('changed')
        with self.assertRaisesRegex(ValueError, 'source_binding'):
            adoption.readiness(self.entries, self.common)

    def test_cross_branch_held_contamination_rejected(self):
        self.change_ready('F2', excluded_ids=['F1_one'])
        with self.assertRaisesRegex(ValueError, 'cross_branch_DEV_FINAL'):
            adoption.readiness(self.entries, self.common)

    def test_cpu_test_source_mismatch_rejected(self):
        ready = adoption.shared.read(self.entries['F2']['path'])
        path = Path(ready['tests_receipt']['path'])
        tests = adoption.shared.read(path)
        tests['source_files'] = {}
        path.write_text(json.dumps(tests))
        self.change_ready('F2', tests_receipt=adoption.reference(path))
        with self.assertRaisesRegex(ValueError, 'tested_source_closure'):
            adoption.readiness(self.entries, self.common)

    def test_unreleased_process_rejected(self):
        self.handoff['branches']['A3']['predecessors'] = [dict(pid=os.getpid())]
        with self.assertRaisesRegex(ValueError, 'predecessor_still_alive'):
            self.adopt()
        self.assertFalse(self.common.exists())

    def test_changed_boundary_file_rejected(self):
        (self.root / 'A1/CARRY.json').write_text('changed')
        with self.assertRaisesRegex(ValueError, 'preserved_boundary_bytes'):
            self.adopt()

    def test_bounds_cannot_be_extended(self):
        self.handoff['branches']['F2']['bounds']['cycles'] = 96
        with self.assertRaisesRegex(ValueError, 'lifetime_reset'):
            self.adopt()

    def test_old_f1_candidate_cannot_be_adopted(self):
        self.handoff['latest_F1_checkpoint'] = dict(self.current['checkpoint'], path_sha256='historical')
        with self.assertRaisesRegex(ValueError, 'latest_released_F1'):
            self.adopt()

    def test_adoption_preserves_optimizer_history_and_unknown_counts(self):
        result = self.adopt()
        config = adoption.shared.read(self.common / 'CONFIG.json')
        self.assertEqual(config['initial_checkpoint'], self.current['checkpoint'])
        self.assertEqual(config['initial_history'], self.current['initial_history'])
        self.assertEqual(config['pretransition_metrics'], self.current['prior_metrics'])
        self.assertEqual(result['state']['shared_optimizer_steps'], 0)
        self.assertIsNone(result['state']['anchor_token_exposures'])
        self.assertEqual(result['actors_launched'], 0)
        self.assertEqual(result['optimizer_updates'], 0)

    def test_retry_does_not_initialize_twice(self):
        first = self.adopt()
        self.assertEqual(first, self.adopt())

    def test_changed_handoff_cannot_replace_adoption(self):
        self.adopt()
        self.handoff['branches']['A4']['next_cycle'] = 5
        with self.assertRaisesRegex(ValueError, 'adoption_is_immutable'):
            self.adopt()

    def test_parent_text_cannot_enter_adopted_history(self):
        self.current['initial_history']['F1'][0]['target'] = 'Substituted parent answer'
        with self.assertRaisesRegex(ValueError, 'actual_target_binding'):
            self.adopt()

    def test_dev_capture_cannot_enter_adopted_history(self):
        row = self.current['initial_history']['F1'][0]
        path = Path(row['source_call_path'])
        call = adoption.shared.read(path)
        call['split'] = 'DEV'
        path.write_text(json.dumps(call))
        row['source_call_sha256'] = adoption.shared.sha(path)
        with self.assertRaisesRegex(ValueError, 'held_split'):
            self.adopt()

    def test_wait_for_missing_release_never_initializes(self):
        output = self.root / 'ASSEMBLED.json'
        result = adoption.adopt_released_once(self.entries, self.common, output)
        self.assertEqual(set(result['missing']), set(adoption.shared.BRANCHES))
        self.assertFalse(output.exists())
        self.assertFalse(self.common.exists())

    def test_actual_certificates_initialize_once_without_actor_launch(self):
        for branch, certificate in self.handoff['branches'].items():
            adoption.shared.write(self.root / branch / 'R118_SHARED_HANDOFF_BRANCH.json', certificate)
        with patch.object(adoption.route, 'adoption_inputs', return_value=copy.deepcopy(self.current)):
            result = adoption.adopt_released_once(self.entries, self.common, self.root / 'ASSEMBLED.json')
        self.assertEqual(result['status'], 'INITIALIZED_NO_ACTORS_LAUNCHED')
        self.assertEqual(result['optimizer_updates'], 0)
        self.assertEqual(result['actors_launched'], 0)

    def test_watch_deadline_is_not_life_extension(self):
        with self.assertRaisesRegex(ValueError, 'future_watch_deadline'):
            adoption.watch(self.entries, self.common, self.root / 'ASSEMBLED.json', 0)
        self.assertFalse(self.common.exists())

    def test_invalid_release_status_does_not_adopt(self):
        path = self.root / 'F4/RELEASED.json'
        path.write_text(json.dumps(dict(status='PREPARED')))
        self.handoff['branches']['F4']['release'] = adoption.reference(path)
        with self.assertRaisesRegex(ValueError, 'release_and_lineage_evidence'):
            self.adopt()
        self.assertFalse(self.common.exists())


if __name__ == '__main__':
    unittest.main()
