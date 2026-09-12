"""Terminal collection of the actual-record paired write; never a readout."""
import argparse
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
ROOT = HOME / 'astra_diagnostics/astra_rulegame_interaction_v3_record_write_20260912_attempt2'
LOGS = ROOT.with_name(ROOT.name + '_launch')
SOURCE = HOME / 'astra_sources/610c6edd05ce9c85720ee6e992889badecc2c158'
DRIVER = Path('/tmp/astra_rulegame_record_write_v2_20260912.py')
ARCHIVE = Path('/tmp/astra_rulegame_record_write_terminal_20260912.tgz')
PLAN_SHA = '48effd1ba154f497e5946d308f990624ada63bd905c198e0abfdf668131a8ee4'
DRIVER_SHA = '183b48be6193da953f699d718575f9227fd946d9f8111d2d1647ae5dd431ec7c'
LAUNCHER_SHA = '4d89e0767a50e514f8080313fc59af10b632c13594b449ae390ecd7eeea9a1d6'
HELPER_SHA = 'd2152c179ca9a6b9801933a480ed62cd203018868a52034e13676963787579eb'
CHECK_SHA = 'a586b03bdb9c52f1061aa1e477ae983cc9d45ec0a2cd440642851fd8df8b609f'
PID, DEVICE, ARMS = 233174, '2', ('P', 'A')
STARTED = '2026-09-12T21:30:37.652148+00:00'
UUID = 'GPU-41a86250-88eb-ed8a-ddfe-9d6f93515da1'


def load(path, pin, name):
    payload = path.read_bytes()
    if hashlib.sha256(payload).hexdigest() != pin:
        raise ValueError('dependency changed: ' + str(path))
    module = importlib.util.module_from_spec(importlib.util.spec_from_file_location(name, path))
    sys.modules[name] = module
    exec(compile(payload, str(path), 'exec'), module.__dict__)
    return module


common = load(Path('/tmp/astra_collect_memory_only_20260912.py'), HELPER_SHA, 'record_write_collection_common')
require, read, digest = common.require, common.read, common.digest


def controller_present():
    return Path(f'/proc/{PID}').exists()


def status():
    return dict(pid=PID, device=DEVICE, controller_present=controller_present(), scoring='NONE',
        markers={name: (ROOT / 'run' / name).is_file() for name in ('controller.json', 'result.json', 'failure.json')},
        arms={arm: {name: (ROOT / name.format(arm=arm)).is_file() for name in
            ('run/{arm}/process.json', 'run/{arm}/supervision.json', 'fits/{arm}/manifest.json',
             'fits/{arm}/receipt.json', 'fits/{arm}/adapter/DONE')} for arm in ARMS})


def metadata():
    files, logs = common.metadata(ROOT, HOME), common.metadata(LOGS, HOME)
    require(not files.keys() & logs.keys(), 'metadata scopes overlap')
    return dict(sorted({**files, **logs}.items()))


def check_uuid(gpu, xml):
    devices = ET.fromstring(xml).findall('gpu')
    require(gpu['gpu_uuid'] == UUID and len(devices) == 1 and devices[0].findtext('uuid') == UUID, 'GPU UUID differs from launch')
    processes = devices[0].find('processes')
    require(processes is not None and not list(processes) and not (processes.text or '').strip(), 'GPU not empty')


def finite_nonnegative(value):
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def bind():
    require(digest(ROOT / 'plan.json') == read(ROOT / 'plan.sha256.json')['sha256'] == PLAN_SHA, 'plan changed')
    bridge = load(DRIVER, DRIVER_SHA, 'record_write_collection_driver')
    root, plan, diagnostic, _, trainer = bridge.checked_plan(ROOT, PLAN_SHA)
    require(root == ROOT and plan['source_root'] == str(SOURCE) and plan['device'] == DEVICE and
        plan['python'] == str(HOME / 'v2/venv/bin/python'), 'wrong source/root/device/python')
    bridge.verify_inputs(plan, diagnostic)
    launch = read(LOGS / 'launch.json')
    require(launch['pid'] == PID and launch['node'] == 3 and launch['device'] == DEVICE and
        launch['phase'] == 'actual_record_write' and launch['source'] == str(SOURCE) and launch['root'] == str(ROOT) and
        launch['started_utc'] == STARTED and launch['plan_sha256'] == PLAN_SHA and launch['driver_sha256'] == DRIVER_SHA and
        launch['launcher_sha256'] == LAUNCHER_SHA and launch['continuous_reservation'] is True and
        (launch['controller_seconds'], launch['cleanup_reserve'], launch['worker_cap_seconds']) == (1200, 140, 600),
        'launch identity/bounds changed')
    require(launch['command'] == [plan['python'], '-B', str(DRIVER), 'write', '--root', str(ROOT),
        '--plan-sha256', PLAN_SHA, '--allow-gpu'], 'launch command changed')
    check_uuid(launch['gpu'], common.read_bytes(LOGS / 'gpu.xml'))
    return bridge, plan, diagnostic, trainer


def audit(bridge, plan, diagnostic, trainer):
    run = ROOT / 'run'
    result = read(run / 'result.json') if (run / 'result.json').is_file() else None
    failure = read(run / 'failure.json') if (run / 'failure.json').is_file() else None
    require((result is None) != (failure is None), 'exactly one terminal result/failure required')
    successful, terminal = result is not None, result if result is not None else failure
    require(terminal['status'] in (('PAIRED_ADAPTERS_SAVED_READOUT_PENDING',) if successful else ('PARTIAL_FAILED', 'FAILED')) and
        terminal['readout'] == ('PENDING_SEPARATE_OFF_P_ON_A_ON' if successful else 'NOT_RUN') and
        finite_nonnegative(terminal['controller_seconds']), 'terminal status/cost differs')
    if not successful:
        require(terminal['retry'] is False, 'failure retry contract changed')
    controller = read(run / 'controller.json')
    require(controller['plan_sha256'] == PLAN_SHA and controller['worker_seconds'] == 600 and controller['cleanup_reserve'] == 140 and
        finite_nonnegative(controller['started_wall']) and controller['hard_end'] ==
        min(controller['started_wall'] + 1200, plan['deadline'], plan['lease_cutoff']), 'controller allocation changed')
    controller_within_bound = terminal['controller_seconds'] <= 1200 and (
        controller['started_wall'] + terminal['controller_seconds'] <= controller['hard_end'] + .001)
    require(not successful or controller_within_bound, 'successful controller exceeded inclusive bound')
    completed = terminal['arms'] if successful else terminal['completed']
    require(set(completed) in (set(), {'P'}, {'P', 'A'}) and (not successful or set(completed) == set(ARMS)),
            'paired completion/order differs')
    reports, receipts = {}, {}
    for arm in ARMS:
        fit, stage = ROOT / 'fits' / arm, run / arm
        missing = [str(path.relative_to(ROOT)) for path in (stage / 'process.json', stage / 'supervision.json',
            fit / 'attempt.json', fit / 'manifest.json', fit / 'receipt.json', fit / 'adapter/DONE') if not path.is_file()]
        report = reports[arm] = dict(verified_saved_adapter=False, controller_completed=arm in completed, missing=missing, fit=None)
        if missing and (fit / 'adapter').is_dir():
            report['partial_adapter_files'] = diagnostic.tree_hashes(fit / 'adapter')
        process = read(stage / 'process.json') if (stage / 'process.json').is_file() else None
        receipt = read(stage / 'supervision.json') if (stage / 'supervision.json').is_file() else None
        if receipt is not None:
            receipts[arm] = receipt
            require(receipt['device'] == DEVICE and finite_nonnegative(receipt['reserved_seconds']), 'worker receipt identity/cost differs')
        if process is not None:
            launch = read(run / (arm + '.launch.json'))
            require(launch['plan_sha256'] == PLAN_SHA and launch['hard_end'] == controller['hard_end'] and
                process['argv'] == [plan['python'], '-B', str(DRIVER), '_worker', '--root', str(ROOT), '--arm', arm,
                    '--plan-sha256', PLAN_SHA, '--launch-token', launch['token'], '--allow-gpu'] and
                process['device'] == DEVICE and type(process['pid']) is int and process['pid'] > 0 and process['pgid'] == process['pid'] and
                finite_nonnegative(process['started']) and 0 < process['timeout'] <= 600, 'worker ownership/launch/bounds differ')
        try:
            require(not missing, 'incomplete fit/worker evidence')
            require(all(receipt.get(key) is True for key in ('ok', 'reservation_release_verified', 'owned_group_empty', 'gpu_processes_absent'))
                and receipt['returncode'] == 0 and receipt['error'] is None, 'worker success/cleanup failed')
            require(read(fit / 'attempt.json') == dict(arm=arm, plan_sha256=PLAN_SHA, init_adapter=None, pid=process['pid']),
                    'fit attempt/worker identity differs')
            require(read(fit / 'manifest.json')['files'] == diagnostic.tree_hashes(fit, ('manifest.json',)), 'fit manifest changed')
            validated = bridge.validate_fit(ROOT, arm, plan, diagnostic, trainer)
            require(validated == read(fit / 'receipt.json') and validated['steps'] == 12 and
                validated['adapter'] == str(fit / 'adapter'), 'saved fit receipt changed')
            if arm in completed:
                require(completed[arm] == dict(validated, fit_manifest_sha256=digest(fit / 'manifest.json'),
                    supervision_sha256=digest(stage / 'supervision.json')), 'controller/worker fit custody differs')
            report.update(verified_saved_adapter=True, fit=validated)
        except (ValueError, OSError, KeyError, TypeError) as error:
            report['error'] = f'{type(error).__name__}: {error}'
            require(not successful, 'successful pair audit rejected: ' + report['error'])
    expected = {run / arm / 'supervision.json' for arm in receipts}
    require(set(ROOT.glob('**/supervision.json')) == expected, 'unexpected supervision outside paired write')
    return dict(status=terminal['status'], write_success=successful, readout_success=None, readout='NOT_COLLECTED_OR_RUN',
        controller=controller, terminal=terminal, arms=reports, supervision=receipts,
        controller_within_bound=controller_within_bound, controller_seconds=terminal['controller_seconds'],
        observed_worker_seconds=sum(row['reserved_seconds'] for row in receipts.values()) if receipts else None,
        worker_cost_complete=all(arm in receipts for arm in ARMS), semantic_no_answer_certification=False)


def collect(started, monotonic):
    observed = status()
    require(not observed['controller_present'] and (observed['markers']['result.json'] or observed['markers']['failure.json']),
            'wait for absent controller AND terminal result/failure; no retry')
    validation_path = Path(str(ARCHIVE) + '.validation.json')
    prefix = ROOT.parent.relative_to(HOME).as_posix() + '/'
    if ARCHIVE.exists() or validation_path.exists():
        require(ARCHIVE.is_file() and validation_path.is_file(), 'partial capsule preserved; no overwrite')
        validation = read(validation_path)
        require(validation['collector_sha256'] == digest(__file__) and validation['plan_sha256'] == PLAN_SHA and
            validation['sha256'] == digest(ARCHIVE) and validation['files'] == metadata(), 'existing capsule/evidence changed')
        with ARCHIVE.open('rb') as stream:
            common.validate_archive(stream, validation['files'], prefix)
        require(not controller_present(), 'controller present after verification')
        return dict(status='ALREADY_COLLECTED_VERIFIED_NO_WRITES', sha256=validation['sha256'])
    release_json, release_xml = ROOT / 'run/main_release.json', ROOT / 'run/main_release.xml'
    require(not release_json.exists() and not release_xml.exists(), 'partial release preserved; manual reconciliation, no retry')
    before = metadata()
    bridge, plan, diagnostic, trainer = bind()
    report = audit(bridge, plan, diagnostic, trainer)
    require('CUDA_VISIBLE_DEVICES' not in os.environ, 'use env -u CUDA_VISIBLE_DEVICES')
    checker = load(SOURCE / 'gpu/astra_mini_sudoku_diagnostic.py', CHECK_SHA, 'record_write_collection_full_release')
    gpu, xml = checker.check_free(DEVICE)
    check_uuid(gpu, xml)
    released = time.time()
    require(not controller_present() and metadata() == before and
        bridge.implementation(SOURCE, diagnostic) == plan['implementation'], 'evidence/source/controller changed')
    full_seconds = released - dt.datetime.fromisoformat(STARTED).timestamp()
    require(finite_nonnegative(full_seconds), 'invalid launch-to-release time')
    common.write_new(release_xml, xml.encode())
    common.write_json(release_json, dict(full_release=True, controller_absent=True, controller_pid=PID, device=DEVICE, gpu=gpu,
        release_utc=dt.datetime.fromtimestamp(released, dt.timezone.utc).isoformat(), full_reservation_seconds=full_seconds,
        plan_sha256=PLAN_SHA, launch_sha256=digest(LOGS / 'launch.json'), xml_sha256=digest(release_xml), collector_sha256=digest(__file__),
        terminal_sha256=digest(ROOT / 'run' / ('result.json' if report['write_success'] else 'failure.json')),
        status=report['status'], controller_seconds=report['controller_seconds'], observed_worker_seconds=report['observed_worker_seconds'],
        worker_cost_complete=report['worker_cost_complete'], collection_started=started, collection_seconds_at_release=time.monotonic() - monotonic,
        bounds=dict(controller=1200, worker=600, cleanup_reserve=140),
        accounting='Full launch-to-observed-vacancy interval including CPU/gaps/cleanup/wait-to-collect; worker/controller intervals are subsets, not additive. Readout NOT validated.'))
    files = metadata()
    with ARCHIVE.open('xb') as stream, tarfile.open(fileobj=stream, mode='w:gz', format=tarfile.USTAR_FORMAT) as archive:
        for name, checksum in files.items():
            payload = common.read_bytes(HOME / name)
            require(hashlib.sha256(payload).hexdigest() == checksum, 'metadata changed while packing')
            member = tarfile.TarInfo(name)
            member.size, member.mode = len(payload), 0o600
            archive.addfile(member, io.BytesIO(payload))
    with ARCHIVE.open('rb') as stream:
        common.validate_archive(stream, files, prefix)
    require(not controller_present() and metadata() == files, 'evidence/controller changed after packaging')
    archive_sha, elapsed = digest(ARCHIVE), time.monotonic() - monotonic
    require(elapsed <= 300, 'collection exceeded margin; preserve partial evidence')
    common.write_json(validation_path, dict(archive=str(ARCHIVE), sha256=archive_sha, files=files, audit=report,
        plan_sha256=PLAN_SHA, collector_sha256=digest(__file__), full_reservation_seconds=full_seconds,
        collection_seconds=elapsed, collection_completed_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
        excluded_suffixes=sorted(common.EXCLUDED), excluded_directories=['__pycache__'],
        weights='Native fit/adapter inventories and safetensors structure validated; weight bytes retained native, excluded from archive.',
        scope='Actual-record write custody and release only; NOT readout success, transfer, model-origin authentication, or semantic judgment.'))
    return dict(status='COLLECTED', write_status=report['status'], sha256=archive_sha, files=len(files), collection_seconds=elapsed)


class CollectionExpired(BaseException):
    pass


def expired(number, frame):
    raise CollectionExpired('300-second collector limit; preserve partial evidence, no retry')


def finish():
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
