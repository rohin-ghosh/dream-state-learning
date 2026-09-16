"""Prospective A2-only compatibility repair; preparation never serves requests."""

import argparse
import fcntl
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from types import FunctionType, SimpleNamespace


OLD = Path('/tmp/orch_math_feedback_uptake_r121_astra_source_20260915_v1')
DATA = Path('/data/home/rohing/courier/runtime')
ROOT = '/localhome/local-rohing/orch_math_feedback_uptake_r124_readout_20260915_attempt1/A2'
QUEUE = '/localhome/local-rohing/orch_math_feedback_uptake_r115_f2_20260915_attempt1/lane5'
PLAN_SHA = '3d387dd15e2424871163773b6d7e97441cb51a60278487ef64e25486cb56d80e'
CONFIG_SHA = '47ad54d07b57fe8dcd2e28fa46d6508506737f14e26a29a3c0887ef374105535'
PINS = {
    'gpu/orch_r110_claude_broker.py': '6d2dc623cf1e7000175de78160d6f791ac040ad3679bbd6ae852529b8db1cb99',
    'gpu/orch_math_feedback_uptake_r121_astra.py': '4ab248e1d9652e754dca704be7644ed59db2f3db6a45b0778fdfcf52a3bdab54',
    'gpu/orch_math_feedback_uptake_r118_broker.py': '5b45444e931edcd9e086ad1339a92803acff48ca1d3187ecdf9ec6ffcb0117b2',
}


def require(condition, code):
    if not condition:
        raise ValueError(code)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n')


def repair_source(text):
    changes = [
        ("    require(set(fields) == {'GAME', 'STYLE', 'NUDGING', 'FOCUS', 'REFLECTION'}, 'head_fields_keys')",
         "    required = {'GAME', 'STYLE', 'NUDGING', 'FOCUS', 'REFLECTION'}\n"
         "    require(required <= set(fields) <= required | {'NEXT_GUIDANCE'}, 'head_fields_keys')\n"
         "    if 'NEXT_GUIDANCE' in fields:\n"
         "        require(isinstance(fields['NEXT_GUIDANCE'], str)\n"
         "            and len(fields['NEXT_GUIDANCE'].encode()) <= 1024, 'bounded_next_guidance')"),
        ("    parent_policy = prompt + '\\n\\n' + principles + '\\n\\n' + SYSTEM_CONTRACT",
         "    parent_policy = prompt + '\\n\\n' + principles\n"
         "    next_guidance = settings['fields'].get('NEXT_GUIDANCE', '')\n"
         "    if next_guidance:\n"
         "        parent_policy += '\\n\\nASYNCHRONOUS HEAD NEXT_GUIDANCE:\\n' + next_guidance\n"
         "    parent_policy += '\\n\\n' + SYSTEM_CONTRACT"),
        ("        head_settings=settings, head_settings_sha256=digest(settings),",
         "        head_settings=settings, head_settings_sha256=digest(settings),\n"
         "        next_guidance_sha256=hashlib.sha256(next_guidance.encode()).hexdigest(),\n"
         "        head_waited=False,"),
    ]
    for before, after in changes:
        require(text.count(before) == 1, 'exact_frozen_patch_site')
        text = text.replace(before, after, 1)
    return text


REMOTE = r'''
import fcntl, hashlib, json, socket, time
from pathlib import Path
root=Path(ROOT_VALUE); queue=Path(QUEUE_VALUE)
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
with (root/'LEDGER.lock').open('r') as stream:
    fcntl.flock(stream,fcntl.LOCK_SH)
    plan=json.loads((root/'PLAN.json').read_text())
    assert sha(root/'PLAN.json')==PLAN_VALUE
    assert plan['branch']=='A2' and plan['index']==5 and plan['root']==str(root)
    assert plan['original_root']==str(queue)
    assert plan['parent_models']==['openai/openai/gpt-6-astra']
    counters=json.loads((root/'COUNTERS.json').read_text())
    reservations={}
    for path in (root/'reservations').glob('parent_*.json'):
        row=json.loads(path.read_text()); identifier=row['metadata']['id']
        assert identifier not in reservations
        reservations[identifier]=dict(first=row['first'],count=row['count'],reserved_unix=row['reserved_unix'])
    requests=[]
    for path in sorted((queue/'parent_queue').glob('*.request.json')):
        identifier=path.name.removesuffix('.request.json')
        requests.append(dict(id=identifier,sha256=sha(path),reservation=reservations.get(identifier),
            response=(queue/'parent_queue'/(identifier+'.response.json')).exists(),
            partial=(queue/'parent_queue'/(identifier+'.response.json.partial')).exists(),
            claim=(queue/'parent_claude'/(identifier+'.claim')).exists(),
            delivered=(root/'parent_delivered'/(identifier+'.json')).exists()))
    claims=list((queue/'parent_claude').glob('*.claim'))
    unfinished=[path.name for path in claims if not (path/'PUBLISHED.json').exists()
        or not (queue/'parent_queue'/(path.name.removesuffix('.claim')+'.response.json')).exists()]
    print(json.dumps(dict(observed_unix=time.time(),plan_sha256=sha(root/'PLAN.json'),
        host_sha256=hashlib.sha256(socket.gethostname().encode()).hexdigest(),
        counters=counters,requests=requests,unfinished_claims=unfinished,
        runner_lock=(queue/'parent_claude/RUNNER.lock').exists(),
        terminal=(root/'TERMINAL.json').exists() or (root/'runtime_recovery5/GUARD_TERMINAL.json').exists())))
'''


def snapshot(repository):
    script = REMOTE.replace('ROOT_VALUE', repr(ROOT)).replace('QUEUE_VALUE', repr(QUEUE)).replace('PLAN_VALUE', repr(PLAN_SHA))
    result = subprocess.run(['bash', str(Path(repository)/'gpu/ovx3_ssh.sh'), 'python3 -'],
        input=script, text=True, capture_output=True, timeout=30)
    require(result.returncode == 0, 'remote_metadata_check_failed')
    return json.loads(result.stdout)


def process_identity(pid):
    proc = Path('/proc')/str(pid)
    if not proc.exists():
        return None
    stat = (proc/'stat').read_text().rsplit(')', 1)[1].split()
    return dict(pid=pid, start_ticks=stat[19], command_sha256=sha(proc/'cmdline'))


def process_activity(identity):
    require(process_identity(identity['pid']) == identity, 'old_broker_identity_changed')
    proc = Path('/proc')/str(identity['pid'])
    args = (proc/'cmdline').read_bytes().split(b'\0')
    require(b'gpu.orch_math_feedback_uptake_r121_astra' in args, 'exact_A2_broker_entry')
    require((proc/'cwd').resolve() == OLD, 'exact_A2_broker_cwd')
    config = args[args.index(b'--config')+1].decode()
    require(sha(OLD/config) == CONFIG_SHA, 'exact_A2_broker_config')
    descriptors = []
    for descriptor in (proc/'fd').iterdir():
        try:
            target = os.readlink(descriptor)
        except FileNotFoundError:
            continue
        if target.startswith('socket:') or '/orch_astra_http_slots/' in target:
            descriptors.append(descriptor.name)
    children = (proc/'task'/str(identity['pid'])/'children').read_text().split()
    state = (proc/'stat').read_text().rsplit(')', 1)[1].split()[0]
    require(process_identity(identity['pid']) == identity, 'old_broker_identity_race')
    return dict(state=state, socket_or_http_slot_fds=descriptors, child_pids=[int(value) for value in children])


def boundary(document):
    return dict(observed_unix=document['observed_unix'], parent_high_water=document['counters']['parent'],
        counters=document['counters'], historical_ids=[row['id'] for row in document['requests']],
        request_inventory_sha256=digest(document['requests']), host_sha256=document['host_sha256'],
        plan_sha256=document['plan_sha256'])


def eligible(row, epoch):
    if row['id'] in epoch['historical_ids']:
        return False
    if any(row[key] for key in ('response', 'partial', 'claim', 'delivered')):
        return False
    reservation = row.get('reservation')
    if not reservation:
        return False
    require(re.fullmatch(r'R121_C[0-9]{6}_E[01]_experience', row['id']) is not None, 'exact_native_request_id')
    require(reservation['count'] == 1, 'one_native_parent_reservation')
    return reservation['first'] > epoch['parent_high_water'] and reservation['reserved_unix'] > epoch['observed_unix']


def stage_path(path):
    path = Path(path)
    require(path.is_absolute() and not path.is_symlink() and path.resolve().is_relative_to(DATA.resolve()), 'data_only_stage')
    return path


def prepare(path, old_pid):
    path = stage_path(path)
    require(not path.exists(), 'new_immutable_stage_only')
    require(sha(OLD/'LOW_CONFIG.json') == CONFIG_SHA, 'frozen_A2_config')
    original = read(OLD/'LOW_CONFIG.json')
    for name, expected in {**original['source_files'], **PINS}.items():
        require(sha(OLD/name) == expected, 'frozen_dependency_changed')
    identity = process_identity(old_pid)
    require(identity is not None, 'old_broker_required_for_binding')
    activity = process_activity(identity)
    observed = snapshot(OLD)
    require(not observed['terminal'], 'A2_already_terminal')
    path.mkdir(mode=0o700)
    source = path/'source'
    files = {}
    for folder in ('gpu', 'organism_v6', 'research_loop', 'research_notes'):
        for previous in sorted((OLD/folder).rglob('*')):
            if '__pycache__' in previous.parts or previous.suffix not in ('.py', '.md', '.sh'):
                continue
            require(previous.is_file() and not previous.is_symlink(), 'regular_source_only')
            relative = previous.relative_to(OLD)
            target = source/relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(previous, target)
            files[str(relative)] = dict(old_sha256=sha(previous), sha256=sha(target))
    broker = source/'gpu/orch_r110_claude_broker.py'
    broker.write_text(repair_source(broker.read_text()))
    files['gpu/orch_r110_claude_broker.py']['sha256'] = sha(broker)
    shutil.copyfile(__file__, path/'orch_r137_math_request_repair.py')
    config = dict(original, source_files=dict(original['source_files']))
    config['source_files']['gpu/orch_r110_claude_broker.py'] = sha(broker)
    write(path/'CONFIG.json', config)
    write(path/'PREPARATION_BOUNDARY.json', boundary(observed))
    write(path/'OLD_BROKER.json', dict(identity=identity, activity=activity,
        unfinished_claims=observed['unfinished_claims'], observed_unix=observed['observed_unix']))
    write(path/'MANIFEST.json', dict(schema='R137_A2_REQUEST_REPAIR_V1', old_source=str(OLD),
        source_files=files, original_config_sha256=CONFIG_SHA, config_sha256=sha(path/'CONFIG.json'),
        original_config=original, wrapper_sha256=sha(path/'orch_r137_math_request_repair.py'),
        boundary_sha256=sha(path/'PREPARATION_BOUNDARY.json'), old_broker_sha256=sha(path/'OLD_BROKER.json')))
    write(path/'GO_TEMPLATE.json', dict(schema='ORCH_R111_FABLE_LAUNCH_V1', authorized=False,
        authorization='WATCHER_RELAYED_ROHIN_DONE', source_reference='MAIN_PUBLICATION_REQUIRED',
        config_sha256=digest(config), not_before_unix=0))
    return dict(status='STAGED_NOT_LAUNCHED', manifest_sha256=sha(path/'MANIFEST.json'),
        config_sha256=sha(path/'CONFIG.json'), boundary=boundary(observed), old_broker=identity)


def verify(path, expected):
    path = stage_path(path)
    require(sha(path/'MANIFEST.json') == expected, 'manifest_hash')
    manifest = read(path/'MANIFEST.json')
    require(sha(__file__) == manifest['wrapper_sha256'], 'running_wrapper_hash')
    require(manifest['original_config_sha256'] == CONFIG_SHA, 'original_config_identity')
    require(sha(OLD/'LOW_CONFIG.json') == CONFIG_SHA, 'original_config_preserved')
    for name, pins in manifest['source_files'].items():
        require(not Path(name).is_absolute() and '..' not in Path(name).parts, 'relative_source')
        require(sha(path/'source'/name) == pins['sha256'], 'staged_source_hash')
        require(sha(OLD/name) == pins['old_sha256'], 'original_source_preserved')
        if name != 'gpu/orch_r110_claude_broker.py':
            require(pins['sha256'] == pins['old_sha256'], 'only_broker_backport')
    for name, key in [('CONFIG.json', 'config_sha256'), ('PREPARATION_BOUNDARY.json', 'boundary_sha256'), ('OLD_BROKER.json', 'old_broker_sha256')]:
        require(sha(path/name) == manifest[key], 'staged_metadata_hash')
    config = read(path/'CONFIG.json')
    original = manifest['original_config']
    require(dict(config, source_files=original['source_files']) == original, 'unchanged_A2_policy')
    require(config['remote_root'] == QUEUE and config['branch'] == 'F2' and config['family'] == 'math', 'A2_queue_only')
    sys.path.insert(0, str(path/'source'))
    active = importlib.import_module('gpu.orch_math_feedback_uptake_r121_astra')
    require(Path(active.__file__).resolve().is_relative_to((path/'source').resolve()), 'staged_import_only')
    active.base.validate_config(config)
    return active, config


def check(path, expected, stopped=False):
    active, config = verify(path, expected)
    observed = snapshot(OLD)
    epoch = read(path/'PREPARATION_BOUNDARY.json')
    require(observed['host_sha256'] == epoch['host_sha256'] and not observed['terminal'], 'same_live_A2')
    identity = read(path/'OLD_BROKER.json')['identity']
    activity = process_activity(identity) if process_identity(identity['pid']) else None
    if stopped:
        require(activity is not None and activity['state'] in ('T', 't'), 'old_broker_must_be_stopped_by_Main')
        require(not activity['socket_or_http_slot_fds'] and not activity['child_pids'] and not observed['unfinished_claims'], 'inflight_resume_old_broker_without_retirement')
    prompt = Path('/data/home/rohing/courier/swarm/prompts/F2.md')
    binding = active.base.head_binding(prompt, prompt.read_bytes())
    return dict(status='HANDOFF_IDLE' if stopped else 'CPU_CHECK_PASS', old_broker=identity,
        old_activity=activity, unfinished_claims=observed['unfinished_claims'], runner_lock=observed['runner_lock'],
        prompt_binding_status=binding['status'], prompt_sha256=sha(prompt), provider_calls=0,
        fresh_observation=boundary(observed), configured_model=active.delivery.STRONG,
        max_output_tokens=config['max_output_tokens'], max_parent_calls=config['max_parent_calls'])


def authorize(active, config, expected, launch_path):
    launch = active.base.loads(Path(launch_path).read_text())
    active.base.validate_launch(config, launch, time.time())
    require(expected in launch['source_reference'], 'Main_publication_must_bind_manifest')
    return launch


def release_runner_lock(store):
    lock = shlex.quote(QUEUE+'/parent_claude/RUNNER.lock')
    command = 'if test ! -e '+lock+' && test ! -L '+lock+'; then :; else rmdir '+lock+'; fi'
    require(store.shell(command, check=False).returncode == 0, 'only_empty_or_already_absent_old_runner_lock')


def retire(path, expected, launch_path):
    active, config = verify(path, expected)
    authorize(active, config, expected, launch_path)
    identity = read(path/'OLD_BROKER.json')['identity']
    descriptor = os.pidfd_open(identity['pid'])
    stopped = False
    try:
        require(process_identity(identity['pid']) == identity, 'exact_broker_before_stop')
        signal.pidfd_send_signal(descriptor, signal.SIGSTOP)
        stopped = True
        cutoff = time.monotonic()+5
        while process_activity(identity)['state'] not in ('T', 't'):
            require(time.monotonic() < cutoff, 'broker_stop_timeout')
            time.sleep(.02)
        receipt = check(path, expected, stopped=True)
        signal.pidfd_send_signal(descriptor, signal.SIGTERM)
        signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        stopped = False
        cutoff = time.monotonic()+10
        while process_identity(identity['pid']) is not None:
            require(time.monotonic() < cutoff, 'broker_exit_timeout_no_force_kill')
            time.sleep(.05)
        current = snapshot(OLD)
        require(not current['unfinished_claims'], 'claims_must_remain_settled')
        store = active.base.Store(OLD)
        release_runner_lock(store)
        write(path/'RETIREMENT.json', dict(receipt, retired_unix=time.time(), provider_calls=0, child_signals=0))
        return dict(status='EXACT_OLD_BROKER_RETIRED', identity=identity, child_signals=0)
    finally:
        if stopped:
            signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        os.close(descriptor)


def data_evaluator(active, packets):
    def evaluate(*args, **kwargs):
        directory = Path(args[1]).resolve()
        require(directory.is_relative_to(packets.resolve()), 'only_private_data_packets')
        function = active.delivery.astra_evaluate
        namespace = dict(function.__globals__, tomllib=SimpleNamespace(loads=active.low_settings))
        shared = SimpleNamespace(**vars(active.base))
        def require_data(condition, code):
            if code == 'bounded_tmp_only':
                return active.base.require(directory.is_relative_to(packets.resolve()), 'bounded_data_only')
            return active.base.require(condition, code)
        shared.require = require_data
        namespace['shared'] = shared
        bound = FunctionType(function.__code__, namespace, function.__name__, function.__defaults__)
        bound.__kwdefaults__ = function.__kwdefaults__
        return bound(*args, **kwargs)
    return evaluate


def serve(path, expected, launch_path):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_only')
    active, config = verify(path, expected)
    base = active.base
    launch = authorize(active, config, expected, launch_path)
    identity = read(path/'OLD_BROKER.json')['identity']
    require(process_identity(identity['pid']) is None, 'old_broker_must_be_absent')
    data = path/'runtime'
    data.mkdir(mode=0o700, exist_ok=True)
    store = base.Store(OLD)
    lock = Path(QUEUE)/'parent_claude/RUNNER.lock'
    with (data/'CONTROLLER.lock').open('a') as descriptor:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require(not (data/'START_BOUNDARY.json').exists(), 'single_activation_no_resume')
        require(store.shell('mkdir '+shlex.quote(str(lock)), check=False).returncode == 0, 'exclusive_original_queue_lock')
        try:
            observed = snapshot(OLD)
            require(not observed['terminal'] and not observed['unfinished_claims'], 'no_inflight_or_terminal')
            epoch = boundary(observed)
            require(epoch['host_sha256'] == read(path/'PREPARATION_BOUNDARY.json')['host_sha256'], 'same_node')
            write(data/'START_BOUNDARY.json', epoch)
            compatibility = Path('/tmp')/(path.name+'_packets')
            require(not compatibility.exists() and not compatibility.is_symlink(), 'fresh_data_compatibility_link')
            packets = data/'packets'
            packets.mkdir(mode=0o700)
            compatibility.symlink_to(packets, target_is_directory=True)
            require(compatibility.resolve() == packets.resolve(), 'packets_on_data')
            process = FunctionType(base.process_request.__code__, dict(base.process_request.__globals__, evaluate=data_evaluator(active, packets)),
                'process_request', base.process_request.__defaults__)
            write(data/'STARTED.json', dict(pid=os.getpid(), identity=process_identity(os.getpid()),
                manifest_sha256=expected, launch_sha256=sha(launch_path), provider_calls_at_start=0))
            while time.time() < config['deadline_unix']:
                current = snapshot(OLD)
                require(current['host_sha256'] == epoch['host_sha256'], 'same_node')
                if current['terminal']:
                    break
                for row in current['requests']:
                    if not eligible(row, epoch):
                        continue
                    launch = authorize(active, config, expected, launch_path)
                    request_path = Path(QUEUE)/'parent_queue'/(row['id']+'.request.json')
                    require(store.hash(request_path) == row['sha256'], 'request_unchanged')
                    temporary = Path(tempfile.mkdtemp(prefix='request_', dir=compatibility))
                    process(store, config, launch, row['id']+'.request.json', temporary,
                        Path('/data/home/rohing/courier/swarm/prompts'),
                        path/'source/research_notes/PARENTING_PRINCIPLES_ROHIN_2026-09-15.md')
                    temporary.rmdir()
                time.sleep(2)
        finally:
            store.shell('rmdir '+shlex.quote(str(lock)), check=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('prepare', 'check', 'handoff-check', 'retire', 'serve'))
    parser.add_argument('--stage', type=Path, required=True)
    parser.add_argument('--old-pid', type=int)
    parser.add_argument('--manifest-sha256')
    parser.add_argument('--launch-receipt', type=Path)
    args = parser.parse_args()
    if args.phase == 'prepare':
        require(args.old_pid is not None, 'old_pid_required')
        result = prepare(args.stage, args.old_pid)
    else:
        require(args.manifest_sha256 is not None, 'manifest_required')
        if args.phase in ('serve', 'retire'):
            require(args.launch_receipt is not None, 'Main_launch_receipt_required')
            if args.phase == 'serve':
                serve(args.stage, args.manifest_sha256, args.launch_receipt)
                result = dict(status='BROKER_EXITED')
            else:
                result = retire(args.stage, args.manifest_sha256, args.launch_receipt)
        else:
            result = check(args.stage, args.manifest_sha256, args.phase == 'handoff-check')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
