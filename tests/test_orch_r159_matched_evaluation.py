"""CPU-only synthetic fixtures; never import sealed items or outputs."""

from contextlib import contextmanager
from copy import deepcopy
import json
import os
from pathlib import Path
from types import SimpleNamespace
import time

import pytest

from gpu import orch_r159_matched_evaluation as subject


def store(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value) + '\n')
    return subject.ref(path)


def update_reference(reference, **changes):
    value = subject.bound(reference)
    value.update(changes)
    return store(Path(reference['path']), value)


def attest_timestamps(fixture, **changes):
    config, candidate = fixture.config, fixture.candidate
    initial = subject.bound(candidate['initial_commit'])
    initialized = subject.bound(candidate['initialized'])
    owner = subject.bound(config['source_owner_authority'])
    observed = time.time()-0.01
    exposures = {}
    for arm in subject.ARMS:
        exposures[arm] = {}
        for kind in ('birth', 'train', 'evaluation'):
            event = dict(schema='R159_FIRST_EXPOSURE_V1', cohort_sha256=candidate['cohort']['sha256'],
                arm=arm, kind=kind, coverage_complete=True, observed_unix=observed,
                status='OBSERVED' if kind == 'birth' else 'NOT_OCCURRED',
                first_unix=observed-1 if kind == 'birth' else None)
            exposures[arm][kind] = store(fixture.root / 'inputs' / f'{arm}_{kind}_TIMESTAMP.json', event)
    timing = dict(schema=subject.TIMESTAMP_SCHEMA, status='TRUSTED_SOURCE_OWNER_ATTESTED',
        campaign_sha256=config['campaign']['sha256'], freeze=fixture.plan['freeze'],
        cohort_sha256=candidate['cohort']['sha256'], initial_commit_sha256=candidate['initial_commit']['sha256'],
        initialized_sha256=candidate['initialized']['sha256'],
        initializer_lifecycle_sha256=owner['initializer_lifecycle']['sha256'],
        initial_created_unix=initial['created_unix'], initialized_unix=initialized['initialized_unix'],
        enrollment_unix=observed-0.1, observed_unix=observed, saved_initial_generation_calls=0,
        saved_initial_optimizer_updates=0, saved_initial_training_exposure=False,
        saved_initial_evaluation_exposure=False, arm_exposures=exposures)
    timing.update(changes)
    reference = store(fixture.root / 'inputs/TIMESTAMP_CUSTODY.json', timing)
    config['source_owner_authority'] = update_reference(config['source_owner_authority'], timestamp_custody=reference)
    candidate['source_custody'] = update_reference(candidate['source_custody'],
        source_owner_authority=config['source_owner_authority'], timestamp_custody=reference)
    config['candidate'] = store(Path(config['candidate']['path']), candidate)
    return reference


@pytest.fixture
def fixture(tmp_path, monkeypatch):
    root = tmp_path / 'campaign'
    old = tmp_path / 'old_campaign'
    monkeypatch.setattr(subject, 'CAMPAIGN_ROOT', root)
    monkeypatch.setattr(subject, 'OLD_ROOT', old)
    freeze = store(tmp_path / 'freeze.json', dict(schema=subject.SCHEMA, status='TASKSET_FROZEN_NO_ENROLLMENT',
                  frozen_unix=time.time()-120, counts=subject.COUNTS))
    monkeypatch.setattr(subject, 'ORIGINAL_FREEZE_SHA256', freeze['sha256'])
    plan = subject.plan_document(freeze)
    plan_ref = store(tmp_path / 'plan.json', plan)
    monkeypatch.setattr(subject, 'ORIGINAL_PLAN_SHA256', plan_ref['sha256'])
    model_dir = tmp_path / 'model'
    model_dir.mkdir()
    python = tmp_path / 'python'
    python.write_text('synthetic interpreter')
    python.chmod(0o700)
    service = tmp_path / 'service'
    service.write_text('synthetic scan binding')
    cohort_root = tmp_path / 'source_node4'
    roots = {arm: str(cohort_root / arm) for arm in subject.ARMS}
    cohort = dict(schema='R150_MATCHED_CONTINUAL_COHORT_V1',
                  members={arm: dict(root=roots[arm], parent_enabled=arm != 'unparented_learning')
                           for arm in subject.ARMS},
                  common=dict(base_sha256=subject.native.BASE_SHA256, source_root=str(cohort_root / 'source')),
                  fresh_histories=True, evaluations_gate_continuation=False, initial_optimizer_steps=0,
                  initial_directory=str(cohort_root / 'common_initial'))
    cohort_ref = store(root / 'inputs/cohort.json', cohort)
    adapter = root / 'inputs/checkpoint/adapter'
    adapter.mkdir(parents=True)
    store(adapter / 'adapter_config.json', dict(r=8, lora_alpha=16, peft_type='LORA',
          target_modules=['q_proj', 'k_proj', 'v_proj', 'o_proj', 'gate_proj', 'up_proj', 'down_proj']))
    (adapter / 'adapter_model.safetensors').write_bytes(b'synthetic adapter only')
    files = {path.name: subject.sha(path) for path in adapter.iterdir()}
    initial = dict(schema=subject.native.NATIVE_SCHEMA, base_sha256=subject.native.BASE_SHA256,
                   optimizer_steps=0, created_unix=time.time()-100, adapter_files=files,
                   adapter_path=str(cohort_root / 'common_initial/adapter'), adapter_state_sha256='a'*64,
                   checkpoint_sha256=dict(adapter=subject.digest(files), optimizer='b'*64, rng='b'*64),
                   experiment=dict(synthetic='same initialization fixture'))
    initial_ref = store(root / 'inputs/initial.json', initial)
    capacity = store(root / 'inputs/capacity.json', dict(schema='R151_MATCHED_INITIAL_CAPACITY_V1', status='PASS',
        state_restored=True, restoration_status='VERIFIED', generation_calls=0, optimizer_updates=0,
        stream_data_written=False, scientific_evaluation=False))
    initialized_ref = store(root / 'inputs/initialized.json', dict(schema=cohort['schema'],
        cohort_sha256=cohort_ref['sha256'], checkpoint_commit_sha256=initial_ref['sha256'],
        generation_calls=0, optimizer_updates=0, initialization_validation=dict(status='PASS',
            schema='R151_MATCHED_INITIAL_CAPACITY_V1', **capacity),
        initialized_unix=time.time()-99))
    arm = 'parented_learning'
    source = Path(roots[arm]) / 'checkpoints/initial'
    commit = dict(initial, adapter_path=str(source / 'adapter'), optimizer_rng_path=str(source / 'optimizer_rng.pt'))
    commit_ref = store(root / 'inputs/checkpoint/COMMIT.json', commit)
    manifest_ref = store(root / 'inputs/checkpoint/MANIFEST.json', dict(schema=subject.native.MANIFEST_SCHEMA,
        adapter_path=str(adapter), commit_path=commit_ref['path'], commit_sha256=commit_ref['sha256']))
    lifecycle = store(root / 'inputs/lifecycle.json', dict(service_returncode=0))
    owner = store(root / 'inputs/source_owner.json', dict(schema=subject.SCHEMA, status='SOURCE_OWNER_ADMITTED',
        cohort_sha256=cohort_ref['sha256'], source_roots=roots, read_end_unix=time.time()+8000,
        source_root=cohort['common']['source_root'], initializer_lifecycle=lifecycle))
    read_end = subject.bound(owner)['read_end_unix']
    custody_ref = store(root / 'inputs/custody.json', dict(schema=subject.SCHEMA,
        cohort_sha256=cohort_ref['sha256'], source_root=roots[arm], source_commit_path=str(source / 'COMMIT.json'),
        commit_sha256=commit_ref['sha256'], manifest_sha256=manifest_ref['sha256'], checkpoint_boundary=0,
        source_owner_authority=owner, source_read_end_unix=read_end, adapter_only=True,
        optimizer_rng_read=False, history_read=False, source_written=False))
    candidate = dict(schema=subject.SCHEMA, arm=arm, milestone=0, cohort=cohort_ref, initialized=initialized_ref, capacity=capacity,
        initial_commit=initial_ref, source_commit_path=str(source / 'COMMIT.json'), manifest=manifest_ref,
        source_custody=custody_ref)
    candidate_ref = store(root / 'inputs/candidate.json', candidate)
    cpu = store(root / 'control/CPU.json', dict(status='PASS', helper_sha256=subject.sha(subject.__file__),
                                             test_sha256='c'*64))
    builder = store(root / 'control/BUILDER.json', dict(status='CPU_AND_PROVENANCE_PASS', campaign=plan_ref,
                    cpu_gate=cpu, created_unix=time.time()-1))
    end = time.time()+7200
    authority = store(root / 'control/NODE2.json', dict(schema=subject.SCHEMA, node='node2',
        campaign_sha256=plan_ref['sha256'], lease_end_unix=end+21600, hard_end_unix=end, physical_slots=[0, 1]))
    from gpu import orch_r130_benchmark_sidecar as sidecar
    monkeypatch.setattr(subject.socket, 'gethostname', lambda: 'synthetic-node2')
    monkeypatch.setattr(sidecar, 'HOST_SHA256', subject.hashlib.sha256(b'synthetic-node2').hexdigest())
    monkeypatch.setattr(sidecar, 'identity', lambda pid: None)
    config = dict(schema=subject.SCHEMA, campaign=plan_ref, campaign_root=str(root), candidate=candidate_ref,
        physical=0, gpu_uuid=sidecar.DEVICES[0], source_root=str(tmp_path / 'source'),
        sources={'tests/test_orch_r159_matched_evaluation.py': 'c'*64}, model_dir=str(model_dir),
        python=str(python), python_sha256=subject.sha(python), hard_end_unix=end,
        lease_end_unix=end+21600, source_owner_authority=owner,
        source_read_end_unix=read_end, old_terminal=store(old / 'COMPLETE.json', dict(status='BOUNDED_PHASE_FINISHED')),
        old_terminal_identity=dict(pid=42, start_ticks='123', boot_id='fixture', uid=1), cpu_gate=cpu,
        builder=builder, node2_authority=authority, service_path=str(service))
    config_path = root / 'control/EXECUTION.json'
    store(config_path, config)
    go_path = root / 'control/MAIN_GO.json'
    store(go_path, dict(schema=subject.SCHEMA, status='MAIN_GO', execution=subject.ref(config_path)))
    monkeypatch.setenv('R159_MAIN_GO_SHA256', subject.sha(go_path))
    monkeypatch.setattr(subject, 'validate_sources', lambda config: None)
    result = SimpleNamespace(root=root, plan=plan, plan_ref=plan_ref, candidate=candidate, config=config,
                             config_path=config_path, go_path=go_path, adapter=adapter, commit=commit_ref)
    attest_timestamps(result)
    rebind(result, monkeypatch)
    return result


def rebind(fixture, monkeypatch):
    store(fixture.config_path, fixture.config)
    store(fixture.go_path, dict(schema=subject.SCHEMA, status='MAIN_GO', execution=subject.ref(fixture.config_path)))
    monkeypatch.setenv('R159_MAIN_GO_SHA256', subject.sha(fixture.go_path))


def test_plan_has_all_controls_and_bounded_calls(fixture):
    assert fixture.plan['slots'] == subject.slots()
    assert len(fixture.plan['slots']) == 12
    assert fixture.plan['calls_per_checkpoint'] * fixture.plan['max_checkpoints'] == 672 <= 720
    assert {slot['milestone'] for slot in fixture.plan['slots']} == {0, 1, 2, 4}
    assert all(slot['weight_control'] == 'step0_repeated' for slot in fixture.plan['slots']
               if slot['arm'] == 'parented_frozen')
    assert subject.validate_plan(fixture.plan_ref) == fixture.plan


@pytest.mark.parametrize('change', [dict(total_call_cap=720), dict(max_checkpoints=13),
    dict(scores_gate_selection=True), dict(evaluation_to_sleep=True), dict(evaluation_to_inbox=True),
    dict(history_shared=True), dict(parent_access=True), dict(file_tools=True), dict(cohort='old_root'),
    dict(failed_keys_retry=True), dict(rank=16), dict(slots=subject.slots()[:-1]),
    dict(conditions=['LORA_ON']), dict(extra_prompt='leak')])
def test_immutable_plan_rejects_changes(fixture, change):
    reference = update_reference(fixture.plan_ref, **change)
    with pytest.raises(ValueError, match='original_12_slot_672_call_plan_bytes'):
        subject.validate_plan(reference)


def test_valid_R150_adapter_only_custody(fixture, monkeypatch):
    original = Path.read_bytes
    def safe_read(path):
        assert 'optimizer_rng.pt' not in str(path) and '/readouts/' not in str(path)
        return original(path)
    monkeypatch.setattr(Path, 'read_bytes', safe_read)
    candidate, checkpoint = subject.candidate_check(fixture.config, fixture.plan)
    assert candidate['arm'] == 'parented_learning'
    assert checkpoint['adapter_path'] == str(fixture.adapter)


@pytest.mark.parametrize('changes', [dict(arm='legacy'), dict(milestone=3), dict(milestone=True),
    dict(source_commit_path='/retired/root/checkpoints/initial/COMMIT.json'),
    dict(milestone=1), dict(arm='unparented_learning')])
def test_wrong_source_or_checkpoint(fixture, changes):
    fixture.config['candidate'] = update_reference(fixture.config['candidate'], **changes)
    with pytest.raises(ValueError):
        subject.candidate_check(fixture.config, fixture.plan)


@pytest.mark.parametrize('change', [dict(adapter_state_sha256='d'*64), dict(optimizer_steps=1),
                                  dict(experiment={'different': True})])
def test_wrong_initial_state_refused(fixture, change):
    changed = update_reference(fixture.commit, **change)
    fixture.candidate['manifest'] = update_reference(fixture.candidate['manifest'], commit_sha256=changed['sha256'])
    fixture.config['candidate'] = store(Path(fixture.config['candidate']['path']), fixture.candidate)
    with pytest.raises(ValueError):
        subject.candidate_check(fixture.config, fixture.plan)


def test_wrong_adapter_files_and_symlinks(fixture):
    (fixture.adapter / 'unexpected.txt').write_text('not a native file')
    with pytest.raises(ValueError, match='native_adapter_file_binding'):
        subject.candidate_check(fixture.config, fixture.plan)


def test_refrozen_timestamp_not_accepted(fixture):
    fixture.plan['freeze'] = update_reference(fixture.plan['freeze'], frozen_unix=time.time())
    with pytest.raises(ValueError, match='original_task_freeze_no_refreezing'):
        subject.candidate_check(fixture.config, fixture.plan)


def test_owner_expiry_and_initializer_exit(fixture):
    fixture.config['source_read_end_unix'] = time.time()-1
    with pytest.raises(ValueError):
        subject.candidate_check(fixture.config, fixture.plan)


def test_actual_execution_gate(fixture):
    config, plan, candidate, _ = subject.validate_execution(fixture.config_path, fixture.go_path)
    assert config == fixture.config and plan == fixture.plan and candidate == fixture.candidate


def test_no_Main_GO(fixture, monkeypatch):
    monkeypatch.delenv('R159_MAIN_GO_SHA256')
    with pytest.raises(ValueError, match='explicit_Main_GO'):
        subject.validate_execution(fixture.config_path, fixture.go_path)


@pytest.mark.parametrize('changes', [dict(physical=2), dict(gpu_uuid='GPU-other'),
    dict(parent_inbox='/parent/INBOX'), dict(readout_path='/child/readouts'),
    dict(campaign_root=str(subject.OLD_ROOT)), dict(hard_end_unix=float('inf')),
    dict(source_root='/different/source')])
def test_wrong_execution_scope(fixture, monkeypatch, changes):
    fixture.config.update(changes)
    rebind(fixture, monkeypatch)
    if 'source_root' in changes:
        monkeypatch.setattr(subject, 'validate_sources', lambda config: subject.require(False, 'wrong_source'))
    with pytest.raises(ValueError):
        subject.validate_execution(fixture.config_path, fixture.go_path)


def test_old_controller_identity_must_be_gone(fixture, monkeypatch):
    from gpu import orch_r130_benchmark_sidecar as sidecar
    monkeypatch.setattr(sidecar, 'identity', lambda pid: fixture.config['old_terminal_identity'])
    with pytest.raises(ValueError, match='old_controller_must_be_gone'):
        subject.validate_execution(fixture.config_path, fixture.go_path)


def test_failed_key_stays_charged_no_retry(fixture):
    key, claim = subject.reserve(fixture.config_path, fixture.config, fixture.candidate)
    subject.write(fixture.root / 'ledger' / (key+'.FAILED.json'),
                  dict(status='FAILED_NO_RETRY', reservation_sha256=subject.sha(claim)))
    status = subject.ledger_status(fixture.root, fixture.plan_ref['sha256'])
    assert status['calls_charged'] == 56 and status['failed'] == 1 and not status['control_complete']
    with pytest.raises(ValueError, match='never_replayed'):
        subject.reserve(fixture.config_path, fixture.config, fixture.candidate)


def test_twelve_slots_preserve_cap_and_completeness(fixture):
    for slot in subject.slots():
        candidate = dict(fixture.candidate, arm=slot['arm'], milestone=slot['milestone'])
        key, claim = subject.reserve(fixture.config_path, fixture.config, candidate)
        subject.write(fixture.root / 'ledger' / (key+'.COMPLETE.json'),
                      dict(status='COMPLETE', reservation_sha256=subject.sha(claim)))
    status = subject.ledger_status(fixture.root, fixture.plan_ref['sha256'])
    assert status['calls_charged'] == 672 and status['calls_remaining'] == 0
    assert status['control_complete'] and status['completed'] == 12
    with pytest.raises(ValueError, match='new_budget_remaining'):
        subject.reserve(fixture.config_path, fixture.config, fixture.candidate)


def test_mixed_cohort_reservation_refused(fixture):
    subject.reserve(fixture.config_path, fixture.config, fixture.candidate)
    candidate = deepcopy(fixture.candidate)
    candidate['arm'] = 'unparented_learning'
    candidate['cohort']['sha256'] = 'e'*64
    with pytest.raises(ValueError, match='no_mixed_actual_cohorts'):
        subject.reserve(fixture.config_path, fixture.config, candidate)


def test_clean_environment_no_parent_credentials(fixture, monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY', 'synthetic-secret')
    monkeypatch.setenv('PARENT_INBOX', '/synthetic/inbox')
    environment = subject.clean_environment(fixture.config, fixture.config_path, fixture.go_path)
    assert 'OPENAI_API_KEY' not in environment and 'PARENT_INBOX' not in environment
    assert environment['HF_HUB_OFFLINE'] == environment['TRANSFORMERS_OFFLINE'] == '1'


@pytest.mark.parametrize('raw,expected', [('ACT: fixture', 'fixture'), ('ACT: a ; b', 'a ; b'),
    ('ACT: a\nACT: b', None), ('unmarked', None), ('ACT: ', None)])
def test_fixed_action_parser(raw, expected):
    assert subject.parse_action(raw) == expected


def test_stable_task_prompt_scoring_hashes():
    tasks = [dict(messages=[dict(role='user', content='synthetic')], entry=dict(answer='fixture'))]
    scoring = dict(algorithm='fixture-only')
    baseline = subject.task_hashes(tasks, scoring)
    assert baseline == subject.task_hashes(deepcopy(tasks), deepcopy(scoring))
    changed = deepcopy(tasks)
    changed[0]['entry']['answer'] = 'other'
    assert subject.task_hashes(changed, scoring)['task_sha256'] != baseline['task_sha256']
    assert subject.task_hashes(changed, scoring)['prompt_sha256'] == baseline['prompt_sha256']
    assert subject.task_hashes(tasks, dict(algorithm='changed'))['scoring_sha256'] != baseline['scoring_sha256']


def synthetic_ledger():
    ledger = dict(train_families=['fixture_train'], gate_families=['fixture_gate'], exam_families=['fixture_exam'],
                  seed_ranges=dict(canary=[1900000, 1900100], gate=[2000000, 2100000], exam=[3000000, 3100000]))
    for split, family, seed in [('canary', 'fixture_train', 1900000), ('gate', 'fixture_gate', 2000000),
                                ('exam', 'fixture_exam', 3000000)]:
        ledger[split+'_set'] = [f'rg/{family}/{seed+index}' for index in range(subject.COUNTS[split])]
    return ledger


def test_ledger_only_canary_not_TRAIN_1500000():
    ledger = synthetic_ledger()
    assert len(subject.ledger_ids(ledger)) == 28
    ledger['canary_set'][0] = 'rg/fixture_train/1500000'
    with pytest.raises(ValueError, match='never_R158TRAIN'):
        subject.ledger_ids(ledger)


def test_gate_exam_no_family_leak():
    ledger = synthetic_ledger()
    ledger['gate_families'] = ledger['train_families']
    with pytest.raises(ValueError, match='disjoint_family_groups'):
        subject.ledger_ids(ledger)


class FakeModel:
    training = False
    def __init__(self):
        self.parameter = SimpleNamespace(requires_grad=False)
        self.disable_adapters = False
        self.lora_A = self.lora_B = {}

    def parameters(self):
        return [self.parameter]

    def modules(self):
        return [self]

    def requires_grad_(self, value):
        self.parameter.requires_grad = value

    @contextmanager
    def disable_adapter(self):
        self.disable_adapters = True
        try:
            yield
        finally:
            self.disable_adapters = False


class FakeEngine:
    def __init__(self):
        self.model = FakeModel()
        self.calls = []
        self.fail_at = None
        self.tokenizer = SimpleNamespace(eos_token_id=9, apply_chat_template=lambda *args, **kwargs: [1, 2])

    def generate(self, messages, max_new_tokens):
        assert max_new_tokens == 512 and len(messages) == 1
        self.calls.append(deepcopy(messages))
        if len(self.calls) == self.fail_at:
            raise RuntimeError('synthetic-sealed-error-content')
        return dict(raw='ACT: fixture', messages=deepcopy(messages), prompt_tokens=2,
                    token_ids=[3, 9], terminal=True, truncated=False)


def prepare_engine(fixture, monkeypatch):
    subject.reserve(fixture.config_path, fixture.config, fixture.candidate)
    monkeypatch.setenv('R159_EXECUTION_SHA256', subject.sha(fixture.config_path))
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES', fixture.config['gpu_uuid'])
    monkeypatch.setattr(subject, 'USED', False)
    engine = FakeEngine()
    monkeypatch.setattr(subject.native, '_load_engine', lambda *args: engine)
    monkeypatch.setattr(subject.native, '_snapshot', lambda *args: dict(adapter_state_sha256='a'*64))
    tasks = [dict(messages=[dict(role='user', content=f'fixture-{index}')]) for index in range(28)]
    monkeypatch.setattr(subject, 'sealed_tasks', lambda plan: deepcopy(tasks))
    monkeypatch.setattr(subject, 'score_task', lambda task, response: dict(eligible=True, score=0.5))
    return engine


def test_actual_evaluator_fresh_items_56_calls_and_no_reuse(fixture, monkeypatch):
    engine = prepare_engine(fixture, monkeypatch)
    result = subject.evaluate(fixture.config_path, fixture.go_path)
    assert result == dict(status='COMPLETE', calls=56)
    assert len(engine.calls) == 56
    assert all(engine.calls[2*index] == engine.calls[2*index+1] for index in range(28))
    output = fixture.root / 'attempts/parented_learning_0/sealed'
    assert subject.completion_metadata(output / 'COMPLETE.json', subject.sha(fixture.config_path))['calls'] == 56
    (output / 'CALL_0000.RAW.private.json').chmod(0o600)
    (output / 'CALL_0000.RAW.private.json').write_text('synthetic tamper')
    with pytest.raises(ValueError, match='sealed_receipt_hash_custody'):
        subject.completion_metadata(output / 'COMPLETE.json', subject.sha(fixture.config_path))
    with pytest.raises(ValueError, match='one_checkpoint_per_fresh_process'):
        subject.evaluate(fixture.config_path, fixture.go_path)


def test_generation_failure_preserved_no_completion(fixture, monkeypatch):
    engine = prepare_engine(fixture, monkeypatch)
    engine.fail_at = 2
    with pytest.raises(RuntimeError):
        subject.evaluate(fixture.config_path, fixture.go_path)
    output = fixture.root / 'attempts/parented_learning_0/sealed'
    assert subject.read(output / 'FAILED.json')['calls'] == 2
    assert not (output / 'COMPLETE.json').exists()
    assert 'synthetic-sealed-error-content' not in (output / 'FAILED.json').read_text()


def test_cli_sanitizes_exception(fixture, monkeypatch, capsys):
    def secret_error(*args):
        raise RuntimeError('synthetic-sealed-error-content')
    monkeypatch.setattr(subject, 'validate_execution', secret_error)
    assert subject.main(['validate', '--config', str(fixture.config_path), '--go', str(fixture.go_path)]) == 1
    output = capsys.readouterr()
    assert 'synthetic-sealed-error-content' not in output.out + output.err
    assert json.loads(output.out)['status'] == 'REFUSED_OR_FAILED'


def test_busy_device_no_admission_no_child_signals(fixture, monkeypatch):
    from gpu import orch_r130_benchmark_sidecar as sidecar
    monkeypatch.setattr(sidecar, 'scan', lambda config: dict(clear=False, blocking_reasons=['occupied']))
    assert subject.dispatch(fixture.config_path, fixture.go_path)['status'] == 'DEVICE_BUSY_NO_SIGNALS_NO_RESERVATION'
    assert not (fixture.root / 'ledger').exists()


def test_no_short_wall_launch(fixture, monkeypatch):
    fixture.config['hard_end_unix'] = time.time()+100
    monkeypatch.setattr(subject, 'validate_execution', lambda *args: (fixture.config, fixture.plan, fixture.candidate, {}))
    with pytest.raises(ValueError, match='full_existing_3600s_job_window'):
        subject.dispatch(fixture.config_path, fixture.go_path)
    assert not (fixture.root / 'ledger').exists()


def test_regular_path_rejects_symlink(tmp_path):
    original = tmp_path / 'file'
    original.write_text('fixture')
    link = tmp_path / 'link'
    link.symlink_to(original)
    with pytest.raises(ValueError, match='regular_absolute_path'):
        subject.regular(link)


def test_write_once_preserves_failed_attempt(tmp_path):
    path = tmp_path / 'receipt.json'
    subject.write(path, dict(status='FAILED'))
    with pytest.raises(FileExistsError):
        subject.write(path, dict(status='COMPLETE'))


def test_existing_venv_interpreter_symlink_valid(fixture, monkeypatch):
    link = fixture.root / 'python-link'
    link.symlink_to(fixture.config['python'])
    fixture.config['python'] = str(link)
    rebind(fixture, monkeypatch)
    subject.validate_execution(fixture.config_path, fixture.go_path)


def test_node5_budget_does_not_authorize_node2(fixture, monkeypatch):
    fixture.config['node2_authority'] = update_reference(fixture.config['node2_authority'], node='node5')
    rebind(fixture, monkeypatch)
    with pytest.raises(ValueError, match='separate_node2_budget_authority'):
        subject.validate_execution(fixture.config_path, fixture.go_path)


def test_forked_evaluator_refused(fixture, monkeypatch):
    monkeypatch.setattr(subject, 'IMPORT_PID', os.getpid()+1)
    with pytest.raises(ValueError, match='one_checkpoint_per_fresh_process'):
        subject.evaluate(fixture.config_path, fixture.go_path)


def test_source_closure_checks_actual_helper_and_required_files(tmp_path, monkeypatch):
    monkeypatch.setattr(subject, '__file__', str(tmp_path / 'gpu/orch_r159_matched_evaluation.py'))
    config = dict(source_root=str(tmp_path), sources={})
    with pytest.raises(ValueError, match='required_evaluator_closure'):
        subject.validate_sources(config)


def test_fake_frozen_weights_never_admitted(fixture):
    candidate = deepcopy(fixture.candidate)
    candidate['arm'], candidate['milestone'] = 'parented_frozen', 1
    cohort = subject.bound(candidate['cohort'])
    source = Path(cohort['members']['parented_frozen']['root']) / 'checkpoints/sleep_000001'
    commit = subject.bound(fixture.commit)
    commit.update(adapter_path=str(source / 'adapter'), optimizer_rng_path=str(source / 'optimizer_rng.pt'),
                  created_unix=time.time()-1)
    commit_reference = store(Path(fixture.commit['path']), commit)
    candidate['source_commit_path'] = str(source / 'COMMIT.json')
    candidate['manifest'] = update_reference(candidate['manifest'], commit_sha256=commit_reference['sha256'])
    candidate['source_custody'] = update_reference(candidate['source_custody'],
        source_root=cohort['members']['parented_frozen']['root'], source_commit_path=candidate['source_commit_path'],
        checkpoint_boundary=1, commit_sha256=commit_reference['sha256'], manifest_sha256=candidate['manifest']['sha256'])
    fixture.config['candidate'] = store(Path(fixture.config['candidate']['path']), candidate)
    subject.candidate_check(fixture.config, fixture.plan)
    commit_reference = update_reference(commit_reference, optimizer_steps=1)
    candidate['manifest'] = update_reference(candidate['manifest'], commit_sha256=commit_reference['sha256'])
    fixture.config['candidate'] = store(Path(fixture.config['candidate']['path']), candidate)
    with pytest.raises(ValueError, match='identical_step0_control_weights'):
        subject.candidate_check(fixture.config, fixture.plan)


def test_freezer_CPU_only_and_no_overwrite(tmp_path, monkeypatch):
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES', 'GPU-fixture')
    with pytest.raises(ValueError, match='CPU_only_freezer'):
        subject.freeze(tmp_path / 'sealed')


def test_extra_terminal_does_not_fake_control_completeness(fixture):
    store(fixture.root / 'ledger/unknown.COMPLETE.json', dict(status='COMPLETE'))
    with pytest.raises(ValueError, match='unknown_ledger_artifact_refused'):
        subject.ledger_status(fixture.root, fixture.plan_ref['sha256'])


def test_completed_dispatch_records_exit_and_private_subprocess(fixture, monkeypatch):
    from gpu import orch_r130_benchmark_sidecar as sidecar
    monkeypatch.setattr(sidecar, 'scan', lambda config: dict(clear=True, blocking_reasons=[]))
    monkeypatch.setattr(sidecar, 'identity', lambda pid: None if pid == 42 else dict(pid=pid))
    engine = FakeEngine()
    def launch(command, **options):
        assert command[:3] == ['timeout', '--signal=TERM', '--kill-after=5s']
        assert command[6:9] == ['-m', 'gpu.orch_r159_matched_evaluation', 'evaluate']
        assert options['start_new_session'] and options['stdin'] == subject.subprocess.DEVNULL
        assert options['stdout'] is options['stderr'] or options['stderr'] == subject.subprocess.STDOUT
        assert 'OPENAI_API_KEY' not in options['env']
        monkeypatch.setenv('R159_EXECUTION_SHA256', subject.sha(fixture.config_path))
        monkeypatch.setenv('CUDA_VISIBLE_DEVICES', fixture.config['gpu_uuid'])
        monkeypatch.setattr(subject, 'USED', False)
        monkeypatch.setattr(subject.native, '_load_engine', lambda *args: engine)
        monkeypatch.setattr(subject.native, '_snapshot', lambda *args: dict(adapter_state_sha256='a'*64))
        monkeypatch.setattr(subject, 'sealed_tasks', lambda plan: [dict(messages=[dict(role='user', content='fixture')])]*28)
        monkeypatch.setattr(subject, 'score_task', lambda *args: dict(eligible=True, score=0.5))
        subject.evaluate(fixture.config_path, fixture.go_path)
        return SimpleNamespace(pid=1234, wait=lambda: 0, poll=lambda: 0)
    monkeypatch.setattr(subject.subprocess, 'Popen', launch)
    result = subject.dispatch(fixture.config_path, fixture.go_path)
    assert result['completed'] == 1 and result['calls_charged'] == 56


def test_COMMIT_alone_not_initialization_readiness(fixture):
    Path(fixture.candidate['initialized']['path']).unlink()
    with pytest.raises(ValueError, match='regular_file_required'):
        subject.candidate_check(fixture.config, fixture.plan)


def test_failed_capacity_is_not_ready(fixture):
    fixture.candidate['initialized'] = update_reference(fixture.candidate['initialized'],
                                                       initialization_validation=dict(status='FAIL'))
    fixture.config['candidate'] = store(Path(fixture.config['candidate']['path']), fixture.candidate)
    with pytest.raises(ValueError, match='successful_common_initializer'):
        subject.candidate_check(fixture.config, fixture.plan)


def test_failed_initializer_exit_is_not_ready(fixture):
    owner = subject.bound(fixture.config['source_owner_authority'])
    owner['initializer_lifecycle'] = update_reference(owner['initializer_lifecycle'], service_returncode=1)
    fixture.config['source_owner_authority'] = store(Path(fixture.config['source_owner_authority']['path']), owner)
    with pytest.raises(ValueError, match='actual_successful_initializer_exit'):
        subject.candidate_check(fixture.config, fixture.plan)


def test_optional_saved_initializer_recovery_copied_provenance(fixture):
    candidate = deepcopy(fixture.candidate)
    donor = subject.bound(candidate['initial_commit'])
    donor_ref = store(fixture.root / 'inputs/saved_donor_COMMIT.json', donor)
    source = dict(schema='R158_SAVED_INITIALIZATION_SOURCE_V1',
                  commit=dict(path='/source-node/previous_attempt/common_initial/COMMIT.json', sha256=donor_ref['sha256']))
    source_copy = store(fixture.root / 'inputs/initialization_source.json', source)
    source_original = dict(path='/source-node/new_attempt/control/initialization_source.json',
                           sha256=source_copy['sha256'])
    cohort = subject.bound(candidate['cohort'])
    cohort['common']['initialization_source'] = source_original
    candidate['cohort'] = store(Path(candidate['cohort']['path']), cohort)
    observation = dict(checkpoint_file_hashes=donor['checkpoint_sha256'])
    candidate['initialized'] = update_reference(candidate['initialized'],
        cohort_sha256=candidate['cohort']['sha256'], initialization_source=source_original,
        recovered_initial_state_before_validation=observation, observed_initial_state=observation)
    fixture.config['source_owner_authority'] = update_reference(fixture.config['source_owner_authority'],
        cohort_sha256=candidate['cohort']['sha256'], initialization_source_copy=source_copy,
        initialization_commit_copy=donor_ref)
    candidate['source_custody'] = update_reference(candidate['source_custody'],
        cohort_sha256=candidate['cohort']['sha256'], source_owner_authority=fixture.config['source_owner_authority'])
    fixture.config['candidate'] = store(Path(fixture.config['candidate']['path']), candidate)
    fixture.candidate = candidate
    attest_timestamps(fixture)
    subject.candidate_check(fixture.config, fixture.plan)
    candidate['initialized'] = update_reference(candidate['initialized'], recovered_initial_state_before_validation={})
    fixture.config['candidate'] = store(Path(fixture.config['candidate']['path']), candidate)
    with pytest.raises(ValueError, match='exact_restored_step0'):
        subject.candidate_check(fixture.config, fixture.plan)


def test_metadata_refs_cannot_point_at_child_readouts(fixture):
    candidate = deepcopy(fixture.candidate)
    candidate['initialized'] = store(fixture.root.parent / 'child/readouts/private.json', dict(synthetic=True))
    fixture.config['candidate'] = store(Path(fixture.config['candidate']['path']), candidate)
    with pytest.raises(ValueError, match='copied_metadata_not_child_files'):
        subject.candidate_check(fixture.config, fixture.plan)


def test_raw_package_metadata_serializes_stably():
    original = dict(metadata=dict(tuple_field=(1, 2)), messages=[dict(role='user', content='synthetic')])
    copied = json.loads(json.dumps(original))
    assert original != copied
    assert subject.digest(original) == subject.digest(copied)


def test_failed_subprocess_charged_without_retry(fixture, monkeypatch):
    from gpu import orch_r130_benchmark_sidecar as sidecar
    monkeypatch.setattr(sidecar, 'scan', lambda config: dict(clear=True, blocking_reasons=[]))
    monkeypatch.setattr(sidecar, 'identity', lambda pid: None if pid == 42 else dict(pid=pid))
    monkeypatch.setattr(subject.subprocess, 'Popen', lambda *args, **kwargs:
                        SimpleNamespace(pid=1234, wait=lambda: 124, poll=lambda: 124))
    with pytest.raises(ValueError, match='fresh_runner_complete_required'):
        subject.dispatch(fixture.config_path, fixture.go_path)
    status = subject.ledger_status(fixture.root, fixture.plan_ref['sha256'])
    assert status['failed'] == 1 and status['calls_charged'] == 56


def test_source_inventory_drift_fails_closed(tmp_path, monkeypatch):
    helper = tmp_path / 'gpu/orch_r159_matched_evaluation.py'
    required = set(subject.native.REQUIRED_SOURCES) | {'gpu/orch_r159_matched_evaluation.py',
        'gpu/orch_r130_benchmark_sidecar.py', 'gpu/orch_rich_hot_node2_scan.py',
        'organism_v6/reasoning_gym_gym.py', 'organism_v6/reasoning_gym_families.json',
        'organism_v6/gym_backend.py', 'organism_v6/bootstrap_reasoning_gym.txt',
        'tests/test_orch_r159_matched_evaluation.py'}
    pins = {}
    for name in required:
        path = tmp_path / name
        path.parent.mkdir(exist_ok=True, parents=True)
        path.write_text('synthetic fixture')
        pins[name] = subject.sha(path)
    monkeypatch.setattr(subject, '__file__', str(helper))
    config = dict(source_root=str(tmp_path), sources=pins)
    subject.validate_sources(config)
    (tmp_path / 'gpu/unpinned.py').write_text('synthetic extra closure')
    with pytest.raises(ValueError, match='complete_executing_python_closure'):
        subject.validate_sources(config)


def test_capacity_summary_cannot_mask_failed_actual_proof(fixture):
    candidate = deepcopy(fixture.candidate)
    candidate['capacity'] = update_reference(candidate['capacity'], status='FAIL')
    summary = subject.bound(candidate['initialized'])['initialization_validation']
    summary['sha256'] = candidate['capacity']['sha256']
    candidate['initialized'] = update_reference(candidate['initialized'], initialization_validation=summary)
    fixture.config['candidate'] = store(Path(fixture.config['candidate']['path']), candidate)
    with pytest.raises(ValueError, match='actual_bound_capacity_PASS_not_summary_only'):
        subject.candidate_check(fixture.config, fixture.plan)


def install_predating_recovery(fixture):
    candidate = fixture.candidate
    created = subject.bound(fixture.plan['freeze'])['frozen_unix']-60
    candidate['initial_commit'] = update_reference(candidate['initial_commit'], created_unix=created)
    original = subject.bound(candidate['initial_commit'])
    donor = dict(original, adapter_path='/source-node/saved-initial/adapter')
    donor_ref = store(fixture.root / 'inputs/saved_initial_COMMIT.json', donor)
    source_copy = store(fixture.root / 'inputs/saved_initial_source.json',
        dict(schema='R158_SAVED_INITIALIZATION_SOURCE_V1',
             commit=dict(path='/source-node/saved-initial/COMMIT.json', sha256=donor_ref['sha256'])))
    source_original = dict(path='/source-node/admitted/control/INITIALIZATION_SOURCE.json', sha256=source_copy['sha256'])
    cohort = subject.bound(candidate['cohort'])
    cohort['common']['initialization_source'] = source_original
    candidate['cohort'] = store(Path(candidate['cohort']['path']), cohort)
    observation = dict(checkpoint_file_hashes=original['checkpoint_sha256'])
    candidate['initialized'] = update_reference(candidate['initialized'],
        cohort_sha256=candidate['cohort']['sha256'], checkpoint_commit_sha256=candidate['initial_commit']['sha256'],
        initialization_source=source_original, observed_initial_state=observation,
        recovered_initial_state_before_validation=observation)
    fixture.commit = update_reference(fixture.commit, created_unix=created)
    candidate['manifest'] = update_reference(candidate['manifest'], commit_sha256=fixture.commit['sha256'])
    fixture.config['source_owner_authority'] = update_reference(fixture.config['source_owner_authority'],
        cohort_sha256=candidate['cohort']['sha256'], initialization_source_copy=source_copy,
        initialization_commit_copy=donor_ref)
    candidate['source_custody'] = update_reference(candidate['source_custody'],
        cohort_sha256=candidate['cohort']['sha256'], commit_sha256=fixture.commit['sha256'],
        manifest_sha256=candidate['manifest']['sha256'])
    return attest_timestamps(fixture)


def revise_timing(fixture, timing):
    owner = subject.bound(fixture.config['source_owner_authority'])
    reference = store(Path(owner['timestamp_custody']['path']), timing)
    fixture.config['source_owner_authority'] = update_reference(fixture.config['source_owner_authority'],
                                                               timestamp_custody=reference)
    fixture.candidate['source_custody'] = update_reference(fixture.candidate['source_custody'],
        source_owner_authority=fixture.config['source_owner_authority'], timestamp_custody=reference)
    fixture.config['candidate'] = store(Path(fixture.config['candidate']['path']), fixture.candidate)


def test_predating_unused_exact_saved_initial_is_valid(fixture):
    install_predating_recovery(fixture)
    assert subject.bound(fixture.candidate['initial_commit'])['created_unix'] < subject.bound(fixture.plan['freeze'])['frozen_unix']
    subject.candidate_check(fixture.config, fixture.plan)
    assert fixture.plan['total_call_cap'] == 672 and len(fixture.plan['slots']) == 12


def test_predating_without_exact_recovery_still_refused(fixture):
    install_predating_recovery(fixture)
    cohort = subject.bound(fixture.candidate['cohort'])
    cohort['common'].pop('initialization_source')
    fixture.candidate['cohort'] = store(Path(fixture.candidate['cohort']['path']), cohort)
    initialized = subject.bound(fixture.candidate['initialized'])
    initialized.pop('initialization_source')
    initialized['cohort_sha256'] = fixture.candidate['cohort']['sha256']
    fixture.candidate['initialized'] = store(Path(fixture.candidate['initialized']['path']), initialized)
    fixture.config['source_owner_authority'] = update_reference(fixture.config['source_owner_authority'],
        cohort_sha256=fixture.candidate['cohort']['sha256'])
    fixture.candidate['source_custody'] = update_reference(fixture.candidate['source_custody'],
        cohort_sha256=fixture.candidate['cohort']['sha256'])
    attest_timestamps(fixture)
    with pytest.raises(ValueError, match='older_initializer_requires_exact_saved_initial_provenance'):
        subject.candidate_check(fixture.config, fixture.plan)


@pytest.mark.parametrize('arm', subject.ARMS)
@pytest.mark.parametrize('kind', ['birth', 'train', 'evaluation'])
def test_freeze_after_any_arm_exposure_refused(fixture, arm, kind):
    timing = subject.bound(install_predating_recovery(fixture))
    timing['arm_exposures'][arm][kind] = update_reference(timing['arm_exposures'][arm][kind],
        status='OBSERVED', first_unix=subject.bound(fixture.plan['freeze'])['frozen_unix']-1)
    revise_timing(fixture, timing)
    with pytest.raises(ValueError, match='task_freeze_before_any_admitted_birth_TRAIN_eval'):
        subject.candidate_check(fixture.config, fixture.plan)


@pytest.mark.parametrize('value', [None, True, float('nan'), float('inf'), '1789620776', 0])
def test_ambiguous_enrollment_timestamps_refused(fixture, value):
    timing = subject.bound(install_predating_recovery(fixture))
    timing['enrollment_unix'] = value
    if type(value) is float and not subject.math.isfinite(value):
        revise_timing(fixture, timing)
        with pytest.raises(ValueError):
            subject.candidate_check(fixture.config, fixture.plan)
        return
    revise_timing(fixture, timing)
    with pytest.raises(ValueError, match='finite_unambiguous_custody_timestamps'):
        subject.candidate_check(fixture.config, fixture.plan)


@pytest.mark.parametrize('changes', [dict(status='UNKNOWN', first_unix=None),
    dict(status='OBSERVED', first_unix=None), dict(status='OBSERVED', first_unix=True),
    dict(status='NOT_OCCURRED', first_unix=123), dict(coverage_complete=False), dict(observed_unix=None)])
def test_unknown_or_incomplete_exposure_history_refused(fixture, changes):
    timing = subject.bound(install_predating_recovery(fixture))
    events = timing['arm_exposures']['parented_learning']
    events['evaluation'] = update_reference(events['evaluation'], **changes)
    revise_timing(fixture, timing)
    with pytest.raises(ValueError):
        subject.candidate_check(fixture.config, fixture.plan)


@pytest.mark.parametrize('change', [dict(saved_initial_generation_calls=1),
    dict(saved_initial_optimizer_updates=1), dict(saved_initial_generation_calls=False),
    dict(saved_initial_training_exposure=True), dict(saved_initial_evaluation_exposure=True)])
def test_used_saved_initial_state_refused(fixture, change):
    timing = subject.bound(install_predating_recovery(fixture))
    timing.update(change)
    revise_timing(fixture, timing)
    with pytest.raises(ValueError, match='untouched_zero_use_saved_initializer'):
        subject.candidate_check(fixture.config, fixture.plan)


def test_freeze_after_enrollment_or_equal_exposure_refused(fixture):
    timing = subject.bound(install_predating_recovery(fixture))
    timing['enrollment_unix'] = subject.bound(fixture.plan['freeze'])['frozen_unix']
    revise_timing(fixture, timing)
    with pytest.raises(ValueError, match='freeze_before_trusted_enrollment'):
        subject.candidate_check(fixture.config, fixture.plan)


def test_refrozen_same_task_selection_receipt_rejected(fixture):
    frozen = subject.bound(fixture.plan['freeze'])
    frozen['frozen_unix'] += 1
    reference = store(fixture.root / 'inputs/REFROZEN.json', frozen)
    with pytest.raises(ValueError, match='original_task_freeze_no_refreezing'):
        subject.plan_document(reference)


def test_saved_initial_timestamp_cannot_be_rewritten(fixture):
    install_predating_recovery(fixture)
    owner = subject.bound(fixture.config['source_owner_authority'])
    owner['initialization_commit_copy'] = update_reference(owner['initialization_commit_copy'], created_unix=time.time()-1)
    source = subject.bound(owner['initialization_source_copy'])
    source['commit']['sha256'] = owner['initialization_commit_copy']['sha256']
    owner['initialization_source_copy'] = store(Path(owner['initialization_source_copy']['path']), source)
    fixture.config['source_owner_authority'] = store(Path(fixture.config['source_owner_authority']['path']), owner)
    with pytest.raises(ValueError):
        subject.candidate_check(fixture.config, fixture.plan)


def test_missing_timestamp_custody_not_inferred_from_commit(fixture):
    owner = subject.bound(fixture.config['source_owner_authority'])
    owner.pop('timestamp_custody')
    fixture.config['source_owner_authority'] = store(Path(fixture.config['source_owner_authority']['path']), owner)
    with pytest.raises(ValueError, match='explicit_timestamp_custody_required'):
        subject.candidate_check(fixture.config, fixture.plan)


def test_main_go_covers_timestamp_custody_bytes(fixture, monkeypatch):
    install_predating_recovery(fixture)
    rebind(fixture, monkeypatch)
    subject.validate_execution(fixture.config_path, fixture.go_path)
    timing = subject.bound(subject.bound(fixture.config['source_owner_authority'])['timestamp_custody'])
    timing['observed_unix'] += 1
    revise_timing(fixture, timing)
    store(fixture.config_path, fixture.config)
    with pytest.raises(ValueError, match='exact_Main_GO_scope'):
        subject.validate_execution(fixture.config_path, fixture.go_path)


def install_interval(fixture, arm='parented_learning', kind='birth', **changes):
    timing = subject.bound(install_predating_recovery(fixture))
    event_ref = timing['arm_exposures'][arm][kind]
    event = subject.bound(event_ref)
    event.pop('first_unix')
    witness = store(fixture.root / 'inputs' / f'{arm}_{kind}_WITNESS.json',
                    dict(kind=kind, arm=arm, metadata_only=True))
    event.update(status='OBSERVED_INTERVAL', first_earliest_unix=timing['observed_unix']-2,
                 first_latest_unix=timing['observed_unix']-1, source_evidence=[witness])
    event.update(changes)
    timing['arm_exposures'][arm][kind] = store(Path(event_ref['path']), event)
    revise_timing(fixture, timing)
    return event, witness


@pytest.mark.parametrize('arm', subject.ARMS)
@pytest.mark.parametrize('kind', ('birth', 'train', 'evaluation'))
def test_witnessed_intervals_accept_all_arms_and_kinds(fixture, arm, kind):
    install_interval(fixture, arm, kind)
    subject.candidate_check(fixture.config, fixture.plan)


@pytest.mark.parametrize('bounds', ('crosses_freeze', 'equals_freeze', 'inverted', 'future',
    'earliest_nan', 'latest_nan', 'earliest_inf', 'latest_inf', 'earliest_bool', 'latest_string'))
def test_invalid_interval_bounds_refused(fixture, bounds):
    freeze = subject.bound(fixture.plan['freeze'])['frozen_unix']
    changes = {
        'crosses_freeze': dict(first_earliest_unix=freeze-1),
        'equals_freeze': dict(first_earliest_unix=freeze),
        'inverted': dict(first_earliest_unix=time.time()),
        'future': dict(first_latest_unix=time.time()+100),
        'earliest_nan': dict(first_earliest_unix=float('nan')),
        'latest_nan': dict(first_latest_unix=float('nan')),
        'earliest_inf': dict(first_earliest_unix=float('inf')),
        'latest_inf': dict(first_latest_unix=float('inf')),
        'earliest_bool': dict(first_earliest_unix=True),
        'latest_string': dict(first_latest_unix='123'),
    }[bounds]
    install_interval(fixture, **changes)
    with pytest.raises(ValueError):
        subject.candidate_check(fixture.config, fixture.plan)


def test_interval_equal_endpoints_allowed(fixture):
    timestamp = time.time()-3
    install_interval(fixture, first_earliest_unix=timestamp, first_latest_unix=timestamp)
    subject.candidate_check(fixture.config, fixture.plan)


@pytest.mark.parametrize('evidence', ([], None, {}, [dict(path='/tmp/not-witness', sha256='x')]))
def test_interval_requires_explicit_evidence(fixture, evidence):
    install_interval(fixture, source_evidence=evidence)
    with pytest.raises(ValueError):
        subject.candidate_check(fixture.config, fixture.plan)


def test_interval_changed_witness_refused(fixture):
    _, witness = install_interval(fixture)
    Path(witness['path']).write_text('changed')
    with pytest.raises(ValueError, match='bound_interval_source_evidence'):
        subject.candidate_check(fixture.config, fixture.plan)


@pytest.mark.parametrize('change', ('missing_witness', 'missing_field', 'extra_exact_field',
                                  'outside_inputs', 'duplicate_witness', 'incomplete_coverage'))
def test_interval_custody_shape_and_scope_refused(fixture, change):
    event, witness = install_interval(fixture)
    if change == 'missing_witness':
        Path(witness['path']).unlink()
    elif change == 'missing_field':
        event.pop('source_evidence')
    elif change == 'extra_exact_field':
        event['first_unix'] = event['first_earliest_unix']
    elif change == 'outside_inputs':
        event['source_evidence'] = [store(fixture.root / 'OUTSIDE.json', dict(metadata=True))]
    elif change == 'duplicate_witness':
        event['source_evidence'] = [witness, witness]
    else:
        event['coverage_complete'] = False
    owner = subject.bound(fixture.config['source_owner_authority'])
    timing = subject.bound(owner['timestamp_custody'])
    event_ref = timing['arm_exposures']['parented_learning']['birth']
    timing['arm_exposures']['parented_learning']['birth'] = store(Path(event_ref['path']), event)
    revise_timing(fixture, timing)
    with pytest.raises(ValueError):
        subject.candidate_check(fixture.config, fixture.plan)


def test_interval_cannot_replace_required_event_kind(fixture):
    install_interval(fixture)
    timing = subject.bound(subject.bound(fixture.config['source_owner_authority'])['timestamp_custody'])
    timing['arm_exposures']['parented_learning'].pop('train')
    revise_timing(fixture, timing)
    with pytest.raises(ValueError, match='birth_TRAIN_evaluation_coverage'):
        subject.candidate_check(fixture.config, fixture.plan)


def test_interval_witness_rechecked_during_evaluation(fixture, monkeypatch):
    _, witness = install_interval(fixture)
    rebind(fixture, monkeypatch)
    engine = prepare_engine(fixture, monkeypatch)
    original = engine.generate

    def tamper_witness(messages, max_new_tokens):
        response = original(messages, max_new_tokens)
        Path(witness['path']).write_text('synthetic witness mutation')
        return response

    monkeypatch.setattr(engine, 'generate', tamper_witness)
    with pytest.raises(ValueError, match='immutable_evaluation_input'):
        subject.evaluate(fixture.config_path, fixture.go_path)
    assert len(engine.calls) == 1
