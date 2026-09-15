"""Copy completed FULL child handoff before readout results, without GPU calls."""

import argparse
import json
from pathlib import Path
import subprocess
import time

from gpu.orch_l2_rich_math_bootstrap import write


def watch(repository, output, until):
    remote = '/localhome/local-rohing/orch_combined_l1_20260915_attempt1'
    command = f'test ! -f {remote}/FULL_CHILD_HANDOFF.json || cat {remote}/FULL_CHILD_HANDOFF.json'
    while time.time() < until:
        result = subprocess.run(['bash', str(repository / 'gpu/a100_ssh.sh'), command],
            capture_output=True, text=True, timeout=30)
        if result.returncode == 0 and result.stdout.strip():
            record = json.loads(result.stdout)
            assert record['schema'] == 'COMBINED_L1_FULL_CHILD_READY_V1'
            assert record['status'] == 'FIT_COMPLETE_HELD_SCORES_NOT_REQUIRED'
            assert record['recipient'] == 'Anscombe' and record['updates'] == 19248
            write(output / 'FULL_CHILD_HANDOFF.json', record)
            write(output / 'HANDOFF_DELIVERED.json', dict(recipient='Anscombe', delivered_unix=time.time(),
                held_scores_waited_for=False, handoff_path=str(output / 'FULL_CHILD_HANDOFF.json'),
                child_path=record['child_path'], transport='Native A100 registry copied to shared local evidence'))
            return
        time.sleep(20)
    write(output / 'HANDOFF_NOT_READY.json', dict(status='NO_COMPLETED_FULL_CHILD_AT_DEADLINE',
        finished_unix=time.time(), no_false_child=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--repository', type=Path, default=Path.cwd())
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--until', type=float, required=True)
    options = parser.parse_args()
    watch(options.repository.resolve(), options.output.resolve(), options.until)
