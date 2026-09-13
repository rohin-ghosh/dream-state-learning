"""CPU-only injected actors and tiny synthetic identity files; no native loads."""

import contextlib
import copy
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from gpu import astra_pcfl_native_actor as actor_api


class Clock:
    def __init__(self):
        self.now = 10.0

    def __call__(self):
        return self.now


class Tokenizer:
    chat_template = "SYNTHETIC_QWEN_TEMPLATE"

    def __init__(self, model):
        self.name_or_path = str(model)
        self.mismatch = False

    def encode(self, text, add_special_tokens=False):
        assert add_special_tokens is False
        return [ord(character) for character in text]

    def decode(self, ids, skip_special_tokens=True):
        assert skip_special_tokens is True
        return "".join(chr(token) for token in ids)

    def apply_chat_template(self, messages, tokenize, add_generation_prompt):
        assert add_generation_prompt is True
        prompt = "".join("<|im_start|>" + message["role"] + "\n" + message["content"] + "<|im_end|>\n" for message in messages)
        prompt += "<|im_start|>assistant\n"
        if tokenize:
            return self.encode(prompt) + ([999] if self.mismatch else [])
        return prompt


class Session:
    def __init__(self, model, clock):
        self.tokenizer = Tokenizer(model)
        self.clock = clock
        self.calls = []
        self.closed = 0
        self.text = "ROUTE N_TEST N_GOAL P_PORT"
        self.duration = 0.25
        self.mutate = lambda raw: raw

    def generate(self, prompt, sampling):
        self.calls.append((prompt, copy.deepcopy(sampling)))
        self.clock.now += self.duration
        raw = {"text": self.text, "output_token_ids": self.tokenizer.encode(self.text),
               "prompt_token_ids": self.tokenizer.encode(prompt), "finish_reason": "stop", "stop_reason": None}
        return self.mutate(raw)

    def close(self):
        self.closed += 1
        return {"shutdown_method_available": True, "shutdown_returned": True}


class ActorTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="pcfl_actor_test_")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.model = self.root / "model"
        self.model.mkdir()
        names = [".gitattributes", "LICENSE", "README.md", "config.json", "generation_config.json",
                 "merges.txt", "model-00001-of-00004.safetensors", "model-00002-of-00004.safetensors",
                 "model-00003-of-00004.safetensors", "model-00004-of-00004.safetensors",
                 "model.safetensors.index.json", "tokenizer.json", "tokenizer_config.json", "vocab.json"]
        files = {}
        for name in names:
            payload = b'{"model_type":"qwen2"}' if name == "config.json" else ("TEST_ONLY/" + name).encode()
            (self.model / name).write_bytes(payload)
            files[name] = {"sha256": hashlib.sha256(payload).hexdigest(), "size": len(payload), "public_match": "LFS_SHA256"}
        self.receipt = self.root / "public_receipt.json"
        self.receipt.write_bytes(actor_api.canonical({"repository": actor_api.MODEL_NAME, "revision": actor_api.REVISION,
            "status": "PUBLIC_REVISION_FILES_MATCHED_PROSPECTIVE_BINDING", "model": str(self.model),
            "file_count": 14, "files": files}))
        self.clock = Clock()
        self.session = Session(self.model, self.clock)
        self.loader = Mock(return_value=self.session)
        self.environment = {"python": "/SYNTHETIC/python", "version": "SYNTHETIC", "packages": {name: "SYNTHETIC" for name in actor_api.PACKAGES}}
        source = Path(actor_api.__file__).resolve()
        self.config = {"schema": actor_api.SCHEMA, "model_path": str(self.model),
            "model_binding": {"path": str(self.receipt), "sha256": hashlib.sha256(self.receipt.read_bytes()).hexdigest()},
            "source_files": {str(source): hashlib.sha256(source.read_bytes()).hexdigest()},
            "tokenizer_files": {name: files[name]["sha256"] for name in actor_api.TOKENIZER_FILES},
            "chat_template_sha256": actor_api.text_hash(Tokenizer.chat_template),
            "tokenizer_probe": {"text": "probe", "token_ids": [ord(character) for character in "probe"]},
            "environment": self.environment, "gpu_uuid": "GPU-CPU-TEST", "engine": actor_api.ENGINE.copy(),
            "output_dir": str(self.root / "output"), "deadline": 100.0, "device_seconds_cap": 80,
            "max_input_tokens": 16000, "max_output_tokens": 2048, "max_calls": 1952}
        self.request = {"id": "task/0/actor/0", "messages": [{"role": "system", "content": "Use only public records."},
                        {"role": "user", "content": "Commit one ROUTE."}], "seed": 71, "mount": "C0"}
        self.limits = {"output_tokens": 100, "returned_tokens": 4096, "remaining_reads": 12,
                       "deadline": 90, "device_seconds": 60}

    def actor(self):
        result = actor_api.NativeActor(self.config, loader=self.loader,
                                       environment_reader=lambda: copy.deepcopy(self.environment), clock=self.clock)
        self.addCleanup(result.close)
        return result

    def read(self, name):
        return json.loads((Path(self.config["output_dir"]) / name).read_bytes())

    def test_constructor_and_unused_close_are_lazy(self):
        actor = self.actor()
        self.loader.assert_not_called()
        self.assertFalse(Path(self.config["output_dir"]).exists())
        self.assertFalse(actor.scripted)
        receipt = actor.close()
        self.assertIsNone(receipt["gpu_vacant"])
        self.assertIsNone(receipt["owned_group_released"])
        self.assertFalse(Path(self.config["output_dir"]).exists())
        with self.assertRaises(actor_api.ActorError):
            actor.generate(self.request, self.limits)

    def test_real_actor_public_api_captures_exact_tokens_and_bytes(self):
        actor = self.actor()
        original = copy.deepcopy(self.request)
        response = actor.generate(self.request, self.limits)
        self.assertEqual(self.request, original)
        self.assertEqual(set(response), {"request_sha256", "text", "prompt_tokens", "output_tokens", "device_seconds"})
        self.assertEqual(response["request_sha256"], actor_api.digest(original))
        self.assertEqual(response["output_tokens"], len(self.session.text))
        self.assertEqual(response["prompt_tokens"], len(self.session.calls[0][0]))
        self.assertEqual(response["device_seconds"], 0.25)
        self.assertEqual(self.session.calls[0][1], {**actor_api.SAMPLING, "seed": 71, "max_tokens": 100})
        self.assertEqual(bytes.fromhex(self.read("call_0000.response.json")["raw_hex"]).decode(), self.session.text)
        self.assertIsNone(self.read("call_0000.raw.json")["lora_request"])
        self.assertEqual(self.read("identity.json")["kind"], "INJECTED_CPU_TEST")
        response["text"] = "changed caller copy"
        self.assertEqual(self.read("call_0000.response.json")["response"]["text"], self.session.text)
        receipt = actor.close()
        self.assertTrue(receipt["outer_release_required"])
        self.assertIsNone(receipt["gpu_vacant"])
        self.assertEqual(actor.close(), receipt)
        self.assertEqual(self.session.closed, 1)

    def test_private_and_oracle_keys_rejected_before_load(self):
        actor = self.actor()
        for key in ("oracle", "scorer", "private", "cell", "adapter"):
            request = copy.deepcopy(self.request)
            request[key] = "secret"
            with self.subTest(key=key), self.assertRaisesRegex(actor_api.ActorError, "public request fields"):
                actor.generate(request, self.limits)
        request = copy.deepcopy(self.request)
        request["messages"][1]["oracle"] = "not public metadata"
        with self.assertRaises(actor_api.ActorError):
            actor.generate(request, self.limits)
        self.loader.assert_not_called()
        self.assertFalse(Path(self.config["output_dir"]).exists())

    def test_non_C0_mount_and_extra_system_rejected(self):
        actor = self.actor()
        self.request["mount"] = "S1_AUTH"
        with self.assertRaisesRegex(actor_api.ActorError, "only C0"):
            actor.generate(self.request, self.limits)
        self.request["mount"] = "C0"
        self.request["messages"][1]["role"] = "system"
        with self.assertRaises(actor_api.ActorError):
            actor.generate(self.request, self.limits)
        self.loader.assert_not_called()

    def test_duplicate_id_fails_without_rewrite_or_retry(self):
        actor = self.actor()
        actor.generate(self.request, self.limits)
        before = (Path(self.config["output_dir"]) / "call_0000.raw.json").read_bytes()
        with self.assertRaisesRegex(actor_api.ActorError, "already consumed"):
            actor.generate(self.request, self.limits)
        self.assertEqual(len(self.session.calls), 1)
        self.assertEqual((Path(self.config["output_dir"]) / "call_0000.raw.json").read_bytes(), before)

    def test_output_root_is_write_once_including_empty_directory(self):
        Path(self.config["output_dir"]).mkdir()
        actor = self.actor()
        with self.assertRaisesRegex(actor_api.ActorError, "must be fresh"):
            actor.generate(self.request, self.limits)
        self.loader.assert_not_called()
        self.assertEqual(list(Path(self.config["output_dir"]).iterdir()), [])

    def test_input_and_output_caps_no_silent_truncation(self):
        actor = self.actor()
        self.limits["input_tokens"] = 1
        with self.assertRaisesRegex(actor_api.ActorError, "input-token cap"):
            actor.generate(self.request, self.limits)
        self.assertEqual(self.session.calls, [])
        self.assertEqual(self.read("call_0000.error.json")["status"], "FAILED_NO_RETRY")

    def test_actual_output_over_cap_retains_raw_and_poisoned_actor(self):
        actor = self.actor()
        self.limits["output_tokens"] = 1
        with self.assertRaisesRegex(actor_api.ActorError, "output token cap"):
            actor.generate(self.request, self.limits)
        self.assertEqual(self.read("call_0000.raw.json")["raw"]["text"], self.session.text)
        self.request["id"] = "another"
        with self.assertRaisesRegex(actor_api.ActorError, "failed; no retry"):
            actor.generate(self.request, self.limits)
        self.assertEqual(len(self.session.calls), 1)

    def test_invalid_cardinality_captures_are_preserved(self):
        captures = [{"prompt_token_ids": [1], "outputs": [{"text": "first"}, {"text": "second"}]}]
        self.session.generate = Mock(side_effect=actor_api._NativeOutputError(captures))
        actor = self.actor()
        with self.assertRaisesRegex(actor_api.ActorError, "cardinality"):
            actor.generate(self.request, self.limits)
        self.assertEqual(self.read("call_0000.raw.json")["invalid_cardinality_captures"], captures)
        self.assertEqual(self.session.generate.call_count, 1)

    def test_template_encoding_mismatch_stops_before_generation(self):
        self.session.tokenizer.mismatch = True
        actor = self.actor()
        with self.assertRaisesRegex(actor_api.ActorError, "template/encode"):
            actor.generate(self.request, self.limits)
        self.assertEqual(self.session.calls, [])

    def test_actual_prompt_token_mismatch_rejected(self):
        self.session.mutate = lambda raw: {**raw, "prompt_token_ids": [1]}
        actor = self.actor()
        with self.assertRaisesRegex(actor_api.ActorError, "actual prompt IDs"):
            actor.generate(self.request, self.limits)

    def test_output_decoding_mismatch_rejected(self):
        self.session.mutate = lambda raw: {**raw, "text": "fabricated text"}
        actor = self.actor()
        with self.assertRaisesRegex(actor_api.ActorError, "text/token decode"):
            actor.generate(self.request, self.limits)

    def test_default_decode_hook_rejects_lf_prefix_even_with_stop_sampling(self):
        prefix = "THINK unchanged"
        self.session.text = prefix + "\nROUTE suffix"
        self.session.mutate = lambda raw: {**raw, "text": prefix, "stop_reason": "\n"}
        actor = self.actor()
        sampling = {**actor_api.SAMPLING, "seed": self.request["seed"], "max_tokens": 100,
                    "stop": ["\n"], "include_stop_str_in_output": False}
        with patch.object(actor, "_sampling", return_value=sampling):
            with self.assertRaisesRegex(actor_api.ActorError, "text/token decode"):
                actor.generate(self.request, self.limits)
        raw = self.read("call_0000.raw.json")["raw"]
        self.assertEqual(raw["text"], prefix)
        self.assertEqual(self.session.tokenizer.decode(raw["output_token_ids"]), self.session.text)
        self.assertFalse((Path(self.config["output_dir"]) / "call_0000.response.json").exists())

    def test_empty_output_and_unicode_are_exact_not_normalized(self):
        self.session.text = "é\n"
        actor = self.actor()
        response = actor.generate(self.request, self.limits)
        self.assertEqual(response["text"], "é\n")
        self.assertEqual(response["output_tokens"], 2)
        self.session.text = ""
        self.request["id"] = "empty"
        response = actor.generate(self.request, self.limits)
        self.assertEqual(response["text"], "")
        self.assertEqual(response["output_tokens"], 0)

    def test_count_tokens_is_exact_and_model_loads_only_once(self):
        actor = self.actor()
        self.assertEqual(actor.count_tokens("abc\n"), 4)
        self.assertEqual(actor.count_tokens(""), 0)
        actor.generate(self.request, self.limits)
        self.assertEqual(self.loader.call_count, 1)
        self.assertEqual(self.read("count_0000.json")["token_ids"], [97, 98, 99, 10])

    def test_model_bytes_drift_block_loader(self):
        (self.model / "model-00001-of-00004.safetensors").write_bytes(b"changed")
        actor = self.actor()
        with self.assertRaisesRegex(actor_api.ActorError, "model file"):
            actor.generate(self.request, self.limits)
        self.loader.assert_not_called()
        self.assertEqual(self.read("call_0000.request.json")["request"], self.request)

    def test_extra_adapter_file_blocked(self):
        (self.model / "adapter_config.json").write_text("{}")
        actor = self.actor()
        with self.assertRaisesRegex(actor_api.ActorError, "inventory"):
            actor.generate(self.request, self.limits)
        self.loader.assert_not_called()

    def test_source_receipt_environment_and_tokenizer_identity(self):
        for kind in ("source", "receipt", "environment", "template", "tokenizer"):
            with self.subTest(kind=kind):
                config = copy.deepcopy(self.config)
                config["output_dir"] = str(self.root / kind)
                session = Session(self.model, self.clock)
                loader = Mock(return_value=session)
                reader = lambda: self.environment
                if kind == "source":
                    config["source_files"][str(Path(actor_api.__file__).resolve())] = "0" * 64
                elif kind == "receipt":
                    config["model_binding"]["sha256"] = "0" * 64
                elif kind == "environment":
                    reader = lambda: {"wrong": "environment"}
                elif kind == "template":
                    session.tokenizer.chat_template = "wrong"
                else:
                    config["tokenizer_probe"]["token_ids"] = [1]
                actor = actor_api.NativeActor(config, loader=loader, environment_reader=reader, clock=self.clock)
                with self.assertRaises(actor_api.ActorError):
                    actor.generate(self.request, self.limits)
                actor.close()
                self.assertEqual(session.calls, [])

    def test_file_change_after_load_detected_without_rehashing_weights(self):
        actor = self.actor()
        actor.start()
        with patch.object(actor, "_hash_file", side_effect=AssertionError("no repeat hashing")):
            actor.generate(self.request, self.limits)
        (self.model / "vocab.json").write_bytes(b"changed")
        self.request["id"] = "next"
        with self.assertRaisesRegex(actor_api.ActorError, "local file changed"):
            actor.generate(self.request, self.limits)
        self.assertEqual(len(self.session.calls), 1)

    def test_deadline_blocks_before_load_and_after_late_return(self):
        actor = self.actor()
        self.limits["deadline"] = self.clock.now
        with self.assertRaisesRegex(actor_api.ActorError, "deadline"):
            actor.generate(self.request, self.limits)
        self.loader.assert_not_called()

    def test_late_native_return_is_recorded_not_retried(self):
        actor = self.actor()
        self.session.duration = 2
        self.limits["device_seconds"] = 1
        with self.assertRaisesRegex(actor_api.ActorError, "deadline"):
            actor.generate(self.request, self.limits)
        self.assertEqual(len(self.session.calls), 1)
        self.assertTrue((Path(self.config["output_dir"]) / "call_0000.raw.json").exists())

    def test_elapsed_load_budget_and_max_calls(self):
        self.config["max_calls"] = 1
        actor = self.actor()
        actor.generate(self.request, self.limits)
        self.request["id"] = "second"
        with self.assertRaisesRegex(actor_api.ActorError, "call cap"):
            actor.generate(self.request, self.limits)
        self.assertEqual(len(self.session.calls), 1)

    def test_load_timeout_stops_before_generation_and_closes_session(self):
        def load(config):
            self.clock.now += 2
            return self.session
        self.loader.side_effect = load
        actor = self.actor()
        self.limits["device_seconds"] = 1
        with self.assertRaisesRegex(actor_api.ActorError, "deadline"):
            actor.generate(self.request, self.limits)
        self.assertEqual(self.session.calls, [])
        actor.close()
        self.assertEqual(self.session.closed, 1)

    def test_shutdown_error_never_becomes_gpu_release(self):
        actor = self.actor()
        actor.start()
        self.session.close = Mock(side_effect=RuntimeError("synthetic shutdown failure"))
        receipt = actor.close()
        self.assertEqual(receipt["error_type"], "RuntimeError")
        self.assertIsNone(receipt["gpu_vacant"])
        self.assertIsNone(receipt["owned_group_released"])

    def test_concurrency_rejected_and_no_loader(self):
        actor = self.actor()
        actor._lock.acquire()
        try:
            with self.assertRaisesRegex(actor_api.ActorError, "concurrent"):
                actor.generate(self.request, self.limits)
        finally:
            actor._lock.release()
        self.loader.assert_not_called()

    def test_output_root_symlink_rejected_before_loader(self):
        target = self.root / "other"
        target.mkdir()
        Path(self.config["output_dir"]).symlink_to(target, target_is_directory=True)
        actor = self.actor()
        with self.assertRaisesRegex(actor_api.ActorError, "fresh"):
            actor.start()
        self.loader.assert_not_called()
        self.assertEqual(list(target.iterdir()), [])

    def test_engine_lora_or_remote_code_cannot_be_enabled(self):
        for key in ("enable_lora", "trust_remote_code"):
            with self.subTest(key=key):
                config = copy.deepcopy(self.config)
                config["engine"][key] = True
                with self.assertRaisesRegex(actor_api.ActorError, "C0 engine"):
                    actor_api.NativeActor(config, loader=self.loader)
        self.loader.assert_not_called()

    def test_context_limit_is_checked_before_native_generation(self):
        actor = self.actor()
        self.request["messages"][1]["content"] = "a" * 15800
        self.limits["output_tokens"] = 1000
        with self.assertRaisesRegex(actor_api.ActorError, "context window"):
            actor.generate(self.request, self.limits)
        self.assertEqual(self.session.calls, [])

    def test_input_config_is_detached_and_internal_drift_rejected(self):
        actor = self.actor()
        self.config["engine"]["enable_lora"] = True
        actor.start()
        self.assertFalse(self.loader.call_args.args[0]["engine"]["enable_lora"])
        actor._config["max_calls"] = 7
        with self.assertRaisesRegex(actor_api.ActorError, "config drift"):
            actor.generate(self.request, self.limits)

    def test_cold_start_and_generation_timing_are_distinct(self):
        def load(config):
            self.clock.now += 2
            return self.session
        self.loader.side_effect = load
        actor = self.actor()
        response = actor.generate(self.request, self.limits)
        self.assertEqual(response["device_seconds"], 2.25)
        load_receipt = self.read("load.json")
        raw_receipt = self.read("call_0000.raw.json")
        self.assertEqual(load_receipt["ready_at"] - load_receipt["model_load_started"], 2)
        self.assertEqual(raw_receipt["generation_ended"] - raw_receipt["generation_started"], 0.25)

    def test_nan_boolean_or_oversized_limits_never_load(self):
        actor = self.actor()
        for key, value in (("device_seconds", float("nan")), ("output_tokens", True),
                           ("output_tokens", 2049), ("remaining_reads", 13)):
            limits = {**self.limits, key: value}
            with self.subTest(key=key, value=value), self.assertRaises(actor_api.ActorError):
                actor.generate(self.request, limits)
        self.loader.assert_not_called()

    def test_native_loader_pattern_with_fake_modules_only(self):
        tokenizer = self.session.tokenizer
        fake_output = SimpleNamespace(text="OK", token_ids=[79, 75], finish_reason="stop", stop_reason=None)
        llm = Mock()
        llm.get_tokenizer.return_value = tokenizer
        llm.generate.return_value = [SimpleNamespace(outputs=[fake_output], prompt_token_ids=[65])]
        llm_constructor = Mock(return_value=llm)
        sampling_constructor = Mock(side_effect=lambda **params: params)
        modules = {"vllm": SimpleNamespace(LLM=llm_constructor, SamplingParams=sampling_constructor),
                   "torch": SimpleNamespace(inference_mode=contextlib.nullcontext)}
        offline = {key: "1" for key in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_HUB_DISABLE_TELEMETRY", "VLLM_NO_USAGE_STATS")}
        offline["CUDA_VISIBLE_DEVICES"] = self.config["gpu_uuid"]
        with patch.dict("sys.modules", modules), patch.dict(os.environ, offline):
            session = actor_api._native_loader(self.config)
            raw = session.generate("A", {**actor_api.SAMPLING, "seed": 9, "max_tokens": 7})
            session.close()
        self.assertEqual(raw["text"], "OK")
        self.assertFalse(llm_constructor.call_args.kwargs["enable_lora"])
        self.assertIsNone(llm.generate.call_args.kwargs["lora_request"])
        self.assertFalse(llm_constructor.call_args.kwargs["trust_remote_code"])
        self.assertEqual(sampling_constructor.call_args.kwargs["max_tokens"], 7)

    def test_native_loader_without_offline_configuration_fails_before_import(self):
        with patch.dict(os.environ, {}, clear=True), self.assertRaisesRegex(actor_api.ActorError, "offline"):
            actor_api._native_loader(self.config)

    def test_native_loader_converts_structured_regex_without_mutating_json(self):
        @dataclass
        class Structured:
            regex: str

        fake_output = SimpleNamespace(text="wrong content\n", token_ids=[1], finish_reason="stop", stop_reason=None)
        llm = Mock()
        llm.generate.return_value = [SimpleNamespace(outputs=[fake_output], prompt_token_ids=[65])]
        sampling_constructor = Mock(side_effect=lambda **params: params)
        structured_constructor = Mock(side_effect=Structured)
        modules = {"vllm": SimpleNamespace(LLM=Mock(return_value=llm), SamplingParams=sampling_constructor),
                   "vllm.sampling_params": SimpleNamespace(StructuredOutputsParams=structured_constructor),
                   "torch": SimpleNamespace(inference_mode=contextlib.nullcontext)}
        offline = {key: "1" for key in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_HUB_DISABLE_TELEMETRY", "VLLM_NO_USAGE_STATS")}
        offline["CUDA_VISIBLE_DEVICES"] = self.config["gpu_uuid"]
        sampling = {**actor_api.SAMPLING, "seed": 0, "max_tokens": 2048,
                    "structured_outputs": {"regex": r"[^\r\n]+\n"}}
        original = copy.deepcopy(sampling)
        with patch.dict("sys.modules", modules), patch.dict(os.environ, offline):
            session = actor_api._native_loader(self.config)
            raw = session.generate("A", sampling)
            for invalid in (None, {}, {"regex": True}, {"regex": ""},
                            {"regex": "x", "choice": ["answer"]}, Structured("x")):
                with self.subTest(invalid=invalid), self.assertRaisesRegex(actor_api.ActorError, "JSON regex"):
                    session.generate("A", {**sampling, "structured_outputs": invalid})
            session.close()
        self.assertEqual(raw["text"], "wrong content\n")
        self.assertEqual(sampling, original)
        self.assertEqual(actor_api.canonical(sampling), actor_api.canonical(original))
        structured_constructor.assert_called_once_with(regex=r"[^\r\n]+\n")
        sampling_constructor.assert_called_once_with(
            **{**original, "structured_outputs": Structured(r"[^\r\n]+\n")})
        llm.generate.assert_called_once()
        self.assertEqual(llm.generate.call_args.args[1],
                         {**original, "structured_outputs": Structured(r"[^\r\n]+\n")})

    def test_default_sampling_hook_matches_existing_dictionary(self):
        actor = self.actor()
        self.assertEqual(actor._sampling(self.request, self.limits),
                         {**actor_api.SAMPLING, "seed": self.request["seed"], "max_tokens": self.limits["output_tokens"]})


if __name__ == "__main__":
    unittest.main()
