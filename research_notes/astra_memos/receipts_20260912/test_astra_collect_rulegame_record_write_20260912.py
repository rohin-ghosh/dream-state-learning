"""CPU-only synthetic receipts and in-memory safetensors; no native/GPU imports."""
import ast
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import struct
import sys
import tarfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

sys.dont_write_bytecode = True
PATH = Path('/tmp/astra_collect_rulegame_record_write_20260912.py')
spec = importlib.util.spec_from_file_location('record_write_collector_tested', PATH)
collector = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = collector
exec(compile(PATH.read_bytes(), str(PATH), 'exec'), collector.__dict__)


class CollectorTests(unittest.TestCase):
    def fixture(self, complete=2):
        plan = dict(python=str(collector.HOME / 'v2/venv/bin/python'), deadline=2000., lease_cutoff=3000.)
        controller = dict(plan_sha256=collector.PLAN_SHA, worker_seconds=600, cleanup_reserve=140, started_wall=100., hard_end=1300.)
        values = {str(collector.ROOT / 'run/controller.json'): controller}
        receipts, completed = {}, {}
        for index, arm in enumerate(collector.ARMS[:complete]):
            fit, stage = collector.ROOT / 'fits' / arm, collector.ROOT / 'run' / arm
            worker = dict(device='2', reserved_seconds=10., ok=True, returncode=0, error=None,
                          reservation_release_verified=True, owned_group_empty=True, gpu_processes_absent=True)
            launch = dict(token=arm + '-token', plan_sha256=collector.PLAN_SHA, hard_end=1300.)
            process = dict(argv=[plan['python'], '-B', str(collector.DRIVER), '_worker', '--root', str(collector.ROOT),
                '--arm', arm, '--plan-sha256', collector.PLAN_SHA, '--launch-token', launch['token'], '--allow-gpu'],
                pid=10 + index, pgid=10 + index, device='2', started=101. + index, timeout=600)
            receipt = dict(arm=arm, adapter=str(fit / 'adapter'), files={'adapter_model.safetensors': arm + '-weight'}, steps=12)
            receipts[arm] = receipt
            completed[arm] = dict(receipt, fit_manifest_sha256='fit-hash', supervision_sha256='worker-hash')
            values.update({str(fit / 'adapter/DONE'): {}, str(fit / 'manifest.json'): {'files': {'weight': arm}},
                str(fit / 'attempt.json'): dict(arm=arm, plan_sha256=collector.PLAN_SHA, init_adapter=None, pid=process['pid']),
                str(fit / 'receipt.json'): receipt, str(stage / 'supervision.json'): worker, str(stage / 'process.json'): process,
                str(collector.ROOT / 'run' / (arm + '.launch.json')): launch})
        terminal = dict(status='PAIRED_ADAPTERS_SAVED_READOUT_PENDING', arms=completed,
            readout='PENDING_SEPARATE_OFF_P_ON_A_ON', controller_seconds=30.) if complete == 2 else dict(
            status='PARTIAL_FAILED' if complete else 'FAILED', completed=completed, readout='NOT_RUN',
            controller_seconds=30., retry=False, error='synthetic failure')
        values[str(collector.ROOT / 'run' / ('result.json' if complete == 2 else 'failure.json'))] = terminal
        bridge = SimpleNamespace(validate_fit=Mock(side_effect=lambda root, arm, plan, diagnostic, trainer: receipts[arm]))
        diagnostic = SimpleNamespace(tree_hashes=lambda fit, excluded=(): {'weight': fit.name})
        return values, plan, bridge, diagnostic

    def audit(self, values, plan, bridge, diagnostic, partial_weights=False):
        with patch.object(collector, 'read', side_effect=lambda path: values[str(path)]), \
             patch.object(Path, 'is_file', autospec=True, side_effect=lambda path: str(path) in values), \
             patch.object(Path, 'is_dir', return_value=partial_weights), \
             patch.object(Path, 'glob', side_effect=lambda pattern: [Path(path) for path in values if path.endswith('/supervision.json')]), \
             patch.object(collector, 'digest', side_effect=lambda path: 'fit-hash' if path.name == 'manifest.json' else 'worker-hash'):
            return collector.audit(bridge, plan, diagnostic, None)

    def test_complete_both_validated_no_readout_claim(self):
        fixture = self.fixture()
        report = self.audit(*fixture)
        self.assertTrue(report['write_success'])
        self.assertIsNone(report['readout_success'])
        self.assertEqual(report['observed_worker_seconds'], 20.)
        self.assertEqual(fixture[2].validate_fit.call_count, 2)
        self.assertTrue(all(row['verified_saved_adapter'] for row in report['arms'].values()))

    def test_partial_retains_saved_P_missing_A(self):
        report = self.audit(*self.fixture(1))
        self.assertFalse(report['write_success'])
        self.assertTrue(report['arms']['P']['verified_saved_adapter'])
        self.assertIsNone(report['arms']['A']['fit'])
        self.assertFalse(report['worker_cost_complete'])

    def test_failed_no_zero_cost(self):
        report = self.audit(*self.fixture(0))
        self.assertIsNone(report['observed_worker_seconds'])
        self.assertEqual(report['status'], 'FAILED')

    def test_partial_weight_inventory_preserved(self):
        report = self.audit(*self.fixture(1), partial_weights=True)
        self.assertEqual(report['arms']['A']['partial_adapter_files'], {'weight': 'adapter'})
        self.assertFalse(report['arms']['A']['verified_saved_adapter'])

    def test_success_weight_hash_mismatch(self):
        values, plan, bridge, diagnostic = self.fixture()
        receipt = copy.deepcopy(values[str(collector.ROOT / 'fits/P/receipt.json')])
        receipt['files']['adapter_model.safetensors'] = 'changed'
        bridge.validate_fit.side_effect = lambda root, arm, *args: receipt
        with self.assertRaisesRegex(ValueError, 'receipt changed'):
            self.audit(values, plan, bridge, diagnostic)

    def test_partial_corrupt_fit_preserved(self):
        values, plan, bridge, diagnostic = self.fixture(1)
        bridge.validate_fit.side_effect = ValueError('bad tensor')
        report = self.audit(values, plan, bridge, diagnostic)
        self.assertFalse(report['arms']['P']['verified_saved_adapter'])
        self.assertIn('bad tensor', report['arms']['P']['error'])

    def test_changed_fit_manifest_refused(self):
        values, plan, bridge, diagnostic = self.fixture()
        values[str(collector.ROOT / 'fits/P/manifest.json')]['files'] = {}
        with self.assertRaisesRegex(ValueError, 'manifest changed'):
            self.audit(values, plan, bridge, diagnostic)

    def test_worker_wrong_token_refused(self):
        values, plan, bridge, diagnostic = self.fixture()
        values[str(collector.ROOT / 'run/P.launch.json')]['token'] = 'wrong'
        with self.assertRaisesRegex(ValueError, 'ownership'):
            self.audit(values, plan, bridge, diagnostic)

    def test_fit_wrong_worker_refused(self):
        values, plan, bridge, diagnostic = self.fixture()
        values[str(collector.ROOT / 'fits/P/attempt.json')]['pid'] = 999
        with self.assertRaisesRegex(ValueError, 'attempt/worker'):
            self.audit(values, plan, bridge, diagnostic)

    def test_success_cleanup_failure_refused(self):
        values, plan, bridge, diagnostic = self.fixture()
        values[str(collector.ROOT / 'run/P/supervision.json')]['owned_group_empty'] = False
        with self.assertRaisesRegex(ValueError, 'cleanup'):
            self.audit(values, plan, bridge, diagnostic)

    def test_success_controller_overrun_refused(self):
        values, plan, bridge, diagnostic = self.fixture()
        values[str(collector.ROOT / 'run/result.json')]['controller_seconds'] = 1201
        with self.assertRaisesRegex(ValueError, 'inclusive bound'):
            self.audit(values, plan, bridge, diagnostic)

    def test_partial_overrun_recorded_not_hidden(self):
        values, plan, bridge, diagnostic = self.fixture(1)
        values[str(collector.ROOT / 'run/failure.json')]['controller_seconds'] = 1201
        self.assertFalse(self.audit(values, plan, bridge, diagnostic)['controller_within_bound'])

    def test_status_markers_only(self):
        with patch.object(collector, 'read', side_effect=AssertionError('read')), patch.object(Path, 'is_file', return_value=False), \
             patch.object(collector, 'controller_present', return_value=True), patch.object(collector, 'bind', side_effect=AssertionError('native')):
            self.assertEqual(collector.status()['scoring'], 'NONE')

    def test_live_refusal(self):
        with patch.object(collector, 'status', return_value=dict(controller_present=True, markers={})), \
             patch.object(collector, 'bind', side_effect=AssertionError('native')):
            with self.assertRaisesRegex(ValueError, 'wait'):
                collector.finish()

    def test_no_terminal_refusal(self):
        with patch.object(collector, 'status', return_value=dict(controller_present=False, markers={'result.json': False, 'failure.json': False})):
            with self.assertRaisesRegex(ValueError, 'wait'):
                collector.finish()

    def test_timeout_finally(self):
        with patch.object(collector, 'collect', side_effect=ValueError('fail')), patch.object(collector.signal, 'signal'), \
             patch.object(collector.signal, 'setitimer') as timer:
            self.assertRaises(ValueError, collector.finish)
            self.assertEqual(timer.call_args_list[0].args[1], 300)
            self.assertEqual(timer.call_args_list[-1].args[1], 0)
        self.assertFalse(issubclass(collector.CollectionExpired, Exception))

    def test_gpu_empty_and_wrong_uuid(self):
        xml = f'<root><gpu><uuid>{collector.UUID}</uuid><processes/></gpu></root>'
        collector.check_uuid({'gpu_uuid': collector.UUID}, xml)
        self.assertRaises(ValueError, collector.check_uuid, {'gpu_uuid': 'wrong'}, xml)

    def test_gpu_occupied(self):
        xml = f'<root><gpu><uuid>{collector.UUID}</uuid><processes><process/></processes></gpu></root>'
        self.assertRaises(ValueError, collector.check_uuid, {'gpu_uuid': collector.UUID}, xml)

    def test_fullcheck_failure_no_evidence_write(self):
        with patch.object(collector, 'status', return_value=dict(controller_present=False, markers={'result.json': True})), \
             patch.object(Path, 'exists', return_value=False), patch.object(collector, 'metadata', return_value={}), \
             patch.object(collector, 'bind', return_value=(None, None, None, None)), patch.object(collector, 'audit', return_value={}), \
             patch.dict(collector.os.environ, {}, clear=True), \
             patch.object(collector, 'load', return_value=SimpleNamespace(check_free=Mock(side_effect=ValueError('occupied')))), \
             patch.object(collector.common, 'write_new', side_effect=AssertionError('write')):
            self.assertRaisesRegex(ValueError, 'occupied', collector.finish)

    def test_orphan_capsule_no_retry(self):
        with patch.object(collector, 'status', return_value=dict(controller_present=False, markers={'result.json': True})), \
             patch.object(Path, 'exists', return_value=True), patch.object(Path, 'is_file', return_value=False):
            self.assertRaisesRegex(ValueError, 'partial capsule', collector.finish)

    def test_orphan_release_no_retry(self):
        with patch.object(collector, 'status', return_value=dict(controller_present=False, markers={'result.json': True})), \
             patch.object(Path, 'exists', autospec=True, side_effect=lambda path: path.name == 'main_release.json'):
            self.assertRaisesRegex(ValueError, 'partial release', collector.finish)

    def test_repeat_no_native_or_writes(self):
        validation = dict(plan_sha256=collector.PLAN_SHA, collector_sha256='collector', sha256='archive', files={'a': 'sha'})
        with patch.object(collector, 'status', return_value=dict(controller_present=False, markers={'result.json': True})), \
             patch.object(collector, 'controller_present', return_value=False), patch.object(Path, 'exists', return_value=True), \
             patch.object(Path, 'is_file', return_value=True), patch.object(collector, 'read', return_value=validation), \
             patch.object(collector, 'digest', side_effect=lambda path: 'archive' if path == collector.ARCHIVE else 'collector'), \
             patch.object(collector, 'metadata', return_value=validation['files']), patch.object(Path, 'open', return_value=io.BytesIO()), \
             patch.object(collector.common, 'validate_archive'), patch.object(collector, 'bind', side_effect=AssertionError('native')), \
             patch.object(collector.common, 'write_json', side_effect=AssertionError('write')):
            self.assertEqual(collector.finish()['status'], 'ALREADY_COLLECTED_VERIFIED_NO_WRITES')

    def test_safe_archive_and_traversal_link_duplicate_hash(self):
        name = 'astra_diagnostics/root/file.json'
        expected = {name: hashlib.sha256(b'x').hexdigest()}
        for names, link, valid in (([name], False, True), ([name, name], False, False),
                                   (['../escape'], False, False), ([name], True, False)):
            stream = io.BytesIO()
            with tarfile.open(fileobj=stream, mode='w:gz', format=tarfile.USTAR_FORMAT) as archive:
                for member_name in names:
                    member = tarfile.TarInfo(member_name)
                    member.size = 0 if link else 1
                    if link:
                        member.type, member.linkname = tarfile.SYMTYPE, 'target'
                    archive.addfile(member, None if link else io.BytesIO(b'x'))
            stream.seek(0)
            if valid:
                self.assertEqual(collector.common.validate_archive(stream, expected, 'astra_diagnostics/'), 1)
                stream.seek(0)
                self.assertRaises(ValueError, collector.common.validate_archive, stream, {name: 'bad'}, 'astra_diagnostics/')
            else:
                self.assertRaises(ValueError, collector.common.validate_archive, stream, expected, 'astra_diagnostics/')

    def test_no_training_or_readout_calls(self):
        calls = {node.func.attr for node in ast.walk(ast.parse(PATH.read_text())) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)}
        self.assertFalse(calls & {'write_pair', 'worker', 'run_training', 'load_native', 'native_tokenizer', 'formation', 'evaluate', 'Popen'})


class NativeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge = collector.load(collector.DRIVER, collector.DRIVER_SHA, 'record_write_contract_tested')

    def fixture(self):
        root, model = Path('/fixture'), Path('/model')
        adapter, fit = root / 'fits/P/adapter', root / 'fits/P'
        trainer = SimpleNamespace(RECIPE='synthetic', ALL_PROJ=['q_proj'])
        tokens = {'total': 10, 'target': 4, 'context': 6}
        plan = dict(config={'test': 'recipe'}, model=str(model), tokens={'P': dict(tokens=tokens, train_tokens_seen=120, max_segment_tokens=5)},
            material_files={'corpora/P.json': 'corpus', 'provenance/P.tokens.json': 'token-hash'})
        manifest = dict(recipe='synthetic', config=plan['config'], base_model=str(model), empty=False,
            steps=12, micro_batches=12, epochs_run=12, nonfinite_batches=0, final_loss=.1, mean_loss_per_epoch=[.1] * 12,
            corpus=dict(file='P.json', sha256='corpus', n_items=2, n_encoded=2, n_skipped_no_target=0), tokens=tokens, train_tokens_seen=120,
            truncation=dict(overflow='split', items_truncated=0, context_tokens_dropped=0, target_tokens_dropped=0, items_split=0, segments_from_splits=0, max_segment_tokens=5),
            packing=dict(mode='one_item_per_sequence', n_sequences=2, n_groups=2, isolation_check={'ran': False}),
            lora=dict(rank=8, alpha=16, dropout=.05, scaling=2., target_modules=['q_proj'], layers='all', n_layers=1, freeze_a=False, trainable_params=32))
        trainability = dict(base_frozen=True, init_adapter=None, adapter_count=1, trainable_params=32, adapters={})
        values = {str(adapter / 'train_manifest.json'): manifest,
            str(adapter / 'train_meta.json'): dict(recipe='synthetic', n_texts=2, steps=12, tokens=120, rank=8, epochs=12, lr=1e-4, seed=2, final_loss=.1),
            str(fit / 'pre_update_trainability.json'): trainability, str(fit / 'post_update_trainability.json'): copy.deepcopy(trainability),
            str(model / 'config.json'): {'num_hidden_layers': 1}, str(fit / 'full_tokens.json'): {'tokens': tokens},
            str(adapter / 'adapter_config.json'): dict(r=8, lora_alpha=16, lora_dropout=.05, bias='none', peft_type='LORA', target_modules=['q_proj'], base_model_name_or_path=str(model))}
        return root, plan, trainer, values

    def validate(self, fixture):
        root, plan, trainer, values = fixture
        diagnostic = SimpleNamespace(read=lambda path: values[str(path)], tree_hashes=Mock(return_value={
            'train_manifest.json': 'manifest-hash', 'adapter_model.safetensors': 'weight-hash'}))
        with patch.object(Path, 'is_file', return_value=True), patch.object(Path, 'exists', return_value=False), \
             patch.object(self.bridge, 'local_path', side_effect=Path), patch.object(self.bridge, 'saved_weights', return_value={'tensor': 'checked'}), \
             patch.object(self.bridge, 'digest', return_value='token-hash'):
            return self.bridge.validate_fit(root, 'P', plan, diagnostic, trainer)

    def test_real_validator_twelve_steps_hashes(self):
        receipt = self.validate(self.fixture())
        self.assertEqual(receipt['steps'], 12)
        self.assertEqual(receipt['files']['adapter_model.safetensors'], 'weight-hash')

    def test_real_validator_steps_drops_warm_nonfinite(self):
        for kind in ('steps', 'drops', 'warm', 'nonfinite', 'tokens', 'trainability'):
            with self.subTest(kind=kind):
                fixture = self.fixture()
                values = fixture[3]
                manifest = values['/fixture/fits/P/adapter/train_manifest.json']
                if kind == 'steps':
                    manifest['steps'] = 11
                elif kind == 'drops':
                    manifest['truncation']['target_tokens_dropped'] = 1
                elif kind == 'warm':
                    manifest['warm_start'] = '/parent'
                elif kind == 'nonfinite':
                    manifest['final_loss'] = float('nan')
                elif kind == 'tokens':
                    manifest['train_tokens_seen'] = 119
                else:
                    values['/fixture/fits/P/post_update_trainability.json']['base_frozen'] = False
                self.assertRaises(ValueError, self.validate, fixture)

    def test_real_safetensors_header_and_size(self):
        key = 'layers.0.self_attn.q_proj.lora_A.weight'
        expected = {key: {'shape': [8, 2]}}
        header = json.dumps({'base_model.model.' + key: dict(dtype='F32', shape=[8, 2], data_offsets=[0, 64])}).encode()
        payload = struct.pack('<Q', len(header)) + header + bytes(64)
        with patch.object(Path, 'open', side_effect=lambda *args: io.BytesIO(payload)), \
             patch.object(Path, 'stat', return_value=SimpleNamespace(st_size=len(payload))):
            self.assertEqual(set(self.bridge.saved_weights(Path('/weight'), expected)), {key})
        with patch.object(Path, 'open', side_effect=lambda *args: io.BytesIO(payload)), \
             patch.object(Path, 'stat', return_value=SimpleNamespace(st_size=len(payload) - 1)):
            self.assertRaises(ValueError, self.bridge.saved_weights, Path('/weight'), expected)


if __name__ == '__main__':
    unittest.main()
