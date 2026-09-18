"""One bounded read-only wrapper inspection; no candidate or ldconfig execution."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shlex
import subprocess


OWNED = Path(__file__).resolve().parent
REPO = OWNED.parents[2]
REMOTE_READ = '''
import hashlib,json,os,pathlib,stat,sysconfig
requested=pathlib.Path('/sbin/ldconfig')
canonical=requested.resolve(strict=True)
metadata=canonical.stat()
assert stat.S_ISREG(metadata.st_mode) and metadata.st_uid==0 and not metadata.st_mode & 0o022
assert metadata.st_size<=2*1024*1024
with canonical.open('rb') as stream:
    raw=stream.read(2*1024*1024+1)
assert len(raw)==metadata.st_size
util=pathlib.Path(sysconfig.get_path('stdlib'))/'ctypes/util.py'
assert util.stat().st_size<=256*1024
text=util.read_text()
lines=text.splitlines()
starts=[position for position,line in enumerate(lines) if 'def _findSoname_ldconfig' in line]
assert len(starts)==1
print(json.dumps(dict(schema='R175_LDCONFIG_READONLY_PREFLIGHT_V1',requested_path=str(requested),
 canonical_path=str(canonical),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),uid=metadata.st_uid,
 mode=oct(stat.S_IMODE(metadata.st_mode)),binary_executed=False,remote_writes=False,
 ctypes_util_path=str(util),ctypes_util_sha256=hashlib.sha256(text.encode()).hexdigest(),
 ctypes_ldconfig_excerpt='\\n'.join(lines[starts[0]:starts[0]+38])),sort_keys=True,indent=2))
'''


def main():
    with (OWNED / 'LDCONFIG_PREFLIGHT_STARTED.json').open('x') as stream:
        json.dump(dict(started_utc=datetime.now(timezone.utc).isoformat(),
                       candidate_attempt=False, retry_permitted=False), stream)
    remote = ('env -i PATH=/usr/bin:/bin LC_ALL=C LANG=C PYTHONDONTWRITEBYTECODE=1 '
              '/localhome/local-rohing/v2/venv/bin/python -I -B -c ' + shlex.quote(REMOTE_READ))
    result = subprocess.run(['bash', str(REPO / 'gpu/ovx2_ssh.sh'), remote],
                            capture_output=True, check=False)
    for name, raw in (('LDCONFIG_PREFLIGHT_STDOUT.txt', result.stdout),
                      ('LDCONFIG_PREFLIGHT_STDERR.txt', result.stderr)):
        with (OWNED / name).open('xb') as stream:
            stream.write(raw)
    with (OWNED / 'LDCONFIG_PREFLIGHT_TRANSPORT.json').open('x') as stream:
        json.dump(dict(returncode=result.returncode,
                       stdout_sha256=hashlib.sha256(result.stdout).hexdigest(),
                       stderr_sha256=hashlib.sha256(result.stderr).hexdigest()), stream, indent=2)
    if result.returncode != 0:
        raise SystemExit(result.returncode)
    document = json.loads(result.stdout)
    with (OWNED / 'LDCONFIG_PREFLIGHT.json').open('xb') as stream:
        stream.write(result.stdout)
    print(json.dumps(document, indent=2))


if __name__ == '__main__':
    main()
