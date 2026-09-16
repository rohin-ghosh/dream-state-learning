"""F2-only saved-state handoff and future-only existing A2 Astra transport."""

import argparse
from copy import deepcopy
import fcntl
import hashlib
import importlib
import importlib.util
import inspect
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from types import FunctionType, SimpleNamespace


OLD_ROOT = Path('/localhome/local-rohing/orch_math_feedback_uptake_r124_readout_20260915_attempt1/F2')
OLD_SOURCE = Path('/localhome/local-rohing/orch_math_feedback_uptake_r124_readout_source_20260915_v1')
ROOT = Path('/localhome/local-rohing/orch_r139_math_astra_handoff_20260916_v1/F2')
SOURCE = Path('/localhome/local-rohing/orch_r139_math_astra_handoff_source_20260916_v1')
QUEUE = Path('/localhome/local-rohing/orch_math_feedback_uptake_r115_f2_20260915_attempt1/lane1')
OLD_CONFIG = Path('/localhome/local-rohing/orch_r124_parent_transport_contract_20260915_v1/F2_math_r124/CONFIG.json')
CONFIG_SHA = 'c10d508ea7377eaa442ca7161ada2f2713a5986ce00fd2c11218ddd867071621'
PLAN_SHA = 'e545e854f759f4bc00104603b4231c5eebcdd45774185a3a92fd5ef18404263d'
HOST_SHA = '0cb7eb43862102b79ae0a30d2babfedfbf9598b31967a1a04122c3cf849c746d'
UUID = 'GPU-7fc4e5b2-060c-ada8-8f91-3fe262c3573c'
MODEL = 'openai/openai/gpt-6-astra'
MODULE = 'gpu.orch_r139_math_astra_handoff'
DIRECTIVE = 'bb2f2eb9:COORDINATION_2026-09-16T02:35Z'
BROKER_OLD = Path('/tmp/orch_math_feedback_uptake_r121_astra_source_20260915_v1')
A2_STAGE = Path('/data/home/rohing/courier/runtime/r137_a2_request_repair_v3')
BROKER_STAGE = Path('/data/home/rohing/courier/runtime/r139_f2_astra_handoff_v1')
PINS = {
    'gpu/orch_math_feedback_uptake_r124_boundary.py': 'e462545f323fedf9cbc7f7a6d5fdde23f983a705b418e2c45550202bdf2ae35b',
    'gpu/orch_math_feedback_uptake_r124_readout.py': 'a161b2121624350fc026ad39e0a4fb45997b8e91ca58adfbdd4be6d40e858011',
    'gpu/orch_math_feedback_uptake_r121_independent.py': 'dafb827518ec1417c4a59431a39fcd89d334a50ad840c47e3cd329335c560a02',
    'gpu/orch_math_feedback_uptake_r121_independent_native.py': '2f73bf7f00ec42cdef24fae97b60143c4a5f97b6501eaa78a494f899715242c9',
}


def require(condition, code):
    if not condition:
        raise ValueError(code)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n')


def ref(path):
    return dict(path=str(Path(path).resolve(strict=True)), sha256=sha(path))


def checked(reference):
    require(sha(reference['path']) == reference['sha256'], 'immutable_reference')
    return read(reference['path'])


def slot(plan):
    require(hashlib.sha256(socket.gethostname().encode()).hexdigest() == HOST_SHA, 'exact_slot_host_hash')
    require(plan['branch'] == 'F2' and plan['index'] == 1 and plan['uuid'] == UUID,
        'exact_F2_slot_UUID')
    require(plan['original_root'] == str(QUEUE), 'original_F2_queue')


def native_modules():
    require(Path(__file__).resolve() == SOURCE / (MODULE.replace('.', '/') + '.py'), 'immutable_native_wrapper')
    for name, expected in PINS.items():
        require(sha(OLD_SOURCE/name) == sha(SOURCE/name) == expected, 'frozen_native_dependency')
    sys.path.insert(0, str(SOURCE))
    run = importlib.import_module('gpu.orch_math_feedback_uptake_r124_readout')
    boundary = importlib.import_module('gpu.orch_math_feedback_uptake_r124_boundary')
    require(Path(run.__file__).resolve() == SOURCE/'gpu/orch_math_feedback_uptake_r124_readout.py', 'native_import_scope')
    return run, boundary


def owned_actor(root, pinned):
    require(Path(root) == OLD_ROOT and sha(OLD_ROOT/'PLAN.json') == PLAN_SHA, 'original_native_plan')
    plan, launch = read(OLD_ROOT/'PLAN.json'), read(OLD_ROOT/'LAUNCH.json')
    slot(plan)
    recorded = launch['identity']
    actual = pinned.identity(recorded['pid'])
    require(all(str(actual[key]) == str(value) for key, value in recorded.items()), 'same_PID_start_boot_command_UID')
    require(actual['uid'] == os.getuid() and actual['cwd'] == str(OLD_SOURCE), 'original_UID_cwd')
    process = Path('/proc')/str(actual['pid'])
    require((process/'cmdline').read_bytes().split(b'\0')[-6:] == [b'-m',
        b'gpu.orch_math_feedback_uptake_r124_readout', b'resident', b'--root', str(OLD_ROOT).encode(), b''],
        'exact_R124_F2_actor')
    environment = (process/'environ').read_bytes().split(b'\0')
    require(('CUDA_VISIBLE_DEVICES='+UUID).encode() in environment
        and ('PYTHONPATH='+str(OLD_SOURCE)).encode() in environment, 'original_source_GPU_environment')
    executable = (process/'exe').stat()
    return dict(actual, exe_device=executable.st_dev, exe_inode=executable.st_ino)


def verify_source():
    manifest = read(SOURCE/'R139_SOURCE_MANIFEST.json')
    for name, expected in manifest.items():
        require(not Path(name).is_absolute() and '..' not in Path(name).parts, 'relative_source_file')
        require(sha(SOURCE/name) == expected, 'native_source_manifest')
    require(read(SOURCE/'R139_CPU_TESTS.json')['passed'] is True, 'native_CPU_tests')
    return manifest


def prepare():
    _, boundary = native_modules()
    verify_source()
    require(sha(OLD_ROOT/'PLAN.json') == PLAN_SHA and sha(OLD_CONFIG) == CONFIG_SHA, 'frozen_originals')
    prior = read(OLD_ROOT/'PLAN.json')
    actor = owned_actor(OLD_ROOT, boundary.pinned)
    require(not (OLD_ROOT/'TERMINAL.json').exists() and not (OLD_ROOT/'GUARD_TERMINAL.json').exists(), 'live_original_required')
    ROOT.mkdir(parents=True, exist_ok=False)
    request = dict(schema='R139_F2_SAVED_STATE_HANDOFF_V1', approved_intake=DIRECTIVE,
        requested_scope='F2_NO_RESET_PROSPECTIVE_PARENT_MODEL_CHOICE', branch='F2', root=str(ROOT),
        predecessor_root=str(OLD_ROOT), predecessor_plan=ref(OLD_ROOT/'PLAN.json'), actor=actor,
        source_root=str(SOURCE), source_manifest=ref(SOURCE/'R139_SOURCE_MANIFEST.json'),
        tests=ref(SOURCE/'R139_CPU_TESTS.json'), index=1, uuid=UUID, host_sha256=HOST_SHA,
        bounds=prior['bounds'], observed_counters=read(OLD_ROOT/'COUNTERS.json'),
        created_unix=time.time(), boundary_expires_unix=min(time.time()+3600, prior['bounds']['train_end_unix']-1200))
    write(ROOT/'REQUEST.json', request)
    write(ROOT/'MAIN_GO_TEMPLATE.json', dict(authorized=False, request_sha256=sha(ROOT/'REQUEST.json'),
        source_manifest_sha256=sha(SOURCE/'R139_SOURCE_MANIFEST.json'), publication='', approved_intake=DIRECTIVE))
    return dict(status='CPU_PREPARED_NO_SIGNALS_NO_LAUNCH', request=ref(ROOT/'REQUEST.json'),
        actor={key:actor[key] for key in ('pid','start_ticks','boot_id','uid','command_sha256')},
        counters=request['observed_counters'], boundary_is_activation=False)


def authorize():
    verify_source()
    go = read(ROOT/'MAIN_GO.json')
    require(go['authorized'] is True and bool(go['publication'].strip()) and go['approved_intake'] == DIRECTIVE,
        'Main_publication_required')
    require(go['request_sha256'] == sha(ROOT/'REQUEST.json') and
        go['source_manifest_sha256'] == sha(SOURCE/'R139_SOURCE_MANIFEST.json'), 'exact_Main_bound_bytes')


def release_source(text):
    start = "                with (root/'GUARD.log').open('x') as log:\n"
    end = '                return\n'
    require(text.count(start) == text.count(end) == 1, 'exact_R124_release_tail')
    before, tail = text.split(start)
    omitted, after = tail.split(end)
    require('subprocess.Popen' in omitted and 'SUCCESSOR_GUARD_DISPATCHED.json' in omitted, 'only_guard_launch_removed')
    result = before + end + after
    require('subprocess.Popen' not in result, 'release_never_launches')
    return result


def history_at(run, prior, cycle):
    history = run.control.checked(prior['initial_history'])
    first = prior['contract']['next_cycle']
    for number in range(first, cycle+1):
        output = OLD_ROOT/f'cycle{number:06d}'
        sleep = read(output/'sleep/COMPLETE.json')
        require(sleep['checkpoint'] == read(OLD_ROOT/'COMMITTED.json')['checkpoint'] if number == cycle else True,
            'latest_saved_sleep')
        rows = read(output/'ROWS.json')
        require(len(rows) == 6, 'six_original_rows_per_cycle')
        history.extend(rows)
    for row in history:
        require(sha(row['source_call_path']) == row['source_call_sha256'], 'exact_history_source')
    require(len({row['source_call_sha256'] for row in history}) == len(history), 'history_append_once')
    return history


def successor_plan(prior, request, release, history, carry):
    plan = deepcopy(prior)
    plan.update(root=str(ROOT), source_root=str(SOURCE), source_manifest=request['source_manifest'], tests=request['tests'],
        initial_history=history, initial_carry=carry, release=ref(ROOT/'RELEASED.json'),
        predecessor_root=str(OLD_ROOT), predecessor_plan=request['predecessor_plan'], preserved=release['preserved'],
        parent_models=[MODEL], created_unix=time.time(),
        r139_segment=dict(kind='SAVED_STATE_NEW_PARENT_MODEL_SEGMENT_NOT_RESET', actual_parent_model=MODEL,
            approved_intake=DIRECTIVE, optimizer_reset=False, adapter_reset=False,
            cpu_cuda_rng='EXACT_SAVED_STATE', history='EXACT_HISTORY_EXTEND', carry='WHOLE_SAVED_CARRY',
            old_pending='ARCHIVED_NEVER_REINJECTED', historical_replay=False, boundary=ref(ROOT/'BOUNDARY.json')))
    plan['contract'].update(initial_checkpoint=release['checkpoint'],
        initial_optimizer_steps=release['counters']['optimizer_steps'], inherited_counters=release['counters'],
        next_cycle=release['next_cycle'])
    return plan


def inventory(root):
    root = Path(root)
    with (root/'LEDGER.lock').open('r') as lock:
        fcntl.flock(lock, fcntl.LOCK_SH)
        reservations = {}
        for path in (root/'reservations').glob('parent_*.json'):
            value = read(path)
            reservations[value['metadata']['id']] = value
        requests = []
        for path in sorted((QUEUE/'parent_queue').glob('*.request.json')):
            identifier = path.name.removesuffix('.request.json')
            requests.append(dict(id=identifier, sha256=sha(path), reservation=reservations.get(identifier),
                response=path.with_name(identifier+'.response.json').exists(),
                partial=path.with_name(identifier+'.response.json.partial').exists(),
                claim=(QUEUE/'parent_claude'/(identifier+'.claim')).exists(),
                delivered=(root/'parent_delivered'/(identifier+'.json')).exists()))
        claims = list((QUEUE/'parent_claude').glob('*.claim'))
        historical = set(row['id'] for row in requests)
        historical.update(path.name.removesuffix('.claim') for path in claims)
        return dict(observed_unix=time.time(), counters=read(root/'COUNTERS.json'), requests=requests,
            historical_ids=sorted(historical), host_sha256=HOST_SHA, plan_sha256=sha(root/'PLAN.json'),
            unfinished_claims=[path.name for path in claims if not (path/'PUBLISHED.json').exists()],
            runner_lock=(QUEUE/'parent_claude/RUNNER.lock').exists(), terminal=(root/'TERMINAL.json').exists())


def build_successor(request, release):
    run, _ = native_modules()
    prior = checked(request['predecessor_plan'])
    history = history_at(run, prior, release['cycle'])
    write(ROOT/'HISTORY_INITIAL.json', history)
    write(ROOT/'CARRY_INITIAL.json', read(OLD_ROOT/f'cycle{release["cycle"]:06d}/CARRY.json'))
    write(ROOT/'COUNTERS.json', release['counters'])
    write(ROOT/'COMMITTED.json', read(OLD_ROOT/'COMMITTED.json'))
    (ROOT/'LEDGER.lock').touch(exist_ok=False)
    preserved = {}
    for folder in ('parent_pending', 'parent_delivered', 'reservations'):
        (ROOT/folder).mkdir(exist_ok=False)
        for path in sorted((OLD_ROOT/folder).glob('*.json')):
            destination = ROOT/'historical'/folder/path.name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, destination)
            require(sha(path) == sha(destination), 'archived_original_bytes')
            preserved[str(path)] = sha(path)
    observed = inventory(OLD_ROOT)
    require(observed['counters'] == release['counters'], 'exact_release_counters')
    epoch = dict(observed_unix=observed['observed_unix'], parent_high_water=release['counters']['parent'],
        counters=release['counters'], historical_ids=observed['historical_ids'],
        request_inventory_sha256=digest(observed['requests']), host_sha256=HOST_SHA,
        predecessor_plan_sha256=PLAN_SHA, next_cycle=release['next_cycle'], archive_preserved=preserved,
        no_historical_replay=True, activation='AFTER_EXACT_PIDFD_RELEASE_BEFORE_ANY_NEW_REQUEST')
    write(ROOT/'BOUNDARY.json', epoch)
    plan = successor_plan(prior, request, release, ref(ROOT/'HISTORY_INITIAL.json'), ref(ROOT/'CARRY_INITIAL.json'))
    write(ROOT/'PLAN.json', plan)
    write(ROOT/'READY.json', dict(plan=ref(ROOT/'PLAN.json'), boundary=ref(ROOT/'BOUNDARY.json'),
        actual_pidfd_exit=True, no_GPU_calls=True, no_launch=True))


def release():
    authorize()
    run, boundary = native_modules()
    values = dict(vars(boundary))
    values['owned_actor'] = lambda root: owned_actor(root, boundary.pinned)
    values['check_actor'] = lambda request: require(values['owned_actor'](request['predecessor_root']) == request['actor'], 'no_PID_reuse_or_exec')
    values['run'] = SimpleNamespace(ROOT=ROOT.parent, SOURCE=SOURCE, MODULE=MODULE, build_successor=build_successor)
    exec(compile(release_source(inspect.getsource(boundary.execute)), '<R139_bound_R124_release>', 'exec'), values)
    values['execute']('F2')
    return dict(status='RELEASED_NOT_LAUNCHED' if (ROOT/'READY.json').exists() else 'NO_SAFE_BOUNDARY',
        ready=ref(ROOT/'READY.json') if (ROOT/'READY.json').exists() else None)


def validate(root):
    require(Path(root) == ROOT, 'exact_new_F2_root')
    authorize()
    plan = read(ROOT/'PLAN.json')
    slot(plan)
    require(plan['root'] == str(ROOT) and plan['source_root'] == str(SOURCE), 'actual_successor_source')
    for key in ('source_manifest','tests','initial_history','initial_carry','release','predecessor_plan','train','dev','final','clock'):
        checked(plan[key])
    epoch = checked(plan['r139_segment']['boundary'])
    require(epoch['host_sha256'] == HOST_SHA and epoch['no_historical_replay'] is True, 'exact_boundary')
    for name, expected in {**{str(OLD_ROOT/name):value for name,value in plan['preserved'].items()}, **epoch['archive_preserved']}.items():
        require(sha(name) == expected, 'preserved_original_state_and_dispositions')
    original = read(OLD_ROOT/'PLAN.json')
    allowed = {'root','source_root','source_manifest','tests','initial_history','initial_carry','release',
        'predecessor_root','predecessor_plan','preserved','parent_models','created_unix','r139_segment','contract'}
    require({key:value for key,value in plan.items() if key not in allowed} ==
        {key:value for key,value in original.items() if key not in allowed}, 'no_other_plan_policy_change')
    changed = {'initial_checkpoint','initial_optimizer_steps','inherited_counters','next_cycle'}
    require({key:value for key,value in plan['contract'].items() if key not in changed} ==
        {key:value for key,value in original['contract'].items() if key not in changed}, 'unchanged_contract')
    require(plan['parent_models'] == [MODEL] and time.time() < plan['bounds']['hard_end_unix'], 'model_and_original_wall')
    checkpoint = plan['contract']['initial_checkpoint']
    require(sha(checkpoint['path']) == checkpoint['path_sha256'] and
        sha(checkpoint['optimizer_path']) == checkpoint['optimizer_path_sha256'], 'saved_adapter_AdamW_RNG')
    return plan


def final_seen(root, key):
    seen = set()
    while root and str(root) not in seen:
        root = Path(root)
        seen.add(str(root))
        if (root/'sealed'/key).exists():
            return True
        if not (root/'PLAN.json').exists():
            break
        root = read(root/'PLAN.json').get('predecessor_root')
    return False


def run_native(phase, binding=None):
    run, _ = native_modules()
    run.control.ROOT, run.control.SOURCE, run.control.MODULE, run.control.validate = ROOT.parent, SOURCE, MODULE, validate
    if phase == 'guard':
        validate(ROOT)
        ready = read(ROOT/'BROKER_ACTIVE.json')
        require(ready['boundary_sha256'] == sha(ROOT/'BOUNDARY.json') and ready['model'] == MODEL, 'prospective_broker_ready_first')
        require(not (ROOT/'LAUNCH.json').exists(), 'single_successor_activation')
        run.old.guard(ROOT)
    elif phase == 'scan':
        return run.old.scan(ROOT)
    elif phase == 'readout':
        run.old.readout(ROOT, binding)
    else:
        def readout(root, actor, plan, checkpoint, key, split='DEV'):
            if split == 'FINAL' and final_seen(root, key):
                return None
            return run.offloaded_readout(root, actor, plan, checkpoint, key, split)
        values = dict(run.resident.__globals__, validate=validate, paired_probe=lambda root, plan: None,
            offloaded_readout=readout)
        FunctionType(run.resident.__code__, values, 'saved_state_resident', run.resident.__defaults__)(ROOT)


def remote(arguments):
    command = 'CUDA_VISIBLE_DEVICES= PYTHONPATH='+shlex.quote(str(SOURCE))+' python3 -B -m '+MODULE+' '+arguments
    result = subprocess.run(['bash', str(BROKER_OLD/'gpu/ovx3_ssh.sh'), command], capture_output=True, text=True, timeout=60)
    require(result.returncode == 0, 'bounded_native_metadata_command_failed')
    return json.loads(result.stdout)


def broker_config(original, pins):
    extras = {'parent_effort','predecessor_config','provider_lock_scope','queue_transport','terminal_binding','terminal_filename'}
    config = {key:deepcopy(value) for key,value in original.items() if key not in extras}
    config['source_files'] = pins
    require(config['remote_root'] == str(QUEUE) and config['branch'] == 'F2' and config['family'] == 'math', 'F2_only_config')
    require(config['max_parent_calls'] == 384 and config['max_output_tokens'] == 8192
        and config['deadline_unix'] == 1789596120 and config['max_budget_usd'] == 1.0, 'original_F2_budgets_not_A2')
    return config


def broker_imports():
    source = BROKER_STAGE/'source'
    sys.path.insert(0, str(source))
    active = importlib.import_module('gpu.orch_math_feedback_uptake_r121_astra')
    require(Path(active.__file__).resolve() == source/'gpu/orch_math_feedback_uptake_r121_astra.py', 'frozen_A2_transport_import')
    specification = importlib.util.spec_from_file_location('r139_pinned_A2_helpers', BROKER_STAGE/'r137_helper.py')
    helper = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(helper)
    return active, helper


def prompt_receipt(active, config):
    prompt = Path('/data/home/rohing/courier/swarm/prompts/F2.md')
    require(prompt.stat().st_size <= active.base.PACKET_CAP, 'bounded_existing_F2_prompt')
    binding = active.base.head_binding(prompt, prompt.read_bytes())
    principles = BROKER_STAGE/'source/research_notes/PARENTING_PRINCIPLES_ROHIN_2026-09-15.md'
    require(sha(principles) == config['principles_sha256'], 'unchanged_principles')
    provider_file = Path.home()/'.codex/nvidia-astra.config.toml'
    settings = active.low_settings(provider_file.read_text())
    provider = settings['model_providers'][settings['model_provider']]
    require(provider['wire_api'] == 'responses' and provider['base_url'] == 'https://inference-api.nvidia.com/v1'
        and provider['env_key'] == 'NVIDIA_API_KEY', 'unchanged_existing_A2_provider')
    return dict(prompt_sha256=sha(prompt), fields_sha256=binding['settings_file_sha256'],
        binding_status=binding['status'], principles_sha256=sha(principles),
        provider_file_sha256=sha(provider_file), model=MODEL, reasoning_effort='low')


def broker_stage():
    require(sha(A2_STAGE/'orch_r137_math_request_repair.py') == '31691422dff7f597fd4ebbf15521d45f6d64bf1ce9479953c44e16fc6bc459c6', 'A2_v3_helper_pin')
    a2 = read(A2_STAGE/'MANIFEST.json')
    require(sha(A2_STAGE/'MANIFEST.json') == 'bb3ab4b49faf867c6c936922a6b5e0bcdd009bd5a697d70309db1ddd619cf713', 'A2_v3_manifest_pin')
    BROKER_STAGE.mkdir(mode=0o700, exist_ok=False)
    files = {}
    for name, pins in a2['source_files'].items():
        require(sha(A2_STAGE/'source'/name) == pins['sha256'], 'unchanged_A2_source')
        destination = BROKER_STAGE/'source'/name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(A2_STAGE/'source'/name, destination)
        files[name] = sha(destination)
    shutil.copyfile(A2_STAGE/'orch_r137_math_request_repair.py', BROKER_STAGE/'r137_helper.py')
    shutil.copyfile(__file__, BROKER_STAGE/'orch_r139_math_astra_handoff.py')
    command = 'cat '+shlex.quote(str(OLD_CONFIG))
    result = subprocess.run(['bash', str(BROKER_OLD/'gpu/ovx3_ssh.sh'), command], capture_output=True, timeout=30)
    require(result.returncode == 0 and hashlib.sha256(result.stdout).hexdigest() == CONFIG_SHA, 'original_F2_broker_config')
    original = json.loads(result.stdout)
    write(BROKER_STAGE/'ORIGINAL_CONFIG.json', original)
    active, _ = broker_imports()
    config = broker_config(original, active.base.source_pins())
    active.base.validate_config(config)
    write(BROKER_STAGE/'CONFIG.json', config)
    write(BROKER_STAGE/'PROMPT_CHECK.json', prompt_receipt(active, config))
    native = remote('check')
    write(BROKER_STAGE/'NATIVE_PREPARATION.json', native)
    write(BROKER_STAGE/'MANIFEST.json', dict(schema='R139_F2_EXISTING_A2_TRANSPORT_V1',
        source_files=files, wrapper=ref(BROKER_STAGE/'orch_r139_math_astra_handoff.py'),
        helper=ref(BROKER_STAGE/'r137_helper.py'), config=ref(BROKER_STAGE/'CONFIG.json'),
        prompt_check=ref(BROKER_STAGE/'PROMPT_CHECK.json'),
        original_config=ref(BROKER_STAGE/'ORIGINAL_CONFIG.json'), native=ref(BROKER_STAGE/'NATIVE_PREPARATION.json'),
        old_config_sha256=CONFIG_SHA, original_A2_manifest_sha256=sha(A2_STAGE/'MANIFEST.json'),
        provider_model=MODEL, reasoning_effort='low', no_calls=True))
    write(BROKER_STAGE/'MAIN_GO_TEMPLATE.json', dict(schema='ORCH_R111_FABLE_LAUNCH_V1', authorized=False,
        authorization='WATCHER_RELAYED_ROHIN_DONE', source_reference='', config_sha256=digest(config), not_before_unix=0))
    return dict(status='CONTROLLER_CPU_STAGED_NOT_LAUNCHED', manifest=ref(BROKER_STAGE/'MANIFEST.json'))


def broker_check(expected):
    require(sha(BROKER_STAGE/'MANIFEST.json') == expected, 'broker_manifest')
    manifest = read(BROKER_STAGE/'MANIFEST.json')
    require(sha(__file__) == manifest['wrapper']['sha256'], 'broker_running_wrapper')
    for name, expected_hash in manifest['source_files'].items():
        require(sha(BROKER_STAGE/'source'/name) == expected_hash, 'broker_source_pin')
    for key in ('config','original_config','native','prompt_check'):
        checked(manifest[key])
    require(sha(manifest['helper']['path']) == manifest['helper']['sha256'], 'broker_helper_pin')
    active, helper = broker_imports()
    config = read(BROKER_STAGE/'CONFIG.json')
    require(config == broker_config(read(BROKER_STAGE/'ORIGINAL_CONFIG.json'), active.base.source_pins()), 'unchanged_F2_policy')
    active.base.validate_config(config)
    prompt = prompt_receipt(active, config)
    require(prompt['provider_file_sha256'] == checked(manifest['prompt_check'])['provider_file_sha256'],
        'unchanged_pinned_provider_file')
    observed = remote('check')
    preparation = read(BROKER_STAGE/'NATIVE_PREPARATION.json')
    require(observed['request'] == preparation['request'] and observed['host_sha256'] == HOST_SHA, 'native_bound_preparation')
    return active, helper, config, observed


def eligible(row, epoch):
    if row['id'] in epoch['historical_ids'] or any(row[key] for key in ('response','partial','claim','delivered')):
        return False
    reservation = row.get('reservation')
    if not reservation:
        return False
    require(re.fullmatch(r'R121_C[0-9]{6}_E[01]_experience', row['id']) is not None, 'native_experience_only')
    require(reservation['count'] == 1 and reservation['kind'] == 'parent' and
        reservation['metadata']['id'] == row['id'], 'exact_parent_reservation')
    return (reservation['first'] > epoch['parent_high_water'] and reservation['reserved_unix'] > epoch['observed_unix']
        and int(row['id'][6:12]) >= epoch['next_cycle'])


def broker_serve(expected):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_broker_only')
    active, helper, config, observed = broker_check(expected)
    require(shutil.disk_usage(BROKER_STAGE).free >= 10 * 1024 ** 3, 'data_disk_launch_floor')
    require(observed['released'] and not observed['launched'], 'release_then_broker_then_child')
    launch_path = BROKER_STAGE/'MAIN_GO.json'
    launch = read(launch_path)
    active.base.validate_launch(config, launch, time.time())
    require(expected in launch['source_reference'], 'Main_broker_manifest_binding')
    store = active.base.Store(BROKER_OLD)
    runtime = BROKER_STAGE/'runtime'
    runtime.mkdir(mode=0o700, exist_ok=True)
    with (runtime/'CONTROLLER.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require(not (runtime/'STARTED.json').exists(), 'single_broker_activation_no_retry')
        queue_lock = QUEUE/'parent_claude/RUNNER.lock'
        require(store.shell('mkdir '+shlex.quote(str(queue_lock)), check=False).returncode == 0, 'exclusive_original_queue_lock')
        try:
            state = remote('inventory')
            epoch = state['boundary']
            require(state['counters'] == epoch['counters'] and not state['terminal'], 'no_successor_calls_before_broker')
            require(state['unfinished_claims'] == [], 'unsettled_historical_claim_requires_Main_review_no_replay')
            packets = runtime/'packets'
            packets.mkdir(mode=0o700)
            compatibility = Path('/tmp/r139_f2_astra_packets_v1')
            require(not compatibility.exists() and not compatibility.is_symlink(), 'new_data_compatibility_link')
            compatibility.symlink_to(packets, target_is_directory=True)
            process = FunctionType(active.base.process_request.__code__, dict(active.base.process_request.__globals__,
                evaluate=helper.data_evaluator(active, packets)), 'prospective_Astra_request', active.base.process_request.__defaults__)
            ready = dict(model=MODEL, reasoning_effort='low', boundary_sha256=state['boundary_sha256'],
                manifest_sha256=expected, config_sha256=sha(BROKER_STAGE/'CONFIG.json'),
                identity=helper.process_identity(os.getpid()), no_calls_at_activation=True, observed_unix=time.time())
            write(runtime/'STARTED.json', ready)
            require(not store.exists(ROOT/'BROKER_ACTIVE.json'), 'one_native_broker_receipt')
            store.copy(runtime/'STARTED.json', 'NODE:'+str(ROOT/'BROKER_ACTIVE.json'))
            require(store.hash(ROOT/'BROKER_ACTIVE.json') == sha(runtime/'STARTED.json'), 'native_broker_receipt_hash')
            while time.time() < config['deadline_unix']:
                state = remote('inventory')
                require(state['boundary'] == epoch, 'immutable_future_boundary')
                if state['terminal']:
                    break
                for row in state['requests']:
                    if not eligible(row, epoch):
                        continue
                    active.base.validate_launch(config, read(launch_path), time.time())
                    require(store.hash(QUEUE/'parent_queue'/(row['id']+'.request.json')) == row['sha256'], 'request_hash')
                    buffer = Path(tempfile.mkdtemp(prefix='request_', dir=compatibility))
                    process(store, config, launch, row['id']+'.request.json', buffer,
                        Path('/data/home/rohing/courier/swarm/prompts'),
                        BROKER_STAGE/'source/research_notes/PARENTING_PRINCIPLES_ROHIN_2026-09-15.md')
                    buffer.rmdir()
                time.sleep(2)
        finally:
            store.shell('rmdir '+shlex.quote(str(queue_lock)), check=False)


def check():
    run, boundary = native_modules()
    verify_source()
    request = read(ROOT/'REQUEST.json')
    checked(request['predecessor_plan'])
    slot(read(OLD_ROOT/'PLAN.json'))
    require(request['host_sha256'] == HOST_SHA, 'request_host')
    released = (ROOT/'RELEASED.json').exists()
    if not released:
        require(owned_actor(OLD_ROOT, boundary.pinned) == request['actor'], 'same_original_actor')
    else:
        require(read(ROOT/'RELEASED.json')['actual_pidfd_exit'] is True, 'actual_release_required')
    return dict(status='CPU_CHECK_PASS', request=ref(ROOT/'REQUEST.json'), host_sha256=HOST_SHA,
        released=released, ready=(ROOT/'READY.json').exists(), launched=(ROOT/'LAUNCH.json').exists(),
        source_manifest=ref(SOURCE/'R139_SOURCE_MANIFEST.json'), counters=read((ROOT if released else OLD_ROOT)/'COUNTERS.json'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('prepare','check','release','guard','resident','readout','scan','inventory',
        'broker-stage','broker-check','broker-serve'))
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--binding', type=Path)
    parser.add_argument('--manifest-sha256')
    args = parser.parse_args()
    require(args.root == ROOT, 'exact_F2_root_only')
    if args.phase in ('guard','resident','readout','scan'):
        result = run_native(args.phase, args.binding)
    elif args.phase == 'inventory':
        slot(read(ROOT/'PLAN.json'))
        result = inventory(ROOT)
        result.update(boundary=read(ROOT/'BOUNDARY.json'), boundary_sha256=sha(ROOT/'BOUNDARY.json'))
    elif args.phase == 'broker-stage':
        result = broker_stage()
    elif args.phase == 'broker-check':
        _, _, _, observed = broker_check(args.manifest_sha256)
        result = dict(status='CPU_BROKER_CHECK_PASS', native=observed)
    elif args.phase == 'broker-serve':
        result = broker_serve(args.manifest_sha256)
    else:
        result = globals()[args.phase]()
    if result is not None:
        print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
