"""Deliver versioned FULL checkpoint handoffs locally without waiting for scores."""

import argparse
from pathlib import Path
import subprocess
import time
import json

from organism_v6.orch_combined_l1_continual import atomic_json


def watch(repository, output, until):
    remote = '/localhome/local-rohing/orch_combined_l1_continual_20260915_attempt1'
    while time.time() < until:
        result = subprocess.run(['bash', str(repository / 'gpu/a100_ssh.sh'),
            f'test ! -f {remote}/FULL_CHILD_HANDOFF.json || cat {remote}/FULL_CHILD_HANDOFF.json'],
            capture_output=True, text=True, timeout=40)
        if result.returncode == 0 and result.stdout.strip():
            record = json.loads(result.stdout)
            assert record['schema'] == 'COMBINED_CONTINUAL_FULL_CHILD_READY_V1'
            assert record['held_results_required'] is False and record['recipient'] == 'Anscombe'
            version = output / 'HANDOFFS' / f'{record["updates"]:09d}.json'
            if not version.exists():
                atomic_json(version, record)
                atomic_json(output / 'FULL_CHILD_HANDOFF.json', record)
                atomic_json(output / 'HANDOFF_DELIVERED.json', dict(recipient='Anscombe',
                    handoff_path=str(version), child_path=record['child_path'],
                    updates=record['updates'], delivered_unix=time.time(), held_scores_waited_for=False))
        time.sleep(10)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--repository', type=Path, default=Path.cwd())
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--until', type=float, required=True)
    options = parser.parse_args()
    watch(options.repository.resolve(), options.output.resolve(), options.until)
