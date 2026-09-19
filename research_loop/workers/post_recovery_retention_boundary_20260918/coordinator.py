"""External reservation state machine. Main supplies staged receiver and dispatch adapters."""

from contextlib import contextmanager
from copy import deepcopy
import fcntl
import json
import os
from pathlib import Path
import re
import select
import signal
import socket
import stat
import time

if __package__:
    from .boundary import (ObservationRace, Refusal, digest, require, required_plan_metadata_receipts,
        same_boundary, verify_source_only_plans)
else:
    from boundary import (ObservationRace, Refusal, digest, require, required_plan_metadata_receipts,
        same_boundary, verify_source_only_plans)


def validate_prepared(binding, prepared, authority):
    require(type(binding['pid']) is int and binding['pid'] > 1
        and type(binding['uid']) is int and binding['uid'] >= 0
        and isinstance(binding['start_ticks'], str) and binding['start_ticks'].isdigit()
        and int(binding['start_ticks']) > 0, 'exact_process_binding')
    require(binding['command'] and binding['guard_path'] in binding['command'], 'exact_guard_in_command')
    require(isinstance(binding.get('boot_id'), str)
        and re.fullmatch(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}', binding['boot_id']),
        'exact_host_boot_identity_required')
    require(authority['schema'] == 'RETENTION_SOURCE_CHANGE_AUTHORITY_V1'
        and authority['life_binding_sha256'] == digest(binding), 'explicit_per_life_source_change_authority')
    require(authority['wall_extension_authorized'] is False, 'source_authority_is_not_wall_extension')
    require(prepared['old_guard_sha256'] == binding['guard_sha256']
        and prepared['old_source_pins'] == binding['source_pins'], 'prepared_against_exact_old_guard_and_sources')
    required_plan_metadata_receipts(prepared['old_plan'], prepared['new_plan'])
    require(prepared['old_plan']['hard_end_unix'] == binding['hard_end_unix'], 'bound_unchanged_deadline')
    changed = {name: dict(before=prepared['old_source_pins'].get(name), after=prepared['new_source_pins'].get(name))
        for name in set(prepared['old_source_pins']) | set(prepared['new_source_pins'])
        if prepared['old_source_pins'].get(name) != prepared['new_source_pins'].get(name)}
    require(changed and changed == authority['approved_source_changes']
        and set(prepared['old_source_pins']) <= set(prepared['new_source_pins']), 'exact_approved_source_delta')
    for pins in (prepared['old_source_pins'], prepared['new_source_pins']):
        require(all(not Path(name).is_absolute() and '..' not in Path(name).parts
            and isinstance(value, str) and re.fullmatch(r'[0-9a-f]{64}', value)
            for name, value in pins.items()), 'relative_source_paths_and_exact_hashes')
    require(prepared['cpu_passed'] is True and prepared['same_journal'] is True
        and prepared['same_checkpoint_payloads'] is True and prepared['same_confinement'] is True,
        'receiver_CPU_and_continuity_gates')
    require(prepared['epoch_id'] == authority['epoch_id'], 'one_bound_source_epoch')


def verify_receiver_plan(binding, prepared, receiver, candidate):
    required = required_plan_metadata_receipts(prepared['old_plan'], prepared['new_plan'])
    if required:
        require('plan' in receiver and 'plan_metadata_receipts' in receiver, 'receiving_plan_and_metadata_receipts_required')
    plan = receiver.get('plan', prepared['new_plan'])
    template = deepcopy(plan)
    if 'checkpoint_tail_recovery' in required:
        require(isinstance(template.get('checkpoint_tail_recovery'), dict), 'checkpoint_tail_reader_must_remain_enabled')
        for key in ('complete_index', 'complete_sha256'):
            template['checkpoint_tail_recovery'][key] = prepared['new_plan']['checkpoint_tail_recovery'][key]
    require(template == prepared['new_plan'], 'receiver_plan_matches_approved_template_except_exact_anchor')
    receipts = receiver.get('plan_metadata_receipts', {})
    verify_source_only_plans(prepared['old_plan'], plan, binding=binding, candidate=candidate, receipts=receipts)
    if required:
        require(receiver.get('plan_sha256') == digest(plan), 'receiver_effective_plan_digest')
    if 'checkpoint_tail_recovery' in required:
        require(receipts['checkpoint_tail_recovery']['reader_source_pins_sha256'] == digest(prepared['new_source_pins']),
            'checkpoint_tail_CPU_receipt_for_exact_receiving_sources')


def coordinate(binding, prepared, authority, operations, *, max_attempts=200, stop_seconds=10):
    """Not a CLI: call only from main's reviewed, explicitly activated integration."""
    binding, prepared, authority = deepcopy((binding, prepared, authority))
    validate_prepared(binding, prepared, authority)
    require(0 < stop_seconds <= 30 and 0 < max_attempts <= 10000, 'bounded_coordinator_budget')
    operations.require_execution_approval(digest(dict(binding=binding, prepared=prepared, authority=authority)))
    with operations.exclusive_life_lock(binding):
        handle = operations.open_exact_handle(binding)
        try:
            operations.verify_prepared(prepared)
            for attempt in range(max_attempts):
                operations.require_exact_identity(handle, binding)
                if operations.wall_time() >= binding['hard_end_unix'] - 2 * stop_seconds - 30:
                    raise Refusal('insufficient_unchanged_deadline_margin')
                try:
                    candidate = operations.observe(binding)
                except (ObservationRace, FileNotFoundError, json.JSONDecodeError):
                    operations.wait()
                    continue
                if candidate is None or not operations.dependents_clear(handle):
                    operations.wait()
                    continue
                proof = operations.verify_checkpoint(candidate)
                require(proof['complete_sha256'] == candidate['complete_sha256']
                    and proof['checkpoint_sha256'] == digest(candidate['checkpoint'])
                    and all(proof.get(key) is True for key in ('adapter_verified', 'optimizer_verified',
                        'python_cpu_cuda_rng_verified', 'working_state_verified', 'durable_files_and_directories')),
                    'prestop_full_saved_state_proof')
                receiver = operations.prepare_receiver(candidate, prepared, proof)
                verify_receiver_plan(binding, prepared, receiver, candidate)
                require(receiver['source_epoch'] == prepared['epoch_id']
                    and receiver['resume_state_sha256'] == candidate['resume_state']['sha256']
                    and receiver['checkpoint_sha256'] == digest(candidate['checkpoint'])
                    and receiver['same_journal_root'] == binding['journal_root']
                    and receiver['rescans_original_inbox'] is True
                    and receiver['no_model_load_before_writer_lock'] is True
                    and receiver['deadline_unix'] == binding['hard_end_unix']
                    and receiver['source_adoption_not_wall_extension'] is True,
                    'prestop_receiver_exact_saved_state_no_duplicate_writer')
                with operations.reserve(handle, stop_seconds) as reservation:
                    try:
                        operations.require_exact_identity(handle, binding, stopped=True)
                        frozen = same_boundary(candidate, operations.observe(binding))
                        require(operations.dependents_clear(handle), 'no_active_readout_or_child_at_handoff')
                        operations.verify_prepared(prepared)
                        operations.recheck_checkpoint(proof, frozen)
                        operations.verify_receiver(receiver, frozen)
                        verify_receiver_plan(binding, prepared, receiver, frozen)
                        final = same_boundary(frozen, operations.observe(binding, durable=True))
                        verify_receiver_plan(binding, prepared, receiver, final)
                        require(final['durable'] is True, 'durable_COMPLETE_LEARN_and_INBOX_before_commit')
                        operations.require_exact_identity(handle, binding, stopped=True)
                        require(operations.wall_time() < binding['hard_end_unix'] - stop_seconds - 30,
                            'unchanged_deadline_margin_before_commit')
                    except (Refusal, FileNotFoundError, json.JSONDecodeError, TimeoutError) as error:
                        operations.record('REOBSERVE_SAME_NATIVE', dict(attempt=attempt,
                            reason=str(error), old_pid=binding['pid'], old_start_ticks=binding['start_ticks']))
                        continue
                    operations.record('RETENTION_HANDOFF_INTENT', dict(epoch_id=prepared['epoch_id'],
                        binding=binding, prepared_sha256=digest(prepared), authority_sha256=digest(authority), complete=final,
                        receiver=receiver, same_weights_optimizer_RNG_targets_and_deadline=True))
                    if not reservation.commit_and_wait_exit():
                        operations.record('REOBSERVE_SAME_NATIVE', dict(attempt=attempt,
                            reason='reservation_expired_resumed_same_handle', old_pid=binding['pid'],
                            old_start_ticks=binding['start_ticks']))
                        continue
                    operations.require_handle_exited(handle)
                    with operations.exclusive_writer_check(binding):
                        exited = same_boundary(final, operations.observe(binding, durable=True))
                        operations.verify_receiver(receiver, exited)
                        verify_receiver_plan(binding, prepared, receiver, exited)
                        require(operations.wall_time() < binding['hard_end_unix'], 'same_deadline_not_expired_before_dispatch')
                        token = dict(schema='RETENTION_HANDOFF_TOKEN_V1', epoch_id=prepared['epoch_id'],
                            life_binding_sha256=digest(binding), prepared_sha256=digest(prepared),
                            authority_sha256=digest(authority), old_pid=binding['pid'],
                            old_start_ticks=binding['start_ticks'], old_native_exited=True,
                            exact_complete=exited, receiver=receiver, new_source_pins=prepared['new_source_pins'],
                            deadline_unix=binding['hard_end_unix'], no_cold_start=True,
                            no_unresolved_work_replayed=True, epoch_record_required_before_first_THINK=True)
                        token['sha256'] = digest(token)
                        operations.record('RETENTION_HANDOFF_READY', token)
                    require(operations.wall_time() < binding['hard_end_unix'], 'same_deadline_not_expired_before_dispatch')
                    operations.dispatch_once(token)
                    return token
            raise Refusal('bounded_observation_expired_old_native_left_running')
        finally:
            operations.close_handle(handle)


class PidfdReservation:
    """Guardian owns STOP/CONT/TERM, serializing watchdog expiry against commit."""

    def __init__(self, descriptor, seconds):
        require(0 < seconds <= 30, 'bounded_reservation_seconds')
        self.descriptor, self.seconds = descriptor, seconds
        self.committed = False

    @staticmethod
    def _send(connection, value):
        connection.send(json.dumps(value).encode())

    @staticmethod
    def _receive(connection):
        data = connection.recv(16384)
        return json.loads(data) if data else None

    def _guard(self, guardian):
        stopped = False
        try:
            stopped = True
            signal.pidfd_send_signal(self.descriptor, signal.SIGSTOP)
            deadline = time.monotonic() + self.seconds
            self._send(guardian, dict(status='STOP_SENT'))
            readable = select.select([guardian, self.descriptor], [], [], max(0, deadline - time.monotonic()))[0]
            command = self._receive(guardian) if guardian in readable else None
            if command == 'COMMIT' and time.monotonic() < deadline and self.descriptor not in readable:
                signal.pidfd_send_signal(self.descriptor, signal.SIGTERM)
                signal.pidfd_send_signal(self.descriptor, signal.SIGCONT)
                stopped = False
                exited = bool(select.select([self.descriptor], [], [], self.seconds)[0])
                self._send(guardian, dict(status='EXITED' if exited else 'EXIT_UNCONFIRMED', irreversible=True))
            else:
                signal.pidfd_send_signal(self.descriptor, signal.SIGCONT)
                stopped = False
                self._send(guardian, dict(status='RESUMED_SAME_PIDFD', irreversible=False))
        except (ProcessLookupError, BrokenPipeError, ConnectionResetError):
            pass
        finally:
            if stopped:
                try:
                    signal.pidfd_send_signal(self.descriptor, signal.SIGCONT)
                except ProcessLookupError:
                    pass

    def __enter__(self):
        parent, guardian = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
        try:
            self.guardian_pid = os.fork()
        except BaseException:
            parent.close()
            guardian.close()
            raise
        if self.guardian_pid == 0:
            parent.close()
            try:
                self._guard(guardian)
            finally:
                guardian.close()
                os._exit(0)
        guardian.close()
        self.connection = parent
        self.connection.settimeout(self.seconds + 2)
        try:
            require(self._receive(parent) == {'status': 'STOP_SENT'}, 'guardian_stop_acknowledged')
        except BaseException:
            self.connection.close()
            os.waitpid(self.guardian_pid, 0)
            raise
        return self

    def commit_and_wait_exit(self):
        self.committed = True
        try:
            self._send(self.connection, 'COMMIT')
        except (BrokenPipeError, ConnectionResetError):
            pass
        reply = self._receive(self.connection)
        if reply == dict(status='RESUMED_SAME_PIDFD', irreversible=False):
            return False
        require(reply is not None and reply.get('status') == 'EXITED', 'watchdog_expired_or_old_exit_unconfirmed')
        return True

    def __exit__(self, kind, value, traceback):
        try:
            if not self.committed:
                try:
                    self._send(self.connection, 'RESUME')
                    reply = self._receive(self.connection)
                    require(reply is not None and reply.get('status') == 'RESUMED_SAME_PIDFD', 'same_handle_resume_acknowledged')
                except (BrokenPipeError, ConnectionResetError, TimeoutError):
                    pass
        finally:
            self.connection.close()
            os.waitpid(self.guardian_pid, 0)


@contextmanager
def exclusive_lock(path, *, create=True):
    path = Path(path)
    descriptor = os.open(path, os.O_RDWR | (os.O_CREAT if create else 0) | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
    try:
        require(stat.S_ISREG(os.fstat(descriptor).st_mode), 'regular_exclusive_lock')
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield descriptor
    finally:
        os.close(descriptor)
