from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import capture_fixed
import preparation_io as common


class FixedCaptureTests(unittest.TestCase):
    def fixture(self):
        context = dict(system_prompt='original system',birth_prompt='original birth')
        commit = dict(checkpoint_sha256={'adapter':'hash'})
        body = dict(cycle=34,status='COMPLETE',checkpoint=commit)
        state = dict(pending=None,rows=[{}],sleep_frontier=1,sleep_receipts=[{}]*33+[deepcopy(body)],
            model_state_sha256=common.digest(commit['checkpoint_sha256']),history=dict(context,events=[]))
        body['resume_state'] = dict(state=state,sha256=common.digest(state))
        return dict(kind='SLEEP_COMPLETE',document=body),commit,context

    def test_exact_archived_sleep_context(self):
        document,commit,context = self.fixture()
        self.assertEqual(capture_fixed.validate_sleep(document,commit,context,34)['events'],[])

    def test_other_cycle_or_incomplete_sleep_refused(self):
        document,commit,context = self.fixture()
        with self.assertRaises(ValueError):
            capture_fixed.validate_sleep(document,commit,context,35)
        document['document']['status'] = 'INCOMPLETE'
        with self.assertRaises(ValueError):
            capture_fixed.validate_sleep(document,commit,context,34)

    def test_living_context_is_not_substituted(self):
        document,commit,context = self.fixture()
        with self.assertRaisesRegex(ValueError,'original_not_living_birth_context'):
            capture_fixed.validate_sleep(document,commit,dict(context,birth_prompt='new living context'),34)


if __name__=='__main__':
    unittest.main()
