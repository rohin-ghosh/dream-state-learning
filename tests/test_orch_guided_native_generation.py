"""CPU doubles: generation-call parity and budget checks, not native throughput."""

from contextlib import nullcontext
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from gpu import orch_guided_native as native
from gpu import orch_guided_native_generation as generation


class Vector:
    def __init__(self, values):
        self.values = values

    def tolist(self):
        return self.values


class Matrix:
    def __init__(self, values):
        self.values = values

    def __getitem__(self, index):
        row, columns = index
        return Vector(self.values[row][columns])


class Tokenizer:
    eos_token_id = 1
    pad_token_id = 0

    def apply_chat_template(self, messages, **kwargs):
        return list(messages[0]['synthetic_tokens'])

    def decode(self, values, **kwargs):
        return ''.join(chr(value) for value in values)


def fixture(tail, *, model_limit=32768, changed_prefix=False):
    calls, checks = [], []
    def model_generate(**kwargs):
        calls.append(kwargs)
        prefix = list(kwargs['input_ids'].values[0])
        if changed_prefix:
            prefix[0] += 1
        return Matrix([prefix + tail])
    engine = SimpleNamespace(device='cuda:0', tokenizer=Tokenizer(), check=checks.append,
        model=SimpleNamespace(training=False, config=SimpleNamespace(max_position_embeddings=model_limit),
            named_parameters=lambda: [('fixture.weight', SimpleNamespace(requires_grad=False))],
            generate=model_generate),
        torch=SimpleNamespace(long='long', tensor=lambda values, **kwargs: Matrix(values),
            ones_like=lambda inputs: Matrix([[1] * len(inputs.values[0])]), inference_mode=nullcontext),
        transformers=SimpleNamespace(GenerationConfig=lambda **kwargs: SimpleNamespace(**kwargs)))
    loaded = SimpleNamespace(engine=engine, process=native.process_identity(),
        context=native.StageContext(), binding=SimpleNamespace(phase='collection', parent_present=False))
    return loaded, calls, checks


class GenerationBudgetTests(unittest.TestCase):
    def setUp(self):
        self.messages = [dict(synthetic_tokens=[20, 21, 22])]

    def test_legacy_call_and_result_parity(self):
        for tail, cap in (([65, 66, 1], 10), ([65, 66], 2), ([65], 10), ([], 10)):
            with self.subTest(tail=tail):
                loaded, calls, checks = fixture(tail)
                old = native.source.Engine.generate(loaded.engine, self.messages, max_new_tokens=cap)
                new = generation.generate(loaded, self.messages, max_prompt_tokens=2048, max_new_tokens=cap)
                self.assertEqual(new, old)
                self.assertEqual(vars(calls[0]['generation_config']), vars(calls[1]['generation_config']))
                self.assertEqual(calls[0]['input_ids'].values, calls[1]['input_ids'].values)
                self.assertEqual(calls[0]['attention_mask'].values, calls[1]['attention_mask'].values)
                self.assertEqual(checks, ['generation', 'generation'])

    def test_explicit_long_budget_is_not_silently_capped(self):
        loaded, calls, checks = fixture([65] * 1000 + [1])
        messages = [dict(synthetic_tokens=[20] * 4096)]
        result = generation.generate(loaded, messages, max_prompt_tokens=8192, max_new_tokens=8192)
        self.assertEqual(result['prompt_tokens'], 4096)
        self.assertEqual(len(result['token_ids']), 1001)
        self.assertEqual(calls[0]['generation_config'].max_new_tokens, 8192)
        self.assertTrue(result['terminal'])
        self.assertFalse(result['truncated'])
        self.assertEqual(checks, ['generation'])
        with self.assertRaisesRegex(ValueError, 'bounded_generation_tokens_required'):
            native.source.Engine.generate(loaded.engine, messages, max_new_tokens=8192)

    def test_invalid_budgets_fail_before_generation(self):
        for prompt, new in ((0, 5), (10, 0), (True, 5), (10, True), (2.5, 3), (10, -1), (32768, 1)):
            with self.subTest(prompt=prompt, new=new):
                loaded, calls, unused = fixture([1])
                with self.assertRaises(ValueError):
                    generation.generate(loaded, self.messages, max_prompt_tokens=prompt, max_new_tokens=new)
                self.assertEqual(calls, [])

    def test_model_limit_and_prompt_limit_fail_without_truncation(self):
        loaded, calls, unused = fixture([1], model_limit=64)
        with self.assertRaisesRegex(ValueError, 'declared_total_budget_exceeds_model_positions'):
            generation.generate(loaded, self.messages, max_prompt_tokens=64, max_new_tokens=1)
        with self.assertRaisesRegex(ValueError, 'context_bound_exceeded_no_truncation'):
            generation.generate(loaded, self.messages, max_prompt_tokens=2, max_new_tokens=10)
        self.assertEqual(calls, [])

    def test_process_parent_and_training_mismatches_fail_before_generation(self):
        mutations = (
            lambda loaded: setattr(loaded, 'process', ('other-boot', -1, 0)),
            lambda loaded: setattr(loaded.binding, 'phase', 'training'),
            lambda loaded: setattr(loaded.engine.model, 'training', True),
            lambda loaded: setattr(loaded, 'context', native.StageContext(('uninventoried-parent',))),
            lambda loaded: setattr(loaded.engine.model, 'named_parameters',
                lambda: [('fixture.weight', SimpleNamespace(requires_grad=True))]),
        )
        for mutation in mutations:
            loaded, calls, unused = fixture([1])
            mutation(loaded)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                generation.generate(loaded, self.messages, max_prompt_tokens=16, max_new_tokens=16)
            self.assertEqual(calls, [])

    def test_readout_context_stays_parent_free(self):
        loaded, calls, unused = fixture([1])
        loaded.binding.phase = 'sealed_readout'
        loaded.context = native.StageContext(sleep_prompt='replay context')
        with self.assertRaisesRegex(ValueError, 'clean_readout_context_required'):
            generation.generate(loaded, self.messages, max_prompt_tokens=16, max_new_tokens=16)
        self.assertEqual(calls, [])

    def test_prefix_and_generated_budget_drift_fail(self):
        for tail, changed_prefix, error in (([1], True, 'generated_prefix_changed'),
                                            ([65, 65, 65], False, 'generated_tail_exceeds_declared_budget')):
            loaded, unused, checks = fixture(tail, changed_prefix=changed_prefix)
            with self.subTest(error=error), self.assertRaisesRegex(ValueError, error):
                generation.generate(loaded, self.messages, max_prompt_tokens=16, max_new_tokens=2)

    def test_caller_deadline_is_not_bypassed(self):
        loaded, calls, unused = fixture([1])
        with patch.object(loaded.engine, 'check', side_effect=ValueError('deadline')):
            with self.assertRaisesRegex(ValueError, 'deadline'):
                generation.generate(loaded, self.messages, max_prompt_tokens=16, max_new_tokens=16)
        self.assertEqual(calls, [])


if __name__ == '__main__':
    unittest.main()
