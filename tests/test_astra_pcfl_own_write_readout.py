"""Injected CPU readout/custody tests; never import a real native model stack."""

import contextlib
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from gpu import astra_pcfl_own_write_readout as api
from tests.test_astra_pcfl_native_actor import Clock, Tokenizer


def file_entry(path):
    data = Path(path).read_bytes()
    return {"size": len(data), "sha256": hashlib.sha256(data).hexdigest()}


class Session:
    def __init__(self, config, clock):
        self.tokenizer = Tokenizer(config["model_path"])
        self.route = api.route_identity(config)
        self.clock = clock
        self.calls, self.closed = [], 0
        self.text = "MISS"
        self.duration = 0.25
        self.mutate = lambda raw: raw
        self.shutdown_binding = config["shutdown_binding"]

    def verify_shutdown(self):
        return {"method": "SYNTHETIC.engine_core.shutdown", "source": self.shutdown_binding}

    def generate(self, prompt, sampling):
        self.calls.append((prompt, copy.deepcopy(sampling)))
        self.clock.now += self.duration
        return self.mutate({"text": self.text, "output_token_ids": self.tokenizer.encode(self.text),
                            "prompt_token_ids": self.tokenizer.encode(prompt), "finish_reason": "stop",
                            "stop_reason": None, "route": copy.deepcopy(self.route)})

    def close(self):
        self.closed += 1
        return {**self.verify_shutdown(), "shutdown_returned": True}


class EngineCore:
    def __init__(self):
        self.closed = 0

    def shutdown(self):
        self.closed += 1


class ReadoutTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="pcfl_readout_synthetic_")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.model = self.root / "model"
        self.model.mkdir()
        names = [".gitattributes", "LICENSE", "README.md", "config.json", "generation_config.json",
                 "merges.txt", "model-00001-of-00004.safetensors", "model-00002-of-00004.safetensors",
                 "model-00003-of-00004.safetensors", "model-00004-of-00004.safetensors",
                 "model.safetensors.index.json", "tokenizer.json", "tokenizer_config.json", "vocab.json"]
        files = {}
        for name in names:
            payload = b'{"model_type":"qwen2"}' if name == "config.json" else ("SYNTHETIC/" + name).encode()
            (self.model / name).write_bytes(payload)
            files[name] = {**file_entry(self.model / name), "public_match": "LFS_SHA256"}
        receipt = self.root / "public_receipt.json"
        receipt.write_bytes(api.canonical({"repository": api.native.MODEL_NAME, "revision": api.native.REVISION,
            "status": "PUBLIC_REVISION_FILES_MATCHED_PROSPECTIVE_BINDING", "model": str(self.model), "file_count": 14, "files": files}))
        self.clock = Clock()
        self.environment = {"python": "/SYNTHETIC/python", "version": "SYNTHETIC", "packages": {name: "SYNTHETIC" for name in api.native.PACKAGES}}
        self.roster = [{"id": "read/0", "request": "READ EVENT E_AAAAAAAAAA", "view": 0, "seed": 42, "output_tokens": 256},
                       {"id": "read/1", "request": "READ EVENT E_AAAAAAAAAA", "view": 8, "seed": 42, "output_tokens": 256}]
        self.config = {"schema": api.SCHEMA, "arm": "NO_WRITE_C0", "adapter": None,
            "model_path": str(self.model), "model_binding": {"path": str(receipt), "sha256": file_entry(receipt)["sha256"]},
            "source_files": {path: file_entry(path)["sha256"] for path in api.required_source_paths()},
            "tokenizer_files": {name: files[name]["sha256"] for name in api.native.TOKENIZER_FILES},
            "chat_template_sha256": api.native.text_hash(Tokenizer.chat_template),
            "tokenizer_probe": {"text": "probe", "token_ids": [ord(character) for character in "probe"]},
            "environment": self.environment, "gpu_uuid": "GPU-SYNTHETIC", "engine": copy.deepcopy(api.ENGINE),
            "output_dir": str(self.root / "output"), "deadline": 100.0, "device_seconds_cap": 80,
            "max_input_tokens": 15000, "max_output_tokens": 256, "max_calls": 2,
            "roster": self.roster, "roster_sha256": api.digest(self.roster),
            "shutdown_binding": {"path": str(Path(__file__).resolve()), "sha256": file_entry(__file__)["sha256"]}}
        self.limits = {"deadline": 90, "device_seconds": 60}
        self.request = {"id": "read/0"}
        self.session, self.loader = None, None

    def adapter(self):
        root = self.root / "adapter"
        root.mkdir()
        (root / "adapter_config.json").write_bytes(api.canonical({"r": 8, "lora_alpha": 16, "lora_dropout": 0.05,
                "peft_type": "LORA", "bias": "none", "modules_to_save": None}))
        (root / "adapter_model.safetensors").write_bytes(b"SYNTHETIC_NOT_REAL_TENSORS")
        self.config["arm"] = "AUTH_WRITE"
        self.config["adapter"] = {"name": "pcfl-own-write", "id": 1, "path": str(root),
                                  "files": {path.name: file_entry(path) for path in root.iterdir()}}

    def actor(self):
        self.session = Session(self.config, self.clock)
        self.loader = Mock(return_value=self.session)
        actor = api.ReadoutActor(self.config, loader=self.loader, environment_reader=lambda: copy.deepcopy(self.environment), clock=self.clock)
        self.addCleanup(actor.close)
        return actor

    def read(self, name):
        return json.loads((Path(self.config["output_dir"]) / name).read_bytes())

    def test_lazy_construct_close_and_no_release_claim(self):
        actor = self.actor()
        self.loader.assert_not_called()
        receipt = actor.close()
        self.assertIsNone(receipt["gpu_vacant"])
        self.assertIsNone(receipt["owned_group_released"])
        self.assertFalse(Path(self.config["output_dir"]).exists())
        self.assertEqual(actor.close(), receipt)

    def test_c0_routes_capture_exact_bytes_and_wrapper_transfer(self):
        actor = self.actor()
        first = actor.generate(self.request, self.limits)
        second = actor.generate({"id": "read/1"}, self.limits)
        self.assertEqual(first["route"], {"arm": "NO_WRITE_C0", "lora_request": None, "adapter_files_sha256": None})
        self.assertEqual(second["text"], "MISS")
        self.assertNotEqual(self.session.calls[0][0], self.session.calls[1][0])
        for index, row in enumerate(self.roster):
            request = self.read(f"call_{index:04d}.request.json")
            self.assertEqual(request["messages"], api.public_messages(row))
            self.assertEqual(len(request["messages"]), 2)
            self.assertEqual(self.session.calls[index][1], {**api.native.SAMPLING, "seed": row["seed"], "max_tokens": row["output_tokens"]})
        self.assertEqual(bytes.fromhex(self.read("call_0000.response.json")["raw_hex"]), b"MISS")
        self.assertTrue(self.read("load.json")["engine"]["enable_lora"])
        self.assertEqual(self.read("identity.json")["kind"], "INJECTED_CPU_TEST")
        self.assertEqual(actor.close()["calls_consumed"], 2)
        self.assertEqual(self.session.closed, 1)

    def test_auth_write_has_explicit_pinned_route_everywhere(self):
        self.adapter()
        actor = self.actor()
        response = actor.generate(self.request, self.limits)
        route = api.route_identity(self.config)
        self.assertEqual(response["route"], route)
        self.assertEqual(route["lora_request"]["id"], 1)
        for name in ("load.json", "call_0000.request.json", "call_0000.render.json", "call_0000.raw.json", "close.json"):
            if name == "close.json":
                actor.close()
            self.assertEqual(self.read(name)["route"], route)
        identity = self.read("identity.json")["identity"]
        self.assertEqual(identity["route"], route)
        self.assertNotIn("mount", identity["base_identity"])

    def test_real_public_cpu_scorer_receives_only_captured_response(self):
        actor = self.actor()
        expected = "EVENT E_AAAAAAAAAA AT N_AAAAAAAAAA DID P_AAAAAAAAAA GOT N_BBBBBBBBBB EVIDENCE R_AAAAAAAAAA\n"
        self.session.text = expected
        response = actor.generate(self.request, self.limits)
        score = api.core.score_memory_response(response["text"], expected)
        self.assertTrue(score["strict"])
        self.assertNotIn(expected, self.session.calls[0][0])
        self.assertNotIn("EVIDENCE", self.session.calls[0][0])

    def test_request_cannot_supply_messages_targets_or_transcript(self):
        actor = self.actor()
        for field in ("messages", "target", "context", "transcript", "oracle", "mount", "seed"):
            with self.subTest(field=field), self.assertRaises(ValueError):
                actor.generate({**self.request, field: "private"}, self.limits)
        self.loader.assert_not_called()

    def test_roster_rejects_extra_data_or_non_read_bytes(self):
        for value in ("READ EVENT E_AAAAAAAAAA\nsecret", "READ EVENT E_AAAAAAAAAA\n", "ROUTE N_AAAAAAAAAA"):
            config = copy.deepcopy(self.config)
            config["roster"][0]["request"] = value
            config["roster_sha256"] = api.digest(config["roster"])
            with self.subTest(value=value), self.assertRaises(ValueError):
                api.ReadoutActor(config)
        config = copy.deepcopy(self.config)
        config["roster"][0]["target"] = "private"
        config["roster_sha256"] = api.digest(config["roster"])
        with self.assertRaises(ValueError):
            api.ReadoutActor(config)

    def test_roster_seal_seed_and_order(self):
        config = copy.deepcopy(self.config)
        config["roster"][0]["seed"] += 1
        with self.assertRaisesRegex(ValueError, "roster"):
            api.ReadoutActor(config)
        actor = self.actor()
        with self.assertRaisesRegex(ValueError, "next frozen"):
            actor.generate({"id": "read/1"}, self.limits)
        self.loader.assert_not_called()

    def test_no_retry_after_consumption(self):
        actor = self.actor()
        actor.generate(self.request, self.limits)
        with self.assertRaises(ValueError):
            actor.generate(self.request, self.limits)
        self.assertEqual(len(self.session.calls), 1)

    def test_engine_is_identical_enabled_and_adapter_arm_is_closed(self):
        for key, value in (("enable_lora", False), ("max_lora_rank", 32)):
            config = copy.deepcopy(self.config)
            config["engine"][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                api.ReadoutActor(config)
        self.config["arm"] = "AUTH_WRITE"
        with self.assertRaises(ValueError):
            api.ReadoutActor(self.config)
        self.adapter()
        self.config["arm"] = "NO_WRITE_C0"
        with self.assertRaises(ValueError):
            api.ReadoutActor(self.config)

    def test_adapter_byte_drift_blocks_before_load(self):
        self.adapter()
        actor = self.actor()
        (Path(self.config["adapter"]["path"]) / "adapter_model.safetensors").write_bytes(b"DRIFT")
        with self.assertRaisesRegex(ValueError, "adapter file drift"):
            actor.generate(self.request, self.limits)
        self.loader.assert_not_called()
        self.assertTrue(actor.close()["failed"])

    def test_wrong_rank_rejected_even_with_matching_file_pin(self):
        self.adapter()
        path = Path(self.config["adapter"]["path"]) / "adapter_config.json"
        metadata = json.loads(path.read_bytes())
        metadata["r"] = 16
        path.write_bytes(api.canonical(metadata))
        self.config["adapter"]["files"][path.name] = file_entry(path)
        actor = self.actor()
        with self.assertRaisesRegex(ValueError, "rank8"):
            actor.start()
        self.loader.assert_not_called()

    def test_extra_adapter_file_rejected_before_load(self):
        self.adapter()
        (Path(self.config["adapter"]["path"]) / "optimizer.pt").write_bytes(b"unbound")
        actor = self.actor()
        with self.assertRaisesRegex(ValueError, "inventory"):
            actor.start()
        self.loader.assert_not_called()

    def test_model_drift_blocks_before_load(self):
        actor = self.actor()
        (self.model / "model-00001-of-00004.safetensors").write_bytes(b"DRIFT")
        with self.assertRaisesRegex(ValueError, "model file"):
            actor.start()
        self.loader.assert_not_called()

    def test_source_and_environment_drift_block_before_load(self):
        self.config["source_files"][str(Path(api.__file__).resolve())] = "0" * 64
        actor = self.actor()
        with self.assertRaisesRegex(ValueError, "source identity"):
            actor.start()
        self.loader.assert_not_called()

    def test_package_identity_drift_before_load(self):
        actor = self.actor()
        self.environment["version"] = "DIFFERENT"
        with self.assertRaisesRegex(ValueError, "package identity"):
            actor.start()
        self.loader.assert_not_called()

    def test_output_is_fresh_and_disjoint_from_adapter(self):
        Path(self.config["output_dir"]).mkdir()
        actor = self.actor()
        with self.assertRaisesRegex(ValueError, "fresh"):
            actor.start()
        self.loader.assert_not_called()

    def test_adapter_output_overlap(self):
        self.adapter()
        self.config["output_dir"] = str(Path(self.config["adapter"]["path"]) / "output")
        actor = self.actor()
        with self.assertRaisesRegex(ValueError, "overlap"):
            actor.start()
        self.loader.assert_not_called()

    def test_actual_route_mismatch_preserves_raw_and_no_retry(self):
        self.adapter()
        actor = self.actor()
        self.session.mutate = lambda raw: {**raw, "route": {"arm": "NO_WRITE_C0"}}
        with self.assertRaisesRegex(ValueError, "actual LoRA route"):
            actor.generate(self.request, self.limits)
        self.assertEqual(self.read("call_0000.raw.json")["raw"]["route"], {"arm": "NO_WRITE_C0"})
        with self.assertRaises(ValueError):
            actor.generate(self.request, self.limits)
        self.assertEqual(len(self.session.calls), 1)

    def test_loaded_route_mismatch_before_generation(self):
        actor = self.actor()
        self.session.route = {"arm": "AUTH_WRITE"}
        with self.assertRaisesRegex(ValueError, "loaded adapter route"):
            actor.start()
        self.assertEqual(self.session.calls, [])

    def test_prompt_id_mismatch_preserves_raw(self):
        actor = self.actor()
        self.session.mutate = lambda raw: {**raw, "prompt_token_ids": [999]}
        with self.assertRaisesRegex(ValueError, "prompt token IDs"):
            actor.generate(self.request, self.limits)
        self.assertEqual(self.read("call_0000.raw.json")["raw"]["prompt_token_ids"], [999])

    def test_truncation_is_preserved_not_retried(self):
        actor = self.actor()
        self.session.mutate = lambda raw: {**raw, "finish_reason": "length"}
        result = actor.generate(self.request, self.limits)
        self.assertTrue(result["truncated"])
        self.assertEqual(result["finish_reason"], "length")
        self.assertEqual(len(self.session.calls), 1)

    def test_output_cap_failure_preserves_raw(self):
        actor = self.actor()
        self.session.text = "x" * 257
        with self.assertRaisesRegex(ValueError, "output token cap"):
            actor.generate(self.request, self.limits)
        self.assertEqual(len(self.read("call_0000.raw.json")["raw"]["text"]), 257)

    def test_input_cap_precedes_generation(self):
        self.config["max_input_tokens"] = 2
        actor = self.actor()
        with self.assertRaisesRegex(ValueError, "input/context"):
            actor.generate(self.request, self.limits)
        self.assertEqual(self.session.calls, [])

    def test_call_timeout_preserves_raw_and_marks_failure(self):
        actor = self.actor()
        self.session.duration = 61
        with self.assertRaisesRegex(ValueError, "deadline"):
            actor.generate(self.request, self.limits)
        self.assertTrue(self.read("call_0000.raw.json")["raw"])
        self.assertTrue(actor.close()["failed"])

    def test_expired_deadline_never_loads(self):
        actor = self.actor()
        with self.assertRaisesRegex(ValueError, "deadline"):
            actor.generate(self.request, {"deadline": 1, "device_seconds": 60})
        self.loader.assert_not_called()

    def test_cardinality_failure_keeps_original_captures(self):
        actor = self.actor()
        self.session.generate = Mock(side_effect=api.native._NativeOutputError([{"SYNTHETIC": "two outputs"}]))
        with self.assertRaises(api.native._NativeOutputError):
            actor.generate(self.request, self.limits)
        self.assertEqual(self.read("call_0000.raw.json")["invalid_cardinality_captures"], [{"SYNTHETIC": "two outputs"}])

    def test_adapter_drift_after_load_blocks_next_read(self):
        self.adapter()
        actor = self.actor()
        actor.generate(self.request, self.limits)
        (Path(self.config["adapter"]["path"]) / "adapter_model.safetensors").write_bytes(b"DRIFT")
        with self.assertRaisesRegex(ValueError, "file changed"):
            actor.generate({"id": "read/1"}, self.limits)
        self.assertEqual(len(self.session.calls), 1)

    def test_failed_shutdown_is_not_release(self):
        actor = self.actor()
        actor.start()
        self.session.close = Mock(side_effect=RuntimeError("synthetic shutdown failure"))
        receipt = actor.close()
        self.assertEqual(receipt["error_type"], "RuntimeError")
        self.assertIsNone(receipt["gpu_vacant"])
        self.assertIsNone(receipt["owned_group_released"])

    def test_native_loader_both_routes_and_actual_engine_core_shutdown_seam(self):
        self.adapter()
        adapter = copy.deepcopy(self.config["adapter"])
        for arm in api.ARMS:
            with self.subTest(arm=arm):
                config = copy.deepcopy(self.config)
                config["arm"], config["adapter"] = arm, adapter if arm == "AUTH_WRITE" else None
                engine_core = EngineCore()
                llm = Mock()
                llm.llm_engine = SimpleNamespace(engine_core=engine_core)
                llm.get_tokenizer.return_value = Tokenizer(self.model)
                llm.generate.return_value = [SimpleNamespace(prompt_token_ids=[1], outputs=[SimpleNamespace(
                    text="MISS", token_ids=[2], finish_reason="stop", stop_reason=None)])]
                constructor = Mock(return_value=llm)
                lora = Mock(side_effect=lambda name, identifier, path: SimpleNamespace(lora_name=name, lora_int_id=identifier, lora_path=path))
                modules = {"vllm": SimpleNamespace(LLM=constructor, SamplingParams=lambda **kwargs: kwargs),
                           "vllm.lora.request": SimpleNamespace(LoRARequest=lora),
                           "torch": SimpleNamespace(inference_mode=contextlib.nullcontext)}
                flags = {"CUDA_VISIBLE_DEVICES": config["gpu_uuid"], "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1",
                         "HF_HUB_DISABLE_TELEMETRY": "1", "VLLM_NO_USAGE_STATS": "1"}
                with patch.dict("sys.modules", modules), patch.dict(os.environ, flags), patch.object(api, "_native_started", False):
                    session = api._native_loader(config)
                    constructor.assert_called_once_with(model=str(self.model), tokenizer=str(self.model), **api.ENGINE)
                    self.assertEqual(session.verify_shutdown()["method"], "llm.llm_engine.engine_core.shutdown")
                    raw = session.generate("public", {"max_tokens": 8})
                    self.assertEqual(raw["route"], api.route_identity(config))
                    if arm == "NO_WRITE_C0":
                        lora.assert_not_called()
                        self.assertIsNone(llm.generate.call_args.kwargs["lora_request"])
                    else:
                        lora.assert_called_once_with("pcfl-own-write", 1, adapter["path"])
                        self.assertEqual(api._lora_identity(llm.generate.call_args.kwargs["lora_request"]), raw["route"]["lora_request"])
                    self.assertTrue(session.close()["shutdown_returned"])
                    self.assertEqual(engine_core.closed, 1)
                    llm.shutdown.assert_not_called()
                    with self.assertRaisesRegex(ValueError, "fresh process"):
                        api._native_loader(config)

    def test_native_loader_offline_failure_precedes_import(self):
        with patch.dict(os.environ, {"HF_HUB_OFFLINE": "0"}), patch.object(api, "_native_started", False):
            with self.assertRaisesRegex(ValueError, "offline"):
                api._native_loader(self.config)

    def test_native_shutdown_source_mismatch_or_missing_method_cannot_pass(self):
        flags = {"CUDA_VISIBLE_DEVICES": self.config["gpu_uuid"], "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1",
                 "HF_HUB_DISABLE_TELEMETRY": "1", "VLLM_NO_USAGE_STATS": "1"}
        for engine_core, expected_error in ((EngineCore(), ValueError), (object(), AttributeError)):
            config = copy.deepcopy(self.config)
            config["shutdown_binding"]["sha256"] = "0" * 64
            llm = Mock()
            llm.llm_engine = SimpleNamespace(engine_core=engine_core)
            modules = {"vllm": SimpleNamespace(LLM=Mock(return_value=llm), SamplingParams=Mock()),
                       "vllm.lora.request": SimpleNamespace(LoRARequest=Mock())}
            with self.subTest(engine=type(engine_core).__name__), patch.dict("sys.modules", modules), \
                    patch.dict(os.environ, flags), patch.object(api, "_native_started", False):
                session = api._native_loader(config)
                with self.assertRaises(expected_error):
                    session.verify_shutdown()
                with self.assertRaises(expected_error):
                    session.close()
                llm.generate.assert_not_called()
                llm.shutdown.assert_not_called()

    def test_tokenizer_probe_drift_prevents_any_generation(self):
        actor = self.actor()
        self.session.tokenizer.encode = Mock(return_value=[999])
        with self.assertRaisesRegex(ValueError, "tokenizer probe"):
            actor.start()
        self.assertEqual(self.session.calls, [])

    def test_shutdown_pin_drift_precedes_model_load(self):
        self.config["shutdown_binding"]["sha256"] = "0" * 64
        actor = self.actor()
        with self.assertRaisesRegex(ValueError, "shutdown source drift"):
            actor.start()
        self.loader.assert_not_called()


if __name__ == "__main__":
    unittest.main()
