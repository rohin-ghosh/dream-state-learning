"""CPU-only loss/gradient and unchanged-default regressions for sleep CE."""

from copy import deepcopy
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from gpu import orch_r125_continual_native as loss_impl

try:
    import torch
    import torch.nn.functional as functional
except ImportError:
    torch = None


def reference_loss(logits, labels):
    shifted = functional.pad(labels, (0, 1), value=-100)[..., 1:].contiguous()
    return functional.cross_entropy(logits.float().reshape(-1, logits.shape[-1]),
        shifted.reshape(-1).to(logits.device), ignore_index=-100, reduction='mean')


class ImplementationContractTests(unittest.TestCase):
    def test_absent_default_and_explicit_version(self):
        self.assertEqual(loss_impl.sleep_loss_implementation({}), loss_impl.MODEL_DEFAULT)
        for implementation in (loss_impl.MODEL_DEFAULT, loss_impl.MASKED_CAUSAL_CE_V1):
            self.assertEqual(loss_impl.sleep_loss_implementation({'sleep_loss_impl': implementation}), implementation)

    def test_unknown_versions_fail_before_model_forward(self):
        for implementation in (None, True, 1, [], {}, 'MASKED_CAUSAL_CE_V2'):
            model = Mock()
            with self.subTest(implementation=implementation), self.assertRaisesRegex(ValueError,
                    'known_versioned_sleep_loss_impl'):
                loss_impl.sleep_causal_loss(model, 'inputs', 'labels', 'mask', implementation=implementation)
            model.assert_not_called()

    def test_default_retains_exact_model_loss_and_kwargs(self):
        expected = object()
        model = Mock(return_value=SimpleNamespace(loss=expected))
        self.assertIs(loss_impl.sleep_causal_loss(model, 'inputs', 'labels', 'mask'), expected)
        model.assert_called_once_with(input_ids='inputs', labels='labels', attention_mask='mask', use_cache=False)

    def test_plan_rejects_unknown_loss_before_runtime_initialization(self):
        with self.assertRaisesRegex(ValueError, 'known_versioned_sleep_loss_impl'):
            loss_impl.validate_plan(dict(schema=loss_impl.SCHEMA, base_sha256=loss_impl.BASE_SHA256,
                sleep_loss_impl='unknown'))


@unittest.skipIf(torch is None, 'PyTorch CPU environment required')
class MaskedCausalLossTests(unittest.TestCase):
    def setUp(self):
        self.rng = torch.random.fork_rng(devices=[])
        self.rng.__enter__()
        self.addCleanup(self.rng.__exit__, None, None, None)
        torch.manual_seed(541)
        torch.set_num_threads(1)

    def compare(self, logits, labels):
        actual_logits = logits.detach().clone().requires_grad_(True)
        expected_logits = logits.detach().clone().requires_grad_(True)
        actual = loss_impl.masked_causal_mean_loss(actual_logits, labels)
        expected = reference_loss(expected_logits, labels)
        torch.testing.assert_close(actual, expected, rtol=2e-6, atol=2e-7, equal_nan=True)
        actual.backward()
        expected.backward()
        torch.testing.assert_close(actual_logits.grad, expected_logits.grad, rtol=2e-5, atol=2e-7)
        return actual, actual_logits.grad

    def test_loss_and_gradient_unequal_prefixes_and_internal_masks(self):
        for dtype in (torch.float32, torch.float64, torch.bfloat16, torch.float16):
            for prefixes in ((0, 3, 8), (1, 9, 11), (10, 2, 6)):
                with self.subTest(dtype=dtype, prefixes=prefixes):
                    logits = torch.randn(3, 11, 17, dtype=dtype)
                    labels = torch.randint(0, 17, (3, 11))
                    for row, count in enumerate(prefixes):
                        labels[row, :count] = -100
                    labels[:, 5] = -100
                    self.compare(logits, labels)

    def test_global_token_mean_not_mean_of_unequal_sequence_means(self):
        logits = torch.zeros(2, 5, 3)
        logits[0, :, 0] = 6
        labels = torch.tensor([[-100, 0, -100, -100, -100], [-100, 0, 0, 0, 0]])
        actual, _ = self.compare(logits, labels)
        wrong = (reference_loss(logits[:1], labels[:1]) + reference_loss(logits[1:], labels[1:])) / 2
        self.assertGreater(abs(actual.item() - wrong.item()), 0.1)

    def test_shift_uses_preceding_logit_and_masks_tail(self):
        labels = torch.tensor([[999, -100, -100, 2, -100]])
        _, gradient = self.compare(torch.randn(1, 5, 4), labels)
        self.assertTrue(bool((gradient[:, (0, 1, 3, 4)] == 0).all()))
        self.assertGreater(gradient[:, 2].abs().sum().item(), 0)

    def test_all_ignored_and_no_shifted_targets_retain_nan_zero_gradient(self):
        for labels in (torch.full((2, 7), -100), torch.tensor([[2]]),
                torch.tensor([[1, -100, -100]]), torch.empty((2, 0), dtype=torch.long)):
            with self.subTest(shape=labels.shape):
                actual, gradient = self.compare(torch.randn(*labels.shape, 5), labels)
                self.assertTrue(bool(torch.isnan(actual)))
                self.assertTrue(bool((gradient == 0).all()))

    def test_noncontiguous_inputs(self):
        logits = torch.randn(2, 9, 12)[..., ::2]
        labels = torch.randint(0, 6, (2, 18))[:, ::2]
        labels[:, :5] = -100
        actual = loss_impl.masked_causal_mean_loss(logits, labels)
        torch.testing.assert_close(actual, reference_loss(logits, labels), rtol=2e-6, atol=2e-7)

    def test_cross_entropy_receives_only_selected_fp32_rows(self):
        logits = torch.randn(2, 128, 19, dtype=torch.bfloat16, requires_grad=True)
        labels = torch.full((2, 128), -100)
        labels[0, 127] = 2
        labels[1, 124:] = 4
        cross_entropy = functional.cross_entropy
        with patch.object(functional, 'cross_entropy', wraps=cross_entropy) as wrapped:
            loss_impl.masked_causal_mean_loss(logits, labels).backward()
        wrapped.assert_called_once()
        selected_logits, selected_labels = wrapped.call_args.args
        self.assertEqual(selected_logits.shape, (5, 19))
        self.assertEqual(selected_logits.dtype, torch.float32)
        self.assertEqual(selected_labels.tolist(), [2, 4, 4, 4, 4])

    def test_invalid_target_dtype_and_indices_keep_ce_errors(self):
        logits = torch.randn(1, 4, 5)
        for labels in (torch.tensor([[-100, -2, 1, 2]]), torch.tensor([[-100, 5, 1, 2]]),
                torch.tensor([[-100., 1., 2., 3.]])):
            with self.subTest(labels=labels):
                with self.assertRaises((RuntimeError, IndexError, TypeError)) as expected:
                    reference_loss(logits, labels)
                with self.assertRaises(type(expected.exception)):
                    loss_impl.masked_causal_mean_loss(logits, labels)

    def test_unaligned_shapes_rejected(self):
        for logits, labels in ((torch.zeros(1, 3, 5), torch.zeros(1, 2, dtype=torch.long)),
                (torch.zeros(3, 5), torch.zeros(3, dtype=torch.long)),
                (torch.zeros(1, 3, 5), torch.zeros(3, dtype=torch.long))):
            with self.assertRaisesRegex(ValueError, 'aligned_batched_causal_logits_labels_required'):
                loss_impl.masked_causal_mean_loss(logits, labels)

    def test_rng_state_unchanged_by_loss(self):
        logits = torch.randn(2, 8, 11, requires_grad=True)
        labels = torch.randint(0, 11, (2, 8))
        labels[:, :6] = -100
        before = torch.get_rng_state().clone()
        loss_impl.masked_causal_mean_loss(logits, labels).backward()
        self.assertTrue(torch.equal(before, torch.get_rng_state()))

    def make_model(self):
        class CausalModel(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.embedding = torch.nn.Embedding(17, 7)
                self.dropout = torch.nn.Dropout(0.2)
                self.projection = torch.nn.Linear(7, 17, bias=False)
                self.calls = []

            def forward(self, **kwargs):
                self.calls.append(kwargs)
                hidden = self.embedding(kwargs['input_ids']).cumsum(dim=1)
                hidden = self.dropout(hidden)
                keep = kwargs.get('logits_to_keep', 0)
                logits = self.projection(hidden[:, -keep:, :])
                labels = kwargs.get('labels')
                return SimpleNamespace(logits=logits, loss=None if labels is None else reference_loss(logits, labels))

        return CausalModel()

    def test_full_context_forward_gradients_and_rng_match(self):
        model = self.make_model()
        candidate = deepcopy(model)
        inputs = torch.tensor([[0, 1, 2, 3, 4, 5, 6]])
        labels = inputs.clone()
        labels[:, :5] = -100
        mask = torch.ones_like(inputs)
        before = torch.get_rng_state().clone()
        expected = loss_impl.sleep_causal_loss(model, inputs, labels, mask)
        expected.backward()
        after = torch.get_rng_state().clone()
        torch.set_rng_state(before)
        actual = loss_impl.sleep_causal_loss(candidate, inputs, labels, mask,
            implementation=loss_impl.MASKED_CAUSAL_CE_V1)
        actual.backward()
        torch.testing.assert_close(actual, expected)
        for parameter, original in zip(candidate.parameters(), model.parameters()):
            torch.testing.assert_close(parameter.grad, original.grad, rtol=2e-5, atol=2e-7)
        self.assertTrue(torch.equal(after, torch.get_rng_state()))
        self.assertEqual(len(candidate.calls), 1)
        self.assertEqual(set(candidate.calls[0]), {'input_ids', 'attention_mask', 'use_cache'})
        self.assertIs(candidate.calls[0]['input_ids'], inputs)
        self.assertIs(candidate.calls[0]['attention_mask'], mask)
        self.assertIs(candidate.calls[0]['use_cache'], False)
        self.assertGreater(candidate.embedding.weight.grad[0].abs().sum().item(), 0)

    def test_native_sample_reuses_R145_window_with_full_input_and_mask(self):
        model = self.make_model()
        candidate = deepcopy(model)
        inputs = torch.arange(12).reshape(1, 12)
        labels = inputs.clone()
        labels[:, :9] = -100
        mask = torch.ones_like(inputs)
        sample = SimpleNamespace(input_ids=tuple(inputs[0].tolist()), labels=tuple(labels[0].tolist()),
            target_ids=tuple(inputs[0, 9:].tolist()))
        before = torch.get_rng_state().clone()
        expected = loss_impl.sleep_causal_loss(model, inputs, labels, mask, sample=sample)
        expected.backward()
        after = torch.get_rng_state().clone()
        torch.set_rng_state(before)
        from gpu.orch_r145_suffix_loss import loss_window
        with patch('gpu.orch_r145_suffix_loss.loss_window', wraps=loss_window) as window:
            actual = loss_impl.sleep_causal_loss(candidate, inputs, labels, mask, sample=sample,
                implementation=loss_impl.MASKED_CAUSAL_CE_V1)
            actual.backward()
        window.assert_called_once_with(sample)
        self.assertIs(candidate.calls[0]['input_ids'], inputs)
        self.assertIs(candidate.calls[0]['attention_mask'], mask)
        self.assertEqual(candidate.calls[0]['logits_to_keep'], 4)
        self.assertNotIn('labels', candidate.calls[0])
        torch.testing.assert_close(actual, expected)
        for parameter, original in zip(candidate.parameters(), model.parameters()):
            torch.testing.assert_close(parameter.grad, original.grad, rtol=2e-5, atol=2e-7)
        self.assertTrue(torch.equal(after, torch.get_rng_state()))

    def test_invalid_native_suffix_fails_before_forward(self):
        inputs = torch.tensor([[1, 2, 3]])
        labels = torch.tensor([[-100, -100, 3]])
        invalid = SimpleNamespace(input_ids=(1, 2, 3), labels=(-100, -100, 3), target_ids=(2, 3))
        model = Mock()
        with self.assertRaisesRegex(ValueError, 'exact_masked_prefix_contiguous_target_required'):
            loss_impl.sleep_causal_loss(model, inputs, labels, torch.ones_like(inputs), sample=invalid,
                implementation=loss_impl.MASKED_CAUSAL_CE_V1)
        model.assert_not_called()

    def test_weighted_anchor_microbatches_optimizer_and_rng_match(self):
        initial = self.make_model()
        models = [deepcopy(initial), deepcopy(initial)]
        inputs = torch.arange(12).reshape(1, 12)
        initial_rng = torch.get_rng_state().clone()
        results = []
        for model, implementation in zip(models, (loss_impl.MODEL_DEFAULT, loss_impl.MASKED_CAUSAL_CE_V1)):
            torch.set_rng_state(initial_rng)
            optimizer = torch.optim.AdamW(model.parameters(), lr=3e-5, foreach=False, fused=False)
            for _ in range(2):
                optimizer.zero_grad(set_to_none=True)
                for prefix, weight in zip((9, 2, 11, 7, 3), (0.75, 0.0625, 0.0625, 0.0625, 0.0625)):
                    labels = inputs.clone()
                    labels[:, :prefix] = -100
                    loss = loss_impl.sleep_causal_loss(model, inputs, labels, torch.ones_like(inputs),
                        implementation=implementation)
                    (loss * weight).backward()
                optimizer.step()
            results.append((optimizer.state_dict(), torch.get_rng_state().clone()))
        self.assertEqual(len(models[0].calls), 10)
        self.assertEqual(len(models[1].calls), 10)
        self.assertTrue(torch.equal(results[0][1], results[1][1]))
        for parameter, original in zip(models[1].parameters(), models[0].parameters()):
            torch.testing.assert_close(parameter, original, rtol=2e-5, atol=2e-7)
        self.assertEqual(results[0][0]['param_groups'], results[1][0]['param_groups'])
        for key, state in results[0][0]['state'].items():
            for field, expected in state.items():
                torch.testing.assert_close(results[1][0]['state'][key][field], expected, rtol=2e-5, atol=2e-7)


if __name__ == '__main__':
    unittest.main()
