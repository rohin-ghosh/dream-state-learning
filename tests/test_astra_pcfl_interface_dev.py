"""Synthetic CPU emissions through NativeActor; no native model or launch."""

import copy
from pathlib import Path
import re
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

    def test_old_roster_bytes_unchanged_except_required_source_repin(self):
        snapshots = {
            "A1_READ_DISCLOSED": "b9b1cdac002c41c1703b4a75fd2141f3e7baa9c9547d428f422f38eb892042f0",
            "A2_DIRECT": "128a0cb53fdd719b15b6316196d4837ddfb2e17489ac1da38646ca6166907ad1",
            "A3_THINK": "6f6dbfc8b3d7cb2789eb3800e711e884e690cf2e155fec104e9b6cae981fa76f",
            "ACTIVE_THINK": "a5c03d367b1520a494b8bdfb2ba8fbd9eff9f43647b3d338235be583d2c76fa3",
            "READ_REQUIRED_SMOKE": "0acea68facad2f4e120225530e49cdeb27ae61f50be5f529b9661cd71a5644ee",
            "READ_REQUIRED_PANEL": "985c0cd62e44c2f2a9727e8db294193acdbe7ba945ad13e435e9f4bbbe4770e3",
            "STRUCTURED_ACTION_SMOKE": "38cfb40f9b8388b7deeae0b63f84561696a8486433b47645ade311b5e86d32d5",
            "STRUCTURED_FIRST_READ_SMOKE": "3c0db7783cf32f9ecc548f1ae89aa419a787e140217c0ca9f1decdea7a5e735b",
            "A3B_NEWLINE_FRAMED_SMOKE": "9a6bbc7c0ba9decf9a380b3d78343b50f14dc0fd7c140913fd2bb02ad2485980",
        }
        with patch.object(driver, "source_pins", return_value={}):
            for stage, checksum in snapshots.items():
                self.assertEqual(driver.build_roster(self.wires, stage)["sha256"], checksum)

    def test_required_read_rosters_change_only_instruction_and_stage_identity(self):
        original = driver.build_roster(self.wires, "A1_READ_DISCLOSED")
        instruction = ("Before any ROUTE, you must issue at least one READ. Use only the public START\n"
                       "and exact identifiers returned by memory; never invent a READ address.")
        for stage, indices in (("READ_REQUIRED_SMOKE", (0, 1, 16, 17, 32, 33, 48, 49)),
                               ("READ_REQUIRED_PANEL", tuple(range(64)))):
            with self.subTest(stage=stage):
                roster = driver.build_roster(self.wires, stage)
                self.assertEqual(roster["roots"], self.wires)
                self.assertEqual(roster["sources"], driver.source_pins())
                expected_limits = {**original["limits"], "possible_calls": len(indices) * 13}
                self.assertEqual(roster["limits"], expected_limits)
                expected = copy.deepcopy([original["tasks"][index] for index in indices])
                for task in expected:
                    task["id"] = f"interface/{stage}/{task['case_id']}"
                    task["slot_ids"] = [f"{driver.core.byte_hash(task['id'])}/actor/{turn}" for turn in range(13)]
                    task["messages"][0]["content"] += "\n" + instruction
                self.assertEqual(roster["tasks"], expected)
                driver.validate_roster(roster, roster["sha256"])
                for task in roster["tasks"]:
                    for request in task["queries"]:
                        self.assertNotIn(request, driver.canonical(task["messages"]).decode())

    def test_required_smoke_selection_or_instruction_drift_rejected(self):
        original = driver.build_roster(self.wires, "READ_REQUIRED_SMOKE")
        for change in ("selection", "instruction", "source"):
            altered = copy.deepcopy(original)
            if change == "selection":
                altered["tasks"][0], altered["tasks"][2] = altered["tasks"][2], altered["tasks"][0]
            elif change == "instruction":
                altered["tasks"][0]["messages"][0]["content"] += " Use a useful address."
            else:
                altered["sources"].pop(str(Path(driver.__file__).resolve()))
            altered = driver.seal({key: value for key, value in altered.items() if key != "sha256"})
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, "reconstruction"):
                driver.validate_roster(altered, altered["sha256"])

    def test_structured_smokes_preserve_prompt_cases_seeds_and_caps(self):
        baseline = driver.build_roster(self.wires, "READ_REQUIRED_SMOKE")
        for stage in driver.STRUCTURED_STAGES:
            roster = driver.build_roster(self.wires, stage)
            expected = copy.deepcopy(baseline["tasks"])
            for task in expected:
                task["id"] = f"interface/{stage}/{task['case_id']}"
                task["slot_ids"] = [f"{driver.core.byte_hash(task['id'])}/actor/{turn}" for turn in range(13)]
            self.assertEqual(roster["tasks"], expected)
            self.assertEqual(roster["limits"], baseline["limits"])
            self.assertEqual(len(roster["tasks"]), 8)
            self.assertEqual(roster["limits"]["possible_calls"], 104)
            policy = roster["sampling_policy"]
            self.assertEqual(policy["name"], f"pcfl.supplied_memory.{stage.lower()}.v1")
            self.assertTrue(policy["externally_scaffolded"])
            self.assertEqual(policy["external_first_read"], stage == "STRUCTURED_FIRST_READ_SMOKE")
            self.assertFalse(policy["learning_claim"] or policy["autonomy_claim"])
            for slot in ("first", "later"):
                self.assertEqual(policy[f"{slot}_slot_regex_sha256"], driver.core.byte_hash(policy[f"{slot}_slot_regex"]))
            driver.validate_roster(roster, roster["sha256"])

    def test_framed_smoke_is_exact_a3_subset_with_separate_frame_metadata(self):
        baseline = driver.build_roster(self.wires, "A3_THINK")
        roster = driver.build_roster(self.wires, "A3B_NEWLINE_FRAMED_SMOKE")
        expected = copy.deepcopy([baseline["tasks"][index] for index in (0, 1, 16, 17, 32, 33, 48, 49)])
        for task in expected:
            task["id"] = f"interface/A3B_NEWLINE_FRAMED_SMOKE/{task['case_id']}"
            task["slot_ids"] = [f"{driver.core.byte_hash(task['id'])}/actor/{turn}" for turn in range(7)]
        self.assertEqual(roster["tasks"], expected)
        self.assertEqual(roster["limits"], {**baseline["limits"], "possible_calls": 56})
        self.assertEqual(roster["continue"], baseline["continue"])
        self.assertEqual(roster["roots"], baseline["roots"])
        self.assertEqual(driver.CUSTOM_STAGES, driver.STRUCTURED_STAGES + driver.FRAMED_STAGES)
        self.assertTrue(roster["sampling_policy"]["externally_framed"])
        self.assertFalse(roster["full_assay_qualified"])
        driver.validate_roster(roster, roster["sha256"])

    def test_exact_frame_relation_rejects_wrong_reason_prefix_or_sampling(self):
        sampling = driver.sampling_for("A3B_NEWLINE_FRAMED_SMOKE", {"id": "unused", "seed": 1}, {"output_tokens": 256})
        valid = {"text": "THINK é", "finish_reason": "stop", "stop_reason": "\n"}
        for decoded in ("THINK é\n", "THINK é\nROUTE suffix\nmore"):
            driver._validate_frame(decoded, valid, sampling)
        driver._validate_frame("THINK é", {**valid, "stop_reason": None}, sampling)
        driver._validate_frame("THINK é\ncut", {"text": "THINK é\ncut", "finish_reason": "length", "stop_reason": None}, sampling)
        cases = [("THINK é", valid, sampling),
                 ("THINK é\nROUTE suffix", {**valid, "text": "ROUTE suffix"}, sampling),
                 ("THINK é \n", valid, sampling),
                 ("THINK é\n", {**valid, "stop_reason": None}, sampling),
                 ("THINK é\n", {**valid, "stop_reason": "other"}, sampling),
                 ("THINK é\n", {**valid, "finish_reason": "length"}, sampling),
                 ("THINK é", {**valid, "stop_reason": 1}, sampling),
                 ("THINK é\n", {**valid, "text": "THINK é\n", "stop_reason": None}, sampling),
                 ("THINK é\n", valid, {**sampling, "include_stop_str_in_output": True}),
                 ("THINK é\n", valid, {**sampling, "stop": ["\n", "other"]}),
                 ("THINK é\n", valid, {**sampling, "structured_outputs": {"regex": ".*"}})]
        for decoded, raw, settings in cases:
            with self.subTest(decoded=decoded, raw=raw, sampling=settings), self.assertRaises(ValueError):
                driver._validate_frame(decoded, raw, settings)

    def test_combined_smoke_changes_only_stage_identity_and_pinned_policy(self):
        baseline = driver.build_roster(self.wires, "A3B_NEWLINE_FRAMED_SMOKE")
        stage = "A3C_STRUCTURED_FRAMED_SMOKE"
        roster = driver.build_roster(self.wires, stage)
        expected = copy.deepcopy(baseline["tasks"])
        for task in expected:
            task["id"] = f"interface/{stage}/{task['case_id']}"
            task["slot_ids"] = [f"{driver.core.byte_hash(task['id'])}/actor/{turn}" for turn in range(7)]
        self.assertEqual(roster["tasks"], expected)
        for field in ("roots", "roots_sha256", "sources", "limits", "continue", "fits", "updates", "full_assay_qualified"):
            self.assertEqual(roster[field], baseline[field])
        policy = roster["sampling_policy"]
        self.assertTrue(policy["externally_scaffolded"] and policy["externally_framed"])
        self.assertFalse(policy["external_first_think"] or policy["autonomy_claim"] or policy["learning_claim"])
        self.assertEqual(policy["structured_outputs"], {"regex": driver.THINK_ROUTE_REGEX})
        self.assertEqual(policy["regex_sha256"], driver.core.byte_hash(driver.THINK_ROUTE_REGEX))
        driver.validate_roster(roster, roster["sha256"])
        roster["sampling_policy"]["structured_outputs"]["regex"] = ".*"
        roster["sampling_policy"]["regex_sha256"] = driver.core.byte_hash(".*")
        roster = driver.seal({key: value for key, value in roster.items() if key != "sha256"})
        with self.assertRaisesRegex(ValueError, "reconstruction"):
            driver.validate_roster(roster, roster["sha256"])

    def test_combined_regex_is_static_generic_think_or_route_with_optional_lf(self):
        expected = (r"(?:THINK [^\r\n]*[^\s\r\n][^\r\n]*"
                    r"|ROUTE N_[A-Z2-7]{10} N_[A-Z2-7]{10} : P_[A-Z2-7]{10}(?:,P_[A-Z2-7]{10})*)\n?")
        self.assertEqual(driver.THINK_ROUTE_REGEX, expected)
        route = "ROUTE N_ZZZZZZZZZZ N_2222222222 : P_7777777777,P_ABCDEF2345"
        valid = ["THINK x", "THINK \t é \t", "THINK ROUTE inert payload", route]
        for raw in valid:
            self.assertIsNotNone(re.fullmatch(expected, raw))
            self.assertIsNotNone(re.fullmatch(expected, raw + "\n"))
        driver.core.parse_route(route)
        invalid = ["THINK", "THINK ", "THINK \t\u00a0", "THINK \n", "THINK x\r", "THINK x\nROUTE later",
                   "THINK x\n\n", "READ EVENT E_ZZZZZZZZZZ", "PROBE Q_ZZZZZZZZZZ", "```THINK x```",
                   route + " ", route + "\r\n", route.replace(",", ", "), route.replace("P_7777777777", "P_0")]
        for raw in invalid:
            with self.subTest(raw=raw):
                self.assertIsNone(re.fullmatch(expected, raw))
        for slot in range(7):
            sampling = driver.sampling_for("A3C_STRUCTURED_FRAMED_SMOKE", {"id": "a" * 64 + f"/actor/{slot}", "seed": 7},
                                           {"output_tokens": 256})
            self.assertEqual(sampling["structured_outputs"], {"regex": expected})
            self.assertEqual(sampling["stop"], ["\n"])
            self.assertIs(sampling["include_stop_str_in_output"], False)

    def test_combined_frame_allows_only_pinned_grammar_without_weakening_a3b(self):
        sampling = driver.sampling_for("A3C_STRUCTURED_FRAMED_SMOKE", {"id": "unused", "seed": 1}, {"output_tokens": 256})
        original = copy.deepcopy(sampling)
        raw = {"text": "THINK x", "finish_reason": "stop", "stop_reason": "\n"}
        driver._validate_structured_frame("THINK x\nsuffix", raw, sampling)
        self.assertEqual(sampling, original)
        with self.assertRaisesRegex(ValueError, "LF framing sampling"):
            driver._validate_frame("THINK x\nsuffix", raw, sampling)
        for structured in (None, {"regex": ".*"}, {"regex": driver.ACTION_REGEX},
                           {"regex": driver.THINK_ROUTE_REGEX, "choice": ["THINK x"]}):
            with self.assertRaisesRegex(ValueError, "grammar differs"):
                driver._validate_structured_frame("THINK x\nsuffix", raw, {**sampling, "structured_outputs": structured})
        for changed in ({**raw, "text": "suffix"}, {**raw, "stop_reason": None}, {**raw, "finish_reason": "length"}):
            with self.assertRaises(ValueError):
                driver._validate_structured_frame("THINK x\nsuffix", changed, sampling)

    def test_exact_regexes_match_parser_and_admit_nonexistent_identifiers(self):
        expected = (r"(?:READ (?:EVENT E_[A-Z2-7]{10}|EVENTS_AT N_[A-Z2-7]{10}|LINKS_FROM E_[A-Z2-7]{10})"
                    r"|ROUTE N_[A-Z2-7]{10} N_[A-Z2-7]{10} : P_[A-Z2-7]{10}(?:,P_[A-Z2-7]{10})*)")
        self.assertEqual(driver.ACTION_REGEX, expected)
        reads = ["READ EVENT E_ZZZZZZZZZZ", "READ EVENTS_AT N_ZZZZZZZZZZ", "READ LINKS_FROM E_ZZZZZZZZZZ"]
        routes = ["ROUTE N_ZZZZZZZZZZ N_2222222222 : P_7777777777",
                  "ROUTE N_ZZZZZZZZZZ N_2222222222 : P_7777777777,P_ABCDEF2345"]
        valid = reads + routes
        invalid = ["THINK reason", "PROBE Q_ZZZZZZZZZZ", "READ NODE N_ZZZZZZZZZZ",
                   "READ EVENT E_ZZZZZZZZZ", "READ EVENT E_ZZZZZZZZZZZ", "READ EVENT E_0000000000",
                   "READ EVENT N_ZZZZZZZZZZ", routes[1].replace(",", ", ")]
        invalid += [changed for raw in valid for changed in (raw + "\n", raw + "\r", raw + " ", " " + raw,
                    raw + "\n" + routes[0], raw.replace(" ", "  ", 1), "```" + raw + "```")]
        for raw in valid + invalid:
            with self.subTest(raw=raw):
                parser = driver.core.parse_read if raw.startswith("READ ") else driver.core.parse_route
                try:
                    parser(raw)
                    parsed = True
                except ValueError:
                    parsed = False
                self.assertEqual(bool(re.fullmatch(driver.ACTION_REGEX, raw)), parsed)
                self.assertEqual(parsed, raw in valid)
                self.assertEqual(bool(re.fullmatch(driver.READ_REGEX, raw)), raw in reads)

    def test_sampling_changes_only_regex_and_never_reads_task_contents(self):
        for stage in driver.STAGES:
            for slot in (0, 1, 12):
                request = {"id": "a" * 64 + f"/actor/{slot}", "seed": 37}
                limits = {"output_tokens": 19}
                expected = {**driver.native.SAMPLING, "seed": 37, "max_tokens": 19}
                if stage in driver.STRUCTURED_STAGES:
                    expected["structured_outputs"] = {"regex": driver.READ_REGEX
                        if stage == "STRUCTURED_FIRST_READ_SMOKE" and slot == 0 else driver.ACTION_REGEX}
                if stage in driver.FRAMED_STAGES:
                    expected.update(stop=["\n"], include_stop_str_in_output=False)
                if stage in driver.STRUCTURED_FRAMED_STAGES:
                    expected["structured_outputs"] = {"regex": driver.THINK_ROUTE_REGEX}
                self.assertEqual(driver.sampling_for(stage, request, limits), expected)
                self.assertEqual(request, {"id": "a" * 64 + f"/actor/{slot}", "seed": 37})
                self.assertEqual(limits, {"output_tokens": 19})

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

    def test_framed_gate_requires_joint_thought_terminal_not_graph_success(self):
        rows = self.rows()[:8]
        for row in rows:
            row.update(success=False, served_reads=0)
        rows[-1]["thinks"] = 0
        summary = driver.summarize(rows, "A3B_NEWLINE_FRAMED_SMOKE", True)
        self.assertEqual(summary["denominator"], 8)
        self.assertEqual(summary["thought_interface_tasks"], 7)
        self.assertEqual(summary["route_successes"], 0)
        self.assertTrue(summary["stage_gate_passed"])
        self.assertFalse(summary["full_assay_qualified"])
        self.assertFalse(driver.summarize(rows, "A3B_NEWLINE_FRAMED_SMOKE", False)["stage_gate_passed"])
        self.assertFalse(driver.summarize(rows[:7], "A3B_NEWLINE_FRAMED_SMOKE", True)["stage_gate_passed"])
        for reason in ("LENGTH", "INVALID_TURN", "THINK_DISABLED_OR_CAP", "INPUT_TOKEN_CAP"):
            altered = copy.deepcopy(rows)
            altered[0]["reason"] = reason
            self.assertFalse(driver.summarize(altered, "A3B_NEWLINE_FRAMED_SMOKE", True)["stage_gate_passed"])

    def test_required_read_thresholds_are_joint_and_not_graph_gates(self):
        for stage, count, threshold in (("READ_REQUIRED_SMOKE", 8, 7), ("READ_REQUIRED_PANEL", 64, 60),
                                         ("STRUCTURED_ACTION_SMOKE", 8, 7), ("STRUCTURED_FIRST_READ_SMOKE", 8, 7)):
            with self.subTest(stage=stage):
                rows = self.rows()[:count]
                for row in rows:
                    row.update(success=False, thinks=0)
                for row in rows[threshold:]:
                    row["served_reads"] = 0
                summary = driver.summarize(rows, stage, True)
                self.assertEqual(summary["denominator"], count)
                self.assertEqual(summary["read_handshake_tasks"], threshold)
                self.assertEqual(summary["route_successes"], 0)
                self.assertTrue(summary["stage_gate_passed"])
                self.assertFalse(driver.summarize(rows, stage, False)["stage_gate_passed"])
                self.assertFalse(driver.summarize(rows[:threshold], stage, True)["stage_gate_passed"])
                rows[0]["served_reads"] = 0
                self.assertFalse(driver.summarize(rows, stage, True)["stage_gate_passed"])

    def test_required_read_invalid_or_capped_terminal_cannot_supply_joint_gate(self):
        for stage, count, threshold in (("READ_REQUIRED_SMOKE", 8, 7), ("READ_REQUIRED_PANEL", 64, 60),
                                         ("STRUCTURED_ACTION_SMOKE", 8, 7), ("STRUCTURED_FIRST_READ_SMOKE", 8, 7)):
            for reason in ("INVALID_TURN", "LENGTH", "TURN_CAP", "ACTOR_TOKEN_CAP",
                           "RETURNED_TOKEN_CAP", "INPUT_TOKEN_CAP"):
                with self.subTest(stage=stage, reason=reason):
                    rows = self.rows()[:count]
                    for row in rows[threshold - 1:]:
                        row.update(reason=reason, success=False)
                    summary = driver.summarize(rows, stage, True)
                    self.assertEqual(summary["served_read_tasks"], count)
                    self.assertEqual(summary["read_handshake_tasks"], threshold - 1)
                    self.assertFalse(summary["stage_gate_passed"])
            rows = self.rows()[:count]
            rows[-1]["invalid_read"] = True
            summary = driver.summarize(rows, stage, True)
            self.assertGreaterEqual(summary["read_handshake_tasks"], threshold)
            self.assertFalse(summary["stage_gate_passed"])


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
        self.raw_overrides = {}
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
        fixture, outputs, finishes, overrides = self.fixture, self.outputs, self.finishes, self.raw_overrides
        actor_type = driver.InterfaceActor if stage in driver.CUSTOM_STAGES else driver.native.NativeActor
        class Scripted(actor_type):
            def generate(self, request, limits):
                fixture.session.text = outputs.get(request["id"], "invalid")
                fixture.session.mutate = lambda raw: {**raw, "finish_reason": finishes.get(request["id"], "stop"),
                                                     **overrides.get(request["id"], {})}
                return super().generate(request, limits)
        arguments = {"stage": stage, "roster": self.plan} if stage in driver.CUSTOM_STAGES else {}
        self.actor = Scripted(self.settings, **arguments, loader=fixture.loader,
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

    def test_required_smoke_captures_only_fixed_eight_and_replays(self):
        self.prepare("READ_REQUIRED_SMOKE")
        report = self.run_stage()
        self.assertEqual(report["status"], "COMPLETE")
        self.assertEqual(len(report["results"]), 8)
        self.assertEqual(report["calls"], 16)
        self.assertEqual(report["possible_calls"], 104)
        self.assertEqual(report["summary"]["denominator"], 8)
        self.assertEqual(report["summary"]["read_handshake_tasks"], 8)
        self.assertTrue(report["summary"]["stage_gate_passed"])
        self.assertFalse(report["full_assay_qualified"])
        self.assertEqual((report["fits"], report["updates"]), (0, 0))
        self.assertEqual([row["id"] for row in report["results"]], [task["id"] for task in self.plan["tasks"]])
        self.replay(report)

    def test_structured_action_generate_capture_and_replay(self):
        self.check_structured_capture("STRUCTURED_ACTION_SMOKE")

    def test_framed_generation_preserves_full_decode_single_token_suffix_and_replay(self):
        self.check_framed_generation("A3B_NEWLINE_FRAMED_SMOKE")

    def test_combined_generation_preserves_full_decode_single_token_suffix_and_replay(self):
        self.check_framed_generation("A3C_STRUCTURED_FRAMED_SMOKE")

    def check_framed_generation(self, stage):
        suffix = "\nROUTE unexecuted suffix"
        class SuffixTokenizer(fixtures.Tokenizer):
            def encode(self, text, add_special_tokens=False):
                if text.endswith(suffix):
                    return super().encode(text[:-len(suffix)], add_special_tokens) + [999999]
                return super().encode(text, add_special_tokens)

            def decode(self, ids, skip_special_tokens=True):
                return "".join(suffix if token == 999999 else chr(token) for token in ids)
        self.tokenizer = self.fixture.session.tokenizer = SuffixTokenizer(self.fixture.model)
        self.prepare(stage)
        for task in self.plan["tasks"]:
            for slot in task["slot_ids"][:2]:
                prefix = self.outputs[slot]
                self.outputs[slot] = prefix + suffix
                self.raw_overrides[slot] = {"text": prefix, "stop_reason": "\n"}
        report = self.run_stage()
        self.assertEqual(report["status"], "COMPLETE")
        self.assertEqual(report["calls"], 16)
        self.assertEqual(report["possible_calls"], 56)
        self.assertEqual(report["summary"]["thought_interface_tasks"], 8)
        self.assertTrue(report["summary"]["stage_gate_passed"])
        self.assertEqual(report["sampling_policy"], self.plan["sampling_policy"])
        total = 0
        for index, attempt in enumerate(report["attempts"]):
            raw = driver._decode(attempt["capture"]["files"][f"call_{index:04d}.raw.json"]["utf8"])["raw"]
            returned = driver._decode(attempt["capture"]["files"][f"call_{index:04d}.response.json"]["utf8"])
            expected = self.outputs[attempt["request"]["id"]]
            self.assertEqual(returned["decoded"], expected)
            self.assertEqual(raw["output_token_ids"][-1], 999999)
            self.assertEqual(raw["text"] + suffix, expected)
            self.assertEqual(bytes.fromhex(returned["raw_hex"]).decode(), raw["text"])
            self.assertEqual(attempt["response"]["text"], raw["text"])
            self.assertEqual(attempt["response"]["output_tokens"], len(raw["text"]) + 1)
            total += attempt["response"]["output_tokens"]
            self.assertEqual(self.fixture.session.calls[index][1], driver.sampling_for(self.plan["stage"], attempt["request"], attempt["limits"]))
        self.assertEqual(sum(row["actor_tokens"] for row in report["results"]), total)
        self.assertEqual(report["attempts"][1]["request"]["messages"][-1]["content"], driver.CONTINUE)
        self.assertNotIn(suffix, report["attempts"][1]["request"]["messages"][-2]["content"])
        self.replay(report)
        for field, value in (("decoded", report["attempts"][0]["response"]["text"]),
                             ("raw_hex", b"invented".hex())):
            altered = copy.deepcopy(report)
            record = altered["attempts"][0]["capture"]["files"]["call_0000.response.json"]
            parsed = driver._decode(record["utf8"])
            parsed[field] = value
            record["utf8"] = driver.canonical(parsed).decode()
            record["sha256"] = driver.core.byte_hash(record["utf8"])
            altered = driver.seal({key: item for key, item in altered.items() if key != "sha256"})
            with self.assertRaises(ValueError):
                self.replay(altered)

    def test_framed_eos_length_and_first_think_requirement_remain_distinct(self):
        first = self.prepare("A3B_NEWLINE_FRAMED_SMOKE")
        self.finishes[first["slot_ids"][0]] = "length"
        second = self.plan["tasks"][1]
        self.outputs[second["slot_ids"][0]] = self.outputs[second["slot_ids"][1]]
        report = self.run_stage()
        self.assertEqual(report["status"], "COMPLETE")
        self.assertEqual(report["results"][0]["reason"], "LENGTH")
        self.assertEqual(report["results"][0]["slots"][1]["status"], "UNCALLED")
        self.assertEqual(report["results"][1]["reason"], "THINK_REQUIRED")
        self.assertEqual(report["summary"]["thought_interface_tasks"], 6)
        self.assertFalse(report["summary"]["stage_gate_passed"])
        self.replay(report)

    def test_combined_physical_gate_is_not_graph_success_and_rejects_sampling_tamper(self):
        self.prepare("A3C_STRUCTURED_FRAMED_SMOKE")
        for task in self.plan["tasks"]:
            route = self.outputs[task["slot_ids"][1]]
            self.outputs[task["slot_ids"][1]] = route.split(" : ")[0] + " : P_ZZZZZZZZZZ"
        report = self.run_stage()
        self.assertEqual(report["status"], "COMPLETE")
        self.assertEqual(report["calls"], 16)
        self.assertEqual(report["possible_calls"], 56)
        self.assertEqual(report["summary"]["thought_interface_tasks"], 8)
        self.assertEqual(report["summary"]["route_successes"], 0)
        self.assertTrue(report["summary"]["stage_gate_passed"])
        self.assertTrue(report["summary"]["externally_scaffolded"])
        self.assertFalse(report["summary"]["external_first_think"] or report["summary"]["full_assay_qualified"])
        self.replay(report)
        for index, field, value in ((0, "structured_outputs", {"regex": "THINK [^\r\n]+"}),
                                    (1, "structured_outputs", {"regex": driver.ACTION_REGEX}),
                                    (0, "stop", []), (0, "include_stop_str_in_output", True)):
            altered = copy.deepcopy(report)
            record = altered["attempts"][index]["capture"]["files"][f"call_{index:04d}.render.json"]
            rendered = driver._decode(record["utf8"])
            rendered["sampling"][field] = value
            record["utf8"] = driver.canonical(rendered).decode()
            record["sha256"] = driver.core.byte_hash(record["utf8"])
            altered = driver.seal({key: item for key, item in altered.items() if key != "sha256"})
            with self.assertRaises(ValueError):
                self.replay(altered)

    def test_combined_does_not_force_first_think_or_salvage_length(self):
        first = self.prepare("A3C_STRUCTURED_FRAMED_SMOKE")
        self.outputs[first["slot_ids"][0]] = self.outputs[first["slot_ids"][1]]
        second = self.plan["tasks"][1]
        self.finishes[second["slot_ids"][0]] = "length"
        report = self.run_stage()
        self.assertEqual(report["status"], "COMPLETE")
        self.assertEqual(report["results"][0]["reason"], "THINK_REQUIRED")
        self.assertEqual(report["results"][1]["reason"], "LENGTH")
        self.assertEqual(report["summary"]["thought_interface_tasks"], 6)
        self.assertFalse(report["summary"]["stage_gate_passed"])
        self.replay(report)

    def test_framed_wrong_stop_reason_preserves_raw_and_aborts_no_rescue(self):
        first = self.prepare("A3B_NEWLINE_FRAMED_SMOKE")
        slot = first["slot_ids"][0]
        prefix = self.outputs[slot]
        self.outputs[slot] = prefix + "\nROUTE unexecuted"
        self.raw_overrides[slot] = {"text": prefix, "stop_reason": None}
        report = self.run_stage()
        self.assertEqual(report["status"], "FAILED")
        self.assertEqual(report["calls"], 1)
        self.assertEqual(report["results"][0]["status"], "ABORTED")
        raw = driver._decode(report["attempts"][0]["capture"]["files"]["call_0000.raw.json"]["utf8"])["raw"]
        self.assertEqual(raw["text"], prefix)
        self.assertEqual(self.tokenizer.decode(raw["output_token_ids"]), self.outputs[slot])
        self.assertNotIn("call_0000.response.json", report["attempts"][0]["capture"]["files"])
        self.replay(report)

    def test_structured_first_read_generate_capture_and_replay(self):
        self.check_structured_capture("STRUCTURED_FIRST_READ_SMOKE")

    def check_structured_capture(self, stage):
        first = self.prepare(stage)
        self.outputs[first["slot_ids"][0]] = "READ EVENT E_ZZZZZZZZZZ"
        self.assertNotIn(self.outputs[first["slot_ids"][0]], first["queries"])
        report = self.run_stage()
        self.assertEqual(report["status"], "COMPLETE")
        self.assertEqual(report["calls"], 16)
        self.assertEqual(report["possible_calls"], 104)
        self.assertEqual(report["summary"]["denominator"], 8)
        self.assertEqual(report["summary"]["read_handshake_tasks"], 7)
        self.assertTrue(report["summary"]["stage_gate_passed"])
        self.assertTrue(report["summary"]["externally_scaffolded"])
        self.assertFalse(report["summary"]["autonomy_claim"] or report["summary"]["learning_claim"])
        self.assertEqual(report["summary"]["external_first_read"], stage == "STRUCTURED_FIRST_READ_SMOKE")
        self.assertEqual(report["sampling_policy"], self.plan["sampling_policy"])
        self.assertEqual(report["results"][0]["services"][0]["raw"], "MISS")
        for index, attempt in enumerate(report["attempts"]):
            sampling = driver.sampling_for(stage, attempt["request"], attempt["limits"])
            rendered = driver._decode(attempt["capture"]["files"][f"call_{index:04d}.render.json"]["utf8"])
            self.assertEqual(rendered["sampling"], sampling)
            self.assertEqual(self.fixture.session.calls[index][1], sampling)
        self.replay(report)

    def test_structured_generic_first_route_is_not_a_handshake(self):
        self.prepare("STRUCTURED_ACTION_SMOKE")
        for task in self.plan["tasks"]:
            self.outputs[task["slot_ids"][0]] = self.outputs[task["slot_ids"][1]]
        report = self.run_stage()
        self.assertEqual(report["calls"], 8)
        self.assertEqual(report["summary"]["route_successes"], 8)
        self.assertEqual(report["summary"]["read_handshake_tasks"], 0)
        self.assertFalse(report["summary"]["stage_gate_passed"])
        self.replay(report)

    def test_structured_length_failure_is_not_salvaged(self):
        first = self.prepare("STRUCTURED_FIRST_READ_SMOKE")
        self.finishes[first["slot_ids"][0]] = "length"
        report = self.run_stage()
        self.assertEqual(report["results"][0]["reason"], "LENGTH")
        self.assertEqual(report["results"][0]["reads"], 0)
        self.assertEqual(report["results"][0]["slots"][1]["status"], "UNCALLED")
        self.assertEqual(report["results"][0]["raw"], self.outputs[first["slot_ids"][0]])
        self.replay(report)

    def test_structured_actor_binds_roster_stage_sources_and_immutable_slots(self):
        task = self.prepare("STRUCTURED_FIRST_READ_SMOKE")
        request = {"id": task["slot_ids"][0], "seed": task["seed"], "messages": task["messages"], "mount": "C0"}
        limits = {"output_tokens": 256}
        for changed in ({**request, "id": "f" * 64 + "/actor/0"},
                        {**request, "seed": request["seed"] + 1},
                        {**request, "id": task["slot_ids"][1]}):
            with self.assertRaisesRegex(ValueError, "structured slot"):
                self.actor._sampling(changed, limits)
        with self.assertRaises(TypeError):
            self.actor._slot_seeds[request["id"]] = 0
        altered = copy.deepcopy(self.plan)
        altered["sampling_policy"]["first_slot_regex"] = ".*"
        altered = driver.seal({key: value for key, value in altered.items() if key != "sha256"})
        with self.assertRaisesRegex(ValueError, "reconstruction"):
            driver.InterfaceActor(self.settings, stage=self.plan["stage"], roster=altered)
        with self.assertRaisesRegex(ValueError, "stage binding"):
            driver.InterfaceActor(self.settings, stage="STRUCTURED_ACTION_SMOKE", roster=self.plan)
        settings = copy.deepcopy(self.settings)
        settings["source_files"].pop(str(Path(driver.__file__).resolve()))
        with self.assertRaisesRegex(ValueError, "source pins"):
            driver.InterfaceActor(settings, stage=self.plan["stage"], roster=self.plan)
        self.fixture.loader.assert_not_called()

    def test_structured_replay_rejects_resealed_sampling_tamper(self):
        self.prepare("STRUCTURED_FIRST_READ_SMOKE")
        report = self.run_stage()
        for index, field, value in ((0, "structured_outputs", {"regex": driver.ACTION_REGEX}),
                                    (1, "structured_outputs", {"regex": driver.READ_REGEX}),
                                    (0, "max_tokens", 255), (0, "seed", 0)):
            altered = copy.deepcopy(report)
            record = altered["attempts"][index]["capture"]["files"][f"call_{index:04d}.render.json"]
            rendered = driver._decode(record["utf8"])
            rendered["sampling"][field] = value
            record["utf8"] = driver.canonical(rendered).decode()
            record["sha256"] = driver.core.byte_hash(record["utf8"])
            altered = driver.seal({key: item for key, item in altered.items() if key != "sha256"})
            with self.assertRaisesRegex(ValueError, "replay differs|extra replay"):
                self.replay(altered)

    def test_structured_live_capture_sampling_drift_fails_stage(self):
        self.prepare("STRUCTURED_FIRST_READ_SMOKE")
        def reader(directory, index):
            capture = driver.read_capture(directory, index)
            record = capture["files"][f"call_{index:04d}.render.json"]
            rendered = driver._decode(record["utf8"])
            rendered["sampling"].pop("structured_outputs")
            record["utf8"] = driver.canonical(rendered).decode()
            record["sha256"] = driver.core.byte_hash(record["utf8"])
            return capture
        report = self.run_stage(reader)
        self.assertEqual(report["status"], "FAILED")
        self.assertEqual(report["calls"], 1)
        self.assertEqual(report["results"][0]["status"], "ABORTED")
        self.assertTrue(all(row["status"] == "UNCALLED" for row in report["results"][1:]))
        self.assertIn("sampling join", report["error"]["message"])
        self.replay(report)

    def test_required_panel_captures_64_only_when_explicitly_selected(self):
        self.prepare("READ_REQUIRED_PANEL")
        report = self.run_stage()
        self.assertEqual(report["status"], "COMPLETE")
        self.assertEqual(report["calls"], 128)
        self.assertEqual(report["possible_calls"], 832)
        self.assertEqual(report["summary"]["denominator"], 64)
        self.assertEqual(report["summary"]["read_handshake_tasks"], 64)
        self.assertTrue(report["summary"]["stage_gate_passed"])
        self.replay(report)

    def test_required_smoke_keeps_raw_failures_miss_and_no_read_as_scored(self):
        self.prepare("READ_REQUIRED_SMOKE")
        tasks = self.plan["tasks"]
        self.outputs[tasks[0]["slot_ids"][0]] += "\n"
        self.finishes[tasks[1]["slot_ids"][0]] = "length"
        self.outputs[tasks[2]["slot_ids"][0]] = "READ EVENT E_ZZZZZZZZZZ"
        self.outputs[tasks[3]["slot_ids"][0]] = self.outputs[tasks[3]["slot_ids"][1]]
        self.outputs[tasks[4]["slot_ids"][1]] += "\n"
        report = self.run_stage()
        self.assertEqual(report["status"], "COMPLETE")
        self.assertEqual(report["summary"]["denominator"], 8)
        self.assertEqual(report["summary"]["read_handshake_tasks"], 3)
        self.assertEqual(report["summary"]["invalid_read_tasks"], 1)
        self.assertFalse(report["summary"]["stage_gate_passed"])
        self.assertEqual([row["reason"] for row in report["results"][:5]],
                         ["INVALID_READ", "LENGTH", "ROUTE", "ROUTE", "INVALID_TURN"])
        self.assertEqual(report["results"][2]["services"][0]["raw"], "MISS")
        self.assertEqual(report["results"][0]["raw"], self.outputs[tasks[0]["slot_ids"][0]])
        self.assertEqual(report["results"][1]["slots"][1]["status"], "UNCALLED")
        self.replay(report)

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
