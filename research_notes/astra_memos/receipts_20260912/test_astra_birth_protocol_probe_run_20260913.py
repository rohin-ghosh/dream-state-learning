"""CPU fixtures only; failing safety assertions report gaps, never authorize launch."""
from contextlib import ExitStack, nullcontext, redirect_stdout
from copy import deepcopy
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tarfile
import tempfile
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch

sys.dont_write_bytecode = True
sys.path[:0] = [str(Path.cwd()), '/tmp']
import astra_birth_protocol_probe_material_20260913 as material
from organism_v6 import fundamental_teaching_readout as capture

RUNTIME_PATH = Path('/tmp/astra_birth_protocol_probe_run_20260913.py')
specification = importlib.util.spec_from_file_location('protocol_runtime_under_test', RUNTIME_PATH)
runner = importlib.util.module_from_spec(specification)
specification.loader.exec_module(runner)
LOADED_SHA = runner.digest(RUNTIME_PATH)


def save(filename, value):
    filename = Path(filename)
    filename.parent.mkdir(parents=True, exist_ok=True)
    filename.write_text(json.dumps(value, sort_keys=True, allow_nan=False))


class Tokenizer:
    eos_token_id = 0

    def apply_chat_template(self, messages, **kwargs):
        return '<user>' + messages[0]['content'] + '</user><assistant>'

    def encode(self, text):
        return list(map(ord, text))

    def decode(self, tokens, **kwargs):
        return ''.join(map(chr, tokens))


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.temporary = self.stack.enter_context(tempfile.TemporaryDirectory(prefix='probe_runtime_cpu_'))
        self.root = Path(self.temporary)/'probe'
        self.root.mkdir()
        self.tokenizer = Tokenizer()
        self.popen = self.stack.enter_context(patch.object(runner.subprocess, 'Popen', side_effect=AssertionError('real process forbidden')))
        self.stack.enter_context(patch.object(capture.base, 'NativeBackend', side_effect=AssertionError('native backend forbidden')))
        self.stack.enter_context(patch.object(capture.base, 'native_tokenizer', return_value=self.tokenizer))
        self.clock = 1000.0
        self.stack.enter_context(patch.object(runner.time, 'time', side_effect=lambda: self.clock))
        self.candidate = material.build_candidate()
        self.requests = material.call_map(self.candidate)
        self.targets = {row['id']: row['auth_example_target'] for row in self.candidate['cases']}
        self.cells = {}
        self.closers = []
        for state in runner.STATES:
            adapter = '/fixture/AUTH' if state == 'AUTH' else None
            cell = dict(model='/fixture/base', adapter=adapter,
                        identity=dict(model='/fixture/base', adapter=adapter),
                        model_files={'config.json': 'fixture-base-hash'},
                        adapter_files={'adapter.safetensors': 'fixture-auth-hash'} if adapter else {},
                        requests=self.requests[state], native_inputs=capture.native_inputs(self.tokenizer, self.requests[state]))
            self.cells[state] = cell
            data = self.root/'run'/state/'data'
            data.mkdir(parents=True)
            backend = Mock()
            backend.identity.return_value = cell['identity']
            def generate(request, cell=cell):
                native = cell['native_inputs'][int(request['call_id'])]
                text = self.targets[request['case_id']]
                return dict(text=text, rendered_prompt=native['rendered_prompt'],
                            prompt_token_ids=native['prompt_token_ids'], output_token_ids=self.tokenizer.encode(text))
            backend.generate.side_effect = generate
            closer = Mock(return_value=True)
            capture.capture(cell, data, factory=Mock(return_value=backend), closer=closer)
            self.closers.append(closer)
            save(data.parent/'worker/supervision.json', dict(ok=True, returncode=0, reservation_release_verified=True,
                 owned_group_empty=True, gpu_processes_absent=True, device='0', reserved_seconds=1))
            save(data.parent/'worker/process.json', dict(pid=300 + len(self.cells), pgid=300 + len(self.cells),
                 start_ticks=30, device='0', argv=['fixture-worker', state]))
        save(self.root/'run/capture_barrier.json', dict(states=list(runner.STATES), calls=32, scores_computed=False))
        self.plan = dict(root=str(self.root), driver_sha256=LOADED_SHA, source_hashes={str(RUNTIME_PATH): LOADED_SHA},
            python=os.path.abspath(sys.executable), states=list(runner.STATES), claims=runner.CLAIMS,
            controller_seconds=runner.CONTROLLER, collection_seconds=runner.COLLECTION,
            source_root=str(Path.cwd()), model='/fixture/base', device='0', deadline=6000, real_lease_end=40000,
            candidate=self.candidate, cells=self.cells, normalized={'fixture': 'released-birth'},
            metric_caveat='formatting-sensitive; not semantic truth')
        save(self.root/'plan.json', self.plan)
        self.pin = runner.digest(self.root/'plan.json')
        self.process = dict(pid=101, start_ticks=10, launcher=dict(pid=102, start_ticks=11),
                            gpu_uuid='fixture-gpu', plan_sha256=self.pin)
        save(self.root/'launch/process.json', self.process)
        save(self.root/'launch/exit.json', dict(returncode=0))
        self.birth = SimpleNamespace(process_identity=Mock(side_effect=FileNotFoundError),
            work_window=Mock(side_effect=lambda *args: nullcontext()),
            supervisor_window=Mock(side_effect=lambda *args: nullcontext()),
            owned_worker=Mock(side_effect=lambda *args: nullcontext()), COMMON=RUNTIME_PATH)
        self.formation = SimpleNamespace(birth=self.birth, BIRTH=RUNTIME_PATH, verify_custody=Mock(),
                                         common=SimpleNamespace(scan_text=Mock()))
        self.stack.enter_context(patch.object(runner, 'api', return_value=(capture, material, self.formation)))
        self.gpu_module = ModuleType('gpu.astra_mini_sudoku_diagnostic')
        self.gpu_module.check_free = Mock(return_value=({'gpu_uuid': 'fixture-gpu'}, '<fixture-gpu/>'))
        self.stack.enter_context(patch.dict(sys.modules, {'gpu.astra_mini_sudoku_diagnostic': self.gpu_module}))
        self.archive = Path(self.temporary)/'capture.tgz'
        self.args = SimpleNamespace(root=str(self.root), plan_sha256=self.pin, archive=str(self.archive),
            allow_gpu=True, state='OFF', hard_end=5000, native_cpu_log=str(Path(self.temporary)/'cpu.log'), native_test_count=21)
        Path(self.args.native_cpu_log).write_text('Ran 21 tests in 0.044s\n\nOK\n')

    def data(self, state='AUTH'):
        return self.root/'run'/state/'data'

    def change(self, relative, mutate, state='AUTH', repin=True):
        filename = self.data(state)/relative
        value = runner.read(filename)
        mutate(value)
        save(filename, value)
        if repin:
            self.remanifest(state)

    def remanifest(self, state='AUTH'):
        data = self.data(state)
        save(data/'manifest.json', {'files': capture.base.tree_hashes(data, ('manifest.json',))})

    def reduce(self):
        return runner.reduce_captures(self.root, self.plan, capture, material)

    def assert_rejected_before_scoring(self):
        with patch.object(material, 'check_outputs', wraps=material.check_outputs) as score:
            with self.assertRaises((ValueError, FileNotFoundError, KeyError)):
                self.reduce()
            score.assert_not_called()

    def test_complete_32_raw_targets_and_close_once(self):
        result = self.reduce()
        self.assertEqual(sum(len(rows) for rows in result['raw_outputs'].values()), 32)
        self.assertTrue(all(row['public_contract_correct'] for rows in result['scores'].values() for row in rows.values()))
        for closer in self.closers:
            closer.assert_called_once()
        self.assertNotEqual(self.cells['OFF']['identity'], self.cells['AUTH']['identity'])
        self.assertEqual(self.cells['OFF']['requests'], self.cells['AUTH']['requests'])
        self.popen.assert_not_called()

    def test_missing_auth_response_blocks_all_scores(self):
        (self.data()/'calls/0015.response.json').unlink()
        self.assert_rejected_before_scoring()

    def test_extra_raw_json_rejected(self):
        save(self.data()/'calls/extra.json', {})
        self.remanifest()
        self.assert_rejected_before_scoring()

    def test_manifest_byte_mismatch_rejected(self):
        self.change('calls/0000.response.json', lambda row: row['response'].update(text='changed'), repin=False)
        self.assert_rejected_before_scoring()

    def test_native_prompt_mismatch_rejected(self):
        self.change('calls/0000.response.json', lambda row: row['response'].update(rendered_prompt='wrong prompt'))
        self.assert_rejected_before_scoring()

    def test_actual_prompt_tokens_mismatch_rejected(self):
        self.change('calls/0000.response.json', lambda row: row['response'].update(prompt_token_ids=[1]))
        self.assert_rejected_before_scoring()

    def test_output_token_budget_rejected(self):
        self.change('calls/0000.response.json', lambda row: row['response'].update(output_token_ids=[1]*401))
        self.assert_rejected_before_scoring()

    def test_wrong_request_identity_rejected(self):
        self.change('calls/0000.request.json', lambda row: row.update(identity=self.cells['OFF']['identity']))
        self.assert_rejected_before_scoring()

    def test_request_sampling_change_rejected(self):
        self.change('calls/0000.request.json', lambda row: row['request'].update(stop=[]))
        self.assert_rejected_before_scoring()

    def test_cleanup_failure_rejected(self):
        self.change('backend.cleanup.json', lambda row: row.update(closed=False))
        self.assert_rejected_before_scoring()

    def test_worker_not_released_rejected(self):
        filename = self.data().parent/'worker/supervision.json'
        receipt = runner.read(filename)
        receipt['reservation_release_verified'] = False
        save(filename, receipt)
        self.assert_rejected_before_scoring()

    def test_missing_barrier_rejected(self):
        (self.root/'run/capture_barrier.json').unlink()
        self.assert_rejected_before_scoring()

    def test_barrier_counts_and_states_must_bind_inventory(self):
        save(self.root/'run/capture_barrier.json', dict(states=['OFF'], calls=16, scores_computed=False))
        self.assert_rejected_before_scoring()

    def test_manifest_must_cover_every_capture_file(self):
        save(self.data()/'manifest.json', {'files': {}})
        self.assert_rejected_before_scoring()

    def test_failure_artifact_must_prevent_reduction(self):
        save(self.data()/'failure.json', {'error': 'fixture incomplete worker'})
        self.remanifest()
        self.assert_rejected_before_scoring()

    def test_full_identity_file_manifest_must_match_plan(self):
        self.change('identity.json', lambda row: row.update(adapter_files={}))
        self.assert_rejected_before_scoring()

    def test_request_hash_receipt_must_match(self):
        self.change('calls/0000.request.json', lambda row: row.update(prompt_sha256='0'*64))
        self.assert_rejected_before_scoring()

    def test_response_hash_receipt_must_match(self):
        self.change('calls/0000.response.json', lambda row: row.update(response_sha256='0'*64))
        self.assert_rejected_before_scoring()

    def test_usage_receipt_must_match_actual_raw_calls(self):
        self.change('usage.json', lambda row: row.clear())
        self.assert_rejected_before_scoring()

    def test_call_end_must_not_precede_start(self):
        self.change('calls/0000.response.json', lambda row: row.update(ended=-1))
        self.assert_rejected_before_scoring()

    def test_output_text_must_match_actual_token_ids(self):
        def change(row):
            row['response']['text'] = 'not the emitted tokens'
            row['response_sha256'] = capture.base.value_hash(row['response'])
        self.change('calls/0000.response.json', change)
        self.assert_rejected_before_scoring()

    def test_collect_archive_metadata_and_all_member_hashes(self):
        result = runner.collect(self.args)
        self.assertEqual(result['status'], 'COLLECTED_RELEASED')
        validation = runner.read(str(self.archive)+'.validation.json')
        self.assertEqual(validation['archive_sha256'], runner.digest(self.archive))
        with tarfile.open(self.archive) as archive:
            self.assertEqual(set(archive.getnames()), set(validation['files']))
            for filename, expected in validation['files'].items():
                self.assertEqual(runner.hashlib.sha256(archive.extractfile(filename).read()).hexdigest(), expected)
        self.assertIn('audit.json', validation['files'])
        self.assertIn('release.json', validation['files'])
        self.formation.verify_custody.assert_called_once()
        self.assertEqual(self.formation.common.scan_text.call_count, len(validation['files']))

    def test_collect_metadata_symlink_rejected(self):
        (self.root/'linked.json').symlink_to(self.root/'plan.json')
        with self.assertRaisesRegex(ValueError, 'symlink'):
            runner.collect(self.args)
        self.assertFalse(self.archive.exists())

    def test_collect_scanner_failure_prevents_archive(self):
        self.formation.common.scan_text.side_effect = ValueError('fixture sensitive metadata')
        with self.assertRaisesRegex(ValueError, 'sensitive metadata'):
            runner.collect(self.args)
        self.assertFalse(self.archive.exists())

    def test_collect_live_controller_rejected_before_release(self):
        self.birth.process_identity.side_effect = lambda pid: self.process if pid == 101 else self.process['launcher']
        with self.assertRaisesRegex(ValueError, 'still live'):
            runner.collect(self.args)
        self.assertFalse((self.root/'release.json').exists())

    def test_collect_wrong_gpu_rejected(self):
        self.gpu_module.check_free.return_value = ({'gpu_uuid': 'other'}, '')
        with self.assertRaisesRegex(ValueError, 'GPU identity changed'):
            runner.collect(self.args)

    def test_collect_failed_controller_rejected(self):
        save(self.root/'launch/exit.json', dict(returncode=1))
        with self.assertRaisesRegex(ValueError, 'failed/unfinished'):
            runner.collect(self.args)

    def test_collect_live_worker_must_be_rejected(self):
        worker = runner.read(self.data().parent/'worker/process.json')
        def identity(pid):
            if pid == worker['pid']:
                return worker
            raise FileNotFoundError
        self.birth.process_identity.side_effect = identity
        with self.assertRaises(ValueError):
            runner.collect(self.args)

    def test_collect_launcher_receipt_must_bind_plan(self):
        save(self.root/'launch/process.json', dict(self.process, plan_sha256='0'*64))
        with self.assertRaises(ValueError):
            runner.collect(self.args)

    def test_collect_must_not_succeed_after_collection_budget(self):
        original = runner.reduce_captures
        def delayed(*args):
            self.clock += runner.COLLECTION+1
            return original(*args)
        with patch.object(runner, 'reduce_captures', side_effect=delayed):
            with self.assertRaises((ValueError, TimeoutError)):
                runner.collect(self.args)

    def test_command_and_gpu_opt_in(self):
        command = runner.command('_worker', self.root, self.pin, '--state', 'AUTH', '--allow-gpu')
        self.assertEqual(command[:4], [os.path.abspath(sys.executable), '-B', str(RUNTIME_PATH), '_worker'])
        self.assertIn(self.pin, command)
        self.args.allow_gpu = False
        for function in (runner.worker, runner.controller, runner.launch):
            with self.assertRaisesRegex(ValueError, 'opt-in'):
                function(self.args)
        self.popen.assert_not_called()

    def test_start_without_opt_in_never_spawns(self):
        with patch.object(sys, 'argv', [str(RUNTIME_PATH), 'start', '--root', str(self.root), '--plan-sha256', self.pin]):
            with self.assertRaisesRegex(ValueError, 'opt-in'):
                runner.main()
        self.popen.assert_not_called()

    def test_worker_device_mismatch_prevents_capture(self):
        with patch.dict(os.environ, {'CUDA_VISIBLE_DEVICES': 'wrong'}):
            with self.assertRaisesRegex(ValueError, 'state/device'):
                runner.worker(self.args)
        self.birth.owned_worker.assert_not_called()

    def test_read_plan_rejects_bad_pin_and_driver(self):
        with self.assertRaisesRegex(ValueError, 'plan hash'):
            runner.read_plan(self.root, '0'*64)
        changed = dict(self.plan, driver_sha256='0'*64)
        save(self.root/'plan.json', changed)
        with self.assertRaisesRegex(ValueError, 'root/driver'):
            runner.read_plan(self.root, runner.digest(self.root/'plan.json'))

    def test_launch_rejects_insufficient_window(self):
        self.clock = self.plan['deadline']-runner.CONTROLLER-runner.COLLECTION
        with self.assertRaisesRegex(ValueError, 'window unavailable'):
            runner.launch(self.args)
        self.popen.assert_not_called()

    def test_launch_rejects_failed_cpu_log(self):
        Path(self.args.native_cpu_log).write_text('Ran 21 tests\nFAILED\n')
        with self.assertRaisesRegex(ValueError, 'CPU acceptance'):
            runner.launch(self.args)
        self.popen.assert_not_called()

    def test_launch_rechecks_birth_custody(self):
        self.formation.verify_custody.side_effect = ValueError('fixture custody failure')
        with self.assertRaisesRegex(ValueError, 'custody failure'):
            runner.launch(self.args)
        self.popen.assert_not_called()

    def test_launch_command_uses_offline_fresh_session(self):
        for filename in (self.root/'launch').iterdir():
            filename.unlink()
        (self.root/'launch').rmdir()
        self.popen.side_effect = None
        self.popen.return_value = Mock(pid=101, wait=Mock(return_value=0))
        self.birth.process_identity.side_effect = lambda pid: dict(pid=pid, start_ticks=1)
        with redirect_stdout(io.StringIO()):
            result = runner.launch(self.args)
        self.assertEqual(result['status'], 'EXITED_REQUIRES_COLLECTION')
        args, kwargs = self.popen.call_args
        self.assertEqual(args[0][3], '_controller')
        self.assertTrue(kwargs['start_new_session'])
        for field in ('HF_HUB_OFFLINE', 'TRANSFORMERS_OFFLINE', 'PYTHONNOUSERSITE'):
            self.assertEqual(kwargs['env'][field], '1')
        self.assertEqual(kwargs['env']['CUDA_VISIBLE_DEVICES'], '0')
        self.assertFalse((self.root/'audit.json').exists())

    def prepare_args(self):
        upstream = Path(self.temporary)/'upstream'
        normalized = dict(pin=dict(child_identity={'model_input': '/fixture/base', 'adapter_input': '/fixture/AUTH'},
                                  model_files={'config.json': 'fixture-base-hash'}),
                          adapter_all_files={'adapter.safetensors': 'fixture-auth-hash'})
        save(upstream/'normalized_birth.json', normalized)
        inherited = dict(model='/fixture/base', source_root=str(Path.cwd()), real_lease_end=40000,
                         source_hashes={}, normalized_file_sha256=runner.digest(upstream/'normalized_birth.json'))
        save(upstream/'plan.json', inherited)
        return SimpleNamespace(root=str(Path(self.temporary)/'prepared'), formation_root=str(upstream),
            formation_plan_sha256=runner.digest(upstream/'plan.json'), deadline=6000, device='0')

    def test_prepare_binds_native_prompts_and_auth_only_adapter(self):
        args = self.prepare_args()
        with patch.object(capture.base, 'expected_identity', side_effect=lambda plan, adapter: dict(model_input=plan['model'], adapter_input=adapter)), \
             patch.dict(os.environ):
            result = runner.prepare(args)
        plan = runner.read(Path(args.root)/'plan.json')
        self.assertEqual(result['status'], 'PREPARED_NOT_LAUNCHED')
        self.assertEqual(plan['cells']['OFF']['adapter_files'], {})
        self.assertIsNone(plan['cells']['OFF']['adapter'])
        self.assertEqual(plan['cells']['AUTH']['adapter'], '/fixture/AUTH')
        for state in runner.STATES:
            for request, native in zip(plan['cells'][state]['requests'], plan['cells'][state]['native_inputs'], strict=True):
                self.assertEqual(native['rendered_prompt'], self.tokenizer.apply_chat_template([{'content': request['prompt']}]))
                self.assertEqual(native['prompt_token_ids'], self.tokenizer.encode(native['rendered_prompt']))
        self.formation.verify_custody.assert_called_once()
        self.popen.assert_not_called()

    def test_prepare_rejects_custody_and_lease_margin(self):
        args = self.prepare_args()
        self.formation.verify_custody.side_effect = ValueError('fixture custody failure')
        with patch.dict(os.environ):
            with self.assertRaisesRegex(ValueError, 'custody failure'):
                runner.prepare(args)
            self.formation.verify_custody.side_effect = None
            args.deadline = 40000-21600
            with self.assertRaisesRegex(ValueError, 'six-hour'):
                runner.prepare(args)
        self.assertFalse(Path(args.root).exists())

    def test_prepare_rejects_actual_context_over_budget(self):
        args = self.prepare_args()
        with patch.object(capture.base, 'MAX_MODEL_LEN', 1), patch.dict(os.environ):
            with self.assertRaises(ValueError):
                runner.prepare(args)
        self.assertFalse(Path(args.root).exists())

    def test_controller_barrier_only_after_both_supervised_cells(self):
        root = Path(self.temporary)/'controller'
        root.mkdir()
        with patch.object(runner, 'read_plan', return_value=(root, self.plan)), \
             patch.multiple(runner.os, getpid=Mock(return_value=100), getpgrp=Mock(return_value=100), getsid=Mock(return_value=100)), \
             patch.dict(os.environ, {'CUDA_VISIBLE_DEVICES': '0'}), \
             patch.object(capture.base, 'supervise', return_value={'ok': True}) as supervise, \
             patch.object(material, 'check_outputs', side_effect=AssertionError('controller must not score')):
            self.birth.process_identity.side_effect = lambda pid: dict(pid=pid, start_ticks=1)
            result = runner.controller(self.args)
        self.assertEqual(result['status'], 'CAPTURED_NOT_SCORED')
        self.assertEqual(supervise.call_count, 2)
        self.assertEqual(runner.read(root/'run/capture_barrier.json')['calls'], 32)
        self.assertEqual([call.args[2].parent.name for call in supervise.call_args_list], ['OFF', 'AUTH'])

    def test_controller_failed_second_worker_preserves_partial_no_barrier(self):
        root = Path(self.temporary)/'controller'
        root.mkdir()
        with patch.object(runner, 'read_plan', return_value=(root, self.plan)), \
             patch.multiple(runner.os, getpid=Mock(return_value=100), getpgrp=Mock(return_value=100), getsid=Mock(return_value=100)), \
             patch.dict(os.environ, {'CUDA_VISIBLE_DEVICES': '0'}), \
             patch.object(capture.base, 'supervise', side_effect=[{'ok': True}, ValueError('fixture second worker failed')]), \
             patch.object(material, 'check_outputs', side_effect=AssertionError('controller must not score')):
            self.birth.process_identity.side_effect = lambda pid: dict(pid=pid, start_ticks=1)
            with self.assertRaisesRegex(ValueError, 'second worker failed'):
                runner.controller(self.args)
        self.assertTrue((root/'run/failure.json').exists())
        self.assertFalse((root/'run/capture_barrier.json').exists())


if __name__ == '__main__':
    print('CPU-only runtime SHA256:', LOADED_SHA, flush=True)
    unittest.main()
