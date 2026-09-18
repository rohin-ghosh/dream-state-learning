import copy
from contextlib import contextmanager
import json
import os
from pathlib import Path
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from gpu import orch_r133_code_feedback_collection as frozen
from gpu import orch_r141_code_interface as prior
from gpu import orch_r142_base_reasoning_collection as arm
from tests.test_orch_r133_code_feedback_collection import inventory, response, solution


SEED = 'e3' * 32


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.tasks = arm.build_tasks(SEED, inventory())

    def test_exact_directed_cue_and_steering_not_redundant_permission(self):
        self.assertEqual(arm.DIRECTED_CUE,
            'Before the final JSON, work through the task in your own words. '
            'If uncertainty or feedback gives you a reason to change your plan, '
            'explain what changes and why. Stop when you have enough evidence; '
            'do not pad the response.')
        self.assertEqual(arm.PROMPT_ARMS, ('PERMISSION_ONLY', 'DIRECTED_REASONING'))
        self.assertEqual(arm.STEERING['DIRECTED_REASONING'], 'text_requested')
        self.assertEqual(arm.MODELS, ('BASE_NO_LORA',))
        self.assertIn('You may reason', frozen.public.CONTRACT)
        self.assertFalse(any(character.isdigit() for character in arm.DIRECTED_CUE))
        for helper in frozen.ledger.HELPERS:
            self.assertNotIn(helper + '(', arm.DIRECTED_CUE)

    def test_only_delta_is_exact_task_independent_system_suffix(self):
        for task in self.tasks:
            for stage in arm.STAGES:
                draft = None if stage == 'draft' else 'Visible text stays intact.\n{"expression":"0"}'
                feedback = frozen.execute_public(task, draft) if stage == 'interpreter_feedback' else None
                original = prior.messages(task, stage, draft, feedback)
                control = arm.messages(task, 'PERMISSION_ONLY', stage, draft, feedback)
                directed = arm.messages(task, 'DIRECTED_REASONING', stage, draft, feedback)
                self.assertEqual(control, original)
                expected = copy.deepcopy(control)
                expected[0]['content'] += '\n' + arm.DIRECTED_CUE
                self.assertEqual(directed, expected)

    def test_feedback_cannot_be_fabricated_or_leaked_into_neutral(self):
        task = self.tasks[0]
        draft = '{"expression":sum(values)}'
        receipt = frozen.execute_public(task, draft)
        for prompt_arm in arm.PROMPT_ARMS:
            actual = arm.messages(task, prompt_arm, 'interpreter_feedback', draft, receipt)
            neutral = arm.messages(task, prompt_arm, 'neutral_review', draft)
            self.assertEqual(actual[:3], neutral[:3])
            self.assertIn(json.dumps(receipt, sort_keys=True), actual[-1]['content'])
            self.assertNotIn(receipt['error'], neutral[-1]['content'])
            with self.assertRaises(ValueError):
                arm.messages(task, prompt_arm, 'interpreter_feedback', draft, dict(receipt, observed=99))
            with self.assertRaises(ValueError):
                arm.messages(task, prompt_arm, 'neutral_review', draft, receipt)
        for label in ('FULL_FIXED18404', 'BASE_NO_LORA', 'BASE_REASONING_PERMISSION', 'unhinted'):
            with self.assertRaisesRegex(ValueError, 'declared_BASE_prompt_arm'):
                arm.messages(task, label)

    def test_exact_parser_scorer_exclusions_and_metrics_reused(self):
        for name in ('parse_expression', 'evaluate', 'verify', 'execute_public', 'exclusions'):
            self.assertIs(getattr(arm, name), getattr(frozen, name))
        for task in self.tasks:
            raw = 'I checked the expression.\n' + response(solution(task))['raw']
            self.assertTrue(arm.verify(task, raw))
            self.assertFalse(arm.verify(task, '{"expression":sum(values)}'))
        self.assertEqual(arm.MAX_NEW_TOKENS, 2048)
        self.assertEqual(arm.CONTEXT_LIMIT, 32768)

    def test_exclusions_required_and_old_planned_hashes_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Main_hash_only'):
            arm.build_tasks(SEED)
        with self.assertRaisesRegex(ValueError, 'seed_already_used'):
            arm.build_tasks(SEED, inventory(used_seed_sha256=[arm.digest(SEED)]))
        document = inventory(spec_sha256=[task['normalized_spec_sha256'] for task in self.tasks],
                             task_id_sha256=[arm.digest(task['id']) for task in self.tasks])
        fresh = arm.build_tasks(SEED, document)
        self.assertFalse(set(document['spec_sha256']) & {task['normalized_spec_sha256'] for task in fresh})
        with patch.object(frozen.ledger, 'build_tasks', side_effect=AssertionError('no held or legacy tasks')):
            self.assertEqual(self.tasks, arm.build_tasks(SEED, inventory()))


class PreparedFixture(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / 'synthetic'

    def prepare(self):
        arm.prepare(self.root, SEED, inventory())
        return arm.verified(self.root)[1]


class PreparedTests(PreparedFixture):
    def test_no_unexcluded_preview_and_no_replacement(self):
        with self.assertRaises(ValueError):
            arm.prepare(self.root, SEED)
        self.assertFalse(self.root.exists())
        self.prepare()
        with self.assertRaises(ValueError):
            arm.prepare(self.root, SEED, inventory())

    def test_R141_and_R142_plans_fail_cross_schema(self):
        prior.prepare(self.root, SEED, inventory())
        with self.assertRaisesRegex(ValueError, 'exact_R142'):
            arm.verified(self.root)
        other = Path(self.temporary.name) / 'r142'
        arm.prepare(other, SEED, inventory())
        with self.assertRaises(ValueError):
            prior.verified(other)

    def test_arm_base_cue_budget_source_and_task_tampering_fail_closed(self):
        tasks = self.prepare()
        original = arm.read(self.root / 'PLAN.json')
        for changes in (dict(models=['FULL_FIXED18404']), dict(prompt_arms=['PERMISSION_ONLY']),
                        dict(effective_models={name: 'FULL_FIXED18404' for name in arm.PROMPT_ARMS}),
                        dict(steering={name: 'unhinted' for name in arm.PROMPT_ARMS}),
                        dict(directed_cue='You may reason'), dict(native_call_cap=97), dict(max_new_tokens=2049),
                        dict(fit_updates=1), dict(source_sha256={})):
            (self.root / 'PLAN.json').write_text(json.dumps(dict(original, **changes)))
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                arm.verified(self.root)
        (self.root / 'PLAN.json').write_text(json.dumps(original))
        changed = copy.deepcopy(tasks)
        changed[0]['public_input'] = [999]
        generate = Mock()
        with self.assertRaises(ValueError):
            arm.run_episodes(self.root, changed, generate)
        generate.assert_not_called()
        with patch.object(arm, 'sha', return_value='0' * 64), self.assertRaisesRegex(ValueError, 'exact_frozen'):
            arm.source_hashes()

    def test_96_calls_balance_arm_identity_raw_reasoning_and_independent_forks(self):
        tasks = self.prepare()
        calls = []

        def generate(prefix, prompt_arm):
            calls.append((prefix, prompt_arm))
            return response('0', raw='Visible work without any internal-process claim.\n{"expression":"0"}')

        result = arm.run_episodes(self.root, tasks, generate)
        self.assertEqual((result['reserved_calls'], result['completed_calls'], len(calls)), (96, 96, 96))
        self.assertEqual(result['effective_model'], arm.BASE_MODEL)
        self.assertEqual((result['rows_admitted'], result['fit_updates'], result['external_calls']), (0, 0, 0))
        self.assertEqual(len(result['results']), 32)
        self.assertEqual([label for _, label in calls[:12]], [arm.PROMPT_ARMS[0]] * 3 + [arm.PROMPT_ARMS[1]] * 6 + [arm.PROMPT_ARMS[0]] * 3)
        for position, task in enumerate(tasks):
            for prompt_arm in arm.PROMPT_ARMS:
                directory = self.root / 'episodes' / task['id'] / prompt_arm
                draft = arm.read(directory / 'draft.CALL.json')
                for stage in arm.STAGES:
                    call = arm.read(directory / (stage + '.CALL.json'))
                    self.assertEqual((call['prompt_arm'], call['effective_model'], call['steering']),
                                     (prompt_arm, arm.BASE_MODEL, arm.STEERING[prompt_arm]))
                    self.assertTrue(call['response']['raw'].startswith('Visible work'))
                    self.assertEqual(arm.read(directory / (stage + '.MEASURE.json'))['metrics'],
                                     prior.response_metrics(task, call['response']))
                    if stage != 'draft':
                        self.assertEqual(call['shared_draft_call_sha256'], arm.sha(directory / 'draft.CALL.json'))
                        self.assertEqual(call['messages'][2]['content'], draft['response']['raw'])
                        expected_order = 1 if (stage == 'interpreter_feedback') == (position % 2 == 0) else 2
                        self.assertEqual(call['reserved_call'] - draft['reserved_call'], expected_order)
        with self.assertRaises(FileExistsError):
            arm.run_episodes(self.root, tasks, generate)
        self.assertEqual(len(calls), 96)

    def test_generation_failure_preserves_intent_without_retry(self):
        tasks = self.prepare()
        generate = Mock(side_effect=[response('0'), RuntimeError('fake failure')])
        with self.assertRaisesRegex(RuntimeError, 'fake failure'):
            arm.run_episodes(self.root, tasks, generate)
        terminal = arm.read(self.root / 'EPISODES_TERMINAL.json')
        self.assertEqual((terminal['reserved_calls'], terminal['completed_calls']), (2, 1))
        self.assertEqual(len(list(self.root.rglob('*.MEASURE.json'))), 1)
        self.assertEqual(len(list(self.root.rglob('*.FAILURE.json'))), 1)
        with self.assertRaises(FileExistsError):
            arm.run_episodes(self.root, tasks, generate)
        self.assertEqual(generate.call_count, 2)

    def test_truncation_preserved_and_correction_ineligible(self):
        tasks = self.prepare()
        result = arm.run_episodes(self.root, tasks,
            lambda prefix, label: response('0', raw='partial reasoning', terminal=False, truncated=True))
        for episode in result['results']:
            for pair in episode['forks'].values():
                self.assertFalse(pair['complete_pair'])
                self.assertFalse(pair['failed_to_passed'])
                self.assertFalse(pair['semantic_correction'])

    def test_deadline_before_generation_and_no_native_cli(self):
        tasks = self.prepare()
        generate = Mock()
        with self.assertRaises(TimeoutError):
            arm.run_episodes(self.root, tasks, generate, Mock(side_effect=TimeoutError('deadline')))
        generate.assert_not_called()
        with patch('sys.argv', ['r142', 'collect', '--root', '/unused']), patch('sys.stderr'), self.assertRaises(SystemExit):
            arm.main()


class BaseOnlyTests(PreparedFixture):
    def loaded(self):
        module = SimpleNamespace(lora_A=True, lora_B=True, disable_adapters=False)
        parameter = SimpleNamespace(requires_grad=False)
        parameter.requires_grad_ = Mock(side_effect=lambda value: setattr(parameter, 'requires_grad', value))

        @contextmanager
        def disable():
            module.disable_adapters = True
            try:
                yield
            finally:
                module.disable_adapters = False
                parameter.requires_grad = True

        model = SimpleNamespace(modules=lambda: [module], parameters=lambda: [parameter], disable_adapter=Mock(side_effect=disable))
        engine = SimpleNamespace(model=model, runtime={}, prompt_tokens=Mock(return_value=[1]), generate=Mock(return_value=response('0')))
        loaded = SimpleNamespace(engine=engine, observed=SimpleNamespace(document=lambda: {'carrier': 'test_only'}))
        return loaded, module, parameter

    def test_one_disable_context_spans_both_arms_and_all_96_calls(self):
        tasks = self.prepare()
        loaded, module, parameter = self.loaded()
        observations = []

        def generate(prefix, **kwargs):
            observations.append((module.disable_adapters, parameter.requires_grad,
                                 arm.DIRECTED_CUE in prefix[0]['content']))
            self.assertEqual(kwargs, dict(max_new_tokens=2048))
            return response('0')

        loaded.engine.generate.side_effect = generate
        result = arm.run_loaded(self.root, tasks, loaded, lambda label: None)
        self.assertEqual(result['completed_calls'], 96)
        loaded.engine.model.disable_adapter.assert_called_once_with()
        self.assertEqual(len(observations), 96)
        self.assertTrue(all(disabled and not trainable for disabled, trainable, _ in observations))
        self.assertEqual(sum(directed for _, _, directed in observations), 48)
        self.assertFalse(module.disable_adapters)
        self.assertFalse(parameter.requires_grad)
        observed = arm.read(self.root / 'LOADED.json')
        self.assertEqual(observed['model_states'], ['BASE_NO_LORA'])
        self.assertEqual(observed['effective_models'], {name: 'BASE_NO_LORA' for name in arm.PROMPT_ARMS})

    def test_adapter_or_trainability_drift_stops_first_call(self):
        for drift in ('adapter', 'gradient'):
            with self.subTest(drift=drift), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary) / 'drift'
                arm.prepare(root, SEED, inventory())
                tasks = arm.verified(root)[1]
                loaded, module, parameter = self.loaded()

                def generate(prefix, **kwargs):
                    if drift == 'adapter':
                        module.disable_adapters = False
                    else:
                        parameter.requires_grad = True
                    return response('0')

                loaded.engine.generate.side_effect = generate
                with self.assertRaises(ValueError):
                    arm.run_loaded(root, tasks, loaded, lambda label: None)
                self.assertEqual(loaded.engine.generate.call_count, 1)
                self.assertFalse(parameter.requires_grad)
                self.assertEqual(arm.read(root / 'EPISODES_TERMINAL.json')['status'], 'FAILED_NO_RETRY')

    def test_unknown_arm_and_context_overflow_never_dispatch(self):
        tasks = self.prepare()
        loaded, _, _ = self.loaded()

        def rogue_loop(root, tasks, generate, check):
            return generate([], 'FULL_FIXED18404')

        with patch.object(arm, 'run_episodes', side_effect=rogue_loop), self.assertRaisesRegex(ValueError, 'declared_BASE_prompt_arm'):
            arm.run_loaded(self.root, tasks, loaded, lambda label: None)
        loaded.engine.generate.assert_not_called()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / 'overflow'
            arm.prepare(root, SEED, inventory())
            loaded, _, _ = self.loaded()
            loaded.engine.prompt_tokens.return_value = [1] * 32768
            with self.assertRaisesRegex(ValueError, 'no_context_trim'):
                arm.run_loaded(root, arm.verified(root)[1], loaded, lambda label: None)
            loaded.engine.generate.assert_not_called()

    def test_native_loader_identity_and_weight_barrier_with_mocked_signals(self):
        import gpu
        import organism_v6

        self.prepare()
        loaded, module, parameter = self.loaded()
        for name in ('weights', 'adapter'):
            (Path(self.temporary.name) / name).mkdir()
        adapter = dict(path=str(Path(self.temporary.name) / 'adapter'), state_sha256='a' * 64,
                       base_sha256=frozen.public.BASE_SHA, files=[['adapter_model.safetensors', 'b' * 64]])
        loaded.observed.document = lambda: adapter
        loaded.verify_unchanged = Mock()
        native = SimpleNamespace(load_stage=Mock(return_value=loaded), StageContext=Mock(return_value='empty_context'))
        bridge = SimpleNamespace(AdapterIdentity=SimpleNamespace(from_document=Mock(return_value='adapter_identity')),
                                 StageBinding=Mock(return_value='load_binding'), ARMS=('OTHER', 'FULL_CARRIER'))
        engine_class = object()
        engine_module = SimpleNamespace(Engine=engine_class)
        authorization = dict(schema='R133_MAIN_NATIVE_AUTHORIZATION_V1', approved_by='Main',
            plan_sha256=arm.sha(self.root / 'PLAN.json'), r130_released=True, allocation_confirmed=True,
            host_sha256=frozen.host_sha256(), gpu_uuid='GPU-CPU-TEST', physical_index=7,
            node_local_root=self.temporary.name, model_dir=str(Path(self.temporary.name) / 'weights'),
            checkpoint=18404, adapter=adapter, native_end_unix=time.time() + 300, lease_end_unix=time.time() + 1000)
        with patch.dict(sys.modules, {'gpu.orch_rich_hot_node2_exhaustion_v3': engine_module}), \
                patch.object(gpu, 'orch_guided_native', native, create=True), \
                patch.object(organism_v6, 'orch_guided_bridge', bridge, create=True), \
                patch.dict(os.environ, CUDA_VISIBLE_DEVICES='GPU-CPU-TEST'), \
                patch.object(arm.signal, 'getitimer', return_value=(0.0, 0.0)), \
                patch.object(arm.signal, 'signal', return_value='prior_handler') as signal_mock, \
                patch.object(arm.signal, 'setitimer') as timer_mock:
            result = arm.collect(self.root, authorization, expected_gpu_uuid='GPU-CPU-TEST')
        self.assertEqual(result['completed_calls'], 96)
        loaded.verify_unchanged.assert_called_once_with()
        self.assertEqual(native.load_stage.call_args.kwargs['engine_factory'], engine_class)
        self.assertEqual(native.load_stage.call_args.kwargs['gpu_uuid'], 'GPU-CPU-TEST')
        self.assertEqual(bridge.StageBinding.call_args.args[1], 'FULL_CARRIER')
        self.assertEqual(arm.read(self.root / 'LOADED.json')['model_states'], ['BASE_NO_LORA'])
        self.assertEqual(arm.read(self.root / 'NATIVE_TERMINAL.json')['effective_model'], 'BASE_NO_LORA')
        self.assertEqual(timer_mock.call_args.args, (arm.signal.ITIMER_REAL, 0))
        self.assertEqual(signal_mock.call_args.args, (arm.signal.SIGALRM, 'prior_handler'))
        self.assertFalse(module.disable_adapters)
        self.assertFalse(parameter.requires_grad)

    def test_wrong_authorization_rejected_before_any_signal_or_load(self):
        self.prepare()
        with patch.object(arm.signal, 'signal') as signal_mock, self.assertRaises(ValueError):
            arm.collect(self.root, {}, expected_gpu_uuid='GPU-CPU-TEST')
        signal_mock.assert_not_called()


if __name__ == '__main__':
    unittest.main()
