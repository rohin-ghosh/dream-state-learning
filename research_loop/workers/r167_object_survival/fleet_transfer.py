"""Exact private source-to-receiver streaming; no model or scoring access."""

import argparse
import hashlib
import io
import os
from pathlib import Path
import sys
import tarfile
import time
import uuid

from gpu import orch_r167_object_probe_queue as queue


protocol = queue.protocol
require = protocol.require
ROOT = Path('/localhome/local-rohing/orch_r167_fleet_20260917_generation2')
SCHEMA = 'R167_EXACT_PRIVATE_FLEET_TRANSFER_V1'


def safe_member(name, life_id, sleep):
    path = Path(name)
    require(not path.is_absolute() and '..' not in path.parts and str(path) == name, 'canonical_transfer_path')
    capture = Path('lives') / life_id / 'captures' / f'{sleep:06d}'
    if path.parent == capture/'adapter':
        require(path.name in ('adapter_model.safetensors','adapter_config.json','README.md'), 'adapter_only_payload')
    elif path.parent == capture:
        require(path.name in ('COMMIT.original.json','BIRTH.private.json','MANIFEST.json','BOUNDARY.json','COMPLETE.json'),
            'capture_metadata_only')
    elif sleep == 0 and path.parent == Path('lives')/life_id:
        require(path.name in ('REGISTERED.json','TRAIN_FREEZE.json','TRAIN_WITNESSES.private.json'), 'exact_private_TRAIN_files')
    else:
        require(sleep == 0 and path.parent == Path('source_controls')/life_id and
            path.name in ('QUEUE_PLAN.json','MAIN_SOURCE_READ_COPY_GO.json','FRESH_CUSTODY.json'), 'exact_source_custody_files')
    return path


def export(plan_path, life_id, sleep, output):
    pipeline = protocol.read(plan_path)
    require(pipeline['schema'] == 'R167_FLEET_SOURCE_GENERATION2_V1' and pipeline['queue_root'] == str(ROOT)
        and time.time() < pipeline['hard_end_unix'], 'bounded_source_pipeline')
    matches = [life for life in pipeline['lives'] if life['life_id'] == life_id and life['status'] == 'SOURCE_CANDIDATE']
    require(len(matches) == 1, 'registered_source_candidate')
    queue_path = ROOT/'source_controls'/life_id/'QUEUE_PLAN.json'
    plan, root, source, authority = queue.initialized(queue_path, True)
    require(sleep in queue.milestones(plan), 'fixed_registered_sleep')
    capture_dir = root/'captures'/f'{sleep:06d}'
    capture = protocol.read(capture_dir/'COMPLETE.json')
    require(not (capture_dir/'FAILED.json').exists() and capture['status'] == 'IMMUTABLE_ADAPTER_BIRTH_CUSTODY', 'complete_copy_only')
    files = [path for path in capture_dir.rglob('*') if path.is_file()]
    if sleep == 0:
        files += [root/name for name in ('REGISTERED.json','TRAIN_FREEZE.json','TRAIN_WITNESSES.private.json')]
        files += [ROOT/'source_controls'/life_id/name for name in ('QUEUE_PLAN.json','MAIN_SOURCE_READ_COPY_GO.json','FRESH_CUSTODY.json')]
    commit = protocol.read(capture_dir/'COMMIT.original.json')
    entries = []
    amounts = dict(metadata=0, adapter=0)
    for path in sorted(files):
        path = protocol.regular(path)
        name = str(path.relative_to(ROOT))
        safe_member(name, life_id, sleep)
        size = path.stat().st_size
        kind = 'adapter' if path.parent == capture_dir/'adapter' else 'metadata'
        amounts[kind] += size
        checksum = commit['adapter_files'][path.name] if kind == 'adapter' else protocol.sha(path)
        entries.append(dict(name=name, bytes=size, sha256=checksum))
    once_dir = ROOT/'transfer_once'
    once_dir.mkdir(mode=0o700, exist_ok=True)
    with protocol.lock(root/'queue.lock'):
        totals = queue.read_totals(root)
        require(all(totals[kind]+amounts[kind] <= plan[kind+'_read_cap'] for kind in amounts), 'second_hop_read_budget')
        protocol.write(once_dir/f'{life_id}_{sleep:06d}.json', dict(status='EXACT_EXPORT_ONCE_NO_RETRY',
            sleep=sleep, life_id=life_id, amounts=amounts, started_unix=time.time()))
        for kind in amounts:
            protocol.write(root/'reads'/(uuid.uuid4().hex+'.json'), dict(kind=kind, reserved_bytes=amounts[kind],
                operation='SECOND_HOP_PRIVATE_EXPORT', failure_charged=True))
    header = dict(schema=SCHEMA, life_id=life_id, sleep=sleep, files=entries,
        capture=protocol.ref(capture_dir/'COMPLETE.json'), source_plan_sha256=protocol.sha(plan_path),
        context_visibility='PRIVATE_EVALUATOR_ONLY', source_charges=amounts)
    with tarfile.open(fileobj=output, mode='w|') as bundle:
        raw = protocol.canonical(header)
        info = tarfile.TarInfo('TRANSFER_HEADER.json')
        info.size = len(raw)
        info.mode = 0o600
        bundle.addfile(info, io.BytesIO(raw))
        for entry in entries:
            info = tarfile.TarInfo(entry['name'])
            info.size = entry['bytes']
            info.mode = 0o600
            with protocol.regular(ROOT/entry['name']).open('rb') as stream:
                bundle.addfile(info, stream)


def receive(stream, root=ROOT):
    os.umask(0o077)
    with tarfile.open(fileobj=stream, mode='r|') as bundle:
        first = bundle.next()
        require(first.name == 'TRANSFER_HEADER.json' and first.isfile() and first.size <= 1024**2, 'bounded_transfer_header')
        header = protocol.parse(bundle.extractfile(first).read())
        require(header['schema'] == SCHEMA and header['context_visibility'] == 'PRIVATE_EVALUATOR_ONLY', 'private_transfer_only')
        life_id, sleep = header['life_id'], header['sleep']
        queue.key(life_id, sleep, queue.CONDITIONS[0])
        require(1 <= len(header['files']) <= 20, 'bounded_exact_files')
        expected = {entry['name']:entry for entry in header['files']}
        require(len(expected) == len(header['files']) and sum(entry['bytes'] for entry in expected.values()) <= 2*1024**3,
            'bounded_unique_transfer')
        operation = root/'receiving_transfers'/f'{life_id}_{sleep:06d}'
        operation.mkdir(parents=True, mode=0o700, exist_ok=False)
        protocol.write(operation/'ONCE.json', header)
        seen = set()
        while member := bundle.next():
            require(member.name in expected and member.name not in seen and member.isfile(), 'only_regular_expected_unique_files')
            safe_member(member.name, life_id, sleep)
            item = expected[member.name]
            require(member.size == item['bytes'] and member.size >= 0, 'exact_transfer_size')
            target = protocol.regular(root/member.name)
            target.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
            checksum = hashlib.sha256()
            with target.open('xb') as output:
                source = bundle.extractfile(member)
                while raw := source.read(1024**2):
                    checksum.update(raw)
                    output.write(raw)
            require(checksum.hexdigest() == item['sha256'], 'copied_bytes_sha256')
            seen.add(member.name)
        require(seen == set(expected), 'all_declared_files_delivered')
    capture_path = root/'lives'/life_id/'captures'/f'{sleep:06d}'/'COMPLETE.json'
    require(protocol.sha(capture_path) == header['capture']['sha256'], 'capture_receipt_join')
    receipt = dict(status='EXACT_RECEIVING_COPY_VERIFIED', life_id=life_id, sleep=sleep,
        capture=header['capture'], source_plan_sha256=header['source_plan_sha256'], files=header['files'],
        observed_unix=time.time(), model_calls=0)
    reference = protocol.write(operation/'COMPLETE.json', receipt)
    return dict(status='EXACT_RECEIVING_COPY_VERIFIED', life_id=life_id, sleep=sleep, receipt=reference, model_calls=0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('export','receive'))
    parser.add_argument('--plan', type=Path)
    parser.add_argument('--life')
    parser.add_argument('--sleep', type=int)
    args = parser.parse_args()
    if args.action == 'export':
        export(args.plan, args.life, args.sleep, sys.stdout.buffer)
    else:
        print(protocol.json.dumps(receive(sys.stdin.buffer)))


if __name__ == '__main__':
    main()
