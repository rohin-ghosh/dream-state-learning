"""Exact owned BASE process release at a settled completed-response boundary."""

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import time


ROOT = Path('/localhome/local-rohing/orch_r118_node3_6_grid_20260915_attempt1')
COMMAND = b'/localhome/local-rohing/orch_r119_grid_continuation_source_20260915_v1/gpu/orch_r119_grid_a40r7_continue.py'


def validate_identity(pid, raw, loaded):
    parts = raw.split(b'\0')
    if pid != 774326 or loaded['pid'] != pid or COMMAND not in parts or b'native' not in parts:
        raise ValueError('only_actual_owned_BASE_predecessor')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--deadline', type=float, required=True)
    args = parser.parse_args()
    path = Path(__file__).with_name('orch_r119_grid_settled_drain.py')
    if hashlib.sha256(path.read_bytes()).hexdigest() != '7c50e64a587a538701e086d1b82b4e1e10e124b76c37fe040dabb1fb4c73a4fa':
        raise ValueError('tested_pending_decoder')
    spec = importlib.util.spec_from_file_location('settled', path)
    settled = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(settled)
    folder = ROOT / 'lease_budget_r119_base'
    folder.mkdir(exist_ok=True)
    pid = 774326
    proc = Path('/proc') / str(pid)
    loaded = json.loads((ROOT / 'migration_a40r7_r119/LOADED.json').read_text())
    raw = (proc / 'cmdline').read_bytes()
    validate_identity(pid, raw, loaded)
    if proc.stat().st_uid != os.getuid() or not time.time() < args.deadline <= time.time() + 900:
        raise ValueError('owned_bounded_release')
    start = (proc / 'stat').read_text().rpartition(') ')[2].split()[19]
    descriptor = os.pidfd_open(pid)
    terminated = False
    try:
        while time.time() < args.deadline:
            signal.pidfd_send_signal(descriptor, signal.SIGSTOP)
            try:
                time.sleep(.05)
                ledger = (ROOT / 'LEDGER.jsonl').read_bytes()
                rows = [json.loads(line) for line in ledger.splitlines() if line]
                if not settled.pending_rows(ROOT, rows):
                    receipt = dict(schema='R119_GRID_LEASE_BUDGET_RELEASE_V1', pid=pid,
                        start_ticks=start, command_sha256=hashlib.sha256(raw).hexdigest(),
                        observed_unix=time.time(), reason='USER_DIRECTED_PROSPECTIVE_LEASE_HEADROOM',
                        completed_response_boundary=True, all_charged_current_TRAIN_and_parents_terminal=True,
                        cycle=max(row.get('cycle', 0) for row in rows),
                        counts={kind: sum(row['kind'] == kind for row in rows) for kind in ('NATIVE', 'PARENT')},
                        ledger_sha256=hashlib.sha256(ledger).hexdigest(),
                        carry_sha256=hashlib.sha256((ROOT / 'CARRY.json').read_bytes()).hexdigest(),
                        counter_reset=False, foreign_signals=0)
                    with (folder / 'SETTLED_RELEASE.json').open('x') as output:
                        json.dump(receipt, output, indent=2)
                    signal.pidfd_send_signal(descriptor, signal.SIGTERM)
                    signal.pidfd_send_signal(descriptor, signal.SIGCONT)
                    terminated = True
                    print(json.dumps(receipt))
                    return
            finally:
                if not terminated:
                    signal.pidfd_send_signal(descriptor, signal.SIGCONT)
            time.sleep(.5)
        raise ValueError('not_settled_no_release')
    finally:
        if not terminated:
            signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        os.close(descriptor)


if __name__ == '__main__':
    main()
