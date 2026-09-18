"""One exact R179 lane3 recovery after a proved pre-native admission failure."""

import argparse
from copy import deepcopy
import fcntl
import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid


BASE = Path('/localhome/local-rohing')
FAILED = BASE / 'orch_r179_node4_20260917t1810z/lane3'
LIFE = BASE / 'orch_r136_raw_parented_seed1_a40r3_20260916_attempt1/run1'
POLICY_SHA = 'b36949c2d93662b876b6519eee9dddba0e5af94a294e1f570f37685cd9604a2b'
GPU_UUID = 'GPU-4d0f10af-119f-10bb-a28f-f7b7703a3b14'
WALL = 1789754400
EXPECTED_BLOCKERS = ['process_identity_drift:4072176', 'process_identity_drift:4599']
AFTER_ADMISSION = ('ADMISSION_TIME.json', 'CONTAINED_COMMAND.json', 'CONTAINMENT_VERIFIED.json',
                   'LAUNCH.json', 'NATIVE.log', 'EXIT.json', 'SERVICE_EXIT.json')


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def ref(path):
    return dict(path=str(path), sha256=sha(path))


def validate_failure(facts):
    require(facts['physical'] == 3 and facts['root'] == str(LIFE) and facts['gpu_uuid'] == GPU_UUID,
            'only_exact_existing_lane3')
    require(facts['wall'] == WALL and facts['resume'] is True and facts['minor'] == 0,
            'same_saved_resume_wall_and_strict_device')
    require(facts['retired'] and not facts['old_owners_alive'] and not facts['supervisor_alive'],
            'old_owners_and_failed_supervisor_must_be_gone')
    require(facts['post_admission_artifacts'] == [] and not facts['loaded_receipt'],
            'only_proven_failure_before_native_dispatch')
    report = facts['admission']
    require(report['clear'] is False and report['scanner_euid'] == 0
            and report['blocking_reasons'] == EXPECTED_BLOCKERS and report['gpu']['uuid'] == GPU_UUID,
            'exact_preserved_original_preload_failure')
    require(facts['log'].rstrip().endswith('ValueError: unchanged_global_exclusive_admission'),
            'proved_guard_failure_not_silent_or_native_failure')
    require(facts['saved_evidence'] == facts['boundary_evidence'], 'exact_original_retired_saved_boundary')
    require(facts['readout_preserved'] and facts['record_inventory_preserved'],
            'no_journal_advance_or_readout_replay')


def make_guard(previous, control, source, plan_sha, allocation_sha, pins):
    result = deepcopy(previous)
    result.update(attempt_dir=str(control), plan_path=str(control / 'PLAN.json'), plan_sha256=plan_sha,
                  allocation_path=str(control / 'ALLOCATION.json'), allocation_sha256=allocation_sha,
                  source_pins={name: value for name, value in pins.items() if name.endswith('.py')})
    result['device_containment']['unit'] = 'orch-r136-native-' + uuid.uuid4().hex
    require(result['resume'] is True and result['hard_end_unix'] == WALL, 'no_resume_or_wall_change')
    return result


def modules():
    sys.path.insert(0, str(FAILED.parent))
    operator = importlib.import_module('node4_rollout')
    request = read(FAILED / 'STAGED.json')
    require(sha(FAILED.parent / 'node4_rollout.py') == request['operator_sha256'], 'frozen_R179_operator_bytes')
    return operator, operator.helper_module(FAILED.parent)


def cpu_command(source, command, output, timeout=180):
    with Path(output).open('x') as log:
        result = subprocess.run(command, cwd=source, env=dict(os.environ, CUDA_VISIBLE_DEVICES='',
            PYTHONPATH=str(source), PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1',
            HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1'), stdout=log, stderr=subprocess.STDOUT,
            timeout=timeout, check=False)
    require(result.returncode == 0, 'receiving_CPU_or_proof_failed:' + str(output))


def verify_failed(operator, helpers):
    helpers.current_node('a40r')
    request = helpers.read(FAILED / 'STAGED.json')
    require(helpers.sha(request['new_config']) == request['new_config_sha256'], 'original_failed_guard_bytes')
    config, plan, original = helpers.originals(Path(request['new_config']))
    proof = helpers.read(FAILED / 'SOURCE_PROOF.json')
    require(helpers.sha(FAILED / 'SOURCE_PROOF.json') == request['source_proof_sha256']
            and helpers.inventory_files(proof['new_source']) == proof['new_inventory']
            and helpers.inventory_files(proof['old_source']) == proof['old_inventory']
            and proof['new_inventory']['gpu/orch_r179_context_survival.py'] == POLICY_SHA,
            'exact_immutable_R179_sources_not_R171_proposals')
    boundary = helpers.read(FAILED / 'BOUNDARY.json')
    require(helpers.read(FAILED / 'RETIREMENT_STARTED.json')['boundary_sha256'] == helpers.sha(FAILED / 'BOUNDARY.json')
            and helpers.read(FAILED / 'RETIRED.json')['processes'] == request['processes'], 'exact_retired_owner_boundary')
    saved = helpers.sleep_boundary(plan['root'])
    require(saved is not None, 'still_exact_sleep_complete_head_before_recovery')
    evidence = operator.saved_evidence(plan, saved, original, helpers)
    old_alive = []
    for process in request['processes'].values():
        try:
            actual = helpers.identity(process['pid'])
            if actual['start_ticks'] == process['start_ticks'] and actual['boot_id'] == process['boot_id']:
                old_alive.append(process['pid'])
        except FileNotFoundError:
            pass
    dispatch = helpers.read(FAILED / 'DISPATCHED.json')
    readout_name = original.native.readout_name(plan, saved['cycle'])
    readout_root = LIFE / 'readouts'
    complete = readout_root / readout_name / 'COMPLETE.json'
    readout_ok = (not (readout_root / (readout_name + '_FAILED.json')).exists()
        and complete.exists() and complete.stat().st_mtime == boundary['readout']['completion_marker_mtime']
        and helpers.sha(readout_root / (readout_name + '_DISPATCH.json')) == boundary['readout']['dispatch_sha256'])
    facts = dict(physical=plan['physical'], root=plan['root'], gpu_uuid=plan['gpu_uuid'], wall=plan['hard_end_unix'],
        resume=config['resume'], minor=config['device_containment']['minor'], retired=(FAILED / 'RETIRED.json').exists(),
        old_owners_alive=old_alive, supervisor_alive=Path('/proc', str(dispatch['supervisor_pid'])).exists(),
        post_admission_artifacts=[name for name in AFTER_ADMISSION if (FAILED / 'control' / name).exists()],
        loaded_receipt=(FAILED / 'LOADED_RECEIPT.json').exists(), admission=helpers.read(FAILED / 'control/ADMISSION.json'),
        log=(FAILED / 'control/SUPERVISOR.log').read_text(), saved_evidence=evidence, boundary_evidence=boundary['saved'],
        readout_preserved=readout_ok,
        record_inventory_preserved=helpers.inventory_files(Path(boundary['snapshot']) / 'records')
            == helpers.inventory_files(LIFE / 'stream/records'))
    validate_failure(facts)
    return request, config, plan, proof, boundary, evidence


def prepare(output):
    require(output.parent.parent == BASE and output.name == 'lane3'
            and output.parent.name.startswith('orch_r179_node4_recovery_') and not output.exists(),
            'fresh_scoped_lane3_recovery_root')
    operator, helpers = modules()
    request, previous, plan, old_proof, boundary, evidence = verify_failed(operator, helpers)
    output.mkdir()
    source, control = output / 'source', output / 'control'
    shutil.copytree(request['source_root'], source)
    control.mkdir()
    pins = helpers.inventory_files(source)
    require(pins == old_proof['new_inventory'], 'copy_exact_R179_bytes_no_native_changes')
    new_plan = helpers.relocated_plan(plan, source)
    helpers.write(control / 'PLAN.json', new_plan)
    cpu_command(source, [str(helpers.PYTHON), '-B', str(FAILED.parent / 'cpu_actual.py'), '--source', str(source),
        '--predecessor', old_proof['old_source'], '--plan', str(control / 'PLAN.json')], output / 'CPU_POLICY.log')
    cpu = helpers.read(output / 'CPU_POLICY.log')
    require(cpu['status'] == 'PASS' and cpu['cases'] == 8, 'eight_actual_source_CPU_cases')
    cpu_command(source, [str(helpers.PYTHON), '-B', '-m', 'unittest', 'tests.test_orch_r124_train_history',
        'tests.test_orch_r125_continual_stream', 'tests.test_orch_r125_stream_journal'], output / 'CPU_FROZEN.log')
    allocation = helpers.read(previous['allocation_path'])
    allocation.update(plan_sha256=helpers.sha(control / 'PLAN.json'), recovery_cpu_sha256=helpers.sha(output / 'CPU_POLICY.log'))
    helpers.write(control / 'ALLOCATION.json', allocation)
    config = make_guard(previous, control, source, helpers.sha(control / 'PLAN.json'),
                        helpers.sha(control / 'ALLOCATION.json'), pins)
    helpers.write(control / 'GUARD.json', config)
    cpu_command(source, [str(helpers.PYTHON), '-B', '-c',
        'from gpu import orch_r125_continual_guard as guard; guard.validate(' + repr(str(control / 'GUARD.json')) + ')'],
        output / 'CPU_GUARD.log')
    probe_config = deepcopy(config)
    probe_config['device_containment']['unit'] = 'orch-r136-native-' + uuid.uuid4().hex
    helpers.write(output / 'PROBE_GUARD.json', probe_config)
    command = operator.handler(3, config)
    sys.path.insert(0, plan['source_root'])
    containment = importlib.import_module(command['module'])
    probe_argv = [str(helpers.PYTHON), '-B', '-c',
        'import json; from gpu import orch_r125_continual_guard as guard; '
        'from gpu import orch_r137_node4_containment as module; '
        'config,plan=guard.validate(' + repr(str(output / 'PROBE_GUARD.json')) + '); '
        'print(json.dumps(module.verify_device_containment(config,plan)))']
    policy = probe_config['device_containment']
    probe_command = containment.device_containment_command(3, 0, 2524, 2524, policy['unit'], source, probe_argv, 120)
    cpu_command(source, probe_command, output / 'DEVICE_PROBE.json')
    device = helpers.read(output / 'DEVICE_PROBE.json')
    require(device['denied_foreign_minors'] == [1, 2, 3, 4, 5, 6, 7], 'receiving_all_seven_foreign_denials')
    helpers.write(output / 'SOURCE_PROOF.json', dict(old_source=request['source_root'], old_inventory=pins,
        new_source=str(source), new_inventory=pins, policy_sha256=POLICY_SHA, source_edits=0))
    helpers.write(output / 'BOUNDARY.json', boundary)
    helpers.write(output / 'RETIRED.json', helpers.read(FAILED / 'RETIRED.json'))
    helpers.write(output / 'RESUME_ENTRYPOINT.json', helpers.verify_resume_entrypoint(source))
    prepared = deepcopy(request)
    prepared.update(status='EXACT_RETIRED_PRELOAD_RECOVERY_PREPARED', source_root=str(source),
        source_proof_sha256=helpers.sha(output / 'SOURCE_PROOF.json'), new_config=str(control / 'GUARD.json'),
        new_config_sha256=helpers.sha(control / 'GUARD.json'), cpu_sha256=helpers.sha(output / 'CPU_POLICY.log'),
        frozen_cpu_sha256=helpers.sha(output / 'CPU_FROZEN.log'), device_probe_sha256=helpers.sha(output / 'DEVICE_PROBE.json'),
        recovery_script_sha256=sha(__file__), failed_stage=str(FAILED), failed_stage_sha256=helpers.sha(FAILED / 'STAGED.json'))
    helpers.write(output / 'STAGED.json', prepared)
    helpers.write(output / 'RECOVERY_PREPARED.json', dict(status='PASS_PRE_NATIVE_RECOVERY_CPU_PROVENANCE', physical=3,
        saved=evidence, failed_admission=ref(FAILED / 'control/ADMISSION.json'), original_source_unchanged=True,
        R171_proposals_applied=False, model_calls=0, signals_sent=0, journal_writes=0,
        recovery_script_sha256=sha(__file__), observed_unix=time.time(),
        builder_line='[Builder] R179 lane3 exact pre-native recovery: eight receiving actual-source cases, frozen CPU suite, full saved optimizer/RNG/history and seven-foreign-device denial proof PASS; same walls/source/state; original guard unchanged.'))
    require(verify_failed(operator, helpers)[-1] == evidence, 'failed_saved_boundary_unchanged_after_receiving_proofs')
    print(json.dumps(dict(status='PREPARED_NOT_LAUNCHED', output=str(output), saved_cycle=evidence['cycle'])), flush=True)


def launch(output):
    operator, helpers = modules()
    gate = helpers.read(output / 'RECOVERY_PREPARED.json')
    request = helpers.read(output / 'STAGED.json')
    require(request['recovery_script_sha256'] == gate['recovery_script_sha256'] == sha(__file__), 'exact_tested_recovery_bytes')
    require(helpers.sha(request['new_config']) == request['new_config_sha256']
            and helpers.sha(output / 'CPU_POLICY.log') == request['cpu_sha256']
            and helpers.sha(output / 'CPU_FROZEN.log') == request['frozen_cpu_sha256']
            and helpers.sha(output / 'DEVICE_PROBE.json') == request['device_probe_sha256'], 'bound_actual_receiving_gates')
    source_proof = helpers.read(output / 'SOURCE_PROOF.json')
    require(helpers.sha(output / 'SOURCE_PROOF.json') == request['source_proof_sha256']
            and helpers.inventory_files(request['source_root']) == source_proof['new_inventory'], 'fresh_immutable_recovery_source')
    with open(FAILED / 'RECOVERY_SERIALIZATION.lock', 'a+b') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        evidence = verify_failed(operator, helpers)[-1]
        require(evidence == gate['saved'] and time.time() + 900 < WALL, 'same_saved_state_and_existing_wall')
        (output / 'RECOVERY_DISPATCH_ONCE').mkdir()
        command = [str(helpers.PYTHON), '-B', '-m', 'gpu.orch_r137_node4_containment', 'contained-supervise',
                   '--config', request['new_config']]
        with (output / 'control/SUPERVISOR.log').open('x') as log:
            process = subprocess.Popen(command, cwd=request['source_root'], stdin=subprocess.DEVNULL,
                stdout=log, stderr=subprocess.STDOUT, start_new_session=True,
                env=dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONPATH=request['source_root'], PYTHONDONTWRITEBYTECODE='1'))
        helpers.write(output / 'DISPATCHED.json', dict(supervisor_pid=process.pid, command=command, started_unix=time.time()))
        deadline = time.monotonic() + 120
        while not (output / 'control/LAUNCH.json').exists():
            if process.poll() is not None:
                helpers.write(output / 'RECOVERY_FAILED_BEFORE_NATIVE.json', dict(returncode=process.returncode,
                    observed_unix=time.time(), no_retry=True, original_report_preserved=True))
                raise ValueError('original_successor_admission_failed_no_retry')
            require(time.monotonic() < deadline, 'bounded_guard_startup_observation_no_native_replay')
            time.sleep(.5)
        result = operator.monitor(output, request, evidence, helpers, seconds=600)
        helpers.write(output / 'RECOVERY_MONITOR_RESULT.json', result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'launch'))
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    (prepare if arguments.action == 'prepare' else launch)(arguments.output)
