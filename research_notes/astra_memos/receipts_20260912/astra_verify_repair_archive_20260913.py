import hashlib
import json
from pathlib import Path
import tarfile


archive_path = Path('/data/home/rohing/dream-state/gpu_artifacts_local/own_replay_repair_20260913_attempt1/evidence.tar')
expected = '86c2aadc7b35a50ccb58ad81e4c4733200423d121db75b25afde1112538d8936'
mirror = Path('/tmp/astra_own_replay_repair_native_20260913_attempt1')
assert not mirror.exists()
assert hashlib.file_digest(archive_path.open('rb'), 'sha256').hexdigest() == expected
roots = {f'own_replay_repair_seed{seed}_20260913_attempt1{suffix}' for seed in range(3)
         for suffix in ('', '_collected', '.collection_claim.json', '.launcher')}
with tarfile.open(archive_path) as archive:
    members = archive.getmembers()
    assert len({member.name for member in members}) == len(members)
    for member in members:
        name = Path(member.name)
        assert not name.is_absolute() and '..' not in name.parts
        assert name.parts[0] in roots
        assert member.isfile() or member.isdir()
    adapters = [member.name for member in members if member.name.endswith('/adapter_model.safetensors')]
    assert len(adapters) == 6
    mirror.mkdir()
    archive.extractall(mirror, filter='data')
    for member in members:
        if member.isfile():
            actual = mirror / member.name
            assert actual.stat().st_size == member.size
            assert hashlib.file_digest(actual.open('rb'), 'sha256').digest() == hashlib.file_digest(archive.extractfile(member), 'sha256').digest()
receipt = dict(archive=str(archive_path), sha256=expected, bytes=archive_path.stat().st_size,
               members=len(members), adapters=adapters, mirror=str(mirror), all_extracted_bytes_verified=True)
Path('/tmp/astra_own_replay_repair_archive_receipt_20260913.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt, indent=2))
