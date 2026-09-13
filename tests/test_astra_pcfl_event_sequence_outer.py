"""Real harmless child sessions, synthetic fit receipts, injected GPU observations."""

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

from gpu import astra_pcfl_event_sequence_outer as outer

REAL_POPEN, REAL_IDENTITY = subprocess.Popen, outer.lifecycle.identity
CHILD = r'''
import json, pathlib, sys, time
from dataclasses import asdict
from gpu import astra_pcfl_event_sequence_fit as fit
path, checksum, output, phase, mode = sys.argv[1:]
started=time.monotonic()
root=pathlib.Path(output)
root.mkdir()
print('SYNTHETIC harmless fit stdout',flush=True)
print('SYNTHETIC harmless fit stderr',file=sys.stderr,flush=True)
(root/'original.txt').write_bytes(b'ORIGINAL SYNTHETIC FIT EVIDENCE\n')
if mode=='timeout': time.sleep(60)
if mode=='short': time.sleep(.15)
if mode=='missing': sys.exit(0)
inputs=json.loads(pathlib.Path(path).read_bytes())
material=json.loads(pathlib.Path(inputs['material']['path']).read_bytes())
selected=material['phases'][phase]
config=fit.sequence.training_config(phase,inputs['model_path'],device='cuda')
fit.write(root/'inputs.json',inputs)
fit.write(root/'config.json',asdict(config))
fit.write(root/'corpus.json',selected['items'])
checkpoint=root/'checkpoint'
checkpoint.mkdir()
fit.write(checkpoint/'adapter_config.json',{'base_model_name_or_path':config.model})
(checkpoint/'adapter_model.safetensors').write_bytes(b'SYNTHETIC_NOT_TENSORS')
(checkpoint/'DONE').write_text('ok\n')
manifest=dict(config=asdict(config),base_model=config.model,recipe=fit.v3.RECIPE,empty=False,
    steps=config.max_steps,micro_batches=config.max_steps,nonfinite_batches=0,final_loss=1.0,
    corpus=dict(file='corpus.json',sha256=fit.file_hash(root/'corpus.json'),n_items=selected['presentations'],
                n_encoded=selected['presentations'],n_skipped_no_target=0),
    truncation=dict.fromkeys(('items_truncated','context_tokens_dropped','target_tokens_dropped','items_split'),0),
    tokens=dict(target=selected['supervised_tokens'],total=selected['input_tokens']))
if mode=='wrongtokens': manifest['tokens']['target']+=1
if mode=='truncation': manifest['truncation']['items_truncated']=1
fit.write(checkpoint/'train_manifest.json',manifest)
if mode=='failure': fit.write(root/'failure.json',dict(error='ORIGINAL FAILURE'))
receipt=dict(schema=fit.SCHEMA+'/completed',status='COMPLETE',kind='NATIVE',phase=phase,
    parent_phase=fit.sequence.PHASES[phase][0],predecessor=inputs.get('predecessor'),
    inputs=dict(path=path,sha256=checksum),material_sha256=inputs['material']['sha256'],
    export_sha256=material['sha256'],spec_sha256=material['spec']['sha256'],import_sha256=material['spec']['import_sha256'],
    items_sha256=selected['items_sha256'],encoding_sha256=selected['encoding_sha256'],
    model_binding=inputs['model_binding'],base_state_receipt=inputs['base_state_receipt'],
    updates=config.max_steps,nonfinite_batches=0,checkpoint=str(checkpoint),warm_start=None,base_unchanged=True,
    trainable_names=['layer.lora_A.default.weight','layer.lora_B.default.weight'],files=fit.v3._warm_inventory(root),
    elapsed_seconds=dict(load_and_base_check=0,v3_fit_call=0,worker=time.monotonic()-started),
    original_status='FORMATION_FAILED',limits=fit.sequence.LIMITS,outer_release_required=True,
    gpu_released=False,full_contract_released=False,automatic_promotion=False)
if mode=='wrongcount': receipt['updates']-=1
if mode=='wrongphase': receipt['phase']='SEQ_REPLAY'
if mode=='wrongpin': receipt['inputs']['sha256']='0'*64
if mode=='injected': receipt['kind']='INJECTED_CPU_TEST'
if mode=='promote': receipt['original_status']='COMPLETE'
if mode=='fakerelease': receipt['gpu_released']=True
if mode=='badtime': receipt['elapsed_seconds']['worker']=1801
receipt=fit.prefix.seal(receipt)
if mode=='badseal': receipt['sha256']='0'*64
fit.write(root/'completed.json',receipt)
if mode=='drift': (root/'original.txt').write_bytes(b'changed')
if mode=='inputdrift': pathlib.Path(inputs['material']['path']).write_bytes(b'changed synthetic input')
sys.exit(7 if mode=='nonzero' else 0)
'''


class OuterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.venv = tempfile.TemporaryDirectory(prefix="SYNTHETIC_SEQUENCE_VENV_")
        cls.addClassCleanup(cls.venv.cleanup)
        venv.EnvBuilder(with_pip=False).create(cls.venv.name)
        cls.python = str(Path(cls.venv.name) / "bin/python")

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="SYNTHETIC_SEQUENCE_OUTER_")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.prepared, self.model = self.root / "prepared", self.root / "model"
        self.prepared.mkdir()
        self.model.mkdir()
        self.output, self.path = self.root / "outer", self.prepared / "inputs.json"
        self.allocation_path = self.root / "allocation.json"
        phases = {}
        for name, (parent, updates) in outer.fit.sequence.PHASES.items():
            items = [{"SYNTHETIC": index} for index in range(updates * 4)]
            phases[name] = outer.fit.prefix.seal(dict(phase=name, parent_phase=parent, updates=updates, items=items,
                items_sha256=outer.fit.prefix.digest(items), encoding_sha256="e" * 64,
                presentations=len(items), supervised_tokens=len(items) * 2, input_tokens=len(items) * 4))
        material = outer.fit.prefix.seal({"schema": outer.fit.sequence.SCHEMA + "/export",
            "spec": outer.fit.prefix.seal({"import_sha256": "a" * 64}), "phases": phases})
        self.inputs = {"schema": outer.fit.SCHEMA + "/inputs", "model_path": str(self.model),
            "source_files": outer.fit.source_files(), "gpu_uuid": "GPU-SYNTHETIC",
            "environment": {"native": {"python": str(Path(self.python).resolve())}}, "predecessor": None}
        for name in outer.PIN_NAMES:
            path = self.prepared / (name + ".json")
            outer.write(path, material if name == "material" else {"SYNTHETIC": name})
            self.inputs[name] = {"path": str(path), "sha256": outer.fit.file_hash(path)}
        self.queue = self.root / "queue"
        for group in ("pending", "running"):
            (self.queue / group).mkdir(parents=True)
        self.source_hash = outer.fit.file_hash(outer.__file__)
        self.allocation = {"schema": outer.lifecycle.SCHEMA + "/allocation", "gpu_index": 0,
            "gpu_uuid": "GPU-SYNTHETIC", "uid": os.getuid(), "boot_id": outer.lifecycle.boot_id(),
            "python": self.python, "queue_dir": str(self.queue), "queue_mode": "direct",
            "queue_allowlist": {"pending": {}, "running": {}}, "coordination_owners": [],
            "lease_end": time.time() + 30000, "lease_margin_seconds": 21600,
            "outer_sha256": self.source_hash, "service_exceptions": []}
        self.children, self.events = [], []
        self.mode, self.phase = "complete", "S_A"
        self.pre_busy = self.post_busy = self.cvd_busy = False
        self.save()
        self.addCleanup(self.reap)
        patches = [patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": ""}),
            patch.object(outer.fit.prefix, "ARCHIVE_SHA256", self.inputs["archive"]["sha256"]),
            patch.object(outer, "sleep", side_effect=lambda seconds: self.events.append(("sleep", seconds))),
            patch.object(outer.subprocess, "Popen", side_effect=self.spawn),
            patch.object(outer.lifecycle, "check_gpu", side_effect=self.gpu),
            patch.object(outer.lifecycle, "check_cvd", side_effect=self.cvd),
            patch.object(outer.lifecycle, "controller", side_effect=AssertionError("no original C0 controller")),
            patch.object(outer.lifecycle, "finalize", side_effect=AssertionError("no foreground finalizer"))]
        for context in patches:
            context.start()
            self.addCleanup(context.stop)

    def save(self):
        self.path.write_bytes(outer.fit.prefix.canonical(self.inputs) + b"\n")
        self.allocation_path.write_bytes(outer.fit.prefix.canonical(self.allocation) + b"\n")
        self.inputs_hash = outer.fit.file_hash(self.path)
        self.allocation_hash = outer.fit.file_hash(self.allocation_path)

    def reap(self):
        for child in self.children:
            child.wait(timeout=5)

    def gpu(self, allocation, deadline):
        self.events.append(("gpu", bool(self.children)))
        return {"empty": not (self.post_busy if self.children else self.pre_busy), "gpu_uuid": allocation["gpu_uuid"]}

    def cvd(self, allocation, deadline, *, release):
        self.assertTrue(release)
        self.events.append(("cvd", bool(self.children)))
        return {"clear": not self.cvd_busy, "owners": [], "unresolved": ["UNREADABLE"] if self.cvd_busy else []}

    def spawn(self, argv, **kwargs):
        self.assertEqual(self.events[0], ("sleep", 4))
        self.assertEqual(argv[:4], [self.python, "-B", "-m", "gpu.astra_pcfl_event_sequence_fit"])
        expected = {"--inputs": str(self.path), "--inputs-sha256": self.inputs_hash,
                    "--output": str(self.output / "fit"), "--phase": self.phase}
        for flag, value in expected.items():
            self.assertEqual(argv[argv.index(flag) + 1], value)
        binding = outer.read(self.output / "binding.json")
        self.assertEqual(float(argv[argv.index("--deadline") + 1]), binding["worker_deadline_monotonic"])
        self.assertTrue(kwargs["start_new_session"])
        self.assertEqual(kwargs["stdin"], subprocess.DEVNULL)
        self.assertEqual(kwargs["env"]["CUDA_VISIBLE_DEVICES"], self.allocation["gpu_uuid"])
        self.assertEqual(kwargs["env"]["PYTHONPATH"], str(Path(outer.fit.__file__).resolve().parents[1]))
        self.assertTrue(all(kwargs["env"][key] == "1" for key in outer.fit.OFFLINE))
        self.assertEqual((self.output / "inputs.input.json").read_bytes(), self.path.read_bytes())
        child = REAL_POPEN([self.python, "-B", "-c", CHILD, str(self.path), self.inputs_hash,
                           str(self.output / "fit"), self.phase, self.mode], **kwargs)
        self.children.append(child)
        return child

    def run_controller(self):
        return outer.controller(str(self.path), self.inputs_hash, str(self.allocation_path), self.allocation_hash,
                                str(self.output), outer_sha256=self.source_hash, phase=self.phase)

    def test_sa_single_phase_real_collection_and_independent_release(self):
        result = self.run_controller()
        self.assertEqual(result["status"], "COMPLETED", result["errors"])
        self.assertEqual(len(self.children), 1)
        self.assertTrue(result["gpu_released"])
        self.assertFalse(result["full_contract_released"] or result["automatic_promotion"])
        self.assertEqual(result["original_status"], "FORMATION_FAILED")
        completed = outer.read(self.output / "fit/completed.json")
        self.assertEqual(completed["updates"], 40)
        self.assertFalse(completed["gpu_released"])
        self.assertEqual((self.output / "fit_completed.json").read_bytes(), (self.output / "fit/completed.json").read_bytes())
        self.assertEqual(result["completed_sha256"], completed["sha256"])
        context, binding = (outer.read(self.output / name) for name in ("context.json", "binding.json"))
        self.assertEqual(binding["deadline_monotonic"], context["entry_monotonic"] + 1800)
        self.assertEqual(binding["worker_deadline_monotonic"], binding["deadline_monotonic"] - 60)
        self.assertEqual(binding["lease_finish_margin_seconds"], 21600)
        self.assertEqual(self.events, [("sleep", 4), ("gpu", False), ("cvd", False), ("gpu", True), ("cvd", True)])
        self.assertEqual(result["worker_identity"]["pid"], self.children[0].pid)

    def test_fresh_mix_is_explicit_and_missing_parent_never_launches(self):
        self.phase = "FRESH_MIX"
        result = self.run_controller()
        self.assertEqual(result["status"], "COMPLETED", result["errors"])
        self.assertEqual(outer.read(self.output / "fit/completed.json")["updates"], 80)
        self.phase, self.output = "SEQ_REPLAY", self.root / "missing_parent"
        self.assertEqual(self.run_controller()["status"], "FAILED")
        self.assertEqual(len(self.children), 1)

    def test_failed_or_misbound_receipts_never_complete_collection(self):
        for mode in ("missing", "nonzero", "failure", "wrongcount", "wrongphase", "wrongpin", "injected",
                     "promote", "fakerelease", "badtime", "badseal", "drift", "wrongtokens", "truncation"):
            with self.subTest(mode=mode):
                self.mode, self.output = mode, self.root / mode
                result = self.run_controller()
                self.assertEqual(result["status"], "FAILED", result)
                self.assertTrue(result["gpu_released"])
                if mode == "failure":
                    self.assertEqual(outer.read(self.output / "fit/failure.json"), {"error": "ORIGINAL FAILURE"})

    def test_timeout_cleanup_targets_only_verified_spawned_group(self):
        self.mode = "timeout"
        with patch.object(outer, "TOTAL_SECONDS", 1.2), patch.object(outer, "CLEANUP_SECONDS", .5):
            result = self.run_controller()
        self.assertEqual(result["status"], "FAILED")
        self.assertEqual(self.children[0].returncode, -signal.SIGTERM)
        events = outer.read(self.output / "worker_exit.json")["events"]
        self.assertTrue(all(event["pgid"] == self.children[0].pid for event in events if "pgid" in event))

    def test_unknown_identity_never_calls_cleanup_or_kills(self):
        self.mode = "short"
        def identify(pid):
            if pid == os.getpid():
                return REAL_IDENTITY(pid)
            raise PermissionError("SYNTHETIC unreadable PID")
        with patch.object(outer.lifecycle, "identity", side_effect=identify), patch.object(outer.lifecycle, "cleanup_owned") as cleanup, patch.object(os, "killpg") as kill:
            result = self.run_controller()
        self.assertEqual(result["status"], "FAILED")
        self.assertFalse(result["gpu_released"])
        cleanup.assert_not_called()
        kill.assert_not_called()

    def test_unowned_session_identity_never_killed(self):
        self.mode = "short"
        with patch.object(outer.lifecycle, "identity", side_effect=lambda pid: REAL_IDENTITY(os.getpid())), patch.object(outer.lifecycle, "cleanup_owned") as cleanup, patch.object(os, "killpg") as kill:
            self.assertEqual(self.run_controller()["status"], "FAILED")
        cleanup.assert_not_called()
        kill.assert_not_called()

    def test_post_busy_does_not_rewrite_fit_release_or_promote(self):
        self.post_busy = True
        result = self.run_controller()
        self.assertEqual(result["status"], "FAILED")
        self.assertFalse(result["gpu_released"])
        self.assertFalse(outer.read(self.output / "fit/completed.json")["gpu_released"])

    def test_input_changed_by_worker_fails_final_custody(self):
        self.mode = "inputdrift"
        result = self.run_controller()
        self.assertEqual(result["status"], "FAILED")
        self.assertTrue(result["gpu_released"])
        self.assertTrue(any(error["phase"] == "stage_evidence" and "drift" in error["error"] for error in result["errors"]))

    def test_failed_predecessor_does_not_launch_descendant(self):
        self.phase = "SEQ_REPLAY"
        predecessor = self.root / "predecessor"
        predecessor.mkdir()
        path = predecessor / "completed.json"
        outer.write(path, outer.fit.prefix.seal({"schema": outer.fit.SCHEMA + "/completed", "status": "FAILED",
                    "kind": "NATIVE", "phase": "S_A", "updates": 40}))
        self.inputs["predecessor"] = {"path": str(path), "sha256": outer.fit.file_hash(path)}
        self.save()
        self.assertEqual(self.run_controller()["status"], "FAILED")
        self.assertEqual(self.children, [])

    def test_resource_failures_prevent_launch(self):
        for mode in ("gpu", "cvd", "queue", "nonempty_cvd"):
            with self.subTest(mode=mode):
                self.output = self.root / ("resource_" + mode)
                self.pre_busy, self.cvd_busy = mode == "gpu", mode == "cvd"
                entry = self.queue / "pending/unknown.json"
                if mode == "queue":
                    entry.write_text("SYNTHETIC unexpected queue entry")
                with patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "GPU-SYNTHETIC" if mode == "nonempty_cvd" else ""}):
                    self.assertEqual(self.run_controller()["status"], "FAILED")
                if entry.exists():
                    entry.unlink()
        self.assertEqual(self.children, [])

    def test_input_source_and_allocation_drift_prevent_launch(self):
        original, allocation = copy.deepcopy(self.inputs), copy.deepcopy(self.allocation)
        for mode in ("inputs", "allocation", "self", "source", "artifact", "lease", "boot", "uid", "python"):
            with self.subTest(mode=mode):
                self.inputs, self.allocation = copy.deepcopy(original), copy.deepcopy(allocation)
                self.output = self.root / mode
                self.source_hash = outer.fit.file_hash(outer.__file__)
                if mode == "source": self.inputs["source_files"].pop(str(Path(outer.fit.__file__).resolve()))
                if mode == "artifact": self.inputs["material"]["sha256"] = "0" * 64
                if mode == "lease": self.allocation["lease_end"] = time.time() + 21630
                if mode == "boot": self.allocation["boot_id"] = "wrong boot"
                if mode == "uid": self.allocation["uid"] += 1
                if mode == "python": self.allocation["python"] = "/missing/python"
                self.save()
                if mode == "inputs": self.inputs_hash = "0" * 64
                if mode == "allocation": self.allocation_hash = "0" * 64
                if mode == "self": self.source_hash = "0" * 64
                self.assertEqual(self.run_controller()["status"], "FAILED")
        self.assertEqual(self.children, [])

    def test_fresh_output_and_input_overlap_are_not_reused(self):
        self.assertEqual(self.run_controller()["status"], "COMPLETED")
        original = (self.output / "collection.json").read_bytes()
        with self.assertRaises(FileExistsError):
            self.run_controller()
        self.assertEqual((self.output / "collection.json").read_bytes(), original)
        self.output = self.prepared / "nested"
        with self.assertRaises(ValueError):
            self.run_controller()


if __name__ == "__main__":
    unittest.main()
