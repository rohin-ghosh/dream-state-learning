"""CPU-only deployment, provenance, and safe-boundary tests using synthetic data."""

from copy import deepcopy
import io
import json
import os
from pathlib import Path
import signal
import tarfile
import time
from types import SimpleNamespace

import pytest

from gpu import orch_r130_benchmark_sidecar as sidecar
from gpu import orch_r130_checkpoint_benchmark as runner


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))
    return sidecar.sha(path)


@pytest.fixture
def setup(tmp_path, monkeypatch):
    source = tmp_path / 'source'
    source.mkdir()
    code = source / 'gpu'
    code.mkdir()
    helper = code / 'orch_r130_benchmark_sidecar.py'
    helper.write_bytes(Path(sidecar.__file__).read_bytes())
    (code / 'orch_r130_checkpoint_benchmark.py').write_bytes(Path(runner.__file__).read_bytes())
    monkeypatch.setattr(sidecar, '__file__', str(helper))
    monkeypatch.setattr(sidecar.socket, 'gethostname', lambda: 'synthetic-fixture-host')
    monkeypatch.setattr(sidecar, 'HOST_SHA256', sidecar.hashlib.sha256(b'synthetic-fixture-host').hexdigest())
    root = tmp_path / 'owned_generators'
    root.mkdir()
    monkeypatch.setattr(sidecar, 'GENERATOR_ROOT', root)
    forks = dict(node='ovx', uuid_by_index=[sidecar.DEVICES[0], sidecar.DEVICES[1]],
        lease_end_unix=time.time() + 86400, hard_deadline_unix=time.time() + 86400 - 21600)
    forks['hard_deadline_unix'] = forks['lease_end_unix'] - 21600
    dump(root / 'FORKS.json', forks)
    sources = sidecar.source_inventory(source)
    config = dict(schema=sidecar.SCHEMA, source_commit=sidecar.SOURCE_COMMIT,
        physical=0, gpu_uuid=sidecar.DEVICES[0], generator_root=str(root), source_root=str(source),
        sources=sources, runner_sha256=sidecar.RUNNER_SHA256, corpus_sha256=sidecar.CORPUS_SHA256,
        created_unix=time.time(), hard_end_unix=time.time() + 3600, lease_end_unix=forks['lease_end_unix'])
    entry = tmp_path / 'BUILDER.md'
    entry.write_text('## [Builder] 2026-09-16 fixture-only CPU gate\n')
    log = tmp_path / 'CPU.log'
    log.write_text('synthetic passing test evidence')
    gate = dict(status='PASS', test_exit_code=0, runner_sha256=sidecar.RUNNER_SHA256,
        corpus_sha256=sidecar.CORPUS_SHA256, source_inventory_sha256=sidecar.digest(sources),
        helper_sha256=sidecar.sha(helper), test_log_path=str(log), test_log_sha256=sidecar.sha(log))
    documents = {
        'cpu_gate': gate,
        'service': {'synthetic_only': True},
        'corpus_manifest': dict(task_file_sha256=sidecar.CORPUS_SHA256, compatible_runner_sha256=sidecar.RUNNER_SHA256),
        'corpus_validation': dict(status='PASS', corpus_sha256=sidecar.CORPUS_SHA256,
            runner_source_sha256=sidecar.RUNNER_SHA256),
    }
    paths = {'forks': root / 'FORKS.json', 'builder_entry': entry}
    for name, document in documents.items():
        paths[name] = tmp_path / (name + '.json')
        dump(paths[name], document)
    for name, path in paths.items():
        config[name + '_path'], config[name + '_sha256'] = str(path), sidecar.sha(path)
    config['jobs'] = []
    for label in sidecar.LABELS[0]:
        plan = dict(gpu_uuid=sidecar.DEVICES[0], corpus_sha256=sidecar.CORPUS_SHA256, sources=sources,
            source_root=str(source), hard_end_unix=config['hard_end_unix'])
        path = tmp_path / (label + '.json')
        dump(path, plan)
        config['jobs'].append(dict(label=label, plan_path=str(path), plan_sha256=sidecar.sha(path),
            checkpoint_commit_sha256='a' * 64))
    config_path = tmp_path / 'config.json'

    def bind():
        dump(config_path, config)
        monkeypatch.setenv('R130_SIDECAR_ADMISSION_SHA256', sidecar.sha(config_path))

    bind()
    monkeypatch.setattr(runner, 'prepare', lambda path: dict(tasks=[{}] * 30,
        checkpoint={'commit_sha256': 'a' * 64}))
    return SimpleNamespace(config=config, config_path=config_path, bind=bind, root=root, source=source, paths=paths)


def test_cpu_preflight_requires_exact_sources_gate_corpus_lease_and_order(setup):
    assert sidecar.validate(setup.config_path, 0, preflight=True) == setup.config


@pytest.mark.parametrize('mutation', ['device', 'commit', 'host', 'env', 'deadline', 'lease_margin',
    'gate', 'test_log', 'builder', 'source', 'job_order', 'job_hash', 'corpus_hash', 'generator_root'])
def test_admission_blocks_drift_before_signals(setup, monkeypatch, mutation):
    config = setup.config
    if mutation == 'device':
        config['physical'] = 3
    elif mutation == 'commit':
        config['source_commit'] = '0' * 40
    elif mutation == 'host':
        monkeypatch.setattr(sidecar.socket, 'gethostname', lambda: 'wrong-fixture-host')
    elif mutation == 'env':
        monkeypatch.delenv('R130_SIDECAR_ADMISSION_SHA256')
    elif mutation == 'deadline':
        config['hard_end_unix'] = time.time() + 10000
    elif mutation == 'lease_margin':
        forks = sidecar.read(setup.paths['forks'])
        forks['hard_deadline_unix'] += 1
        config['forks_sha256'] = dump(setup.paths['forks'], forks)
    elif mutation == 'gate':
        gate = sidecar.read(setup.paths['cpu_gate'])
        gate['test_exit_code'] = 1
        config['cpu_gate_sha256'] = dump(setup.paths['cpu_gate'], gate)
    elif mutation == 'test_log':
        Path(sidecar.read(setup.paths['cpu_gate'])['test_log_path']).write_text('modified')
    elif mutation == 'builder':
        setup.paths['builder_entry'].write_text('not an admitted Builder gate')
        config['builder_entry_sha256'] = sidecar.sha(setup.paths['builder_entry'])
    elif mutation == 'source':
        (setup.source / 'extra.py').write_text('unbound = True')
    elif mutation == 'job_order':
        config['jobs'].reverse()
    elif mutation == 'job_hash':
        config['jobs'][0]['plan_sha256'] = '0' * 64
    elif mutation == 'corpus_hash':
        config['corpus_sha256'] = '0' * 64
    else:
        config['generator_root'] = '/not-authorized'
    if mutation != 'env':
        setup.bind()
    with pytest.raises(ValueError):
        sidecar.validate(setup.config_path, 0, preflight=True)


@pytest.mark.parametrize('physical', [-1, 2, 3, 6, 7])
def test_nonowned_devices_are_always_rejected(setup, physical):
    with pytest.raises(ValueError, match='only_ovx'):
        sidecar.validate(setup.config_path, physical)


def test_environment_is_restored_even_on_error(tmp_path, monkeypatch):
    path = tmp_path / 'plan.json'
    path.write_text('{}')
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES', 'original')
    monkeypatch.delenv('R130_ADMISSION_PLAN_SHA256', raising=False)
    with pytest.raises(RuntimeError):
        with sidecar.plan_environment(path, sidecar.DEVICES[0]):
            assert os.environ['R130_ADMISSION_PLAN_SHA256'] == sidecar.sha(path)
            raise RuntimeError('fixture')
    assert os.environ['CUDA_VISIBLE_DEVICES'] == 'original'
    assert 'R130_ADMISSION_PLAN_SHA256' not in os.environ


@pytest.mark.parametrize('member', ['../escape', '/absolute', 'link', 'duplicate'])
def test_archive_safety_rejects_traversal_links_duplicates(tmp_path, member):
    archive = tmp_path / 'bundle.tar'
    with tarfile.open(archive, 'w') as stream:
        info = tarfile.TarInfo(member)
        if member == 'link':
            info.type, info.linkname = tarfile.SYMTYPE, '/outside'
        stream.addfile(info)
        if member == 'duplicate':
            stream.addfile(info)
    with pytest.raises(ValueError, match='regular_unique'):
        sidecar.extract_regular_archive(archive, tmp_path / 'dest', sidecar.sha(archive))
    assert not (tmp_path / 'dest').exists()


def test_archive_extracts_only_bound_regular_bytes(tmp_path):
    archive = tmp_path / 'bundle.tar'
    with tarfile.open(archive, 'w') as stream:
        info = tarfile.TarInfo('adapter/config.json')
        raw = b'fixture'
        info.size = len(raw)
        stream.addfile(info, io.BytesIO(raw))
    result = sidecar.extract_regular_archive(archive, tmp_path / 'dest', sidecar.sha(archive))
    assert (tmp_path / 'dest/adapter/config.json').read_bytes() == b'fixture'
    assert result['files']['adapter/config.json'] == sidecar.sha(tmp_path / 'dest/adapter/config.json')
    with pytest.raises(ValueError):
        sidecar.extract_regular_archive(archive, tmp_path / 'dest2', '0' * 64)


def make_boundary(directory, family='math'):
    dump(directory / 'PROGRESS.json', dict(calls=2, batch=3, position=4, finished_unix=10))
    dump(directory / 'CALL_000002.json', dict(response={'raw': 'synthetic'}, family=family, finished_unix=9))


def test_safe_boundary_requires_committed_progress_and_complete_route(tmp_path):
    make_boundary(tmp_path)
    assert sidecar.boundary(tmp_path)['calls'] == 2
    dump(tmp_path / 'INTENT_000003.json', {})
    assert sidecar.boundary(tmp_path) is None
    (tmp_path / 'INTENT_000003.json').unlink()
    make_boundary(tmp_path, 'route')
    with pytest.raises(ValueError, match='route_episode'):
        sidecar.boundary(tmp_path)
    dump(tmp_path / 'EPISODE_0003_04.json', {})
    assert sidecar.boundary(tmp_path)
    dump(tmp_path / 'FAILED_000001.json', {})
    with pytest.raises(ValueError, match='failed_capture'):
        sidecar.boundary(tmp_path)


def test_candidate_boundary_never_reads_large_capture_before_pause(tmp_path, monkeypatch):
    make_boundary(tmp_path)
    original = sidecar.read

    def read(path):
        assert Path(path).name == 'PROGRESS.json'
        return original(path)

    monkeypatch.setattr(sidecar, 'read', read)
    assert sidecar.candidate_boundary(tmp_path)['calls'] == 2


def release_fixture(setup, tmp_path, monkeypatch):
    config = deepcopy(setup.config)
    stage = setup.root / 'gpu0/segment0001'
    stage.mkdir(parents=True)
    generator = dict(pid=11, uid=os.getuid(), start_ticks='fixture', boot_id='fixture')
    supervisor = dict(generator, pid=12)
    dump(stage / 'LAUNCH.json', {'identity': generator})
    dump(stage / 'PLAN.json', {})
    make_boundary(stage / 'gpu0')
    config.update(stage=str(stage), generator=generator, supervisor=supervisor,
        generator_cmdline_sha256='a' * 64, supervisor_cmdline_sha256='b' * 64, _sha256='c' * 64)
    signals = []
    monkeypatch.setattr(sidecar, 'identity', lambda pid: generator if pid == 11 else supervisor)
    monkeypatch.setattr(sidecar, 'owned_descriptor', lambda expected, *args: expected['pid'])
    monkeypatch.setattr(sidecar, 'wait_stopped', lambda expected: None)
    monkeypatch.setattr(sidecar.signal, 'pidfd_send_signal', lambda descriptor, event: signals.append((descriptor, event)))
    monkeypatch.setattr(sidecar.os, 'close', lambda descriptor: None)
    monkeypatch.setattr(sidecar, 'gone', lambda expected: True)
    directory = tmp_path / 'release'
    directory.mkdir()
    return config, signals, directory


def test_retirement_targets_only_bound_pair_and_preserves_outputs(setup, tmp_path, monkeypatch):
    config, signals, directory = release_fixture(setup, tmp_path, monkeypatch)
    sidecar.retire(config, directory)
    assert signals[:2] == [(12, signal.SIGSTOP), (11, signal.SIGSTOP)]
    assert set(descriptor for descriptor, event in signals) == {11, 12}
    assert (12, signal.SIGTERM) in signals and (11, signal.SIGTERM) in signals
    preserved = sidecar.read(directory / 'PRESERVED_CAPTURES.json')
    assert all(sidecar.sha(Path(config['stage']) / name) == checksum for name, checksum in preserved['files'].items())
    assert sidecar.read(directory / 'RELEASED.json')['status'] == 'SAFE_TASK_BOUNDARY_RELEASED'


def test_failed_boundary_recheck_resumes_without_retirement(setup, tmp_path, monkeypatch):
    config, signals, directory = release_fixture(setup, tmp_path, monkeypatch)
    original = sidecar.boundary
    calls = []

    def boundary(path):
        calls.append(path)
        if len(calls) == 2:
            raise ValueError('synthetic changed boundary')
        return original(path)

    monkeypatch.setattr(sidecar, 'boundary', boundary)
    with pytest.raises(ValueError, match='changed boundary'):
        sidecar.retire(config, directory)
    assert all(event != signal.SIGTERM for _, event in signals)
    assert (11, signal.SIGCONT) in signals and (12, signal.SIGCONT) in signals
    assert not (directory / 'RELEASED.json').exists()


def test_cli_sanitizes_private_exception_text(monkeypatch, capsys):
    def fail(*args, **kwargs):
        raise ValueError('synthetic private endpoint or held answer')

    monkeypatch.setattr(sidecar, 'validate', fail)
    assert sidecar.main(['preflight', '--config', 'fixture', '--physical', '0']) == 1
    output = capsys.readouterr()
    assert 'synthetic private' not in output.out + output.err
    assert json.loads(output.out)['status'] == 'FAILED'


def test_owned_descriptor_checks_exact_physical_role_and_command(tmp_path, monkeypatch):
    expected = dict(pid=11, uid=os.getuid(), start_ticks='fixture', boot_id='fixture')
    process = tmp_path / '11'
    process.mkdir()
    args = ['python', 'script.py', 'generate', '--root', str(sidecar.GENERATOR_ROOT), '--index', '0']
    raw = ('\0'.join(args) + '\0').encode()
    (process / 'cmdline').write_bytes(raw)
    (process / 'environ').write_text('CUDA_VISIBLE_DEVICES=' + sidecar.DEVICES[0] + '\0')
    monkeypatch.setattr(sidecar, 'Path', lambda value: tmp_path if value == '/proc' else Path(value))
    monkeypatch.setattr(sidecar, 'identity', lambda pid: expected)
    monkeypatch.setattr(sidecar.os, 'pidfd_open', lambda pid: 99)
    checksum = sidecar.hashlib.sha256(raw).hexdigest()
    assert sidecar.owned_descriptor(expected, 0, 'generate', checksum) == 99
    with pytest.raises(ValueError, match='generation_only'):
        sidecar.owned_descriptor(expected, 1, 'generate', checksum)
    with pytest.raises(ValueError, match='command_hash'):
        sidecar.owned_descriptor(expected, 0, 'generate', '0' * 64)


def test_private_curve_requires_bound_raw_receipts(tmp_path, monkeypatch):
    task = dict(task_id='synthetic', family='fixture', messages=[dict(role='user', content='fixture')],
        scoring=dict(type='choice', answer='A', choices=['A', 'B'], response_format='text'))
    corpus = tmp_path / 'tasks.json'
    dump(corpus, dict(schema=runner.TASK_SCHEMA, tasks=[task]))
    output = tmp_path / 'output'
    output.mkdir()
    plan = tmp_path / 'plan.json'
    dump(plan, dict(corpus_path=str(corpus), output_path=str(output)))
    commit_sha = dump(output / 'COMMIT.original.json', dict(optimizer_steps=0))
    job = dict(label='fixture', plan_path=str(plan), plan_sha256=sidecar.sha(plan),
        checkpoint_commit_sha256=commit_sha)
    receipts = {'COMMIT.original.json': commit_sha}
    for position, condition in enumerate(runner.CONDITIONS):
        name = f'CALL_{position:05d}.json'
        record = dict(task_id=task['task_id'], condition=condition, status='COMPLETE', response_valid=True,
            score=runner.score_response(task, 'A'))
        receipts[name] = dump(output / name, record)
    dump(output / 'COMPLETE.json', dict(status='COMPLETE', before_after_verified=True,
        plan_sha256=job['plan_sha256'], corpus_sha256=sidecar.CORPUS_SHA256,
        checkpoint={'commit_sha256': commit_sha}, receipts=receipts, coverage={}))
    path = sidecar.private_curve({'jobs': [job]}, ['fixture'], tmp_path)
    assert sidecar.read(path)['rows'][0]['families']['fixture']['LORA_ON']['correct_items'] == 1
    assert sidecar.read(path)['rows'][0]['optimizer_steps'] == 0
    (output / 'CALL_00000.json').write_text('{}')
    with pytest.raises(ValueError, match='receipt_binding'):
        sidecar.private_curve({'jobs': [job]}, ['fixture'], tmp_path)


@pytest.mark.parametrize('steps', [0, 48])
def test_curve_steps_come_from_original_commit_without_operator_metadata(tmp_path, steps):
    checksum = dump(tmp_path / 'COMMIT.original.json', dict(optimizer_steps=steps))
    complete = dict(checkpoint={'commit_sha256': checksum})
    job = dict(checkpoint_commit_sha256=checksum)
    assert sidecar.checkpoint_steps(tmp_path, complete, job) == steps
    assert sidecar.checkpoint_steps(tmp_path, complete, dict(job, optimizer_steps=steps)) == steps
    with pytest.raises(ValueError, match='must_match_native_commit'):
        sidecar.checkpoint_steps(tmp_path, complete, dict(job, optimizer_steps=steps + 1))
    with pytest.raises(ValueError, match='original_commit_binding'):
        sidecar.checkpoint_steps(tmp_path, complete, dict(job, checkpoint_commit_sha256='0' * 64))


@pytest.mark.parametrize('steps', [None, True, -1, 1.5, '48'])
def test_curve_rejects_missing_or_invalid_native_step_metadata(tmp_path, steps):
    checksum = dump(tmp_path / 'COMMIT.original.json', dict(optimizer_steps=steps))
    with pytest.raises(ValueError, match='native_optimizer_steps'):
        sidecar.checkpoint_steps(tmp_path, {'checkpoint': {'commit_sha256': checksum}},
            {'checkpoint_commit_sha256': checksum})


def test_kernel_followup_requires_both_completed_matrices_and_release_receipts(tmp_path):
    prior = []
    for physical in (0, 1):
        config = dict(physical=physical, source_commit=sidecar.SOURCE_COMMIT,
            corpus_sha256=sidecar.CORPUS_SHA256, gpu_uuid=sidecar.DEVICES[physical],
            generator={'pid': 11 + physical}, supervisor={'pid': 21 + physical})
        path = tmp_path / f'config{physical}.json'
        config_sha = dump(path, config)
        complete = tmp_path / f'complete{physical}.json'
        complete_sha = dump(complete, dict(status='COMPLETE', completed=list(sidecar.LABELS[physical]),
            config_sha256=config_sha))
        release = tmp_path / f'release{physical}.json'
        release_sha = dump(release, dict(status='SAFE_TASK_BOUNDARY_RELEASED', physical=physical,
            generator=config['generator'], supervisor=config['supervisor']))
        prior.append(dict(config_path=str(path), config_sha256=config_sha,
            complete_path=str(complete), complete_sha256=complete_sha,
            release_path=str(release), release_sha256=release_sha))
    sidecar.verify_prior_matrix(prior)
    with pytest.raises(ValueError, match='both_initial'):
        sidecar.verify_prior_matrix(prior[:1])
    changed = deepcopy(prior)
    document = sidecar.read(changed[1]['complete_path'])
    document['status'] = 'FAILED'
    changed[1]['complete_sha256'] = dump(Path(changed[1]['complete_path']), document)
    with pytest.raises(ValueError, match='must_finish'):
        sidecar.verify_prior_matrix(changed)


def test_kernel_followup_never_admits_an_unfinished_matrix(setup):
    setup.config['matrix'] = 'kernel_followup'
    setup.config['prior_matrix'] = []
    for job, label in zip(setup.config['jobs'], sidecar.KERNEL_LABELS):
        job['label'] = label
    setup.bind()
    with pytest.raises(ValueError, match='both_initial'):
        sidecar.validate(setup.config_path, 0)


def test_admission_wait_preserves_idle_tail_and_requires_new_clear_scan(tmp_path, monkeypatch):
    reports = iter([dict(clear=False, blocking_reasons=['device_not_idle']), dict(clear=True, blocking_reasons=[])])
    monkeypatch.setattr(sidecar, 'scan', lambda config: next(reports))
    monkeypatch.setattr(sidecar.time, 'sleep', lambda seconds: None)
    path = sidecar.await_clear({'hard_end_unix': time.time() + 1000}, tmp_path, 'fixture')
    assert path.name == 'fixture.ADMISSION_001.private.json'
    assert sidecar.read(tmp_path / 'fixture.ADMISSION_000.private.json')['clear'] is False
    assert sidecar.read(path)['clear'] is True


def test_admission_wait_is_bounded_and_never_clears_a_block(tmp_path, monkeypatch):
    times = iter([0, 0, 200])
    monkeypatch.setattr(sidecar.time, 'time', lambda: next(times))
    monkeypatch.setattr(sidecar.time, 'sleep', lambda seconds: None)
    monkeypatch.setattr(sidecar, 'scan', lambda config: dict(clear=False, blocking_reasons=['owned_elsewhere']))
    with pytest.raises(TimeoutError, match='no_model_call'):
        sidecar.await_clear({'hard_end_unix': 1000}, tmp_path, 'fixture')
    assert sidecar.read(tmp_path / 'fixture.ADMISSION_000.private.json')['clear'] is False


def test_retained_successes_cannot_skip_a_prefix_or_replay_all_jobs(setup):
    setup.config['retained_completed'] = [{'label': 'legacy_sleep17'}]
    setup.bind()
    with pytest.raises(ValueError, match='ordered_prefix'):
        sidecar.validate(setup.config_path, 0)
    setup.config['retained_completed'] = [{'label': label} for label in sidecar.LABELS[0]]
    setup.bind()
    with pytest.raises(ValueError, match='ordered_prefix'):
        sidecar.validate(setup.config_path, 0)


def test_retention_rejects_unbound_complete_bytes(tmp_path):
    path = tmp_path / 'config.json'
    dump(path, {})
    retained = dict(original_config_path=str(path), original_config_sha256='0' * 64)
    with pytest.raises(ValueError, match='retained_receipt_binding'):
        sidecar.verify_retained({}, {}, retained)


def test_retention_requires_every_original_call_without_rerunning(setup, tmp_path, monkeypatch):
    tasks = [dict(task_id=str(index), family='fixture', messages=[dict(role='user', content='fixture')],
        scoring={'type': 'behavior'}) for index in range(30)]
    corpus = tmp_path / 'retained-corpus.json'
    corpus_sha = dump(corpus, dict(schema=runner.TASK_SCHEMA, tasks=tasks))
    monkeypatch.setattr(sidecar, 'CORPUS_SHA256', corpus_sha)
    output = tmp_path / 'retained-output'
    output.mkdir()
    manifest = tmp_path / 'retained-manifest.json'
    dump(manifest, {})
    monkeypatch.setattr(runner, 'verify_checkpoint', lambda *args: {'commit_sha256': 'a' * 64})
    plan_path = tmp_path / 'retained-plan.json'
    plan = dict(corpus_sha256=corpus_sha, corpus_path=str(corpus), sources=setup.config['sources'],
        source_root=str(setup.source), manifest_path=str(manifest), manifest_sha256=sidecar.sha(manifest),
        output_path=str(output))
    dump(plan_path, plan)
    job = dict(label='legacy_initial', plan_path=str(plan_path), plan_sha256=sidecar.sha(plan_path),
        checkpoint_commit_sha256='a' * 64)
    config = dict(physical=0, gpu_uuid=sidecar.DEVICES[0], source_commit=sidecar.SOURCE_COMMIT,
        corpus_sha256=corpus_sha, jobs=[job], generator={'pid': 11}, supervisor={'pid': 12})
    original = tmp_path / 'original-config.json'
    dump(original, config)
    release = tmp_path / 'original-release.json'
    dump(release, dict(status='SAFE_TASK_BOUNDARY_RELEASED', physical=0,
        generator=config['generator'], supervisor=config['supervisor']))
    receipts = {}
    for index, task in enumerate(tasks):
        for position, condition in enumerate(runner.CONDITIONS):
            name = f'CALL_{index * 2 + position:05d}.json'
            receipts[name] = dump(output / name, dict(task_id=task['task_id'], condition=condition,
                status='COMPLETE', response_valid=True, score=runner.score_response(task, 'fixture')))
    complete = dict(status='COMPLETE', before_after_verified=True, calls=60,
        plan_sha256=job['plan_sha256'], corpus_sha256=corpus_sha,
        checkpoint={'commit_sha256': 'a' * 64}, receipts=receipts)
    path = output / 'COMPLETE.json'
    dump(path, complete)
    retained = dict(label=job['label'], original_config_path=str(original), original_config_sha256=sidecar.sha(original),
        complete_path=str(path), complete_sha256=sidecar.sha(path), release_path=str(release), release_sha256=sidecar.sha(release))
    sidecar.verify_retained(config, job, retained)
    complete['receipts'].pop('CALL_00000.json')
    retained['complete_sha256'] = dump(path, complete)
    with pytest.raises(ValueError, match='cell_inventory'):
        sidecar.verify_retained(config, job, retained)
