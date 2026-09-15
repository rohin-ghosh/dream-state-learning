"""Route-only bounded concurrent admission, preserving both failed startup eras."""

import argparse
import ast
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import time
from types import FunctionType, SimpleNamespace


STARTUP_END = 1789490100
FAILED_SESSIONS = frozenset(('e834ff7869f9309d70cf46f682adcc522f3120c8ac293ed7065708a6f50da94b',
    '2987f2cba47868934fd6d465f0001c94e7d754d3b7972bb56c328ed6f081e641'))


def require(value, reason):
    if not value:
        raise ValueError(reason)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(reference, name):
    require(sha(reference['path']) == reference['sha256'], 'exact_dependency_source')
    spec = importlib.util.spec_from_file_location(name, reference['path'])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def proof_binding(source, transient, record):
    tree = ast.parse(source)
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'bind_scan']
    require(len(nodes) == 1, 'one_exact_math_bind_scan')

    def preserved(scanner):
        envelope = transient.reconcile_scan(scanner)
        record('PIDFD_ENVELOPE', envelope)
        return envelope

    namespace = dict(os=os, resource=resource, deepcopy=deepcopy, hashlib=hashlib, json=json,
        require=require, transient=SimpleNamespace(reconcile_scan=preserved,
        TRANSIENT_REASONS=transient.TRANSIENT_REASONS))
    exec(compile(ast.Module(body=nodes, type_ignores=[]), '<bound_math_bind_scan>', 'exec'), namespace)
    return namespace['bind_scan']


def keep_observations(argv, report, observations):
    result = argv.reconcile(report, observations)
    result['all_identity_observations'] = {str(pid): deepcopy(samples) for pid, samples in observations.items()}
    result['rejected_observations_preserved'] = True
    return result


def validate_window(request):
    require(type(request['expires_unix']) is int and time.time() < request['expires_unix'] <= STARTUP_END,
            'fixed_1635_startup_no_sliding_window')
    require(request['failed_dispatch']['sha256'] in FAILED_SESSIONS, 'actual_previous_failed_session')
    preserved = {reference['sha256'] for reference in request['preserved_failures']}
    require(FAILED_SESSIONS <= preserved, 'both_failed_sessions_preserved')


def verify(request, lifecycle, previous=None):
    validate_window(request)
    for reference in request['dependencies'].values():
        require(sha(reference['path']) == reference['sha256'], 'immutable_admission_dependencies')
    previous = previous or load(request['dependencies']['previous'], 'route_previous_verify')
    return previous.verify(request, lifecycle)


def bind_window(request, expires_unix):
    require(type(expires_unix) is int and expires_unix == STARTUP_END, 'explicit_fixed_1635_window')
    updated = dict(request, expires_unix=expires_unix,
        startup_extension_authority='Main16:22 nonmaterial concurrent-admission repair; fixed16:35 startup only')
    validate_window(updated)
    return updated


def session_live(backend):
    digest = os.environ['R118_PARALLEL_SESSION_SHA256']
    require(digest not in FAILED_SESSIONS, 'neither_failed_session_reused')
    session, control = backend.fresh_session(os.environ['R118_PARALLEL_SESSION'], digest)
    require(not (control / 'FAILED.json').exists() and
            time.time() < min(STARTUP_END, session['startup_deadline_unix']), 'session_live_before_model_spawn')


def scan(request, lifecycle):
    require(os.geteuid() == 0 and os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'privileged_CPU_scan')
    validate_window(request)
    root = Path(request['root'])
    plan = lifecycle.verify_plan(root)
    from gpu import orch_r118_route_parallel_run as native
    from gpu import orch_rich_hot_a100_minor_scan as minor
    dependencies = request['dependencies']
    argv = load(dependencies['argv'], 'route_argv_dependency')
    transient = load(dependencies['transient'], 'route_exit_dependency')
    require(sha(dependencies['math']['path']) == dependencies['math']['sha256'], 'frozen_math_binding')
    minor.pinned.policy = SimpleNamespace(HOST_SHA=native.HOST_SHA, DEVICES=native.UUIDS,
        require=require, allocation=lambda index: require(index == plan['physical'], 'own_single_slot'))
    directory = Path(request['attempt_directory'])
    observations = []

    def record(kind, value):
        path = directory / (kind + '_' + str(time.time_ns()) + '.json')
        write(path, value)
        observations.append(dict(path=str(path), sha256=sha(path)))

    def reconciler(report, samples):
        result = keep_observations(argv, report, samples)
        record('ARGV_REPORT', result)
        return result

    original = argv.original.scan
    scanner = FunctionType(original.__code__, dict(original.__globals__, reconcile=reconciler),
                           'route_observed_scan', original.__defaults__)
    binding = proof_binding(Path(dependencies['math']['path']).read_text(), transient, record)
    try:
        report = binding(lambda: scanner(plan['physical'], root / 'SERVICE_IDENTITY.json'))
        report['admission_binding'] = 'ROUTE_CONCURRENT_SINGLE_SCAN_NO_RETRY_V1'
        report['preserved_observation_refs'] = observations
        path = directory / ('FULL_ADMISSION_' + str(time.time_ns()) + '.json')
        write(path, report)
        return dict(clear=report['clear'], blocking_reasons=report['blocking_reasons'],
                    scan_path=str(path), scan_sha256=sha(path), scanned_unix=time.time())
    except BaseException as error:
        write(directory / ('PROOF_REJECTED_' + str(time.time_ns()) + '.json'),
              dict(error=type(error).__name__ + ': ' + str(error), preserved_observation_refs=observations))
        raise


def launch(request, request_ref, lifecycle, backend, previous):
    session_live(backend)

    def run(command, **kwargs):
        if command[-3] == 'scan':
            prefix = command[:command.index('python3')]
            command = prefix + ['python3', '-B', str(Path(__file__).resolve()), 'scan',
                '--request', request_ref['path'], '--request-sha256', request_ref['sha256']]
        return subprocess.run(command, **kwargs)

    def popen(*args, **kwargs):
        session_live(backend)
        return subprocess.Popen(*args, **kwargs)

    namespace = dict(previous.launch.__globals__, __file__=str(Path(__file__).resolve()),
        verify=lambda request, lifecycle: verify(request, lifecycle, previous),
        subprocess=SimpleNamespace(run=run, Popen=popen, DEVNULL=subprocess.DEVNULL, STDOUT=subprocess.STDOUT))
    return FunctionType(previous.launch.__code__, namespace, 'route_concurrent_launch',
                        previous.launch.__defaults__)(request, lifecycle, backend)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', nargs='?', default='launch', choices=('launch', 'scan', 'bind', 'final'))
    parser.add_argument('--request')
    parser.add_argument('--request-sha256')
    parser.add_argument('--prepared')
    parser.add_argument('--prepared-sha256')
    parser.add_argument('--campaign')
    parser.add_argument('--campaign-sha256')
    parser.add_argument('--output')
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    if args.phase in ('bind', 'final'):
        require(args.prepared and args.output and sha(args.prepared) == args.prepared_sha256,
                'exact_prepared_owner')
        owner = json.loads(Path(args.prepared).read_text())
        request_ref = owner['pre_inference_recovery_request']
        require(sha(request_ref['path']) == request_ref['sha256'], 'exact_prepared_request')
        request = json.loads(Path(request_ref['path']).read_text())
    else:
        require(args.request and sha(args.request) == args.request_sha256, 'exact_new_request')
        request = json.loads(Path(args.request).read_text())
    require(request['source']['path'] == str(Path(__file__).resolve()) and
            request['source']['sha256'] == sha(__file__), 'exact_new_wrapper')
    sys.path.insert(0, request['frozen_source'])
    from gpu import orch_r118_route_parallel_lifecycle as lifecycle
    from gpu import orch_r118_parallel_consolidation as backend
    previous = load(request['dependencies']['previous'], 'route_previous_launcher')
    if args.phase in ('bind', 'final'):
        binder = load(request['dependencies']['binder'], 'route_frozen_binder')
        own_api = SimpleNamespace(verify=lambda doc, runtime: verify(doc, runtime, previous))
        if args.phase == 'bind':
            require(args.campaign and args.campaign_sha256, 'actual_new_Main_campaign')
            bound_stage = FunctionType(binder.stage.__code__, dict(binder.stage.__globals__, startup_window=bind_window),
                                       'route_concurrent_stage', binder.stage.__defaults__)
            result = bound_stage(dict(path=args.prepared, sha256=args.prepared_sha256),
                dict(path=args.campaign, sha256=args.campaign_sha256), args.output, own_api, lifecycle, backend, STARTUP_END)
        else:
            result = binder.finish(args.output, own_api, lifecycle)
    elif args.phase == 'scan':
        result = scan(request, lifecycle)
    elif args.verify_only:
        verify(request, lifecycle, previous)
        result = dict(status='CPU_VERIFIED_NOT_DISPATCHED')
    else:
        result = launch(request, dict(path=args.request, sha256=args.request_sha256), lifecycle, backend, previous)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
