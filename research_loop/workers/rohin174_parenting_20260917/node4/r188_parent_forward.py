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
PREVIOUS = {physical: HOME / 'activation_r184_20260917T2248Z' / f'physical{physical}' for physical in (0, 3, 4)}
ARMS = {0: ('B', 2), 3: ('D', 3), 4: ('A', 1)}
EXAMPLES_SHA = '19e813b21d2b43d3ea274eb1783d7f2a2ce0f5b703f6fda94051d5cda21c978f'
POLICY = 'R184/R185 forward parent policy, replacing the prior rhetorical style but not its cadence or evidence rules:\nAt the next legitimate parent turn, give one short attributed worked-method example from the supplied R188 examples, followed by exactly three numbered question lines, numbered 1., 2., 3., each ending in one question mark. The example must be a single paragraph beginning exactly with one of: Reported example (Rohin; C2): or Reported example (Rohin; Pilot): or Reported example (Rohin; Raw):. Do not supply the recipient task answer or repeat an introductory baseline. Keep the entire message within the existing arm cap; for the 90-word D arm keep the example very short. The example is reported, not recipient evidence.\nGround all three questions in this child\'s current object and actual evidence. Probe effort in BOTH directions: what concrete uncertainty would more thinking resolve, versus what uncertainty would a small real attempt resolve? More thought is not automatically better, and acting sooner is not automatically better. Sometimes staying with the present approach is justified. Leave that choice to the child.\nQuestion1 should ask which current uncertainty is decision-relevant and whether further thought or an attempt would distinguish it. Question2 should ask what the child chooses to do or deliberately keep doing, with its expected consequence. Question3 should ask what actual observation would support staying, thinking more, or trying differently. These are action-guiding questions, not supplied answers or an order to switch tasks.\nDo not invent executor availability, results, peers, or observations. Existing kernel and raw external executors remain unavailable here. An intended attempt is not an executed result. Preserve strict private evidence, lowercase object IDs, disposition/next_task consistency and all existing validation. Never duplicate an original or Fable baseline, retry PUBLICATION_UNKNOWN, or force a call while an accepted publication awaits rendering.\nValidator clarification, not a rule change: if disposition is set_aside, include an explicit English release such as "set aside", state "unresolved", and include the exact private next_task in the message. That next_task must retain the exact continuity.chosen_object.quote; the message must include keep/continue/stay with/within. With no actual rendered Tool receipt, say "not yet verified". If disposition is continue, private next_task and continuity stay null. Never invent an object alias to escape the existing object-turn budget, and never fabricate evidence. These constraints can be expressed inside the three questions; do not silently normalize a rejected response.\n\nR188_REPORTED_WORKED_EXAMPLES_V1\nSource: Rohin message188, relayed by Fable, September17,2026.\nC2 separating case: Rohin reports C2 compared competing formulas using a separating k=3 case: state what each predicts, make the actual calculation, compare the observation, revise the judgment, and carry the correction into the next choice. This is a reported example, not a new result or a numerical answer for this child.\nPilot receipt discipline: The pilot example is: "no execution receipt is visible". Distinguish a proposed action, an attempted action, a returned receipt, and evidence that the intended claim passed. A successful process exit alone does not verify its answer.\nRaw Next-Steps handshake: Rohin cites the raw child\'s Next-Steps handshake: carry an unfinished next step forward and check what actually happened before reporting progress. Do not invent its transcript or an execution outcome; this is the reported pattern.\nUse one short worked example at a time, attributed to its source child, then ask the recipient to apply the method to its OWN current object. Do not copy another child\'s object, assert that the recipient did the example, supply its task answer, or make a recurring checklist. Preserve English, the existing message cap, parent attribution and masked training status. Do not repeat a queued baseline or inject into a fixed comparison during its declared parent-withdrawal window. Ask both ways: should you keep thinking, or are you better off with new data? If data is becoming redundant, perhaps think more. Sometimes staying with the problem is right. Show how the observation changes the next action, not merely the vocabulary.\n'


def question_shape(message):
    lines = [line.strip() for line in message.splitlines() if line.strip()]
    prefixes = ('Reported example (Rohin; C2): ', 'Reported example (Rohin; Pilot): ', 'Reported example (Rohin; Raw): ')
    base.require(len(lines) == 4 and lines[0].startswith(prefixes), 'R188_one_attributed_example_then_three_questions')
    base.require(all(re.fullmatch(str(index) + r'\. [^?\n]+\?', line)
        for index, line in enumerate(lines[1:], 1)), 'R184_three_question_lines_no_answer_prose')
    base.require(not message.endswith(raw.BASELINE_END), 'never_duplicate_baseline')


def validation_recovery(output, state):
    attempt = output / f"parent_{state['request_count']:012d}"
    source = base.read(attempt / 'SOURCE.json')
    result = base.read(attempt / 'RESULT.json')
    base.require(result['status'] == 'VALIDATION_FAILED' and 'publication' not in result
        and not (attempt / 'PUBLISH_INTENT.json').exists(), 'only_known_prepublication_validation_failure')
    base.require(result['source_sha256'] == base.sha(attempt / 'SOURCE.json')
        and source['head_sha256'] == state['head_sha256']
        and source['response_count'] == state['response_count'], 'exact_failed_source_not_replayed')
    return dict(status='AWAIT_FRESH_RESPONSE_AFTER_VALIDATION_FAILURE',
        error=result.get('error'), result_sha256=base.sha(attempt / 'RESULT.json'),
        failed_source_head=source['head_sha256'], failed_response_count=source['response_count'],
        same_source_retry=False, publication_attempted=False, observed_unix=time.time())


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
    base.require(lane.parent.parent == HOME and lane.parent.name.startswith('activation_r188_'), 'owned_R184_parent_output')
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
    base.require(physical in ARMS, 'R188_only_parents_0_3_4_raw1_untouched')
    previous = PREVIOUS[physical]
    base.checked_bundle(previous)
    base.require(not lane.exists() and lane.parent.parent == HOME
        and lane.parent.name.startswith('activation_r188_') and lane.name == f'physical{physical}', 'new_owned_lane')
    lane.mkdir(parents=True)
    shutil.copytree(previous / 'source', lane / 'source')
    for name in ('CONFIG.json', 'PARENT_METADATA_ERRATA_V1.md', 'orch_r175_parent_response.py'):
        shutil.copyfile(previous / name, lane / name)
    base.write(lane / 'PLAN.json', dict(physical=physical, arm=ARMS[physical][0], root=base.ROOTS[physical],
        one_corrective_call=False))
    predecessor = base.read(previous / 'parent/STARTED.json')['actor']
    older = Path(base.read(previous / 'BINDING.json')['previous_lane'])
    base.require(older.parent.parent == HOME and older.name == f'physical{physical}', 'same_life_previous_exposure')
    anchors = [path / 'parent/FIRST_RENDERED_EXPOSURE.json' for path in (previous, older)]
    anchor = next((path for path in anchors if path.exists()), None)
    proof = dict(physical=physical, wrapper_sha256=base.sha(__file__), previous_lane=str(previous),
        predecessor=predecessor, config_sha256=base.sha(lane / 'CONFIG.json'),
        source_files={str(path.relative_to(lane / 'source')): base.sha(path)
            for path in (lane / 'source').rglob('*') if path.is_file()},
        raw_release_sha256=None, exposure_anchor_path=str(anchor) if anchor else None,
        exposure_anchor_sha256=base.sha(anchor) if anchor else None,
        policy_sha256=hashlib.sha256(POLICY.encode()).hexdigest(), Main_examples_sha256=EXAMPLES_SHA,
        scope='R188_next_fresh_response_only_keep_caps_English_object_rules_no_child_changes')
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
            base.write(output / ('R188_PUBLISHED_' + receipt['id'] + '.json'), dict(publication=receipt,
                message_sha256=hashlib.sha256(message.encode()).hexdigest(), observed_unix=time.time(),
                baseline_republished=False, policy_sha256=proof['policy_sha256']))
            return receipt

        parent.publish = publish
        reference = observed['reference']
        previous_anchor = proof['exposure_anchor_path']
        base.require(previous_anchor is None or base.sha(previous_anchor) == proof['exposure_anchor_sha256'], 'preserved_first_exposure_clock')
        anchor = base.read(previous_anchor) if previous_anchor else None
        for sequence in range(18000):
            if time.time() >= base.WALL:
                break
            observed = base.snapshot(reader(proof), reference)
            reference, state = observed['reference'], observed['snapshot']
            base.write(output / f'POLL_{sequence:06d}.json', observed)
            for path in output.glob('R188_PUBLISHED_*.json'):
                publication = base.read(path)
                identifier = publication['publication']['id']
                delivered = state['delivered'].get(identifier)
                target = output / ('R188_RENDERED_' + identifier + '.json')
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
            if status['status'] == 'VALIDATION_FAILED':
                base.write(output / f'VALIDATION_RECOVERY_{sequence:06d}.json', validation_recovery(output, state))
            if status['status'] in ('PUBLICATION_UNKNOWN', 'PROVIDER_FAILED'):
                base.write(output / 'ATTENTION_REQUIRED.json', dict(status=status['status'], no_implicit_retry=True))
                return status
            time.sleep(5)


def activate(lane):
    config, proof = checked(lane)
    physical = proof['physical']
    previous = PREVIOUS[physical]
    actor = proof['predecessor']
    base.require(not Path('/proc', str(actor['pid'])).exists(), 'confirmed_stopped_owned_predecessor_only')
    donor_lane = HOME / 'activation_r184_20260917T2248Z/physical1'
    donor = base.read(donor_lane / 'parent/STARTED.json')['actor']
    base.same_parent(donor, base.identity(donor['pid']))
    environment = dict(part.decode().split('=', 1) for part in
        Path('/proc', str(donor['pid']), 'environ').read_bytes().split(b'\0') if b'=' in part)
    base.same_parent(donor, base.identity(donor['pid']))
    environment.update(CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(lane / 'source'))
    with (HOME / f'R175_PARENT_{physical}.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        latest = base.read(sorted((previous / 'parent').glob('POLL_*.json'))[-1])
        reference = latest['reference']
        for sequence in range(8):
            observed = base.snapshot(reader(proof), reference)
            reference = observed['reference']
            if observed['snapshot']['caught_up']:
                break
        base.require(observed['snapshot']['caught_up'], 'bounded_verified_current_snapshot')
        policy, parent = load(lane)
        seed = errata.preserved_seed(previous, policy, observed['snapshot'])
        base.require(not any(attempt['result']['status'] == 'PUBLICATION_UNKNOWN' for attempt in seed['attempts']),
            'unknown_publication_requires_reconciliation_no_replay')
        base.write(lane / 'SEED.json', seed)
        base.write(lane / 'TAKEOVER_SNAPSHOT.json', observed)
        base.write(lane / 'PREVIOUS_VALIDATION_FAILURES.json', dict(
            attempts=[attempt for attempt in seed['attempts'] if attempt['result']['status'] == 'VALIDATION_FAILED'],
            future_source_only=True, observed_unix=time.time()))
        command = [sys.executable, '-B', str(Path(__file__).resolve()), 'serve', '--lane', str(lane)]
        execution = subprocess.run(command + ['--preflight'], cwd=lane / 'source', env=environment,
            capture_output=True, text=True, timeout=45)
        base.require(execution.returncode == 0, 'actual_bound_CPU:' + execution.stderr[-1500:])
        base.write(lane / 'CPU.json', json.loads(execution.stdout))
        base.require(errata.preserved_seed(previous, policy, observed['snapshot']) == seed,
            'settled_attempt_ledger_unchanged')
        base.write(lane / 'ACTIVATION_INTENT.json', dict(predecessor=actor, predecessor_absent=True,
            provider_environment_donor_pid=donor['pid'], donor_unmodified=True,
            observed_unix=time.time(), native_signals=0, raw1_mutations=0))
    with (lane / 'PARENT.log').open('x') as log:
        process = subprocess.Popen(command, cwd=lane / 'source', env=environment, stdin=subprocess.DEVNULL,
            stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    result = dict(status='R188_PARENT_STARTED_NOT_A_PUBLICATION', physical=physical,
        pid=process.pid, command=command, observed_unix=time.time(), child_signals=0, raw1_mutations=0)
    base.write(lane / 'DISPATCHED.json', result)
    return result


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
