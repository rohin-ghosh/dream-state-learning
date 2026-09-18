import os
import signal
import subprocess
import sys

import pytest

from gpu.orch_r125_bounded_capture import capture


def execute(source, **limits):
    process = subprocess.Popen([sys.executable, '-c', source], stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    stops = []

    def stop():
        stops.append(True)
        os.killpg(process.pid, signal.SIGKILL)

    try:
        result = capture(process, stop, **limits)
        process.wait(timeout=2)
        return result, stops
    finally:
        if process.poll() is None:
            stop()
            process.wait(timeout=2)


def test_normal_output_and_error_are_preserved():
    result, stops = execute('import sys; print("ok"); print("err", file=sys.stderr)')
    assert result['stdout'] == b'ok\n'
    assert result['stderr'] == b'err\n'
    assert result['returncode'] == 0
    assert result['limit_reason'] is None
    assert not stops


def test_combined_output_budget_stops_job_once():
    result, stops = execute('import os; os.write(2,b"x"*100); os.write(1,b"y"*1000000)', max_bytes=256)
    assert result['retained_bytes'] == 256
    assert result['observed_bytes'] > 256
    assert result['limit_reason'] == 'OUTPUT_LIMIT'
    assert result['teardown_error'] is None
    assert len(stops) == 1


def test_silent_job_times_out():
    result, stops = execute('import time; time.sleep(20)', timeout=0.1)
    assert result['limit_reason'] == 'TIMEOUT'
    assert len(stops) == 1
    assert result['elapsed_seconds'] < 3


def test_exact_limit_is_not_truncation():
    result, stops = execute('import os; os.write(1,b"x"*256)', max_bytes=256)
    assert result['stdout'] == b'x' * 256
    assert result['limit_reason'] is None
    assert not stops


def test_descendant_holding_pipes_does_not_hang_capture():
    source = 'import os,time; child=os.fork(); time.sleep(20) if child==0 else None'
    result, stops = execute(source, timeout=0.2)
    assert result['limit_reason'] == 'TIMEOUT'
    assert result['teardown_error'] is None
    assert len(stops) == 1


@pytest.mark.parametrize('budget', [0, True, -1, 1048577])
def test_invalid_output_budget_rejected_without_execution(budget):
    with pytest.raises(ValueError, match='bounded_output'):
        capture(None, lambda: None, max_bytes=budget)
