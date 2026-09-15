from copy import deepcopy
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import Mock, patch

from gpu import orch_math_feedback_uptake_r117_shared as client


class SharedMathTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.shared = self.root / 'shared'
        self.specs = {branch: dict(root=str(self.root / branch), train_ids=[branch+'_one', branch+'_two'])
            for branch in client.shared.BRANCHES}
        roots = {branch: Path(self.specs[branch]['root']) for branch in ('F2', 'A2')}
        self.patch = patch.object(client, 'BRANCHES', roots)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        mounted = patch.object(client.math, 'mounted', return_value={'uuid': client.math.policy.DEVICES[1]})
        mounted.start()
        self.addCleanup(mounted.stop)
        self.checkpoint = self.make_checkpoint('initial')
        client.shared.initialize(self.shared, self.specs, self.checkpoint, excluded_ids=['DEV', 'FINAL'],
            prior_metrics=dict.fromkeys(client.shared.METRICS, None), initial_history={})
        self.session = client.prepare(self.shared, 'F2')
        self.lane = Path(self.session['branch_root'])
        self.output = self.lane / 'cycle044'
        self.output.mkdir(parents=True)
        self.tasks = [dict(id=identifier, split='TRAIN', question_sha256='b'*64)
            for identifier in self.session['train_ids']]

    def make_checkpoint(self, name):
        folder = self.root / name
        adapter = folder / 'adapter'
        client.shared.write(adapter / 'adapter_config.json', dict(r=8))
        identity = client.native.bridge.AdapterIdentity(str(adapter), 'a'*64, client.math.direct.BASE_SHA,
            (('adapter_config.json', client.shared.sha(adapter/'adapter_config.json')),))
        optimizer = folder / 'optimizer.json'
        client.shared.write(optimizer, dict(owner='F1'))
        checkpoint = folder / 'COMPLETE.json'
        client.shared.write(checkpoint, dict(complete=True, adapter=identity.document(),
            optimizer_rng_sha256=client.shared.sha(optimizer), source_process=['boot', 123, 456]))
        return dict(path=str(checkpoint), path_sha256=client.shared.sha(checkpoint),
            optimizer_path=str(optimizer), optimizer_path_sha256=client.shared.sha(optimizer))

    def engine(self, fail=False):
        session = deepcopy(self.session)
        def generate(messages, *, max_new_tokens):
            requests = sorted(self.output.glob('*.request.json'))
            request = client.shared.read(requests[-1])
            self.assertEqual(request['shared_generation'], session['generation'])
            self.assertIs(type(request['shared_generation']), int)
            self.assertEqual(request['shared_checkpoint_sha256'], session['checkpoint_sha256'])
            self.assertEqual(request['messages'], messages)
            self.assertFalse(requests[-1].with_name(requests[-1].name.replace('.request', '')).exists())
            if fail:
                raise RuntimeError('native_failure')
            return dict(messages=messages, prompt_tokens=2, token_ids=[3, 4], raw='Incorrect past attempt: 684.',
                terminal=False, truncated=True)
        return SimpleNamespace(session=session, loaded=SimpleNamespace(binding=SimpleNamespace(phase='collection')),
            tokenizer=SimpleNamespace(apply_chat_template=lambda *args, **kwargs: [1, 2]), generate=generate)

    def capture_cycle(self):
        engine = self.engine()
        for ordinal, phase in enumerate(client.PHASES):
            task = self.tasks[0 if ordinal < 2 else 1]
            experience = client.math.policy.Experience()
            experience.append(client.math.policy.event('environment', 'Recorded attempt is incorrect.', 'TRAIN', {}))
            client.child_call(self.lane, engine, self.output, task, experience, 'Reflect freely.', phase, 3072)
        return sorted(path for path in self.output.glob('CALL_*.json') if '.request.' not in path.name)

    def rewrite(self, path, change):
        value = client.shared.read(path)
        change(value)
        client.shared.write(path, value, replace=True)

    def export(self):
        return client.export_cycle(self.session, self.output, self.session['train_ids'])

    def test_prepare_requires_registered_math_branch(self):
        with self.assertRaisesRegex(ValueError, 'math_shared_branch_only'):
            client.prepare(self.shared, 'F1')

    def test_prepare_verifies_checkpoint_and_owner_optimizer(self):
        self.assertEqual(self.session['optimizer_owner'], 'F1')
        Path(self.checkpoint['optimizer_path']).write_text('{}')
        with self.assertRaisesRegex(ValueError, 'checkpoint_or_optimizer_hash'):
            client.prepare(self.shared, 'F2')

    def test_capture_tags_written_before_dispatch_and_export_exact_six(self):
        self.capture_cycle()
        result = self.export()
        self.assertEqual(result['source_calls'], 6)
        self.assertEqual(result['source_tokens'], 12)
        self.assertEqual(result['branch_weight_updates'], 0)
        self.assertEqual(client.shared.barrier_status(self.shared)['present'], ['F2'])

    def test_wrong_attempts_and_nonterminal_tokens_retained(self):
        self.capture_cycle()
        rows = client.shared.read(self.export()['path'])['rows']
        self.assertEqual(len(rows), 6)
        for row in rows:
            self.assertEqual(row['target'], 'Incorrect past attempt: 684.')
            self.assertFalse(row['observed_fact_endorsement'])
            self.assertTrue(row['continuation_only'])
            self.assertFalse(row['append_eos'])
            self.assertEqual(row['source_generated_token_ids'], [3, 4])

    def test_export_idempotent_without_new_calls(self):
        self.capture_cycle()
        self.assertEqual(self.export(), self.export())
        self.assertEqual(client.shared.read(self.lane/'COUNTERS.json')['native'], 6)

    def test_old_base_capture_not_relabelled(self):
        paths = self.capture_cycle()
        self.rewrite(paths[0], lambda value: value.pop('shared_generation'))
        with self.assertRaisesRegex(ValueError, 'prospective_shared_capture_only'):
            self.export()

    def test_boolean_generation_is_not_integer_tag(self):
        paths = self.capture_cycle()
        self.rewrite(paths[0], lambda value: value.update(shared_generation=False))
        with self.assertRaisesRegex(ValueError, 'prospective_shared_capture_only'):
            self.export()

    def test_checkpoint_tag_mismatch_rejected(self):
        paths = self.capture_cycle()
        self.rewrite(paths[0], lambda value: value.update(shared_checkpoint_sha256='c'*64))
        with self.assertRaisesRegex(ValueError, 'prospective_shared_capture_only'):
            self.export()

    def test_predispatch_request_tamper_rejected(self):
        paths = self.capture_cycle()
        self.rewrite(paths[0].with_suffix('.request.json'), lambda value: value.update(messages=[]))
        with self.assertRaisesRegex(ValueError, 'predispatch_request_hash'):
            self.export()

    def test_causal_messages_tamper_rejected(self):
        paths = self.capture_cycle()
        self.rewrite(paths[0], lambda value: value['response'].update(messages=[]))
        with self.assertRaisesRegex(ValueError, 'immutable_predispatch_capture'):
            self.export()

    def test_attached_dev_or_final_never_submitted(self):
        paths = self.capture_cycle()
        self.rewrite(paths[1], lambda value: value.update(attached_readout=True))
        with self.assertRaisesRegex(ValueError, 'readout_open_turn_never_experience'):
            self.export()

    def test_nontrain_never_dispatched_or_reserved(self):
        for split in ('DEV', 'FINAL', 'PROBE'):
            task = dict(self.tasks[0], split=split)
            with self.assertRaisesRegex(ValueError, 'bound_train_only'):
                client.child_call(self.lane, self.engine(), self.output, task,
                    client.math.policy.Experience(), 'inspect', 'open_turn', 128)
        self.assertFalse((self.lane/'COUNTERS.json').exists())

    def test_duplicate_episode_ids_rejected(self):
        with self.assertRaisesRegex(ValueError, 'two_distinct_bound_episodes'):
            client.export_cycle(self.session, self.output, [self.tasks[0]['id']]*2)

    def test_partial_cycle_not_submitted(self):
        with self.assertRaisesRegex(ValueError, 'all_six_train_attempts_required'):
            self.export()

    def test_failed_capture_preserves_request_and_charge(self):
        with self.assertRaisesRegex(RuntimeError, 'native_failure'):
            client.child_call(self.lane, self.engine(fail=True), self.output, self.tasks[0],
                client.math.policy.Experience(), 'try', 'episode', 128)
        call = client.shared.read(self.output/'CALL_0001.json')
        self.assertEqual(call['status'], 'FAILED')
        self.assertEqual(call['shared_checkpoint_sha256'], self.session['checkpoint_sha256'])
        self.assertEqual(client.shared.read(self.lane/'COUNTERS.json')['native'], 1)

    def test_failed_attempt_never_dropped_from_complete_cycle(self):
        paths = self.capture_cycle()
        self.rewrite(paths[1], lambda value: value.update(status='FAILED'))
        with self.assertRaisesRegex(ValueError, 'failed_attempt_preserved_no_silent_drop'):
            self.export()

    def test_stale_generation_stops_before_capture(self):
        self.rewrite(self.shared/'STATE.json', lambda value: value.update(generation=1))
        with self.assertRaisesRegex(ValueError, 'shared_child_changed'):
            self.capture_cycle()
        self.assertFalse((self.lane/'COUNTERS.json').exists())

    def test_loader_readout_is_fresh_and_parent_free(self):
        def loader(stage, **kwargs):
            self.assertEqual(stage.phase, 'sealed_readout')
            self.assertTrue(stage.fresh_process)
            self.assertFalse(stage.parent_present)
            self.assertEqual(kwargs['context'].private_guidance, ())
            self.assertIsNone(kwargs['check']('forward'))
            return SimpleNamespace(binding=stage, optimizer=None, verify_unchanged=lambda: stage.adapter)
        actor = client.load(self.session, model_dir=client.math.MODEL, gpu_uuid=client.math.policy.DEVICES[1],
            check=lambda label: {'status': 'checked'}, readout=True, loader=loader)
        self.assertIsNone(actor.loaded.optimizer)

    def test_loader_rejects_any_nonowner_optimizer(self):
        def loader(stage, **kwargs):
            return SimpleNamespace(binding=stage, optimizer=object(), verify_unchanged=lambda: stage.adapter)
        with self.assertRaisesRegex(ValueError, 'readonly_math_shared_actor'):
            client.load(self.session, model_dir=client.math.MODEL, gpu_uuid=client.math.policy.DEVICES[1],
                check=lambda label: None, loader=loader)

    def test_loader_rejects_wrong_gpu_before_model_load(self):
        loader = Mock()
        with self.assertRaisesRegex(ValueError, 'allocated_branch_uuid'):
            client.load(self.session, model_dir=client.math.MODEL, gpu_uuid='wrong',
                check=lambda label: None, loader=loader)
        loader.assert_not_called()

    def test_no_readout_batch_on_training_actor(self):
        loaded = SimpleNamespace(binding=SimpleNamespace(phase='collection',
            adapter=client.native.bridge.AdapterIdentity.from_document(self.session['adapter'])),
            optimizer=None, verify_unchanged=lambda: None)
        actor = client.SharedEngine(loaded, self.session)
        with self.assertRaisesRegex(ValueError, 'batch_only_parent_free_readout'):
            actor.batch([[]], 16)

    def test_nonreflection_uses_adapter_safe_decoder(self):
        stage = SimpleNamespace(phase='collection',
            adapter=client.native.bridge.AdapterIdentity.from_document(self.session['adapter']))
        loaded = SimpleNamespace(binding=stage, optimizer=None, verify_unchanged=lambda: None,
            engine=SimpleNamespace(model=SimpleNamespace(parameters=lambda: [])))
        actor = client.SharedEngine(loaded, self.session)
        with patch.object(client.generation, 'generate', return_value={}) as decoder:
            actor.generate([], max_new_tokens=2048)
        decoder.assert_called_once_with(loaded, [], max_prompt_tokens=14336, max_new_tokens=2048)

    def test_reflection_preserves_guard_without_auto_fit_label(self):
        stage = SimpleNamespace(phase='collection',
            adapter=client.native.bridge.AdapterIdentity.from_document(self.session['adapter']))
        loaded = SimpleNamespace(binding=stage, optimizer=None, verify_unchanged=lambda: None,
            engine=SimpleNamespace(model=SimpleNamespace(parameters=lambda: [])))
        actor = client.SharedEngine(loaded, self.session)
        actor.purpose = 'reflection'
        with patch.object(client.math.Engine, 'generate', return_value={'reflection_guard': {'terminal': False}}):
            result = actor.generate([], max_new_tokens=3072)
        self.assertFalse(result['reflection_guard']['terminal'])
        self.assertEqual(result['reflection_guard']['fit_eligibility'], 'UNASSESSED_SOURCE_PRESERVED_OWNER_ENCODER_CHECKS')

    def reload_fixture(self):
        self.capture_cycle()
        submission = self.export()
        checkpoint = self.make_checkpoint('next')
        state = client.shared.read(self.shared/'STATE.json')
        state.update(generation=1, checkpoint=checkpoint)
        client.shared.write(self.shared/'STATE.json', state, replace=True)
        session = client.prepare(self.shared, 'F2')
        identity = client.native.bridge.AdapterIdentity.from_document(self.session['adapter'])
        stage = client.native.bridge.StageBinding('F2', client.native.bridge.ARMS[0], 0,
            'collection', identity, True, False, self.session['config_sha256'])
        parameter = SimpleNamespace(shape=(2, 3), device='cpu', dtype='float32', copy_=Mock())
        base = SimpleNamespace(copy_=Mock())
        model = SimpleNamespace(named_parameters=lambda: [('layer.lora_A.default.weight', parameter), ('base.weight', base)])
        loaded = SimpleNamespace(binding=stage, optimizer=None, observed=identity,
            verify_unchanged=Mock(return_value=identity), engine=SimpleNamespace(model=model,
                torch=SimpleNamespace(no_grad=nullcontext)))
        actor = client.SharedEngine(loaded, self.session)
        archive = SimpleNamespace(keys=lambda: ['layer.lora_A.weight'],
            get_slice=lambda name: SimpleNamespace(get_shape=lambda: (2, 3)),
            get_tensor=lambda name: SimpleNamespace(to=lambda **kwargs: 'new_tensor'))
        module = SimpleNamespace(safe_open=lambda *args, **kwargs: nullcontext(archive))
        return actor, session, submission, module, parameter, base

    def test_reload_only_lora_same_resident_no_optimizer(self):
        actor, session, submission, module, parameter, base = self.reload_fixture()
        identity = client.native.bridge.AdapterIdentity.from_document(session['adapter'])
        with patch.dict('sys.modules', {'safetensors': module}), patch.object(client.native,
                'observe_adapter', return_value=identity):
            receipt = client.reload_at_boundary(actor, session, submission)
        parameter.copy_.assert_called_once_with('new_tensor')
        base.copy_.assert_not_called()
        self.assertEqual(actor.session['generation'], 1)
        self.assertIsNone(actor.loaded.optimizer)
        self.assertEqual(receipt['resident_process'], client.native.process_identity())

    def test_reload_hash_failure_poisoned_not_used(self):
        actor, session, submission, module, parameter, base = self.reload_fixture()
        with patch.dict('sys.modules', {'safetensors': module}), patch.object(client.native,
                'observe_adapter', return_value=None):
            with self.assertRaisesRegex(ValueError, 'actual_reloaded_adapter_hash'):
                client.reload_at_boundary(actor, session, submission)
        self.assertTrue(actor.poisoned)
        with self.assertRaisesRegex(ValueError, 'readonly_math_shared_actor'):
            actor.verify_base()

    def test_reload_requires_own_completed_barrier(self):
        actor, session, submission, module, parameter, base = self.reload_fixture()
        submission = dict(submission, path=str(self.shared/'generation_000000'/'F1.json'))
        with self.assertRaisesRegex(ValueError, 'own_barrier_receipt'):
            client.reload_at_boundary(actor, session, submission)
        parameter.copy_.assert_not_called()

    def test_reload_rejects_unpublished_valid_adapter(self):
        actor, session, submission, module, parameter, base = self.reload_fixture()
        session['adapter'] = deepcopy(self.session['adapter'])
        with self.assertRaisesRegex(ValueError, 'published_adapter_binding'):
            client.reload_at_boundary(actor, session, submission)
        parameter.copy_.assert_not_called()

    def test_integrated_cycle_six_train_calls_six_parent_slots_no_sleep_claim(self):
        tasks = [dict(task, question='Compute 31 times 21.') for task in self.tasks]
        client.shared.write(self.lane.parent/'TRAIN.json', [tasks])
        self.output = self.lane/'cycle001'
        engine = self.engine()
        identity = client.native.bridge.AdapterIdentity.from_document(self.session['adapter'])
        engine.verify_base = lambda: identity
        parents = []
        def parent(lane, task, experience, cycle, episode, phase):
            parents.append((task['id'], phase))
            experience.append(client.math.policy.event('parent', 'Check the conflicting computation.', 'TRAIN', {}))
        with patch.object(client.math, 'parent', side_effect=parent), patch.object(
                client.math.policy.previous.original.source, 'judge', return_value={'correct': False}), patch.object(
                client.time, 'time', return_value=client.math.NATIVE-300):
            result = client.collect_cycle(self.lane, engine, 1, tasks)
        self.assertEqual(len(parents), 6)
        self.assertEqual(result['submission']['source_calls'], 6)
        complete = client.shared.read(self.output/'TRAIN_COMPLETE.json')
        self.assertFalse(complete['sleep_complete'])
        self.assertFalse(complete['readout_complete'])
        self.assertEqual(result['carry']['actor'], 'child')
        history = client.shared.read(self.output/'TRAIN_EXPERIENCE.json')
        self.assertEqual(sum('"correct": false' in event['text'] for event in history), 2)
        self.assertFalse((self.output/'COMPLETE.json').exists())


if __name__ == '__main__':
    unittest.main()
