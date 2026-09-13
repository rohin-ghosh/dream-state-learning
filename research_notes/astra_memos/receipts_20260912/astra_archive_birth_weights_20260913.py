import argparse
import hashlib
import json
from pathlib import Path
import tarfile
import time


def digest(path):
    checksum = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            checksum.update(block)
    return checksum.hexdigest()


parser = argparse.ArgumentParser()
parser.add_argument('--fit-root', type=Path, required=True)
parser.add_argument('--plan-sha256', required=True)
parser.add_argument('--release', type=Path, required=True)
parser.add_argument('--release-sha256', required=True)
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args()
assert digest(args.fit_root / 'plan.json') == args.plan_sha256
assert digest(args.release) == args.release_sha256
release = json.loads(args.release.read_text())
assert release['root'] == str(args.fit_root)
assert release['plan_sha256'] == args.plan_sha256
assert release['phase_complete'] is True and release['full_release'] is True
assert release['status'] == 'COLLECTED_RELEASED'
assert not args.out.exists()
args.out.mkdir()
members = {}
for arm in ('AUTH', 'DERANGED'):
    receipt_path = args.fit_root / 'run' / arm / 'receipt.json'
    assert digest(receipt_path) == release['evidence_hashes'][str(receipt_path)]
    receipt = json.loads(receipt_path.read_text())
    adapter = args.fit_root / 'run' / arm / 'adapter'
    expected = receipt['adapter_files']
    assert set(expected) == {path.name for path in adapter.iterdir()}
    for name, pin in expected.items():
        source = adapter / name
        assert source.is_file() and not source.is_symlink()
        assert source.parent == adapter and digest(source) == pin
        members[arm + '/' + name] = (source, pin)
archive = args.out / 'birth_adapters.tgz'
with tarfile.open(archive, 'x:gz') as output:
    for name, (source, pin) in sorted(members.items()):
        output.add(source, arcname=name, recursive=False)
with tarfile.open(archive) as stored:
    assert set(stored.getnames()) == set(members)
    assert len(stored.getnames()) == len(members)
    for member in stored.getmembers():
        assert member.isfile()
        assert hashlib.sha256(stored.extractfile(member).read()).hexdigest() == members[member.name][1]
for source, pin in members.values():
    assert digest(source) == pin
receipt = dict(status='WEIGHT_BYTES_ARCHIVED', archived_wall=time.time(), fit_root=str(args.fit_root),
    plan_sha256=args.plan_sha256, release_sha256=args.release_sha256, archive=str(archive),
    archive_sha256=digest(archive), members={name: pin for name, (source, pin) in members.items()},
    tool_sha256=digest(__file__), no_gpu_work=True, model_origin='UNRESOLVED_LOCAL_HASHES_ONLY',
    scientific_promotion=False)
with (args.out / 'receipt.json').open('x') as output:
    json.dump(receipt, output, sort_keys=True, indent=2)
    output.write('\n')
print(json.dumps(dict(archive=str(archive), archive_sha256=receipt['archive_sha256'],
    receipt=str(args.out / 'receipt.json'), receipt_sha256=digest(args.out / 'receipt.json'))))
