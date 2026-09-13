"""Synthetic manifests/reports, fake /proc, mocked subprocesses; no GPU calls."""

import copy
import hashlib
import importlib.util
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from gpu import astra_pcfl_zero_fit_outer as outer


class FixtureTokenizer:
    chat_template = "SYNTHETIC_OUTER_TEST_ONLY"

    def encode(self, text, add_special_tokens=False):
        hashed = hashlib.sha256(text.encode()).digest()
        return [int.from_bytes(hashed[index:index + 4], "big") for index in range(0, 16, 4)]

    def apply_chat_template(self, messages, tokenize, add_generation_prompt):
        text = "".join("<|im_start|>" + message["role"] + "\n" + message["content"]
                       + "<|im_end|>\n" for message in messages) + "<|im_start|>assistant\n"
        return self.encode(text) if tokenize else text


def install_service_fixtures(test):
    cgroup = f"0::/user.slice/user-{test.allocation['uid']}.slice/user@{test.allocation['uid']}.service/init.scope\n"
    records = []
    for role, pid, parent, ticks, comm in (("user_manager", 900010, 1, 40, "systemd"),
                                          ("pam_helper", 900011, 900010, 41, "(sd-pam)")):
        test.process_record(pid, pgid=900010, sid=900010, ticks=ticks, ppid=parent)
        path = test.proc / str(pid)
        (path / "comm").write_bytes((comm + "\n").encode())
        (path / "cgroup").write_bytes(cgroup.encode())
        (path / "cmdline").write_bytes(("SYNTHETIC_METADATA_ONLY_" + role + "\0").encode())
        records.append({"role": role, "identity": outer.identity(pid), "ppid": parent,
                        "comm": comm, "cgroup": cgroup, "cmdline_sha256": outer.file_hash(path / "cmdline")})
    test.allocation["service_exceptions"] = records


class OuterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = outer.driver.build_tasks([outer.driver.core.to_data(outer.driver.core.build_root(f"excluded/{index}"))
                                            for index in range(4)])
        cls.construct = outer.driver._construct(cls.plan["roots"])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="pcfl_outer_cpu_")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.proc = self.root / "proc"
        (self.proc / "sys/kernel/random").mkdir(parents=True)
        (self.proc / "sys/kernel/random/boot_id").write_text("fixture-boot")
        self.process_record(os.getpid(), pgid=os.getpid(), sid=os.getpid(), ticks=100)
        self.out = self.root / "outer"
        self.output = self.root / "diagnostic"
        self.queue = self.root / "queue"
        for name in ("pending", "running"):
            (self.queue / name).mkdir(parents=True)
        self.allocation = {"schema": outer.SCHEMA + "/allocation", "gpu_index": 2,
                           "gpu_uuid": "GPU-FIXTURE", "boot_id": "fixture-boot", "uid": os.getuid(),
                           "python": str(Path(sys.executable).resolve()), "queue_dir": str(self.queue),
                           "queue_mode": "direct", "queue_allowlist": {"pending": {}, "running": {}},
                           "coordination_owners": [], "service_exceptions": [], "lease_end": time.time() + 10000,
                           "lease_margin_seconds": 100, "outer_sha256": outer.file_hash(outer.__file__)}
        tokenizer = FixtureTokenizer()
        source_files = outer.driver.source_snapshot()
        source_files[str(outer.COMMAND)] = outer.file_hash(outer.COMMAND)
        actor = {"schema": outer.driver.native.SCHEMA, "model_path": str(self.root / "model"),
                 "model_binding": {"path": str(self.root / "model_receipt.json"), "sha256": "1" * 64},
                 "source_files": source_files,
                 "tokenizer_files": {name: "2" * 64 for name in outer.driver.native.TOKENIZER_FILES},
                 "chat_template_sha256": outer.driver.core.byte_hash(tokenizer.chat_template),
                 "tokenizer_probe": {"text": "test only", "token_ids": tokenizer.encode("test only")},
                 "environment": {"python": self.allocation["python"], "version": "SYNTHETIC",
                                 "packages": {name: "SYNTHETIC" for name in outer.driver.native.PACKAGES}},
                 "gpu_uuid": "GPU-FIXTURE", "engine": copy.deepcopy(outer.driver.native.ENGINE),
                 "output_dir": str(self.output / "actor"), "deadline": time.monotonic() + 600,
                 "device_seconds_cap": 300, "max_input_tokens": 8192, "max_output_tokens": 2048, "max_calls": 1952}
        measurements = outer.driver.measure_tokenizer(self.plan, tokenizer, outer.driver.tokenizer_binding(actor), synthetic=True)
        measurements = outer.driver._seal({**outer.driver._unseal(measurements), "kind": "ACTUAL_OFFLINE"})
        self.manifest = outer.driver._seal({"schema": outer.driver.SCHEMA, "plan": self.plan,
            "measurements": measurements, "actor": actor, "sources": outer.driver.source_snapshot(),
            "construct": self.construct, "wall_seconds": 300, "device_seconds": 300,
            "output_dir": str(self.output), "test_only": False,
            "panels": {"delayed": {key: list(value) for key, value in outer.driver.runtime.DELAYED.items()},
                       "reachout": {key: list(value) for key, value in outer.driver.runtime.REACHOUT.items()}},
            "full_v22_release": False, "fits": 0, "updates": 0})
        self.manifest_path = self.root / "manifest.json"
        self.allocation_path = self.root / "allocation.json"
        self.save_inputs()
        self.compute = ""
        self.gpu_uuid = "GPU-FIXTURE"
        self.mode = "success"
        self.waits = 0
        self.fake_process = SimpleNamespace(pid=900001, returncode=None, wait=self.wait)
        patches = [patch.object(outer, "PROC", self.proc), patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": ""}),
                   patch.object(outer.subprocess, "Popen", side_effect=self.spawn),
                   patch.object(outer.subprocess, "run", side_effect=self.query),
                   patch.object(outer.os, "killpg", side_effect=self.kill)]
        self.mocks = [item.start() for item in patches]
        for item in patches:
            self.addCleanup(item.stop)

    def process_record(self, pid, *, pgid, sid, ticks, ppid=1, cvd=""):
        directory = self.proc / str(pid)
        directory.mkdir(exist_ok=True)
        fields = ["S", str(ppid), str(pgid), str(sid)] + ["0"] * 15 + [str(ticks)]
        (directory / "stat").write_text(f"{pid} (synthetic cpu fixture) " + " ".join(fields))
        (directory / "environ").write_bytes(b"CUDA_VISIBLE_DEVICES=" + cvd.encode() + b"\0")

    def save_inputs(self):
        self.manifest_path.write_bytes(outer.driver.canonical(self.manifest))
        self.allocation_path.write_bytes(outer.driver.canonical(self.allocation))
        self.manifest_sha = outer.file_hash(self.manifest_path)
        self.allocation_sha = outer.file_hash(self.allocation_path)

    def query(self, command, **kwargs):
        self.assertGreater(kwargs["timeout"], 0)
        self.assertLessEqual(kwargs["timeout"], 10)
        stdout = f"2, {self.gpu_uuid}\n" if command[1].startswith("--query-gpu=") else self.compute
        return SimpleNamespace(returncode=0, stdout=stdout, stderr="")

    def spawn(self, command, **kwargs):
        self.assertTrue(kwargs["start_new_session"])
        self.assertEqual(kwargs["env"]["CUDA_VISIBLE_DEVICES"], "GPU-FIXTURE")
        self.assertEqual(command[-4:], ["--manifest", str(self.manifest_path), "--manifest-sha256", self.manifest_sha])
        kwargs["stdout"].write(b"synthetic child stdout\n")
        kwargs["stderr"].write(b"synthetic child stderr\n")
        self.process_record(900001, pgid=900001, sid=900001, ticks=500, cvd="GPU-FIXTURE")
        return self.fake_process

    def wait(self, timeout):
        self.assertGreater(timeout, 0)
        self.waits += 1
        if self.waits == 1:
            if self.mode in ("timeout", "reused"):
                if self.mode == "reused":
                    self.process_record(900001, pgid=900001, sid=900001, ticks=999, cvd="GPU-FIXTURE")
                raise subprocess.TimeoutExpired("SYNTHETIC WORKER", timeout)
            self.write_report()
            shutil.rmtree(self.proc / "900001")
            self.fake_process.returncode = True if self.mode == "boolrc" else 3 if self.mode == "nonzero" else 0
        return self.fake_process.returncode

    def kill(self, pgid, action):
        self.assertEqual(pgid, 900001)
        self.assertIn(action, (signal.SIGTERM, signal.SIGKILL))
        shutil.rmtree(self.proc / str(pgid))
        self.fake_process.returncode = -int(action)

    def write_report(self):
        self.output.mkdir()
        report = {"schema": outer.driver.SCHEMA + "/report", "manifest_sha256": self.manifest["sha256"],
                  "actor_config_sha256": outer.driver.digest(self.manifest["actor"]),
                  "source_files_sha256": outer.driver.digest(self.manifest["sources"]),
                  "tokenizer_measurements_sha256": self.manifest["measurements"]["sha256"],
                  "test_only": False, "status": "COMPLETE_AWAITING_OUTER_RELEASE", "diagnostic_usable": False,
                  "full_v22_release": False, "fits": 0, "updates": 0, "tasks": 800, "scored_tasks": 800,
                  "actor_attempts": 800, "actor_responses": 800,
                  "results": [{"id": task["id"], "execution": "SCORED", "success": False} for task in self.plan["tasks"]],
                  "panels": {}, "thresholds_passed": False, "error": None,
                  "backend_close": {"kind": "NATIVE", "error_type": None, "failed": False,
                                    "budget_exceeded": False, "calls_consumed": 800,
                                    "owned_group_released": None, "gpu_vacant": None},
                  "wall_seconds_through_close": 0, "started_monotonic": time.monotonic(),
                  "gpu_uuid": "GPU-FIXTURE", "wall_cap": 300, "device_cap": 300}
        outer.write(self.output / "report.json", outer.driver._seal(report))

    def run_controller(self):
        return outer.controller(str(self.manifest_path), self.manifest_sha, str(self.allocation_path),
                                self.allocation_sha, str(self.out), cleanup_seconds=120)

    def test_capture_then_actual_finalizer_and_crosslinks(self):
        captured = self.run_controller()
        self.assertTrue(captured["worker_group_released"])
        self.assertTrue(captured["reservation_released"])
        self.assertFalse(captured["finalized"])
        original = (self.output / "report.json").read_bytes()
        collected = outer.finalize(str(self.out), captured["capture_file_sha256"])
        attestation = outer.read(self.out / "release_attestation.json")
        self.assertEqual(set(attestation), {"report_sha256", "gpu_uuid", "owned_group_released", "gpu_vacant", "elapsed_seconds_from_start"})
        final = outer.read(self.out / "final.json")
        self.assertTrue(final["diagnostic_usable"])
        self.assertFalse(final["report"]["thresholds_passed"])
        self.assertFalse(final["full_v22_release"])
        self.assertEqual(original, (self.output / "report.json").read_bytes())
        for name, digest in collected["files"].items():
            self.assertEqual(outer.file_hash(self.out / name), digest)
        self.assertGreaterEqual(collected["outer_elapsed_seconds"], attestation["elapsed_seconds_from_start"])
        self.assertEqual(self.mocks[2].call_count, 1)
        self.mocks[4].assert_not_called()

    def holder(self):
        self.process_record(900002, pgid=900002, sid=900002, ticks=50, cvd="2")
        self.process_record(os.getpid(), pgid=os.getpid(), sid=os.getpid(), ticks=100, ppid=900002)
        self.allocation["coordination_owners"] = [outer.identity(900002)]
        self.save_inputs()

    def test_remaining_exact_ancestor_is_not_unreserved(self):
        self.holder()
        captured = self.run_controller()
        self.assertTrue(captured["gpu_compute_vacant"])
        self.assertFalse(captured["reservation_released"])
        scan = outer.read(self.out / "post_worker_cvd.json")["value"]
        self.assertEqual(scan["excluded_own_ancestors"][0]["identity"], self.allocation["coordination_owners"][0])
        with self.assertRaisesRegex(ValueError, "CVD owner remains"):
            outer.finalize(str(self.out), captured["capture_file_sha256"])
        self.assertFalse((self.out / "final.json").exists())
        self.assertTrue((self.out / "finalize_failure.json").exists())

    def test_holder_removal_before_single_finalization(self):
        self.holder()
        captured = self.run_controller()
        self.process_record(os.getpid(), pgid=os.getpid(), sid=os.getpid(), ticks=100)
        shutil.rmtree(self.proc / "900002")
        outer.finalize(str(self.out), captured["capture_file_sha256"])
        self.assertTrue((self.out / "collection.json").exists())

    def test_arbitrary_cvd_exclusion_refused(self):
        self.process_record(900002, pgid=900002, sid=900002, ticks=50, cvd="GPU-FIXTURE")
        self.allocation["coordination_owners"] = [outer.identity(900002)]
        self.save_inputs()
        with self.assertRaisesRegex(ValueError, "exact own ancestor"):
            self.run_controller()
        self.mocks[2].assert_not_called()

    def test_foreign_cvd_precheck_no_spawn_or_kill(self):
        self.process_record(900002, pgid=900002, sid=900002, ticks=50, cvd="GPU-FIXTURE")
        with self.assertRaisesRegex(ValueError, "CVD reservation"):
            self.run_controller()
        self.mocks[2].assert_not_called()
        self.mocks[4].assert_not_called()
        self.assertTrue((self.out / "controller_failure.json").exists())

    def test_nonempty_gpu_no_spawn(self):
        self.compute = "GPU-FIXTURE, 888\n"
        with self.assertRaisesRegex(ValueError, "GPU occupied"):
            self.run_controller()
        self.mocks[2].assert_not_called()

    def test_wrong_uuid_no_spawn(self):
        self.gpu_uuid = "GPU-OTHER"
        with self.assertRaisesRegex(ValueError, "GPU occupied"):
            self.run_controller()
        self.mocks[2].assert_not_called()

    def test_queue_requires_exact_managed_coordination(self):
        job = self.queue / "running" / "own.job"
        job.write_bytes(b"SYNTHETIC MAIN QUEUE RECORD")
        self.allocation["queue_mode"] = "managed"
        self.allocation["queue_allowlist"]["running"]["own.job"] = outer.file_hash(job)
        self.save_inputs()
        captured = self.run_controller()
        job.unlink()
        outer.finalize(str(self.out), captured["capture_file_sha256"])

    def test_uncoordinated_queue_no_spawn(self):
        (self.queue / "pending" / "other.job").write_text("SYNTHETIC")
        with self.assertRaisesRegex(ValueError, "queue coordination"):
            self.run_controller()
        self.mocks[2].assert_not_called()

    def test_timeout_only_signals_verified_owned_group(self):
        self.mode = "timeout"
        self.process_record(900003, pgid=900003, sid=900003, ticks=50)
        with self.assertRaises(subprocess.TimeoutExpired):
            self.run_controller()
        self.mocks[4].assert_called_once_with(900001, signal.SIGTERM)
        self.assertTrue((self.proc / "900003").exists())
        self.assertTrue((self.out / "worker_release.json").exists())
        self.assertTrue((self.out / "post_worker_gpu.json").exists())
        self.assertEqual(outer.read(self.out / "worker_wait.json")["error_type"], "TimeoutExpired")
        self.assertIn(b"synthetic child stderr", (self.out / "stderr.log").read_bytes())
        self.assertFalse((self.out / "capture_complete.json").exists())

    def test_reused_pid_never_signaled(self):
        self.mode = "reused"
        with self.assertRaisesRegex(ValueError, "identity changed/reused"):
            self.run_controller()
        self.mocks[4].assert_not_called()
        self.assertTrue((self.out / "cleanup_failure.json").exists())
        self.assertTrue((self.out / "worker_wait.json").exists())

    def test_bool_returncode_is_not_success(self):
        self.mode = "boolrc"
        with self.assertRaisesRegex(ValueError, "invalid exit"):
            self.run_controller()
        self.assertIs(outer.read(self.out / "worker_exit.json")["returncode"], True)
        self.assertTrue((self.output / "report.json").exists())
        self.assertFalse((self.out / "capture_complete.json").exists())

    def test_nonzero_preserves_outputs_without_finalization(self):
        self.mode = "nonzero"
        with self.assertRaisesRegex(ValueError, "worker nonzero"):
            self.run_controller()
        self.assertEqual(outer.read(self.out / "worker_exit.json")["returncode"], 3)
        self.assertTrue((self.output / "report.json").exists())

    def test_manifest_drift_no_spawn(self):
        self.manifest_path.write_bytes(self.manifest_path.read_bytes() + b"\n")
        with self.assertRaisesRegex(ValueError, "manifest file changed"):
            self.run_controller()
        self.mocks[2].assert_not_called()

    def test_outer_source_pin_no_spawn(self):
        self.allocation["outer_sha256"] = "0" * 64
        self.save_inputs()
        with self.assertRaisesRegex(ValueError, "outer source changed"):
            self.run_controller()
        self.mocks[2].assert_not_called()

    def test_expired_prepared_deadline_no_spawn(self):
        self.manifest["actor"]["deadline"] = time.monotonic() - 1
        self.save_inputs()
        with self.assertRaisesRegex(ValueError, "deadline exhausted"):
            self.run_controller()
        self.mocks[2].assert_not_called()

    def test_original_output_cannot_be_reopened(self):
        self.output.mkdir()
        (self.output / "sentinel").write_bytes(b"preserve")
        with self.assertRaisesRegex(ValueError, "fresh output"):
            self.run_controller()
        self.assertEqual((self.output / "sentinel").read_bytes(), b"preserve")
        self.mocks[2].assert_not_called()

    def test_output_drift_blocks_single_finalization(self):
        captured = self.run_controller()
        (self.output / "report.json").write_bytes((self.output / "report.json").read_bytes() + b"\n")
        with self.assertRaisesRegex(ValueError, "captured output changed"):
            outer.finalize(str(self.out), captured["capture_file_sha256"])
        with self.assertRaises(FileExistsError):
            outer.finalize(str(self.out), captured["capture_file_sha256"])
        self.assertFalse((self.out / "final.json").exists())

    def test_no_second_controller_even_new_outer_directory(self):
        self.run_controller()
        with self.assertRaises(FileExistsError):
            self.run_controller()
        self.assertEqual(self.mocks[2].call_count, 1)

    def test_capture_pin_and_late_total_cap_fail(self):
        captured = self.run_controller()
        deadline = outer.read(self.out / "context.json")["deadline_monotonic"]
        with patch.object(outer.time, "monotonic", return_value=deadline + 1):
            with self.assertRaisesRegex(ValueError, "deadline exhausted"):
                outer.finalize(str(self.out), captured["capture_file_sha256"])
        self.assertFalse((self.out / "final.json").exists())

    def test_gpu_query_timeout_retains_raw_without_spawn(self):
        self.mocks[3].side_effect = subprocess.TimeoutExpired("nvidia-smi", 10, output=b"partial", stderr=b"timeout")
        with self.assertRaisesRegex(ValueError, "GPU occupied"):
            self.run_controller()
        capture = outer.read(self.out / "preflight_gpu.json")["value"]
        self.assertEqual(capture["queries"][0]["stdout"], "partial")
        self.mocks[2].assert_not_called()

    def test_boot_change_after_capture_blocks_release(self):
        captured = self.run_controller()
        (self.proc / "sys/kernel/random/boot_id").write_text("other-boot")
        with self.assertRaisesRegex(ValueError, "boot/UID changed"):
            outer.finalize(str(self.out), captured["capture_file_sha256"])
        self.mocks[4].assert_not_called()

    def test_cleanup_reserve_bounded(self):
        for seconds in (True, 0, 29, 121):
            with self.subTest(seconds=seconds), self.assertRaisesRegex(ValueError, "30..120"):
                outer.controller(str(self.manifest_path), self.manifest_sha, str(self.allocation_path),
                                 self.allocation_sha, str(self.out), cleanup_seconds=seconds)
        self.mocks[2].assert_not_called()

    def test_import_performs_no_launch_or_hardware_query(self):
        spec = importlib.util.spec_from_file_location("outer_import_fixture", outer.__file__)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.mocks[2].assert_not_called()
        self.mocks[3].assert_not_called()
        self.mocks[4].assert_not_called()

    def test_missing_start_identity_keeps_failure_without_blind_kill(self):
        original = Path.read_text
        def read_text(path, *args, **kwargs):
            if path == self.proc / "900001/stat":
                raise PermissionError("synthetic inaccessible start identity")
            return original(path, *args, **kwargs)
        with patch.object(Path, "read_text", read_text):
            with self.assertRaises(ValueError):
                self.run_controller()
        self.mocks[4].assert_not_called()
        self.assertEqual(outer.read(self.out / "worker_error.json")["type"], "PermissionError")
        self.assertFalse(outer.read(self.out / "controller_failure.json")["identity_verified"])
        self.assertTrue((self.out / "cleanup_failure.json").exists())
        self.assertFalse((self.out / "capture_complete.json").exists())

    def test_capture_file_pin_refused_once(self):
        self.run_controller()
        with self.assertRaisesRegex(ValueError, "capture completion changed"):
            outer.finalize(str(self.out), "0" * 64)
        self.assertFalse((self.out / "final.json").exists())

    def test_new_queue_entry_at_release_is_not_ignored(self):
        captured = self.run_controller()
        (self.queue / "pending" / "late.job").write_text("SYNTHETIC LATE JOB")
        with self.assertRaisesRegex(ValueError, "new queue coordination"):
            outer.finalize(str(self.out), captured["capture_file_sha256"])
        self.assertTrue((self.out / "final_queue.json").exists())

    def test_outer_cvd_must_be_empty(self):
        with patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "GPU-FIXTURE"}):
            with self.assertRaisesRegex(ValueError, "explicitly empty CVD"):
                self.run_controller()
        self.mocks[2].assert_not_called()

    def test_gpu_query_boolean_rc_is_not_success(self):
        self.mocks[3].side_effect = None
        self.mocks[3].return_value = SimpleNamespace(returncode=False, stdout="2, GPU-FIXTURE\n", stderr="")
        with self.assertRaisesRegex(ValueError, "GPU occupied"):
            self.run_controller()
        self.mocks[2].assert_not_called()

    def test_ratified_service_exception_capture_and_finalizer_visibility(self):
        install_service_fixtures(self)
        self.save_inputs()
        original = Path.read_bytes
        denied = {self.proc / str(pid) / "environ" for pid in (900010, 900011)}
        def read_bytes(path):
            if path in denied:
                raise PermissionError("SYNTHETIC UNREADABLE INIT ENVIRONMENT")
            return original(path)
        with patch.object(Path, "read_bytes", read_bytes):
            captured = self.run_controller()
            self.assertIsNone(captured["reservation_released"])
            self.assertFalse(captured["complete_cvd_visibility"])
            collected = outer.finalize(str(self.out), captured["capture_file_sha256"])
        self.assertEqual(collected["reservation_check_status"], "PASS_WITH_EXPLICIT_NON_WORKER_SERVICE_EXCEPTIONS")
        self.assertFalse(collected["complete_cvd_visibility"])
        self.assertEqual(collected["approved_unreadable_service_pids"], [900010, 900011])
        self.assertTrue(outer.read(self.out / "final.json")["diagnostic_usable"])
        self.assertNotIn("complete_cvd_visibility", outer.read(self.out / "release_attestation.json"))
        self.mocks[4].assert_not_called()


class ServiceExceptionTests(unittest.TestCase):
    process_record = OuterTests.process_record

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="pcfl_service_metadata_cpu_")
        self.addCleanup(self.temp.cleanup)
        self.proc = Path(self.temp.name) / "proc"
        (self.proc / "sys/kernel/random").mkdir(parents=True)
        (self.proc / "sys/kernel/random/boot_id").write_text("fixture-boot")
        self.process_record(os.getpid(), pgid=os.getpid(), sid=os.getpid(), ticks=100)
        self.allocation = {"uid": os.getuid(), "boot_id": "fixture-boot", "gpu_index": 2,
                           "gpu_uuid": "GPU-FIXTURE", "coordination_owners": [], "service_exceptions": []}
        self.proc_patch = patch.object(outer, "PROC", self.proc)
        self.proc_patch.start()
        self.addCleanup(self.proc_patch.stop)
        install_service_fixtures(self)

    def scan(self, *, denied=(900010, 900011), release=False, hook=None, error_type=PermissionError):
        original = Path.read_bytes
        attempts = []
        paths = {self.proc / str(pid) / "environ" for pid in denied}
        def read_bytes(path):
            if path in paths:
                attempts.append(int(path.parent.name))
                if hook is not None:
                    hook(path)
                raise error_type("SYNTHETIC environment access denied")
            return original(path)
        with patch.object(Path, "read_bytes", read_bytes):
            result = outer.check_cvd(self.allocation, time.monotonic() + 20, release=release)
        return result, attempts

    def test_exact_pair_permissionerror_before_after_receipts(self):
        result, attempts = self.scan()
        self.assertTrue(result["clear"])
        self.assertEqual(attempts, [900010, 900011])
        self.assertFalse(result["complete_cvd_visibility"])
        self.assertIsNone(result["device_unreserved"])
        self.assertEqual(result["unresolved"], [])
        for record in result["approved_unreadable_services"]:
            self.assertFalse(record["environment_read"])
            self.assertEqual(record["error_type"], "PermissionError")
            self.assertEqual(record["metadata_before"], record["metadata_after"])
            for member in record["metadata_before"].values():
                self.assertEqual(len(member["comm_sha256"]), 64)
                self.assertEqual(len(member["cgroup_sha256"]), 64)

    def test_no_protected_environment_alternative_open(self):
        original = Path.open
        attempts = []
        protected = {self.proc / str(pid) / "environ" for pid in (900010, 900011)}
        def open_path(path, *args, **kwargs):
            if path in protected:
                attempts.append(path)
                raise AssertionError("alternate open of protected environment")
            return original(path, *args, **kwargs)
        with patch.object(Path, "open", open_path):
            result, _ = self.scan()
        self.assertTrue(result["clear"])
        self.assertEqual(attempts, [])

    def test_unlisted_unreadable_worker_still_blocks(self):
        self.process_record(900012, pgid=900012, sid=900012, ticks=200, cvd="GPU-FIXTURE")
        result, _ = self.scan(denied=(900010, 900011, 900012))
        self.assertFalse(result["clear"])
        self.assertEqual([item["pid"] for item in result["unresolved"]], [900012])
        self.assertEqual(len(result["approved_unreadable_services"]), 2)

    def test_listed_but_readable_cvd_reservation_blocks_all_phases(self):
        (self.proc / "900010/environ").write_bytes(b"CUDA_VISIBLE_DEVICES=GPU-FIXTURE\0")
        for release in (False, True):
            with self.subTest(release=release):
                result, _ = self.scan(denied=(900011,), release=release)
                self.assertFalse(result["clear"])
                self.assertEqual(result["owners"][0]["identity"]["pid"], 900010)
                self.assertEqual([item["pid"] for item in result["approved_unreadable_services"]], [900011])

    def test_readable_pair_is_scanned_without_exception(self):
        result, _ = self.scan(denied=())
        self.assertTrue(result["clear"])
        self.assertTrue(result["device_unreserved"])
        self.assertTrue(result["complete_cvd_visibility"])
        self.assertEqual(result["approved_unreadable_services"], [])

    def test_non_permission_error_never_uses_exception(self):
        result, _ = self.scan(error_type=OSError)
        self.assertFalse(result["clear"])
        self.assertEqual(result["approved_unreadable_services"], [])
        self.assertEqual(len(result["unresolved"]), 2)

    def test_command_comm_cgroup_and_parent_drift_before_denial(self):
        for filename, value in (("cmdline", b"changed\0"), ("comm", b"python\n"),
                                 ("cgroup", b"0::/other.scope\n"),
                                 ("stat", b"900010 (systemd) S 42 900010 900010 " + b"0 " * 15 + b"40")):
            path = self.proc / "900010" / filename
            original = path.read_bytes()
            path.write_bytes(value)
            with self.subTest(filename=filename):
                result, _ = self.scan()
                self.assertFalse(result["clear"])
                self.assertEqual(result["approved_unreadable_services"], [])
            path.write_bytes(original)

    def test_metadata_drift_after_denial_does_not_pass(self):
        changed = False
        def drift(path):
            nonlocal changed
            if not changed:
                (self.proc / "900011/cmdline").write_bytes(b"changed-after-before-check\0")
                changed = True
        result, _ = self.scan(hook=drift)
        self.assertFalse(result["clear"])
        self.assertEqual(result["approved_unreadable_services"], [])

    def test_peer_disappearance_cannot_hide_still_present_manager(self):
        def disappear(path):
            helper = self.proc / "900011"
            if helper.exists():
                shutil.rmtree(helper)
        result, _ = self.scan(hook=disappear)
        self.assertFalse(result["clear"])
        self.assertIn(900010, [item["pid"] for item in result["unresolved"]])

    def test_reused_pid_boot_and_uid_bindings(self):
        self.process_record(900010, pgid=900010, sid=900010, ticks=999, ppid=1)
        result, _ = self.scan()
        self.assertFalse(result["clear"])
        self.assertEqual(result["approved_unreadable_services"], [])
        self.process_record(900010, pgid=900010, sid=900010, ticks=40, ppid=1)
        (self.proc / "sys/kernel/random/boot_id").write_text("different-boot")
        result, _ = self.scan()
        self.assertFalse(result["clear"])
        self.allocation["service_exceptions"][0]["identity"]["uid"] += 1
        with self.assertRaisesRegex(ValueError, "UID/boot"):
            outer._service_expectations(self.allocation)

    def test_shape_relationship_and_scope_restrictions(self):
        records = copy.deepcopy(self.allocation["service_exceptions"])
        variants = [records[:1], records + [records[0]]]
        for role_index, field, value in ((0, "comm", "python"), (0, "ppid", True),
                                         (0, "cgroup", "0::/worker.scope\n"), (1, "ppid", 123)):
            variant = copy.deepcopy(records)
            variant[role_index][field] = value
            variants.append(variant)
        for variant in variants:
            with self.subTest(variant=variant), self.assertRaises(ValueError):
                outer._service_expectations({**self.allocation, "service_exceptions": variant})
        with self.assertRaisesRegex(ValueError, "overlaps"):
            outer._service_expectations({**self.allocation, "coordination_owners": [records[0]["identity"]]})

    def test_main_supplied_native_pair_metadata_schema_only(self):
        allocation = {"uid": 2524, "boot_id": "8ff7b0dc-fbdf-4945-9044-3dffe94b5407", "coordination_owners": []}
        cgroup = "0::/user.slice/user-2524.slice/user@2524.service/init.scope\n"
        allocation["service_exceptions"] = [
            {"role": "user_manager", "identity": {"pid": 36935, "pgid": 36935, "sid": 36935,
                "start_ticks": 4243834, "boot_id": allocation["boot_id"], "uid": 2524},
             "ppid": 1, "comm": "systemd", "cgroup": cgroup,
             "cmdline_sha256": "3127082f907652bfa48e38fddcaf16c3e73b2da5a2d64602eafe88869c222925"},
            {"role": "pam_helper", "identity": {"pid": 36938, "pgid": 36935, "sid": 36935,
                "start_ticks": 4243835, "boot_id": allocation["boot_id"], "uid": 2524},
             "ppid": 36935, "comm": "(sd-pam)", "cgroup": cgroup,
             "cmdline_sha256": "971490059d839d27af3ded30a476216b92689d837b0236a700723fb13640e370"}]
        self.assertEqual(set(outer._service_expectations(allocation)), {"user_manager", "pam_helper"})


if __name__ == "__main__":
    unittest.main()
