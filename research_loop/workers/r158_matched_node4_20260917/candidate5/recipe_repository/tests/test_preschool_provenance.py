"""New dependency-free preschool provenance regressions; no model or GPU calls."""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from organism_v6 import preschool
from organism_v6.batch_loop import run_episodes_batch
from organism_v6.gym_backend import Episode
from organism_v6.ledger import Ledger


def execution(index=0, text=None):
    before, after = 1000 + index, 800 + index
    reduction = round(100 * (before - after) / before, 1)
    outcome = f"instructions {before} -> {after} ({reduction}% reduction)"
    action = dict(kind="act", execution_id=f"event-{index}",
                  episode_id=f"train/item_{index}", tick=index + 1,
                  action="-mem2reg", outcome=outcome)
    record = dict(action, kind="note_after", **preschool.parse_outcome(outcome))
    record["text"] = text or f"I ran -mem2reg. Instructions went from {before} to {after}, a {reduction}% reduction."
    return action, record


class StubGym:
    name = "compiler"
    def birth_prompt(self):
        return "frozen birth"

    def evaluate(self, episode, action):
        return .2, "instructions 1000 -> 800 (20.0% reduction)"


class SlotModel:
    def __init__(self, fail_at=None):
        self.fail_at = fail_at

    def batch(self, prompts, **kwargs):
        outputs = []
        for prompt in prompts:
            is_record = prompt.rstrip().endswith("NOTE_AFTER:")
            if self.fail_at == "wake" or self.fail_at == "record" and is_record:
                raise RuntimeError("injected generation interruption")
            outputs.append(execution()[1]["text"] if is_record else "ACT: -mem2reg")
        return outputs


class PreschoolProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory(prefix="preschool_provenance_", dir="/tmp")
        self.addCleanup(self.scratch.cleanup)
        self.life = Path(self.scratch.name)
        self.sleep = self.life / "sleep_0032"
        self.sleep.mkdir()

    def gate(self, rows, mode="enforce", sleep=None):
        return preschool.gate_sleep(rows, str(self.life), str(sleep or self.sleep), mode)

    def test_orphan_is_rejected_with_default_threshold(self):
        action, record = execution()
        result = self.gate([record])
        self.assertEqual(result["rejection_families"], {"provenance-orphan": 1})
        self.assertEqual(result["n_admitted_total"], 0)
        self.assertEqual(result["min_items"], 64)
        self.assertTrue(result["training_skipped"])

    def test_duplicate_and_conflicting_acts_are_rejected(self):
        for conflicting in (False, True):
            with self.subTest(conflicting=conflicting):
                action, record = execution()
                other = dict(action)
                if conflicting:
                    other["outcome"] = "instructions 1000 -> 1000 (0.0% reduction)"
                self.assertEqual(preschool._record_provenance(record,
                                 {"event-0": [action, other]}, {"event-0": [record]}, []),
                                 "provenance-ambiguous-execution")
        result = self.gate([action, other, record])
        self.assertEqual(result["n_admitted_total"], 0)

    def test_duplicate_notes_are_rejected(self):
        action, record = execution()
        result = self.gate([action, record, dict(record)])
        self.assertEqual(result["rejection_families"], {"provenance-ambiguous-record": 2})
        self.assertEqual(result["n_admitted_total"], 0)

    def test_forged_join_and_measurements_fail_closed(self):
        for field, value in (("episode_id", "other"), ("tick", 999),
                             ("action", "-sroa"), ("outcome", "forged"),
                             ("status", "failure"), ("before", 777),
                             ("after", 777), ("reduction", 99)):
            with self.subTest(field=field):
                action, record = execution()
                record[field] = value
                self.assertEqual(preschool._record_provenance(record,
                                 {"event-0": [action]}, {"event-0": [record]}, []),
                                 "provenance-mismatch-" + field)
        action, record = execution()
        del record["before"]
        result = self.gate([action, record])
        self.assertEqual(result["n_admitted_total"], 0)

    def test_actual_matching_record_accepted_but_no_forced_update(self):
        action, record = execution()
        result = self.gate([action, record])
        self.assertEqual(result["n_admitted_new"], 1)
        self.assertTrue(result["training_skipped"])
        corpus = json.loads((self.sleep / "corpus.json").read_text())["corpus"]
        self.assertEqual(corpus, [preschool.RECORD_ITEM.format(eid=record["episode_id"], text=record["text"])])

    def test_sixty_four_actual_records_reach_unchanged_threshold(self):
        rows = [row for index in range(64) for row in execution(index)]
        result = self.gate(rows)
        self.assertEqual(result["n_admitted_new"], 64)
        self.assertEqual(result["record_items"], 64)
        self.assertFalse(result["training_skipped"])

    def test_delivered_example_echo_rejected_even_with_matching_act(self):
        preschool.deliver_lesson(str(self.life), "lesson", 0)
        action, record = execution()
        action["action"] = record["action"] = "-mem2reg and -sroa"
        record["text"] = preschool.LESSON_EXAMPLES[0]
        result = self.gate([action, record])
        self.assertEqual(result["rejection_families"], {"provenance-lesson-echo": 1})
        self.assertEqual(result["n_admitted_total"], 0)

    def test_normalized_example_and_refresher_echo_rejected(self):
        preschool.deliver_lesson(str(self.life), "lesson", 0)
        preschool.deliver_lesson(str(self.life), "lesson", 1)
        payloads = preschool._delivered_payloads(str(self.life))
        for text in (preschool.LESSON_EXAMPLES[0], preschool.REFRESHER_EXAMPLES[0]):
            with self.subTest(text=text):
                action, record = execution()
                record["text"] = "My note: " + text.upper().replace(",", "").replace(" ", "  ")
                self.assertEqual(preschool._record_provenance(record,
                                 {"event-0": [action]}, {"event-0": [record]}, payloads),
                                 "provenance-lesson-echo")

    def test_delivered_paragraph_echo_and_full_lesson_rejected(self):
        delivered = preschool.deliver_lesson(str(self.life), "lesson", 0)
        payloads = preschool._delivered_payloads(str(self.life))
        for copied in (delivered, preschool.LESSON_PARAGRAPH):
            with self.subTest(copied=copied):
                action, record = execution()
                record["text"] += "\n" + copied
                self.assertEqual(preschool._record_provenance(record,
                                 {"event-0": [action]}, {"event-0": [record]}, payloads),
                                 "provenance-lesson-echo")

    def test_shared_words_not_rejected_and_shadow_bytes_preserved(self):
        preschool.deliver_lesson(str(self.life), "lesson", 0)
        action, record = execution()
        legacy = '{"corpus": ["legacy harness text"]}\n'
        (self.sleep / "corpus.json").write_text(legacy)
        result = self.gate([action, record], "shadow")
        self.assertEqual(result["n_admitted_new"], 1)
        self.assertEqual((self.sleep / "corpus.json").read_text(), legacy)

    def test_shadow_exposes_orphan_reason_without_changing_corpus(self):
        action, record = execution()
        legacy = '{"corpus": ["untouched"]}'
        (self.sleep / "corpus.json").write_text(legacy)
        result = self.gate([record], "shadow")
        self.assertIn("provenance-orphan", result["rejection_families"])
        self.assertEqual((self.sleep / "corpus.json").read_text(), legacy)

    def test_cumulative_admission_is_rechecked(self):
        action, record = execution()
        self.gate([action, record])
        later = self.life / "sleep_0064"
        later.mkdir()
        result = self.gate([action, record, dict(action)], sleep=later)
        self.assertEqual(result["n_admitted_total"], 0)
        self.assertEqual(result["prior_provenance_rejections"], {"provenance-ambiguous-execution": 1})

    def test_malformed_delivery_fails_closed(self):
        (self.life / "lesson_deliveries.jsonl").write_text('{"mode":"lesson"}\n')
        with self.assertRaises(RuntimeError):
            self.gate(list(execution()))

    def test_prior_echo_cannot_survive_new_delivery_receipt(self):
        action, record = execution()
        first = self.gate([action, record])
        self.assertEqual(first["n_admitted_total"], 1)
        with patch.object(preschool, "LESSON_EXAMPLES", (record["text"],)):
            preschool.deliver_lesson(str(self.life), "lesson", 0)
        later = self.life / "sleep_0064"
        later.mkdir()
        result = self.gate([action, record], sleep=later)
        self.assertEqual(result["n_admitted_total"], 0)
        self.assertEqual(result["prior_provenance_rejections"], {"provenance-lesson-echo": 1})
        self.assertEqual(json.loads((later / "corpus.json").read_text())["corpus"], [])

    def probe(self, adapter=None, **changes):
        arguments = dict(model=object(), gym=StubGym(), life=str(self.life), when="post",
                         episode_index=32, sleep_index=1, panel=["held/out"],
                         budget_ticks=16, log=None, adapter_path=adapter,
                         open_base=lambda: object(), close_base=lambda base: object())
        arguments.update(changes)
        return preschool.neutral_probe(**arguments)

    def fake_probe(self, *args, **kwargs):
        adapter = args[9]
        return dict(program="held/out", adapter=adapter, adapter_sha256=preschool._adapter_sha(adapter),
                    best_score=0, n_acts=1, n_executions_numeric=1, n_scratchpads=1,
                    articulation_hi=0, articulation_lo=0, scratchpads=[], slot={}, ledger="separate.jsonl")

    def test_cache_roundtrip_and_requested_config_mismatch(self):
        with patch.object(preschool, "neutral_probe_run", side_effect=self.fake_probe) as runner:
            first, model = self.probe()
            cached, model = self.probe()
            self.assertEqual(first, cached)
            self.assertEqual(runner.call_count, 1)
            for changes in ({"budget_ticks": 17}, {"max_tokens": 101},
                            {"panel": ["other/panel"]}, {"sleep_index": 2}):
                with self.subTest(changes=changes), self.assertRaises(RuntimeError):
                    self.probe(**changes)

    def test_cache_rejects_changed_weights_and_adapter_config(self):
        adapter = self.life / "adapter"
        adapter.mkdir()
        weights = adapter / "adapter_model.safetensors"
        config = adapter / "adapter_config.json"
        weights.write_bytes(b"fixture weights, not a model")
        config.write_text('{"r":8}')
        with patch.object(preschool, "neutral_probe_run", side_effect=self.fake_probe):
            self.probe(str(adapter))
            weights.write_bytes(b"changed")
            with self.assertRaises(RuntimeError):
                self.probe(str(adapter))
            weights.write_bytes(b"fixture weights, not a model")
            config.write_text('{"r":16}')
            with self.assertRaises(RuntimeError):
                self.probe(str(adapter))

    def test_legacy_cache_and_unhashed_adapter_refused(self):
        path = Path(preschool.neutral_probe_path(str(self.life), "post", 32))
        original = '{"adapter_sha256":"old"}'
        path.write_text(original)
        with self.assertRaises(RuntimeError):
            self.probe()
        self.assertEqual(path.read_text(), original)
        with self.assertRaises(RuntimeError):
            self.probe(str(self.life / "missing"))

    def drive_slots(self, life, episode_ids, model=None, enabled=True):
        return run_episodes_batch(model or SlotModel(), StubGym(),
                                  [Episode(eid=episode_id) for episode_id in episode_ids],
                                  "birth", Ledger(str(life / "ledger.jsonl")),
                                  budget_ticks=1, log=lambda text: None, gen_seed=10100,
                                  note_after=preschool.PostOutcomeSlot() if enabled else None)

    def life_rows(self, life=None):
        return Ledger(str((life or self.life) / "ledger.jsonl")).rows()

    def test_repeated_visits_and_restart_have_unique_shared_ids(self):
        self.drive_slots(self.life, ["train/repeat", "train/repeat"])
        path = self.life / "ledger.jsonl"
        previous = path.read_bytes()
        self.drive_slots(self.life, ["train/repeat", "train/repeat"])
        self.assertTrue(path.read_bytes().startswith(previous))
        rows = self.life_rows()
        acts = [row for row in rows if row["kind"] == "act"]
        records = [row for row in rows if row["kind"] == "note_after"]
        self.assertEqual(len({row["execution_id"] for row in acts}), 4)
        self.assertEqual([row["occurrence_index"] for row in acts], [1, 2, 3, 4])
        for action, record in zip(acts, records):
            for field in ("execution_id", "occurrence_id", "occurrence_index"):
                self.assertEqual(action[field], record[field])

    def test_ids_are_deterministic_for_matching_append_histories(self):
        twins = [self.life / name for name in ("left", "right")]
        for life in twins:
            life.mkdir()
            self.drive_slots(life, ["train/repeat", "train/repeat"])
            self.drive_slots(life, ["train/repeat"])
        sequences = [[row["execution_id"] for row in self.life_rows(life)
                      if row["kind"] == "act"] for life in twins]
        self.assertEqual(sequences[0], sequences[1])

    def test_visit_reservations_are_serialized(self):
        from concurrent.futures import ThreadPoolExecutor
        def reserve(unused):
            driver = SimpleNamespace(ep=SimpleNamespace(eid="train/repeat"))
            ledger = Ledger(str(self.life / "ledger.jsonl"))
            preschool.PostOutcomeSlot().reserve_occurrences([driver], ledger)
            return driver.occurrence_index
        with ThreadPoolExecutor(max_workers=4) as executor:
            indices = list(executor.map(reserve, range(8)))
        self.assertEqual(sorted(indices), list(range(1, 9)))
        self.assertEqual(len({row["occurrence_id"] for row in self.life_rows()}), 8)

    def test_interrupted_reservations_and_acts_are_never_reused(self):
        for failure in ("wake", "record"):
            with self.subTest(failure=failure):
                life = self.life / failure
                life.mkdir()
                with self.assertRaisesRegex(RuntimeError, "interruption"):
                    self.drive_slots(life, ["train/repeat"], SlotModel(failure))
                previous = (life / "ledger.jsonl").read_bytes()
                self.drive_slots(life, ["train/repeat"])
                self.assertTrue((life / "ledger.jsonl").read_bytes().startswith(previous))
                rows = self.life_rows(life)
                reservations = [row for row in rows if row["kind"] == "episode_occurrence"]
                self.assertEqual([row["occurrence_index"] for row in reservations], [1, 2])
                records = [row for row in rows if row["kind"] == "note_after"]
                self.assertEqual(records[0]["occurrence_index"], 2)

    def test_legacy_ledger_preserved_and_slot_off_has_no_new_fields(self):
        self.drive_slots(self.life, ["train/repeat"], enabled=False)
        rows = self.life_rows()
        self.assertFalse(any("occurrence_id" in row or "execution_id" in row for row in rows))
        self.assertFalse(any(row["kind"] == "episode_occurrence" for row in rows))
        path = self.life / "ledger.jsonl"
        legacy = json.dumps(dict(execution()[0], execution_id="train/repeat#t1a1")) + "\n"
        with path.open("a") as ledger:
            ledger.write(legacy)
        previous = path.read_bytes()
        self.drive_slots(self.life, ["train/repeat"])
        self.assertTrue(path.read_bytes().startswith(previous))
        self.assertNotEqual(self.life_rows()[-1]["execution_id"], "train/repeat#t1a1")

    def test_corrupt_occurrence_index_fails_without_rewriting(self):
        path = self.life / "ledger.jsonl"
        original = '{"kind":"episode_occurrence","occurrence_index":true}\n'
        path.write_text(original)
        with self.assertRaisesRegex(RuntimeError, "invalid occurrence index"):
            self.drive_slots(self.life, ["train/repeat"])
        self.assertEqual(path.read_text(), original)

    def test_occurrence_mismatch_is_rejected(self):
        action, record = execution()
        action.update(occurrence_id="first", occurrence_index=1)
        record.update(occurrence_id="second", occurrence_index=1)
        result = self.gate([action, record])
        self.assertEqual(result["rejection_families"], {"provenance-mismatch-occurrence_id": 1})

    def test_partial_neutral_ledger_is_preserved(self):
        path = self.life / "neutral_probe_post_0032.ledger.jsonl"
        original = '{"kind":"episode_occurrence","occurrence_index":1}\n'
        path.write_text(original)
        with self.assertRaisesRegex(RuntimeError, "partial neutral probe ledger"):
            self.probe()
        self.assertEqual(path.read_text(), original)

    def test_exact_b0_low_diversity_still_skips(self):
        self.run_b0_pair(diverse=False)

    def test_exact_b0_diverse_records_train_and_reload(self):
        self.run_b0_pair(diverse=True)

    def run_b0_pair(self, diverse):
        tests_path = str(Path(__file__).resolve().parent)
        original_mkdtemp = tempfile.mkdtemp
        def contained_mkdtemp(*args, **kwargs):
            kwargs["dir"] = str(self.life)
            return original_mkdtemp(*args, **kwargs)
        with patch.object(sys, "path", [tests_path] + sys.path), patch.dict(os.environ), patch("tempfile.mkdtemp", side_effect=contained_mkdtemp):
            import golden_harness as harness
            from test_preschool_flags import RecordingFakeModel
            class DiverseRecordModel(RecordingFakeModel):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    harness.FakeModel.transcript.add(kind="load", adapter=self.adapter_path)

                def batch(self, prompts, max_tokens=400, temperature=.7, seeds=None):
                    outputs = []
                    for index, prompt in enumerate(prompts):
                        tail = prompt.rstrip().splitlines()[-1]
                        if tail in ("NOTE_AFTER:", "Scratchpad:"):
                            text = self._record(prompt)
                            harness.FakeModel.transcript.add(kind="post_outcome", prompt=prompt,
                                                           output=text, adapter=self.adapter_path)
                        else:
                            seed = seeds[index] if seeds is not None else index
                            passes = [name for bit, name in enumerate(harness.VALID_PASSES)
                                      if seed & (1 << bit)] or ["-mem2reg"]
                            text = "PREDICT: 0.3\nACT: " + ", ".join(passes)
                            harness.FakeModel.transcript.add(kind="batch", seed=seed, prompt=prompt,
                                                           output=text, adapter=self.adapter_path)
                        outputs.append(text)
                    return outputs

            original_trainer_factory = harness.make_fake_subprocess_run
            def trainer_factory(transcript):
                trainer = original_trainer_factory(transcript)
                def train(command, *args, **kwargs):
                    result = trainer(command, *args, **kwargs)
                    output = Path(command[command.index("--out") + 1])
                    (output / "adapter_model.safetensors").write_bytes(b"CPU fixture only; not real weights")
                    (output / "adapter_config.json").write_text('{"r":8}')
                    return result
                return train
            receipts = {}
            for arm in ("A", "B"):
                life = self.life / ("B0_" + arm)
                life.mkdir()
                (life / "QUARANTINE_TASK_EXPOSED").write_text("disposable CPU fixture")
                arguments = ["--life-dir", str(life), "--gym", "compiler", "--arm", arm,
                             "--seed", "9100", "--train-seed", "9100", "--rank", "8",
                             "--episodes", "32", "--sleep-every", "32", "--probe-every", "32",
                             "--budget-ticks", "16", "--wake-batch", "8", "--note-after",
                             "--artifact-lesson", "none", "--articulation-gate", "enforce", "--neutral-probes"]
                with patch.object(harness, "FakeModel", DiverseRecordModel if diverse else RecordingFakeModel), patch.object(harness, "make_fake_subprocess_run", trainer_factory), contextlib.redirect_stdout(io.StringIO()):
                    transcript = harness.run_life(arguments)
                sleep = life / "sleep_0032"
                report = json.loads((sleep / "articulation_shadow.json").read_text())
                corpus = json.loads((sleep / "corpus.json").read_text())["corpus"]
                state = json.loads((life / "articulation_state.json").read_text())
                expected = preschool._dedup([preschool.RECORD_ITEM.format(eid=record["episode_id"], text=record["text"])
                                            for record in state["admitted"]])
                self.assertEqual(corpus, expected)
                self.assertEqual(report["min_items"], 64)
                self.assertEqual(report["training_skipped"], not diverse)
                self.assertFalse(any(event["kind"] == "parent" for event in transcript.events))
                self.assertEqual(sum(event["kind"] == "train" for event in transcript.events),
                                 int(diverse and arm == "B"))
                self.assertNotIn("provenance-ambiguous-execution", report["rejection_families"])
                if diverse:
                    self.assertGreaterEqual(report["n_admitted_new"], 64)
                    self.assertGreaterEqual(len(corpus), 64)
                if diverse and arm == "B":
                    self.assertTrue((sleep / "adapter" / "DONE").exists())
                    self.assertGreaterEqual(sum(event["kind"] == "load" and event["adapter"] is not None
                                                for event in transcript.events), 2)
                self.assertFalse((life / "lesson_deliveries.jsonl").exists())
                self.assertTrue((sleep / "corpus_legacy.json").exists())
                for filename in ("neutral_probe_pre_0032.json", "neutral_probe_post_0032.json"):
                    payload = json.loads((life / filename).read_text())
                    if diverse and arm == "B" and "post" in filename:
                        self.assertEqual(payload["cache_identity"]["adapter_sha256"],
                                         hashlib.sha256(b"CPU fixture only; not real weights").hexdigest())
                    else:
                        self.assertIsNone(payload["cache_identity"]["adapter_sha256"])
                rows = self.life_rows(life)
                actions = [row for row in rows if row["kind"] == "act"]
                self.assertEqual(len({row["execution_id"] for row in actions}), len(actions))
                self.assertEqual(sum(row["kind"] == "episode_occurrence" for row in rows), 32)
                tape = [json.loads(path.read_text()) for path in sorted(life.glob("wake_*.json"))]
                receipts[arm] = dict(admitted=report["n_admitted_new"], corpus_items=len(corpus),
                                     rejection_families=report["rejection_families"],
                                     corpus_sha256=hashlib.sha256((sleep / "corpus.json").read_bytes()).hexdigest(),
                                     tape_sha256=hashlib.sha256(json.dumps(tape, sort_keys=True).encode()).hexdigest())
            self.assertEqual(receipts["A"], receipts["B"])
            print("B0_NEW_CPU_RECEIPT diverse=" + str(diverse) + " " + json.dumps(receipts, sort_keys=True))


if __name__ == "__main__":
    unittest.main()
