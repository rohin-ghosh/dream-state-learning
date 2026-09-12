"""Synthetic CPU source joins through the actual formation producer and V3 encoder."""
from contextlib import contextmanager
from dataclasses import replace
import copy
import json
import unittest
from unittest.mock import patch

import test_parent_material_diagnostic as fixtures
from organism_v6 import parent_material_diagnostic as formation
from organism_v6 import parent_wake_material as exporter
from organism_v6 import preschool_reasoning as policy, train_adapter_v3 as trainer


class Tokenizer(fixtures.FixtureTokenizer):
    eos_token_id = 999999


class NativeFixtureGym(fixtures.FixtureGym):
    def _item(self, family, seed):
        return self, dict(question=f"Submit north for {family}/{seed}.",
                          answer="SEALED_NEVER_IN_TRAINING", seed=seed, family=family)

    def score_answer(self, answer, entry):
        return 1.0 if entry["family"] == "mini_sudoku" and entry["seed"] == self.solved_seed else .5


class WakeExporterTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.DiagnosticTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root = self.fixture.root
        self.gym = NativeFixtureGym()
        self.gym.solved_seed = next(int(episode.rsplit("/", 1)[1]) for episode in
            self.gym.training_schedule(64, 6101) if episode.startswith("rg/mini_sudoku/"))
        self.lesson = self.make_arm("lesson")
        self.sham = self.make_arm("sham")
        self.out = self.root / "export"
        self.tokenizer = Tokenizer()

    def make_arm(self, mode, *, name=None, wake="\nACT: north\nACT: north\n\n"):
        model = fixtures.FixtureModel(str(self.fixture.model_dir))
        model.wake = wake
        model.note = "NOTE: continue solving, not a post-outcome record"

        @contextmanager
        def backend(path):
            yield model

        root = self.root / (name or mode)
        with patch.object(formation, "DiagnosticDriver", fixtures.OneTickDriver):
            formation.run(replace(self.fixture.config, out=str(root), mode=mode),
                          gym=self.gym, backend_factory=backend)
        return root

    def export(self, **kwargs):
        return exporter.export_pair(self.lesson, self.sham, kwargs.pop("output_dir", self.out),
                                    count=kwargs.pop("count", 4), selection=kwargs.pop("selection", "measured"),
                                    tokenizer=kwargs.pop("tokenizer", self.tokenizer), **kwargs)

    def read(self, path):
        return json.loads(path.read_bytes())

    def rewrite(self, root, filename, rows):
        path = root / filename
        path.chmod(0o644)
        if filename.endswith(".jsonl"):
            path.write_bytes(b"".join(policy._encoded(row) for row in rows))
        else:
            path.write_bytes(policy._encoded(rows))
        path.chmod(0o444)
        manifest = self.read(root / "artifact_hashes.json")
        manifest["files"][filename] = formation._hash(path)
        target = root / "artifact_hashes.json"
        target.chmod(0o644)
        target.write_bytes(policy._encoded(manifest))
        target.chmod(0o444)

    def rows(self, root, filename="ledger.jsonl"):
        return [json.loads(line) for line in (root / filename).read_bytes().splitlines()]

    def test_exact_raw_join_without_note_or_first_person_gate(self):
        before = {root: {path.name: path.read_bytes() for path in root.iterdir()}
                  for root in (self.lesson, self.sham)}
        with patch.object(policy, "judge_record", side_effect=AssertionError("no NOTE content gate")), \
                patch.object(policy, "_judge_source", side_effect=AssertionError("no NOTE source gate")), \
                patch.object(trainer, "main", side_effect=AssertionError("no training")):
            result = self.export()
        self.assertEqual(result["status"], "READY")
        self.assertEqual(result["selection"]["selected_episodes"], self.gym.training_schedule(64, 6101)[:4])
        for mode in ("lesson", "sham"):
            corpus = self.read(self.out / f"{mode}.json")["corpus"]
            sources = self.read(self.out / f"{mode}_source_map.json")["rows"]
            self.assertEqual(len(corpus), 4)
            for item, linked in zip(corpus, sources):
                self.assertEqual(item["spans"][1], ["\nACT: north\nACT: north\n\n", True, "raw_child_wake"])
                self.assertEqual(linked["source"]["raw_output"], item["spans"][1][0])
                self.assertEqual([entry["act"]["action"] for entry in linked["source"]["events"]], ["north", "north"])
                execution_ids = [entry["act"]["execution_id"] for entry in linked["source"]["events"]]
                self.assertTrue(execution_ids[0].endswith("#t1a1"))
                self.assertTrue(execution_ids[1].endswith("#t1a2"))
                self.assertNotEqual(execution_ids[0], execution_ids[1])
                self.assertNotIn("SEALED_NEVER_IN_TRAINING", str(item))
        for root in before:
            self.assertEqual(before[root], {path.name: path.read_bytes() for path in root.iterdir()})

    def test_teacher_removed_not_same_event_score_appended(self):
        self.export()
        payloads = exporter.replay._payloads([policy.lesson_block(mode, 0) for mode in ("lesson", "sham")])
        for mode in ("lesson", "sham"):
            rows = self.read(self.out / f"{mode}_source_map.json")["rows"]
            for row in rows:
                self.assertIn(policy.lesson_block(mode, 0), row["source"]["original_prompt"])
                self.assertFalse(exporter.replay._echo(row["context"], payloads))
                self.assertIn(self.gym.birth_prompt().strip(), row["context"])
                self.assertIn("LAST OUTCOME: (no actions taken yet)", row["context"])
                self.assertNotIn("attempt 1: verifier score", row["context"])
                self.assertNotIn("0.50", row["context"])
                for event in row["source"]["events"]:
                    self.assertIn("verifier score", event["act"]["outcome"])
                encoded = trainer.encode_item_segments(row["item"], self.tokenizer, 4096, chat_template=False)[0]
                context = self.tokenizer.encode(row["rendered_context"])
                self.assertEqual(encoded.labels[:len(context)], [-100] * len(context))
                self.assertEqual(encoded.labels[len(context):],
                    self.tokenizer.encode(row["source"]["raw_output"]) + [self.tokenizer.eos_token_id])

    def test_clipped_ledger_recovers_full_actual_output_without_rewriting(self):
        raw = "x" * 2200 + "\nACT: north\nACT: north\n"
        self.lesson = self.make_arm("lesson", name="clipped", wake=raw)
        result = self.export(max_len=8192)
        self.assertEqual(result["status"], "READY")
        self.assertEqual(result["arms"]["lesson"]["ledger_clipped_chunks"], 64)
        source = self.read(self.out / "lesson_source_map.json")["rows"][0]["source"]
        self.assertEqual(len(source["ledger_note"]), 2000)
        self.assertEqual(source["raw_output"], raw)
        self.assertEqual(self.read(self.out / "lesson.json")["corpus"][0]["spans"][1][0], raw)

    def test_unjoined_raw_output_tamper_rejected_even_when_inventory_resealed(self):
        events = self.rows(self.lesson, "generations.jsonl")
        next(event for event in events if event["kind"] == "output")["text"] += "bad"
        self.rewrite(self.lesson, "generations.jsonl", events)
        with self.assertRaisesRegex(ValueError, "generation text/hash"):
            self.export()
        self.assertFalse(self.out.exists())

    def test_duplicate_repeated_action_identity_rejected(self):
        rows = self.rows(self.lesson)
        acts = [row for row in rows if row["kind"] == "act"]
        acts[1]["execution_id"] = acts[0]["execution_id"]
        self.rewrite(self.lesson, "ledger.jsonl", rows)
        with self.assertRaisesRegex(ValueError, "duplicate execution"):
            self.export()

    def test_missing_repeated_action_is_not_membership_join(self):
        rows = self.rows(self.lesson)
        first_action = next(row for row in rows if row["kind"] == "act")
        first_action["action"] = "east"
        self.rewrite(self.lesson, "ledger.jsonl", rows)
        with self.assertRaisesRegex(ValueError, "multiplicity/order"):
            self.export()

    def test_wrong_tick_and_occurrence_cannot_join(self):
        rows = self.rows(self.lesson)
        next(row for row in rows if row["kind"] == "act")["occurrence_index"] += 1
        self.rewrite(self.lesson, "ledger.jsonl", rows)
        with self.assertRaisesRegex(ValueError, "occurrence mismatch"):
            self.export()

    def test_teacher_echo_target_produces_explicit_paired_skip(self):
        teacher_echo = policy.LESSON_EXAMPLES[0] + "\nACT: north\nACT: north"
        self.lesson = self.make_arm("lesson", name="echo", wake=teacher_echo)
        result = self.export()
        self.assertEqual(result["status"], "PAIRED_SKIP")
        self.assertEqual(result["arms"]["lesson"]["eligible_unique_episodes"], 0)
        self.assertEqual(result["arms"]["lesson"]["rejected"][0]["reason"], "teacher-echo-target")
        for mode in ("lesson", "sham"):
            self.assertEqual(self.read(self.out / f"{mode}.json")["corpus"], [])

    def test_teacher_echo_in_context_rejects_without_deleting_child_history(self):
        arm = exporter.source_arm(self.lesson, "lesson")
        chunk = copy.deepcopy(arm["chunks"][0])
        chunk["original_prompt"] += policy.LESSON_EXAMPLES[0]
        result, reason = exporter.encode_candidate(chunk, arm, exporter.replay._payloads([arm["teacher"]["text"]]),
                                                  self.tokenizer, 4096)
        self.assertIsNone(result)
        self.assertEqual(reason, "teacher-echo-context")

    def test_single_successful_mini_sudoku_is_not_padded_to_count(self):
        result = self.export(count=2, selection="accepted", families=["mini_sudoku"])
        self.assertEqual(result["status"], "PAIRED_SKIP")
        self.assertEqual(result["selection"]["available_paired_episodes"], 1)
        for arm in result["arms"].values():
            self.assertEqual(arm["accepted_mini_sudoku_episodes"], 1)
            self.assertEqual(arm["selected_examples"], 0)

    def test_token_shortage_no_truncation_or_partial_fit(self):
        result = self.export(max_len=16)
        self.assertEqual(result["status"], "PAIRED_SKIP")
        self.assertEqual(result["arms"]["lesson"]["rejected"][0]["reason"], "over-token-budget-no-truncation")
        self.assertEqual(result["arms"]["sham"]["target_tokens"], 0)

    def test_output_conflict_and_source_overlap(self):
        self.export()
        before = (self.out / "artifact_hashes.json").read_bytes()
        with self.assertRaises(FileExistsError):
            self.export()
        self.assertEqual(before, (self.out / "artifact_hashes.json").read_bytes())
        for path in self.out.iterdir():
            self.assertEqual(path.stat().st_mode & 0o222, 0)
        with self.assertRaisesRegex(ValueError, "overlap"):
            self.export(output_dir=self.lesson / "new")

    def test_failed_or_drifted_original_rejects(self):
        result = self.read(self.lesson / "results.json")
        result["status"] = "INCOMPLETE"
        self.rewrite(self.lesson, "results.json", result)
        with self.assertRaisesRegex(ValueError, "incomplete original"):
            self.export()

    def test_tokenizer_rendering_mismatch_rejects(self):
        class WrongTokenizer(Tokenizer):
            def apply_chat_template(self, *args, **kwargs):
                return "wrong-render"
        with self.assertRaisesRegex(ValueError, "tokenizer/rendering"):
            self.export(tokenizer=WrongTokenizer())

    def test_source_changes_during_export_reject_before_output(self):
        real = exporter.encode_candidate
        changed = []
        def mutate(*args, **kwargs):
            result = real(*args, **kwargs)
            if not changed:
                changed.append(True)
                config = self.read(self.lesson / "config.json")
                config["unexpected"] = "source changed"
                self.rewrite(self.lesson, "config.json", config)
            return result
        with patch.object(exporter, "encode_candidate", side_effect=mutate):
            with self.assertRaisesRegex(ValueError, "source changed during export"):
                self.export()
        self.assertFalse(self.out.exists())

    def test_original_generation_seed_cannot_be_reassigned(self):
        events = self.rows(self.lesson, "generations.jsonl")
        request = next(event for event in events if event["kind"] == "request" and event["max_tokens"] == 400)
        old_seed = request["seed"]
        request["seed"] += 1
        self.rewrite(self.lesson, "generations.jsonl", events)
        rows = self.rows(self.lesson)
        for row in rows:
            receipt = row.get("generation", {})
            if receipt.get("seed") == old_seed and receipt.get("prompt_sha256") == request["prompt_sha256"]:
                receipt["seed"] = request["seed"]
        self.rewrite(self.lesson, "ledger.jsonl", rows)
        with self.assertRaisesRegex(ValueError, "tick/seed"):
            self.export()

    def test_selection_is_explicit_and_bad_bounds_reject(self):
        for kwargs in (dict(count=0), dict(count=True), dict(count=65), dict(selection="note"),
                       dict(max_len=0), dict(families=["n_queens"])):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.export(**kwargs)


if __name__ == "__main__":
    unittest.main()
