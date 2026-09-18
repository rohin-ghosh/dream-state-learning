"""Real harmless CPU children; injected manifest/resource observations only."""

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

from gpu import astra_pcfl_event_only_outer as outer

REAL_POPEN, REAL_IDENTITY = subprocess.Popen, outer.lifecycle.identity
CHILD = r'''
import hashlib,json,os,pathlib,sys,time
root,stage,manifest_hash,mode=sys.argv[1:]
directory=pathlib.Path(root)/stage
directory.mkdir()
started=time.monotonic()
(directory/'original.txt').write_bytes(b'ORIGINAL SYNTHETIC STAGE BYTES\n')
print('synthetic harmless stdout',flush=True)
print('synthetic harmless stderr',file=sys.stderr,flush=True)
if mode=='timeout':time.sleep(60)
if mode=='short':time.sleep(.1)
if mode=='signal':os.kill(os.getpid(),15)
if mode=='missing':sys.exit(0)
if mode=='failure':(directory/'failure.json').write_text('{"error":"ORIGINAL FAILURE"}\n')
if stage.startswith('readout_'):
    (directory/'actor').mkdir()
    (directory/'actor/identity.json').write_text(json.dumps({'pid':os.getpid(),'kind':'NATIVE_OWN_WRITE_READOUT'}))
ended=time.monotonic()
receipt=dict(schema='pcfl.event_only.command.v1/completed',status='COMPLETE',stage=stage,
    manifest_sha256=manifest_hash,started=started,ended=ended,elapsed_seconds=ended-started,
    outer_release_required=True,gpu_released=False,kind='NATIVE',full_contract_released=False,
    original_status='FORMATION_FAILED',original_returncode=1,
    calls=0 if stage=='fit' else 28,fits=1 if stage=='fit' else 0,updates=200 if stage=='fit' else 0,
    files={str(path.relative_to(directory)):hashlib.sha256(path.read_bytes()).hexdigest() for path in directory.rglob('*') if path.is_file()})
if mode=='wrongcount':receipt['updates']=199
if mode=='promote':receipt['original_status']='COMPLETE'
if mode=='injected':receipt['kind']='INJECTED_CPU_TEST'
receipt['sha256']=hashlib.sha256(json.dumps(receipt,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
(directory/'completed.json').write_text(json.dumps(receipt)+'\n')
if mode=='drift':(directory/'original.txt').write_bytes(b'changed')
sys.exit(7 if mode=='nonzero' else 0)
'''


class OuterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.venv = tempfile.TemporaryDirectory(prefix="SYNTHETIC_EVENT_OUTER_VENV_")
        cls.addClassCleanup(cls.venv.cleanup)
        venv.EnvBuilder(with_pip=False).create(cls.venv.name)
        cls.python = str(Path(cls.venv.name) / "bin/python")

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="SYNTHETIC_EVENT_OUTER_")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.prepared = self.root / "prepared"
        self.prepared.mkdir()
        self.output = self.root / "outer"
        self.path = self.prepared / "manifest.json"
        self.allocation_path = self.root / "allocation.json"
        self.source_hash = outer.command.file_hash(outer.__file__)
        self.manifest = {"schema": outer.command.SCHEMA + "/manifest", "root": str(self.prepared),
            "kind": "OFFLINE_PREPARATION", "sources": outer.command.source_files(),
            "spec": {"gpu_uuid": "GPU-SYNTHETIC", "boot_id": outer.lifecycle.boot_id(),
                     "expires_monotonic": time.monotonic()+3600,
                     "environment": {"native": {"python": str(Path(self.python).resolve())}}}}
        self.queue = self.root / "queue"
        for name in ("pending", "running"):
            (self.queue/name).mkdir(parents=True)
        self.allocation = {"schema": outer.lifecycle.SCHEMA + "/allocation", "gpu_index": 0,
            "gpu_uuid": "GPU-SYNTHETIC", "uid": os.getuid(), "boot_id": outer.lifecycle.boot_id(),
            "python": self.python, "queue_dir": str(self.queue), "queue_mode": "direct",
            "queue_allowlist": {"pending": {}, "running": {}}, "coordination_owners": [],
            "lease_end": time.time()+30000, "lease_margin_seconds": 21600,
            "outer_sha256": self.source_hash, "service_exceptions": []}
        self.children, self.events = [], []
        self.mode, self.stage, self.arm = "complete", "fit", None
        self.post_busy = False
        environment = patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": ""})
        environment.start()
        self.addCleanup(environment.stop)
        self.save()
        self.addCleanup(self.reap)
        for target, arguments in (
            ("sleep", {"side_effect": lambda seconds: self.events.append(("sleep", seconds))}),
            ("subprocess.Popen", {"side_effect": self.spawn}),
            ("command.validate_manifest", {"side_effect": lambda path, checksum: copy.deepcopy(self.manifest)}),
            ("lifecycle.check_gpu", {"side_effect": lambda allocation, deadline: {"empty": not (self.children and self.post_busy), "gpu_uuid": allocation["gpu_uuid"]}}),
            ("lifecycle.check_cvd", {"return_value": {"clear": True, "owners": [], "unresolved": []}}),
            ("lifecycle.controller", {"side_effect": AssertionError("no original C0 controller")}),
            ("lifecycle.finalize", {"side_effect": AssertionError("no separate finalizer")})):
            mocked = patch("gpu.astra_pcfl_event_only_outer." + target, **arguments)
            mocked.start()
            self.addCleanup(mocked.stop)

    def save(self):
        self.manifest = outer.command.prefix.seal({key: value for key,value in self.manifest.items() if key != "sha256"})
        self.path.write_bytes(outer.command.canonical(self.manifest))
        self.allocation_path.write_bytes(outer.command.canonical(self.allocation))
        self.manifest_hash = outer.command.file_hash(self.path)
        self.allocation_hash = outer.command.file_hash(self.allocation_path)

    def reap(self):
        for child in self.children: child.wait(timeout=5)

    def spawn(self, argv, **kwargs):
        self.assertEqual(self.events[0], ("sleep", 4))
        expected = [self.python,"-B","-m","gpu.astra_pcfl_event_only_command",self.stage,
                    "--manifest",str(self.path),"--manifest-sha256",self.manifest_hash]
        self.assertEqual(argv[:9], expected)
        self.assertEqual(argv[9], "--deadline")
        if self.arm is not None: self.assertEqual(argv[11:], ["--arm",self.arm])
        self.assertEqual(kwargs["stdin"], subprocess.DEVNULL)
        self.assertTrue(kwargs["start_new_session"])
        self.assertEqual(kwargs["env"]["CUDA_VISIBLE_DEVICES"], "GPU-SYNTHETIC")
        self.assertEqual(kwargs["env"]["PYTHONPATH"], str(Path(outer.command.__file__).resolve().parents[1]))
        self.assertEqual((self.output / "manifest.input.json").read_bytes(), self.path.read_bytes())
        name = self.stage if self.stage == "fit" else "readout_"+self.arm
        child = REAL_POPEN([self.python,"-B","-c",CHILD,str(self.prepared),name,self.manifest["sha256"],self.mode],**kwargs)
        self.children.append(child)
        return child

    def run_controller(self):
        return outer.controller(str(self.path),self.manifest_hash,str(self.allocation_path),self.allocation_hash,
            str(self.output),outer_sha256=self.source_hash,stage=self.stage,arm=self.arm)

    def test_fit_and_both_arm_argv_custody_and_fixed_budget(self):
        result = self.run_controller()
        self.assertEqual(result["status"], "COMPLETED", result["errors"])
        context = outer.command.read(self.output / "context.json")
        binding = outer.command.read(self.output / "binding.json")
        self.assertEqual(binding["deadline_monotonic"], context["entry_monotonic"]+1800)
        self.assertEqual(binding["worker_deadline_monotonic"], binding["deadline_monotonic"]-60)
        self.assertEqual(binding["lease_finish_margin_seconds"], 21600)
        for arm in outer.command.readout_api.ARMS:
            self.stage,self.arm,self.output = "readout",arm,self.root/arm
            result=self.run_controller()
            self.assertEqual(result["status"], "COMPLETED",result["errors"])
        self.assertEqual(len({child.pid for child in self.children}),3)

    def test_nonzero_signal_invalidcounts_and_original_failure_never_promoted(self):
        for mode in ("nonzero","signal","failure","missing","wrongcount","promote","injected","drift"):
            with self.subTest(mode=mode):
                self.prepared=self.root/("prepared_"+mode)
                self.prepared.mkdir()
                self.path=self.prepared/"manifest.json"
                self.manifest["root"]=str(self.prepared)
                self.output,self.mode=self.root/("outer_"+mode),mode
                self.save()
                self.assertEqual(self.run_controller()["status"],"FAILED")
                if mode=="failure":self.assertEqual((self.prepared/"fit/failure.json").read_text(),'{"error":"ORIGINAL FAILURE"}\n')

    def test_timeout_cleanup_targets_only_spawned_verified_group(self):
        self.mode="timeout"
        with patch.object(outer,"TOTAL_SECONDS",.8),patch.object(outer,"CLEANUP_SECONDS",.4):
            result=self.run_controller()
        self.assertEqual(result["status"],"FAILED")
        self.assertEqual(self.children[0].returncode,-signal.SIGTERM)
        events=outer.command.read(self.output/"worker_exit.json")["events"]
        self.assertTrue(all(event["pgid"]==self.children[0].pid for event in events if "pgid" in event))

    def test_unknown_pid_never_killed(self):
        self.mode="short"
        def identify(pid):
            if pid==os.getpid():return REAL_IDENTITY(pid)
            raise PermissionError("SYNTHETIC unreadable PID")
        with patch.object(outer.lifecycle,"identity",side_effect=identify),patch.object(outer.lifecycle,"cleanup_owned") as cleanup,patch.object(os,"killpg") as kill:
            result=self.run_controller()
        self.assertEqual(result["status"],"FAILED")
        cleanup.assert_not_called()
        kill.assert_not_called()

    def test_post_release_failure_is_not_stage_success(self):
        self.post_busy=True
        self.assertEqual(self.run_controller()["status"],"FAILED")
        self.assertTrue((self.prepared/"fit/completed.json").is_file())

    def test_input_pin_source_binding_short_lease_and_empty_cvd_guards(self):
        original,allocation=copy.deepcopy(self.manifest),copy.deepcopy(self.allocation)
        for mode in ("manifest","allocation","self","source","lease","kind"):
            self.manifest,self.allocation=copy.deepcopy(original),copy.deepcopy(allocation)
            self.output=self.root/mode
            self.source_hash=outer.command.file_hash(outer.__file__)
            if mode=="source":self.manifest["sources"].pop(str(Path(outer.command.__file__).resolve()))
            if mode=="lease":self.allocation["lease_end"]=time.time()+21630
            if mode=="kind":self.manifest["kind"]="INJECTED_CPU_TEST"
            self.save()
            if mode=="manifest":self.manifest_hash="0"*64
            if mode=="allocation":self.allocation_hash="0"*64
            if mode=="self":self.source_hash="0"*64
            self.assertEqual(self.run_controller()["status"],"FAILED")
        self.assertEqual(self.children,[])

    def test_fresh_output_and_existing_stage_never_reused(self):
        self.assertEqual(self.run_controller()["status"],"COMPLETED")
        with self.assertRaises(FileExistsError):self.run_controller()
        self.output=self.root/"another_outer"
        self.assertEqual(self.run_controller()["status"],"FAILED")
        self.output=self.prepared/"nested_outer"
        with self.assertRaises(ValueError):self.run_controller()

    def test_empty_cvd_queue_and_unreadable_release_guards(self):
        with patch.dict(os.environ,{"CUDA_VISIBLE_DEVICES":"GPU-SYNTHETIC"}):
            self.assertEqual(self.run_controller()["status"],"FAILED")
        self.output=self.root/"queue_drift"
        (self.queue/"pending/unknown.json").write_text("unexpected")
        self.assertEqual(self.run_controller()["status"],"FAILED")
        self.assertEqual(self.children,[])


if __name__=="__main__":
    unittest.main()
