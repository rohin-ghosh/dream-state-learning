"""Withdraw one unconsumed inbox item with a momentary exact-native quiesce."""

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import time


ROOT = Path('/localhome/local-rohing/orch_r136_raw_unparented_a40r1_20260916_attempt1/run1')
PID = 294158
TICKS = '24386173'
CONFIG = '/localhome/local-rohing/orch_r179_node4_20260917t1810z/lane1/control/GUARD.json'
IDENTIFIER = '11a39e52e43540f8839c312cf64e86ff'
EXPECTED_SHA = '0fa7c82f47b6bfb7e63162e2635171206f375b7a8a2539a5fc32c78067d50d05'
ARCHIVE = Path('/localhome/local-rohing/orch_r175_control_withdrawal_20260917')


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def identity():
    process = Path('/proc') / str(PID)
    fields = (process / 'stat').read_text().rsplit(')', 1)[1].split()
    argv = (process / 'cmdline').read_bytes().rstrip(b'\0').decode().split('\0')
    require(fields[19] == TICKS and argv == ['/localhome/local-rohing/v2/venv/bin/python', '-B', '-m',
            'gpu.orch_r125_continual_guard', 'native', '--config', CONFIG], 'exact_native_identity')
    return fields[0]


def main():
    require(identity() not in ('T', 't', 'Z', 'X'), 'native_running_not_pre_stopped')
    guard = json.loads(Path(CONFIG).read_text())
    plan = json.loads(Path(guard['plan_path']).read_text())
    require(plan['root'] == str(ROOT), 'native_bound_to_control')
    source = ROOT / 'stream/inbox' / (IDENTIFIER + '.json')
    require(not source.is_symlink() and source.is_file(), 'exact_existing_inbox')
    raw = source.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == EXPECTED_SHA, 'exact_publication_hash')
    message = json.loads(raw)
    require(message['id'] == IDENTIFIER and message['actor'] == 'parent' and message['speaker'] == 'Astra',
            'exact_Astra_publication')
    ARCHIVE.mkdir(mode=0o700, exist_ok=True)
    target = ARCHIVE / source.name
    require(not target.exists(), 'new_withdrawal_receipt')
    descriptor = os.pidfd_open(PID)
    stopped = False
    started = time.time()
    try:
        identity()
        signal.pidfd_send_signal(descriptor, signal.SIGSTOP)
        stopped = True
        for attempt in range(100):
            if identity() in ('T', 't'):
                break
            time.sleep(0.01)
        require(identity() in ('T', 't'), 'native_quiesced')
        paths = sorted(path for path in (ROOT / 'stream/records').iterdir()
                       if re.fullmatch(r'[0-9]{20}\.json', path.name))
        require(len(paths) <= 100000, 'bounded_journal')
        for path in paths:
            require(path.stat().st_size <= 16 * 1024 * 1024, 'bounded_record')
            record = json.loads(path.read_text())
            if record['kind'] == 'INBOX':
                require(record['document']['message']['id'] != IDENTIFIER, 'already_ingested_do_not_rewrite_history')
        require(hashlib.sha256(source.read_bytes()).hexdigest() == EXPECTED_SHA, 'unchanged_inbox')
        os.rename(source, target)
        require(not source.exists() and hashlib.sha256(target.read_bytes()).hexdigest() == EXPECTED_SHA,
                'withdrawn_and_preserved_exactly')
        last = json.loads(paths[-1].read_text())
        result = dict(status='WITHDRAWN_BEFORE_INGESTION', observed_utc=datetime.now(timezone.utc).isoformat(),
                      root=str(ROOT), native_pid=PID, native_start_ticks=TICKS, inbox_id=IDENTIFIER,
                      publication_sha256=EXPECTED_SHA, archived_path=str(target),
                      inspected_records=len(paths), journal_head_index=last['index'], journal_head_sha256=last['sha256'],
                      adapter_optimizer_rng_untouched=True, native_restart=False, authority='Fable relayed user order 2026-09-17 14:02 PDT')
    finally:
        if stopped:
            signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        os.close(descriptor)
    result.update(native_resumed=identity() not in ('T', 't', 'Z', 'X'), elapsed_seconds=time.time() - started)
    with (ARCHIVE / 'WITHDRAWAL_RECEIPT.json').open('x') as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
