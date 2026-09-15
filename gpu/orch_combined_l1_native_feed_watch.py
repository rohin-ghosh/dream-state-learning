"""Bounded CPU-only publisher polling; raw packets travel only through pipes."""

import argparse
import fcntl
import json
from pathlib import Path
import shlex
import subprocess
import time


ROOT = '/localhome/local-rohing/orch_combined_l1_continual_20260915_attempt1'
EXPORT = '/localhome/local-rohing/orch_combined_l1_native_feed_auto_0545/export.py'
EXCLUSIONS = '/localhome/local-rohing/orch_combined_l1_native_feed_20260915/EXCLUSIONS.json'
PYTHON = '/localhome/local-rohing/v2/venv/bin/python'
VALIDATION = ROOT + '/feed_auto_validation_0545'


def pending(discovered, inventory, attempted):
    known = {entry['batch_id']: entry for entry in inventory['entries']}
    selected = []
    for entry in sorted(discovered, key=lambda item: item['number']):
        previous = known.get(entry['batch_id'])
        if previous and previous['manifest_sha256'] != entry['manifest_sha256']:
            raise ValueError('known_batch_manifest_rebound:' + entry['batch_id'])
        if previous and previous['area'] == 'CONTENT_QUEUE':
            continue
        if entry['manifest_sha256'] not in attempted:
            selected.append(entry)
    return selected[:4]


def main(repository, output, once=False, *, exporter=None, validation=None,
         receiver_module='gpu.orch_combined_l1_native_feed_node'):
    exporter = exporter or f'python3 -B {EXPORT}'
    validation = validation or VALIDATION
    output.mkdir(parents=True, exist_ok=True)
    with (output / 'WATCH.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        attempted = {path.stem for path in output.glob('ATTEMPTS/*.json')}
        while True:
            remote = f'CUDA_VISIBLE_DEVICES= PYTHONPATH={validation} {PYTHON} -B -m {receiver_module} --root {ROOT}'
            def ssh(wrapper, command, **kwargs):
                return subprocess.run(['bash', str(repository / 'gpu' / wrapper), command],
                    capture_output=True, text=True, check=True, timeout=120, **kwargs)
            inventory = json.loads(ssh('a100_ssh.sh', remote + ' --inventory').stdout)
            if inventory['native_unix'] >= inventory['training_deadline']:
                print(json.dumps(dict(status='TRAINING_DEADLINE', native_unix=inventory['native_unix'])), flush=True)
                return
            discovered = json.loads(ssh('ovx_ssh.sh', exporter + ' --discover').stdout)
            for entry in pending(discovered, inventory, attempted):
                expected = entry['manifest_sha256']
                command = f'{exporter} --number {entry["number"]} --manifest-sha {shlex.quote(expected)} --exclusions {EXCLUSIONS}'
                remaining = inventory['training_deadline'] - time.time()
                if remaining < 120:
                    return
                producer = subprocess.Popen(['bash', str(repository / 'gpu/ovx_ssh.sh'), command],
                    stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                consumer = subprocess.Popen(['bash', str(repository / 'gpu/a100_ssh.sh'),
                    remote + ' --manifest-sha ' + shlex.quote(expected)],
                    stdin=producer.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                producer.stdout.close()
                try:
                    stdout, stderr = consumer.communicate(timeout=min(120, remaining))
                    producer.wait(timeout=10)
                    producer_error = producer.stderr.read().decode()
                    result = dict(entry=entry, producer_returncode=producer.returncode,
                        consumer_returncode=consumer.returncode, receiver_stdout=stdout.decode(),
                        receiver_stderr=stderr.decode(), exporter_stderr=producer_error,
                        native_calls=0, finished_unix=time.time())
                except subprocess.TimeoutExpired:
                    consumer.kill()
                    producer.kill()
                    stdout, stderr = consumer.communicate()
                    producer.wait()
                    result = dict(entry=entry, status='TRANSFER_TIMEOUT_NO_AUTOMATIC_RETRY',
                        receiver_stdout=stdout.decode(), receiver_stderr=stderr.decode(),
                        native_calls=0, finished_unix=time.time())
                finally:
                    producer.stderr.close()
                folder = output / 'ATTEMPTS'
                folder.mkdir(exist_ok=True)
                with (folder / (expected + '.json')).open('x') as stream:
                    json.dump(result, stream, indent=2)
                attempted.add(expected)
                print(json.dumps(result), flush=True)
            print(json.dumps(dict(status='POLL_COMPLETE', found=len(discovered),
                attempted=len(attempted), time_unix=time.time(), native_calls=0)), flush=True)
            if once:
                return
            time.sleep(min(60, max(0, inventory['training_deadline'] - time.time())))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--repository', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args()
    main(args.repository, args.output, args.once)
