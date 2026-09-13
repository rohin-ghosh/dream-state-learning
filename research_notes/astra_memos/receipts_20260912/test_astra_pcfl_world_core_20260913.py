"""CPU structural fixtures only; exact scientific PCFL construct stays blocked."""
import ast
import copy
from dataclasses import replace
from itertools import product
from pathlib import Path
import unittest
from unittest.mock import patch

import astra_pcfl_world_core_20260913 as core


class WorldTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = core.build_fixture_root(0, 0)
        cls.cells = core.expand_cube(cls.root)
        cls.certificate = core.construct_gate()

    def test_unbound_gate_never_authorizes_model_calls(self):
        result = self.certificate
        self.assertEqual(result["status"], "VS_ASSAY_INVALID")
        self.assertEqual(result["reason"], "UNBOUND_SCIENTIFIC_CONSTRUCT_NOT_A_FAILED_MODEL")
        self.assertFalse(result["ready_for_model_calls"])
        self.assertFalse(result["full_construct_passed"])
        self.assertEqual(result["declared_dev_slots"], [dict(slot=0, realized_old=0, root_manifest=None),
                                                       dict(slot=1, realized_old=1, root_manifest=None)])
        self.assertEqual(len(result["unresolved_bindings"]), 6)
        self.assertIn("distractor", " ".join(result["unresolved_bindings"]))

    def test_golden_inventory_route_receipt_task_and_certificate(self):
        self.assertEqual(self.root.identifier, "cfc0a5c3dbf89597b1e962d3")
        inventory = {namespace: [[slot, identifier] for slot, identifier in values] for namespace, values in self.root.inventory}
        self.assertEqual(core.digest(dict(id=self.root.identifier, inventory=inventory)),
                         "15dcc382f9df109ce8d288e165d6ee12928d6d56a0b619edb9b9e89edf40ae72")
        route = "ROUTE bb60c701b91fd1d7e72a5c8c 1df2576786824f3c0ba565a1 : e5b2c32043e37aed72ed07d9,969eb67b3c660e73ccef3b00,c15a39c9bef8d603797cd91d,13c9599724a554cc40555dc2,8186977ccccdb1985019f5e4"
        self.assertEqual(core.oracle_route_v1(self.cells[0], 0), route)
        self.assertEqual(core.oracle_routes_v2(self.cells[0], 0), (route,))
        self.assertEqual(core.digest(core.task_fields(self.cells[0], 0)), "8f7974c9eb52109ce6fdff8b3b3469f32a9db157fd4486c9782e95ba28acc409")
        edge = self.cells[0].edges[0]
        receipt = core.execute_action(self.cells[0], dict(source=edge.source, port=edge.port), stage="OLD")[-1]
        self.assertEqual(receipt["sha256"], "1cefce3ca168466e524ca4c448db40349e9332676092dd9023baf7000622320e")
        self.assertEqual(self.certificate["sha256"], "2249743f96b919a6741bc21585d81442ddda25d642b88a8029d0dd00ddcad0c8")

    def test_fixture_root_and_namespace_determinism(self):
        self.assertEqual(core.build_fixture_root(0, 0), self.root)
        self.assertNotEqual(core.build_fixture_root(1, 1), self.root)
        report = core.validate_inventory(self.root)
        self.assertEqual(report["identifier_count"], 52)
        self.assertFalse(report["tokenizer_equality_verified"])
        identifiers = [identifier for namespace, values in self.root.inventory for slot, identifier in values]
        self.assertEqual(len(set(identifiers)), len(identifiers))
        self.assertTrue(all(value.isascii() and len(value) == 24 for value in identifiers))
        with patch.object(core, "digest", return_value="0" * 64) as allocate:
            with self.assertRaisesRegex(ValueError, "collision"):
                core.build_fixture_root(7, 0)
            self.assertEqual(allocate.call_count, 52)

    def test_strict_seed_bits_wire_and_namespace_schema(self):
        for invalid in (True, -1, 1.0, "0", None):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                core.build_fixture_root(invalid, 0)
        for invalid in (False, 2, "1", float("nan")):
            with self.assertRaises(ValueError):
                core.build_fixture_root(0, invalid)
        with self.assertRaises(ValueError):
            core.canonical(self.cells[0])
        with self.assertRaises(ValueError):
            core.canonical({"bits": (0, 1)})
        with self.assertRaises(ValueError):
            core.canonical({"value": float("nan")})
        with self.assertRaisesRegex(ValueError, "immutable"):
            core.validate_inventory(replace(self.root, inventory=list(self.root.inventory)))

    def test_exact_cube_old_swap_and_distractor_route_independence(self):
        self.assertEqual([(cell.old, cell.relevant, cell.distractor) for cell in self.cells], list(product((0, 1), repeat=3)))
        for cell in self.cells:
            self.assertEqual(len(cell.edges), 9)
            other_old = next(other for other in self.cells if (other.old, other.relevant, other.distractor) == (1 - cell.old, cell.relevant, cell.distractor))
            self.assertEqual(cell.edges[0].port, other_old.edges[6].port)
            self.assertEqual(cell.edges[6].port, other_old.edges[0].port)
            other_d = next(other for other in self.cells if (other.old, other.relevant, other.distractor) == (cell.old, cell.relevant, 1 - cell.distractor))
            self.assertEqual(cell.edges, other_d.edges)
            self.assertEqual(core.oracle_route_v1(cell, 1), core.oracle_route_v1(other_d, 1))

    def test_all_paths_and_registered_cuts_agree_exhaustively(self):
        for root in (core.build_fixture_root(seed, seed % 2) for seed in range(6)):
            for cell in core.expand_cube(root):
                for goal in (0, 1):
                    route = core.oracle_route_v1(cell, goal)
                    self.assertEqual(core.oracle_routes_v2(cell, goal), (route,))
                    score = core.score_route(cell, goal, route)
                    self.assertTrue(score["graph_success"] and score["used_old"] and score["used_new"])
                    for cut in ("OLD", "NEW"):
                        self.assertIsNone(core.oracle_route_v1(cell, goal, cut))
                        self.assertEqual(core.oracle_routes_v2(cell, goal, cut), ())
                        self.assertFalse(core.score_route(cell, goal, route, cut)["graph_success"])
                    self.assertTrue(core.score_route(cell, goal, route, "NEW")["used_old"])

    def test_structural_two_and_four_root_counts_are_not_native_certificates(self):
        for name, counts in (("two_slot_fixture", (16, 32, 96, 16, 16, 4, 8)),
                             ("four_root_fixture", (32, 64, 192, 32, 32, 8, 16))):
            result = self.certificate[name]
            self.assertEqual(tuple(result[key] for key in ("worlds", "delayed_tasks", "parse_execute_decisions", "old_only_groups",
                                                           "new_only_groups", "task_groups", "entropy_quartets")), counts)
            self.assertTrue(result["structural_checks_passed"])
            self.assertFalse(result["full_construct_passed"])
            self.assertFalse(result["ready_for_model_calls"])
            self.assertEqual(result["missing_native_projections"], ["goal_text", "outcome_frequencies", "affordance_order"])

    def test_public_fields_exclude_private_bits_targets_and_symbolic_slots(self):
        forbidden = ("relevant", "distractor", "old", "oracle", "correct", "S_L", "G_R", "e0", "e8")
        for cell in self.cells:
            public = core.task_fields(cell, 0)
            self.assertEqual(set(public), core.PUBLIC_TASK_FIELDS)
            self.assertEqual(public["candidates"], [])
            self.assertEqual((public["commits"], public["retries"], public["intermediate_returns"]), (1, 0, 0))
            self.assertFalse(set(forbidden) & set(public))
            public["candidates"].append("attempt to mutate")
            self.assertEqual(core.task_fields(cell, 0)["candidates"], [])

    def test_candidate_free_parser_and_one_shot_no_intermediate_return(self):
        cell = self.cells[0]
        route = core.oracle_route_v1(cell, 0)
        for raw in (" " + route, route + "\n", "thought\n" + route, route + "\n" + route,
                    "```\n" + route + "\n```", route.replace(" : ", ":"), b"ROUTE", "", None):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                core.parse_route(raw)
        session = core.RouteSession(cell, 0)
        self.assertEqual(session.commit(route), dict(terminal=True, arrived=True))
        with self.assertRaisesRegex(ValueError, "consumed"):
            session.commit(route)
        session = core.RouteSession(cell, 0)
        self.assertEqual(session.commit("bad command"), dict(terminal=True, arrived=False))
        with self.assertRaises(ValueError):
            session.commit(route)

    def test_wrong_root_goal_port_and_dependency_cuts_fail(self):
        cell = self.cells[0]
        route = core.oracle_route_v1(cell, 0)
        other = core.expand_cube(core.build_fixture_root(1, 1))[0]
        self.assertFalse(core.score_route(other, 0, route)["legal"])
        self.assertFalse(core.score_route(cell, 1, route)["legal"])
        start, target, ports = core.parse_route(route)
        wrong = core.format_route(start, target, (cell.root.lookup("port", "a1"),) + ports[1:])
        self.assertFalse(core.score_route(cell, 0, wrong)["graph_success"])
        with self.assertRaises(ValueError):
            core.oracle_route_v1(cell, 0, "UNREGISTERED")

    def test_actual_action_receipts_have_exact_chronology(self):
        cell, history = self.cells[0], ()
        for edge in cell.edges[:8]:
            prior = history
            history = core.execute_action(cell, dict(source=edge.source, port=edge.port), stage="OLD", history=history)
            receipt = history[-1]
            self.assertEqual(set(receipt), core.PUBLIC_RECEIPT_FIELDS)
            self.assertEqual((receipt["source"], receipt["port"], receipt["destination"]), (edge.source, edge.port, edge.destination))
            self.assertTrue(core.check_receipt(cell, receipt, prior))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            core.execute_action(cell, dict(source=cell.edges[0].source, port=cell.edges[0].port), stage="OLD", history=history)

    def test_unexecuted_or_premature_actions_never_make_receipts(self):
        cell = self.cells[0]
        edge = cell.edges[8]
        with self.assertRaises(ValueError):
            core.execute_action(cell, dict(source=edge.source, port=edge.port), stage="OLD")
        with self.assertRaisesRegex(ValueError, "allowlist"):
            core.execute_action(cell, dict(source=edge.source, port=edge.port, destination=edge.destination), stage="NEW")
        receipt = core.execute_action(cell, dict(source=edge.source, port=edge.port), stage="NEW")[-1]
        self.assertTrue(core.check_receipt(cell, receipt))
        self.assertEqual(receipt["turn"], 0)
        self.assertIsNone(receipt["previous_sha256"])

    def test_rehashed_receipt_tampering_and_prior_corruption_rejected(self):
        cell = self.cells[0]
        edge = cell.edges[0]
        history = core.execute_action(cell, dict(source=edge.source, port=edge.port), stage="OLD")
        edge = cell.edges[1]
        history = core.execute_action(cell, dict(source=edge.source, port=edge.port), stage="OLD", history=history)
        for field, value in (("destination", cell.root.lookup("node", "X")), ("turn", True), ("previous_sha256", "bad"),
                             ("root", "0" * 24), ("stage", "NEW")):
            changed = copy.deepcopy(history[-1])
            changed[field] = value
            changed["sha256"] = core.digest({key: item for key, item in changed.items() if key != "sha256"})
            with self.subTest(field=field), self.assertRaises(ValueError):
                core.check_receipt(cell, changed, history[:-1])
        prior = copy.deepcopy(history[0])
        prior["port"] = cell.root.lookup("port", "q1")
        with self.assertRaisesRegex(ValueError, "hash"):
            core.check_receipt(cell, history[-1], (prior,))

    def test_symbolic_entropy_full_tables_and_independent_calculation(self):
        for name in ("two_slot_fixture", "four_root_fixture"):
            for result in self.certificate[name]["symbolic_entropy"]:
                self.assertEqual(result["table"], [[0, 0], [0, 1], [1, 0], [1, 1]])
                self.assertEqual(result["bits"], [1, 1, 1, 0])
                self.assertFalse(result["probe_schema_verified"])
        self.assertEqual(core.entropy_v2([0, 0, 1, 1], ["a", "a", "b", "b"]), (1, 1))
        self.assertEqual(core.entropy_v2([0, 1, 0, 1], ["a", "a", "b", "b"]), (1, 0))

    def test_prescribed_collision_groups_and_route_label_multiplicity(self):
        for old, distractor, goal in product((0, 1), repeat=3):
            cells = [cell for cell in self.cells if cell.old == old and cell.distractor == distractor]
            self.assertEqual(core.structural_projection(cells[0], goal, "OLD_ONLY"), core.structural_projection(cells[1], goal, "OLD_ONLY"))
            self.assertNotEqual(core.oracle_route_v1(cells[0], goal), core.oracle_route_v1(cells[1], goal))
        for relevant, distractor, goal in product((0, 1), repeat=3):
            cells = [cell for cell in self.cells if cell.relevant == relevant and cell.distractor == distractor]
            self.assertEqual(core.structural_projection(cells[0], goal, "NEW_ONLY"), core.structural_projection(cells[1], goal, "NEW_ONLY"))
            self.assertNotEqual(core.oracle_route_v1(cells[0], goal), core.oracle_route_v1(cells[1], goal))
        for goal in (0, 1):
            self.assertEqual(len({core.digest(core.task_fields(cell, goal)) for cell in self.cells}), 1)
            self.assertEqual(len({core.oracle_route_v1(cell, goal) for cell in self.cells}), 4)

    def test_all_registered_structural_shortcuts_have_support_and_no_decoder(self):
        for name in ("two_slot_fixture", "four_root_fixture"):
            report = self.certificate[name]
            self.assertEqual(len(report["structural_shortcuts"]), 36)
            for projection in report["structural_shortcuts"]:
                self.assertEqual(projection["coverage"], report["delayed_tasks"])
                self.assertGreaterEqual(projection["minimum_support"], 2)
                self.assertGreaterEqual(projection["minimum_labels"], 2)
                self.assertEqual((projection["deterministic_keys"], projection["decoded_occurrences"]), (0, 0))
                ceiling = projection["bayes_best_exact_route"]
                self.assertLessEqual(ceiling["numerator"] * 2, ceiling["denominator"])

    def test_shortcut_audit_exposes_singletons_and_perfect_label_leak(self):
        records = [dict(features=dict(leak=str(index)), label=str(index)) for index in range(8)]
        report = core.shortcut_report(records, ("leak",))
        self.assertEqual((report["minimum_support"], report["minimum_labels"]), (1, 1))
        self.assertEqual((report["deterministic_keys"], report["decoded_occurrences"]), (8, 8))
        self.assertEqual(report["bayes_best_exact_route"], dict(numerator=8, denominator=8))

    def test_bad_topology_and_oracle_disagreement_fail_closed(self):
        altered = replace(self.cells[0], edges=self.cells[0].edges[:-1])
        with self.assertRaisesRegex(ValueError, "topology"):
            core.oracle_routes_v2(altered, 0)
        with patch.object(core, "oracle_routes_v2", return_value=()):
            with self.assertRaisesRegex(ValueError, "oracle disagreement"):
                core.audit_structural_fixtures((self.root,))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            core.audit_structural_fixtures((self.root, self.root))

    def test_controlling_document_drift_stops_certificate(self):
        with patch.object(Path, "read_bytes", return_value=b"altered controlling design"):
            with self.assertRaisesRegex(ValueError, "document pin"):
                core.construct_gate()

    def test_no_model_runtime_compiler_or_training_imports(self):
        tree = ast.parse(Path(core.__file__).read_text())
        imported = {node.module.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module}
        imported.update(alias.name.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names)
        self.assertFalse(imported & {"torch", "transformers", "vllm", "subprocess", "socket", "requests"})
        definitions = {node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
        self.assertFalse(definitions & {"compile", "train", "fit", "parse_event_line", "parse_link_line"})


if __name__ == "__main__":
    unittest.main()
