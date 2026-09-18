"""Incremental identity/expiry regression tests; no real transport or signals."""

import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import observe
from test_audit import fixture


class ObserverTests(unittest.TestCase):
    def base(self):
        evidence = fixture().evidence()
        evidence['journal_id'] = 'synthetic-journal'
        evidence['continuity'] = []
        evidence['head']['journal_id'] = evidence['journal_id']
        return evidence

    def tail(self, evidence):
        anchor = copy.deepcopy(evidence['head'])
        return dict(journal_id=evidence['journal_id'], anchor=anchor, through=copy.deepcopy(anchor),
                    remote_head=copy.deepcopy(anchor), continuity=[], events=[], observed_unix=2001.0)

    def test_empty_tail_preserves_rows_and_moves_observation_time(self):
        evidence = self.base()
        before = copy.deepcopy(evidence)
        merged = observe.merge_tail(evidence, self.tail(evidence))
        self.assertEqual(merged['events'], evidence['events'])
        self.assertEqual(evidence, before)
        self.assertEqual(merged['observed_unix'], 2001.0)

    def test_wrong_anchor_or_other_journal_rejected(self):
        evidence = self.base()
        for key in ('journal_id', 'sha256'):
            batch = self.tail(evidence)
            if key == 'journal_id':
                batch[key] = 'other-journal'
            else:
                batch['anchor'][key] = 'a' * 64
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'tail_does_not_extend_exact_cut'):
                observe.merge_tail(evidence, batch)

    def test_event_not_in_tail_chain_rejected(self):
        evidence = self.base()
        batch = self.tail(evidence)
        batch['events'] = [evidence['events'][0]]
        with self.assertRaisesRegex(ValueError, 'tail_event_identity_mismatch'):
            observe.merge_tail(evidence, batch)

    def test_new_chain_metadata_preserves_partial_generation_without_counting_it(self):
        evidence = self.base()
        batch = self.tail(evidence)
        meta = dict(index=evidence['head']['index'] + 1, sha256='a' * 64,
                    previous_sha256=evidence['head']['sha256'], journal_id=evidence['journal_id'], kind='GENERATION_PARTIAL')
        batch['continuity'] = [meta]
        batch['through'] = meta
        batch['remote_head'] = meta
        merged = observe.merge_tail(evidence, batch)
        self.assertEqual(merged['events'], evidence['events'])
        self.assertEqual(merged['head']['index'], meta['index'])

    def test_invalid_observer_budget_rejected_before_io(self):
        with self.assertRaisesRegex(ValueError, 'bounded_observer_configuration_required'):
            observe.run({}, 0, 3600, 256)

    def test_finite_observer_expires_with_sanitized_identity_and_no_signals(self):
        clock = [1000.0]
        evidence = self.base()
        with tempfile.TemporaryDirectory() as directory:
            own = Path(directory)
            (own / 'private').mkdir()
            (own / 'audit.py').write_text('synthetic source fixture')
            initial = own / 'private/source.json'
            initial.write_text(json.dumps(evidence))
            def read_batch(label, cursor, limit, remaining):
                clock[0] += 1
                batch = self.tail(evidence)
                batch['observed_unix'] = clock[0]
                return batch, dict(batch_file_sha256='a' * 64)
            def sleep(seconds):
                clock[0] += seconds
            with mock.patch.object(observe, 'OWN', own), mock.patch.object(observe, 'read_batch', side_effect=read_batch), \
                    mock.patch.object(observe, 'process_identity', return_value=dict(pid=123, start_ticks=456, uid=789)), \
                    mock.patch.object(observe.time, 'time', side_effect=lambda: clock[0]), \
                    mock.patch.object(observe.time, 'sleep', side_effect=sleep):
                observe.run({'C2': initial}, 15, 30, 32)
            process = json.loads((own / 'operator/PROCESS.json').read_bytes())
            self.assertEqual(process['status'], 'EXPIRED_NORMALLY')
            self.assertEqual(process['successful_polls']['C2'], 2)
            self.assertEqual(process['child_signals'], 0)
            self.assertEqual(process['parent_messages'], 0)
            self.assertNotIn(str(initial), json.dumps(process))
            self.assertTrue((own / 'operator/C2_LATEST.json').exists())


if __name__ == '__main__':
    unittest.main()
