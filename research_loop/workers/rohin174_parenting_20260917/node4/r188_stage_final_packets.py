"""Stage only finalized NODE3 originals on their assigned NODE4 receiver."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile
import time


HOME = Path(__file__).resolve().parent
REPO = HOME.parents[3]
PACKETS = HOME.parent / 'node3/r188/final_relocation_20260917t2350z'
REMOTE = '/localhome/local-rohing/orch_r188_node4_relocated_20260917t2349z'
TARGETS = {0: 7, 2: 5, 3: 6}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def validate(physical, document):
    require(physical in TARGETS and document['physical'] == physical, 'only_assigned_originals')
    require(document['status'] == 'PERSISTENT_LOCAL_PACKET_VERIFIED'
        and document['archive_paths_verified'] and document['gzip_crc_verified'], 'verified_final_packet')
    require(document['archive'] == str(PACKETS / f'physical{physical}.tar.gz'), 'final_batch_not_initial_snapshot')
    packet = document['packet']
    require(packet['final_full_stream_included'] and not packet['current_learner_continues']
        and not packet['later_live_updates_not_in_this_packet'], 'actual_stopped_final_packet')


def stage(physical):
    document = json.loads((PACKETS / f'physical{physical}.VERIFIED.json').read_text())
    validate(physical, document)
    archive = Path(document['archive'])
    with archive.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    require(digest == document['archive_sha256'] and archive.stat().st_size == document['archive_bytes'], 'immutable_verified_packet')
    with tarfile.open(archive, 'r:gz') as content:
        prefix = f'physical{physical}/'
        final = json.load(content.extractfile(prefix + 'FINAL_STOP.json'))
        audit = json.loads((PACKETS.parent / 'FINAL_SOURCE_STOP_AUDIT.json').read_text())
        stopped = next(row for row in audit['rows'] if row['physical'] == physical)
    require(final['original_actors_exited'] and stopped['actors_absent']
        and stopped['final'] == final, 'actual_final_source_exit_audit')
    require(final['latest_complete_cycle'] == document['packet']['captured_cycle']
        and final['latest_complete_index'] == document['packet']['saved_record_index'], 'matching_saved_boundary')
    receipt_root = HOME / f'rehome_final_transport_20260917T2349Z/physical{physical}'
    receipt_root.mkdir(parents=True, exist_ok=False)
    for name, value in (('VERIFIED.json', document), ('FINAL_STOP.json', final), ('STOPPED.json', stopped)):
        with (receipt_root / name).open('x') as stream:
            json.dump(value, stream, sort_keys=True, indent=2)
    target = f'{REMOTE}/transport/physical{physical}.tar.gz'
    command = f'set -eu; umask 077; mkdir -p {REMOTE}/transport; set -C; cat > {target}; sha256sum {target}'
    with (receipt_root / 'TRANSPORT_INTENT.json').open('x') as stream:
        json.dump(dict(physical=physical, target_physical=TARGETS[physical], archive_sha256=digest,
            remote_archive=target, observed_unix=time.time(), native_dispatch=False), stream, indent=2)
    with archive.open('rb') as stream:
        result = subprocess.run(['bash', str(REPO / 'gpu/a40r_ssh.sh'), command], stdin=stream,
            capture_output=True, text=True, cwd=REPO, timeout=240)
    matched = result.returncode == 0 and result.stdout.strip() == f'{digest}  {target}'
    receipt = dict(status='FINAL_STOPPED_ARCHIVE_STAGED' if matched else 'FAILED_PRESERVED_NO_RETRY',
        physical=physical, target_physical=TARGETS[physical], remote_archive=target,
        archive_sha256=digest, archive_bytes=document['archive_bytes'], exit_code=result.returncode,
        stdout=result.stdout, stderr=result.stderr, observed_unix=time.time(), native_dispatch=False,
        parent_final_inbox_delta_still_to_reconcile=True)
    receipt['clean_saved_boundary'] = final['clean_saved_boundary']
    receipt['quiet_exit_reconciled'] = stopped.get('quiet_exit_reconciled', False)
    receipt['preserved_suffix_accounting'] = final['current_suffix_accounting']
    with (receipt_root / 'TRANSPORT_RESULT.json').open('x') as stream:
        json.dump(receipt, stream, sort_keys=True, indent=2)
    require(matched, 'exact_remote_transport_hash')
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--physical', type=int, choices=tuple(TARGETS), required=True)
    arguments = parser.parse_args()
    print(json.dumps(stage(arguments.physical), sort_keys=True))
