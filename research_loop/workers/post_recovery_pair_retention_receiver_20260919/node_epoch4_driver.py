"""Bounded operator-only diagnostic subprocesses; full journal/proof stays on node."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from remote_epoch4_stage import ROOT, LIVES, checksum, exact_native, inventory, read, require
from node_epoch4_probe import PAIR, write_once


HERE = Path(__file__).resolve().parent
PYTHON = '/localhome/local-rohing/v2/venv/bin/python'


def execute(phase, life):
    observation = read(HERE / 'OBSERVATIONS.json')[life]
    before = exact_native(observation)
    source = ROOT / life / 'epoch4/source'
    manifest = read(source.parent / 'EPOCH4_SOURCE.json')
    require(inventory(source) == manifest['new_source_pins'], 'exact_immutable_receiving_source_before')
    life_root = HERE / life
    life_root.mkdir(exist_ok=True)
    request = life_root / 'REQUEST.json'
    write_once(request, dict(observation=observation, life_root=str(life_root)))
    attempt = life_root / (phase + '_' + str(time.time_ns()))
    attempt.mkdir(mode=0o700)
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1',
        OMP_NUM_THREADS='1', PYTHONPATH=str(source))
    tools = ROOT / 'pair_operator_bundle_v4' / PAIR
    if phase == 'source-tests':
        environment['TMPDIR'] = str(attempt)
        commands = [[PYTHON, '-B', str(tools / name), '--source', str(source)]
            for name in ('source_checks.py', 'prefix_source_checks.py')]
    elif phase == 'native-view':
        proof = life_root / 'PROOF.json'
        commands = [[PYTHON, '-B', str(HERE / 'native_view_probe.py'), '--proof', str(proof),
            '--proof-sha256', checksum(proof.read_bytes()), '--pid', str(observation['native']['pid']),
            '--start-ticks', observation['native']['start_ticks'], '--uid', str(observation['native']['uid'])]]
    else:
        require(phase in ('select', 'checkpoint', 'produce', 'read'), 'CPU_phases_only')
        commands = [[PYTHON, '-B', str(HERE / 'node_epoch4_probe.py'), phase, '--request', str(request)]]
    results = []
    for index, command in enumerate(commands):
        started = time.monotonic()
        try:
            process = subprocess.run(command, cwd=source, env=environment, capture_output=True,
                text=True, check=False, timeout=240, close_fds=True)
            elapsed = time.monotonic() - started
            output = json.loads(process.stdout) if process.returncode == 0 else None
            result = dict(command=command, returncode=process.returncode, elapsed_seconds=elapsed, result=output,
                stdout_sha256=checksum(process.stdout.encode()), stderr_sha256=checksum(process.stderr.encode()))
            if process.returncode:
                result['stderr_tail'] = process.stderr[-4096:]
            write_once(attempt / (str(index) + '.PROCESS.json'), dict(result, stdout=process.stdout, stderr=process.stderr))
        except subprocess.TimeoutExpired as error:
            result = dict(command=command, returncode=None, elapsed_seconds=time.monotonic() - started,
                status='CPU_HELPER_TIMEOUT_NO_NATIVE_ACTION', timeout_seconds=240)
            write_once(attempt / (str(index) + '.PROCESS.json'), result)
        results.append(result)
        if result.get('returncode') != 0 or (result.get('result') or {}).get('status') == 'CPU_DIAGNOSTIC_REFUSED_NO_NATIVE_ACTION':
            break
    require(inventory(source) == manifest['new_source_pins'], 'receiving_source_untouched_after')
    after = exact_native(observation)
    receipt = dict(status='PAIR_EPOCH4_CPU_DIAGNOSTIC_ONLY', phase=phase, life=life, remote_artifacts=str(attempt),
        results=results, before=before, after=after, old_native_source_guard_unchanged=True,
        source_unchanged=True, source=str(source), source_file_count=len(manifest['new_source_pins']),
        native_signals=[], parent_actions=[], reservations=[], GPU_calls=0, journal_writes=0,
        receiving_admission_proven=False, handoff_eligible_claim=False)
    write_once(attempt / 'RECEIPT.json', receipt)
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('source-tests', 'select', 'checkpoint', 'produce', 'read', 'native-view'))
    parser.add_argument('life', choices=LIVES)
    args = parser.parse_args()
    print(json.dumps(execute(args.phase, args.life), sort_keys=True, allow_nan=False))
