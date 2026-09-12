"""CPU fixtures only; no files written, model loading, subprocesses or GPU probes."""
import copy
import importlib.util
import os
from pathlib import Path
import time
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("memory_only", "/tmp/astra_memory_only_20260912.py")
side = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(side)
side.bind(Path.cwd(), "/tmp/astra_fading_sentinel_20260912.py")


class Tokenizer:
    eos_token_id = 99

    def encode(self, text, **kwargs):
        return [{"red": 1, "blue": 2, "green": 3, "yellow": 4}[text]] if text in (
            "red", "blue", "green", "yellow") else [7] * 42


class MemoryOnlyTests(unittest.TestCase):
    def setUp(self):
        self.plan = dict(model="/fixture/model", configs={str(seed): side.config("/fixture/model", seed) for seed in range(3)},
            parents={str(seed): dict(parent=f"/fixture/original/seed{seed}/adapter", parent_files={"weight": str(seed)},
                                    baseline_counts={"total": 48}) for seed in range(3)},
            branches=side.branches(["3", "4", "5"]), subset_sha256="subset", templates={"dev": {}, "exact": {}},
            deadline=time.time() + 3600, real_lease_end=time.time() + 7200)
        self.state = {"lora": dict(shape=[2, 2], dtype="torch.float32", sha256="before")}
        self.saved = {"lora": dict(shape=[2, 2], dtype="torch.float32", sha256="after")}

    def receipt(self):
        return dict(ok=True, reservation_release_verified=True, owned_group_empty=True, gpu_processes_absent=True,
                    returncode=0, error=None, reserved_seconds=1.0)

    def manifest(self, seed="0"):
        parent = self.plan["parents"][seed]
        warm = dict(mode="WEIGHT_WARM_START_FRESH_OPTIMIZER", parent_path=parent["parent"],
            parent_files=parent["parent_files"], parent_files_after=parent["parent_files"], parent_unchanged=True,
            base_frozen=True, initialized_loaded_state_check=True, adapter_count=1, phase_seed=int(seed),
            optimizer_initial_state_entries=0, optimizer_state_restored=False, optimizer_state_saved=False,
            optimizer_initialization="fresh_per_write", phase_steps=80, parent_cumulative_steps=80,
            cumulative_steps=160, source_state=self.state, initialized_state=self.state,
            final_state=self.saved, dtype_conversions={})
        return dict(config=self.plan["configs"][seed], base_model=self.plan["model"], steps=80, micro_batches=80,
            epochs_run=20, nonfinite_batches=0, empty=False, final_loss=1.0, warm_start=warm,
            corpus=dict(sha256="subset", n_items=16, n_encoded=16, n_skipped_no_target=0),
            truncation=dict(items_truncated=0, context_tokens_dropped=0, target_tokens_dropped=0, items_split=0),
            tokens=dict(total=704, target=32), train_tokens_seen=14080)

    def material(self):
        cases = side.exact.selected_cases()
        rows = [dict(view="memory", group=case["id"], order=0, meta=dict(source_event_ids=case["source_event_ids"]),
            spans=[["fixture:" + case["id"], False, "context"], [case["expected"], True, "authored_birth_target"]]) for case in cases]
        rows.reverse()
        native = [dict(rendered_prompt="fixture:" + case["id"], prompt_token_ids=[7] * 42) for case in cases]
        return dict(corpus=rows + [dict(view="addition")]), native

    def test_exact_subset_order_metadata_tokens_and_no_mutation(self):
        original, native = self.material()
        preserved = copy.deepcopy(original)
        with patch.object(side.exact, "native_inputs", return_value=native):
            subset, audit = side.subset(original, Tokenizer())
        self.assertEqual(original, preserved)
        self.assertEqual(subset["corpus"], original["corpus"][:-1])
        self.assertEqual(sum(len(row["input_ids"]) for row in audit) * 20, 14080)
        self.assertEqual(sum(sum(label != -100 for label in row["labels"]) for row in audit) * 20, 640)
        self.assertTrue(all(row["predictor_indices"] == [41, 42] for row in audit))

    def test_reject_duplicate_missing_and_changed_memory(self):
        for mutation in ("duplicate", "missing", "target", "context", "source"):
            with self.subTest(mutation=mutation):
                material, native = self.material()
                if mutation == "duplicate":
                    material["corpus"][1] = copy.deepcopy(material["corpus"][0])
                elif mutation == "missing":
                    material["corpus"].pop(0)
                elif mutation == "target":
                    material["corpus"][0]["spans"][1][0] = "unknown"
                elif mutation == "context":
                    material["corpus"][0]["spans"][0][0] += " changed"
                else:
                    material["corpus"][0]["meta"]["source_event_ids"] = ["wrong"]
                with patch.object(side.exact, "native_inputs", return_value=native), self.assertRaises(ValueError):
                    side.subset(material, Tokenizer())

    def test_native_label_mismatch_rejected(self):
        material, native = self.material()
        native[0]["prompt_token_ids"][0] = 8
        with patch.object(side.exact, "native_inputs", return_value=native), self.assertRaisesRegex(ValueError, "labels"):
            side.subset(material, Tokenizer())

    def test_cli_effective_config_each_seed(self):
        for seed in ("0", "1", "2"):
            command = side.fit_command(Path("/fixture/root"), self.plan, seed, Path("/fixture/child"))
            self.assertEqual(command[command.index("--seed") + 1], seed)
            self.assertEqual(command[command.index("--init-adapter") + 1], self.plan["parents"][seed]["parent"])
            self.assertIn("--no-pack", command)
            self.assertNotIn("--chat-template", command)

    def test_cli_recipe_mismatch_rejected(self):
        self.plan["configs"]["1"]["epochs"] = 4
        with self.assertRaisesRegex(ValueError, "CLI"):
            side.fit_command(Path("/fixture/root"), self.plan, "1", Path("/fixture/child"))

    def test_manifest_all_seeds(self):
        for seed in ("0", "1", "2"):
            side.validate_manifest(self.plan, seed, self.manifest(seed), self.state, self.saved)

    def test_fit_accounting_failures(self):
        for key, value in (("steps", 79), ("micro_batches", 81), ("epochs_run", 19), ("nonfinite_batches", 1),
                           ("empty", True), ("final_loss", float("nan")), ("train_tokens_seen", 14079)):
            with self.subTest(key=key):
                manifest = self.manifest()
                manifest[key] = value
                with self.assertRaises(ValueError):
                    side.validate_manifest(self.plan, "0", manifest, self.state, self.saved)

    def test_targets_corpus_and_truncation_failures(self):
        for section, key, value in (("tokens", "target", 31), ("tokens", "total", 705),
                ("corpus", "n_items", 80), ("corpus", "sha256", "wrong"), ("corpus", "n_skipped_no_target", 1),
                ("truncation", "items_split", 1), ("truncation", "target_tokens_dropped", 1)):
            with self.subTest(key=key):
                manifest = self.manifest()
                manifest[section][key] = value
                with self.assertRaises(ValueError):
                    side.validate_manifest(self.plan, "0", manifest, self.state, self.saved)

    def test_warm_ownership_optimizer_seed_and_history_failures(self):
        for key, value in (("phase_seed", 1), ("optimizer_initial_state_entries", 1), ("adapter_count", 2),
                ("optimizer_state_restored", True), ("base_frozen", False), ("phase_steps", 79),
                ("parent_cumulative_steps", 96), ("cumulative_steps", 176), ("parent_path", "/wrong"),
                ("parent_unchanged", False), ("initialized_loaded_state_check", False)):
            with self.subTest(key=key):
                manifest = self.manifest()
                manifest["warm_start"][key] = value
                with self.assertRaises(ValueError):
                    side.validate_manifest(self.plan, "0", manifest, self.state, self.saved)

    def test_loaded_state_must_equal_parent(self):
        manifest = self.manifest()
        manifest["warm_start"]["initialized_state"] = self.saved
        with self.assertRaisesRegex(ValueError, "loaded state"):
            side.validate_manifest(self.plan, "0", manifest, self.state, self.saved)

    def test_devices_explicit_complete_and_schedulable(self):
        self.assertEqual(set(side.branches(["0", "0", "1"])), {"0", "1", "2"})
        for devices in (["0", "1"], ["0", "1", "0,1"], ["0", "1", "01"]):
            with self.assertRaises(ValueError):
                side.branches(devices)

    def test_bounds_full900_and_startup_charged(self):
        now = time.time()
        self.assertEqual(side.bounds(now-30, now+3600, now+7200), now+870)
        for deadline, lease in ((now+899, now+7200), (now+3600, now+909), (float("nan"), now+7200)):
            with self.assertRaises(ValueError):
                side.bounds(now, deadline, lease)
        with self.assertRaisesRegex(ValueError, "startup"):
            side.bounds(now-751, now+3600, now+7200)

    def test_permission_and_device_fail_before_actions(self):
        with self.assertRaises(ValueError):
            side.run("/fixture", "0")
        with patch.object(Path, "resolve", lambda path, **kwargs: path), \
                patch.object(side.old, "read_plan", return_value=self.plan), patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "9"}), \
                patch.object(Path, "mkdir") as mkdir, self.assertRaisesRegex(ValueError, "device"):
            side.run("/fixture", "0", True)
        mkdir.assert_not_called()

    def test_existing_output_rejected(self):
        with patch.object(Path, "exists", return_value=True), self.assertRaisesRegex(ValueError, "fresh"):
            side.fresh("/fixture")

    def test_bad_helper_hash_rejected_before_import(self):
        with patch.object(Path, "resolve", lambda path, **kwargs: path), patch.object(Path, "read_bytes", return_value=b"changed"), \
                self.assertRaisesRegex(ValueError, "helper"):
            side.bind("/fixture", "/fixture/helper")

    def test_supervisor_failures_rejected(self):
        for key, value in (("ok", False), ("returncode", 1), ("owned_group_empty", False), ("error", {}),
                           ("reserved_seconds", float("nan"))):
            receipt = self.receipt()
            receipt[key] = value
            with self.assertRaises(ValueError):
                side.successful(receipt)

    def test_execute_always_both_readouts_even_zero_scores(self):
        calls = []
        def supervise(root, plan, path, command, call_path=None):
            calls.append((plan, path, command, call_path))
            return self.receipt()
        with patch.object(Path, "mkdir"), patch.object(Path, "is_file", return_value=True), \
                patch.object(side.old, "write"), patch.object(side.old, "seal"), \
                patch.object(side.old, "state_inventory", side_effect=[self.state, self.saved]), \
                patch.object(side.base, "read", return_value=self.manifest()), patch.object(side.base, "digest", return_value="hash"), \
                patch.object(side.base, "expected_identity", return_value={}), patch.object(side.base, "supervise", side_effect=supervise), \
                patch.object(side.trainer, "_warm_inventory", return_value={"child": "hash"}), patch.object(side, "verify"), \
                patch.object(side.dev, "verify"), patch.object(side.exact, "verify"), \
                patch.object(side.dev, "reduce", return_value=dict(complete=True, counts=dict(total=48, correct=0), rows=["dev-raw"])), \
                patch.object(side.exact, "reduce", return_value=dict(complete=True, counts=dict(total=16, correct=0), rows=["exact-raw"])):
            result = side.execute(Path("/fixture"), Path("/fixture/seed0"), self.plan, "0", time.time()+900)
        self.assertEqual(len(calls), 3)
        self.assertTrue(all(call[0]["device"] == "3" for call in calls))
        self.assertEqual(len({call[0]["lease_end"] for call in calls}), 1)
        self.assertEqual(calls[1][3], Path("/fixture/seed0/dev/run/data/calls"))
        self.assertEqual(calls[2][3], Path("/fixture/seed0/exact/run/data/calls"))
        self.assertEqual(result["readouts"]["exact"]["reduction"]["rows"], ["exact-raw"])

    def test_partial_controller_preserves_receipt_no_success(self):
        writes = {}
        def write(path, value):
            writes[str(path)] = value
        with patch.object(Path, "resolve", lambda path, **kwargs: path), patch.object(Path, "mkdir"), \
                patch.object(Path, "glob", return_value=[]), patch.object(side, "fresh", side_effect=lambda path: path), \
                patch.object(side.old, "read_plan", return_value=self.plan), patch.object(side.old, "write", side_effect=write), \
                patch.object(side.base, "digest", return_value="seal"), patch.object(side, "verify"), \
                patch.object(side, "execute", side_effect=ValueError("fixture failure")), \
                patch.object(side.base.supervisor, "gpu_processes_absent", return_value=True), \
                patch.object(side.signal, "signal", return_value=None), patch.object(side.signal, "setitimer") as timer, \
                patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "3"}), self.assertRaisesRegex(ValueError, "partial seed"):
            side.run("/fixture", "0", True, clock=(time.time()-30, time.monotonic()-30))
        terminal = writes["/fixture/seed0/terminal.json"]
        self.assertEqual(terminal["status"], "FAILED_PARTIAL_NO_RETRY")
        self.assertGreaterEqual(terminal["reserved_seconds"], 30)
        self.assertFalse(terminal["counts_used_for_selection"])
        self.assertLessEqual(timer.call_args_list[0].args[1], 730)

    def test_controller_requires_three_receipts_and_release(self):
        for receipt_count, released, expected in ((3, True, "COMPLETE"), (2, True, "FAILED_PARTIAL_NO_RETRY"),
                                                   (3, False, "FAILED_PARTIAL_NO_RETRY")):
            with self.subTest(receipt_count=receipt_count, released=released):
                writes = {}
                paths = [Path(f"/fixture/worker{index}/supervision.json") for index in range(receipt_count)]
                with patch.object(Path, "resolve", lambda path, **kwargs: path), patch.object(Path, "mkdir"), \
                        patch.object(Path, "glob", side_effect=[paths, []]), patch.object(side, "fresh", side_effect=lambda path: path), \
                        patch.object(side.old, "read_plan", return_value=self.plan), \
                        patch.object(side.old, "write", side_effect=lambda path, value: writes.update({str(path): value})), \
                        patch.object(side.base, "read", return_value=self.receipt()), patch.object(side.base, "digest", return_value="seal"), \
                        patch.object(side, "verify"), patch.object(side, "execute", return_value={"all_scores": 0}), \
                        patch.object(side.base.supervisor, "gpu_processes_absent", return_value=released), \
                        patch.object(side.signal, "signal", return_value=None), patch.object(side.signal, "setitimer"), \
                        patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "3"}):
                    if expected == "COMPLETE":
                        side.run("/fixture", "0", True)
                    else:
                        with self.assertRaises(ValueError):
                            side.run("/fixture", "0", True)
                self.assertEqual(writes["/fixture/seed0/terminal.json"]["status"], expected)


if __name__ == "__main__":
    unittest.main()
