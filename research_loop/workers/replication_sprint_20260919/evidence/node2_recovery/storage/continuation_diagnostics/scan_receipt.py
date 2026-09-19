"""Non-material diagnostics: durable raw evidence before the unchanged predicate."""

import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

import node2_scope as scope


POLICY = 'DURABLE_RAW_SCAN_BEFORE_UNCHANGED_ADMISSION_V1'
SCANNER_SOURCE_SHA256 = '3f2e858d2d540759aaef0d7cd56acae56600460a72da039803793dc71d15503c'


def target_identity(path):
    try:
        info = Path(path).lstat()
        return dict(path=str(path), device=info.st_dev, inode=info.st_ino, size=info.st_size,
                    nlink=info.st_nlink, uid=info.st_uid, gid=info.st_gid, mode=info.st_mode,
                    mtime_ns=info.st_mtime_ns, ctime_ns=info.st_ctime_ns)
    except OSError as error:
        return dict(path=str(path), error_type=type(error).__name__, errno=error.errno)


def raw_bytes(value):
    if value is None:
        return b''
    return value.encode() if isinstance(value, str) else value


def scan_with_receipt(paths, ledger, batch_sha256):
    scope.require(0 < len(paths) <= 40, 'bounded_exact_writer_scope')
    for path in paths:
        scope.owned_retired_path(path, scope.ROOT)
    before = [target_identity(path) for path in paths]
    started = datetime.now(timezone.utc).isoformat()
    payload = json.dumps(paths).encode()
    command = ['sudo', '-n', 'python3', '-B', '-c', scope.PRIVILEGED_SCAN]
    failure = None
    result = None
    try:
        result = subprocess.run(command, input=payload, capture_output=True, timeout=45, check=False)
        stdout, stderr = result.stdout, result.stderr
    except (OSError, subprocess.SubprocessError) as error:
        failure = error
        stdout, stderr = raw_bytes(getattr(error, 'stdout', None)), raw_bytes(getattr(error, 'stderr', None))
    parse_error = None
    parsed = None
    try:
        parsed = json.loads(stdout)
    except (ValueError, UnicodeError) as error:
        parse_error = error
    document = dict(policy=POLICY, batch_sha256=batch_sha256, target_paths=list(paths),
                    started_utc=started, finished_utc=datetime.now(timezone.utc).isoformat(),
                    target_identity_before=before, target_identity_after=[target_identity(path) for path in paths],
                    scanner_source_sha256=SCANNER_SOURCE_SHA256,
                    scanner_program_sha256=hashlib.sha256(scope.PRIVILEGED_SCAN.encode()).hexdigest(),
                    stdin_sha256=hashlib.sha256(payload).hexdigest(),
                    stdout_base64=base64.b64encode(stdout).decode(), stderr_base64=base64.b64encode(stderr).decode(),
                    returncode=None if result is None else result.returncode,
                    process_failure=None if failure is None else dict(type=type(failure).__name__,
                        errno=getattr(failure, 'errno', None), timeout_seconds=getattr(failure, 'timeout', None)),
                    parse_status='PARSED' if parse_error is None else 'FAILED',
                    parse_error=None if parse_error is None else dict(type=type(parse_error).__name__, message=str(parse_error)),
                    parsed_result=parsed, admission_predicate_not_yet_called=True)
    ledger.record('PRIVILEGED_WRITER_SCAN_RAW_RESULT', document)
    if failure is not None:
        raise failure
    result.check_returncode()
    if parse_error is not None:
        raise parse_error
    scope.validate_writer_scan(parsed)
    return parsed
