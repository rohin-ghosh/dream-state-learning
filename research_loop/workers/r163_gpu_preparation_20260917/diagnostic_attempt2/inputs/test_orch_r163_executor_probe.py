"""Real-Torch CPU probe checks; these never establish seven-billion validation."""

from dataclasses import replace
import json
from types import SimpleNamespace

import pytest

from test_orch_r161_native_executor import case
from gpu import orch_r163_executor_probe as probe


def longest(case):
    original = case.batch.components[0]
    component = replace(original, input_ids=(1,)*14+(3, 4),
        labels=(-100,)*14+(3, 4), target_ids=(3, 4))
    return SimpleNamespace(sha256='d'*64, components=(component, *case.batch.components[1:]))


def test_real_cpu_probe_restores_every_state(case, tmp_path):
    case.child.plan['r163_validation_only'] = True
    before = case.executor.snapshot()
    initial = probe.saved_state(case.child)
    receipt = probe.run_probe(case.executor, [case.batch], longest(case), tmp_path/'probe')
    assert receipt['status'] == 'PASS'
    assert receipt['real_7b_validated'] is False
    assert receipt['scientific_optimizer_updates'] == 0
    assert receipt['frozen_no_update_verified'] is True
    assert receipt['state_restored'] is True
    assert case.executor.snapshot() == before
    probe.compare_tree(case.child.torch, probe.saved_state(case.child), initial, dict(atol=0, rtol=0))
    assert receipt['comparisons'][0]['reference_losses'] == receipt['comparisons'][0]['suffix_losses']
    assert receipt['comparisons'][0]['reference_repeat_verified'] is True
    assert receipt['reference_repeat']['passed'] is True
    assert json.loads((tmp_path/'probe/PROBE.json').read_text())['status'] == 'PASS'


def test_live_child_not_admitted_as_validation(case, tmp_path):
    with pytest.raises(ValueError, match='explicit_non_science_validation_plan'):
        probe.run_probe(case.executor, [case.batch], longest(case), tmp_path/'probe')
    assert not (tmp_path/'probe').exists()


def test_probe_never_promotes_cpu_to_real_model(case, tmp_path):
    case.child.plan['r163_validation_only'] = True
    case.executor.execution_kind = 'EXTERNALLY_VALIDATED_EXECUTOR'
    with pytest.raises(ValueError, match='isolated_validation_learning_fork_only'):
        probe.run_probe(case.executor, [case.batch], longest(case), tmp_path/'probe')


def test_requires_full_configured_context(case, tmp_path):
    case.child.plan['r163_validation_only'] = True
    with pytest.raises(ValueError, match='test_actual_context_limit'):
        probe.run_probe(case.executor, [case.batch], case.batch, tmp_path/'probe')


def test_failure_preserves_receipt_and_initial_state(case, tmp_path):
    case.child.plan['r163_validation_only'] = True
    before = case.executor.snapshot()
    case.model.get_base_model().fail = True
    with pytest.raises(ValueError, match='finite_reference_loss'):
        probe.run_probe(case.executor, [case.batch], longest(case), tmp_path/'probe')
    receipt = json.loads((tmp_path/'probe/PROBE.json').read_text())
    assert receipt['status'] == 'FAIL' and receipt['state_restored'] is True
    assert receipt['real_7b_validated'] is False
    assert case.executor.snapshot() == before


def test_optimizer_update_mismatch_is_detected(case, tmp_path, monkeypatch):
    case.child.plan['r163_validation_only'] = True
    original = case.executor.update

    def changed(batch):
        result = original(batch)
        with case.child.torch.no_grad():
            next(iter(case.child.parameters.values())).add_(1)
        return result

    monkeypatch.setattr(case.executor, 'update', changed)
    before = case.executor.snapshot()
    with pytest.raises(AssertionError):
        probe.run_probe(case.executor, [case.batch], longest(case), tmp_path/'probe')
    assert case.executor.snapshot() == before
    receipt = json.loads((tmp_path/'probe/PROBE.json').read_text())
    assert receipt['status'] == 'FAIL'
    assert len(receipt['current_pair']['reference_losses']) == 5
    assert receipt['current_pair']['reference_rng_sha256'] == receipt['current_pair']['suffix_rng_sha256']
    assert receipt['current_pair']['gradients']


@pytest.mark.parametrize('corruption', ['gradient', 'rng'])
def test_reference_repeat_failure_precedes_suffix(case, tmp_path, monkeypatch, corruption):
    case.child.plan['r163_validation_only'] = True
    original = probe.full_label_update
    calls = []

    def changed(executor, batch):
        result = original(executor, batch)
        calls.append(batch.sha256)
        if len(calls) == 2:
            if corruption == 'gradient':
                next(iter(case.child.parameters.values())).grad.add_(1)
            else:
                case.child.torch.rand(1)
        return result

    def forbidden(batch):
        pytest.fail('suffix update must not run after failed full/full control')

    monkeypatch.setattr(probe, 'full_label_update', changed)
    monkeypatch.setattr(case.executor, 'update', forbidden)
    before = probe.saved_state(case.child)
    with pytest.raises((AssertionError, ValueError)):
        probe.run_probe(case.executor, [case.batch], longest(case), tmp_path/'probe')
    receipt = json.loads((tmp_path/'probe/PROBE.json').read_text())
    assert receipt['status'] == 'FAIL' and receipt['phase'] == 'REFERENCE_REPEAT'
    assert receipt['reference_repeat']['passed'] is False
    assert receipt['state_restored'] is True
    assert len(calls) == 2
    probe.compare_tree(case.child.torch, probe.saved_state(case.child), before, dict(atol=0, rtol=0))


@pytest.mark.parametrize('corruption', ['adapter_nan', 'moment_inf', 'wrong_step'])
def test_longest_invalid_post_update_cannot_be_restored_into_pass(case, tmp_path, monkeypatch, corruption):
    case.child.plan['r163_validation_only'] = True
    original = case.executor.update

    def changed(batch):
        result = original(batch)
        if batch.sha256 == 'd'*64:
            parameter = next(iter(case.child.parameters.values()))
            with case.child.torch.no_grad():
                if corruption == 'adapter_nan':
                    parameter.fill_(float('nan'))
                elif corruption == 'moment_inf':
                    case.child.optimizer.state[parameter]['exp_avg'].fill_(float('inf'))
                else:
                    case.child.optimizer.state[parameter]['step'].add_(1)
        return result

    monkeypatch.setattr(case.executor, 'update', changed)
    before = case.executor.snapshot()
    with pytest.raises(ValueError):
        probe.run_probe(case.executor, [case.batch], longest(case), tmp_path/'probe')
    assert case.executor.snapshot() == before
    receipt = json.loads((tmp_path/'probe/PROBE.json').read_text())
    assert receipt['status'] == 'FAIL' and receipt['real_7b_validated'] is False
    assert receipt['state_restored'] is True and receipt['executor_uncertain'] is True
    with pytest.raises(ValueError, match='uncertain_executor_never_retried'):
        case.executor.update(case.batch)
