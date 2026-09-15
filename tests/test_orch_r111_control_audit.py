import json

import pytest

from gpu import orch_r111_control_audit as audit


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


@pytest.fixture
def control(tmp_path):
    root = tmp_path/'canonical'
    put(root/'COHORT.json', dict(fixture=True))
    put(root/'PREPARE.json', dict(caps=dict(cycles=2), inputs={'COHORT.json': audit.sha(root/'COHORT.json')},
        source_files={name: 'fixture_source_hash' for name in audit.SOURCES}))
    model = root/'adapter'/'adapter_model.safetensors'
    model.parent.mkdir()
    model.write_bytes(b'fixture_saved_adapter')
    adapter = dict(path=str(model.parent), files=[[model.name, audit.sha(model)]], state_sha256='a'*64,
                   base_sha256='b'*64)
    base = dict(kind='FROZEN_QWEN_BASE_NO_ADAPTER', path=None, files=[], state_sha256='b'*64, base_sha256='b'*64)
    for index, arm in enumerate(audit.ARMS):
        identity = base if arm == 'NO_LORA' else adapter
        put(root/f'DISPATCH_{arm}.json', dict(pid=2147483647, physical_index=index))
        put(root/(arm+'_GUARD')/'COMPLETE.json', dict(status='COMPLETE', finished_unix=10))
        for cycle in (0, 1):
            folder = root/arm/f'cycle{cycle}'
            if cycle:
                put(folder/'sleep/COMPLETE.json', dict(input_adapter=identity, output_adapter=identity,
                    updates=0 if arm == 'NO_LORA' else 4 if arm == 'GUIDED' else 8,
                    fits=0 if arm == 'NO_LORA' else 1, process=['boot', 1, cycle], finished_unix=5))
            put(folder/'readout/COMPLETE.json', dict(input_adapter=identity, parent_free=True,
                process=['boot', 2, cycle], successes=1, all_episode_count=2, world_denominator=1, finished_unix=6))
            put(folder/'readout/LOADED.json', dict(observed=identity, parent_present=False))
            for task in range(2):
                put(folder/'readout'/f'EPISODE_{task}.json', dict(task={'cycle': cycle, 'task': task},
                    private_raw_fixture='must_not_export'))
    return root


def test_one_matched_control_triple_and_gaps_without_raw_export(control):
    before = {path: path.read_bytes() for path in control.rglob('*') if path.is_file()}
    result = audit.audit(control)
    assert result['cohort_matches_prepared'] is True
    assert [row['cycle'] for row in result['matched_cycles']] == [0, 1]
    assert result['matched_cycles'][1]['post_sleep_joins_verified'] is True
    assert result['matched_saved_updates'] == dict(GUIDED=4, UNPARENTED=8, NO_LORA=0)
    assert result['comparability']['no_lora_is_frozen_base_not_adapter_matched_twin'] is True
    assert result['comparability']['guided_unparented_realized_update_doses_equal'] is False
    assert result['adjacent_readout_task_overlaps'] == [0]
    assert 'must_not_export' not in json.dumps(result)
    assert all(path.read_bytes() == value for path, value in before.items())


def test_zero_update_sleep_is_not_hidden_or_counted_as_new_learning(control):
    path = control/'GUIDED/cycle1/sleep/COMPLETE.json'
    value = json.loads(path.read_bytes())
    value.update(updates=0, fits=0, reason='NO_VALID_REFLECTIONS')
    put(path, value)
    result = audit.audit(control)
    assert result['matched_saved_updates']['GUIDED'] == 0
    assert result['arms']['GUIDED']['cycles'][1]['sleep']['same_child'] is True
    assert result['arms']['GUIDED']['cycles'][1]['sleep']['reason'] == 'NO_VALID_REFLECTIONS'


def test_readout_from_wrong_checkpoint_fails_join_without_fixing_artifacts(control):
    path = control/'GUIDED/cycle1/readout/LOADED.json'
    value = json.loads(path.read_bytes())
    value['observed']['state_sha256'] = 'wrong'
    put(path, value)
    assert audit.audit(control)['matched_cycles'][1]['post_sleep_joins_verified'] is False


def test_tampered_saved_weights_and_cohort_are_reported(control):
    (control/'adapter/adapter_model.safetensors').write_bytes(b'changed')
    put(control/'COHORT.json', dict(changed=True))
    result = audit.audit(control)
    assert result['cohort_matches_prepared'] is False
    assert result['initial']['GUIDED']['saved_files_verified'] is False


def test_unmatched_later_readout_is_not_added_to_matched_result(control):
    previous = control/'UNPARENTED/cycle1/readout'
    later = control/'UNPARENTED/cycle2/readout'
    for path in previous.iterdir():
        put(later/path.name, json.loads(path.read_bytes()))
    result = audit.audit(control)
    assert result['arms']['UNPARENTED']['latest_readout_cycle'] == 2
    assert [row['cycle'] for row in result['matched_cycles']] == [0, 1]


def test_conflicting_terminals_are_not_silently_promoted(control):
    folder = control/'GUIDED/cycle1/readout'
    put(folder/'FAILED.json', dict(error='private_fixture', error_type='ValueError'))
    result = audit.audit(control)
    assert result['arms']['GUIDED']['cycles'][1]['phases']['readout']['status'] == 'CONFLICTING_TERMINALS'
    assert [row['cycle'] for row in result['matched_cycles']] == [0]
