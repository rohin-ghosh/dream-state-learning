"""Separate, one-shot sealed grid FINAL evaluation; no parenting or training."""

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from types import SimpleNamespace


START = 1789491600
END = 1789492800
LEASE_END = int(datetime(2026, 9, 17, 4, 4, tzinfo=timezone.utc).timestamp())
ROOT = Path('/localhome/local-rohing/orch_r115_grid_pair_20260915')
COMMON = Path('/localhome/local-rohing/orch_r116_shared_node5_20260915_attempt1')
RUNTIME = Path('/localhome/local-rohing/orch_r118_grid_shared_source_20260915_attempt2')
CLOSURE_SHA = '03a2f241f2a043da9de28d9fc6d91fa7dc240b7ce6ef9fa08b2ff2bd92face9d'
COMMON_SHA = 'e5ac72af0d88e4481174f853fbf3951294278b1c9f62c88080f7d4b816cceb51'
INITIALIZED_SHA = 'd4e2c87e97bcfccb639d332d996f9f239023bbaa19f9312ce95d30f3f0aecff6'
ADOPTION_SHA = '6dfc7dcd59e86648478a13852ff740701930f36499c92bef1178d3e645dcf7b5'
SELECTION_SHA = '64ccee2884b1dddafde70da8ccc2795127c8a4553fb6eb1a301484da369334ed'
BASE_SHA = 'a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992'
HOST_SHA = '0cb7eb43862102b79ae0a30d2babfedfbf9598b31967a1a04122c3cf849c746d'
FINAL_SHA = 'ae12939950f8c57fe35e11fc40509b109a88661d3615671d7b371d1ec2f5c578'
FINAL_SPLIT_SHA = 'de7668856d4cd3d0dd91c5798017e34509cb730435cf050f26fca5f9a66a4b90'
IDS = tuple(f'R114_F4_FINAL_{ordinal:02d}' for ordinal in range(1, 9))
BRANCHES = {
    'F4': (3, 'GPU-d23c9369-39cf-51fd-833e-13292f173006',
           'b75690eae7e762834abd9ca824c3deacbdfe1d6d9045e2c8e13dc4fbd2a090a8'),
    'A4': (7, 'GPU-9e6cdf73-7181-4405-2aec-787cc73a3e5b',
           '9aeba909f17ac11f9dc4328c70e8597cd371cfa9d45d4b81894590b80ebb4d21'),
}
PYTHON = '/localhome/local-rohing/v2/venv/bin/python'
HELD_PROMPT = ('Play this grid navigation game using the supplied observation. '
               'When submitting moves, write MOVES: followed by space-separated UP, DOWN, LEFT, RIGHT, or WAIT.')
DECODER = dict(do_sample=False, num_beams=1, no_repeat_ngram_size=4, repetition_penalty=1.0,
               context_limit=16384, held_max_new_tokens=2048, held_batch_size=8,
               truncate_inputs=False, post_generation_deletion=False)


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def ref(path):
    return dict(path=str(Path(path).resolve(strict=True)), sha256=sha(path))


def bound(reference):
    require(sha(reference['path']) == reference['sha256'], 'bound_file_changed')
    return read(reference['path'])


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = path.with_name(path.name + f'.{os.getpid()}.tmp')
    with temporary.open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    try:
        os.link(temporary, path)
    finally:
        temporary.unlink()


def window(now, deadline):
    require(START <= now < deadline <= min(END, LEASE_END - 21600), 'FINAL_time_window')


def config_for(branch):
    require(branch in BRANCHES, 'only_grid_F4_A4')
    physical, uuid, expected = BRANCHES[branch]
    root = ROOT / branch
    require(sha(root / 'CONFIG.json') == expected, 'original_branch_config')
    config = read(root / 'CONFIG.json')
    require(config['root'] == str(root) and config['physical'] == physical and config['uuid'] == uuid,
            'exact_assigned_grid_device')
    require(config['base_sha256'] == BASE_SHA and config['inputs']['FINAL.json'] == FINAL_SHA
            and config['split_sha256']['FINAL'] == FINAL_SPLIT_SHA, 'original_FINAL_commitment')
    require(all(config['decoder'][key] == value for key, value in DECODER.items())
            and config['prompts']['held'] == HELD_PROMPT, 'original_held_prompt_decoder')
    return config


def selection_api(reference):
    require(sha(reference['path']) == reference['sha256'] == SELECTION_SHA, 'frozen_Main_selection_validator')
    spec = importlib.util.spec_from_file_location('r118_main_final_selection_readonly', reference['path'])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    require(callable(getattr(module, 'validate_selection', None)), 'Main_pure_read_API_required')
    return module


def prepare(branch, output, selection_source):
    config = config_for(branch)
    output = Path(output).resolve()
    require(not output.exists() and not output.is_relative_to(ROOT), 'new_separate_eval_writer')
    require(time.time() < START, 'metadata_preparation_before_FINAL')
    require(sha(COMMON / 'CONFIG.json') == COMMON_SHA, 'original_common_config')
    require(sha(RUNTIME / 'SOURCE_CLOSURE.json') == CLOSURE_SHA, 'frozen_native_runtime')
    selector = ref(selection_source)
    selection_api(selector)
    era = ROOT / branch / 'shared_repair_v1'
    guard, actor = read(era / 'CPU_LAUNCH.json'), read(era / 'LOADED.json')
    require(guard['terminal_filename'] == 'R118_SHARED_REPAIR_TERMINAL.json', 'actual_repair_era')
    plan = dict(schema='R118_GRID_FINAL_EVAL_V1', branch=branch, branch_root=str(ROOT / branch),
        output=str(output), config=ref(ROOT / branch / 'CONFIG.json'), common=str(COMMON),
        common_config_sha256=COMMON_SHA, source=ref(Path(__file__)), runtime=str(RUNTIME),
        selection_validator=selector, initialized_sha256=INITIALIZED_SHA, adoption_sha256=ADOPTION_SHA,
        runtime_closure=ref(RUNTIME / 'SOURCE_CLOSURE.json'), final_ids=list(IDS), ids_sha256=digest(IDS),
        final_file_sha256=FINAL_SHA, final_split_sha256=FINAL_SPLIT_SHA,
        physical=config['physical'], uuid=config['uuid'], model_dir=config['model_dir'],
        base_sha256=BASE_SHA, held_prompt=HELD_PROMPT, decoder=DECODER,
        start_unix=START, end_unix=min(END, LEASE_END - 21600), lease_end_unix=LEASE_END,
        max_native_calls=8, max_parent_calls=0, max_optimizer_steps=0, max_training_calls=0,
        attached_open_calls=0, parent_absent=True, fresh_process=True,
        old_ledger_unchanged=True, final_contents_read=False,
        predecessor_refs=[ref(era / 'CPU_LAUNCH.json'), ref(era / 'LOADED.json')],
        predecessor_processes=[guard['identity'], dict(boot_id=actor['process'][0],
            pid=actor['process'][1], start_ticks=str(actor['process'][2]), uid=guard['identity']['uid'])],
        interpretation='Parenting systems on one common learned child; paired duplicates are not independent models.',
        created_unix=time.time())
    write(output / 'PLAN.json', plan)
    return ref(output / 'PLAN.json')


def validate_plan(plan):
    config = config_for(plan['branch'])
    require(plan['schema'] == 'R118_GRID_FINAL_EVAL_V1' and plan['branch_root'] == str(ROOT / plan['branch']),
            'original_eval_scope')
    require(plan['start_unix'] == START and plan['end_unix'] == min(END, LEASE_END - 21600)
            and plan['lease_end_unix'] == LEASE_END, 'separate_absolute_eval_bounds')
    require(plan['max_native_calls'] == 8 and plan['max_parent_calls'] == 0
            and plan['max_optimizer_steps'] == 0 and plan['max_training_calls'] == 0
            and plan['attached_open_calls'] == 0, 'evaluation_only_quota')
    require(plan['parent_absent'] is True and plan['fresh_process'] is True
            and plan['old_ledger_unchanged'] is True, 'sealed_eval_visibility')
    require(plan['held_prompt'] == HELD_PROMPT and plan['decoder'] == DECODER
            and plan['final_ids'] == list(IDS) and plan['ids_sha256'] == digest(IDS)
            and plan['final_file_sha256'] == FINAL_SHA and plan['final_split_sha256'] == FINAL_SPLIT_SHA,
            'frozen_panel_decoder')
    require(plan['physical'] == config['physical'] and plan['uuid'] == config['uuid']
            and plan['model_dir'] == config['model_dir'] and plan['base_sha256'] == BASE_SHA,
            'native_device_and_base')
    require(bound(plan['config']) == config and plan['common'] == str(COMMON)
            and plan['common_config_sha256'] == sha(COMMON / 'CONFIG.json') == COMMON_SHA,
            'same_common_and_branch')
    require(plan['initialized_sha256'] == sha(COMMON / 'INITIALIZED.json') == INITIALIZED_SHA
            and plan['adoption_sha256'] == sha(COMMON / 'ADOPTION.json') == ADOPTION_SHA,
            'original_shared_initialization_adoption')
    selection_api(plan['selection_validator'])
    require(sha(Path(plan['branch_root']) / 'SERVICE_IDENTITY.json') == config['inputs']['SERVICE_IDENTITY.json'],
            'original_service_identity')
    require(Path(plan['source']['path']).resolve() == Path(__file__).resolve()
            and sha(__file__) == plan['source']['sha256'], 'frozen_evaluator_source')
    require(plan['runtime'] == str(RUNTIME) and plan['runtime_closure'] == ref(RUNTIME / 'SOURCE_CLOSURE.json')
            and plan['runtime_closure']['sha256'] == CLOSURE_SHA, 'frozen_runtime_closure')
    for name, expected in bound(plan['runtime_closure'])['files'].items():
        require(not Path(name).is_absolute() and '..' not in Path(name).parts, 'safe_source_path')
        require(sha(RUNTIME / name) == expected, 'runtime_dependency_changed:' + name)
    for reference in plan['predecessor_refs']:
        bound(reference)
    guard, actor = map(bound, plan['predecessor_refs'])
    require(plan['predecessor_processes'] == [guard['identity'], dict(boot_id=actor['process'][0],
        pid=actor['process'][1], start_ticks=str(actor['process'][2]), uid=guard['identity']['uid'])],
        'bound_current_predecessors')
    return config


def alive(expected):
    try:
        directory = Path('/proc') / str(expected['pid'])
        fields = (directory / 'stat').read_text().rsplit(')', 1)[1].split()
        return (fields[0] != 'Z' and fields[19] == str(expected['start_ticks'])
                and directory.stat().st_uid == expected['uid']
                and Path('/proc/sys/kernel/random/boot_id').read_text().strip() == expected['boot_id'])
    except FileNotFoundError:
        return False


def predecessor_release(plan):
    require(not any(alive(item) for item in plan['predecessor_processes']), 'old_guard_or_actor_still_live')
    return dict(status='RELEASED_OBSERVED_NO_SIGNALS', observed_unix=time.time(),
                processes=plan['predecessor_processes'], predecessor_refs=plan['predecessor_refs'])


def prior_morning(root):
    if list(Path(root).glob('readouts/*/final_morning/COMPLETE.json')):
        return 'COMPLETE_NO_RERUN'
    if list(Path(root).glob('readouts/*/final_morning/STARTED.json')):
        return 'PRIOR_ATTEMPT_NO_RETRY'
    ledger = Path(root) / 'LEDGER.jsonl'
    for line in ledger.read_text().splitlines():
        item = json.loads(line)
        if item.get('kind') == 'NATIVE' and (item.get('purpose') == 'final_morning' or
                item.get('split') == 'FINAL' and (item.get('cycle', 0) > 0 or item['reserved_unix'] >= START)):
            return 'PRIOR_RESERVATION_NO_RETRY'
    return None


def validate_binding(plan, reference, now):
    window(now, plan['end_unix'])
    require(Path(reference['path']) == COMMON / 'FINAL_SELECTION.json', 'Main_common_freeze_only')
    binding = bound(reference)
    validator = selection_api(plan['selection_validator'])
    selected = validator.validate_selection(COMMON, config_sha256=COMMON_SHA,
        initialized_sha256=plan['initialized_sha256'], adoption_sha256=plan['adoption_sha256'], clock=lambda: now)
    require(selected == binding and binding['schema'] == 'R118_FINAL_SELECTION_V1'
            and binding['evaluation_deadline_unix'] == END and binding['scheduled_unix'] == START,
            'canonical_frozen_selection_not_latest_STATE')
    require(binding['shared_root'] == str(COMMON) and plan['branch'] in binding['branches'], 'same_all_eight_selection')
    checkpoint = binding['checkpoint']
    for name in ('path', 'optimizer_path'):
        require(Path(checkpoint[name]).is_absolute() and sha(checkpoint[name]) == checkpoint[name + '_sha256'],
                'checkpoint_optimizer_provenance')
    document = read(checkpoint['path'])
    require(document['complete'] is True and document['optimizer_rng_sha256'] == checkpoint['optimizer_path_sha256']
            and document['adapter']['base_sha256'] == BASE_SHA, 'complete_same_base_checkpoint')
    return binding, document


def validate_dispatch(plan, dispatch):
    output = Path(plan['output'])
    require(dispatch['plan'] == ref(output / 'PLAN.json') and bound(dispatch['plan']) == plan,
            'dispatch_plan_binding')
    require(START <= dispatch['dispatched_unix'] <= time.time() < dispatch['deadline_unix'] == plan['end_unix'],
            'actual_dispatch_within_eval_window')
    require(Path(dispatch['admission']['path']).parent == output / 'admission', 'own_full_scanner_evidence')
    report = bound(dispatch['admission'])
    require(report['clear'] is True and report['scanner_euid'] == 0 and not report['blocking_reasons']
            and report['gpu']['uuid'] == plan['uuid'], 'strict_scoped_admission')
    require(dispatch['release']['processes'] == plan['predecessor_processes']
            and dispatch['release']['status'] == 'RELEASED_OBSERVED_NO_SIGNALS', 'explicit_predecessor_release')


def read_final(plan, now):
    window(now, plan['end_unix'])
    path = Path(plan['branch_root']) / 'FINAL.json'
    require(sha(path) == plan['final_file_sha256'], 'sealed_file_changed')
    tasks = read(path)
    require(len(tasks) == 8 and [task['id'] for task in tasks] == list(IDS)
            and all(task['split'] == 'FINAL' for task in tasks) and digest(tasks) == plan['final_split_sha256'],
            'exact_sealed_eight')
    return tasks


def runtime_imports():
    sys.path.insert(0, str(RUNTIME))
    sys.path.insert(1, str(RUNTIME / 'gpu'))
    from gpu import orch_r116_grid_shared_client as client
    require(Path(client.__file__).resolve().is_relative_to(RUNTIME), 'actual_frozen_import')
    return client


def scan(plan):
    require(hashlib.sha256(socket.gethostname().encode()).hexdigest() == HOST_SHA, 'exact_node5')
    if os.geteuid() != 0:
        command = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
            'python3', '-B', str(Path(__file__).resolve()), 'scan', '--plan', str(Path(plan['output']) / 'PLAN.json'),
            '--plan-sha256', sha(Path(plan['output']) / 'PLAN.json')]
        return json.loads(subprocess.check_output(command, text=True, timeout=100))
    sys.path.insert(0, str(RUNTIME))
    from gpu import orch_r111_route_admission as admission
    admission.original.minor.pinned.policy = SimpleNamespace(DEVICES={plan['physical']: plan['uuid']},
        HOST_SHA=HOST_SHA, require=require,
        allocation=lambda index: require(index == plan['physical'], 'only_owned_grid_eval_device'))
    return admission.scan(plan['physical'], Path(plan['branch_root']) / 'SERVICE_IDENTITY.json')


def readout(plan, dispatch):
    validate_plan(plan)
    validate_dispatch(plan, dispatch)
    window(time.time(), plan['end_unix'])
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == plan['uuid'] and
            ('CUDA_VISIBLE_DEVICES=' + plan['uuid']).encode() in Path('/proc/self/environ').read_bytes().split(b'\0'),
            'fresh_process_exact_device')
    require(prior_morning(plan['branch_root']) is None, 'old_morning_attempt_no_rerun')
    predecessor_release(plan)
    binding, document = validate_binding(plan, dispatch['binding'], time.time())
    output = Path(plan['output'])
    write(Path(plan['branch_root']) / 'R118_FINAL_EVAL_CLAIM.json',
          dict(plan=ref(output / 'PLAN.json'), dispatch=ref(output / 'DISPATCH.json'), pid=os.getpid()))
    client = runtime_imports()
    require(client.grid.policy.HELD_PROMPT == HELD_PROMPT
            and all(client.grid.policy.DECODER[key] == value for key, value in DECODER.items()), 'native_decoder_binding')
    identity = client.native.bridge.AdapterIdentity.from_document(document['adapter'])
    stage = client.native.bridge.StageBinding('R118_FINAL_' + plan['branch'], client.native.bridge.ARMS[0],
        binding['generation'], 'sealed_readout', identity, False, True, dispatch['binding']['sha256'])
    process = client.native.process_identity()
    write(output / 'STARTED.json', dict(process=process, shared_binding=dispatch['binding'],
        parent_calls=0, optimizer_steps=0, training_calls=0, carry_access=False, started_unix=time.time()))
    check = lambda unused: window(time.time(), plan['end_unix'])
    predecessors = tuple((item['boot_id'], item['pid'], int(item['start_ticks']))
                         for item in plan['predecessor_processes']) + (tuple(document['source_process']),)
    loaded = client.native.load_stage(stage, model_dir=plan['model_dir'], device='cuda:0', gpu_uuid=plan['uuid'],
        context=client.native.StageContext(), check=check, predecessor_processes=predecessors)
    require(loaded.optimizer is None, 'never_restore_optimizer_in_eval')
    engine = client.SharedDecoder(loaded)
    tasks = read_final(plan, time.time())
    messages = [[dict(role='system', content=HELD_PROMPT), dict(role='user', content=json.dumps(
        client.grid.policy.public_observation(task, client.grid.policy.game.initial(task)), sort_keys=True))] for task in tasks]
    window(time.time(), plan['end_unix'])
    reservations = [dict(number=ordinal, task_id=task['id'], split='FINAL', purpose='final_morning',
        evaluation_only=True, trainingAllowed=False, reserved_unix=time.time(), cap=2048)
        for ordinal, task in enumerate(tasks, 1)]
    write(output / 'EVAL_LEDGER.json', dict(max_native_calls=8, parent_calls=0, training_calls=0,
        optimizer_steps=0, binding=dispatch['binding'], reservations=reservations))
    responses = engine.batch(messages, 2048)
    response_refs = []
    for item, prompt, response in zip(reservations, messages, responses):
        destination = output / 'sealed_calls' / f'{item["number"]:02d}.json'
        write(destination, dict(item, status='COMPLETE', messages=prompt, response=response,
            shared_binding=dispatch['binding'], finished_unix=time.time()))
        response_refs.append(ref(destination))
    require(len(responses) == 8, 'exact_eight_returned_no_retry')
    window(time.time(), plan['end_unix'])
    engine.verify_base()
    write(output / 'COMPLETE.json', dict(status='COMPLETE', response_refs=response_refs,
        native_calls=8, parent_calls=0, training_calls=0, optimizer_steps=0,
        shared_binding=dispatch['binding'], process=process, parent_absent=True, carry_access=False,
        child_tokens=sum(len(item['token_ids']) for item in responses),
        final_never_parent_head_exchange=True, fresh_process=True, finished_unix=time.time()))


def guard(plan, binding_path):
    validate_plan(plan)
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_scheduler_no_device')
    require(Path(binding_path) == COMMON / 'FINAL_SELECTION.json', 'Main_common_binding_path')
    output = Path(plan['output'])
    (output / 'SCHEDULER_ONCE').mkdir()
    write(output / 'SCHEDULER_STARTED.json', dict(pid=os.getpid(), observed_unix=time.time(), native_calls=0))
    try:
        while time.time() < START:
            time.sleep(min(5, START - time.time()))
        attempt = 0
        while True:
            window(time.time(), plan['end_unix'] - 5)
            old = prior_morning(plan['branch_root'])
            if old or (Path(plan['branch_root']) / 'R118_FINAL_EVAL_CLAIM.json').exists():
                write(output / 'DISPOSITION.json', dict(status='NOT_RUN', reason=old or 'EXISTING_EVAL_CLAIM', native_calls=0))
                return
            if any(alive(item) for item in plan['predecessor_processes']) or not Path(binding_path).exists():
                time.sleep(2)
                continue
            binding_ref = ref(binding_path)
            validate_binding(plan, binding_ref, time.time())
            report = scan(plan)
            write(output / 'admission' / f'{attempt:04d}.json', report)
            attempt += 1
            require(report['gpu']['uuid'] == plan['uuid'], 'scanned_assigned_UUID')
            if report['clear'] and report['scanner_euid'] == 0 and not report['blocking_reasons']:
                break
            time.sleep(2)
        predecessor_release(plan)
        require(prior_morning(plan['branch_root']) is None, 'morning_race_no_retry')
        validate_plan(plan)
        dispatch = dict(plan=ref(output / 'PLAN.json'), binding=binding_ref,
            release=predecessor_release(plan), admission=ref(output / 'admission' / f'{attempt - 1:04d}.json'),
            dispatched_unix=time.time(), deadline_unix=plan['end_unix'])
        write(output / 'DISPATCH.json', dispatch)
        environment = dict(os.environ, CUDA_VISIBLE_DEVICES=plan['uuid'], HF_HUB_OFFLINE='1',
            TRANSFORMERS_OFFLINE='1', PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(RUNTIME) + ':' + str(RUNTIME / 'gpu'),
            OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', TOKENIZERS_PARALLELISM='false')
        duration = max(1, int(plan['end_unix'] - time.time() - 3))
        command = ['timeout', '--signal=TERM', '--kill-after=2s', str(duration) + 's', PYTHON, '-B',
            str(Path(__file__).resolve()), 'readout', '--plan', str(output / 'PLAN.json'),
            '--plan-sha256', sha(output / 'PLAN.json')]
        with (output / 'NATIVE.log').open('x') as log:
            result = subprocess.run(command, env=environment, cwd=RUNTIME, stdin=subprocess.DEVNULL,
                stdout=log, stderr=subprocess.STDOUT)
        write(output / 'TERMINAL.json', dict(status='COMPLETE' if result.returncode == 0 else 'FAILED',
            exit_code=result.returncode, finished_unix=time.time(), no_retry=True))
    except BaseException as error:
        if not (output / 'TERMINAL.json').exists():
            write(output / 'TERMINAL.json', dict(status='FAILED', error_type=type(error).__name__,
                error=str(error), finished_unix=time.time(), no_retry=True))
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'validate', 'guard', 'scan', 'readout'))
    parser.add_argument('--branch', choices=tuple(BRANCHES))
    parser.add_argument('--output', type=Path)
    parser.add_argument('--plan', type=Path)
    parser.add_argument('--plan-sha256')
    parser.add_argument('--selection-source', type=Path)
    parser.add_argument('--binding', type=Path, default=COMMON / 'FINAL_SELECTION.json')
    args = parser.parse_args()
    os.umask(0o077)
    if args.action == 'prepare':
        require(args.branch is not None and args.output is not None and args.selection_source is not None, 'prepare_arguments')
        print(json.dumps(prepare(args.branch, args.output, args.selection_source), sort_keys=True))
        return
    require(args.plan is not None and sha(args.plan) == args.plan_sha256, 'pinned_eval_plan')
    plan = read(args.plan)
    require(args.plan.resolve() == Path(plan['output']) / 'PLAN.json', 'own_plan_path')
    validate_plan(plan)
    if args.action == 'validate':
        print(json.dumps(dict(status='PASS', final_contents_read=False, model_calls=0, parent_calls=0)))
    elif args.action == 'scan':
        window(time.time(), plan['end_unix'])
        print(json.dumps(scan(plan), sort_keys=True))
    elif args.action == 'guard':
        guard(plan, args.binding)
    else:
        readout(plan, read(Path(plan['output']) / 'DISPATCH.json'))


if __name__ == '__main__':
    main()
