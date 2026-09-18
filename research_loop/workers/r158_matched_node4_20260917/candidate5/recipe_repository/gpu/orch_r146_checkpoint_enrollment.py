"""Bounded, CPU-only adapter custody; proposals are never enrollment or READY.

Source execution contains only standard-library readers. Runtime pins are
source-owner GUARD declarations, not a new scan of executable source or processes.
No model, optimizer, RNG, TRAIN, parent or held-result payload is opened.
"""

import argparse
import fcntl
import hashlib
import inspect
import io
import json
import math
import os
from pathlib import Path
import re
import shlex
import stat
import subprocess
import sys
import tarfile
import time


SCHEMA = 'R146_CHECKPOINT_ENROLLMENT_PROPOSAL_V1'
SOURCE_SCHEMA = 'R146_CHECKPOINT_SOURCE_SPEC_V1'
CUSTODY_SCHEMA = 'R146_CHECKPOINT_CUSTODY_V1'
BASE_SHA = 'a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992'
NATIVE_SCHEMA = 'R125_NATIVE_CONTINUITY_V1'
ROOT = '/localhome/local-rohing/orch_r130_checkpoint_benchmark_20260916_attempt1'
CONFIG_SHA = 'a22dfa29a16ef419de3cb2e2ad2740b673700c4669c9ecbfc76de1238dea0805'
ADAPTER_NAMES = {'adapter_config.json', 'adapter_model.safetensors', 'README.md'}
ROLES = ('initial', 'firstsleep', 'latest')
LIMIT = 512 * 1024 * 1024
SOURCE_PARENT = '/localhome/local-rohing'
ROLLOUT = '/localhome/local-rohing/orch_r144_target_rollout_a40r_suffix_20260916t1643z'
LIVES = {
    'r137_raw_unparented_a40r1': 'orch_r136_raw_unparented_a40r1_20260916_attempt1',
    'r137_raw_parented_seed1_a40r3': 'orch_r136_raw_parented_seed1_a40r3_20260916_attempt1',
}
ORIGINALS = {
    'legacy': ('ovx3_ssh.sh', 'orch_r125_continual_20260916_attempt1',
        'fbcbb4791f84b7a21e662d25cf44de6dba791a73526c63743c07ba1ff4681324'),
    'pilot': ('ovx3_ssh.sh', 'orch_r127_pilot_20260916_attempt1',
        '4d2080e9f9c1355782dd954d3fb76875f3393c21ae8d71d94e303db05742358e'),
    'kernel': ('a40r_ssh.sh', 'orch_r132_kernel_child_20260916_attempt1',
        '7989781649936b711cd63c29c96d35bbd2004acf78a353489f2d5c9ed903a13b'),
}


def require(value, reason):
    if not value:
        raise ValueError(reason)


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
        allow_nan=False).encode()).hexdigest()


def checksum(raw):
    return hashlib.sha256(raw).hexdigest()


def is_hash(value):
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value) is not None


def object_pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'duplicate_JSON_key')
        result[key] = value
    return result


def parse(raw):
    def invalid(value):
        raise ValueError('nonfinite_JSON')
    return json.loads(raw, object_pairs_hook=object_pairs, parse_constant=invalid)


def finite_time(value):
    return type(value) in (int, float) and math.isfinite(value) and 0 < value <= time.time()


def lexical(value, root):
    require(isinstance(value, str) and isinstance(root, str), 'absolute_path_string')
    path, parent = Path(value), Path(root)
    require(path.is_absolute() and parent.is_absolute() and '..' not in path.parts
        and '..' not in parent.parts and path.is_relative_to(parent), 'path_scope')
    require(str(path) == value and str(parent) == root, 'canonical_path')
    return path


def regular(value, root, directory=False):
    path = lexical(value, root)
    for part in (path, *path.parents):
        require(not part.is_symlink(), 'symlink_forbidden')
    mode = path.stat().st_mode
    require(stat.S_ISDIR(mode) if directory else stat.S_ISREG(mode), 'regular_file_required')
    return path


def bounded_read(value, root, maximum=4 * 1024 * 1024):
    path = regular(value, root)
    require(path.stat().st_size <= maximum, 'bounded_file_bytes')
    with path.open('rb') as stream:
        raw = stream.read(maximum + 1)
    require(len(raw) <= maximum, 'bounded_file_bytes')
    return raw


def binding(path, raw):
    return dict(path=str(path), sha256=checksum(raw))


def validate_spec(spec, pinned=False):
    require(isinstance(spec, dict) and set(spec) == {'schema', 'lineage_id', 'life_root',
        'metadata', 'classification'}, 'source_spec_fields')
    require(spec['schema'] == SOURCE_SCHEMA and spec['lineage_id'] in LIVES, 'source_spec_scope')
    root = SOURCE_PARENT + '/' + LIVES[spec['lineage_id']]
    require(spec['life_root'] == root, 'exact_source_owned_root')
    require(set(spec['metadata']) == {'origin', 'current'}, 'origin_and_current_metadata')
    for stage, metadata in spec['metadata'].items():
        metadata_root = root if stage == 'origin' else ROLLOUT + ('/lane1' if spec['classification']['seed'] == 0 else '/lane3')
        require(set(metadata) == {'plan', 'guard', 'launch'}, 'metadata_fields')
        for kind, item in metadata.items():
            require(set(item) == {'path', 'sha256'}, 'metadata_binding_fields')
            path = lexical(item['path'], metadata_root)
            names = {'plan': {'PLAN.json'}, 'guard': {'GUARD.json', 'CONTAINED_GUARD.json'},
                'launch': {'LAUNCH.json'}}
            require(path.name in names[kind] and len(path.relative_to(metadata_root).parts) <= 4,
                'only_exact_plan_start_metadata')
            require(is_hash(item['sha256']) or (not pinned and item['sha256'] is None),
                'metadata_hash_required')
    classification = spec['classification']
    require(set(classification) == {'programme', 'parenting', 'seed', 'replay', 'matched_control'},
        'classification_fields')
    require(classification['programme'] == 'raw' and classification['matched_control'] is False,
        'no_unproven_matched_twin')
    seed = 0 if spec['lineage_id'] == 'r137_raw_unparented_a40r1' else 1
    require(type(classification['seed']) is int and classification['seed'] == seed
        and classification['parenting'] == ('none_declared' if seed == 0 else 'socratic_sparse3_declared')
        and classification['replay'] == 'free_distillation', 'honest_programme_seed_replay')
    return spec


def source_metadata(spec):
    validate_spec(spec)
    root = spec['life_root']
    projected = {}
    for stage, metadata in spec['metadata'].items():
        metadata_root = root if stage == 'origin' else ROLLOUT + ('/lane1' if spec['classification']['seed'] == 0 else '/lane3')
        documents, bindings = {}, {}
        for kind, item in metadata.items():
            raw = bounded_read(item['path'], metadata_root)
            require(item['sha256'] is None or checksum(raw) == item['sha256'], 'metadata_pin_changed')
            documents[kind], bindings[kind] = parse(raw), binding(item['path'], raw)
        plan, guard, launch = (documents[kind] for kind in ('plan', 'guard', 'launch'))
        require(plan['schema'] == NATIVE_SCHEMA and plan['base_sha256'] == BASE_SHA
            and plan['root'] == root + '/run1', 'plan_life_base_binding')
        require(guard['plan_path'] == metadata['plan']['path']
            and guard['plan_sha256'] == bindings['plan']['sha256']
            and launch['plan_sha256'] == bindings['plan']['sha256']
            and launch['guard_sha256'] == bindings['guard']['sha256'], 'source_start_plan_chain')
        require(Path(metadata['launch']['path']).parent == Path(guard['attempt_dir']), 'launch_attempt_binding')
        require(finite_time(launch['started_unix']), 'real_programme_start_metadata')
        require(plan.get('seed', 0) == spec['classification']['seed']
            and plan.get('presleep_variant', 'free_distillation') == spec['classification']['replay'],
            'plan_seed_replay_binding')
        lexical(plan['source_root'], metadata_root)
        pins = guard['source_pins']
        require(isinstance(pins, dict) and 1 <= len(pins) <= 4096, 'bounded_runtime_pin_inventory')
        for relative, expected in pins.items():
            require(isinstance(relative, str) and not Path(relative).is_absolute()
                and '..' not in Path(relative).parts and is_hash(expected), 'runtime_pin_schema')
        required = ('gpu/orch_r125_continual_native.py', 'organism_v6/orch_r125_continual_stream.py')
        require(all(name in pins for name in required), 'native_runtime_declared')
        projected[stage] = dict(bindings=bindings, source_root=plan['source_root'],
            source_inventory_sha256=digest(pins), source_file_count=len(pins),
            core_source_pins={name: pins[name] for name in required},
            runtime_verification='source_owner_guard_declaration_not_source_or_process_scan',
            started_unix=launch['started_unix'], seed=plan.get('seed', 0),
            replay=plan.get('presleep_variant', 'free_distillation'),
            replay_field_explicit='presleep_variant' in plan)
    require(projected['origin']['started_unix'] <= projected['current']['started_unix'], 'origin_before_current')
    return projected


def source_checkpoint(path, root, payloads=False):
    checkpoint_root = root + '/run1/checkpoints'
    path = lexical(str(path), checkpoint_root)
    require(path.name == 'COMMIT.json' and path.parent.parent == Path(checkpoint_root)
        and (path.parent.name == 'initial' or re.fullmatch('sleep_[0-9]{6}', path.parent.name)),
        'only_committed_checkpoint_names')
    raw = bounded_read(str(path), checkpoint_root)
    document = parse(raw)
    fields = {'schema', 'base_sha256', 'adapter_path', 'adapter_files', 'adapter_state_sha256',
        'optimizer_rng_path', 'checkpoint_sha256', 'optimizer_steps', 'created_unix'}
    require(isinstance(document, dict) and fields <= set(document)
        and set(document) <= fields | {'experiment'}, 'native_commit_fields_no_held_content')
    require(document['schema'] == NATIVE_SCHEMA and document['base_sha256'] == BASE_SHA,
        'native_base_contract')
    require(is_hash(document['adapter_state_sha256']) and finite_time(document['created_unix'])
        and type(document['optimizer_steps']) is int and document['optimizer_steps'] >= 0,
        'native_state_steps_time')
    require(document['adapter_path'] == str(path.parent / 'adapter')
        and document['optimizer_rng_path'] == str(path.parent / 'optimizer_rng.pt'), 'native_path_provenance')
    files = document['adapter_files']
    require(isinstance(files, dict) and {'adapter_config.json', 'adapter_model.safetensors'} <= set(files)
        and set(files) <= ADAPTER_NAMES and all(is_hash(value) for value in files.values()),
        'adapter_only_inventory')
    require(set(document['checkpoint_sha256']) == {'adapter', 'optimizer', 'rng'}
        and all(is_hash(value) for value in document['checkpoint_sha256'].values())
        and document['checkpoint_sha256']['adapter'] == digest(files), 'native_inventory_digest')
    if 'experiment' in document:
        experiment = document['experiment']
        require(isinstance(experiment, dict) and set(experiment) == {'schema', 'seed',
            'presleep_variant', 'compaction_invitation', 'system_prompt', 'birth_prompt',
            'seed_initialization'}, 'native_experiment_fields')
        require(type(experiment['seed']) is int and experiment['seed'] in (0, 1)
            and experiment['presleep_variant'] == 'free_distillation'
            and experiment['schema'] == 'R133_CONTINUAL_EXPERIMENT_V1'
            and experiment['seed_initialization'] == 'before_lora'
            and all(isinstance(experiment[key], str) for key in
                ('compaction_invitation', 'system_prompt', 'birth_prompt')), 'experiment_seed_replay')
    adapter = regular(str(path.parent / 'adapter'), checkpoint_root, directory=True)
    require({item.name for item in adapter.iterdir()} == set(files), 'exact_adapter_inventory')
    contents = {'COMMIT.json': raw}
    total = len(raw)
    for name, expected in sorted(files.items()):
        item = regular(str(adapter / name), checkpoint_root)
        require(total + item.stat().st_size <= LIMIT, 'bounded_adapter_bytes')
        if payloads:
            payload = bounded_read(str(item), checkpoint_root, LIMIT - total)
            require(checksum(payload) == expected, 'adapter_file_hash_changed')
            contents['adapter/' + name] = payload
            total += len(payload)
        else:
            total += item.stat().st_size
    result = dict(commit_path=str(path), commit_sha256=checksum(raw),
        created_unix=document['created_unix'], optimizer_steps=document['optimizer_steps'],
        adapter_state_sha256=document['adapter_state_sha256'], adapter_files=files,
        experiment=(dict(schema=document['experiment']['schema'], seed=document['experiment']['seed'],
            presleep_variant=document['experiment']['presleep_variant'],
            binding_sha256=digest(document['experiment'])) if 'experiment' in document else None))
    return result, contents


def discover(spec):
    metadata = source_metadata(spec)
    root = spec['life_root']
    checkpoints = Path(root) / 'run1/checkpoints'
    if not (checkpoints / 'initial/COMMIT.json').is_file() or not (checkpoints / 'sleep_000001/COMMIT.json').is_file():
        return dict(status='MISSING_BASELINE', lineage_id=spec['lineage_id'], metadata=metadata,
            checkpoint_requested=False)
    initial = source_checkpoint(checkpoints / 'initial/COMMIT.json', root)[0]
    first = source_checkpoint(checkpoints / 'sleep_000001/COMMIT.json', root)[0]
    require(initial['optimizer_steps'] == 0 and first['optimizer_steps'] > 0
        and metadata['origin']['started_unix'] <= initial['created_unix'] < first['created_unix'],
        'exact_step0_firstsleep_order')
    candidates = [first]
    count = 0
    for path in checkpoints.glob('sleep_??????/COMMIT.json'):
        count += 1
        require(count <= 4096, 'bounded_checkpoint_inventory')
        if re.fullmatch('sleep_[0-9]{6}', path.parent.name):
            candidates.append(source_checkpoint(path, root)[0])
    latest = max(candidates, key=lambda item: (item['created_unix'], item['commit_sha256']))
    require(latest['optimizer_steps'] >= first['optimizer_steps'], 'latest_steps_monotonic')
    selected = dict(initial=initial, firstsleep=first, latest=latest)
    for item in selected.values():
        experiment = item['experiment']
        if experiment is not None:
            require(experiment['seed'] == spec['classification']['seed']
                and experiment['presleep_variant'] == spec['classification']['replay'], 'commit_experiment_match')
    require(source_metadata(spec) == metadata, 'metadata_changed_during_discovery')
    return dict(status='BASELINES_DISCOVERED_NOT_ENROLLED', lineage_id=spec['lineage_id'],
        metadata=metadata, checkpoints=selected, observed_unix=time.time(), checkpoint_requested=False)


def pack(spec, discovery, role):
    validate_spec(spec, pinned=True)
    require(role in ROLES and discovery['status'] == 'BASELINES_DISCOVERED_NOT_ENROLLED'
        and discovery['lineage_id'] == spec['lineage_id'], 'discovery_binding')
    metadata = source_metadata(spec)
    require(metadata == discovery['metadata'], 'current_original_metadata_changed')
    for baseline in ('initial', 'firstsleep'):
        expected = discovery['checkpoints'][baseline]
        require(source_checkpoint(expected['commit_path'], spec['life_root'])[0] == expected,
            'baseline_COMMIT_changed')
    expected = discovery['checkpoints'][role]
    before, contents = source_checkpoint(expected['commit_path'], spec['life_root'], payloads=True)
    after, after_contents = source_checkpoint(expected['commit_path'], spec['life_root'], payloads=True)
    require(before == after == expected and contents == after_contents
        and source_metadata(spec) == metadata, 'source_before_after_changed')
    receipt = dict(schema='R146_SOURCE_COPY_RECEIPT_V1', lineage_id=spec['lineage_id'], role=role,
        source_spec_sha256=digest(spec), discovery_sha256=digest(discovery), metadata=metadata,
        checkpoint=before, classification=spec['classification'], observed_unix=time.time(),
        source_writes=False, checkpoint_requested=False, held_or_TRAIN_opened=False,
        optimizer_or_RNG_opened=False, model_imported=False, before_after_verified=True)
    contents['SOURCE_COPY_RECEIPT.json'] = encoded(receipt)
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode='w') as archive:
        for name, raw in sorted(contents.items()):
            member = tarfile.TarInfo(name)
            member.size, member.mode, member.mtime = len(raw), 0o400, 0
            archive.addfile(member, io.BytesIO(raw))
    return output.getvalue()


def verify_original(name):
    require(name in ORIGINALS, 'registered_original_only')
    wrapper, basename, expected = ORIGINALS[name]
    root = '/localhome/local-rohing/' + basename
    path = root + '/run1/checkpoints/initial/COMMIT.json'
    before, contents = source_checkpoint(path, root, payloads=True)
    after, after_contents = source_checkpoint(path, root, payloads=True)
    require(before == after and contents == after_contents and before['commit_sha256'] == expected
        and before['optimizer_steps'] == 0, 'original_baseline_identity')
    return dict(lineage_id=name, checkpoint=before, observed_unix=time.time(),
        before_after_verified=True, source_writes=False, wrapper_name=wrapper)


def source_batch(specs):
    require(isinstance(specs, list) and len(specs) == 2
        and {spec['lineage_id'] for spec in specs} == set(LIVES), 'two_cleared_node4_lives_only')
    for spec in specs:
        validate_spec(spec)
    lock_path = regular(ROLLOUT + '/NODE_HANDOFF.lock', ROLLOUT)
    descriptor = os.open(lock_path, os.O_RDONLY | os.O_NOFOLLOW)
    acquired = False
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            acquired = True
        except BlockingIOError:
            sys.stdout.buffer.write(encoded(dict(status='DEFERRED_OWNER_HANDOFF_LOCK_BUSY', source_writes=False)))
            return
        started = time.monotonic()
        total = 0
        with tarfile.open(fileobj=sys.stdout.buffer, mode='w|') as archive:
            for spec in specs:
                discovery = discover(spec)
                if discovery['status'] == 'BASELINES_DISCOVERED_NOT_ENROLLED':
                    spec = parse(encoded(spec))
                    for stage in ('origin', 'current'):
                        spec['metadata'][stage] = discovery['metadata'][stage]['bindings']
                    validate_spec(spec, pinned=True)
                files = {'spec.json': encoded(spec), 'discovery.json': encoded(discovery)}
                for name, raw in files.items():
                    member = tarfile.TarInfo(spec['lineage_id'] + '/' + name)
                    member.size = len(raw)
                    archive.addfile(member, io.BytesIO(raw))
                if discovery['status'] != 'BASELINES_DISCOVERED_NOT_ENROLLED':
                    continue
                for role in ROLES:
                    require(time.monotonic() - started < 120, 'bounded_owner_lock_copy_wall')
                    raw = pack(spec, discovery, role)
                    total += len(raw)
                    require(total <= 768 * 1024 * 1024, 'bounded_two_life_archive_bytes')
                    member = tarfile.TarInfo(spec['lineage_id'] + '/' + role + '.tar')
                    member.size = len(raw)
                    archive.addfile(member, io.BytesIO(raw))
    finally:
        sys.stdout.buffer.flush()
        time.sleep(15)
        if acquired:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def source_command(action, payload):
    require(action in ('discover', 'pack', 'original', 'batch'), 'read_only_source_action')
    if action not in ('original', 'batch'):
        validate_spec(payload['spec'], pinned=action == 'pack')
    functions = (require, encoded, digest, checksum, is_hash, object_pairs, parse, finite_time,
        lexical, regular, bounded_read, binding, validate_spec, source_metadata, source_checkpoint,
        discover, pack, verify_original, source_batch)
    constants = ('SCHEMA', 'SOURCE_SCHEMA', 'BASE_SHA', 'NATIVE_SCHEMA', 'ADAPTER_NAMES',
        'ROLES', 'LIMIT', 'LIVES', 'ORIGINALS', 'SOURCE_PARENT', 'ROLLOUT')
    program = 'from pathlib import Path\nimport fcntl,hashlib,io,json,math,os,re,stat,sys,tarfile,time\n'
    program += '\n'.join(name + '=' + repr(globals()[name]) for name in constants) + '\n'
    program += '\n\n'.join(inspect.getsource(function) for function in functions)
    program += '\npayload=json.loads(sys.argv[1])\n'
    if action == 'batch':
        program += "source_batch(payload['specs'])\n"
    elif action == 'pack':
        program += "sys.stdout.buffer.write(pack(payload['spec'],payload['discovery'],payload['role']))\n"
    elif action == 'discover':
        program += "print(json.dumps(discover(payload['spec']),allow_nan=False))\n"
    else:
        program += "print(json.dumps(verify_original(payload['lineage_id']),allow_nan=False))\n"
    return ('CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 python3 -B -c '
        + shlex.quote(program) + ' ' + shlex.quote(json.dumps(payload, allow_nan=False)))


def validate_clearance(clearance, now=None):
    now = time.time() if now is None else now
    require(set(clearance) == {'schema', 'owner_id', 'status', 'start_unix', 'end_unix',
        'evidence_path', 'evidence_sha256'}, 'clearance_schema')
    require(clearance['schema'] == 'R146_A40R_READONLY_CLEARANCE_V1'
        and clearance['owner_id'] == '01a0aa81-5d5f-7910-a330-dcdaff1ceb10'
        and clearance['status'] == 'READ_ONLY_CLEARED', 'explicit_Confucius_clearance')
    require(finite_time(clearance['start_unix']) and type(clearance['end_unix']) in (int, float)
        and math.isfinite(clearance['end_unix'])
        and clearance['start_unix'] <= now < clearance['end_unix'] <= clearance['start_unix'] + 3600,
        'bounded_clearance_window')
    require(checksum(Path(clearance['evidence_path']).read_bytes()) == clearance['evidence_sha256'],
        'owner_clearance_evidence_binding')


def wrapper_call(name, command, expected_sha256, *, clearance=None, input_bytes=None, timeout=120):
    require(name in {'a40r_ssh.sh', 'ovx3_ssh.sh', 'ovx_ssh.sh'} and 0 < timeout <= 180,
        'only_sanctioned_bounded_wrappers')
    repository = Path(__file__).resolve().parents[1]
    wrapper = regular(str(repository / 'gpu' / name), str(repository))
    require(is_hash(expected_sha256) and checksum(wrapper.read_bytes()) == expected_sha256,
        'sanctioned_wrapper_pin')
    if name == 'a40r_ssh.sh':
        require(clearance is not None, 'a40r_read_clearance_required')
        validate_clearance(clearance)
        require(time.time() + timeout <= clearance['end_unix'], 'full_call_inside_clearance')
    return subprocess.run(['bash', str(wrapper), command], input=input_bytes,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=True).stdout


def immutable(path, raw):
    path = Path(path)
    with path.open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    path.chmod(0o400)
    return checksum(raw)


def destination_admission(root=ROOT):
    from gpu import orch_r130_checkpoint_scheduler as scheduler
    require(str(root) == ROOT and os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'existing_node2_CPU_only')
    require(checksum(scheduler.socket.gethostname().encode()) == scheduler.sidecar.HOST_SHA256,
        'bound_node2_host')
    config_path = Path(root) / 'SCHEDULER_CONFIG_V1.json'
    raw = bounded_read(str(config_path), str(root))
    require(checksum(raw) == CONFIG_SHA, 'frozen_original_config')
    config = parse(raw)
    require(config['source_root'] == ROOT + '/source6_scheduler'
        and scheduler.sidecar.source_inventory(config['source_root']) == config['sources'],
        'frozen_destination_runtime')
    for field in ('registry', 'lineages'):
        path = config[field + '_path']
        require(checksum(bounded_read(path, ROOT)) == config[field + '_sha256'], 'original_registry_pin')
    require(config['registry_sha256'] == scheduler.REGISTRY_SHA256, 'frozen_original_registry')
    entries = scheduler.enrolled_lineages(parse(bounded_read(config['lineages_path'], ROOT)))
    require(set(entries) == set(ORIGINALS) and all(entries[name]['initial_commit_sha256']
        == ORIGINALS[name][2] for name in ORIGINALS), 'original_enrollment_preserved')
    require(config['copy_roots'] == [ROOT + '/checkpoints', ROOT + '/scheduler_inbox/copies']
        and config['inbox_root'] == ROOT + '/scheduler_inbox', 'existing_admitted_copy_roots')
    for name in ('scheduler_inbox', 'scheduler_inbox/copies'):
        path = regular(ROOT + '/' + name, ROOT, directory=True)
        require(path.stat().st_uid == os.getuid() and path.stat().st_mode & 0o077 == 0,
            'private_owned_admitted_destination')
    return config


def unpack_adapter(raw, expected):
    require(len(raw) <= LIMIT + 1024 * 1024, 'bounded_archive_bytes')
    contents = {}
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:') as archive:
        total = 0
        for member in archive:
            require(member.isfile() and member.name not in contents and member.name in
                {'COMMIT.json', 'SOURCE_COPY_RECEIPT.json'} | {'adapter/' + name for name in ADAPTER_NAMES},
                'adapter_only_regular_archive')
            total += member.size
            require(0 <= member.size and total <= LIMIT + 1024 * 1024, 'bounded_archive_payload')
            contents[member.name] = archive.extractfile(member).read()
    require({'COMMIT.json', 'SOURCE_COPY_RECEIPT.json'} <= set(contents), 'copy_receipt_required')
    commit = parse(contents['COMMIT.json'])
    require(checksum(contents['COMMIT.json']) == expected['commit_sha256'], 'copied_COMMIT_pin')
    require(set(contents) == {'COMMIT.json', 'SOURCE_COPY_RECEIPT.json'}
        | {'adapter/' + name for name in commit['adapter_files']}, 'complete_adapter_archive')
    require(all(checksum(contents['adapter/' + name]) == expected_sha
        for name, expected_sha in commit['adapter_files'].items()), 'copied_adapter_hashes')
    proof = parse(contents['SOURCE_COPY_RECEIPT.json'])
    require(proof['schema'] == 'R146_SOURCE_COPY_RECEIPT_V1' and proof['checkpoint'] == expected
        and proof['before_after_verified'] is True and all(proof[name] is False for name in
        ('source_writes', 'checkpoint_requested', 'held_or_TRAIN_opened', 'optimizer_or_RNG_opened', 'model_imported')),
        'safe_source_copy_proof')
    return contents, proof


def verify_original_receipts(originals):
    require(isinstance(originals, dict) and set(originals) == set(ORIGINALS), 'all_current_originals_verified')
    for name, proof in originals.items():
        require(proof['lineage_id'] == name and proof['before_after_verified'] is True
            and proof['source_writes'] is False and finite_time(proof['observed_unix'])
            and time.time() - proof['observed_unix'] <= 3600
            and proof['checkpoint']['commit_sha256'] == ORIGINALS[name][2]
            and proof['scope'] == 'EXISTING_NODE2_ORIGINAL_BASELINE_COPY', 'fresh_original_copy_receipt')


def destination_originals():
    from gpu import orch_r130_checkpoint_benchmark as runner
    destination_admission()
    root = ROOT + '/checkpoints'
    paths = list(regular(root, ROOT, directory=True).glob('*/manifest.json'))
    require(len(paths) <= 64, 'bounded_original_manifest_inventory')
    originals = {}
    for path in paths:
        raw = bounded_read(str(path), root)
        manifest = parse(raw)
        for name, original in ORIGINALS.items():
            if manifest.get('commit_sha256') != original[2]:
                continue
            require(name not in originals and manifest['adapter_path'] == 'adapter'
                and manifest['commit_path'] == 'COMMIT.json', 'unique_original_local_manifest')
            before = runner.verify_checkpoint(manifest, path.parent)
            after = runner.verify_checkpoint(manifest, path.parent)
            require(before == after and bounded_read(str(path), root) == raw, 'current_original_adapter_verified')
            originals[name] = dict(lineage_id=name, scope='EXISTING_NODE2_ORIGINAL_BASELINE_COPY',
                checkpoint=before, observed_unix=time.time(), before_after_verified=True,
                source_writes=False, manifest_path=str(path), manifest_sha256=checksum(raw))
    verify_original_receipts(originals)
    return originals


def stage_copy(params, raw):
    from gpu import orch_r130_checkpoint_benchmark as runner
    destination_admission()
    verify_original_receipts(params['originals'])
    validate_spec(params['spec'], pinned=True)
    require(re.fullmatch('r146_[a-z0-9_]{1,64}', params['batch_id']) is not None
        and params['role'] in ROLES, 'unique_copy_namespace')
    require(checksum(raw) == params['archive_sha256'], 'source_archive_pin')
    expected = params['discovery']['checkpoints'][params['role']]
    contents, proof = unpack_adapter(raw, expected)
    require(proof['source_spec_sha256'] == digest(params['spec'])
        and proof['discovery_sha256'] == digest(params['discovery'])
        and proof['lineage_id'] == params['spec']['lineage_id'] and proof['role'] == params['role'],
        'source_proof_discovery_chain')
    copies = Path(ROOT) / 'scheduler_inbox/copies'
    name = '_'.join((params['batch_id'], params['spec']['lineage_id'], params['role'], expected['commit_sha256']))
    destination = copies / name
    staging = copies / ('.' + name + '_stage')
    require(not destination.exists() and not destination.is_symlink(), 'copy_is_never_overwritten')
    staging.mkdir(mode=0o700)
    (staging / 'adapter').mkdir(mode=0o700)
    for relative, payload in contents.items():
        immutable(staging / relative, payload)
    manifest = dict(schema='R130_CHECKPOINT_MANIFEST_V1', adapter_path='adapter',
        commit_path='COMMIT.json', commit_sha256=expected['commit_sha256'])
    immutable(staging / 'manifest.json', encoded(manifest))
    runner.verify_checkpoint(manifest, staging)
    destination_admission()
    os.rename(staging, destination)
    runner.verify_checkpoint(manifest, destination)
    return dict(manifest_path=str(destination / 'manifest.json'),
        manifest_sha256=checksum(encoded(manifest)), commit_sha256=expected['commit_sha256'])


def publish_proposal(params):
    from gpu import orch_r130_checkpoint_benchmark as runner
    destination_admission()
    verify_original_receipts(params['originals'])
    validate_spec(params['spec'], pinned=True)
    discovery = params['discovery']
    require(discovery['status'] == 'BASELINES_DISCOVERED_NOT_ENROLLED'
        and discovery['lineage_id'] == params['spec']['lineage_id'], 'proposal_discovery_identity')
    require(set(params['checkpoints']) == set(ROLES), 'all_three_roles_bound')
    for role, bound in params['checkpoints'].items():
        require(set(bound) == {'manifest_path', 'manifest_sha256', 'commit_sha256'}, 'checkpoint_binding_schema')
        path = regular(bound['manifest_path'], ROOT + '/scheduler_inbox/copies')
        require(path.name == 'manifest.json' and path.parent.name.startswith(params['batch_id'] + '_')
            and path.parent.parent == Path(ROOT) / 'scheduler_inbox/copies', 'unique_batch_copy_only')
        raw = bounded_read(str(path), ROOT)
        require(checksum(raw) == bound['manifest_sha256']
            and bound['commit_sha256'] == discovery['checkpoints'][role]['commit_sha256'], 'manifest_and_baseline_pin')
        manifest = parse(raw)
        require(manifest['adapter_path'] == 'adapter' and manifest['commit_path'] == 'COMMIT.json',
            'local_adapter_manifest_only')
        require(runner.verify_checkpoint(manifest, path.parent)['commit_sha256'] == bound['commit_sha256'],
            'manifest_original_COMMIT_binding')
        proof = parse(bounded_read(str(path.parent / 'SOURCE_COPY_RECEIPT.json'), ROOT))
        require(proof['source_spec_sha256'] == digest(params['spec'])
            and proof['discovery_sha256'] == digest(discovery) and proof['role'] == role,
            'copy_custody_proof_binding')
    initial, first = (discovery['checkpoints'][role] for role in ('initial', 'firstsleep'))
    require(initial['optimizer_steps'] == 0 and first['optimizer_steps'] > 0
        and initial['commit_sha256'] != first['commit_sha256'], 'missingbaseline_no_invention')
    receipt = dict(schema=CUSTODY_SCHEMA, status='COPIES_VERIFIED_PROPOSAL_ONLY',
        source_spec=params['spec'], discovery=discovery, originals=params['originals'],
        checkpoints=params['checkpoints'], observed_unix=time.time(),
        limitations=['NOT_MATCHED_TWINS', 'DIFFERENT_SEED_INITIAL_ADAPTER_AND_RUNTIME',
            'DECLARED_PARENTING_NOT_DELIVERY_EVIDENCE', 'NO_HELD_RESULTS_READ',
            'RUNTIME_PINS_FROM_OWNER_METADATA_NOT_PROCESS_ATTESTATION'],
        current_registry_modified=False, ready_published=False)
    receipt_raw = encoded(receipt)
    copies = Path(ROOT) / 'scheduler_inbox/copies'
    receipt_path = copies / (params['batch_id'] + '_' + params['spec']['lineage_id'] + '_custody.json')
    immutable(receipt_path, receipt_raw)
    entry = dict(lineage_id=params['spec']['lineage_id'], cohort='R137',
        initial_commit_sha256=initial['commit_sha256'], first_sleep_commit_sha256=first['commit_sha256'],
        programme_start_unix=discovery['metadata']['origin']['started_unix'])
    require(finite_time(entry['programme_start_unix']), 'programme_start_required')
    proposal = dict(schema=SCHEMA, entry=entry, checkpoints=params['checkpoints'],
        custody=dict(receipt_path=str(receipt_path), receipt_sha256=checksum(receipt_raw)))
    raw = encoded(proposal)
    staging = copies / (params['batch_id'] + '_' + entry['lineage_id'] + '_proposal.json')
    immutable(staging, raw)
    destination_admission()
    directory = Path(ROOT) / 'scheduler_inbox/enrollment_proposals'
    if not directory.exists():
        directory.mkdir(mode=0o700)
    regular(str(directory), ROOT, directory=True)
    destination = directory / (checksum(raw) + '.json')
    os.link(staging, destination)
    require(checksum(destination.read_bytes()) == checksum(raw), 'published_proposal_bytes')
    return dict(status='PROPOSAL_STAGED_NOT_ENROLLED', proposal_path=str(destination),
        proposal_sha256=checksum(raw), custody=proposal['custody'], entry=entry,
        checkpoints=params['checkpoints'], ready_published=False)


def destination_command(action, params):
    require(action in ('admission', 'originals', 'stage', 'propose'), 'no_READY_or_registry_action')
    functions = (require, encoded, digest, checksum, is_hash, object_pairs, parse, finite_time,
        lexical, regular, bounded_read, validate_spec, immutable, destination_admission,
        unpack_adapter, verify_original_receipts, destination_originals, stage_copy, publish_proposal)
    program = 'from pathlib import Path\nimport hashlib,io,json,math,os,re,stat,sys,tarfile,time\n'
    for name in ('SCHEMA', 'SOURCE_SCHEMA', 'CUSTODY_SCHEMA', 'ROOT', 'CONFIG_SHA', 'ADAPTER_NAMES',
            'ROLES', 'LIMIT', 'LIVES', 'ORIGINALS', 'SOURCE_PARENT', 'ROLLOUT'):
        program += name + '=' + repr(globals()[name]) + '\n'
    program += '\n\n'.join(inspect.getsource(function) for function in functions)
    program += '\nparams=json.loads(sys.argv[1])\n'
    if action == 'originals':
        program += 'print(json.dumps(destination_originals()))\n'
    elif action == 'admission':
        program += "destination_admission();print(json.dumps(dict(status='ORIGINAL_DESTINATION_VERIFIED',config_sha256=CONFIG_SHA)))\n"
    elif action == 'stage':
        program += 'print(json.dumps(stage_copy(params,sys.stdin.buffer.read(LIMIT+1024*1024+1))))\n'
    else:
        program += 'print(json.dumps(publish_proposal(params)))\n'
    return ('CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 PYTHONPATH='
        + shlex.quote(ROOT + '/source6_scheduler') + ' /localhome/local-rohing/v2/venv/bin/python -B -c '
        + shlex.quote(program) + ' ' + shlex.quote(json.dumps(params, allow_nan=False)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('source-command', 'destination-command'))
    parser.add_argument('--operation', required=True)
    parser.add_argument('--payload', type=Path, required=True)
    args = parser.parse_args()
    payload = parse(args.payload.read_bytes())
    print(source_command(args.operation, payload) if args.action == 'source-command'
        else destination_command(args.operation, payload))


if __name__ == '__main__':
    main()
