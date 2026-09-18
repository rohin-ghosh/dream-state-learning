"""R185-authorized forward parent policy; no learner or pending-inbox edits."""

import argparse
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import select
import shutil
import signal
import subprocess
import sys
import time


HOME = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('preserved_R178_runtime', HOME / 'r178_forward_parent.py')
raw = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(raw)
base, errata = raw.base, raw.errata
PREVIOUS = {physical: HOME / ('activation_r178_20260917T2148Z' if physical == 1 else
    'activation_20260917T2057Z') / f'physical{physical}' for physical in (0, 1, 3, 4)}
ARMS = {0: ('B', 2), 1: ('B', 2), 3: ('D', 3), 4: ('A', 1)}
POLICY = '''R184/R185 forward parent policy, replacing the prior rhetorical style but not its cadence or evidence rules:
At the next legitimate parent turn, return exactly three numbered question lines, numbered 1., 2., 3., each ending in one question mark. No introductory baseline, answer, explanation, worked solution, or closing directive.
Ground all three questions in this child's current object and actual evidence. Probe effort in BOTH directions: what concrete uncertainty would more thinking resolve, versus what uncertainty would a small real attempt resolve? More thought is not automatically better, and acting sooner is not automatically better. Sometimes staying with the present approach is justified. Leave that choice to the child.
Question1 should ask which current uncertainty is decision-relevant and whether further thought or an attempt would distinguish it. Question2 should ask what the child chooses to do or deliberately keep doing, with its expected consequence. Question3 should ask what actual observation would support staying, thinking more, or trying differently. These are action-guiding questions, not supplied answers or an order to switch tasks.
Do not invent executor availability, results, peers, or observations. Existing kernel and raw external executors remain unavailable here. An intended attempt is not an executed result. Preserve strict private evidence, lowercase object IDs, disposition/next_task consistency and all existing validation. Never duplicate an original or Fable baseline, retry PUBLICATION_UNKNOWN, or force a call while an accepted publication awaits rendering.'''


def question_shape(message):
    lines = [line.strip() for line in message.splitlines() if line.strip()]
    base.require(len(lines) == 3 and all(re.fullmatch(str(index) + r'\. [^?\n]+\?', line)
        for index, line in enumerate(lines, 1)), 'R184_three_question_lines_no_answer_prose')
    base.require(not message.endswith(raw.BASELINE_END), 'never_duplicate_baseline')


def bind(policy):
    original_prompt, original_decision = policy.prompt, policy.decision

    def prompt(config, state, memory):
        instruction, payload = original_prompt(config, state, memory)
        return instruction + '\n\n' + POLICY, payload

    def decision(response, state, memory):
        details = original_decision(response, state, memory)
        if details is not None:
            question_shape(response['message'])
        return details

    policy.prompt, policy.decision = prompt, decision
    return policy


def phase_hold(physical, anchor, state):
    baseline = state['delivered'].get(raw.TURN) if physical == 1 else None
    exposure = baseline['sleep_count'] if baseline else anchor['baseline_completed_sleeps'] if anchor else None
    return exposure is not None and base.withdrawal_state(exposure, state['sleep_count']) == 'PARENT_WITHDRAWAL_ONE_SLEEP'


def checked(lane):
    lane = lane.resolve()
    base.require(lane.parent.parent == HOME and lane.parent.name.startswith('activation_r184_'), 'owned_R184_parent_output')
    proof = base.read(lane / 'BINDING.json')
    physical = proof['physical']
    base.require(physical in ARMS and lane.name == f'physical{physical}' and
        proof['wrapper_sha256'] == base.sha(__file__), 'bound_owned_wrapper')
    config = base.read(lane / 'CONFIG.json')
    base.require(base.sha(lane / 'CONFIG.json') == proof['config_sha256'] and config['root'] == base.ROOTS[physical]
        and (config['r175_arm'], config['cadence_responses']) == ARMS[physical]
        and config['hard_end_unix'] == base.WALL and config['community_learner'] is False,
        'same_life_arm_cadence_wall_no_community_append')
    base.require({str(path.relative_to(lane / 'source')): base.sha(path)
        for path in (lane / 'source').rglob('*') if path.is_file()} == proof['source_files'], 'immutable_existing_parent_source')
    if physical == 1:
        raw.release(base.read(raw.MAIN_RECEIPT))
        base.require(proof['raw_release_sha256'] == base.sha(raw.MAIN_RECEIPT), 'R178_preservation_release')
    return config, proof


def load(lane):
    policy, parent = errata.import_bound(lane)
    bind(policy)
    return policy, parent


def reader(proof):
    return raw.OLD if proof['physical'] == 1 else PREVIOUS[proof['physical']]


def stage(lane, physical):
    previous = PREVIOUS[physical]
    if physical == 1:
        raw.checked(previous)
    else:
        base.checked_bundle(previous)
    base.require(not lane.exists() and lane.parent.parent == HOME and lane.name == f'physical{physical}', 'new_owned_lane')
    lane.mkdir(parents=True)
    shutil.copytree(previous / 'source', lane / 'source')
    for name in ('CONFIG.json', 'PARENT_METADATA_ERRATA_V1.md', 'orch_r175_parent_response.py'):
        shutil.copyfile(previous / name, lane / name)
    base.write(lane / 'PLAN.json', dict(physical=physical, arm=ARMS[physical][0], root=base.ROOTS[physical],
        one_corrective_call=False))
    actor = base.read(previous / 'parent/STARTED.json')['actor']
    proof = dict(physical=physical, wrapper_sha256=base.sha(__file__), previous_lane=str(previous),
        predecessor=actor, config_sha256=base.sha(lane / 'CONFIG.json'),
        source_files={str(path.relative_to(lane / 'source')): base.sha(path)
            for path in (lane / 'source').rglob('*') if path.is_file()},
        raw_release_sha256=base.sha(raw.MAIN_RECEIPT) if physical == 1 else None,
        policy_sha256=hashlib.sha256(POLICY.encode()).hexdigest(),
        scope='R185_next_legitimate_parent_turn_only_no_duplicate_baseline_no_child_changes')
    base.write(lane / 'BINDING.json', proof)
    return dict(status='STAGED_NOT_PUBLISHED', physical=physical, lane=str(lane))


def serve(lane, preflight=False):
    config, proof = checked(lane)
    policy, parent = load(lane)
    policy.validate(config)
    seed = base.read(lane / 'SEED.json')
    observed = base.read(lane / 'TAKEOVER_SNAPSHOT.json')
    if preflight:
        memory = policy.memory(seed, [], observed['snapshot'])
        instruction, payload = policy.prompt(config, observed['snapshot'], memory)
        base.require(POLICY in instruction and payload, 'actual_bound_effort_prompt')
        return dict(status='PASS', model_calls=0, awaiting_render=memory['awaiting_render'])
    output = lane / 'parent'
    base.require(not output.exists(), 'new_parent_output_never_replay')
    with (HOME / f"R175_PARENT_{proof['physical']}.lock").open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        output.mkdir()
        base.write(output / 'STARTED.json', dict(actor=base.identity(os.getpid()), observed_unix=time.time(),
            policy_sha256=proof['policy_sha256'], child_signals=0))
        original_publish = parent.publish

        def publish(repository, published_config, message):
            question_shape(message)
            if proof['physical'] == 1:
                raw.release(base.read(raw.MAIN_RECEIPT))
            receipt = original_publish(repository, published_config, message)
            base.write(output / ('R184_PUBLISHED_' + receipt['id'] + '.json'), dict(publication=receipt,
                message_sha256=hashlib.sha256(message.encode()).hexdigest(), observed_unix=time.time(),
                baseline_republished=False, policy_sha256=proof['policy_sha256']))
            return receipt

        parent.publish = publish
        reference = observed['reference']
        previous_anchor = PREVIOUS[proof['physical']] / 'parent/FIRST_RENDERED_EXPOSURE.json'
        anchor = base.read(previous_anchor) if previous_anchor.exists() else None
        for sequence in range(18000):
            if time.time() >= base.WALL:
                break
            observed = base.snapshot(reader(proof), reference)
            reference, state = observed['reference'], observed['snapshot']
            base.write(output / f'POLL_{sequence:06d}.json', observed)
            for path in output.glob('R184_PUBLISHED_*.json'):
                publication = base.read(path)
                identifier = publication['publication']['id']
                delivered = state['delivered'].get(identifier)
                target = output / ('R184_RENDERED_' + identifier + '.json')
                if delivered and not target.exists():
                    base.require(delivered['inbox_sha256'] == publication['publication']['sha256'], 'exact_R184_render')
                    base.write(target, dict(publication=publication, rendered=delivered, observed_unix=time.time()))
                    if anchor is None:
                        anchor = dict(baseline_completed_sleeps=delivered['sleep_count'], first_render=delivered,
                            third_sleep_target=delivered['sleep_count'] + 3,
                            fourth_sleep_target=delivered['sleep_count'] + 4, observed_unix=time.time())
                        base.write(output / 'FIRST_RENDERED_EXPOSURE.json', anchor)
            held = phase_hold(proof['physical'], anchor, state)
            raw_status = raw.ready(state) if proof['physical'] == 1 else 'READY_FOR_EXISTING_B_RESPONSE_CLOCK'
            if held:
                status = dict(status='PARENT_WITHDRAWAL_ONE_SLEEP')
            elif raw_status != 'READY_FOR_EXISTING_B_RESPONSE_CLOCK':
                status = dict(status=raw_status, model_calls=0)
            else:
                status = policy.tick(base.REPO, config, output, seed, state)
            base.write(output / f'STATUS_{sequence:06d}.json', dict(status, observed_unix=time.time(),
                sleep_count=state['sleep_count'], policy_bound=True))
            if status['status'] in ('PUBLICATION_UNKNOWN', 'VALIDATION_FAILED', 'PROVIDER_FAILED'):
                base.write(output / 'ATTENTION_REQUIRED.json', dict(status=status['status'], no_implicit_retry=True))
                return status
            time.sleep(5)


def activate(lane):
    config, proof = checked(lane)
    previous = PREVIOUS[proof['physical']]
    actor = proof['predecessor']
    base.same_parent(actor, base.identity(actor['pid']))
    descriptor, paused, terminated = os.pidfd_open(actor['pid']), False, False
    try:
        for attempt in range(60):
            base.same_parent(actor, base.identity(actor['pid']))
            if base.children(actor['pid']):
                time.sleep(.25)
                continue
            signal.pidfd_send_signal(descriptor, signal.SIGSTOP)
            paused = True
            time.sleep(.05)
            if not base.children(actor['pid']):
                break
            signal.pidfd_send_signal(descriptor, signal.SIGCONT)
            paused = False
        base.require(paused and base.identity(actor['pid'])['state'] in ('T', 't'), 'quiet_existing_parent_only')
        latest = base.read(sorted((previous / 'parent').glob('POLL_*.json'))[-1])
        observed = base.snapshot(reader(proof), latest['reference'])
        base.require(observed['snapshot']['caught_up'], 'caught_up_source_not_static_head_gate')
        policy, parent = load(lane)
        seed = errata.preserved_seed(previous, policy, observed['snapshot'])
        base.require(not any(attempt['result']['status'] == 'PUBLICATION_UNKNOWN' for attempt in seed['attempts']),
            'unknown_publication_requires_reconciliation_no_replay')
        base.write(lane / 'SEED.json', seed)
        base.write(lane / 'TAKEOVER_SNAPSHOT.json', observed)
        environment = dict(part.decode().split('=', 1) for part in Path('/proc', str(actor['pid']), 'environ').read_bytes().split(b'\0') if b'=' in part)
        environment.update(CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(lane / 'source'))
        command = [sys.executable, '-B', str(Path(__file__).resolve()), 'serve', '--lane', str(lane)]
        execution = subprocess.run(command + ['--preflight'], cwd=lane / 'source', env=environment,
            capture_output=True, text=True, timeout=45)
        base.require(execution.returncode == 0, 'actual_bound_CPU:' + execution.stderr[-1500:])
        base.write(lane / 'CPU.json', json.loads(execution.stdout))
        base.require(errata.preserved_seed(previous, policy, observed['snapshot']) == seed, 'settled_attempt_ledger_unchanged')
        base.write(lane / 'PARENT_RETIREMENT_INTENT.json', dict(predecessor=actor, observed_unix=time.time(), child_signals=0))
        signal.pidfd_send_signal(descriptor, signal.SIGTERM)
        signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        paused, terminated = False, True
        base.require(bool(select.select([descriptor], [], [], 10)[0]), 'old_parent_exited')
        with (lane / 'PARENT.log').open('x') as log:
            process = subprocess.Popen(command, cwd=lane / 'source', env=environment, stdin=subprocess.DEVNULL,
                stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        result = dict(status='R184_PARENT_STARTED_NOT_A_PUBLICATION', physical=proof['physical'],
            pid=process.pid, command=command, observed_unix=time.time(), child_signals=0)
        base.write(lane / 'DISPATCHED.json', result)
        return result
    finally:
        if paused and not terminated:
            signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        os.close(descriptor)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('stage', 'activate', 'serve'))
    parser.add_argument('--lane', type=Path, required=True)
    parser.add_argument('--physical', type=int, choices=tuple(ARMS))
    parser.add_argument('--preflight', action='store_true')
    arguments = parser.parse_args()
    selected = arguments.lane.resolve()
    result = (stage(selected, arguments.physical) if arguments.action == 'stage' else
        activate(selected) if arguments.action == 'activate' else serve(selected, arguments.preflight))
    print(json.dumps(result, sort_keys=True))
