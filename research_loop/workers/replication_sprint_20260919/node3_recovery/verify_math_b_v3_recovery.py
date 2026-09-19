"""Read-only live recovery proof: all pending updates, saved bytes, and ACT chain."""

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess


ROOT = Path('/localhome/local-rohing/orch_r205_node3_20260918/r213_math_b_fork')
CONTROL = ROOT / 'control_ws6_pending_math_b_20260919T144429Z'
RAW = ROOT / 'raw'


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def checksum(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as source:
        while block := source.read(4 * 1024**2):
            value.update(block)
    return value.hexdigest()


def read_record(index):
    path = RAW / 'stream' / 'records' / f'{index:020d}.json'
    raw = path.read_bytes()
    require(len(raw) <= 64 * 1024**2, 'bounded_record_bytes')
    record = json.loads(raw)
    require(record['index'] == index and record['sha256']
        == digest({key: value for key, value in record.items() if key != 'sha256'}), 'record_digest')
    expected = {key: record[key] for key in ('schema', 'journal_id', 'index', 'previous_sha256')}
    expected['record_sha256'] = record['sha256']
    require(json.loads(path.with_name(path.stem + '.intent.json').read_bytes()) == expected, 'record_intent')
    return record


def reference(record):
    return {key: record[key] for key in ('index', 'kind', 'sha256')}


def verify():
    require(os.uname().nodename == 'ipp2-ovx-p6-09', 'original_node')
    envelope = json.loads((CONTROL / 'PENDING_SLEEP_CANDIDATE.json').read_bytes())
    candidate = envelope['candidate']
    require(envelope['sha256'] == digest(candidate), 'candidate_pin')
    contract = candidate['contract']['contract']
    completed_path = RAW / 'interrupted_sleep_restarts' / candidate['attempt_key'] / 'COMPLETED.json'
    result = dict(utc=datetime.now(timezone.utc).isoformat(), read_only=True, control=str(CONTROL),
        recovery_complete=False, first_ACT_chain_verified=False, parent_bound=False,
        parent_blocker='original_seven_native_prerequisite_unsatisfied_no_relaxation')
    if not completed_path.exists():
        result['status'] = 'RECOVERY_COMPLETION_NOT_YET_PUBLISHED'
        print(json.dumps(result, sort_keys=True), flush=True)
        return
    completed = json.loads(completed_path.read_bytes())
    complete = read_record(completed['complete']['index'])
    require(complete['kind'] == 'SLEEP_COMPLETE'
        and complete['sha256'] == completed['complete']['sha256'], 'recovery_COMPLETE_reference')
    completion = complete['document']
    old_state = contract['preserved_state']['state']
    new_state = completion['resume_state']['state']
    require(completion['resume_state']['sha256'] == digest(new_state), 'restored_state_digest')
    require(new_state['rows'] == old_state['rows'] and new_state['history'] == old_state['history']
        and len(new_state['rows']) == new_state['sleep_frontier'] == 580
        and new_state['pending'] is None, 'all_rows_history_working_state_preserved')
    changed = {key for key in old_state if old_state[key] != new_state[key]}
    require(changed <= {'pending', 'sleep_frontier', 'sleep_receipts', 'model_state_sha256'}
        and set(old_state) == set(new_state), 'only_sleep_completion_state_changes')
    require(new_state['sleep_receipts'][:-1] == old_state['sleep_receipts'], 'all_old_sleep_receipts_preserved')
    require(completion['optimizer_steps'] == 48 and completion['total_optimizer_steps'] == 9788
        and completion['excluded_rows'] == []
        and completion['new_row_sha256'] == contract['pending_row_sha256'], 'exact_full_pending_sleep')
    require(completed['accounting']['recovery_start_steps'] == 9740
        and completed['accounting']['recovery_end_steps'] == 9788
        and completed['accounting']['recovery_updates'] == 48
        and completed['accounting']['exact_resident_continuity_claimed'] is False,
        'durable_state_and_recovery_compute_accounting')
    previous = contract['old_head']['sha256']
    records = []
    for index in range(9556, complete['index'] + 1):
        record = read_record(index)
        require(record['previous_sha256'] == previous, 'recovery_chain')
        previous = record['sha256']
        records.append(record)
    updates = [record for record in records if record['kind'] == 'UPDATE']
    require([record['document']['optimizer_step'] for record in updates] == list(range(9741, 9789)),
        'all_48_actual_update_records')
    counts = Counter(record['document']['source_sha256'] for record in updates)
    require(dict(counts) == {source: 16 for source in contract['pending_row_sha256']}, 'every_pending_row_16_presentations')
    require(all(record['document']['interrupted_sleep_restart']['compute_origin'] == 'NEW_RECOVERY_COMPUTE'
        for record in updates), 'new_not_adopted_unsaved_compute')
    checkpoint = completion['checkpoint']
    checkpoint_root = RAW / 'checkpoints' / candidate['checkpoint_name']
    require(json.loads((checkpoint_root / 'COMMIT.json').read_bytes()) == checkpoint, 'durable_checkpoint_COMMIT')
    saved_files = {}
    for name, expected in checkpoint['adapter_files'].items():
        path = checkpoint_root / 'adapter' / name
        require(checksum(path) == expected, 'saved_adapter_' + name)
        saved_files[str(path)] = expected
    optimizer = checkpoint_root / 'optimizer_rng.pt'
    require(checksum(optimizer) == checkpoint['checkpoint_sha256']['optimizer']
        == checkpoint['checkpoint_sha256']['rng'], 'saved_optimizer_RNG_hash')
    saved_files[str(optimizer)] = checksum(optimizer)
    learned = read_record(completed['paired_LEARN']['index'])
    require(learned['kind'] == 'R184_LEARN_COMPLETE'
        and learned['sha256'] == completed['paired_LEARN']['sha256']
        and learned['document']['checkpoint'] == checkpoint, 'paired_LEARN_same_checkpoint')
    result.update(status='RECOVERY_COMPLETE_VERIFIED_WAITING_FOR_ACT', recovery_complete=True,
        complete=reference(complete), paired_LEARN=reference(learned),
        first_recovery_update=reference(updates[0]), last_recovery_update=reference(updates[-1]),
        optimizer_start=9740, optimizer_end=9788, new_recovery_updates=48,
        presentations=dict(counts), excluded_rows=[], row_count=580, frontier=580,
        identical_prior_history_rows_working_state=True, checkpoint_files=saved_files,
        completion_file_sha256=checksum(completed_path), exact_resident_RNG_claimed=False)
    following = []
    for index in range(complete['index'] + 1, complete['index'] + 101):
        path = RAW / 'stream' / 'records' / f'{index:020d}.json'
        if not path.exists():
            break
        record = read_record(index)
        require(record['previous_sha256'] == previous, 'post_recovery_chain')
        previous = record['sha256']
        following.append(record)
        if record['kind'] == 'LOADED':
            require(record['document']['optimizer_steps'] == 9788, 'LOADED_recovered_optimizer')
            result['loaded'] = dict(reference(record), loaded_unix=record['document']['loaded_unix'],
                pid=record['document']['pid'])
        if record['kind'] == 'NODE3_PENDING_SLEEP_STARTUP_COMPLETE':
            result['startup_complete'] = reference(record)
            result['prefix_validation'] = record['document']['journal_audit']
        if record['kind'] != 'R184_ACT':
            continue
        response_index = record['document']['origin']['record_index']
        response = next(item for item in following if item['index'] == response_index)
        require(response['kind'] == 'RESPONSE'
            and response['sha256'] == record['document']['origin']['record_sha256'], 'ACT_response_origin')
        matching = [item for item in following if item['kind'] == 'REQUEST'
            and item['index'] < response_index and digest({key: value for key, value in item['document'].items()
                if key != 'resume_state'}) == response['document']['request_sha256']]
        require(len(matching) == 1, 'ACT_exact_REQUEST_RESPONSE')
        commits = [item for item in following if item['kind'] == 'COMMITTED'
            and response_index < item['index'] < record['index']
            and item['document']['source_sha256'] == record['document']['source_sha256']]
        require(len(commits) == 1 and 'loaded' in result, 'ACT_committed_after_LOADED')
        result.update(status='RECOVERY_COMPLETE_LOADED_AND_FIRST_ACT_CHAIN_VERIFIED', first_ACT_chain_verified=True,
            ACT_request=reference(matching[0]), ACT_response=reference(response), ACT_commit=reference(commits[0]),
            ACT=reference(record), ACT_outcome=record['document']['outcome'],
            ACT_raw_excerpt=response['document']['response']['raw'][:500])
        break
    exited = json.loads((CONTROL / 'ORIGINAL_EXIT.json').read_bytes())['finished_unix']
    result['original_exit_unix'] = exited
    if 'loaded' in result:
        result['downtime_to_LOADED_seconds'] = result['loaded']['loaded_unix'] - exited
    result['owner_available_bytes'] = os.statvfs(ROOT).f_bavail * os.statvfs(ROOT).f_frsize
    result['compute_apps'] = subprocess.run(['nvidia-smi', '--query-compute-apps=pid,gpu_uuid,process_name',
        '--format=csv,noheader'], check=True, capture_output=True, text=True, timeout=20).stdout
    print(json.dumps(result, sort_keys=True), flush=True)


def main():
    here = Path(__file__).resolve().parent
    source = Path(__file__).read_text().rsplit("if __name__ == '__main__':", 1)[0] + '\nverify()\n'
    response = subprocess.run(['bash', 'gpu/ovx2_ssh.sh', 'env PYTHONDONTWRITEBYTECODE=1 python3 -B -'],
        cwd=here.parents[3], input=source, capture_output=True, text=True, timeout=120)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    path = here / ('MATH_B_V3_VERIFICATION_' + stamp + '.json')
    value = dict(returncode=response.returncode, stdout=response.stdout, stderr=response.stderr)
    if response.returncode == 0:
        value = json.loads(response.stdout)
    with path.open('x') as output:
        json.dump(value, output, sort_keys=True, indent=2)
        output.flush()
        os.fsync(output.fileno())
    print(json.dumps(dict(receipt=str(path), result=value), sort_keys=True))
    response.check_returncode()


if __name__ == '__main__':
    main()
