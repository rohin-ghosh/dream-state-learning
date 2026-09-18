"""Pause only the exact quiescent original C2 COMPLETE boundary."""

import importlib.util
import os
from pathlib import Path
import signal
import time


ROOT = Path('/localhome/local-rohing/orch_r209_C2_20260918_resume1')
LIFE = Path('/localhome/local-rohing/orch_r153_community_C2_20260916_attempt1/life')
OUTPUT = ROOT / 'control/R210_HOMEWORK_BOUNDARY'
specification = importlib.util.spec_from_file_location('existing',
    '/localhome/local-rohing/orch_r204_C2_20260918_resume1/r204_followup_original.py')
existing = importlib.util.module_from_spec(specification)
specification.loader.exec_module(existing)
saved = existing.saved


def main():
    OUTPUT.mkdir(exist_ok=False)
    actor = saved.identity(3304081)
    saved.require(actor['start_ticks'] == '24203056' and actor['parent'] == 3304080
        and actor['cwd'] == str(ROOT / 'source') and actor['argv'][-3:] ==
        ['native', '--config', str(ROOT / 'control/GUARD.json')], 'exact_original_R209_actor')
    paths = existing.records()
    complete = next(path for path in reversed(paths)
        if existing.metadata(path)['kind'] == 'SLEEP_COMPLETE')
    record = saved.read(complete)
    tail = [existing.metadata(path) for path in paths[record['index'] + 1:]]
    saved.require(all(item['kind'] == 'R184_LEARN_COMPLETE' for item in tail),
        'no_generation_started_after_complete')
    descriptor = os.pidfd_open(actor['pid'])
    saved.pause_exact(actor, descriptor)
    latest = existing.records()
    tail = [existing.metadata(path) for path in latest[record['index'] + 1:]]
    if any(item['kind'] != 'R184_LEARN_COMPLETE' for item in tail):
        signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        raise RuntimeError('advanced_boundary_resumed_without_inflight_kill')
    document = record['document']
    saved.require(document['status'] == 'COMPLETE'
        and document['resume_state']['state']['pending'] is None,
        'complete_saved_state')
    receipt = dict(observed_unix=time.time(), actor=actor, cycle=document['cycle'],
        complete_index=record['index'], complete_sha256=record['sha256'],
        exact_head=saved.reference(latest[-1]), tail=tail,
        optimizer_steps=document['checkpoint']['optimizer_steps'],
        checkpoint_root=str(Path(document['checkpoint']['optimizer_rng_path']).parent),
        authority='R210 genuine homework before next human reply; same-life safe boundary',
        pending_source='e540198699ee4ddb9fbfd8b34b72ced3',
        human_inbox_writes=0, no_inflight_kill=True, parent_untouched=True)
    saved.write(OUTPUT / 'PAUSED.json', receipt)
    print(__import__('json').dumps(receipt))
    os.close(descriptor)


if __name__ == '__main__':
    main()
