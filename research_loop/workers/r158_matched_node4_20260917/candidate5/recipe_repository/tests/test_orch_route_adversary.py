from copy import deepcopy

import pytest

from organism_v6 import orch_route_adversary as probe


def collection(missing=False):
    world = probe.hop.build_world()
    records = []
    for index, edge in enumerate(world['edges']):
        raw = ('EVENT {event} AT {node} DID {port} GOT {outcome} EVIDENCE {receipt}').format(**edge)
        records.append(dict(edge=deepcopy(edge), accepted=not (missing and index == 3), event=dict(raw=raw)))
    return dict(world=world, records=records, collection_sha256='fixture_not_native')


def test_display_only_changes_ports_and_swap_only_changes_sources():
    original = collection()
    frozen = deepcopy(original)
    cases = {condition: probe.build_case(original, probe.SEEDS[0], condition, 0) for condition in probe.CONDITIONS}
    reference, display, swap = [cases[name] for name in probe.CONDITIONS[:3]]
    assert original == frozen
    assert reference['store'] == display['store']
    assert reference['task']['events'] == display['task']['events']
    assert reference['task']['ports'] == display['task']['ports'][::-1]
    assert reference['task'] == swap['task']
    assert reference['expected_first_port'] != swap['expected_first_port']
    assert len(swap['transformations']) == 2


@pytest.mark.parametrize('condition', probe.CONDITIONS)
def test_missing_source_never_repaired(condition):
    case = probe.build_case(collection(True), probe.SEEDS[2], condition, 1)
    assert len(case['original_missing_addresses']) == 1
    assert all(case['store'][address] == probe.UNAVAILABLE for address in case['original_missing_addresses'])
    assert not case['route_sources_available']


def test_oracle_and_first_port_control_separate_causal_switch():
    results, controls = [], []
    for seed in probe.SEEDS:
        for condition in probe.CONDITIONS:
            for goal in (0, 1):
                case = probe.build_case(collection(), seed, condition, goal)
                calls = []

                def oracle(messages):
                    port = case['expected_first_port'] if not calls else next(
                        edge['port'] for edge in case['world']['edges'] if edge['node'] == next(
                            first['outcome'] for first in case['world']['edges']
                            if first['port'] == case['expected_first_port']))
                    calls.append(port)
                    return dict(raw='ROUTE ' + port, terminal=True, truncated=False)

                results.append(probe.run_case(case, oracle))
                controls.append(probe.first_available_reference(case))
    summary = probe.summarize(results)
    control = probe.summarize(controls)
    assert sum(item['native_calls'] for item in results) == 48
    assert summary['paired_interventions']['causal_switch_correct'] == 6
    assert control['paired_interventions']['causal_switch_correct'] == 0
    assert control['paired_interventions']['display_invariant_correct'] == 0
    assert control['REFERENCE']['both_goal_pairs_correct'] == 0
    assert summary['UNAVAILABLE']['unsupported_commits'] == 6


def test_native_failure_is_retained_not_retried():
    case = probe.build_case(collection(), probe.SEEDS[0], 'REFERENCE', 0)

    def broken(messages):
        raise RuntimeError('deliberate_test_failure')

    result = probe.run_case(case, broken)
    assert result['native_calls'] == 1
    assert result['native'][0]['error']['message'] == 'deliberate_test_failure'
    assert not result['first_correct']
    assert not result['complete_correct']


def test_duplicate_or_incomplete_results_rejected():
    with pytest.raises(ValueError):
        probe.summarize([])


def test_unreadable_unknown_process_fails_closed(tmp_path):
    from gpu import orch_route_adversary as driver

    path = tmp_path / '123'
    with pytest.raises(ValueError, match='unreadable_process_not_bound_service'):
        driver.verify_service(path, dict(pid=123), 1, {})


def test_bound_service_requires_exact_identity_and_bytes(tmp_path):
    from gpu import orch_route_adversary as driver

    path = tmp_path / '123'
    path.mkdir()
    identity = dict(pid=123, start_ticks=1)
    entry = dict(identity=identity, ppid=1)
    for name in ('comm', 'cmdline', 'cgroup'):
        (path / name).write_text('fixture_' + name)
        entry[name + '_sha256'] = driver.source.file_hash(path / name)
    driver.verify_service(path, identity, 1, {123: entry})
    with pytest.raises(ValueError, match='unreadable_process_not_bound_service'):
        driver.verify_service(path, dict(identity, start_ticks=2), 1, {123: entry})
    (path / 'cmdline').write_text('drift')
    with pytest.raises(ValueError, match='service_identity_bytes_drift'):
        driver.verify_service(path, identity, 1, {123: entry})
