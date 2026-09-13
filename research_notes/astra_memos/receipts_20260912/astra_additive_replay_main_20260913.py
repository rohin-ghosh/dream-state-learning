"""Main-only additive launcher; import is inert and tests mock native operations."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time


BASE = Path('/tmp/astra_additive_replay_specs_20260913_attempt1')
DIAGNOSTICS = Path('/localhome/local-rohing/astra_diagnostics')
RUNNER = Path('/tmp/astra_additive_replay_run_20260913.py')
RUNNER_PIN = 'ca54e7e1971d89224bb8dec8f3518d0a6a73ec4d1abe6f29278bab335b1618a5'
CORE = Path('/tmp/astra_additive_replay_core_20260913.py')
CORE_PIN = 'b58e4c90e2abdd26648475c9fb1fe92e3bc3fef2fa7664ecaaa69fc93591076a'
TRAINER = Path('/tmp/astra_additive_replay_train_20260913.py')
TRAINER_PIN = '3f2e73ef69b12c8db211e1d3043e4559713e036ffe09571ab8bc4c5199a426a0'
TRAINER_TEST_PIN = '49e1fc9d266f89dfc69c1ea1c0112ed61e035190fd1ad2abfb8d7867828fdce1'
FROZEN_TRAINER_PIN = '7bbf165fcb4b8ae3a1180328bcd19f57382c30516daddc95fd61e8a2c749fad7'
REPAIR_RUNTIME = Path('/tmp/astra_own_replay_repair_run_20260913.py')
REPAIR_PIN = 'f1e3782378959f0c2552eaf9646a6b8827b876652a535d3248e38fe28371c4fe'
PROTOCOL_PIN = '724d5a6e1aea7dca4b0ae42aec6e2fd0252b98646f7c903432927263f2c391e9'
SOURCE = '/tmp/astra_level1_real_record_source_20260913_attempt1'
TINY_RECEIPT = Path('/tmp/astra_additive_replay_tiny_cpu_20260913_attempt1/receipt.json')
TINY_RECEIPT_PIN = 'ff2346a72f7e4fed9f4cdb51c90bb701c736557add56f0462f2b1e7ef2bc0b7d'
TINY_CHECKS = {'existing_output_writeonce_and_parent_immutable', 'fresh_optimizer_base_frozen_parent_load_and_exposures',
               'legacy_memory_only_parity', 'nonfinite_loss_and_gradient_reject_no_done',
               'unequal_length_separate_masked_mean_ce_gradient_sum'}
RESERVATIONS = Path('/tmp/astra_level1_next_batch_20260913.py')
RESERVATIONS_PIN = '03ac5f43f19e3a54ed57c7362085ff2d96d7a06c2d9f7fc354c5789e84f8f6c2'
PRECHECKS = Path('/tmp/astra_level1_roster_20260913_attempt1/prechecks.json')
PRECHECKS_PIN = '71e8eaa0c326ddef4414539684d20315e3752c48ce425a280438100e32815929'
GPUS = {0: 'GPU-c70cba10-6ab6-a287-e2db-51dccd617ab0',
        1: 'GPU-e7a322fc-fe84-919f-7534-cdfefb6ce1e4',
        2: 'GPU-d2db2a6a-a308-1782-bf41-e41411d8dc05'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    checksum = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            checksum.update(block)
    return checksum.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, sort_keys=True, allow_nan=False)
        stream.write('\n')


def load(name, path, expected):
    require(digest(path) == expected, 'module byte pin differs: '+str(path))
    specification = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


def root_for(seed):
    require(type(seed) is int and seed in GPUS, 'strict original seed0/1/2 required')
    return DIAGNOSTICS / f'additive_replay_seed{seed}_20260913_attempt1'


def runtime(checksum):
    require(checksum == RUNNER_PIN, 'final additive runner pin required')
    return load('additive_main_runtime', RUNNER, RUNNER_PIN)


def tiny_gate(receipt_path):
    path = Path(receipt_path)
    require(path.is_absolute() and not path.is_symlink() and digest(path) == TINY_RECEIPT_PIN, 'accepted tiny CPU receipt byte pin required')
    receipt = read(path)
    require(receipt['schema'] == 'astra_additive_replay_tiny_cpu_receipt_v1' and receipt['status'] == 'PASS' and
            receipt['fixture_only'] is True and receipt['native_scientific_evidence'] is False and
            receipt['trainer_sha256'] == TRAINER_PIN and receipt['tests_sha256'] == TRAINER_TEST_PIN and
            receipt['frozen_trainer_sha256'] == FROZEN_TRAINER_PIN and receipt['protocol_sha256'] == PROTOCOL_PIN and
            set(receipt['checks']) == TINY_CHECKS and all(value is True for value in receipt['checks'].values()),
            'tiny CPU acceptance/config/checks differ')
    return dict(path=str(path), sha256=TINY_RECEIPT_PIN, trainer_sha256=TRAINER_PIN, tests_sha256=TRAINER_TEST_PIN,
                fixture_only=True, native_scientific_evidence=False)


def binding(root):
    collection = Path(str(root)+'_collected') / 'collection.json'
    return dict(root=str(root), plan_sha256=digest(root/'plan.json'), completion_sha256=digest(root/'capture_complete.json'),
                collection=dict(path=str(collection), sha256=digest(collection)), scores_sha256=digest(collection.parent/'scores.json'))


def specs(checksum, core_checksum=CORE_PIN, receipt_path=TINY_RECEIPT):
    gate = tiny_gate(receipt_path)
    candidate = runtime(checksum)
    require(core_checksum == CORE_PIN == candidate.CORE_PIN and digest(CORE) == CORE_PIN and
            digest(TRAINER) == TRAINER_PIN == candidate.TRAINER_PIN and
            digest(REPAIR_RUNTIME) == REPAIR_PIN == candidate.REPAIR_PIN and
            digest(BASE/'protocol.md') == PROTOCOL_PIN == candidate.PROTOCOL_PIN, 'final source/protocol pins differ')
    pending = []
    for seed, uuid in GPUS.items():
        old_root = DIAGNOSTICS / f'own_replay_repair_seed{seed}_20260913_attempt1'
        inherited = read(old_root/'spec.json')
        require(inherited['runner_sha256'] == REPAIR_PIN and inherited['seed'] == inherited['fit_seed'] == seed,
                'old original seed/runtime differs')
        spec = dict(runner_sha256=checksum, repair_runtime=dict(path=str(REPAIR_RUNTIME), sha256=REPAIR_PIN),
                    core=dict(path=str(CORE), sha256=CORE_PIN), trainer=dict(path=str(TRAINER), sha256=TRAINER_PIN),
                    protocol=dict(path=str(BASE/'protocol.md'), sha256=PROTOCOL_PIN), repair_history=binding(old_root),
                    seed=seed, fit_seed=seed, gpu_index=seed, gpu_uuid=uuid,
                    expected_boot_id=inherited['expected_boot_id'], lease_end=inherited['lease_end'])
        candidate.validate_spec(spec)
        candidate.allocation(dict(specification=spec))
        for suffix in ('.json', '_gate.json', '_prepared.json'):
            require(not (BASE/f'seed{seed}{suffix}').exists(), 'spec/gate/prepare output already exists')
        require(not root_for(seed).exists() and not Path(str(root_for(seed))+'.launcher').exists() and
                not Path(str(root_for(seed))+'_collected').exists(), 'fresh additive root/custody required')
        pending.append((seed, spec))
    results = []
    for seed, spec in pending:
        path = BASE/f'seed{seed}.json'
        write(path, spec)
        record = dict(seed=seed, spec_sha256=digest(path), tiny_cpu_receipt=gate,
                      custodian_sha256=digest(__file__), runner_sha256=checksum)
        write(BASE/f'seed{seed}_gate.json', record)
        results.append(record)
        print(json.dumps(record), flush=True)
    return results


def checked_spec(seed, checksum, receipt_path):
    root_for(seed)
    gate = tiny_gate(receipt_path)
    candidate = runtime(checksum)
    spec_path = BASE/f'seed{seed}.json'
    spec = read(spec_path)
    record = read(BASE/f'seed{seed}_gate.json')
    require(record == dict(seed=seed, spec_sha256=digest(spec_path), tiny_cpu_receipt=gate,
                           custodian_sha256=digest(__file__), runner_sha256=checksum), 'launcher/spec/CPU gate custody differs')
    candidate.validate_spec(spec)
    require(spec['seed'] == spec['fit_seed'] == seed and spec['gpu_index'] == seed and spec['gpu_uuid'] == GPUS[seed] and
            spec['repair_history']['root'] == str(DIAGNOSTICS/f'own_replay_repair_seed{seed}_20260913_attempt1'),
            'fixed seed/allocation/history root differs')
    return candidate, spec, record


def prepare(seed, checksum, receipt_path=TINY_RECEIPT):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'prepare requires explicitly empty CVD')
    candidate, spec, gate = checked_spec(seed, checksum, receipt_path)
    path = BASE/f'seed{seed}_prepared.json'
    require(not path.exists(), 'prepare already recorded')
    candidate.allocation(dict(specification=spec))
    result = candidate.prepare(str(root_for(seed)), str(BASE/f'seed{seed}.json'), gate['spec_sha256'], allow_native=True)
    require(result['status'] == 'NATIVE_CPU_PREPARED_NOT_LAUNCHED', 'native CPU preparation incomplete')
    result = dict(result, launcher_gate=gate)
    write(path, result)
    print(json.dumps(result), flush=True)
    return result


def checked_prepared(seed, checksum, receipt_path):
    candidate, spec, gate = checked_spec(seed, checksum, receipt_path)
    prepared = read(BASE/f'seed{seed}_prepared.json')
    root = root_for(seed)
    require(prepared['status'] == 'NATIVE_CPU_PREPARED_NOT_LAUNCHED' and prepared['launcher_gate'] == gate and
            digest(root/'plan.json') == prepared['plan_sha256'], 'prepared plan/gate pin differs')
    plan = read(root/'plan.json')
    require(plan['root'] == str(root) and plan['specification'] == spec and plan['status'] == 'READY' and
            plan['gpu_index'] == seed and plan['gpu_uuid'] == GPUS[seed], 'prepared identity/allocation differs')
    return candidate, prepared, plan


def launch(seed, checksum, receipt_path=TINY_RECEIPT):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'launcher requires explicitly empty CVD')
    candidate, prepared, plan = checked_prepared(seed, checksum, receipt_path)
    candidate.runtime().offline()
    batch = load('additive_main_reservations', RESERVATIONS, RESERVATIONS_PIN)
    require(digest(PRECHECKS) == PRECHECKS_PIN, 'roster byte pin differs')
    config = read(PRECHECKS)['node2']
    root = root_for(seed)
    _, verified_plan, bound = candidate.verify(str(root), prepared['plan_sha256'])
    require(verified_plan == plan and not (root/'controller_started.json').exists() and
            not Path(str(root)+'_collected').exists(), 'verified plan changed or controller/collection already started')
    candidate.allocation(plan)
    require(bound['probe'].gpu_state(plan) is True, 'GPU not idle/owned before reservation')
    require(config['host_boot_id'] == plan['specification']['expected_boot_id'], 'roster/spec boot differs')
    config = dict(config, gpus={str(seed): GPUS[seed]})
    claim = Path(str(root)+'.launcher')
    claim.mkdir()
    process = None
    try:
        write(claim/'precheck.json', batch.reservations(config, seed, GPUS[seed]))
        candidate.allocation(plan)
        require(bound['probe'].gpu_state(plan) is True, 'GPU changed after reservation check')
        command = [sys.executable, '-B', str(Path(__file__).resolve()), 'hold', '--seed', str(seed),
                   '--runner-sha256', checksum, '--tiny-cpu-receipt', str(receipt_path)]
        with (claim/'stdout.log').open('xb') as output:
            process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT,
                      env=dict(os.environ, CUDA_VISIBLE_DEVICES=GPUS[seed], PYTHONPATH=SOURCE), start_new_session=True)
        result = dict(status='LAUNCHED_NOT_RESULT', seed=seed, root=str(root), pid=process.pid,
                      identity=batch.identity(Path('/proc')/str(process.pid)), started_unix=time.time(), gpu_index=seed,
                      gpu_uuid=GPUS[seed], plan_sha256=prepared['plan_sha256'], command=command,
                      custodian_sha256=digest(__file__), runner_sha256=checksum,
                      tiny_cpu_receipt=prepared['launcher_gate']['tiny_cpu_receipt'], automatic_once_collection=True)
        write(claim/'launched.json', result)
        print(json.dumps(result), flush=True)
        return result
    except BaseException as error:
        write(claim/'failure.json', dict(error=repr(error), holder_may_be_running=process is not None))
        raise


def hold(seed, checksum, receipt_path=TINY_RECEIPT):
    root = root_for(seed)
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == GPUS[seed], 'holder requires the exact UUID CVD')
    candidate, prepared, plan = checked_prepared(seed, checksum, receipt_path)
    claim = Path(str(root)+'.launcher')
    require(claim.is_dir() and not (root/'controller_started.json').exists() and
            not Path(str(root)+'_collected').exists(), 'holder requires fresh claimed controller/collection')
    write(claim/'holder_started.json', dict(pid=os.getpid(), started_unix=time.time(),
          plan_sha256=prepared['plan_sha256'], tiny_cpu_receipt=prepared['launcher_gate']['tiny_cpu_receipt'],
          custodian_sha256=digest(__file__), runner_sha256=checksum))
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONPATH=SOURCE)
    process = collector = None
    try:
        candidate.allocation(plan)
        command = [sys.executable, '-B', str(RUNNER), 'controller', '--root', str(root),
                   '--plan-sha256', prepared['plan_sha256'], '--allow-gpu']
        process = subprocess.Popen(command, stdin=subprocess.DEVNULL, env=environment, start_new_session=True)
        write(claim/'controller.json', dict(pid=process.pid, pgid=process.pid, command=command, started_unix=time.time()))
        result = process.wait()
        write(claim/'controller_exit.json', dict(returncode=result, completed_unix=time.time()))
        if result == 0:
            completion = digest(root/'capture_complete.json')
            write(claim/'collection_started.json', dict(completion_sha256=completion, plan_sha256=prepared['plan_sha256'],
                                                        started_unix=time.time()))
            command = [sys.executable, '-B', str(RUNNER), 'collect', '--root', str(root),
                       '--plan-sha256', prepared['plan_sha256'], '--completion-sha256', completion, '--out', str(root)+'_collected']
            collector = subprocess.Popen(command, stdin=subprocess.DEVNULL, env=environment, start_new_session=True)
            write(claim/'collector.json', dict(pid=collector.pid, pgid=collector.pid, command=command, started_unix=time.time()))
            result = collector.wait()
            write(claim/'collector_exit.json', dict(returncode=result, completed_unix=time.time()))
        write(claim/'exit.json', dict(returncode=result, completed_unix=time.time()))
    except BaseException as error:
        write(claim/'holder_failure.json', dict(error=repr(error), controller_may_be_running=process is not None,
                                               collector_may_be_running=collector is not None))
        raise
    return result


if __name__ == '__main__':
    sys.dont_write_bytecode = True
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('specs', 'prepare', 'launch', 'hold'))
    parser.add_argument('--seed', type=int, choices=(0, 1, 2))
    parser.add_argument('--runner-sha256', required=True)
    parser.add_argument('--core-sha256', default=CORE_PIN)
    parser.add_argument('--tiny-cpu-receipt', default=str(TINY_RECEIPT))
    options = parser.parse_args()
    if options.action == 'specs':
        specs(options.runner_sha256, options.core_sha256, options.tiny_cpu_receipt)
    else:
        if options.seed is None:
            parser.error('--seed is required for prepare/launch/hold')
        result = dict(prepare=prepare, launch=launch, hold=hold)[options.action](options.seed, options.runner_sha256, options.tiny_cpu_receipt)
        if options.action == 'hold':
            sys.exit(result)
