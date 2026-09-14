"""CPU fixtures for the bounded own-event native runner; no model execution."""

from collections import Counter
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from gpu import astra_experienced_event_microloop as runner
from organism_v6 import experienced_event_microloop as material
from organism_v6 import pcfl_vertical_dev as world
from test_astra_pchain2_native import FakeTokenizer


def fixture():
    bank = material.build_bank(runner.MASTER)
    episodes = []
    for fact in bank:
        event = world.EVENT_WIRE.format(event=fact["event"], source=fact["node"],
            port=fact["port"], destination=fact["outcome"], receipt=fact["receipt"])
        episodes.append(dict(fact=fact, accepted=True,
            exploration=dict(raw="EXPLORE " + fact["node"] + " " + fact["port"], terminal=True, truncated=False),
            event=dict(raw=event, terminal=True, truncated=False)))
    return bank, episodes


class Tests(unittest.TestCase):
    def test_torch_distribution_and_cuda_build_are_separately_pinned(self):
        versions = dict(runner.native.NUMERICAL_BINDING["runtime"])
        distributions = dict(versions, torch="2.13.0")
        runner.validate_runtime(versions, distributions)
        with self.assertRaises(ValueError):
            runner.validate_runtime(dict(versions, torch="2.13.0+cu129"), distributions)
        with self.assertRaises(ValueError):
            runner.validate_runtime(versions, dict(distributions, torch="2.12.0"))

    def test_schedule_exact_fixed_dose_and_distinct_batch_facts(self):
        bank, episodes = fixture()
        rows = material.compile_rows(bank, episodes)
        counts = Counter(index for update in range(1, 201) for index in runner.batch_indexes(update))
        self.assertEqual(counts, Counter({index: 25 for index in range(32)}))
        for update in range(1, 201):
            self.assertEqual(len({rows[index]["event"] for index in runner.batch_indexes(update)}), 4)
        with self.assertRaises(ValueError):
            runner.batch_indexes(201)

    def test_masks_and_loss_only_actual_assistant_eot(self):
        bank, episodes = fixture()
        rows = material.compile_rows(bank, episodes)
        tokenizer = FakeTokenizer()
        encoded = runner.encode_rows(rows, tokenizer)
        self.assertEqual(len(encoded), 32)
        for row, tokens in zip(rows, encoded):
            target = tokenizer.encode(row["messages"][-1]["content"]) + [tokenizer.eos_token_id]
            self.assertEqual([label for label in tokens.labels if label != -100], target)
            self.assertEqual(tokens.labels[-1], -100)
            self.assertNotIn(row["messages"][-1]["content"], row["messages"][1]["content"])

    def test_reject_injected_answer_and_wrong_system(self):
        bank, episodes = fixture()
        rows = material.compile_rows(bank, episodes)
        for index in (0, 1):
            changed = deepcopy(rows)
            if index == 0:
                changed[0]["messages"][0]["content"] = "teacher"
            else:
                changed[0]["messages"][1]["content"] += changed[0]["messages"][-1]["content"]
            with self.assertRaises(ValueError):
                runner.encode_rows(changed, FakeTokenizer())

    def test_source_roundtrip_and_drift(self):
        bank, episodes = fixture()
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name, value in (("BANK.json", bank), ("EPISODES.json", episodes),
                                ("ROWS.json", material.compile_rows(bank, episodes))):
                runner.write(root / name, value)
            runner.write(root / "RESULT.json", dict(schema=runner.SCHEMA, phase="collect", status="COMPLETE",
                accepted_events=4, files={name: runner.file_hash(root / name)
                    for name in ("BANK.json", "EPISODES.json", "ROWS.json")}))
            restored = runner.load_collection(root)
            self.assertEqual(restored[:2], (bank, episodes))
            (root / "ROWS.json").write_text("[]")
            with self.assertRaises(ValueError):
                runner.load_collection(root)

    def test_failure_inclusive_readout_roster_and_ceiling(self):
        bank, episodes = fixture()

        class MissEngine:
            def generate(self, messages):
                return dict(messages=messages, raw="MISS", terminal=True, truncated=False)

        with TemporaryDirectory() as temporary:
            report = runner.evaluate(MissEngine(), bank, episodes, Path(temporary))
            self.assertEqual(report["model_calls"], 24)
            self.assertEqual(len(report["panels"]), 6)
            self.assertTrue(all(panel["denominator"] == 4 for panel in report["panels"].values()))
            self.assertEqual(report["panels"]["unseen_miss"]["correct"], 4)
            self.assertEqual(report["panels"]["native_action"]["correct"], 0)

    def test_unterminated_memory_is_not_repaired_before_action(self):
        bank, episodes = fixture()

        class TruncatedEngine:
            def __init__(self):
                self.prompts = []

            def generate(self, messages):
                self.prompts.append(messages)
                return dict(messages=messages, raw="BROKEN_OWN_READ", terminal=False, truncated=True)

        engine = TruncatedEngine()
        with TemporaryDirectory() as temporary:
            report = runner.evaluate(engine, bank, episodes, Path(temporary))
        own_read_prompts = [messages for messages in engine.prompts
                            if "ACTUAL MODEL-READ TEXT" in messages[-1]["content"]]
        self.assertEqual(len(own_read_prompts), 4)
        self.assertTrue(all("BROKEN_OWN_READ\nBROKEN_OWN_READ" in messages[-1]["content"]
                            for messages in own_read_prompts))
        self.assertEqual(report["panels"]["recall_W8"]["correct"], 0)


if __name__ == "__main__":
    unittest.main()
