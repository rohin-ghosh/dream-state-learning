"""Terminal-only actual-record readout custody; Main executes status/finish.

No inference, training, selection or retries. The 300s collection window is
external to the readout controller budget; full release requires UUID/process/
queue reconciliation, not just a worker's cleanup flag.
"""
import argparse
from collections import Counter
import datetime as dt
import hashlib
import importlib.util
import io
import json
import math
import os
from pathlib import Path
import signal
import sys
import tarfile
import time
import xml.etree.ElementTree as ET


sys.dont_write_bytecode = True
HOME = Path('/localhome/local-rohing')
ROOT = HOME / 'astra_diagnostics/astra_rulegame_interaction_v3_record_readout_20260912_attempt1'
LOGS = ROOT.with_name(ROOT.name + '_launch')
SOURCE = HOME / 'astra_sources/610c6edd05ce9c85720ee6e992889badecc2c158'
DRIVER = Path('/tmp/astra_rulegame_record_readout_20260912.py')
LAUNCHER = Path('/tmp/astra_launch_rulegame_record_readout_20260912.py')
ARCHIVE = Path('/tmp/astra_rulegame_record_readout_terminal_20260912.tgz')
PLAN_SHA = 'cdb71865359498ca0f75db57566e638b667d2e849cc11c9cbd45dd6bfbb97375'
WRITE_PLAN_SHA = '48effd1ba154f497e5946d308f990624ada63bd905c198e0abfdf668131a8ee4'
DRIVER_SHA = '120e260a76395586736d47e4f8a55c425b090f9f8654208dcfbef7eac5cccbde'
LAUNCHER_SHA = '49178ed96a2404379af2cb511c111e91c399b77f84fd547618497744b02e5fef'
HELPER = Path('/tmp/astra_collect_memory_only_20260912.py')
HELPER_SHA = 'd2152c179ca9a6b9801933a480ed62cd203018868a52034e13676963787579eb'
CHECK_SHA = 'a586b03bdb9c52f1061aa1e477ae983cc9d45ec0a2cd440642851fd8df8b609f'
UUID = 'GPU-41a86250-88eb-ed8a-ddfe-9d6f93515da1'
PID, DEVICE = 234660, '2'
STARTED = '2026-09-12T21:39:20.620581+00:00'
CELLS = ('OFF', 'P_ON', 'A_ON')
COST_KEYS = ('requests', 'native_input_tokens', 'native_output_tokens', 'output_token_ceiling', 'generation_seconds')


def load(path, checksum, name):
    path = Path(path).absolute()
    if any(item.is_symlink() for item in (path, *path.parents)):
        raise ValueError('symlink dependency rejected')
    payload = path.read_bytes()
    if hashlib.sha256(payload).hexdigest() != checksum:
        raise ValueError('dependency changed: ' + str(path))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(payload, str(path), 'exec'), module.__dict__)
    return module


common = load(HELPER, HELPER_SHA, 'actual_record_readout_collection_common')
require, read, digest = common.require, common.read, common.digest


def finite_nonnegative(value):
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def controller_present():
    return Path(f'/proc/{PID}').exists()


def status():
    return dict(pid=PID, device=DEVICE, controller_present=controller_present(), scoring='NONE',
        markers={name: (ROOT / 'run' / name).is_file() for name in ('controller.json', 'result.json', 'failure.json')},
        cells={cell: {name: (ROOT / 'run' / cell / name).is_file() for name in
            ('process.json', 'supervision.json', 'data/manifest.json', 'data/failure.json', 'data/backend.cleanup.json')}
            for cell in CELLS})


def metadata():
    files, logs = common.metadata(ROOT, HOME), common.metadata(LOGS, HOME)
    require(not files.keys() & logs.keys(), 'metadata scopes overlap')
    return dict(sorted({**files, **logs}.items()))


def check_uuid(gpu, xml):
    devices = ET.fromstring(xml).findall('gpu')
    require(gpu['gpu_uuid'] == UUID and len(devices) == 1 and devices[0].findtext('uuid') == UUID, 'GPU UUID differs from launch')
    processes = devices[0].find('processes')
    require(processes is not None and not list(processes) and not (processes.text or '').strip(), 'GPU processes not empty')


def bind():
    require(digest(ROOT / 'plan.json') == read(ROOT / 'plan.sha256.json')['sha256'] == PLAN_SHA, 'readout plan changed')
    require(digest(LAUNCHER) == LAUNCHER_SHA, 'launcher source changed')
    bridge = load(DRIVER, DRIVER_SHA, 'actual_record_readout_collection_driver')
    root, plan, diagnostic = bridge.checked_plan(ROOT, PLAN_SHA)
    require(root == ROOT and plan['source_root'] == str(SOURCE) and plan['device'] == DEVICE
        and plan['python'] == str(HOME / 'v2/venv/bin/python') and plan['write_plan_sha256'] == WRITE_PLAN_SHA,
        'source/root/device/interpreter/write lineage differs')
    lineage = bridge.accepted_writes(plan)
    launch = read(LOGS / 'launch.json')
    require(launch['pid'] == PID and launch['node'] == 3 and launch['device'] == DEVICE
        and launch['phase'] == 'actual_record_parent_free_readout' and launch['source'] == str(SOURCE)
        and launch['root'] == str(ROOT) and launch['started_utc'] == STARTED and launch['plan_sha256'] == PLAN_SHA
        and launch['driver_sha256'] == DRIVER_SHA and launch['launcher_sha256'] == LAUNCHER_SHA
        and launch['write_plan_sha256'] == WRITE_PLAN_SHA and launch['continuous_reservation'] is True
        and launch['cells'] == list(CELLS) and launch['adaptation_test'] is False
        and launch['claim_boundary'] == diagnostic.CLAIM_BOUNDARY
        and (launch['controller_seconds'], launch['cleanup_reserve'], launch['worker_cap_seconds']) == (1800, 140, 600),
        'launch identity/bounds changed')
    require(launch['command'] == [plan['python'], '-B', str(DRIVER), 'evaluate', '--root', str(ROOT),
        '--plan-sha256', PLAN_SHA, '--allow-gpu'], 'launch command changed')
    require(launch['write_release_sha256'] == digest(Path(plan['write_root']) / 'run/main_release.json'), 'write release changed')
    check_uuid(launch['gpu'], common.read_bytes(LOGS / 'gpu.xml'))
    return bridge, plan, diagnostic, lineage


def raw_cost(data):
    costs = {key: 0 for key in COST_KEYS}
    roles, durations = Counter(), []
    requests = sorted((data / 'calls').glob('*.request.json'))
    for path in requests:
        sent = read(path)
        request = sent['request']
        response = read(path.with_name(path.name.replace('.request.', '.response.')))
        body = response['response']
        duration = response['ended'] - sent['started']
        require(finite_nonnegative(duration), 'raw generation clock invalid')
        role = request['role']
        require(role in ('wake', 'record') and request['max_tokens'] == (400 if role == 'wake' else 100), 'unexpected role/token cap')
        roles[role] += 1
        costs['native_input_tokens'] += len(body['prompt_token_ids'])
        costs['native_output_tokens'] += len(body['output_token_ids'])
        costs['output_token_ceiling'] += request['max_tokens']
        costs['generation_seconds'] += duration
        durations.append(duration)
    costs['requests'] = len(requests)
    require(roles['wake'] <= 20 and roles['record'] <= 12 and len(requests) <= 32, 'cell response cap exceeded')
    return costs, dict(roles), max(durations) if durations else None


def checked_cell(bridge, plan, diagnostic, lineage, controller, cell, tokenizer):
    stage, spec_path = ROOT / 'run' / cell, ROOT / 'run' / (cell + '.spec.json')
    data = stage / 'data'
    spec, process, supervision = read(spec_path), read(stage / 'process.json'), read(stage / 'supervision.json')
    expected_spec = bridge.worker_spec(ROOT, plan, lineage, cell, controller['hard_end'])
    expected_spec['nonce'] = spec['nonce']
    require(spec == expected_spec and isinstance(spec['nonce'], str) and len(spec['nonce']) == 32, 'worker spec/adapter/protocol differs')
    command = [plan['python'], '-B', str(DRIVER), '_worker', '--spec', str(spec_path),
               '--spec-sha256', digest(spec_path), '--allow-gpu']
    require(process['argv'] == command and process['device'] == DEVICE
        and type(process['pid']) is int and process['pid'] > 1 and process['pid'] == process['pgid']
        and finite_nonnegative(process['started']) and finite_nonnegative(process['timeout']) and 0 < process['timeout'] <= 600,
        'worker ownership/cap differs')
    require(supervision['device'] == DEVICE and supervision['ok'] is True and supervision['returncode'] == 0
        and supervision['error'] is None and supervision['reservation_release_verified'] is True
        and supervision['owned_group_empty'] is True and supervision['gpu_processes_absent'] is True
        and finite_nonnegative(supervision['reserved_seconds'])
        and supervision['reserved_seconds'] <= process['timeout'] + 140, 'worker supervision/cleanup/cost differs')
    isolation, ready = read(data / 'isolation.json'), read(data / 'backend.ready.json')
    require(isolation['pid'] == isolation['pgid'] == ready['pid'] == process['pid']
        and isolation['parent_pid'] == PID and isolation['spec_sha256'] == digest(spec_path)
        and isolation['parent_calls'] == 0 and isolation['task_prefix'] == '' and isolation['record_training'] is False,
        'capture isolation/worker receipt differs')
    require(finite_nonnegative(ready['ready'] - process['started']) and ready['ready'] - process['started'] <= 180,
        'backend readiness clock differs')
    audit = bridge.audit_cell(ROOT, plan, lineage, cell, diagnostic)
    diagnostic.audit_native_calls(tokenizer, data)
    result = audit['result']
    tasks = result['tasks']
    require([row['eid'] for row in tasks] == diagnostic.schedule()['evaluation'] and len(tasks) == 4,
        'four-task denominator/schedule differs')
    require(all(row['arm'] == cell and type(row['valid_quiz']) is bool and finite_nonnegative(row['quiz_accuracy'])
        and row['quiz_accuracy'] <= 1 and (row['valid_quiz'] or row['quiz_accuracy'] == 0) for row in tasks),
        'invalid or missing quiz must retain zero')
    require(result['cell'] == cell and result['mean_quiz_accuracy'] == sum(row['quiz_accuracy'] for row in tasks) / 4
        and result['allotted_record_opportunities'] == 12 and type(result['faithful_records']) is int
        and 0 <= result['faithful_records'] <= 12, 'score/record denominator differs')
    costs, roles, max_call_seconds = raw_cost(data)
    require(result['calls'] == costs['requests'] and result['roles'] == roles
        and read(data / 'native_audit.json')['calls'] == costs['requests'], 'native/role/call counts differ')
    require(read(stage / 'provenance.json') == audit, 'stored replay differs')
    usage = diagnostic.usage(data)
    require(all(math.isclose(sum(row[key] for row in usage.values()), value, rel_tol=0, abs_tol=1e-6 if key == 'generation_seconds' else 0)
        for key, value in costs.items()), 'raw/stored usage cost differs')
    receipt = dict(result=result, capture_sha256=digest(data / 'manifest.json'), spec_sha256=digest(spec_path),
        supervision_sha256=digest(stage / 'supervision.json'))
    return dict(verified=True, error=None, result=result, costs=costs, roles=roles, max_call_seconds=max_call_seconds,
        controller_receipt=receipt, worker_pid=process['pid'], worker_reserved_seconds=supervision['reserved_seconds'])


def audit(bridge, plan, diagnostic, lineage):
    run = ROOT / 'run'
    result = read(run / 'result.json') if (run / 'result.json').is_file() else None
    failure = read(run / 'failure.json') if (run / 'failure.json').is_file() else None
    require((result is None) != (failure is None), 'exactly one terminal required')
    successful, terminal = result is not None, result if result is not None else failure
    if successful:
        require(result['status'] == 'COMPLETE_EXPLORATORY_READOUT' and set(result['cells']) == set(CELLS)
            and result['inference'] == plan['protocol']['inference'] and result['claim_boundary'] == diagnostic.CLAIM_BOUNDARY
            and result['adaptation_test'] is False and result['semantic_nonleakage_certified'] is False
            and result['model_authentication_certified'] is False, 'complete terminal claims/cells differ')
        completed = list(CELLS)
    else:
        require(failure['retry'] is False and isinstance(failure['error'], str), 'failure terminal invalid')
        completed = failure['completed_cells']
        require(completed in [list(CELLS[:count]) for count in range(4)], 'failed completion order differs')
    controller = read(run / 'controller.json') if (run / 'controller.json').is_file() else None
    if controller is not None:
        require(controller['pid'] == PID and controller['plan_sha256'] == PLAN_SHA and controller['cleanup_reserve'] == 140
            and finite_nonnegative(controller['started_wall']) and controller['started_wall'] >= dt.datetime.fromisoformat(STARTED).timestamp()
            and controller['hard_end'] == min(controller['started_wall'] + 1800, plan['deadline'], plan['lease_cutoff']),
            'controller identity/deadline differs')
    controller_seconds = terminal.get('controller_seconds')
    require(controller_seconds is None or finite_nonnegative(controller_seconds), 'invalid controller seconds')
    within = (controller_seconds <= 1800 and controller['started_wall'] + controller_seconds <= controller['hard_end'] + .001
              if controller is not None and controller_seconds is not None else None)
    require(not successful or within is True, 'successful controller exceeded inclusive bound')
    stored_lineage = read(run / 'lineage.json') if (run / 'lineage.json').is_file() else None
    require(stored_lineage is None or stored_lineage == lineage, 'accepted-writes lineage changed')
    require(not successful or stored_lineage is not None, 'successful readout missing lineage')
    tokenizer, reports, supervision = None, {}, {}
    for cell in CELLS:
        stage = run / cell
        row = reports[cell] = dict(verified=False, controller_completed=cell in completed, error=None,
            result=None, costs=None, roles=None, max_call_seconds=None, worker_reserved_seconds=None,
            markers={name: (stage / name).is_file() for name in ('process.json', 'supervision.json', 'data/manifest.json', 'data/failure.json')})
        if (stage / 'supervision.json').is_file():
            receipt = read(stage / 'supervision.json')
            supervision[cell] = receipt
            if receipt.get('device') == DEVICE and finite_nonnegative(receipt.get('reserved_seconds')):
                row['worker_reserved_seconds'] = receipt['reserved_seconds']
        try:
            require(controller is not None and stored_lineage is not None, 'controller/lineage missing')
            require((stage / 'data/manifest.json').is_file(), 'capture incomplete or not started')
            if tokenizer is None:
                tokenizer = diagnostic.native_tokenizer(plan['model'])
            checked = checked_cell(bridge, plan, diagnostic, lineage, controller, cell, tokenizer)
            if successful:
                require(result['cells'][cell] == checked['controller_receipt'], 'terminal/capture/worker custody differs')
            row.update(checked)
        except (ValueError, OSError, KeyError, TypeError) as error:
            row['error'] = type(error).__name__ + ': ' + str(error)
            require(not successful, 'successful cell audit failed: ' + row['error'])
    require(set(ROOT.glob('**/supervision.json')) == {run / cell / 'supervision.json' for cell in supervision},
        'unexpected supervision outside three readout cells')
    verified = [row for row in reports.values() if row['verified']]
    pids = [row['worker_pid'] for row in verified]
    require(len(pids) == len(set(pids)) and PID not in pids, 'cells did not use distinct fresh workers')
    aggregate, total_costs = None, None
    if successful:
        total_costs = {key: sum(row['costs'][key] for row in verified) for key in COST_KEYS}
        require(total_costs['requests'] <= 96 and total_costs['output_token_ceiling'] <= 27600, 'three-cell call/token ceiling exceeded')
        means = {cell: row['result']['mean_quiz_accuracy'] for cell, row in reports.items()}
        aggregate = dict(P_minus_OFF=means['P_ON']-means['OFF'], A_minus_OFF=means['A_ON']-means['OFF'],
                         P_minus_A=means['P_ON']-means['A_ON'])
        require(all(type(result[key]) in (int, float) and result[key] == value for key, value in aggregate.items()), 'aggregate differs')
    observed = [row['worker_reserved_seconds'] for row in reports.values() if row['worker_reserved_seconds'] is not None]
    return dict(status='COMPLETE_EXPLORATORY_READOUT' if successful else 'FAILED_PARTIAL_NO_AGGREGATE', readout_success=successful,
        cells=reports, aggregate=aggregate, costs=total_costs, terminal=terminal, controller=controller,
        controller_seconds=controller_seconds, controller_within_bound=within,
        observed_worker_seconds=sum(observed) if observed else None, worker_cost_complete=len(observed) == 3,
        semantic_nonleakage_certified=False, adaptation_test=False)


def release_check():
    require('CUDA_VISIBLE_DEVICES' not in os.environ, 'use env -u CUDA_VISIBLE_DEVICES for full release')
    checker = load(SOURCE / 'gpu/astra_mini_sudoku_diagnostic.py', CHECK_SHA, 'actual_record_readout_full_release')
    return checker.check_free(DEVICE)


def collect(started, monotonic):
    observed = status()
    require(not observed['controller_present'] and (observed['markers']['result.json'] or observed['markers']['failure.json']),
        'wait for absent controller AND terminal; no live reads or retry')
    validation_path = Path(str(ARCHIVE) + '.validation.json')
    prefix = ROOT.parent.relative_to(HOME).as_posix() + '/'
    if ARCHIVE.exists() or validation_path.exists():
        require(ARCHIVE.is_file() and validation_path.is_file(), 'partial capsule preserved; no overwrite/retry')
        validation = read(validation_path)
        require(validation['collector_sha256'] == digest(__file__) and validation['plan_sha256'] == PLAN_SHA
            and validation['sha256'] == digest(ARCHIVE) and validation['files'] == metadata(), 'existing capsule/evidence changed')
        common.validate_archive(io.BytesIO(common.read_bytes(ARCHIVE)), validation['files'], prefix)
        require(not controller_present(), 'controller present after archive verification')
        return dict(status='ALREADY_COLLECTED_VERIFIED_NO_WRITES', sha256=validation['sha256'])
    release_json, release_xml = ROOT / 'run/main_release.json', ROOT / 'run/main_release.xml'
    require(not release_json.exists() and not release_xml.exists(), 'partial release preserved; manual reconciliation, no retry')
    before = metadata()
    bridge, plan, diagnostic, lineage = bind()
    report = audit(bridge, plan, diagnostic, lineage)
    gpu, xml = release_check()
    check_uuid(gpu, xml)
    released = time.time()
    require(not controller_present() and metadata() == before, 'evidence/controller changed during collection')
    bridge.checked_plan(ROOT, PLAN_SHA)
    require(bridge.accepted_writes(plan) == lineage, 'adapter/write identity changed during collection')
    full_seconds = released-dt.datetime.fromisoformat(STARTED).timestamp()
    require(finite_nonnegative(full_seconds), 'invalid full launch-to-release clock')
    common.write_new(release_xml, xml.encode())
    common.write_json(release_json, dict(full_release=True, controller_absent=True, controller_pid=PID, device=DEVICE,
        gpu=gpu, release_utc=dt.datetime.fromtimestamp(released, dt.timezone.utc).isoformat(),
        full_reservation_seconds=full_seconds, plan_sha256=PLAN_SHA, launch_sha256=digest(LOGS / 'launch.json'),
        terminal_sha256=digest(ROOT / 'run' / ('result.json' if report['readout_success'] else 'failure.json')),
        xml_sha256=digest(release_xml), collector_sha256=digest(__file__), status=report['status'],
        controller_seconds=report['controller_seconds'], observed_worker_seconds=report['observed_worker_seconds'],
        worker_cost_complete=report['worker_cost_complete'], collection_started=started,
        collection_seconds_at_release=time.monotonic()-monotonic,
        bounds=dict(controller=1800, worker=600, cleanup_reserve=140, external_collection=300),
        accounting='Generation is inside workers; worker supervised/cleanup windows are inside controller. Full launch-to-observed-vacancy includes CPU/gaps/wait-to-collect. Collection overlaps release interval; clocks are not additive.'))
    files = metadata()
    release_names = {path.relative_to(HOME).as_posix() for path in (release_json, release_xml)}
    require(set(files) == set(before) | release_names and all(files[name] == checksum for name, checksum in before.items()),
        'evidence changed before packing')
    common.unaliased(ARCHIVE)
    with ARCHIVE.open('xb') as stream, tarfile.open(fileobj=stream, mode='w:gz', format=tarfile.USTAR_FORMAT) as archive:
        for name, checksum in files.items():
            payload = common.read_bytes(HOME / name)
            require(hashlib.sha256(payload).hexdigest() == checksum, 'metadata changed while packing')
            member = tarfile.TarInfo(name)
            member.size, member.mode = len(payload), 0o600
            archive.addfile(member, io.BytesIO(payload))
    common.validate_archive(io.BytesIO(common.read_bytes(ARCHIVE)), files, prefix)
    require(not controller_present() and metadata() == files, 'evidence/controller changed after packing')
    bridge.checked_plan(ROOT, PLAN_SHA)
    require(bridge.accepted_writes(plan) == lineage, 'adapter/write identity changed after packing')
    elapsed = time.monotonic()-monotonic
    require(elapsed <= 300, 'collection exceeded 300s; preserve evidence, no retry')
    common.write_json(validation_path, dict(archive=str(ARCHIVE), sha256=digest(ARCHIVE), files=files, audit=report,
        plan_sha256=PLAN_SHA, collector_sha256=digest(__file__), full_reservation_seconds=full_seconds,
        collection_seconds=elapsed, collection_completed_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
        excluded_suffixes=sorted(common.EXCLUDED), excluded_directories=['__pycache__'],
        weights='Accepted P/A saved adapter identity checked natively; all weight bytes stay at original write root.',
        scope='Readout replay/native token custody and full release, not a learning claim, semantic certificate or model-origin authentication.'))
    return dict(status='COLLECTED', readout_status=report['status'], sha256=digest(ARCHIVE), files=len(files), collection_seconds=elapsed)


class CollectionExpired(BaseException):
    pass


def expired(number, frame):
    raise CollectionExpired('300s external collector margin exhausted; preserve partial evidence, no retry')


def finish():
    require(signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0), 'existing timer conflicts')
    started, monotonic = time.time(), time.monotonic()
    handler = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, 300)
    try:
        return collect(started, monotonic)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, handler)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=('status', 'finish'))
    args = parser.parse_args()
    print(json.dumps(status() if args.stage == 'status' else finish(), indent=2, sort_keys=True, allow_nan=False), flush=True)
