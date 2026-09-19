"""Independent bounded read of the completed node2 canary; no writer locks or writes."""

from collections import Counter
import json
from pathlib import Path
import subprocess
import sys


HERE = Path(__file__).resolve().parent
FROZEN = HERE.parent / 'coalescence_locked'
sys.path.insert(0, str(FROZEN))
import transport_canary as frozen


FINAL_CHAIN = 'e4c78e5fd2acef52b830d6a1c5b9ec4c6696d13b0f2e2858895148287e7daa64'
MAIN_BINDING = 'bd1548fbc5128ba3515edd61bc0e471e417a720a6a0b333b32379cbc1df3c14b'
TRANSPORT_SHA = 'd7f72730d6df730e390a6e9c58b186f3aff281f2420e023cc920b8afe8040452'
READONLY = '''
import base64,hashlib,json,os,stat
from datetime import datetime,timezone
from pathlib import Path
def require(condition):
    if not condition:
        raise ValueError('independent_canary_mismatch')
require(os.getuid()==os.geteuid()==2524)
group=canary['groups'][0]
expected=group['metadata']
canonical=group['canonical']
paths=[entry['path'] for inode in [canonical,*group['replacement_inodes']] for entry in inode['paths']]
require(len(paths)==8 and len(set(paths))==8)
verified=[]
for name in paths:
    path=Path(name)
    require(path.is_absolute() and path.resolve()==path and not path.is_symlink())
    descriptor=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NOATIME)
    try:
        before=os.fstat(descriptor)
        require(stat.S_ISREG(before.st_mode))
        value=hashlib.sha256()
        while block:=os.read(descriptor,4*1024*1024):
            value.update(block)
        actual=dict(size=before.st_size,sha256=value.hexdigest(),uid=before.st_uid,gid=before.st_gid,
            mode=stat.S_IMODE(before.st_mode),mtime_ns=before.st_mtime_ns,
            xattrs={key:base64.b64encode(os.getxattr(descriptor,key)).decode() for key in os.listxattr(descriptor)})
        require(actual==expected and os.fstat(descriptor)==before and path.lstat()==before)
        require((before.st_dev,before.st_ino,before.st_nlink)==(canonical['device'],canonical['inode'],8))
        verified.append(dict(path=name,metadata=actual,device=before.st_dev,inode=before.st_ino,
            nlink=before.st_nlink,ctime_ns=before.st_ctime_ns,atime_ns=before.st_atime_ns,allocated_bytes=before.st_blocks*512))
    finally:
        os.close(descriptor)
for binding in locks['locks']:
    path=Path(binding['path'])
    require(path.resolve()==path and not path.is_symlink())
    info=path.lstat()
    require(binding==dict(path=str(path),device=info.st_dev,inode=info.st_ino,uid=info.st_uid,gid=info.st_gid,
        mode=stat.S_IMODE(info.st_mode),size=info.st_size,nlink=info.st_nlink,mtime_ns=info.st_mtime_ns,ctime_ns=info.st_ctime_ns))
capacity=os.statvfs('/localhome/local-rohing')
print(json.dumps(dict(status='INDEPENDENT_EIGHT_PATH_BYTES_REQUIRED_METADATA_AND_LOCK_IDENTITIES_VERIFIED',
    utc=datetime.now(timezone.utc).isoformat(),host=os.uname().nodename,uid=os.getuid(),paths=verified,
    owner_available_bytes=capacity.f_bavail*capacity.f_frsize,free_bytes_including_reserved=capacity.f_bfree*capacity.f_frsize,
    source_writes=False,WRITER_locks_acquired=False),sort_keys=True))
'''


def local_proof():
    frozen.frozen_artifacts()
    require = frozen.require
    require(frozen.sha((FROZEN / 'transport_canary.py').read_bytes()) == TRANSPORT_SHA, 'unchanged_transport')
    execution = FROZEN / 'CANARY_EXECUTION'
    require(frozen.sha((execution / 'MAIN_BINDING.json').read_bytes()) == MAIN_BINDING, 'exact_Main_binding')
    previous = '0' * 64
    events = [json.loads(line) for line in (execution / 'LEDGER.jsonl').read_bytes().splitlines()]
    for sequence, event in enumerate(events):
        unsigned = {key: value for key, value in event.items() if key != 'sha256'}
        digest = frozen.sha(json.dumps(unsigned, sort_keys=True, separators=(',', ':')).encode())
        require(event['sequence'] == sequence and event['previous_sha256'] == previous
                and event['sha256'] == digest, 'complete_unbroken_canary_ledger')
        previous = digest
    completion = json.loads((execution / 'VERIFIED.json').read_bytes())
    require(len(events) == completion['ledger_records'] == 24 and completion['ssh_exit'] == 0
            and previous == completion['ledger_sha256'] == FINAL_CHAIN
            and completion['completion'] == events[-1]
            and events[-1]['kind'] == 'CANARY_COMPLETE_ALL_PATHS_VERIFIED', 'exact_canary_success')
    return dict(ledger_records=len(events), final_chain=previous, event_counts=dict(Counter(event['kind'] for event in events)),
                receipt_sha256=frozen.sha((execution / 'VERIFIED.json').read_bytes()),
                ledger_raw_sha256=frozen.sha((execution / 'LEDGER.jsonl').read_bytes()), main_binding_sha256=MAIN_BINDING)


def main():
    proof = local_proof()
    program = 'import json\n'
    for name, filename in [('canary', 'CANARY.json'), ('locks', 'WRITER_LOCKS.json')]:
        program += f'{name}=json.loads({(FROZEN / filename).read_text()!r})\n'
    repo = next(path for path in HERE.parents if (path / 'gpu/ovx_ssh.sh').is_file())
    result = subprocess.run(['bash', str(repo / 'gpu/ovx_ssh.sh'), frozen.encoded_command(program + READONLY)],
                            check=True, capture_output=True, text=True, timeout=90)
    print(json.dumps(dict(local=proof, remote=json.loads(result.stdout)), sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
