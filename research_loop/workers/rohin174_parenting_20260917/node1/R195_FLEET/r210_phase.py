"""Node1-only R210 parented phase after a preserved normal COMPLETE57 screen."""

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parent
BASE = Path('/localhome/local-rohing/rohin174_parenting_20260917/node1/R195_FLEET')
ARCHIVE_SHA = 'ccd62dbb0483240c23ac5caddc23cf5e7ee4a54b45e6896e49267f5f2efd60ec'
FILTER_SHA = '4bceeff13176f61b8ee32f4ae4f995ce8cce5d2aba7b2286bd13b6e48281d9ed'
MAX_SLEEPS = 69


def imported(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


continuation = imported(ROOT/'continue_r204.py', 'r210_existing_continuation')
read, write, sha = continuation.read, continuation.write, continuation.sha
continuation.ROOT = ROOT
continuation.RELEASE = 'R210'
continuation.OVERLAY_SHA = ARCHIVE_SHA


def replace(path, value):
    temporary = path.with_name(path.name+'.r210-partial')
    write(temporary, value)
    os.replace(temporary, path)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def boundary(raw):
    paths = sorted((raw/'stream/records').glob('[0-9]'*20+'.json'))[-3:]
    complete, learned, terminal = [read(path) for path in paths]
    assert [record['kind'] for record in (complete, learned, terminal)] == ['SLEEP_COMPLETE', 'R184_LEARN_COMPLETE', 'TERMINAL']
    for record in (complete, learned, terminal):
        assert record['sha256'] == digest({key: value for key, value in record.items() if key != 'sha256'})
    assert learned['previous_sha256'] == complete['sha256'] and terminal['previous_sha256'] == learned['sha256']
    assert terminal['document'] == dict(completed_sleeps=57, status='R184_SCREEN_STOP')
    document = complete['document']
    state = document['resume_state']['state']
    assert document['cycle'] == learned['document']['cycle'] == 57 and document['status'] == 'COMPLETE'
    assert document['checkpoint'] == learned['document']['checkpoint']
    assert state['pending'] is None and state['sleep_frontier'] == len(state['rows'])
    assert digest(state) == document['resume_state']['sha256']
    return dict(path=str(paths[0]), record_sha256=complete['sha256'], cycle=57, state=state,
                state_sha256=document['resume_state']['sha256'], checkpoint=document['checkpoint'],
                terminal_path=str(paths[-1]), terminal_sha256=terminal['sha256'])


def check_owners():
    request = read(ROOT/'REQUEST.json')
    control = Path(request['old_control'])
    assert read(control/'EXIT.json')['exit_code'] == 0
    for pid, ticks in continuation.PROTECTED.items():
        assert (Path('/proc')/str(pid)/'stat').read_text().rsplit(') ', 1)[1].split()[19] == ticks
    for process in Path('/proc').glob('[0-9]*'):
        try:
            arguments = (process/'cmdline').read_bytes().decode().split('\0')
        except (OSError, UnicodeDecodeError):
            continue
        assert str(control/'GUARD.json') not in arguments, 'previous_owner_or_supervisor_alive'
    return control


def stage():
    assert ROOT.parent == BASE and ROOT.name.endswith('_r210')
    request = read(ROOT/'REQUEST.json')
    assert request['phase'] == 'R210_PARENTED_ENRICHMENT' and request['max_sleeps'] == MAX_SLEEPS
    assert sha(ROOT/'READY.json') == request['ready_sha256'] and sha(ROOT/'runtime_overlay.tar.gz') == ARCHIVE_SHA
    continuation.READY_SHA = request['ready_sha256']
    def released_read(path):
        value = read(path)
        if Path(path) == ROOT/'READY.json':
            assert value['status'] == 'CPU_TESTED' and value['cpu_validation']['passed'] is True
            return dict(value, status='CPU_TESTED_NOT_LIVE')
        return value
    continuation.read = released_read
    old_control = check_owners()
    saved = boundary(Path(request['old_root'])/'life')
    assert time.time() < 1790442300-3600
    continuation.stage()
    plan_path = ROOT/'control/PLAN.json'
    plan = read(plan_path)
    assert plan['max_sleeps'] == 57 and plan['physical'] in (2, 3, 4, 5, 7)
    assert plan['think_act_learn']['prose_target_filter'] == 'R209_ENGLISH_PROSE_TARGET_QUARANTINE_V1'
    assert sha(ROOT/'source/organism_v6/orch_r203_prose_target_filter.py') == FILTER_SHA
    write(ROOT/'PHASE1_PLAN.json', read(old_control/'PLAN.json'))
    plan['max_sleeps'] = MAX_SLEEPS
    replace(plan_path, plan)
    allocation_path = ROOT/'control/ALLOCATION.json'
    allocation = read(allocation_path)
    allocation.update(plan_sha256=sha(plan_path), authorization='Rohin R210 node1 parented enrichment, own exact COMPLETE57, cycles58-69; no dose/wall/reset')
    replace(allocation_path, allocation)
    for filename in ('GUARD.json', 'CPU_GUARD.json'):
        path = ROOT/'control'/filename
        guard = read(path)
        guard.update(plan_sha256=sha(plan_path), allocation_sha256=sha(allocation_path))
        replace(path, guard)
    bridge = read(ROOT/'BRIDGE.json')
    bridge['guard_sha256'] = sha(ROOT/'control/GUARD.json')
    replace(ROOT/'BRIDGE.json', bridge)
    sys.path.insert(0, str(ROOT/'source'))
    from gpu.orch_r125_continual_guard import validate
    from gpu.r210_inbox import think_incoming
    from types import SimpleNamespace
    validate(ROOT/'control/GUARD.json')
    assert not think_incoming([SimpleNamespace(text='Astra: [R210_PEER] fixture')], 'ACT')
    assert len(think_incoming([SimpleNamespace(text='Astra: [R210_PARENT] fixture')], 'THINK')) == 1
    write(ROOT/'BOUNDARY_STATE.json', saved)
    write(ROOT/'R210_CPU.json', dict(passed=True, observed_unix=time.time(), Main_R209_tests_reused=62,
          private_CPU_branch_preserved=True, R210_parent_peer_first_delivery_THINK_only=True,
          english_prose_filter_sha256=FILTER_SHA, broad_tests=False, CUDA_initialized=False))
    print(json.dumps(dict(status='STAGED_NOT_LIVE', physical=plan['physical'], cycle=57, next_phase_cycles=[58, 69])))


def restore():
    continuation.verify_saved()


def launch():
    assert (ROOT/'R210_CPU.json').exists() and not (ROOT/'DISPATCH_ATTEMPT.json').exists()
    check_owners()
    request, arm = read(ROOT/'REQUEST.json'), read(ROOT/'ARM.json')
    raw = Path(arm['raw_root'])
    saved = boundary(raw)
    assert saved == read(ROOT/'BOUNDARY_STATE.json')
    write(ROOT/'DISPATCH_ATTEMPT.json', dict(started_unix=time.time(), no_automatic_retry=True, no_signals=True))
    preserved = ROOT/'phase1_preserved'
    preserved.mkdir(mode=0o700)
    for relative in ('stream', 'checkpoints/sleep_000057'):
        target = preserved/relative
        target.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(['cp', '-a', '--reflink=auto', str(raw/relative), str(target)], check=True, timeout=180)
    assert boundary(preserved)['terminal_sha256'] == saved['terminal_sha256']
    for path in (raw/'checkpoints/sleep_000057').rglob('*'):
        if path.is_file():
            assert sha(path) == sha(preserved/path.relative_to(raw))
    write(ROOT/'PHASE1_ENDED.json', dict(ended_at_cycle=57, status='NORMAL_SCREEN_END_PRESERVED',
          terminal_sha256=saved['terminal_sha256'], state_sha256=saved['state_sha256'],
          checkpoint=saved['checkpoint'], raw_root_owner=dict(uid=raw.stat().st_uid, gid=raw.stat().st_gid, inode=raw.stat().st_ino),
          next_phase='R210_PARENTED_ENRICHMENT', no_withdrawn_suffix_claim=True,
          previous_queued_feedback_withdrawal_confounded=True, snapshot=str(preserved), preserved_unix=time.time()))
    receiver = imported(ROOT/'receive_creative_b_v3.py', 'r210_existing_receiver')
    command = receiver.namespace_command('check')
    command[-2:] = [str(Path(__file__).resolve()), 'restore']
    with (ROOT/'RESTORE_SERVICE.log').open('xb') as output:
        checked = subprocess.run(command, stdout=output, stderr=subprocess.STDOUT, timeout=260)
    assert checked.returncode == 0 and read(ROOT/'RESTORE_CPU.json')['optimizer_restored_exact'], 'exact_CPU_restore_failed'
    assert boundary(raw) == saved
    check_owners()
    deadline = time.monotonic()+180
    while not (ROOT/'PARENT_ATTACHED.json').exists():
        assert time.monotonic() < deadline, 'parent_not_attached_no_GPU_dispatch'
        time.sleep(1)
    assert read(ROOT/'PARENT_ATTACHED.json')['phase'] == 'R210_PARENTED_ENRICHMENT'
    write(ROOT/'RETIRED.json', dict(status='PRIOR_OWNER_ALREADY_EXITED_NORMALLY_NO_KILL', signals=0,
                                  boundary_sha256=saved['state_sha256'], preserved_root=str(preserved)))
    helper = imported(ROOT/'r203_receive.py', 'r210_process_helper')
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONPATH=str(ROOT/'source'), PYTHONDONTWRITEBYTECODE='1',
                       OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
    bridge = helper.start_process(ROOT, 'BRIDGE', [continuation.PYTHON, '-B', str(ROOT/'source/gpu/r184_cpu_bridge.py'),
                                  '--config', str(ROOT/'BRIDGE.json')], environment)
    deadline = time.monotonic()+20
    while not list((ROOT/'bridge_receipts').glob('READY_*.json')):
        assert time.monotonic() < deadline and Path('/proc', str(bridge['pid'])).exists(), 'bridge_not_ready'
        time.sleep(.2)
    check_owners()
    process = helper.start_process(ROOT, 'DISPATCH', [continuation.PYTHON, '-B', str(ROOT/'receive_creative_b_v3.py'), 'dispatch'], environment)
    active_path = Path(request['old_root'])/'ACTIVE_CONTROL.json'
    assert read(active_path) == read(ROOT/'PREVIOUS_ACTIVE_CONTROL.json')
    replace(active_path, dict(control_root=str(ROOT/'control'), guard_sha256=sha(ROOT/'control/GUARD.json'),
                             published_unix=time.time(), same_logical_life=True, unchanged_raw_root=str(raw), phase='R210_PARENTED_ENRICHMENT'))
    write(ROOT/'DISPATCHED.json', dict(dispatched_unix=time.time(), supervisor=process, actual_loaded=False,
                                     max_sleeps=MAX_SLEEPS, no_baseline_reset=True, no_part_one_replay=True))
    print(json.dumps(dict(status='DISPATCHED_NOT_YET_LOADED', physical=arm['physical'], supervisor_pid=process['pid'])))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('stage', 'restore', 'launch'))
    args = parser.parse_args()
    try:
        globals()[args.mode]()
    except Exception as error:
        write(ROOT/('R210_FAILURE_'+str(time.time_ns())+'.json'), dict(error_type=type(error).__name__,
              reason=str(error) if isinstance(error, AssertionError) else None, mode=args.mode, no_automatic_retry=True))
        raise
