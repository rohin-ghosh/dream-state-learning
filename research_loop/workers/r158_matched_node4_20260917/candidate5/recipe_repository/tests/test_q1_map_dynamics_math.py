"""Offline arithmetic regression fixtures; no archived outcomes or model calls."""

import ast
import copy
import math
from pathlib import Path
import statistics
import unittest

from gpu import q1_map_dynamics_math as dynamics


class Q1MapDynamicsMathTests(unittest.TestCase):
    def assert_vector(self, actual, expected):
        self.assertEqual(len(actual), len(expected))
        for actual_value, expected_value in zip(actual, expected):
            self.assertAlmostEqual(actual_value, expected_value)

    def test_constant_shift_and_singleton_quantiles(self):
        off = [5.5377, 7.5417, 5.2742, 5.4192]
        result = dynamics.reduce_arm(off, [value - 2 for value in off], "P_AUTH")
        self.assert_vector(result["delta"], [-2] * 4)
        self.assertEqual(result["C"], {
            "vector": [-2.0],
            "stats": {
                "mean": -2.0, "median": -2.0, "q25": -2.0, "q75": -2.0,
                "iqr": 0.0, "quantile_method": "inclusive",
                "sign_counts": {"positive": 0, "negative": 1, "zero": 0},
            },
        })
        for component in ("O", "M", "X", "map_aligned_X"):
            self.assertEqual(result[component]["vector"], [0.0])

    def test_xor_signs_and_opposite_own_maps(self):
        result = dynamics.reduce_pair([0] * 4, [3, -3, -3, 3], [-5, 5, 5, -5])
        auth = result["arms"]["P_AUTH"]
        deranged = result["arms"]["P_DERANGED"]
        self.assertEqual(auth["X"]["vector"], [3.0])
        self.assertEqual(deranged["X"]["vector"], [-5.0])
        self.assertEqual(auth["map_aligned_X"]["vector"], [3.0])
        self.assertEqual(deranged["map_aligned_X"]["vector"], [5.0])
        self.assertEqual(auth["own_map_signed_margin"], {
            "mean": 3.0, "median": 3.0, "correct_count": 4,
            "incorrect_count": 0, "zero_count": 0, "total": 4,
        })
        self.assertEqual(deranged["own_map_signed_margin"]["mean"], 5.0)
        self.assertEqual(result["C_shared"]["vector"], [0.0])
        self.assertEqual(result["X_split"]["vector"], [4.0])
        self.assertEqual(result["both_correct"], 4)
        self.assertAlmostEqual(result["delta_cosine"], -1.0)

    def test_each_walsh_basis_and_reconstruction(self):
        basis = {
            "C": [1, 1, 1, 1], "O": [1, 1, -1, -1],
            "M": [1, -1, 1, -1], "X": [1, -1, -1, 1],
        }
        for name, values in basis.items():
            with self.subTest(basis=name):
                result = dynamics.reduce_arm([0] * 4, values, "P_AUTH")
                for component in basis:
                    self.assertEqual(result[component]["vector"], [float(component == name)])
        off = [11, -2, 5, 8]
        delta = [8, -2, 4, -6]
        result = dynamics.reduce_arm(off, [left + right for left, right in zip(off, delta)], "P_AUTH")
        self.assertEqual([result[name]["vector"][0] for name in basis], [1, 2, 5, 0])
        reconstructed = [
            sum(result[name]["vector"][0] * signs[index] for name, signs in basis.items())
            for index in range(4)
        ]
        self.assert_vector(reconstructed, delta)

    def test_raw_margins_not_deltas_determine_own_map_correctness(self):
        result = dynamics.reduce_arm([100] * 4, [2, -4, -6, 8], "P_AUTH")
        self.assertTrue(all(value < 0 for value in result["delta"]))
        self.assertEqual(result["own_map_signed_margin"], {
            "mean": 5.0, "median": 5.0, "correct_count": 4,
            "incorrect_count": 0, "zero_count": 0, "total": 4,
        })

    def test_ties_are_separate_and_never_both_correct(self):
        result = dynamics.reduce_pair([0] * 4, [0, -2, 2, -0.0], [-1, 3, 0, 0])
        self.assertEqual(result["arms"]["P_AUTH"]["own_map_signed_margin"], {
            "mean": 0.0, "median": 0.0, "correct_count": 1,
            "incorrect_count": 1, "zero_count": 2, "total": 4,
        })
        self.assertEqual(result["arms"]["P_DERANGED"]["own_map_signed_margin"]["zero_count"], 2)
        self.assertEqual(result["both_correct"], 1)

    def test_common_motion_and_orthogonal_cosines(self):
        shared = dynamics.reduce_pair([0] * 4, [2] * 4, [4] * 4)
        self.assertEqual(shared["C_shared"]["vector"], [3.0])
        self.assertEqual(shared["X_split"]["vector"], [0.0])
        self.assertAlmostEqual(shared["delta_cosine"], 1.0)
        self.assertEqual(shared["both_correct"], 0)
        orthogonal = dynamics.reduce_pair([0] * 4, [2] * 4, [3, -3, -3, 3])
        self.assertEqual(orthogonal["delta_cosine"], 0.0)

    def test_zero_norm_in_either_arm(self):
        off = [1, 2, 3, 4]
        moved = [2, 3, 4, 5]
        for auth, deranged in ((off, off), (off, moved), (moved, off)):
            with self.subTest(auth=auth, deranged=deranged):
                self.assertIsNone(dynamics.reduce_pair(off, auth, deranged)["delta_cosine"])

    def test_cosine_scales_without_norm_overflow_or_underflow(self):
        for scale in (1e-300, 1e300):
            with self.subTest(scale=scale):
                result = dynamics.reduce_pair([0] * 4, [scale] * 4, [-scale] * 4)
                self.assertAlmostEqual(result["delta_cosine"], -1.0)

    def test_128_rows_preserve_quartet_vectors_and_inclusive_quantiles(self):
        coefficients = list(range(-16, 16))
        off = [100] * 128
        margins = [100 + value for coefficient in coefficients for value in (
            coefficient + 7, coefficient - 3, coefficient - 5, coefficient + 1
        )]
        result = dynamics.reduce_arm(off, margins, "P_AUTH")
        self.assertEqual(len(result["delta"]), 128)
        self.assertEqual(result["C"]["vector"], coefficients)
        for name, expected in (("O", 2), ("M", 1), ("X", 4), ("map_aligned_X", 4)):
            self.assertEqual(result[name]["vector"], [expected] * 32)
        self.assertEqual(result["C"]["stats"], {
            "mean": -0.5, "median": -0.5, "q25": -8.25, "q75": 7.25,
            "iqr": 15.5, "quantile_method": "inclusive",
            "sign_counts": {"positive": 15, "negative": 16, "zero": 1},
        })
        self.assertEqual(statistics.quantiles(coefficients, n=4, method="inclusive"), [-8.25, -0.5, 7.25])
        for index in range(32):
            constant, orientation, mode, xor = [result[name]["vector"][index] for name in ("C", "O", "M", "X")]
            self.assert_vector(result["delta"][4 * index:4 * index + 4], [
                constant + orientation + mode + xor,
                constant + orientation - mode - xor,
                constant - orientation + mode - xor,
                constant - orientation - mode + xor,
            ])
        pair = dynamics.reduce_pair(off, margins, margins)
        self.assertEqual(pair["arms"]["P_AUTH"], result)
        self.assertEqual(pair["C_shared"]["vector"], coefficients)
        self.assertEqual(pair["X_split"]["vector"], [0] * 32)
        self.assertEqual(pair["X_split"]["stats"]["sign_counts"]["zero"], 32)
        self.assertEqual(pair["arms"]["P_DERANGED"]["own_map_signed_margin"]["total"], 128)
        self.assertEqual(pair["both_correct"], 0)
        self.assertAlmostEqual(pair["delta_cosine"], 1.0)

    def test_pair_128_both_correct_uses_all_rows(self):
        auth = [1, -1, -1, 1] * 32
        deranged = [-value for value in auth]
        self.assertEqual(dynamics.reduce_pair([0] * 128, auth, deranged)["both_correct"], 128)

    def test_invalid_inputs_in_every_argument(self):
        invalid = [
            None, "0000", (0, 0, 0, 0), {0: 0}, [], [0], [0] * 8,
            [0] * 127, [0] * 129, [True, 0, 0, 0], [False, 0, 0, 0],
            [math.inf, 0, 0, 0], [-math.inf, 0, 0, 0], [math.nan, 0, 0, 0],
            ["1", 0, 0, 0], [None, 0, 0, 0], [1j, 0, 0, 0], [[1], 0, 0, 0],
            [10 ** 400, 0, 0, 0],
        ]
        for values in invalid:
            for position in range(2):
                with self.subTest(values=values, arm_position=position):
                    args = [[0] * 4, [0] * 4]
                    args[position] = values
                    with self.assertRaises(ValueError):
                        dynamics.reduce_arm(*args, "P_AUTH")
            for position in range(3):
                with self.subTest(values=values, pair_position=position):
                    args = [[0] * 4, [0] * 4, [0] * 4]
                    args[position] = values
                    with self.assertRaises(ValueError):
                        dynamics.reduce_pair(*args)

    def test_unequal_valid_lengths_and_invalid_arms(self):
        for first, second in ((4, 128), (128, 4)):
            with self.assertRaises(ValueError):
                dynamics.reduce_arm([0] * first, [0] * second, "P_AUTH")
        for position in range(3):
            args = [[0] * 4, [0] * 4, [0] * 4]
            args[position] = [0] * 128
            with self.assertRaises(ValueError):
                dynamics.reduce_pair(*args)
        for arm in (None, True, 1, [], {}, "AUTH", "DERANGED", "p_auth", "P_OFF"):
            with self.subTest(arm=arm), self.assertRaises(ValueError):
                dynamics.reduce_arm([0] * 4, [0] * 4, arm)

    def test_unrepresentable_delta_is_rejected(self):
        with self.assertRaises(ValueError):
            dynamics.reduce_arm([-1e308] * 4, [1e308] * 4, "P_AUTH")

    def test_no_input_mutation_or_result_aliasing(self):
        args = [[0] * 4, [1, -1, -1, 1], [-2, 2, 2, -2]]
        before = copy.deepcopy(args)
        result = dynamics.reduce_pair(*args)
        self.assertEqual(args, before)
        result["arms"]["P_AUTH"]["delta"][0] = 99
        self.assertEqual(args, before)
        result["arms"]["P_AUTH"]["map_aligned_X"]["vector"][0] = 99
        self.assertEqual(result["arms"]["P_AUTH"]["X"]["vector"], [1.0])

    def test_public_schema_and_stdlib_only_import_boundary(self):
        result = dynamics.reduce_pair([0] * 4, [0] * 4, [0] * 4)
        self.assertEqual(set(result), {"arms", "C_shared", "X_split", "delta_cosine", "both_correct"})
        self.assertEqual(set(result["arms"]), {"P_AUTH", "P_DERANGED"})
        self.assertEqual(set(result["arms"]["P_AUTH"]), {
            "C", "O", "M", "X", "delta", "own_map_signed_margin", "map_aligned_X",
        })
        tree = ast.parse(Path(dynamics.__file__).read_text())
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.add(node.module)
        self.assertEqual(imports, {"math", "numbers", "statistics"})


if __name__ == "__main__":
    unittest.main()
