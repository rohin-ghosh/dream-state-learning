import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from gpu import orch_math_pipeline_l2_r104_audit as audit
from organism_v6 import orch_math_pipeline_l2 as policy


class R104AuditTest(unittest.TestCase):
    def write(self, path, data):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data))

    def fixture(self, campaign):
        output = campaign / 'GUIDED_SLEEP/cycle1/experience'
        episode = dict(task=dict(id='TRAIN_FAILURE', question='1+1?'), trace='FINAL: 3',
            outcome=dict(status='INCORRECT', correct=False))
        self.write(output / 'EPISODE_00.json', episode)
        rows, losses = [], []
        for position, kind in enumerate(('past_attempt', 'past_reflection')):
            target = episode['trace'] if kind == 'past_attempt' else 'My past answer was incorrect.'
            call = dict(task_id='TRAIN_FAILURE', response=dict(raw=target))
            source = output / f'CALL_{position:04d}.json'
            self.write(source, call)
            rows.append(dict(episode_id='TRAIN_FAILURE', kind=kind, outcome='INCORRECT',
                target=target, target_sha256=hashlib.sha256(target.encode()).hexdigest(),
                source_call_path=str(source.relative_to(campaign)), source_call_sha256=audit.sha(source),
                student_prefix=policy.historical_prefix(episode, kind), teacher_in_prefix=False,
                observed_fact_endorsement=False, actual_presentations=1))
            self.write(output / f'MASK_00_{kind}.json', dict(input_ids=[1, 2, 3],
                labels=[-100, 2, 3], target_ids=[2, 3]))
            losses.append(dict(source=dict(episode_id='TRAIN_FAILURE', kind=kind)))
        self.write(output / 'ROWS.json', rows)
        self.write(output / 'COMPLETE.json', dict(status='COMPLETE'))
        (output / 'LOSSES.jsonl').write_text(''.join(json.dumps(loss)+'\n' for loss in losses))
        return output, rows

    def test_negative_attempt_and_reflection_both_verified(self):
        with tempfile.TemporaryDirectory() as directory:
            campaign = Path(directory)
            output, rows = self.fixture(campaign)
            result = audit.coverage(campaign, output)
            self.assertEqual(result['negative_episodes'], 1)
            self.assertEqual(len(result['verified_rows']), 2)
            self.assertTrue(all(row['outcome'] == 'INCORRECT' for row in result['verified_rows']))

    def test_relabel_or_drop_negative_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            campaign = Path(directory)
            output, rows = self.fixture(campaign)
            rows[0]['outcome'] = 'CORRECT'
            self.write(output / 'ROWS.json', rows)
            with self.assertRaises(AssertionError):
                audit.coverage(campaign, output)
            self.write(output / 'ROWS.json', rows[1:])
            with self.assertRaises(AssertionError):
                audit.coverage(campaign, output)

    def test_source_hash_tampering_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            campaign = Path(directory)
            output, rows = self.fixture(campaign)
            self.write(campaign / rows[0]['source_call_path'], dict(response=dict(raw='changed')))
            with self.assertRaises(AssertionError):
                audit.verify_source(campaign, rows[0])

    def test_off_never_borrows_guided_parent_timing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            campaign = root / 'campaign_test'
            output = campaign / 'UNPARENTED_SLEEP/cycle1/experience'
            self.write(output / 'REQUEST.json', dict(started_unix=10))
            transcript = root / 'parent_transcripts/campaign_test/GUIDED_SLEEP_C1'
            self.write(transcript / 'INVOCATION.json', dict(started_unix=11,
                provider='EXISTING_VERIFIED_PRIMARY_RESPONSES'))
            self.write(transcript / 'COMPLETE.json', dict(finished_unix=15))
            result = audit.timing(campaign, output, 20)
            self.assertIsNone(result['parent_http_wall_seconds'])


if __name__ == '__main__':
    unittest.main()
