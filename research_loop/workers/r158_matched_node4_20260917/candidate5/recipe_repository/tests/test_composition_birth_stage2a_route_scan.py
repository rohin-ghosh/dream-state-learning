"""Route-language mutation checks, separate from the unchanged leak scanner."""

import unittest
from unittest.mock import patch

from organism_v6 import composition_birth_stage2a_route_scan as routes
from organism_v6 import composition_birth_stage2a_route_inputs as inputs
from organism_v6 import composition_birth_stage2a_scanner as scanner
from tests.test_composition_birth_stage2a_future_inputs import arguments


class RouteScanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.arguments = arguments(5, ordinal=3)
        cls.original = routes.scan_birth_route_language(**cls.arguments)
        cls.index = cls.original.source
        facts = cls.index.source.case.facts
        cls.first = next(edge for edge in cls.index.transitions.values() if edge.event == facts.failed_event)
        cls.second = next(edge for edge in cls.index.transitions.values() if edge.event == facts.selected_event)

    def scan(self, suffix):
        return routes.scan_birth_route_language(**self.arguments,
            candidate_prefix=self.original.binding.projection_bytes + b"\n" + suffix)

    def test_authentic_history_not_a_route_failure(self):
        self.assertTrue(self.original.registered_grammar_clear)
        self.assertTrue(self.original.occurrences)
        self.assertTrue(all(item.authenticated for item in self.original.occurrences))
        self.assertFalse(self.original.inventory_completeness_verified)
        self.assertFalse(any(self.original.science_gates.values()))

    def test_all_birth_prefixes_keep_occurrence_local_authentication(self):
        for number in range(32):
            for member in range(2):
                for ordinal in range(4):
                    for arm in ("CLOSED", "ATOM_LOCAL"):
                        with self.subTest(number=number, member=member, ordinal=ordinal, arm=arm):
                            result = routes.scan_birth_route_language(**arguments(number, member, ordinal, arm))
                            self.assertTrue(result.registered_grammar_clear)

    def test_action_route_through_typed_world_and_read_separators(self):
        suffix = (f"STEP {self.first.port}\nWORLD\nCURRENT {self.first.actual}\n"
                  f"THINK REVISE {self.first.event}\nACK\nREAD RELATION {self.first.recover}\n"
                  f"STEP {self.second.port}").encode("ascii")
        result = self.scan(suffix)
        self.assertTrue(any(item.grammar == "actions" and not item.authenticated for item in result.issues))
        result = self.scan(suffix.lower().replace(b" ", b"\t\t"))
        self.assertTrue(result.issues)
        result = self.scan(suffix.translate(None, b"_- <>"))
        self.assertTrue(result.issues)

    def test_both_service_skins_and_copied_occurrence(self):
        from organism_v6 import composition_birth_stage2a_worlds as worlds
        construction = self.index.source.case.construction
        blocks = [construction.blocks["READ RELATION " + edge.query] for edge in (self.first, self.second)]
        for skin in (0, 1):
            suffix = "\n".join("SERVICE\n" + worlds.render_service(block.kind, block.rows, skin=skin)
                               for block in blocks).encode("ascii")
            result = self.scan(suffix)
            self.assertTrue(any(item.grammar == "event_rows" for item in result.issues))
        copied = self.original.binding.projection_bytes
        result = self.scan(copied)
        self.assertTrue(result.issues)

    def test_ordered_port_event_query_formats(self):
        for field in ("port", "event", "query"):
            for separator in (" ", " -> ", ", "):
                suffix = separator.join((getattr(self.first, field), getattr(self.second, field))).encode("ascii")
                result = self.scan(suffix)
                self.assertTrue(any(item.grammar == "ordered_ids" for item in result.issues), (field, separator))

    def test_changed_causal_world_does_not_inherit_endpoint_authentication(self):
        original_world = ("WORLD\nCURRENT " + self.first.actual).encode("ascii")
        changed_world = ("WORLD\nCURRENT " + self.first.predicted).encode("ascii")
        original = self.original.binding.projection_bytes
        self.assertIn(original_world, original)
        candidate = original.replace(original_world, changed_world, 1)
        result = routes.scan_birth_route_language(**self.arguments, candidate_prefix=candidate)
        self.assertTrue(any(item.grammar == "actions" for item in result.issues))

    def test_mixed_action_and_event_row_route_disclosure(self):
        construction = self.index.source.case.construction
        second_block = construction.blocks["READ RELATION " + self.second.query]
        second_line = next(line for line in second_block.raw.split("\n") if self.second.port in line)
        result = self.scan((f"STEP {self.first.port}\n" + second_line).encode("ascii"))
        self.assertTrue(any(item.grammar == "mixed" for item in result.issues))
        first_block = construction.blocks["READ RELATION " + self.first.query]
        first_line = next(line for line in first_block.raw.split("\n") if self.first.port in line)
        result = self.scan((first_line + f"\nSTEP {self.second.port}").encode("ascii"))
        self.assertTrue(any(item.grammar == "mixed" for item in result.issues))

    def test_disconnected_ids_and_arbitrary_prose_do_not_form_route(self):
        disconnected = next(edge for edge in self.index.transitions.values()
                            if not self.index.contains_pair(self.first.port, edge.port))
        result = self.scan(f"{self.first.port} -> {disconnected.port}".encode("ascii"))
        self.assertFalse(result.issues)
        result = self.scan(f"STEP {self.first.port}\narbitrary commentary\nSTEP {self.second.port}".encode("ascii"))
        self.assertFalse(result.issues)
        self.assertTrue(result.unrecognized_line_spans)

    def test_atom_does_not_inherit_closed_occurrence_exemptions(self):
        atom_arguments = dict(self.arguments, record=arguments(5, ordinal=3, arm="ATOM_LOCAL")["record"])
        atom = routes.scan_birth_route_language(**atom_arguments)
        self.assertFalse(atom.occurrences)
        result = routes.scan_birth_route_language(**atom_arguments,
            candidate_prefix=atom.binding.projection_bytes + b"\n" + self.original.binding.projection_bytes)
        self.assertTrue(result.issues)

    def test_overflow_and_invalid_wire_fail_closed(self):
        suffix = f"{self.first.port} -> {self.second.port}".encode("ascii")
        with patch.object(scanner, "BOUNDS", dict(scanner.BOUNDS, hits=0)):
            with self.assertRaises(inputs.RouteInputError):
                self.scan(suffix)
        for suffix in (b"\0", b"\r", "invalid-é".encode("utf8")):
            with self.assertRaises(ValueError):
                self.scan(suffix)


if __name__ == "__main__":
    unittest.main()
