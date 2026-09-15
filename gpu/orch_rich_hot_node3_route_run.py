"""Backfill only completed node3 generators; original common caps never reset."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import subprocess
import time

from gpu import astra_portable_actor_bundle as portable
from gpu import orch_rich_intensity_guard as ownership
from gpu.orch_rich_hot_node3_run import Engine, bind_host, reserve
from gpu.orch_rich_hot_node1_run import sha, write
from gpu.orch_math_replication_guard import verify_sources
from gpu.orch_math_rich_screen import mounted_adapter_parameters
from organism_v6 import orch_rich_hot_node3_route as route
from organism_v6 import orch_rich_hot_node3 as limits


ORIGINAL_ROOT = Path('/localhome/local-rohing/orch_rich_hot_node3_20260915_attempt1')
PREVIOUS = {3: ('repair1', 130587), 4: ('attempt1', 129826), 5: ('attempt1', 129833)}


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
    for world in cohort['worlds']:
        for task in route.tasks(world):
            prompt = [dict(role='system', content=route.original.SYSTEM + '\n\n' + route.GUIDANCE),
                dict(role='user', content=route.original.readout.display(task['node'], task, task['ports']))]
            tokens = tokenizer.apply_chat_template(prompt, tokenize=True, add_generation_prompt=True, return_dict=False)
            limits.context_check(len(tokens))
            lengths.append(len(tokens))
    lifetime = json.loads((ORIGINAL_ROOT / 'run/START.json').read_text())
    assert time.time() < lifetime['native_deadline_unix']
    current_calls = len((ORIGINAL_ROOT / 'CALL_RESERVATIONS.jsonl').read_text().splitlines())
    previous_three = Path('/localhome/local-rohing/orch_rich_hot_node3_20260915_repair1/run/shard3')
    remaining_v1 = max(0, 256 - len(list(previous_three.glob('INTENT_*.json'))))
    assert current_calls + remaining_v1 + 576 <= limits.MAX_CALLS
    write(root / 'PREPARED.json', dict(status='PREPARED_NO_MODEL', native_calls=0, fits=0, updates=0,
        base_verification=verification, phase_version=route.PHASE, task_count=len(lengths),
        maximum_prompt_tokens=max(lengths), source_events=len(store),
        files={name: sha(root / name) for name in ('COHORT.json', 'SOURCE_EVENTS.json', 'SOURCE_SHA256.json', 'PROTOCOL.json')},
        inherited_start_sha256=sha(ORIGINAL_ROOT / 'run/START.json'),
        inherited_hard_deadline_unix=lifetime['hard_deadline_unix'], maximum_route_calls=576,
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
            for task_index, task in enumerate(route.tasks(world)):
                task_id = f'route-train-{world_index}-{task_index}'

                def generate(messages):
                    nonlocal calls
                    check('route_turn')
                    assert calls < 192
                    intent = reserve(ORIGINAL_ROOT, dict(phase_version=route.PHASE, family='route',
                        physical_index=index, task_id=task_id, started_unix=time.time(),
                        messages=messages, max_new_tokens=8192, kind='route_turn'))
                    calls += 1
                    write(output / f'INTENT_{calls:04d}.json', intent)
                    try:
                        response = engine.generate(messages, max_new_tokens=8192)
                    except BaseException as error:
                        write(output / f'CALL_{calls:04d}_FAILED.json', dict(intent, error=str(error),
                            error_type=type(error).__name__, finished_unix=time.time()))
                        raise
                    write(output / f'CALL_{calls:04d}.json', dict(intent, response=response,
                        generated_tokens=len(response['token_ids']) - int(response['terminal']),
                        finished_unix=time.time(), elapsed_seconds=time.time() - intent['started_unix'],
                        semantic_status='UNREVIEWED', admitted=False, trainingAllowed=False,
                        episode_receipt=f'EPISODE_{world_index}_{task_index}.json',
                        source_events_sha256=prepared['files']['SOURCE_EVENTS.json'], source_state=portable.PARENT_STATE))
                    write(output / 'PROGRESS.json', dict(index=index, calls=calls, task_id=task_id,
                        phase_version=route.PHASE, updated_unix=time.time()))
                    return response

                record = route.episode(world, task, generate, store)
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
    stage, previous_pid = PREVIOUS[index]
    old = Path('/localhome/local-rohing/orch_rich_hot_node3_20260915_' + stage) / 'run' / f'shard{index}'
    lifetime = json.loads((ORIGINAL_ROOT / 'run/START.json').read_text())
    while (Path('/proc') / str(previous_pid)).exists():
        assert time.time() < lifetime['native_deadline_unix']
        time.sleep(2)
    assert json.loads((old / 'RESULT.json').read_text())['status'] == 'COMPLETE'
    verify_sources(root / 'source', root / 'SOURCE_SHA256.json')
    snapshot = ownership.scan(index, root / 'SERVICE_IDENTITY.json')
    write(root / f'ADMISSION_{index}.json', snapshot)
    assert snapshot['clear']
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES=ownership.DEVICES[index], PYTHONPATH=str(root / 'source'),
        HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='1',
        MKL_NUM_THREADS='1', TOKENIZERS_PARALLELISM='false')
    with (root / f'shard{index}.log').open('x') as log:
        child = subprocess.Popen([ownership.existing.PYTHON, '-B', '-m', 'gpu.orch_rich_hot_node3_route_run',
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
