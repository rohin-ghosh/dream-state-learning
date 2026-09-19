import json
from pathlib import Path
import unittest

import stage


class StageTests(unittest.TestCase):
    def test_refuses_incomplete_overlay_before_any_access(self):
        with self.assertRaisesRegex(ValueError, 'three_file'):
            stage.stage(dict(status='EXACT_GUARDED_SOURCE_VERIFIED'), {}, '/not/created')

    def test_preserves_input_file_set_and_does_not_offer_dispatch(self):
        self.assertEqual(len(stage.FILES), 3)
        text = Path(stage.__file__).read_text()
        for forbidden in ('SIGTERM', 'SIGSTOP', 'pidfd_send_signal', 'torch.load', 'subprocess.Popen'):
            self.assertNotIn(forbidden, text)

    def test_pair_overlay_hashes_match_verified_preimages(self):
        own = Path(__file__).resolve().parent
        report = json.loads((own / 'PATCH_APPLICABILITY.json').read_bytes())
        staged = own.parent / 'post_recovery_parent_retention_adoption_20260918/stage'
        pair = [item for item in report['results'] if item['life'].startswith('curriculum_')]
        self.assertEqual(len(pair), 2)
        for item in pair:
            for name in stage.FILES:
                self.assertEqual(stage.digest((staged / name).read_bytes()), item['changes'][name]['after'])


if __name__ == '__main__':
    unittest.main()
