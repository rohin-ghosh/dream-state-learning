from __future__ import annotations

import hashlib
import unittest

from rml_d0.bayes import first_accept_toy_goldens
from rml_d0.canonical import canonical_bytes


class NoLifeBayesTests(unittest.TestCase):
    def test_independent_first_accept_vector(self) -> None:
        vector = first_accept_toy_goldens()["oracle_vector"]
        self.assertEqual(
            hashlib.sha256(canonical_bytes(vector)).hexdigest(),
            "8ba883f19c7c6fee04e42c9bc64488ef9359a65e684c53799a74253fab08d704",
        )
        self.assertEqual(vector["attempt_weights_by_cap"], [[1], [4, 3], [16, 12, 9], [64, 48, 36, 27]])
        self.assertEqual(vector["heterogeneous_posterior_h0_h1"], [[1, 2], [7, 12], [37, 56], [35, 48]])


if __name__ == "__main__":
    unittest.main()
