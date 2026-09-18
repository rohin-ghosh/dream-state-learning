"""One 90-minute batch deadline; signal only process groups created by this guardian."""

import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import time

from organism_v6 import orch_code_channel as policy
from gpu.orch_code_channel_freeze import digest, write
from gpu.orch_code_bounded_source import verify_archive


PYTHON = '/localhome/local-rohing/v2/venv/bin/python'
MODEL = '/localhome/local-rohing/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28'
BUNDLE = '/tmp/astra_portable_37ec_20260914_attempt1'
SCANNER_ROOT = Path('/tmp/orch_l2_shared_20260914_attempt1')


def scan(root, arm, freeze, label, deadline):
    index, uuid = policy.DEVICES[arm]
    assert digest(SCANNER_ROOT / 'scanner.py') == freeze['scanner_sha256']
    assert digest(SCANNER_ROOT / 'service_exceptions.json') == freeze['service_exceptions_sha256']
    for attempt in range(10):
        if deadline - time.time() < 1:
            return False
        with (SCANNER_ROOT / 'service_exceptions.json').open() as services:
            try:
                result = subprocess.run(['python3', str(SCANNER_ROOT / 'scanner.py'), str(index), uuid],
                    stdin=services, capture_output=True, text=True, timeout=min(15, deadline - time.time()),
                    env=dict(os.environ, CUDA_VISIBLE_DEVICES=''))
            except subprocess.TimeoutExpired:
                write(root / f'{label}_{arm}_{attempt}.json', dict(clear=False, error='scanner_timeout'))
                return False
        try:
            report = json.loads(result.stdout)
        except ValueError:
            report = dict(clear=False, stdout=result.stdout, stderr=result.stderr)
        report['returncode'] = result.returncode
        write(root / f'{label}_{arm}_{attempt}.json', report)
        if result.returncode == 0 and report['clear']:
            target = next(line.split(',') for line in report['gpus'].splitlines()
                          if line.split(',')[0].strip() == str(index))
            assert target[1].strip() == uuid and 'A100' in target[2] and int(target[5]) <= 2
            return True
        unresolved = report.get('unresolved', [])
        if report.get('owners') or not unresolved or any(item.get('comm') not in ('sshd', 'sftp-server')
                                                       for item in unresolved):
            return False
        time.sleep(min(2, max(0, deadline - time.time())))
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True)
    parser.add_argument('--archive-sha256', required=True)
    options = parser.parse_args()
    root = Path(options.root).resolve()
    assert root == Path('/tmp/orch_code_channel_20260915_attempt1')
    source = root / 'source'
    assert digest(root / 'source.tar') == options.archive_sha256
    verified = verify_archive(root / 'source.tar', source)
    freeze_path = source / 'research_notes/analysis/orch_code_channel_20260915_attempt1/FREEZE.json'
    freeze = json.loads(freeze_path.read_text())
    prepared = json.loads((root / 'prepare/RESULT.json').read_text())
    assert prepared['status'] == 'PREPARED_NO_MODEL' and prepared['model_calls'] == 0
    assert prepared['freeze_sha256'] == digest(freeze_path) and prepared['base_verification']['verified']
    for relative, expected in freeze['files'].items():
        assert digest(source / relative) == expected
    started = time.time()
    deadline = started + 5400
    assert deadline < 1790463900 - 21600
    write(root / 'LIFETIME.json', dict(started_unix=started, deadline_unix=deadline,
        maximum_aggregate_gpu_hours=4.5, guardian_pid=os.getpid(), archive_sha256=options.archive_sha256,
        verified_source_files=verified, freeze_sha256=digest(freeze_path)))
    processes, logs, exits = {}, {}, {}
    environment = dict(os.environ, PYTHONPATH=str(source), HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
        OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', TOKENIZERS_PARALLELISM='false', PYTHONDONTWRITEBYTECODE='1')
    try:
        for arm in policy.ARMS:
            if not scan(root, arm, freeze, 'preGPU', deadline - 180):
                raise ValueError('resource_admission_failed:' + arm)
        for arm in policy.ARMS:
            index, uuid = policy.DEVICES[arm]
            logs[arm] = (root / f'{arm}.log').open('x')
            process = subprocess.Popen([PYTHON, '-B', '-m', 'gpu.orch_code_channel_screen',
                '--bundle', BUNDLE, '--model-dir', MODEL, '--freeze', str(freeze_path),
                '--output', str(root / arm), '--phase', 'screen', '--arm', arm,
                '--deadline', str(deadline)], cwd=source, start_new_session=True,
                env=dict(environment, CUDA_VISIBLE_DEVICES=uuid), stdout=logs[arm], stderr=subprocess.STDOUT)
            processes[arm] = process
            write(root / f'PROCESS_{arm}.json', dict(pid=process.pid, pgid=process.pid,
                stat=Path(f'/proc/{process.pid}/stat').read_text(), gpu_uuid=uuid, physical_index=index))
        while any(process.poll() is None for process in processes.values()) and time.time() < deadline - 60:
            time.sleep(2)
    except BaseException as error:
        write(root / 'GUARD_FAILED.json', dict(error_type=type(error).__name__, error=str(error)))
        raise
    finally:
        for arm, process in processes.items():
            if process.poll() is None:
                assert os.getpgid(process.pid) == process.pid
                os.killpg(process.pid, signal.SIGINT)
                try:
                    process.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    if process.poll() is None and os.getpgid(process.pid) == process.pid:
                        os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=5)
            exits[arm] = process.returncode
            logs[arm].close()
        releases = {arm: scan(root, arm, freeze, 'release', deadline - 2) for arm in policy.ARMS}
        write(root / 'TERMINAL.json', dict(exits=exits, releases=releases, completed_unix=time.time(),
            elapsed_seconds=time.time() - started, conservative_gpu_hours=3 * (time.time() - started) / 3600))


if __name__ == '__main__':
    main()
