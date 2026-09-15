"""Backfill only completed node3 generators; original common caps never reset."""

import argparse
import fcntl
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import subprocess
import time

from gpu import astra_portable_actor_bundle as portable
from gpu import orch_rich_intensity_guard as ownership
from gpu.orch_rich_hot_node3_run import bind_host
from gpu.orch_rich_hot_node1_exhaustion_engine import Engine
from organism_v6 import orch_rich_hot_node1_exhaustion as exhaustion
from gpu.orch_rich_hot_node1_run import sha, write
from gpu.orch_math_replication_guard import verify_sources
from gpu.orch_math_rich_screen import mounted_adapter_parameters
from organism_v6 import orch_rich_hot_node3_exhaustion as route
from organism_v6 import orch_rich_hot_node3 as limits


ORIGINAL_ROOT = Path('/localhome/local-rohing/orch_rich_hot_node3_20260915_attempt1')
PREVIOUS = {3, 4, 5}
PRIOR_ROUTE = Path('/localhome/local-rohing/orch_rich_hot_node3_20260915_route_v2_batch02')


def reserve(root, intent):
    with (root / 'CALL_RESERVATIONS.jsonl').open('a+') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        stream.seek(0)
        count = sum(1 for line in stream if line.strip())
        if count >= 720:
            raise RuntimeError('prospective_exhaustion_segment_720_call_cap')
        record = dict(intent, global_call=count + 1, segment='ROHIN100_ROUTE_720_ADDITIONAL')
        stream.write(json.dumps(record, sort_keys=True) + '\n')
        stream.flush()
        os.fsync(stream.fileno())
        return record


def load_inputs(root):
    cohort = json.loads((root / 'COHORT.json').read_text())
    source = json.loads((root / 'SOURCE_EVENTS.json').read_text())
    return cohort, route.validate(cohort, source)


def prepare(root):
    bind_host()
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
    verify_sources(root / 'source', root / 'SOURCE_SHA256.json')
    cohort, store = load_inputs(root)
    verification = portable.verify_base_files(ownership.existing.BUNDLE, ownership.existing.MODEL,
        expected_manifest_sha256=limits.BUNDLE_SHA)
    tokenizer = portable.source.native.load_local_tokenizer(ownership.existing.MODEL)
    lengths = []
    for row in route.roster(cohort)['tasks']:
        task = row['task']
        prompt = [dict(role='system', content=route.original.SYSTEM + '\n\n' + route.guidance(row['index'])),
            dict(role='user', content=route.original.readout.display(task['node'], task, task['ports']))]
        tokens = tokenizer.apply_chat_template(prompt, tokenize=True, add_generation_prompt=True, return_dict=False)
        exhaustion.token_budget(len(tokens))
        lengths.append(len(tokens))
    lifetime = json.loads((ORIGINAL_ROOT / 'run/START.json').read_text())
    assert time.time() < lifetime['native_deadline_unix']
    current_calls = len((ORIGINAL_ROOT / 'CALL_RESERVATIONS.jsonl').read_text().splitlines())
    assert json.loads((root / 'TASKS.json').read_text()) == route.roster(cohort)
    segment = json.loads((root / 'SEGMENT.json').read_text())
    assert segment['maximum_calls'] == 720 and segment['prior_segment_cap'] == 2048
    assert segment['aggregate_cap_ceiling'] == 2768 and segment['no_quota_reset']
    remaining_v1 = 0
    config = json.loads((Path(ownership.existing.MODEL) / 'config.json').read_text())
    assert config['max_position_embeddings'] >= 32768 and config.get('rope_scaling') is None
    assert config['hidden_size'] == 3584 and config['num_hidden_layers'] == 28
    write(root / 'PREPARED.json', dict(status='PREPARED_NO_MODEL', native_calls=0, fits=0, updates=0,
        base_verification=verification, phase_version=route.PHASE, task_count=len(lengths),
        maximum_prompt_tokens=max(lengths), source_events=len(store),
        files={name: sha(root / name) for name in ('COHORT.json', 'SOURCE_EVENTS.json', 'SOURCE_SHA256.json', 'PROTOCOL.json', 'TASKS.json', 'SEGMENT.json')},
        inherited_start_sha256=sha(ORIGINAL_ROOT / 'run/START.json'),
        inherited_hard_deadline_unix=lifetime['hard_deadline_unix'], maximum_route_calls=720, requested_output_cap=16384, requested_context=32768, native_config_sha256=sha(Path(ownership.existing.MODEL) / 'config.json'), max_position_embeddings=config['max_position_embeddings'], rope_scaling=config.get('rope_scaling'),
        existing_reserved_calls=current_calls, remaining_v1_upper_bound=remaining_v1))


def run(root, index):
    assert index in PREVIOUS
    bind_host()
    uuid = ownership.DEVICES[index]
    assert os.environ['CUDA_VISIBLE_DEVICES'] == uuid
    output = root / f'shard{index}'
    output.mkdir(exist_ok=False)
    prepared = json.loads((root / 'PREPARED.json').read_text())
    for name, expected in prepared['files'].items():
        assert sha(root / name) == expected
    assert sha(ORIGINAL_ROOT / 'run/START.json') == prepared['inherited_start_sha256']
    lifetime = json.loads((ORIGINAL_ROOT / 'run/START.json').read_text())
    calls = 0

    def check(label):
        if time.time() >= lifetime['native_deadline_unix']:
            raise TimeoutError('inherited_node3_deadline:' + label)

    try:
        cohort, store = load_inputs(root)
        portable.verify_base_files(ownership.existing.BUNDLE, ownership.existing.MODEL,
            expected_manifest_sha256=limits.BUNDLE_SHA)
        arguments = portable.read_bundle(ownership.existing.BUNDLE, expected_manifest_sha256=limits.BUNDLE_SHA,
            model_dir=ownership.existing.MODEL, device='cuda:0', gpu_uuid=uuid)
        engine = Engine(arguments, portable.source.native.load_local_tokenizer(arguments.model_dir), check=check)
        from organism_v6.pcfl_vertical_train import _state_hash
        parameters = mounted_adapter_parameters(engine.model)
        assert _state_hash(parameters) == portable.PARENT_STATE
        write(output / 'ACTOR_READY.json', dict(pid=os.getpid(), index=index, uuid=uuid,
            phase_version=route.PHASE, adapter_state=portable.PARENT_STATE, ready_unix=time.time()))
        for world_index, world in enumerate(cohort['worlds']):
            for task_index, task in enumerate(route.tasks(world, index)):
                task_id = 'route-train-display-' + route.original.digest(task)

                def generate(messages):
                    nonlocal calls
                    check('route_turn')
                    assert calls < 240
                    tokens = engine.tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_dict=False)
                    call_cap = exhaustion.token_budget(len(tokens))
                    intent = reserve(root, dict(phase_version=route.PHASE, arm=route.arm(index), family='route',
                        physical_index=index, task_id=task_id, started_unix=time.time(),
                        messages=messages, max_new_tokens=call_cap, kind='route_turn'))
                    calls += 1
                    write(output / f'INTENT_{calls:04d}.json', intent)
                    try:
                        response = engine.generate(messages, max_new_tokens=call_cap)
                    except BaseException as error:
                        write(output / f'CALL_{calls:04d}_FAILED.json', dict(intent, error=str(error),
                            error_type=type(error).__name__, finished_unix=time.time()))
                        raise
                    write(output / f'CALL_{calls:04d}.json', dict(intent, response=response, approach_assessment=exhaustion.assess(response),
                        generated_tokens=len(response['token_ids']) - int(response['terminal']),
                        finished_unix=time.time(), elapsed_seconds=time.time() - intent['started_unix'],
                        semantic_status='UNREVIEWED', admitted=False, trainingAllowed=False,
                        episode_receipt=f'EPISODE_{world_index}_{task_index}.json',
                        source_events_sha256=prepared['files']['SOURCE_EVENTS.json'], source_state=portable.PARENT_STATE))
                    write(output / 'PROGRESS.json', dict(index=index, calls=calls, task_id=task_id,
                        phase_version=route.PHASE, arm=route.arm(index), max_new_tokens=call_cap, updated_unix=time.time()))
                    return response

                record = route.episode(world, task, generate, store, index)
                write(output / f'EPISODE_{world_index}_{task_index}.json', dict(record,
                    task_id=task_id, world=world, phase_version=route.PHASE,
                    semantic_status='UNREVIEWED', admitted=False, trainingAllowed=False))
        engine.verify_base()
        assert _state_hash(parameters) == portable.PARENT_STATE
        write(output / 'RESULT.json', dict(status='COMPLETE', calls=calls,
            phase_version=route.PHASE, finished_unix=time.time(), fits=0, updates=0))
    except BaseException as error:
        write(output / 'FAILED.json', dict(error_type=type(error).__name__, error=str(error),
            calls=calls, finished_unix=time.time()))
        raise


def watch(root, index):
    assert index in PREVIOUS
    bind_host()
    publication = json.loads((root / 'PUBLICATION.json').read_text())
    assert publication['own_cpu_tests_passed'] and publication['dated_builder_publication']
    for name, expected in publication['files'].items():
        assert sha(root / name) == expected
    lifetime = json.loads((ORIGINAL_ROOT / 'run/START.json').read_text())
    assert json.loads((root / f'CHECKPOINT_{index}.json').read_text())['safe_episode_boundary']
    verify_sources(root / 'source', root / 'SOURCE_SHA256.json')
    for attempt in range(12):
        snapshot = ownership.scan(index, root / 'SERVICE_IDENTITY.json')
        write(root / f'ADMISSION_{index}_{attempt:02d}.json', snapshot)
        if snapshot['clear']:
            break
        time.sleep(3)
    assert snapshot['clear']
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES=ownership.DEVICES[index], PYTHONPATH=str(root / 'source'),
        HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='1',
        MKL_NUM_THREADS='1', TOKENIZERS_PARALLELISM='false')
    with (root / f'shard{index}.log').open('x') as log:
        child = subprocess.Popen([ownership.existing.PYTHON, '-B', '-m', 'gpu.orch_rich_hot_node3_exhaustion_run',
            'run', '--root', str(root), '--index', str(index)], cwd=root / 'source',
            env=environment, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        write(root / f'LAUNCH_{index}.json', dict(pid=child.pid, index=index,
            uuid=ownership.DEVICES[index], started_unix=time.time(), phase_version=route.PHASE))
        try:
            while child.poll() is None and time.time() < lifetime['hard_deadline_unix'] - 180:
                time.sleep(2)
        finally:
            ownership.existing.stop_owned(child)
            write(root / f'RELEASE_{index}.json', ownership.scan(index, root / 'SERVICE_IDENTITY.json'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('prepare', 'run', 'watch'))
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--index', type=int, choices=(3, 4, 5))
    options = parser.parse_args()
    if options.phase == 'prepare':
        prepare(options.root)
    else:
        globals()[options.phase](options.root, options.index)
