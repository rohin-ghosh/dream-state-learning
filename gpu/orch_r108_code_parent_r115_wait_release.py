"""Start A3 only after the grid owner's explicit exact-process cycle release."""

import argparse
import os
from pathlib import Path
import subprocess
import sys
import time

from gpu import orch_r108_code_parent_r115_guard as guard


def wait_release(root):
    run = guard.run
    plan = guard.verify(root)
    run.policy.require(plan['physical'] == 6 and os.environ.get('CUDA_VISIBLE_DEVICES') == '',
        'cpu_waiter_A3_only')
    (root / 'WAIT_RELEASE_ONCE').mkdir()
    source = root / 'admission_source'
    for relative, expected in run.read(root / 'ADMISSION_SOURCE_SHA256.json').items():
        run.policy.require(run.sha(source / relative) == expected, 'immutable_admission_source')
    previous = Path('/localhome/local-rohing/orch_r109_grid_node5_6_20260915_attempt1/R115_HANDOFF')
    while time.time() < plan['hard_deadline_unix'] - 180:
        path = previous / 'RELEASE.json'
        if not path.exists():
            time.sleep(5)
            continue
        release = run.read(path)
        run.policy.require(release['exited'] is True and release['physical'] == 6
            and release['receiver'] == 'Cicero', 'explicit_owner_cycle_release')
        original = run.read(previous / 'REQUEST.json')['identity']
        process = Path('/proc') / str(release['prior_pid'])
        run.policy.require(original['pid'] == release['prior_pid'], 'same_released_process')
        if process.exists() and (process / 'stat').read_text().rsplit(')', 1)[1].split()[0] != 'Z':
            time.sleep(5)
            continue
        run.write_new(root / 'PREDECESSOR_RELEASE.json', dict(explicit_owner_release=True,
            physical=6, native_path=str(path), native_sha256=run.sha(path), release=release,
            original_identity=original, request_sha256=run.sha(previous / 'REQUEST.json'),
            observed_unix=time.time()))
        with (root / 'guard.log').open('x') as log:
            child = subprocess.Popen([sys.executable, '-B', '-m',
                'gpu.orch_r108_code_parent_r115_admission', 'guard', '--root', str(root)],
                cwd=source, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                start_new_session=True, env=dict(os.environ, PYTHONPATH=str(source)))
        run.write_new(root / 'WAIT_RELEASE_GUARD_STARTED.json', dict(
            identity=guard.scanner.pinned.identity(Path('/proc') / str(child.pid)),
            observed_unix=time.time(), native_dispatched=False,
            note='Guardian still must pass fresh full privileged UUID/minor/proc admission'))
        return
    run.write_new(root / 'WAIT_RELEASE_EXPIRED.json', dict(native_dispatched=False,
        observed_unix=time.time(), deadline_unchanged=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    wait_release(parser.parse_args().root)
