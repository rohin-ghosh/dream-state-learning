"""Fresh CODE guard-only wrapper reusing exact Math admission proofs."""

import argparse
import ast
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import time
from types import FunctionType, SimpleNamespace

from gpu import orch_r118_code_parallel_loop as core
from gpu import orch_r118_code_parallel_admission_record as recording
from gpu import orch_admission_transient_exit as transient
from gpu import orch_math_feedback_uptake_r118_argv_admission as argv_admission


io, handoff, require = core.io, core.handoff, core.require
FAILED_SESSIONS = frozenset(('e834ff7869f9309d70cf46f682adcc522f3120c8ac293ed7065708a6f50da94b',
    '2987f2cba47868934fd6d465f0001c94e7d754d3b7972bb56c328ed6f081e641'))


def bind_function(path, expected):
    require(io.sha(path) == expected, 'exact_existing_Math_binding_source')
    tree = ast.parse(Path(path).read_text())
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'bind_scan']
    require(len(functions) == 1, 'one_existing_Math_binding_function')
    namespace = dict(os=os, resource=resource, transient=transient, require=require,
        deepcopy=deepcopy, hashlib=hashlib, json=json)
    exec(compile(ast.Module(body=functions, type_ignores=[]), str(path), 'exec'), namespace)
    return namespace['bind_scan']


def verify_auxiliary():
    root = Path(__file__).resolve().parents[1]
    manifest = io.read(root / 'AUXILIARY_SOURCE_FILES.json')
    require(all(io.sha(path) == expected for path, expected in manifest.items()), 'frozen_auxiliary_dependencies')
    return root, manifest


def scan(service):
    require(os.geteuid() == 0, 'privileged_same_process_proof_scan')
    auxiliary, manifest = verify_auxiliary()
    runtime = io.read(Path(service) / 'RUNTIME.json')
    root = Path(runtime['root'])
    plan = io.read(root / 'PLAN.json')
    handoff.previous.original.bind(plan['physical'])
    binding_path = auxiliary / 'vendor/math_preinfer.py'
    binding = bind_function(binding_path, manifest[str(binding_path)])
    report = binding(lambda: argv_admission.scan(plan['physical'], root / 'SERVICE_IDENTITY.json'))
    report['CODE_proof_source'] = handoff.ref(binding_path)
    report['CODE_scan_root'] = str(root)
    return report


def guard(service):
    service = Path(service)
    auxiliary, manifest = verify_auxiliary()
    session_path = Path(os.environ['R118_PARALLEL_SESSION'])
    expected = os.environ['R118_PARALLEL_SESSION_SHA256']
    require(expected not in FAILED_SESSIONS and io.sha(session_path) == expected, 'new_Main_session_only')
    session, control = core.consolidation.fresh_session(session_path, expected)
    require(not (control / 'FAILED.json').exists() and time.time() < session['startup_deadline_unix'],
        'session_open_before_scan')
    runtime, released, plan = core.validate_runtime(service)
    identity = handoff.identities.identity(os.getpid())
    io.write(service / 'GUARD_IDENTITY.json', dict(identity=identity,
        session=handoff.ref(session_path), source=handoff.ref(__file__), observed_unix=time.time()))

    def recorded_scan(root):
        require(Path(root) == Path(runtime['root']), 'original_CODE_scan_root')
        bootstrap = 'import sys,runpy; sys.path.insert(0,' + repr(str(core.SOURCE_ROOT)) + '); import gpu; gpu.__path__.insert(0,' + repr(str(auxiliary / 'gpu')) + '); sys.argv=["code-proof-scan","scan","--service",' + repr(str(service)) + ']; runpy.run_module("gpu.orch_r118_code_parallel_proof_guard",run_name="__main__")'
        def privileged_scan(unused):
            result = subprocess.run(['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=',
                'PYTHONDONTWRITEBYTECODE=1', 'python3', '-B', '-c', bootstrap],
                capture_output=True, text=True, timeout=120, check=True)
            return json.loads(result.stdout)
        return recording.acquire(service, root, plan, deadline=session['startup_deadline_unix'],
            scan=privileged_scan, attempts=1)

    previous = SimpleNamespace(**dict(vars(handoff.previous), scan=recorded_scan))
    bound_handoff = SimpleNamespace(**dict(vars(handoff), previous=previous))
    namespace = dict(core.guard.__globals__, handoff=bound_handoff)
    try:
        return FunctionType(core.guard.__code__, namespace, 'guard', core.guard.__defaults__)(service)
    except BaseException as error:
        if not (service / 'LAUNCH.json').exists() and not (service / 'GUARD_TERMINAL.json').exists():
            io.write(service / 'GUARD_TERMINAL.json', dict(schema='R118_CODE_PRENATIVE_GUARD_FAILURE_V1',
                guardian=identity, native_started=False, native_alive=False, returncode=1,
                error_type=type(error).__name__, observed_unix=time.time(), no_retry=True))
        raise


def rebind_final(service):
    from gpu import orch_r118_code_parallel_stage as stage
    from gpu import orch_r118_code_parallel_recovery_final as timer
    runtime = io.read(Path(service) / 'RUNTIME.json')
    proof = handoff.checked(handoff.checked(runtime['handoff'])['failed_startup_recovery'])
    require(proof['new_calls'] == 0 and proof['optimizer_steps'] == 0
        and proof['root'] == runtime['root'], 'exact_preinference_recovery')
    require(proof['predecessors'] and all(not handoff.alive(identity) for identity in proof['predecessors']),
        'all_prior_guard_native_identities_exited')
    return stage.rebind(service, cancel=timer.cancel_timer)


def arm_final(service):
    from gpu import orch_r118_code_parallel_stage as stage
    verify_auxiliary()
    FunctionType(stage.serve.__code__, dict(vars(stage), rebind=rebind_final), 'serve')(service)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('scan', 'guard', 'arm-final'))
    parser.add_argument('--service', required=True, type=Path)
    args = parser.parse_args()
    if args.phase == 'scan':
        print(json.dumps(scan(args.service), sort_keys=True))
    elif args.phase == 'arm-final':
        arm_final(args.service)
    else:
        guard(args.service)
