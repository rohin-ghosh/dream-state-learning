"""Unbound, non-material admission repair candidate; never authorizes a launch."""

from contextlib import ExitStack
from copy import deepcopy
from datetime import datetime, timezone
import errno
import hashlib
import json
import os
import select
import time


TRANSIENT_REASONS = frozenset(('process_identity_drift', 'minor_scan_identity_changed'))
IDENTITY_FIELDS = ('pid', 'uid', 'start_ticks', 'boot_id', 'command_sha256')


def _read_at(directory, name):
    descriptor = os.open(name, os.O_RDONLY | os.O_CLOEXEC, dir_fd=directory)
    with os.fdopen(descriptor, 'rb') as stream:
        chunks = []
        length = 0
        while length <= 8 * 1024 * 1024:
            chunk = stream.read(min(4096, 8 * 1024 * 1024 + 1 - length))
            if not chunk:
                break
            chunks.append(chunk)
            length += len(chunk)
        value = b''.join(chunks)
    if len(value) > 8 * 1024 * 1024:
        raise ValueError('proc_record_too_large')
    return value


def _stat_identity(raw):
    text = raw.decode()
    process_id = int(text.split('(', 1)[0].strip())
    fields = text.rsplit(')', 1)[1].split()
    ticks = fields[19]
    if process_id <= 0 or not ticks.isdecimal():
        raise ValueError('invalid_proc_identity')
    return process_id, ticks


def _exited(descriptor):
    poller = select.poll()
    poller.register(descriptor, select.POLLIN)
    events = poller.poll(0)
    if any(mask & (select.POLLERR | select.POLLNVAL) for _, mask in events):
        raise OSError(errno.EIO, 'invalid_pidfd_poll')
    return any(mask & select.POLLIN for _, mask in events)


class _ProcSession:
    def __init__(self, stack):
        self.stack = stack
        self.root = os.open('/proc', os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
        stack.callback(os.close, self.root)
        self.context = self._context()

    def _context(self):
        if os.geteuid() != 0 or not hasattr(os, 'pidfd_open'):
            raise ValueError('root_and_pidfd_required')
        status = _read_at(self.root, 'self/status').decode()
        capabilities = dict(line.split(':', 1) for line in status.splitlines() if ':' in line)
        if not int(capabilities['CapEff'].strip(), 16) & (1 << 19):
            raise ValueError('unrestricted_proc_requires_cap_sys_ptrace')
        namespaces = tuple(os.readlink(name, dir_fd=self.root) for name in
                           ('self/ns/pid', '1/ns/pid', 'self/ns/user', '1/ns/user'))
        if namespaces[0] != namespaces[1] or namespaces[2] != namespaces[3]:
            raise ValueError('proc_namespace_mismatch')
        if _stat_identity(_read_at(self.root, 'self/stat'))[0] != os.getpid():
            raise ValueError('proc_pid_view_mismatch')
        anchored = os.fstat(self.root)
        current = os.stat('/proc')
        if (anchored.st_dev, anchored.st_ino) != (current.st_dev, current.st_ino):
            raise ValueError('proc_mount_changed')
        boot_id = _read_at(self.root, 'sys/kernel/random/boot_id').decode().strip()
        if not boot_id:
            raise ValueError('boot_identity_missing')
        return boot_id, namespaces, os.getpid(), anchored.st_dev, anchored.st_ino

    def check_context(self):
        if self._context() != self.context:
            raise ValueError('proc_context_changed')

    def pids(self):
        return sorted(int(name) for name in os.listdir(self.root) if name.isdecimal())

    def _identity(self, directory, process_id):
        observed_pid, ticks = _stat_identity(_read_at(directory, 'stat'))
        if observed_pid != process_id:
            raise ValueError('proc_pid_mismatch')
        return dict(pid=process_id, uid=os.fstat(directory).st_uid, start_ticks=ticks,
                    boot_id=self.context[0],
                    command_sha256=hashlib.sha256(_read_at(directory, 'cmdline')).hexdigest())

    def pin(self, process_id):
        with ExitStack() as temporary:
            directory = os.open(str(process_id), os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC,
                                dir_fd=self.root)
            temporary.callback(os.close, directory)
            before = self._identity(directory, process_id)
            descriptor = os.pidfd_open(process_id, 0)
            temporary.callback(os.close, descriptor)
            if _exited(descriptor):
                return None
            fdinfo = _read_at(self.root, f'self/fdinfo/{descriptor}').decode()
            fields = dict(line.split(':', 1) for line in fdinfo.splitlines() if ':' in line)
            if int(fields['Pid'].strip()) != process_id:
                raise ValueError('pidfd_namespace_mismatch')
            after = self._identity(directory, process_id)
            if before != after or _exited(descriptor):
                return None
            held = os.dup(descriptor)
            self.stack.callback(os.close, held)
            return dict(identity=after, descriptor=held, captured_monotonic_ns=time.monotonic_ns())

    def prove_exit(self, pin):
        self.check_context()
        if not _exited(pin['descriptor']):
            return dict(proven=False, disposition='historical_process_not_exited')
        try:
            os.stat(str(pin['identity']['pid']), dir_fd=self.root, follow_symlinks=False)
        except FileNotFoundError as error:
            if error.errno != errno.ENOENT:
                raise
        else:
            return dict(proven=False, disposition='pid_present_including_replacement_or_zombie')
        try:
            replacement = os.pidfd_open(pin['identity']['pid'], 0)
        except ProcessLookupError as error:
            if error.errno != errno.ESRCH:
                raise
        else:
            os.close(replacement)
            return dict(proven=False, disposition='kernel_pid_present_including_hidden_replacement')
        return dict(proven=True, disposition='pidfd_exited_and_pid_absent',
                    pidfd_pollin=True, proc_lookup_errno=errno.ENOENT,
                    kernel_pidfd_open_errno=errno.ESRCH,
                    observed_monotonic_ns=time.monotonic_ns())


def _history_matches(process, pin, report):
    expected = pin['identity']
    if any(process.get(key) != expected[key] for key in IDENTITY_FIELDS if key != 'boot_id'):
        return False
    pinned = process.get('pinned_identity')
    if not isinstance(pinned, dict) or any(pinned.get(key) != expected[key] for key in IDENTITY_FIELDS):
        return False
    if ('unreadable' in process or process.get('vanished') or process.get('foreign_owned')
            or process.get('target_device_open') is not False or 'cvd' not in process):
        return False
    if process.get('cvd') not in (None, '', '-1'):
        return False
    return not any(entry.get('pid') == expected['pid'] for entry in report['compute_processes'])


def _validate_report(report, started, finished):
    if (not isinstance(report, dict) or report.get('scanner_euid') != 0
            or report.get('scanner_pid') != os.getpid()
            or not isinstance(report.get('blocking_reasons'), list)
            or any(not isinstance(reason, str) for reason in report['blocking_reasons'])
            or type(report.get('clear')) is not bool
            or report['clear'] != (not report['blocking_reasons'])
            or not isinstance(report.get('processes'), list)
            or not isinstance(report.get('compute_processes'), list)):
        raise ValueError('invalid_privileged_report')
    created = datetime.fromisoformat(report['created_utc'])
    if created.tzinfo is None or not started <= created <= finished:
        raise ValueError('report_not_created_during_callback')
    processes = {}
    for process in report['processes']:
        if (not isinstance(process, dict) or type(process.get('pid')) is not int
                or process['pid'] <= 0 or process['pid'] in processes):
            raise ValueError('invalid_or_duplicate_process_record')
        processes[process['pid']] = process
    if any(not isinstance(entry, dict) for entry in report['compute_processes']):
        raise ValueError('invalid_compute_record')
    return processes


def reconcile_scan(scanner, *, max_pins=4096):
    """Wrap one fresh synchronous same-process read-only scan; return an audit envelope.

    This is not a scanner-compatible admission result. Main must review and test
    any future binding. A saved report or a privileged subprocess is not a valid
    substitute for the scanner callback. No polling, retries, signals or launch.
    """
    if type(max_pins) is not int or max_pins <= 0:
        raise ValueError('positive_pin_budget_required')
    errors = []
    pins = {}
    decisions = []
    cleared = []
    with ExitStack() as stack:
        session = None
        try:
            session = _ProcSession(stack)
            process_ids = session.pids()
            if len(process_ids) > max_pins:
                raise ValueError('pidfd_budget_exceeded')
            for process_id in process_ids:
                try:
                    pin = session.pin(process_id)
                    if pin is not None:
                        pins[process_id] = pin
                except (FileNotFoundError, ProcessLookupError):
                    continue
                except (OSError, ValueError, KeyError, IndexError) as error:
                    errors.append(f'capture_failed:{process_id}:{type(error).__name__}')
        except (OSError, ValueError, KeyError, IndexError) as error:
            errors.append('capture_unavailable:' + type(error).__name__)
        scan_started = datetime.now(timezone.utc)
        report = deepcopy(scanner())
        scan_finished = datetime.now(timezone.utc)
        canonical = json.dumps(report, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
        try:
            processes = _validate_report(report, scan_started, scan_finished)
            if session is not None:
                session.check_context()
            if not errors:
                for reason in report['blocking_reasons']:
                    prefix, separator, suffix = reason.partition(':')
                    if prefix not in TRANSIENT_REASONS or not separator:
                        continue
                    decision = dict(reason=reason, cleared=False)
                    decisions.append(decision)
                    if not suffix.isdecimal() or str(int(suffix)) != suffix:
                        decision['disposition'] = 'noncanonical_pid'
                        continue
                    process_id = int(suffix)
                    pin = pins.get(process_id)
                    process = processes.get(process_id)
                    if pin is None or process is None or not _history_matches(process, pin, report):
                        decision['disposition'] = 'missing_or_conflicting_historical_identity_or_facts'
                        continue
                    decision['historical_identity'] = deepcopy(pin['identity'])
                    decision['captured_monotonic_ns'] = pin['captured_monotonic_ns']
                    decision['first_observation'] = session.prove_exit(pin)
                    if not decision['first_observation']['proven']:
                        decision['disposition'] = decision['first_observation']['disposition']
                        continue
                    decision['final_observation'] = session.prove_exit(pin)
                    decision['disposition'] = decision['final_observation']['disposition']
                    if decision['final_observation']['proven']:
                        decision['cleared'] = True
                        cleared.append(reason)
            if session is not None:
                session.check_context()
        except (OSError, ValueError, KeyError, IndexError, TypeError) as error:
            errors.append('reconciliation_failed:' + type(error).__name__)
        if errors:
            cleared = []
            for decision in decisions:
                decision['cleared'] = False
        remaining = [reason for reason in report.get('blocking_reasons', []) if reason not in cleared]
        remaining.extend('transient_exit_sidecar:' + error for error in errors)
        return dict(schema='orch_admission_transient_exit/v1', original_report=report,
                    original_report_sha256=hashlib.sha256(canonical).hexdigest(),
                    reconciliation=dict(candidate_clear=not remaining, blocking_reasons=remaining,
                                        cleared_reasons=cleared, decisions=decisions, errors=errors,
                                        pins_captured=len(pins), max_pins=max_pins,
                                        scan_started_utc=scan_started.isoformat(),
                                        scan_finished_utc=scan_finished.isoformat()),
                    binding_status='UNBOUND_REQUIRES_MAIN_REVIEW_AND_TESTS', launch_authorized=False)
