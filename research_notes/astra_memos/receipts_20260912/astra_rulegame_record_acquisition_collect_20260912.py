"""Main-only terminal acquisition custody; no scoring, training, kills or retries.

status reads only launch/process receipts and terminal marker existence. finish
opens score bodies only after a terminal marker and absence of every owned
controller/worker PID, process group and session. Failed runs remain diagnostic
metadata, never a partial science aggregate. Collection is bounded to 300s.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import io
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import signal
import stat
import sys
import tarfile
import time
import xml.etree.ElementTree as ET


sys.dont_write_bytecode = True
DRIVER = Path('/tmp/astra_rulegame_record_acquisition_20260912.py')
DRIVER_SHA = 'ae3bbad045a7ec205ed2d711e03fcdcd08aa3b2bde8b529decda597d6e9888ea'
COMMON = Path('/tmp/astra_collect_memory_only_20260912.py')
COMMON_SHA = 'd2152c179ca9a6b9801933a480ed62cd203018868a52034e13676963787579eb'
CHECK_SHA = 'a586b03bdb9c52f1061aa1e477ae983cc9d45ec0a2cd440642851fd8df8b609f'
LAUNCHER = Path('/tmp/astra_launch_rulegame_record_acquisition_20260912.py')
LAUNCHER_SHA = '273c8bd297ab4bec98287771c2910bf6f759194b8686f41dfd3ae5c1f6eebf19'
CELLS = ('OFF', 'P', 'A')
MAX_FILE = 32 * 1024 * 1024
MAX_TOTAL = 256 * 1024 * 1024
MAX_FILES = 2048
WEIGHTS = {'.bin', '.safetensors', '.pt', '.pth', '.ckpt', '.pyc', '.pyo'}
TEXT = {'.json', '.jsonl', '.log', '.txt', '.xml', '.py', '.md', '.sha256', '.csv'}
SECRET_KEYS = {'password', 'passwd', 'secret', 'api_key', 'access_token', 'refresh_token',
               'authorization', 'private_key', 'hf_token', 'aws_secret_access_key'}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def unaliased(path):
    path = Path(os.path.abspath(Path(path).expanduser()))
    require(not any(part.is_symlink() for part in (path, *path.parents)), 'symlink path rejected')
    return path


def payload(path, limit=MAX_FILE):
    path = unaliased(path)
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_size <= limit,
                'special/hardlinked/oversized file rejected')
        data = stream.read(limit + 1)
        after = os.fstat(stream.fileno())
        fields = ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns', 'st_nlink')
        require(len(data) == before.st_size and all(getattr(before, key) == getattr(after, key)
                == getattr(path.stat(), key) for key in fields), 'file changed during read')
    return data


def digest(path):
    return hashlib.sha256(payload(path)).hexdigest()


def unique(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'duplicate JSON key')
        result[key] = value
    return result


def read(path):
    def reject(value):
        raise ValueError('nonfinite JSON rejected')
    return json.loads(payload(path), object_pairs_hook=unique, parse_constant=reject)


def write_new(path, data):
    descriptor = os.open(unaliased(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'wb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def write_json(path, value):
    write_new(path, (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode())


def load(path, pin, name):
    data = payload(path)
    require(hashlib.sha256(data).hexdigest() == pin, 'dependency hash differs')
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(data, str(path), 'exec'), module.__dict__)
    return module


def finite(value):
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def utc(value):
    parsed = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    require(parsed.tzinfo is not None, 'timezone required')
    return parsed.timestamp()


def process_snapshot():
    result = []
    for path in Path('/proc').glob('[0-9]*/stat'):
        try:
            fields = path.read_text().rsplit(')', 1)[1].split()
        except FileNotFoundError:
            continue
        result.append(dict(pid=int(path.parent.name), pgid=int(fields[2]), session=int(fields[3])))
    return result


def status(root, plan_sha256, launch_root, launch_sha256):
    root, logs = unaliased(root), unaliased(launch_root)
    require(root.is_dir() and logs.is_dir() and logs.parent == root.parent and root != logs,
            'distinct sibling root/launch directories required')
    require(digest(logs / 'launch.json') == launch_sha256, 'launch pin differs')
    launch = read(logs / 'launch.json')
    require(launch['root'] == str(root) and launch['plan_sha256'] == plan_sha256
            and launch['driver_sha256'] == DRIVER_SHA and type(launch['pid']) is int and launch['pid'] > 1,
            'launch root/plan/driver/PID differs')
    require(utc(launch['started_utc']) <= time.time(), 'launch starts in future')
    owned, cells = {launch['pid']}, {}
    expected_process_paths = {root / 'run' / cell / 'process.json' for cell in CELLS}
    require(set(root.glob('**/process.json')) <= expected_process_paths, 'unexpected owned process receipt')
    for cell in CELLS:
        stage = root / 'run' / cell
        receipt = stage / 'process.json'
        cells[cell] = {name: unaliased(stage / name).is_file() for name in
                       ('process.json', 'supervision.json', 'data/manifest.json', 'data/failure.json')}
        if receipt.exists():
            process = read(receipt)
            require(type(process['pid']) is int and process['pid'] > 1 and process['pgid'] == process['pid'],
                    'worker is not a distinct session leader')
            require(process['pid'] not in owned, 'reused controller/worker PID')
            owned.add(process['pid'])
    live = [row for row in process_snapshot() if any(row[key] in owned for key in ('pid', 'pgid', 'session'))]
    markers = {name: unaliased(root / 'run' / name).is_file() for name in ('result.json', 'failure.json')}
    return dict(ready=not live and sum(markers.values()) == 1, owned_ids=sorted(owned), live_owned=live,
                markers=markers, cells=cells, score_bodies_read=False, launch=launch)


def scan_text(data, name):
    text = data.decode('utf-8')
    lower = PurePosixPath(name).name.lower()
    require(not any(word in lower for word in ('secret', 'credential', '.env', 'private_key')),
            'credential filename rejected')
    require(not re.search(r'-----BEGIN [A-Z ]*PRIVATE KEY-----|\b(?:hf_|sk-)[A-Za-z0-9_-]{20,}|'
                          r'(?i:authorization\s*[:=]\s*[\"\x27]?bearer\s+\S+)', text), 'credential payload rejected')
    if name.endswith('.json'):
        def inspect(pairs):
            for key, value in pairs:
                require(key.lower() not in SECRET_KEYS, 'credential JSON field rejected')
            return unique(pairs)
        json.loads(text, object_pairs_hook=inspect)
    require(not re.search(r'(?im)^\s*(?:export\s+)?(?:HF_TOKEN|API_KEY|PASSWORD|AWS_SECRET_ACCESS_KEY)\s*=', text),
            'credential assignment rejected')


def bind_launch(root, logs, plan, launch):
    require(launch['device'] == plan['device'] and launch['command'] ==
            [plan['python'], '-B', str(DRIVER), 'run', '--root', str(root), '--plan-sha256', launch['plan_sha256'], '--allow-gpu'],
            'launch command/device differs')
    require(launch['source'] == plan['source_root'] and launch['write_plan_sha256'] == plan['write_plan_sha256']
            and launch['write_release_sha256'] == digest(Path(plan['write_root']) / 'run/main_release.json')
            and launch['launcher_sha256'] == LAUNCHER_SHA == digest(LAUNCHER), 'launch source/write release/launcher differs')
    expected = dict(phase='trained_record_acquisition', continuous_reservation=True, controller_seconds=1800,
                    cleanup_reserve=140, worker_cap_seconds=600, external_collection_margin_seconds=300,
                    requests=24, candidate_forwards=48, generations=0, updates=0, cells=list(CELLS), adaptation_test=False,
                    model_origin='UNRESOLVED_LOCAL_HASHES_ONLY')
    require(all(launch[key] == value for key, value in expected.items()), 'launch prospective protocol differs')
    devices = ET.fromstring(payload(logs / 'gpu.xml')).findall('gpu')
    require(len(devices) == 1 and devices[0].findtext('uuid') == launch['gpu']['gpu_uuid'], 'launch GPU XML identity differs')
    processes = devices[0].find('processes')
    require(processes is not None and not list(processes) and not (processes.text or '').strip(), 'launch GPU was not empty')


def inventory(root, logs, sources=()):
    files, excluded, size, entries = {}, [], 0, 0
    for base, prefix in ((root, 'metadata/root'), (logs, 'metadata/launch')):
        for directory, dirs, names in os.walk(base, followlinks=False):
            for name in dirs + names:
                entries += 1
                require(entries <= MAX_FILES, 'filesystem entry-count bound exceeded')
                path = unaliased(Path(directory) / name)
                require(path.is_dir() or path.is_file(), 'special filesystem entry rejected')
            dirs[:] = sorted(name for name in dirs if name != '__pycache__')
            for name in sorted(names):
                path = Path(directory) / name
                member = prefix + '/' + path.relative_to(base).as_posix()
                if path.suffix.lower() in WEIGHTS:
                    excluded.append(member)
                    continue
                require(path.suffix.lower() in TEXT, 'unknown metadata type rejected: ' + member)
                files[member] = path
    for index, (path, pin) in enumerate(sorted(sources)):
        path = unaliased(path)
        require(path.suffix in {'.py', '.txt'} and digest(path) == pin, 'source custody differs')
        files[f'metadata/source/{index:03d}_{path.name}'] = path
    require(0 < len(files) <= MAX_FILES, 'metadata file-count bound exceeded')
    hashes = {}
    for name, path in sorted(files.items()):
        data = payload(path)
        scan_text(data, name)
        size += len(data)
        require(size <= MAX_TOTAL, 'metadata byte bound exceeded')
        hashes[name] = hashlib.sha256(data).hexdigest()
    return files, hashes, sorted(excluded)


def check_cell(bridge, root, plan, cell, controller):
    stage = root / 'run' / cell
    process, supervision = read(stage / 'process.json'), read(stage / 'supervision.json')
    spec_path = root / 'run' / (cell + '.spec.json')
    command = [plan['python'], '-B', str(DRIVER), '_worker', '--spec', str(spec_path),
               '--spec-sha256', digest(spec_path), '--allow-gpu']
    require(process['argv'] == command and process['device'] == plan['device'] and finite(process['started'])
            and finite(process['timeout']) and 0 < process['timeout'] <= 600, 'worker command/device/cap differs')
    require(supervision['device'] == plan['device'] and supervision['ok'] is True and supervision['returncode'] == 0
            and supervision['error'] is None
            and all(supervision[key] is True for key in ('owned_group_empty', 'gpu_processes_absent', 'reservation_release_verified'))
            and finite(supervision['reserved_seconds']) and supervision['reserved_seconds'] <= process['timeout'] + 140,
            'worker supervision/release/cost differs')
    data = stage / 'data'
    isolation, ready = read(data / 'isolation.json'), read(data / 'backend.ready.json')
    require(isolation['pid'] == isolation['pgid'] == ready['pid'] == process['pid']
            and isolation['parent_pid'] == controller['pid'] and isolation['spec_sha256'] == digest(spec_path)
            and isolation['generations'] == 0 and isolation['training'] is False, 'fresh worker isolation differs')
    require(finite(ready['ready']) and 0 <= ready['ready'] - process['started'] <= 180, 'backend load bound differs')
    native = ready['runtime']
    expected = dict(loader='conditional_behavior_readout.HFScorer', scorer='semantic_carrier_diagnostic.score',
                    training=False, trainable_parameters=0, adapter_count=0 if cell == 'OFF' else 1,
                    use_cache=False, load_dtype='bf16', attention='eager', generation=False)
    require(all(native[key] == value for key, value in expected.items()) and type(native['parameter_count']) is int
            and native['parameter_count'] > 0 and native['dtypes'], 'frozen native backend receipt differs')
    result = bridge.replay(root, plan, cell)
    spec = read(spec_path)
    require(isinstance(spec['nonce'], str) and re.fullmatch('[0-9a-f]{32}', spec['nonce']), 'worker nonce differs')
    maximum = 0.0
    for request in plan['requests']:
        call = data / 'calls' / request['call_id']
        sent, returned = read(str(call) + '.request.json'), read(str(call) + '.response.json')
        require(set(returned['response']) == {'token_logprobs', 'native_forwards'}, 'unexpected generation/score response fields')
        duration = returned['ended'] - sent['started']
        require(0 <= duration <= 120 and ready['ready'] <= sent['started'] <= returned['ended']
                <= process['started'] + supervision['reserved_seconds'] + 1e-6, 'call/worker clock differs')
        maximum = max(maximum, duration)
    require((result['costs']['requests'], result['costs']['candidate_forwards'], result['costs']['generations']) == (8, 16, 0),
            'cell workload differs')
    reduction = stage / 'reduction.json'
    if reduction.exists():
        require(read(reduction) == result, 'stored reduction differs from raw replay')
    return dict(replay=result, worker_pid=process['pid'], worker_started=process['started'],
                worker_reserved_seconds=supervision['reserved_seconds'], max_call_seconds=maximum,
                process_sha256=digest(stage / 'process.json'), supervision_sha256=digest(stage / 'supervision.json'))


def audit(bridge, root, plan, diagnostic, launch):
    run = root / 'run'
    successful = (run / 'result.json').exists()
    terminal = read(run / ('result.json' if successful else 'failure.json'))
    controller = read(run / 'controller.json') if (run / 'controller.json').exists() else None
    reports, errors, captures = {}, [], {}
    seconds = terminal.get('controller_seconds')
    require(finite(seconds), 'terminal controller clock missing/invalid')
    if controller is not None:
        require(controller['pid'] == launch['pid'] and controller['plan_sha256'] == launch['plan_sha256']
                and finite(controller['started_wall']) and utc(launch['started_utc']) <= controller['started_wall']
                and controller['hard_end'] == min(controller['started_wall'] + 1800, plan['deadline'], plan['lease_cutoff'])
                and (controller['cleanup_reserve'], controller['requests'], controller['candidate_forwards'], controller['generations'])
                == (140, 24, 48, 0), 'controller identity/prospective limits differ')
    within = controller is not None and seconds <= 1800 and controller['started_wall'] + seconds <= controller['hard_end'] + .001
    if successful:
        require(within and terminal['status'] == 'COMPLETE_TRAINED_RECORD_ACQUISITION_CHECK'
                and set(terminal['cells']) == set(CELLS), 'complete controller/coverage differs')
    else:
        require(terminal['aggregate'] is None and terminal['retry'] is False
                and terminal['completed_cells'] == list(CELLS)[:len(terminal['completed_cells'])], 'failure prefix/aggregate differs')
    tokenizer = diagnostic.native_tokenizer(plan['model'])
    bridge.checked_plan(root, launch['plan_sha256'], tokenizer)
    for cell in CELLS:
        try:
            require(controller is not None, 'controller receipt absent')
            report = check_cell(bridge, root, plan, cell, controller)
            reports[cell] = dict(verified=True, **report)
            captures[cell] = report['replay']
            if successful:
                require((run / cell / 'reduction.json').is_file() and terminal['cells'][cell] == report['replay'],
                        'complete result/raw replay differs')
        except (ValueError, OSError, KeyError, TypeError) as error:
            reports[cell] = dict(verified=False, error_type=type(error).__name__, detail=str(error)[:1000], costs=None)
            errors.append(cell)
    verified = [reports[cell] for cell in CELLS if reports[cell]['verified']]
    require(len({row['worker_pid'] for row in verified}) == len(verified)
            and all(row['worker_pid'] != launch['pid'] for row in verified), 'fresh worker PIDs differ')
    require(all(left['worker_started'] + left['worker_reserved_seconds'] <= right['worker_started']
                for left, right in zip(verified, verified[1:])), 'OFF/P/A supervised windows overlap/reorder')
    expected_supervision = {run / cell / 'supervision.json' for cell in CELLS if (run / cell / 'supervision.json').exists()}
    require(set(root.glob('**/supervision.json')) == expected_supervision, 'unexpected scoring worker')
    summary, totals = None, None
    if successful and not errors:
        summary = bridge.summarize(captures)
        totals = {key: sum(row['costs'][key] for row in captures.values()) for key in captures['OFF']['costs']}
        require((totals['requests'], totals['candidate_forwards'], totals['generations']) == (24, 48, 0)
                and all(terminal[key] == totals[key] for key in ('requests', 'candidate_forwards', 'generations'))
                and terminal['summary'] == summary, '24/48/0 aggregate replay differs')
        require(terminal['claim_boundary'] == bridge.protocol()['interpretation']
                and terminal['model_authentication_certified'] is False and terminal['semantic_nonleakage_certified'] is False,
                'scientific boundary differs')
    return dict(verified=successful and not errors, status='VERIFIED_COMPLETE' if successful and not errors else 'FAILED_PARTIAL_OR_AUDIT',
                cells=reports, aggregate=summary, totals=totals, controller_seconds=seconds, controller_within_bound=within,
                observed_verified_worker_seconds=sum(row['worker_reserved_seconds'] for row in verified) if verified else None,
                verified_worker_cost_complete=len(verified) == 3,
                terminal_sha256=digest(run / ('result.json' if successful else 'failure.json')))


def release_check(plan, expected_uuid):
    require('CUDA_VISIBLE_DEVICES' not in os.environ, 'unset CUDA_VISIBLE_DEVICES for full release check')
    checker = load(Path(plan['source_root']) / 'gpu/astra_mini_sudoku_diagnostic.py', CHECK_SHA, 'acquisition_release_checker')
    gpu, xml = checker.check_free(plan['device'])
    devices = ET.fromstring(xml).findall('gpu')
    require(len(devices) == 1 and gpu['gpu_uuid'] == devices[0].findtext('uuid') == expected_uuid, 'GPU UUID differs')
    processes = devices[0].find('processes')
    require(processes is not None and not list(processes) and not (processes.text or '').strip(), 'GPU process list not empty')
    return gpu, xml


def pack(path, files, hashes):
    common = load(COMMON, COMMON_SHA, 'acquisition_safe_archive_common')
    descriptor = os.open(unaliased(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'wb') as stream, tarfile.open(fileobj=stream, mode='w:gz', format=tarfile.USTAR_FORMAT) as archive:
        for name, source in sorted(files.items()):
            data = payload(source)
            require(hashlib.sha256(data).hexdigest() == hashes[name], 'metadata changed during packing')
            member = tarfile.TarInfo(name)
            member.size, member.mode = len(data), 0o600
            archive.addfile(member, io.BytesIO(data))
    pin = file_hash(path)
    with path.open('rb') as stream:
        common.validate_archive(stream, hashes, 'metadata/')
    require(file_hash(path) == pin, 'archive changed during validation')
    return pin


def collect(root, plan_sha256, launch_root, launch_sha256, out):
    started, wall = time.monotonic(), time.time()
    root, logs, output = unaliased(root), unaliased(launch_root), unaliased(out)
    observed = status(root, plan_sha256, logs, launch_sha256)
    require(observed['ready'], 'wait for terminal AND all owned sessions absent; no score reads')
    require(output.parent == root.parent and output not in (root, logs), 'fresh sibling collection output required')
    output.mkdir(mode=0o700)
    write_json(output / 'started.json', dict(started_wall=wall, plan_sha256=plan_sha256, launch_sha256=launch_sha256,
               collector_sha256=digest(__file__), deadline_seconds=300, blind_until_all_owned_stopped=True))
    try:
        inventory(root, logs)
        bridge = load(DRIVER, DRIVER_SHA, 'acquisition_collected_driver')
        checked_root, plan, diagnostic = bridge.checked_plan(root, plan_sha256)
        launch = observed['launch']
        require(checked_root == root, 'checked root differs')
        bind_launch(root, logs, plan, launch)
        sources = dict(plan['source_pins'], **plan['scoring_pins'])
        sources.update({str(DRIVER): DRIVER_SHA, str(COMMON): COMMON_SHA, str(Path(__file__).absolute()): digest(__file__),
                        str(LAUNCHER): LAUNCHER_SHA,
                        plan['write_driver']: plan['write_driver_sha256'],
                        str(Path(plan['source_root']) / 'gpu/astra_mini_sudoku_diagnostic.py'): CHECK_SHA})
        sources = tuple(sources.items())
        files, before, excluded = inventory(root, logs, sources)
        try:
            report = audit(bridge, root, plan, diagnostic, launch)
        except Exception as error:
            report = dict(verified=False, status='AUDIT_FAILED', aggregate=None, totals=None,
                          error_type=type(error).__name__, detail=str(error)[:1000])
        release = dict(full_release=False, gpu=None, error_type=None)
        try:
            require(status(root, plan_sha256, logs, launch_sha256)['ready'], 'owned session reappeared')
            gpu, xml = release_check(plan, launch['gpu']['gpu_uuid'])
            require(status(root, plan_sha256, logs, launch_sha256)['ready'], 'owned session reappeared')
            release = dict(full_release=True, gpu=gpu, observed_wall=time.time(), error_type=None)
            write_new(output / 'release.xml', xml.encode())
        except Exception as error:
            release['error_type'] = type(error).__name__
            release['detail'] = str(error)[:1000]
        bridge.checked_plan(root, plan_sha256)
        bind_launch(root, logs, plan, launch)
        require(inventory(root, logs, sources)[1:] == (before, excluded), 'terminal metadata changed')
        report['aggregate'] = report.get('aggregate') if release['full_release'] and report['verified'] else None
        report['totals'] = report.get('totals') if release['full_release'] and report['verified'] else None
        write_json(output / 'audit.json', report)
        write_json(output / 'release.json', release)
        full_seconds = release['observed_wall'] - utc(launch['started_utc']) if release['full_release'] else None
        write_json(output / 'custody.json', dict(input_hashes=before, excluded_weights=excluded, source_pins=dict(sources),
                   plan_sha256=plan_sha256, launch_sha256=launch_sha256, full_launch_to_release_seconds=full_seconds,
                   controller_seconds=report.get('controller_seconds'), collection_seconds_at_snapshot=time.monotonic()-started,
                   accounting='Call/load inside supervised workers; workers/cleanup inside controller; launch-to-observed-release includes gaps and collection. Nested clocks, never additive.',
                   claims='Trained-record conditional acquisition only; neither semantic nonleakage nor model authentication certified.',
                   secret_policy='Known credential keys/patterns rejected, no environment dump; not a universal secret detector.'))
        for path in sorted(output.iterdir()):
            name = 'metadata/collection/' + path.name
            data = payload(path)
            scan_text(data, name)
            files[name], before[name] = path, hashlib.sha256(data).hexdigest()
        require(len(files) <= MAX_FILES and sum(path.stat().st_size for path in files.values()) <= MAX_TOTAL, 'capsule bounds exceeded')
        archive = output / 'metadata.tgz'
        archive_pin = pack(archive, files, before)
        require(status(root, plan_sha256, logs, launch_sha256)['ready'], 'owned session reappeared after archive')
        bridge.checked_plan(root, plan_sha256)
        bind_launch(root, logs, plan, launch)
        require(all(digest(path) == before[name] for name, path in files.items()), 'metadata changed after archive')
        require(set(inventory(root, logs, sources)[0]) == {name for name in files if not name.startswith('metadata/collection/')},
                'new metadata appeared after archive')
        require(file_hash(archive) == archive_pin, 'validated archive changed')
        elapsed = time.monotonic() - started
        require(elapsed <= 300, 'external collection window exceeded')
        result = dict(status='COLLECTED_COMPLETE' if report['verified'] and release['full_release'] else 'COLLECTED_PARTIAL_NO_AGGREGATE',
                      archive=str(archive), archive_sha256=archive_pin,
                      files=before, collection_seconds=elapsed, full_release=release['full_release'],
                      science_aggregate_available=report['verified'] and release['full_release'], retry=False)
        write_json(output / 'validation.json', result)
        return {key: value for key, value in result.items() if key != 'files'}
    except BaseException as error:
        write_json(output / 'failure.json', dict(error_type=type(error).__name__, aggregate=None, retry=False,
                   collection_seconds=time.monotonic()-started, partial_artifacts_preserved=True))
        raise


def file_hash(path):
    result, size = hashlib.sha256(), 0
    path = unaliased(path)
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1, 'unsafe archive hash input')
        for data in iter(lambda: stream.read(1024 * 1024), b''):
            size += len(data)
            require(size <= MAX_TOTAL + 16*1024*1024, 'archive byte bound exceeded')
            result.update(data)
        after = os.fstat(stream.fileno())
        require(size == before.st_size and all(getattr(before, key) == getattr(after, key) == getattr(path.stat(), key)
                for key in ('st_ino', 'st_dev', 'st_size', 'st_mtime_ns', 'st_ctime_ns')), 'archive changed during hashing')
    return result.hexdigest()


class CollectionExpired(BaseException):
    pass


def finish(**kwargs):
    require(signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0), 'existing timer conflicts')
    def expired(number, frame):
        raise CollectionExpired('300s external custody window exhausted')
    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, 300)
    try:
        return collect(**kwargs)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('status', 'finish'))
    for name in ('root', 'plan-sha256', 'launch-root', 'launch-sha256'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--out')
    args = vars(parser.parse_args(argv))
    action = args.pop('action')
    if action == 'status':
        args.pop('out')
        result = status(**args)
        result.pop('launch')
    else:
        require(args['out'], '--out fresh sibling directory required')
        result = finish(**args)
    print(json.dumps(result, sort_keys=True, allow_nan=False), flush=True)


if __name__ == '__main__':
    main()
