import json
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

from gpu import astra_pcfl_event_sequence_v2_warm_overlay as api
from gpu import astra_pcfl_event_sequence_v2_followup as operator


ORIGINAL_FIT = '''def validate_warm_tensors(warm, trainable):
    return False
def validate_predecessor(inputs, material, phase, root, config, kind):
    v3._warm_parent(parent, root / "checkpoint", config)
    return parent, prior, before
def run_phase(inputs, material, phase, root, config, kind):
    return validate_predecessor(inputs, material, phase, root, config, kind)
'''
WRAPPER = '''def validate_predecessor_for_write(inputs, material, phase, root, config, kind):
    parent, prior, before = validate_predecessor(inputs, material, phase, root, config, kind)
    if parent is not None:
        v3._warm_parent(parent, root / "checkpoint", config)
    return parent, prior, before
'''
REPLACEMENT_FIT = ORIGINAL_FIT.replace('return False', 'return True').replace(
    '    v3._warm_parent(parent, root / "checkpoint", config)\n', '').replace(
    'return validate_predecessor(', 'return validate_predecessor_for_write(') + WRAPPER
ORIGINAL_OUTER = '''def _inputs(inputs, material, phase, root, config, kind):
    fit.validate_predecessor(inputs, material, phase, root, config, kind)
def validate_stage(inputs, material, phase, root, config, kind):
    fit.validate_predecessor(inputs, material, phase, root, config, kind)
def controller(inputs, material, phase, root, config, kind):
    _inputs(inputs, material, phase, root, config, kind)
    try:
        _inputs(inputs, material, phase, root, config, kind)
    finally:
        _inputs(inputs, material, phase, root, config, kind)
'''
OUTER_WRAPPER = '''def _inputs_for_write(inputs_path, inputs_sha256, allocation_path, allocation_sha256, outer_sha256, phase, deadline, *, stage="fit", state=None, output=None):
    inputs, allocation, material = _inputs(inputs_path, inputs_sha256, allocation_path, allocation_sha256,
                                         outer_sha256, phase, deadline, stage=stage, state=state, output=output)
    if stage == "fit":
        config = fit.sequence.training_config(phase, inputs["model_path"], learner_seed=inputs["learner_seed"], device="cuda")
        fit.validate_predecessor_for_write(inputs, material, phase, output, config, "NATIVE")
    return inputs, allocation, material
'''
REPLACEMENT_OUTER = ORIGINAL_OUTER.replace('    _inputs(', '    _inputs_for_write(', 2) + OUTER_WRAPPER


class OverlayTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source, self.destination = self.root / 'old', self.root / 'new'
        self.original = self.source / api.RELATIVE
        self.original.parent.mkdir(parents=True)
        self.original.write_text(ORIGINAL_FIT)
        self.other = self.source / 'gpu/material.py'
        self.other.write_text('MATERIAL = "UNCHANGED"\n')
        (self.source / api.OUTER).write_text(ORIGINAL_OUTER)
        self.replacement = self.root / 'replacement.py'
        self.replacement.write_text(REPLACEMENT_FIT)
        self.outer_replacement = self.root / 'outer_replacement.py'
        self.outer_replacement.write_text(REPLACEMENT_OUTER)
        self.enterContext(patch.object(api, 'SOURCE', self.source))
        self.enterContext(patch.object(api, 'DESTINATION', self.destination))
        self.enterContext(patch.object(api, 'ORIGINAL_SHA', api.pin(self.original)['sha256']))
        self.enterContext(patch.object(api, 'OUTER_ORIGINAL_SHA', api.pin(self.source / api.OUTER)['sha256']))

    def build(self, commit='a' * 40):
        return api.build(self.replacement, commit, self.outer_replacement)

    def test_overlay_preserves_original_and_resolved_material_path(self):
        original = api.pin(self.original)
        receipt = self.build()
        self.assertTrue(Path(receipt['path']).is_file())
        self.assertEqual(api.pin(self.original), original)
        self.assertEqual((self.destination / 'gpu/material.py').resolve(), self.other)
        self.assertFalse((self.destination / api.RELATIVE).is_symlink())
        self.assertFalse((self.destination / api.OUTER).is_symlink())
        self.assertEqual((self.destination / api.OUTER).read_bytes(), self.outer_replacement.read_bytes())
        saved = json.loads(Path(receipt['path']).read_text())
        self.assertEqual(saved['outer_original'], api.pin(self.source / api.OUTER))
        self.assertEqual(saved['outer_replacement'], api.pin(self.destination / api.OUTER))
        self.assertEqual(saved['replacement'], api.pin(self.destination / api.RELATIVE))
        self.assertEqual(saved['scope'], operator.REPAIR_SCOPE)
        self.assertEqual((self.destination / api.RELATIVE).read_bytes(), self.replacement.read_bytes())
        with self.assertRaisesRegex(ValueError, 'fresh overlay'):
            self.build()

    def test_changed_other_code_refused_before_write(self):
        self.replacement.write_text(self.replacement.read_text() + '\nCHANGED = True\n')
        with self.assertRaisesRegex(ValueError, 'non-validator change'):
            self.build()
        self.assertFalse(self.destination.exists())

    def test_original_drift_refused(self):
        self.original.write_text(self.original.read_text() + '\n')
        with self.assertRaisesRegex(ValueError, 'frozen fit drift'):
            self.build()
        self.assertFalse(self.destination.exists())

    def test_full_commit_required(self):
        with self.assertRaisesRegex(ValueError, 'full committed'):
            self.build('ab1234')

    def test_original_outer_drift_refused(self):
        with (self.source / api.OUTER).open('a') as stream:
            stream.write('\n')
        with self.assertRaisesRegex(ValueError, 'frozen outer drift'):
            self.build()
        self.assertFalse(self.destination.exists())

    def test_both_validators_accept_exact_split_and_reject_other_edits(self):
        mutations = (
            REPLACEMENT_FIT + '\nCHANGED = True\n',
            REPLACEMENT_FIT.replace('root / "checkpoint"', 'root / "unused"'),
            REPLACEMENT_FIT.replace('if parent is not None:', 'if False:'),
            REPLACEMENT_FIT.replace('return validate_predecessor_for_write(', 'return validate_predecessor('),
            REPLACEMENT_FIT.replace('return validate_predecessor_for_write(inputs,', 'return validate_predecessor_for_write(None,'),
            REPLACEMENT_FIT.replace('def validate_predecessor(inputs,', 'def validate_predecessor(wrong,'),
            REPLACEMENT_FIT.replace('    return parent, prior, before', '    v3._warm_parent(parent, root / "unused", config)\n    return parent, prior, before', 1),
            REPLACEMENT_FIT + WRAPPER,
            REPLACEMENT_FIT.replace('def run_phase(', '@decorator\ndef run_phase('),
        )
        for validator in (api.validate_repair, operator.validate_repair):
            self.replacement.write_text(REPLACEMENT_FIT)
            validator(self.original, self.replacement)
            for mutation in mutations:
                with self.subTest(validator=validator.__module__, mutation=mutation):
                    self.replacement.write_text(mutation)
                    with self.assertRaises(ValueError):
                        validator(self.original, self.replacement)

    def test_outer_only_two_prefit_renames_and_exact_wrapper_permitted(self):
        for validator in (api.validate_repair, operator.validate_repair):
            self.outer_replacement.write_text(REPLACEMENT_OUTER)
            validator(self.source / api.OUTER, self.outer_replacement, outer=True)
            for mutation in (ORIGINAL_OUTER,
                             REPLACEMENT_OUTER.replace('fit.validate_predecessor(', 'fit.validate_predecessor_for_write('),
                             REPLACEMENT_OUTER.replace('for_write(inputs,', 'for_write(None,', 1),
                             REPLACEMENT_OUTER.replace('        _inputs(', '        _inputs_for_write(', 1),
                             REPLACEMENT_OUTER.replace('    _inputs_for_write(', '    _inputs(', 1),
                             REPLACEMENT_OUTER.replace('if stage == "fit":', 'if stage == "readout":'),
                             REPLACEMENT_OUTER.replace('return inputs, allocation, material', 'return inputs, material, allocation'),
                             REPLACEMENT_OUTER.replace('finally:', 'except Exception:'),
                             REPLACEMENT_OUTER.replace('fit.validate_predecessor(', 'fit.validate_predecessor( ', 1),
                             REPLACEMENT_OUTER.replace('    try:', '    unrelated()\n    try:'),
                             REPLACEMENT_OUTER + '\nCHANGED = True\n'):
                self.outer_replacement.write_text(mutation)
                with self.subTest(validator=validator.__module__, mutation=mutation), self.assertRaises(ValueError):
                    validator(self.source / api.OUTER, self.outer_replacement, outer=True)

    def test_bad_outer_replacement_refused_before_creation(self):
        self.outer_replacement.write_text(REPLACEMENT_OUTER + '\nCHANGED = True\n')
        with self.assertRaisesRegex(ValueError, 'explicit AST'):
            self.build()
        self.assertFalse(self.destination.exists())

    def test_runtime_loader_rechecks_postflight_boundary(self):
        binding = self.build()
        receipt = json.loads(Path(binding['path']).read_text())
        outer = self.destination / api.OUTER
        outer.write_text(REPLACEMENT_OUTER.replace('        _inputs(', '        _inputs_for_write(', 1))
        receipt['outer_replacement'] = api.pin(outer)
        Path(binding['path']).write_text(json.dumps(receipt))
        with patch.object(operator, 'SOURCE', self.source), patch.object(operator, 'REPAIR_SOURCE', self.destination):
            with self.assertRaisesRegex(ValueError, 'postflight must stay read-only'):
                operator.load_runtime(str(self.destination))

    def test_runtime_loader_rechecks_frozen_inventory(self):
        binding = self.build()
        receipt = json.loads(Path(binding['path']).read_text())
        receipt['original_inventory'].pop('gpu/material.py')
        Path(binding['path']).write_text(json.dumps(receipt))
        with patch.object(operator, 'SOURCE', self.source), patch.object(operator, 'REPAIR_SOURCE', self.destination):
            with self.assertRaisesRegex(ValueError, 'original inventory drift'):
                operator.load_runtime(str(self.destination))


if __name__ == '__main__':
    unittest.main()
