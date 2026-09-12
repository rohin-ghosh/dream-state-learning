"""CPU fixtures only: no native model, GPU query, process launch, or seed0 outputs."""
import copy
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

import astra_fundamental_replication_20260912 as replication

base = replication.base
readout = replication.readout


class Tokenizer:
    def encode(self, text):
        return [ord(character) for character in text]

    def apply_chat_template(self, messages, *, tokenize, add_generation_prompt):
        if tokenize is not False or add_generation_prompt is not True or len(messages) != 1:
            raise AssertionError("template call differs")
        return "<|im_start|>user\n" + messages[0]["content"] + "<|im_end|>\n<|im_start|>assistant\n"


class ReplicationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="replication-cpu-", dir="/tmp")
        self.addCleanup(temporary.cleanup)
        self.home = Path(temporary.name)
        self.seed0 = self.home / "seed0"
        self.seed0.mkdir()
        self.model = self.home / "model"
        self.model.mkdir()
        (self.model / "config.json").write_text('{"model_type":"qwen2"}')
        self.pair = self.home / "pair.py"
        self.pair.write_text("CPU fixture; never executed")
        self.off = self.seed0 / "readouts" / "OFF"
        self.off.mkdir(parents=True)
        self.out = self.home / "replications"
        self.plan = self.make_seed0()
        replication.write_plan(self.seed0, self.plan)
        cases = readout.selected_cases()
        off = dict(model=str(self.model), model_files=self.plan["model_files"], adapter=None,
                   adapter_files={}, source_hashes=readout.sources(), cases=cases, requests=readout.requests(cases),
                   worker_seconds=600, output_token_ceiling=3072)
        replication.write_plan(self.off, off)
        for name, value in (("SEED0_PLAN_SHA256", base.digest(self.seed0 / "plan.json")),
                            ("PAIR_SCRIPT_SHA256", base.digest(self.pair)),
                            ("OFF_PLAN_SHA256", base.digest(self.off / "plan.json"))):
            context = patch.object(replication, name, value)
            context.start()
            self.addCleanup(context.stop)
        self.gpu_guard = self.guarded(replication, "check_free")
        self.supervisor_guard = self.guarded(base, "supervise")
        self.native_guard = self.guarded(base, "native_tokenizer")
        self.readout_guard = self.guarded(readout, "run")

    def guarded(self, owner, name):
        context = patch.object(owner, name, side_effect=AssertionError("forbidden CPU-test external operation: " + name))
        result = context.start()
        self.addCleanup(context.stop)
        return result

    def make_seed0(self):
        groups = [f"train-addition-{index:03d}" for index in range(64)] + [f"train-memory-{index:03d}" for index in range(16)]
        audits, hashes = {}, {}
        for arm in replication.ARMS:
            rows = [dict(group=group, spans=[["fixture context", False, "context"],
                                          [arm + " target", True, "authored_birth_target"]]) for group in groups]
            base.write_json(self.seed0 / (arm + ".json"), dict(corpus=rows))
            hashes[arm] = base.digest(self.seed0 / (arm + ".json"))
            audits[arm] = [dict(case_id=group, input_tokens=56 if index < 79 else 93,
                               target_tokens=11 if index < 79 else 43, labels_sha256="fixture")
                           for index, group in enumerate(groups)]
        sources = dict(base.sources(), **{name: base.digest(base.REPO / "organism_v6" / name)
            for name in ("fundamental_teaching_corpus.py", "train_adapter_v3.py")})
        sources["launcher_script"] = base.digest(self.pair)
        return dict(model=str(self.model), model_files=base.model_hashes(self.model), source_hashes=sources,
                    config=replication.recipe(str(self.model), 0), selected_control_label="COMPUTED",
                    row_audits=audits, corpus_sha256=hashes, alternatives=[dict(label="COMPUTED", matched=True)],
                    tokens={arm: dict(replication.TOKENS) for arm in replication.ARMS},
                    lease_end=float(time.time() + 90000), material_role=replication.MATERIAL_ROLE,
                    model_origin="UNRESOLVED_LOCAL_HASHES_ONLY", fits_authorized_by_script=False,
                    status="NATIVE_ENCODER_AND_PAIRED_TOKENS_VERIFIED", eval_dev_ids=list(readout.CASE_IDS))

    def prepare(self):
        return replication.prepare(self.seed0, self.out, self.pair, self.off)

    def rewrite(self, path, value):
        path.write_bytes(base.encoded(value))

    def fit_evidence(self, root, arm):
        plan = replication.verify(root)
        stage = root / ("fit_" + arm)
        stage.mkdir(exist_ok=True)
        adapter = stage / "adapter"
        adapter.mkdir()
        worker = stage / "worker"
        worker.mkdir()
        base.write_json(worker / "supervision.json", dict(ok=True, reservation_release_verified=True,
            owned_group_empty=True, gpu_processes_absent=True, returncode=0, error=None,
            device=replication.device_for(plan, arm), reserved_seconds=2.0))
        base.write_json(worker / "process.json", dict(argv=replication.fit_command(root, plan, arm),
            device=replication.device_for(plan, arm), timeout=600))
        if not (stage / "allocation.json").exists():
            base.write_json(stage / "allocation.json", dict(plan_sha256=base.digest(root / "plan.json"),
                arm=arm, device=replication.device_for(plan, arm), fresh_adapter=True))
        manifest = dict(config=plan["config"], base_model=plan["model"], steps=80, micro_batches=80,
            epochs_run=4, nonfinite_batches=0, empty=False, final_loss=.1,
            corpus=dict(sha256=plan["corpus_sha256"][arm], n_items=80, n_encoded=80, n_skipped_no_target=0),
            truncation=dict(items_truncated=0, context_tokens_dropped=0, target_tokens_dropped=0, items_split=0),
            tokens=dict(total=4517, target=912), train_tokens_seen=18068)
        saved = dict(r=8, lora_alpha=16, lora_dropout=.05, peft_type="LORA", bias="none",
                     base_model_name_or_path=plan["model"], target_modules=plan["config"]["target_modules"])
        base.write_json(adapter / "train_manifest.json", manifest)
        base.write_json(adapter / "adapter_config.json", saved)
        (adapter / "adapter_model.safetensors").write_bytes(f"CPU fixture seed {plan['config']['seed']} arm {arm}".encode())
        (adapter / "DONE").write_text("fixture")
        return manifest, saved

    def prepared_fits(self):
        self.prepare()
        root = self.out / "seed1"
        for arm in replication.ARMS:
            self.fit_evidence(root, arm)
            replication.verify_fit(root, arm)
        return root

    def prepared_readouts(self):
        root = self.prepared_fits()
        with patch.object(base, "native_tokenizer", return_value=Tokenizer()):
            replication.prepare_readouts(root)
        return root

    def test_transform_changes_only_seed_and_explicit_provenance(self):
        original = copy.deepcopy(self.plan)
        for seed in (1, 2):
            transformed = replication.transform_plan(self.plan, seed, {"fixture": True})
            self.assertEqual(transformed["config"], dict(original["config"], seed=seed))
            self.assertEqual(transformed["replication"]["paired_seeds"], [1, 2])
            self.assertTrue(transformed["replication"]["fresh_adapter_per_arm"])
            del transformed["replication"]
            transformed["config"]["seed"] = 0
            self.assertEqual(transformed, original)
        self.assertEqual(self.plan, original)
        for seed in (0, 3, -1, True, 1.0, "1"):
            with self.assertRaises(ValueError):
                replication.transform_plan(self.plan, seed, {})

    def test_recipe_tokens_label_and_cases_cannot_change(self):
        variants = []
        for key, value in (("lr", .001), ("rank", 16), ("epochs", 8), ("seed", 1),
                           ("svd_init", True), ("pack", True), ("max_len", 1024)):
            changed = copy.deepcopy(self.plan)
            changed["config"][key] = value
            variants.append(changed)
        for key, value in (("selected_control_label", "RESULT"), ("eval_dev_ids", ["eval-unknown-016"]),
                           ("tokens", {arm: dict(input_tokens=4517, target_tokens=910) for arm in replication.ARMS})):
            changed = copy.deepcopy(self.plan)
            changed[key] = value
            variants.append(changed)
        changed = copy.deepcopy(self.plan)
        changed["row_audits"]["control"].reverse()
        variants.append(changed)
        for changed in variants:
            with self.subTest(config=changed["config"]), self.assertRaises(ValueError):
                replication.validate_seed0(changed)

    def test_prepare_both_seeds_exact_bytes_no_native_calls_no_adapters(self):
        result = self.prepare()
        self.assertEqual(result["optimizer_seeds"], [1, 2])
        for seed in (1, 2):
            root = self.out / f"seed{seed}"
            plan = replication.verify(root)
            self.assertEqual(plan["config"]["seed"], seed)
            self.assertEqual(plan["source_hashes"], self.plan["source_hashes"])
            self.assertEqual(plan["corpus_sha256"], self.plan["corpus_sha256"])
            for arm in replication.ARMS:
                self.assertEqual((root / (arm + ".json")).read_bytes(), (self.seed0 / (arm + ".json")).read_bytes())
                self.assertFalse((root / ("fit_" + arm)).exists())
        for guard in (self.gpu_guard, self.supervisor_guard, self.native_guard, self.readout_guard):
            guard.assert_not_called()

    def test_plan_pin_launcher_model_corpus_and_source_drift_rejected(self):
        with patch.object(replication, "SEED0_PLAN_SHA256", "wrong"), self.assertRaisesRegex(ValueError, "pinned attempt1"):
            self.prepare()
        with patch.object(replication, "PAIR_SCRIPT_SHA256", "wrong"), self.assertRaisesRegex(ValueError, "source bytes"):
            self.prepare()
        with patch.object(base, "model_hashes", return_value={"changed": "hash"}), self.assertRaisesRegex(ValueError, "model bytes"):
            self.prepare()
        with patch.object(base, "sources", return_value={}), self.assertRaisesRegex(ValueError, "source bytes"):
            self.prepare()
        (self.seed0 / "teach.json").write_text('{}')
        with self.assertRaisesRegex(ValueError, "seed0 corpus changed"):
            self.prepare()
        self.assertFalse(self.out.exists())

    def test_off_binding_reads_plan_only_and_rejects_changed_base(self):
        (self.off / "model_output_do_not_read").write_bytes(b"not accessed")
        original = base.read(self.off / "plan.json")
        changed = dict(original, model="different base")
        self.rewrite(self.off / "plan.json", changed)
        self.rewrite(self.off / "plan.sha256.json", dict(sha256=base.digest(self.off / "plan.json")))
        with patch.object(replication, "OFF_PLAN_SHA256", base.digest(self.off / "plan.json")), \
             self.assertRaisesRegex(ValueError, "OFF plan/base"):
            self.prepare()

    def test_stale_roots_partial_bundle_and_missing_sibling_stop(self):
        self.prepare()
        with self.assertRaisesRegex(ValueError, "stale/partial"):
            self.prepare()
        completion = (self.out / "preparation.json").read_bytes()
        (self.out / "preparation.json").unlink()
        with self.assertRaises(FileNotFoundError):
            replication.verify(self.out / "seed1")
        (self.out / "preparation.json").write_bytes(completion)
        (self.out / "seed2" / "control.json").unlink()
        with self.assertRaises(FileNotFoundError):
            replication.verify(self.out / "seed1")

    def test_output_cannot_overlap_seed0(self):
        with self.assertRaisesRegex(ValueError, "overlaps seed0"):
            replication.prepare(self.seed0, self.seed0 / "replications", self.pair, self.off)

    def test_seed_specific_fresh_adapter_paths_and_effective_native_recipe(self):
        self.prepare()
        paths = set()
        for seed in (1, 2):
            root = self.out / f"seed{seed}"
            plan = replication.verify(root)
            for arm in replication.ARMS:
                command = replication.fit_command(root, plan, arm)
                self.assertEqual(command[command.index("--seed") + 1], str(seed))
                self.assertEqual(command[command.index("--lr") + 1], "0.0003")
                paths.add(command[command.index("--out") + 1])
                self.assertFalse(any("resume" in item or item == "--adapter" for item in command))
        self.assertEqual(len(paths), 4)

    def test_launch_requires_allow_gpu_before_any_external_operation(self):
        for function in (replication.launch_fit, replication.launch_readout):
            with self.assertRaisesRegex(ValueError, "allow-gpu"):
                function(self.out / "seed1", "teach")
            with self.assertRaises(ValueError):
                function(self.out / "seed1", "OFF", allow_gpu=True)
        self.gpu_guard.assert_not_called()
        self.supervisor_guard.assert_not_called()

    def test_exact_four_gpu_mapping_and_seed2_fit_readouts(self):
        self.prepare()
        for seed, expected in ((1, {"teach": "0", "control": "1"}), (2, {"teach": "2", "control": "3"})):
            plan = replication.verify(self.out / f"seed{seed}")
            self.assertEqual({arm: replication.device_for(plan, arm) for arm in replication.ARMS}, expected)
        root = self.out / "seed2"
        for arm in replication.ARMS:
            self.fit_evidence(root, arm)
            replication.verify_fit(root, arm)
        with patch.object(base, "native_tokenizer", return_value=Tokenizer()):
            replication.prepare_readouts(root)
        for arm, expected in (("teach", "2"), ("control", "3")):
            self.assertEqual(replication.sealed_plan(root / "readouts" / arm)["device"], expected)
        self.gpu_guard.assert_not_called()

    def test_seed2_launch_checks_gpu2_and_seed2_receipt_rejects_gpu0(self):
        self.prepare()
        root = self.out / "seed2"

        def supervise(selected_root, selected_plan, stage, command):
            self.assertEqual(selected_plan["device"], "2")
            self.fit_evidence(root, "teach")

        with patch.object(replication, "check_free", return_value=({}, "fixture")) as free, \
             patch.object(base, "supervise", side_effect=supervise):
            replication.launch_fit(root, "teach", allow_gpu=True)
            free.assert_called_once_with("2")
        path = root / "fit_teach" / "worker" / "supervision.json"
        self.rewrite(path, dict(base.read(path), device="0"))
        with self.assertRaisesRegex(ValueError, "cleanup unverified"):
            replication.verify_fit(root, "teach")

    def test_fit_launch_reuses_check_free_and_one_supervisor_no_retry(self):
        self.prepare()
        root = self.out / "seed1"

        def supervise(selected_root, selected_plan, stage, command):
            self.assertEqual(selected_root, root)
            self.assertEqual(selected_plan["device"], "0")
            self.assertEqual(stage, root / "fit_teach" / "worker")
            self.assertFalse((root / "fit_teach" / "adapter").exists())
            self.fit_evidence(root, "teach")

        with patch.object(replication, "check_free", return_value=({"fixture": True}, "<fixture/>")) as free, \
             patch.object(base, "supervise", side_effect=supervise) as supervisor:
            result = replication.launch_fit(root, "teach", allow_gpu=True)
            self.assertEqual(result["steps"], 80)
            free.assert_called_once_with("0")
            self.assertEqual(supervisor.call_count, 1)
            with self.assertRaisesRegex(ValueError, "stale/partial"):
                replication.launch_fit(root, "teach", allow_gpu=True)
            self.assertEqual(supervisor.call_count, 1)

    def test_failed_supervision_retains_partial_path_without_retry(self):
        self.prepare()
        root = self.out / "seed1"
        with patch.object(replication, "check_free", return_value=({}, "fixture")), \
             patch.object(base, "supervise", side_effect=ValueError("supervised failure")) as supervisor:
            with self.assertRaisesRegex(ValueError, "supervised failure"):
                replication.launch_fit(root, "control", allow_gpu=True)
            self.assertTrue((root / "fit_control" / "allocation.json").exists())
            with self.assertRaisesRegex(ValueError, "stale/partial"):
                replication.launch_fit(root, "control", allow_gpu=True)
            self.assertEqual(supervisor.call_count, 1)

    def test_fit_manifest_validation_and_sealed_adapter_drift(self):
        self.prepare()
        root = self.out / "seed1"
        manifest, saved = self.fit_evidence(root, "teach")
        plan = replication.verify(root)
        for key, value in (("steps", 79), ("epochs_run", 3), ("nonfinite_batches", 1),
                           ("final_loss", float("inf")), ("train_tokens_seen", 18067)):
            changed = copy.deepcopy(manifest)
            changed[key] = value
            with self.assertRaises(ValueError):
                replication.validate_fit_manifest(plan, "teach", changed, saved)
        result = replication.verify_fit(root, "teach")
        self.assertEqual(result, replication.verify_fit(root, "teach"))
        (root / "fit_teach" / "adapter" / "adapter_model.safetensors").write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "verified fit artifact changed"):
            replication.verify_fit(root, "teach")

    def test_partial_fit_is_not_complete_or_ready_for_readouts(self):
        self.prepare()
        root = self.out / "seed1"
        (root / "fit_teach").mkdir()
        with self.assertRaises(FileNotFoundError):
            replication.verify_fit(root, "teach")
        with self.assertRaises(FileNotFoundError):
            replication.prepare_readouts(root)
        status = replication.terminal_status(root)
        self.assertIn("NOT_TERMINALLY_VERIFIED", status["fits"]["teach"])
        self.assertEqual(status["fits"]["control"], "NOT_STARTED")
        self.assertFalse((root / "readouts").exists())

    def test_readout_preparation_only_two_arms_preserves_base_cases_and_requests(self):
        root = self.prepared_readouts()
        preparation = base.read(root / "readout_preparation.json")
        self.assertEqual(set(preparation["cells"]), {"teach", "control"})
        self.assertEqual(preparation["new_off_calls"], 0)
        self.assertFalse((root / "readouts" / "OFF").exists())
        teach = replication.sealed_plan(root / "readouts" / "teach")
        control = replication.sealed_plan(root / "readouts" / "control")
        self.assertEqual(teach["requests"], control["requests"])
        self.assertEqual(teach["native_inputs"], control["native_inputs"])
        self.assertEqual(len(teach["cases"]), 48)
        self.assertEqual(teach["model_files"], self.plan["model_files"])
        self.assertNotEqual(teach["adapter"], control["adapter"])
        self.gpu_guard.assert_not_called()
        self.readout_guard.assert_not_called()
        with self.assertRaisesRegex(ValueError, "stale/partial"):
            replication.prepare_readouts(root)

    def test_partial_readout_preparation_cannot_resume_or_launch(self):
        root = self.prepared_fits()
        with patch.object(readout, "prepare", side_effect=ValueError("fixture tokenizer failure")):
            with self.assertRaisesRegex(ValueError, "tokenizer failure"):
                replication.prepare_readouts(root)
        with self.assertRaisesRegex(ValueError, "stale/partial"):
            replication.prepare_readouts(root)
        with self.assertRaises(FileNotFoundError):
            replication.launch_readout(root, "teach", allow_gpu=True)
        self.gpu_guard.assert_not_called()

    def test_readout_launch_delegates_once_and_status_does_not_read_responses(self):
        root = self.prepared_readouts()
        target = root / "readouts" / "teach"
        with patch.object(base, "native_tokenizer", return_value=Tokenizer()), \
             patch.object(replication, "check_free", return_value=({}, "fixture")) as free, \
             patch.object(readout, "run", return_value={"fixture": True}) as run:
            self.assertEqual(replication.launch_readout(root, "teach", allow_gpu=True), {"fixture": True})
            free.assert_called_once_with("0")
            run.assert_called_once_with(target, allow_gpu=True)
            with self.assertRaisesRegex(ValueError, "stale/partial"):
                replication.launch_readout(root, "teach", allow_gpu=True)
        status = replication.terminal_status(root)
        self.assertIn("NOT_TERMINALLY_VERIFIED", status["readouts"]["teach"])
        self.assertEqual(status["readouts"]["control"], "PREPARED_ONLY")
        self.assertFalse(status["reads_model_outputs"])

    def test_fit_command_supervision_and_done_are_checked(self):
        self.prepare()
        root = self.out / "seed1"
        self.fit_evidence(root, "control")
        path = root / "fit_control" / "worker" / "supervision.json"
        original = base.read(path)
        self.rewrite(path, dict(original, reservation_release_verified=False))
        with self.assertRaisesRegex(ValueError, "cleanup unverified"):
            replication.verify_fit(root, "control")
        self.rewrite(path, original)
        (root / "fit_control" / "adapter" / "DONE").unlink()
        with self.assertRaisesRegex(ValueError, "missing DONE"):
            replication.verify_fit(root, "control")

    def test_no_lease_extension_and_changed_replication_source_rejected(self):
        self.prepare()
        root = self.out / "seed1"
        with patch.object(replication, "dependency_hashes", return_value={}), \
             self.assertRaisesRegex(ValueError, "source/interpreter"):
            replication.verify(root)
        with patch.object(replication.time, "time", return_value=self.plan["lease_end"] - 100), \
             self.assertRaisesRegex(ValueError, "inherited lease"):
            replication.launch_fit(root, "teach", allow_gpu=True)
        self.gpu_guard.assert_not_called()


if __name__ == "__main__":
    unittest.main()
