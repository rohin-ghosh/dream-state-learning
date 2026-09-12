"""Non-material NOTE seam regression; synthetic CPU fixtures, not science evidence."""
import hashlib
import json
import unittest
from unittest.mock import patch

import test_clean_nursery_runner as nursery
from organism_v6 import preschool_reasoning as reasoning
from organism_v6.ledger import Ledger


NOTE_TEXT = "I will check the next answer rather than assume it is correct."


class NoteNurseryModelFixture(nursery.VariedNurseryModelFixture):
    def batch(self, prompts, max_tokens=400, temperature=0.7, seeds=None):
        outputs = super().batch(prompts, max_tokens, temperature, seeds)
        return [output if prompt.endswith("NOTE_AFTER:") else f"NOTE: {NOTE_TEXT}\n{output}"
                for prompt, output in zip(prompts, outputs)]


class NurseryNoteIntegrationTests(unittest.TestCase):
    def fixture(self):
        fixture = nursery.CleanNurseryRunnerTests(methodName="runTest")
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        return fixture

    def test_full_run_preserves_notes_without_admitting_them(self):
        fixture = self.fixture()
        with patch.object(nursery, "VariedNurseryModelFixture", NoteNurseryModelFixture):
            fixture.run_admitted_fixture()
        sleep = fixture.life / "sleep_0064"
        ledger_bytes = (sleep / "reasoning_ledger.jsonl").read_bytes()
        lines = ledger_bytes.splitlines(keepends=True)
        rows = [json.loads(line) for line in lines]
        notes = [row for row in rows if row["kind"] == "note"]
        self.assertEqual(len(notes), 64)
        self.assertTrue(all(row["note"] == NOTE_TEXT for row in notes))
        self.assertTrue(all("generation" not in row for row in notes))
        corpus = json.loads((sleep / "corpus.json").read_bytes())
        gate = json.loads((sleep / "gate_receipt.json").read_bytes())
        self.assertEqual(len(corpus["corpus"]), 64)
        self.assertTrue(all(NOTE_TEXT not in item for item in corpus["corpus"]))
        self.assertEqual(gate["decision"], "ADMIT")
        self.assertEqual(gate["ledger_sha256"], hashlib.sha256(ledger_bytes).hexdigest())
        for admission in gate["admissions"]:
            self.assertEqual(rows[admission["source_line"]]["kind"], "act")
            self.assertEqual(rows[admission["record_line"]]["kind"], "note_after")
            for prefix in ("source", "record"):
                self.assertEqual(admission[prefix + "_sha256"], hashlib.sha256(
                    lines[admission[prefix + "_line"]]).hexdigest())
        lineage = fixture.life / "lineage" / "sleep_0064"
        self.assertEqual((lineage / "ledger.jsonl").read_bytes(), ledger_bytes)
        self.assertTrue((fixture.life / "LIFE_DONE").exists())

    def test_corrupted_notes_fail_before_training_or_promotion(self):
        append = Ledger.append
        changes = ({"kind": "scratchpad"}, {"note": ""}, {"speaker": "teacher"},
                   {"episode_id": "rg/mini_sudoku/1000999"},
                   {"episode_id": "rg/n_queens/2000001"}, {"gym": "other_gym"},
                   {"clone_id": True}, {"exposure_status": "QUARANTINE_TASK_EXPOSED"})
        for change in changes:
            with self.subTest(change=change):
                fixture = self.fixture()

                def corrupt_note(ledger, row):
                    return append(ledger, dict(row, **change) if row.get("kind") == "note" else row)

                with patch.object(Ledger, "append", corrupt_note), \
                        patch.object(nursery.run_life_v2.subprocess, "run") as training:
                    error = (RuntimeError if change.get("episode_id") == "rg/n_queens/2000001"
                             else reasoning.ReasoningGateError)
                    with self.assertRaises(error):
                        fixture.run_fixture(model_class=NoteNurseryModelFixture, varied=True)
                    training.assert_not_called()
                self.assertTrue((fixture.life / "ledger.jsonl").is_file())
                self.assertFalse((fixture.life / "LIFE_DONE").exists())
                self.assertFalse((fixture.life / "lineage" / "sleep_0002").exists())
