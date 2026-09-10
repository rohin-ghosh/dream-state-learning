from __future__ import annotations

import unittest

from rml_d0.targets import make_target, recall_goldens, transition_law_goldens
from rml_d0.world import action_universe, initial_state, resolve_public_action, step_public


class WorldTransitionTests(unittest.TestCase):
    def test_closed_law_and_recall(self) -> None:
        golden = transition_law_goldens()
        self.assertEqual(golden["action_universe_cardinality"], 23)
        self.assertIn("move_current_illegal", golden["cases"])
        self.assertIn("post_terminal_illegal_zero", golden["cases"])
        self.assertEqual(len(recall_goldens()), 2)

    def test_public_handle_roundtrip_and_malformed_failure(self) -> None:
        spec = make_target(0, 0)
        for action in action_universe(spec):
            record = action.public_record(spec.handles)
            self.assertNotIn("item_index", str(record))
            self.assertEqual(resolve_public_action(spec, record), action)
        start = initial_state(spec)
        malformed = {
            "action_kind": "OBSERVE",
            "arguments": {"object_or_site": "MF000000000000"},
        }
        result = step_public(spec, start, malformed)
        self.assertEqual(result.result_code, "ILLEGAL")
        self.assertEqual(result.state.coolant, start.coolant)
        self.assertEqual(result.state.statuses, start.statuses)


if __name__ == "__main__":
    unittest.main()
