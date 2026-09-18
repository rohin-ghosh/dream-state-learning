"""Thin selected-life retirement adapter over existing R181/R144 primitives."""

import fcntl
import importlib.util
import json
import os
from pathlib import Path
import select
import shutil
import signal
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parent
ARM = json.loads((ROOT/'ARM.json').read_bytes()) if (ROOT/'ARM.json').exists() else {}
PYTHON = '/localhome/local-rohing/v2/venv/bin/python'
OLD = Path(ARM.get('old_guard', '/localhome/local-rohing/orch_r181_node1_20260917/journal_overlay/lanes/lane7/identity_repair/control/GUARD.json'))
PROTECTED = {int(pid): ticks for pid, ticks in ARM.get('protected', {
    2258434: '28070412', 2245391: '28062062', 273681: '40858962',
    418870: '40957164', 43557: '40702162', 574750: '41061383', 183848: '40797822'}).items()}


def imported(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    legacy = imported('/localhome/local-rohing/orch_r181_node1_20260917/operator/r181_operator.py', 'existing_node1_r181')
    base = legacy.legacy()
    require, read, sha, write = legacy.require, legacy.read, legacy.sha, legacy.write
    require(str(ROOT) == ARM.get('remote_root', '/localhome/local-rohing/rohin174_parenting_20260917/node1/R195_FLEET/creative_b1')
            and ROOT.parent == Path('/localhome/local-rohing/rohin174_parenting_20260917/node1/R195_FLEET')
            and os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'own_CPU_operator_root')
    base.current_node('a100')
    require(read(ROOT/'RESTORE_CPU.json')['optimizer_restored_exact'], 'receiving_private_namespace_ready')
    require(read(ROOT/'RECEIVING_CPU.json')['status'] == 'PASS', 'focused_receiving_tests_pass')
    source = read(ROOT/('R203_SOURCE.json' if ARM else 'R202_SOURCE.json'))
    require({str(path.relative_to(ROOT/'source')): sha(path) for path in (ROOT/'source').rglob('*.py')}
            == source['source_pins'], 'immutable_receiving_source_closure')
    require(read(ROOT/'R202_PART_ONE_PUBLICATION.json')['new_clone_input_ordinal'] == 1, 'Rohin_first_input_bound')
    require(list((ROOT/'bridge_receipts').glob('READY_*.json')), 'actual_existing_CPU_bridge_ready')
    bridge_owner = read(ROOT/'BRIDGE_STARTED.json')
    require(base.identity(bridge_owner['pid'])['start_ticks'] == bridge_owner['start_ticks'], 'same_bridge_owner')
    require(sha(OLD) == ARM.get('old_guard_sha256', 'bebd9405765e439fea4490aafef78b958e7d8377e294c6b3c014c8ef34fc3e17'), 'exact_selected_guard')
    config, plan, original = base.originals(OLD)
    require(plan['root'] == ARM.get('old_root', '/localhome/local-rohing/orch_r136_a100_classroom_support_20260916_attempt1/run1'), 'only_exact_selected_life')
    base.check_scope('a100', config, plan)
    pair = base.process_pair(ARM.get('old_pid', 159864), 'a100', OLD, config, plan)
    require(pair['actor']['start_ticks'] == ARM.get('old_start_ticks', '40781479'), 'selected_exact_actor')
    device = base.actual_device(plan)
    require(device['physical'] == ARM.get('physical', 7) and device['minor'] == ARM.get('device_minor', 4), 'actual_same_slot_not_index_as_minor')
    for pid, ticks in PROTECTED.items():
        require(base.identity(pid)['start_ticks'] == ticks, 'protected_life_identity')
    lock = os.open(ROOT/'SELECTED_LIFE.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    descriptors = {}
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        (ROOT/'HANDOFF_ONCE').mkdir()
        for role, expected in pair.items():
            require(base.identity(expected['pid']) == expected, 'same_actor_before_pidfd')
            descriptors[role] = os.pidfd_open(expected['pid'])
            require(base.identity(expected['pid']) == expected, 'same_actor_after_pidfd')
        deadline = min(time.monotonic()+1200, time.monotonic()+plan['hard_end_unix']-time.time()-900)
        write(ROOT/'ARMED.json', dict(armed_unix=time.time(), operator_pid=os.getpid(), wait_seconds=1200,
            original_actors=pair, device=device, signals_sent=0, new_clone_root=str(ROOT/'life')))
        while time.monotonic() < deadline:
            saved = base.sleep_boundary(plan['root'])
            if saved is None:
                time.sleep(.2)
                continue
            started_readout = legacy.readout_ready(base, plan, config, saved, pair['actor'], original.native)
            if started_readout is None:
                time.sleep(.2)
                continue
            with legacy.pause_watchdog(descriptors['actor'], 900) as pause_deadline:
                base.pause_exact(pair['actor'], descriptors['actor'])
                if base.sleep_boundary(plan['root']) != saved:
                    continue
                drained = False
                while time.monotonic()+120 < pause_deadline:
                    drained = base.readout_drained(plan, saved, pair['actor']['pid'], config['plan_path'], original.native)
                    if drained:
                        break
                    time.sleep(.2)
                require(drained, 'drain_deadline_original_resumes')
                original_stream = Path(plan['root'])/'stream'
                checkpoint = Path(plan['root'])/'checkpoints'/f"sleep_{saved['cycle']:06d}"
                size = legacy.reserve_tree(original_stream, 4*1024**3)+legacy.reserve_tree(checkpoint, 2*1024**3)
                require(shutil.disk_usage(ROOT).free > size+512*1024**2, 'whole_state_disk_admission')
                evidence = base.saved_evidence(plan, saved, original)
                shutil.copytree(original_stream, ROOT/'preserved_support_stream')
                shutil.copytree(checkpoint, ROOT/'preserved_support_checkpoint')
                base.verify_snapshot(ROOT/'preserved_support_stream', plan['root'], saved['state_sha256'], original)
                require(base.inventory_files(checkpoint) == base.inventory_files(ROOT/'preserved_support_checkpoint'), 'whole_saved_checkpoint')
                original_inbox = original_stream/'inbox'
                preserved_inbox = ROOT/'preserved_support_stream/inbox'
                for path in original_inbox.iterdir():
                    if not (preserved_inbox/path.name).exists():
                        shutil.copy2(path, preserved_inbox/path.name)
                require(base.inventory_files(original_inbox) == base.inventory_files(preserved_inbox), 'all_inbox_bytes_preserved')
                shutil.copy2(OLD, ROOT/'PRESERVED_SUPPORT_GUARD.json')
                shutil.copy2(config['plan_path'], ROOT/'PRESERVED_SUPPORT_PLAN.json')
                require(time.monotonic()+45 < pause_deadline and base.sleep_boundary(plan['root']) == saved, 'pre_retirement_boundary_and_time')
                for role, expected in pair.items():
                    require(base.identity(expected['pid']) == expected, 'same_owned_actor_before_retirement')
                write(ROOT/'BOUNDARY.json', dict(saved=evidence, readout=drained, started_readout=started_readout,
                    preserved_unix=time.time(), full_stream_and_checkpoint=True, inbox_inventory=base.inventory_files(preserved_inbox),
                    original_root_untouched=plan['root'], all_prior_original_artifacts_retained=True))
                write(ROOT/'RETIREMENT_STARTED.json', dict(started_unix=time.time(), original_actors=pair))
                signal.pidfd_send_signal(descriptors['actor'], signal.SIGTERM)
                signal.pidfd_send_signal(descriptors['actor'], signal.SIGCONT)
                for role in ('actor', 'timer', 'supervisor'):
                    require(select.select([descriptors[role]], [], [], 30)[0], 'natural_exact_exit_'+role)
                require(base.sleep_boundary(plan['root']) == saved, 'no_dropped_inflight_suffix')
                for pid, ticks in PROTECTED.items():
                    require(base.identity(pid)['start_ticks'] == ticks, 'protected_lives_still_exact')
                write(ROOT/'RETIRED.json', dict(saved=evidence, retired_unix=time.time(), physical=ARM.get('physical', 7),
                    actors_exited=pair, protected_lives_unchanged=PROTECTED, old_root_preserved=plan['root']))
            with (ROOT/'DISPATCH.log').open('x') as output:
                process = subprocess.Popen([PYTHON, '-B', str(ROOT/'receive_creative_b_v3.py'), 'dispatch'],
                    cwd=ROOT/'source', env=legacy.environment(ROOT/'source'), stdin=subprocess.DEVNULL,
                    stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
            write(ROOT/'DISPATCHED.json', dict(supervisor_pid=process.pid, dispatched_unix=time.time(),
                                              no_retry=True, actual_loaded=False))
            return
        write(ROOT/'NO_BOUNDARY.json', dict(observed_unix=time.time(), original_left_running=True, no_retry=True))
    except BaseException as error:
        write(ROOT/('HANDOFF_FAILURE_'+str(time.time_ns())+'.json'), dict(error_type=type(error).__name__,
            reason=str(error)[:1200], retired=(ROOT/'RETIRED.json').exists(), no_retry=True, observed_unix=time.time()))
        raise
    finally:
        for descriptor in descriptors.values():
            os.close(descriptor)
        os.close(lock)


if __name__ == '__main__':
    main()
