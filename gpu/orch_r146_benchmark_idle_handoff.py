"""Observation and single-use, Main-approved retirement of the R130 CPU scheduler.

Non-material operational repair; no deployment, model calls, source-node access,
scientific reads, old-file writes, or automatic retries. Run locally on the
destination only, through the sanctioned wrapper when Main chooses to execute.
Archimedes' copier is never inspected or signaled. Its normal FAILED handling,
and the phase's lack-of-COMPLETE handling, remain unchanged.

observe(request, output) creates OBSERVATION.json in a new caller-stable directory.
execute(output, approval, approval_sha256) consumes that directory's one execution
attempt, even on deferral. Approval is external, not manufactured by this helper.
All hashes bind bytes except request/snapshot hashes, which bind canonical JSON.
The result records intentional handoff, NOT scientific failure or proven exit.

Request fields: schema=SCHEMA, operation_id, hostname, phase_identity and
scheduler_identity. Both identities have exactly IDENTITY_FIELDS; argv is a
list, start_ticks is the original /proc string, uid/pid/ppid are integers.
Approval fields: schema=APPROVAL_SCHEMA, operation_id, action=ACTION,
approved_by="Main", cpu_tests_passed=true, provenance_passed=true,
observation_sha256, request_sha256, snapshot_sha256, helper_sha256, issued_unix,
expires_unix. Main supplies and byte-pins this after its CPU/provenance gate;
the labels are attestations, not authentication or an independent test runner.
Approval expires within 30 seconds of observation. Status age is at most 65
seconds; both dispatch and hard deadline must remain strictly over 120 seconds
away. Any changed receipt, inventory or identity requires a new operation and
new approval, never a retry of an existing execution attempt.

There is no pause/lock of the immutable scheduler. The final reread, child
check and dispatch margin bound the race but cannot prove absence of unlogged,
detached model descendants. Main must resolve any such ambiguity before
approval. Historical FAILED artifacts stay FAILED; this separate audit label
does not relabel scientific results or verify the downstream exit cascade.
Main must independently wait for scheduler FAILED, phase FAILED and the old
copier's normal COMPLETE before proceeding. Never fabricate phase COMPLETE.
"""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import signal
import socket
import stat
import time


ROOT = Path('/localhome/local-rohing/orch_r130_checkpoint_benchmark_20260916_attempt1')
PHASE_ROOT = ROOT / 'successor_phase_v2'
PHASE_CONFIG = ROOT / 'SUCCESSOR_PHASE_V2.json'
PHASE_SHA256 = 'f32bf19f79f8f0ded3d90376323a6bb30b1f88522db470b27d542d204b72843b'
SEGMENT_CONFIG = PHASE_ROOT / 'SEGMENT_02.CONFIG.json'
SEGMENT_SHA256 = 'b373bcb321d048c25c98c43bf79c4c05da31ca31c7ffc06f7a0146b19388cb79'
SCHEDULER_ROOT = ROOT / 'scheduler_run_phase2_02'
LEDGER_ROOT = ROOT / 'scheduler_ledger'
SCHEMA = 'R146_BENCHMARK_IDLE_HANDOFF_V1'
APPROVAL_SCHEMA = 'R146_BENCHMARK_IDLE_HANDOFF_APPROVAL_V1'
ACTION = 'PIDFD_SIGINT_SCHEDULER_ONLY'
STATUS_MAX_AGE = 65
APPROVAL_MAX_AGE = 30
DISPATCH_MARGIN = 120
EXECUTION_MAX_SECONDS = 10
IDENTITY_FIELDS = {'pid', 'uid', 'start_ticks', 'boot_id', 'ppid', 'cmdline', 'cwd'}
LEGACY_FIELDS = {'pid', 'uid', 'start_ticks', 'boot_id'}


class Defer(ValueError):
    """Insufficient evidence; do not signal anything."""


def require(condition, reason):
    if not condition:
        raise Defer(reason)


def encoded(document):
    return (json.dumps(document, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()


def digest(document):
    return hashlib.sha256(encoded(document)).hexdigest()


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def no_symlinks(path):
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts, 'absolute_no_traversal_path')
    require(not any(parent.is_symlink() for parent in (path, *path.parents)), 'no_symlink_paths')
    return path


def read_bytes(path):
    path = no_symlinks(path)
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as stream:
        info = os.fstat(stream.fileno())
        require(stat.S_ISREG(info.st_mode) and info.st_size <= 4 * 1024 * 1024, 'bounded_regular_metadata')
        raw = stream.read(4 * 1024 * 1024 + 1)
        require(len(raw) <= 4 * 1024 * 1024, 'bounded_metadata_read')
        return raw


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'duplicate_json_key')
        result[key] = value
    return result


def document(raw):
    value = json.loads(raw, object_pairs_hook=unique_object)
    require(type(value) is dict, 'metadata_object_required')
    return value


def write_once(path, value):
    path = no_symlinks(path)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'wb') as stream:
        stream.write(encoded(value))
        stream.flush()
        os.fsync(stream.fileno())
    descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def process_identity(pid):
    require(type(pid) is int and pid > 1, 'non_init_exact_pid')
    directory = Path('/proc') / str(pid)
    before = (directory / 'stat').read_text().rsplit(')', 1)[1].split()
    uid_rows = [row.split()[1:] for row in (directory / 'status').read_text().splitlines()
        if row.startswith('Uid:')]
    require(len(uid_rows) == 1 and len(set(uid_rows[0])) == 1, 'unambiguous_process_uid')
    raw_command = (directory / 'cmdline').read_bytes()
    require(raw_command.endswith(b'\0'), 'complete_process_cmdline')
    result = dict(pid=pid, uid=int(uid_rows[0][0]), start_ticks=before[19],
        boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(), ppid=int(before[1]),
        cmdline=[part.decode() for part in raw_command[:-1].split(b'\0')],
        cwd=os.readlink(directory / 'cwd'))
    after = (directory / 'stat').read_text().rsplit(')', 1)[1].split()
    require(before[19] == after[19] and before[1] == after[1]
        and before[0] not in ('Z', 'X', 'T', 't') and after[0] not in ('Z', 'X', 'T', 't'),
        'live_stable_unstopped_identity')
    return result


def process_environment(pid):
    wanted = {b'CUDA_VISIBLE_DEVICES', b'R130_PHASE_SHA256', b'R130_SCHEDULER_ADMISSION_SHA256'}
    result = {}
    for entry in (Path('/proc') / str(pid) / 'environ').read_bytes().split(b'\0'):
        key, separator, value = entry.partition(b'=')
        if separator and key in wanted:
            require(key.decode() not in result, 'duplicate_process_binding')
            result[key.decode()] = value.decode()
    return result


def scheduler_children(pid):
    tasks = Path('/proc') / str(pid) / 'task'
    children = []
    threads = sorted(tasks.iterdir())
    require(bool(threads), 'scheduler_threads_missing')
    for thread in threads:
        children.extend((thread / 'children').read_text().split())
    require(sorted(tasks.iterdir()) == threads, 'scheduler_threads_changed')
    return children


def validate_legacy(identity):
    require(type(identity) is dict and set(identity) == LEGACY_FIELDS, 'legacy_identity_fields')
    require(type(identity['pid']) is int and identity['pid'] > 1
        and type(identity['uid']) is int and identity['uid'] == os.getuid()
        and isinstance(identity['start_ticks'], str) and identity['start_ticks'].isdigit()
        and isinstance(identity['boot_id'], str) and bool(identity['boot_id']), 'legacy_identity_values')


def legacy(identity):
    return {key: identity[key] for key in LEGACY_FIELDS}


def launch_gone(identity):
    validate_legacy(identity)
    boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    require(identity['boot_id'] == boot, 'launch_boot_ambiguity')
    try:
        directory = Path('/proc') / str(identity['pid'])
        fields = (directory / 'stat').read_text().rsplit(')', 1)[1].split()
        require(directory.stat().st_uid == identity['uid'], 'launch_uid_ambiguity')
        return fields[19] != identity['start_ticks'] or fields[0] in ('Z', 'X')
    except FileNotFoundError:
        return True


def validate_request(request):
    require(set(request) == {'schema', 'operation_id', 'hostname', 'phase_identity', 'scheduler_identity'},
        'request_fields')
    require(request['schema'] == SCHEMA and re.fullmatch(r'[a-zA-Z0-9_-]{1,80}', request['operation_id']),
        'request_schema_and_stable_operation_id')
    require(request['hostname'] == socket.gethostname(), 'destination_host_binding')
    for name in ('phase_identity', 'scheduler_identity'):
        identity = request[name]
        require(type(identity) is dict and set(identity) == IDENTITY_FIELDS, 'full_identity_fields')
        validate_legacy(legacy(identity))
        require(type(identity['ppid']) is int and identity['ppid'] > 0
            and type(identity['cmdline']) is list and identity['cmdline']
            and all(isinstance(part, str) and part for part in identity['cmdline']), 'exact_argv_required')
        no_symlinks(identity['cwd'])
    require(request['scheduler_identity']['ppid'] == request['phase_identity']['pid']
        and request['scheduler_identity']['pid'] != request['phase_identity']['pid'], 'original_phase_parent')


class Metadata:
    def __init__(self):
        self.hashes = {}

    def read(self, path, expected=None):
        path = no_symlinks(path)
        require(path.is_relative_to(ROOT), 'destination_metadata_only')
        require(path.name in {'SUCCESSOR_PHASE_V2.json', 'STARTED.json', 'PLAN.json', 'LAUNCH.json',
            'EXIT.json', 'FAILED.json'} or re.fullmatch(
                r'SEGMENT_[0-9]{2}\.(CONFIG|LAUNCH)\.json|STATUS_[0-9]{6}\.json|'
                r'[0-9a-f]{64}\.(RESERVED|COMPLETE)\.json|physical[01]\.FAILED\.json', path.name),
            'metadata_allowlist_no_science_reads')
        require('results' not in path.relative_to(ROOT).parts, 'no_native_science_reads')
        raw = read_bytes(path)
        checksum = hashlib.sha256(raw).hexdigest()
        require(expected is None or checksum == expected, 'metadata_sha256_binding')
        require(str(path) not in self.hashes or self.hashes[str(path)] == checksum, 'metadata_changed_during_read')
        self.hashes[str(path)] = checksum
        return document(raw)

    def latest(self, root, now):
        require(not any((root / name).exists() for name in ('COMPLETE.json', 'FAILED.json')), 'already_terminal')
        paths = sorted(root.glob('STATUS_*.json'))
        require(bool(paths), 'status_missing')
        receipt = self.read(paths[-1])
        require(finite(receipt['observed_unix']) and 0 <= now - receipt['observed_unix'] <= STATUS_MAX_AGE,
            'status_freshness')
        require(receipt['active_physical'] == [], 'active_work')
        require(finite(receipt['next_dispatch_unix'])
            and receipt['next_dispatch_unix'] - now > DISPATCH_MARGIN, 'late_or_ambiguous_dispatch')
        require(finite(receipt['hard_end_unix']) and receipt['hard_end_unix'] - now > DISPATCH_MARGIN,
            'late_or_ambiguous_deadline')
        return receipt


def inventory():
    runs = sorted(ROOT.glob('scheduler_run_*'))
    require(SCHEDULER_ROOT in runs, 'current_scheduler_inventory_missing')
    paths = []
    for root in [PHASE_ROOT, LEDGER_ROOT, *runs]:
        no_symlinks(root)
        require(root.is_dir(), 'metadata_root_missing')
    paths.extend(PHASE_ROOT.glob('SEGMENT_*.LAUNCH.json'))
    for root in runs:
        for dispatch in sorted(root.glob('dispatch_*')):
            no_symlinks(dispatch)
            require(dispatch.is_dir(), 'dispatch_directory_required')
            for job in sorted(dispatch.glob('physical*_job_*')):
                no_symlinks(job)
                require(job.is_dir(), 'job_directory_required')
                paths.extend(job.glob('LAUNCH.json'))
                paths.extend(job.glob('PLAN.json'))
                paths.extend(job.glob('EXIT.json'))
                paths.extend(job.glob('FAILED.json'))
            paths.extend(dispatch.glob('physical*.FAILED.json'))
    paths.extend(LEDGER_ROOT.glob('*.RESERVED.json'))
    paths.extend(LEDGER_ROOT.glob('*.COMPLETE.json'))
    return sorted(paths)


def ledger_check(metadata, paths, current_identity):
    claims = {path.name.removesuffix('.RESERVED.json'): path for path in paths
        if path.parent == LEDGER_ROOT and path.name.endswith('.RESERVED.json')}
    completed = {path.name.removesuffix('.COMPLETE.json'): path for path in paths
        if path.parent == LEDGER_ROOT and path.name.endswith('.COMPLETE.json')}
    require(set(completed) <= set(claims), 'orphan_completion')
    launches, plans, failures = {}, {}, {}
    for path in paths:
        if path.name.endswith('.RESERVED.json') or path.name.endswith('.COMPLETE.json'):
            continue
        item = metadata.read(path)
        if path.name.endswith('.LAUNCH.json') or path.name == 'LAUNCH.json':
            validate_legacy(item['identity'])
            if path == PHASE_ROOT / 'SEGMENT_02.LAUNCH.json':
                require(item['identity'] == legacy(current_identity)
                    and item['config_path'] == str(SEGMENT_CONFIG)
                    and item['config_sha256'] == SEGMENT_SHA256, 'phase_launch_binding')
            else:
                require(launch_gone(item['identity']), 'launch_identity_still_present')
                if path.name == 'LAUNCH.json':
                    require(path.parent / 'EXIT.json' in paths, 'launch_without_exit')
                    launches[path.parent] = item
        if path.name == 'PLAN.json':
            plans[path.parent] = path
        if path.name == 'FAILED.json' or re.fullmatch(r'physical[01]\.FAILED\.json', path.name):
            require(item['status'] in ('FAILED', 'ADMISSION_FAILED_NO_MODEL_REPLAY'), 'nonterminal_failure')
            failures.setdefault(item['key'], []).append((path, item))
    used_jobs, failed_count = set(), 0
    for key, claim_path in claims.items():
        claim = metadata.read(claim_path)
        require(re.fullmatch('[0-9a-f]{64}', key) and key == digest_legacy_key(claim), 'reservation_key_binding')
        plan_path = Path(claim['plan_path'])
        require(plan_path in paths and plan_path.name == 'PLAN.json', 'reservation_plan_inventory')
        metadata.read(plan_path, claim['plan_sha256'])
        job = plan_path.parent
        require(job.name.endswith('_job_' + key), 'reservation_job_binding')
        used_jobs.add(job)
        launch = launches.get(job)
        if launch is not None:
            require(launch['claim_sha256'] == metadata.hashes[str(claim_path)]
                and launch['plan_sha256'] == claim['plan_sha256']
                and launch['config_sha256'] == claim['config_sha256'], 'launch_claim_binding')
            exit_record = metadata.read(job / 'EXIT.json')
            require(type(exit_record['exit_code']) is int, 'terminal_exit_code')
        if key in completed:
            require(key not in failures and launch is not None, 'ambiguous_completed_reservation')
            terminal = metadata.read(completed[key])
            require(terminal['status'] == 'COMPLETE' and terminal['key'] == key
                and terminal['claim_sha256'] == metadata.hashes[str(claim_path)]
                and exit_record['exit_code'] == 0, 'ledger_completion_binding')
        else:
            require(len(failures.get(key, [])) == 1, 'unresolved_reservation')
            failure_path, failure = failures[key][0]
            if failure_path == job / 'FAILED.json':
                require(launch is not None and failure.get('automatic_retry') is False,
                    'failed_job_requires_exit_no_retry')
            else:
                require(launch is None and failure_path == job.parent / (job.name.split('_job_')[0] + '.FAILED.json')
                    and failure['status'] == 'ADMISSION_FAILED_NO_MODEL_REPLAY', 'admission_failure_scope')
            failed_count += 1
    require(set(launches) <= used_jobs and set(plans) <= used_jobs, 'unreserved_job_ambiguity')
    require(set(failures) <= set(claims), 'orphan_failure')
    return dict(reservations=len(claims), completed=len(completed), terminal_failed=failed_count)


def digest_legacy_key(claim):
    value = {key: claim[key] for key in ('lineage_id', 'commit_sha256', 'corpus_sha256')}
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def snapshot(request, now):
    validate_request(request)
    metadata = Metadata()
    phase = metadata.read(PHASE_CONFIG, PHASE_SHA256)
    config = metadata.read(SEGMENT_CONFIG, SEGMENT_SHA256)
    require(phase['output_root'] == str(PHASE_ROOT) and config['output_root'] == str(SCHEDULER_ROOT)
        and config['ledger_root'] == str(LEDGER_ROOT), 'pinned_output_scopes')
    phase_identity, scheduler_identity = request['phase_identity'], request['scheduler_identity']
    require(scheduler_identity['cmdline'] == [config['python'], '-B', '-m',
        'gpu.orch_r130_checkpoint_scheduler', 'run', '--config', str(SEGMENT_CONFIG)], 'scheduler_CPU_command')
    require(phase_identity['cmdline'] == [config['python'], '-B',
        str(ROOT / 'successor_tools_v2/gpu/orch_r130_successor_phase.py'), 'node', '--config', str(PHASE_CONFIG)],
        'original_phase_command')
    require(scheduler_identity['cwd'] == config['source_root'], 'exact_scheduler_cwd')
    for name, expected, checksum in [('phase', phase_identity, PHASE_SHA256),
            ('scheduler', scheduler_identity, SEGMENT_SHA256)]:
        require(process_identity(expected['pid']) == expected, 'exact_' + name + '_identity')
        environment = process_environment(expected['pid'])
        binding = 'R130_PHASE_SHA256' if name == 'phase' else 'R130_SCHEDULER_ADMISSION_SHA256'
        require(environment.get('CUDA_VISIBLE_DEVICES') == '' and environment.get(binding) == checksum,
            'CPU_only_' + name + '_environment')
    require(not scheduler_children(scheduler_identity['pid']), 'scheduler_has_children')
    phase_started = metadata.read(PHASE_ROOT / 'STARTED.json')
    scheduler_started = metadata.read(SCHEDULER_ROOT / 'STARTED.json')
    require(phase_started['identity'] == legacy(phase_identity) and phase_started['phase_sha256'] == PHASE_SHA256,
        'phase_STARTED_binding')
    require(scheduler_started['identity'] == legacy(scheduler_identity)
        and scheduler_started['config_sha256'] == SEGMENT_SHA256, 'scheduler_STARTED_binding')
    phase_status = metadata.latest(PHASE_ROOT, now)
    scheduler_status = metadata.latest(SCHEDULER_ROOT, now)
    require(phase_status['status'] == 'SEGMENT_RUNNING' and phase_status['phase_sha256'] == PHASE_SHA256
        and phase_status['active_config_path'] == str(SEGMENT_CONFIG)
        and phase_status['active_config_sha256'] == SEGMENT_SHA256, 'current_phase_segment_binding')
    require(scheduler_status['status'] == 'BOUNDED_POLLING' and scheduler_status['config_sha256'] == SEGMENT_SHA256,
        'current_scheduler_status_binding')
    require(phase_status['hard_end_unix'] == phase['hard_end_unix']
        and scheduler_status['hard_end_unix'] == config['hard_end_unix']
        and phase_status['next_dispatch_unix'] == scheduler_status['next_dispatch_unix'], 'current_deadline_binding')
    paths = inventory()
    require(PHASE_ROOT / 'SEGMENT_02.LAUNCH.json' in paths, 'phase_launch_missing')
    counts = ledger_check(metadata, paths, scheduler_identity)
    seeds = scheduler_status['baseline_completed_checkpoints']
    require(type(seeds) is int and seeds == 6, 'original_six_seed_metadata')
    require(phase_status['reserved_checkpoint_count'] == counts['reservations'] + seeds
        and phase_status['completed_checkpoint_count'] == scheduler_status['completed_checkpoint_count']
        == counts['completed'] + seeds, 'status_ledger_counts_disagree')
    require(metadata.latest(PHASE_ROOT, time.time()) == phase_status
        and metadata.latest(SCHEDULER_ROOT, time.time()) == scheduler_status, 'status_changed_during_inventory')
    require(inventory() == paths, 'inventory_changed')
    return dict(request_sha256=digest(request), metadata_sha256=metadata.hashes,
        inventory=[str(path) for path in paths], ledger=counts,
        phase_identity=phase_identity, scheduler_identity=scheduler_identity,
        dispatch_unix=scheduler_status['next_dispatch_unix'],
        deadline_unix=min(phase['hard_end_unix'], config['hard_end_unix']))


def fresh(snapshot_value, now):
    require(finite(now) and snapshot_value['dispatch_unix'] - now > DISPATCH_MARGIN
        and snapshot_value['deadline_unix'] - now > DISPATCH_MARGIN, 'final_dispatch_deadline_margin')


def output_path(output):
    output = no_symlinks(output)
    require(not output.is_relative_to(ROOT), 'old_artifacts_are_read_only')
    return output


def observe(request, output):
    output = output_path(output)
    output.mkdir(mode=0o700, exist_ok=False)
    started = time.time()
    result = dict(schema=SCHEMA, output=str(output), request=request, request_sha256=digest(request), observed_unix=started,
        helper_sha256=hashlib.sha256(read_bytes(Path(__file__).absolute())).hexdigest(), signal_sent=False)
    try:
        before = snapshot(request, started)
        require(snapshot(request, time.time()) == before, 'observation_changed')
        fresh(before, time.time())
        require(0 <= time.time() - started <= EXECUTION_MAX_SECONDS, 'observation_took_too_long')
        result.update(status='ELIGIBLE_OBSERVATION_ONLY', snapshot=before, snapshot_sha256=digest(before))
    except (ValueError, KeyError, TypeError, OSError) as error:
        result.update(status='DEFER_WITHOUT_SIGNAL', reason=str(error))
    write_once(output / 'OBSERVATION.json', result)
    return result


def execute(output, approval, approval_sha256):
    output = output_path(output)
    require(output.is_dir() and output.stat().st_uid == os.getuid()
        and output.stat().st_mode & 0o077 == 0, 'private_owned_operation_directory')
    try:
        write_once(output / 'EXECUTION_CLAIM.json', dict(schema=SCHEMA, action=ACTION, observed_unix=time.time()))
    except FileExistsError:
        return dict(status='ALREADY_CONSUMED_NO_RETRY', signal_sent=False)
    descriptor = None
    attempted = False
    wall, monotonic = time.time(), time.monotonic()
    result = dict(schema=SCHEMA, status='DEFER_WITHOUT_SIGNAL', signal_sent=False, retirement_verified=False)
    try:
        raw = read_bytes(output / 'OBSERVATION.json')
        observed = document(raw)
        require(observed['status'] == 'ELIGIBLE_OBSERVATION_ONLY' and observed['schema'] == SCHEMA,
            'eligible_observation_required')
        require(observed['output'] == str(output), 'caller_stable_output_binding')
        request, bound = observed['request'], observed['snapshot']
        result['operation_id'] = request['operation_id']
        approval_raw = read_bytes(approval)
        require(hashlib.sha256(approval_raw).hexdigest() == approval_sha256, 'external_approval_bytes_binding')
        approved = document(approval_raw)
        require(set(approved) == {'schema', 'operation_id', 'action', 'approved_by', 'cpu_tests_passed',
            'provenance_passed', 'observation_sha256', 'request_sha256', 'snapshot_sha256',
            'helper_sha256', 'issued_unix', 'expires_unix'}, 'approval_fields')
        require(approved['schema'] == APPROVAL_SCHEMA and approved['approved_by'] == 'Main'
            and approved['action'] == ACTION and approved['cpu_tests_passed'] is True
            and approved['provenance_passed'] is True, 'Main_CPU_provenance_approval_required')
        require(approved['operation_id'] == request['operation_id']
            and approved['observation_sha256'] == hashlib.sha256(raw).hexdigest()
            and approved['request_sha256'] == observed['request_sha256'] == digest(request)
            and approved['snapshot_sha256'] == observed['snapshot_sha256'] == digest(bound)
            and approved['helper_sha256'] == observed['helper_sha256']
            == hashlib.sha256(read_bytes(Path(__file__).absolute())).hexdigest(), 'approval_exact_scope_binding')
        require(all(finite(approved[key]) for key in ('issued_unix', 'expires_unix'))
            and observed['observed_unix'] <= approved['issued_unix'] <= wall < approved['expires_unix']
            <= observed['observed_unix'] + APPROVAL_MAX_AGE, 'approval_freshness')
        require(snapshot(request, time.time()) == bound, 'approved_snapshot_changed')
        descriptor = os.pidfd_open(bound['scheduler_identity']['pid'], 0)
        write_once(output / 'INTENT.json', dict(schema=SCHEMA, status='INTENTIONAL_IDLE_HANDOFF',
            operation_id=request['operation_id'], approval_sha256=approval_sha256,
            observation_sha256=approved['observation_sha256'], action=ACTION,
            scheduler_identity=bound['scheduler_identity'], scientific_failure=False,
            observed_unix=time.time(), automatic_retry=False))
        require(snapshot(request, time.time()) == bound, 'final_snapshot_changed')
        require(process_identity(bound['phase_identity']['pid']) == bound['phase_identity']
            and process_identity(bound['scheduler_identity']['pid']) == bound['scheduler_identity'],
            'final_process_identity_changed')
        require(not scheduler_children(bound['scheduler_identity']['pid']), 'final_scheduler_children')
        now, elapsed = time.time(), time.monotonic() - monotonic
        fresh(bound, now)
        require(0 <= elapsed <= EXECUTION_MAX_SECONDS and wall <= now
            and abs((now - wall) - elapsed) <= 1
            and approved['issued_unix'] <= now < approved['expires_unix'], 'final_clock_and_approval_freshness')
        attempted = True
        signal.pidfd_send_signal(descriptor, signal.SIGINT, None, 0)
        result.update(status='INTENTIONAL_IDLE_HANDOFF', signal_sent=True, scientific_failure=False,
            outcome='SIGINT_SENT_RETIREMENT_UNVERIFIED', automatic_retry=False)
    except (ValueError, KeyError, TypeError, OSError, AttributeError) as error:
        result.update(status='SIGNAL_OUTCOME_UNKNOWN_NO_RETRY' if attempted else 'DEFER_WITHOUT_SIGNAL',
            reason=str(error), automatic_retry=False)
    finally:
        if descriptor is not None:
            os.close(descriptor)
    write_once(output / 'RESULT.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action', required=True)
    observation = commands.add_parser('observe')
    observation.add_argument('--request', type=Path, required=True)
    observation.add_argument('--output', type=Path, required=True)
    execution = commands.add_parser('execute')
    execution.add_argument('--output', type=Path, required=True)
    execution.add_argument('--approval', type=Path, required=True)
    execution.add_argument('--approval-sha256', required=True)
    args = parser.parse_args()
    if args.action == 'observe':
        result = observe(document(read_bytes(args.request)), args.output)
    else:
        result = execute(args.output, args.approval, args.approval_sha256)
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return 0 if result['status'] in ('ELIGIBLE_OBSERVATION_ONLY', 'INTENTIONAL_IDLE_HANDOFF') else 2


if __name__ == '__main__':
    raise SystemExit(main())
