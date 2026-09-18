"""Synthetic CPU contract tests; no model execution or native-data claims."""
import copy
import datetime
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from gpu import astra_parent_wake_diagnostic as diagnostic


class WakeDiagnosticTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.material, self.root = self.base / "material", self.base / "run"
        self.material.mkdir()
        self.model = self.base / "model"
        self.model.mkdir()
        (self.model / "base.safetensors").write_bytes(b"synthetic fixture, not weights")
        self.selected = [f"rg/mini_sudoku/{1850000 + index}" for index in range(5)]
        self.selected += [f"rg/countdown/{1200000 + index}" for index in range(27)]
        self.schedule = self.selected + [f"rg/countdown/{1300000 + index}" for index in range(32)]
        self.sources = {}
        self.boundary = dict(tokenizer_validation="actual local tokenizer")
        self.selection = dict(count=32, selected_episodes=self.selected, selection="measured", max_len=4096)
        result = dict(status="READY", selection=self.selection, boundary=self.boundary, arms={})
        for arm, target_tokens in (("lesson", 3), ("sham", 4)):
            original = self.base / arm
            original.mkdir()
            self.put(original / "schedule.json", self.schedule)
            self.sources[arm] = dict(root=str(original), inventory=dict(files={"schedule.json": diagnostic.digest(original / "schedule.json")}),
                                     local_pins=dict(model_path=str(self.model), files=diagnostic.file_hashes(self.model)))
            rows = []
            for episode in self.selected:
                prompt = "=== STATE ===\nGOAL: mini puzzle.\nquestion " + episode + "\nWrite each attempt on one ACT: line; format\n"
                item = dict(meta=dict(episode_id=episode), spans=[["rendered context", False, "parent_removed_context"],
                                                                ["ACT: child", True, "raw_child_wake"]])
                rows.append(dict(item=item, rendered_context="rendered context", input_tokens=10,
                                 target_tokens=target_tokens, source=dict(raw_output="ACT: child", original_prompt=prompt)))
            self.put(self.material / f"{arm}.json", dict(recipe="source_linked_raw_wake_v3_spans_v1",
                     boundary=self.boundary, corpus=[row["item"] for row in rows]))
            self.put(self.material / f"{arm}_source_map.json", dict(rows=rows))
            result["arms"][arm] = dict(selected_examples=32, input_tokens=320, target_tokens=32 * target_tokens,
                                        teacher_tokens=203 if arm == "lesson" else 158)
        self.put(self.material / "results.json", result)
        self.put(self.material / "selection.json", self.selection)
        self.put(self.material / "original_sources.json", self.sources)
        source = self.base / "producer.py"
        source.write_text("synthetic producer")
        self.put(self.material / "source_hashes.json", {str(source): diagnostic.digest(source)})
        self.reseal()
        self.addCleanup(patch.stopall)
        patch.object(diagnostic, "native_gym", return_value=None).start()

    def put(self, path, value):
        path.write_text(json.dumps(value))

    def reseal(self):
        self.put(self.material / "artifact_hashes.json", dict(files={path.name: diagnostic.digest(path)
                 for path in self.material.iterdir() if path.name != "artifact_hashes.json"}))

    def prepare(self):
        return diagnostic.prepare(self.material, self.root)

    def make_fit(self, arm, plan):
        adapter = self.root / "training" / f"{arm}_seed0"
        adapter.mkdir()
        (adapter / "adapter_model.safetensors").write_bytes(b"synthetic adapter " + arm.encode())
        self.put(adapter / "adapter_config.json", dict(r=8, lora_alpha=16, lora_dropout=0.05))
        (adapter / "DONE").write_text("synthetic")
        tokens = plan["bound"]["tokens"][arm]
        manifest = dict(config=diagnostic.TRAIN_CONFIG, base_model=str(self.model), steps=96,
                        nonfinite_batches=0, final_loss=0.5,
                        corpus=dict(sha256=diagnostic.digest(self.material / f"{arm}.json"), n_items=32,
                                    n_encoded=32, n_skipped_no_target=0),
                        truncation=dict(items_truncated=0, context_tokens_dropped=0, target_tokens_dropped=0, items_split=0),
                        tokens=dict(target=tokens["target_tokens"], total=tokens["input_tokens"],
                                    context=tokens["input_tokens"] - tokens["target_tokens"]),
                        train_tokens_seen=3 * tokens["input_tokens"])
        self.put(adapter / "train_manifest.json", manifest)
        return adapter

    def test_prepare_is_cpu_only_and_commands_exact(self):
        before = {path.name: path.read_bytes() for path in self.material.iterdir()}
        with patch.object(diagnostic.subprocess, "Popen") as popen, patch.object(diagnostic, "check_free") as free:
            plan = self.prepare()
            free.assert_not_called()
            popen.assert_not_called()
        for arm in diagnostic.ARMS:
            command = plan["commands"][arm]
            self.assertEqual(command[:4], [diagnostic.sys.executable, "-B", "-m", "organism_v6.train_adapter_v3"])
            for key, value in {"--corpus": str(self.material / f"{arm}.json"), "--out": str(self.root / "training" / f"{arm}_seed0"),
                               "--rank": "8", "--alpha": "16", "--dropout": "0.05", "--lr": "1e-4", "--epochs": "3",
                               "--seed": "0", "--batch-size": "1", "--max-len": "4096"}.items():
                self.assertEqual(command[command.index(key) + 1], value)
            self.assertIn("--no-pack", command)
            self.assertNotIn("--chat-template", command)
            self.assertNotIn("--no-grad-checkpoint", command)
            self.assertFalse(any("source_map" in argument for argument in command))
        self.assertEqual(before, {path.name: path.read_bytes() for path in self.material.iterdir()})
        self.assertNotEqual(plan["bound"]["tokens"]["lesson"], plan["bound"]["tokens"]["sham"])
        self.assertEqual(plan["bound"]["question_audit"]["status"], "EPISODE_DISJOINT_ONLY")

    def test_preexisting_output_rejected(self):
        self.prepare()
        before = (self.root / "plan.json").read_bytes()
        with self.assertRaises(ValueError):
            self.prepare()
        self.assertEqual(before, (self.root / "plan.json").read_bytes())

    def test_material_tamper_rejected(self):
        self.prepare()
        with (self.material / "lesson.json").open("a") as target:
            target.write(" ")
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            diagnostic.verify_plan(self.root)

    def test_source_model_plan_and_schedule_tamper(self):
        self.prepare()
        for path in (self.base / "producer.py", self.model / "base.safetensors", self.base / "lesson/schedule.json", self.root / "plan.json"):
            original = path.read_bytes()
            path.write_bytes(original + b" ")
            with self.subTest(path=path), self.assertRaises(ValueError):
                diagnostic.verify_plan(self.root)
            path.write_bytes(original)

    def test_source_membership_all64_must_not_overlap_canary(self):
        changed = [*self.schedule[:-1], diagnostic.CANARIES[0]]
        for source in self.sources.values():
            path = Path(source["root"]) / "schedule.json"
            self.put(path, changed)
            source["inventory"]["files"]["schedule.json"] = diagnostic.digest(path)
        self.put(self.material / "original_sources.json", self.sources)
        self.reseal()
        with self.assertRaisesRegex(ValueError, "source/canary"):
            self.prepare()
        self.assertFalse(self.root.exists())

    def test_skip_injected_tokenizer_and_wrong_counts_rejected(self):
        original = diagnostic.read(self.material / "results.json")
        for changed in (dict(original, status="PAIRED_SKIP"),
                        dict(original, boundary=dict(tokenizer_validation="injected CPU fixture"))):
            self.put(self.material / "results.json", changed)
            self.reseal()
            with self.assertRaisesRegex(ValueError, "native tokenizer READY"):
                self.prepare()
        self.put(self.material / "results.json", original)
        original["arms"]["lesson"]["target_tokens"] += 1
        self.put(self.material / "results.json", original)
        self.reseal()
        with self.assertRaisesRegex(ValueError, "token totals"):
            self.prepare()

    def test_manifest_path_traversal_rejected(self):
        inventory = diagnostic.read(self.material / "artifact_hashes.json")
        inventory["files"]["../outside"] = "0" * 64
        self.put(self.material / "artifact_hashes.json", inventory)
        with self.assertRaises(ValueError):
            self.prepare()

    def test_mask_or_target_modification_rejected_even_if_resealed(self):
        corpus = diagnostic.read(self.material / "lesson.json")
        corpus["corpus"][0]["spans"][0][1] = True
        self.put(self.material / "lesson.json", corpus)
        self.reseal()
        with self.assertRaisesRegex(ValueError, "corpus/source-map"):
            self.prepare()

    def test_training_tokens_and_actual_adapter_configuration(self):
        plan = self.prepare()
        adapter = self.make_fit("lesson", plan)
        self.assertIn("adapter_model.safetensors", diagnostic.verify_fit(self.root, plan, "lesson"))
        path = adapter / "train_manifest.json"
        original = diagnostic.read(path)
        for section, key, value in (("tokens", "target", 999), ("tokens", "total", 321),
                                    ("config", "chat_template", True), ("config", "alpha", 0),
                                    ("truncation", "items_split", 1), ("corpus", "n_encoded", 33)):
            changed = copy.deepcopy(original)
            changed[section][key] = value
            self.put(path, changed)
            with self.subTest(section=section, key=key), self.assertRaises(ValueError):
                diagnostic.verify_fit(self.root, plan, "lesson")
        self.put(path, original)
        self.put(adapter / "adapter_config.json", dict(r=8, lora_alpha=32, lora_dropout=0.05))
        with self.assertRaisesRegex(ValueError, "actual adapter"):
            diagnostic.verify_fit(self.root, plan, "lesson")

    def exercise(self, fail=None, mutate_prior=False):
        plan = self.prepare()
        calls = []

        def worker(command, *, log_path, timeout, device):
            arm = log_path.parent.name
            kind = "train" if command[3].endswith("train_adapter_v3") else "pair"
            calls.append((arm, kind, device, timeout))
            self.assertEqual(os.environ["CUDA_VISIBLE_DEVICES"], "1")
            if fail == (arm, kind):
                raise subprocess.TimeoutExpired(command, timeout)
            if kind == "train":
                self.make_fit(arm, plan)
            else:
                spec = diagnostic.read(log_path.parent / "probe_spec.json")
                self.assertEqual(spec["episode_ids"], diagnostic.CANARIES)
                self.assertEqual((spec["gen_seed"], spec["budget_ticks"], spec["wake_max_tokens"], spec["scratchpad_max_tokens"],
                                  spec["total_token_budget"]), (0, 1, 400, 100, 38400))
                self.assertEqual(spec["order"], ["off", "on"])
                self.assertNotIn("teacher", spec)
                output = Path(spec["output_dir"])
                output.mkdir()
                self.put(output / "PAIR_DONE.json", dict(spec_sha256=diagnostic.digest(log_path.parent / "probe_spec.json"),
                         workers=dict(off={"pid": 1}, on={"pid": 2}), source_snapshot={}, receipt_sha256={"synthetic": arm}))
                if mutate_prior and arm == "sham":
                    prior = self.root / "probes/lesson/PAIR_DONE.json"
                    changed = diagnostic.read(prior)
                    changed["unexpected"] = True
                    self.put(prior, changed)
            return 1

        with patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "1"}), patch.object(diagnostic.supervisor, "run_worker", side_effect=worker), \
                patch.object(diagnostic, "validate_pair", side_effect=lambda output, *_: {"synthetic": output.name}), \
                patch.object(diagnostic.supervisor, "gpu_processes_absent", return_value=False):
            if fail or mutate_prior:
                with self.assertRaises((subprocess.TimeoutExpired, ValueError)):
                    diagnostic.execute(self.root, "1")
            else:
                diagnostic.execute(self.root, "1")
        return calls

    def test_sequential_same_device_control_retained_and_revalidated(self):
        self.assertEqual(self.exercise(), [("lesson", "train", "1", 900), ("lesson", "pair", "1", 2100),
                                          ("sham", "train", "1", 900), ("sham", "pair", "1", 2100)])
        done = diagnostic.read(self.root / "COMPLETED.json")
        self.assertEqual(set(done["arms"]), {"lesson", "sham"})
        self.assertFalse(done["boundary"]["H1_claim"])
        self.assertTrue((self.root / "probes/lesson/PAIR_DONE.json").exists())
        for value in (done["completed_utc"], diagnostic.read(self.root / "STARTED.json")["started_utc"],
                      *(evidence["completed_utc"] for evidence in done["arms"].values())):
            self.assertEqual(datetime.datetime.fromisoformat(value).utcoffset(), datetime.timedelta(0))

    def test_timeout_stops_without_retry_or_dropping_completed_control(self):
        calls = self.exercise(fail=("sham", "train"))
        self.assertEqual(len(calls), 3)
        self.assertFalse((self.root / "COMPLETED.json").exists())
        failure = diagnostic.read(self.root / "FAILED.json")
        self.assertEqual(failure["completed_arms"], ["lesson"])
        self.assertFalse(failure["gpu_processes_absent"])
        self.assertEqual(datetime.datetime.fromisoformat(failure["failed_utc"]).utcoffset(), datetime.timedelta(0))
        self.assertTrue((self.root / "logs/lesson/result.json").exists())

    def test_prior_pair_mutation_rejects_final_completion(self):
        self.exercise(mutate_prior=True)
        self.assertFalse((self.root / "COMPLETED.json").exists())

    def test_missing_probe_output_rejected(self):
        self.prepare()
        with self.assertRaises(FileNotFoundError):
            diagnostic.verify_probe(self.root, "lesson", "0" * 64)

    def test_explicit_launch_preserves_venv_and_continuous_reservation(self):
        self.prepare()
        with patch.object(diagnostic, "check_free", return_value=({"gpu_uuid": "test"}, "<xml/>")) as free, \
                patch.object(diagnostic.subprocess, "Popen") as popen:
            popen.return_value.pid = 4242
            receipt = diagnostic.launch(self.root, "1")
            free.assert_called_once_with("1")
            args, kwargs = popen.call_args
            self.assertEqual(args[0][0], diagnostic.sys.executable)
            self.assertEqual(kwargs["env"]["CUDA_VISIBLE_DEVICES"], "1")
            self.assertEqual(kwargs["env"]["V6_MODEL"], str(self.model))
            self.assertEqual(kwargs["env"]["HF_HUB_OFFLINE"], "1")
            self.assertEqual(kwargs["env"]["PYTHONPATH"], str(diagnostic.SOURCE))
            self.assertTrue(kwargs["start_new_session"])
            self.assertNotIn("shell", kwargs)
            self.assertEqual(receipt["status"], "LAUNCHED_NOT_COMPLETED")
            self.assertEqual(receipt["source"], str(diagnostic.SOURCE))
            self.assertEqual(receipt["script_sha256"], diagnostic.digest(Path(diagnostic.__file__)))
            self.assertEqual(datetime.datetime.fromisoformat(receipt["launched_utc"]).utcoffset(), datetime.timedelta(0))
            with self.assertRaisesRegex(ValueError, "already attempted"):
                diagnostic.launch(self.root, "1")

    def test_occupied_device_does_not_start_controller(self):
        self.prepare()
        with patch.object(diagnostic, "check_free", side_effect=ValueError("occupied")), patch.object(diagnostic.subprocess, "Popen") as popen:
            with self.assertRaisesRegex(ValueError, "occupied"):
                diagnostic.launch(self.root, "1")
            popen.assert_not_called()

    def test_native_question_overlap_and_solutions_reported_without_exclusion(self):
        rows = {arm: diagnostic.read(self.material / f"{arm}_source_map.json")["rows"] for arm in diagnostic.ARMS}
        entries = {episode: dict(question="question " + episode, answer="shared grid")
                   for episode in self.selected[:5] + diagnostic.CANARIES}

        class Gym:
            def _item(self, family, seed):
                return None, entries[f"rg/{family}/{seed}"]

        with patch.object(diagnostic, "native_gym", return_value=Gym()):
            audit = diagnostic.question_audit(rows)
            self.assertEqual(audit["status"], "SELECTED_MINI_QUESTION_DISJOINT")
            self.assertEqual(len(audit["solution_overlaps"]), 80)
            self.assertEqual(len(audit["selected_mini_episodes"]), 5)
            entries[diagnostic.CANARIES[0]]["question"] = entries[self.selected[0]]["question"]
            with self.assertRaisesRegex(ValueError, "exact source/canary puzzle overlap"):
                diagnostic.question_audit(rows)

    def test_actual_local_p0_prompt_envelope_when_capsule_available(self):
        material = Path("/tmp/astra_raw_wake_export_capture_20260912/astra_P0_raw_wake_export_20260912_attempt1")
        if not material.is_dir():
            self.skipTest("optional real P0 CPU capsule absent")
        rows = {arm: diagnostic.read(material / f"{arm}_source_map.json")["rows"] for arm in diagnostic.ARMS}
        audit = diagnostic.question_audit(rows)
        self.assertEqual(audit["status"], "EPISODE_DISJOINT_ONLY")
        self.assertEqual(len(audit["selected_mini_episodes"]), 5)
        self.assertEqual(len(audit["source_question_sha256"]), 5)
        self.assertTrue(all(len(value) == 64 for value in audit["source_question_sha256"].values()))


if __name__ == "__main__":
    unittest.main()
