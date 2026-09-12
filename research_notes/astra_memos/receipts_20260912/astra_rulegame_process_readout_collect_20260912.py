"""Main-only, terminal-only process-v2 readout metadata custody. No model rerun.

status reads launch/process receipts and marker existence only. finish requires
all recorded owned PID/PGID/session scopes absent before opening score bodies.
No kills, retries, overwrites, live metrics, partial aggregates or weight export.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import signal
import stat
import sys
import time
import xml.etree.ElementTree as ET


sys.dont_write_bytecode = True
BASE = Path('/tmp/astra_rulegame_record_acquisition_collect_20260912.py')
BASE_SHA = '422c2fd2efcc2e8c315d6082c05a803353ee8b67f0b31e23eab19fe0119ae951'
DRIVER_SHA = '46e3d0974cab9a3c35e732634a22c29ad25ccd670472dc5b1a57c344cb20af46'
CELLS = ('OFF', 'P_ON', 'A_ON')
COST_KEYS = ('requests', 'native_input_tokens', 'native_output_tokens', 'output_token_ceiling', 'generation_seconds')


def common_module():
    if any(path.is_symlink() for path in (BASE, *BASE.parents)):
        raise ValueError('symlink common source rejected')
    descriptor = os.open(BASE, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or before.st_size > 2*1024*1024:
            raise ValueError('unsafe/oversized common source')
        data = stream.read(2*1024*1024+1)
        after = os.fstat(stream.fileno())
        if len(data) != before.st_size or any(getattr(before, key) != getattr(after, key) or
                getattr(before, key) != getattr(BASE.stat(), key) for key in ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns')):
            raise ValueError('common source changed while reading')
    if hashlib.sha256(data).hexdigest() != BASE_SHA:
        raise ValueError('validated collection helper changed')
    name = 'process_readout_collection_common'
    spec = importlib.util.spec_from_file_location(name, BASE)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(data, str(BASE), 'exec'), module.__dict__)
    return module


common = common_module()
require, read, digest = common.require, common.read, common.digest
write_json, write_new = common.write_json, common.write_new


def settings(values):
    values = dict(values)
    for key in ('root', 'driver', 'write_driver', 'launch_root', 'launcher'):
        values[key] = common.unaliased(values[key])
    if values.get('out') is not None:
        values['out'] = common.unaliased(values['out'])
    for key in ('plan_sha256', 'driver_sha256', 'write_driver_sha256', 'write_plan_sha256', 'launch_sha256', 'launcher_sha256'):
        require(isinstance(values[key], str) and re.fullmatch('[0-9a-f]{64}', values[key]), 'explicit SHA256 required: ' + key)
    require(values['driver_sha256'] == DRIVER_SHA, 'only the accepted process readout is supported')
    require(values['root'].is_dir() and values['launch_root'].is_dir()
            and values['root'].parent == values['launch_root'].parent and values['root'] != values['launch_root'],
            'distinct sibling readout/launch directories required')
    return values


def status(config):
    root, logs = config['root'], config['launch_root']
    require(digest(logs / 'launch.json') == config['launch_sha256'], 'launch pin differs')
    launch = read(logs / 'launch.json')
    require(launch['root'] == str(root) and launch['plan_sha256'] == config['plan_sha256']
            and launch['driver_sha256'] == config['driver_sha256']
            and launch['write_plan_sha256'] == config['write_plan_sha256']
            and ('write_driver_sha256' not in launch or launch['write_driver_sha256'] == config['write_driver_sha256'])
            and launch['launcher_sha256'] == config['launcher_sha256']
            and type(launch['pid']) is int and launch['pid'] > 1, 'launch root/driver/write/PID differs')
    require(common.utc(launch['started_utc']) <= time.time(), 'launch time is in future')
    expected = {root / 'run' / cell / 'process.json' for cell in CELLS}
    require(set(root.glob('**/process.json')) <= expected, 'unexpected owned process receipt')
    owned, cells = {launch['pid']}, {}
    for cell in CELLS:
        stage = root / 'run' / cell
        cells[cell] = {name: common.unaliased(stage / name).is_file() for name in
                       ('process.json', 'supervision.json', 'data/manifest.json', 'data/failure.json')}
        if cells[cell]['process.json']:
            process = read(stage / 'process.json')
            require(type(process['pid']) is int and process['pid'] > 1 and process['pgid'] == process['pid']
                    and process['pid'] not in owned, 'nonfresh/reused worker PID/PGID')
            owned.add(process['pid'])
    live = [row for row in common.process_snapshot() if any(row[key] in owned for key in ('pid', 'pgid', 'session'))]
    markers = {name: common.unaliased(root / 'run' / name).is_file() for name in ('result.json', 'failure.json')}
    return dict(ready=not live and sum(markers.values()) == 1, live_owned=live, owned_ids=sorted(owned),
                markers=markers, cells=cells, score_bodies_read=False, launch=launch)


def write_release(plan, launch):
    require(isinstance(launch.get('write_release_path'), str)
            and isinstance(launch.get('write_release_sha256'), str)
            and re.fullmatch('[0-9a-f]{64}', launch['write_release_sha256']), 'explicit write release path/hash required')
    path = common.unaliased(launch['write_release_path'])
    require(str(path) == launch['write_release_path'] and path.name == 'validation.json'
            and path.parent.parent == Path(plan['write_root']).parent
            and path.parent != Path(plan['write_root']), 'write release must be exact sibling collection validation path')
    require(digest(path) == launch['write_release_sha256'], 'write release hash differs')
    receipt = read(path)
    require(receipt.get('status') == 'COLLECTED_PAIRED_WRITE' and receipt.get('full_release') is True
            and receipt.get('aggregate_available') is True and receipt.get('plan_sha256') == plan['write_plan_sha256'],
            'write release acceptance/plan differs')
    require(digest(path) == launch['write_release_sha256'], 'write release changed during read')
    return path


def bind(config, bridge, plan, launch):
    root, logs = config['root'], config['launch_root']
    require(plan['write_driver'] == str(config['write_driver'])
            and plan['write_driver_sha256'] == config['write_driver_sha256']
            and plan['write_plan_sha256'] == config['write_plan_sha256'], 'CLI process-write pins differ from readout plan')
    require('write_driver_sha256' not in launch or launch['write_driver_sha256'] == plan['write_driver_sha256'],
            'optional launch write driver pin differs')
    require(digest(config['driver']) == config['driver_sha256'] and digest(config['write_driver']) == config['write_driver_sha256']
            and digest(config['launcher']) == config['launcher_sha256'], 'driver/write/launcher source changed')
    require(launch['device'] == plan['device'] and launch['source'] == plan['source_root']
            and launch['command'] == [plan['python'], '-B', str(config['driver']), 'evaluate', '--root', str(root),
                                     '--plan-sha256', config['plan_sha256'], '--allow-gpu'], 'launch command/source/device differs')
    expected = dict(cells=list(CELLS), controller_seconds=1800, cleanup_reserve=140,
                    worker_cap_seconds=600, continuous_reservation=True)
    require(all(launch[key] == value for key, value in expected.items()), 'launch bounds/order differ')
    optional = dict(external_collection_margin_seconds=300, max_calls=96, max_generated_tokens=27600,
                    adaptation_test=False, model_origin=bridge.ORIGIN, conditioning=bridge.CONDITIONING)
    require(all(key not in launch or launch[key] == value for key, value in optional.items()), 'optional launch boundary differs')
    write_release(plan, launch)
    devices = ET.fromstring(common.payload(logs / 'gpu.xml')).findall('gpu')
    require(len(devices) == 1 and devices[0].findtext('uuid') == launch['gpu']['gpu_uuid'], 'launch GPU XML UUID differs')
    processes = devices[0].find('processes')
    require(processes is not None and not list(processes) and not (processes.text or '').strip(), 'launch GPU XML was not vacant')


def raw_cost(data, process, ready, supervision):
    costs, roles, previous, maximum = {key: 0 for key in COST_KEYS}, Counter(), ready['ready'], None
    for path in sorted((data / 'calls').glob('*.request.json')):
        sent = read(path)
        received = read(path.with_name(path.name.replace('.request.', '.response.')))
        request, response = sent['request'], received['response']
        require(common.finite(sent['started']) and common.finite(received['ended'])
                and previous <= sent['started'] <= received['ended'], 'nonmonotone/invalid native call clocks')
        duration = received['ended'] - sent['started']
        require(duration <= 120 and received['ended'] <= process['started'] + supervision['reserved_seconds'] + 1e-6,
                'native call outside inherited worker/call bound')
        previous = received['ended']
        role = request['role']
        require(role in ('wake', 'record') and request['max_tokens'] == (400 if role == 'wake' else 100), 'parent/unknown role or token cap')
        require(len(response['output_token_ids']) <= request['max_tokens'], 'output token ceiling exceeded')
        roles[role] += 1
        costs['requests'] += 1
        costs['native_input_tokens'] += len(response['prompt_token_ids'])
        costs['native_output_tokens'] += len(response['output_token_ids'])
        costs['output_token_ceiling'] += request['max_tokens']
        costs['generation_seconds'] += duration
        maximum = duration if maximum is None else max(maximum, duration)
    require(roles['wake'] <= 20 and roles['record'] <= 12 and costs['requests'] <= 32, 'cell call ceiling exceeded')
    return costs, dict(roles), maximum


def checked_cell(config, bridge, plan, diagnostic, lineage, controller, cell):
    root, stage = config['root'], config['root'] / 'run' / cell
    spec_path, data = root / 'run' / (cell+'.spec.json'), stage / 'data'
    spec = read(spec_path)
    expected = bridge.worker_spec(root, plan, lineage, cell, controller['hard_end'])
    expected['nonce'] = spec['nonce']
    require(spec == expected and isinstance(spec['nonce'], str) and re.fullmatch('[0-9a-f]{32}', spec['nonce']), 'worker spec/context/adapter differs')
    process, supervision = read(stage / 'process.json'), read(stage / 'supervision.json')
    require(process['argv'] == [plan['python'], '-B', str(config['driver']), '_worker', '--spec', str(spec_path),
                                '--spec-sha256', digest(spec_path), '--allow-gpu'] and process['device'] == plan['device']
            and type(process['pid']) is int and process['pid'] == process['pgid'] > 1
            and common.finite(process['started']) and common.finite(process['timeout']) and 0 < process['timeout'] <= 600,
            'worker ownership/command/cap differs')
    require(supervision['device'] == plan['device'] and supervision['returncode'] == 0 and supervision['error'] is None
            and all(supervision[key] is True for key in ('ok', 'owned_group_empty', 'gpu_processes_absent', 'reservation_release_verified'))
            and common.finite(supervision['reserved_seconds']) and supervision['reserved_seconds'] <= process['timeout']+140,
            'worker supervision/release/cost differs')
    isolation, ready = read(data / 'isolation.json'), read(data / 'backend.ready.json')
    require(isolation['pid'] == isolation['pgid'] == ready['pid'] == process['pid']
            and isolation['parent_pid'] == controller['pid'] and isolation['spec_sha256'] == digest(spec_path)
            and isolation['parent_calls'] == 0 and isolation['task_prefix'] == '' and isolation['record_training'] is False,
            'fresh parent-free worker isolation differs')
    require(common.finite(ready['ready']) and 0 <= ready['ready']-process['started'] <= 180, 'native readiness clock differs')
    native, cleanup = read(data / 'native_audit.json'), read(data / 'backend.cleanup.json')
    require(native['ok'] is True and cleanup['closed'] is True and cleanup['error'] is None, 'native audit/cleanup differs')
    audit = bridge.audit_cell(root, plan, lineage, cell, diagnostic)
    result, metrics = audit['result'], audit['process_metrics']
    require(read(stage / 'provenance.json') == audit, 'stored process replay/metrics differ')
    require([row['eid'] for row in result['tasks']] == diagnostic.schedule()['evaluation'] and len(result['tasks']) == 4
            and all(row['arm'] == cell and type(row['valid_quiz']) is bool and common.finite(row['quiz_accuracy'])
                    and row['quiz_accuracy'] <= 1 and (row['valid_quiz'] or row['quiz_accuracy'] == 0) for row in result['tasks']),
            'fixed development tasks/invalid-zero quiz differs')
    require(metrics == bridge.process_metrics(data, audit, diagnostic) and metrics['totals']['quiz_items'] == 24
            and metrics['totals']['allotted_record_opportunities'] == 12
            and metrics['totals']['allotted_probe_opportunities'] == 12
            and math.isclose(metrics['quiz_accuracy_fixed24'], result['mean_quiz_accuracy'], abs_tol=1e-12),
            'fixed24/probe/prediction/record denominators differ')
    costs, roles, maximum = raw_cost(data, process, ready, supervision)
    require(result['calls'] == native['calls'] == costs['requests'] and result['roles'] == roles, 'raw/native/role call counts differ')
    usage = diagnostic.usage(data)
    require(all(math.isclose(sum(row[key] for row in usage.values()), costs[key], rel_tol=0,
                            abs_tol=1e-6 if key == 'generation_seconds' else 0) for key in COST_KEYS), 'raw usage accounting differs')
    receipt = dict(result=result, capture_sha256=digest(data / 'manifest.json'), spec_sha256=digest(spec_path),
                   supervision_sha256=digest(stage / 'supervision.json'), process_metrics=metrics)
    return dict(verified=True, controller_receipt=receipt, costs=costs, roles=roles, process_metrics=metrics,
                worker_pid=process['pid'], worker_started=process['started'], worker_reserved_seconds=supervision['reserved_seconds'],
                max_call_seconds=maximum)


def audit(config, bridge, plan, diagnostic, launch):
    root, run = config['root'], config['root'] / 'run'
    successful = (run / 'result.json').exists()
    terminal_path = run / ('result.json' if successful else 'failure.json')
    terminal = read(terminal_path)
    seconds = terminal.get('controller_seconds')
    require(common.finite(seconds), 'terminal controller clock missing/invalid')
    controller = read(run / 'controller.json') if (run / 'controller.json').is_file() else None
    if controller is not None:
        require(controller['pid'] == launch['pid'] and controller['plan_sha256'] == config['plan_sha256']
                and common.finite(controller['started_wall']) and common.utc(launch['started_utc']) <= controller['started_wall']
                and controller['hard_end'] == min(controller['started_wall']+1800, plan['deadline'], plan['lease_cutoff'])
                and controller['cleanup_reserve'] == 140, 'controller identity/bounds differ')
    within = controller is not None and seconds <= 1800 and controller['started_wall']+seconds <= controller['hard_end']+.001
    if successful:
        require(within and terminal['status'] == 'COMPLETE_EXPLORATORY_READOUT' and set(terminal['cells']) == set(CELLS),
                'complete result requires bounded three-cell coverage')
    else:
        require(terminal['aggregate'] is None and terminal['retry'] is False
                and terminal['completed_cells'] == list(CELLS)[:len(terminal['completed_cells'])], 'failed terminal aggregate/prefix differs')
    lineage = bridge.accepted_writes(plan, native=True)
    require(lineage == plan['lineage'], 'native process-write lineage changed')
    stored_lineage = read(run / 'lineage.json') if (run / 'lineage.json').is_file() else None
    require(stored_lineage is None or stored_lineage == lineage, 'stored process-write lineage changed')
    reports, errors = {}, []
    for cell in CELLS:
        stage = run / cell
        observed_seconds = None
        if (stage / 'supervision.json').is_file():
            receipt = read(stage / 'supervision.json')
            if receipt.get('device') == plan['device'] and common.finite(receipt.get('reserved_seconds')):
                observed_seconds = receipt['reserved_seconds']
        try:
            require(controller is not None and stored_lineage is not None, 'controller/lineage receipt absent')
            row = checked_cell(config, bridge, plan, diagnostic, lineage, controller, cell)
            if successful:
                require(terminal['cells'][cell] == row['controller_receipt'], 'terminal/raw cell receipt differs')
            reports[cell] = row
        except (ValueError, OSError, KeyError, TypeError) as error:
            reports[cell] = dict(verified=False, costs=None, process_metrics=None, worker_reserved_seconds=observed_seconds,
                                 error_type=type(error).__name__, detail=str(error)[:1000])
            errors.append(cell)
    verified = [reports[cell] for cell in CELLS if reports[cell]['verified']]
    require(len({row['worker_pid'] for row in verified}) == len(verified)
            and all(row['worker_pid'] != launch['pid'] for row in verified), 'workers reused PID/controller')
    require(all(left['worker_started']+left['worker_reserved_seconds'] <= right['worker_started']
                for left, right in zip(verified, verified[1:])), 'OFF/P_ON/A_ON windows overlap/reorder')
    require(set(root.glob('**/supervision.json')) == {run / cell / 'supervision.json' for cell in CELLS
            if (run / cell / 'supervision.json').exists()}, 'unexpected supervisor outside readout cells')
    aggregate, totals = None, None
    if successful and not errors:
        require(terminal['version'] == bridge.VERSION and terminal['training_objective'] == plan['protocol']['training_objective']
                and terminal['conditioning'] == bridge.CONDITIONING and terminal['model_origin'] == bridge.ORIGIN
                and terminal['claims'] == bridge.CLAIMS and terminal['training_metadata'] == lineage['training_metadata']
                and terminal['protocol'] == plan['protocol'] and terminal['inference'] == plan['protocol']['inference']
                and terminal['claim_boundary'] == diagnostic.CLAIM_BOUNDARY
                and all(terminal[key] is False for key in ('adaptation_test', 'semantic_nonleakage_certified', 'model_authentication_certified')),
                'process objective/training/claim boundary changed')
        totals = {key: sum(row['costs'][key] for row in verified) for key in COST_KEYS}
        require(totals['requests'] <= 96 and totals['output_token_ceiling'] <= 27600, 'three-cell generation ceiling exceeded')
        means = {cell: reports[cell]['process_metrics']['quiz_accuracy_fixed24'] for cell in CELLS}
        contrasts = dict(P_minus_OFF=means['P_ON']-means['OFF'], A_minus_OFF=means['A_ON']-means['OFF'],
                         P_minus_A=means['P_ON']-means['A_ON'])
        require(all(math.isclose(terminal[key], value, rel_tol=0, abs_tol=1e-12) for key, value in contrasts.items()), 'quiz contrasts differ')
        aggregate = dict(quiz_contrasts=contrasts, quiz_items_per_cell=24,
                         descriptive_event_metrics={cell: reports[cell]['process_metrics'] for cell in CELLS})
    observed = [row['worker_reserved_seconds'] for row in reports.values() if row['worker_reserved_seconds'] is not None]
    return dict(verified=successful and not errors, status='VERIFIED_COMPLETE' if successful and not errors else 'FAILED_PARTIAL_OR_AUDIT',
                cells=reports, aggregate=aggregate, totals=totals, controller_seconds=seconds, controller_within_bound=within,
                observed_worker_seconds=sum(observed) if observed else None, worker_cost_complete=len(observed) == 3,
                terminal_sha256=digest(terminal_path), model_origin=bridge.ORIGIN, conditioning=bridge.CONDITIONING,
                claim_boundary='Process-wake context-distillation readout; not raw RECORD objective, clean lineage, autonomous updates, G5 or H2.',
                prediction_limit='Boot requests PREDICT; pre-TRY emission/adherence is not unprompted cognition or information gain.')


def collect(config):
    started, wall = time.monotonic(), time.time()
    observed = status(config)
    require(observed['ready'], 'wait for terminal and all owned PID/PGID/session scopes absent; no score reads')
    root, logs, output = config['root'], config['launch_root'], config.get('out')
    require(output is not None and output.parent == root.parent and output not in (root, logs), 'fresh sibling output required')
    output.mkdir(mode=0o700)
    write_json(output / 'started.json', dict(started_wall=wall, input_pins={key: str(value) for key, value in config.items()},
               collector_sha256=digest(__file__), external_seconds=300, blind_until_all_owned_scopes_absent=True))
    try:
        common.inventory(root, logs)
        bridge = common.load(config['driver'], config['driver_sha256'], 'process_readout_collected_driver')
        checked_root, plan, diagnostic = bridge.checked_plan(root, config['plan_sha256'])
        require(checked_root == root, 'checked readout root differs')
        launch = observed['launch']
        bind(config, bridge, plan, launch)
        release_bytes = common.payload(write_release(plan, launch))
        require(hashlib.sha256(release_bytes).hexdigest() == launch['write_release_sha256'], 'write release copy hash differs')
        common.scan_text(release_bytes, 'write_release.json')
        write_new(output / 'write_release.json', release_bytes)
        sources = dict(plan['source_pins'])
        sources.update({str(config['driver']): config['driver_sha256'], str(config['write_driver']): config['write_driver_sha256'],
                        str(config['launcher']): config['launcher_sha256'], str(BASE): BASE_SHA,
                        str(common.COMMON): common.COMMON_SHA, str(bridge.FROZEN_READOUT): bridge.FROZEN_SHA256,
                        str(Path(__file__).absolute()): digest(__file__),
                        str(Path(plan['source_root']) / 'gpu/astra_mini_sudoku_diagnostic.py'): common.CHECK_SHA})
        sources = tuple(sources.items())
        files, hashes, excluded = common.inventory(root, logs, sources)
        try:
            report = audit(config, bridge, plan, diagnostic, launch)
        except Exception as error:
            report = dict(verified=False, status='AUDIT_FAILED', aggregate=None, totals=None,
                          error_type=type(error).__name__, detail=str(error)[:1000])
        release = dict(full_release=False, gpu=None, error_type=None)
        try:
            require(status(config)['ready'], 'owned session reappeared')
            gpu, xml = common.release_check(plan, launch['gpu']['gpu_uuid'])
            require(status(config)['ready'], 'owned session reappeared')
            release = dict(full_release=True, gpu=gpu, observed_wall=time.time(), error_type=None)
            write_new(output / 'release.xml', xml.encode())
        except Exception as error:
            release.update(error_type=type(error).__name__, detail=str(error)[:1000])
        bridge.checked_plan(root, config['plan_sha256'])
        bind(config, bridge, plan, launch)
        require(common.inventory(root, logs, sources)[1:] == (hashes, excluded), 'terminal metadata changed during collection')
        if not (report['verified'] and release['full_release']):
            report['aggregate'], report['totals'] = None, None
        write_json(output / 'audit.json', report)
        write_json(output / 'release.json', release)
        full_seconds = release['observed_wall']-common.utc(launch['started_utc']) if release['full_release'] else None
        write_json(output / 'custody.json', dict(input_hashes=hashes, excluded_weights=excluded, source_pins=dict(sources),
                   write_release_path=launch['write_release_path'], write_release_sha256=launch['write_release_sha256'],
                   readout_plan_sha256=config['plan_sha256'], write_plan_sha256=config['write_plan_sha256'],
                   launch_sha256=config['launch_sha256'], full_launch_to_release_seconds=full_seconds,
                   controller_seconds=report.get('controller_seconds'), observed_worker_seconds=report.get('observed_worker_seconds'),
                   collection_seconds_at_snapshot=time.monotonic()-started,
                   accounting='Generation/load inside workers; supervised cleanup inside controller; collection overlaps launch-to-observed-release. Nested clocks, not additive.',
                   limitations='Hash/native replay custody is not semantic nonleakage or model authentication. Known credential patterns rejected, not a universal secret detector.'))
        for path in sorted(output.iterdir()):
            name = 'metadata/collection/'+path.name
            data = common.payload(path)
            common.scan_text(data, name)
            files[name], hashes[name] = path, hashlib.sha256(data).hexdigest()
        require(len(files) <= common.MAX_FILES and sum(path.stat().st_size for path in files.values()) <= common.MAX_TOTAL, 'capsule bounds exceeded')
        archive = output / 'metadata.tgz'
        archive_pin = common.pack(archive, files, hashes)
        require(status(config)['ready'], 'owned scope reappeared after packing')
        bridge.checked_plan(root, config['plan_sha256'])
        bind(config, bridge, plan, launch)
        require(all(digest(path) == hashes[name] for name, path in files.items()), 'metadata changed after packing')
        require(set(common.inventory(root, logs, sources)[0]) == {name for name in files if not name.startswith('metadata/collection/')},
                'metadata appeared after packing')
        require(common.file_hash(archive) == archive_pin, 'validated archive changed')
        elapsed = time.monotonic()-started
        require(elapsed <= 300, 'external custody window exceeded')
        result = dict(status='COLLECTED_COMPLETE' if report['verified'] and release['full_release'] else 'COLLECTED_PARTIAL_NO_AGGREGATE',
                      archive=str(archive), archive_sha256=archive_pin, files=hashes, full_release=release['full_release'],
                      science_aggregate_available=report['verified'] and release['full_release'], collection_seconds=elapsed,
                      full_launch_to_release_seconds=full_seconds, retry=False)
        write_json(output / 'validation.json', result)
        return {key: value for key, value in result.items() if key != 'files'}
    except BaseException as error:
        write_json(output / 'failure.json', dict(error_type=type(error).__name__, aggregate=None, retry=False,
                   partial_artifacts_preserved=True, collection_seconds=time.monotonic()-started))
        raise


def finish(config):
    require(signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0), 'existing timer conflicts')
    def expired(number, frame):
        raise common.CollectionExpired('300s external custody window exhausted')
    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, 300)
    try:
        return collect(config)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('status', 'finish'))
    for name in ('root', 'plan-sha256', 'driver', 'driver-sha256', 'write-driver', 'write-driver-sha256',
                 'write-plan-sha256', 'launch-root', 'launch-sha256', 'launcher', 'launcher-sha256'):
        parser.add_argument('--'+name, required=True)
    parser.add_argument('--out')
    args = vars(parser.parse_args(argv))
    action = args.pop('action')
    config = settings(args)
    if action == 'status':
        result = status(config)
        result.pop('launch')
    else:
        result = finish(config)
    print(json.dumps(result, sort_keys=True, allow_nan=False), flush=True)


if __name__ == '__main__':
    main()
