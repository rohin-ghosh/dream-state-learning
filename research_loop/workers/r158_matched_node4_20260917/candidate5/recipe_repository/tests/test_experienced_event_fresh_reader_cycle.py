"""Pure captured A3 collection, route replay and actual-reader audit tests."""

from copy import deepcopy
import unittest

from organism_v6 import experienced_event_actual_reader_audit as actual
from organism_v6 import experienced_event_adult_cycle as adult
from organism_v6 import experienced_event_fresh_reader_cycle as fresh
from organism_v6 import experienced_event_microloop as micro
from organism_v6 import experienced_event_read_route as controller


def generation(raw, **extra):
    return dict(raw=raw, terminal=True, truncated=False, **extra)


class FreshCycleTests(unittest.TestCase):
    def setUp(self):
        self.bank = fresh.build_bank()

    def generate(self, messages):
        fact = next(fact for fact in self.bank if fact["port"] in messages[1]["content"])
        raw = "EXPLORE " + fact["node"] + " " + fact["port"] if len(messages) == 2 else micro._event(fact)
        return generation(raw, messages=deepcopy(messages))

    def fixture(self, no_reads=False, false_transition=False):
        collection = fresh.collect(self.generate)
        sources = {fact["event"]: micro._event(fact) for fact in self.bank}
        records = []
        for fact in self.bank:
            commands = [] if no_reads else ["READ EVENT " + address for address in fact["public_events"]]
            commands = iter(commands + ["ROUTE " + fact["public_ports"][0]])

            def actor(messages):
                return generation(next(commands), messages=deepcopy(messages))

            def reader(address):
                raw = sources[address] if address == fact["public_events"][0] else "MISS\n"
                return generation(raw, private_score="SECRET_METADATA")

            transitions = {other["port"]: other["outcome"] for other in self.bank if other["node"] == fact["node"]}
            episode = controller.run_episode(controller.public_task(fact), actor, reader,
                (lambda port: self.bank[3]["outcome"]) if false_transition else transitions.__getitem__)
            records.append(dict(event=fact["event"], episode=episode))
        return collection, records

    def test_fixed_bank_disjoint_from_prior_and_reserved_banks(self):
        self.assertEqual(fresh.MASTER, "ASTRA-READER-AUDIT-CONTINUATION-20260914-A3")
        self.assertEqual(self.bank, micro.build_bank(fresh.MASTER))
        others = [micro.build_bank(adult.source.MASTER), adult.build_bank(1), adult.build_bank(2),
                  *adult.collector.training_banks(), micro.build_bank(adult.source.MASTER + "-UNSEEN-MISS")]
        others.extend(micro.build_bank(adult.cue_sleep.HELD_MASTER + "-" + str(index)) for index in range(2))
        for bank in others:
            self.assertFalse(adult._identities(self.bank) & adult._identities(bank))

    def test_complete_collection_exact_prompt_receipt_roles_and_replay(self):
        record = fresh.collect(self.generate)
        self.assertEqual((record["count"], record["accepted_events"], len(record["rows"])), (8, 4, 32))
        self.assertEqual(record["schema"], fresh.SCHEMA)
        self.assertNotIn("cycle", record)
        self.assertEqual(record["master"], fresh.MASTER)
        self.assertEqual(record["serialization"], "FINAL_LF_ONLY")
        self.assertFalse(record["clean_claim"] or record["parent_present"])
        self.assertTrue(record["new_material"])
        self.assertEqual(record["fits"], 0)
        for index, fact in enumerate(self.bank):
            explore, event = record["captures"][2 * index:2 * index + 2]
            self.assertEqual(explore["messages"], micro.exploration_messages(fact))
            self.assertNotIn(fact["receipt"], str(explore["messages"]))
            self.assertEqual(event["messages"], micro.observation_messages(fact, explore["response"]["raw"]))
            self.assertIn(fact["receipt"], event["messages"][-1]["content"])
        for row in record["rows"]:
            self.assertEqual([message["role"] for message in row["messages"]], ["system", "user", "assistant"])
            self.assertEqual(row["messages"][0]["content"], micro.MEMORY_SYSTEM)
        original = deepcopy(record)
        self.assertEqual(fresh.replay_collection(record), record["rows"])
        self.assertEqual(record, original)
        with self.assertRaises(ValueError):
            adult.replay_collection(record)

    def test_final_lf_only_preserves_raw_but_normalizes_training_rows(self):
        for suffix in ("", "\n", "\n\n"):
            def generate(messages):
                response = self.generate(messages)
                if len(messages) == 4:
                    response["raw"] = response["raw"].rstrip("\n") + suffix
                return response
            record = fresh.collect(generate)
            self.assertEqual(record["accepted_events"], 4)
            self.assertEqual(fresh.replay_collection(record), record["rows"])
            self.assertEqual(record["episodes"][0]["event"]["raw"], micro._event(self.bank[0]).rstrip("\n") + suffix)
        def wrong_whitespace(messages):
            response = self.generate(messages)
            if len(messages) == 4:
                response["raw"] += " "
            return response
        record = fresh.collect(wrong_whitespace)
        self.assertEqual(record["rows"], [])
        self.assertEqual(fresh.replay_collection(record), [])

    def test_one_bad_event_retains_all_four_attempts_no_partial_rows(self):
        def generate(messages):
            response = self.generate(messages)
            if len(messages) == 4 and self.bank[1]["receipt"] in messages[-1]["content"]:
                response["raw"] = micro._event(self.bank[0])
            return response
        record = fresh.collect(generate)
        self.assertEqual((record["count"], record["accepted_events"], len(record["episodes"])), (8, 3, 4))
        self.assertEqual(record["episodes"][1]["event"]["raw"], micro._event(self.bank[0]))
        self.assertEqual(record["infrastructure_failures"], 0)
        self.assertEqual(fresh.replay_collection(record), [])
        with self.assertRaises(ValueError):
            fresh.build_cases(record, [])

    def test_cuda_callback_failures_are_retained_not_policy_failures(self):
        def fail(messages):
            raise RuntimeError("CUDA unavailable")
        record = fresh.collect(fail)
        self.assertEqual((record["count"], len(record["episodes"]), record["infrastructure_failures"]), (4, 4, 4))
        self.assertTrue(all(capture["error"] == dict(type="RuntimeError", message="CUDA unavailable") for capture in record["captures"]))
        self.assertEqual(fresh.replay_collection(record), [])

    def test_event_callback_failure_retains_eight_calls(self):
        def generate(messages):
            if len(messages) == 4:
                raise RuntimeError("event inference failed")
            return self.generate(messages)
        record = fresh.collect(generate)
        self.assertEqual((record["count"], record["infrastructure_failures"]), (8, 4))
        self.assertEqual(fresh.replay_collection(record), [])

    def test_nonterminal_or_malformed_generation_is_not_admitted(self):
        for response in (None, "EVENT", dict(raw="bad", terminal=False, truncated=True)):
            record = fresh.collect(lambda messages: deepcopy(response))
            self.assertEqual(record["accepted_events"], 0)
            self.assertEqual(record["infrastructure_failures"], 0)
            self.assertEqual(fresh.replay_collection(record), [])

    def test_replay_rejects_provenance_prompt_target_and_capture_drift(self):
        record = fresh.collect(self.generate)
        for key, value in (("master", adult.SECOND_MASTER), ("schema", adult.SCHEMA), ("fits", 1),
                           ("accepted_events", 3), ("bank", adult.build_bank(2)), ("captures", record["captures"][:-1])):
            changed = deepcopy(record)
            changed[key] = value
            with self.assertRaises(ValueError):
                fresh.replay_collection(changed)
        for target in ("prompt", "output", "row"):
            changed = deepcopy(record)
            if target == "prompt":
                changed["captures"][0]["messages"][0]["content"] = "teacher"
            elif target == "output":
                changed["captures"][1]["response"]["raw"] = "NONE"
            else:
                changed["rows"][0]["messages"][-1]["content"] = "forged"
            with self.assertRaises(ValueError):
                fresh.replay_collection(changed)

    def test_build_cases_exact_existing_audit_messages_and_source_mapping(self):
        collection, records = self.fixture()
        original = deepcopy((collection, records))
        bundle = fresh.build_cases(collection, records)
        self.assertEqual(bundle["expected_calls"], 8)
        self.assertEqual(bundle["schema"], fresh.AUDIT_SCHEMA)
        self.assertEqual(bundle["source_document_sha256"], dict(collection=fresh.document_sha256(collection),
                                                              route_records=fresh.document_sha256(records)))
        table = "".join(micro._event(fact) for fact in self.bank)
        for case in bundle["cases"]:
            self.assertEqual(case["messages"], [dict(role="system", content=actual.SYSTEM), dict(role="user", content=
                actual.SKIN + "\nREQUESTED EVENT: " + case["address"] + "\nRECEIPT-GROUNDED SOURCE TABLE\n" + table
                + "UNTRUSTED READER REPLY\n" + case["reader_raw"])])
            self.assertNotIn("SECRET_METADATA", str(case["messages"]))
            self.assertNotIn("reached_goal", str(case["messages"]))
            self.assertNotIn("PARENT", str(case["messages"]))
        self.assertEqual([case["kind"] for case in bundle["cases"]], ["true", "fault"] * 4)
        for source in bundle["sources"]:
            self.assertEqual(source["row_source_indexes"], list(range(source["source_index"], 32, 4)))
        self.assertEqual(original, (collection, records))

    def test_receipt_provenance_uses_capture_even_without_response_messages(self):
        def generate(messages):
            response = self.generate(messages)
            response.pop("messages")
            return response
        collection = fresh.collect(generate)
        unused, records = self.fixture()
        bundle = fresh.build_cases(collection, records)
        for source in bundle["sources"]:
            self.assertIn(self.bank[source["source_index"]]["receipt"], source["receipt"])

    def test_wrong_transition_even_coherently_replayed_is_rejected(self):
        collection, records = self.fixture(false_transition=True)
        with self.assertRaisesRegex(ValueError, "actual_transition_disagrees"):
            fresh.build_cases(collection, records)

    def test_missing_reordered_and_tampered_routes_rejected(self):
        collection, records = self.fixture()
        for changed in (records[:-1], list(reversed(records))):
            with self.assertRaises(ValueError):
                fresh.build_cases(collection, changed)
        changed = deepcopy(records)
        changed[0]["episode"]["traces"][0]["messages"][0]["content"] = "modified"
        with self.assertRaises(ValueError):
            fresh.build_cases(collection, changed)

    def test_wrong_duplicate_pointers_remain_admitted_and_replay_exactly(self):
        bundle = fresh.build_cases(*self.fixture())
        record = fresh.collect_audit(bundle, lambda messages: generation(self.bank[1]["event"], messages=deepcopy(messages)))
        self.assertEqual(record["chosen_source_indexes"], [1] * 8)
        self.assertEqual(record["admitted_selections"], 8)
        self.assertLess(record["correct"], 8)
        self.assertEqual(record["row_source_indexes"], list(range(1, 32, 4)) * 8)
        self.assertEqual(len(record["material_origins"]), 64)
        captures = iter(record["captures"])
        def replay(messages):
            capture = next(captures)
            self.assertEqual(messages, capture["messages"])
            return deepcopy(capture["response"])
        self.assertEqual(record, fresh.collect_audit(bundle, replay))
        self.assertIsNone(next(captures, None))
        self.assertFalse(record["parent_present"])
        self.assertEqual(record["fits"], 0)

    def test_exact_correct_classifier_scores_true_and_fault(self):
        bundle = fresh.build_cases(*self.fixture())
        outputs = iter(case["expected"] + "\n" for case in bundle["cases"])
        record = fresh.collect_audit(bundle, lambda messages: generation(next(outputs)))
        self.assertEqual(record["summary"], dict(overall=dict(correct=8, denominator=8),
                                               true=dict(correct=4, denominator=4), fault=dict(correct=4, denominator=4)))
        self.assertEqual(record["admitted_selections"], 4)

    def test_invalid_choices_none_and_nonterminal_are_never_repaired(self):
        bundle = fresh.build_cases(*self.fixture())
        outputs = iter([generation("ADDRESS " + self.bank[0]["event"]), generation("E_ID\n"),
                        generation("NONE"), generation(self.bank[0]["event"] + "\n\n"),
                        dict(raw=self.bank[0]["event"], terminal=False, truncated=True), None,
                        generation(micro._event(self.bank[0])), generation(self.bank[0]["event"], messages=[])])
        record = fresh.collect_audit(bundle, lambda messages: next(outputs))
        self.assertEqual(record["chosen_source_indexes"], [None] * 8)
        self.assertEqual(record["row_source_indexes"], [])
        self.assertEqual([capture["status"] for capture in record["captures"]],
            ["INVALID_POINTER", "INVALID_POINTER", "NONE", "INVALID_POINTER", "NONTERMINAL_OR_TRUNCATED",
             "MALFORMED_RESPONSE", "INVALID_POINTER", "RESPONSE_PROMPT_DRIFT"])

    def test_audit_callback_errors_retained_and_replayed(self):
        bundle = fresh.build_cases(*self.fixture())
        def fail(messages):
            raise RuntimeError("native CUDA failure")
        record = fresh.collect_audit(bundle, fail)
        self.assertEqual(record["model_calls"], 8)
        self.assertTrue(all(capture["status"] == "CALL_ERROR" for capture in record["captures"]))
        self.assertEqual(record["captures"][0]["error"], dict(type="RuntimeError", message="native CUDA failure"))
        self.assertEqual(record, fresh.collect_audit(bundle, fail))

    def test_rehashed_case_tampering_rejected_before_any_callback(self):
        bundle = fresh.build_cases(*self.fixture())
        for key, value in (("expected_calls", 9), ("master", adult.SECOND_MASTER), ("schema", actual.SCHEMA)):
            changed = deepcopy(bundle)
            changed[key] = value
            changed.pop("cases_sha256")
            changed = actual._seal(changed, "cases_sha256")
            with self.assertRaises(ValueError):
                fresh.collect_audit(changed, lambda messages: self.fail("must not call"))
        changed = deepcopy(bundle)
        changed["cases"][0]["messages"][0]["content"] = "changed system"
        with self.assertRaises(ValueError):
            fresh.collect_audit(changed, lambda messages: self.fail("must not call"))

    def test_no_reads_no_calls_no_substitute(self):
        bundle = fresh.build_cases(*self.fixture(no_reads=True))
        record = fresh.collect_audit(bundle, lambda messages: self.fail("no reads"))
        self.assertEqual((record["model_calls"], record["denominator"], record["admitted_selections"]), (0, 0, 0))
        self.assertEqual(record["chosen_source_indexes"], [])
        self.assertEqual(record["task_denominator"], 4)


if __name__ == "__main__":
    unittest.main()
