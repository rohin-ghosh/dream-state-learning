import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tarfile

spec = importlib.util.spec_from_file_location('replication', '/tmp/astra_fading_replication_20260912.py')
replication = importlib.util.module_from_spec(spec)
spec.loader.exec_module(replication)
source = Path.home() / 'astra_sources/3a12807f88747bafd0aada1d4a09ba88b915f903'
replication.bind(source, '/tmp/astra_fading_sentinel_20260912.py')
from gpu.astra_mini_sudoku_diagnostic import check_free
base = replication.base
root = Path.home() / 'astra_diagnostics/astra_fundamental_plasticity_replications_20260912_attempt1'
stage = sys.argv[1]
assert stage in ('status', 'finish')
status = {}
for name, branch in replication.BRANCHES.items():
    launch = base.read(root / 'launch' / name / 'launch.json')
    terminal_path = root / name / 'terminal.json'
    terminal = base.read(terminal_path) if terminal_path.exists() else None
    status[name] = dict(pid=launch['pid'], device=branch['device'],
        controller_present=(Path('/proc') / str(launch['pid'])).exists(),
        fit_complete=(root / name / 'fit-result.json').exists(),
        readout_complete=(root / name / 'readout/reduction.json').exists(),
        status=terminal['status'] if terminal else None, error=terminal['error'] if terminal else None)
print(json.dumps(status, sort_keys=True), flush=True)
if stage == 'status':
    sys.exit(0)
assert all(not row['controller_present'] and row['status'] is not None for row in status.values())
replication.verify(root)
for name, branch in replication.BRANCHES.items():
    target = root / name
    terminal = base.read(target / 'terminal.json')
    launch = base.read(root / 'launch' / name / 'launch.json')
    if terminal['result'] is not None:
        fit = terminal['result']['fit']
        assert replication.trainer._warm_inventory(fit['adapter']) == fit['adapter_files']
        assert replication.trainer._warm_inventory(fit['parent']) == fit['parent_files']
    release_path = target / 'main_release.json'
    if release_path.exists():
        assert base.read(release_path)['terminal_sha256'] == base.digest(target / 'terminal.json')
        continue
    gpu, xml = check_free(branch['device'])
    observed = datetime.datetime.now(datetime.timezone.utc)
    with (target / 'main_release.xml').open('x') as output:
        output.write(xml)
    release = dict(full_release=True, controller_absent=True, controller_pid=launch['pid'],
        release_utc=observed.isoformat(), device=branch['device'], gpu=gpu,
        status=terminal['status'], terminal_sha256=base.digest(target / 'terminal.json'),
        full_reservation_seconds=(observed - datetime.datetime.fromisoformat(launch['started_utc'])).total_seconds())
    replication.old.write(release_path, release)
    print(json.dumps(dict(branch=name, **release), sort_keys=True), flush=True)
archive = Path('/tmp/astra_plasticity_replications_terminal_20260912.tgz')
assert not archive.exists()
files = [path for path in sorted(root.rglob('*')) if path.is_file() and path.suffix not in ('.bin', '.safetensors', '.pt', '.pyc')]
manifest = {str(path.relative_to(Path.home())): base.digest(path) for path in files}
with tarfile.open(archive, 'x:gz') as output:
    for path in files:
        output.add(path, arcname=str(path.relative_to(Path.home())), recursive=False)
with tarfile.open(archive, 'r:gz') as archived:
    for name, expected in manifest.items():
        assert hashlib.sha256(archived.extractfile(name).read()).hexdigest() == expected
assert manifest == {str(path.relative_to(Path.home())): base.digest(path) for path in files}
validation = dict(archive=str(archive), sha256=base.digest(archive), files=manifest,
                  statuses=status, weights='Immutable node3 roots; excluded from lightweight capsule')
replication.old.write(Path(str(archive) + '.validation.json'), validation)
print(json.dumps(dict(archive=str(archive), sha256=validation['sha256'], files=len(files)), sort_keys=True))
