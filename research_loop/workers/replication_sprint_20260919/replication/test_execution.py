"""Offline execution-path regressions; all services and model calls are mocked."""

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import construct_candidate as candidate
import dispatch_sampling as dispatch
import execution as common
import prepare_executable as prepare
import sealed_runner as role_runtime
import report_sampling as reporting


HERE = Path(__file__).resolve().parent
RECEIPT = common.read(HERE / 'ORIGINALS_RECEIPT.json')
CANDIDATE = common.read(HERE / 'C2_SAMPLING_CANDIDATE_V2.json')


def config_fixture(document, job):
    row = RECEIPT['rows'][job['arm']]
    config = deepcopy(row['config'])
    config.update(root=job['root'] + '/view', job_root=job['root'], block_root=document['root'],
        diagnostic_epoch_sha256=document['diagnostic_epoch_sha256'], diagnostic_epoch=document['diagnostic_epoch'],
        seeds=list(common.SEEDS), job_id=job['job_id'], job_identity=job['identity'], block_id=document['block_id'],
        original_config=deepcopy(row['config']), source_checkpoint=deepcopy(row['source_age']),
        preregistration=document['preregistration'], expected_scene_ids=document['expected_scene_ids'],
        original_parameter_identity=row['identity'], hard_end_unix=document['hard_end_unix'])
    config['identity']['condition'] = 'R233_SAMPLING_FIXTURE'
    return config


class ExecutionTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(dir=HERE)
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.registry = common.registry(CANDIDATE, RECEIPT)

    def test_new_ids_are_derived_and_original_history_preserved(self):
        common.validate_registry(self.registry)
        self.assertEqual(self.registry['original_no_retry_history'], RECEIPT['queue']['history'])
        self.assertEqual(len({job['job_id'] for job in self.registry['jobs']}), 3)
        old_ids = {row['job_id'] for row in RECEIPT['queue']['registry']['capsules']}
        self.assertFalse(old_ids & {job['job_id'] for job in self.registry['jobs']})
        self.assertEqual(self.registry, common.registry(CANDIDATE, RECEIPT))

    def test_rebinding_source_epoch_or_resource_is_rejected(self):
        for mutation in ('seed', 'job', 'lease', 'device'):
            changed = deepcopy(self.registry)
            if mutation == 'seed':
                changed['diagnostic_epoch']['sampling_seeds'] = [23201, 23202]
            elif mutation == 'job':
                changed['jobs'][0]['job_id'] = 'synthetic-other-job'
            elif mutation == 'lease':
                changed['hard_end_unix'] += 1
            else:
                changed['role_devices']['player']['physical'] = 0
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                common.validate_registry(changed)

    def test_shared_lock_excludes_concurrent_dispatch(self):
        with common.shared_lock(self.root):
            with self.assertRaises(BlockingIOError):
                with common.shared_lock(self.root):
                    self.fail('second dispatcher entered')

    def test_other_claim_blocks_without_partial_writes(self):
        now = time.time()
        devices = list(self.registry['role_devices'].values())
        path = self.root / (devices[1]['uuid'] + '.json')
        common.write_once(path, dict(job_id='synthetic-other-job', hold_until_unix=now + 100))
        original = path.read_bytes()
        with self.assertRaisesRegex(ValueError, 'existing_lane_claim'):
            common.reserve(self.registry, now + 1000, now, self.root)
        self.assertEqual(path.read_bytes(), original)
        self.assertFalse((self.root / (devices[0]['uuid'] + '.json')).exists())

    def test_expired_claim_archived_never_deleted(self):
        now = time.time()
        device = self.registry['role_devices']['player']
        path = self.root / (device['uuid'] + '.json')
        previous = dict(job_id='synthetic-old-job', hold_until_unix=now - 1)
        common.write_once(path, previous)
        with common.shared_lock(self.root):
            common.reserve(self.registry, now + 1000, now, self.root)
        archive = list(self.root.glob('*.expired.*.json'))
        self.assertEqual(len(archive), 1)
        self.assertEqual(common.read(archive[0]), previous)
        common.verify_claims(self.registry, now + 1000, self.root)

    def test_foreign_claim_never_adopted(self):
        now = time.time()
        common.reserve(self.registry, now + 1000, now, self.root)
        with self.assertRaisesRegex(ValueError, 'same_block_owns'):
            common.verify_claims(self.registry, now + 999, self.root)

    def test_denial_submitted_once_and_terminal(self):
        runner = Mock(return_value=SimpleNamespace(returncode=1))
        with self.assertRaisesRegex(ValueError, 'PLATFORM_DENIAL_TERMINAL'):
            common.terminal_submit(dict(argv=['synthetic-unit']), runner)
        runner.assert_called_once()

    def test_failed_or_unknown_units_never_resubmitted(self):
        for state in (dict(LoadState='not-found'), dict(LoadState='loaded', ActiveState='failed',
                Result='exit-code', ExecMainStatus='1')):
            observer = Mock(return_value=state)
            with self.subTest(state=state), self.assertRaises(ValueError):
                dispatch.wait_units([dict(unit='synthetic')], time.time() + 100, observer, lambda _: None)
            observer.assert_called_once()

    def test_completed_units_retained_for_unambiguous_review(self):
        state = dict(LoadState='loaded', ActiveState='active', SubState='exited',
            Result='success', ExecMainStatus='0')
        result = dispatch.wait_units([dict(unit='synthetic')], time.time() + 1,
            lambda _: state, lambda _: self.fail('completed unit polled again'))
        self.assertEqual(result, {'synthetic': state})

    def test_sealed_command_keeps_original_route_and_custody(self):
        job = self.registry['jobs'][0]
        mounts = {role: dict(readonly=[dict(source='/usr', target='/usr')],
            writable=[dict(source=job['root'] + '/view', target=job['root'] + '/view')])
            for role in ('player', 'judge')}
        now = time.time()
        with patch.object(common, 'read', return_value=mounts):
            spec = common.command(self.registry, job, 'player', 'proof', 'synthetic-config',
                'synthetic-launch', now + 1000, now)
        argv = spec['argv']
        self.assertEqual(argv[:3], ['sudo', '-n', 'systemd-run'])
        self.assertIn('--property=RootDirectory=' + job['root'] + '/rootfs_player', argv)
        self.assertIn('--property=MountAPIVFS=no', argv)
        self.assertIn('--property=PrivateNetwork=yes', argv)
        self.assertIn('--property=DevicePolicy=closed', argv)
        self.assertIn('--property=DeviceAllow=/dev/nvidia2 rw', argv)
        self.assertNotIn('--property=DeviceAllow=/dev/nvidia7 rw', argv)
        self.assertNotIn('--property=BindReadOnlyPaths=/proc', argv)

    def test_run_mounts_exact_main_review(self):
        job = self.registry['jobs'][0]
        mounts = {role: dict(readonly=[], writable=[]) for role in ('player', 'judge')}
        now = time.time()
        with patch.object(common, 'read', return_value=mounts), patch.object(common, 'sha', return_value='synthetic-review'):
            spec = common.command(self.registry, job, 'player', 'run', 'synthetic-config',
                'synthetic-launch', now + 1000, now)
        self.assertIn('--review-sha256', spec['argv'])
        self.assertIn('synthetic-review', spec['argv'])
        binds = next(value for value in spec['argv'] if value.startswith('--property=BindReadOnlyPaths='))
        self.assertIn('/GPU_REVIEW.json', binds)
        self.assertIn('/PROOFS_COMPLETE.json', binds)

    def test_config_retains_original_controls(self):
        config = config_fixture(self.registry, self.registry['jobs'][0])
        now = time.time()
        launch = dict(block_id=self.registry['block_id'],
            diagnostic_epoch_sha256=self.registry['diagnostic_epoch_sha256'],
            job_configs={config['job_id']: 'synthetic-config'}, created_unix=now - 1, deadline_unix=now + 1000)
        role_runtime.check_config(config, launch, 'synthetic-config')
        for name, value in (('parent_tokens', 1), ('training_updates', 1), ('seeds', [23201, 23202]),
                ('token_budget', 100), ('primary_config', '/different'),
                ('expected_scene_ids', ['other-scene']), ('preregistration', {'sha256': 'wrong'})):
            changed = deepcopy(config)
            changed[name] = value
            with self.subTest(name=name), self.assertRaises(ValueError):
                role_runtime.check_config(changed, launch, 'synthetic-config')

    def test_preregistration_exact_bytes_are_bound(self):
        repo = HERE.parents[3]
        common.regular(repo / common.PREREGISTRATION['repo_relative'], common.PREREGISTRATION['sha256'])
        changed = deepcopy(self.registry)
        changed['preregistration']['sha256'] = 'different-document'
        with self.assertRaisesRegex(ValueError, 'preregistered_document'):
            common.validate_registry(changed)

    def test_completion_rejects_unbound_scenes_and_short_cells(self):
        config = config_fixture(self.registry, self.registry['jobs'][0])
        identity = RECEIPT['rows']['base']['identity']
        fields = dict(diagnostic_epoch_sha256=config['diagnostic_epoch_sha256'],
            judge_epoch_sha256=candidate.ADOPTED_EPOCH, source_age=None, parent_tokens=0)
        loaded = dict(fields, identity=identity, snapshot_context_used=False)
        complete = dict(fields, actual_generated_tokens=6144, training_updates=0,
            unchanged_identity=RECEIPT['rows']['base']['unchanged_identity'],
            cells=[dict(contest_id=scene, seed=seed, generated_tokens=1024,
                status='COMPLETE_FIXED_ACTUAL_TOKEN_BUDGET')
                for scene in common.SCENE_IDS for seed in common.SEEDS])
        dispatch.validate_completion(config, complete, loaded)
        changed = deepcopy(complete)
        for cell in changed['cells']:
            cell['contest_id'] += '_unbound'
        with self.assertRaisesRegex(ValueError, 'pinned_manifest_scene_identity'):
            dispatch.validate_completion(config, changed, loaded)
        changed = deepcopy(complete)
        changed['cells'][0]['generated_tokens'] = 1023
        with self.assertRaisesRegex(ValueError, 'all_cells_complete'):
            dispatch.validate_completion(config, changed, loaded)

    def test_actual_device_and_private_denial_required(self):
        config = dict(expected_uid=1352, protected_policy={'receiving_boot_id': 'synthetic-boot'},
            custody_forbidden=['/synthetic/host'], player_private_paths=['/synthetic/private'],
            role_devices=self.registry['role_devices'])
        def opened(path, flags):
            if path == '/dev/nvidia2':
                return 123
            raise PermissionError()
        with patch.object(role_runtime.os, 'getuid', return_value=1352), \
                patch.object(Path, 'read_text', return_value='synthetic-boot'), \
                patch.object(role_runtime, 'denial', return_value=True), \
                patch.object(role_runtime.os, 'open', side_effect=opened), \
                patch.object(role_runtime.os, 'close'), \
                patch.dict(role_runtime.os.environ, CUDA_VISIBLE_DEVICES=self.registry['role_devices']['player']['uuid']):
            proof = role_runtime.custody(config, 'player')
            self.assertEqual(sum(value['opened'] for value in proof['device_opens'].values()), 1)
            with patch.object(role_runtime, 'denial', return_value=False):
                with self.assertRaisesRegex(ValueError, 'private_paths'):
                    role_runtime.custody(config, 'player')

    def test_public_readable_file_is_not_a_denial(self):
        path = self.root / 'synthetic.txt'
        path.write_text('not private')
        self.assertFalse(role_runtime.denial(path))
        self.assertTrue(role_runtime.denial(self.root / 'absent'))

    def test_rootfs_has_no_host_proc_tree(self):
        root = self.root / 'rootfs'
        prepare.skeleton(root)
        self.assertEqual(list((root / 'proc').iterdir()), [])
        self.assertTrue((root / 'bin').is_symlink())

    def test_prepared_player_view_excludes_private_panel_mounts(self):
        original = self.root / 'original'
        original.mkdir()
        row = deepcopy(RECEIPT['rows']['base'])
        row['root'] = str(original)
        for name in ('GAME_MANIFEST.json', 'SELECTION.json', 'SOURCE_MANIFEST.json', 'FRESHNESS_VERIFIED.json'):
            contents = dict(contests=[dict(contest_id=scene) for scene in common.SCENE_IDS]) \
                if name == 'GAME_MANIFEST.json' else {'synthetic': True}
            common.write_once(original / name, contents)
        document = deepcopy(self.registry)
        document['root'] = str(self.root / 'block')
        (Path(document['root']) / 'jobs').mkdir(parents=True)
        job = dict(document['jobs'][0], root=str(Path(document['root']) / 'jobs' / document['jobs'][0]['job_id']))
        def append_mount(rows, source, target=None):
            rows.append(dict(source=str(source), target=str(target or source)))
        primary = dict(base_model={'path': '/synthetic/model_manifest'},
            adapter={'adapter_model.safetensors': {'path': '/synthetic/adapter_model.safetensors'}})
        with patch.object(prepare, 'source_verified', return_value=primary), \
                patch.object(prepare, 'backbone_directory', return_value=Path('/synthetic/cache/snapshots/revision')), \
                patch.object(prepare, 'add_mount', side_effect=append_mount):
            result = prepare.make_job(document, job, row, {'synthetic.py': 'synthetic-hash'})
        config = common.read(Path(job['root']) / 'CONFIG.json')
        mounts = common.read(Path(job['root']) / 'MOUNTS.json')
        self.assertEqual(result['mounts_sha256'], common.sha(Path(job['root']) / 'MOUNTS.json'))
        self.assertEqual(config['mounts_sha256'], result['mounts_sha256'])
        for entry in mounts['player']['readonly']:
            self.assertNotIn('REFERENCE_PANELS.private.json', entry['source'])
            self.assertNotIn('PRIMARY_PANELS.private.json', entry['source'])
            self.assertNotEqual(entry['source'], str(original))
        self.assertIn(str(Path(job['root']) / 'CONFIG.json'),
            [entry['source'] for entry in mounts['player']['readonly']])
        self.assertTrue(any('REFERENCE_PANELS.private.json' in entry['source']
            for entry in mounts['judge']['readonly']))

    def test_backbone_uses_bound_manifest_root_not_obsolete_file_reference_paths(self):
        cache = self.root / 'cache'
        revision = 'a09a35458c702b33eeacc393d103063234e8bc28'
        snapshot = cache / 'snapshots' / revision
        snapshot.mkdir(parents=True)
        manifest = self.root / 'base_manifest.json'
        common.write_once(manifest, dict(model_id='Qwen/Qwen2.5-7B-Instruct', revision=revision,
            root=str(snapshot), files={'config.json': {'path': '/obsolete/path'}}))
        primary = dict(base_model=dict(path=str(manifest), sha256=common.sha(manifest)))
        with patch.object(prepare, 'HF_REPO', cache):
            self.assertEqual(prepare.backbone_directory(primary), snapshot)
        with patch.object(prepare, 'HF_REPO', self.root / 'different-cache'):
            with self.assertRaisesRegex(ValueError, 'pinned_snapshot'):
                prepare.backbone_directory(primary)

    def partial_stage(self):
        root = self.root / 'partial'
        root.mkdir()
        common.write_once(root / 'SOURCE_FREEZE.json', {'synthetic': 'old release'})
        common.write_once(root / 'REGISTRY.json', self.registry)
        return root

    def test_partial_stage_preserved_with_exact_tree_before_new_preparation(self):
        root = self.partial_stage()
        snapshot = prepare.unlaunched_inventory(root)
        result = prepare.preserve_unlaunched(root, self.registry, snapshot['source_freeze_sha256'],
            snapshot['tree_sha256'], self.root)
        self.assertFalse(root.exists())
        archive = Path(result['archive'])
        self.assertTrue(archive.is_dir())
        self.assertEqual(common.sha(archive / 'SOURCE_FREEZE.json'), snapshot['source_freeze_sha256'])
        self.assertTrue((archive / 'UNLAUNCHED_STAGING_PRESERVED.json').is_file())

    def test_prepared_or_attempted_stage_cannot_be_repaired(self):
        root = self.partial_stage()
        common.write_once(root / 'BLOCK_LAUNCH.json', {'synthetic': 'attempted'})
        with self.assertRaisesRegex(ValueError, 'not_an_unlaunched'):
            prepare.unlaunched_inventory(root)

    def test_changed_tree_or_own_claim_cannot_be_reprepared(self):
        root = self.partial_stage()
        snapshot = prepare.unlaunched_inventory(root)
        with self.assertRaisesRegex(ValueError, 'exact_failed_staging_tree'):
            prepare.preserve_unlaunched(root, self.registry, snapshot['source_freeze_sha256'], 'wrong', self.root)
        claim = self.root / (self.registry['role_devices']['player']['uuid'] + '.json')
        common.write_once(claim, dict(job_id=self.registry['block_id']))
        with self.assertRaisesRegex(ValueError, 'already_claimed'):
            prepare.preserve_unlaunched(root, self.registry, snapshot['source_freeze_sha256'],
                snapshot['tree_sha256'], self.root)
        self.assertTrue(root.exists())


class TaggedReuseTests(unittest.TestCase):
    def test_original_function_code_reused_without_mutating_module(self):
        def player(config):
            return 'unused'
        original = SimpleNamespace(player=player, runtime=object(), epoch=SimpleNamespace(SEEDS=(23201, 23202)))
        config = dict(diagnostic_epoch_sha256='synthetic-epoch', root='/synthetic')
        wrapped = role_runtime.wrapped_role(original, config, 'player')
        self.assertIs(wrapped.__code__, player.__code__)
        self.assertEqual(original.epoch.SEEDS, (23201, 23202))
        self.assertEqual(wrapped.__globals__['epoch'].SEEDS, common.SEEDS)

    def test_request_tags_participate_in_request_hash(self):
        written = []
        original = SimpleNamespace(write=lambda path, value: written.append(deepcopy(value)))
        runtime = role_runtime.TaggedRuntime(original, 'synthetic-epoch', '/synthetic/job')
        request = dict(raw='caption', origin={'stage': 'ACT'})
        runtime.write(Path('/synthetic/job/queue/request.json'), request)
        self.assertEqual(common.digest(request), common.digest(written[0]))
        self.assertEqual(request['diagnostic_epoch_sha256'], 'synthetic-epoch')

    def test_tagging_does_not_change_feedback_text(self):
        original = SimpleNamespace(write=lambda path, value: None)
        runtime = role_runtime.TaggedRuntime(original, 'synthetic-epoch', '/synthetic/job')
        reply = dict(feedback='Caption 1: rank 25 of 65; accepted True.', results=[])
        feedback = reply['feedback']
        runtime.write(Path('/synthetic/job/reply.json'), reply)
        self.assertEqual(reply['feedback'], feedback)

    def test_other_diagnostic_cannot_supply_feedback(self):
        original = SimpleNamespace(wait=lambda path, deadline: dict(diagnostic_epoch_sha256='another-epoch'))
        runtime = role_runtime.TaggedRuntime(original, 'synthetic-epoch', '/synthetic/job')
        with self.assertRaisesRegex(ValueError, 'same_diagnostic_reply'):
            runtime.wait('/synthetic/job/reply.json', time.time() + 1)

    def test_writer_cannot_modify_original_or_other_roots(self):
        writer = Mock()
        runtime = role_runtime.TaggedRuntime(SimpleNamespace(write=writer), 'synthetic', '/synthetic/job')
        with self.assertRaisesRegex(ValueError, 'job_local_output'):
            runtime.write('/original/result.json', {})
        writer.assert_not_called()

    def test_backend_checks_decoder_libraries_and_tokenizer_before_generation(self):
        expected = RECEIPT['rows']['base']['identity']
        backend = SimpleNamespace(identity=deepcopy(expected))
        original = SimpleNamespace(Backend=lambda source, root: backend)
        runtime = role_runtime.TaggedRuntime(original, 'synthetic', '/synthetic/job', expected)
        self.assertIs(runtime.Backend(None, '/synthetic/job'), backend)
        backend.identity['tokenizer_backend_sha256'] = 'synthetic-wrong-tokenizer'
        with self.assertRaisesRegex(ValueError, 'original_backend_identity:tokenizer'):
            runtime.Backend(None, '/synthetic/job')


class ReportingTests(unittest.TestCase):
    def test_dedup_and_rankless_rejections_are_not_provider_failures(self):
        accepted = dict(caption_sha256='synthetic-caption', result=dict(rank=50, accepted=True, status='new_pixel'))
        rejected = dict(caption_sha256='synthetic-rejection', result=dict(rank=None, accepted=False,
            status='injection_detected'))
        events = [dict(origin={'stage': 'ACT'}, score={'results': [accepted, accepted, rejected]}),
            dict(origin={'stage': 'THINK'}, score={'results': []}),
            dict(origin={'stage': 'ACT'}, score={'results': []})]
        result = reporting.summarize([dict(contest_id='synthetic-scene', generated_tokens=1024, events=events)])
        self.assertEqual((result['distinct_scored'], result['distinct_accepted'], result['new_pixels']), (1, 1, 1))
        self.assertEqual(result['rankless_by_status'], {'injection_detected': 1})
        self.assertEqual(result['acts_without_results'], 1)
        self.assertEqual((result['think_events'], result['act_attempts']), (1, 2))

    def test_empty_summary_has_unknown_accept_rate(self):
        self.assertIsNone(reporting.summarize([])['accept_rate'])

    def test_missing_cells_are_reported_for_every_arm_not_scored_as_zero(self):
        document = common.registry(CANDIDATE, RECEIPT)
        root = Path(document['root'])
        prepared = dict(registry_sha256='synthetic', jobs=[dict(job_id=job['job_id'], config_sha256='synthetic')
            for job in document['jobs']])
        files = {root / 'REGISTRY.json': document, root / 'PREPARED.json': prepared}
        for job in document['jobs']:
            config = config_fixture(document, job)
            config['condition'] = config['identity']['condition']
            files[Path(job['root']) / 'CONFIG.json'] = config
        with patch.object(common, 'read', side_effect=lambda path: files[path]), \
                patch.object(common, 'regular'), patch.object(Path, 'exists', return_value=False):
            result = reporting.report(root)
        self.assertEqual(len(result['rows']), 6)
        self.assertTrue(all(row['status'] == 'INCOMPLETE' and row['actual_generated_tokens'] is None
            and row['missing_cells'] == 3 for row in result['rows']))

    def test_present_incomplete_cell_keeps_all_rows_and_partial_evidence(self):
        document = common.registry(CANDIDATE, RECEIPT)
        root = Path(document['root'])
        prepared = dict(registry_sha256='synthetic', jobs=[dict(job_id=job['job_id'], config_sha256='synthetic')
            for job in document['jobs']])
        files = {root / 'REGISTRY.json': document, root / 'PREPARED.json': prepared}
        for job in document['jobs']:
            config = config_fixture(document, job)
            config['condition'] = config['identity']['condition']
            files[Path(job['root']) / 'CONFIG.json'] = config
        job = document['jobs'][0]
        config = files[Path(job['root']) / 'CONFIG.json']
        partial = Path(config['root']) / 'players' / config['condition'] / f'{common.SCENE_IDS[0]}_23301/RESULT.json'
        files[partial] = dict(diagnostic_epoch_sha256=document['diagnostic_epoch_sha256'], contest_id=common.SCENE_IDS[0],
            seed=23301, status='INCOMPLETE_ZERO_TOKEN_GENERATION', generated_tokens=128, events=[])
        with patch.object(common, 'read', side_effect=lambda path: files[path]), patch.object(common, 'regular'), \
                patch.object(common, 'sha', return_value='synthetic'), \
                patch.object(Path, 'exists', lambda path: path == partial):
            result = reporting.report(root)
        self.assertEqual(len(result['rows']), 6)
        first = result['rows'][0]
        self.assertIsNone(first['actual_generated_tokens'])
        self.assertEqual((first['missing_cells'], first['incomplete_present_cells']), (2, 1))
        self.assertEqual(first['cells'][0]['observed_generated_tokens'], 128)


if __name__ == '__main__':
    unittest.main()
