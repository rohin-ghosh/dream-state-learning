"""CPU fixtures only; all allocation checks and detached processes are mocked."""
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
PATH = Path("/tmp/astra_launch_l2_public_record_20260913.py")
spec = importlib.util.spec_from_file_location("l2_launcher_cpu", PATH)
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)
RUNTIME = Path("/data/home/rohing/dream-state/gpu/astra_l2_public_record_dev.py")
PRECHECK = Path("/tmp/astra_node3_targeted_prelaunch_20260913.py")


class LauncherTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="l2_launcher_cpu_", dir="/tmp")
        self.addCleanup(temporary.cleanup)
        self.home = Path(temporary.name)
        self.root = self.home / "prepared"
        self.root.mkdir()
        self.source = self.home / "source"
        for name in launcher.SOURCE_NAMES:
            path = self.source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(RUNTIME.read_bytes() if name.startswith("gpu/") else b'"CPU source fixture; never imported"\n')
        self.driver = self.source / "gpu/astra_l2_public_record_dev.py"
        self.runtime = launcher.load_runtime(self.driver)
        self.precheck = self.home / "precheck.py"
        self.precheck.write_bytes(PRECHECK.read_bytes())
        self.model = self.home / "model"
        self.model.mkdir()
        records = {}
        for name in ("reflection", "public", "protocol", "model_binding"):
            path = self.home / (name + ".fixture")
            path.write_text("CPU fixture; must not execute")
            records[name] = dict(path=str(path), sha256=launcher.digest(path))
        self.specification = dict(schema=launcher.SCHEMA, core_schema=launcher.CORE_SCHEMA, source=str(self.source),
                                  source_files=self.runtime.tree(self.source), helpers={key: records[key] for key in ("reflection", "public")},
                                  model=str(self.model), model_binding=records["model_binding"], protocol=records["protocol"],
                                  gpu_index=3, gpu_uuid=launcher.GPU_UUID, lease_end=time.time() + 40000)
        self.spec_hash = self.runtime.value_hash(self.specification)
        launcher.write(self.root / "prepare_started.json", dict(spec_sha256=self.spec_hash, time=1))
        for name in ("calls.json", "world.json", "model_binding.json"):
            launcher.write(self.root / name, {"fixture": True})
        model_files = {"fixture": "a" * 64}
        self.plan = dict(schema=launcher.SCHEMA, spec=self.specification, spec_sha256=self.spec_hash, root=str(self.root),
                         python=os.path.abspath(sys.executable), python_sha256=launcher.digest(sys.executable),
                         model_files=model_files, base_sha256=self.runtime.value_hash(model_files),
                         seeds=self.runtime.SEEDS, config=dict(self.runtime.RECIPE, model=str(self.model)),
                         engine=self.runtime.ENGINE, params=self.runtime.PARAMS, stages=list(self.runtime.STAGES),
                         caps=self.runtime.CAPS, generic_system=self.runtime.GENERIC_SYSTEM, chat_template="CPU fixture",
                         environment={"fixture": True}, claim=self.runtime.CLAIM,
                         prepared_files={name: launcher.digest(self.root / name) for name in ("calls.json", "world.json", "model_binding.json")})
        launcher.write(self.root / "plan.json", self.plan)
        self.log = self.home / "controller.stdout"
        self.claim = self.root.with_name(self.root.name + ".launcher")
        self.options = SimpleNamespace(root=str(self.root), driver=str(self.driver), driver_sha256=launcher.RUNTIME_SHA256,
                                       plan_sha256=launcher.digest(self.root / "plan.json"), precheck=str(self.precheck),
                                       precheck_sha256=launcher.PRECHECK_SHA256, stdout=str(self.log), allow_gpu=True)
        self.initial = self.runtime.tree(self.root)
        self.process = Mock(pid=87654)
        self.run = self.patch(launcher.subprocess, "run", return_value=SimpleNamespace(returncode=0, stdout="vacant fixture", stderr=""))
        self.popen = self.patch(launcher.subprocess, "Popen", return_value=self.process)
        self.identity = self.patch(launcher, "process_identity", return_value=dict(pid=87654, pgid=87654, start_ticks=123456))

    def patch(self, target, name, **kwargs):
        patcher = patch.object(target, name, **kwargs)
        result = patcher.start()
        self.addCleanup(patcher.stop)
        return result

    def repin(self):
        (self.root / "plan.json").write_text(json.dumps(self.plan))
        self.options.plan_sha256 = launcher.digest(self.root / "plan.json")

    def test_success_exact_command_identity_budget_and_external_only_evidence(self):
        result = launcher.launch(self.options)
        self.assertEqual(result["status"], "LAUNCHED_NOT_SCIENTIFIC_RESULT")
        self.assertEqual((result["pid"], result["pgid"], result["start_ticks"]), (87654, 87654, 123456))
        self.assertEqual(result["command"], [self.plan["python"], "-B", str(self.driver), "controller", "--root",
                                           str(self.root), "--plan-sha256", self.options.plan_sha256, "--allow-gpu"])
        self.assertEqual((result["controller_seconds"], result["collection_seconds"], result["post_finish_margin_seconds"]),
                         (5400, 180, 21600))
        self.assertEqual(result["required_lease_seconds"], 27180)
        self.assertTrue(result["cleanup_included_in_controller"])
        self.assertFalse(result["collection_launched"])
        self.assertEqual(result["pins"]["source_files"], self.specification["source_files"])
        self.assertEqual(launcher.read(self.claim / "detached.json"), result)
        self.assertEqual(self.runtime.tree(self.root), self.initial)
        self.assertEqual(set(path.name for path in self.claim.iterdir()), {"started.json", "precheck.json", "detached.json"})
        kwargs = self.popen.call_args.kwargs
        self.assertEqual(kwargs["env"]["CUDA_VISIBLE_DEVICES"], launcher.GPU_UUID)
        self.assertEqual(kwargs["stdin"], subprocess.DEVNULL)
        self.assertEqual(kwargs["stderr"], subprocess.STDOUT)
        self.assertTrue(kwargs["start_new_session"])
        self.assertEqual(kwargs["cwd"], self.driver.parent)
        self.assertEqual(self.run.call_args.kwargs["env"]["CUDA_VISIBLE_DEVICES"], "")
        self.assertEqual(self.run.call_args.kwargs["timeout"], 60)
        self.assertEqual(self.run.call_args.args[0][-4:], ["--gpu-index", "3", "--gpu-uuid", launcher.GPU_UUID])

    def test_explicit_gpu_opt_in_required(self):
        self.options.allow_gpu = False
        with self.assertRaisesRegex(ValueError, "explicit --allow-gpu"):
            launcher.launch(self.options)
        self.run.assert_not_called()
        self.assertFalse(self.claim.exists())

    def test_all_prior_start_failure_terminal_and_witness_markers_rejected(self):
        for name in ("controller_started.json", "prepare_failure.json", "terminal.json", "SEAL.json", "FINALIZED.json",
                     "FINALIZATION_ABORT.json", "launcher_started.json", "extra.json", "run"):
            path = self.root / name
            path.mkdir() if name == "run" else path.write_text("prior fixture")
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "prior start, run, terminal or seal"):
                launcher.launch(self.options)
            path.rmdir() if name == "run" else path.unlink()
        self.run.assert_not_called()
        self.popen.assert_not_called()

    def test_fixed_runtime_precheck_and_plan_pins(self):
        for key in ("driver_sha256", "precheck_sha256", "plan_sha256"):
            old = getattr(self.options, key)
            setattr(self.options, key, "0" * 64)
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "pin differs"):
                launcher.launch(self.options)
            setattr(self.options, key, old)
        self.popen.assert_not_called()

    def test_exact_schema_gpu3_configuration_and_four_file_inventory(self):
        original = copy.deepcopy(self.plan)
        for kind in ("schema", "core", "gpu_index", "gpu_uuid", "seeds", "params", "recipe", "source_files", "extra_plan", "python"):
            self.plan = copy.deepcopy(original)
            if kind == "schema": self.plan["schema"] = "wrong"
            if kind == "core": self.plan["spec"]["core_schema"] = "wrong"
            if kind == "gpu_index": self.plan["spec"]["gpu_index"] = 2
            if kind == "gpu_uuid": self.plan["spec"]["gpu_uuid"] = "GPU-wrong"
            if kind == "seeds": self.plan["seeds"]["learner"] = False
            if kind == "params": self.plan["params"]["max_tokens"] = 192
            if kind == "recipe": self.plan["config"]["lr"] = .0001
            if kind == "source_files": self.plan["spec"]["source_files"].pop("organism_v6/train_adapter_v3.py")
            if kind == "extra_plan": self.plan["extra"] = True
            if kind == "python": self.plan["python_sha256"] = "0" * 64
            self.repin()
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                launcher.launch(self.options)
        self.run.assert_not_called()

    def test_source_helper_and_prepared_byte_drift_rejected(self):
        for path in (self.source / "organism_v6/l2_public_record_dev.py", Path(self.specification["helpers"]["public"]["path"]),
                     self.root / "world.json"):
            original = path.read_bytes()
            path.write_text("fixture drift")
            with self.subTest(path=path), self.assertRaises(ValueError):
                launcher.launch(self.options)
            path.write_bytes(original)
        self.run.assert_not_called()

    def test_existing_symlink_parent_and_root_overlap_stdout_rejected(self):
        self.log.write_text("old evidence")
        with self.assertRaisesRegex(ValueError, "existing stdout"):
            launcher.launch(self.options)
        self.assertEqual(self.log.read_text(), "old evidence")
        self.log.unlink()
        self.log.symlink_to(self.home / "missing")
        with self.assertRaisesRegex(ValueError, "symlink stdout"):
            launcher.launch(self.options)
        self.log.unlink()
        link = self.home / "link"
        link.symlink_to(self.home, target_is_directory=True)
        self.options.stdout = str(link / "new.log")
        with self.assertRaisesRegex(ValueError, "symlink stdout"):
            launcher.launch(self.options)
        for parent in (self.root, self.source, self.model):
            self.options.stdout = str(parent / "new.log")
            with self.assertRaisesRegex(ValueError, "overlapping stdout"):
                launcher.launch(self.options)
        self.run.assert_not_called()

    def test_external_claim_blocks_relaunch_with_different_stdout(self):
        launcher.launch(self.options)
        self.options.stdout = str(self.home / "different.log")
        with self.assertRaisesRegex(ValueError, "launch claim"):
            launcher.launch(self.options)
        self.assertEqual(self.popen.call_count, 1)
        self.assertEqual(self.runtime.tree(self.root), self.initial)

    def test_exact_finish_plus_six_hour_lease_boundary(self):
        now = 1000000.0
        with patch.object(launcher.time, "time", return_value=now):
            self.plan["spec"]["lease_end"] = now + 5400 + 180 + 21600 - .001
            self.repin()
            with self.assertRaisesRegex(ValueError, "margin after 5400"):
                launcher.launch(self.options)
            self.run.assert_not_called()
            self.plan["spec"]["lease_end"] = now + 5400 + 180 + 21600
            self.repin()
            result = launcher.launch(self.options)
        self.assertEqual(result["lease_end"] - result["launched_unix"] - 5580, 21600)

    def test_precheck_elapsed_time_rechecks_finish_margin(self):
        now = [1000000.0]
        self.plan["spec"]["lease_end"] = now[0] + 27181
        self.repin()
        def advance(*args, **kwargs):
            now[0] += 2
            return SimpleNamespace(returncode=0, stdout="vacant", stderr="")
        self.run.side_effect = advance
        with patch.object(launcher.time, "time", side_effect=lambda: now[0]), self.assertRaisesRegex(ValueError, "margin after 5400"):
            launcher.launch(self.options)
        self.popen.assert_not_called()
        self.assertTrue((self.claim / "failure.json").exists())

    def test_precheck_failure_keeps_all_evidence_outside_root(self):
        self.run.return_value.returncode = 1
        with self.assertRaisesRegex(ValueError, "precheck failed"):
            launcher.launch(self.options)
        self.assertEqual(launcher.read(self.claim / "precheck.json")["returncode"], 1)
        self.assertEqual(self.runtime.tree(self.root), self.initial)
        self.assertFalse(self.log.exists())
        self.popen.assert_not_called()

    def test_timeout_and_partial_output_preserved(self):
        self.run.side_effect = subprocess.TimeoutExpired("fixture", 60, output=b"partial", stderr=b"deadline")
        with self.assertRaises(subprocess.TimeoutExpired):
            launcher.launch(self.options)
        self.assertEqual(launcher.read(self.claim / "failure.json")["precheck_stdout"], "partial")
        self.assertEqual(self.runtime.tree(self.root), self.initial)
        self.popen.assert_not_called()

    def test_precheck_race_with_native_start_does_not_launch(self):
        def changed(*args, **kwargs):
            launcher.write(self.root / "controller_started.json", {"another_owner": True})
            return SimpleNamespace(returncode=0, stdout="vacant", stderr="")
        self.run.side_effect = changed
        with self.assertRaisesRegex(ValueError, "prior start"):
            launcher.launch(self.options)
        self.popen.assert_not_called()

    def test_precheck_race_with_source_edit_rechecks_pins(self):
        def changed(*args, **kwargs):
            (self.source / "organism_v6/train_adapter_v3.py").write_text("changed fixture")
            return SimpleNamespace(returncode=0, stdout="vacant", stderr="")
        self.run.side_effect = changed
        with self.assertRaisesRegex(ValueError, "snapshot inventory differs"):
            launcher.launch(self.options)
        self.popen.assert_not_called()

    def test_detachment_receipt_never_changes_root_even_if_controller_seals_immediately(self):
        after_seal = {}
        def sealed(*args, **kwargs):
            launcher.write(self.root / "terminal.json", {"mock_controller": True})
            launcher.write(self.root / "SEAL.json", {"mock_seal": True})
            after_seal.update(self.runtime.tree(self.root))
            return self.process
        self.popen.side_effect = sealed
        launcher.launch(self.options)
        self.assertEqual(self.runtime.tree(self.root), after_seal)
        self.assertTrue((self.claim / "detached.json").exists())

    def test_identity_failure_reports_pid_without_touching_sealed_root_or_relaunch(self):
        self.identity.side_effect = ProcessLookupError("fixture identity unavailable")
        with self.assertRaises(ProcessLookupError):
            launcher.launch(self.options)
        failure = launcher.read(self.claim / "failure.json")
        self.assertEqual(failure["pid"], 87654)
        self.assertTrue(failure["controller_may_be_running"])
        self.assertFalse((self.claim / "detached.json").exists())
        self.assertEqual(self.runtime.tree(self.root), self.initial)

    def test_concurrent_external_claim_is_exclusive_without_native_root_mutation(self):
        mkdir = Path.mkdir
        def competing(path, *args, **kwargs):
            if path == self.claim:
                mkdir(path, *args, **kwargs)
                launcher.write(path / "other-owner.json", {"owned": True})
            return mkdir(path, *args, **kwargs)
        with patch.object(Path, "mkdir", competing), self.assertRaises(FileExistsError):
            launcher.launch(self.options)
        self.assertEqual(launcher.read(self.claim / "other-owner.json"), {"owned": True})
        self.assertEqual(self.runtime.tree(self.root), self.initial)
        self.run.assert_not_called()
        self.popen.assert_not_called()

    def test_stdout_race_preserves_other_writer_evidence_and_refuses_spawn(self):
        def competing(*args, **kwargs):
            self.log.write_text("other owner's evidence")
            return SimpleNamespace(returncode=0, stdout="vacant", stderr="")
        self.run.side_effect = competing
        with self.assertRaisesRegex(ValueError, "existing stdout"):
            launcher.launch(self.options)
        self.assertEqual(self.log.read_text(), "other owner's evidence")
        self.assertEqual(self.runtime.tree(self.root), self.initial)
        self.popen.assert_not_called()

    def test_extra_source_file_or_hardlink_is_not_a_final_four_file_snapshot(self):
        extra = self.source / "extra.py"
        extra.write_text("unexpected fixture")
        with self.assertRaisesRegex(ValueError, "snapshot inventory differs"):
            launcher.launch(self.options)
        extra.unlink()
        os.link(self.source / "organism_v6/train_adapter_v3.py", self.home / "hardlink")
        with self.assertRaisesRegex(ValueError, "hardlinked artifact"):
            launcher.launch(self.options)
        self.run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
