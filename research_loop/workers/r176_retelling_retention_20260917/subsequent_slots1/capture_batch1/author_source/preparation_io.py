"""R176-only, nonrefundable pre-I/O authorities and exact bounded reads."""

from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat
import time


MIB = 1024 ** 2
GIB = 1024 ** 3
END = 1789673400
REMOTE = Path('/localhome/local-rohing/orch_r176_retelling_retention_20260917_generation1')
SCOPE_SHA = '745921c838ae4190f5d633d30ba01375ad2c995a27d08134caa055503c5318d6'
PINS = {
    'PREPARATION_SCOPE.json': SCOPE_SHA,
    'PROPOSAL.json': '352938ee4d9e4adc4365064e34ca4059f8d71f1025762a57e335684445270021',
    'SLOTS.json': '1601bf731ec7c75c4f5db09a0d5bbf99e77989e916e02f2394ad851e02ef7a49',
    'SCOPE.md': '0c86ea05c9c06a4c32c53531c1942dfde63f3608f45accccca6f45fb956d840e',
}
PASSES = ('original_capture', 'source_export', 'receiver_stream', 'receiving_CPU_verification',
    'ON_preflight_verification', 'OFF_preflight_verification', 'ON_native_verification',
    'OFF_native_verification', 'ON_model_load', 'OFF_model_load')


def require(value, reason):
    if not value:
        raise ValueError(reason)


def canonical(document):
    return json.dumps(document, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(document):
    return hashlib.sha256(canonical(document)).hexdigest()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def write(path, document):
    path = Path(path)
    path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    raw = document if isinstance(document, bytes) else canonical(document)
    with path.open('xb') as stream:
        os.fchmod(stream.fileno(), 0o600)
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    return dict(path=str(path), sha256=sha(raw), bytes=len(raw))


@contextmanager
def lock(path):
    path = Path(path)
    path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    with path.open('ab') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        yield


def validate_controls(directory):
    return {name: dict(path=str(Path(directory)/name), sha256=checksum)
        for name, checksum in PINS.items()
        if require(sha((Path(directory)/name).read_bytes()) == checksum, 'frozen_R176_'+name) is None}


class Ledger:
    def __init__(self, root):
        self.root = Path(root)

    def reserve(self, operation, life_id, kind, amount, *, discovery=False, sleep=None, read_pass=None,
            repair_authority=None):
        require(time.time() < END, 'preparation_window_ended')
        require(life_id in ('C2', 'C5', '_campaign'), 'two_declared_lives')
        require(kind in ('metadata', 'adapter', 'storage') and type(amount) is int and amount >= 0,
            'finite_resource_reservation')
        require(not discovery or kind == 'metadata', 'discovery_metadata_only')
        if kind == 'adapter':
            require(life_id in ('C2', 'C5') and sleep in (range(33,39) if life_id == 'C2' else range(29,35))
                and read_pass in PASSES and amount <= 128*MIB, 'fixed_checkpoint_named_pass_cap')
        with lock(self.root/'ledger.lock'):
            rows = [json.loads(path.read_bytes()) for path in (self.root/'reservations').glob('*.json')]
            require(all(row['status'] == 'PRECHARGED_NO_REFUND' and row['scope_sha256'] == SCOPE_SHA
                for row in rows), 'persistent_authority_integrity')
            require(not any(row['operation'] == operation for row in rows), 'attempt_consumed_no_retry')
            if kind == 'adapter':
                previous = [row for row in rows if row['kind'] == kind and row['life_id'] == life_id
                    and row['sleep'] == sleep and row['read_pass'] == read_pass]
                if previous:
                    require(repair_authority is not None, 'named_adapter_pass_already_consumed')
                    raw = Path(repair_authority['path']).read_bytes()
                    require(sha(raw) == repair_authority['sha256'], 'exact_repair_authority')
                    repair = json.loads(raw)
                    failed_raw = Path(repair['failed_receipt']['path']).read_bytes()
                    require(sha(failed_raw) == repair['failed_receipt']['sha256'], 'exact_failed_receipt')
                    failed = json.loads(failed_raw)
                    require(life_id == 'C2' and sleep == 33 and read_pass == 'original_capture' and
                        len(previous) == 1 and repair['scope_sha256'] == SCOPE_SHA and
                        repair['new_operation'] == operation and
                        repair['failed_operation'] == previous[0]['operation'] and
                        failed['status'] == 'FAILED_CAPTURE_PRESERVED_NO_RETRY' and
                        failed['actual_bytes']['adapter'] == 0 and
                        failed['model_calls'] == failed['provider_calls'] == 0, 'one_explicit_pre_model_repair')
                    repair_bytes = sum(row['bytes'] for row in rows if row.get('repair_authority')) + amount
                    life_repairs = sum(row['bytes'] for row in rows if row.get('repair_authority')
                        and row['life_id'] == life_id) + amount
                    require(15*GIB + repair_bytes <= 16*GIB and
                        7680*MIB + life_repairs <= 8*GIB, 'repair_preserves_all_twelve_future_pass_envelopes')
                else:
                    require(repair_authority is None, 'repair_requires_failed_prior_pass')
            require(sum(row['bytes'] for row in rows if row['kind'] == kind) + amount <=
                dict(metadata=2*GIB, adapter=16*GIB, storage=2*GIB)[kind], 'global_resource_cap')
            if life_id != '_campaign' and kind != 'storage':
                require(sum(row['bytes'] for row in rows if row['kind'] == kind and row['life_id'] == life_id)
                    + amount <= dict(metadata=GIB, adapter=8*GIB)[kind], 'per_life_kind_cap')
            require(not discovery or sum(row['bytes'] for row in rows if row['discovery']) + amount <= 32*MIB,
                'discovery_included_subcap')
            document = dict(status='PRECHARGED_NO_REFUND', operation=operation, life_id=life_id, kind=kind,
                bytes=amount, discovery=discovery, sleep=sleep, read_pass=read_pass,
                scope_sha256=SCOPE_SHA, reserved_unix=time.time())
            if repair_authority:
                document['repair_authority'] = repair_authority
            reference = write(self.root/'reservations'/(sha(operation.encode())+'.json'), document)
            return dict(document=document, reference=reference)


class Reader:
    def __init__(self, root, authority, allowed_paths):
        self.root = Path(root)
        self.authority = authority
        self.allowed_paths = {Path(path) for path in allowed_paths}
        self.charged = dict(metadata=0, adapter=0, discovery=0)
        self.actual = dict(metadata=0, adapter=0, discovery=0)
        self.sequence = 0

    def charge(self, path, kind, amount):
        require(kind in self.charged and type(amount) is int and amount >= 0, 'exact_nonnegative_read_charge')
        require(time.time() < END, 'read_window_ended')
        self.charged[kind] += amount
        require(self.charged[kind] <= self.authority[kind]['document']['bytes'], 'delegated_read_cap')
        write(self.root/'reads'/f'{self.sequence:06d}.json', dict(path=str(path), kind=kind, bytes=amount,
            authority=self.authority[kind]['reference'], status='CHARGED_BEFORE_READ_NO_REFUND',
            charged_unix=time.time()))
        self.sequence += 1

    def raw(self, path, kind='metadata', limit=32*MIB):
        path = Path(path)
        require(path in self.allowed_paths and path.is_absolute() and path == path.resolve(), 'exact_source_allowlist')
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(descriptor, 'rb', buffering=0) as stream:
            before = os.fstat(stream.fileno())
            require(stat.S_ISREG(before.st_mode) and before.st_size <= limit, 'regular_bounded_source')
            self.charge(path, kind, before.st_size)
            raw = stream.read(before.st_size)
            self.actual[kind] += len(raw)
            after = os.fstat(stream.fileno())
            current = os.stat(path, follow_symlinks=False)
            require(len(raw) == before.st_size and path == path.resolve() and all(
                getattr(before, field) == getattr(after, field) == getattr(current, field)
                for field in ('st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns')), 'source_changed_during_read')
            return raw

    def document(self, path, checksum=None):
        raw = self.raw(path)
        require(checksum is None or sha(raw) == checksum, 'exact_source_bytes')
        return json.loads(raw), dict(path=str(path), sha256=sha(raw)), raw

    def proc(self, path):
        path = Path(path)
        require(path in self.allowed_paths and str(path).startswith('/proc/'), 'exact_operational_proc_allowlist')
        self.charge(path, 'discovery', 65536)
        with path.open('rb', buffering=0) as stream:
            raw = stream.read(65536)
        self.actual['discovery'] += len(raw)
        require(len(raw) < 65536, 'proc_cap')
        return raw
