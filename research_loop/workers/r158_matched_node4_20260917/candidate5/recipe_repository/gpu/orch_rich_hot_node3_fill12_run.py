"""Isolated two-slot fillers; native raw and all ownership receipts stay on-node."""

import argparse
import fcntl
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
from gpu.orch_rich_hot_node1_run import sha, write
from gpu.orch_rich_hot_node1_scan import process_identity
from gpu.orch_math_replication_guard import verify_sources
from gpu.orch_math_rich_screen import mounted_adapter_parameters
from organism_v6 import orch_rich_hot_node3 as original
from organism_v6 import orch_rich_intensity as prior
from organism_v6 import orch_rich_hot_node3_fill12 as policy


ORIGINAL = Path('/localhome/local-rohing/orch_rich_hot_node3_20260915_attempt1')


def release_requested(root, index):
    path = root / f'RELEASE_REQUEST_{index}.json'
    if not path.exists():
        return False
    request = json.loads(path.read_text())
    assert request['index'] == index and request['uuid'] == ownership.DEVICES[index]
    assert request['root'] == str(root) and request['canonical_ready'] is True
    assert request['requester'] in ('Main', 'Pasteur') and request['handoff_reference']
    return True


def reserve(root, index, intent):
    policy.condition(index)
    with (root / 'CALL_RESERVATIONS.jsonl').open('a+') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        stream.seek(0)
        reservations = [json.loads(line) for line in stream if line.strip()]
        own = sum(row['index'] == index for row in reservations)
        if not policy.can_dispatch(time.time(), own, len(reservations), release_requested(root, index)):
            return None
        record = dict(intent, index=index, global_call=len(reservations) + 1, slot_call=own + 1,
                      phase_version=policy.PHASE, arm=policy.exhaustion.arm(policy.condition(index)))
        stream.write(json.dumps(record, sort_keys=True) + '\n')
        stream.flush()
        os.fsync(stream.fileno())
        return record


def prepare(root):
    bind_host()
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
    assert time.time() < policy.DISPATCH_CUTOFF
    verify_sources(root / 'source', root / 'SOURCE_SHA256.json')
    assert sha(root / 'TASKS.json') == original.TASKS_SHA == sha(ORIGINAL / 'TASKS.json')
    document = json.loads((root / 'TASKS.json').read_text())
    prior.validate(document)
    assert json.loads((root / 'PROTOCOL.json').read_text()) == policy.protocol()
    handoff = json.loads((root / 'OWNED_HANDOFF.json').read_text())
    assert handoff['released'] and handoff['physical_indices'] == [1, 2]
    assert handoff['uuids'] == [ownership.DEVICES[index] for index in (1, 2)]
    assert handoff['physical0_untouched'] and handoff['no_future_route_launch_on_released_lanes_without_new_handoff']
    config_path = Path(ownership.existing.MODEL) / 'config.json'
    config = json.loads(config_path.read_text())
    assert config['model_type'] == 'qwen2' and config['hidden_size'] == 3584
    assert config['num_hidden_layers'] == 28 and config['max_position_embeddings'] >= 32768
    assert config.get('rope_scaling') is None
    base = portable.verify_base_files(ownership.existing.BUNDLE, ownership.existing.MODEL,
                                     expected_manifest_sha256=original.BUNDLE_SHA)
    tokenizer = portable.source.native.load_local_tokenizer(ownership.existing.MODEL)
    lengths = []
    for index in (1, 2):
        for task in document['tasks']:
            encoded = tokenizer.apply_chat_template(policy.messages(task, index), tokenize=True,
                                                     add_generation_prompt=True, return_dict=False)
            policy.exhaustion.token_budget(len(encoded))
            lengths.append(len(encoded))
    write(root / 'PREPARED.json', dict(status='PREPARED_NO_MODEL', native_calls=0, fits=0, updates=0,
        base_verification=base, adapter_state=portable.PARENT_STATE, source_prompts_checked=len(lengths),
        maximum_prompt_tokens=max(lengths), config_sha256=sha(config_path), max_position_embeddings=32768,
        rope_scaling=None, files={name:sha(root / name) for name in
            ('TASKS.json', 'SOURCE_SHA256.json', 'PROTOCOL.json', 'OWNED_HANDOFF.json', 'SEGMENT.json')},
        finished_unix=time.time()))


def run(root, index):
    bind_host()
    policy.condition(index)
    uuid = ownership.DEVICES[index]
    assert os.environ['CUDA_VISIBLE_DEVICES'] == uuid
    assert ('CUDA_VISIBLE_DEVICES=' + uuid).encode() in Path('/proc/self/environ').read_bytes().split(b'\0')
    prepared = json.loads((root / 'PREPARED.json').read_text())
    for name, expected in prepared['files'].items():
        assert sha(root / name) == expected
    output = root / f'shard{index}'
    output.mkdir(exist_ok=False)
    calls = 0

    def check(label):
        if time.time() >= policy.HARD_END:
            raise TimeoutError('filler_hard_end:' + label)
        if label == 'generation' and time.time() >= policy.DISPATCH_CUTOFF:
            raise TimeoutError('filler_dispatch_cutoff')

    def interrupted(signum, frame):
        raise SystemExit(128 + signum)

    signal.signal(signal.SIGTERM, interrupted)
    try:
        check('load')
        portable.verify_base_files(ownership.existing.BUNDLE, ownership.existing.MODEL,
                                  expected_manifest_sha256=original.BUNDLE_SHA)
        arguments = portable.read_bundle(ownership.existing.BUNDLE,
            expected_manifest_sha256=original.BUNDLE_SHA, model_dir=ownership.existing.MODEL,
            device='cuda:0', gpu_uuid=uuid)
        engine = Engine(arguments, portable.source.native.load_local_tokenizer(arguments.model_dir), check=check)
        from organism_v6.pcfl_vertical_train import _state_hash
        parameters = mounted_adapter_parameters(engine.model)
        assert _state_hash(parameters) == portable.PARENT_STATE
        write(output / 'ACTOR_READY.json', dict(index=index, pid=os.getpid(), uuid=uuid,
            phase_version=policy.PHASE, ready_unix=time.time(), all_parameters_frozen=True,
            adapter_state=portable.PARENT_STATE, fits=0, updates=0))
        for task in json.loads((root / 'TASKS.json').read_text())['tasks']:
            if time.time() >= policy.DISPATCH_CUTOFF or release_requested(root, index):
                break
            messages = policy.messages(task, index)
            tokens = engine.tokenizer.apply_chat_template(messages, tokenize=True,
                add_generation_prompt=True, return_dict=False)
            cap = policy.exhaustion.token_budget(len(tokens))
            intent = reserve(root, index, dict(task_id=task['id'], messages=messages,
                prompt_tokens=len(tokens), max_new_tokens=cap, started_unix=time.time(),
                tasks_sha256=prepared['files']['TASKS.json'], source_sha256=prepared['files']['SOURCE_SHA256.json']))
            if intent is None:
                break
            calls += 1
            write(output / f'INTENT_{calls:04d}.json', intent)
            try:
                response = engine.generate(messages, max_new_tokens=cap)
            except BaseException as error:
                write(output / f'CALL_{calls:04d}_FAILED.json', dict(intent, error_type=type(error).__name__,
                    error=str(error), finished_unix=time.time(), partial_native_tokens_unavailable=True))
                raise
            outcome = policy.exhaustion.outcome(task, response)
            write(output / f'CALL_{calls:04d}.json', dict(intent, response=response, outcome=outcome,
                approach_assessment=policy.exhaustion.assess(response), source_state=portable.PARENT_STATE,
                elapsed_seconds=time.time()-intent['started_unix'], finished_unix=time.time(),
                trainingAllowed=False, semantic_status='UNREVIEWED'))
            write(output / f'EPISODE_{calls:04d}.json', dict(task_id=task['id'], global_call=intent['global_call'],
                completed=True, outcome=outcome, finished_unix=time.time()))
            write(output / 'PROGRESS.json', dict(index=index, calls=calls, task_id=task['id'],
                phase_version=policy.PHASE, max_new_tokens=cap, generated_tokens=outcome['content_tokens'],
                updated_unix=time.time()))
        assert _state_hash(parameters) == portable.PARENT_STATE
        paths = sorted(output.glob('CALL_[0-9][0-9][0-9][0-9].json'))
        episodes = sorted(output.glob('EPISODE_*.json'))
        assert len(paths) == len(episodes) == calls
        write(output / 'CHECKPOINT.json', dict(safe_episode_boundary=True, pending_calls=0, calls=calls,
            files={str(path.relative_to(root)):sha(path) for path in paths+episodes}, created_unix=time.time()))
        write(output / 'RESULT.json', dict(status='COMPLETE_BOUNDARY', calls=calls,
            release_requested=release_requested(root,index), finished_unix=time.time()))
    except BaseException as error:
        write(output / 'FAILED.json', dict(error_type=type(error).__name__, error=str(error),
            calls=calls, finished_unix=time.time(), phase_version=policy.PHASE))
        raise


def watch(root, index):
    bind_host()
    policy.condition(index)
    verify_sources(root / 'source', root / 'SOURCE_SHA256.json')
    publication = json.loads((root / 'PUBLICATION.json').read_text())
    assert publication['own_cpu_tests_passed'] and publication['dated_builder_publication']
    for name, expected in publication['files'].items():
        assert sha(root / name) == expected
    assert time.time() < policy.DISPATCH_CUTOFF and not release_requested(root,index)
    with (root / f'WATCH_{index}.lock').open('x') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        for attempt in range(12):
            snapshot = ownership.scan(index, root / 'SERVICE_IDENTITY.json')
            write(root / f'ADMISSION_{index}_{attempt:02d}.json', snapshot)
            if snapshot['clear']:
                break
            time.sleep(2)
        assert snapshot['clear'] and time.time() < policy.DISPATCH_CUTOFF
        environment = dict(os.environ, CUDA_VISIBLE_DEVICES=ownership.DEVICES[index],
            PYTHONPATH=str(root/'source'), HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
            PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', TOKENIZERS_PARALLELISM='false')
        with (root / f'shard{index}.log').open('x') as log:
            child = subprocess.Popen([ownership.existing.PYTHON,'-B','-m','gpu.orch_rich_hot_node3_fill12_run',
                'run','--root',str(root),'--index',str(index)],cwd=root/'source',env=environment,
                stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            identity = process_identity(Path('/proc')/str(child.pid))
            write(root/f'LAUNCH_{index}.json',dict(index=index,identity=identity,uuid=ownership.DEVICES[index],
                phase_version=policy.PHASE,started_unix=time.time()))
            try:
                while child.poll() is None and time.time() < policy.HARD_END - 30:
                    time.sleep(1)
            finally:
                if child.poll() is None:
                    assert process_identity(Path('/proc')/str(child.pid)) == identity
                    ownership.existing.stop_owned(child)
                snapshot = ownership.scan(index,root/'SERVICE_IDENTITY.json')
                write(root/f'RELEASE_SCAN_{index}.json',snapshot)
                write(root/f'RELEASE_{index}.json',dict(index=index,identity=identity,uuid=ownership.DEVICES[index],
                    released=snapshot['clear'],returncode=child.returncode,finished_unix=time.time(),
                    safe_episode_boundary=(root/f'shard{index}/CHECKPOINT.json').exists(),
                    no_automatic_reclaim=True,canonical_requires_exact_receipt=True))


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('phase',choices=('prepare','run','watch'))
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--index',type=int,choices=(1,2))
    options=parser.parse_args()
    if options.phase=='prepare':
        prepare(options.root)
    else:
        globals()[options.phase](options.root,options.index)
