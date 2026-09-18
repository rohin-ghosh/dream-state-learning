import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time


def persist(path, value):
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, 'w') as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    Path(path).chmod(0o400)


def recording_profile(target, destination):
    def record(frame, event, result):
        if frame.f_code is target.__code__ and event == 'return':
            persist(destination, dict(schema='R159_ACTUAL_DISPATCH_SCAN_CAPTURE_V1',
                observed_unix=time.time(), report=result,
                label='ACTUAL_NEW_DISPATCH_SCAN_NOT_HISTORICAL_RECOVERY'))
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True)
    parser.add_argument('--go', required=True)
    parser.add_argument('--operator', required=True)
    parser.add_argument('--source', required=True)
    args = parser.parse_args()
    directory = Path(args.operator)
    sys.path.insert(0, args.source)
    from gpu import orch_r159_matched_evaluation as evaluator
    from gpu import orch_r130_benchmark_sidecar as sidecar
    assert evaluator.sha(evaluator.__file__) == '100e952409e9e76eb143db2d8f5a504ea8120593e52f85b56f19b07fd7d0bafc'
    time.sleep(5)
    initiator = evaluator.read(directory / 'INITIATOR.json')
    assert sidecar.gone(initiator['identity']), 'initiating_transport_not_released'
    assert time.time() < 1789628385, 'full_window_required'
    assert sys.getprofile() is None
    profile = recording_profile(sidecar.scan, directory / 'ACTUAL_ADMISSION.private.json')
    persist(directory / 'WRAPPER_STARTED.json', dict(identity=sidecar.identity(os.getpid()),
        wrapper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        observed_unix=time.time(), initiator_gone=True, source_changed=False))
    try:
        sys.setprofile(profile)
        result = evaluator.dispatch(Path(args.config), Path(args.go))
    except BaseException as error:
        sys.setprofile(None)
        persist(directory / 'DISPATCH_ERROR.json', dict(status='ERROR_NO_RETRY',
            error_type=type(error).__name__, observed_unix=time.time()))
        raise
    finally:
        sys.setprofile(None)
    persist(directory / 'DISPOSITION.json', dict(result=result, observed_unix=time.time(),
        admission_sha256=evaluator.sha(directory / 'ACTUAL_ADMISSION.private.json')))


if __name__ == '__main__':
    main()
