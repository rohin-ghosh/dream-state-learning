import contextlib
import copy
import math
import unittest
from types import SimpleNamespace

from organism_v6 import multikey_writer_gateway_simple as w0
from organism_v6 import semantic_carrier_diagnostic as carrier


class Tensor:
    def __init__(self, data):
        self.data = data

    def __getitem__(self, key):
        if isinstance(key, tuple):
            return Tensor(self.data[key[0]][key[1]])
        return Tensor(self.data[key])

    def float(self):
        return self

    def cpu(self):
        return self.data

    def unsqueeze(self, dimension):
        assert dimension == 0
        return Tensor([self.data])

    def all(self):
        def flatten(data):
            if isinstance(data, list):
                return all(flatten(value) for value in data)
            return bool(data)
        return Tensor(flatten(self.data))

    def item(self):
        return self.data


class CpuTorch:
    long = "long"
    inference_mode = staticmethod(contextlib.nullcontext)

    @staticmethod
    def tensor(data, dtype, device):
        assert dtype == "long" and device == "cuda:0"
        return Tensor(copy.deepcopy(data))

    @staticmethod
    def arange(length, dtype, device):
        assert dtype == "long" and device == "cuda:0"
        return Tensor(list(range(length)))

    @staticmethod
    def ones_like(tensor):
        return Tensor([[1] * len(row) for row in tensor.data])

    @staticmethod
    def log_softmax(tensor, dim):
        assert dim == -1
        rows = []
        for logits in tensor.data:
            maximum = max(logits)
            normalizer = math.log(sum(math.exp(value - maximum) for value in logits))
            rows.append([value - maximum - normalizer for value in logits])
        return Tensor(rows)

    @staticmethod
    def isfinite(tensor):
        return Tensor([[math.isfinite(value) for value in row] for row in tensor.data])

    @staticmethod
    def allclose(left, right, rtol, atol):
        assert rtol == 0 and atol == 1e-6
        return len(left.data) == len(right.data) and all(
            len(left_row) == len(right_row) and all(abs(first - second) <= atol
                for first, second in zip(left_row, right_row))
            for left_row, right_row in zip(left.data, right.data))


class TinyCausalModel:
    def __init__(self, leak=False, corrupt=None):
        self.calls = []
        self.leak = leak
        self.corrupt = corrupt

    def __call__(self, input_ids, attention_mask, use_cache, position_ids=None):
        tokens = input_ids.data[0]
        assert attention_mask.data == [[1] * len(tokens)] and use_cache is False
        if position_ids is not None:
            assert position_ids.data == [list(range(len(tokens)))]
        self.calls.append(dict(tokens=list(tokens), positions=copy.deepcopy(position_ids.data)
                               if position_ids is not None else None))
        rows = []
        for index, token in enumerate(tokens):
            following = {1: 2, 2: 3, 4: 5, 5: 0, 6: 0, 0: 0}.get(token, 0)
            if token == 3:
                following = 4 if len(tokens) % 2 == 0 else 6
                if self.leak:
                    following = tokens[index + 1]
            logits = [-8.] * 8
            logits[following] = 8.
            if self.corrupt is not None:
                logits[following] = self.corrupt
            rows.append(logits)
        return SimpleNamespace(logits=Tensor([rows]))


def request_fixture():
    prefix = [1, 2]
    return dict(payload=dict(prompt_input_ids=prefix), candidates=[
        dict(input_ids=prefix + response, labels=[-100] * len(prefix) + response,
             response_ids=list(response), text=text)
        for response, text in [([3, 4, 5, 0], "long"), ([3, 6, 0], "short")]])


def natural_score(model, request):
    result = []
    for candidate in request["candidates"]:
        tokens = CpuTorch.tensor([candidate["input_ids"]], dtype="long", device="cuda:0")
        logits = model(tokens, CpuTorch.ones_like(tokens), False).logits
        probabilities = CpuTorch.log_softmax(logits[0].float(), dim=-1)
        result.append([probabilities[index - 1, token].cpu()
                       for index, (token, label) in enumerate(zip(candidate["input_ids"], candidate["labels"]))
                       if label != -100])
    return result


class SemanticScoreShapeTests(unittest.TestCase):
    def test_old_shape_dependency_fails_mass_new_alignment_passes(self):
        request = request_fixture()
        old = natural_score(TinyCausalModel(), request)
        self.assertGreater(sum(math.exp(sum(values)) for values in old), 1.99)
        result = carrier.score(CpuTorch, TinyCausalModel(), request)
        self.assertEqual(set(result), {"token_logprobs"})
        self.assertLessEqual(sum(math.exp(sum(values)) for values in result["token_logprobs"]), 1)

    def test_exact_originals_masks_positions_and_target_indexing(self):
        request = request_fixture()
        original = copy.deepcopy(request)
        model = TinyCausalModel()
        result = carrier.score(CpuTorch, model, request)
        self.assertEqual(request, original)
        self.assertEqual([call["tokens"] for call in model.calls], [[1, 2, 3, 4, 5, 0], [1, 2, 3, 6, 0, 0]])
        self.assertEqual([call["positions"] for call in model.calls], [[list(range(6))]] * 2)
        self.assertEqual([len(values) for values in result["token_logprobs"]], [4, 3])
        high = -math.log(1 + 7 * math.exp(-16))
        for actual, expected in zip(result["token_logprobs"], [[high] * 4, [high, high - 16, high]]):
            for value, target in zip(actual, expected):
                self.assertAlmostEqual(value, target)

    def test_causal_future_padding_does_not_change_fixed_shape_prefix(self):
        model = TinyCausalModel()
        first = Tensor([[1, 2, 3, 6, 0, 0]])
        second = Tensor([[1, 2, 3, 6, 0, 7]])
        first_logits = model(first, CpuTorch.ones_like(first), False).logits[0].data
        second_logits = model(second, CpuTorch.ones_like(second), False).logits[0].data
        self.assertEqual(first_logits[:5], second_logits[:5])

    def test_future_leak_at_divergent_target_is_rejected(self):
        with self.assertRaisesRegex(w0.ContractError, "shared-prefix"):
            carrier.score(CpuTorch, TinyCausalModel(leak=True), request_fixture())

    def test_full_shared_distribution_checked_not_only_observed_shared_tokens(self):
        class BranchOnlyLeak(TinyCausalModel):
            def __call__(self, *args, **kwargs):
                result = super().__call__(*args, **kwargs)
                result.logits.data[0][2][7] = -7. if len(self.calls) == 1 else -6.
                return result
        with self.assertRaisesRegex(w0.ContractError, "shared-prefix"):
            carrier.score(CpuTorch, BranchOnlyLeak(), request_fixture())

    def test_disjoint_mass_checked_independently(self):
        class InvalidProbabilities(CpuTorch):
            @staticmethod
            def log_softmax(tensor, dim):
                return Tensor([[0.] * len(row) for row in tensor.data])
        with self.assertRaisesRegex(w0.ContractError, "mass exceeds one"):
            carrier.score(InvalidProbabilities, TinyCausalModel(), request_fixture())

    def test_nonfinite_and_positive_values_rejected(self):
        for invalid in (float("nan"), float("inf"), -float("inf"), .1):
            class InvalidProbabilities(CpuTorch):
                @staticmethod
                def log_softmax(tensor, dim):
                    return Tensor([[invalid] * len(row) for row in tensor.data])
            with self.subTest(value=invalid), self.assertRaisesRegex(w0.ContractError, "finite"):
                carrier.score(InvalidProbabilities, TinyCausalModel(), request_fixture())

    def test_candidate_order_does_not_change_scores(self):
        request = request_fixture()
        expected = carrier.score(CpuTorch, TinyCausalModel(), request)["token_logprobs"]
        request["candidates"].reverse()
        self.assertEqual(carrier.score(CpuTorch, TinyCausalModel(), request)["token_logprobs"], expected[::-1])

    def test_equal_length_inputs_require_no_padding(self):
        request = request_fixture()
        request["candidates"][1].update(input_ids=[1, 2, 3, 6, 5, 0], labels=[-100, -100, 3, 6, 5, 0],
                                         response_ids=[3, 6, 5, 0])
        model = TinyCausalModel()
        result = carrier.score(CpuTorch, model, request)
        self.assertEqual([call["tokens"] for call in model.calls], [row["input_ids"] for row in request["candidates"]])
        self.assertEqual([len(values) for values in result["token_logprobs"]], [4, 4])

    def test_source_mask_prefix_and_terminal_drift_rejected_before_forward(self):
        for field, index, value in [("labels", 0, 1), ("labels", -1, -100),
                                     ("input_ids", 0, 7), ("response_ids", -1, 7)]:
            request = request_fixture()
            request["candidates"][1][field][index] = value
            model = TinyCausalModel()
            with self.subTest(field=field, index=index), self.assertRaises(w0.ContractError):
                carrier.score(CpuTorch, model, request)
            self.assertEqual(model.calls, [])
        request = request_fixture()
        request["candidates"][1] = copy.deepcopy(request["candidates"][0])
        with self.assertRaisesRegex(w0.ContractError, "disjoint"):
            carrier.score(CpuTorch, TinyCausalModel(), request)


if __name__ == "__main__":
    unittest.main()
