"""Drain only the exact owned R119 process; always resume on failed inspection."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import time


def pending_rows(root, rows):
    cycle = max(row.get('cycle', 0) for row in rows)
    pending = []
    for row in rows:
        if row.get('cycle') != cycle:
            continue
        if row['kind'] == 'PARENT':
            path = root / 'parent_received' / f'P{row["number"]:04d}.json'
            if not path.exists():
                pending.append(row)
        elif row.get('split') == 'TRAIN' and not row.get('attached_readout', False):
            path = root / 'calls' / f'N{row["number"]:05d}.json'
            if not path.exists() or json.loads(path.read_text())['status'] != 'COMPLETE':
                pending.append(row)
    return pending


def drain(physical):
    root = Path(f'/localhome/local-rohing/orch_r118_node3_{physical}_grid_20260915_attempt1')
    folder = root / 'continuation_r119_1710'
    pid = json.loads((folder / 'LOADED.json').read_text())['pid']
    proc = Path('/proc') / str(pid)
    raw = (proc / 'cmdline').read_bytes()
    parts = raw.split(b'\0')
    assert b'/localhome/local-rohing/orch_r119_grid_continuation_source_20260915_v1/gpu/orch_r119_grid_continuation.py' in parts
    assert b'native' in parts and parts[parts.index(b'--physical')+1] == str(physical).encode()
    assert proc.stat().st_uid == os.getuid()
    start = (proc / 'stat').read_text().rpartition(') ')[2].split()[19]
    descriptor = os.pidfd_open(pid)
    terminated = False
    try:
        signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        while time.time() < 1789494300:
            signal.pidfd_send_signal(descriptor, signal.SIGSTOP)
            try:
                time.sleep(.05)
                rows = [json.loads(line) for line in (root / 'LEDGER.jsonl').read_text().splitlines() if line]
                if not pending_rows(root, rows):
                    signal.pidfd_send_signal(descriptor, signal.SIGTERM)
                    signal.pidfd_send_signal(descriptor, signal.SIGCONT)
                    terminated = True
                    receipt = dict(physical=physical, pid=pid, start_ticks=start,
                        command_sha256=hashlib.sha256(raw).hexdigest(), observed_unix=time.time(),
                        reason='MAIN_1717_SLOT_MODEL_SCOPE_CORRECTION',
                        all_charged_current_TRAIN_and_parents_terminal=True,
                        cycle=max(row.get('cycle', 0) for row in rows),
                        counts={kind: sum(row['kind'] == kind for row in rows) for kind in ('NATIVE', 'PARENT')},
                        ledger_sha256=hashlib.sha256((root / 'LEDGER.jsonl').read_bytes()).hexdigest(),
                        carry_sha256=hashlib.sha256((root / 'CARRY.json').read_bytes()).hexdigest(),
                        foreign_signals=0, checkpoint_reset=False)
                    with (folder / 'SCOPED_SETTLED_RELEASE.json').open('x') as output:
                        json.dump(receipt, output, indent=2)
                    print(json.dumps(receipt))
                    return
            finally:
                if not terminated:
                    signal.pidfd_send_signal(descriptor, signal.SIGCONT)
            time.sleep(.05)
        raise ValueError('bounded_drain_not_settled')
    finally:
        if not terminated:
            signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        os.close(descriptor)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--physical', type=int, choices=(6, 7), required=True)
    drain(parser.parse_args().physical)
