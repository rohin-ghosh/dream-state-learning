import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest import mock


SOURCE = Path(__file__).with_name("astra_a100_native_readiness_20260913.py")
SPEC = importlib.util.spec_from_file_location("a100_readiness", SOURCE)
READINESS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(READINESS)


class ReadinessTests(unittest.TestCase):
    def test_import_is_cpu_only(self):
        for name in ("torch", "vllm", "flashinfer"):
            self.assertNotIn(name, sys.modules)

    def test_settings_match_pinned_runtime_except_four_token_cap(self):
        engine, params = READINESS.runtime_settings()
        self.assertEqual(engine, dict(max_model_len=16384, tensor_parallel_size=1, seed=0,
            gpu_memory_utilization=0.85, enforce_eager=True, enable_lora=True,
            max_lora_rank=32, enable_prefix_caching=False, dtype="bfloat16", trust_remote_code=False))
        self.assertEqual(params["max_tokens"], 4)
        self.assertEqual(params["n"], 1)
        self.assertFalse(params["ignore_eos"])

    def test_runtime_pin_mismatch(self):
        with mock.patch.object(READINESS, "RUNTIME_SHA256", "0" * 64), self.assertRaises(ValueError):
            READINESS.runtime_settings()

    def test_helper_pin_mismatch_before_import(self):
        with self.assertRaises(ValueError):
            READINESS.pinned_module(SOURCE, "0" * 64, "not_imported")

    def test_binding_exact_14_files(self):
        binding = READINESS.read_binding()
        self.assertEqual(len(binding["files"]), 14)
        self.assertEqual(binding["revision"], READINESS.REVISION)

    def test_binding_pin_mismatch(self):
        with mock.patch.object(READINESS, "BINDING_SHA256", "0" * 64), self.assertRaises(ValueError):
            READINESS.read_binding()

    def fixture_files(self, directory):
        files = {}
        for index in range(14):
            path = directory / (str(index) + ".fixture")
            content = str(index).encode()
            path.write_bytes(content)
            files[path.name] = {"sha256": hashlib.sha256(content).hexdigest(), "size": len(content)}
        return {"files": files}

    def test_all_fixture_payloads_match(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = READINESS.verify_model_files(root, self.fixture_files(root))
            self.assertTrue(result["all_match"])
            self.assertEqual(len(result["files"]), 14)

    def test_corruption_and_missing_file_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            binding = self.fixture_files(root)
            (root / "0.fixture").write_bytes(b"changed")
            (root / "1.fixture").unlink()
            result = READINESS.verify_model_files(root, binding)
            self.assertFalse(result["all_match"])
            self.assertFalse(result["files"]["0.fixture"]["match"])
            self.assertEqual(result["files"]["1.fixture"]["error_type"], "FileNotFoundError")

    def test_incomplete_inventory_is_not_full_binding(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            binding = self.fixture_files(root)
            binding["files"].pop("0.fixture")
            self.assertFalse(READINESS.verify_model_files(root, binding)["all_match"])

    def test_unsafe_filename_refused(self):
        with self.assertRaises(ValueError):
            READINESS.verify_model_files(Path("/fixture"), {"files": {"../escape": {}}})

    def outputs(self, tokens=None, prompt=None, text="not a scored answer"):
        completion = types.SimpleNamespace(token_ids=[7] if tokens is None else tokens,
            text=text, finish_reason="length", stop_reason=None)
        return [types.SimpleNamespace(outputs=[completion], prompt_token_ids=[1, 2] if prompt is None else prompt)]

    def test_response_checks_no_semantics(self):
        result = READINESS.check_response(self.outputs(), [1, 2])
        self.assertFalse(result["semantic_scoring"])
        self.assertIsNone(result["lora_request"])
        self.assertEqual(result["text"], "not a scored answer")

    def test_response_range_and_prompt_rejected(self):
        for tokens in ([], [1] * 5, [-1], [True]):
            with self.subTest(tokens=tokens), self.assertRaises(ValueError):
                READINESS.check_response(self.outputs(tokens=tokens), [1, 2])
        with self.assertRaises(ValueError):
            READINESS.check_response(self.outputs(prompt=[9]), [1, 2])

    def test_response_cardinality_rejected(self):
        for outputs in ([], self.outputs() * 2):
            with self.assertRaises(ValueError):
                READINESS.check_response(outputs, [1, 2])

    def test_opt_in_and_uuid_guard_before_any_helper_or_output(self):
        for allow, uuid in ((False, READINESS.EXPECTED_UUID), (True, "0"), (True, ""), (True, READINESS.EXPECTED_UUID + ",1")):
            with tempfile.TemporaryDirectory() as directory, mock.patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": uuid}), mock.patch.object(READINESS, "pinned_module") as load, contextlib.redirect_stdout(io.StringIO()):
                output = Path(directory) / "fresh"
                arguments = ["--output", str(output)] + (["--allow-gpu"] if allow else [])
                self.assertEqual(READINESS.main(arguments), 2)
                load.assert_not_called()
                self.assertFalse(output.exists())

    def test_existing_root_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory, mock.patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": READINESS.EXPECTED_UUID}), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(READINESS.main(["--allow-gpu", "--output", directory]), 2)

    @contextlib.contextmanager
    def fake_native(self, directory, failure=None, uuid=None):
        model = directory / "model"
        model.mkdir()
        (model / "tokenizer_config.json").write_text(json.dumps({"chat_template": "fixture-template"}))
        engine = mock.Mock()
        engine.get_tokenizer.return_value = types.SimpleNamespace(chat_template="fixture-template")
        engine.generate.return_value = self.outputs()
        if failure:
            engine.generate.side_effect = failure
        factory = mock.Mock(return_value=engine)
        sampling = mock.Mock(side_effect=lambda **kwargs: kwargs)
        torch = types.SimpleNamespace(inference_mode=contextlib.nullcontext,
            cuda=types.SimpleNamespace(is_available=lambda: True, device_count=lambda: 1,
                get_device_properties=lambda index: types.SimpleNamespace(uuid=uuid or READINESS.EXPECTED_UUID, name="A100 fixture")))
        probe = types.SimpleNamespace(render=lambda tokenizer, messages: dict(rendered_prompt="fixture prompt", prompt_token_ids=[1, 2]))
        support = READINESS.pinned_module(READINESS.TOOLS, READINESS.TOOLS_SHA256, "fixture_support")
        modules = {"torch": torch, "vllm": types.SimpleNamespace(LLM=factory, SamplingParams=sampling)}
        with mock.patch.dict(sys.modules, modules):
            yield model, probe, support, factory, engine

    def test_one_off_load_and_generation_with_no_adapter(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.fake_native(root) as (model, probe, support, factory, instance):
                engine, params = READINESS.runtime_settings()
                result = READINESS.run_native(model, engine, params, probe, root, support, {})
                factory.assert_called_once_with(model=str(model), tokenizer=str(model), **engine)
                instance.generate.assert_called_once_with(["fixture prompt"], params, lora_request=None, use_tqdm=False)
                instance.shutdown.assert_called_once()
                self.assertEqual(result["model_loads"], 1)
                self.assertEqual(result["generation_calls"], 1)

    def test_generation_failure_preserves_native_log_and_shutdown(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.fake_native(root, failure=RuntimeError("fixture compiler failure")) as (model, probe, support, factory, instance):
                record = {}
                with self.assertRaisesRegex(RuntimeError, "compiler failure"):
                    with support.private_native_output(root, record):
                        READINESS.run_native(model, *READINESS.runtime_settings(), probe, root, support, record)
                instance.shutdown.assert_called_once()
                self.assertIn("fixture compiler failure", (root / "native.log").read_text())
                self.assertEqual((root / "native.log").stat().st_mode & 0o777, 0o600)

    def test_wrong_runtime_uuid_prevents_model_load(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.fake_native(root, uuid="GPU-wrong") as (model, probe, support, factory, instance):
                with self.assertRaises(ValueError):
                    READINESS.run_native(model, *READINESS.runtime_settings(), probe, root, support, {})
                factory.assert_not_called()

    def mocked_main(self, directory, matches):
        support = READINESS.pinned_module(READINESS.TOOLS, READINESS.TOOLS_SHA256, "main_fixture_support")
        home = Path(directory)
        output = home / "fresh"
        def native(*arguments):
            self.assertEqual(os.environ["HF_HUB_OFFLINE"], "1")
            self.assertEqual(os.environ["TRANSFORMERS_OFFLINE"], "1")
            self.assertEqual(os.environ["CUDA_HOME"], "/usr/local/cuda")
            return {"route": "OFF", "mock_only": True}
        with mock.patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": READINESS.EXPECTED_UUID}), mock.patch.object(READINESS.Path, "home", return_value=home), mock.patch.object(READINESS.sys, "prefix", str(home / "v2/venv")), mock.patch.object(READINESS, "pinned_module", side_effect=lambda path, pin, name: support if path == READINESS.TOOLS else types.SimpleNamespace()), mock.patch.object(READINESS, "verify_model_files", side_effect=[{"all_match": value, "files": {}} for value in matches]) as hashes, mock.patch.object(support, "inspect_tools", return_value={"ninja": {"ready": True}}), mock.patch.object(READINESS, "run_native", side_effect=native) as run, contextlib.redirect_stdout(io.StringIO()):
            code = READINESS.main(["--allow-gpu", "--output", str(output)])
        return code, json.loads((output / "result.json").read_text()), run.call_count, hashes.call_count

    def test_main_model_mismatch_prevents_native_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            code, result, runs, checks = self.mocked_main(directory, [False])
        self.assertEqual((code, runs, checks), (1, 0, 1))
        self.assertEqual(result["status"], "OFF_NATIVE_READINESS_FAILED")

    def test_main_offline_success_rechecks_payloads_not_science(self):
        with tempfile.TemporaryDirectory() as directory:
            code, result, runs, checks = self.mocked_main(directory, [True, True])
        self.assertEqual((code, runs, checks), (0, 1, 2))
        self.assertEqual(result["status"], "OFF_NATIVE_READINESS_PASS")
        self.assertIsNone(result["scientific_pass"])

    def test_main_post_readout_drift_is_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            code, result, runs, checks = self.mocked_main(directory, [True, False])
        self.assertEqual((code, runs, checks), (1, 1, 2))
        self.assertEqual(result["status"], "OFF_NATIVE_READINESS_FAILED")


if __name__ == "__main__":
    unittest.main()
