"""Bounded pipe capture; caller owns whole-job teardown, not just client PID."""

import os
import selectors
import time


def capture(process, stop_job, *, max_bytes=65536, timeout=25, teardown_timeout=5):
    if type(max_bytes) is not int or not 1 <= max_bytes <= 1048576:
        raise ValueError('bounded_output_required')
    if not 0 < timeout <= 120 or not 0 < teardown_timeout <= 10:
        raise ValueError('bounded_time_required')
    if process.stdout is None or process.stderr is None:
        raise ValueError('both_binary_pipes_required')
    started = time.monotonic()
    deadline = started + timeout
    data = {'stdout': bytearray(), 'stderr': bytearray()}
    received = 0
    reason = None
    teardown_error = None
    stopped = False
    with selectors.DefaultSelector() as selector:
        for name in data:
            pipe = getattr(process, name)
            os.set_blocking(pipe.fileno(), False)
            selector.register(pipe, selectors.EVENT_READ, name)
        try:
            while selector.get_map() or process.poll() is None:
                now = time.monotonic()
                if now >= deadline and reason is None:
                    reason = 'TIMEOUT'
                if reason is not None and not stopped:
                    stopped = True
                    try:
                        stop_job()
                    except Exception as error:
                        teardown_error = type(error).__name__ + ': ' + str(error)
                    deadline = time.monotonic() + teardown_timeout
                elif stopped and now >= deadline:
                    teardown_error = teardown_error or 'job_client_or_pipes_remain_after_teardown'
                    break
                for selected, events in selector.select(min(0.1, max(0, deadline - now))):
                    chunk = os.read(selected.fileobj.fileno(), 4096)
                    if not chunk:
                        selector.unregister(selected.fileobj)
                        continue
                    remaining = max(0, max_bytes - received)
                    data[selected.data].extend(chunk[:remaining])
                    received += len(chunk)
                    if received > max_bytes and reason is None:
                        reason = 'OUTPUT_LIMIT'
            return dict(stdout=bytes(data['stdout']), stderr=bytes(data['stderr']),
                retained_bytes=sum(len(value) for value in data.values()),
                observed_bytes=received, limit_reason=reason,
                teardown_called=stopped, teardown_error=teardown_error,
                returncode=process.poll(), elapsed_seconds=time.monotonic() - started)
        finally:
            for name in data:
                getattr(process, name).close()
