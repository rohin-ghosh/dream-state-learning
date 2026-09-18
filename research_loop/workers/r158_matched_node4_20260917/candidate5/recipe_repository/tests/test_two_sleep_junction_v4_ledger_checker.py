"""Independent symbolic validation regression tests; no science execution."""

import ast
from copy import deepcopy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from organism_v6 import two_sleep_junction_v4_ledger as source
from organism_v6 import two_sleep_junction_v4_ledger_checker as checker


class IndependentLedgerCheckerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = source.build_ledger()

    def setUp(self):
        self.ledger = deepcopy(self.fixture)

    def phase(self, name):
        return next(phase for phase in self.ledger["phases"] if phase["phase"] == name)

    def reject(self, value=None):
        with self.assertRaises(checker.LedgerCheckError):
            checker.check_ledger(self.ledger if value is None else value)

    def test_object_and_json_success_do_not_authorize_or_mutate(self):
        before = deepcopy(self.ledger)
        result = checker.check_ledger(self.ledger)
        self.assertEqual(result, checker.validate_ledger(json.dumps(self.ledger)))
        self.assertEqual(self.ledger, before)
        self.assertEqual(result["status"], "PARTIAL_LEDGER_CHECK_ONLY")
        self.assertTrue(all(value is False for value in result["gates"].values()))
        self.assertFalse(result["empirical_feasibility_claim"])
        self.assertFalse(result["predicates_evaluated"])
        self.assertEqual(len(result["unimplemented_coverage"]), 6)
        result["gates"]["GO_GPU"] = True
        self.assertFalse(checker.check_ledger(self.ledger)["gates"]["GO_GPU"])

    def test_independence_from_primary_and_other_runtime_helpers(self):
        tree = ast.parse(Path(checker.__file__).read_text())
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module)
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                self.assertNotIn(node.func.id, {"__import__", "eval", "exec", "compile"})
        self.assertEqual(set(imports), {"__future__", "hashlib", "json", "pathlib", "re"})
        with patch.object(source, "build_ledger", side_effect=AssertionError("generator used")), \
             patch.object(source, "canonical_phases", side_effect=AssertionError("roster used")), \
             patch.object(source, "validate_ledger", side_effect=AssertionError("validator used")), \
             patch.object(source, "derive_resources", side_effect=AssertionError("arithmetic used")), \
             patch.object(source, "canonical_json", side_effect=AssertionError("renderer used")):
            self.assertEqual(checker.check_ledger(self.ledger)["status"], checker.CHECK_STATUS)

    def test_local_contract_unavailable_or_modified_fails_closed(self):
        original = Path.read_bytes

        def modified(path):
            return original(path) + b"\n"

        with patch.object(Path, "read_bytes", modified):
            self.reject()
        with patch.object(Path, "read_bytes", side_effect=OSError("missing source")):
            self.reject()

    def test_duplicate_json_keys_at_any_depth_even_identical(self):
        encoded = json.dumps(self.ledger)
        cases = (
            '{"source_status":"PARTIAL_SOURCE_ONLY",' + encoded[1:],
            encoded.replace('"GO_GPU": false', '"GO_GPU": false, "GO_GPU": false', 1),
            encoded.replace('"calls": 1', '"calls": 1, "calls": 1', 1),
            encoded.replace('"calls": 1', '"calls": 1, "call\\u0073": 1', 1),
        )
        for value in cases:
            with self.subTest(value=value[:90]):
                with self.assertRaisesRegex(checker.LedgerCheckError, "duplicate key"):
                    checker.check_ledger(value)

    def test_non_json_malformed_nonfinite_and_cyclic_inputs(self):
        for value in ([], 1, True, b"{}", "null", "[]", "{", "{} trailing",
                      '{"bad":NaN}', '{"bad":Infinity}', '{"bad":-Infinity}',
                      {"bad": float("nan")}, {"bad": object()}, {1: "bad"},
                      {"bad": ()}, "[" * 1000 + "]" * 1000):
            with self.subTest(value=repr(value)[:90]):
                self.reject(value)
        cyclic = {}
        cyclic["self"] = cyclic
        self.reject(cyclic)
        nested = {}
        for _ in range(66):
            nested = {"child": nested}
        self.reject(nested)

    def test_phase_omission_duplication_reordering_and_unknown(self):
        for index in range(len(self.fixture["phases"])):
            for action in ("omit", "duplicate", "replace", "swap"):
                self.ledger = deepcopy(self.fixture)
                phases = self.ledger["phases"]
                with self.subTest(index=index, action=action):
                    if action == "omit":
                        phases.pop(index)
                    elif action == "duplicate":
                        phases.insert(index, deepcopy(phases[index]))
                    elif action == "replace":
                        phases[index]["phase"] = "UNKNOWN"
                    else:
                        other = (index + 1) % len(phases)
                        phases[index], phases[other] = phases[other], phases[index]
                    self.reject()

    def test_each_condition_row_is_ordered_unique_and_required(self):
        for phase_index, phase in enumerate(self.fixture["phases"]):
            for row_index in range(len(phase["rows"])):
                for action in ("omit", "duplicate", "replace", "swap"):
                    self.ledger = deepcopy(self.fixture)
                    rows = self.ledger["phases"][phase_index]["rows"]
                    if action == "swap" and len(rows) == 1:
                        continue
                    with self.subTest(phase=phase["phase"], row=row_index, action=action):
                        if action == "omit":
                            rows.pop(row_index)
                        elif action == "duplicate":
                            rows.insert(row_index, deepcopy(rows[row_index]))
                        elif action == "replace":
                            rows[row_index] = {"kind": "UNKNOWN"}
                        else:
                            other = (row_index + 1) % len(rows)
                            rows[row_index], rows[other] = rows[other], rows[row_index]
                        self.reject()

    def test_atom_is_a_root_local_gate_in_all_four_panels(self):
        for phase_name, condition in (("P10", "ATOM_TEXT"), ("P30", "ATOM"),
                                      ("P50", "ATOM_TEXT"), ("P70", "ATOM")):
            for key, changed in (("role", "diagnostic"), ("expected", "success <=2/2"),
                                 ("predicate_scope", "pair_pooled")):
                self.ledger = deepcopy(self.fixture)
                row = next(row for row in self.phase(phase_name)["rows"] if row["condition"] == condition)
                row[key] = changed
                with self.subTest(phase=phase_name, field=key):
                    self.reject()

    def test_p05_is_single_zero_call_import_not_execution(self):
        for key, value in (("budgets", [{"category": "preservation", "calls": 1, "generated_tokens": 256}]),
                           ("receipt_import_implemented", True), ("kind", "formation"),
                           ("chain_ordinals", list(range(8))), ("canary_ordinals", list(range(15)))):
            self.ledger = deepcopy(self.fixture)
            self.phase("P05_IMPORT_CONTROLLER_BASELINE")["rows"][0][key] = value
            with self.subTest(field=key):
                self.reject()

    def test_fixed_metrics_and_birth_drop_cannot_be_modified(self):
        for phase_name in ("P05_IMPORT_CONTROLLER_BASELINE", "P31", "P71"):
            for metric_index in range(9):
                for key, value in (("denominator", 100), ("absolute_minimum", 0),
                                   ("birth_maximum_count_drop", 2), ("scope", "pooled"),
                                   ("count_rule", "rounded ratio"), ("role", "diagnostic")):
                    self.ledger = deepcopy(self.fixture)
                    phase = self.phase(phase_name)
                    metrics = phase["rows"][0]["metrics"] if phase_name.startswith("P05") else phase["metrics"]
                    metrics[metric_index][key] = value
                    with self.subTest(phase=phase_name, metric=metric_index, field=key):
                        self.reject()

    def test_aliases_and_empty_policy_cannot_consume_or_redirect_calls(self):
        for phase_name in ("P31", "P71"):
            for index in range(32, 56):
                self.ledger = deepcopy(self.fixture)
                row = self.phase(phase_name)["rows"][index]
                row["budgets"][0]["calls"] += 1
                with self.subTest(phase=phase_name, index=index):
                    self.reject()
            changes = (("empty_slot_calls", 1), ("empty_slot_tokens", 256),
                       ("unused_tail_state", "EXECUTED"), ("reservation_state", "EMPTY"),
                       ("token_cap_scope", "each_reserved_slot"))
            for key, value in changes:
                self.ledger = deepcopy(self.fixture)
                self.phase(phase_name)["rows"][32][key] = value
                with self.subTest(phase=phase_name, field=key):
                    self.reject()
            for key, value in (("phase", "P00"), ("fit", "ATOM"), ("world", "other_world"),
                               ("query_ordinal", 1), ("canary_ordinal", 16)):
                self.ledger = deepcopy(self.fixture)
                self.phase(phase_name)["rows"][40]["target"][key] = value
                with self.subTest(phase=phase_name, target=key):
                    self.reject()
            self.ledger = deepcopy(self.fixture)
            self.phase(phase_name)["rows"][40]["identical_raw_hashes_required"] = False
            self.reject()

    def test_each_budget_category_call_and_token_is_checked(self):
        for phase_index, phase in enumerate(self.fixture["phases"]):
            for row_index, row in enumerate(phase["rows"]):
                paths = [("budgets", index) for index in range(len(row["budgets"]))]
                for cold_index, cold in enumerate(row.get("cold_immediately_after_fit", [])):
                    paths.extend(("cold_immediately_after_fit", cold_index, "budgets", index)
                                 for index in range(len(cold["budgets"])))
                for path in paths:
                    for key in ("category", "calls", "generated_tokens"):
                        self.ledger = deepcopy(self.fixture)
                        budget = self.ledger["phases"][phase_index]["rows"][row_index]
                        for part in path:
                            budget = budget[part]
                        budget[key] = "wrong_category" if key == "category" else budget[key] + 1
                        with self.subTest(phase=phase["phase"], row=row_index, path=path, field=key):
                            self.reject()

    def test_budget_redistribution_with_unchanged_totals_is_rejected(self):
        rows = self.phase("P10")["rows"]
        rows[0]["budgets"][0]["calls"] -= 1
        rows[1]["budgets"][0]["calls"] += 1
        self.reject()
        self.ledger = deepcopy(self.fixture)
        rows = self.phase("P31")["rows"]
        rows[0]["budgets"][0]["calls"] -= 1
        rows[40]["budgets"][0]["calls"] += 1
        self.reject()

    def test_wrong_native_reader_and_deterministic_service_budgets(self):
        for phase_name, row_index in (("P10", 0), ("P30", 7), ("P50", 6), ("P70", 7)):
            self.ledger = deepcopy(self.fixture)
            self.phase(phase_name)["rows"][row_index]["budgets"].append(
                {"category": "native_reader", "calls": 20, "generated_tokens": 3200})
            self.reject()
        self.ledger = deepcopy(self.fixture)
        self.phase("P30")["rows"][0]["budgets"].pop()
        self.reject()

    def test_exact_contract_arithmetic_independent_of_generator_totals(self):
        result = checker.check_ledger(self.ledger)
        world = result["per_world"]
        self.assertEqual((world["route_rollouts"], world["native_reader_rollouts"], world["fits"]), (68, 34, 13))
        for phase, routes, readers, calls, tokens, fits in (
            ("P00", 0, 0, 20, 2176, 0),
            ("P05_IMPORT_CONTROLLER_BASELINE", 0, 0, 0, 0, 0),
            ("P10", 12, 0, 264, 49152, 0),
            ("P20", 0, 0, 420, 77952, 7),
            ("P30", 18, 16, 556, 99328, 0),
            ("P31", 0, 0, 264, 40960, 0),
            ("P40", 0, 0, 6, 704, 0),
            ("P50", 16, 0, 352, 65536, 0),
            ("P60", 0, 0, 420, 76416, 6),
            ("P70", 22, 18, 664, 118912, 0),
            ("P71", 0, 0, 264, 40960, 0),
        ):
            actual = result["by_phase_per_world"][phase]
            self.assertEqual([actual[key] for key in ("route_rollouts", "native_reader_rollouts", "model_calls", "generated_tokens", "fits")],
                             [routes, readers, calls, tokens, fits])
        self.assertEqual(world["categories"], {
            "actor": {"calls": 68 * 22, "generated_tokens": 68 * 4096},
            "native_reader": {"calls": 34 * 10, "generated_tokens": 34 * 10 * 160},
            "cold_canary": {"calls": 7 * 60 + 6 * 70, "generated_tokens": 154368},
            "formation": {"calls": 26, "generated_tokens": 2880},
            "preservation": {"calls": 2 * (32 + 8 * 29), "generated_tokens": 2 * (32 * 256 + 8 * 4096)},
        })
        self.assertEqual((world["model_calls"], world["generated_tokens"]), (3230, 572096))
        self.assertEqual((result["pair"]["model_calls"], result["pair"]["generated_tokens"], result["pair"]["fits"]),
                         (6460, 1144192, 26))

    def test_every_resource_scalar_is_checked_including_training_and_limits(self):
        def leaves(value, path=()):
            if type(value) is dict:
                for key, child in value.items():
                    yield from leaves(child, (*path, key))
            else:
                yield path, value

        for path, value in leaves(self.fixture["resources"]):
            self.ledger = deepcopy(self.fixture)
            parent = self.ledger["resources"]
            for part in path[:-1]:
                parent = parent[part]
            if type(value) is bool:
                changed = not value
            elif type(value) is int:
                changed = value + 1
            elif value is None:
                changed = 1
            else:
                changed = "modified"
            parent[path[-1]] = changed
            with self.subTest(path=path):
                self.reject()

    def test_bool_and_float_never_substitute_for_counts(self):
        for changed in (True, 1.0, "1", -1, None):
            self.ledger = deepcopy(self.fixture)
            self.phase("P00")["rows"][0]["ordinal"] = changed
            self.reject()
        for changed in (False, 0.0):
            self.ledger = deepcopy(self.fixture)
            self.phase("P10")["rows"][0]["goals"][0] = changed
            self.reject()

    def test_all_science_gates_and_unknown_go_fields_rejected(self):
        for gate in self.fixture["gates"]:
            for value in (True, 0, None):
                self.ledger = deepcopy(self.fixture)
                self.ledger["gates"][gate] = value
                with self.subTest(gate=gate, value=value):
                    self.reject()
        for scope in ("root", "gates", "phase", "row"):
            self.ledger = deepcopy(self.fixture)
            target = {"root": self.ledger, "gates": self.ledger["gates"],
                      "phase": self.phase("P10"), "row": self.phase("P10")["rows"][0]}[scope]
            target["GO_CPU_SOURCE"] = True
            self.reject()

    def test_every_roster_field_rejects_missing_or_extra_and_bad_type(self):
        for phase_index, phase in enumerate(self.fixture["phases"]):
            for row_index, row in enumerate(phase["rows"]):
                for key in row:
                    self.ledger = deepcopy(self.fixture)
                    del self.ledger["phases"][phase_index]["rows"][row_index][key]
                    with self.subTest(phase=phase["phase"], row=row_index, missing=key):
                        self.reject()
        for value in (None, [], "bad", 1):
            for path in (("phases",), ("phases", 0), ("phases", 0, "rows"),
                         ("phases", 0, "rows", 0), ("resources",),
                         ("resources", "training")):
                self.ledger = deepcopy(self.fixture)
                parent = self.ledger
                for part in path[:-1]:
                    parent = parent[part]
                parent[path[-1]] = value
                self.reject()

    def test_fit_ancestry_training_and_cold_coverage_amendments(self):
        changes = (("actor_mount", "S1 AUTH"), ("memory_units", 12),
                   ("views_per_unit", 7), ("repeats_per_view", 24), ("fits", 2))
        for key, value in changes:
            self.ledger = deepcopy(self.fixture)
            self.phase("P60")["rows"][2][key] = value
            self.reject()
        for phase_name in ("P20", "P60"):
            self.ledger = deepcopy(self.fixture)
            cold = self.phase(phase_name)["rows"][0]["cold_immediately_after_fit"]
            cold[0], cold[1] = cold[1], cold[0]
            self.reject()
            self.ledger = deepcopy(self.fixture)
            cold = self.phase(phase_name)["rows"][0]["cold_immediately_after_fit"]
            cold[0]["ordinals"][1] = cold[0]["ordinals"][0]
            self.reject()


if __name__ == "__main__":
    unittest.main()
