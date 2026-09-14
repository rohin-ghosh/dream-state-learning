import copy
from collections import Counter
import hashlib
import json
import subprocess
import sys
import unittest
from unittest.mock import patch

from organism_v6 import experienced_event_adult_cycle as adult
from organism_v6 import experienced_event_microloop as micro


class AdultCycleTests(unittest.TestCase):
    def setUp(self):
        self.bank = adult.build_bank()

    def generation(self, messages, final_lfs=1):
        fact = next(fact for fact in self.bank if fact["port"] in messages[1]["content"])
        raw = ("EXPLORE " + fact["node"] + " " + fact["port"] if len(messages) == 2
               else micro._event(fact).rstrip("\n") + "\n" * final_lfs)
        return dict(raw=raw, terminal=True, truncated=False, messages=copy.deepcopy(messages))

    def test_grounded_collection_exact_prompts_rows_and_replay(self):
        record = adult.collect(self.generation)
        self.assertEqual(record["status"], "COLLECTION_COMPLETE_NO_FIT")
        self.assertEqual((record["count"], record["accepted_events"], len(record["episodes"])), (8, 4, 4))
        self.assertEqual(record["serialization"], "FINAL_LF_ONLY")
        self.assertTrue(record["new_material"])
        self.assertFalse(record["clean_claim"])
        self.assertFalse(record["parent_present"])
        self.assertEqual(record["fits"], 0)
        self.assertEqual(record["infrastructure_failures"], 0)
        self.assertEqual(len(record["rows"]), 32)
        for index, fact in enumerate(self.bank):
            explore, event = record["captures"][2 * index:2 * index + 2]
            self.assertEqual(explore["messages"], micro.exploration_messages(fact))
            self.assertNotIn(fact["outcome"], json.dumps(explore["messages"]))
            self.assertNotIn(fact["receipt"], json.dumps(explore["messages"]))
            self.assertEqual(event["messages"], micro.observation_messages(fact, explore["response"]["raw"]))
            self.assertIn(fact["outcome"], event["messages"][-1]["content"])
        for row in record["rows"]:
            fact = next(fact for fact in self.bank if fact["event"] == row["event"])
            self.assertEqual([message["role"] for message in row["messages"]], ["system", "user", "assistant"])
            self.assertEqual(row["messages"][-1]["content"], micro._event(fact))
            self.assertEqual(row["messages"][0]["content"], micro.MEMORY_SYSTEM)
            self.assertNotIn(fact["outcome"], row["messages"][1]["content"])
            self.assertNotIn("Teacher strategy", json.dumps(row))
            self.assertNotIn("Public-feedback teacher", json.dumps(row))
            self.assertNotIn("EXPLORE TASK", json.dumps(row))
        original = copy.deepcopy(record)
        self.assertEqual(adult.replay_collection(record), record["rows"])
        self.assertEqual(record, original)

    def test_final_lf_only_is_explicit_and_preserves_source(self):
        for final_lfs in (0, 1, 2, 5):
            with self.subTest(final_lfs=final_lfs):
                record = adult.collect(lambda messages: self.generation(messages, final_lfs))
                self.assertEqual(record["accepted_events"], 4)
                self.assertEqual(adult.replay_collection(record), record["rows"])
                for index, episode in enumerate(record["episodes"]):
                    raw = micro._event(self.bank[index]).rstrip("\n") + "\n" * final_lfs
                    self.assertEqual(episode["event"]["raw"], raw)
                    self.assertEqual(record["rows"][index]["source_raw_sha256"], hashlib.sha256(raw.encode()).hexdigest())
                if final_lfs != 1:
                    self.assertEqual(micro.compile_rows(record["bank"], record["episodes"]), [])

    def test_every_identity_field_is_grounded_not_repaired(self):
        for field in ("event", "node", "port", "outcome", "receipt"):
            def generate(messages):
                response = self.generation(messages)
                if len(messages) == 4 and self.bank[0]["event"] in response["raw"]:
                    response["raw"] = response["raw"].replace(self.bank[0][field], self.bank[2][field])
                return response
            with self.subTest(field=field):
                record = adult.collect(generate)
                self.assertEqual((record["accepted_events"], record["count"]), (3, 8))
                self.assertEqual(record["status"], "COLLECTION_FAILED_NO_FIT")
                self.assertEqual(record["rows"], [])
                self.assertEqual(adult.replay_collection(record), [])
                self.assertIsNotNone(record["episodes"][0]["error"])

    def test_event_grammar_failures_are_not_repaired(self):
        for transform in (lambda raw: " " + raw, lambda raw: raw.replace(" AT ", "  AT "),
                          lambda raw: raw.rstrip("\n") + "\r\n", lambda raw: raw + "explanation"):
            def generate(messages):
                response = self.generation(messages)
                if len(messages) == 4:
                    response["raw"] = transform(response["raw"])
                return response
            record = adult.collect(generate)
            self.assertEqual((record["count"], record["accepted_events"]), (8, 0))
            self.assertEqual(adult.replay_collection(record), [])

    def test_invalid_explore_gets_no_receipt_or_event_call(self):
        for raw in ("MISS", "EXPLORE " + self.bank[0]["node"] + " " + self.bank[0]["port"] + "\n",
                    "EXPLORE " + self.bank[0]["node"] + " " + self.bank[2]["port"]):
            record = adult.collect(lambda messages: dict(raw=raw, terminal=True, truncated=False))
            self.assertEqual((record["count"], record["accepted_events"]), (4, 0))
            self.assertTrue(all(episode["event"] is None for episode in record["episodes"]))
            self.assertTrue(all(capture["response"]["raw"] == raw for capture in record["captures"]))
            self.assertEqual(adult.replay_collection(record), [])

    def test_generation_schema_flags_and_prompt_fail_closed(self):
        for patch_response in ({"raw": None}, {"terminal": 1}, {"truncated": 0},
                               {"terminal": False}, {"truncated": True}, {"messages": []}):
            def generate(messages):
                response = self.generation(messages)
                response.update(patch_response)
                return response
            record = adult.collect(generate)
            self.assertEqual((record["count"], record["accepted_events"]), (4, 0))
            self.assertEqual(adult.replay_collection(record), [])
        for response in (None, "not a dict", {"raw": "MISS"}):
            record = adult.collect(lambda messages: response)
            self.assertEqual(record["count"], 4)
            self.assertEqual(adult.replay_collection(record), [])

    def test_callback_and_non_json_failures_retain_available_raw(self):
        def broken(messages):
            raise RuntimeError("generation failed")
        record = adult.collect(broken)
        self.assertEqual(record["count"], 4)
        self.assertTrue(all(capture["error"] == {"type": "RuntimeError", "message": "generation failed"}
                            for capture in record["captures"]))
        self.assertEqual(record["infrastructure_failures"], 4)
        self.assertTrue(all(episode["infrastructure_failure"] and
                            episode["error"] == {"type": "RuntimeError", "message": "generation failed"}
                            for episode in record["episodes"]))
        self.assertEqual(adult.replay_collection(record), [])

    def test_event_callback_failure_retains_explore_and_native_error(self):
        def generate(messages):
            if len(messages) == 4 and self.bank[0]["event"] in messages[-1]["content"]:
                raise RuntimeError("CUDA out of memory: captured test error")
            return self.generation(messages)
        record = adult.collect(generate)
        self.assertEqual((record["count"], record["accepted_events"], record["infrastructure_failures"]), (8, 3, 1))
        self.assertEqual(record["rows"], [])
        self.assertTrue(record["episodes"][0]["exploration"]["terminal"])
        self.assertIsNone(record["episodes"][0]["event"])
        self.assertEqual(record["episodes"][0]["error"], record["captures"][1]["error"])
        self.assertEqual(record["episodes"][0]["error"]["type"], "RuntimeError")
        self.assertIn("CUDA out of memory", record["episodes"][0]["error"]["message"])
        self.assertEqual(adult.replay_collection(record), [])

    def test_nonterminal_event_is_retained_and_blocks_all_rows(self):
        def generate(messages):
            response = self.generation(messages)
            if len(messages) == 4:
                response.update(terminal=False, truncated=True)
            return response
        record = adult.collect(generate)
        self.assertEqual((record["count"], record["accepted_events"]), (8, 0))
        self.assertEqual(record["rows"], [])
        self.assertTrue(all(episode["event"]["raw"] == micro._event(fact)
                            for episode, fact in zip(record["episodes"], self.bank)))
        self.assertEqual(adult.replay_collection(record), [])
        record = adult.collect(lambda messages: dict(raw="raw retained", terminal=True, truncated=False, bad=object()))
        self.assertTrue(all(capture["response"]["raw"] == "raw retained" for capture in record["captures"]))
        self.assertEqual(adult.replay_collection(record), [])

    def test_callback_cannot_mutate_recorded_prompt(self):
        def generate(messages):
            response = self.generation(messages)
            messages.clear()
            return response
        record = adult.collect(generate)
        self.assertEqual(record["accepted_events"], 4)
        self.assertEqual(adult.replay_collection(record), record["rows"])

    def test_replay_rejects_source_split_target_and_metadata_drift(self):
        original = adult.collect(self.generation)
        mutations = [
            lambda record: record.update(master="different"),
            lambda record: record.update(serialization="EXACT"),
            lambda record: record.update(clean_claim=True),
            lambda record: record.update(count=7),
            lambda record: record.update(status="COMPLETE"),
            lambda record: record["bank"].reverse(),
            lambda record: record["episodes"].pop(),
            lambda record: record["episodes"][0].update(accepted=False),
            lambda record: record["captures"].pop(),
            lambda record: record["captures"].append(copy.deepcopy(record["captures"][-1])),
            lambda record: record["captures"][0].update(episode_index=1),
            lambda record: record["captures"][0]["messages"][1].update(content="teacher"),
            lambda record: record["captures"][1]["response"].update(raw=micro._event(self.bank[2])),
            lambda record: record["episodes"][0]["event"].update(raw=micro._event(self.bank[2])),
            lambda record: record["rows"][0]["messages"][-1].update(content=micro._event(self.bank[2])),
            lambda record: record["rows"][0]["messages"][0].update(role="assistant"),
            lambda record: record["rows"][0].update(source_raw_sha256="0" * 64),
            lambda record: record["rows"].pop(),
        ]
        for index, mutate in enumerate(mutations):
            with self.subTest(index=index):
                record = copy.deepcopy(original)
                mutate(record)
                with self.assertRaises(ValueError):
                    adult.replay_collection(record)

    def test_bank_disjoint_from_every_reserved_bank(self):
        banks = [micro.build_bank(adult.source.MASTER), *adult.collector.training_banks()]
        banks.extend(micro.build_bank(adult.cue_sleep.HELD_MASTER + "-" + str(index)) for index in range(2))
        for bank in banks:
            self.assertFalse(adult._identities(self.bank) & adult._identities(bank))
        for master in (adult.source.MASTER, adult.collector.MASTER + "-0", adult.collector.MASTER + "-1",
                       adult.cue_sleep.HELD_MASTER + "-0", adult.cue_sleep.HELD_MASTER + "-1"):
            with self.subTest(master=master), patch.object(adult, "MASTER", master):
                with self.assertRaisesRegex(ValueError, "adult_identity_overlap"):
                    adult.collect(self.generation)

    def test_fixed_layout_schedule_and_exact_group_doses(self):
        counts = Counter()
        for update in range(1, 401):
            indexes = adult.adult_indexes(update, 20)
            self.assertIsInstance(indexes, tuple)
            self.assertEqual(len(indexes), 4)
            old, cue, first, second = indexes
            self.assertTrue(0 <= old < 32 and 32 <= cue < 52 and 52 <= first < 84 and 52 <= second < 84)
            self.assertNotEqual(first, second)
            counts.update(indexes)
        self.assertEqual(sum(counts[index] for index in range(32)), 400)
        self.assertEqual(sum(counts[index] for index in range(32, 52)), 400)
        self.assertEqual(sum(counts[index] for index in range(52, 84)), 800)
        self.assertEqual({counts[index] for index in range(32, 52)}, {20})
        self.assertEqual({counts[index] for index in range(52, 84)}, {25})
        self.assertEqual(adult.adult_indexes(1, 20), (0, 32, 52, 53))
        self.assertEqual(adult.adult_indexes(400, 20), (15, 51, 82, 83))
        for update in (True, False, 0, 401, 1.0, "1", None):
            with self.assertRaises(ValueError):
                adult.adult_indexes(update, 20)
        for count in (True, 0, 19, 21, 20.0, "20", None):
            with self.assertRaises(ValueError):
                adult.adult_indexes(1, count)

    def test_import_does_not_load_native_libraries(self):
        command = """
import importlib.abc
import sys
class Guard(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'torch', 'transformers', 'tokenizers', 'peft'}:
            raise RuntimeError(fullname)
sys.meta_path.insert(0, Guard())
from organism_v6 import experienced_event_adult_cycle as adult
assert len(adult.build_bank()) == 4
"""
        subprocess.run([sys.executable, "-B", "-c", command], check=True, capture_output=True)


if __name__ == "__main__":
    unittest.main()
