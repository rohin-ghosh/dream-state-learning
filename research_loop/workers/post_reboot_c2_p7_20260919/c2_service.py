"""Restartable foreground owner for C2's existing CPU parent, with ledger continuity."""

import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from c2_restore import OWN, PREVIOUS, REPO, read, sha, validate_manifest, write


def main():
    with (OWN / 'C2_SERVICE.lock').open('a') as service:
        fcntl.flock(service.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        while time.time() < 1789927200:
            with (PREVIOUS / 'private/C2_WAIT_CONTROLLER.lock').open('a') as controller:
                try:
                    fcntl.flock(controller.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    time.sleep(5)
                    continue
                prior_paths = sorted(OWN.glob('c2_session*/MANIFEST.json'), key=lambda path: path.stat().st_mtime_ns)
                prior_paths = [path for path in prior_paths if (Path(read(path)['output']) / 'STARTED.json').exists()]
                if not prior_paths:
                    raise ValueError('preserved_started_parent_ledger_required')
                prior_path = prior_paths[-1]
                previous = read(prior_path)
                previous_config = read(previous['config_path'])
                for filename, expected in previous['local_source_sha256'].items():
                    if sha(filename) != expected:
                        raise ValueError('preserved_parent_source_changed:' + filename)
                previous_output = Path(previous['output'])
                session = OWN / ('c2_session_' + str(time.time_ns()))
                session.mkdir()
                reserved = max([previous_config['start_after_response_count']] + [read(path)['response_count']
                    for path in previous_output.glob('parent_*/SOURCE.json')])
                config = dict(previous_config, predecessor_output=str(previous_output),
                    predecessor_started_sha256=sha(previous_output / 'STARTED.json'), start_after_response_count=reserved)
                config_path = session / 'CONFIG.json'
                write(config_path, config)
                pins = dict(previous['local_source_sha256'])
                pins.update({str(path): sha(path) for path in (config_path, Path(__file__))})
                manifest = dict(previous, config_path=str(config_path), predecessor_config_path=previous['config_path'],
                    output=str(session / 'parent'), local_source_sha256=pins,
                    status='CPU_PARENT_RESTART_PRESERVING_PRIOR_LEDGER')
                manifest_path = session / 'MANIFEST.json'
                write(manifest_path, manifest)
                validate_manifest(manifest)
            command = [sys.executable, '-B', str(PREVIOUS / 'checkpoint_tail_parent_strong.py'),
                '--manifest', str(manifest_path), '--manifest-sha256', sha(manifest_path)]
            with (session / 'CPU_PARENT.log').open('x') as log:
                child = subprocess.Popen(command, cwd=REPO, stdin=subprocess.DEVNULL,
                    stdout=log, stderr=subprocess.STDOUT)
                write(session / 'SPAWNED.json', dict(pid=child.pid, started_unix=time.time(), native_signals=[]))
                code = child.wait()
            write(session / 'EXIT.json', dict(code=code, finished_unix=time.time(), native_signals=[]))
            time.sleep(10)


if __name__ == '__main__':
    main()
