"""Focused CPU regressions for the explicit parent-only treatment change."""

import json
from pathlib import Path
import re
import unittest

from checkpoint_tail_parent_strong import FLEET, NEW_RULE, OLD_RULE, STYLE, WALL, scoped_source, validate_config


class StrongParentTests(unittest.TestCase):
    def test_only_obsolete_V_rule_changes(self):
        source = (FLEET / 'r202_parent.py').read_bytes()
        changed = scoped_source(source)
        self.assertEqual(changed.replace(NEW_RULE, OLD_RULE, 1), source.decode())
        compile(changed, 'scoped_parent_test', 'exec')

    def test_source_drift_rejected(self):
        with self.assertRaises(ValueError):
            scoped_source((FLEET / 'r202_parent.py').read_bytes() + b'\n')

    def test_authorized_V_correction_allowed_unrelated_bounds_preserved(self):
        pattern = NEW_RULE[2:-1]
        self.assertIsNone(re.search(pattern, 'Your saved calculation gives V=3, not 29. Show the arithmetic.'))
        for text in ('n=4', 'n = 4', '354'):
            with self.subTest(text=text):
                self.assertIsNotNone(re.search(pattern, text))

    def config(self):
        old = json.loads((FLEET / 'LIVE_CONVERSATION_PARENT14_CONFIG.json').read_bytes())
        old.update(hard_end_unix=WALL, native_binding_path='/source-bound/test-only/LOAD.json',
            native_binding_sha256='test-only')
        new = dict(old, parent_style=STYLE, cadence_label='PERSISTENT', minimum_duration_seconds=3600)
        return old, new

    def test_treatment_only_config_allowed(self):
        validate_config(*self.config())

    def test_native_provider_human_priority_and_cadence_cannot_change(self):
        for field in ('root', 'source_root', 'ordinary_console_priority_since_unix',
                'existing_parent_lock', 'parent_reasoning_effort', 'cadence_responses', 'native_binding_sha256'):
            old, new = self.config()
            new[field] = 'unauthorized'
            with self.subTest(field=field):
                with self.assertRaises((ValueError, TypeError)):
                    validate_config(old, new)

    def test_actual_pending_human_guard_preserved(self):
        changed = scoped_source((FLEET / 'r202_parent.py').read_bytes())
        self.assertIn('pending = ordinary_pending(repository, binding)', changed)
        self.assertIn("raise RuntimeError('parent_quiet_while_genuine_ordinary_turn_pending')", changed)

    def test_full_original_parent_validator_accepts_treatment(self):
        import sys
        sys.path.insert(0, str(FLEET.parents[5]))
        from gpu.orch_r133_programme_parent import validate
        old, proposed = self.config()
        validate(proposed)


if __name__ == '__main__':
    unittest.main()
