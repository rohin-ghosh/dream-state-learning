"""CPU orchestration fixtures; no native model, tokenizer, subprocess, or GPU."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location("sentinel", "/tmp/astra_fading_sentinel_20260912.py")
sentinel = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sentinel)
sentinel.bind(Path.cwd())


class SentinelTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="fading-sentinel-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.model = self.root / "fixture-model"
        self.model.mkdir()
        self.seedroot = self.root / "astra_fundamental_teaching_20260912_attempt1"
        self.parent = self.seedroot / "fit_teach" / "adapter"
        self.parent.mkdir(parents=True)
        self.seedconfig = sentinel.config(str(self.model), "0")
        self.seedconfig["lr"] = 3e-4
        self.seed = dict(model=str(self.model), model_files={"fixture": "hash"}, config=self.seedconfig,
            eval_dev_ids=list(sentinel.readout.CASE_IDS))
        self.manifest = dict(recipe=sentinel.trainer.RECIPE, config=self.seedconfig, empty=False, steps=80,
            nonfinite_batches=0, final_loss=1.0, base_model=str(self.model))
        sentinel.write(self.parent / "train_manifest.json", self.manifest)
        sentinel.write(self.parent / "adapter_config.json", {"base_model_name_or_path": str(self.model)})
        (self.parent / "DONE").write_text("ok\n")
        (self.parent / "adapter_model.safetensors").write_bytes(b"not-native-weights-fixture-only")
        self.parent_files = sentinel.trainer._warm_inventory(self.parent)
        sentinel.write(self.parent.parent / "result.json", dict(arm="teach", adapter=str(self.parent),
            adapter_files=self.parent_files, manifest=self.manifest,
            supervised=dict(ok=True, reservation_release_verified=True)))
        sentinel.seal(self.seedroot, self.seed)
        self.matroot = self.root / "material"
        self.matroot.mkdir()
        sentinel.write(self.matroot / "manifest.json", dict(status="NATIVE_V3_TOKEN_AUDIT_COMPLETE",
            native_token_audit=True, tokenizer_injected=False, model=str(self.model), model_files=self.seed["model_files"],
            phase_corpora={phase: phase + ".json" for phase in sentinel.PHASES}))
        for phase in sentinel.PHASES:
            sentinel.write(self.matroot / (phase + ".json"), {"corpus": [dict(fixture=index) for index in range(16)]})
        sentinel.write(self.matroot / "token_audit.json", {"phases": {phase: {"per_epoch":
            {"input_tokens": 640, "target_tokens": 80}} for phase in sentinel.PHASES}})
        self.runroot = self.root / "run"
        self.deadline = time.time() + 7200
        self.lease_end = self.deadline + 3600
        self.addCleanup(patch.stopall)
        patch.object(sentinel, "SEED0_SHA", sentinel.base.digest(self.seedroot / "plan.json")).start()
        patch.object(sentinel.base, "model_hashes", return_value=self.seed["model_files"]).start()
        patch.object(sentinel.material, "verify", return_value={"fixture": True}).start()
        patch.object(sentinel.readout, "prepare", side_effect=self.fake_readout_prepare).start()
        patch.object(sentinel.base.supervisor, "gpu_processes_absent", return_value=True).start()

    def fake_readout_prepare(self, out, model, adapter, device, end):
        Path(out).mkdir()
        sentinel.seal(Path(out), dict(adapter=adapter, device=device, lease_end=end, model=model,
            cases=sentinel.readout.selected_cases(), requests=sentinel.readout.requests(sentinel.readout.selected_cases())))

    def prepare(self):
        sentinel.prepare(self.matroot, self.parent, self.seedroot / "plan.json", sentinel.base.REPO,
            self.deadline, self.lease_end, self.runroot)
        return sentinel.read_plan(self.runroot)

    def replace_json(self, path, value):
        path.write_text(json.dumps(value))

    def test_prepare_binds_actual_model_source_material_and_parent(self):
        plan = self.prepare()
        self.assertEqual(plan["model"], self.seed["model"])
        self.assertEqual(plan["parent_files"], self.parent_files)
        self.assertEqual(plan["material_files"], sentinel.base.tree_hashes(self.matroot))
        self.assertEqual(plan["source_hashes"], sentinel.sources())
        self.assertEqual(plan["real_lease_end"], self.lease_end)
        self.assertEqual(plan["cases"], sentinel.readout.selected_cases())
        self.assertEqual(len(plan["cases"]), 48)

    def test_all_commands_parse_to_exact_native_config(self):
        plan = self.prepare()
        for rate in sentinel.RATES:
            row = sentinel.phase_paths(self.runroot / ("rate-" + rate), str(self.parent))[0]
            command = sentinel.fit_command(plan, rate, row)
            args = sentinel.trainer.build_parser().parse_args(command[4:])
            self.assertEqual(sentinel.asdict(sentinel.trainer.config_from_args(args)), plan["rates"][rate])
            self.assertEqual(args.init_adapter, str(self.parent))
            self.assertEqual(args.corpus, str(self.matroot / (row["phase"] + ".json")))

    def test_only_lr_changes_across_rates_and_seed_always_zero(self):
        plan = self.prepare()
        for config in plan["rates"].values():
            self.assertEqual(dict(config, lr=3e-4), self.seedconfig)
            self.assertEqual(config["seed"], 0)
        with self.assertRaises(ValueError):
            sentinel.config(str(self.model), "3e-4")

    def test_parent_chain_and_separate_lineages(self):
        adapters = set()
        for rate in sentinel.RATES:
            rows = sentinel.phase_paths(self.runroot / ("rate-" + rate), str(self.parent))
            self.assertEqual([row["phase"] for row in rows], list(sentinel.PHASES))
            self.assertEqual(rows[0]["parent"], str(self.parent))
            self.assertEqual([row["parent"] for row in rows[1:]], [row["adapter"] for row in rows[:-1]])
            adapters.update(row["adapter"] for row in rows)
        self.assertEqual(len(adapters), 12)

    def test_stale_prepare_preserves_old_bytes(self):
        self.prepare()
        before = sentinel.base.tree_hashes(self.runroot)
        with self.assertRaises(ValueError):
            self.prepare()
        self.assertEqual(before, sentinel.base.tree_hashes(self.runroot))

    def test_exclusive_write_and_plan_tampering(self):
        self.prepare()
        with self.assertRaises(FileExistsError):
            sentinel.write(self.runroot / "plan.json", {})
        (self.runroot / "plan.json").write_text("{}")
        with self.assertRaisesRegex(ValueError, "plan changed"):
            sentinel.verify(self.runroot)

    def test_native_material_required_and_no_injected_evidence(self):
        path = self.matroot / "manifest.json"
        value = sentinel.base.read(path)
        value["tokenizer_injected"] = True
        self.replace_json(path, value)
        with self.assertRaisesRegex(ValueError, "actual native"):
            self.prepare()
        self.assertFalse(self.runroot.exists())

    def test_mismatched_prepared_base_rejected(self):
        path = self.matroot / "manifest.json"
        value = sentinel.base.read(path)
        value["model"] = "guessed-base"
        self.replace_json(path, value)
        with self.assertRaisesRegex(ValueError, "base bytes"):
            self.prepare()

    def test_wrong_starting_arm_or_seed0_bytes_rejected(self):
        other = self.seedroot / "fit_control" / "adapter"
        other.mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, "actual seed0 teach"):
            sentinel.prepare(self.matroot, other, self.seedroot / "plan.json", sentinel.base.REPO,
                self.deadline, self.lease_end, self.runroot)
        with patch.object(sentinel, "SEED0_SHA", "not-the-pin"):
            with self.assertRaisesRegex(ValueError, "pinned actual"):
                self.prepare()

    def test_partial_or_changed_seed0_adapter_rejected(self):
        (self.parent / "DONE").unlink()
        with self.assertRaisesRegex(ValueError, "inventory differs"):
            self.prepare()

    def test_material_or_parent_changes_after_prepare_fail(self):
        self.prepare()
        (self.matroot / (sentinel.PHASES[0] + ".json")).write_text("tampered")
        with self.assertRaisesRegex(ValueError, "material/template"):
            sentinel.verify(self.runroot)
        (self.parent / "DONE").write_text("changed")
        with self.assertRaisesRegex(ValueError, "initial parent"):
            sentinel.verify(self.runroot)

    def test_bounds_cap_1800_and_preserve_real_lease(self):
        self.assertEqual(sentinel.bounds(1000., 9000., 10000.), 2800.)
        self.assertEqual(sentinel.bounds(1000., 2000., 10000.), 2000.)
        self.assertEqual(sentinel.bounds(1000., 9000., 2200.), 2190.)
        for deadline in (1050., float("inf"), float("nan")):
            with self.assertRaises(ValueError):
                sentinel.bounds(1000., deadline, 10000.)

    def test_no_launch_authority_or_wrong_initial_device_rejected(self):
        self.prepare()
        with self.assertRaises(ValueError):
            sentinel.run_one_rate(self.runroot, "0")
        with patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "5"}):
            with self.assertRaisesRegex(ValueError, "inherit exact"):
                sentinel.run_one_rate(self.runroot, "0", True)
        self.assertFalse((self.runroot / "rate-0").exists())

    def test_four_phases_do_not_depend_on_probe_outcomes(self):
        self.prepare()
        observed = []
        def execute(root, lineage, plan, rate, row, effective):
            observed.append(row)
            for name in ("fit-worker", "readout-worker"):
                worker = Path(row["stage"]) / name
                worker.mkdir(parents=True)
                sentinel.write(worker / "supervision.json", dict(ok=True, reservation_release_verified=True,
                    owned_group_empty=True, gpu_processes_absent=True, reserved_seconds=1.))
            return dict(phase=row["phase"], arbitrary_probe_counts=[0, 48, -1, None][len(observed)-1])
        with patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "4"}), \
            patch.object(sentinel, "execute_phase", side_effect=execute), \
            patch.object(sentinel.signal, "setitimer") as timer:
            result = sentinel.run_one_rate(self.runroot, "0", True)
        self.assertGreater(timer.call_args_list[0].args[1], 1659)
        self.assertLessEqual(timer.call_args_list[0].args[1], 1660)
        self.assertEqual(timer.call_args_list[-1].args[1], 0)
        self.assertEqual(len(observed), 4)
        self.assertFalse(result["counts_used_for_selection"])
        self.assertEqual(result["status"], "COMPLETE")
        self.assertFalse(result["release_between_workers"])
        self.assertLessEqual(result["effective_deadline"] - result["started"], 1800)
        self.assertEqual(result["real_lease_end"], self.lease_end)

    def test_failed_phase_stops_honestly_and_cannot_replay(self):
        self.prepare()
        with patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "4"}), patch.object(sentinel, "execute_phase", side_effect=ValueError("partial")) as step:
            with self.assertRaisesRegex(ValueError, "partial lineage"):
                sentinel.run_one_rate(self.runroot, "0", True)
            self.assertEqual(step.call_count, 1)
            with self.assertRaises(FileExistsError):
                sentinel.run_one_rate(self.runroot, "0", True)
            self.assertEqual(step.call_count, 1)
        terminal = sentinel.base.read(self.runroot / "rate-0" / "terminal.json")
        self.assertEqual(terminal["status"], "FAILED_PARTIAL_NO_RETRY")
        self.assertEqual(terminal["phases"], [])
        self.assertEqual(terminal["error"]["message"], "partial")

    def inventories(self):
        before = {"layer.lora_A.weight": dict(shape=[8, 16], dtype="torch.float32", sha256="aaa"),
            "layer.lora_B.weight": dict(shape=[16, 8], dtype="torch.float32", sha256="bbb")}
        warm = dict(source_state=copy.deepcopy(before), initialized_state=copy.deepcopy(before), final_state=copy.deepcopy(before))
        return before, warm, copy.deepcopy(before)

    def test_zero_lr_parameter_equality_not_artifact_tree_equality(self):
        before, warm, saved = self.inventories()
        warm["legitimate_new_manifest"] = {"steps": 16, "parent": "prior-phase"}
        self.assertTrue(sentinel.check_states("0", before, warm, saved))

    def test_zero_lr_changed_tensor_or_dtype_rejected(self):
        for key, value in (("sha256", "changed"), ("dtype", "torch.bfloat16")):
            before, warm, saved = self.inventories()
            saved["layer.lora_B.weight"][key] = value
            warm["final_state"] = copy.deepcopy(saved)
            with self.assertRaisesRegex(ValueError, "LR0"):
                sentinel.check_states("0", before, warm, saved)

    def test_zero_lr_changed_initialization_even_if_saved_restored_rejected(self):
        before, warm, saved = self.inventories()
        warm["initialized_state"]["layer.lora_A.weight"]["sha256"] = "changed"
        with self.assertRaisesRegex(ValueError, "LR0"):
            sentinel.check_states("0", before, warm, saved)

    def test_nonzero_allows_updates_but_not_partial_or_bad_saved_state(self):
        before, warm, saved = self.inventories()
        saved["layer.lora_A.weight"]["sha256"] = "updated"
        warm["final_state"] = copy.deepcopy(saved)
        self.assertFalse(sentinel.check_states("3e-5", before, warm, saved))
        warm["initialized_state"].pop("layer.lora_B.weight")
        with self.assertRaisesRegex(ValueError, "partial"):
            sentinel.check_states("3e-5", before, warm, saved)
        warm["final_state"] = {}
        with self.assertRaisesRegex(ValueError, "serialized"):
            sentinel.check_states("1e-4", before, warm, saved)

    def test_missing_or_ambiguous_weight_files_rejected_without_loader(self):
        empty = self.root / "empty"
        empty.mkdir()
        with self.assertRaisesRegex(ValueError, "missing/ambiguous"):
            sentinel.state_inventory(empty)
        (self.parent / "adapter_model.bin").write_bytes(b"ambiguous")
        with self.assertRaisesRegex(ValueError, "missing/ambiguous"):
            sentinel.state_inventory(self.parent)

    def test_phase_uses_two_native_supervisors_and_same_lineage_budget(self):
        plan = self.prepare()
        lineage = self.runroot / "rate-0"
        lineage.mkdir()
        row = sentinel.phase_paths(lineage, str(self.parent))[0]
        fit = dict(adapter_files={"fixture": "hash"})
        calls = []
        def supervise(root, active, stage, command, call_path=None):
            calls.append((root, active, stage, command, call_path))
            return dict(reserved_seconds=1)
        def reduce(root):
            sentinel.write(root / "reduction.json", {"complete": True, "counts": {"total": 48}})
            return sentinel.base.read(root / "reduction.json")
        with patch.object(sentinel, "state_inventory", return_value={}), \
            patch.object(sentinel, "verify_fit", return_value=fit), \
            patch.object(sentinel, "verify", return_value=plan), \
            patch.object(sentinel.base, "supervise", side_effect=supervise), \
            patch.object(sentinel.base, "expected_identity", return_value={}), \
            patch.object(sentinel.readout, "verify"), patch.object(sentinel.readout, "reduce", side_effect=reduce), \
            patch.object(sentinel.trainer, "_warm_inventory", return_value=fit["adapter_files"]):
            sentinel.execute_phase(self.runroot, lineage, plan, "0", row, self.deadline)
        self.assertEqual(len(calls), 2)
        self.assertTrue(all(call[0] == lineage and call[1]["lease_end"] == self.deadline for call in calls))
        self.assertEqual(calls[1][3][4], "_worker")
        self.assertEqual(calls[1][4], Path(row["stage"]) / "readout" / "run" / "data" / "calls")
        self.assertEqual(sentinel.read_plan(Path(row["stage"]) / "readout")["cases"], plan["cases"])

    def fit_fixture(self):
        plan = self.prepare()
        row = sentinel.phase_paths(self.runroot / "rate-0", str(self.parent))[0]
        adapter = Path(row["adapter"])
        adapter.mkdir(parents=True)
        before, warm, saved = self.inventories()
        warm.update(mode="WEIGHT_WARM_START_FRESH_OPTIMIZER", parent_path=str(self.parent),
            parent_files=self.parent_files, parent_files_after=self.parent_files, parent_unchanged=True,
            base_frozen=True, initialized_loaded_state_check=True, adapter_count=1, phase_seed=0,
            optimizer_initial_state_entries=0, optimizer_state_restored=False, optimizer_state_saved=False,
            optimizer_initialization="fresh_per_write", phase_steps=16, parent_cumulative_steps=80, cumulative_steps=96)
        manifest = dict(config=plan["rates"]["0"], steps=16, micro_batches=16, epochs_run=4, nonfinite_batches=0,
            final_loss=1.0, corpus=dict(sha256=plan["material_files"][row["phase"] + ".json"], n_items=16,
                n_encoded=16, n_skipped_no_target=0), truncation=dict(items_truncated=0, context_tokens_dropped=0,
                target_tokens_dropped=0, items_split=0), tokens=dict(total=640, target=80),
            train_tokens_seen=2560, warm_start=warm)
        sentinel.write(adapter / "train_manifest.json", manifest)
        (adapter / "DONE").write_text("ok")
        return plan, row, before, saved, manifest

    def test_verify_fit_checks_exact_steps_masks_tokens_and_parent(self):
        plan, row, before, saved, manifest = self.fit_fixture()
        with patch.object(sentinel, "state_inventory", return_value=saved):
            result = sentinel.verify_fit(plan, "0", row, self.parent_files, before)
        self.assertEqual(result["steps"], 16)
        self.assertEqual(result["train_tokens_seen"], 2560)
        self.assertTrue(result["parameter_state_unchanged"])
        self.assertEqual(sentinel.trainer._warm_inventory(self.parent), self.parent_files)

    def test_verify_fit_rejects_partial_nonfinite_or_token_mismatch(self):
        plan, row, before, saved, manifest = self.fit_fixture()
        for key, bad in (("steps", 15), ("nonfinite_batches", 1), ("train_tokens_seen", 2559), ("final_loss", float("nan"))):
            invalid = dict(manifest, **{key: bad})
            self.replace_json(Path(row["adapter"]) / "train_manifest.json", invalid)
            with self.assertRaises(ValueError), patch.object(sentinel, "state_inventory", return_value=saved):
                sentinel.verify_fit(plan, "0", row, self.parent_files, before)

    def test_verify_fit_rejects_restored_optimizer_or_wrong_chain(self):
        plan, row, before, saved, manifest = self.fit_fixture()
        for key, bad in (("optimizer_initial_state_entries", 1), ("adapter_count", 2),
            ("base_frozen", False), ("cumulative_steps", 97), ("phase_seed", 1), ("parent_path", "/wrong")):
            invalid = copy.deepcopy(manifest)
            invalid["warm_start"][key] = bad
            self.replace_json(Path(row["adapter"]) / "train_manifest.json", invalid)
            with self.assertRaises(ValueError), patch.object(sentinel, "state_inventory", return_value=saved):
                sentinel.verify_fit(plan, "0", row, self.parent_files, before)

    def test_missing_supervision_is_not_a_success_or_release(self):
        self.prepare()
        def execute(root, lineage, plan, rate, row, effective):
            stage = Path(row["stage"])
            stage.mkdir()
            sentinel.write(stage / "process.json", {"pid": 123})
            raise ValueError("incomplete receipt")
        with patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "4"}), patch.object(sentinel, "execute_phase", side_effect=execute):
            with self.assertRaisesRegex(ValueError, "partial lineage"):
                sentinel.run_one_rate(self.runroot, "0", True)
        result = sentinel.base.read(self.runroot / "rate-0" / "terminal.json")
        self.assertFalse(result["release_verified"])
        self.assertEqual(result["status"], "FAILED_PARTIAL_NO_RETRY")

    def test_cleanup_failure_never_reports_complete(self):
        self.prepare()
        with patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "4"}), \
            patch.object(sentinel, "execute_phase", return_value={}), \
            patch.object(sentinel.base.supervisor, "gpu_processes_absent", return_value=False):
            with self.assertRaisesRegex(ValueError, "partial lineage"):
                sentinel.run_one_rate(self.runroot, "0", True)
        result = sentinel.base.read(self.runroot / "rate-0" / "terminal.json")
        self.assertFalse(result["release_verified"])

    def test_symlink_or_input_nested_output_rejected(self):
        linked = self.root / "linked"
        linked.symlink_to(self.matroot, target_is_directory=True)
        self.runroot = linked / "new-output"
        with self.assertRaisesRegex(ValueError, "symlink output"):
            self.prepare()
        self.runroot = self.matroot / "new-output"
        with self.assertRaisesRegex(ValueError, "output overlaps"):
            self.prepare()
        self.assertFalse(self.runroot.exists())

    def test_source_drift_rejected(self):
        self.prepare()
        with patch.object(sentinel, "sources", return_value={"changed": "hash"}):
            with self.assertRaisesRegex(ValueError, "sources changed"):
                sentinel.verify(self.runroot)


if __name__ == "__main__":
    unittest.main()
