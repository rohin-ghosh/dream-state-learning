"""Synthetic continuation gates; no model, sealed corpus or provider access."""

from copy import deepcopy
import builtins
import io
import json
import os
from pathlib import Path
from types import SimpleNamespace
import time

import pytest

from gpu import orch_r158_benchmark_continuation as continuation
from tests.test_orch_r146_checkpoint_scheduler import setup
from tests.test_orch_r130_checkpoint_copier import source


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True))
    return continuation.sha(path)


@pytest.fixture
def bundle(setup, monkeypatch):
    source = setup.source
    old_inventory = continuation.scheduler.sidecar.source_inventory(source)
    own = source / 'gpu/orch_r158_benchmark_continuation.py'
    own.write_bytes(Path(continuation.__file__).read_bytes())
    test = source / 'tests/test_orch_r158_benchmark_continuation.py'
    test.parent.mkdir()
    test.write_text('synthetic_test_source')
    monkeypatch.setattr(continuation, '__file__', str(own))
    monkeypatch.setattr(continuation, 'ROOT', setup.root)
    original = deepcopy(setup.config)
    old_output = setup.root / 'old_phase'
    template_path = old_output / 'SEGMENT_00.CONFIG.json'
    template_sha = dump(template_path, original)
    earlier_path = setup.root / 'earlier.json'
    earlier_sha = dump(earlier_path, dict(output_root=str(setup.root / 'earlier_output')))
    old_path = setup.root / 'old.json'
    old = dict(output_root=str(old_output), sources=old_inventory, hard_end_unix=time.time() - 20,
               predecessor_phase_path=str(earlier_path), predecessor_phase_sha256=earlier_sha)
    old_sha = dump(old_path, old)
    monkeypatch.setattr(continuation, 'PREVIOUS_SHA', old_sha)
    dump(old_output / 'COMPLETE.json', dict(status='BOUNDED_PHASE_FINISHED', phase_sha256=old_sha))
    dump(old_output / 'STARTED.json', dict(identity=dict(pid=123)))
    config = deepcopy(original)
    config.update(sources=continuation.scheduler.sidecar.source_inventory(source),
                  created_unix=time.time(), hard_end_unix=time.time() + 7100,
                  first_dispatch_unix=(int(time.time()) // 1800 + 1) * 1800,
                  output_root=str(setup.root / 'scheduler_run_r158_test'))
    gate = continuation.read(original['cpu_gate_path'])
    gate.update(helper_sha256=continuation.sha(own), test_sha256=continuation.sha(test),
                source_inventory_sha256=continuation.scheduler.digest(config['sources']))
    gate_path = setup.root / 'new_cpu_gate.json'
    config.update(cpu_gate_path=str(gate_path), cpu_gate_sha256=dump(gate_path, gate))
    config_path = setup.root / 'scheduler.json'
    config_sha = dump(config_path, config)
    builder = setup.root / 'BUILDER.md'
    builder.write_text('## [Builder] 2026-09-17 R158 synthetic gate\n')
    custody_path = setup.root / 'CUSTODY.json'
    entries = continuation.scheduler.enrolled_lineages(continuation.read(config['lineages_path']))
    custody = dict(sources={lineage:dict(lineage_id=lineage, read_end_unix=time.time() + 86400,
                    checkpoint_root='/synthetic/' + lineage + '/checkpoints',
                    initial_commit_sha256=entries[lineage]['initial_commit_sha256'])
                    for lineage in continuation.ORIGINALS})
    custody_sha = dump(custody_path, custody)
    phase = dict(schema=continuation.SCHEMA, helper_sha256=continuation.sha(own),
                 operator_root=str(setup.root), output_root=str(setup.root / 'successor_phase_r158_test'),
                 total_call_cap=4800, max_phase_jobs=58, predecessor_path=str(old_path), predecessor_sha256=old_sha,
                 template_path=str(template_path), template_sha256=template_sha,
                 scheduler_path=str(config_path), scheduler_sha256=config_sha,
                 builder_path=str(builder), builder_sha256=continuation.sha(builder),
                 custody_path=str(custody_path), custody_sha256=custody_sha,
                 hard_end_unix=config['hard_end_unix'], charged_configs={str(template_path):template_sha},
                 preserved={str(old_output / 'COMPLETE.json'):continuation.sha(old_output / 'COMPLETE.json')})
    phase_path = setup.root / 'phase.json'

    def bind():
        phase['scheduler_sha256'] = dump(config_path, config)
        monkeypatch.setenv('R158_ADMISSION_SHA256', dump(phase_path, phase))

    bind()
    return SimpleNamespace(phase=phase, path=phase_path, config=config, bind=bind, root=setup.root,
                           original=original, custody=custody, custody_path=custody_path, old_output=old_output,
                           setup=setup)


def test_real_scheduler_validation_and_residual_quota(bundle):
    phase, config, lineages, seeds, quota = continuation.validate(bundle.path)
    assert config == bundle.config
    assert len(lineages) == 3 and len(seeds) == 6
    assert quota['reserved_checkpoint_count'] == 6 and quota['remaining_jobs'] == 8
    continuation.predecessor_clear(phase)


@pytest.mark.parametrize('field,value', [('total_call_cap', 4860), ('max_phase_jobs', 59)])
def test_caps_cannot_be_raised(bundle, field, value):
    bundle.phase[field] = value
    bundle.bind()
    with pytest.raises(ValueError, match='unchanged_both_caps'):
        continuation.validate(bundle.path)


@pytest.mark.parametrize('field,value', [('physical_devices', [2, 3]), ('job_max_seconds', 300),
    ('dispatch_seconds', 60), ('lineages_path', '/different/lineages'), ('ledger_root', '/fresh/ledger'),
    ('corpus_sha256', 'f' * 64)])
def test_protocol_or_device_delta_rejected(bundle, field, value):
    bundle.config[field] = value
    bundle.bind()
    with pytest.raises(ValueError, match='wall_only_scheduler_delta'):
        continuation.validate(bundle.path)


def test_donor_dependencies_cannot_change():
    old = {'organism_v6/orch_r125_plain_context.py': 'a'}
    new = dict(old, **{name:'b' for name in continuation.OWN_FILES})
    continuation.snapshot_delta(old, new)
    new['organism_v6/orch_r125_plain_context.py'] = 'c'
    with pytest.raises(ValueError, match='append_only'):
        continuation.snapshot_delta(old, new)


def test_unscoped_source_addition_rejected():
    new = {name:'b' for name in continuation.OWN_FILES}
    new['gpu/unrelated.py'] = 'c'
    with pytest.raises(ValueError):
        continuation.snapshot_delta({}, new)


def test_omitted_history_config_rejected(bundle):
    bundle.phase['charged_configs'] = {}
    bundle.bind()
    with pytest.raises(ValueError, match='all_predecessor_configs_counted'):
        continuation.validate(bundle.path)


def test_historical_terminal_mutation_rejected(bundle):
    (bundle.old_output / 'COMPLETE.json').write_text('{}')
    with pytest.raises(ValueError, match='historical_artifact_preserved'):
        continuation.validate(bundle.path)


def test_live_old_controller_refuses_handoff(bundle, monkeypatch):
    monkeypatch.setattr(continuation.scheduler.sidecar, 'gone', lambda identity: False)
    with pytest.raises(ValueError, match='previous_controller_still_alive'):
        continuation.predecessor_clear(bundle.phase)


def test_old_failure_not_silently_restarted(bundle):
    dump(bundle.old_output / 'FAILED.json', dict(status='FAILED'))
    with pytest.raises(ValueError, match='R146_not_failed'):
        continuation.predecessor_clear(bundle.phase)


def test_expired_source_read_custody_rejected(bundle):
    bundle.custody['sources']['legacy']['read_end_unix'] = bundle.config['hard_end_unix']
    bundle.phase['custody_sha256'] = dump(bundle.custody_path, bundle.custody)
    bundle.bind()
    with pytest.raises(ValueError, match='source_read_ceiling'):
        continuation.validate(bundle.path)


def test_only_original_source_payloads_and_baselines(bundle):
    _, _, lineages, _, _ = continuation.validate(bundle.path)
    payload = dict(lineage_id='legacy', initial_commit_sha256=lineages['legacy']['initial_commit_sha256'],
                   commit_sha256='b' * 64, adapter_state_sha256='c' * 64)
    proof = continuation.source_payload(bundle.phase, lineages, payload)
    assert proof['checkpoint_root'] == '/synthetic/legacy/checkpoints'
    for changed in [dict(payload, lineage_id='new_child'), dict(payload, commit_sha256='../bad'),
                    dict(payload, initial_commit_sha256='a' * 64), dict(payload, prompt='not_allowed')]:
        with pytest.raises(ValueError):
            continuation.source_payload(bundle.phase, lineages, changed)


def test_environment_restored_on_failure(monkeypatch):
    monkeypatch.setenv('R130_SCHEDULER_ADMISSION_SHA256', 'old')
    with pytest.raises(RuntimeError):
        with continuation.scheduler_environment('new'):
            assert os.environ['R130_SCHEDULER_ADMISSION_SHA256'] == 'new'
            raise RuntimeError('synthetic')
    assert os.environ['R130_SCHEDULER_ADMISSION_SHA256'] == 'old'


def test_shared_budget_exhaustion_and_failed_charge(bundle, monkeypatch):
    scheduler = continuation.scheduler
    monkeypatch.setattr(scheduler, 'ledger_state', lambda *args: (set(range(80)), set(range(77)), {}))
    bundle.config['max_jobs'] = 1
    with pytest.raises(ValueError, match='own_admissions_plus_residual_cap'):
        continuation.quota(bundle.phase, bundle.config, set(), {})


def test_unknown_controller_reservation_is_not_free_budget(bundle):
    claim = dict(lineage_id='legacy', commit_sha256='b' * 64, config_path='/unknown/config', config_sha256='c' * 64)
    key = continuation.scheduler.key_for('legacy', 'b' * 64)
    dump(Path(bundle.config['ledger_root']) / (key + '.RESERVED.json'), claim)
    with pytest.raises(ValueError, match='unknown_reservation_config_refused'):
        continuation.quota(bundle.phase, bundle.config, set(), {})


def test_status_reads_only_metadata_terminal(bundle):
    output = Path(bundle.phase['output_root'])
    terminal = dict(status='BOUNDED_PHASE_FINISHED', phase_sha256=continuation.sha(bundle.path),
                    completed_checkpoint_count=62)
    dump(output / 'COMPLETE.json', terminal)
    assert continuation.status(bundle.phase) == terminal


def test_failed_key_never_requests_an_archive(bundle, monkeypatch):
    phase, config, lineages, seeds, quota = continuation.validate(bundle.path)
    payload = dict(lineage_id='legacy', initial_commit_sha256=lineages['legacy']['initial_commit_sha256'],
                   commit_sha256='b' * 64, adapter_state_sha256='c' * 64)
    monkeypatch.setattr(continuation, 'validate', lambda path:(phase, config, lineages, seeds, quota))
    monkeypatch.setattr(continuation, 'status', lambda phase:dict(status='SEGMENT_RUNNING',
        active_config_sha256=phase['scheduler_sha256']))
    dump(Path(config['output_root']) / 'STARTED.json', dict(identity=dict(pid=123)))
    key = continuation.scheduler.key_for('legacy', 'b' * 64)
    monkeypatch.setattr(continuation.scheduler, 'ledger_state', lambda *args:({key}, set(), {}))
    monkeypatch.setattr(continuation.scheduler.sidecar, 'gone', lambda identity:False)
    assert continuation.stage(bundle.path, 'stage', payload)['status'] == 'ALREADY_RESERVED_NO_REPLAY'


@pytest.fixture
def staged(bundle, source, monkeypatch):
    phase, config, lineages, seeds, quota = continuation.validate(bundle.path)
    lineages['kernel']['initial_commit_sha256'] = source.params['initial_commit_sha256']
    proof = bundle.custody['sources']['kernel']
    proof.update(checkpoint_root=str(source.root), initial_commit_sha256=source.params['initial_commit_sha256'])
    phase['custody_sha256'] = dump(bundle.custody_path, bundle.custody)
    monkeypatch.setattr(continuation, 'validate', lambda path:(phase, config, lineages, seeds, quota))
    monkeypatch.setattr(continuation, 'status', lambda phase:dict(status='SEGMENT_RUNNING',
        active_config_sha256=phase['scheduler_sha256']))
    monkeypatch.setattr(continuation.scheduler.sidecar, 'gone', lambda identity:False)
    dump(Path(config['output_root']) / 'STARTED.json', dict(identity=dict(pid=123)))
    (bundle.root / 'incoming').mkdir()
    selected = continuation.copier_backend().discover(source.params)['selected']
    raw = continuation.copier_backend().pack(source.params, selected)
    payload = dict(lineage_id='kernel', initial_commit_sha256=source.params['initial_commit_sha256'],
                   commit_sha256=selected['commit_sha256'], adapter_state_sha256=selected['adapter_state_sha256'],
                   archive_sha256=continuation.hashlib.sha256(raw).hexdigest())
    monkeypatch.setattr(continuation.sys, 'stdin', SimpleNamespace(buffer=io.BytesIO(raw)))
    return SimpleNamespace(bundle=bundle, payload=payload, raw=raw, phase=phase, config=config)


def test_real_source_pack_stage_and_content_addressed_ready(staged):
    receipt = continuation.stage(staged.bundle.path, 'stage', staged.payload)
    assert receipt['status'] == 'COPIED_AND_READY_VERIFIED'
    known = {key:value for key, value in staged.payload.items() if key != 'archive_sha256'}
    assert continuation.stage(staged.bundle.path, 'known', known)['status'] == 'ALREADY_STAGED'
    destination = Path(staged.config['inbox_root']) / 'copies' / ('kernel_' + staged.payload['commit_sha256'])
    assert {path.name for path in destination.iterdir()} == {'COMMIT.json', 'adapter', 'manifest.json', 'SOURCE_COPY_RECEIPT.json'}


def test_wrong_original_root_archive_never_publishes_ready(staged):
    custody = staged.bundle.custody
    custody['sources']['kernel']['checkpoint_root'] = '/unregistered/recovery/checkpoints'
    staged.phase['custody_sha256'] = dump(staged.bundle.custody_path, custody)
    with pytest.raises(ValueError, match='readonly_original_source_proof'):
        continuation.stage(staged.bundle.path, 'stage', staged.payload)
    assert not list((Path(staged.config['inbox_root']) / 'ready').glob('*.json'))


def test_bad_archive_hash_never_publishes(staged):
    staged.payload['archive_sha256'] = 'a' * 64
    with pytest.raises(ValueError, match='archive_hash'):
        continuation.stage(staged.bundle.path, 'stage', staged.payload)


def test_failed_reservation_remains_charged(bundle):
    scheduler = continuation.scheduler
    _, config, lineages, seeds, _ = continuation.validate(bundle.path)
    key = scheduler.key_for('kernel', 'c' * 64)
    claim = dict(lineage_id='kernel', commit_sha256='c' * 64, corpus_sha256=config['corpus_sha256'],
                 config_path=bundle.phase['template_path'], config_sha256=bundle.phase['template_sha256'])
    dump(Path(config['ledger_root']) / (key + '.RESERVED.json'), claim)
    quota = continuation.quota(bundle.phase, config, seeds, lineages)
    assert quota['phase_charged'] == 1 and quota['reserved_checkpoint_count'] == 7
    assert quota['completed_checkpoint_count'] == 6 and quota['remaining_total_call_budget'] == 4380


def test_missing_local_dependency_closure_rejected(tmp_path, monkeypatch):
    config = dict(schema=continuation.COPY_SCHEMA, helper_sha256=continuation.sha(continuation.__file__),
                  local_dependencies={})
    path = tmp_path / 'copy.json'
    monkeypatch.setenv('R158_COPY_ADMISSION_SHA256', dump(path, config))
    with pytest.raises(ValueError, match='complete_local_copy_closure'):
        continuation.copy_validate(path)


def test_copy_phase_commands_bound_to_node2_and_CPU(tmp_path, monkeypatch):
    observed = []
    def run(command, **kwargs):
        observed.append((command, kwargs))
        return SimpleNamespace(stdout=b'{"status":"NEEDS_COPY"}')
    monkeypatch.setattr(continuation.subprocess, 'run', run)
    config = dict(destination_wrapper='gpu/ovx_ssh.sh', remote_source_root='/bound/source_r158',
        remote_phase_sha256='a' * 64, remote_python='/bound/python', remote_phase_path='/bound/phase.json')
    assert continuation.remote(config, dict(hard_end_unix=time.time()+600), 'known', {'synthetic':True})['status'] == 'NEEDS_COPY'
    command, kwargs = observed[0]
    assert command[:2] == ['bash', 'gpu/ovx_ssh.sh']
    assert 'CUDA_VISIBLE_DEVICES=' in command[2] and 'R158_ADMISSION_SHA256=' in command[2]
    assert 'gpu.orch_r158_benchmark_continuation' in command[2] and kwargs['check'] is True


def test_node_import_does_not_require_local_only_copier(monkeypatch):
    original_import = builtins.__import__
    def guarded(name, globals=None, locals=None, fromlist=(), level=0):
        if 'orch_r130_checkpoint_copier' in name or 'orch_r130_checkpoint_copier' in (fromlist or ()):
            raise ImportError('local_copier_not_deployed_on_node2')
        return original_import(name, globals, locals, fromlist, level)
    source = Path(continuation.__file__).read_text()
    monkeypatch.setattr(builtins, '__import__', guarded)
    namespace = dict(__name__='synthetic_node_import', __file__=continuation.__file__)
    exec(compile(source, continuation.__file__, 'exec'), namespace)
    assert callable(namespace['validate']) and callable(namespace['stage'])
