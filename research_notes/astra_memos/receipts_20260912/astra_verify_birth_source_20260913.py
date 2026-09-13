import hashlib
import json
from pathlib import Path
import time


source = Path.home() / 'astra_sources/31b5535ec9f73f7b32fdaf21ccfc3a2a68a948a6'
manifest_path = Path('/tmp/astra_birth_full_source_manifest_20260913.json')
manifest = json.loads(manifest_path.read_text())
for name, expected in manifest.items():
    target = source / name
    assert not Path(name).is_absolute() and '..' not in Path(name).parts
    if expected['kind'] == 'symlink':
        assert target.is_symlink() and str(target.readlink()) == expected['target']
    else:
        assert target.is_file() and not target.is_symlink(), name
        checksum = hashlib.sha256()
        with target.open('rb') as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b''):
                checksum.update(block)
        assert checksum.hexdigest() == expected['sha256'], name
extras = [str(path.relative_to(source)) for path in source.rglob('*')
          if (path.is_file() or path.is_symlink()) and str(path.relative_to(source)) not in manifest]
result = dict(status='CURRENT_SOURCE_SNAPSHOT_MATCH', source=str(source), expected_entries=len(manifest),
    manifest_sha256=hashlib.sha256(manifest_path.read_bytes()).hexdigest(), extra_paths=sorted(extras),
    verified_wall=time.time(), historical_execution_attestation=False)
output = Path('/tmp/astra_birth_full_source_verification_20260913.json')
with output.open('x') as stream:
    json.dump(result, stream, indent=2, sort_keys=True)
    stream.write('\n')
print(json.dumps(result))
