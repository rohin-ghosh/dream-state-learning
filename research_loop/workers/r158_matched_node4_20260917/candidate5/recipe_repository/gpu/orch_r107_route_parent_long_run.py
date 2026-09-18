"""Bounded long A1001/5 route-only discovery, with no optimizer or actor retries."""

import argparse
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import time

from gpu import astra_portable_actor_bundle as portable
from gpu import orch_math_pipeline_l2_run as common
from gpu import orch_r107_route_parent_long_scan as admission
from gpu.orch_r107_route_parent_long_engine import Engine
from gpu.orch_rich_hot_node3_base107_engine import assert_no_adapter
from gpu.orch_r107_route_parent_long_protocol import parse as parse_parent, protocol_status
from organism_v6 import orch_r107_route_parent_long as policy


ROOT = Path('/localhome/local-rohing/orch_r107_route_parent_20260915_attempt3_long')
ORIGINAL = Path('/localhome/local-rohing/orch_math_pipeline_l2_20260915_attempt1')
BUNDLE_SHA = '5e675c309b202625a6ddf1d36c1a58f51ef656985821cec1cd6123424d927469'
write, read, sha = common.write, common.read, common.sha


def verify(root):
    policy.require(root == ROOT and root.resolve() == root and common.host_identity() == policy.HOST_SHA,
                   'exact_new_root_and_hashed_host')
    source = read(root / 'SOURCE_SHA256.json')
    for relative, expected in source.items():
        policy.require(sha(root / 'source' / relative) == expected, 'source_changed:' + relative)
    return source


def inventory():
    from xml.etree import ElementTree
    import stat
    xml = ElementTree.fromstring(subprocess.check_output(['nvidia-smi', '-q', '-x'], text=True))
    minors = {gpu.findtext('uuid'): int(gpu.findtext('minor_number')) for gpu in xml.findall('gpu')}
    kernel = {}
    for path in Path('/proc/driver/nvidia/gpus').glob('*/information'):
        fields = dict(line.split(':', 1) for line in path.read_text().splitlines() if ':' in line)
        kernel[fields['GPU UUID'].strip()] = int(fields['Device Minor'].strip())
    rows = []
    for line in subprocess.check_output(['nvidia-smi', '--query-gpu=index,uuid', '--format=csv,noheader,nounits'], text=True).splitlines():
        index, uuid = line.split(','); index, uuid = int(index), uuid.strip()
        minor = minors[uuid]; device = Path(f'/dev/nvidia{minor}').stat()
        policy.require(kernel[uuid] == minor and stat.S_ISCHR(device.st_mode) and os.minor(device.st_rdev) == minor,
                       'full_uuid_kernel_minor_mapping')
        if index in policy.DEVICES:
            policy.require(policy.DEVICES[index] == uuid, 'allocation_uuid_changed')
        rows.append(dict(index=index, uuid=uuid, minor=minor))
    policy.require(len(rows) == 8, 'full_inventory')
    return rows


def spend(root, index, kind, detail):
    policy.allocation(index)
    policy.require(kind in ('NATIVE', 'PARENT'), 'known_reservation_kind')
    cap = policy.NATIVE_CAP if kind == 'NATIVE' else policy.PARENT_CAP
    with (root / 'RESERVATIONS.jsonl').open('a+') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        stream.seek(0)
        rows = [json.loads(line) for line in stream if line.strip()]
        own = [row for row in rows if row['index'] == index and row['kind'] == kind]
        total = [row for row in rows if row['kind'] == kind]
        policy.require(len(own) < cap and len(total) < len(policy.DEVICES) * cap, 'explicit_new_segment_cap')
        row = dict(index=index, kind=kind, own_number=len(own) + 1, aggregate_number=len(total) + 1,
                   reserved_unix=time.time(), **detail)
        stream.write(json.dumps(row, sort_keys=True) + '\n'); stream.flush(); os.fsync(stream.fileno())
    return row


def prepare(root):
    policy.require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'cpu_prepare_only')
    verify(root)
    policy.require(not (root / 'PREPARED.json').exists(), 'prepare_once')
    provenance = read(ORIGINAL / 'PREPARE.json')
    base = portable.verify_base_files(provenance['bundle'], provenance['model_dir'], expected_manifest_sha256=BUNDLE_SHA)
    policy.require(base['expected_base_sha256'] == policy.BASE_SHA, 'frozen_base_provenance')
    exclusions = read(root / 'EXCLUSIONS.json')
    seen = set(exclusions['identifiers'])
    cohorts = {}
    for index in policy.DEVICES:
        cohorts[str(index)] = policy.cohort(seen, index)
        seen.update(policy.identifiers(cohorts[str(index)]))
    frozen = dict(by_index=cohorts, independent_lineages=True)
    write(root / 'COHORT.json', frozen)
    tokenizer = portable.source.native.load_local_tokenizer(provenance['model_dir'])
    lengths = []
    for split in ('train', 'held'):
        for group in [group for cohort in cohorts.values() for group in cohort[split]]:
            for task in group['tasks']:
                messages = [dict(role='system', content=policy.SYSTEM + '\n\n' + policy.GUIDANCE),
                    dict(role='user', content=policy.gym.readout.display(task['node'], task, task['ports']))]
                length = len(tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_dict=False))
                policy.token_budget(length); lengths.append(length)
    engine = Engine(provenance['model_dir'], tokenizer, device='cpu', check=lambda phase: None)
    write(root / 'BASE_CPU_IDENTITY.json', dict(actual_base_sha256=engine.loaded_base_sha256,
        no_adapter=engine.no_adapter, runtime=engine.runtime, direct_base=True, gpu_calls=0))
    del engine
    policy.require(sha(root / 'source/gpu/orch_reflection_repetition_stop.py') == policy.STOP_SHA, 'exact_reflection_helper')
    tests = read(root / 'CPU_TESTS.json')
    policy.require(tests['passed'], 'own_native_cpu_tests')
    started = time.time()
    lifetime = dict(started_unix=started, native_deadline_unix=min(started + 7080, common.LEASE_END - 21600 - 120),
        hard_deadline_unix=min(started + 7200, common.LEASE_END - 21600), lease_end_unix=common.LEASE_END,
        lease_margin_seconds=21600, maximum_gpu_hours_per_arm=2.0)
    write(root / 'LIFETIME.json', lifetime)
    write(root / 'INVENTORY.json', inventory())
    files = {name:sha(root / name) for name in ('COHORT.json','EXCLUSIONS.json','SOURCE_SHA256.json',
        'BASE_CPU_IDENTITY.json','CPU_TESTS.json','LIFETIME.json','PRIOR_LEDGERS.json','PROVIDER_FILES.json')}
    prepared = dict(files=files, base=base, model_dir=provenance['model_dir'], bundle=provenance['bundle'],
        source_model_config_sha256=sha(Path(provenance['model_dir']) / 'config.json'),
        maximum_initial_prompt_tokens=max(lengths), output_cap=8192, context=32768,
        new_native_cap=1400, new_parent_cap=40, no_quota_reset=True, no_weight_updates=True,
        planned_upper_native_per_arm=540, reflection_helper_sha256=policy.STOP_SHA)
    write(root / 'PREPARED.json', prepared)
    for index in policy.DEVICES:
        lane = root / f'campaign_route_parent_{index}'
        lane.mkdir(exist_ok=False); (lane / 'base_parent_queue_r107').mkdir()
        write(lane / 'READY.json', dict(index=index, uuid=policy.DEVICES[index], style=policy.STYLES[index],
            family_prepared_sha256=sha(root / 'PREPARED.json'), provider_files=read(root / 'PROVIDER_FILES.json'),
            native_cap=700, parent_cap=20, cycles=10, no_adapter=True, no_optimizer=True,
            held_parent_free=True, own_train_reflection_carry=True, no_L2_to_L1_feed=True))
    print(json.dumps(dict(prepared_sha256=sha(root / 'PREPARED.json'), lifetime=lifetime,
        lane_ready={str(index):sha(root / f'campaign_route_parent_{index}/READY.json') for index in policy.DEVICES})))


def bound_parent(root, lane, index, cycle, episode_index, record, memories, parent_messages, check):
    payload = policy.parent_payload(index, cycle, episode_index, record, memories, parent_messages)
    held = [group['held'] for group in read(root / 'COHORT.json')['by_index'].values()]
    policy.require(not policy.identifiers(payload).intersection(policy.identifiers(held)), 'sealed_held_identifiers_not_exported')
    identifier = f'GUIDED_SLEEP_C{cycle}_P{episode_index}'
    queue = lane / 'base_parent_queue_r107'; request_path = queue / (identifier + '.request.json')
    policy.require(not request_path.exists(), 'parent_no_retry')
    check('parent_dispatch')
    spend(root, index, 'PARENT', dict(cycle=cycle, episode_index=episode_index))
    write(request_path, dict(id=identifier, payload=payload, payload_sha256=policy.digest(payload),
                            ready_sha256=sha(lane / 'READY.json')))
    response_path = queue / (identifier + '.response.json'); until = time.time() + 300
    while not response_path.exists():
        check('parent_wait'); policy.require(time.time() < until, 'parent_timeout_no_retry'); time.sleep(1)
    result = read(response_path)
    policy.require(result['status'] == 'COMPLETE' and result['request_sha256'] == sha(request_path), 'actual_parent_request_join')
    archive = result['archive']; directory = Path(archive['remote_root'])
    policy.require(directory.is_relative_to(root / 'parent_transcripts' / lane.name), 'own_private_parent_archive')
    for name, expected in archive['files'].items():
        policy.require(not Path(name).is_absolute() and '..' not in Path(name).parts and sha(directory / name) == expected,
                       'parent_archive_hash')
    plan = parse_parent(read(directory / 'RAW_RESPONSE.json'), [record['task']['task_id']])
    policy.require(plan == result['plan'] == read(directory / 'PLAN.json'), 'actual_native_parent_response')
    write(lane / f'PARENT_C{cycle}_P{episode_index}.json', dict(result,
        observed_unix=time.time(), held_exposed=False, learning_claim=False,
        protocol_status=protocol_status(read(directory / 'RAW_RESPONSE.json'))))
    return plan['guidance'] + '\n' + plan['episode_guidance'][record['task']['task_id']]


def native(root, index):
    uuid = policy.allocation(index); verify(root)
    policy.require(os.environ.get('CUDA_VISIBLE_DEVICES') == uuid, 'physical_uuid_cvd_binding')
    lane = root / f'campaign_route_parent_{index}'; output = lane / 'native'; output.mkdir(exist_ok=False)
    prepared = read(root / 'PREPARED.json'); lifetime = read(root / 'LIFETIME.json')
    for name, expected in prepared['files'].items():
        policy.require(sha(root / name) == expected, 'prepared_input_changed')

    def check(phase):
        policy.require(time.time() < lifetime['native_deadline_unix'], 'native_deadline:' + phase)

    try:
        tokenizer = portable.source.native.load_local_tokenizer(prepared['model_dir'])
        engine = Engine(prepared['model_dir'], tokenizer, device='cuda:0', check=check)
        write(lane / 'ACTOR_READY.json', dict(index=index, pid=os.getpid(), uuid=uuid,
            base_sha256=engine.loaded_base_sha256, no_adapter=engine.no_adapter,
            input_truncated_contract='EXPLICIT_FALSE_AFTER_FULL_PREFIX_ASSERTION', ready_unix=time.time()))

        def generate(messages, purpose, task_id, cycle):
            check('native_reserve')
            tokens = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_dict=False)
            cap = policy.token_budget(len(tokens))
            intent = spend(root, index, 'NATIVE', dict(purpose=purpose, task_id=task_id, cycle=cycle))
            path = output / f"CALL_{intent['own_number']:04d}.json"
            row = dict(intent, messages=messages, input_tokens=len(tokens), input_token_ids_sha256=policy.digest(tokens),
                effective_cap=cap, started_unix=time.time(), source_state=policy.BASE_SHA, adapter_state=None,
                semantic_functional_change=None, trainingAllowed=False, weight_updates=0)
            write(path, row)
            try:
                response = engine.generate(messages, max_new_tokens=cap, reflection=purpose == 'reflection')
                policy.require(response['input_truncated'] is False and response['full_prompt_prefix_verified'] is True
                    and response['messages'] == messages and response['prompt_token_ids_sha256'] == policy.digest(tokens),
                    'actual_minimal_engine_full_prompt_contract')
                row['response'] = response
            except BaseException as error:
                row['error'] = dict(type=type(error).__name__, message=str(error)); raise
            finally:
                row['finished_unix'] = time.time(); write(path, row)
            write(lane / 'LATEST_NATIVE.json', dict(path=str(path), sha256=sha(path), purpose=purpose,
                content_tokens=len(response['token_ids']) - int(response['terminal']), finished_unix=row['finished_unix']))
            return response

        frozen = read(root / 'COHORT.json')['by_index'][str(index)]; memories, parent_messages = [], []
        for cycle in range(1, policy.CYCLES + 1):
            group = frozen['train'][cycle - 1]
            source = policy.collect_source(group['world'], lambda messages:generate(messages, 'train_source', f'TRAIN-SOURCE-C{cycle}', cycle))
            write(output / f'TRAIN_SOURCE_C{cycle}.json', source)
            for episode_index, task in enumerate(group['tasks'], 1):
                record = policy.episode(group['world'], task,
                    lambda messages:generate(messages, 'train_episode', task['task_id'], cycle), source['store'],
                    memories[-1] if memories else '')
                write(output / f'TRAIN_C{cycle}_E{episode_index}.json', record)
                lesson = bound_parent(root, lane, index, cycle, episode_index, record, memories[-1:], parent_messages[-1:], check)
                parent_messages.append(lesson)
                prompt = [dict(role='system', content=policy.REFLECTION_SYSTEM), dict(role='user', content=json.dumps(dict(
                    actual_train_experience=policy.public_record(record), actual_parent_message=lesson,
                    own_prior_reflection=memories[-1] if memories else ''), sort_keys=True))]
                reflection = generate(prompt, 'reflection', task['task_id'], cycle)
                memories.append(reflection['raw'])
                write(output / f'CARRY_C{cycle}_E{episode_index}.json', dict(own_reflection=reflection,
                    parent_message_sha256=policy.digest(lesson), weight_updates=0))
            group = frozen['held'][cycle - 1]
            source = policy.collect_source(group['world'], lambda messages:generate(messages, 'held_source', f'HELD-SOURCE-C{cycle}', cycle))
            write(output / f'HELD_SOURCE_C{cycle}.json', source)
            for episode_index, task in enumerate(group['tasks'], 1):
                record = policy.episode(group['world'], task,
                    lambda messages:generate(messages, 'held_episode', task['task_id'], cycle), source['store'], memories[-1])
                write(output / f'HELD_C{cycle}_E{episode_index}.json', dict(record, parent_free=True,
                    own_train_context_carried=True, sealed_from_parent=True, retained_weight_learning_claim=False))
            engine.verify_base(); assert_no_adapter(engine.model)
            write(lane / f'CYCLE_{cycle}_COMPLETE.json', dict(finished_unix=time.time(), cycle=cycle,
                held_parent_free=True, base_verified=True, weights_updated=0, functional_diagnostics='UNKNOWN_PENDING_AUDIT'))
        engine.verify_base()
        write(lane / 'COMPLETE.json', dict(finished_unix=time.time(), status='COMPLETE', cycles=policy.CYCLES,
            actual_base_sha256=policy.BASE_SHA, no_adapter=assert_no_adapter(engine.model), fits=0, updates=0))
    except BaseException as error:
        write(lane / 'FAILED.json', dict(type=type(error).__name__, error=str(error), finished_unix=time.time()))
        raise


def guard(root, index):
    policy.allocation(index); verify(root)
    lane = root / f'campaign_route_parent_{index}'
    publication = read(lane / 'PUBLICATION.json')
    policy.require(publication['ready_sha256'] == sha(lane / 'READY.json')
        and publication['allocation_sha256'] == sha(root / 'ALLOCATION.md')
        and publication['dated_builder_publication'], 'publication_before_gpu')
    lifetime = read(root / 'LIFETIME.json'); inventory()
    child = identity = None
    status = 'FAILED'
    try:
        for attempt in range(90):
            policy.require(time.time() < lifetime['native_deadline_unix'], 'admission_deadline')
            snapshot = admission.scan(index, root / 'SERVICE_IDENTITY.json')
            write(lane / f'ADMISSION_{attempt:02d}.json', snapshot)
            if snapshot['clear']:
                break
            time.sleep(3)
        policy.require(snapshot['clear'] and snapshot['scanner_euid'] == 0, 'strict_privileged_clear_required')
        with (lane / 'native.log').open('x') as log:
            child = subprocess.Popen([common.PYTHON, '-B', '-m', 'gpu.orch_r107_route_parent_long_run', 'native',
                '--root', str(root), '--index', str(index)], cwd=root / 'source', start_new_session=True,
                stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                env=dict(os.environ, CUDA_VISIBLE_DEVICES=policy.DEVICES[index], PYTHONPATH=str(root / 'source'),
                    HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', PYTHONDONTWRITEBYTECODE='1',
                    OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', TOKENIZERS_PARALLELISM='false'))
            identity = common.process_identity(Path('/proc') / str(child.pid))
            write(lane / 'LAUNCH.json', dict(pid=child.pid, identity=identity, uuid=policy.DEVICES[index],
                started_unix=time.time(), ready_sha256=sha(lane / 'READY.json')))
            while child.poll() is None:
                policy.require(time.time() < lifetime['hard_deadline_unix'] - 30, 'bounded_hard_end')
                time.sleep(1)
            policy.require(child.returncode == 0 and (lane / 'COMPLETE.json').exists(), 'native_failure_no_replay')
            status = 'COMPLETE'
    except BaseException as error:
        write(lane / 'GUARDIAN_FAILED.json', dict(type=type(error).__name__, error=str(error), finished_unix=time.time()))
        raise
    finally:
        if child is not None:
            common.stop_owned(child, identity)
        write(lane / 'TERMINAL.json', dict(status=status, finished_unix=time.time(), no_refill=True))
        write(lane / 'RELEASE.json', admission.scan(index, root / 'SERVICE_IDENTITY.json'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('prepare', 'native', 'guard'))
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--index', type=int, choices=(1, 5))
    options = parser.parse_args()
    if options.phase == 'prepare':
        prepare(options.root)
    else:
        globals()[options.phase](options.root, options.index)
