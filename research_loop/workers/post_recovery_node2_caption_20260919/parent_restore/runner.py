"""Restart-safe continuation of the existing finite xhigh caption-parent policy."""

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
ORIGINAL = HERE.parents[1] / 'rohin233_focus_node2_20260918'
sys.path.insert(0, str(ORIGINAL))
import caption_parent as previous
sys.path.insert(0, str(REPO))
from gpu.orch_route_parent_campaign_providers import strong


def require(condition, reason):
    previous.focus.require(condition, reason)


def write(path, value):
    previous.focus.write(path, value)


def remote(request):
    source = (HERE / 'endpoint.py').read_text()
    result = subprocess.run(['bash', str(REPO / 'gpu/ovx_ssh.sh'), 'python3 -B -c ' + shlex.quote(source)],
                            input=json.dumps(request), text=True, capture_output=True, timeout=60)
    require(result.returncode == 0, 'caption_parent_transport_failed_no_retry: ' + result.stderr[-1000:])
    return json.loads(result.stdout)


def pending_from(receipt, text):
    return dict(text=text, publication=receipt['publication'], source_index=receipt['source_index'])


def recovery_state(directory, initial):
    attempts = sorted(directory.glob('turn_[0-9][0-9][0-9][0-9]'))
    pending, prior, latest_source = initial, [], -1
    for attempt in attempts:
        require((attempt / 'PUBLISHED.json').exists(), 'incomplete_provider_or_publication_attempt_requires_reconciliation')
        publication = json.loads((attempt / 'PUBLISHED.json').read_text())
        pending = pending_from(publication, publication['text'])
        latest_source = max(latest_source, publication['source_index'])
        if (attempt / 'ANSWER.json').exists():
            answer = json.loads((attempt / 'ANSWER.json').read_text())['answer']
            prior.append(dict(parent=pending['text'], actual_child_act=answer['actual_act']['raw'],
                              parent_visible_in_act=answer['parent_visible_in_act']))
            pending = None
    return attempts, pending, prior[-3:], latest_source


def serve():
    require(os.uname().nodename == 'nvl-ai' and os.getuid() == 158984
            and Path('/proc/1/comm').read_text().strip() == 'systemd', 'actual_VM_namespace_required')
    os.umask(0o077)
    manifest = json.loads((HERE / 'MANIFEST.json').read_text())
    for name, expected in manifest['sources'].items():
        require(previous.focus.file_sha(REPO / name) == expected, 'parent_source_changed')
    require(os.environ.get('NVIDIA_API_KEY'), 'existing_credential_required_not_persisted')
    locks = []
    for name in manifest['singleton_locks']:
        lock = (REPO / name).open('a')
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        locks.append(lock)
    directory = HERE / 'turns'
    directory.mkdir(mode=0o700, exist_ok=True)
    initial_receipt = json.loads((HERE.parent / 'PARENT_ONCE_20260919T045838Z/PUBLISHED.json').read_text())
    initial = pending_from(initial_receipt['publication'], initial_receipt['response']['message'])
    if (HERE / 'INITIAL_ANSWER.json').exists():
        initial = None
    attempts, pending, prior, latest_source = recovery_state(directory, initial)
    number = manifest['prior_provider_attempts'] + len(attempts)
    require(number <= 640, 'original_640_call_ceiling')
    deadline = manifest['hard_end_unix'] - 60
    write(HERE / f'SERVICE_{time.time_ns()}.json', dict(started_utc=previous.focus.utc(),
          identity=previous.focus.process(os.getpid()), deadline_unix=deadline, original_call_ceiling=640,
          next_number=number, learner_controls=0, policy_unchanged=True, boot_installation='BLOCKED_UNINSTALLED'))
    while time.time() < deadline - 120 and not (HERE / 'STOP').exists():
        observation = remote(dict(operation='poll', pending=pending))
        if pending:
            require(not observation.get('unresolved_publication_outside_window'), 'publication_window_lost_needs_reconciliation')
            if not observation.get('answer'):
                time.sleep(10)
                continue
            answer = observation['answer']
            path = attempts[-1] / 'ANSWER.json' if attempts else HERE / 'INITIAL_ANSWER.json'
            write(path, observation)
            prior.append(dict(parent=pending['text'], actual_child_act=answer['actual_act']['raw'],
                              parent_visible_in_act=answer['parent_visible_in_act']))
            prior = prior[-3:]
            pending = None
        act = observation.get('latest_act')
        if act is None or act['index'] <= latest_source:
            time.sleep(10)
            continue
        require(number < 640, 'original_paid_parent_budget_exhausted')
        attempt = directory / f'turn_{number:04d}'
        attempt.mkdir(mode=0o700)
        payload = json.dumps(dict(epoch='R233_PARENTED_NOT_OLD_UNPARENTED_CONTROL', actual_child_act=act,
                                  previous_turns=prior, tool_metadata=observation['visible_tool_receipts_metadata_only'],
                                  tool_text_and_scores_withheld=True, parent_visibility_is_not_uptake=True))
        write(attempt / 'SOURCE.json', dict(observed=observation, instruction_sha256=previous.focus.sha(previous.INSTRUCTION.encode()),
                                          payload_sha256=previous.focus.sha(payload.encode())))
        response, model, usage = strong(payload, attempt, deadline, previous.INSTRUCTION, reasoning_effort='xhigh')
        text = previous.validate_message(response)
        write(attempt / 'PUBLICATION_INTENT.json', dict(text=text, source_index=act['index'], source_sha256=act['sha256']))
        publication = remote(dict(operation='publish', number=number, text=text,
                                  source_index=act['index'], source_sha256=act['sha256']))
        write(attempt / 'PUBLISHED.json', dict(**publication, text=text, model=model, usage=usage, policy_unchanged=True))
        pending = pending_from(publication, text)
        latest_source = act['index']
        attempts.append(attempt)
        number += 1
    write(HERE / f'EXIT_{time.time_ns()}.json', dict(utc=previous.focus.utc(), next_number=number, learner_signals=0))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--observe-initial', action='store_true')
    args = parser.parse_args()
    if args.observe_initial:
        receipt = json.loads((HERE.parent / 'PARENT_ONCE_20260919T045838Z/PUBLISHED.json').read_text())
        print(json.dumps(remote(dict(operation='poll', pending=pending_from(receipt['publication'], receipt['response']['message']))), sort_keys=True))
    else:
        try:
            serve()
        except Exception as error:
            write(HERE / f'FAILED_{time.time_ns()}.json', dict(utc=previous.focus.utc(), error_type=type(error).__name__,
                  reason=str(error), learner_controls=0, no_provider_or_publication_retry=True))
            raise
