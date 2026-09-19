"""CPU repair diagnostics and dead-claim disposition, without real service calls."""

from copy import deepcopy
import ast
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

import dispatch_sampling as dispatch
import execution as common
import release_failed_claims as release
import sealed_runner
from test_execution import CANDIDATE, RECEIPT, HERE, config_fixture


REPAIR = common.read(HERE / 'CPU_CUSTODY_REPAIR_V2.json')


class RepairTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=HERE)
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.document = common.registry(CANDIDATE, RECEIPT, REPAIR)

    def test_distinct_cpu_root_jobs_units_keep_scientific_identity(self):
        common.validate_registry(self.document)
        original = common.registry(CANDIDATE, RECEIPT)
        self.assertNotEqual(self.document['root'], original['root'])
        self.assertNotEqual(self.document['block_id'], original['block_id'])
        self.assertEqual(self.document['diagnostic_epoch'], original['diagnostic_epoch'])
        self.assertEqual(self.document['claims_namespace'], original['claims_namespace'])
        self.assertTrue(self.document['proof_only'])
        self.assertFalse(set(job['job_id'] for job in original['jobs'])
            & set(job['job_id'] for job in self.document['jobs']))

    def test_cpu_incarnation_cannot_construct_or_dispatch_model_run(self):
        with self.assertRaisesRegex(ValueError, 'cannot_load_models'):
            common.command(self.document, self.document['jobs'][0], 'player', 'run', 'synthetic',
                'synthetic', time.time() + 500, time.time())
        with self.assertRaisesRegex(ValueError, 'cannot_load_models'):
            dispatch.run(self.document, {}, object(), 'synthetic')

    def test_cpu_cannot_be_relabelled_for_science(self):
        changed = deepcopy(self.document)
        changed['proof_only'] = False
        with self.assertRaises(ValueError):
            common.validate_registry(changed)

    def test_player_mounts_private_directories_inaccessible(self):
        mounts = {role: dict(readonly=[], writable=[]) for role in ('player', 'judge')}
        with patch.object(common, 'read', return_value=mounts):
            player = common.command(self.document, self.document['jobs'][0], 'player', 'proof',
                'synthetic', 'synthetic', time.time() + 500, time.time())
            judge = common.command(self.document, self.document['jobs'][0], 'judge', 'proof',
                'synthetic', 'synthetic', time.time() + 500, time.time())
        guard = next(argument for argument in player['argv'] if argument.startswith('--property=InaccessiblePaths='))
        self.assertIn('/view/judge', guard)
        self.assertIn('/view/epoch', guard)
        self.assertIn('/view/assets', guard)
        self.assertFalse(any(argument.startswith('--property=InaccessiblePaths=') for argument in judge['argv']))

    def test_failed_path_is_reported_without_relaxing_custody(self):
        config = dict(expected_uid=1352, protected_policy={'receiving_boot_id': 'synthetic-boot'},
            custody_forbidden=['/synthetic/host-secret'], player_private_paths=['/synthetic/panel'],
            diagnostic_config_sha256='synthetic-config', diagnostic_epoch_sha256='synthetic-epoch')
        diagnostic = self.root / 'PATHS.json'
        with patch.object(sealed_runner.os, 'getuid', return_value=1352), \
                patch.object(Path, 'read_text', return_value='synthetic-boot'), \
                patch.object(sealed_runner, 'denial', side_effect=[True, False]):
            with self.assertRaisesRegex(ValueError, 'private_paths'):
                sealed_runner.custody(config, 'player', diagnostic)
        report = common.read(diagnostic)
        self.assertFalse(report['private_denials']['/synthetic/panel'])
        self.assertFalse(report['model_loaded'])

    def test_original_encoder_has_no_sentence_transformers_package_dependency(self):
        source = HERE.parents[3] / 'gpu/ny_caption_similarity.py'
        self.assertEqual(common.sha(source), RECEIPT['rows']['base']['source_closure']['gpu/ny_caption_similarity.py'])
        tree = ast.parse(source.read_text())
        encoder = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'FrozenCPUEncoder')
        imported = []
        for node in ast.walk(encoder):
            if isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported.append(node.module)
        self.assertIn('torch', imported)
        self.assertIn('transformers', imported)
        self.assertNotIn('sentence_transformers', imported)

    def test_fresh_cpu_claims_still_refuse_held_failed_claim(self):
        observation = REPAIR['claim_observation']
        for uuid in observation['claims']:
            common.write_once(self.root / (uuid + '.json'), dict(job_id=observation['job_id'],
                hold_until_unix=time.time() + 1000))
        with self.assertRaisesRegex(ValueError, 'existing_lane_claim'):
            common.reserve(self.document, time.time() + 500, time.time(), self.root)
        self.assertFalse(list(self.root.glob('*.expired.*')))

    def test_cpu_incarnation_has_its_own_bound_config(self):
        config = config_fixture(self.document, self.document['jobs'][0])
        config.update(proof_only=True, cpu_repair=REPAIR,
            execution_incarnation_sha256=self.document['execution_incarnation_sha256'])
        launch = dict(block_id=self.document['block_id'], diagnostic_epoch_sha256=self.document['diagnostic_epoch_sha256'],
            job_configs={config['job_id']: 'synthetic'}, created_unix=time.time() - 1, deadline_unix=time.time() + 500)
        sealed_runner.check_config(config, launch, 'synthetic')
        config['execution_incarnation_sha256'] = 'other'
        with self.assertRaisesRegex(ValueError, 'bound_cpu_incarnation'):
            sealed_runner.check_config(config, launch, 'synthetic')


class ClaimTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=HERE)
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.repair = deepcopy(REPAIR)
        self.evidence = dict(block_id=REPAIR['claim_observation']['job_id'], no_models=True)
        for uuid, reference in self.repair['claim_observation']['claims'].items():
            claim = dict(job_id=self.evidence['block_id'], created_unix=REPAIR['claim_observation']['created_unix'],
                hold_until_unix=REPAIR['claim_observation']['hold_until_unix'],
                diagnostic_epoch_sha256=REPAIR['diagnostic_epoch_sha256'])
            path = self.root / (uuid + '.json')
            common.write_once(path, claim)
            reference['sha256'] = common.sha(path)
        self.repair['prior_refs'] = {}

    def test_check_never_renames_claims(self):
        result = release.disposition(self.repair, namespace=self.root, audit_parent=self.root / 'audits',
            auditor=lambda _: self.evidence)
        self.assertEqual(result['status'], 'VERIFIED_DEAD_CPU_PROOF_CLAIMS_NOT_RELEASED')
        self.assertEqual(len(list(self.root.glob('GPU-*.json'))), 2)
        self.assertFalse((self.root / 'audits').exists())

    def test_verified_dead_claims_preserved_byte_for_byte(self):
        auditor = Mock(return_value=self.evidence)
        result = release.disposition(self.repair, True, self.root, self.root / 'audits', auditor)
        auditor.assert_called_once()
        self.assertEqual(result['status'], 'DEAD_CPU_PROOF_CLAIMS_ARCHIVED_GUARDS_PRESERVED')
        for uuid, reference in self.repair['claim_observation']['claims'].items():
            self.assertFalse((self.root / (uuid + '.json')).exists())
            archive = self.root / (uuid + '.failed.' + self.evidence['block_id'] + '.json')
            self.assertEqual(common.sha(archive), reference['sha256'])
        self.assertTrue((Path(result['audit_root']) / 'COMPLETE.json').exists())

    def test_changed_claim_or_active_audit_blocks_all_renames(self):
        auditor = Mock(side_effect=ValueError('still active'))
        with self.assertRaisesRegex(ValueError, 'still active'):
            release.disposition(self.repair, True, self.root, self.root / 'audits', auditor)
        reference = next(iter(self.repair['claim_observation']['claims'].values()))
        reference['sha256'] = 'synthetic-wrong-hash'
        with self.assertRaisesRegex(ValueError, 'bound_file'):
            release.disposition(self.repair, True, self.root, self.root / 'audits', lambda _: self.evidence)
        self.assertEqual(len(list(self.root.glob('GPU-*.json'))), 2)
        self.assertFalse(list(self.root.glob('*.failed.*')))

    def test_audit_runs_under_original_style_shared_lock(self):
        def auditor(repair):
            with self.assertRaises(BlockingIOError):
                with common.shared_lock(self.root):
                    self.fail('concurrent lock acquired')
            return self.evidence
        release.disposition(self.repair, namespace=self.root, auditor=auditor)

    def test_owned_unit_requires_exact_argv_identity_and_terminal_state(self):
        expected = dict(unit='synthetic.service', argv=[str(common.PYTHON), '-B', '/synthetic/runner.py', '--mode', 'proof'])
        state = dict(Id='synthetic.service', LoadState='loaded', Transient='yes', User='1352', Group='1352',
            InvocationID='synthetic-invocation', ActiveState='failed', SubState='failed', MainPID='0', ControlPID='0',
            Result='exit-code', ExecMainPID='123',
            ExecStart='{ path=' + str(common.PYTHON) + ' ; argv[]=' + ' '.join(expected['argv']) + ' ; ignore_errors=no }')
        release.validate_unit(state, expected)
        for key, value in (('MainPID', '123'), ('User', '0'), ('ActiveState', 'active'),
                ('ExecStart', state['ExecStart'].replace('--mode proof', '--mode run'))):
            changed = dict(state, **{key: value})
            with self.subTest(key=key), self.assertRaises(ValueError):
                release.validate_unit(changed, expected)


if __name__ == '__main__':
    unittest.main()
