"""CPU-only seam, provenance, lifetime and A100 admission regression checks."""

from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from shutil import copyfile
from types import SimpleNamespace

import pytest

from gpu import orch_r107_continual_capability_run as runner


@pytest.fixture
def seam(tmp_path, monkeypatch):
    training = tmp_path / 'training'
    monkeypatch.setattr(runner.continual, 'ROOT', training)
    path = training / 'R107_CONTINUATION_20260915/READOUT_SEAM.json'
    monkeypatch.setattr(runner, 'SEAM_PATH', path)
    paths = {}
    for arm in ('FULL', 'OFF'):
        destination = training / arm / 'checkpoints/000008932'
        destination.parent.mkdir(parents=True)
        staging = training / arm / 'staging'
        for name in ('optimizer.pt', 'rank0.pt', 'rank1.pt',
                     'adapter/adapter_config.json', 'adapter/adapter_model.safetensors'):
            file = staging / name
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text('mock-' + arm + '-' + name)
        identity = dict(path=str(destination / 'adapter'), state_sha256=('a' if arm == 'FULL' else 'b') * 64,
            base_sha256=runner.paired.BASE_SHA,
            files=[[file.name, runner.sha(file)] for file in sorted((staging / 'adapter').iterdir())])
        metadata = dict(update=8932, corpus_sha256='c' * 64, corpus_version=13,
            exposure_counts={'mock-row': 4}, reference_tokens=200, adapter=identity,
            source_sha256='d' * 64)
        runner.state.commit_checkpoint(staging, destination, metadata)
        paths[arm] = str(destination)
    runner.write(path, dict(time_unix=runner.TRAIN_CUTOFF + 2, update=8932, checkpoint_paths=paths))
    return path


@pytest.fixture
def prepared(tmp_path, monkeypatch, seam):
    source_root = tmp_path / 'source_snapshot'
    for relative in runner.REQUIRED_SOURCES:
        destination = source_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        copyfile(runner.SOURCE_ROOT / relative, destination)
    monkeypatch.setattr(runner, 'SOURCE_ROOT', source_root)
    root = tmp_path / 'diagnostic'
    root.mkdir()
    model = tmp_path / 'model'
    model.mkdir()
    runner.write(model / 'config.json', dict(model_type='qwen2', max_position_embeddings=32768))
    runner.write(model / 'tokenizer.json', {})
    runner.write(model / 'tokenizer_config.json', {})
    runner.write(runner.continual.ROOT / 'PREPARE.json', dict(model_dir=str(model)))
    cpu_log = tmp_path / 'CPU_TESTS.log'
    cpu_log.write_text('35 passed in 0.1s')
    binding = runner.checkpoint_binding(seam)
    monkeypatch.setattr(runner, 'checkpoint_binding', lambda: binding)
    monkeypatch.setattr(runner.time, 'time', lambda: runner.TRAIN_CUTOFF + 10)
    monkeypatch.setattr(runner, 'host_identity', lambda: runner.continual.combined.HOST_SHA)
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES', '')
    tokenizer = SimpleNamespace(apply_chat_template=lambda *args, **kwargs: [7, 8])
    monkeypatch.setattr(runner.paired.native.source.native, 'load_local_tokenizer', lambda unused: tokenizer)
    def forbid_engine(*args, **kwargs):
        pytest.fail('CPU preparation must not load an engine')
    monkeypatch.setattr(runner.paired, 'Engine', forbid_engine)
    runner.prepare(root, cpu_log)
    runner.write(root / 'PUBLICATION.json', dict(ready_sha256=runner.sha(root / 'READY.json'),
        own_cpu_tests_passed=True, dated_builder_publication='[Builder] CPU checks',
        board_allocation='A100 physical0 after natural release'))
    return root


def test_seam_selects_full_and_verifies_matched_checkpoint(seam):
    binding = runner.checkpoint_binding(seam)
    assert binding['update'] == 8932
    assert binding['adapter']['state_sha256'] == 'a' * 64
    assert '/FULL/' in binding['adapter']['path']
    assert set(binding['commit_sha256']) == {'FULL', 'OFF'}


def test_seam_rejects_pre_cutoff_checkpoint(seam):
    document = runner.read(seam)
    document['time_unix'] = runner.TRAIN_CUTOFF - 1
    runner.write(seam, document)
    with pytest.raises(ValueError, match='post_cutoff'):
        runner.checkpoint_binding(seam)


def test_seam_rejects_unmatched_exposures(seam):
    document = runner.read(seam)
    commit = Path(document['checkpoint_paths']['OFF']) / 'COMMIT.json'
    metadata = runner.read(commit)
    metadata['metadata']['exposure_counts']['mock-row'] = 5
    runner.write(commit, metadata)
    with pytest.raises(ValueError, match='exposure_drift'):
        runner.checkpoint_binding(seam)


def test_prepare_reserves64_identical_prompts_and_never_loads_model(prepared):
    plan = runner.read(prepared / 'PLAN.json')
    ready = runner.read(prepared / 'READY.json')
    assert runner.validate(plan, runner.time.time()) is plan
    assert ready['native_calls'] == ready['parent_calls'] == ready['training_updates'] == 0
    assert len(ready['tokenization']) == 32 and ready['suite_sha256'] == runner.encoding.SUITE_SHA
    cells = runner.read(prepared / 'RESERVATIONS.json')['cells']
    assert len(cells) == 64
    for position, task in enumerate(runner.policy.tasks()):
        pair = cells[position * 2:position * 2 + 2]
        assert tuple(cell['condition'] for cell in pair) == runner.paired.ordered_conditions(position)
        assert all(cell['prompt_sha256'] == task['prompt_sha256'] and cell['max_new_tokens'] == 512 for cell in pair)
    assert plan['hard_deadline_unix'] - plan['lifetime_started_unix'] == 1800
    assert plan['gpu_hours_cap'] == 0.5 and plan['base_calls'] == 0


def test_prepared_uses_isolated_snapshot_and_keeps_hash_guard(prepared, tmp_path):
    plan = runner.read(prepared / 'PLAN.json')
    assert runner.SOURCE_ROOT == tmp_path / 'source_snapshot'
    assert runner.SOURCE_ROOT != Path(runner.__file__).resolve().parents[1]
    assert set(plan['sources']) == set(runner.REQUIRED_SOURCES)
    assert runner.validate(plan, runner.time.time()) is plan
    copied_source = runner.SOURCE_ROOT / runner.REQUIRED_SOURCES[0]
    copied_source.write_bytes(copied_source.read_bytes() + b'\n')
    with pytest.raises(AssertionError, match='source_binding_changed'):
        runner.validate(plan, runner.time.time())


@pytest.mark.parametrize('field,value', [
    ('experiment', 'other'), ('max_new_tokens', 1536), ('task_count', 31),
    ('call_cap', 65), ('base_calls', 32), ('gpu_hours_cap', 1),
    ('physical_index', 1), ('gpu_uuid', 'GPU-node3'), ('suite_sha256', 'changed'),
    ('training_updates', 1), ('parent_calls', 1), ('train_ingestion', True),
    ('conditions', ['LORA_OFF']), ('retained_calls', ['prior']), ('new_call_cap', 64),
    ('prior_root', '/prior'), ('lease_end_unix', 100),
])
def test_fixed_scope_rejects_changed_plan(prepared, field, value):
    plan = runner.read(prepared / 'PLAN.json')
    plan[field] = value
    with pytest.raises((ValueError, AssertionError)):
        runner.validate(plan, runner.time.time())


def test_lifetime_cannot_reset_or_extend(prepared):
    plan = runner.read(prepared / 'PLAN.json')
    with pytest.raises(AssertionError):
        runner.validate(plan, plan['native_deadline_unix'])
    plan['hard_deadline_unix'] += 1
    with pytest.raises(ValueError, match='global_30minute'):
        runner.validate(plan, runner.time.time())


def test_commit_drift_and_missing_runtime_source_rejected(prepared):
    plan = runner.read(prepared / 'PLAN.json')
    changed = deepcopy(plan)
    changed['sources'].pop('tests/test_orch_r107_continual_capability.py')
    with pytest.raises(ValueError, match='runtime_sources'):
        runner.validate(changed, runner.time.time())
    commit = Path(plan['checkpoint']['checkpoint_paths']['FULL']) / 'COMMIT.json'
    commit.write_text(commit.read_text() + '\n')
    with pytest.raises(ValueError, match='checkpoint_commit_changed'):
        runner.validate(plan, runner.time.time())


def valid_scan():
    return dict(created_utc=datetime.fromtimestamp(runner.time.time(), timezone.utc).isoformat(),
        scanner_euid=0, host_sha256=runner.continual.combined.HOST_SHA, clear=True,
        blocking_reasons=[], gpu=dict(index=0, uuid=runner.GPU_UUID), device_minor=3,
        device_path='/dev/nvidia3',
        minor_scanner_sha256=runner.sha(runner.continual.minor_scan.__file__),
        scanner_sha256=runner.sha(runner.continual.minor_scan.pinned.__file__))


@pytest.mark.parametrize('field,value', [
    ('scanner_euid', 1), ('clear', False), ('blocking_reasons', ['busy']),
    ('host_sha256', 'node3'), ('device_path', '/dev/nvidia0'),
    ('device_minor', -1), ('minor_scanner_sha256', 'other'),
    ('created_utc', '2000-01-01T00:00:00+00:00'),
    ('gpu', dict(index=0, uuid='GPU-node3')),
])
def test_scan_requires_a100_uuid_privilege_and_kernel_minor(field, value):
    report = valid_scan()
    runner.validate_scan(report, runner.time.time())
    report[field] = value
    with pytest.raises(ValueError):
        runner.validate_scan(report, runner.time.time())


def test_publication_required_and_reservation_immutable(prepared):
    plan = runner.read(prepared / 'PLAN.json')
    assert runner.validate_ready(prepared, plan)['status'] == 'PASS'
    publication = runner.read(prepared / 'PUBLICATION.json')
    publication['board_allocation'] = ''
    runner.write(prepared / 'PUBLICATION.json', publication)
    with pytest.raises(ValueError, match='publication_required'):
        runner.validate_ready(prepared, plan)


def test_launch_once_uses_bounded_timeout_and_only_a1000(prepared, monkeypatch):
    observed = []
    monkeypatch.setattr(runner.continual, 'scan', lambda index, service: valid_scan())
    def launch(command, **kwargs):
        observed.append((command, kwargs['env']))
        return SimpleNamespace(pid=123)
    monkeypatch.setattr(runner.subprocess, 'Popen', launch)
    monkeypatch.setattr(runner.continual.minor_scan.pinned, 'identity', lambda unused: dict(pid=123))
    result = runner.launch(prepared)
    assert result['timeout_identity']['pid'] == 123 and len(observed) == 1
    command, environment = observed[0]
    assert command[:3] == ['timeout', '--signal=TERM', '--kill-after=5s']
    assert command[3] == '1795s' and environment['CUDA_VISIBLE_DEVICES'] == runner.GPU_UUID
    assert environment['HF_HUB_OFFLINE'] == environment['TRANSFORMERS_OFFLINE'] == '1'
    with pytest.raises(FileExistsError):
        runner.launch(prepared)
    assert len(observed) == 1


def test_partial_reduction_preserves_failed_reservation_and_all64_cells(prepared):
    task = runner.policy.tasks()[0]
    call = dict(position=0, task_id=task['id'], messages=runner.policy.messages(task),
        condition='LORA_ON', status='FAILED', error_type='TimeoutError')
    runner.write(prepared / 'readout/CALL_000.json', call)
    result = runner.reduce(prepared)
    assert result['expected_cells'] == 64 and result['recorded_cells'] == 1
    assert not result['all_pairs_complete'] and not result['before_after_verified']
    assert result['overall']['pairs']['denominator'] == 32
    assert result['thinking_metrics'] is None and not result['raw_text_included']


@pytest.mark.parametrize('phase', ['prepare', 'launch', 'run'])
def test_pinned_host_hash_required_before_any_native_action(tmp_path, monkeypatch, phase):
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES', '')
    monkeypatch.setattr(runner, 'host_identity', lambda: '0' * 64)
    with pytest.raises(ValueError, match='exact_a100'):
        if phase == 'prepare':
            runner.prepare(tmp_path, tmp_path / 'unused.log')
        else:
            getattr(runner, phase)(tmp_path)


def test_pinned_hash_function_reused_without_direct_host_disclosure():
    assert runner.host_identity is runner.continual.minor_scan.pinned.host_identity
    assert len(runner.continual.combined.HOST_SHA) == 64
