"""Launch unchanged grid science through the tested node5 idle-baseline scanner."""

import argparse
import json
import os
from pathlib import Path
import subprocess
from types import SimpleNamespace

from gpu import orch_r115_grid_native as native
import orch_r111_route_admission as node5


def scan(root):
    if os.geteuid() != 0:
        command = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
            'PYTHONPATH=' + str(native.SOURCE), 'python3', '-B', str(Path(__file__).resolve()),
            'scan', '--root', str(root)]
        return json.loads(subprocess.check_output(command, text=True, timeout=100))
    config = native.validate(root)
    native.admission.minor.pinned.policy = SimpleNamespace(DEVICES={config['physical']: config['uuid']},
        HOST_SHA=native.HOST_SHA, require=native.require,
        allocation=lambda index: native.require(index == config['physical'], 'assigned_device_only'))
    return node5.scan(config['physical'], root / 'SERVICE_IDENTITY.json')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('scan', 'guard'))
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    if args.mode == 'scan':
        print(json.dumps(scan(args.root), sort_keys=True))
    else:
        native.scan = scan
        native.guard(args.root)
