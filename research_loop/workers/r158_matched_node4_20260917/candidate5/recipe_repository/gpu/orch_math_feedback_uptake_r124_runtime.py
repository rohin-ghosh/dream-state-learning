"""A2 interpreter repair; preserve failed probes and resume saved learner."""

import argparse
import fcntl
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from types import FunctionType

from gpu import orch_math_feedback_uptake_r124_readout as run


PYTHON = '/localhome/local-rohing/v2/venv/bin/python'
SERVICE = run.ROOT / 'A2' / 'runtime_recovery'


def failed_before_input(root, plan):
    run.require(run.read(root/'COUNTERS.json') == plan['contract']['inherited_counters'], 'no_new_charges_or_updates')
    for pattern in ('reservations/*.json', 'cycle*', 'LOADED.json', 'OPTIMIZER_RESTORED.json'):
        run.require(not any(root.glob(pattern)), 'no_loaded_learner_or_inputs:' + pattern)
    evidence = {}
    for role in ('before', 'after'):
        output = root/'paired_DEV'/role
        result = run.read(output/'PROCESS_RESULT.json')
        run.require(result['status'] == 'FAILED_NO_RETRY' and result['returncode'] == 1, 'preserved_failed_probe')
        run.require((output/'process.log').read_text().rstrip().endswith("ModuleNotFoundError: No module named 'tokenizers'"), 'exact_environment_failure')
        for pattern in ('LOADED.json', 'BATCH.request.json', 'CALL*', 'COMPLETE.json'):
            run.require(not any(output.glob(pattern)), 'no_probe_model_or_input:' + pattern)
        evidence[role] = {name:run.ref(output/name) for name in ('PROCESS_RESULT.json','process.log','LAUNCH.json','BINDING.json')}
    return evidence


def require_absent(identity):
    try:
        descriptor = os.pidfd_open(identity['pid'])
    except ProcessLookupError:
        run.require(not Path(f'/proc/{identity["pid"]}').exists(), 'absent_failed_actor')
    else:
        os.close(descriptor)
        raise ValueError('live_or_reused_actor_no_takeover')


def preflight():
    run.require(sys.executable == PYTHON, 'exact_verified_model_interpreter')
    versions = {name:str(getattr(importlib.import_module(name), '__version__', 'unknown'))
        for name in ('tokenizers','torch','transformers','peft')}
    return dict(executable=sys.executable, prefix=sys.prefix, packages=versions)


def guard():
    run.configure()
    root = run.ROOT/'A2'
    plan = run.validate(root)
    environment_receipt = preflight()
    evidence = failed_before_input(root, plan)
    require_absent(run.read(root/'LAUNCH.json')['identity'])
    require_absent(run.read(root/'admission_attempt2/GUARD_STARTED.json')['identity'])
    run.require(run.read(root/'GUARD_TERMINAL.json')['returncode'] == 1, 'actual_failed_guard_exit')
    tests = Path(__file__).parents[1]/'CPU_TESTS.json'
    checked = run.read(tests)
    run.require(checked['passed'] and run.sha(__file__) == checked['source_files']['gpu/'+Path(__file__).name], 'tested_frozen_runtime')
    SERVICE.mkdir(exist_ok=False)
    run.write(SERVICE/'PREMODEL_RELEASE.json', dict(probe_failures=evidence,
        original_guard_terminal=run.ref(root/'GUARD_TERMINAL.json'), original_launch=run.ref(root/'LAUNCH.json'),
        counters=run.read(root/'COUNTERS.json'), environment=environment_receipt,
        tests=run.ref(tests), source=run.ref(__file__), policy='NO_PROBE_RETRY_RESUME_NEXT_GENUINE_CYCLE'))
    run.write(SERVICE/'GUARD_STARTED.json', dict(identity=run.math.common.process_identity(Path('/proc')/str(os.getpid()))))
    command = ['sudo','-n','env','CUDA_VISIBLE_DEVICES=','PYTHONPATH='+str(run.SOURCE),
        PYTHON,'-B','-m',run.MODULE,'scan','--root',str(root)]
    process = subprocess.run(command,text=True,capture_output=True,timeout=180)
    run.require(process.returncode == 0,'strict_scan_process:'+process.stderr[-1000:])
    report = json.loads(process.stdout)
    run.write(SERVICE/'ADMISSION.json',report)
    run.require(report['clear'] and report['scanner_euid'] == 0 and report['gpu']['uuid'] == plan['uuid'], 'strict_full_scan_no_waiver')
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES=plan['uuid'], PYTHONPATH=str(run.SOURCE),
        HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
    with (SERVICE/'native.log').open('x') as log:
        actor = subprocess.Popen([PYTHON,'-B',str(Path(__file__).resolve()),'resident'],env=environment,
            stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        identity = run.math.common.process_identity(Path('/proc')/str(actor.pid))
        run.write(SERVICE/'LAUNCH.json',dict(identity=identity,started_unix=time.time(),plan=run.ref(root/'PLAN.json')))
        try:
            actor.wait(timeout=max(.1,plan['bounds']['hard_end_unix']-time.time()))
        except subprocess.TimeoutExpired:
            run.math.common.stop_owned(actor,identity)
        run.write(SERVICE/'GUARD_TERMINAL.json',dict(identity=identity,returncode=actor.returncode,finished_unix=time.time()))


def successor_write(root, path, data):
    destination = SERVICE / 'MOUNTED_BEFORE.json' if Path(path) == root/'MOUNTED_BEFORE.json' else path
    run.write(destination,data)


def resident():
    run.configure()
    preflight()
    def skip_failed(root, plan):
        evidence = failed_before_input(root,plan)
        run.write(SERVICE/'PROBES_NOT_RETRIED.json',dict(original_failures=evidence,
            before='FAILED_PREMODEL_NOT_RETRIED',after='FAILED_PREMODEL_NOT_RETRIED',
            next_cycle=plan['contract']['next_cycle'],completed_unix=time.time()))
    restored = FunctionType(run.resident.__code__,dict(run.resident.__globals__,paired_probe=skip_failed,
        write=lambda path,data:successor_write(run.ROOT/'A2',path,data)),
        'saved_learner_after_failed_probes',run.resident.__defaults__)
    restored(run.ROOT/'A2')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase',choices=('guard','resident','preflight'))
    phase = parser.parse_args().phase
    if phase == 'preflight':
        print(json.dumps(preflight()))
    else:
        globals()[phase]()
