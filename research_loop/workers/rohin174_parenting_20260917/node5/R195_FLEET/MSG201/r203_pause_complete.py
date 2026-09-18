"""R203: preserve source51, finish current sleep, pause exact C2 at COMPLETE."""

import fcntl
import importlib.util
import json
import os
from pathlib import Path
import shutil
import signal
import time


ROOT = Path('/localhome/local-rohing/orch_r202_C2_20260918_resume1')
LIFE = Path('/localhome/local-rohing/orch_r153_community_C2_20260916_attempt1/life')
OUTPUT = ROOT / 'control/R203_PAUSE'
specification = importlib.util.spec_from_file_location('saved', ROOT / 'saved_primitives.py')
saved = importlib.util.module_from_spec(specification)
specification.loader.exec_module(saved)


def metadata(path):
    with path.open('rb') as handle:
        handle.seek(max(0, path.stat().st_size - 4096))
        raw = handle.read()
    return json.loads(b'{' + raw[raw.rfind(b',"index":') + 1:])


def records():
    return sorted((LIFE / 'stream/records').glob('[0-9]' * 20 + '.json'))


def preserve_checkpoint(cycle):
    source = LIFE / 'checkpoints' / f'sleep_{cycle:06d}'
    destination = OUTPUT / f'checkpoint_{cycle:06d}'
    shutil.copytree(source, destination)
    checksums = saved.files(source)
    saved.require(saved.files(destination) == checksums, 'checkpoint_bytes_preserved')
    return dict(source=str(source), destination=str(destination), files=checksums,
        commit=saved.read(source / 'COMMIT.json'))


def main():
    descriptor = os.open(OUTPUT / 'WATCHER.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    actor = saved.identity(3114821)
    saved.require(actor['start_ticks'] == '23528031' and actor['parent'] == 3114820
        and actor['cwd'] == str(ROOT / 'source') and actor['argv'][-3:] ==
        ['native', '--config', str(ROOT / 'control/GUARD.json')], 'exact_R202_original_C2_actor')
    plan = saved.read(ROOT / 'control/PLAN.json')
    saved.require(plan['root'] == str(LIFE) and plan['physical'] == 1
        and plan['hard_end_unix'] == 1789776000, 'same_original_C2_wall_scope')
    actor_fd = os.pidfd_open(actor['pid'])
    source51 = preserve_checkpoint(51)
    saved.write(OUTPUT / 'SOURCE51_PRESERVED.json', dict(observed_unix=time.time(), **source51))
    saved.write(OUTPUT / 'ARMED.json', dict(observed_unix=time.time(), watcher_pid=os.getpid(),
        actor=actor, source51=saved.reference(OUTPUT / 'SOURCE51_PRESERVED.json'),
        target_cycle=52, authority='ROHIN203_EXPLICIT_COMPLETE_BOUNDARY_PAUSE',
        no_inflight_kill=True, no_automatic_resume=True, parent_autopublish_frozen=True))
    initial = records()
    next_index = 5893
    pause_attempt = 0
    try:
        while time.time() < plan['hard_end_unix'] - 30:
            path = LIFE / 'stream/records' / f'{next_index:020d}.json'
            if not path.exists():
                time.sleep(0.01)
                continue
            item = metadata(path)
            next_index += 1
            if item['kind'] != 'SLEEP_COMPLETE':
                continue
            saved.pause_exact(actor, actor_fd)
            paused_unix = time.time()
            complete = saved.read(path)
            document = complete['document']
            state = document['resume_state']['state']
            saved.require(complete['sha256'] == saved.digest({key: value for key, value in complete.items()
                if key != 'sha256'}) and document['resume_state']['sha256'] == saved.digest(state)
                and document['status'] == 'COMPLETE' and state['pending'] is None
                and state['sleep_frontier'] == len(state['rows'])
                and state['sleep_receipts'][-1]['status'] == 'COMPLETE', 'exact_complete_quiescent_state')
            current = records()
            tail = [metadata(entry) for entry in current[complete['index'] + 1:]]
            if any(entry['kind'] != 'R184_LEARN_COMPLETE' for entry in tail):
                saved.write(OUTPUT / f'ADVANCED_BEFORE_PAUSE_{pause_attempt:03d}.json', dict(
                    observed_unix=paused_unix, complete_index=complete['index'], cycle=document['cycle'],
                    actual_tail=tail, no_kill=True, decision='continue_to_next_safe_complete'))
                pause_attempt += 1
                signal.pidfd_send_signal(actor_fd, signal.SIGCONT)
                continue
            saved.write(OUTPUT / 'PAUSED.json', dict(observed_unix=paused_unix,
                actor=actor, cycle=document['cycle'], complete_index=complete['index'],
                complete_record_sha256=complete['sha256'], exact_head=saved.reference(current[-1]),
                no_new_training_request_after_complete=True, tail_metadata=tail,
                no_automatic_resume=True, no_inflight_kill=True))
            checkpoint = preserve_checkpoint(document['cycle'])
            saved.write(OUTPUT / 'COMPLETED_CHECKPOINT_PRESERVED.json', dict(
                observed_unix=time.time(), cycle=document['cycle'], **checkpoint))
            saved.require(saved.files(LIFE / 'checkpoints/sleep_000051') == source51['files'],
                'source51_never_overwritten_or_rolled_back')
            stream_copy = OUTPUT / 'preserved_stream'
            stream_copy.mkdir(mode=0o700)
            shutil.copy2(LIFE / 'stream/JOURNAL.json', stream_copy / 'JOURNAL.json')
            shutil.copytree(LIFE / 'stream/records', stream_copy / 'records')
            shutil.copytree(LIFE / 'stream/inbox', stream_copy / 'inbox')
            saved.verify_snapshot(stream_copy, LIFE, dict(reference=saved.reference(current[-1])))
            saved.require(records() == current and saved.sha(current[-1]) == saved.sha(
                stream_copy / 'records' / current[-1].name), 'paused_journal_head_unchanged')
            saved.write(OUTPUT / 'PRESERVED_COMPLETE.json', dict(observed_unix=time.time(),
                status='ORIGINAL_C2_PAUSED_AT_PRESERVED_COMPLETE', same_life_root=str(LIFE),
                actor=actor, cycle=document['cycle'], complete_index=complete['index'],
                complete_record_sha256=complete['sha256'], state_sha256=document['resume_state']['sha256'],
                history_events=len(state['history']['events']), working_state=state['history']['working_state'],
                checkpoint=saved.reference(OUTPUT / 'COMPLETED_CHECKPOINT_PRESERVED.json'),
                source51=saved.reference(OUTPUT / 'SOURCE51_PRESERVED.json'),
                saved_model_optimizer_RNG_bytes_verified=True,
                preceding_console_sampling_RNG_caveat_not_erased=True,
                stream_snapshot=str(stream_copy), inbox_files=saved.files(stream_copy / 'inbox'),
                source51_intact=True, completed_sleep_not_discarded=True,
                history_rolled_back=False, source_inbox_modified=False,
                paused_no_automatic_resume=True, awaiting_Main_compaction_console_repair=True))
            print(json.dumps(dict(status='PAUSED_AND_PRESERVED', cycle=document['cycle'],
                complete_index=complete['index'], paused_unix=paused_unix, output=str(OUTPUT))), flush=True)
            return
        raise TimeoutError('no_safe_complete_before_existing_wall')
    except BaseException as error:
        saved.write(OUTPUT / ('FAILURE_' + str(time.time_ns()) + '.json'), dict(
            observed_unix=time.time(), error_type=type(error).__name__, reason=str(error),
            actor_paused=(OUTPUT / 'PAUSED.json').exists(), no_automatic_resume=True))
        raise
    finally:
        os.close(actor_fd)
        os.close(descriptor)


if __name__ == '__main__':
    main()
