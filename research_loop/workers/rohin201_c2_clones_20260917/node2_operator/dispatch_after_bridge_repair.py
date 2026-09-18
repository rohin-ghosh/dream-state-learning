"""Explicit pre-native repair: use the tested math package, not native gpu package."""

import os
from pathlib import Path
import sys
import time

from receive_math_d import ROOT, SOURCE, read, sha, write, require
from launch_math_d_v2 import dispatch


def main():
    require(not (ROOT / 'FIRST_INPUTS.json').exists() and not (ROOT / 'control/LAUNCH.json').exists()
        and not (ROOT / 'STARTED.json').exists(), 'proved_no_native_or_first_input_before_repair')
    for process in Path('/proc').iterdir():
        if not process.name.isdigit():
            continue
        try:
            if process.stat().st_uid != os.getuid():
                continue
            arguments = (process / 'cmdline').read_bytes().decode().split('\0')
            require(str(ROOT / 'BRIDGE.json') not in arguments, 'no_existing_bridge_actor')
        except (FileNotFoundError, PermissionError):
            continue
    require('gate_build_and_boot_binding' in (ROOT / 'cpu_bridge.log').read_text(), 'known_pre_native_import_path_failure')
    pins = {str(path.relative_to(SOURCE)): sha(path) for path in SOURCE.rglob('*.py')}
    require(pins == read(ROOT / 'CPU.json')['source_pins'], 'unchanged400_tested_runtime')
    sys.path.insert(0, str(SOURCE))
    from gpu import orch_r125_continual_guard as guard
    guard.validate(ROOT / 'control/GUARD.json')
    first = ROOT / 'R202_PART_ONE.txt'
    expected = '48921afaf6c1a7dec7fbe7cbb79c3be8c52bd9612cbcdad3ff6da64fc7469e30'
    require(sha(first) == expected, 'exact_authorized_first_input')
    write(ROOT / 'PRE_NATIVE_BRIDGE_REPAIR.json', dict(observed_unix=time.time(), original_failure_log='cpu_bridge.log',
        failure='Module-mode gpu package selected native stdlib profile; corrected standalone script selects actual math source',
        repair='Invocation only; no runtime/source/test/plan/checkpoint bytes changed', no_prior_native=True,
        no_prior_publications=True, no_stop_or_restart=True, explicit_once_only=True))
    dispatch(first.read_text(), expected, bridge_name='cpu_bridge2')


if __name__ == '__main__':
    main()
