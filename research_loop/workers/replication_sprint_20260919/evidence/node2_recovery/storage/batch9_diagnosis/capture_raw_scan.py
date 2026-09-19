"""Capture original BATCH9 scanner stdout before validation; never acquire locks or mutate."""

import base64
import json
from pathlib import Path
import subprocess
import sys


HERE = Path(__file__).resolve().parent
STORAGE = HERE.parent
FROZEN = STORAGE / 'coalescence_locked'
sys.path.insert(0, str(FROZEN))
import transport_canary as frozen
import pidfd_scan


BATCH_SHA = '722ad53ce435564128ff2b2e6e32b8d8495c2c83f3f091f2c28f72d222cbd45e'
SCANNER_SHA = '3f2e858d2d540759aaef0d7cd56acae56600460a72da039803793dc71d15503c'
PROGRAM = '''
import base64,json,os,subprocess,time
from datetime import datetime,timezone
from pathlib import Path
def metadata(path):
    info=Path(path).lstat()
    return dict(path=path,device=info.st_dev,inode=info.st_ino,size=info.st_size,nlink=info.st_nlink,
        uid=info.st_uid,gid=info.st_gid,mode=info.st_mode,mtime_ns=info.st_mtime_ns,ctime_ns=info.st_ctime_ns)
assert len(paths)==40 and len(set(paths))==40 and os.getuid()==os.geteuid()==2524
before=[metadata(path) for path in paths]
started=datetime.now(timezone.utc).isoformat()
clock=time.monotonic()
result=subprocess.run(['sudo','-n','python3','-B','-c',scanner_program],input=json.dumps(paths).encode(),
    capture_output=True,timeout=45)
after=[metadata(path) for path in paths]
space=os.statvfs('/localhome/local-rohing')
report=dict(started_utc=started,finished_utc=datetime.now(timezone.utc).isoformat(),elapsed_seconds=time.monotonic()-clock,
    host=os.uname().nodename,uid=os.getuid(),batch_sha256=batch_sha256,scanner_source_sha256=scanner_source_sha256,
    target_paths=paths,returncode=result.returncode,raw_stdout_base64=base64.b64encode(result.stdout).decode(),
    raw_stderr_base64=base64.b64encode(result.stderr).decode(),path_metadata_before=before,path_metadata_after=after,
    all_target_metadata_unchanged=before==after,writer_locks_acquired=False,coalescence_attempted=False,
    owner_available_bytes=space.f_bavail*space.f_frsize,bfree=space.f_bfree,bavail=space.f_bavail,frsize=space.f_frsize)
try: report['raw_scan']=json.loads(result.stdout)
except ValueError: report['raw_scan_parse_failed']=True
print(json.dumps(report,sort_keys=True))
'''


def main():
    frozen.frozen_artifacts()
    frozen.require(frozen.sha((FROZEN / 'pidfd_scan.py').read_bytes()) == SCANNER_SHA, 'unchanged_original_scanner')
    raw = (STORAGE / 'coalescence_remaining/BATCH_0009.json').read_bytes()
    frozen.require(frozen.sha(raw) == BATCH_SHA, 'exact_failed_batch')
    batch = json.loads(raw)
    paths = [entry['path'] for group in batch['groups'] for inode in [group['canonical'], *group['replacement_inodes']]
             for entry in inode['paths']]
    program = f'paths={paths!r}\nscanner_program={pidfd_scan.PROGRAM!r}\nbatch_sha256={BATCH_SHA!r}\nscanner_source_sha256={SCANNER_SHA!r}\n' + PROGRAM
    repo = next(path for path in HERE.parents if (path / 'gpu/ovx_ssh.sh').is_file())
    result = subprocess.run(['bash', str(repo / 'gpu/ovx_ssh.sh'), frozen.encoded_command(program)],
                            capture_output=True, text=True, check=True, timeout=60)
    report = json.loads(result.stdout)
    timestamp = report['started_utc'].replace('-', '').replace(':', '').replace('+0000', 'Z').replace('.', '_')
    destination = HERE / f'RAW_SCAN_{timestamp}.json'
    with destination.open('x') as output:
        json.dump(report, output, sort_keys=True, indent=2)
        output.write('\n')
    print(json.dumps(dict(receipt=str(destination),sha256=frozen.sha(destination.read_bytes()),
        started_utc=report['started_utc'],returncode=report['returncode'],raw_scan=report.get('raw_scan'),
        owner_available_bytes=report['owner_available_bytes'],all_target_metadata_unchanged=report['all_target_metadata_unchanged']),sort_keys=True))


if __name__ == '__main__':
    main()
