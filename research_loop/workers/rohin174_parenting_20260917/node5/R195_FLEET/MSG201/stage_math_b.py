"""Stage the exact shared capture and Main overlay into a new node2 root."""

import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import tarfile


REPO = Path(__file__).resolve().parents[6]
OWN = Path(__file__).resolve().parent
CAPTURE = REPO / 'research_loop/workers/rohin174_parenting_20260917/node5/R195_FLEET/MSG201/C2_SNAPSHOT_20260918T021847Z'
REMOTE = '/localhome/local-rohing/orch_r201_math_b_node5_20260918_attempt1'
MANIFEST_SHA = '29ca04c2c51671c7df922a4b05448586e74eec35da45b03009877baccbccce84'
ARCHIVE_SHA = '9beaf7a79063c5cf4af2868e1f3122dfea7f4fa5ce3f7d3f2f51716676cdee34'
MAIN_SHA = '599f44f1a39bc0a312a180963feef8affc62748cec20721a79112bfc5a0540b1'


def sha(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def run_remote(code, incoming=None):
    command = '/usr/bin/python3 -B -c ' + shlex.quote(code)
    result = subprocess.run(['bash', 'gpu/ovx3_ssh.sh', command], cwd=REPO,
                            stdin=incoming, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, timeout=240)
    if result.returncode:
        raise RuntimeError(result.stderr.decode()[-1600:])
    return result.stdout.decode()


def main():
    assert sha(CAPTURE / 'MANIFEST.json') == MANIFEST_SHA
    assert sha(CAPTURE / 'SNAPSHOT.tar') == ARCHIVE_SHA
    manifest = json.loads((CAPTURE / 'MANIFEST.json').read_bytes())
    expected = {item['relative']: item['sha256'] for item in manifest['files']}
    with tarfile.open(CAPTURE / 'SNAPSHOT.tar') as archive:
        members = archive.getmembers()
        assert len(members) == len(expected) == 180
        assert all(member.isfile() and member.name in expected for member in members)
        assert len({member.name for member in members}) == len(members)
        for member in members:
            assert hashlib.file_digest(archive.extractfile(member), 'sha256').hexdigest() == expected[member.name]
    with (CAPTURE / 'SNAPSHOT.tar').open('rb') as incoming:
        run_remote(f'''import hashlib,pathlib,sys
root=pathlib.Path({REMOTE!r})
target=root/'snapshot'
target.mkdir(mode=0o700)
archive=target/'SNAPSHOT.tar'
with archive.open('xb') as output:
    while chunk:=sys.stdin.buffer.read(1024*1024):output.write(chunk)
with archive.open('rb') as handle:assert hashlib.file_digest(handle,'sha256').hexdigest()=={ARCHIVE_SHA!r}
print('EXACT_CAPTURE_RECEIVED')
''', incoming)
    for filename in ('MANIFEST.json', 'VERIFIED.json'):
        with (CAPTURE / filename).open('rb') as incoming:
            run_remote(f"import pathlib,sys;pathlib.Path({REMOTE!r},'snapshot',{filename!r}).write_bytes(sys.stdin.buffer.read())", incoming)
    print(run_remote(f'''import hashlib,json,pathlib,shutil,tarfile,time
root=pathlib.Path({REMOTE!r})
snapshot=root/'snapshot'
def sha(path):
    with path.open('rb') as handle:return hashlib.file_digest(handle,'sha256').hexdigest()
assert sha(snapshot/'MANIFEST.json')=={MANIFEST_SHA!r}
assert sha(root/'main_ready/runtime_overlay.tar.gz')=={MAIN_SHA!r}
manifest=json.loads((snapshot/'MANIFEST.json').read_bytes())
expected={{item['relative']:item['sha256'] for item in manifest['files']}}
with tarfile.open(snapshot/'SNAPSHOT.tar') as archive:
    members=archive.getmembers()
    assert len(members)==len(expected) and all(member.isfile() and member.name in expected for member in members)
    archive.extractall(snapshot,filter='data')
assert all(sha(snapshot/name)==digest for name,digest in expected.items())
arm=root
assert arm.is_dir()
shutil.copytree(snapshot/'source',arm/'source')
ready=json.loads((root/'main_ready/READY.json').read_bytes())
with tarfile.open(root/'main_ready/runtime_overlay.tar.gz') as archive:
    members=archive.getmembers()
    assert all(member.isfile() and member.name in ready['files'] for member in members)
    assert len(members)==len(ready['files'])==33
    archive.extractall(arm/'source',filter='data')
for name,digest in ready['files'].items():
    assert sha(arm/'source'/name)==digest
receipt=dict(status='EXACT_CAPTURE_MAIN_OVERLAY_STAGED_NOT_LAUNCHED',observed_unix=time.time(),
    source_root=str(arm/'source'),snapshot_manifest_sha256={MANIFEST_SHA!r},snapshot_archive_sha256={ARCHIVE_SHA!r},
    main_archive_sha256={MAIN_SHA!r},snapshot_files=len(expected),overlay_files=len(ready['files']),
    checkpoint_cycle=51,optimizer_steps=4908,console_record=5846,launches=0,signals=0)
with (arm/'STAGED.json').open('x') as output:json.dump(receipt,output,sort_keys=True,indent=2)
print(json.dumps(receipt))
'''))


if __name__ == '__main__':
    main()
