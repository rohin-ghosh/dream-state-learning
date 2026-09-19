"""Seven concrete receiving hooks. Importing/constructing this module never launches."""

from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import time

from research_loop.workers.post_recovery_retention_boundary_20260918.boundary import (
    ObservationRace, Refusal, digest, file_bytes, plan_metadata_binding, read, require, same_boundary, sha,
    verify_source_only_plans)
from research_loop.workers.post_recovery_retention_boundary_20260918.operations import ReceivingHooks, process_identity


def write_once(path, document):
    path = Path(path)
    content = (json.dumps(document, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.exists():
        require(file_bytes(path) == content, 'immutable_receiving_artifact')
        return
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
    with os.fdopen(descriptor, 'wb') as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
    sync_directory(path.parent)


def sync_directory(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def preservation(candidate, selection):
    return dict(checkpoint=deepcopy(candidate['checkpoint']), coherent_state=deepcopy(candidate['resume_state']),
        journal_id=candidate['journal_id'], head_index=candidate['head_index'], head_sha256=candidate['head_sha256'],
        complete_index=candidate['complete_index'], complete_record_sha256=candidate['complete_sha256'],
        checkpoint_tail_selection=selection, saved_checkpoint_RNG_preserved=True,
        resident_after_checkpoint_RNG_captured=False, journal_changed=False, historical_rows_changed=False)


def parent_handoff_contract(binding, epoch_id):
    return dict(schema='PAIR_RETENTION_PARENT_REBIND_REQUIRED_V1', source_epoch=epoch_id,
        life_binding_sha256=digest(binding), old_native={key: binding[key]
            for key in ('pid', 'start_ticks', 'boot_id', 'guard_path', 'guard_sha256')},
        journal_root=binding['journal_root'], journal_id=binding['journal_id'], new_native=None,
        parent_owner_action_required=True, automatic_pid_adoption=False,
        preserve_existing_ledgers=True, replay_delivered_messages=False,
        required_before_native_handoff=['owner_bound_dependency_receipt', 'old_parent_delivery_fence',
            'zero_inflight_deliveries', 'durable_existing_ledger_pins'],
        required_before_parent_rebind=['verified_LOADED_receipt', 'exact_new_native_pid_start_boot_guard',
            'durable_RETENTION_SOURCE_ADOPTED_record', 'unchanged_ledgers_and_delivery_ids',
            'explicit_parent_owner_rebind_receipt'], parent_rebind_allowed=False)


class PairReceiver:
    def __init__(self, binding, staged, *, cpu_receipt_path, consumed_wall_receipt, python_executable,
            parent_dependency_receipt_path=None, checkpoint_probe=None, parent_owner=None, probe_timeout_seconds=120):
        self.binding, self.staged = deepcopy(binding), deepcopy(staged)
        self.reservation_budget = None
        self.source = Path(staged['new_source'])
        self.control = self.source.parent / 'control'
        self.cpu_receipt_path = Path(cpu_receipt_path)
        self.consumed = deepcopy(consumed_wall_receipt)
        self.python = str(python_executable)
        self.probe_override = checkpoint_probe
        self.parent_dependency_receipt_path = parent_dependency_receipt_path
        self.parent_owner = parent_owner
        require(0 < probe_timeout_seconds <= 120, 'bounded_CPU_probe_timeout')
        self.probe_timeout_seconds = probe_timeout_seconds
        self.prepared = None

    def verify_parent_dependencies(self, epoch_id):
        require(self.parent_dependency_receipt_path is not None, 'parent_owner_dependency_proof_required_before_handoff')
        owner = getattr(self, 'parent_owner', None)
        if owner is not None:
            try:
                proof = owner.check(self.binding, epoch_id)
            except (ValueError, OSError, TimeoutError) as error:
                raise Refusal('fresh_parent_owner_verification_failed:' + str(error)) from error
            require(proof['path'] == str(self.parent_dependency_receipt_path), 'same_original_parent_receipt_path')
            receipt = proof['receipt']
        else:
            receipt = read(self.parent_dependency_receipt_path)
        require(receipt['schema'] == 'PAIR_RETENTION_PARENT_DEPENDENCIES_V1'
            and receipt['life_binding_sha256'] == digest(self.binding) and receipt['source_epoch'] == epoch_id,
            'exact_parent_dependency_life_and_epoch')
        require(receipt['owner'] and receipt['delivery_fenced'] is True and receipt['inflight_deliveries'] == 0
            and receipt['durable'] is True and receipt['preserve_existing_ledgers'] is True
            and receipt['automatic_pid_adoption'] is False and receipt['replay_delivered_messages'] is False,
            'parent_owner_fenced_delivery_and_no_ledger_reset')
        require(receipt['ledger_pins'], 'original_parent_ledger_inventory_required')
        if owner is not None:
            return proof
        require(all(sha(path) == expected for path, expected in receipt['ledger_pins'].items()),
            'unchanged_parent_ledgers_and_delivery_ids')
        return dict(path=str(self.parent_dependency_receipt_path), sha256=sha(self.parent_dependency_receipt_path),
            receipt=receipt)

    def hooks(self):
        return ReceivingHooks(**{name: getattr(self, name) for name in ReceivingHooks.__dataclass_fields__})

    def environment(self):
        return dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1',
            PYTHONPATH=str(self.source), OMP_NUM_THREADS='1')

    def verify_prepared(self, prepared):
        require(self.parent_owner is not None, 'fresh_CPU_owner_bridge_required_before_wait_or_reservation')
        self.verify_parent_dependencies(prepared['epoch_id'])
        require(sha(self.binding['guard_path']) == self.binding['guard_sha256']
            == self.staged['old_guard_sha256'], 'exact_pair_old_guard')
        guard = read(self.binding['guard_path'])
        require(read(guard['plan_path']) == prepared['old_plan']
            and sha(guard['plan_path']) == guard['plan_sha256'], 'exact_pair_old_plan')
        require(str(Path(guard.get('copy_raw', prepared['old_plan']['root'])) / 'stream')
            == self.binding['journal_root'], 'preserve_guard_copy_raw_mapping')
        require(prepared['new_plan']['physical'] in (0, 1) and guard['resume'] is True,
            'pair_same_identity_resume_only')
        require(self.source.is_absolute() and self.source.resolve() == self.source
            and str(self.source) == prepared['new_plan']['source_root'], 'immutable_receiving_source')
        pins = {str(path.relative_to(self.source)): sha(path) for path in self.source.rglob('*.py')}
        require(pins == prepared['new_source_pins'] == self.staged['new_source_pins'], 'complete_staged_source_closure')
        changes = {name: dict(before=prepared['old_source_pins'].get(name), after=pins.get(name))
            for name in set(prepared['old_source_pins']) | set(pins)
            if prepared['old_source_pins'].get(name) != pins.get(name)}
        require(changes == self.staged['changed'], 'separately_bound_retention_plus_reader_source_delta')
        require({'gpu/checkpoint_tail_runtime.py', 'gpu/pair_retention_runtime.py'} <= set(pins)
            and b'bind_journal(journal_module.StreamJournal, plan)' in file_bytes(self.source / 'gpu/r232_recovery.py'),
            'reviewed_checkpoint_tail_port_required_no_full_replay_fallback')
        cpu = read(self.cpu_receipt_path)
        require(cpu.get('live_handoff_authorization') is not False, 'local_source_CPU_is_not_live_handoff_proof')
        require(cpu['passed'] is True and cpu['source_pins'] == pins and cpu['no_GPU_calls'] is True
            and cpu['checkpoint_tail_port_passed'] is True and cpu['pair_controls_passed'] is True,
            'actual_receiving_source_CPU_and_control_receipt')
        self.prepared = deepcopy(prepared)

    def dependents_clear(self, handle):
        require(handle.binding_sha256 == digest(self.binding), 'exact_owned_handle')
        try:
            actor = process_identity(self.binding['pid'])
            require(all(actor[key] == self.binding[key] for key in ('pid', 'uid', 'start_ticks', 'command')),
                'same_native_for_dependent_check')
            for task in (Path('/proc') / str(self.binding['pid']) / 'task').iterdir():
                for child in (task / 'children').read_text().split():
                    try:
                        if process_identity(int(child))['state'] not in ('Z', 'X'):
                            return False
                    except FileNotFoundError:
                        pass
            return True
        except FileNotFoundError:
            return False

    def _probe(self, mode, candidate, selection=None):
        budget = getattr(self, 'reservation_budget', None)
        if budget is not None:
            budget.check()
        if self.probe_override is not None:
            result = self.probe_override(mode, candidate, self.prepared['new_plan'], selection)
            if budget is not None:
                budget.check()
            return result
        request = dict(source=str(self.source), candidate=candidate, plan=self.prepared['new_plan'], selection=selection)
        path = self.control / 'cpu_requests' / (digest(request) + '.json')
        write_once(path, request)
        timeout = self.probe_timeout_seconds if budget is None else budget.timeout(self.probe_timeout_seconds)
        try:
            result = subprocess.run([self.python, '-B', str(Path(__file__).with_name('cpu_probe.py')),
                mode, '--request', str(path)], cwd=self.source, env=self.environment(),
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                timeout=timeout, check=True, close_fds=True)
        except subprocess.TimeoutExpired as error:
            write_once(path.with_name(path.stem + '.timeout.' + str(time.time_ns()) + '.json'),
                dict(mode=mode, timeout_seconds=timeout, native_actions=[],
                    status='CPU_PROBE_TIMEOUT_REVIEW_REQUIRED_NO_AUTOMATIC_RETRY',
                    reservation_active=budget is not None, helper_killed_and_waited=True))
            reason = ('CPU_probe_timeout_no_reservation_or_slow_replay_fallback' if budget is None
                else 'CPU_probe_timeout_reserved_review_required_no_automatic_retry')
            raise Refusal(reason) from error
        except subprocess.CalledProcessError as error:
            stderr = error.stderr or ''
            write_once(path.with_name(path.stem + '.failure.' + str(time.time_ns()) + '.json'),
                dict(mode=mode, returncode=error.returncode, stderr=stderr, native_actions=[]))
            race = stderr.rstrip().splitlines()[-1:] in (["ValueError: journal_changed_during_scan"],
                ["ValueError: unraced_tail_probe"], ["ValueError: same_resolved_pair_state"])
            if mode == 'tail' and race:
                raise ObservationRace('receiving_tail_raced_reobserve_same_native_handle') from error
            raise Refusal('CPU_probe_failed_no_handoff:' + stderr[-1000:]) from error
        if budget is not None:
            budget.check()
        write_once(path.with_suffix('.result.json'), dict(mode=mode, result=json.loads(result.stdout),
            stderr=result.stderr, source_pins=self.prepared['new_source_pins']))
        return json.loads(result.stdout)

    def verify_candidate_family(self, candidate):
        require(self.prepared is not None, 'static_source_control_checks_required_first')
        checkpoint = candidate['checkpoint']
        directory = Path(checkpoint['adapter_path']).parent
        require(directory.parent == Path(self.binding['journal_root']).parent / 'checkpoints'
            and directory.resolve() == directory and read(directory / 'COMMIT.json') == checkpoint,
            'exact_bound_checkpoint_family_before_reservation')
        require(Path(checkpoint['optimizer_rng_path']).parent == directory
            and type(checkpoint['optimizer_steps']) is int
            and ((checkpoint['optimizer_steps'] == 0) if self.prepared['new_plan']['physical'] == 1
                else checkpoint['optimizer_steps'] > 0), 'unchanged_checkpoint_family_control')

    def verify_checkpoint(self, candidate):
        require(self.prepared is not None, 'prepared_source_verified_first')
        checkpoint = candidate['checkpoint']
        directory = Path(checkpoint['adapter_path']).parent
        require(directory.parent == Path(self.binding['journal_root']).parent / 'checkpoints'
            and read(directory / 'COMMIT.json') == checkpoint, 'exact_original_checkpoint_COMMIT')
        paths = [directory / 'COMMIT.json', Path(checkpoint['optimizer_rng_path'])]
        paths.extend(sorted(Path(checkpoint['adapter_path']).iterdir()))
        pins = {str(path): sha(path) for path in paths}
        for path in paths:
            file_bytes(path, durable=True)
        for path in (Path(checkpoint['adapter_path']), directory, directory.parent):
            sync_directory(path)
        proof = self._probe('checkpoint', candidate)
        proof.update(complete_sha256=candidate['complete_sha256'], checkpoint_sha256=digest(checkpoint),
            durable_files_and_directories=True, files=pins)
        require(all(proof.get(key) is True for key in ('adapter_verified', 'optimizer_verified',
            'python_cpu_cuda_rng_verified', 'working_state_verified', 'no_GPU_calls')), 'CPU_restore_proof')
        return proof

    def prepare_receiver(self, candidate, prepared, proof):
        self.verify_prepared(prepared)
        plan = deepcopy(prepared['new_plan'])
        require('authorized_wall_extension' not in plan and 'checkpoint_tail_recovery' not in plan,
            'pair_sidecar_enrollment_no_new_plan_semantics')
        stamp = plan_metadata_binding(self.binding, candidate, prepared['old_plan'], plan)
        receipts = dict(consumed_wall_extension=dict(self.consumed, binding=stamp, durable=True))
        verify_source_only_plans(prepared['old_plan'], plan, binding=self.binding, candidate=candidate, receipts=receipts)
        root = Path(self.binding['journal_root'])
        sidecars = ([dict(name='correction_ledger.json', kind='R197_CORRECTION_CYCLE', required=True)]
            if (root / 'correction_ledger.json').exists() else [])
        selection = dict(policy='R233_PINNED_COMPLETE_TAIL_V1', root=str(root), journal_id=self.binding['journal_id'],
            complete_index=candidate['complete_index'], complete_sha256=candidate['complete_sha256'],
            life_id=plan['think_act_learn']['trial_id'], max_tail_records=2048, max_tail_bytes=1024**3,
            sidecars=sidecars, persist_complete_anchors=False)
        scanned = self._probe('tail', candidate, selection)
        require(scanned['restored_state_sha256'] == candidate['resume_state']['sha256']
            and scanned['head_sha256'] == candidate['head_sha256']
            and scanned['complete_index'] == candidate['complete_index']
            and scanned['complete_sha256'] == candidate['complete_sha256']
            and scanned['prefix_work'] == 'ALL_RETAINED_BYTES_HASHED_NO_HISTORICAL_BODY_JSON_REPLAY'
            and scanned['read_only'] is True and scanned['journal_writes'] == 0, 'actual_fast_checkpoint_tail_CPU_scan')
        require(not (self.control / 'RETENTION_HANDOFF.json').exists()
            and not (self.control / 'DISPATCH_CLAIM.json').exists(), 'no_receiving_writer_or_dispatch_already_armed')
        preserved = preservation(candidate, selection)
        snapshot = self.control / ('PRESERVATION.' + digest(preserved) + '.json')
        write_once(snapshot, preserved)
        self.control.mkdir(parents=True, exist_ok=True, mode=0o700)
        temporary = self.control / ('PRESERVATION.link.' + str(time.time_ns()))
        os.link(snapshot, temporary)
        os.replace(temporary, self.control / 'PRESERVATION.json')
        sync_directory(self.control)
        attempt = self.control / 'attempts' / str(time.time_ns())
        old_guard = read(self.binding['guard_path'])
        require(sha(old_guard['lease_path']) == old_guard['lease_sha256']
            and sha(old_guard['allocation_path']) == old_guard['allocation_sha256'], 'unchanged_original_admission_evidence')
        write_once(attempt / 'PLAN.json', plan)
        write_once(attempt / 'LEASE_WINDOW.json', read(old_guard['lease_path']))
        write_once(attempt / 'RECEIVING_CPU.json', read(self.cpu_receipt_path))
        allocation = read(old_guard['allocation_path'])
        allocation.update(plan_sha256=sha(attempt / 'PLAN.json'), declared_unix=time.time(),
            cpu_receipt_path=str(attempt / 'RECEIVING_CPU.json'), cpu_receipt_sha256=sha(attempt / 'RECEIVING_CPU.json'),
            cpu_tests_passed=True)
        write_once(attempt / 'ALLOCATION.json', allocation)
        guard = deepcopy(old_guard)
        guard.update(attempt_dir=str(attempt), plan_path=str(attempt / 'PLAN.json'), plan_sha256=sha(attempt / 'PLAN.json'),
            lease_path=str(attempt / 'LEASE_WINDOW.json'), lease_sha256=sha(attempt / 'LEASE_WINDOW.json'),
            allocation_path=str(attempt / 'ALLOCATION.json'), allocation_sha256=sha(attempt / 'ALLOCATION.json'),
            source_pins=prepared['new_source_pins'])
        write_once(attempt / 'GUARD.json', guard)
        guard_proof = self._probe('guard', candidate, dict(guard_path=str(attempt / 'GUARD.json')))
        require(guard_proof['validated'] is True and guard_proof['admission_bypassed'] is False
            and guard_proof['guard_sha256'] == sha(attempt / 'GUARD.json'), 'actual_receiving_guard_CPU_validation')
        parent = parent_handoff_contract(self.binding, prepared['epoch_id'])
        parent.update(receiving_guard_path=str(attempt / 'GUARD.json'), receiving_guard_sha256=sha(attempt / 'GUARD.json'),
            receiving_plan_sha256=sha(attempt / 'PLAN.json'), source_pins_sha256=digest(prepared['new_source_pins']),
            dependency_proof=self.verify_parent_dependencies(prepared['epoch_id']))
        write_once(attempt / 'PARENT_REBIND_REQUIRED.json', parent)
        receiver = dict(source_epoch=prepared['epoch_id'], plan=plan, plan_sha256=digest(plan),
            plan_metadata_receipts=receipts, resume_state_sha256=candidate['resume_state']['sha256'],
            checkpoint_sha256=digest(candidate['checkpoint']), same_journal_root=self.binding['journal_root'],
            rescans_original_inbox=True, no_model_load_before_writer_lock=True, deadline_unix=self.binding['hard_end_unix'],
            source_adoption_not_wall_extension=True, preservation_sha256=sha(self.control / 'PRESERVATION.json'),
            guard_path=str(attempt / 'GUARD.json'), candidate=candidate, checkpoint_tail_receipt=scanned,
            parent_handoff_path=str(attempt / 'PARENT_REBIND_REQUIRED.json'), parent_rebind_allowed=False,
            artifact_pins={str(path): sha(path) for path in attempt.iterdir() if path.is_file()})
        write_once(attempt / 'RECEIVER.json', receiver)
        return receiver

    def recheck_checkpoint(self, proof, frozen):
        require(proof['complete_sha256'] == frozen['complete_sha256']
            and proof['checkpoint_sha256'] == digest(frozen['checkpoint']), 'same_saved_checkpoint_proof')
        require(all(sha(path) == expected for path, expected in proof['files'].items()), 'unchanged_checkpoint_files')

    def verify_receiver(self, receiver, frozen):
        require(self.parent_owner is not None, 'fresh_CPU_owner_bridge_required_before_dispatch')
        parent = read(receiver['parent_handoff_path'])
        require(self.verify_parent_dependencies(receiver['source_epoch']) == parent['dependency_proof'],
            'same_parent_dependency_proof_before_dispatch')
        same_boundary(receiver['candidate'], frozen)
        require(all(sha(path) == expected for path, expected in receiver['artifact_pins'].items()), 'immutable_receiving_artifacts')
        require(sha(self.control / 'PRESERVATION.json') == receiver['preservation_sha256']
            and read(self.control / 'PRESERVATION.json')['checkpoint'] == frozen['checkpoint'], 'same_exact_preservation_sidecar')
        guard = read(receiver['guard_path'])
        old = read(self.binding['guard_path'])
        allowed = {'attempt_dir', 'plan_path', 'plan_sha256', 'lease_path', 'lease_sha256',
            'allocation_path', 'allocation_sha256', 'source_pins'}
        require({key: value for key, value in guard.items() if key not in allowed}
            == {key: value for key, value in old.items() if key not in allowed}, 'unchanged_confinement_guard_and_copy_mapping')

    def dispatch_once(self, token):
        require(token['old_native_exited'] is True and token['life_binding_sha256'] == digest(self.binding)
            and token['sha256'] == digest({key: value for key, value in token.items() if key != 'sha256'}),
            'exact_exited_handoff_token_only')
        require(self.prepared is not None and token['new_source_pins'] == self.prepared['new_source_pins']
            and token['epoch_id'] == self.prepared['epoch_id'] == token['receiver']['source_epoch']
            and token['deadline_unix'] == self.binding['hard_end_unix'], 'approved_pair_source_epoch_only')
        require(time.time() < token['deadline_unix'], 'original_deadline_not_extended')
        self.verify_receiver(token['receiver'], token['exact_complete'])
        claim = self.control / 'DISPATCH_CLAIM.json'
        require(not claim.exists(), 'dispatch_claim_exists_reconcile_never_blind_retry')
        descriptor = os.open(claim, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
        with os.fdopen(descriptor, 'w') as handle:
            json.dump(dict(handoff_sha256=token['sha256'], claimed_unix=time.time()), handle)
            handle.flush()
            os.fsync(handle.fileno())
        sync_directory(self.control)
        write_once(self.control / 'RETENTION_HANDOFF.json', token)
        attempt = Path(token['receiver']['guard_path']).parent
        with (attempt / 'DISPATCH.stdout').open('x') as stdout, (attempt / 'DISPATCH.stderr').open('x') as stderr:
            process = subprocess.Popen([self.python, '-B', '-m', 'gpu.r232_recovery', 'dispatch',
                '--config', token['receiver']['guard_path']], cwd=self.source, env=self.environment(),
                stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, start_new_session=True, close_fds=True)
        result = dict(pid=process.pid, handoff_sha256=token['sha256'], launched_unix=time.time(),
            pid_role='DISPATCH_SUPERVISOR_NOT_NATIVE', loaded=False, parent_rebind_allowed=False,
            parent_handoff_path=token['receiver']['parent_handoff_path'],
            fresh_privileged_admission_required=True, no_management_restriction_bypass=True)
        write_once(attempt / 'DISPATCHED.json', result)
        return result
