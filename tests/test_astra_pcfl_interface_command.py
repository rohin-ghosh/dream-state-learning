"""Synthetic preserved roots and injected native sessions; CPU only."""

import copy
import os
from pathlib import Path
from types import SimpleNamespace
import sys
import time
import unittest
from unittest.mock import patch

import test_astra_pcfl_native_actor as fixtures
from gpu import astra_pcfl_interface_command as command


class EngineCore:
    def __init__(self):
        self.calls = 0
        self.fail = False

    def shutdown(self):
        self.calls += 1
        if self.fail:
            raise RuntimeError("synthetic installed shutdown failure")


class Session:
    def __init__(self, tokenizer, clock, texts):
        self.tokenizer, self.clock, self.texts = tokenizer, clock, iter(texts)
        self.engine = EngineCore()
        self.llm = SimpleNamespace(llm_engine=SimpleNamespace(engine_core=self.engine))
        self.closed = 0
        self.backend_failure = False

    def generate(self, prompt, sampling):
        if self.backend_failure:
            raise RuntimeError("synthetic backend failure")
        self.clock.now += .001
        text = next(self.texts)
        return {"text": text, "output_token_ids": self.tokenizer.encode(text),
                "prompt_token_ids": self.tokenizer.encode(prompt), "finish_reason": "stop", "stop_reason": None}

    def close(self):
        self.closed += 1
        return {"shutdown_method_available": False, "shutdown_returned": False}


class Harness:
    def __init__(self, case):
        self.fixture = fixtures.ActorTests("test_real_actor_public_api_captures_exact_tokens_and_bytes")
        self.fixture.setUp()
        case.addCleanup(self.fixture.doCleanups)
        self.root, self.clock = self.fixture.root, self.fixture.clock
        self.clock.now = time.monotonic()
        self.fixture.environment["python"] = str(Path(sys.executable).resolve())
        self.tokenizer = self.fixture.session.tokenizer
        self.output = self.root / "prepared"
        self.roots = self.root / "original_roots.json"
        command.write(self.roots, [command.driver.core.to_data(command.driver.core.build_root(f"excluded/{index}")) for index in range(4)])
        self.spec = {"schema": command.SCHEMA + "/spec", "model_path": str(self.fixture.model),
            "model_binding": self.fixture.config["model_binding"],
            "roots_file": {"path": str(self.roots), "sha256": command.file_hash(self.roots)},
            "shutdown_binding": {"path": str(Path(__file__).resolve()), "sha256": command.file_hash(__file__)},
            "gpu_uuid": "GPU-CPU-TEST", "environment": self.fixture.environment,
            "expires_monotonic": self.clock() + 7200, "boot_id": command.lifecycle.boot_id(),
            "source_files": command.source_files()}
        self.spec_path = self.root / "spec.json"
        self.environment = patch.dict(os.environ, {**{name: "1" for name in command.OFFLINE}, "CUDA_VISIBLE_DEVICES": ""})
        self.environment.start()
        case.addCleanup(self.environment.stop)

    def prepare(self, stage="A2_DIRECT"):
        self.spec_path.write_bytes(command.canonical(self.spec) + b"\n")
        self.manifest = command.prepare(str(self.spec_path), command.file_hash(self.spec_path), str(self.output), stage,
            tokenizer_factory=lambda model: self.tokenizer, environment_reader=lambda: self.fixture.environment, clock=self.clock)
        self.path = self.output / "manifest.json"
        self.pin = command.file_hash(self.path)
        return self.manifest

    def actor(self, settings):
        if self.manifest["stage"] in command.driver.STRUCTURED_STAGES:
            return command.driver.InterfaceActor(settings, stage=self.manifest["stage"], roster=self.manifest["roster"],
                loader=lambda config: self.session, environment_reader=lambda: self.fixture.environment, clock=self.clock)
        return command.native.NativeActor(settings, loader=lambda config: self.session,
                                         environment_reader=lambda: self.fixture.environment, clock=self.clock)

    def run(self, stage="A2_DIRECT", default=False, backend_failure=False, shutdown_failure=False):
        self.prepare(stage)
        texts = []
        for task in self.manifest["roster"]["tasks"]:
            if command.driver.STAGES[stage]["thinks"]:
                texts.append("THINK Follow the supplied edges.")
            if command.driver.STAGES[stage]["reads"]:
                texts.append(next(query for query in task["queries"] if query.startswith("READ EVENTS_AT ")))
            if stage == "A1_READ_DISCLOSED" or stage in command.driver.STRUCTURED_STAGES:
                route = command.driver.core.oracle_route_v1(command.driver.core.from_data(task["cell"]), task["goal"])
                wrong = route.split(" : ")[0] + " : P_ZZZZZZZZZZ"
                score = command.driver.core.score_route(command.driver.core.from_data(task["cell"]), task["goal"], wrong)
                assert score["strict"] and not score["graph_success"]
                texts.append(wrong)
            else:
                texts.append("MISS")
        self.session = Session(self.tokenizer, self.clock, texts)
        self.session.backend_failure = backend_failure
        self.session.engine.fail = shutdown_failure
        arguments = dict(tokenizer_factory=lambda model: self.tokenizer,
                         environment_reader=lambda: self.fixture.environment, clock=self.clock)
        if default:
            actual = command.native.NativeActor
            def construct(settings):
                return actual(settings, loader=lambda config: self.session,
                              environment_reader=lambda: self.fixture.environment, clock=self.clock)
            with patch.object(command.native, "NativeActor", side_effect=construct) as selected:
                result = command.stage(str(self.path), self.pin, self.clock() + 1000, **arguments)
                selected.assert_called_once()
                self.selected_settings = selected.call_args.args[0]
                return result
        return command.stage(str(self.path), self.pin, self.clock() + 1000, actor_factory=self.actor, **arguments)


class CommandTests(unittest.TestCase):
    def setUp(self):
        self.harness = Harness(self)

    def test_default_actor_no_lora_complete_science_failure_exit_zero(self):
        result = self.harness.run(default=True)
        self.assertEqual(result["status"], "COMPLETE")
        self.assertEqual(result["summary"]["route_successes"], 0)
        self.assertFalse(result["summary"]["stage_gate_passed"])
        self.assertEqual(self.harness.selected_settings["engine"], command.native.ENGINE)
        self.assertFalse(self.harness.selected_settings["engine"]["enable_lora"])
        self.assertEqual(self.harness.selected_settings["max_calls"], 64)
        self.assertEqual(self.harness.session.engine.calls, 1)
        self.assertEqual(self.harness.session.closed, 1)
        with patch.object(command, "stage", return_value=result):
            self.assertEqual(command.main(["stage", "--manifest", str(self.harness.path), "--manifest-sha256", self.harness.pin,
                                           "--deadline", str(self.harness.clock() + 1000)]), 0)

    def test_a1_handshake_is_not_route_ceiling(self):
        result = self.harness.run("A1_READ_DISCLOSED")
        self.assertEqual(result["summary"]["denominator"], 64)
        self.assertEqual(result["summary"]["served_read_tasks"], 64)
        self.assertEqual(result["summary"]["invalid_read_tasks"], 0)
        self.assertEqual(result["summary"]["route_successes"], 0)
        self.assertTrue(result["summary"]["stage_gate_passed"])
        self.assertEqual(self.harness.manifest["actor_template"]["max_calls"], 832)

    def test_structured_default_factory_is_stage_bound(self):
        for stage in command.driver.STRUCTURED_STAGES:
            roster = {"stage": stage, "tasks": []}
            settings = {"fixture": True}
            with self.subTest(stage=stage), patch.object(command.driver, "InterfaceActor") as structured, \
                    patch.object(command.native, "NativeActor") as default:
                self.assertIs(command._actor(settings, roster), structured.return_value)
                structured.assert_called_once_with(settings, stage=stage, roster=roster)
                default.assert_not_called()
                injected = lambda config: config
                self.assertIs(command._actor(settings, roster, injected), settings)
                structured.assert_called_once()

    def test_both_structured_smokes_complete_replay_without_route_success(self):
        for stage in command.driver.STRUCTURED_STAGES:
            with self.subTest(stage=stage):
                self.harness.output = self.harness.root / stage
                result = self.harness.run(stage)
                self.assertEqual(result["status"], "COMPLETE")
                self.assertEqual(result["summary"]["denominator"], 8)
                self.assertEqual(result["actual_calls"], 16)
                self.assertEqual(result["possible_calls"], 104)
                self.assertEqual(result["summary"]["served_read_tasks"], 8)
                self.assertEqual(result["summary"]["route_successes"], 0)
                self.assertTrue(result["summary"]["stage_gate_passed"])
                self.assertFalse(result["full_assay_qualified"])
                actor_path = self.harness.output / stage / "actor"
                for index in range(16):
                    render = command.read(actor_path / f"call_{index:04d}.render.json")
                    self.assertEqual(set(render["sampling"]["structured_outputs"]), {"regex"})
                self.assertEqual(self.harness.session.engine.calls, 1)
                self.assertEqual(self.harness.session.closed, 1)

    def test_think_stages_complete_but_fail_threshold(self):
        for stage, maximum in (("A3_THINK", 448), ("ACTIVE_THINK", 1216)):
            with self.subTest(stage=stage):
                self.harness.output = self.harness.root / stage
                result = self.harness.run(stage)
                self.assertEqual(result["summary"]["thought_tasks"], 64)
                self.assertFalse(result["summary"]["stage_gate_passed"])
                self.assertEqual(self.harness.manifest["actor_template"]["max_calls"], maximum)

    def test_backend_failure_preserves_failed_report_and_closes(self):
        with self.assertRaisesRegex(ValueError, "infrastructure"):
            self.harness.run(backend_failure=True)
        directory = self.harness.output / "A2_DIRECT"
        self.assertEqual(command.read(directory / "records/report.json")["status"], "FAILED")
        self.assertEqual(command.read(directory / "failure.json")["usage_status"], "UNAVAILABLE_OR_PARTIAL_SEE_ORIGINAL_CAPTURES")
        self.assertTrue((directory / "failure.json").is_file())
        self.assertFalse((directory / "completed.json").exists())
        self.assertEqual(self.harness.session.engine.calls, 1)
        self.assertEqual(self.harness.session.closed, 1)

    def test_installed_shutdown_failure_is_infrastructure_failure(self):
        with self.assertRaisesRegex(RuntimeError, "shutdown failure"):
            self.harness.run(shutdown_failure=True)
        self.assertEqual(self.harness.session.closed, 1)
        self.assertTrue((self.harness.output / "A2_DIRECT/failure.json").is_file())
        self.assertFalse((self.harness.output / "A2_DIRECT/completed.json").exists())

    def test_missing_mutated_source_or_original_root_refuses_prepare(self):
        original = copy.deepcopy(self.harness.spec)
        cases = ("missing_source", "mutated_source", "roots", "root_hash", "shutdown", "boot", "environment", "expired", "extra")
        for name in cases:
            with self.subTest(name=name):
                self.harness.spec = copy.deepcopy(original)
                self.harness.output = self.harness.root / name
                spec = self.harness.spec
                if name == "missing_source": spec["source_files"].pop(str(Path(command.__file__).resolve()))
                elif name == "mutated_source": spec["source_files"][str(Path(command.__file__).resolve())] = "0" * 64
                elif name == "roots": spec["roots_file"]["path"] += ".missing"
                elif name == "root_hash": spec["roots_file"]["sha256"] = "0" * 64
                elif name == "shutdown": spec["shutdown_binding"]["sha256"] = "0" * 64
                elif name == "boot": spec["boot_id"] = "different"
                elif name == "environment": spec["environment"]["python"] = "/wrong/python"
                elif name == "expired": spec["expires_monotonic"] = 1
                else: spec["adapter"] = "/not/allowed"
                with self.assertRaises(ValueError): self.harness.prepare()

    def test_mutated_preserved_roots_and_prepared_roster_never_start(self):
        self.harness.prepare()
        for target in (self.harness.roots, self.harness.output / "roster.json"):
            previous = target.read_bytes()
            target.write_bytes(previous + b" ")
            with self.assertRaises(ValueError), patch.object(command.native, "NativeActor", side_effect=AssertionError("never start")):
                command.stage(str(self.harness.path), self.harness.pin, self.harness.clock() + 1000)
            target.write_bytes(previous)

    def test_fresh_prepare_and_stage_no_reuse(self):
        self.harness.run()
        original = (self.harness.output / "A2_DIRECT/completed.json").read_bytes()
        with self.assertRaises(FileExistsError): self.harness.prepare()
        with self.assertRaises(FileExistsError):
            command.stage(str(self.harness.path), self.harness.pin, self.harness.clock() + 1000)
        self.assertEqual((self.harness.output / "A2_DIRECT/completed.json").read_bytes(), original)

    def test_expired_or_unbounded_worker_deadline_never_loads(self):
        self.harness.prepare()
        for label, deadline in (("expired", self.harness.clock() - 1), ("unbounded", self.harness.clock() + 3600)):
            with self.subTest(label=label), patch.object(command.native, "NativeActor", side_effect=AssertionError("never start")):
                with self.assertRaisesRegex(ValueError, "deadline cap"):
                    command.stage(str(self.harness.path), self.harness.pin, deadline,
                                  tokenizer_factory=lambda model: self.harness.tokenizer,
                                  environment_reader=lambda: self.harness.fixture.environment, clock=self.harness.clock)
            if label == "expired":
                self.harness.output = self.harness.root / "second_prepared"
                self.harness.prepare()

    def test_injected_preparation_cannot_be_native_stage(self):
        self.harness.prepare()
        with self.assertRaisesRegex(ValueError, "test preparation"):
            command.stage(str(self.harness.path), self.harness.pin, self.harness.clock() + 1000)

    def test_offline_tokenizer_uses_only_local_untrusted_code_disabled(self):
        from unittest.mock import Mock
        tokenizer = Mock()
        with patch.dict(sys.modules, {"transformers": SimpleNamespace(AutoTokenizer=tokenizer)}):
            command._tokenizer("/synthetic/model")
        tokenizer.from_pretrained.assert_called_once_with("/synthetic/model", local_files_only=True, trust_remote_code=False)

    def test_all_64_initial_prompts_are_measured_and_last_oversize_rejects(self):
        original = command.driver._render
        seen = []
        def render(tokenizer, messages):
            text, tokens = original(tokenizer, messages)
            seen.append(messages)
            return text, [1] * 15000 if len(seen) == 64 else tokens
        with patch.object(command.driver, "_render", side_effect=render):
            with self.assertRaisesRegex(ValueError, "initial task context cap"):
                self.harness.prepare()
        self.assertEqual(len(seen), 64)
        self.assertFalse((self.harness.output / "manifest.json").exists())
        self.assertFalse((self.harness.output / "A2_DIRECT").exists())

    def test_native_custody_rejects_injected_and_load_close_count_drift(self):
        completed = self.harness.run()
        directory = self.harness.output / "A2_DIRECT"
        report = command.read(directory / "records/report.json")
        arguments = (directory, report, report["actor_config"])
        with self.assertRaisesRegex(ValueError, "NATIVE captures"):
            command._custody(*arguments, False, completed["started"], report["deadline"])
        for name, key, value in (("close.json", "token_count_calls", 1), ("close.json", "calls_consumed", 65),
                                 ("load.json", "ready_at", report["deadline"] + 1)):
            path = directory / "actor" / name
            original = path.read_bytes()
            changed = command.read(path)
            changed[key] = value
            path.write_bytes(command.canonical(changed))
            with self.assertRaises(ValueError):
                command._custody(*arguments, True, completed["started"], report["deadline"])
            path.write_bytes(original)
        self.assertEqual(completed["actual_calls"], 64)
        self.assertEqual(completed["possible_calls"], 64)
        self.assertEqual(completed["task_reasons"], {"INVALID_TURN": 64})

    def test_current_driver_source_and_original_root_file_are_pinned(self):
        manifest = self.harness.prepare()
        self.assertEqual(manifest["sources"][str(Path(command.driver.__file__).resolve())], command.file_hash(command.driver.__file__))
        self.assertEqual(manifest["spec"]["roots_file"]["sha256"], command.file_hash(self.harness.roots))
        self.assertEqual((self.harness.output / "roots.input.json").read_bytes(), self.harness.roots.read_bytes())
        self.assertEqual(len(command.read(self.harness.output / "measurements.json")), 64)


if __name__ == "__main__":
    unittest.main()
