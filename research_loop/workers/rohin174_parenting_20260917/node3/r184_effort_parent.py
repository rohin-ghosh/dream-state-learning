"""Private next-turn effort amendment over the unchanged owned parent loop."""

import argparse
import hashlib
import importlib
import inspect
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import time
import types

import parent_http_retry as previous
import node3_route_binding as route
import observe_r181_receipts as observer
import takeover as base


STATE = base.HERE / 'r184_effort'
MARKER = 'ROHIN184_TWO_WAY_EFFORT_QUESTIONS_V1'
AMENDMENT = '''
ROHIN184_TWO_WAY_EFFORT_QUESTIONS_V1 — prospective parent-private amendment.
At the next already-eligible parent turn, ground your child-facing message in
the child's actual current object and response. Use questions only; never give
the answer, solve the task, prescribe a solution, invent an outcome, or turn
this into a fixed ritual. Ask in BOTH directions: why would additional thinking
be worth its time versus making an informative attempt now, and what unresolved
uncertainty could make staying with the question more valuable than acting yet?
Invite the child to judge what evidence would justify continuing thought or
making an attempt. Sometimes staying and thinking is the right choice; do not
assume that more thinking is always better or that action is always better.
Let the child decide and carry out its own next step. Adapt the questions to
what the child actually did, noticed, and intends, without supplying answers.
This supersedes conflicting pedagogical advice only. Keep the assigned arm's
existing response cadence and word/byte caps, strict metadata validators,
lowercase object IDs, exact quote hash, and continue=>next_task=null and
continuity=null. Do not repeat the shared baseline, bypass pending ingestion,
force a turn, reset counters, or claim unobserved execution or learning.
'''


def amended_prompt(original):
    def prompt(config, state, memory_state):
        instruction, payload = original(config, state, memory_state)
        base.require(MARKER not in instruction, 'single_effort_amendment')
        return instruction + '\n' + AMENDMENT, payload
    return prompt


def install_prompt(policy):
    closure = inspect.getclosurevars(policy.tick).nonlocals
    strict_tick, dispatch = closure['strict_tick'], closure['dispatch']
    prompt = amended_prompt(policy.prompt)
    policy.prompt = prompt
    dispatch.__globals__['prompt'] = prompt
    base.require(strict_tick.__globals__['prompt'] is prompt
        and dispatch.__globals__['prompt'] is prompt, 'actual_normal_and_corrective_prompt_binding')


def exposure(physical, output, state):
    folder = STATE / ('physical' + str(physical))
    first_path = folder / 'FIRST_PUBLICATION.json'
    if not first_path.exists():
        for attempt in sorted(Path(output).glob('parent_*')):
            paths = [attempt / name for name in ('RESULT.json', 'PROMPT.json', 'SOURCE.json')]
            if not all(path.exists() for path in paths):
                continue
            result, prompt, source = [base.read(path) for path in paths]
            if result['status'] != 'PUBLISHED' or MARKER not in prompt['instruction']:
                continue
            base.require(result['source_sha256'] == base.sha(paths[2])
                and base.read(attempt / 'PUBLISH_INTENT.json')['message'] == result['message'],
                'actual_amended_publication_source')
            publication = result['publication']
            observed = observer.remote({physical: publication})
            actual = next(row for row in observed['rows'] if row['physical'] == physical)['publication']
            base.require(actual['sha256'] == publication['sha256'], 'exact_actual_inbox_bytes')
            first = dict(status='ACTUAL_R184_EFFORT_PUBLISHED', physical=physical,
                publication=publication, actual_inbox=actual, observed_unix=observed['observed_unix'],
                source=base.reference(paths[2]), prompt=base.reference(paths[1]), result=base.reference(paths[0]),
                source_head=source['head_sha256'], marker=MARKER,
                message_sha256=hashlib.sha256(result['message'].encode()).hexdigest())
            base.write(first_path, first)
            observer.post(f"{observer.NAMES[physical]} R184 effort FIRST ACTUAL PUBLISHED: inbox{publication['id']}, persisted_unix{actual['file_mtime_unix']}; exact source/prompt/provider/inbox evidence `{first_path.relative_to(base.REPO)}`. Rendering not yet claimed; no baseline duplicate.")
            break
    rendered_path = folder / 'FIRST_RENDERED_REQUEST.json'
    if first_path.exists() and not rendered_path.exists():
        first = base.read(first_path)
        delivery = state['delivered'].get(first['publication']['id'])
        if delivery is not None:
            base.require(delivery['text_sha256'] == first['message_sha256'], 'same_effort_text_rendered')
            proof = observer.request_proof(physical, first['publication']['id'], delivery['record_index'])
            base.write(rendered_path, dict(status='ACTUAL_R184_EFFORT_RENDERED', delivery=delivery,
                exact_request=proof, publication=base.reference(first_path), observed_unix=time.time()))
            observer.post(f"{observer.NAMES[physical]} R184 effort FIRST ACTUAL RENDERED REQUEST{delivery['record_index']} SHA{delivery['record_sha256']}; exact framed proof `{rendered_path.relative_to(base.REPO)}`. No learned-outcome claim.")


def runtime(physical, config_path):
    parent, provider, config, helper = previous.runtime(physical, config_path)
    policy = importlib.import_module('gpu.orch_r166_parent_policy')
    install_prompt(policy)
    original_tick = policy.tick

    def tick(repository, current_config, output, seed, state):
        status = original_tick(repository, current_config, output, seed, state)
        try:
            exposure(physical, output, state)
        except Exception as error:
            base.write(STATE / ('physical' + str(physical)) / ('EVIDENCE_RECHECK_%d.json' % time.time_ns()),
                dict(error_type=type(error).__name__, no_publication_retry=True, observed_unix=time.time()))
        return status

    policy.tick = tick
    return parent, provider, config, helper


def preflight(physical):
    folder = route.folder_for(physical)
    parent, provider, config, helper = runtime(physical, folder / 'CONFIG.json')
    policy = importlib.import_module('gpu.orch_r166_parent_policy')
    state = dict(events=[], delivered={}, journal_id='CPU', split='TRAIN', response_count=100,
        request_count=100, sleep_count=0, caught_up=True, head_sha256='0' * 64)
    seed = dict(journal_id='CPU', object_delivered_turns={}, last_response_count=100,
        last_request_count=100, prospective_request_count=100, credits={}, grammar_delivered=False, attempts=[])
    instruction, payload = policy.prompt(config, state, policy.memory(seed, [], state))
    base.require(instruction.count(MARKER) == 1 and 'Use questions only' in instruction
        and 'Sometimes staying and thinking is the right choice' in instruction, 'two_way_question_policy')
    base.require(config['hard_end_unix'] == base.HARD_END and config['schedule_on'] == 'response', 'unchanged_clock_wall')
    return dict(status='FOCUSED_PARENT_PROMPT_PASS', physical=physical, arm=config['r175_arm'],
        cadence=config['cadence_responses'], word_limit=config['r175_word_limit'],
        config=base.reference(folder / 'CONFIG.json'), seed=base.reference(folder / 'SEED.json'),
        wrapper=base.reference(__file__), marker=MARKER,
        instruction_sha256=hashlib.sha256(instruction.encode()).hexdigest(),
        provider_calls=0, publication_calls=0, child_signals=0, actual_tick_prompt_paths=2)


def serve(physical):
    folder = route.folder_for(physical)
    owned = STATE / ('physical' + str(physical))
    offset = max((int(path.stem.split('_')[1]) for path in folder.glob('STATUS_*.json')), default=-1) + 1

    def preserved_write(path, document):
        path = Path(path)
        if path == folder / 'parent/STARTED.json':
            path = owned / 'STARTED.json'
            document = dict(document, amendment=MARKER, wrapper=base.reference(__file__),
                unchanged_seed=base.reference(folder / 'SEED.json'), no_cursor_reseed=True)
        elif path.parent == folder and path.name.startswith('STATUS_'):
            path = folder / ('STATUS_%06d.json' % (offset + int(path.stem.split('_')[1])))
        base.write(path, document)

    namespace = dict(previous.current.metadata.__dict__, STATE=folder.parent.parent, runtime=runtime,
        hashlib=hashlib, write=preserved_write, __file__=str(Path(__file__).resolve()))
    try:
        types.FunctionType(previous.current.metadata.serve.__code__, namespace, 'serve')(physical)
    except BaseException as error:
        base.write(owned / 'SERVICE_FAILED.json', dict(error_type=type(error).__name__, observed_unix=time.time()))
        raise


def bind(physical):
    folder = route.folder_for(physical)
    owned = STATE / ('physical' + str(physical))
    base.require(not (owned / 'TAKEOVER_ONCE.json').exists(), 'no_duplicate_effort_takeover')
    checked = subprocess.run([sys.executable, '-B', __file__, 'preflight', '--physical', str(physical)],
        capture_output=True, text=True, timeout=30)
    base.require(checked.returncode == 0, 'focused_actual_parent_prompt_check:' + checked.stderr[-300:])
    base.write(owned / 'PREFLIGHT.json', json.loads(checked.stdout))
    expected = base.read(folder / 'RETRY_SPAWNED.json')['identity']
    config = base.read(folder / 'CONFIG.json')
    base.ledger = previous.current.metadata.modern_ledger
    descriptor, reserved = base.quiet_pause(expected, str(folder / 'parent'), config, time.monotonic() + 120)
    terminated = False
    try:
        base.require(base.same(expected, base.identity(expected['pid']))
            and base.ledger(folder / 'parent', config) == reserved, 'same_quiet_parent_and_ledger')
        base.write(owned / 'TAKEOVER_ONCE.json', dict(predecessor=expected, ledger=reserved,
            config=base.reference(folder / 'CONFIG.json'), seed=base.reference(folder / 'SEED.json'),
            wrapper=base.reference(__file__), amendment=MARKER, observed_unix=time.time(),
            no_cursor_reseed=True, no_baseline_resend=True, child_signals=0))
        signal.pidfd_send_signal(descriptor, signal.SIGTERM)
        signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        terminated = True
        base.require(bool(select.select([descriptor], [], [], 20)[0]), 'predecessor_exit_before_new_parent')
        command = [sys.executable, '-B', str(Path(__file__).resolve()), 'serve', '--physical', str(physical)]
        process = subprocess.Popen(command, cwd=base.REPO,
            env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES=''),
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        for unused in range(200):
            actual = base.identity(process.pid)
            if actual['argv'] == command:
                break
            time.sleep(.01)
        base.require(actual['argv'] == command, 'actual_new_parent_exec')
        receipt = dict(status='R184_EFFORT_PARENT_BOUND_NOT_DELIVERED', physical=physical,
            identity=actual, predecessor=expected, observed_unix=time.time(), amendment=MARKER,
            config_unchanged=True, seed_unchanged=True, pending_ids_preserved=reserved['pending_existing_inbox_ids'],
            hard_end_unix=base.HARD_END, child_signals=0)
        base.write(owned / 'SPAWNED.json', receipt)
        return receipt
    finally:
        if not terminated:
            signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        os.close(descriptor)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('preflight', 'bind', 'serve'))
    parser.add_argument('--physical', type=int, choices=base.PHYSICALS, required=True)
    options = parser.parse_args()
    result = globals()[options.action](options.physical)
    if result is not None:
        print(json.dumps(result, sort_keys=True))
