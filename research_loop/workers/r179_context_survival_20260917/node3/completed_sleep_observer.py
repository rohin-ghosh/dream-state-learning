"""Bounded read-only observation; never dispatch, signal, restart or call models."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
HARD_END = 1789689000


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, document):
    with Path(path).open('x') as stream:
        json.dump(document, stream, sort_keys=True, indent=2)


def first_completed(observation):
    for row in observation['rows']:
        for receipt in row.get('history_progress', {}).get('completed_sleeps', []):
            if receipt.get('retained_history_through_completed_sleep') is True:
                return dict(physical=row['physical'], completed_sleep=receipt,
                    actor_state=row.get('actor_state'), native_pid=row.get('native_pid'),
                    observed_unix=observation['observed_unix'], no_scientific_claim=True)
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=Path, required=True)
    args = parser.parse_args()
    config = json.loads(args.config.read_bytes())
    output = args.config.parent
    if output.parent != HERE or config['hard_end_unix'] != HARD_END or config['poll_seconds'] != 120:
        raise ValueError('one_local_bounded_readonly_observer')
    expected = config['files']
    for name, checksum in expected.items():
        if Path(name).name != name or sha(HERE / name) != checksum:
            raise ValueError('pinned_observer_files')
    if config['wrapper_sha256'] != sha(REPO / 'gpu/ovx2_ssh.sh'):
        raise ValueError('exact_node3_readonly_wrapper')
    script = (HERE / 'observe_recovery.py').read_bytes()
    write(output / 'STARTED.json', dict(pid=__import__('os').getpid(), started_unix=time.time(),
        hard_end_unix=HARD_END, config_sha256=sha(args.config), files=expected, signals=0, model_calls=0,
        stop_on_first_verified_retained_completed_sleep=True, no_workload_actions=True))
    while time.time() < HARD_END:
        try:
            result = subprocess.run(['bash', str(REPO / 'gpu/ovx2_ssh.sh'),
                'env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 /localhome/local-rohing/v2/venv/bin/python -I -B -'],
                input=script, capture_output=True, check=True, timeout=min(45, max(1, HARD_END - time.time())), cwd=REPO)
            observation = json.loads(result.stdout)
            path = output / ('OBSERVATION_' + str(time.time_ns()) + '.json')
            with path.open('xb') as stream:
                stream.write(result.stdout)
            complete = first_completed(observation)
            if complete is not None:
                write(output / 'FIRST_COMPLETED_CONTEXT_SLEEP.json', dict(complete,
                    observation_path=str(path), observation_sha256=sha(path), config_sha256=sha(args.config)))
                return
        except BaseException as error:
            write(output / 'OBSERVER_FAILED.json', dict(error_type=type(error).__name__, observed_unix=time.time(),
                no_learner_action=True, no_completion_claim=True))
            raise
        time.sleep(min(config['poll_seconds'], max(0, HARD_END - time.time())))
    write(output / 'EXPIRED.json', dict(observed_unix=time.time(), no_new_completion_claim=True, signals=0))


if __name__ == '__main__':
    main()
