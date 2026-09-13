"""CPU fixtures only: no model, native tokenizer, GPU, queue, or network calls."""
from contextlib import ExitStack, contextmanager, redirect_stdout
from copy import deepcopy
import datetime as dt
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import signal
import struct
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
DRIVER = Path('/tmp/astra_birth_conditional_run_20260913.py')
SOURCE = Path('/data/home/rohing/dream-state')
spec = importlib.util.spec_from_file_location('birth_runner_tested', DRIVER)
run = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = run
spec.loader.exec_module(run)


class Tokenizer:
    eos_token_id = 900000
    pad_token_id = 900001

    def apply_chat_template(self, messages, *, tokenize, add_generation_prompt):
        assert tokenize is False and add_generation_prompt is True
        assert len(messages) == 1 and messages[0]['role'] == 'user'
        return 'USER:\n'+messages[0]['content']+'\nASSISTANT:\n'

    def encode(self, text, add_special_tokens=False):
        assert add_special_tokens is False
        return [ord(character)+100 for character in text]


def replace_json(path, value):
    path.write_bytes(run.encoded(value))


def iso(seconds):
    return dt.datetime.fromtimestamp(seconds, dt.timezone.utc).isoformat()


def weights(path, nonfinite=False):
    prefix = 'base_model.model.layers.0.self_attn.q_proj'
    header = {prefix+'.lora_A.weight': dict(dtype='F32', shape=[8, 2], data_offsets=[0, 64]),
        prefix+'.lora_B.weight': dict(dtype='F32', shape=[2, 8], data_offsets=[64, 128])}
    payload = json.dumps(header).encode()
    path.write_bytes(struct.pack('<Q', len(payload))+payload+struct.pack('<32f', *([float('nan') if nonfinite else .1]*32)))


@contextmanager
def no_window(*args, **kwargs):
    yield


class PipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module_pin = run.digest(SOURCE/'organism_v6/birth_conditional_corpus.py')
        cls.api = run.source_api(SOURCE, cls.module_pin)
        cls.corpus, cls.base, cls.trainer, cls.capture = cls.api
        cls.candidate = cls.corpus.build_candidate(root=0)
        cls.recipe = cls.corpus.training_recipe(learning_rate=1e-4, seed=0, epochs=4)
        cls.native = cls.corpus.audit_tokenizer(cls.candidate, Tokenizer(), recipe=cls.recipe)

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='birth_runner_cpu_')
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.model = self.directory/'mock_model'
        self.model.mkdir()
        for name in ('config.json', 'tokenizer.json', 'tokenizer_config.json'):
            run.write_json(self.model/name, dict(model_type='qwen2'))
        self.deadline = iso(time.time()+20000)
        self.lease = iso(time.time()+60000)
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.object(self.corpus, 'audit_native', side_effect=self.mock_native))
        self.stack.enter_context(patch.object(self.base, 'native_tokenizer', return_value=Tokenizer()))
        self.stack.enter_context(patch.dict(os.environ, {}, clear=True))
        self.stack.enter_context(patch.object(run.common, 'process_snapshot', return_value=[]))
        self.stack.enter_context(patch.object(run, 'vacancy', side_effect=self.mock_vacancy))
        self.launcher = self.directory/'reviewed_launcher.py'
        self.launcher.write_text('print("Main-owned launcher fixture")\n')
        self.counter = 0

    def mock_native(self, candidate, model, expected_file_hashes, *, recipe):
        self.assertEqual(candidate, self.candidate)
        self.assertEqual(recipe, self.recipe)
        result = deepcopy(self.native)
        result.update(status='NATIVE_TOKEN_MATCH_VERIFIED', tokenizer_path=str(model), tokenizer_file_hashes=expected_file_hashes)
        return result

    def mock_vacancy(self, plan, uuid):
        self.assertEqual(uuid, 'GPU-00000000-0000-0000-0000-000000000002')
        return dict(gpu_uuid=uuid, reconciled_system_services=[]), '<nvidia_smi_log><gpu><uuid>'+uuid+'</uuid><processes/></gpu></nvidia_smi_log>'

    def prepare(self):
        self.counter += 1
        root = self.directory/('fit'+str(self.counter))
        result = run.prepare_fit(SOURCE, self.module_pin, self.model, root, '2', self.deadline, self.lease)
        return root, result['plan_sha256'], run.read(root/'plan.json')

    def start(self, root, pin, plan):
        (root/'run').mkdir()
        now = time.time()
        identity = dict(pid=41001, ppid=41000, pgid=41001, session=41001, start_ticks=123,
            argv=run.controller_command(root, pin, plan['phase'], plan['python']), plan_sha256=pin,
            started_wall=now-20, started_monotonic=time.monotonic()-20,
            hard_end=min(now-20+plan['controller_seconds'], plan['deadline']), cleanup_reserve=140, continuous_reservation=True)
        run.write_json(root/'run/controller.json', identity)
        return identity

    def fit_files(self, root, plan, arm):
        adapter = root/'run'/arm/'adapter'
        adapter.mkdir()
        run.write_new(adapter/'DONE', b'ok\n')
        run.write_new(adapter/'README.md', b'CPU mock checkpoint only\n')
        weights(adapter/'adapter_model.safetensors')
        run.write_json(adapter/'adapter_config.json', dict(r=8, lora_alpha=16, lora_dropout=.05, bias='none',
            peft_type='LORA', target_modules=self.trainer.ALL_PROJ, base_model_name_or_path=str(self.model)))
        tokens = plan['expected_tokens'][arm]
        manifest = dict(config=plan['train_config'], recipe=self.trainer.RECIPE, base_model=str(self.model), empty=False,
            steps=128, micro_batches=128, epochs_run=4, nonfinite_batches=0, final_loss=.5, mean_loss_per_epoch=[2., 1., .7, .5],
            corpus=dict(file=arm+'.json', sha256=plan['material_files'][arm+'.json'], n_items=256, n_encoded=256, n_skipped_no_target=0),
            tokens=tokens, train_tokens_seen=tokens['total']*4,
            truncation=dict(items_truncated=0, context_tokens_dropped=0, target_tokens_dropped=0, items_split=0, segments_from_splits=0),
            packing=dict(mode='one_item_per_sequence', n_sequences=256))
        run.write_json(adapter/'train_manifest.json', manifest)
        run.write_json(adapter/'train_meta.json', dict(recipe=self.trainer.RECIPE, n_texts=256, steps=128,
            tokens=tokens['total']*4, rank=8, epochs=4, lr=1e-4, seed=0, final_loss=.5))

    def member(self, root, pin, plan, member, index):
        stage = root/'run'/member
        stage.mkdir()
        (stage/'worker').mkdir()
        controller = run.read(root/'run/controller.json')
        worker_spec = run.make_worker_spec(root, plan, member, controller['hard_end'])
        spec_path = root/'run'/(member+'.spec.json')
        run.write_json(spec_path, worker_spec)
        process = dict(pid=42001+index, pgid=42001+index, device='2', timeout=600,
            started=controller['started_monotonic']+1+index*5,
            argv=run.worker_command(plan['python'], spec_path, run.digest(spec_path)))
        run.write_json(stage/'worker/process.json', process)
        if plan['phase'] == 'fit':
            self.fit_files(root, plan, member)
        else:
            process['started'] = time.monotonic()-.01
            replace_json(stage/'worker/process.json', process)
            data = stage/'data'
            data.mkdir()
            run.write_json(data/'isolation.json', dict(pid=process['pid'], pgid=process['pid'], parent_pid=controller['pid'],
                spec_sha256=run.digest(spec_path), parent_calls=0, task_prefix='', online_updates=False))
            targets = {row['id']: self.corpus.response_text(row, 'DERANGED' if member == 'DERANGED' else 'AUTH')
                for row in self.candidate['dev']}
            inputs = {row['call_id']: row for row in plan['native_inputs']}
            identity = self.base.expected_identity(plan, worker_spec['adapter'])
            class Backend:
                backend = None
                def identity(inner):
                    return identity
                def generate(inner, request):
                    text = targets[request['case_id']]
                    return dict(text=text, prompt_token_ids=inputs[request['call_id']]['prompt_token_ids'],
                        output_token_ids=Tokenizer().encode(text)+[900000], rendered_prompt=inputs[request['call_id']]['rendered_prompt'],
                        finish_reason='stop', stop_reason=900000)
            capture_plan = dict(worker_spec, identity=identity)
            with patch.object(self.capture.os, 'getpid', return_value=process['pid']):
                self.capture.capture(capture_plan, data, factory=lambda *args: Backend(), closer=lambda backend: True)
        reserved = 2.0 if plan['phase'] == 'fit' else time.monotonic()-process['started']
        supervision = dict(ok=True, error=None, returncode=0, owned_group_empty=True, gpu_processes_absent=True,
            reservation_release_verified=True, reserved_seconds=reserved, device='2')
        run.write_json(stage/'worker/supervision.json', supervision)
        run.write_new(stage/'worker/stdout.log', b'CPU simulation\n')
        run.write_json(stage/'receipt.json', run.verify_member(root, plan, self.api, member))
        return dict(receipt_sha256=run.digest(stage/'receipt.json'), spec_sha256=run.digest(spec_path),
            supervision_sha256=run.digest(stage/'worker/supervision.json'))

    def complete(self, root, pin, plan):
        controller = self.start(root, pin, plan)
        members = {member: self.member(root, pin, plan, member, index) for index, member in enumerate(plan['members'])}
        aggregate = run.reduce_completed(root, plan, self.api)
        terminal = dict(status='COMPLETE', phase=plan['phase'], members=members, aggregate=aggregate,
            controller_seconds=time.monotonic()-controller['started_monotonic'], ended_wall=time.time(),
            plan_sha256=pin, automatic_pass=False, origin=run.ORIGIN, claims=run.CLAIMS)
        run.write_json(root/'run/result.json', terminal)
        return terminal

    def launch(self, root, pin, plan, failed=False):
        logs = root.with_name(root.name+'_launch')
        logs.mkdir()
        contract = run.launch_contract(root, plan, pin, self.launcher, run.digest(self.launcher))
        contract.update(pid=41001, pgid=41001, session=41001, launcher_pid=41000, launcher_pgid=41000, launcher_session=41000,
            started_wall=time.time()-25, gpu_uuid='GPU-00000000-0000-0000-0000-000000000002')
        run.write_json(logs/'launch.json', contract)
        launch_pin = run.digest(logs/'launch.json')
        run.write_json(logs/'exit.json', dict(launch_sha256=launch_pin, returncode=1 if failed else 0, ended_wall=time.time()))
        return dict(root=root, plan_sha256=pin, launch_root=logs, launch_sha256=launch_pin,
            launcher=self.launcher, launcher_sha256=run.digest(self.launcher), out=root.with_name(root.name+'_collected'))

    def released_fit(self):
        root, pin, plan = self.prepare()
        self.complete(root, pin, plan)
        result = run.collect(**self.launch(root, pin, plan))
        return root, pin, plan, result

    def readout(self):
        root, pin, plan, release = self.released_fit()
        readout = root.with_name(root.name+'_readout')
        result = run.prepare_readout(root, pin, release['validation'], release['validation_sha256'], readout, self.deadline, self.lease)
        return readout, result['plan_sha256'], run.read(readout/'plan.json')

    def test_prepare_real_owner_audit_counts_masks_batches(self):
        root, pin, plan = self.prepare()
        run.verify_plan(root, pin)
        self.assertEqual((plan['expected_steps'], plan['expected_rows']), (128, 256))
        self.assertEqual(plan['train_config']['grad_accum'], 1)
        self.assertFalse(plan['train_config']['pack'])
        for arm in run.ARMS:
            for row in self.native['rows'][arm]:
                self.assertEqual(row['labels'][:row['context_tokens']], [-100]*row['context_tokens'])
                self.assertEqual(row['labels'].count(900000), 1)
                self.assertEqual(row['labels'][-1], 900000)
            self.assertEqual(len(self.native['optimizer_update_rows']['0']), 128)
        self.assertGreater(sum(cost['padding_tokens'] for cost in self.native['group_costs']['0']), 0)
        self.assertIn('not isolated', plan['dose_limitation'])

    def test_explicit_frozen_config_rejects_seed_lr_batch_and_dose(self):
        for key, value in (('seed', 1), ('lr', .0002), ('batch_size', 4), ('fit_seconds', 1801),
                           ('readout_seconds', 2701), ('epochs', 0)):
            with self.subTest(key=key), self.assertRaises(ValueError):
                run.validate_config(dict(run.DEFAULT_CONFIG, **{key: value}))

    def test_wrong_source_fails_and_preserves_exclusive_prepare(self):
        root = self.directory/'wrong'
        with self.assertRaises(ValueError):
            run.prepare_fit(SOURCE, '0'*64, self.model, root, '2', self.deadline, self.lease)
        self.assertTrue((root/'prepare_failure.json').is_file())
        with self.assertRaises(ValueError):
            run.prepare_fit(SOURCE, self.module_pin, self.model, root, '2', self.deadline, self.lease)

    def test_callback_cannot_claim_native_prepare(self):
        with patch.object(self.corpus, 'audit_native', return_value=deepcopy(self.native)), self.assertRaises(ValueError):
            self.prepare()

    def test_native_recipe_or_count_mismatch_rejected(self):
        native = self.mock_native(self.candidate, self.model, {}, recipe=self.recipe)
        native['updates_per_audited_seed'] = 127
        with patch.object(self.corpus, 'audit_native', return_value=native), self.assertRaises(ValueError):
            self.prepare()

    def test_changed_material_and_wrong_plan_pin(self):
        root, pin, plan = self.prepare()
        with self.assertRaises(ValueError):
            run.read_plan(root, '0'*64)
        (root/'material/AUTH.json').write_text('{}')
        with self.assertRaises(ValueError):
            run.verify_plan(root, pin)

    def test_plan_primary_and_interpreter_guard(self):
        root, pin, plan = self.prepare()
        for key, value in (('primary_criteria', {}), ('python', '/invented/python')):
            modified = dict(plan, **{key: value})
            replace_json(root/'plan.json', modified)
            changed = run.digest(root/'plan.json')
            replace_json(root/'plan.sha256.json', dict(sha256=changed))
            with self.subTest(key=key), self.assertRaises(ValueError):
                run.read_plan(root, changed)

    def test_deadline_six_hour_margin(self):
        root = self.directory/'lease'
        with self.assertRaises(ValueError):
            run.prepare_fit(SOURCE, self.module_pin, self.model, root, '2', iso(time.time()+2000), iso(time.time()+2100))

    def test_full_fit_collection_finite_metadata_archive(self):
        root, pin, plan, collected = self.released_fit()
        accepted = run.accepted_release(collected['validation'], collected['validation_sha256'], plan, pin)
        self.assertTrue(accepted['phase_complete'])
        self.assertFalse(any(name.endswith('.safetensors') for name in accepted['archive_files']))
        audit = run.read(Path(collected['validation']).parent/'audit.json')
        self.assertEqual(len(audit['excluded_weights']), 2)
        self.assertEqual(audit['evidence']['aggregate']['optimizer_updates'], 256)
        self.assertTrue(accepted['costs_nested_not_added'])

    def test_fit_saved_receipt_join_or_loss_mismatch(self):
        root, pin, plan = self.prepare()
        self.complete(root, pin, plan)
        target = root/'run/AUTH/adapter/train_meta.json'
        meta = run.read(target)
        meta['steps'] = 127
        replace_json(target, meta)
        with self.assertRaises(ValueError):
            run.verify_fit(root, plan, self.api, 'AUTH')

    def test_nonfinite_adapter_rejected_without_torch(self):
        root, pin, plan = self.prepare()
        self.complete(root, pin, plan)
        weights(root/'run/AUTH/adapter/adapter_model.safetensors', nonfinite=True)
        with self.assertRaises(ValueError):
            run.verify_fit(root, plan, self.api, 'AUTH')

    def test_partial_pair_never_aggregates(self):
        root, pin, plan = self.prepare()
        self.start(root, pin, plan)
        self.member(root, pin, plan, 'AUTH', 0)
        with self.assertRaises(FileNotFoundError):
            run.reduce_completed(root, plan, self.api)

    def test_failed_phase_collects_without_reducers(self):
        root, pin, plan = self.prepare()
        self.start(root, pin, plan)
        self.member(root, pin, plan, 'AUTH', 0)
        run.write_json(root/'run/failure.json', dict(status='FAILED_PARTIAL', completed=['AUTH'], aggregate=None,
            error_type='TimeoutError', controller_seconds=20., retry=False))
        with patch.object(run, 'reduce_completed', side_effect=AssertionError('failed phase scored')):
            collected = run.collect(**self.launch(root, pin, plan, failed=True))
        receipt = run.accepted_release(collected['validation'], collected['validation_sha256'], plan, pin)
        self.assertFalse(receipt['phase_complete'])
        new_plan = dict(plan, root=str(self.directory/'restart'))
        self.assertFalse(run.check_restart(collected['validation'], collected['validation_sha256'], new_plan)['automatic_retry'])
        with self.assertRaises(ValueError):
            run.prepare_readout(root, pin, collected['validation'], collected['validation_sha256'],
                self.directory/'blocked_readout', self.deadline, self.lease)

    def test_unknown_file_and_credentials_fail_exclusively(self):
        root, pin, plan = self.prepare()
        self.complete(root, pin, plan)
        arguments = self.launch(root, pin, plan)
        (root/'unexpected.txt').write_text('unknown')
        with self.assertRaises(ValueError):
            run.collect(**arguments)
        self.assertTrue((arguments['out']/'collection_failure.json').exists())
        self.assertFalse((arguments['out']/'validation.json').exists())
        with self.assertRaises(ValueError):
            run.collect(**arguments)
        (root/'unexpected.txt').unlink()
        (root/'run/AUTH/worker/stdout.log').write_text('API_KEY=fixture_value')
        with self.assertRaises(ValueError):
            run.inventory(root, plan, arguments['launch_root'])

    def test_live_owned_session_blocks_before_results(self):
        root, pin, plan = self.prepare()
        self.complete(root, pin, plan)
        arguments = self.launch(root, pin, plan)
        orphan = dict(pid=49999, ppid=1, pgid=49998, session=42001)
        with patch.object(run.common, 'process_snapshot', return_value=[orphan]), \
                patch.object(run, 'audit_terminal', side_effect=AssertionError('premature read')):
            self.assertFalse(run.status(root, pin, arguments['launch_root'], arguments['launch_sha256'])['ready'])
            with self.assertRaises(ValueError):
                run.collect(**arguments)

    def test_second_vacancy_failure_preserves_partial_capsule(self):
        root, pin, plan = self.prepare()
        self.complete(root, pin, plan)
        arguments = self.launch(root, pin, plan)
        result = self.mock_vacancy(plan, 'GPU-00000000-0000-0000-0000-000000000002')
        with patch.object(run, 'vacancy', side_effect=[result, ValueError('queue busy')]), self.assertRaises(ValueError):
            run.collect(**arguments)
        self.assertTrue((arguments['out']/'capsule.tgz').is_file())
        self.assertFalse((arguments['out']/'validation.json').exists())

    def test_wrong_launcher_hash_and_exit_returncode(self):
        root, pin, plan = self.prepare()
        self.complete(root, pin, plan)
        arguments = self.launch(root, pin, plan)
        with self.assertRaises(ValueError):
            run.validate_launch(root, plan, pin, arguments['launch_root'], arguments['launch_sha256'], self.launcher, '0'*64)
        exit_path = arguments['launch_root']/'exit.json'
        finished = run.read(exit_path)
        finished['returncode'] = 1
        replace_json(exit_path, finished)
        with self.assertRaises(ValueError):
            run.validate_launch(root, plan, pin, arguments['launch_root'], arguments['launch_sha256'], self.launcher, run.digest(self.launcher))

    def test_readout_complete_capture_then_component_counts(self):
        root, pin, plan = self.readout()
        self.assertEqual(len(plan['requests']), 128)
        self.assertEqual(plan['total_calls'], 384)
        terminal = self.complete(root, pin, plan)
        aggregate = terminal['aggregate']
        self.assertEqual(aggregate['costs']['calls'], 384)
        self.assertFalse(aggregate['automatic_L1_pass'])
        auth = aggregate['registered_component_counts']['AUTH']
        self.assertEqual(auth['operations']['PROSPECT']['required'], 29)
        self.assertEqual(auth['operations']['REVISE']['required'], 58)
        self.assertEqual(auth['anchors']['ADDITION']['required'], 16)
        self.assertEqual(set(auth['twins']), {'goal', 'belief', 'expected', 'observed', 'prior_action'})
        self.assertEqual(set(aggregate['scores']), set(run.CELLS))
        self.assertIn('auth_joint_semantic', aggregate['scores']['DERANGED']['operations']['PROSPECT'])
        first = next(iter(aggregate['flags']['OFF'].values()))
        self.assertTrue(first['tokenizer_eos_in_raw_ids'])
        arguments = self.launch(root, pin, plan)
        launch = run.read(arguments['launch_root']/'launch.json')
        fitted_release = run.read(plan['fit_release'])
        launch['started_wall'] = fitted_release['released_wall']+.001
        controller_path = root/'run/controller.json'
        controller = run.read(controller_path)
        controller['started_wall'] = launch['started_wall']+.001
        replace_json(controller_path, controller)
        replace_json(arguments['launch_root']/'launch.json', launch)
        arguments['launch_sha256'] = run.digest(arguments['launch_root']/'launch.json')
        replace_json(arguments['launch_root']/'exit.json', dict(launch_sha256=arguments['launch_sha256'], returncode=0, ended_wall=time.time()))
        collected = run.collect(**arguments)
        self.assertTrue(collected['phase_complete'])

    def test_no_scorer_before_all_three_complete_captures(self):
        root, pin, plan = self.readout()
        self.start(root, pin, plan)
        self.member(root, pin, plan, 'OFF', 0)
        self.member(root, pin, plan, 'AUTH', 1)
        with patch.object(self.corpus, 'score_outputs', side_effect=AssertionError('premature scoring')) as scorer:
            with self.assertRaises(FileNotFoundError):
                run.reduce_completed(root, plan, self.api)
            scorer.assert_not_called()

    def test_worker_spec_no_parent_answers_or_candidate(self):
        root, pin, plan = self.readout()
        for member in run.CELLS:
            child = run.make_worker_spec(root, plan, member, time.time()+100)
            self.assertFalse({'candidate', 'candidate_path', 'primary_criteria', 'parent', 'targets', 'fit_receipts'} & set(child))
            self.assertEqual(child['requests'], plan['requests'])
            self.assertEqual(child['adapter'] is None, member == 'OFF')

    def test_invalid_outputs_remain_in_denominators(self):
        outputs = {row['id']: '' for row in self.candidate['dev']}
        score = self.corpus.score_outputs(self.candidate, outputs, assigned_arm='DERANGED')
        self.assertEqual(score['operations']['PROSPECT']['total'], 32)
        self.assertEqual(score['operations']['REVISE']['total'], 64)
        self.assertEqual(score['operations']['PROSPECT']['own_map_strict_joint'], 0)
        with self.assertRaises(ValueError):
            self.corpus.score_outputs(self.candidate, dict(list(outputs.items())[:-1]))

    def test_stop_refuses_pid_reuse_without_signal(self):
        root, pin, plan = self.prepare()
        identity = self.start(root, pin, plan)
        with patch.object(run, 'status', return_value=dict(live_owned=[identity])), \
                patch.object(run, 'process_identity', return_value=dict(identity, start_ticks=456)), patch.object(run.os, 'kill') as kill:
            with self.assertRaises(ValueError):
                run.stop(root, pin)
            kill.assert_not_called()

    def test_stop_only_verified_controller_and_preserves_request(self):
        root, pin, plan = self.prepare()
        identity = self.start(root, pin, plan)
        with patch.object(run, 'status', side_effect=[dict(live_owned=[identity]), dict(live_owned=[])]), \
                patch.object(run, 'process_identity', return_value=identity), patch.object(run.os, 'kill') as kill:
            stopped = run.stop(root, pin)
            kill.assert_called_once_with(identity['pid'], signal.SIGTERM)
            self.assertTrue(stopped['collection_required'])
            self.assertTrue((root/'run/stop.request.json').is_file())

    def test_expired_work_window_restores_handlers(self):
        before = signal.getsignal(signal.SIGTERM)
        with self.assertRaises(ValueError), run.work_window(time.time()):
            pass
        self.assertEqual(signal.getsignal(signal.SIGTERM), before)

    def test_main_gpu_opt_in_required(self):
        with self.assertRaises(ValueError):
            run.run_controller('/missing', '0'*64)
        with self.assertRaises(ValueError):
            run.worker('/missing', '0'*64)

    def test_actual_worker_uses_original_trainer_fresh_init_and_exact_masks(self):
        root, pin, plan = self.prepare()
        (root/'run').mkdir()
        (root/'run/AUTH').mkdir()
        child = run.make_worker_spec(root, plan, 'AUTH', time.time()+600)
        spec_path = root/'run/AUTH.spec.json'
        run.write_json(spec_path, child)
        model = object()
        with patch.dict(os.environ, {'CUDA_VISIBLE_DEVICES': '2'}), patch.object(run, 'owned_worker', no_window), \
                patch.object(run, 'load_native', return_value=(Tokenizer(), model)), patch.object(self.trainer, 'run_training') as train:
            result = run.worker(spec_path, run.digest(spec_path), allow_gpu=True)
        self.assertEqual(result['status'], 'WORKER_COMPLETE')
        train.assert_called_once()
        args, kwargs = train.call_args
        self.assertEqual(len(args[0]), 256)
        self.assertIs(args[2], model)
        self.assertEqual(args[3].seed, 0)
        self.assertEqual(args[3].batch_size, 8)
        self.assertNotIn('init_adapter', kwargs)
        self.assertEqual(kwargs['corpus_sha'], plan['material_files']['AUTH.json'])

    def test_changed_actual_fit_mask_fails_before_training(self):
        root, pin, plan = self.prepare()
        (root/'run').mkdir()
        (root/'run/AUTH').mkdir()
        native_path = root/'material/native_audit.json'
        native = run.read(native_path)
        native['rows']['AUTH'][0]['labels'][0] = 3
        replace_json(native_path, native)
        plan['material_files']['native_audit.json'] = run.digest(native_path)
        child = run.make_worker_spec(root, plan, 'AUTH', time.time()+600)
        spec_path = root/'run/AUTH.spec.json'
        run.write_json(spec_path, child)
        with patch.dict(os.environ, {'CUDA_VISIBLE_DEVICES': '2'}), patch.object(run, 'owned_worker', no_window), \
                patch.object(run, 'load_native', return_value=(Tokenizer(), object())), patch.object(self.trainer, 'run_training') as train:
            with self.assertRaises(ValueError):
                run.worker(spec_path, run.digest(spec_path), allow_gpu=True)
        train.assert_not_called()

    def test_real_fit_controller_dispatch_with_mock_supervision(self):
        root, pin, plan = self.prepare()
        identity = dict(pid=41001, ppid=41000, pgid=41001, session=41001, start_ticks=123,
            argv=run.controller_command(root, pin, 'fit'))
        members = []
        def supervise(root, plan, api, member, spec_path, spec_pin, hard_end):
            members.append(member)
            stage = root/'run'/member
            (stage/'worker').mkdir()
            began = time.monotonic()
            run.write_json(stage/'worker/process.json', dict(pid=42000+len(members), pgid=42000+len(members),
                device='2', timeout=600, started=began, argv=run.worker_command(plan['python'], spec_path, spec_pin)))
            self.fit_files(root, plan, member)
            receipt = dict(ok=True, error=None, returncode=0, owned_group_empty=True, gpu_processes_absent=True,
                reservation_release_verified=True, reserved_seconds=time.monotonic()-began, device='2')
            run.write_json(stage/'worker/supervision.json', receipt)
            return receipt
        with patch.dict(os.environ, {'CUDA_VISIBLE_DEVICES': '2'}), patch.object(run, 'process_identity', return_value=identity), \
                patch.object(run.os, 'getpid', return_value=41001), patch.object(run.os, 'getpgrp', return_value=41001), \
                patch.object(run.os, 'getsid', return_value=41001), patch.object(run, 'supervise_member', side_effect=supervise):
            result = run.run_controller(root, pin, allow_gpu=True)
        self.assertEqual(members, list(run.ARMS))
        self.assertEqual(result['aggregate']['optimizer_updates'], 256)
        self.assertTrue(run.audit_terminal(root, plan, self.api, pin)['phase_complete'])
        with self.assertRaises(ValueError), patch.dict(os.environ, {'CUDA_VISIBLE_DEVICES': '2'}), \
                patch.object(run.os, 'getpid', return_value=41001), patch.object(run.os, 'getpgrp', return_value=41001), \
                patch.object(run.os, 'getsid', return_value=41001):
            run.run_controller(root, pin, allow_gpu=True)

    def test_readout_incomplete_usage_is_not_scorable(self):
        root, pin, plan = self.readout()
        self.start(root, pin, plan)
        self.member(root, pin, plan, 'OFF', 0)
        data = root/'run/OFF/data'
        replace_json(data/'usage.json', {})
        replace_json(data/'manifest.json', {'files': self.base.tree_hashes(data, ('manifest.json',))})
        with self.assertRaises(ValueError):
            run.capture_receipt(root, plan, self.api, 'OFF')

    def test_shared_supervisor_parameters_are_unchanged(self):
        root, pin, plan = self.prepare()
        spec_path = root/'run/AUTH.spec.json'
        receipt = dict(ok=True, reservation_release_verified=True, owned_group_empty=True, gpu_processes_absent=True)
        end = time.time()+1800
        with patch.object(run, 'supervisor_window', no_window), patch.object(self.base, 'supervise', return_value=receipt) as supervise:
            run.supervise_member(root, plan, self.api, 'AUTH', spec_path, 'mockpin', end)
        args = supervise.call_args.args
        self.assertEqual(args[0], root/'run/AUTH')
        self.assertEqual(args[1], dict(model=plan['model'], device='2', lease_end=end))
        self.assertEqual(args[2], root/'run/AUTH/worker')
        self.assertIsNone(args[4])

    def test_parent_death_watch_signals_only_owned_worker_group(self):
        stage = self.directory/'owned_worker'
        stage.mkdir()
        run.write_json(stage/'process.json', dict(pid=43001, pgid=43001))
        with patch.object(run.os, 'getpid', return_value=43001), patch.object(run.os, 'getpgrp', return_value=43001), \
                patch.object(run.os, 'getsid', return_value=43001), patch.object(run.os, 'getppid', side_effect=[41001, 1]), \
                patch.object(run.os, 'killpg') as kill:
            with run.owned_worker(stage, time.time()+600):
                until = time.monotonic()+2
                while not kill.called and time.monotonic() < until:
                    time.sleep(.01)
            kill.assert_called_once_with(43001, signal.SIGTERM)

    def test_collection_timeout_preserves_attempt_without_validation(self):
        root, pin, plan = self.prepare()
        self.complete(root, pin, plan)
        arguments = self.launch(root, pin, plan)
        with patch.object(run, 'inventory', side_effect=TimeoutError('mock300s')), self.assertRaises(TimeoutError):
            run.collect(**arguments)
        self.assertFalse((arguments['out']/'validation.json').exists())
        self.assertFalse(run.read(arguments['out']/'collection_failure.json')['retry'])

    def test_successful_phase_cannot_be_restart_source(self):
        root, pin, plan, release = self.released_fit()
        with self.assertRaises(ValueError):
            run.check_restart(release['validation'], release['validation_sha256'], dict(plan, root=str(self.directory/'another')))

    def test_symlink_metadata_is_rejected(self):
        root, pin, plan = self.prepare()
        self.complete(root, pin, plan)
        arguments = self.launch(root, pin, plan)
        (root/'run/AUTH/worker/stdout.log').unlink()
        (root/'run/AUTH/worker/stdout.log').symlink_to(self.launcher)
        with self.assertRaises(ValueError):
            run.inventory(root, plan, arguments['launch_root'])

    def test_huggingface_tokenizer_asset_symlinks_pin_actual_bytes(self):
        original = self.model/'tokenizer.json'
        blob = self.directory/'tokenizer_blob'
        original.rename(blob)
        original.symlink_to(blob)
        pins = run.tokenizer_files(self.model)
        self.assertEqual(pins['tokenizer.json'], run.digest(blob))
        with self.assertRaises(ValueError):
            run.raw(original)


class CLITests(unittest.TestCase):
    def dispatch(self, argv, target, expected, *, plan=None):
        with patch.object(run, target, return_value={'fixture': True}) as called, redirect_stdout(io.StringIO()):
            with patch.object(run, 'read_plan', return_value=(Path('/fixture'), plan or {'phase': 'fit'})):
                run.main(argv)
        called.assert_called_once_with(**expected)

    def test_generated_controller_command_real_parser_and_dispatch(self):
        for phase in run.CAPS:
            command = run.controller_command('/fixture', 'abc', phase)
            self.assertEqual(command[:3], [os.path.abspath(sys.executable), '-B', str(DRIVER)])
            self.dispatch(command[3:], 'run_controller', dict(root='/fixture', plan_sha256='abc', allow_gpu=True), plan={'phase': phase})

    def test_generated_worker_command_real_parser_and_dispatch(self):
        self.dispatch(run.worker_command(os.path.abspath(sys.executable), '/spec', 'sha')[3:], 'worker',
            dict(spec='/spec', spec_sha256='sha', allow_gpu=True))

    def test_generated_collection_command_real_parser_and_dispatch(self):
        command = run.collection_command('/fixture', 'abc', '/launch', 'def', '/launcher', 'ghi', '/output')
        self.dispatch(command[3:], 'collect', dict(root='/fixture', plan_sha256='abc', launch_root='/launch',
            launch_sha256='def', launcher='/launcher', launcher_sha256='ghi', out='/output'))

    def test_prepare_fit_actual_parser_dispatch(self):
        self.dispatch(['prepare-fit', '--source', '/source', '--module-sha256', 'pin', '--model', '/model', '--out', '/out',
            '--device', '2', '--deadline', 'end', '--lease-end', 'lease'], 'prepare_fit',
            dict(source='/source', module_sha256='pin', model='/model', out='/out', device='2', deadline='end', lease_end='lease',
                config=None, restart_release=None, restart_sha256=None))

    def test_prepare_readout_actual_parser_dispatch(self):
        values = dict(fit_root='/fit', fit_plan_sha256='fitpin', fit_release='/release', fit_release_sha256='releasepin',
            out='/out', deadline='end', lease_end='lease')
        argv = ['prepare-readout']+[value for key, item in values.items() for value in ('--'+key.replace('_', '-'), item)]
        self.dispatch(argv, 'prepare_readout', dict(values, restart_release=None, restart_sha256=None))

    def test_status_stop_actual_parser_dispatch(self):
        self.dispatch(['status', '--root', '/root', '--plan-sha256', 'pin'], 'status',
            dict(root='/root', plan_sha256='pin', launch_root=None, launch_sha256=None))
        self.dispatch(['stop', '--root', '/root', '--plan-sha256', 'pin'], 'stop', dict(root='/root', plan_sha256='pin'))

    def test_real_subprocess_help_no_native_import(self):
        result = subprocess.run([sys.executable, '-B', str(DRIVER), '--help'], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0)
        self.assertIn('prepare-readout', result.stdout)
        self.assertIn('collect', result.stdout)

    def test_wrong_phase_dispatch_fails_before_launch(self):
        with patch.object(run, 'read_plan', return_value=(Path('/fixture'), {'phase': 'readout'})), \
                patch.object(run, 'run_controller') as controller, self.assertRaises(ValueError):
            run.main(['fit', '--root', '/fixture', '--plan-sha256', 'pin', '--allow-gpu'])
        controller.assert_not_called()


if __name__ == '__main__':
    unittest.main(verbosity=2)
