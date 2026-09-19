from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

import dispatch_sampling
import execution as common
import prepare_executable
from test_custody_repair import REPAIR
from test_execution import CANDIDATE, RECEIPT


def repair_fixture():
    repair = deepcopy(REPAIR)
    incarnation = common.digest(REPAIR)
    prior = common.CUSTODY_PARENT / incarnation
    repair.update(schema='C2_CUSTODY_REPAIR_EXECUTION_AUTHORIZATION_V3', repair_version=3,
        proof_only=False, model_execution_authorized=True,
        model_dispatch_requires_fresh_custody=True, preregistration=common.PREREGISTRATION,
        prior_root=str(prior), prior_execution_incarnation_sha256=incarnation,
        authorization='Main approves the exact preregistered diagnostic after fresh custody proof.')
    for name, reference in repair['prior_refs'].items():
        reference['path'] = str(prior / name)
    return repair


class MainRepairTests(unittest.TestCase):
    def test_empty_readonly_sources_are_outside_shared_view(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            view = root / 'view'
            view.mkdir()
            readonly = []
            prepare_executable.player_private_masks(root, view, readonly)
            self.assertEqual(len(readonly), 3)
            for binding in readonly:
                source = Path(binding['source'])
                target = Path(binding['target'])
                self.assertFalse(source.is_relative_to(view))
                self.assertEqual(target.parent, view)
                self.assertFalse(list(source.iterdir()))
                target.mkdir()
                (target / 'judge_created_placeholder').touch()
                self.assertFalse(list(source.iterdir()))

    def test_v3_identity_is_distinct_but_scientific_epoch_is_not_changed(self):
        original = common.registry(CANDIDATE, RECEIPT, REPAIR)
        candidate = common.registry(CANDIDATE, RECEIPT, repair_fixture())
        common.validate_registry(candidate)
        self.assertNotEqual(original['root'], candidate['root'])
        self.assertNotEqual(original['block_id'], candidate['block_id'])
        self.assertEqual(original['diagnostic_epoch'], candidate['diagnostic_epoch'])
        self.assertEqual(original['role_devices'], candidate['role_devices'])
        self.assertEqual(original['claims_namespace'], candidate['claims_namespace'])
        self.assertEqual(original['hard_end_unix'], candidate['hard_end_unix'])

    def test_v3_still_cannot_run_without_actual_bound_proof(self):
        candidate = common.registry(CANDIDATE, RECEIPT, repair_fixture())
        with self.assertRaisesRegex(ValueError, 'bound_file'):
            dispatch_sampling.run(candidate, {}, None, 'not-a-proof')

    def test_cannot_flip_v2_scope_to_allow_models(self):
        repair = deepcopy(REPAIR)
        repair.update(proof_only=False, model_execution_authorized=True)
        with self.assertRaisesRegex(ValueError, 'cpu_only'):
            common.registry(CANDIDATE, RECEIPT, repair)

    def test_cannot_remove_fresh_custody_or_change_preregistration(self):
        for changes in ({'model_dispatch_requires_fresh_custody': False},
                {'preregistration': {}}, {'model_execution_authorized': False}):
            with self.subTest(changes=changes):
                repair = repair_fixture()
                repair.update(changes)
                with self.assertRaisesRegex(ValueError, 'explicit_bound_model_scope'):
                    common.registry(CANDIDATE, RECEIPT, repair)

    def test_cannot_substitute_old_failed_root_or_unbound_execution(self):
        repair = repair_fixture()
        repair['prior_root'] = REPAIR['prior_root']
        with self.assertRaisesRegex(ValueError, 'bound_prior_failed'):
            common.registry(CANDIDATE, RECEIPT, repair)
        candidate = common.registry(CANDIDATE, RECEIPT, repair_fixture())
        candidate['proof_only'] = True
        with self.assertRaisesRegex(ValueError, 'bound_execution_scope'):
            common.validate_registry(candidate)


if __name__ == '__main__':
    unittest.main()
