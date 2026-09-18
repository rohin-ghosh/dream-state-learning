"""Arm an exclusive successor for the existing P3 feedback CPU relay."""

import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import select
import subprocess
import time


ROOT = Path('/localhome/local-rohing/orch_r228_p3_feedback_20260918')
SOURCE = ROOT / 'source_v2/relay.py'
SOURCE_SHA = '0b0ea65a243a1ecfce0944b8a7ad50efcd86abb7cb646a6b0f95555a3207a9ab'
LIFE = '/localhome/local-rohing/orch_r201_node4_20260918/node4/R195_FLEET/SCALE_physical3/life'
SESSIONS = tuple('/localhome/local-rohing/' + name for name in (
    'orch_r213_caption_service_20260918/session1',
    'orch_r224_caption_scorer_20260918/session2',
    'orch_r226_caption_scorer_20260918/session2'))
OLD_PID = 1493939
OLD_TICKS = '29059965'
OLD_END = 1789729629
NEW_END = datetime(2026, 9, 18, 14, 9, 7, tzinfo=timezone.utc).timestamp()
POLICY = 'R232_P3_RELAY_EXCLUSIVE_SUCCESSOR_V1'


def checksum(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, document):
    temporary = path.with_suffix('.temporary')
    with temporary.open('w') as stream:
        json.dump(document, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def renewed_command(arguments, new_end):
    expected = ['python3', '-B', str(SOURCE), '--life', LIFE,
                '--output', str(ROOT / 'relay')]
    for session in SESSIONS:
        expected.extend(('--session', session))
    expected.extend(('--end-unix', str(OLD_END)))
    if arguments != expected:
        raise ValueError('exact_existing_P3_CPU_relay_only')
    if not OLD_END < new_end <= NEW_END:
        raise ValueError('bounded_forward_renewal_only')
    return arguments[:-1] + [str(int(new_end))]


def inventory(output):
    result = {}
    for directory in ('projections', 'published'):
        for path in sorted((output / directory).glob('*.json')):
            if path.is_symlink() or not path.is_file():
                raise ValueError('regular_receipt_required')
            result[str(path.relative_to(output))] = checksum(path)
    return result


def verify_preserved(before, after):
    if any(after.get(name) != digest for name, digest in before.items()):
        raise ValueError('existing_dedup_or_projection_changed')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    options = parser.parse_args()
    output = options.output.resolve()
    if output.parent != ROOT or output.name != 'r232_renewal':
        raise ValueError('exact_renewal_receipt_directory')
    output.mkdir(exist_ok=True)
    with (output / 'SUPERVISOR.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if (output / 'ACTIVATED.json').exists():
            raise ValueError('successor_already_started')
        process = Path('/proc') / str(OLD_PID)
        arguments = (process / 'cmdline').read_bytes().decode().strip('\0').split('\0')
        if (process / 'stat').read_text().rsplit(') ', 1)[1].split()[19] != OLD_TICKS:
            raise ValueError('old_process_identity_changed')
        command = renewed_command(arguments, NEW_END)
        if checksum(SOURCE) != SOURCE_SHA or time.time() >= OLD_END:
            raise ValueError('source_hash_and_pre_expiry_arming_required')
        executable = os.readlink(process / 'exe')
        working_directory = os.readlink(process / 'cwd')
        variables = dict(entry.split(b'=', 1) for entry in (process / 'environ').read_bytes().split(b'\0')
                         if b'=' in entry)
        environment = dict(os.environ)
        environment['PYTHONPATH'] = variables[b'PYTHONPATH'].decode()
        before = inventory(ROOT / 'relay')
        descriptor = os.pidfd_open(OLD_PID)
        try:
            armed = dict(policy=POLICY, supervisor_pid=os.getpid(), old_pid=OLD_PID,
                         old_start_ticks=OLD_TICKS, old_end_unix=OLD_END, new_end_unix=NEW_END,
                         armed_unix=time.time(), relay_source_sha256=SOURCE_SHA,
                         preserved_receipts=before, learner_signals=[], relay_signals=[],
                         status='ARMED_WAITING_FOR_EXISTING_WRITER_EXIT')
            write(output / 'ARMED.json', armed)
            poller = select.poll()
            poller.register(descriptor, select.POLLIN)
            remaining = max(1, int((OLD_END + 180 - time.time()) * 1000))
            if not poller.poll(remaining):
                write(output / 'FAILED.json', dict(policy=POLICY,
                    observed_unix=time.time(), reason='existing_writer_did_not_exit_no_signal_sent'))
                return
            exited = time.time()
            if checksum(SOURCE) != SOURCE_SHA:
                raise ValueError('source_changed_before_successor')
            after = inventory(ROOT / 'relay')
            verify_preserved(before, after)
            with (ROOT / 'relay/WRITER.lock').open('a') as writer:
                fcntl.flock(writer, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with (output / 'relay.log').open('a') as log:
                successor = subprocess.Popen([executable, *command[1:]], cwd=working_directory,
                    env=environment, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                    start_new_session=True)
            started = time.time()
            receipt = ROOT / f'relay/STARTED_{successor.pid}.json'
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline and not receipt.exists() and successor.poll() is None:
                time.sleep(.1)
            if not receipt.exists() or successor.poll() is not None:
                write(output / 'FAILED.json', dict(policy=POLICY, observed_unix=time.time(),
                    reason='successor_start_not_verified', successor_pid=successor.pid,
                    returncode=successor.poll(), learner_signals=[], relay_signals=[]))
                return
            verify_preserved(after, inventory(ROOT / 'relay'))
            write(output / 'ACTIVATED.json', dict(policy=POLICY, successor_pid=successor.pid,
                old_pid=OLD_PID, old_exit_observed_unix=exited, successor_started_unix=started,
                cpu_writer_handoff_seconds=started - exited, new_end_unix=NEW_END,
                relay_source_sha256=SOURCE_SHA, startup_receipt_sha256=checksum(receipt),
                preserved_receipt_count=len(after), learner_signals=[], relay_signals=[],
                next_Tool_rendering='not_yet_verified'))
        finally:
            os.close(descriptor)


if __name__ == '__main__':
    main()
