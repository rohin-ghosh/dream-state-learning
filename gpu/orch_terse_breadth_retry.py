"""Retry failed admission only; never rerun a native stage that created output."""

import json
from pathlib import Path
import subprocess
import sys
import time


def retryable(root, lane, phase):
    stage = f'{phase}{lane}'
    native = root / stage
    resource = root / f'launch_{stage}/RESOURCE.json'
    if native.exists() or not resource.is_file():
        return False
    return json.loads(resource.read_text()).get('clear') is False


def main(argv=None):
    arguments = list(sys.argv[1:] if argv is None else argv)
    if len(arguments) != 7:
        raise ValueError('exact_original_guard_arguments_required')
    root, lane, phase = Path(arguments[0]), arguments[1], arguments[2]
    if phase not in ('train', 'after', 'baseline') or lane not in ('0', '1', '2', '3', '4', '5'):
        raise ValueError('fixed_fit_readout_stage_required')
    for attempt in range(6):
        result = subprocess.run(['bash', str(root / 'source/gpu/orch_terse_breadth_guard.sh'), *arguments])
        if result.returncode == 0 or not retryable(root, lane, phase):
            return result.returncode
        archived = root / 'admission_failures' / f'{phase}{lane}_{time.time_ns()}'
        archived.parent.mkdir(exist_ok=True)
        (root / f'launch_{phase}{lane}').rename(archived)
        if attempt < 5:
            time.sleep(10)
    return 1


if __name__ == '__main__':
    sys.exit(main())
