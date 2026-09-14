from copy import deepcopy

import pytest

from organism_v6 import orch_replication as replica


def answer(raw):
    return dict(raw=raw, terminal=True, truncated=False)


def source_actor(messages):
    public = messages[-1]['content']
    if public.startswith('EXPOSURE TASK'):
        port = next(line[6:] for line in public.splitlines() if line.startswith('PORTS '))
        return answer('ROUTE ' + port)
    raise ValueError('deliberately_missing_generated_record')


def oracle(world, task):
    ports = [edge['port'] for edge in world['edges'] if edge['node'] == task['node']
             and any(second['node'] == edge['outcome'] and second['outcome'] == task['goal']
                     for second in world['edges'])]
    first = next(edge for edge in world['edges'] if edge['port'] == ports[0])
    second = next(edge for edge in world['edges'] if edge['node'] == first['outcome'])
    outputs = iter([answer('ROUTE ' + first['port']), answer('ROUTE ' + second['port'])])
    return lambda messages: next(outputs)


def test_fixed_worlds_and_namespace_exclusion():
    frozen = replica.cohort()
    assert len(frozen['worlds']) == 8
    assert frozen['pair_denominator'] == 16 and frozen['goal_denominator'] == 32
    for world in frozen['worlds']:
        assert replica.tasks(world) == replica.runtime(world['master'])['build_tasks'](world)
    collision = frozen['worlds'][0]['edges'][0]['event']
    with pytest.raises(ValueError, match='collision'):
        replica.cohort([collision])


def test_collection_failures_stay_in_denominators():
    frozen = replica.cohort()
    document = replica.collect(frozen, source_actor, lambda name, value: None)
    assert document['accepted_events'] == 0
    assert document['event_denominator'] == 32 and document['model_calls'] == 64
    assert len(document['collections']) == 8
    assert replica.verify_source(frozen, document) == {}
    assert all(not item['ready'] for item in document['collections'])


def test_no_invented_source_store():
    frozen = replica.cohort()
    document = replica.collect(frozen, source_actor, lambda name, value: None)
    document['store']['invented'] = 'EVENT invented'
    document['store_sha256'] = replica.digest(document['store'])
    with pytest.raises(ValueError, match='source_raw_bytes'):
        replica.verify_source(frozen, document)


def test_reference_individual_and_pair_denominators():
    result = replica.evaluate(replica.cohort(), {}, replica.first_port, lambda name, value: None)
    assert result['goals'] == 16 and result['goal_denominator'] == 32
    assert result['pairs'] == 0 and result['pair_denominator'] == 16


def test_correct_transitions_count_both_opposite_goals():
    world = replica.cohort()['worlds'][0]
    records = [replica.episode(world, task, oracle(world, task), {}) for task in replica.tasks(world)]
    assert replica.summarize(world, records)['pairs'] == 2
    records[0]['routes'][1]['destination'] = 'forged'
    with pytest.raises(ValueError, match='score_disagrees'):
        replica.summarize(world, records)


def test_supplied_text_is_only_served_when_read():
    world = replica.cohort()['worlds'][0]
    task = replica.tasks(world)[0]
    generated = iter([answer('READ EVENT ' + task['events'][0]), answer('not a command')])
    episode = replica.episode(world, task, lambda messages: next(generated), {task['events'][0]: 'ACTUAL CHILD BYTES\n'})
    assert episode['reads'] == [dict(address=task['events'][0], raw='ACTUAL CHILD BYTES\n')]
    assert 'ACTUAL CHILD BYTES' not in str(episode['captures'][0]['messages'])
    assert episode['captures'][1]['messages'][-1]['content'] == 'MEMORY RESULT\nACTUAL CHILD BYTES\n'


def test_missing_address_response_and_duplicate_failure():
    world = replica.cohort()['worlds'][0]
    task = replica.tasks(world)[0]
    response = answer('READ EVENT ' + task['events'][0])
    record = replica.episode(world, task, lambda messages: response, {})
    assert record['reads'][0]['raw'] == replica.UNAVAILABLE
    assert record['actor_calls'] == 2 and record['terminal_reason'] == 'invalid_or_duplicate_read'
    assert not record['correct']


@pytest.mark.parametrize('raw', ['ROUTE invented', 'ROUTE x\nROUTE y', ' READ EVENT x', 'MISS'])
def test_malformed_commands_fail_without_retry(raw):
    world = replica.cohort()['worlds'][0]
    record = replica.episode(world, replica.tasks(world)[0], lambda messages: answer(raw), {})
    assert record['actor_calls'] == 1 and not record['correct']


def test_truncated_generation_fails():
    world = replica.cohort()['worlds'][0]
    task = replica.tasks(world)[0]
    record = replica.episode(world, task, lambda messages: dict(raw='ROUTE '+task['ports'][0], terminal=False, truncated=True), {})
    assert not record['routes'] and record['terminal_reason'] == 'generation_failure'


def test_six_turn_bound_with_four_reads_and_two_routes():
    world = replica.cohort()['worlds'][0]
    task = replica.tasks(world)[0]
    route_actor = oracle(world, task)
    outputs = iter([answer('READ EVENT ' + address) for address in task['events']])

    def actor(messages):
        return next(outputs, None) or route_actor(messages)

    record = replica.episode(world, task, actor, {})
    assert record['correct'] and record['actor_calls'] == 6 and len(record['reads']) == 4


def test_all_generation_failures_still_have_fixed_denominators():
    def fail(messages):
        raise RuntimeError('simulated')

    result = replica.evaluate(replica.cohort(), {}, fail, lambda name, value: None)
    assert (result['pairs'], result['pair_denominator'], result['goals'], result['goal_denominator']) == (0, 16, 0, 32)


def test_matched_comparison_requires_all_three_sources():
    reference = replica.evaluate(replica.cohort(), {}, replica.first_port, lambda name, value: None)
    common = dict(status='COMPLETE', routing=reference, retention={}, audit={}, model_calls=64,
                  adapter_state_before='example', cohort_sha256='cohort', store_sha256='source',
                  protocol_sha256='protocol', prepare_sha256='prepare', source_commit='commit')
    results = {state: deepcopy(common) for state in replica.STATES}
    assert replica.compare(results, reference)['full_minus_off_pairs'] == 0
    results['FULL_TARGET']['store_sha256'] = 'other'
    with pytest.raises(ValueError, match='unmatched_store'):
        replica.compare(results, reference)


def test_call_arithmetic():
    assert replica.CALL_CAP == 32 * 6 + 16 * 2 + 16
    assert replica.SOURCE_CAP + 3 * replica.CALL_CAP == 784


def test_guard_lease_and_gpu_mapping():
    from gpu import orch_replication_guard as guardian
    from datetime import datetime, timezone

    assert guardian.LEASE_CUTOFF == datetime(2026, 9, 19, 21, 3, tzinfo=timezone.utc).timestamp()
    assert {device[0] for device in guardian.DEVICES.values()} == {0, 1, 5}


@pytest.mark.parametrize('memory,owners,safe', [('1', [], True), ('3', [], False),
                                              ('1', [['uuid', '123', '1']], False)])
def test_guard_never_admits_occupied_gpu(monkeypatch, memory, owners, safe):
    from gpu import orch_replication_guard as guardian

    monkeypatch.setattr(guardian, 'query', lambda fields, kind: [['0', 'uuid', memory]] if kind == 'gpu' else owners)
    monkeypatch.setattr(guardian.Path, 'iterdir', lambda path: iter(()))
    assert guardian.scan(0, 'uuid')['safe'] is safe


def test_guard_rejects_physical_uuid_change(monkeypatch):
    from gpu import orch_replication_guard as guardian

    monkeypatch.setattr(guardian, 'query', lambda fields, kind: [['0', 'other_uuid', '1']])
    with pytest.raises(ValueError, match='physical_uuid_changed'):
        guardian.scan(0, 'uuid')
