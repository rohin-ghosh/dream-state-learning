"""Bounded read-only node1 parent/native inventory; no provider imports or signals."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import socket
import subprocess
import time


HERE = Path(__file__).resolve().parent if '__file__' in globals() else None
REFRESH_SUFFIX = '/r169_parent_auth_refresh_20260917/refresh.py'
CONFIG_FIELDS = ('node', 'branch', 'root', 'source_root', 'programme', 'actual_programme',
                 'parent_style', 'cadence_responses', 'cadence_label', 'schedule_on',
                 'hard_end_unix', 'principles_path', 'principles_sha256',
                 'programme_path', 'programme_sha256', 'start_after_response_count')


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


class Reader:
    def __init__(self, cap=64 * 1024 * 1024):
        self.cap = cap
        self.used = 0

    def raw(self, path, maximum=2 * 1024 * 1024):
        path = Path(path)
        require(not path.is_symlink(), 'no_symlink_file')
        before = path.stat()
        require(before.st_size <= maximum and self.used + before.st_size <= self.cap,
                'read_before_charge_budget')
        self.used += before.st_size
        with path.open('rb') as stream:
            raw = stream.read(before.st_size)
            after = os.fstat(stream.fileno())
        require(len(raw) == before.st_size and before.st_size == after.st_size
                and before.st_mtime_ns == after.st_mtime_ns, 'stable_file_read')
        return raw

    def document(self, path):
        raw = self.raw(path)
        return json.loads(raw), dict(path=str(path), sha256=digest(raw), bytes=len(raw))


def identity(process):
    with (process / 'cmdline').open('rb') as stream:
        raw = stream.read(65537)
    require(len(raw) <= 65536, 'bounded_argv')
    fields = (process / 'stat').read_text().rsplit(') ', 1)[1].split()
    return dict(pid=int(process.name), ticks=fields[19], state=fields[0],
                uid=process.stat().st_uid, cwd=str((process / 'cwd').resolve(strict=True)),
                argv=raw.rstrip(b'\0').decode().split('\0'), argv_sha256=digest(raw))


def unchanged(before, after):
    return all(before[name] == after[name] for name in ('pid', 'ticks', 'uid', 'cwd', 'argv_sha256'))


def scoped_plan_path(path):
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts and path.suffix == '.json'
            and str(path).startswith('/localhome/local-rohing/orch_'), 'scoped_node_plan_only')
    return path


def ledger(output, reader):
    output = Path(output)
    directories = sorted(path for path in output.iterdir()
                         if re.fullmatch(r'parent_[0-9]{6}', path.name))
    require(len(directories) <= 2048, 'bounded_parent_attempts')
    rows = []
    for directory in directories:
        require(directory.is_dir() and not directory.is_symlink(), 'regular_parent_attempt')
        row = dict(attempt=directory.name)
        for name in ('SOURCE.json', 'RESULT.json', 'DELIVERED.json'):
            path = directory / name
            if not path.exists():
                continue
            document, reference = reader.document(path)
            row[name] = reference
            if name == 'SOURCE.json':
                row.update(response_count=document.get('response_count'),
                           request_count=document.get('request_count'), head_sha256=document.get('head_sha256'))
            elif name == 'RESULT.json':
                row.update(status=document.get('status'), finished_unix=document.get('finished_unix'),
                           publication=document.get('inbox_publication'),
                           source_response_count=document.get('source_response_count'),
                           source_head_sha256=document.get('source_head_sha256'))
            else:
                row.update(legacy_delivery_status=document.get('status'),
                           inbox_id=document.get('inbox_id'),
                           consumption=document.get('consumption'),
                           delivered_label_is_request_exposure=False)
        row['settled'] = row.get('status') in ('PUBLISHED', 'MISSING', 'SILENT')
        rows.append(row)
    return rows


def local_parents(reader):
    rows = []
    for process in Path('/proc').iterdir():
        if not process.name.isdigit():
            continue
        try:
            if process.stat().st_uid != os.getuid():
                continue
            current = identity(process)
            argv = current['argv']
            if '--binding' not in argv or not any(item.endswith(REFRESH_SUFFIX) for item in argv[:5]):
                continue
            binding_path = Path(argv[argv.index('--binding') + 1])
            require(binding_path.name == 'BINDING.json'
                    and 'r169_parent_auth_refresh_20260917' in binding_path.parts,
                    'known_parent_binding_only')
            binding, binding_ref = reader.document(binding_path)
            match = re.fullmatch(r'a100_([0-7])_(.+)', binding.get('branch', ''))
            if match is None:
                continue
            config, config_ref = reader.document(binding['config'])
            require(config_ref['sha256'] == binding['config_sha256'], 'actual_bound_config')
            require(config['node'] == 'a100' and config['branch'] == binding['branch'], 'parent_node_binding')
            source = reader.raw(binding['source_copy'])
            require(digest(source) == binding['source_sha256'], 'actual_bound_parent_source')
            operator = next(item for item in argv[:5] if item.endswith(REFRESH_SUFFIX))
            require(digest(reader.raw(operator)) == binding['operator_sha256'], 'actual_bound_parent_operator')
            principles = reader.raw(config['principles_path'])
            programme = reader.raw(config['programme_path'])
            require(digest(principles) == config['principles_sha256']
                    and digest(programme) == config['programme_sha256'], 'actual_parent_text_inputs')
            started, started_ref = reader.document(Path(binding['output']) / 'STARTED.json')
            require(started['pid'] == current['pid'] and started['config_sha256'] == config_ref['sha256'],
                    'actual_started_parent_config')
            attempts = ledger(binding['output'], reader)
            require(unchanged(current, identity(process)), 'stable_parent_identity')
            rows.append(dict(physical=int(match.group(1)), label=match.group(2), parent=current,
                             binding=binding_ref, config=config_ref,
                             fields={key: config[key] for key in CONFIG_FIELDS if key in config},
                             source=dict(path=binding['source_copy'], sha256=digest(source)),
                             operator=dict(path=operator, sha256=binding['operator_sha256']),
                             started=started_ref, reserved_cursor_at_start=binding['cursor'],
                             output=binding['output'], previous_output=binding['previous_output'],
                             attempts=attempts, controls_frozen=int(match.group(1)) in (0, 1)))
        except (FileNotFoundError, ProcessLookupError, PermissionError):
            continue
    return sorted(rows, key=lambda row: row['physical'])


def remote_natives():
    reader = Reader(16 * 1024 * 1024)
    rows = []
    for process in Path('/proc').iterdir():
        if not process.name.isdigit():
            continue
        try:
            if process.stat().st_uid != os.getuid():
                continue
            current = identity(process)
            argv = current['argv']
            learner = 'gpu.orch_r125_continual_guard' in argv and 'native' in argv
            control = 'gpu.orch_r136_node1_launcher' in argv and 'control-native' in argv
            if not (learner or control) or '--config' not in argv or not Path(argv[0]).name.startswith('python'):
                continue
            guard_path = scoped_plan_path(argv[argv.index('--config') + 1])
            guard, guard_ref = reader.document(guard_path)
            plan, plan_ref = reader.document(scoped_plan_path(guard['plan_path']))
            require(plan_ref['sha256'] == guard['plan_sha256'], 'actual_native_plan_pin')
            if not re.search(r'/orch_r(?:136|139)_a100_', plan.get('root', '')):
                continue
            require(unchanged(current, identity(process)), 'stable_native_identity')
            keys = ('root', 'physical', 'physical_gpu', 'gpu_uuid', 'hard_end_unix', 'source_root',
                    'presleep_variant', 'mode', 'control', 'control_kind', 'adapter_rank', 'rank',
                    'sleep_enabled', 'max_sleeps', 'segments_per_sleep')
            rows.append(dict(actor=current, guard=guard_ref, plan=plan_ref,
                             plan_fields={key: plan[key] for key in keys if key in plan},
                             plan_keys=sorted(plan), guard_physical=guard.get('physical_gpu'),
                             control_native=control))
        except (FileNotFoundError, ProcessLookupError, PermissionError):
            continue
    return dict(hostname=socket.gethostname(), observed_unix=time.time(), natives=rows,
                bytes_read=reader.used, sealed_reads=0, key_reads=0, signals=0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--remote', action='store_true')
    args = parser.parse_args()
    if args.remote:
        print(json.dumps(remote_natives(), sort_keys=True))
        return
    reader = Reader()
    parents = local_parents(reader)
    repository = HERE.parents[3]
    command = shlex.join(['env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
                          '/localhome/local-rohing/v2/venv/bin/python', '-B', '-c',
                          Path(__file__).read_text(), '--remote'])
    remote = subprocess.run(['bash', 'gpu/a100_ssh.sh', command], cwd=repository,
                            capture_output=True, text=True, timeout=90)
    require(remote.returncode == 0, 'read_only_node_inventory_failed:' + remote.stderr[-500:])
    native_receipt = json.loads(remote.stdout)
    for row in parents:
        row['natives'] = [native for native in native_receipt['natives']
                          if native['plan_fields']['root'] == row['fields']['root']]
        row['unique_live_native'] = len(row['natives']) == 1 and row['natives'][0]['actor']['state'] not in ('Z', 'X')
    output = dict(schema='ROHIN174_NODE1_PARENT_BASELINE_V1', observed_unix=time.time(),
                  parents=parents, remote=native_receipt,
                  all_eight_parents=len(parents) == 8 and {row['physical'] for row in parents} == set(range(8)),
                  local_bytes_read=reader.used, inventory_source_sha256=digest(Path(__file__).read_bytes()),
                  no_switch=True, assignments_frozen=False, policy_frozen=False,
                  sealed_reads=0, key_reads=0, messages_sent=0, signals=0,
                  legacy_delivery_is_ingestion_not_request_exposure=True)
    path = HERE / ('INVENTORY_' + str(time.time_ns()) + '.json')
    with path.open('x') as stream:
        json.dump(output, stream, indent=2, sort_keys=True)
    print(json.dumps(dict(path=str(path), sha256=digest(path.read_bytes()),
                          rows=[dict(physical=row['physical'], label=row['label'],
                                     parent_pid=row['parent']['pid'], cadence=row['fields']['cadence_responses'],
                                     unique_live_native=row['unique_live_native']) for row in parents])))


if __name__ == '__main__':
    main()
