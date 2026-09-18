"""Prospective renewal of the existing authentic ACT/Tool relay, without native controls."""

import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from lease_horizon import cpu_horizon


OWN = Path(__file__).resolve().parent
REPO = OWN.parents[2]
FLEET = REPO / 'research_loop/workers/rohin174_parenting_20260917/node4/R195_FLEET'
sys.path.insert(0, str(FLEET))
import r229_coordinator as previous
from r229_bridge import digest, write_once


def call(node, script, request):
    wrapper = 'a40r_ssh.sh' if node == 'P7' else 'ovx_ssh.sh'
    endpoint = ('/localhome/local-rohing/orch_r233_p7_recovery_20260918/renewed/p7_endpoint.py'
        if node == 'P7' else '/localhome/local-rohing/orch_r229_Astra7_20260918/node4_bridge/r233_recovery/operator/astra7_receiver.py')
    result = subprocess.run(['bash', str(REPO / 'gpu' / wrapper), f'{previous.PYTHON} -B {endpoint}'],
        input=json.dumps(request), text=True, capture_output=True, timeout=120)
    if result.returncode:
        raise RuntimeError(result.stderr[-1800:])
    return json.loads(result.stdout)


def act_only(batch):
    admitted = []
    for projection in batch['exports']:
        if projection['origin']['stage'] == 'ACT':
            admitted.append(projection)
        else:
            batch['decisions'].append(dict(origin=projection['origin'],
                decision='UNCHANGED_ACT_ONLY_RECEIVER_NO_RELABEL_OR_RETRY'))
    return dict(batch, exports=admitted)


def main():
    output = OWN / 'private/bridge'
    output.mkdir(exist_ok=True)
    old_output = FLEET / 'r229_bridge_run'
    with (old_output / 'COORDINATOR.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        previous.call = call
        binding_path = output / 'BINDING.json'
        if not binding_path.exists():
            child = call('ASTRA7', '', dict(op='status'))
            frontier = json.loads((OWN / 'private/P7_RENEWED_EXPORT_PROBE.json').read_bytes())
            binding = dict(astra7=child, p7_frontier_index=frontier['cursor'],
                p7_frontier_source_sha256=digest(frontier), bound_unix=time.time(),
                old_binding_sha256=digest(json.loads((old_output / 'BINDING.json').read_bytes())),
                old_cursor_preserved=json.loads((old_output / 'CURSOR.json').read_bytes()),
                historical_backlog_replay=False, forward_stages=['ACT'],
                cpu_hard_end_unix=cpu_horizon(), native_deadline_changed=False)
            write_once(binding_path, binding)
        binding = json.loads(binding_path.read_bytes())
        wall = min(cpu_horizon(), binding['astra7']['hard_end_unix'])
        write_once(output / f'STARTED_{time.time_ns()}.json', dict(pid=os.getpid(), started_unix=time.time(),
            hard_end_unix=wall, native_deadline_changed=False, native_signals=[]))
        cursor_path = output / 'CURSOR.json'
        cursors = (json.loads(cursor_path.read_bytes()) if cursor_path.exists() else dict(
            P7_TO_ASTRA7=binding['p7_frontier_index'], ASTRA7_TO_P7=binding['astra7']['loaded_record']['index']))
        while time.time() < wall:
            try:
                for direction in ('P7_TO_ASTRA7', 'ASTRA7_TO_P7'):
                    if direction == 'P7_TO_ASTRA7':
                        batch = call('P7', '', dict(op='export', cursor=cursors[direction],
                            cutoff_index=binding['p7_frontier_index']))
                        batch = act_only(batch)
                    else:
                        if not any((output / 'P7_TO_ASTRA7/published').glob('*.json')):
                            continue
                        batch = call('ASTRA7', '', dict(op='export', cursor=cursors[direction],
                            cutoff_index=binding.get('astra7_export_cutoff_index', binding['astra7']['loaded_record']['index']),
                            loaded_sha256=binding['astra7']['loaded_record']['sha256']))
                    write_once(output / direction / 'polls' / f'{time.time_ns()}.json', batch)
                    previous.drain(output, direction, batch, binding)
                    cursors[direction] = batch['cursor']
                    previous.save_cursor(cursor_path, cursors)
            except Exception as error:
                write_once(output / f'ERROR_{time.time_ns()}.json', dict(error=str(error)[:1800],
                    observed_unix=time.time(), native_signals=[]))
            time.sleep(5)


if __name__ == '__main__':
    main()
