"""Source-only wrapper tests; no native model or collection."""

import subprocess
import sys
import unittest
from unittest.mock import patch

from gpu import astra_stage2a_d2_collect_v2 as successor


class Tests(unittest.TestCase):
    def test_import_does_not_reconfigure_original(self):
        result = subprocess.run([sys.executable, "-B", "-c", (
            "from gpu import astra_stage2a_d2_collect as source; "
            "before=(source.MASTER,source.collector.MASTER,source.collector.GUIDANCE); "
            "from gpu import astra_stage2a_d2_collect_v2; "
            "assert before==(source.MASTER,source.collector.MASTER,source.collector.GUIDANCE)"
        )], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_only_fresh_master_and_existing_strategy_are_configured(self):
        source = successor.source
        with patch.object(source, "MASTER", source.MASTER), patch.object(
                source.collector, "GUIDANCE", source.collector.GUIDANCE):
            def native_main(arguments):
                self.assertEqual(arguments, ["native-arguments"])
                self.assertEqual(source.MASTER, successor.MASTER)
                self.assertEqual(source.collector.GUIDANCE, successor.strategy.GUIDANCE)
                return "SYNTHETIC_NO_NATIVE_RUN"
            with patch.object(source, "main", side_effect=native_main):
                self.assertEqual(successor.main(["native-arguments"]), "SYNTHETIC_NO_NATIVE_RUN")

    def test_master_is_disjoint_from_previous_collectors_and_evaluation(self):
        from gpu import astra_stage2a_outcome_distill as student

        self.assertNotIn(successor.MASTER, (
            b"ASTRA-OUTCOME-COLLECT-TRAIN-20260914-A1", successor.strategy.MASTER,
            b"ASTRA-OUTCOME-COLLECT-TRAIN-20260914-A3", student.EVAL_MASTER))


if __name__ == "__main__":
    unittest.main()
