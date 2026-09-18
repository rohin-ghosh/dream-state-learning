import unittest

from gpu import orch_r130_route_probe_guard as guard


class GuardScopeTests(unittest.TestCase):
    def plan(self):
        return dict(gpu_uuid=guard.UUID, physical=7, wrapper='ovx3',
            created_unix=1000, hard_end_unix=2000, next_reserved_unix=4000,
            max_native_calls=96)

    def test_exact_scope_accepted(self):
        guard.validate_scope(self.plan())

    def test_foreign_device_wrapper_and_quota_rejected(self):
        for key, value in (('physical', 6), ('gpu_uuid', 'GPU-other'),
                           ('wrapper', 'ovx'), ('max_native_calls', 97)):
            with self.subTest(key=key), self.assertRaises(ValueError):
                guard.validate_scope(dict(self.plan(), **{key: value}))

    def test_timer_collision_rejected(self):
        with self.assertRaisesRegex(ValueError, 'release_before_existing_timer'):
            guard.validate_scope(dict(self.plan(), next_reserved_unix=2600))

    def test_unbounded_duration_rejected(self):
        with self.assertRaisesRegex(ValueError, 'bounded_diagnostic_duration'):
            guard.validate_scope(dict(self.plan(), hard_end_unix=5000,
                                      next_reserved_unix=10000))
