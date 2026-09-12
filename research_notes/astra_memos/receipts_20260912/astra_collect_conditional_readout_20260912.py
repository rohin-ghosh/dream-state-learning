"""Root0 terminal metadata collection only; Main executes status/finish natively."""
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
ROOT = HOME / 'astra_diagnostics/astra_conditional_behavior_20260912_attempt2/readouts_root0_attempt1'
SOURCE = HOME / 'astra_sources/90e181a4b0a02cfe655bc76ba480eac9166222b4'
DRIVER = Path('/tmp/astra_conditional_readout_run_20260912.py')
ARCHIVE = Path('/tmp/astra_conditional_readout_root0_terminal_20260912.tgz')
MANIFEST_SHA = '5a26f0da17d53518aa00c80bce3bfbfbe76ef61e65ea5ebc781f797dd33190a6'
DRIVER_SHA = 'e7a42bf3644d6e4ce5fbd1f129b37008cc455ea2088d3f65dbc18d27bd1ccd74'
HELPER_SHA = 'd2152c179ca9a6b9801933a480ed62cd203018868a52034e13676963787579eb'
CHECK_SHA = 'a586b03bdb9c52f1061aa1e477ae983cc9d45ec0a2cd440642851fd8df8b609f'
READOUT_SHA = 'b4cd06137e3743186b885a809e1f2d3316fffd420a75c8c24838d6df72fa80df'
UUID = 'GPU-0ee6f753-c61e-e18a-8aea-acccd3042939'
STARTED = '2026-09-12T20:41:19.619663+00:00'
PID, DEVICE = 220273, '0'
ORDER = tuple(state + '_' + phase for state in ('OFF', 'AUTH', 'DERANGED') for phase in ('generate', 'score'))
COST_KEYS = ('requests', 'native_input_tokens', 'native_output_tokens', 'output_token_ceiling',
             'candidate_forwards', 'scored_target_tokens', 'padded_forward_tokens', 'call_seconds')


class CollectionExpired(BaseException):
    pass


def expired(number, frame):
    raise CollectionExpired('collection margin exhausted; preserve partial evidence, no retry')


def load(path, checksum, name):
    payload = path.read_bytes()
    if hashlib.sha256(payload).hexdigest() != checksum:
        raise ValueError('dependency changed: ' + str(path))
    module = importlib.util.module_from_spec(importlib.util.spec_from_file_location(name, path))
    exec(compile(payload, str(path), 'exec'), module.__dict__)
    return module


common = load(Path('/tmp/astra_collect_memory_only_20260912.py'), HELPER_SHA, 'readout_collection_common')
require, read, digest = common.require, common.read, common.digest


def controller_present():
    return Path(f'/proc/{PID}').exists()


def status():
    markers = ('plan.json', 'run/worker/process.json', 'run/worker/supervision.json',
               'run/data/manifest.json', 'run/data/failure.json', 'run/data/backend.cleanup.json')
    return dict(pid=PID, device=DEVICE, controller_present=controller_present(),
        terminal_available=(ROOT / 'controller/terminal.json').is_file(),
        summary_available=(ROOT / 'controller/summary.json').is_file(), scoring='NONE',
        phases={name: {marker: (ROOT / name / marker).is_file() for marker in markers} for name in ORDER})


def check_uuid(gpu, xml):
    devices = ET.fromstring(xml).findall('gpu')
    require(gpu['gpu_uuid'] == UUID and len(devices) == 1 and devices[0].findtext('uuid') == UUID,
            'GPU UUID differs from launch')
    processes = devices[0].find('processes')
    require(processes is not None and not list(processes) and not (processes.text or '').strip(), 'GPU not empty')


def same_cost(actual, expected):
    require(set(actual) == set(expected) == set(COST_KEYS), 'cost keys differ')
    require(all(type(actual[key]) in (int, float) and math.isfinite(actual[key]) and actual[key] >= 0 and
        math.isclose(actual[key], expected[key], rel_tol=0, abs_tol=1e-6 if key == 'call_seconds' else 0)
        for key in COST_KEYS), 'raw/stored cost mismatch')


def capture(plan, api, data):
    require(not (data / 'failure.json').exists() and read(data / 'backend.cleanup.json')['closed'] is True,
            'capture failure/cleanup missing')
    require(read(data / 'manifest.json')['files'] == common.capture_files(data), 'raw capture hashes differ')
    require(read(data / 'identity.json') == dict(backend=plan['identity'], model_files=plan['model_files'],
        adapter_files=plan['adapter_files']), 'capture identity differs')
    require({entry.name for entry in (data / 'calls').iterdir()} ==
        {row['call_id'] + suffix for row in plan['requests'] for suffix in ('.request.json', '.response.json')},
        'missing/extra raw pairs')
    cost, last_ended = dict.fromkeys(COST_KEYS, 0), 0.0
    for index, request in enumerate(plan['requests']):
        stem = data / 'calls' / request['call_id']
        sent, received = read(str(stem) + '.request.json'), read(str(stem) + '.response.json')
        response = received['response']
        require(sent['request'] == request and sent['identity'] == plan['identity'] and
            sent['prompt_sha256'] == api.base.value_hash(request['prompt']) and
            received['response_sha256'] == api.base.value_hash(response), 'raw identity/request/response seal differs')
        require(math.isfinite(sent['started']) and math.isfinite(received['ended']) and
            last_ended <= sent['started'] <= received['ended'], 'invalid raw call timing')
        last_ended = received['ended']
        cost['requests'] += 1
        cost['call_seconds'] += received['ended'] - sent['started']
        if plan['phase'] == 'generate':
            api.base.validate_response(request, response)
            require(all(response[key] == plan['native_inputs'][index][key] for key in
                ('rendered_prompt', 'prompt_token_ids')), 'prepared causal input differs')
            cost['native_input_tokens'] += len(response['prompt_token_ids'])
            cost['native_output_tokens'] += len(response['output_token_ids'])
            cost['output_token_ceiling'] += request['max_tokens']
        else:
            api.validate_scores(request, response)
            cost['candidate_forwards'] += len(request['candidates'])
            cost['scored_target_tokens'] += sum(len(row['response_ids']) for row in request['candidates'])
            cost['native_input_tokens'] += sum(len(row['input_ids']) for row in request['candidates'])
            cost['padded_forward_tokens'] += sum(2 * max(len(row['input_ids']) for row in group)
                                                for group in api.scoring_groups(request))
    if plan['phase'] == 'generate':
        require(api.base.usage(data) == read(data / 'usage.json'), 'generation usage receipt changed')
    return cost


def inventories(record, plans, api):
    require(api.sources() == record['source_hashes'] and api.ASSAY_VERSION == record['assay_version'], 'source/assay changed')
    material = api.read_material(plans[0]['material'])
    require(material['inventory'] == record['material_inventory'] and
        material['manifest_sha256'] == plans[0]['material_manifest_sha256'] and
        api.corpus.digest(material['candidate']) == plans[0]['candidate_sha256'], 'material changed')
    require(api.base.model_hashes(plans[0]['model']) == record['model_files'], 'base inventory changed')
    shared = ('device', 'model', 'model_files', 'material', 'material_inventory', 'material_manifest_sha256',
              'candidate_sha256', 'source_hashes', 'controls', 'worker_seconds', 'resource_budget', 'lease_end')
    require(all(all(plan[key] == plans[0][key] for key in shared) for plan in plans), 'shared contract differs')
    for index in (0, 2, 4):
        plan, score = plans[index:index + 2]
        require(all(plan[key] == score[key] for key in ('adapter', 'adapter_files')), 'state adapter differs across panels')
        require(api.fit_contract(plan['adapter'], plan['state'], plan['model'], material) == plan['adapter_files'],
                'current adapter differs')
    require(plans[0]['adapter'] is None and plans[0]['adapter_files'] == {} and
        plans[2]['adapter'] != plans[4]['adapter'], 'OFF/fit states differ')
    for row, plan in zip(record['phases'], plans):
        require((plan['state'], plan['phase']) == (row['state'], row['phase']) and plan['device'] == DEVICE and
            all(plan[key] == record[key] for key in ('model_files', 'source_hashes', 'material_inventory')), 'phase identity differs')
        identity = api.base.expected_identity(plan, plan['adapter']) if plan['phase'] == 'generate' else dict(
            backend='hf_complete_candidate', model_input=plan['model'], adapter_input=plan['adapter'], adapter_files=plan['adapter_files'])
        require(plan['identity'] == identity, 'sealed backend identity differs')


def audit(record, terminal, driver, api):
    plans = [read(Path(row['root']) / 'plan.json') for row in record['phases']]
    inventories(record, plans, api)
    require(all(terminal[key] == value for key, value in read(ROOT / 'controller/reservation.json').items()) and
        terminal['controller_pid'] == PID and terminal['device'] == DEVICE and terminal['manifest_sha256'] == MANIFEST_SHA and
        terminal['driver_sha256'] == DRIVER_SHA and terminal['status'] in ('COMPLETE', 'PARTIAL') and
        terminal['retries'] == 0 and terminal['counts_used_for_queue_selection'] is False, 'terminal custody differs')
    require(all(math.isfinite(terminal[key]) and terminal[key] >= 0 for key in
        ('started', 'ended', 'reserved_seconds', 'worker_reserved_seconds')) and terminal['ended'] >= terminal['started'] and
        terminal['controller_seconds'] == 4500 and terminal['cleanup_reserve_seconds'] == 140 and
        terminal['external_collection_margin_seconds'] == 300 and terminal['total_ceiling_seconds'] == 5400 and
        terminal['prior_fit_full_reservation_seconds'] == record['prior_fit_full_reservation_seconds'] == 464.397178,
        'terminal cost/allocation invalid')
    attempts = terminal['attempts']
    require([row['name'] for row in attempts] == list(ORDER[:len(attempts)]) and len(attempts) <= 6, 'attempt order differs')
    reports, receipts, reductions = {}, {}, []
    for index, (row, plan) in enumerate(zip(record['phases'], plans)):
        name, root = ORDER[index], Path(row['root'])
        report = reports[name] = dict(complete=False, missing=[], cost=None)
        for marker in ('run/worker/process.json', 'run/worker/supervision.json', 'run/data/manifest.json',
                       'run/data/identity.json', 'run/data/backend.ready.json', 'run/data/backend.cleanup.json'):
            if not (root / marker).is_file():
                report['missing'].append(marker)
        try:
            receipt_path = root / 'run/worker/supervision.json'
            if receipt_path.is_file():
                receipt = receipts[name] = read(receipt_path)
                require(receipt == terminal['supervision'][name], 'terminal/stored receipt differs')
            require(index < len(attempts), 'phase not attempted')
            attempt = attempts[index]
            require(attempt == read(ROOT / 'controller/phases' / (name + '.json')) and
                attempt['root'] == str(root) and attempt['plan_sha256'] == row['plan_sha256'], 'phase attempt differs')
            require(not report['missing'], 'required phase evidence missing')
            process = read(root / 'run/worker/process.json')
            require(process == attempt['process'] and process['device'] == DEVICE and process['pgid'] == process['pid'] and
                process['argv'] == [str(HOME / 'v2/venv/bin/python'), '-B', '-m', 'organism_v6.conditional_behavior_readout',
                                    '_worker', '--root', str(root), '--allow-gpu'] and
                0 < process['timeout'] <= 600, 'worker ownership/command/bounds differ')
            driver.successful(receipt, DEVICE)
            require(receipt == attempt['supervision'], 'attempt supervision differs')
            reduction = attempt['reduction']
            require(reduction['complete'] is True and reduction['status'] == 'COMPLETE_PHASE' and
                reduction['root'] == str(root) and reduction['state'] == row['state'] and reduction['phase'] == row['phase'] and
                reduction['plan_sha256'] == row['plan_sha256'] and reduction['reserved_seconds'] == receipt['reserved_seconds'] and
                all(reduction[key] == plan[key] for key in ('material_inventory', 'source_hashes', 'model_files',
                                                          'adapter_files', 'assay_version', 'resource_budget')), 'reduction custody differs')
            cost = capture(plan, api, root / 'run/data')
            same_cost(cost, reduction['cost'])
            report.update(complete=True, cost=cost)
            reductions.append(reduction)
        except (ValueError, KeyError, TypeError, OSError) as failure:
            report['error'] = f'{type(failure).__name__}: {failure}'
    require(math.isclose(sum(row['reserved_seconds'] for row in terminal['supervision'].values()),
        terminal['worker_reserved_seconds'], rel_tol=0, abs_tol=1e-6), 'terminal worker cost differs')
    if terminal['status'] == 'COMPLETE':
        require(receipts == terminal['supervision'], 'terminal worker receipt set differs')
    summary_path = ROOT / 'controller/summary.json'
    summary = read(summary_path) if summary_path.is_file() else None
    require(summary == terminal['summary'], 'summary/terminal differs')
    if summary is not None:
        require(len(reductions) == 6 and summary['complete'] is True and summary['reductions'] == reductions and
            (summary['actual_generation_calls'], summary['actual_scoring_requests'], summary['candidate_forwards']) == (672, 192, 576),
            'summary incomplete or reduction/workload identity differs')
        same_cost({key: sum(row['cost'][key] for row in reductions) for key in COST_KEYS}, summary['cost'])
        require(math.isclose(summary['readout_reserved_seconds'], terminal['worker_reserved_seconds'], rel_tol=0, abs_tol=1e-6),
                'summary worker reservation differs')
    if terminal['status'] == 'COMPLETE':
        require(len(reductions) == terminal['completed_phases'] == 6 and summary is not None and
            terminal['release_verified'] is True and not terminal['unaccounted_processes'] and terminal['error'] is None and
            terminal['deadline_met'] is True and 0 <= terminal['reserved_seconds'] <= 4500, 'COMPLETE technical evidence incomplete')
    return reports


def collect():
    require(not controller_present() and (ROOT / 'controller/terminal.json').is_file(), 'wait for controller absence AND terminal')
    started, monotonic = time.time(), time.monotonic()
    validation_path = Path(str(ARCHIVE) + '.validation.json')
    prefix = ROOT.relative_to(HOME).as_posix() + '/'
    if ARCHIVE.exists() or validation_path.exists():
        require(ARCHIVE.is_file() and validation_path.is_file(), 'partial capsule preserved; no retry/overwrite')
        validation = read(validation_path)
        require(digest(ARCHIVE) == validation['sha256'] and validation['collector_sha256'] == digest(__file__) and
            validation['manifest_sha256'] == MANIFEST_SHA and common.metadata(ROOT, HOME) == validation['files'], 'saved capsule/evidence changed')
        with ARCHIVE.open('rb') as stream:
            common.validate_archive(stream, validation['files'], prefix)
        return dict(status='ALREADY_COLLECTED_VERIFIED_NO_WRITES', sha256=validation['sha256'])
    stage = ROOT / 'controller'
    release_json, release_xml = stage / 'main_release.json', stage / 'main_release.xml'
    require(not release_json.exists() and not release_xml.exists(), 'partial release preserved; manual reconciliation, no retry')
    deadline = min(started + 300, dt.datetime.fromisoformat(STARTED).timestamp() + 4500 + 300)

    require(deadline > time.time(), 'collection allocation already expired; no silent extension')
    handler = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, deadline - time.time())
    try:
        driver = load(DRIVER, DRIVER_SHA, 'readout_collection_driver')
        record = driver.manifest(SOURCE, ROOT, MANIFEST_SHA, DRIVER_SHA)
        require(digest(SOURCE / 'organism_v6/conditional_behavior_readout.py') == READOUT_SHA, 'readout pin changed')
        launch, terminal = read(ROOT / 'launch/launch.json'), read(stage / 'terminal.json')
        require(launch['pid'] == PID and launch['device'] == DEVICE and launch['node'] == 3 and launch['seed'] == 0 and
            launch['source'] == str(SOURCE) and launch['started_utc'] == STARTED and launch['manifest_sha256'] == MANIFEST_SHA and
            launch['driver_sha256'] == DRIVER_SHA and launch['phase_order'] == list(ORDER) and
            launch['continuous_reservation'] is True and launch['gpu']['gpu_uuid'] == UUID, 'launch binding differs')
        require(launch['command'] == [str(HOME / 'v2/venv/bin/python'), '-B', str(DRIVER), 'run', '--source-root', str(SOURCE),
            '--runroot', str(ROOT), '--manifest-sha256', MANIFEST_SHA, '--driver-sha256', DRIVER_SHA,
            '--deadline', '1789250239.6182988', '--lease-end', '1790391780.0', '--allow-gpu'], 'launch command differs')
        before = common.metadata(ROOT, HOME)
        reports = audit(record, terminal, driver, driver.import_api(SOURCE))
        require('CUDA_VISIBLE_DEVICES' not in os.environ, 'run collector with env -u CUDA_VISIBLE_DEVICES')
        checker = load(SOURCE / 'gpu/astra_mini_sudoku_diagnostic.py', CHECK_SHA, 'readout_collection_full_release')
        gpu, xml = checker.check_free(DEVICE)
        check_uuid(gpu, xml)
        released = time.time()
        require(not controller_present() and common.metadata(ROOT, HOME) == before, 'evidence/controller changed during audit')
        common.write_new(release_xml, xml.encode())
        common.write_json(release_json, dict(full_release=True, controller_absent=True, controller_pid=PID, device=DEVICE,
            gpu=gpu, release_utc=dt.datetime.fromtimestamp(released, dt.timezone.utc).isoformat(),
            full_reservation_seconds=released - dt.datetime.fromisoformat(STARTED).timestamp(),
            controller_reserved_seconds=terminal['reserved_seconds'], worker_reserved_seconds=terminal['worker_reserved_seconds'],
            terminal_status=terminal['status'], manifest_sha256=MANIFEST_SHA, launch_sha256=digest(ROOT / 'launch/launch.json'),
            terminal_sha256=digest(stage / 'terminal.json'), xml_sha256=digest(release_xml), collector_sha256=digest(__file__),
            collector_started=started, collection_seconds_at_release=time.monotonic() - monotonic,
            note='Vacancy observation, not packaging completion; controller/worker times are subsets, not additive'))
        files = common.metadata(ROOT, HOME)
        with ARCHIVE.open('xb') as stream, tarfile.open(fileobj=stream, mode='w:gz', format=tarfile.USTAR_FORMAT) as archive:
            for name, checksum in files.items():
                payload = common.read_bytes(HOME / name)
                require(hashlib.sha256(payload).hexdigest() == checksum, 'metadata changed while packing')
                member = tarfile.TarInfo(name)
                member.size, member.mode = len(payload), 0o600
                archive.addfile(member, io.BytesIO(payload))
        with ARCHIVE.open('rb') as stream:
            common.validate_archive(stream, files, prefix)
        require(not controller_present() and common.metadata(ROOT, HOME) == files, 'evidence/controller changed after packing')
        archive_sha = digest(ARCHIVE)
        completed, elapsed = time.time(), time.monotonic() - monotonic
        require(completed <= deadline and elapsed <= 300, 'collection exceeded reserved margin')
        common.write_json(validation_path, dict(archive=str(ARCHIVE), sha256=archive_sha, files=files, audits=reports,
            manifest_sha256=MANIFEST_SHA, collector_sha256=digest(__file__), terminal_status=terminal['status'],
            technical_complete=terminal['status'] == 'COMPLETE', collection_seconds=elapsed,
            collection_completed_utc=dt.datetime.fromtimestamp(completed, dt.timezone.utc).isoformat(),
            terminal_to_collection_seconds=completed - terminal['ended'], postterminal_margin_met=completed - terminal['ended'] <= 300,
            prior_fit_full_reservation_seconds=record['prior_fit_full_reservation_seconds'],
            launch_to_collection_seconds=completed - dt.datetime.fromisoformat(STARTED).timestamp(),
            conservative_total_seconds=record['prior_fit_full_reservation_seconds'] + completed - dt.datetime.fromisoformat(STARTED).timestamp(),
            excluded_suffixes=sorted(common.EXCLUDED), excluded_directories=['__pycache__'],
            scope='Hash/identity/receipt and resource-count audit; no tokenizer, reducer, scientific rescoring, or L1 verdict',
            authorship='Collector author also authored controller; not fresh-author independent review',
            weights='Retained native, current base once and each distinct adapter once; excluded from capsule'))
        return dict(status='COLLECTED', terminal_status=terminal['status'], sha256=archive_sha, files=len(files), collection_seconds=elapsed)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, handler)


def finish():
    handler = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, 300)
    try:
        return collect()
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, handler)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=('status', 'finish'))
    args = parser.parse_args()
    print(json.dumps(status() if args.stage == 'status' else finish(), indent=2, sort_keys=True, allow_nan=False), flush=True)
