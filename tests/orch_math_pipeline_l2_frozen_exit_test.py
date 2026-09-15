from pathlib import Path
import tempfile
import unittest

from gpu import orch_math_pipeline_l2_frozen_exit as final


class FrozenExitTest(unittest.TestCase):
    def test_final_test_requires_actual_unchanged_failed_mount(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            campaign = root / 'campaign_01_existing_rich'
            failed = campaign / 'FROZEN/cycle3/experience'
            prior = campaign / 'FROZEN/cycle2/experience'
            failed.mkdir(parents=True)
            prior.mkdir(parents=True)
            adapter = dict(state_sha256=final.common.INITIAL_SHA)
            failure = dict(message='verbatim_teacher_sentence_not_child_sleep_target', arm='FROZEN',
                phase='experience', cycle=3, process=['boot', 1, 2], input_adapter=adapter)
            final.common.write(failed / 'FAILED.json', failure)
            final.common.write(prior / 'COMPLETE.json', dict(status='COMPLETE', updates=0, output_adapter=adapter))
            after = dict(frozen_base_verified=True, process=failure['process'], mounted_adapter_state_sha256='wrong')
            final.common.write(failed / 'FAILED_AFTER.json', after)
            with self.assertRaises(AssertionError):
                final.binding(root)
            final.common.write(failed / 'FAILED_AFTER.json', dict(after, mounted_adapter_state_sha256=final.common.INITIAL_SHA))
            self.assertEqual(final.binding(root)[0], campaign)


if __name__ == '__main__':
    unittest.main()
