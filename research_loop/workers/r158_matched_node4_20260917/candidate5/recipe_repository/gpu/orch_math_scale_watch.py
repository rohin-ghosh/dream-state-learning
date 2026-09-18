"""Finite native snapshot and memory-gated author-review scheduling."""

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import tarfile
import time

from gpu.orch_math_rich_screen import write
from gpu.orch_math_scale_reduce import load_raw, reduce, read
from gpu.orch_math_scale_review import available_memory, memory_limit, make_packets, run_batch


REMOTE = '/localhome/local-rohing/orch_math_scale_20260914_attempt1'
ARCHIVE_COMMAND = (f'find {REMOTE} -maxdepth 1 '
    '\\( -name "shard*" -o -name TASKS.json -o -name PREGPU_PUBLICATION.txt '
    '-o -name collection_deadline.txt \\) -printf "%f\\0" | '
    f'tar -C {REMOTE} --null -T - -czf -')


def snapshot(directory, sequence):
    archive = directory / f'capture_{sequence:03d}.tar.gz'
    with archive.open('wb') as output:
        result = subprocess.run(['bash', 'gpu/ovx_ssh.sh', ARCHIVE_COMMAND],
            stdout=output, stderr=subprocess.PIPE, timeout=90)
    if result.returncode:
        raise RuntimeError(result.stderr.decode())
    destination = directory / f'capture_{sequence:03d}'
    destination.mkdir()
    with tarfile.open(archive) as stream:
        stream.extractall(destination, filter='data')
    load_raw(destination)
    return destination


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seconds', type=int, default=14400)
    options = parser.parse_args()
    assert 0 < options.seconds <= 14400
    workspace = Path.cwd()
    local = workspace / 'gpu_artifacts_local/orch_math_scale_20260914_attempt1/watch'
    local.mkdir(parents=True, exist_ok=False)
    reviews = workspace / 'research_notes/analysis/orch_math_scale_20260914_attempt1/fulltext_review'
    reviews.mkdir(parents=True, exist_ok=True)
    started = time.time()
    deadline = started + options.seconds
    write(local / 'REQUEST.json', dict(started_unix=started, deadline_unix=deadline,
        max_reviewers=2, mem_wait_gib=1.5, mem_single_gib=3, native_changes=False,
        max_snapshots=80, snapshot_interval_seconds=120, max_batches=128))
    latest, sequence, last_capture, terminal = None, 0, 0, False
    with ThreadPoolExecutor(max_workers=2) as pool:
        running = {}
        while time.time() < deadline:
            now = time.time()
            if not terminal and now-last_capture >= 120 and sequence < 80:
                sequence += 1
                last_capture = now
                try:
                    latest = snapshot(local, sequence)
                    document, rows, binding = load_raw(latest)
                    terminal = all((latest / f'shard{shard}_outer_exit.txt').exists() for shard in range(4))
                    make_packets(latest, reviews)
                    write(local / 'COLLECTION_PROGRESS.json', dict(observed_unix=time.time(),
                        snapshot=str(latest), calls=len(rows), complete=binding['complete'],
                        terminal=terminal, statuses=binding['statuses']))
                    if terminal:
                        write(local / 'COLLECTION_TERMINAL.json', dict(observed_unix=time.time(),
                            snapshot=str(latest), complete=binding['complete'], calls=len(rows),
                            release_receipts_required=True, fits=0))
                except BaseException as error:
                    write(local / f'CAPTURE_FAILURE_{sequence:03d}.json', dict(error=str(error), observed_unix=time.time()))
            for future in list(running):
                if future.done():
                    print(future.result(), flush=True)
                    del running[future]
            available = available_memory()
            allowed = memory_limit(available)
            pending = [batch for batch in sorted(reviews.glob('batch_*'))
                       if not (batch / 'reader').exists() and not (batch / 'FAILED_REVIEW.json').exists()
                       and batch not in running.values()]
            if latest and pending and len(running) < allowed and now+610 < deadline:
                batch = pending[0]
                write(batch / 'MEMORY_RECEIPT.json', dict(available_bytes=available,
                    allowed_concurrency=allowed, already_running=len(running), observed_unix=now))
                running[pool.submit(run_batch, batch, workspace, latest)] = batch
            write(local / 'REVIEW_PROGRESS.json', dict(observed_unix=now, available_bytes=available,
                allowed_concurrency=allowed, running=[str(batch) for batch in running.values()],
                pending=len(pending), reviewed_batches=len(list(reviews.glob('batch_*/ACCEPTED_REVIEW.json'))),
                failed_batches=len(list(reviews.glob('batch_*/FAILED_REVIEW.json'))),
                independent_blind_audit=False))
            if terminal and not pending and not running:
                break
            time.sleep(10)
    write(local / 'FINISHED.json', dict(started=started, finished=time.time(),
        terminal=terminal, snapshot=str(latest), no_automatic_fit=True,
        finish_utc=datetime.now(timezone.utc).isoformat()))


if __name__ == '__main__':
    main()
