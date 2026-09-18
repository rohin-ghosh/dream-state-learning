"""Bounded R188 kernel0 rollback or unchanged raw1 pre-native readmission."""

import argparse
from copy import deepcopy
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid


HOME = Path(__file__).resolve().parent
BUNDLE = Path('/localhome/local-rohing/orch_r179_node4_r181journal_20260917t2220z')
ROOT = Path('/localhome/local-rohing/orch_r188_node4_20260917t2315z')
OPERATOR_SHA = '3bebf07c0eb71b8dfaef71511cc01662973da335a8e781bdc1034cb6742a3874'
WALL = 1789754400


def modules():
    spec = importlib.util.spec_from_file_location('r188_node4_original', BUNDLE / 'node4_rollout.py')
    operator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(operator)
    helpers = operator.helper_module(BUNDLE)
    helpers.require(helpers.sha(BUNDLE / 'node4_rollout.py') == OPERATOR_SHA, 'exact_existing_operator')
    helpers.current_node('a40r')
    return operator, helpers


def cpu(source, command, log):
    with log.open('x') as output:
        result = subprocess.run(command, cwd=source, env=dict(os.environ, CUDA_VISIBLE_DEVICES='',
            PYTHONPATH=str(source), PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1'),
            stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT, timeout=240)
    if result.returncode:
        raise ValueError('receiving_CPU_failure:' + str(log))


def state_evidence(physical, helpers):
    require = helpers.require
    prior = BUNDLE / f'lane{physical}'
    request = helpers.read(prior / 'STAGED.json')
    require(physical in (0, 1) and request['physical'] == physical, 'only_R188_kernel0_or_raw1')
    require(helpers.sha(request['new_config']) == request['new_config_sha256'], 'original_staged_guard')
    config, plan, original = helpers.originals(Path(request['new_config']))
    require(plan['hard_end_unix'] == WALL and plan['rehearsal_presentations'] == 0
        and plan['new_presentations'] == 16, 'existing_R181_same_wall')
    root = Path(plan['root'])
    records = helpers.records(root)
    documents = [helpers.read(path) for path in records]
    last_complete = next(record for record in reversed(documents) if record['kind'] == 'SLEEP_COMPLETE')
    checkpoint_path = root / 'checkpoints' / f"sleep_{last_complete['document']['cycle']:06d}" / 'COMMIT.json'
    checkpoint = helpers.read(checkpoint_path)
    if physical == 0:
        stop = helpers.read(ROOT / 'kernel0/STOPPED.json')
        require(stop['physical'] == 0 and stop['exact_inflight_continuation'] is False, 'R188_actual_stop')
        archived = helpers.read(ROOT / 'kernel0/FULL_OLD_ROOT_MANIFEST.json')
        for path in records:
            require(helpers.sha(path) == archived[str(path.relative_to(root))], 'preserved_full_journal_suffix')
        pending = next(record for record in reversed(documents) if record['kind'] == 'SLEEP_REQUEST')
        require(pending['index'] > last_complete['index'] and last_complete['document']['cycle'] == 40,
            'only_saved40_pending41')
        updates = [record['document']['optimizer_step'] for record in documents
            if record['index'] > last_complete['index'] and record['kind'] == 'UPDATE']
        require(updates == list(range(4208, 4208 + len(updates))), 'exact_discarded_logged_update_range')
        envelope = pending['document']['resume_state']
        binding = dict(schema='R188_KERNEL0_SAVED40_ROLLBACK_V1', archive_root=str(ROOT / 'kernel0'),
            saved_cycle=40, saved_optimizer_steps=4207, uncertain_inflight_update=True,
            discarded_logged_updates=len(updates), discarded_steps=[updates[0], updates[-1]],
            archive_receipt_sha256=helpers.sha(ROOT / 'kernel0/ARCHIVED.json'),
            stop_receipt_sha256=helpers.sha(ROOT / 'kernel0/STOPPED.json'),
            checkpoint_path=str(checkpoint_path), checkpoint_sha256=helpers.sha(checkpoint_path),
            pending_state_sha256=envelope['sha256'], rows=len(envelope['state']['rows']),
            sleep_frontier=envelope['state']['sleep_frontier'], head_file=records[-1].name,
            head_file_sha256=helpers.sha(records[-1]))
    else:
        require(not (prior / 'LOADED_RECEIPT.json').exists()
            and not (prior / 'control/LAUNCH.json').exists(), 'raw1_failure_before_any_native')
        admission = helpers.read(prior / 'control/ADMISSION.json')
        require(admission['clear'] is False and admission['scanner_euid'] == 0
            and admission['blocking_reasons'] == ['process_identity_drift:1635982', 'process_identity_drift:1635983'],
            'exact_preserved_raw1_pre_native_failure')
        require((prior / 'control/SUPERVISOR.log').read_text().rstrip().endswith(
            'ValueError: unchanged_global_exclusive_admission'), 'raw1_actual_guard_failure')
        dispatch = helpers.read(prior / 'DISPATCHED.json')
        require(not Path('/proc', str(dispatch['supervisor_pid'])).exists(), 'failed_raw1_supervisor_gone')
        boundary = helpers.read(prior / 'BOUNDARY.json')
        require(last_complete['sha256'] == boundary['saved']['record_sha256']
            and documents[-1]['sha256'] == last_complete['sha256'], 'raw1_exact_saved42_head_no_replay')
        binding = None
    for owner in request['processes'].values():
        process = Path('/proc', str(owner['pid']))
        if process.exists():
            require(helpers.identity(owner['pid'])['start_ticks'] != owner['start_ticks'], 'old_owner_not_alive')
    return request, config, plan, checkpoint, binding, dict(
        physical=physical, cycle=last_complete['document']['cycle'], checkpoint_path=str(checkpoint_path),
        checkpoint_sha256=helpers.sha(checkpoint_path), adapter_state_sha256=checkpoint['adapter_state_sha256'],
        optimizer_steps=checkpoint['optimizer_steps'], old_head_index=documents[-1]['index'],
        old_head_sha256=documents[-1]['sha256'], root=str(root))


def prepare(physical):
    operator, helpers = modules()
    require = helpers.require
    request, previous, plan, checkpoint, binding, saved = state_evidence(physical, helpers)
    output = ROOT / f'recovery{physical}'
    require(not output.exists(), 'new_single_recovery_output')
    output.mkdir()
    source, control = output / 'source', output / 'control'
    shutil.copytree(request['source_root'], source)
    control.mkdir()
    old_pins = helpers.inventory_files(request['source_root'])
    require(helpers.inventory_files(source) == old_pins, 'exact_prepared_R181_cache_R179_source_copy')
    if physical == 0:
        import r188_sleep_rollback as rollback
        native = source / 'gpu/orch_r125_continual_native.py'
        native.write_text(rollback.patch_native(native.read_text()))
        shutil.copyfile(HOME / 'r188_sleep_rollback.py', source / 'gpu/orch_r188_node4_sleep_rollback.py')
    new_plan = helpers.relocated_plan(plan, source)
    if binding is not None:
        new_plan['r188_sleep_rollback'] = binding
    helpers.write(control / 'PLAN.json', new_plan)
    allocation = helpers.read(previous['allocation_path'])
    allocation['plan_sha256'] = helpers.sha(control / 'PLAN.json')
    helpers.write(control / 'ALLOCATION.json', allocation)
    config = deepcopy(previous)
    config.update(attempt_dir=str(control), plan_path=str(control / 'PLAN.json'),
        plan_sha256=helpers.sha(control / 'PLAN.json'), allocation_path=str(control / 'ALLOCATION.json'),
        allocation_sha256=helpers.sha(control / 'ALLOCATION.json'),
        source_pins={name: digest for name, digest in helpers.inventory_files(source).items() if name.endswith('.py')})
    config['device_containment']['unit'] = 'orch-r136-native-' + uuid.uuid4().hex
    helpers.write(control / 'GUARD.json', config)
    cpu(source, [str(helpers.PYTHON), '-B', '-c',
        'from gpu import orch_r125_continual_guard as guard; guard.validate(' + repr(str(control / 'GUARD.json')) + ')'],
        output / 'CPU_GUARD.log')
    cpu(source, [str(helpers.PYTHON), '-B', '-m', 'unittest', 'tests.test_orch_r124_train_history',
        'tests.test_orch_r125_continual_stream', 'tests.test_orch_r125_stream_journal'], output / 'CPU_FROZEN.log')
    if physical == 0:
        cpu(source, [str(helpers.PYTHON), '-B', str(HOME / 'test_r188_sleep_rollback.py')], output / 'CPU_R188.log')
    probe = deepcopy(config)
    probe['device_containment']['unit'] = 'orch-r136-native-' + uuid.uuid4().hex
    helpers.write(output / 'PROBE_GUARD.json', probe)
    sys.path.insert(0, str(source))
    from gpu import orch_r179_node4_legacy_containment as containment
    command = [str(helpers.PYTHON), '-B', '-m', 'gpu.orch_r179_node4_legacy_containment',
        'probe', '--config', str(output / 'PROBE_GUARD.json')]
    policy = probe['device_containment']
    cpu(source, containment.device_containment_command(physical, policy['minor'], 2524, 2524,
        policy['unit'], source, command, 120), output / 'DEVICE_PROBE.json')
    proof = helpers.read(output / 'DEVICE_PROBE.json')
    require(len(proof['denied_foreign_minors']) == 7, 'all_seven_foreign_minors_denied')
    require(state_evidence(physical, helpers)[-1] == saved, 'same_retired_history_before_receiving_ready')
    helpers.write(output / 'READY.json', dict(physical=physical, saved=saved, plan=new_plan,
        source_inventory=helpers.inventory_files(source), guard_sha256=helpers.sha(control / 'GUARD.json'),
        operator_sha256=helpers.sha(__file__), observed_unix=time.time(),
        builder_line='[Builder] R188 same-life recovery CPU/provenance and strict receiving device proof PASS; no lease, guard, judge or other-life change.',
        exact_inflight_continuation=False if physical == 0 else None))
    print(json.dumps(dict(status='READY_NO_LAUNCH', physical=physical, output=str(output))), flush=True)


def launch(physical):
    operator, helpers = modules()
    require = helpers.require
    output = ROOT / f'recovery{physical}'
    ready = helpers.read(output / 'READY.json')
    require(helpers.sha(__file__) == ready['operator_sha256'], 'tested_recovery_operator')
    require(state_evidence(physical, helpers)[-1] == ready['saved'], 'unchanged_retired_state')
    require(helpers.inventory_files(output / 'source') == ready['source_inventory']
        and helpers.sha(output / 'control/GUARD.json') == ready['guard_sha256'], 'immutable_receiving_source_guard')
    with (ROOT / f'RECOVERY_{physical}.lock').open('a+b') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        (output / 'DISPATCH_ONCE').mkdir()
        command = [str(helpers.PYTHON), '-B', '-m', 'gpu.orch_r179_node4_legacy_containment',
            'contained-supervise', '--config', str(output / 'control/GUARD.json')]
        with (output / 'control/SUPERVISOR.log').open('x') as log:
            process = subprocess.Popen(command, cwd=output / 'source', env=dict(os.environ,
                CUDA_VISIBLE_DEVICES='', PYTHONPATH=str(output / 'source'), PYTHONDONTWRITEBYTECODE='1'),
                stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        helpers.write(output / 'DISPATCHED.json', dict(pid=process.pid, command=command, observed_unix=time.time()))
        cursor = ready['saved']['old_head_index']
        loaded = False
        deadline = min(time.time() + 900, WALL - 30)
        while time.time() < deadline:
            require(process.poll() is None, 'original_admission_or_native_failed_no_retry')
            for path in helpers.records(ready['plan']['root']):
                if int(path.stem) <= cursor:
                    continue
                record = helpers.read(path)
                require(record['sha256'] == helpers.digest({key: value for key, value in record.items() if key != 'sha256'}),
                    'actual_record_hash')
                cursor = record['index']
                if record['kind'] == 'LOADED' and not loaded:
                    document = record['document']
                    require(document['resume'] is True and document['optimizer_steps'] == ready['saved']['optimizer_steps']
                        and document['adapter_sha256'] == ready['saved']['adapter_state_sha256'], 'actual_last_COMPLETE_model_restored')
                    actor = helpers.identity(document['pid'])
                    require(actor['cwd'] == str(output / 'source') and actor['argv'][-1] == str(output / 'control/GUARD.json'),
                        'actual_new_source_and_guard')
                    admission = helpers.read(output / 'control/ADMISSION.json')
                    require(admission['clear'] is True and not admission['blocking_reasons']
                        and admission['scanner_euid'] == 0, 'unchanged_final_clear_admission')
                    confinement = helpers.read(output / 'control/CONTAINMENT_VERIFIED.json')
                    require(len(confinement['denied_foreign_minors']) == 7, 'actual_native_strict_confinement')
                    helpers.write(output / 'LOADED_RECEIPT.json', dict(status='R188_SAVED_MODEL_LOADED',
                        physical=physical, actor=actor, saved=ready['saved'], record_index=record['index'],
                        record_sha256=record['sha256'], observed_unix=time.time(),
                        exact_inflight_continuation=False if physical == 0 else None))
                    loaded = True
                if loaded and record['kind'] in ('SLEEP_RECIPE', 'SLEEP_COMPLETE', 'CONTEXT_RETAINED'):
                    helpers.write(output / f"ACTUAL_{record['kind']}_{record['index']}.json", dict(
                        record_index=record['index'], record_sha256=record['sha256'], document=record['document']
                        if record['kind'] == 'SLEEP_RECIPE' else dict(cycle=record['document'].get('cycle')),
                        observed_unix=time.time()))
                if loaded and record['kind'] == ('SLEEP_COMPLETE' if physical == 0 else 'COMMITTED'):
                    helpers.write(output / 'RECOVERY_COMPLETE.json', dict(physical=physical, record_index=record['index'],
                        record_sha256=record['sha256'], observed_unix=time.time(), exact_inflight_continuation=False))
                    return
            time.sleep(1)
        require(loaded, 'bounded_load_observation_expired')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'launch'))
    parser.add_argument('--physical', type=int, choices=(0, 1), required=True)
    arguments = parser.parse_args()
    (prepare if arguments.action == 'prepare' else launch)(arguments.physical)
