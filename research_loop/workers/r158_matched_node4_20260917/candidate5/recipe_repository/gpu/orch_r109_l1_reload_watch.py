"""Read-only native reload timing; never launches, stops, or releases GPU jobs."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


ORIGIN = Path('/localhome/local-rohing/orch_r109_l1_20260915')
ROOT = ORIGIN/'reload_watch_v1'
END = 1789491360
CUTOFF = END-300
STARTUP_WARNING_SECONDS = 75


def read(path):
    return json.loads(path.read_text())


def alive(expected):
    try:
        directory = Path('/proc')/str(expected['pid'])
        fields = (directory/'stat').read_text().rsplit(')',1)[1].split()
        return (fields[0] != 'Z' and fields[19] == expected['start_ticks']
            and directory.stat().st_uid == expected['uid']
            and Path('/proc/sys/kernel/random/boot_id').read_text().strip() == expected['boot_id'])
    except FileNotFoundError:
        return False


def update_window(previous, now, resident):
    state = dict(previous or {})
    closed = None
    if not resident:
        state.setdefault('first_empty_unix',now)
        state['last_empty_unix'] = now
    else:
        if 'first_empty_unix' in state:
            before = state.get('previous_nonempty_unix')
            closed = dict(first_empty_unix=state['first_empty_unix'],last_empty_unix=state['last_empty_unix'],
                previous_nonempty_unix=before,next_nonempty_unix=now,
                lower_bound_seconds=state['last_empty_unix']-state['first_empty_unix'],
                upper_bound_seconds=now-before if before is not None else None)
        state = dict(previous_nonempty_unix=now)
    return state,closed


def startup_estimate(launched, now, progressed):
    deadline = min(launched+STARTUP_WARNING_SECONDS,CUTOFF)
    return dict(first_progress_eta_upper_unix=deadline,eta_is_estimate_not_guarantee=True,
        startup_warning=not progressed and now>deadline,
        never_a_scientific_gate=True,never_a_release_signal=True)


def first_progress(arm,phase,segment,index):
    directory = ORIGIN/'fit'/arm/f'segment{segment:03d}'
    if phase == 'train':
        rank = index if arm == 'FULL' else 0
        path = directory/f'RANK{rank}_LOSSES.jsonl'
        if path.exists():
            with path.open() as stream:
                line = stream.readline()
            if line.endswith('\n'):
                return json.loads(line)['finished_unix']
    else:
        name = 'BEHAVIOR_000.json' if index == 2 else f'CAPABILITY_{16 if index == 1 else 0:03d}.json'
        path = directory/'readout/ON'/name
        if path.exists():return path.stat().st_mtime
    return None


def sample():
    now = time.time()
    heartbeat = read(ORIGIN/'async_v3/HEARTBEAT.json')
    guardian = read(ORIGIN/'async_v3/CPU_LAUNCH.json')['identity']
    gpu = {}
    output = subprocess.check_output(['nvidia-smi','-i','0,1,2,3',
        '--query-gpu=index,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True)
    for line in output.splitlines():
        index,memory,utilization = [int(value.strip()) for value in line.split(',')]
        gpu[index] = dict(index=index,memory_mib=memory,utilization_percent=utilization)
    result = dict(observed_unix=now,hard_deadline_unix=END,guardian_identity=guardian,
        guardian_alive=alive(guardian),raw_output=False,read_only=True,slots=[])
    for arm,state in heartbeat['arms'].items():
        for job in state['processes']:
            index = job['index']
            phase,segment = state['phase'],state['segment']
            launch = read(ORIGIN/f'async_{phase}_{segment}_{arm}_{index}_LAUNCH.json')
            progress = first_progress(arm,phase,segment,index)
            running = alive(job['identity'])
            result['slots'].append(dict(gpu[index],arm=arm,phase=phase,segment=segment,
                identity=job['identity'],process_alive=running,resume=state['resume'],
                launched_unix=launch['started_unix'],first_progress_unix=progress,
                launch_to_first_progress_seconds=progress-launch['started_unix'] if progress else None,
                allocation_status='RESERVED_RELOAD_OR_ACTIVE' if running or not state['terminal'] else 'TERMINAL_OWNER_REVIEW_REQUIRED',
                **startup_estimate(launch['started_unix'],now,progress is not None)))
    return result


def watch():
    import fcntl
    ROOT.mkdir(exist_ok=True)
    lock = (ROOT/'LOCK').open('a')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    source = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    windows = {}
    closed_windows = []
    with (ROOT/'FRAMES.jsonl').open('x') as frames:
        while time.time()<END:
            assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest() == source
            try:
                report = sample()
                for slot in report['slots']:
                    index = slot['index']
                    windows[index],closed = update_window(windows.get(index),report['observed_unix'],slot['memory_mib']>0)
                    if closed:closed_windows.append(dict(index=index,**closed))
                report.update(source_sha256=source,sampling_seconds=2,closed_empty_windows=closed_windows,
                    open_empty_windows={index:state for index,state in windows.items() if 'first_empty_unix' in state})
                frames.write(json.dumps(report)+'\n');frames.flush()
                temporary = ROOT/f'.STATUS.{os.getpid()}.json'
                temporary.write_text(json.dumps(report,indent=2))
                os.replace(temporary,ROOT/'STATUS.json')
            except Exception as failure:
                frames.write(json.dumps(dict(observed_unix=time.time(),error_type=type(failure).__name__))+'\n')
                frames.flush()
            time.sleep(min(2,max(0,END-time.time())))


if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['sample','watch'])
    if parser.parse_args().action=='watch':watch()
    else:print(json.dumps(sample()))
