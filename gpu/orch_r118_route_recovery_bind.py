"""CPU-only campaign metadata binding and final recovery-owner export."""

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def reference(path):
    path = Path(path)
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def read_bound(document):
    require(reference(document['path']) == document, 'exact_reference')
    return json.loads(Path(document['path']).read_text())


def write_new(path, document):
    with Path(path).open('x') as stream:
        json.dump(document, stream, sort_keys=True, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def campaign_plan(plan, campaign, campaign_ref, owner):
    require(campaign['root'] == plan['shared_learner']['root'], 'same_common_root')
    require(campaign['first_generation'] == 1, 'same_committed_generation')
    require(campaign['deadline_unix'] == plan['parallel_control']['train_end_unix'] == 1789491300,
            'original_1655_TRAIN_end')
    require(all(campaign['source_files'].get(path) == digest
                for path, digest in owner['source_files'].items()), 'new_campaign_full_owner_closure')
    changed = deepcopy(plan)
    changed['parallel_control']['campaign'] = campaign_ref
    changed['parallel_control']['activation_directory'] = campaign['activation_directory']
    return changed


def startup_window(request, expires_unix):
    require(type(expires_unix) is int and request['expires_unix'] <= expires_unix <= 1789489500,
            'Main_startup_only_extension_through_1625')
    require(time.time() < expires_unix, 'startup_window_not_expired')
    return dict(request, expires_unix=expires_unix,
                startup_extension_authority='Main explicit CPU failed-startup/new-startup window through16:25 UTC; no TRAIN/caps/FINAL extension')


def stage(prepared, campaign_ref, output, recovery, lifecycle, backend, expires_unix):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_only')
    owner = read_bound(prepared)
    request = read_bound(owner['pre_inference_recovery_request'])
    previous_expiry = request['expires_unix']
    request = startup_window(request, expires_unix)
    root, old_plan = recovery.verify(request, lifecycle)
    campaign, unused = backend.campaign_document(campaign_ref['path'], campaign_ref['sha256'])
    require(campaign_ref != old_plan['parallel_control']['campaign'], 'new_campaign_not_failed_era')
    plan = campaign_plan(old_plan, campaign, campaign_ref, owner)
    output = Path(output)
    require(output.is_absolute() and not output.exists(), 'fresh_stage_directory')
    old_bytes = (root / lifecycle.PLAN).read_bytes()
    output.mkdir(parents=True)
    with (output / 'OLD_PLAN.json').open('xb') as stream:
        stream.write(old_bytes)
    broker = root / 'R118_PARALLEL_BROKER_BINDING.json'
    with (output / 'OLD_BROKER_BINDING.json').open('xb') as stream:
        stream.write(broker.read_bytes())
    write_new(output / 'STAGE_INTENT.json', dict(prepared=prepared, campaign=campaign_ref,
        old_plan=reference(output / 'OLD_PLAN.json'), broker_refresh_required=True,
        previous_request=owner['pre_inference_recovery_request'], previous_expiry_unix=previous_expiry,
        new_startup_expiry_unix=request['expires_unix'], startup_extension_authority=request['startup_extension_authority'],
        no_GPU_dispatch=True, created_unix=time.time()))
    require((root / lifecycle.PLAN).read_bytes() == old_bytes, 'PLAN_did_not_change_concurrently')
    temporary = root / ('R118_PLAN_STAGE_' + str(os.getpid()) + '.partial')
    write_new(temporary, plan)
    require((root / lifecycle.PLAN).read_bytes() == old_bytes, 'PLAN_did_not_change_before_replace')
    os.replace(temporary, root / lifecycle.PLAN)
    request = dict(request, plan=reference(root / lifecycle.PLAN))
    write_new(output / 'REQUEST_FINAL.json', request)
    result = dict(status='PLAN_BOUND_BROKER_REFRESH_REQUIRED', root=str(root),
        plan=reference(root / lifecycle.PLAN), request=reference(output / 'REQUEST_FINAL.json'),
        prepared=prepared, campaign=campaign_ref, original_expiry_unix=previous_expiry,
        new_startup_expiry_unix=request['expires_unix'],
        no_new_calls=True, no_GPU_dispatch=True)
    write_new(output / 'STAGED.json', result)
    return result


def finish(output, recovery, lifecycle):
    output = Path(output)
    staged = json.loads((output / 'STAGED.json').read_text())
    request = read_bound(staged['request'])
    root, unused = recovery.verify(request, lifecycle)
    owner = read_bound(staged['prepared'])
    source = request['source']['path']
    owner['command'] = [owner['command'][0], '-B', source, '--request', staged['request']['path'],
                        '--request-sha256', staged['request']['sha256']]
    owner['env']['CUDA_VISIBLE_DEVICES'] = ''
    owner['pre_inference_recovery_request'] = staged['request']
    owner['runtime_staged'] = True
    owner['requires_new_Main_campaign_binding'] = False
    write_new(output / 'FRESH_OWNER_FINAL.json', owner)
    result = dict(status='CPU_PREFLIGHT_PASS_NOT_DISPATCHED', owner=reference(output / 'FRESH_OWNER_FINAL.json'),
        plan=staged['plan'], broker=reference(root / 'R118_PARALLEL_BROKER_BINDING.json'),
        expires_unix=request['expires_unix'], no_GPU_dispatch=True)
    write_new(output / 'FINAL_EXPORT.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('stage', 'final'))
    parser.add_argument('--prepared', required=True)
    parser.add_argument('--prepared-sha256', required=True)
    parser.add_argument('--campaign')
    parser.add_argument('--campaign-sha256')
    parser.add_argument('--output', required=True)
    parser.add_argument('--startup-expires-unix', type=int)
    arguments = parser.parse_args()
    prepared = dict(path=arguments.prepared, sha256=arguments.prepared_sha256)
    owner = read_bound(prepared)
    request = read_bound(owner['pre_inference_recovery_request'])
    read_bound(request['plan']) if arguments.phase == 'stage' else None
    require(reference(request['source']['path']) == request['source'], 'frozen_recovery_source')
    sys.path.insert(0, request['frozen_source'])
    from gpu import orch_r118_route_parallel_lifecycle as lifecycle
    from gpu import orch_r118_parallel_consolidation as backend
    spec = importlib.util.spec_from_file_location('route_recovery_frozen', request['source']['path'])
    recovery = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(recovery)
    if arguments.phase == 'stage':
        require(arguments.campaign and arguments.campaign_sha256, 'actual_new_campaign_reference')
        require(arguments.startup_expires_unix is not None, 'explicit_startup_window_required')
        result = stage(prepared, dict(path=arguments.campaign, sha256=arguments.campaign_sha256),
                       arguments.output, recovery, lifecycle, backend, arguments.startup_expires_unix)
    else:
        result = finish(arguments.output, recovery, lifecycle)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
