from copy import deepcopy
import unittest

import r188_readmit3 as readmit


class FreshAdmissionTests(unittest.TestCase):
    def test_only_exact_gone_prelaunch_process(self):
        report = dict(clear=False, scanner_euid=0, blocking_reasons=['process_identity_drift:1980126'],
            gpu=dict(uuid=readmit.receiving.DEVICES[6][0], memory_used_mib=0, utilization_percent=0))
        readmit.eligible(report, False, False)
        for launched, present in ((True, False), (False, True), (True, True)):
            with self.assertRaises(ValueError):
                readmit.eligible(report, launched, present)
        for field, value in (('blocking_reasons', ['unknown']), ('scanner_euid', 2524), ('clear', True)):
            candidate = deepcopy(report)
            candidate[field] = value
            with self.assertRaises(ValueError):
                readmit.eligible(candidate, False, False)


if __name__ == '__main__':
    unittest.main()
