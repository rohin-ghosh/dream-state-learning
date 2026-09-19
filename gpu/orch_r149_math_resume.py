"""Exact F2 C96 recovery with a prospective, independently pinned TRAIN suffix."""

import argparse
from copy import deepcopy
import fcntl
import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from types import FunctionType


ROOT = Path('/localhome/local-rohing/orch_r139_math_astra_handoff_20260916_v1/F2')
SOURCE = Path('/localhome/local-rohing/orch_r139_math_astra_handoff_source_20260916_v1')
SERVICE = ROOT/'runtime_r149_cohort96_20260916t1920z_candidate2'
PYTHON = '/localhome/local-rohing/v2/venv/bin/python'
PLAN_SHA = '498b94f8c3662918d88a7d79072e094870c29b04831d858cb0fa737ec9cf24c2'
CHECKPOINT_SHA = 'f1b6bd6352aaccbf64660c43d51b56562eab0c68f0fff02f0b97b64a91c18305'
OPTIMIZER_SHA = 'c427b0bc7af21562dec475200d6b9cdeb9ee994b6a7187ecc3fbed5df1f81a5f'
STARTUP = {'MOUNTED_BEFORE.json', 'OPTIMIZER_RESTORED.json', 'LOADED.json', 'ANCHORS.json', 'TERMINAL.json'}


def require(condition, code):
    if not condition:
        raise ValueError(code)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n')


def ref(path):
    return {'path': str(Path(path).resolve(strict=True)), 'sha256': sha(path)}


def checked(reference):
    require(sha(reference['path']) == reference['sha256'], 'immutable_reference')
    return read(reference['path'])


def modules():
    sys.path.insert(0, str(SOURCE))
    handoff = importlib.import_module('gpu.orch_r139_math_astra_handoff')
    require(Path(handoff.__file__).resolve() == SOURCE/'gpu/orch_r139_math_astra_handoff.py', 'frozen_handoff_import')
    run, _ = handoff.native_modules()
    return handoff, run


def boundary(terminal, counters, committed, complete, sleep, next_exists):
    require(terminal['status'] == 'FAILED' and terminal['error'] ==
            'prospective_cohort_extension_required_before_dispatch', 'only_exhausted_cohort')
    require(committed['cycle'] == complete['cycle'] == 96 and complete['next_cycle'] == 97,
            'exact_C96_boundary')
    checkpoint = committed['checkpoint']
    require(checkpoint == complete['checkpoint'] == sleep['checkpoint'] == terminal['last_committed_checkpoint'],
            'same_saved_checkpoint')
    require(checkpoint['path_sha256'] == CHECKPOINT_SHA and checkpoint['optimizer_path_sha256'] == OPTIMIZER_SHA,
            'exact_C96_checkpoint_hashes')
    require(counters == terminal['counters'] and counters['optimizer_steps'] ==
            sleep['cumulative_optimizer_steps'] == 48021, 'exact_saved_counters')
    require(counters['native'] == 2494 and counters['parent'] == 232 and not next_exists,
            'no_unsaved_next_cycle_or_charges')
    return deepcopy(checkpoint)


def continuation_plan(prior, checkpoint, counters, history, carry, train):
    result = deepcopy(prior)
    result.update(initial_history=history, initial_carry=carry, train=train)
    result['contract'].update(initial_checkpoint=deepcopy(checkpoint), initial_optimizer_steps=counters['optimizer_steps'],
                              inherited_counters=deepcopy(counters), next_cycle=97)
    return result


def redirected_writer(original, root, service):
    def emit(path, value):
        path = Path(path)
        return original(service/path.name if path.parent == root and path.name in STARTUP else path, value)
    return emit


def config_reader(original, old_path, new_path):
    def load(path):
        return original(new_path if Path(path) == old_path else path)
    return load


def collision_clearance(clearance, train_sha256, original_sha256, manifest_sha256):
    require(clearance['passed'] is True and clearance['complete_exclusion_coverage'] is True
            and clearance['exact_prefix'] is True, 'complete_independent_cohort_clearance')
    require(clearance['train_sha256'] == train_sha256 and clearance['original_train_sha256'] == original_sha256
            and clearance['manifest_sha256'] == manifest_sha256, 'exact_collision_checked_bytes')
    require(clearance['task_id_collisions'] == clearance['question_hash_collisions'] == 0
            and clearance['checked_new_task_count'] == 192 and clearance['excluded_id_count'] >= 5846
            and clearance['excluded_question_hash_count'] >= 5838, 'full_inherited_cohort_coverage')
    require(set(clearance['exclusion_sources_sha256']) >= {'original_train', 'dev', 'final', 'inherited_registry'},
            'all_exclusion_sources_bound')


def prepare():
    handoff, run = modules()
    prior = handoff.validate(ROOT)
    require(sha(ROOT/'PLAN.json') == PLAN_SHA, 'unchanged_original_plan')
    checkpoint = boundary(read(ROOT/'TERMINAL.json'), read(ROOT/'COUNTERS.json'), read(ROOT/'COMMITTED.json'),
                          read(ROOT/'cycle000096/COMPLETE.json'), read(ROOT/'cycle000096/sleep/COMPLETE.json'),
                          (ROOT/'cycle000097').exists())
    require(not Path('/proc/2627464').exists(), 'original_actor_or_reused_PID_present')
    for key in ('path', 'optimizer_path'):
        require(sha(checkpoint[key]) == checkpoint[key+'_sha256'], 'saved_checkpoint_bytes')
    run.native.bridge.AdapterIdentity.from_document(read(checkpoint['path'])['adapter']).verify()
    original_train, new_train = checked(prior['train']), read(SERVICE/'TRAIN.json')
    require(len(original_train) == 96 and len(new_train) > 96 and new_train[:96] == original_train,
            'prospective_cohort_exact_prefix')
    collision_clearance(read(SERVICE/'COLLISION_CLEARANCE.json'), sha(SERVICE/'TRAIN.json'),
                        prior['train']['sha256'], sha(SERVICE/'COHORT.json'))
    history = checked(prior['initial_history'])
    preserved = {str(ROOT/name): sha(ROOT/name) for name in
                 ('PLAN.json', 'TERMINAL.json', 'COMMITTED.json', 'COUNTERS.json', 'GUARD_TERMINAL.json')}
    for cycle in range(prior['contract']['next_cycle'], 97):
        output = ROOT/f'cycle{cycle:06d}'
        require(read(output/'COMPLETE.json')['next_cycle'] == cycle+1, 'fully_completed_history_cycle')
        rows = read(output/'ROWS.json')
        require(len(rows) == 6, 'six_original_rows_per_cycle')
        history.extend(rows)
        for name in ('ROWS.json', 'CARRY.json', 'COMPLETE.json', 'sleep/COMPLETE.json'):
            preserved[str(output/name)] = sha(output/name)
    for row in history:
        require(sha(row['source_call_path']) == row['source_call_sha256'], 'original_TRAIN_row_source')
        run.shared.replay.verify_source(row, read(row['source_call_path']))
    require(len({row['source_call_sha256'] for row in history}) == len(history), 'history_no_double_replay')
    write(SERVICE/'HISTORY.json', history)
    write(SERVICE/'CARRY.json', read(ROOT/'cycle000096/CARRY.json'))
    counters = read(ROOT/'COUNTERS.json')
    resumed = continuation_plan(prior, checkpoint, counters, ref(SERVICE/'HISTORY.json'),
                                ref(SERVICE/'CARRY.json'), ref(SERVICE/'TRAIN.json'))
    write(SERVICE/'RESUME_PLAN.json', resumed)
    inventory = handoff.inventory(ROOT)
    require(not inventory['unfinished_claims'], 'unfinished_provider_claim_needs_disposition')
    write(SERVICE/'EPOCH.json', dict(counters=counters, parent_high_water=counters['parent'], next_cycle=97,
                                    historical_ids=inventory['historical_ids'], observed_unix=time.time(),
                                    no_historical_replay=True))
    tests = read(SERVICE/'CPU_TESTS.json')
    require(tests['passed'] is True and tests['source_sha256'] == sha(__file__), 'tested_recovery_bytes')
    write(SERVICE/'PREPARED.json', dict(plan=ref(SERVICE/'RESUME_PLAN.json'), epoch=ref(SERVICE/'EPOCH.json'),
          original_plan=ref(ROOT/'PLAN.json'), source=ref(__file__), tests=ref(SERVICE/'CPU_TESTS.json'),
          cohort=ref(SERVICE/'COHORT.json'), clearance=ref(SERVICE/'COLLISION_CLEARANCE.json'),
          preserved=preserved, history_rows=len(history),
          optimizer_reset=False, adapter_reset=False, prepared_unix=time.time(),
          rng_scope='EXACT_SAVED_TORCH_CPU_CUDA; PYTHON_RNG_NOT_IN_ORIGINAL_CHECKPOINT'))
    return {'status': 'PREPARED_NOT_LAUNCHED', 'prepared': ref(SERVICE/'PREPARED.json'), 'history_rows': len(history)}


def validate():
    handoff, run = modules()
    prior = handoff.validate(ROOT)
    prepared = read(SERVICE/'PREPARED.json')
    require(sha(__file__) == prepared['source']['sha256'], 'exact_recovery_source')
    require(sha(ROOT/'PLAN.json') == PLAN_SHA == prepared['original_plan']['sha256'], 'old_plan_unchanged')
    require(checked(prepared['tests'])['passed'] is True, 'CPU_tests_passed')
    checked(prepared['cohort'])
    checked(prepared['epoch'])
    plan = checked(prepared['plan'])
    for name in ('initial_history', 'initial_carry', 'train'):
        checked(plan[name])
    collision_clearance(checked(prepared['clearance']), plan['train']['sha256'],
                        prior['train']['sha256'], prepared['cohort']['sha256'])
    checkpoint = plan['contract']['initial_checkpoint']
    for key in ('path', 'optimizer_path'):
        require(sha(checkpoint[key]) == checkpoint[key+'_sha256'], 'resume_checkpoint_bytes')
    expected = continuation_plan(prior, checkpoint, read(SERVICE/'EPOCH.json')['counters'],
                                 plan['initial_history'], plan['initial_carry'], plan['train'])
    require(plan == expected and plan['bounds'] == prior['bounds'], 'only_saved_boundary_and_TRAIN_delta')
    return handoff, run, plan


def resident():
    handoff, run, plan = validate()
    config = read(SERVICE/'BROKER_CONFIG.json')
    require(config['cohort_sha256'] == plan['train']['sha256'], 'native_parent_same_TRAIN_cohort')
    ready = read(SERVICE/'BROKER_ACTIVE.json')
    require(ready['config_sha256'] == sha(SERVICE/'BROKER_CONFIG.json') and ready['model'] == handoff.MODEL,
            'same_Astra_broker_ready')
    run.control.ROOT, run.control.SOURCE = ROOT.parent, SOURCE
    run.control.MODULE, run.control.validate = handoff.MODULE, handoff.validate
    run.control.append_parent = FunctionType(run.control.append_parent.__code__,
        dict(run.control.append_parent.__globals__, read=config_reader(run.control.read,
             handoff.QUEUE/'parent_claude/CONFIG.json', SERVICE/'BROKER_CONFIG.json')))
    emit = redirected_writer(run.write, ROOT, SERVICE)
    restore = FunctionType(run.restore.__code__, dict(run.restore.__globals__, write=emit))
    def readout(root, actor, selected_plan, checkpoint, key, split='DEV'):
        if split == 'FINAL' and handoff.final_seen(root, key):
            return {'status': 'EXISTING_ATTEMPT_NEVER_RETRIED'}
        return run.offloaded_readout(root, actor, selected_plan, checkpoint, key, split)
    entry = FunctionType(run.resident.__code__, dict(run.resident.__globals__, validate=lambda root: validate()[2],
        paired_probe=lambda root, selected_plan: None, restore=restore, write=emit, offloaded_readout=readout))
    entry(ROOT)


def guard():
    handoff, run, plan = validate()
    go = read(SERVICE/'MAIN_GO.json')
    require(go['authorized'] is True and go['prepared_sha256'] == sha(SERVICE/'PREPARED.json')
            and bool(go['publication']), 'dated_bound_builder_publication')
    ready = read(SERVICE/'BROKER_ACTIVE.json')
    require(ready['config_sha256'] == sha(SERVICE/'BROKER_CONFIG.json') and ready['model'] == handoff.MODEL,
            'prospective_Astra_broker_ready_before_native')
    with (SERVICE/'GUARD.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        prepared = read(SERVICE/'PREPARED.json')
        for path, expected in prepared['preserved'].items():
            require(sha(path) == expected, 'unchanged_until_resume:'+path)
        require(not Path('/proc/2627464').exists() and not (ROOT/'cycle000097').exists(), 'original_actor_absent')
        write(SERVICE/'GUARD_STARTED.json', dict(pid=os.getpid(), started_unix=time.time()))
        actor = None
        try:
            command = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
                       'PYTHONPATH='+str(SOURCE), PYTHON, '-B', str(Path(__file__).resolve()), 'scan']
            scanned = subprocess.run(command, capture_output=True, text=True, timeout=180)
            require(scanned.returncode == 0, 'privileged_scan_failed:'+scanned.stderr[-1500:])
            report = json.loads(scanned.stdout)
            write(SERVICE/'ADMISSION.json', report)
            require(report['clear'] and report['scanner_euid'] == 0 and report['gpu']['uuid'] == plan['uuid'],
                    'fresh_strict_F2_admission_no_waiver')
            environment = dict(os.environ, CUDA_VISIBLE_DEVICES=plan['uuid'], PYTHONPATH=str(SOURCE),
                PYTHONDONTWRITEBYTECODE='1', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', PYTORCH_CUDA_ALLOC_CONF='expandable_segments:True')
            with (SERVICE/'native.log').open('x') as log:
                actor = subprocess.Popen([PYTHON, '-B', str(Path(__file__).resolve()), 'resident'], env=environment,
                    cwd=SOURCE, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                identity = run.math.common.process_identity(Path('/proc')/str(actor.pid))
                write(SERVICE/'LAUNCH.json', dict(identity=identity, started_unix=time.time(), plan=prepared['plan']))
                try:
                    actor.wait(timeout=max(.1, plan['bounds']['hard_end_unix']-time.time()))
                except subprocess.TimeoutExpired:
                    run.math.common.stop_owned(actor, identity)
                write(SERVICE/'GUARD_TERMINAL.json', dict(returncode=actor.returncode, finished_unix=time.time()))
        except BaseException as error:
            write(SERVICE/'GUARD_FAILURE.json', dict(error_type=type(error).__name__, error=str(error),
                  native_started=actor is not None, finished_unix=time.time()))
            raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('prepare', 'validate', 'scan', 'guard', 'resident'))
    args = parser.parse_args()
    if args.phase == 'scan':
        handoff, run, plan = validate()
        print(json.dumps(handoff.run_native('scan')))
    elif args.phase == 'validate':
        handoff, run, plan = validate()
        print(json.dumps({'status': 'CPU_VALIDATED_NOT_LAUNCHED', 'next_cycle': plan['contract']['next_cycle']}))
    else:
        result = globals()[args.phase]()
        if result is not None:
            print(json.dumps(result, sort_keys=True))
