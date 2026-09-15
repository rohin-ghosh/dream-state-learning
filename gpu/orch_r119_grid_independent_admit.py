"""Preserve pre-model admission failure; require a fresh unchanged clear scan."""

import argparse
import importlib.util
import json
import os
from pathlib import Path
import time


ERA = 'independent_r119_recovery_v2'
TERMINAL = 'R119_GRID_INDEPENDENT_RECOVERY_V2_TERMINAL.json'


def stable_scan(scanner, save, attempts=8):
    for attempt in range(attempts):
        report = scanner()
        save(attempt, report)
        if report['clear'] and report['scanner_euid'] == 0 and not report['blocking_reasons']:
            return report
        time.sleep(.25)
    return report


def load():
    path = Path(__file__).with_name('orch_r119_grid_independent_recover.py')
    spec = importlib.util.spec_from_file_location('previous_grid_recovery', path)
    recovery = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(recovery)
    recovery.ERA = ERA
    base = recovery.loader()
    base.ERA, base.TERMINAL = ERA, TERMINAL
    original_configure, original_scan = base.configure, base.scan

    def configure(branch):
        grid, admission, root, config, checkpoint = original_configure(branch)
        failure = grid.read(root / 'R119_GRID_INDEPENDENT_RECOVERY_TERMINAL.json')
        recovery.require(failure['status'] == 'FAILED' and failure['reason'] == 'fresh_privileged_admission'
            and not (root / 'independent_r119_recovery_v1/LAUNCH.json').exists(), 'preserved_premodel_failure')
        writer = grid.write

        def write(path, document, replace=False):
            if Path(path) == root / ERA / 'READY.json':
                document = dict(document, source_files=dict(document['source_files'],
                    **{str(Path(__file__).resolve()): grid.sha(__file__)}),
                    admission_failure=grid.ref(root / 'R119_GRID_INDEPENDENT_RECOVERY_TERMINAL.json'))
            return writer(path, document, replace=replace)

        grid.write = write
        return grid, admission, root, config, checkpoint

    def scan(branch):
        if os.geteuid() == 0:
            return original_scan(branch)
        grid, admission, root, config, checkpoint = configure(branch)
        return stable_scan(lambda: original_scan(branch),
            lambda number, report: grid.write(root / ERA / 'admission' / f'{number:03d}.json', report))

    base.configure, base.scan, base.__file__ = configure, scan, __file__
    return recovery, base


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('cpu', 'guard', 'native', 'scan'))
    parser.add_argument('--branch', choices=('A4',), required=True)
    arguments = parser.parse_args()
    recovery, base = load()
    if arguments.mode == 'cpu':
        recovery.cpu(base)
    elif arguments.mode == 'native':
        recovery.native(base)
    else:
        result = getattr(base, arguments.mode)('A4')
        if result is not None:
            print(json.dumps(result))
