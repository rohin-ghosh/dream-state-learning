"""Complete synthetic source coverage, not route-rendering or science approval."""

from dataclasses import FrozenInstanceError, replace
import unittest

from organism_v6 import composition_birth_stage2a_route_inputs as routes
from organism_v6 import composition_birth_stage2a_source_inputs as source_inputs
from tests.test_composition_birth_stage2a_future_inputs import arguments


class RouteInputTests(unittest.TestCase):
    def test_complete_registered_rows_all_worlds_and_members(self):
        for number in range(32):
            for member in range(2):
                with self.subTest(number=number, member=member):
                    supplied = arguments(number, member)
                    result = routes.derive_birth_route_inputs(**supplied)
                    construction = supplied["case"].construction
                    expected = {row.port: (request, position, row)
                                for request, block in construction.blocks.items() if block.kind == "EVENTS"
                                for position, row in enumerate(block.rows)}
                    self.assertEqual(set(result.transitions), set(expected))
                    self.assertEqual(len(result.transitions), len(construction.world_edges))
                    for port, (request, position, row) in expected.items():
                        edge = result.transitions[port]
                        self.assertEqual((edge.event, edge.current, edge.goal, edge.predicted),
                                         (row.event, row.node, row.goal, row.got))
                        self.assertEqual(edge.actual, construction.world_edges[row.node, port])
                        self.assertEqual(edge.query, request.removeprefix("READ RELATION "))
                        self.assertEqual(edge.source_path[-3:], (request, "rows", str(position)))
                    self.assertFalse(result.inventory_completeness_verified)
                    self.assertFalse(result.rendering_coverage_verified)
                    self.assertFalse(any(result.science_gates.values()))

    def test_successors_use_effective_outcomes_and_recovery_ownership(self):
        result = routes.derive_birth_route_inputs(**arguments(1))
        mismatches = [edge for edge in result.transitions.values() if edge.mismatches]
        self.assertEqual(len(mismatches), 2)
        for previous in mismatches:
            successors = result.successors(previous.port)
            self.assertTrue(successors)
            for port in successors:
                following = result.transitions[port]
                self.assertEqual(following.current, previous.actual)
                self.assertNotEqual(following.current, previous.predicted)
                self.assertEqual(following.query, previous.recover)
                self.assertEqual(following.recovery_owner_port, previous.port)
                self.assertTrue(result.contains_pair(previous.port, port))
            other = next(edge for edge in mismatches if edge.port != previous.port)
            self.assertTrue(set(successors).isdisjoint(result.successors(other.port)))

    def test_exact_off_oracle_recovery_successors_for_both_relation_members(self):
        for member in range(2):
            result = routes.derive_birth_route_inputs(**arguments(25, member))
            construction = result.source.case.construction
            mismatches = [edge for edge in result.transitions.values() if edge.mismatches]
            self.assertEqual(len(mismatches), 2)
            for previous in mismatches:
                recovery = construction.blocks["READ RELATION " + previous.recover]
                expected = {row.port for row in recovery.rows if row.node == previous.actual}
                self.assertEqual(set(result.successors(previous.port)), expected)
                self.assertTrue(expected)

    def test_off_oracle_branches_cycles_and_unregistered_recovery_are_preserved(self):
        result = routes.derive_birth_route_inputs(**arguments(4))
        oracle_ports = {turn.action.removeprefix("STEP ") for turn in result.source.case.trace
                        if turn.action.startswith("STEP ")}
        self.assertGreater(len(result.transitions), len(oracle_ports))
        owners = {token: role for role, token in result.source.role_tokens.items()}
        seen, port = set(), next(port for port, edge in result.transitions.items()
                                if result.successors(port) and port not in oracle_ports
                                and "/x" in owners[edge.current])
        while port not in seen:
            seen.add(port)
            successors = result.successors(port)
            self.assertTrue(successors)
            port = successors[0]
        self.assertGreater(len(seen), 1)
        self.assertTrue(result.unavailable_recover_queries)
        self.assertTrue(result.unavailable_recover_queries.isdisjoint(result.ports_by_query))
        self.assertTrue(all(edge.recovery_owner_port is None for edge in result.transitions.values()))

    def test_immutable_and_rejects_unknown_ports(self):
        result = routes.derive_birth_route_inputs(**arguments())
        port = next(iter(result.transitions))
        with self.assertRaises(TypeError):
            result.transitions[port] = result.transitions[port]
        with self.assertRaises(FrozenInstanceError):
            result.transitions[port].actual = "altered"
        with self.assertRaises(routes.RouteInputError):
            result.successors("missing")
        with self.assertRaises(routes.RouteInputError):
            result.contains_pair(port, "missing")

    def test_off_trace_corruption_is_not_certified(self):
        supplied = arguments()
        construction = supplied["case"].construction
        world_edges = dict(construction.world_edges)
        world_edges.pop(next(reversed(world_edges)))
        supplied["case"] = replace(supplied["case"], construction=replace(construction, world_edges=world_edges))
        with self.assertRaises(source_inputs.SourceInputError):
            routes.derive_birth_route_inputs(**supplied)


if __name__ == "__main__":
    unittest.main()
