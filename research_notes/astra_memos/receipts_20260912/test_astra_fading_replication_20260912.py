"""CPU fixtures only; no native models, subprocesses, or GPU probes."""
import copy
import importlib.util
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location("replication", "/tmp/astra_fading_replication_20260912.py")
rep = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rep)
rep.bind(Path.cwd(), "/tmp/astra_fading_sentinel_20260912.py")


class Tokenizer:
    def apply_chat_template(self, messages, **kwargs):
        return "fixture user:" + messages[0]["content"] + "\nassistant:"

    def encode(self, text):
        return list(text.encode())

    def decode(self, tokens, **kwargs):
        return bytes(tokens).decode()


class ReplicationTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="plasticity-fixture-")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.parents = self.root / "parents"
        self.model = self.root / "model"
        self.model.mkdir()
        self.material = self.root / "material"
        self.material.mkdir()
        self.out = self.root / "run"
        self.end = time.time() + 7200
        self.model_files = {"fixture": "base-bytes"}
        self.pins = {}
        self.addCleanup(patch.stopall)
        patch.object(rep.base, "model_hashes", return_value=self.model_files).start()
        patch.object(rep.base, "native_tokenizer", return_value=Tokenizer()).start()
        patch.object(rep.material, "verify", return_value={}).start()
        patch.object(rep.trainer, "_warm_parent", return_value={}).start()
        patch.object(rep.base.supervisor, "gpu_processes_absent", return_value=True).start()
        for seed in (1, 2):
            self.make_parent(seed)
        patch.object(rep, "PINS", self.pins).start()
        rep.old.write(self.material / "manifest.json", dict(status="NATIVE_V3_TOKEN_AUDIT_COMPLETE",
            native_token_audit=True, tokenizer_injected=False, model=str(self.model), model_files=self.model_files,
            phase_corpora={phase: phase + ".json" for phase in rep.old.PHASES}))
        for phase in rep.old.PHASES:
            rep.old.write(self.material / (phase + ".json"), {"fixture": phase})

    def receipt(self):
        return dict(ok=True, reservation_release_verified=True, owned_group_empty=True,
                    gpu_processes_absent=True, reserved_seconds=1)

    def make_parent(self, seed):
        root = self.parents / f"seed{seed}"
        adapter = root / "fit_teach/adapter"
        adapter.mkdir(parents=True)
        config = rep.old.config(str(self.model), "0")
        config.update(seed=seed, lr=3e-4)
        rep.old.write(adapter / "train_manifest.json", dict(config=config, steps=80))
        (adapter / "DONE").write_text("ok")
        (adapter / "adapter_model.safetensors").write_bytes(b"fixture not real weights")
        rep.old.write(adapter / "adapter_config.json", {"fixture": seed})
        rep.old.seal(root, dict(config=config, replication={"seed": seed}, model=str(self.model), model_files=self.model_files))
        worker = root / "fit_teach/worker"
        worker.mkdir()
        rep.old.write(worker / "supervision.json", self.receipt())
        files = rep.trainer._warm_inventory(adapter)
        rep.old.write(root / "fit_teach/verified.json", dict(seed=seed, arm="teach", adapter=str(adapter), adapter_files=files,
            status="FIT_COMPLETE_PENDING_PAIRED_READOUT", plan_sha256=rep.base.digest(root / "plan.json"), steps=80,
            supervision_sha256=rep.base.digest(worker / "supervision.json")))
        readroot = root / "readouts/teach"
        calls = readroot / "run/data/calls"
        calls.mkdir(parents=True)
        requests = rep.readout.requests(rep.readout.selected_cases())
        inputs = rep.readout.native_inputs(Tokenizer(), requests)
        plan = dict(model=str(self.model), model_files=self.model_files, adapter=str(adapter), adapter_files=files,
                    cases=rep.readout.selected_cases(), requests=requests, native_inputs=inputs, source_hashes={"old": "source"})
        plan["identity"] = rep.base.expected_identity(plan, str(adapter))
        rep.old.seal(readroot, plan)
        for request, native in zip(requests, inputs):
            response = dict(rendered_prompt=native["rendered_prompt"], prompt_token_ids=native["prompt_token_ids"],
                            text="red", output_token_ids=list(b"red"), finish_reason="stop", stop_reason=None)
            rep.old.write(calls / (request["call_id"] + ".request.json"), dict(request=request, identity=plan["identity"],
                prompt_sha256=rep.base.value_hash(request["prompt"])))
            rep.old.write(calls / (request["call_id"] + ".response.json"), dict(response=response, response_sha256=rep.base.value_hash(response)))
        rep.old.write(readroot / "run/data/backend.cleanup.json", {"closed": True})
        (readroot / "run/worker").mkdir()
        rep.old.write(readroot / "run/worker/supervision.json", self.receipt())
        self.pins[str(seed)] = tuple(rep.base.digest(root / name) for name in ("plan.json", "fit_teach/verified.json", "readouts/teach/plan.json"))

    def prepare(self):
        rep.prepare(self.out, self.material, self.parents, self.end, self.end + 100)
        return rep.verify(self.out)

    def test_prepare_six_fixed_branches(self):
        plan = self.prepare()
        self.assertEqual(len(plan["branches"]), 6)
        self.assertEqual([plan["branches"][name]["device"] for name in rep.BRANCHES], ["0", "1", "2", "3", "4", "5"])
        self.assertEqual(plan["phase"], "continuation-phase-01")
        self.assertTrue(all(config["seed"] == 0 for config in plan["rates"].values()))
        self.assertEqual(plan["parents"]["1"]["readout"]["native_inputs"], plan["parents"]["2"]["readout"]["native_inputs"])

    def test_material_never_recreated(self):
        before = rep.base.tree_hashes(self.material)
        self.prepare()
        self.assertEqual(before, rep.base.tree_hashes(self.material))

    def test_stale_output_rejected(self):
        self.prepare()
        with self.assertRaisesRegex(ValueError, "fresh"):
            self.prepare()

    def test_overlapping_output_rejected(self):
        with self.assertRaisesRegex(ValueError, "overlap"):
            rep.fresh(self.parents / "new", [self.parents])

    def test_symlink_output_rejected(self):
        link = self.root / "link"
        link.symlink_to(self.parents, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlink"):
            rep.fresh(link / "new", [self.model])

    def test_bad_pin_rejected_before_writes(self):
        self.pins["1"] = ("bad", "bad", "bad")
        with self.assertRaisesRegex(ValueError, "pinned"):
            self.prepare()
        self.assertFalse(self.out.exists())

    def test_parent_weights_changed_rejected(self):
        (self.parents / "seed1/fit_teach/adapter/adapter_model.safetensors").write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "parent fit"):
            self.prepare()

    def test_missing_response_rejected(self):
        (self.parents / "seed1/readouts/teach/run/data/calls/0000.response.json").unlink()
        with self.assertRaisesRegex(ValueError, "completeness"):
            self.prepare()

    def test_actual_response_prefix_mismatch_rejected(self):
        path = self.parents / "seed1/readouts/teach/run/data/calls/0000.response.json"
        value = rep.base.read(path)
        value["response"]["prompt_token_ids"] = [99]
        value["response_sha256"] = rep.base.value_hash(value["response"])
        path.unlink()
        rep.old.write(path, value)
        with self.assertRaisesRegex(ValueError, "input mismatch"):
            self.prepare()

    def test_changed_sources_rejected(self):
        self.prepare()
        with patch.object(rep, "sources", return_value={}):
            with self.assertRaisesRegex(ValueError, "source"):
                rep.verify(self.out)

    def test_changed_material_rejected(self):
        self.prepare()
        (self.material / (rep.PHASE + ".json")).write_text("changed")
        with self.assertRaisesRegex(ValueError, "material"):
            rep.verify(self.out)

    def test_bounds_include_cleanup_and_lease(self):
        self.assertEqual(rep.bounds(1000, 3000, 4000), 1600)
        self.assertEqual(rep.bounds(1000, 1500, 1400), 1390)
        for values in ((1000, 1100, 4000), (1000, float("nan"), 4000)):
            with self.assertRaises(ValueError):
                rep.bounds(*values)

    def test_fixed_fit_commands_and_parent_chain(self):
        plan = self.prepare()
        for name, branch in rep.BRANCHES.items():
            parent = plan["parents"][str(branch["parent_seed"])]["parent"]
            row = dict(phase=rep.PHASE, parent=parent, adapter=str(self.out / name / "adapter"))
            argv = rep.old.fit_command(plan, branch["rate"], row)
            for flag, value in (("--seed", "0"), ("--epochs", "4"), ("--batch-size", "4"), ("--grad-accum", "1"),
                                ("--init-adapter", parent), ("--rank", "8")):
                self.assertEqual(argv[argv.index(flag) + 1], value)
            self.assertIn(rep.PHASE + ".json", argv[argv.index("--corpus") + 1])

    def test_readplan_retains_exact_inputs_not_outputs(self):
        plan = self.prepare()
        branch = rep.BRANCHES["seed2-rate-1e-4"]
        original = copy.deepcopy(plan["parents"]["2"]["readout"])
        with patch.object(rep.base, "expected_identity", return_value={}):
            result = rep.readplan_for(plan, branch, {"adapter": "child"}, {"adapter_files": {}}, 2500)
        for key in ("cases", "requests", "native_inputs"):
            self.assertEqual(result[key], original[key])
        self.assertEqual(plan["parents"]["2"]["readout"], original)
        self.assertEqual(result["source_hashes"], rep.readout.sources())

    def test_zero_lr_full_state_not_manifest(self):
        state = {"lora": {"shape": [8, 8], "dtype": "bf16", "sha256": "same"}}
        warm = dict(source_state=copy.deepcopy(state), initialized_state=copy.deepcopy(state), final_state=copy.deepcopy(state), new_manifest=True)
        self.assertTrue(rep.old.check_states("0", state, warm, state))
        warm["initialized_state"]["lora"]["sha256"] = "changed"
        with self.assertRaisesRegex(ValueError, "LR0"):
            rep.old.check_states("0", state, warm, state)

    def test_nonzero_state_may_change(self):
        state = {"lora": {"shape": [8, 8], "dtype": "bf16", "sha256": "old"}}
        saved = copy.deepcopy(state)
        saved["lora"]["sha256"] = "new"
        self.assertFalse(rep.old.check_states("3e-5", state, dict(source_state=state, initialized_state=state, final_state=saved), saved))

    def test_no_gpu_authority(self):
        with self.assertRaisesRegex(ValueError, "explicit"):
            rep.run(self.out, "seed1-rate-0")

    def test_wrong_device_rejected(self):
        with patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "5"}):
            with self.assertRaisesRegex(ValueError, "device"):
                rep.run(self.out, "seed1-rate-0", True)

    def test_run_one_phase_no_count_selection(self):
        self.prepare()
        observed = []
        def execute(root, stage, plan, branch, effective):
            observed.append(branch)
            for name in ("fit-worker", "read-worker"):
                (stage / name).mkdir()
                rep.old.write(stage / name / "supervision.json", self.receipt())
            return {"arbitrary_dev_counts": 0}
        with patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "0"}), patch.object(rep, "execute", side_effect=execute), \
                patch.object(rep.signal, "setitimer") as timer:
            result = rep.run(self.out, "seed1-rate-0", True)
        self.assertEqual(len(observed), 1)
        self.assertEqual(result["status"], "COMPLETE")
        self.assertFalse(result["counts_used_for_selection"])
        self.assertLessEqual(result["effective_deadline"] - result["started"], 600)
        self.assertLessEqual(timer.call_args_list[0].args[1], 460)

    def test_partial_no_retry(self):
        self.prepare()
        with patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "0"}), patch.object(rep, "execute", side_effect=ValueError("partial")) as execute:
            with self.assertRaisesRegex(ValueError, "partial branch"):
                rep.run(self.out, "seed1-rate-0", True)
            with self.assertRaisesRegex(ValueError, "fresh"):
                rep.run(self.out, "seed1-rate-0", True)
        self.assertEqual(execute.call_count, 1)
        self.assertEqual(rep.base.read(self.out / "seed1-rate-0/terminal.json")["status"], "FAILED_PARTIAL_NO_RETRY")

    def test_unverified_release_cannot_complete(self):
        self.prepare()
        with patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "0"}), patch.object(rep, "execute", return_value={}), \
                patch.object(rep.base.supervisor, "gpu_processes_absent", return_value=False):
            with self.assertRaisesRegex(ValueError, "partial branch"):
                rep.run(self.out, "seed1-rate-0", True)
        self.assertFalse(rep.base.read(self.out / "seed1-rate-0/terminal.json")["release_verified"])

    def test_cpu_startup_charged_to_outer_bound(self):
        self.prepare()
        clock = time.time() - 30, time.monotonic() - 30
        with patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "0"}), patch.object(rep, "execute", side_effect=ValueError("fixture")), \
                patch.object(rep.signal, "setitimer") as timer:
            with self.assertRaises(ValueError):
                rep.run(self.out, "seed1-rate-0", True, clock=clock)
        terminal = rep.base.read(self.out / "seed1-rate-0/terminal.json")
        self.assertGreaterEqual(terminal["reserved_seconds"], 30)
        self.assertLessEqual(timer.call_args_list[0].args[1], 430)

    def test_execute_one_fit_one_readout_same_bound(self):
        plan = self.prepare()
        stage = self.out / "fixture-execute"
        stage.mkdir()
        branch = rep.BRANCHES["seed2-rate-3e-5"]
        files = plan["parents"]["2"]["parent_files"]
        calls = []
        def supervise(root, active, path, command, call_path=None):
            calls.append((root, active, path, command, call_path))
            return self.receipt()
        def reduce(root):
            value = {"complete": True, "counts": {"total": 48, "arbitrary_science_result": 0}}
            rep.old.write(root / "reduction.json", value)
            return value
        with patch.object(rep.old, "state_inventory", return_value={}), \
                patch.object(rep.old, "verify_fit", return_value={"adapter_files": files}), \
                patch.object(rep, "verify", return_value=plan), \
                patch.object(rep.trainer, "_warm_inventory", return_value=files), \
                patch.object(rep.base, "expected_identity", return_value={}), \
                patch.object(rep.base, "supervise", side_effect=supervise), \
                patch.object(rep.readout, "verify"), patch.object(rep.readout, "reduce", side_effect=reduce):
            rep.execute(self.out, stage, plan, branch, 2000)
        self.assertEqual(len(calls), 2)
        self.assertTrue(all(call[0] == stage and call[1]["lease_end"] == 2000 and call[1]["device"] == "4" for call in calls))
        self.assertIn("--init-adapter", calls[0][3])
        self.assertIn("_worker", calls[1][3])
        self.assertEqual(calls[1][4], stage / "readout/run/data/calls")

    def test_fresh_optimizer_receipt_enforced(self):
        plan = self.prepare()
        parent = plan["parents"]["1"]
        adapter = self.root / "test-child"
        adapter.mkdir()
        (adapter / "DONE").write_text("ok")
        rep.old.write(self.material / "token_audit.json", {"phases": {rep.PHASE: {"per_epoch": {"input_tokens": 100, "target_tokens": 20}}}})
        warm = dict(mode="WEIGHT_WARM_START_FRESH_OPTIMIZER", parent_path=parent["parent"],
                    parent_files=parent["parent_files"], parent_files_after=parent["parent_files"],
                    parent_unchanged=True, base_frozen=True, initialized_loaded_state_check=True,
                    adapter_count=1, phase_seed=0, optimizer_initial_state_entries=1,
                    optimizer_state_restored=False, optimizer_state_saved=False,
                    optimizer_initialization="fresh_per_write", phase_steps=16)
        manifest = dict(config=plan["rates"]["0"], steps=16, micro_batches=16, epochs_run=4,
                        nonfinite_batches=0, final_loss=0.1, warm_start=warm,
                        corpus=dict(sha256=plan["material_files"][rep.PHASE + ".json"], n_items=16, n_encoded=16, n_skipped_no_target=0),
                        truncation=dict(items_truncated=0, context_tokens_dropped=0, target_tokens_dropped=0, items_split=0),
                        tokens=dict(total=100, target=20), train_tokens_seen=400)
        rep.old.write(adapter / "train_manifest.json", manifest)
        with self.assertRaisesRegex(ValueError, "optimizer"):
            rep.old.verify_fit(plan, "0", dict(adapter=str(adapter), parent=parent["parent"], phase=rep.PHASE), parent["parent_files"], {})


if __name__ == "__main__":
    unittest.main()
