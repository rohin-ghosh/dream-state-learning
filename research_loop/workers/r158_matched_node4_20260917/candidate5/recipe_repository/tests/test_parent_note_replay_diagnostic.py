"""Synthetic CPU source generations and replay; never real GPU evidence."""
from contextlib import contextmanager
from dataclasses import replace
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
import unittest
from unittest.mock import patch

from organism_v6 import parent_note_replay_diagnostic as replay
from organism_v6 import parent_material_diagnostic as formation
from organism_v6 import parent_material_write as writer
from organism_v6 import preschool_reasoning as policy
import test_parent_material_diagnostic as fixtures


class SourceModel(fixtures.FixtureModel):
    def __init__(self, path, actions=5):
        super().__init__(path)
        self.actions = actions
        self.counter = 0

    def batch(self, prompts, max_tokens=400, seeds=None, temperature=.7):
        outputs = []
        for prompt in prompts:
            if max_tokens == 100:
                outputs.append("NOTE: Continue the puzzle. ACT: guess again")
            else:
                actions = [f"ACT: source-action-{self.counter + index}" for index in range(self.actions)]
                self.counter += self.actions
                outputs.append("\n".join(actions))
        return outputs


class ReplayModel(fixtures.FixtureModel):
    def __init__(self, path):
        super().__init__(path)
        self.calls = []
        self.override = None
        self.truncate_batch = False

    def batch(self, prompts, max_tokens=400, seeds=None, temperature=.7):
        self.calls.append(dict(prompts=prompts, max_tokens=max_tokens, seeds=seeds, temperature=temperature))
        outputs = []
        for prompt in prompts:
            action = json.loads(re.findall(r"^ACT submitted: (.+)$", prompt, re.M)[-1])
            score = re.findall(r"^Displayed verifier score: (.+)$", prompt, re.M)[-1]
            text = f'I submitted "{action}"; the score was {score}.'
            outputs.append(self.override(text) if self.override else text)
        return outputs[:-1] if self.truncate_batch else outputs


class ReplayTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.DiagnosticTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root = self.fixture.root
        self.lesson = self.make_source("lesson")
        self.sham = self.make_source("sham")
        self.output = self.root / "replay"
        self.model = ReplayModel(str(self.fixture.model_dir))
        self.loaded = 0
        self.closed = 0

    def make_source(self, mode, actions=5, name=None):
        model = SourceModel(str(self.fixture.model_dir), actions=actions)

        @contextmanager
        def backend(model_path):
            yield model

        config = replace(self.fixture.config, mode=mode, out=str(self.root / (name or mode)))
        with patch.object(formation, "DiagnosticDriver", fixtures.OneTickDriver):
            result = formation.run(config, gym=self.fixture.gym, backend_factory=backend)
        self.assertEqual(result["n_unique_grounded_records"], 0)
        return Path(config.out)

    @contextmanager
    def backend(self, model_path):
        self.assertEqual(model_path, str(self.fixture.model_dir))
        self.loaded += 1
        try:
            yield self.model
        finally:
            self.closed += 1

    def run_replay(self):
        return replay.run(self.lesson, self.sham, self.output, allow_gpu=True, backend_factory=self.backend)

    @staticmethod
    def read(path):
        return writer._read(path)

    @staticmethod
    def rewrite(path, value):
        path.chmod(0o644)
        path.write_bytes(policy._encoded(value))

    def reseal(self, root):
        path = root / "artifact_hashes.json"
        manifest = self.read(path)
        manifest["files"] = {name: formation._hash(root / name) for name in manifest["files"]}
        self.rewrite(path, manifest)

    def test_real_source_join_selection_coaching_and_revalidation(self):
        before = {str(path): formation._hash(path) for root in (self.lesson, self.sham) for path in root.iterdir()}
        with patch.object(formation.batch_loop, "run_episodes_batch", side_effect=AssertionError("no new childhood")), \
                patch.object(fixtures.FixtureGym, "score_answer", side_effect=AssertionError("no new world measurements")):
            result = self.run_replay()
        self.assertEqual(result["status"], "COMPLETE")
        self.assertEqual(result["total_note_requests"], 512)
        self.assertEqual(len(self.model.calls), 64)
        self.assertEqual((self.loaded, self.closed), (1, 1))
        for arm, root in (("lesson", self.lesson), ("sham", self.sham)):
            sources = self.read(self.output / (arm + "_sources.json"))["sources"]
            _, ledger = policy._lines((root / "ledger.jsonl").read_bytes())
            selected = []
            counts = {}
            for index, row in enumerate(ledger):
                if row["kind"] == "act":
                    episode = row["episode_id"]
                    if counts.get(episode, 0) < 4:
                        selected.append(index)
                        counts[episode] = counts.get(episode, 0) + 1
            self.assertEqual([source["act_line"] for source in sources], selected)
            self.assertEqual(len(sources), 256)
            self.assertEqual(result["arms"][arm]["old_content_eligible"], 0)
            self.assertEqual(result["arms"][arm]["faithful"], 256)
            for source in sources:
                suffix = "\n\n" + policy.outcome_block(policy.facts_from_act(source["source_act"]), "NOTE_AFTER")
                self.assertEqual(source["replay_prompt"], source["original_prompt"][:-len(suffix)] + "\n\n" + replay.COACH + suffix)
                self.assertEqual(source["replay_prompt"].count(replay.COACH), 1)
            calls = self.model.calls[:32] if arm == "lesson" else self.model.calls[32:]
            self.assertEqual([seed for call in calls for seed in call["seeds"]], [source["original_seed"] for source in sources])
        for call in self.model.calls:
            self.assertEqual(len(call["prompts"]), 8)
            self.assertEqual((call["max_tokens"], call["temperature"]), (100, .7))
        checked = replay.validate_replay(self.output, tokenizer=self.model.tok)
        self.assertEqual(checked["results"], result)
        self.assertEqual(len(checked["records"]), 512)
        self.assertEqual(before, {name: formation._hash(Path(name)) for name in before})
        self.assertFalse((self.output / "ledger.jsonl").exists())
        self.assertFalse((self.output / "corpus.json").exists())
        with self.assertRaises((ValueError, KeyError)):
            writer._formation_snapshot(self.output)

    def test_raw_prefixes_preserved_and_default_judge_not_relaxed(self):
        self.model.override = lambda text: "NOTE: ACT: solve again\n" + text + "\n"
        self.run_replay()
        checked = replay.validate_replay(self.output, tokenizer=self.model.tok)
        row = checked["records"][0]
        self.assertTrue(row["text"].startswith("NOTE: ACT:"))
        self.assertTrue(row["text"].endswith("\n"))
        facts = policy.facts_from_act(checked["sources"]["lesson"]["sources"][0]["source_act"])
        self.assertEqual(row["judgment"]["judge_record"], policy.judge_record(row["text"], facts))
        self.assertFalse(row["judgment"]["faithful"])

    def test_complete_coach_and_teacher_sentence_echo_excluded(self):
        source = replay.inspect_source(self.lesson, "lesson")["sources"][0]
        text = f'I submitted "{source["source_act"]["action"]}"; the score was 0.50.'
        teacher = policy.lesson_block("lesson", 0)
        self.assertTrue(replay._judgment(text, source, teacher)["faithful"])
        for echoed in (replay.COACH, replay.COACH.split(". ")[1] + ".", policy.LESSON_PARAGRAPH.split(". ")[0] + "."):
            judgment = replay._judgment(text + " " + echoed, source, teacher)
            self.assertTrue(judgment["delivered_text_echo"])
            self.assertFalse(judgment["faithful"])

    def test_exact256_required_before_backend_no_backfill(self):
        short = self.make_source("sham", actions=3, name="short")
        with self.assertRaisesRegex(ValueError, "256 per arm"):
            replay.run(self.lesson, short, self.output, allow_gpu=True, backend_factory=self.backend)
        self.assertEqual(self.loaded, 0)
        self.assertFalse(self.output.exists())

    def test_source_provenance_corruption_rejects_even_when_old_content_bad(self):
        path = self.lesson / "ledger.jsonl"
        _, rows = policy._lines(path.read_bytes())
        row = next(row for row in rows if row["kind"] == "note_after")
        row["action"] = "forged source"
        path.chmod(0o644)
        path.write_bytes(b"".join(policy._encoded(row) for row in rows))
        self.reseal(self.lesson)
        with self.assertRaisesRegex(ValueError, "provenance mismatch"):
            self.run_replay()
        self.assertFalse(self.model.calls)

    def test_actual_wake_trace_tamper_rejected(self):
        path = self.lesson / "generations.jsonl"
        _, rows = policy._lines(path.read_bytes())
        next(row for row in rows if row["kind"] == "output")["text"] = "ACT: invented"
        path.chmod(0o644)
        path.write_bytes(b"".join(policy._encoded(row) for row in rows))
        self.reseal(self.lesson)
        with self.assertRaisesRegex(ValueError, "generation source mismatch"):
            self.run_replay()
        self.assertEqual(self.loaded, 0)

    def test_original_producer_can_differ_but_recorded_bytes_must_survive(self):
        historical = self.root / "historical/organism_v6"
        historical.mkdir(parents=True)
        hashes = {}
        for name in formation._sources():
            path = historical / Path(name).name
            shutil.copy2(name, path)
            if path.name == "parent_material_diagnostic.py":
                path.write_bytes(path.read_bytes() + b"\n# Synthetic historical producer version\n")
            hashes[str(path)] = formation._hash(path)
        with patch.object(formation, "_sources", return_value=hashes):
            historical_source = self.make_source("lesson", name="old_lesson")
        self.assertEqual(len(replay.inspect_source(historical_source, "lesson")["sources"]), 256)
        next(historical.glob("parent_material_diagnostic.py")).write_text("changed")
        with self.assertRaisesRegex(ValueError, "original producer bytes changed"):
            replay.inspect_source(historical_source, "lesson")

    def test_failed_backend_output_preserves_raw_partial_no_retry(self):
        self.model.truncate_batch = True
        with self.assertRaisesRegex(ValueError, "cardinality"):
            self.run_replay()
        self.assertEqual(len(self.model.calls), 1)
        self.assertEqual(self.closed, 1)
        _, trace = policy._lines((self.output / "generations.jsonl").read_bytes())
        self.assertEqual(len(trace[-1]["outputs"]), 7)
        self.assertTrue((self.output / "failure.json").exists())
        with self.assertRaisesRegex(ValueError, "failed"):
            replay.validate_replay(self.output, tokenizer=self.model.tok)

    def test_token_context_preflight_fails_without_generation_or_truncation(self):
        original = self.model.tok.apply_chat_template
        self.model.tok.apply_chat_template = lambda messages, **kwargs: (
            "x" * 17000 if replay.COACH in messages[0]["content"] else original(messages, **kwargs))
        with self.assertRaisesRegex(ValueError, "no truncation"):
            self.run_replay()
        self.assertFalse(self.model.calls)
        self.assertEqual(self.closed, 1)

    def test_revalidation_detects_new_record_tamper_even_if_resealed(self):
        self.run_replay()
        path = self.output / "records.jsonl"
        _, rows = policy._lines(path.read_bytes())
        rows[0]["text"] = "invented replacement"
        path.chmod(0o644)
        path.write_bytes(b"".join(policy._encoded(row) for row in rows))
        self.reseal(self.output)
        with self.assertRaisesRegex(ValueError, "output/source/judgment"):
            replay.validate_replay(self.output, tokenizer=self.model.tok)

    def test_explicit_opt_in_and_no_overwrite(self):
        with self.assertRaisesRegex(ValueError, "opt-in"):
            replay.run(self.lesson, self.sham, self.output, backend_factory=self.backend)
        self.assertEqual(self.loaded, 0)
        self.output.mkdir()
        with self.assertRaises(FileExistsError):
            self.run_replay()

    def test_controller_uses_one_hour_owned_worker_and_external_log(self):
        log = self.root / "replay.log"
        def worker(command, **kwargs):
            self.assertEqual(kwargs["timeout"], 3600)
            self.assertEqual(kwargs["device"], "1")
            self.assertEqual(kwargs["log_path"], log)
            self.assertIn("--worker", command)
            self.output.mkdir()
            formation._write(self.output / "results.json", dict(synthetic_cpu=True))
            return 123
        with patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "1"}), \
                patch.object(replay.neutral, "gpu_processes_absent", return_value=True), \
                patch.object(replay.neutral, "run_worker", side_effect=worker):
            replay.main(["--lesson-root", str(self.lesson), "--sham-root", str(self.sham),
                         "--out", str(self.output), "--log", str(log), "--execute"])


if __name__ == "__main__":
    unittest.main()
