"""Synthetic CPU emissions through NativeActor; no native model or launch."""

import copy
from pathlib import Path
import unittest
from unittest.mock import patch

import test_astra_pcfl_native_actor as fixtures
from gpu import astra_pcfl_interface_dev as driver


class RosterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.wires = [driver.core.to_data(driver.core.build_root(f"excluded/{index}")) for index in range(4)]

    def test_all_four_rosters_use_supplied_wires_and_fixed_factorial(self):
        original = copy.deepcopy(self.wires)
        for stage, maximum in (("A1_READ_DISCLOSED", 832), ("A2_DIRECT", 64), ("A3_THINK", 448), ("ACTIVE_THINK", 1216)):
            plan = driver.build_roster(self.wires, stage)
            self.assertEqual(plan["roots"], original)
            self.assertEqual(len(plan["tasks"]), 64)
            self.assertEqual(plan["limits"]["possible_calls"], maximum)
            cases = {(task["cell"]["root"]["label"], task["cell"]["old"], task["cell"]["relevant"],
                      task["cell"]["distractor"], task["goal"]) for task in plan["tasks"]}
            self.assertEqual(len(cases), 64)
            driver.validate_roster(plan, plan["sha256"])
        self.assertEqual(self.wires, original)

    def test_exact_paired_graph_and_seeds_and_no_address_enumeration(self):
        direct = driver.build_roster(self.wires, "A2_DIRECT")
        thought = driver.build_roster(self.wires, "A3_THINK")
        active = driver.build_roster(self.wires, "ACTIVE_THINK")
        for left, right, reads in zip(direct["tasks"], thought["tasks"], active["tasks"]):
            self.assertEqual(left["messages"][1], right["messages"][1])
            self.assertEqual(left["case_id"], right["case_id"])
            self.assertEqual(left["seed"], right["seed"])
            self.assertEqual(left["source_rows"], right["source_rows"])
            self.assertNotEqual(left["slot_ids"], right["slot_ids"])
            system = reads["messages"][0]["content"]
            for command in ("READ EVENT <event_id>", "READ EVENTS_AT <node_id>", "READ LINKS_FROM <event_id>"):
                self.assertIn(command, system)
            for request in reads["queries"]:
                self.assertNotIn(request, driver.canonical(reads["messages"]).decode())
            self.assertNotIn("expected", system)
            self.assertEqual(left["queries"], {})

    def test_wrong_root_order_namespace_or_stage_rejected(self):
        for wires in (self.wires[::-1], self.wires[:3]):
            with self.assertRaises(ValueError):
                driver.build_roster(wires, "A2_DIRECT")
        with self.assertRaises(ValueError):
            driver.build_roster(self.wires, "A4_SCAFFOLD")
        changed = copy.deepcopy(self.wires)
        changed[0] = driver.core.to_data(driver.core.build_root("disposable/0"))
        with self.assertRaises(ValueError):
            driver.build_roster(changed, "A2_DIRECT")

    def test_resealed_task_or_source_change_rejected(self):
        plan = driver.build_roster(self.wires, "A2_DIRECT")
        plan["tasks"][0]["seed"] += 1
        plan = driver.seal({key: value for key, value in plan.items() if key != "sha256"})
        with self.assertRaisesRegex(ValueError, "reconstruction"):
            driver.validate_roster(plan, plan["sha256"])


class SummaryTests(unittest.TestCase):
    def rows(self):
        return [{"status": "SCORED", "reason": "ROUTE", "score": {"strict": True},
                 "success": True, "thinks": 1, "served_reads": 1, "invalid_read": False}
                for _ in range(64)]

    def test_marginal_success_and_read_counts_do_not_replace_joint_gate(self):
        rows = self.rows()
        for row in rows[:4]:
            row["success"] = False
        for row in rows[4:8]:
            row["served_reads"] = 0
        summary = driver.summarize(rows, "ACTIVE_THINK", True)
        self.assertEqual(summary["route_successes"], 60)
        self.assertEqual(summary["served_read_tasks"], 60)
        self.assertEqual(summary["active_thought_route_tasks"], 56)
        self.assertFalse(summary["stage_gate_passed"])

    def test_read_followed_by_invalid_turn_or_cap_is_not_handshake(self):
        rows = self.rows()
        for row, reason in zip(rows[:5], ["INVALID_TURN", "TURN_CAP", "ACTOR_TOKEN_CAP",
                                         "RETURNED_TOKEN_CAP", "LENGTH"]):
            row.update(reason=reason, success=False, score=None)
        summary = driver.summarize(rows, "A1_READ_DISCLOSED", True)
        self.assertEqual(summary["served_read_tasks"], 64)
        self.assertEqual(summary["read_handshake_tasks"], 59)
        self.assertFalse(summary["stage_gate_passed"])

    def test_wrong_graph_with_valid_terminal_can_pass_handshake_only(self):
        rows = self.rows()
        for row in rows:
            row["success"] = False
        self.assertTrue(driver.summarize(rows, "A1_READ_DISCLOSED", True)["stage_gate_passed"])
        self.assertFalse(driver.summarize(rows, "A3_THINK", True)["stage_gate_passed"])
        self.assertFalse(driver.summarize(rows, "A1_READ_DISCLOSED", False)["stage_gate_passed"])


class StageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.wires = RosterTests.wires if hasattr(RosterTests, "wires") else [
            driver.core.to_data(driver.core.build_root(f"excluded/{index}")) for index in range(4)]

    def setUp(self):
        self.fixture = fixtures.ActorTests("test_real_actor_public_api_captures_exact_tokens_and_bytes")
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.settings = copy.deepcopy(self.fixture.config)
        self.settings["source_files"].update(driver.source_pins())
        self.settings.update(deadline=1000.0, device_seconds_cap=900.0, max_calls=1952)
        self.tokenizer = self.fixture.session.tokenizer
        self.output = self.fixture.root / "stage"
        self.outputs = {}
        self.finishes = {}
        self.plan = None

    def prepare(self, stage="ACTIVE_THINK"):
        self.plan = driver.build_roster(self.wires, stage)
        for task in self.plan["tasks"]:
            route = driver.core.oracle_route_v1(driver.core.from_data(task["cell"]), task["goal"])
            read = next(request for request in task["queries"] if request.startswith("READ EVENTS_AT ")) if task["queries"] else None
            script = []
            if self.plan["limits"]["thinks"]:
                script.append("THINK Follow recorded transitions in order.")
            if read:
                script.append(read)
            script.append(route)
            for slot, raw in zip(task["slot_ids"], script):
                self.outputs[slot] = raw
        fixture, outputs, finishes = self.fixture, self.outputs, self.finishes
        class Scripted(driver.native.NativeActor):
            def generate(self, request, limits):
                fixture.session.text = outputs.get(request["id"], "invalid")
                fixture.session.mutate = lambda raw: {**raw, "finish_reason": finishes.get(request["id"], "stop")}
                return super().generate(request, limits)
        self.actor = Scripted(self.settings, loader=fixture.loader,
                              environment_reader=lambda: copy.deepcopy(fixture.environment), clock=fixture.clock)
        self.addCleanup(self.actor.close)
        return self.plan["tasks"][0]

    def run_stage(self, reader=driver.read_capture):
        return driver.run_stage(self.plan, self.plan["sha256"], self.actor, self.tokenizer, self.output,
                                actor_config=self.settings, deadline=900.0, receipt_reader=reader, clock=self.fixture.clock)

    def replay(self, report):
        result = driver.replay_validate(self.plan, self.plan["sha256"], report, self.tokenizer)
        self.assertTrue(result["local_replay_valid"])
        self.assertFalse(result["native_custody_verified"])

    def test_real_think_read_think_route_prefixes_and_all_denominators(self):
        first = self.prepare()
        route = self.outputs[first["slot_ids"][2]]
        self.outputs[first["slot_ids"][2]] = "THINK Continue from the observed destination."
        self.outputs[first["slot_ids"][3]] = route
        report = self.run_stage()
        self.assertEqual(report["status"], "COMPLETE")
        self.assertEqual(report["summary"]["route_successes"], 64)
        self.assertTrue(report["summary"]["stage_gate_passed"])
        self.assertEqual(report["calls"], 193)
        self.assertEqual(report["possible_calls"], 1216)
        self.assertEqual(report["results"][0]["thinks"], 2)
        attempts = report["attempts"]
        self.assertEqual(attempts[1]["request"]["messages"][-1], {"role": "user", "content": driver.CONTINUE})
        self.assertEqual(attempts[2]["request"]["messages"][-1]["content"], report["results"][0]["services"][0]["raw"])
        self.assertEqual(attempts[3]["request"]["messages"][-1]["content"], driver.CONTINUE)
        self.assertEqual(attempts[4]["request"]["messages"], self.plan["tasks"][1]["messages"])
        self.assertEqual(attempts[1]["limits"]["remaining_reads"], 12)
        self.assertEqual(attempts[2]["limits"]["remaining_reads"], 11)
        self.assertEqual(sum(slot["status"] == "UNCALLED" for row in report["results"] for slot in row["slots"]), 1216-193)
        self.assertEqual(self.fixture.session.closed, 0)
        self.assertEqual((report["fits"], report["updates"]), (0, 0))
        self.replay(report)
        with self.assertRaises(ValueError):
            self.run_stage()

    def test_three_legal_read_families_and_miss_exact_source_joins(self):
        first = self.prepare("A1_READ_DISCLOSED")
        requests = [next(request for request in first["queries"] if request.startswith(prefix))
                    for prefix in ("READ EVENT ", "READ EVENTS_AT ", "READ LINKS_FROM ")]
        requests.append("READ EVENT E_ZZZZZZZZZZ")
        route = self.outputs[first["slot_ids"][1]]
        for slot, raw in zip(first["slot_ids"], requests + [route]):
            self.outputs[slot] = raw
        report = self.run_stage()
        services = report["results"][0]["services"]
        self.assertEqual(len(services), 4)
        for service, request in zip(services, requests):
            self.assertEqual({key: service[key] for key in ("request", "raw", "source_sha256", "role")},
                             driver.core.read_query(first["queries"], request))
        self.assertEqual(services[-1]["raw"], "MISS")
        self.assertEqual(report["results"][0]["served_reads"], 3)
        self.replay(report)

    def test_raw_rejects_multiple_read_fence_and_thought_final_not_salvaged(self):
        self.prepare("A1_READ_DISCLOSED")
        bad = ["READ N_AAAAAAAAAA\nREAD N_BBBBBBBBBB", "```\nROUTE wrong\n```", "THINK reason\nROUTE wrong", "ROUTE wrong\n"]
        for task, raw in zip(self.plan["tasks"], bad):
            self.outputs[task["slot_ids"][0]] = raw
        report = self.run_stage()
        self.assertEqual(report["status"], "COMPLETE")
        for row, raw in zip(report["results"], bad):
            self.assertFalse(row["success"])
            self.assertEqual(row["raw"], raw)
            self.assertEqual(sum(slot["status"] == "RETURNED" for slot in row["slots"]), 1)
        self.assertTrue(report["results"][0]["invalid_read"])
        self.assertFalse(report["summary"]["stage_gate_passed"])
        self.replay(report)

    def test_whitespace_only_think_is_not_a_reasoning_turn(self):
        first = self.prepare("A3_THINK")
        self.outputs[first["slot_ids"][0]] = "THINK \t\u2003 "
        report = self.run_stage()
        self.assertEqual(report["results"][0]["reason"], "INVALID_TURN")
        self.assertEqual(report["results"][0]["thinks"], 0)
        self.replay(report)

    def test_think_required_and_disabled_and_no_semantic_route_rescue(self):
        first = self.prepare("A3_THINK")
        self.outputs[first["slot_ids"][0]] = self.outputs[first["slot_ids"][1]]
        task = self.plan["tasks"][1]
        self.outputs[task["slot_ids"][1]] = "ROUTE N_AAAAAAAAAA N_BBBBBBBBBB : P_CCCCCCCCCC"
        report = self.run_stage()
        self.assertEqual(report["results"][0]["reason"], "THINK_REQUIRED")
        self.assertTrue(report["results"][0]["score"]["graph_success"])
        self.assertFalse(report["results"][0]["success"])
        self.assertTrue(report["results"][1]["score"]["strict"])
        self.assertFalse(report["results"][1]["success"])
        self.replay(report)

    def test_a2_direct_never_accepts_think_or_read(self):
        self.prepare("A2_DIRECT")
        self.outputs[self.plan["tasks"][0]["slot_ids"][0]] = "THINK reason"
        self.outputs[self.plan["tasks"][1]["slot_ids"][0]] = "READ EVENTS_AT N_AAAAAAAAAA"
        report = self.run_stage()
        self.assertEqual(report["calls"], 64)
        self.assertEqual(report["results"][0]["reason"], "THINK_DISABLED_OR_CAP")
        self.assertEqual(report["results"][1]["reason"], "READ_DISABLED_OR_CAP")
        self.replay(report)

    def test_length_final_preserved_and_not_passed(self):
        first = self.prepare("A2_DIRECT")
        self.finishes[first["slot_ids"][0]] = "length"
        report = self.run_stage()
        self.assertEqual(report["results"][0]["reason"], "LENGTH")
        self.assertFalse(report["results"][0]["success"])
        self.assertEqual(report["results"][0]["raw"], self.outputs[first["slot_ids"][0]])
        self.replay(report)

    def test_think_and_read_caps_no_forced_extra_answer(self):
        first = self.prepare("ACTIVE_THINK")
        for slot in first["slot_ids"]:
            self.outputs[slot] = "THINK keep thinking"
        second = self.plan["tasks"][1]
        for slot in second["slot_ids"]:
            self.outputs[slot] = "READ EVENT E_ZZZZZZZZZZ"
        report = self.run_stage()
        self.assertEqual(report["results"][0]["thinks"], 6)
        self.assertEqual(report["results"][0]["reason"], "THINK_DISABLED_OR_CAP")
        self.assertEqual(report["results"][1]["reads"], 12)
        self.assertEqual(report["results"][1]["reason"], "READ_DISABLED_OR_CAP")
        self.replay(report)

    def test_maximum_nineteen_turns_and_budget_not_reset_by_think(self):
        first = self.prepare()
        route = self.outputs[first["slot_ids"][2]]
        script = ["THINK reason"] * 6 + ["READ EVENT E_ZZZZZZZZZZ"] * 12 + [route]
        for slot, raw in zip(first["slot_ids"], script):
            self.outputs[slot] = raw
        report = self.run_stage()
        self.assertTrue(report["results"][0]["success"])
        self.assertEqual(sum(slot["status"] == "RETURNED" for slot in report["results"][0]["slots"]), 19)
        self.assertEqual(report["results"][0]["actor_tokens"], sum(len(raw) for raw in script))
        self.assertEqual(report["results"][0]["returned_tokens"], 12 * len("MISS"))
        self.replay(report)

    def test_replay_rejects_service_or_attempt_or_extra_slot_tampering(self):
        self.prepare()
        report = self.run_stage()
        changes = [lambda value: value["results"][0]["services"][0].update(raw="teacher repaired"),
                   lambda value: value["attempts"][0]["request"]["messages"][-1].update(content="answer leaked"),
                   lambda value: value["attempts"].append(copy.deepcopy(value["attempts"][0]))]
        for change in changes:
            altered = copy.deepcopy(report)
            change(altered)
            altered = driver.seal({key: value for key, value in altered.items() if key != "sha256"})
            with self.assertRaises((ValueError, StopIteration)):
                self.replay(altered)

    def test_cumulative_actor_cap_stops_at_2048_without_extra_final_call(self):
        first = self.prepare()
        class PaddedTokenizer(fixtures.Tokenizer):
            def encode(self, text, add_special_tokens=False):
                ids = super().encode(text, add_special_tokens)
                if text.startswith(("THINK ", "READ ")):
                    ids += [0] * (256 - len(ids))
                return ids

            def decode(self, ids, skip_special_tokens=True):
                return super().decode([token for token in ids if token != 0], skip_special_tokens)
        self.tokenizer = self.fixture.session.tokenizer = PaddedTokenizer(self.fixture.model)
        script = ["THINK reason"] * 6 + ["READ EVENT E_ZZZZZZZZZZ"] * 2
        for slot, raw in zip(first["slot_ids"], script):
            self.outputs[slot] = raw
        report = self.run_stage()
        row = report["results"][0]
        self.assertEqual(row["actor_tokens"], 2048)
        self.assertEqual(row["reason"], "ACTOR_TOKEN_CAP")
        self.assertEqual(sum(slot["status"] == "RETURNED" for slot in row["slots"]), 8)
        self.assertEqual(row["slots"][8]["status"], "UNCALLED")
        self.assertTrue(all(attempt["limits"]["output_tokens"] <= 256 for attempt in report["attempts"]))
        self.replay(report)

    def test_returned_cap_records_undelivered_block_without_inserting_it(self):
        first = self.prepare("A1_READ_DISCLOSED")
        query = self.outputs[first["slot_ids"][0]]
        block = first["queries"][query]["target"]
        class PaddedTokenizer(fixtures.Tokenizer):
            def encode(self, text, add_special_tokens=False):
                ids = super().encode(text, add_special_tokens)
                if text == block:
                    ids += [0] * (4097 - len(ids))
                return ids
        self.tokenizer = self.fixture.session.tokenizer = PaddedTokenizer(self.fixture.model)
        report = self.run_stage()
        row = report["results"][0]
        self.assertEqual(row["reason"], "RETURNED_TOKEN_CAP")
        self.assertEqual(row["returned_tokens"], 0)
        self.assertFalse(row["services"][0]["delivered"])
        self.assertEqual(row["services"][0]["raw"], block)
        self.assertEqual(row["slots"][1]["status"], "UNCALLED")
        self.replay(report)

    def test_capture_join_failure_aborts_stage_and_preserves_raw(self):
        self.prepare("A2_DIRECT")
        def reader(directory, index):
            capture = driver.read_capture(directory, index)
            capture["files"]["call_0000.raw.json"]["sha256"] = "0" * 64
            return capture
        report = self.run_stage(reader)
        self.assertEqual(report["status"], "FAILED")
        self.assertEqual(report["calls"], 1)
        self.assertEqual(report["results"][0]["status"], "ABORTED")
        self.assertEqual(report["results"][1]["status"], "UNCALLED")
        self.assertIsNotNone(report["attempts"][0]["response"])
        self.assertTrue((self.output / "attempt_0000.json").exists())
        self.replay(report)

    def test_backend_error_preserved_no_retry_remaining_tasks_uncalled(self):
        self.prepare("A2_DIRECT")
        with patch.object(self.actor, "generate", side_effect=RuntimeError("injected backend failure")) as generate:
            report = self.run_stage()
        generate.assert_called_once()
        self.assertEqual(report["status"], "FAILED")
        self.assertEqual(report["attempts"][0]["error"]["message"], "injected backend failure")
        self.assertEqual(sum(row["status"] == "UNCALLED" for row in report["results"]), 63)
        self.replay(report)

    def test_missing_source_pin_prevents_any_generation(self):
        self.prepare("A2_DIRECT")
        del self.settings["source_files"][str(Path(driver.__file__).resolve())]
        with self.assertRaisesRegex(ValueError, "source pins"):
            self.run_stage()
        self.assertFalse(self.output.exists())
        self.fixture.loader.assert_not_called()

    def test_input_cap_is_failure_without_truncation_or_call(self):
        self.prepare("A2_DIRECT")
        self.settings["max_input_tokens"] = 10
        report = self.run_stage()
        self.assertEqual(report["status"], "COMPLETE")
        self.assertEqual(report["calls"], 0)
        self.assertTrue(all(row["reason"] == "INPUT_TOKEN_CAP" for row in report["results"]))
        self.assertFalse(report["summary"]["stage_gate_passed"])
        self.replay(report)

    def test_deadline_exhaustion_aborts_without_generation(self):
        self.prepare("A2_DIRECT")
        self.fixture.clock.now = 900.0
        report = self.run_stage()
        self.assertEqual(report["status"], "FAILED")
        self.assertEqual(report["calls"], 0)
        self.fixture.loader.assert_not_called()
        self.replay(report)


if __name__ == "__main__":
    unittest.main()
