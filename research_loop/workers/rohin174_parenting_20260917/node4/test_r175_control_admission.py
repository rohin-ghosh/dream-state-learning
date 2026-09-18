"""CPU refusal tests for old V1 restarts; no network, models, or publication."""

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch


HOME = Path(__file__).resolve().parent


def load(name):
    spec = importlib.util.spec_from_file_location(name, HOME / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


operator = load('r175_node4_operator')
errata = load('r175_node4_errata')
stage = load('stage_parent_inputs')
admission = operator.admission
OLD_V1 = HOME / 'activation_20260917T2040Z/physical1'
CORRECTIVE_V1 = HOME / 'activation_20260917T2057Z/physical1'


class AdmissionTests(unittest.TestCase):
    def test_original_physical_refused_for_any_root(self):
        for root in (None, admission.CONTROL_ROOT, '/localhome/local-rohing/a_separate_fork/run1'):
            with self.subTest(root=root), self.assertRaisesRegex(ValueError, admission.REFUSAL):
                admission.target(1, root)

    def test_original_root_refused_for_other_or_missing_physical(self):
        variants = [admission.CONTROL_ROOT, admission.CONTROL_ROOT + '/', admission.CONTROL_ROOT + '/stream',
            admission.CONTROL_ROOT + '/../run1', '/' + admission.CONTROL_ROOT]
        for root in variants:
            for physical in (None, 0, 3, 4, 6):
                with self.subTest(root=root, physical=physical), self.assertRaisesRegex(ValueError, admission.REFUSAL):
                    admission.target(physical, root)

    def test_other_three_scopes_pass_exclusion_only(self):
        for physical in (0, 3, 4):
            self.assertTrue(admission.target(physical, operator.ROOTS[physical])['other_authorization_and_provenance_gates_still_required'])

    def test_generic_H_remains_available_for_separately_authorized_forks(self):
        path = operator.REPO / 'gpu/orch_r175_parent_arms.py'
        spec = importlib.util.spec_from_file_location('generic_arm_fixture', path)
        arms = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(arms)
        self.assertEqual(operator.sha(path), operator.BUILDER_SHA)
        self.assertEqual(arms.specification('H')['cadence'], 1)
        self.assertTrue(admission.target(6, '/localhome/local-rohing/a_separate_fork/run1')['other_authorization_and_provenance_gates_still_required'])

    def test_missing_or_changed_V2_never_falls_back_to_V1(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, 'amendment.json')
            with patch.object(admission, 'V2_PATH', path), self.assertRaises(ValueError):
                admission.target(0, operator.ROOTS[0])
            path.write_text('{}')
            with patch.object(admission, 'V2_PATH', path), self.assertRaisesRegex(ValueError, 'no_V1_fallback'):
                admission.target(0, operator.ROOTS[0])

    def test_mismatched_CONFIG_cannot_hide_raw_root_behind_physical0(self):
        with tempfile.TemporaryDirectory() as directory:
            lane = Path(directory, 'physical0')
            lane.mkdir()
            (lane / 'PLAN.json').write_text(json.dumps(dict(physical=0, root=operator.ROOTS[0])))
            (lane / 'CONFIG.json').write_text(json.dumps(dict(root=admission.CONTROL_ROOT)))
            with self.assertRaisesRegex(ValueError, admission.REFUSAL):
                admission.lane(lane)

    def test_old_V1_operator_restart_before_any_side_effect(self):
        for function in (operator.bootstrap, operator.activate, operator.serve):
            with self.subTest(function=function.__name__), patch.object(operator, 'ssh') as transport, \
                    patch.object(operator.os, 'pidfd_open') as signal_target, patch.object(operator.subprocess, 'Popen') as dispatch, \
                    self.assertRaisesRegex(ValueError, admission.REFUSAL):
                try:
                    function(OLD_V1)
                finally:
                    transport.assert_not_called()
                    signal_target.assert_not_called()
                    dispatch.assert_not_called()

    def test_corrective_recovery_and_fresh_stage_refused(self):
        for function in (errata.activate, lambda lane: errata.serve(lane, False),
                lambda lane: errata.stage(lane, HOME / 'activation_REFUSAL_ONLY/physical1')):
            with self.subTest(function=function), patch.object(errata.subprocess, 'Popen') as dispatch, \
                    self.assertRaisesRegex(ValueError, admission.REFUSAL):
                try:
                    function(CORRECTIVE_V1)
                finally:
                    dispatch.assert_not_called()
        self.assertFalse((HOME / 'activation_REFUSAL_ONLY').exists())

    def test_direct_corrective_call_stops_before_validator_or_provider(self):
        policy = types.SimpleNamespace(validate=Mock(), parent=types.SimpleNamespace(strong=Mock(), publish=Mock()))
        with self.assertRaisesRegex(ValueError, admission.REFUSAL):
            errata.corrective_tick(policy, None, {'root': admission.CONTROL_ROOT}, None, None, None)
        policy.validate.assert_not_called()
        policy.parent.strong.assert_not_called()
        policy.parent.publish.assert_not_called()

    def test_staging_descriptor_refuses_original_control_from_V1(self):
        assignment = stage.read(HOME / 'R175_FROZEN_ASSIGNMENT.json')
        with self.assertRaisesRegex(ValueError, admission.REFUSAL):
            stage.descriptor(1, assignment, None, {'root': admission.CONTROL_ROOT})

    def test_publication_guard_denies_first_and_all_later_H_calls(self):
        with tempfile.TemporaryDirectory() as directory:
            for message in ('baseline', 'recovery', 'republish'):
                with self.assertRaisesRegex(ValueError, admission.REFUSAL):
                    operator.publication_allowed(1, directory, message, 90)
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_old_V1_CLI_actions_return_explicit_refusal(self):
        cases = [('r175_node4_operator.py', action, OLD_V1) for action in ('bootstrap', 'activate', 'serve')]
        cases += [('r175_node4_errata.py', action, CORRECTIVE_V1) for action in ('activate', 'serve')]
        for filename, action, lane in cases:
            with self.subTest(filename=filename, action=action):
                result = subprocess.run([sys.executable, '-B', str(HOME / filename), action, '--lane', str(lane)],
                    env=dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1'),
                    text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(admission.REFUSAL, result.stderr)


if __name__ == '__main__':
    unittest.main()
