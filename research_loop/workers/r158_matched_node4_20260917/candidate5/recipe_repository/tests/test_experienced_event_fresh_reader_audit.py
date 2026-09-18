"""Audit real reads even when the route never commits; pure captured replay."""

from copy import deepcopy
import unittest

from organism_v6 import experienced_event_fresh_reader_audit as audit
from organism_v6 import experienced_event_fresh_reader_cycle as fresh
from organism_v6 import experienced_event_microloop as micro
from organism_v6 import experienced_event_read_route as controller


def generation(raw):
    return dict(raw=raw, terminal=True, truncated=False)


class FreshAuditTests(unittest.TestCase):
    def setUp(self):
        self.bank = fresh.build_bank()
        def generate(messages):
            fact = next(fact for fact in self.bank if fact["port"] in messages[1]["content"])
            return generation("EXPLORE " + fact["node"] + " " + fact["port"] if len(messages) == 2 else micro._event(fact))
        self.collection = fresh.collect(generate)

    def routes(self, mode="invalid_route", affected=(1, 2)):
        records = []
        sources = {fact["event"]: micro._event(fact) for fact in self.bank}
        for index, fact in enumerate(self.bank):
            commands = ["READ EVENT " + address for address in fact["public_events"]]
            commands.append("ROUTE " + fact["public_ports"][0])
            if index in affected:
                foreign = self.bank[(index + 2) % 4]
                if mode == "invalid_route":
                    commands[-1] = "ROUTE " + foreign["port"]
                elif mode == "invalid_command":
                    commands[-1] = "not a command"
                elif mode == "duplicate_address":
                    commands[1] = commands[0]
                elif mode == "unsupported_address":
                    commands[-1] = "READ EVENT " + foreign["event"]
                elif mode == "no_reads":
                    commands = [commands[-1]]
            remaining = iter(commands)
            actor_calls = 0
            def actor(messages):
                nonlocal actor_calls
                actor_calls += 1
                if index in affected and actor_calls == 3:
                    if mode == "actor_error":
                        raise RuntimeError("captured actor failure")
                    if mode == "actor_invalid":
                        return None
                    if mode == "actor_nonterminal":
                        return dict(raw="ROUTE ", terminal=False, truncated=True)
                return dict(generation(next(remaining)), messages=deepcopy(messages))
            def reader(address):
                if index in affected and mode == "memory_error":
                    raise RuntimeError("captured reader failure")
                if index in affected and mode == "memory_invalid":
                    return None
                raw = sources[address] if address == fact["public_events"][0] else "MISS\n"
                if index in affected and mode == "memory_nonterminal":
                    return dict(raw=raw, terminal=False, truncated=True)
                return generation(raw)
            def transition(port):
                if index in affected and mode == "transition_error":
                    raise RuntimeError("captured transition failure")
                if index in affected and mode == "wrong_transition":
                    return foreign["outcome"]
                return next(other["outcome"] for other in self.bank if other["node"] == fact["node"] and other["port"] == port)
            episode = controller.run_episode(controller.public_task(fact), actor, reader, transition)
            records.append(dict(event=fact["event"], episode=episode))
        return records

    def test_invalid_routes_retain_all_eight_reads_without_transition(self):
        records = self.routes()
        with self.assertRaises(ValueError):
            fresh.build_cases(self.collection, records)
        original = deepcopy((self.collection, records))
        cases = audit.build_cases(self.collection, records)
        self.assertEqual(cases["schema"], "DEV_FRESH_READER_CYCLE_ACTUAL_AUDIT_V2")
        self.assertEqual((cases["actual_reader_calls"], cases["expected_calls"], cases["invalid_route_count"]), (8, 8, 2))
        self.assertEqual(cases["unavailable_readers"], [])
        for index in (1, 2):
            route = cases["route_diagnostics"][index]
            self.assertEqual(route["terminal_reason"], "invalid_route")
            self.assertEqual(route["transition_calls"], 0)
            self.assertIsNone(route["outcome"])
            self.assertIsNone(route["chosen_port"])
            self.assertEqual(route["memory_calls"], 2)
        self.assertEqual([case["episode_index"] for case in cases["cases"]], [0, 0, 1, 1, 2, 2, 3, 3])
        record = audit.collect_audit(cases, lambda messages: generation(self.bank[1]["event"]))
        self.assertEqual(record["chosen_source_indexes"], [1] * 8)
        self.assertEqual(record["row_source_indexes"], list(range(1, 32, 4)) * 8)
        self.assertEqual(record["invalid_route_count"], 2)
        self.assertEqual(original, (self.collection, records))

    def test_old_committed_prompts_captures_scores_and_origins_identical(self):
        records = self.routes(affected=())
        old_cases = fresh.build_cases(self.collection, records)
        new_cases = audit.build_cases(self.collection, records)
        for key in ("cases", "sources", "source_document_sha256", "expected_calls"):
            self.assertEqual(old_cases[key], new_cases[key])
        def generate(messages):
            return generation(self.bank[1]["event"])
        old, new = fresh.collect_audit(old_cases, generate), audit.collect_audit(new_cases, generate)
        for key in ("captures", "summary", "chosen_source_indexes", "row_source_indexes", "material_origins",
                    "correct", "denominator", "model_calls", "admitted_selections"):
            self.assertEqual(old[key], new[key], key)

    def test_other_controller_terminations_replay_without_commit_requirement(self):
        for mode in ("invalid_command", "duplicate_address", "unsupported_address", "actor_error", "actor_invalid",
                     "actor_nonterminal", "memory_error", "memory_invalid", "memory_nonterminal", "transition_error"):
            with self.subTest(mode=mode):
                records = self.routes(mode)
                cases = audit.build_cases(self.collection, records)
                self.assertEqual(cases["actual_reader_calls"], sum(record["episode"]["memory_calls"] for record in records))
                self.assertEqual(cases["actual_reader_calls"], cases["expected_calls"] + len(cases["unavailable_readers"]))
                for index in (1, 2):
                    self.assertIsNone(cases["route_diagnostics"][index]["outcome"])
                if mode in ("memory_error", "memory_invalid"):
                    self.assertEqual(len(cases["unavailable_readers"]), 2)
                    self.assertTrue(all(item["reason"] == "NO_AUDITABLE_CAPTURED_READER_TEXT" for item in cases["unavailable_readers"]))

    def test_wrong_real_transition_rejected_even_when_episode_is_coherent(self):
        with self.assertRaises(ValueError):
            audit.build_cases(self.collection, self.routes("wrong_transition"))

    def test_missing_or_fabricated_transition_never_filled_from_bank(self):
        records = self.routes(affected=())
        changed = deepcopy(records)
        changed[0]["episode"]["traces"] = [trace for trace in changed[0]["episode"]["traces"] if trace["kind"] != "transition"]
        with self.assertRaises(ValueError):
            audit.build_cases(self.collection, changed)
        changed = self.routes()
        changed[1]["episode"]["traces"].append(dict(kind="transition", port=self.bank[1]["port"],
                                                  outcome=self.bank[1]["outcome"], committed=True))
        with self.assertRaises(ValueError):
            audit.build_cases(self.collection, changed)

    def test_route_prompt_address_response_and_count_drift_rejected(self):
        records = self.routes()
        for kind in ("prompt", "address", "response", "outcome", "count", "order"):
            changed = deepcopy(records)
            episode = changed[0]["episode"]
            if kind == "prompt":
                episode["traces"][0]["messages"][0]["content"] = "changed"
            elif kind == "address":
                episode["traces"][1]["address"] = self.bank[2]["event"]
            elif kind == "response":
                episode["traces"][1]["response"]["raw"] = "forged reader"
            elif kind == "outcome":
                changed[1]["episode"]["outcome"] = self.bank[1]["outcome"]
            elif kind == "count":
                episode["memory_calls"] = 0
            else:
                changed.reverse()
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                audit.build_cases(self.collection, changed)

    def test_collection_and_case_provenance_rejected_before_audit(self):
        records = self.routes()
        changed = deepcopy(self.collection)
        changed["master"] = "other"
        with self.assertRaises(ValueError):
            audit.build_cases(changed, records)
        cases = audit.build_cases(self.collection, records)
        cases["cases"][0]["messages"][0]["content"] = "new instruction"
        with self.assertRaises(ValueError):
            audit.collect_audit(cases, lambda messages: self.fail("must not generate"))

    def test_actual_responses_replay_identically_and_failures_stay_explicit(self):
        cases = audit.build_cases(self.collection, self.routes())
        outputs = iter(["NONE", "E_ID", self.bank[0]["event"], "ADDRESS " + self.bank[1]["event"],
                        "NONE\n", self.bank[1]["event"], "NONE", "NONE"])
        record = audit.collect_audit(cases, lambda messages: generation(next(outputs)))
        self.assertEqual(record["chosen_source_indexes"], [None, None, 0, None, None, 1, None, None])
        captures = iter(record["captures"])
        def replay(messages):
            capture = next(captures)
            self.assertEqual(messages, capture["messages"])
            return deepcopy(capture["response"])
        self.assertEqual(record, audit.collect_audit(cases, replay))
        def fail(messages):
            raise RuntimeError("native inference failed")
        failed = audit.collect_audit(cases, fail)
        self.assertEqual(failed["model_calls"], 8)
        self.assertTrue(all(capture["status"] == "CALL_ERROR" for capture in failed["captures"]))

    def test_no_reads_needs_no_audit_or_invented_case(self):
        cases = audit.build_cases(self.collection, self.routes("no_reads", affected=(0, 1, 2, 3)))
        record = audit.collect_audit(cases, lambda messages: self.fail("no reads"))
        self.assertEqual((record["model_calls"], record["denominator"]), (0, 0))
        self.assertEqual(record["task_denominator"], 4)


if __name__ == "__main__":
    unittest.main()
