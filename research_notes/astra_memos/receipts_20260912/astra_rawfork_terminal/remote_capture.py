import datetime
import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile

ROOT = Path('/localhome/local-rohing/astra_diagnostics/astra_P0_raw_wake_fork_seed0_20260912_attempt1')
WEIGHTS = {'adapter_model.safetensors', 'adapter_model.bin'}


def read(path):
    return json.loads(path.read_text())


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def terminal():
    observed = datetime.datetime.now(datetime.timezone.utc).isoformat()
    launched, started, completed = [read(ROOT / name) for name in ('LAUNCHED.json', 'STARTED.json', 'COMPLETED.json')]
    assert not (ROOT / 'FAILED.json').exists()
    assert launched['pid'] == started['pid'] == 77998
    assert launched['device'] == started['device'] == '1'
    assert not Path('/proc/77998').exists(), 'controller still present; reservation remains Main-owned'
    assert set(completed['arms']) == {'lesson', 'sham'}
    cleanups = {}
    for arm in ('lesson', 'sham'):
        result = read(ROOT / f'logs/{arm}/result.json')
        done = read(ROOT / f'probes/{arm}/PAIR_DONE.json')
        assert result == completed['arms'][arm] and result['pair_done'] == done
        assert done['evidence_label'] == 'EVALUATION_ONLY'
        for prefix, stages in ((f'logs/{arm}', ('train', 'pair')), (f'probes/{arm}', ('off', 'on'))):
            for stage in stages:
                relative = f'{prefix}/{stage}.cleanup.json'
                cleanup = read(ROOT / relative)
                process = read(ROOT / f'{prefix}/{stage}.process.json')
                assert cleanup['pid'] == process['pid'] and cleanup['device'] == '1'
                assert cleanup['cleanup_error'] is None
                assert all(cleanup[key] is True for key in
                           ('owned_group_empty', 'gpu_processes_absent', 'reservation_release_verified'))
                cleanups[relative] = cleanup
    return dict(observed_utc=observed, controller_pid=77998, controller_proc_present=False,
                completed_utc=completed['completed_utc'], cleanup_receipts=cleanups,
                reservation='No release action taken; Main owns reservation decisions')


before = terminal()
rehashes = []
for arm in ('lesson', 'sham'):
    spec_path = ROOT / f'logs/{arm}/probe_spec.json'
    spec_hash = digest(spec_path)
    spec = read(spec_path)
    adapter = ROOT / f'training/{arm}_seed0'
    assert spec['adapter_path'] == str(adapter)
    expected = spec['expected_adapter_hashes']
    assert len(WEIGHTS & expected.keys()) == 1
    actual = {}
    for name, expected_hash in expected.items():
        relative = Path(name)
        assert not relative.is_absolute() and '..' not in relative.parts
        path = adapter / name
        assert path.is_file() and not path.is_symlink()
        actual[name] = digest(path)
        assert actual[name] == expected_hash, (arm, name, 'adapter hash mismatch')
    assert digest(spec_path) == spec_hash
    rehashes.append(dict(arm=arm, training_seed=0, adapter_path=str(adapter), spec_sha256=spec_hash,
                        expected_adapter_hashes=expected, actual_adapter_hashes=actual))

files = sorted(path for path in ROOT.rglob('*') if path.is_file() and path.name not in WEIGHTS)
assert all(not path.is_symlink() for path in ROOT.rglob('*'))
hashes = {str(path.relative_to(ROOT)): digest(path) for path in files}


def add_json(archive, name, value):
    content = (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()
    info = tarfile.TarInfo(name)
    info.size, info.mode = len(content), 0o600
    archive.addfile(info, io.BytesIO(content))


with tarfile.open(fileobj=sys.stdout.buffer, mode='w|gz') as archive:
    for path in files:
        archive.add(path, arcname=f'{ROOT.name}/{path.relative_to(ROOT)}', recursive=False)
    assert all(digest(ROOT / relative) == expected for relative, expected in hashes.items()), 'run files changed during capture'
    after = terminal()
    add_json(archive, 'terminal_receipt.json', dict(before=before, after=after))
    add_json(archive, 'remote_adapter_rehash.json', dict(records=rehashes, observed_utc=after['observed_utc'],
        scope='Remote CPU byte rehash only; no local weight payload or loaded-runtime authentication'))
    add_json(archive, 'run_file_sha256.json', dict(root=str(ROOT), sha256=hashes, excluded_weight_names=sorted(WEIGHTS)))
