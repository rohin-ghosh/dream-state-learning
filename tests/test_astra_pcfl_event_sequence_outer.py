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

READOUT_CHILD = r'''
import json, os, pathlib, sys, time
from gpu import astra_pcfl_event_sequence_readout as api
path, checksum, output, state, mode, deadline = sys.argv[1:]
started = time.monotonic()
root = pathlib.Path(output)
root.mkdir()
if mode == 'timeout': time.sleep(60)
if mode == 'short': time.sleep(.15)
inputs = api.read(path)
material = api.read(inputs['material']['path'])
checkpoint = pathlib.Path(inputs['fit_receipt']['path']).parent / 'checkpoint' if inputs.get('fit_receipt') else None
adapter = api._adapter_view(checkpoint, root)
settings = dict(schema=api.reader.SCHEMA, model_path=inputs['model_path'], model_binding=inputs['model_binding'],
    source_files=inputs['source_files'], environment=inputs['environment']['native'], gpu_uuid=inputs['gpu_uuid'],
    shutdown_binding=inputs['shutdown_binding'], roster=material['spec']['roster'], roster_sha256=material['spec']['roster_sha256'],
    tokenizer_files=material['tokenizer_receipt']['tokenizer_files'], chat_template_sha256=material['tokenizer_receipt']['chat_template_sha256'],
    tokenizer_probe={'text':'probe','token_ids':[1]}, engine=api.reader.ENGINE, output_dir=str(root/'actor'),
    deadline=float(deadline), device_seconds_cap=api.CAP_SECONDS, max_calls=16, max_input_tokens=14336,
    max_output_tokens=2048, arm='NO_WRITE_C0' if state=='NO_WRITE' else 'AUTH_WRITE', adapter=adapter)
route = api.reader.route_identity(settings)
actor = root/'actor'
actor.mkdir()
identity = dict(kind='NATIVE_OWN_WRITE_READOUT', pid=os.getpid(), config_sha256=api.prefix.digest(settings), identity={'route':route})
if mode == 'identity': identity['pid'] += 1
shutdown = {'source':inputs['shutdown_binding'], 'shutdown_returned':True}
load = dict(kind=identity['kind'], route=route, model_load_started=started, ready_at=started, shutdown=shutdown)
close = dict(kind=identity['kind'], route=route, calls_consumed=16, planned_calls=16, error_type=None,
    failed=False, budget_exceeded=False, shutdown=shutdown, elapsed_actor_seconds=0)
results = []
for index, row in enumerate(settings['roster']):
    record = material['spec']['records'][index%8]
    text = 'SYNTHETIC WRONG ANSWER\n'
    response = dict(id=row['id'], request_sha256=api.prefix.digest({'id':row['id']}), roster_sha256=settings['roster_sha256'],
        route=route, text=text, prompt_tokens=1, output_tokens=1, finish_reason='stop', stop_reason=None)
    raw = dict(text=text, prompt_token_ids=[1], output_token_ids=[2], finish_reason='stop', stop_reason=None, route=route)
    captures = {'.raw':dict(kind=identity['kind'], route=route, raw=raw, generation_started=started, generation_ended=started),
        '.response':dict(response=response, raw_hex=text.encode().hex(), raw_utf8_sha256=api.native.text_hash(text)),
        '.request':dict(row=row, request={'id':row['id']}, messages=api.reader.public_messages(row)),
        '.render':dict(prompt_token_ids=[1], route=route, sampling={**api.native.SAMPLING, 'seed':row['seed'], 'max_tokens':2048})}
    if index == 0:
        if mode == 'raw': raw['text'] += 'changed'
        if mode == 'tokens': raw['output_token_ids'].append(3)
        if mode == 'sampling': captures['.render']['sampling']['stop'] = ['\n']
        if mode == 'request': captures['.request']['request'] = {'id':'OTHER'}
        if mode == 'rawkind': captures['.raw']['kind'] = 'INJECTED_CPU_TEST'
    for suffix, value in captures.items(): api.write(actor/f'call_{index:04d}{suffix}.json',value)
    api.write(root/f'response_{index:04d}.json',response)
    score = api.sequence.core.score_memory_response(text, record['target'])
    results.append(dict(id=row['id'], request=row['request'], view=row['view'], bank=record['bank'], record=record['index'],
        raw=text, target_sha256=api.native.text_hash(record['target']), finish_reason='stop', prompt_tokens=1, output_tokens=1,
        score=score, strict_stop=False))
panels = {f'W{view}':{} for view in (0,8)}
for view in (0,8):
    for bank in ('A','B'):
        rows = [row for row in results if row['view']==view and row['bank']==bank]
        panels[f'W{view}'][bank] = dict(denominator=4, ids=[row['id'] for row in rows], strict_stop=[False]*4, correct=0)
if mode == 'close': close['calls_consumed'] = 15
if mode == 'shutdown': shutdown['shutdown_returned'] = False
if mode == 'settings': settings['model_path'] += '/wrong'
for name, value in (('config',settings),('identity',identity),('load',load),('close',close)):
    api.write(actor/(name+'.json'),value)
times = dict(model_load=0.0,generation_calls=0.0,actor_operations=0)
api.write(root/'inputs.json',inputs)
api.write(root/'readout_config.json',settings)
api.write(root/'actor_close.json',close)
api.write(root/'custody.json',dict(kind=identity['kind'],route=route,calls=16,identity_sha256=api.prefix.digest(identity),elapsed_seconds=times))
api.write(root/'scores.json',dict(state=state,denominator=16,results=results,panels=panels,pass_threshold=None))
if mode == 'adapter' and adapter: (root/'adapter/adapter_model.safetensors').write_bytes(b'MUTATED_SYNTHETIC_ADAPTER')
if mode == 'fitdrift' and checkpoint: (checkpoint/'adapter_model.safetensors').write_bytes(b'MUTATED_SYNTHETIC_FIT')
if mode == 'failure': api.write(root/'failure.json',{'error':'ORIGINAL READOUT FAILURE'})
receipt = dict(schema=api.SCHEMA+'/completed',status='COMPLETE',kind='NATIVE',state=state,
    inputs=dict(path=path,sha256=checksum),material_sha256=inputs['material']['sha256'],spec_sha256=material['spec']['sha256'],
    import_sha256=material['spec']['import_sha256'],fit_receipt=inputs.get('fit_receipt'),route=route,calls=16,fits=0,updates=0,
    panels=panels,tokens={'prompt':16,'output':16},truncated=0,elapsed_seconds={**times,'worker':time.monotonic()-started},
    original_status='FORMATION_FAILED',limits=api.sequence.LIMITS,files=api.v3._warm_inventory(root),
    outer_release_required=True,gpu_released=False,full_contract_released=False,automatic_promotion=False)
if mode == 'count': receipt['calls'] = 15
if mode == 'state': receipt['state'] = 'FRESH_MIX'
if mode == 'fitpin': receipt['fit_receipt'] = {'path':'/wrong','sha256':'0'*64}
if mode == 'injected': receipt['kind'] = 'INJECTED_CPU_TEST'
if mode == 'panels': receipt['panels']['W0']['A']['correct'] = 4
if mode == 'release': receipt['gpu_released'] = True
receipt = api.prefix.seal(receipt)
if mode == 'seal': receipt['sha256'] = '0'*64
api.write(root/'completed.json',receipt)
if mode == 'inventory': (root/'scores.json').write_bytes(b'CHANGED')
sys.exit(7 if mode == 'nonzero' else 0)
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
        self.stage, self.state = "fit", None
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
        self.assertEqual(argv[:4], [self.python, "-B", "-m", "gpu.astra_pcfl_event_sequence_" + self.stage])
        expected = {"--inputs": str(self.path), "--inputs-sha256": self.inputs_hash,
                    "--output": str(self.output / self.stage),
                    "--phase" if self.stage == "fit" else "--state": self.phase if self.stage == "fit" else self.state}
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
        script = CHILD if self.stage == "fit" else READOUT_CHILD
        args = [self.phase, self.mode] if self.stage == "fit" else [self.state, self.mode, argv[argv.index("--deadline") + 1]]
        child = REAL_POPEN([self.python, "-B", "-c", script, str(self.path), self.inputs_hash,
                           str(self.output / self.stage), *args], **kwargs)
        self.children.append(child)
        return child

    def run_controller(self):
        return outer.controller(str(self.path), self.inputs_hash, str(self.allocation_path), self.allocation_hash,
                                str(self.output), outer_sha256=self.source_hash, phase=self.phase, stage=self.stage, state=self.state)

    def prepare_readout(self, state="NO_WRITE"):
        records = [{"bank": "A" if index < 4 else "B", "index": index,
                    "request": "READ EVENT E_" + "ABCDEFGH"[index] * 10,
                    "target": outer.fit.sequence.core.EVENT_WIRE.format(event="E_" + "ABCDEFGH"[index] * 10,
                        source="N_AAAAAAAAAA", port="P_AAAAAAAAAA", destination="N_BBBBBBBBBB", receipt="R_AAAAAAAAAA")}
                   for index in range(8)]
        roster = [{"id": f"synthetic-W{view}-{index}", "request": row["request"], "view": view, "seed": index, "output_tokens": 2048}
                  for view in (0, 8) for index, row in enumerate(records)]
        material = outer.read(self.inputs["material"]["path"])
        material["spec"] = outer.fit.prefix.seal({"import_sha256": "a" * 64, "records": records,
            "roster": roster, "roster_sha256": outer.fit.prefix.digest(roster)})
        material["tokenizer_receipt"] = {"tokenizer_files": {}, "chat_template_sha256": "c" * 64}
        material.pop("sha256")
        Path(self.inputs["material"]["path"]).write_bytes(outer.fit.prefix.canonical(outer.fit.prefix.seal(material)))
        self.inputs["material"]["sha256"] = outer.fit.file_hash(self.inputs["material"]["path"])
        self.save()
        if state != "NO_WRITE":
            self.assertEqual(self.run_controller()["status"], "COMPLETED")
            fit_root = self.output / "fit"
            self.inputs["fit_receipt"] = {"path": str(fit_root / "completed.json"), "sha256": outer.fit.file_hash(fit_root / "completed.json")}
            self.fit_inventory = outer.fit.v3._warm_inventory(fit_root)
            self.children.clear()
            self.events.clear()
        else:
            self.inputs["fit_receipt"] = None
        self.stage, self.state, self.output = "readout", state, self.root / "cold"
        self.inputs["schema"] = outer.readout.SCHEMA + "/inputs"
        self.inputs["source_files"] = outer.readout.source_files()
        shutdown = self.prepared / "shutdown.py"
        shutdown.write_text("SYNTHETIC_SHUTDOWN_SOURCE_ONLY\n")
        self.inputs["shutdown_binding"] = {"path": str(shutdown), "sha256": outer.fit.file_hash(shutdown)}
        self.save()

    def test_readout_base_and_fitted_lifecycle_preserve_fit_and_failed_scores(self):
        self.prepare_readout("S_A")
        for state in ("S_A", "NO_WRITE"):
            with self.subTest(state=state):
                self.state, self.output = state, self.root / ("cold_" + state)
                fit_root = Path(self.inputs["fit_receipt"]["path"]).parent
                if state == "NO_WRITE": self.inputs["fit_receipt"] = None
                self.save()
                result = self.run_controller()
                self.assertEqual(result["status"], "COMPLETED", result["errors"])
                self.assertEqual((result["stage"], result["state"]), ("readout", state))
                self.assertTrue(result["gpu_released"])
                receipt = outer.read(self.output / "readout/completed.json")
                self.assertEqual(receipt["calls"], 16)
                self.assertFalse(receipt["gpu_released"] or receipt["automatic_promotion"])
                self.assertTrue(all(panel["correct"] == 0 for view in receipt["panels"].values() for panel in view.values()))
                self.assertEqual((self.output / "readout_completed.json").read_bytes(), (self.output / "readout/completed.json").read_bytes())
                self.assertEqual(outer.fit.v3._warm_inventory(fit_root), self.fit_inventory)

    def test_readout_receipt_custody_and_capture_mismatches_fail_collection(self):
        self.prepare_readout()
        for mode in ("count", "state", "fitpin", "injected", "seal", "inventory", "identity", "close", "shutdown",
                     "raw", "rawkind", "tokens", "sampling", "request", "settings", "panels", "release", "failure", "nonzero"):
            with self.subTest(mode=mode):
                self.mode, self.output = mode, self.root / mode
                result = self.run_controller()
                self.assertEqual(result["status"], "FAILED", result)
                self.assertTrue(result["gpu_released"])
                self.assertEqual(result["returncode"], 7 if mode == "nonzero" else 0)
                if mode == "failure":
                    self.assertEqual(outer.read(self.output / "readout/failure.json"), {"error": "ORIGINAL READOUT FAILURE"})

    def test_readout_adapter_and_immutable_fit_drift_fail(self):
        self.prepare_readout("S_A")
        for mode in ("adapter", "fitdrift"):
            self.mode, self.output = mode, self.root / mode
            result = self.run_controller()
            self.assertEqual(result["status"], "FAILED", result)
            self.assertEqual(result["returncode"], 0)
            self.assertTrue(any(error["phase"] == "stage_evidence" for error in result["errors"]))

    def test_readout_pins_state_and_resources_prevent_launch(self):
        self.prepare_readout()
        original = copy.deepcopy(self.inputs)
        for mode in ("missingfit", "fitforbase", "source", "shutdown", "roster", "gpu", "cvd"):
            with self.subTest(mode=mode):
                self.inputs, self.state = copy.deepcopy(original), "NO_WRITE"
                self.output = self.root / mode
                self.pre_busy, self.cvd_busy = mode == "gpu", mode == "cvd"
                if mode == "missingfit": self.state = "S_A"
                if mode == "fitforbase": self.inputs["fit_receipt"] = self.inputs["material"]
                if mode == "source": self.inputs["source_files"].pop(str(Path(outer.readout.__file__).resolve()))
                if mode == "shutdown": self.inputs["shutdown_binding"]["sha256"] = "0" * 64
                if mode == "roster": self.inputs["schema"] = outer.fit.SCHEMA + "/inputs"
                self.save()
                self.assertEqual(self.run_controller()["status"], "FAILED")
        self.assertEqual(self.children, [])

    def test_readout_wrong_fit_phase_and_failed_receipt_never_launch(self):
        self.prepare_readout("S_A")
        self.state = "FRESH_MIX"
        self.assertEqual(self.run_controller()["status"], "FAILED")
        self.state, self.output = "S_A", self.root / "failed_fit"
        outer.write(Path(self.inputs["fit_receipt"]["path"]).parent / "failure.json", {"error": "ORIGINAL FIT FAILURE"})
        self.assertEqual(self.run_controller()["status"], "FAILED")
        self.assertEqual(self.children, [])

    def test_readout_timeout_and_unknown_pid_cleanup(self):
        self.prepare_readout()
        self.mode = "timeout"
        with patch.object(outer, "TOTAL_SECONDS", 1.2), patch.object(outer, "CLEANUP_SECONDS", .5):
            self.assertEqual(self.run_controller()["status"], "FAILED")
        self.assertEqual(self.children[-1].returncode, -signal.SIGTERM)
        self.mode, self.output = "short", self.root / "unknown"
        def identify(pid):
            if pid == os.getpid(): return REAL_IDENTITY(pid)
            raise PermissionError("SYNTHETIC unreadable PID")
        with patch.object(outer.lifecycle, "identity", side_effect=identify), patch.object(outer.lifecycle, "cleanup_owned") as cleanup, patch.object(os, "killpg") as kill:
            result = self.run_controller()
        self.assertEqual(result["status"], "FAILED")
        self.assertFalse(result["gpu_released"])
        cleanup.assert_not_called()
        kill.assert_not_called()

    def test_standalone_controller_pins_itself_but_uses_imported_worker_source(self):
        self.prepare_readout()
        standalone = self.root / "standalone.py"
        standalone.write_bytes(Path(outer.__file__).read_bytes())
        with patch.object(outer, "__file__", str(standalone)):
            self.assertEqual(self.run_controller()["status"], "COMPLETED")
        binding = outer.read(self.output / "binding.json")
        self.assertEqual(binding["source_root"], str(Path(outer.fit.__file__).resolve().parents[1]))
        with self.assertRaises(FileExistsError): self.run_controller()

    def test_cli_readout_requires_explicit_state_and_fit_remains_default(self):
        args = ["--inputs", str(self.path), "--inputs-sha256", self.inputs_hash, "--allocation", str(self.allocation_path),
                "--allocation-sha256", self.allocation_hash, "--outer-sha256", self.source_hash, "--outer", str(self.output)]
        with patch.object(outer, "controller", return_value={"status": "COMPLETED"}) as controller:
            self.assertEqual(outer.main(args), 0)
            self.assertEqual(controller.call_args.kwargs, dict(outer_sha256=self.source_hash, phase="S_A", stage="fit", state=None))
            self.assertEqual(outer.main([*args, "--stage", "readout", "--state", "NO_WRITE"]), 0)
            self.assertEqual(controller.call_args.kwargs["state"], "NO_WRITE")
        self.stage = "readout"
        with self.assertRaises(ValueError): self.run_controller()

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
