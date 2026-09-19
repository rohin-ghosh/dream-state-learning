"""Read and hash only selected COMPLETE/SLEEP_REQUEST/head records on node2."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


TARGETS = {
    'C0': ('/localhome/local-rohing/orch_r216_C0_20260918_attempt2', 6631, 6660, 6710,
        'c9d2aa785f44f81f80aa50b2dbcc04e734bc1f37c1c5743e73a32e12c9ccb587'),
    'Astra7': ('/localhome/local-rohing/orch_r229_Astra7_20260918', 7750, 7776, 7807,
        'a77e37494bf0c93ab640b67ef96f59cc520f2b4382a6b0f5651891a27d0ed485'),
}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
        allow_nan=False).encode()).hexdigest()


def read(path, limit=64 * 1024 * 1024):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as stream:
        before = os.fstat(stream.fileno())
        if before.st_size > limit:
            raise ValueError('bounded_read_required')
        raw = stream.read(limit + 1)
        after = os.fstat(stream.fileno())
        if (before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
                after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns):
            raise ValueError('changed_during_read')
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def remote():
    result = dict(observed_unix=time.time(), full_journal_verified=False,
        checkpoint_binaries_hashed=False, journal_bodies_exported=False,
        node_writes=False, native_signals=[], lives=[])
    for life, (base_name, complete_index, request_index, head_index, complete_sha) in TARGETS.items():
        base = Path(base_name)
        guard, guard_sha = read(base / 'control_r233_lease_continuation/GUARD.json')
        plan, plan_sha = read(Path(guard['plan_path']))
        if plan_sha != guard['plan_sha256']:
            raise ValueError('bound_plan_required')
        records = Path(guard['copy_raw']) / 'stream/records'
        summary = dict(life=life, guard_sha256=guard_sha, records=[])
        for index in (complete_index, request_index, head_index):
            record, raw_sha = read(records / f'{index:020d}.json')
            if digest({key: value for key, value in record.items() if key != 'sha256'}) != record['sha256']:
                raise ValueError('canonical_selected_record_hash_mismatch')
            item = dict(index=index, kind=record['kind'], sha256=record['sha256'],
                raw_file_sha256=raw_sha, canonical_record_hash_verified=True)
            document = record['document']
            if index == head_index:
                item['optimizer_step'] = document['optimizer_step']
            else:
                saved = document['resume_state']
                if digest(saved['state']) != saved['sha256']:
                    raise ValueError('saved_state_digest_mismatch')
                state = saved['state']
                item.update(state_sha256=saved['sha256'], saved_state_digest_verified=True,
                    rows=len(state['rows']), sleep_frontier=state['sleep_frontier'],
                    pending=state['pending'], cycle=document['cycle'],
                    model_state_sha256=state['model_state_sha256'],
                    deadline_unix=state['deadline_unix'], history_keys=sorted(state['history']))
                if index == complete_index:
                    if record['sha256'] != complete_sha:
                        raise ValueError('exact_previously_observed_COMPLETE_required')
                    checkpoint = document['checkpoint']
                    relative = Path(checkpoint['adapter_path']).parent.relative_to(plan['root'])
                    commit_path = Path(guard['copy_raw']) / relative / 'COMMIT.json'
                    commit, commit_sha = read(commit_path, 1024 * 1024)
                    if checkpoint != commit or document['checkpoint_sha256'] != commit['checkpoint_sha256']:
                        raise ValueError('COMPLETE_commit_document_mismatch')
                    item.update(commit_document_exact_match=True, commit_path=str(commit_path),
                        commit_file_sha256=commit_sha, optimizer_steps=commit['optimizer_steps'],
                        adapter_state_sha256=commit['adapter_state_sha256'],
                        checkpoint_sha256=commit['checkpoint_sha256'])
            summary['records'].append(item)
        source = Path(plan['source_root']) / 'gpu/orch_r125_preupdate_recovery.py'
        raw = source.read_bytes()
        summary['preupdate_source'] = dict(path=str(source), sha256=hashlib.sha256(raw).hexdigest(),
            guard_pin=guard['source_pins']['gpu/orch_r125_preupdate_recovery.py'])
        result['lives'].append(summary)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    if sys.argv[1:] == ['--remote-read-only']:
        remote()
    elif len(sys.argv) == 3 and sys.argv[1] == '--receipt':
        completed = subprocess.run(['bash', 'gpu/ovx_ssh.sh', 'python3 -B - --remote-read-only'],
            input=Path(__file__).read_bytes(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=45)
        value = dict(returncode=completed.returncode, stderr=completed.stderr.decode(errors='replace'),
            inspector_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            report=json.loads(completed.stdout) if completed.returncode == 0 else None)
        with Path(sys.argv[2]).open('x') as stream:
            json.dump(value, stream, sort_keys=True, indent=2)
            stream.write('\n')
        print(json.dumps(dict(path=sys.argv[2], returncode=completed.returncode)))
    else:
        raise SystemExit('use --receipt NEW_LOCAL_PATH or --remote-read-only')
