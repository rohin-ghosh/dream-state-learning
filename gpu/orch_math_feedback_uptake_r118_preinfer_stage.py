"""CPU-only custody stage for authentic reparented failed-startup timers."""

import argparse
import json
from pathlib import Path
import time
from types import FunctionType

from gpu import orch_math_feedback_uptake_r118_preinfer as repair


life = repair.life
IDENTITY_KEYS = ('pid', 'uid', 'start_ticks', 'boot_id', 'command_sha256', 'cwd', 'exe_device', 'exe_inode')


def validate_timer_identity(expected, actual):
    life.require(expected['pid'] != 1519259 and actual['pid'] != 1519259, 'Main_selector_never_owned_timer')
    life.require(all(key in expected and key in actual and str(expected[key]) == str(actual[key])
        for key in IDENTITY_KEYS), 'same_boot_PID_start_UID_command_executable_cwd')
    life.require(all(str(actual.get(key)) == str(value) for key, value in expected.items() if key != 'ppid'),
        'only_parent_PID_may_change_after_guard_exit')


def retire(service, permission_reference):
    service = Path(service)
    plan = life.plan_for(service)
    permission = life.authorization(permission_reference, plan, 'LAUNCH')
    life.require(permission.get('all_eight_released') is True, 'coordinated_all8_released')
    life.released(service)
    release = life.shared.read(service/'RELEASED.json')
    life.require(release.get('final_custody_pending') is True, 'only_pending_failed_startup_timers')
    life.require(not (service/'FINAL_TIMERS_RETIRED.json').exists(), 'single_timer_retirement')
    retired = []
    for reference in plan['old_timer_records']:
        historical = life.checked(reference)['identity']
        actual = life.identity(historical['pid'])
        validate_timer_identity(historical, actual)
        life.unused_old_FINAL(plan)
        life.cpu_only(actual)
        life.terminate_owned(actual, deadline=permission['expires_unix'])
        retired.append(dict(record=reference, historical_identity=historical, identity=actual,
            actual_eval_calls=0, parent_pid_change_only=historical.get('ppid') != actual.get('ppid')))
    life.shared.write(service/'FINAL_TIMERS_RETIRED.json', dict(release=life.ref(service/'RELEASED.json'),
        authorization=permission_reference, timers=retired, observed_unix=time.time(),
        stage_tool=life.ref(Path(__file__)), no_selector_signal=True))
    return life.ref(service/'FINAL_TIMERS_RETIRED.json')


def stage(service, permission, campaign_reference):
    repair.configure()
    campaign = life.checked(campaign_reference)
    evidence = life.shared.read(Path(service)/'PREINFERENCE_EXIT.json')
    failed_campaign = Path(evidence['failed_dispatch']['path']).parents[1]/'CAMPAIGN.json'
    life.require(Path(campaign_reference['path']).resolve() != failed_campaign.resolve(), 'new_Main_campaign_required')
    namespace = dict(life.stage.__globals__, retire_final_timers=retire)
    scoped_stage = FunctionType(life.stage.__code__, namespace, 'stage', life.stage.__defaults__)
    runtime = scoped_stage(service, permission, Path(campaign['activation_directory']), campaign_reference)
    return dict(runtime=runtime, owner=repair.owner(service), timers=life.ref(Path(service)/'FINAL_TIMERS_RETIRED.json'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--service', type=Path, required=True)
    parser.add_argument('--authorization', type=Path, required=True)
    parser.add_argument('--campaign', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(stage(args.service, life.ref(args.authorization), life.ref(args.campaign))))


if __name__ == '__main__':
    main()
