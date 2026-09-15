"""CPU-only PUREBASE contracts; no native engine, tokenizer or GPU calls."""

from types import SimpleNamespace

import pytest

from gpu import orch_r107_capability_base as runner


@pytest.fixture
def plan():
    return dict(schema=runner.SCHEMA, base_sha256=runner.BASE_SHA, adapter=None,
        training_updates=0, parent_calls=0, parent_access=False, train_ingestion=False,
        max_new_tokens=512, task_count=32, call_cap=32, conditions=['PUREBASE'],
        native_deadline_unix=200, hard_deadline_unix=250, lease_end_unix=30000,
        physical_index=3, device_minor=3, gpu_uuid=runner.scanner.DEVICES[3],
        model_dir='/unused/local/base', suite_sha256=runner.SUITE_SHA,
        sources={path: runner.sha(runner.SOURCE_ROOT / path) for path in runner.REQUIRED_SOURCES})


def test_plan_fixed_suite_and_actual_noadapter_options(plan):
    assert runner.validate_plan(plan, runner.SOURCE_ROOT, 100) is plan
    assert len(runner.policy.tasks()) == 32
    assert runner.policy.digest(runner.policy.tasks()) == runner.SUITE_SHA
    options = runner.base.options(plan['model_dir'], plan['gpu_uuid'])
    assert options.adapter_dir is None and options.phase == 'readout'
    assert options.expected_base_sha256 == runner.BASE_SHA


@pytest.mark.parametrize('field,value', [
    ('adapter', '/adapter'), ('base_sha256', 'changed'),
    ('training_updates', 1), ('parent_calls', 1), ('parent_access', True),
    ('train_ingestion', True), ('max_new_tokens', 1536), ('max_new_tokens', True),
    ('call_cap', 33), ('task_count', 31), ('conditions', ['LORA_OFF']),
    ('native_deadline_unix', 100), ('hard_deadline_unix', 200),
    ('lease_end_unix', 1000), ('gpu_uuid', 'GPU-other'), ('physical_index', 2),
    ('device_minor', 2), ('model_dir', 'relative'), ('suite_sha256', 'changed'),
    ('retained_calls', ['old']), ('prior_root', '/old'), ('new_call_cap', 32),
])
def test_plan_rejects_scope_or_budget_drift(plan, field, value):
    plan[field] = value
    with pytest.raises(ValueError):
        runner.validate_plan(plan, runner.SOURCE_ROOT, 100)


def test_plan_requires_test_and_runtime_hashes(plan):
    plan['sources'].pop('tests/test_orch_r107_capability_base.py')
    with pytest.raises(ValueError, match='runtime_sources_required'):
        runner.validate_plan(plan, runner.SOURCE_ROOT, 100)


def test_plan_rejects_changed_source_hash(plan):
    plan['sources']['gpu/orch_r107_capability_base.py'] = '0' * 64
    with pytest.raises(ValueError, match='source_binding_changed'):
        runner.validate_plan(plan, runner.SOURCE_ROOT, 100)


def frozen_engine(names=None, peft_config=None):
    observations = []
    parameters = [('weight', SimpleNamespace(requires_grad=False))] if names is None else names
    model = SimpleNamespace(named_parameters=lambda: parameters, peft_config=peft_config)
    return SimpleNamespace(model=model, verify_base=lambda: observations.append('base_hash')), observations


def test_frozen_check_verifies_base_and_noadapter_each_time():
    engine, observations = frozen_engine()
    before = runner.verify_frozen(engine)
    after = runner.verify_frozen(engine)
    assert observations == ['base_hash', 'base_hash']
    assert before == after
    assert before['no_adapter_verified'] and before['frozen_base_verified']
    assert before['base_sha256'] == runner.BASE_SHA and before['parameter_count'] == 1
    assert before['training_updates'] == before['parent_calls'] == 0


@pytest.mark.parametrize('names,peft_config', [
    ([('lora_A.weight', SimpleNamespace(requires_grad=False))], None),
    ([('weight', SimpleNamespace(requires_grad=True))], None),
    ([('weight', SimpleNamespace(requires_grad=False))], {}),
    ([], None),
])
def test_frozen_check_rejects_lora_peft_trainable_or_empty(names, peft_config):
    engine, observations = frozen_engine(names, peft_config)
    with pytest.raises(AssertionError):
        runner.verify_frozen(engine)
    assert observations == []


def test_frozen_check_propagates_base_hash_failure():
    engine, unused = frozen_engine()
    def changed_base():
        raise ValueError('frozen_base_changed')
    engine.verify_base = changed_base
    with pytest.raises(ValueError, match='frozen_base_changed'):
        runner.verify_frozen(engine)


def test_results_keep_all32_and_four_family_denominators_when_missing(tmp_path):
    result = runner.compact_results(tmp_path, [], False)
    assert result['totals']['tasks'] == len(result['rows']) == 32
    assert result['totals']['completions'] == {'missing': 32}
    assert result['totals']['passed'] == result['native_reserved_calls'] == 0
    assert not result['before_after_verified']
    assert set(result['families']) == set(runner.policy.FAMILIES)
    assert all(family['tasks'] == 8 for family in result['families'].values())


@pytest.mark.parametrize('terminal', [True, False])
def test_machine_outcome_separate_from_truncation_and_compact_tokens(tmp_path, terminal):
    task = runner.policy.tasks()[0]
    response = dict(messages=runner.policy.messages(task), raw='{"expression":"value * value"}',
        token_ids=[7, 99] if terminal else [7] * 512, terminal=terminal,
        truncated=not terminal, prompt_tokens=12)
    summary = runner.response_summary(task, response, 99)
    assert summary['machine_outcome']['passed']
    assert summary['passed'] is terminal
    assert summary['completion'] == ('complete' if terminal else 'truncated')
    assert summary['content_tokens'] == (1 if terminal else 512)
    call = dict(status='COMPLETE', response=response, summary=summary)
    runner.storage.atomic_json(tmp_path / 'CALL_000.json', call)
    result = runner.compact_results(tmp_path, [call], True)
    assert result['totals']['tasks'] == 32 and result['totals']['passed'] == int(terminal)
    assert result['native_reserved_calls'] == result['native_completed_calls'] == 1
    assert result['totals']['completions']['missing'] == 31
    assert result['rows'][0]['call_sha256'] == runner.sha(tmp_path / 'CALL_000.json')
    assert all(not {'raw', 'messages', 'token_ids'} & row.keys() for row in result['rows'])


def test_failed_reservation_is_not_dropped_or_counted_as_complete(tmp_path):
    call = dict(status='FAILED', error_type='TimeoutError')
    runner.storage.atomic_json(tmp_path / 'CALL_000.json', call)
    result = runner.compact_results(tmp_path, [call], False)
    assert result['native_reserved_calls'] == 1 and result['native_completed_calls'] == 0
    assert result['totals']['completions'] == {'execution_error': 1, 'missing': 31}
    assert result['totals']['passed'] == 0
