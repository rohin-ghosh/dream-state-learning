import argparse
import hashlib
import json
from pathlib import Path
import tarfile


parser = argparse.ArgumentParser()
parser.add_argument('--archive-sha256', required=True)
options = parser.parse_args()
expected = options.archive_sha256
assert len(expected) == 64 and all(character in '0123456789abcdef' for character in expected)
archive_path = Path('/data/home/rohing/dream-state/gpu_artifacts_local/parenting_alignment_20260913_attempt1/evidence.tar')
mirror = Path('/tmp/astra_parenting_alignment_native_20260913_attempt1')
receipt_path = Path('/tmp/astra_parenting_alignment_archive_receipt_20260913.json')
assert not mirror.exists() and not receipt_path.exists()
assert hashlib.file_digest(archive_path.open('rb'), 'sha256').hexdigest() == expected
roots = {f'parenting_alignment_seed{seed}_20260913_attempt1{suffix}' for seed in range(3)
         for suffix in ('', '_collected', '.collection_claim.json', '.launcher')}
with tarfile.open(archive_path) as archive:
    members = archive.getmembers()
    assert len({member.name for member in members}) == len(members)
    assert {Path(member.name).parts[0] for member in members} == roots
    for member in members:
        name = Path(member.name)
        assert not name.is_absolute() and '..' not in name.parts
        assert name.parts[0] in roots
        assert member.isfile() or member.isdir()
    adapters = [member.name for member in members if member.name.endswith('/adapter_model.safetensors')]
    assert not adapters
    mirror.mkdir()
    archive.extractall(mirror, filter='data')
    for member in members:
        if member.isfile():
            actual = mirror / member.name
            assert actual.stat().st_size == member.size
            assert hashlib.file_digest(actual.open('rb'), 'sha256').digest() == hashlib.file_digest(archive.extractfile(member), 'sha256').digest()
for seed in range(3):
    launcher = mirror / f'parenting_alignment_seed{seed}_20260913_attempt1.launcher'
    for name in ('controller_exit.json', 'collector_exit.json', 'exit.json'):
        receipt = json.loads((launcher / name).read_text())
        assert type(receipt['returncode']) is int and receipt['returncode'] == 0
receipt = dict(archive=str(archive_path), sha256=expected, bytes=archive_path.stat().st_size,
               members=len(members), new_adapters=0, mirror=str(mirror), all_extracted_bytes_verified=True,
               original_adapter_archive='gpu_artifacts_local/level1_second_roster_20260913/node2_second_perception.tar',
               original_adapter_archive_sha256='addc2e61ce05f2b622482adde82f16c2c571db6dd072b0fb7750a4d6dc559a3a')
with receipt_path.open('x') as stream:
    stream.write(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt, indent=2))
