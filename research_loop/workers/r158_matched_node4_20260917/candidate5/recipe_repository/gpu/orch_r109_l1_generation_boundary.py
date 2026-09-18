"""Fast owned-boundary holder; the immutable V3 supervisor performs retirement."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import time


ORIGIN = Path('/localhome/local-rohing/orch_r109_l1_20260915')
END = 1789491360


def read(path):
    return json.loads(path.read_text())


def candidate(directory):
    progress = read(directory/'PROGRESS.json')
    count = progress['calls']
    return (not (directory/f'INTENT_{count+1:06d}.json').exists()
        and (directory/f'CALL_{count:06d}.json').exists()),progress


def hold(index):
    import orch_r109_l1_generation_v3 as runner
    from gpu.orch_r109_l1_ops import identity
    from gpu.orch_r109_l1_train import write
    from gpu.orch_math_rich_source import verify_archive
    plan = runner.verify()
    assert index in plan['lanes']
    receipt = read(runner.ROOT/'BOUNDARY_PRE_GPU.json')
    assert receipt['cpu_passed'] and receipt['source_sha256'] == hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    assert receipt['builder_line'].startswith('[Builder]')
    source = Path(__file__).parent
    archive = source.parent/'source.tar'
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == receipt['archive_sha256']
    assert verify_archive(archive,source) == 2
    assert {path.name for path in source.glob('*.py')} == {
        'orch_r109_l1_generation_boundary.py','test_orch_r109_l1_generation_boundary.py'}
    expected = read(ORIGIN/f'generation_{index}_LAUNCH.json')['identity']
    assert expected['uid'] == os.getuid() and identity(expected['pid']) == expected
    directory = ORIGIN/'generation'/f'gpu{index}'
    release = runner.ROOT/f'RELEASE_{index}.json'
    if release.exists():return
    descriptor = os.pidfd_open(expected['pid'])
    held = False
    try:
        while time.time() < END-900 and not release.exists():
            assert identity(expected['pid']) == expected
            possible,progress = candidate(directory)
            if possible:
                signal.pidfd_send_signal(descriptor,signal.SIGSTOP)
                held = True
                runner.wait_stopped(expected['pid'])
                possible,after = candidate(directory)
                if possible and after == progress:
                    last = read(directory/f'CALL_{progress["calls"]:06d}.json')
                    episode = directory/f'EPISODE_{progress["batch"]:03d}_{progress["position"]:02d}.json'
                    assert last['family'] != 'route' or episode.exists()
                    assert not list(directory.glob('FAILED_*.json'))
                    write(runner.ROOT/f'FAST_BOUNDARY_HOLD_{index}.json',dict(identity=expected,index=index,
                        progress=progress,observed_unix=time.time(),source_sha256=receipt['source_sha256'],
                        stop_acknowledged=True,retirement_by_existing_supervisor_only=True))
                    while time.time() < END-900 and not release.exists():
                        if (runner.ROOT/f'FAILURE_{index}.json').exists():
                            raise RuntimeError('owner_supervisor_failed_while_holding')
                        time.sleep(.01)
                    if release.exists():return
                    break
                signal.pidfd_send_signal(descriptor,signal.SIGCONT)
                held = False
            time.sleep(.0001)
    except (FileNotFoundError,ProcessLookupError):
        assert release.exists(),'unexpected_owned_generator_exit'
    finally:
        if held and not release.exists():
            try:signal.pidfd_send_signal(descriptor,signal.SIGCONT)
            except ProcessLookupError:pass
        os.close(descriptor)


if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--index',type=int,required=True)
    hold(parser.parse_args().index)
