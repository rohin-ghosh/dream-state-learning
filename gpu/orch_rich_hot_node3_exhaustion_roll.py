"""Serialized episode-boundary rollout with metadata-only local receipts."""

import argparse
import json
from pathlib import Path
import shlex
import time

from gpu.orch_rich_hot_node1_exhaustion_roll import remote
from gpu.orch_rich_hot_node1_run import write


ROOT = '/localhome/local-rohing/orch_rich_hot_node3_20260915_exhaustion_v1'
WRAPPER = 'gpu/ovx2_ssh.sh'
PYTHON = '/localhome/local-rohing/v2/venv/bin/python'
PREFIX = f'env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 PYTHONPATH={ROOT}/source'


def status(index):
    code = ('from pathlib import Path;import json;'
            + f'root=Path({ROOT!r});shard=root/"shard{index}";'
            + 'print(json.dumps(dict(ready=(shard/"ACTOR_READY.json").exists(),'
            + 'failed=(shard/"FAILED.json").exists(),'
            + 'progress=json.loads((shard/"PROGRESS.json").read_text()) '
            + 'if (shard/"PROGRESS.json").exists() else None)))')
    return json.loads(remote(WRAPPER, 'python3 -c ' + shlex.quote(code)))


def roll(output):
    output.mkdir(exist_ok=False)
    completed = []
    try:
        for index in (3, 4, 5):
            command = (f'{PREFIX} {PYTHON} -B -m gpu.orch_rich_hot_node3_exhaustion_boundary '
                       f'--destination {ROOT} --index {index}')
            receipt = json.loads(remote(WRAPPER, command, timeout=3600))
            write(output / f'BOUNDARY_{index}.json', receipt)
            command = (f'{PREFIX} HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 '
                       f'nohup {PYTHON} -B -m gpu.orch_rich_hot_node3_exhaustion_run watch '
                       f'--root {ROOT} --index {index} > {ROOT}/guard_{index}.log 2>&1 < /dev/null '
                       '& echo SUBMITTED')
            remote(WRAPPER, command)
            deadline = time.monotonic() + 1800
            while time.monotonic() < deadline:
                observed = status(index)
                write(output / f'STATUS_{index}.json', observed)
                if observed['failed']:
                    raise RuntimeError('worker_failed_stop_further_rolls:' + str(index))
                if observed['ready'] and observed['progress'] and observed['progress']['calls'] >= 1:
                    break
                time.sleep(5)
            else:
                raise TimeoutError('no_native_output_stop_further_rolls:' + str(index))
            completed.append(index)
            write(output / 'PROGRESS.json', dict(completed_indices=completed, updated_unix=time.time()))
            print(json.dumps(dict(index=index, first_native_confirmed=True)), flush=True)
        write(output / 'RESULT.json', dict(status='COMPLETE_THREE_EXHAUSTION',
                                          completed_indices=completed, finished_unix=time.time()))
    except BaseException as error:
        write(output / 'FAILED.json', dict(error_type=type(error).__name__, error=str(error),
                                          completed_indices=completed, finished_unix=time.time()))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    roll(arguments.output)
