"""Synthetic source-only mechanics; no native model/tokenizer qualification."""

from contextlib import contextmanager
from copy import deepcopy
from dataclasses import replace
import importlib
import importlib.util
import json
import os
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from organism_v6 import composition_birth_stage2a_actor as source
from organism_v6 import composition_birth_stage2a_held as held
from organism_v6 import composition_birth_stage2a_primitives as primitives
from organism_v6 import composition_birth_stage2a_rollout as rollout
from tests.test_composition_birth_stage2a_held import fixtures


class SyntheticTokenizer:
    eos_token_id = 1
    pad_token_id = 2
    eos_token = "<eos>"
    pad_token = "<pad>"
    all_special_ids = [1, 2, 3]
    padding_side = "right"

    def __init__(self):
        self.templates = []
        self.decodes = []
        self.template_mismatch = False
        self.roundtrip_mismatch = False
        self.decode_error_ids = None

    def encode(self, text, *, add_special_tokens, truncation):
        assert add_special_tokens is False and truncation is False
        special = {"<eos>": 1, "<pad>": 2, "<other>": 3}
        if text in special:
            return [special[text]]
        return [ord(character) + 10 for character in text]

    def decode(self, ids, *, skip_special_tokens, clean_up_tokenization_spaces):
        assert skip_special_tokens is False and clean_up_tokenization_spaces is False
        self.decodes.append(tuple(ids))
        if tuple(ids) == self.decode_error_ids:
            raise RuntimeError("synthetic decode failure")
        special = {token: f"<synthetic:{token}>" for token in range(10)}
        special.update({1: "<eos>", 2: "<pad>", 3: "<other>"})
        text = "".join(special[token] if token in special else chr(token - 10) for token in ids)
        return text + "!" if self.roundtrip_mismatch else text

    def apply_chat_template(self, messages, *, tokenize, add_generation_prompt,
                            truncation=False, padding=False):
        assert add_generation_prompt is True and truncation is False and padding is False
        assert all(set(message) == {"role", "content"} for message in messages)
        self.templates.append((deepcopy(messages), tokenize))
        text = "".join(f"<{message['role']}>\n{message['content']}\n" for message in messages)
        text += "<assistant>\n"
        if not tokenize:
            return text
        ids = self.encode(text, add_special_tokens=False, truncation=False)
        return ids + [99] if self.template_mismatch else ids


class SyntheticTensor:
    def __init__(self, rows):
        self.rows = deepcopy(rows)

    def tolist(self):
        return deepcopy(self.rows)


class SyntheticTorch:
    long = "synthetic-int64"

    def __init__(self):
        self.cpu_rng = 101
        self.cuda_rngs = [202, 303]
        self.seeds = []
        self.forks = []
        self.inference = False
        self.random = SimpleNamespace(fork_rng=self.fork_rng)

    @contextmanager
    def fork_rng(self, *, devices):
        self.forks.append(devices)
        assert devices is None
        cpu_rng, cuda_rngs = self.cpu_rng, self.cuda_rngs[:]
        try:
            yield
        finally:
            self.cpu_rng, self.cuda_rngs = cpu_rng, cuda_rngs

    def manual_seed(self, seed):
        self.seeds.append(seed)
        self.cpu_rng = seed
        self.cuda_rngs = [seed] * len(self.cuda_rngs)

    @contextmanager
    def inference_mode(self):
        previous = self.inference
        self.inference = True
        try:
            yield
        finally:
            self.inference = previous

    def tensor(self, rows, *, dtype, device):
        assert self.inference and dtype == self.long and device == "synthetic-device"
        return SyntheticTensor([list(row) for row in rows])

    def ones_like(self, tensor):
        return SyntheticTensor([[1] * len(row) for row in tensor.rows])


class SyntheticModel:
    def __init__(self, torch, continuation):
        self.torch = torch
        self.continuation = continuation
        self.training = True
        self.generation_config = SimpleNamespace(do_sample=True, stop_strings=["STOP"],
                                                forced_eos_token_id=9, bad_words_ids=[[20]])
        self.child = SimpleNamespace(training=False, generation_config=SimpleNamespace(top_k=50))
        self.parameters = [SimpleNamespace(requires_grad=True, grad=object()),
                           SimpleNamespace(requires_grad=False, grad=None)]
        self.received = []
        self.output = None
        self.generate_error = None
        self.eval_error = None
        self.output_override = None

    def modules(self):
        return iter((self, self.child))

    def eval(self):
        self.training = False
        self.child.training = False
        if self.eval_error is not None:
            raise self.eval_error
        return self

    def generate(self, **kwargs):
        assert set(kwargs) == {"input_ids", "attention_mask", "generation_config"}
        assert self.torch.inference and not self.training and not self.child.training
        config = kwargs["generation_config"]
        assert self.generation_config is config and self.child.generation_config is config
        self.received.append(kwargs)
        self.torch.cpu_rng += 17
        self.torch.cuda_rngs = [value + 19 for value in self.torch.cuda_rngs]
        if self.generate_error is not None:
            raise self.generate_error
        self.output = (self.output_override if self.output_override is not None else
                       SyntheticTensor([kwargs["input_ids"].rows[0] + list(self.continuation)]))
        return self.output


class ForwardedConfigModel:
    def __init__(self, model, *, shadow=False):
        self.base_model = model
        self.training = True
        self.shadow = shadow

    def __getattr__(self, name):
        return getattr(self.base_model, name)

    def modules(self):
        return iter((self, *self.base_model.modules()))

    def eval(self):
        self.training = False
        self.base_model.eval()
        return self

    def generate(self, **kwargs):
        self.base_model.generation_config = self.generation_config
        if self.shadow:
            self.generation_config = self.base_model.generation_config
        try:
            return self.base_model.generate(**kwargs)
        finally:
            self.generation_config.stop_strings = ["native mutation"]
            self.generation_config.eos_token_id = 199
            self.generation_config.max_new_tokens = 999


class ActorTests(unittest.TestCase):
    prefix = (held.Message("system", "public rules"), held.Message("user", "public task"),
              held.Message("assistant", "READ public"), held.Message("user", "public response"))

    def test_synthetic_tokenizer_total_decode_over_native_fixture_vocabulary(self):
        tokenizer = SyntheticTokenizer()
        decoded = []
        specials = {1: "<eos>", 2: "<pad>", 3: "<other>"}
        for token in range(256):
            with self.subTest(token=token):
                text = tokenizer.decode([token], skip_special_tokens=False,
                                        clean_up_tokenization_spaces=False)
                expected = (specials.get(token, f"<synthetic:{token}>") if token < 10
                            else chr(token - 10))
                self.assertEqual(text, expected)
                self.assertEqual(text.encode("utf-8").decode("utf-8"), text)
                decoded.append(text)
        self.assertEqual(tokenizer.decode(list(range(256)), skip_special_tokens=False,
                                          clean_up_tokenization_spaces=False), "".join(decoded))

    def bridge(self, continuation=None, **changes):
        tokenizer = SyntheticTokenizer()
        torch = SyntheticTorch()
        if continuation is None:
            continuation = [ord(character) + 10 for character in "STOP"] + [1]
        model = SyntheticModel(torch, continuation)
        options = dict(tokenizer=tokenizer, model=model, torch=torch, device="synthetic-device",
                       count_basis="SYNTHETIC_FIXTURE", generation_config_factory=SimpleNamespace)
        options.update(changes)
        actor = source.ReadoutActor(**options)
        return actor, tokenizer, model, torch

    def request(self, actor, **changes):
        request = rollout.DecodeRequest(self.prefix, 256, 2**64 - 1, actor.count_context(self.prefix))
        return replace(request, **changes)

    def test_import_and_construction_need_no_native_dependencies(self):
        with patch.dict(sys.modules, {"torch": None, "transformers": None}):
            importlib.reload(source)
            actor = source.ReadoutActor(tokenizer=object(), model=object(), torch=object(),
                                       device=object(), count_basis="SYNTHETIC_FIXTURE")
        self.assertEqual(actor.calls, [])
        self.assertFalse(actor.native_tokenizer_validated)
        self.assertFalse(any(source.SCIENCE_GATES.values()))

    def test_exact_low64_seeds_and_continuation_rng_and_modes_survive(self):
        slot = primitives.chain_slot("D1", 0, 0, 0)
        derived = primitives.decode_seed(b"synthetic-stage2a-actor", slot.panel_label, slot.global_ordinal)
        for seed in (0, 2**63 - 1, 2**63, 2**64 - 1, derived):
            actor, tokenizer, model, torch = self.bridge()
            original_configs = (model.generation_config, model.child.generation_config)
            roster = [(parameter, parameter.requires_grad, parameter.grad) for parameter in model.parameters]
            result = actor(self.request(actor, seed=seed))
            self.assertEqual(result, rollout.Generation("STOP", 5, 5, False, "stop"))
            self.assertEqual(torch.seeds, [seed])
            self.assertEqual(torch.forks, [None])
            self.assertEqual((torch.cpu_rng, torch.cuda_rngs), (101, [202, 303]))
            self.assertFalse(torch.inference)
            self.assertTrue(model.training)
            self.assertFalse(model.child.training)
            self.assertIs(model.generation_config, original_configs[0])
            self.assertIs(model.child.generation_config, original_configs[1])
            self.assertEqual([(parameter, parameter.requires_grad, parameter.grad)
                              for parameter in model.parameters], roster)
            self.assertEqual(actor.calls[0]["generated_ids"][-1], tokenizer.eos_token_id)

    def test_identical_public_template_and_strict_clean_generation(self):
        actor, tokenizer, model, _ = self.bridge()
        request = self.request(actor)
        actor(request)
        expected = [{"role": message.role, "content": message.content} for message in self.prefix]
        self.assertEqual(tokenizer.templates, [(expected, False), (expected, True)] * 2)
        kwargs = model.received[0]
        self.assertEqual(kwargs["input_ids"].rows, [list(actor.calls[0]["prompt_ids"])])
        self.assertEqual(kwargs["attention_mask"].rows, [[1] * request.context_tokens])
        config = vars(kwargs["generation_config"])
        for key, value in dict(do_sample=False, temperature=0.0, top_p=1.0, top_k=0,
                               num_beams=1, num_return_sequences=1, repetition_penalty=1.0,
                               max_new_tokens=256, stop_strings=None, forced_eos_token_id=None,
                               bad_words_ids=None, eos_token_id=1, pad_token_id=2,
                               min_new_tokens=0, min_length=0, max_time=None,
                               token_healing=False, return_dict_in_generate=False).items():
            self.assertEqual(config[key], value, key)

    def test_only_transport_terminal_eos_removed_no_strip_or_special_filter(self):
        content = [ord(character) + 10 for character in " \tSTOP\r\n\x00é  "] + [3, 2, 1]
        actor, _, _, _ = self.bridge(content + [1])
        result = actor(self.request(actor))
        self.assertEqual(result.raw, " \tSTOP\r\n\x00é  <other><pad><eos>")
        self.assertEqual(result.actual_tokens, len(content) + 1)
        self.assertEqual(actor.calls[0]["generated_ids"], tuple(content + [1]))
        self.assertEqual(actor.calls[0]["raw_bytes"], result.raw.encode("utf-8"))
        self.assertEqual(actor.calls[0]["decoded_with_terminal_eos"], result.raw + "<eos>")

    def test_eos_only_and_eos_at_exact_cap(self):
        for ids, raw in (([1], ""), ([90, 1], "P")):
            actor, _, _, _ = self.bridge(ids)
            result = actor(self.request(actor, max_new_tokens=len(ids)))
            self.assertEqual(result, rollout.Generation(raw, len(ids), len(ids), False, "stop"))

    def test_length_finish_never_repaired_or_retried(self):
        actor, _, model, _ = self.bridge([90] * 256)
        result = actor(self.request(actor))
        self.assertEqual(result.raw, "P" * 256)
        self.assertEqual((result.actual_tokens, result.finish_reason), (256, "length"))
        self.assertTrue(result.truncated)
        self.assertEqual(len(model.received), 1)

    def test_invalid_requests_are_retained_before_validation_without_generation(self):
        changes = [dict(seed=value) for value in (-1, 2**64, True, 1.5)]
        changes += [dict(max_new_tokens=value) for value in (0, 257, True)]
        changes += [dict(context_tokens=value) for value in (0, 16385, True, 16384)]
        changes += [dict(prefix=[held.Message("user", "public")]),
                    dict(prefix=(held.Message("tool", "private"),)),
                    dict(prefix=(SimpleNamespace(role="user", content="public", witness="private"),))]
        for change in changes:
            actor, _, model, torch = self.bridge()
            request = self.request(actor, **change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                actor(request)
            self.assertIs(actor.calls[0]["request"], request)
            self.assertIsNotNone(actor.calls[0]["error"])
            self.assertEqual(model.received, [])
            self.assertEqual(torch.seeds, [])
        actor, _, _, _ = self.bridge()
        with self.assertRaisesRegex(ValueError, "decode_request_required"):
            actor({"prefix": self.prefix, "witness": "private"})
        with self.assertRaisesRegex(ValueError, "explicit_non_native_count_basis"):
            self.bridge(count_basis="NATIVE_CERTIFIED")

    def test_context_count_template_and_roundtrip_disagreements_fail_closed(self):
        for mismatch in ("context", "template", "roundtrip"):
            actor, tokenizer, model, _ = self.bridge()
            request = self.request(actor)
            if mismatch == "context":
                request = replace(request, context_tokens=request.context_tokens + 1)
            elif mismatch == "template":
                tokenizer.template_mismatch = True
            else:
                tokenizer.roundtrip_mismatch = True
            with self.subTest(mismatch=mismatch), self.assertRaises(ValueError):
                actor(request)
            self.assertEqual(model.received, [])
            if mismatch != "context":
                with self.assertRaises(ValueError):
                    actor.count_context(self.prefix)

    def test_context_exact_boundary_and_overflow_without_truncation(self):
        actor, _, model, _ = self.bridge([1])
        empty = (held.Message("user", ""),)
        overhead = actor.count_context(empty)
        prefix = (held.Message("user", "x" * (16383 - overhead)),)
        self.assertEqual(actor.count_context(prefix), 16383)
        actor(rollout.DecodeRequest(prefix, 1, 0, 16383))
        self.assertEqual(len(model.received[0]["input_ids"].rows[0]), 16383)
        overflow = (held.Message("user", "x" * (16385 - overhead)),)
        with self.assertRaisesRegex(ValueError, "over_context"):
            actor.count_context(overflow)

    def test_native_object_retained_when_tensor_conversion_fails(self):
        actor, _, model, torch = self.bridge()
        error = RuntimeError("synthetic device-to-host failure")
        model.output_override = SimpleNamespace(tolist=lambda: self.raise_error(error))
        with self.assertRaises(RuntimeError) as caught:
            actor(self.request(actor))
        self.assertIs(caught.exception, error)
        self.assertIs(actor.calls[0]["native_output"], model.output)
        self.assertIs(actor.calls[0]["error"], error)
        self.assertIsNone(actor.calls[0]["native_sequences"])
        self.assertEqual((torch.cpu_rng, torch.cuda_rngs), (101, [202, 303]))
        self.assertTrue(model.training)

    @staticmethod
    def raise_error(error):
        raise error

    def test_decode_failure_keeps_native_output_ids_and_exception(self):
        actor, tokenizer, model, _ = self.bridge()
        request = self.request(actor)
        tokenizer.decode_error_ids = tuple(model.continuation[:-1])
        with self.assertRaisesRegex(RuntimeError, "decode failure"):
            actor(request)
        receipt = actor.calls[0]
        self.assertIs(receipt["native_output"], model.output)
        self.assertEqual(receipt["native_sequences"], model.output.tolist())
        self.assertEqual(receipt["generated_ids"], tuple(model.continuation))
        self.assertIsNotNone(receipt["error"])
        with self.assertRaisesRegex(ValueError, "actor_failed_no_retry"):
            actor(request)
        self.assertEqual(len(model.received), 1)
        self.assertEqual(len(actor.calls), 2)

    def test_malformed_native_results_keep_full_prevalidation_custody(self):
        for suffix in ([], [90], [90] * 257, [True], [-1]):
            actor, _, model, _ = self.bridge(suffix)
            with self.subTest(suffix=suffix[:3]), self.assertRaises(ValueError):
                actor(self.request(actor))
            receipt = actor.calls[0]
            self.assertIs(receipt["native_output"], model.output)
            self.assertEqual(receipt["native_sequences"], model.output.tolist())
            if suffix == [90]:
                self.assertEqual(receipt["raw_bytes"], b"P")
        for rows in ([], [[1], [2]], [[False]], [[999, 1]]):
            actor, _, model, _ = self.bridge()
            model.output_override = SyntheticTensor(rows)
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                actor(self.request(actor))
            self.assertEqual(actor.calls[0]["native_sequences"], rows)
            self.assertIs(actor.calls[0]["native_output"], model.output)

    def test_backend_and_eval_failures_preserve_modes_configs_and_rng(self):
        for stage in ("generate_error", "eval_error"):
            actor, _, model, torch = self.bridge()
            original = model.generation_config
            error = RuntimeError("synthetic native failure")
            error.native_output = {"partial_ids": [101, 102], "text": "unfinished"}
            setattr(model, stage, error)
            with self.subTest(stage=stage), self.assertRaises(RuntimeError) as caught:
                actor(self.request(actor))
            self.assertIs(caught.exception, error)
            self.assertIs(actor.calls[0]["error"].native_output, error.native_output)
            self.assertIs(model.generation_config, original)
            self.assertTrue(model.training)
            self.assertFalse(model.child.training)
            self.assertEqual((torch.cpu_rng, torch.cuda_rngs), (101, [202, 303]))

    def test_forwarded_config_owners_and_absence_restored_after_mutation_and_failure(self):
        for shadow in (False, True):
            for failure in (None, "generate", "decode", "length"):
                actor, tokenizer, base, torch = self.bridge()
                tuner = ForwardedConfigModel(base, shadow=shadow)
                wrapper = ForwardedConfigModel(tuner, shadow=shadow)
                actor.model = wrapper
                request = self.request(actor)
                original = base.generation_config
                original_values = deepcopy(vars(original))
                child_config = base.child.generation_config
                if failure == "generate":
                    base.generate_error = RuntimeError("forwarded native failure")
                elif failure == "decode":
                    tokenizer.decode_error_ids = tuple(base.continuation[:-1])
                elif failure == "length":
                    base.continuation = [90] * 257
                with self.subTest(shadow=shadow, failure=failure):
                    if failure is not None:
                        with self.assertRaises((RuntimeError, ValueError)):
                            actor(request)
                    else:
                        result = actor(request)
                        self.assertEqual(result, rollout.Generation("STOP", 5, 5, False, "stop"))
                    self.assertNotIn("generation_config", vars(wrapper))
                    self.assertNotIn("generation_config", vars(tuner))
                    self.assertIs(wrapper.generation_config, original)
                    self.assertIs(base.generation_config, original)
                    self.assertIs(base.child.generation_config, child_config)
                    self.assertEqual(vars(original), original_values)
                    self.assertEqual(actor.calls[0]["generation_config"]["eos_token_id"], 1)
                    self.assertEqual(actor.calls[0]["generation_config"]["max_new_tokens"], 256)
                    self.assertIsNone(actor.calls[0]["generation_config"]["stop_strings"])
                    self.assertTrue(wrapper.training)
                    self.assertTrue(tuner.training)
                    self.assertTrue(base.training)
                    self.assertFalse(base.child.training)
                    self.assertEqual((torch.cpu_rng, torch.cuda_rngs), (101, [202, 303]))
                    if failure != "generate":
                        self.assertIs(actor.calls[0]["native_output"], base.output)

    def test_rollout_consumes_bridge_without_hidden_world_input(self):
        tokens = fixtures("dose_chain")
        world = held.build_chain_world(world="h00", role_tokens=tokens["h00"])
        actor, tokenizer, _, _ = self.bridge()
        result = rollout.run_chain(world, "m0", actor=actor, count_context=actor.count_context,
                                   counter_provenance=actor.count_basis,
                                   master=b"synthetic-stage2a-actor")
        self.assertEqual(len(result.attempts), 1)
        self.assertEqual(result.attempts[0].capture.raw_bytes, b"STOP")
        self.assertEqual(result.terminal_reason, "premature_stop")
        expected = [{"role": message.role, "content": message.content}
                    for message in world.public_view("m0").prefix]
        self.assertTrue(all(messages == expected for messages, _ in tokenizer.templates))


@unittest.skipUnless(all(importlib.util.find_spec(name) is not None
                         for name in ("torch", "transformers", "peft")),
                     "optional existing torch+transformers+peft required; never install")
class NativeCPUCompatibilityTests(unittest.TestCase):
    """Optional engineering compatibility only; synthetic tokenizer, no weights IO.

    Run explicitly in a caller-bound CUDA-hidden process with OMP/MKL pins.
    The thread receipt is printed before constructing either tiny random model.
    Compatibility target: torch 2.13.0, transformers 5.5.3, PEFT 0.20.0,
    tokenizers 0.22.2 (caller-reported node2 metadata, not locally verified).
    This class never sets global threads or claims native-tokenizer, learning,
    checkpoint-continuation, or Stage2A scientific qualification.
    """

    FIXTURE_SEED = 20260913

    @classmethod
    def setUpClass(cls):
        if os.environ.get("CUDA_VISIBLE_DEVICES") not in ("", "-1"):
            raise unittest.SkipTest("explicit CUDA-hidden CPU process required")
        if any(os.environ.get(name) != "1" for name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS")):
            raise unittest.SkipTest("prospective OMP_NUM_THREADS=1 and MKL_NUM_THREADS=1 required")
        import torch
        import transformers
        import peft
        import tokenizers
        cls.torch = torch
        cls.transformers = transformers
        cls.peft = peft
        cls.thread_binding = dict(
            OMP_NUM_THREADS=os.environ["OMP_NUM_THREADS"], MKL_NUM_THREADS=os.environ["MKL_NUM_THREADS"],
            CUDA_VISIBLE_DEVICES=os.environ["CUDA_VISIBLE_DEVICES"],
            torch_num_threads=torch.get_num_threads(), torch_num_interop_threads=torch.get_num_interop_threads(),
            torch_version=torch.__version__, transformers_version=transformers.__version__,
            peft_version=peft.__version__, tokenizers_version=tokenizers.__version__,
            status="ENGINEERING_BACKEND_ONLY",
            tokenizer="SYNTHETIC_FIXTURE", device="cpu", dtype="float32",
            fixture_seed=cls.FIXTURE_SEED,
        )
        print("stage2a_native_cpu_prospective_binding=" + json.dumps(cls.thread_binding, sort_keys=True), flush=True)
        if torch.get_num_threads() != 1:
            raise AssertionError("prospectively bound single-thread CPU run required; no thread repair")

    def check_backend(self, *, with_peft):
        torch = self.torch
        torch.manual_seed(self.FIXTURE_SEED)
        config = self.transformers.GPT2Config(vocab_size=256, n_positions=256, n_ctx=256,
                                             n_embd=16, n_layer=1, n_head=2,
                                             bos_token_id=0, eos_token_id=1, pad_token_id=2,
                                             attn_implementation="eager")
        model = self.transformers.GPT2LMHeadModel(config).to(device="cpu", dtype=torch.float32)
        if with_peft:
            lora = self.peft.LoraConfig(r=8, lora_alpha=16, lora_dropout=0.05,
                                       target_modules=["c_attn", "c_proj"], fan_in_fan_out=True,
                                       bias="none", task_type="CAUSAL_LM")
            model = self.peft.get_peft_model(model, lora)
            self.assertNotIn("generation_config", vars(model))
        model.train()
        next(module for module in model.modules() if isinstance(module, torch.nn.Dropout)).eval()
        first_trainable = next(parameter for parameter in model.parameters() if parameter.requires_grad)
        first_trainable.grad = torch.ones_like(first_trainable)
        named = tuple(model.named_parameters())
        self.assertTrue(all(parameter.device.type == "cpu" for _, parameter in named))
        parameters = tuple((name, parameter, parameter.requires_grad, parameter.detach().clone(),
                            parameter.grad, None if parameter.grad is None else parameter.grad.clone())
                           for name, parameter in named)
        modes = tuple((module, module.training) for module in model.modules())
        absent = object()
        configs = tuple((module, vars(module).get("generation_config", absent)) for module, _ in modes)
        config_values = tuple(deepcopy(vars(original)) if original is not absent else None
                              for _, original in configs)
        public_config = model.generation_config
        rng_before = torch.get_rng_state().clone()
        actor = source.ReadoutActor(tokenizer=SyntheticTokenizer(), model=model, torch=torch,
                                   device="cpu", count_basis="SYNTHETIC_FIXTURE")
        prefix = (held.Message("user", "tiny engineering fixture"),)
        context = actor.count_context(prefix)
        results = []
        for seed in (2**63, 2**64 - 1):
            with patch.object(torch, "manual_seed", wraps=torch.manual_seed) as manual_seed:
                result = actor(rollout.DecodeRequest(prefix, 4, seed, context))
            manual_seed.assert_called_once_with(seed)
            receipt = actor.calls[-1]
            self.assertIsInstance(receipt["native_output"], torch.Tensor)
            generated = tuple(receipt["native_output"][0, context:].tolist())
            self.assertEqual(receipt["generated_ids"], generated)
            self.assertTrue(1 <= len(generated) <= 4)
            ended = generated[-1] == 1
            expected_text = actor.tokenizer.decode(list(generated[:-1] if ended else generated),
                                                  skip_special_tokens=False,
                                                  clean_up_tokenization_spaces=False)
            self.assertEqual(result, rollout.Generation(expected_text, len(generated), len(generated),
                                                        not ended, "stop" if ended else "length"))
            self.assertTrue(torch.equal(torch.get_rng_state(), rng_before))
            self.assertIs(model.generation_config, public_config)
            self.assertFalse(torch.is_inference_mode_enabled())
            self.assertEqual(tuple(model.named_parameters()), named)
            for module, training in modes:
                self.assertEqual(module.training, training)
            for (module, original), expected in zip(configs, config_values):
                if original is absent:
                    self.assertNotIn("generation_config", vars(module))
                else:
                    self.assertIs(module.generation_config, original)
                    self.assertEqual(vars(original), expected)
            for name, parameter, requires_grad, value, gradient, grad_value in parameters:
                self.assertEqual(parameter.requires_grad, requires_grad, name)
                self.assertTrue(torch.equal(parameter.detach(), value), name)
                self.assertIs(parameter.grad, gradient)
                if gradient is not None:
                    self.assertTrue(torch.equal(gradient, grad_value), name)
            self.assertEqual(torch.get_num_threads(), self.thread_binding["torch_num_threads"])
            self.assertEqual(torch.get_num_interop_threads(), self.thread_binding["torch_num_interop_threads"])
            results.append(result)
        self.assertEqual(results[0], results[1])

    def test_tiny_random_baseline_cpu_generate(self):
        self.check_backend(with_peft=False)

    def test_tiny_random_rank8_peft_cpu_generate(self):
        self.check_backend(with_peft=True)


if __name__ == "__main__":
    unittest.main()
