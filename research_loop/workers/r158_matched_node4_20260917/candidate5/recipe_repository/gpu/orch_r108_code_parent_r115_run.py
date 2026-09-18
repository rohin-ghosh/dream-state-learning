"""R115 resident F3 lifecycle. Raw and all reservations stay on the node."""

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from gpu import orch_r108_code_parent_r114_adapter as adapter
from gpu import orch_r110_claude_broker as broker
from organism_v6 import orch_r108_code_parent_r115 as environment


policy = environment.policy
FINAL_CUT = policy.FINAL_CUT.timestamp()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.' + str(os.getpid()) + '.partial')
    with temporary.open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def write_new(path, value):
    policy.require(not Path(path).exists(), 'immutable_receipt_exists')
    write(path, value)


def check(root, phase):
    plan = read(root / 'PLAN.json')
    policy.require(time.time() < plan['hard_deadline_unix'] - 10, 'fixed_native_hard_wall')
    policy.require(os.environ.get('CUDA_VISIBLE_DEVICES') == plan['gpu_uuid'], 'exact_native_cvd')
    return plan


class Driver:
    def __init__(self, root, engine, *, evaluation=False):
        self.root, self.engine = Path(root), engine
        self.plan = read(self.root / 'PLAN.json')
        self.evaluation = evaluation
        self.settings = dict(effective_max_new_tokens=4096, status='DEFAULT_CAP')
        self.sleep_buffer = []
        self.sequence = 0

    def reserve(self, identifier, kind, *, split, phase, cycle, evaluation_origin=None):
        check(self.root, 'reserve')
        path = self.root / 'reservations' / (identifier + '.json')
        policy.require(not path.exists(), 'no_call_retry_or_replacement')
        cap = self.plan['native_cap'] if kind == 'NATIVE' else self.plan['parent_cap']
        row = dict(id=identifier, kind=kind, split=split, phase=phase, cycle=cycle,
            status='STARTED', started_unix=time.time(), evaluation_origin=evaluation_origin,
            routes=environment.capture_routes(split, phase, evaluation_origin=evaluation_origin))
        with (self.root / 'RESERVATION.lock').open('a') as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            issued = sum(read(item)['kind'] == kind for item in (self.root / 'reservations').glob('*.json'))
            policy.require(issued < cap, 'fixed_total_call_cap')
            write_new(path, row)
        return path, row

    def capture(self, identifier, task, phase, cycle, messages, cap, *, evaluation_origin=None):
        path, row = self.reserve(identifier, 'NATIVE', split=task['split'], phase=phase, cycle=cycle,
            evaluation_origin=evaluation_origin)
        try:
            row['response'] = self.engine.generate(messages, max_new_tokens=cap)
            row.update(status='COMPLETE', requested_generation_cap=cap,
                applied_reflection_settings=self.settings if phase in ('reflection', 'presleep') else None)
            return row
        except Exception as error:
            row.update(status='FAILED', error_type=type(error).__name__)
            return row
        finally:
            row['finished_unix'] = time.time()
            write(path, row)
            self.status()

    def batch(self, identifiers, tasks, phase, cycle, messages, cap):
        reserved = [self.reserve(identifier, 'NATIVE', split=task['split'], phase=phase,
            cycle=cycle, evaluation_origin=task['split']) for identifier, task in zip(identifiers, tasks)]
        try:
            responses = self.engine.generate_batch(messages, max_new_tokens=cap)
            policy.require(len(responses) == len(reserved), 'batch_denominator')
            for (path, row), response in zip(reserved, responses):
                row.update(status='COMPLETE', response=response, finished_unix=time.time())
                write(path, row)
        except Exception as error:
            for path, row in reserved:
                if row['status'] == 'STARTED':
                    row.update(status='FAILED', error_type=type(error).__name__, finished_unix=time.time())
                    write(path, row)
        self.status()
        return [row for path, row in reserved]

    def status(self):
        rows = [read(path) for path in (self.root / 'reservations').glob('*.json')]
        counts = Counter(row['kind'] + '_' + row['status'] for row in rows)
        write(self.root / 'STATUS.json', dict(observed_unix=time.time(), counts=dict(counts),
            generated_tokens=sum(len(row.get('response', {}).get('token_ids', [])) for row in rows),
            completed_cycles=len(list((self.root / 'cycles').glob('C*_COMPLETE.json'))),
            optimizer_steps=0, sleep_count=0, sleep_buffer_rows=len(self.sleep_buffer),
            semantic_behavior='UNASSESSED', comparison='PARENTING_SYSTEMS'))

    def parent(self, identifier, task, events, cycle, episode, phase):
        policy.require(not self.evaluation and task['split'] == 'TRAIN', 'no_evaluator_parent')
        path, record = self.reserve(identifier, 'PARENT', split='TRAIN', phase=phase, cycle=cycle)
        deadline = min(time.time() + 180, self.plan['hard_deadline_unix'] - 20)
        request = adapter.request(task, events, phase=phase, identifier=identifier,
            life_id=self.plan['life_id'], cycle=cycle, episode=episode, lane_deadline_unix=deadline)
        request['payload_sha256'] = broker.digest(request['payload'])
        request_path = self.root / 'parent_queue' / (identifier + '.request.json')
        write_new(request_path, request)
        response_path = request_path.with_name(identifier + '.response.json')
        response = None
        while time.time() < deadline:
            check(self.root, 'parent_wait')
            if response_path.exists():
                response = read(response_path)
                break
            time.sleep(1)
        guidance = ''
        record.update(status='MISSING', late=response is None, no_retry=True)
        if response is not None:
            record['response_sha256'] = sha(response_path)
            valid = response.get('id') == identifier and response.get('request_sha256') == broker.digest(request)
            valid = valid and response.get('payload_sha256') == request['payload_sha256'] and time.time() < deadline
            archive = response.get('transcript_receipt', {})
            archive_root = Path(archive.get('remote_root', '/nonexistent'))
            if not archive_root.is_absolute() or not archive_root.is_relative_to(self.root):
                valid = False
            files = archive.get('files', {})
            verified = bool(files) and all(Path(name).name == name and (archive_root / name).is_file()
                and sha(archive_root / name) == expected for name, expected in files.items())
            valid = valid and verified and response.get('actual_model') == self.plan['parent_model']
            record.update(provider_dispatched=response.get('provider_dispatched'),
                provider_actual_model=response.get('actual_model'),
                prompt_binding_sha256=broker.digest(response.get('prompt_binding')))
            if valid and response.get('status') in ('COMPLETE', 'SILENT'):
                record.update(status=response['status'], actual_model=response['actual_model'], late=False)
                self.settings = broker.reflection_call_settings(response, request, 4096,
                    config=read(self.root / 'BROKER_CONFIG.json'))
                record['reflection_settings'] = self.settings
                plan = response.get('plan') or {}
                guidance = plan.get('guidance', plan.get('message', '')) if record['status'] == 'COMPLETE' else ''
                record['guidance'] = guidance
        record['finished_unix'] = time.time()
        write(path, record)
        self.status()
        return guidance

    def reflection(self, identifier, task, cycle, messages):
        return self.capture(identifier, task, 'reflection', cycle, messages,
            self.settings['effective_max_new_tokens'])

    def open_turn(self, task, events, *, cycle, episode, parent_present, prefix):
        messages = policy.open_turn_messages(events, parent_present=parent_present, task_finished=True)
        record = self.capture(prefix + '_OPEN', task, 'open_turn', cycle, messages, 2048,
            evaluation_origin=None if parent_present else task['split'])
        if record['status'] != 'COMPLETE':
            return events
        events = list(events) + [environment.event(task, 'environment', policy.OPEN_TURN_PROMPT),
            environment.event(task, 'child', record['response']['raw'], completed=True)]
        observation = environment.inspect_environment(record['response']['raw'])
        write_new(self.root / 'environment' / (prefix + '_OPEN.json'), dict(observation=observation,
            source_call_sha256=sha(self.root / 'reservations' / (prefix + '_OPEN.json')),
            split=task['split'], attached_evaluation=not parent_present, sleep_eligible=False))
        if observation['status'] != 'NO_ENVIRONMENT_ACTION':
            text = json.dumps(observation, sort_keys=True)
            events.append(environment.event(task, 'environment', text, event_type='environment_feedback'))
            messages += [dict(role='assistant', content=record['response']['raw']), dict(role='user', content=text)]
            continuation = self.capture(prefix + '_OPEN_OBSERVE', task, 'open_observation', cycle,
                messages, 2048, evaluation_origin=None if parent_present else task['split'])
            if continuation['status'] == 'COMPLETE':
                events.append(environment.event(task, 'child', continuation['response']['raw'], completed=True))
        if parent_present:
            guidance = self.parent(prefix + '_OPEN_PARENT', task, events, cycle, episode, 'open_turn')
            if guidance:
                events.append(environment.event(task, 'parent', guidance))
                messages = [dict(role='assistant' if event['actor'] == 'child' else 'user', content=event['text']) for event in events]
                after = self.reflection(prefix + '_OPEN_REFLECTION', task, cycle, messages)
                if after['status'] == 'COMPLETE':
                    events.append(environment.event(task, 'child', after['response']['raw'], completed=True))
        return events


def episode(driver, task, cycle, episode_index):
    prefix = f'C{cycle:03d}_E{episode_index}'
    messages = policy.previous.messages(task)
    messages[-1]['content'] += '\n\n' + environment.AFFORDANCE
    events = [environment.event(task, 'environment', messages[-1]['content'])]
    first = driver.capture(prefix + '_ORIGINAL', task, 'episode', cycle, messages, 4096)
    if first['status'] != 'COMPLETE':
        return events
    events.append(environment.event(task, 'child', first['response']['raw'], completed=True))
    feedback = environment.visible_checker(task, first['response']['raw'])
    events.append(environment.event(task, 'checker', json.dumps(feedback, sort_keys=True), event_type='checker_output'))
    guidance = driver.parent(prefix + '_PARENT', task, events, cycle, episode_index, 'experience')
    if guidance:
        events.append(environment.event(task, 'parent', guidance))
    reflection_messages = [dict(role='system', content=policy.previous.PROMPTS['reflection'])]
    reflection_messages += [dict(role='assistant' if event['actor'] == 'child' else 'user', content=event['text']) for event in events]
    reflected = driver.reflection(prefix + '_REFLECTION', task, cycle, reflection_messages)
    if reflected['status'] == 'COMPLETE':
        events.append(environment.event(task, 'child', reflected['response']['raw'], completed=True))
    write_new(driver.root / 'triples' / (prefix + '.json'), dict(task_id=task['task_id'], cycle=cycle,
        events=events, parent_present=bool(guidance), classification='UNJUDGED', optimizer_steps=0))
    return driver.open_turn(task, events, cycle=cycle, episode=episode_index, parent_present=True, prefix=prefix)


def readouts(driver, cycle, scope):
    output = driver.root / 'readouts' / (f'C{cycle:03d}_' + scope)
    output.mkdir(parents=True, exist_ok=False)
    splits = ('DEV', 'FINAL') if scope == 'ZERO' else ('FINAL',) if scope == 'FINAL' else ('DEV',)
    dev_rows = None
    for split in splits:
        tasks = policy.tasks(split)
        rows = driver.batch([f'R{cycle:03d}_{scope}_{split}_{index}' for index in range(8)], tasks,
            'readout', cycle, [policy.previous.messages(task, 'readout') for task in tasks], 2048)
        outcomes = [dict(task_id=task['task_id'], status=row['status'],
            outcome=environment.score(task, row['response']['raw']) if row['status'] == 'COMPLETE' else None)
            for task, row in zip(tasks, rows)]
        write_new(output / (split + '.json'), dict(split=split, outcomes=outcomes, parent_visible=False,
            head_visible=split == 'DEV', sleep_eligible=False))
        if split == 'DEV':
            dev_rows = rows
    if scope != 'FINAL':
        tasks = policy.focused_tasks()
        driver.batch([f'R{cycle:03d}_{scope}_FOCUS_{index}' for index in range(2)], tasks,
            'focused', cycle, [policy.focused_messages(task) for task in tasks], 2048)
        if dev_rows and dev_rows[0]['status'] == 'COMPLETE':
            task = policy.tasks('DEV')[0]
            events = [environment.event(task, 'environment', task['prompt'] + '\n' + environment.AFFORDANCE),
                environment.event(task, 'child', dev_rows[0]['response']['raw'], completed=True)]
            driver.open_turn(task, events, cycle=cycle, episode=0, parent_present=False,
                prefix=f'R{cycle:03d}_{scope}_DEV')
        from gpu import astra_goal_quality_train as legacy
        material = read(driver.root / 'LEGACY_READOUT.json')
        facts = material['old_bank']
        policy.require(len(facts) == 16, 'all_sixteen_legacy_facts')
        legacy_tasks = [dict(split='LEGACY') for fact in facts]
        driver.batch([f'R{cycle:03d}_{scope}_OLD_{index}' for index in range(16)], legacy_tasks,
            'legacy', cycle, [legacy.memory.memory_messages(fact['event'], 0) for fact in facts], 512)
        cases = [next(case for case in material['held']['cases'] if case['kind'] == kind) for kind in ('true', 'fault')]
        driver.batch([f'R{cycle:03d}_{scope}_AUDIT_{index}' for index in range(2)], legacy_tasks[:2],
            'audit', cycle, [legacy.memory.audit._messages(case, False) for case in cases], 512)
    write_new(output / 'COMPLETE.json', dict(cycle=cycle, scope=scope, fresh_process=True,
        finished_unix=time.time(), optimizer_steps=0, sleep_buffer_rows=len(driver.sleep_buffer)))


def readout_process(root, cycle, scope):
    log = root / 'readouts' / (f'C{cycle:03d}_{scope}.log')
    log.parent.mkdir(exist_ok=True)
    with log.open('x') as stream:
        child = subprocess.Popen([sys.executable, '-B', '-m', 'gpu.orch_r108_code_parent_r115_run', 'readout', '--root', str(root),
            '--cycle', str(cycle), '--scope', scope], stdout=stream, stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL, start_new_session=False)
    return child


def load_engine(root):
    from transformers import AutoTokenizer
    from gpu.orch_r108_code_parent_r115_engine import Engine
    plan = read(root / 'PLAN.json')
    tokenizer = AutoTokenizer.from_pretrained(plan['model_dir'], local_files_only=True, trust_remote_code=False)
    tokenizer.padding_side = 'left'
    return Engine(plan['model_dir'], tokenizer, device='cuda:0', check=lambda phase: forward_check(root, phase))


def forward_check(root, phase):
    check(root, phase)


def native(root):
    plan = check(root, 'native_start')
    initial = readout_process(root, 0, 'ZERO')
    initial.wait()
    write_new(root / 'CYCLE_ZERO_PROCESS.json', dict(pid=initial.pid, returncode=initial.returncode,
        complete=(root / 'readouts/C000_ZERO/COMPLETE.json').exists(), finished_unix=time.time()))
    engine = load_engine(root)
    driver = Driver(root, engine)
    write_new(root / 'ACTOR_READY.json', dict(pid=os.getpid(), observed_unix=time.time(), base_sha256=engine.loaded_base_sha256,
        no_adapter=engine.no_adapter, lambda_actual='NOT_APPLIED', optimizer_steps=0))
    pending = []
    final_started = False
    try:
        for cycle in range(1, plan['cycles'] + 1):
            if time.time() >= plan['hard_deadline_unix'] - 120:
                break
            if time.time() >= FINAL_CUT and not final_started:
                for child in pending:
                    child.wait()
                pending = [readout_process(root, cycle, 'FINAL')]
                final_started = True
            tasks = policy.tasks('TRAIN')[(cycle - 1) * 2:cycle * 2]
            combined = []
            for episode_index, task in enumerate(tasks):
                combined.extend(episode(driver, task, cycle, episode_index))
            task = tasks[-1]
            meta_messages = [dict(role='assistant' if event['actor'] == 'child' else 'user', content=event['text']) for event in combined]
            meta_messages.append(dict(role='user', content=policy.previous.PROMPTS['presleep']))
            before = driver.capture(f'C{cycle:03d}_META', task, 'presleep', cycle, meta_messages,
                driver.settings['effective_max_new_tokens'])
            if before['status'] == 'COMPLETE':
                combined.append(environment.event(task, 'child', before['response']['raw'], completed=True))
                guidance = driver.parent(f'C{cycle:03d}_META_PARENT', task, combined, cycle, 1, 'presleep_metacognition')
                if guidance:
                    meta_messages += [dict(role='assistant', content=before['response']['raw']), dict(role='user', content=guidance)]
                    driver.reflection(f'C{cycle:03d}_META_REFLECTION', task, cycle, meta_messages)
            write_new(root / 'cycles' / f'C{cycle:03d}_COMPLETE.json', dict(cycle=cycle, completed_unix=time.time(),
                optimizer_steps=0, sleep_buffer_rows=len(driver.sleep_buffer), lambda_actual='NOT_APPLIED'))
            driver.status()
            if (root / 'RELEASE_AFTER_CYCLE.json').exists():
                request = read(root / 'RELEASE_AFTER_CYCLE.json')
                if request.get('receiver_ready') is True:
                    write_new(root / 'CYCLE_RELEASE_READY.json', dict(cycle=cycle, request_sha256=sha(root / 'RELEASE_AFTER_CYCLE.json')))
                    break
            for child in pending:
                child.wait()
            pending = [readout_process(root, cycle, 'DEV')]
        for child in pending:
            child.wait()
        engine.verify_base()
        write_new(root / 'COMPLETE.json', dict(finished_unix=time.time(), optimizer_steps=0, unchanged_base=True))
    finally:
        write_new(root / 'TERMINAL.json', dict(finished_unix=time.time(), optimizer_steps=0))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('native', 'readout'))
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--cycle', type=int, default=0)
    parser.add_argument('--scope', choices=('ZERO', 'DEV', 'FINAL'), default='ZERO')
    args = parser.parse_args()
    if args.phase == 'native':
        native(args.root)
    else:
        engine = load_engine(args.root)
        readouts(Driver(args.root, engine, evaluation=True), args.cycle, args.scope)
        engine.verify_base()
