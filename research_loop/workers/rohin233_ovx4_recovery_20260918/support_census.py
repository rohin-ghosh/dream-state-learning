"""Bounded read-only support-process/deadline census without command-line secrets."""

import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time


ROLES = {
    'ovx4': {'base_player_generation': 459712, 'shared_node3_scorer': 499900,
             'shared_node2_scorer': 499905, 'base_scorer': 506797,
             'shared2_prior_bridge': 448173, 'shared3_prior_bridge': 448322,
             'shared2_judge_bridge': 502015, 'shared3_judge_bridge': 502012,
             'base_judge_bridge': 507837},
    'node4': {'P3_scorer': 573479, 'P3_prior_bridge': 428814,
              'P3_judge_bridge': 570041, 'P3_Tool_writer': 458401},
    'operator_vm': {'node3_upstream_timeout': 3044137, 'node2_upstream_timeout': 3044280,
                    'node3_proxy': 3044140, 'node2_proxy': 3044283,
                    'node2_downstream_timeout': 3334145, 'node3_downstream_timeout': 3334410,
                    'every_sleep_enrollment': 3524450},
    'node2': {}, 'node3': {'node3_existing_Tool_writer_Copernicus': 1970178},
}
SOCKET_PREFIXES = {
    'node2': ('/tmp/r233-source-lease-node2-',),
    'node3': ('/tmp/r233-source-lease-node3-',),
    'ovx4': ('/tmp/r233-', '/localhome/local-rohing/orch_r226_shared_caption_20260918/',
             '/localhome/local-rohing/orch_r230_extra_caption_scorer_20260918/'),
    'node4': ('/tmp/r233-',),
    'operator_vm': ('/tmp/r233-lease-transport-20260918/',),
}


def utc(stamp):
    return datetime.datetime.fromtimestamp(stamp, datetime.timezone.utc).isoformat()


def process(pid):
    root = Path('/proc', str(pid))
    try:
        tail = (root/'stat').read_text().rsplit(')', 1)[1].split()
        command = (root/'cmdline').read_bytes().split(b'\0')
        args = [value.decode() for value in command if value]
        boot = next(int(line.split()[1]) for line in Path('/proc/stat').read_text().splitlines()
                    if line.startswith('btime '))
        start = boot + int(tail[19]) / os.sysconf('SC_CLK_TCK')
        return dict(pid=pid, state=tail[0], ppid=int(tail[1]), start_ticks=int(tail[19]),
                    start_utc=utc(start), start_unix=start, executable=Path(args[0]).name if args else '',
                    command_sha256=hashlib.sha256((root/'cmdline').read_bytes()).hexdigest(), args=args)
    except (OSError, ValueError, IndexError) as error:
        return dict(pid=pid, state='NOT_OBSERVED', error=type(error).__name__, args=[])


def duration(args):
    if not args or Path(args[0]).name != 'timeout':
        return None
    for value in args[1:]:
        match = re.fullmatch(r'(\d+(?:\.\d+)?)([smhd]?)', value)
        if match:
            return float(match[1]) * {'':1, 's':1, 'm':60, 'h':3600, 'd':86400}[match[2]]
    return None


def systemd_duration(value):
    scales = {'w':604800, 'd':86400, 'h':3600, 'min':60, 's':1, 'ms':0.001, 'us':0.000001}
    parts = re.findall(r'(\d+(?:\.\d+)?)(min|ms|us|w|d|h|s)', value)
    if not parts or re.sub(r'\d+(?:\.\d+)?(?:min|ms|us|w|d|h|s)|\s', '', value):
        return None
    return sum(float(amount)*scales[unit] for amount, unit in parts)


def observe(name, pid, alias):
    row = process(pid)
    args = row.pop('args')
    row.update(name=name, actual_host_alias=alias, proof=[], actual_deadline=None)
    bounds = []
    for flag in ('--config', '--epoch'):
        if flag in args:
            path = Path(args[args.index(flag)+1])
            try:
                raw = path.read_bytes()
                config = json.loads(raw)
                evidence = dict(kind='PROCESS_CONFIG', path=str(path), sha256=hashlib.sha256(raw).hexdigest())
                for field in ('deadline_unix', 'end_unix', 'stop_unix'):
                    if type(config.get(field)) in (int, float):
                        evidence[field] = config[field]
                        bounds.append(config[field])
                row['proof'].append(evidence)
            except (OSError, ValueError) as error:
                row['proof'].append(dict(kind='CONFIG_UNREADABLE', error=type(error).__name__))
    for index, value in enumerate(args):
        if value in ('--end-unix', '--deadline-unix') and index + 1 < len(args):
            bounds.append(float(args[index+1]))
            row['proof'].append(dict(kind='EXPLICIT_PROCESS_ARGUMENT', flag=value, unix=float(args[index+1])))
    current = dict(row, args=args)
    for _ in range(3):
        seconds = duration(current.get('args', []))
        if seconds is not None:
            deadline = current['start_unix'] + seconds
            bounds.append(deadline)
            row['proof'].append(dict(kind='LIVE_OUTER_TIMEOUT', pid=current['pid'],
                start_ticks=current['start_ticks'], seconds=seconds, approximate_end_utc=utc(deadline),
                clock_precision_seconds=1, args_sha256=current['command_sha256']))
        if current.get('ppid', 1) <= 1:
            break
        current = process(current['ppid'])
    try:
        groups = Path('/proc',str(pid),'cgroup').read_text().splitlines()
        units = [line.rsplit('/',1)[-1] for line in groups if line.endswith('.service')]
        for unit in units[:1]:
            result = subprocess.run(['systemctl','show',unit,'-p','RuntimeMaxUSec','-p','ActiveEnterTimestamp',
                '-p','ExecMainStartTimestamp','-p','MainPID'],capture_output=True,text=True,timeout=3)
            properties = dict(line.split('=',1) for line in result.stdout.splitlines() if '=' in line)
            evidence = dict(kind='LIVE_SYSTEMD_UNIT',unit=unit,properties=properties)
            runtime = systemd_duration(properties.get('RuntimeMaxUSec', ''))
            start = properties.get('ActiveEnterTimestamp')
            if runtime is not None and start:
                stamp = datetime.datetime.strptime(start, '%a %Y-%m-%d %H:%M:%S %Z').replace(
                    tzinfo=datetime.timezone.utc).timestamp() + runtime
                evidence['derived_end_utc'] = utc(stamp)
                evidence['display_precision_seconds'] = 1
                bounds.append(stamp)
            row['proof'].append(evidence)
    except (OSError, subprocess.TimeoutExpired):
        pass
    if bounds:
        row['actual_deadline'] = utc(min(bounds))
    row['alive'] = row['state'] not in ('NOT_OBSERVED', 'Z', 'X')
    return row


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', choices=ROLES, required=True)
    alias = parser.parse_args().host
    rows = [observe(name,pid,alias) for name,pid in ROLES[alias].items()]
    if alias == 'operator_vm':
        parents = {row['pid']:row['name'] for row in rows if 'timeout' in row['name']}
        for entry in Path('/proc').iterdir():
            if entry.name.isdigit():
                item = process(int(entry.name))
                if item.get('ppid') in parents:
                    rows.append(observe(parents[item['ppid']]+'_ssh_child',item['pid'],alias))
    command = ['ss','-xlnpH']
    if alias in ('node2','node3'):
        command = ['sudo','-n'] + command
    result = subprocess.run(command,capture_output=True,text=True,timeout=5)
    if result.returncode:
        result = subprocess.run(['ss','-xlnpH'],capture_output=True,text=True,timeout=5)
    endpoints = []
    for line in result.stdout.splitlines():
        paths = [value for value in line.split() if any(value.startswith(prefix) for prefix in SOCKET_PREFIXES[alias])]
        if not paths:
            continue
        owners = sorted(set(int(value) for value in re.findall(r'pid=(\d+)',line)))
        endpoints.append(dict(socket=paths[0], listener_pids=owners, actual_host_alias=alias))
        for pid in owners:
            if not any(row['pid']==pid for row in rows):
                rows.append(observe('remote_socket_owner',pid,alias))
    print(json.dumps(dict(unix=time.time(),host_alias=alias,
        host_identity_sha256=hashlib.sha256(subprocess.check_output(['hostname']).strip()).hexdigest(),
        rows=rows,listeners=endpoints,read_only=True,scoring_calls=0,native_signals=[])))


if __name__ == '__main__':
    main()
