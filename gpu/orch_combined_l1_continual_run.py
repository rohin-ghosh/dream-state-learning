"""Persistent two-rank-per-arm native LoRA training; no generation during fitting."""

import argparse
from dataclasses import asdict
from datetime import timedelta
import json
import os
from pathlib import Path
import random
import socket
import subprocess
import sys
import time
from types import SimpleNamespace

from gpu import orch_combined_l1_run as combined
from gpu import orch_guided_native as native
from gpu import orch_rich_breadth_bootstrap_run as common
from gpu import orch_rich_hot_a100_minor_scan as minor_scan
from gpu.orch_l2_rich_math_bootstrap import BUNDLE_SHA, LEASE_END, read, sha
from gpu.orch_l2_shared_run import legacy_encode
from gpu.orch_math_rich_source import verify_archive
from organism_v6 import orch_combined_l1_continual as policy
from organism_v6 import orch_l2_rich_math as encoding
from organism_v6.experienced_event_goal_replay_layout import GoalReplayLayout


ROOT = Path('/localhome/local-rohing/orch_combined_l1_continual_20260915_attempt1')
MATH_ROOT = Path('/localhome/local-rohing/orch_rich_breadth_bootstrap_scale764_20260915_attempt1')
PROGRAM = 'gpu.orch_combined_l1_continual_run'
PYTHON = '/localhome/local-rohing/v2/venv/bin/python'
DEVICES = {0: 'GPU-ff5f84e9-c70e-272d-a8e0-eb20aad05ac6',
           1: 'GPU-604c4ea8-8c29-099e-76ed-571ec7d9be4b',
           2: 'GPU-8e15ce78-4e9c-4c48-724f-2b753c6c2296',
           3: 'GPU-631f3e6a-fbce-0ec5-b934-f08dd64634f8',
           6: 'GPU-6de3930d-104a-f969-7d36-009271368dd1'}
TOPOLOGY = {'FULL': (0, 2, 6), 'OFF': (1, 3)}
TRANSITIONAL_TOPOLOGY = {'FULL': (2, 6), 'OFF': (3,)}
INITIAL_TOPOLOGY = {'FULL': (2,), 'OFF': (3,)}
INITIAL_CHILD = Path('/tmp/orch_terse_breadth_20260914_attempt2/train0/adapter')
INITIAL_STATE = 'd13fabd566e04926f45aa66ee0a30ff7dc88d411430ab3e1fe15dfffeb2fd27f'
write = policy.atomic_json


def encode_corpus(rows, tokenizer, cache):
    assert len(rows) >= 2394
    if not cache:
        initial = combined.encode_rows(rows[:2394], tokenizer)
        cache.update({policy.digest(entry): value for entry, value in zip(rows[:2394], initial)})
    encoded = []
    for entry in rows:
        key = policy.digest(entry)
        if key not in cache:
            assert entry['encoding'] in ('math', 'math_content_v2', 'rich_route')
            material = entry['row']
            if entry['encoding'] == 'rich_route':
                student = material['student']
                material = dict(student_prefix=student['messages'][:-1], target=student['target'])
            if entry['encoding'] == 'math_content_v2':
                from gpu.orch_combined_l1_continual_content import encode_rows as content_encode
                cache[key] = content_encode([material], tokenizer)[0]
            else:
                cache[key] = encoding.encode_rows([material], tokenizer)[0]
        encoded.append(cache[key])
    return tuple(encoded)


def scan(index, service):
    assert index in DEVICES
    if os.geteuid() != 0:
        result = subprocess.run(['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=',
            'PYTHONDONTWRITEBYTECODE=1', 'PYTHONPATH=' + str(Path(__file__).resolve().parents[1]),
            'python3', '-B', '-m', PROGRAM, 'scan', '--root', str(ROOT), '--index', str(index)],
            capture_output=True, text=True, timeout=90, check=True)
        return json.loads(result.stdout)
    prior_policy = minor_scan.pinned.policy
    minor_scan.pinned.policy = SimpleNamespace(DEVICES=DEVICES, HOST_SHA=combined.HOST_SHA,
        require=prior_policy.require, allocation=lambda number: prior_policy.require(number in DEVICES, 'unallocated'))
    try:
        return minor_scan.scan(index, service)
    finally:
        minor_scan.pinned.policy = prior_policy


def prepare(root):
    assert root == ROOT and socket.gethostname() == 'a4u8g-0147'
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == '' and not (root / 'PREPARE.json').exists()
    manifest = combined.validate_corpus(root)
    prior = read(MATH_ROOT / 'PREPARE.json')
    common.portable.read_manifest(prior['bundle'], expected_manifest_sha256=BUNDLE_SHA)
    base = common.portable.verify_base_files(prior['bundle'], prior['model_dir'], expected_manifest_sha256=BUNDLE_SHA)
    identity = common.bridge.AdapterIdentity(str(INITIAL_CHILD), INITIAL_STATE,
        prior['initial']['base_sha256'], tuple((path.name, sha(path)) for path in sorted(INITIAL_CHILD.iterdir())
        if path.is_file())).verify()
    tokenizer = native.source.native.load_local_tokenizer(prior['model_dir'])
    legacy = legacy_encode(root, tokenizer)
    new = encode_corpus(read(root / 'PACKET/ADMITTED_ROWS.json'), tokenizer, {})
    layout = GoalReplayLayout(len(new), 1)
    encoded = native.assemble_replay(legacy, new, layout, legacy_reference=legacy, eos_token_id=tokenizer.eos_token_id)
    write(root / 'ENCODER_CHECK.json', dict(status='PASS', native_calls=0, model_loaded=False,
        row_masks=[asdict(row) for row in new], legacy_masks=[asdict(row) for row in legacy]))
    audit = common.token_audit(encoded, layout, tokenizer.pad_token_id)
    audit['scope'] = 'one traversal for audit only; NOT a stopping budget'
    write(root / 'TOKEN_AUDIT.json', audit)
    state = policy.initial_state(read(root / 'PACKET/ADMITTED_ROWS.json'), combined.MANIFEST_SHA)
    write(root / 'CORPORA/000000.json', state)
    for inbox in sorted((root / 'INBOX').glob('*/BOUND_PACKET.json')):
        packet = read(inbox)
        extra = encoding.encode_rows([entry['row'] for entry in packet['rows']], tokenizer)
        native.assemble_replay(legacy, extra, GoalReplayLayout(len(extra), 2),
            legacy_reference=legacy, eos_token_id=tokenizer.eos_token_id)
        write(inbox.parent / 'NATIVE_ENCODER.json', dict(status='PASS', native_calls=0,
            model_loaded=False, rows=len(extra), packet_sha256=sha(inbox),
            row_masks=[asdict(row) for row in extra]))
    names = ('CONTINUAL_PROTOCOL.md', 'CONTINUAL_USER_RELAY.md', 'ALLOCATION_ESTIMATE.json',
             'SERVICE_IDENTITY.json', 'ENCODER_CHECK.json', 'TOKEN_AUDIT.json', 'CORPORA/000000.json')
    write(root / 'PREPARE.json', dict(status='CPU_PREPARED_NO_MODEL', native_calls=0,
        model_dir=prior['model_dir'], bundle=prior['bundle'], base_verification=base, initial=identity.document(),
        recipe=common.RECIPE, corpus=manifest['counts'], topology=TOPOLOGY, initial_topology=INITIAL_TOPOLOGY,
        source_sha256=sha(root / 'source.tar'), source_files=verify_archive(root / 'source.tar', root / 'source'),
        files={name: sha(root / name) for name in names}, manifest_sha256=combined.MANIFEST_SHA,
        packet_sha256=combined.PACKET_SHA, prepared_unix=time.time()))
    print(json.dumps(dict(status='PASS', prepare_sha256=sha(root / 'PREPARE.json'),
                         encoder_sha256=sha(root / 'ENCODER_CHECK.json'), audit=audit), indent=2))


def validate(root):
    assert root == ROOT and socket.gethostname() == 'a4u8g-0147' and not root.is_symlink()
    prepared = read(root / 'PREPARE.json')
    assert sha(root / 'source.tar') == prepared['source_sha256']
    assert verify_archive(root / 'source.tar', root / 'source') == prepared['source_files']
    assert all(sha(root / name) == expected for name, expected in prepared['files'].items())
    assert prepared['recipe'] == common.RECIPE
    combined.validate_corpus(root)
    return prepared


def rng_state(torch):
    import numpy
    return dict(python=random.getstate(), numpy=numpy.random.get_state(),
                torch=torch.get_rng_state(), cuda=torch.cuda.get_rng_state())


def restore_rng(torch, state):
    import numpy
    random.setstate(state['python'])
    numpy.random.set_state(state['numpy'])
    torch.set_rng_state(state['torch'])
    torch.cuda.set_rng_state(state['cuda'])


def checkpoint(root, arm, rank, loaded, state, parameters, world_size):
    torch = loaded.engine.torch
    destination = root / arm / 'checkpoints' / f'{state["update"]:09d}'
    staging = destination.with_name(destination.name + '.pending')
    if rank == 0:
        staging.mkdir(parents=True, exist_ok=False)
    torch.distributed.barrier()
    torch.save(rng_state(torch), staging / f'rank{rank}.pt')
    if world_size == 1:
        torch.save(rng_state(torch), staging / 'rank1.pt')
    if rank == 0 and world_size < 3:
        torch.save(rng_state(torch), staging / 'rank2.pt')
    rank_hashes = [None] * world_size
    torch.distributed.all_gather_object(rank_hashes, native.state_hash(parameters))
    assert len(set(rank_hashes)) == 1, 'replica_adapter_drift'
    if rank == 0:
        loaded.engine.verify_base()
        torch.save(loaded.optimizer.state_dict(), staging / 'optimizer.pt')
        loaded.engine.model.save_pretrained(staging / 'adapter', safe_serialization=True, save_embedding_layers=False)
        adapter = common.bridge.AdapterIdentity(str(destination / 'adapter'), rank_hashes[0],
            loaded.observed.base_sha256, tuple((path.name, sha(path))
                for path in sorted((staging / 'adapter').iterdir()) if path.is_file()))
        metadata = dict(state, adapter=adapter.document(), source_sha256=sha(root / 'source.tar'),
            prepare_sha256=sha(root / 'PREPARE.json'), process=loaded.process,
            world_size=world_size,
            optimizer_preserved=True, rng_per_rank=True,
            expansion_rng='rank0 retained; new rank1 starts from explicitly saved shadow of rank0',
            saved_unix=time.time(), initial_migration=read(root / 'MIGRATION.json')[arm])
        policy.commit_checkpoint(staging, destination, metadata)
        adapter.verify()
        pointer = dict(checkpoint=str(destination), commit_sha256=sha(destination / 'COMMIT.json'),
                       update=state['update'])
        write(root / arm / 'LATEST.json', pointer)
        if arm == 'FULL':
            handoff = dict(schema='COMBINED_CONTINUAL_FULL_CHILD_READY_V1', recipient='Anscombe',
                status='DURABLE_CHECKPOINT_HELD_SCORES_NOT_REQUIRED', child_path=adapter.path,
                adapter=adapter.document(), checkpoint=str(destination),
                commit_sha256=pointer['commit_sha256'], updates=state['update'],
                corpus_version=state['corpus_version'], corpus_sha256=state['corpus_sha256'],
                source_sha256=metadata['source_sha256'], held_results_required=False,
                parent_present=False, no_promotion_claim=True, created_unix=time.time())
            write(root / 'HANDOFFS' / f'{state["update"]:09d}.json', handoff)
            write(root / 'FULL_CHILD_HANDOFF.json', handoff)
    torch.distributed.barrier()


def wait_window(root, update, lifetime):
    path = root / 'WINDOWS' / f'{update:09d}.json'
    while not path.exists():
        assert time.time() < lifetime['native_deadline_unix'], 'window_wait_deadline'
        if (root / 'ABORT.json').exists():
            raise RuntimeError('coordinator_aborted')
        time.sleep(0.2)
    return read(path)


def train(root, arm, rank, port, resume, world_size=1, index=None):
    prepared, lifetime = validate(root), read(root / 'LIFETIME.json')
    assert world_size in (1, 2, 3) and 0 <= rank < world_size
    assert index in TOPOLOGY[arm]
    uuid = DEVICES[index]
    assert os.environ['CUDA_VISIBLE_DEVICES'] == uuid
    migration = read(root / 'MIGRATION.json')[arm]
    previous = policy.verify_checkpoint(resume)['metadata'] if resume else None
    identity = common.bridge.AdapterIdentity.from_document(previous['adapter'] if previous else migration['adapter'])
    binding = common.bridge.StageBinding(root.name, common.bridge.ARMS[2], 0, 'training', identity,
                                        False, False, sha(root / 'PREPARE.json'))
    plan = SimpleNamespace(binding=lambda unused: binding,
        contract=SimpleNamespace(manifest=lambda unused: dict(recipe=common.RECIPE)),
        lineage=SimpleNamespace(arm=common.bridge.ARMS[2]))
    loaded = native.load_training(plan, model_dir=prepared['model_dir'], device='cuda:0', gpu_uuid=uuid,
        context=native.StageContext(), check=lambda label: common.check_deadline(lifetime, label))
    torch = loaded.engine.torch
    torch.cuda.set_device(0)
    torch.distributed.init_process_group('gloo', init_method=f'tcp://127.0.0.1:{port}',
        rank=rank, world_size=world_size, timeout=timedelta(minutes=10))
    parameters = {name: parameter for name, parameter in loaded.engine.model.named_parameters() if native.is_lora(name)}
    if previous:
        if previous['source_sha256'] != prepared['source_sha256']:
            transition = read(root / 'SOURCE_TRANSITION.json')
            assert transition['from_source_sha256'] == previous['source_sha256']
            assert transition['to_source_sha256'] == prepared['source_sha256']
            assert transition['checkpoint_sha256'][arm] == sha(Path(resume) / 'COMMIT.json')
            assert transition['update'] == previous['update']
            assert transition['preserve_adapter_optimizer_rng_cursor'] is True
        loaded.optimizer.load_state_dict(torch.load(Path(resume) / 'optimizer.pt', map_location='cuda:0', weights_only=False))
        restored_rng = torch.load(Path(resume) / f'rank{rank}.pt', map_location='cpu', weights_only=False)
        state = {key: previous[key] for key in ('update', 'corpus_version', 'corpus_sha256',
            'exposure_counts', 'supervised_tokens', 'reference_tokens')}
    else:
        state = dict(update=0, corpus_version=0, corpus_sha256='', exposure_counts=[],
                     supervised_tokens=0, reference_tokens=0)
        restored_rng = None
    write(root / arm / f'RANK{rank}_LOADED_{state["update"]:09d}.json',
        dict(process=loaded.process, adapter=identity.document(), loaded_unix=time.time(),
             optimizer_restored=bool(previous), legacy_optimizer_available=False, uuid=uuid))
    legacy = legacy_encode(root, loaded.engine.tokenizer)
    encoded_cache = {}
    if restored_rng is not None:
        restore_rng(torch, restored_rng)
    log_path = root / arm / f'RANK{rank}_LOSSES_{state["update"]:09d}.jsonl'
    with log_path.open('x') as stream:
        while True:
            window = wait_window(root, state['update'], lifetime)
            if window['stop']:
                break
            corpus_path = root / window['corpus_path']
            assert sha(corpus_path) == window['corpus_sha256']
            corpus = read(corpus_path)
            assert len(corpus['rows']) >= 2394
            new = encode_corpus(corpus['rows'], loaded.engine.tokenizer, encoded_cache)
            layout = policy.ContinualLayout(len(new), 2)
            encoded = native.assemble_replay(legacy, new, layout, legacy_reference=legacy,
                eos_token_id=loaded.engine.tokenizer.eos_token_id)
            state['corpus_version'], state['corpus_sha256'] = corpus['version'], window['corpus_sha256']
            state['exposure_counts'].extend([0] * (len(encoded) - len(state['exposure_counts'])))
            for update in range(state['update'] + 1, window['end_update'] + 1):
                common.check_deadline(lifetime, 'update')
                indexes, batch, reference, active, unused = native.training_batch(encoded, layout, update,
                    pad_id=loaded.engine.tokenizer.pad_token_id,
                    replay_arm='FULL_TARGET' if arm == 'FULL' else 'NEW_TRAJECTORY_LOSS_OFF')
                positions = policy.rank_positions(rank, world_size)
                local_active = sum(label != -100 for position in positions for label in batch['labels'][position][1:])
                assert local_active > 0
                tensors = {name: torch.tensor([value[position] for position in positions],
                    dtype=torch.long, device=loaded.engine.device) for name, value in batch.items()}
                loaded.optimizer.zero_grad(set_to_none=True)
                with torch.autocast(device_type='cuda', dtype=torch.bfloat16):
                    loss = loaded.engine.model(**tensors, use_cache=False).loss * (local_active / reference)
                assert bool(torch.isfinite(loss))
                loss.backward()
                assert all(parameter.grad is not None for parameter in parameters.values())
                gradients = torch.cat([parameter.grad.reshape(-1) for parameter in parameters.values()]).cpu()
                torch.distributed.all_reduce(gradients, op=torch.distributed.ReduceOp.SUM)
                assert bool(torch.isfinite(gradients).all())
                gradients = gradients.to(loaded.engine.device)
                offset = 0
                for parameter in parameters.values():
                    count = parameter.numel()
                    parameter.grad.copy_(gradients[offset:offset + count].view_as(parameter))
                    offset += count
                loaded.optimizer.step()
                state['update'] = update
                state['supervised_tokens'] += active
                state['reference_tokens'] += reference
                for index in indexes:
                    state['exposure_counts'][index] += 1
                record = dict(update=update, rank=rank, loss=loss.item(), rows=indexes,
                    local_active=local_active, supervised=active, reference=reference,
                    corpus_version=corpus['version'], finished_unix=time.time())
                stream.write(json.dumps(record) + '\n')
                stream.flush()
                if update == 1:
                    write(root / arm / f'RANK{rank}_FIRST_UPDATE.json', record)
            checkpoint(root, arm, rank, loaded, state, parameters, world_size)
    torch.distributed.destroy_process_group()
    write(root / arm / f'RANK{rank}_FINISHED.json', dict(update=state['update'], finished_unix=time.time()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('prepare', 'train', 'scan'))
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--arm', choices=policy.ARMS)
    parser.add_argument('--rank', type=int, choices=(0, 1))
    parser.add_argument('--port', type=int)
    parser.add_argument('--resume', type=Path)
    parser.add_argument('--world-size', type=int, choices=(1, 2, 3), default=1)
    parser.add_argument('--index', type=int, choices=tuple(DEVICES))
    options = parser.parse_args()
    if options.phase == 'prepare':
        prepare(options.root)
    elif options.phase == 'scan':
        print(json.dumps(scan(options.index, options.root / 'SERVICE_IDENTITY.json')))
    else:
        train(options.root, options.arm, options.rank, options.port, options.resume, options.world_size, options.index)
