"""Reviewed COPY only, original node routes, no source writes or GPU operations."""

import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
SOURCE = '/localhome/local-rohing/orch_r205_node3_20260918'
DESTINATION = '/localhome/local-rohing/node3_retired_archive_copy_20260919T133405Z_ws6'
DIRECTORIES = ('r225_siege_retirement_20260918', 'r233_retirement_20260918T1144Z',
    'r224_challenger_retirement_20260918')


def route(node, command):
    return ['bash', str(REPO / 'gpu' / f'{node}_ssh.sh'), command]


def remote(node, command):
    return subprocess.check_output(route(node, command), text=True)


def pipe(source_command, destination_command, label):
    with (HERE / f'ARCHIVE_{label}_SOURCE.stderr').open('xb') as source_error, (
            HERE / f'ARCHIVE_{label}_DESTINATION.stderr').open('xb') as destination_error:
        source = subprocess.Popen(route('ovx2', source_command), stdout=subprocess.PIPE, stderr=source_error)
        destination = subprocess.Popen(route('ovx4', destination_command), stdin=source.stdout,
            stdout=subprocess.PIPE, stderr=destination_error)
        source.stdout.close()
        result, unused = destination.communicate()
        source_status = source.wait()
        if source_status != 0 or destination.returncode != 0:
            raise RuntimeError(f'{label}: source={source_status}, destination={destination.returncode}')
        return result.decode()


def record(name, value):
    with (HERE / name).open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write('\n')


def main():
    started = datetime.now(timezone.utc).isoformat()
    script = HERE / 'archive_manifest.py'
    program = base64.b64encode(script.read_bytes()).decode()
    expression = f"import base64;exec(compile(base64.b64decode('{program}'),'archive_manifest.py','exec'))"
    scanner = 'python3 -B -c ' + shlex.quote(expression)
    source_facts = remote('ovx2', 'hostname; id; df -B1 /localhome/local-rohing; '
        'nvidia-smi --query-gpu=index,memory.used --format=csv,noheader; '
        'nvidia-smi --query-compute-apps=pid,gpu_uuid --format=csv,noheader')
    dest_facts = remote('ovx4', 'hostname; id; df -B1 /localhome/local-rohing')
    available = int(remote('ovx4', "df -B1 --output=avail /localhome/local-rohing | tail -1"))
    if available < 160_000_000_000:
        raise RuntimeError('insufficient_destination_headroom')
    remote('ovx4', f'set -e; umask 077; test ! -e {shlex.quote(DESTINATION)}; mkdir {shlex.quote(DESTINATION)}; '
        f'test -d {shlex.quote(DESTINATION)} && test ! -L {shlex.quote(DESTINATION)}')
    record('ARCHIVE_COPY_STARTED.json', dict(started_utc=started, source_root=SOURCE,
        destination_root=DESTINATION, exact_directories=DIRECTORIES,
        source_facts=source_facts, destination_facts=dest_facts,
        verification_code_sha256=hashlib.sha256(script.read_bytes()).hexdigest(),
        authorization='Main: lossless COPY of exactly three reviewed retired directories',
        source_deletion_or_remapping=False, no_new_credentials=True, no_gpu_operations=True))
    manifest = DESTINATION + '/SOURCE_MANIFEST.jsonl'
    pipe(f'{scanner} inventory {shlex.quote(SOURCE)}',
        f'set -o noclobber; cat > {shlex.quote(manifest)}', 'MANIFEST')
    manifest_sha = remote('ovx4', f'sha256sum {shlex.quote(manifest)}')
    record('ARCHIVE_MANIFEST_READY.json', dict(destination_manifest_sha256=manifest_sha,
        utc=datetime.now(timezone.utc).isoformat()))
    archive = DESTINATION + '/retired-node3.tar.zst'
    names = ' '.join(shlex.quote(name) for name in DIRECTORIES)
    source_command = f'set -o pipefail; tar --format=pax --acls --xattrs --xattrs-include="*" '
    source_command += f'--selinux --numeric-owner --sort=name --sparse --atime-preserve=system '
    source_command += f'-C {shlex.quote(SOURCE)} -cf - {names} | zstd -T2 -1 -c'
    pipe(source_command, f'set -e; set -o noclobber; cat > {shlex.quote(archive)}; '
        f'sync -f {shlex.quote(archive)}', 'TRANSFER')
    record('ARCHIVE_TRANSFER_READY.json', dict(utc=datetime.now(timezone.utc).isoformat(),
        destination_archive=archive, archive_stat=remote('ovx4', f'stat {shlex.quote(archive)}'),
        transfer_exit_codes=[0, 0], validation_pending=True, reclaimed_bytes=0))
    verification = remote('ovx4', f'set -o pipefail; zstd -dc {shlex.quote(archive)} | '
        f'{scanner} verify {shlex.quote(manifest)}')
    result = json.loads(verification)
    result.update(utc=datetime.now(timezone.utc).isoformat(), destination_root=DESTINATION,
        manifest_sha256=manifest_sha, archive_sha256=remote('ovx4', f'sha256sum {shlex.quote(archive)}'),
        source_disk=remote('ovx2', 'df -B1 /localhome/local-rohing'),
        source_deletion_or_remapping=False, full_filesystem_restore_not_claimed=True)
    record('ARCHIVE_COPY_VERIFIED.json', result)
    payload = base64.b64encode(json.dumps(result, sort_keys=True, indent=2).encode()).decode()
    remote('ovx4', f'set -o noclobber; printf %s {shlex.quote(payload)} | base64 -d > '
        f'{shlex.quote(DESTINATION + "/COPY_VERIFIED.json")}')
    print(json.dumps(result, sort_keys=True), flush=True)


if __name__ == '__main__':
    try:
        main()
    except BaseException as error:
        record('ARCHIVE_COPY_FAILED.json', dict(utc=datetime.now(timezone.utc).isoformat(),
            error_type=type(error).__name__, error=str(error), no_automatic_retry=True,
            source_untouched=True, partial_destination_preserved=True))
        raise
