"""CPU fixtures only; no model weights, GPUs, downloads, or scientific results."""
from __future__ import annotations

from collections import Counter
import copy
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from gpu import astra_memory_cumulative_diagnostic as probe
from organism_v6 import memory_dose as md


class Tokenizer:
    eos_token = md.IM_END
    pad_token = md.IM_END

    def __call__(self, text, **kwargs):
        pieces = re.findall(r" not|.", text, re.DOTALL)
        return SimpleNamespace(input_ids=[100000 if piece == " not" else ord(piece) for piece in pieces])

    def apply_chat_template(self, messages, **kwargs):
        return md.render_chat(messages[0]["content"])


def bank_fixture():
    taken = set()
    owners = md.make_owner_ids(md._rng("owners", 1), md.OWNERS_PER_DOSE * len(md.DOSES), taken)
    return md.generate_bank(0, 1, owners, {}, {}, taken)


def old_fixture():
    rows = [dict(context="", target="x" * (20 if index < 4439 else 19), chat=False,
                 mask_context=False, weight=1.0, kind="filler_colour", owner=None,
                 colour=None, session=1, order_key=index, event_ids=[f"fixture-{index}"])
            for index in range(probe.OLD_ROWS)]
    corpus, _ = probe.corpus_snapshot(rows, Tokenizer())
    return corpus


def fit_meta(corpus, model):
    stats = corpus["stats"]
    return dict(**probe.RECIPE, recipe=probe.NATIVE_RECIPE, n_items=len(corpus["corpus"]),
                steps=stats["steps"], total_steps=stats["steps"], tokens=stats["input_tokens"] * 3,
                supervised_tokens=stats["shifted_supervised_tokens"] * 3,
                corpus_sha=corpus["sha"], items_sha=corpus["items_sha"], final_loss=1.0,
                ordering="chronological", writer="occurrences", representation="frames", shuffled=False,
                boundary_straddles=0, truncated_items=0, measure_only=False, wall_seconds=.1, model=str(model))


class DataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bank = bank_fixture()
        cls.old = old_fixture()

    def test_native_event_copy_order_and_unchanged_old_prefix(self):
        before = probe.value_sha(self.old)
        new, union = probe.build_rows(self.bank, self.old)
        self.assertEqual((len(new), len(union)), (2048, 14972))
        self.assertEqual(union[:12924], self.old["corpus"])
        self.assertEqual(probe.value_sha(self.old), before)
        events = probe.new_events(self.bank)
        self.assertEqual([row["event_ids"][0] for row in new],
                         [event["event_id"] for event in events for _ in range(16)])
        self.assertEqual(Counter(row["owner"] for row in new), {event["owner"]: 64 for event in events})
        for index, event in enumerate(events):
            copies = new[index * 16:(index + 1) * 16]
            self.assertEqual([row["frame_copy"] for row in copies], list(range(16)))
            self.assertEqual({row["frame_template"] for row in copies}, set(range(16)))
            for row in copies:
                self.assertEqual((row["context"], row["target"], row["frame_template"]),
                                 md.render_frame(event, 16, 16, row["frame_copy"], 1, 0))
                self.assertEqual((row["session"], row["weight"], row["chat"], row["mask_context"]),
                                 (5, 1.0, False, False))

    def test_source_coverage_excludes_session_six(self):
        events = probe.new_events(self.bank)
        source = {event["event_id"] for event in self.bank["interference"]["events"]
                  if self.bank["schedule"]["across"][event["event_id"]] == 5}
        self.assertEqual({event["event_id"] for event in events}, source)
        self.assertEqual(Counter({event["owner"]: event["colour"] for event in events}.values()),
                         {colour: 8 for colour in md.COLOURS})
        changed = copy.deepcopy(self.bank)
        changed["schedule"]["across"][events[0]["event_id"]] = 6
        with self.assertRaisesRegex(ValueError, "session5"):
            probe.new_events(changed)

    def test_wrong_bank_or_duplicate_events_rejected(self):
        changed = copy.deepcopy(self.bank)
        changed["seed"] = 2
        with self.assertRaisesRegex(ValueError, "seed1"):
            probe.new_events(changed)
        changed = copy.deepcopy(self.bank)
        changed["interference"]["events"].append(probe.new_events(self.bank)[0])
        with self.assertRaises(ValueError):
            probe.new_events(changed)

    def test_old_mask_change_rejected(self):
        old = copy.deepcopy(self.old)
        old["corpus"][0]["mask_context"] = True
        with self.assertRaisesRegex(ValueError, "mask/weight"):
            probe.build_rows(self.bank, old)

    def test_native_cues_unchanged_new_ids_and_no_answer_leak(self):
        cues = probe.build_cues(self.bank, "CPU fixture", Tokenizer())
        self.assertEqual(cues[:1313], md.build_cues(self.bank, "CPU fixture", adjacent_subset=4, tokenizer=Tokenizer()))
        self.assertEqual(len(cues), 1377)
        new = cues[1313:]
        self.assertEqual(Counter(cue["kind"] for cue in new), {"new_frame": 32, "new_bicycle": 32})
        self.assertEqual(len({cue["cue_id"] for cue in cues}), 1377)
        for cue in new:
            self.assertTrue(all(colour not in cue["prompt"].lower() for colour in md.COLOURS))
            self.assertNotIn(cue["a"], cue["prompt"].lower())
            self.assertEqual(cue["candidates"], md.colour_candidates(True))
            self.assertEqual(cue["abstain"], md.ABSTAIN_CANDIDATES)
        work = probe.candidate_work(cues)
        self.assertEqual(work["passes"], 2)
        self.assertGreater(work["scored_prompt_rows"], 2 * 1377)
        self.assertEqual(work["abstention_sequences"], 448)

    def test_snapshot_full_hashes_tokens_counts_no_budget_repadding(self):
        new, union = probe.build_rows(self.bank, self.old)
        control, audit = probe.corpus_snapshot(new, Tokenizer())
        treatment, combined = probe.corpus_snapshot(union, Tokenizer())
        self.assertEqual((control["stats"]["steps"], treatment["stats"]["steps"]), (1536, 11229))
        self.assertEqual(len(audit["row_sha256"]), 2048)
        self.assertEqual(len(combined["encoding_sha256"]), 14972)
        self.assertEqual(combined["row_sha256"][12924:], audit["row_sha256"])
        self.assertEqual(combined["encoding_sha256"][12924:], audit["encoding_sha256"])
        self.assertIsNone(treatment["token_budget"])
        self.assertNotEqual(treatment["sha"], self.old["sha"])
        self.assertNotEqual(treatment["items_sha"], self.old["items_sha"])
        changed = list(reversed(new))
        reordered, _ = probe.corpus_snapshot(changed, Tokenizer())
        self.assertNotEqual(reordered["sha"], control["sha"])
        self.assertEqual(reordered["items_sha"], control["items_sha"])

    def test_truncation_and_empty_supervision_stop(self):
        row = dict(self.old["corpus"][0], target="x" * 513)
        with self.assertRaisesRegex(ValueError, "truncation"):
            probe.corpus_snapshot([row], Tokenizer())
        row["target"] = "x"
        with self.assertRaisesRegex(ValueError, "supervision"):
            probe.corpus_snapshot([row], Tokenizer())

    def test_native_scoring_off_on_and_abstention_measured(self):
        cues = probe.build_cues(self.bank, "CPU fixture", None)
        scorer = md.MockScorer()
        result = probe.evaluate(scorer, cues, "A1_before", {})
        self.assertEqual(result["n_cues"], 1377)
        self.assertEqual(result["measured_work"]["candidate_calls"], 2)
        self.assertEqual(result["measured_work"]["prompt_rows"], result["work"]["scored_prompt_rows"])
        self.assertEqual(result["measured_work"]["candidate_sequences"],
                         result["work"]["candidate_sequences"] + result["work"]["abstention_sequences"])
        self.assertFalse(result["measured_work"]["forward_count_available"])
        self.assertTrue(all("p_abstain" in row["OFF"] and "p_abstain" in row["ON"]
                            for row in result["cues"] if row.get("abstain")))

    def test_real_forward_instrumentation_preserves_output(self):
        scorer = md.MockScorer()
        scorer._forward_last = lambda rows, keep: "unchanged"
        native = scorer.candidate_logprobs

        def candidates(prompts, values):
            self.assertEqual(scorer._forward_last([[1, 2], [3]], 1), "unchanged")
            return native(prompts, values)

        scorer.candidate_logprobs = candidates
        cues = probe.build_cues(self.bank, "CPU fixture", None)[1313:]
        result = probe.evaluate(scorer, cues, "AN", {})
        self.assertEqual(result["measured_work"]["forward_calls"], 2)
        self.assertEqual(result["measured_work"]["padded_input_tokens"], 8)
        self.assertIs(scorer.candidate_logprobs, candidates)

    def test_fit_receipt_checks_skipped_steps_and_original_recipe(self):
        corpus, _ = probe.corpus_snapshot(probe.build_rows(self.bank, self.old)[0], Tokenizer())
        meta = fit_meta(corpus, "/cpu-fixture")
        probe.validate_fit(meta, corpus)
        for key, value in (("steps", 1535), ("tokens", 1), ("rank", 16),
                           ("seed", 1), ("lr", 3e-5), ("measure_only", True)):
            with self.subTest(key=key), self.assertRaises(ValueError):
                probe.validate_fit(dict(meta, **{key: value}), corpus)

    def test_retention_denominator_and_global_bias_not_promoted(self):
        cues = probe.build_cues(self.bank, "CPU fixture", None)
        before = probe.evaluate(md.MockScorer(), cues, "A1_before", {})
        after = copy.deepcopy(before)
        ids = [cue["cue_id"] for cue in cues if cue["kind"] == "new_frame"]
        for row in before["cues"] + after["cues"]:
            if row["cue_id"] in ids:
                row["OFF"] = dict(p_raw={colour: .25 for colour in md.COLOURS}, mass=1)
                row["ON"] = copy.deepcopy(row["OFF"])
        for row in after["cues"]:
            if row["cue_id"] in ids:
                row["ON"] = dict(p_raw={colour: float(colour == "red") for colour in md.COLOURS}, mass=1)
        result = probe.contrast(before, after, ids)
        self.assertIsNone(result["retention_ratio"])
        self.assertEqual(result["delta_effect"], 0)
        self.assertNotIn("passed", result)


class LifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bank, cls.old = bank_fixture(), old_fixture()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.original = self.base / "original"
        self.original.mkdir()
        paths = probe.original_paths(self.original)
        for path in paths.values():
            path.parent.mkdir(parents=True, exist_ok=True)
        paths["a1"].mkdir()
        probe.write(paths["old"], self.old)
        probe.write(paths["bank"], self.bank)
        probe.write(paths["distractor"], dict(text="CPU fixture"))
        self.model = self.base / "model"
        self.model.mkdir()
        probe.write(self.model / "config.json", dict(model_type="qwen2", hidden_size=3584, num_hidden_layers=28))
        self.a1 = paths["a1"]
        self.save_adapter(self.a1, self.old)
        self.pins = self.base / "pins.json"
        probe.write(self.pins, dict(model=probe.tree_hashes(self.model), a1=probe.tree_hashes(self.a1),
                                    distractor_sha256=probe.file_sha(paths["distractor"])))
        self.root = self.base / "run"
        for name, value in (("OLD_SHA", probe.file_sha(paths["old"])),
                            ("BANK_SHA", probe.file_sha(paths["bank"])),
                            ("A1_WEIGHTS_SHA", probe.file_sha(self.a1 / "adapter_model.safetensors"))):
            context = patch.object(probe, name, value)
            context.start()
            self.addCleanup(context.stop)
        context = patch.object(probe, "load_tokenizer", return_value=Tokenizer())
        context.start()
        self.addCleanup(context.stop)
        context = patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "0"})
        context.start()
        self.addCleanup(context.stop)

    def save_adapter(self, path, corpus):
        path.mkdir(parents=True, exist_ok=True)
        probe.write(path / "adapter_config.json", dict(r=8, lora_alpha=16, lora_dropout=.05,
                    bias="none", target_modules=md.LORA_TARGETS))
        (path / "adapter_model.safetensors").write_bytes(b"CPU FIXTURE, NOT MODEL WEIGHTS")
        (path / "DONE").write_text("ok\n")
        probe.write(path / "train_meta.json", fit_meta(corpus, self.model))

    def prepare(self):
        result = probe.prepare(self.root, original_root=self.original, model=self.model, pins=self.pins)
        self.digest = result["manifest_sha256"]
        return probe.read(self.root / "manifest.json")

    def fake_worker(self, command, *, log_path, timeout, device):
        stage = command[command.index("--stage") + 1]
        directory = self.root / "stages" / stage
        directory.mkdir(parents=True)
        pid = 9000 + probe.STAGES.index(stage)
        manifest = probe.read(self.root / "manifest.json")
        common = dict(stage=stage, pid=pid, manifest_sha256=self.digest,
                      job_sha256=probe.file_sha(self.root / f"{stage}.job.json"),
                      starting_state=probe.STARTING_STATE, device=device, worker_seconds=.1)
        if stage.startswith("fit_"):
            corpus = probe.read(self.root / f"{stage[4:]}.json")
            self.save_adapter(directory / "adapter", corpus)
            common.update(train_meta=fit_meta(corpus, self.model), adapter_hashes=probe.tree_hashes(directory / "adapter"))
        else:
            adapter, hashes = probe.artifact(self.root, manifest, stage)
            scorer = md.MockScorer()
            evaluation = probe.evaluate(scorer, probe.read(self.root / "cues.json"), stage,
                                         probe.read(adapter / "train_meta.json"))
            probe.write(directory / "eval.json", evaluation)
            common.update(adapter_hashes=hashes, eval_sha256=probe.file_sha(directory / "eval.json"))
        probe.write(directory / "DONE.json", common)
        probe.write(log_path.with_suffix(".cleanup.json"), dict(pid=pid, owned_group_empty=True,
                    gpu_processes_absent=True, reservation_release_verified=True, device=device))
        return pid

    def execute(self):
        with patch.object(probe.supervisor, "gpu_processes_absent", return_value=True), \
             patch.object(probe.supervisor, "run_worker", side_effect=self.fake_worker) as run:
            result = probe.run(self.root, self.digest, lease_cutoff_unix=time.time() + 10000, allow_gpu=True)
        return result, run

    def test_preparation_immutable_native_hashes_and_row_audits(self):
        manifest = self.prepare()
        self.assertEqual(manifest["starting_state"], probe.STARTING_STATE)
        self.assertEqual(probe.file_sha(self.root / "OLD.json"), probe.OLD_SHA)
        self.assertEqual(probe.verify_prepared(self.root, self.digest), manifest)
        audit = probe.read(self.root / "OLD.audit.json")
        union = probe.read(self.root / "A2.audit.json")
        self.assertEqual(audit["encoding_sha256"], union["encoding_sha256"][:12924])
        with self.assertRaises(FileExistsError):
            self.prepare()

    def test_preparation_rejects_real_weight_pin_mismatch(self):
        with patch.object(probe, "A1_WEIGHTS_SHA", "wrong"), self.assertRaisesRegex(ValueError, "weight pin"):
            self.prepare()
        self.assertFalse((self.root / "manifest.json").exists())
        with self.assertRaises(FileExistsError):
            self.prepare()

    def test_no_gpu_opt_in_and_no_artifact_writes(self):
        with patch.object(probe.supervisor, "run_worker") as run:
            with self.assertRaisesRegex(ValueError, "allow-gpu"):
                probe.run(self.root, "none", lease_cutoff_unix=time.time() + 100)
            with self.assertRaisesRegex(ValueError, "allow-gpu"):
                probe.worker(self.root, "none", "fit_AN")
        self.assertFalse(self.root.exists())
        run.assert_not_called()

    def test_preparation_drift_fails_closed(self):
        self.prepare()
        with (self.root / "AN.json").open("a") as target:
            target.write(" ")
        with self.assertRaisesRegex(ValueError, "prepared file drift"):
            probe.verify_prepared(self.root, self.digest)

    def test_six_fresh_processes_bounded_once_and_replay(self):
        self.prepare()
        finished, runner = self.execute()
        self.assertTrue(finished["completed"])
        self.assertEqual(runner.call_count, 6)
        self.assertEqual([record["stage"] for record in finished["records"]], list(probe.STAGES))
        for call in runner.call_args_list:
            self.assertIn("--allow-gpu", call.args[0])
            self.assertEqual(call.kwargs["device"], "0")
            self.assertLessEqual(call.kwargs["timeout"], 5400 - 45)
        report = probe.reduce(self.root, self.digest, self.root / "report.json")
        self.assertEqual(report["cost"]["new_fit_steps"], 12765)
        self.assertEqual(len(report["cost"]["reads"]), 4)
        self.assertTrue(report["no_update"]["exact_scores_equal"])
        self.assertIsNone(report["native_fact_retention_fraction"])
        self.assertNotIn("passed", report)
        native = md.evaluate_gates(report["native_old_summaries"]["A2"], seed=0)
        self.assertEqual(native, report["native_old_gates"]["A2"])
        self.assertIn("G9_frame_binding", native["failed"])
        probe.reduce(self.root, self.digest, self.root / "replay.json")
        self.assertEqual(probe.file_sha(self.root / "report.json"), probe.file_sha(self.root / "replay.json"))
        with self.assertRaises(FileExistsError):
            probe.reduce(self.root, self.digest, self.root / "report.json")
        with self.assertRaises(FileExistsError), patch.object(probe.supervisor, "run_worker") as execute:
            probe.run(self.root, self.digest, lease_cutoff_unix=time.time() + 100, allow_gpu=True)
        execute.assert_not_called()
        (self.a1 / "adapter_model.safetensors").write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "artifact drift"):
            probe.reduce(self.root, self.digest, self.root / "invalid.json")

    def test_failed_subprocess_has_cost_and_no_retry(self):
        self.prepare()
        with patch.object(probe.supervisor, "gpu_processes_absent", return_value=True), \
             patch.object(probe.supervisor, "run_worker", side_effect=subprocess.TimeoutExpired("fixture", .1)) as execute:
            with self.assertRaises(subprocess.TimeoutExpired):
                probe.run(self.root, self.digest, lease_cutoff_unix=time.time() + 70, allow_gpu=True)
        self.assertEqual(execute.call_count, 1)
        receipt = probe.read(self.root / "RUN_FINISHED.json")
        self.assertFalse(receipt["completed"])
        self.assertEqual(receipt["failure"]["type"], "TimeoutExpired")
        self.assertGreater(receipt["reserved_gpu_seconds"], 0)
        self.assertLess(receipt["records"][0]["timeout_seconds"], 25)
        with self.assertRaisesRegex(ValueError, "incomplete"):
            probe.reduce(self.root, self.digest, self.root / "report.json")

    def test_native_fit_worker_uses_base_not_a1_and_rejects_replay(self):
        self.prepare()
        self.root.joinpath("stages/A1_before").mkdir(parents=True)
        probe.write(self.root / "stages/A1_before/DONE.json", {})
        now = time.time()
        probe.write(self.root / "RUN_STARTED.json", dict(manifest_sha256=self.digest, device="0", started_unix=now,
                    deadline_unix=now + 200, lease_cutoff_unix=now + 200))
        probe.write(self.root / "fit_AN.job.json", dict(manifest_sha256=self.digest, stage="fit_AN",
                    device="0", deadline_unix=now + 100))

        def train(corpus, destination, **kwargs):
            self.assertFalse(Path(destination).exists())
            self.save_adapter(Path(destination), corpus)
            return fit_meta(corpus, self.model)

        with patch.object(md, "train_hf", side_effect=train) as train_call, patch.object(md, "load_scorer") as load:
            probe.worker(self.root, self.digest, "fit_AN", allow_gpu=True)
            self.assertEqual(train_call.call_args.kwargs, dict(rank=8, epochs=3, lr=1e-4, seed=2,
                             bsz=4, max_len=512, model_name=str(self.model)))
            load.assert_not_called()
            with self.assertRaises(FileExistsError):
                probe.worker(self.root, self.digest, "fit_AN", allow_gpu=True)
            self.assertEqual(train_call.call_count, 1)

    def test_native_read_worker_fresh_load_and_cue_hash_check(self):
        self.prepare()
        now = time.time()
        probe.write(self.root / "RUN_STARTED.json", dict(manifest_sha256=self.digest, device="0", started_unix=now,
                    deadline_unix=now + 200, lease_cutoff_unix=now + 200))
        probe.write(self.root / "A1_before.job.json", dict(manifest_sha256=self.digest, stage="A1_before",
                    device="0", deadline_unix=now + 100))
        scorer = md.MockScorer()
        scorer.tok = Tokenizer()
        with patch.object(md, "MODEL_NAME", str(self.model)), patch.object(md, "load_scorer", return_value=scorer) as load:
            probe.worker(self.root, self.digest, "A1_before", allow_gpu=True)
        load.assert_called_once_with("hf", str(self.a1), batch_size=16, seed=0)
        self.assertEqual(probe.read(self.root / "stages/A1_before/eval.json")["n_cues"], 1377)

    def test_supervisor_cpu_subprocess_timeout_cleanup(self):
        log = self.base / "cpu.log"
        with patch.object(probe.supervisor, "gpu_processes_absent", return_value=True):
            with self.assertRaises(subprocess.TimeoutExpired):
                probe.supervisor.run_worker([sys.executable, "-B", "-c", "import time; time.sleep(5)"],
                                            log_path=log, timeout=.05, device="0")
        self.assertTrue(probe.read(log.with_suffix(".cleanup.json"))["reservation_release_verified"])


if __name__ == "__main__":
    unittest.main()
