"""Read-only VM preflight for GRID recovery; never dispatches or signals."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess


OWNERS = {
    'F4': '9d81dd699eca744bc10f88e07e70c190da14353411b3667b3a027a15f4275d55',
    'A4': '29c58e47b04208f9fbf6a9e11c2088dab8e16c4d8f83b24776d564194ecbe9da',
}
CAMPAIGN_SHA = '7ea22b7fe4637ac344df140c7b56d49304091d067ec32d2558975ea1759e6610'
SOURCE = '/localhome/local-rohing/orch_r118_grid_failed_startup_source_20260915_v2'
RUNTIME = '/localhome/local-rohing/orch_r118_grid_shared_source_20260915_attempt2'


def require(value, reason):
    if not value:
        raise ValueError(reason)


def checked_identity(expected, *, proc=Path('/proc')):
    directory = proc / str(expected['pid'])
    fields = (directory / 'stat').read_text().rsplit(')', 1)[1].split()
    require(fields[0] not in ('Z','X') and int(fields[19]) == int(expected['start_ticks']) and
            (proc / 'sys/kernel/random/boot_id').read_text().strip() == expected['boot_id'] and
            directory.stat().st_uid == expected['uid'] and
            hashlib.sha256((directory / 'cmdline').read_bytes()).hexdigest() == expected['command_sha256'],
            'actual_broker_identity_without_mutable_ppid')


def native_code(branch):
    require(branch in OWNERS, 'owned_GRID_branch')
    return '''import hashlib,json,os,sys,time
from pathlib import Path
sys.path.insert(0, RUNTIME)
import gpu
gpu.__path__.insert(0,SOURCE+'/gpu')
from gpu import orch_r118_grid_failed_startup_run as helper
root=Path('/localhome/local-rohing/orch_r115_grid_pair_20260915')/BRANCH
directory=root/'parallel_recovery_1548'
owner_ref=helper.ref(directory/'FRESH_OWNER_FINAL.json')
assert owner_ref['sha256']==OWNER_SHA, 'exact_final_owner'
owner=helper.read(owner_ref)
plan=helper.read(owner['runtime_plan'])
assert plan['campaign']['sha256']==CAMPAIGN_SHA, 'exact_new_campaign'
assert os.environ.get('CUDA_VISIBLE_DEVICES')=='', 'CPU_only_preflight'
assert time.time()<plan['bounds']['train_end_unix']==1789491300, 'original_TRAIN_end'
runner=helper.configured_runner(plan)
handoff,unused=runner.modules(plan)
helper.verify_failed_start(plan,handoff)
handoff.validate_snapshot(helper.read(plan['boundary']))
handoff.parallel.campaign_document(plan['campaign']['path'],plan['campaign']['sha256'])
assert not (root/helper.TERMINAL).exists(), 'unused_recovery_terminal'
assert not (directory/'GUARD_ONCE').exists(), 'not_already_dispatched'
broker_ref=helper.ref(directory/'BROKER_READY.json')
broker=helper.read(broker_ref)
assert broker['runtime']==owner['runtime_plan'], 'broker_bound_new_PLAN'
assert broker['terminal_path']==str(root/helper.TERMINAL), 'broker_real_terminal'
assert broker['actual_single_lane_lock_acquired'] is True, 'actual_exclusive_lock_receipt'
assert (root/'parent_claude/RUNNER.lock').is_dir(), 'queue_lock_still_present'
if BRANCH=='F4':
 identity=broker['identity']
 process=Path('/proc')/str(identity['pid'])
 fields=(process/'stat').read_text().rsplit(')',1)[1].split()
 assert fields[0] not in ('Z','X') and int(fields[19])==int(identity['start_ticks'])
 assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==identity['boot_id']
 assert process.stat().st_uid==identity['uid']
 assert hashlib.sha256((process/'cmdline').read_bytes()).hexdigest()==identity['command_sha256']
 assert helper.ref(broker['source']['path'])==broker['source'], 'actual_native_broker_source'
else:
 assert broker['identity_location']=='VM', 'actual_A4_identity_location'
print(json.dumps(dict(branch=BRANCH,owner=owner_ref,broker=broker_ref,broker_document=broker,observed_unix=time.time(),GPU_started=False)))
'''.replace('RUNTIME', repr(RUNTIME)).replace('SOURCE', repr(SOURCE)).replace('OWNER_SHA', repr(OWNERS[branch])).replace('CAMPAIGN_SHA', repr(CAMPAIGN_SHA)).replace('BRANCH', repr(branch))


def preflight(branch, wrapper):
    command = 'CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 /localhome/local-rohing/v2/venv/bin/python -B -c ' + shlex.quote(native_code(branch))
    result = subprocess.run(['bash', str(wrapper), command], capture_output=True, text=True, timeout=90, check=True)
    document = json.loads(result.stdout)
    if branch == 'A4':
        broker = document['broker_document']
        checked_identity(broker['identity'])
        require(hashlib.sha256(Path(broker['source']['path']).read_bytes()).hexdigest() == broker['source']['sha256'],
                'actual_VM_broker_source')
    document.pop('broker_document')
    document.update(status='PASS_LIVE_BROKER_AND_CPU_PROVENANCE',signals=0,provider_calls=0)
    return document


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--branch', choices=tuple(OWNERS), required=True)
    parser.add_argument('--wrapper', type=Path, required=True)
    args = parser.parse_args()
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'VM_CPU_only_preflight')
    print(json.dumps(preflight(args.branch, args.wrapper), sort_keys=True))


if __name__ == '__main__':
    main()
