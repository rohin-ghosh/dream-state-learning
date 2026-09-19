"""Bounded public TRAIN feedback collection; no optimizer, admission, or fit."""

import argparse
from contextlib import nullcontext
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from organism_v6 import orch_persist_code as ledger


NATIVE_END = 1789491300
EXTERNAL_END = 1789491420
UUID = 'GPU-7c213554-a6c0-5c5a-1117-0422c8eee4ed'
BRANCHES = ('CHILD_PUBLIC_FEEDBACK', 'CHILD_NO_FEEDBACK', 'BASE_PUBLIC_FEEDBACK')
SOURCE = 'R109_SELF_PUBLIC_FEEDBACK_REPAIR'
PUBLIC_KEYS = {'schema', 'input', 'source', 'hidden_tests_exposed', 'public_tests_executed',
               'expression', 'observed', 'error'}


def require(value, reason):
    if not value:
        raise ValueError(reason)


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def identity(pid=None):
    directory = Path('/proc') / str(os.getpid() if pid is None else pid)
    fields = (directory / 'stat').read_text().rsplit(')', 1)[1].split()
    return dict(pid=int(directory.name), uid=directory.stat().st_uid,
                start_ticks=fields[19], boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())


def public_probe(task):
    return [task['threshold'] - 1, task['threshold'], task['threshold'] + 1,
            task['low'] - 1, task['high'] + 1, 0, 0]


def execute_public(task, text):
    values = public_probe(task)
    receipt = dict(schema='R109_PUBLIC_TRAIN_EXECUTION_V2', input=values,
                   source='ACTUAL_PUBLIC_INPUT_INTERPRETER',
                   hidden_tests_exposed=False, public_tests_executed=1)
    try:
        action, reasoning = ledger.parse_action(text)
        require(set(action) == {'expression'}, 'expression_required')
        receipt['expression'] = action['expression']
        receipt['observed'] = ledger.evaluate(action['expression'], values)
    except (ValueError, TypeError, SyntaxError, KeyError) as error:
        receipt.update(error=type(error).__name__ + ': ' + str(error))
    return receipt


def verify_train(task, text):
    try:
        action, reasoning = ledger.parse_action(text)
        require(set(action) == {'expression'}, 'expression_required')
        return ledger.check_expression(task, action['expression'])
    except (ValueError, TypeError, SyntaxError, KeyError) as error:
        return dict(success=False, error=type(error).__name__ + ': ' + str(error))


def messages(task, branch, previous=None, feedback=None):
    require(branch in BRANCHES, 'known_branch')
    system = ('Solve the actual task using only its specification and received evidence. '
              'You may check or revise a consequential uncertainty, or stop when satisfied. '
              'Do not invent tests, observations or a correction. No required length or headings. '
              'The token budget is a limit, not a target. Finish within it.')
    prompt = (task['spec'] + '\n' + ledger.HELPER_SPEC + '\n'
              'One public TRAIN probe input is: ' + json.dumps(public_probe(task)) + '.\n'
              'Produce a general expression, not a constant answer for this one input. '
              'Finish with exactly one expression JSON object on the last line.')
    result = [dict(role='system', content=system), dict(role='user', content=prompt)]
    if previous is not None:
        if branch == 'CHILD_NO_FEEDBACK':
            text = ('No execution feedback or new observation is supplied. You may revisit your '
                    'own attempt if useful, or finish. Do not manufacture a check or correction.')
        else:
            require(feedback is not None and set(feedback) <= PUBLIC_KEYS
                    and feedback['hidden_tests_exposed'] is False
                    and feedback['input'] == public_probe(task), 'actual_public_feedback_whitelist')
            text = ('Actual execution of your previous expression on the public TRAIN probe:\n' +
                    json.dumps(feedback, sort_keys=True) + '\nUse this evidence if it matters. '
                    'You may correct your own expression, check a consequential cause, or finish. '
                    'No other test feedback or gold expression is provided.')
        result.extend([dict(role='assistant', content=previous), dict(role='user', content=text +
                       '\nFinish with exactly one expression JSON object on the last line.')])
    return result


def correction(before, after, public, first_text, last_text):
    changed = first_text != last_text
    verified = before.get('success') is False and after.get('success') is True and changed
    interface = verified and any(label in public.get('error', '') for label in
                                ('identifier', 'arity', 'syntax', 'SyntaxError', 'JSON', 'Expecting'))
    return dict(verified_failed_to_passed_candidate=verified,
                interface_repair_candidate=bool(interface),
                behavior_repair_candidate=bool(verified and not interface),
                semantic_review='PENDING', functional_admission=False,
                metacognition_claim=False, persistence_claim=False, fit_updates=0)


def validate_plan(plan, now):
    require(plan['source_label'] == SOURCE and plan['physical'] == 7 and plan['uuid'] == UUID, 'exact_allocation')
    require(plan['max_responses'] == 96 and plan['task_count'] == 16 and plan['max_new_tokens'] == 8192, 'exact_finite_budget')
    require(plan['native_end_unix'] == NATIVE_END and plan['external_end_unix'] == EXTERNAL_END
            and now < NATIVE_END < EXTERNAL_END, 'fixed_deadline_no_reset')
    require(plan['parents'] == plan['optimizer_steps'] == plan['fit_allowed'] == 0, 'collection_only')


def verified(root):
    plan = read(root / 'PLAN.json')
    validate_plan(plan, time.time())
    for path, digest in plan['source_files'].items():
        require(sha(path) == digest, 'frozen_source_drift')
    require(sha(root / 'TASKS.json') == plan['tasks_sha256'], 'task_freeze')
    require(sha(root / 'SEED.json') == plan['seed_sha256'], 'seed_freeze')
    return plan


def collect(root):
    from gpu import orch_guided_native as native
    from gpu.orch_r107_capability_run import readonly_condition
    from gpu.orch_rich_hot_node2_exhaustion_v3 import Engine
    from organism_v6 import orch_guided_bridge as bridge
    plan = verified(root)
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == UUID, 'single_exact_physical7')
    require(not (root / 'NATIVE_START.json').exists(), 'single_use_no_retry')
    write(root / 'NATIVE_START.json', dict(identity=identity(), time_unix=time.time(), plan_sha256=sha(root / 'PLAN.json')))
    seed = read(root / 'SEED.json')
    adapter = bridge.AdapterIdentity.from_document(seed['adapter'])
    binding = bridge.StageBinding(root.name, bridge.ARMS[1], 0, 'sealed_readout', adapter,
                                  False, True, sha(root / 'PLAN.json'))

    def check(label):
        if time.time() >= NATIVE_END:
            raise TimeoutError('fixed_native_end:' + label)

    loaded = native.load_stage(binding, model_dir=plan['model_dir'], device='cuda:0', gpu_uuid=UUID,
                               context=native.StageContext(), check=check, engine_factory=Engine)
    write(root / 'LOADED.json', dict(identity=identity(), adapter=loaded.observed.document(),
                                   optimizer_count=0, prior_optimizer_sha256=seed['optimizer_sha256'],
                                   time_unix=time.time()))
    count = 0
    completed = []
    status = 'COMPLETE'
    try:
        for task in read(root / 'TASKS.json')['tasks']:
            for branch in BRANCHES:
                check('episode')
                episode = root / 'episodes' / task['id'] / branch
                episode.mkdir(parents=True, exist_ok=False)
                condition = 'LORA_OFF' if branch == 'BASE_PUBLIC_FEEDBACK' else 'LORA_ON'
                branch_result = []
                previous = None
                feedback = None
                for stage in ('draft', 'continuation'):
                    check('response')
                    require(count < 96, 'response_ceiling')
                    prefix = messages(task, branch, previous, feedback)
                    prefix_tokens = loaded.engine.prompt_tokens(prefix)
                    budget = min(8192, 32768 - len(prefix_tokens))
                    require(budget > 0, 'no_context_trim')
                    count += 1
                    intent = dict(source_label=SOURCE if branch != 'BASE_PUBLIC_FEEDBACK' else 'R109_BASE_PUBLIC_FEEDBACK_REFERENCE',
                                  split='TRAIN', source_task_id=task['source_task_id'], task_id=task['id'],
                                  branch=branch, stage=stage, messages=prefix, reserved_response=count,
                                  seed_state_sha256=adapter.state_sha256, lora_enabled=condition == 'LORA_ON',
                                  base_sha256=adapter.base_sha256, task_manifest_sha256=plan['tasks_sha256'],
                                  source_manifest_sha256=plan['source_manifest_sha256'],
                                  max_new_tokens=budget, started_unix=time.time(), parents=0,
                                  optimizer_count=0, trainingAllowed=False)
                    write(episode / (stage + '.INTENT.json'), intent)
                    with readonly_condition(loaded.engine.model, condition):
                        response = loaded.engine.generate(prefix, max_new_tokens=budget)
                    write(episode / (stage + '.CALL.json'), dict(intent, response=response, finished_unix=time.time()))
                    public = execute_public(task, response['raw'])
                    verification = verify_train(task, response['raw'])
                    write(episode / (stage + '.PUBLIC.json'), public)
                    write(episode / (stage + '.TRAIN_VERIFY.json'), verification)
                    branch_result.append((response, public, verification))
                    previous, feedback = response['raw'], public
                before, after = branch_result
                result = correction(before[2], after[2], before[1], before[0]['raw'], after[0]['raw'])
                result.update(task_id=task['id'], source_task_id=task['source_task_id'], branch=branch,
                              terminal_pair=all(item[0]['terminal'] and not item[0]['truncated'] for item in branch_result),
                              before_success=before[2]['success'], after_success=after[2]['success'],
                              source_calls={stage:sha(episode / (stage + '.CALL.json')) for stage in ('draft','continuation')},
                              parent_text_masked=True, time_unix=time.time())
                if not result['terminal_pair']:
                    result.update(verified_failed_to_passed_candidate=False, behavior_repair_candidate=False,
                                  interface_repair_candidate=False, rejection='incomplete_or_cap_hit')
                write(episode / 'COMPLETE.json', result)
                completed.append(result)
                temporary = root / 'PROGRESS.pending.json'
                write(temporary, dict(responses_reserved=count, completed_episodes=len(completed),
                                      results=completed, observed_unix=time.time(), native_end_unix=NATIVE_END))
                os.replace(temporary, root / 'PROGRESS.json')
        loaded.verify_unchanged()
    except BaseException as error:
        status = 'FAILED_OR_BOUNDED_STOP'
        write(root / 'FAILURE.json', dict(error=type(error).__name__ + ': ' + str(error),
                                        responses_reserved=count, time_unix=time.time(), retry_allowed=False))
        raise
    finally:
        write(root / 'TERMINAL.json', dict(status=status, responses_reserved=count, completed_episodes=len(completed),
                                          results=completed, time_unix=time.time(), optimizer_steps=0,
                                          rows_admitted=0, parents=0, retry_allowed=False))


def guard(root):
    from gpu.orch_rich_hot_node2_scan import scan
    plan = verified(root)
    require(os.environ.get('CUDA_VISIBLE_DEVICES', '') == '', 'CPU_guard_CVD_empty')
    require(not (root / 'GUARD_START.json').exists(), 'single_use_guard_no_retry')
    ready = read(root / 'PRE_GPU.json')
    require(ready['cpu_passed'] is True and ready['plan_sha256'] == sha(root / 'PLAN.json'), 'dated_builder_receipt')
    release = read(root / 'RELEASE.json')
    require(release['status'] == 'RELEASED' and sha(release['terminal']['path']) == release['terminal']['sha256'], 'actual_old_release')
    for pid in release['old_group_pids']:
        require(not (Path('/proc') / str(pid)).exists(), 'old_group_not_released')
    require(sha(root / 'RELEASE.json') == ready['release_sha256'], 'release_bound')
    write(root / 'GUARD_START.json', dict(identity=identity(), time_unix=time.time(), plan_sha256=sha(root / 'PLAN.json')))
    snapshot = scan(7, Path(plan['service_identity']))
    snapshot.pop('host', None)
    write(root / 'ADMISSION.json', snapshot)
    require(snapshot['clear'] and snapshot['scanner_euid'] == 0 and snapshot['gpu']['uuid'] == UUID,
            'strict_physical7_admission')
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES=UUID, HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                       PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', TOKENIZERS_PARALLELISM='false')
    with (root / 'NATIVE.log').open('x') as log:
        child = subprocess.Popen([sys.executable, '-B', str(Path(__file__).resolve()), 'collect', '--root', str(root)],
                                 env=environment, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                                 start_new_session=True)
        expected = identity(child.pid)
        write(root / 'LAUNCH.json', dict(identity=expected, physical=7, uuid=UUID, time_unix=time.time(),
                                       native_end_unix=NATIVE_END, external_end_unix=EXTERNAL_END))
        try:
            child.wait(timeout=max(.001, NATIVE_END - time.time()))
        except subprocess.TimeoutExpired:
            require(identity(child.pid) == expected, 'owned_native_identity')
            write(root / 'CUTOFF.json', dict(identity=expected, time_unix=time.time(), reason='FIXED_NATIVE_1655'))
            os.killpg(child.pid, signal.SIGTERM)
            try:
                child.wait(timeout=max(.001, min(15, EXTERNAL_END - time.time())))
            except subprocess.TimeoutExpired:
                require(identity(child.pid) == expected, 'owned_kill_identity')
                os.killpg(child.pid, signal.SIGKILL)
                child.wait(timeout=10)
    write(root / 'GUARD_TERMINAL.json', dict(returncode=child.returncode, identity=expected,
                                           time_unix=time.time(), retry_allowed=False, calls_not_replayed=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('guard', 'collect'))
    parser.add_argument('--root', type=Path, required=True)
    options = parser.parse_args()
    (guard if options.action == 'guard' else collect)(options.root)
