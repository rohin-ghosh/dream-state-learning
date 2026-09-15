"""Operator-only audit of immutable terminal artifacts; no inference or dispatch."""

from collections import Counter
from contextlib import ExitStack
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import tarfile


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
CONTROL = ROOT.parent / 'orch_l2_shared_20260914_attempt1'
EXPECTED = {
    ROOT / 'FINAL_LONG_NATIVE.tar.gz': '8f770ed7602afc3121dfd2e4d03f4bd75e68b1e45a6e4f048cf3c676b4f93331',
    ROOT / 'FINAL_LONG_PROVIDER.tar.gz': '730c9fda9711cc6c18cdf9b1568ba715a3c0e46865c054f43abf7bcf26dce0df',
    ROOT / 'FINAL_CONTROL_PROVIDER_COST.tar.gz': '28a4e7c35af2a62d775456989f3bde0aefdfb297eef6b8f1c3f6eddebc8998d7',
    CONTROL / 'ORIGINAL_OWNED_TERMINAL_20260915.tar.gz': 'e18ee9d5102d8950921151ed546eac4ea583730b0385989223c4cc23c47a6278',
    CONTROL / 'ORIGINAL_OWNED_TERMINAL_20260915_SUMMARY.json': '6120ee1f4810385cbd29eddbf445dba0212590a3a668fd9accd8e0c635b945e1',
}


def file_hash(path):
    digest = sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def document_hash(value):
    return sha256(json.dumps(value, sort_keys=True, ensure_ascii=True,
                             allow_nan=False, separators=(',', ':')).encode('ascii')).hexdigest()


def raw(archive, name):
    if not hasattr(archive, '_long_buffers'):
        archive._long_buffers = {member.name: archive.extractfile(member).read()
                                 for member in archive if member.isfile()}
    return archive._long_buffers[name]


def read(archive, name):
    return json.loads(raw(archive, name))


def ledger(archive, name):
    rows = [json.loads(line) for line in raw(archive, name).splitlines()]
    assert [row['index'] for row in rows] == list(range(len(rows))), name
    return rows


def main():
    for path, expected in EXPECTED.items():
        assert file_hash(path) == expected, str(path)
    summary = json.loads((CONTROL / 'ORIGINAL_OWNED_TERMINAL_20260915_SUMMARY.json').read_text())
    specification = importlib.util.spec_from_file_location('long_envelope', REPO / 'gpu/orch_l2_long_envelope.py')
    envelope = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(envelope)
    terminal = json.loads((ROOT / 'FINAL_TERMINAL.json').read_text())
    release = json.loads((ROOT / 'FINAL_RELEASE_GPU1.json').read_text())
    assert terminal['status'] == 'COMPLETE'
    assert release['safe'] and release['clear'] and not release['owners']
    result = {
        'scope': 'OPERATOR_ONLY_TERMINAL_AUDIT_NEVER_PARENT_INPUT',
        'new_model_or_provider_calls': 0,
        'artifacts': {str(path.relative_to(REPO)): value for path, value in EXPECTED.items()},
        'terminal': terminal,
        'release': release,
        'stages': {},
        'long_provider_requests': [],
        'provider_accounting_exceptions': [],
        'controls': {},
    }
    with ExitStack() as stack:
        native = stack.enter_context(tarfile.open(ROOT / 'FINAL_LONG_NATIVE.tar.gz'))
        provider = stack.enter_context(tarfile.open(ROOT / 'FINAL_LONG_PROVIDER.tar.gz'))
        original = stack.enter_context(tarfile.open(ROOT / 'RESUME_ORIGINAL_001.tar.gz'))
        controls = stack.enter_context(tarfile.open(CONTROL / 'ORIGINAL_OWNED_TERMINAL_20260915.tar.gz'))
        control_costs = stack.enter_context(tarfile.open(ROOT / 'FINAL_CONTROL_PROVIDER_COST.tar.gz'))
        learner = ledger(native, 'CALLS_LONG.jsonl')
        logical = ledger(native, 'CALLS_PARENT_LONG.jsonl')
        reservations = ledger(provider, 'CALLS_PROVIDER_LONG.jsonl')
        assert len(learner) <= 1600 and len(reservations) <= 600
        original_calls = raw(original, 'CALLS_LONG.jsonl')
        assert len(original_calls.splitlines()) == 16
        assert raw(native, 'CALLS_LONG.jsonl').startswith(original_calls)
        assert raw(native, 'CALLS_PARENT_LONG.jsonl').startswith(raw(original, 'CALLS_PARENT_LONG.jsonl'))
        preserved = []
        for member in original.getmembers():
            if member.isfile() and (Path(member.name).name.startswith(('EPISODE_', 'CALL_'))):
                assert raw(original, member.name) == raw(native, member.name), member.name
                preserved.append(member.name)
        assert len([name for name in preserved if '/EPISODE_' in name]) == 4
        result['original_prefix'] = {'first_16_call_ledger_bytes_preserved': True,
                                     'unchanged_files': preserved}
        call_paths = [name for name in native.getnames() if Path(name).name.startswith('CALL_') and name.endswith('.json')]
        call_indexes = [read(native, name)['index'] for name in call_paths]
        assert sorted(call_indexes) == list(range(len(learner)))
        expected_state = 'e226cea230b4b970cd5a94cb2b853350aa8bfb95ab4ba69cba3e78ebdd0ad3bf'
        base = 'a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992'
        stage_order = [(0, 'readout')] + [(cycle, phase) for cycle in range(1, 4)
                                                     for phase in ('experience', 'sleep', 'readout')]
        for cycle, phase in stage_order:
            prefix = f'LONG/cycle{cycle}/{phase}'
            path = prefix + '/COMPLETE.json'
            complete = read(native, path)
            assert complete['status'] == 'COMPLETE'
            assert complete['input_adapter']['state_sha256'] == expected_state
            assert complete['input_adapter']['base_sha256'] == base
            stage = {'completion_sha256': sha256(raw(native, path)).hexdigest(),
                     'complete': {key: value for key, value in complete.items() if key not in ('admitted', 'gates')},
                     'admitted_row_sha256': [row['sha256'] for row in complete.get('admitted', [])],
                     'ledger_calls': sum(row['cycle'] == cycle and row['phase'] == phase for row in learner)}
            if phase == 'sleep':
                output = complete['output_adapter']
                assert output['base_sha256'] == base
                if cycle > 1:
                    assert complete['updates'] == 0 and complete['unchanged']
                    assert output == complete['input_adapter']
                for name, expected in output['files']:
                    relative = output['path'].split('/orch_l2_shared_20260914_attempt1/')[1] + '/' + name
                    assert sha256(raw(native, relative)).hexdigest() == expected
                expected_state = output['state_sha256']
            else:
                loaded = read(native, prefix + '/LOADED.json')['observed']
                assert loaded == complete['input_adapter']
                episodes = [read(native, f'{prefix}/EPISODE_{ordinal:02d}.json') for ordinal in range(1, 17)]
                assert sum(episode['correct'] for episode in episodes) == complete['successes']
                pairs = [episodes[index:index + 2] for index in range(0, 16, 2)]
                assert all(pair[0]['task']['events'] == pair[1]['task']['events'] and
                           pair[0]['task']['goal'] != pair[1]['task']['goal'] for pair in pairs)
                stage.update(both_goals_correct_pairs=sum(all(episode['correct'] for episode in pair) for pair in pairs),
                             pair_denominator=8, actor_calls=sum(episode['actor_calls'] for episode in episodes),
                             actual_reads=sum(len(episode['reads']) for episode in episodes),
                             actual_routes=sum(len(episode['routes']) for episode in episodes))
                if phase == 'readout':
                    assert all(not episode['parent_messages'] for episode in episodes)
                    for arm in ('SHORT', 'FROZEN', 'UNPARENTED'):
                        control_stage = summary['lanes'][arm]['cycles'][str(cycle)]['readout']
                        control_path = f'{arm}/cycle{cycle}/readout/COMPLETE.json'
                        assert sha256(raw(controls, control_path)).hexdigest() == control_stage['complete']['sha256']
                        for ordinal, episode in enumerate(episodes, 1):
                            twin = read(controls, f'{arm}/cycle{cycle}/readout/EPISODE_{ordinal:02d}.json')
                            assert episode['task'] == twin['task']
                        result['controls'].setdefault(arm, {})[str(cycle)] = {
                            'successes': control_stage['complete']['value']['successes'],
                            'both_goals_correct_pairs': control_stage['both_goals_correct_pairs'],
                            'completion_sha256': control_stage['complete']['sha256'],
                            'same_tasks_verified': True,
                        }
                else:
                    stage['distillation'] = read(native, prefix + '/PARENT_DISTILLATION.json')
            result['stages'][f'{cycle}_{phase}'] = stage
        for stage in terminal['stages']:
            assert stage['exit_code'] == 0
            assert stage['completion_sha256'] == result['stages'][f"{stage['cycle']}_{stage['phase']}"]['completion_sha256']
        request_names = sorted(name for name in provider.getnames() if name.endswith('.request.json'))
        assert len(request_names) == len(logical) == 17
        assert len(reservations) == 2 * len(request_names) == 34
        usage_totals = Counter()
        for request_name, entry in zip(request_names, logical):
            request = read(provider, request_name)
            identity = request['id']
            assert int(identity.split('_')[0]) == entry['index']
            assert request['payload']['kind'] == entry['kind']
            request_slots = [row for row in reservations if row['request_id'] == identity]
            assert Counter(row['component'] for row in request_slots) == Counter(['utility', 'evaluation'])
            assert all(row['pre_dispatch'] for row in request_slots)
            invocation = read(provider, identity + '/INVOCATION.json')
            assert invocation['attempts'] == 1 and invocation['tools'] == []
            assert max(row['reserved_unix'] for row in request_slots) <= invocation['started_unix']
            stdout = read(provider, identity + '/stdout.json')
            assert not stdout['permission_denials']
            assert len(stdout['modelUsage']) == 2
            for usage in stdout['modelUsage'].values():
                for key in ('inputTokens', 'outputTokens', 'cacheCreationInputTokens', 'cacheReadInputTokens', 'costUSD'):
                    usage_totals[key] += usage.get(key, 0)
            original_response_name = identity + '.response.json'
            recovered_name = identity + '.recovered.response.json'
            response_name = recovered_name if recovered_name in provider.getnames() else original_response_name
            response = read(provider, response_name)
            assert response['request_sha256'] == document_hash(request)
            if stdout['is_error']:
                assert identity in ('0004_LONG_C1', '0016_LONG_C3')
                assert stdout['num_turns'] == 4
                assert response['result']['error'] and response['result']['reviews'] == []
                result['provider_accounting_exceptions'].append({
                    'id': identity, 'reserved_slots': 2, 'reported_main_turns': stdout['num_turns'],
                    'turn_based_invocations_including_utility': stdout['num_turns'] + 1,
                    'error': stdout['result'], 'disposition': 'FAIL_CLOSED_EMPTY_REVIEWS_NO_RETRY',
                })
            else:
                assert stdout['num_turns'] == 1
                assert response['result'] == envelope.parse_json_envelope(stdout['result'])
            if response_name == recovered_name:
                recovery = response['recovery']
                assert recovery['provider_calls'] == 0
                assert recovery['original_response_sha256'] == sha256(raw(provider, original_response_name)).hexdigest()
                assert recovery['stdout_sha256'] == sha256(raw(provider, identity + '/stdout.json')).hexdigest()
                assert recovery['request_file_sha256'] == sha256(raw(provider, request_name)).hexdigest()
                assert recovery['invocation_sha256'] == sha256(raw(provider, identity + '/INVOCATION.json')).hexdigest()
            result['long_provider_requests'].append({
                'id': identity, 'kind': entry['kind'], 'slots': [row['index'] for row in request_slots],
                'request_file_sha256': sha256(raw(provider, request_name)).hexdigest(),
                'response_file_sha256': sha256(raw(provider, response_name)).hexdigest(),
                'recovered_without_dispatch': response_name == recovered_name,
                'reported_main_turns': stdout['num_turns'], 'is_error': stdout['is_error'],
                'duration_api_ms': stdout.get('duration_api_ms'), 'duration_ms': stdout.get('duration_ms'),
            })
        result['long_provider_usage'] = dict(usage_totals)
        counts = {'LONG': len(learner)}
        for arm in ('SOURCE', 'SHORT', 'FROZEN', 'UNPARENTED'):
            name = f'CALLS_{arm}.jsonl'
            rows = ledger(controls, name)
            assert sha256(raw(controls, name)).hexdigest() == summary['ledger_snapshot'][name]['sha256']
            counts[arm] = len(rows)
        provider_counts = {'LONG': len(reservations)}
        turn_counts = {'LONG': sum(item['reported_main_turns'] + 1 for item in result['long_provider_requests'])}
        for arm in ('SHORT', 'FROZEN'):
            name = f'CALLS_PROVIDER_{arm}.jsonl'
            rows = ledger(control_costs, name)
            assert len(rows) == 184
            provider_counts[arm] = len(rows)
            turn_counts[arm] = 0
            for identity in sorted({row['request_id'] for row in rows}):
                stdout = read(control_costs, identity + '/stdout.json')
                assert len(stdout['modelUsage']) == 2
                turn_counts[arm] += stdout['num_turns'] + 1
                if stdout['num_turns'] != 1:
                    result['provider_accounting_exceptions'].append({
                        'id': identity, 'reserved_slots': 2, 'reported_main_turns': stdout['num_turns'],
                        'turn_based_invocations_including_utility': stdout['num_turns'] + 1,
                        'is_error': stdout['is_error'], 'disposition': 'READ_ONLY_CONTROL_COST_DISCLOSURE',
                    })
        total = sum(counts.values()) + sum(turn_counts.values())
        assert total <= 8648 <= 20000
        result['accounting'] = {'learner_source': counts, 'provider_reserved_slots': provider_counts,
                                'provider_cli_turn_based_invocations': turn_counts,
                                'batch_cli_turn_based_invocations': total,
                                'batch_reservations': sum(counts.values()) + sum(provider_counts.values()),
                                'network_attempts': 'NOT_INDEPENDENTLY_EXPOSED_DO_NOT_CLAIM_EXACT_WIRE_CALLS',
                                'pre_dispatch_provider_reservation_complete': False, 'batch_ceiling': 8648,
                                'logical_long_requests_not_added_again': len(logical),
                                'long_kind_counts': dict(Counter(row['kind'] for row in logical)),
                                'long_ledger_sha256': sha256(raw(native, 'CALLS_LONG.jsonl')).hexdigest()}
        result['shared_identity'] = {name: sha256(raw(controls, name)).hexdigest()
                                     for name in ('COHORT.json', 'SOURCE.json')}
        assert result['shared_identity']['SOURCE.json'] == '6f5f8811c28bc3ccee94232d628a246f70b604e7ea70be746e3e09536553627d'
        assert result['shared_identity']['COHORT.json'] == '8cd5a0f85ca8cb20a1d96b47e267debd580bb260e0c4ed5a5d7999a2481a5c5c'
        result['deadline'] = raw(native, 'DEADLINE').decode()
        assert float(result['deadline']) == 1789472611.845884
        assert terminal['finished_unix'] < float(result['deadline'])
        assert terminal['assigned_gpu_hours'] <= 12
        result['final_adapter_state_sha256'] = expected_state
    (ROOT / 'FINAL_AUDIT.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'status': 'RECONCILED_WITH_PROVIDER_ACCOUNTING_EXCEPTIONS',
                      'stages': len(result['stages']), 'accounting': result['accounting'],
                      'held': [result['stages'][f'{cycle}_readout']['complete']['successes'] for cycle in range(4)],
                      'pairs': [result['stages'][f'{cycle}_readout']['both_goals_correct_pairs'] for cycle in range(4)]}, indent=2))


if __name__ == '__main__':
    main()
