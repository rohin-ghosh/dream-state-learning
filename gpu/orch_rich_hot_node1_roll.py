"""VM-side serialized rollout, with fresh conservative generation-floor checks."""

import argparse
import fcntl
import json
from pathlib import Path
import shlex
import subprocess
import time

from gpu.orch_rich_hot_node1_run import write


ORIGINAL = '/localhome/local-rohing/orch_rich_hot_node1_20260915_attempt1'
REVISED = '/localhome/local-rohing/orch_rich_hot_node1_20260915_v2'
QUERY = '''
from pathlib import Path
import json
rows=[]
for root_text, indices, marker in CONFIG:
 root=Path(root_text)
 for index in indices:
  launch=root/f"LAUNCH_{index}.json"
  if not launch.exists():continue
  entry=json.loads(launch.read_text());identity=entry.get("identity",entry);pid=identity["pid"]
  directory=Path('/proc')/str(pid)
  if not directory.exists():continue
  try:
   command=(directory/'cmdline').read_bytes()
   if b'rich_hot_' not in command or root_text.encode() not in command:continue
   if 'start_ticks' in identity and (directory/'stat').read_text().rsplit(')',1)[1].split()[19]!=identity['start_ticks']:continue
   ready=(root/f'shard{index}'/marker).exists()
   failed=(root/f'shard{index}'/'FAILED.json').exists() or (root/f'shard{index}'/'RESULT.json').exists()
   rows.append(dict(index=index,pid=pid,root=root_text,ready=ready,failed=failed))
  except (FileNotFoundError,ProcessLookupError):continue
print(json.dumps(rows))
'''


def remote(wrapper, command, timeout=60):
    result = subprocess.run(['bash', wrapper, command], capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError('remote_failed:' + wrapper + ':' + str(result.returncode))
    return result.stdout


def query(wrapper, config):
    code = 'CONFIG=' + repr(config) + '\n' + QUERY
    return json.loads(remote(wrapper, 'python3 -c ' + shlex.quote(code)))


def floor():
    node1 = query('gpu/a40r_ssh.sh', [(ORIGINAL, list(range(8)), 'ACTOR_READY.json'),
        (REVISED, list(range(8)), 'ACTOR_READY.json')])
    node2 = query('gpu/ovx_ssh.sh', [('/localhome/local-rohing/orch_rich_hot_node2_20260915_attempt1',
        list(range(8)), 'LOADED.json')])
    node3 = query('gpu/ovx2_ssh.sh', [('/localhome/local-rohing/orch_rich_hot_node3_20260915_route_v2',
        [3, 4, 5], 'ACTOR_READY.json'),
        ('/localhome/local-rohing/orch_rich_hot_node3_20260915_route_v2_batch02',
        [3, 4, 5], 'ACTOR_READY.json')])
    counts = {name: len({row['index'] for row in rows if row['ready'] and not row['failed']})
              for name, rows in [('node1', node1), ('node2', node2), ('node3', node3)]}
    total = sum(counts.values())
    return dict(observed_unix=time.time(), counted_nodes=counts, active_generators=total,
                minimum_during_one_gpu_roll=total - 1, rows=dict(node1=node1, node2=node2, node3=node3))


def send_floor(index, receipt):
    code = ('from pathlib import Path;import os;'
        + 'path=Path(' + repr(REVISED + f'/FLOOR_{index}.json') + ');'
        + 'temporary=path.with_suffix(".tmp");temporary.write_text(' + repr(json.dumps(receipt))
        + ');os.replace(temporary,path)')
    remote('gpu/a40r_ssh.sh', 'python3 -c ' + shlex.quote(code))


def status(index):
    code = ('from pathlib import Path;import json;root=Path(' + repr(REVISED) + ');'
        + f'path=root/"shard{index}";'
        + 'print(json.dumps(dict(ready=(path/"ACTOR_READY.json").exists(),failed=(path/"FAILED.json").exists(),'
        + 'progress=json.loads((path/"PROGRESS.json").read_text()) if (path/"PROGRESS.json").exists() else None)))')
    return json.loads(remote('gpu/a40r_ssh.sh', 'python3 -c ' + shlex.quote(code)))


def roll(output, start_index=0):
    output.mkdir(exist_ok=False)
    with (output / 'CONTROLLER.lock').open('x') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        completed = []
        try:
            for index in range(start_index):
                observed = status(index)
                if observed['failed'] or not observed['ready'] or not observed['progress']:
                    raise RuntimeError('cannot_resume_without_prior_v2_native:' + str(index))
                completed.append(index)
            for index in range(start_index, 8):
                receipt = floor()
                write(output / f'FLOOR_BEFORE_{index}.json', receipt)
                if receipt['active_generators'] < 17:
                    raise RuntimeError('generation_floor_requires_backfill_before_next_roll')
                send_floor(index, receipt)
                command = (f'env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 PYTHONPATH={REVISED}/source '
                    f'/localhome/local-rohing/v2/venv/bin/python -B -m gpu.orch_rich_hot_node1_boundary '
                    f'--root {ORIGINAL} --destination {REVISED} --index {index} --floor-receipt {REVISED}/FLOOR_{index}.json')
                boundary = subprocess.Popen(['bash', 'gpu/a40r_ssh.sh', command], stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE, text=True)
                while boundary.poll() is None:
                    time.sleep(5)
                    receipt = floor()
                    send_floor(index, receipt)
                stdout, stderr = boundary.communicate()
                if boundary.returncode:
                    write(output / f'BOUNDARY_FAILED_{index}.json', dict(returncode=boundary.returncode,
                        needs_floor_refresh='refresh_floor' in stderr, stdout=stdout))
                    raise RuntimeError('boundary_failed_no_next_gpu_stop:' + str(index))
                write(output / f'BOUNDARY_{index}.json', json.loads(stdout))
                command = (f'env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 PYTHONPATH={REVISED}/source '
                    f'HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false nohup '
                    f'/localhome/local-rohing/v2/venv/bin/python -B -m gpu.orch_rich_hot_node1_v2_run supervise '
                    f'--root {REVISED} --index {index} > {REVISED}/guard_{index}.log 2>&1 < /dev/null & echo SUBMITTED')
                remote('gpu/a40r_ssh.sh', command)
                limit = time.monotonic() + 240
                while time.monotonic() < limit:
                    observed = status(index)
                    write(output / f'STATUS_{index}.json', observed)
                    if observed['failed']:
                        raise RuntimeError('v2_worker_failed_keep_other_v1_workers:' + str(index))
                    if observed['ready'] and observed['progress'] and observed['progress']['calls'] >= 1:
                        break
                    time.sleep(5)
                else:
                    raise RuntimeError('v2_first_call_not_confirmed_no_further_stops')
                completed.append(index)
                write(output / 'PROGRESS.json', dict(completed_indices=completed, last=observed,
                    updated_unix=time.time(), simultaneous_rolls=1))
                print(json.dumps(dict(v2_index=index, first_native_confirmed=True, completed_indices=completed)), flush=True)
            write(output / 'RESULT.json', dict(status='COMPLETE_EIGHT_V2', completed_indices=completed,
                finished_unix=time.time(), final_floor=floor()))
        except BaseException as error:
            write(output / 'FAILED.json', dict(error_type=type(error).__name__, error=str(error),
                completed_indices=completed, finished_unix=time.time()))
            raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--start-index', type=int, choices=range(8), default=0)
    arguments = parser.parse_args()
    roll(arguments.output, arguments.start_index)
