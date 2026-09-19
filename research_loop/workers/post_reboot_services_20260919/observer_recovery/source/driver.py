"""Non-material source-lease admission repair for the unchanged age enrollment."""

import argparse
import datetime
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import time


POLICY = 'R233_PER_SOURCE_LEASE_ADMISSION_V1'
SERVICE_END = 1790791170
READ_SECONDS = 30
EXIT_MARGIN = 5
SOURCE_DAYS = {
    'ovx_ssh.sh': ('node2', 20),
    'ovx3_ssh.sh': ('node5', 20),
    'ovx2_ssh.sh': ('node3', 24),
    'a40r_ssh.sh': ('node4', 25),
    'ovx4_ssh.sh': ('ovx4', 30),
}


class SourceLeaseClosed(ValueError):
    pass


def checksum(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def utc(stamp):
    return datetime.datetime.fromtimestamp(stamp, datetime.timezone.utc).isoformat()


def admission(target, now, service_end=SERVICE_END):
    alias, day = SOURCE_DAYS[target['wrapper']]
    source_end = datetime.datetime(2026, 9, day, 18, tzinfo=datetime.timezone.utc).timestamp()
    effective_end = min(source_end, service_end)
    admitted = now < effective_end - READ_SECONDS - EXIT_MARGIN
    return dict(policy=POLICY, source_host_alias=alias, source_cutoff_utc=utc(source_end),
                effective_cutoff_utc=utc(effective_end), effective_cutoff_unix=effective_end,
                latest_start_utc=utc(effective_end-READ_SECONDS-EXIT_MARGIN),
                receiver_finish_utc=utc(effective_end-EXIT_MARGIN), observed_unix=now,
                allowed=admitted, caller_timeout_seconds=READ_SECONDS,
                receiver_alarm=True, cleanup_margin_seconds=EXIT_MARGIN)


def remote_program(source, target, cursor, decision):
    guard = ('import signal, time\n'
             f"_source_read_end = {decision['effective_cutoff_unix']!r} - {EXIT_MARGIN}\n"
             f'_remaining = min({READ_SECONDS}, _source_read_end - time.time())\n'
             "if _remaining <= 0: raise SystemExit('source_lease_closed_before_read')\n"
             'signal.signal(signal.SIGALRM, signal.SIG_DFL)\n'
             'signal.setitimer(signal.ITIMER_REAL, _remaining)\n')
    return guard + source + '\nprint(json.dumps(page(' + repr(target) + ',' + repr(cursor) + ',limit=64)))\n'


def guarded_page(target, cursor, repo, source, decisions, now=None, runner=None):
    clock = time.time if now is None else now
    execute = subprocess.run if runner is None else runner
    decision = admission(target, clock())
    decisions[target['label']] = decision
    if not decision['allowed']:
        raise SourceLeaseClosed('source_cutoff_no_remote_read')
    code = remote_program(source, target, cursor, decision)
    decision = admission(target, clock())
    decisions[target['label']] = decision
    if not decision['allowed']:
        raise SourceLeaseClosed('source_cutoff_before_dispatch_no_remote_read')
    result = execute(['bash', str(Path(repo)/'gpu'/target['wrapper']), 'python3 -B -'],
                     input=code, text=True, capture_output=True, timeout=READ_SECONDS)
    if result.returncode or len(result.stdout) > 1048576:
        raise ValueError('bounded_remote_metadata_failed')
    return json.loads(result.stdout)


def lease_tick(reader, registration, output, repo, source, now=None, runner=None):
    decisions = {}
    original = reader.remote_page
    reader.remote_page = lambda target, cursor, repo: guarded_page(
        target, cursor, repo, source, decisions, now, runner)
    try:
        status = reader.tick(registration, output, repo)
    finally:
        reader.remote_page = original
    for row in status['rows']:
        decision = decisions.get(row['life'])
        row['source_admission'] = decision
        if decision is not None and not decision['allowed']:
            row['status'] = 'SOURCE_LEASE_CLOSED_NO_REMOTE_READ'
    status['source_admission_policy'] = POLICY
    status['extra_node2_player'] = 'CONFIRMED_KEPT_SEPARATE_SIXTEENTH_ROOT'
    reader.put(output/'STATUS.json', status)
    return status


def load_reader(reference):
    path = Path(reference['path'])
    if checksum(path) != reference['sha256']:
        raise ValueError('frozen_reader_source_changed')
    spec = importlib.util.spec_from_file_location('frozen_age_enrollment', path)
    reader = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reader)
    return reader


def verify_preserved(state, original):
    if any(state['entries'].get(key) != value for key, value in original['entries'].items()):
        raise ValueError('historical_enrollment_changed')
    for label, cursor in original['cursors'].items():
        if state['cursors'][label]['last_index'] < cursor['last_index']:
            raise ValueError('enrollment_cursor_regressed')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=Path, required=True)
    config_path = parser.parse_args().config
    config = json.loads(config_path.read_bytes())
    if not time.time() < config['deadline_unix'] == SERVICE_END:
        raise ValueError('same_operator_vm_service_horizon')
    if checksum(__file__) != config['driver_sha256']:
        raise ValueError('frozen_driver_source_changed')
    reader = load_reader(config['reader'])
    source = Path(config['reader']['path']).read_text().rsplit("if __name__ == '__main__':", 1)[0]
    receipt_root = Path(config['receipt_root'])
    registrations, locks, preserved = [], [], []
    for ledger in config['ledgers']:
        output = Path(ledger['output'])
        lock = (output/'ENROLL.lock').open('a')
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        locks.append(lock)
        if checksum(output/'private/STATE.json') != ledger['state_sha256']:
            raise ValueError('exact_handoff_enrollment_state_required')
        if checksum(ledger['registration']['path']) != ledger['registration']['sha256']:
            raise ValueError('same_registered_roots_required')
        state = json.loads((output/'private/STATE.json').read_bytes())
        registration = json.loads(Path(ledger['registration']['path']).read_bytes())
        registration['deadline_unix'] = SERVICE_END
        for target in registration['targets']:
            admission(target, time.time())
            wrapper = Path(config['repo'])/'gpu'/target['wrapper']
            if checksum(wrapper) != config['wrappers_sha256'][target['wrapper']]:
                raise ValueError('same_registered_ssh_wrapper_required')
        registrations.append((registration, output))
        preserved.append(state)
    targets = [target for registration, unused in registrations for target in registration['targets']]
    if len(targets) != 16 or len({target['journal_id'] for target in targets}) != 16:
        raise ValueError('same_sixteen_registered_journals_required')
    reader.put(receipt_root/'LOADED.json', dict(unix=time.time(),pid=os.getpid(),
        deadline_unix=SERVICE_END,policy=POLICY,config_sha256=checksum(config_path),
        driver_sha256=config['driver_sha256'],reader_sha256=config['reader']['sha256'],
        preserved_state_sha256=[ledger['state_sha256'] for ledger in config['ledgers']],
        preserved_entries=sum(len(state['entries']) for state in preserved),registered_roots=16,
        target_admission=[dict(life=target['label'], **admission(target,time.time())) for target in targets],
        cursors_reset=False,learner_signals=[],new_evaluations=0,backlog_dispatcher_started=False))
    first = True
    while time.time() < SERVICE_END:
        statuses = [lease_tick(reader, registration, output, config['repo'], source)
                    for registration, output in registrations]
        for (_, output), original in zip(registrations, preserved):
            verify_preserved(json.loads((output/'private/STATE.json').read_bytes()), original)
        status = dict(unix=time.time(),pid=os.getpid(),deadline_unix=SERVICE_END,policy=POLICY,
            enrolled=sum(item['enrolled'] for item in statuses),roots=16,
            rows=[row for item in statuses for row in item['rows']],historical_entries_unchanged=True,
            cursor_regressions=0,new_evaluations=0,backlog_dispatcher_started=False,
            capture_and_evaluations='separate_actual_receipts',learner_signals=[])
        reader.put(receipt_root/'LATEST.json', status)
        reader.put(Path(config['support_root'])/'LEASE_ENROLLMENT_LATEST.json', status)
        if first:
            reader.put(receipt_root/'FIRST_CYCLE.json', status)
            first = False
        time.sleep(min(15, max(0, SERVICE_END-time.time())))


if __name__ == '__main__':
    main()
