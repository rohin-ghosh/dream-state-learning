import unittest
from gpu.orch_math_feedback_uptake_r124_broker_handoff import ready


class BrokerHandoffTests(unittest.TestCase):
    def test_all_five_conditions_required(self):
        self.assertTrue(ready(True,True,True,True,True))
        for index in range(5):
            conditions=[True]*5
            conditions[index]=False
            self.assertFalse(ready(*conditions))


if __name__=='__main__':unittest.main()
