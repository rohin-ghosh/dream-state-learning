"""Separately versioned matched AUTH/OFF projection practice; no parameter writes."""
from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.util
import json
import math
import os
from pathlib import Path, PurePosixPath
import signal
import subprocess
import sys
import time

sys.dont_write_bytecode = True
SELF = Path(os.path.abspath(__file__))
BIRTH = Path('/tmp/astra_birth_conditional_run_20260913.py')
BIRTH_SHA = '072a1333c0411a73ae0fc46c6e70de9afe0bce9b49c74e01bdaae16174195daa'
ROLE_SHA = '2cb24cf0447d3e5a7d8e61c9a0a65658e033f2c0bfc01b4b60ae15bce437a945'
PROTOCOL = 'projected_auth_off_rulegame_formation_run_v1_20260913'
PUBLIC_RECEIPT = Path('/tmp/astra_qwen_public_binding_receipt_20260913_attempt1.json')
PUBLIC_SHA = 'e87abf9c83845a32bb5df3828901dde1929e86a57fa0278158d4101b7df9a019'
CONTROLLER, WORKER, CLEANUP, COLLECT = 900, 600, 140, 300
LIMITS = dict(wake=40, record=12, parent=4, restate=4)
TOKENS = dict(wake=400, record=100, parent=200, restate=120)
CLAIMS = 'EXPLORATORY_AUTH_OFF_ACTION_PROJECTION; SOURCE_AUTHORED_BIRTH_NOT_CLEAN; no write/persistence/efficacy or P1/G3/G5/H1/H2 claim'


def load_birth():
    data = BIRTH.read_bytes()
    if hashlib.sha256(data).hexdigest() != BIRTH_SHA:
        raise ValueError('frozen birth dependency changed')
    spec = importlib.util.spec_from_file_location('born_formation_frozen_birth', BIRTH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    exec(compile(data, str(BIRTH), 'exec'), module.__dict__)
    return module


birth = load_birth()
require, path, fresh, read = birth.require, birth.path, birth.fresh, birth.read
digest, write_json, write_new, raw = birth.digest, birth.write_json, birth.write_new, birth.raw
common = birth.common


def normalize_birth(fit_root, fit_plan_sha256, fit_release, fit_release_sha256):
    root, plan = birth.read_plan(fit_root, fit_plan_sha256)
    require(plan['phase'] == 'fit', 'exact birth FIT plan required, not readout or arbitrary adapter')
    released = birth.accepted_release(fit_release, fit_release_sha256, plan, fit_plan_sha256)
    require(released['phase_complete'] is True, 'both completed AND released birth fits required')
    root, plan, api = birth.verify_plan(root, fit_plan_sha256)
    birth.audit_terminal(root, plan, api, fit_plan_sha256)
    fit = birth.verify_fit(root, plan, api, 'AUTH')
    terminal = root/'run/result.json'
    pin = dict(schema='completed_birth_adapter_pin_v1', status='COMPLETE', birth_arm='AUTH',
        birth_plan_sha256=fit_plan_sha256, completion_receipt_sha256=digest(terminal),
        child_identity=api[1].expected_identity(plan, fit['adapter']), model_files=plan['model_files'],
        origin='SOURCE_AUTHORED_BIRTH_NOT_CLEAN', model_origin=birth.ORIGIN)
    input_hashes = dict(released['evidence_hashes']) | dict(plan['input_hashes']) | {
        str(path(fit_release)): fit_release_sha256, str(root/'plan.json'): fit_plan_sha256,
        str(path(released['archive'])): released['archive_sha256'],
        str(path(fit_release).parent/'final_vacancy.xml'): released['final_vacancy_sha256']}
    return dict(pin=pin, pin_sha256=api[1].value_hash(pin), fit_root=str(root), fit_plan_sha256=fit_plan_sha256,
        fit_release=str(path(fit_release)), fit_release_sha256=fit_release_sha256,
        birth_source_root=plan['source_root'], birth_source_hashes=plan['source_hashes'],
        birth_module_sha256=plan['module_sha256'], birth_driver_sha256=BIRTH_SHA,
        input_hashes=input_hashes, auth_receipt_sha256=digest(root/'run/AUTH/receipt.json'),
        adapter_all_files=fit['adapter_files'], released_wall=released['released_wall'],
        full_release=True, both_fits_complete=True, component_pass_required=False)


def normalized_in_subprocess(fit_root, fit_plan_sha256, fit_release, fit_release_sha256):
    command = [os.path.abspath(sys.executable), '-B', str(SELF), '_birth-pin',
        '--fit-root', str(fit_root), '--fit-plan-sha256', fit_plan_sha256,
        '--fit-release', str(fit_release), '--fit-release-sha256', fit_release_sha256]
    result = subprocess.run(command, capture_output=True, text=True, timeout=300, check=True,
        env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1'))
    return json.loads(result.stdout)


def source_api(source, role_sha256):
    source = path(source)
    require(role_sha256 == ROLE_SHA and digest(source/'organism_v6/born_rulegame_formation.py') == role_sha256,
        'reviewed born role module required in newer source snapshot')
    sys.path.insert(0, str(source))
    role = importlib.import_module('organism_v6.born_rulegame_formation')
    require(path(role.__file__).parent.parent == source and role.diagnostic.REPO == source, 'cached/wrong source snapshot')
    diagnostic = role.diagnostic
    require(role.PROTOCOL == 'interaction_v3' and diagnostic.LIMITS['formation'] == LIMITS and diagnostic.TOKENS == TOKENS
        and (diagnostic.WORKER_SECONDS, diagnostic.CLEANUP_RESERVE, diagnostic.LOAD_SECONDS, diagnostic.CALL_SECONDS)
        == (WORKER, CLEANUP, 180, 120), 'existing formation/supervisor budgets changed')
    return role, diagnostic


def verify_custody(normalized, source, diagnostic):
    require(normalized['birth_driver_sha256'] == BIRTH_SHA and normalized['both_fits_complete'] is True
        and normalized['full_release'] is True and normalized['pin']['birth_arm'] == 'AUTH', 'completed AUTH custody required')
    birth.verify_pins(normalized['birth_source_hashes'])
    for name, pin in normalized['input_hashes'].items():
        require(common.file_hash(path(name)) == pin, 'upstream birth/release evidence changed')
    for name, pin in normalized['birth_source_hashes'].items():
        require(digest(path(source)/'organism_v6'/Path(name).name) == pin, 'new snapshot changed a pinned birth dependency')
    child = normalized['pin']['child_identity']
    require(diagnostic.model_hashes(child['model_input']) == normalized['pin']['model_files']
        and diagnostic.tree_hashes(child['adapter_input']) == normalized['adapter_all_files']
        and diagnostic.expected_identity({'model': child['model_input']}, child['adapter_input']) == child,
        'same base/completed AUTH adapter pins required')


def public_binding(normalized):
    require(digest(PUBLIC_RECEIPT) == PUBLIC_SHA, 'public model receipt changed')
    receipt = read(PUBLIC_RECEIPT)
    require(receipt['status'] == 'PUBLIC_REVISION_FILES_MATCHED_PROSPECTIVE_BINDING'
        and receipt['repository'] == 'Qwen/Qwen2.5-7B-Instruct'
        and receipt['revision'] == 'a09a35458c702b33eeacc393d103063234e8bc28'
        and receipt['model'] == normalized['pin']['child_identity']['model_input']
        and receipt['file_count'] == len(receipt['files']) == 14
        and {name: row['sha256'] for name, row in receipt['files'].items()} == normalized['pin']['model_files'],
        'prospective public content/local file binding mismatch')
    return dict(receipt=receipt, receipt_sha256=PUBLIC_SHA, historical_labels_preserved=True,
        clean_ancestry_claim=False)


def prepare(source, role_sha256, fit_root, fit_plan_sha256, fit_release, fit_release_sha256,
            out, device, deadline, lease_end, child_mode, controller_seconds=CONTROLLER):
    require(child_mode in ('AUTH', 'OFF'), 'explicit matched child mode required')
    root = fresh(out, (source, fit_root, fit_release, SELF, BIRTH))
    root.mkdir(mode=0o700)
    write_json(root/'preparation.started.json', dict(started_wall=time.time(), native=False, retry=False))
    try:
        normalized = normalized_in_subprocess(fit_root, fit_plan_sha256, fit_release, fit_release_sha256)
        role, diagnostic = source_api(source, role_sha256)
        verify_custody(normalized, source, diagnostic)
        child = normalized['pin']['child_identity']
        require(root != path(child['model_input']) and path(child['model_input']) not in root.parents
            and path(child['adapter_input']) not in root.parents, 'output overlaps upstream model/adapter')
        config = dict(birth.DEFAULT_CONFIG, fit_seconds=controller_seconds)
        plan = birth.make_plan(root, 'fit', source, normalized['birth_module_sha256'], child['model_input'], device,
            deadline, lease_end, config, (None, diagnostic, None, None))
        require(CLEANUP < controller_seconds <= CONTROLLER, 'formation controller cap900s; no implicit extension')
        binding = role.make_binding(normalized['pin'], expected_birth_pin_sha256=normalized['pin_sha256'],
            interface=role.projection.INTERFACE, child_mode=child_mode)
        plan.update(protocol=PROTOCOL, phase='formation', sidecar=str(SELF), sidecar_sha256=digest(SELF),
            birth_driver_sha256=BIRTH_SHA, role_sha256=role_sha256, source_hashes={str(path(source)/'organism_v6'/name): pin
                for name, pin in role.source_hashes(role.projection.INTERFACE).items()}, claims=CLAIMS, members=['formation'],
            binding=binding, binding_sha256=diagnostic.value_hash(binding), normalized=normalized,
            public_model_binding=public_binding(normalized), child_mode=child_mode,
            interface=role.projection.INTERFACE,
            limits=LIMITS, tokens=TOKENS, max_calls=60, max_output_tokens=18480,
            automatic_progression=False, teacher='same fixed base OFF', child=child_mode,
            controller_seconds=controller_seconds, collection_seconds=COLLECT)
        for key in ('main_config', 'primary_criteria', 'primary_criteria_sha256', 'generation', 'module_sha256', 'input_hashes'):
            plan.pop(key)
        write_json(root/'normalized_birth.json', normalized)
        plan['normalized_file_sha256'] = digest(root/'normalized_birth.json')
        return birth.seal_plan(root, plan)
    except BaseException as error:
        write_json(root/'prepare_failure.json', dict(error_type=type(error).__name__, retry=False))
        raise


def read_plan(root, plan_sha256):
    root = path(root)
    require(digest(root/'plan.json') == read(root/'plan.sha256.json')['sha256'] == plan_sha256, 'immutable formation plan mismatch')
    plan = read(root/'plan.json')
    require(plan['protocol'] == PROTOCOL and plan['phase'] == 'formation' and plan['root'] == str(root)
        and plan['sidecar'] == str(SELF) and plan['sidecar_sha256'] == digest(SELF) and plan['birth_driver_sha256'] == BIRTH_SHA
        and digest(BIRTH) == BIRTH_SHA and plan['python'] == os.path.abspath(sys.executable), 'runner/source/interpreter mismatch')
    require(plan['claims'] == CLAIMS and plan['origin'] == birth.ORIGIN and plan['automatic_progression'] is False
        and plan['members'] == ['formation'] and plan['limits'] == LIMITS and plan['tokens'] == TOKENS
        and plan['max_calls'] == 60 and plan['max_output_tokens'] == 18480 and plan['automatic_pass'] is False,
        'formation scope or budgets changed')
    require(plan['child_mode'] in ('AUTH', 'OFF') and plan['child'] == plan['child_mode']
        and plan['public_model_binding'] == public_binding(plan['normalized']),
        'child mode or prospective public binding changed')
    require(CLEANUP < plan['controller_seconds'] <= CONTROLLER and plan['worker_seconds'] == WORKER
        and plan['cleanup_seconds'] == CLEANUP and plan['collection_seconds'] == COLLECT
        and plan['deadline'] <= plan['lease_cutoff'] == plan['real_lease_end']-birth.LEASE_MARGIN, 'runtime/lease bounds changed')
    require(digest(root/'normalized_birth.json') == plan['normalized_file_sha256']
        and read(root/'normalized_birth.json') == plan['normalized'] and not (root/'prepare_failure.json').exists(), 'normalization seal changed')
    return root, plan


def checked_plan(root, plan_sha256):
    root, plan = read_plan(root, plan_sha256)
    birth.verify_pins(plan['source_hashes'])
    role, diagnostic = source_api(plan['source_root'], plan['role_sha256'])
    require(plan['interface'] == role.projection.INTERFACE and plan['source_hashes'] == {
        str(path(plan['source_root'])/'organism_v6'/name): pin for name, pin in role.source_hashes(role.projection.INTERFACE).items()},
        'role source inventory changed')
    verify_custody(plan['normalized'], plan['source_root'], diagnostic)
    require(plan['binding'] == role.make_binding(plan['normalized']['pin'], expected_birth_pin_sha256=plan['normalized']['pin_sha256'],
        interface=plan['interface'], child_mode=plan['child_mode'])
        and plan['binding_sha256'] == diagnostic.value_hash(plan['binding'])
        and plan['model'] == plan['binding']['birth']['child_identity']['model_input']
        and plan['model_files'] == plan['binding']['birth']['model_files'], 'role/birth/base binding mismatch')
    return root, plan, role, diagnostic


def controller_command(root, pin, python=None):
    return [python or os.path.abspath(sys.executable), '-B', str(SELF), 'formation', '--root', str(root), '--plan-sha256', pin, '--allow-gpu']


def worker_command(root, pin, hard_end, python=None):
    return [python or os.path.abspath(sys.executable), '-B', str(SELF), '_worker', '--root', str(root),
        '--plan-sha256', pin, '--hard-end', str(hard_end), '--allow-gpu']


class JournalBackend:
    def __init__(self, backend, data, diagnostic):
        self.backend, self.data, self.diagnostic = backend, data, diagnostic
        self.verifications = 0
        self.completed = []

    def identity(self, role):
        return self.backend.identity(role)

    def generate(self, request):
        stem = self.data/'calls'/request['call_id']
        write_json(str(stem)+'.request.json', dict(request=request, started=time.monotonic(),
            identity=self.identity(request['role'])))
        envelope = self.backend.generate(request)
        write_json(str(stem)+'.response.json', dict(envelope=envelope, ended=time.monotonic()))
        self.completed.append(request['call_id'])
        return envelope

    def verify(self):
        self.backend.verify()
        self.verifications += 1
        if self.verifications == 2:
            files = self.diagnostic.tree_hashes(self.data/'calls')
            require(set(files) == {call+suffix for call in self.completed for suffix in ('.request.json', '.response.json')},
                'all raw pairs required before replay')
            write_json(self.data/'capture_barrier.json', dict(calls=len(self.completed), files=files,
                completed_monotonic=time.monotonic(), replay_not_started=True))


def capture_worker(root, plan_sha256, hard_end, allow_gpu=False):
    require(allow_gpu, 'Main-only --allow-gpu required')
    pin = plan_sha256
    root, plan = read_plan(root, pin)
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == plan['device'], 'selected Main reservation required')
    stage = root/'run/formation'
    with birth.owned_worker(stage/'worker', hard_end):
        root, plan, role, diagnostic = checked_plan(root, pin)
        process = read(stage/'worker/process.json')
        require(process['argv'] == worker_command(root, pin, hard_end, plan['python']), 'owned worker command mismatch')
        cutoff = min(process['started']+process['timeout'], time.monotonic()+hard_end-time.time()-CLEANUP)
        data = fresh(stage/'data')
        data.mkdir()
        (data/'calls').mkdir()
        write_json(data/'isolation.json', dict(pid=os.getpid(), parent_pid=os.getppid(), pgid=os.getpgrp(),
            plan_sha256=pin, binding_sha256=plan['binding_sha256'], hard_end=hard_end, cutoff=cutoff,
            one_engine=True, prompt_parent=False, online_updates=False))
        backend = None
        try:
            backend = role.NativeRoleBackend(plan['binding'], expected_binding_sha256=plan['binding_sha256'], allow_gpu=True)
            write_json(data/'backend.ready.json', dict(pid=os.getpid(), ready=time.monotonic()))
            capture = role.capture_formation(JournalBackend(backend, data, diagnostic), plan['binding'],
                expected_binding_sha256=plan['binding_sha256'], cutoff=cutoff)
            write_json(data/'capture.json', capture)
        except BaseException as error:
            if isinstance(error, role.FormationFailure):
                write_json(data/'partial_capture.json', error.partial)
            write_json(data/'failure.json', dict(error_type=type(error).__name__, retry=False))
            raise
        finally:
            from organism_v6.model_backend import close_backend
            closed, error = False, None
            try:
                closed = close_backend(backend.backend if backend is not None else None)
            except Exception as failure:
                error = type(failure).__name__
            write_json(data/'backend.cleanup.json', dict(closed=closed, error=error))
            require(closed is True and error is None, 'owned backend cleanup failed')
        write_json(data/'manifest.json', dict(files=diagnostic.tree_hashes(data)))
    return dict(status='CAPTURE_COMPLETE_AWAITING_MAIN', claims=CLAIMS)


def verify_capture(root, plan, role, diagnostic):
    stage, data = root/'run/formation', root/'run/formation/data'
    process, supervision = read(stage/'worker/process.json'), read(stage/'worker/supervision.json')
    controller = read(root/'run/controller.json')
    require(process['pid'] == process['pgid'] > 1 and process['pid'] != controller['pid']
        and process['argv'] == worker_command(root, digest(root/'plan.json'), controller['hard_end'], plan['python'])
        and process['device'] == supervision['device'] == plan['device'] and 0 < process['timeout'] <= WORKER,
        'worker ownership/command mismatch')
    require(supervision['error'] is None and supervision['returncode'] == 0
        and all(supervision.get(key) is True for key in ('ok', 'owned_group_empty', 'gpu_processes_absent', 'reservation_release_verified'))
        and 0 < supervision['reserved_seconds'] <= process['timeout']+CLEANUP, 'worker/cleanup did not complete')
    require(read(data/'manifest.json')['files'] == diagnostic.tree_hashes(data, ('manifest.json',))
        and not (data/'failure.json').exists() and read(data/'backend.cleanup.json') == dict(closed=True, error=None),
        'incomplete/changed capture')
    isolated, ready = read(data/'isolation.json'), read(data/'backend.ready.json')
    require(isolated == dict(pid=process['pid'], parent_pid=controller['pid'], pgid=process['pgid'],
        plan_sha256=digest(root/'plan.json'), binding_sha256=plan['binding_sha256'], hard_end=controller['hard_end'],
        cutoff=isolated['cutoff'], one_engine=True, prompt_parent=False, online_updates=False)
        and ready['pid'] == process['pid'] and process['started'] <= ready['ready'] <= process['started']+180
        and ready['ready'] < isolated['cutoff'] <= process['started']+process['timeout'], 'isolation/load/cutoff mismatch')
    capture, barrier = read(data/'capture.json'), read(data/'capture_barrier.json')
    require(capture['cutoff'] == isolated['cutoff'] and barrier['calls'] == len(capture['calls']) <= 60
        and barrier['files'] == diagnostic.tree_hashes(data/'calls') and barrier['replay_not_started'] is True,
        'durable all-call capture barrier missing')
    costs = dict(calls=0, input_tokens=0, output_tokens=0, output_token_ceiling=0, call_seconds=0.0)
    for row in capture['calls']:
        request = row['request']
        sent = read(data/'calls'/(request['call_id']+'.request.json'))
        got = read(data/'calls'/(request['call_id']+'.response.json'))
        require(sent['request'] == request and sent['identity'] == row['identity'] and got['envelope'] == row['envelope']
            and row['started'] <= sent['started'] <= got['ended'] <= row['ended'] <= barrier['completed_monotonic']
            and row['ended']-row['started'] <= 120, 'journal/role raw call/time join mismatch')
        response = got['envelope']['response']
        costs['calls'] += 1
        costs['input_tokens'] += len(response['prompt_token_ids'])
        costs['output_tokens'] += len(response['output_token_ids'])
        costs['output_token_ceiling'] += request['max_tokens']
        costs['call_seconds'] += got['ended']-sent['started']
    require(barrier['completed_monotonic'] <= process['started']+supervision['reserved_seconds']
        and costs['output_token_ceiling'] <= 18480, 'capture window/generation budget mismatch')
    replay = role.replay_formation(capture, plan['binding'], expected_binding_sha256=plan['binding_sha256'], cutoff=isolated['cutoff'])
    return dict(status='AWAITING_MAIN_AUDIT', capture_sha256=digest(data/'capture.json'), manifest_sha256=digest(data/'manifest.json'),
        replay=replay, costs=costs, binding_sha256=plan['binding_sha256'], claims=CLAIMS,
        fit_or_write=False, retained_learning=False, component_pass_required=False)


def formation(root, plan_sha256, allow_gpu=False):
    require(allow_gpu, 'Main must separately authorize --allow-gpu formation')
    started, wall = time.monotonic(), time.time()
    root, plan = read_plan(root, plan_sha256)
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == plan['device'] and os.getpid() == os.getpgrp() == os.getsid(0),
        'Main continuous reservation and fresh controller session required')
    run = fresh(root/'run')
    run.mkdir()
    hard_end = min(wall+plan['controller_seconds'], plan['deadline'], plan['lease_cutoff'])
    try:
        with birth.work_window(hard_end):
            write_json(run/'controller.json', dict(birth.process_identity(os.getpid()), plan_sha256=plan_sha256,
                started_wall=wall, started_monotonic=started, hard_end=hard_end, continuous_reservation=True))
            root, plan, role, diagnostic = checked_plan(root, plan_sha256)
            stage = run/'formation'
            stage.mkdir()
            with birth.supervisor_window(hard_end):
                diagnostic.supervise(stage, dict(model=plan['model'], device=plan['device'], lease_end=hard_end), stage/'worker',
                    worker_command(root, plan_sha256, hard_end, plan['python']), stage/'data/calls')
            checked_plan(root, plan_sha256)
            receipt = verify_capture(root, plan, role, diagnostic)
            write_json(stage/'receipt.json', receipt)
        require(time.monotonic()-started <= plan['controller_seconds'] and time.time() <= hard_end, 'formation inclusive cap exceeded')
        result = dict(status='COMPLETE_AWAITING_MAIN_AUDIT', phase='formation', plan_sha256=plan_sha256,
            receipt_sha256=digest(stage/'receipt.json'), supervision_sha256=digest(stage/'worker/supervision.json'),
            controller_seconds=time.monotonic()-started, ended_wall=time.time(), claims=CLAIMS, automatic_progression=False)
        write_json(run/'result.json', result)
        return result
    except BaseException as error:
        write_json(run/'failure.json', dict(status='FAILED_PARTIAL', error_type=type(error).__name__, retry=False,
            controller_seconds=time.monotonic()-started, aggregate=None))
        raise


def launch_contract(root, plan, pin, launcher, launcher_sha256):
    require(digest(launcher) == launcher_sha256, 'reviewed launcher hash mismatch')
    return dict(protocol=PROTOCOL, phase='formation', root=str(root), plan_sha256=pin, driver_sha256=plan['sidecar_sha256'],
        launcher=str(path(launcher)), launcher_sha256=launcher_sha256, command=controller_command(root, pin, plan['python']),
        device=plan['device'], controller_seconds=plan['controller_seconds'], continuous_reservation=True)


def status(root, plan_sha256, launch_root=None, launch_sha256=None):
    root, plan = read_plan(root, plan_sha256)
    owned, launch = set(), None
    if launch_root is not None:
        require(digest(path(launch_root)/'launch.json') == launch_sha256, 'launch receipt hash mismatch')
        launch = read(path(launch_root)/'launch.json')
        require(launch['root'] == str(root) and launch['plan_sha256'] == plan_sha256
            and launch['driver_sha256'] == plan['sidecar_sha256'] and launch['pid'] == launch['pgid'] == launch['session'] > 1
            and launch['launcher_pid'] == launch['launcher_pgid'] == launch['launcher_session'] > 1
            and launch['pid'] != launch['launcher_pid'], 'launch ownership mismatch')
        owned.update((launch['pid'], launch['launcher_pid']))
    if (root/'run/controller.json').exists():
        controller = read(root/'run/controller.json')
        require(controller['plan_sha256'] == plan_sha256 and controller['pid'] == controller['pgid'] == controller['session'] > 1
            and (launch is None or controller['pid'] == launch['pid']), 'controller ownership mismatch')
        owned.add(controller['pid'])
    process_path = root/'run/formation/worker/process.json'
    require(set(root.glob('**/process.json')) <= {process_path}, 'unknown process receipt')
    if process_path.exists():
        process = read(process_path)
        require(process['pid'] == process['pgid'] > 1 and process['pid'] not in owned, 'worker ownership reused')
        owned.add(process['pid'])
    snapshot, descendants = common.process_snapshot(), set(owned)
    while True:
        extra = {row['pid'] for row in snapshot if row['ppid'] in descendants}-descendants
        if not extra:
            break
        descendants.update(extra)
    live = [row for row in snapshot if row['pid'] in descendants or any(row[key] in owned for key in ('pgid', 'session'))]
    markers = {name: (root/'run'/name).is_file() for name in ('result.json', 'failure.json')}
    return dict(ready=not live and sum(markers.values()) == 1, live_owned=live, terminal_markers=markers,
        terminal_bodies_read=False, launch=launch)


def inventory(root, logs):
    allowed = {'plan.json', 'plan.sha256.json', 'normalized_birth.json', 'preparation.started.json', 'prepare_failure.json',
        'collection.claim.json', 'run/controller.json', 'run/result.json', 'run/failure.json', 'run/formation/receipt.json'}
    allowed.update('run/formation/worker/'+name for name in ('process.json', 'supervision.json', 'stdout.log'))
    allowed.update('run/formation/data/'+name for name in ('isolation.json', 'backend.ready.json', 'backend.cleanup.json',
        'capture.json', 'partial_capture.json', 'failure.json', 'capture_barrier.json', 'manifest.json'))
    allowed.update(f'run/formation/data/calls/{index:04d}{suffix}' for index in range(60) for suffix in ('.request.json', '.response.json'))
    files, hashes, total, count = {}, {}, 0, 0
    for directory, prefix, permitted in ((root, 'formation', allowed),
        (logs, 'launch', {'launch.json', 'exit.json', 'gpu.xml', 'controller.log', 'launcher.log'})):
        folders = {str(parent) for name in permitted for parent in PurePosixPath(name).parents if str(parent) != '.'}
        def inaccessible(error):
            raise error
        for current, children, names in os.walk(directory, followlinks=False, onerror=inaccessible):
            for name in children+names:
                count += 1
                require(count <= 2048, 'metadata entry limit')
                item = path(Path(current)/name)
                relative = item.relative_to(directory).as_posix()
                if name in children:
                    require(relative in folders, 'unknown directory')
                    continue
                require(relative in permitted, 'unknown metadata file: '+relative)
                data = raw(item)
                archive_name = 'metadata/'+prefix+'/'+relative
                common.scan_text(data, archive_name)
                total += len(data)
                require(total <= common.MAX_TOTAL, 'metadata size limit')
                files[archive_name], hashes[archive_name] = item, hashlib.sha256(data).hexdigest()
    return files, hashes


def collect(root, plan_sha256, launch_root, launch_sha256, launcher, launcher_sha256, out):
    started, wall = time.monotonic(), time.time()
    root, logs = path(root), path(launch_root)
    output = fresh(out, (root, logs, SELF, BIRTH, launcher))
    require(output.parent == root.parent == logs.parent and 'CUDA_VISIBLE_DEVICES' not in os.environ,
        'fresh sibling outputs and released reservation environment required')
    output.mkdir(mode=0o700)
    try:
        with birth.collection_window():
            write_json(output/'started.json', dict(started_wall=wall, collection_seconds=COLLECT, retry=False))
            write_json(root/'collection.claim.json', dict(output=str(output), collector_sha256=digest(SELF)))
            observed = status(root, plan_sha256, logs, launch_sha256)
            require(observed['ready'], 'whole launcher/controller/worker/session release before terminal reads')
            root, plan, role, diagnostic = checked_plan(root, plan_sha256)
            launch = observed['launch']
            expected = launch_contract(root, plan, plan_sha256, launcher, launcher_sha256)
            require(all(launch.get(key) == value for key, value in expected.items()) and set(launch) == set(expected) |
                {'pid', 'pgid', 'session', 'launcher_pid', 'launcher_pgid', 'launcher_session', 'started_wall', 'gpu_uuid'},
                'launcher exact fields/custody mismatch')
            exited = read(logs/'exit.json')
            require(set(exited) == {'launch_sha256', 'returncode', 'ended_wall'} and exited['launch_sha256'] == launch_sha256
                and type(exited['returncode']) is int and math.isfinite(launch['started_wall']) and math.isfinite(exited['ended_wall'])
                and plan['normalized']['released_wall'] <= launch['started_wall'] <= exited['ended_wall'] <= time.time(),
                'birth release/formation launch/exit join mismatch')
            files, hashes = inventory(root, logs)
            gpu, xml = birth.vacancy(plan, launch['gpu_uuid'])
            write_new(output/'initial_vacancy.xml', xml.encode())
            successful = (root/'run/result.json').exists()
            require((exited['returncode'] == 0) == successful, 'exit/terminal mismatch')
            terminal = read(root/'run'/('result.json' if successful else 'failure.json'))
            report = dict(phase_complete=False, aggregate=None, claims=CLAIMS, costs_nested_not_added=True)
            if successful:
                controller = read(root/'run/controller.json')
                require(controller['argv'] == expected['command'] and all(controller[key] == launch[key] for key in ('pid', 'pgid', 'session'))
                    and launch['started_wall'] <= controller['started_wall'] <= terminal['ended_wall'] <= controller['hard_end']
                    and terminal['plan_sha256'] == plan_sha256 and terminal['claims'] == CLAIMS
                    and terminal['status'] == 'COMPLETE_AWAITING_MAIN_AUDIT' and terminal['automatic_progression'] is False
                    and 0 < terminal['controller_seconds'] <= plan['controller_seconds'], 'controller/terminal join mismatch')
                receipt = verify_capture(root, plan, role, diagnostic)
                require(read(root/'run/formation/receipt.json') == receipt and terminal['receipt_sha256'] == digest(root/'run/formation/receipt.json')
                    and terminal['supervision_sha256'] == digest(root/'run/formation/worker/supervision.json'), 'terminal/capture receipt changed')
                report.update(phase_complete=True, formation=receipt, controller_seconds=terminal['controller_seconds'])
            else:
                require(terminal['status'] == 'FAILED_PARTIAL' and terminal['retry'] is False and terminal['aggregate'] is None,
                    'failed phase must not be promoted')
                report['failure'] = terminal
            write_json(output/'audit.json', report)
            for name in ('started.json', 'initial_vacancy.xml', 'audit.json'):
                item = output/name
                common.scan_text(raw(item), name)
                files['metadata/collection/'+name], hashes['metadata/collection/'+name] = item, digest(item)
            archive = output/'capsule.tgz'
            archive_sha = common.pack(archive, files, hashes)
            require(status(root, plan_sha256, logs, launch_sha256)['ready'], 'owned processes reappeared')
            final_gpu, final_xml = birth.vacancy(plan, launch['gpu_uuid'])
            write_new(output/'final_vacancy.xml', final_xml.encode())
            require(inventory(root, logs)[1] == {name: pin for name, pin in hashes.items() if not name.startswith('metadata/collection/')},
                'metadata inventory changed during collection')
            birth.verify_pins({str(item): hashes[name] for name, item in files.items()})
            require(common.file_hash(archive) == archive_sha, 'archive changed')
            elapsed, released = time.monotonic()-started, time.time()
            require(elapsed <= COLLECT and 0 <= released-launch['started_wall'] <= plan['controller_seconds']+COLLECT
                and released <= plan['lease_cutoff'], 'inclusive phase/collection/lease bound exceeded')
            validation = dict(protocol=PROTOCOL, status='COLLECTED_RELEASED', root=str(root), plan_sha256=plan_sha256,
                collector_sha256=digest(SELF), phase_complete=successful, full_release=True, archive=str(archive), archive_sha256=archive_sha,
                archive_files=hashes, final_vacancy=final_gpu, final_vacancy_sha256=digest(output/'final_vacancy.xml'),
                released_wall=released, collection_seconds=elapsed, launch_to_release_seconds=released-launch['started_wall'],
                costs_nested_not_added=True, claims=CLAIMS, automatic_progression=False, archived_adapter_bytes=False,
                evidence_hashes={str(item): hashes[name] for name, item in files.items()},
                terminal_sha256=digest(root/'run'/('result.json' if successful else 'failure.json')))
            write_json(output/'validation.json', validation)
            return dict(validation=str(output/'validation.json'), validation_sha256=digest(output/'validation.json'),
                archive=str(archive), archive_sha256=archive_sha, phase_complete=successful)
    except BaseException as error:
        write_json(output/'collection_failure.json', dict(error_type=type(error).__name__, retry=False, accepted_release=False,
            partial_archive_preserved=(output/'capsule.tgz').exists()))
        raise


def verified_release(root, plan_sha256, release, release_sha256):
    root, plan = read_plan(root, plan_sha256)
    release = path(release)
    require(release.name == 'validation.json' and digest(release) == release_sha256
        and not (release.parent/'collection_failure.json').exists(), 'release pin/failure mismatch')
    receipt = read(release)
    require(receipt['protocol'] == PROTOCOL and receipt['status'] == 'COLLECTED_RELEASED'
        and receipt['phase_complete'] is True and receipt['full_release'] is True and receipt['root'] == str(root)
        and receipt['plan_sha256'] == plan_sha256 and receipt['collector_sha256'] == digest(SELF)
        and receipt['claims'] == CLAIMS and receipt['automatic_progression'] is False
        and receipt['terminal_sha256'] == digest(root/'run/result.json') and not (root/'run/failure.json').exists(),
        'completed formation/release custody mismatch')
    require(receipt['archive'] == str(release.parent/'capsule.tgz') and common.file_hash(path(receipt['archive'])) == receipt['archive_sha256']
        and digest(release.parent/'final_vacancy.xml') == receipt['final_vacancy_sha256'], 'release archive/vacancy changed')
    common.validate_archive(path(receipt['archive']), receipt['archive_files'])
    common.check_uuid(receipt['final_vacancy'], raw(release.parent/'final_vacancy.xml').decode(), receipt['final_vacancy']['gpu_uuid'])
    birth.verify_pins(receipt['evidence_hashes'])
    require(0 <= receipt['collection_seconds'] <= COLLECT and 0 <= receipt['launch_to_release_seconds']
        <= plan['controller_seconds']+COLLECT, 'release clock mismatch')
    root, plan, role, diagnostic = checked_plan(root, plan_sha256)
    capture = verify_capture(root, plan, role, diagnostic)
    require(capture == read(root/'run/formation/receipt.json'), 'released capture receipt mismatch')
    return dict(root=str(root), plan=plan, release=receipt, formation_receipt=capture,
        capture_path=str(root/'run/formation/data/capture.json'), binding=plan['binding'],
        binding_sha256=plan['binding_sha256'], normalized_birth=plan['normalized'])


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    prepare_parser = commands.add_parser('prepare')
    for name in ('source', 'role-sha256', 'fit-root', 'fit-plan-sha256', 'fit-release', 'fit-release-sha256',
                 'out', 'device', 'deadline', 'lease-end', 'child-mode'):
        prepare_parser.add_argument('--'+name, required=True)
    prepare_parser.add_argument('--controller-seconds', type=int, default=CONTROLLER)
    normalize = commands.add_parser('_birth-pin')
    for name in ('fit-root', 'fit-plan-sha256', 'fit-release', 'fit-release-sha256'):
        normalize.add_argument('--'+name, required=True)
    for name in ('formation', '_worker', 'status', 'collect'):
        command = commands.add_parser(name)
        command.add_argument('--root', required=True)
        command.add_argument('--plan-sha256', required=True)
        if name in ('formation', '_worker'):
            command.add_argument('--allow-gpu', action='store_true')
        if name == '_worker':
            command.add_argument('--hard-end', type=float, required=True)
        if name in ('status', 'collect'):
            command.add_argument('--launch-root', required=name == 'collect')
            command.add_argument('--launch-sha256', required=name == 'collect')
        if name == 'collect':
            for field in ('launcher', 'launcher-sha256', 'out'):
                command.add_argument('--'+field, required=True)
    return parser


def main(argv=None):
    args = vars(build_parser().parse_args(argv))
    name = args.pop('command')
    result = {'prepare': prepare, '_birth-pin': normalize_birth, 'formation': formation, '_worker': capture_worker,
              'status': status, 'collect': collect}[name](**args)
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return result


if __name__ == '__main__':
    main()
