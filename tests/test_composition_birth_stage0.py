"""Authored CPU checks only; no model or training authorization."""

from dataclasses import replace
from itertools import combinations
import unittest

from organism_v6 import composition_birth_stage0 as source


class CompositionBirthStage0Test(unittest.TestCase):
    def setUp(self):
        self.tasks = source.generate()
        self.task = self.tasks[0]

    def test_deterministic_authored_causal_twins(self):
        self.assertEqual(self.tasks, source.generate())
        self.assertEqual(len(self.tasks), 32)
        self.assertEqual(len({task.world_id for task in self.tasks}), 16)
        self.assertEqual(len({task.structure_id for task in self.tasks}), 16)
        inventories = []
        for first, second in zip(self.tasks[::2], self.tasks[1::2]):
            self.assertEqual(first.events, second.events)
            self.assertEqual(first.start, second.start)
            self.assertNotEqual(first.goal, second.goal)
            self.assertEqual(first.provenance, source.PROVENANCE)
            self.assertEqual(first.domain, "tiny_interface_dev")
            inventories.append({value for event in first.events for value in
                                (event.event, event.source, event.port,
                                 event.destination, event.receipt)})
        for first, second in combinations(inventories, 2):
            self.assertFalse(first & second)

    def test_reserved_train_dev_test_and_writer_domains_fail_closed(self):
        for domain in source.DISABLED_DOMAINS:
            with self.subTest(domain=domain), self.assertRaisesRegex(ValueError, "disabled"):
                source.generate(domain)
        with self.assertRaisesRegex(ValueError, "unknown_domain"):
            source.generate("arbitrary_reseed")

    def test_no_secret_prompt_exposure(self):
        for task in self.tasks:
            self.assertEqual(task.prompt,
                             f"START {task.start}\nGOAL {task.goal}\nCURRENT {task.start}\n")
            self.assertNotIn(task.world_id, task.prompt)
            self.assertNotIn(task.structure_id, task.prompt)
            for event in task.events:
                for secret in (event.event, event.port, event.receipt):
                    self.assertNotIn(secret, task.prompt)
                for node in (event.source, event.destination):
                    if node not in (task.start, task.goal):
                        self.assertNotIn(node, task.prompt)
            changed = replace(task, events=tuple(reversed(task.events)))
            self.assertEqual(changed.prompt, task.prompt)
            self.assertEqual(source.Session(task).receipts, [])

    def test_exact_passive_memory_and_miss(self):
        memory = source.ExactMemory(self.task.events)
        for event in self.task.events:
            self.assertEqual(memory.read(f"READ EVENT {event.event}\n"), event.raw)
            self.assertEqual(memory.read(f"READ LINKS_FROM {event.event}\n"), "MISS")
        expected = "".join(event.raw for event in self.task.events
                           if event.source == self.task.start)
        self.assertEqual(memory.read(f"READ EVENTS_AT {self.task.start}\n"), expected)
        foreign = self.tasks[2].events[0]
        self.assertEqual(memory.read(f"READ EVENT {foreign.event}\n"), "MISS")
        self.assertEqual(memory.read(f"READ EVENTS_AT {self.task.goal}\n"), "MISS")
        self.assertEqual(source.parse_events(expected), tuple(
            event for event in self.task.events if event.source == self.task.start))
        with self.assertRaises(ValueError):
            memory.read("STOP\n")

    def test_oracle_all_tasks_receipts_and_exact_stop(self):
        self.assertEqual(source.evaluate(self.tasks), 32)
        for task in self.tasks:
            session = source.Session(task)
            source.scripted_oracle(task.start, task.goal, session.turn)
            self.assertTrue(session.success)
            self.assertEqual(dict(session.counts), {"READ": 3, "STEP": 2, "STOP": 1})
            self.assertEqual(session.current, task.goal)
            self.assertEqual(len(session.receipts), 6)
            self.assertEqual(session.receipts[-1], ("STOP\n", ""))
            for request, response in session.receipts:
                if request.startswith("READ"):
                    self.assertEqual(response, source.ExactMemory(task.events).read(request))
                if request.startswith("STEP"):
                    self.assertTrue(response.startswith("CURRENT N_"))
                    self.assertEqual(len(response.splitlines()), 1)
            with self.assertRaisesRegex(ValueError, "session_terminated"):
                session.turn("STOP\n", generated_tokens=1)

    def test_arrival_without_stop_is_not_success(self):
        session = source.Session(self.task)
        def without_stop(raw, *, generated_tokens):
            if raw == "STOP\n":
                return ""
            return session.turn(raw, generated_tokens=generated_tokens)
        source.scripted_oracle(self.task.start, self.task.goal, without_stop)
        self.assertEqual(session.current, self.task.goal)
        self.assertFalse(session.success)
        self.assertFalse(session.terminated)

    def test_static_grammar_and_invalid_actions_terminate_without_repair(self):
        malformed = ("STOP", "STOP\n\n", " STOP\n", "STOP \n", "STOP\r\n",
                     "STOP\nTHINK repair\n", "THINK \n", "THINK \t\n",
                     "READ EVENTS_AT N_short\n", "DREAM something\n", None)
        for raw in malformed:
            with self.subTest(raw=raw):
                session = source.Session(self.task)
                session.turn(raw, generated_tokens=1)
                self.assertEqual(session.reason, "malformed_action")
                self.assertEqual(session.current, self.task.start)
                self.assertEqual(session.receipts, [])
                with self.assertRaises(ValueError):
                    session.turn("STOP\n", generated_tokens=1)
        raw = "STEP " + self.tasks[2].events[0].port + "\n"
        self.assertEqual(source.parse_action(raw)[0], "STEP")
        session = source.Session(self.task)
        session.turn(raw, generated_tokens=1)
        self.assertEqual(session.reason, "invalid_step")
        self.assertEqual(session.current, self.task.start)

    def test_miss_is_valid_but_premature_stop_fails(self):
        session = source.Session(self.task)
        self.assertEqual(session.turn(f"READ EVENTS_AT {self.task.goal}\n", generated_tokens=1), "MISS")
        self.assertFalse(session.terminated)
        session.turn("STOP\n", generated_tokens=1)
        self.assertEqual(session.reason, "premature_stop")
        self.assertFalse(session.success)

    def test_exact_budget_boundaries(self):
        for operation, limit in (("THINK", 4), ("READ", 3)):
            session = source.Session(self.task)
            raw = "THINK inspect\n" if operation == "THINK" else f"READ EVENTS_AT {self.task.start}\n"
            for _ in range(limit):
                session.turn(raw, generated_tokens=1)
                self.assertFalse(session.terminated)
            session.turn(raw, generated_tokens=1)
            self.assertEqual(session.reason, "over_budget")
            self.assertEqual(len(session.receipts), limit)
        session = source.Session(self.task)
        session.turn("THINK inspect\n", generated_tokens=source.TOKEN_CAP)
        self.assertFalse(session.terminated)
        session.turn("STOP\n", generated_tokens=1)
        self.assertEqual(session.reason, "over_budget")
        for value in (-1, 0, True, 1.5, None):
            session = source.Session(self.task)
            session.turn("STOP\n", generated_tokens=value)
            self.assertEqual(session.reason, "invalid_token_accounting")
        session = source.Session(self.task)
        session.turn("THINK complete-looking\n", generated_tokens=1, truncated=True)
        self.assertEqual(session.reason, "length_limited")
        self.assertEqual(session.receipts, [])
        session = source.Session(self.task)
        def without_stop(raw, *, generated_tokens):
            if raw == "STOP\n":
                return ""
            return session.turn(raw, generated_tokens=generated_tokens)
        source.scripted_oracle(self.task.start, self.task.goal, without_stop)
        session.turn(f"STEP {self.task.events[0].port}\n", generated_tokens=1)
        self.assertEqual(session.reason, "over_budget")

    def test_core_is_computed_and_rejects_topology_mutation(self):
        core = source.decision_core(self.task)
        self.assertEqual(core, source.decision_core(replace(
            self.task, events=tuple(reversed(self.task.events)))))
        self.assertNotEqual(core["goal_role"], source.decision_core(self.tasks[1])["goal_role"])
        changed = replace(self.task.events[-1], destination=self.task.start)
        with self.assertRaisesRegex(ValueError, "not_tiny"):
            source.decision_core(replace(self.task, events=self.task.events[:-1] + (changed,)))

    def test_nulls_run_and_ambiguous_shortcuts_cannot_certify_gate(self):
        report = source.source_report()
        self.assertEqual(report, source.source_report())
        self.assertEqual(report["oracle_successes"], 32)
        self.assertEqual(report["null_diagnostic_successes"]["constant_action"], 0)
        for name in source.NULL_NAMES[1:7]:
            self.assertEqual(report["null_diagnostic_successes"][name], 16)
        self.assertEqual(report["nulls_over_half"], ["fixed_read_schedule", "fixed_stop_depth"])
        for name in report["nulls_over_half"]:
            self.assertEqual(report["null_diagnostic_successes"][name], 32)
        self.assertEqual(len(report["disabled_pairwise_nulls"]), 36)
        self.assertEqual(report["goal_side_counts"], {0: 16, 1: 16})
        self.assertEqual(report["crossing_counts"], [{0: 16, 1: 16}] * 4)
        self.assertEqual(report["status"], "NO_GO_PARTIAL_SOURCE_ONLY")
        self.assertFalse(report["launch_authorized"])
        self.assertFalse(report["registered_null_suite_complete"])
        self.assertEqual(report["birth_units_emitted"], 0)
        self.assertEqual(report["cross_domain_intersections"], "UNVERIFIED_NOT_MATERIALIZED")
        self.assertEqual(report["forbidden_motif_overlap"], "UNVERIFIED")
        for task, manifest in zip(self.tasks, report["manifests"]):
            self.assertEqual(manifest["prompt_bytes"], len(task.prompt.encode()))
            self.assertEqual(manifest["row_bytes"], sum(len(event.raw.encode()) for event in task.events))
            self.assertEqual(manifest["rooted_depth_one_signatures"], [[1, 0], [1, 0]])


if __name__ == "__main__":
    unittest.main()
