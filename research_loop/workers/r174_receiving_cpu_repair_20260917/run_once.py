"""Consume one local latch and one sanctioned wrapper invocation; never retry."""

import base64
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import shlex
import subprocess
import sys


OWNED = Path(__file__).resolve().parent
REPO = OWNED.parents[2]
specification = importlib.util.spec_from_file_location('r173_receiving_cpu', OWNED / 'receiving_cpu.py')
receiving = importlib.util.module_from_spec(specification)
specification.loader.exec_module(receiving)


def payload():
    pins = dict(receiving.HELPERS, **receiving.TESTS, **receiving.TEST_SUPPORT,
                **{receiving.FIXTURE: receiving.FIXTURE_SHA256})
    files = {}
    for name, checksum in pins.items():
        raw = (REPO / name).read_bytes()
        receiving.require(receiving.sha(raw) == checksum, 'local_transfer_pin:' + name)
        files[name] = base64.b64encode(raw).decode()
    runner = (OWNED / 'receiving_cpu.py').read_bytes()
    return dict(files=files, runner=base64.b64encode(runner).decode(), runner_sha256=receiving.sha(runner))


def command():
    bootstrap = ('import base64,json,sys; payload=json.load(sys.stdin); '
                 'namespace={"__name__":"r173_receiving_cpu"}; '
                 'exec(compile(base64.b64decode(payload["runner"],validate=True),'
                 '"<R173_transferred_receiving_cpu>","exec"),namespace); '
                 'sys.stdout.buffer.write(namespace["execute"](payload))')
    remote = ('env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 '
              'HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1 '
              'OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 '
              '/localhome/local-rohing/v2/venv/bin/python -I -B -c ' + shlex.quote(bootstrap))
    return ['bash', str(REPO / 'gpu/ovx2_ssh.sh'), remote]


def run_once(output=OWNED, invoke=subprocess.run):
    prepared = payload()
    bundle = receiving.encoded(prepared)
    invocation = command()
    marker = dict(schema='R173_SINGLE_ATTEMPT_LATCH_V1', started_utc=datetime.now(timezone.utc).isoformat(),
        payload_sha256=receiving.sha(bundle), runner_sha256=prepared['runner_sha256'],
        wrapper='gpu/ovx2_ssh.sh', command=invocation[-1], retry_permitted=False,
        scratch=receiving.SCRATCH)
    receiving.write_once(output / 'ATTEMPT_STARTED.json', receiving.encoded(marker))
    receiving.write_once(output / 'PAYLOAD_MANIFEST.json', receiving.encoded(dict(
        files=dict(receiving.HELPERS, **receiving.TESTS, **receiving.TEST_SUPPORT,
                   **{receiving.FIXTURE: receiving.FIXTURE_SHA256}),
        runner_sha256=marker['runner_sha256'], payload_sha256=marker['payload_sha256'])))
    try:
        result = invoke(invocation, input=bundle, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    except BaseException as error:
        receiving.write_once(output / 'WRAPPER_FAILURE.json', receiving.encoded(dict(
            type=type(error).__name__, error=str(error), retry_permitted=False)))
        raise
    receiving.write_once(output / 'WRAPPER_STDOUT.txt', result.stdout)
    receiving.write_once(output / 'WRAPPER_STDERR.txt', result.stderr)
    receiving.write_once(output / 'WRAPPER_RESULT.json', receiving.encoded(dict(
        returncode=result.returncode, stdout_sha256=receiving.sha(result.stdout),
        stderr_sha256=receiving.sha(result.stderr), retry_permitted=False,
        ended_utc=datetime.now(timezone.utc).isoformat())))
    receipt = json.loads(result.stdout)
    receiving.require(receipt['schema'] == 'R173_ACTUAL_RECEIVING_CPU_V1'
                      and receipt['scratch'] == receiving.SCRATCH, 'actual_receiving_receipt')
    receiving.write_once(output / 'ACTUAL_RECEIVING_CPU.json', result.stdout)
    print(json.dumps({key: receipt.get(key) for key in (
        'status', 'success', 'tests_run', 'failures', 'errors', 'skipped', 'failure',
        'evidence_rebind_eligible', 'started_utc', 'ended_utc')}, indent=2))
    return 0 if result.returncode == 0 and receipt['success'] else 1


if __name__ == '__main__':
    sys.exit(run_once())
