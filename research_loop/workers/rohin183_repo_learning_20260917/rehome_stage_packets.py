"""Stage verified opaque node3 archives on node2; never extract or dispatch."""

from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
PACKETS = REPO / 'research_loop/workers/rohin174_parenting_20260917/node3/r188/relocation_20260917t2341z'
REMOTE = '/localhome/local-rohing/orch_r188_node2_rehome_20260917t2344z'


def validate(physical, document):
    if physical not in (1, 4, 7) or document.get('physical') != physical:
        raise ValueError('only_assigned_originals')
    if document.get('status') != 'PERSISTENT_LOCAL_PACKET_VERIFIED':
        raise ValueError('verified_packet_required')
    if not document.get('archive_paths_verified') or not document.get('gzip_crc_verified'):
        raise ValueError('archive_validation_required')
    if not re.fullmatch('[0-9a-f]{64}', document.get('archive_sha256', '')):
        raise ValueError('exact_archive_hash_required')
    if document.get('archive') != str(PACKETS / f'physical{physical}.tar.gz'):
        raise ValueError('exact_archive_path_required')


def stage(physical):
    document = json.loads((PACKETS / f'physical{physical}.VERIFIED.json').read_bytes())
    validate(physical, document)
    archive = Path(document['archive'])
    with archive.open('rb') as stream:
        actual = hashlib.file_digest(stream, 'sha256').hexdigest()
    if actual != document['archive_sha256'] or archive.stat().st_size != document['archive_bytes']:
        raise ValueError('local_packet_changed')
    prefix = HERE / f'REHOME_PHYSICAL{physical}_TRANSPORT'
    with prefix.with_suffix('.STARTED.json').open('x') as stream:
        json.dump(dict(started_unix=time.time(), archive_sha256=actual, no_retry=True,
            original_physical=physical, native_dispatch=False), stream, sort_keys=True)
    target = f'{REMOTE}/transport/physical{physical}.tar.gz'
    command = f'set -eu; umask 077; mkdir -p {REMOTE}/transport; set -C; cat > {target}; sha256sum {target}'
    started = time.time()
    try:
        with archive.open('rb') as stream:
            result = subprocess.run(['bash', 'gpu/ovx_ssh.sh', command], stdin=stream,
                capture_output=True, text=True, cwd=REPO, timeout=180)
        matched = result.returncode == 0 and result.stdout.strip() == f'{actual}  {target}'
        receipt = dict(status='OPAQUE_ARCHIVE_STAGED' if matched else 'FAILED_PRESERVED_NO_RETRY',
            original_physical=physical, remote_archive=target, archive_sha256=actual,
            archive_bytes=document['archive_bytes'], started_unix=started, finished_unix=time.time(),
            exit_code=result.returncode, stdout=result.stdout, stderr=result.stderr,
            final_source_stop_delta_required=True, extracted=False, native_dispatch=False)
    except Exception as error:
        receipt = dict(status='UNKNOWN_TRANSPORT_PRESERVED_NO_RETRY', original_physical=physical,
            remote_archive=target, error_type=type(error).__name__, finished_unix=time.time(), native_dispatch=False)
    with prefix.with_suffix('.RESULT.json').open('x') as stream:
        json.dump(receipt, stream, indent=2, sort_keys=True)
    return receipt


if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=3) as pool:
        print(json.dumps(list(pool.map(stage, (1, 4, 7))), sort_keys=True))
