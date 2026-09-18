"""Recover published receipt bookkeeping without replaying a parent publication."""

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

import metadata_rebind as metadata
import response_rebind as response
import takeover as base
from takeover import HERE, REPO, require, read, write, sha, reference

STATE = HERE / 'receipt_repair_v1'
RESPONSE_SHA = '59434e03d58a0c1c8b6d605db0bc6d2bf3d350399be864ca6761defc7c95dd46'
CARRY = ('FIRST_PUBLICATION.json', 'FIRST_RENDERED_REQUEST.json', 'AUDIT_AT_3_SLEEPS.json',
         'WITHDRAWAL_STARTED.json', 'WITHDRAWAL_COMPLETE.json', 'TECHNICAL_RETRY_ONCE.json')


def reconcile_first(folder, physical):
    if (folder / 'FIRST_PUBLICATION.json').exists():
        return read(folder / 'FIRST_PUBLICATION.json')
    config = read(folder / 'CONFIG.json')
    for attempt in sorted((folder / 'parent').glob('parent_*')):
        path = attempt / 'RESULT.json'
        if not path.exists() or read(path)['status'] != 'PUBLISHED':
            continue
        result = read(path)
        require(result['source_sha256'] == sha(attempt / 'SOURCE.json'), 'published_source_binding')
        require((attempt / 'PUBLISH_INTENT.json').exists(), 'actual_existing_publication_intent')
        require(read(attempt / 'PUBLISH_INTENT.json')['message'] == result['message'], 'unchanged_published_message')
        first = dict(status='PUBLISHED_RENDER_NOT_YET_VERIFIED', physical=physical, arm=config['r175_arm'],
            config=reference(folder / 'CONFIG.json'), result=reference(path), source=reference(attempt / 'SOURCE.json'),
            prompt=reference(attempt / 'PROMPT.json'), requested_model=base.MODEL, actual_model=result['model'],
            publication=result['publication'], message_sha256=hashlib.sha256(result['message'].encode()).hexdigest(),
            source_response_count=read(attempt / 'SOURCE.json')['response_count'], schedule_on='response',
            published_observed_unix=time.time(), helper_sha256=base.HELPER_SHA, assignments_sha256=base.ASSIGNMENT_SHA,
            bookkeeping_recovery='Existing actual PUBLISHED result; no provider call or console replay',
            response_adapter_sha256=response.ADAPTER_SHA)
        write(folder / 'FIRST_PUBLICATION.json', first)
        return first
    return None


def runtime(physical, config_path):
    require(sha(HERE / 'response_rebind.py') == RESPONSE_SHA, 'immutable_response_runtime')
    parent, provider, config, helper = response.runtime(physical, config_path)
    require(config['receipt_wrapper']['sha256'] == sha(__file__), 'immutable_receipt_runtime')
    supplement = config['validator_supplement']
    require(sha(supplement['path']) == supplement['sha256'], 'private_documentation_pin')
    policy = importlib.import_module('gpu.orch_r166_parent_policy')
    previous_prompt = policy.prompt

    def prompt(current_config, state, memory_state):
        instruction, payload = previous_prompt(current_config, state, memory_state)
        instruction += '\nPARENT-PRIVATE EXISTING VALIDATOR DOCUMENTATION, NOT CHILD BOILERPLATE:\n'
        instruction += Path(supplement['path']).read_text()
        return instruction, payload

    policy.prompt = prompt
    return parent, provider, config, helper


def prepare():
    require(sha(HERE / 'response_rebind.py') == RESPONSE_SHA, 'immutable_predecessor')
    for physical in base.PHYSICALS:
        old = response.STATE / 'parents' / ('physical' + str(physical))
        new = STATE / 'parents' / ('physical' + str(physical))
        reconcile_first(old, physical)
        config = copy.deepcopy(read(old / 'CONFIG.json'))
        config.update(predecessor_output=str(old / 'parent'), predecessor_started_sha256=sha(old / 'parent/STARTED.json'),
                      receipt_wrapper=reference(__file__), validator_supplement=reference(STATE / 'VALIDATOR_SUPPLEMENT.md'),
                      receipt_repair='Missing hashlib binding only; no publication retry or validation relaxation')
        write(new / 'CANDIDATE_CONFIG.json', config)
    print(json.dumps(dict(status='RECEIPT_REPAIR_CANDIDATES_READY')))


def service_namespace():
    return dict(metadata.__dict__, STATE=STATE, runtime=runtime, hashlib=hashlib, __file__=str(Path(__file__).resolve()))


def preflight(physical, final=False):
    namespace = dict(response.__dict__, STATE=STATE, runtime=runtime, __file__=str(Path(__file__).resolve()))
    result = types.FunctionType(response.preflight.__code__, namespace, 'preflight')(physical, final)
    require(service_namespace()['hashlib'].sha256(b'exact').hexdigest() == hashlib.sha256(b'exact').hexdigest(), 'publication_receipt_hash_regression')
    require('TECHNICAL_RETRY_ONCE.json' in CARRY, 'carry_one_shot_retry_reservation')
    result.update(receipt_hash_regression='PASS', corrective_reservation_carried=True)
    return result


def rebind(physical):
    import snapshot_transport
    require(bool(os.environ.get('NVIDIA_API_KEY')), 'private_inherited_credential')
    old = response.STATE / 'parents' / ('physical' + str(physical))
    new = STATE / 'parents' / ('physical' + str(physical))
    require(not (new / 'HANDOFF_ONCE.json').exists(), 'no_duplicate_handoff')
    expected = read(old / 'SPAWNED.json')['identity']
    observed = snapshot_transport.poll(physical, read(old / 'LIVE_BOOTSTRAP_READY.json')['cursor'])
    require(observed['snapshot']['caught_up'], 'fresh_caught_up_snapshot')
    write(new / 'LIVE_BOOTSTRAP_READY.json', observed)
    checked = subprocess.run([sys.executable, '-B', __file__, 'preflight', '--physical', str(physical)], capture_output=True, text=True, timeout=30)
    require(checked.returncode == 0, 'receipt_CPU_before_parent_handoff')
    config = read(old / 'CONFIG.json')
    descriptor = None
    terminated = False
    base.ledger = metadata.modern_ledger
    if (Path('/proc') / str(expected['pid'])).exists():
        descriptor, reserved = base.quiet_pause(expected, str(old / 'parent'), config, time.monotonic() + 150)
    else:
        require((old / 'SERVICE_FAILED.json').exists(), 'actual_parent_exit_evidence_not_waiter')
        require(read(old / 'SERVICE_FAILED.json')['error_type'] == 'NameError', 'known_receipt_bookkeeping_failure')
        reconcile_first(old, physical)
        reserved = metadata.modern_ledger(old / 'parent', config)
    try:
        require(observed['snapshot']['response_count'] >= reserved['response_cursor'], 'no_counter_rewind')
        write(new / 'PREDECESSOR_SETTLED_LEDGER.json', reserved)
        seed = copy.deepcopy(read(old / 'SEED.json'))
        seed['attempts'] += reserved['attempts']
        seed.update(last_response_count=reserved['response_cursor'], last_request_count=reserved['request_cursor'],
                    legacy_ledger=reference(new / 'PREDECESSOR_SETTLED_LEDGER.json'))
        write(new / 'SEED.json', seed)
        candidate = read(new / 'CANDIDATE_CONFIG.json')
        candidate.update(start_after_response_count=reserved['response_cursor'], start_after_request_count=reserved['request_cursor'],
                         predecessor_seed=reference(new / 'SEED.json'))
        write(new / 'CONFIG.json', candidate)
        for name in CARRY:
            if (old / name).exists():
                write(new / name, (old / name).read_text())
        checked = subprocess.run([sys.executable, '-B', __file__, 'preflight', '--physical', str(physical), '--final'], capture_output=True, text=True, timeout=30)
        require(checked.returncode == 0, 'final_receipt_CPU')
        write(new / 'CPU_PREFLIGHT.json', json.loads(checked.stdout))
        require(metadata.modern_ledger(old / 'parent', config) == reserved, 'settled_ledger_unchanged')
        write(new / 'HANDOFF_ONCE.json', dict(identity=expected, actual_predecessor_exit=descriptor is None,
              reason='Nonmaterial first-publication receipt missing hashlib; preserve successful inbox publication',
              at_unix=time.time(), pending_ids=reserved['pending_existing_inbox_ids'], child_signals=0))
        if descriptor is not None:
            require(base.same(expected, base.identity(expected['pid'])), 'same_owned_parent')
            signal.pidfd_send_signal(descriptor, signal.SIGTERM)
            signal.pidfd_send_signal(descriptor, signal.SIGCONT)
            terminated = True
            require(bool(select.select([descriptor], [], [], 20)[0]), 'parent_exit_before_successor')
        require(not (Path('/proc') / str(expected['pid'])).exists() or terminated, 'no_duplicate_parent')
        process = subprocess.Popen([sys.executable, '-B', str(Path(__file__).resolve()), 'serve', '--physical', str(physical)],
            cwd=REPO, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES=''),
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        receipt = dict(status='RECEIPT_REPAIR_PARENT_STARTED', physical=physical, identity=base.identity(process.pid),
            predecessor=expected, config=reference(new / 'CONFIG.json'), pending_ids_preserved=reserved['pending_existing_inbox_ids'],
            wrapper=reference(__file__), child_restarts=0, publication_replays=0, started_unix=time.time())
        write(new / 'SPAWNED.json', receipt)
        return receipt
    finally:
        if descriptor is not None:
            if not terminated:
                signal.pidfd_send_signal(descriptor, signal.SIGCONT)
            os.close(descriptor)


def serve(physical):
    require(sha(HERE / 'metadata_rebind.py') == response.METADATA_SHA, 'immutable_service_body')
    types.FunctionType(metadata.serve.__code__, service_namespace(), 'serve')(physical)


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
