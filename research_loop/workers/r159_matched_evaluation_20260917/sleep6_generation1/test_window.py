import unittest
from admission_wrapper import require_prospective_window


class WindowTests(unittest.TestCase):
    def setUp(self):
        self.config = dict(hard_end_unix=1789646400,source_read_end_unix=1789646400,lease_end_unix=1789980180)

    def test_proposed_waves_fit(self):
        for now in (1789631100,1789635000,1789638900):
            require_prospective_window(now,self.config)

    def test_equal_late_nonfinite_rejected(self):
        for now in (1789642785,1789642786,float('nan'),float('inf'),True):
            with self.assertRaises(AssertionError):
                require_prospective_window(now,self.config)

    def test_wrong_wall_or_margin_rejected(self):
        for changed in (dict(hard_end_unix=1789632000),dict(source_read_end_unix=1789632000),dict(lease_end_unix=1789646400)):
            with self.assertRaises(AssertionError):
                require_prospective_window(1789631100,dict(self.config,**changed))


if __name__ == '__main__':
    unittest.main()
