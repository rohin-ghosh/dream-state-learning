"""Node5 fixed51/common5846 receiver and exact-boundary resource reallocation."""

import argparse
import ast
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import select
import shutil
import signal
import socket
import subprocess
import sys
import tarfile
import time


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'source'
CONTROL = ROOT / 'r204_control'
MAIN = Path('/localhome/local-rohing/orch_r204_C2_20260918_resume1/main_ready')
PYTHON = '/localhome/local-rohing/v2/venv/bin/python'
COMMON = Path('/localhome/local-rohing/orch_r201_math_b_node5_20260918_attempt1')
specification = importlib.util.spec_from_file_location('saved',
    '/localhome/local-rohing/orch_r202_C2_20260918_resume1/saved_primitives.py')
saved = importlib.util.module_from_spec(specification)
specification.loader.exec_module(saved)
read, sha, write, require = saved.read, saved.sha, saved.write, saved.require
SLOT = next(item for item in read(COMMON / 'R203_SCALE_ASSIGNMENT.json')['arms']
    if item['control_root'] == str(ROOT))
TRIAL = 'R204_node5_' + SLOT['arm'].replace('-', '_') + '_clone1'


def environment():
    return dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1',
        PYTHONPATH=str(SOURCE), HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
        OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')


def metadata(path):
    with path.open('rb') as handle:
        handle.seek(max(0, path.stat().st_size - 4096))
        raw = handle.read()
    return json.loads(b'{' + raw[raw.rfind(b',"index":') + 1:])


def configure():
    require(SLOT['physical'] in (0, 2, 3, 4, 5, 6), 'only_six_assigned_slots')
    require(not (ROOT / 'STARTED.json').exists(), 'unlaunched_fixed_copy')
    CONTROL.mkdir()
    main = read(MAIN / 'READY.json')
    require(main['schema'] == 'R204_MAIN_TESTED_SOURCE_OVERLAY_V1'
        and main['status'] == 'CPU_TESTED_NOT_LIVE' and len(main['files']) == 37
        and sha(MAIN / 'runtime_overlay.tar.gz') == main['archive_sha256'] ==
        'b0f148c92172af9d1525fda79a97bebfb31337e312e26c0f6bc805b3c687f8fc', 'Main_R204_frozen37')
    require(sha(ROOT / 'snapshot/MANIFEST.json') ==
        '29ca04c2c51671c7df922a4b05448586e74eec35da45b03009877baccbccce84', 'shared_capture')
    require(read(ROOT / 'life/stream/records/00000000000000005846.json')['sha256'] ==
        '3c8c45a6bfef9bb7d5a36dd9ddaf1e0a2293c6a83c718cbe2bca8e0ed6d16b48', 'common_console_cut')
    with tarfile.open(MAIN / 'runtime_overlay.tar.gz') as package:
        members = package.getmembers()
        require(len(members) == 37 and all(member.isfile() and member.name in main['files']
            and not Path(member.name).is_absolute() and '..' not in Path(member.name).parts
            for member in members), 'bounded_overlay')
        package.extractall(SOURCE, filter='data')
    require(all(sha(SOURCE / name) == expected for name, expected in main['files'].items()), 'exact37_files')
    driver = SOURCE / 'gpu/orch_r184_think_act_learn.py'
    text = driver.read_text()
    method = next(node for node in ast.walk(ast.parse(text))
        if isinstance(node, ast.FunctionDef) and node.name == '_cpu')
    original = ast.get_source_segment(text, method)
    replacement = ('def _cpu(self, origin):\n'
        + f'        if self.config["trial_id"] == {TRIAL!r}:\n'
        + '            from gpu.r184_cpu_bridge import call\n'
        + '            return call(self.config, origin)\n'
        + ''.join(original.splitlines(keepends=True)[1:]))
    require(text.count(original) == 1, 'single_existing_bridge_hook')
    driver.write_text(text.replace(original, replacement, 1))
    shutil.copy2(ROOT / 'math_b_bridge.py', SOURCE / 'gpu/r184_cpu_bridge.py')
    confinement = SOURCE / 'gpu/r184_node2_confinement.py'
    text = confinement.read_text()
    kernel = []
    for info in Path('/proc/driver/nvidia/gpus').glob('*/information'):
        values = dict(line.split(':', 1) for line in info.read_text().splitlines() if ':' in line)
        if values['GPU UUID'].strip() == SLOT['gpu_uuid']:
            require(int(values['Device Minor']) == SLOT['physical'], 'kernel_minor_matches_assignment')
            kernel.append(info.parent.name)
    require(len(kernel) == 1, 'actual_kernel_PCI_not_reconstructed_case')
    substitutions = {
        "DEVICE='GPU-d23c9369-39cf-51fd-833e-13292f173006'": 'DEVICE=' + repr(SLOT['gpu_uuid']),
        'MINOR=3': 'MINOR=' + str(SLOT['physical']),
        '/dev/nvidia3': '/dev/nvidia' + str(SLOT['physical']),
        '0000:57:00.0': kernel[0],
        '[0, 1, 2, 4, 5, 6, 7]': str([minor for minor in range(8) if minor != SLOT['physical']]),
        "'orch-r201-math-b1-'": repr('orch-r204-node5-' + str(SLOT['physical']) + '-'),
    }
    for before, after in substitutions.items():
        require(before in text, 'existing_namespace_copy_confinement_token:' + before)
        text = text.replace(before, after)
    require("properties['BindPaths']=config['copy_raw']+':'+plan['root']" in text, 'private_namespace_copy')
    confinement.write_text(text)
    plan = deepcopy(read(ROOT / 'snapshot/source_binding/PLAN.json'))
    plan.update(main['required_native_options'])
    plan.update(source_root=str(SOURCE), physical=SLOT['physical'], gpu_uuid=SLOT['gpu_uuid'], max_sleeps=57)
    plan['startup_context']['path'] = str(SOURCE / 'context/R153_STARTUP.md')
    facts = plan['think_act_learn']['environment_facts']
    plan['think_act_learn'] = dict(main['required_driver_options'], trial_id=TRIAL,
        cpu_gate_root='/localhome/local-rohing/orch_r153_cpu_smoke_20260917t2350z/gate',
        cpu_gate_sha256='c7821ed5b02651ed624c6dbe29a488bd15496440b59364e98e52ff2afe705e82',
        environment_facts=facts)
    if 'STRUCTURED' in SLOT['arm']:
        plan['think_act_learn']['structured_think_policy'] = main['optional_structured_think_policy']
    require(plan['hard_end_unix'] == 1789776000 and plan['lease_end_unix'] == 1789776600
        and plan['new_presentations'] == 16 and plan['rehearsal_presentations'] == 0
        and plan['anchor_lambda'] == .25 and plan.get('plasticity') is None, 'same_fixed_recipe_and_wall')
    sys.path.insert(0, str(SOURCE))
    from gpu.orch_r125_continual_native import validate_plan
    from gpu.orch_r125_cpu_experiment import digest, verify_gate
    validate_plan(plan)
    require(digest(verify_gate(plan['think_act_learn']['cpu_gate_root'])) ==
        plan['think_act_learn']['cpu_gate_sha256'], 'actual_same_boot_gate')
    write(CONTROL / 'PLAN.json', plan)
    write(ROOT / 'R204_SOURCE.json', dict(observed_unix=time.time(), Main_READY=saved.reference(MAIN / 'READY.json'),
        driver_delta='existing exact-trial external bridge adapter', confinement_delta='assigned UUID/minor/actual PCI only',
        original_C2_source_writes=0, original_C2_inbox_writes=0))
    logical = Path(plan['root'])
    original_stat = logical.stat()
    write(ROOT / 'ORIGINAL_MOUNT_IDENTITY.json', dict(original_device_inode=[original_stat.st_dev, original_stat.st_ino]))
    proof = ROOT / 'receiving_cpu.py'
    proof.write_text(proof.read_text().replace("ROOT / 'control/PLAN.json'", "ROOT / 'r204_control/PLAN.json'"))
    argv = ['sudo', '-n', '/usr/bin/systemd-run', '--quiet', '--wait', '--pipe',
        '--unit=orch-r204-node5-clone-state-' + str(SLOT['physical']) + '-' + str(time.time_ns()),
        '--property=User=2524', '--property=Group=2524', '--property=NoNewPrivileges=yes',
        '--property=DevicePolicy=closed', '--property=CapabilityBoundingSet=',
        '--property=BindPaths=' + str(ROOT / 'life') + ':' + str(logical),
        '--property=WorkingDirectory=' + str(SOURCE), '--property=MemoryMax=8589934592',
        '/usr/bin/env', '-i', 'PATH=/usr/bin:/bin', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
        'PYTHONPATH=' + str(SOURCE), 'OMP_NUM_THREADS=1', PYTHON, '-B', str(proof), 'state']
    with (ROOT / 'R204_STATE_CPU.log').open('x') as output:
        result = subprocess.run(argv, stdout=output, stderr=subprocess.STDOUT, timeout=120)
    require(result.returncode == 0, 'existing_receiving_state_proof_see_R204_STATE_CPU.log')
    with (ROOT / 'R204_TOOL_SMOKE.log').open('x') as output:
        result = subprocess.run([PYTHON, '-B', str(proof), 'smoke'], cwd=SOURCE, env=environment(),
            stdout=output, stderr=subprocess.STDOUT, timeout=90)
    require(result.returncode == 0, 'existing_actual_tool_smoke_see_R204_TOOL_SMOKE.log')
    pins = {str(path.relative_to(SOURCE)): sha(path) for path in SOURCE.rglob('*.py')}
    write(CONTROL / 'RECEIVING_CPU.json', dict(passed=True, source_pins=pins,
        Main_validation=main['validation'], Main_READY=saved.reference(MAIN / 'READY.json'),
        state=saved.reference(ROOT / 'STATE_CPU.json'), tool=saved.reference(ROOT / 'TOOL_SMOKE.json'),
        broad_suite_rerun=False, observed_unix=time.time()))
    old_guard = read(SLOT['old_guard']['path'])
    write(CONTROL / 'ALLOCATION.json', dict(plan_sha256=sha(CONTROL / 'PLAN.json'),
        cpu_tests_passed=True, physical=SLOT['physical'], gpu_uuid=SLOT['gpu_uuid'], builder_entry_logged=True,
        declared_unix=time.time(), cpu_receipt_path=str(CONTROL / 'RECEIVING_CPU.json'),
        cpu_receipt_sha256=sha(CONTROL / 'RECEIVING_CPU.json'), authority='Rohin203 six-slot resource reallocation plus R204'))
    config = dict(schema='R125_CONTINUAL_GUARD_V1', source_pins=pins, resume=True,
        copy_raw=str(ROOT / 'life'), plan_path=str(CONTROL / 'PLAN.json'), plan_sha256=sha(CONTROL / 'PLAN.json'),
        attempt_dir=str(CONTROL), host_sha256=hashlib.sha256(socket.gethostname().encode()).hexdigest(),
        hard_end_unix=plan['hard_end_unix'], lease_path=old_guard['lease_path'],
        lease_sha256=old_guard['lease_sha256'], next_reserved_unix=plan['lease_end_unix'],
        allocation_path=str(CONTROL / 'ALLOCATION.json'), allocation_sha256=sha(CONTROL / 'ALLOCATION.json'))
    write(CONTROL / 'GUARD.json', config)
    from gpu.orch_r125_continual_guard import validate
    validate(CONTROL / 'GUARD.json')
    write(ROOT / 'BRIDGE.json', dict(raw_root=str(ROOT / 'life'),
        journal_id=read(ROOT / 'life/stream/JOURNAL.json')['journal_id'],
        socket='/tmp/r204_node5_clone_' + str(SLOT['physical']) + '.sock', cpu_source=str(SOURCE),
        native_source=str(SOURCE), guard_path=str(CONTROL / 'GUARD.json'), guard_sha256=sha(CONTROL / 'GUARD.json'),
        gate_root=plan['think_act_learn']['cpu_gate_root'], gate_sha256=plan['think_act_learn']['cpu_gate_sha256'],
        code_policy=plan['think_act_learn']['code_policy'], stop_unix=min(time.time() + 7200, plan['hard_end_unix'])))
    write(ROOT / 'R204_READY.json', dict(observed_unix=time.time(), arm=SLOT['arm'], physical=SLOT['physical'],
        status='SOURCE_COMPATIBLE_RECEIVER_READY_NOT_RETIRED', source_cycle=51, optimizer_steps=4908,
        console_cut=5846, guided_cycles=[52, 53, 54], withdrawn_cycles=[55, 56, 57], success_required=False,
        cpu=saved.reference(CONTROL / 'RECEIVING_CPU.json'), plan=saved.reference(CONTROL / 'PLAN.json'),
        guard=saved.reference(CONTROL / 'GUARD.json'), operator=saved.reference(Path(__file__).resolve())))
    print(json.dumps(dict(arm=SLOT['arm'], status='R204_RECEIVER_READY_NO_RETIREMENT')), flush=True)


def execute():
    ready = read(ROOT / 'R204_READY.json')
    require(ready['status'] == 'SOURCE_COMPATIBLE_RECEIVER_READY_NOT_RETIRED', 'replacement_executable')
    require(sha(ready['operator']['path']) == ready['operator']['sha256'], 'bound_operator')
    for name in ('cpu', 'plan', 'guard'):
        require(sha(ready[name]['path']) == ready[name]['sha256'], 'bound_' + name)
    old = Path(SLOT['old_storage_root'])
    require('C2_' not in str(old) and 'repo_reader' not in str(old), 'reserved_lives_excluded')
    actor = saved.identity(SLOT['old_native']['pid'])
    require(actor['start_ticks'] == SLOT['old_native']['start_ticks'] and actor['cwd'] == SLOT['old_native']['cwd'],
        'exact_owned_old_native')
    plan = read(SLOT['old_plan']['path'])
    require(plan['physical'] == SLOT['physical'] and plan['gpu_uuid'] == SLOT['gpu_uuid'], 'old_slot_binding')
    (ROOT / 'RETIRE_ONCE').mkdir()
    handles = {'actor': os.pidfd_open(actor['pid'])}
    preserved = ROOT / 'retired_previous_life'
    preserved.mkdir()
    paths = sorted((old / 'stream/records').glob('[0-9]' * 20 + '.json'))
    next_index = max(0, len(paths) - 1)
    write(ROOT / 'RETIRE_ARMED.json', dict(observed_unix=time.time(), pid=os.getpid(), actor=actor,
        old_life=str(old), next_index=next_index, reason=SLOT['retirement_reason'], failed_science_claim=False))
    try:
        while time.time() < 1789775970:
            path = old / 'stream/records' / f'{next_index:020d}.json'
            if not path.exists():
                time.sleep(.01)
                continue
            next_index += 1
            if metadata(path)['kind'] != 'SLEEP_COMPLETE':
                continue
            saved.pause_exact(actor, handles['actor'])
            paused_unix = time.time()
            record = read(path)
            paths = sorted((old / 'stream/records').glob('[0-9]' * 20 + '.json'))
            tail = [metadata(item) for item in paths[record['index'] + 1:]]
            if any(item['kind'] != 'R184_LEARN_COMPLETE' for item in tail):
                write(preserved / f'MISSED_{record["index"]}.json', dict(observed_unix=paused_unix, tail=tail))
                signal.pidfd_send_signal(handles['actor'], signal.SIGCONT)
                continue
            document = record['document']
            state = document['resume_state']['state']
            require(document['status'] == 'COMPLETE' and state['pending'] is None
                and document['resume_state']['sha256'] == saved.digest(state), 'complete_old_state')
            checkpoint = old / 'checkpoints' / f'sleep_{document["cycle"]:06d}'
            shutil.copytree(checkpoint, preserved / checkpoint.name)
            require(saved.files(checkpoint) == saved.files(preserved / checkpoint.name), 'old_checkpoint_bytes')
            shutil.copytree(old / 'stream', preserved / 'stream')
            saved.verify_snapshot(preserved / 'stream', old, dict(reference=saved.reference(paths[-1])))
            owners = dict(actor=actor, timer=saved.identity(actor['parent']))
            parent_identity = saved.identity(owners['timer']['parent'])
            if parent_identity['cwd'] == actor['cwd']:
                owners['supervisor'] = parent_identity
            for name, identity in owners.items():
                if name != 'actor':
                    handles[name] = os.pidfd_open(identity['pid'])
            write(ROOT / 'PRESERVED_RETIREMENT.json', dict(paused_unix=paused_unix, preserved_unix=time.time(),
                old_life=str(old), owners=owners, cycle=document['cycle'], complete_index=record['index'],
                complete_sha256=record['sha256'], checkpoint_files=saved.files(preserved / checkpoint.name),
                optimizer_steps=document['checkpoint']['optimizer_steps'], exact_head=saved.reference(paths[-1]),
                snapshot_root=str(preserved), reason=SLOT['retirement_reason'], no_scientific_failure_claim=True,
                original_C2_signals=0, original_C2_inbox_writes=0, no_old_life_reset=True))
            saved.same(actor)
            signal.pidfd_send_signal(handles['actor'], signal.SIGTERM)
            signal.pidfd_send_signal(handles['actor'], signal.SIGCONT)
            for name in owners:
                require(bool(select.select([handles[name]], [], [], 30)[0]), 'exact_old_actor_exit:' + name)
            write(ROOT / 'RETIRED.json', dict(retired_unix=time.time(), owners=owners,
                old_life=str(old), preservation=saved.reference(ROOT / 'PRESERVED_RETIREMENT.json'),
                original_C2_signals=0, repo_reader_signals=0))
            dispatch()
            return
        raise TimeoutError('no_complete_before_existing_wall')
    except BaseException as error:
        write(ROOT / ('RETIRE_FAILURE_' + str(time.time_ns()) + '.json'), dict(observed_unix=time.time(),
            error_type=type(error).__name__, reason=str(error)))
        raise
    finally:
        for descriptor in handles.values():
            os.close(descriptor)


def dispatch():
    sys.path.insert(0, str(SOURCE))
    from gpu import orch_r127_pilot_console as console
    part_one = ROOT / 'PART_ONE.txt'
    require(sha(part_one) == read(ROOT / 'PART_ONE_BINDING.json')['sha256'], 'exact_authorized_first_console')
    processes = {}
    for name, command in (
        ('bridge', [PYTHON, '-B', str(ROOT / 'math_b_bridge.py'), '--config', str(ROOT / 'BRIDGE.json')]),
        ('supervisor', [PYTHON, '-B', '-m', 'gpu.r184_node2_confinement', 'dispatch', '--config', str(CONTROL / 'GUARD.json')]),
    ):
        if name == 'supervisor':
            with console._open_stream_directory(ROOT / 'life', 'inbox') as (directory, path):
                publication = console._publish(directory, path, dict(schema=console.SCHEMA,
                    id='r204_000_rohin_part_one', text=part_one.read_text(), split='TRAIN', actor='parent',
                    speaker='Rohin', source_receipt=None))
            write(ROOT / 'FIRST_INPUT.json', dict(published_unix=time.time(), publication=publication,
                exact_authorized_source_sha256=sha(part_one), no_future_original_inbox_relay=True))
        with (ROOT / ('R204_' + name + '.log')).open('x') as output:
            process = subprocess.Popen(command, cwd=SOURCE, env=environment(), stdin=subprocess.DEVNULL,
                stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
        processes[name] = saved.identity(process.pid)
        if name == 'bridge':
            deadline = time.monotonic() + 20
            while not list((ROOT / 'bridge_receipts').glob('READY*')):
                require(process.poll() is None and time.monotonic() < deadline, 'actual_bridge_ready')
                time.sleep(.1)
    write(ROOT / 'STARTED.json', dict(observed_unix=time.time(), status='WRAPPERS_STARTED_NOT_LOADED_PROOF',
        arm=SLOT['arm'], physical=SLOT['physical'], processes=processes, old_life_retired=True,
        source_cycle=51, optimizer_steps=4908, console_cut=5846, actual_new_storage_root=str(ROOT / 'life'),
        inherited_logical_root=read(CONTROL / 'PLAN.json')['root']))
    print(json.dumps(dict(arm=SLOT['arm'], status='RETIRED_AND_NEW_CLONE_DISPATCHED', processes=processes)), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('configure', 'execute'))
    globals()[parser.parse_args().action]()
