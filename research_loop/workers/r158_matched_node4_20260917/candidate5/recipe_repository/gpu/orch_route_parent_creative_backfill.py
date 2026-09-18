"""CPU preparation and deferred, strictly released physical1-only treatment."""

import argparse
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time

from gpu import orch_route_parent_campaign_run as run
from organism_v6 import orch_route_parent_creative_backfill as policy


MODULE = 'gpu.orch_route_parent_creative_backfill'
ROOT = Path(policy.ROOT)
BASELINE = Path(policy.BASELINE_ROOT)


def configure():
    policy.require(not os.environ.get('ROUTE_PARENT_CONFIG') and not os.environ.get('ROUTE_PARENT_WIRE_RESUME')
                   and not os.environ.get('ROUTE_PARENT_REPROJECT'), 'no_live_replay_or_repair_changes')
    run.policy = policy
    run.ROOT = ROOT
    run.RUN_MODULE = MODULE
    run.DEVICES = {'GUIDED': (1, run.guardian.DEVICES[1])}


def process(pid):
    directory = Path('/proc') / str(pid)
    try:
        return dict(pid=pid, boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
            start_ticks=int((directory/'stat').read_text().rsplit(')', 1)[1].split()[19]),
            uid=directory.stat().st_uid, command_sha256=run.sha(directory/'cmdline'))
    except FileNotFoundError:
        return None


def is_same_process(expected):
    return expected is not None and process(expected['pid']) == expected


def prepare():
    policy.require(socket.gethostname() == '[REDACTED_HOST]' and not (ROOT/'PREPARE.json').exists(), 'fresh_node3_cpu_prepare')
    dispatch = run.read(BASELINE/'DISPATCH_UNPARENTED.json')
    guardian = process(dispatch['pid'])
    policy.require(guardian is not None and guardian['uid'] == os.getuid()
        and (Path('/proc')/str(dispatch['pid'])/'cmdline').read_bytes().decode().split('\x00')[:-1] == dispatch['command'],
        'capture_exact_existing_off_guardian_before_release')
    baseline = run.read(BASELINE/'PREPARE.json')
    for name, expected in baseline['inputs'].items():
        policy.require(run.sha(BASELINE/name) == expected, 'canonical_input_drift:'+name)
    for name, expected in baseline['source_files'].items():
        policy.require(run.sha(BASELINE/'source'/name) == expected, 'canonical_source_drift:'+name)
    for name in ('initial_source_receipt.json', 'LEGACY_MATERIAL.json', 'OLD_MASKS.json',
                 'LEGACY_READOUT.json', 'SERVICE_IDENTITY.json', 'PROVIDER.json'):
        policy.require(not (ROOT/name).exists(), 'no_input_overwrite')
        shutil.copy2(BASELINE/name, ROOT/name)
    shutil.copytree(BASELINE/'initial_adapter', ROOT/'initial_adapter')
    run.prepare(ROOT)
    selected = run.read(ROOT/'COHORT.json')
    source = run.read(BASELINE/'SOURCE.json')
    policy.require(source['cohort_sha256'] == policy.BASELINE_COHORT_SHA256
                   and source['initial']['state_sha256'] == policy.INITIAL_STATE, 'reused_fixed_child_source')
    collections = {entry['world']['master']:entry for entry in source['collections']}
    chosen = [collections[world['master']] for group in selected['train']+selected['held'] for world in group]
    store = {}
    for collection in chosen:
        for record in collection['records']:
            if record['accepted']:
                store[record['edge']['event']] = record['event']['raw']
    run.write(ROOT/'SOURCE.json', dict(source, cohort_sha256=policy.digest(selected), collections=chosen,
        events=len(store), store_sha256=policy.digest(store)))
    (ROOT/'source_capture').mkdir()
    for group in selected['train']:
        for world in group:
            shutil.copy2(BASELINE/'source_capture'/(world['master']+'.json'), ROOT/'source_capture'/(world['master']+'.json'))
    run.source_store(ROOT, selected)
    for group in selected['train']:
        run.training_store(ROOT, group)
    run.write(ROOT/'OFF_OWNER.json', dict(guardian=guardian, dispatch_sha256=run.sha(BASELINE/'DISPATCH_UNPARENTED.json')))
    run.write(ROOT/'PROPOSAL.json', policy.proposal())
    run.write(ROOT/'REUSED_SOURCE_PROVENANCE.json', dict(baseline_root=str(BASELINE),
        baseline_prepare_sha256=run.sha(BASELINE/'PREPARE.json'), baseline_source_sha256=run.sha(BASELINE/'SOURCE.json'),
        baseline_cohort_sha256=policy.BASELINE_COHORT_SHA256, newly_generated_source_calls=0,
        same_initial_adapter_state=True, selection='FIXED_FIRST_GROUPS_NOT_OUTCOME_SELECTED'))
    prepared = run.read(ROOT/'PREPARE.json')
    for name in ('SOURCE.json','OFF_OWNER.json','PROPOSAL.json','REUSED_SOURCE_PROVENANCE.json'):
        prepared['inputs'][name] = run.sha(ROOT/name)
    for path in sorted((ROOT/'source_capture').glob('*.json')):
        prepared['inputs'][str(path.relative_to(ROOT))] = run.sha(path)
    test_path = 'tests/test_orch_route_parent_creative_backfill.py'
    prepared['source_files'][test_path] = run.sha(run.TREE/test_path)
    run.write(ROOT/'PREPARE.json', prepared)
    result = subprocess.run([sys.executable,'-B','-m','unittest','discover','-s',str(run.TREE/'tests'),
        '-p','test_orch_route_parent_creative_backfill.py','-v'], cwd=run.TREE, capture_output=True, text=True)
    (ROOT/'CPU_TESTS.log').write_text(result.stdout+result.stderr)
    policy.require(result.returncode == 0, 'own_native_cpu_tests_required')
    (ROOT/'parent_queue').mkdir()
    run.write(ROOT/'READY.json', dict(status='CPU_READY_NOT_LAUNCHED', prepared_unix=time.time(),
        prepare_sha256=run.sha(ROOT/'PREPARE.json'), proposal_sha256=run.sha(ROOT/'PROPOSAL.json'),
        cpu_tests_sha256=run.sha(ROOT/'CPU_TESTS.log'), source_files=prepared['source_files'],
        model_calls=0, gpu_calls=0, updates=0, main_post_required=True, authority=policy.proposal()['authority']))


def verify_ready():
    prepared = run.verify(ROOT)
    ready = run.read(ROOT/'READY.json')
    policy.require(ready['prepare_sha256'] == run.sha(ROOT/'PREPARE.json')
        and ready['proposal_sha256'] == run.sha(ROOT/'PROPOSAL.json')
        and ready['cpu_tests_sha256'] == run.sha(ROOT/'CPU_TESTS.log'), 'exact_ready_binding')
    policy.validate_posted(run.read(ROOT/'MAIN_POSTED.json'), run.sha(ROOT/'READY.json'), run.sha(ROOT/'PROPOSAL.json'))
    return prepared


def wait_release():
    owner = run.read(ROOT/'OFF_OWNER.json')
    deadline = run.read(BASELINE/'START.json')['hard_deadline_unix']
    while True:
        policy.require(time.time() < deadline, 'bounded_natural_completion_wait')
        policy.require(not (BASELINE/'UNPARENTED_GUARD/FAILED.json').exists(), 'off_failure_not_natural_release')
        guard_path = BASELINE/'UNPARENTED_GUARD/COMPLETE.json'
        if guard_path.exists() and not is_same_process(owner['guardian']):
            sleep_path = BASELINE/'UNPARENTED/cycle8/sleep/COMPLETE.json'
            readout_path = BASELINE/'UNPARENTED/cycle8/readout/COMPLETE.json'
            guard, sleep, readout = (run.read(path) for path in (guard_path,sleep_path,readout_path))
            boot, pid, ticks = readout['process']
            current = process(pid)
            child_alive = current is not None and (current['boot_id'],current['start_ticks']) == (boot,ticks)
            if child_alive:
                time.sleep(2)
                continue
            policy.validate_completion(guard,sleep,readout,False,False)
            return dict(released=True,owner='ROUTE_PARENT_CAMPAIGN',physical_index=1,
                uuid=run.guardian.DEVICES[1],natural_completion=True,recorded_unix=time.time(),
                prior_guardian=owner['guardian'],guard_sha256=run.sha(guard_path),
                final_sleep_sha256=run.sha(sleep_path),final_readout_sha256=run.sha(readout_path),
                canonical_files_modified=False)
        time.sleep(2)


def launch():
    verify_ready()
    policy.require(socket.gethostname() == '[REDACTED_HOST]' and os.geteuid() != 0, 'native_user_only')
    with (ROOT/'LAUNCH_CLAIM.json').open('x') as stream:
        json.dump(dict(claimed_unix=time.time(), automatic_restart=False),stream)
    release = wait_release()
    started = time.time()
    deadline = started + policy.CAPS['seconds']
    policy.require(deadline <= policy.CAMPAIGN_DEADLINE and deadline < run.guardian.LEASE_CUTOFF-6*3600,
                   'campaign_and_six_hour_lease_margins')
    with (ROOT/'START.json').open('x') as stream:
        json.dump(dict(started_unix=started,hard_deadline_unix=deadline,native_deadline_unix=deadline-30,
            caps=policy.CAPS,proposal_sha256=run.sha(ROOT/'PROPOSAL.json'),no_clock_reset=True),stream)
    admission = run.admit(ROOT,1,ROOT/'RELEASE_ADMISSION.json',deadline)
    run.write(ROOT/'STRICT_RELEASE.json',dict(release,admission_sha256=run.sha(ROOT/'RELEASE_ADMISSION.json'),
        privileged=admission['scanner_euid']==0, clear=admission['clear']))
    command=[run.guardian.PYTHON,'-B','-m',MODULE,'--phase','lane']
    with (ROOT/'LANE.log').open('x') as log:
        child=subprocess.Popen(command,cwd=run.TREE,env=dict(os.environ,PYTHONPATH=str(run.TREE),CUDA_VISIBLE_DEVICES=''),
            stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    run.write(ROOT/'DISPATCH.json',dict(pid=child.pid,command=command,physical_index=1,uuid=run.guardian.DEVICES[1],
        launched_unix=time.time(),deadline_unix=deadline,ready_sha256=run.sha(ROOT/'READY.json')))


def main():
    configure()
    parser=argparse.ArgumentParser()
    parser.add_argument('--phase',required=True,choices=('prepare','launch','lane','experience','sleep','readout'))
    parser.add_argument('--arm',choices=('GUIDED',),default='GUIDED')
    parser.add_argument('--cycle',type=int,default=0)
    args=parser.parse_args()
    if args.phase=='prepare':prepare()
    elif args.phase=='launch':launch()
    else:
        verify_ready()
        policy.require((ROOT/'STRICT_RELEASE.json').exists() and (ROOT/'START.json').exists(), 'strict_release_before_native_work')
        if args.phase=='lane':run.lane(ROOT,'GUIDED')
        else:
            policy.require(args.phase=='readout' and args.cycle==0 or 1<=args.cycle<=4, 'registered_cycle_only')
            run.stage(ROOT,'GUIDED',args.cycle,args.phase)


if __name__ == '__main__':
    main()
