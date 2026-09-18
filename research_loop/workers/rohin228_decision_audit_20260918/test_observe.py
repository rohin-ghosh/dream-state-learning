"""Local projection/expiry checks; no real processes, transport or signals."""

import copy
import datetime
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import observe
import source_adapter
from test_decision_audit import FIXTURE, cycle


class ObserverTests(unittest.TestCase):
    def test_invalid_limits_rejected_before_io(self):
        with self.assertRaisesRegex(ValueError, 'bounded_local_observer_required'):
            observe.run(0, 60)

    def test_source_tail_identity_cannot_be_crossed(self):
        evidence = dict(journal_id='first', head=dict(index=1, sha256='a' * 64))
        batch = dict(journal_id='other', anchor=dict(index=1, sha256='a' * 64))
        with self.assertRaisesRegex(ValueError, 'source_tail_anchor_mismatch'):
            source_adapter.merge(evidence, batch)

    def test_raw_is_written_only_once_and_only_privately(self):
        journal = FIXTURE.Journal()
        cycle(journal, 1, 'PRIVATE_THINK I will continue.', 'Scene 1\nPRIVATE_ACT')
        evidence = journal.evidence()
        report = observe.analyze(evidence, 'SYNTHETIC')
        with tempfile.TemporaryDirectory() as directory:
            own = Path(directory)
            (own / 'private').mkdir()
            seen = set()
            with mock.patch.object(observe, 'OWN', own):
                observe.retain_new_raw('C2', evidence, report, seen)
                observe.retain_new_raw('C2', evidence, report, seen)
            lines = (own / 'private/C2_RAW_DECISION_SOURCES.jsonl').read_text().splitlines()
            self.assertEqual(len(lines), 2)
            self.assertIn('PRIVATE_ACT', '\n'.join(lines))
            self.assertNotIn('PRIVATE_ACT', json.dumps(report))

    def test_follower_expires_at_prior_window_without_restart(self):
        clock = [1000.0]
        journal = FIXTURE.Journal()
        cycle(journal, 1, 'I will continue.', 'Scene 1\nAn observation.')
        evidence = journal.evidence()
        prior = dict(proc_identity_matches=True, status='RUNNING', pid=123, start_ticks=456,
                     expires_utc=datetime.datetime.fromtimestamp(1030, datetime.timezone.utc).isoformat(),
                     last_success_utc={'C2': None, 'P7': None})
        with tempfile.TemporaryDirectory() as directory:
            own = Path(directory)
            for filename in ('decision_audit.py', 'source_adapter.py'):
                (own / filename).write_text('synthetic module bytes')
            def read_source(label):
                clock[0] += 1
                return copy.deepcopy(evidence), dict(observed_utc='1970-01-01T00:33:20+00:00')
            with mock.patch.object(observe, 'OWN', own), \
                    mock.patch.object(observe, 'identity', return_value=dict(pid=321, start_ticks=654, uid=1)), \
                    mock.patch.object(observe, 'prior_watcher_receipt', return_value=prior), \
                    mock.patch.object(observe, 'from_observer', side_effect=read_source), \
                    mock.patch.object(observe.time, 'time', side_effect=lambda: clock[0]), \
                    mock.patch.object(observe.time, 'sleep', side_effect=lambda seconds: clock.__setitem__(0, clock[0] + seconds)):
                observe.run(15, 3600)
            process = json.loads((own / 'operator/PROCESS.json').read_bytes())
            self.assertEqual(process['status'], 'EXPIRED_NORMALLY')
            self.assertEqual(process['expires_utc'], prior['expires_utc'])
            self.assertEqual(process['successful_projections'], {'C2': 2, 'P7': 2})
            self.assertEqual(process['remote_calls'], 0)
            self.assertEqual(process['inbox_writes'], 0)
            self.assertEqual(process['learner_signals'], 0)
            self.assertFalse(process['upstream_restarted'])
            self.assertFalse(process['upstream_expiry_extended'])


if __name__ == '__main__':
    unittest.main()
