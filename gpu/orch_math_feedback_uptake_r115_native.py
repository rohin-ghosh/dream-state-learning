"""Resident frozen BASE F2 with enacted math actions and isolated fresh readouts."""

import argparse
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import time
from types import SimpleNamespace

from gpu import orch_math_feedback_uptake_r108_run as reuse
from gpu import orch_math_feedback_uptake_stopped as stopping
from gpu import orch_r110_claude_broker as broker
from gpu import orch_rich_hot_a100_minor_scan as scanner
from gpu import orch_rich_hot_node3_base107_engine as direct
from organism_v6 import orch_math_feedback_uptake_r115 as policy


require = policy.require
common = reuse.common
SOURCE = Path(__file__).resolve().parents[1]
PYTHON = reuse.existing.PYTHON
MODEL, BUNDLE = reuse.existing.MODEL, reuse.existing.BUNDLE
HARD, NATIVE = policy.previous.original.HARD_END, policy.previous.original.NATIVE_END


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')


def atomic(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + '.pending')
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')
    os.replace(temporary, path)


def bind():
    def allocation(index):
        require(index in policy.DEVICES, 'allocated_f2_1_5_only')
        return policy.DEVICES[index]
    scanner.pinned.policy = SimpleNamespace(DEVICES=policy.DEVICES, HOST_SHA=policy.HOST_SHA,
        require=require, allocation=allocation)
    require(scanner.pinned.host_identity() == policy.HOST_SHA, 'hashed_native_host')
    require(Path('/proc/sys/kernel/random/boot_id').read_text().strip() == policy.BOOT, 'pinned_boot')


def validate(root):
    bind()
    require(root == policy.ROOT and root.resolve() == root, 'exact_root')
    ready = read(root / 'READY.json')
    for name, digest in ready['source_files'].items():
        require(policy.sha(SOURCE / name) == digest, 'immutable_source:' + name)
    require(ready['common_contract_sha256'] == policy.digest(read(root / 'COMMON_CONTRACT.json')), 'contract_binding')
    for name, digest in ready['data_files'].items():
        require(policy.sha(root / name) == digest, 'exact_cohort:' + name)
    return ready


def mounted(lane, phase):
    index = read(lane / 'CONFIG.json')['index']
    bind()
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == policy.DEVICES[index], 'uuid_cvd')
    require(('CUDA_VISIBLE_DEVICES=' + policy.DEVICES[index]).encode() in
        Path('/proc/self/environ').read_bytes().split(b'\0'), 'startup_uuid_cvd')
    actual = subprocess.check_output(['nvidia-smi', '-i', str(index), '--query-gpu=uuid', '--format=csv,noheader'], text=True).strip()
    require(actual == policy.DEVICES[index], 'physical_uuid')
    files = reuse.driver.seam.portable.verify_base_files(BUNDLE, MODEL,
        expected_manifest_sha256=reuse.node_limits.BUNDLE_SHA)
    require(files['expected_base_sha256'] == policy.previous.original.BASE_SHA, 'genuine_base_files')
    return dict(phase=phase, index=index, uuid=actual, device_minor=scanner.device_minor(actual),
        process=scanner.pinned.identity(Path('/proc') / str(os.getpid())), base_files=files,
        adapter=None, optimizer=None, observed_unix=time.time())


def reserve(lane, kind, count, metadata):
    with (lane / 'COUNTERS.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        path = lane / 'COUNTERS.json'
        values = read(path) if path.exists() else dict(native=0, parent=0)
        cap = policy.NATIVE_CAP if kind == 'native' else policy.PARENT_CAP
        require(values[kind] + count <= cap, 'fixed_' + kind + '_cap')
        first = values[kind] + 1
        values[kind] += count
        atomic(path, values)
        write(lane / 'reservations' / f'{kind}_{first:04d}.json', dict(kind=kind, count=count,
            first=first, metadata=metadata, reserved_unix=time.time(), retries=0))
        return first


class Engine(stopping.engine_class(direct.Engine)):
    purpose = 'experience'

    def generate(self, messages, *, max_new_tokens):
        if self.purpose not in ('reflection', 'presleep'):
            response = direct.Engine.generate(self, messages, max_new_tokens=max_new_tokens)
            return dict(response, input_truncated=False, context_limit=16384,
                requested_generation_cap=max_new_tokens, effective_generation_cap=max_new_tokens)
        self.check('reflection_generation')
        tokens = self.tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_dict=False)
        require(0 < max_new_tokens <= min(8192, 16384-len(tokens)), 'bounded_reflection_prefix')
        inputs = self.torch.tensor([tokens], dtype=self.torch.long, device=self.device)
        criterion = stopping.safeguard.ExactParagraphRepetitionStop(self.tokenizer,
            prompt_length=len(tokens), eos_token_ids=self.tokenizer.eos_token_id)
        config = self.transformers.GenerationConfig(do_sample=False, num_beams=1, use_cache=True,
            max_new_tokens=max_new_tokens, repetition_penalty=1.0, no_repeat_ngram_size=8,
            eos_token_id=self.tokenizer.eos_token_id, pad_token_id=self.tokenizer.pad_token_id)
        with self.torch.inference_mode():
            generated = self.model.generate(input_ids=inputs, attention_mask=self.torch.ones_like(inputs),
                generation_config=config, stopping_criteria=self.transformers.StoppingCriteriaList([criterion]))
        require(generated[0, :len(tokens)].tolist() == tokens, 'unchanged_reflection_prefix')
        tail = generated[0, len(tokens):].tolist()
        ending = criterion.finalize(generated, max_new_tokens=max_new_tokens)
        raw = self.tokenizer.decode(tail[:-1] if ending['terminal'] else tail,
            skip_special_tokens=False, clean_up_tokenization_spaces=False)
        return dict(messages=messages, raw=raw, token_ids=tail, prompt_tokens=len(tokens),
            terminal=ending['terminal'], truncated=ending['truncated'], input_truncated=False,
            context_limit=16384, requested_generation_cap=max_new_tokens, effective_generation_cap=max_new_tokens,
            reflection_guard=dict(ending, no_repeat_ngram_size=8, scope='REFLECTION_METACOGNITION_ONLY',
                fit_eligibility='NOT_APPLICABLE_NO_WEIGHT_TRAINING'))

    def batch(self, prompts, cap):
        self.check('batch_generation')
        token_lists = [self.tokenizer.apply_chat_template(prompt, tokenize=True,
            add_generation_prompt=True, return_dict=False) for prompt in prompts]
        width = max(map(len, token_lists))
        require(width + cap <= 16384, 'uncropped_independent_batch')
        inputs = self.torch.tensor([[self.tokenizer.pad_token_id] * (width-len(tokens)) + tokens
            for tokens in token_lists], dtype=self.torch.long, device=self.device)
        masks = self.torch.tensor([[0] * (width-len(tokens)) + [1] * len(tokens)
            for tokens in token_lists], dtype=self.torch.long, device=self.device)
        config = self.transformers.GenerationConfig(do_sample=False, num_beams=1, use_cache=True,
            max_new_tokens=cap, repetition_penalty=1.0, eos_token_id=self.tokenizer.eos_token_id,
            pad_token_id=self.tokenizer.pad_token_id)
        with self.torch.inference_mode():
            generated = self.model.generate(input_ids=inputs, attention_mask=masks, generation_config=config)
        responses = []
        for position, prompt in enumerate(prompts):
            require(generated[position, :width].tolist() == inputs[position].tolist(), 'unchanged_batch_prefix')
            tail = generated[position, width:].tolist()
            terminal = self.tokenizer.eos_token_id in tail
            if terminal:
                tail = tail[:tail.index(self.tokenizer.eos_token_id)+1]
            responses.append(dict(messages=prompt, raw=self.tokenizer.decode(tail[:-1] if terminal else tail,
                skip_special_tokens=False, clean_up_tokenization_spaces=False), token_ids=tail,
                terminal=terminal, truncated=not terminal and len(tail) == cap, input_truncated=False,
                prompt_tokens=len(token_lists[position]), requested_generation_cap=cap,
                effective_generation_cap=cap, context_limit=16384, independent_sequence=True))
        return responses


def create_engine(check):
    tokenizer = reuse.driver.seam.native.source.native.load_local_tokenizer(MODEL)
    return Engine(MODEL, tokenizer, device='cuda:0', check=check)


def parent(lane, task, experience, cycle, episode, phase):
    config = read(lane / 'BROKER_CONFIG.json')
    identifier = f'C{cycle:03d}_E{episode}_{phase}'
    payload = experience.payload(task, config['life_id'], cycle, episode, phase, config['cohort_sha256'])
    deadline = min(time.time()+120, NATIVE)
    request = dict(id=identifier, payload=payload, payload_sha256=policy.digest(payload), lane_deadline_unix=deadline)
    reserve(lane, 'parent', 1, dict(id=identifier))
    broker.validate_request(request, config)
    path = lane / 'parent_queue' / (identifier + '.request.json')
    write(path, request)
    response_path = path.with_name(identifier + '.response.json')
    response = dict(status='MISSING', error=dict(code='lane_wait_expired'), id=identifier)
    while time.time() < deadline:
        if response_path.exists():
            candidate = read(response_path)
            try:
                require(candidate['id'] == identifier and candidate['request_sha256'] == policy.digest(request), 'parent_request_join')
                receipt = candidate['transcript_receipt']
                directory = Path(receipt['remote_root'])
                require(directory == lane / 'parent_transcripts' / identifier, 'native_parent_archive')
                for name, digest in receipt['files'].items():
                    require(Path(name).name == name and policy.sha(directory / name) == digest, 'actual_parent_archive_hash')
                require(candidate['status'] in ('COMPLETE', 'SILENT', 'MISSING'), 'parent_status')
                if candidate['status'] in ('COMPLETE', 'SILENT'):
                    require(candidate['actual_model'] == policy.MODELS[read(lane / 'CONFIG.json')['index']], 'actual_parent_model')
                response = candidate
            except (ValueError, KeyError, OSError) as error:
                response.update(error=dict(code='invalid_parent_receipt', detail=str(error)))
            break
        time.sleep(.5)
    if response['status'] == 'COMPLETE':
        text = response['plan']['guidance']
        experience.append(policy.event('parent', text, 'TRAIN', response))
    delivered = dict(id=identifier, status=response['status'], actual_model=response.get('actual_model'),
        provider_dispatched=response.get('provider_dispatched'), finished_unix=time.time(),
        prompt_binding=response.get('prompt_binding'), request_sha256=policy.digest(request),
        response_sha256=policy.sha(response_path) if response_path.exists() else None,
        native_archive=response.get('transcript_receipt'), error=response.get('error'))
    write(lane / 'delivered' / (identifier + '.json'), delivered)
    atomic(lane / 'LATEST_PARENT.json', delivered)
    return response, request, config


def child_call(lane, engine, output, task, experience, invitation, phase, cap, carry=None, settings=None):
    prompt = policy.messages(experience, invitation, carry)
    tokens = engine.tokenizer.apply_chat_template(prompt, tokenize=True, add_generation_prompt=True, return_dict=False)
    actual_cap = min(cap, 16384-len(tokens))
    require(actual_cap > 0, 'uncropped_context_has_generation_space')
    number = reserve(lane, 'native', 1, dict(phase=phase, task_id=task['id'], split='TRAIN'))
    path = output / f'CALL_{number:04d}.json'
    request = dict(phase=phase, split='TRAIN', task_id=task['id'], started_unix=time.time(),
        requested_cap=cap, context_limited_cap=actual_cap, messages=prompt, source_question_sha256=task['question_sha256'])
    write(path.with_suffix('.request.json'), request)
    engine.purpose = phase
    try:
        if phase == 'reflection' and settings:
            response, applied = policy.reflection_generate(engine, prompt, *settings, now=time.time(), context_cap=actual_cap)
        else:
            response, applied = engine.generate(prompt, max_new_tokens=actual_cap), None
        item = policy.event('child', response['raw'], 'TRAIN', dict(request=request, response=response))
        experience.append(item)
        write(path, dict(request, response=response, reflection_settings=applied, finished_unix=time.time(), status='COMPLETE'))
        atomic(lane / 'LATEST_CHILD.json', dict(phase=phase, task_id=task['id'], path=str(path),
            tokens=len(response['token_ids']), terminal=response['terminal'], truncated=response['truncated'],
            reflection_settings=applied, finished_unix=time.time(), status='COMPLETE'))
        return response, item
    except BaseException as error:
        write(path, dict(request, error=dict(type=type(error).__name__, message=str(error)), finished_unix=time.time(), status='FAILED'))
        raise


def environment(experience, task, response):
    observations = policy.enact(task, response['raw'])
    for observation in observations:
        experience.append(policy.event('environment', json.dumps(observation, sort_keys=True), 'TRAIN', observation))
    return observations


def readout(lane, cycle, stage):
    root = lane.parent
    validate(root)
    require(stage != 'morning_final' or policy.previous.MORNING <= time.time() < HARD, 'morning_final_actual_window')
    require(not stage.startswith('sleep0') or cycle == 0, 'sleep0_only_before_experience')
    output = (lane / 'sealed' if stage in ('sleep0_final', 'morning_final') else lane / 'readouts') / f'{stage}_{cycle:03d}'
    output.mkdir(parents=True, exist_ok=False)
    write(output / 'BEFORE.json', mounted(lane, stage))
    deadline = HARD if stage == 'morning_final' else NATIVE
    def check(label):
        require(time.time() < deadline, 'readout_hard_bound:' + label)
    engine = None
    planned = 16 if 'final' in stage else 20 if stage == 'cycle' else 18
    write(output / 'DENOMINATORS.json', dict(planned_native=planned, retries=0, status='PENDING', never_rows_or_buffer=True))
    try:
        engine = create_engine(check)
        tasks = read(root / ('sealed/FINAL8.json' if 'final' in stage else 'DEV8.json'))
        def batch(selected, purpose, previous=None, cap=2048):
            prompts = [policy.readout_messages(task, purpose, None if previous is None else previous[position])
                for position, task in enumerate(selected)]
            first = reserve(lane, 'native', len(selected), dict(phase=stage, purpose=purpose, split=selected[0]['split']))
            write(output / f'BATCH_{first:04d}.request.json', dict(prompts=prompts, task_ids=[task['id'] for task in selected],
                cap=cap, started_unix=time.time(), parent_free=True, never_rows_or_buffer=True))
            responses = engine.batch(prompts, cap)
            for position, (task, response) in enumerate(zip(selected, responses)):
                observed = policy.enact(task, response['raw']) if purpose == 'open_turn' else []
                write(output / f'CALL_{first+position:04d}.json', dict(task_id=task['id'], split=task['split'],
                    purpose=purpose, response=response, observations=observed, status='COMPLETE',
                    finished_unix=time.time(), parent_free=True, never_rows_or_buffer=True))
            return responses
        answers = batch(tasks, 'held')
        batch(tasks, 'open_turn', answers, cap=1024)
        if 'final' not in stage:
            batch(tasks[:2], 'focused')
        if stage == 'cycle':
            train = read(root / 'TRAIN.json')[cycle-1]
            probes = [dict(task, split='PROBE') for task in train]
            boundary = read(lane / f'cycle{cycle:03d}' / 'BOUNDARY.json')
            batch(probes, 'open_turn', boundary['original_responses'], cap=1024)
        engine.verify_base()
        write(output / 'AFTER.json', mounted(lane, stage + '_after'))
        write(output / 'COMPLETE.json', dict(status='COMPLETE', planned_native=planned,
            actual_native=sum(1 for path in output.glob('CALL_*.json')), finished_unix=time.time(),
            parent_free=True, weight_updates=0, never_rows_or_buffer=True))
    except BaseException as error:
        write(output / 'FAILED.json', dict(status='FAILED', error=str(error), type=type(error).__name__,
            completed_native=sum(1 for path in output.glob('CALL_*.json')), planned_native=planned,
            finished_unix=time.time(), retries=0))
        raise
    finally:
        if engine is not None:
            engine.check = lambda label: None
            engine.verify_base()
        write(output / 'MOUNTED_FINAL.json', mounted(lane, stage + '_final'))


def dispatch_readout(lane, cycle, stage):
    command = [PYTHON, '-B', str(Path(__file__)), 'readout', '--root', str(lane.parent),
        '--index', str(read(lane / 'CONFIG.json')['index']), '--cycle', str(cycle), '--stage', stage]
    with (lane / f'READOUT_{stage}_{cycle:03d}.log').open('x') as log:
        child = subprocess.Popen(command, cwd=SOURCE, stdout=log, stderr=subprocess.STDOUT)
        write(lane / f'READOUT_{stage}_{cycle:03d}_PROCESS.json', scanner.pinned.identity(Path('/proc') / str(child.pid)))
        require(child.wait() == 0, 'fresh_readout_failed_no_retry')


def resident(lane):
    root = lane.parent
    validate(root)
    write(lane / 'MOUNTED_STARTUP.json', mounted(lane, 'resident_start'))
    engine = None
    status = 'FAILED'
    def check(label):
        require(time.time() < NATIVE, 'native_wall:' + label)
    try:
        dispatch_readout(lane, 0, 'sleep0_final')
        dispatch_readout(lane, 0, 'sleep0_dev')
        engine = create_engine(check)
        write(lane / 'MODEL_LOADED.json', dict(base_sha256=engine.loaded_base_sha256, no_adapter=engine.no_adapter,
            process=scanner.pinned.identity(Path('/proc') / str(os.getpid())), finished_unix=time.time()))
        carry = None
        for cycle, tasks in enumerate(read(root / 'TRAIN.json')[:policy.CYCLES], 1):
            if time.time() >= NATIVE-120:
                break
            output = lane / f'cycle{cycle:03d}'
            output.mkdir()
            started = time.time()
            combined, originals = policy.Experience(), []
            settings = None
            for episode, task in enumerate(tasks):
                experience = policy.Experience()
                experience.append(policy.event('environment', task['question'] + '\n\n' + policy.ENVIRONMENT, 'TRAIN', task['question_sha256']))
                response, item = child_call(lane, engine, output, task, experience,
                    policy.previous.original.EPISODE.format(question=task['question']), 'episode', 2048, carry)
                originals.append(response)
                verdict = policy.previous.original.source.judge(task, response)
                experience.append(policy.event('environment', 'Checker feedback delivered to you: ' + json.dumps(verdict), 'TRAIN', verdict))
                settings = parent(lane, task, experience, cycle, episode, 'experience')
                response, item = child_call(lane, engine, output, task, experience, policy.previous.OPEN_TURN, 'open_turn', 1024)
                observations = environment(experience, task, response)
                write(output / f'OPEN_ENVIRONMENT_E{episode}.json', dict(observations=observations, actual_environment_executed=True))
                settings = parent(lane, task, experience, cycle, episode, 'open_turn')
                for item in experience.events:
                    combined.append(item)
            response, item = child_call(lane, engine, output, tasks[-1], combined,
                policy.previous.original.PRESLEEP, 'presleep', 4096)
            settings = parent(lane, tasks[-1], combined, cycle, 1, 'presleep_metacognition')
            response, carry = child_call(lane, engine, output, tasks[-1], combined,
                policy.previous.original.REFLECTION, 'reflection', 8192, settings=settings)
            parent(lane, tasks[-1], combined, cycle, 1, 'reflection')
            write(output / 'TRAIN_EXPERIENCE.json', combined.events)
            write(output / 'BOUNDARY.json', dict(original_responses=originals, own_reflection=carry,
                source_history_sha256=policy.digest(combined.events), weight_updates=0, optimizer_steps=0,
                label='CONTEXT_BOUNDARY_ELICITATION_ONLY', finished_unix=time.time()))
            dispatch_readout(lane, cycle, 'cycle')
            write(output / 'COMPLETE.json', dict(status='COMPLETE', cycle=cycle, started_unix=started,
                finished_unix=time.time(), counters=read(lane / 'COUNTERS.json'), label='ELICITATION_ONLY',
                child_semantic_change='UNKNOWN_REQUIRES_JUDGE_OR_AUTHOR_REVIEW', weight_updates=0))
            atomic(lane / 'PROGRESS.json', dict(cycle=cycle, phase='CYCLE_COMPLETE', counters=read(lane / 'COUNTERS.json'),
                observed_unix=time.time(), cycle_seconds=time.time()-started))
        engine.check = lambda label: require(time.time() < HARD, 'final_hard_wall')
        engine.verify_base()
        while time.time() < policy.previous.MORNING:
            time.sleep(min(5, policy.previous.MORNING-time.time()))
        dispatch_readout(lane, 0, 'morning_final')
        status = 'COMPLETE'
    except BaseException as error:
        write(lane / 'NATIVE_FAILED.json', dict(type=type(error).__name__, error=str(error), finished_unix=time.time()))
        raise
    finally:
        if engine is not None:
            engine.check = lambda label: None
            engine.verify_base()
        write(lane / 'MOUNTED_AFTER.json', mounted(lane, 'resident_after'))
        write(lane / 'RESIDENT_TERMINAL.json', dict(status=status, counters=read(lane / 'COUNTERS.json'),
            finished_unix=time.time(), adapter=None, optimizer=None, weight_updates=0))


def scan(root, index):
    bind()
    return scanner.scan(index, root / 'SERVICE_IDENTITY.json')


def stop_readouts(lane):
    for record in lane.glob('READOUT_*_PROCESS.json'):
        expected = read(record)
        directory = Path('/proc') / str(expected['pid'])
        try:
            if scanner.pinned.identity(directory) != expected or expected['uid'] != os.getuid():
                continue
            descriptor = os.pidfd_open(expected['pid'])
            try:
                require(scanner.pinned.identity(directory) == expected, 'owned_readout_identity_before_signal')
                signal.pidfd_send_signal(descriptor, signal.SIGTERM)
                until = time.time()+8
                while directory.exists() and time.time() < until:
                    time.sleep(.2)
                if directory.exists() and scanner.pinned.identity(directory) == expected:
                    signal.pidfd_send_signal(descriptor, signal.SIGKILL)
            finally:
                os.close(descriptor)
        except FileNotFoundError:
            continue


def guard(root, index):
    validate(root)
    lane = root / f'lane{index}'
    release = read(lane / 'RELEASE.json')
    require(release['released'] is True and release['uuid'] == policy.DEVICES[index], 'actual_previous_owner_release')
    publication = read(root / 'PUBLICATION.json')
    require(publication['ready_sha256'] == policy.sha(root / 'READY.json'), 'published_cpu_provenance')
    require(read(root / 'GO.json')['authorization'] == 'WATCHER_RELAYED_ROHIN_DONE', 'explicit_r115_go')
    write(lane / 'ACTIVATION.json', dict(started_unix=time.time(), hard_deadline_unix=HARD,
        native_deadline_unix=NATIVE, index=index, guardian=scanner.pinned.identity(Path('/proc') / str(os.getpid()))))
    child = identity = None
    status = 'FAILED'
    def interrupted(signum, frame):
        raise SystemExit(128+signum)
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    try:
        admitted = False
        for attempt in range(30):
            result = subprocess.run(['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
                'PYTHONPATH=' + str(SOURCE), 'python3', '-B', str(Path(__file__)), 'scan', '--root', str(root),
                '--index', str(index)], capture_output=True, text=True, check=True, timeout=90)
            report = json.loads(result.stdout)
            write(lane / f'ADMISSION_{attempt:03d}.json', report)
            admitted = report['clear'] and not report['blocking_reasons'] and report['scanner_euid'] == 0
            if admitted:
                break
            time.sleep(2)
        require(admitted, 'strict_full_proc_admission_no_waiver')
        with (lane / 'RESIDENT.log').open('x') as log:
            child = subprocess.Popen([PYTHON, '-B', str(Path(__file__)), 'resident', '--root', str(root), '--index', str(index)],
                cwd=SOURCE, stdout=log, stderr=subprocess.STDOUT, start_new_session=True,
                env=dict(os.environ, CUDA_VISIBLE_DEVICES=policy.DEVICES[index], PYTHONPATH=str(SOURCE),
                    HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', PYTHONDONTWRITEBYTECODE='1',
                    OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', TOKENIZERS_PARALLELISM='false'))
            identity = common.process_identity(Path('/proc') / str(child.pid))
            write(lane / 'LAUNCH.json', dict(identity=identity, uuid=policy.DEVICES[index], started_unix=time.time()))
            while child.poll() is None:
                require(time.time() < HARD, 'absolute_hard_wall')
                time.sleep(1)
            require(child.returncode == 0, 'resident_failed_no_hidden_replay')
            status = 'COMPLETE'
    except BaseException as error:
        write(lane / 'GUARDIAN_FAILED.json', dict(error=str(error), type=type(error).__name__, finished_unix=time.time()))
        raise
    finally:
        if child is not None:
            common.stop_owned(child, identity)
        stop_readouts(lane)
        write(lane / 'TERMINAL.json', dict(status=status, finished_unix=time.time(), peer_processes_signalled=0))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('service', 'scan', 'guard', 'resident', 'readout'))
    parser.add_argument('--root', type=Path, default=policy.ROOT)
    parser.add_argument('--index', type=int, choices=(1, 5))
    parser.add_argument('--cycle', type=int, default=0)
    parser.add_argument('--stage', choices=('sleep0_dev', 'sleep0_final', 'cycle', 'morning_final'))
    args = parser.parse_args()
    if args.phase == 'service':
        bind()
        scanner.pinned.service(args.root / 'SERVICE_IDENTITY.json')
    elif args.phase == 'scan':
        print(json.dumps(scan(args.root, args.index)))
    elif args.phase == 'guard':
        guard(args.root, args.index)
    elif args.phase == 'resident':
        resident(args.root / f'lane{args.index}')
    else:
        readout(args.root / f'lane{args.index}', args.cycle, args.stage)
