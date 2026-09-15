from copy import deepcopy
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import Mock, patch

from gpu import orch_math_feedback_uptake_r118_final as final


class FinalTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.plan = dict(start_unix=final.START, end_unix=final.END, lease_end_unix=final.END+21600,
            native_cap=8, task_ids=list(final.FINAL_IDS), decoder=deepcopy(final.DECODER),
            final_file_sha256=final.FINAL_FILE_SHA, final_set_sha256=final.FINAL_SET_SHA)
        self.tasks = [dict(id=identifier, split='FINAL', question='Synthetic test question', answer='test')
                      for identifier in final.FINAL_IDS]

    def batch(self, prompts, cap):
        self.assertEqual(cap, 2048)
        self.assertEqual(final.read(self.root/'LEDGER.json')['native'], 8)
        self.assertEqual(len(list(self.root.glob('*.request.json'))), 8)
        return [dict(messages=prompt, raw='Complete reasoning before FINAL: test', token_ids=[3, 4, 5],
                     terminal=True, truncated=False, input_truncated=False) for prompt in prompts]

    def messages(self, task, purpose):
        self.assertEqual(purpose, 'held')
        return [dict(role='user', content=task['question'])]

    def capture(self, batch=None):
        with patch.object(final.time, 'time', return_value=final.START+10):
            return final.capture(self.root, self.plan, self.tasks, dict(path_sha256='a'*64),
                                 batch or self.batch, self.messages)

    def test_exact_clock_boundaries(self):
        for moment in (final.START-1, final.END, final.END+1):
            with self.subTest(moment=moment), self.assertRaisesRegex(ValueError, 'FINAL_clock_gate'):
                final.window(self.plan, moment)
        final.window(self.plan, final.START)
        final.window(self.plan, final.END-1)

    def test_earlier_lease_margin_is_binding(self):
        self.plan.update(lease_end_unix=final.START+21600+120, end_unix=final.START+120)
        final.window(self.plan, final.START+119)
        with self.assertRaises(ValueError):
            final.window(self.plan, final.START+120)
        self.plan['end_unix'] = final.END
        with self.assertRaisesRegex(ValueError, 'separate_absolute_window'):
            final.window(self.plan, final.START)

    def test_no_early_sealed_open_or_hash(self):
        with patch.object(final, 'read') as reader, patch.object(final, 'sha') as hasher:
            with self.assertRaisesRegex(ValueError, 'FINAL_clock_gate'):
                final.materialize(self.plan, final.START-1)
            reader.assert_not_called()
            hasher.assert_not_called()

    def test_materialize_checks_exact_ids_and_file_bytes(self):
        path = self.root/'sealed/FINAL8.json'
        final.write(path, self.tasks)
        self.plan.update(final_file_sha256=final.sha(path), final_set_sha256=final.digest(self.tasks))
        with patch.object(final, 'ORIGINAL', self.root):
            self.assertEqual(final.materialize(self.plan, final.START), self.tasks)
            self.plan['task_ids'] = list(reversed(final.FINAL_IDS))
            with self.assertRaisesRegex(ValueError, 'exact_sealed_eight'):
                final.materialize(self.plan, final.START)

    def test_sleep0_does_not_suppress_morning(self):
        (self.root/'sealed/sleep0_final_000').mkdir(parents=True)
        self.assertEqual(final.prior_attempts(self.root, final.START), [])

    def test_any_partial_or_completed_morning_prevents_replay(self):
        for folder in ('sealed/morning_final_000', 'shared_readout_bindings'):
            (self.root/folder).mkdir(parents=True)
        final.write(self.root/'shared_readout_bindings/morning_final_000.json', {'unstarted': True})
        self.assertEqual(len(final.prior_attempts(self.root, final.START)), 2)

    def test_charged_morning_without_capture_prevents_replay(self):
        final.write(self.root/'reservations/native_0999.json', dict(metadata=dict(phase='morning_final'), count=8))
        self.assertEqual(len(final.prior_attempts(self.root, final.START)), 1)
        with self.assertRaisesRegex(ValueError, 'no_early_FINAL_attempt_inspection'):
            final.prior_attempts(self.root, final.START-1)

    def test_full_text_and_tokens_saved_before_any_parser(self):
        self.capture()
        self.assertEqual(final.denominators(self.root)['completed_native'], 8)
        for number in range(1, 9):
            raw = final.read(self.root/f'CALL_{number:04d}.raw.json')['response']
            saved = final.read(self.root/f'CALL_{number:04d}.json')
            self.assertEqual(raw, saved['response'])
            self.assertIn('Complete reasoning', raw['raw'])
            self.assertEqual(raw['token_ids'], [3, 4, 5])
            self.assertEqual(saved['split'], 'FINAL')
            self.assertTrue(saved['never_rows_or_buffer'])

    def test_reserved_batch_failure_preserves_all_denominators(self):
        with self.assertRaisesRegex(RuntimeError, 'synthetic_generation_error'):
            self.capture(Mock(side_effect=RuntimeError('synthetic_generation_error')))
        counts = final.denominators(self.root)
        self.assertEqual((counts['charged_native'], counts['failed_or_partial_native'], counts['unattempted_native']), (8, 8, 0))
        self.assertEqual(len(list(self.root.glob('CALL_*.json'))), 16)

    def test_no_second_batch_or_ledger_reset(self):
        self.capture()
        batch = Mock()
        with self.assertRaises(FileExistsError):
            self.capture(batch)
        batch.assert_not_called()
        self.assertEqual(final.read(self.root/'LEDGER.json')['attempts'], 1)

    def test_truncated_response_is_retained_not_relabelled_EOS(self):
        def batch(prompts, cap):
            responses = self.batch(prompts, cap)
            responses[0].update(terminal=False, truncated=True, token_ids=[4]*2048)
            return responses
        self.capture(batch)
        response = final.read(self.root/'CALL_0001.json')['response']
        self.assertFalse(response['terminal'])
        self.assertTrue(response['truncated'])
        self.assertEqual(len(response['token_ids']), 2048)

    def test_invalid_response_retains_raw_and_failure_counts(self):
        def batch(prompts, cap):
            responses = self.batch(prompts, cap)
            responses[2]['input_truncated'] = True
            return responses
        with self.assertRaisesRegex(ValueError, 'full_native_response'):
            self.capture(batch)
        self.assertEqual(len(list(self.root.glob('*.raw.json'))), 8)
        self.assertEqual(final.denominators(self.root)['completed_native'], 2)
        self.assertEqual(final.denominators(self.root)['failed_or_partial_native'], 6)

    def test_same_process_does_not_use_mutable_commandline(self):
        identity = dict(pid=1, uid=123, boot_id='boot', start_ticks='1234')
        stat = '1 (changed process title) ' + ' '.join(['S']+['0']*18+['1234'])
        with patch.object(Path, 'read_text', side_effect=[stat, 'boot']), \
                patch.object(Path, 'stat', return_value=SimpleNamespace(st_uid=123)):
            self.assertTrue(final.same_process(identity))
        with patch.object(Path, 'read_text', side_effect=[stat, 'different_boot']), \
                patch.object(Path, 'stat', return_value=SimpleNamespace(st_uid=123)):
            self.assertFalse(final.same_process(identity))

    def test_release_requires_real_guard_terminal_and_absence(self):
        from gpu import orch_math_feedback_uptake_r118_final_drain as drain
        self.plan['drain_plan'] = dict(path='exact_drain_plan', sha256='a'*64)
        with patch.object(drain, 'validate_release', side_effect=ValueError('missing_real_release')) as verifier:
            with self.assertRaisesRegex(ValueError, 'missing_real_release'):
                final.release(self.plan)
        verifier.assert_called_once_with(self.plan['drain_plan'])

    def test_writer_never_overwrites_existing_evidence(self):
        path = self.root/'evidence.json'
        final.write(path, {'first': True})
        with self.assertRaises(FileExistsError):
            final.write(path, {'second': True})
        self.assertEqual(final.read(path), {'first': True})


class SelectionTests(unittest.TestCase):
    def setUp(self):
        from tests.test_orch_r118_final_selection import SelectionTests as CommonSelectionTests
        self.fixture = CommonSelectionTests(methodName='runTest')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root = self.fixture.root
        self.plan = dict(start_unix=final.START, end_unix=final.END, lease_end_unix=final.END+21600,
            common_root=str(self.root), selector_source={})

    def consume(self, when):
        from gpu import orch_r118_final_selection as selector
        lineage = {name: final.sha(self.root/name) for name in final.LINEAGE}
        with patch.object(final, 'LINEAGE', lineage), patch.object(final, 'module_from', return_value=selector), \
                patch.object(selector, 'select', side_effect=AssertionError('consumer_must_not_select')):
            return final.selection(self.plan, when)

    def test_initial_or_completed_shared_checkpoint_only(self):
        self.fixture.completed_state(final.START-1)
        selected = self.fixture.call(final.START+1)
        self.assertEqual(self.consume(final.START+2), selected)

    def test_mutable_STATE_is_not_a_second_checkpoint_selector(self):
        selected = self.fixture.call(final.START+1)
        (self.root/'STATE.json').write_text('{"generation":99,"checkpoint":"uncommitted"}')
        self.assertEqual(self.consume(final.START+2), selected)

    def test_postcut_sleep_is_rejected(self):
        self.fixture.completed_state(final.START-1)
        selected = self.fixture.call(final.START+1)
        completed = final.read(selected['committed_sleep']['path'])
        completed['completed_unix'] = final.START+1
        Path(selected['committed_sleep']['path']).write_text(final.json.dumps(completed))
        selected['committed_sleep'] = final.ref(selected['committed_sleep']['path'])
        (self.root/'FINAL_SELECTION.json').write_text(final.json.dumps(selected))
        with self.assertRaisesRegex(ValueError, 'committed_sleep_binding'):
            self.consume(final.START+2)


class NativeIntegrationTests(unittest.TestCase):
    def test_original_batch_implementation_exact_decoder_and_raw_continuation(self):
        from gpu import orch_math_feedback_uptake_r115_native as math
        class Tensor:
            def __init__(self, values):
                self.values = values
            def __getitem__(self, indices):
                if isinstance(indices, int):
                    return Tensor(self.values[indices])
                row, columns = indices
                return Tensor(self.values[row][columns])
            def tolist(self):
                return self.values
        configs = []
        def config(**values):
            configs.append(values)
            return SimpleNamespace(**values)
        def generate(**values):
            return Tensor([prefix+[66, 2] for prefix in values['input_ids'].values])
        engine = SimpleNamespace(check=Mock(), device='cpu', torch=SimpleNamespace(
            tensor=lambda values, **unused: Tensor(values), long='long', inference_mode=nullcontext),
            tokenizer=SimpleNamespace(pad_token_id=0, eos_token_id=2,
                apply_chat_template=lambda prompt, **unused: [11, 12],
                decode=lambda tokens, **unused: 'complete continuation ' + str(tokens)),
            transformers=SimpleNamespace(GenerationConfig=config), model=SimpleNamespace(generate=generate))
        prompts = [[dict(role='user', content='Synthetic test')] for unused in range(8)]
        responses = math.Engine.batch(engine, prompts, 2048)
        self.assertEqual(configs, [dict(do_sample=False, num_beams=1, use_cache=True, max_new_tokens=2048,
                                       repetition_penalty=1.0, eos_token_id=2, pad_token_id=0)])
        self.assertEqual(responses[0]['token_ids'], [66, 2])
        self.assertEqual(responses[0]['raw'], 'complete continuation [66]')
        self.assertTrue(all(response['independent_sequence'] for response in responses))

    def test_actual_eval_seam_is_fresh_parent_free_and_original_batch_decoder(self):
        from gpu import orch_math_feedback_uptake_r117_shared as client
        from tests.orch_math_feedback_uptake_r117_test import SharedMathTests
        fixture = SharedMathTests(methodName='runTest')
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        root = fixture.root/'evaluation'
        root.mkdir()
        chosen = dict(checkpoint=fixture.checkpoint, generation=0)
        selection_path = fixture.root/'SELECTED_FINAL.json'
        final.write(selection_path, chosen)
        final.write(root/'SELECTED.json', dict(reference=final.ref(selection_path)))
        plan = dict(start_unix=final.START, end_unix=final.END, lease_end_unix=final.END+21600,
            original_root=str(fixture.lane), selection_path=str(selection_path), branch='F2',
            uuid=client.math.policy.DEVICES[1], native_cap=8, task_ids=final.FINAL_IDS, decoder=final.DECODER)
        tasks = [dict(id=identifier, question='Synthetic question', split='FINAL') for identifier in final.FINAL_IDS]
        observed = SimpleNamespace(document=lambda: fixture.session['adapter'])
        loaded = SimpleNamespace(optimizer=None, engine=SimpleNamespace(), verify_unchanged=Mock(return_value=observed))
        def batch(engine, prompts, cap):
            self.assertEqual(cap, 2048)
            self.assertEqual(len(prompts), 8)
            return [dict(messages=prompt, raw='All reasoning preserved FINAL: synthetic', token_ids=[6, 7],
                         terminal=True, truncated=False, input_truncated=False) for prompt in prompts]
        with patch.object(final, 'validate', return_value=plan), patch.object(final.time, 'time', return_value=final.START+1), \
                patch.object(final, 'prior_attempts', return_value=[]), patch.object(final, 'release'), \
                patch.object(final, 'selection', return_value=chosen), patch.object(final, 'materialize', return_value=tasks), \
                patch.object(client.native, 'load_stage', return_value=loaded) as loader, \
                patch.object(client.math.Engine, 'batch', side_effect=batch), patch.object(client, 'current') as live_pointer:
            final.native(root)
        live_pointer.assert_not_called()
        args, kwargs = loader.call_args
        self.assertEqual(args[0].phase, 'sealed_readout')
        self.assertTrue(args[0].fresh_process)
        self.assertEqual(kwargs['context'].private_guidance, ())
        self.assertEqual(kwargs['predecessor_processes'], (('boot', 123, 456),))
        self.assertEqual(final.read(root/'COMPLETE.json')['native'], 8)
        self.assertIsNone(final.read(root/'AFTER.json')['optimizer'])
        self.assertFalse((fixture.lane/'LEDGER.json').exists())


if __name__ == '__main__':
    unittest.main()
