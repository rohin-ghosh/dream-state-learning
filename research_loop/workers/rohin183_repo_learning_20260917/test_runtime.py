import errno
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from gpu.orch_r125_stream_journal import StreamJournal
from organism_v6.orch_r124_train_history import TrainHistory
from organism_v6.orch_r125_continual_stream import ContinualStream
from research_loop.workers.rohin183_repo_learning_20260917 import broker,confinement
from research_loop.workers.rohin183_repo_learning_20260917.safe_snapshot import write,digest


class RuntimeTests(unittest.TestCase):
    def test_device_policy_accepts_only_target_and_permission_denials(self):
        closed=[]
        def opener(path,flags):
            if path not in ('/dev/nvidia2','/dev/nvidiactl','/dev/nvidia-uvm'):
                raise OSError(errno.EPERM,'fixture denial')
            return 17
        proof=confinement.device_checks(opener,closed.append)
        self.assertEqual(proof['denied_foreign_minors'],[0,1,3,4,5,6,7])
        self.assertEqual(closed,[17,17,17])

    def test_foreign_open_is_closed_then_rejected(self):
        closed=[]
        with self.assertRaisesRegex(ValueError,'foreign_GPU_open_abort'):
            confinement.device_checks(lambda path,flags: 19,closed.append)
        self.assertEqual(closed,[19])

    def test_missing_devices_do_not_count_as_confinement(self):
        def missing(path,flags):
            raise OSError(errno.ENOENT,'missing fixture')
        with self.assertRaisesRegex(ValueError,'actual_foreign_device_denial'):
            confinement.device_checks(missing,lambda descriptor: None)

    def test_real_incremental_response_causes_actual_read_and_attributed_inbox(self):
        with tempfile.TemporaryDirectory() as temporary:
            base=Path(temporary).resolve()
            root=base/'life'
            root.mkdir()
            reference=write(base/'snapshot/README.md',b'Actual local fixture bytes.')
            manifest=write(base/'manifest.json',dict(schema='R183_SAFE_WORKING_TREE_SNAPSHOT_V1',
                files={'README.md':{key:reference[key] for key in ('bytes','sha256')}}))
            config=dict(schema='R183_REPO_TOOLS_V1',root=str(root),workspace=str(base/'workspace'),
                snapshot=str(base/'snapshot'),snapshot_manifest=manifest,receipts=str(base/'receipts'),hard_end_unix=time.time()+30)
            path=base/'config.json'
            write(path,config)
            with StreamJournal(root/'stream',create=True) as journal:
                stream=ContinualStream(TrainHistory(system_prompt='System.',birth_prompt='Birth.'),
                    context_limit=4096,segment_tokens=128,segments_per_sleep=2,deadline_unix=time.time()+30,
                    model_state_sha256='f'*64)
                journal.record('COMMITTED',dict(kind='BIRTH',state=stream.checkpoint()))
                stream.step(lambda *args,**kwargs:dict(raw='repo_read README.md',token_ids=[10,2],terminal=True,truncated=False),
                    lambda messages:sum(len(message['content'].split())+4 for message in messages),journal.record,now=time.time)
                with patch.object(broker.tools,'ACTION_LIMIT',1):
                    broker.serve(path)
                action=json.loads((base/'receipts/ACTION_000000.json').read_bytes())
                self.assertEqual(action['content'],'Actual local fixture bytes.')
                self.assertEqual(action['origin']['split'],'TRAIN')
                self.assertEqual(action['origin']['actor'],'child')
                incoming=journal.read_inbox()
                self.assertEqual(len(incoming),1)
                self.assertEqual(incoming[0].actor,'environment')
                self.assertEqual(incoming[0].phase,'feedback')
                self.assertEqual(incoming[0].split,'TRAIN')
                self.assertTrue((base/'receipts/PUBLICATION_000000.json').is_file())
                with self.assertRaisesRegex(ValueError,'once_only_broker'):
                    broker.serve(path)


if __name__=='__main__':
    unittest.main()
