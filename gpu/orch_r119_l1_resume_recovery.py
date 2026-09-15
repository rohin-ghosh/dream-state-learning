"""CONTROL-only recovery; scanner execution errors remain blocking, never clear."""

import argparse
import hashlib
import importlib.util
from pathlib import Path
import subprocess


def guarded_scan(scanner, index, service):
    try:
        return scanner(index, service)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as failure:
        details = repr((getattr(failure, 'returncode', None), getattr(failure, 'stdout', None),
                        getattr(failure, 'stderr', None))).encode()
        return dict(clear=False, scanner_euid=None, blocking_reasons=[
                    'strict_scanner_execution_failure:' + type(failure).__name__],
                    error_details_sha256=hashlib.sha256(details).hexdigest(),
                    ownership_not_verified=True, no_gpu_launch=True)


def execute(root):
    from gpu import orch_combined_l1_continual_run as admission
    path = root / 'orch_r119_l1_resume.py'
    spec = importlib.util.spec_from_file_location('frozen_continuation', path)
    frozen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(frozen)
    recovery = frozen.trainer.read(root/'RECOVERY.json')
    assert recovery['arm'] == 'CONTROL' and recovery['physical'] == 1
    assert frozen.trainer.sha(__file__) == recovery['recovery_source_sha256']
    assert frozen.trainer.sha(root/'CONTINUATION.json') == recovery['continuation_sha256']
    assert not Path('/proc',str(recovery['prior_supervisor']['pid'])).exists()
    scanner = admission.scan
    admission.scan = lambda index, service: guarded_scan(scanner,index,service)
    frozen.supervise(root,'CONTROL')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    execute(parser.parse_args().root)
