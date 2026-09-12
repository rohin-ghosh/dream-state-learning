"""CPU-only fixtures: no model, subprocess, GPU probe, or fixture-file writes."""
import copy
import importlib.util
import os
from pathlib import Path
import time
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("memory_replay", "/tmp/astra_memory_replay_20260912.py")
side = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(side)
side.bind(Path.cwd(), "/tmp/astra_memory_only_20260912.py", "/tmp/astra_fading_sentinel_20260912.py")


class Tokenizer:
    eos_token_id = 99

    def encode(self, text, **kwargs):
        colors = {"red": 1, "blue": 2, "green": 3, "yellow": 4}
        if text in colors:
            return [colors[text]]
        if text.startswith("tokens:"):
            return [8] * int(text.split(":")[1])
        return [7] * 42


class ReplayTests(unittest.TestCase):
    def setUp(self):
        self.plan = dict(model="/fixture/model", seed=0, device="3", configs=side.configs("/fixture/model", 0),
            parent=dict(parent="/fixture/original/fit_teach/adapter", parent_files={"weight": "parent"}),
            material_files={arm + ".json": arm for arm in side.ARMS}, templates={"dev": {}, "exact": {}},
            deadline=time.time() + 3600, real_lease_end=time.time() + 7200)
        self.state = {"lora": dict(shape=[2, 2], dtype="torch.float32", sha256="before")}
        self.saved = {"lora": dict(shape=[2, 2], dtype="torch.float32", sha256="after")}

    def receipt(self):
        return dict(ok=True, reservation_release_verified=True, owned_group_empty=True, gpu_processes_absent=True,
                    returncode=0, error=None, reserved_seconds=1.0)

    def manifest(self, arm):
        expected, parent = side.COUNTS[arm], self.plan["parent"]
        warm = dict(mode="WEIGHT_WARM_START_FRESH_OPTIMIZER", parent_path=parent["parent"],
            parent_files=parent["parent_files"], parent_files_after=parent["parent_files"], parent_unchanged=True,
            base_frozen=True, initialized_loaded_state_check=True, adapter_count=1, phase_seed=self.plan["seed"],
            optimizer_initial_state_entries=0, optimizer_state_restored=False, optimizer_state_saved=False,
            optimizer_initialization="fresh_per_write", phase_steps=160, parent_cumulative_steps=80,
            cumulative_steps=240, source_state=self.state, initialized_state=self.state,
            final_state=self.saved, dtype_conversions={})
        return dict(config=copy.deepcopy(self.plan["configs"][arm]), base_model=self.plan["model"], steps=160,
            micro_batches=160, epochs_run=expected["epochs"], nonfinite_batches=0, empty=False, final_loss=1.0,
            warm_start=warm, corpus=dict(sha256=arm, n_items=expected["items"], n_encoded=expected["items"], n_skipped_no_target=0),
            truncation=dict(items_truncated=0, context_tokens_dropped=0, target_tokens_dropped=0, items_split=0),
            tokens=dict(total=expected["input_per_epoch"], target=expected["target_per_epoch"]),
            train_tokens_seen=expected["input_presentations"])

    def material(self):
        cases = side.exact.selected_cases()
        additions = list(side.ADDITION_IDS) + [f"train-addition-{index:03d}" for index in range(64)
                                              if f"train-addition-{index:03d}" not in side.ADDITION_IDS]
        rows = []
        for index, group in enumerate(additions):
            rows.append(dict(view="addition", group=group, order=len(rows),
                meta=dict(source_event_ids=[group.replace("train-", "source-")]),
                spans=[["tokens:51" if index in (14, 15) else "tokens:45", False, "context"],
                       ["tokens:10" if index in (14, 15) else "tokens:13", True, "authored_birth_target"]]))
            if index < 16:
                case = cases[index]
                rows.append(dict(view="memory", group=case["id"], order=len(rows),
                    meta=dict(source_event_ids=case["source_event_ids"]),
                    spans=[["fixture:" + case["id"], False, "context"],
                           [case["expected"], True, "authored_birth_target"]]))
        native = [dict(rendered_prompt="fixture:" + case["id"], prompt_token_ids=[7] * 42) for case in cases]
        receipts = []
        for item in rows:
            encoded = side.trainer.encode_item_segments(side.trainer.normalize_items([item])[0], Tokenizer(), 512, False, True)[0]
            receipts.append(dict(case_id=item["group"], input_tokens=len(encoded.ids),
                target_tokens=sum(label != -100 for label in encoded.labels), labels_sha256=side.base.value_hash([encoded.labels])))
        return dict(corpus=rows), native, dict(row_audits=dict(teach=receipts))

    def test_stable_source_filter_preserves_full_records(self):
        original, _, _ = self.material()
        snapshot = copy.deepcopy(original)
        selected = side.select_material(original)
        self.assertEqual(original, snapshot)
        self.assertEqual(selected["mixed"]["corpus"], original["corpus"][:32])
        self.assertEqual(len(selected["all_memory"]["corpus"]), 16)
        self.assertIs(selected["mixed"]["corpus"][0], original["corpus"][0])
        self.assertEqual([row["order"] for row in selected["all_memory"]["corpus"]], list(range(1, 32, 2)))

    def test_wrong_source_order_missing_duplicate_rejected(self):
        for mutation in ("order", "missing", "duplicate", "view"):
            original, _, _ = self.material()
            if mutation == "order":
                original["corpus"][0], original["corpus"][2] = original["corpus"][2], original["corpus"][0]
            elif mutation == "missing":
                original["corpus"].pop()
            elif mutation == "duplicate":
                original["corpus"][-1] = original["corpus"][0]
            else:
                original["corpus"][0]["view"] = "new-fact"
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                side.select_material(original)

    def test_native_masks_counts_and_eos(self):
        original, native, prior = self.material()
        with patch.object(side.exact, "native_inputs", return_value=native):
            _, audit = side.audit_material(original, prior, Tokenizer())
        for arm in side.ARMS:
            expected = side.COUNTS[arm]
            self.assertEqual(sum(row["input_tokens"] for row in audit[arm]) * expected["epochs"], expected["input_presentations"])
            self.assertEqual(sum(row["target_tokens"] for row in audit[arm]) * expected["epochs"], expected["target_presentations"])
        self.assertTrue(all(row["labels"] == [-100] * 42 + row["input_ids"][-2:] for row in audit["all_memory"]))
        self.assertTrue(all(row["labels"][-1] == 99 for row in audit["all_memory"]))

    def test_native_receipt_mismatch_rejected(self):
        for field, value in (("labels_sha256", "flat-or-wrong-hash"), ("input_tokens", 999), ("target_tokens", 0)):
            original, native, prior = self.material()
            prior["row_audits"]["teach"][0][field] = value
            with patch.object(side.exact, "native_inputs", return_value=native), self.assertRaisesRegex(ValueError, "receipt"):
                side.audit_material(original, prior, Tokenizer())

    def test_no_new_memory_label_or_context(self):
        for part in (0, 1):
            original, native, prior = self.material()
            original["corpus"][1]["spans"][part][0] += " changed"
            with patch.object(side.exact, "native_inputs", return_value=native), self.assertRaises(ValueError):
                side.audit_material(original, prior, Tokenizer())

    def test_recipes_cli_both_arms_all_seeds(self):
        for seed in range(3):
            self.plan.update(seed=seed, configs=side.configs(self.plan["model"], seed))
            for arm in side.ARMS:
                command = side.fit_command(Path("/fixture"), self.plan, arm, "/fixture/child")
                self.assertEqual(command[command.index("--epochs") + 1], str(side.COUNTS[arm]["epochs"]))
                self.assertEqual(command[command.index("--seed") + 1], str(seed))
                self.assertEqual(command[command.index("--init-adapter") + 1], self.plan["parent"]["parent"])
                self.assertIn("--no-pack", command)
                self.assertNotIn("--chat-template", command)
                side.validate_manifest(self.plan, arm, self.manifest(arm), self.state, self.saved)

    def test_cli_mismatch_rejected(self):
        self.plan["configs"]["all_memory"]["epochs"] = 20
        with self.assertRaisesRegex(ValueError, "CLI"):
            side.fit_command(Path("/fixture"), self.plan, "all_memory", "/fixture/child")

    def test_separate_original_parent_forks(self):
        paths = side.paths(Path("/fixture/run"), self.plan["parent"]["parent"])
        self.assertEqual({row["parent"] for row in paths.values()}, {self.plan["parent"]["parent"]})
        self.assertEqual(len({row["adapter"] for row in paths.values()}), 2)
        self.assertNotEqual(paths["all_memory"]["parent"], paths["mixed"]["adapter"])

    def test_fit_step_epoch_finite_token_failures(self):
        for arm in side.ARMS:
            for key, value in (("steps", 80), ("micro_batches", 159), ("epochs_run", 19), ("nonfinite_batches", 1),
                               ("empty", True), ("final_loss", float("nan")), ("train_tokens_seen", 14080)):
                manifest = self.manifest(arm)
                manifest[key] = value
                with self.subTest(arm=arm, key=key), self.assertRaises(ValueError):
                    side.validate_manifest(self.plan, arm, manifest, self.state, self.saved)

    def test_corpus_masks_and_truncation_failures(self):
        for section, key, value in (("tokens", "target", 32), ("tokens", "total", 704), ("corpus", "n_items", 16),
                ("corpus", "sha256", "changed"), ("corpus", "n_skipped_no_target", 1),
                ("truncation", "items_split", 1), ("truncation", "target_tokens_dropped", 1)):
            manifest = self.manifest("mixed")
            manifest[section][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                side.validate_manifest(self.plan, "mixed", manifest, self.state, self.saved)

    def test_warm_state_seed_optimizer_history_failures(self):
        for key, value in (("parent_path", "/fixture/run/mixed/adapter"), ("parent_unchanged", False),
                ("phase_seed", 1), ("adapter_count", 2), ("optimizer_initial_state_entries", 1),
                ("optimizer_state_restored", True), ("optimizer_state_saved", True), ("phase_steps", 80),
                ("parent_cumulative_steps", 160), ("cumulative_steps", 320), ("base_frozen", False),
                ("initialized_loaded_state_check", False), ("dtype_conversions", {"lora": "changed"})):
            manifest = self.manifest("mixed")
            manifest["warm_start"][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                side.validate_manifest(self.plan, "mixed", manifest, self.state, self.saved)

    def test_loaded_and_saved_state_mismatch_rejected(self):
        for key in ("source_state", "initialized_state", "final_state"):
            manifest = self.manifest("mixed")
            manifest["warm_start"][key] = {"wrong": {}}
            with self.subTest(key=key), self.assertRaises(ValueError):
                side.validate_manifest(self.plan, "mixed", manifest, self.state, self.saved)

    def test_full1200_bound_includes_startup_and_cleanup(self):
        now = time.time()
        self.assertEqual(side.bounds(now - 30, now + 3600, now + 7200), now + 1170)
        for started, deadline, lease in ((now, now + 1199, now + 7200), (now, now + 3600, now + 1209),
                (now - 1051, now + 3600, now + 7200), (now, float("nan"), now + 7200)):
            with self.assertRaises(ValueError):
                side.bounds(started, deadline, lease)

    def test_gpu_permission_and_device_before_writes(self):
        with self.assertRaises(ValueError):
            side.run("/fixture")
        with patch.object(Path, "resolve", lambda path, **kwargs: path), \
                patch.object(side.old, "read_plan", return_value=self.plan), patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "9"}), \
                patch.object(Path, "mkdir") as mkdir, self.assertRaisesRegex(ValueError, "device"):
            side.run("/fixture", True)
        mkdir.assert_not_called()

    def test_existing_output_rejected(self):
        with patch.object(Path, "exists", return_value=True), self.assertRaisesRegex(ValueError, "fresh"):
            side.memory.fresh("/fixture")

    def test_helper_pin_rejected_before_import(self):
        with patch.object(Path, "resolve", lambda path, **kwargs: path), patch.object(Path, "read_bytes", return_value=b"changed"), \
                self.assertRaisesRegex(ValueError, "helper"):
            side.bind("/fixture", "/fixture/helper", "/fixture/fading")

    def test_both_panels_each_arm_even_zero_scores(self):
        calls = []
        for arm in side.ARMS:
            with patch.object(Path, "mkdir"), patch.object(Path, "is_file", return_value=True), \
                    patch.object(side.old, "write"), patch.object(side.old, "seal"), \
                    patch.object(side.old, "state_inventory", side_effect=[self.state, self.saved]), \
                    patch.object(side.base, "read", return_value=self.manifest(arm)), patch.object(side.base, "digest", return_value="hash"), \
                    patch.object(side.base, "expected_identity", return_value={}), \
                    patch.object(side.base, "supervise", side_effect=lambda *args: calls.append(args) or self.receipt()), \
                    patch.object(side.trainer, "_warm_inventory", return_value={"child": "hash"}), patch.object(side, "verify"), \
                    patch.object(side.dev, "verify"), patch.object(side.exact, "verify"), \
                    patch.object(side.dev, "reduce", return_value=dict(complete=True, counts=dict(total=48, correct=0), rows=["dev-raw"])), \
                    patch.object(side.exact, "reduce", return_value=dict(complete=True, counts=dict(total=16, correct=0), rows=["exact-raw"])):
                result = side.execute_arm(Path("/fixture"), Path("/fixture/run"), self.plan, arm, 9999999999)
            self.assertEqual(result["readouts"]["exact"]["reduction"]["rows"], ["exact-raw"])
        self.assertEqual(len(calls), 6)
        self.assertTrue(all(call[1]["device"] == "3" and call[1]["lease_end"] == 9999999999 for call in calls))
        self.assertEqual([str(calls[index][4]) for index in (1, 2, 4, 5)],
            [f"/fixture/run/{arm}/{panel}/run/data/calls" for arm in side.ARMS for panel in ("dev", "exact")])

    def controller(self, receipt_count=6, released=True, failure=False):
        writes, order = {}, []
        def execute(*args):
            order.append(args[3])
            if failure and args[3] == "all_memory":
                raise ValueError("technical failure")
            return {"all_scores": 0}
        paths = [Path(f"/fixture/run/worker{index}/supervision.json") for index in range(receipt_count)]
        with patch.object(Path, "resolve", lambda path, **kwargs: path), patch.object(Path, "mkdir"), \
                patch.object(Path, "glob", side_effect=[paths, []]), patch.object(side.memory, "fresh", side_effect=lambda path: path), \
                patch.object(side.old, "read_plan", return_value=self.plan), \
                patch.object(side.old, "write", side_effect=lambda path, value: writes.update({str(path): value})), \
                patch.object(side.base, "read", return_value=self.receipt()), patch.object(side.base, "digest", return_value="seal"), \
                patch.object(side, "verify"), patch.object(side, "execute_arm", side_effect=execute), \
                patch.object(side.base.supervisor, "gpu_processes_absent", return_value=released), \
                patch.object(side.signal, "signal", return_value=None), patch.object(side.signal, "setitimer") as timer, \
                patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "3"}):
            if receipt_count == 6 and released and not failure:
                side.run("/fixture", True, clock=(time.time() - 30, time.monotonic() - 30))
            else:
                with self.assertRaisesRegex(ValueError, "partial pair"):
                    side.run("/fixture", True, clock=(time.time() - 30, time.monotonic() - 30))
        self.assertLessEqual(timer.call_args_list[0].args[1], 1030)
        return writes["/fixture/run/terminal.json"], order

    def test_controller_fixed_order_no_score_skip(self):
        terminal, order = self.controller()
        self.assertEqual(order, ["mixed", "all_memory"])
        self.assertEqual(terminal["status"], "COMPLETE")
        self.assertFalse(terminal["outcome_selective_skips"])
        self.assertEqual(terminal["progression_owner"], "Main")
        self.assertGreaterEqual(terminal["reserved_seconds"], 30)
        self.assertEqual(terminal["worker_reserved_seconds"], 6)

    def test_partial_second_arm_retains_first_no_retry(self):
        terminal, order = self.controller(receipt_count=3, failure=True)
        self.assertEqual(order, ["mixed", "all_memory"])
        self.assertEqual(list(terminal["arms"]), ["mixed"])
        self.assertEqual(terminal["status"], "FAILED_PARTIAL_NO_RETRY")

    def test_completion_requires_six_receipts_and_release(self):
        for count, released in ((5, True), (6, False)):
            terminal, _ = self.controller(receipt_count=count, released=released)
            self.assertEqual(terminal["status"], "FAILED_PARTIAL_NO_RETRY")

    def test_external_progression_not_automatic(self):
        self.assertEqual(side.PROGRESSION, dict(owner="Main", first_seed=0, decide_only_after_both_arms=True,
            mixed_dev_memory_min=15, mixed_exact_memory_min=15, mixed_adherence_min=30, mixed_act_min=31,
            technical_completion_required=True, next_seeds=[1, 2], automatic_progression=False))

    def test_prepare_seals_material_counts_device_and_two_parent_forks(self):
        original, native, prior = self.material()
        prior["model"] = self.plan["model"]
        template = dict(cases=[], requests=[], native_inputs=[])
        parent = dict(self.plan["parent"], readout=template)
        writes = {}
        with patch.object(Path, "resolve", lambda path, **kwargs: path), patch.object(Path, "mkdir"), \
                patch.object(side.memory, "fresh", return_value=Path("/fixture/prepared")), \
                patch.object(side.old, "read_plan", return_value=prior), patch.object(side.base, "read", return_value=original), \
                patch.object(side.base, "model_hashes", return_value={}), patch.object(side.memory, "parent_record", return_value=parent), \
                patch.object(side.base, "native_tokenizer", return_value=Tokenizer()), \
                patch.object(side.exact, "native_inputs", return_value=native), patch.object(side.memory, "template", return_value=template), \
                patch.object(side.old, "write", side_effect=lambda path, value: writes.update({str(path): value})), \
                patch.object(side.base, "digest", return_value="fixture-hash"), patch.object(side, "sources", return_value={}), \
                patch.object(side.trainer, "_warm_parent") as warm, patch.object(side.old, "seal") as seal:
            result = side.prepare("/fixture/original", 0, "3", time.time() + 3600, time.time() + 7200, "/fixture/prepared")
        self.assertEqual(result["status"], "PAIR_PREPARED_NOT_LAUNCHED")
        sealed = seal.call_args.args[1]
        self.assertEqual(sealed["device"], "3")
        self.assertEqual(sealed["arm_order"], ["mixed", "all_memory"])
        self.assertEqual(sealed["accounting"], side.COUNTS)
        self.assertEqual(sealed["aggregate_a40_seconds"], 5400)
        self.assertEqual(set(writes), {"/fixture/prepared/mixed.json", "/fixture/prepared/all_memory.json"})
        self.assertEqual([call.args[0] for call in warm.call_args_list], [parent["parent"]] * 2)
        self.assertEqual([call.args[1] for call in warm.call_args_list],
                         [f"/fixture/prepared/run/{arm}/adapter" for arm in side.ARMS])


if __name__ == "__main__":
    unittest.main()
