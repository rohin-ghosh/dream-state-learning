import datetime
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2] if sys.argv[1:2] != ['emit'] else ROOT
LIVES = {
    'C2': 'orch_r153_community_C2_20260916_attempt1/life',
    'C1': 'orch_r153_community_C1_20260916_attempt1/life',
    'run1': 'orch_r125_continual_20260916_attempt1/run1',
    'C3': 'orch_r153_community_C3_20260916_attempt1/life',
    'C4': 'orch_r153_community_C4_20260916_attempt1/life',
    'C5': 'orch_r153_community_C5_20260916_attempt1/life',
    'pilot': 'orch_r127_pilot_20260916_attempt1/run1',
    'repo_reader': 'orch_r136_repo_reader_20260916_attempt1/recovery_r154_saved30_20260916_attempt2/run1',
}


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def write_json(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')
    os.replace(temporary, path)


def emit(relative, life):
    source = Path('/localhome/local-rohing') / relative
    checkpoints = sorted(path.parent for path in (source / 'checkpoints').glob('sleep_*/COMMIT.json'))
    if not checkpoints:
        raise RuntimeError('No complete checkpoint')
    selected = [checkpoints[-1]]
    if life == 'C2':
        selected.extend(source / 'checkpoints' / f'sleep_{sleep:06d}' for sleep in (51, 52))
    for checkpoint in selected:
        if not (checkpoint / 'COMMIT.json').is_file():
            raise RuntimeError(f'Missing required checkpoint: {checkpoint.name}')
    files = []
    for child in source.iterdir():
        if child.name == 'checkpoints':
            continue
        files.extend(child.rglob('*') if child.is_dir() and not child.is_symlink() else [child])
    for checkpoint in set(selected):
        files.extend(checkpoint.rglob('*'))
    files = sorted({path for path in files if path.is_file() or path.is_symlink()})
    total = sum(path.lstat().st_size for path in files)
    if total > 12 * 1024 ** 3:
        raise RuntimeError('Per-life backup exceeds bounded 12GiB')
    manifest = dict(life=life, source=str(source), started=now(), host=os.uname().nodename,
        selected_checkpoints=[path.name for path in sorted(set(selected))], files={},
        consistency='Immutable completed checkpoints and enumerated journal prefix; mutable sidecars are a live insurance copy, not an atomic whole-life snapshot.')
    with tarfile.open(fileobj=sys.stdout.buffer, mode='w|gz') as archive:
        for path in files:
            name = str(path.relative_to(source))
            info = archive.gettarinfo(str(path), arcname=name)
            if info.issym():
                archive.addfile(info)
                manifest['files'][name] = dict(symlink=info.linkname)
            elif info.isfile():
                data = path.read_bytes()
                info.size = len(data)
                archive.addfile(info, io.BytesIO(data))
                manifest['files'][name] = dict(size=len(data), sha256=hashlib.sha256(data).hexdigest())
        manifest['finished'] = now()
        data = json.dumps(manifest, sort_keys=True).encode()
        info = tarfile.TarInfo('OFFNODE_MANIFEST.json')
        info.size = len(data)
        archive.addfile(info, io.BytesIO(data))


def verify(path):
    observed = {}
    commit_checks = {}
    with tarfile.open(path, 'r|gz') as archive:
        for entry in archive:
            if entry.issym():
                observed[entry.name] = dict(symlink=entry.linkname)
                continue
            handle = archive.extractfile(entry)
            if entry.name == 'OFFNODE_MANIFEST.json':
                manifest = json.load(handle)
                continue
            hasher = hashlib.sha256()
            captured = []
            for block in iter(lambda: handle.read(1024 * 1024), b''):
                hasher.update(block)
                if entry.name.endswith('/COMMIT.json'):
                    captured.append(block)
            observed[entry.name] = dict(size=entry.size, sha256=hasher.hexdigest())
            if captured:
                commit_checks[entry.name] = json.loads(b''.join(captured))
    if observed != manifest['files']:
        raise RuntimeError('Manifest mismatch')
    for commit_name, commit in commit_checks.items():
        prefix = str(Path(commit_name).parent)
        for filename, expected in commit['adapter_files'].items():
            if observed[f'{prefix}/adapter/{filename}']['sha256'] != expected:
                raise RuntimeError('Adapter commit hash mismatch')
        for key in ('optimizer', 'rng'):
            if observed[f'{prefix}/optimizer_rng.pt']['sha256'] != commit['checkpoint_sha256'][key]:
                raise RuntimeError('Optimizer/RNG commit hash mismatch')
    hasher = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            hasher.update(block)
    return dict(verified=now(), archive=str(path), archive_sha256=hasher.hexdigest(),
        bytes=path.stat().st_size, file_count=len(observed), **{key: manifest[key] for key in
        ('life', 'source', 'host', 'selected_checkpoints', 'consistency', 'started', 'finished')})


def run():
    for life, relative in LIVES.items():
        target = ROOT / life
        target.mkdir(exist_ok=True)
        if (target / 'VERIFIED.json').exists():
            continue
        write_json(ROOT / 'STATUS.json', dict(pid=os.getpid(), life=life, stage='copy', updated=now()))
        partial = target / 'SNAPSHOT.tar.gz.partial'
        with partial.open('wb') as output, (target / 'stderr.log').open('wb') as errors:
            result = subprocess.run(['bash', str(REPO / 'gpu/ovx3_ssh.sh'),
                f'python3 - emit {relative} {life}'], input=Path(__file__).read_bytes(),
                stdout=output, stderr=errors, timeout=1800)
        if result.returncode:
            raise RuntimeError(f'{life} remote copy failed: {result.returncode}')
        receipt = verify(partial)
        complete = target / 'SNAPSHOT.tar.gz'
        partial.rename(complete)
        receipt['archive'] = str(complete)
        write_json(target / 'VERIFIED.json', receipt)
        print(json.dumps(receipt), flush=True)
    write_json(ROOT / 'STATUS.json', dict(pid=os.getpid(), stage='complete', updated=now(), lives=list(LIVES)))


if __name__ == '__main__':
    if sys.argv[1] == 'emit':
        emit(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == 'start':
        with (ROOT / 'service.log').open('ab') as output:
            process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), 'run'],
                stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
        write_json(ROOT / 'SERVICE.json', dict(pid=process.pid, started=now()))
        print(process.pid)
    elif sys.argv[1] == 'run':
        try:
            run()
        except Exception as error:
            write_json(ROOT / 'STATUS.json', dict(pid=os.getpid(), stage='failed', updated=now(), error=str(error)))
            raise
