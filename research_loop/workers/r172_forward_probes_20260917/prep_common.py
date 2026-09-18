"""Preparation-only scope binding, durable reservations, and bounded reads."""

from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import time


PROPOSAL_SHA = '6ccd3b029948aa228d67d6f3123fc5289ff20d3ccf506b932d2574d874f80958'
REMOTE_ROOT = Path('/localhome/local-rohing/orch_r172_forward_probes_20260917_generation1')
END = 1789673400
GIB = 1024 ** 3


def require(value, reason):
    if not value:
        raise ValueError(reason)


def canonical(document):
    return json.dumps(document, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(document):
    return hashlib.sha256(canonical(document)).hexdigest()


def write(path, document):
    path = Path(path)
    path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    raw = document if isinstance(document, bytes) else canonical(document)
    with path.open('xb') as stream:
        os.chmod(path, 0o600)
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest())


def read(path):
    return json.loads(Path(path).read_bytes())


def ref(path):
    return dict(path=str(path), sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest())


def bound(reference):
    raw = Path(reference['path']).read_bytes()
    require(hashlib.sha256(raw).hexdigest() == reference['sha256'], 'bound_reference_changed')
    return json.loads(raw)


def scope(scope_path, proposal_path, reader=None):
    proposal_raw = reader.raw(proposal_path) if reader else Path(proposal_path).read_bytes()
    document = reader.document(scope_path)[0] if reader else read(scope_path)
    require(document['schema'] == 'R172_MAIN_BUILDER_PREPARATION_SCOPE_V1', 'preparation_scope_schema')
    require(document['proposal_ref']['sha256'] == hashlib.sha256(proposal_raw).hexdigest() == PROPOSAL_SHA,
        'exact_Main_bound_proposal')
    require(document['gpu_execution_authorized_now'] is False and document['model_calls_authorized_now'] is False,
        'preparation_only_no_model_GO')
    limits = document['preparation_source_limits']
    require(limits['metadata_bytes'] == 32 * GIB and limits['adapter_bytes'] == 16 * GIB
        and limits['per_life_per_kind_bytes'] == 2 * GIB
        and limits['operational_discovery_bytes_included_in_metadata'] == 64 * 1024 ** 2,
        'exact_preparation_read_limits')
    require(time.time() < END, 'absolute_preparation_wall')
    return document, json.loads(proposal_raw)


@contextmanager
def lock(path):
    path = Path(path)
    path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    with path.open('a+b') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        yield


class Ledger:
    def __init__(self, root, limits, lives):
        self.root = Path(root)
        self.limits = limits
        self.lives = set(lives) | {'_campaign'}

    def totals(self):
        rows = [read(path) for path in (self.root / 'reservations').glob('*.json')]
        require(all(row.get('status') == 'CHARGED_BEFORE_IO_NO_REFUND' and row.get('life_id') in self.lives
            and row.get('kind') in ('metadata', 'adapter') and type(row.get('bytes')) is int and row['bytes'] >= 0
            and type(row.get('discovery')) is bool and (not row['discovery'] or row['kind'] == 'metadata')
            for row in rows), 'valid_persistent_read_reservations_no_refunds')
        return dict(metadata=sum(row['bytes'] for row in rows if row['kind'] == 'metadata'),
            adapter=sum(row['bytes'] for row in rows if row['kind'] == 'adapter'),
            discovery=sum(row['bytes'] for row in rows if row['discovery']), rows=rows)

    def reserve(self, operation, life_id, kind, amount, discovery=False):
        require(life_id in self.lives and kind in ('metadata', 'adapter'), 'declared_read_account')
        require(type(amount) is int and amount >= 0 and isinstance(operation, str) and operation,
            'finite_read_reservation')
        require(not discovery or kind == 'metadata', 'discovery_included_in_metadata')
        require(time.time() < END, 'read_window_ended')
        key = hashlib.sha256(operation.encode()).hexdigest()
        with lock(self.root / 'ledger.lock'):
            target = self.root / 'reservations' / (key + '.json')
            require(not target.exists(), 'operation_consumed_no_retry_or_refund')
            totals = self.totals()
            require(totals[kind] + amount <= self.limits[kind], 'aggregate_read_budget')
            life_total = sum(row['bytes'] for row in totals['rows'] if row['kind'] == kind and row['life_id'] == life_id)
            require(life_total + amount <= self.limits['per_life'], 'per_life_read_budget')
            require(not discovery or totals['discovery'] + amount <= self.limits['discovery'], 'discovery_subcap')
            return write(target, dict(status='CHARGED_BEFORE_IO_NO_REFUND', operation=operation,
                life_id=life_id, kind=kind, bytes=amount, discovery=discovery,
                reserved_unix=time.time(), failures_charged=True))


def safe_file(path):
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts and path == path.resolve(), 'exact_non_symlink_path')
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    if not stat.S_ISREG(os.fstat(descriptor).st_mode):
        os.close(descriptor)
        raise ValueError('regular_source_only')
    return descriptor


class Reader:
    def __init__(self, ledger, life_id, operation, allowed_roots, discovery=False):
        self.ledger = ledger
        self.life_id = life_id
        self.operation = operation
        self.allowed_roots = [Path(root) for root in allowed_roots]
        self.discovery = discovery
        self.sequence = 0
        self.bytes = 0

    def raw(self, path, kind='metadata', limit=32 * 1024 ** 2):
        path = Path(path)
        require(any(path == root or path.is_relative_to(root) for root in self.allowed_roots), 'source_allowlist')
        descriptor = safe_file(path)
        with os.fdopen(descriptor, 'rb', buffering=0) as stream:
            before = os.fstat(stream.fileno())
            require(before.st_size <= limit, 'source_file_size_cap')
            self.ledger.reserve(f'{self.operation}:{self.sequence}:{path}', self.life_id, kind,
                before.st_size, self.discovery)
            self.sequence += 1
            raw = stream.read(before.st_size)
            self.bytes += len(raw)
            after = os.fstat(stream.fileno())
            current = os.stat(path, follow_symlinks=False)
            require(path == path.resolve() and len(raw) == before.st_size and all(
                getattr(before, field) == getattr(after, field) == getattr(current, field)
                for field in ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns')), 'source_changed_during_read')
            return raw

    def document(self, path, kind='metadata', limit=32 * 1024 ** 2):
        raw = self.raw(path, kind, limit)
        return json.loads(raw), dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest())


class DiskLedger:
    """Nonrefundable reservations include failed and uncertain transfers.

    Free-space admission conservatively retains prior reservations as outstanding;
    it never assumes an old reservation has been freed or deletes old evidence.
    """

    CAPS = dict(staging=24 * GIB, receiving=16 * GIB)

    def __init__(self, root, role):
        require(role in self.CAPS, 'declared_disk_role')
        self.root = Path(root)
        require(self.root.is_absolute() and self.root == self.root.resolve(), 'canonical_disk_root')
        self.role = role
        self.directory = self.root / 'transfer_disk_ledger' / role

    def reserve(self, operation, amount):
        with lock(self.directory / 'disk.lock'):
            return self._reserve_locked(operation, amount)

    def _reserve_locked(self, operation, amount):
        require(type(amount) is int and amount >= 0, 'finite_disk_reservation')
        require(time.time() < END, 'read_window_ended')
        target = self.directory / 'reservations' / (hashlib.sha256(operation.encode()).hexdigest() + '.json')
        require(not target.exists(), 'disk_operation_consumed_no_refund')
        operation_root = operation.removesuffix(':control').removesuffix(':payload')
        for prior in (self.root / f'{self.role}_transfers').glob('*'):
            require(prior.is_dir() and prior == prior.resolve(), 'canonical_prior_transfer_operation')
            if str(prior) == operation_root:
                continue
            phases = ['control', 'payload'] if (prior / 'payload').exists() else ['control']
            for phase in phases:
                key = hashlib.sha256((str(prior) + ':' + phase).encode()).hexdigest()
                require((self.directory / 'reservations' / (key + '.json')).is_file(),
                    'prior_transfer_disk_custody_unaccounted_hold')
        rows = [read(path) for path in (self.directory / 'reservations').glob('*.json')]
        require(all(row['status'] == 'DISK_RESERVED_BEFORE_PAYLOAD_NO_REFUND'
            and row['role'] == self.role and type(row['bytes']) is int and row['bytes'] >= 0
            for row in rows), 'valid_persistent_disk_reservations')
        reserved = sum(row['bytes'] for row in rows)
        require(reserved + amount <= self.CAPS[self.role], 'aggregate_disk_budget')
        require(shutil.disk_usage(self.root).free >= reserved + amount, 'insufficient_free_disk')
        return write(target, dict(status='DISK_RESERVED_BEFORE_PAYLOAD_NO_REFUND', role=self.role,
            operation=operation, bytes=amount, reserved_unix=time.time(), failures_charged=True))


class ChargedStream:
    """Exact unbuffered transport reads; failed/short reads retain full charges."""

    def __init__(self, stream, ledger, life_id, operation):
        import io
        require(isinstance(stream, (io.RawIOBase, io.BytesIO)), 'unbuffered_transfer_stream_required')
        self.stream = stream
        self.ledger = ledger
        self.life_id = life_id
        self.operation = operation
        self.sequence = 0
        self.bytes = 0

    def exact(self, amount, kind='metadata'):
        require(type(amount) is int and amount >= 0, 'finite_stream_read')
        if amount:
            self.ledger.reserve(f'{self.operation}:{self.sequence}', self.life_id, kind, amount)
            self.sequence += 1
        parts = []
        remaining = amount
        while remaining:
            require(time.time() < END, 'read_window_ended')
            requested = min(remaining, 1024 ** 2)
            raw = self.stream.read(requested)
            require(isinstance(raw, bytes) and 0 < len(raw) <= requested, 'truncated_or_invalid_transfer_read')
            self.bytes += len(raw)
            parts.append(raw)
            remaining -= len(raw)
        return b''.join(parts)
