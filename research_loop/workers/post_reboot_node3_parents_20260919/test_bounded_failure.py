"""No bound bypass, ancestry loss, fake judgment, or duplicate error publication."""

from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parent))
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
import bounded_failure as failure
from gpu.orch_r125_stream_journal import _digest
from gpu.ny_caption_life import child_act, latest_own_think
from research_loop.workers.rohin221_continuous_caption_20260918 import journal_transport


def actual_chain(root):
    directory=root/'stream/records'
    directory.mkdir(parents=True)
    think=dict(response=dict(raw='Scene1: "A literal THINK caption."'))
    act=dict(response=dict(raw='unclear ACT'))
    documents=[('RESPONSE',think),('COMMITTED',dict(source_sha256=_digest(think),state='kept'*200)),
        ('R184_STAGE',dict(stage='THINK',source_sha256=_digest(think))),
        ('CONTEXT_INPUT',dict(state='kept'*200)),('REQUEST',dict(state='kept'*200)),
        ('RESPONSE',act),('COMMITTED',dict(source_sha256=_digest(act),state='kept'*200)),
        ('R184_STAGE',dict(stage='ACT',source_sha256=_digest(act)))]
    previous='seed'
    for index,(kind,document) in enumerate(documents):
        value=dict(index=index,journal_id='journal',kind=kind,document=document,previous_sha256=previous)
        value['sha256']=_digest(value)
        (directory/f'{index:020d}.json').write_text(json.dumps(value))
        previous=value['sha256']
        if index==5:origin=dict(kind='TRAIN_CHILD_RESPONSE',record_index=index,record_sha256=previous)
    return origin


class BoundedFailureTests(unittest.TestCase):
    def test_minimal_window_retains_all_original_ACT_THINK_records(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            origin=actual_chain(root)
            window=failure.minimal_window(root,origin,'journal')
            self.assertEqual([row['index'] for row in window['records']],list(range(8)))
            self.assertEqual(window['THINK']['record_index'],0)
            self.assertEqual(window['total_bytes'],sum(path.stat().st_size for path in (root/'stream/records').iterdir()))
            self.assertEqual(child_act(root,origin),'unclear ACT')
            self.assertIn('literal THINK',latest_own_think(root,origin)['raw'])

    def test_smaller_window_or_hole_breaks_required_source_proof(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            origin=actual_chain(root)
            for index in range(8):
                path=root/'stream/records'/f'{index:020d}.json'
                parked=path.with_suffix('.parked')
                path.rename(parked)
                with self.assertRaises((ValueError,OSError)):
                    failure.minimal_window(root,origin,'journal')
                parked.rename(path)

    def test_total_bound_is_reported_not_raised_or_bypassed(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            origin=actual_chain(root)
            with patch.object(failure,'MAX_TOTAL_BYTES',100),patch.object(journal_transport,'MAX_TOTAL_BYTES',100):
                with self.assertRaisesRegex(ValueError,'bounded_total_journal'):
                    journal_transport.export_chunks(root,origin,'journal')
                window=failure.minimal_window(root,origin,'journal')
                self.assertTrue(window['exceeds_bound'])
                self.assertFalse(window['repairable_by_smaller_contiguous_window'])
                self.assertTrue(window['no_export_or_scoring_performed'])
            self.assertEqual(failure.MAX_TOTAL_BYTES,67108864)
            self.assertEqual(journal_transport.MAX_TOTAL_BYTES,67108864)

    def test_foreign_journal_and_modified_original_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            origin=actual_chain(root)
            with self.assertRaisesRegex(ValueError,'journal_hash'):
                failure.minimal_window(root,origin,'foreign')
            path=root/'stream/records/00000000000000000003.json'
            value=json.loads(path.read_bytes());value['document']['state']='changed'
            path.write_text(json.dumps(value))
            with self.assertRaises(ValueError):failure.minimal_window(root,origin,'journal')

    def test_executed_native_RPC_does_not_mean_scorer_dispatch(self):
        origin=dict(kind='TRAIN_CHILD_RESPONSE',record_index=5,record_sha256='a'*64)
        transport=dict(origin=origin,dispatched=False,receipt_sha256=None,
            error='ORIGIN_TRANSPORT_NOT_DISPATCHED',error_type='CalledProcessError')
        environment=dict(origin=origin,report=dict(error=transport['error'],error_type=transport['error_type'],feedback=[]))
        act=dict(kind='R184_ACT',journal_id='journal',document=dict(origin=origin,outcome=dict(executed=True,environment=environment)))
        failure.validate_failure(transport,act,'journal')
        with self.assertRaises(ValueError):failure.validate_failure(dict(transport,dispatched=True),act,'journal')
        changed=deepcopy(act);changed['document']['outcome']['environment']['receipt_sha256']='real'
        with self.assertRaises(ValueError):failure.validate_failure(transport,changed,'journal')

    def test_error_text_is_not_a_fake_score_or_task(self):
        text=failure.message(dict(record_index=5,record_sha256='a'*64),dict(exceeds_bound=True,total_bytes=70000000))
        self.assertIn('No judgment:',text)
        self.assertIn('scorer was not contacted',text)
        self.assertIn('No rank, acceptance decision, or zero score exists',text)
        self.assertNotIn('accepted=',text)
        with self.assertRaises(ValueError):
            failure.message(dict(record_index=5,record_sha256='a'*64),dict(exceeds_bound=False))

    def test_stale_partial_never_blocks_immutable_recovery(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'projection.json'
            path.with_suffix('.pending').write_text('incomplete earlier attempt')
            failure.immutable(path,dict(actual='projection'))
            failure.immutable(path,dict(actual='projection'))
            with self.assertRaises(ValueError):failure.immutable(path,dict(actual='changed'))

    def test_publication_retry_uses_same_inbox_and_no_scorer_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'stream/inbox').mkdir(parents=True)
            output=root/'operational'
            projection=dict(origin=dict(record_index=5,record_sha256='a'*64),
                ACT_record=dict(index=8,path=str(root/'stream/records/00000000000000000008.json'),sha256='b'*64),
                text='No judgment: operational export limit; the scorer was not contacted.')
            def publish(life,speaker,text,source):
                path=life/'stream/inbox/test.json'
                path.write_text(json.dumps(dict(id='id',speaker=speaker,text=text,actor='environment',source_receipt=source)))
                return dict(id='id',path=str(path),sha256=failure.digest_bytes(path.read_bytes()))
            with patch('gpu.orch_r127_pilot_console._inbox',side_effect=publish) as inbox:
                first=failure.publish_once(root,output,projection)
                second=failure.publish_once(root,output,projection)
                self.assertEqual(first,second)
                self.assertEqual(inbox.call_count,1)
                self.assertFalse(first['scorer_receipt'])
                self.assertEqual(first['target_rows_written'],0)
                next(output.glob('*.published.json')).unlink()
                third=failure.publish_once(root,output,projection)
                self.assertEqual(inbox.call_count,1)
                self.assertTrue(third['recovered_existing_inbox'])

    def test_native_inbox_metadata_at_tail_proves_actual_consumption(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root/'stream/inbox').mkdir(parents=True)
            (root/'stream/records').mkdir()
            inbox_path=root/'stream/inbox/item.json'
            inbox_path.write_text(json.dumps(dict(id='item',text='No judgment.')))
            projection=root/'projection.json';projection.write_text('{}')
            saved=dict(publication=dict(id='item',path=str(inbox_path),sha256=failure.digest_bytes(inbox_path.read_bytes())),
                source_receipt=dict(path=str(projection),sha256=failure.digest_bytes(projection.read_bytes())),ACT_record=dict(index=8))
            native=dict(index=9,journal_id='journal',kind='INBOX',previous_sha256='prior',
                document=dict(message=dict(id='item',text='message'*2000),source_sha256=saved['publication']['sha256']))
            native['sha256']=_digest(native)
            path=root/'stream/records/00000000000000000009.json'
            path.write_text(json.dumps(native,sort_keys=True,separators=(',',':')))
            result=failure.receipt(root,saved,'journal')
            self.assertEqual(result['INBOX']['index'],9)
            self.assertEqual(result['status'],'OPERATIONAL_ERROR_INBOX_VERIFIED')


if __name__=='__main__':
    unittest.main()
