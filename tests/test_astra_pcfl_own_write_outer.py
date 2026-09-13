"""Real harmless child sessions; synthetic manifests and injected GPU/CVD checks."""
import copy
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import venv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gpu import astra_pcfl_own_write_outer as outer

REAL_POPEN = subprocess.Popen
REAL_IDENTITY = outer.lifecycle.identity
CHILD = r'''
import hashlib, json, os, pathlib, signal, sys, time
root, stage, manifest_hash, mode = sys.argv[1:]
directory = pathlib.Path(root) / stage
directory.mkdir()
started = time.monotonic()
print("harmless stdout", flush=True)
print("harmless stderr", file=sys.stderr, flush=True)
(directory / "payload.txt").write_bytes(b"ORIGINAL STAGE BYTES\n")
if mode == "timeout":
    time.sleep(60)
if mode == "signal":
    os.kill(os.getpid(), signal.SIGTERM)
if mode == "missing":
    sys.exit(0)
if mode == "failure":
    (directory / "failure.json").write_text('{"error":"ORIGINAL FAILURE"}\n')
ended = time.monotonic()
receipt = dict(schema="pcfl.own_write.command.v1/completed", status="COMPLETE",
    manifest_sha256=manifest_hash, stage=stage, started=started, ended=ended,
    elapsed_seconds=ended-started, outer_release_required=True, gpu_released=False,
    files={path.name:hashlib.sha256(path.read_bytes()).hexdigest() for path in directory.iterdir()})
if mode == "wrongstage": receipt["stage"] = "different"
if mode == "wrongmanifest": receipt["manifest_sha256"] = "0" * 64
if mode == "future": receipt["ended"] += 2000
seal = lambda value: hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",",":"), ensure_ascii=False, allow_nan=False).encode()).hexdigest()
receipt["sha256"] = seal(receipt)
if mode == "badseal": receipt["status"] = "changed"
(directory / "completed.json").write_text(json.dumps(receipt) + "\n")
if mode == "drift": (directory / "payload.txt").write_text("changed")
if mode == "symlink": (directory / "alias").symlink_to(directory / "payload.txt")
sys.exit(7 if mode == "nonzero" else 0)
'''


class OwnWriteOuterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.venv_temporary = tempfile.TemporaryDirectory(prefix="SYNTHETIC_OWN_OUTER_VENV_")
        cls.addClassCleanup(cls.venv_temporary.cleanup)
        venv.EnvBuilder(with_pip=False).create(cls.venv_temporary.name)
        cls.python = str(Path(cls.venv_temporary.name) / "bin/python")

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="SYNTHETIC_OWN_OUTER_")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.stage_root = self.root / "stages"
        self.stage_root.mkdir()
        self.output = self.root / "outer"
        self.manifest_path, self.allocation_path = self.stage_root / "manifest.json", self.root / "allocation.json"
        self.source_hash = outer.lifecycle.file_hash(outer.__file__)
        self.manifest = {"schema": outer.command.SCHEMA + "/manifest", "root": str(self.stage_root),
            "kind": "OFFLINE_PREPARATION", "full_assay_qualified": False, "full_L8_qualified": False,
            "stage_seconds": 1800, "spec": {"gpu_uuid": "GPU-SYNTHETIC", "boot_id": outer.lifecycle.boot_id(),
                "expires_monotonic": time.monotonic() + 3600,
                "environment": {"native": {"python": str(Path(self.python).resolve())}}},
            "sources": {str(Path(path).resolve()):outer.lifecycle.file_hash(path)
                        for path in (outer.command.__file__, outer.command.readout_api.SCOPE)}}
        self.queue = self.root / "queue"
        for name in ("pending", "running"):
            (self.queue / name).mkdir(parents=True)
        self.allocation = {"schema": outer.lifecycle.SCHEMA + "/allocation", "gpu_index": 2,
            "gpu_uuid": "GPU-SYNTHETIC", "uid": os.getuid(), "boot_id": outer.lifecycle.boot_id(),
            "python": self.python, "queue_dir": str(self.queue), "queue_mode": "direct",
            "queue_allowlist": {"pending": {}, "running": {}}, "coordination_owners": [],
            "lease_end": time.time() + 30000, "lease_margin_seconds": 21600,
            "outer_sha256": self.source_hash, "service_exceptions": []}
        self.events, self.children = [], []
        self.mode = "complete"
        self.arm, self.stage = None, "formation"
        self.gpu_values = [{"empty": True, "gpu_uuid": "GPU-SYNTHETIC", "processes": []}] * 2
        self.cvd_values = [{"clear": True, "owners": [], "unresolved": [], "approved_unreadable_services": [],
                            "complete_cvd_visibility": True, "reservation_check_status": "PASS"}] * 2
        self.save()
        self.addCleanup(self.reap)
        self.stack = []
        for target, kwargs in (("sleep", {"side_effect": lambda seconds: self.events.append(("sleep", seconds))}),
                               ("subprocess.Popen", {"side_effect": self.spawn}),
                               ("lifecycle.check_gpu", {"side_effect": self.gpu}),
                               ("lifecycle.check_cvd", {"side_effect": self.cvd}),
                               ("lifecycle.controller", {"side_effect": AssertionError("no C0 controller")}),
                               ("lifecycle.finalize", {"side_effect": AssertionError("no C0 finalizer")})):
            mocked = patch("gpu.astra_pcfl_own_write_outer." + target, **kwargs)
            self.stack.append(mocked.start())
            self.addCleanup(mocked.stop)
        environment = patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": ""})
        environment.start()
        self.addCleanup(environment.stop)

    def save(self):
        self.manifest.pop("sha256", None)
        self.manifest["sha256"] = outer.command.digest(self.manifest)
        self.manifest_path.write_bytes(outer.command.canonical(self.manifest) + b"\n")
        self.allocation_path.write_bytes(outer.command.canonical(self.allocation) + b"\n")
        self.manifest_hash = outer.lifecycle.file_hash(self.manifest_path)
        self.allocation_hash = outer.lifecycle.file_hash(self.allocation_path)

    def reap(self):
        for child in self.children:
            if child.poll() is None:
                identity = REAL_IDENTITY(child.pid)
                self.assertEqual((identity["pid"], identity["pgid"], identity["sid"]), (child.pid,) * 3)
                os.killpg(child.pid, signal.SIGKILL)
            child.wait(timeout=5)

    def gpu(self, allocation, deadline):
        self.assertGreater(deadline, time.monotonic())
        self.events.append(("gpu", len(self.children)))
        value = self.gpu_values[bool(self.children)]
        if isinstance(value, Exception):
            raise value
        return copy.deepcopy(value)

    def cvd(self, allocation, deadline, *, release):
        self.assertTrue(release)
        self.events.append(("cvd", len(self.children)))
        return copy.deepcopy(self.cvd_values[bool(self.children)])

    def spawn(self, argv, **kwargs):
        self.assertEqual(self.events[0], ("sleep", 4))
        expected = [self.python, "-B", "-m", "gpu.astra_pcfl_own_write_command", self.stage,
                    "--manifest", str(self.manifest_path), "--manifest-sha256", self.manifest_hash]
        if self.arm is not None:
            expected += ["--arm", self.arm]
        self.assertEqual(argv, expected)
        self.assertTrue(kwargs["start_new_session"])
        self.assertEqual(kwargs["stdin"], subprocess.DEVNULL)
        self.assertEqual(kwargs["env"]["CUDA_VISIBLE_DEVICES"], "GPU-SYNTHETIC")
        self.assertEqual(kwargs["env"]["PYTHONPATH"], str(Path(outer.command.__file__).resolve().parents[1]))
        self.assertEqual(kwargs["cwd"], Path(kwargs["env"]["PYTHONPATH"]))
        self.assertTrue(all(kwargs["env"][key] == "1" for key in outer.command.OFFLINE))
        self.assertEqual((self.output / "manifest.input.json").read_bytes(), self.manifest_path.read_bytes())
        self.assertEqual((self.output / "allocation.input.json").read_bytes(), self.allocation_path.read_bytes())
        self.assertTrue((self.output / "context.json").is_file())
        stage_name = self.stage if self.stage != "readout" else "readout_" + self.arm
        child = REAL_POPEN([self.python, "-B", "-c", CHILD, str(self.stage_root), stage_name,
                            self.manifest["sha256"], self.mode], **kwargs)
        self.children.append(child)
        return child

    def run_controller(self):
        return outer.controller(str(self.manifest_path), self.manifest_hash, str(self.allocation_path),
                                self.allocation_hash, str(self.output), outer_sha256=self.source_hash,
                                stage=self.stage, arm=self.arm)

    def test_real_child_success_raw_bytes_and_actual_identity(self):
        result = self.run_controller()
        self.assertEqual(result["status"], "COMPLETED", result["errors"])
        self.assertEqual(result["returncode"], 0)
        self.assertEqual(result["worker_identity"]["pid"], self.children[0].pid)
        self.assertEqual(result["observations"]["worker_release"]["identity"], result["worker_identity"])
        self.assertTrue(result["observations"]["worker_release"]["owned_group_released"])
        self.assertEqual((self.output / "stage_completed.json").read_bytes(), (self.stage_root / "formation/completed.json").read_bytes())
        self.assertEqual((self.output / "stdout.log").read_text(), "harmless stdout\n")
        self.assertEqual((self.output / "stderr.log").read_text(), "harmless stderr\n")
        self.assertEqual([name for name, _ in self.events], ["sleep", "gpu", "cvd", "gpu", "cvd"])
        self.assertEqual(result, outer.command.read(self.output / "collection.json"))
        for name, entry in result["files"].items():
            self.assertEqual(outer.lifecycle.file_hash(self.output / name), entry["sha256"])
        self.assertFalse((self.output / "release_attestation.json").exists())

    def test_fit_argv_and_directory(self):
        self.stage = "fit"
        self.assertEqual(self.run_controller()["status"], "COMPLETED")
        self.assertTrue((self.stage_root / "fit/completed.json").exists())

    def test_readout_arm_binding(self):
        self.stage, self.arm = "readout", "NO_WRITE_C0"
        self.assertEqual(self.run_controller()["status"], "COMPLETED")
        self.assertTrue((self.stage_root / "readout_NO_WRITE_C0/completed.json").exists())

    def test_stage_and_arm_arguments_reject_before_writes(self):
        for stage, arm in (("prepare", None), ("readout", None), ("fit", "AUTH_WRITE"), ("readout", "UNKNOWN")):
            with self.subTest(stage=stage, arm=arm):
                self.stage, self.arm = stage, arm
                with self.assertRaises(ValueError):
                    self.run_controller()
                self.assertFalse(self.output.exists())

    def test_nonzero_with_completion_is_failed_and_release_still_checked(self):
        self.mode = "nonzero"
        result = self.run_controller()
        self.assertEqual((result["status"], result["returncode"]), ("FAILED", 7))
        self.assertTrue((self.output / "stage_completed.json").exists())
        self.assertTrue(result["observations"]["worker_release"]["owned_group_released"])
        self.assertIn("post_cvd", result["observations"])

    def test_real_timeout_signals_only_verified_child_and_reserves_cleanup(self):
        self.mode = "timeout"
        with patch.object(outer, "TOTAL_SECONDS", 60.15):
            result = self.run_controller()
        self.assertEqual(result["status"], "FAILED")
        self.assertTrue(any(error["type"] == "TimeoutExpired" for error in result["errors"]))
        exited = outer.command.read(self.output / "worker_exit.json")
        self.assertEqual(exited["signal"], signal.SIGTERM)
        self.assertTrue(any(event.get("signal") == signal.SIGTERM and event["pgid"] == self.children[0].pid for event in exited["events"]))
        self.assertIsNotNone(self.children[0].poll())
        self.assertIn("post_gpu", result["observations"])
        binding = outer.command.read(self.output / "binding.json")
        self.assertEqual(binding["deadline_monotonic"] - binding["worker_deadline_monotonic"], 60)

    def test_child_signal_is_preserved(self):
        self.mode = "signal"
        result = self.run_controller()
        self.assertEqual((result["status"], result["returncode"]), ("FAILED", -signal.SIGTERM))
        self.assertEqual(outer.command.read(self.output / "worker_exit.json")["signal"], signal.SIGTERM)

    def test_unknown_identity_never_calls_cleanup_or_kills_foreign(self):
        def identity(pid):
            if pid == os.getpid():
                return REAL_IDENTITY(pid)
            raise PermissionError("synthetic unreadable worker identity")
        with patch.object(outer.lifecycle, "identity", side_effect=identity), patch.object(outer.lifecycle, "cleanup_owned") as cleanup:
            result = self.run_controller()
        self.assertEqual(result["status"], "FAILED")
        self.assertIsNone(result["worker_identity"])
        cleanup.assert_not_called()
        self.assertIn("post_cvd", result["observations"])

    def test_foreign_group_candidate_never_authorizes_cleanup(self):
        def identity(pid):
            record = REAL_IDENTITY(pid)
            if pid != os.getpid():
                record["pgid"] = os.getpgrp()
            return record
        with patch.object(outer.lifecycle, "identity", side_effect=identity), patch.object(outer.lifecycle, "cleanup_owned") as cleanup:
            result = self.run_controller()
        self.assertEqual(result["status"], "FAILED")
        cleanup.assert_not_called()

    def test_failed_cleanup_cannot_pass_on_empty_gpu(self):
        with patch.object(outer.lifecycle, "cleanup_owned", side_effect=ValueError("identity reused; no signal")):
            result = self.run_controller()
        self.assertEqual(result["status"], "FAILED")
        self.assertIn("post_queue", result["observations"])
        self.assertIn("post_gpu", result["observations"])
        self.assertIn("post_cvd", result["observations"])

    def test_nonaffirmative_cleanup_receipt_fails(self):
        with patch.object(outer.lifecycle, "cleanup_owned", return_value={"owned_group_released": False}):
            self.assertEqual(self.run_controller()["status"], "FAILED")

    def test_post_gpu_error_does_not_skip_single_post_cvd(self):
        self.gpu_values[1] = RuntimeError("synthetic query error")
        result = self.run_controller()
        self.assertEqual(result["status"], "FAILED")
        self.assertEqual(self.events.count(("cvd", 1)), 1)
        self.assertTrue((self.output / "post_gpu.json").exists())
        self.assertIn("post_cvd", result["observations"])

    def test_post_cvd_unreadable_pid_fails_without_exception_expansion(self):
        self.cvd_values[1] = {**self.cvd_values[1], "clear": False, "unresolved": [{"pid": 99999, "error_type": "PermissionError"}]}
        result = self.run_controller()
        self.assertEqual(result["status"], "FAILED")
        self.assertEqual(result["observations"]["post_cvd"]["unresolved"][0]["pid"], 99999)

    def test_stage_completion_negative_guards_preserve_bytes(self):
        for mode in ("missing", "failure", "wrongstage", "wrongmanifest", "future", "badseal", "drift", "symlink"):
            with self.subTest(mode=mode):
                self.output = self.root / ("outer_" + mode)
                self.stage_root = self.root / ("stage_" + mode)
                self.stage_root.mkdir()
                self.manifest["root"] = str(self.stage_root)
                self.manifest_path = self.stage_root / "manifest.json"
                self.save()
                self.mode = mode
                result = self.run_controller()
                self.assertEqual(result["status"], "FAILED")
                if mode == "failure":
                    self.assertEqual((self.stage_root / "formation/failure.json").read_text(), '{"error":"ORIGINAL FAILURE"}\n')
                if (self.output / "stage_completed.json").exists():
                    self.assertEqual((self.output / "stage_completed.json").read_bytes(), (self.stage_root / "formation/completed.json").read_bytes())

    def test_manifest_allocation_and_self_file_pins(self):
        for attribute in ("manifest_hash", "allocation_hash", "source_hash"):
            with self.subTest(attribute=attribute):
                self.output = self.root / attribute
                original = getattr(self, attribute)
                setattr(self, attribute, "0" * 64)
                result = self.run_controller()
                setattr(self, attribute, original)
                self.assertEqual(result["status"], "FAILED")
                self.assertEqual(self.children, [])

    def test_pinned_but_wrong_manifest_bindings_never_spawn(self):
        mutations = [lambda: self.manifest["sources"].pop(str(Path(outer.command.__file__).resolve())),
            lambda: self.manifest["sources"].update({"/different/astra_pcfl_own_write_command.py": "0"*64}),
            lambda: self.manifest["sources"].pop(str(outer.command.readout_api.SCOPE.resolve())),
            lambda: self.manifest["spec"].update(gpu_uuid="GPU-WRONG"),
            lambda: self.manifest["spec"].update(boot_id="wrong"),
            lambda: self.manifest.update(kind="INJECTED_CPU_TEST"),
            lambda: self.manifest.update(full_assay_qualified=True),
            lambda: self.manifest.update(stage_seconds=3600),
            lambda: self.manifest["spec"]["environment"]["native"].update(python="/wrong/python"),
            lambda: self.allocation.update(outer_sha256="0"*64),
            lambda: self.allocation.update(uid=os.getuid()+1),
            lambda: self.allocation.update(lease_end=time.time()+21630),
            lambda: self.manifest["spec"].update(expires_monotonic=time.monotonic()+30)]
        original_manifest, original_allocation = copy.deepcopy(self.manifest), copy.deepcopy(self.allocation)
        for index, mutate in enumerate(mutations):
            with self.subTest(index=index):
                self.manifest, self.allocation = copy.deepcopy(original_manifest), copy.deepcopy(original_allocation)
                self.output = self.root / f"guard_{index}"
                mutate()
                self.save()
                self.assertEqual(self.run_controller()["status"], "FAILED")
                self.assertEqual(self.children, [])

    def test_nonempty_outer_cvd_and_busy_resource_reject(self):
        with patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "GPU-SYNTHETIC"}):
            self.assertEqual(self.run_controller()["status"], "FAILED")
        self.output = self.root / "busy_gpu"
        self.gpu_values[0] = {"empty": False, "gpu_uuid": "GPU-SYNTHETIC"}
        self.assertEqual(self.run_controller()["status"], "FAILED")
        self.assertEqual(self.children, [])

    def test_real_queue_drift_prevents_spawn(self):
        (self.queue / "pending/job.json").write_text("unexpected")
        self.assertEqual(self.run_controller()["status"], "FAILED")
        self.assertEqual(self.children, [])

    def test_fresh_outer_and_stage_are_never_reused(self):
        self.assertEqual(self.run_controller()["status"], "COMPLETED")
        original = (self.output / "collection.json").read_bytes()
        with self.assertRaises(FileExistsError):
            self.run_controller()
        self.assertEqual((self.output / "collection.json").read_bytes(), original)
        self.output = self.root / "retry"
        self.assertEqual(self.run_controller()["status"], "FAILED")
        self.assertEqual(len(self.children), 1)

    def test_output_cannot_overlap_input_or_source(self):
        for output in (self.stage_root / "outer", self.root, Path(outer.__file__).resolve().parent / "MUST_NOT_CREATE"):
            with self.subTest(output=output):
                self.output = output
                with self.assertRaises(ValueError):
                    self.run_controller()
        self.assertEqual(self.children, [])

    def test_detach_delay_is_inside_original_budget(self):
        actual_sleep = time.sleep
        with patch.object(outer, "sleep", side_effect=lambda seconds: (self.events.append(("sleep", seconds)), actual_sleep(seconds))):
            result = self.run_controller()
        self.assertEqual(result["status"], "COMPLETED")
        self.assertGreaterEqual(result["elapsed_seconds"], 4)
        context = outer.command.read(self.output / "context.json")
        binding = outer.command.read(self.output / "binding.json")
        self.assertEqual(binding["deadline_monotonic"], context["entry_monotonic"] + 1800)


if __name__ == "__main__":
    unittest.main()
