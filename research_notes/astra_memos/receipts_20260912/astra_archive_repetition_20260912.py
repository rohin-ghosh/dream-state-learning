import hashlib
import json
from pathlib import Path
import tarfile

home = Path.home()
root = home / 'astra_diagnostics/astra_fundamental_repetition_20260912_attempt1'
release = json.loads((root / 'readout_main_release.json').read_text())
assert release['status'] == 'FOUR_REPETITION_DEV_READOUTS_COMPLETE'
assert all(cell['full_release'] for cell in release['cells'].values())
archive = Path('/tmp/astra_fundamental_repetition_terminal_20260912.tgz')
files = [path for path in sorted(root.rglob('*')) if path.is_file()
         and path.suffix not in ('.safetensors', '.bin', '.pt', '.pyc')]
manifest = {str(path.relative_to(home)): hashlib.sha256(path.read_bytes()).hexdigest() for path in files}
with tarfile.open(archive, 'x:gz') as output:
    for path in files:
        output.add(path, arcname=str(path.relative_to(home)), recursive=False)
with tarfile.open(archive, 'r:gz') as source:
    assert len(source.getmembers()) == len(files)
    for name, expected in manifest.items():
        assert hashlib.sha256(source.extractfile(name).read()).hexdigest() == expected
assert manifest == {str(path.relative_to(home)): hashlib.sha256(path.read_bytes()).hexdigest() for path in files}
receipt = dict(archive=str(archive), sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
               files=manifest, weights='Retained on node3; exact inventories in fits/readout plans, not in this lightweight capsule')
with Path(str(archive) + '.validation.json').open('x') as output:
    json.dump(receipt, output, indent=2, sort_keys=True)
print(json.dumps(dict(archive=str(archive), sha256=receipt['sha256'], files=len(files))))
