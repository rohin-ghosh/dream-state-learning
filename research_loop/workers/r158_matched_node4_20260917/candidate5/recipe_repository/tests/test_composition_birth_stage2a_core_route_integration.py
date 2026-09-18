"""Partial private-core/route/scanner integration; not a complete inventory."""

import unittest

from organism_v6 import composition_birth_stage2a_core_inputs as cores
from organism_v6 import composition_birth_stage2a_route_scan as routes
from organism_v6 import composition_birth_stage2a_scanner as scanner
from organism_v6.composition_birth_stage2a_primitives import canonical_json
from tests.test_composition_birth_stage2a_future_inputs import arguments


class CoreRouteIntegrationTests(unittest.TestCase):
    def test_full_constructor_snapshot_core_and_route_scanner_agree(self):
        for number, member, ordinal, arm in ((0, 0, 0, "CLOSED"), (1, 1, 3, "ATOM_LOCAL")):
            with self.subTest(number=number, member=member, ordinal=ordinal, arm=arm):
                supplied = arguments(number, member, ordinal, arm)
                route_report = routes.scan_birth_route_language(**supplied)
                validated = route_report.source.source
                core = cores.build_birth_core_inputs(case=validated.case, record=validated.record,
                                                      role_tokens=validated.role_tokens)
                binding = route_report.binding
                report = scanner.scan_forward_targets(
                    binding.projection_bytes, target=binding.target, phase=binding.phase,
                    decision_index=binding.decision_index, semantic_bytes=canonical_json({"core": core.core}),
                    future_identifiers=(), registered_routes=(), fields=binding.fields,
                    task_start=binding.task_start, task_goal=binding.task_goal, current=binding.current,
                    implicated_query=binding.implicated_query, implicated_event=binding.implicated_event,
                    observed_contradiction=binding.observed_contradiction,
                )
                self.assertTrue(route_report.registered_grammar_clear)
                self.assertTrue(report.passed)
                self.assertTrue(any(hit.value == b"STATE" for hit in report.receipts))
                self.assertFalse(route_report.inventory_completeness_verified)
                self.assertFalse(any(core.science_gates.values()))

    def test_protocol_alias_receipts_do_not_waive_scheduled_action(self):
        supplied = arguments()
        route_report = routes.scan_birth_route_language(**supplied)
        binding = route_report.binding
        report = scanner.scan_forward_targets(
            binding.projection_bytes + b"\n" + binding.target,
            target=binding.target, phase=binding.phase, decision_index=binding.decision_index,
            semantic_bytes=canonical_json({"core": {"type_labels": ["PORT", "STATE"]}}),
            fields=binding.fields, task_start=binding.task_start, task_goal=binding.task_goal,
            current=binding.current,
        )
        self.assertFalse(report.passed)
        self.assertTrue(any(hit.category == "full_target" for hit in report.issues))


if __name__ == "__main__":
    unittest.main()
