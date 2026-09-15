import json
from pathlib import Path

import pytest

from gpu import orch_r108_guided_run as runner
from organism_v6 import orch_r107_capability as capability


def test_capability_condition_normalizes_without_confusing_training_mask_control():
    task = capability.tasks()[0]
    response = dict(messages=capability.messages(task), raw='"abs(left-right)"', token_ids=[5, 6],
        prompt_tokens=10, terminal=True, truncated=False, requested_generation_cap=512,
        effective_generation_cap=512, context_limit=16384)
    for condition, arm in [('LORA_ON', 'ON'), ('LORA_OFF', 'OFF')]:
        record = runner.capability_capture(task, condition, response, 'a' * 64)
        assert record['arm'] == arm and record['lora_enabled'] == (arm == 'ON')
    with pytest.raises(ValueError, match='known_capability_condition'):
        runner.capability_capture(task, 'NEW_LABELS_MASKED', response, 'a' * 64)


def test_source_reference_cannot_escape(tmp_path):
    with pytest.raises(ValueError, match='source_call_relative'):
        runner.source_row(tmp_path, dict(source_call_path='../foreign.json'))


def test_parent_native_caps_are_separate_and_no_failed_reservation_refund(tmp_path):
    for index in range(4):
        assert runner.spend(tmp_path, 'PARENT', dict(id=str(index))) == index + 1
    with pytest.raises(ValueError, match='lifetime_call_cap'):
        runner.spend(tmp_path, 'PARENT', dict(id='retry'))
    assert runner.spend(tmp_path, 'NATIVE', dict(id='readout')) == 1
    entries = [json.loads(line) for line in (tmp_path / 'RESERVATIONS.jsonl').read_text().splitlines()]
    assert len(entries) == 5


@pytest.mark.parametrize('cycle,phase,generation,expected', [
    (1, 'collection', 0, 'INITIAL.json'), (1, 'sleep', 0, 'INITIAL.json'),
    (1, 'readout', 1, 'cycle1/sleep/carry/CARRY.json'),
    (2, 'collection', 1, 'cycle1/sleep/carry/CARRY.json'),
    (2, 'sleep', 1, 'cycle1/sleep/carry/CARRY.json'),
    (2, 'readout', 2, 'cycle2/sleep/carry/CARRY.json')])
def test_exact_phase_to_inherited_seed_join(tmp_path, monkeypatch, cycle, phase, generation, expected):
    path = tmp_path / expected
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(generation=generation, proof=expected)))
    monkeypatch.setattr(runner.seed, 'validate', lambda document: document)
    assert runner.input_seed(tmp_path, cycle, phase)['proof'] == expected
    path.write_text(json.dumps(dict(generation=99)))
    with pytest.raises(ValueError, match='exact_sleep_generation'):
        runner.input_seed(tmp_path, cycle, phase)


def test_all_held_and_capability_calls_fit_declared_single_lifetime():
    assert runner.NATIVE_CAP == 2 * (2 * 3 + 8 + len(capability.tasks()) * 2)
    assert runner.PARENT_CAP == 2 * 2
