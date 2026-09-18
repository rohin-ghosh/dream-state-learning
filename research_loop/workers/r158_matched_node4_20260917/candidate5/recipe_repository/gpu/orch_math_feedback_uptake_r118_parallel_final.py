"""Custody-only successor for the SAME eight-call canonical math FINAL allocation."""

import argparse
from copy import deepcopy
import fcntl
import json
import os
from pathlib import Path
import subprocess
import time
from types import FunctionType

from gpu import orch_math_feedback_uptake_r118_final as original
from gpu import orch_math_feedback_uptake_r118_parallel_lifecycle as life


MODULE = 'gpu.orch_math_feedback_uptake_r118_parallel_final'
SOURCE = life.SOURCE
shared, require = life.shared, life.require


def original_functions():
    namespace = dict(vars(original), MODULE=MODULE, SOURCE=SOURCE, OUTPUT=life.FINAL_ROOT)
    for name, value in vars(original).items():
        if isinstance(value, FunctionType) and value.__module__ == original.__name__:
            namespace[name] = FunctionType(value.__code__, namespace, name, value.__defaults__, value.__closure__)
            namespace[name].__kwdefaults__ = value.__kwdefaults__
    namespace['legacy_validate'] = namespace['validate']
    namespace['validate'] = validate
    namespace['release'] = release
    return namespace


def prepare(service):
    service = Path(service)
    plan = life.plan_for(service)
    runtime = shared.read(service/'RUNTIME.json')
    life.released(service)
    previous = life.checked(plan['old_evaluation_plan'])
    output = Path(plan['final_root'])
    require(not output.exists(), 'new_FINAL_custody_namespace_no_retry')
    document = deepcopy(previous)
    document.update(root=str(output), source_root=str(SOURCE), source_manifest=plan['source_manifest'],
        tests=plan['tests_receipt'], previous_evaluation_plan=plan['old_evaluation_plan'],
        parallel_service=str(service), parallel_runtime=life.ref(service/'RUNTIME.json'),
        parallel_handoff=life.ref(service/'RELEASED.json'),
        custody_note='SAME_UNUSED_8_CALL_ALLOCATION_NOT_ADDITIONAL_QUOTA',
        parallel_authorization=runtime['authorization'])
    shared.write(output/'PLAN.json', document)
    shared.write(output/'DENOMINATORS.json', dict(planned_native=8, parent=0, optimizer_steps=0,
        experience_rows=0, extra_native_authorized=0, inherited_evaluation=plan['old_evaluation_plan']))
    validate(output)
    return life.ref(output/'PLAN.json')


def validate(root):
    plan = original_functions()['legacy_validate'](Path(root))
    service = Path(plan['parallel_service'])
    runtime = life.checked(plan['parallel_runtime'])
    require(plan['parallel_runtime'] == life.ref(service/'RUNTIME.json')
            and plan['parallel_handoff'] == runtime['release']
            and plan['parallel_authorization'] == runtime['authorization'], 'exact_NEW_math_FINAL_custody')
    require(plan['native_cap'] == 8 and plan['parent_cap'] == 0 and plan['optimizer_steps'] == 0
            and plan['attached_open_calls'] == 0, 'no_extra_FINAL_or_parent_calls')
    life.released(service, require_unchanged=False)
    return plan


def release(plan):
    service = Path(plan['parallel_service'])
    life.released(service, require_unchanged=False)
    launch = shared.read(service/'LAUNCH.json')
    guard = shared.read(service/'GUARD_STARTED.json')
    require(not life.alive(launch['identity']) and not life.alive(guard['identity']), 'NEW_native_guard_still_live')
    clean = shared.read(service/'CLEAN_RELEASE.json')
    terminal = shared.read(service/'GUARD_TERMINAL.json')
    require(clean['identity'] == launch['identity'] and clean['runtime'] == plan['parallel_runtime']
            and terminal['identity'] == launch['identity'] and terminal['native_alive'] is False,
            'actual_NEW_clean_boundary_and_authentic_guard_terminal')
    life.drain.verify_snapshot(dict(root=plan['original_root']), clean['boundary'])
    require(shared.sha(Path(plan['original_root'])/'COUNTERS.json') == clean['counter_sha256'], 'no_post_release_charges')
    require(not life.drain.live_readout_identities(Path(plan['original_root'])), 'no_live_old_or_NEW_readout')
    return dict(handoff=plan['parallel_handoff'], new_launch=life.ref(service/'LAUNCH.json'),
        clean_release=life.ref(service/'CLEAN_RELEASE.json'), authentic_guard_terminal=life.ref(service/'GUARD_TERMINAL.json'))


def schedule(root):
    root = Path(root)
    plan = validate(root)
    functions = original_functions()
    service = Path(plan['parallel_service'])
    child = expected = None
    status = 'NOT_RUN'
    with (root/'SCHEDULER.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        shared.write(root/'SCHEDULED.json', dict(identity=life.identity(os.getpid()), plan=life.ref(root/'PLAN.json'),
            runtime=plan['parallel_runtime'], status='ARMED_NOT_EVALUATED', observed_unix=time.time(), GPU_allocated=False))
        try:
            while time.time() < original.START:
                time.sleep(min(10, original.START-time.time()))
            while time.time() < plan['end_unix']-120:
                life.unused_old_FINAL(life.plan_for(service))
                if (service/'CLEAN_RELEASE.json').exists() and (service/'GUARD_TERMINAL.json').exists():
                    released = release(plan)
                    if Path(plan['selection_path']).exists():
                        chosen = functions['selection'](plan, time.time())
                        shared.write(root/'RELEASE.json', released)
                        shared.write(root/'SELECTED.json', dict(selection=chosen, reference=life.ref(plan['selection_path'])))
                        break
                time.sleep(2)
            else:
                shared.write(root/'NOT_RUN.json', dict(reason='NO_GENUINE_NEW_RELEASE_OR_CANONICAL_SELECTION',
                    native_calls=0, observed_unix=time.time()))
                return
            result = subprocess.run(['sudo','-n','env','CUDA_VISIBLE_DEVICES=','PYTHONDONTWRITEBYTECODE=1',
                'PYTHONPATH='+str(SOURCE),'python3','-B','-m',MODULE,'scan','--root',str(root)],
                capture_output=True, text=True, timeout=min(90, plan['end_unix']-time.time()), check=True)
            admission = json.loads(result.stdout)
            shared.write(root/'ADMISSION.json', admission)
            require(admission['clear'] and admission['scanner_euid'] == 0 and not admission['blocking_reasons'],
                    'strict_fresh_FINAL_full_proc_UUID_admission')
            release(plan)
            life.unused_old_FINAL(life.plan_for(service))
            original.window(plan, time.time())
            shared.write(root/'NATIVE_CLAIM.json', dict(attempt=1, retry=False, claimed_unix=time.time()))
            with (root/'NATIVE.log').open('x') as log:
                child = subprocess.Popen([life.previous.math.PYTHON,'-B','-m',MODULE,'native','--root',str(root)],
                    cwd=SOURCE, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True,
                    env=dict(os.environ, CUDA_VISIBLE_DEVICES=plan['uuid'], PYTHONPATH=str(SOURCE),
                        PYTHONDONTWRITEBYTECODE='1', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                        OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', TOKENIZERS_PARALLELISM='false'))
                for attempt in range(100):
                    expected = life.identity(child.pid)
                    if MODULE.encode() in (Path('/proc')/str(child.pid)/'cmdline').read_bytes().split(b'\0'):
                        break
                    time.sleep(.01)
                else:
                    raise ValueError('actual_FINAL_exec_not_observed')
                shared.write(root/'LAUNCH.json', dict(identity=expected, uuid=plan['uuid'], started_unix=time.time()))
                require(child.wait(timeout=max(.01, plan['end_unix']-20-time.time())) == 0
                        and (root/'COMPLETE.json').exists(), 'actual_FINAL_complete_no_retry')
                status = 'COMPLETE'
        except BaseException as error:
            status = 'FAILED'
            shared.write(root/'FAILED.json', dict(error=type(error).__name__+': '+str(error), observed_unix=time.time()))
            raise
        finally:
            if child is not None and child.poll() is None:
                life.terminate_owned(expected, force=True)
            shared.write(root/'TERMINAL.json', dict(status=status, **original.denominators(root),
                original_allocation_unchanged=True, observed_unix=time.time()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('prepare','schedule','native','scan'))
    parser.add_argument('--root', type=Path)
    parser.add_argument('--service', type=Path)
    args = parser.parse_args()
    if args.phase == 'prepare':
        print(json.dumps(prepare(args.service)))
    elif args.phase == 'schedule':
        schedule(args.root)
    elif args.phase == 'native':
        original_functions()['native'](args.root)
    else:
        plan = validate(args.root)
        original.window(plan, time.time())
        print(json.dumps(life.previous.math.scan(Path(plan['original_root']).parent, plan['physical'])))


if __name__ == '__main__':
    main()
