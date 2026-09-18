"""CPU-only immutable copy tests; all file contents are synthetic fixtures."""

import io
import json
from pathlib import Path
import shlex
import sys
import tarfile
import time
from types import SimpleNamespace

import pytest

from gpu import orch_r130_checkpoint_copier as copier


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))
    return copier.sha(path)


@pytest.fixture
def source(tmp_path):
    runner = copier.scheduler.sidecar.runner
    root = tmp_path / 'source/run1/checkpoints'

    def checkpoint(name, steps, created):
        directory = root / name
        adapter = directory / 'adapter'
        adapter.mkdir(parents=True)
        (adapter / 'adapter_model.safetensors').write_bytes(('synthetic ' + name).encode())
        dump(adapter / 'adapter_config.json', {'synthetic_only': True})
        files = {path.name: copier.sha(path) for path in adapter.iterdir()}
        path = directory / 'COMMIT.json'
        checksum = dump(path, dict(schema=runner.NATIVE_SCHEMA, base_sha256=runner.BASE_SHA256,
            adapter_files=files, adapter_state_sha256='a' * 64, optimizer_steps=steps,
            created_unix=created, adapter_path='/unavailable/original/adapter',
            optimizer_rng_path='/never/open/optimizer_rng.pt', checkpoint_sha256={'adapter': copier.scheduler.digest(files)}))
        (directory / 'optimizer_rng.pt').write_bytes(b'never read')
        return path, checksum

    initial, initial_sha = checkpoint('initial', 0, time.time() - 1000)
    latest, latest_sha = checkpoint('sleep_000003', 137, time.time() - 100)
    (root.parent / 'TRAIN.jsonl').write_bytes(b'never inspect')
    params = dict(lineage_id='kernel', checkpoint_root=str(root), initial_commit_path=str(initial),
        initial_commit_sha256=initial_sha, native_schema=runner.NATIVE_SCHEMA, base_sha256=runner.BASE_SHA256)
    return SimpleNamespace(root=root, params=params, initial=initial, latest=latest, latest_sha=latest_sha,
        checkpoint=checkpoint)


def test_discover_latest_committed_metadata_ignores_partial_commit(source):
    partial = source.root / 'partial/COMMIT.json'
    partial.parent.mkdir()
    partial.write_text('{')
    result = copier.discover(source.params)
    assert result['selected']['commit_sha256'] == source.latest_sha
    assert result['incomplete_or_invalid_commits'] == 1


def test_pack_only_original_commit_adapter_and_readonly_proof(source, monkeypatch):
    original = Path.read_bytes
    opened = []

    def guarded(path):
        assert 'TRAIN' not in path.name and 'optimizer' not in path.name
        opened.append(path)
        return original(path)

    monkeypatch.setattr(Path, 'read_bytes', guarded)
    selected = copier.discover(source.params)['selected']
    raw = copier.pack(source.params, selected)
    with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
        names = archive.getnames()
        assert names == ['COMMIT.json', 'SOURCE_COPY_RECEIPT.json', 'adapter/adapter_config.json',
            'adapter/adapter_model.safetensors']
        assert archive.extractfile('COMMIT.json').read() == original(source.latest)
        proof = json.loads(archive.extractfile('SOURCE_COPY_RECEIPT.json').read())
        assert proof['before_after_verified'] is True
        assert proof['source_writes'] is False and proof['optimizer_or_TRAIN_opened'] is False
    assert opened and copier.sha(source.latest) == source.latest_sha


@pytest.mark.parametrize('mutation', ['initial', 'selected', 'adapter', 'inventory', 'symlink', 'state'])
def test_copy_rejects_provenance_and_file_drift(source, mutation):
    selected = copier.discover(source.params)['selected']
    directory = source.latest.parent
    if mutation == 'initial':
        source.initial.write_text('{}')
    elif mutation == 'selected':
        selected['commit_sha256'] = '0' * 64
    elif mutation == 'adapter':
        (directory / 'adapter/adapter_model.safetensors').write_bytes(b'changed')
    elif mutation == 'inventory':
        (directory / 'adapter/unexpected').write_text('extra')
    elif mutation == 'symlink':
        target = directory / 'adapter/adapter_model.safetensors'
        target.unlink()
        target.symlink_to(source.initial)
    elif mutation == 'state':
        selected['adapter_state_sha256'] = '0' * 64
    with pytest.raises(ValueError):
        copier.pack(source.params, selected)


def test_source_program_uses_python_wrapper_payload_and_no_training_or_signals(source):
    command = copier.source_command(source.params)
    words = shlex.split(command)
    assert words[:5] == ['PYTHONDONTWRITEBYTECODE=1', 'CUDA_VISIBLE_DEVICES=', 'python3', '-B', '-c']
    assert json.loads(words[-1]) == source.params
    assert 'import torch' not in words[5] and 'subprocess.' not in words[5] and 'os.kill' not in words[5]


@pytest.mark.parametrize('now,expected', [(11 * 3600 + 16 * 60, 11 * 3600 + 27 * 60),
    (11 * 3600 + 28 * 60, 11 * 3600 + 57 * 60), (12 * 3600 + 28 * 60, None)])
def test_copy_cadence_precedes_dispatch_and_stops_before_scheduler_end(now, expected):
    assert copier.next_copy(now, 13 * 3600 + 160) == expected


@pytest.fixture
def destination(source, tmp_path, monkeypatch):
    scheduler = copier.scheduler
    helper = scheduler.sidecar
    root = tmp_path / 'destination'
    (root / 'incoming').mkdir(parents=True)
    (root / 'scheduler_inbox/ready').mkdir(parents=True)
    (root / 'scheduler_inbox/copies').mkdir()
    output = root / 'scheduler_run_v1'
    output.mkdir()
    dump(output / 'STARTED.json', {'identity': {'pid': 123}})
    monkeypatch.setattr(helper, 'gone', lambda identity: False)
    monkeypatch.setattr(copier, 'ROOT', str(root))
    registry = root / 'PRIVATE_RESULTS_REGISTRY.json'
    registry_sha = dump(registry, {'synthetic_only': True})
    monkeypatch.setattr(scheduler, 'REGISTRY_SHA256', registry_sha)
    lineages = root / 'LINEAGES.json'
    lineages_sha = dump(lineages, dict(schema=scheduler.LINEAGES_SCHEMA, lineages=[
        dict(lineage_id=name, cohort='original', initial_commit_sha256=source.params['initial_commit_sha256'])
        for name in ('legacy', 'pilot', 'kernel')]))
    config = dict(registry_path=str(registry), registry_sha256=registry_sha, lineages_path=str(lineages),
        lineages_sha256=lineages_sha, inbox_root=str(root / 'scheduler_inbox'), output_root=str(output),
        hard_end_unix=time.time() + 3600, copy_roots=[str(root / 'scheduler_inbox/copies')])
    config_sha = dump(root / 'SCHEDULER_CONFIG_V1.json', config)
    selected = copier.discover(source.params)['selected']
    archive = copier.pack(source.params, selected)
    payload = dict(lineage_id='kernel', initial_commit_sha256=source.params['initial_commit_sha256'],
        commit_sha256=selected['commit_sha256'], adapter_state_sha256=selected['adapter_state_sha256'],
        archive_sha256=copier.hashlib.sha256(archive).hexdigest())
    local_config = dict(destination_source_root='synthetic-source', scheduler_config_sha256=config_sha)

    def execute(action, contents=archive):
        command = shlex.split(copier.destination_command(local_config, action, payload))
        position = command.index('-c')
        monkeypatch.setattr(sys, 'argv', ['program', command[position + 2], command[position + 3]])
        monkeypatch.setattr(sys, 'stdin', SimpleNamespace(buffer=io.BytesIO(contents)))
        exec(command[position + 1], {})

    return SimpleNamespace(root=root, execute=execute, archive=archive, payload=payload, selected=selected)


def test_destination_verifies_copy_then_atomically_publishes_ready(destination, capsys):
    destination.execute('stage')
    receipt = json.loads(capsys.readouterr().out)
    assert receipt['status'] == 'COPIED_AND_READY_VERIFIED'
    ready = list((destination.root / 'scheduler_inbox/ready').glob('*.json'))
    assert len(ready) == 1 and ready[0].name == copier.sha(ready[0]) + '.json'
    assert not list((destination.root / 'scheduler_inbox/copies').rglob('optimizer*'))
    destination.execute('known')
    assert json.loads(capsys.readouterr().out)['status'] == 'ALREADY_STAGED'
    destination.execute('stage')
    assert json.loads(capsys.readouterr().out)['ready_sha256'] == receipt['ready_sha256']


def test_bad_archive_never_publishes_ready(destination):
    with pytest.raises(ValueError, match='archive_hash'):
        destination.execute('stage', b'corrupted archive')
    assert not list((destination.root / 'scheduler_inbox/ready').iterdir())


def test_wrong_native_state_never_publishes_ready(destination):
    destination.payload['adapter_state_sha256'] = '0' * 64
    with pytest.raises(ValueError, match='state_declaration'):
        destination.execute('stage')
    assert not list((destination.root / 'scheduler_inbox/ready').iterdir())


@pytest.fixture
def admitted_config(tmp_path, monkeypatch):
    repository = Path(copier.__file__).resolve().parents[1]
    selection = tmp_path / 'selection.json'
    entries = [dict(label=lineage + '_initial', path=f'/synthetic/{lineage}/run1/checkpoints/initial/COMMIT.json',
        commit_sha256='a' * 64) for lineage in ('legacy', 'pilot', 'kernel')]
    selection_sha = dump(selection, {'checkpoints': entries})
    sources = []
    for item in entries:
        lineage = item['label'].removesuffix('_initial')
        wrapper = repository / 'gpu' / copier.WRAPPERS[lineage]
        sources.append(dict(lineage_id=lineage, wrapper_path=str(wrapper), wrapper_sha256=copier.sha(wrapper),
            prior_selection_path=str(selection), prior_selection_sha256=selection_sha,
            initial_commit_path=item['path'], initial_commit_sha256=item['commit_sha256'],
            checkpoint_root=str(Path(item['path']).parent.parent), native_schema=copier.scheduler.sidecar.runner.NATIVE_SCHEMA,
            base_sha256=copier.scheduler.sidecar.runner.BASE_SHA256))
    log = tmp_path / 'CPU.log'
    log.write_text('synthetic pass')
    gate = tmp_path / 'gate.json'
    gate_sha = dump(gate, dict(status='PASS', test_exit_code=0, copier_sha256=copier.sha(copier.__file__),
        test_log_path=str(log), test_log_sha256=copier.sha(log)))
    entry = tmp_path / 'builder.md'
    entry.write_text('## [Builder] 2026-09-16 synthetic gate\n')
    now = time.time()
    config = dict(schema=copier.SCHEMA, copier_sha256=copier.sha(copier.__file__),
        scheduler_config_sha256='a22dfa29a16ef419de3cb2e2ad2740b673700c4669c9ecbfc76de1238dea0805',
        destination_source_root=copier.ROOT + '/source6_scheduler',
        destination_wrapper=str(repository / 'gpu/ovx_ssh.sh'),
        destination_wrapper_sha256=copier.sha(repository / 'gpu/ovx_ssh.sh'),
        created_unix=now, hard_end_unix=now + 1800, scheduler_hard_end_unix=now + 3600,
        copy_lead_seconds=180, dispatch_seconds=1800, max_cycles=4,
        builder_entry_path=str(entry), builder_entry_sha256=copier.sha(entry), cpu_gate_path=str(gate), cpu_gate_sha256=gate_sha,
        sources=sources, output_root='/tmp/r130-deploy-20260916/bounded_copy_fixture')
    path = tmp_path / 'config.json'

    def bind():
        monkeypatch.setenv('R130_COPIER_ADMISSION_SHA256', dump(path, config))

    bind()
    return SimpleNamespace(config=config, path=path, bind=bind)


def test_copier_config_binds_wrappers_roots_baselines_cpu_and_wall(admitted_config):
    assert copier.validate(admitted_config.path) == admitted_config.config


@pytest.mark.parametrize('mutation', ['env', 'source', 'wrapper', 'root', 'baseline', 'wall', 'cadence', 'gate', 'enrollment'])
def test_copier_rejects_out_of_scope_admission(admitted_config, monkeypatch, mutation):
    config = admitted_config.config
    if mutation == 'env':
        monkeypatch.setenv('R130_COPIER_ADMISSION_SHA256', '0' * 64)
    else:
        if mutation == 'source':
            config['copier_sha256'] = '0' * 64
        elif mutation == 'wrapper':
            config['sources'][0]['wrapper_path'] = config['sources'][2]['wrapper_path']
        elif mutation == 'root':
            config['sources'][0]['checkpoint_root'] = '/another/root'
        elif mutation == 'baseline':
            config['sources'][0]['initial_commit_sha256'] = '0' * 64
        elif mutation == 'wall':
            config['hard_end_unix'] = config['scheduler_hard_end_unix']
        elif mutation == 'cadence':
            config['max_cycles'] = 999
        elif mutation == 'gate':
            config['cpu_gate_sha256'] = '0' * 64
        elif mutation == 'enrollment':
            config['sources'][0]['lineage_id'] = 'r137_unregistered'
        admitted_config.bind()
    with pytest.raises(ValueError):
        copier.validate(admitted_config.path)
