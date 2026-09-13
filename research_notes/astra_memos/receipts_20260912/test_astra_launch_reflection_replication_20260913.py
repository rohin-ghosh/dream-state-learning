"""CPU mock tests only: no controller/helper/native/GPU/network/Git execution."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch


sys.dont_write_bytecode = True
PATH = Path("/tmp/astra_launch_reflection_replication_20260913.py")
spec = importlib.util.spec_from_file_location("reflection_replication_launcher_cpu", PATH)
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)


class LauncherTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="reflection_launch_cpu_", dir="/tmp")
        self.addCleanup(temporary.cleanup)
        self.home = Path(temporary.name)
        self.root = self.home / "prepared"
        self.root.mkdir()
        self.driver = self.home / "final_runtime.py"
        self.precheck = self.home / "final_precheck.py"
        self.driver.write_text("raise AssertionError('fixture runtime must never execute')\n")
        self.precheck.write_text("raise AssertionError('fixture precheck must never execute')\n")
        self.log = self.home / "controller.stdout"
        self.plan = dict(root=str(self.root), self_sha256=launcher.digest(self.driver),
                         python=os.path.abspath(sys.executable), scope=launcher.SCOPE, stages=launcher.STAGES,
                         learner_seed=1, config={"seed": 1}, parent_driver_sha256=launcher.PARENT_DRIVER_SHA256,
                         calls=144, outer_seconds=3600, collection_seconds=180, gpu_query_seconds=30,
                         fit_seconds=600, readout_seconds=300, lease_end=time.time() + 8 * 3600,
                         gpu_index=2, gpu_uuid="GPU-00000000-0000-0000-0000-000000000002",
                         source=str(self.home / "source"), model=str(self.home / "model"),
                         log_dir=str(self.home / "worker-logs"), probe_driver=str(self.home / "public_helper.py"))
        for key in ("source", "model", "log_dir"):
            Path(self.plan[key]).mkdir()
        Path(self.plan["probe_driver"]).write_text("fixture helper; never execute")
        launcher.write(self.root / "prepare_started.json", {"fixture": True})
        launcher.write(self.root / "plan.json", self.plan)
        self.options = SimpleNamespace(root=str(self.root), driver=str(self.driver), stdout=str(self.log),
                                       driver_sha256=launcher.digest(self.driver), plan_sha256=launcher.digest(self.root / "plan.json"),
                                       precheck=str(self.precheck), precheck_sha256=launcher.digest(self.precheck), allow_gpu=True, learner_seed=1)
        self.process = Mock(pid=87654)
        self.process.poll.return_value = None
        self.run = self.patch(launcher.subprocess, "run", return_value=SimpleNamespace(returncode=0, stdout='{"vacant":true}\n', stderr=""))
        self.popen = self.patch(launcher.subprocess, "Popen", return_value=self.process)
        self.identity = self.patch(launcher, "process_identity", return_value=dict(pid=87654, pgid=87654, start_ticks=123456))

    def patch(self, target, name, **kwargs):
        patcher = patch.object(target, name, **kwargs)
        value = patcher.start()
        self.addCleanup(patcher.stop)
        return value

    def repin_plan(self):
        (self.root / "plan.json").write_text(json.dumps(self.plan))
        self.options.plan_sha256 = launcher.digest(self.root / "plan.json")

    def assert_no_launch(self):
        self.run.assert_not_called()
        self.popen.assert_not_called()
        self.assertFalse(self.log.exists())

    def test_exact_detachment_identity_pins_commands_and_ceiling(self):
        receipt = launcher.launch(self.options)
        self.assertEqual(receipt["status"], "LAUNCHED_NOT_SCIENTIFIC_RESULT")
        self.assertEqual([receipt[key] for key in ("pid", "pgid", "start_ticks")], [87654, 87654, 123456])
        self.assertEqual(receipt["controller_seconds"], 3600)
        self.assertEqual(receipt["collection_seconds"], 180)
        self.assertEqual(receipt["cleanup_seconds"], 40)
        self.assertEqual(receipt["controller_work_seconds"], 3560)
        self.assertEqual(receipt["controller_and_separate_collection_seconds"], 3780)
        self.assertEqual(receipt["ceiling"], dict(controller_seconds=3600, cleanup_seconds=40,
                                                cleanup_included=True, collection_seconds=180, collection_separate=True))
        self.assertTrue(receipt["cleanup_included_in_controller"])
        self.assertFalse(receipt["collection_launched"])
        self.assertGreaterEqual(receipt["lease_margin_at_spawn_seconds"], 25420)
        self.assertEqual(receipt["finish_reserve_seconds"], 3820)
        self.assertEqual(receipt["required_lease_seconds"], 25420)
        self.assertEqual(receipt["reserved_finish_unix"] - receipt["launched_unix"], 3820)
        self.assertGreaterEqual(receipt["lease_margin_after_reserved_finish_seconds"], 21600)
        self.assertEqual(receipt["pins"]["precheck_sha256"], self.options.precheck_sha256)
        self.assertEqual(receipt["pins"]["launcher_sha256"], launcher.digest(PATH))
        self.assertEqual(launcher.read(self.root / "launcher_detached.json"), receipt)
        self.assertEqual(self.popen.call_args.args[0], receipt["command"])
        self.assertEqual(receipt["command"], [self.plan["python"], "-B", str(self.driver), "controller", "--root",
                                             str(self.root), "--plan-sha256", self.options.plan_sha256, "--allow-gpu"])
        kwargs = self.popen.call_args.kwargs
        self.assertTrue(kwargs["start_new_session"])
        self.assertEqual(kwargs["stdin"], subprocess.DEVNULL)
        self.assertEqual(kwargs["stderr"], subprocess.STDOUT)
        self.assertEqual(kwargs["cwd"], self.driver.parent)
        self.assertEqual(kwargs["env"]["CUDA_VISIBLE_DEVICES"], self.plan["gpu_uuid"])
        self.assertTrue(kwargs["stdout"].closed)
        self.assertEqual(self.log.stat().st_mode & 0o777, 0o600)
        self.run.assert_called_once()
        self.popen.assert_called_once()
        self.identity.assert_called_once_with(self.process)

    def test_precheck_fresh_empty_cuda_offline_and_bounded(self):
        with patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "FOREIGN", "HF_HUB_OFFLINE": "0"}):
            launcher.launch(self.options)
        args = self.run.call_args
        self.assertEqual(args.args[0], [self.plan["python"], "-B", str(self.precheck), "--gpu-index", "2",
                                      "--gpu-uuid", self.plan["gpu_uuid"]])
        self.assertEqual(args.kwargs["env"]["CUDA_VISIBLE_DEVICES"], "")
        self.assertEqual(args.kwargs["env"]["HF_HUB_OFFLINE"], "1")
        self.assertEqual(args.kwargs["timeout"], 60)
        self.assertTrue(args.kwargs["capture_output"])
        self.assertEqual(launcher.read(self.root / "launcher_precheck.json")["returncode"], 0)

    def test_explicit_opt_in_before_any_files_or_processes(self):
        self.options.allow_gpu = False
        with self.assertRaisesRegex(ValueError, "explicit --allow-gpu"):
            launcher.launch(self.options)
        self.assert_no_launch()
        self.assertFalse((self.root / "launcher_started.json").exists())

    def test_started_failed_completed_pending_and_empty_run_roots_refused(self):
        for name in ("controller_started.json", "prepare_failure.json", "controller_failure.json", "launcher_failure.json",
                     "launcher_started.json", "capture_complete.json", "launcher_detached.json", ".receipt.pending", "run"):
            marker = self.root / name
            marker.mkdir() if name == "run" else marker.write_text("fixture")
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "root forbidden"):
                launcher.launch(self.options)
            marker.rmdir() if name == "run" else marker.unlink()
        self.assert_no_launch()

    def test_existing_and_dangling_symlink_stdout_refused_without_overwrite(self):
        self.log.write_text("old evidence")
        with self.assertRaisesRegex(ValueError, "existing stdout"):
            launcher.launch(self.options)
        self.assertEqual(self.log.read_text(), "old evidence")
        self.log.unlink()
        self.log.symlink_to(self.home / "missing")
        with self.assertRaisesRegex(ValueError, "symlink stdout"):
            launcher.launch(self.options)
        self.assertTrue(self.log.is_symlink())
        self.run.assert_not_called()
        self.popen.assert_not_called()

    def test_symlink_parent_and_protected_overlap_refused(self):
        link = self.home / "link"
        link.symlink_to(self.home, target_is_directory=True)
        self.options.stdout = str(link / "new.log")
        with self.assertRaisesRegex(ValueError, "symlink stdout"):
            launcher.launch(self.options)
        for parent in (self.root, Path(self.plan["source"]), Path(self.plan["model"]), Path(self.plan["log_dir"])):
            self.options.stdout = str(parent / "new.log")
            with self.subTest(parent=parent), self.assertRaisesRegex(ValueError, "overlapping stdout"):
                launcher.launch(self.options)
        self.assert_no_launch()

    def test_all_three_final_pins_required(self):
        for name in ("driver_sha256", "plan_sha256", "precheck_sha256"):
            original = getattr(self.options, name)
            setattr(self.options, name, "0" * 64)
            with self.subTest(pin=name), self.assertRaisesRegex(ValueError, "pin changed"):
                launcher.launch(self.options)
            setattr(self.options, name, original)
        self.assert_no_launch()

    def test_wrong_scope_budgets_identity_and_interpreter_refused(self):
        original = copy.deepcopy(self.plan)
        for field, value in (("scope", "perception"), ("outer_seconds", 2700), ("collection_seconds", 181),
                             ("gpu_query_seconds", 20), ("fit_seconds", 601), ("readout_seconds", 301),
                             ("calls", 72), ("stages", []), ("root", "/tmp/wrong"), ("self_sha256", "a" * 64),
                             ("python", "/usr/bin/other-python"), ("gpu_index", True)):
            self.plan = dict(original, **{field: value})
            self.repin_plan()
            with self.subTest(field=field), self.assertRaises(ValueError):
                launcher.launch(self.options)
        self.assert_no_launch()

    def test_six_hour_lease_margin_not_merely_experiment_duration(self):
        for seconds in (3820, 21599, 21600, 25419):
            self.plan["lease_end"] = time.time() + seconds
            self.repin_plan()
            with self.assertRaisesRegex(ValueError, "six-hour"):
                launcher.launch(self.options)
        self.assert_no_launch()

    def test_precheck_failure_or_timeout_leaves_terminal_claim_no_spawn(self):
        self.run.return_value = SimpleNamespace(returncode=1, stdout="occupied", stderr="reservation")
        with self.assertRaisesRegex(ValueError, "precheck failed"):
            launcher.launch(self.options)
        self.assertTrue((self.root / "launcher_started.json").exists())
        self.assertTrue((self.root / "launcher_failure.json").exists())
        self.assertEqual(launcher.read(self.root / "launcher_precheck.json")["stdout"], "occupied")
        self.popen.assert_not_called()
        self.assertFalse(self.log.exists())
        with self.assertRaisesRegex(ValueError, "root forbidden"):
            launcher.launch(self.options)
        self.assertEqual(self.run.call_count, 1)

    def test_precheck_timeout_retains_partial_output(self):
        self.run.side_effect = subprocess.TimeoutExpired("fixture", 60, output=b"partial", stderr=b"timeout")
        with self.assertRaises(subprocess.TimeoutExpired):
            launcher.launch(self.options)
        failure = launcher.read(self.root / "launcher_failure.json")
        self.assertEqual(failure["precheck_stdout"], "partial")
        self.assertFalse(failure["controller_may_be_running"])
        self.popen.assert_not_called()

    def test_pin_mutation_during_precheck_refuses_spawn(self):
        def changed(*args, **kwargs):
            self.driver.write_text("fixture mutated")
            return SimpleNamespace(returncode=0, stdout="vacant", stderr="")
        self.run.side_effect = changed
        with self.assertRaisesRegex(ValueError, "pin changed"):
            launcher.launch(self.options)
        self.popen.assert_not_called()

    def test_lease_margin_rechecked_after_precheck(self):
        original = time.time()
        self.plan["lease_end"] = original + 25421
        self.repin_plan()
        with patch.object(launcher.time, "time", side_effect=[original, original, original, original + 3, original + 3]):
            with self.assertRaisesRegex(ValueError, "six-hour"):
                launcher.launch(self.options)
        self.popen.assert_not_called()
        self.run.assert_called_once()

    def test_exact_finish_plus_six_hour_lease_boundary(self):
        now = 1000000.0
        with patch.object(launcher.time, "time", return_value=now):
            self.plan["lease_end"] = now + 3600 + 180 + 40 + 21600 - .001
            self.repin_plan()
            with self.assertRaisesRegex(ValueError, "after reserved run finish"):
                launcher.launch(self.options)
            self.assert_no_launch()
            self.plan["lease_end"] = now + 3600 + 180 + 40 + 21600
            self.repin_plan()
            receipt = launcher.launch(self.options)
        self.assertEqual(receipt["lease_margin_after_reserved_finish_seconds"], 21600)
        self.assertEqual(receipt["lease_end"] - receipt["reserved_finish_unix"], 21600)

    def test_stdout_and_started_root_races_refused_after_precheck(self):
        def changed(*args, **kwargs):
            self.log.write_text("other owner's evidence")
            return SimpleNamespace(returncode=0, stdout="vacant", stderr="")
        self.run.side_effect = changed
        with self.assertRaisesRegex(ValueError, "existing stdout"):
            launcher.launch(self.options)
        self.assertEqual(self.log.read_text(), "other owner's evidence")
        self.popen.assert_not_called()

    def test_detached_root_cannot_launch_twice(self):
        launcher.launch(self.options)
        self.options.stdout = str(self.home / "another.log")
        with self.assertRaisesRegex(ValueError, "root forbidden"):
            launcher.launch(self.options)
        self.assertEqual(self.popen.call_count, 1)
        self.assertEqual(self.run.call_count, 1)

    def test_controller_start_during_precheck_refuses_second_controller(self):
        def changed(*args, **kwargs):
            launcher.write(self.root / "controller_started.json", {"fixture": True})
            return SimpleNamespace(returncode=0, stdout="vacant", stderr="")
        self.run.side_effect = changed
        with self.assertRaisesRegex(ValueError, "root forbidden"):
            launcher.launch(self.options)
        self.popen.assert_not_called()
        self.assertFalse(self.log.exists())

    def test_atomic_launch_claim_refuses_concurrent_claim_without_precheck(self):
        real_write = launcher.write
        def collision(path, value):
            if Path(path).name == "launcher_started.json":
                real_write(path, {"other_launch": True})
            return real_write(path, value)
        with patch.object(launcher, "write", side_effect=collision), self.assertRaises(FileExistsError):
            launcher.launch(self.options)
        self.assertEqual(launcher.read(self.root / "launcher_started.json"), {"other_launch": True})
        self.assert_no_launch()

    def test_failed_popen_preserves_log_and_failure(self):
        self.popen.side_effect = OSError("mock exec failure")
        with self.assertRaises(OSError):
            launcher.launch(self.options)
        self.assertTrue(self.log.exists())
        self.assertFalse(launcher.read(self.root / "launcher_failure.json")["controller_may_be_running"])
        self.assertFalse((self.root / "launcher_detached.json").exists())

    def test_uncertain_identity_reports_pid_never_fake_success_or_retry(self):
        self.identity.side_effect = ProcessLookupError("mock vanished controller")
        with self.assertRaises(ProcessLookupError):
            launcher.launch(self.options)
        failure = launcher.read(self.root / "launcher_failure.json")
        self.assertEqual(failure["pid"], self.process.pid)
        self.assertTrue(failure["controller_may_be_running"])
        self.assertFalse((self.root / "launcher_detached.json").exists())
        self.assertEqual(self.popen.call_count, 1)

    def test_proc_identity_parsing_checks_pid_pgid_session_ticks_and_liveness(self):
        fields = ["S", "1", "87654", "87654"] + ["0"] * 15 + ["123456"]
        actual = spec.loader.get_source(spec.name)
        namespace = {"__file__": str(PATH), "__name__": "identity_fixture"}
        exec(compile(actual, str(PATH), "exec"), namespace)
        identity = namespace["process_identity"]
        with patch.object(Path, "read_text", return_value="87654 (name with ) space) " + " ".join(fields)), \
                patch.object(os, "getpgid", return_value=87654):
            self.assertEqual(identity(self.process), dict(pid=87654, pgid=87654, start_ticks=123456))
            self.process.poll.return_value = 1
            with self.assertRaisesRegex(ValueError, "not live or isolated"):
                identity(self.process)


    def test_seed_selection_required_and_restricted_before_precheck(self):
        for seed in (None, 0, 3, True, 1.0, "1"):
            self.options.learner_seed = seed
            with self.subTest(seed=seed), self.assertRaisesRegex(ValueError, "integer 1 or 2"):
                launcher.launch(self.options)
        self.assert_no_launch()

    def test_seed1_cannot_launch_seed2_or_parent_root(self):
        self.plan["learner_seed"] = 2
        self.plan["config"]["seed"] = 2
        self.repin_plan()
        with self.assertRaisesRegex(ValueError, "selected learner seed"):
            launcher.launch(self.options)
        self.options.learner_seed = 2
        self.plan["parent_driver_sha256"] = "0" * 64
        self.repin_plan()
        with self.assertRaisesRegex(ValueError, "parent source"):
            launcher.launch(self.options)
        self.assert_no_launch()

    def test_seed2_receipts_preserve_selection_without_changing_controller_command(self):
        self.options.learner_seed = 2
        self.plan.update(learner_seed=2, config={"seed": 2})
        self.repin_plan()
        receipt = launcher.launch(self.options)
        self.assertEqual(receipt["learner_seed"], 2)
        self.assertEqual(receipt["parent_driver_sha256"], launcher.PARENT_DRIVER_SHA256)
        self.assertEqual(receipt["parent_launcher_sha256"], launcher.PARENT_LAUNCHER_SHA256)
        self.assertNotIn("--learner-seed", receipt["command"])
        for name in ("launcher_started.json", "launcher_precheck.json", "launcher_detached.json"):
            self.assertEqual(launcher.read(self.root / name)["learner_seed"], 2)
        self.assertEqual(receipt["required_lease_seconds"], 25420)

    def test_config_seed_type_strict_and_parent_launcher_unchanged(self):
        self.assertEqual(launcher.digest("/tmp/astra_launch_reflection_fit_20260913.py"), launcher.PARENT_LAUNCHER_SHA256)
        for seed in (True, 1.0, 2):
            self.plan["config"]["seed"] = seed
            self.repin_plan()
            with self.subTest(seed=seed), self.assertRaisesRegex(ValueError, "selected learner seed"):
                launcher.launch(self.options)
        self.assert_no_launch()


if __name__ == "__main__":
    unittest.main()
