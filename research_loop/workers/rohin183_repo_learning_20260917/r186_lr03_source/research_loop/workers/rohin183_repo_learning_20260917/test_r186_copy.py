"""CPU-only one-factor, immutable adapter and treatment-boundary regressions."""

import ast
from copy import deepcopy
import unittest

from gpu import orch_r125_continual_native as native
from research_loop.workers.rohin183_repo_learning_20260917.r186_copy import (
    ARMS, GATE_ROOT, GATE_SHA, confinement, cpu_adapter, make_plan, retain_bridge,
)
from tests.test_orch_r125_continual_native import make_plan as fixture_plan


class CopyTests(unittest.TestCase):
    def baseline(self):
        plan = fixture_plan('/tmp/r186-synthetic')
        plan.update(new_presentations=16, rehearsal_presentations=0,
            startup_context=dict(path='/tmp/r184/context/R153_STARTUP.md'),
            think_act_learn=dict(schema='R184_THINK_ACT_LEARN_V1', trial_id='C2_explicit_v1',
                reflection_policy='explicit', think_segments=1, cpu_gate_root=GATE_ROOT, cpu_gate_sha256=GATE_SHA))
        return plan

    def test_only_four_assigned_slots(self):
        self.assertEqual({item[0] for item in ARMS.values()}, {0, 1, 5, 6})
        self.assertEqual(len({item[1] for item in ARMS.values()}), 4)

    def test_one_factor_and_exact_policy(self):
        for label, (physical, device, unused_pci, presentations, multiplier) in ARMS.items():
            with self.subTest(label=label):
                plan = make_plan(self.baseline(), '/tmp/new-source', label)
                self.assertEqual((plan['physical'], plan['gpu_uuid']), (physical, device))
                self.assertEqual(plan['new_presentations'], presentations)
                self.assertEqual(plan['plasticity']['learning_rate_multiplier'], multiplier)
                self.assertEqual((presentations != 16) + (multiplier != 1), 1)
                self.assertAlmostEqual(native.plasticity_policy(plan)['learning_rate'], 3e-5 * multiplier)
                self.assertEqual(plan['max_sleeps'], 41 + 3)

    def test_no_original_mutation_or_cadence_parent_change(self):
        baseline = self.baseline()
        before = deepcopy(baseline)
        allowed = {'source_root', 'physical', 'gpu_uuid', 'new_presentations', 'max_sleeps',
            'plasticity', 'startup_context', 'think_act_learn'}
        for label in ARMS:
            plan = make_plan(baseline, '/tmp/new-source', label)
            self.assertEqual(baseline, before)
            self.assertTrue({key for key in plan if plan[key] != baseline.get(key)} <= allowed)
            config = dict(plan['think_act_learn'])
            config['trial_id'] = baseline['think_act_learn']['trial_id']
            self.assertEqual(config, baseline['think_act_learn'])
            self.assertEqual(plan['root'], baseline['root'])
            self.assertEqual(plan['hard_end_unix'], baseline['hard_end_unix'])

    def test_wrong_recipe_or_gate_rejected(self):
        for field, value in (('new_presentations', 4), ('rehearsal_presentations', 1)):
            plan = self.baseline()
            plan[field] = value
            with self.assertRaises(ValueError):
                make_plan(plan, '/tmp/source', 'p4')
        for field, value in (('reflection_policy', 'brief'), ('think_segments', 2), ('cpu_gate_sha256', '0' * 64)):
            plan = self.baseline()
            plan['think_act_learn'][field] = value
            with self.assertRaises(ValueError):
                make_plan(plan, '/tmp/source', 'p4')

    def test_unknown_arm_rejected(self):
        with self.assertRaises(ValueError):
            make_plan(self.baseline(), '/tmp/source', 'gpu7')

    def test_frozen_cpu_method_exact(self):
        canonical = b'class Driver:\n    def _cpu(self, origin):\n        from gpu.orch_r153_community_transport import cpu_once\n        return cpu_once(origin)\n\n    def act(self):\n        return 7\n'
        frozen = b'class Driver:\n    def _cpu(self, origin):\n        from gpu.r184_cpu_bridge import call\n        return call(origin)\n'
        result = retain_bridge(canonical, frozen)
        self.assertEqual(cpu_adapter(result), cpu_adapter(frozen))
        self.assertIn(b'def act(self):\n        return 7', result)
        ast.parse(result)

    def test_changed_cpu_dispatch_refuses(self):
        with self.assertRaises(ValueError):
            retain_bridge(b'class Driver:\n    def _cpu(self, origin):\n        return None\n', b'')

    def test_all_seven_foreign_minors_and_unique_service(self):
        frozen = b"DEVICE='GPU-c9450d3d-0455-f034-b9bf-7f8956e44733'\nMINOR=3\nPATH='/dev/nvidia3'\nPCI='0000:57:00.0'\nDENIED=[0, 1, 2, 4, 5, 6, 7]\nUNIT='orch-r184-c2-explicit-'\n"
        units = set()
        for label, (physical, device, pci, unused_presentations, unused_multiplier) in ARMS.items():
            values = {}
            exec(confinement(frozen, label), values)
            self.assertEqual(values['DEVICE'], device)
            self.assertEqual(values['MINOR'], physical)
            self.assertEqual(values['PATH'], '/dev/nvidia' + str(physical))
            self.assertEqual(values['PCI'], pci)
            self.assertEqual(values['DENIED'], [minor for minor in range(8) if minor != physical])
            units.add(values['UNIT'])
        self.assertEqual(len(units), 4)

    def test_adamw_state_moments_and_count_untouched(self):
        class Optimizer:
            param_groups = [{'lr': 3e-5, 'step_marker': 4428}]
            state = {'parameter': {'step': 4428, 'exp_avg': [1, 2], 'exp_avg_sq': [3, 4]}}
        for label in ARMS:
            optimizer = Optimizer()
            optimizer.param_groups = deepcopy(Optimizer.param_groups)
            before = deepcopy(optimizer.state)
            policy = native.apply_plasticity(optimizer, make_plan(self.baseline(), '/tmp/source', label))
            self.assertEqual(optimizer.state, before)
            self.assertEqual(optimizer.param_groups[0]['step_marker'], 4428)
            self.assertEqual(policy['loaded_learning_rates'], [3e-5])
            self.assertAlmostEqual(optimizer.param_groups[0]['lr'], 3e-5 * ARMS[label][4])


if __name__ == '__main__':
    unittest.main()
