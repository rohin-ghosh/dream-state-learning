import copy
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import unittest

from organism_v6 import pcfl_vertical_dev as core


class PCFLVerticalTests(unittest.TestCase):
    def setUp(self):
        self.root = core.build_root("excluded/0")
        self.cell = core.WorldCell(self.root, 0, 0, 0)

    def old_life(self, cell=None):
        cell = cell or self.cell
        session = core.WorldSession(cell, "OLD")
        admissions, receipts = [], []
        for index in range(8):
            source, ports = session._affordances()
            result = session.explore("EXPLORE " + source + " " + ports[0])
            self.assertTrue(result["ok"])
            receipt = result["receipt"]
            fresh = cell.root.lookup("event", f"e{index}")
            raw = core.EVENT_WIRE.format(event=fresh, **receipt)
            admission = core.admit_event(raw, receipt, session, fresh)
            self.assertTrue(admission["accepted"], admission)
            admissions.append(admission)
            receipts.append(receipt)
        events = [item["row"] for item in admissions]
        pairs = [(first, second) for first in events for second in events
                 if first["fields"]["destination"] == second["fields"]["source"]]
        self.assertEqual(len(pairs), 4)
        for index, (first, second) in enumerate(pairs):
            fresh = cell.root.lookup("link", f"l{index}")
            fields = dict(link=fresh, first=first["fields"]["event"], second=second["fields"]["event"],
                          via=first["fields"]["destination"], receipt_first=first["fields"]["receipt"],
                          receipt_second=second["fields"]["receipt"])
            evidence = [next(receipt for receipt in receipts if receipt["receipt"] == fields[key])
                        for key in ("receipt_first", "receipt_second")]
            admission = core.admit_link(core.LINK_WIRE.format(**fields), evidence, session, fresh, [first, second])
            self.assertTrue(admission["accepted"], admission)
            admissions.append(admission)
        return session, admissions

    def test_source_pins(self):
        root = Path(__file__).resolve().parents[1] / "research_notes" / "analysis"
        for name, expected in core.SOURCE_PINS.items():
            self.assertEqual(hashlib.sha256((root / name).read_bytes()).hexdigest(), expected, name)
        self.assertEqual(hashlib.sha256((root / core.BINDING_MEMO).read_bytes()).hexdigest(), core.BINDING_MEMO_SHA256)
        self.assertEqual(hashlib.sha256((Path(__file__).resolve().parents[1] / core.PRODUCTION_BINDING_PATH).read_bytes()).hexdigest(), core.PRODUCTION_BINDING_SHA256)

    def test_root_roundtrip_and_closed_json(self):
        for label in core.ROOT_LABELS:
            root = core.build_root(label)
            self.assertEqual(core.from_data(json.loads(core.canonical(core.to_data(root)))), root)
            for cell in core.expand_cube(root):
                self.assertEqual(core.from_data(core.to_data(cell)), cell)
        with self.assertRaises(ValueError):
            core.canonical(self.cell)
        with self.assertRaises(ValueError):
            core.canonical({"sample": 0.7})
        data = core.to_data(self.root)
        data["outcome"] = "injected"
        with self.assertRaises(ValueError):
            core.from_data(data)

    def test_inventory_invalid_and_unqualified(self):
        data = core.to_data(self.root)
        data["inventory"]["node"]["A"] = data["inventory"]["node"]["H"]
        with self.assertRaises(ValueError):
            core.from_data(data)
        with self.assertRaises(ValueError):
            core.build_root("dev/2")
        with self.assertRaises(ValueError):
            core.opaque_candidate("dev/0", "node", 0, 1000000)
        data = core.to_data(self.cell)
        data["old"] = True
        with self.assertRaises(ValueError):
            core.from_data(data)
        self.assertFalse(core.registries()["root_schema"]["tokenizer_qualified"])

    def test_seed_reference(self):
        expected = int.from_bytes(hashlib.sha256(b"PCFL-V2.1-PREP\x00root/dev/0").digest()[:8], "big") & 0x7fffffffffffffff
        self.assertEqual(core.seed("root/dev/0"), expected)
        self.assertNotEqual(core.seed("root/dev/0"), core.seed("opaque/dev/0"))
        self.assertRegex(core.opaque_candidate("dev/0", "event", 0), r"^E_[A-Z2-7]{10}$")
        self.assertEqual(core.opaque_candidate("dev/0", "event", 0), "E_3TGT3U43QK")

    def test_preoutput_root_registry_and_ten_render_snapshots(self):
        cell = core.WorldCell(self.root, 1, 1, 0)
        wrong = core.ideal_rows(core.WorldCell(core.build_root("excluded/1"), 0, 0, 0))
        self.assertEqual(core.digest(core.to_data(self.root)), "823754da5823bbcef0d00852d3c1160d5e012b6e8c236eb7555acdd906d6d186")
        self.assertEqual(core.digest(core.registries()), "cf8dd4b26388676dc2466139f49252c39a537f7d6383b3ef0b4fb48468354825")
        self.assertEqual(core.digest(core.render_views(cell, 0, core.ideal_rows(cell), wrong, fixture_only=True)), "ca87f40f3c78ac9885a071297408d08b40b1401a31454a1c6d5af1b16b02b5bc")

    def test_registry_detached_no_pad_and_main_literals(self):
        registry = core.registries()
        self.assertEqual(set(registry["render_registry"]["projections"]), set(core.PROJECTIONS))
        self.assertEqual(registry["render_registry"]["wrappers"]["W8"], "Provide the exact stored personal-memory block at this address.\n{REQUEST}\nOutput only the block.")
        self.assertEqual(registry["parser_registry"]["refusals"], ["MISS", "MISS\n"])
        self.assertNotIn("PAD", core.canonical(registry))
        registry["root_schema"]["slots"]["node"].append("bad")
        self.assertNotIn("bad", core.registries()["root_schema"]["slots"]["node"])
        self.assertTrue(core.validate_registries(core.registries()))
        with self.assertRaises(ValueError):
            core.validate_registries(registry)

    def test_production_definition_bound_does_not_close_other_gates(self):
        binding = core.production_binding_status()
        self.assertEqual(binding["status"], "WORLD_DEFINITION_BOUND")
        self.assertTrue(binding["definition_bound"])
        self.assertFalse(binding["execution_contract_valid"])
        self.assertFalse(binding["production_inventory_complete"])
        self.assertEqual(binding["source_sha256"], core.PRODUCTION_BINDING_SHA256)
        self.assertEqual(binding["distractor"]["endpoints"], ["X", "Z"])
        self.assertEqual(binding["relevant_public_result"], core.PROBE_WIRE)
        world = core.registries()["world_registry"]
        self.assertEqual(world["distractor"], binding)
        self.assertEqual(world["probe_endpoints"], [["H", "S_R"], ["X", "Z"]])
        self.assertEqual(world["probe_result"], core.PROBE_WIRE)
        self.assertEqual(world["probe_receipt_slots"], ["r9", "r10"])
        binding["distractor"]["endpoints"] = ["invented", "invented"]
        self.assertEqual(core.production_binding_status()["distractor"]["endpoints"], ["X", "Z"])

    def test_bound_default_cpu_interfaces_do_not_authorize_native(self):
        self.assertTrue(core.require_production_bindings())
        self.assertFalse(core.WorldSession(self.cell, "NEW").terminal)
        self.assertIn(self.root.lookup("node", "X"), core.render_reachout(self.cell, 0))
        self.assertIn("PROBE RESULT", core.render_task(self.cell, 0, "RAW_EPISODIC")["user"])
        old = core.WorldSession(self.cell, "OLD")
        with self.assertRaises(ValueError):
            old.probe("PROBE " + self.root.lookup("probe", "distractor"))
        self.assertEqual(old.receipts, [])
        self.assertFalse(core.production_binding_status()["execution_contract_valid"])

    def test_fixture_flag_never_bypasses_bound_terminal_rules(self):
        session = core.WorldSession(self.cell, "NEW", fixture_only=True)
        result = session.probe("PROBE " + self.root.lookup("probe", "distractor"))
        self.assertTrue(result["ok"])
        self.assertTrue(result["receipt"]["fixture_only"])
        self.assertTrue(result["terminal"])
        self.assertEqual(result["receipt"]["destination"], self.root.lookup("node", "Z"))
        with self.assertRaises(ValueError):
            session.explore_prompt()
        self.assertFalse(core.production_binding_status()["execution_contract_valid"])
        with self.assertRaises(ValueError):
            core.WorldSession(self.cell, "NEW", fixture_only="true")

    def test_cube_oracle_and_cut_exhaustive(self):
        for label in core.ROOT_LABELS:
            for cell in core.expand_cube(core.build_root(label)):
                for goal in (0, 1, "old_left", "old_right"):
                    for cut in (None, "OLD", "NEW"):
                        route = core.oracle_route_v1(cell, goal, cut)
                        self.assertEqual(core.oracle_routes_v2(cell, goal, cut), () if route is None else (route,))
                        if route is not None:
                            self.assertTrue(core.score_route(cell, goal, route, cut)["graph_success"])

    def test_actual_receipts_follow_cpu_chronology(self):
        cell = core.WorldCell(self.root, 1, 1, 0)
        fixture = core.ceiling_fixture(cell)
        self.assertEqual(fixture["origin"], "HARNESS_SCRIPTED_CPU_CEILING_NOT_CHILD")
        self.assertEqual(len(fixture["receipts"]), 10)
        self.assertEqual(fixture["receipts"][0]["destination"], self.root.lookup("node", "X"))
        rows = core.ideal_rows(cell)
        e0 = next(row for row in rows if row["fields"].get("event") == self.root.lookup("event", "e0"))
        self.assertEqual(e0["fields"]["receipt"], self.root.lookup("receipt", "r6"))
        for row in rows:
            self.assertEqual(row["taint"], "CEILING_FIXTURE")
            if row["kind"] == "EVENT":
                fields = row["fields"]
                self.assertTrue(any(all(receipt[key] == fields[key] for key in ("receipt", "source", "port", "destination"))
                                    for receipt in fixture["receipts"] if receipt["kind"] == "EXPLORE"))

    def test_read_only_public_projections(self):
        for cell in core.expand_cube(self.root):
            rows = core.ideal_rows(cell)
            views = core.render_views(cell, 0, rows, core.ideal_rows(core.WorldCell(core.build_root("excluded/1"), 0, 0, 0)), fixture_only=True)
            for name, view in views.items():
                self.assertEqual(set(view), {"system", "user", "service_enabled"})
                self.assertNotIn("sha256", view["user"])
                self.assertNotIn("CEILING_FIXTURE", view["user"])
                self.assertEqual(view["service_enabled"], name == "ACTIVE_LINKED_TEXT")
            self.assertEqual(views["NONE_OFF"]["user"], views["ACTIVE_LINKED_TEXT"]["user"])
            self.assertNotIn("LINK ", views["NEW_ONLY_TEXT"]["user"])
            self.assertNotIn("EVENT ", views["RAW_EPISODIC"]["user"])
            self.assertEqual(views["NATIVE_CONTEXT"]["user"], "MEMORY\n" + "".join(row["raw"] for row in rows) + "\n" + views["NONE_OFF"]["user"])

    def test_projection_equalities(self):
        cells = core.expand_cube(self.root)
        for goal in (0, 1):
            for old in (0, 1):
                renders = [core.render_task(cell, goal, "OLD_ONLY_TEXT", rows=core.ideal_rows(cell)) for cell in cells if cell.old == old]
                self.assertEqual(len({core.digest(render) for render in renders}), 1)
            for relevant in (0, 1):
                renders = [core.render_task(cell, goal, "NEW_ONLY_TEXT", rows=core.ideal_rows(cell)) for cell in cells if cell.relevant == relevant]
                self.assertEqual(len({core.digest(render) for render in renders}), 1)
            self.assertEqual(len({core.digest(core.render_task(cell, goal, "NONE_OFF")) for cell in cells}), 1)

    def test_render_order_fixed_and_missing_rows_not_silently_off(self):
        rows = core.ideal_rows(self.cell)
        self.assertEqual(core.render_task(self.cell, 0, rows=rows), core.render_task(self.cell, 0, rows=list(reversed(rows))))
        with self.assertRaises(ValueError):
            core.render_task(self.cell, 0, rows=rows[:-1])
        with self.assertRaises(ValueError):
            core.render_task(self.cell, 0, rows=rows + rows[:1])

    def test_reachout_preoutcome_order_and_result(self):
        rendered = [core.render_reachout(cell, 0, "RA", fixture_only=True) for cell in core.expand_cube(self.root)]
        self.assertEqual(len(set(rendered)), 1)
        relevant = self.root.lookup("probe", "relevant")
        distractor = self.root.lookup("probe", "distractor")
        self.assertLess(rendered[0].index(relevant), rendered[0].index(distractor))
        reverse = core.render_reachout(self.cell, 0, "RB", fixture_only=True)
        self.assertLess(reverse.index(distractor), reverse.index(relevant))
        for cell in core.expand_cube(self.root):
            for name, bit in (("relevant", cell.relevant), ("distractor", cell.distractor)):
                session = core.WorldSession(cell, "NEW", fixture_only=True)
                result = session.probe("PROBE " + self.root.lookup("probe", name))
                self.assertTrue(result["ok"])
                self.assertEqual(result["receipt"]["port"], self.root.lookup("port", f"q{bit}"))
                if name == "relevant":
                    self.assertFalse(result["terminal"])
                    source, ports = session._affordances()
                    executed = session.explore("EXPLORE " + source + " " + ports[0])
                    self.assertEqual(executed["receipt"]["destination"], self.root.lookup("node", "S_R"))
                else:
                    self.assertTrue(result["terminal"])
                    self.assertEqual(result["receipt"]["destination"], self.root.lookup("node", "Z"))
                    with self.assertRaises(ValueError):
                        session._affordances()

    def test_invalid_actions_consumed_no_retry(self):
        session = core.WorldSession(self.cell, "OLD")
        result = session.explore("not an action")
        self.assertFalse(result["ok"])
        self.assertEqual(session._explore_turn, 1)
        self.assertEqual(len(session.attempts), 1)
        fresh = core.WorldSession(self.cell, "NEW", fixture_only=True)
        self.assertFalse(fresh.probe("bad")["ok"])
        with self.assertRaises(ValueError):
            fresh.probe("PROBE " + self.root.lookup("probe", "relevant"))
        with self.assertRaises(ValueError):
            fresh.explore("bad")

    def test_latent_transition_in_full_private_audit_not_witnessed_banks(self):
        for cell in core.expand_cube(self.root):
            self.assertEqual(len(cell.edges), 9)
            self.assertEqual(len(cell.full_transitions), 10)
            latent = cell.full_transitions[-1]
            self.assertIsNone(latent.event)
            self.assertIsNone(latent.receipt)
            self.assertEqual((latent.source, latent.port, latent.destination),
                             (self.root.lookup("node", "X"), self.root.lookup("port", f"q{cell.distractor}"), self.root.lookup("node", "Z")))
            detour_ports = tuple(self.root.lookup("port", name) for name in (f"a{1-cell.old}", f"q{cell.distractor}", "u"))
            start = self.root.lookup("node", "S_L")
            dead_end = self.root.lookup("node", "Y")
            self.assertTrue(core.execute_route(cell.full_transitions, (start, dead_end, detour_ports))["graph_success"])
            self.assertFalse(core.execute_route(cell.edges, (start, dead_end, detour_ports))["legal"])
            for goal in (0, 1):
                raw = core.format_route(start, self.root.lookup("node", f"G_R{goal}"), detour_ports)
                result = core.score_route(cell, goal, raw)
                self.assertTrue(result["legal"])
                self.assertFalse(result["graph_success"])
                for cut in ("OLD", "NEW"):
                    self.assertEqual(core.oracle_routes_v2(cell, goal, cut), ())
            rows = core.ideal_rows(cell)
            self.assertEqual(len(rows), 15)
            events = [row for row in rows if row["kind"] == "EVENT"]
            self.assertEqual(len(events), 9)
            self.assertTrue(all(row["fields"]["source"] != latent.source for row in events))
            self.assertTrue(all(row["fields"]["receipt"] not in [self.root.lookup("receipt", name) for name in ("r9", "r10")] for row in events))
            queries = core.materialize_queries(rows)
            self.assertEqual(len(queries), 19)
            self.assertNotIn("READ EVENTS_AT " + latent.source, queries)
            graph = core.render_task(cell, 0, "EXACT_WITNESSED_GRAPH")["user"]
            self.assertNotIn(f"EDGE {latent.source} {latent.port} {latent.destination}\n", graph)
            self.assertNotIn("PROBE " + self.root.lookup("probe", "distractor"), core.ceiling_fixture(cell)["raw_public"])

    def test_distractor_commit_is_terminal_without_relevant_reveal(self):
        for cell in core.expand_cube(self.root):
            for fixture_only in (False, True):
                session = core.WorldSession(cell, "NEW", fixture_only=fixture_only)
                result = session.probe("PROBE " + self.root.lookup("probe", "distractor"))
                self.assertTrue(result["ok"])
                self.assertTrue(result["terminal"])
                self.assertTrue(session.terminal)
                self.assertIsNone(session._probe_result)
                self.assertEqual(result["public"].count("\n"), 1)
                self.assertNotIn(self.root.lookup("probe", "relevant"), result["public"])
                evidence_before = session.receipts
                for action in (session.public_affordances, session.explore_prompt, session.link_prompt,
                               lambda: session.event_prompt(result["receipt"]),
                               lambda: session.explore("EXPLORE " + self.root.lookup("node", "H") + " " + self.root.lookup("port", f"q{cell.relevant}")),
                               lambda: session.probe("PROBE " + self.root.lookup("probe", "relevant"))):
                    with self.assertRaises(ValueError):
                        action()
                fresh = self.root.lookup("event", "e8")
                raw = core.EVENT_WIRE.format(event=fresh, **result["receipt"])
                self.assertFalse(core.admit_event(raw, result["receipt"], session, fresh)["accepted"])
                self.assertFalse(core.admit_link("", [result["receipt"]]*2, session, self.root.lookup("link", "l4"), [])["accepted"])
                self.assertEqual(session.receipts, evidence_before)
                self.assertEqual(len(session.attempts), 1)

    def test_missing_malformed_and_unlisted_probes_terminate_without_bytes(self):
        probe = "PROBE " + self.root.lookup("probe", "relevant")
        unlisted = "PROBE " + core.build_root("excluded/1").lookup("probe", "relevant")
        for raw in ("", None, "bad", probe + "\n", " " + probe, probe + " " + probe, probe.lower(), unlisted):
            session = core.WorldSession(self.cell, "NEW")
            result = session.probe(raw)
            self.assertFalse(result["ok"])
            self.assertTrue(result["terminal"])
            self.assertEqual(result["public"], "")
            self.assertNotIn("receipt", result)
            self.assertEqual(session.receipts, [])
            self.assertEqual(len(session.attempts), 1)
            with self.assertRaises(ValueError):
                session.probe(probe)
            with self.assertRaises(ValueError):
                session.explore_prompt()
            with self.assertRaises(ValueError):
                session.link_prompt()

    def test_public_probe_wire_and_private_observation_receipts(self):
        self.assertEqual(core.PROBE_WIRE, "PROBE RESULT {probe} TESTED {source} TO {destination} AVAILABLE PORT {port}\n")
        for cell in core.expand_cube(self.root):
            for name, source, destination, receipt_slot, outcome in (
                ("relevant", "H", "S_R", "r9", cell.relevant),
                ("distractor", "X", "Z", "r10", cell.distractor),
            ):
                session = core.WorldSession(cell, "NEW")
                result = session.probe("PROBE " + self.root.lookup("probe", name))
                receipt = result["receipt"]
                self.assertEqual(receipt["kind"], "PROBE")
                self.assertEqual(receipt["receipt"], self.root.lookup("receipt", receipt_slot))
                self.assertTrue(session.check_receipt(receipt))
                expected = ("PROBE RESULT " + self.root.lookup("probe", name) + " TESTED " + self.root.lookup("node", source) +
                            " TO " + self.root.lookup("node", destination) + " AVAILABLE PORT " + self.root.lookup("port", f"q{outcome}") + "\n")
                self.assertEqual(result["public"], expected)
                for forbidden in (receipt["receipt"], self.root.label, "relevant", "distractor", "sha256", "terminal", "R=", "D="):
                    self.assertNotIn(forbidden, result["public"])
                fresh = self.root.lookup("event", "e8")
                self.assertFalse(core.admit_event(core.EVENT_WIRE.format(event=fresh, **receipt), receipt, session, fresh)["accepted"])
                with self.assertRaises(ValueError):
                    session.event_prompt(receipt)

    def test_actual_public_result_entropy_and_d_neutrality(self):
        def entropy(values):
            return -sum((count/len(values))*math.log2(count/len(values)) for count in Counter(values).values())
        def mutual_information(first, second):
            return entropy(first) + entropy(second) - entropy(list(zip(first, second)))
        for root_index in range(4):
            root = core.build_root(f"excluded/{root_index}")
            for old in (0, 1):
                quartet = [cell for cell in core.expand_cube(root) if cell.old == old]
                outputs = {name: [core.WorldSession(cell, "NEW").probe("PROBE " + root.lookup("probe", name))["public"] for cell in quartet]
                           for name in ("relevant", "distractor")}
                self.assertEqual(len(set(zip(outputs["relevant"], outputs["distractor"]))), 4)
                for goal in (0, 1):
                    labels = [core.oracle_route_v1(cell, goal) for cell in quartet]
                    self.assertEqual([entropy(outputs["relevant"]), entropy(outputs["distractor"]),
                                      mutual_information(outputs["relevant"], labels), mutual_information(outputs["distractor"], labels)], [1, 1, 1, 0])
                    for render_id in ("RA", "RB"):
                        self.assertEqual(len({core.render_reachout(cell, goal, render_id) for cell in quartet}), 1)
                    for first, second in ((quartet[0], quartet[1]), (quartet[2], quartet[3])):
                        self.assertEqual([row["raw"] for row in core.ideal_rows(first)], [row["raw"] for row in core.ideal_rows(second)])
                        self.assertEqual(core.ceiling_fixture(first)["raw_public"], core.ceiling_fixture(second)["raw_public"])
                        for cut in (None, "OLD", "NEW"):
                            self.assertEqual(core.oracle_routes_v2(first, goal, cut), core.oracle_routes_v2(second, goal, cut))

    def test_bound_goal_and_root_visibility_and_probe_order_balance(self):
        positions = Counter()
        for root_index in range(4):
            root = core.build_root(f"excluded/{root_index}")
            for old in (0, 1):
                cell = core.WorldCell(root, old, 0, 0)
                for goal in (0, 1):
                    for render_id in ("RA", "RB"):
                        public = core.render_reachout(cell, goal, render_id)
                        relevant = root.lookup("probe", "relevant")
                        distractor = root.lookup("probe", "distractor")
                        positions[1 if public.index(relevant) < public.index(distractor) else 2] += 1
                        self.assertIn("START " + root.lookup("node", "S_L"), public)
                        self.assertIn("GOAL " + root.lookup("node", f"G_R{goal}"), public)
                        for forbidden in (root.label, "relevant", "distractor", "PROBE_0", "PROBE_1"):
                            self.assertNotIn(forbidden, public)
                        for goal_slot in core.SLOTS["goal"]:
                            self.assertNotIn(root.lookup("goal", goal_slot), public)
                    route = core.oracle_route_v1(cell, goal)
                    start, target, _ = core.parse_route(route)
                    self.assertTrue(start.startswith("N_") and target.startswith("N_"))
        self.assertEqual(positions, {1: 16, 2: 16})

    def test_relevant_continuation_one_event_two_links_and_chronology(self):
        old, admissions = self.old_life()
        events = {item["row"]["fields"]["event"]: item["row"] for item in admissions if item["kind"] == "EVENT"}
        self.assertEqual(events[self.root.lookup("event", "e5")]["fields"]["source"], self.root.lookup("node", "Z"))
        self.assertEqual(events[self.root.lookup("event", "e7")]["fields"]["source"], self.root.lookup("node", "B"))
        session = core.WorldSession(self.cell, "NEW", old)
        probe = session.probe("PROBE " + self.root.lookup("probe", "relevant"))
        self.assertFalse(probe["terminal"])
        public = session.public_affordances()
        receipt = session.explore("EXPLORE " + public["source"] + " " + public["ports"][0])["receipt"]
        self.assertEqual(receipt["receipt"], self.root.lookup("receipt", "r8"))
        self.assertEqual(receipt["kind"], "EXPLORE")
        self.assertEqual(receipt["previous_sha256"], probe["receipt"]["sha256"])
        fresh = self.root.lookup("event", "e8")
        new = core.admit_event(core.EVENT_WIRE.format(event=fresh, **receipt), receipt, session, fresh)
        self.assertTrue(new["accepted"])
        events[fresh] = new["row"]
        for index, (first_id, second_id) in enumerate(((self.root.lookup("event", "e1"), fresh), (fresh, self.root.lookup("event", "e3")))):
            first, second = events[first_id], events[second_id]
            fields = dict(link=self.root.lookup("link", f"l{index+4}"), first=first_id, second=second_id,
                          via=first["fields"]["destination"], receipt_first=first["fields"]["receipt"], receipt_second=second["fields"]["receipt"])
            evidence = [next(item for item in old.receipts + session.receipts if item["receipt"] == fields[key]) for key in ("receipt_first", "receipt_second")]
            self.assertTrue(core.admit_link(core.LINK_WIRE.format(**fields), evidence, session, fields["link"], [first, second])["accepted"])
        with self.assertRaises(ValueError):
            session.link_prompt()
        with self.assertRaises(ValueError):
            session.explore_prompt()
        self.assertFalse(core.admit_event(new["raw"], receipt, session, fresh)["accepted"])

    def test_probe_receipt_cannot_substitute_link_evidence(self):
        old, admissions = self.old_life()
        session = core.WorldSession(self.cell, "NEW", old)
        probe = session.probe("PROBE " + self.root.lookup("probe", "relevant"))["receipt"]
        public = session.public_affordances()
        receipt = session.explore("EXPLORE " + public["source"] + " " + public["ports"][0])["receipt"]
        fresh = self.root.lookup("event", "e8")
        event = core.admit_event(core.EVENT_WIRE.format(event=fresh, **receipt), receipt, session, fresh)["row"]
        first = admissions[1]["row"]
        first_receipt = old.receipts[1]
        fields = dict(link=self.root.lookup("link", "l4"), first=first["fields"]["event"], second=fresh,
                      via=public["source"], receipt_first=first_receipt["receipt"], receipt_second=probe["receipt"])
        result = core.admit_link(core.LINK_WIRE.format(**fields), [first_receipt, probe], session, fields["link"], [first, event])
        self.assertFalse(result["accepted"])
        self.assertIn("executed", result["error"])

    def test_strict_parsers_no_normalization(self):
        rows = core.ideal_rows(self.cell)
        event, link = rows[0]["raw"], rows[8]["raw"]
        for raw, parser in ((event, core.parse_event_line), (link, core.parse_link_line)):
            parser(raw)
            for invalid in (raw[:-1], raw + "\n", " " + raw, raw.replace(" ", "  ", 1), raw.replace("\n", "\r\n"), "```\n" + raw + "```", raw + raw):
                with self.assertRaises(ValueError):
                    parser(invalid)
        route = core.oracle_route_v1(self.cell, 0)
        for invalid in (route + "\n", " " + route, route + " ", route.lower()):
            self.assertFalse(core.score_route(self.cell, 0, invalid)["strict"])
        with self.assertRaises(ValueError):
            core.parse_read("READ EVENT " + self.root.lookup("event", "e0") + "\n")

    def test_one_shot_route_session(self):
        session = core.RouteSession(self.cell, 0)
        self.assertEqual(session.commit("bad"), {"terminal": True, "arrived": False})
        with self.assertRaises(ValueError):
            session.commit(core.oracle_route_v1(self.cell, 0))

    def test_event_exact_raw_and_no_repair(self):
        session = core.WorldSession(self.cell, "OLD")
        source, ports = session._affordances()
        receipt = session.explore("EXPLORE " + source + " " + ports[0])["receipt"]
        fresh = self.root.lookup("event", "e0")
        raw = core.EVENT_WIRE.format(event=fresh, **receipt)
        result = core.admit_event(raw, receipt, session, fresh)
        self.assertTrue(result["accepted"])
        self.assertEqual(result["row"]["raw"], raw)
        self.assertEqual(result["byte_end"], len(raw.encode()))
        self.assertEqual(result["generation_sha256"], hashlib.sha256(raw.encode()).hexdigest())
        self.assertFalse(result["native_generation_verified"])
        self.assertFalse(core.admit_event(raw, receipt, session, fresh)["accepted"])

    def test_malformed_event_consumes_opportunity(self):
        session = core.WorldSession(self.cell, "OLD")
        source, ports = session._affordances()
        receipt = session.explore("EXPLORE " + source + " " + ports[0])["receipt"]
        fresh = self.root.lookup("event", "e0")
        raw = core.EVENT_WIRE.format(event=fresh, **receipt)
        self.assertFalse(core.admit_event("```\n" + raw + "```", receipt, session, fresh)["accepted"])
        self.assertFalse(core.admit_event(raw, receipt, session, fresh)["accepted"])

    def test_invented_field_or_fresh_handle_not_repaired(self):
        for mutation in ("destination", "event"):
            session = core.WorldSession(self.cell, "OLD")
            source, ports = session._affordances()
            receipt = session.explore("EXPLORE " + source + " " + ports[0])["receipt"]
            fresh = self.root.lookup("event", "e0")
            fields = dict(event=fresh, **receipt)
            fields[mutation] = self.root.lookup("node", "X") if mutation == "destination" else self.root.lookup("event", "e1")
            result = core.admit_event(core.EVENT_WIRE.format(**fields), receipt, session, fresh)
            self.assertFalse(result["accepted"])
            self.assertIsNone(result["row"])

    def test_old_receipt_cannot_be_reissued_after_new_action(self):
        session = core.WorldSession(self.cell, "OLD")
        source, ports = session._affordances()
        earlier = session.explore("EXPLORE " + source + " " + ports[0])["receipt"]
        source, ports = session._affordances()
        session.explore("EXPLORE " + source + " " + ports[0])
        fresh = self.root.lookup("event", "e0")
        self.assertFalse(core.admit_event(core.EVENT_WIRE.format(event=fresh, **earlier), earlier, session, fresh)["accepted"])

    def test_receipt_tamper_crossroot_and_detachment(self):
        session = core.WorldSession(self.cell, "OLD")
        source, ports = session._affordances()
        receipt = session.explore("EXPLORE " + source + " " + ports[0])["receipt"]
        altered = copy.deepcopy(receipt)
        altered["destination"] = self.root.lookup("node", "X")
        altered["sha256"] = core.digest({key: value for key, value in altered.items() if key != "sha256"})
        with self.assertRaises(ValueError):
            session.check_receipt(altered)
        other = core.WorldSession(core.WorldCell(core.build_root("excluded/1"), 0, 0, 0), "OLD")
        with self.assertRaises(ValueError):
            other.check_receipt(receipt)
        snapshot = session.receipts
        snapshot.clear()
        self.assertEqual(len(session.receipts), 1)

    def test_old_formation_all_rows_and_denominators(self):
        for old in (0, 1):
            _, admissions = self.old_life(core.WorldCell(self.root, old, 0, 0))
            report = core.formation_report(admissions)
            self.assertTrue(report["structural_complete"])
            self.assertFalse(report["formation_complete"])
            self.assertEqual(report["status"], "REQUIRED_BANK_UNBOUND")
            self.assertEqual(report["link_precision"], [4, 4])
            self.assertFalse(core.formation_report(admissions[:-1])["formation_complete"])
            self.assertEqual(core.formation_report(admissions[:-1])["missing_calls"], 1)
            self.assertEqual(len(core.materialize_queries([item["row"] for item in admissions])), 17)
            with self.assertRaises(ValueError):
                core.formation_report(admissions + admissions[:1])
        empty = core.formation_report([])
        self.assertEqual(empty["missing_calls"], 12)
        self.assertEqual(empty["link_precision"], [0, 4])
        self.assertFalse(empty["formation_complete"])

    def test_presealed_bank_is_not_reselected_after_child_choices(self):
        cell = core.WorldCell(self.root, 1, 0, 0)
        bank = {row["fields"].get("event", row["fields"].get("link")): copy.deepcopy(row["fields"])
                for row in core.ideal_rows(cell)[:12]}
        bank_hash = core.digest(bank)
        _, admissions = self.old_life(cell)
        report = core.formation_report(admissions, required_bank=bank)
        self.assertTrue(report["structural_complete"])
        self.assertFalse(report["formation_complete"])
        self.assertFalse(report["required_bank_verified"])
        self.assertEqual(report["status"], "VS_FORMATION_BANK_MISMATCH")
        self.assertIn(self.root.lookup("event", "e0"), report["bank_different"])
        self.assertEqual(core.digest(bank), bank_hash)
        self.assertEqual(admissions[0]["row"]["fields"]["destination"], self.root.lookup("node", "X"))
        missing = core.formation_report(admissions[:-1], required_bank=bank)
        self.assertIn(self.root.lookup("link", "l3"), missing["bank_missing"])
        self.assertFalse(missing["formation_complete"])

    def test_explicit_bank_comparison_success_does_not_verify_native(self):
        _, admissions = self.old_life()
        bank = {item["row"]["fields"].get("event", item["row"]["fields"].get("link")): item["row"]["fields"]
                for item in admissions}
        report = core.formation_report(admissions, required_bank=bank)
        self.assertTrue(report["formation_complete"])
        self.assertTrue(report["required_bank_verified"])
        self.assertFalse(report["native_generation_verified"])

    def test_parent_reset_and_new_links_use_private_verification(self):
        old, admissions = self.old_life()
        session = core.WorldSession(self.cell, "NEW", old, fixture_only=True)
        self.assertEqual(session.receipts, [])
        probe = session.probe("PROBE " + self.root.lookup("probe", "relevant"))
        for row in [item["row"] for item in admissions]:
            self.assertNotIn(row["raw"], probe["public"])
            self.assertNotIn(row["raw"], session.explore_prompt())
        source, ports = session._affordances()
        receipt = session.explore("EXPLORE " + source + " " + ports[0])["receipt"]
        fresh = self.root.lookup("event", "e8")
        event = core.admit_event(core.EVENT_WIRE.format(event=fresh, **receipt), receipt, session, fresh)["row"]
        old_events = [item["row"] for item in admissions if item["kind"] == "EVENT"]
        predecessor = next(row for row in old_events if row["fields"]["destination"] == source)
        old_receipt = next(item for item in old.receipts if item["receipt"] == predecessor["fields"]["receipt"])
        link_id = self.root.lookup("link", "l4")
        self.assertNotIn(predecessor["fields"]["event"], session.link_prompt())
        raw = core.LINK_WIRE.format(link=link_id, first=predecessor["fields"]["event"], second=fresh,
                                   via=source, receipt_first=old_receipt["receipt"], receipt_second=receipt["receipt"])
        result = core.admit_link(raw, [old_receipt, receipt], session, link_id, [predecessor, event])
        self.assertTrue(result["accepted"], result)
        wrong_cell = core.WorldCell(self.root, 1, 0, 0)
        with self.assertRaises(ValueError):
            core.WorldSession(wrong_cell, "NEW", old, fixture_only=True)

    def test_probe_not_event_and_fixture_not_authentic(self):
        session = core.WorldSession(self.cell, "NEW", fixture_only=True)
        receipt = session.probe("PROBE " + self.root.lookup("probe", "relevant"))["receipt"]
        fresh = self.root.lookup("event", "e8")
        raw = core.EVENT_WIRE.format(event=fresh, **receipt)
        self.assertFalse(core.admit_event(raw, receipt, session, fresh)["accepted"])
        with self.assertRaises(ValueError):
            session.event_prompt(receipt)

    def test_new_link_parent_removal_splicing_and_taint(self):
        old, admissions = self.old_life()
        old_events = [item["row"] for item in admissions if item["kind"] == "EVENT"]
        predecessor = next(row for row in old_events if row["fields"]["destination"] == self.root.lookup("node", "H"))
        old_receipt = next(item for item in old.receipts if item["receipt"] == predecessor["fields"]["receipt"])
        for invalid in ("parent_removed", "receipt_swapped", "fixture", "control", "old_only"):
            session = core.WorldSession(self.cell, "NEW", None if invalid == "parent_removed" else old, fixture_only=True)
            session.probe("PROBE " + self.root.lookup("probe", "relevant"))
            source, ports = session._affordances()
            receipt = session.explore("EXPLORE " + source + " " + ports[0])["receipt"]
            fresh = self.root.lookup("event", "e8")
            new_event = core.admit_event(core.EVENT_WIRE.format(event=fresh, **receipt), receipt, session, fresh)["row"]
            fields = dict(link=self.root.lookup("link", "l4"), first=predecessor["fields"]["event"], second=fresh,
                          via=source, receipt_first=old_receipt["receipt"], receipt_second=receipt["receipt"])
            events = [predecessor, new_event]
            evidence = [old_receipt, receipt]
            if invalid == "receipt_swapped":
                evidence.reverse()
            elif invalid == "fixture":
                events[1] = core.ideal_rows(self.cell)[12]
            elif invalid == "control":
                events[0] = core.make_event_twin([predecessor], self.root)[0]
            elif invalid == "old_only":
                events = old_events[:2]
                evidence = old.receipts[:2]
            result = core.admit_link(core.LINK_WIRE.format(**fields), evidence, session, fields["link"], events)
            self.assertFalse(result["accepted"], invalid)

    def test_raw_generation_contract_does_not_authenticate_native(self):
        _, admissions = self.old_life()
        for admission in admissions:
            self.assertEqual(admission["origin"], "CALLER_SUPPLIED_GENERATION")
            self.assertFalse(admission["native_generation_verified"])
            self.assertFalse(admission["row"]["provenance"]["native_generation_verified"])

    def test_query_counts_multirow_sort_copy_only(self):
        rows = core.ideal_rows(self.cell)
        old, full = core.materialize_queries(rows[:12]), core.materialize_queries(rows)
        self.assertEqual((len(old), len(full)), (17, 19))
        atoms = core.materialize_queries([row for row in rows[:12] if row["kind"] == "EVENT"])
        self.assertEqual(len(atoms), 14)
        for queries, request, wanted in (
            (old, "READ EVENTS_AT " + self.root.lookup("node", "S_L"), ("e0", "e6")),
            (old, "READ EVENTS_AT " + self.root.lookup("node", "B"), ("e4", "e5")),
            (old, "READ LINKS_FROM " + self.root.lookup("event", "e3"), ("l2", "l3")),
            (full, "READ EVENTS_AT " + self.root.lookup("node", "H"), ("e2", "e8")),
            (full, "READ LINKS_FROM " + self.root.lookup("event", "e1"), ("l1", "l4")),
        ):
            namespace = "event" if wanted[0].startswith("e") else "link"
            identifiers = sorted(self.root.lookup(namespace, slot) for slot in wanted)
            self.assertEqual(queries[request]["support"], identifiers)
            by_id = {row["fields"].get("event", row["fields"].get("link")): row["raw"] for row in rows}
            self.assertEqual(queries[request]["target"], "".join(by_id[identifier] for identifier in identifiers))

    def test_query_compiler_rejects_tamper_duplicates_mixed_roots(self):
        rows = core.ideal_rows(self.cell)
        with self.assertRaises(ValueError):
            core.materialize_queries(rows + rows[:1])
        altered = copy.deepcopy(rows)
        altered[0]["raw"] = altered[0]["raw"].replace(" AT ", "  AT ")
        with self.assertRaises(ValueError):
            core.materialize_queries(altered)
        with self.assertRaises(ValueError):
            core.materialize_queries(rows + core.ideal_rows(core.WorldCell(core.build_root("excluded/1"), 0, 0, 0)))

    def test_memory_parser_truth_table(self):
        rows = core.ideal_rows(self.cell)
        expected = rows[0]["raw"] + rows[1]["raw"]
        self.assertTrue(core.score_memory_response(expected, expected)["strict"])
        for raw in (expected[:-1], "```\n" + expected + "```", "```text\n" + expected + "```\n"):
            result = core.score_memory_response(raw, expected)
            self.assertTrue(result["semantic"])
            self.assertFalse(result["strict"])
        for raw in ("Here:\n" + expected, rows[0]["raw"], rows[0]["raw"] * 2,
                    rows[1]["raw"] + rows[0]["raw"], expected + rows[0]["raw"],
                    "```json\n" + expected + "```", "```\n" + expected + "```\n```\n" + expected + "```",
                    "MISS\n" + expected, expected + "\n"):
            self.assertFalse(core.score_memory_response(raw, expected)["semantic"], raw)

    def test_false_rows_even_with_refusal_or_prose(self):
        rows = core.ideal_rows(self.cell)
        correct, false = rows[0]["raw"], rows[1]["raw"]
        for raw in (false, "MISS\n" + false, "text " + false[:-1] + " prose", "```text\n" + false + "```"):
            self.assertTrue(core.score_memory_response(raw, correct)["usable_false_row"], raw)
            self.assertTrue(core.score_memory_response(raw, None)["usable_false_row"], raw)
        for raw in ("MISS", "MISS\n"):
            self.assertTrue(core.score_memory_response(raw, None)["refusal"])
        self.assertFalse(core.score_memory_response("MISS ", None)["refusal"])
        self.assertFalse(core.score_memory_response("text\n" + correct, correct)["usable_false_row"])

    def test_control_taint_twin_and_permutation(self):
        rows = core.ideal_rows(self.cell)[:12]
        twin = core.make_event_twin(rows, self.root)
        other = core.ideal_rows(core.WorldCell(self.root, 1, 0, 0))[:12]
        for original, changed in zip(rows, twin):
            self.assertEqual(changed["taint"], "CONTROL")
            self.assertEqual(changed["provenance"]["source_sha256"], original["sha256"])
        self.assertEqual(core.routes_from_rows(twin, self.root.lookup("node", "S_L"), self.root.lookup("node", "G_L")),
                         core.routes_from_rows(other, self.root.lookup("node", "S_L"), self.root.lookup("node", "G_L")))
        permuted = core.make_link_permute(rows, self.root)
        self.assertEqual([row["raw"] for row in permuted[:8]], [row["raw"] for row in rows[:8]])
        for index, donor in enumerate((2, 3, 0, 1)):
            self.assertEqual(permuted[8+index]["fields"]["first"], rows[8+index]["fields"]["first"])
            self.assertEqual(permuted[8+index]["fields"]["second"], rows[8+donor]["fields"]["second"])
        self.assertEqual(core.routes_from_rows(permuted, self.root.lookup("node", "S_L"), self.root.lookup("node", "G_L"), True), ())

    def test_read_cuts_cover_grouped_and_incident_rows(self):
        queries = core.materialize_queries(core.ideal_rows(self.cell))
        original_hash = core.digest(queries)
        report = core.cut_queries(queries, self.root, "OLD")
        self.assertIn("READ EVENT " + self.root.lookup("event", "e0"), report["affected"])
        self.assertIn("READ EVENTS_AT " + self.root.lookup("node", "S_L"), report["affected"])
        self.assertIn("READ LINKS_FROM " + self.root.lookup("event", "e0"), report["affected"])
        for request in queries:
            if request not in report["affected"]:
                self.assertEqual(report["queries"][request], queries[request])
        new = core.cut_queries(queries, self.root, "NEW")
        self.assertIn("READ LINKS_FROM " + self.root.lookup("event", "e1"), new["affected"])
        self.assertIn("READ LINKS_FROM " + self.root.lookup("event", "e8"), new["affected"])
        self.assertEqual(core.digest(queries), original_hash)
        paired = core.paired_cuts(self.cell, 0, core.ideal_rows(self.cell))
        self.assertFalse(paired["link_information_necessary"])
        self.assertEqual(paired["expected_graph"], {"OLD": False, "NEW": False})

    def test_diagnostic_universe_and_offset_boundary(self):
        queries = core.materialize_queries(core.ideal_rows(self.cell))
        universe = [query["target"] for query in queries.values()]
        report = core.diagnostic_registry(queries, universe)
        for request, candidates in report["addresses"].items():
            self.assertTrue(candidates)
            self.assertNotIn(queries[request]["target"], [item["target"] for item in candidates])
            self.assertEqual(len({item["sha256"] for item in candidates}), len(candidates))
        target = core.ideal_rows(self.cell)[0]["raw"]
        self.assertEqual(core.classify_offsets(target, [(0, 6), (5, 7), (6, 18), (18, 22), (len(target), len(target))]),
                         ["grammar", "content", "content", "grammar", "grammar"])
        with self.assertRaises(ValueError):
            core.classify_offsets(target, [(0, len(target)+1)])
        with self.assertRaises(ValueError):
            core.diagnostic_registry({"single": {"target": target}}, [target])

    def test_service_returns_raw_source_identity_without_inference(self):
        queries = core.materialize_queries(core.ideal_rows(self.cell))
        request = "READ EVENT " + self.root.lookup("event", "e0")
        result = core.read_query(queries, request)
        self.assertEqual(result["raw"], queries[request]["target"])
        self.assertEqual(result["source_sha256"], queries[request]["source_sha256"])
        absent = "READ LINKS_FROM " + self.root.lookup("event", "e6")
        self.assertEqual(core.read_query(queries, absent)["raw"], "MISS")
        self.assertNotIn(absent, queries)
        altered = copy.deepcopy(queries)
        alternate = "READ EVENT " + self.root.lookup("event", "e1")
        altered[request] = dict(altered[alternate], request=request)
        with self.assertRaises(ValueError):
            core.read_query(altered, request)
        cut = core.cut_queries(queries, self.root, "OLD")
        self.assertEqual(core.read_query(cut["queries"], request)["source_sha256"], [])

    def test_exhaustive_cpu_report_honest_readiness(self):
        report = core.audit_construct([core.build_root(f"excluded/{index}") for index in range(4)])
        self.assertTrue(report["route_construct_passed"])
        self.assertFalse(report["full_construct_passed"])
        self.assertFalse(report["ready_for_model_calls"])
        self.assertEqual(report["scope"], "CPU_BOUND_WORLD_DEFINITION_NOT_NATIVE_READINESS")
        self.assertFalse(report["production_binding"]["execution_contract_valid"])
        self.assertEqual(len(report["route_cut_decisions"]), 192)
        self.assertEqual(len(report["atoms_link_decisions"]), 48)
        self.assertEqual(len(report["link_successor_support"]), 32)
        self.assertEqual(len(report["entropy_quartets"]), 16)
        self.assertEqual(len(report["d_neutrality_pairs"]), 32)
        self.assertTrue(all(row["latent_transition_included"] for row in report["route_cut_decisions"]))
        self.assertEqual(report["projection_ceilings"]["OLD_ONLY_TEXT"]["bayes_correct"], 32)
        self.assertEqual(report["projection_ceilings"]["NEW_ONLY_TEXT"]["bayes_correct"], 32)
        self.assertEqual(report["projection_ceilings"]["NONE_OFF"]["bayes_correct"], 16)


if __name__ == "__main__":
    unittest.main()
