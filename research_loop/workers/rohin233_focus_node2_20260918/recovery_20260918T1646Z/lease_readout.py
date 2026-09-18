"""Read only the current continuation's public operational receipts."""

import argparse
from copy import deepcopy
from datetime import datetime
import json
import os
from pathlib import Path
import subprocess

from observe import checked, header, observation, utc
from recover import locations, read, sha


def restored_state_checks(candidate, complete, wall, loaded):
    expected = deepcopy(complete['document']['resume_state']['state'])
    expected['deadline_unix'] = wall['authorization']['new_deadline_unix']
    return dict(source_record_matches=complete['sha256'] == candidate['record_sha256'],
        only_deadline_changed=expected == wall['state']['state'],
        extended_hash_matches=wall['state']['sha256'] == candidate['extended_state_sha256'],
        optimizer_steps_match=loaded['optimizer_steps'] == candidate['optimizer_steps'],
        adapter_state_hash_matches=loaded['adapter_sha256']
            == complete['document']['checkpoint']['adapter_state_sha256'])


def receipt(name):
    observed = observation(name)
    root, _, control, _ = locations(name)
    observed['control_name'] = control.name
    observed['plan_sha256'] = sha(control / 'PLAN.json')
    recovery = read(control / 'RECOVERY.json')
    if 'candidate' in recovery:
        observed['preserved_checkpoint'] = recovery['candidate']
        observed['handoff'] = {key: recovery[key] for key in
            ('native_term_utc', 'old_native_absent_utc', 'old_owner', 'no_SIGSTOP', 'no_idle_hold')}
        if observed.get('loaded'):
            observed['signal_to_loaded_seconds'] = (
                datetime.fromisoformat(observed['loaded']['loaded_utc'])
                - datetime.fromisoformat(recovery['native_term_utc'])).total_seconds()
    if observed.get('loaded'):
        floor = observed['loaded']['index'] - 3
        for path in sorted((root / 'raw/stream/records').glob('[0-9]' * 20 + '.json')):
            if not floor <= int(path.stem) < observed['loaded']['index']:
                continue
            if header(path)['kind'] == 'WALL_EXTENDED':
                record = checked(path)
                observed['wall_extended'] = dict(index=record['index'], sha256=record['sha256'],
                    authorization=record['document']['authorization'],
                    state_sha256=record['document']['state']['sha256'],
                    record_mtime_utc=utc(path.stat().st_mtime))
                if 'candidate' in recovery:
                    candidate = recovery['candidate']
                    complete = checked(root / 'raw/stream/records' / f'{candidate["record_index"]:020d}.json')
                    observed['state_verification'] = restored_state_checks(candidate, complete,
                        record['document'], observed['loaded'])
    owner = observed.get('native')
    if owner:
        process = Path('/proc', str(owner['pid']))
        stat = (process / 'stat').read_text().rsplit(')', 1)[1].split()
        parent = Path('/proc', stat[1])
        command = (parent / 'cmdline').read_bytes().split(b'\0')
        if Path(os.fsdecode(command[0])).name == 'timeout':
            parent_stat = (parent / 'stat').read_text().rsplit(')', 1)[1].split()
            duration = next(os.fsdecode(argument) for argument in command[1:]
                if argument.endswith(b's') and argument[:-1].isdigit())
            boot = next(int(line.split()[1]) for line in Path('/proc/stat').read_text().splitlines()
                if line.startswith('btime '))
            observed['timeout'] = dict(pid=int(parent.name), start_ticks=int(parent_stat[19]),
                duration=duration, estimated_expiry_utc=utc(
                    boot + int(parent_stat[19]) / os.sysconf('SC_CLK_TCK') + int(duration[:-1])))
        groups = (process / 'cgroup').read_text().splitlines()
        unit = next((part for line in groups for part in line.split('/')
            if part.startswith('orch-') and part.endswith('.service')), None)
        if unit:
            result = subprocess.run(['systemctl', 'show', unit, '-p', 'ActiveState', '-p', 'SubState',
                '-p', 'RuntimeMaxUSec', '-p', 'ExecMainStartTimestamp'], text=True,
                capture_output=True, timeout=10, check=True)
            observed['systemd'] = dict(unit=unit,
                properties=dict(line.split('=', 1) for line in result.stdout.splitlines() if '=' in line))
    return observed


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('name', choices=('C0', 'ASTRA7', 'CAPTION'))
    print(json.dumps(receipt(parser.parse_args().name), indent=2, sort_keys=True))
