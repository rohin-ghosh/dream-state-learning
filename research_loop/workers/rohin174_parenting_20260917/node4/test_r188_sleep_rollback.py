"""CPU-only R188 binding and exact-source patch regressions."""

from copy import deepcopy
from pathlib import Path
import sys
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parent))
import r188_sleep_rollback as rollback


class RollbackTests(unittest.TestCase):
    def setUp(self):
        self.plan = dict(physical=0, root=rollback.ROOT, gpu_uuid=rollback.UUID,
            hard_end_unix=1789754400, rehearsal_presentations=0, new_presentations=16, anchor_lambda=0.25,
            r188_sleep_rollback=dict(schema='R188_KERNEL0_SAVED40_ROLLBACK_V1', archive_root=rollback.ARCHIVE,
                saved_cycle=40, saved_optimizer_steps=4207, uncertain_inflight_update=True,
                discarded_logged_updates=133, discarded_steps=[4208, 4340]))

    def test_exact_saved_recipe_and_explicit_uncertainty(self):
        self.assertEqual(rollback.validate_plan(self.plan), self.plan['r188_sleep_rollback'])

    def test_foreign_life_wall_or_recipe_refused(self):
        for field, value in [('physical', 1), ('root', '/other'), ('gpu_uuid', 'GPU-other'),
                ('hard_end_unix', 1789754401), ('rehearsal_presentations', 1), ('new_presentations', 32),
                ('anchor_lambda', 0.5)]:
            with self.subTest(field=field), self.assertRaises(ValueError):
                candidate = deepcopy(self.plan)
                candidate[field] = value
                rollback.validate_plan(candidate)

    def test_fake_exact_inflight_or_wrong_saved_model_refused(self):
        for field, value in [('uncertain_inflight_update', False), ('saved_cycle', 41),
                ('saved_optimizer_steps', 4340), ('discarded_logged_updates', 132), ('archive_root', '/other')]:
            with self.subTest(field=field), self.assertRaises(ValueError):
                candidate = deepcopy(self.plan)
                candidate['r188_sleep_rollback'][field] = value
                rollback.validate_plan(candidate)

    def test_unrecognized_native_bytes_refused(self):
        with self.assertRaises(ValueError):
            rollback.patch_native('def run():\n    pass\n')

    def test_three_actual_seams_preserve_existing_recovery_branch(self):
        source = """def validate_plan(plan):
    return plan

def run():
    if True:
        if True:
            if True:
                recovering = (isinstance(stream.pending, str) and stream.pending.startswith('sleep:')
                    and isinstance(plan.get('preupdate_recovery'), dict))
                if recovering:
                    from gpu.orch_r138_kernel_recovery import recover_rng
                    recover_rng(child, stream, journal, plan['preupdate_recovery'])
"""
        patched = rollback.patch_native(source)
        self.assertIn('from gpu.orch_r138_kernel_recovery import recover_rng', patched)
        self.assertIn('from gpu.orch_r188_node4_sleep_rollback import record_rollback', patched)
        with self.assertRaises(ValueError):
            rollback.patch_native(patched)


if __name__ == '__main__':
    unittest.main()
