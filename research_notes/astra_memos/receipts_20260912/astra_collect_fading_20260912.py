import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tarfile

spec = importlib.util.spec_from_file_location('sentinel', '/tmp/astra_fading_sentinel_20260912.py')
sentinel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sentinel)
source = Path.home() / 'astra_sources/3a12807f88747bafd0aada1d4a09ba88b915f903'
sentinel.bind(source)
from gpu.astra_mini_sudoku_diagnostic import check_free

root = Path.home() / 'astra_diagnostics/astra_fundamental_fading_20260912_attempt1/runs'
read = sentinel.base.read
stage = sys.argv[1]
assert stage in ('status', 'finish')
status = {}
for rate in sentinel.RATES:
    launch = read(root / 'launch' / ('rate-' + rate) / 'launch.json')
    lineage = root / ('rate-' + rate)
    terminal_path = lineage / 'terminal.json'
    terminal = read(terminal_path) if terminal_path.exists() else None
    status[rate] = dict(pid=launch['pid'], controller_present=(Path('/proc') / str(launch['pid'])).exists(),
        completed_fits=len(list(lineage.glob('*/fit-result.json'))),
        completed_readouts=len(list(lineage.glob('*/result.json'))),
        terminal_status=terminal['status'] if terminal else None,
        error=terminal['error'] if terminal else None)
print(json.dumps(status, sort_keys=True), flush=True)
if stage == 'status':
    sys.exit(0)
assert all(not row['controller_present'] and row['terminal_status'] is not None for row in status.values())
sentinel.verify(root)
for rate, (_, device) in sentinel.RATES.items():
    lineage = root / ('rate-' + rate)
    terminal = read(lineage / 'terminal.json')
    launch = read(root / 'launch' / ('rate-' + rate) / 'launch.json')
    for phase in terminal['phases']:
        phase_root = lineage / phase['phase']
        fit = read(phase_root / 'fit-result.json')
        assert sentinel.trainer._warm_inventory(fit['adapter']) == fit['adapter_files']
        assert sentinel.trainer._warm_inventory(fit['parent']) == fit['parent_files']
    release_path = lineage / 'main_release.json'
    if release_path.exists():
        release = read(release_path)
        assert release['terminal_sha256'] == sentinel.base.digest(lineage / 'terminal.json')
        continue
    gpu, xml = check_free(device)
    observed = datetime.datetime.now(datetime.timezone.utc)
    release = dict(full_release=True, terminal_status=terminal['status'], device=device,
        controller_pid=launch['pid'], controller_absent=True, release_utc=observed.isoformat(),
        terminal_sha256=sentinel.base.digest(lineage / 'terminal.json'),
        full_reservation_seconds=(observed - datetime.datetime.fromisoformat(launch['started_utc'])).total_seconds(),
        gpu=gpu)
    with (lineage / 'main_release.xml').open('x') as output:
        output.write(xml)
    sentinel.write(release_path, release)
    print(json.dumps(dict(rate=rate, **release), sort_keys=True), flush=True)
archive = Path('/tmp/astra_fundamental_fading_terminal_20260912.tgz')
assert not archive.exists()
files = [path for path in sorted(root.parent.rglob('*')) if path.is_file()
         and path.suffix not in ('.bin', '.safetensors', '.pt', '.pyc')]
manifest = {str(path.relative_to(Path.home())): sentinel.base.digest(path) for path in files}
with tarfile.open(archive, 'x:gz') as output:
    for path in files:
        output.add(path, arcname=str(path.relative_to(Path.home())), recursive=False)
with tarfile.open(archive, 'r:gz') as archived:
    assert len(archived.getmembers()) == len(files)
    for name, expected in manifest.items():
        assert hashlib.sha256(archived.extractfile(name).read()).hexdigest() == expected
assert manifest == {str(path.relative_to(Path.home())): sentinel.base.digest(path) for path in files}
validation = dict(archive=str(archive), sha256=sentinel.base.digest(archive), files=manifest,
    weights='Retained at node3 immutable run roots, not in lightweight capsule',
    terminal_statuses={rate: row['terminal_status'] for rate, row in status.items()})
sentinel.write(Path(str(archive) + '.validation.json'), validation)
print(json.dumps(dict(archive=str(archive), sha256=validation['sha256'], files=len(files)), sort_keys=True))
