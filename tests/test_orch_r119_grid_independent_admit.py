import unittest
from unittest.mock import patch

from gpu import orch_r119_grid_independent_admit as subject


class AdmissionTests(unittest.TestCase):
    def test_failure_preserved_then_fresh_clear(self):
        failed=dict(clear=False,scanner_euid=0,blocking_reasons=['process_identity_drift:1'])
        clear=dict(clear=True,scanner_euid=0,blocking_reasons=[])
        sequence=iter([failed,clear]); saved=[]
        with patch.object(subject.time,'sleep'):
            result=subject.stable_scan(lambda:next(sequence),lambda index,report:saved.append(report))
        self.assertIs(result,clear)
        self.assertEqual(saved,[failed,clear])
        self.assertEqual(failed['blocking_reasons'],['process_identity_drift:1'])

    def test_nonprivileged_clear_never_suffices(self):
        report=dict(clear=True,scanner_euid=1000,blocking_reasons=[]); saved=[]
        with patch.object(subject.time,'sleep'):
            subject.stable_scan(lambda:report,lambda index,item:saved.append(item),attempts=3)
        self.assertEqual(len(saved),3)

    def test_target_occupied_never_waived(self):
        report=dict(clear=False,scanner_euid=0,blocking_reasons=['target_open'])
        with patch.object(subject.time,'sleep'):
            result=subject.stable_scan(lambda:report,lambda index,item:None,attempts=2)
        self.assertFalse(result['clear'])
        self.assertEqual(result['blocking_reasons'],['target_open'])


if __name__ == '__main__':
    unittest.main()
