"""Fetch only guard-pinned original source and small control documents."""

import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import subprocess
import tarfile

from verify_saved import BASE, GUARD_SHA, PLAN_SHA, require


HERE = Path(__file__).resolve().parent
REMOTE = '''
import hashlib,io,json,sys,tarfile
from pathlib import Path
base=Path(BASE)
guard_raw=(base/'control_r233_recovery/GUARD.json').read_bytes()
assert hashlib.sha256(guard_raw).hexdigest()==GUARD_SHA
guard=json.loads(guard_raw)
plan_raw=Path(guard['plan_path']).read_bytes()
assert hashlib.sha256(plan_raw).hexdigest()==PLAN_SHA
plan=json.loads(plan_raw)
with tarfile.open(fileobj=sys.stdout.buffer,mode='w|') as archive:
    blobs={'GUARD.json':guard_raw,'PLAN.json':plan_raw}
    for name,expected in guard['source_pins'].items():
        content=(Path(plan['source_root'])/name).read_bytes()
        assert hashlib.sha256(content).hexdigest()==expected,(name,'source_pin_mismatch')
        blobs['source/'+name]=content
    for name,content in blobs.items():
        member=tarfile.TarInfo(name)
        member.size=len(content)
        member.mode=0o444
        archive.addfile(member,io.BytesIO(content))
'''


def main():
    require((HERE / 'COMMITTED_BINARY_VERIFIED.json').is_file(), 'verify_checkpoint_binaries_first')
    payload = 'BASE=' + repr(str(BASE)) + '\nGUARD_SHA=' + repr(GUARD_SHA) + '\nPLAN_SHA=' + repr(PLAN_SHA) + '\n' + REMOTE
    result = subprocess.run(['bash', 'gpu/ovx_ssh.sh', 'python3 -B -'], input=payload.encode(),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    require(result.returncode == 0, result.stderr.decode())
    destination = HERE / 'original'
    destination.mkdir(exist_ok=False)
    with tarfile.open(fileobj=io.BytesIO(result.stdout)) as archive:
        for member in archive:
            relative = PurePosixPath(member.name)
            require(member.isfile() and not relative.is_absolute() and '..' not in relative.parts,
                'safe_source_archive_member')
            output = destination / relative
            output.parent.mkdir(parents=True, exist_ok=True)
            with output.open('xb') as stream:
                stream.write(archive.extractfile(member).read())
            output.chmod(0o444)
    guard = json.loads((destination / 'GUARD.json').read_bytes())
    for name, expected in guard['source_pins'].items():
        require(hashlib.sha256((destination / 'source' / name).read_bytes()).hexdigest() == expected,
            'fetched_source_integrity')
    print(json.dumps(dict(files=len(guard['source_pins']), transferred_bytes=len(result.stdout),
        original_source_verified=True)))


if __name__ == '__main__':
    main()
