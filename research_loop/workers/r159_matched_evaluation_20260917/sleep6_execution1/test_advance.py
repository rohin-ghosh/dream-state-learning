from copy import deepcopy
import unittest
from advance import ready_keys


class AdvanceTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = dict(keys={arm+'_'+str(step):dict(operator_exists=False)
            for arm in ('parented_learning','unparented_learning') for step in (1,2,4)})
        self.snapshot['keys']['parented_learning_1'] = dict(operator_exists=True,completion={'hash':'test'},
            native_gone=True,timeout_gone=True,wrapper_gone=True,failed=False,
            DISPOSITION=dict(result=dict(status='METADATA_ONLY')))

    def test_independent_slot_advances_without_clock_wave(self):
        self.assertEqual(ready_keys(self.snapshot,1789630500),['parented_learning_2'])

    def test_each_identity_required(self):
        for role in ('native_gone','timeout_gone','wrapper_gone'):
            snapshot = deepcopy(self.snapshot)
            snapshot['keys']['parented_learning_1'][role] = False
            self.assertEqual(ready_keys(snapshot,1789630500),[])

    def test_existing_attempt_never_retried(self):
        self.snapshot['keys']['parented_learning_2']['operator_exists'] = True
        self.assertEqual(ready_keys(self.snapshot,1789630500),[])

    def test_failure_or_missing_completion_stops(self):
        for change in (dict(failed=True),dict(completion=None),dict(DISPATCH_ERROR={'status':'error'}),
                       dict(DISPOSITION=dict(result=dict(status='DEVICE_BUSY_NO_SIGNALS_NO_RESERVATION')))):
            snapshot = deepcopy(self.snapshot)
            snapshot['keys']['parented_learning_1'].update(change)
            self.assertEqual(ready_keys(snapshot,1789630500),[])

    def test_full_window_required(self):
        self.assertEqual(ready_keys(self.snapshot,1789642780),[])


if __name__ == '__main__':
    unittest.main()
