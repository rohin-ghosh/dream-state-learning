"""A2-only C52 recovery; keep the original life, parent queue and sealed attempts."""

import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from types import FunctionType

from gpu import orch_math_feedback_uptake_r124_readout as run
from gpu import orch_math_feedback_uptake_r125_runtime_scan as scanner


ROOT = run.ROOT/'A2'
SERVICE = ROOT/'runtime_recovery7'
SOURCE = Path(__file__).resolve().parents[1]
ORIGINAL_SOURCE = Path('/localhome/local-rohing/orch_math_feedback_uptake_r124_readout_source_20260915_v1')
MODULE = 'gpu.orch_r125_a2_boundary_resume'
PYTHON = '/localhome/local-rohing/v2/venv/bin/python'
original_validate = FunctionType(run.validate.__code__, dict(run.validate.__globals__, SOURCE=ORIGINAL_SOURCE))


def continuation_plan(plan, checkpoint, counters, history, carry, cycle):
    result = deepcopy(plan)
    result['initial_history'], result['initial_carry'] = history, carry
    result['contract'].update(initial_checkpoint=deepcopy(checkpoint), initial_optimizer_steps=counters['optimizer_steps'],
        inherited_counters=deepcopy(counters), next_cycle=cycle+1,
        historical_math_optimizer_continuity=True, optimizer_reset=False)
    return result


def prepare():
    plan = original_validate(ROOT)
    run.math.reuse.driver.seam.portable.verify_base_files(run.math.BUNDLE, run.math.MODEL,
        expected_manifest_sha256=run.math.reuse.node_limits.BUNDLE_SHA)
    terminal = run.read(ROOT/'TERMINAL.json')
    counters = run.read(ROOT/'COUNTERS.json')
    committed = run.read(ROOT/'COMMITTED.json')
    cycle = committed['cycle']
    complete = run.read(ROOT/f'cycle{cycle:06d}/COMPLETE.json')
    checkpoint = committed['checkpoint']
    run.require(cycle == 52 and counters['optimizer_steps'] == 21639, 'exact_A2_C52_recovery')
    run.require(terminal['error_type'] == 'FileExistsError' and 'R121_SEP16_0600_FINAL8.json' in terminal['error'],
                'exact_offload_receipt_collision')
    run.require(terminal['last_committed_checkpoint'] == complete['checkpoint'] == checkpoint
                and terminal['counters'] == counters and complete['next_cycle'] == cycle+1,
                'terminal_matches_complete_saved_boundary')
    run.require(not (ROOT/f'cycle{cycle+1:06d}').exists(), 'no_unsaved_next_cycle')
    run.require(run.sha(checkpoint['path']) == checkpoint['path_sha256']
                and run.sha(checkpoint['optimizer_path']) == checkpoint['optimizer_path_sha256'], 'checkpoint_bytes')
    run.native.bridge.AdapterIdentity.from_document(run.read(checkpoint['path'])['adapter']).verify()
    history = run.control.checked(plan['initial_history'])
    paths = []
    for number in range(plan['contract']['next_cycle'], cycle+1):
        output = ROOT/f'cycle{number:06d}'
        run.require(run.read(output/'COMPLETE.json')['cycle'] == number, 'completed_history_cycle')
        history.extend(run.read(output/'ROWS.json'))
        paths.extend([output/'COMPLETE.json', output/'ROWS.json', output/'CARRY.json'])
    for row in history:
        run.require(run.sha(row['source_call_path']) == row['source_call_sha256'], 'TRAIN_source_hash')
        run.shared.replay.verify_source(row, run.read(row['source_call_path']))
    run.require(len({row['source_call_sha256'] for row in history}) == len(history), 'no_duplicate_rehearsal')
    SERVICE.mkdir(exist_ok=False)
    run.write(SERVICE/'HISTORY.json', history)
    run.write(SERVICE/'CARRY.json', run.read(ROOT/f'cycle{cycle:06d}/CARRY.json'))
    resumed = continuation_plan(plan, checkpoint, counters, run.ref(SERVICE/'HISTORY.json'),
                                run.ref(SERVICE/'CARRY.json'), cycle)
    run.write(SERVICE/'RESUME_PLAN.json', resumed)
    preserved = {str(path):run.sha(path) for path in paths+[ROOT/'PLAN.json', ROOT/'TERMINAL.json',
        ROOT/'COMMITTED.json', ROOT/'COUNTERS.json', ROOT/'runtime_recovery5/GUARD_TERMINAL.json']}
    run.write(SERVICE/'PREPARED.json', dict(cycle=cycle, inherited_counters=counters,
        plan=run.ref(SERVICE/'RESUME_PLAN.json'), original_plan=run.ref(ROOT/'PLAN.json'),
        preserved=preserved, history_rows=len(history), reset=False,
        rng_scope='SAVED_TORCH_CPU_AND_CUDA; PYTHON_RNG_NOT_IN_ORIGINAL_CHECKPOINT',
        prepared_unix=time.time()))
    return dict(cycle=cycle, optimizer_steps=counters['optimizer_steps'], history_rows=len(history))


def validate(root):
    run.require(Path(root) == ROOT, 'only_A2')
    original_validate(ROOT)
    prepared = run.read(SERVICE/'PREPARED.json')
    run.require(run.sha(ROOT/'PLAN.json') == prepared['original_plan']['sha256'], 'unchanged_parent_binding_plan')
    plan = run.control.checked(prepared['plan'])
    for key in ('initial_history', 'initial_carry'):
        run.control.checked(plan[key])
    checkpoint = plan['contract']['initial_checkpoint']
    run.require(run.sha(checkpoint['path']) == checkpoint['path_sha256']
                and run.sha(checkpoint['optimizer_path']) == checkpoint['optimizer_path_sha256'], 'saved_learning_state')
    tested = run.read(SOURCE/'A2_CPU_TESTS.json')
    run.require(tested['passed'] and tested['builder_entry_pushed'], 'tested_and_posted_repair')
    for name, expected in tested['source_pins'].items():
        run.require(run.sha(SOURCE/name) == expected, 'frozen_recovery_source:'+name)
    return plan


def relocated_write(path, document):
    path = Path(path)
    startup_names = {'MOUNTED_BEFORE.json', 'OPTIMIZER_RESTORED.json', 'LOADED.json', 'ANCHORS.json', 'TERMINAL.json'}
    destination = SERVICE/path.name if path.parent == ROOT and path.name in startup_names else path
    run.write(destination, document)


def resident():
    def no_probe(root, plan):
        run.write(SERVICE/'PROBES_NOT_RETRIED.json', dict(status='PRIOR_ATTEMPTS_PRESERVED',
            next_cycle=plan['contract']['next_cycle'], reset=False))
    restored = FunctionType(run.restore.__code__, dict(run.restore.__globals__, write=relocated_write))
    continuation = FunctionType(run.resident.__code__, dict(run.resident.__globals__,
        validate=validate, paired_probe=no_probe, restore=restored, write=relocated_write))
    continuation(ROOT)


def scan():
    plan = validate(ROOT)
    run.old.admission.life.previous.math.bind()
    return run.old.admission.bind_scan(lambda: scanner.enriched_scan(plan['index'],
        run.control.ORIGINAL/'SERVICE_IDENTITY.json'))


def guard():
    plan = validate(ROOT)
    prepared = run.read(SERVICE/'PREPARED.json')
    for path, expected in prepared['preserved'].items():
        run.require(run.sha(path) == expected, 'unchanged_until_resume:'+path)
    for name in ('GUARD_STARTED.json', 'LAUNCH.json'):
        identity = run.read(ROOT/'runtime_recovery5'/name)['identity']
        run.require(not Path('/proc',str(identity['pid'])).exists(), 'old_actor_or_reused_PID_still_present')
    failed = ROOT/'runtime_recovery6'
    run.require(run.read(failed/'GUARD_TERMINAL.json')['returncode'] == 1
                and not (failed/'LOADED.json').exists() and not (ROOT/'cycle000053').exists(),
                'prior_attempt_failed_before_model_or_new_cycle')
    for name in ('GUARD_STARTED.json', 'LAUNCH.json'):
        identity = run.read(failed/name)['identity']
        run.require(not Path('/proc',str(identity['pid'])).exists(), 'failed_attempt_actor_absent')
    run.write(SERVICE/'GUARD_STARTED.json', dict(identity=run.math.common.process_identity(Path('/proc')/str(os.getpid())),
                                              started_unix=time.time()))
    command = ['sudo','-n','env','CUDA_VISIBLE_DEVICES=','PYTHONDONTWRITEBYTECODE=1',
        'PYTHONPATH='+str(SOURCE), PYTHON,'-B','-m',MODULE,'scan']
    scanned = subprocess.run(command, capture_output=True, text=True, timeout=180)
    run.require(scanned.returncode == 0, 'privileged_scan_failed:'+scanned.stderr[-1000:])
    report = json.loads(scanned.stdout)
    run.write(SERVICE/'ADMISSION.json', report)
    run.require(report['clear'] and report['scanner_euid'] == 0 and report['gpu']['uuid'] == plan['uuid'],
                'fresh_strict_A2_admission')
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES=plan['uuid'], PYTHONPATH=str(SOURCE),
        PYTHONDONTWRITEBYTECODE='1', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
        OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
    with (SERVICE/'native.log').open('x') as log:
        actor = subprocess.Popen([PYTHON,'-B','-m',MODULE,'resident'], env=environment,
            cwd=SOURCE, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        identity = run.math.common.process_identity(Path('/proc')/str(actor.pid))
        run.write(SERVICE/'LAUNCH.json', dict(identity=identity, started_unix=time.time(), reset=False))
        try:
            actor.wait(timeout=max(.1,plan['bounds']['hard_end_unix']-time.time()))
        except subprocess.TimeoutExpired:
            run.math.common.stop_owned(actor, identity)
        run.write(SERVICE/'GUARD_TERMINAL.json', dict(returncode=actor.returncode, identity=identity,
                                                  finished_unix=time.time()))


def configure():
    run.control.ROOT, run.control.SOURCE, run.control.MODULE, run.control.validate = run.ROOT, SOURCE, MODULE, validate


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('prepare', 'guard', 'resident', 'scan', 'readout'))
    parser.add_argument('--root', type=Path)
    parser.add_argument('--binding', type=Path)
    arguments = parser.parse_args()
    configure()
    if arguments.phase in ('prepare', 'scan'):
        print(json.dumps(globals()[arguments.phase]()))
    elif arguments.phase == 'readout':
        run.old.readout(arguments.root, arguments.binding)
    else:
        globals()[arguments.phase]()
