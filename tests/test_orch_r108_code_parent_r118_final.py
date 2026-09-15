from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest

from gpu import orch_r108_code_parent_r118_final as final


write = final.coordinator.write
read = final.coordinator.read


def selection_fixture(common, state, *, commit=None):
    snapshot = common / 'final_selection' / f"state_{state['generation']}.json"
    write(snapshot, state, replace=True)
    selected = dict(schema='R118_FINAL_SELECTION_V1', scheduled_unix=final.CUTOFF,
        selected_unix=final.CUTOFF + 1, evaluation_deadline_unix=final.EVAL_END,
        shared_root=str(common), generation=state['generation'], checkpoint=state['checkpoint'],
        committed_sleep=commit, state_reference=final.ref(snapshot),
        lineage_sha256={name:final.coordinator.sha(common / name)
            for name in ('CONFIG.json', 'INITIALIZED.json', 'ADOPTION.json')},
        lifetime_metrics={name:state[name] for name in final.selector.METRICS},
        shared_metrics={name:state['shared_' + name] for name in final.selector.METRICS},
        branches=list(final.selector.BRANCHES))
    write(common / 'FINAL_SELECTION.json', selected, replace=True)
    return dict(state=state, selection=selected)


@pytest.fixture
def prepared(tmp_path, monkeypatch):
    source = tmp_path / 'source'
    source.mkdir()
    (source / 'fixture.py').write_text('CPU fixture only\n')
    manifest = {'fixture.py': final.coordinator.sha(source / 'fixture.py')}
    write(tmp_path / 'SOURCE_SHA256.json', manifest)
    write(tmp_path / 'CPU_TESTS.json', dict(passed=True, cuda_initialized=False,
        source_manifest_sha256=final.coordinator.sha(tmp_path / 'SOURCE_SHA256.json')))
    monkeypatch.setattr(final, 'SOURCE_ROOT', source)
    original = tmp_path / 'original'
    common = tmp_path / 'common'
    owner = common / 'F1'
    owner.mkdir(parents=True)
    optimizer = owner / 'optimizer.json'
    write(optimizer, dict(CPU_fixture=True))
    checkpoint_file = owner / 'CHECKPOINT.json'
    write(checkpoint_file, dict(adapter={}, complete=True, optimizer_rng_sha256=final.coordinator.sha(optimizer)))
    checkpoint = dict(path=str(checkpoint_file), path_sha256=final.coordinator.sha(checkpoint_file),
        optimizer_path=str(optimizer), optimizer_path_sha256=final.coordinator.sha(optimizer))
    original_plan = dict(physical=2, gpu_uuid=final.activation.original.DEVICES[2],
        lease_end_unix=final.EVAL_END + 21600 + 3600, hard_deadline_unix=final.CUTOFF + 60,
        native_cap=25, parent_cap=10, model_dir=str(tmp_path / 'model'))
    write(original / 'PLAN.json', original_plan)
    write(common / 'CONFIG.json', dict(owner='F1', initial_checkpoint=checkpoint, branches={
        branch:dict(root=str(original if branch == 'F3' else common / branch))
        for branch in final.coordinator.BRANCHES}))
    config_sha = final.coordinator.sha(common / 'CONFIG.json')
    write(original / 'SHARED_ACTIVATION.json', dict(
        predecessor_plan_sha256=final.coordinator.sha(original / 'PLAN.json'),
        shared_learner=dict(branch='F3', root=str(common), config_sha256=config_sha)))
    tasks = []
    for identifier in final.TASK_IDS:
        task = dict(task_id=identifier, split='FINAL', prompt='Synthetic CPU-only fixture.', tests=[])
        task['content_sha256'] = final.run.policy.digest(task)
        tasks.append(task)
    write(original / 'COHORT.json', dict(FINAL=tasks))
    metrics = dict(optimizer_steps=1125, child_token_exposures=100, anchor_token_exposures=42)
    state = dict(generation=0, config_sha256=config_sha, checkpoint=checkpoint, **metrics,
        **{'shared_' + name:0 for name in final.selector.METRICS})
    write(common / 'INITIALIZED.json', dict(state=state))
    write(common / 'ADOPTION.json', dict(CPU_fixture=True))
    binding_path = common / 'FINAL_SELECTION.json'
    binding = selection_fixture(common, state)
    monkeypatch.setattr(final.release, 'prepare', lambda root, original: write(root / 'RELEASE_PLAN.json',
        dict(CPU_fixture=True)))
    monkeypatch.setattr(final.release, 'wait_release', lambda root: dict(CPU_fixture=True))
    monkeypatch.setattr(final.release, 'validate_release', lambda root: dict(CPU_fixture=True))
    monkeypatch.setattr(final.selector, 'select', lambda *args, **kwargs: pytest.fail('CODE cannot select'))
    monkeypatch.setattr(final.selector, 'wait_select', lambda *args, **kwargs: pytest.fail('CODE cannot wait/select'))
    root = tmp_path / 'evaluation'
    plan = final.prepare(root, original, binding_path, source)
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES', original_plan['gpu_uuid'])
    return SimpleNamespace(root=root, original=original, common=common, source=source,
        binding_path=binding_path, binding=binding, plan=plan, tasks=tasks)


def test_prepare_hashes_but_never_parses_sealed_cohort(prepared):
    (prepared.original / 'COHORT.json').write_text('Not JSON; preparation must only hash bytes.')
    plan = final.prepare(prepared.root.parent / 'second_eval', prepared.original,
        prepared.binding_path, prepared.source)
    assert plan['native_cap'] == 8 and plan['parent_cap'] == 0
    assert plan['decoder'] == final.DECODER
    assert not (prepared.root.parent / 'second_eval/reservations').exists()


def test_new_eval_deadline_does_not_extend_original_ledger(prepared):
    original = (prepared.original / 'PLAN.json').read_bytes()
    assert prepared.plan['hard_deadline_unix'] == final.EVAL_END
    assert read(prepared.original / 'PLAN.json')['hard_deadline_unix'] == final.CUTOFF + 60
    final.validate_plan(prepared.root)
    assert (prepared.original / 'PLAN.json').read_bytes() == original


def test_earlier_lease_margin_limits_only_new_allocation(prepared):
    original = read(prepared.original / 'PLAN.json')
    original['lease_end_unix'] = final.CUTOFF + 300 + 21600
    write(prepared.original / 'PLAN.json', original, replace=True)
    adopted = read(prepared.original / 'SHARED_ACTIVATION.json')
    adopted['predecessor_plan_sha256'] = final.coordinator.sha(prepared.original / 'PLAN.json')
    write(prepared.original / 'SHARED_ACTIVATION.json', adopted, replace=True)
    plan = final.prepare(prepared.root.parent / 'short_eval', prepared.original,
        prepared.binding_path, prepared.source)
    assert plan['hard_deadline_unix'] == final.CUTOFF + 300


@pytest.mark.parametrize('now', [final.CUTOFF - 1, final.EVAL_END, final.EVAL_END - 4])
def test_clock_gate_precedes_any_sealed_task_read(prepared, monkeypatch, now):
    monkeypatch.setattr(final, 'bound', lambda reference: pytest.fail('sealed read before gate'))
    with pytest.raises(ValueError, match='FINAL_clock_gate'):
        final.final_tasks(prepared.plan, now)


@pytest.mark.parametrize('field,value', [('native_cap', 9), ('parent_cap', 1),
    ('experience_rows', 1), ('optimizer_steps', 1), ('max_output_token_ids', 17000)])
def test_caps_and_no_training_are_not_mutable(prepared, field, value):
    plan = dict(prepared.plan, **{field:value})
    write(prepared.root / 'PLAN.json', plan, replace=True)
    with pytest.raises(ValueError, match='exact_eight_call'):
        final.validate_plan(prepared.root)


def test_exact_fixed_default_decoder(prepared):
    plan = deepcopy(prepared.plan)
    plan['decoder']['max_new_tokens'] = 3072
    write(prepared.root / 'PLAN.json', plan, replace=True)
    with pytest.raises(ValueError, match='fixed_FINAL_contract'):
        final.validate_plan(prepared.root)


def test_initial_fully_committed_checkpoint_allowed(prepared):
    assert final.validate_binding(prepared.plan, prepared.binding_path,
        final.CUTOFF + 2) == prepared.binding


def committed(prepared, generation=1, completed_unix=final.CUTOFF - 1):
    state = dict(prepared.binding['state'], generation=generation)
    path = prepared.common / f'generation_{generation - 1:06d}/sleep/COMPLETE.json'
    write(path, dict(state=state, completed_unix=completed_unix, same_optimizer=True))
    return selection_fixture(prepared.common, state, commit=final.ref(path))


def test_committed_shared_state_not_partial_training(prepared):
    binding = committed(prepared)
    assert final.validate_binding(prepared.plan, prepared.binding_path,
        final.CUTOFF + 2) == binding


def test_post_cutoff_checkpoint_rejected(prepared):
    committed(prepared, completed_unix=final.CUTOFF + 1)
    with pytest.raises(ValueError, match='committed_sleep_binding'):
        final.validate_binding(prepared.plan, prepared.binding_path, final.CUTOFF + 2)


def test_future_STATE_never_changes_frozen_Main_selection(prepared, monkeypatch):
    write(prepared.common / 'STATE.json', dict(generation=900, checkpoint='future state must not be read'))
    real_read = final.selector.read

    def checked(path):
        assert Path(path) != prepared.common / 'STATE.json'
        return real_read(path)

    monkeypatch.setattr(final.selector, 'read', checked)
    assert final.validate_binding(prepared.plan, prepared.binding_path, final.CUTOFF + 2) == prepared.binding


def test_uncommitted_state_cannot_be_forged_from_old_commit(prepared):
    binding = deepcopy(prepared.binding['selection'])
    binding['checkpoint']['path_sha256'] = '0' * 64
    write(prepared.binding_path, binding, replace=True)
    with pytest.raises(ValueError, match='selected_state_binding'):
        final.validate_binding(prepared.plan, prepared.binding_path, final.CUTOFF + 2)


def test_sealed_tasks_open_only_after_gate_and_match_content(prepared):
    assert final.final_tasks(prepared.plan, final.CUTOFF + 1) == prepared.tasks
    cohort = read(prepared.original / 'COHORT.json')
    cohort['FINAL'][0]['prompt'] = 'Changed CPU fixture'
    write(prepared.original / 'COHORT.json', cohort, replace=True)
    plan = dict(prepared.plan, cohort=final.ref(prepared.original / 'COHORT.json'))
    with pytest.raises(ValueError, match='original_task_content_hash'):
        final.final_tasks(plan, final.CUTOFF + 1)


def test_zero_baseline_not_replayed_but_not_confused_with_terminal_final(prepared):
    (prepared.original / 'readouts/C000_ZERO').mkdir(parents=True)
    assert final.prior_final_attempts(prepared.original) == []
    partial = prepared.original / 'readouts/C021_FINAL'
    partial.mkdir()
    assert final.prior_final_attempts(prepared.original) == [str(partial)]
    write(partial / 'COMPLETE.json', dict(completed=True))
    assert final.prior_final_attempts(prepared.original) == [str(partial)]


def fake_factory(prepared, monkeypatch, *, fail=False, bad_count=False):
    observed = []
    monkeypatch.setattr(final, 'verify_engine', lambda engine, binding: observed.append('verified'))
    monkeypatch.setattr(final.run.environment, 'score', lambda task, raw: dict(cpu_fixture=True))

    class Engine:
        def generate_batch(self, messages, *, max_new_tokens):
            assert max_new_tokens == 2048 and len(messages) == 8
            assert all(message[-1]['content'] == 'Synthetic CPU-only fixture.' for message in messages)
            assert not any('reference_expression' in str(message) for message in messages)
            observed.append('generated')
            if fail:
                raise RuntimeError('CPU operational failure')
            rows = [dict(messages=message, raw='CPU synthetic response', token_ids=[7, 9],
                terminal=True, truncated=False, input_truncated=False, effective_generation_cap=2048)
                for message in messages]
            return rows[:-1] if bad_count else rows

    def load(plan, binding, check):
        reservations = list((prepared.root / 'reservations').glob('*.json'))
        assert len(reservations) == 8
        assert all(read(path)['status'] == 'STARTED' for path in reservations)
        assert all(read(path)['routes'] == final.ROUTES for path in reservations)
        assert not (prepared.original / 'reservations').exists()
        check('CPU_load')
        return Engine()

    return load, observed


def test_eight_reserved_before_dispatch_separate_ledger_no_parent_buffer(prepared, monkeypatch):
    factory, observed = fake_factory(prepared, monkeypatch)
    final.evaluate(prepared.root, prepared.plan, prepared.binding,
        engine_factory=factory, clock=lambda: final.CUTOFF + 2)
    complete = read(prepared.root / 'COMPLETE.json')
    assert complete['native_calls'] == complete['completed_calls'] == 8
    assert complete['child_tokens'] == 16 and complete['experience_rows'] == 0
    assert complete['parent_calls'] == complete['optimizer_steps'] == 0
    assert observed == ['generated', 'verified']
    assert not (prepared.root / 'parent_queue').exists()
    assert not (prepared.root / 'sleep_buffer').exists()
    assert not (prepared.original / 'reservations').exists()


@pytest.mark.parametrize('bad_count', [False, True])
def test_failed_batch_preserved_and_cannot_retry(prepared, monkeypatch, bad_count):
    factory, observed = fake_factory(prepared, monkeypatch, fail=not bad_count, bad_count=bad_count)
    with pytest.raises((RuntimeError, ValueError)):
        final.evaluate(prepared.root, prepared.plan, prepared.binding,
            engine_factory=factory, clock=lambda: final.CUTOFF + 2)
    assert len(list((prepared.root / 'reservations').glob('*.json'))) == 8
    assert all(read(path)['status'] == 'FAILED' for path in (prepared.root / 'reservations').glob('*.json'))
    assert not (prepared.root / 'COMPLETE.json').exists()
    if bad_count:
        assert len(read(prepared.root / 'NATIVE_BATCH_RESPONSE.json')['responses']) == 7
    with pytest.raises(FileExistsError):
        final.evaluate(prepared.root, prepared.plan, prepared.binding,
            engine_factory=factory, clock=lambda: final.CUTOFF + 3)
    assert observed == ['generated']


def test_prior_original_FINAL_blocks_model_loading(prepared, monkeypatch):
    (prepared.original / 'readouts/C021_FINAL').mkdir(parents=True)
    with pytest.raises(ValueError, match='prior_FINAL_attempt'):
        final.evaluate(prepared.root, prepared.plan, prepared.binding,
            engine_factory=lambda *args: pytest.fail('duplicate GPU load'), clock=lambda: final.CUTOFF + 2)
    assert not (prepared.root / 'reservations').exists()


def test_scheduler_before_cutoff_has_no_scan_or_checkpoint_or_final_read(prepared, monkeypatch):
    current = [final.CUTOFF - 100]
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES', '')
    monkeypatch.setattr(final.activation.original, 'bind', lambda physical: None)
    monkeypatch.setattr(final.time, 'time', lambda: current[0])
    monkeypatch.setattr(final.time, 'sleep', lambda seconds: current.__setitem__(0, final.EVAL_END))
    monkeypatch.setattr(final.activation, 'scan', lambda root: pytest.fail('early GPU scan'))
    monkeypatch.setattr(final, 'validate_binding', lambda *args: pytest.fail('early common binding read'))
    monkeypatch.setattr(final, 'final_tasks', lambda *args: pytest.fail('early FINAL read'))
    final.schedule(prepared.root)
    assert (prepared.root / 'NOT_LAUNCHED.json').exists()
    assert not (prepared.root / 'LAUNCH.json').exists()


def test_scheduler_does_not_preempt_existing_owner_lock(prepared, monkeypatch):
    current = [final.CUTOFF + 2]
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES', '')
    monkeypatch.setattr(final.activation.original, 'bind', lambda physical: None)
    monkeypatch.setattr(final.time, 'time', lambda: current[0])
    monkeypatch.setattr(final.time, 'sleep', lambda seconds: current.__setitem__(0, final.EVAL_END))

    def busy(*args):
        raise BlockingIOError('CPU owned custody lock')

    monkeypatch.setattr(final.fcntl, 'flock', busy)
    monkeypatch.setattr(final.activation, 'scan', lambda root: pytest.fail('scan while custody held'))
    monkeypatch.setattr(final, 'run_child', lambda *args: pytest.fail('preemptive launch'))
    final.schedule(prepared.root)
    assert (prepared.root / 'NOT_LAUNCHED.json').exists()


def test_scheduler_launches_only_after_cutoff_binding_and_full_clear(prepared, monkeypatch):
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES', '')
    monkeypatch.setattr(final.activation.original, 'bind', lambda physical: None)
    monkeypatch.setattr(final.time, 'time', lambda: final.CUTOFF + 2)
    snapshot = dict(clear=True, scanner_euid=0, gpu={'uuid':prepared.plan['gpu_uuid']},
        device_minor=2, blocking_reasons=[])
    monkeypatch.setattr(final.activation, 'scan', lambda root: snapshot)
    calls = []
    monkeypatch.setattr(final, 'run_child', lambda root, plan: calls.append(root))
    final.schedule(prepared.root)
    assert calls == [prepared.root]
    assert read(prepared.root / 'ADMISSION.json') == snapshot
    assert not (prepared.original / 'reservations').exists()


def test_scheduler_uses_existing_strict_admission_not_memory_only():
    assert not final.activation.admitted(dict(clear=False, scanner_euid=0,
        gpu={'uuid':'OWN', 'memory_used_mib':0}, device_minor=2, blocking_reasons=['foreign_process']),
        {'gpu_uuid':'OWN'})


def test_no_actual_release_proof_means_no_eval_launch(prepared, monkeypatch):
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES', '')
    monkeypatch.setattr(final.activation.original, 'bind', lambda physical: None)
    monkeypatch.setattr(final.release, 'wait_release', lambda root: None)
    monkeypatch.setattr(final.activation, 'scan', lambda root: pytest.fail('scan without release'))
    monkeypatch.setattr(final, 'run_child', lambda *args: pytest.fail('no predecessor release'))
    final.schedule(prepared.root)
    assert read(prepared.root / 'NOT_LAUNCHED.json')['reason'] == 'NO_ACTUAL_PREDECESSOR_RELEASE'
