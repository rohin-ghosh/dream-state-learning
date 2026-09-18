"""Same-life R204 continuation through the existing private bind and pidfd handoff."""

from copy import deepcopy
import fcntl
import hashlib
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
import uuid


ROOT = Path(__file__).resolve().parent
BASE = Path('/localhome/local-rohing/rohin174_parenting_20260917/node1/R195_FLEET')
PYTHON = '/localhome/local-rohing/v2/venv/bin/python'
READY_SHA = 'cc81c6218fbdb83f218e679250fdec5765e1d3829c1b88b76c166b275242cbb9'
OVERLAY_SHA = 'b0f148c92172af9d1525fda79a97bebfb31337e312e26c0f6bc805b3c687f8fc'
RELEASE = 'R204'
PROTECTED = {2258434: '28070412', 2245391: '28062062', 183848: '40797822'}


def read(path):
    return json.loads(Path(path).read_bytes())


def write(path, value):
    with Path(path).open('x') as output:
        json.dump(value, output, sort_keys=True, indent=2)


def sha(path):
    with Path(path).open('rb') as incoming:
        return hashlib.file_digest(incoming, 'sha256').hexdigest()


def imported(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def stage():
    assert ROOT.parent == BASE and os.getuid() == 1395 and os.environ.get('CUDA_VISIBLE_DEVICES') == ''
    request = read(ROOT/'REQUEST.json')
    old = Path(request['old_root'])
    assert old.parent == BASE and old.name in {'creative_b1', 'r203_math_comm_b2',
        'r203_repo_evidence_c3', 'r203_creative_structured_a4', 'r203_math_self_derive_c5'}
    old_control = Path(request.get('old_control', str(old/'control')))
    assert old_control in {old/'control', BASE/(old.name+'_r204')/'control'}
    if old_control != old/'control':
        active = read(old/'ACTIVE_CONTROL.json')
        assert active['control_root'] == str(old_control)
        assert active['guard_sha256'] == sha(old_control/'GUARD.json')
        write(ROOT/'PREVIOUS_ACTIVE_CONTROL.json', active)
    guard = read(old_control/'GUARD.json')
    old_plan = read(guard['plan_path'])
    assert sha(guard['plan_path']) == guard['plan_sha256']
    old_source = Path(old_plan['source_root'])
    assert {str(path.relative_to(old_source)): sha(path) for path in old_source.rglob('*.py')} == guard['source_pins']
    assert sha(ROOT/'READY.json') == READY_SHA and sha(ROOT/'runtime_overlay.tar.gz') == OVERLAY_SHA
    ready = read(ROOT/'READY.json')
    assert ready['status'] == 'CPU_TESTED_NOT_LIVE'
    source = ROOT/'source'
    shutil.copytree(old_source, source)
    for path in [source, *source.rglob('*')]:
        assert not path.is_symlink() and path.stat().st_uid == os.getuid()
        if path.is_file():
            assert path.stat().st_nlink == 1 and path.stat().st_ino != (old_source/path.relative_to(source)).stat().st_ino
        path.chmod(0o700 if path.is_dir() else 0o600)
    helper = imported(ROOT/'r203_receive.py', 'existing_overlay_receiver')
    helper.overlay(ROOT/'runtime_overlay.tar.gz', source, ready['files'])
    adapted = read(ROOT/'ADAPTER_FILES.json')
    helper.overlay(ROOT/'RECEIVING_ADAPTER.tar', source, adapted)
    plan = deepcopy(old_plan)
    plan.update(ready['required_native_options'])
    plan['source_root'] = str(source)
    plan['startup_context']['path'] = str(source/Path(old_plan['startup_context']['path']).relative_to(old_source))
    plan['think_act_learn'].update(ready['required_driver_options'])
    consumed_wall = plan.pop('authorized_wall_extension', None)
    assert (plan['hard_end_unix'], plan['lease_end_unix']) == (1790442300, 1790463900)
    assert plan['new_presentations'] == 16 and plan['rehearsal_presentations'] == 0
    assert plan['anchor_lambda'] == .25 and plan.get('plasticity') is None
    assert plan['think_act_learn']['trial_id'] == old_plan['think_act_learn']['trial_id']
    control = ROOT/'control'
    control.mkdir(mode=0o700)
    write(control/'PLAN.json', plan)
    raw = Path(guard['copy_raw'])
    assert raw == old/'life'
    arm = dict(physical=plan['physical'], device_minor=guard['device_containment']['minor'],
        gpu_uuid=plan['gpu_uuid'], trial_id=plan['think_act_learn']['trial_id'],
        old_guard=str(old_control/'GUARD.json'), old_guard_sha256=sha(old_control/'GUARD.json'),
        remote_root=str(ROOT), raw_root=str(raw), same_logical_life=True,
        hard_end_unix=plan['hard_end_unix'], lease_end_unix=plan['lease_end_unix'])
    write(ROOT/'ARM.json', arm)
    pins = {str(path.relative_to(source)): sha(path) for path in source.rglob('*.py')}
    write(ROOT/(RELEASE+'_SOURCE.json'), dict(source_root=str(source), source_pins=pins,
        Main_ready_sha256=READY_SHA, archive_sha256=OVERLAY_SHA, adapter_files=adapted,
        consumed_wall_authorization_removed=consumed_wall, no_new_wall=True,
        same_physical_journal=str(raw/'stream'), no_new_inputs=True))
    allocation = dict(plan_sha256=sha(control/'PLAN.json'), cpu_tests_passed=True,
        physical=plan['physical'], gpu_uuid=plan['gpu_uuid'], builder_entry_pushed=True,
        declared_unix=time.time(), authorization='Rohin '+RELEASE+' same-life saved-boundary continuation; Main tests reused')
    write(control/'ALLOCATION.json', allocation)
    config = deepcopy(guard)
    config.update(resume=True, source_pins=pins, attempt_dir=str(control),
        plan_path=str(control/'PLAN.json'), plan_sha256=sha(control/'PLAN.json'),
        allocation_path=str(control/'ALLOCATION.json'), allocation_sha256=sha(control/'ALLOCATION.json'))
    config['device_containment']['unit'] = 'orch-r136-native-'+uuid.uuid4().hex
    write(control/'GUARD.json', config)
    check = deepcopy(config)
    check['device_containment']['unit'] = 'orch-r136-native-'+uuid.uuid4().hex
    write(control/'CPU_GUARD.json', check)
    sys.path.insert(0, str(source))
    from gpu.orch_r125_continual_guard import validate
    from gpu.orch_r125_cpu_experiment import digest, verify_gate
    validate(control/'GUARD.json')
    driver = plan['think_act_learn']
    assert digest(verify_gate(driver['cpu_gate_root'])) == driver['cpu_gate_sha256']
    bridge = dict(raw_root=str(raw), journal_id=read(raw/'stream/JOURNAL.json')['journal_id'],
        socket=str(ROOT/'s'), cpu_source=str(source), native_source=str(source),
        guard_path=str(control/'GUARD.json'), guard_sha256=sha(control/'GUARD.json'),
        gate_root=driver['cpu_gate_root'], gate_sha256=driver['cpu_gate_sha256'],
        code_policy=driver['code_policy'], stop_unix=plan['hard_end_unix'])
    write(ROOT/'BRIDGE.json', bridge)
    write(ROOT/'STAGED.json', dict(observed_unix=time.time(), old_root=str(old),
        same_logical_life=True, no_rollback=True, no_input_publication=True,
        Main_tests_reused=True, receiving_config_hashes_and_existing_gate=True))


def boundary(base, logical):
    paths = base.records(logical)
    if not paths:
        return None
    terminal = base.read(paths[-1])
    if terminal['kind'] == 'SLEEP_COMPLETE':
        saved = base.sleep_boundary(logical)
        if saved is not None:
            saved['terminal_sha256'] = terminal['sha256']
        return saved
    if terminal['kind'] != 'R184_LEARN_COMPLETE' or len(paths) < 2:
        return None
    record = base.read(paths[-2])
    assert terminal['sha256'] == base.digest({key: value for key, value in terminal.items() if key != 'sha256'})
    assert record['kind'] == 'SLEEP_COMPLETE' and terminal['previous_sha256'] == record['sha256']
    assert record['sha256'] == base.digest({key: value for key, value in record.items() if key != 'sha256'})
    document = record['document']
    envelope = document['resume_state']
    state = envelope['state']
    assert document['status'] == 'COMPLETE' and envelope['sha256'] == base.digest(state)
    assert state['pending'] is None and state['sleep_frontier'] == len(state['rows'])
    assert terminal['document']['cycle'] == document['cycle']
    assert terminal['document']['checkpoint'] == read(Path(logical)/'checkpoints'/f"sleep_{document['cycle']:06d}"/'COMMIT.json')
    return dict(path=str(paths[-2]), record_sha256=record['sha256'], state_sha256=envelope['sha256'],
        state=state, cycle=document['cycle'], terminal_sha256=terminal['sha256'])


def verify_saved():
    sys.path.insert(0, str(ROOT/'source'))
    import torch
    from gpu.orch_r125_continual_native import NativeChild, ContinualStream, validate_plan
    from gpu.orch_r136_node1_launcher import verify_device_containment
    receiver = imported(ROOT/'receive_creative_b_v3.py', 'existing_receiving_roundtrip')
    plan = validate_plan(read(ROOT/'control/PLAN.json'))
    os.environ['CUDA_VISIBLE_DEVICES'] = plan['gpu_uuid']
    proof = verify_device_containment(read(ROOT/'control/CPU_GUARD.json'), plan)
    saved = read(ROOT/'BOUNDARY_STATE.json')
    stream = ContinualStream.restore(dict(state=saved['state'], sha256=saved['state_sha256']),
        expected_sha256=saved['state_sha256'])
    assert stream.deadline_unix == plan['hard_end_unix'] and stream.pending is None
    assert stream.sleep_frontier == len(stream.rows)
    checkpoint = read(Path(plan['root'])/'checkpoints'/f"sleep_{saved['cycle']:06d}"/'COMMIT.json')
    NativeChild.verify_checkpoint(checkpoint)
    payload = torch.load(checkpoint['optimizer_rng_path'], map_location='cpu', weights_only=False)
    group = payload['optimizer']['param_groups'][0]
    parameters = [torch.nn.Parameter(torch.zeros_like(payload['optimizer']['state'][identifier]['exp_avg']))
        for identifier in group['params']]
    optimizer = torch.optim.AdamW(parameters, lr=3e-5, foreach=False, fused=False)
    optimizer.load_state_dict(payload['optimizer'])
    assert receiver.equal(payload['optimizer'], optimizer.state_dict(), torch)
    assert payload['optimizer_steps'] == checkpoint['optimizer_steps'] and group['lr'] == 3e-5
    assert not torch.cuda.is_initialized()
    write(ROOT/'RESTORE_CPU.json', dict(status='PASS', observed_unix=time.time(),
        optimizer_restored_exact=True, optimizer_steps=payload['optimizer_steps'],
        same_logical_life=True, exact_state_sha256=saved['state_sha256'],
        adapter_sha256=checkpoint['adapter_state_sha256'], strict_device=proof,
        cuda_initialized=False, no_broad_tests=True, no_input_replay=True))


def handoff():
    request, arm = read(ROOT/'REQUEST.json'), read(ROOT/'ARM.json')
    old = Path(request['old_root'])
    legacy = imported('/localhome/local-rohing/orch_r181_node1_20260917/operator/r181_operator.py', 'existing_r181')
    base = legacy.legacy()
    config, plan, original = base.originals(Path(arm['old_guard']))
    assert sha(arm['old_guard']) == arm['old_guard_sha256']
    pair = base.process_pair(request['pid'], 'a100', Path(arm['old_guard']), config, plan)
    assert pair['actor']['start_ticks'] == request['start_ticks']
    for pid, ticks in PROTECTED.items():
        assert base.identity(pid)['start_ticks'] == ticks
    assert Path(plan['root']).stat().st_ino == Path(arm['raw_root']).stat().st_ino
    lock = os.open(ROOT/'HANDOFF.lock', os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW, 0o600)
    fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
    (ROOT/'HANDOFF_ONCE').mkdir()
    descriptors = {}
    try:
        for role, expected in pair.items():
            assert base.identity(expected['pid']) == expected
            descriptors[role] = os.pidfd_open(expected['pid'])
            assert base.identity(expected['pid']) == expected
        write(ROOT/'ARMED.json', dict(armed_unix=time.time(), original_actors=pair,
            same_logical_life=True, no_reseed=True, wait_seconds=1200))
        deadline = min(time.monotonic()+1200, time.monotonic()+plan['hard_end_unix']-time.time()-900)
        while time.monotonic() < deadline:
            saved = boundary(base, plan['root'])
            if saved is None:
                time.sleep(.2)
                continue
            started = legacy.readout_ready(base, plan, config, saved, pair['actor'], original.native)
            if started is None:
                time.sleep(.2)
                continue
            with legacy.pause_watchdog(descriptors['actor'], 900) as pause_deadline:
                base.pause_exact(pair['actor'], descriptors['actor'])
                if boundary(base, plan['root']) != saved:
                    continue
                drained = False
                while time.monotonic()+180 < pause_deadline:
                    drained = base.readout_drained(plan, saved, pair['actor']['pid'], config['plan_path'], original.native)
                    if drained:
                        break
                    time.sleep(.2)
                assert drained, 'readout_not_drained_original_resumes'
                evidence = base.saved_evidence(plan, saved, original)
                raw = Path(arm['raw_root'])
                checkpoint = raw/'checkpoints'/f"sleep_{saved['cycle']:06d}"
                required = legacy.reserve_tree(raw/'stream', 4*1024**3)+legacy.reserve_tree(checkpoint, 2*1024**3)
                assert shutil.disk_usage(ROOT).free > required+512*1024**2
                shutil.copytree(raw/'stream', ROOT/'preserved_stream')
                shutil.copytree(checkpoint, ROOT/'preserved_checkpoint')
                base.verify_snapshot(ROOT/'preserved_stream', plan['root'], saved['state_sha256'], original)
                assert base.inventory_files(checkpoint) == base.inventory_files(ROOT/'preserved_checkpoint')
                for path in (raw/'stream/inbox').iterdir():
                    if not (ROOT/'preserved_stream/inbox'/path.name).exists():
                        shutil.copy2(path, ROOT/'preserved_stream/inbox'/path.name)
                assert base.inventory_files(raw/'stream/inbox') == base.inventory_files(ROOT/'preserved_stream/inbox')
                shutil.copy2(arm['old_guard'], ROOT/'PRESERVED_GUARD.json')
                shutil.copy2(config['plan_path'], ROOT/'PRESERVED_PLAN.json')
                write(ROOT/'BOUNDARY_STATE.json', saved)
                with (ROOT/'SAVED_RESTORE.log').open('xb') as output:
                    result = subprocess.run([PYTHON, '-B', str(Path(__file__)), 'verify-saved'],
                        cwd=ROOT/'source', env=dict(os.environ, CUDA_VISIBLE_DEVICES=plan['gpu_uuid'], PYTHONPATH=str(ROOT/'source')),
                        stdout=output, stderr=subprocess.STDOUT, timeout=120)
                assert result.returncode == 0, 'same_life_R204_restore_failed_original_resumes'
                assert time.monotonic()+45 < pause_deadline and boundary(base, plan['root']) == saved
                write(ROOT/'BOUNDARY.json', dict(saved=evidence, preserved_unix=time.time(),
                    readout=drained, started_readout=started, same_logical_life=True,
                    full_stream_and_checkpoint=True, original_root_untouched=str(raw),
                    inbox_inventory=base.inventory_files(ROOT/'preserved_stream/inbox')))
                if RELEASE == 'R206' and plan['max_sleeps'] is not None and saved['cycle'] >= plan['max_sleeps']:
                    write(ROOT/'TERMINAL_SCREEN_PRESERVED.json', dict(observed_unix=time.time(),
                        cycle=saved['cycle'], state_sha256=saved['state_sha256'],
                        no_native_dispatch=True, no_screen_extension=True, original_resumes_to_normal_exit=True))
                    return
                for role, expected in pair.items():
                    assert base.identity(expected['pid']) == expected
                signal.pidfd_send_signal(descriptors['actor'], signal.SIGTERM)
                signal.pidfd_send_signal(descriptors['actor'], signal.SIGCONT)
                for role in ('actor', 'timer', 'supervisor'):
                    assert select.select([descriptors[role]], [], [], 30)[0], 'exact_exit_'+role
                assert boundary(base, plan['root']) == saved, 'no_inflight_suffix_loss'
                for pid, ticks in PROTECTED.items():
                    assert base.identity(pid)['start_ticks'] == ticks
                write(ROOT/'RETIRED.json', dict(retired_unix=time.time(), saved=evidence,
                    actors_exited=pair, same_logical_life=True, old_process_only=True,
                    continuing_raw_root=str(raw), no_new_inputs=True))
            return
        write(ROOT/'NO_BOUNDARY.json', dict(observed_unix=time.time(), original_preserved=True))
    finally:
        for descriptor in descriptors.values():
            os.close(descriptor)
        os.close(lock)


def run():
    stage()
    return resume_staged()


def resume_staged():
    assert (ROOT/'STAGED.json').is_file() and not (ROOT/'HANDOFF_ONCE').exists()
    pins = read(ROOT/(RELEASE+'_SOURCE.json'))['source_pins']
    assert {str(path.relative_to(ROOT/'source')): sha(path) for path in (ROOT/'source').rglob('*.py')} == pins
    request, arm = read(ROOT/'REQUEST.json'), read(ROOT/'ARM.json')
    deadline = time.monotonic()+1200
    if arm['physical'] == 7:
        for name in ('r203_math_comm_b2', 'r203_repo_evidence_c3', 'r203_creative_structured_a4', 'r203_math_self_derive_c5'):
            while not (BASE/name/'RETIRED.json').is_file():
                assert time.monotonic() < deadline, 'await_selected_retirements_without_cancelling'
                time.sleep(2)
    helper = imported(ROOT/'r203_receive.py', 'existing_receiver_processes')
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONPATH=str(ROOT/'source'),
        PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
    bridge_label = 'BRIDGE_AFTER_SOCKET_REPAIR' if (ROOT/'BRIDGE_STARTED.json').exists() else 'BRIDGE'
    bridge_receipt = ROOT/(bridge_label+'_STARTED.json')
    if not bridge_receipt.exists() and (ROOT/'BRIDGE_STARTED.json').exists():
        bridge_receipt = ROOT/'BRIDGE_STARTED.json'
    if bridge_receipt.exists() and list((ROOT/'bridge_receipts').glob('READY_*.json')):
        bridge = read(bridge_receipt)
        assert (Path('/proc')/str(bridge['pid'])/'stat').read_text().rsplit(') ', 1)[1].split()[19] == bridge['start_ticks']
    else:
        bridge = helper.start_process(ROOT, bridge_label, [PYTHON, '-B', str(ROOT/'source/gpu/r184_cpu_bridge.py'),
            '--config', str(ROOT/'BRIDGE.json')], environment)
    for attempt in range(100):
        if list((ROOT/'bridge_receipts').glob('READY_*.json')):
            break
        assert Path('/proc', str(bridge['pid'])).exists()
        time.sleep(.2)
    assert list((ROOT/'bridge_receipts').glob('READY_*.json'))
    sys.path.insert(0, str(ROOT/'source'))
    from gpu.orch_r136_node1_launcher import device_containment_command
    plan = read(ROOT/'control/PLAN.json')
    config = read(ROOT/'control/CPU_GUARD.json')
    command = device_containment_command(arm['physical'], arm['device_minor'], 1395, 1395,
        config['device_containment']['unit'], ROOT/'source', [PYTHON, '-B', str(Path(__file__)), 'handoff'], 2400)
    position = command.index('/usr/bin/env')
    command[position:position] = ['--property=BindPaths='+arm['raw_root']+':'+plan['root'],
        '--property=ReadOnlyPaths='+str(ROOT/'source')]
    with (ROOT/'HANDOFF_SERVICE.log').open('xb') as output:
        result = subprocess.run(command, stdout=output, stderr=subprocess.STDOUT, timeout=2420)
    write(ROOT/'HANDOFF_SERVICE_EXIT.json', dict(returncode=result.returncode, observed_unix=time.time()))
    if result.returncode == 0 and (ROOT/'TERMINAL_SCREEN_PRESERVED.json').exists():
        return
    assert result.returncode == 0 and (ROOT/'RETIRED.json').is_file(), 'handoff_not_complete_no_dispatch'
    process = helper.start_process(ROOT, 'DISPATCH', [PYTHON, '-B', str(ROOT/'receive_creative_b_v3.py'), 'dispatch'], environment)
    write(ROOT/'DISPATCHED.json', dict(dispatched_unix=time.time(), supervisor_pid=process['pid'],
        same_logical_life=True, actual_loaded=False, no_input_replay=True))
    active = dict(control_root=str(ROOT/'control'),
        guard_sha256=sha(ROOT/'control/GUARD.json'), published_unix=time.time(),
        same_logical_life=True, unchanged_raw_root=arm['raw_root'])
    destination = Path(request['old_root'])/'ACTIVE_CONTROL.json'
    if RELEASE == 'R206':
        assert read(destination) == read(ROOT/'PREVIOUS_ACTIVE_CONTROL.json')
        temporary = destination.with_name('ACTIVE_CONTROL_R206.partial')
        write(temporary, active)
        os.replace(temporary, destination)
    else:
        write(destination, active)


if __name__ == '__main__':
    actions = {'run': run, 'resume-staged': resume_staged, 'handoff': handoff, 'verify-saved': verify_saved}
    try:
        actions[sys.argv[1]]()
    except Exception as error:
        write(ROOT/('CONTINUATION_FAILURE_'+str(time.time_ns())+'.json'),
            dict(observed_unix=time.time(), error_type=type(error).__name__, reason=str(error),
                 retired=(ROOT/'RETIRED.json').exists(), no_automatic_retry=True))
        raise
