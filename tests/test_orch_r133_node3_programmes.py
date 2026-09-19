import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from gpu import orch_r133_node3_programmes as programme


class ProgrammeTests(unittest.TestCase):
    def setUp(self):
        self.original = ('### Your situation\nR127.\n### Learning and memory\nOld.\n'
                         '### Working with Rohin\nCollaborate.\n### Resources and initial orientation\nOld.')
        self.plan = dict(physical=6, gpu_uuid=programme.DEVICES[6], source_root='/local/source')
        self.policy = dict(minor=5, uid=1001, gid=1002, unit='orch-r133-node3-'+'a'*32)

    def test_protected_and_foreign_slots_rejected(self):
        for physical in (0, 1, 2, 8, -1, True, '6'):
            with self.subTest(physical=physical), self.assertRaisesRegex(ValueError, 'only_owned'):
                programme.spec(physical)

    def test_exact_table(self):
        expected = {3: ('parent_guided_distillation', 2), 4: ('free_distillation', 2),
                    5: ('no_distillation', 4), 6: ('no_distillation', 5), 7: ('reread_select', 3)}
        for physical, (replay, cadence) in expected.items():
            with self.subTest(physical=physical):
                actual = programme.spec(physical)
                self.assertEqual((actual['replay'], actual['cadence']), (replay, cadence))
                self.assertEqual(actual['seed'], 0)

    def test_none_startup_truthful(self):
        for physical in (5, 6):
            with self.subTest(physical=physical):
                text = programme.startup_text(self.original, physical, '/source', '/workspace')
                self.assertIn('no third pre-sleep generation', text)
                self.assertIn('available visible history is retained', text)
                self.assertNotIn('nonempty selected text replaces', text)
                self.assertNotIn('reread_select', text)

    def test_guided_description_and_absent_parent_fallback(self):
        text = programme.startup_text(self.original, 3, '/source', '/workspace')
        self.assertIn('parent_guided_distillation', text)
        self.assertIn('no guidance is present, choose for yourself', text)
        self.assertIn('nonempty distillation replaces', text)

    def test_all_startups_fixed_budget_and_attribution(self):
        for physical in programme.LANES:
            with self.subTest(physical=physical):
                text = programme.startup_text(self.original, physical, '/source', '/workspace')
                for field in ('rank-8', '0.25', '16,384', '512', '18:00 UTC', 'Astra', f'physical{physical}'):
                    self.assertIn(field, text)
                self.assertNotIn('physical1 through', text)
                self.assertLess(len(text.encode()), 16384)

    def test_containment_is_exact_target_and_nonroot(self):
        command = programme.containment_command(self.plan, self.policy, ['python3'], 600)
        for expected in ('--property=DevicePolicy=strict', '--property=NoNewPrivileges=yes',
                         '--property=User=1001', '--property=Group=1002', '--property=RuntimeMaxSec=600',
                         '--property=DeviceAllow=/dev/nvidia5 rw', '--property=CapabilityBoundingSet='):
            self.assertIn(expected, command)
        for minor in (0, 1, 2, 3, 4, 6, 7):
            self.assertNotIn(f'--property=DeviceAllow=/dev/nvidia{minor} rw', command)
        self.assertIn('CUDA_VISIBLE_DEVICES='+programme.DEVICES[6], command)

    def test_containment_rejects_unknown_uuid_root_unbounded_or_unit(self):
        cases = [(dict(self.plan, gpu_uuid='wrong'), self.policy, 600),
                 (self.plan, dict(self.policy, uid=0), 600),
                 (self.plan, dict(self.policy, unit='existing'), 600),
                 (self.plan, self.policy, 0)]
        for plan, policy, lifetime in cases:
            with self.subTest(policy=policy), self.assertRaises(ValueError):
                programme.containment_command(plan, policy, ['python3'], lifetime)

    def test_supervisor_rejects_missing_verified_release_before_dispatch(self):
        config = dict(attempt_dir='/must-not-write')
        with patch.object(programme.guard, 'validate', return_value=(config, self.plan)), \
             patch.object(programme.native, 'read', return_value=dict(status='NO_RELEASE')):
            with self.assertRaisesRegex(ValueError, 'verified_owned_release'):
                programme.supervise('/config', '/release')

    def test_parent_styles_distinct_and_no_extra_leader(self):
        self.assertEqual(len({programme.spec(physical)['style'] for physical in programme.LANES}), 5)
        for physical in programme.LANES:
            self.assertIn('One autonomous Astra parent leads', programme.programme_text(physical))
            self.assertIn('never receive sealed evaluation', programme.programme_text(physical))

    def test_busy_admission_cannot_start_contained_child(self):
        with tempfile.TemporaryDirectory() as temporary:
            config = dict(attempt_dir=temporary)
            release = dict(status='RELEASED', physical=6, uuid=programme.DEVICES[6])
            report = dict(clear=False, scanner_euid=0, blocking_reasons=['open_device_pid:123'],
                          gpu=dict(uuid=programme.DEVICES[6]))
            with patch.object(programme.guard, 'validate', return_value=(config, self.plan)), \
                 patch.object(programme.native, 'read', return_value=release), \
                 patch.object(programme.native, 'sha', return_value='a'*64), \
                 patch.object(programme.subprocess, 'check_output', return_value=json.dumps(report)), \
                 patch.object(programme.subprocess, 'run') as run:
                with self.assertRaisesRegex(ValueError, 'unchanged_global_exclusive_admission'):
                    programme.supervise('/config', '/release')
                run.assert_not_called()
            self.assertTrue((Path(temporary)/'FAILED.json').exists())
            self.assertEqual(json.loads((Path(temporary)/'ADMISSION.json').read_text()), report)


if __name__ == '__main__':
    unittest.main()
