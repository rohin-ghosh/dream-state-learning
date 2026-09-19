"""CPU-only preparation of a new diagnostic; never submit a unit or claim a GPU."""

import argparse
from copy import deepcopy
import os
from pathlib import Path
import shutil
import time

import execution as common
from construct_candidate import build, require, sha


HERE = Path(__file__).resolve().parent
HF_REPO = common.BASE / '.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct'


def add_mount(rows, source, target=None):
    source = Path(source)
    require(source.exists(), 'mount_source_exists:' + str(source))
    rows.append(dict(source=common.path_text(source), target=common.path_text(target or source)))


def skeleton(root):
    root.mkdir()
    for name in ('usr', 'etc', 'dev', 'proc', 'sys', 'tmp', 'localhome'):
        (root / name).mkdir()
    for name in ('bin', 'sbin', 'lib', 'lib64'):
        (root / name).symlink_to('usr/' + name)


def source_verified(row):
    original = Path(row['root'])
    for name in ('CONFIG.json', 'CONDITION.json', 'FRESHNESS_VERIFIED.json', 'SOURCE_MANIFEST.json',
            'GAME_MANIFEST.json', 'SELECTION.json'):
        common.regular(original / name, row['files'][name]['sha256'])
    exposure = common.read(original / 'FRESHNESS_VERIFIED.json')
    require(exposure['eligible'] is True, 'recorded_exposure_eligible')
    manifest = common.read(original / 'SOURCE_MANIFEST.json')
    require(manifest == row['source_closure'], 'same_source_manifest')
    for name, expected in manifest.items():
        common.regular(original / 'source' / name, expected)
    if row['source_age']:
        for name, ref in row['source_age']['copy_files'].items():
            common.regular(original / 'sources' / row['source_age']['source_relative'] / name, ref['sha256'])
    for name in ('JUDGE_EPOCH.json', 'PRIMARY_PANELS.private.json'):
        common.regular(Path(row['files'][name]['path']), row['files'][name]['sha256'])
    primary = common.read(row['config']['primary_config'])
    common.regular(Path(row['config']['primary_config']), row['config']['primary_config_sha256'])
    common.regular(Path(primary['base_model']['path']), primary['base_model']['sha256'])
    for ref in primary['adapter'].values():
        common.regular(Path(ref['path']), ref['sha256'])
    return primary


def backbone_directory(primary):
    reference = primary['base_model']
    common.regular(Path(reference['path']), reference['sha256'])
    manifest = common.read(reference['path'])
    require(manifest['model_id'] == 'Qwen/Qwen2.5-7B-Instruct'
        and manifest['revision'] == 'a09a35458c702b33eeacc393d103063234e8bc28', 'same_pinned_scalar_backbone')
    root = Path(manifest['root'])
    require(root.is_dir() and root.parent.name == 'snapshots'
        and root.parent.parent == HF_REPO and root.name == manifest['revision'], 'pinned_snapshot_inside_existing_cache_bind')
    require(root.resolve().is_relative_to(HF_REPO.resolve()), 'scalar_backbone_no_escape')
    return root


def player_private_masks(root, view, readonly):
    for name in ('judge', 'epoch', 'assets'):
        empty = root / ('player_empty_' + name)
        empty.mkdir(mode=0o700)
        add_mount(readonly, empty, view / name)


def unlaunched_inventory(root):
    require(root.is_dir() and not root.is_symlink(), 'existing_regular_staging_root')
    forbidden = ('PREPARED.json', 'BLOCK_LAUNCH.json', 'BLOCK_FAILED.json', 'PROOFS_COMPLETE.json',
        'GPU_REVIEW.json', 'BLOCK_COMPLETE.json')
    require(not any((root / name).exists() for name in forbidden), 'not_an_unlaunched_partial_stage')
    rows = []
    for path in sorted(root.rglob('*')):
        relative = path.relative_to(root)
        require(path.name not in ('DISPATCH_INTENT.json', 'COMPLETION_VERIFIED.json')
            and not any(token in path.name for token in ('STARTED', 'FAILED', 'CUSTODY_PROOF', '.log', '.request.', '.result.')),
            'execution_evidence_blocks_staging_repair')
        if path.is_symlink():
            rows.append(dict(path=str(relative), kind='symlink', target=str(path.readlink())))
        elif path.is_dir():
            rows.append(dict(path=str(relative), kind='directory'))
        else:
            require(path.is_file() and path.stat().st_size < 4_194_304
                and not ({'players', 'queue'} & set(relative.parts)), 'only_small_unexecuted_staging_files')
            rows.append(dict(path=str(relative), kind='file', bytes=path.stat().st_size, sha256=sha(path)))
    require(len(rows) < 2000, 'bounded_staging_inventory')
    return dict(root=str(root), files=rows, tree_sha256=common.digest(rows),
        source_freeze_sha256=sha(root / 'SOURCE_FREEZE.json'),
        registry_sha256=sha(root / 'REGISTRY.json'), no_execution_markers=True)


def preserve_unlaunched(root, document, old_freeze_sha, tree_sha, namespace=common.CLAIMS):
    require(old_freeze_sha and tree_sha, 'explicit_old_freeze_and_tree_required')
    snapshot = unlaunched_inventory(root)
    require(snapshot['source_freeze_sha256'] == old_freeze_sha
        and snapshot['tree_sha256'] == tree_sha, 'exact_failed_staging_tree')
    require(common.read(root / 'REGISTRY.json') == document, 'same_diagnostic_not_new_source_attempt')
    for device in document['role_devices'].values():
        path = Path(namespace) / (device['uuid'] + '.json')
        if path.exists():
            require(common.read(path)['job_id'] != document['block_id'], 'already_claimed_diagnostic_cannot_be_reprepared')
    archive = root.with_name(root.name + '.unlaunched.' + old_freeze_sha)
    require(not archive.exists(), 'failed_staging_archive_never_overwritten')
    root.rename(archive)
    preservation = dict(status='CPU_STAGE_FAILED_PRESERVED_NO_DISPATCH', snapshot=snapshot,
        archive=str(archive), observed_unix=time.time(), diagnostic_epoch_sha256=document['diagnostic_epoch_sha256'],
        original_attempt_guards_reused=False)
    common.write_once(archive / 'UNLAUNCHED_STAGING_PRESERVED.json', preservation)
    return preservation


def make_job(document, job, row, runtime_manifest):
    root = Path(job['root'])
    view = root / 'view'
    root.mkdir()
    view.mkdir()
    for name in ('source', 'assets', 'judge', 'epoch', 'queue', 'players', 'sources'):
        (view / name).mkdir()
    original = Path(row['root'])
    primary = source_verified(row)
    identity = deepcopy(row['config']['identity'])
    identity['condition'] = 'R233_SAMPLING_' + job['arm'] + '_' + document['diagnostic_epoch_sha256'][:12]
    common.write_once(view / 'CONDITION.json', identity)
    for name in ('GAME_MANIFEST.json', 'SELECTION.json', 'SOURCE_MANIFEST.json', 'FRESHNESS_VERIFIED.json'):
        shutil.copyfile(original / name, view / name)
    require(tuple(sorted(scene['contest_id'] for scene in common.read(view / 'GAME_MANIFEST.json')['contests']))
        == common.SCENE_IDS, 'exact_original_manifest_scenes')
    if row['source_age']:
        shutil.copyfile(original / 'sources/CAPTURE.json', view / 'sources/CAPTURE.json')
        relative = row['source_age']['source_relative']
        (view / 'sources' / relative).mkdir()
        (view / 'sources' / relative / 'adapter').mkdir()
    config = deepcopy(row['config'])
    config.update(root=str(view), identity=identity, seeds=list(common.SEEDS), epoch_root=str(view / 'epoch'),
        diagnostic_epoch_sha256=document['diagnostic_epoch_sha256'], diagnostic_epoch=document['diagnostic_epoch'],
        job_id=job['job_id'], job_identity=job['identity'], block_id=document['block_id'],
        block_root=document['root'], job_root=str(root),
        condition=identity['condition'], source_checkpoint=row['source_age'],
        original_files=row['files'], original_root=row['root'], original_config=row['config'],
        original_source_closure=row['source_closure'], original_parameter_identity=row['identity'],
        preregistration=document['preregistration'], expected_scene_ids=document['expected_scene_ids'],
        proof_only=document.get('proof_only', False), cpu_repair=document.get('cpu_repair'),
        execution_incarnation_sha256=document.get('execution_incarnation_sha256'),
        public_files={str(path.relative_to(view)): sha(path) for path in view.rglob('*') if path.is_file()},
        runtime_files=runtime_manifest, protected_policy=document['original_policy'],
        role_devices=document['role_devices'], max_runtime_seconds=2400,
        hard_end_unix=document['hard_end_unix'], expected_uid=document['original_policy']['expected_uid'])
    config.pop('deadline_unix')
    mounts = {}
    for role in ('judge', 'player'):
        readonly, writable = [], []
        for source in ('/usr', '/etc/ld.so.cache', '/etc/passwd', '/etc/group', '/sys',
                '/proc/sys/kernel/random/boot_id', '/proc/cpuinfo', '/proc/meminfo'):
            add_mount(readonly, source)
        if Path('/proc/driver/nvidia').exists():
            add_mount(readonly, '/proc/driver/nvidia')
        add_mount(readonly, common.BASE / 'v2/venv')
        add_mount(readonly, HF_REPO)
        add_mount(readonly, Path(document['root']) / 'runtime')
        add_mount(readonly, view / 'CONDITION.json')
        for name in ('GAME_MANIFEST.json', 'SELECTION.json', 'SOURCE_MANIFEST.json', 'FRESHNESS_VERIFIED.json'):
            add_mount(readonly, view / name)
        add_mount(readonly, original / 'source', view / 'source')
        if row['source_age']:
            add_mount(readonly, view / 'sources/CAPTURE.json')
            for name in row['source_age']['copy_files']:
                path = Path('sources') / row['source_age']['source_relative'] / name
                add_mount(readonly, original / path, view / path)
        if role == 'judge':
            add_mount(readonly, original / 'assets', view / 'assets')
            add_mount(readonly, original / 'judge/REFERENCE_PANELS.private.json', view / 'judge/REFERENCE_PANELS.private.json')
            for name in ('JUDGE_EPOCH.json', 'PRIMARY_PANELS.private.json'):
                add_mount(readonly, Path(row['files'][name]['path']), view / 'epoch' / name)
            backbone_directory(primary)
            add_mount(readonly, row['config']['primary_config'])
            add_mount(readonly, primary['base_model']['path'])
            for ref in primary['adapter'].values():
                add_mount(readonly, ref['path'])
        add_mount(writable, view)
        if role == 'player':
            player_private_masks(root, view, readonly)
        device = document['role_devices'][role]
        for name in ('/dev/nvidia' + str(device['physical']), '/dev/nvidiactl', '/dev/nvidia-uvm',
                '/dev/nvidia-uvm-tools', '/dev/null', '/dev/zero', '/dev/random', '/dev/urandom'):
            add_mount(writable, name)
        skeleton(root / ('rootfs_' + role))
        for path in (root / 'CONFIG.json', Path(document['root']) / 'REGISTRY.json',
                Path(document['root']) / 'BLOCK_LAUNCH.json', Path(document['root']) / 'SOURCE_FREEZE.json',
                Path(document['root']) / 'PREREGISTRATION.md'):
            readonly.append(dict(source=common.path_text(path), target=common.path_text(path)))
        mounts[role] = dict(readonly=readonly, writable=writable)
    config['custody_forbidden'] = [str(Path(document['root']) / 'CUSTODY_CANARY'),
        str(original / 'judge/REFERENCE_PANELS.private.json'),
        str(Path(row['files']['PRIMARY_PANELS.private.json']['path'])), '/proc/1/root',
        str(common.CLAIMS), str(common.BASE / 'post_reboot_probe_queue_20260919/inputs')]
    config['player_private_paths'] = [str(view / 'judge/REFERENCE_PANELS.private.json'),
        str(view / 'epoch/PRIMARY_PANELS.private.json'), str(view / 'epoch/JUDGE_EPOCH.json')]
    for private_target in config['player_private_paths']:
        Path(private_target).touch(exist_ok=False)
    common.write_once(root / 'MOUNTS.json', mounts)
    config['mounts_sha256'] = sha(root / 'MOUNTS.json')
    common.write_once(root / 'CONFIG.json', config)
    return dict(job_id=job['job_id'], config_sha256=sha(root / 'CONFIG.json'),
        mounts_sha256=config['mounts_sha256'], config_path=str(root / 'CONFIG.json'))


def stage(candidate, receipt, seal, preregistration, resume_freeze_sha=None, resume_tree_sha=None, cpu_repair=None):
    require(seal['files'] == {name: sha(HERE / name) for name in common.RUNTIME_NAMES}, 'reviewed_wrapper_source')
    require(seal['preregistration'] == common.PREREGISTRATION, 'reviewed_preregistration_binding')
    common.regular(preregistration, common.PREREGISTRATION['sha256'])
    require(not cpu_repair or not (resume_freeze_sha or resume_tree_sha), 'new_cpu_incarnation_not_staging_resume')
    document = common.registry(candidate, receipt, cpu_repair)
    original = common.load_v4()
    common.verify_host(document, original)
    root = Path(document['root'])
    require(root.parent == (common.CUSTODY_PARENT if cpu_repair else common.PARENT), 'bound_diagnostic_root')
    preservation = None
    with common.shared_lock():
        if resume_freeze_sha or resume_tree_sha:
            require(common.digest(seal) != common.digest(common.read(root / 'SOURCE_FREEZE.json')),
                'repaired_preparation_requires_new_source_release')
            preservation = preserve_unlaunched(root, document, resume_freeze_sha, resume_tree_sha)
        else:
            require(not root.exists(), 'new_diagnostic_root_no_replay')
        root.parent.mkdir(mode=0o700, exist_ok=True)
        root.mkdir(mode=0o700)
    (root / 'jobs').mkdir()
    (root / 'runtime').mkdir()
    for name in common.RUNTIME_NAMES:
        shutil.copyfile(HERE / name, root / 'runtime' / name)
    common.write_once(root / 'SOURCE_FREEZE.json', seal)
    common.write_once(root / 'REGISTRY.json', document)
    if preservation is not None:
        common.write_once(root / 'PREPARATION_CONTINUATION.json', preservation)
    shutil.copyfile(preregistration, root / 'PREREGISTRATION.md')
    (root / 'CUSTODY_CANARY').write_bytes(os.urandom(32))
    prepared = []
    for job in document['jobs']:
        prepared.append(make_job(document, job, receipt['rows'][job['arm']], seal['files']))
    proof = dict(status='CPU_STAGED_NO_GPU_DISPATCH', observed_unix=time.time(),
        registry_sha256=sha(root / 'REGISTRY.json'), source_freeze_sha256=sha(root / 'SOURCE_FREEZE.json'),
        preregistration=common.PREREGISTRATION,
        unlaunched_stage_preservation=preservation,
        jobs=prepared, original_queue_mutated=False, custody_runtime_proof_pending=True)
    common.write_once(root / 'PREPARED.json', proof)
    return proof


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--candidate-sha256', required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('--receipt-sha256', required=True)
    parser.add_argument('--seal', type=Path, required=True)
    parser.add_argument('--seal-sha256', required=True)
    parser.add_argument('--preregistration', type=Path, required=True)
    parser.add_argument('--resume-staging-freeze-sha256')
    parser.add_argument('--resume-staging-tree-sha256')
    parser.add_argument('--cpu-proof-repair', type=Path)
    parser.add_argument('--cpu-proof-repair-sha256')
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--stage', action='store_true')
    mode.add_argument('--plan', action='store_true')
    mode.add_argument('--inspect-unlaunched', action='store_true')
    args = parser.parse_args()
    for path, expected in ((args.candidate, args.candidate_sha256), (args.receipt, args.receipt_sha256),
            (args.seal, args.seal_sha256)):
        common.regular(path, expected)
    candidate, receipt, seal = (common.read(path) for path in (args.candidate, args.receipt, args.seal))
    common.regular(args.preregistration, common.PREREGISTRATION['sha256'])
    require(seal['preregistration'] == common.PREREGISTRATION
        and seal['files'] == {name: sha(HERE / name) for name in common.RUNTIME_NAMES}, 'reviewed_source_and_preregistration')
    cpu_repair = None
    if args.cpu_proof_repair is not None:
        common.regular(args.cpu_proof_repair, args.cpu_proof_repair_sha256)
        cpu_repair = common.read(args.cpu_proof_repair)
        require(seal['cpu_repair_sha256'] == args.cpu_proof_repair_sha256, 'sealed_new_cpu_diagnostic')
    rebuilt = build(receipt, common.SEEDS, 'c2', time.time())
    require(candidate['sampling_epoch_sha256'] == rebuilt['sampling_epoch_sha256'], 'candidate_unchanged_scientific_scope')
    if args.stage:
        result = stage(candidate, receipt, seal, args.preregistration,
            args.resume_staging_freeze_sha256, args.resume_staging_tree_sha256, cpu_repair)
    elif args.inspect_unlaunched:
        result = unlaunched_inventory(Path(common.registry(candidate, receipt)['root']))
    else:
        result = common.registry(candidate, receipt, cpu_repair)
    print(__import__('json').dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
