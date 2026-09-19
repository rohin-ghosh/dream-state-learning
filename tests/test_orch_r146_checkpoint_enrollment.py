"""Synthetic CPU-only custody tests, never an inference or source-node request."""

import copy
import fcntl
import io
import json
from pathlib import Path
import shlex
import subprocess
import sys
import tarfile
import time
from types import SimpleNamespace

import pytest

from gpu import orch_r146_checkpoint_enrollment as enrollment


def dump(path, document):
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = enrollment.encoded(document)
    path.write_bytes(raw)
    return enrollment.binding(path, raw)


@pytest.fixture
def life(tmp_path, monkeypatch):
    monkeypatch.setattr(enrollment, 'SOURCE_PARENT', str(tmp_path))
    monkeypatch.setattr(enrollment, 'ROLLOUT', str(tmp_path / 'rollout'))
    lineage = 'r137_raw_parented_seed1_a40r3'
    root = tmp_path / enrollment.LIVES[lineage]
    start = time.time() - 1000
    metadata = {}
    for stage in ('origin', 'current'):
        parent = root if stage == 'origin' else tmp_path / 'rollout/lane3'
        control = parent / 'control'
        plan = dump(control / 'PLAN.json', dict(schema=enrollment.NATIVE_SCHEMA,
            root=str(root / 'run1'), source_root=str(parent / 'source'), base_sha256=enrollment.BASE_SHA,
            seed=1, presleep_variant='free_distillation', birth_prompt='PRIVATE_SOURCE_BIRTH',
            system_prompt='PRIVATE_SYSTEM', anchors={'never_open': 'TRAIN_SENTINEL'}))
        guard = dump(control / 'GUARD.json', dict(plan_path=plan['path'], plan_sha256=plan['sha256'],
            attempt_dir=str(control), source_pins={'gpu/orch_r125_continual_native.py': 'a' * 64,
                'organism_v6/orch_r125_continual_stream.py': 'b' * 64}))
        launch = dump(control / 'LAUNCH.json', dict(plan_sha256=plan['sha256'], guard_sha256=guard['sha256'],
            started_unix=start if stage == 'origin' else start + 200))
        metadata[stage] = dict(plan=plan, guard=guard, launch=launch)
    spec = dict(schema=enrollment.SOURCE_SCHEMA, lineage_id=lineage, life_root=str(root),
        metadata=metadata, classification=dict(programme='raw', parenting='socratic_sparse3_declared',
            seed=1, replay='free_distillation', matched_control=False))

    def checkpoint(name, steps, created):
        directory = root / 'run1/checkpoints' / name
        adapter = directory / 'adapter'
        adapter.mkdir(parents=True)
        (adapter / 'adapter_model.safetensors').write_bytes(('synthetic_' + name).encode())
        dump(adapter / 'adapter_config.json', {'synthetic': True})
        (adapter / 'README.md').write_bytes(b'opaque adapter model card')
        files = {path.name: enrollment.checksum(path.read_bytes()) for path in adapter.iterdir()}
        document = dict(schema=enrollment.NATIVE_SCHEMA, base_sha256=enrollment.BASE_SHA,
            adapter_path=str(adapter), adapter_files=files, adapter_state_sha256='c' * 64,
            optimizer_rng_path=str(directory / 'optimizer_rng.pt'),
            checkpoint_sha256=dict(adapter=enrollment.digest(files), optimizer='d' * 64, rng='d' * 64),
            optimizer_steps=steps, created_unix=created,
            experiment=dict(schema='R133_CONTINUAL_EXPERIMENT_V1', seed=1,
                presleep_variant='free_distillation', compaction_invitation='PRIVATE_COMPACTION',
                system_prompt='PRIVATE_SYSTEM', birth_prompt='PRIVATE_SOURCE_BIRTH', seed_initialization='before_lora'))
        dump(directory / 'COMMIT.json', document)
        (directory / 'optimizer_rng.pt').write_bytes(b'NO_OPTIMIZER_RNG_READ')
        return directory / 'COMMIT.json'

    checkpoint('initial', 0, start + 10)
    checkpoint('sleep_000001', 5, start + 100)
    checkpoint('sleep_000003', 15, start + 300)
    (root / 'run1/TRAIN.jsonl').write_bytes(b'NO_TRAIN_READ')
    return spec


def params_for(life):
    discovery = enrollment.discover(life)
    return dict(spec=life, discovery=discovery, role='initial', batch_id='r146_test',
        originals={name: dict(lineage_id=name, before_after_verified=True, source_writes=False,
            scope='EXISTING_NODE2_ORIGINAL_BASELINE_COPY', observed_unix=time.time(),
            checkpoint=dict(commit_sha256=value[2])) for name, value in enrollment.ORIGINALS.items()})


def test_exact_discovery_no_private_projection(life):
    found = enrollment.discover(life)
    assert found['checkpoints']['initial']['optimizer_steps'] == 0
    assert found['checkpoints']['firstsleep']['optimizer_steps'] == 5
    assert found['checkpoints']['latest']['optimizer_steps'] == 15
    assert found['metadata']['origin']['started_unix'] < found['metadata']['current']['started_unix']
    for token in ('PRIVATE_SOURCE_BIRTH', 'PRIVATE_SYSTEM', 'PRIVATE_COMPACTION', 'TRAIN_SENTINEL'):
        assert token not in json.dumps(found)


def test_read_set_only_metadata_commits_adapters(life, monkeypatch):
    original = enrollment.bounded_read
    opened = []

    def guarded(value, root, maximum=4 * 1024 * 1024):
        path = Path(value)
        assert path.name in {'PLAN.json', 'GUARD.json', 'LAUNCH.json', 'COMMIT.json'} | enrollment.ADAPTER_NAMES
        opened.append(value)
        return original(value, root, maximum)

    monkeypatch.setattr(enrollment, 'bounded_read', guarded)
    params = params_for(life)
    raw = enrollment.pack(life, params['discovery'], 'latest')
    files, proof = enrollment.unpack_adapter(raw, params['discovery']['checkpoints']['latest'])
    assert set(files) == {'COMMIT.json', 'SOURCE_COPY_RECEIPT.json'} | {'adapter/' + name for name in enrollment.ADAPTER_NAMES}
    assert proof['held_or_TRAIN_opened'] is False
    assert proof['optimizer_or_RNG_opened'] is False
    assert 'PRIVATE_SOURCE_BIRTH' not in json.dumps(proof)
    assert opened


@pytest.mark.parametrize('field', ['schema', 'life_root', 'lineage_id', 'extra', 'matched'])
def test_rejects_scope_schema_and_unproven_twin(life, field):
    if field == 'matched':
        life['classification']['matched_control'] = True
    elif field == 'extra':
        life['messages'] = []
    else:
        life[field] = 'invalid'
    with pytest.raises(ValueError):
        enrollment.validate_spec(life)


@pytest.mark.parametrize('name', ['TRAIN.jsonl', 'optimizer_rng.pt', 'held_results.json', 'credentials.json'])
def test_arbitrary_metadata_path_rejected_before_open(life, name):
    life['metadata']['origin']['plan']['path'] = str(Path(life['life_root']) / 'control' / name)
    with pytest.raises(ValueError, match='only_exact_plan_start_metadata'):
        enrollment.discover(life)


@pytest.mark.parametrize('role', ['initial', 'firstsleep'])
def test_missingbaseline_never_requests_or_invents_checkpoint(life, role):
    path = Path(life['life_root']) / 'run1/checkpoints' / ('initial' if role == 'initial' else 'sleep_000001') / 'COMMIT.json'
    path.unlink()
    found = enrollment.discover(life)
    assert found['status'] == 'MISSING_BASELINE' and found['checkpoint_requested'] is False
    assert 'checkpoints' not in found


@pytest.mark.parametrize('mutation', ['commit', 'adapter', 'plan', 'symlink', 'unexpected_adapter'])
def test_copy_detects_provenance_drift(life, mutation):
    found = enrollment.discover(life)
    path = Path(found['checkpoints']['latest']['commit_path'])
    if mutation == 'commit':
        path.write_text('{}')
    elif mutation == 'plan':
        Path(life['metadata']['current']['plan']['path']).write_text('{}')
    elif mutation == 'unexpected_adapter':
        (path.parent / 'adapter/optimizer_rng.pt').write_bytes(b'forbidden')
    else:
        target = path.parent / 'adapter/adapter_model.safetensors'
        if mutation == 'symlink':
            target.unlink()
            target.symlink_to(path.parent / 'optimizer_rng.pt')
        else:
            target.write_bytes(b'changed')
    with pytest.raises(ValueError):
        enrollment.pack(life, found, 'latest')


def test_nonzero_initial_is_not_baseline(life):
    path = Path(life['life_root']) / 'run1/checkpoints/initial/COMMIT.json'
    document = enrollment.parse(path.read_bytes())
    document['optimizer_steps'] = 2
    dump(path, document)
    with pytest.raises(ValueError, match='step0'):
        enrollment.discover(life)


def test_checkpoint_inventory_cannot_smuggle_optimizer(life):
    path = Path(life['life_root']) / 'run1/checkpoints/initial/COMMIT.json'
    document = enrollment.parse(path.read_bytes())
    document['adapter_files']['optimizer_rng.pt'] = 'a' * 64
    dump(path, document)
    with pytest.raises(ValueError, match='adapter_only_inventory'):
        enrollment.discover(life)


@pytest.mark.parametrize('payload', [b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":Infinity}'])
def test_strict_json(payload):
    with pytest.raises(ValueError):
        enrollment.parse(payload)


@pytest.mark.parametrize('member_name', ['../escape', 'adapter/optimizer_rng.pt', 'held.json'])
def test_archive_rejects_non_adapter_payload(member_name):
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode='w') as archive:
        member = tarfile.TarInfo(member_name)
        member.size = 1
        archive.addfile(member, io.BytesIO(b'x'))
    with pytest.raises(ValueError, match='adapter_only_regular_archive'):
        enrollment.unpack_adapter(output.getvalue(), {})


def test_generated_source_is_standalone_cpu_reader(life):
    command = enrollment.source_command('discover', {'spec': life})
    for forbidden in ('import torch', 'import transformers', 'kill(', 'nvidia-smi', 'ssh ', 'requests.', 'write_bytes('):
        assert forbidden not in command
    words = shlex.split(command)
    result = subprocess.run([sys.executable, '-B', '-c', words[5], words[6]],
        capture_output=True, check=True)
    assert json.loads(result.stdout)['status'] == 'BASELINES_DISCOVERED_NOT_ENROLLED'


def test_no_ready_or_live_config_actions():
    for operation in ('ready', 'admit', 'enroll', 'write_registry', 'run_model'):
        with pytest.raises(ValueError):
            enrollment.destination_command(operation, {})
        with pytest.raises(ValueError):
            enrollment.source_command(operation, {})


def test_a40r_requires_clearance_before_transport(monkeypatch):
    monkeypatch.setattr(subprocess, 'run', lambda *args, **kwargs: pytest.fail('must_not_connect'))
    path = Path(enrollment.__file__).resolve().parents[1] / 'gpu/a40r_ssh.sh'
    with pytest.raises(ValueError, match='clearance_required'):
        enrollment.wrapper_call('a40r_ssh.sh', 'unused', enrollment.checksum(path.read_bytes()))


def test_two_stage_copy_then_proposal_without_ready(life, tmp_path, monkeypatch):
    root = tmp_path / 'destination'
    copies = root / 'scheduler_inbox/copies'
    copies.mkdir(parents=True)
    monkeypatch.setattr(enrollment, 'ROOT', str(root))
    monkeypatch.setattr(enrollment, 'destination_admission', lambda: {})
    params = params_for(life)
    references = {}
    for role in enrollment.ROLES:
        raw = enrollment.pack(life, params['discovery'], role)
        item = dict(params, role=role, archive_sha256=enrollment.checksum(raw))
        references[role] = enrollment.stage_copy(item, raw)
        assert not (root / 'scheduler_inbox/enrollment_proposals').exists()
        with pytest.raises(ValueError, match='never_overwritten'):
            enrollment.stage_copy(item, raw)
    result = enrollment.publish_proposal(dict(params, checkpoints=references))
    assert result['status'] == 'PROPOSAL_STAGED_NOT_ENROLLED' and result['ready_published'] is False
    assert not (root / 'scheduler_inbox/ready').exists()
    assert not list(root.glob('*CONFIG*')) and not list(root.glob('*REGISTRY*'))
    proposal_path = Path(result['proposal_path'])
    assert proposal_path.name == enrollment.checksum(proposal_path.read_bytes()) + '.json'
    proposal = json.loads(proposal_path.read_bytes())
    assert set(proposal) == {'schema', 'entry', 'checkpoints', 'custody'}
    assert set(proposal['entry']) == {'lineage_id', 'cohort', 'initial_commit_sha256',
        'first_sleep_commit_sha256', 'programme_start_unix'}
    custody = Path(proposal['custody']['receipt_path']).read_text()
    assert 'PRIVATE_SOURCE_BIRTH' not in custody and 'PRIVATE_COMPACTION' not in custody


def test_proposal_fails_without_complete_baselines(life, tmp_path, monkeypatch):
    monkeypatch.setattr(enrollment, 'destination_admission', lambda: {})
    with pytest.raises(ValueError, match='all_three_roles'):
        enrollment.publish_proposal(dict(params_for(life), checkpoints={}))


def test_originals_must_be_verified_before_copy(life, monkeypatch):
    monkeypatch.setattr(enrollment, 'destination_admission', lambda: {})
    params = params_for(life)
    params['originals'] = {}
    with pytest.raises(ValueError, match='all_current_originals'):
        enrollment.stage_copy(params, b'')


def test_parent_directory_symlink_rejected(tmp_path):
    (tmp_path / 'real').mkdir()
    (tmp_path / 'real/file').touch()
    (tmp_path / 'alias').symlink_to(tmp_path / 'real', target_is_directory=True)
    with pytest.raises(ValueError, match='symlink'):
        enrollment.bounded_read(str(tmp_path / 'alias/file'), str(tmp_path))


def test_owner_lock_busy_defers_without_source_reads(life, tmp_path, monkeypatch):
    lock_path = Path(enrollment.ROLLOUT) / 'NODE_HANDOFF.lock'
    lock_path.write_bytes(b'owner lock preserved')
    output = io.BytesIO()
    monkeypatch.setattr(enrollment, 'validate_spec', lambda spec: spec)
    monkeypatch.setattr(enrollment, 'discover', lambda spec: pytest.fail('must_defer_without_reads'))
    monkeypatch.setattr(sys, 'stdout', SimpleNamespace(buffer=output))
    delays = []
    monkeypatch.setattr(time, 'sleep', delays.append)
    with lock_path.open('rb') as owner:
        fcntl.flock(owner, fcntl.LOCK_EX | fcntl.LOCK_NB)
        enrollment.source_batch([{'lineage_id': name} for name in enrollment.LIVES])
    assert json.loads(output.getvalue())['status'] == 'DEFERRED_OWNER_HANDOFF_LOCK_BUSY'
    assert lock_path.read_bytes() == b'owner lock preserved' and delays == [15]


def test_owner_lock_is_not_created(life):
    with pytest.raises(FileNotFoundError):
        enrollment.source_batch([life, dict(life, lineage_id='r137_raw_unparented_a40r1',
            life_root=str(Path(enrollment.SOURCE_PARENT) / enrollment.LIVES['r137_raw_unparented_a40r1']),
            classification=dict(programme='raw', parenting='none_declared', seed=0,
                replay='free_distillation', matched_control=False),
            metadata={stage:{kind:dict(item, path=item['path'].replace(enrollment.LIVES['r137_raw_parented_seed1_a40r3'],
                enrollment.LIVES['r137_raw_unparented_a40r1']).replace('/lane3/', '/lane1/'))
                for kind,item in metadata.items()} for stage,metadata in life['metadata'].items()} )])
    assert not (Path(enrollment.ROLLOUT) / 'NODE_HANDOFF.lock').exists()
