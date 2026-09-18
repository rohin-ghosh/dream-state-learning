"""Non-material Main response compatibility and one logged prepublication retry."""

import argparse
import ast
import copy
import importlib
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import types

import metadata_rebind as metadata
import takeover as base
from takeover import HERE, REPO, require, read, write, sha, reference

STATE = HERE / 'response_compat_v1'
ADAPTER_SHA = 'a0f8d74530b558724a8b5636a5b53556abd21267c316d94b3beeb08cd41c61a1'
METADATA_SHA = '2b278daeaadd84a16fe6589ab9b0b6f45335300db252f56a47711e194100760f'
FAILURES = {0: 'parent_000000000135', 4: 'parent_000000000126'}


def retry_candidate(physical, folder, state, memory_state):
    if physical not in FAILURES or (folder / 'TECHNICAL_RETRY_ONCE.json').exists():
        return None
    if not state['caught_up'] or memory_state['awaiting_render']:
        return None
    failed = HERE / 'parents' / ('physical' + str(physical)) / 'parent' / FAILURES[physical]
    result, source = read(failed / 'RESULT.json'), read(failed / 'SOURCE.json')
    require(result['status'] in ('PROVIDER_FAILED', 'VALIDATION_FAILED'), 'documented_prepublication_failure')
    require(result['source_sha256'] == sha(failed / 'SOURCE.json'), 'failed_source_pin')
    require(not (failed / 'PUBLISH_INTENT.json').exists(), 'never_replay_publication_intent')
    require(source['journal_id'] == state['journal_id'], 'same_retry_life')
    require(state['response_count'] >= source['response_count'], 'no_retry_counter_rewind')
    require(state['response_count'] >= memory_state['last_response_count'], 'preserve_retry_memory_cursor')
    for root in (HERE, metadata.STATE, STATE):
        for attempt in (root / 'parents' / ('physical' + str(physical)) / 'parent').glob('parent_*'):
            require((attempt / 'RESULT.json').exists(), 'unfinished_attempt_no_corrective_call')
            receipt = read(attempt / 'RESULT.json')
            require(receipt['status'] in ('PROVIDER_FAILED', 'VALIDATION_FAILED', 'SILENT', 'PUBLISHED'), 'unknown_publication_no_corrective_call')
            if receipt['status'] == 'PUBLISHED' or (attempt / 'PUBLISH_INTENT.json').exists():
                return None
    return dict(failed_result=reference(failed / 'RESULT.json'), failed_source=reference(failed / 'SOURCE.json'))


def corrective_dispatch(policy):
    function = ast.parse(inspect.getsource(policy.tick)).body[0]
    starts = [index for index, statement in enumerate(function.body)
              if isinstance(statement, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'directory' for target in statement.targets)]
    require(len(starts) == 1, 'one_exact_dispatch_boundary')
    function.name = 'corrective_dispatch'
    function.args.args += [ast.arg(arg='memory_state'), ast.arg(arg='status')]
    function.body = function.body[starts[0]:]
    function.body[0].value = ast.parse('Path(output) / ("parent_%012d_technicalretry_1" % state["request_count"])', mode='eval').body
    module = ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[]))
    namespace = dict(policy.__dict__)
    exec(compile(module, policy.__file__ + ':authorized_technical_retry', 'exec'), namespace)
    return namespace['corrective_dispatch']


def runtime(physical, config_path):
    require(sha(HERE / 'metadata_rebind.py') == METADATA_SHA, 'immutable_metadata_runtime')
    require(sha(STATE / 'orch_r175_parent_response.py') == ADAPTER_SHA, 'exact_Main_response_adapter')
    parent, provider, config, helper = metadata.runtime(physical, config_path)
    require(sha(__file__) == config['response_wrapper']['sha256'], 'immutable_response_wrapper')
    adapter = base.load_file(STATE / 'orch_r175_parent_response.py', 'node3_Main_response_compat')
    policy = importlib.import_module('gpu.orch_r166_parent_policy')
    strict_parser = provider.response_schema
    provider.response_schema = adapter.compatible_parser(strict_parser)
    policy.community.response_schema = provider.response_schema
    strict_tick = policy.tick
    dispatch = corrective_dispatch(policy)
    folder = Path(config_path).parent

    def tick(repository, current_config, output, seed, state):
        policy.validate(current_config)
        if not state['caught_up']:
            return strict_tick(repository, current_config, output, seed, state)
        memory_state = policy.memory(seed, policy.local_attempts(output), state)
        policy.bind_watcher_audits(memory_state, current_config.get('watcher_audits', []), state)
        candidate = retry_candidate(physical, folder, state, memory_state)
        if candidate is None:
            return strict_tick(repository, current_config, output, seed, state)
        require(time.time() < current_config['hard_end_unix'], 'unchanged_retry_stop')
        directory = Path(output) / ('parent_%012d_technicalretry_1' % state['request_count'])
        require(not directory.exists(), 'fresh_technical_attempt_directory')
        write(folder / 'TECHNICAL_RETRY_ONCE.json', dict(candidate, status='AUTHORIZED_ONE_CORRECTIVE_CALL_RESERVED',
            authorizing_directive='Main: one corrective call after known pre-publication failure, no new child wait',
            attempt_directory=str(directory), source_response_count=state['response_count'], source_request_count=state['request_count'],
            source_head_sha256=state['head_sha256'], adapter=reference(STATE / 'orch_r175_parent_response.py'),
            wrapper=reference(__file__), strict_policy=reference(policy.__file__), counters_reset=False, at_unix=time.time()))
        status = dict(memory=memory_state, observed_unix=time.time(), journal_head=state['head_sha256'])
        return dispatch(repository, current_config, output, seed, state, memory_state, status)

    policy.tick = tick
    return parent, provider, config, helper


def prepare():
    require(sha(REPO / 'gpu/orch_r175_parent_response.py') == ADAPTER_SHA, 'released_Main_adapter')
    require(sha(HERE / 'metadata_rebind.py') == METADATA_SHA, 'released_metadata_wrapper')
    write(STATE / 'orch_r175_parent_response.py', (REPO / 'gpu/orch_r175_parent_response.py').read_text())
    for physical in base.PHYSICALS:
        old = metadata.STATE / 'parents' / ('physical' + str(physical))
        new = STATE / 'parents' / ('physical' + str(physical))
        config = copy.deepcopy(read(old / 'CONFIG.json'))
        config.update(predecessor_output=str(old / 'parent'), predecessor_started_sha256=sha(old / 'parent/STARTED.json'),
                      response_adapter=reference(STATE / 'orch_r175_parent_response.py'), response_wrapper=reference(__file__),
                      repair_label='NONMATERIAL_LOSSLESS_RATIONALE_OBJECT_COMPATIBILITY',
                      unchanged_strict_decision=True, technical_retry_limit=1 if physical in FAILURES else 0)
        write(new / 'CANDIDATE_CONFIG.json', config)
    write(STATE / 'DIRECTIVE.json', dict(status='NONMATERIAL_REPAIR', adapter_sha256=ADAPTER_SHA,
        scope='NODE3_PARENT_PRIVATE_ONLY', same_latest_source_retry='ONE_AFTER_DOCUMENTED_PREPUBLICATION_FAILURE_ONLY',
        validators_relaxed=False, child_restarts=0, stop_unix=base.HARD_END, peer_service='NOT_OPERATIONAL'))
    print(json.dumps(dict(status='RESPONSE_COMPAT_CANDIDATES_READY_NO_SIGNALS')))


def preflight(physical, final=False):
    folder = STATE / 'parents' / ('physical' + str(physical))
    path = folder / ('CONFIG.json' if final else 'CANDIDATE_CONFIG.json')
    parent, provider, config, helper = runtime(physical, path)
    policy = importlib.import_module('gpu.orch_r166_parent_policy')
    require(policy.community.response_schema is provider.response_schema, 'both_actual_parser_references_bound')
    details = dict(object_id='unchanged_id', source_records=[], disposition='continue', next_task=None,
                   perception=dict(record_index=1, record_sha256='0' * 64, quote='exact quote'), credit=None, relapse_credit_id=None)
    response = dict(speak=True, message='Keep the exact message unchanged.', rationale=details)
    parsed = provider.response_schema(json.dumps(response))
    require(json.loads(parsed['rationale']) == details and parsed['message'] == response['message'], 'lossless_rationale_object_only')
    require(provider.response_schema(json.dumps(parsed)) == parsed, 'string_rationale_unchanged')
    for bad in [None, [], 1, True]:
        try:
            provider.response_schema(json.dumps(dict(response, rationale=bad)))
        except ValueError:
            pass
        else:
            raise ValueError('invalid_rationale_type_must_still_fail')
    maximum = config['r175_word_limit']
    provider.response_schema(json.dumps(dict(parsed, message=' '.join(['word'] * maximum))))
    try:
        provider.response_schema(json.dumps(dict(parsed, message=' '.join(['word'] * (maximum + 1)))))
    except ValueError:
        pass
    else:
        raise ValueError('unchanged_bound_arm_cap')
    state = dict(events=[], delivered={}, journal_id='CPU', split='TRAIN', response_count=100, request_count=100,
                 sleep_count=0, caught_up=True, head_sha256='0' * 64)
    seed = dict(journal_id='CPU', object_delivered_turns={}, last_response_count=100, last_request_count=100,
                prospective_request_count=100, credits={}, grammar_delivered=False, attempts=[])
    memory_state = policy.memory(seed, [], state)
    instruction, payload = policy.prompt(config, state, memory_state)
    require('MUST be JSON null' in instruction and '[a-z0-9]' in instruction, 'Main_errata_still_bound')
    require('not been verified' in ' '.join(instruction.split()), 'honest_executable_task_constraint')
    require(config['hard_end_unix'] == base.HARD_END and config['schedule_on'] == 'response', 'clock_and_stop_unchanged')
    require(config['cadence_responses'] == base.release()[1][physical]['cadence'], 'frozen_cadence')
    details['object_id'] = 'UpperCase'
    normalized = provider.response_schema(json.dumps(dict(response, rationale=details)))
    require(json.loads(normalized['rationale'])['object_id'] == 'UpperCase', 'never_autonormalize_object_ids')
    try:
        policy.decision(normalized, state, memory_state)
    except ValueError:
        pass
    else:
        raise ValueError('strict_later_decision_must_reject')
    return dict(status='RESPONSE_COMPAT_CPU_PASS', physical=physical, parser_reference_identity=True,
        arm=config['r175_arm'], word_cap=maximum, cadence=config['cadence_responses'],
        adapter=reference(STATE / 'orch_r175_parent_response.py'), strict_policy=reference(policy.__file__),
        exact_errata_sha256=metadata.ERRATA_SHA, config=reference(path), wrapper=reference(__file__),
        provider_calls=0, validators_unchanged=True, child_signals=0)


def rebind(physical):
    require(sha(HERE / 'metadata_rebind.py') == METADATA_SHA, 'immutable_quiet_handoff')
    function = ast.parse(inspect.getsource(metadata.rebind)).body[0]
    replacements = 0
    for statement in function.body:
        if isinstance(statement, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'old' for target in statement.targets):
            statement.value = ast.parse("metadata.STATE / 'parents' / ('physical' + str(physical))", mode='eval').body
            replacements += 1
    require(replacements == 1, 'exact_current_predecessor_not_initial_parent')
    namespace = dict(metadata.__dict__, STATE=STATE, metadata=metadata, runtime=runtime, preflight=preflight,
                     __file__=str(Path(__file__).resolve()))
    exec(compile(ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[])), __file__ + ':quiet_handoff', 'exec'), namespace)
    receipt = namespace['rebind'](physical)
    receipt.update(response_adapter_sha256=ADAPTER_SHA, status='RESPONSE_COMPAT_PARENT_STARTED_NOT_DELIVERY')
    write(STATE / 'parents' / ('physical' + str(physical)) / 'RESPONSE_ADAPTER_REBIND_RECEIPT.json', receipt)
    return receipt


def serve(physical):
    require(sha(HERE / 'metadata_rebind.py') == METADATA_SHA, 'immutable_service_body')
    namespace = dict(metadata.__dict__, STATE=STATE, runtime=runtime, __file__=str(Path(__file__).resolve()))
    types.FunctionType(metadata.serve.__code__, namespace, 'serve')(physical)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('prepare', 'preflight', 'rebind', 'serve'))
    parser.add_argument('--physical', type=int, choices=base.PHYSICALS)
    parser.add_argument('--final', action='store_true')
    args = parser.parse_args()
    if args.action == 'prepare':
        prepare()
    elif args.action == 'preflight':
        print(json.dumps(preflight(args.physical, args.final), sort_keys=True))
    elif args.action == 'rebind':
        print(json.dumps(rebind(args.physical), sort_keys=True))
    else:
        serve(args.physical)


if __name__ == '__main__':
    main()
