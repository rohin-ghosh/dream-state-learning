"""Separate R118 evaluation-only route scheduling; never selects a checkpoint."""

import argparse
from copy import deepcopy
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


START = 1789491600
END = START + 1200
CALLS = 48
SCHEMA = 'R118_ROUTE_FINAL_EVALUATION_V1'
OWNED = {'F1': (0, 'GPU-f237c5b5-c2a3-b377-92ee-46cf2658db9a'),
         'A1': (4, 'GPU-94c9a79c-8b13-5679-ad35-8dda3fe5c94d')}
MODULE = 'gpu.orch_r111_route_pair_shared'


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def read(path):
    return json.loads(Path(path).read_bytes())


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def ref(path):
    return dict(path=str(Path(path).resolve(strict=True)), sha256=sha(path))


def bound(reference):
    require(sha(reference['path']) == reference['sha256'], 'immutable_reference')
    return read(reference['path'])


def write(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + '.' + str(os.getpid()) + '.tmp')
    with temporary.open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    try:
        os.link(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def module_from(reference, name):
    require(sha(reference['path']) == reference['sha256'], 'pinned_helper')
    spec = importlib.util.spec_from_file_location(name, reference['path'])
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def window(config, now):
    require(config['start_unix'] == START and config['end_unix'] <= END, 'fixed_evaluation_window')
    require(START <= now < config['end_unix'], 'not_in_FINAL_window')


def prepare(branch, original, root, control_reference, selector_reference, cpu_reference):
    require(branch in OWNED, 'owned_route_branch')
    original, root = Path(original).resolve(strict=True), Path(root).resolve()
    require(not root.exists(), 'new_evaluation_root_only')
    control = bound(control_reference)
    owned = control['routes'][branch]
    require(owned['root'] == str(original), 'actual_owned_predecessor_root')
    plan = bound(owned['plan'])
    physical, uuid = OWNED[branch]
    require(plan['physical'] == physical and plan['uuid'] == uuid, 'exact_physical_UUID')
    require(plan['decoder']['do_sample'] is False and plan['decoder']['num_beams'] == 1
            and plan['decoder']['readout_max_new_tokens'] == 2048, 'original_default_decoder')
    for path, expected in plan['source_files'].items():
        require(sha(path) == expected, 'frozen_runtime_source')
    require(sha(selector_reference['path']) == selector_reference['sha256'], 'selector_source_binding')
    cpu = bound(cpu_reference)
    require(cpu['exitcode'] == 0 and cpu['CUDA_VISIBLE_DEVICES'] == ''
            and cpu['model_calls'] == cpu['provider_calls'] == cpu['real_FINAL_reads'] == 0
            and cpu['source_sha256'] == sha(__file__)
            and cpu['selector_sha256'] == selector_reference['sha256'], 'exact_CPU_provenance')
    end = min(END, plan['bounds']['lease_end_unix'] - 21600)
    require(time.time() < START < end, 'prepare_before_FINAL_and_within_lease')
    runtime = Path(owned['source_root'])
    executable = runtime / 'gpu/orch_r111_route_pair_shared.py'
    require(plan['source_files'].get(str(executable)) == sha(executable), 'actual_readout_source')
    config = dict(schema=SCHEMA, branch=branch, original_root=str(original), root=str(root),
        predecessor_plan=owned['plan'], predecessor_bounds=plan['bounds'], cutoff=control_reference,
        selector_source=selector_reference, selection_path=str(Path(control['common']) / 'FINAL_SELECTION.json'),
        common=control['common'], common_config=control['immutable']['CONFIG.json'],
        common_lineage=control['immutable'],
        source=ref(__file__), cpu=cpu_reference, runtime_source=str(runtime), runtime_executable=ref(executable),
        sealed_final=dict(path=str(original / 'SEALED_FINAL.json'), sha256=plan['final_sha256']),
        physical=physical, uuid=uuid, start_unix=START, end_unix=end, native_calls=CALLS,
        parent_calls=0, optimizer_steps=0, training_rows=0, evaluation_buffer=False,
        default_decoder=plan['decoder'], max_target_tokens=8 * 2048,
        authorization='R118_MAIN_FINAL_READOUT_SCOPE_2026-09-15T13:07Z',
        no_old_ledger_reset=True, no_early_FINAL_reads=True, prepared_unix=time.time())
    evaluation = deepcopy(plan)
    evaluation.pop('shared_learner', None)
    evaluation.update(root=str(root), mode='EVALUATION_ONLY_CANONICAL_COMMITTED_SHARED_CHECKPOINT',
        initial_optimizer='NONE_EVALUATION_ONLY', sleep0_required=False,
        bounds=dict(native_calls=CALLS, parent_calls=0, cycles=0, hard_end_unix=end,
                    gpu_hours=(end-START)/3600, lease_end_unix=plan['bounds']['lease_end_unix'],
                    lease_margin_seconds=21600), final_readouts=['2026-09-15T17:00:00Z'],
        evaluation_only=True, parenting_and_training_forbidden=True,
        canonical_selection_path=config['selection_path'])
    root.mkdir(parents=True, mode=0o700)
    write(root / 'PLAN.json', evaluation)
    config['evaluation_plan'] = ref(root / 'PLAN.json')
    write(root / 'EVALUATION.json', config)
    return ref(root / 'EVALUATION.json')


def validate_config(reference):
    config = bound(reference)
    require(config['schema'] == SCHEMA and config['branch'] in OWNED, 'evaluation_schema_scope')
    require((config['physical'], config['uuid']) == OWNED[config['branch']], 'evaluation_UUID')
    require(config['native_calls'] == CALLS and config['parent_calls'] == 0
            and config['optimizer_steps'] == 0 and config['training_rows'] == 0
            and config['evaluation_buffer'] is False, 'evaluation_only_bounds')
    require(config['source'] == ref(__file__), 'scheduler_source_unchanged')
    cpu = bound(config['cpu'])
    require(cpu['exitcode'] == 0 and cpu['source_sha256'] == config['source']['sha256']
            and cpu['selector_sha256'] == config['selector_source']['sha256'], 'bound_CPU_receipt')
    plan = bound(config['evaluation_plan'])
    require(plan['root'] == config['root'] and plan['bounds']['native_calls'] == CALLS
            and plan['bounds']['parent_calls'] == 0 and plan['bounds']['cycles'] == 0
            and plan['bounds']['hard_end_unix'] == config['end_unix'], 'explicit_separate_ledger_bounds')
    require(config['end_unix'] == min(END, plan['bounds']['lease_end_unix']-21600), 'actual_lease_margin')
    require(plan['decoder'] == config['default_decoder'], 'unchanged_decoder')
    bound(config['predecessor_plan'])
    require(sha(config['runtime_executable']['path']) == config['runtime_executable']['sha256'],
            'frozen_runtime_unchanged')
    for path, expected in plan['source_files'].items():
        require(sha(path) == expected, 'frozen_source_closure')
    bound(config['common_config'])
    return config


def completed_morning(original, now):
    require(now >= START, 'no_early_FINAL_inspection')
    for path in sorted((Path(original) / 'sealed_final_readouts').glob('readout_*/COMPLETE.json')):
        if path.parent.name == 'readout_0000':
            continue
        document = read(path)
        if document.get('scope') == 'FINAL' and document.get('finished_unix', 0) >= START:
            return ref(path)
    return None


def release_evidence(config):
    control = bound(config['cutoff'])
    guard = module_from(control['source'], 'route_FINAL_release_guard')
    guard.validate(control)
    directory = Path(control['directory'])
    require((directory / 'COMPLETED.json').exists(), 'actual_cutoff_completion_required')
    path = directory / config['branch'] / 'DISPOSITION.json'
    disposition = read(path)
    require(disposition['status'] in ('RELEASED', 'PREDECESSOR_ALREADY_EXITED'), 'confirmed_route_release')
    spec = control['routes'][config['branch']]
    identities = [spec['supervisor'], spec['initial_actor']]
    identities += [item['identity'] for item in disposition.get('processes', [])]
    require(all(not guard.alive(identity) for identity in identities), 'owned_predecessors_absent')
    return dict(completed=ref(directory / 'COMPLETED.json'), disposition=ref(path))


def selection_checkpoint(config, now):
    window(config, now)
    selector = module_from(config['selector_source'], 'canonical_FINAL_selection_consumer')
    require(selector.SCHEMA == 'R118_FINAL_SELECTION_V1', 'actual_Main_selection_contract')
    path = Path(config['selection_path'])
    require(path == Path(config['common']) / 'FINAL_SELECTION.json', 'canonical_marker_only')
    before = ref(path)
    expected = {name: reference['sha256'] for name, reference in config['common_lineage'].items()}
    selected = selector.validate_selection(Path(config['common']), config_sha256=expected['CONFIG.json'],
        initialized_sha256=expected['INITIALIZED.json'], adoption_sha256=expected['ADOPTION.json'],
        clock=lambda: now)
    require(selected['selected_unix'] <= now, 'no_future_selection_timestamp')
    require(ref(path) == before, 'selection_not_changed_during_validation')
    return selected


def materialize(config, now):
    window(config, now)
    root = Path(config['root'])
    require(sha(config['sealed_final']['path']) == config['sealed_final']['sha256'], 'original_sealed_inventory')
    sealed = read(config['sealed_final']['path'])
    require(len(sealed['tasks']) == 8 and len({row['id'] for row in sealed['tasks']}) == 8, 'exact_sealed_eight')
    for name in ('COHORT.json', 'SEALED_FINAL.json'):
        os.symlink(Path(config['original_root']) / name, root / name)
    write(root / 'FINAL_INVENTORY_BINDING.json', dict(ids=[row['id'] for row in sealed['tasks']],
        source=config['sealed_final'], inspected_unix=now, visibility='SEALED_EVALUATION_ONLY'))
    plan = read(root / 'PLAN.json')
    write(root / 'PUBLICATION.json', dict(plan_sha256=sha(root / 'PLAN.json'), cpu_tests_passed=True,
        cpu=config['cpu'], coordination_reference=config['authorization'], evaluation_only=True))
    if config['branch'] == 'F1':
        write(root / 'ROHIN_GO.json', dict(authorization='WATCHER_RELAYED_ROHIN_DONE',
            plan_sha256=sha(root / 'PLAN.json'), parent_prompt_sha256=plan['parent_prompt_sha256'],
            source_reference=config['authorization'], provider_calls_authorized=0))


def admission(config):
    root = Path(config['root'])
    prefix = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
        'PYTHONPATH='+config['runtime_source'], 'python3', '-B', '-m', MODULE]
    for phase, timeout in (('service', 90), ('scan', 100)):
        window(config, time.time())
        receipt = subprocess.run(prefix + [phase, '--root', str(root)], capture_output=True,
                                 check=True, timeout=min(timeout, config['end_unix']-time.time()))
        if phase == 'scan':
            report = json.loads(receipt.stdout)
    require(report['clear'] is True and time.time()-report['scanned_unix'] < 30, 'strict_fresh_CLEAR')
    write(root / 'ADMISSION.json', report)
    return ref(root / 'ADMISSION.json')


def command(config, checkpoint):
    return [sys.executable, '-B', '-m', MODULE, 'readout', '--root', config['root'],
            '--sleep-index', '1', '--checkpoint', checkpoint['path'], '--scope', 'final']


def environment(config):
    result = {key: value for key, value in os.environ.items()
              if not key.startswith(('PARENT_', 'CLAUDE_', 'ANTHROPIC_', 'OPENAI_'))}
    result.update(CUDA_VISIBLE_DEVICES=config['uuid'], PYTHONPATH=config['runtime_source'],
                  PYTHONDONTWRITEBYTECODE='1', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
    return result


def finish_child(process, descriptor, deadline, grace_seconds=5):
    signals = []
    try:
        return process.wait(timeout=max(.001, deadline-time.time()-grace_seconds)), signals
    except subprocess.TimeoutExpired:
        try:
            signal.pidfd_send_signal(descriptor, signal.SIGTERM)
            signals.append('SIGTERM')
        except ProcessLookupError:
            return process.wait(timeout=1), signals
        try:
            return process.wait(timeout=max(.001, deadline-time.time())), signals
        except subprocess.TimeoutExpired:
            try:
                signal.pidfd_send_signal(descriptor, signal.SIGKILL)
                signals.append('SIGKILL_AT_BOUND')
            except ProcessLookupError:
                pass
            return process.wait(timeout=10), signals


def dispatch(config):
    root = Path(config['root'])
    window(config, time.time())
    require(not (root / 'ATTEMPT.json').exists(), 'prior_attempt_preserved_no_replay')
    prior = completed_morning(config['original_root'], time.time())
    if prior:
        write(root / 'SKIPPED_ALREADY_COMPLETE.json', dict(original_complete=prior, no_calls=True))
        return
    release = release_evidence(config)
    selected = selection_checkpoint(config, time.time())
    checkpoint = selected['checkpoint']
    write(root / 'ATTEMPT.json', dict(started_unix=time.time(), release=release,
        selection=ref(config['selection_path']), checkpoint=checkpoint, no_retry=True))
    materialize(config, time.time())
    admission(config)
    window(config, time.time())
    require(selection_checkpoint(config, time.time()) == selected, 'same_canonical_selection_before_launch')
    require(completed_morning(config['original_root'], time.time()) is None, 'morning_completed_during_admission')
    require(config['end_unix']-time.time() > 5, 'insufficient_remaining_evaluation_wall')
    output = root / 'sealed_final_readouts/readout_0001'
    output.mkdir(parents=True, mode=0o700)
    with (output / 'process.log').open('x') as stream:
        process = subprocess.Popen(command(config, checkpoint), env=environment(config),
            stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
    descriptor = os.pidfd_open(process.pid)
    try:
        write(root / 'DISPATCH.json', dict(pid=process.pid, started_unix=time.time(),
            checkpoint=checkpoint, selection=ref(config['selection_path']), fresh_process=True,
            parents=False, training=False, command=command(config, checkpoint)))
        deadline = min(config['end_unix'], time.time()+415)
        returncode, sent = finish_child(process, descriptor, deadline)
        if sent:
            write(root / 'TIMEOUT.json', dict(deadline_unix=deadline, observed_unix=time.time(),
                pid=process.pid, exact_owned_pidfd=True, signals=sent, partial_calls_preserved=True))
        complete = output / 'COMPLETE.json'
        rows = [json.loads(line) for line in (root / 'RESERVATIONS.jsonl').read_text().splitlines()] \
            if (root / 'RESERVATIONS.jsonl').exists() else []
        require(len(rows) <= CALLS and all(row['kind'] == 'NATIVE' for row in rows), 'evaluation_charges_only')
        write(root / 'FINISHED.json', dict(returncode=returncode, finished_unix=time.time(),
            complete=ref(complete) if complete.exists() else None, native_calls=len(rows), parent_calls=0,
            optimizer_steps=0, checkpoint=checkpoint, selected=ref(config['selection_path']),
            success=returncode == 0 and complete.exists(), no_replay=True))
    finally:
        os.close(descriptor)


def wait(reference):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_only_scheduler')
    config = validate_config(reference)
    root = Path(config['root'])
    with (root / 'SCHEDULER.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        write(root / 'SCHEDULER_STARTED.json', dict(pid=os.getpid(), started_unix=time.time(),
            config=reference, CUDA_VISIBLE_DEVICES=os.environ.get('CUDA_VISIBLE_DEVICES'), GPU_calls=0))
        while time.time() < START:
            time.sleep(max(0, min(5, START-time.time())))
        while time.time() < config['end_unix']:
            control = bound(config['cutoff'])
            if Path(config['selection_path']).exists() and (Path(control['directory'])/'COMPLETED.json').exists():
                try:
                    dispatch(validate_config(reference))
                except Exception as error:
                    write(root / 'FAILED.json', dict(exception_type=type(error).__name__,
                        error_sha256=hashlib.sha256(str(error).encode()).hexdigest(),
                        failed_unix=time.time(), no_retry=True, partials_preserved=True))
                    raise
                return
            time.sleep(min(5, max(0, config['end_unix']-time.time())))
        write(root / 'NOT_RUN_BOUND.json', dict(finished_unix=time.time(),
            reason='SELECTION_OR_RELEASE_UNAVAILABLE_WITHIN_NEW_EVALUATION_BOUND', no_calls=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('prepare', 'wait'))
    parser.add_argument('--branch', choices=tuple(OWNED))
    parser.add_argument('--original', type=Path)
    parser.add_argument('--root', type=Path)
    parser.add_argument('--control', type=Path)
    parser.add_argument('--control-sha256')
    parser.add_argument('--selector', type=Path)
    parser.add_argument('--selector-sha256')
    parser.add_argument('--cpu', type=Path)
    parser.add_argument('--cpu-sha256')
    parser.add_argument('--config', type=Path)
    parser.add_argument('--config-sha256')
    arguments = parser.parse_args()
    if arguments.phase == 'prepare':
        result = prepare(arguments.branch, arguments.original, arguments.root,
            dict(path=str(arguments.control), sha256=arguments.control_sha256),
            dict(path=str(arguments.selector), sha256=arguments.selector_sha256),
            dict(path=str(arguments.cpu), sha256=arguments.cpu_sha256))
        print(json.dumps(result))
    else:
        wait(dict(path=str(arguments.config), sha256=arguments.config_sha256))
