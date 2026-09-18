from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from gpu import orch_r119_lease_clock as clock


class LeaseClockTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.config = dict(owner='F1', branches={str(index): {} for index in range(8)},
                           episodes_per_branch=2, new_presentations=16,
                           rehearsal_presentations=1, anchor_loss_weight=.25)
        config = self.save('CONFIG.json', self.config)
        self.state = dict(config_sha256=config['sha256'], generation=1,
                          checkpoint=dict(path_sha256='checkpoint', optimizer_path_sha256='optimizer'),
                          optimizer_steps=3009, child_token_exposures=388033,
                          anchor_token_exposures=56236)
        self.save('STATE.json', self.state)
        initial = self.save('STATE_AT_AUTHORIZATION.json', self.state)
        self.backend = self.root / 'backend.py'
        self.backend.write_text('original source\n')
        self.policy = dict(schema=clock.SCHEMA, node='ovx3', shared_root=str(self.root),
                           shared_config=config, state_at_authorization=initial,
                           lease=self.save('LEASE.json', dict(expires='2026-09-17T04:04:00Z')),
                           lease_expiry_field=['expires'], lease_margin_seconds=21600,
                           commit_reserve_seconds=120, backend_sha256=clock.sha(self.backend),
                           hard_end_unix=clock.timestamp('2026-09-16T22:04:00Z'),
                           train_end_unix=clock.timestamp('2026-09-16T22:02:00Z'))
        self.authorization = dict(scope='REPORT_CUT_NOT_RUN_END_LEASE_CONTINUATION', node='ovx3',
                                  preserve_checkpoint_optimizer_counters=True,
                                  preserve_final_evaluation=True,
                                  hard_end_unix=self.policy['hard_end_unix'])
        self.policy['authorization'] = self.save('AUTHORIZATION.json', self.authorization)
        self.now = clock.timestamp('2026-09-15T17:15:00Z')

    def save(self, name, document):
        path = self.root / name
        path.write_text(json.dumps(document, sort_keys=True))
        return dict(path=str(path), sha256=clock.sha(path))

    def validate(self, policy=None):
        return clock.validate(self.save('POLICY.json', policy or self.policy),
                              backend_path=self.backend, now=self.now)

    def test_extends_report_cut_without_state_or_optimizer_reset(self):
        before = (self.root / 'STATE.json').read_bytes()
        result = self.validate()
        self.assertEqual(result['hard_end_unix'], clock.timestamp('2026-09-16T22:04:00Z'))
        self.assertEqual(before, (self.root / 'STATE.json').read_bytes())

    def test_no_environment_retains_original_behavior(self):
        self.assertIsNone(clock.from_environment({}, self.backend))

    def test_partial_environment_rejected(self):
        with self.assertRaisesRegex(ValueError, 'complete_lease_clock'):
            clock.from_environment({'ORCH_R119_LEASE_CLOCK': 'anything'}, self.backend)

    def test_lease_margin_cannot_shrink(self):
        for update in (dict(lease_margin_seconds=1), dict(hard_end_unix=self.policy['hard_end_unix'] + 1)):
            with self.assertRaises(ValueError):
                self.validate(dict(self.policy, **update))

    def test_changed_authorization_or_lease_is_rejected(self):
        for name in ('AUTHORIZATION.json', 'LEASE.json'):
            original = (self.root / name).read_bytes()
            (self.root / name).write_text('{}')
            with self.assertRaises(ValueError):
                self.validate()
            (self.root / name).write_bytes(original)

    def test_state_or_exposure_reset_rejected(self):
        for update in (dict(generation=0), dict(optimizer_steps=0), dict(child_token_exposures=0),
                       dict(checkpoint=dict(path_sha256='different', optimizer_path_sha256='new'))):
            self.save('STATE.json', dict(self.state, **update))
            with self.assertRaises(ValueError):
                self.validate()
        self.save('STATE.json', self.state)

    def test_new_committed_generation_can_advance(self):
        self.save('STATE.json', dict(self.state, generation=2, optimizer_steps=3100,
                                    checkpoint=dict(path_sha256='next', optimizer_path_sha256='next_optimizer')))
        self.assertEqual(self.validate()['current_generation'], 2)

    def test_changed_backend_and_expired_clock_rejected(self):
        self.backend.write_text('changed')
        with self.assertRaisesRegex(ValueError, 'backend'):
            self.validate()
        with self.assertRaisesRegex(ValueError, 'expired'):
            clock.validate(self.save('POLICY.json', self.policy), now=self.policy['train_end_unix'])

    def test_recipe_changes_and_unknown_expiry_rejected(self):
        altered = deepcopy(self.config)
        altered['episodes_per_branch'] = 8
        self.save('CONFIG.json', altered)
        with self.assertRaises(ValueError):
            self.validate()
        with self.assertRaises(ValueError):
            clock.timestamp('2026-09-17T04:04:00')


if __name__ == '__main__':
    unittest.main()
