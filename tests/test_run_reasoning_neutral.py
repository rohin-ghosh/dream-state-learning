"""CPU fixtures for the evaluation wrapper, not actual GPU/process evidence."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from organism_v6 import run_reasoning_neutral as runner
from organism_v6.reasoning_neutral_probe import file_hashes, run_probe
from organism_v6.neutral_pair_custody import source_snapshot
from organism_v6.reasoning_gym_gym import BOOTSTRAP_PATH
from test_reasoning_neutral_probe import FixtureBackend, FixtureGym


class NeutralRunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.cleanup)
        environment = patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "0"})
        environment.start()
        self.addCleanup(environment.stop)
        self.root = Path(self.temp.name)
        for name in ("model", "adapter", "probes"):
            (self.root / name).mkdir()
        (self.root / "model/config.json").write_text("{}")
        (self.root / "adapter/adapter_config.json").write_text("{}")
        (self.root / "adapter/adapter_model.safetensors").write_bytes(b"CPU FIXTURE ONLY")
        self.families = self.root / "families.json"
        self.families.write_text("{}")
        self.spec_path = self.root / "spec.json"
        self.spec = dict(
            model_path=str(self.root / "model"), adapter_path=str(self.root / "adapter"),
            expected_model_hashes=file_hashes(self.root / "model"),
            expected_adapter_hashes=file_hashes(self.root / "adapter"),
            families_path=str(self.families), families_sha256=runner._digest(self.families),
            probe_root=str(self.root / "probes"), output_dir=str(self.root / "probes/pair"),
            training_life_roots=[str(self.root / "life")], lineage_roots=[str(self.root / "lineage")],
            episode_ids=["rg/heldout/1"], gen_seed=3, seed_salt=123, budget_ticks=1,
            wake_max_tokens=40, scratchpad_max_tokens=40, total_token_budget=80,
            max_episodes=1, max_model_len=256, worker_timeout_seconds=30, order=["off", "on"],
            panel_role="untouched_confirmation", selection_used_episode_ids=["rg/selection/1"])
        self.save_spec()

    def cleanup(self):
        for path in self.root.rglob("*"):
            if path.is_dir():
                path.chmod(0o755)
        self.temp.cleanup()

    def started(self):
        output = Path(self.spec["output_dir"])
        output.mkdir()
        runner._write(output / "PAIR_STARTED.json", dict(
            spec_sha256=self.digest, device="0", source_snapshot=source_snapshot()))
        return output

    def save_spec(self):
        self.spec_path.write_text(json.dumps(self.spec))
        self.digest = runner._digest(self.spec_path)

    def read(self):
        return runner.read_spec(self.spec_path, self.digest)

    def pair(self):
        return runner.run_pair(self.spec_path, self.digest, allow_gpu=True)

    def fake_worker(self, command, **kwargs):
        condition = command[command.index("--condition") + 1]
        output = Path(self.spec["output_dir"])
        child = output / condition
        gym = FixtureGym()
        gym._bootstrap = Path(BOOTSTRAP_PATH).read_text()
        options = {name: self.spec[name] for name in runner.PROBE_FIELDS}
        if condition == "off":
            options.update(adapter_path=None, expected_adapter_hashes={})
        model = FixtureBackend(options["model_path"], options["adapter_path"])
        run_probe(model, gym, output_dir=child, **options)
        runner._write(output / (condition + "_WORKER_DONE.json"), dict(
            evidence_label="EVALUATION_ONLY", spec_sha256=self.digest, condition=condition,
            pid=os.getpid() + (100 if condition == "off" else 200),
            device="0", multiprocessing="spawn",
            results_sha256=runner._digest(child / "results.json"),
            manifest_sha256=runner._digest(child / "manifest.json")))
        return os.getpid() + (100 if condition == "off" else 200)

    def test_preflight_and_model_hashes(self):
        self.assertEqual(self.read(), self.spec)
        (self.root / "model/config.json").write_text('{"changed": true}')
        with self.assertRaisesRegex(ValueError, "model digest"):
            self.read()

    def test_requires_explicit_gpu_opt_in(self):
        with patch.object(runner, "run_worker") as execute:
            with self.assertRaisesRegex(ValueError, "allow-gpu"):
                runner.run_pair(self.spec_path, self.digest)
            with self.assertRaisesRegex(ValueError, "allow-gpu"):
                runner.run_condition(self.spec_path, self.digest, "on")
        execute.assert_not_called()
        self.assertFalse(Path(self.spec["output_dir"]).exists())

    def test_fresh_worker_commands_and_bound_receipts(self):
        with patch.object(runner, "run_worker", side_effect=self.fake_worker) as execute:
            receipts = self.pair()
        self.assertEqual(list(receipts), ["off", "on"])
        self.assertEqual(execute.call_count, 2)
        for call in execute.call_args_list:
            self.assertIn("--allow-gpu", call.args[0])
            self.assertEqual(call.kwargs["timeout"], 30)
            self.assertEqual(call.kwargs["device"], "0")
        self.assertTrue((Path(self.spec["output_dir"]) / "PAIR_DONE.json").is_file())

    def test_declared_order_can_be_on_first(self):
        self.spec["order"] = ["on", "off"]
        self.save_spec()
        with patch.object(runner, "run_worker", side_effect=self.fake_worker):
            self.assertEqual(list(self.pair()), ["on", "off"])

    def test_confirmation_overlap_rejected(self):
        self.spec["selection_used_episode_ids"] = self.spec["episode_ids"]
        self.save_spec()
        with self.assertRaisesRegex(ValueError, "confirmation panel overlaps"):
            self.read()
        self.spec["panel_role"] = "exploratory"
        self.save_spec()
        self.read()

    def test_unknown_fields_and_false_budgets(self):
        original = dict(self.spec)
        for name, value in (("parent_context", "teacher"), ("budget_ticks", True),
                            ("order", ["off", "off"]), ("episode_ids", []),
                            ("max_episodes", 0), ("panel_role", "clean")):
            self.spec = original | {name: value}
            self.save_spec()
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.read()

    def test_spec_and_families_mutation_rejected(self):
        with self.assertRaisesRegex(ValueError, "spec digest"):
            runner.read_spec(self.spec_path, "0" * 64)
        self.families.write_text('{"changed": true}')
        with self.assertRaisesRegex(ValueError, "families digest"):
            self.read()

    def test_protected_directory_collision(self):
        self.spec["training_life_roots"] = [self.spec["output_dir"]]
        self.save_spec()
        with self.assertRaisesRegex(ValueError, "protected"):
            self.read()

    def test_existing_output_never_reused(self):
        output = Path(self.spec["output_dir"])
        output.mkdir()
        (output / "evidence").write_text("preserve")
        with patch.object(runner, "run_worker") as execute:
            with self.assertRaises(FileExistsError):
                self.pair()
        execute.assert_not_called()
        self.assertEqual((output / "evidence").read_text(), "preserve")

    def test_failed_worker_stops_before_second_condition(self):
        with patch.object(runner, "run_worker", side_effect=subprocess.CalledProcessError(2, "fixture")) as execute:
            with self.assertRaises(subprocess.CalledProcessError):
                self.pair()
        self.assertEqual(execute.call_count, 1)
        output = Path(self.spec["output_dir"])
        self.assertTrue((output / "PAIR_FAILED.json").exists())
        self.assertFalse((output / "PAIR_DONE.json").exists())

    def test_timeout_preserves_failed_run_and_no_retry(self):
        with patch.object(runner, "run_worker", side_effect=subprocess.TimeoutExpired("fixture", 30)) as execute:
            with self.assertRaises(subprocess.TimeoutExpired):
                self.pair()
        self.assertEqual(execute.call_count, 1)
        self.assertTrue((Path(self.spec["output_dir"]) / "PAIR_FAILED.json").exists())

    def test_missing_completion_receipt_rejected(self):
        with patch.object(runner, "run_worker", return_value=os.getpid() + 100):
            with self.assertRaisesRegex(ValueError, "missing evidence directory"):
                self.pair()
        self.assertFalse((Path(self.spec["output_dir"]) / "PAIR_DONE.json").exists())

    def test_changed_result_rejected(self):
        def changed(command, **kwargs):
            result = self.fake_worker(command, **kwargs)
            condition = command[command.index("--condition") + 1]
            path = Path(self.spec["output_dir"]) / condition / "results.json"
            path.chmod(0o644)
            path.write_text("changed")
            return result

        with patch.object(runner, "run_worker", side_effect=changed):
            with self.assertRaisesRegex(ValueError, "evidence digest"):
                self.pair()

    def test_previous_arm_mutation_is_rechecked_before_pair_done(self):
        def changed(command, **kwargs):
            result = self.fake_worker(command, **kwargs)
            condition = command[command.index("--condition") + 1]
            if condition == "on":
                path = Path(self.spec["output_dir"]) / "off/results.json"
                path.chmod(0o644)
                path.write_text("changed after first validation")
            return result

        with patch.object(runner, "run_worker", side_effect=changed):
            with self.assertRaisesRegex(ValueError, "evidence digest"):
                self.pair()
        self.assertFalse((Path(self.spec["output_dir"]) / "PAIR_DONE.json").exists())

    def test_condition_real_probe_with_cpu_backend(self):
        output = self.started()
        backend = FixtureBackend(self.spec["model_path"], self.spec["adapter_path"])
        with patch.dict(os.environ), \
                patch("organism_v6.model_backend.MODEL", self.spec["model_path"]), \
                patch("organism_v6.model_backend.VLLMBackend", return_value=backend), \
                patch("organism_v6.model_backend.close_backend", return_value=True) as close, \
                patch("organism_v6.reasoning_gym_gym.ReasoningGymGym", return_value=FixtureGym()):
            result = runner.run_condition(self.spec_path, self.digest, "on", allow_gpu=True)
        self.assertEqual(result["n_correct_grounded_scratchpads"], 1)
        close.assert_called_once_with(backend)
        self.assertTrue((output / "on_WORKER_DONE.json").exists())
        (output / "on").chmod(0o755)

    def test_close_failure_blocks_worker_completion(self):
        output = self.started()
        backend = FixtureBackend(self.spec["model_path"], None)
        with patch.dict(os.environ), \
                patch("organism_v6.model_backend.MODEL", self.spec["model_path"]), \
                patch("organism_v6.model_backend.VLLMBackend", return_value=backend), \
                patch("organism_v6.model_backend.close_backend", return_value=False), \
                patch("organism_v6.reasoning_gym_gym.ReasoningGymGym", return_value=FixtureGym()):
            with self.assertRaisesRegex(RuntimeError, "did not close"):
                runner.run_condition(self.spec_path, self.digest, "off", allow_gpu=True)
        self.assertFalse((output / "off_WORKER_DONE.json").exists())
        (output / "off").chmod(0o755)

    def test_constructor_failure_still_attempts_owned_cleanup(self):
        self.started()
        with patch.dict(os.environ), \
                patch("organism_v6.model_backend.MODEL", self.spec["model_path"]), \
                patch("organism_v6.model_backend.VLLMBackend", side_effect=RuntimeError("construction")), \
                patch("organism_v6.model_backend.close_backend", return_value=True) as close, \
                patch("organism_v6.reasoning_gym_gym.ReasoningGymGym", return_value=FixtureGym()):
            with self.assertRaisesRegex(RuntimeError, "construction"):
                runner.run_condition(self.spec_path, self.digest, "on", allow_gpu=True)
        close.assert_called_once_with(None)

    def test_reserved_device_must_be_explicit_and_unambiguous(self):
        for value in ("", "0,1", "-1", "GPU-unknown"):
            with self.subTest(value=value), patch.dict(os.environ, CUDA_VISIBLE_DEVICES=value):
                with self.assertRaisesRegex(ValueError, "reserved CUDA"):
                    self.pair()

    def test_gpu_process_query_fails_closed_and_sees_graphics(self):
        empty = "<nvidia_smi_log><gpu><processes/></gpu></nvidia_smi_log>"
        graphics = "<nvidia_smi_log><gpu><processes><process_info><type>G</type></process_info></processes></gpu></nvidia_smi_log>"
        for status, text, expected in ((0, empty, True), (0, graphics, False), (1, "", False),
                                       (0, "", False), (0, "<nvidia_smi_log><gpu/></nvidia_smi_log>", False)):
            response = subprocess.CompletedProcess([], status, stdout=text)
            with self.subTest(status=status, text=text), patch.object(runner.subprocess, "run", return_value=response):
                self.assertEqual(runner.gpu_processes_absent("0"), expected)

    def test_real_cpu_worker_timeout_kills_owned_child(self):
        pid_file = self.root / "child_pid"
        script = ("import subprocess,sys,time; from pathlib import Path; "
                  "child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)']); "
                  f"Path({str(pid_file)!r}).write_text(str(child.pid)); time.sleep(30)")
        log = self.root / "cpu.log"
        with patch.object(runner, "gpu_processes_absent", return_value=True):
            with self.assertRaises(subprocess.TimeoutExpired):
                runner.run_worker([sys.executable, "-c", script], log_path=log, timeout=1, device="0")
        cleanup = json.loads(log.with_suffix(".cleanup.json").read_text())
        self.assertTrue(cleanup["owned_group_empty"])
        self.assertTrue(cleanup["reservation_release_verified"])
        child_stat = Path("/proc") / pid_file.read_text() / "stat"
        if child_stat.exists():
            self.assertIn(child_stat.read_text().rsplit(")", 1)[1].split()[0], ("Z", "X"))

    def test_real_cpu_worker_failure_and_interrupt_are_cleaned(self):
        log = self.root / "failure.log"
        with patch.object(runner, "gpu_processes_absent", return_value=True):
            with self.assertRaises(subprocess.CalledProcessError):
                runner.run_worker([sys.executable, "-c", "raise RuntimeError('fixture')"],
                                  log_path=log, timeout=5, device="0")
        self.assertTrue(json.loads(log.with_suffix(".cleanup.json").read_text())["owned_group_empty"])
        original_popen = subprocess.Popen

        def interrupting_process(*args, **kwargs):
            process = original_popen(*args, **kwargs)
            original_wait = process.wait
            first = True

            def wait(*wait_args, **wait_kwargs):
                nonlocal first
                if first:
                    first = False
                    time.sleep(.1)
                    raise KeyboardInterrupt()
                return original_wait(*wait_args, **wait_kwargs)

            process.wait = wait
            return process

        log = self.root / "interrupt.log"
        with patch.object(runner.subprocess, "Popen", side_effect=interrupting_process), \
                patch.object(runner, "gpu_processes_absent", return_value=True):
            with self.assertRaises(KeyboardInterrupt):
                runner.run_worker([sys.executable, "-c", "import time; time.sleep(30)"],
                                  log_path=log, timeout=5, device="0")
        self.assertTrue(json.loads(log.with_suffix(".cleanup.json").read_text())["owned_group_empty"])


if __name__ == "__main__":
    unittest.main()
