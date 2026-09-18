"""CPU-staged, explicitly approved future-only F2 C96 broker successor."""

import argparse
import ast
from copy import deepcopy
import fcntl
import hashlib
import importlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import shlex
import shutil
import sys
import tempfile
import time
from types import FunctionType


FROZEN = Path('/data/home/rohing/courier/runtime/r139_f2_astra_handoff_v1')
FROZEN_SHA = '428713960d2bb44ed804228f0a133861a486e8598c250703d6fc8fbc8a0eeddc'
WRAPPER_ROOT = Path('/tmp/orch_math_feedback_uptake_r121_astra_source_20260915_v1')
DATA_ROOT = Path('/data/home/rohing/courier/runtime')
ROOT = Path('/localhome/local-rohing/orch_r139_math_astra_handoff_20260916_v1/F2')
QUEUE = Path('/localhome/local-rohing/orch_math_feedback_uptake_r115_f2_20260915_attempt1/lane1')
SERVICE = ROOT/'runtime_r149_cohort96_20260916t1920z_candidate2'
HOST_SHA = '0cb7eb43862102b79ae0a30d2babfedfbf9598b31967a1a04122c3cf849c746d'
MODEL = 'openai/openai/gpt-6-astra'
COUNTERS = dict(native=2494, parent=232, optimizer_steps=48021)
SCHEMA = 'R149_F2_FUTURE_BROKER_V1'


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
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')


def ref(path):
    return dict(path=str(Path(path).resolve(strict=True)), sha256=sha(path))


def checked(reference):
    require(sha(reference['path']) == reference['sha256'], 'immutable_local_reference')
    return read(reference['path'])


def frozen_metadata():
    require(sha(FROZEN/'MANIFEST.json') == FROZEN_SHA, 'original_frozen_manifest')
    manifest = read(FROZEN/'MANIFEST.json')
    for key in ('wrapper', 'helper', 'config', 'prompt_check'):
        require(sha(manifest[key]['path']) == manifest[key]['sha256'], 'frozen_'+key)
    for name, expected in manifest['source_files'].items():
        require(sha(FROZEN/'source'/name) == expected, 'frozen_transport_source')
    for name in ('ovx3_ssh.sh', 'ovx3_scp.sh'):
        require(sha(WRAPPER_ROOT/'gpu'/name) == manifest['source_files']['gpu/'+name],
            'existing_node_wrapper_context')
    return manifest


def load_module(name, path):
    specification = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def frozen_imports():
    source = FROZEN/'source'
    saved = {name: module for name, module in sys.modules.items()
        if name.split('.')[0] in ('gpu', 'organism_v6')}
    previous_path = sys.path[:]
    previous_bytecode = sys.dont_write_bytecode
    try:
        for name in saved:
            del sys.modules[name]
        sys.path.insert(0, str(source))
        sys.dont_write_bytecode = True
        active = importlib.import_module('gpu.orch_math_feedback_uptake_r121_astra')
        helper = load_module('r149_frozen_helper', FROZEN/'r137_helper.py')
        prior = load_module('r149_frozen_handoff', FROZEN/'orch_r139_math_astra_handoff.py')
        for name, module in tuple(sys.modules.items()):
            if name.split('.')[0] in ('gpu', 'organism_v6') and getattr(module, '__file__', None):
                require(Path(module.__file__).resolve().is_relative_to(source.resolve()), 'frozen_import_scope')
        require(active.delivery.STRONG == MODEL, 'unchanged_astra_model')
        return active, helper, prior
    finally:
        for name in list(sys.modules):
            if name.split('.')[0] in ('gpu', 'organism_v6'):
                del sys.modules[name]
        sys.modules.update(saved)
        sys.path[:] = previous_path
        sys.dont_write_bytecode = previous_bytecode


def validate_delta(original, config):
    require(original['branch'] == 'F2' and original['family'] == 'math'
        and original['remote_root'] == str(QUEUE), 'original_F2_queue')
    require(original['deadline_unix'] == 1789596120 and original['max_parent_calls'] == 384
        and original['max_budget_usd'] == 1.0 and original['max_output_tokens'] == 8192,
        'unchanged_F2_limits')
    expected = deepcopy(original)
    expected.update(train_tasks=config['train_tasks'], cohort_sha256=config['cohort_sha256'])
    require(config == expected, 'only_prospective_train_and_cohort_delta')
    old_tasks, tasks = original['train_tasks'], config['train_tasks']
    require(len(old_tasks) == 192 and len(tasks) > 192 and len(tasks) % 2 == 0, 'extend_96_two_episode_cycles')
    require(all(tasks.get(identifier) == value for identifier, value in old_tasks.items()), 'exact_old_192_task_bindings')
    require(config['cohort_sha256'] != original['cohort_sha256'], 'new_cohort_hash')


def broker_config(original, training, cohort_sha256):
    require(len(training) > 96 and all(isinstance(group, list) and len(group) == 2 for group in training),
        'extended_two_episode_TRAIN_only')
    tasks = [task for group in training for task in group]
    require(all(task['split'] == 'TRAIN' for task in tasks), 'TRAIN_only_config_producer')
    require(len({task['id'] for task in tasks}) == len(tasks), 'unique_train_ids')
    result = deepcopy(original)
    result.update(train_tasks={task['id']: task['question_sha256'] for task in tasks}, cohort_sha256=cohort_sha256)
    validate_delta(original, result)
    require(not set(result['train_tasks']).intersection(result['excluded_task_ids']), 'train_exclusions')
    return result


def validate_epoch(epoch):
    require(epoch['next_cycle'] == 97 and epoch['parent_high_water'] == 232, 'exact_C96_boundary')
    require(all(epoch['counters'].get(key) == value for key, value in COUNTERS.items()), 'exact_saved_counters')
    require(type(epoch['observed_unix']) in (int, float) and math.isfinite(epoch['observed_unix'])
        and epoch['observed_unix'] > 0, 'finite_epoch_time')
    require(epoch.get('no_historical_replay') is True, 'explicit_no_historical_replay')
    identifiers = epoch['historical_ids']
    require(isinstance(identifiers, list) and all(isinstance(value, str) for value in identifiers)
        and len(set(identifiers)) == len(identifiers), 'historical_request_and_claim_ids')


def validate_binding(binding, config, config_sha, original):
    require(binding['schema'] == SCHEMA and binding['service'] == str(SERVICE), 'exact_native_service')
    for key, filename in (('prepared', 'PREPARED.json'), ('plan', 'RESUME_PLAN.json'),
            ('epoch', 'EPOCH.json'), ('train', 'TRAIN.json'), ('broker_config', 'BROKER_CONFIG.json')):
        reference = binding[key]
        require(reference['path'] == str(SERVICE/filename)
            and re.fullmatch('[a-f0-9]{64}', reference['sha256']), 'native_'+key+'_reference')
    old = binding['old_train']
    old_path = Path(old['path'])
    require(old_path.name == 'TRAIN.json' and old_path.is_relative_to('/localhome/local-rohing')
        and '..' not in old_path.parts and not {'sealed', 'held'}.intersection(old_path.parts)
        and old['sha256'] == original['cohort_sha256'], 'original_train_reference_only')
    require(binding['train']['sha256'] == config['cohort_sha256']
        and binding['broker_config']['sha256'] == config_sha, 'native_config_train_hashes')
    validate_epoch(binding['epoch_document'])


def data_stage(path):
    path = Path(path).resolve()
    require(path.is_relative_to(DATA_ROOT.resolve()) and not path.is_relative_to(FROZEN.resolve())
        and not path.is_relative_to(Path('/tmp').resolve()), 'new_runtime_on_data_not_tmp_or_frozen')
    return path


def stage(config_path, binding_path, manifest_path):
    frozen_metadata()
    active, _, _ = frozen_imports()
    config, original = read(config_path), read(FROZEN/'CONFIG.json')
    validate_delta(original, config)
    active.base.validate_config(config)
    binding = read(binding_path)
    validate_binding(binding, config, sha(config_path), original)
    manifest_path = data_stage(manifest_path)
    require(manifest_path.name == 'MANIFEST.json', 'manifest_filename')
    directory = manifest_path.parent
    directory.mkdir(mode=0o700, parents=True, exist_ok=False)
    for source, name in ((config_path, 'CONFIG.json'), (binding_path, 'BINDING.json'),
            (__file__, 'orch_r149_f2_broker.py')):
        shutil.copyfile(source, directory/name)
    manifest = dict(schema=SCHEMA, frozen=ref(FROZEN/'MANIFEST.json'),
        config=ref(directory/'CONFIG.json'), binding=ref(directory/'BINDING.json'),
        wrapper=ref(directory/'orch_r149_f2_broker.py'), model=MODEL, reasoning_effort='low',
        native_prefix_gate='REQUIRED_AT_APPROVED_ACTIVATION', no_calls=True)
    write(manifest_path, manifest)
    write(directory/'MAIN_GO_TEMPLATE.json', dict(schema='ORCH_R111_FABLE_LAUNCH_V1', authorized=False,
        authorization='WATCHER_RELAYED_ROHIN_DONE', source_reference=approval_reference(sha(manifest_path)),
        config_sha256=digest(config), not_before_unix=0))
    return dict(status='CPU_STAGED_NOT_LAUNCHED', manifest=ref(manifest_path), native_prefix_checked=False)


def check(manifest_path, expected):
    manifest_path = data_stage(manifest_path)
    require(sha(manifest_path) == expected, 'exact_successor_manifest')
    manifest = read(manifest_path)
    require(manifest['schema'] == SCHEMA and manifest['frozen'] == ref(FROZEN/'MANIFEST.json')
        and manifest['model'] == MODEL and manifest['reasoning_effort'] == 'low', 'frozen_transport_binding')
    require(manifest['wrapper']['path'] == str(manifest_path.parent/'orch_r149_f2_broker.py')
        and sha(__file__) == manifest['wrapper']['sha256'] == sha(manifest['wrapper']['path']), 'running_wrapper_hash')
    for key, filename in (('config', 'CONFIG.json'), ('binding', 'BINDING.json')):
        require(manifest[key]['path'] == str(manifest_path.parent/filename), 'staged_'+key+'_path')
    config, binding = checked(manifest['config']), checked(manifest['binding'])
    frozen_metadata()
    active, helper, prior = frozen_imports()
    original = read(FROZEN/'CONFIG.json')
    validate_delta(original, config)
    active.base.validate_config(config)
    validate_binding(binding, config, manifest['config']['sha256'], original)
    return active, helper, prior, config, binding


def approval_reference(expected):
    return 'R149_F2_BROKER_MANIFEST_SHA256:'+expected


def authorize(active, config, launch_path, expected):
    launch = read(launch_path)
    active.base.validate_launch(config, launch, time.time())
    require(launch['source_reference'] == approval_reference(expected), 'explicit_exact_Main_manifest_approval')
    return launch


def mapped_store(base, service=SERVICE):
    def mapped(path):
        path = Path(path)
        if path == QUEUE/'parent_claude/CONFIG.json':
            return service/'BROKER_CONFIG.json'
        if path in (ROOT/'TERMINAL.json', QUEUE/'TERMINAL.json', QUEUE/'SHARED_TERMINAL.json'):
            return service/'TERMINAL.json'
        return path

    class Store(base.Store):
        def exists(self, path):
            return super().exists(mapped(path))

        def hash(self, path):
            return super().hash(mapped(path))

        def copy(self, source, destination):
            if str(source).startswith('NODE:'):
                source = 'NODE:'+str(mapped(str(source)[5:]))
            if str(destination).startswith('NODE:'):
                destination = 'NODE:'+str(mapped(str(destination)[5:]))
            return super().copy(source, destination)

        def shell(self, script, check=True):
            for command in ('cat ', 'sha256sum ', 'test -e '):
                path = QUEUE/'parent_claude/CONFIG.json'
                if script == command+shlex.quote(str(path)):
                    script = command+shlex.quote(str(mapped(path)))
            return super().shell(script, check=check)

    return Store(WRAPPER_ROOT)


def function_source(path, name):
    text = Path(path).read_text()
    tree = ast.parse(text)
    matches = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name]
    require(len(matches) == 1, 'exact_frozen_function')
    return ast.get_source_segment(text, matches[0])+'\n'


def validate_clearance(clearance, binding, manifest_sha256):
    require(clearance['passed'] is True and clearance['complete_exclusion_coverage'] is True
        and clearance['exact_prefix'] is True, 'complete_independent_cohort_clearance')
    require(clearance['train_sha256'] == binding['train']['sha256']
        and clearance['original_train_sha256'] == binding['old_train']['sha256']
        and clearance['manifest_sha256'] == manifest_sha256, 'exact_collision_checked_bytes')
    require(clearance['task_id_collisions'] == clearance['question_hash_collisions'] == 0
        and clearance['checked_new_task_count'] == 192 and clearance['excluded_id_count'] >= 5846
        and clearance['excluded_question_hash_count'] >= 5838, 'full_inherited_cohort_coverage')
    require(set(clearance['exclusion_sources_sha256']) >= {'original_train', 'dev', 'final', 'inherited_registry'},
        'complete_exclusion_source_metadata')
    require(all(isinstance(value, str) and re.fullmatch('[a-f0-9]{64}', value)
        for value in clearance['exclusion_sources_sha256'].values()), 'exclusion_source_hash_metadata')


def native_probe(binding, config, prefix):
    import socket

    require(hashlib.sha256(socket.gethostname().encode()).hexdigest() == HOST_SHA, 'exact_node_host')
    for key in ('prepared', 'plan', 'epoch', 'train', 'old_train', 'broker_config'):
        require(sha(binding[key]['path']) == binding[key]['sha256'], 'native_bound_'+key)
    prepared = read(binding['prepared']['path'])
    require(prepared['plan'] == binding['plan'] and prepared['epoch'] == binding['epoch'], 'prepared_plan_epoch_join')
    require(prepared['original_plan']['path'] == str(ROOT/'PLAN.json'), 'original_native_plan_path')
    require(prepared['clearance']['path'] == str(SERVICE/'COLLISION_CLEARANCE.json'), 'separate_clearance_path')
    require(prepared['cohort']['path'] == str(SERVICE/'COHORT.json'), 'immutable_candidate_manifest_path')
    for key in ('original_plan', 'source', 'tests', 'cohort', 'clearance'):
        reference = prepared[key]
        require(sha(reference['path']) == reference['sha256'], 'prepared_bound_'+key)
    require(read(prepared['original_plan']['path'])['train'] == binding['old_train'], 'original_train_plan_join')
    require(read(prepared['tests']['path'])['passed'] is True, 'native_CPU_tests_passed')
    clearance = read(prepared['clearance']['path'])
    validate_clearance(clearance, binding, prepared['cohort']['sha256'])
    require(len(config['train_tasks']) == 192+clearance['checked_new_task_count'], 'cleared_extension_size')
    require(read(binding['plan']['path'])['train'] == binding['train'], 'resume_plan_train_binding')
    require(read(binding['broker_config']['path']) == config, 'native_broker_config_bytes')
    epoch = read(binding['epoch']['path'])
    require(epoch == binding['epoch_document'], 'native_epoch_bytes')
    if prefix:
        old, training = read(binding['old_train']['path']), read(binding['train']['path'])
        require(len(old) == 96 and len(training) > 96 and training[:96] == old, 'exact_old96_prefix')
        require(all(isinstance(group, list) and len(group) == 2 for group in training), 'two_episodes_per_cycle')
        tasks = [task for group in training for task in group]
        require(all(task['split'] == 'TRAIN' for task in tasks), 'TRAIN_only_cohort')
        require(len({task['id'] for task in tasks}) == len(tasks), 'unique_train_ids')
        require({task['id']: task['question_sha256'] for task in tasks} == config['train_tasks'], 'exact_train_roster')
    state = inventory(ROOT)
    state.update(terminal=(SERVICE/'TERMINAL.json').exists(),
        boundary=epoch, boundary_sha256=sha(binding['epoch']['path']),
        native_started=any((SERVICE/name).exists() for name in ('LAUNCH.json', 'STARTED.json', 'NATIVE_STARTED.json')))
    return state


def remote_inventory(store, binding, config, prefix=False):
    imports = 'import fcntl, hashlib, json, re\nfrom pathlib import Path\n'
    constants = 'ROOT=Path('+repr(str(ROOT))+')\nQUEUE=Path('+repr(str(QUEUE))+')\nSERVICE=Path('+repr(str(SERVICE))+')\nHOST_SHA='+repr(HOST_SHA)+'\n'
    helpers = ''.join(function_source(__file__, name) for name in ('require', 'sha', 'read', 'validate_clearance', 'native_probe'))
    inherited = function_source(FROZEN/'orch_r139_math_astra_handoff.py', 'inventory')
    payload = json.dumps(dict(binding=binding, config=config, prefix=prefix), allow_nan=False)
    program = imports+'import time\n'+constants+helpers+inherited+'\nprint(json.dumps(native_probe(**json.loads('+repr(payload)+'))))\n'
    result = store.shell('CUDA_VISIBLE_DEVICES= python3 -B -c '+shlex.quote(program))
    return json.loads(result.stdout)


def validate_activation(state, epoch):
    require(state['boundary'] == epoch and state['host_sha256'] == HOST_SHA, 'immutable_native_epoch_host')
    require(state['counters'] == epoch['counters'] and not state['terminal']
        and not state['native_started'], 'broker_before_exact_native_resume')
    require(set(state['historical_ids']) <= set(epoch['historical_ids']), 'every_old_request_and_claim_excluded')


def serve(manifest_path, expected, launch_path):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_broker_only')
    active, helper, prior, config, binding = check(manifest_path, expected)
    directory = Path(manifest_path).resolve().parent
    require(Path(__file__).resolve() == directory/'orch_r149_f2_broker.py', 'serve_only_staged_wrapper')
    launch = authorize(active, config, launch_path, expected)
    launch_sha = sha(launch_path)
    require(shutil.disk_usage(directory).free >= 10 * 1024 ** 3, 'data_disk_launch_floor')
    old_identity = read(FROZEN/'runtime/STARTED.json')['identity']
    require(helper.process_identity(old_identity['pid']) != old_identity, 'prior_broker_no_longer_running')
    store = mapped_store(active.base)
    epoch = binding['epoch_document']
    validate_activation(remote_inventory(store, binding, config, prefix=True), epoch)
    runtime = directory/'runtime'
    runtime.mkdir(mode=0o700, exist_ok=True)
    with (runtime/'CONTROLLER.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require(not (runtime/'STARTED.json').exists(), 'single_activation_no_retry')
        queue_lock = QUEUE/'parent_claude/RUNNER.lock'
        require(store.shell('mkdir '+shlex.quote(str(queue_lock)), check=False).returncode == 0,
            'exclusive_original_queue_lock_no_stale_lock_removal')
        try:
            state = remote_inventory(store, binding, config, prefix=True)
            validate_activation(state, epoch)
            require(not store.exists(SERVICE/'BROKER_ACTIVE.json'), 'new_service_receipt_only')
            packets = runtime/'packets'
            packets.mkdir(mode=0o700)
            process = FunctionType(active.base.process_request.__code__,
                dict(active.base.process_request.__globals__, evaluate=helper.data_evaluator(active, packets)),
                'future_only_astra_request', active.base.process_request.__defaults__)
            ready = dict(schema=SCHEMA, model=MODEL, reasoning_effort='low', manifest_sha256=expected,
                config_sha256=binding['broker_config']['sha256'], boundary_sha256=binding['epoch']['sha256'],
                prepared=binding['prepared'], plan=binding['plan'], train=binding['train'],
                service=str(SERVICE), counters=epoch['counters'], next_cycle=97, parent_high_water=232,
                launch_sha256=launch_sha, identity=helper.process_identity(os.getpid()),
                no_calls_at_activation=True, native_prefix_checked=True, observed_unix=time.time())
            write(runtime/'STARTED.json', ready)
            store.copy(runtime/'STARTED.json', 'NODE:'+str(SERVICE/'BROKER_ACTIVE.json'))
            require(store.hash(SERVICE/'BROKER_ACTIVE.json') == sha(runtime/'STARTED.json'), 'native_ready_hash')
            while time.time() < config['deadline_unix']:
                state = remote_inventory(store, binding, config)
                require(state['boundary'] == epoch and state['host_sha256'] == HOST_SHA, 'immutable_future_boundary')
                if state['terminal']:
                    break
                for row in state['requests']:
                    if not prior.eligible(row, epoch):
                        continue
                    require(sha(launch_path) == launch_sha, 'unchanged_Main_approval')
                    launch = authorize(active, config, launch_path, expected)
                    require(store.hash(QUEUE/'parent_queue'/(row['id']+'.request.json')) == row['sha256'], 'request_hash')
                    buffer = Path(tempfile.mkdtemp(prefix='request_', dir=packets))
                    process(store, config, launch, row['id']+'.request.json', buffer,
                        Path('/data/home/rohing/courier/swarm/prompts'),
                        FROZEN/'source/research_notes/PARENTING_PRINCIPLES_ROHIN_2026-09-15.md')
                    buffer.rmdir()
                time.sleep(2)
        finally:
            store.shell('rmdir '+shlex.quote(str(queue_lock)), check=False)
    return dict(status='BROKER_STOPPED', manifest_sha256=expected)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('stage', 'check', 'serve'))
    parser.add_argument('--config', type=Path)
    parser.add_argument('--binding', type=Path)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--manifest-sha256')
    parser.add_argument('--launch-receipt', type=Path)
    args = parser.parse_args()
    if args.phase == 'stage':
        require(args.config is not None and args.binding is not None, 'local_config_and_binding_required')
        result = stage(args.config, args.binding, args.manifest)
    else:
        require(args.manifest_sha256 is not None, 'explicit_manifest_hash_required')
        if args.phase == 'check':
            check(args.manifest, args.manifest_sha256)
            result = dict(status='CPU_BROKER_CHECK_PASS_NATIVE_PREFIX_PENDING', no_calls=True, no_remote_access=True)
        else:
            require(args.launch_receipt is not None, 'explicit_Main_launch_receipt_required')
            result = serve(args.manifest, args.manifest_sha256, args.launch_receipt)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
