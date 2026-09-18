"""R115 matched resident BASE grid lives with enacted open turns and sealed readouts."""

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import time
from types import SimpleNamespace

from organism_v6 import orch_r111_grid_v4 as policy
from gpu import orch_r110_claude_broker as broker
from gpu import orch_r110_admission as admission
from gpu import orch_r109_grid_run as original


require = policy.require
SOURCE = Path(__file__).resolve().parents[1]
PYTHON = '/localhome/local-rohing/v2/venv/bin/python'
HOST_SHA = '0cb7eb43862102b79ae0a30d2babfedfbf9598b31967a1a04122c3cf849c746d'
LEASE_END = datetime(2026, 9, 17, 4, 4, tzinfo=timezone.utc).timestamp()
END = policy.HARD_END_UNIX
TRAIN_END = policy.FINAL_UNIX - 300
MAX_NATIVE = 1858
MAX_PARENT = 298
EPISODE = policy.EPISODE_PROMPT + (
    ' You may inspect any grid cell by ending with INSPECT: row,column; '
    'the environment returns that cell and retains the observation. '
    'After the task ends, this same environment remains available for inspection or movement.')
JUDGE_SHA = '0466c6fa8bbd8c75f8e2d4c625498423835b2b5285e58c4f703069e8b6c532fd'


class TrainWindowClosed(Exception):
    pass


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def ref(path):
    return dict(path=str(path), sha256=sha(path))


def write(path, value, replace=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.' + str(os.getpid()) + '.tmp')
    with temporary.open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    if replace:
        os.replace(temporary, path)
    else:
        os.link(temporary, path); temporary.unlink()


def reserve(root, kind, detail):
    with (root / 'LEDGER.jsonl').open('a+') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        stream.seek(0)
        rows = [json.loads(line) for line in stream if line.strip()]
        number = 1 + sum(row['kind'] == kind for row in rows)
        require(number <= (MAX_NATIVE if kind == 'NATIVE' else MAX_PARENT), 'fixed_call_ceiling')
        require(time.time() < END, 'hard_end')
        stream.write(json.dumps(dict(kind=kind, number=number, reserved_unix=time.time(), **detail), sort_keys=True) + '\n')
        stream.flush(); os.fsync(stream.fileno())
        return number


def enacted_environment(task, state, raw, *, open_turn=False):
    before = deepcopy(state)
    inspection = re.search(r'^INSPECT:\s*(\d+)\s*,\s*(\d+)\s*$', raw, re.MULTILINE)
    if inspection:
        row, column = map(int, inspection.groups())
        inside = 0 <= row < len(task['cells']) and 0 <= column < len(task['cells'][0])
        value = task['cells'][row][column] if inside else 'OUT_OF_BOUNDS'
        after = deepcopy(state)
        if inside:
            after['observed'][f'{row},{column}'] = value
        if not open_turn:
            after['steps'] += 1
            after['done'] = after['done'] or after['steps'] >= policy.game.MAX_STEPS
        response = dict(operation='INSPECT', arguments=dict(row=row, column=column),
            value=value, enacted=True, child_received=True)
    else:
        action = policy.game.parse_action(raw)
        if action == 'INVALID' and open_turn:
            return deepcopy(state), dict(operation='NO_ENVIRONMENT_REQUEST', enacted=False,
                semantic_initiative='UNASSESSED', child_received=True)
        working = deepcopy(state)
        if open_turn:
            working['done'] = False
        after, transition = policy.game.transition(task, working, action)
        response = dict(operation='MOVE', arguments=dict(action=action), result=transition,
            enacted=True, child_received=True)
    response.update(before_observation=policy.public_observation(task, before),
        after_observation=policy.public_observation(task, after), post_task_exploration=open_turn,
        original_task_outcome_recomputed=False)
    return after, response


def carry_rows(records):
    for record in records:
        require(record['split'] == 'TRAIN' and record['purpose'] == 'reflection'
            and not record.get('attached_readout'), 'held_and_attached_open_never_carry')
    return deepcopy(records[-2:])


def reflection_settings(response, request, config, *, now=None):
    settings = broker.reflection_call_settings(response, request, 8192, config=config, now=now)
    if settings['status'] != 'BOUND_FOR_LANE_DECODER':
        settings['effective_max_new_tokens'] = 1024
    return settings


class Decoder(original.Engine):
    def batch(self, messages, cap):
        self.check('generation')
        encoded = [self.tokenizer.apply_chat_template(item, tokenize=True, add_generation_prompt=True,
            return_dict=False) for item in messages]
        require(all(len(tokens) + cap <= policy.DECODER['context_limit'] for tokens in encoded), 'uncropped_native_context')
        width = max(map(len, encoded))
        pad = self.tokenizer.pad_token_id
        if pad is None:
            pad = self.tokenizer.eos_token_id
        inputs = self.torch.tensor([[pad] * (width - len(tokens)) + tokens for tokens in encoded],
            dtype=self.torch.long, device=self.device)
        masks = self.torch.tensor([[0] * (width - len(tokens)) + [1] * len(tokens) for tokens in encoded],
            dtype=self.torch.long, device=self.device)
        config = self.transformers.GenerationConfig(do_sample=False, num_beams=1, use_cache=True,
            max_new_tokens=cap, no_repeat_ngram_size=4, repetition_penalty=1.0,
            eos_token_id=self.tokenizer.eos_token_id, pad_token_id=pad)
        with self.torch.inference_mode():
            generated = self.model.generate(input_ids=inputs, attention_mask=masks, generation_config=config)
        require(self.torch.equal(generated[:, :width], inputs), 'exact_native_prefix')
        result = []
        for index, tokens in enumerate(encoded):
            tail = generated[index, width:].tolist()
            terminal = self.tokenizer.eos_token_id in tail
            if terminal:
                tail = tail[:tail.index(self.tokenizer.eos_token_id) + 1]
            result.append(dict(raw=self.tokenizer.decode(tail[:-1] if terminal else tail,
                skip_special_tokens=False, clean_up_tokenization_spaces=False), token_ids=tail,
                prompt_tokens=len(tokens), terminal=terminal, truncated=not terminal and len(tail) == cap,
                requested_generation_cap=cap, full_prompt_prefix_verified=True))
        return result


def validate(root, gpu=False):
    config = read(root / 'CONFIG.json')
    require(root.resolve() == root and str(root) == config['root'], 'native_root')
    require(hashlib.sha256(socket.gethostname().encode()).hexdigest() == HOST_SHA, 'exact_node5')
    require(config['physical'] in (3, 7) and config['uuid'] == policy.LANES[config['life_id']]['uuid'], 'assigned_pair')
    require(time.time() < END <= LEASE_END - 21600, 'hard_end_lease_margin')
    require(sha(SOURCE / 'R115_SOURCE_SHA256.json') == config['source_manifest_sha256'], 'source_manifest_binding')
    for name, expected in read(SOURCE / 'R115_SOURCE_SHA256.json').items():
        require(not Path(name).is_absolute() and '..' not in Path(name).parts and sha(SOURCE / name) == expected,
            'immutable_native_source:' + name)
    for name, expected in config['inputs'].items():
        require(sha(root / name) == expected, 'immutable_input:' + name)
    require(config['base_sha256'] == policy.game.BASE_SHA and config['optimizer_steps'] == 0, 'BASE_context_only')
    require(sha(SOURCE / 'research_notes/R114_SHARED_JUDGE_PROMPT.md') == JUDGE_SHA, 'bound_judge')
    if gpu:
        require(os.environ.get('CUDA_VISIBLE_DEVICES') == config['uuid'], 'initial_GPU_UUID')
        require(('CUDA_VISIBLE_DEVICES=' + config['uuid']).encode() in Path('/proc/self/environ').read_bytes().split(b'\0'),
            'initial_process_visibility')
    return config


def scan(root):
    config = read(root / 'CONFIG.json')
    if os.geteuid() != 0:
        command = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
            'PYTHONPATH=' + str(SOURCE), 'python3', '-B', '-m', 'gpu.orch_r115_grid_native', 'scan', '--root', str(root)]
        return json.loads(subprocess.check_output(command, text=True, timeout=100))
    admission.minor.pinned.policy = SimpleNamespace(DEVICES={config['physical']: config['uuid']},
        HOST_SHA=HOST_SHA, require=require,
        allocation=lambda index: require(index == config['physical'], 'assigned_device_only'))
    return admission.scan(config['physical'], root / 'SERVICE_IDENTITY.json')


class Life:
    def __init__(self, root, engine, config, cycle):
        self.root, self.engine, self.config, self.cycle = root, engine, config, cycle
        self.events = []
        self.settings = dict(effective_max_new_tokens=1024, status='INITIAL_SHORT1024')
        self.last_request = None

    def calls(self, tasks, purpose, messages, cap, *, attached_readout=False):
        if not attached_readout and any(task['split'] == 'TRAIN' for task in tasks) and time.time() >= TRAIN_END:
            raise TrainWindowClosed('reserve_morning_FINAL_after_completed_response')
        reservations = []
        for task, prompt in zip(tasks, messages):
            number = reserve(self.root, 'NATIVE', dict(cycle=self.cycle, task_id=task['id'],
                split=task['split'], purpose=purpose, attached_readout=attached_readout))
            folder = 'sealed_readout_calls' if task['split'] == 'FINAL' else (
                'readout_calls' if attached_readout or task['split'] != 'TRAIN' else 'calls')
            path = self.root / folder / f'N{number:05d}.json'
            record = dict(status='STARTED', number=number, cycle=self.cycle, task_id=task['id'],
                split=task['split'], purpose=purpose, attached_readout=attached_readout, messages=prompt,
                cap=cap, base_sha256=policy.game.BASE_SHA, adapter=None, started_unix=time.time())
            write(path, record); reservations.append((path, record))
        results = self.engine.batch(messages, cap)
        for (path, record), response in zip(reservations, results):
            record.update(status='COMPLETE', response=response, finished_unix=time.time())
            write(path, record, replace=True)
            response['reference'] = ref(path)
            if record['split'] == 'TRAIN' and not attached_readout:
                self.event('child', response['raw'], ref(path)['sha256'])
        return results

    def generate(self, task, purpose, messages, cap, *, attached_readout=False):
        return self.calls([task], purpose, [messages], cap, attached_readout=attached_readout)[0]

    def event(self, actor, text, source_sha):
        sequence = len(self.events)
        event = policy.feedback_event(sequence, text, source_sha, child_received=True) if actor == 'environment' else (
            policy.previous.public_event(sequence, actor, text, source_sha))
        self.events.append(event)

    def ask(self, task, episode, phase):
        require(task['split'] == 'TRAIN', 'no_readout_parent')
        if time.time() >= TRAIN_END:
            raise TrainWindowClosed('no_late_parent_dispatch_before_FINAL')
        number = reserve(self.root, 'PARENT', dict(cycle=self.cycle, task_id=task['id'], phase=phase))
        identifier = f'P{number:04d}'
        request = policy.queue_request(identifier, self.config['life_id'], self.cycle, episode, phase,
            task, self.events, self.config['cohort_sha256'], time.time())
        path = self.root / 'parent_queue' / (identifier + '.request.json')
        write(path, request)
        response_path = path.with_name(identifier + '.response.json')
        response = None
        while time.time() < min(request['lane_deadline_unix'], END - 5):
            if response_path.exists():
                response = read(response_path); break
            time.sleep(.1)
        disposition = policy.previous.parent_disposition(request, response, time.time(), self.config['parent_model'])
        settings = reflection_settings(response, request, read(self.root / 'BROKER_CONFIG.json'))
        if settings['status'] == 'BOUND_FOR_LANE_DECODER':
            self.settings = settings
        result = dict(request=ref(path), response=ref(response_path) if response_path.exists() else None,
            disposition=disposition, reflection_settings=settings, observed_unix=time.time())
        write(self.root / 'parent_received' / (identifier + '.json'), result)
        if disposition['guidance']:
            self.event('parent', disposition['guidance'], sha(response_path))
        return result

    def environment(self, task, state, raw, purpose, sequence, *, open_turn=False, attached_readout=False):
        state, result = enacted_environment(task, state, raw, open_turn=open_turn)
        folder = 'readout_environment' if attached_readout else 'cycles'
        path = self.root / folder / f'{self.cycle:04d}' / purpose / (task['id'] + f'_{sequence:02d}.json')
        write(path, dict(task_id=task['id'], split=task['split'], attached_readout=attached_readout,
            environment_call=result, resulting_state=state, created_unix=time.time()))
        if task['split'] == 'TRAIN' and not attached_readout:
            self.event('environment', json.dumps(result, sort_keys=True), sha(path))
        return state, result, ref(path)


def episode(life, task, ordinal, memory):
    state = policy.game.initial(task)
    messages = [dict(role='system', content=EPISODE), dict(role='user', content=json.dumps(dict(
        observation=policy.public_observation(task, state), prior_own_reflections=memory), sort_keys=True))]
    remaining = 4096
    last = None
    for step in range(1, 17):
        if state['done'] or remaining <= 0:
            break
        reply = life.generate(task, 'episode', messages, min(384, remaining))
        remaining -= len(reply['token_ids']); messages.append(dict(role='assistant', content=reply['raw']))
        chosen = reply
        intervention = None
        if step == 1:
            intervention = life.ask(task, ordinal, 'experience')
            guidance = intervention['disposition']['guidance']
            if guidance and remaining > 0:
                messages.append(dict(role='user', content=guidance))
                chosen = life.generate(task, 'continuation', messages, min(384, remaining))
                remaining -= len(chosen['token_ids']); messages.append(dict(role='assistant', content=chosen['raw']))
        state, feedback, environment_ref = life.environment(task, state, chosen['raw'], 'experience', step)
        messages.append(dict(role='user', content=json.dumps(feedback, sort_keys=True)))
        if intervention:
            write(life.root / 'triples' / f'C{life.cycle:04d}_E{ordinal}.json', dict(
                before=reply['reference'], intervention=intervention, continuation=chosen['reference'],
                actual_environment=environment_ref, child_state=state, semantic_change='UNASSESSED'))
        last = chosen
    require(last is not None, 'episode_has_real_response')
    return dict(task_id=task['id'], split='TRAIN', final_state=state, last=last['reference'],
        last_trace=last['raw'], original_task_success=state['success'], child_tokens=4096 - remaining)


def open_opportunity(life, task, state, ordinal, *, parent, attached_readout):
    require(not parent or not attached_readout, 'readout_open_parent_absent')
    messages = [dict(role='system', content=EPISODE), dict(role='user', content=json.dumps(
        policy.public_observation(task, state), sort_keys=True)), dict(role='user', content=policy.OPEN_PROMPT)]
    remaining = 2048
    records = []
    for turn in range(1, 9):
        if remaining <= 0:
            break
        reply = life.generate(task, 'open_readout' if attached_readout else 'open_turn', messages,
            min(384, remaining), attached_readout=attached_readout)
        remaining -= len(reply['token_ids']); messages.append(dict(role='assistant', content=reply['raw']))
        if parent and turn == 1:
            response = life.ask(task, ordinal, 'open_turn')
            if response['disposition']['guidance'] and remaining > 0:
                messages.append(dict(role='user', content=response['disposition']['guidance']))
                continue
        state, feedback, evidence = life.environment(task, state, reply['raw'],
            'open_readout' if attached_readout else 'open_train', turn,
            open_turn=True, attached_readout=attached_readout)
        records.append(evidence)
        if not feedback['enacted']:
            break
        messages.append(dict(role='user', content=json.dumps(feedback, sort_keys=True)))
    return dict(environment_records=records, tokens=2048 - remaining, parent=parent,
        attached_readout=attached_readout, semantic_persistence='UNASSESSED', eligible_for_carry=False)


def train_cycle(life, tasks, memory):
    outcomes = []
    all_events = []
    for ordinal, task in enumerate(tasks):
        life.events = []
        observation = policy.public_observation(task, policy.game.initial(task))
        life.event('environment', json.dumps(observation, sort_keys=True), policy.digest(observation))
        outcome = episode(life, task, ordinal, memory)
        outcome['open'] = open_opportunity(life, task, outcome['final_state'], ordinal, parent=True, attached_readout=False)
        outcomes.append(outcome)
        all_events.extend(life.events)
    life.events = [dict(event, sequence=index) for index, event in enumerate(all_events)]
    task = tasks[-1]
    messages = [dict(role='system', content=policy.PRESLEEP_PROMPT), dict(role='user', content=json.dumps(
        dict(actual_experience=outcomes, prior_own_reflections=memory), sort_keys=True))]
    initial = life.generate(task, 'presleep', messages, 2048)
    messages.append(dict(role='assistant', content=initial['raw']))
    response = life.ask(task, 1, 'presleep_metacognition')
    if response['disposition']['guidance']:
        messages.append(dict(role='user', content=response['disposition']['guidance']))
    messages.append(dict(role='user', content=policy.REFLECTION_PROMPT))
    cap = life.settings['effective_max_new_tokens']
    reflection = life.generate(task, 'reflection', messages, cap)
    carry = carry_rows(memory + [dict(split='TRAIN', purpose='reflection', attached_readout=False,
        trace=reflection['raw'], source=reflection['reference'], actual_cap=cap)])
    output = life.root / 'cycles' / f'{life.cycle:04d}'
    write(output / 'TRAIN_COMPLETE.json', dict(outcomes=outcomes, reflection=reflection['reference'],
        actual_reflection_cap=cap, reflection_settings=life.settings, carry=carry,
        lambda_rehearsal='N/A_NO_OPTIMIZER', optimizer_steps=0, finished_unix=time.time()))
    write(life.root / 'CARRY.json', carry, replace=True)


def load_engine(config):
    tokenizer = original.portable.source.native.load_local_tokenizer(config['model_dir'])
    def check(label):
        require(time.time() < END - 2, 'hard_end:' + label)
    return Decoder(config['model_dir'], tokenizer, device='cuda:0', check=check)


def readout(root, cycle, scope):
    config = validate(root, gpu=True)
    require(scope in ('dev', 'final0', 'final_morning'), 'readout_scope')
    require(scope != 'final_morning' or time.time() >= policy.FINAL_UNIX, 'morning_not_early')
    directory = root / 'readouts' / f'{cycle:04d}' / scope
    require(not (directory / 'STARTED.json').exists(), 'no_silent_readout_retry')
    write(directory / 'STARTED.json', dict(pid=os.getpid(), parent=False, carry_access=False, started_unix=time.time()))
    engine = load_engine(config)
    life = Life(root, engine, config, cycle)
    tasks = read(root / ('FINAL.json' if scope.startswith('final') else 'DEV.json'))
    messages = [[dict(role='system', content=policy.HELD_PROMPT), dict(role='user', content=json.dumps(
        policy.public_observation(task, policy.game.initial(task)), sort_keys=True))] for task in tasks]
    responses = life.calls(tasks, scope, messages, 2048, attached_readout=True)
    if scope == 'dev':
        chosen = [tasks[0], tasks[4]]
        focused = [messages[index] + [dict(role='user', content=policy.FOCUSED_PROMPT)] for index in (0, 4)]
        life.calls(chosen, 'focused_DEV', focused, 2048, attached_readout=True)
        from gpu import astra_goal_quality_train as legacy_source
        legacy = read(root / 'LEGACY_READOUT.json')
        require(len(legacy['old_bank']) == 16, 'same_sixteen_old_facts')
        facts = legacy['old_bank']
        cases = [next(case for case in legacy['held']['cases'] if case['kind'] == kind) for kind in ('true', 'fault')]
        legacy_tasks = [dict(id='OLD-' + item['event'], split='LEGACY') for item in facts]
        legacy_messages = [legacy_source.memory.memory_messages(item['event'], 0) for item in facts]
        for start in (0, 8):
            life.calls(legacy_tasks[start:start + 8], 'legacy_facts', legacy_messages[start:start + 8], 512, attached_readout=True)
        life.calls([dict(id='AUDIT-' + case['case_sha256'], split='LEGACY') for case in cases],
            'audit', [legacy_source.memory.audit._messages(case, False) for case in cases], 512, attached_readout=True)
        if cycle:
            history = read(root / 'cycles' / f'{cycle:04d}' / 'TRAIN_COMPLETE.json')
            train = {task['id']: task for task in read(root / 'TRAIN.json')}
            for ordinal, outcome in enumerate(history['outcomes']):
                open_opportunity(life, train[outcome['task_id']], outcome['final_state'], ordinal,
                    parent=False, attached_readout=True)
    engine.verify_base()
    write(directory / 'COMPLETE.json', dict(status='COMPLETE', scope=scope, cycle=cycle,
        response_refs=[item['reference'] for item in responses], parent_calls=0, fresh_process=True,
        child_tokens=sum(len(item['token_ids']) for item in responses), optimizer_steps=0,
        no_carry_writes=True, final_never_parent_head_exchange=scope.startswith('final'), finished_unix=time.time()))


def spawn_readout(root, cycle, scope):
    command = [PYTHON, '-B', '-m', 'gpu.orch_r115_grid_native', 'readout', '--root', str(root),
        '--cycle', str(cycle), '--scope', scope]
    log = root / 'readout_logs' / f'{cycle:04d}_{scope}.log'
    log.parent.mkdir(exist_ok=True)
    with log.open('x') as stream:
        result = subprocess.run(command, cwd=SOURCE, stdout=stream, stderr=subprocess.STDOUT)
    require(result.returncode == 0, 'readout_failure_preserved:' + scope)


def resident(root):
    config = validate(root, gpu=True)
    write(root / 'RESIDENT_STARTED.json', dict(pid=os.getpid(), started_unix=time.time()))
    spawn_readout(root, 0, 'final0')
    spawn_readout(root, 0, 'dev')
    engine = load_engine(config)
    write(root / 'LOADED.json', dict(pid=os.getpid(), base_sha256=engine.loaded_base_sha256,
        no_adapter=engine.no_adapter, loaded_unix=time.time()))
    roster = read(root / 'TRAIN.json')
    cycle = 1
    while time.time() < TRAIN_END:
        ledger = [json.loads(line) for line in (root / 'LEDGER.jsonl').read_text().splitlines() if line.strip()]
        if sum(row['kind'] == 'NATIVE' for row in ledger) > MAX_NATIVE - 120 or sum(row['kind'] == 'PARENT' for row in ledger) > MAX_PARENT - 6:
            write(root / 'BUDGET_TRAIN_END.json', dict(cycle=cycle, reason='reserve_final_no_refill', observed_unix=time.time()))
            break
        memory = read(root / 'CARRY.json') if (root / 'CARRY.json').exists() else []
        tasks = [roster[(cycle - 1) % 8], roster[8 + (cycle - 1) % 8]]
        life = Life(root, engine, config, cycle)
        try:
            train_cycle(life, tasks, memory)
        except TrainWindowClosed as error:
            write(root / 'cycles' / f'{cycle:04d}' / 'CLOCK_BOUNDARY.json', dict(reason=str(error),
                all_completed_calls_preserved=True, partial_cycle=True, optimizer_steps=0, observed_unix=time.time()))
            break
        spawn_readout(root, cycle, 'dev')
        write(root / 'cycles' / f'{cycle:04d}' / 'CYCLE_COMPLETE.json', dict(cycle=cycle,
            optimizer_steps=0, mode='ELICITATION_ONLY_SYSTEMS', finished_unix=time.time()))
        cycle += 1
    engine.verify_base()
    del engine
    import gc
    import torch
    gc.collect(); torch.cuda.empty_cache()
    while time.time() < policy.FINAL_UNIX:
        time.sleep(min(5, policy.FINAL_UNIX - time.time()))
    spawn_readout(root, cycle, 'final_morning')
    write(root / 'RESIDENT_COMPLETE.json', dict(completed_cycles=cycle - 1, finished_unix=time.time(), optimizer_steps=0))


def guard(root):
    config = validate(root)
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_guard')
    (root / 'GUARD_ONCE').mkdir()
    try:
        publication = read(root / 'PUBLICATION.json')
        require(publication['own_CPU_passed'] and publication['dated_builder'] and publication['R115_user_GO'], 'preGPU_publication')
        for attempt in range(120):
            report = scan(root)
            write(root / 'admission' / f'{attempt:03d}.json', report)
            if report['clear'] and report['scanner_euid'] == 0 and not report['blocking_reasons']:
                break
            time.sleep(2)
        else:
            raise ValueError('strict_admission_not_clear')
        environment = dict(os.environ, CUDA_VISIBLE_DEVICES=config['uuid'], PYTHONPATH=str(SOURCE),
            PYTHONDONTWRITEBYTECODE='1', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
        command = ['timeout', '--signal=TERM', '--kill-after=5s', str(int(END - time.time() - 5)) + 's',
            PYTHON, '-B', '-m', 'gpu.orch_r115_grid_native', 'resident', '--root', str(root)]
        with (root / 'NATIVE.log').open('x') as stream:
            process = subprocess.Popen(command, cwd=SOURCE, env=environment, stdout=stream,
                stderr=subprocess.STDOUT, start_new_session=True)
        write(root / 'LAUNCH.json', dict(pid=process.pid, command=command, started_unix=time.time()))
        code = process.wait()
        write(root / 'TERMINAL.json', dict(status='COMPLETE' if code == 0 else 'FAILED', exit_code=code, finished_unix=time.time()))
    except BaseException as error:
        if not (root / 'TERMINAL.json').exists():
            write(root / 'TERMINAL.json', dict(status='FAILED', error_type=type(error).__name__, error=str(error), finished_unix=time.time()))
        raise
    finally:
        write(root / 'FINAL_RELEASE.json', scan(root))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('guard', 'resident', 'readout', 'scan'))
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--cycle', type=int, default=0)
    parser.add_argument('--scope', default='dev')
    args = parser.parse_args()
    if args.mode == 'scan':
        print(json.dumps(scan(args.root), sort_keys=True))
    elif args.mode == 'readout':
        readout(args.root, args.cycle, args.scope)
    else:
        (guard if args.mode == 'guard' else resident)(args.root)
