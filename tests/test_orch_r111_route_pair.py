from collections import Counter
from contextlib import nullcontext
from dataclasses import dataclass
import json
from pathlib import Path
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from gpu import orch_r111_route_pair as route
from gpu import orch_r110_claude_broker as broker
from gpu.astra_pchain2_native import EncodedRow


class Tensor:
    def __init__(self, data):
        self.data = data

    def __getitem__(self, key):
        if isinstance(key, tuple):
            rows, columns = key
            if isinstance(rows, int):
                return Tensor(self.data[rows][columns])
            return Tensor([row[columns] for row in self.data[rows]])
        return Tensor(self.data[key])

    def tolist(self):
        return self.data


class Loss:
    def __init__(self, value):
        self.value = value

    def __mul__(self, weight):
        return Loss(self.value*weight)

    def backward(self):
        pass

    def detach(self):
        return self

    def cpu(self):
        return self.value


class NativeShapeModel:
    def __init__(self):
        self.config = SimpleNamespace(use_cache=True)
        self.actual_configs = []

    def requires_grad_(self, flag):
        pass

    def eval(self):
        pass

    def train(self):
        pass

    def gradient_checkpointing_enable(self, **kwargs):
        pass

    def gradient_checkpointing_disable(self):
        pass

    def enable_input_require_grads(self):
        pass

    def generate(self, input_ids, attention_mask, generation_config):
        self.actual_configs.append(generation_config)
        return Tensor([row+[7, 9] for row in input_ids.data])

    def __call__(self, **kwargs):
        return SimpleNamespace(loss=Loss(2.0))


def native_shape_engine():
    tokenizer = SimpleNamespace(apply_chat_template=lambda messages, **kwargs: [1, 2],
                                eos_token_id=9, pad_token_id=0,
                                decode=lambda ids, **kwargs: 'thought' if ids == [7] else '')
    torch = SimpleNamespace(tensor=lambda value, **kwargs: Tensor(value), long='long', bfloat16='bf16',
                            ones_like=lambda value: Tensor([[1]*len(row) for row in value.data]),
                            inference_mode=nullcontext, autocast=lambda **kwargs: nullcontext(),
                            isfinite=lambda value: True, equal=lambda left, right: left.data == right.data)
    return SimpleNamespace(tokenizer=tokenizer, model=NativeShapeModel(), torch=torch,
                           transformers=SimpleNamespace(GenerationConfig=lambda **kwargs: kwargs),
                           check=lambda label: None, verify_base=lambda: None, device='fixture_cpu')


class RouteTests(unittest.TestCase):
    def request(self):
        payload = dict(schema='r111_train_public_v1', life_id='fixture', cycle=1, episode=0,
            phase='experience', game='route', task_id='train1',
            task_provenance=dict(split='TRAIN', task_sha256='a'*64, cohort_sha256='b'*64),
            events=[dict(sequence=0, actor='child', text='I predicted left; the public receipt went elsewhere.',
                         visibility='TRAIN_PUBLIC', source_sha256='c'*64)])
        return dict(id='000001_F1_C0001', payload=payload, payload_sha256=route.digest(payload),
                    lane_deadline_unix=100.0)

    def reply(self, request, text='Consider where your attention went.'):
        plan, metadata = broker.adapt_plan(dict(guidance=text, tag='SHIFT', intervention_class='metacognition',
                                               rationale='Attend to the thinking.'), 'route', 'train1')
        return dict(id=request['id'], request_sha256=route.digest(request), status='COMPLETE',
                    actual_model='claude-fable-5-1', plan=plan, parent_metadata=metadata,
                    transcript_receipt=dict(node_only=True, all_verified=True))

    def test_exact_hubble_wire_and_actual_provider_identity(self):
        request = self.request()
        config = dict(life_id='fixture', family='route', train_tasks={'train1': 'a'*64},
                      excluded_task_ids=['final1'], cohort_sha256='b'*64)
        broker.validate_request(request, config)
        result = route.parent_result(self.reply(request), request, 'claude-fable-5-1', now=50)
        self.assertEqual(result['status'], 'COMPLETE')
        self.assertEqual(result['tag'], 'SHIFT')
        self.assertEqual(result['functional_change'], 'UNKNOWN')

    def test_missing_late_wrong_model_and_unarchived_continue(self):
        request = self.request()
        self.assertEqual(route.parent_result(None, request, 'claude-fable-5-1', now=50)['status'], 'MISSING')
        reply = self.reply(request)
        self.assertEqual(route.parent_result(reply, request, 'claude-fable-5-1', now=101)['status'], 'MISSING')
        self.assertEqual(route.parent_result(reply, request, 'wrong-model', now=50)['status'], 'MISSING')
        reply['transcript_receipt'] = {}
        self.assertEqual(route.parent_result(reply, request, 'claude-fable-5-1', now=50)['status'], 'MISSING')

    def test_silent_valid_not_failed(self):
        request = self.request()
        reply = self.reply(request)
        reply.update(status='SILENT', plan=None, parent_metadata=None)
        result = route.parent_result(reply, request, 'claude-fable-5-1', now=50)
        self.assertEqual(result['status'], 'SILENT')
        self.assertEqual(result['parent_text'], '')

    def test_public_feedback_kept_hidden_oracle_not_added(self):
        plan = dict(cohort_sha256='b'*64)
        task = dict(id='train1', task={'opaque': 'task'})
        messages = [dict(role='system', content='system'), dict(role='user', content='Actual receipt: went right'),
                    dict(role='assistant', content='I thought left.')]
        payload = route.public_payload(Path('/tmp/fixture'), plan, task, 1, 0, messages, 'experience', 'a'*64)
        self.assertNotIn('outcome', payload)
        self.assertNotIn('correct', payload)
        self.assertEqual(payload['events'][0]['text'], 'Actual receipt: went right')
        with self.assertRaises(ValueError):
            route.public_payload(Path('/tmp/fixture'), plan, task, 1, 0, messages, 'FINAL', 'a'*64)

    def test_actual_minimal_native_tensor_response_gets_required_fields(self):
        engine = native_shape_engine()
        messages = [dict(role='user', content='experience')]
        response = route.generate(engine, messages)
        self.assertFalse(response['input_truncated'])
        self.assertTrue(response['full_prompt_prefix_verified'])
        self.assertEqual(response['raw'], 'thought')
        self.assertEqual(response['token_ids'], [7, 9])
        self.assertEqual(response['messages'], messages)
        self.assertEqual(response['prompt_tokens'], 2)
        self.assertTrue(response['terminal'])

    def test_native_batch_and_decoding_repetition_guard(self):
        engine = native_shape_engine()
        messages = [dict(role='user', content='experience')]
        response = route.generate(engine, messages, reflection=True)
        self.assertEqual(engine.model.actual_configs[-1]['no_repeat_ngram_size'], 16)
        batch = route.generate_batch(engine, [messages]*8, 2048)
        self.assertEqual(len(batch), 8)
        self.assertTrue(all(row['full_prompt_prefix_verified'] and not row['input_truncated'] for row in batch))

    def test_no_silent_context_crop(self):
        engine = native_shape_engine()
        engine.tokenizer.apply_chat_template = lambda messages, **kwargs: [1]*16384
        with self.assertRaisesRegex(ValueError, 'no_prompt_cropping'):
            route.generate(engine, [dict(role='user', content='large')])

    def test_v3_exact_presentation_and_all_anchor_coverage(self):
        schedule = route.sleep_schedule(2, 3)
        exposures = Counter(tuple(row['own']) for row in schedule)
        self.assertEqual(exposures[('NEW', 0)], 16)
        self.assertEqual(exposures[('NEW', 1)], 16)
        self.assertTrue(all(exposures[('REHEARSAL', index)] == 1 for index in range(3)))
        self.assertEqual(set(index for row in schedule for index in row['anchors']), set(range(42)))

    def test_real_training_loop_updates_exposure_and_lambda(self):
        engine = native_shape_engine()
        optimizer = SimpleNamespace(steps=0, zero_grad=lambda **kwargs: None)
        def step():
            optimizer.steps += 1
        optimizer.step = step
        encoded = EncodedRow((1, 7), (-100, 7), (7,))
        rows = [dict(encoded=encoded, source_call_sha256='a'*64)]
        anchors = [dict(encoded=encoded) for index in range(42)]
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(route.replay, 'encode_row', side_effect=lambda row, tokenizer, limit: row['encoded']), \
                 patch.object(route.native.development, 'enable_existing_adapter'):
                result = route.train_sleep(engine, optimizer, rows, rows, anchors, Path(directory), lambda label: None)
            self.assertEqual(optimizer.steps, 17)
            self.assertEqual(result['child_token_exposure_including_eos'], 17)
            self.assertEqual(result['anchor_token_exposure_including_eos'], 42)
            self.assertEqual(result['anchor_lambda'], .25)
            self.assertEqual(result['rehearsal_presentations_per_row'], 1)
            self.assertFalse(result['optimizer_reset'])
            updates = [json.loads(line) for line in (Path(directory)/'UPDATES.jsonl').read_text().splitlines()]
            self.assertTrue(all(abs(sum(row['losses'])-2) < 1e-6 for row in updates))

    def test_final_separate_and_only_sleep0_morning(self):
        self.assertTrue(route.final_due(0, 0))
        self.assertFalse(route.final_due(1, route.MORNING_CUT-1))
        self.assertTrue(route.final_due(1, route.MORNING_CUT))
        self.assertNotEqual(route.readout_directory(Path('/tmp/root'), 0, 'dev'),
                            route.readout_directory(Path('/tmp/root'), 0, 'final'))

    def test_three_prompts_open_and_no_exhaustion_counts(self):
        self.assertEqual(set(route.prompts()), {'episode', 'presleep', 'reflection'})
        self.assertNotIn('\n', route.PRESLEEP_PROMPT)
        self.assertNotIn('1.', route.PRESLEEP_PROMPT)
        self.assertNotIn('two', route.PRESLEEP_PROMPT)
        self.assertNotIn('bare', route.EPISODE_PROMPT)


if __name__ == '__main__':
    unittest.main()
