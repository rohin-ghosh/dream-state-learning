"""CPU fixtures only; no tokenizer/model loads, training, GPU, or live outcomes."""
import copy
from dataclasses import asdict
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch


REPO = Path('/data/home/rohing/dream-state').resolve()
sys.path[:0] = [str(REPO), str(REPO / 'tests')]
spec = importlib.util.spec_from_file_location('born_write', '/tmp/astra_born_process_write_20260912.py')
writer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(writer)
from organism_v6 import born_rulegame_formation as born
from organism_v6 import model_backend, rulegame_parenting_diagnostic as diagnostic
from organism_v6 import rulegame_process_material as exporter
from organism_v6 import train_adapter_v3 as trainer
from test_born_rulegame_formation import RoleBackend
from test_rulegame_process_material import Tokenizer


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, allow_nan=False) + '\n')


def weights(path, value=.125):
    header, states, chunks = {}, {}, []
    offset = 0
    for group, projections in (('self_attn', ('q_proj', 'k_proj', 'v_proj', 'o_proj')),
                                ('mlp', ('gate_proj', 'up_proj', 'down_proj'))):
        for projection in projections:
            for part, shape in (('A', [8, 2]), ('B', [2, 8])):
                name = f'base_model.model.model.layers.0.{group}.{projection}.lora_{part}.weight'
                payload = struct.pack('<16f', *([value] * 16))
                header[name] = dict(dtype='F32', shape=shape, data_offsets=[offset, offset + len(payload)])
                states[name] = dict(shape=shape, dtype='torch.float32', sha256=hashlib.sha256(payload).hexdigest())
                offset += len(payload)
                chunks.append(payload)
    encoded = json.dumps(header).encode()
    path.write_bytes(struct.pack('<Q', len(encoded)) + encoded + b''.join(chunks))
    return states


class Tensor:
    def __init__(self, rows):
        self.rows = rows

    def detach(self):
        return self

    def cpu(self):
        return self

    def tolist(self):
        return self.rows


class BindingTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='born-write-cpu-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.model, self.parent = self.root / 'model', self.root / 'birth/run/AUTH/adapter'
        self.model.mkdir()
        self.parent.mkdir(parents=True)
        save(self.model / 'config.json', dict(model_type='qwen2', num_hidden_layers=1))
        self.old, *_ = writer.apis(REPO)
        self.cfg = self.old.fit_config(trainer, str(self.model))
        self.saved = dict(r=8, lora_alpha=16, lora_dropout=.05, bias='none', peft_type='LORA',
            target_modules=list(trainer.ALL_PROJ), base_model_name_or_path=str(self.model))
        save(self.parent / 'adapter_config.json', self.saved)
        self.states = weights(self.parent / 'adapter_model.safetensors')
        (self.parent / 'DONE').write_text('ok\n')
        save(self.parent / 'train_manifest.json', dict(recipe=trainer.RECIPE, empty=False, steps=64,
            nonfinite_batches=0, final_loss=.4, config=asdict(self.cfg), base_model=str(self.model), lora=dict(n_layers=1)))
        save(self.parent / 'train_meta.json', dict(fixture=True))
        self.pin = dict(schema=born.BIRTH_PIN_SCHEMA, status='COMPLETE', birth_arm='AUTH', birth_plan_sha256='a' * 64,
            completion_receipt_sha256='b' * 64, origin=born.ORIGIN, model_origin=born.MODEL_ORIGIN,
            child_identity=model_backend.configured_generation_identity(str(self.model), str(self.parent)),
            model_files=diagnostic.model_hashes(self.model))
        self.custody = dict(fit_root=str(self.root / 'birth'), fit_plan_sha256='a' * 64,
            fit_release=str(self.root / 'birth-release/validation.json'), fit_release_sha256='c' * 64)
        self.proof = dict(birth_pin=self.pin, custody=self.custody, parent_files=trainer._warm_inventory(self.parent),
            parent_steps=64, terminal_sha256='b' * 64, auth_receipt_sha256='d' * 64, birth_driver_sha256=writer.BIRTH_SHA,
            full_release=True, phase_complete=True)
        self.birth_check = patch.object(writer, 'checked_birth', return_value=self.proof)
        self.birth_check.start()
        self.addCleanup(self.birth_check.stop)
        self.binding = born.make_binding(self.pin, expected_birth_pin_sha256=diagnostic.value_hash(self.pin))
        self.binding_sha = diagnostic.value_hash(self.binding)
        self.capture = born.capture_formation(RoleBackend(self.binding), self.binding,
            expected_binding_sha256=self.binding_sha, cutoff=1000, clock=lambda: 1)
        self.capture_file = self.root / 'original.json'
        save(self.capture_file, self.capture)
        self.capture_sha = writer.digest(self.capture_file)
        self.projection = writer.project_capture(REPO, self.capture_file, self.capture_sha, self.binding_sha, self.root / 'projection')
        self.bound = writer.bound_exporter(REPO, **self.projection)
        self.candidate = self.bound.inspect_capture(self.projection['capture_root'], protocol=exporter.PROTOCOL_V2)
        self.review = exporter.review_template(self.candidate, protocol=exporter.PROTOCOL_V2)
        self.review['context_distillation_acknowledged'] = True
        for row in self.review['reviews']:
            row.update(decision='accept', notes='CPU fixture acceptance, not scientific evidence')
        self.tokenizer = Tokenizer()

    def prepare(self):
        return writer.prepare(REPO, self.projection, self.custody, self.review, self.candidate, self.tokenizer, self.root / 'write')

    def load_plan(self, prepared):
        return diagnostic.read(Path(prepared['root']) / 'plan.json')

    def finished_fit(self, prepared, arm):
        request = writer.worker_binding(**prepared, arm=arm, tokenizer=self.tokenizer)
        adapter = Path(request['out_dir'])
        adapter.parent.mkdir(parents=True)
        observer = writer.forward_observer(**prepared, arm=arm)
        plan = self.load_plan(prepared)
        for index in range(12):
            batch = self.old.expected_forward_batch(plan['tokens'][arm], [index % 2, 1 - index % 2])
            observer(None, (), {key: Tensor(value) for key, value in batch.items()})
        adapter.mkdir()
        (adapter / 'DONE').write_text('ok\n')
        save(adapter / 'adapter_config.json', self.saved)
        weights(adapter / 'adapter_model.safetensors', .25)
        warm = dict(mode='WEIGHT_WARM_START_FRESH_OPTIMIZER', optimizer_initialization='fresh_per_write',
            optimizer_state_restored=False, optimizer_state_saved=False, initialized_loaded_state_check=True,
            base_frozen=True, adapter_count=1, phase_seed=2, phase_steps=12, parent_unchanged=True,
            parent_path=str(self.parent), parent_files=self.proof['parent_files'], parent_files_after=self.proof['parent_files'],
            parent_cumulative_steps=64, cumulative_steps=76, trainer_sha256=writer.digest(trainer.__file__),
            source_state=self.states, initialized_state=self.states, dtype_conversions={},
            trainable_names=[name.replace('.weight', '.default.weight') for name in self.states])
        tokens = plan['tokens'][arm]
        manifest = dict(recipe=trainer.RECIPE, config=plan['config'], base_model=str(self.model), empty=False,
            steps=12, micro_batches=12, epochs_run=12, nonfinite_batches=0, final_loss=.3, mean_loss_per_epoch=[.3] * 12,
            corpus=dict(file=arm + '.json', sha256=request['corpus_sha'], n_items=2, n_encoded=2, n_skipped_no_target=0),
            tokens=tokens['tokens'], train_tokens_seen=tokens['train_tokens_seen'], warm_start=warm,
            truncation=dict(overflow='split', items_truncated=0, context_tokens_dropped=0, target_tokens_dropped=0, items_split=0,
                segments_from_splits=0, max_segment_tokens=tokens['max_segment_tokens']),
            packing=dict(mode='one_item_per_sequence', n_sequences=2, n_groups=2, isolation_check=dict(ran=False)),
            lora=dict(rank=8, alpha=16, dropout=.05, scaling=2.0, target_modules=list(trainer.ALL_PROJ),
                layers='all', n_layers=1, freeze_a=False, trainable_params=224))
        save(adapter / 'train_manifest.json', manifest)
        save(adapter / 'train_meta.json', dict(recipe=trainer.RECIPE, n_texts=2, steps=12, tokens=tokens['train_tokens_seen'],
            rank=8, epochs=12, lr=1e-4, seed=2, final_loss=.3))
        return adapter

    def test_lossless_original_capture_role_replay_and_unchanged_exporter(self):
        self.assertEqual(writer.digest(Path(self.projection['capture_root']) / 'native_capture.json'), self.capture_sha)
        self.assertEqual(self.candidate['status'], 'AVAILABLE_PENDING_MAIN_REVIEW')
        self.assertEqual(len(self.candidate['candidates']), 4)
        self.assertIsNot(self.bound.diagnostic, diagnostic)
        self.assertEqual(self.bound.transform_context.__code__.co_code, exporter.transform_context.__code__.co_code)
        self.assertFalse(diagnostic.check_capture(self.projection['capture_root'], protocol='interaction_v3')['ok'])
        for row in self.candidate['candidates']:
            self.assertNotIn(exporter.RESTATEMENT_MARKER, row['context'])
            self.assertEqual(row['target'], self.capture['calls'][int(row['selected']['call_id'])]['envelope']['response']['text'])

    def test_prepare_and_both_worker_bindings_same_immutable_birth(self):
        before = trainer._warm_inventory(self.parent)
        prepared = self.prepare()
        plan = self.load_plan(prepared)
        requests = [writer.worker_binding(**prepared, arm=arm, tokenizer=self.tokenizer) for arm in writer.ARMS]
        self.assertEqual([request['init_adapter'] for request in requests], [str(self.parent)] * 2)
        self.assertNotEqual(requests[0]['out_dir'], requests[1]['out_dir'])
        self.assertEqual(before, trainer._warm_inventory(self.parent))
        self.assertEqual(plan['birth']['birth_pin'], self.binding['birth'])
        for arm, request in zip(writer.ARMS, requests):
            self.assertEqual(len(request['items']), 2)
            cfg = request['cfg']
            self.assertEqual((cfg.rank, cfg.alpha, cfg.dropout, cfg.lr, cfg.seed, cfg.batch_size, cfg.max_steps, cfg.epochs),
                (8, 16, .05, 1e-4, 2, 2, 12, 12))
            self.assertFalse(cfg.pack)
            self.assertFalse(plan['boundary']['target_tokens_matched'])
            for row in plan['tokens'][arm]['rows']:
                self.assertEqual(row['labels'][:row['context_tokens']], [-100] * row['context_tokens'])
                self.assertEqual(row['labels'][-1], self.tokenizer.eos_token_id)
                self.assertEqual(row['input_tokens'], row['context_tokens'] + row['target_tokens'])
        self.assertFalse((Path(prepared['root']) / 'fits').exists())

    def test_reject_projection_edit_even_if_inventory_resealed(self):
        root = Path(self.projection['capture_root'])
        path = next((root / 'calls').glob('*.request.json'))
        content = diagnostic.read(path)
        content['identity']['adapter_input'] = None
        save(path, content)
        save(root / 'manifest.json', dict(files=diagnostic.tree_hashes(root, ('manifest.json',))))
        with self.assertRaisesRegex(ValueError, 'projection differs'):
            writer.bound_exporter(REPO, **self.projection)

    def test_reject_old_off_capture_or_different_birth(self):
        changed = copy.deepcopy(self.proof)
        changed['birth_pin']['completion_receipt_sha256'] = 'e' * 64
        with patch.object(writer, 'checked_birth', return_value=changed), self.assertRaisesRegex(ValueError, 'custody/formation'):
            self.prepare()
        invalid = copy.deepcopy(self.capture)
        invalid['calls'][0]['identity']['adapter_input'] = None
        save(self.capture_file, invalid)
        with self.assertRaises(ValueError):
            writer.project_capture(REPO, self.capture_file, writer.digest(self.capture_file), self.binding_sha, self.root / 'badprojection')

    def test_pending_review_and_wrong_candidate_fail_closed(self):
        self.review['reviews'][0]['decision'] = 'pending'
        with self.assertRaisesRegex(ValueError, 'acceptance'):
            self.prepare()
        self.assertFalse((self.root / 'write').exists())

    def test_no_overwrite_and_parent_mutation_detected(self):
        prepared = self.prepare()
        with self.assertRaises(ValueError):
            self.prepare()
        (self.parent / 'DONE').write_text('changed')
        with self.assertRaisesRegex(ValueError, 'parent inventory changed'):
            writer.worker_binding(**prepared, arm='P', tokenizer=self.tokenizer)

    def test_material_and_plan_tamper_fail_closed(self):
        prepared = self.prepare()
        path = Path(prepared['root']) / 'material/corpora/P.json'
        path.write_text('{}\n')
        with self.assertRaisesRegex(ValueError, 'material changed'):
            writer.worker_binding(**prepared, arm='P', tokenizer=self.tokenizer)

    def test_no_native_tokenizer_substitution(self):
        prepared = self.prepare()
        tokenizer = Tokenizer()
        tokenizer.eos_token_id = 999999
        with self.assertRaisesRegex(ValueError, 'tokenizer or masks'):
            writer.worker_binding(**prepared, arm='P', tokenizer=tokenizer)

    def test_complete_pair_receipts_not_release_no_hash_divergence_requirement(self):
        prepared = self.prepare()
        self.finished_fit(prepared, 'P')
        self.finished_fit(prepared, 'A')
        receipt = writer.pair_receipt(**prepared)
        self.assertEqual(receipt['status'], 'PAIR_COMPLETE_NOT_RELEASED')
        self.assertTrue(receipt['release_required'])
        self.assertEqual(receipt['fits']['P']['adapter_files']['adapter_model.safetensors'],
            receipt['fits']['A']['adapter_files']['adapter_model.safetensors'])

    def test_missing_forward_rejects_completion(self):
        prepared = self.prepare()
        adapter = self.finished_fit(prepared, 'P')
        (adapter.parent / 'forwards/0001.json').unlink()
        with self.assertRaisesRegex(ValueError, 'observed forward'):
            writer.validate_fit(**prepared, arm='P')

    def test_forward_thirteenth_and_wrong_masks_rejected(self):
        prepared = self.prepare()
        stage = Path(prepared['root']) / 'fits/P'
        stage.mkdir(parents=True)
        observe = writer.forward_observer(**prepared, arm='P')
        tokens = self.load_plan(prepared)['tokens']['P']
        batch = self.old.expected_forward_batch(tokens, [0, 1])
        wrong = copy.deepcopy(batch)
        wrong['labels'][0][0] = wrong['input_ids'][0][0]
        with self.assertRaisesRegex(ValueError, 'row/input/label'):
            observe(None, (), {key: Tensor(value) for key, value in wrong.items()})
        for _ in range(12):
            observe(None, (), {key: Tensor(value) for key, value in batch.items()})
        with self.assertRaisesRegex(ValueError, 'forward number'):
            observe(None, (), {key: Tensor(value) for key, value in batch.items()})

    def test_warm_start_and_complete_receipt_mutations_rejected(self):
        prepared = self.prepare()
        adapter = self.finished_fit(prepared, 'P')
        path = adapter / 'train_manifest.json'
        baseline = diagnostic.read(path)
        mutations = [('parent_path', str(self.root / 'write/fits/A/adapter')), ('adapter_count', 2),
            ('optimizer_state_restored', True), ('initialized_loaded_state_check', False), ('phase_steps', 11),
            ('parent_files_after', {}), ('parent_unchanged', False), ('phase_seed', 3)]
        for field, value in mutations:
            with self.subTest(field=field):
                changed = copy.deepcopy(baseline)
                changed['warm_start'][field] = value
                save(path, changed)
                with self.assertRaises(ValueError):
                    writer.validate_fit(**prepared, arm='P')
        save(path, baseline)
        self.assertEqual(writer.validate_fit(**prepared, arm='P')['steps'], 12)

    def test_unknown_arm_and_fresh_output_enforced(self):
        prepared = self.prepare()
        with self.assertRaisesRegex(ValueError, 'only P/A'):
            writer.worker_binding(**prepared, arm='OFF', tokenizer=self.tokenizer)
        output = Path(prepared['root']) / 'fits/P/adapter'
        output.mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, 'fresh'):
            writer.worker_binding(**prepared, arm='P', tokenizer=self.tokenizer)

    def test_source_initial_state_hashes_are_checked_against_real_parent_bytes(self):
        prepared = self.prepare()
        adapter = self.finished_fit(prepared, 'P')
        path = adapter / 'train_manifest.json'
        manifest = diagnostic.read(path)
        name = next(iter(manifest['warm_start']['source_state']))
        manifest['warm_start']['source_state'][name]['sha256'] = 'a' * 64
        manifest['warm_start']['initialized_state'][name]['sha256'] = 'a' * 64
        save(path, manifest)
        with self.assertRaisesRegex(ValueError, 'tensor bytes mismatch'):
            writer.validate_fit(**prepared, arm='P')

    def test_explicit_dtype_conversion_is_byte_verified(self):
        prepared = self.prepare()
        adapter = self.finished_fit(prepared, 'P')
        path = adapter / 'train_manifest.json'
        manifest = diagnostic.read(path)
        warm = manifest['warm_start']
        for name in warm['initialized_state']:
            warm['initialized_state'][name]['dtype'] = 'torch.bfloat16'
            warm['initialized_state'][name]['sha256'] = hashlib.sha256(b'\0\x3e' * 16).hexdigest()
            warm['dtype_conversions'][name] = dict(source='torch.float32', initialized='torch.bfloat16')
        save(path, manifest)
        self.assertEqual(writer.validate_fit(**prepared, arm='P')['steps'], 12)
        warm['initialized_state'][name]['sha256'] = 'a' * 64
        save(path, manifest)
        with self.assertRaisesRegex(ValueError, 'tensor bytes mismatch'):
            writer.validate_fit(**prepared, arm='P')


class CustodyTests(unittest.TestCase):
    def test_original_frozen_verifiers_and_terminal_pin_used(self):
        custody = dict(fit_root='/tmp/cpu-birth', fit_plan_sha256='a' * 64, fit_release='/tmp/cpu-release/validation.json', fit_release_sha256='b' * 64)
        root = Path(custody['fit_root'])
        plan = dict(phase='fit', model='/tmp/cpu-model', model_files={'config.json': 'c' * 64})
        fit = dict(adapter='/tmp/cpu-birth/run/AUTH/adapter', adapter_files={'DONE': 'd' * 64}, steps=64)
        driver = SimpleNamespace(verify_plan=Mock(return_value=(root, plan, ('cpu-api',))),
            accepted_release=Mock(return_value=dict(phase_complete=True, full_release=True)),
            audit_terminal=Mock(return_value=dict(phase_complete=True)), verify_fit=Mock(return_value=fit),
            verify_member=Mock(return_value=fit), read=Mock(return_value=fit), digest=Mock(side_effect=lambda path: 'e' * 64 if path.name == 'result.json' else 'f' * 64))
        with patch.object(writer, 'load_helper', return_value=driver), patch.object(model_backend, 'configured_generation_identity', return_value={'fixture': True}):
            result = writer.verify_birth(custody)
            self.assertEqual(result['birth_pin']['completion_receipt_sha256'], 'e' * 64)
            driver.accepted_release.assert_called_once_with(custody['fit_release'], custody['fit_release_sha256'], plan, custody['fit_plan_sha256'])
            driver.audit_terminal.assert_called_once()
            driver.verify_fit.assert_called_once_with(root, plan, ('cpu-api',), 'AUTH')
            driver.accepted_release.return_value['phase_complete'] = False
            with self.assertRaisesRegex(ValueError, 'incomplete or unreleased'):
                writer.verify_birth(custody)

    def test_subprocess_is_offline_cpu_and_no_native_import(self):
        result = SimpleNamespace(stdout='{"fixture": true}')
        with patch.object(writer.subprocess, 'run', return_value=result) as run:
            self.assertTrue(writer.checked_birth({'fixture': True})['fixture'])
        options = run.call_args.kwargs
        self.assertEqual(options['env']['CUDA_VISIBLE_DEVICES'], '')
        self.assertEqual(options['env']['HF_HUB_OFFLINE'], '1')
        self.assertEqual(options['timeout'], 300)
        self.assertNotIn('torch', sys.modules)
        self.assertNotIn('transformers', sys.modules)
        self.assertNotIn('vllm', sys.modules)


if __name__ == '__main__':
    unittest.main(verbosity=2)
