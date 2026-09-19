"""Deliver only reviewed additions and CPU proof inputs to unique original-node staging."""

import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

from run_approved_canary import encoded_command


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]


def main():
    files = []

    def add(surface, destination, raw):
        files.append(dict(surface=surface, path=destination, sha256=hashlib.sha256(raw).hexdigest(),
            content=base64.b64encode(raw).decode()))

    for name in ['pending_sleep_contract.py', 'math_b_runtime_candidate.py', 'math_b_startup.py',
            'checkpoint_tail_runtime.py', 'recovery_primitives.py']:
        add('source', name, (HERE / name).read_bytes())
    add('source', 'gpu/ws6_math_b_pending_entry.py', (HERE / 'ws6_math_b_pending_entry.py').read_bytes())
    for name in ['test_pending_sleep_contract.py', 'test_math_b_runtime_candidate.py',
            'test_math_b_startup.py', 'test_original_confinement_chain.py']:
        add('control', 'receiving_tests/' + name, (HERE / name).read_bytes())
    support = 'test_support/research_loop/workers/post_recovery_node2_sleep_20260919/'
    for directory in ['test_support/research_loop', 'test_support/research_loop/workers',
            support.rstrip('/'), support + 'runtime_candidate']:
        add('control', directory + '/__init__.py', b'')
    fixture_root = REPO / 'research_loop/workers/post_recovery_node2_sleep_20260919'
    for name in ['restart_contract.py', 'runtime_candidate/receiving_fixture.py']:
        add('control', support + name, (fixture_root / name).read_bytes())
    payload = dict(gpu_launch_authorized=False, files=files,
        test_source_evidence=[str(path.relative_to(HERE / 'source_evidence'))
            for path in (HERE / 'source_evidence').rglob('*.py')])
    with (HERE / 'MATH_B_STAGING_REQUEST.json').open('x') as output:
        json.dump(dict(utc=datetime.now(timezone.utc).isoformat(),
            worker_sha256=hashlib.sha256((HERE / 'math_b_receiving_worker.py').read_bytes()).hexdigest(),
            inputs=[{key: value for key, value in entry.items() if key != 'content'} for entry in files],
            native_or_GPU_launch_authorized=False), output, indent=2)
    command = '/usr/bin/env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 ' + encoded_command(
        (HERE / 'math_b_receiving_worker.py').read_text()).replace('python3 -u -B',
            '/localhome/local-rohing/v2/venv/bin/python -u -B', 1)
    with (HERE / 'MATH_B_RECEIVING_PROGRESS.jsonl').open('x') as output, \
            (HERE / 'MATH_B_RECEIVING.stderr').open('x') as errors:
        result = subprocess.run(['bash', str(REPO / 'gpu/ovx2_ssh.sh'), command],
            input=json.dumps(payload) + '\n', stdout=output, stderr=errors, text=True, timeout=300)
    if result.returncode:
        raise RuntimeError('MathB staging/receiving failed; preserve all artifacts, no automatic retry')


if __name__ == '__main__':
    main()
