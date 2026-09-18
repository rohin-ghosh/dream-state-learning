"""Bounded node1 metadata observer and one clean-expiry rearm per learner."""

import argparse
from datetime import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import time
from zoneinfo import ZoneInfo


HERE = Path(__file__).resolve().parent if '__file__' in globals() else Path('.')
REPOSITORY = HERE.parents[3] if '__file__' in globals() else Path('.')
PYTHON = '/localhome/local-rohing/v2/venv/bin/python'
ROOTS = {attempt: Path('/localhome/local-rohing/orch_r179_node1_20260917_attempt' + str(attempt)) for attempt in (2, 3)}
LABELS = {2: 'teach_replay', 3: 'teach_perception', 4: 'teach_parenting', 5: 'classroom_brain', 6: 'classroom_creative'}
POLICY_SHA = 'b36949c2d93662b876b6519eee9dddba0e5af94a294e1f570f37685cd9604a2b'
REARM_OPERATOR_SHA = '25a3f7144bf4b35d686d7a82c287b5e43dbb9f793482ba33495d08bac57bdd44'
KNOWN_LOADS = ('40ebb03a0e13bf50bf83a14ad2c944559dadff30dff6260e9c026e729f48adaa',
               '1c8fa0737be20bacdd9bc1cb5927559a5616a07bcdf620b7eec18051b91a4e07')


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, document):
    with path.open('x') as stream:
        json.dump(document, stream, sort_keys=True, indent=2)
        stream.write('\n')


def tail_metadata(raw, expected_index):
    candidates = list(re.finditer(rb',\s*"index"\s*:', raw))
    require(bool(candidates), 'canonical_record_metadata_tail_required')
    metadata = json.loads(b'{' + raw[candidates[-1].start() + 1:])
    require(set(metadata) == {'index', 'journal_id', 'kind', 'previous_sha256', 'schema', 'sha256'},
            'record_tail_contains_only_metadata')
    require(metadata['index'] == expected_index and isinstance(metadata['kind'], str)
            and re.fullmatch(r'[A-Z_]+', metadata['kind']) is not None, 'actual_record_tail_identity')
    require(re.fullmatch(r'[0-9a-f]{64}', metadata['sha256']) is not None, 'record_hash_metadata')
    return {key: metadata[key] for key in ('index', 'kind', 'sha256')}


def read_small(path, budget, cap=1024 * 1024):
    require(not path.is_symlink(), 'no_metadata_symlink')
    size = path.stat().st_size
    require(size <= cap and size <= budget[0], 'metadata_read_reservation')
    budget[0] -= size
    with path.open('rb') as stream:
        raw = stream.read(size + 1)
    require(len(raw) == size, 'immutable_metadata_record_size')
    return json.loads(raw), sha(raw)


def remote_poll(state):
    budget = [8 * 1024 * 1024]
    rows = []
    for physical, label in LABELS.items():
        for attempt, root in ROOTS.items():
            output = root / 'lanes' / ('lane' + str(physical))
            if not output.exists():
                continue
            names = sorted(path.name for path in output.iterdir())
            row = dict(physical=physical, attempt=attempt, names=names, loaded=None, operator_state='ABSENT',
                       successor_epoch_exists=(ROOTS[3] / 'lanes' / ('lane' + str(physical))).exists())
            log = output / 'OPERATOR.log'
            if log.exists():
                charge = min(log.stat().st_size, 4096)
                require(charge <= budget[0], 'precharged_operator_log_tail')
                budget[0] -= charge
                with log.open('rb') as stream:
                    stream.seek(max(0, log.stat().st_size - charge))
                    tail = stream.read(charge).decode('utf-8', 'replace')
                row['operator_exception_types'] = sorted(set(re.findall(
                    r'(?m)^(ValueError|RuntimeError|TimeoutError|FileNotFoundError|PermissionError|KeyError):', tail)))
            if (output / 'ARMED.json').exists():
                armed = read_small(output / 'ARMED.json', budget)[0]
                process = Path('/proc') / str(armed['operator_pid'])
                try:
                    row['operator_state'] = (process / 'stat').read_text().rsplit(') ', 1)[1].split()[0]
                except (FileNotFoundError, ProcessLookupError):
                    pass
                row.update(operator_pid=armed['operator_pid'], remaining_seconds=armed['deadline_monotonic'] - time.monotonic())
            if (output / 'NO_BOUNDARY.json').exists():
                row['timeout'] = read_small(output / 'NO_BOUNDARY.json', budget)[0]
            loaded_path = output / 'LOADED_RECEIPT.json'
            if physical == 4 and (output / 'readmission1/LOADED_RECEIPT.json').exists():
                loaded_path = output / 'readmission1/LOADED_RECEIPT.json'
            if loaded_path.exists():
                loaded, loaded_sha = read_small(loaded_path, budget)
                row.update(loaded=loaded, loaded_sha256=loaded_sha)
                staged = read_small(output / 'STAGED.json', budget)[0]
                life = Path('/localhome/local-rohing/orch_r136_a100_' + label + '_20260916_attempt1/run1')
                require(staged['old_plan']['root'] == str(life), 'fixed_training_life_only')
                boundary = read_small(output / 'BOUNDARY.json', budget)[0]['saved']
                key = str(attempt) + ':' + str(physical)
                cursor = state.get('cursors', {}).get(key, int(Path(boundary['record_path']).stem))
                if key not in state.get('finished', []):
                    paths = sorted(path for path in (life / 'stream/records').iterdir()
                                   if re.fullmatch(r'[0-9]{20}\.json', path.name) and int(path.stem) > cursor)
                    require(len(paths) <= 512, 'bounded_new_record_metadata_window')
                    metadata = []
                    for path in paths:
                        size = path.stat().st_size
                        charge = min(size, 4096)
                        require(not path.is_symlink() and charge <= budget[0], 'precharged_record_tail')
                        budget[0] -= charge
                        with path.open('rb') as stream:
                            stream.seek(size - charge)
                            raw = stream.read(charge)
                        require(len(raw) == charge, 'stable_record_tail')
                        metadata.append(tail_metadata(raw, int(path.stem)))
                    row['new_kinds'] = sorted({record['kind'] for record in metadata})
                    row['cursor'] = metadata[-1]['index'] if metadata else cursor
            elif (output / 'control/ADMISSION.json').exists():
                admission, admission_sha = read_small(output / 'control/ADMISSION.json', budget, 4 * 1024 * 1024)
                row['admission'] = dict(clear=admission.get('clear'), sha256=admission_sha,
                                        blocking_reason_count=len(admission.get('blocking_reasons', [])))
            rows.append(row)
    return dict(observed_unix=time.time(), rows=rows, bytes_read=8 * 1024 * 1024 - budget[0],
                read_cap_bytes=8 * 1024 * 1024, sealed_content_reads=0, child_text_exported=False)


def can_rearm(row):
    forbidden = {'BOUNDARY.json', 'BOUNDARY_RECEIVING_CPU.json', 'RETIREMENT_STARTED.json',
                 'RETIRED.json', 'DISPATCHED.json', 'LOADED_RECEIPT.json', 'HANDOFF_COMPLETE.json'}
    return (row['attempt'] == 2 and row['physical'] in (2, 5, 6) and row['loaded'] is None
            and not row.get('successor_epoch_exists', False)
            and row['operator_state'] in ('ABSENT', 'Z', 'X') and row.get('remaining_seconds', 1) <= 0
            and row.get('timeout', {}).get('original_left_running') is True
            and not forbidden.intersection(row['names'])
            and not any(name.startswith('FAILURE_') for name in row['names']))


def custody_events(observed):
    status = observed['status']
    if status == 'POST_SLEEP_PROMPT_HISTORY_CUSTODY_VERIFIED':
        require(observed['full_raw_and_visible_history_preserved'] is True, 'positive_prompt_custody_proof')
        return ['RETAINED_SLEEP_COMPLETE', 'POST_SLEEP_PROMPT_CUSTODY']
    if status == 'COMPLETED_RETAINED_SLEEP_WAITING_POST_SLEEP_REQUEST':
        require('sleep_complete' in observed['progress']['records'], 'actual_completed_sleep_record')
        return ['RETAINED_SLEEP_COMPLETE']
    return []


def rpc(arguments, payload=None, timeout=90):
    command = shlex.join(['env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1', PYTHON, '-B'] + arguments)
    result = subprocess.run(['bash', 'gpu/a100_ssh.sh', command], cwd=REPOSITORY,
                            text=True, input=payload, capture_output=True, timeout=timeout)
    require(result.returncode == 0, 'remote_metadata_or_rearm_command_failed:' + result.stderr[-1200:])
    return json.loads(result.stdout)


def post(run, state, event, title, body):
    if event in state['posted']:
        return
    timestamp = datetime.now(ZoneInfo('America/Los_Angeles')).strftime('%Y-%m-%d %H:%M:%S PDT')
    entry = '\n## [Builder/node1 — ' + title + '] ' + timestamp + '\n' + body + '\n'
    identifier = sha(event.encode())
    intent = run / ('POST_' + identifier + '.json')
    save(intent, dict(event=event, body=entry, body_sha256=sha(entry.encode()), observed_unix=time.time()))
    descriptor = os.open(REPOSITORY / 'research_loop/COORDINATION.md', os.O_WRONLY | os.O_APPEND | os.O_NOFOLLOW)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        raw = entry.encode()
        require(os.write(descriptor, raw) == len(raw), 'complete_metadata_coordination_append')
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    state['posted'].append(event)
    save(run / ('POSTED_' + identifier + '.json'), dict(event=event, published_unix=time.time(),
                                                       intent_sha256=sha(intent.read_bytes())))


def observe(run, row):
    result = subprocess.run([sys.executable, '-B', str(HERE / 'observe_retained.py'),
                             '--physical', str(row['physical']), '--attempt', str(row['attempt'])],
                            cwd=REPOSITORY, text=True, capture_output=True, timeout=120)
    require(result.returncode == 0, 'bounded_custody_observer_process')
    receipt = json.loads(result.stdout)
    require(receipt['returncode'] == 0, 'actual_custody_verifier_success')
    observed = json.loads(receipt['stdout'])
    require(observed.get('actor', {}).get('identity_matches') is True
            and observed['actor'].get('source_matches') is True
            and observed.get('source_pins', {}).get('gpu/orch_r179_context_survival.py') == POLICY_SHA,
            'actual_current_actor_and_policy_binding')
    return receipt, observed


def rearm(run, state, row):
    physical = row['physical']
    state['rearm_attempted'].append(physical)
    save(run / ('REARM_INTENT_' + str(physical) + '.json'), dict(physical=physical, observed_unix=time.time(),
         prior=row, authorization='Main clean-expiry no-signal rearm within original walls; one new namespace only'))
    prepared = rpc([str(ROOTS[3] / 'operator/rearm_node1.py'), 'prepare', '--physical', str(physical)], timeout=300)
    require(prepared['signals_sent'] == 0 and prepared['model_calls'] == 0
            and prepared['receiving_cpu_passed'] >= 3 and prepared['cuda_initialized'] is False
            and prepared['operator_sha256'] == REARM_OPERATOR_SHA and prepared['source_reused_not_repatched'] is True,
            'actual_pre_signal_receiving_CPU_and_source_gate')
    path = run / ('REARM_PREPARED_' + str(physical) + '.json')
    save(path, prepared)
    post(run, state, 'REARM_CPU:' + str(physical), 'R179 non-material clean-expiry rearm CPU gate',
         f"Lane{physical}/{LABELS[physical]}: explicit prior clean timeout, exact live owner/device and both source closures revalidated. "
         f"Fresh actual receiving CPU {prepared['receiving_cpu_passed']}PASS, CUDA uninitialized, zero signals/model calls during preparation. "
         f"Reuse immutable prepared source; new operator namespace only, SHA `{REARM_OPERATOR_SHA}`; policy `{POLICY_SHA}`. "
         f"Next independent wait5400s within unchanged hard wall{prepared['original_hard_end_unix']}; prior attempts/one-shot tokens preserved, no consumed-call replay. "
         f"Receipt `{path.relative_to(REPOSITORY)}` SHA `{sha(path.read_bytes())}`. Actual LOADED requires a later receipt.")
    command = shlex.join(['env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1', PYTHON, '-B',
                          str(ROOTS[3] / 'operator/rearm_node1.py'), 'handoff', '--physical', str(physical)])
    log = ROOTS[3] / 'lanes' / ('lane' + str(physical)) / 'OPERATOR.log'
    shell = 'nohup ' + command + ' >' + shlex.quote(str(log)) + ' 2>&1 </dev/null & echo $!'
    result = subprocess.run(['bash', 'gpu/a100_ssh.sh', shell], cwd=REPOSITORY,
                            text=True, capture_output=True, timeout=30)
    require(result.returncode == 0 and result.stdout.strip().isdigit(), 'actual_rearm_waiter_dispatch')
    save(run / ('REARM_DISPATCHED_' + str(physical) + '.json'),
         dict(physical=physical, operator_pid=int(result.stdout.strip()), observed_unix=time.time(), loaded=False))


def process_row(run, state, row, snapshot_path):
    physical = row['physical']
    key = str(row['attempt']) + ':' + str(physical)
    if (any(name.startswith('FAILURE_') for name in row['names']) or row.get('operator_exception_types')
            or row.get('admission', {}).get('clear') is False):
        post(run, state, 'FAILURE:' + key, 'R179 node1 concrete handoff failure',
             f"Lane{physical}/{LABELS[physical]} attempt{row['attempt']} has controller failure metadata; no automatic consumed-native/readout retry. "
             f"Metadata `{snapshot_path.relative_to(REPOSITORY)}`. Other independent lives continue.")
    if row['loaded'] is not None:
        kinds = set(row.get('new_kinds', []))
        pending_post_sleep = state['observed'].get(key, {}).get('status') == 'COMPLETED_RETAINED_SLEEP_WAITING_POST_SLEEP_REQUEST'
        needs_observer = (key not in state['observed'] or 'LOADED:' + row['loaded_sha256'] not in state['posted']
                          or bool(kinds.intersection({'CONTEXT_RETAINED', 'SLEEP_COMPLETE'}))
                          or (pending_post_sleep and 'REQUEST' in kinds))
        cursor = row.get('cursor', state['cursors'].get(key, 0))
        if needs_observer and key not in state['finished']:
            receipt, observed = observe(run, row)
            state['observed'][key] = dict(status=observed['status'], path=receipt['path'], sha256=receipt['sha256'])
            cursor = max(cursor, observed.get('last_index', cursor))
            loaded = row['loaded']
            post(run, state, 'LOADED:' + row['loaded_sha256'], 'R179 ' + LABELS[physical] + ' actual LOADED',
                 f"Lane{physical}, native{loaded['actor_pid']}/start{loaded['actor_start_ticks']}, saved sleep{loaded['saved_cycle']}/optimizer{loaded['optimizer_steps']}. "
                 f"Actual LOADED receipt SHA `{row['loaded_sha256']}`, observed load Unix{loaded['observed_unix']}; fresh PID/source/guard-policy and journal prefix verified. "
                 f"Policy `{POLICY_SHA}`; source and proofs `{Path(receipt['path']).relative_to(REPOSITORY)}` SHA `{receipt['sha256']}`. "
                 "Loading alone is not a completed retained sleep or weight-retention claim. Sealed content reads0; both R164 channels unchanged.")
            for event in custody_events(observed):
                cycle = observed['cycle'] if 'cycle' in observed else observed['progress']['retention_decision']['cycle']
                complete_sha = (observed['sleep_complete_sha256'] if 'sleep_complete_sha256' in observed
                                else observed['progress']['records']['sleep_complete']['sha256'])
                post(run, state, event + ':' + key, 'R179 ' + LABELS[physical] + ' ' + event,
                     f"Lane{physical}, cycle{cycle}, SLEEP_COMPLETE SHA `{complete_sha}`: actual runtime record-chain/full-history verifier reports `{observed['status']}`. "
                     f"Post-sleep request SHA `{observed.get('post_sleep_request_sha256', 'PENDING')}`. "
                     f"Receipt `{Path(receipt['path']).relative_to(REPOSITORY)}` SHA `{receipt['sha256']}` contains exact cycle/source/history/record hashes. "
                     "Completed retained sleep is distinct from post-sleep rendered-prompt custody; neither is saved-adapter weight-retention proof. "
                     "No sealed content or evaluator output exported; both R164 channels retained.")
            if observed['status'] == 'POST_SLEEP_PROMPT_HISTORY_CUSTODY_VERIFIED':
                state['finished'].append(key)
        state['cursors'][key] = cursor
    elif can_rearm(row) and physical not in state['rearm_attempted']:
        rearm(run, state, row)


def run_monitor(run, seconds, interval):
    require(run.parent == HERE and run.name.startswith('AUTONOMY_'), 'own_run_directory_only')
    require(1 <= seconds <= 21600 and 30 <= interval <= 300, 'bounded_CPU_observer_duration_and_cadence')
    lock = os.open(HERE / 'AUTONOMY.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    run.mkdir()
    state = dict(cursors={}, observed={}, finished=[], rearm_attempted=[],
                 posted=['LOADED:' + checksum for checksum in KNOWN_LOADS])
    source = Path(__file__).read_text()
    observer_sha = sha((HERE / 'observe_retained.py').read_bytes())
    save(run / 'STARTED.json', dict(pid=os.getpid(), observed_unix=time.time(), deadline_unix=time.time() + seconds,
                                  source_sha256=sha(source.encode()), custody_observer_sha256=observer_sha,
                                  interval_seconds=interval, max_rearms_per_remaining_life=1))
    deadline = time.monotonic() + seconds
    try:
        while time.monotonic() < deadline:
            try:
                require(sha(Path(__file__).read_bytes()) == sha(source.encode())
                        and sha((HERE / 'observe_retained.py').read_bytes()) == observer_sha, 'immutable_running_monitor_bytes')
                snapshot = rpc(['-c', source, '--remote'], json.dumps(state))
                stamp = str(time.time_ns())
                save(run / ('POLL_' + stamp + '.json'), snapshot)
                for row in snapshot['rows']:
                    try:
                        process_row(run, state, row, run / ('POLL_' + stamp + '.json'))
                    except Exception as error:
                        path = run / ('LANE_ERROR_' + str(row['physical']) + '_' + str(time.time_ns()) + '.json')
                        save(path, dict(error_type=type(error).__name__, reason=str(error), observed_unix=time.time()))
                        post(run, state, 'LANE_ERROR:' + str(row['physical']) + ':' + type(error).__name__,
                             'R179 independent node1 lane observer/rearm error',
                             f"Lane{row['physical']} concrete `{type(error).__name__}`; receipt `{path.relative_to(REPOSITORY)}`. "
                             "Other lanes continue independently. No native/readout call is replayed.")
                save(run / ('STATE_' + stamp + '.json'), state)
                print(json.dumps(dict(observed_unix=time.time(), observed=state['observed'], finished=state['finished'],
                                      rearm_attempted=state['rearm_attempted'])), flush=True)
                if len(state['finished']) == 5:
                    break
            except Exception as error:
                path = run / ('ERROR_' + str(time.time_ns()) + '.json')
                save(path, dict(error_type=type(error).__name__, reason=str(error), observed_unix=time.time()))
                post(run, state, 'MONITOR_ERROR:' + type(error).__name__, 'R179 node1 observer/rearm error',
                     f"Concrete observer/rearm error `{type(error).__name__}`; receipt `{path.relative_to(REPOSITORY)}`. "
                     "No model-call retry is authorized by this error. Existing independent live handoff operators are not stopped.")
            time.sleep(min(interval, max(0, deadline - time.monotonic())))
    finally:
        save(run / 'FINISHED.json', dict(observed_unix=time.time(), state=state,
                                        all_first_post_sleep_proofs_complete=len(state['finished']) == 5,
                                        original_lives_not_stopped_by_monitor_exit=True))
        os.close(lock)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--remote', action='store_true')
    parser.add_argument('--run-dir', type=Path)
    parser.add_argument('--seconds', type=int, default=21600)
    parser.add_argument('--interval', type=int, default=120)
    arguments = parser.parse_args()
    if arguments.remote:
        print(json.dumps(remote_poll(json.load(sys.stdin)), sort_keys=True))
    else:
        require(arguments.run_dir is not None, 'explicit_bounded_run_directory')
        run_monitor(arguments.run_dir.resolve(), arguments.seconds, arguments.interval)


if __name__ == '__main__':
    main()
