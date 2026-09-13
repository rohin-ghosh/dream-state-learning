"""Injected command glue only: synthetic receipts, no native models or fitting."""

import copy
import contextlib
import io
import json
import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import test_astra_pcfl_native_actor as native_fixtures
import test_pcfl_own_write_train as writer_fixtures
import test_pcfl_vertical_formation_plan as plan_fixtures
from gpu import astra_pcfl_own_write_command as command


class EngineCore:
    def __init__(self):
        self.calls = 0
        self.fail = False

    def shutdown(self):
        self.calls += 1
        if self.fail:
            raise RuntimeError("synthetic shutdown failure")


class FormationSession:
    def __init__(self, settings, clock, outputs):
        self.tokenizer = writer_fixtures.SyntheticTokenizer(settings["model_path"])
        self.clock, self.outputs = clock, outputs
        self.engine = EngineCore()
        self.llm = SimpleNamespace(llm_engine=SimpleNamespace(engine_core=self.engine))
        self.closed, self.calls = 0, []

    def generate(self, prompt, sampling):
        text = self.outputs[len(self.calls)]
        self.calls.append((prompt, sampling))
        self.clock.now += .25
        return {"text": text, "output_token_ids": self.tokenizer.encode(text),
                "prompt_token_ids": self.tokenizer.encode(prompt), "finish_reason": "stop", "stop_reason": None}

    def close(self):
        self.closed += 1
        return {"shutdown_method_available": False, "shutdown_returned": False}


class ReadSession:
    def __init__(self, settings, clock):
        self.tokenizer = writer_fixtures.SyntheticTokenizer(settings["model_path"])
        self.route = command.readout_api.route_identity(settings)
        self.binding = settings["shutdown_binding"]
        self.clock, self.calls, self.closed = clock, [], 0
        self.finish = "stop"
        self.text = "MISS"

    def verify_shutdown(self):
        return {"method": "SYNTHETIC_SHUTDOWN", "source": self.binding}

    def generate(self, prompt, sampling):
        self.calls.append((prompt, sampling))
        self.clock.now += .25
        return {"text": self.text, "output_token_ids": self.tokenizer.encode(self.text),
                "prompt_token_ids": self.tokenizer.encode(prompt), "finish_reason": self.finish,
                "stop_reason": None, "route": self.route}

    def close(self):
        self.closed += 1
        return {**self.verify_shutdown(), "shutdown_returned": True}


class CommandTests(unittest.TestCase):
    def setUp(self):
        self.fixture = native_fixtures.ActorTests("test_real_actor_public_api_captures_exact_tokens_and_bytes")
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root, self.clock = self.fixture.root, self.fixture.clock
        self.output = self.root / "command"
        self.env = {"native": self.fixture.environment, "peft_version": "SYNTHETIC"}
        self.env_patch = patch.dict(os.environ, {**{name: "1" for name in command.OFFLINE}, "CUDA_VISIBLE_DEVICES": ""})
        self.env_patch.start()
        self.addCleanup(self.env_patch.stop)
        self.shutdown_path = Path(__file__).resolve()
        self.shutdown_patch = patch.object(command, "SHUTDOWN_SHA256", command.file_hash(self.shutdown_path))
        self.shutdown_patch.start()
        self.addCleanup(self.shutdown_patch.stop)
        self.models = {name: value["sha256"] for name, value in command.read(self.fixture.receipt)["files"].items()}
        self.cpu_path = self.root / "base_cpu.json"
        command.write(self.cpu_path, {"schema": "pcfl.own_write.cpu_base_state.v1", "status": "COMPLETE",
            "base_state_sha256": "a" * 64, "model_binding_sha256": command.file_hash(self.fixture.receipt),
            "model_files": self.models, "dtype": "bfloat16", "device": "cpu", "environment": self.env})
        self.spec = {"schema": command.SCHEMA + "/spec", "model_path": str(self.fixture.model),
                     "model_binding": {"path": str(self.fixture.receipt), "sha256": command.file_hash(self.fixture.receipt)},
                     "base_state_receipt": {"path": str(self.cpu_path), "sha256": command.file_hash(self.cpu_path)},
                     "shutdown_binding": {"path": str(self.shutdown_path), "sha256": command.file_hash(self.shutdown_path)},
                     "gpu_uuid": "GPU-SYNTHETIC", "environment": self.env,
                     "expires_monotonic": 10000.0, "boot_id": command.boot_id()}
        self.spec_path = self.root / "spec.json"
        command.write(self.spec_path, self.spec)
        self.manifest_path = self.output / "manifest.json"
        self.form_session = self.read_session = None

    def prepare(self, tokenizer_factory=None):
        return command.prepare(str(self.spec_path), command.file_hash(self.spec_path), self.output,
                               tokenizer_factory=tokenizer_factory or writer_fixtures.SyntheticTokenizer,
                               identity_reader=lambda deadline: {"model_files": self.models},
                               environment_reader=lambda: self.env, clock=self.clock)

    def form_factory(self, settings):
        cell, actions, links = command.choices()
        events, link_rows = plan_fixtures.synthetic_child_spans(cell, actions, links)
        outputs = [raw for pair in zip(actions, events) for raw in pair] + link_rows
        self.form_session = FormationSession(settings, self.clock, outputs)
        return command.native.NativeActor(settings, loader=lambda config: self.form_session,
                                          environment_reader=lambda: self.env["native"], clock=self.clock)

    def read_factory(self, settings):
        self.read_session = ReadSession(settings, self.clock)
        return command.readout_api.ReadoutActor(settings, loader=lambda config: self.read_session,
                                                environment_reader=lambda: self.env["native"], clock=self.clock)

    def formation(self, factory=None):
        return command.formation(str(self.manifest_path), command.file_hash(self.manifest_path),
                                 actor_factory=factory or self.form_factory, environment_reader=lambda: self.env, clock=self.clock)

    def readout(self, arm="NO_WRITE_C0"):
        return command.readout(str(self.manifest_path), command.file_hash(self.manifest_path), arm,
                               actor_factory=self.read_factory, environment_reader=lambda: self.env, clock=self.clock)

    def test_prepare_only_measures_and_freezes_exact_roster_schedule(self):
        with patch.object(command, "_model", side_effect=AssertionError("no model")), \
             patch.object(command.native.NativeActor, "generate", side_effect=AssertionError("no generation")):
            manifest = self.prepare()
        self.assertEqual(manifest["kind"], "INJECTED_CPU_TEST")
        self.assertFalse(manifest["full_L8_qualified"])
        self.assertFalse(manifest["full_assay_qualified"])
        self.assertEqual(manifest["formation_template"]["planner"]["cell"], command.core.to_data(command.choices()[0]))
        self.assertEqual(len(manifest["schedule"]["corpus"]["slots"]), 20)
        self.assertEqual(len(manifest["roster"]), 153)
        self.assertEqual({row["view"] for row in manifest["roster"]}, set(range(9)))
        self.assertTrue(all(row["seed"] == 0 and row["output_tokens"] == 2048 for row in manifest["roster"]))
        measured = command.read(self.output / "measurements.json")
        self.assertEqual(len(measured["formation_prompt_lengths"]), 20)
        self.assertEqual(len(measured["training_sequence_lengths"]), 160)
        self.assertLessEqual(max(measured["training_sequence_lengths"]), 512)
        self.assertEqual(measured["salt"], 0)
        self.assertTrue(measured["identifier_token_lengths"])
        self.assertFalse((self.output / "formation").exists())

    def test_formation_is_lazy_and_explicit_shutdown_precedes_actor_close(self):
        manifest = self.prepare()
        receipt = self.formation()
        self.assertEqual((receipt["calls"], receipt["fits"], receipt["updates"]), (20, 0, 0))
        self.assertEqual(self.form_session.engine.calls, 1)
        self.assertEqual(self.form_session.closed, 1)
        self.assertEqual(len(self.form_session.calls), 20)
        directory = self.output / "formation"
        config = command.read(directory / "formation_config.json")
        self.assertEqual(config["planner"], manifest["formation_template"]["planner"])
        self.assertEqual(config["actor_config"]["deadline"], receipt["started"] + 1800)
        service = command.read(directory / "exact_child_service.json")
        report = command.read(directory / "records" / "formation.json")
        self.assertEqual(service["calls"], 0)
        self.assertEqual(len(service["items"]), 17)
        for row in service["items"]:
            self.assertEqual(row["raw"], report["writer_payload"]["queries"][row["request"]]["target"])
        self.assertFalse(receipt["gpu_released"])
        command._completed(manifest, "formation")

    def test_failed_child_preserved_and_shutdown_still_called_no_retry(self):
        self.prepare()
        def factory(settings):
            actor = self.form_factory(settings)
            self.form_session.outputs[0] = "not an action"
            return actor
        with self.assertRaisesRegex(ValueError, "formation/close failed"):
            self.formation(factory)
        self.assertEqual(len(self.form_session.calls), 1)
        self.assertEqual((self.form_session.engine.calls, self.form_session.closed), (1, 1))
        self.assertTrue((self.output / "formation" / "failure.json").exists())
        self.assertFalse((self.output / "formation" / "completed.json").exists())
        with self.assertRaises(FileExistsError):
            self.formation()

    def test_shutdown_failure_preserves_close_and_denies_completion(self):
        self.prepare()
        def factory(settings):
            actor = self.form_factory(settings)
            self.form_session.engine.fail = True
            return actor
        with self.assertRaisesRegex(RuntimeError, "shutdown failure"):
            self.formation(factory)
        self.assertEqual(self.form_session.closed, 1)
        self.assertTrue((self.output / "formation" / "actor_close.json").exists())
        self.assertFalse((self.output / "formation" / "completed.json").exists())

    def test_no_write_runs_all_153_queries_no_history_and_no_fit(self):
        self.prepare()
        self.formation()
        with patch.object(command.train_api, "train_fit", side_effect=AssertionError("no fit")):
            receipt = self.readout()
        self.assertEqual((receipt["calls"], receipt["fits"], receipt["updates"]), (153, 0, 0))
        self.assertEqual(len(self.read_session.calls), 153)
        self.assertEqual(self.read_session.closed, 1)
        self.assertIsNone(self.read_session.route["lora_request"])
        scores = command.read(self.output / "readout_NO_WRITE_C0" / "scores.json")
        self.assertEqual(scores["denominator"], 153)
        self.assertTrue(all(row["raw"] == "MISS" and row["score"]["refusal"] for row in scores["results"]))
        for prompt, _ in self.read_session.calls:
            self.assertNotIn("COMMIT EVENT", prompt)
            self.assertNotIn("EVIDENCE", prompt)

    def mocked_fit(self, manifest, *, updates=200):
        config, report, receipts = command._formation_inputs(manifest)
        def build_fit(*args):
            self.assertEqual(args[0], config)
            self.assertEqual(args[2], report)
            self.assertEqual(args[4], manifest["schedule"])
            self.assertEqual(args[6], manifest["binding"])
            self.assertEqual(args[7], receipts)
            return {"SYNTHETIC_ONLY": True, "binding": args[6]}
        factory = Mock(return_value=(object(), manifest["binding"]["environment"]))
        def trainer(fit, tokenizer, base_factory, out):
            self.assertIs(base_factory, factory)
            base_factory()
            out.mkdir()
            adapter = out / "adapter"
            adapter.mkdir()
            command.write(adapter / "adapter_config.json", {"r": 8, "lora_alpha": 16, "lora_dropout": .05,
                          "peft_type": "LORA", "bias": "none", "modules_to_save": None})
            (adapter / "adapter_model.safetensors").write_bytes(b"SYNTHETIC_NOT_A_MODEL")
            receipt = {"status": "COMPLETE", "updates": updates}
            command.write(out / "completed.json", receipt)
            return receipt
        with patch.object(command.train_api, "build_fit", side_effect=build_fit):
            result = command.fit(str(self.manifest_path), command.file_hash(self.manifest_path),
                                 tokenizer_factory=writer_fixtures.SyntheticTokenizer, base_factory=factory,
                                 trainer=trainer, environment_reader=lambda: self.env, clock=self.clock)
        factory.assert_called_once()
        return result

    def test_fit_glue_passes_actual_formation_payload_and_final_adapter_to_auth(self):
        manifest = self.prepare()
        self.formation()
        receipt = self.mocked_fit(manifest)
        self.assertEqual((receipt["calls"], receipt["fits"], receipt["updates"]), (0, 1, 200))
        readout = self.readout("AUTH_WRITE")
        self.assertEqual(readout["calls"], 153)
        route = self.read_session.route["lora_request"]
        self.assertEqual(route["path"], str(self.output / "fit" / "write" / "adapter"))
        self.assertEqual(route["id"], 1)
        self.assertEqual(self.read_session.closed, 1)
        auth_config = command.read(self.output / "readout_AUTH_WRITE" / "readout_config.json")
        self.readout("NO_WRITE_C0")
        off_config = command.read(self.output / "readout_NO_WRITE_C0" / "readout_config.json")
        self.assertEqual(auth_config["roster"], off_config["roster"])
        self.assertEqual(auth_config["roster_sha256"], off_config["roster_sha256"])
        self.assertEqual(auth_config["engine"], off_config["engine"])
        self.assertIsNone(off_config["adapter"])

    def test_bool_update_count_rejected_without_readout(self):
        manifest = self.prepare()
        self.formation()
        with self.assertRaisesRegex(ValueError, "update count"):
            self.mocked_fit(manifest, updates=True)
        self.assertFalse((self.output / "fit" / "completed.json").exists())

    def test_prepare_refuses_existing_root_wrong_hash_and_nonempty_cvd(self):
        self.prepare()
        with self.assertRaisesRegex(ValueError, "fresh preparation"):
            self.prepare()
        with self.assertRaisesRegex(ValueError, "spec file hash"):
            command.prepare(self.spec_path, "0" * 64, self.root / "new")
        with patch.dict(os.environ, CUDA_VISIBLE_DEVICES="GPU-SYNTHETIC"), self.assertRaisesRegex(ValueError, "empty CVD"):
            self.prepare()

    def test_environment_failure_before_generation_preserves_attempt(self):
        self.prepare()
        factory = Mock(side_effect=AssertionError("no actor"))
        with self.assertRaisesRegex(ValueError, "environment drift"):
            command.formation(str(self.manifest_path), command.file_hash(self.manifest_path), actor_factory=factory,
                              environment_reader=lambda: {}, clock=self.clock)
        factory.assert_not_called()
        self.assertTrue((self.output / "formation" / "failure.json").exists())

    def test_caps_include_cold_work_and_close(self):
        self.prepare()
        def factory(settings):
            actor = self.form_factory(settings)
            original = actor.close
            def close():
                result = original()
                self.clock.now += 1800
                return result
            actor.close = close
            return actor
        with self.assertRaisesRegex(ValueError, "stage time"):
            self.formation(factory)
        self.assertEqual(self.form_session.closed, 1)
        self.assertTrue((self.output / "formation" / "failure.json").exists())

    def test_token_budget_failure_does_not_redraw_root(self):
        class TooLong(writer_fixtures.SyntheticTokenizer):
            def encode(self, text, add_special_tokens=False):
                return [3] * 20000
        with self.assertRaisesRegex(ValueError, "context cap"):
            self.prepare(TooLong)
        self.assertTrue((self.output / "prepare_failure.json").exists())
        self.assertFalse(self.manifest_path.exists())

    def test_modified_upstream_capture_blocks_readout_before_actor(self):
        self.prepare()
        self.formation()
        path = self.output / "formation" / "records" / "formation.json"
        path.write_bytes(path.read_bytes() + b" ")
        factory = Mock(side_effect=AssertionError("no actor"))
        with self.assertRaisesRegex(ValueError, "upstream files changed"):
            command.readout(str(self.manifest_path), command.file_hash(self.manifest_path), "NO_WRITE_C0",
                            actor_factory=factory, environment_reader=lambda: self.env, clock=self.clock)
        factory.assert_not_called()

    def test_injected_prepare_cannot_enter_native_cli_stage(self):
        self.prepare()
        with self.assertRaisesRegex(ValueError, "test preparation"):
            command.formation(str(self.manifest_path), command.file_hash(self.manifest_path),
                              environment_reader=lambda: self.env, clock=self.clock)

    def test_expired_stage_never_constructs_actor(self):
        self.prepare()
        self.clock.now = 10001
        factory = Mock(side_effect=AssertionError("no actor"))
        with self.assertRaisesRegex(ValueError, "expired"):
            self.formation(factory)
        factory.assert_not_called()

    def test_modified_shutdown_source_pin_blocks_prepare(self):
        self.spec["shutdown_binding"]["sha256"] = "b" * 64
        self.spec_path.write_bytes(command.canonical(self.spec))
        factory = Mock(side_effect=AssertionError("no tokenizer"))
        with self.assertRaisesRegex(ValueError, "input file drift"):
            self.prepare(factory)
        factory.assert_not_called()
        self.assertTrue((self.output / "prepare_failure.json").exists())

    def test_source_drift_before_generation_is_not_relaxed(self):
        self.prepare()
        factory = Mock(side_effect=AssertionError("no actor"))
        with patch.object(command, "source_files", return_value={}), self.assertRaisesRegex(ValueError, "source/cap drift"):
            self.formation(factory)
        factory.assert_not_called()

    def test_cpu_base_receipt_cannot_be_cuda_or_an_adapter_hash_label(self):
        receipt = command.read(self.cpu_path)
        receipt["device"] = "cuda"
        self.cpu_path.write_bytes(command.canonical(receipt))
        self.spec["base_state_receipt"]["sha256"] = command.file_hash(self.cpu_path)
        self.spec_path.write_bytes(command.canonical(self.spec))
        with self.assertRaisesRegex(ValueError, "CPU base identity"):
            self.prepare()

    def test_length_correct_readout_is_scored_raw_but_not_stop_pass(self):
        manifest = self.prepare()
        self.formation()
        report = command.read(self.output / "formation" / "records" / "formation.json")
        first = manifest["roster"][0]["request"]
        target = report["writer_payload"]["queries"][first]["target"]
        def factory(settings):
            actor = self.read_factory(settings)
            self.read_session.text = target
            self.read_session.finish = "length"
            return actor
        receipt = command.readout(str(self.manifest_path), command.file_hash(self.manifest_path), "NO_WRITE_C0",
                                  actor_factory=factory, environment_reader=lambda: self.env, clock=self.clock)
        scores = command.read(self.output / "readout_NO_WRITE_C0" / "scores.json")
        self.assertEqual(receipt["calls"], 153)
        self.assertTrue(scores["results"][0]["score"]["strict"])
        self.assertFalse(scores["results"][0]["strict_stop"])
        self.assertEqual(scores["results"][0]["raw"], target)

    def test_failed_readout_closes_and_keeps_all_planned_slots_without_retry(self):
        self.prepare()
        self.formation()
        def factory(settings):
            actor = self.read_factory(settings)
            generate = self.read_session.generate
            def fail(prompt, sampling):
                if len(self.read_session.calls) == 3:
                    raise RuntimeError("synthetic read failure")
                return generate(prompt, sampling)
            self.read_session.generate = fail
            return actor
        with self.assertRaisesRegex(RuntimeError, "synthetic read failure"):
            command.readout(str(self.manifest_path), command.file_hash(self.manifest_path), "NO_WRITE_C0",
                            actor_factory=factory, environment_reader=lambda: self.env, clock=self.clock)
        self.assertEqual(self.read_session.closed, 1)
        directory = self.output / "readout_NO_WRITE_C0"
        self.assertEqual(len(command.read(directory / "readout_config.json")["roster"]), 153)
        self.assertTrue((directory / "actor" / "call_0003.error.json").exists())
        self.assertFalse((directory / "completed.json").exists())
        with self.assertRaises(FileExistsError):
            self.readout()

    def test_cli_passes_exact_stage_arguments(self):
        for stage in ("formation", "fit"):
            with patch.object(command, "file_hash", return_value="b" * 64), \
                 patch.object(command, stage, return_value={"sha256": "f" * 64}) as worker, contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(command.main([stage, "--manifest", "manifest", "--manifest-sha256", "abc"]), 0)
                worker.assert_called_once_with("manifest", "abc")
        output = io.StringIO()
        with patch.object(command, "file_hash", return_value="b" * 64), \
             patch.object(command, "prepare", return_value={"sha256": "f" * 64}) as worker, contextlib.redirect_stdout(output):
            command.main(["prepare", "--spec", "spec", "--spec-sha256", "abc", "--out", "out"])
            worker.assert_called_once_with("spec", "abc", "out")
        printed = json.loads(output.getvalue())
        self.assertEqual(printed["manifest_sha256"], "b" * 64)
        self.assertEqual(printed["seal_sha256"], "f" * 64)
        with patch.object(command, "file_hash", return_value="b" * 64), \
             patch.object(command, "readout", return_value={"sha256": "f" * 64}) as worker, contextlib.redirect_stdout(io.StringIO()):
            command.main(["readout", "--manifest", "manifest", "--manifest-sha256", "abc", "--arm", "AUTH_WRITE"])
            worker.assert_called_once_with("manifest", "abc", "AUTH_WRITE")


if __name__ == "__main__":
    unittest.main()
