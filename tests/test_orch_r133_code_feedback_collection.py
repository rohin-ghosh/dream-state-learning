import ast
from contextlib import contextmanager, nullcontext
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

from gpu import orch_r133_code_feedback_collection as arm


SEED = '12' * 32


def inventory(**updates):
    result = dict(schema='R133_HASH_ONLY_EXCLUSIONS_V1', normalization=arm.public.NORMALIZATION,
                  attested_by='Main', coverage='R119_LINEAGE_DECLARED_CODE_INVENTORIES',
                  inventory_refs=[dict(ref='CPU_TEST_HASH_PROJECTION', sha256='c' * 64)],
                  spec_sha256=['a' * 64], task_id_sha256=[], used_seed_sha256=[])
    result.update(updates)
    return result


def response(expression, **updates):
    result = dict(raw=json.dumps({'expression': expression}), terminal=True, truncated=False)
    result.update(updates)
    return result


def solution(task):
    threshold, factor, offset = task['threshold'], task['factor'], task['offset']
    low, high = task['low'], task['high']
    return (
        f'sum(affine(ge(values,{threshold}),{factor},{offset}))',
        f'sum(unique(clip(affine(values,{factor},{offset}),{low},{high})))',
        f'sum(affine(ge(unique(values),{threshold}),{factor},{offset}))',
        f'len(ge(affine(clip(values,{low},{high}),{factor},{offset}),{threshold}))',
    )[task['kind']]


class TaskTests(unittest.TestCase):
    def test_fresh_balanced_TRAIN_without_legacy_task_access(self):
        with patch.object(arm.ledger, 'build_tasks', side_effect=AssertionError('forbidden legacy task access')):
            tasks = arm.build_tasks(SEED, inventory())
        self.assertEqual(len(tasks), 16)
        self.assertEqual(len({task['id'] for task in tasks}), 16)
        self.assertEqual(len({task['normalized_spec_sha256'] for task in tasks}), 16)
        self.assertEqual([task['kind'] for task in tasks], list(range(4)) * 4)
        self.assertTrue(all(task['split'] == 'TRAIN' and set(task) == arm.TASK_KEYS for task in tasks))
        self.assertEqual(tasks, arm.build_tasks(SEED, inventory()))
        other = arm.build_tasks('34' * 32, inventory())
        self.assertFalse({task['id'] for task in tasks} & {task['id'] for task in other})
        self.assertFalse({task['normalized_spec_sha256'] for task in tasks}
                         & {task['normalized_spec_sha256'] for task in other})

    def test_spec_ID_and_seed_exclusion(self):
        original = arm.build_tasks(SEED)[0]
        for key, value in [('spec_sha256', original['normalized_spec_sha256']),
                           ('task_id_sha256', arm.digest(original['id']))]:
            with self.subTest(key=key):
                tasks = arm.build_tasks(SEED, inventory(**{key: [value]}))
                self.assertNotIn(original['id'], [task['id'] for task in tasks])
                self.assertNotIn(original['normalized_spec_sha256'], [task['normalized_spec_sha256'] for task in tasks])
        with self.assertRaisesRegex(ValueError, 'seed_already_used'):
            arm.build_tasks(SEED, inventory(used_seed_sha256=[arm.digest(SEED)]))

    def test_reject_missing_coverage_raw_IDs_and_invalid_seed(self):
        for document in [inventory(attested_by='self'), inventory(coverage='PARTIAL'),
                         inventory(coverage='ALL_SEALED_AND_PRIOR_PUBLIC'),
                         inventory(spec_sha256=[]), inventory(task_id_sha256=['raw-evaluation-id']),
                         inventory(spec_sha256=['a' * 64, 'a' * 64]),
                         inventory(inventory_refs=[]),
                         inventory(inventory_refs=[dict(ref='RAW/path', sha256='c' * 64)]),
                         inventory(inventory_refs=[dict(ref='HASH_PROJECTION', sha256='bad')]),
                         inventory(inventory_refs=[dict(ref='HASH_PROJECTION', sha256='c' * 64)] * 2),
                         dict(inventory(), tasks=[]), dict(inventory(), evaluation_ids=[])]:
            with self.subTest(document=document), self.assertRaises(ValueError):
                arm.build_tasks(SEED, document)
        for seed in (None, 3, 'short', 'g' * 64):
            with self.subTest(seed=seed), self.assertRaises(ValueError):
                arm.build_tasks(seed)

    def test_generated_semantics_independent_positive_and_negative(self):
        for seed in (SEED, '56' * 32, '78' * 32):
            for task in arm.build_tasks(seed):
                with self.subTest(task=task['id']):
                    self.assertTrue(arm.verify(task, response(solution(task))['raw']))
                    self.assertFalse(arm.verify(task, response('0')['raw']))
                    for values in task['verification_inputs']:
                        factor, offset = task['factor'], task['offset']
                        if task['kind'] in (0, 2):
                            items = set(values) if task['kind'] == 2 else values
                            expected = sum(factor * value + offset for value in items if value >= task['threshold'])
                        elif task['kind'] == 1:
                            expected = sum({max(task['low'], min(task['high'], factor * value + offset)) for value in values})
                        else:
                            expected = sum(factor * max(task['low'], min(task['high'], value)) + offset
                                           >= task['threshold'] for value in values)
                        self.assertEqual(arm.evaluate(solution(task), values), expected)


class SandboxTests(unittest.TestCase):
    def test_no_eval_or_compile_execution(self):
        with (patch('builtins.eval', side_effect=AssertionError('arbitrary eval')),
              patch.object(arm.ledger, 'evaluate', side_effect=AssertionError('legacy evaluator'))):
            self.assertEqual(arm.evaluate('sum(affine(unique(ge(values,-2)),3,-1))', [-3, -2, -2, 4]), 4)
        tree = ast.parse(Path(arm.__file__).read_text())
        self.assertFalse(any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                             and node.func.id in ('eval', 'exec', 'compile') for node in ast.walk(tree)))

    def test_sandbox_rejections(self):
        expressions = ["__import__('os').system('true')", 'values.__class__', 'values[0]',
                       '[value for value in values]', 'lambda: 0', 'sum([1])', '1+2', '1**999',
                       'sum(values,0)', 'ge(values,threshold=0)', 'ge(values,values)', 'sum(1)',
                       'sum(ge)', 'affine', 'xs', 'True', '1.5', '1001', '--1', 'values',
                       'sum(clip(values,2,1))', 'sum(values)' + ' ' * 501,
                       'sum(' + 'unique(' * 34 + 'values' + ')' * 34 + ')']
        for expression in expressions:
            with self.subTest(expression=expression), self.assertRaises((ValueError, SyntaxError, TypeError)):
                arm.evaluate(expression, [1, 2])
        for values in ([True], [1000001], list(range(129))):
            with self.assertRaises(ValueError):
                arm.evaluate('sum(values)', values)

    def test_JSON_contract_positive_negative(self):
        self.assertEqual(arm.parse_expression('Reasoning\n{"expression":"sum(values)"}'), 'sum(values)')
        for raw in ('', ' ', '{"record":"x"}', '{"expression":3}',
                    '{"expression":"0","expression":"1"}', '{"expression":"0","extra":2}',
                    '```json\n{"expression":"0"}\n```', '{"expression":"0"}\ntrailing'):
            with self.subTest(raw=raw), self.assertRaises((ValueError, TypeError)):
                arm.parse_expression(raw)


class FeedbackTests(unittest.TestCase):
    def setUp(self):
        self.task = arm.build_tasks(SEED)[0]

    def test_real_observation_not_expected_answer(self):
        with patch.object(arm.public, 'expected', side_effect=AssertionError('label accessed')):
            receipt = arm.execute_public(self.task, response('sum(values)')['raw'])
            self.assertEqual(receipt['observed'], sum(self.task['public_input']))
            self.assertEqual(receipt['expression'], 'sum(values)')
            self.assertTrue(receipt['interpreter_started'])
            self.assertFalse(receipt['hidden_tests_exposed'])
            payload = arm.messages(self.task, 'interpreter_feedback', response('sum(values)')['raw'], receipt)
            self.assertEqual(len(payload), 4)
        syntax = arm.execute_public(self.task, response('values[0]')['raw'])
        self.assertFalse(syntax['interpreter_started'])
        self.assertIn('error', syntax)
        runtime = arm.execute_public(self.task, response('sum(7)')['raw'])
        self.assertTrue(runtime['interpreter_started'])
        self.assertIn('integer_list', runtime['error'])
        parser = arm.execute_public(self.task, 'not JSON')
        self.assertTrue(parser['parser_attempted'])
        self.assertFalse(parser['interpreter_started'])

    def test_labels_exclusions_IDs_and_fork_evidence_absent(self):
        task = dict(self.task, verification_inputs=[['PRIVATE_LABEL_SENTINEL']])
        draft = response('sum(values)')['raw']
        receipt = arm.execute_public(task, draft)
        payload = arm.messages(task, 'interpreter_feedback', draft, receipt)
        neutral = arm.messages(task, 'neutral_review', draft)
        for messages in (payload, neutral, arm.messages(task)):
            serialized = json.dumps(messages)
            for forbidden in ('PRIVATE_LABEL_SENTINEL', task['id'], task['normalized_spec_sha256'],
                              'verification_inputs', 'before_success', 'after_success', 'FULL_FIXED18404', 'BASE_NO_LORA'):
                self.assertNotIn(forbidden, serialized)
        self.assertNotIn('observed', neutral[-1]['content'])
        self.assertNotIn('draft_text_sha256', neutral[-1]['content'])
        self.assertEqual(payload[:3], neutral[:3])
        for contaminated in (dict(receipt, expected=5), dict(receipt, observed=receipt['observed'] + 1)):
            with self.assertRaises(ValueError):
                arm.messages(task, 'interpreter_feedback', draft, contaminated)
        with self.assertRaises(ValueError):
            arm.messages(task, 'neutral_review', draft, receipt)
        with self.assertRaises(ValueError):
            arm.messages(dict(task, expected=5))

    def test_formatting_vs_semantic_vs_interface_repair(self):
        correct = response(solution(self.task))
        wrapped = dict(correct, raw='```json\n' + correct['raw'] + '\n```')
        formatting = arm.correction(self.task, wrapped, correct)
        self.assertTrue(formatting['formatting_only_recovery'])
        self.assertFalse(formatting['task_semantic_correction'])
        semantic = arm.correction(self.task, response('0'), correct)
        self.assertTrue(semantic['task_semantic_correction'])
        self.assertFalse(semantic['formatting_only_recovery'])
        interface = arm.correction(self.task, response('sum(xs)'), correct)
        self.assertTrue(interface['interface_execution_recovery'])
        self.assertTrue(interface['unclassified_recovery'])
        self.assertFalse(interface['task_semantic_correction'])
        still_wrong = arm.correction(self.task, response('0'), response('1'))
        self.assertFalse(still_wrong['failed_to_passed'])
        incomplete = arm.correction(self.task, response('0'), dict(correct, terminal=False, truncated=True))
        self.assertFalse(incomplete['failed_to_passed'])
        unchanged = arm.correction(self.task, correct, correct)
        self.assertFalse(unchanged['failed_to_passed'])


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tasks = arm.build_tasks(SEED)

    def test_shared_draft_exact_quota_and_controls(self):
        calls = []

        def generate(messages, state):
            calls.append((messages, state))
            return response('0', raw=f'Native CPU fake call {len(calls)}\n' + response('0')['raw'])

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            result = arm.run_episodes(root, self.tasks, generate)
            self.assertEqual(result['reserved_calls'], 96)
            self.assertEqual(result['completed_calls'], 96)
            self.assertEqual(len(calls), 96)
            self.assertEqual(len(result['results']), 32)
            for task in self.tasks:
                for state in arm.MODELS:
                    directory = root / 'episodes' / task['id'] / state
                    draft = arm.read(directory / 'draft.CALL.json')
                    continuations = [arm.read(directory / (stage + '.CALL.json')) for stage in arm.STAGES[1:]]
                    for continuation in continuations:
                        self.assertEqual(continuation['shared_draft_call_sha256'], arm.sha(directory / 'draft.CALL.json'))
                        self.assertEqual(continuation['messages'][2]['content'], draft['response']['raw'])
                        self.assertEqual(continuation['shared_draft_text_sha256'], arm.digest(draft['response']['raw']))
                    self.assertEqual(continuations[0]['messages'][:3], continuations[1]['messages'][:3])
            with self.assertRaises(FileExistsError):
                arm.run_episodes(root, self.tasks, generate)
            self.assertEqual(len(calls), 96)
        self.assertEqual([state for messages, state in calls].count('BASE_NO_LORA'), 48)

    def test_native_failure_reserves_call_and_never_retries(self):
        calls = []

        def generate(messages, state):
            calls.append(state)
            if len(calls) == 2:
                raise RuntimeError('native_generation_failed')
            return response('0')

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaisesRegex(RuntimeError, 'native_generation_failed'):
                arm.run_episodes(root, self.tasks, generate)
            terminal = arm.read(root / 'EPISODES_TERMINAL.json')
            self.assertEqual((terminal['reserved_calls'], terminal['completed_calls']), (2, 1))
            self.assertEqual(len(list(root.rglob('*.FAILURE.json'))), 1)
            self.assertEqual(len(list(root.rglob('*.CALL.json'))), 1)
            self.assertEqual(len(list(root.rglob('*.INTENT.json'))), 2)
            with self.assertRaises(FileExistsError):
                arm.run_episodes(root, self.tasks, generate)
            self.assertEqual(len(calls), 2)

    def test_refusal_and_cap_hits_do_not_reroute_or_retry(self):
        calls = []

        def generate(messages, state):
            calls.append(state)
            return response('0', raw='I cannot provide that.', terminal=False, truncated=True)

        with tempfile.TemporaryDirectory() as temporary:
            result = arm.run_episodes(Path(temporary), self.tasks, generate)
        self.assertEqual(len(calls), 96)
        self.assertEqual(calls[:6], ['FULL_FIXED18404'] * 3 + ['BASE_NO_LORA'] * 3)
        self.assertEqual(calls[6:12], ['BASE_NO_LORA'] * 3 + ['FULL_FIXED18404'] * 3)
        self.assertTrue(all(not fork['failed_to_passed'] for result in result['results'] for fork in result['forks'].values()))

    def test_deadline_and_wrong_count_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            generate = unittest.mock.Mock()
            with self.assertRaises(ValueError):
                arm.run_episodes(Path(temporary), self.tasks[:1], generate)
            with self.assertRaises(TimeoutError):
                arm.run_episodes(Path(temporary), self.tasks, generate,
                                 check=unittest.mock.Mock(side_effect=TimeoutError('deadline')))
            generate.assert_not_called()


class PreparationTests(unittest.TestCase):
    def test_CPU_preview_not_launchable_or_overwritable(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / 'preview'
            plan = arm.prepare(root, SEED)
            self.assertEqual(plan['status'], 'PREVIEW_NOT_LAUNCHABLE')
            self.assertFalse(plan['gpu_launched'])
            arm.verified(root)
            with self.assertRaisesRegex(ValueError, 'exclusions_still_required'):
                arm.verified(root, require_launchable=True)
            with self.assertRaises(ValueError):
                arm.prepare(root, SEED)

    def test_hash_excluded_prepare_and_tamper_detection(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / 'ready'
            arm.prepare(root, SEED, inventory())
            arm.verified(root, require_launchable=True)
            path = root / 'TASKS.json'
            document = arm.read(path)
            document['tasks'][0]['spec'] = 'tampered'
            path.write_text(json.dumps(document))
            with self.assertRaisesRegex(ValueError, 'bytes_changed'):
                arm.verified(root)
            plan = arm.read(root / 'PLAN.json')
            plan['tasks_sha256'] = arm.sha(path)
            (root / 'PLAN.json').write_text(json.dumps(plan))
            with self.assertRaisesRegex(ValueError, 'fresh_generated_tasks'):
                arm.verified(root)

    def test_no_native_CLI(self):
        with patch('sys.argv', ['r133', 'collect', '--root', '/unused']), patch('sys.stderr'):
            with self.assertRaises(SystemExit) as error:
                arm.main()
        self.assertEqual(error.exception.code, 2)


class FrozenLoaderTests(unittest.TestCase):
    def model(self):
        module = types.SimpleNamespace(lora_A=True, lora_B=True, disable_adapters=False)
        parameter = types.SimpleNamespace(requires_grad=False)
        parameter.requires_grad_ = unittest.mock.Mock(side_effect=lambda enabled: setattr(parameter, 'requires_grad', enabled))

        @contextmanager
        def disable():
            previous_disabled = module.disable_adapters
            module.disable_adapters = True
            try:
                yield
            finally:
                module.disable_adapters = previous_disabled
                if not previous_disabled:
                    parameter.requires_grad = True

        return types.SimpleNamespace(parameters=lambda: [parameter], modules=lambda: [module], disable_adapter=disable), module, parameter

    def test_PEFT_exit_trainability_reproduction_and_repeated_states(self):
        model, module, parameter = self.model()
        weight_storage = object()
        parameter.data = weight_storage
        with model.disable_adapter():
            self.assertFalse(parameter.requires_grad)
        self.assertTrue(parameter.requires_grad)
        parameter.requires_grad = False
        for state in ('FULL_FIXED18404',) * 3 + ('BASE_NO_LORA',) * 3 + ('FULL_FIXED18404', 'BASE_NO_LORA'):
            with self.subTest(state=state):
                with arm.readonly_model(model, state):
                    self.assertFalse(parameter.requires_grad)
                    self.assertIs(parameter.data, weight_storage)
                    self.assertEqual(module.disable_adapters, state == 'BASE_NO_LORA')
                self.assertFalse(parameter.requires_grad)
                self.assertFalse(module.disable_adapters)
                self.assertIs(parameter.data, weight_storage)
        self.assertEqual(parameter.requires_grad_.call_args_list, [unittest.mock.call(False)] * 4)

    def test_body_trainability_drift_rejected_and_flags_restored(self):
        for state in arm.MODELS:
            model, module, parameter = self.model()
            with self.subTest(state=state), self.assertRaisesRegex(ValueError, 'weights_became_trainable'):
                with arm.readonly_model(model, state):
                    parameter.requires_grad = True
            self.assertFalse(parameter.requires_grad)
            self.assertFalse(module.disable_adapters)

    def test_context_exit_exception_restores_frozen_flags(self):
        model, module, parameter = self.model()

        @contextmanager
        def failed_exit():
            module.disable_adapters = True
            try:
                yield
            finally:
                module.disable_adapters = False
                parameter.requires_grad = True
                raise RuntimeError('PEFT_context_exit_failed')

        model.disable_adapter = failed_exit
        with self.assertRaisesRegex(RuntimeError, 'PEFT_context_exit_failed'):
            with arm.readonly_model(model, 'BASE_NO_LORA'):
                pass
        self.assertFalse(parameter.requires_grad)
        self.assertFalse(module.disable_adapters)

    def test_adapter_enable_state_drift_rejected_after_exit(self):
        model, module, parameter = self.model()

        @contextmanager
        def bad_exit():
            module.disable_adapters = True
            try:
                yield
            finally:
                parameter.requires_grad = True

        model.disable_adapter = bad_exit
        with self.assertRaisesRegex(ValueError, 'adapter_enable_state_not_restored'):
            with arm.readonly_model(model, 'BASE_NO_LORA'):
                pass
        self.assertFalse(parameter.requires_grad)
        self.assertTrue(module.disable_adapters)

    def test_already_disabled_entry_state_preserved(self):
        model, module, parameter = self.model()
        module.disable_adapters = True
        with arm.readonly_model(model, 'BASE_NO_LORA'):
            self.assertTrue(module.disable_adapters)
        self.assertTrue(module.disable_adapters)
        self.assertFalse(parameter.requires_grad)
        parameter.requires_grad_.assert_not_called()

    def test_true_base_adapter_disabled_and_restored_even_on_failure(self):
        model, module, parameter = self.model()
        with arm.readonly_model(model, 'FULL_FIXED18404'):
            self.assertFalse(module.disable_adapters)
        with self.assertRaises(RuntimeError):
            with arm.readonly_model(model, 'BASE_NO_LORA'):
                self.assertTrue(module.disable_adapters)
                raise RuntimeError('native failure')
        self.assertFalse(module.disable_adapters)
        self.assertFalse(parameter.requires_grad)
        parameter.requires_grad = True
        with self.assertRaisesRegex(ValueError, 'all_weights_frozen'):
            with arm.readonly_model(model, 'BASE_NO_LORA'):
                pass

    def test_broken_noLoRA_and_unknown_states_rejected(self):
        model, module, parameter = self.model()
        model.disable_adapter = nullcontext
        with self.assertRaisesRegex(ValueError, 'disable_state'):
            with arm.readonly_model(model, 'BASE_NO_LORA'):
                pass
        with self.assertRaisesRegex(ValueError, 'known_model_state'):
            with arm.readonly_model(model, 'ALTERNATIVE_REFUSAL_MODEL'):
                pass

    def test_preview_blocks_native_import_and_missing_authorization(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / 'preview'
            arm.prepare(root, SEED)
            with self.assertRaisesRegex(ValueError, 'exclusions_still_required'):
                arm.collect(root, {}, expected_gpu_uuid='GPU-CPU-TEST-ONLY')
            self.assertFalse((root / 'NATIVE_START.json').exists())
        with self.assertRaisesRegex(ValueError, 'exact_Main_launch_metadata'):
            arm.validate_authorization('/unused', {}, 0, expected_gpu_uuid='GPU-CPU-TEST-ONLY')

    def test_host_hash_is_raw_utf8_SHA256_not_JSON_digest(self):
        with patch.object(arm.socket, 'gethostname', return_value='CPU_TEST_HOST_ONLY'):
            expected = arm.hashlib.sha256(b'CPU_TEST_HOST_ONLY').hexdigest()
            self.assertEqual(arm.host_sha256(), expected)
            self.assertNotEqual(arm.host_sha256(), arm.digest('CPU_TEST_HOST_ONLY'))

    def test_frozen_native_loader_binding_CPU_seam(self):
        model, module, parameter = self.model()
        engine = types.SimpleNamespace(model=model, runtime={'CPU_TEST_DOUBLE': True},
                    prompt_tokens=lambda prefix: [1, 2],
                    generate=unittest.mock.Mock(return_value=response('0')))
        adapter = types.SimpleNamespace(document=lambda: {'CPU_TEST_DOUBLE': True})
        loaded = types.SimpleNamespace(engine=engine, observed=adapter, verify_unchanged=unittest.mock.Mock())
        native = types.SimpleNamespace(load_stage=unittest.mock.Mock(return_value=loaded),
                                       StageContext=unittest.mock.Mock(return_value='empty_context'))
        bridge = types.SimpleNamespace(AdapterIdentity=types.SimpleNamespace(
                    from_document=unittest.mock.Mock(return_value=adapter)), ARMS=['unused', 'FROZEN'],
                    StageBinding=unittest.mock.Mock(return_value='bound_fixed_adapter'))
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / 'native_cpu_mock'
            weights = Path(temporary) / 'readonly_weights'
            weights.mkdir()
            arm.prepare(root, SEED, inventory())
            authorization = dict(schema='R133_MAIN_NATIVE_AUTHORIZATION_V1', approved_by='Main',
                    plan_sha256=arm.sha(root / 'PLAN.json'), r130_released=True, allocation_confirmed=True,
                    host_sha256=arm.host_sha256(), gpu_uuid='GPU-CPU-TEST-ONLY', physical_index=7,
                    node_local_root=temporary, model_dir=str(weights), checkpoint=18404,
                    adapter=dict(path=str(weights), base_sha256=arm.public.BASE_SHA),
                    native_end_unix=arm.time.time() + 60, lease_end_unix=arm.time.time() + 600)
            fake_modules = {'gpu.orch_guided_native': native,
                            'gpu.orch_rich_hot_node2_exhaustion_v3': types.SimpleNamespace(Engine='frozen_engine'),
                            'organism_v6.orch_guided_bridge': bridge}
            with (patch.dict('sys.modules', fake_modules),
                  patch.dict(arm.os.environ, {'CUDA_VISIBLE_DEVICES': 'GPU-CPU-TEST-ONLY'})):
                result = arm.collect(root, authorization, expected_gpu_uuid='GPU-CPU-TEST-ONLY')
                self.assertEqual(result['completed_calls'], 96)
                native.load_stage.assert_called_once()
                options = native.load_stage.call_args.kwargs
                self.assertEqual(options['device'], 'cuda:0')
                self.assertEqual(options['engine_factory'], 'frozen_engine')
                self.assertEqual(options['context'], 'empty_context')
                self.assertEqual(bridge.StageBinding.call_args.args[1:7],
                                 ('FROZEN', 0, 'collection', adapter, False, True))
                bridge.AdapterIdentity.from_document.assert_called_once_with(authorization['adapter'])
                self.assertEqual(engine.generate.call_count, 96)
                loaded.verify_unchanged.assert_called_once()
                self.assertFalse(module.disable_adapters)
                self.assertFalse(parameter.requires_grad)
                self.assertNotIn(arm.socket.gethostname(), (root / 'NATIVE_START.json').read_text())
                self.assertNotIn('hostname', arm.read(root / 'NATIVE_START.json')['authorization'])
                with self.assertRaises(FileExistsError):
                    arm.collect(root, authorization, expected_gpu_uuid='GPU-CPU-TEST-ONLY')
                self.assertEqual(native.load_stage.call_count, 1)
                for changes in ({'r130_released': False}, {'allocation_confirmed': False},
                                {'checkpoint': 18405}, {'physical_index': 6},
                                {'gpu_uuid': 'GPU-DIFFERENT'}, {'native_end_unix': 0},
                                {'plan_sha256': 'b' * 64}, {'host_sha256': 'd' * 64},
                                {'host_sha256': 'raw-host-forbidden'}, {'hostname': 'raw-host-forbidden'}):
                    with self.subTest(changes=changes), self.assertRaises(ValueError):
                        arm.validate_authorization(root, dict(authorization, **changes), arm.time.time(),
                                                   expected_gpu_uuid='GPU-CPU-TEST-ONLY')
                with self.assertRaisesRegex(ValueError, 'allocation_binding'):
                    arm.validate_authorization(root, authorization, arm.time.time(), expected_gpu_uuid='GPU-OTHER-GUARD')


if __name__ == '__main__':
    unittest.main()
