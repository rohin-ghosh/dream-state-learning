import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import curriculum_parent as curriculum


def state(**changes):
    legacy = dict(completed_cycle=76, record_cursor=1500, pending=None, step=2)
    legacy.update(changes)
    return curriculum.initial_state(legacy)


class CurriculumTests(unittest.TestCase):
    def test_persistent_recall_has_no_one_or_two_attempt_cap(self):
        current = state()
        seen = []
        for number in range(36):
            topic = curriculum.choose_topic(current)
            seen.append(topic)
            current['topic_index'] += 1
            current['pending'] = dict(topic=topic, render={'index': number})
            curriculum.acknowledge(current, {'awake_cycle': current['completed_cycle'] + 1})
            self.assertIsNone(curriculum.choose_topic(current))
            current['completed_cycle'] += 1
        self.assertEqual(seen.count('recall'), 18)
        self.assertEqual(set(seen), set(curriculum.TOPICS))
        self.assertTrue(current['unresolved_recall'])

    def test_one_outstanding_and_no_duplicate_cycle(self):
        current = state(pending={'text': 'already waiting'})
        self.assertIsNone(curriculum.choose_topic(current))
        current['pending'] = None
        current['last_publication_cycle'] = 76
        self.assertIsNone(curriculum.choose_topic(current))

    def test_adopts_pending_and_preserves_new_topic_order(self):
        pending = dict(action='reading', text='existing prompt', render={'index': 1490})
        current = state(pending=pending)
        self.assertIs(current['pending'], pending)
        self.assertTrue(current['inherited_pending'])
        curriculum.acknowledge(current, {'awake_cycle': 77})
        self.assertEqual(current['reading_step'], 3)
        self.assertEqual(current['topic_index'], 0)
        self.assertFalse(current['inherited_pending'])

    def test_response_needs_render(self):
        current = state(pending=dict(topic='recall', render=None))
        with self.assertRaisesRegex(ValueError, 'actual_render'):
            curriculum.acknowledge(current, {'awake_cycle': 77})

    def test_reading_wraps_six_steps_not_semantic_selection(self):
        current = state(step=5, pending=dict(topic='reading', render={'index': 7}))
        curriculum.acknowledge(current, {'awake_cycle': 77})
        self.assertEqual(current['reading_step'], 0)

    def test_recall_contains_no_story_answer_and_no_required_schema(self):
        excerpts = curriculum.protocol(Path(__file__).with_name('PROTOCOL.md'))
        text = curriculum.prompt('recall', 0, excerpts)
        self.assertNotIn(excerpts[0], text)
        for fact in ('Iona', 'horse', 'son died', 'Petersburg'):
            self.assertNotIn(fact, text)
        self.assertIn('do not remember', text)
        self.assertIn('still see in context', text)
        self.assertIn('your own situation', text)
        self.assertIn('not asking for fixed headings', text)
        self.assertIn(excerpts[0], curriculum.prompt('reading', 0, excerpts))

    def test_paper_does_not_assert_unseen_findings_or_adapter_causality(self):
        self.assertIn('Do not invent', curriculum.QUESTIONS['paper'])
        self.assertIn('guesses', curriculum.QUESTIONS['science'])
        self.assertNotIn('drift is evidence', ' '.join(curriculum.QUESTIONS.values()))

    def test_observations_are_read_only_not_exclusions_or_advancement(self):
        raw = 'public fixture 中文'
        observed = curriculum.observations(raw, {'raw_sha256': curriculum.sha(raw.encode())})
        self.assertTrue(observed['cjk_kana_hangul_observed'])
        self.assertTrue(observed['exactly_repeated_previous_response'])
        self.assertFalse(observed['semantic_exclusion'])
        self.assertFalse(observed['learning_gate'])
        self.assertFalse(observed['raw_modified'])
        self.assertIsNone(observed['stage_transition'])
        self.assertEqual(observed['content_vs_intention'], 'manual_review_required')
        self.assertNotIn(raw, json.dumps(observed))
        text = curriculum.prompt('recall', 0, [], {'observations': observed})
        self.assertIn('previous reply included', text)
        self.assertIn('exactly repeated', text)
        self.assertNotIn('中文', text)
        self.assertIn('Answer the question itself', text)

    def test_actual_inbox_exact_request_and_loss_mask_binding(self):
        pending = dict(text='test question', publication=dict(id='example', sha256='source'))
        inbox = dict(kind='INBOX', index=10, sha256='inbox', document=dict(source_sha256='source',
            message=dict(id='example', text='test question', speaker='Astra', actor='parent', source_receipt=None)))
        request = dict(kind='REQUEST', index=11, sha256='request', document=dict(started_unix=1789724000,
            prompt_tokens=500, messages=[dict(content='Astra: test question')],
            resume_state={'state': {'sleep_receipts': [{'cycle': 77}]}},
            render_receipt=dict(all_history_tokens_masked=True)))
        self.assertIsNone(curriculum.request_receipt(pending, request, 'story fixture'))
        curriculum.capture_inbox(pending, inbox)
        receipt = curriculum.request_receipt(pending, request, 'story fixture')
        self.assertEqual(receipt['document_sha256'], curriculum.sha(curriculum.canonical(request['document'])))
        self.assertTrue(receipt['all_history_tokens_masked'])
        self.assertFalse(receipt['exact_story_visible'])
        self.assertNotIn('test question', json.dumps(receipt))
        request['document']['render_receipt']['all_history_tokens_masked'] = False
        with self.assertRaisesRegex(ValueError, 'external_parent_tokens_masked'):
            curriculum.request_receipt(pending, request, 'story fixture')

    def test_response_request_digest_excludes_journal_resume_state(self):
        pending = dict(text='question', inbox={'index': 10})
        document = dict(started_unix=1789724000, prompt_tokens=500, messages=[dict(content='question')],
            render_receipt=dict(all_history_tokens_masked=True))
        source_digest = curriculum.sha(curriculum.canonical(document))
        document['resume_state'] = dict(state={'pending': source_digest, 'sleep_receipts': [{'cycle': 77}]}, sha256='fixture state')
        record = dict(kind='REQUEST', index=11, sha256='record', document=document)
        receipt = curriculum.request_receipt(pending, record, 'story fixture')
        self.assertEqual(receipt['request_sha256'], source_digest)
        self.assertNotEqual(receipt['document_sha256'], source_digest)
        self.assertEqual(receipt['awake_cycle'], 78)
        document['resume_state']['state']['unrelated_journal_metadata'] = True
        self.assertEqual(curriculum.request_receipt(pending, record, 'story fixture')['request_sha256'], source_digest)

    def test_rejects_inbox_tampering_and_preexisting_request(self):
        pending = dict(text='real', publication=dict(id='example', sha256='source'))
        inbox = dict(kind='INBOX', index=10, sha256='inbox', document=dict(source_sha256='source',
            message=dict(id='example', text='altered', speaker='Astra', actor='parent', source_receipt=None)))
        with self.assertRaisesRegex(ValueError, 'exact_parent_inbox'):
            curriculum.capture_inbox(pending, inbox)
        pending['inbox'] = {'index': 10}
        self.assertIsNone(curriculum.request_receipt(pending, dict(kind='REQUEST', index=9), 'story'))

    def test_completed_checkpoint_binding_and_tamper_detection(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            directory = root/'raw/checkpoints/sleep_000076'
            (directory/'adapter').mkdir(parents=True)
            (directory/'adapter/adapter_model.safetensors').write_bytes(b'public development fixture')
            (directory/'optimizer_rng.pt').write_bytes(b'fixture optimizer and RNG')
            adapter_hash = curriculum.file_hash(directory/'adapter/adapter_model.safetensors')
            optimizer_hash = curriculum.file_hash(directory/'optimizer_rng.pt')
            hashes = dict(optimizer=optimizer_hash, rng=optimizer_hash)
            commit = dict(checkpoint_sha256=hashes, optimizer_steps=5548, adapter_state_sha256='fixture',
                created_unix=1789724000, adapter_files={'adapter_model.safetensors': adapter_hash})
            (directory/'COMMIT.json').write_text(json.dumps(commit))
            resume = dict(state={'working': 'public fixture'}, sha256=curriculum.sha(curriculum.canonical({'working': 'public fixture'})))
            record = dict(kind='SLEEP_COMPLETE', index=1469, sha256='fixture record', document=dict(
                status='COMPLETE', cycle=76, checkpoint_sha256=hashes, total_optimizer_steps=5548, resume_state=resume))
            receipt = curriculum.checkpoint_reference(record, root)
            self.assertEqual(receipt['files']['optimizer_rng.pt'], optimizer_hash)
            self.assertEqual(receipt['learner_controls'], 0)
            altered = copy.deepcopy(record)
            altered['document']['total_optimizer_steps'] += 1
            with self.assertRaisesRegex(ValueError, 'record_commit_binding'):
                curriculum.checkpoint_reference(altered, root)
            altered = copy.deepcopy(record)
            altered['document']['resume_state']['state']['working'] = 'changed'
            with self.assertRaisesRegex(ValueError, 'resume_state_hash'):
                curriculum.checkpoint_reference(altered, root)
            (directory/'optimizer_rng.pt').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'optimizer_rng_payload_hash'):
                curriculum.checkpoint_reference(record, root)


if __name__ == '__main__':
    unittest.main()
