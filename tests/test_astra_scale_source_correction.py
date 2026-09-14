"""Mock-only source-copy correction tests; no model or device runtime."""

from contextlib import ExitStack
from copy import deepcopy
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from gpu import astra_scale_source_correction as runner
from tests.test_astra_goal_scale_collection import fixture, cli as original_cli, replay_inputs
from tests.test_astra_event_two_hop_memory import write
from tests.test_astra_goal_pair_collection import rehash
from tests.test_experienced_event_two_hop import exposed_child


def wrong_address(response):
    response = deepcopy(response)
    address = response['raw'].split()[1]
    replacement = address[:-1] + ('A' if address[-1] != 'A' else 'B')
    response['raw'] = response['raw'].replace(address, replacement)
    return response


def corrected_child(messages, *, max_new_tokens):
    assert max_new_tokens == 160
    response = exposed_child(messages[:4], suffix='\n\n')
    response['messages'] = deepcopy(messages)
    return response


class CorrectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stack = ExitStack()
        cls.addClassCleanup(cls.stack.close)
        cls.root = Path(cls.stack.enter_context(TemporaryDirectory()))
        cls.state = fixture(cls.root, cls.stack)
        cls.engine_factory = staticmethod(cls.state.factory.side_effect)
        for shard in range(8):
            bad_index = 65 if shard == 6 else 1 if shard in (0, 1, 4) else -1

            def factory(arguments, tokenizer, *, check, bad_index=bad_index):
                engine = cls.engine_factory(arguments, tokenizer, check=check)
                generate = engine.generate

                def child(messages, *, max_new_tokens):
                    index = engine.native_calls
                    response = generate(messages, max_new_tokens=max_new_tokens)
                    return wrong_address(response) if index == bad_index else response

                engine.generate = child
                return engine

            with patch.object(runner.source, 'Engine', side_effect=factory):
                runner.original.main(original_cli(cls.root, cls.state, 'expose', shard))
            (cls.root / f'shard-{shard}/source_commit.txt').write_text(runner.SOURCE_COMMIT + '\n')
        cls.options = type('Options', (), dict(bundle=str(cls.root / 'bundle'), bundle_sha=cls.state.bundle_sha,
            model_dir=str(cls.root / 'model'), shard_roots=[str(cls.root / f'shard-{shard}') for shard in range(8)]))()
        cls.inputs = runner.load_inputs(cls.options)

    def setUp(self):
        self.output = Path(self.enterContext(TemporaryDirectory()))
        self.state.factory.reset_mock()
        self.state.token_loader.reset_mock()

    def cli(self, phase):
        values = ['--phase', phase, '--output', str(self.output / phase), '--bundle', self.options.bundle,
            '--bundle-sha', self.options.bundle_sha, '--model-dir', self.options.model_dir,
            '--gpu-uuid', 'fake-gpu', '--shard-roots', *self.options.shard_roots]
        if phase == 'correct':
            values += ['--prepared', str(self.output / 'prepare')]
        return values

    def native_factory(self, mode='valid'):
        def factory(arguments, tokenizer, *, check):
            engine = self.engine_factory(arguments, tokenizer, check=check)
            if mode == 'loaded_state':
                engine.parameter.state = 'f' * 64

            def child(messages, *, max_new_tokens):
                engine.native_calls += 1
                if mode == 'native_error':
                    raise RuntimeError('actual mock native failure')
                if mode == 'state_drift':
                    engine.parameter.state = 'd' * 64
                return corrected_child(messages, max_new_tokens=max_new_tokens)

            engine.generate = child
            return engine
        return factory

    def test_exact_protocol_and_import_without_ml_or_network(self):
        path = Path(runner.__file__).resolve().parents[1] / runner.PROTOCOL_PATH
        self.assertEqual(runner.source.file_hash(path), runner.PROTOCOL_SHA)
        self.assertEqual(runner.FEEDBACK, 'Recorded EVENT identifiers do not exactly match the observed receipt. '
            'Recheck all identifiers and output one correct EVENT line, no other text.\n')
        script = '''
import builtins
original = builtins.__import__
def checked(name, *args, **kwargs):
    if name.split('.')[0] in ('torch', 'transformers', 'tokenizers', 'peft', 'requests', 'httpx'):
        raise AssertionError(name)
    return original(name, *args, **kwargs)
builtins.__import__ = checked
from gpu import astra_scale_source_correction
'''
        result = subprocess.run([sys.executable, '-B', '-c', script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_prepare_all_eight_partial_exposes_no_scores_or_model(self):
        read = runner.source.read

        def bounded(path):
            self.assertFalse({'teach', 'baseline', 'after'} & set(Path(path).parts))
            return read(path)

        with patch.object(runner.source, 'read', side_effect=bounded):
            result = runner.main(self.cli('prepare'))
        self.assertEqual(result['status'], 'PREPARED_NO_MODEL')
        self.assertEqual((result['model_calls'], result['fits'], result['updates']), (0, 0, 0))
        self.assertEqual((result['binding']['routes'], result['binding']['valid_original_events']), (320, 316))
        self.assertEqual([item['shard'] for item in result['binding']['original_exposes'] if not item['source_ready']], [0, 1, 4, 6])
        self.assertEqual([case['source']['split'] for case in self.inputs['selected']], ['TRAIN', 'TRAIN', 'TRAIN', 'PROBE'])
        self.state.factory.assert_not_called()
        self.state.token_loader.assert_not_called()
        self.state.forbidden.assert_not_called()

    def test_reject_duplicate_wrong_source_and_resealed_call_drift(self):
        options = deepcopy(self.options)
        options.shard_roots = [options.shard_roots[0]] * 8
        with self.assertRaisesRegex(ValueError, 'eight_unique'):
            runner.load_inputs(options)
        copy = self.output / 'copied-shard'
        shutil.copytree(self.root / 'shard-0', copy)
        options.shard_roots = [str(copy), *self.options.shard_roots[1:]]
        (copy / 'source_commit.txt').write_text('wrong\n')
        with self.assertRaisesRegex(ValueError, 'original_source_commit'):
            runner.load_inputs(options)
        (copy / 'source_commit.txt').write_text(runner.SOURCE_COMMIT + '\n')
        capture = runner.source.read(copy / 'expose/CALL_001.json')
        capture['messages'][-1]['content'] += '\nUNSEEN ANSWER'
        write(copy / 'expose/CALL_001.json', capture)
        rehash(copy / 'expose')
        with self.assertRaisesRegex(ValueError, 'scale_(native_capture|stage_artifact)_drift'):
            runner.load_inputs(options)

    def test_nonterminal_missing_receipt_or_native_error_not_eligible(self):
        root = self.root / 'shard-0'
        result = runner.source.read(root / 'expose/RESULT.json')
        exposure = runner.source.read(root / 'expose/DATA.json')
        for change in ('nonterminal', 'truncated', 'receipt', 'native_error'):
            with self.subTest(change=change):
                document = deepcopy(exposure)
                record = document['collections'][0]['records'][0]
                if change == 'nonterminal':
                    record['event']['terminal'] = False
                elif change == 'truncated':
                    record['event']['truncated'] = True
                elif change == 'receipt':
                    record['transition'] = None
                else:
                    document['collections'][0]['captures'][1]['error'] = dict(type='RuntimeError', message='native')
                selected, failures = runner.select_records(document, replay_inputs(result), root, 'fixture')
                self.assertEqual(selected, [])
                self.assertEqual(len(failures), 1)
                self.assertFalse(failures[0]['eligible'])

    def test_first_valid_stops_preserves_raw_and_only_public_feedback(self):
        before = deepcopy(self.inputs)
        emitted = {}
        document = runner.execute(self.inputs, corrected_child, lambda name, value: emitted.update({name: deepcopy(value)}))
        self.assertEqual((document['accepted'], document['case_count'], document['model_calls']), (4, 4, 4))
        self.assertEqual(self.inputs, before)
        for index, selected in enumerate(self.inputs['selected']):
            capture = emitted[f'CALL_{index:03d}.json']
            expected = selected['original_event_capture']['messages'] + [
                dict(role='assistant', content=selected['original_record']['event']['raw']),
                dict(role='user', content=runner.FEEDBACK + selected['public_receipt'])]
            self.assertEqual(capture['messages'], expected)
            self.assertNotIn('GOAL ', str(expected))
            self.assertNotIn('EVENT ', selected['public_receipt'])
            candidate = document['cases'][index]['candidate']
            self.assertEqual(candidate['raw'], capture['response']['raw'])
            self.assertTrue(candidate['raw'].endswith('\n\n'))
            self.assertEqual(candidate['correction_capture_sha256'], runner.scale.document_sha256(capture))
            self.assertEqual(candidate['source'], selected['source'])
        self.assertFalse(any(name.startswith('COLLECTION') for name in emitted))

    def test_second_attempt_appends_actual_failure_identical_feedback(self):
        calls = []

        def child(messages, **kwargs):
            calls.append(deepcopy(messages))
            response = corrected_child(messages, **kwargs)
            return wrong_address(response) if len(calls) % 2 else response

        document = runner.execute(self.inputs, child)
        self.assertEqual((document['accepted'], document['model_calls']), (4, 8))
        for index in range(0, 8, 2):
            first = calls[index]
            bad = wrong_address(corrected_child(first, max_new_tokens=160))['raw']
            self.assertEqual(calls[index + 1], first + [dict(role='assistant', content=bad), first[-1]])
        self.assertTrue(all(len(case['attempts']) == 2 for case in document['cases']))

    def test_unfixed_truncated_wrong_address_or_prompt_drift_retained(self):
        for mode in ('wrong', 'truncated', 'prompt'):
            with self.subTest(mode=mode):
                def child(messages, **kwargs):
                    response = corrected_child(messages, **kwargs)
                    if mode == 'wrong':
                        return wrong_address(response)
                    if mode == 'truncated':
                        response.update(terminal=False, truncated=True)
                    else:
                        response['messages'] = []
                    return response

                document = runner.execute(self.inputs, child)
                self.assertEqual((document['accepted'], document['case_count'], document['model_calls']), (0, 4, 8))
                self.assertTrue(all(case['candidate'] is None for case in document['cases']))
                self.assertTrue(all(attempt['validation_error'] for case in document['cases'] for attempt in case['attempts']))

    def test_native_and_malformed_responses_no_fabricated_retry(self):
        for mode in ('native', 'malformed'):
            with self.subTest(mode=mode):
                emitted = {}

                def child(messages, **kwargs):
                    if mode == 'native':
                        raise RuntimeError('actual failure')
                    return {'raw': None, 'terminal': True, 'truncated': False}

                document = runner.execute(self.inputs, child, lambda name, value: emitted.update({name: deepcopy(value)}))
                self.assertEqual((document['accepted'], document['case_count'], document['model_calls']), (0, 4, 4))
                self.assertEqual(document['native_errors'], 4 if mode == 'native' else 0)
                self.assertEqual(len([name for name in emitted if name.startswith('CASE_')]), 4)
                self.assertEqual(emitted['CALL_000.json']['messages'][-2]['content'],
                                 self.inputs['selected'][0]['original_record']['event']['raw'])

    def test_native_bridge_same_state_immutable_sources_and_fresh_outputs(self):
        before = {str(path): runner.source.file_hash(path) for root in self.options.shard_roots
                  for path in Path(root).rglob('*') if path.is_file()}
        runner.main(self.cli('prepare'))
        with patch.object(runner.source, 'Engine', side_effect=self.native_factory()):
            result = runner.main(self.cli('correct'))
        self.assertEqual((result['status'], result['accepted'], result['model_calls']), ('COMPLETE', 4, 4))
        self.assertEqual(result['loaded_adapter_state_sha256'], result['adapter_state_after'])
        self.assertEqual(result['adapter_state_after'], runner.PARENT_STATE)
        self.assertTrue(result['frozen_base_unchanged'])
        self.assertFalse(result['repair_promotion'])
        self.assertFalse(result['trainingAllowed'])
        self.assertEqual(result['max_seconds'], 900)
        engine = self.state.engines[-1]
        self.assertEqual((engine.steps, engine.optimizers), (0, []))
        self.assertEqual(Path(engine.arguments.adapter_dir), self.root / 'bundle/adapter')
        for path, digest in before.items():
            self.assertEqual(runner.source.file_hash(path), digest)
        runner.portable.transfer.verify_files(self.output / 'correct', result['output_files'])
        self.assertFalse(list((self.output / 'correct').glob('COLLECTION*')))
        with self.assertRaisesRegex(ValueError, 'fresh_correction_output'):
            runner.main(self.cli('correct'))

    def test_runtime_native_and_state_failures_retained(self):
        runner.main(self.cli('prepare'))
        for mode in ('native_error', 'state_drift', 'loaded_state'):
            with self.subTest(mode=mode):
                values = self.cli('correct')
                directory = self.output / mode
                values[values.index('--output') + 1] = str(directory)
                with patch.object(runner.source, 'Engine', side_effect=self.native_factory(mode)):
                    with self.assertRaises(ValueError):
                        runner.main(values)
                failed = runner.source.read(directory / 'FAILED.json')
                self.assertEqual(failed['status'], 'FAILED')
                self.assertFalse((directory / 'RESULT.json').exists())
                self.assertEqual(failed['model_calls'], 0 if mode == 'loaded_state' else 4)
                if mode == 'native_error':
                    self.assertEqual(runner.source.read(directory / 'DATA.json')['native_errors'], 4)
                if mode == 'state_drift':
                    self.assertNotEqual(failed['adapter_state_after'], runner.PARENT_STATE)

    def test_preparation_tamper_offline_gpu_and_overlap_before_model(self):
        runner.main(self.cli('prepare'))
        selection = runner.source.read(self.output / 'prepare/SELECTION.json')
        selection[0]['public_receipt'] += 'UNSEEN ANSWER'
        write(self.output / 'prepare/SELECTION.json', selection)
        rehash(self.output / 'prepare')
        with self.assertRaisesRegex(ValueError, 'prepared_selection_drift'):
            runner.main(self.cli('correct'))
        for environment, reason in ((dict(CUDA_VISIBLE_DEVICES='other-gpu'), 'exact_gpu'),
                                    (dict(HF_HUB_OFFLINE='0'), 'offline')):
            with patch.dict(os.environ, environment):
                with self.assertRaisesRegex(ValueError, reason):
                    runner.main(self.cli('correct'))
        values = self.cli('prepare')
        values[values.index('--output') + 1] = str(self.root / 'shard-0/new-output')
        with self.assertRaisesRegex(ValueError, 'readonly_input_output_overlap'):
            runner.main(values)
        self.state.factory.assert_not_called()
        self.state.token_loader.assert_not_called()

    def test_bad_protocol_base_and_deadline_stop_before_model(self):
        with patch.object(runner, 'PROTOCOL_SHA', '0' * 64):
            with self.assertRaisesRegex(ValueError, 'exact_correction_protocol'):
                runner.load_inputs(self.options)
        model = self.output / 'wrong-base'
        shutil.copytree(self.root / 'model', model)
        (model / 'model.safetensors').write_bytes(b'wrong')
        options = deepcopy(self.options)
        options.model_dir = str(model)
        with self.assertRaisesRegex(ValueError, 'local_base_file_inventory_drift'):
            runner.load_inputs(options)
        runner.main(self.cli('prepare'))
        with patch.object(runner.time, 'time', side_effect=[0, 901, 901]):
            with self.assertRaisesRegex(ValueError, 'correction_deadline:before_model'):
                runner.main(self.cli('correct'))
        self.state.factory.assert_not_called()
        self.state.token_loader.assert_not_called()


if __name__ == '__main__':
    unittest.main()
