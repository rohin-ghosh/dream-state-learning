"""CPU fixtures only: no model, tokenizer package, GPU, subprocess, or network."""
import copy
from collections import UserDict
import importlib.util
import json
import os
from pathlib import Path
import signal
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.dont_write_bytecode = True
DRIVER = Path(os.environ.get('BIRTH_PROBE_DRIVER', '/tmp/astra_birth_skill_probe_run_20260913.py'))
spec = importlib.util.spec_from_file_location('birth_probe_driver', DRIVER)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)
SOURCE = Path(os.environ.get('BIRTH_PROBE_PUBLIC_SOURCE', '/data/home/rohing/dream-state'))


class TokenizerFixture:
    chat_template = 'CPU_ONLY_QWEN_SHAPED_TEMPLATE'

    def apply_chat_template(self, messages, tokenize, add_generation_prompt):
        assert add_generation_prompt is True
        messages = copy.deepcopy(messages)
        if messages[0]['role'] != 'system':
            messages.insert(0, dict(role='system', content='Actual fixture default system.'))
        text = ''.join(f"<|im_start|>{item['role']}\n{item['content']}<|im_end|>\n"
                       for item in messages) + '<|im_start|>assistant\n'
        return self.encode(text, add_special_tokens=False) if tokenize else text

    def encode(self, text, add_special_tokens=False):
        assert add_special_tokens is False
        return list(text.encode())


class FixtureBackend:
    instances = []
    answers = {}
    fail_at = None

    def __init__(self, plan):
        self.seen = []
        self.closed = False
        self.instances.append(self)

    def generate(self, messages):
        if self.fail_at is not None and len(self.seen) == self.fail_at:
            raise RuntimeError('fixture capture failure')
        self.seen.append(copy.deepcopy(messages))
        native = probe.render(TokenizerFixture(), messages)
        text = self.answers[messages[-1]['content']]
        started = probe.time.monotonic()
        return dict(**native, actual_prompt_token_ids=native['prompt_token_ids'],
                    text=text, output_token_ids=list(text.encode()), decoded_output=text,
                    finish_reason='stop', stop_reason=None, started=started, ended=probe.time.monotonic())

    def close(self):
        self.closed = True


class ProbeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='birth-probe-cpu-')
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.root = self.home / 'run'
        self.logs = self.home / 'logs'
        self.logs.mkdir()
        self.source = self.home / 'public'
        for name in probe.SOURCE_NAMES:
            destination = self.source / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes((SOURCE / name).read_bytes())
        self.model = self.home / 'model'
        self.model.mkdir()
        self.model_files = {'config.json': 'cpu-fixture-config',
                            'model.safetensors': 'cpu-fixture-not-real-weights'}
        self.environment = {'cpu_fixture_only': True}
        self.binding = dict(schema=1, scope=probe.SCOPE, visibility='model-only-public',
                            model_name=probe.MODEL_NAME, revision=probe.REVISION,
                            model_files=self.model_files,
                            source_files={name: probe.digest(self.source / name) for name in probe.SOURCE_NAMES},
                            native_environment=self.environment, approved_by='Main')
        self.receipt = self.home / 'binding.json'
        self.receipt.write_text(json.dumps(self.binding, indent=2))
        for target, replacement in (
                ('model_hashes', lambda model: self.model_files),
                ('native_environment', lambda: self.environment),
                ('native_tokenizer', lambda model: TokenizerFixture()),
                ('offline', lambda: None)):
            patcher = patch.object(probe, target, replacement)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.kwargs = dict(root=self.root, source=self.source, model=self.model,
                           binding_path=self.receipt, binding_sha256=probe.digest(self.receipt),
                           corpus_sha256=self.binding['source_files'][probe.SOURCE_NAMES[0]],
                           gpu_uuid='GPU-00000000-0000-0000-0000-000000000001', gpu_index=0,
                           lease_end=probe.time.time() + 10000, log_dir=self.logs)
        result = probe.prepare(**self.kwargs)
        self.plan_hash = result['plan_sha256']
        self.plan = probe.read(self.root / 'plan.json')
        FixtureBackend.instances = []
        FixtureBackend.fail_at = None
        FixtureBackend.answers = {row['input_messages'][-1]['content']: row['raw_target']
                                  for row in probe.read(self.root / 'rows.json')['absent']}

    def seal_fixture(self):
        for condition, pid in zip(probe.CONDITIONS, (100001, 100002), strict=True):
            probe.write(self.root / f'{condition}.process.json', dict(pid=pid))
            with patch.object(probe.os, 'getpid', return_value=pid), \
                    patch.object(probe.os, 'getpgrp', return_value=pid):
                probe.capture(self.plan, condition, self.root / condition, FixtureBackend)
            probe.write(self.root / f'{condition}.release.json', dict(ok=True, returncode=0,
                        owned_group_empty=True, gpu_processes_absent=True, pid=pid,
                        gpu_uuid=self.plan['gpu_uuid']))
        probe.write(self.root / 'release.json', dict(ok=True, calls_closed=24,
                    owned_groups_empty=True, gpu_processes_absent=True,
                    gpu_uuid=self.plan['gpu_uuid'], elapsed=30.0))
        probe.write(self.root / 'archive.json', dict(schema=1, plan_sha256=self.plan_hash,
                    files=probe.tree(self.root)))
        return probe.digest(self.root / 'archive.json')

    def rewrite_archive_fixture(self):
        archive = self.root / 'archive.json'
        files = probe.tree(self.root)
        files.pop('archive.json')
        archive.write_bytes(probe.encoded(dict(schema=1, plan_sha256=self.plan_hash, files=files)))
        return probe.digest(archive)

    def test_pairing_dev12_anchor_only_and_no_metadata_in_input(self):
        rows = probe.read(self.root / 'rows.json')
        self.assertEqual(len(self.plan['calls']['absent']) + len(self.plan['calls']['present']), 24)
        for absent, present in zip(rows['absent'], rows['present'], strict=True):
            self.assertEqual(absent['row_id'], present['row_id'])
            self.assertEqual(present['input_messages'], [dict(role='system', content=probe.ANCHOR)]
                             + absent['input_messages'])
            self.assertEqual(absent['source'], present['source'])
        self.assertEqual(self.plan['calls']['absent'][0]['native']['actual_system_text'],
                         'Actual fixture default system.')
        self.assertEqual(self.plan['calls']['present'][0]['native']['actual_system_text'], probe.ANCHOR)
        self.assertEqual(set(self.plan['calls']['absent'][0]), {'call_id', 'row_id', 'messages', 'native'})

    def test_fresh_backend_each_condition_and_messages_only(self):
        self.seal_fixture()
        self.assertEqual(len(FixtureBackend.instances), 2)
        for backend in FixtureBackend.instances:
            self.assertTrue(backend.closed)
            self.assertEqual(len(backend.seen), 12)
            self.assertTrue(all(set(message) == {'role', 'content'}
                                for messages in backend.seen for message in messages))

    def test_scope_adapter_fit_revision_rejected(self):
        for key, value in [('scope', 'train'), ('revision', 'wrong'), ('adapter', '/old/fitted'),
                           ('fit', True), ('normalization', '/contaminated')]:
            binding = dict(self.binding, **{key: value})
            with self.subTest(key=key), self.assertRaises(ValueError):
                probe.validate_binding(binding, self.kwargs['corpus_sha256'])
        binding = copy.deepcopy(self.binding)
        binding['model_files']['adapter_model.safetensors'] = 'forbidden'
        with self.assertRaisesRegex(ValueError, 'adapter'):
            probe.validate_binding(binding, self.kwargs['corpus_sha256'])

    def test_actual_final_corpus_hash_required(self):
        with self.assertRaisesRegex(ValueError, 'pin'):
            probe.validate_binding(self.binding, '0' * 64)

    def public_receipt_fixture(self):
        return dict(checked_utc='fixture', clean_lineage_certified=False, elapsed_seconds=0,
                    file_count=14, files={f'file{index}': dict(public_match='GIT_BLOB_SHA1',
                    sha256='1' * 64, size=1) for index in range(14)}, historical_receipts_changed=False,
                    limitation='fixture only', metadata_sha256='2' * 64, metadata_url='not-fetched',
                    model=str(self.model), repository=probe.MODEL_NAME, revision=probe.REVISION,
                    status='PUBLIC_REVISION_FILES_MATCHED_PROSPECTIVE_BINDING')

    def test_existing_public_model_receipt_scopes_without_legacy_normalization(self):
        receipt = self.public_receipt_fixture()
        binding = probe.scope_binding(receipt, self.source, self.model, self.kwargs['corpus_sha256'])
        self.assertEqual(binding['scope'], probe.SCOPE)
        self.assertEqual(binding['native_environment'], self.environment)
        self.assertEqual(len(binding['model_files']), 14)
        self.assertEqual(binding['source_files'], self.binding['source_files'])

    def test_public_receipt_wrong_revision_unmatched_file_adapter_rejected(self):
        for mutation in ('revision', 'public_match', 'adapter'):
            receipt = self.public_receipt_fixture()
            if mutation == 'revision':
                receipt['revision'] = 'wrong'
            elif mutation == 'public_match':
                receipt['files']['file0']['public_match'] = 'UNVERIFIED'
            else:
                receipt['adapter'] = '/old/fitted'
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                probe.public_model_files(receipt, self.model)

    def test_dropout_free_greedy_off_capture_settings(self):
        self.assertEqual(probe.PARAMS['temperature'], 0.0)
        self.assertEqual(probe.PARAMS['seed'], 0)
        self.assertEqual(probe.PARAMS['max_tokens'], 192)
        self.assertEqual(probe.PARAMS['n'], 1)
        self.assertFalse(probe.ENGINE['enable_lora'])
        self.assertFalse(probe.ENGINE['enable_prefix_caching'])
        self.assertEqual(probe.ENGINE['tensor_parallel_size'], 1)
        self.assertIn('with torch.inference_mode():', DRIVER.read_text())
        self.assertIn('lora_request=None', DRIVER.read_text())

    def test_failure_preserves_raw_and_never_closes(self):
        FixtureBackend.fail_at = 3
        with self.assertRaisesRegex(RuntimeError, 'fixture capture failure'):
            probe.capture(self.plan, 'absent', self.root / 'absent', FixtureBackend)
        self.assertEqual(len(list((self.root / 'absent').glob('*.response.json'))), 3)
        self.assertTrue((self.root / 'absent' / '03.request.json').exists())
        self.assertFalse((self.root / 'absent' / 'closed.json').exists())
        self.assertTrue(FixtureBackend.instances[0].closed)

    def test_collect_success_only_after_all_captures_closed(self):
        archive_hash = self.seal_fixture()
        scoring = probe.load_corpus(self.root / 'source')
        original = scoring.score_response
        order = []

        def score(row, text):
            probe.validate_captures(self.root, self.plan)
            order.append(row['row_id'])
            return original(row, text)

        scoring.score_response = score
        with patch.object(probe, 'load_corpus', return_value=scoring):
            probe.collect(self.root, self.home / 'collected', self.plan_hash, archive_hash)
        report = probe.read(self.home / 'collected' / 'report.json')
        self.assertEqual(len(order), 24)
        self.assertEqual(report['passed_counts'], {'absent': 12, 'present': 12})
        self.assertIsNone(report['science_pass'])
        self.assertFalse(report['learned_skill_claim'])

    def test_missing_last_capture_never_scores_even_with_resealed_archive(self):
        self.seal_fixture()
        (self.root / 'present' / '11.response.json').unlink()
        archive_hash = self.rewrite_archive_fixture()
        scoring = probe.load_corpus(self.root / 'source')
        scoring.score_response = Mock(side_effect=AssertionError('must not score'))
        with patch.object(probe, 'load_corpus', return_value=scoring), self.assertRaises(FileNotFoundError):
            probe.collect(self.root, self.home / 'failed', self.plan_hash, archive_hash)
        scoring.score_response.assert_not_called()
        self.assertFalse((self.home / 'failed' / 'report.json').exists())

    def test_source_drift(self):
        with (self.source / probe.SOURCE_NAMES[0]).open('a') as stream:
            stream.write('\n')
        with self.assertRaisesRegex(ValueError, 'source drift'):
            probe.verify(self.root, self.plan_hash)

    def test_model_and_native_environment_drift(self):
        with patch.object(probe, 'model_hashes', return_value={'different': 'weights'}):
            with self.assertRaisesRegex(ValueError, 'model drift'):
                probe.verify(self.root, self.plan_hash, native=True)
        with patch.object(probe, 'native_environment', return_value={'different': 'environment'}):
            with self.assertRaisesRegex(ValueError, 'environment drift'):
                probe.verify(self.root, self.plan_hash, native=True)

    def test_stdout_inside_root_and_overlapping_lifecycle_rejected(self):
        with patch.object(probe.os, 'readlink', return_value=str(self.root / 'stdout.log')):
            with self.assertRaisesRegex(ValueError, 'stdout'):
                probe.stdout_outside(self.root)
        with self.assertRaisesRegex(ValueError, 'immutable'):
            probe.prepare(**self.kwargs)
        with self.assertRaisesRegex(ValueError, 'disjoint'):
            probe.collect(self.root, self.root / 'collect', self.plan_hash, 'not-used')

    def test_controller_timeout_no_retry(self):
        process = Mock()
        process.poll.return_value = None
        with patch.object(probe.time, 'monotonic', return_value=11):
            with self.assertRaisesRegex(ValueError, 'controller timeout'):
                probe.wait_worker(process, 10)
        process.poll.assert_called_once()
        with self.assertRaisesRegex(ValueError, 'allocate GPU'):
            probe.controller(self.root, self.plan_hash)

    def test_controller_failure_cleans_only_owned_group_and_external_stdout(self):
        process = Mock(pid=100003)
        with patch.object(probe, 'gpu_state', return_value=True), \
                patch.object(probe.subprocess, 'Popen', return_value=process) as popen, \
                patch.object(probe, 'cleanup', return_value=True) as cleanup, \
                patch.object(probe, 'wait_worker', side_effect=TimeoutError('fixture timeout')):
            with self.assertRaisesRegex(ValueError, 'worker failed'):
                probe.controller(self.root, self.plan_hash, allow_gpu=True)
        popen.assert_called_once()
        cleanup.assert_called_once_with(process)
        self.assertTrue(popen.call_args.kwargs['start_new_session'])
        self.assertTrue(probe.disjoint(self.root, popen.call_args.kwargs['stdout'].name))
        self.assertFalse(probe.read(self.root / 'absent.release.json')['ok'])
        self.assertFalse((self.root / 'present.process.json').exists())
        self.assertFalse((self.root / 'archive.json').exists())
        with self.assertRaises(FileExistsError):
            probe.controller(self.root, self.plan_hash, allow_gpu=True)

    def test_collection_and_controller_alarms_are_separate(self):
        self.assertEqual((probe.CONTROLLER_SECONDS, probe.COLLECT_SECONDS), (900, 180))
        with patch.object(probe.signal, 'signal') as handler, patch.object(probe.signal, 'setitimer') as timer:
            with probe.budget(180):
                with self.assertRaises(TimeoutError):
                    handler.call_args.args[1](signal.SIGALRM, None)
            self.assertEqual(timer.call_args_list[0].args, (signal.ITIMER_REAL, 180))
            self.assertEqual(timer.call_args_list[-1].args, (signal.ITIMER_REAL, 0))

    def test_immutable_collect_and_archive_tamper(self):
        archive_hash = self.seal_fixture()
        before = probe.tree(self.root)
        out = self.home / 'collected'
        probe.collect(self.root, out, self.plan_hash, archive_hash)
        self.assertEqual(before, probe.tree(self.root))
        with self.assertRaisesRegex(ValueError, 'immutable'):
            probe.collect(self.root, out, self.plan_hash, archive_hash)
        (self.root / 'unlisted').write_text('unexpected')
        with self.assertRaisesRegex(ValueError, 'archive hashes'):
            probe.collect(self.root, self.home / 'tampered', self.plan_hash, archive_hash)

    def test_no_weak_false_success_release_and_termination(self):
        self.seal_fixture()
        release = self.root / 'present.release.json'
        contents = probe.read(release)
        contents['gpu_processes_absent'] = 1
        release.write_bytes(probe.encoded(contents))
        archive_hash = self.rewrite_archive_fixture()
        with self.assertRaisesRegex(ValueError, 'release'):
            probe.collect(self.root, self.home / 'unreleased', self.plan_hash, archive_hash)
        call = self.plan['calls']['absent'][0]
        response = probe.read(self.root / 'absent' / '00.response.json')
        for change in ({'finish_reason': None}, {'actual_prompt_token_ids': []},
                       {'output_token_ids': []}, {'ended': float('nan')}, {'decoded_output': 'changed'}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                probe.validate_response(call, dict(response, **change))

    def test_fresh_process_receipts_required(self):
        self.seal_fixture()
        process_path = self.root / 'present.process.json'
        process_path.write_bytes(probe.encoded(dict(pid=100001)))
        with self.assertRaisesRegex(ValueError, 'identity'):
            probe.validate_captures(self.root, self.plan)


class RenderNormalizationTests(unittest.TestCase):
    messages = [dict(role='user', content='CPU public fixture')]

    def template_result(self, tokenizer, result):
        original = tokenizer.apply_chat_template

        def render_result(messages, tokenize, add_generation_prompt):
            if tokenize:
                return result
            return original(messages, tokenize=False, add_generation_prompt=add_generation_prompt)

        return patch.object(tokenizer, 'apply_chat_template', side_effect=render_result)

    def test_mapping_template_input_ids_matches_list_and_preserves_system(self):
        tokenizer = TokenizerFixture()
        expected = probe.render(tokenizer, self.messages)
        tokens = expected['prompt_token_ids']
        for wrapper in (dict, UserDict):
            with self.subTest(wrapper=wrapper.__name__), self.template_result(
                    tokenizer, wrapper(input_ids=tokens, attention_mask=[1] * len(tokens))):
                self.assertEqual(probe.render(tokenizer, self.messages), expected)

    def test_malformed_template_vectors_rejected(self):
        invalid = (None, [], 'input_ids', [True], [False], [1.0], [-1], ['1'], [[1]], {'nested': [1]})
        tokenizer = TokenizerFixture()
        for vector in invalid:
            for result in (vector, {'input_ids': vector, 'attention_mask': [1]}):
                with self.subTest(result=result), self.template_result(tokenizer, result):
                    with self.assertRaisesRegex(ValueError, 'invalid template token vector'):
                        probe.render(tokenizer, self.messages)
        with self.template_result(tokenizer, {'attention_mask': [1]}):
            with self.assertRaisesRegex(ValueError, 'invalid template token vector'):
                probe.render(tokenizer, self.messages)

    def test_mapping_token_mismatch_still_fails_equality_check(self):
        tokenizer = TokenizerFixture()
        tokens = probe.render(tokenizer, self.messages)['prompt_token_ids']
        with self.template_result(tokenizer, {'input_ids': tokens[:-1] + [tokens[-1] + 1]}):
            with self.assertRaisesRegex(ValueError, 'template/token disagreement'):
                probe.render(tokenizer, self.messages)

    def test_malformed_encoded_vectors_cannot_pass_numeric_equality(self):
        tokenizer = TokenizerFixture()
        tokens = probe.render(tokenizer, self.messages)['prompt_token_ids']
        for invalid in (None, [], [True], [-1], [[1]], [float(token) for token in tokens]):
            with self.subTest(invalid=invalid), self.template_result(tokenizer, {'input_ids': tokens}), \
                    patch.object(tokenizer, 'encode', return_value=invalid):
                with self.assertRaisesRegex(ValueError, 'invalid encoded token vector'):
                    probe.render(tokenizer, self.messages)


if __name__ == '__main__':
    unittest.main(verbosity=2)
