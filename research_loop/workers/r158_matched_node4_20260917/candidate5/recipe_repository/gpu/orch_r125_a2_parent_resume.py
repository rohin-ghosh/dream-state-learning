"""Resume the unchanged Astra transport against the verified C52 successor."""

import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shlex
import tempfile
import time
from types import FunctionType


STAGE = Path('/data/home/rohing/courier/runtime/r137_a2_request_repair_v3')
OUTPUT = Path('/data/home/rohing/courier/runtime/r125_a2_parent_resume_v1')
MANIFEST = 'bb3ab4b49faf867c6c936922a6b5e0bcdd009bd5a697d70309db1ddd619cf713'


def remote_source(original):
    marker = '    print(json.dumps(dict(observed_unix=time.time(),plan_sha256=sha(root/\'PLAN.json\'),'
    guard = '''    service=root/'runtime_recovery7'
    loaded=json.loads((service/'LOADED.json').read_text())
    identity=json.loads((service/'LAUNCH.json').read_text())['identity']
    process=Path('/proc')/str(identity['pid'])
    live=False
    try:
        fields=(process/'stat').read_text().rsplit(')',1)[1].split()
        live=(fields[19]==identity['start_ticks'] and fields[0] not in ('Z','X')
              and sha(process/'cmdline')==identity['command_sha256']
              and loaded['actual_process'][1]==identity['pid']
              and not (service/'TERMINAL.json').exists()
              and not (service/'GUARD_TERMINAL.json').exists())
    except (FileNotFoundError,ProcessLookupError):
        pass
'''
    old = "terminal=(root/'TERMINAL.json').exists() or (root/'runtime_recovery5/GUARD_TERMINAL.json').exists()"
    if original.count(marker) != 1 or original.count(old) != 1:
        raise ValueError('exact_snapshot_seams')
    return original.replace(marker, guard+marker).replace(old,
        "terminal=not live, resumed_unix=loaded['loaded_unix'], resumed_pid=identity['pid']")


def epoch(document):
    return dict(observed_unix=document['resumed_unix'], parent_high_water=128,
        historical_ids=[row['id'] for row in document['requests']
                        if (row.get('reservation') or {}).get('first', 0) <= 128],
        host_sha256=document['host_sha256'], resumed_pid=document['resumed_pid'])


def main():
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
    assert OUTPUT.is_dir() and not (OUTPUT/'STARTED.json').exists()
    path = STAGE/'orch_r137_math_request_repair.py'
    spec = importlib.util.spec_from_file_location('preserved_r137_parent', path)
    wrapper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(wrapper)
    active, config = wrapper.verify(STAGE, MANIFEST)
    launch = wrapper.authorize(active, config, MANIFEST, STAGE/'MAIN_GO.json')
    prior = wrapper.read(STAGE/'runtime/STARTED.json')['identity']
    assert wrapper.process_identity(prior['pid']) is None, 'old_parent_actor_absent'
    snapshot = FunctionType(wrapper.snapshot.__code__, dict(wrapper.snapshot.__globals__,
        REMOTE=remote_source(wrapper.REMOTE)))
    observed = snapshot(wrapper.OLD)
    assert not observed['terminal'] and not observed['runner_lock'] and not observed['unfinished_claims']
    boundary = epoch(observed)
    packets = OUTPUT/'packets'
    packets.mkdir()
    store = active.base.Store(wrapper.OLD)
    lock = shlex.quote(wrapper.QUEUE+'/parent_claude/RUNNER.lock')
    with (OUTPUT/'CONTROLLER.lock').open('a') as descriptor:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert store.shell('mkdir '+lock, check=False).returncode == 0, 'exclusive_parent_queue'
        try:
            process = FunctionType(active.base.process_request.__code__,
                dict(active.base.process_request.__globals__, evaluate=wrapper.data_evaluator(active, packets)))
            wrapper.write(OUTPUT/'STARTED.json', dict(pid=os.getpid(), boundary=boundary,
                manifest_sha256=MANIFEST, source_sha256=wrapper.sha(__file__),
                launch_sha256=wrapper.sha(STAGE/'MAIN_GO.json'), unchanged_parent_policy=True,
                historical_requests_replayed=False, started_unix=time.time()))
            while time.time() < config['deadline_unix']:
                current = snapshot(wrapper.OLD)
                assert current['host_sha256'] == boundary['host_sha256'] and current['resumed_pid'] == boundary['resumed_pid']
                if current['terminal']:
                    break
                for row in current['requests']:
                    if not wrapper.eligible(row, boundary):
                        continue
                    assert store.hash(Path(wrapper.QUEUE)/'parent_queue'/(row['id']+'.request.json')) == row['sha256']
                    temporary = Path(tempfile.mkdtemp(prefix='request_', dir=packets))
                    status = process(store, config, launch, row['id']+'.request.json', temporary,
                        Path('/data/home/rohing/courier/swarm/prompts'),
                        STAGE/'source/research_notes/PARENTING_PRINCIPLES_ROHIN_2026-09-15.md')
                    wrapper.write(OUTPUT/(row['id']+'.json'), dict(status=status, finished_unix=time.time(), retry=False))
                    temporary.rmdir()
                time.sleep(2)
        finally:
            store.shell('rmdir '+lock, check=False)


if __name__ == '__main__':
    main()
