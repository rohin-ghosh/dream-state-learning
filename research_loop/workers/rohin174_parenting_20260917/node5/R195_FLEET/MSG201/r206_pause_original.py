"""Preserve original C2 at its next COMPLETE using existing saved primitives."""

import fcntl
import importlib.util
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import time


ROOT = Path('/localhome/local-rohing/orch_r205_C2_20260918_resume1')
LIFE = Path('/localhome/local-rohing/orch_r153_community_C2_20260916_attempt1/life')
OUTPUT = ROOT / 'control/R206_PAUSE_20260918T0407Z'
RECEIVER = Path('/localhome/local-rohing/orch_r206_C2_20260918_resume1')
specification = importlib.util.spec_from_file_location('existing',
    '/localhome/local-rohing/orch_r204_C2_20260918_resume1/r204_followup_original.py')
existing = importlib.util.module_from_spec(specification)
specification.loader.exec_module(existing)
saved = existing.saved


def main():
    OUTPUT.mkdir(exist_ok=False)
    lock = os.open(OUTPUT / 'WATCHER.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    saved.require(saved.read(RECEIVER / 'STAGED.json')['status'] == 'R206_STAGED_NOT_LOADED',
        'executable_tested_R206_receiver_before_arming')
    actor = saved.identity(3236422)
    saved.require(actor['start_ticks'] == '23963642' and actor['parent'] == 3236421
        and actor['cwd'] == str(ROOT / 'source') and actor['argv'][-3:] ==
        ['native', '--config', str(ROOT / 'control/GUARD.json')], 'exact_original_R205_actor')
    plan = saved.read(ROOT / 'control/PLAN.json')
    saved.require(plan['root'] == str(LIFE) and plan['physical'] == 1
        and plan['hard_end_unix'] == 1789776000, 'same_original_life_wall')
    actor_fd = os.pidfd_open(actor['pid'])
    saved.write(OUTPUT / 'ARMED.json', dict(observed_unix=time.time(), watcher_pid=os.getpid(),
        actor=actor, authority='Rohin206 frozen verbatim-source pin followup at next exact COMPLETE',
        parent_untouched=True, human_inbox_writes=0, clone_operations_frozen=True))
    next_index = max(0, len(existing.records()) - 2)
    try:
        while time.time() < plan['hard_end_unix'] - 30:
            path = LIFE / 'stream/records' / f'{next_index:020d}.json'
            if not path.exists():
                time.sleep(.01)
                continue
            next_index += 1
            if existing.metadata(path)['kind'] != 'SLEEP_COMPLETE':
                continue
            saved.pause_exact(actor, actor_fd)
            paused_unix = time.time()
            record = saved.read(path)
            current = existing.records()
            tail = [existing.metadata(item) for item in current[record['index'] + 1:]]
            if any(item['kind'] != 'R184_LEARN_COMPLETE' for item in tail):
                saved.write(OUTPUT / f'ADVANCED_{record["index"]}.json',
                    dict(observed_unix=paused_unix, tail=tail, decision='continue_to_next_complete'))
                signal.pidfd_send_signal(actor_fd, signal.SIGCONT)
                continue
            document = record['document']
            state = document['resume_state']['state']
            saved.require(document['status'] == 'COMPLETE' and state['pending'] is None
                and document['resume_state']['sha256'] == saved.digest(state)
                and state['sleep_frontier'] == len(state['rows']), 'complete_quiescent_saved_state')
            saved.write(OUTPUT / 'PAUSED.json', dict(observed_unix=paused_unix, actor=actor,
                cycle=document['cycle'], complete_index=record['index'], complete_sha256=record['sha256'],
                exact_head=saved.reference(current[-1]), tail=tail, no_inflight_kill=True,
                parent_untouched=True, human_inbox_writes=0))
            checkpoint = LIFE / 'checkpoints' / f'sleep_{document["cycle"]:06d}'
            shutil.copytree(checkpoint, OUTPUT / checkpoint.name)
            saved.require(saved.files(checkpoint) == saved.files(OUTPUT / checkpoint.name), 'exact_checkpoint_bytes')
            shutil.copytree(LIFE / 'stream', OUTPUT / 'preserved_stream')
            saved.verify_snapshot(OUTPUT / 'preserved_stream', LIFE, dict(reference=saved.reference(current[-1])))
            saved.require(saved.reference(existing.records()[-1]) == saved.reference(current[-1]), 'same_paused_head')
            saved.write(OUTPUT / 'PRESERVED_COMPLETE.json', dict(observed_unix=time.time(),
                paused_unix=paused_unix, cycle=document['cycle'], complete_index=record['index'],
                complete_sha256=record['sha256'], state_sha256=document['resume_state']['sha256'],
                optimizer_steps=document['checkpoint']['optimizer_steps'],
                checkpoint_files=saved.files(OUTPUT / checkpoint.name),
                checkpoint_root=str(OUTPUT / checkpoint.name), stream_root=str(OUTPUT / 'preserved_stream'),
                history_events=len(state['history']['events']), human_inbox_writes=0,
                preserved_inbox_files=saved.files(OUTPUT / 'preserved_stream/inbox'),
                same_life=True, no_history_or_weight_rollback=True, parent_untouched=True,
                prior_corrupt_exposure_not_erased=True,
                earlier_resident_post_console_sampling_RNG_not_separately_checkpointed=True,
                awaiting_Main_overlay=False, receiver=str(RECEIVER)))
            print(json.dumps(dict(status='ORIGINAL_C2_PAUSED_PRESERVED_FOR_R206', paused_unix=paused_unix,
                cycle=document['cycle'], complete_index=record['index'],
                optimizer_steps=document['checkpoint']['optimizer_steps'], output=str(OUTPUT))), flush=True)
            subprocess.run(['/localhome/local-rohing/v2/venv/bin/python', '-B',
                str(RECEIVER / 'r206_resume_original.py'), 'execute'], cwd=RECEIVER, check=True)
            return
        raise TimeoutError('no_complete_before_existing_wall')
    except BaseException as error:
        saved.write(OUTPUT / ('FAILURE_' + str(time.time_ns()) + '.json'), dict(observed_unix=time.time(),
            error_type=type(error).__name__, reason=str(error), actor_paused=(OUTPUT / 'PAUSED.json').exists()))
        raise
    finally:
        os.close(actor_fd)
        os.close(lock)


if __name__ == '__main__':
    main()
