import hashlib
import json
from pathlib import Path
import tarfile


archive_path = Path('/data/home/rohing/dream-state/gpu_artifacts_local/additive_replay_20260913_attempt1/evidence.tar')
expected = '1faf1f6a6482a3834f7aa4c98c34b71c29644acdc4dfec9ac7c0b3cd7c3b1d16'
mirror = Path('/tmp/astra_additive_replay_native_20260913_attempt1')
receipt_path = Path('/tmp/astra_additive_archive_receipt_20260913.json')
assert not mirror.exists() and not receipt_path.exists()
assert hashlib.file_digest(archive_path.open('rb'), 'sha256').hexdigest() == expected
roots = {f'additive_replay_seed{seed}_20260913_attempt1{suffix}' for seed in range(3)
         for suffix in ('', '.launcher', '.collection_claim.json', '_collected', '.collection_repair1_claim.json', '_collected_repair1')}
roots.update(('astra_additive_replay_collection_repair_20260913.py', 'astra_additive_replay_specs_20260913_attempt1'))
with tarfile.open(archive_path) as archive:
    members = archive.getmembers()
    assert len(members) == len({member.name for member in members}) == 1366
    assert {Path(member.name).parts[0] for member in members} == roots
    for member in members:
        path = Path(member.name)
        assert not path.is_absolute() and '..' not in path.parts
        assert member.isfile() or member.isdir()
    adapters = [member.name for member in members if member.name.endswith('/adapter_model.safetensors')]
    assert len(adapters) == 6
    mirror.mkdir()
    archive.extractall(mirror, filter='data')
    for member in members:
        if member.isfile():
            assert hashlib.file_digest((mirror / member.name).open('rb'), 'sha256').digest() == hashlib.file_digest(archive.extractfile(member), 'sha256').digest()
recovery_pins = ('91ad84077e8edf34ab4c5ec5be763b6cab9c333d74e22073f53a95b0f110220e',
                 '72bee9376c7aafa1a052a6bf31a951264076c990bea7a446e4ef4fa6e5adb50a',
                 '72eefd3e8e6bcc20cbe8717bf26c60a625b055f44edacfa59667b391d497c956')
for seed, checksum in enumerate(recovery_pins):
    name = f'additive_replay_seed{seed}_20260913_attempt1'
    for filename, expected_exit in (('controller_exit.json', 0), ('collector_exit.json', 1), ('exit.json', 1)):
        receipt = json.loads((mirror / (name + '.launcher') / filename).read_text())
        assert type(receipt['returncode']) is int and receipt['returncode'] == expected_exit
    recovered = mirror / (name + '_collected_repair1') / 'recovery.json'
    assert hashlib.file_digest(recovered.open('rb'), 'sha256').hexdigest() == checksum
    receipt = json.loads(recovered.read_text())
    assert receipt['scientific_retry'] is False and receipt['collection_attempt'] == 2
    assert type(receipt['returncode']) is int and receipt['returncode'] == 0
    assert receipt['fits'] == receipt['updates'] == receipt['generation_calls'] == 0
receipt = dict(archive=str(archive_path), sha256=expected, bytes=archive_path.stat().st_size,
               members=len(members), adapters=6, mirror=str(mirror), all_extracted_bytes_verified=True,
               native_controller_returncodes=[0, 0, 0], original_collector_returncodes=[1, 1, 1],
               original_holder_returncodes=[1, 1, 1], collection_repair_returncodes=[0, 0, 0],
               collection_repair_sha256='9b67256c42b7f7c18e79a10f9bc6201140833e8d6c339a7e192ca18de67c854a',
               scientific_retry=False)
with receipt_path.open('x') as stream:
    stream.write(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt, indent=2))
