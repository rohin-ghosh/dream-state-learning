"""Regression checks for exact porting and fail-closed local preparation."""

from copy import deepcopy
import hashlib
from pathlib import Path
import tempfile
import unittest

import manifest_checks as checks
import prepare_epoch3 as prepare


class Epoch3Tests(unittest.TestCase):
    def setUp(self):
        self.old = prepare.base.read(prepare.EPOCH2 / 'EPOCH2_SOURCE.json')
        self.original = (prepare.EPOCH2 / 'source' / checks.HISTORY).read_bytes()
        self.port_bytes = prepare.PORT.read_bytes()
        self.manifest = deepcopy(self.old)
        pins = dict(self.old['new_source_pins'], **{checks.HISTORY: checks.AFTER})
        self.manifest.update(schema='C2_EPOCH3_EXACT_LOCAL_SOURCE_V1', epoch2_manifest_sha256=checks.EPOCH2,
            frontier_port_sha256=checks.PORT, new_source_pins=pins,
            epoch2_source_pins=self.old['new_source_pins'],
            epoch2_to_epoch3_delta=checks.delta(self.old['new_source_pins'], pins),
            changed=checks.delta(self.old['old_source_pins'], pins),
            epoch1_to_epoch3_delta=checks.delta(self.old['epoch1_source_pins'], pins))

    def test_exact_four_seam_output_and_inverse(self):
        result = prepare.exact_port(self.original, self.port_bytes)
        self.assertEqual(hashlib.sha256(result).hexdigest(), checks.AFTER)

    def test_wrong_preimage_and_port_fail_closed(self):
        for original, port in ((self.original + b'\n', self.port_bytes),
                (self.original, self.port_bytes + b'\n')):
            with self.subTest(original=len(original), port=len(port)), self.assertRaises(ValueError):
                prepare.exact_port(original, port)

    def test_Main_port_rejects_each_missing_or_duplicate_seam(self):
        port = prepare.load('c2_test_exact_Main_port', prepare.PORT)
        for before, after in port.EDITS:
            for content in (self.original.replace(before.encode(), b'', 1),
                    self.original + before.encode()):
                with self.subTest(seam=before[:32]), self.assertRaises(ValueError):
                    port.port(content)
        with self.assertRaises(ValueError):
            port.port(port.port(self.original))

    def test_exact_five_three_one_delta_maps(self):
        checks.validate(self.manifest)
        self.assertEqual(len(self.manifest['changed']), 5)
        self.assertEqual(len(self.manifest['epoch1_to_epoch2_delta']), 2)
        self.assertEqual(len(self.manifest['epoch1_to_epoch3_delta']), 3)
        self.assertEqual(len(self.manifest['epoch2_to_epoch3_delta']), 1)

    def test_extra_or_different_source_delta_rejected(self):
        for name in (*checks.UNCHANGED, 'gpu/c2_retention_runtime.py', checks.HISTORY):
            manifest = deepcopy(self.manifest)
            manifest['new_source_pins'][name] = '0' * 64
            with self.subTest(name=name), self.assertRaises(ValueError):
                checks.validate(manifest)

    def test_inconsistent_history_delta_maps_rejected(self):
        for key in ('epoch1_to_epoch2_delta', 'epoch1_to_epoch3_delta', 'epoch2_to_epoch3_delta', 'changed'):
            manifest = deepcopy(self.manifest)
            manifest[key] = {}
            with self.subTest(key=key), self.assertRaises(ValueError):
                checks.validate(manifest)

    def test_deadline_journal_or_authority_change_rejected(self):
        for key, value in (('deadline_unix', 1789927201), ('lease_end_unix', 1789948801),
                ('journal_id', '0' * 32), ('admission_granted', True), ('receiving_plan_ready', True),
                ('remote_staging_performed', True), ('epoch2_manifest_sha256', '0' * 64),
                ('frontier_port_sha256', '0' * 64)):
            manifest = deepcopy(self.manifest)
            manifest[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                checks.validate(manifest)

    def test_existing_or_outside_output_rejected(self):
        for path in (prepare.EPOCH2, prepare.WORKER, '/tmp/c2_epoch3_outside_forbidden'):
            with self.subTest(path=str(path)), self.assertRaises(ValueError):
                prepare.validate_output(path)

    def test_symlink_output_rejected(self):
        with tempfile.TemporaryDirectory(dir=prepare.WORKER) as temporary:
            path = Path(temporary)
            (path / 'alias').symlink_to(prepare.WORKER, target_is_directory=True)
            with self.assertRaises(ValueError):
                prepare.validate_output(path / 'alias/new-output')

    def test_plan_only_relocates_source_and_startup(self):
        original = prepare.base.read(prepare.EPOCH2 / 'control/PLAN.template.json')
        source = Path('/localhome/local-rohing/orch_retention_20260919/C2/epoch3/source')
        new = prepare.base.plan_template(original, source)
        self.assertEqual(new['source_root'], str(source))
        new['source_root'] = original['source_root']
        new['startup_context']['path'] = original['startup_context']['path']
        self.assertEqual(new, original)

    def test_portable_helper_references_only_epoch3_manifest(self):
        original = (prepare.EPOCH2 / 'tools/cpu_check.py').read_bytes()
        result = prepare.portable_checker(original)
        self.assertNotIn(b'EPOCH2_SOURCE.json', result)
        self.assertIn(b'EPOCH3_SOURCE.json', result)
        self.assertIn(b'validator.verify(source, manifest)', result)
        self.assertIn(b'guard_only_reanchors_COMPLETE_no_recipe_wall_or_bridge_change', result)

    def test_exact_epoch2_manifest_and_preimage_still_pinned(self):
        self.assertEqual(prepare.sha(prepare.EPOCH2 / 'EPOCH2_SOURCE.json'), checks.EPOCH2)
        self.assertEqual(hashlib.sha256(self.original).hexdigest(), checks.BEFORE)


if __name__ == '__main__':
    unittest.main(verbosity=2)
