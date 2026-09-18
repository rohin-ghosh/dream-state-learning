"""Synthetic source fixtures, never a material seed/root search or admission.

Optional real CPU solver tests use only Main's supplied pinned environment.
The injected backend tests exercise orchestration/failures, not optimality.
No native model, tokenizer, shared environment modification or remote work.
"""

from copy import deepcopy
from dataclasses import replace
import importlib.util
import inspect
from itertools import combinations, product
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from gpu import astra_pchain2_nulls as source


HAS_SCIPY = importlib.util.find_spec("scipy") is not None and importlib.util.find_spec("numpy") is not None


def fixture(*, source_matches=False, block_lengths=(1, 1)):
    endpoints = tuple(chr(97 + index) for index in range(16))
    sources = tuple("Q" + (endpoint if source_matches else chr(65 + index))
                    for index, endpoint in enumerate(endpoints))
    orders = tuple(endpoints[index // 8 * 8:index // 8 * 8 + 8] for index in range(16))
    lengths = tuple((block_lengths[index // 8],) * 8 for index in range(16))
    return dict(sources=sources, candidate_orders=orders, token_lengths=lengths), endpoints


def binary_vector(assignment):
    return tuple(int(column == endpoint % 8) for endpoint in assignment for column in range(8))


def unicode_fixture():
    first = ("éa", "éb", "êa", "êb", "øa", "øb", "ÿa", "ÿb")
    second = ("Āa", "Āb", "Ăa", "Ăb", "Ąa", "Ąb", "Ća", "Ćb")
    return dict(sources=tuple("é" + chr(65 + index) for index in range(16)),
                candidate_orders=(first,) * 8 + (second,) * 8,
                token_lengths=((2, 2, 3, 3, 1, 1, 2, 2),) * 16)


def optimal_outcome(objective, *, assignment=tuple(range(16))):
    vector = binary_vector(assignment)
    optimum = sum(coefficient * value for coefficient, value in zip(objective, vector))
    return SimpleNamespace(status=0, success=True, x=vector, fun=float(optimum),
                           mip_gap=0.0, mip_dual_bound=float(optimum))


class FakeClock:
    def __init__(self):
        self.value = 0.0

    def __call__(self):
        return self.value


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.inputs, self.endpoints = fixture()
        self.registry = source.build_null_registry(**self.inputs)

    def test_registry_input_visibility_and_deterministic_hashes(self):
        self.assertEqual(tuple(inspect.signature(source.build_null_registry).parameters),
                         ("sources", "candidate_orders", "token_lengths"))
        with self.assertRaises(TypeError):
            source.build_null_registry(**self.inputs, assigned_targets=self.endpoints)
        self.assertEqual(self.registry, source.build_null_registry(**deepcopy(self.inputs)))
        for digest in (self.registry.inputs_sha256, self.registry.membership_sha256, self.registry.registry_sha256):
            self.assertEqual(len(digest), 64)
            int(digest, 16)
        changed = self.inputs | {"sources": tuple("Z" + item for item in self.inputs["sources"])}
        other = source.build_null_registry(**changed)
        self.assertNotEqual(other.inputs_sha256, self.registry.inputs_sha256)
        self.assertNotEqual(other.membership_sha256, self.registry.membership_sha256)
        self.assertNotEqual(other.registry_sha256, self.registry.registry_sha256)

    def test_membership_uses_within_question_variation_not_between_questions(self):
        inputs, _ = fixture(block_lengths=(1, 2))
        registry = source.build_null_registry(**inputs)
        self.assertEqual(registry.nonconstant_features,
                         ("display_position", "lexicographic_rank", "byte_0", "byte_sum_mod_257"))
        self.assertNotIn("tokenizer_length", registry.nonconstant_features)
        names = {policy.name for policy in registry.policies}
        for feature in registry.features:
            self.assertIn(f"single:{feature.name}:min", names)
            self.assertIn(f"single:{feature.name}:max", names)
        self.assertEqual(len(registry.policies), 2 * 9 + 8 + 2 + 4 * 6)
        self.assertEqual(len(registry.policies), len(names))
        self.assertEqual(source.MEMBERSHIP_RULE, "varies_across_candidates_in_at_least_one_question")

    def test_constant_feature_max_ties_choose_smaller_display_position(self):
        policies = {policy.name: policy.positions for policy in self.registry.policies}
        self.assertEqual(policies["single:byte_length:min"], (0,) * 16)
        self.assertEqual(policies["single:byte_length:max"], (0,) * 16)
        for position in range(8):
            self.assertEqual(policies[f"position:{position}"], (position,) * 16)
        self.assertEqual(policies["lex:min"], (0,) * 16)
        self.assertEqual(policies["lex:max"], (7,) * 16)
        self.assertEqual(source._ranks((7, 7, 2, 2, 7, 0, 0, 2)), (5, 6, 2, 3, 7, 0, 1, 4))

    def test_byte_features_are_unsigned_utf8_not_character_features(self):
        registry = source.build_null_registry(**unicode_fixture())
        features = {feature.name: feature.values for feature in registry.features}
        self.assertEqual(features["byte_length"][0], (3,) * 8)
        self.assertEqual(features["byte_0"][0], (195,) * 8)
        self.assertEqual(features["byte_1"][0], (169, 169, 170, 170, 184, 184, 191, 191))
        self.assertEqual(features["byte_2"][0], (97, 98) * 4)
        self.assertEqual(features["common_byte_prefix"][0], (2, 2, 1, 1, 1, 1, 1, 1))
        self.assertEqual(features["byte_levenshtein"][0], (1, 1, 2, 2, 2, 2, 2, 2))
        self.assertEqual(features["byte_sum_mod_257"][0][0], 204)
        self.assertEqual(source._levenshtein("é".encode(), b"e"), 2)
        self.assertEqual(source._prefix(b"abcd"[::-1], b"xxcd"[::-1]), 2)
        self.assertNotIn("byte_0", registry.nonconstant_features)

    def test_all_pairwise_signs_use_ordinal_tie_ranks_then_final_position(self):
        registry = source.build_null_registry(**unicode_fixture())
        features = {feature.name: feature.values for feature in registry.features}
        actual = {policy.name: policy.positions for policy in registry.policies if policy.name.startswith("pair:")}
        expected = {}
        for first, second in combinations(registry.nonconstant_features, 2):
            for first_sign, second_sign in product((1, -1), repeat=2):
                choices = []
                for left, right in zip(features[first], features[second]):
                    first_order = sorted(range(8), key=lambda position: (left[position], position))
                    second_order = sorted(range(8), key=lambda position: (right[position], position))
                    totals = [first_sign * first_order.index(position) + second_sign * second_order.index(position)
                              for position in range(8)]
                    choices.append(totals.index(min(totals)))
                expected[f"pair:{first}:{second}:{first_sign:+d},{second_sign:+d}"] = tuple(choices)
        self.assertEqual(actual, expected)
        self.assertEqual(len(registry.policies), 2 * len(features) + 10 + len(expected))

    def test_invalid_prelabel_inputs_fail_without_padding_or_redraw(self):
        invalid = (
            {"sources": self.inputs["sources"][:15]},
            {"sources": ("same",) * 16},
            {"sources": ("has space",) + self.inputs["sources"][1:]},
            {"sources": ("e\u0301",) + self.inputs["sources"][1:]},
            {"candidate_orders": (self.endpoints[:7],) + self.inputs["candidate_orders"][1:]},
            {"candidate_orders": (self.endpoints[8:],) + self.inputs["candidate_orders"][1:]},
            {"token_lengths": ((0,) * 8,) * 16},
            {"token_lengths": ((True,) * 8,) * 16},
            {"token_lengths": ((2,) * 8,) + self.inputs["token_lengths"][1:]},
        )
        for change in invalid:
            with self.subTest(change=tuple(change)), self.assertRaises(ValueError):
                source.build_null_registry(**(self.inputs | change))
        orders = tuple(tuple("long" if item == "a" else item for item in order)
                       for order in self.inputs["candidate_orders"])
        with self.assertRaisesRegex(ValueError, "ragged_candidate_byte_positions_unbound"):
            source.build_null_registry(**(self.inputs | {"candidate_orders": orders}))

    def test_constraints_use_128_within_block_variables_and_pi_on_query_rows(self):
        orders = list(self.inputs["candidate_orders"])
        orders[1] = tuple(reversed(orders[1]))
        registry = source.build_null_registry(**(self.inputs | {"candidate_orders": tuple(orders)}))
        constraints = source._constraints(registry, self.endpoints)
        by_name = {item.name: item for item in constraints}
        self.assertEqual(len(constraints), 32 + 16 + 2 * len(registry.policies))
        self.assertTrue(all(0 <= index < 128 for item in constraints for index in item.indices))
        self.assertEqual(by_name["row:8"].indices, tuple(range(64, 72)))
        self.assertEqual(by_name["column:9"].indices, tuple(query * 8 + 1 for query in range(8, 16)))
        self.assertEqual(by_name["position:AUTH:0"].indices[:2], (0, 15))
        self.assertEqual(by_name["position:DERANGED:0"].indices[:2], (8, 7))
        self.assertEqual(by_name["null:DERANGED:position:0"].indices, by_name["position:DERANGED:0"].indices)
        self.assertEqual(source.PI, tuple(index ^ 1 for index in range(16)))

    def test_import_and_registry_build_do_not_import_optional_or_native_modules(self):
        script = """
import sys
class BlockedImports:
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'scipy', 'numpy', 'torch', 'transformers', 'peft'}:
            raise AssertionError(fullname)
sys.meta_path.insert(0, BlockedImports())
from gpu import astra_pchain2_nulls as module
sources = tuple('Q' + chr(65 + index) for index in range(16))
endpoints = tuple(chr(97 + index) for index in range(16))
orders = tuple(endpoints[index // 8 * 8:index // 8 * 8 + 8] for index in range(16))
module.build_null_registry(sources=sources, candidate_orders=orders, token_lengths=((1,) * 8,) * 16)
assert not {'scipy', 'numpy', 'torch', 'transformers', 'peft'}.intersection(sys.modules)
"""
        subprocess.run([sys.executable, "-B", "-c", script], check=True,
                       cwd=Path(__file__).resolve().parents[1])


class InjectedSolverTests(unittest.TestCase):
    def setUp(self):
        inputs, self.endpoints = fixture()
        self.registry = source.build_null_registry(**inputs)
        self.calls = []
        self.clock = FakeClock()

    def solver(self, objective, constraints, remaining):
        self.calls.append((objective, constraints, remaining))
        return optimal_outcome(objective)

    def run_solver(self, **changes):
        options = dict(endpoint_ids=self.endpoints, expected_registry_sha256=self.registry.registry_sha256,
                       _solver=self.solver, _clock=self.clock)
        return source.solve_assignment(self.registry, **(options | changes))

    def assert_failure(self, result, fragment):
        self.assertIn(fragment, str(result.error))
        self.assertIsNone(result.assignment)
        self.assertIsNone(result.deranged_assignment)
        self.assertIsNone(result.solution_sha256)
        self.assertNotEqual(result.terminal_reason, "source_solution")

    def test_sixteen_sequential_objectives_fix_optimal_rows_and_retain_registry(self):
        before = deepcopy(self.registry)
        result = self.run_solver()
        self.assertIsNone(result.error)
        self.assertEqual(result.assignment, tuple(range(16)))
        self.assertEqual(result.deranged_assignment, source.PI)
        self.assertEqual(self.registry, before)
        self.assertEqual(result.registry_sha256, before.registry_sha256)
        self.assertEqual(result.membership_sha256, before.membership_sha256)
        self.assertEqual(result.backend, "injected_test_solver")
        self.assertEqual(len(self.calls), 16)
        for query, (objective, constraints, remaining) in enumerate(self.calls):
            self.assertEqual(objective, tuple(query // 8 * 8 + column if row == query else 0
                                             for row in range(16) for column in range(8)))
            fixed = tuple(item for item in constraints if item.name.startswith("fixed:"))
            self.assertEqual(tuple(item.indices for item in fixed), tuple((row * 8 + row % 8,) for row in range(query)))
            self.assertTrue(all(item.lower == item.upper == 1 for item in fixed))
            self.assertLessEqual(remaining, 60)
        self.assertEqual(result.stats["variables"], 128)
        for arm in ("AUTH", "DERANGED"):
            self.assertEqual(result.stats[arm]["position_counts"], (2,) * 8)
            self.assertEqual(result.stats[arm]["endpoint_counts"], (1,) * 16)
            self.assertEqual(result.stats[arm]["endpoint_token_length_histogram"], ((1, 16),))
            self.assertEqual(len(result.stats[arm]["policy_scores"]), len(self.registry.policies))
            self.assertEqual(result.stats[arm]["max_policy_score"], 2)
        again = self.run_solver()
        self.assertEqual(again.solution_sha256, result.solution_sha256)
        self.assertTrue(result.remaining_interfaces)
        self.assertFalse(hasattr(result, "admitted"))

    def test_registry_hash_and_endpoint_index_blocks_must_match_preseal(self):
        for changes in ({"expected_registry_sha256": "0" * 64}, {"endpoint_ids": self.endpoints[::-1]}):
            result = self.run_solver(**changes)
            self.assertIsNotNone(result.error)
            self.assertIsNone(result.assignment)
        self.assertEqual(self.calls, [])
        self.registry = replace(self.registry, policies=self.registry.policies[:-1])
        self.assert_failure(self.run_solver(), "prelabel_registry_hash_mismatch")
        self.assertEqual(self.calls, [])

    def test_unknown_timeout_and_infeasible_statuses_retain_witness_but_never_pass(self):
        for status in (1, 2, 3, 4, 99):
            def failed(objective, constraints, remaining):
                outcome = optimal_outcome(objective)
                outcome.status = status
                return outcome

            with self.subTest(status=status):
                result = self.run_solver(_solver=failed)
                self.assert_failure(result, "optimal_solver_status_required")
                self.assertEqual(len(result.steps), 1)
                self.assertEqual(result.steps[0]["outcome"].status, status)
                self.assertEqual(result.fixed_prefix, ())

    def test_bad_integrality_nan_and_exact_constraint_violations_fail(self):
        for mode in ("fractional", "nan", "out_of_bounds", "column", "missing", "gap", "bound", "fun"):
            def invalid(objective, constraints, remaining):
                outcome = optimal_outcome(objective)
                if mode == "column":
                    outcome.x = binary_vector((1, 1) + tuple(range(2, 16)))
                elif mode == "missing":
                    outcome.x = outcome.x[:-1]
                elif mode in ("gap", "bound", "fun"):
                    setattr(outcome, {"gap": "mip_gap", "bound": "mip_dual_bound", "fun": "fun"}[mode], 0.25)
                else:
                    values = list(outcome.x)
                    values[0] = {"fractional": 0.5, "nan": float("nan"), "out_of_bounds": 2.0}[mode]
                    outcome.x = values
                return outcome

            with self.subTest(mode=mode):
                result = self.run_solver(_solver=invalid)
                self.assertIsNotNone(result.error)
                self.assertIsNone(result.assignment)
                self.assertEqual(result.fixed_prefix, ())

    def test_rounding_does_not_excuse_position_or_null_constraint_failures(self):
        inputs, _ = fixture(source_matches=True)
        self.registry = source.build_null_registry(**inputs)
        self.assert_failure(self.run_solver(), "exact_constraint_failed:null:")
        inputs, _ = fixture()
        orders = list(inputs["candidate_orders"])
        orders[1] = tuple(reversed(orders[1]))
        self.registry = source.build_null_registry(**(inputs | {"candidate_orders": tuple(orders)}))
        self.assert_failure(self.run_solver(), "exact_constraint_failed:position:")

    def test_near_integral_values_require_exact_revalidated_rounded_constraints(self):
        def near(objective, constraints, remaining):
            outcome = optimal_outcome(objective)
            outcome.x = tuple(value + 1e-8 if value == 0 else value - 1e-8 for value in outcome.x)
            return outcome

        self.assertEqual(self.run_solver(_solver=near).assignment, tuple(range(16)))

    def test_prior_row_fix_cannot_be_changed_by_later_optimal_claim(self):
        def drift(objective, constraints, remaining):
            assignment = ((1, 0) + tuple(range(2, 16))) if self.calls else tuple(range(16))
            self.calls.append(objective)
            return optimal_outcome(objective, assignment=assignment)

        result = self.run_solver(_solver=drift)
        self.assert_failure(result, "exact_constraint_failed:fixed:0")
        self.assertEqual(result.fixed_prefix, (0,))
        self.assertEqual(len(self.calls), 2)

    def test_one_total_budget_not_sixteen_fresh_time_limits(self):
        def slow(objective, constraints, remaining):
            self.calls.append(remaining)
            self.clock.value += 4.0
            return optimal_outcome(objective)

        result = self.run_solver(_solver=slow)
        self.assert_failure(result, "total_60_second_budget_exhausted")
        self.assertEqual(result.terminal_reason, "time_budget_exhausted")
        self.assertEqual(self.calls, [60.0 - 4 * index for index in range(15)])
        self.assertEqual(len(result.fixed_prefix), 14)
        self.assertEqual(len(result.steps), 15)

    def test_import_time_counts_against_total_budget(self):
        def late_import():
            self.clock.value = 61.0
            return self.solver

        with patch.object(source, "_scipy_solver", side_effect=late_import):
            result = self.run_solver(_solver=None)
        self.assert_failure(result, "total_60_second_budget_exhausted")
        self.assertEqual(self.calls, [])

    def test_final_validation_overrun_cannot_publish_a_full_prefix(self):
        original = source._assignment_stats

        def delayed(*args):
            stats = original(*args)
            self.clock.value = 60.0
            return stats

        with patch.object(source, "_assignment_stats", side_effect=delayed):
            result = self.run_solver()
        self.assert_failure(result, "total_60_second_budget_exhausted")
        self.assertEqual(result.fixed_prefix, tuple(range(16)))
        self.assertEqual(len(result.steps), 16)

    def test_exception_or_unavailable_dependency_is_retained_without_retry(self):
        error = KeyboardInterrupt("synthetic interruption")

        def interrupted(objective, constraints, remaining):
            raise error

        result = self.run_solver(_solver=interrupted)
        self.assertIs(result.error, error)
        self.assertIsNone(result.assignment)
        self.assertEqual(len(result.steps), 1)
        unavailable = ImportError("synthetic scipy unavailable")
        with patch.object(source, "_scipy_solver", side_effect=unavailable):
            result = self.run_solver(_solver=None)
        self.assertIs(result.error, unavailable)
        self.assertEqual(result.steps, [])
        self.assertIsNone(result.assignment)


@unittest.skipUnless(HAS_SCIPY, "Main's isolated pinned SciPy/NumPy environment is not available")
class ActualScipyTests(unittest.TestCase):
    def solve(self, inputs, endpoints):
        registry = source.build_null_registry(**inputs)
        result = source.solve_assignment(registry, endpoint_ids=endpoints,
                                         expected_registry_sha256=registry.registry_sha256)
        self.assertIsNone(result.error, str(result.error))
        self.assertEqual(result.terminal_reason, "source_solution")
        self.assertEqual(result.backend, "scipy.optimize.milp")
        self.assertEqual(len(result.steps), 16)
        self.assertLess(result.stats["elapsed_seconds"], 60.0)
        self.assertTrue(all(step["outcome"].status == 0 for step in result.steps))
        return result

    def test_actual_pinned_milp_lexicographic_solution_and_repeatable_hash(self):
        import numpy
        import scipy

        self.assertEqual((scipy.__version__, numpy.__version__), ("1.15.3", "1.26.4"))
        inputs, endpoints = fixture()
        result = self.solve(inputs, endpoints)
        self.assertEqual(result.assignment, tuple(range(16)))
        self.assertEqual(result.deranged_assignment, source.PI)
        self.assertEqual(result.solution_sha256, self.solve(inputs, endpoints).solution_sha256)
        reverse_blocks = endpoints[:8][::-1] + endpoints[8:][::-1]
        reordered = self.solve(inputs, reverse_blocks)
        self.assertEqual(reordered.assignment, tuple(range(16)))
        self.assertNotEqual(result.constraints_sha256, reordered.constraints_sha256)
        self.assertNotEqual(result.solution_sha256, reordered.solution_sha256)

    def test_actual_solver_enforces_source_sensitive_nulls_for_both_arms(self):
        inputs, endpoints = fixture(source_matches=True)
        result = self.solve(inputs, endpoints)
        self.assertNotEqual(result.assignment, tuple(range(16)))
        self.assertEqual(result.deranged_assignment, tuple(result.assignment[index ^ 1] for index in range(16)))
        for arm in ("AUTH", "DERANGED"):
            self.assertEqual(result.stats[arm]["position_counts"], (2,) * 8)
            self.assertLessEqual(result.stats[arm]["max_policy_score"], 4)
        self.assertEqual(result.solution_sha256, self.solve(inputs, endpoints).solution_sha256)

    def test_actual_backend_uses_documented_binary_bounds_constraints_and_shared_budget(self):
        from scipy import optimize

        inputs, endpoints = fixture()
        with patch.object(optimize, "milp", wraps=optimize.milp) as calls:
            result = self.solve(inputs, endpoints)
        self.assertEqual(calls.call_count, 16)
        limits = []
        for query, call in enumerate(calls.call_args_list):
            options = call.kwargs
            self.assertEqual(tuple(options["integrality"]), (1,) * 128)
            self.assertIsInstance(options["bounds"], optimize.Bounds)
            self.assertEqual(tuple(options["bounds"].lb), (0,))
            self.assertEqual(tuple(options["bounds"].ub), (1,))
            self.assertIsInstance(options["constraints"], optimize.LinearConstraint)
            self.assertEqual(options["constraints"].A.shape, (result.stats["constraints"] + query, 128))
            self.assertEqual(options["options"]["mip_rel_gap"], 0.0)
            self.assertGreater(options["options"]["time_limit"], 0)
            self.assertLessEqual(options["options"]["time_limit"], result.steps[query]["time_limit"])
            limits.append(options["options"]["time_limit"])
        self.assertLess(limits[-1], limits[0])
        self.assertLessEqual(max(limits), 60.0)

    def test_actual_infeasibility_is_terminal_not_a_redraw(self):
        inputs, endpoints = fixture()
        registry = source.build_null_registry(**inputs)
        constraints = source._constraints(registry, endpoints)
        contradictory = constraints + (source.BinaryConstraint("require", (0,), 1, 1),
                                       source.BinaryConstraint("forbid", (0,), 0, 0))
        with patch.object(source, "_constraints", return_value=contradictory):
            result = source.solve_assignment(registry, endpoint_ids=endpoints,
                                             expected_registry_sha256=registry.registry_sha256)
        self.assertIsNone(result.assignment)
        self.assertIsNone(result.solution_sha256)
        self.assertEqual(len(result.steps), 1)
        self.assertEqual(result.steps[0]["outcome"].status, 2)

    def test_mismatched_package_version_fails_before_solving(self):
        import scipy

        inputs, endpoints = fixture()
        registry = source.build_null_registry(**inputs)
        with patch.object(scipy, "__version__", "not-the-bound-version"):
            result = source.solve_assignment(registry, endpoint_ids=endpoints,
                                             expected_registry_sha256=registry.registry_sha256)
        self.assertIn("pinned_scipy_numpy_versions_required", str(result.error))
        self.assertIsNone(result.assignment)
        self.assertEqual(result.steps, [])


if __name__ == "__main__":
    unittest.main()
