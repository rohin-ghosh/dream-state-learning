from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from gpu import astra_experienced_event_cue_collect as runner
from test_experienced_event_cue_collection import PublicReadingActor, generation


class SyntheticEngine:
    def __init__(self, *, bad_first_bank=False, actor_error=False):
        self.banks = runner.training_banks()
        self.facts = sum(self.banks, [])
        self.actor = PublicReadingActor()
        self.bad_events = {fact["event"] for fact in self.banks[0]} if bad_first_bank else set()
        self.actor_error = actor_error

    def generate(self, messages):
        if messages[0]["content"] == runner.source.material.FORMATION_SYSTEM:
            fact = next(fact for fact in self.facts if fact["port"] in messages[1]["content"])
            if len(messages) == 2:
                return generation("EXPLORE " + fact["node"] + " " + fact["port"])
            raw = "invalid event" if fact["event"] in self.bad_events else runner.source.material._event(fact) + "\n"
            return generation(raw)
        if self.actor_error:
            raise RuntimeError("synthetic generation infrastructure fault")
        return self.actor(messages)


class CueNativeTests(unittest.TestCase):
    def test_training_banks_exclude_previous_bank_and_each_other(self):
        banks = runner.training_banks()
        self.assertEqual(len(banks), 2)
        identities = [{value for fact in bank for value in fact.values() if type(value) is str}
                      for bank in banks + [runner.source.material.build_bank(runner.source.MASTER)]]
        self.assertTrue(all(not identities[first] & identities[second]
                            for first in range(3) for second in range(first + 1, 3)))

    def test_source_then_external_text_collection_no_fit(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            result = runner.collect(SyntheticEngine(), root)
            self.assertEqual(result["admitted_events"], 8)
            self.assertEqual(result["selected_successes"], 8)
            self.assertEqual(result["student_rows"], 20)
            self.assertEqual(result["physical_model_calls"], 36)
            self.assertEqual(result["fits"], 0)
            self.assertEqual(len(list(root.glob("CALL_*.json"))), 36)
            bank = runner.source.read(root / "BANK_00/CUE_COLLECTION.json")
            self.assertTrue(all(raw.endswith("\n\n") for raw in bank["raw_memory_by_address"].values()))

    def test_wrong_source_events_are_not_repaired_or_used_for_cues(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            result = runner.collect(SyntheticEngine(bad_first_bank=True), root)
            self.assertEqual(result["admitted_events"], 4)
            self.assertEqual(result["selected_successes"], 4)
            self.assertEqual(result["cue_task_denominator"], 8)
            bank = runner.source.read(root / "BANK_00/CUE_COLLECTION.json")
            self.assertEqual(bank["status"], "SOURCE_INCOMPLETE_NO_CUE_EPISODES")
            self.assertEqual(bank["student_rows"], [])

    def test_infrastructure_fault_cannot_finish_as_complete_collection(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaisesRegex(ValueError, "native_callback_failure"):
                runner.collect(SyntheticEngine(actor_error=True), root)
            calls = [runner.source.read(path) for path in root.glob("CALL_*.json")]
            self.assertTrue(any(call["error"] for call in calls))
            self.assertTrue((root / "BANK_RESULTS.json").exists())


if __name__ == "__main__":
    unittest.main()
