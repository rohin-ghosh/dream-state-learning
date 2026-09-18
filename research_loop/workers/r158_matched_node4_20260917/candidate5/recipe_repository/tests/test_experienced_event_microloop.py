import copy
import hashlib
import json
import unittest

from organism_v6 import experienced_event_microloop as micro
from organism_v6 import pcfl_vertical_dev as pcfl


class ExperiencedEventMicroloopTests(unittest.TestCase):
    def setUp(self):
        self.bank = micro.build_bank("MICROLOOP-CPU-TEST-A1")
        self.episodes = [dict(
            event=fact["event"],
            exploration_raw=f"EXPLORE {fact['node']} {fact['port']}",
            event_raw=(f"EVENT {fact['event']} AT {fact['node']} DID {fact['port']} "
                       f"GOT {fact['outcome']} EVIDENCE {fact['receipt']}\n"),
        ) for fact in self.bank]

    def records(self):
        return [dict(fact=copy.deepcopy(fact), exploration=dict(
            raw=episode["exploration_raw"], terminal=True, truncated=False),
            event=dict(raw=episode["event_raw"], terminal=True, truncated=False),
            accepted=True, error=None) for fact, episode in zip(self.bank, self.episodes)]

    def test_deterministic_fresh_bank_and_exact_keys(self):
        self.assertEqual(self.bank, micro.build_bank("MICROLOOP-CPU-TEST-A1"))
        other = micro.build_bank("MICROLOOP-CPU-TEST-A2")
        for key in ("world", "event", "node", "port", "outcome", "receipt"):
            self.assertFalse({fact[key] for fact in self.bank} & {fact[key] for fact in other})
        self.assertEqual(len(self.bank), 4)
        self.assertTrue(all(set(fact) == micro.FACT_KEYS for fact in self.bank))
        self.assertEqual(json.loads(json.dumps(self.bank)), self.bank)
        self.assertEqual([fact["public_ports"].index(fact["port"]) for fact in self.bank], [0, 1, 1, 0])
        for master in (None, "", "  ", 1):
            with self.assertRaises(ValueError):
                micro.build_bank(master)

    def test_singleton_offer_and_actual_receipt(self):
        for fact, episode in zip(self.bank, self.episodes):
            messages = micro.exploration_messages(fact)
            prompt = messages[-1]["content"]
            self.assertIn(fact["port"], prompt)
            for hidden in (fact["outcome"], fact["event"], fact["receipt"],
                           next(port for port in fact["public_ports"] if port != fact["port"])):
                self.assertNotIn(hidden, prompt)
            observed = micro.observation_messages(fact, episode["exploration_raw"])
            self.assertEqual(observed[:2], messages)
            self.assertEqual(observed[2]["content"], episode["exploration_raw"])
            self.assertTrue(observed[3]["content"].startswith(
                f"RECEIPT {fact['receipt']} AT {fact['node']} DID {fact['port']} GOT {fact['outcome']}\n"))
            self.assertTrue(micro.validate_episode(fact, episode["exploration_raw"], episode["event_raw"]))

    def test_rejected_exploration_cannot_observe_or_train(self):
        fact, episode = self.bank[0], self.episodes[0]
        for raw in (None, "", "MISS", episode["exploration_raw"] + "\n",
                    " " + episode["exploration_raw"], self.episodes[1]["exploration_raw"]):
            with self.subTest(raw=raw):
                with self.assertRaises(ValueError):
                    micro.validate_episode(fact, raw, episode["event_raw"])
                with self.assertRaises((ValueError, TypeError)):
                    micro.observation_messages(fact, raw)

    def test_exact_event_no_repair_or_cross_fact_grounding(self):
        fact, episode = self.bank[0], self.episodes[0]
        raw = episode["event_raw"]
        invalid = [None, "", "MISS", raw.rstrip(), raw + "\n", " " + raw, raw + raw]
        for key in ("event", "node", "port", "outcome", "receipt"):
            replacement = self.bank[2][key]
            invalid.append(raw.replace(fact[key], replacement))
        for event_raw in invalid:
            with self.subTest(raw=event_raw):
                with self.assertRaises(ValueError):
                    micro.validate_episode(fact, episode["exploration_raw"], event_raw)

    def test_compiler_uses_actual_bytes_and_exact_eight_wrappers(self):
        saved = copy.deepcopy(self.episodes)
        rows = micro.compile_rows(self.bank, self.records())
        self.assertEqual(len(rows), 32)
        self.assertEqual(self.episodes, saved)
        for fact_index, episode in enumerate(self.episodes):
            for wrapper_index in range(8):
                row = rows[wrapper_index * 4 + fact_index]
                self.assertEqual(row["wrapper"], f"W{wrapper_index}")
                self.assertEqual(row["messages"], [
                    dict(role="system", content=pcfl.MEMORY_SYSTEM),
                    dict(role="user", content=pcfl.WRAPPERS[wrapper_index].format(
                        REQUEST="READ EVENT " + episode["event"])),
                    dict(role="assistant", content=episode["event_raw"]),
                ])
        for offset in range(0, 32, 4):
            batch = rows[offset:offset + 4]
            self.assertEqual([row["event"] for row in batch], [fact["event"] for fact in self.bank])
            self.assertEqual({row["wrapper"] for row in batch}, {f"W{offset // 4}"})

    def test_failures_retained_and_success_flag_not_trusted(self):
        self.episodes[0]["exploration_raw"] = "MISS"
        self.episodes[0]["success"] = True
        self.episodes[1]["event_raw"] = None
        saved = copy.deepcopy(self.episodes)
        rows = micro.compile_rows(self.bank, self.records())
        self.assertEqual(len(rows), 16)
        self.assertEqual({row["event"] for row in rows}, {fact["event"] for fact in self.bank[2:]})
        self.assertEqual(self.episodes, saved)

    def test_compiler_refuses_missing_unknown_duplicate_and_malformed_sources(self):
        missing_raw = self.records()
        del missing_raw[0]["exploration"]["raw"]
        unknown = self.records()
        unknown[0]["fact"]["event"] = "E_UNKNOWN"
        for episodes in (self.records()[:3], missing_raw, unknown,
                         [self.records()[0]] * 4, [None] * 4):
            with self.assertRaises(ValueError):
                micro.compile_rows(self.bank, episodes)
        altered = copy.deepcopy(self.bank)
        altered[1]["public_ports"].reverse()
        with self.assertRaises(ValueError):
            micro.compile_rows(altered, self.records())

    def test_compiler_checks_generation_flags_and_ignores_accepted(self):
        records = self.records()
        records[0]["exploration"]["terminal"] = False
        records[1]["event"]["truncated"] = True
        records[2]["event"] = None
        records[3]["accepted"] = False
        saved = copy.deepcopy(records)
        rows = micro.compile_rows(self.bank, records)
        self.assertEqual(len(rows), 8)
        self.assertEqual({row["event"] for row in rows}, {self.bank[3]["event"]})
        self.assertEqual(records, saved)

    def test_final_lf_only_retains_strict_failures_sources_and_provenance(self):
        records = self.records()
        for index, record in enumerate(records):
            record["event"]["raw"] = record["event"]["raw"].rstrip("\n") + ("\n\n" if index < 3 else "")
            record["accepted"] = False
            record["error"] = "not exact EVENT"
        saved = copy.deepcopy(records)
        self.assertEqual(micro.compile_rows(self.bank, records), [])
        rows = micro.compile_rows(self.bank, records, serialization="FINAL_LF_ONLY")
        self.assertEqual(len(rows), 32)
        for index, row in enumerate(rows):
            source = records[index % 4]["event"]["raw"]
            target = self.episodes[index % 4]["event_raw"]
            self.assertEqual(row["event"], self.bank[index % 4]["event"])
            self.assertEqual(row["wrapper"], f"W{index // 4}")
            self.assertEqual(row["messages"][-1]["content"], target)
            self.assertEqual(row["source_raw_sha256"], hashlib.sha256(source.encode("utf-8")).hexdigest())
            self.assertEqual(row["target_sha256"], hashlib.sha256(target.encode("utf-8")).hexdigest())
            self.assertEqual(row["serialization"], "FINAL_LF_ONLY")
        self.assertEqual(records, saved)
        for record in records:
            with self.assertRaises(ValueError):
                micro.validate_episode(record["fact"], record["exploration"]["raw"], record["event"]["raw"])

    def test_exact_serialization_preserves_row_shape(self):
        rows = micro.compile_rows(self.bank, self.records())
        self.assertEqual(rows, micro.compile_rows(self.bank, self.records(), serialization="EXACT"))
        self.assertTrue(all(set(row) == {"world", "event", "wrapper", "messages"} for row in rows))
        for mode in (None, "", "STRIP", "final_lf_only"):
            with self.assertRaises(ValueError):
                micro.compile_rows(self.bank, self.records(), serialization=mode)

    def test_canonical_event_changes_only_final_lfs(self):
        raw = self.episodes[0]["event_raw"]
        for count in (0, 1, 2, 5):
            self.assertEqual(micro.canonical_event(raw.rstrip("\n") + "\n" * count), raw)
        for invalid in (None, "", "\n", " " + raw, "\n" + raw,
                        raw.replace(" AT ", "  AT "), raw.replace(" DID ", "\nDID "),
                        raw.replace(" GOT ", "\tGOT "), raw.rstrip("\n") + "\r\n",
                        raw.rstrip("\n") + " \n", raw + "explanation\n",
                        raw.replace(self.bank[0]["event"], "E_BAD")):
            with self.subTest(raw=invalid):
                with self.assertRaises(ValueError):
                    micro.canonical_event(invalid)
                records = self.records()
                records[0]["event"]["raw"] = invalid
                rows = micro.compile_rows(self.bank, records, serialization="FINAL_LF_ONLY")
                self.assertEqual(len(rows), 24)
                self.assertNotIn(self.bank[0]["event"], {row["event"] for row in rows})

    def test_final_lf_only_does_not_repair_ids_actions_or_generation_flags(self):
        for field in ("event", "node", "port", "outcome", "receipt"):
            records = self.records()
            records[0]["event"]["raw"] = records[0]["event"]["raw"].replace(
                self.bank[0][field], self.bank[2][field]).rstrip("\n")
            self.assertEqual(len(micro.compile_rows(self.bank, records, serialization="FINAL_LF_ONLY")), 24)
        records = self.records()
        records[0]["exploration"]["raw"] += "\n"
        records[1]["event"]["terminal"] = False
        records[2]["event"]["truncated"] = True
        records[3]["event"] = None
        self.assertEqual(micro.compile_rows(self.bank, records, serialization="FINAL_LF_ONLY"), [])

    def test_goal_swap_only_changes_goal_not_lists_or_hidden_target(self):
        for offset in (0, 2):
            first, second = self.bank[offset:offset + 2]
            first_messages = micro.action_messages(first)
            second_messages = micro.action_messages(second)
            self.assertEqual(first_messages[0], second_messages[0])
            self.assertEqual(first_messages[1]["content"].replace(first["outcome"], second["outcome"]),
                             second_messages[1]["content"])
            self.assertNotEqual(micro.expected_action(first), micro.expected_action(second))
            for fact, messages in ((first, first_messages), (second, second_messages)):
                prompt = messages[1]["content"]
                self.assertNotIn(micro.expected_action(fact), prompt)
                self.assertNotIn(fact["receipt"], prompt)
                for port in fact["public_ports"]:
                    self.assertEqual(prompt.count(port), 1)
                for event in fact["public_events"]:
                    self.assertEqual(prompt.count(event), 1)

    def test_memory_is_actual_unrepaired_text_and_ceiling_is_explicit(self):
        fact = self.bank[0]
        for memory in ("MISS", "", "bad output\n", self.episodes[2]["event_raw"]):
            messages = micro.action_messages(fact, memory)
            self.assertTrue(messages[1]["content"].endswith("ACTUAL MODEL-READ TEXT\n" + memory))
            self.assertNotIn(self.episodes[0]["event_raw"], messages[1]["content"])
        pair = "".join(episode["event_raw"] for episode in self.episodes[:2])
        messages = micro.action_messages(fact, pair, ceiling=True)
        self.assertTrue(messages[1]["content"].endswith("EXACT-FACTS CEILING\n" + pair))
        native_join = "\n".join(episode["event_raw"] for episode in self.episodes[:2])
        messages = micro.action_messages(fact, native_join, ceiling=True)
        self.assertTrue(messages[1]["content"].endswith("EXACT-FACTS CEILING\n" + native_join))
        for memory in (None, "MISS", self.episodes[0]["event_raw"], pair.rstrip()):
            with self.assertRaises(ValueError):
                micro.action_messages(fact, memory, ceiling=True)

    def test_short_action_strict_grammar_and_counterfactual_scoring(self):
        for fact in self.bank:
            target = micro.expected_action(fact)
            self.assertEqual(micro.parse_action(target), fact["port"])
            wrong = next(port for port in fact["public_ports"] if port != fact["port"])
            self.assertNotEqual(micro.parse_action(f"ROUTE {wrong}\n"), fact["port"])
            for raw in (None, "", "MISS", target.rstrip(), target + "\n", " " + target,
                        target + "explanation", f"ROUTE {fact['node']} {fact['outcome']} : {fact['port']}"):
                with self.assertRaises(ValueError):
                    micro.parse_action(raw)
            with self.assertRaises(ValueError):
                pcfl.parse_route(target)


if __name__ == "__main__":
    unittest.main()
