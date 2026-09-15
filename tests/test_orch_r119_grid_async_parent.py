import json
from pathlib import Path
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from gpu import orch_r119_grid_async_parent as subject
from gpu import orch_r115_grid_native as native


class AsyncParentTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / 'parent_queue').mkdir()
        (self.root / 'LEDGER.jsonl').write_text('')
        native.write(self.root / 'BROKER_CONFIG.json', {})
        outer = self

        class BaseLife:
            def __init__(self, root, engine, config, cycle):
                self.root, self.config, self.cycle = root, config, cycle
                self.events = []
                self.settings = {'effective_max_new_tokens': 1024}

            def event(self, *values):
                self.events.append(values)

            def calls(self, tasks, purpose, messages, cap, attached_readout=False):
                outer.calls.append(dict(messages=messages, cap=cap))
                return [dict(reference=dict(path='new_TRAIN_call', sha256='a' * 64))]

        def reserve(root, kind, detail):
            rows = [json.loads(line) for line in (root/'LEDGER.jsonl').read_text().splitlines()]
            number = 41 + len(rows)
            with (root/'LEDGER.jsonl').open('a') as stream:
                stream.write(json.dumps(dict(kind=kind, number=number, reserved_unix=time.time(), **detail))+'\n')
            return number

        self.calls = []
        self.grid = SimpleNamespace(Life=BaseLife, read=native.read, write=native.write, ref=native.ref,
            require=native.require, reserve=reserve, TRAIN_END=time.time()+1000, END=time.time()+2000,
            policy=SimpleNamespace(queue_request=lambda identifier,*args: dict(id=identifier, lane_deadline_unix=time.time()+120),
                previous=SimpleNamespace(parent_disposition=lambda request,response,now,model:
                    dict(status='COMPLETE' if response else 'MISSING',guidance=response.get('guidance') if response else None))),
            reflection_settings=lambda response,request,config: dict(status='BOUND_FOR_LANE_DECODER',effective_max_new_tokens=128))
        self.life=subject.life_class(self.grid,'era')(self.root,None,dict(life_id='life',cohort_sha256='b'*64,parent_model='parent'),9)
        self.task=dict(id='TRAIN',split='TRAIN')

    def test_pending_parent_never_sleeps_or_blocks_child(self):
        with patch.object(subject.time,'sleep',side_effect=AssertionError('no_wait')):
            result=self.life.ask(self.task,0,'experience')
            self.assertEqual(result['disposition']['status'],'PENDING')
            self.life.calls([self.task],'episode',[[dict(role='user',content='act')]],128)
        self.assertEqual(len(self.calls),1)
        self.assertFalse((self.root/'parent_received/P0041.json').exists())

    def test_pending_backpressure_no_duplicate_charges(self):
        self.life.ask(self.task,0,'experience')
        result=self.life.ask(self.task,1,'open_turn')
        self.assertTrue(result['backlog_backpressure'])
        self.assertEqual(len((self.root/'LEDGER.jsonl').read_text().splitlines()),1)

    def test_reply_injected_once_next_actual_call(self):
        self.life.ask(self.task,0,'experience')
        native.write(self.root/'parent_queue/P0041.response.json',dict(guidance='Try checking your last move.',finished_unix=time.time()))
        self.life.calls([self.task],'reflection',[[dict(role='user',content='reflect')]],1024)
        self.assertEqual(self.calls[0]['cap'],128)
        self.assertIn('Try checking',self.calls[0]['messages'][0][-1]['content'])
        self.life.calls([self.task],'episode',[[dict(role='user',content='act')]],128)
        self.assertEqual(len(self.calls[1]['messages'][0]),1)
        self.assertTrue((self.root/'era/parent_applied/P0041.json').exists())

    def test_readout_never_reads_mailbox(self):
        with self.assertRaisesRegex(ValueError,'never_DEV_FINAL'):
            self.life.calls([dict(id='HELD',split='FINAL')],'final',[],128,attached_readout=True)

    def test_expired_missing_does_not_stop_life(self):
        self.life.ask(self.task,0,'experience')
        path=self.root/'parent_queue/P0041.request.json'
        request=native.read(path); request['lane_deadline_unix']=0
        native.write(path,request,replace=True)
        self.life.calls([self.task],'episode',[[dict(role='user',content='act')]],128)
        self.assertEqual(native.read(self.root/'parent_received/P0041.json')['disposition']['status'],'MISSING')
        self.assertEqual(len(self.calls),1)


if __name__ == '__main__':
    unittest.main()
