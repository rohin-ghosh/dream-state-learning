"""Explicitly activated Linux mechanics; main supplies all receiving-side hooks."""

from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass
import json
import os
from pathlib import Path
import select
import time
from typing import Callable

if __package__:
    from .boundary import digest, journal_identity, read, read_boundary, recheck_consumed_wall_receipt, require, sha
    from .coordinator import PidfdReservation, exclusive_lock
else:
    from boundary import digest, journal_identity, read, read_boundary, recheck_consumed_wall_receipt, require, sha
    from coordinator import PidfdReservation, exclusive_lock


@dataclass(frozen=True)
class ExactHandle:
    descriptor: int
    binding_sha256: str


@dataclass(frozen=True)
class ReceivingHooks:
    verify_prepared: Callable[[dict], None]
    dependents_clear: Callable[[ExactHandle], bool]
    verify_checkpoint: Callable[[dict], dict]
    prepare_receiver: Callable[[dict, dict, dict], dict]
    recheck_checkpoint: Callable[[dict, dict], None]
    verify_receiver: Callable[[dict, dict], None]
    dispatch_once: Callable[[dict], object]


def process_identity(process_id):
    directory = Path('/proc', str(process_id))
    fields = (directory / 'stat').read_text().rsplit(')', 1)[1].split()
    return dict(pid=process_id, uid=directory.stat().st_uid, start_ticks=fields[19],
        state=fields[0], command=[os.fsdecode(part) for part in
            (directory / 'cmdline').read_bytes().split(b'\0') if part])


class LinuxOperations:
    """No CLI, discovery, staging, authorization inference, or automatic rollout."""

    def __init__(self, binding, hooks, *, approved_execution_sha256, control_root, poll_seconds=.15):
        self.binding = deepcopy(binding)
        self.hooks = hooks
        self.approved_execution_sha256 = approved_execution_sha256
        self.control_root = Path(control_root)
        require(self.control_root.is_absolute() and self.control_root.resolve() == self.control_root
            and self.control_root.is_dir(), 'existing_literal_control_root_required')
        require(0 < poll_seconds <= 5, 'bounded_observation_interval')
        self.poll_seconds = poll_seconds
        self.approved = False
        self.bound_journal = None

    def require_execution_approval(self, execution_sha256):
        require(execution_sha256 == self.approved_execution_sha256, 'explicit_exact_execution_approval')
        self.approved = True

    def _bound(self, binding):
        require(self.approved and binding == self.binding, 'approved_exact_life_only')

    def _guard(self):
        binding = self.binding
        require(sha(binding['guard_path']) == binding['guard_sha256'], 'unchanged_exact_guard_bytes')
        guard = read(binding['guard_path'])
        require(guard['source_pins'] == binding['source_pins']
            and guard['hard_end_unix'] == binding['hard_end_unix'], 'guard_sources_and_deadline')
        require(sha(guard['plan_path']) == guard['plan_sha256'], 'unchanged_guard_plan_bytes')
        plan = read(guard['plan_path'])
        require(plan['hard_end_unix'] == binding['hard_end_unix']
            and str(Path(guard.get('copy_raw', plan['root'])) / 'stream') == binding['journal_root'],
            'guard_plan_same_life_journal')
        require(sha(binding['guard_path']) == binding['guard_sha256'], 'guard_raced_during_read')
        return plan

    @contextmanager
    def exclusive_life_lock(self, binding):
        self._bound(binding)
        with exclusive_lock(Path(binding['journal_root']) / 'RETENTION_BOUNDARY.lock'):
            yield

    def open_exact_handle(self, binding):
        self._bound(binding)
        self._boot()
        self._guard()
        self.bound_journal = journal_identity(binding)
        descriptor = os.pidfd_open(binding['pid'])
        handle = ExactHandle(descriptor, digest(binding))
        try:
            self.require_exact_identity(handle, binding)
        except BaseException:
            os.close(descriptor)
            raise
        return handle

    def require_exact_identity(self, handle, binding, *, stopped=False):
        self._bound(binding)
        self._boot()
        require(handle.binding_sha256 == digest(binding), 'same_bound_pidfd')
        deadline = time.monotonic() + 1 if stopped else time.monotonic()
        while True:
            require(not select.select([handle.descriptor], [], [], 0)[0], 'old_native_not_exited')
            actor = process_identity(binding['pid'])
            require(all(actor[key] == binding[key] for key in ('pid', 'uid', 'start_ticks', 'command')),
                'exact_pid_start_uid_and_guard_command')
            require(actor['state'] not in ('Z', 'X'), 'live_native_not_zombie')
            require(stopped or actor['state'] not in ('T', 't'), 'native_not_already_suspended')
            if not stopped or actor['state'] in ('T', 't'):
                break
            require(time.monotonic() < deadline, 'native_suspended_before_boundary_check')
            time.sleep(.01)
        self._guard()
        require(journal_identity(binding) == self.bound_journal, 'same_bound_journal_directories')

    def _boot(self):
        require(Path('/proc/sys/kernel/random/boot_id').read_text().strip() == self.binding['boot_id'],
            'same_host_boot_no_rebooted_native_rebinding')

    def verify_prepared(self, prepared):
        require(self._guard() == prepared['old_plan'], 'prepared_old_plan_is_admitted_plan')
        self.hooks.verify_prepared(prepared)

    def observe(self, binding, *, durable=False):
        self._bound(binding)
        require(journal_identity(binding) == self.bound_journal, 'same_bound_journal_directories')
        return read_boundary(binding, durable=durable)

    def dependents_clear(self, handle):
        return self.hooks.dependents_clear(handle) is True

    def verify_checkpoint(self, candidate):
        return self.hooks.verify_checkpoint(candidate)

    def prepare_receiver(self, candidate, prepared, proof):
        return self.hooks.prepare_receiver(candidate, prepared, proof)

    def recheck_checkpoint(self, proof, frozen):
        self.hooks.recheck_checkpoint(proof, frozen)

    def verify_receiver(self, receiver, frozen):
        recheck_consumed_wall_receipt(self.binding, receiver.get('plan_metadata_receipts', {}))
        self.hooks.verify_receiver(receiver, frozen)

    def reserve(self, handle, seconds):
        self.require_exact_identity(handle, self.binding)
        return PidfdReservation(handle.descriptor, seconds)

    def require_handle_exited(self, handle):
        require(handle.binding_sha256 == digest(self.binding)
            and bool(select.select([handle.descriptor], [], [], 0)[0]), 'exact_pidfd_exit_before_dispatch')

    @contextmanager
    def exclusive_writer_check(self, binding):
        self._bound(binding)
        require(journal_identity(binding) == self.bound_journal, 'same_bound_journal_directories')
        with exclusive_lock(Path(binding['journal_root']) / 'WRITER.lock', create=False):
            require(journal_identity(binding) == self.bound_journal, 'same_writer_lock_after_acquisition')
            yield

    def record(self, kind, document):
        require(self.approved and kind.isidentifier(), 'approved_audit_record_only')
        path = self.control_root / f'{time.time_ns()}_{kind}.json'
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
        with os.fdopen(descriptor, 'w') as handle:
            json.dump(dict(kind=kind, document=document), handle, sort_keys=True, allow_nan=False)
            handle.write('\n')
            handle.flush()
            os.fsync(handle.fileno())
        descriptor = os.open(self.control_root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)

    def dispatch_once(self, token):
        require(self.approved and token['life_binding_sha256'] == digest(self.binding)
            and token['sha256'] == digest({key: value for key, value in token.items() if key != 'sha256'})
            and token['old_native_exited'] is True, 'bound_durable_handoff_token')
        return self.hooks.dispatch_once(token)

    @staticmethod
    def close_handle(handle):
        os.close(handle.descriptor)

    @staticmethod
    def wall_time():
        return time.time()

    def wait(self):
        time.sleep(self.poll_seconds)
