from datetime import datetime
import hashlib
import io
import json
import os
from pathlib import Path
import socket
import stat
import tarfile
import time


AUTHORITY_SHA = 'c55f64ad16f62e76fe7e4d584e85692e841d29a0ea541fdbbf85178cee9f3cd3'
SELECTED_ARMS = ('parented_learning', 'unparented_learning')
ADAPTER_NAMES = {'README.md', 'adapter_config.json', 'adapter_model.safetensors'}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def archive_size(sizes):
    blocks = sum(512 + ((size + 511)//512)*512 for size in sizes) + 1024
    return ((blocks + 10239)//10240)*10240


def safe_member(name):
    path = Path(name)
    return not path.is_absolute() and '..' not in path.parts and len(path.parts) in (4, 5)


def capture(payload, base, inventory, checked_bytes, output):
    authority_raw = payload['authority_raw'].encode()
    assert sha(authority_raw) == AUTHORITY_SHA
    authority = json.loads(authority_raw)
    start = datetime.fromisoformat(authority['issued_utc'].replace('Z', '+00:00')).timestamp()
    end = datetime.fromisoformat(authority['source_read_end_utc'].replace('Z', '+00:00')).timestamp()
    assert start < time.time() < end, 'fresh_observation_after_authority_required'
    assert socket.gethostname() == '[REDACTED_HOST]'
    root = Path(authority['source_root'])
    assert root == base['ROOT'] and authority['cohort_sha256'] == base['COHORT']
    expected_keys = {f'{arm}/sleep_{milestone:06d}' for arm in SELECTED_ARMS for milestone in (1, 2, 4)}
    assert set(authority['selected_commits']) == expected_keys
    reader_class = base['Reader']
    class CurrentReader(reader_class):
        def __init__(self, root):
            super().__init__(root, limit=authority['source_metadata_read_bytes_maximum'], end=end)
    base = dict(base, Reader=CurrentReader, ARMS=SELECTED_ARMS, END=end)
    observed = inventory['observe'](base)
    assert observed['started_unix'] > start
    original_raw = payload['original_observation_raw'].encode()
    assert sha(original_raw) == authority['observation_sha256']
    original = json.loads(original_raw)
    metadata_reader = CurrentReader(root)
    metadata_reader.bytes = observed['scanned_bytes']
    commits, allowlist, boundary_refs = {}, {}, []
    for selected, expected in authority['selected_commits'].items():
        arm, checkpoint_name = selected.split('/')
        milestone = str(int(checkpoint_name.removeprefix('sleep_')))
        fresh = observed['arms'][arm]['intended'][milestone]
        prior = original['arms'][arm]['intended'][milestone]
        assert fresh['disposition'] == 'COMPLETED_BOUNDARY_METADATA_BOUND_PENDING_CUSTODY'
        assert fresh['commit']['sha256'] == expected == prior['commit']['sha256']
        for name in ('record', 'intent'):
            assert fresh['boundary_matches'][0][name]['sha256'] == prior['boundary_matches'][0][name]['sha256']
            boundary_refs.append(fresh['boundary_matches'][0][name])
        prefix = Path(arm)/'checkpoints'/checkpoint_name
        raw, reference = metadata_reader.read(root/prefix/'COMMIT.json')
        assert reference['sha256'] == expected
        commit = base['decode'](raw)
        assert set(commit['adapter_files']) == ADAPTER_NAMES
        assert Path(commit['adapter_path']) == root/prefix/'adapter'
        commits[str(prefix/'COMMIT.json')] = raw
        allowlist[str(prefix/'COMMIT.json')] = dict(sha256=expected, bytes=len(raw), kind='commit_metadata')
        for name, expected_hash in commit['adapter_files'].items():
            relative = prefix/'adapter'/name
            assert safe_member(str(relative)) and name in ADAPTER_NAMES
            path = root/relative
            base['regular_path'](path)
            info = path.stat(follow_symlinks=False)
            assert stat.S_ISREG(info.st_mode)
            allowlist[str(relative)] = dict(sha256=expected_hash, bytes=info.st_size, kind='adapter_payload')
    payload_limit = authority['adapter_source_payload_bytes_maximum']
    payload_bytes = sum(item['bytes'] for item in allowlist.values() if item['kind'] == 'adapter_payload')
    assert payload_bytes <= payload_limit
    captured = dict(commits)
    used = 0
    for relative, item in allowlist.items():
        if item['kind'] != 'adapter_payload':
            continue
        raw = checked_bytes(root/relative, item['sha256'], payload_limit-used, end)
        assert len(raw) == item['bytes']
        used += len(raw)
        captured[relative] = raw
    for relative, expected in commits.items():
        raw, reference = metadata_reader.read(root/relative)
        assert raw == expected
    for reference in boundary_refs:
        raw, current = metadata_reader.read(Path(reference['path']))
        assert current['sha256'] == reference['sha256']
    assert time.time() < end
    receipt = dict(schema='R159_SLEEP6_ADAPTER_ONLY_CAPTURE_V1', status='BOUNDARIES_AND_PAYLOAD_HASHES_VERIFIED',
        authority_sha256=AUTHORITY_SHA, started_unix=observed['started_unix'], captured_unix=time.time(),
        observation=observed, allowlist=allowlist, source_adapter_bytes_read=used,
        source_metadata_bytes_read=metadata_reader.bytes, source_read_end_unix=end,
        source_written=False, optimizer_rng_history_held_payload_read=False, enrolled=False, dispatched=False)
    receipt_raw = json.dumps(receipt, sort_keys=True, indent=2, allow_nan=False).encode()+b'\n'
    metadata_bytes = sum(len(raw) for raw in commits.values()) + len(receipt_raw)
    assert metadata_bytes <= authority['metadata_copy_bytes_maximum']
    expected_archive_size = archive_size([len(receipt_raw)] + [len(raw) for raw in captured.values()])
    assert expected_archive_size*2 <= authority['adapter_copy_bytes_all_transport_legs_maximum']
    with tarfile.open(fileobj=output, mode='w|', format=tarfile.USTAR_FORMAT) as archive:
        for name, raw in [('R159_CAPTURE_RECEIPT.json', receipt_raw), *captured.items()]:
            member = tarfile.TarInfo(name)
            member.size, member.mode = len(raw), 0o600
            archive.addfile(member, io.BytesIO(raw))
