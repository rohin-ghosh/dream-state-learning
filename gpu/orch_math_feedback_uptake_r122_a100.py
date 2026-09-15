"""Explicit C8 read-only elicitation forks; no optimizer loading or weight writes."""

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from types import SimpleNamespace

from gpu import orch_math_feedback_uptake_r115_native as math
from gpu import orch_math_feedback_uptake_r121_independent_native as reuse
from gpu import orch_math_feedback_uptake_r118_preinfer as admission
from gpu import orch_math_feedback_uptake_r118_argv_admission as argv_scan
from gpu import orch_rich_hot_a100_minor_scan as scanner
from organism_v6 import orch_math_pipeline_l2 as gym


ROOT = Path('/localhome/local-rohing/orch_math_feedback_uptake_r122_a100_20260915_attempt2')
SOURCE = Path(__file__).resolve().parents[1]
MODULE = 'gpu.orch_math_feedback_uptake_r122_a100'
INVENTORY = Path('/localhome/local-rohing/orch_math_feedback_uptake_r120_checkpoint_inventory_20260915_attempt1/VERIFIED.json')
OLD = Path('/localhome/local-rohing/orch_math_pipeline_l2_20260915_attempt1')
HOST = '6bcd6b8370cc2f2a15e1e488352b4cec96b1e137489d52c3324c199536a09ba8'
DEVICES = {5: 'GPU-c1650c7f-ac26-f1a0-2ab8-c7354a6f27c9',
    6: 'GPU-6de3930d-104a-f969-7d36-009271368dd1',
    7: 'GPU-f0405a96-813d-7ac7-d641-3ec31d103037'}
CAMPAIGNS = {5: 'campaign_03_r102_micro5', 6: 'campaign_05_r104_training4', 7: 'campaign_04_r102_creative7'}
LEASE_END = 1790463900
HARD = LEASE_END - 21600
NATIVE = HARD - 600
read, write, atomic, require = math.read, math.write, math.atomic, math.require
sha = scanner.pinned.sha


def reference(path):
    return dict(path=str(path), sha256=sha(path))


def bind():
    def allocation(index):
        require(index in DEVICES, 'owned_A100_5_6_7_only')
        return DEVICES[index]
    scanner.pinned.policy = SimpleNamespace(DEVICES=DEVICES, HOST_SHA=HOST,
        allocation=allocation, require=require)
    require(scanner.pinned.host_identity() == HOST, 'actual_host_hash')


def validate_lineage(record):
    require(record['cycle'] == 8 and record['historical_save_verified'], 'genuine_saved_C8')
    identity = reuse.native.bridge.AdapterIdentity.from_document(record['adapter']).verify()
    require(sha(record['optimizer']['path']) == record['optimizer']['sha256'], 'raw_AdamW_preserved')
    require(sha(record['complete']['path']) == record['complete']['sha256'], 'genuine_complete')
    after = Path(record['complete']['path']).with_name('AFTER.json')
    require(sha(after) == record['after_sha256'], 'genuine_after')
    return identity


def fresh_pair(index, cycle, excluded):
    result = []
    used = set(excluded)
    for position in range(2):
        for nonce in range(10000):
            task = gym.make_task(f'R122_A100_{index}_TRAIN', cycle, (cycle * 2 + position) % 4 + nonce * 1001)
            task['split'] = 'TRAIN'
            if task['question_sha256'] not in used:
                used.add(task['question_sha256'])
                result.append(task)
                break
        else:
            raise ValueError('fresh_question_space_exhausted_no_replay')
    return result


def prepare(index):
    bind()
    record = next(item for item in read(INVENTORY)['records'] if item['campaign'] == CAMPAIGNS[index])
    validate_lineage(record)
    root = ROOT / f'lane{index}'
    root.mkdir(parents=True, exist_ok=False)
    campaign = OLD / CAMPAIGNS[index]
    cohort = read(campaign / 'COHORT.json')
    excluded = set(cohort['excluded_question_hashes'])
    for name in ('train', 'held'):
        for group in cohort[name]:
            excluded.update(task['question_sha256'] for task in group)
    rows = read(campaign / 'GUIDED_SLEEP/cycle8/experience/ROWS.json')
    own = rows[-1]
    source = campaign / own['source_call_path']
    if not source.exists():
        source = OLD / own['source_call_path']
    require(sha(source) == own['source_call_sha256'] and read(source)['response']['raw'] == own['target'], 'actual_C8_carry')
    write(root / 'CARRY_INITIAL.json', math.policy.event('child', own['target'], 'TRAIN', reference(source)))
    write(root / 'EXCLUSIONS.json', sorted(excluded))
    write(root / 'DEV.json', [dict(task, split='DEV') for task in cohort['held'][-1][:8]])
    require(len(read(root / 'DEV.json')) == 8, 'eight_existing_parent_free_DEV')
    write(root / 'COUNTERS.json', dict(native=0, parent=0, optimizer_updates=0))
    write(root / 'CURSOR.json', dict(next_cycle=9, carry=reference(root / 'CARRY_INITIAL.json')))
    for directory in ('queue', 'parent_transcripts', 'reservations', 'consumed'):
        (root / directory).mkdir()
    plan = dict(schema='R122_C8_READ_ONLY_ELICITATION_V1', index=index, uuid=DEVICES[index], root=str(root),
        source_root=str(SOURCE), source_manifest=reference(SOURCE / 'R122_SOURCE_MANIFEST.json'),
        cpu_tests=reference(SOURCE / 'R122_CPU_TESTS.json'), inventory=reference(INVENTORY), record=record,
        lineage='EXPLICIT_READ_ONLY_ELICITATION_FORK_OF_GENUINE_MATH_C8', historical_root=str(campaign),
        historical_cohort=reference(campaign / 'COHORT.json'), historical_rows=reference(campaign / 'GUIDED_SLEEP/cycle8/experience/ROWS.json'),
        initial_carry=reference(root / 'CARRY_INITIAL.json'), dev=reference(root / 'DEV.json'), exclusions=reference(root / 'EXCLUSIONS.json'),
        optimizer_loaded=False, optimizer_updates=0, adapter_read_only=True, no_reset_or_resume_optimizer_claim=True,
        context_boundaries_not_weight_sleeps=True, episodes_per_context_boundary=2,
        native_end=NATIVE, hard_end=HARD, lease_end=LEASE_END, lease_margin_seconds=21600,
        lease_source=reference(SOURCE / 'gpu/orch_rich_hot_a100_run.py'),
        prospective_native_capacity=10000000, prospective_parent_capacity=1000000, cycle_cap=None,
        old_counters_untouched=True, no_completed_old_inputs_replayed=True, parent_ttl=600,
        parent_wait_seconds=0, parent_effort='low', parent_output_cap=1024,
        fixed_parent_prompt='PARENTING_BATTLE_PLAN_v4_SECTION6', created_unix=time.time(),
        fresh_DEV_process=True, DEV_historically_exposed_not_new_holdout=True,
        base_model=math.MODEL, bundle=math.BUNDLE)
    write(root / 'PLAN.json', plan)
    return reference(root / 'PLAN.json')


def validate(index):
    bind()
    root = ROOT / f'lane{index}'
    plan = read(root / 'PLAN.json')
    require(plan['root'] == str(root) and plan['uuid'] == DEVICES[index] and plan['source_root'] == str(SOURCE), 'exact_plan_host_source')
    for key in ('source_manifest', 'cpu_tests', 'initial_carry', 'dev', 'exclusions', 'lease_source'):
        require(sha(plan[key]['path']) == plan[key]['sha256'], 'pinned_' + key)
    require(read(plan['cpu_tests']['path'])['passed'], 'CPU_tests_required')
    for name, digest in read(plan['source_manifest']['path']).items():
        require(sha(SOURCE / name) == digest, 'immutable_source:' + name)
    validate_lineage(plan['record'])
    require(time.time() < plan['hard_end'] and plan['hard_end'] <= plan['lease_end'] - 21600, 'lease_margin')
    return root, plan


def mounted(plan, phase):
    bind()
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == plan['uuid'], 'UUID_CVD')
    require(('CUDA_VISIBLE_DEVICES=' + plan['uuid']).encode() in Path('/proc/self/environ').read_bytes().split(b'\0'), 'startup_CVD')
    actual = subprocess.check_output(['nvidia-smi', '-i', str(plan['index']), '--query-gpu=uuid', '--format=csv,noheader'], text=True).strip()
    require(actual == plan['uuid'], 'physical_UUID')
    base = math.reuse.driver.seam.portable.verify_base_files(math.BUNDLE, math.MODEL,
        expected_manifest_sha256=math.reuse.node_limits.BUNDLE_SHA)
    identity = validate_lineage(plan['record'])
    return dict(phase=phase, process=reuse.native.process_identity(), uuid=actual,
        adapter=identity.document(), base=base, optimizer_loaded=False, weight_updates=0, observed_unix=time.time())


def load(plan, check, readout=False):
    identity = validate_lineage(plan['record'])
    binding = reuse.native.bridge.StageBinding(f'R122_A100_{plan["index"]}', reuse.native.bridge.ARMS[0], 0,
        'sealed_readout' if readout else 'collection', identity, not readout, True, sha(Path(plan['root']) / 'PLAN.json'))
    stage = reuse.native.load_stage(binding, model_dir=math.MODEL, device='cuda:0', gpu_uuid=plan['uuid'],
        context=reuse.native.StageContext(private_guidance=() if readout else ('PRIVATE_TRAIN_PARENT_ONLY',)), check=check)
    return reuse.Actor(stage)


def charge(root, kind, metadata):
    with (root / 'LEDGER.lock').open('a') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        counters = read(root / 'COUNTERS.json')
        counters[kind] += 1
        require(counters[kind] <= (10000000 if kind == 'native' else 1000000), 'prospective_lease_capacity')
        atomic(root / 'COUNTERS.json', counters)
        write(root / 'reservations' / f'{kind}_{counters[kind]:08d}.json', dict(metadata=metadata, reserved_unix=time.time(), retries=0))
        return counters[kind]


def poll(root, experience):
    for path in sorted((root / 'queue').glob('*.response.json')):
        receipt = root / 'consumed' / path.name
        if receipt.exists():
            continue
        response = read(path)
        request = read(path.with_name(path.name.replace('.response.json', '.request.json')))
        require(response['request_sha256'] == math.policy.digest(request), 'bound_parent')
        for name, digest in response['archive']['files'].items():
            require(Path(name).name == name and sha(Path(response['archive']['root']) / name) == digest, 'native_parent_archive')
        accepted = response['status'] in ('COMPLETE', 'SILENT') and time.time() < request['lane_deadline_unix']
        if accepted and response.get('guidance'):
            experience.append(math.policy.event('parent', response['guidance'], 'TRAIN', reference(path)))
        write(receipt, dict(accepted=accepted, status=response['status'], source=reference(path), observed_unix=time.time()))


def call(root, actor, task, experience, invitation, purpose, cap, carry=None, split='TRAIN'):
    if split == 'TRAIN':
        poll(root, experience)
        messages = math.policy.messages(experience, invitation, carry)
    else:
        messages = math.policy.readout_messages(task, 'held')
    tokens = actor.tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_dict=False)
    cap = min(cap, 16384 - len(tokens))
    require(cap > 0, 'no_prompt_truncation')
    identifier = charge(root, 'native', dict(task_id=task['id'], split=split, purpose=purpose))
    path = root / 'calls' / f'CALL_{identifier:08d}.json'
    started = time.time()
    write(path.with_suffix('.request.json'), dict(messages=messages, task_id=task['id'], split=split,
        purpose=purpose, cap=cap, started_unix=started, process=reuse.native.process_identity()))
    actor.purpose = purpose
    response = actor.generate(messages, max_new_tokens=cap)
    item = dict(status='COMPLETE', task_id=task['id'], split=split, purpose=purpose, response=response,
        messages=messages, started_unix=started, completed_unix=time.time(), token_count=len(response['token_ids']), raw_saved_before_parser=True)
    write(path, item)
    event = math.policy.event('child', response['raw'], split, reference(path))
    if split == 'TRAIN':
        experience.append(event)
    return response, event


def resident(index, readout=False):
    root, plan = validate(index)
    def check(label):
        require(time.time() < plan['native_end'], 'lease_native_wall:' + label)
    suffix = 'READOUT' + os.environ.get('R122_CYCLE', '') if readout else 'RESIDENT'
    write(root / (suffix + '_BEFORE.json'), mounted(plan, 'before'))
    actor = load(plan, check, readout)
    write(root / (suffix + '_LOADED.json'), dict(process=reuse.native.process_identity(),
        adapter=actor.loaded.observed.document(), optimizer_loaded=False, weight_updates=0, loaded_unix=time.time()))
    status = 'FAILED'
    try:
        if readout:
            for task in read(root / 'DEV.json'):
                call(root, actor, task, None, '', 'held', 2048, split='DEV')
            status = 'COMPLETE'
            return
        cursor = read(root / 'CURSOR.json')
        carry = read(cursor['carry']['path'])
        excluded = set(read(root / 'EXCLUSIONS.json'))
        cycle = cursor['next_cycle']
        while time.time() < plan['native_end'] - 900:
            output = root / f'cycle{cycle:06d}'
            tasks = fresh_pair(index, cycle, excluded)
            excluded.update(task['question_sha256'] for task in tasks)
            write(output / 'TRAIN.json', tasks)
            combined = math.policy.Experience()
            for episode, task in enumerate(tasks):
                experience = math.policy.Experience()
                experience.append(math.policy.event('environment', task['question'] + '\n\n' + math.policy.ENVIRONMENT, 'TRAIN', task['question_sha256']))
                response, event = call(root, actor, task, experience, math.policy.previous.original.EPISODE.format(question=task['question']), 'episode', 2048, carry)
                outcome = gym.judge(task, response)
                experience.append(math.policy.event('environment', 'Checker feedback delivered to you: ' + json.dumps(outcome), 'TRAIN', outcome))
                identifier = f'C{cycle:06d}_E{episode}'
                payload = experience.payload(task, f'R122_A100_{index}', cycle, episode, 'experience', sha(root / 'PLAN.json'))
                request = dict(id=identifier, payload=payload, payload_sha256=math.policy.digest(payload), lane_deadline_unix=min(time.time() + 600, plan['native_end']))
                charge(root, 'parent', dict(id=identifier, nonblocking=True))
                write(root / 'queue' / (identifier + '.request.json'), request)
                response, event = call(root, actor, task, experience, math.policy.previous.OPEN_TURN, 'open_turn', 1024)
                observations = math.environment(experience, task, response)
                write(output / f'EPISODE_{episode}.json', dict(task_id=task['id'], outcome=outcome, observations=observations, events=experience.events))
                for event in experience.events:
                    combined.append(event)
            call(root, actor, tasks[-1], combined, math.policy.previous.original.PRESLEEP, 'presleep', 4096)
            response, carry = call(root, actor, tasks[-1], combined, math.policy.previous.original.REFLECTION, 'reflection', 3072)
            write(output / 'CARRY.json', carry)
            write(output / 'EXPERIENCE.json', combined.events)
            write(output / 'CONTEXT_BOUNDARY.json', dict(cycle=cycle, episodes=2, weight_sleep=False, optimizer_updates=0, completed_unix=time.time()))
            with (output / 'DEV.log').open('x') as log:
                child = subprocess.Popen([sys.executable, '-B', '-m', MODULE, 'readout', '--index', str(index)],
                    env=dict(os.environ, R122_CYCLE=str(cycle)), stdout=log, stderr=subprocess.STDOUT)
                identity = math.common.process_identity(Path('/proc') / str(child.pid))
                write(output / 'DEV_LAUNCH.json', dict(identity=identity, parent_free=True, fresh_process=True))
                try:
                    code = child.wait(timeout=min(900, plan['hard_end'] - time.time()))
                except subprocess.TimeoutExpired:
                    math.common.stop_owned(child, identity)
                    code = child.returncode
                write(output / 'DEV_RESULT.json', dict(status='COMPLETE' if code == 0 else 'FAILED_NO_RETRY', returncode=code))
            cycle += 1
            atomic(root / 'CURSOR.json', dict(next_cycle=cycle, carry=reference(output / 'CARRY.json')))
        status = 'LEASE_BOUNDARY'
    finally:
        observed = reuse.native.observe_adapter(actor.loaded.engine, actor.loaded.observed)
        write(root / (suffix + '_AFTER.json'), dict(mounted=mounted(plan, 'after'), adapter=observed.document()))
        write(root / (suffix + '_TERMINAL.json'), dict(status=status, process=reuse.native.process_identity(), finished_unix=time.time(), optimizer_updates=0))


def scan(index):
    bind()
    service = ROOT / f'lane{index}/SERVICE.json'
    return admission.bind_scan(lambda: argv_scan.scan(index, service))


def guard(index):
    root, plan = validate(index)
    with (root / 'GUARD.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require(not (root / 'LAUNCH.json').exists(), 'no_duplicate_native_launch')
        command = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONPATH=' + str(SOURCE), 'PYTHONDONTWRITEBYTECODE=1', 'python3', '-B', '-m', MODULE]
        subprocess.run(command + ['service', '--index', str(index)], check=True, timeout=30)
        result = subprocess.run(command + ['scan', '--index', str(index)], capture_output=True, text=True, check=True, timeout=150)
        report = json.loads(result.stdout)
        write(root / 'ADMISSION.json', report)
        require(report['clear'] and report['scanner_euid'] == 0 and not report['blocking_reasons'] and report['gpu']['uuid'] == plan['uuid'], 'strict_full_proc_admission')
        with (root / 'NATIVE.log').open('x') as log:
            child = subprocess.Popen([math.PYTHON, '-B', '-m', MODULE, 'resident', '--index', str(index)],
                cwd=SOURCE, env=dict(os.environ, CUDA_VISIBLE_DEVICES=plan['uuid'], HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                    OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', PYTHONPATH=str(SOURCE)),
                stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            identity = math.common.process_identity(Path('/proc') / str(child.pid))
            write(root / 'LAUNCH.json', dict(identity=identity, plan=reference(root / 'PLAN.json'), started_unix=time.time()))
            try:
                code = child.wait(timeout=plan['hard_end'] - time.time())
            except subprocess.TimeoutExpired:
                math.common.stop_owned(child, identity)
                code = child.returncode
            write(root / 'GUARD_TERMINAL.json', dict(returncode=code, identity=identity, finished_unix=time.time()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('prepare', 'guard', 'resident', 'readout', 'service', 'scan'))
    parser.add_argument('--index', type=int, choices=(5, 6, 7), required=True)
    args = parser.parse_args()
    if args.action == 'service':
        bind()
        scanner.pinned.service(ROOT / f'lane{args.index}/SERVICE.json')
    elif args.action == 'readout':
        resident(args.index, True)
    else:
        result = globals()[args.action](args.index)
        if result is not None:
            print(json.dumps(result))
