"""R155 custody observation and explicitly gated, future-only sidecar handoff."""

import argparse
from contextlib import ExitStack, contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time


POLICY = 'R153_FIRST_CODE_BLOCK_ASCII_PUNCTUATION_V1'
BASE = Path('/localhome/local-rohing')
CAMPAIGN = 'orch_r148_kernel_campaign_20260916t1900z'
MODULE_PREFIXES = ('gpu.orch_', 'orch_')
SCANNER_WORDS = ('tool_service', 'service_campaign', 'kernel_bridge', 'kernel_smoke',
                 'kernel_parser_activate', 'kernel_executor')
ROOTS = {0: str(BASE / 'orch_r132_kernel_child_20260916_attempt1/run1'),
         4: str(BASE / 'orch_r136_kernel_parented_a40r4_20260916_attempt1/run1')}
CHILD_PIDS = {0: 2709461, 4: 3496993}
TEST_NAMES = ('orch_r155_kernel_parser_activate', 'orch_r153_code_blocks',
              'orch_r132_kernel_bridge', 'orch_r148_kernel_tool_service',
              'orch_r148_kernel_service_campaign')
FAILED_PROBE_SHA256 = '2b8ea8ed4fd8a0ab6d4b2a4dcdefe06be8f0f4ea09f8279773e7ae76ae9c2a04'


def scanner_modules(arguments):
    found = []
    for argument in arguments:
        candidate = Path(argument).name.removesuffix('.py')
        if candidate.startswith(MODULE_PREFIXES) and any(
                word in candidate for word in SCANNER_WORDS):
            found.append(candidate)
    return sorted(set(found))


def process_inventory(proc_root=Path('/proc')):
    scanners, unreadable = [], []
    for process in sorted(proc_root.iterdir()):
        if not process.name.isdigit():
            continue
        try:
            raw = (process / 'cmdline').read_bytes()
            if len(raw) > 1048576:
                raise ValueError('oversized_cmdline')
            modules = scanner_modules(raw.decode(errors='replace').split('\0'))
            if modules:
                scanners.append(dict(pid=int(process.name), modules=modules))
        except FileNotFoundError:
            if process.exists():
                unreadable.append(int(process.name))
        except (OSError, ValueError):
            unreadable.append(int(process.name))
    return dict(scanners=scanners, unreadable_pids=unreadable)


def metadata(path, keys):
    raw = path.read_bytes()
    if len(raw) > 65536:
        raise ValueError('bounded_metadata_required')
    value = json.loads(raw)
    return dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest(),
                value={key: value[key] for key in keys if key in value})


def assess(snapshot):
    reasons = []
    inventory = snapshot['process_inventory']
    if inventory['scanners']:
        reasons.append('COMPETING_SCANNER_LIVE')
    if inventory['unreadable_pids']:
        reasons.append('PROCESS_CUSTODY_INCOMPLETE')
    if snapshot.get('errors'):
        reasons.append('METADATA_INCOMPLETE')
    state = snapshot.get('campaign_state', {}).get('value', {})
    if state.get('phase') != 'STOPPED':
        reasons.append('CAMPAIGN_NOT_CLEANLY_STOPPED')
    terminal = snapshot.get('campaign_terminal', {}).get('value', {})
    if terminal.get('status') != 'STOPPED':
        reasons.append('CLEAN_CAMPAIGN_TERMINAL_MISSING')
    return dict(status='BLOCKED_CUSTODY' if reasons else 'REQUIRES_LOCKED_HANDOFF',
                reasons=reasons, activation_authorized=False, activated=False,
                model_submission_claimed=False, gpu_call_attempted=False,
                signals_sent=False, policy=POLICY)


def observe(base=BASE, proc_root=Path('/proc')):
    snapshot = dict(schema='R155_READ_ONLY_CUSTODY_V1', observed_unix=time.time(),
                    process_inventory=process_inventory(proc_root), errors=[])
    directory = base / CAMPAIGN
    paths = [('campaign_state', directory / 'STATE.json',
              ('schema', 'phase', 'phases', 'deadline_unix')),
             ('campaign_terminal', directory / 'TERMINAL.json', ('status',))]
    for label, path, keys in paths:
        try:
            snapshot[label] = metadata(path, keys)
        except (OSError, ValueError, TypeError) as error:
            snapshot['errors'].append(dict(label=label, error_type=type(error).__name__))
    phase = snapshot.get('campaign_state', {}).get('value', {}).get('phases')
    if type(phase) is int and 1 <= phase <= 12:
        phase_path = directory / f'phase_{phase:02d}'
        try:
            snapshot['service_state'] = metadata(phase_path / 'service/STATE.json',
                ('schema', 'phase', 'next_index', 'previous_sha256', 'calls',
                 'deadline_unix', 'pending_index', 'pending_response_sha256'))
            snapshot['service_config'] = metadata(phase_path / 'CONFIG.json',
                ('root', 'state', 'spool', 'source_root', 'code_policy',
                 'executor_lock', 'gate_path'))
        except (OSError, ValueError, TypeError) as error:
            snapshot['errors'].append(dict(label='service', error_type=type(error).__name__))
    snapshot['assessment'] = assess(snapshot)
    return snapshot


def modules():
    from gpu import orch_r148_kernel_service_campaign as campaign
    from gpu import orch_r148_kernel_tool_service as service
    from gpu import orch_r153_kernel_smoke as smoke
    return service, campaign, smoke


def source_pins():
    service, campaign, smoke = modules()
    pins = service.closure()
    source = Path(__file__).resolve().parents[1]
    paths = [Path(__file__).resolve(), Path(campaign.__file__), Path(smoke.__file__)]
    paths.append(source / 'organism_v6/orch_r125_plain_context.py')
    paths += [source / 'tests' / f'test_{name}.py' for name in TEST_NAMES]
    for path in paths:
        pins[str(path)] = service.sha(service.read(path, 1048576))
    service.require(all(source in Path(path).parents for path in pins), 'new_source_closure_contained')
    return pins


def attest(directory, cpu_log, exit_code):
    service, _, _ = modules()
    directory = service.executor.trusted_path(str(directory))
    raw = service.read(cpu_log, 1048576)
    service.require(exit_code == 0 and re.search(rb'\b[1-9][0-9]* passed\b', raw)
                    and not re.search(rb'\b[1-9][0-9]* (failed|errors?)\b', raw), 'passing_CPU_log_required')
    receipt = dict(schema='R155_ACTIVATION_CPU_V1', status='PASS_NOT_GPU_ADMITTED',
                   source_pins=source_pins(), cpu_log=str(cpu_log), cpu_log_sha256=service.sha(raw),
                   exit_code=exit_code, observed_unix=time.time())
    service.store(directory / 'CPU_GATE.json', service.encoded(receipt))
    return receipt


def clean_terminal(campaign_state, campaign_terminal, state, terminal):
    service, campaign, _ = modules()
    service.require(campaign_state.get('phase') == 'STOPPED'
                    and campaign_terminal == dict(status='STOPPED', state=campaign_state),
                    'matching_clean_campaign_terminal_required')
    campaign.stopped(terminal, state)
    service.require(campaign_state.get('service_state') == state
                    and campaign_state.get('observed_service_state') == state,
                    'final_service_state_binding')
    service.require(state['calls'] == 0, 'nonzero_prior_calls_require_separate_reconciliation')
    return {key: state[key] for key in campaign.COUNTERS}


def future_start(prefix, previous_next):
    service, _, _ = modules()
    service.require(type(prefix.get('index')) is int and prefix['index'] >= previous_next - 1,
                    'future_frontier_not_before_prior_cursor')
    service.require(prefix.get('kind') in ('UPDATE', 'SLEEP_COMPLETE', 'COMMITTED',
                    'TARGET_ELIGIBILITY', 'COMPACTION', 'COMPACTION_SKIPPED'),
                    'future_frontier_must_exclude_inflight_generation')
    return prefix['index'] + 1


def inherit_counters(seeded, previous):
    service, campaign, _ = modules()
    service.require(previous.get('phase') == 'STOPPED'
                    and not any(key.startswith('pending_') for key in previous), 'no_pending_state_inheritance')
    result = dict(seeded)
    for key in campaign.COUNTERS:
        service.require(type(previous.get(key)) is int and previous[key] >= 0, 'nonnegative_inherited_counter')
        result[key] = previous[key]
    return result


def child_identities():
    service, _, _ = modules()
    result = {}
    for lane, pid in CHILD_PIDS.items():
        process = Path('/proc') / str(pid)
        status = (process / 'stat').read_text().rsplit(')', 1)[1].split()
        command = (process / 'cmdline').read_bytes()
        service.require(status[0] not in ('Z', 'X') and b'native' in command, 'original_child_live_required')
        result[str(lane)] = dict(pid=pid, start_ticks=status[19], cmdline_sha256=service.sha(command))
    return result


def original_bundle():
    service, campaign, _ = modules()
    directory = BASE / CAMPAIGN
    refs = {}

    def document(path, limit=65536):
        raw = service.read(path, limit)
        refs[str(path)] = service.sha(raw)
        return service.cpu.read_document(raw)

    config = document(directory / 'CONFIG.json')
    receipt = document(directory / 'CPU_RECEIPT.json')
    service.require(service.sha(service.read(directory / 'CONFIG.json', 65536)) == receipt['config_sha256'],
                    'old_campaign_config_pin')
    for path, digest in receipt['source_closure'].items():
        service.require(service.sha(service.read(path, 1048576)) == digest, 'old_campaign_source_pin')
    state = document(directory / 'STATE.json')
    terminal = document(directory / 'TERMINAL.json')
    service.require(type(state.get('phases')) is int and 1 <= state['phases'] <= 12, 'bounded_old_phases')
    phase = directory / f'phase_{state["phases"]:02d}'
    old = document(phase / 'CONFIG.json')
    final = document(phase / 'service/STATE.json')
    final_terminal = document(phase / 'TERMINAL.json')
    clean_terminal(state, terminal, final, final_terminal)
    service.require(final['config_sha256'] == service.sha(service.encoded(old)), 'old_service_config_pin')
    service.base_config(old)
    service.require(old['root'] == ROOTS[0] and not Path('/proc/3754322').exists(), 'original_campaign_gone')
    for path, digest in old['source_closure'].items():
        service.require(service.sha(service.read(path, 1048576)) == digest, 'old_service_source_pin')
    for key, path in (('lease_receipt_sha256', Path(old['lease_receipt_path'])),
                      ('runtime_manifest_sha256', Path(old['runtime_root']) / 'MANIFEST.json'),
                      ('journal_manifest_sha256', Path(old['root']) / 'stream/JOURNAL.json')):
        service.require(service.sha(service.read(path, 4194304)) == old[key], 'original_pin_' + key)
    campaign.cursor(old, final)
    service.require(campaign.lease_wall(old) > time.time() + 2100, 'original_lease_reserve')
    predecessor = document(Path(config['predecessor_config']))
    locks = [campaign.campaign_lock(old), Path(predecessor['state']) / 'SERVICE.lock']
    locks.append(campaign.campaign_lock(dict(old, root=ROOTS[4])))
    for number in range(1, state['phases'] + 1):
        previous = directory / f'phase_{number:02d}'
        previous_state = document(previous / 'service/STATE.json')
        campaign.stopped(document(previous / 'TERMINAL.json'), previous_state)
        service.require(previous_state['calls'] == 0
                        and not list((previous / 'service').glob('*/INTENT.json')),
                        'no_historical_dispatch_intent')
        locks.append(previous / 'service/SERVICE.lock')
    return old, final, refs, locks


def worker(config_path):
    service, _, _ = modules()
    config = service.cpu.read_document(service.read(config_path, 65536))
    service.require(config['root'] in ROOTS.values() and config.get('code_policy') == POLICY,
                    'only_authorized_sidecar_roots_and_policy')
    service.validate_config(config)
    service.limits(config, time.time())
    directory = Path(config['state']).parent
    service.store(directory / 'SCANNER_STARTED.json', service.encoded(dict(
        pid=os.getpid(), observed_unix=time.time(), config_sha256=service.sha(service.encoded(config)),
        code_policy=POLICY, start_index=config['start_index'], model_submission_claimed=False)))
    result = service.run(config)
    service.store(directory / 'TERMINAL.json', service.encoded(result))
    return result


@contextmanager
def probe_umask():
    previous = os.umask(0o022)
    try:
        yield
    finally:
        os.umask(previous)


def reconcile_preexec_failure(directory):
    service, _, smoke = modules()
    failed = BASE / 'orch_r155_kernel_parser_20260917t0225z_attempt2'
    probe = failed / 'smoke/probes/basic'
    raw = service.read(probe / 'RECEIPT.json', 65536)
    service.require(service.sha(raw) == FAILED_PROBE_SHA256, 'exact_owned_preexec_failure_required')
    receipt = service.cpu.read_document(raw)
    service.require(receipt.get('cgroup_removed') is True and receipt.get('passed') is False
                    and receipt.get('unit_outcome') == dict(ExecMainStatus='200', Result='exit-code')
                    and receipt.get('capture', {}).get('returncode') == 200
                    and receipt.get('source_kind') == 'FIXED_BUILDER_PROBE_NOT_CHILD'
                    and receipt.get('checks') == {}, 'proved_preexec_CHDIR_failure_only')
    failure = service.cpu.read_document(service.read(failed / 'FAILED.json', 65536))
    service.require(failure.get('worker_pids') == [] and not (failed / 'ACTIVATION.json').exists()
                    and not (failed / 'smoke/REQUEST.json').exists(), 'no_prior_model_or_smoke_request')
    unit = 'orch-r132-kernel-' + service.sha(str(probe).encode())[:32]
    with service.lock_file(service.executor.LOCK_PATH) as descriptor:
        previous = os.read(descriptor, 65536)
        lock = service.cpu.read_document(previous)
        service.require(lock.get('owner') == str(failed / 'smoke')
                        and lock.get('result_status') == 'DISPATCH_INCOMPLETE', 'only_owned_failed_probe_lock')
        outcome = subprocess.run(['sudo', '-n', 'systemctl', 'show', unit + '.service',
                    '--property=LoadState'], capture_output=True, text=True, timeout=5)
        service.require(outcome.returncode in (0, 1) and outcome.stdout.strip() == 'LoadState=not-found'
                        and not (Path('/sys/fs/cgroup/system.slice') / (unit + '.service')).exists(),
                        'failed_probe_unit_and_cgroup_absent')
        census = service.census()
        service.store(directory / 'PREEXEC_RECONCILIATION.json', service.encoded(dict(
            observed_unix=time.time(), status='OWNED_PREEXEC_FAILURE_REAPED_NO_REQUEST',
            failed_probe_sha256=service.sha(raw), prior_lock_sha256=service.sha(previous),
            census_sha256=service.sha(census), unit=unit, old_artifacts_preserved=True)))
        smoke.write_lock(descriptor, dict(result_status='PROCESS_FAILED', last_finished_unix=time.time(),
            owner=str(failed / 'smoke'), reconciliation_path=str(directory / 'PREEXEC_RECONCILIATION.json')))


def activate(directory, reconcile_preexec=False):
    service, campaign, smoke = modules()
    directory = service.executor.trusted_path(str(directory))
    gate = service.cpu.read_document(service.read(directory / 'CPU_GATE.json', 65536))
    service.require(gate.get('schema') == 'R155_ACTIVATION_CPU_V1'
                    and gate.get('exit_code') == 0 and gate['source_pins'] == source_pins()
                    and service.sha(service.read(gate['cpu_log'], 1048576)) == gate['cpu_log_sha256']
                    and 0 <= time.time() - gate['observed_unix'] < 1800, 'fresh_bound_CPU_gate_required')
    old, final, refs, locks = original_bundle()
    children = child_identities()
    processes = []
    with ExitStack() as stack:
        lock_descriptors = []
        for path in locks:
            lock_descriptors.append(stack.enter_context(service.lock_file(path)))
        inventory = process_inventory()
        service.require(not inventory['unreadable_pids'] and not [item for item in inventory['scanners']
                        if item['pid'] != os.getpid()], 'no_competing_scanner')
        service.require(original_bundle()[2] == refs, 'predecessor_changed_under_locks')
        service.store(directory / 'HANDOFF_INTENT.json', service.encoded(dict(
            observed_unix=time.time(), pid=os.getpid(), predecessor_refs=refs,
            preserved_service_state=final, children=children, code_policy=POLICY)))
        try:
            if reconcile_preexec:
                reconcile_preexec_failure(directory)
            with probe_umask():
                result = smoke.run(directory / 'smoke', old['runtime_root'], old['lease_receipt_path'])
            service.require(result['status'] == 'PASS', 'new_actual_confinement_smoke_required')
            service.require(child_identities() == children, 'children_changed_during_smoke')
            service.require(original_bundle()[2] == refs and source_pins() == gate['source_pins'],
                            'handoff_pins_changed_after_smoke')
            configs = []
            for lane, root in ROOTS.items():
                lane_directory = directory / f'lane{lane}'
                service.common.mkdir_durable(lane_directory)
                files = [path for path in (Path(root) / 'stream/records').iterdir()
                         if re.fullmatch(r'[0-9]{20}\.json', path.name)]
                service.require(0 < len(files) <= 100000, 'bounded_native_journal')
                index = int(max(files, key=lambda path: path.name).stem)
                prefix_raw, prefix = service.record(dict(root=root), index)
                start = future_start(prefix, final['next_index'] if lane == 0 else 1)
                base = {key: old[key] for key in service.BASE_KEYS}
                base.update(root=root, source_root=str(Path(__file__).resolve().parents[1]),
                    state=str(lane_directory / 'service'), spool=str(lane_directory / 'spool'),
                    gate_path=result['gate_path'], start_index=start, code_policy=POLICY,
                    wall_seconds=1800, max_calls=2)
                config = service.pin_config(base)
                service.validate_config(config)
                service.limits(config, time.time())
                service.store(lane_directory / 'CONFIG.json', service.encoded(config))
                service.store(lane_directory / 'FUTURE_ORIGIN.json', service.encoded(dict(
                    observed_unix=time.time(), prefix_index=index, prefix_kind=prefix['kind'],
                    prefix_record_sha256=service.sha(prefix_raw), prefix_chain_sha256=prefix['sha256'],
                    previous_next_index=final['next_index'] if lane == 0 else None,
                    start_index=start, skipped_history_not_dispatched=True)))
                with service.namespace(config) as (namespace, seeded):
                    if lane == 0:
                        seeded = inherit_counters(seeded, final)
                    service.common.save_state(namespace, seeded)
                    service.store(lane_directory / 'INITIAL_STATE.json', service.encoded(seeded))
                configs.append(lane_directory / 'CONFIG.json')
            for config_path in configs:
                log = stack.enter_context((config_path.parent / 'SCANNER.log').open('xb'))
                process = subprocess.Popen([sys.executable, '-B', '-m',
                    'gpu.orch_r155_kernel_parser_activate', 'worker', '--config', str(config_path)],
                    cwd=Path(__file__).resolve().parents[1], stdin=subprocess.DEVNULL,
                    stdout=log, stderr=subprocess.STDOUT,
                    pass_fds=tuple(lock_descriptors),
                    env=dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1'))
                processes.append(process)
            service.store(directory / 'ACTIVATION.json', service.encoded(dict(
                status='SCANNERS_SPAWNED_NOT_MODEL_RESULT', observed_unix=time.time(),
                pids=[process.pid for process in processes], configs=[str(path) for path in configs],
                smoke=result, children=child_identities(), no_child_restart=True)))
        except BaseException as error:
            service.store(directory / 'FAILED.json', service.encoded(dict(
                error_type=type(error).__name__, error=str(error), observed_unix=time.time(),
                no_replay=True, worker_pids=[process.pid for process in processes])))
            raise
        finally:
            for process in processes:
                process.wait()
        result = dict(status='WORKERS_EXITED_NO_AUTOMATIC_RETRY', observed_unix=time.time(),
                      exit_codes=[process.returncode for process in processes], children=child_identities())
        service.store(directory / 'FINISHED.json', service.encoded(result))
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', nargs='?', default='observe', choices=('observe', 'attest', 'activate', 'worker'))
    parser.add_argument('--directory', type=Path)
    parser.add_argument('--config', type=Path)
    parser.add_argument('--cpu-log', type=Path)
    parser.add_argument('--cpu-exit-code', type=int)
    parser.add_argument('--reconcile-owned-preexec', action='store_true')
    options = parser.parse_args()
    if options.action == 'observe':
        result = observe()
    elif options.action == 'attest':
        result = attest(options.directory, options.cpu_log, options.cpu_exit_code)
    elif options.action == 'activate':
        result = activate(options.directory, options.reconcile_owned_preexec)
    else:
        result = worker(options.config)
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
