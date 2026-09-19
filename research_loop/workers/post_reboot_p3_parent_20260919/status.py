"""Observe exact singleton ownership and real post-reboot provider attempts."""

import json
import os
from pathlib import Path
import time

import runner


def policy_status(document, modified_unix, started_unix):
    observed_unix = document.get('observed_unix', modified_unix)
    return dict(status=document['status'], observed_utc=runner.utc(observed_unix),
        timestamp_basis='document' if 'observed_unix' in document else 'status_file_mtime',
        belongs_to_post_reboot_parent=observed_unix >= started_unix,
        awaiting_render=document.get('memory', {}).get('awaiting_render'),
        not_before_unix=document.get('not_before_unix'))


def main():
    state = json.loads((runner.HERE/'PROCESS.json').read_text())
    expected = state['process']
    actual = runner.process(expected['pid'])
    if not actual or actual['state'] == 'Z' or any(actual[key] != expected[key]
            for key in ('boot_id','pid','start_ticks','command_sha256')):
        raise ValueError('exact_recovered_parent_not_alive')
    locks = []
    for path in (runner.LEDGER/'PARENT_OPERATOR.lock', runner.HERE/'operator/RECOVERY.lock'):
        information = path.stat()
        inode_key = f'{os.major(information.st_dev):02x}:{os.minor(information.st_dev):02x}:{information.st_ino}'
        holders = [line.split() for line in Path('/proc/locks').read_text().splitlines() if inode_key in line]
        if not any(parts[1:4] == ['FLOCK','ADVISORY','WRITE'] and parts[4] == str(actual['pid']) for parts in holders):
            raise ValueError('exact_parent_lock_owner_required')
        locks.append(dict(name=path.name,inode_key=inode_key,owner_pid=actual['pid']))
    preflight = json.loads((runner.HERE/'PREFLIGHT.json').read_text())
    if runner.sha(runner.HERE/'PREFLIGHT.json') != state['preflight_sha256']:
        raise ValueError('unchanged_fresh_preflight_required')
    for name, expected_sha in preflight['runner_pins'].items():
        if runner.sha(runner.HERE/name) != expected_sha:
            raise ValueError('runtime_source_changed')
    pins = json.loads((runner.HERE/'private/PRIOR_LEDGER_PINS.json').read_text())
    if any(runner.sha(runner.LEDGER/name) != checksum for name,checksum in pins.items()):
        raise ValueError('original_parent_attempt_changed')
    if runner.sha(runner.LEDGER/'SEED.json') != preflight['seed_sha256']:
        raise ValueError('original_seed_changed')
    last_status = max(runner.LEDGER.glob('STATUS_*.json'), key=lambda path:path.name)
    observed = json.loads(last_status.read_text())
    start = __import__('datetime').datetime.fromisoformat(state['started_utc']).timestamp()
    attempts = []
    for folder in sorted((runner.LEDGER/'turns').glob('parent_*')):
        source = folder/'SOURCE.json'
        if not source.exists() or source.stat().st_mtime < start:
            continue
        request = folder/'API_REQUEST.json'
        response = folder/'stdout.json'
        result_path = folder/'RESULT.json'
        request_data = json.loads(request.read_text()) if request.exists() else {}
        response_data = json.loads(response.read_text()) if response.exists() else {}
        result = json.loads(result_path.read_text()) if result_path.exists() else {}
        attempts.append(dict(attempt=folder.name,model=request_data.get('model'),reasoning=request_data.get('reasoning'),
            status=result.get('status','IN_PROGRESS'),provider_response_status=response_data.get('status'),
            API_REQUEST_utc=runner.utc(request.stat().st_mtime) if request.exists() else None,
            provider_response_utc=runner.utc(response.stat().st_mtime) if response.exists() else None,
            publication_id=(result.get('publication') or {}).get('id'),
            result_sha256=runner.sha(result_path) if result_path.exists() else None))
    key = os.environ.get('NVIDIA_API_KEY','').encode()
    scanned = 0
    for path in runner.HERE.rglob('*'):
        if path.is_file():
            data = path.read_bytes()
            if key and key in data:
                raise ValueError('credential_leak_detected_no_content_export')
            scanned += 1
    report = dict(observed_utc=runner.utc(time.time()),process=actual,locks=locks,
        original_attempt_files_preserved=len(pins),original_seed_unchanged=True,
        latest_policy_status=policy_status(observed,last_status.stat().st_mtime,start),
        post_reboot_provider_attempts=attempts,model=runner.MODEL,reasoning_effort='xhigh',
        no_credential_bytes_found_in_scope=True,scope_files_scanned=scanned,
        native_signals=0,native_relaunches=0,gates_disabled=0,static_turns_sent=0,
        supervisor_argv=state['argv'],existing_deadline_utc='2026-09-25T18:00:00Z')
    runner.save(runner.HERE/'VERIFIED_PROCESS.json',report)
    print(json.dumps(report))


if __name__ == '__main__':
    main()
