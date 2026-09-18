"""Node1 binding of existing R201 prefix, CPU bridge and strict launcher."""

import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import time
import uuid


ROOT = Path(__file__).resolve().parent
ARM = json.loads((ROOT/'ARM.json').read_bytes()) if (ROOT/'ARM.json').exists() else {}
SOURCE = ROOT / 'source'
RAW = Path(ARM.get('raw_root', str(ROOT/'life')))
CONTROL = ROOT / 'control'
PYTHON = '/localhome/local-rohing/v2/venv/bin/python'
GUARD = Path(ARM.get('old_guard', '/localhome/local-rohing/orch_r181_node1_20260917/journal_overlay/lanes/lane7/identity_repair/control/GUARD.json'))
DEVICE = ARM.get('gpu_uuid', 'GPU-f0405a96-813d-7ac7-d641-3ec31d103037')
TRIAL = ARM.get('trial_id', 'R202_CREATIVE_B_node1_clone1')
PHYSICAL = ARM.get('physical', 7)
MINOR = ARM.get('device_minor', 4)
SOURCE_RECEIPT = 'R203_SOURCE.json' if ARM else 'R202_SOURCE.json'
GATE = '/localhome/local-rohing/orch_r153_cpu_smoke_20260918t0212z/gate'
GATE_SHA = 'ca755cbd60be96fa310bff0c8149ed8777159e0e09dbd437c076190f7577356d'


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def write(path, document):
    with Path(path).open('x') as output:
        json.dump(document, output, sort_keys=True, indent=2)
        output.flush()
        os.fsync(output.fileno())


def environment():
    return dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONPATH=str(SOURCE),
                PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')


def install_overlay(archive_path, expected):
    with tarfile.open(archive_path) as archive:
        members = archive.getmembers()
        require({item.name for item in members} == set(expected) and len(members) == len(expected), 'exact_overlay_members')
        for item in members:
            require(item.isfile() and '..' not in Path(item.name).parts and not Path(item.name).is_absolute(), 'regular_overlay')
            require(hashlib.file_digest(archive.extractfile(item), 'sha256').hexdigest() == expected[item.name], 'exact_overlay_bytes')
        archive.extractall(SOURCE, filter='data')


def prepare():
    if ARM:
        return prepare_r203()
    require(str(ROOT) == '/localhome/local-rohing/rohin174_parenting_20260917/node1/R195_FLEET/creative_b1', 'own_receiving_root')
    require(not CONTROL.exists(), 'new_receiver_not_restart')
    ready = read(ROOT / 'READY.json')
    structured = read(ROOT / 'R202_READY.json')
    require(sha(ROOT / 'R202_READY.json') == '801286b1eff706a372e90188b5983a0cdb324177261faaa3612e45c5fb4c0fe6'
            and sha(ROOT / 'structured_think_overlay.tar.gz') == structured['archive_sha256'], 'Main_R202_READY')
    require(read(ROOT / 'FIXED_PREFIX_READY.json')['full_receiving_journal_and_intents_verified'], 'fixed_prefix_receipt')
    install_overlay(ROOT / 'structured_think_overlay.tar.gz', structured['files'])
    adapted = read(ROOT / 'ADAPTER_FILES.json')
    install_overlay(ROOT / 'RECEIVING_ADAPTER.tar', adapted)
    plan = deepcopy(read(ROOT / 'snapshot/source_binding/PLAN.json'))
    old_guard = read(GUARD)
    old_plan = read(old_guard['plan_path'])
    context = read(ROOT / 'snapshot/console/CONTEXT_COMMITTED.json')['document']['state']
    plan.update(source_root=str(SOURCE), physical=7, gpu_uuid=DEVICE, max_sleeps=57,
                hard_end_unix=old_plan['hard_end_unix'], lease_end_unix=old_plan['lease_end_unix'])
    plan.update(ready['required_native_options'])
    plan['think_act_learn'] = dict(ready['required_driver_options'], **structured['driver_config_delta'],
        trial_id=TRIAL, cpu_gate_root=GATE, cpu_gate_sha256=GATE_SHA,
        environment_facts='You are a new CREATIVE-B clone, with a private scene/dialogue task. '
        'Your exact drafts and attributed parent feedback are recorded; parent judgments are not objective scores. '
        'No peer service is connected. A confined standard-library Python tool is available through an external '
        'CPU bridge, without network, GPU or home access; SymPy, mpmath and Torch are not exposed. '
        'Only a returned receipt establishes execution. Parent guidance is offered during the first three '
        'complete clone cycles and withdrawn for the next three. No original-C2 future inbox is copied.')
    plan['authorized_wall_extension'] = dict(schema='R131_SAVED_STATE_WALL_EXTENSION_V1',
        previous_deadline_unix=context['state']['deadline_unix'], previous_stream_sha256=context['sha256'],
        new_deadline_unix=old_plan['hard_end_unix'], lease_end_unix=old_plan['lease_end_unix'], safety_margin_seconds=21600)
    require(plan.get('plasticity') is None and plan['new_presentations'] == 16 and plan['anchor_lambda'] == .25,
            'fixed_LR3e5_new16_anchor')
    startup = plan['birth_prompt'].encode()
    require(hashlib.sha256(startup).hexdigest() == plan['startup_context']['sha256'], 'unchanged_source_birth_binding')
    context_dir = SOURCE / 'context'
    context_dir.mkdir(exist_ok=True)
    startup_path = context_dir / 'R202_INHERITED_STARTUP.md'
    with startup_path.open('xb') as output:
        output.write(startup)
    plan['startup_context']['path'] = str(startup_path)
    CONTROL.mkdir(mode=0o700)
    write(CONTROL / 'PLAN.json', plan)
    sys.path.insert(0, str(SOURCE))
    from gpu.orch_r125_continual_native import validate_plan, prepare_wall_extension
    from organism_v6.orch_r125_continual_stream import ContinualStream
    validate_plan(plan)
    stream = ContinualStream.restore(context, expected_sha256=context['sha256'])
    prepare_wall_extension(plan, stream, resume=True, plan_sha256=sha(CONTROL / 'PLAN.json'))
    require(all(Path(plan[key]).is_dir() for key in ('model_dir', 'anchors')), 'same_local_base_anchors')
    return finish()


def finish(log_name='RECEIVING_CPU2.log'):
    require(not (ROOT/SOURCE_RECEIPT).exists(), 'unconsumed_receiving_configuration')
    ready = read(ROOT/'READY.json')
    structured = read(ROOT/'R202_READY.json')
    adapted = read(ROOT/'ADAPTER_FILES.json')
    plan = read(CONTROL/'PLAN.json')
    old_guard = read(GUARD)
    sys.path.insert(0, str(SOURCE))
    run_env = dict(environment(), PYTEST_DISABLE_PLUGIN_AUTOLOAD='1', PYTHONPATH=str(SOURCE)+':'+str(SOURCE/'tests'))
    if ARM:
        approved = read(ROOT/'R203_READY.json')
        require(approved['status'] == 'CPU_TESTED_NOT_LIVE', 'Main_tested_R203_overlay')
        counts = ['0']
    else:
        with (ROOT / log_name).open('x') as output:
            result = subprocess.run([PYTHON, '-B', '-m', 'unittest', 'discover', '-s', str(SOURCE/'tests'),
                '-p', 'test_orch_r184_think_act_learn.py', '-q'],
                cwd=SOURCE, env=run_env, stdout=output, stderr=subprocess.STDOUT, timeout=180)
        require(result.returncode == 0, 'receiving_tests_failed_see_RETAINED_CPU_log')
        counts = re.findall(r'Ran (\d+) tests?', (ROOT / log_name).read_text())
        require(len(counts) == 1, 'actual_receiving_test_count')
    pins = {str(path.relative_to(SOURCE)): sha(path) for path in SOURCE.rglob('*.py')}
    source_receipt = dict(source_root=str(SOURCE), source_pins=pins, base_ready_sha256=sha(ROOT/'READY.json'),
        structured_ready_sha256=sha(ROOT/'R202_READY.json'), adapter_files=adapted,
        adapter_scope='Only trial '+TRIAL+'; default Main CPU dispatcher unchanged')
    if ARM:
        source_receipt.update(r203_ready_sha256=sha(ROOT/'R203_READY.json'),
            r203_overlay_binding=read(ROOT/'R203_OVERLAY_BINDING.json'))
    write(ROOT / SOURCE_RECEIPT, source_receipt)
    cpu = dict(status='PASS', tests_passed=int(counts[0]), cuda_initialized=False,
               source_manifest_sha256=sha(ROOT/SOURCE_RECEIPT), observed_unix=time.time(),
               Main_tests_reused=bool(ARM), receiving_config_and_hash_checks=True)
    write(ROOT / 'RECEIVING_CPU.json', cpu)
    allocation = dict(plan_sha256=sha(CONTROL/'PLAN.json'), cpu_tests_passed=True, gpu_uuid=DEVICE,
        physical=PHYSICAL, builder_entry_pushed=True, declared_unix=time.time(),
        authorization=('Main R203 exact node1 resource reallocation; tested overlay' if ARM else
            'Main scoped CREATIVE-B/support7 selection; tested R201 and R202 overlay receipts'),
        receiving_cpu_sha256=sha(ROOT/'RECEIVING_CPU.json'), original_C2_protected=True)
    write(CONTROL/'ALLOCATION.json', allocation)
    config = deepcopy(old_guard)
    config.update(resume=True, source_pins=pins, copy_raw=str(RAW), attempt_dir=str(CONTROL),
        plan_path=str(CONTROL/'PLAN.json'), plan_sha256=sha(CONTROL/'PLAN.json'),
        allocation_path=str(CONTROL/'ALLOCATION.json'), allocation_sha256=sha(CONTROL/'ALLOCATION.json'))
    config['device_containment']['unit'] = 'orch-r136-native-'+uuid.uuid4().hex
    write(CONTROL/'GUARD.json', config)
    check_config = deepcopy(config)
    check_config['device_containment']['unit'] = 'orch-r136-native-'+uuid.uuid4().hex
    write(CONTROL/'CPU_GUARD.json', check_config)
    from gpu.orch_r125_continual_guard import validate
    validate(CONTROL/'GUARD.json')
    bridge = dict(raw_root=str(RAW), journal_id=read(RAW/'stream/JOURNAL.json')['journal_id'],
        socket=str(ROOT/'cpu.sock'), cpu_source=str(SOURCE), native_source=str(SOURCE),
        guard_path=str(CONTROL/'GUARD.json'), guard_sha256=sha(CONTROL/'GUARD.json'),
        gate_root=GATE, gate_sha256=GATE_SHA, code_policy=plan['think_act_learn']['code_policy'],
        stop_unix=plan['hard_end_unix'])
    write(ROOT/'BRIDGE.json', bridge)
    print(json.dumps(dict(cpu, status='CONFIGURED_CPU_PASS_NOT_DISPATCHED')))


def prepare_r203():
    require(ROOT.parent == Path('/localhome/local-rohing/rohin174_parenting_20260917/node1/R195_FLEET')
        and str(ROOT) == ARM['remote_root'] and PHYSICAL in (2, 3, 4, 5), 'explicit_new_node1_arm')
    require(not CONTROL.exists(), 'new_receiver_not_restart')
    binding = read(ROOT/'R203_OVERLAY_BINDING.json')
    require(sha(ROOT/'R203_READY.json') == binding['ready_sha256'], 'exact_Main_R203_manifest')
    require(all(sha(SOURCE/name) == expected for name, expected in binding['received_files'].items()),
        'exact_received_overlay_and_scoped_adapter')
    require(read(ROOT/'FIXED_PREFIX_READY.json')['full_receiving_journal_and_intents_verified'], 'same_fixed_prefix')
    require(sha(GUARD) == ARM['old_guard_sha256'], 'selected_original_guard')
    plan = read(ROOT/'PLAN_R203.json')
    require(sha(ROOT/'PLAN_R203.json') == binding['plan_sha256'], 'bound_receiving_plan')
    require(plan['source_root'] == str(SOURCE) and plan['physical'] == PHYSICAL
        and plan['gpu_uuid'] == DEVICE and plan['hard_end_unix'] == ARM['hard_end_unix']
        and plan['lease_end_unix'] == ARM['lease_end_unix'], 'exact_selected_slot_and_wall')
    require(plan['new_presentations'] == 16 and plan['rehearsal_presentations'] == 0
        and plan['anchor_lambda'] == .25 and plan.get('plasticity') is None, 'fixed_new_only_recipe')
    require(plan['think_act_learn']['trial_id'] == TRIAL, 'exact_new_arm')
    CONTROL.mkdir(mode=0o700)
    write(CONTROL/'PLAN.json', plan)
    sys.path.insert(0, str(SOURCE))
    from gpu.orch_r125_continual_native import validate_plan, prepare_wall_extension
    from gpu.orch_r125_cpu_experiment import digest, verify_gate
    from organism_v6.orch_r125_continual_stream import ContinualStream
    validate_plan(plan)
    require(digest(verify_gate(GATE)) == GATE_SHA, 'actual_node1_existing_gate')
    context = read(ROOT/'snapshot/console/CONTEXT_COMMITTED.json')['document']['state']
    stream = ContinualStream.restore(context, expected_sha256=context['sha256'])
    prepare_wall_extension(plan, stream, resume=True, plan_sha256=sha(CONTROL/'PLAN.json'))
    require(all(Path(plan[key]).is_dir() for key in ('model_dir', 'anchors')), 'same_local_base_anchors')
    return finish()


def dependencies():
    require(not (ROOT/'R202_SOURCE.json').exists(), 'not_repairing_frozen_or_launched_source')
    capture = read(ROOT/'MANIFEST.json')
    installed = {}
    for entry in capture['files']:
        name = Path(entry['relative'])
        if name.parts[0] != 'source' or name.suffix != '.py':
            continue
        donor = ROOT/'snapshot'/name
        destination = SOURCE/name.relative_to('source')
        if destination.exists():
            continue
        require(sha(donor) == entry['sha256'], 'fixed_capture_dependency')
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(donor, destination)
        installed[str(name.relative_to('source'))] = entry['sha256']
    write(ROOT/'RECEIVING_DEPENDENCIES.json', dict(added=installed, source='exact_fixed_C2_capture',
        existing_files_overwritten=0, original_sources_changed=0, observed_unix=time.time()))
    return finish('RECEIVING_CPU3.log')


def equal(left, right, torch):
    if torch.is_tensor(left):
        return torch.equal(left, right)
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(equal(left[key], right[key], torch) for key in left)
    if isinstance(left, (list, tuple)):
        return len(left) == len(right) and all(equal(first, second, torch) for first, second in zip(left, right))
    return left == right


def namespace_command(mode):
    sys.path.insert(0, str(SOURCE))
    from gpu.orch_r136_node1_launcher import device_containment_command
    config = read(CONTROL/('CPU_GUARD.json' if mode == 'check' else 'GUARD.json'))
    plan = read(CONTROL/'PLAN.json')
    policy = config['device_containment']
    arguments = ([PYTHON, '-B', str(Path(__file__).resolve()), 'bound-check'] if mode == 'check' else
        [PYTHON, '-B', '-m', 'gpu.orch_r136_node1_launcher', 'contained-native', '--config', str(CONTROL/'GUARD.json')])
    command = device_containment_command(PHYSICAL, MINOR, 1395, 1395, policy['unit'], SOURCE, arguments,
        240 if mode == 'check' else int(plan['hard_end_unix']-time.time()-10))
    location = command.index('/usr/bin/env')
    command[location:location] = ['--property=BindPaths='+str(RAW)+':'+plan['root'],
                                '--property=ReadOnlyPaths='+str(SOURCE)]
    return command


def bound_check():
    sys.path.insert(0, str(SOURCE))
    import torch
    from gpu.orch_r136_node1_launcher import verify_device_containment
    from gpu.orch_r125_stream_journal import StreamJournal
    from gpu.orch_r125_continual_native import NativeChild
    config, plan = read(CONTROL/'CPU_GUARD.json'), read(CONTROL/'PLAN.json')
    device_proof = verify_device_containment(config, plan)
    logical = Path(plan['root'])
    require(logical.stat().st_ino == RAW.stat().st_ino, 'private_namespace_exact_new_clone_root')
    with StreamJournal(logical/'stream') as journal:
        audit = journal.audit()
        require(audit['record_count'] == 5847, 'no_new_history_input_consumed_by_CPU_check')
        checkpoint = read(logical/'checkpoints/sleep_000051/COMMIT.json')
        NativeChild.verify_checkpoint(checkpoint)
        payload = torch.load(checkpoint['optimizer_rng_path'], map_location='cpu', weights_only=False)
        groups = payload['optimizer']['param_groups']
        require(payload['optimizer_steps'] == 4908 and len(groups) == 1 and groups[0]['lr'] == 3e-5,
                'exact_source_optimizer_steps_LR')
        parameters = [torch.nn.Parameter(torch.zeros_like(payload['optimizer']['state'][identifier]['exp_avg']))
                      for identifier in groups[0]['params']]
        optimizer = torch.optim.AdamW(parameters, lr=3e-5, foreach=False, fused=False)
        optimizer.load_state_dict(payload['optimizer'])
        require(equal(payload['optimizer'], optimizer.state_dict(), torch), 'exact_AdamW_load_roundtrip')
        require(not torch.cuda.is_initialized(), 'CPU_only_no_model')
    proof = dict(status='PASS', observed_unix=time.time(), audit=audit, strict_device=device_proof,
        optimizer_restored_exact=True, optimizer_steps=4908, learning_rate=3e-5,
        cuda_initialized=False, console_masking_preserved=True, part_one_consumed=False,
        physical_new_root=str(RAW), inherited_logical_root=plan['root'])
    write(ROOT/'RESTORE_CPU.json', proof)
    print(json.dumps(proof))


def check():
    with (ROOT/'NAMESPACE_CHECK.log').open('x') as output:
        result = subprocess.run(namespace_command('check'), stdout=output, stderr=subprocess.STDOUT, timeout=250)
    require(result.returncode == 0, 'namespace_CPU_binding_failed_see_log')
    print(json.dumps(read(ROOT/'RESTORE_CPU.json')))


def dispatch():
    require((ROOT/'RETIRED.json').is_file() and not (CONTROL/'DISPATCH_ONCE').exists(), 'exact_support_retired_once')
    require(read(ROOT/'RESTORE_CPU.json')['optimizer_restored_exact'], 'actual_receiving_restore')
    sys.path.insert(0, str(SOURCE))
    from gpu import orch_r136_node1_launcher as launcher
    from gpu.orch_r125_continual_guard import validate
    config, plan = validate(CONTROL/'GUARD.json')
    (CONTROL/'DISPATCH_ONCE').mkdir()
    report = launcher.scan(CONTROL/'GUARD.json', CONTROL/'ADMISSION.json')
    require(report['scanner_euid'] == 0 and report['clear'] and not report['blocking_reasons'], 'fresh_exclusive_slot')
    write(CONTROL/'ADMISSION_TIME.json', dict(verified_unix=time.time()))
    command = namespace_command('native')
    write(CONTROL/'CONTAINED_COMMAND.json', dict(command=command, issued_unix=time.time()))
    with (ROOT/'NATIVE_SERVICE.log').open('x') as output:
        result = subprocess.run(command, stdout=output, stderr=subprocess.STDOUT)
    write(CONTROL/'SERVICE_EXIT.json', dict(returncode=result.returncode, finished_unix=time.time()))
    require(result.returncode == 0, 'native_service_failed_no_retry')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('prepare', 'finish', 'dependencies', 'check', 'bound-check', 'dispatch'))
    arguments = parser.parse_args()
    {'prepare': prepare, 'finish': finish, 'dependencies': dependencies,
     'check': check, 'bound-check': bound_check, 'dispatch': dispatch}[arguments.action]()
