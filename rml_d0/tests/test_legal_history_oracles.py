from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from rml_d0.canonical import canonical_bytes
from rml_d0.isolation import evaluation_isolation_golden
from rml_d0.planner import QUOTIENT_FIELDS, compare_literal_and_quotient
from rml_d0.probes import mutation_kills
from rml_d0.targets import make_target


class LegalHistoryOracleTests(unittest.TestCase):
    def test_fixed_quotient_vector_and_representative_bisimulation(self) -> None:
        self.assertEqual(
            hashlib.sha256(canonical_bytes(list(QUOTIENT_FIELDS))).hexdigest(),
            "927ae08326f7341dc37db6a5798b7d8d8224beda8f6ce6b92e571f65457b1aca",
        )
        for spec in (make_target(0, 0), make_target(0, 0).twin()):
            result = compare_literal_and_quotient(spec, 6)
            self.assertEqual(len(result.depth_summaries), 6)
            self.assertEqual(result.transitions, 27117)

    def test_runner_contains_all_32_literal_vectors(self) -> None:
        report_path = Path(__file__).resolve().parents[1] / "stage_a_report.json"
        if not report_path.is_file():
            self.skipTest("run the Stage-A command before report integration test")
        report = json.loads(report_path.read_text(encoding="utf-8"))
        vectors = report["gate_values"]["literal_history_vectors"]
        self.assertEqual(len(vectors), 32)
        self.assertTrue(all(len(row["depth_summaries"]) == 6 for row in vectors))
        self.assertEqual(report["gate_values"]["fixture_counts"]["literal_target_sides"], 32)

    def test_mutation_kills_and_isolation(self) -> None:
        mutations = mutation_kills()
        self.assertEqual([row["id"] for row in mutations], ["M1", "M2", "M3a", "M3b", "M4", "M5a", "M5b", "M5c", "M6", "M7", "M8", "M9"])
        self.assertTrue(all(row["killed"] for row in mutations))
        isolation = evaluation_isolation_golden()
        self.assertTrue(isolation["run_skip_equal"])
        self.assertTrue(isolation["source_descriptor_unchanged"])
        self.assertTrue(all(isolation["capability_attempts_denied"].values()))


if __name__ == "__main__":
    unittest.main()
