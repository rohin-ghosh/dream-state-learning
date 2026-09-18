"""Bounded actual component deadlines; configured successors are not adoption."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

from recovery import PHASE, read, utc
from recovery_proof import project as native_projection
from retirement import identity, public_identity, sha


def timeout_seconds(arguments):
    if not arguments or Path(arguments[0]).name != 'timeout':
        raise ValueError('actual_GNU_timeout_parent_required')
    duration = next(value for value in arguments[1:] if not value.startswith('-'))
    if not duration.endswith('s') or not duration[:-1].isdigit():
        raise ValueError('explicit_seconds_timeout_required')
    return int(duration[:-1])


def service(receipt, horizon_flag):
    if not receipt.exists():
        return dict(status='NO_ATTACHMENT_RECEIPT')
    expected = read(receipt)['process']
    try:
        actual = identity(expected['pid'])
        if any(actual[key] != expected[key] for key in ('pid', 'start_ticks', 'command_sha256')):
            return dict(status='IDENTITY_CHANGED_NOT_CURRENT')
        if actual['state'] in ('Z', 'X'):
            return dict(status='EXITED', **public_identity(actual))
        deadline = float(actual['args'][actual['args'].index(horizon_flag) + 1])
        return dict(status='ACTUAL_LIVE_COMMAND_BOUND', end_utc=utc(deadline), **public_identity(actual))
    except (FileNotFoundError, ProcessLookupError):
        return dict(status='EXITED', pid=expected['pid'])


def project(root):
    native = native_projection(root)
    boot = int(next(line.split()[1] for line in Path('/proc/stat').read_text().splitlines() if line.startswith('btime ')))
    clock = os.sysconf('SC_CLK_TCK')
    rows = []
    for row in native['lives']:
        item = dict(life=row['life'], gpu=row['gpu'], status=row['status'],
            configured_deadline_utc=row['configured_deadline_utc'],
            resident_deadline_utc=row['resident_deadline_utc'], WALL_EXTENDED=row.get('WALL_EXTENDED'),
            LOADED=row['LOADED'], actual_native=row['actual_native'])
        if row['actual_native']:
            timeout = identity(row['actual_native']['ppid'])
            duration = timeout_seconds(timeout['args'])
            item['GNU_timeout'] = dict(**public_identity(timeout), duration_seconds=duration,
                derived_end_utc=utc(boot + int(timeout['start_ticks']) / clock + duration),
                boot_timestamp_resolution_seconds=1)
            cgroup = Path('/proc', str(row['actual_native']['pid']), 'cgroup').read_text()
            units = [part for line in cgroup.splitlines() for part in line.split(':')[-1].split('/') if part.endswith('.service')]
            if len(set(units)) == 1:
                unit = units[0]
                result = subprocess.run(['systemctl', 'show', unit, '--property=RuntimeMaxUSec',
                    '--property=ActiveEnterTimestamp', '--property=ActiveState'], text=True,
                    capture_output=True, check=True, timeout=5)
                item['systemd'] = dict(unit_name_sha256=hashlib.sha256(unit.encode()).hexdigest(),
                    actual_properties=dict(line.split('=', 1) for line in result.stdout.splitlines() if '=' in line))
        control = root / row['life'] / ('control_' + PHASE + '_boundary_lease_ceiling')
        if control.exists():
            item['boundary_handoff'] = dict(files={filename:sha(control / filename) for filename in
                ('PREPARED.json', 'WAITING_NEXT_COMPLETE.json', 'HANDOFF_SIGNAL.json', 'OLD_EXIT_OBSERVED.json',
                 'RECOVERY.json', 'RECONCILED.json', 'DISPATCHED.json') if (control / filename).exists()},
                actually_adopted=bool(row.get('WALL_EXTENDED') and row['LOADED'] and row['actual_native']
                    and row['configured_deadline_utc'].startswith('2026-09-24T18:00:00')))
            if (control / 'OLD_EXIT_OBSERVED.json').exists():
                exited = read(control / 'OLD_EXIT_OBSERVED.json')
                item['boundary_handoff']['old_exit_utc'] = exited['observed_utc']
                if item['boundary_handoff']['actually_adopted']:
                    item['boundary_handoff']['observed_reload_gap_seconds'] = row['LOADED']['loaded_unix'] - exited['observed_unix']
            if (control / 'RECOVERY.json').exists():
                recovery = read(control / 'RECOVERY.json')
                item['boundary_handoff'].update(lost_tail_updates=recovery['lost_tail_updates'],
                    preserved_manifest_sha256=recovery['preservation_manifest_sha256'],
                    checkpoint_sha256=recovery['checkpoint_sha256'], complete_cycle=recovery['complete_cycle'])
        rows.append(item)
    services = root / 'r233_recovery_services_v4'
    debate = dict(status='NO_ACTUAL_ATTACHMENT')
    debate_receipt = services / 'math_debate.json'
    if debate_receipt.exists():
        expected = read(debate_receipt)['process']
        actual = identity(expected['pid'])
        attachment = root / 'r231_math_parent_live_v2/attachments' / (str(actual['pid']) + '.json')
        started = read(attachment)
        if (all(actual[key] == expected[key] for key in ('pid', 'start_ticks', 'command_sha256'))
                and actual['state'] not in ('Z', 'X')
                and started['source_sha256'] == sha(root / 'r231_math_operator_v2/r229_math_parents.py')):
            debate = dict(status='ACTUAL_LIVE_STARTUP_BINDINGS', **public_identity(actual),
                end_utc=utc(min(binding['deadline'] for binding in started['bindings'].values()) - 60),
                attachment_sha256=sha(attachment), source_sha256=started['source_sha256'])
    return dict(observed_utc=utc(), node='node3', lives=rows,
        parent_classroom=service(services / 'classroom.json', '--service-end-unix'),
        fifth_caption_parent=service(services / 'caption_gpu7.json', '--service-end-unix'),
        Tool_feedback_projection=service(root / 'r233_recovery_services_v3/feedback.json', '--end-unix'),
        math_debate=debate,
        shared_scorer_transport=dict(status='OWNER_VERIFICATION_PENDING', owner='Leibniz',
            node3_Tool_projection_is_not_a_scorer=True),
        operator_ceiling_utc='2026-09-24T18:00:00+00:00', provider_expiry_new_claim=False,
        lease_purchase_or_extension=False, stage_never_counted_as_adoption=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    options = parser.parse_args()
    print(json.dumps(project(options.root), indent=2, sort_keys=True))
