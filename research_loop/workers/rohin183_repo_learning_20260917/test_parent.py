import unittest
import tempfile
from pathlib import Path
import time

from gpu.orch_r125_stream_journal import StreamJournal
from organism_v6.orch_r124_train_history import TrainHistory
from organism_v6.orch_r125_continual_stream import ContinualStream
from research_loop.workers.rohin183_repo_learning_20260917.parent_feed import collect

from research_loop.workers.rohin183_repo_learning_20260917.parent import should_call


class ParentTests(unittest.TestCase):
    def test_waits_for_actual_first_response(self):
        self.assertFalse(should_call(0,0,0,0,1000,None))
        self.assertTrue(should_call(1,0,0,0,1000,None))

    def test_requires_new_content_and_elapsed_time(self):
        self.assertFalse(should_call(3,1,1,1000,1400,None))
        self.assertFalse(should_call(4,1,1,1000,1200,None))
        self.assertTrue(should_call(4,1,1,1000,1400,None))

    def test_never_adds_unrendered_followup_or_exceeds_cap(self):
        self.assertFalse(should_call(500,1,1,1000,1400,object()))
        self.assertFalse(should_call(500,1,12,1000,1400,None))

    def test_incremental_chain_no_old_response_replay_and_bad_anchor_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve()
            (root/'readouts').mkdir()
            (root/'readouts/DO_NOT_OPEN').write_bytes(b'Not part of the TRAIN feed.')
            with StreamJournal(root/'stream',create=True) as journal:
                stream=ContinualStream(TrainHistory(system_prompt='System.',birth_prompt='Birth.'),
                    context_limit=4096,segment_tokens=128,segments_per_sleep=2,deadline_unix=time.time()+30,
                    model_state_sha256='f'*64)
                journal.record('COMMITTED',dict(kind='BIRTH',state=stream.checkpoint()))
                stream.step(lambda *args,**kwargs:dict(raw='repo_read README.md',token_ids=[10,2],terminal=True,truncated=False),
                    lambda messages:sum(len(message['content'].split())+4 for message in messages),journal.record,now=time.time)
                first=collect(root,0,None,None,None)
                self.assertEqual(first['new_responses'],1)
                self.assertEqual(first['events'][0]['actor'],'child')
                second=collect(root,first['cursor'],first['previous'],first['journal_id'],None)
                self.assertEqual(second['new_responses'],0)
                self.assertEqual(second['events'],[])
                with self.assertRaisesRegex(ValueError,'cursor_anchor_changed'):
                    collect(root,first['cursor'],'f'*64,first['journal_id'],None)


if __name__=='__main__':
    unittest.main()
