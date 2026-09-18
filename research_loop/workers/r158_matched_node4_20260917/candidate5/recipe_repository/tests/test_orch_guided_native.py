"""Mock-native CPU integration only: no model imports, task generation or GPU."""

from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from gpu import orch_guided_native as native
from organism_v6 import orch_guided_bridge as bridge
from organism_v6.experienced_event_goal_replay_layout import GoalReplayLayout
from tests.test_experienced_event_two_hop_lesson import Tokenizer


BASE_NAME = 'base_model.model.model.layer.base_layer.weight'
LORA_NAMES = ('base_model.model.model.layer.lora_A.default.weight',
              'base_model.model.model.layer.lora_B.default.weight')


def digest(text):
    return sha256(text.encode()).hexdigest()


class Tensor:
    def __init__(self, value, dtype='float32'):
        self.value, self.dtype, self.requires_grad = value, dtype, False

    def requires_grad_(self, value):
        self.requires_grad = value


def measured_hash(parameters):
    return digest(json.dumps({name: tensor.value for name, tensor in parameters.items()}, sort_keys=True))


class Model:
    def __init__(self, value):
        self.parameters = {BASE_NAME: Tensor('frozen-base', 'bfloat16'),
                           **{name: Tensor(value + str(index)) for index, name in enumerate(LORA_NAMES)}}
        self.buffer = Tensor('buffer', 'float32')
        self.peft_config = {'default': SimpleNamespace(r=8, lora_alpha=16, lora_dropout=0.05,
            target_modules=native.source.native.TARGET_MODULES, bias='none', modules_to_save=None,
            use_dora=False, use_rslora=False)}
        self.active_adapters = ['default']
        self.config = SimpleNamespace(use_cache=True)
        self.training = False
        self.checkpointing = None

    def named_parameters(self):
        return iter(self.parameters.items())

    def state_dict(self, keep_vars=True):
        return dict(self.parameters, **{'base_model.model.model.buffer': self.buffer})

    def modules(self):
        return iter((self, SimpleNamespace(disable_adapters=False)))

    def disable_adapters(self):
        raise AssertionError('mixin method must not be called')

    def gradient_checkpointing_enable(self, **kwargs):
        self.checkpointing = kwargs

    def enable_input_require_grads(self):
        self.input_grads = True

    def train(self):
        self.training = True


class Engine:
    def __init__(self, options, tokenizer, *, check):
        self.options, self.tokenizer, self.check = options, tokenizer, check
        self.model = Model((Path(options.adapter_dir) / 'adapter.bin').read_text())
        self.base_references = {'model.layer.weight': self.model.parameters[BASE_NAME],
                                'model.buffer': self.model.buffer}
        self.seeds, self.optimizers = [], []
        self.torch = SimpleNamespace(float32='float32', manual_seed=self.seeds.append,
                                     optim=SimpleNamespace(AdamW=self.adamw))

    def adamw(self, parameters, **kwargs):
        optimizer = SimpleNamespace(parameters=parameters, kwargs=kwargs, state={})
        self.optimizers.append(optimizer)
        return optimizer


def adapter(path, value):
    path.mkdir(parents=True)
    (path / 'adapter.bin').write_text(value)
    (path / 'adapter_config.json').write_text('{"synthetic_fixture":true}')
    model = Model(value)
    return bridge.AdapterIdentity(str(path), measured_hash({name: model.parameters[name] for name in LORA_NAMES}),
        measured_hash({'model.layer.weight': model.parameters[BASE_NAME], 'model.buffer': model.buffer}),
        tuple((name, bridge.file_sha256(path / name)) for name in ('adapter.bin', 'adapter_config.json')))


def readout_subprocess(path):
    document = json.loads(Path(path).read_text())
    binding = bridge.StageBinding(**dict(document['binding'],
        adapter=bridge.AdapterIdentity.from_document(document['binding']['adapter']),
        receipt_refs=tuple(bridge.ReceiptRef(**reference) for reference in document['binding']['receipt_refs'])))
    with patch.object(native, 'state_hash', measured_hash):
        loaded = native.load_readout(binding, model_dir=document['model_dir'], device='cuda:0',
            gpu_uuid='synthetic-gpu', context=native.StageContext(), check=lambda phase: None,
            predecessor_processes=tuple(tuple(value) for value in document['predecessors']),
            engine_factory=Engine, tokenizer_loader=lambda directory: Tokenizer())
        print(json.dumps(dict(process=loaded.process, observed=loaded.verify_unchanged().document(),
            model_imports=[name for name in ('torch', 'peft', 'transformers') if name in sys.modules])))


class NativeSeamTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.initial = adapter(self.root / 'initial', 'original')
        self.contract = bridge.CallerContract(5, 4, 'RESET_EACH_CYCLE', json.dumps(dict(
            optimizer='AdamW', optimizer_kwargs=dict(betas=[0.9, 0.999], eps=1e-8,
                weight_decay=0.01, amsgrad=False, foreach=False, fused=False),
            learning_rate=3e-5, seed=7, native_protocol_sha256=digest('synthetic-protocol'))))
        self.hash_patch = patch.object(native, 'state_hash', measured_hash)
        self.hash_patch.start()
        self.addCleanup(self.hash_patch.stop)
        self.process_patch = patch.object(native, '_USED_PROCESSES', set())
        self.process_patch.start()
        self.addCleanup(self.process_patch.stop)

    def lineage(self, arm=bridge.ARMS[0]):
        return bridge.ArmLineage('synthetic-run', arm, str(self.root / 'outputs'), self.initial)

    def kwargs(self, context=None):
        return dict(model_dir=str(self.root), device='cuda:0', gpu_uuid='synthetic-gpu',
            context=context or native.StageContext(), check=lambda phase: None,
            engine_factory=Engine, tokenizer_loader=lambda directory: Tokenizer())

    def complete(self, plan):
        output = self.initial if plan.lineage.arm == bridge.ARMS[1] else adapter(
            Path(plan.output_path), plan.lineage.arm + str(plan.cycle))
        path = self.root / 'outputs' / plan.lineage.run_id / plan.lineage.arm / ('cycle-' + str(plan.cycle)) / 'COMPLETE.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(dict(schema='ORCH_GUIDED_BRIDGE_COMPLETION_V1', status='COMPLETE',
            plan_sha256=bridge.document_sha256(plan.document()), run_id=plan.lineage.run_id,
            arm=plan.lineage.arm, cycle=plan.cycle, input_adapter=plan.input_adapter.document(),
            output_adapter=output.document(), contract=plan.contract.manifest(plan.lineage.arm))))
        return bridge.complete_cycle(plan, bridge.ReceiptRef(str(path), bridge.file_sha256(path)))

    def capture(self, binding):
        return dict(run_id=binding.run_id, arm=binding.arm, cycle=binding.cycle,
            actor=binding.adapter.document(), origin='ACTUAL_CHILD_OUTPUT', complete=True,
            admitted=True, error=None, student_prefix=[dict(role='system', content='fixture system'),
                dict(role='user', content='fixture input')], response=dict(raw='own bytes λ\n\n'))

    def test_prior_child_in_both_phases_three_cycles_all_arms(self):
        process_counter = 100
        optimizer_ids = []
        for arm in bridge.ARMS:
            lineage = self.lineage(arm)
            for cycle in range(1, 4):
                plan = bridge.plan_cycle(lineage, self.contract)
                guidance = () if arm == bridge.ARMS[2] else ('synthetic private guidance',)
                collector = native.load_collection(plan, **self.kwargs(native.StageContext(guidance)))
                self.assertEqual(collector.engine.options.adapter_dir, plan.input_adapter.path)
                self.assertEqual(collector.engine.options.phase, 'readout')
                self.assertEqual(collector.observed, plan.input_adapter)
                self.assertEqual(collector.verify_unchanged(), plan.input_adapter)
                if arm == bridge.ARMS[1]:
                    with self.assertRaisesRegex(ValueError, 'frozen_training_forbidden'):
                        native.load_training(plan, **self.kwargs())
                else:
                    trainer = native.load_training(plan, **self.kwargs())
                    self.assertEqual(trainer.engine.options.phase, 'readout')
                    self.assertEqual(trainer.engine.options.adapter_dir, collector.engine.options.adapter_dir)
                    self.assertEqual(trainer.observed, collector.observed)
                    self.assertEqual(trainer.engine.seeds, [7])
                    self.assertTrue(trainer.engine.model.training)
                    self.assertFalse(trainer.engine.model.parameters[BASE_NAME].requires_grad)
                    self.assertTrue(all(trainer.engine.model.parameters[name].requires_grad for name in LORA_NAMES))
                    self.assertEqual(trainer.optimizer.state, {})
                    self.assertEqual(trainer.optimizer.kwargs, dict(
                        lr=3e-5, betas=(0.9, 0.999), eps=1e-8, weight_decay=0.01,
                        amsgrad=False, foreach=False, fused=False))
                    optimizer_ids.append(trainer.optimizer)
                lineage, binding = self.complete(plan)
                process_counter += 1
                with patch.object(native, 'process_identity', return_value=('synthetic-boot', process_counter, 1)):
                    reader = native.load_readout(binding, predecessor_processes=(collector.process,), **self.kwargs())
                    self.assertEqual(reader.observed, binding.adapter)
                    self.assertEqual(reader.verify_unchanged(), binding.adapter)
                if arm != bridge.ARMS[1]:
                    self.assertNotEqual(reader.observed.state_sha256, collector.observed.state_sha256)
        self.assertEqual(len({id(optimizer) for optimizer in optimizer_ids}), 6)

    def test_default_factory_receives_saved_adapter_not_train_phase(self):
        plan = bridge.plan_cycle(self.lineage(), self.contract)
        kwargs = self.kwargs()
        kwargs.pop('engine_factory')
        kwargs.pop('tokenizer_loader')
        with patch.object(native.source, 'Engine', wraps=Engine) as factory, patch.object(
                native.source.native, 'load_local_tokenizer', return_value=Tokenizer()):
            loaded = native.load_training(plan, **kwargs)
        self.assertEqual(factory.call_args.args[0].phase, 'readout')
        self.assertEqual(loaded.engine.options.adapter_dir, self.initial.path)

    def test_wrong_mounted_adapter_rejected_not_echoed(self):
        plan = bridge.plan_cycle(self.lineage(), self.contract)
        def wrong(options, tokenizer, check):
            engine = Engine(options, tokenizer, check=check)
            engine.model.parameters[LORA_NAMES[0]].value = 'wrong-actual-tensor'
            return engine
        with self.assertRaisesRegex(ValueError, 'loaded_adapter_state_path_or_files_drift'):
            native.load_training(plan, **dict(self.kwargs(), engine_factory=wrong))

    def test_mounted_base_measured_even_when_old_references_unchanged(self):
        plan = bridge.plan_cycle(self.lineage(), self.contract)
        def wrong(options, tokenizer, check):
            engine = Engine(options, tokenizer, check=check)
            engine.model.parameters[BASE_NAME] = Tensor('different-mounted-base')
            return engine
        with self.assertRaisesRegex(ValueError, 'loaded_adapter_state_path_or_files_drift'):
            native.load_training(plan, **dict(self.kwargs(), engine_factory=wrong))

    def test_stale_original_reset_at_cycle2_fails(self):
        first = bridge.plan_cycle(self.lineage(), self.contract)
        lineage, unused = self.complete(first)
        plan = bridge.plan_cycle(lineage, self.contract)
        def reset(options, tokenizer, check):
            return Engine(SimpleNamespace(**dict(vars(options), adapter_dir=self.initial.path)), tokenizer, check=check)
        with self.assertRaisesRegex(ValueError, 'loaded_adapter_state_path_or_files_drift'):
            native.load_training(plan, **dict(self.kwargs(), engine_factory=reset))

    def test_trainable_or_disabled_or_extra_adapter_fails(self):
        plan = bridge.plan_cycle(self.lineage(), self.contract)
        def invalid(options, tokenizer, check):
            engine = Engine(options, tokenizer, check=check)
            mutation(engine)
            return engine
        changes = (
            lambda engine: engine.model.parameters[BASE_NAME].requires_grad_(True),
            lambda engine: setattr(engine.model, 'disable_adapters', True),
            lambda engine: setattr(engine.model, 'active_adapters', ['other']),
            lambda engine: engine.model.peft_config.update(other=engine.model.peft_config['default']),
            lambda engine: setattr(engine.model.peft_config['default'], 'r', 16),
        )
        for mutation in changes:
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                native.load_training(plan, **dict(self.kwargs(), engine_factory=invalid))

    def test_same_process_readout_and_context_leak_rejected_before_model_load(self):
        plan = bridge.plan_cycle(self.lineage(), self.contract)
        collector = native.load_collection(plan, **self.kwargs(native.StageContext(('guidance',))))
        unused, binding = self.complete(plan)
        with patch.object(native.source, 'Engine', side_effect=AssertionError('must not load')):
            with self.assertRaisesRegex(ValueError, 'fresh_readout_process_required'):
                native.load_readout(binding, predecessor_processes=(collector.process,), **self.kwargs())
            for context in (native.StageContext(('guidance',)), native.StageContext(transient_context=('cached turn',)),
                            native.StageContext(sleep_prompt='sleep')):
                with self.subTest(context=context), self.assertRaises(ValueError):
                    native.load_readout(binding, **self.kwargs(context))

    def test_output_readout_in_real_fresh_cpu_subprocess(self):
        plan = bridge.plan_cycle(self.lineage(), self.contract)
        trainer = native.load_training(plan, **self.kwargs())
        unused, binding = self.complete(plan)
        document = dict(binding=asdict(binding), model_dir=str(self.root), predecessors=[trainer.process])
        path = self.root / 'readout.json'
        path.write_text(json.dumps(document))
        result = subprocess.run([sys.executable, '-B', '-c',
            'from tests.test_orch_guided_native import readout_subprocess; import sys; readout_subprocess(sys.argv[1])',
            str(path)], check=True, text=True, capture_output=True, timeout=20)
        observed = json.loads(result.stdout)
        self.assertNotEqual(tuple(observed['process']), trainer.process)
        self.assertEqual(observed['observed'], binding.adapter.document())
        self.assertEqual(observed['model_imports'], [])

    def test_readonly_guard_detects_mutation(self):
        plan = bridge.plan_cycle(self.lineage(), self.contract)
        loaded = native.load_collection(plan, **self.kwargs(native.StageContext(('guidance',))))
        loaded.engine.model.buffer = Tensor('changed-buffer')
        with self.assertRaisesRegex(ValueError, 'loaded_stage_state_changed'):
            loaded.verify_unchanged()

    def test_mutated_receipt_rejected_before_loading(self):
        plan = bridge.plan_cycle(self.lineage(), self.contract)
        lineage, binding = self.complete(plan)
        Path(lineage.receipts[-1].path).write_text('{}')
        with self.assertRaisesRegex(ValueError, 'prior_receipt_hash_drift'):
            native.load_readout(binding, predecessor_processes=(('old-boot', 1, 1),), **self.kwargs())

    def test_inherited_fork_rejected_before_loading(self):
        plan = bridge.plan_cycle(self.lineage(), self.contract)
        with patch.object(native, '_IMPORT_PID', -1), self.assertRaisesRegex(
                ValueError, 'native_stage_requires_exec_not_inherited_fork'):
            native.load_training(plan, **self.kwargs())

    def test_nonempty_optimizer_state_rejected(self):
        plan = bridge.plan_cycle(self.lineage(), self.contract)
        def stale(options, tokenizer, check):
            engine = Engine(options, tokenizer, check=check)
            engine.torch.optim.AdamW = lambda *args, **kwargs: SimpleNamespace(state={'old': 1})
            return engine
        with self.assertRaisesRegex(ValueError, 'fresh_optimizer_required'):
            native.load_training(plan, **dict(self.kwargs(), engine_factory=stale))

    def test_exact_capture_projection_and_dynamic_native_masks(self):
        binding = bridge.plan_cycle(self.lineage(), self.contract).binding('collection')
        capture = self.capture(binding)
        tokenizer = Tokenizer()
        projected, encoded = native.encode_child_captures([capture], [bridge.document_sha256(capture)],
            binding, tokenizer, private_guidance=('guidance',), max_context=2048, max_supervised_tokens=768)
        self.assertEqual(projected[0]['assistant'], capture['response']['raw'])
        self.assertEqual(tokenizer.decode(encoded[0].target_ids), capture['response']['raw'] + tokenizer.eos_token)
        self.assertEqual(encoded[0].labels[-1], -100)
        self.assertEqual(encoded[0].target_ids[-1], tokenizer.eos_token_id)
        self.assertNotIn('guidance', tokenizer.decode(encoded[0].input_ids))

    def test_capture_hash_guidance_special_tokens_and_token_budgets_fail(self):
        binding = bridge.plan_cycle(self.lineage(), self.contract).binding('collection')
        for target, budget in (('guidance', 768), ('bad <|im_end|> token', 768), ('many words here', 2)):
            capture = self.capture(binding)
            capture['response']['raw'] = target
            with self.subTest(target=target), self.assertRaises(ValueError):
                native.encode_child_captures([capture], [bridge.document_sha256(capture)], binding,
                    Tokenizer(), private_guidance=('guidance',), max_context=2048, max_supervised_tokens=budget)
        capture = self.capture(binding)
        digest_before = bridge.document_sha256(capture)
        capture['response']['raw'] += 'tampered'
        with self.assertRaisesRegex(ValueError, 'child_capture_hash_drift'):
            native.encode_child_captures([capture], [digest_before], binding, Tokenizer(),
                private_guidance=('guidance',), max_context=2048, max_supervised_tokens=768)

    def test_tokenizer_roundtrip_failure_not_silently_repaired(self):
        binding = bridge.plan_cycle(self.lineage(), self.contract).binding('collection')
        capture = self.capture(binding)
        tokenizer = Tokenizer()
        decode = tokenizer.decode
        tokenizer.decode = lambda values, **kwargs: decode(values, **kwargs).rstrip()
        with self.assertRaisesRegex(ValueError, 'exact_native_token_roundtrip_required'):
            native.encode_child_captures([capture], [bridge.document_sha256(capture)], binding, tokenizer,
                private_guidance=('guidance',), max_context=2048, max_supervised_tokens=768)

    def test_variable_replay_and_reference_denominators(self):
        layout = GoalReplayLayout(5, 4)
        rows = tuple(native.source.native.EncodedRow((8,) + (42,) * (index % 4 + 1) + (1, 9),
            (-100,) + (42,) * (index % 4 + 1) + (1, -100), (42,) * (index % 4 + 1) + (1,))
            for index in range(layout.row_count))
        encoded = native.assemble_replay(rows[:222], rows[222:], layout,
                                         legacy_reference=rows[:222], eos_token_id=1)
        for update in range(1, layout.updates + 1):
            full = native.training_batch(encoded, layout, update, pad_id=0)
            off = native.training_batch(encoded, layout, update, pad_id=0, replay_arm='NEW_TRAJECTORY_LOSS_OFF')
            self.assertEqual(full[1]['input_ids'], off[1]['input_ids'])
            self.assertEqual(full[1]['attention_mask'], off[1]['attention_mask'])
            self.assertEqual(full[2], off[2])
            self.assertEqual(off[4], off[3] / off[2])
            self.assertEqual(full[4], 1.0)
        with self.assertRaisesRegex(ValueError, 'legacy_reference_encoding_drift'):
            native.assemble_replay(rows[:222], rows[222:], layout,
                                  legacy_reference=rows[1:223], eos_token_id=1)

    def test_historical_recipe_batch_parity(self):
        from gpu import astra_goal_quality_train as historical
        from tests.test_astra_goal_quality_train import encoded_fixture

        encoded = encoded_fixture()
        layout = GoalReplayLayout(1452, 4)
        for arm in ('FULL_TARGET', 'NEW_TRAJECTORY_LOSS_OFF'):
            for update in (1, 7, 64, 128, 129, 1464, 2928):
                self.assertEqual(native.training_batch(encoded, layout, update, pad_id=151643, replay_arm=arm),
                                 historical.training_batch(encoded, update, arm))

    def test_imports_require_no_model_libraries(self):
        subprocess.run([sys.executable, '-B', '-c',
            'import sys; from gpu import orch_guided_native; '
            'assert not any(name in sys.modules for name in ("torch","transformers","peft","tokenizers"))'],
            check=True, timeout=20)


if __name__ == '__main__':
    unittest.main()
