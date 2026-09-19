"""Latest pending evidence cannot be hidden by an older successful delivery."""

from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parent))
from audit_fresh_errors import attach_report, latest_failures


class FreshErrorTests(unittest.TestCase):
    def test_unreported_new_transport_failure_stays_pending(self):
        transport=dict(session_id='life',unix=2,origin=dict(record_sha256='new'))
        older=dict(life='life',transport_failure=dict(unix=1),result=dict(origin=dict(record_sha256='old'),INBOX=dict(index=3)))
        pending=attach_report(transport,'actual.json',[older])
        self.assertEqual(latest_failures([older,pending]),[pending])
        self.assertEqual(pending['result']['status'],'NEW_NATURAL_FAILURE_FEEDBACK_PENDING')

    def test_new_pending_failure_not_replaced_with_old_verified_delivery(self):
        older=dict(life='life',transport_failure=dict(unix=1),result=dict(INBOX=dict(index=3)))
        newer=dict(life='life',transport_failure=dict(unix=2),result=dict(INBOX=None))
        self.assertEqual(latest_failures([newer,older]),[newer])

    def test_lives_are_independent_and_input_order_is_irrelevant(self):
        first=dict(life='first',transport_failure=dict(unix=5))
        second=dict(life='second',transport_failure=dict(unix=4))
        self.assertEqual(latest_failures([second,first]),[first,second])


if __name__=='__main__':
    unittest.main()
