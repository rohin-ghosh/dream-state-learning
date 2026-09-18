"""Main-authorized Node3-operator fallback; exclusive custody and no provider claim."""

import argparse
import copy
import hashlib
import importlib
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import time
import types

import receipt_rebind as predecessor
import takeover as base
from takeover import HERE, REPO, require, read, write, sha, reference

STATE = HERE / 'manual_baseline_v1'
FOLDER = STATE / 'parents/physical0'
OLD = predecessor.STATE / 'parents/physical0'
PREDECESSOR_SHA = '9c58532185f83b6a3163d8f219ac54aca3a0c21644fe7b487308ce50440aea33'
AUTHOR = 'NODE3_OPERATOR_AUTHORED_MAIN_AUTHORIZED_NO_PROVIDER_CALL'


def eligibility(seed, attempts, memory_state):
    require(not memory_state['awaiting_render'], 'pending_publication_no_fallback')
    combined = seed['attempts'] + attempts
    require(all(entry['result']['status'] in ('PROVIDER_FAILED', 'VALIDATION_FAILED', 'SILENT') for entry in combined),
            'published_or_uncertain_no_fallback')
    require(any(entry['result']['status'] in ('PROVIDER_FAILED', 'VALIDATION_FAILED') for entry in combined),
            'documented_prepublication_block_required')


def binding(config_path):
    require(sha(HERE / 'receipt_rebind.py') == PREDECESSOR_SHA, 'immutable_predecessor_runtime')
    return predecessor.runtime(0, config_path)


def preflight():
    parent, provider, config, helper = binding(OLD / 'CONFIG.json')
    policy = importlib.import_module('gpu.orch_r166_parent_policy')
    state = read(STATE / 'SUPPORT_SOURCE_CANDIDATE.json')['snapshot']
    seed = read(OLD / 'SEED.json')
    attempts = policy.local_attempts(OLD / 'parent')
    memory_state = policy.memory(seed, attempts, state)
    eligibility(seed, attempts, memory_state)
    authored = read(STATE / 'SUPPORT_RESPONSE.json')
    parsed = provider.response_schema(json.dumps(authored))
    details = policy.decision(parsed, state, memory_state)
    require(details['object_id'] == 'sleep_training_evidence' and details['next_task'] is None, 'same_existing_mismatch_no_counter_reset')
    require(len(parsed['message'].split()) <= 240 and len(parsed['message'].encode()) <= 4096, 'A_arm_caps')
    for field, value in [('object_id', 'UpperCase'), ('next_task', 'unbound next action')]:
        invalid = copy.deepcopy(authored)
        invalid['rationale'][field] = value
        try:
            policy.decision(provider.response_schema(json.dumps(invalid)), state, memory_state)
        except ValueError:
            pass
        else:
            raise ValueError('unchanged_strict_validator_regression')
    for status in ('PUBLISHED', 'PUBLICATION_UNKNOWN'):
        try:
            eligibility(dict(attempts=[dict(result=dict(status=status))]), [], dict(awaiting_render=False))
        except ValueError:
            pass
        else:
            raise ValueError('no_duplicate_fallback_regression')
    return dict(status='CPU_PASS', author=AUTHOR, provider_calls=0, publication_calls=0, child_signals=0,
        exact_response=reference(STATE / 'SUPPORT_RESPONSE.json'), source=reference(STATE / 'SUPPORT_SOURCE_CANDIDATE.json'),
        strict_policy=reference(policy.__file__), config=reference(OLD / 'CONFIG.json'), wrapper=reference(__file__),
        words=len(parsed['message'].split()), unchanged_validators=True, preserved_object_id=details['object_id'])


def activate():
    require(bool(os.environ.get('NVIDIA_API_KEY')), 'private_inherited_provider_environment_for_successor')
    require(not (STATE / 'FALLBACK_ONCE.json').exists(), 'never_replay_manual_baseline')
    gate = read(STATE / 'CPU_GATE.json')
    require(gate['status'] == 'CPU_PASS' and gate['wrapper']['sha256'] == sha(__file__)
            and gate['exact_response']['sha256'] == sha(STATE / 'SUPPORT_RESPONSE.json'), 'exact_CPU_gate_before_custody')
    parent, provider, config, helper = binding(OLD / 'CONFIG.json')
    policy = importlib.import_module('gpu.orch_r166_parent_policy')
    import snapshot_transport
    expected = read(OLD / 'SPAWNED.json')['identity']
    base.ledger = predecessor.metadata.modern_ledger
    descriptor, reserved = base.quiet_pause(expected, str(OLD / 'parent'), config, time.monotonic() + 120)
    terminated = False
    try:
        require(not (OLD / 'FIRST_PUBLICATION.json').exists(), 'existing_baseline_no_manual_fallback')
        observed = snapshot_transport.poll(0, read(STATE / 'SUPPORT_SOURCE_CANDIDATE.json')['cursor'])
        state = observed['snapshot']
        require(state['caught_up'], 'fresh_exclusive_TRAIN_source')
        write(FOLDER / 'LIVE_BOOTSTRAP_READY.json', observed)
        seed = copy.deepcopy(read(OLD / 'SEED.json'))
        attempts = policy.local_attempts(OLD / 'parent')
        memory_state = policy.memory(seed, attempts, state)
        eligibility(seed, attempts, memory_state)
        for root in (HERE, predecessor.metadata.STATE, predecessor.response.STATE, predecessor.STATE, STATE):
            for directory in (root / 'parents/physical0/parent').glob('parent_*'):
                require(not (directory / 'PUBLISH_INTENT.json').exists(), 'no_prior_publish_intent_replay')
                require((directory / 'RESULT.json').exists(), 'unfinished_attempt_no_fallback')
        authored = read(STATE / 'SUPPORT_RESPONSE.json')
        parsed = provider.response_schema(json.dumps(authored))
        details = policy.decision(parsed, state, memory_state)
        require(time.time() < base.HARD_END and config['hard_end_unix'] == base.HARD_END, 'unchanged_1650_stop')
        write(FOLDER / 'PREDECESSOR_SETTLED_LEDGER.json', reserved)
        seed['attempts'] += reserved['attempts']
        seed.update(last_response_count=reserved['response_cursor'], last_request_count=reserved['request_cursor'],
                    legacy_ledger=reference(FOLDER / 'PREDECESSOR_SETTLED_LEDGER.json'))
        write(FOLDER / 'SEED.json', seed)
        config.update(predecessor_output=str(OLD / 'parent'), predecessor_started_sha256=sha(OLD / 'parent/STARTED.json'),
            predecessor_seed=reference(FOLDER / 'SEED.json'), start_after_request_count=reserved['request_cursor'],
            start_after_response_count=reserved['response_cursor'], manual_fallback_wrapper=reference(__file__),
            manual_fallback_authorship=AUTHOR, manual_fallback_cpu=reference(STATE / 'CPU_GATE.json'))
        write(FOLDER / 'CONFIG.json', config)
        for name in predecessor.CARRY:
            if (OLD / name).exists():
                write(FOLDER / name, (OLD / name).read_text())
        directory = FOLDER / 'parent' / ('parent_%012d_manual_baseline_1' % state['request_count'])
        write(directory / 'SOURCE.json', state)
        instruction, payload = policy.prompt(config, state, memory_state)
        write(directory / 'PROMPT.json', dict(instruction=instruction, payload=payload, author=AUTHOR, provider_called=False))
        write(directory / 'AUTHORSHIP.json', dict(author=AUTHOR, authorizing_directive='Main resumed14:15 PDT: deliver source-grounded support_free fallback under exclusive custody if provider remains prepublication-blocked; own node3 operations.',
            exact_response=reference(STATE / 'SUPPORT_RESPONSE.json'), source=reference(directory / 'SOURCE.json'),
            predecessor_ledger=reference(FOLDER / 'PREDECESSOR_SETTLED_LEDGER.json'), provider_calls=0, existing_object_id_preserved=True))
        require(predecessor.metadata.modern_ledger(OLD / 'parent', config) == reserved and base.same(expected, base.identity(expected['pid'])), 'exclusive_parent_ledger_unchanged')
        write(STATE / 'FALLBACK_ONCE.json', dict(status='RESERVED_ONCE_BEFORE_PUBLICATION', old_parent=expected,
            source=reference(directory / 'SOURCE.json'), author=AUTHOR, at_unix=time.time(), child_signals=0))
        signal.pidfd_send_signal(descriptor, signal.SIGTERM)
        signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        terminated = True
        require(bool(select.select([descriptor], [], [], 20)[0]), 'predecessor_exit_before_exclusive_console')
        result = dict(details, status='PUBLICATION_UNKNOWN', source_sha256=sha(directory / 'SOURCE.json'),
            message=parsed['message'], model=AUTHOR, usage=None, grammar_lesson=False, relapse_audit_sha256=[],
            author=AUTHOR, provider_called=False, authorship=reference(directory / 'AUTHORSHIP.json'))
        with policy.community.parent_lock(FOLDER / 'parent'):
            write(directory / 'PUBLISH_INTENT.json', dict(message=parsed['message'], speaker='Astra', author=AUTHOR,
                source=reference(directory / 'SOURCE.json'), created_unix=time.time()))
            try:
                result['publication'] = parent.publish(REPO, config, parsed['message'])
                result.update(status='PUBLISHED', published_observed_unix=time.time())
            except Exception as error:
                result.update(error_type=type(error).__name__, error=str(error)[:500])
            write(directory / 'RESULT.json', result)
        require(result['status'] == 'PUBLISHED', 'unknown_console_publication_no_replay_or_parent_calls')
        first = dict(status='PUBLISHED_RENDER_NOT_YET_VERIFIED', physical=0, arm='A', config=reference(FOLDER / 'CONFIG.json'),
            result=reference(directory / 'RESULT.json'), source=reference(directory / 'SOURCE.json'), prompt=reference(directory / 'PROMPT.json'),
            requested_model=None, actual_model=None, author=AUTHOR, provider_called=False, publication=result['publication'],
            message_sha256=hashlib.sha256(parsed['message'].encode()).hexdigest(), source_response_count=state['response_count'],
            schedule_on='response', published_observed_unix=result['published_observed_unix'], helper_sha256=base.HELPER_SHA,
            assignments_sha256=base.ASSIGNMENT_SHA, authorship=reference(directory / 'AUTHORSHIP.json'))
        write(FOLDER / 'FIRST_PUBLICATION.json', first)
        process = subprocess.Popen([sys.executable, '-B', str(Path(__file__).resolve()), 'serve'], cwd=REPO,
            env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES=''), stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        write(FOLDER / 'SPAWNED.json', dict(status='MANUAL_BASELINE_PUBLISHED_PARENT_SUCCESSOR_STARTED', identity=base.identity(process.pid),
            predecessor=expected, publication=result['publication'], child_restarts=0, author=AUTHOR, started_unix=time.time()))
        return dict(status='PUBLISHED_RENDER_PENDING', publication=result['publication'], parent_pid=process.pid, author=AUTHOR,
            result=reference(directory / 'RESULT.json'), source_response_count=state['response_count'])
    finally:
        if not terminated:
            signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        os.close(descriptor)


def serve():
    namespace = dict(predecessor.metadata.__dict__, STATE=STATE, runtime=predecessor.runtime, hashlib=hashlib,
                     __file__=str(Path(__file__).resolve()))
    types.FunctionType(predecessor.metadata.serve.__code__, namespace, 'serve')(0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('preflight', 'activate', 'serve'))
    args = parser.parse_args()
    if args.action == 'preflight':
        gate = preflight()
        write(STATE / 'CPU_GATE.json', gate)
        print(json.dumps(gate, sort_keys=True))
    elif args.action == 'activate':
        print(json.dumps(activate(), sort_keys=True))
    else:
        serve()


if __name__ == '__main__':
    main()
