import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from gpu import orch_l2_adjacent_run as run
from organism_v6 import orch_l2_adjacent as adjacent


class AdjacentTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.initial = dict(path='/synthetic/initial', state_sha256=adjacent.shared.INITIAL_STATE,
                            base_sha256=adjacent.BASE_SHA, files=[['adapter.bin', 'a' * 64]])
        self.cohort = dict(held=[[dict(master=f'synthetic-{stage}-{index}',
            edges=[dict(event=f'event-{stage}-{index}')]) for index in range(8)] for stage in range(4)])
        run.write(self.root / 'INITIAL.json', self.initial)
        run.write(self.root / 'COHORT.json', self.cohort)

    def sleep(self, cycle, updates, previous=None, output=None, arm='SHORT'):
        previous = previous or self.initial
        output = output or (dict(previous, path=f'/synthetic/output{cycle}', state_sha256='b' * 64)
                            if updates else previous)
        folder = self.root / arm / f'cycle{cycle}' / 'sleep'
        receipt = dict(status='COMPLETE', arm=arm, cycle=cycle, phase='sleep', updates=updates,
                       fits=int(updates > 0), unchanged=previous['state_sha256'] == output['state_sha256'],
                       input_adapter=previous, output_adapter=output, process=['synthetic-boot', 100, 200])
        run.write(folder / 'COMPLETE.json', receipt)
        if updates:
            run.write(folder / 'LOADED.json', dict(observed=previous, phase='sleep', process=receipt['process']))
            (folder / 'LOSSES.jsonl').write_text(''.join(json.dumps(dict(update=index, loss=1.0)) + '\n'
                                                       for index in range(1, updates + 1)))
        return receipt

    def test_missing_first_sleep_never_skips_to_later_or_unparented(self):
        self.sleep(1, 2, arm='UNPARENTED')
        self.sleep(2, 2)
        result = adjacent.select_first(self.root)
        self.assertEqual(result['status'], 'WAITING_SHORT_SLEEP')
        self.assertEqual(result['cycle'], 1)

    def test_first_actual_update_after_null_is_selected(self):
        self.sleep(1, 0)
        self.sleep(2, 2)
        result = adjacent.select_first(self.root)
        self.assertEqual(result['cycle'], 2)
        self.assertEqual(result['previous'], self.initial)
        self.assertEqual(result['held_sha256'], adjacent.digest(self.cohort['held'][2]))
        self.assertEqual([entry['updates'] for entry in result['checked']], [0, 2])

    def test_later_positive_sleep_cannot_replace_first(self):
        first = self.sleep(1, 2)
        self.sleep(2, 3, previous=first['output_adapter'])
        self.assertEqual(adjacent.select_first(self.root)['cycle'], 1)

    def test_all_three_nulls_deallocate_without_calls(self):
        for cycle in (1, 2, 3):
            self.sleep(cycle, 0)
        result = adjacent.select_first(self.root)
        self.assertEqual(result['status'], 'DEALLOCATED_ALL_THREE_SHORT_SLEEPS_ZERO')
        self.assertEqual(result['native_calls'], 0)

    def test_identical_saved_hashes_with_actual_updates_are_valid(self):
        self.sleep(1, 2, output=dict(self.initial, path='/synthetic/saved-identical'))
        self.assertEqual(adjacent.select_first(self.root)['status'], 'SELECTED')

    def test_zero_update_cannot_change_child(self):
        self.sleep(1, 0, output=dict(self.initial, path='/synthetic/changed'))
        with self.assertRaisesRegex(ValueError, 'zero_update_must_preserve_child'):
            adjacent.select_first(self.root)

    def test_optimizer_ledger_must_match_actual_count(self):
        self.sleep(1, 2)
        (self.root / 'SHORT/cycle1/sleep/LOSSES.jsonl').write_text('{"update": 1, "loss": 1.0}\n')
        with self.assertRaisesRegex(ValueError, 'actual_optimizer_ledger_mismatch'):
            adjacent.select_first(self.root)

    def test_nonfinite_loss_rejected(self):
        self.sleep(1, 1)
        (self.root / 'SHORT/cycle1/sleep/LOSSES.jsonl').write_text('{"update": 1, "loss": NaN}\n')
        with self.assertRaisesRegex(ValueError, 'actual_optimizer_ledger_mismatch'):
            adjacent.select_first(self.root)

    def test_native_loaded_identity_is_required(self):
        self.sleep(1, 2)
        path = self.root / 'SHORT/cycle1/sleep/LOADED.json'
        document = adjacent.read(path)
        document['observed']['state_sha256'] = 'c' * 64
        run.write(path, document)
        with self.assertRaisesRegex(ValueError, 'actual_mounted_input_drift'):
            adjacent.select_first(self.root)

    def test_lineage_cannot_substitute_another_previous_adapter(self):
        self.sleep(1, 2, previous=dict(self.initial, path='/synthetic/wrong'))
        with self.assertRaisesRegex(ValueError, 'immediate_previous_child_drift'):
            adjacent.select_first(self.root)

    def test_selection_never_opens_any_held_result(self):
        self.sleep(1, 2)
        reads = []
        original = adjacent.read

        def allowed(path):
            reads.append(str(path))
            self.assertNotIn('/readout/', str(path))
            return original(path)

        with patch.object(adjacent, 'read', side_effect=allowed):
            self.assertEqual(adjacent.select_first(self.root)['status'], 'SELECTED')
        self.assertTrue(reads)

    def test_original_outcomes_inaccessible_before_binding(self):
        with patch.object(adjacent, 'read') as reader:
            with self.assertRaisesRegex(ValueError, 'bind_selection_before_original_outcomes'):
                adjacent.original_counts('/forbidden', dict(status='WAITING_SHORT_SLEEP'))
            reader.assert_not_called()

    def test_selection_file_is_immutable(self):
        self.sleep(1, 2)
        run.select(self.root / 'own', self.root)
        self.sleep(1, 3)
        with self.assertRaisesRegex(ValueError, 'immutable_adjacent_binding_changed'):
            run.select(self.root / 'own', self.root)

    def test_exact_fixed_evaluator_fits_without_omission(self):
        legacy = dict(old_bank=[{}] * 16, old_episodes=[{}] * 16,
                      held=dict(cases=[{}] * 16, expected_calls=16))
        with patch.object(adjacent.shared, 'tasks', return_value=[{}, {}]):
            result = adjacent.budget(self.cohort, legacy)
            self.assertEqual(result['worst_case_total'], 288)
            self.assertEqual(result['lifetime_cap'], 512)
            legacy['old_bank'].pop()
            with self.assertRaisesRegex(ValueError, 'fixed_W0_W8_denominators'):
                adjacent.budget(self.cohort, legacy)

    def test_audit_size_or_evaluator_overflow_rejected_before_calls(self):
        legacy = dict(old_bank=[{}] * 16, old_episodes=[{}] * 16,
                      held=dict(cases=[{}] * 17, expected_calls=17))
        with patch.object(adjacent.shared, 'tasks', return_value=[{}, {}]):
            with self.assertRaisesRegex(ValueError, 'fixed_audit_denominator'):
                adjacent.budget(self.cohort, legacy)
            legacy['held'] = dict(cases=[{}] * 16, expected_calls=16)
            with patch.dict(adjacent.shared.CAPS, child_turns_per_episode=20):
                with self.assertRaisesRegex(ValueError, 'exact_evaluator_exceeds_lifetime_cap_before_calls'):
                    adjacent.budget(self.cohort, legacy)

    def test_failed_routing_keeps_fixed_counts_and_neutral_world_local_inputs(self):
        store = {f'event-1-{index}': f'raw-{index}' for index in range(7)}
        store['other-world'] = 'must-not-leak'
        emitted = []

        def episode(world, task, generate, local_store, **kwargs):
            self.assertIsNone(kwargs['parent'])
            self.assertFalse(kwargs['rich_contract'])
            self.assertNotIn('other-world', local_store)
            self.assertLessEqual(len(local_store), 1)
            return dict(correct=False, task=task, terminal_reason='capture_error', captures=[dict(response=None)])

        with patch.object(adjacent.shared, 'verify_source', return_value=store), \
                patch.object(adjacent.shared, 'tasks', return_value=[{'goal': 'left'}, {'goal': 'right'}]), \
                patch.object(adjacent.guided, 'episode', side_effect=episode):
            result = adjacent.routing(self.cohort, {}, 1, Mock(), lambda name, value: emitted.append(value))
        self.assertEqual(result['episodes'], 16)
        self.assertEqual(result['successes'], 0)
        self.assertEqual(result['world_denominator'], 8)
        self.assertEqual(len(emitted), 16)

    def test_shared_budget_reserves_before_failed_attempt_and_never_overruns(self):
        for attempt in range(2):
            self.assertEqual(run.spend(self.root, 'ADJACENT', 2, dict(failed_attempt=attempt)), attempt)
        with self.assertRaisesRegex(ValueError, 'call_budget_exhausted'):
            run.spend(self.root, 'ADJACENT', 2, {})
        self.assertEqual(len((self.root / 'CALLS_ADJACENT.jsonl').read_text().splitlines()), 2)

    def test_retention_and_audit_use_existing_callbacks_without_coaching(self):
        from gpu import astra_goal_quality_train as old

        legacy = dict(old_bank=[dict(event='synthetic-event')],
                      old_episodes=[dict(event=dict(raw='synthetic-raw'))], held=dict(cases=['synthetic-case']))
        generate, emitted = Mock(), []
        with patch.object(adjacent, 'routing', return_value=dict(episodes=16)), \
                patch.object(old.memory, 'recall', return_value={'0': {}, '8': {}}) as recall, \
                patch.object(old.memory.audit, 'collect_cases', return_value=dict(summary={'overall': {}})) as audit:
            result = adjacent.evaluate({}, {}, legacy, 1, generate, self.root,
                                       lambda name, value: emitted.append((name, value)))
        recall.assert_called_once_with([dict(event='synthetic-event', raw='synthetic-raw')], generate, self.root, 'OLD')
        audit.assert_called_once_with(legacy['held'], generate, coached=False)
        self.assertEqual(result['audit'], {'overall': {}})
        self.assertEqual(emitted[0][0], 'AUDIT.json')

    def test_original_counts_must_match_selected_cycle_and_output_identity(self):
        self.sleep(1, 2)
        selection = adjacent.select_first(self.root)
        path = self.root / 'original.json'
        run.write(path, dict(status='COMPLETE', arm='SHORT', phase='readout', cycle=2))
        with self.assertRaisesRegex(ValueError, 'matching_original_readout'):
            adjacent.original_counts(path, selection)

    def test_assigned_GPU_with_existing_owner_is_not_loaded_or_killed(self):
        expected = run.DEVICES['PREVIOUS'][1]
        with patch.object(run.subprocess, 'check_output', side_effect=[expected + '\n', expected + ', 123\n']):
            with self.assertRaisesRegex(ValueError, 'assigned_GPU_has_existing_owner'):
                run.device_free('PREVIOUS')

    def test_tokenizer_and_config_are_bound_to_original_files(self):
        names = ('config.json', 'generation_config.json', 'tokenizer.json',
                 'tokenizer_config.json', 'special_tokens_map.json')
        reference = {name: None for name in names}
        self.assertEqual(run.verify_model_files(self.root, reference), reference)
        (self.root / 'tokenizer.json').write_text('different')
        with self.assertRaisesRegex(ValueError, 'original_SHORT_tokenizer_or_config_drift'):
            run.verify_model_files(self.root, reference)

    def test_deadline_abort_is_not_swallowed_as_an_episode_error(self):
        self.assertFalse(issubclass(run.StopNative, Exception))

    def test_lifetime_cannot_restart_or_create_extra_processes(self):
        run.write(self.root / 'SELECTION.json', dict(status='SELECTED'))
        run.write(self.root / 'PREPARE_ADJACENT.json', dict(selection=dict(status='SELECTED')))
        run.write(self.root / 'LIFETIME.json', dict(started_unix=1))
        with patch.object(run, 'own_root', return_value=self.root), patch.object(run, 'device_free'), \
                patch.object(run.subprocess, 'Popen') as popen:
            with self.assertRaises(FileExistsError):
                run.launch(self.root)
            popen.assert_not_called()

    def test_exact_UUID_ownership_and_no_name_kills(self):
        process = Mock(pid=123)
        process.poll.return_value = None
        with patch.object(run, 'process_start', return_value=999):
            with self.assertRaisesRegex(ValueError, 'PID_reuse_do_not_signal'):
                run.terminate_owned(process, 998)
        process.send_signal.assert_not_called()
        with patch.object(run.subprocess, 'check_output', return_value='GPU-wrong\n'):
            with self.assertRaisesRegex(ValueError, 'assigned_physical_UUID_drift'):
                run.device_free('PREVIOUS')


if __name__ == '__main__':
    unittest.main()
