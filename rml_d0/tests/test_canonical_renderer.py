from __future__ import annotations

import hashlib
import unittest

from rml_d0.canonical import (
    CanonicalError,
    canonical_bytes,
    canonical_goldens,
    parse_record_bytes,
    record_bytes,
    strict_loads,
)
from rml_d0.probes import actual_vector_digests


class CanonicalRendererTests(unittest.TestCase):
    def test_all_independent_oracle_vector_digests(self) -> None:
        expected = {
            "conditioner_table": "316aac145f65bd5d9362e03a6fca1338a662cc0843f43e8fb96badadffd4c944",
            "valve_table": "4d836dd079900c096afdef06d32fc09711f494f5126f0407a5d021793e92d5ac",
            "nw_target_00": "e422c5cc4bdf893308b3e260553e5a665948ba5f34c4ac8294365f861d54ee9a",
            "bridge_table": "f096c7ca5d2f4b8cf614963ec7fe4a997c8d757057c89ca10bf494b6fa3d5b8a",
            "bridge_result": "c9c9d05dda01d0f8bdc7d09b73d4ea99020039d2a135b67c5fba0e4ab554ff64",
            "source_counts": "a5860239f79a5f97b84f82b758e5fa242c9932a0a22d69f441fce68407a6335c",
            "p_atoms": "45e104c62cca1d3ec115ce3e2fc20465e03cca3e6016d7da92dd9d9a668fc917",
            "j_inventory": "8593c0f7b57d01c59f30eb074353f6f988b23594bf6e25618ef0363b20edbb4b",
            "first_accept": "8ba883f19c7c6fee04e42c9bc64488ef9359a65e684c53799a74253fab08d704",
            "quotient_fields": "927ae08326f7341dc37db6a5798b7d8d8224beda8f6ce6b92e571f65457b1aca",
            "recall_goal_high_lean": "61ce382efad86108f7708d506d6ef7d447b26ffb713e64e46b22b9cb0504ec8b",
            "recall_goal_low_rich": "ed4e557cac54ab2cd1a2d08aebb9b95b0dbffbc98f58a3d5e966d2cf66f30f8d",
        }
        self.assertEqual(actual_vector_digests(), expected)

    def test_independent_recall_goal_vectors(self) -> None:
        actual = actual_vector_digests()
        self.assertEqual(
            actual["recall_goal_high_lean"],
            "61ce382efad86108f7708d506d6ef7d447b26ffb713e64e46b22b9cb0504ec8b",
        )
        self.assertEqual(
            actual["recall_goal_low_rich"],
            "ed4e557cac54ab2cd1a2d08aebb9b95b0dbffbc98f58a3d5e966d2cf66f30f8d",
        )
        for row in canonical_goldens():
            payload = bytes.fromhex(row["bytes_hex"])
            self.assertTrue(payload.endswith(b"\n"))
            self.assertEqual(hashlib.sha256(payload[:-1]).hexdigest(), row["sha256"])

    def test_raw_negative_cases(self) -> None:
        invalid = (
            lambda: strict_loads(b'{"a":1,"a":2}'),
            lambda: strict_loads(b'{"a":1.5}'),
            lambda: strict_loads(b'{"a":null}'),
            lambda: strict_loads('{"a":"e\u0301"}'),
            lambda: parse_record_bytes("PublicAction", b'{"action_kind":"STOP","arguments":{}}'),
            lambda: parse_record_bytes("PublicAction", b'{"action_kind":"STOP","arguments":{}}\n\n'),
        )
        for function in invalid:
            with self.assertRaises(CanonicalError):
                function()

    def test_jcs_exact_roundtrip(self) -> None:
        record = {"action_kind": "STOP", "arguments": {}}
        payload = record_bytes("PublicAction", record)
        self.assertEqual(parse_record_bytes("PublicAction", payload), record)
        self.assertEqual(payload, canonical_bytes(record) + b"\n")


if __name__ == "__main__":
    unittest.main()
