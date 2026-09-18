"""CPU regressions for the scoped saved-boundary repair and truthful receipts."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import r209_filter_resume as repair
from r209_node3_audit import metadata, read_record


class RepairTests(unittest.TestCase):
    def test_R210_changes_phase_cap_but_never_rate_or_wall(self):
        previous = dict(source_root='/old/source', startup_context=dict(path='/old/source/context/START.md'),
            think_act_learn=dict(prose_target_filter='OLD', environment_facts='OLD', trial_id='SAME'),
            max_sleeps=57, hard_end_unix=123, learning_rate=3e-5, new_presentations=32,
            rehearsal_presentations=0, anchor_lambda=.25, learning_rate_multiplier=.3)
        result = repair.proposed_plan(previous, Path('/new/source'), enrich=True)
        self.assertIsNone(result['max_sleeps'])
        self.assertEqual(previous['max_sleeps'], 57)
        for key in ('hard_end_unix', 'learning_rate', 'new_presentations', 'rehearsal_presentations',
                'anchor_lambda', 'learning_rate_multiplier'):
            self.assertEqual(result[key], previous[key])

    def test_R210_peer_capsule_is_bound_unverified_context(self):
        from r210_node3_runtime import capsule
        def bound(record):
            record['sha256'] = hashlib.sha256(json.dumps(record, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
            return record
        response = bound(dict(kind='RESPONSE', index=2, document=dict(response=dict(raw='Own prose 中文'))))
        act = bound(dict(kind='R184_ACT', index=4, document=dict(
            origin=dict(record_index=2, record_sha256=response['sha256']),
            outcome=dict(status='LANGUAGE_RESPONSE_UNVERIFIED', executed=False))))
        text = capsule('peer_math', act, response)
        self.assertIn('Own prose 中文', text)
        self.assertIn('masked context', text)
        self.assertIn('not your verified result', text)
        response['document']['response']['raw'] = 'Changed'
        with self.assertRaises(ValueError):
            capsule('peer_math', act, response)

    def test_only_paths_and_filter_change_not_plasticity_or_controls(self):
        original = dict(source_root='/old/source', root='/same/raw', physical=0,
            hard_end_unix=123, lease_end_unix=456, max_sleeps=None,
            startup_context=dict(path='/old/source/context/START.md', sha256='abc'),
            think_act_learn=dict(trial_id='SAME', prose_target_filter='OLD',
                peer_policy='SAME', new_presentations=32),
            plasticity=dict(learning_rate=9e-5, anchor_lambda=.25, rehearsal_presentations=0))
        before = deepcopy(original)
        changed = repair.proposed_plan(original, Path('/new/source'))
        self.assertEqual(original, before)
        self.assertEqual(changed['think_act_learn']['prose_target_filter'], repair.POLICY)
        changed['source_root'] = original['source_root']
        changed['startup_context']['path'] = original['startup_context']['path']
        changed['think_act_learn']['prose_target_filter'] = original['think_act_learn']['prose_target_filter']
        self.assertEqual(changed, original)

    def record(self):
        state = dict(pending=None, sleep_frontier=1, rows=[dict(target='Original 中文')])
        digest = hashlib.sha256(json.dumps(state, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        return dict(kind='SLEEP_COMPLETE', document=dict(status='COMPLETE',
            resume_state=dict(state=state, sha256=digest)))

    def test_quiescent_boundary_preserves_raw_rows(self):
        record = self.record()
        before = deepcopy(record)
        repair.boundary_document(record, ['R184_LEARN_COMPLETE'])
        self.assertEqual(record, before)

    def test_new_generation_or_update_is_not_a_boundary(self):
        for kind in ('REQUEST', 'UPDATE', 'COMMITTED', 'COMPACTION', 'TERMINAL'):
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                repair.boundary_document(self.record(), [kind])

    def test_state_hash_and_pending_are_enforced(self):
        for key, value in (('pending', 'generation'), ('sleep_frontier', 0)):
            record = self.record()
            record['document']['resume_state']['state'][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                repair.boundary_document(record, [])

    def test_outer_metadata_and_integrity_ignore_nested_assertions(self):
        record = dict(document=dict(outcome=dict(executed=False), text='A prose assertion is not a tool receipt.'),
            index=0, journal_id='journal', kind='R184_ACT', previous_sha256='a' * 64)
        record['sha256'] = hashlib.sha256(json.dumps(record, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / '00000000000000000000.json'
            path.write_text(json.dumps(record, sort_keys=True, separators=(',', ':')))
            self.assertEqual(metadata(path), 'R184_ACT')
            self.assertFalse(read_record(path)['document']['outcome']['executed'])
            record['document']['outcome']['executed'] = True
            path.write_text(json.dumps(record, sort_keys=True, separators=(',', ':')))
            with self.assertRaises(ValueError):
                read_record(path)


if __name__ == '__main__':
    unittest.main()
