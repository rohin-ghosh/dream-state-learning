import copy
from contextlib import nullcontext
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from gpu import orch_math_feedback_uptake_stopped as integration
from gpu import orch_math_feedback_uptake_stopped_native as native
from organism_v6 import orch_math_feedback_uptake_base as policy
import orch_math_feedback_uptake_base_test as fixture


class Tensor:
    def __init__(self, values):
        self.values = values

    def tolist(self):
        return self.values

    def __getitem__(self, key):
        if isinstance(key, tuple):
            return Tensor(self.values[key[0]][key[1]])
        return Tensor(self.values[key])


class Tokenizer:
    eos_token_id = 0
    pad_token_id = 0

    def apply_chat_template(self, messages, **unused):
        return [999]

    def decode(self, tokens, **unused):
        return ''.join(chr(token) for token in tokens if token)


class Model:
    def __init__(self, output):
        self.output = output

    def eval(self):
        pass

    def generate(self, input_ids, attention_mask, generation_config, stopping_criteria):
        values = input_ids.tolist()[0].copy()
        for token in self.output[:generation_config.max_new_tokens]:
            values.append(token)
            if any(criterion(Tensor([values]), None) for criterion in stopping_criteria) or token == 0:
                break
        return Tensor([values])


class Engine:
    def __init__(self, output):
        self.check = lambda label: None
        self.tokenizer = Tokenizer()
        self.model = Model(output)
        self.device = 'cpu'
        self.torch = SimpleNamespace(tensor=lambda values, **unused: Tensor(values), long=int,
            ones_like=lambda value: value, inference_mode=nullcontext)
        self.transformers = SimpleNamespace(GenerationConfig=lambda **values: SimpleNamespace(**values), StoppingCriteriaList=list)

    def generate(self, messages, max_new_tokens):
        return dict(original_method=True, messages=messages, cap=max_new_tokens)


class StoppedIntegrationTests(unittest.TestCase):
    def test_only_explicit_reflections_have_a_guard(self):
        engine = integration.engine_class(Engine)([])
        for purpose in ('experience', 'check', 'held'):
            messages = integration.TaggedMessages([{'role': 'user', 'content': 'unchanged'}], purpose)
            self.assertEqual(engine.generate(messages, max_new_tokens=27), Engine([]).generate(list(messages), max_new_tokens=27))
        with self.assertRaisesRegex(AssertionError, 'explicit_purpose'):
            engine.generate([], max_new_tokens=27)

    def test_actual_long_short_long_reflection_stops_without_eos_or_cap(self):
        block = ['This is a recorded thought about checking available evidence. ' * 4, '31 * 21 = 651',
            'I am reconsidering the calculation using the same supplied information. ' * 4]
        text = '\n\n'.join(block * 8)
        output = list(map(ord, text))
        engine = integration.engine_class(Engine)(output)
        response = engine.generate(integration.TaggedMessages([], 'revision'), max_new_tokens=8192)
        ending = response['reflection_guard']
        self.assertTrue(ending['repetition_stop_honored'])
        self.assertEqual(ending['stop_reason'], 'EXACT_REPEATED_PARAGRAPH')
        self.assertFalse(response['terminal'])
        self.assertFalse(response['truncated'])
        self.assertLess(len(response['token_ids']), len(output))
        self.assertEqual(response['raw'], ending['raw_prefix'])
        self.assertEqual(ending['semantic_novelty_yield'], 'UNKNOWN')
        self.assertIn('NOT_AUTO_ADMITTED', ending['fit_eligibility'])

    def test_varied_reflection_survives_until_eos(self):
        text = '\n\n'.join(f'Check {index}: ' + 'The new observation changes this inference. ' * 5 for index in range(5))
        engine = integration.engine_class(Engine)(list(map(ord, text)) + [0])
        response = engine.generate(integration.TaggedMessages([], 'revision'), max_new_tokens=8192)
        self.assertTrue(response['terminal'])
        self.assertFalse(response['truncated'])
        self.assertEqual(response['reflection_guard']['stop_reason'], 'EOS')

    def test_real_cap_distinguished_from_repetition(self):
        engine = integration.engine_class(Engine)(list(map(ord, 'A novel long reflection. ' * 30)))
        response = engine.generate(integration.TaggedMessages([], 'revision'), max_new_tokens=90)
        self.assertFalse(response['terminal'])
        self.assertTrue(response['truncated'])
        self.assertEqual(response['reflection_guard']['stop_reason'], 'MAX_NEW_TOKENS')

    def test_cpu_full_continuation_has_fourteen_calls_and_context_not_weights(self):
        with tempfile.TemporaryDirectory() as temporary:
            original = Path(temporary).resolve()
            root = original / 'campaign_stopped_fixture'
            root.mkdir()
            (root / fixture.broker.QUEUE).mkdir()
            write, read = native.common.write, native.common.read
            write(root / 'READY.json', dict(source_files={}, files={}))
            write(root / 'ACTIVATION.json', dict(native_deadline_unix=9999999999))
            write(root / 'COHORT.json', dict(train=[fixture.tasks()], held=[fixture.tasks('HELD') * 4]))
            carry = dict(task_id='PREVIOUS_TRAIN_C2', question='An earlier question', trace='My prior own sourced reflection.',
                source_record_sha256='a' * 64, outcome={'status': 'INCORRECT'}, original_outcome={'status': 'INCORRECT'})
            write(root / 'PREVIOUS_CARRY.json', carry)
            process = ['fixture_boot', 1, 10]
            observed = []
            class RecordingEngine(fixture.FakeEngine):
                def generate(self, messages, max_new_tokens):
                    observed.append(messages.purpose)
                    return super().generate(messages, max_new_tokens)
            def deliver(unused):
                for path in (root / fixture.broker.QUEUE).glob('*.request.json'):
                    destination = path.with_name(path.name.replace('.request.', '.response.'))
                    if destination.exists():
                        continue
                    directory = original / 'parent_transcripts' / root.name / path.stem
                    directory.mkdir(parents=True)
                    write(directory / 'RAW_RESPONSE.json', fixture.envelope())
                    write(directory / 'PLAN.json', fixture.plan())
                    files = {item.name: native.common.sha(item) for item in directory.iterdir()}
                    write(destination, dict(status='COMPLETE', plan=fixture.plan(), request_sha256=native.common.sha(path),
                        archive=dict(remote_root=str(directory), files=files)))
            with patch.dict(os.environ, CUDA_VISIBLE_DEVICES=policy.UUID), \
                patch.object(Path, 'read_bytes', autospec=True, side_effect=lambda path: ('CUDA_VISIBLE_DEVICES=' + policy.UUID).encode() if str(path) == '/proc/self/environ' else fixture.original_read_bytes(path)), \
                patch.object(native.common, 'validate', return_value=dict(bundle='/fixture', model_dir='/fixture')), \
                patch.object(native.seam.portable, 'verify_base_files', return_value=dict(expected_base_sha256=policy.BASE_SHA)), \
                patch.object(native.seam.native.source.native, 'load_local_tokenizer', return_value=fixture.Tokenizer()), \
                patch.object(integration, 'engine_class', return_value=RecordingEngine), \
                patch.object(native.seam.native, 'process_identity', side_effect=lambda: tuple(process)), \
                patch.object(native.time, 'sleep', side_effect=deliver):
                for phase in ('experience', 'readout'):
                    process[1] += 1
                    native.run(root, 1, phase)
                    self.assertEqual(read(root / 'cycle1' / phase / 'COMPLETE.json')['status'], 'COMPLETE')
                self.assertEqual(observed, ['experience'] * 2 + ['check'] * 2 + ['revision'] * 2 + ['held'] * 8)
                self.assertEqual(len(list(root.glob('cycle*/*/CALL_*.json'))), 14)
                first = read(sorted((root / 'cycle1/experience').glob('CALL_*.json'))[0])
                self.assertIn(carry['trace'], json.dumps(first['messages']))
                self.assertFalse(list(root.rglob('optimizer*')))
                self.assertFalse(list(root.rglob('ROWS.json')))
                context = read(root / 'cycle1/experience/CONTEXT_CONDITION.json')
                self.assertTrue(context['own_train_memory'])


if __name__ == '__main__':
    unittest.main()
