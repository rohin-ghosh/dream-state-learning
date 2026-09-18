from copy import deepcopy
import unittest

from extension_spec import digest, preview_plan


class ExtensionSpecTests(unittest.TestCase):
    def setUp(self):
        self.plan = dict(physical=1, root='/localhome/local-rohing/orch_r232_curriculum_frozen_20260918/raw',
            source_root='/old/source', startup_context={'path': '/old/source/birth.txt'}, gpu_uuid='frozen',
            hard_end_unix=1789754400, lease_end_unix=1789776000,
            learn_row_policy='R227_ALL_AUTHENTIC_CHILD_ROWS_V1',
            think_act_learn={'learn_row_policy': 'R227_ALL_AUTHENTIC_CHILD_ROWS_V1'}, learning_rate=3e-5,
            new_presentations=16, control_policy='unchanged')
        self.model = dict(checkpoint_sha256={'adapter': 'a', 'optimizer': 'b', 'rng': 'b'}, optimizer_steps=0)
        state = dict(pending=None, sleep_frontier=1, rows=[{'original': 'bytes'}],
            sleep_receipts=[{'status': 'COMPLETE'}], model_state_sha256=digest(self.model['checkpoint_sha256']),
            deadline_unix=1789754400)
        self.saved = dict(state=state, sha256=digest(state))
        self.authority = dict(schema='R233_EXISTING_PAIR_ALLOCATION_DATE_CORRECTION_V1',
            node_alias='ovx4', same_physical_pair=True, physical_devices=[0, 1], gpu_uuids=['learner', 'frozen'],
            lease_end_unix=1790812800, hard_end_unix=1790791200, safety_margin_seconds=21600,
            lease_purchase_or_extension_performed=False, provider_exact_expiry_independently_verified=False)

    def preview(self):
        return preview_plan(self.plan, self.saved, self.model, self.authority, '/new/source')

    def test_only_receiving_and_deadline_fields_change(self):
        before = deepcopy((self.plan, self.saved, self.model, self.authority))
        result = self.preview()
        self.assertEqual(before, (self.plan, self.saved, self.model, self.authority))
        self.assertEqual({key for key in result if result[key] != self.plan.get(key)},
            {'source_root', 'startup_context', 'hard_end_unix', 'lease_end_unix', 'authorized_wall_extension'})
        self.assertEqual(result['authorized_wall_extension']['previous_stream_sha256'], self.saved['sha256'])

    def test_pending_or_bad_model_cannot_preview(self):
        for field, value in [('pending', 'sleep:inflight'), ('model_state_sha256', 'wrong')]:
            with self.subTest(field=field), self.assertRaises(ValueError):
                original = deepcopy(self.saved)
                self.saved['state'][field] = value
                self.saved['sha256'] = digest(self.saved['state'])
                try:
                    self.preview()
                finally:
                    self.saved = original

    def test_wrong_device_or_scope_rejected(self):
        for field, value in [('physical', 2), ('gpu_uuid', 'foreign'), ('root', '/other/raw')]:
            with self.subTest(field=field), self.assertRaises(ValueError):
                previous = self.plan[field]
                self.plan[field] = value
                try:
                    self.preview()
                finally:
                    self.plan[field] = previous

    def test_margin_and_authority_cannot_be_relaxed(self):
        for field, value in [('safety_margin_seconds', 120), ('hard_end_unix', 1790812700),
                ('lease_purchase_or_extension_performed', True), ('provider_exact_expiry_independently_verified', True)]:
            with self.subTest(field=field), self.assertRaises(ValueError):
                previous = self.authority[field]
                self.authority[field] = value
                try:
                    self.preview()
                finally:
                    self.authority[field] = previous

    def test_frozen_cannot_unfreeze(self):
        self.model['optimizer_steps'] = 1
        with self.assertRaisesRegex(ValueError, 'same_frozen'):
            self.preview()

    def test_learner_keeps_dose_and_control(self):
        self.plan.update(physical=0, gpu_uuid='learner',
            root='/localhome/local-rohing/orch_r231_curriculum_birth_20260918/raw')
        self.model['optimizer_steps'] = 1280
        result = self.preview()
        self.assertEqual(result['new_presentations'], 16)
        self.assertEqual(result['learning_rate'], 3e-5)
        self.assertEqual(result['control_policy'], 'unchanged')


if __name__ == '__main__':
    unittest.main()
