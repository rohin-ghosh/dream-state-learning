"""Lease-bound route owner preparation and original strict concurrent admission."""

import argparse
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import sys
import subprocess
import time
from types import FunctionType, SimpleNamespace

from gpu import orch_r120_route_clock as lease


require, ref, checked = lease.require, lease.reference, lease.checked


def write(path, value):
    path = Path(path)
    with path.open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def load(pointer, name):
    require(ref(pointer['path']) == pointer, 'frozen_dependency')
    spec = importlib.util.spec_from_file_location(name, pointer['path'])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def runtime(request):
    require(ref(__file__) == request['source'], 'exact_continuation_launcher')
    os.environ.update(ORCH_R119_LEASE_CLOCK=request['lease_policy']['path'],
                      ORCH_R119_LEASE_CLOCK_SHA256=request['lease_policy']['sha256'])
    limits = lease.current()
    from gpu import orch_r120_route_shared_lifecycle as lifecycle
    from gpu import orch_r118_parallel_consolidation as backend
    admission = load(request['dependencies']['concurrent'], 'route_continuation_admission')
    admission.STARTUP_END = int(limits['train_end_unix']) - 180
    admission.__file__ = str(Path(__file__).resolve())
    previous = load(request['dependencies']['previous'], 'route_continuation_previous')
    return lifecycle, backend, admission, previous


def privileged_command(command, request_pointer, policy):
    command = list(command)
    if command[:3] != ['sudo', '-n', 'env']:
        return command
    marker = command.index('python3')
    prefix = command[:marker] + ['ORCH_R119_LEASE_CLOCK=' + policy['path'],
        'ORCH_R119_LEASE_CLOCK_SHA256=' + policy['sha256']]
    if command[-3] == 'scan':
        return prefix + ['python3', '-B', str(Path(__file__).resolve()), 'scan',
            '--request', request_pointer['path'], '--request-sha256', request_pointer['sha256']]
    return prefix + command[marker:]


def launch(request, pointer, lifecycle, backend, admission, previous):
    admission.session_live(backend)

    def run(command, **kwargs):
        return subprocess.run(privileged_command(command, pointer, request['lease_policy']), **kwargs)

    def popen(*args, **kwargs):
        admission.session_live(backend)
        return subprocess.Popen(*args, **kwargs)

    namespace = dict(previous.launch.__globals__, __file__=str(Path(__file__).resolve()),
        verify=lambda document, module: admission.verify(document, module, previous),
        subprocess=SimpleNamespace(run=run, Popen=popen, DEVNULL=subprocess.DEVNULL,
                                   STDOUT=subprocess.STDOUT))
    return FunctionType(previous.launch.__code__, namespace, 'lease_route_launch',
                        previous.launch.__defaults__)(request, lifecycle, backend)


def prepare(previous_owner, source_files, final_custody, output, expires):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_preparation_only')
    limits = lease.current()
    require(time.time() < expires <= limits['train_end_unix'] - 180, 'bounded_startup')
    owner = checked(previous_owner)
    prior_request = checked(owner['pre_inference_recovery_request'])
    root = Path(prior_request['root'])
    old_plan = checked(prior_request['plan'])
    for name, digest in source_files.items():
        require(ref(name)['sha256'] == digest, 'source_closure')
    from gpu import orch_r120_route_shared_lifecycle as lifecycle
    from gpu import orch_r120_route_shared_client as client
    previous = load(prior_request['dependencies']['previous'], 'route_prepare_previous')
    previous.no_inference(root)
    require(ref(root / 'RESERVATIONS.jsonl')['sha256'] == prior_request['reservations_sha256'],
            'original_native_parent_charges')
    snapshot = lifecycle.boundary.released(root, old_plan['route_boundary_release'])
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    plan = deepcopy(old_plan)
    original = json.loads((root / 'PLAN.json').read_bytes())
    plan['bounds'] = lease.updated_bounds(original['bounds'], limits)
    branch = plan['shared_learner']['branch']
    plan['parent_wait_seconds'] = 600 if branch == 'F1' else 120
    plan['parallel_source'] = str(Path(__file__).resolve().parents[1])
    plan['source_files'] = source_files
    policy = dict(path=os.environ['ORCH_R119_LEASE_CLOCK'],
                  sha256=os.environ['ORCH_R119_LEASE_CLOCK_SHA256'])
    plan['lease_continuation'] = dict(policy=policy, completed_final=final_custody,
        previous_plan=prior_request['plan'], era='R120_LEASE_CONTINUATION',
        source=ref(__file__), no_final_replay=True, no_optimizer_or_counter_reset=True,
        parent_transport='F1 high effort/600seconds; A1 unchanged120; not parent-model-only comparison')
    plan['parallel_control'].update(train_end_unix=limits['train_end_unix'],
        activation_wait_end_unix=limits['train_end_unix'],
        backend_source=ref(Path(__file__).with_name('orch_r118_parallel_consolidation.py')))
    plan['parallel_control'].pop('campaign', None)
    lease.same_life(plan, original)
    lease.preserve_final(plan)
    write(output / 'PLAN_PREPARED.json', plan)
    request = deepcopy(prior_request)
    request.update(source=ref(__file__), frozen_source=plan['parallel_source'],
        lease_policy=policy, expires_unix=expires,
        attempt_directory=str(root / ('R118_STARTUP_RECOVERY_R120_' + output.parent.name)),
        prospective_plan=ref(output / 'PLAN_PREPARED.json'),
        authority='Main report-cut-not-stop lease continuation; no changes to shared state or call caps',
        previous_request=owner['pre_inference_recovery_request'])
    request['dependencies']['concurrent'] = prior_request['source']
    write(output / 'REQUEST_PREPARED.json', request)
    envelope = deepcopy(checked(owner['handoff']))
    envelope['bounds'] = client.original_bounds(root, plan)
    envelope['original_bounds'] = original['bounds']
    envelope['lease_policy'] = policy
    envelope['prior_handoff'] = owner['handoff']
    require(envelope['next_cycle'] == snapshot['next_cycle'], 'same_next_cycle')
    write(output / 'HANDOFF.json', envelope)
    owner.update(handoff=ref(output / 'HANDOFF.json'), inherited_bounds=envelope['bounds'],
        source_files=source_files, cwd=plan['parallel_source'],
        runtime_staged=False, requires_new_Main_campaign_binding=True,
        previous_owner=previous_owner, lease_policy=policy,
        pre_inference_recovery_request=ref(output / 'REQUEST_PREPARED.json'))
    owner['env'].update(CUDA_VISIBLE_DEVICES='', PYTHONPATH=plan['parallel_source'],
        ORCH_R119_LEASE_CLOCK=policy['path'], ORCH_R119_LEASE_CLOCK_SHA256=policy['sha256'])
    owner['command'] = [owner['command'][0], '-B', str(Path(__file__).resolve()),
        '--request', str(output / 'REQUEST_PREPARED.json'), '--request-sha256', ref(output / 'REQUEST_PREPARED.json')['sha256']]
    write(output / 'OWNER_PREPARED.json', owner)
    return dict(branch=branch, owner=ref(output / 'OWNER_PREPARED.json'),
                plan=ref(output / 'PLAN_PREPARED.json'), no_GPU_dispatch=True)


def stage(prepared, campaign_pointer, output):
    owner = checked(prepared)
    request = checked(owner['pre_inference_recovery_request'])
    lifecycle, backend, admission, previous = runtime(request)
    root = Path(request['root'])
    previous.no_inference(root)
    require(ref(root / lifecycle.PLAN) == request['plan'], 'previous_PLAN_unchanged')
    require(ref(root / 'RESERVATIONS.jsonl')['sha256'] == request['reservations_sha256'], 'no_new_calls')
    admission.validate_window(request)
    plan = checked(request['prospective_plan'])
    campaign, unused = backend.campaign_document(campaign_pointer['path'], campaign_pointer['sha256'])
    require(campaign['root'] == plan['shared_learner']['root'] and campaign['first_generation'] == 1,
            'actual_same_common_gen1_campaign')
    require(campaign['deadline_unix'] <= plan['parallel_control']['train_end_unix'], 'same_lease_bounds')
    require(all(campaign['source_files'].get(path) == digest for path, digest in owner['source_files'].items()),
            'full_campaign_source_closure')
    plan['parallel_control'].update(campaign=campaign_pointer,
        activation_directory=campaign['activation_directory'])
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    old_bytes = (root / lifecycle.PLAN).read_bytes()
    (output / 'OLD_PLAN.json').write_bytes(old_bytes)
    (output / 'OLD_BROKER_BINDING.json').write_bytes((root / 'R118_PARALLEL_BROKER_BINDING.json').read_bytes())
    write(output / 'STAGE_INTENT.json', dict(prepared=prepared, campaign=campaign_pointer,
        prior_plan=ref(output / 'OLD_PLAN.json'), no_GPU_dispatch=True))
    temporary = output / 'PLAN_NEW.json'
    write(temporary, plan)
    require((root / lifecycle.PLAN).read_bytes() == old_bytes, 'concurrent_PLAN_change_rejected')
    os.replace(temporary, root / lifecycle.PLAN)
    request['plan'] = ref(root / lifecycle.PLAN)
    write(output / 'REQUEST_FINAL.json', request)
    result = dict(prepared=prepared, request=ref(output / 'REQUEST_FINAL.json'),
        plan=request['plan'], status='PLAN_BOUND_BROKER_REFRESH_REQUIRED')
    write(output / 'STAGED.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', nargs='?', default='launch', choices=('launch', 'scan', 'stage', 'final'))
    parser.add_argument('--request')
    parser.add_argument('--request-sha256')
    parser.add_argument('--prepared')
    parser.add_argument('--prepared-sha256')
    parser.add_argument('--campaign')
    parser.add_argument('--campaign-sha256')
    parser.add_argument('--output')
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    if args.phase == 'stage':
        owner_pointer = dict(path=args.prepared, sha256=args.prepared_sha256)
        owner = checked(owner_pointer)
        runtime(checked(owner['pre_inference_recovery_request']))
        result = stage(owner_pointer, dict(path=args.campaign, sha256=args.campaign_sha256), args.output)
    elif args.phase == 'final':
        staged = json.loads((Path(args.output) / 'STAGED.json').read_bytes())
        request = checked(staged['request'])
        lifecycle, backend, admission, previous = runtime(request)
        admission.verify(request, lifecycle, previous)
        owner = checked(staged['prepared'])
        owner['pre_inference_recovery_request'] = staged['request']
        owner['command'] = [owner['command'][0], '-B', str(Path(__file__).resolve()),
            '--request', staged['request']['path'], '--request-sha256', staged['request']['sha256']]
        owner.update(runtime_staged=True, requires_new_Main_campaign_binding=False)
        write(Path(args.output) / 'OWNER_FINAL.json', owner)
        result = dict(owner=ref(Path(args.output) / 'OWNER_FINAL.json'), status='CPU_VERIFIED_NOT_DISPATCHED')
    else:
        request_pointer = dict(path=args.request, sha256=args.request_sha256)
        request = checked(request_pointer)
        lifecycle, backend, admission, previous = runtime(request)
        if args.phase == 'scan':
            result = admission.scan(request, lifecycle)
        elif args.verify_only:
            admission.verify(request, lifecycle, previous)
            result = dict(status='CPU_VERIFIED_NOT_DISPATCHED')
        else:
            result = launch(request, request_pointer, lifecycle, backend, admission, previous)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
