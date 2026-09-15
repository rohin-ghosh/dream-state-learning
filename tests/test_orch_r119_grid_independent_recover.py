import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

from gpu import orch_r115_grid_native as grid
from gpu import orch_r119_grid_independent_recover as subject


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.messages = [dict(role='user', content='same actual prefix')]
        self.row = dict(kind='NATIVE', number=1, cycle=9, task_id='TRAIN1', purpose='episode')
        grid.write(self.root/'calls/N00001.json',dict(status='COMPLETE',messages=self.messages,
            cap=384,response=dict(raw='actual old response',token_ids=[1,2])))

        class Parent:
            def __init__(self, root):
                self.root, self.cycle = root, 9

            def calls(self, *args, **kwargs):
                raise AssertionError('no redispatch or mailbox poll during cached prefix')

            def event(self, *args):
                pass

        self.life=subject.replay_class(grid,Parent,[self.row],dry=True)(self.root)

    def test_returns_actual_cached_tokens_without_model(self):
        result=self.life.calls([dict(id='TRAIN1')],'episode',[self.messages],384)
        self.assertEqual(result[0]['raw'],'actual old response')
        self.assertEqual(result[0]['token_ids'],[1,2])
        with self.assertRaises(subject.CachedBoundary):
            self.life.calls([dict(id='TRAIN1')],'episode',[self.messages],384)

    def test_no_prefix_target_rescue(self):
        with self.assertRaisesRegex(ValueError,'exact_cached_prompt'):
            self.life.calls([dict(id='TRAIN1')],'episode',[[dict(role='user',content='changed')]],384)

    def test_no_cap_change(self):
        with self.assertRaisesRegex(ValueError,'exact_cached_prompt'):
            self.life.calls([dict(id='TRAIN1')],'episode',[self.messages],385)

    def test_no_held_reconstruction(self):
        with self.assertRaisesRegex(ValueError,'cached_causal_sequence'):
            self.life.calls([dict(id='TRAIN1')],'episode',[self.messages],384,attached_readout=True)

    def test_clean_does_not_erase_intervention_or_source(self):
        self.assertEqual(subject.clean(dict(created_unix=1,observed_unix=2,source='pin')),
                         dict(observed_unix=2,source='pin'))

    def test_prospective_low_broker_preserves_old_claims(self):
        from gpu import orch_r119_grid_fast_recovery_parent as parent
        source = parent.source()
        compile(source, 'recovery_parent', 'exec')
        self.assertIn('EXISTING_CLAIM_NO_RETRY', source)
        self.assertIn('R119_GRID_INDEPENDENT_RECOVERY_TERMINAL.json', source)
        self.assertIn('"\'low\'"', source)


if __name__ == '__main__':
    unittest.main()
