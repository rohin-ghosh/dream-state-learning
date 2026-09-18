"""CPU-only scheduler tests; all checkpoints and task data are artificial."""

from copy import deepcopy
import json
import os
from pathlib import Path
from types import SimpleNamespace
import time

import pytest

from gpu import orch_r130_checkpoint_scheduler as scheduler


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))
    return scheduler.sha(path)


def copied_checkpoint(root, name, steps=0, created=None):
    runner = scheduler.sidecar.runner
    directory = root / name
    adapter = directory / 'adapter'
    adapter.mkdir(parents=True)
    (adapter / 'adapter_model.safetensors').write_bytes(b'synthetic-never-loaded-' + name.encode())
    dump(adapter / 'adapter_config.json', {'synthetic': True})
    files = {path.name: scheduler.sha(path) for path in adapter.iterdir()}
    commit = dict(schema=runner.NATIVE_SCHEMA, base_sha256=runner.BASE_SHA256,
        adapter_path='/unreachable/original/adapter', optimizer_rng_path='/unreachable/optimizer.pt',
        adapter_files=files, adapter_state_sha256='a' * 64, optimizer_steps=steps,
        created_unix=created or time.time() - 10, checkpoint_sha256={'adapter': scheduler.digest(files)})
    commit_sha = dump(directory / 'COMMIT.json', commit)
    manifest = directory / 'manifest.json'
    checksum = dump(manifest, dict(schema=runner.MANIFEST_SCHEMA, adapter_path='adapter',
        commit_path='COMMIT.json', commit_sha256=commit_sha))
    return dict(manifest_path=str(manifest), manifest_sha256=checksum, commit_sha256=commit_sha)


@pytest.fixture
def setup(tmp_path, monkeypatch):
    sidecar = scheduler.sidecar
    runner = sidecar.runner
    source = tmp_path / 'source'
    (source / 'gpu').mkdir(parents=True)
    helper = source / 'gpu/orch_r130_checkpoint_scheduler.py'
    helper.write_bytes(Path(scheduler.__file__).read_bytes())
    (source / 'gpu/orch_r130_checkpoint_benchmark.py').write_bytes(Path(runner.__file__).read_bytes())
    monkeypatch.setattr(scheduler, '__file__', str(helper))
    monkeypatch.setattr(scheduler.socket, 'gethostname', lambda: 'synthetic-host')
    monkeypatch.setattr(sidecar, 'HOST_SHA256', scheduler.hashlib.sha256(b'synthetic-host').hexdigest())
    monkeypatch.setattr(sidecar, 'gone', lambda identity: True)
    root = tmp_path / 'operator'
    root.mkdir()
    inbox = root / 'scheduler_inbox'
    inbox.mkdir(mode=0o700)
    (inbox / 'ready').mkdir()
    (inbox / 'copies').mkdir()
    ledger = root / 'scheduler_ledger'
    ledger.mkdir(mode=0o700)
    originals = root / 'checkpoints'
    originals.mkdir()
    generator_root = tmp_path / 'generators'
    monkeypatch.setattr(sidecar, 'GENERATOR_ROOT', generator_root)
    now = time.time()
    config = dict(schema=scheduler.SCHEMA, source_commit=sidecar.SOURCE_COMMIT,
        source_root=str(source), sources=sidecar.source_inventory(source), operator_root=str(root),
        physical_devices=[0, 1], gpu_uuids=list(sidecar.DEVICES.values()),
        inbox_root=str(inbox), ledger_root=str(ledger), copy_roots=[str(originals), str(inbox / 'copies')],
        output_root=str(root / 'scheduler_run_fixture'), created_unix=now,
        hard_end_unix=now + 3600, first_dispatch_unix=now + 1, lease_end_unix=now + 86400,
        poll_seconds=30, dispatch_seconds=1800, max_jobs=4, job_max_seconds=3600, python='/usr/bin/python3')
    rows = []
    lineages = []
    for label, lineage in scheduler.SEED_LABELS.items():
        initial = label.endswith('_initial')
        checkpoint = copied_checkpoint(originals, label, steps=0 if initial else 12)
        complete = root / label / 'COMPLETE.json'
        complete_sha = dump(complete, dict(status='COMPLETE', synthetic_only=True))
        rows.append(dict(label=label, checkpoint_commit_sha256=checkpoint['commit_sha256'],
            complete_path=str(complete), complete_sha256=complete_sha))
        if initial:
            lineages.append(dict(lineage_id=lineage, cohort='original', initial_commit_sha256=checkpoint['commit_sha256']))
    registry = dict(status='EXECUTION_COMPLETE_VERIFIED', corpus_sha256=sidecar.CORPUS_SHA256,
        runner_sha256=sidecar.RUNNER_SHA256, checkpoints=rows)
    corpus = root / 'corpus.json'
    corpus_sha = dump(corpus, {'synthetic_only': True})
    monkeypatch.setattr(sidecar, 'CORPUS_SHA256', corpus_sha)
    registry['corpus_sha256'] = corpus_sha
    release_receipts = []
    for physical in (0, 1):
        path = root / f'release{physical}.json'
        checksum = dump(path, dict(status='SAFE_TASK_BOUNDARY_RELEASED', physical=physical,
            generator={'pid': 111 + physical}, supervisor={'pid': 222 + physical}))
        release_receipts.append(dict(path=str(path), sha256=checksum))
    config['release_receipts'] = release_receipts
    entry = root / 'builder.md'
    entry.write_text('## [Builder] 2026-09-16 synthetic CPU admission\n')
    log = root / 'CPU.log'
    log.write_text('synthetic tests passed')
    documents = dict(registry=registry, lineages=dict(schema=scheduler.LINEAGES_SCHEMA, lineages=lineages),
        cpu_gate=dict(status='PASS', test_exit_code=0, scheduler_sha256=scheduler.sha(helper),
            source_inventory_sha256=scheduler.digest(config['sources']), test_log_path=str(log), test_log_sha256=scheduler.sha(log)),
        forks=dict(node='ovx', uuid_by_index=config['gpu_uuids'], lease_end_unix=config['lease_end_unix'],
            hard_deadline_unix=config['lease_end_unix'] - 21600), service={'synthetic_only': True},
        reservation=dict(node_alias='node2', physical_devices=[0, 1], ad_hoc_generator_takeover_allowed=False,
            preserved_generation_devices=list(range(2, 8))),
        template_plan=dict(model_id=runner.MODEL_ID, base_sha256=runner.BASE_SHA256, decoder=runner.DECODER,
            corpus_path=str(corpus), corpus_sha256=corpus_sha))
    for name, document in documents.items():
        path = generator_root / 'FORKS.json' if name == 'forks' else root / (name + '.json')
        config[name + '_path'] = str(path)
        config[name + '_sha256'] = dump(path, document)
    config.update(builder_entry_path=str(entry), builder_entry_sha256=scheduler.sha(entry),
        corpus_path=str(corpus), corpus_sha256=corpus_sha)
    monkeypatch.setattr(scheduler, 'REGISTRY_SHA256', config['registry_sha256'])
    config_path = root / 'CONFIG.json'

    def bind():
        monkeypatch.setenv('R130_SCHEDULER_ADMISSION_SHA256', dump(config_path, config))
        monkeypatch.setenv('CUDA_VISIBLE_DEVICES', '')

    def ready(lineage='legacy', steps=24, name='new', created=None):
        copied = copied_checkpoint(inbox / 'copies', name, steps, created)
        document = dict(schema=scheduler.READY_SCHEMA, lineage_id=lineage, **copied)
        raw = json.dumps(document).encode()
        path = inbox / 'ready' / (scheduler.hashlib.sha256(raw).hexdigest() + '.json')
        path.write_bytes(raw)
        return path

    bind()
    return SimpleNamespace(config=config, path=config_path, bind=bind, root=root, ready=ready,
        lineages=lineages, inbox=inbox, source=source, rows=rows)


def test_preflight_binds_sources_devices_registry_lease_gate_and_lineages(setup):
    config, lineages, seeds = scheduler.validate(setup.path)
    assert config == setup.config and len(lineages) == 3 and len(seeds) == 6


@pytest.mark.parametrize('mutation,match', [('env', 'admission_binding'), ('device', 'benchmark_devices'),
    ('host', 'bound_node2'), ('source', 'source_binding'), ('registry', 'registry_and_corpus'),
    ('gate', 'CPU_provenance'), ('cpu', 'CPU_only'), ('wall', 'bounded_scheduler_wall'),
    ('lease', 'six_hour_margin'), ('poll', 'bounded_poll'), ('reservation', 'reservation_only'),
    ('retired', 'remain_retired'), ('lineages', 'lineages_hash_binding'), ('output', 'output_scope')])
def test_admission_drift_rejected_before_any_subprocess(setup, monkeypatch, mutation, match):
    config = setup.config
    if mutation == 'env':
        monkeypatch.setenv('R130_SCHEDULER_ADMISSION_SHA256', '0' * 64)
    elif mutation == 'cpu':
        monkeypatch.setenv('CUDA_VISIBLE_DEVICES', '0')
    else:
        if mutation == 'device':
            config['physical_devices'] = [0, 2]
        elif mutation == 'host':
            monkeypatch.setattr(scheduler.sidecar, 'HOST_SHA256', '0' * 64)
        elif mutation == 'source':
            (setup.source / 'gpu/drift.py').write_text('changed')
        elif mutation == 'registry':
            config['registry_sha256'] = '0' * 64
        elif mutation == 'gate':
            path = Path(config['cpu_gate_path'])
            document = scheduler.read(path)
            document['test_exit_code'] = 1
            config['cpu_gate_sha256'] = dump(path, document)
        elif mutation == 'wall':
            config['hard_end_unix'] = config['created_unix'] + 7201
        elif mutation == 'lease':
            config['lease_end_unix'] += 1
        elif mutation == 'poll':
            config['poll_seconds'] = 1
        elif mutation == 'reservation':
            path = Path(config['reservation_path'])
            document = scheduler.read(path)
            document['ad_hoc_generator_takeover_allowed'] = True
            config['reservation_sha256'] = dump(path, document)
        elif mutation == 'retired':
            monkeypatch.setattr(scheduler.sidecar, 'gone', lambda identity: False)
        elif mutation == 'lineages':
            Path(config['lineages_path']).write_text('{}')
        elif mutation == 'output':
            config['output_root'] = str(setup.root / 'checkpoints')
        setup.bind()
    monkeypatch.setattr(scheduler.subprocess, 'Popen', lambda *args, **kwargs: pytest.fail('must not spawn'))
    with pytest.raises(ValueError, match=match):
        scheduler.validate(setup.path)


def test_ready_verifies_local_copy_without_original_absolute_paths(setup):
    _, lineages, _ = scheduler.validate(setup.path)
    path = setup.ready()
    item = scheduler.candidate(setup.config, lineages, path)
    assert item['lineage_id'] == 'legacy' and not item['is_initial']
    assert item['key'] == scheduler.key_for('legacy', item['commit_sha256'])
    assert not list(setup.inbox.rglob('optimizer*'))


@pytest.mark.parametrize('mutation,match', [('unknown', 'lineage_not_pinned'), ('extra', 'ready_fields'),
    ('hash', 'content_addressed'), ('manifest', 'manifest_binding'), ('commit', 'commit_binding'),
    ('outside', 'outside_admitted'), ('symlink', 'symlink'), ('file_drift', 'adapter_file_binding')])
def test_intake_rejects_scope_path_hash_inventory_and_prompt_injection(setup, mutation, match):
    _, lineages, _ = scheduler.validate(setup.path)
    path = setup.ready()
    item = scheduler.read(path)
    if mutation == 'unknown':
        item['lineage_id'] = 'r137_unregistered'
    elif mutation == 'extra':
        item['messages'] = ['synthetic injection must not be consumed']
    elif mutation == 'manifest':
        item['manifest_sha256'] = '0' * 64
    elif mutation == 'commit':
        item['commit_sha256'] = '0' * 64
    elif mutation == 'outside':
        outside = setup.root / 'outside.json'
        outside.write_bytes(Path(item['manifest_path']).read_bytes())
        item['manifest_path'] = str(outside)
    elif mutation == 'symlink':
        link = setup.inbox / 'copies/link.json'
        link.symlink_to(item['manifest_path'])
        item['manifest_path'] = str(link)
    elif mutation == 'file_drift':
        (Path(item['manifest_path']).parent / 'adapter/adapter_model.safetensors').write_bytes(b'changed')
    raw = json.dumps(item).encode()
    modified = path if mutation == 'hash' else path.parent / (scheduler.hashlib.sha256(raw).hexdigest() + '.json')
    modified.write_bytes(raw + b' ' if mutation == 'hash' else raw)
    with pytest.raises(ValueError, match=match):
        scheduler.candidate(setup.config, lineages, modified)


def test_R137_registry_requires_explicit_two_baselines_and_start(setup):
    document = dict(schema=scheduler.LINEAGES_SCHEMA, lineages=deepcopy(setup.lineages))
    item = dict(lineage_id='r137_fixture', cohort='R137', initial_commit_sha256='a' * 64,
        first_sleep_commit_sha256='b' * 64, programme_start_unix=time.time() - 7200)
    document['lineages'].append(item)
    assert 'r137_fixture' in scheduler.enrolled_lineages(document)
    item['first_sleep_commit_sha256'] = None
    with pytest.raises(ValueError, match='baselines_and_start'):
        scheduler.enrolled_lineages(document)
    item['cohort'] = 'R138'
    with pytest.raises(ValueError):
        scheduler.enrolled_lineages(document)


def test_original_queue_chooses_newest_and_deduplicates_completed(setup):
    config, lineages, seeds = scheduler.validate(setup.path)
    old = scheduler.candidate(config, lineages, setup.ready(name='older', created=time.time() - 100))
    new = scheduler.candidate(config, lineages, setup.ready(name='newer'))
    assert scheduler.select_candidates([old, new], seeds, None, 0, seeds, lineages, {}) == [new]
    assert scheduler.select_candidates([new], seeds | {new['key']}, None, 0, seeds, lineages, {}) == []


def test_R137_requires_initial_then_first_sleep_then_earliest_hourly_landmark(setup):
    _, lineages, seeds = scheduler.validate(setup.path)
    name = 'r137_fixture'
    start = time.time() - 10800
    lineages[name] = dict(lineage_id=name, cohort='R137', initial_commit_sha256='a' * 64,
        first_sleep_commit_sha256='b' * 64, programme_start_unix=start)
    items = []
    for checksum, age in [('a', 0), ('b', 100), ('c', 3700), ('d', 4000), ('e', 7100)]:
        items.append(dict(lineage_id=name, cohort='R137', commit_sha256=checksum * 64,
            key=scheduler.key_for(name, checksum * 64), created_unix=start + age,
            is_initial=checksum == 'a', is_first_sleep=checksum == 'b', ready_sha256=checksum * 64))
    assert scheduler.select_candidates(items[1:], seeds, None, 1, seeds, lineages, {}) == []
    assert scheduler.select_candidates(items, seeds, None, 1, seeds, lineages, {}) == [items[0]]
    complete = seeds | {items[0]['key']}
    assert scheduler.select_candidates(items, complete, None, 1, complete, lineages, {name: [start]}) == [items[1]]
    complete.add(items[1]['key'])
    assert scheduler.select_candidates(items, complete, None, 1, complete, lineages,
        {name: [start, start + 100]}) == [items[2]]
    complete.add(items[2]['key'])
    assert scheduler.select_candidates(items, complete, None, 1, complete, lineages,
        {name: [start, start + 100, start + 3700]}) == []


def test_ambiguous_reserved_claim_is_not_replayed_or_counted_complete(setup):
    config, lineages, seeds = scheduler.validate(setup.path)
    item = scheduler.candidate(config, lineages, setup.ready())
    dump(Path(config['ledger_root']) / (item['key'] + '.RESERVED.json'),
        dict(lineage_id=item['lineage_id'], commit_sha256=item['commit_sha256'], corpus_sha256=config['corpus_sha256']))
    taken, completed, _ = scheduler.ledger_state(config, seeds, lineages)
    assert item['key'] in taken and item['key'] not in completed and len(completed) == 6


def test_busy_gpu_defers_without_reservation_spawn_or_signal(setup, monkeypatch):
    config, lineages, _ = scheduler.validate(setup.path)
    item = scheduler.candidate(config, lineages, setup.ready())
    monkeypatch.setattr(scheduler.sidecar, 'scan', lambda config: {'clear': False, 'blocking_reasons': ['occupied']})
    monkeypatch.setattr(scheduler.subprocess, 'Popen', lambda *args, **kwargs: pytest.fail('busy GPU must not spawn'))
    assert scheduler.dispatch(config, setup.path, lineages, item, 0, setup.root) is None
    assert not list(Path(config['ledger_root']).iterdir())


def test_dispatch_has_exact_device_plan_environment_and_fresh_process(setup, monkeypatch):
    config, lineages, _ = scheduler.validate(setup.path)
    item = scheduler.candidate(config, lineages, setup.ready())
    monkeypatch.setattr(scheduler.sidecar, 'scan', lambda config: {'clear': True, 'blocking_reasons': []})
    monkeypatch.setattr(scheduler.sidecar.runner, 'prepare', lambda path:
        dict(tasks=[{}] * 30, checkpoint={'commit_sha256': item['commit_sha256']}))
    observed = []
    monkeypatch.setattr(scheduler.sidecar, 'identity', lambda pid: {'pid': pid})
    monkeypatch.setattr(scheduler.subprocess, 'Popen', lambda command, **kwargs:
        observed.append((command, kwargs)) or SimpleNamespace(pid=777))
    active = scheduler.dispatch(config, setup.path, lineages, item, 1, setup.root)
    command, options = observed[0]
    assert command[:3] == ['timeout', '--signal=TERM', '--kill-after=5s']
    assert command[4:8] == [config['python'], '-B', '-m', 'gpu.orch_r130_checkpoint_benchmark']
    assert options['env']['CUDA_VISIBLE_DEVICES'] == scheduler.sidecar.DEVICES[1]
    assert options['env']['R130_ADMISSION_PLAN_SHA256'] == scheduler.sha(active['job']['plan_path'])
    assert options['start_new_session'] is True
    assert os.environ['CUDA_VISIBLE_DEVICES'] == ''
    assert active['claim_path'].is_file()


def test_bounded_empty_polling_writes_status_only_counts_and_releases_locks(setup, monkeypatch):
    clock = [setup.config['created_unix'] + 1]
    monkeypatch.setattr(scheduler.time, 'time', lambda: clock[0])
    monkeypatch.setattr(scheduler.time, 'sleep', lambda seconds: clock.__setitem__(0, setup.config['hard_end_unix']))
    monkeypatch.setattr(scheduler.subprocess, 'Popen', lambda *args, **kwargs: pytest.fail('empty queue must not spawn'))
    result = scheduler.run(setup.path)
    assert result['status'] == 'BOUNDED_SCHEDULER_FINISHED'
    assert result['completed_checkpoint_count'] == 6 and result['future_completed_checkpoints'] == 0
    status = scheduler.read(Path(setup.config['output_root']) / 'STATUS_000000.json')
    assert status['active_physical'] == [] and status['held_content_or_scores_in_status'] is False
    assert not any(key in status for key in ('scores', 'messages', 'tasks', 'responses'))
    for physical in (0, 1):
        with (setup.root / f'physical{physical}.lock').open('a') as lock:
            scheduler.fcntl.flock(lock.fileno(), scheduler.fcntl.LOCK_EX | scheduler.fcntl.LOCK_NB)


def test_nonzero_native_exit_never_counts_missing_items_as_success(setup):
    directory = setup.root / 'failed_job'
    directory.mkdir()
    job = dict(job_root=directory, item={'key': 'a' * 64})
    assert scheduler.finish(setup.config, job, 1) is False
    assert scheduler.read(directory / 'FAILED.json')['automatic_retry'] is False
    assert not list(Path(setup.config['ledger_root']).glob('*.COMPLETE.json'))


def status_bundle():
    return dict(receipt_sha256='a' * 64, receipt_name='STATUS_000001.json', receipt=dict(
        status='BOUNDED_POLLING', config_sha256='b' * 64, completed_checkpoint_count=6,
        future_completed_checkpoints=0, next_dispatch_unix=1789556400, active_physical=[0],
        observed_unix=1789556300))


def test_status_projection_never_passes_unrecognized_or_private_fields():
    bundle = status_bundle()
    bundle['receipt']['scores'] = 'synthetic forbidden private value'
    projected = scheduler.status_projection(bundle, 'b' * 64)
    assert 'scores' not in projected and 'synthetic forbidden' not in json.dumps(projected)
    assert projected['completed_checkpoint_count'] == 6


@pytest.mark.parametrize('field,value', [('status', 'injected notebook command'),
    ('completed_checkpoint_count', True), ('completed_checkpoint_count', 7),
    ('future_completed_checkpoints', -1), ('next_dispatch_unix', 'injected command'),
    ('active_physical', [2]), ('active_physical', [True]), ('config_sha256', 'c' * 64)])
def test_status_projection_rejects_unsafe_values(field, value):
    bundle = status_bundle()
    bundle['receipt'][field] = value
    with pytest.raises(ValueError):
        scheduler.status_projection(bundle, 'b' * 64)


def test_status_fetch_rejects_remote_path_injection_before_ssh(monkeypatch):
    monkeypatch.setattr(scheduler.subprocess, 'run', lambda *args, **kwargs: pytest.fail('must not call SSH'))
    with pytest.raises(ValueError, match='remote_status_directory'):
        scheduler.fetch_status('synthetic-wrapper', '/tmp/bad; injected-command', 'b' * 64)


def test_notebook_append_only_formats_allowlisted_status_and_retries_concurrent_append(tmp_path, monkeypatch):
    notebook = tmp_path / 'COORDINATION.md'
    notebook.write_text('existing other author\n')
    patches = []

    def apply(command, **kwargs):
        assert command == ['apply_patch']
        patches.append(kwargs['input'])
        if len(patches) == 1:
            notebook.write_text('existing other author\nconcurrent other author\n')
            return SimpleNamespace(returncode=1)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(scheduler.subprocess, 'run', apply)
    status = scheduler.status_projection(status_bundle(), 'b' * 64)
    checksum = scheduler.append_notebook_status(notebook, status)
    assert len(checksum) == 64 and len(patches) == 2
    assert ' concurrent other author' in patches[-1]
    assert 'completed checkpoints=6' in patches[-1] and 'future completed=0' in patches[-1]
    assert 'generators2-7 untouched' in patches[-1]


def test_shared_benchmark_lock_blocks_second_scheduler_before_spawn(setup, monkeypatch):
    monkeypatch.setattr(scheduler.subprocess, 'Popen', lambda *args, **kwargs: pytest.fail('must not spawn'))
    with (setup.root / 'physical1.lock').open('a') as lock:
        scheduler.fcntl.flock(lock.fileno(), scheduler.fcntl.LOCK_EX | scheduler.fcntl.LOCK_NB)
        with pytest.raises(BlockingIOError):
            scheduler.run(setup.path)
    assert not (Path(setup.config['output_root']) / 'STARTED.json').exists()


def test_status_fetch_uses_wrapper_and_returns_only_safe_projection(monkeypatch):
    observed = []

    def fetch(command, **kwargs):
        observed.append(command)
        return SimpleNamespace(stdout=json.dumps(status_bundle()))

    monkeypatch.setattr(scheduler.subprocess, 'run', fetch)
    result = scheduler.fetch_status('fixture/ovx_ssh.sh',
        '/localhome/local-rohing/orch_r130_checkpoint_benchmark_20260916_attempt1/scheduler_run_fixture', 'b' * 64)
    assert observed[0][:2] == ['bash', 'fixture/ovx_ssh.sh']
    assert 'python3 -c ' in observed[0][2] and result['completed_checkpoint_count'] == 6


@pytest.mark.parametrize('missing', [False, True])
def test_finish_validates_all_sixty_cells_before_ledger_success(setup, monkeypatch, missing):
    sidecar = scheduler.sidecar
    runner = sidecar.runner
    directory = setup.root / 'completed_job'
    output = directory / 'results'
    output.mkdir(parents=True)
    tasks = [dict(task_id=f'fixture{index}', family='synthetic', messages=[dict(role='user', content='fixture')],
        scoring=dict(type='choice', choices=['A', 'B'], answer='A', response_format='text')) for index in range(30)]
    corpus = directory / 'tasks.json'
    corpus_sha = dump(corpus, dict(schema=runner.TASK_SCHEMA, tasks=tasks))
    monkeypatch.setattr(sidecar, 'CORPUS_SHA256', corpus_sha)
    commit_sha = dump(output / 'COMMIT.original.json', dict(optimizer_steps=12))
    key = scheduler.key_for('legacy', commit_sha)
    plan = directory / 'plan.json'
    plan_sha = dump(plan, dict(corpus_path=str(corpus), output_path=str(output)))
    records = []
    receipts = {'COMMIT.original.json': commit_sha}
    for task in tasks:
        for condition in runner.CONDITIONS:
            if missing and len(records) == 59:
                continue
            record = dict(task_id=task['task_id'], condition=condition, status='COMPLETE', response_valid=True,
                score=runner.score_response(task, 'A'))
            name = f'CALL_{len(records):05d}.json'
            receipts[name] = dump(output / name, record)
            records.append(record)
    dump(output / 'COMPLETE.json', dict(status='COMPLETE', before_after_verified=True, calls=60,
        corpus_sha256=corpus_sha, plan_sha256=plan_sha, checkpoint={'commit_sha256': commit_sha},
        receipts=receipts, coverage=runner.reduce_coverage(tasks, records)))
    claim = Path(setup.config['ledger_root']) / (key + '.RESERVED.json')
    dump(claim, dict(lineage_id='legacy', commit_sha256=commit_sha, corpus_sha256=corpus_sha,
        plan_path=str(plan), plan_sha256=plan_sha, checkpoint_created_unix=time.time() - 10))
    active = dict(job_root=directory, item={'key': key}, claim_path=claim,
        job=dict(label=key, plan_path=str(plan), plan_sha256=plan_sha, checkpoint_commit_sha256=commit_sha))
    assert scheduler.finish(setup.config, active, 0) is (not missing)
    completed_path = Path(setup.config['ledger_root']) / (key + '.COMPLETE.json')
    assert completed_path.exists() is (not missing)
    assert claim.exists()
    if not missing:
        _, completed, _ = scheduler.ledger_state(setup.config, set(), {})
        assert completed == {key}
