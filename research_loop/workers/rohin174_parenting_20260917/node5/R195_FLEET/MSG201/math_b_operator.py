"""Single local entrypoint; dispatch only a tested, hash-bound receiving operator."""

import argparse
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys


HERE = Path(__file__).resolve().parent
SNAPSHOT = HERE / 'C2_SNAPSHOT_20260918T021847Z'
SNAPSHOT_SHA = '29ca04c2c51671c7df922a4b05448586e74eec35da45b03009877baccbccce84'
CONSOLE_SHA = '3c8c45a6bfef9bb7d5a36dd9ddaf1e0a2293c6a83c718cbe2bca8e0ed6d16b48'
CONTROL = '/localhome/local-rohing/orch_r201_math_b_node5_20260918_attempt1'
LIFE = CONTROL + '/life'
C3_ROOT = '/localhome/local-rohing/orch_r153_community_C3_20260916_attempt1/life'
C3_PID = 2668022
C3_START = '22198740'
GPU_UUID = 'GPU-d23c9369-39cf-51fd-833e-13292f173006'


def sha(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def bound_local(reference):
    path = Path(reference['path']).resolve()
    require(sha(path) == reference['sha256'], 'exact_local_' + path.name)
    return json.loads(path.read_bytes())


REMOTE_CHECK = r'''
import hashlib,json,os,sys
from pathlib import Path
def sha(path):
 with Path(path).open('rb') as handle:return hashlib.file_digest(handle,'sha256').hexdigest()
ready=json.load(sys.stdin)
for name in ('operator','plan','config','source_manifest','cpu'):
 reference=ready[name]
 assert sha(reference['path'])==reference['sha256'],'receiving_'+name+'_changed'
source=json.loads(Path(ready['source_manifest']['path']).read_bytes())
for relative,expected in source['source_files'].items():
 assert not Path(relative).is_absolute() and '..' not in Path(relative).parts
 assert sha(Path(source['source_root'])/relative)==expected,'receiving_source_changed'
plan=json.loads(Path(ready['plan']['path']).read_bytes())
assert plan['root']==LIFE and plan['source_root']==CONTROL+'/source'
assert plan['physical']==3 and plan['gpu_uuid']==GPU_UUID
assert plan['new_presentations']==16 and plan['rehearsal_presentations']==0
assert plan['hard_end_unix']==1789776000 and plan['lease_end_unix']==1789776600
cpu=json.loads(Path(ready['cpu']['path']).read_bytes())
assert cpu['status']=='PASS' and cpu['cuda_initialized'] is False
assert cpu['optimizer_restored_exact'] and cpu['console_masking_preserved']
assert cpu['learning_rate']==3e-5 and cpu['tool_root']==LIFE
assert cpu['snapshot_manifest_sha256']==SNAPSHOT_SHA and cpu['console_record_sha256']==CONSOLE_SHA
process=Path('/proc')/str(C3_PID)
fields=(process/'stat').read_text().rsplit(')',1)[1].split()
assert fields[19]==C3_START and fields[0] not in ('Z','X')
args=(process/'cmdline').read_bytes().rstrip(b'\0').decode().split('\0')
assert args[:4]==['/localhome/local-rohing/v2/venv/bin/python','-B','-m','gpu.orch_r125_continual_guard']
assert 'native' in args
guard=json.loads(Path(args[args.index('--config')+1]).read_bytes())
old_plan=json.loads(Path(guard['plan_path']).read_bytes())
assert old_plan['root']==C3_ROOT and old_plan['physical']==3 and old_plan['gpu_uuid']==GPU_UUID
os.execv('/localhome/local-rohing/v2/venv/bin/python',
 ['/localhome/local-rohing/v2/venv/bin/python','-B',ready['operator']['path'],
  'execute','--output',CONTROL,'--seconds','1200'])
'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('status', 'execute'))
    parser.add_argument('--ready', type=Path)
    parser.add_argument('--ready-sha256')
    arguments = parser.parse_args()
    require(sha(SNAPSHOT / 'MANIFEST.json') == SNAPSHOT_SHA, 'canonical_shared_snapshot')
    snapshot = json.loads((SNAPSHOT / 'MANIFEST.json').read_bytes())
    require(snapshot['console_record']['sha256'] == CONSOLE_SHA, 'same_console_for_all_arms')
    if arguments.action == 'status':
        print(json.dumps(dict(status='WAITING_MAIN_AND_RECEIVING_READY_NO_RETIREMENT',
            arm='MATH-B', retired_life='C3', physical=3, control_root=CONTROL, new_life_root=LIFE,
            source_cycle=51, source_optimizer_steps=4908, snapshot_manifest_sha256=SNAPSHOT_SHA,
            console_record_index=5846, console_record_sha256=CONSOLE_SHA,
            receiving_operator=CONTROL + '/rollout_operator.py', uniform_rollout_paused=True,
            guided_complete_cycles=3, parent_withdrawn_complete_cycles=3,
            no_original_C2_action=True)))
        return
    require(arguments.ready is not None and arguments.ready_sha256 is not None,
            'Main_and_actual_receiving_READY_required_before_any_retirement')
    ready = bound_local(dict(path=str(arguments.ready), sha256=arguments.ready_sha256))
    require(ready['status'] == 'ACTUAL_SOURCE_CPU_READY_NOT_STOPPED' and ready['arm'] == 'MATH-B',
            'tested_receiving_ready_for_MATH_B')
    main_ready = bound_local(ready['main_ready'])
    require(main_ready['schema'] == 'R201_MAIN_TESTED_SOURCE_OVERLAY_V1'
            and main_ready['status'] == 'CPU_TESTED_NOT_LIVE'
            and main_ready['archive_sha256'] == '599f44f1a39bc0a312a180963feef8affc62748cec20721a79112bfc5a0540b1'
            and len(main_ready['files']) == 33
            and [suite['passed'] for suite in main_ready['tests']] == [292, 108]
            and all(suite['failed'] == suite['skipped'] == 0 for suite in main_ready['tests']),
            'supplied_Main_schema_hash_and_passing_tests')
    require(ready['snapshot_manifest_sha256'] == SNAPSHOT_SHA
            and ready['console_record_sha256'] == CONSOLE_SHA, 'shared_source_and_console_bytes')
    require(ready['retire_root'] == C3_ROOT and ready['retire_pid'] == C3_PID
            and ready['retire_start_ticks'] == C3_START, 'C3_only_retirement')
    require(ready['parent_style'] == 'B_OWN_OBJECT_WALKTHROUGH'
            and ready['guided_complete_cycles'] == ready['parent_withdrawn_complete_cycles'] == 3,
            'declared_three_guided_then_three_withdrawn_regardless_of_success')
    require(ready['live_inbox_replication'] is False and ready['publish_new_Rohin_messages'] is False,
            'no_live_original_C2_inputs')
    for name in ('operator', 'plan', 'config', 'source_manifest', 'cpu'):
        require(Path(ready[name]['path']).is_relative_to(CONTROL), 'owned_receiving_' + name)
    require(ready['operator']['path'] == CONTROL + '/rollout_operator.py', 'existing_handoff_adapter_entrypoint')
    constants = '\n'.join(name + '=' + repr(globals()[name]) for name in (
        'CONTROL', 'LIFE', 'C3_ROOT', 'C3_PID', 'C3_START', 'GPU_UUID', 'SNAPSHOT_SHA', 'CONSOLE_SHA'))
    command = 'python3 -B -c ' + shlex.quote(constants + '\n' + REMOTE_CHECK)
    result = subprocess.run(['bash', str(HERE.parents[5] / 'gpu/ovx3_ssh.sh'), command],
                            input=json.dumps(ready), text=True, timeout=1800)
    raise SystemExit(result.returncode)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, FileNotFoundError) as error:
        print(json.dumps(dict(status='BLOCKED_NO_DISPATCH', reason=str(error))), file=sys.stderr)
        raise SystemExit(3)
