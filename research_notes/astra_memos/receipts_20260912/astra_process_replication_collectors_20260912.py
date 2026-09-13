"""Terminal-only seed0/1 replication custody; no launches, tokenizer loads or retries."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import signal
import stat
import sys
import time

sys.dont_write_bytecode = True
SELF = Path(os.path.abspath(__file__))
DRIVER = Path('/tmp/astra_rulegame_process_replication_20260912.py')
DRIVER_SHA = '96e27f5b8becaa59263f221206dc89a1b7d9a95eba8056810339556d8d9d11dd'
COMMON = Path('/tmp/astra_rulegame_process_write_collect_20260912.py')
COMMON_SHA = 'e23160132bf4eac82f220b8066c49de3cf8461e50929f9a82f3eac5e12906892'
CHECK_SHA = 'a586b03bdb9c52f1061aa1e477ae983cc9d45ec0a2cd440642851fd8df8b609f'
ARMS, CELLS = ('P', 'A'), ('OFF', 'P_ON', 'A_ON')
CAPS = {'write': 1200, 'readout': 1800}
COLLECTION_SECONDS = 300
COST_KEYS = ('requests', 'native_input_tokens', 'native_output_tokens', 'output_token_ceiling', 'generation_seconds')


def _common():
    if any(path.is_symlink() for path in (COMMON, *COMMON.parents)):
        raise ValueError('symlink collection helper')
    descriptor = os.open(COMMON, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or before.st_size > 2*1024*1024:
            raise ValueError('unsafe collection helper')
        data = stream.read(2*1024*1024+1)
        after = os.fstat(stream.fileno())
        if len(data) != before.st_size or any(getattr(before, key) != getattr(after, key)
                or getattr(before, key) != getattr(COMMON.stat(), key)
                for key in ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns')):
            raise ValueError('collection helper changed')
    if hashlib.sha256(data).hexdigest() != COMMON_SHA:
        raise ValueError('collection helper hash mismatch')
    spec = importlib.util.spec_from_file_location('replication_collection_common', COMMON)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    exec(compile(data, str(COMMON), 'exec'), module.__dict__)
    return module


common = _common()
require, read, digest = common.require, common.read, common.digest
write_json, write_new = common.write_json, common.write_new
process_snapshot = common.process_snapshot


def settings(values):
    config = dict(values)
    require(config.get('phase') in CAPS and type(config.get('fit_seed')) is int
        and config['fit_seed'] in (0, 1), 'explicit phase and FIT seed0/1 required')
    for key in ('root', 'launch_root', 'launcher', 'out', 'write_release'):
        if config.get(key) is not None:
            config[key] = common.unaliased(config[key])
    for key in ('plan_sha256', 'launch_sha256', 'launcher_sha256'):
        require(isinstance(config.get(key), str) and re.fullmatch('[0-9a-f]{64}', config[key]), 'explicit SHA256 required: '+key)
    require(config['root'].is_dir() and config['launch_root'].is_dir()
        and config['root'].parent == config['launch_root'].parent and config['root'] != config['launch_root'],
        'distinct sibling run/launch directories required')
    if config['phase'] == 'readout':
        require(config.get('write_release') is not None and isinstance(config.get('write_release_sha256'), str)
            and re.fullmatch('[0-9a-f]{64}', config['write_release_sha256']), 'readout requires explicit write release pins')
    else:
        require(config.get('write_release') is None and config.get('write_release_sha256') is None,
            'write phase cannot consume a write release')
    return config


def load_runner():
    return common.load(DRIVER, DRIVER_SHA, 'replication_collection_runner')


def status(config):
    root, logs = config['root'], config['launch_root']
    require(digest(root/'plan.json') == config['plan_sha256'] == read(root/'plan.sha256.json')['sha256'], 'plan hash/seal mismatch')
    plan = read(root/'plan.json')
    require(type(plan.get('fit_seed')) is int and plan['fit_seed'] == config['fit_seed'], 'plan FIT seed mismatch')
    expected = 'rulegame_process_fit_seed_'+config['phase']+'_v1_20260912'
    require(plan.get('protocol' if config['phase'] == 'write' else 'version') == expected, 'wrong phase protocol')
    require(digest(logs/'launch.json') == config['launch_sha256'], 'launch hash mismatch')
    launch = read(logs/'launch.json')
    require(launch['root'] == str(root) and launch['plan_sha256'] == config['plan_sha256']
        and launch['driver_sha256'] == DRIVER_SHA and launch['launcher_sha256'] == config['launcher_sha256']
        and type(launch.get('fit_seed')) is int and launch['fit_seed'] == config['fit_seed']
        and type(launch['pid']) is int and launch['pid'] > 1, 'launch phase/seed/source/ownership mismatch')
    require(common.utc(launch['started_utc']) <= time.time(), 'future launch time')
    members = ARMS if config['phase'] == 'write' else CELLS
    expected_processes = {root/'run'/member/'process.json' for member in members}
    require(set(root.glob('**/process.json')) <= expected_processes, 'unexpected owned process receipt')
    owned = {launch['pid']}
    for path in expected_processes:
        if common.unaliased(path).is_file():
            process = read(path)
            require(type(process['pid']) is int and process['pid'] > 1 and process['pgid'] == process['pid']
                and process['pid'] not in owned, 'nonfresh/reused worker PID/PGID')
            owned.add(process['pid'])
    snapshot = process_snapshot()
    descendants = set(owned)
    while True:
        extended = descendants | {row['pid'] for row in snapshot if row.get('ppid') in descendants}
        if extended == descendants:
            break
        descendants = extended
    live = [row for row in snapshot if row['pid'] in descendants or
            any(row[key] in owned for key in ('pgid', 'session'))]
    markers = {name: common.unaliased(root/'run'/name).is_file() for name in ('result.json', 'failure.json')}
    return dict(ready=not live and sum(markers.values()) == 1, owned_ids=sorted(owned), live_owned=live,
        markers=markers, launch=launch, terminal_bodies_read=False, vacancy_queried=False,
        phase=config['phase'], fit_seed=config['fit_seed'])


def write_release(config, plan, launch):
    path = config['write_release']
    require(path.name == 'validation.json' and path.parent.parent == config['root'].parent
        and path.parent not in (config['root'], config['launch_root'], Path(plan['write_root'])), 'write release location mismatch')
    require(digest(path) == config['write_release_sha256'] == launch['write_release_sha256']
        and str(path) == launch['write_release_path'], 'write release launch/CLI hash mismatch')
    receipt = read(path)
    require(receipt['status'] == 'COLLECTED_PAIRED_WRITE' and receipt['phase'] == 'write'
        and type(receipt['fit_seed']) is int and receipt['fit_seed'] == config['fit_seed']
        and receipt['driver_sha256'] == DRIVER_SHA and receipt['plan_sha256'] == plan['write_plan_sha256']
        and receipt['collector_sha256'] == digest(SELF)
        and receipt['full_release'] is True and receipt['aggregate_available'] is True
        and receipt['phase_within_bound'] is True and receipt['retry'] is False, 'write release not complete/bounded/same-seed')
    require(common.finite(receipt['full_launch_to_final_vacancy_seconds'])
        and receipt['full_launch_to_final_vacancy_seconds'] <= 1500
        and common.finite(receipt['collection_seconds']) and receipt['collection_seconds'] <= 300
        and receipt['final_vacancy']['observed_wall'] <= common.utc(launch['started_utc']), 'write/readout reservation overlap or invalid cost')
    archive = common.unaliased(receipt['archive'])
    require(archive.parent == path.parent and archive.name == 'metadata.tgz'
        and common.file_hash(archive) == receipt['archive_sha256'], 'write capsule hash/location changed')
    common.validate_archive(archive, receipt['files'])
    final_xml = common.payload(path.parent/'final_release.xml')
    require(hashlib.sha256(final_xml).hexdigest() == receipt['final_vacancy']['xml_sha256'], 'write final release XML changed')
    common.check_uuid(receipt['final_vacancy']['gpu'], final_xml, launch['gpu']['gpu_uuid'])
    require(digest(path) == config['write_release_sha256'], 'write release changed during check')
    return receipt


def bind(config, launch):
    require(digest(config['launcher']) == config['launcher_sha256'], 'launcher source hash mismatch')
    runner = load_runner()
    bridge = runner.WritePhase(config['fit_seed']) if config['phase'] == 'write' else runner.ReadoutPhase(config['fit_seed'])
    checked = bridge.checked_plan(config['root'], config['plan_sha256'])
    root, plan, diagnostic = checked[:3]
    require(root == config['root'] and plan['python'] == os.path.abspath(sys.executable), 'root/concrete interpreter mismatch')
    require(plan['replication'] == runner.contract(config['fit_seed']), 'replication budget/seed changed')
    action = 'write' if config['phase'] == 'write' else 'evaluate'
    command = [plan['python'], '-B', str(DRIVER), action, '--fit-seed', str(config['fit_seed']),
               '--root', str(root), '--plan-sha256', config['plan_sha256'], '--allow-gpu']
    expected = dict(command=command, device=plan['device'], source=plan['source_root'], continuous_reservation=True,
        controller_seconds=CAPS[config['phase']], cleanup_reserve=140, worker_cap_seconds=600,
        external_collection_margin_seconds=300)
    require(all(launch.get(key) == value for key, value in expected.items()), 'launcher command/bounds/reservation mismatch')
    version = bridge.WRITE_PROTOCOL if config['phase'] == 'write' else bridge.VERSION
    require('phase' not in launch or launch['phase'] == version, 'launcher phase mismatch')
    order_key, members = ('arms', ARMS) if config['phase'] == 'write' else ('cells', CELLS)
    require(launch.get(order_key) == list(members), 'launcher phase member order mismatch')
    common.check_uuid(launch['gpu'], common.payload(config['launch_root']/'gpu.xml'), launch['gpu']['gpu_uuid'])
    previous = None
    if config['phase'] == 'readout':
        require(launch['write_plan_sha256'] == plan['write_plan_sha256'] and
            launch.get('write_driver_sha256', DRIVER_SHA) == plan['write_driver_sha256'] == DRIVER_SHA,
            'readout/write plan or driver mismatch')
        previous = write_release(config, plan, launch)
    return runner, bridge, checked, previous


def allowed_paths(phase):
    if phase == 'write':
        return common.allowed_paths()
    names = {'plan.json', 'plan.sha256.json', 'run/controller.json', 'run/lineage.json', 'run/result.json', 'run/failure.json'}
    for cell in CELLS:
        names.add(f'run/{cell}.spec.json')
        names.update(f'run/{cell}/{name}' for name in ('process.json', 'supervision.json', 'stdout.log', 'provenance.json'))
        names.update(f'run/{cell}/data/{name}' for name in ('identity.json', 'isolation.json', 'backend.ready.json',
            'backend.cleanup.json', 'native_audit.json', 'manifest.json', 'result.json', 'usage.json', 'events.jsonl', 'failure.json'))
        names.update(f'run/{cell}/data/calls/{index:04d}.{kind}.json' for index in range(32) for kind in ('request', 'response'))
    return names, set(), set()


def inventory(config):
    allowed, raw, weights = allowed_paths(config['phase'])
    files, hashes, exclusions = {}, {}, {}
    count, total = 0, 0
    for base, prefix, permitted in ((config['root'], 'metadata/run', allowed),
            (config['launch_root'], 'metadata/launch', {'launch.json', 'gpu.xml', 'controller.log'})):
        directories = {str(parent) for name in permitted for parent in PurePosixPath(name).parents if str(parent) != '.'}
        def inaccessible(error):
            raise error
        for directory, children, names in os.walk(base, followlinks=False, onerror=inaccessible):
            for name in children + names:
                count += 1
                require(count <= common.MAX_FILES, 'filesystem entry limit')
                path = common.unaliased(Path(directory)/name)
                relative = path.relative_to(base).as_posix()
                require(path.is_dir() or path.is_file(), 'special filesystem entry')
                if path.is_dir():
                    require(relative in directories, 'unknown metadata directory: '+relative)
                    continue
                require(relative in permitted, 'unknown metadata file: '+relative)
                member = prefix+'/'+relative
                if base == config['root'] and relative in weights:
                    require(path.stat().st_size <= common.MAX_WEIGHTS, 'weight byte limit')
                    exclusions[member] = dict(sha256=common.file_hash(path), reason='weights_native_only')
                    continue
                data = common.payload(path)
                common.scan_text(data, member)
                if member.endswith('.jsonl'):
                    for line in data.splitlines():
                        common.scan_text(line, member+'.json')
                total += len(data)
                require(total <= common.MAX_TOTAL, 'metadata total byte limit')
                checksum = hashlib.sha256(data).hexdigest()
                if base == config['root'] and relative in raw:
                    exclusions[member] = dict(sha256=checksum, reason='raw_material_native_only')
                else:
                    files[member], hashes[member] = path, checksum
    require(files, 'empty inventory')
    return files, hashes, exclusions


def controller_receipts(config, plan, launch):
    run = config['root']/'run'
    success = (run/'result.json').is_file()
    terminal = read(run/('result.json' if success else 'failure.json'))
    controller = read(run/'controller.json') if (run/'controller.json').is_file() else None
    seconds = terminal.get('controller_seconds')
    require(common.finite(seconds), 'terminal controller clock invalid')
    bounded = False
    if controller is not None:
        require(controller['pid'] == launch['pid'] and controller['plan_sha256'] == config['plan_sha256']
            and common.finite(controller['started_wall']) and controller['cleanup_reserve'] == 140
            and controller['hard_end'] == min(controller['started_wall']+CAPS[config['phase']], plan['deadline'], plan['lease_cutoff'])
            and common.utc(launch['started_utc']) <= controller['started_wall'], 'controller identity/bounds mismatch')
        bounded = seconds <= CAPS[config['phase']] and controller['started_wall']+seconds <= controller['hard_end']+.001
    if success:
        require(bounded and type(terminal.get('fit_seed')) is int and terminal['fit_seed'] == config['fit_seed']
            and terminal.get('automatic_promotion') is False, 'successful terminal seed/cap/promotion mismatch')
    else:
        require(terminal.get('retry') is False and terminal.get('aggregate') is None, 'failed run must preserve partial/no retry')
    return success, terminal, controller, bounded


def worker_receipts(config, plan, controller, member, command):
    require(controller is not None, 'missing controller')
    stage = config['root']/'run'/member
    process, supervision = read(stage/'process.json'), read(stage/'supervision.json')
    require(type(process['pid']) is int and process['pid'] == process['pgid'] > 1
        and process['pid'] != controller['pid'] and process['argv'] == command and process['device'] == plan['device']
        and common.finite(process['started']) and common.finite(process['timeout']) and 0 < process['timeout'] <= 600,
        'worker ownership/command/cap mismatch')
    require(supervision['device'] == plan['device'] and supervision['returncode'] == 0 and supervision['error'] is None
        and all(supervision[key] is True for key in ('ok', 'owned_group_empty', 'gpu_processes_absent', 'reservation_release_verified'))
        and common.finite(supervision['reserved_seconds']) and supervision['reserved_seconds'] <= process['timeout']+140,
        'worker cleanup/cost mismatch')
    return process, supervision


def audit_write(config, runner, bridge, checked, launch):
    root, plan, diagnostic, exporter, trainer = checked
    material = runner.ReadoutPhase(config['fit_seed']).material_custody(bridge, root, plan, diagnostic, exporter, trainer, native=False)
    success, terminal, controller, bounded = controller_receipts(config, plan, launch)
    require(controller is None or controller['worker_seconds'] == 600, 'write worker cap changed')
    completed = terminal['arms'] if success else terminal['completed']
    require(set(completed) in (set(), {'P'}, {'P', 'A'}), 'write completion prefix changed')
    if success:
        require(terminal['status'] == 'PAIRED_ADAPTERS_SAVED_READOUT_PENDING' and set(completed) == set(ARMS)
            and terminal['protocol'] == bridge.WRITE_PROTOCOL and terminal['conditioning'] == bridge.CONDITIONING
            and terminal['claims'] == bridge.CLAIMS and terminal['model_origin'] == bridge.ORIGIN
            and terminal['model_authentication_certified'] is False and terminal['semantic_no_answer_certification'] is False,
            'write terminal protocol/claim mismatch')
    reports = {}
    for arm in ARMS:
        fit, stage = root/'fits'/arm, root/'run'/arm
        try:
            worker_launch = read(root/'run'/(arm+'.launch.json'))
            require(controller is not None and re.fullmatch('[0-9a-f]{32}', worker_launch['token'])
                and worker_launch['plan_sha256'] == config['plan_sha256'] and worker_launch['hard_end'] == controller['hard_end']
                and worker_launch['controller_pid'] == controller['pid'], 'write launch ownership mismatch')
            command = [plan['python'], '-B', str(DRIVER), '_write-worker', '--root', str(root), '--arm', arm,
                '--plan-sha256', config['plan_sha256'], '--launch-token', worker_launch['token'], '--allow-gpu']
            require(worker_launch['command'] == command, 'write worker launch command mismatch')
            process, supervision = worker_receipts(config, plan, controller, arm, command)
            require(read(fit/'attempt.json') == dict(arm=arm, plan_sha256=config['plan_sha256'], init_adapter=None,
                pid=process['pid']), 'fit attempt ownership mismatch')
            require(read(fit/'manifest.json')['files'] == diagnostic.tree_hashes(fit, ('manifest.json',)), 'fit manifest changed')
            receipt = bridge.validate_fit(root, arm, plan, diagnostic, trainer)
            require(read(fit/'receipt.json') == receipt and receipt['steps'] == receipt['observed_forward_batches'] == 12,
                'saved fit/forward receipt mismatch')
            sealed = dict(receipt, fit_manifest_sha256=digest(fit/'manifest.json'), supervision_sha256=digest(stage/'supervision.json'))
            require(arm not in completed or completed[arm] == sealed, 'controller/fit receipt mismatch')
            weights = common.finite_weights(fit/'adapter/adapter_model.safetensors', receipt['files']['adapter_model.safetensors'])
            manifest = read(fit/'adapter/train_manifest.json')
            reports[arm] = dict(verified=True, receipt=sealed, finite_weights=weights, final_loss=manifest['final_loss'],
                mean_loss_per_epoch=manifest['mean_loss_per_epoch'], steps=manifest['steps'], epochs=manifest['epochs_run'],
                tokens=manifest['tokens'], exposure=receipt['exposure'], worker_pid=process['pid'],
                worker_started=process['started'], worker_reserved_seconds=supervision['reserved_seconds'])
        except (ValueError, OSError, KeyError, TypeError) as error:
            reports[arm] = dict(verified=False, error_type=type(error).__name__, aggregate=None)
    verify_windows(reports)
    verified = success and all(reports[arm]['verified'] for arm in ARMS)
    aggregate = None
    if verified:
        require(terminal['exposure'] == {arm: plan['tokens'][arm]['exposure'] for arm in ARMS}, 'write exposure summary changed')
        aggregate = dict(optimizer_updates=24, epochs_per_arm=12, rows_per_arm=2,
            full_target_tokens_seen=sum(reports[arm]['exposure']['full_target_tokens_seen'] for arm in ARMS),
            input_tokens_seen=sum(plan['tokens'][arm]['train_tokens_seen'] for arm in ARMS),
            padded_input_tokens_seen=sum(reports[arm]['exposure']['padded_input_tokens_seen'] for arm in ARMS),
            target_matched=False, input_matched=False, efficacy=None)
    return dict(verified=verified, terminal_success=success, arms=reports, material=material, aggregate=aggregate,
        controller_seconds=terminal['controller_seconds'], controller_within_bound=bounded,
        model_origin=bridge.ORIGIN, conditioning=bridge.CONDITIONING, fit_seed=config['fit_seed'])


def verify_windows(reports):
    rows = [row for row in reports.values() if row['verified']]
    require(len({row['worker_pid'] for row in rows}) == len(rows), 'worker PID reused')
    require(all(left['worker_started']+left['worker_reserved_seconds'] <= right['worker_started']
        for left, right in zip(rows, rows[1:])), 'worker windows overlap or reorder')


def raw_cost(data, process, ready, supervision):
    costs, roles = {key: 0 for key in COST_KEYS}, Counter()
    previous = ready['ready']
    requests = sorted((data/'calls').glob('*.request.json'))
    require([path.name for path in requests] == [f'{index:04d}.request.json' for index in range(len(requests))]
        and set((data/'calls').glob('*.json')) == set(requests) | {path.with_name(path.name.replace('.request.', '.response.')) for path in requests},
        'raw call sequence/response inventory mismatch')
    for path in requests:
        sent, received = read(path), read(path.with_name(path.name.replace('.request.', '.response.')))
        request, response = sent['request'], received['response']
        require(common.finite(sent['started']) and common.finite(received['ended']) and previous <= sent['started'] <= received['ended'],
            'nonmonotone native call clocks')
        duration = received['ended']-sent['started']
        require(duration <= 120 and received['ended'] <= process['started']+supervision['reserved_seconds']+1e-6, 'native call cap/window mismatch')
        previous = received['ended']
        role = request['role']
        require(role in ('wake', 'record') and request['max_tokens'] == (400 if role == 'wake' else 100)
            and request['temperature'] == .7 and len(response['output_token_ids']) <= request['max_tokens'], 'role/generation cap mismatch')
        require(all(isinstance(response[key], list) and all(type(token) is int and token >= 0 for token in response[key])
            for key in ('prompt_token_ids', 'output_token_ids')), 'malformed native token IDs')
        roles[role] += 1
        costs['requests'] += 1
        costs['native_input_tokens'] += len(response['prompt_token_ids'])
        costs['native_output_tokens'] += len(response['output_token_ids'])
        costs['output_token_ceiling'] += request['max_tokens']
        costs['generation_seconds'] += duration
    require(roles['wake'] <= 20 and roles['record'] <= 12 and costs['requests'] <= 32, 'cell call ceiling exceeded')
    return costs, dict(roles)


def checked_cell(config, runner, bridge, plan, diagnostic, lineage, controller, cell):
    root = config['root']
    stage, spec_path = root/'run'/cell, root/'run'/(cell+'.spec.json')
    data = stage/'data'
    spec = read(spec_path)
    require(controller is not None, 'missing readout controller')
    expected = bridge.worker_spec(root, plan, lineage, cell, controller['hard_end'])
    expected['nonce'] = spec['nonce']
    require(spec == expected and re.fullmatch('[0-9a-f]{32}', spec['nonce']), 'readout spec/context/adapter mismatch')
    command = [plan['python'], '-B', str(DRIVER), '_readout-worker', '--spec', str(spec_path),
        '--spec-sha256', digest(spec_path), '--allow-gpu']
    process, supervision = worker_receipts(config, plan, controller, cell, command)
    isolation, ready = read(data/'isolation.json'), read(data/'backend.ready.json')
    require(isolation['pid'] == isolation['pgid'] == ready['pid'] == process['pid']
        and isolation['parent_pid'] == controller['pid'] and isolation['spec_sha256'] == digest(spec_path)
        and isolation['parent_calls'] == 0 and isolation['task_prefix'] == '' and isolation['record_training'] is False,
        'parent-free readout isolation mismatch')
    require(common.finite(ready['ready']) and 0 <= ready['ready']-process['started'] <= 180, 'readiness clock mismatch')
    native, cleanup, header = read(data/'native_audit.json'), read(data/'backend.cleanup.json'), read(data/'identity.json')
    require(native['ok'] is True and cleanup['closed'] is True and cleanup['error'] is None
        and not (data/'failure.json').exists(), 'native audit or cleanup failed')
    adapter = None if cell == 'OFF' else lineage['fits'][cell[0]]['adapter']
    require(header['stage'] == 'evaluation' and header['cell'] == cell and header['model_files'] == plan['model_files'], 'capture identity mismatch')
    audit = diagnostic.check_capture(data, diagnostic.expected_identity(plan, adapter), 'interaction_v3')
    require(audit['ok'], 'recorded-event replay failed')
    audit['process_metrics'] = bridge.process_metrics(data, audit, diagnostic)
    require(read(stage/'provenance.json') == audit, 'stored process provenance/metrics mismatch')
    result, metrics = audit['result'], audit['process_metrics']
    require([row['eid'] for row in result['tasks']] == diagnostic.schedule()['evaluation'] and len(result['tasks']) == 4
        and all(row['arm'] == cell and type(row['valid_quiz']) is bool and common.finite(row['quiz_accuracy'])
            and row['quiz_accuracy'] <= 1 and (row['valid_quiz'] or row['quiz_accuracy'] == 0) for row in result['tasks']),
        'fixed task panel or invalid-zero changed')
    require(metrics['totals']['quiz_items'] == 24 and metrics['totals']['allotted_record_opportunities'] == 12
        and metrics['totals']['allotted_probe_opportunities'] == 12
        and math.isclose(metrics['quiz_accuracy_fixed24'], result['mean_quiz_accuracy'], rel_tol=0, abs_tol=1e-12), 'metric denominators changed')
    costs, roles = raw_cost(data, process, ready, supervision)
    require(result['calls'] == native['calls'] == costs['requests'] and result['roles'] == roles, 'raw/native call counts mismatch')
    usage = diagnostic.usage(data)
    require(all(math.isclose(sum(row[key] for row in usage.values()), costs[key], rel_tol=0,
        abs_tol=1e-6 if key == 'generation_seconds' else 0) for key in COST_KEYS), 'raw usage costs mismatch')
    receipt = dict(result=result, capture_sha256=digest(data/'manifest.json'), spec_sha256=digest(spec_path),
        supervision_sha256=digest(stage/'supervision.json'), process_metrics=metrics)
    return dict(verified=True, receipt=receipt, costs=costs, roles=roles, process_metrics=metrics,
        worker_pid=process['pid'], worker_started=process['started'], worker_reserved_seconds=supervision['reserved_seconds'])


def audit_readout(config, runner, bridge, checked, launch):
    root, plan, diagnostic = checked
    lineage = bridge.accepted_writes(plan, native=False)
    require(lineage == plan['lineage'], 'prepared lineage changed')
    weights = {arm: common.finite_weights(Path(lineage['fits'][arm]['adapter'])/'adapter_model.safetensors',
        lineage['fits'][arm]['files']['adapter_model.safetensors']) for arm in ARMS}
    success, terminal, controller, bounded = controller_receipts(config, plan, launch)
    if success:
        require(terminal['status'] == 'COMPLETE_EXPLORATORY_READOUT' and set(terminal['cells']) == set(CELLS), 'complete three-cell result required')
    else:
        require(terminal['completed_cells'] == list(CELLS)[:len(terminal['completed_cells'])], 'readout completion prefix changed')
    stored = read(root/'run/lineage.json') if (root/'run/lineage.json').is_file() else None
    require(stored is None or stored == lineage, 'stored lineage changed')
    reports = {}
    for cell in CELLS:
        try:
            require(stored is not None, 'missing lineage receipt')
            report = checked_cell(config, runner, bridge, plan, diagnostic, lineage, controller, cell)
            require(not success or terminal['cells'][cell] == report['receipt'], 'terminal/cell receipt mismatch')
            reports[cell] = report
        except (ValueError, OSError, KeyError, TypeError) as error:
            reports[cell] = dict(verified=False, error_type=type(error).__name__, aggregate=None)
    verify_windows(reports)
    verified = success and all(reports[cell]['verified'] for cell in CELLS)
    aggregate, totals = None, None
    if verified:
        require(terminal['version'] == bridge.VERSION and terminal['training_objective'] == plan['protocol']['training_objective']
            and terminal['conditioning'] == bridge.CONDITIONING and terminal['model_origin'] == bridge.ORIGIN
            and terminal['claims'] == bridge.CLAIMS and terminal['training_metadata'] == lineage['training_metadata']
            and terminal['protocol'] == plan['protocol'] and terminal['inference'] == plan['protocol']['inference']
            and terminal['claim_boundary'] == diagnostic.CLAIM_BOUNDARY
            and all(terminal[key] is False for key in ('adaptation_test', 'semantic_nonleakage_certified', 'model_authentication_certified')),
            'readout terminal metadata/claim mismatch')
        totals = {key: sum(reports[cell]['costs'][key] for cell in CELLS) for key in COST_KEYS}
        require(totals['requests'] <= 96 and totals['output_token_ceiling'] <= 27600, 'readout total call/token cap exceeded')
        means = {cell: reports[cell]['process_metrics']['quiz_accuracy_fixed24'] for cell in CELLS}
        contrasts = dict(P_minus_OFF=means['P_ON']-means['OFF'], A_minus_OFF=means['A_ON']-means['OFF'], P_minus_A=means['P_ON']-means['A_ON'])
        require(all(math.isclose(terminal[key], value, rel_tol=0, abs_tol=1e-12) for key, value in contrasts.items()), 'readout contrasts mismatch')
        aggregate = dict(quiz_contrasts=contrasts, quiz_items_per_cell=24,
            descriptive_event_metrics={cell: reports[cell]['process_metrics'] for cell in CELLS})
    return dict(verified=verified, terminal_success=success, cells=reports, aggregate=aggregate, totals=totals,
        finite_weights=weights, controller_seconds=terminal['controller_seconds'], controller_within_bound=bounded,
        model_origin=bridge.ORIGIN, conditioning=bridge.CONDITIONING, fit_seed=config['fit_seed'],
        native_tokenizer_reloaded=False, saved_native_receipts_only=True)


def vacancy(plan, expected_uuid):
    require('CUDA_VISIBLE_DEVICES' not in os.environ, 'unset CUDA_VISIBLE_DEVICES for full proc/GPU/queue reconciliation')
    checker = common.load(Path(plan['source_root'])/'gpu/astra_mini_sudoku_diagnostic.py', CHECK_SHA, 'replication_release_checker')
    gpu, xml = checker.check_free(plan['device'])
    common.check_uuid(gpu, xml, expected_uuid)
    return gpu, xml


def collect(config):
    started, wall = time.monotonic(), time.time()
    output = config['out']
    require(output.parent == config['root'].parent and output not in (config['root'], config['launch_root'])
        and not output.exists(), 'exclusive fresh sibling collection required; preserve failed attempts')
    output.mkdir(mode=0o700)
    try:
        write_json(output/'started.json', dict(phase=config['phase'], fit_seed=config['fit_seed'], started_wall=wall,
            collection_seconds_limit=300, retry=False, driver_sha256=DRIVER_SHA))
        observed = status(config)
        require(observed['ready'], 'terminal plus full owned process/group/session release required before score reads')
        runner, bridge, checked, previous = bind(config, observed['launch'])
        plan = checked[1]
        gpu, xml = vacancy(plan, observed['launch']['gpu']['gpu_uuid'])
        files, hashes, excluded = inventory(config)
        initial_hashes, initial_excluded = dict(hashes), dict(excluded)
        if previous is not None:
            member = 'metadata/lineage/write_validation.json'
            common.scan_text(common.payload(config['write_release']), member)
            files[member], hashes[member] = config['write_release'], config['write_release_sha256']
        own_pin = digest(SELF)
        report = audit_write(config, runner, bridge, checked, observed['launch']) if config['phase'] == 'write' else audit_readout(config, runner, bridge, checked, observed['launch'])
        write_json(output/'audit.json', report)
        write_json(output/'custody.json', dict(files=hashes, exclusions=excluded, collector_sha256=own_pin,
            driver_sha256=DRIVER_SHA, helper_sha256=COMMON_SHA, checker_sha256=CHECK_SHA,
            weights_in_capsule=False, native_tokenizer_reloaded=False, model_loaded=False))
        write_new(output/'release.xml', xml.encode())
        write_json(output/'release.json', dict(phase=config['phase'], fit_seed=config['fit_seed'], gpu=gpu,
            owned_ids=observed['owned_ids'], full_release=True, observed_wall=time.time(),
            xml_sha256=digest(output/'release.xml'), plan_sha256=config['plan_sha256'], launch_sha256=config['launch_sha256'],
            proc_queue_reconciled_by=CHECK_SHA, accounting='Controller/worker clocks nested inside launch-to-vacancy; never add them.'))
        for name in ('started.json', 'audit.json', 'custody.json', 'release.xml', 'release.json'):
            path = output/name
            data = common.payload(path)
            member = 'metadata/collection/'+name
            common.scan_text(data, member)
            files[member], hashes[member] = path, hashlib.sha256(data).hexdigest()
        archive = output/'metadata.tgz'
        pin = common.pack(archive, files, hashes)
        require(status(config)['ready'], 'owned scope appeared after packing')
        bridge.checked_plan(config['root'], config['plan_sha256'])
        require(inventory(config)[1:] == (initial_hashes, initial_excluded)
            and all(digest(path) == hashes[name] for name, path in files.items()), 'custody inputs changed after packing')
        require(common.file_hash(archive) == pin and digest(SELF) == own_pin and digest(DRIVER) == DRIVER_SHA
            and digest(COMMON) == COMMON_SHA and digest(config['launcher']) == config['launcher_sha256'], 'collector/archive/dependency changed')
        if previous is not None:
            require(write_release(config, plan, observed['launch']) == previous, 'write release changed')
        final_gpu, final_xml = vacancy(plan, observed['launch']['gpu']['gpu_uuid'])
        require(status(config)['ready'], 'owned scope reappeared at publication')
        release_time = time.time()
        seconds = time.monotonic()-started
        require(seconds <= COLLECTION_SECONDS, 'collection cap exceeded')
        full_seconds = release_time-common.utc(observed['launch']['started_utc'])
        within = 0 <= full_seconds <= CAPS[config['phase']]+COLLECTION_SECONDS and release_time <= plan['lease_cutoff']
        aggregate_seconds = None if previous is None else previous['full_launch_to_final_vacancy_seconds']+full_seconds
        require(aggregate_seconds is None or aggregate_seconds >= 0, 'negative aggregate reservation')
        write_new(output/'final_release.xml', final_xml.encode())
        require(within and (aggregate_seconds is None or aggregate_seconds <= 3600),
            'phase/aggregate reservation or six-hour lease ceiling exceeded')
        accepted = report['verified']
        result = dict(status=('COLLECTED_PAIRED_WRITE' if config['phase'] == 'write' else 'COLLECTED_PROCESS_READOUT')
            if accepted else 'COLLECTED_FAILURE_NO_AGGREGATE', phase=config['phase'], fit_seed=config['fit_seed'],
            full_release=True, aggregate_available=accepted, phase_within_bound=within, archive=str(archive), archive_sha256=pin,
            files=hashes, plan_sha256=config['plan_sha256'], launch_sha256=config['launch_sha256'], driver_sha256=DRIVER_SHA,
            collector_sha256=own_pin, weights_in_capsule=False, retry=False, automatic_next_phase=False, automatic_promotion=False,
            final_vacancy=dict(gpu=final_gpu, observed_wall=release_time, xml_sha256=hashlib.sha256(final_xml.encode()).hexdigest(),
                proc_queue_reconciled_by=CHECK_SHA), collection_seconds=seconds, full_launch_to_final_vacancy_seconds=full_seconds,
            aggregate_reserved_seconds=aggregate_seconds, aggregate_reservation_ceiling_seconds=3600,
            aggregate_accounting='Only separately released write and readout launch-to-final-vacancy intervals added; CPU gaps excluded.',
            model_origin=bridge.ORIGIN, conditioning=bridge.CONDITIONING, saved_native_receipts_only=True,
            limitation='Finite saved writes and descriptive recorded-event custody, not utility, conditional learning, clean lineage or G3/P1/G5/H1/H2.')
        write_json(output/'validation.json', result)
        return {key: value for key, value in result.items() if key != 'files'}
    except BaseException as error:
        write_json(output/'failure.json', dict(error_type=type(error).__name__, phase=config['phase'], fit_seed=config['fit_seed'],
            aggregate=None, retry=False, partial_artifacts_preserved=True, collection_seconds=time.monotonic()-started))
        raise


class CollectionExpired(BaseException):
    pass


def finish(config):
    require(signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0), 'existing timer conflicts')
    def expired(number, frame):
        raise CollectionExpired('300s collection window exhausted')
    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, COLLECTION_SECONDS)
    try:
        return collect(config)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def cli_command(config, action):
    require(action in ('status', 'finish'), 'unknown collection action')
    command = [os.path.abspath(sys.executable), '-B', str(SELF), config['phase'], action]
    for key in ('fit_seed', 'root', 'plan_sha256', 'launch_root', 'launch_sha256', 'launcher', 'launcher_sha256',
                'write_release', 'write_release_sha256'):
        if config.get(key) is not None:
            command.extend(['--'+key.replace('_', '-'), str(config[key])])
    if action == 'finish':
        require(config.get('out') is not None, 'finish requires out')
        command.extend(['--out', str(config['out'])])
    return command


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=tuple(CAPS))
    parser.add_argument('action', choices=('status', 'finish'))
    parser.add_argument('--fit-seed', required=True, type=int, choices=(0, 1))
    for name in ('root', 'plan-sha256', 'launch-root', 'launch-sha256', 'launcher', 'launcher-sha256'):
        parser.add_argument('--'+name, required=True)
    for name in ('out', 'write-release', 'write-release-sha256'):
        parser.add_argument('--'+name)
    values = vars(parser.parse_args(argv))
    action = values.pop('action')
    require((action == 'finish') == (values['out'] is not None), 'finish requires out; status forbids out')
    config = settings(values)
    result = status(config) if action == 'status' else finish(config)
    result.pop('launch', None)
    print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == '__main__':
    main()
