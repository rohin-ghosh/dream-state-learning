"""Fake original boundary operations; no pidfd, guardian, native, or transport action."""

from contextlib import contextmanager
from copy import deepcopy
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

import common as core
sys.path.insert(0, str(core.REPO))
from coordinator import coordinate, execution_digest
from research_loop.workers.post_recovery_retention_boundary_20260918.boundary import digest

BOUNDARY = core.REPO / 'research_loop/workers/post_recovery_retention_boundary_20260918'
sys.path.insert(0, str(BOUNDARY))
from test_boundary import inputs, selected


def load(name, path):
    specification = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


from research_loop.workers.post_recovery_retention_boundary_20260918 import coordinator as original_coordinator
with patch.dict(sys.modules, coordinator=original_coordinator):
    original = load('original_boundary_test_fixture_for_C2_owner', BOUNDARY / 'test_coordinator.py')
prefix = load('exact_C2_epoch4_budget_for_owner_tests', core.HERE.parent /
    'prepared_epoch4_v5/C2/epoch4/tools/prefix_preflight.py')


class Operations(original.FakeOperations):
    def __init__(self, binding):
        super().__init__(binding)
        self.clock = 0
        self.budget = None
        self.gate = False
        self.checkpoint_cost = 0
        self.after_exit_cost = 0
        self.fail_static = False
        self.postexit_verified_under_budget = False

    def monotonic(self):
        return self.clock

    def verify_static(self, prepared):
        self.event('static')
        if self.fail_static:
            raise ValueError('no_real_all_in_preflight')

    def begin_attempt(self, candidate):
        if self.gate:
            raise ValueError('no_retry')
        self.gate = True
        self.event('attempt')

    @contextmanager
    def bounded_path(self, deadline):
        self.budget = prefix.ReservationBudget(deadline, clock=self.monotonic)
        try:
            yield self.budget
        finally:
            self.budget = None

    def verify_checkpoint(self, candidate):
        assert self.stopped and self.budget is not None
        self.clock += self.checkpoint_cost
        return super().verify_checkpoint(candidate)

    def verify_receiver(self, receiver, candidate):
        assert self.budget is not None
        if self.exited:
            self.postexit_verified_under_budget = True
            self.clock += self.after_exit_cost
        return super().verify_receiver(receiver, candidate)

    def dispatch_once(self, token):
        assert self.budget is not None
        return super().dispatch_once(token)


class CoordinatorTests(unittest.TestCase):
    def setUp(self):
        self.binding, self.prepared, self.authority = inputs()
        self.configuration = dict(binding=self.binding, prepared=self.prepared, authority=self.authority,
            prefix_policy=dict(schema='C2_RESERVED_PREFLIGHT_POLICY_V1', stop_seconds=30, commit_margin_seconds=2))
        self.operations = Operations(self.binding)

    def run_coordinate(self):
        return coordinate(self.configuration, self.operations, max_observations=2)

    def test_original_guardian_30_seconds_and_one_budget_through_dispatch(self):
        token = self.run_coordinate()
        self.assertTrue(token['old_native_exited'])
        self.assertTrue(self.operations.postexit_verified_under_budget)
        self.assertIsNone(self.operations.budget)

    def test_missing_real_static_evidence_prevents_reservation(self):
        self.operations.fail_static = True
        with self.assertRaisesRegex(ValueError, 'no_real'):
            self.run_coordinate()
        self.assertFalse(self.operations.stopped)
        self.assertFalse(self.operations.exited)

    def test_expensive_checkpoint_resumes_same_native_without_dispatch(self):
        self.operations.checkpoint_cost = 29
        with self.assertRaises(ValueError):
            self.run_coordinate()
        self.assertFalse(self.operations.exited)
        self.assertFalse(self.operations.stopped)
        self.assertTrue(self.operations.gate)

    def test_expiration_after_exit_never_falls_back_or_dispatches(self):
        self.operations.after_exit_cost = 29
        with self.assertRaises(ValueError):
            self.run_coordinate()
        self.assertTrue(self.operations.exited)
        self.assertTrue(self.operations.gate)

    def test_reservation_cannot_extend_30_seconds(self):
        self.configuration['prefix_policy']['stop_seconds'] = 31
        with self.assertRaises(ValueError):
            self.run_coordinate()
        self.assertFalse(self.operations.stopped)

    def test_owner_transport_is_in_execution_digest(self):
        before = execution_digest(self.configuration)
        self.configuration['owner_bridge'] = {'command': ['another-owner']}
        self.assertNotEqual(before, execution_digest(self.configuration))


if __name__ == '__main__':
    unittest.main(verbosity=2)
