"""Transfer six immutable NODE3 packets to persistent local storage."""

from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess
import time

import takeover as base


BATCH = 'relocation_20260917t2341z'
REMOTE = '/localhome/local-rohing/research_loop/workers/rohin174_parenting_20260917/node3'
OUTPUT = base.HERE / 'r188' / BATCH
FINAL = False


def transfer(physical):
    destination = OUTPUT / ('physical' + str(physical) + '.tar.gz.part')
    log_path = OUTPUT / ('physical' + str(physical) + '.transfer.log')
    command = ('/localhome/local-rohing/v2/venv/bin/python -B ' + REMOTE +
        '/r188_preserve_packet_v3.py --physical ' + str(physical) + ' --batch ' + BATCH +
        (' --final' if FINAL else '') +
        ' >&2 && tar -C ' + REMOTE + '/r188/' + BATCH +
        ' -I "gzip -1" -cf - physical' + str(physical))
    started = time.time()
    try:
        with destination.open('xb') as output, log_path.open('x') as log:
            result = subprocess.run(['bash', str(base.REPO / 'gpu/ovx2_ssh.sh'), command],
                stdout=output, stderr=log, timeout=540)
        base.require(result.returncode == 0, 'actual_packet_capture_and_transfer_failed')
        subprocess.run(['gzip', '-t', str(destination)], check=True, timeout=120)
        listing = subprocess.run(['tar', '-tzf', str(destination)], text=True,
            capture_output=True, check=True, timeout=120).stdout.splitlines()
        prefix = 'physical' + str(physical) + '/'
        base.require(all(name.startswith(prefix) and '..' not in Path(name).parts
            for name in listing), 'safe_owned_archive_paths')
        packet = json.loads(subprocess.run(['tar', '-xOzf', str(destination), prefix + 'PACKET.json'],
            text=True, capture_output=True, check=True, timeout=120).stdout)
        final = destination.with_suffix('')
        destination.rename(final)
        digest = hashlib.file_digest(final.open('rb'), 'sha256').hexdigest()
        base.write(OUTPUT / ('physical' + str(physical) + '.VERIFIED.json'),
            dict(status='PERSISTENT_LOCAL_PACKET_VERIFIED', physical=physical,
                started_unix=started, verified_unix=time.time(), archive=str(final),
                archive_bytes=final.stat().st_size, archive_sha256=digest,
                gzip_crc_verified=True, archive_paths_verified=True, packet=packet,
                original_learner_not_signaled=True))
        print(json.dumps(dict(physical=physical, status='PERSISTENT_LOCAL_PACKET_VERIFIED',
            cycle=packet['captured_cycle'], bytes=final.stat().st_size)), flush=True)
    except BaseException as error:
        base.write(OUTPUT / ('physical' + str(physical) + '.FAILED.json'),
            dict(error_type=type(error).__name__, reason=str(error)[:500], observed_unix=time.time(),
                partial_archive=str(destination), capture_log=str(log_path)))
        raise


if __name__ == '__main__':
    OUTPUT.mkdir(parents=True, exist_ok=False)
    base.write(OUTPUT / 'STARTED.json', dict(started_unix=time.time(),
        physicals=[0, 1, 2, 3, 4, 7], local_filesystem='persistent /data',
        no_child_signals=True, source_ceiling_unix=base.HARD_END))
    with ThreadPoolExecutor(max_workers=6) as executor:
        list(executor.map(transfer, (0, 1, 2, 3, 4, 7)))
