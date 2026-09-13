"""Synthetic CPU provenance/captures and harmless detached processes; no models."""

import copy
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from gpu import astra_level1_prediction_transfer_readout as api


RECEIPTS = Path(__file__).resolve().parents[1] / "research_notes/astra_memos/receipts_20260912"
RUNTIME = RECEIPTS / "astra_level1_skill_run_20260913.py"
PUBLIC = RECEIPTS / "astra_birth_skill_probe_query_fixed_20260913.py"
ORIGINAL_MATERIAL = RECEIPTS / "astra_level1_prediction_goal_material_20260913.py"
REFLECTION = RECEIPTS / "astra_reflection_fit_run_20260913.py"
REAL_POPEN, REAL_IDENTITY = subprocess.Popen, api.lifecycle.identity
CHILD = r'''
import pathlib, sys, time
from unittest.mock import patch
from gpu import astra_level1_prediction_transfer_readout as api
root, pin, state, deadline, mode = sys.argv[1:]
if mode == 'timeout': time.sleep(60)
if mode == 'short': time.sleep(.2)
plan = api.read(pathlib.Path(root)/'plan.json')
spec = plan['spec']
runtime = api.load_module(spec['runtime'], 'synthetic_runtime')
parent = api.read(spec['original_plan']['path'])
probe = runtime.load_probe(parent['specification']['public']['path'], parent['specification']['public']['sha256'])
allocation = api.read(spec['allocation']['path'])
calls = api.read(pathlib.Path(root)/'calls.json')
rows = api.read(pathlib.Path(root)/'material.json')['rows']
class Session:
    def __init__(self, adapter):
        self.index = 0
        self.route = None if adapter is None else dict(name='level1_skill',id=1,path=adapter)
    def generate(self, messages):
        call, row = calls[self.index], rows[self.index]
        self.index += 1
        assert call['messages'] == messages
        raw = row['raw_target'] if state == 'post' else '{}'
        finish = 'stop'
        if mode == 'length': raw, finish = '{}' + ' '*190, 'length'
        response = dict(**call['native'], text=raw, decoded_output=raw, output_token_ids=list(raw.encode()),
            actual_prompt_token_ids=call['native']['prompt_token_ids'], finish_reason=finish, stop_reason=None,
            started=time.monotonic(), ended=time.monotonic(), lora_request=self.route)
        if mode == 'route': response['lora_request'] = {'wrong':'route'}
        if mode == 'tokens': response['actual_prompt_token_ids'] = [123]
        if mode == 'decoded': response['decoded_output'] = 'OTHER'
        return response
    def close(self):
        return {'source':spec['shutdown_binding'], 'shutdown_returned':mode != 'shutdown'}
bound = (runtime,None,parent,probe,plan['adapter'],plan['adapter_files'],allocation)
with patch.object(api,'verify',return_value=(plan,bound)), patch.object(api,'backend',side_effect=lambda runtime,parent,probe,adapter,pin:Session(adapter)):
    api.worker(root,pin,state,float(deadline),allow_gpu=True)
'''


class Tokenizer:
    chat_template = "SYNTHETIC_QWEN_TEMPLATE"

    def encode(self, text, add_special_tokens=False):
        return list(text.encode())

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True):
        text = "<|im_start|>system\nSYNTHETIC GENERIC SYSTEM<|im_end|>\n"
        text += "".join(f"<|im_start|>{message['role']}\n{message['content']}<|im_end|>\n" for message in messages)
        text += "<|im_start|>assistant\n"
        return self.encode(text) if tokenize else text


class TransferTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="SYNTHETIC_PREDICTION_TRANSFER_")
        self.addCleanup(temporary.cleanup)
        self.home = Path(temporary.name)
        self.root, self.out = self.home / "transfer", self.home / "collected"
        self.runtime = api.load_module(self.pin(RUNTIME), "synthetic_parent_runtime")
        self.probe = self.runtime.load_probe(str(PUBLIC), self.runtime.digest(PUBLIC))
        self.material_path = Path(api.__file__).resolve().parents[1] / "organism_v6/level1_prediction_transfer.py"
        self.material = api.load_module(self.pin(self.material_path), "synthetic_transfer_material")
        self.parent_root, self.source, self.model = (self.home / name for name in ("parent", "source", "model"))
        self.parent_root.mkdir()
        self.model.mkdir()
        for name in self.runtime.SOURCE_NAMES:
            path = self.source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("SYNTHETIC PINNED SOURCE ONLY\n")
        self.protocol = self.home / "protocol.md"
        self.protocol.write_text("SYNTHETIC DECLARED NO-FIT DEV ONLY")
        self.shutdown = self.home / "shutdown.py"
        self.shutdown.write_text("SYNTHETIC ENGINE CLOSE SOURCE")
        self.original_spec = {"runner_sha256": self.runtime.digest(RUNTIME), "source": str(self.source),
            "source_files": self.runtime.tree(self.source), "material": self.pin(ORIGINAL_MATERIAL),
            "public": self.pin(PUBLIC), "reflection": self.pin(REFLECTION),
            "protocol": self.pin(self.protocol), "binding": self.pin(self.protocol)}
        self.parent = {"root": str(self.parent_root), "scope": self.runtime.SCOPE, "skill": "prediction", "learner_seed": 0,
            "self_sha256": self.runtime.digest(RUNTIME), "specification": self.original_spec, "source": str(self.source),
            "model": str(self.model), "model_files": {"SYNTHETIC.safetensors": "a"*64}, "environment": {"SYNTHETIC": True},
            "python": os.path.abspath(sys.executable), "python_sha256": self.runtime.digest(sys.executable),
            "engine": self.runtime.ENGINE, "params": self.runtime.PARAMS, "chat_template": Tokenizer.chat_template,
            "binding": {"revision": "SYNTHETIC"}, "config": {"target_modules": ["q_proj"]}}
        self.original_artifacts()
        queue = self.home / "queue"
        for name in ("pending", "running"): (queue / name).mkdir(parents=True)
        self.allocation = {"schema": api.lifecycle.SCHEMA + "/allocation", "gpu_index": 0, "gpu_uuid": "GPU-SYNTHETIC",
            "uid": os.getuid(), "boot_id": api.lifecycle.boot_id(), "python": os.path.abspath(sys.executable),
            "queue_dir": str(queue), "queue_mode": "direct", "queue_allowlist": {"pending": {}, "running": {}},
            "coordination_owners": [], "service_exceptions": [], "lease_end": time.time() + 40000,
            "lease_margin_seconds": 21600, "outer_sha256": api.lifecycle.file_hash(api.SELF)}
        self.allocation_path = self.home / "allocation.json"
        api.write(self.allocation_path, self.allocation)
        self.spec = {"schema": api.SCHEMA + "/spec", "self_sha256": api.lifecycle.file_hash(api.SELF), "source_files": api.source_files(),
            "runtime": self.pin(RUNTIME), "material": self.pin(self.material_path), "protocol": self.pin(self.protocol),
            "shutdown_binding": self.pin(self.shutdown), "allocation": self.pin(self.allocation_path), "learner_seed": 0,
            "original_plan": self.pin(self.parent_root / "plan.json"), "original_completion": self.pin(self.parent_root / "capture_complete.json"),
            "original_collection": self.pin(self.home / "old_collected/collection.json")}
        self.spec_path = self.home / "spec.json"
        api.write(self.spec_path, self.spec)
        self.children, self.mode, self.busy, self.unreadable = [], "complete", False, False
        self.addCleanup(self.reap)
        self.patch(patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": ""}))
        self.patch(patch.object(self.runtime, "load_probe", return_value=self.probe))
        self.patch(patch.object(self.runtime, "environment", return_value=self.parent["environment"]))
        self.patch(patch.object(self.probe, "model_hashes", return_value=self.parent["model_files"]))
        self.patch(patch.object(self.probe, "native_tokenizer", return_value=Tokenizer()))
        loader = api.load_module
        def load(pin, name):
            api.pin_file(pin)
            if name == "prediction_transfer_runtime": return self.runtime
            if name == "prediction_transfer_material": return self.material
            return loader(pin, name)
        self.patch(patch.object(api, "load_module", side_effect=load))
        self.patch(patch.object(api.time, "sleep", return_value=None))
        self.patch(patch.object(api.subprocess, "Popen", side_effect=self.spawn))
        self.patch(patch.object(api.lifecycle, "check_gpu", side_effect=lambda allocation, deadline: {"empty": not self.busy}))
        self.patch(patch.object(api.lifecycle, "check_cvd", side_effect=lambda allocation, deadline, release: {"clear": not self.unreadable}))
        for name in ("fit_one", "controller", "worker", "capture_cell"):
            self.patch(patch.object(self.runtime, name, side_effect=AssertionError("no historical execution: " + name)))

    def patch(self, context):
        result = context.start()
        self.addCleanup(context.stop)
        return result

    def pin(self, path):
        return {"path": str(path), "sha256": api.lifecycle.file_hash(path)}

    def original_artifacts(self):
        runtime, root = self.runtime, self.parent_root
        prepared = {"items": [{}] * 96, "epochs_run": 14, "target_tokens": 96, "total_tokens": 192, "actual_train_tokens": 2560}
        runtime.write(root / "train.json", prepared)
        runtime.write(root / "material.json", {"SYNTHETIC": True})
        runtime.write(root / "costs.json", {"SYNTHETIC": True})
        calls = [{"call_id": f"old_{index:02d}", "messages": [{"role": "user", "content": "SYNTHETIC OLD"}],
                  "native": self.probe.render(Tokenizer(), [{"role": "user", "content": "SYNTHETIC OLD"}])} for index in range(60)]
        runtime.write(root / "calls.json", calls)
        self.parent["input_hashes"] = {name: runtime.digest(root / name) for name in ("train.json", "material.json", "costs.json", "calls.json")}
        runtime.write(root / "plan.json", self.parent)
        plan_pin = runtime.digest(root / "plan.json")
        adapter = root / "run/fit/adapter"
        adapter.mkdir(parents=True)
        runtime.write(adapter / "adapter_config.json", {"r": 8, "lora_alpha": 16, "lora_dropout": .05, "bias": "none", "target_modules": ["q_proj"]})
        (adapter / "adapter_model.safetensors").write_bytes(b"SYNTHETIC NOT TENSORS")
        (adapter / "DONE").write_text("SYNTHETIC DONE")
        runtime.write(adapter / "train_manifest.json", {"config": self.parent["config"], "empty": False, "steps": 320, "micro_batches": 320,
            "epochs_run": 14, "nonfinite_batches": 0, "corpus": {"n_items": 96, "n_encoded": 96, "n_skipped_no_target": 0},
            "truncation": dict.fromkeys(("items_truncated", "context_tokens_dropped", "target_tokens_dropped", "items_split"), 0),
            "packing": {"mode": "one_item_per_sequence", "n_sequences": 96}, "tokens": {"target": 96, "total": 192},
            "train_tokens_seen": 2560, "mean_loss_per_epoch": [.5] * 14, "final_loss": .5})
        files = runtime.tree(adapter)
        runtime.write(adapter.parent / "fit.json", {"adapter": str(adapter), "updates": 320, "presentations": 1280, "adapter_files": files})
        for index, stage in enumerate(runtime.STAGES):
            directory = root / "run" / stage
            directory.mkdir(exist_ok=True)
            identity = {"pid": 90000 + index, "pgid": 90000 + index, "stage": stage, "plan_sha256": plan_pin}
            for name in ("launch.json", "started.json", "released.json"): runtime.write(directory / name, identity)
            if stage == "fit": continue
            route = None if stage == "OFF" else {"name": "level1_skill", "id": 1, "path": str(adapter)}
            runtime.write(directory / "identity.json", {"cell": stage, "model": self.parent["model"], "revision": "SYNTHETIC",
                "model_files": self.parent["model_files"], "adapter": None if stage == "OFF" else str(adapter),
                "adapter_files": {} if stage == "OFF" else files, "lora_request": route, "engine": runtime.ENGINE, "params": runtime.PARAMS})
            names = ["identity.json"]
            for call in calls:
                response = {**call["native"], "text": "{}", "decoded_output": "{}", "output_token_ids": [1, 2],
                    "actual_prompt_token_ids": call["native"]["prompt_token_ids"], "finish_reason": "stop", "stop_reason": None,
                    "started": 1., "ended": 2., "lora_request": route}
                for suffix, value in ((".request.json", call), (".response.json", response)):
                    name = call["call_id"] + suffix
                    runtime.write(directory / name, value)
                    names.append(name)
            runtime.write(directory / "closed.json", {"calls": 60, "files": {name: runtime.digest(directory / name) for name in names}})
        runtime.write(root / "capture_complete.json", {"calls": 120, "scored": False, "plan_sha256": plan_pin,
            "stages": runtime.validate_completed(self.parent, plan_pin, self.probe)})
        collected = self.home / "old_collected"
        collected.mkdir()
        runtime.write(collected / "scores.json", {"plan_sha256": plan_pin, "skill": "prediction", "learner_seed": 0})
        runtime.write(collected / "collection.json", {"completion_sha256": runtime.digest(root / "capture_complete.json"), "scores_sha256": runtime.digest(collected / "scores.json")})

    def reap(self):
        for child in self.children: child.wait(timeout=5)

    def spawn(self, argv, **kwargs):
        self.assertTrue(kwargs["start_new_session"])
        self.assertEqual(kwargs["stdin"], subprocess.DEVNULL)
        self.assertEqual(argv[:4], [os.path.abspath(sys.executable), "-B", str(api.SELF), "worker"])
        self.assertEqual(kwargs["env"]["CUDA_VISIBLE_DEVICES"], self.allocation["gpu_uuid"])
        state, deadline = argv[argv.index("--state") + 1], argv[argv.index("--deadline") + 1]
        child = REAL_POPEN([sys.executable, "-B", "-c", CHILD, str(self.root), self.plan_pin, state, deadline, self.mode], **kwargs)
        self.children.append(child)
        return child

    def prepare(self):
        receipt = api.prepare(str(self.root), str(self.spec_path), api.lifecycle.file_hash(self.spec_path), allow_native=True)
        self.plan_pin = receipt["plan_sha256"]
        return receipt

    def complete(self):
        self.prepare()
        self.completion = api.controller(str(self.root), self.plan_pin, allow_gpu=True)["completion_sha256"]

    def collect(self):
        return api.collect(str(self.root), self.plan_pin, self.completion, str(self.out))

    def test_real_paired_processes_collect_frozen_material_and_old_parent_unchanged(self):
        before = self.runtime.tree(self.parent_root)
        self.complete()
        result = self.collect()
        self.assertEqual(result["collection_sha256"], api.lifecycle.file_hash(self.out / "collection.json"))
        report = api.read(self.out / "scores.json")
        self.assertEqual((report["calls"], report["fits"], report["updates"]), (96, 0, 0))
        self.assertEqual(len({child.pid for child in self.children}), 2)
        for view in api.VIEWS:
            self.assertEqual(report["summaries"]["post"][view]["content_correct"], 24)
            self.assertEqual(report["post_minus_OFF"][view]["post_minus_OFF"], 24)
        self.assertEqual(before, self.runtime.tree(self.parent_root))
        self.assertFalse(report["automatic_pass"])
        self.assertIsNone(report["scientific_pass"])
        for call, row in zip(api.read(self.root / "calls.json"), self.material.build_material()["rows"]):
            self.assertEqual(call["messages"], row["input_messages"])
            self.assertEqual(set(call), {"call_id", "row_id", "messages", "native"})
        self.assertEqual(api.read(self.root / "controller_started.json")["deadline"] - api.read(self.root / "controller_started.json")["started"], 1800)

    def test_tracked_receipts_match_original_runtime_dependency_pins(self):
        for path, expected in (
            (RUNTIME, "6f4c391419500d046e2b15729ee09485baa07b45938db1f96484b07e69e1ed9e"),
            (PUBLIC, "59874c678ce1b36feaa1969721c0dcc761b4fa05072a6231892269991201052c"),
            (ORIGINAL_MATERIAL, "3da282322f65525271a48b628b30ecdc8a2fba6ba6ba84d8cf1f3e65ad6d6433"),
            (REFLECTION, "0f79efa1f4e4da6a9d1ec245c09e665f7c2b7d8bce31f7e01fe01b00f95a72fc"),
        ):
            with self.subTest(path=path):
                self.assertTrue(path.is_relative_to(RECEIPTS))
                self.assertEqual(api.lifecycle.file_hash(path), expected)

    def test_wrong_and_length_outputs_complete_without_rescue(self):
        self.mode = "length"
        self.complete()
        self.collect()
        report = api.read(self.out / "scores.json")
        self.assertEqual(report["summaries"]["post"]["MINIMAL"]["content_correct"], 0)
        self.assertEqual(report["summaries"]["post"]["MINIMAL"]["finish_reasons"], {"length": 24})
        self.assertEqual(report["costs"]["post"]["output_tokens"], 48 * 192)
        self.assertEqual(report["cells"]["post"][0]["raw"], "{}" + " " * 190)

    def test_bad_native_bytes_tokens_route_or_close_never_score(self):
        for mode in ("route", "tokens", "decoded", "shutdown"):
            with self.subTest(mode=mode):
                self.root, self.mode = self.home / mode, mode
                self.prepare()
                with self.assertRaises(ValueError): api.controller(str(self.root), self.plan_pin, allow_gpu=True)
                self.assertTrue((self.root / "controller_failure.json").exists())
                self.assertFalse((self.root / "capture_complete.json").exists())
                self.assertTrue((self.root / "run/OFF/call_00.response.json").exists())

    def test_busy_gpu_or_unreadable_cvd_never_spawns(self):
        for mode in ("gpu", "cvd"):
            self.root = self.home / mode
            self.busy, self.unreadable = mode == "gpu", mode == "cvd"
            self.prepare()
            with self.assertRaises(ValueError): api.controller(str(self.root), self.plan_pin, allow_gpu=True)
        self.assertEqual(self.children, [])

    def test_timeout_cleans_only_owned_group_and_unknown_pid_never_killed(self):
        self.prepare()
        self.mode = "timeout"
        with patch.object(self.runtime, "READOUT_SECONDS", .5):
            with self.assertRaises(ValueError): api.controller(str(self.root), self.plan_pin, allow_gpu=True)
        self.assertEqual(self.children[-1].returncode, -signal.SIGTERM)
        self.root, self.mode = self.home / "unknown", "short"
        self.prepare()
        def identity(pid):
            if pid == os.getpid(): return REAL_IDENTITY(pid)
            raise PermissionError("SYNTHETIC unknown process")
        with patch.object(api.lifecycle, "identity", side_effect=identity), patch.object(api.lifecycle, "cleanup_owned") as cleanup, patch.object(os, "killpg") as kill:
            with self.assertRaises(ValueError): api.controller(str(self.root), self.plan_pin, allow_gpu=True)
        cleanup.assert_not_called()
        kill.assert_not_called()

    def test_parent_adapter_source_and_completion_pins_reject_drift(self):
        self.prepare()
        for path in (self.source / self.runtime.SOURCE_NAMES[0], self.parent_root / "run/fit/adapter/adapter_model.safetensors",
                     self.parent_root / "capture_complete.json", self.protocol):
            with self.subTest(path=path):
                original = path.read_bytes()
                path.write_bytes(original + b"MUTATION")
                with self.assertRaises(ValueError): api.verify(str(self.root), self.plan_pin)
                path.write_bytes(original)
        self.assertEqual(self.children, [])

    def test_seed_selection_no_fit_and_failed_original_are_rejected(self):
        for mutation in ({"learner_seed": 2}, {"learner_seed": True}):
            spec = {**self.spec, **mutation}
            with self.assertRaises(ValueError): api.inputs(spec)
        (self.parent_root / "controller_failure.json").write_text("{}")
        with self.assertRaises(ValueError): api.inputs(self.spec)
        with self.assertRaises(ValueError): api.worker(str(self.root), "0" * 64, "fit", time.monotonic() + 1, allow_gpu=True)

    def test_freshness_collection_hash_and_receipt_tamper(self):
        self.complete()
        with self.assertRaises(FileExistsError): self.prepare()
        with self.assertRaises(FileExistsError): api.controller(str(self.root), self.plan_pin, allow_gpu=True)
        with self.assertRaises(ValueError): api.collect(str(self.root), self.plan_pin, "0" * 64, str(self.out))
        self.collect()
        with self.assertRaises(ValueError): self.collect()
        self.out = self.home / "another_collection"
        with self.assertRaises(FileExistsError): self.collect()

    def test_sealed_capture_mutation_fails_collection_once(self):
        self.complete()
        path = self.root / "run/post/call_00.response.json"
        response = api.read(path)
        response["lora_request"] = None
        path.write_bytes(self.runtime.encoded(response))
        with self.assertRaises(ValueError): self.collect()
        self.assertTrue((self.out / "collection_failure.json").exists())
        self.assertFalse((self.out / "scores.json").exists())

    def test_collection_is_within_original_1800_seconds(self):
        self.complete()
        with patch.object(api.lifecycle.time, "monotonic", return_value=api.read(self.root / "capture_complete.json")["deadline"] + 1):
            with self.assertRaises(ValueError): self.collect()
        self.assertFalse((self.out / "scores.json").exists())

    def test_material_count_prompt_or_scorer_pin_tampering(self):
        data = self.material.build_material()
        for mode in ("count", "prompt", "pin"):
            changed = copy.deepcopy(data)
            if mode == "count": changed["rows"].pop()
            if mode == "prompt": changed["rows"][0]["input_messages"].append({"role": "assistant", "content": changed["rows"][0]["raw_target"]})
            if mode == "pin": changed["original_material"]["sha256"] = "0" * 64
            with patch.object(self.material, "build_material", return_value=changed):
                with self.assertRaises(ValueError): api.material_rows(self.material, self.parent)

    def test_native_backend_reuses_generate_and_closes_bound_enginecore(self):
        source = self.home / "synthetic_engine.py"
        source.write_text("class Engine:\n    closed = False\n    def shutdown(self):\n        self.closed = True\n")
        module = api.load_module(self.pin(source), "synthetic_engine")
        engine = module.Engine()
        class Native:
            def __init__(self, parent, probe, adapter):
                self.llm = SimpleNamespace(llm_engine=SimpleNamespace(engine_core=engine))
            def generate(self, messages):
                return "INHERITED_GENERATE"
        with patch.object(self.runtime, "Native", Native):
            session = api.backend(self.runtime, self.parent, self.probe, None, self.pin(source))
            self.assertEqual(session.generate([]), "INHERITED_GENERATE")
            self.assertEqual(session.close(), {"source": self.pin(source), "shutdown_returned": True})
            self.assertTrue(engine.closed)
            engine.closed = False
            session = api.backend(self.runtime, self.parent, self.probe, None, self.pin(self.shutdown))
            with self.assertRaises(ValueError): session.close()
            self.assertFalse(engine.closed)

    def test_post_release_failure_preserved_and_no_second_state(self):
        self.prepare()
        with patch.object(api.lifecycle, "check_gpu", side_effect=lambda allocation, deadline: {"empty": not self.children}):
            with self.assertRaises(ValueError): api.controller(str(self.root), self.plan_pin, allow_gpu=True)
        self.assertEqual(len(self.children), 1)
        self.assertTrue((self.root / "run/OFF/released.json").exists())
        self.assertTrue((self.root / "run/OFF/stage_failure.json").exists())
        self.assertFalse((self.root / "run/post").exists())


if __name__ == "__main__":
    unittest.main()
