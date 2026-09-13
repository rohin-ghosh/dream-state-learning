import hashlib
import json
from pathlib import Path
import tarfile

base = Path('/data/home/rohing/dream-state/gpu_artifacts_local/pcfl_event_sequence_S_A_20260913_attempt4')
root = base / 'unpacked/pcfl_event_sequence_S_A_20260913_attempt4'
failed = Path('/data/home/rohing/dream-state/gpu_artifacts_local/pcfl_event_sequence_S_A_20260913_attempt3/unpacked/pcfl_event_sequence_S_A_20260913_attempt3')
read = lambda path: json.loads(path.read_text())
checksum = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
with tarfile.open(base / 'evidence.tar') as archive:
    files = [member for member in archive if member.isfile()]
    assert len(files) == len({member.name for member in files})
    for member in files:
        assert not Path(member.name).is_absolute() and '..' not in Path(member.name).parts
        with archive.extractfile(member) as stream:
            assert hashlib.file_digest(stream, 'sha256').hexdigest() == checksum(base / 'unpacked' / member.name)
collection = read(root / 'collection.json')
completed = read(root / 'fit/completed.json')
manifest = read(root / 'fit/checkpoint/train_manifest.json')
previous = read(failed / 'fit/checkpoint/train_manifest.json')
assert collection['status'] == 'COMPLETED' and collection['returncode'] == 0 and collection['errors'] == []
assert collection['gpu_released'] is True
assert completed['kind'] == 'NATIVE' and completed['status'] == 'COMPLETE' and completed['phase'] == 'S_A'
assert completed['updates'] == manifest['steps'] == manifest['micro_batches'] == 40
assert completed['nonfinite_batches'] == manifest['nonfinite_batches'] == 0
assert completed['base_unchanged'] is True
assert not (root / 'fit/failure.json').exists()
for name, digest in completed['files'].items():
    assert checksum(root / 'fit' / name) == digest, name
assert all(name.endswith(('.lora_A.default.weight', '.lora_B.default.weight')) for name in completed['trainable_names'])
comparable = ['config', 'corpus', 'tokens', 'truncation', 'base_model', 'versions', 'lora',
              'packing', 'steps', 'micro_batches', 'nonfinite_batches', 'epochs_run', 'mean_loss_per_epoch',
              'final_loss', 'train_tokens_seen', 'empty']
field_matches = {name: manifest[name] == previous[name] for name in comparable}
adapter_match = checksum(root / 'fit/checkpoint/adapter_model.safetensors') == checksum(failed / 'fit/checkpoint/adapter_model.safetensors')
output = {'status': 'COMPLETED_NATIVE_FIT_ARCHIVE_AUDIT_PASS', 'archive_files_verified': len(files),
    'phase': 'S_A', 'updates': 40, 'nonfinite_batches': 0, 'final_loss': manifest['final_loss'],
    'base_unchanged_assertion_verified': True, 'trainable_names_count': len(completed['trainable_names']),
    'trainable_params': manifest['lora']['trainable_params'], 'truncation': manifest['truncation'],
    'previous_failed_attempt_comparable_field_matches': field_matches,
    'adapter_bytes_equal_failed_attempt': adapter_match,
    'elapsed_seconds': {'outer': collection['elapsed_seconds'], **completed['elapsed_seconds']},
    'completed_file_sha256': checksum(root / 'fit/completed.json'),
    'adapter_file_sha256': checksum(root / 'fit/checkpoint/adapter_model.safetensors'),
    'cold_calls': 0, 'acquisition_measured': False, 'retention_measured': False,
    'previous_failed_attempt_eligible': False, 'automatic_promotion': False}
destination = Path('/tmp/astra_pcfl_event_sequence_S_A_audit_20260913_attempt4.json')
with destination.open('x') as stream:
    json.dump(output, stream, indent=2, sort_keys=True)
    stream.write('\n')
print(json.dumps(output, indent=2))
