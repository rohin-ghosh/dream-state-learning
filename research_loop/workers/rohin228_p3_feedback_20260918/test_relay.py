import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from relay import initial_cursor, journal_paths, messages, pending_results
from organism_v6.orch_r124_train_history import TrainEvent
from organism_v6.orch_r125_plain_context import event_message


class FeedbackTests(unittest.TestCase):
    def document(self):
        text = 'A real caption.'
        return dict(origin=dict(record_index=12, record_sha256='a' * 64), raw_act=text,
            report=dict(receipt_sha256='b' * 64, caption_sources=[dict(stage='ACT', start=0,
                end=len(text), text_sha256=hashlib.sha256(text.encode()).hexdigest())], feedback=[
                    dict(caption_source_index=0, contest_id='scene1', result=dict(ok=True,
                        accepted=True, rank=25, reference_count=64, status='new_pixel', replayed=False))]))

    def test_every_result_survives_actual_plain_renderer(self):
        text = messages(self.document())[0]
        event = TrainEvent(event_id='environment:inbox:actual', actor='environment', text='Tool: ' + text,
            split='TRAIN', phase='feedback', episode_id='continual_stream', source_id='/tmp/source.json',
            source_sha256='c' * 64, origin='TRAIN_COLLECTION')
        rendered = event_message(event)
        self.assertEqual(rendered['role'], 'user')
        self.assertIn('Rank 25/65; accepted=true; novelty=new_pixel', rendered['content'])

    def test_unknown_is_explicit_not_silent_or_zero_rank(self):
        document = self.document()
        document['report'] = dict(error='no_caption_found', feedback=[])
        text = messages(document)[0]
        self.assertIn('No judgment: no_caption_found', text)
        self.assertNotIn('Rank 0', text)

    def test_many_captions_are_chunked_without_dropping(self):
        document = self.document()
        document['report']['feedback'] *= 19
        output = messages(document)
        self.assertEqual(len(output), 4)
        self.assertEqual(sum(text.count('Rank 25/65') for text in output), 19)

    def test_tampered_caption_reference_refuses_attribution(self):
        document = self.document()
        document['report']['caption_sources'][0]['text_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'caption_span_hash_mismatch'):
            messages(document)

    def test_journal_backfill_is_bounded_without_loading_old_records(self):
        with tempfile.TemporaryDirectory() as directory:
            life = Path(directory)
            records = life / 'stream/records'
            records.mkdir(parents=True)
            for index in (1, 5000, 5100):
                (records / f'{index:020d}.json').write_text('not loaded')
            (records / '00000000000000000000.intent.json').write_text('not a record')
            self.assertEqual(initial_cursor(life), 4972)
            self.assertEqual(len(journal_paths(life)), 3)

    def test_immutable_results_are_not_reloaded_each_poll(self):
        with tempfile.TemporaryDirectory() as directory:
            session = Path(directory)
            path = session / 'attempts/example/RESULT.json'
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps(dict(unix=1)))
            first = pending_results([session], {})
            processed = {first[0][2]: first[0][3]}
            with patch('relay.load', side_effect=AssertionError('unnecessary reload')):
                self.assertEqual(pending_results([session], processed), [])
            path.write_text(json.dumps(dict(unix=123)))
            with self.assertRaisesRegex(ValueError, 'immutable_result_changed'):
                pending_results([session], processed)


if __name__ == '__main__':
    unittest.main()
