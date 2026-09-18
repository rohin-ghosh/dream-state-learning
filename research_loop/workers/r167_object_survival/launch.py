import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('start', 'worker'))
    parser.add_argument('--config', required=True)
    parser.add_argument('--go', required=True)
    parser.add_argument('--go-sha256', required=True)
    parser.add_argument('--source', required=True)
    parser.add_argument('--directory', required=True)
    args = parser.parse_args()
    sys.path.insert(0, args.source)
    from gpu import orch_r167_object_survival_eval as evaluator
    from gpu import orch_r130_benchmark_sidecar as sidecar
    directory = Path(args.directory)
    assert evaluator.sha(args.go) == args.go_sha256
    os.environ['R167_MAIN_GO_SHA256'] = args.go_sha256
    evaluator.validate(args.config, args.go)
    if args.action == 'start':
        directory.mkdir(parents=True, mode=0o700, exist_ok=False)
        evaluator.write(directory / 'INITIATOR.json', dict(identity=sidecar.identity(os.getpid())))
        command = [sys.executable, '-B', str(Path(__file__).resolve()), 'worker', *sys.argv[2:]]
        with (directory / 'wrapper.private.log').open('x') as log:
            process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                cwd=directory, start_new_session=True, close_fds=True)
        print(json.dumps(dict(status='WRAPPER_STARTED_NOT_YET_ADMITTED', identity=sidecar.identity(process.pid))))
        return
    time.sleep(5)
    assert sidecar.gone(evaluator.read(directory / 'INITIATOR.json')['identity'])
    evaluator.write(directory / 'WRAPPER.json', dict(identity=sidecar.identity(os.getpid()), created_unix=time.time()))
    try:
        result = evaluator.dispatch(args.config, args.go)
        evaluator.write(directory / 'DISPOSITION.json', result)
    except BaseException as error:
        evaluator.write(directory / 'DISPATCH_ERROR.json', dict(status='FAILED_NO_RETRY', error_type=type(error).__name__))


if __name__ == '__main__':
    main()
