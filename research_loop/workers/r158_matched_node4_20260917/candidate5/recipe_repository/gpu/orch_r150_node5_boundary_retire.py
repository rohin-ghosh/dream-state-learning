"""CPU-only retirement planning; never signal, publish, scan, or launch."""

import argparse
from copy import deepcopy
import json
import math
from pathlib import PurePosixPath
import re
import sys
import time


HOST = '[REDACTED_HOST]'
BOOT_ID = '2c05ffec-1b4c-472f-9688-2a37543a6f4a'
BASE = '/localhome/local-rohing'
PHYSICALS = (0, 3, 4)
PROTECTED = (1, 2, 5, 6, 7)
HARD_END = 1789596240
LEASE_END = 1789617840
F4_TRAIN_END = 1789596120
FRESH_SECONDS = 120
SCHEMA = 'R150_NODE5_RETIREMENT_METADATA_V1'
RUNTIME_BLOCKERS = [
    'current_owner_route_retirement_interlock_not_implemented',
    'F4_current_runtime_RNG_capture_not_implemented',
    'F4_timer_disposition_not_bound',
    'known_good_confinement_capsule_maps_only_2_6_not_0_3_4',
    'new_child_existing_lease_scope_requires_MAIN_verification',
    'runtime_must_revalidate_bytes_identities_and_locked_boundaries',
    'original_privileged_scan_required_after_actual_exit',
]


def reference(path, sha256):
    return dict(path=path, sha256=sha256)


def route(physical, label, pid, ticks, command_sha, plan_sha):
    root = f'{BASE}/orch_r111_f1_v4_20260915_node5_{physical}_attempt1'
    return dict(label=label, root=root, kind='route', owner=dict(
        pid=pid, start_ticks=str(ticks), uid=2524, boot_id=BOOT_ID,
        cmdline_sha256=command_sha), lease=reference(
            root+'/R121_INDEPENDENT_PLAN_V2.json', plan_sha))


TARGETS = {
    0: route(0, 'F1', 2664733, 6398743,
        '5b7590a41ba36c1a00f930a81871265fd526d1ec4787a4cfbd0a5dd1fd124efc',
        '9a5537780508ac451125d9bc4afde85a45a021fb762498efdf05c070513b884e'),
    4: route(4, 'A1', 3356568, 3136146,
        '683b67c651a9be289bc289eecf959c140e8bc2ca55bb57f09c606e8dbe44d862',
        '14533604ee37024e9ed60c641d39d04eb5cf2156412e3b7409dbcf353031e7ec'),
    3: dict(label='F4', kind='grid', root=BASE+'/orch_r115_grid_pair_20260915/F4',
        owner=dict(pid=4148447, start_ticks='7411484', uid=2524, boot_id=BOOT_ID,
            cmdline_sha256='2c1debfc9db7c15794b33d2cc5b504127904270ac18133831d36016f68798766'),
        lease=reference(BASE+'/orch_r115_grid_pair_20260915/F4/independent_r119_v1/LEASE_BUDGET.json',
            'afd47a446543700ec1e838fd2584ba05080c9f537a5a70b0ee9483ec3b5cb41c')),
}
UUIDS = {
    0: 'GPU-f237c5b5-c2a3-b377-92ee-46cf2658db9a',
    3: 'GPU-d23c9369-39cf-51fd-833e-13292f173006',
    4: 'GPU-94c9a79c-8b13-5679-ad35-8dda3fe5c94d',
}
COMPONENTS = {
    'route': ('checkpoint', 'adapter', 'optimizer_rng', 'carry', 'history', 'charges', 'parent_context'),
    'grid': ('checkpoint', 'adapter', 'runtime_rng', 'carry', 'history', 'charges', 'parent_claims'),
}


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def valid_ref(value):
    if not isinstance(value, dict) or set(value) != {'path', 'sha256'}:
        return False
    path, checksum = value['path'], value['sha256']
    return (isinstance(path, str) and path.startswith(BASE+'/')
        and '..' not in PurePosixPath(path).parts
        and not any(character in path for character in ('\n', '\r', '\x00'))
        and isinstance(checksum, str) and re.fullmatch('[a-f0-9]{64}', checksum) is not None)


def exact_scope(value):
    return (isinstance(value, list) and all(type(item) is int for item in value)
        and sorted(value) == list(PHYSICALS))


def fresh(value, now):
    return finite(value) and 0 <= now-value <= FRESH_SECONDS


def contract():
    lanes = []
    for physical in PHYSICALS:
        target = TARGETS[physical]
        lanes.append(dict(physical=physical, root=target['root'], uuid=UUIDS[physical],
            owner=deepcopy(target['owner']), lease=deepcopy(target['lease']),
            observed_unix=None, children_reaped=False, active_work_count=None,
            future_charges=None, boundary=dict(cycle=None, sleep=None,
                complete=False, preserved={key: None for key in COMPONENTS[target['kind']]},
                readouts={})))
    return dict(schema=SCHEMA, host=HOST, scope=list(PHYSICALS), observed_unix=None,
        child=dict(ready=False, plan=None, source_manifest=None, cpu_gate=None,
            cpu_passed=False, lease_scope_verified=False, physicals=list(PHYSICALS),
            hard_end_unix=HARD_END, lease_end_unix=LEASE_END,
            expected_duration_seconds=None),
        main_go=None, lanes=lanes)


def assess(document, now=None):
    now = time.time() if now is None else now
    if not finite(now):
        raise ValueError('finite_current_time_required')
    if not isinstance(document, dict):
        raise ValueError('metadata_object_required')
    blockers = []

    def check(condition, reason):
        if not condition:
            blockers.append(reason)

    check(document.get('schema') == SCHEMA, 'schema')
    check(document.get('host') == HOST, 'node5_host')
    check(exact_scope(document.get('scope')), 'only_exact_0_3_4_scope')
    check(fresh(document.get('observed_unix'), now), 'fresh_metadata_required')
    check(now < HARD_END, 'legacy_wall_expired_no_renewal')
    child = document.get('child')
    child = child if isinstance(child, dict) else {}
    check(child.get('ready') is True and child.get('cpu_passed') is True, 'child_not_CPU_ready')
    check(child.get('lease_scope_verified') is True, 'new_child_lease_scope_unverified')
    check(exact_scope(child.get('physicals')), 'matched_triplet_scope')
    for field in ('plan', 'source_manifest', 'cpu_gate'):
        check(valid_ref(child.get(field)), 'child_'+field+'_binding')
    hard_end = child.get('hard_end_unix')
    check(finite(hard_end) and now < hard_end <= HARD_END, 'incompatible_child_wall_no_extension')
    check(child.get('lease_end_unix') == LEASE_END, 'same_existing_lease_end')
    duration = child.get('expected_duration_seconds')
    check(finite(duration) and duration > 0 and finite(hard_end)
        and now+duration+120 < hard_end, 'insufficient_remaining_window')
    permission = document.get('main_go')
    permission = permission if isinstance(permission, dict) else {}
    check(permission.get('authorized') is True and permission.get('published_by') == 'MAIN',
        'MAIN_GO_missing')
    check(exact_scope(permission.get('physicals')), 'MAIN_GO_scope')
    check(valid_ref(permission.get('receipt')), 'MAIN_GO_receipt_binding')
    for field in ('plan', 'source_manifest', 'cpu_gate'):
        check(valid_ref(permission.get(field)) and permission.get(field) == child.get(field),
            'MAIN_GO_ready_child_'+field+'_join')
    start, expires = permission.get('not_before_unix'), permission.get('expires_unix')
    check(finite(start) and finite(expires) and finite(hard_end)
        and start <= now < expires <= hard_end, 'MAIN_GO_window')
    lanes = document.get('lanes')
    lanes = lanes if isinstance(lanes, list) else []
    check(exact_scope([lane.get('physical') if isinstance(lane, dict) else None for lane in lanes]),
        'exact_three_unique_target_records')
    for lane in lanes:
        if not isinstance(lane, dict):
            continue
        physical = lane.get('physical')
        if type(physical) is not int or physical not in PHYSICALS:
            continue
        target = TARGETS[physical]
        prefix = f'physical{physical}:'
        for field in ('root', 'owner', 'lease'):
            check(lane.get(field) == target[field], prefix+field+'_drift')
        owner = lane.get('owner')
        check(isinstance(owner, dict) and type(owner.get('pid')) is int
            and type(owner.get('uid')) is int, prefix+'integer_owner_identity')
        check(lane.get('uuid') == UUIDS[physical], prefix+'UUID_drift')
        check(fresh(lane.get('observed_unix'), now), prefix+'stale_owner_boundary')
        check(lane.get('children_reaped') is True, prefix+'started_child_not_reaped')
        check(type(lane.get('active_work_count')) is int and lane['active_work_count'] == 0,
            prefix+'started_learning_or_readout')
        check(type(lane.get('future_charges')) is int and lane['future_charges'] == 0,
            prefix+'successor_already_charged')
        boundary = lane.get('boundary')
        boundary = boundary if isinstance(boundary, dict) else {}
        check(boundary.get('complete') is True, prefix+'incomplete_cycle')
        cycle, sleep = boundary.get('cycle'), boundary.get('sleep')
        check(type(cycle) is int and cycle > 0, prefix+'cycle_required')
        check(type(sleep) is int and sleep >= 0, prefix+'sleep_required')
        preserved = boundary.get('preserved')
        preserved = preserved if isinstance(preserved, dict) else {}
        for component in COMPONENTS[target['kind']]:
            check(valid_ref(preserved.get(component)), prefix+'preserve_'+component)
        if target['kind'] == 'grid':
            check(now < F4_TRAIN_END, prefix+'TRAIN_window_closed')
            check(boundary.get('optimizer_used') is False, prefix+'frozen_grid_no_optimizer')
            check(boundary.get('failed_predispatch_charges') == [4456], prefix+'failed_charge4456_preserved')
        else:
            readouts = boundary.get('readouts')
            readouts = readouts if isinstance(readouts, dict) else {}
            for scope in ('dev', 'open'):
                readout = readouts.get(scope)
                readout = readout if isinstance(readout, dict) else {}
                checkpoint = preserved.get('checkpoint')
                checkpoint = checkpoint if isinstance(checkpoint, dict) else {}
                check(readout.get('status') == 'COMPLETE' and type(readout.get('returncode')) is int
                    and readout['returncode'] == 0 and readout.get('reaped') is True
                    and type(readout.get('sleep')) is int and readout['sleep'] == sleep
                    and isinstance(checkpoint.get('sha256'), str)
                    and readout.get('checkpoint_sha256') == checkpoint['sha256']
                    and valid_ref(readout.get('process_result')) and valid_ref(readout.get('complete')),
                    prefix+scope+'_fresh_readout_not_successfully_finished')
    return dict(schema='R150_NODE5_RETIREMENT_ASSESSMENT_V1',
        status='BLOCKED' if blockers else 'METADATA_PREREQUISITES_MET_RUNTIME_BLOCKED',
        execution_permitted=False, remote_mutations=0, signals_sent=0,
        blockers=sorted(set(blockers)), runtime_blockers=list(RUNTIME_BLOCKERS),
        protected_physicals=list(PROTECTED), hard_end_unix=HARD_END,
        next_step='Keep old lanes working; MAIN must bind ready source and implement remaining runtime gates.')


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate_metadata_key')
        result[key] = value
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('contract', 'assess'))
    args = parser.parse_args()
    try:
        result = contract() if args.mode == 'contract' else assess(
            json.load(sys.stdin, object_pairs_hook=unique_object))
    except (ValueError, TypeError, KeyError):
        print(json.dumps(dict(status='INVALID_METADATA', execution_permitted=False)))
        return 2
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))
    return 0 if args.mode == 'contract' else 2 if result['blockers'] or result['runtime_blockers'] else 0


if __name__ == '__main__':
    sys.exit(main())
