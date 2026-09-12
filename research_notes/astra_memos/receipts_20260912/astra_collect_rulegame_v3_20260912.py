"""Formation-only root0 metadata collector. Main executes; no semantic promotion."""
import argparse
import datetime as dt
import hashlib
import importlib
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
ROOT = HOME / 'astra_diagnostics/astra_rulegame_interaction_v3_20260912_attempt1'
LOGS = ROOT.with_name(ROOT.name + '_formation_launch')
SOURCE = HOME / 'astra_sources/610c6edd05ce9c85720ee6e992889badecc2c158'
ARCHIVE = Path('/tmp/astra_rulegame_v3_formation_terminal_20260912.tgz')
PLAN_SHA = '7dae3ca492ed39545987ab8deb5f39631a40332d480ddb99292e5f083741c468'
SOURCE_SHA = 'e6055da48b2c6fa1bd294c9d991e07f32f05dc6630fe8973373977bdfe977526'
LAUNCHER_SHA = '9b37905d6fb7271aac14e7630269e6767378bd6de8a19217ab49a78897fa1cb3'
HELPER_SHA = 'd2152c179ca9a6b9801933a480ed62cd203018868a52034e13676963787579eb'
CHECK_SHA = 'a586b03bdb9c52f1061aa1e477ae983cc9d45ec0a2cd440642851fd8df8b609f'
STARTED = '2026-09-12T21:12:06.864318+00:00'
UUID = 'GPU-41a86250-88eb-ed8a-ddfe-9d6f93515da1'
PID, DEVICE = 228661, '2'
MARKERS = ('result.json', 'failure.json', 'worker/process.json', 'worker/supervision.json',
           'data/manifest.json', 'data/failure.json', 'data/backend.cleanup.json', 'provenance.json')


def load(path, pin, name):
    payload = path.read_bytes()
    if hashlib.sha256(payload).hexdigest() != pin:
        raise ValueError('dependency changed: ' + str(path))
    module = importlib.util.module_from_spec(importlib.util.spec_from_file_location(name, path))
    exec(compile(payload, str(path), 'exec'), module.__dict__)
    return module


common = load(Path('/tmp/astra_collect_memory_only_20260912.py'), HELPER_SHA, 'rulegame_collection_common')
require, read, digest = common.require, common.read, common.digest


def controller_present():
    return Path(f'/proc/{PID}').exists()


def status():
    return dict(pid=PID, device=DEVICE, controller_present=controller_present(),
        markers={name: (ROOT / 'formation' / name).is_file() for name in MARKERS},
        launch_available=(LOGS / 'launch.json').is_file(), scoring='NONE')


def metadata():
    root_files, log_files = common.metadata(ROOT, HOME), common.metadata(LOGS, HOME)
    require(not root_files.keys() & log_files.keys(), 'root/launch inventory collision')
    return dict(sorted({**root_files, **log_files}.items()))


def check_uuid(gpu, xml):
    devices = ET.fromstring(xml).findall('gpu')
    require(gpu['gpu_uuid'] == UUID and len(devices) == 1 and devices[0].findtext('uuid') == UUID, 'launch GPU UUID mismatch')
    processes = devices[0].find('processes')
    require(processes is not None and not list(processes) and not (processes.text or '').strip(), 'GPU not empty')


def bind():
    require(digest(ROOT / 'plan.json') == read(ROOT / 'plan.sha256.json')['sha256'] == PLAN_SHA, 'plan pin changed')
    require(digest(SOURCE / 'organism_v6/rulegame_parenting_diagnostic.py') == SOURCE_SHA, 'source pin changed')
    sys.path.insert(0, str(SOURCE))
    api = importlib.import_module('organism_v6.rulegame_parenting_diagnostic')
    require(api.REPO == SOURCE and Path(api.__file__).resolve() == SOURCE / 'organism_v6/rulegame_parenting_diagnostic.py', 'wrong imported source')
    plan = api.verify_plan(ROOT)
    require(plan['protocol'] == 'interaction_v3' and plan['device'] == DEVICE and
        (api.WORKER_SECONDS, api.RESERVED_SECONDS) == (600, 1800), 'protocol/device/worker bounds changed')
    launch, native = read(LOGS / 'launch.json'), read(ROOT / 'native_preparation.json')
    require(launch['pid'] == PID and launch['node'] == 3 and launch['device'] == DEVICE and launch['phase'] == 'formation' and
        launch['source'] == str(SOURCE) and launch['root'] == str(ROOT) and launch['started_utc'] == STARTED and
        launch['plan_sha256'] == PLAN_SHA and launch['launcher_sha256'] == LAUNCHER_SHA and
        launch['worker_cap_seconds'] == 600 and launch['aggregate_worker_cap_seconds'] == 1800 and
        launch['continuous_reservation_within_phase'] is True and launch['no_automatic_write_or_readout'] is True,
        'launch binding changed')
    require(launch['command'] == [str(HOME / 'v2/venv/bin/python'), '-B', '-m', 'organism_v6.rulegame_parenting_diagnostic',
        'formation', '--root', str(ROOT), '--allow-gpu'], 'launch command differs')
    require(launch['native_preparation_sha256'] == digest(ROOT / 'native_preparation.json') and
        native['status'] == 'NATIVE_RULEGAME_V3_FORMATION_PREPARATION_PASS' and native['plan_sha256'] == PLAN_SHA and
        native['root'] == str(ROOT) and native['source'] == str(SOURCE) and native['source_hashes'] == plan['source_hashes'],
        'native preparation changed')
    check_uuid(launch['gpu'], common.read_bytes(LOGS / 'gpu.xml'))
    require(not any((ROOT / name).exists() for name in ('material', 'write', 'evaluation')), 'scope is formation only')
    return api, plan, launch


def audit(api, plan):
    stage, data = ROOT / 'formation', ROOT / 'formation/data'
    failures = {name: read(stage / name) for name in ('failure.json', 'data/failure.json') if (stage / name).is_file()}
    successful = (stage / 'result.json').is_file() and not failures
    missing = [name for name in ('result.json', 'worker/process.json', 'worker/supervision.json', 'data/manifest.json',
        'data/identity.json', 'data/backend.ready.json', 'data/backend.cleanup.json', 'provenance.json', 'main_audit.template.json')
        if not (stage / name).is_file()]
    process = read(stage / 'worker/process.json') if (stage / 'worker/process.json').is_file() else None
    receipt = read(stage / 'worker/supervision.json') if (stage / 'worker/supervision.json').is_file() else None
    require(set(ROOT.glob('**/supervision.json')) == ({stage / 'worker/supervision.json'} if receipt is not None else set()),
            'unexpected supervisor outside formation')
    if process is not None:
        require(process['argv'] == [str(HOME / 'v2/venv/bin/python'), '-B', '-m', 'organism_v6.rulegame_parenting_diagnostic',
            '_worker', '--root', str(ROOT), '--stage', 'formation', '--out', str(data), '--allow-gpu'] and
            process['device'] == DEVICE and type(process['pid']) is int and process['pid'] > 0 and
            process['pgid'] == process['pid'] and math.isfinite(process['started']) and process['started'] >= 0 and
            0 < process['timeout'] <= 600, 'worker command/ownership/bounds changed')
    if receipt is not None:
        require(receipt['device'] == DEVICE and math.isfinite(receipt['reserved_seconds']) and receipt['reserved_seconds'] >= 0,
                'supervisor identity/cost invalid')
    report = dict(status='COMPLETE_FORMATION_AWAITING_MAIN_AUDIT' if successful else 'PARTIAL', failures=failures,
        missing=missing, process=process, supervision=receipt, native_token_text_audit=False, world_replay_ok=None, usage=None)
    if successful:
        require(not missing, 'successful formation has missing evidence')
        require(all(receipt.get(key) is True for key in ('ok', 'reservation_release_verified', 'owned_group_empty', 'gpu_processes_absent'))
            and receipt['returncode'] == 0 and receipt['error'] is None, 'successful supervisor/cleanup invalid')
        require(read(stage / 'result.json') == dict(status='AWAITING_MAIN_AUDIT', formation_sha256=digest(data / 'manifest.json')),
                'formation result seal changed')
        header = read(data / 'identity.json')
        require(header['stage'] == 'formation' and header['cell'] is None and header['model_files'] == plan['model_files'],
                'capture state/base identity differs')
        require(read(data / 'backend.cleanup.json')['closed'] is True, 'backend cleanup incomplete')
        replay = api.check_capture(data, api.expected_identity(plan), 'interaction_v3')
        require(replay['ok'] and replay == read(stage / 'provenance.json'), 'world replay/provenance mismatch')
        api.audit_native_calls(api.native_tokenizer(plan['model']), data)
        report.update(native_token_text_audit=True, world_replay_ok=True, usage=read(data / 'usage.json'))
    return report


def collect(started, monotonic):
    observed = status()
    require(not observed['controller_present'] and any(observed['markers'][name] for name in
        ('result.json', 'failure.json', 'data/failure.json')), 'wait for absent controller AND result/failure; otherwise Main reconciles')
    validation_path = Path(str(ARCHIVE) + '.validation.json')
    prefix = ROOT.parent.relative_to(HOME).as_posix() + '/'
    if ARCHIVE.exists() or validation_path.exists():
        require(ARCHIVE.is_file() and validation_path.is_file(), 'partial capsule preserved; no retry/overwrite')
        validation = read(validation_path)
        require(validation['plan_sha256'] == PLAN_SHA and validation['collector_sha256'] == digest(__file__) and
            validation['sha256'] == digest(ARCHIVE) and validation['files'] == metadata(), 'existing evidence/capsule changed')
        with ARCHIVE.open('rb') as stream:
            common.validate_archive(stream, validation['files'], prefix)
        require(not controller_present(), 'controller present after archive check')
        return dict(status='ALREADY_COLLECTED_VERIFIED_NO_WRITES', sha256=validation['sha256'])
    release_json, release_xml = ROOT / 'formation/main_release.json', ROOT / 'formation/main_release.xml'
    require(not release_json.exists() and not release_xml.exists(), 'orphan release preserved; no retry/overwrite')
    before = metadata()
    api, plan, launch = bind()
    report = audit(api, plan)
    require('CUDA_VISIBLE_DEVICES' not in os.environ, 'use env -u CUDA_VISIBLE_DEVICES for collection')
    checker = load(SOURCE / 'gpu/astra_mini_sudoku_diagnostic.py', CHECK_SHA, 'rulegame_collection_full_release')
    gpu, xml = checker.check_free(DEVICE)
    check_uuid(gpu, xml)
    released = time.time()
    require(not controller_present() and metadata() == before and api.sources() == plan['source_hashes'], 'evidence/source/controller changed')
    full_seconds = released - dt.datetime.fromisoformat(STARTED).timestamp()
    require(math.isfinite(full_seconds) and full_seconds >= 0, 'invalid full reservation interval')
    common.write_new(release_xml, xml.encode())
    common.write_json(release_json, dict(full_release=True, controller_absent=True, controller_pid=PID, device=DEVICE,
        release_utc=dt.datetime.fromtimestamp(released, dt.timezone.utc).isoformat(), full_reservation_seconds=full_seconds,
        gpu=gpu, status=report['status'], plan_sha256=PLAN_SHA, launch_sha256=digest(LOGS / 'launch.json'),
        xml_sha256=digest(release_xml), collector_sha256=digest(__file__), collection_started=started,
        collection_seconds_at_release=time.monotonic() - monotonic,
        worker_reserved_seconds=report['supervision']['reserved_seconds'] if report['supervision'] is not None else None,
        worker_cap_seconds=600, legacy_aggregate_worker_cap_seconds=1800, full_controller_cap_seconds=None,
        accounting='Actual launch-to-observed-full-vacancy; includes CPU/gaps/cleanup/wait-to-collect. Worker interval is a subset; 1800 is NOT a controller guarantee.'))
    files = metadata()
    with ARCHIVE.open('xb') as stream, tarfile.open(fileobj=stream, mode='w:gz', format=tarfile.USTAR_FORMAT) as archive:
        for name, checksum in files.items():
            payload = common.read_bytes(HOME / name)
            require(hashlib.sha256(payload).hexdigest() == checksum, 'metadata changed during packaging')
            member = tarfile.TarInfo(name)
            member.size, member.mode = len(payload), 0o600
            archive.addfile(member, io.BytesIO(payload))
    with ARCHIVE.open('rb') as stream:
        common.validate_archive(stream, files, prefix)
    require(metadata() == files and not controller_present(), 'evidence/controller changed after packaging')
    archive_sha = digest(ARCHIVE)
    elapsed = time.monotonic() - monotonic
    require(elapsed <= 300, 'collection exceeded 300-second margin; preserve evidence')
    common.write_json(validation_path, dict(archive=str(ARCHIVE), sha256=archive_sha, files=files, audit=report,
        plan_sha256=PLAN_SHA, collector_sha256=digest(__file__), collection_seconds=elapsed,
        collection_completed_utc=dt.datetime.now(dt.timezone.utc).isoformat(), full_reservation_seconds=full_seconds,
        excluded_suffixes=sorted(common.EXCLUDED), excluded_directories=['__pycache__'],
        scope='Formation raw-call/token/world and technical release audit only; no Main semantic judgment, material, write or evaluation.',
        model_origin='UNRESOLVED_LOCAL_HASHES_ONLY', semantic_no_answer_certification=False, promotion_authorized=False))
    return dict(status='COLLECTED', formation_status=report['status'], sha256=archive_sha, files=len(files), collection_seconds=elapsed)


class CollectionExpired(BaseException):
    pass


def expired(number, frame):
    raise CollectionExpired('300-second collector alarm; preserve partial evidence, no retry')


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
