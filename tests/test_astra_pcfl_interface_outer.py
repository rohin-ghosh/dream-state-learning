"""Real harmless child sessions; only queue/GPU/CVD observations are injected."""

import copy
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch
import venv

from test_astra_pcfl_interface_command import Harness
from gpu import astra_pcfl_interface_outer as outer

REAL_POPEN, REAL_IDENTITY = subprocess.Popen, outer.lifecycle.identity
CHILD = r'''
import hashlib,json,os,pathlib,sys,time
path,mode,deadline=sys.argv[1:]
manifest=json.loads(pathlib.Path(path).read_text())
stage=manifest['stage']
root=pathlib.Path(manifest['root'])/stage
root.mkdir()
started=time.monotonic()
print('SYNTHETIC harmless child stdout',flush=True)
print('SYNTHETIC harmless child stderr',file=sys.stderr,flush=True)
(root/'original.txt').write_bytes(b'ORIGINAL SYNTHETIC EVIDENCE\n')
if mode=='timeout':time.sleep(60)
if mode=='short':time.sleep(.1)
if mode=='signal':os.kill(os.getpid(),15)
if mode=='missing':sys.exit(0)
if mode=='failure':(root/'failure.json').write_text('{"error":"ORIGINAL FAILURE"}\n')
digest=lambda value:hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
seal=lambda value:dict(value,sha256=digest(value))
write=lambda path,value:path.write_text(json.dumps(value)+'\n')
(root/'actor').mkdir()
(root/'records').mkdir()
settings=dict(manifest['actor_template'],deadline=float(deadline))
summary=dict(denominator=64,route_successes=0,stage_gate_passed=False,full_assay_qualified=False)
report=seal(dict(status='COMPLETE',roster_sha256=manifest['roster']['sha256'],actor_config=settings,
    summary=summary,calls=64,possible_calls=manifest['roster']['limits']['possible_calls'],attempts=[{}]*64))
write(root/'records/report.json',report)
write(root/'actor/identity.json',dict(kind='NATIVE',pid=os.getpid(),config_sha256=digest(settings)))
write(root/'actor/close.json',dict(kind='NATIVE',calls_consumed=64,token_count_calls=0))
ended=time.monotonic()
completed=dict(schema='pcfl.interface.command.v1/completed',status='COMPLETE',stage=stage,
    manifest_sha256=manifest['sha256'],report_sha256=report['sha256'],summary=summary,
    started=started,ended=ended,elapsed_seconds=ended-started,outer_release_required=True,
    gpu_released=False,full_assay_qualified=False,kind='NATIVE',fits=0,updates=0,
    actual_calls=64,possible_calls=report['possible_calls'],
    files={str(path.relative_to(root)):hashlib.sha256(path.read_bytes()).hexdigest() for path in root.rglob('*') if path.is_file()})
if mode=='wrongstage':completed['stage']='A3_THINK'
if mode=='injected':completed['kind']='INJECTED_CPU_TEST'
write(root/'completed.json',seal(completed))
if mode=='drift':(root/'original.txt').write_bytes(b'changed')
sys.exit(9 if mode=='nonzero' else 0)
'''


class OuterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.venv = tempfile.TemporaryDirectory(prefix="SYNTHETIC_INTERFACE_OUTER_VENV_")
        cls.addClassCleanup(cls.venv.cleanup)
        venv.EnvBuilder(with_pip=False).create(cls.venv.name)
        cls.python = str(Path(cls.venv.name) / "bin/python")

    def setUp(self):
        self.harness = Harness(self)
        self.harness.fixture.environment["python"] = str(Path(self.python).resolve())
        self.manifest = self.harness.prepare()
        self.manifest["kind"] = "OFFLINE_PREPARATION"
        self.root = self.harness.root
        self.output = self.root / "outer"
        self.source_hash = outer.command.file_hash(outer.__file__)
        self.queue = self.root / "queue"
        for name in ("pending", "running"):
            (self.queue / name).mkdir(parents=True)
        self.allocation_path = self.root / "allocation.json"
        self.allocation = {"schema": outer.lifecycle.SCHEMA + "/allocation", "gpu_index": 0,
            "gpu_uuid": "GPU-CPU-TEST", "uid": os.getuid(), "boot_id": outer.lifecycle.boot_id(),
            "python": self.python, "queue_dir": str(self.queue), "queue_mode": "direct",
            "queue_allowlist": {"pending": {}, "running": {}}, "coordination_owners": [],
            "lease_end": time.time() + 30000, "lease_margin_seconds": 21600,
            "outer_sha256": self.source_hash, "service_exceptions": []}
        self.children, self.observations = [], []
        self.mode = "complete"
        self.gpu_clear = True
        self.cvd_clear = True
        self.save()
        self.addCleanup(self.reap)
        for target, arguments in (
            ("sleep", {"side_effect": lambda duration: self.observations.append(("sleep", duration))}),
            ("subprocess.Popen", {"side_effect": self.spawn}),
            ("lifecycle.check_gpu", {"side_effect": self.gpu}),
            ("lifecycle.check_cvd", {"side_effect": self.cvd}),
            ("lifecycle.controller", {"side_effect": AssertionError("no C0 controller")}),
            ("lifecycle.finalize", {"side_effect": AssertionError("no foreground finalizer")})):
            mocked = patch("gpu.astra_pcfl_interface_outer." + target, **arguments)
            mocked.start()
            self.addCleanup(mocked.stop)

    def save(self):
        self.manifest = outer.command.driver.seal({key: value for key, value in self.manifest.items() if key != "sha256"})
        self.harness.path.write_bytes(outer.command.canonical(self.manifest) + b"\n")
        self.allocation_path.write_bytes(outer.command.canonical(self.allocation) + b"\n")
        self.manifest_hash = outer.command.file_hash(self.harness.path)
        self.allocation_hash = outer.command.file_hash(self.allocation_path)

    def reap(self):
        for child in self.children:
            child.wait(timeout=5)

    def gpu(self, allocation, deadline):
        self.observations.append(("gpu", bool(self.children)))
        return {"empty": self.gpu_clear, "gpu_uuid": allocation["gpu_uuid"]}

    def cvd(self, allocation, deadline, *, release):
        self.assertTrue(release)
        self.observations.append(("cvd", bool(self.children)))
        return {"clear": self.cvd_clear, "owners": [], "unresolved": [] if self.cvd_clear else ["UNREADABLE"]}

    def spawn(self, argv, **kwargs):
        self.assertEqual(self.observations[0], ("sleep", 4))
        self.assertEqual(argv[:5], [self.python, "-B", "-m", "gpu.astra_pcfl_interface_command", "stage"])
        self.assertEqual(argv[5:9], ["--manifest", str(self.harness.path), "--manifest-sha256", self.manifest_hash])
        self.assertEqual(argv[9], "--deadline")
        binding = outer.command.read(self.output / "binding.json")
        self.assertEqual(float(argv[10]), binding["worker_deadline_monotonic"])
        self.assertEqual(kwargs["stdin"], subprocess.DEVNULL)
        self.assertTrue(kwargs["start_new_session"])
        self.assertEqual(kwargs["env"]["CUDA_VISIBLE_DEVICES"], "GPU-CPU-TEST")
        self.assertEqual(kwargs["env"]["PYTHONPATH"], str(Path(outer.command.__file__).resolve().parents[1]))
        self.assertTrue(all(kwargs["env"][key] == "1" for key in outer.command.OFFLINE))
        self.assertEqual((self.output / "manifest.input.json").read_bytes(), self.harness.path.read_bytes())
        child = REAL_POPEN([self.python, "-B", "-c", CHILD, str(self.harness.path), self.mode, argv[10]], **kwargs)
        self.children.append(child)
        return child

    def run_controller(self):
        return outer.controller(str(self.harness.path), self.manifest_hash, str(self.allocation_path),
            self.allocation_hash, str(self.output), outer_sha256=self.source_hash, stage="A2_DIRECT")

    def test_real_child_complete_failed_ceiling_and_release(self):
        result = self.run_controller()
        self.assertEqual(result["status"], "COMPLETED", result["errors"])
        self.assertFalse(result["stage_summary"]["stage_gate_passed"])
        self.assertEqual(result["worker_identity"]["pid"], self.children[0].pid)
        self.assertEqual(result["returncode"], 0)
        self.assertEqual([entry for entry in self.observations if entry[0] == "gpu"], [("gpu", False), ("gpu", True)])
        context = outer.command.read(self.output / "context.json")
        binding = outer.command.read(self.output / "binding.json")
        self.assertEqual(binding["deadline_monotonic"], context["entry_monotonic"] + 3600)
        self.assertEqual(binding["worker_deadline_monotonic"], binding["deadline_monotonic"] - 120)
        self.assertEqual(binding["lease_finish_margin_seconds"], 21600)
        with patch.object(outer, "controller", return_value=result):
            self.assertEqual(outer.main(["--manifest", str(self.harness.path), "--manifest-sha256", self.manifest_hash,
                "--allocation", str(self.allocation_path), "--allocation-sha256", self.allocation_hash,
                "--outer-sha256", self.source_hash, "--outer", str(self.output), "--stage", "A2_DIRECT"]), 0)

    def test_nonzero_signal_and_invalid_stage_evidence_fail(self):
        for mode in ("nonzero", "signal", "missing", "failure", "drift", "wrongstage", "injected"):
            with self.subTest(mode=mode):
                self.harness.output = self.root / ("prepared_" + mode)
                self.manifest = self.harness.prepare()
                self.manifest["kind"] = "OFFLINE_PREPARATION"
                self.mode, self.output = mode, self.root / ("outer_" + mode)
                self.save()
                self.assertEqual(self.run_controller()["status"], "FAILED")
                if mode == "failure":
                    self.assertEqual((self.harness.output / "A2_DIRECT/failure.json").read_text(), '{"error":"ORIGINAL FAILURE"}\n')

    def test_timeout_kills_only_verified_child_session(self):
        self.mode = "timeout"
        with patch.object(outer, "TOTAL_SECONDS", .8), patch.object(outer, "CLEANUP_SECONDS", .4):
            result = self.run_controller()
        self.assertEqual(result["status"], "FAILED")
        self.assertEqual(self.children[0].returncode, -signal.SIGTERM)
        events = outer.command.read(self.output / "worker_exit.json")["events"]
        self.assertTrue(any(event.get("signal") == signal.SIGTERM for event in events))
        self.assertTrue(all(event["pgid"] == self.children[0].pid for event in events if "pgid" in event))

    def test_unknown_identity_never_invokes_cleanup_or_signal(self):
        self.mode = "short"
        def identity(pid):
            if pid == os.getpid(): return REAL_IDENTITY(pid)
            raise PermissionError("synthetic unreadable owned PID")
        with patch.object(outer.lifecycle, "identity", side_effect=identity), patch.object(outer.lifecycle, "cleanup_owned") as cleanup, patch.object(os, "killpg") as kill:
            result = self.run_controller()
        cleanup.assert_not_called()
        kill.assert_not_called()
        self.assertEqual(result["status"], "FAILED")
        self.assertIsNone(result["worker_identity"])

    def test_post_worker_release_observation_failure_is_not_completion(self):
        original = self.gpu
        def busy_after(allocation, deadline):
            value = original(allocation, deadline)
            if self.children: value["empty"] = False
            return value
        with patch.object(outer.lifecycle, "check_gpu", side_effect=busy_after):
            result = self.run_controller()
        self.assertEqual(result["status"], "FAILED")
        self.assertTrue((self.harness.output / "A2_DIRECT/completed.json").is_file())

    def test_pinned_manifest_stage_source_allocation_and_lease_guards(self):
        baseline, allocation = copy.deepcopy(self.manifest), copy.deepcopy(self.allocation)
        for mode in ("source", "manifest", "allocation", "boot", "lease", "python", "kind", "stage", "roots"):
            with self.subTest(mode=mode):
                self.manifest, self.allocation = copy.deepcopy(baseline), copy.deepcopy(allocation)
                self.output = self.root / ("guard_" + mode)
                if mode == "source": self.manifest["sources"].pop(str(Path(outer.command.__file__).resolve()))
                if mode == "boot": self.allocation["boot_id"] = "different"
                if mode == "lease": self.allocation["lease_end"] = time.time() + 21630
                if mode == "python": self.allocation["python"] = "/missing/python"
                if mode == "kind": self.manifest["kind"] = "INJECTED_CPU_TEST"
                if mode == "stage": self.manifest["stage"] = "A3_THINK"
                if mode == "roots": self.manifest["spec"]["roots_file"]["sha256"] = "0" * 64
                self.save()
                if mode == "manifest": self.manifest_hash = "0" * 64
                if mode == "allocation": self.allocation_hash = "0" * 64
                self.assertEqual(self.run_controller()["status"], "FAILED")
                self.assertEqual(self.children, [])

    def test_nonempty_cvd_queue_and_unreadable_cvd_prevent_spawn(self):
        with patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "GPU-CPU-TEST"}):
            self.assertEqual(self.run_controller()["status"], "FAILED")
        self.output = self.root / "queue_drift"
        (self.queue / "pending/unknown.json").write_text("unexpected")
        self.assertEqual(self.run_controller()["status"], "FAILED")
        self.output = self.root / "unreadable"
        self.cvd_clear = False
        self.assertEqual(self.run_controller()["status"], "FAILED")
        self.assertEqual(self.children, [])

    def test_freshness_and_output_overlap(self):
        self.assertEqual(self.run_controller()["status"], "COMPLETED")
        original = (self.output / "collection.json").read_bytes()
        with self.assertRaises(FileExistsError): self.run_controller()
        self.assertEqual((self.output / "collection.json").read_bytes(), original)
        self.output = self.root / "second_outer"
        self.assertEqual(self.run_controller()["status"], "FAILED")
        self.output = self.harness.output / "nested_outer"
        with self.assertRaises(ValueError): self.run_controller()


if __name__ == "__main__":
    unittest.main()
