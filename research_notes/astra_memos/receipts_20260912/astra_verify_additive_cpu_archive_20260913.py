import hashlib
import json
from pathlib import Path
import tarfile


archive_path = Path('/data/home/rohing/dream-state/gpu_artifacts_local/additive_replay_tiny_cpu_20260913_attempt1/evidence.tar')
expected = '6b4114b63b4ee0bfee46d145a425bf71037512de1e02be3ffebf972c1abcff9a'
mirror = Path('/tmp/astra_additive_cpu_archive_mirror_20260913_attempt1')
assert hashlib.file_digest(archive_path.open('rb'), 'sha256').hexdigest() == expected
assert not mirror.exists()
with tarfile.open(archive_path) as archive:
    members = archive.getmembers()
    assert len(members) == 48 and len({member.name for member in members}) == 48
    for member in members:
        name = Path(member.name)
        assert not name.is_absolute() and '..' not in name.parts
        assert member.isfile() or member.isdir()
        assert name.parts[0] in ('astra_additive_replay_tiny_cpu_20260913_attempt1', 'astra_additive_replay_cpu_payload_20260913_attempt1')
    mirror.mkdir()
    archive.extractall(mirror, filter='data')
    for member in members:
        if member.isfile():
            assert hashlib.file_digest((mirror / member.name).open('rb'), 'sha256').digest() == hashlib.file_digest(archive.extractfile(member), 'sha256').digest()
root = mirror / 'astra_additive_replay_tiny_cpu_20260913_attempt1'
receipt_path = root / 'receipt.json'
assert hashlib.file_digest(receipt_path.open('rb'), 'sha256').hexdigest() == 'ff2346a72f7e4fed9f4cdb51c90bb701c736557add56f0462f2b1e7ef2bc0b7d'
receipt = json.loads(receipt_path.read_text())
assert receipt['status'] == 'PASS' and receipt['fixture_only'] is True
assert receipt['native_scientific_evidence'] is False and all(receipt['checks'].values())
for name, checksum in receipt['retained_files'].items():
    assert hashlib.file_digest((root / name).open('rb'), 'sha256').hexdigest() == checksum
print(json.dumps(dict(archive_sha256=expected, members=len(members), verified=True, checks=receipt['checks'], elapsed_seconds=receipt['elapsed_seconds'])))
