"""Restart only the existing P3 MODEL parent; retain original publication gates."""

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import urllib.error


HERE = Path(__file__).resolve().parent
OLD = HERE.parent / 'rohin233_recovery_20260918'
LEDGER = HERE.parent / 'rohin174_parenting_20260917/node4/R195_FLEET/r210_parent3'
MODEL = 'openai/openai/gpt-6-astra'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = path.with_name(path.name + '.next')
    temporary.write_text(json.dumps(value, sort_keys=True, indent=2) + '\n')
    temporary.replace(path)


def utc(stamp):
    return datetime.fromtimestamp(stamp, timezone.utc).isoformat()


def process(pid):
    directory = Path('/proc') / str(pid)
    try:
        fields = directory.joinpath('stat').read_text().rsplit(') ', 1)[1].split()
        return dict(pid=pid, start_ticks=fields[19], state=fields[0],
            boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
            command_sha256=hashlib.sha256(directory.joinpath('cmdline').read_bytes()).hexdigest())
    except (FileNotFoundError, ProcessLookupError):
        return None


def backoff_seconds(headers, count, now):
    value = (headers or {}).get('Retry-After')
    fallback = min(300, 60 * 2 ** min(count - 1, 3))
    if value is None:
        return fallback
    try:
        delay = float(value)
    except (ValueError, TypeError):
        try:
            delay = parsedate_to_datetime(value).timestamp() - now
        except (ValueError, TypeError, OverflowError):
            return fallback
    return max(fallback, delay)


def install_backoff(module, policy):
    path = HERE / 'operator/RATE_LIMIT.json'
    cooldown = json.loads(path.read_text()) if path.exists() else dict(not_before_unix=0, consecutive_429=0)
    original_strong, original_tick = policy.parent.strong, module.tick_once

    def strong(*arguments, **keywords):
        if time.time() < cooldown['not_before_unix']:
            raise ValueError('provider_backoff_not_elapsed_no_dispatch')
        directory = Path(arguments[1])
        save(HERE / 'PROVIDER_ACTIVITY.json', dict(observed_utc=utc(time.time()), process=process(os.getpid()),
            phase='REQUEST_IN_PROGRESS', attempt=directory.name, model=MODEL, reasoning_effort='xhigh', retries=0))
        try:
            result = original_strong(*arguments, **keywords)
        except urllib.error.HTTPError as error:
            if error.code == 429:
                now = time.time()
                cooldown['consecutive_429'] += 1
                cooldown.update(not_before_unix=now + backoff_seconds(error.headers, cooldown['consecutive_429'], now),
                    observed_utc=utc(now), status='HTTP_429_BACKOFF_NO_RETRY_OF_CONSUMED_ATTEMPT')
                save(path, cooldown)
                save(HERE / 'PROVIDER_ACTIVITY.json', dict(observed_utc=utc(now), phase='RATE_LIMITED', attempt=directory.name,
                    http_status=429, not_before_utc=utc(cooldown['not_before_unix']), retries=0, process=process(os.getpid())))
            raise
        except Exception as error:
            save(HERE / 'PROVIDER_ACTIVITY.json', dict(observed_utc=utc(time.time()), phase='PROVIDER_FAILED',
                error_type=type(error).__name__, attempt=directory.name, retries=0, process=process(os.getpid())))
            raise
        request = json.loads((directory / 'API_REQUEST.json').read_text())
        if request['model'] != MODEL or request.get('reasoning') != {'effort': 'xhigh'}:
            raise ValueError('unchanged_exact_xhigh_provider_required')
        cooldown.update(not_before_unix=0, consecutive_429=0)
        save(path, cooldown)
        save(HERE / 'PROVIDER_ACTIVITY.json', dict(observed_utc=utc(time.time()), phase='PROVIDER_RESPONSE_RECEIVED',
            attempt=directory.name, model=MODEL, reasoning_effort='xhigh', API_REQUEST_sha256=sha(directory / 'API_REQUEST.json'),
            response_sha256=sha(directory / 'stdout.json'), publication_verified=False, process=process(os.getpid())))
        return result

    def tick(*arguments, **keywords):
        if time.time() < cooldown['not_before_unix']:
            return dict(status='PROVIDER_BACKOFF', not_before_unix=cooldown['not_before_unix'])
        return original_tick(*arguments, **keywords)

    policy.parent.strong, module.tick_once = strong, tick


def main():
    os.umask(0o077)
    preflight = json.loads((HERE / 'PREFLIGHT.json').read_text())
    for relative, expected in preflight['runner_pins'].items():
        if sha(HERE / relative) != expected:
            raise ValueError('pinned_recovery_runner_changed')
    if time.time() - preflight['observed_unix'] > 600:
        raise ValueError('fresh_P3_preflight_required')
    lock_path = HERE / 'operator/RECOVERY.lock'
    lock_path.parent.mkdir(exist_ok=True)
    with lock_path.open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with (LEDGER / 'PARENT_OPERATOR.lock').open('r') as previous:
            fcntl.flock(previous, fcntl.LOCK_EX | fcntl.LOCK_NB)
        sys.path.insert(0, str(OLD))
        import p3_retry_parent as parent
        original_load = parent.p3_lease_parent.load_on_renewed_wall

        def load():
            module, policy, config, manifest = original_load()
            install_backoff(module, policy)
            return module, policy, config, manifest

        parent.p3_lease_parent.load_on_renewed_wall = load
        parent.HERE = HERE
        state = dict(process=process(os.getpid()), started_utc=utc(time.time()), native_pid=699464,
            existing_ledger_preserved=True, model=MODEL, reasoning_effort='xhigh', native_signals=0,
            preflight_sha256=sha(HERE / 'PREFLIGHT.json'), phase='ENTERING_ORIGINAL_GATED_PARENT',
            argv=[sys.executable, '-B', str(HERE / 'runner.py')], original_parent_manifest_sha256=sha(OLD / 'P3_RETRY_PARENT_MANIFEST.json'))
        save(HERE / 'PROCESS.json', state)
        sys.argv = [str(OLD / 'p3_retry_parent.py'), 'serve']
        try:
            parent.main()
        except BaseException as error:
            save(HERE / 'EXIT.json', dict(observed_utc=utc(time.time()), process=process(os.getpid()),
                error_type=type(error).__name__, phase='EXITED_NO_AUTOMATIC_RELAUNCH', native_signals=0))
            raise SystemExit(1) from None
        save(HERE / 'EXIT.json', dict(observed_utc=utc(time.time()), phase='EXISTING_HORIZON_REACHED', native_signals=0))


if __name__ == '__main__':
    main()
