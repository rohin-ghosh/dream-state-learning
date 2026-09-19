"""Bounded R155 successor: new confinement, preserved counters, no gap replay."""

import argparse
from contextlib import ExitStack
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

from gpu import orch_r155_kernel_parser_activate as prior


PREDECESSOR = prior.BASE / 'orch_r155_kernel_parser_20260917t0225z_attempt3'
PHASE_SECONDS = 1500
PHASES = 2
service, campaign, smoke = prior.modules()


def source_pins():
    pins = prior.source_pins()
    source = Path(__file__).resolve().parents[1]
    for path in (Path(__file__).resolve(), source / 'tests/test_orch_r158_kernel_execution.py'):
        pins[str(path)] = service.sha(service.read(path, 1048576))
    return pins


def attest(directory, cpu_log, exit_code):
    raw = service.read(cpu_log, 1048576)
    service.require(exit_code == 0 and re.search(rb'\b[1-9][0-9]* passed\b', raw)
                    and not re.search(rb'\b[1-9][0-9]* (failed|errors?)\b', raw), 'passing_CPU_gate_required')
    receipt = dict(schema='R158_CPU_V1', status='PASS_NOT_GPU_ADMITTED', source_pins=source_pins(),
                   cpu_log=str(cpu_log), cpu_log_sha256=service.sha(raw), exit_code=0,
                   observed_unix=time.time())
    service.store(directory / 'CPU_GATE.json', service.encoded(receipt))
    return receipt


def terminal_counters(config, state, terminal):
    campaign.stopped(terminal, state)
    service.require(state['config_sha256'] == service.sha(service.encoded(config)), 'terminal_config_binding')
    service.require(state['next_index'] >= config['start_index'], 'no_cursor_regression')
    for key, budget in campaign.BUDGETS.items():
        service.require(state[key] <= config[budget], 'bounded_prior_' + key)
    return {key: state[key] for key in campaign.COUNTERS}


def predecessor():
    _, _, ancestor_refs, locks = prior.original_bundle()
    refs = dict(ancestor_refs)

    def document(path):
        raw = service.read(path, 65536)
        refs[str(path)] = service.sha(raw)
        return service.cpu.read_document(raw)

    cpu_gate = document(PREDECESSOR / 'CPU_GATE.json')
    for path, checksum in cpu_gate['source_pins'].items():
        service.require(service.sha(service.read(path, 1048576)) == checksum, 'prior_source_unchanged')
    finished = document(PREDECESSOR / 'FINISHED.json')
    service.require(finished.get('status') == 'WORKERS_EXITED_NO_AUTOMATIC_RETRY'
                    and finished.get('exit_codes') == [0, 0], 'both_prior_workers_finished')
    activation = document(PREDECESSOR / 'ACTIVATION.json')
    intent = document(PREDECESSOR / 'HANDOFF_INTENT.json')
    for pid in activation['pids'] + [intent['pid']]:
        service.require(type(pid) is int and not Path('/proc', str(pid)).exists(), 'prior_process_gone')
    lanes = {}
    for lane in prior.ROOTS:
        directory = PREDECESSOR / f'lane{lane}'
        config = document(directory / 'CONFIG.json')
        state = document(directory / 'service/STATE.json')
        terminal = document(directory / 'TERMINAL.json')
        service.base_config(config)
        service.require(config['root'] == prior.ROOTS[lane] and config.get('code_policy') == prior.POLICY,
                        'exact_prior_target_and_policy')
        terminal_counters(config, state, terminal)
        service.require(state['calls'] == 0 and not list((directory / 'service').glob('*/INTENT.json')),
                        'nonzero_prior_intent_requires_reconciliation')
        service.require(service.read(directory / 'service/CONFIG.json', 65536) == service.encoded(config)
                        and service.read(directory / 'spool/SERVICE_OWNER.json', 65536) == service.encoded(config),
                        'prior_namespaces_bound')
        for path, checksum in config['source_closure'].items():
            service.require(service.sha(service.read(path, 1048576)) == checksum, 'prior_service_source_unchanged')
        service.require(service.sha(service.read(config['lease_receipt_path'], 65536)) == config['lease_receipt_sha256']
                        and campaign.lease_wall(config) > time.time() + 3600, 'original_lease_reserve')
        service.require(service.sha(service.read(Path(config['runtime_root']) / 'MANIFEST.json', 4194304))
                        == config['runtime_manifest_sha256'], 'same_runtime_manifest')
        campaign.cursor(config, state)
        lanes[lane] = dict(config=config, state=state)
        locks.append(directory / 'service/SERVICE.lock')
    return lanes, refs, locks


def refresh_gate(directory, config):
    runtime = Path(config['runtime_root'])
    runtime_hash = service.executor.validate_runtime(runtime)
    service.require(runtime_hash == config['runtime_manifest_sha256'], 'same_runtime_before_probe')
    identity = service.executor.policy_identity(runtime, runtime_hash, service.executor.device_identity())
    with service.lock_file(service.executor.LOCK_PATH) as descriptor:
        wall = min(campaign.lease_wall(config), time.time() + 3300)
        admission = smoke.locked_census(descriptor, 'R158_NEW_ASSIGNED_EXECUTOR_GATE',
                                       Path(config['lease_receipt_path']), wall)
        path = directory / 'PROBE_ADMISSION.json'
        service.store(path, service.encoded(admission))
        service.executor.validate_admission(path, time.time())
        smoke.write_lock(descriptor, dict(result_status='DISPATCH_INCOMPLETE',
            last_finished_unix=time.time(), owner=str(directory)))
        with prior.probe_umask():
            result = service.executor.run_trusted_probes(directory / 'probes', runtime, path)
        service.store(directory / 'PROBE_RESULT.json', service.encoded(result))
        service.require(result.get('passed') is True and result.get('checks') == 26,
                        'all_26_real_confinement_checks_required')
        gate_path = directory / 'probes/GATE.json'
        gate_sha = service.executor.validate_gate(gate_path, identity, time.time())
        smoke.write_lock(descriptor, dict(result_status='TRUSTED_PROBES_PASSED',
            last_finished_unix=time.time(), gate_sha256=gate_sha, owner=str(directory)))
    return str(gate_path)


def seed(directory, base, previous, *, frontier=False):
    service.common.mkdir_durable(directory)
    config = {key: base[key] for key in service.BASE_KEYS}
    config.update(code_policy=prior.POLICY, source_root=str(Path(__file__).resolve().parents[1]),
                  state=str(directory / 'service'), spool=str(directory / 'spool'),
                  wall_seconds=PHASE_SECONDS)
    if frontier:
        files = [path for path in (Path(config['root']) / 'stream/records').iterdir()
                 if re.fullmatch(r'[0-9]{20}\.json', path.name)]
        service.require(0 < len(files) <= 100000, 'bounded_journal_frontier')
        raw, prefix = service.record(dict(root=config['root']), int(max(files, key=lambda path: path.name).stem))
        config['start_index'] = prior.future_start(prefix, previous['next_index'])
        service.store(directory / 'FUTURE_ORIGIN.json', service.encoded(dict(
            observed_unix=time.time(), previous_next_index=previous['next_index'],
            start_index=config['start_index'], prefix_sha256=service.sha(raw),
            prefix_chain_sha256=prefix['sha256'], prefix_kind=prefix['kind'],
            historical_gap_not_dispatched=True)))
    config = service.pin_config(config)
    service.validate_config(config)
    gate, _ = service.limits(config, time.time())
    service.require(gate['expires_unix'] > time.time() + PHASE_SECONDS + 180, 'gate_covers_whole_next_phase')
    service.store(directory / 'CONFIG.json', service.encoded(config))
    with service.namespace(config) as (namespace, state):
        state = prior.inherit_counters(state, previous)
        if not frontier:
            state.update(next_index=previous['next_index'], previous_sha256=previous['previous_sha256'])
            campaign.cursor(config, state)
        service.common.save_state(namespace, state)
        service.store(directory / 'INITIAL_STATE.json', service.encoded(state))
    return config


def renew_allowed(config, state, terminal):
    terminal_counters(config, state, terminal)
    return state['reason'] == 'WALL_LIMIT' and state['calls'] < config['max_calls']


def worker(config_path):
    lane_directory = config_path.parent.parent
    try:
        for number in range(1, PHASES + 1):
            config = service.cpu.read_document(service.read(config_path, 65536))
            result = prior.worker(config_path)
            state = service.cpu.read_document(service.read(Path(config['state']) / 'STATE.json', 65536))
            service.store(lane_directory / f'PHASE_{number:02d}_FINISHED.json', service.encoded(result))
            if not renew_allowed(config, state, result) or number == PHASES:
                break
            next_directory = lane_directory / f'phase_{number + 1:02d}'
            seed(next_directory, config, state)
            config_path = next_directory / 'CONFIG.json'
        service.store(lane_directory / 'FINISHED.json', service.encoded(result))
        return result
    except BaseException as error:
        service.store(lane_directory / 'FAILED_NO_RETRY.json', service.encoded(dict(
            error_type=type(error).__name__, error=str(error), observed_unix=time.time())))
        raise


def activate(directory):
    gate = service.cpu.read_document(service.read(directory / 'CPU_GATE.json', 65536))
    service.require(gate.get('schema') == 'R158_CPU_V1' and gate.get('exit_code') == 0
                    and gate['source_pins'] == source_pins()
                    and service.sha(service.read(gate['cpu_log'], 1048576)) == gate['cpu_log_sha256']
                    and 0 <= time.time() - gate['observed_unix'] < 1800, 'fresh_bound_CPU_gate')
    lanes, refs, locks = predecessor()
    children = prior.child_identities()
    processes = []
    with ExitStack() as stack:
        descriptors = [stack.enter_context(service.lock_file(path)) for path in locks]
        inventory = prior.process_inventory()
        service.require(not inventory['unreadable_pids'] and not inventory['scanners'], 'exclusive_scanner_custody')
        service.require(predecessor()[1] == refs, 'predecessor_stable_under_locks')
        service.store(directory / 'HANDOFF_INTENT.json', service.encoded(dict(
            observed_unix=time.time(), pid=os.getpid(), predecessor_refs=refs,
            states={str(lane): value['state'] for lane, value in lanes.items()}, children=children)))
        try:
            gate_path = refresh_gate(directory, lanes[0]['config'])
            service.require(prior.child_identities() == children and predecessor()[1] == refs
                            and source_pins() == gate['source_pins'], 'post_probe_pins_and_children_unchanged')
            configs = []
            for lane, value in lanes.items():
                lane_directory = directory / f'lane{lane}'
                service.common.mkdir_durable(lane_directory)
                config_directory = lane_directory / 'phase_01'
                seed(config_directory, dict(value['config'], gate_path=gate_path), value['state'], frontier=True)
                configs.append(config_directory / 'CONFIG.json')
            for config_path in configs:
                log = stack.enter_context((config_path.parent.parent / 'WORKER.log').open('xb'))
                process = subprocess.Popen([sys.executable, '-B', '-m', 'gpu.orch_r158_kernel_execution',
                    'worker', '--config', str(config_path)], cwd=Path(__file__).resolve().parents[1],
                    stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                    pass_fds=tuple(descriptors), env=dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1'))
                processes.append(process)
            service.store(directory / 'ACTIVATION.json', service.encoded(dict(
                observed_unix=time.time(), status='SCANNERS_SPAWNED_NOT_CHILD_RESULT',
                pids=[process.pid for process in processes], config_paths=[str(path) for path in configs],
                phases=PHASES, phase_seconds=PHASE_SECONDS, children=prior.child_identities(),
                no_fixture_kernel_dispatch=True)))
        except BaseException as error:
            service.store(directory / 'FAILED_NO_RETRY.json', service.encoded(dict(
                observed_unix=time.time(), error_type=type(error).__name__, error=str(error),
                worker_pids=[process.pid for process in processes])))
            raise
        finally:
            for process in processes:
                process.wait()
        result = dict(observed_unix=time.time(), status='WORKERS_EXITED',
                      exit_codes=[process.returncode for process in processes], children=prior.child_identities())
        service.store(directory / 'FINISHED.json', service.encoded(result))
        return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('attest', 'activate', 'worker'))
    parser.add_argument('--directory', type=Path)
    parser.add_argument('--cpu-log', type=Path)
    parser.add_argument('--cpu-exit-code', type=int)
    parser.add_argument('--config', type=Path)
    options = parser.parse_args()
    if options.action == 'attest':
        result = attest(options.directory, options.cpu_log, options.cpu_exit_code)
    elif options.action == 'activate':
        result = activate(options.directory)
    else:
        result = worker(options.config)
    print(json.dumps(result, sort_keys=True, indent=2))
