"""Prospective keyed continuation of ONE existing exhaustion ledger; no auto-allocation."""

import argparse
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import time
import urllib.error

from gpu import orch_continual_exhaustion_publish as old
from gpu import orch_continual_exhaustion_publish_keyed as keyed


PROGRAM = 'gpu.orch_continual_exhaustion_keyed_runtime'
OLD_PROGRAM = 'gpu.orch_continual_exhaustion_publish'
DEADLINE = 1789459200.0
CUTOFF = DEADLINE - 660
SCOPE = 'NEXT_NEVER_REVIEWED_BATCHES_SAME_EXHAUSTION_LEDGER_KEYED_TRANSPORT'
FROZEN = ('REGISTRATION.json', 'SOURCE_REGISTRY.json', 'PUBLISHER_REGISTRY.json',
          'EXCLUSIONS.json', 'NATIVE_READY.json')
R106_ADDENDUM = '''
PROSPECTIVE R106 INTERPRETATION (no new acceptance threshold):
Branching includes valid checks, judgments, what-ifs and associative departures
returning to the main computation, not a requirement for two same-given methods.
Use has_meaningful_branch for that broader interpretation. Keep worked-method
counts separate. Describe actual checks/judgments in the existing approach fields
and reason; INTERPRETATION_CHECK can cover these non-method departures.
Distinguish MID-SOLUTION departure/return from terminal Check/verification or
aside. A terminal check is not mid-solution merely because FINAL follows it.
Do not infer positive mid-solution counts from headings or broad branch presence.
Grounding, arithmetic, unsupported claims, coherence and repetition remain
separate assessments. Never fail solely for a considered-and-rejected path.
No new branch, method, length, first-person or composition acceptance threshold.
Unsampled rows remain UNREVIEWED with semantic measurements UNKNOWN.
Return the exact integer row_key once per supplied row; do not return hashes.
The host binds identity. Read all source text and preserve exact evidence_line_ids.
independent_answer remains a canonical numeric string; never repair a wrong answer.
'''
require, read, sha, write_once = old.policy.require, old.read, old.sha, old.write_once
FROZEN_VALIDATOR = old.validate_reviews


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    allow_nan=False).encode()).hexdigest()


def identity(pid):
    root = Path('/proc') / str(pid)
    if not root.exists():
        return None
    try:
        return dict(pid=pid, uid=root.stat().st_uid,
            start_ticks=int((root / 'stat').read_text().rsplit(')', 1)[1].split()[19]),
            boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
    except FileNotFoundError:
        return None


def worker_scan():
    active, unreadable = [], []
    for root in Path('/proc').iterdir():
        if not root.name.isdigit() or int(root.name) == os.getpid():
            continue
        try:
            args = (root / 'cmdline').read_bytes().decode(errors='replace').split('\0')
            if OLD_PROGRAM in args or PROGRAM in args:
                current = identity(int(root.name))
                if current:
                    active.append(current)
        except (FileNotFoundError, ProcessLookupError):
            continue
        except PermissionError:
            unreadable.append(int(root.name))
    return dict(active=active, unreadable_pids=unreadable)


def packet_rows(packet):
    return [dict(target=''.join(line['text'] for line in row['target_source_lines']),
        target_sha256=row['target_sha256'], gold=row['gold'], student_prefix_sha256=row['student_prefix_sha256'],
        provenance=dict(raw_call_sha256=row['raw_call_sha256'])) for row in packet]


def model_packet(packet):
    require(len(packet) == 6, 'exact_six_row_group')
    return [dict({key: value for key, value in row.items() if key not in keyed.HASH_FIELDS}, row_key=index)
            for index, row in enumerate(packet)]


def validate_result(packet, result, expected_packet_sha256):
    require(digest(packet) == expected_packet_sha256, 'immutable_full_packet_mismatch')
    rows = packet_rows(packet)
    reviews = deepcopy(result['reviews'])
    keys = [review.get('row_key') for review in reviews]
    require(all(type(key) is int for key in keys) and sorted(keys) == list(range(len(rows))),
            'exact_unique_response_keys')
    for review in reviews:
        require(not any(field in review for field in keyed.HASH_FIELDS), 'model_hash_fields_forbidden')
        row = rows[review.pop('row_key')]
        review.update(target_sha256=row['target_sha256'], student_prefix_sha256=row['student_prefix_sha256'],
                      raw_call_sha256=row['provenance']['raw_call_sha256'])
    return FROZEN_VALIDATOR(rows, dict(reviews=reviews))


def review_instructions(base):
    replacements = {
        'Copy all hashes exactly and\nreturn every supplied row once.':
            'Return each supplied integer row_key exactly once; never return hashes.',
        'has_meaningful_branch measures whether a consequential alternative was actually\nexamined and evaluated, not merely mentioned.':
            'has_meaningful_branch follows the prospective R106 broad departure/check interpretation below.',
        'Keep has_meaningful_branch as the legacy alternative/rejection measurement, not a two-method claim.':
            'For this prospective keyed version, has_meaningful_branch follows R106, not the legacy alternative-only definition.'}
    for previous, replacement in replacements.items():
        require(base.count(previous) == 1, 'pinned_instruction_replacement_binding')
        base = base.replace(previous, replacement)
    return base + R106_ADDENDUM


def validate_allocation(allocation, config, config_sha256, now):
    require(allocation.get('approved_by') == 'MAIN' and allocation.get('scope') == SCOPE
            and allocation.get('dispatch_authorized') is True, 'explicit_main_allocation_required')
    require(allocation['config_sha256'] == config_sha256 and allocation['deadline_unix'] == DEADLINE
            and allocation['dispatch_cutoff_unix'] == CUTOFF and now < DEADLINE, 'allocation_bounds_binding')
    require(allocation['old_reserved_preserved'] == 96 and allocation['shared_limit'] == 128
            and allocation['aggregate_allocation_ceiling'] == 256, 'same_pool_never_new128')
    require(allocation['predecessor'] == config['predecessor']
            and allocation['native_root'] == config['native_root'], 'exact_predecessor_and_shared_root')
    require(re.fullmatch(r'[a-zA-Z0-9_-]{8,80}', allocation['allocation_id']) is not None,
            'bounded_allocation_id')
    require(len(allocation['quiescent_native_state_sha256']) == 64, 'quiescent_state_binding_required')


def verify_config(path, side):
    config = read(path)
    require(config['schema'] == 'ORCH_EXHAUSTION_KEYED_CONTINUATION_CONFIG_V1'
            and config['deadline_unix'] == DEADLINE and config['dispatch_cutoff_unix'] == CUTOFF
            and config['shared_limit'] == 128 and config['old_reserved_preserved'] == 96,
            'inherited_bounds_no_reset')
    require(not any(name in config for name in ('initial_reserved', 'new_budget', 'first_packet_path')),
            'fresh_ledger_fields_forbidden')
    runtime = Path(config['vm_runtime'] if side == 'vm' else config['native_runtime'])
    require(Path(__file__).resolve().is_relative_to(runtime / 'source'), 'outside_git_pinned_runtime_only')
    require(all(sha(runtime / name) == value for name, value in config[side + '_files'].items()),
            'pinned_runtime_source_drift')
    require(sha(runtime / 'source/gpu/orch_continual_exhaustion_publish.py') ==
            '4c7e53ea0ac06234be30dcee48c84f08cfe30f7fa0187e65a644d27eec3fc5e7', 'original_semantic_runtime_pin')
    return config


def native_state(root):
    old.verify_native(root)
    budget = read(root / 'BUDGET.json')
    require(type(budget['reserved']) is int and 4 <= budget['reserved'] <= 128
            and budget['reserved'] % 2 == 0 and budget['limit'] == 128
            and budget['old_reserved'] == 96, 'live_ledger_not_reset')
    batches, pending, reservations = [], [], []
    all_pass, accepted_pass, admitted = set(), set(), set()
    for batch in sorted(root.glob('orch_continual_exhaustion_feed_batch_*')):
        if not batch.is_dir():
            continue
        number = int(batch.name.rsplit('_', 1)[1])
        entry = dict(number=number, reserved=False)
        if (batch / 'REVIEW_RESERVATION.json').exists():
            entry['reserved'] = True
            calls = read(batch / 'REVIEW_RESERVATION.json')['calls']
            reservations.extend(calls)
            decision = batch / 'RESULT_REDUCTION.json'
            failed = any((batch / 'PROVIDER_UPLOAD').rglob('*FAILED*.json'))
            verified = (batch / 'PROVIDER_UPLOAD_VERIFIED.json').exists()
            if not (verified and (decision.exists() or failed)):
                pending.append(number)
            if decision.exists():
                result = read(decision)
                all_pass.update(result['all_adjudicated_sample_pass_sha256s'])
                accepted_pass.update(result['accepted_sample_pass_sha256s'])
                admitted.update(result['admitted_target_sha256s'])
            entry['preserved_hashes'] = {str(path.relative_to(batch)): sha(path) for path in sorted(batch.rglob('*.json'))
                if path.name in ('REVIEW_RESERVATION.json', 'RESULT_REDUCTION.json', 'PROVIDER_UPLOAD_VERIFIED.json',
                                 'SAMPLED_REVIEWS.json', 'FAILED.json', 'PROCESS_FAILED.json')}
        batches.append(entry)
    require(sorted(reservations) == list(range(1, budget['reserved'] + 1)), 'complete_charged_reservation_history')
    return dict(budget=budget, budget_sha256=sha(root / 'BUDGET.json'), seen_sha256=sha(root / 'SEEN.json'),
        seen_count=len(read(root / 'SEEN.json')), frozen_hashes={name: sha(root / name) for name in FROZEN},
        next_number=max((item['number'] for item in batches), default=-1) + 1,
        pending_reserved_batches=pending, batches=batches,
        all_sample_pass=sorted(all_pass), accepted_sample_pass=sorted(accepted_pass), admitted_targets=sorted(admitted))


def assert_quiescent(state, scan, allocation):
    require(not scan['active'] and not scan['unreadable_pids'], 'all_uid_native_workers_must_be_drained')
    require(not state['pending_reserved_batches'], 'unsettled_review_or_upload_no_handoff')
    require(digest(state) == allocation['quiescent_native_state_sha256'], 'stale_quiescent_state_no_rewind')


def take_old_lock(config):
    require(identity(config['predecessor']['pid']) != config['predecessor'], 'predecessor_still_running_no_stop_authority')
    scan = worker_scan()
    require(not scan['active'] and not scan['unreadable_pids'], 'vm_provider_or_controller_not_drained')
    path = Path(config['predecessor_runtime']) / 'CONTROLLER.lock'
    stat = path.stat()
    require([stat.st_dev, stat.st_ino] == config['predecessor_lock_inode'], 'original_lock_inode_required')
    stream = path.open('r+')
    try:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BaseException:
        stream.close()
        raise
    require(identity(config['predecessor']['pid']) != config['predecessor'], 'predecessor_identity_race')
    return stream


def native_phase(config, allocation, allocation_sha, phase, number=None):
    root = Path(config['native_root'])
    if phase == 'inspect':
        state = native_state(root)
        return dict(state=state, state_sha256=digest(state), workers=worker_scan())
    old.verify_native(root)
    claim_path = root / 'KEYED_CONTINUATION_CLAIM.json'
    if phase == 'claim':
        with (root / 'BUDGET.lock').open('a') as stream:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            state = native_state(root)
            assert_quiescent(state, worker_scan(), allocation)
            write_once(claim_path, dict(allocation_sha256=allocation_sha, state=state,
                allocation_id=allocation['allocation_id'], claimed_unix=time.time()))
        return state
    claim = read(claim_path)
    require(claim['allocation_sha256'] == allocation_sha and claim['allocation_id'] == allocation['allocation_id'],
            'single_native_continuation_owner')
    require(type(number) is int and number >= claim['state']['next_number'] and number > 1,
            'never_revisit_failed_or_prior_batches')
    batch = root / f'orch_continual_exhaustion_feed_batch_{number:03d}'
    if phase == 'prepare':
        capture = old.native_prepare(root, number)
        if 'packets' in capture:
            write_once(batch / 'KEYED_DISPATCH_REGISTRATION.json', dict(allocation_sha256=allocation_sha,
                packet_sha256s=[digest(packet) for packet in capture['packets']],
                sample_registration_sha256=sha(batch / 'SAMPLE_REGISTRATION.json'),
                r106_instruction_sha256=digest(R106_ADDENDUM), semantic_thresholds_unchanged=True))
        return capture
    registration = read(batch / 'KEYED_DISPATCH_REGISTRATION.json')
    require(registration['allocation_sha256'] == allocation_sha
            and registration['sample_registration_sha256'] == sha(batch / 'SAMPLE_REGISTRATION.json'),
            'prospective_keyed_registration')
    if phase == 'reserve':
        return old.native_reserve(root, number)
    if phase == 'verify_upload':
        return old.native_verify_upload(root, number)
    require(phase == 'finalize', 'known_native_phase')
    require(not (batch / 'RESULT_REDUCTION.json').exists(), 'single_finalize_no_salvage')
    packets = [read(batch / f'REVIEW_PACKET_{group}.json') for group in range(2)]
    for group, packet in enumerate(packets):
        uploaded = batch / 'PROVIDER_UPLOAD' / f'batch_{number:03d}_{group}'
        require(read(uploaded / 'HOST_REGISTRY.json') == packet
                and digest(packet) == registration['packet_sha256s'][group], 'native_host_registry_join')
        require(read(uploaded / 'PACKET.json') == model_packet(packet), 'exact_model_packet_projection')
        require(not list(uploaded.rglob('*FAILED*.json')), 'failed_review_never_finalized')

    def bound_validate(rows, result):
        matches = [packet for packet in packets if packet_rows(packet) == [dict(target=row['target'],
            target_sha256=row['target_sha256'], gold=row['gold'], student_prefix_sha256=row['student_prefix_sha256'],
            provenance=dict(raw_call_sha256=row['provenance']['raw_call_sha256'])) for row in rows]]
        require(len(matches) == 1, 'exact_native_sample_group_join')
        return validate_result(matches[0], result, digest(matches[0]))

    validator = old.validate_reviews
    try:
        old.validate_reviews = bound_validate
        result = old.native_finalize(root, number)
    finally:
        old.validate_reviews = validator
    measurement = dict(schema='R106_KEYED_PROSPECTIVE_MEASUREMENT_INTERPRETATION_V1',
        allocation_sha256=allocation_sha, keyed_registration_sha256=sha(batch / 'KEYED_DISPATCH_REGISTRATION.json'),
        result_sha256=sha(batch / 'RESULT_REDUCTION.json'), historical_batches_reinterpreted=False,
        r106_broad_author_branch_count=result['legacy_meaningful_branch_label_count'],
        mid_solution_count=None, mid_solution_status='NOT_SEPARATELY_MEASURED_DO_NOT_INFER_FROM_BROAD_COUNT',
        method_counts='UNCHANGED_SEPARATE_WORKED_METHOD_MEASUREMENTS', acceptance_thresholds_unchanged=True,
        unsampled_measurements='UNKNOWN')
    write_once(batch / 'KEYED_MEASUREMENT_RECEIPT.json', measurement)
    return dict(result, measurement_receipt_path=str(batch / 'KEYED_MEASUREMENT_RECEIPT.json'),
                measurement_receipt_sha256=sha(batch / 'KEYED_MEASUREMENT_RECEIPT.json'))


def failure(error):
    if isinstance(error, urllib.error.HTTPError):
        return dict(stage='HTTP_TRANSPORT', type=type(error).__name__, status=error.code)
    if isinstance(error, ValueError):
        reason = str(error)
        return dict(stage='RESPONSE_OR_BINDING_VALIDATION', type='ValueError',
                    reason=reason if re.fullmatch(r'[a-zA-Z0-9_:.-]{1,120}', reason) else 'validation_failed')
    return dict(stage='PROCESS_OR_NETWORK_FAILURE', type=type(error).__name__)


def provider(config, allocation_sha, number, group, permit_sha):
    directory = Path(config['vm_runtime']) / f'review_batch_{number:03d}' / 'review_workspace' / f'batch_{number:03d}_{group}'
    require(group in (0, 1) and number > 1 and time.time() < CUTOFF, 'provider_bound_group_and_cutoff')
    require(sha(directory / 'PERMIT.json') == permit_sha, 'exact_single_dispatch_permit')
    permit = read(directory / 'PERMIT.json')
    require(permit['allocation_sha256'] == allocation_sha and permit['number'] == number and permit['group'] == group,
            'allocation_dispatch_binding')
    packet = read(directory / 'HOST_REGISTRY.json')
    require(digest(packet) == permit['packet_sha256'] and read(directory / 'PACKET.json') == model_packet(packet),
            'provider_registry_and_model_projection')
    require(read(directory / 'SCHEMA.json') == keyed.keyed_schema(6)
            and (directory.parent / 'REVIEW_INSTRUCTIONS.md').read_text() ==
                review_instructions((Path(config['vm_runtime']) / 'REVIEW_INSTRUCTIONS.md').read_text()),
            'exact_prospective_schema_and_instructions')
    old.publisher.ROOT = directory.parent.parent
    validator = old.validate_reviews
    try:
        old.validate_reviews = lambda rows, result: validate_result(packet, result, permit['packet_sha256'])
        return old.review_group_http(number, group, packet_rows(packet))
    except Exception as error:
        write_once(directory / 'KEYED_FAILED.json', dict(failure(error), retries=0, raw_preserved=True))
        raise
    finally:
        old.validate_reviews = validator


class Transport:
    def __init__(self, config, config_path, allocation, allocation_path, allocation_sha):
        self.config, self.config_path = config, config_path
        self.allocation, self.allocation_path, self.allocation_sha = allocation, allocation_path, allocation_sha
        self.target = os.environ['ORCH_CONTINUAL_BATCH_SSH_TARGET']

    def ssh(self, command):
        remaining = DEADLINE - time.time()
        require(remaining > 0, 'original_deadline_expired')
        return subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15', self.target, command],
            check=True, text=True, capture_output=True, timeout=min(240, remaining))

    def rpc(self, phase, number=None):
        runtime = self.config['native_runtime']
        args = ['env', 'CUDA_VISIBLE_DEVICES=', 'HF_HUB_OFFLINE=1', 'TRANSFORMERS_OFFLINE=1',
            'PYTHONPATH=' + runtime + '/source', self.config['native_python'], '-B', '-m', PROGRAM,
            'native', '--phase', phase, '--config', runtime + '/CONFIG.json',
            '--allocation', runtime + '/ALLOCATION.json', '--allocation-sha256', self.allocation_sha]
        if number is not None:
            args += ['--number', str(number)]
        return json.loads(self.ssh(shlex.join(args)).stdout)

    def upload(self, source, destination):
        remaining = DEADLINE - time.time()
        require(remaining > 0, 'original_deadline_expired')
        subprocess.run(['scp', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15', str(source),
            self.target + ':' + destination], check=True, capture_output=True, timeout=min(120, remaining))

    def review(self, number, group, directory):
        subprocess.run([sys.executable, '-B', '-m', PROGRAM, 'provider', '--config', str(self.config_path),
            '--allocation', str(self.allocation_path), '--allocation-sha256', self.allocation_sha,
            '--number', str(number), '--group', str(group), '--permit-sha256', sha(directory / 'PERMIT.json')],
            check=True, timeout=310, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def run(config, config_path, allocation, allocation_path, allocation_sha):
    runtime, reductions = Path(config['vm_runtime']), Path(config['reductions'])
    require(sha(Path(config['predecessor_runtime']) / 'CONFIG.json') == config['predecessor_config_sha256'],
            'predecessor_configuration_unchanged')
    predecessor_config = read(Path(config['predecessor_runtime']) / 'CONFIG.json')
    require(sha(predecessor_config['old_terminal_path']) == predecessor_config['old_terminal_sha256'],
            'original96_terminal_receipt_preserved')
    with take_old_lock(config), (runtime / 'CONTROLLER.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        transport = Transport(config, config_path, allocation, allocation_path, allocation_sha)
        inspected = transport.rpc('inspect')
        assert_quiescent(inspected['state'], inspected['workers'], allocation)
        state = transport.rpc('claim')
        started = time.time()
        write_once(runtime / 'HANDOFF.json', dict(predecessor=config['predecessor'], successor=identity(os.getpid()),
            inherited=state, allocation_sha256=allocation_sha, started_unix=started,
            old_lock_inode=config['predecessor_lock_inode'], no_reset=True))
        reductions.mkdir(parents=True, exist_ok=True)
        counters = {name: set(state[name]) for name in ('all_sample_pass', 'accepted_sample_pass', 'admitted_targets')}
        number, reserved = state['next_number'], state['budget']['reserved']
        while time.time() < CUTOFF and reserved < 128:
            available = int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines()
                                 if line.startswith('MemAvailable:'))) * 1024
            if available < 800 * 1024**2:
                time.sleep(min(30, max(0, CUTOFF - time.time())))
                continue
            local = runtime / f'review_batch_{number:03d}'
            try:
                capture = transport.rpc('prepare', number)
                packets = capture.pop('packets', None)
                write_once(reductions / f'CAPTURE_{number:03d}.json', capture)
                if packets is None:
                    number += 1
                    time.sleep(min(30, max(0, CUTOFF - time.time())))
                    continue
                budget = transport.rpc('reserve', number)
                require(budget['reserved'] == reserved + 2, 'shared_reservation_progress_no_reset')
                reserved = budget['reserved']
                write_once(reductions / f'RESERVATION_{number:03d}.json', budget)
                workspace = local / 'review_workspace'
                workspace.mkdir(parents=True, exist_ok=False)
                (workspace / 'REVIEW_INSTRUCTIONS.md').write_text(review_instructions((runtime / 'REVIEW_INSTRUCTIONS.md').read_text()))
                directories = []
                for group, packet in enumerate(packets):
                    directory = workspace / f'batch_{number:03d}_{group}'
                    directory.mkdir()
                    write_once(directory / 'HOST_REGISTRY.json', packet)
                    write_once(directory / 'PACKET.json', model_packet(packet))
                    write_once(directory / 'SCHEMA.json', keyed.keyed_schema(6))
                    write_once(directory / 'PERMIT.json', dict(number=number, group=group,
                        allocation_sha256=allocation_sha, packet_sha256=digest(packet),
                        charged_slot=reserved - 1 + group, maximum_output_tokens=8192, attempts=1, retries=0))
                    directories.append(directory)
                errors = []
                with ThreadPoolExecutor(max_workers=2 if available >= 2400 * 1024**2 else 1) as pool:
                    futures = [pool.submit(transport.review, number, group, directory)
                               for group, directory in enumerate(directories)]
                    for directory, future in zip(directories, futures):
                        try:
                            future.result()
                        except Exception as error:
                            record = read(directory / 'KEYED_FAILED.json') if (directory / 'KEYED_FAILED.json').exists() else failure(error)
                            write_once(directory / 'PROCESS_FAILED.json', record)
                            errors.append(record)
                upload_root = capture['native_batch_path'] + '/PROVIDER_UPLOAD'
                files = {str(path.relative_to(workspace)): path for path in workspace.rglob('*') if path.is_file()}
                inventory = {name: sha(path) for name, path in files.items()}
                write_once(workspace / 'UPLOAD_INVENTORY.json', inventory)
                transport.ssh('mkdir ' + shlex.quote(upload_root))
                for name, path in files.items():
                    destination = str(Path(upload_root) / name)
                    transport.ssh('mkdir -p ' + shlex.quote(str(Path(destination).parent)))
                    transport.upload(path, destination)
                transport.upload(workspace / 'UPLOAD_INVENTORY.json', upload_root + '/UPLOAD_INVENTORY.json')
                receipt = transport.rpc('verify_upload', number)
                require(receipt['inventory_sha256'] == sha(workspace / 'UPLOAD_INVENTORY.json'), 'exact_native_transfer_hash')
                write_once(reductions / f'TRANSFER_VERIFIED_{number:03d}.json', receipt)
                if errors:
                    write_once(reductions / f'FAILED_{number:03d}.json', dict(errors=errors, native_raw_preserved=True, retries=0))
                else:
                    result = transport.rpc('finalize', number)
                    write_once(reductions / f'RESULT_{number:03d}.json', result)
                    for name, field in (('all_sample_pass', 'all_adjudicated_sample_pass_sha256s'),
                        ('accepted_sample_pass', 'accepted_sample_pass_sha256s'), ('admitted_targets', 'admitted_target_sha256s')):
                        counters[name].update(result[field])
                    if result['decision']['accepted']:
                        with Path(config['journal']).open('a') as stream:
                            stream.write('\n[Builder — Laplace keyed continuation ready] ' + datetime.now(timezone.utc).isoformat()
                                + ' Native manifest ' + result['native_manifest_path'] + ' SHA256 ' + result['native_manifest_sha256']
                                + '; sampled/unsampled eligibility as bound in manifest; no ingestion claimed.\n')
                old.cleanup_verified_packets(local, receipt, sha(workspace / 'UPLOAD_INVENTORY.json'))
            except Exception as error:
                write_once(reductions / f'CONTINUATION_BLOCKED_{number:03d}.json', dict(failure(error), reserved=reserved,
                    temporary_packets_preserved=local.exists(), no_retry=True, no_budget_reset=True))
                return
            old.publisher.write(reductions / 'LIVE_STATUS.json', dict(observed_unix=time.time(), pid=os.getpid(),
                reserved=reserved, limit=128, old_reserved_preserved=96, deadline_unix=DEADLINE,
                counts={name: len(values) for name, values in counters.items()},
                sampled_pass_outside_accepted=len(counters['all_sample_pass'] - counters['accepted_sample_pass']),
                unsampled_in_accepted=len(counters['admitted_targets'] - counters['accepted_sample_pass']),
                inherited_counters=state, successor_wall_seconds=time.time() - started,
                original_publisher_started_unix=config['original_publisher_started_unix'],
                rates_not_inferred_from_mixed_clock_origins=True, r106_mid_solution_count='NOT_SEPARATELY_MEASURED'))
            number += 1
        write_once(reductions / 'WATCH_TERMINAL.json', dict(reserved=reserved, deadline_unix=DEADLINE,
            finished_unix=time.time(), pool_reset=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('native', 'run', 'provider'))
    parser.add_argument('--config', required=True, type=Path)
    parser.add_argument('--allocation', type=Path)
    parser.add_argument('--allocation-sha256')
    parser.add_argument('--phase', choices=('inspect', 'claim', 'prepare', 'reserve', 'verify_upload', 'finalize'))
    parser.add_argument('--number', type=int)
    parser.add_argument('--group', type=int)
    parser.add_argument('--permit-sha256')
    args = parser.parse_args()
    config = verify_config(args.config, 'native' if args.mode == 'native' else 'vm')
    allocation, allocation_sha = None, args.allocation_sha256
    if not (args.mode == 'native' and args.phase == 'inspect'):
        require(args.allocation is not None and allocation_sha is not None, 'no_implicit_allocation')
        require(sha(args.allocation) == allocation_sha, 'allocation_exact_bytes')
        allocation = read(args.allocation)
        validate_allocation(allocation, config, sha(args.config), time.time())
        if args.mode in ('run', 'provider') or args.phase in ('claim', 'prepare', 'reserve'):
            require(time.time() < CUTOFF, 'no_new_dispatch_or_reservation_after_cutoff')
    if args.mode == 'native':
        print(json.dumps(native_phase(config, allocation, allocation_sha, args.phase, args.number), sort_keys=True))
    elif args.mode == 'provider':
        provider(config, allocation_sha, args.number, args.group, args.permit_sha256)
    else:
        run(config, args.config, allocation, args.allocation, allocation_sha)


if __name__ == '__main__':
    main()
