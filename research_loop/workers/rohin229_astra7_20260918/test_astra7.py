from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import Mock

from gpu import r229_p7_inbox as inbox
from gpu.orch_r125_stream_journal import StreamJournal
from organism_v6.orch_r124_train_history import TrainHistory
from organism_v6.orch_r125_continual_stream import ContinualStream
from organism_v6.orch_r125_plain_context import VERSION, eligible_rows
from organism_v6.orch_r227_learning_policy import POLICY, recipe_fields


def record(index, kind, document, journal_id=inbox.P7_JOURNAL_ID):
    value = dict(index=index, kind=kind, document=document, journal_id=journal_id)
    value['sha256'] = hashlib.sha256(inbox.canonical(value)).hexdigest()
    return value


def capsule(text='What would you like to investigate?'):
    response = record(10, 'RESPONSE', dict(response=dict(raw=text)))
    stage = record(12, 'R184_STAGE', dict(stage='ACT',
        source_sha256=hashlib.sha256(inbox.canonical(response['document'])).hexdigest()))
    return dict(schema=inbox.SCHEMA, source_response=response, source_stage=stage,
        projection_start=0, projection_end=len(text))


class Astra7InboxTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name) / 'life'
        self.root.mkdir()

    def receipt(self, value=None):
        path = self.root / 'stream/p7_receipts/parent.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(inbox.canonical(capsule() if value is None else value))
        return path

    def test_authentic_projection_and_masked_actual_prefix(self):
        child = ContinualStream(TrainHistory(system_prompt='system', birth_prompt='birth'),
            context_limit=4096, segment_tokens=64, segments_per_sleep=2,
            deadline_unix=time.time()+1000, model_state_sha256='a'*64)
        child.set_presentation(dict(version=VERSION, system_prompt='system', birth_prompt='birth'), 16384)
        with inbox.journal_class(StreamJournal)(self.root/'stream', create=True) as journal:
            journal.record('COMMITTED', dict(state=child.checkpoint()))
            publication = inbox.publish_p7(self.root, self.receipt(), 'What would you like to investigate?')
            incoming = journal.read_inbox()
            self.assertEqual(incoming[0].actor, 'parent')
            self.assertEqual(incoming[0].text, 'P7: What would you like to investigate?')
            self.assertEqual(incoming[0].source_sha256, publication['sha256'])
            generate = Mock(return_value=dict(raw='I will choose my own question.', token_ids=[10,2], terminal=True, truncated=False))
            child.step(generate, lambda messages: sum(len(message['content']) for message in messages), journal.record, incoming=incoming)
            self.assertIn(dict(role='user', content=incoming[0].text), generate.call_args.args[0])
            self.assertIn(dict(role='user', content=incoming[0].text), child.rows[0]['prefix'])
            rendered = child.render(lambda messages: sum(len(message['content']) for message in messages))
            self.assertEqual(set(rendered.labels), {-100})
            self.assertTrue(child.rows[0]['prefix_loss'] is False and child.rows[0]['target_loss'] is True)

    def test_other_human_speakers_and_legacy_parent_rejected(self):
        with inbox.journal_class(StreamJournal)(self.root/'stream', create=True) as journal:
            for speaker in ('Astra','Fable','Rohin','Astra7'):
                message=dict(schema='R127_ATTRIBUTED_INBOX_V1',id='one',actor='parent',split='TRAIN',speaker=speaker,text='external',source_receipt=None)
                with self.subTest(speaker=speaker), self.assertRaises(ValueError):
                    journal._inbox_event(message,str(journal.inbox/'one.json'),'a'*64)
            with self.assertRaises(ValueError):
                journal._inbox_event(dict(id='one',actor='parent',split='TRAIN',text='legacy'),str(journal.inbox/'one.json'),'a'*64)

    def test_original_human_whitelist_unchanged(self):
        with StreamJournal(self.root/'stream', create=True) as journal:
            for speaker in ('Astra','Fable','Rohin'):
                message=dict(schema='R127_ATTRIBUTED_INBOX_V1',id='one',actor='parent',split='TRAIN',speaker=speaker,text='hello',source_receipt=None)
                self.assertEqual(journal._inbox_event(message,str(journal.inbox/'one.json'),'a'*64).actor,'parent')
            message['speaker']='P7'
            with self.assertRaises(ValueError): journal._inbox_event(message,str(journal.inbox/'one.json'),'a'*64)

    def test_spoofed_identity_stage_hash_and_projection_rejected(self):
        for mutation in ('journal','response_hash','stage_hash','stage_kind','projection','empty','rewritten'):
            value=capsule(); text='What would you like to investigate?'
            if mutation=='journal': value['source_response']['journal_id']='a'*32
            elif mutation=='response_hash': value['source_response']['sha256']='b'*64
            elif mutation=='stage_hash': value['source_stage']['document']['source_sha256']='c'*64
            elif mutation=='stage_kind': value['source_stage']=record(12,'R184_STAGE',dict(stage='THINK',source_sha256=hashlib.sha256(inbox.canonical(value['source_response']['document'])).hexdigest()))
            elif mutation=='projection': value['projection_start']=1
            elif mutation=='empty': value['projection_end']=0
            else: text='An operator invented this instruction.'
            with self.subTest(mutation=mutation), self.assertRaises(ValueError): inbox.validate_capsule(value,text)

    def test_receipt_file_tamper_rejected(self):
        with inbox.journal_class(StreamJournal)(self.root/'stream',create=True) as journal:
            path=self.receipt(); inbox.publish_p7(self.root,path,'What would you like to investigate?')
            path.write_bytes(path.read_bytes()+b' ')
            with self.assertRaises(ValueError): journal.read_inbox()

    def test_r227_preserves_own_rows_and_external_prefix(self):
        rows=[dict(source_sha256='a'*64,target='source_sha256 meta 中文 Ａ',prefix=[dict(role='system',content='system'),dict(role='user',content='birth'),dict(role='user',content='P7: A parent question')])]
        accepted,excluded=eligible_rows(rows,dict(version=VERSION,system_prompt='system',birth_prompt='birth'),exclude_scaffolding=False)
        self.assertEqual(excluded,[])
        self.assertEqual(accepted[0]['target'],rows[0]['target'])
        self.assertEqual(accepted[0]['prefix'][-1],rows[0]['prefix'][-1])
        self.assertEqual(recipe_fields(dict(learn_row_policy=POLICY))['active_semantic_filters'],[])


if __name__=='__main__':
    unittest.main()
