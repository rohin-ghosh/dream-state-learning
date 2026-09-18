import unittest

from gpu.astra_stage2a_terminal_summary import CRITERIA, inert_value, validate_criteria


class TerminalSummaryTests(unittest.TestCase):
    def rows(self):
        return [{"name": name, "count": minimum, "denominator": denominator, "minimum": minimum}
                for name, (denominator, minimum) in CRITERIA.items()]

    def test_complete_numeric_miss_remains_valid_data(self):
        rows = self.rows()
        rows[0]["count"] = 0
        self.assertEqual(validate_criteria(rows)["SEEK"], 0)

    def test_empty_or_missing_criteria_cannot_pass_vacuously(self):
        for rows in ([], self.rows()[:-1]):
            with self.assertRaisesRegex(ValueError, "exact_ten"):
                validate_criteria(rows)

    def test_duplicate_contract_and_type_changes_rejected(self):
        for field, value in (("name", "CONTINUE"), ("minimum", 1), ("denominator", 32), ("count", True)):
            rows = self.rows()
            rows[0][field] = value
            with self.assertRaises(ValueError):
                validate_criteria(rows)

    def test_gain_must_imply_valid_baseline(self):
        rows = self.rows()
        rows[-1]["count"] = -8
        with self.assertRaisesRegex(ValueError, "baseline_chain"):
            validate_criteria(rows)

    def test_inert_decoder_never_imports_types(self):
        self.assertEqual(inert_value({"list": [{"mapping": [["loss", 1.0]]}]}), [{"loss": 1.0}])
        with self.assertRaises(ValueError):
            inert_value({"dataclass": "arbitrary.module"})
        with self.assertRaises(ValueError):
            inert_value({"mapping": [["key", 1], ["key", 2]]})


if __name__ == "__main__":
    unittest.main()
