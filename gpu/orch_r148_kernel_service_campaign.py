"""One-shot, finite renewal of the original kernel0 tool bridge; never retry intent."""

import argparse
import datetime
import json
import math
import os
from pathlib import Path
import re
import sys
import time

from gpu import orch_r148_kernel_tool_service as service


SCHEMA = 'R148_KERNEL_CAMPAIGN_V1'
KERNEL_ROOT = '/localhome/local-rohing/orch_r132_kernel_child_20260916_attempt1/run1'
COUNTERS = ('polls', 'calls', 'reads', 'read_bytes', 'request_bytes', 'output_reserved')
BUDGETS = dict(zip(COUNTERS, ('max_polls', 'max_calls', 'max_reads', 'max_read_bytes',
                              'max_request_bytes', 'max_output_bytes')))
KEYS = {'directory', 'source_root', 'predecessor_config', 'predecessor_config_sha256',
        'predecessor_state_sha256', 'predecessor_terminal', 'predecessor_terminal_sha256',
        'predecessor_pid', 'hard_wall_unix', 'wall_seconds', 'phase_seconds', 'max_phases',
        'phase_calls', 'poll_seconds'} | set(BUDGETS.values())
require = service.require
read = service.read
sha = service.sha
encoded = service.encoded
store = service.store
common = service.common
executor = service.executor


def document(path, limit=65536):
    return service.cpu.read_document(read(path, limit))


def private_file(path, limit=65536):
    raw = read(path, limit)
    metadata = Path(path).stat()
    require(metadata.st_uid == os.geteuid() and metadata.st_mode & 0o077 == 0,
            'private_operator_file_required')
    return raw


def closure():
    sources = service.closure()
    for path in (Path(__file__).resolve(), Path(__file__).resolve().parents[1] /
                 'tests/test_orch_r148_kernel_service_campaign.py'):
        sources[str(path)] = sha(read(path, 1048576))
    require(len(sources) <= 34, 'bounded_campaign_source_closure')
    return sources


def lease_wall(original):
    raw = read(original['lease_receipt_path'], 65536)
    require(sha(raw) == original['lease_receipt_sha256'], 'lease_hash_changed')
    lease = service.cpu.read_document(raw)
    end = datetime.datetime.fromisoformat(lease['conservative_lease_end_utc'])
    require(end.tzinfo is not None and type(lease['margin_seconds']) is int
            and lease['margin_seconds'] >= 21600, 'original_lease_margin_required')
    return end.timestamp() - lease['margin_seconds']


def stopped(terminal, state):
    require(state.get('schema') == service.SCHEMA and state.get('phase') == 'STOPPED'
            and state.get('reason') in ('WALL_LIMIT', 'CALL_LIMIT')
            and not any(key.startswith('pending_') for key in state), 'unsafe_predecessor_state')
    require(terminal.get('state') == state, 'terminal_state_mismatch')
    status = terminal.get('status')
    require((status == 'STOPPED_NO_REPLAY' and terminal.get('error') == state['reason']
             and terminal.get('error_type') == 'ValueError')
            or (status == 'WALL_LIMIT_NO_REPLAY' and state['reason'] == 'WALL_LIMIT'
                and 'error' not in terminal)
            or (status == 'STOPPED' and 'error' not in terminal), 'terminal_status_mismatch')
    for key in COUNTERS:
        require(type(state.get(key)) is int and state[key] >= 0, 'invalid_inherited_counter')
    require(type(state.get('next_index')) is int, 'invalid_inherited_cursor')


def terminal_document(raw):
    offset = raw.rfind(b'\n{')
    return service.cpu.read_document(raw[offset + 1:] if offset >= 0 else raw)


def cursor(original, state):
    require(state['next_index'] >= original['start_index'], 'cursor_before_original_start')
    raw, value = service.record(original, state['next_index'] - 1)
    require(value['sha256'] == state['previous_sha256'], 'cursor_predecessor_changed')
    return raw


def predecessor(config):
    raw = private_file(config['predecessor_config'])
    require(sha(raw) == config['predecessor_config_sha256'], 'predecessor_config_changed')
    original = service.cpu.read_document(raw)
    service.base_config(original)
    require(set(original) == service.BASE_KEYS | service.PIN_KEYS, 'original_pins_required')
    require(original['root'] == KERNEL_ROOT, 'single_original_kernel0_only')
    require(not Path('/proc', str(config['predecessor_pid'])).exists(), 'predecessor_process_not_gone')
    for key in ('state', 'spool'):
        common.private_directory(Path(original[key]))
    require((Path(original['state']) / 'SERVICE.lock').is_file(), 'predecessor_lock_missing')
    require(read(Path(original['state']) / 'CONFIG.json', 65536) == encoded(original)
            and read(Path(original['spool']) / 'SERVICE_OWNER.json', 65536) == encoded(original),
            'predecessor_namespace_binding')
    state_raw = read(Path(original['state']) / 'STATE.json', 65536)
    terminal_raw = read(config['predecessor_terminal'], 1048576)
    require(sha(state_raw) == config['predecessor_state_sha256'], 'predecessor_state_changed')
    require(sha(terminal_raw) == config['predecessor_terminal_sha256'], 'predecessor_terminal_changed')
    state = service.cpu.read_document(state_raw)
    require(state.get('config_sha256') == sha(encoded(original)), 'predecessor_state_binding')
    stopped(terminal_document(terminal_raw), state)
    for key, budget in BUDGETS.items():
        require(state[key] <= original[budget] and state[key] <= config[budget],
                'inherited_budget_exhausted_or_invalid')
    cursor(original, state)
    return original, state


def frozen(config, original, sources):
    require(closure() == sources, 'campaign_source_changed')
    require(all(Path(config['source_root']) in Path(path).parents for path in sources),
            'campaign_source_root_binding')
    old_sources = original['source_closure']
    require(type(old_sources) is dict and 0 < len(old_sources) <= 32, 'original_source_closure')
    for path, expected in old_sources.items():
        require(Path(original['source_root']) in Path(path).parents
                and sha(read(path, 1048576)) == expected, 'original_source_changed')
        replacement = str(Path(config['source_root']) / Path(path).relative_to(original['source_root']))
        require(replacement not in sources or sources[replacement] == expected,
                'original_shared_source_changed')
    for name in ('orch_r132_kernel_executor.py', 'orch_r132_kernel_bridge.py'):
        current = Path(service.__file__).resolve().parent / name
        prior = Path(original['source_root']) / 'gpu' / name
        require(str(prior) in old_sources and sha(read(current, 1048576)) == old_sources[str(prior)],
                'original_executor_bridge_changed')
    for path, expected, limit in (
        (Path(original['runtime_root']) / 'MANIFEST.json', original['runtime_manifest_sha256'], 4194304),
        (original['gate_path'], original['gate_sha256'], 1048576),
        (Path(original['root']) / 'stream/JOURNAL.json', original['journal_manifest_sha256'], 4096)):
        require(sha(read(path, limit)) == expected, 'original_immutable_pin_changed')
    prefix_raw, prefix = service.record(original, original['start_index'] - 1)
    require(sha(prefix_raw) == original['start_after_sha256']
            and read(Path(original['state']) / 'PREDECESSOR.record.json', service.RECORD_LIMIT) == prefix_raw,
            'original_prefix_changed')
    lease_wall(original)


def configuration(path):
    raw = private_file(path)
    config = service.cpu.read_document(raw)
    require(set(config) == KEYS, 'exact_campaign_config_fields')
    for key in ('directory', 'source_root', 'predecessor_config', 'predecessor_terminal'):
        executor.trusted_path(config[key])
    for key, upper in dict(wall_seconds=21600, phase_seconds=1800, max_phases=12,
                           phase_calls=24, max_calls=24, max_polls=10000, max_reads=10**8,
                           max_read_bytes=2**50, max_request_bytes=10000000,
                           max_output_bytes=100 * service.OUTPUT_RESERVATION,
                           predecessor_pid=2**31 - 1).items():
        require(type(config[key]) is int and 1 <= config[key] <= upper, 'bounded_' + key)
    require(config['predecessor_pid'] > 1 and config['phase_seconds'] > service.DISPATCH_RESERVE,
            'pid_and_phase_reserve')
    require(type(config['hard_wall_unix']) in (int, float)
            and math.isfinite(config['hard_wall_unix']), 'finite_campaign_wall')
    require(type(config['poll_seconds']) in (int, float) and math.isfinite(config['poll_seconds'])
            and 0.05 <= config['poll_seconds'] <= 60, 'bounded_poll_seconds')
    original, state = predecessor(config)
    directory = Path(config['directory'])
    for protected in [Path(config[key]) for key in ('source_root', 'predecessor_config', 'predecessor_terminal')] + [
            Path(original[key]) for key in ('root', 'state', 'spool', 'source_root', 'runtime_root',
                                            'gate_path', 'lease_receipt_path', 'executor_lock')]:
        require(directory != protected and directory not in protected.parents
                and protected not in directory.parents, 'disjoint_campaign_directory')
    require(Path(path) != directory and directory not in Path(path).parents, 'external_private_config')
    return raw, config, original, state


def attest(config_path, cpu_log, receipt_path, exit_code):
    raw, config, original, state = configuration(config_path)
    sources = closure()
    frozen(config, original, sources)
    log = read(cpu_log, 1048576)
    require(exit_code == 0 and re.search(rb'\b[1-9][0-9]* passed\b', log)
            and not re.search(rb'\b[1-9][0-9]* (failed|errors?)\b', log), 'passing_Main_CPU_log_required')
    receipt = dict(schema=SCHEMA, status='MAIN_CPU_ATTESTED_NOT_GPU_ADMITTED',
                   config_sha256=sha(raw), source_closure=sources, cpu_log_path=str(cpu_log),
                   cpu_log_sha256=sha(log), cpu_exit_code=exit_code)
    store(Path(receipt_path), encoded(receipt))
    return receipt


def write_lock(descriptor, value):
    raw = encoded(value)
    os.lseek(descriptor, 0, os.SEEK_SET)
    os.ftruncate(descriptor, 0)
    require(os.write(descriptor, raw) == len(raw), 'complete_lock_receipt_write')
    os.fsync(descriptor)


def campaign_lock(original):
    return Path(original['executor_lock']).with_name(
        '.orch_r148_campaign_' + sha(original['root'].encode())[:24] + '.lock')


def renew(config, original, phase, deadline, remaining, sources):
    require(remaining() > service.DISPATCH_RESERVE, 'campaign_wall_exhausted')
    require(executor.validate_runtime(original['runtime_root']) == original['runtime_manifest_sha256'],
            'runtime_changed')
    devices = executor.device_identity()
    identity = executor.policy_identity(Path(original['runtime_root']), original['runtime_manifest_sha256'], devices)
    with service.lock_file(Path(original['executor_lock'])) as descriptor:
        previous = os.read(descriptor, 65537)
        require(len(previous) <= 65536, 'bounded_executor_lock')
        store(phase / 'EXECUTOR_LOCK_BEFORE.bin', previous)
        observed = time.time()
        if previous:
            last = service.cpu.read_document(previous)
            require(last.get('result_status') in ('CORRECT', 'INCORRECT', 'KERNEL_ERROR',
                    'PROCESS_FAILED', 'OUTPUT_LIMIT', 'TIMEOUT', 'TRUSTED_PROBES_PASSED')
                    and type(last.get('last_finished_unix')) in (float, int)
                    and observed > last['last_finished_unix'], 'ambiguous_executor_predecessor')
        require(executor.device_identity() == devices, 'device_mapping_changed')
        census_raw = service.census()
        store(phase / 'CENSUS.xml', census_raw)
        frozen(config, original, sources)
        require(time.time() - observed <= 30, 'stale_probe_census')
        wall = min(deadline, lease_wall(original), time.time() + remaining())
        admission = dict(schema='R132_KERNEL_ADMISSION_V1', main_authorized=True, census_clear=True,
            gpu_uuid=original['gpu_uuid'], device_minor=original['device_minor'], observed_unix=observed,
            expires_unix=min(observed + 210, wall), hard_wall_unix=wall,
            lease_receipt_path=original['lease_receipt_path'], lease_receipt_sha256=original['lease_receipt_sha256'],
            census_sha256=sha(census_raw), config_sha256=sha(encoded(config)), source_closure=sources)
        admission_path = phase / 'PROBE_ADMISSION.json'
        store(admission_path, encoded(admission))
        executor.validate_admission(admission_path, time.time())
        write_lock(descriptor, dict(result_status='DISPATCH_INCOMPLETE', last_finished_unix=time.time(),
                                    campaign_phase=str(phase)))
        store(phase / 'PROBE_INTENT.json', encoded(admission))
        with common.hard_wall(remaining()):
            result = executor.run_trusted_probes(str(phase / 'probes'), original['runtime_root'], str(admission_path))
        store(phase / 'PROBE_RESULT.json', encoded(result))
        gate_path = phase / 'probes/GATE.json'
        require(result.get('passed') is True and result.get('checks') == 26
                and len(executor.GATE_CHECKS) == 26 and result.get('gate_path') == str(gate_path),
                'fresh_full_probe_matrix_required')
        gate_hash = executor.validate_gate(gate_path, identity, time.time())
        require(document(gate_path, 1048576)['observed_unix'] >= observed, 'new_phase_gate_required')
        require(executor.device_identity() == devices, 'device_mapping_changed_after_probes')
        require(executor.validate_runtime(original['runtime_root']) == original['runtime_manifest_sha256'],
                'runtime_changed_after_probes')
        frozen(config, original, sources)
        require(remaining() > service.DISPATCH_RESERVE, 'phase_wall_exhausted_after_probes')
        write_lock(descriptor, dict(result_status='TRUSTED_PROBES_PASSED', last_finished_unix=time.time(),
                                    gate_sha256=gate_hash, campaign_phase=str(phase)))
    return str(gate_path)


def run(config_path, receipt_path):
    raw, config, original, inherited = configuration(config_path)
    receipt_raw = private_file(receipt_path)
    receipt = service.cpu.read_document(receipt_raw)
    sources = closure()
    require(receipt.get('schema') == SCHEMA and receipt.get('status') == 'MAIN_CPU_ATTESTED_NOT_GPU_ADMITTED'
            and receipt.get('config_sha256') == sha(raw) and receipt.get('source_closure') == sources
            and receipt.get('cpu_exit_code') == 0
            and sha(read(receipt['cpu_log_path'], 1048576)) == receipt['cpu_log_sha256'], 'bound_CPU_receipt_required')
    frozen(config, original, sources)
    directory = Path(config['directory'])
    deadline = min(config['hard_wall_unix'], time.time() + config['wall_seconds'], lease_wall(original))
    monotonic_deadline = time.monotonic() + max(0, deadline - time.time())

    def left():
        return min(deadline - time.time(), monotonic_deadline - time.monotonic())

    with service.lock_file(campaign_lock(original)) as owner, service.lock_file(Path(original['state']) / 'SERVICE.lock'):
        require(os.fstat(owner).st_size == 0, 'campaign_already_claimed_no_retry')
        require(not directory.exists(), 'fresh_campaign_directory_required')
        require(left() > service.DISPATCH_RESERVE, 'campaign_wall_exhausted')
        predecessor(config)
        write_lock(owner, dict(schema=SCHEMA, config_sha256=sha(raw), directory=str(directory), status='CLAIMED_NO_RETRY'))
        common.mkdir_durable(directory)
        store(directory / 'CONFIG.json', raw)
        store(directory / 'CPU_RECEIPT.json', receipt_raw)
        state = dict(schema=SCHEMA, phase='ACTIVE', phases=0, deadline_unix=deadline,
                     deadline_monotonic=monotonic_deadline, service_state=inherited)
        common.save_state(directory, state)
        previous_phase = None
        phase = None
        try:
            inherited = dict(inherited)
            inherited['reads'] += 2000
            inherited['read_bytes'] += 256 * 1048576
            inherited['output_reserved'] += 72 * 1048576
            for key, budget in BUDGETS.items():
                require(inherited[key] <= config[budget], 'campaign_initial_' + budget + '_exhausted')
            state['service_state'] = inherited
            common.save_state(directory, state)
            for path, checksum in dict(original['source_closure'], **sources).items():
                target = directory / ('SOURCE_' + checksum + '.bin')
                if not target.exists():
                    store(target, read(path, 1048576))
            for number in range(1, config['max_phases'] + 1):
                if inherited['calls'] >= config['max_calls']:
                    state['reason'] = 'CALL_LIMIT'
                    break
                if left() <= service.DISPATCH_RESERVE:
                    state['reason'] = 'WALL_LIMIT'
                    break
                require(private_file(config_path) == raw and private_file(receipt_path) == receipt_raw,
                        'campaign_config_or_receipt_changed')
                predecessor(config)
                frozen(config, original, sources)
                if previous_phase is not None:
                    previous_config, previous_result = previous_phase
                    require(read(Path(previous_config['state']) / 'CONFIG.json', 65536) == encoded(previous_config)
                            and read(Path(previous_config['spool']) / 'SERVICE_OWNER.json', 65536) == encoded(previous_config)
                            and read(Path(previous_config['state']).parent / 'CONFIG.json', 65536) == encoded(previous_config),
                            'previous_phase_namespace_changed')
                    require(document(Path(previous_config['state']).parent / 'TERMINAL.json') == previous_result,
                            'previous_phase_terminal_changed')
                    stopped(previous_result, document(Path(previous_config['state']) / 'STATE.json'))
                    service.validate_config(previous_config)
                cursor_raw = cursor(original, inherited)
                reserved = dict(inherited)
                reserved['reads'] += 2000 + 4 * original['max_runtime_files']
                reserved['read_bytes'] += 1024**3 + 4 * original['max_runtime_bytes']
                reserved['output_reserved'] += 16 * 1048576
                for key, budget in BUDGETS.items():
                    require(reserved[key] < config[budget], 'campaign_' + budget + '_exhausted')
                phase = directory / f'phase_{number:02d}'
                common.mkdir_durable(phase)
                store(phase / 'CURSOR.record.json', cursor_raw)
                store(phase / 'INHERITED.json', encoded(inherited))
                state.update(phases=number, phase='PROBE_INTENT', service_state=reserved)
                common.save_state(directory, state)
                phase_deadline = min(deadline, time.time() + config['phase_seconds'])
                phase_monotonic = min(monotonic_deadline, time.monotonic() + config['phase_seconds'])

                def phase_left():
                    return min(left(), phase_deadline - time.time(), phase_monotonic - time.monotonic())

                gate_path = renew(config, original, phase, phase_deadline, phase_left, sources)
                require(phase_left() > service.DISPATCH_RESERVE, 'phase_wall_exhausted')
                require(cursor(original, inherited) == cursor_raw, 'cursor_changed_during_probe')
                require(private_file(config_path) == raw and private_file(receipt_path) == receipt_raw,
                        'campaign_config_or_receipt_changed')
                phase_config = dict(original, state=str(phase / 'service'), spool=str(phase / 'spool'),
                                    source_root=config['source_root'], gate_path=gate_path,
                                    poll_seconds=config['poll_seconds'],
                                    wall_seconds=min(1800, int(phase_left())))
                phase_config.update({key: config[key] for key in BUDGETS.values()})
                phase_config['max_calls'] = min(config['max_calls'], inherited['calls'] + config['phase_calls'])
                phase_config = service.pin_config(phase_config)
                store(phase / 'CONFIG.json', encoded(phase_config))
                with service.namespace(phase_config) as (namespace, seeded):
                    seeded.update({key: reserved[key] for key in COUNTERS})
                    seeded.update(next_index=inherited['next_index'], previous_sha256=inherited['previous_sha256'],
                                  deadline_unix=phase_deadline, deadline_monotonic=phase_monotonic)
                    common.save_state(namespace, seeded)
                    store(phase / 'INITIAL_STATE.json', encoded(seeded))
                state['phase'] = 'SERVICE_INTENT'
                common.save_state(directory, state)
                result = service.run(phase_config)
                store(phase / 'TERMINAL.json', encoded(result))
                finished = document(Path(phase_config['state']) / 'STATE.json')
                state['observed_service_state'] = finished
                stopped(result, finished)
                require(finished.get('config_sha256') == sha(encoded(phase_config)), 'phase_state_binding')
                require(all(reserved[key] <= finished[key] <= phase_config[BUDGETS[key]] for key in COUNTERS)
                        and finished['next_index'] >= inherited['next_index'], 'phase_counter_or_cursor_regression')
                cursor(original, finished)
                service.validate_config(phase_config)
                frozen(config, original, sources)
                inherited = finished
                previous_phase = phase_config, result
                state.update(phase='BETWEEN_PHASES', service_state=inherited)
                common.save_state(directory, state)
            else:
                state['reason'] = 'PHASE_LIMIT'
            state['phase'] = 'STOPPED'
        except (Exception, common.WallExpired) as error:
            state.update(phase='FAILED_NO_RETRY', reason=str(error)[:4096] or type(error).__name__)
            if phase is not None:
                store(phase / 'FAILURE.json', encoded(state))
        common.save_state(directory, state)
        result = dict(status=state['phase'], state=state)
        store(directory / 'TERMINAL.json', encoded(result))
        write_lock(owner, dict(schema=SCHEMA, config_sha256=sha(raw), directory=str(directory), status=state['phase']))
        return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('attest', 'run'))
    parser.add_argument('--config', required=True)
    parser.add_argument('--receipt', required=True)
    parser.add_argument('--cpu-log')
    parser.add_argument('--cpu-exit-code', type=int)
    options = parser.parse_args(argv)
    if options.command == 'attest':
        require(options.cpu_log is not None and options.cpu_exit_code is not None, 'CPU_log_and_exit_code_required')
        result = attest(options.config, options.cpu_log, options.receipt, options.cpu_exit_code)
    else:
        result = run(options.config, options.receipt)
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))
    return int(result.get('status') == 'FAILED_NO_RETRY')


if __name__ == '__main__':
    sys.exit(main())
