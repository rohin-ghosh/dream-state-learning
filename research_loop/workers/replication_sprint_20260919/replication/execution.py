"""Shared identity, staging and original-route commands for one new sampling block."""

from contextlib import contextmanager
from copy import deepcopy
import fcntl
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

from construct_candidate import ADOPTED_EPOCH, ADOPTED_SOURCE, C2_PREPARATION_BOUND, digest, require, sha


BASE = Path('/localhome/local-rohing')
V4 = BASE / 'post_reboot_probe_queue_20260919/candidate_v4'
V4_FREEZE = 'd77089e8d7eb3ff06e709fb8f16c9555a2c620a614fe9c335a516c54475061e0'
CLAIMS = BASE / 'post_reboot_probe_dispatch_20260919/dispatch_locks'
PARENT = BASE / 'post_sampling_replication_20260919'
CUSTODY_PARENT = BASE / 'post_sampling_custody_diagnostics_20260919'
PYTHON = BASE / 'v2/venv/bin/python'
RUNTIME_NAMES = ('execution.py', 'construct_candidate.py', 'sealed_runner.py', 'dispatch_sampling.py',
    'prepare_executable.py', 'report_sampling.py', 'release_failed_claims.py')
ARM_ORDER = ('base', 'c2sleep51', 'c2sleep117')
SEEDS = (23301, 23302)
PREREGISTRATION = dict(
    repo_relative='research_loop/workers/replication_sprint_20260919/C2_SAMPLING_PREREGISTRATION.md',
    sha256='afb4de49f040c589ec416f7901c02b945776593ecf8670d4505aa417a30c5c63')
SCENE_IDS = ('agentdev_621cb5d0bdea9584dc9f', 'agentdev_769e881d85fc5d27cb4c',
    'agentdev_92a6a32f99def322d70e')


def read(path):
    return json.loads(Path(path).read_bytes())


def write_once(path, value):
    path = Path(path)
    payload = (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n').encode()
    with path.open('xb') as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def regular(path, expected):
    path = Path(path)
    require(path.is_file() and not path.is_symlink() and sha(path) == expected, 'bound_file:' + str(path))


def path_text(path):
    value = str(path)
    require(value.startswith('/') and all(character.isalnum() or character in '/_.-' for character in value)
        and '..' not in Path(value).parts, 'safe_absolute_path')
    return value


def load_v4():
    regular(V4 / 'SOURCE_FREEZE_V4_REBIND.json', V4_FREEZE)
    for name, expected in read(V4 / 'SOURCE_FREEZE_V4_REBIND.json')['files'].items():
        regular(V4 / name, expected)
    sys.path.insert(0, str(V4))
    try:
        spec = importlib.util.spec_from_file_location('sampling_original_v4_runtime', V4 / 'probe_runtime.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module


def registry(candidate, receipt, cpu_repair=None):
    epoch = candidate['sampling_epoch']
    require(candidate['sampling_epoch_sha256'] == digest(epoch), 'diagnostic_epoch_binding')
    require(epoch['block'] == 'c2' and tuple(epoch['arm_order']) == ARM_ORDER
        and tuple(epoch['sampling_seeds']) == SEEDS, 'main_selected_block_and_seeds')
    require(epoch['judge_epoch_sha256'] == ADOPTED_EPOCH
        and epoch['source_manifest_sha256'] == ADOPTED_SOURCE, 'original_adopted_protocol')
    require(candidate['effective_hard_end_unix'] == C2_PREPARATION_BOUND, 'stricter_original_c2_bound')
    policy = receipt['queue']['policy']
    require(policy['claims_namespace'] == str(CLAIMS), 'original_claims_namespace')
    root = PARENT / candidate['sampling_epoch_sha256']
    jobs = []
    for arm in ARM_ORDER:
        require(tuple(sorted({cell['contest_id'] for cell in receipt['rows'][arm]['cell_budgets']}))
            == SCENE_IDS, 'same_three_original_development_scenes')
        identity = dict(schema='C2_SAMPLING_JOB_ID_V1', diagnostic_epoch_sha256=digest(epoch), arm=arm,
            original_config_sha256=receipt['rows'][arm]['files']['CONFIG.json']['sha256'],
            checkpoint=epoch['source_checkpoints'][arm])
        job_id = digest(identity)
        jobs.append(dict(arm=arm, job_id=job_id, identity=identity, root=str(root / 'jobs' / job_id)))
    block_id = digest(dict(schema='C2_SAMPLING_BLOCK_ID_V1', diagnostic_epoch_sha256=digest(epoch),
        jobs=[job['job_id'] for job in jobs]))
    document = dict(schema='C2_SAMPLING_EXECUTION_REGISTRY_V1', root=str(root), block_id=block_id,
        diagnostic_epoch=deepcopy(epoch), diagnostic_epoch_sha256=digest(epoch), jobs=jobs,
        original_policy=deepcopy(policy), original_queue_registry=deepcopy(receipt['queue']['registry_ref']),
        original_policy_ref=deepcopy(receipt['queue']['policy_ref']),
        original_no_retry_history=deepcopy(receipt['queue']['history']),
        original_history_ref=deepcopy(receipt['queue']['history_ref']),
        preregistration=deepcopy(PREREGISTRATION), expected_scene_ids=list(SCENE_IDS),
        hard_end_unix=min(C2_PREPARATION_BOUND, policy['lease_end_unix']),
        max_block_runtime_seconds=2400, teardown_margin_seconds=policy['teardown_margin_seconds'],
        claims_namespace=str(CLAIMS), role_devices=deepcopy(policy['role_devices']),
        semantics='NEW_PREDECLARED_SEED_DIAGNOSTIC_NOT_RETRY_OF_ORIGINAL_SOURCE_AGE_JOB',
        independent_training_lineages=False, execution_performed=False)
    if cpu_repair is not None:
        validate_cpu_repair(cpu_repair, document['diagnostic_epoch_sha256'])
        incarnation = digest(cpu_repair)
        document.update(schema='C2_CUSTODY_DIAGNOSTIC_REGISTRY_V1', proof_only=cpu_repair['proof_only'],
            cpu_repair=deepcopy(cpu_repair), execution_incarnation_sha256=incarnation,
            root=str(CUSTODY_PARENT / incarnation), semantics='BOUND_CUSTODY_REPAIR_FRESH_EXECUTION_NO_FAILED_ATTEMPT_REUSE')
        for job in document['jobs']:
            job['identity'].update(schema='C2_CUSTODY_DIAGNOSTIC_JOB_V1', original_job_id=job['job_id'],
                execution_incarnation_sha256=incarnation)
            job['job_id'] = digest(job['identity'])
            job['root'] = str(Path(document['root']) / 'jobs' / job['job_id'])
        document['block_id'] = digest(dict(schema='C2_SAMPLING_BLOCK_ID_V1',
            diagnostic_epoch_sha256=document['diagnostic_epoch_sha256'], jobs=[job['job_id'] for job in document['jobs']]))
    return document


def validate_cpu_repair(repair, epoch_sha):
    if repair['schema'] == 'C2_CUSTODY_REPAIR_EXECUTION_AUTHORIZATION_V3':
        require(repair['repair_version'] == 3 and repair['proof_only'] is False
            and repair['model_execution_authorized'] is True
            and repair['model_dispatch_requires_fresh_custody'] is True
            and repair['preregistration'] == PREREGISTRATION, 'explicit_bound_model_scope_after_custody')
        prior_incarnation = repair['prior_execution_incarnation_sha256']
        require(len(prior_incarnation) == 64 and all(character in '0123456789abcdef'
            for character in prior_incarnation), 'canonical_prior_incarnation')
        prior_root = CUSTODY_PARENT / prior_incarnation
    else:
        require(repair['schema'] == 'C2_CPU_CUSTODY_REPAIR_AUTHORIZATION_V1'
            and repair['proof_only'] is True and repair['model_execution_authorized'] is False
            and repair['repair_version'] == 2, 'explicit_separate_cpu_only_diagnostic')
        prior_root = PARENT / epoch_sha
    require(repair['diagnostic_epoch_sha256'] == epoch_sha
        and repair['prior_root'] == str(prior_root), 'bound_prior_failed_diagnostic')
    require(set(repair['prior_refs']) == {'REGISTRY.json', 'SOURCE_FREEZE.json', 'PREPARED.json',
        'BLOCK_LAUNCH.json', 'BLOCK_FAILED.json'}, 'full_preserved_failed_admission_chain')
    require(repair['authorization'], 'explicit_repair_authorization')
    for name, reference in repair['prior_refs'].items():
        require(reference['path'] == str(prior_root / name)
            and len(reference['sha256']) == 64, 'exact_prior_evidence_path')


def verify_prior_failed_cpu_proof(document):
    repair = document['cpu_repair']
    validate_cpu_repair(repair, document['diagnostic_epoch_sha256'])
    for reference in repair['prior_refs'].values():
        regular(Path(reference['path']), reference['sha256'])
    root = Path(repair['prior_root'])
    launch = read(root / 'BLOCK_LAUNCH.json')
    failure = read(root / 'BLOCK_FAILED.json')
    require(launch['mode'] == 'CPU_CUSTODY_PROOF_ONLY' and launch['model_dispatch_authorized'] is False
        and failure['error'] == 'own_unit_failure_terminal_no_retry'
        and failure['status'] == 'TERMINAL_NO_RETRY_NO_FALLBACK', 'cpu_role_failure_not_platform_denial')
    require(not (root / 'GPU_REVIEW.json').exists() and not (root / 'BLOCK_COMPLETE.json').exists(),
        'no_prior_science_execution')
    prior = read(root / 'REGISTRY.json')
    require(prior['diagnostic_epoch_sha256'] == document['diagnostic_epoch_sha256'], 'same_scientific_epoch')
    if repair['repair_version'] == 3:
        require(prior.get('proof_only') is True and prior['execution_incarnation_sha256']
            == repair['prior_execution_incarnation_sha256'] == digest(prior['cpu_repair']),
            'prior_was_explicit_cpu_only_incarnation')
        verify_prior_failed_cpu_proof(prior)
    require(launch['block_id'] == prior['block_id'] != document['block_id'], 'fresh_block_not_reused')
    for job in prior['jobs']:
        require(not (Path(job['root']) / 'DISPATCH_INTENT.json').exists(), 'prior_model_dispatch_forbidden')
        for role in ('player', 'judge'):
            require(not (Path(job['root']) / 'view' / (role + '_run_STARTED.json')).exists(), 'prior_model_run_forbidden')


def validate_registry(document):
    if document.get('cpu_repair') is not None:
        require(document['schema'] == 'C2_CUSTODY_DIAGNOSTIC_REGISTRY_V1', 'separate_cpu_diagnostic_schema')
        validate_cpu_repair(document['cpu_repair'], document['diagnostic_epoch_sha256'])
        require(document.get('proof_only') == document['cpu_repair']['proof_only'], 'bound_execution_scope')
        require(document['execution_incarnation_sha256'] == digest(document['cpu_repair'])
            and Path(document['root']) == CUSTODY_PARENT / document['execution_incarnation_sha256'],
            'separate_cpu_root_not_failed_root')
    else:
        require(document['schema'] == 'C2_SAMPLING_EXECUTION_REGISTRY_V1', 'diagnostic_registry_not_v4_capsule')
        require(Path(document['root']) == PARENT / document['diagnostic_epoch_sha256'], 'stable_single_attempt_root')
    require(digest(document['diagnostic_epoch']) == document['diagnostic_epoch_sha256'], 'sampling_epoch_unchanged')
    require(document['preregistration'] == PREREGISTRATION
        and tuple(document['expected_scene_ids']) == SCENE_IDS, 'preregistered_document_and_scenes')
    require(tuple(document['diagnostic_epoch']['sampling_seeds']) == SEEDS
        and tuple(job['arm'] for job in document['jobs']) == ARM_ORDER, 'predeclared_seeds_and_order')
    require(document['claims_namespace'] == str(CLAIMS)
        and document['max_block_runtime_seconds'] == 2400
        and document['hard_end_unix'] == C2_PREPARATION_BOUND, 'no_resource_or_lease_extension')
    require(document['role_devices'] == document['original_policy']['role_devices']
        and document['role_devices']['player'] == dict(physical=2, uuid='GPU-ac7e4165-630c-eafe-4ba5-2b2fc4a4e5d1')
        and document['role_devices']['judge'] == dict(physical=7, uuid='GPU-b7ec9035-3ba3-464f-6c2f-7588a3e328c1')
        and set(document['original_policy']['protected_physical']) == {0, 1, 3, 4, 5, 6}
        and document['original_policy']['expected_uid'] == 1352, 'exact_original_resource_boundary')
    for job in document['jobs']:
        require(digest(job['identity']) == job['job_id']
            and job['identity']['diagnostic_epoch_sha256'] == document['diagnostic_epoch_sha256']
            and job['identity']['arm'] == job['arm']
            and Path(job['root']) == Path(document['root']) / 'jobs' / job['job_id'], 'job_identity_join')
    require(document['block_id'] == digest(dict(schema='C2_SAMPLING_BLOCK_ID_V1',
        diagnostic_epoch_sha256=document['diagnostic_epoch_sha256'], jobs=[job['job_id'] for job in document['jobs']])),
        'block_identity_join')


def verify_host(document, original):
    validate_registry(document)
    if document.get('cpu_repair') is not None:
        verify_prior_failed_cpu_proof(document)
    policy = document['original_policy']
    regular(Path(document['original_policy_ref']['path']), document['original_policy_ref']['sha256'])
    require(read(document['original_policy_ref']['path']) == policy, 'original_queue_policy_never_rebound_silently')
    original.verify_protected(dict(policy, queue_policy=policy))
    require(time.time() + 60 < document['hard_end_unix'], 'existing_lease_unexpired')


@contextmanager
def shared_lock(namespace=CLAIMS):
    require(Path(namespace).is_dir(), 'existing_claim_namespace_required')
    with (Path(namespace) / 'DISPATCH.lock').open('a') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def reserve(document, deadline, now, namespace=CLAIMS):
    require(360 < deadline - now <= 2400 and deadline <= document['hard_end_unix'], 'finite_original_bound')
    paths = [Path(namespace) / (device['uuid'] + '.json') for device in document['role_devices'].values()]
    for path in paths:
        require(not path.is_symlink(), 'claim_symlink_forbidden')
        if path.exists():
            require(now > read(path)['hold_until_unix'], 'existing_lane_claim_no_overlap')
    for path in paths:
        if path.exists():
            path.rename(path.with_name(path.stem + '.expired.' + str(time.time_ns()) + '.json'))
        write_once(path, dict(job_id=document['block_id'], created_unix=now,
            hold_until_unix=deadline + document['teardown_margin_seconds'],
            protocol='C2_SAMPLING_DIAGNOSTIC_V1', diagnostic_epoch_sha256=document['diagnostic_epoch_sha256']))


def verify_claims(document, deadline, namespace=CLAIMS):
    for device in document['role_devices'].values():
        claim = read(Path(namespace) / (device['uuid'] + '.json'))
        require(claim['job_id'] == document['block_id']
            and claim['hold_until_unix'] == deadline + document['teardown_margin_seconds'], 'same_block_owns_both_claims')


def original_inventory_config(document):
    return dict(role_devices=document['role_devices'])


def command(document, job, role, mode, config_sha, launch_sha, deadline, now):
    require(role in ('player', 'judge') and mode in ('proof', 'run'), 'explicit_role_and_mode')
    require(not document.get('proof_only') or mode == 'proof', 'cpu_diagnostic_cannot_load_models')
    remaining = math.floor(deadline - now)
    require(60 < remaining <= 2400 and deadline <= document['hard_end_unix'], 'unchanged_finite_runtime')
    root = Path(job['root'])
    block = Path(document['root'])
    view = root / 'view'
    device = document['role_devices'][role]
    mounts = read(root / 'MOUNTS.json')[role]
    mounts = deepcopy(mounts)
    if mode == 'run':
        for path in (block / 'GPU_REVIEW.json', block / 'PROOFS_COMPLETE.json'):
            mounts['readonly'].append(dict(source=str(path), target=str(path)))
    unit = 'orch-sampling-' + job['job_id'][:16] + '-' + role + '-' + mode
    properties = dict(User=str(document['original_policy']['expected_uid']),
        Group=str(document['original_policy']['expected_uid']), RootDirectory=str(root / ('rootfs_' + role)),
        WorkingDirectory=str(view / 'source'), RuntimeMaxSec=str(remaining), TimeoutStopSec='15',
        RemainAfterExit='yes',
        KillMode='control-group', UMask='0077', DevicePolicy='closed', NoNewPrivileges='yes',
        MountAPIVFS='no', PrivateNetwork='yes', ProtectSystem='strict', ProtectHome='yes',
        CapabilityBoundingSet='', AmbientCapabilities='', RestrictNamespaces='yes',
        RestrictSUIDSGID='yes', ProtectKernelTunables='yes', ProtectKernelModules='yes',
        ProtectControlGroups='yes', LimitCORE='0',
        BindReadOnlyPaths=' '.join(path_text(row['source']) + ':' + path_text(row['target']) for row in mounts['readonly']),
        BindPaths=' '.join(path_text(row['source']) + ':' + path_text(row['target']) for row in mounts['writable']),
        TemporaryFileSystem='/tmp:rw,size=256M,mode=1777',
        ReadWritePaths=str(view) + ' /tmp',
        StandardOutput='append:' + str(root / (role + '_' + mode + '.log')),
        StandardError='append:' + str(root / (role + '_' + mode + '.log')))
    if role == 'player':
        properties['InaccessiblePaths'] = ' '.join(path_text(view / name) for name in ('judge', 'epoch', 'assets'))
    argv = ['sudo', '-n', 'systemd-run', '--unit=' + unit]
    argv += ['--property=' + name + '=' + value for name, value in properties.items()]
    for path in ['/dev/nvidia' + str(device['physical']), '/dev/nvidiactl', '/dev/nvidia-uvm',
            '/dev/nvidia-uvm-tools', '/dev/null', '/dev/zero', '/dev/random', '/dev/urandom']:
        argv.append('--property=DeviceAllow=' + path + ' rw')
    environment = dict(CUDA_VISIBLE_DEVICES=device['uuid'], HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
        PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(view / 'source'), OMP_NUM_THREADS='2',
        MKL_NUM_THREADS='2', TOKENIZERS_PARALLELISM='false', HOME='/tmp', HF_HOME='/tmp/hf')
    argv += ['--setenv=' + name + '=' + value for name, value in environment.items()]
    argv += [str(PYTHON), '-B', str(block / 'runtime/sealed_runner.py'),
        '--config', str(root / 'CONFIG.json'), '--config-sha256', config_sha,
        '--launch-sha256', launch_sha, '--role', role, '--mode', mode]
    if mode == 'run':
        argv += ['--review-sha256', sha(block / 'GPU_REVIEW.json')]
    return dict(unit=unit, argv=argv, role=role, mode=mode)


def terminal_submit(spec, runner=subprocess.run):
    result = runner(spec['argv'], check=False, capture_output=True, text=True, timeout=25)
    require(result.returncode == 0, 'PLATFORM_DENIAL_TERMINAL_NO_RETRY_NO_FALLBACK')
