"""R206 release binding for the existing exact-boundary continuation helper."""

import importlib.util
from pathlib import Path
import sys
import time


ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('node1_existing_continuation', ROOT/'continue_r204.py')
continuation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(continuation)
continuation.ROOT = ROOT
continuation.RELEASE = 'R206'
continuation.READY_SHA = '77c98baa295964118caeb58e7a0b6a2ad1f1c52c6703d3cb15f989cfed38b2ad'
continuation.OVERLAY_SHA = 'ab7c3ada0780d8414aba30e59721df1bb8c51fdee747105359682bae3c144f84'
continuation.__file__ = str(Path(__file__).resolve())


if __name__ == '__main__':
    actions = {'run': continuation.run, 'resume-staged': continuation.resume_staged,
        'handoff': continuation.handoff, 'verify-saved': continuation.verify_saved}
    try:
        actions[sys.argv[1]]()
    except Exception as error:
        continuation.write(ROOT/('CONTINUATION_FAILURE_'+str(time.time_ns())+'.json'),
            dict(observed_unix=time.time(), error_type=type(error).__name__, reason=str(error),
                retired=(ROOT/'RETIRED.json').exists(), no_automatic_retry=True))
        raise
