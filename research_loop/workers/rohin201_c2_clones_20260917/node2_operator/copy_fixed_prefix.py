"""Copy only the immutable journal prefix ending at the shared console cut."""

import hashlib
import json
from pathlib import Path
import shlex
import subprocess

from stage_math_d import CAPTURE, OWN, REMOTE, REPO


def main():
    manifest = json.loads((CAPTURE / 'MANIFEST.json').read_bytes())
    complete = next(item for item in manifest['files'] if item['relative'] == 'complete/SLEEP_COMPLETE.json')
    records = str(Path(complete['source']).parent)
    assert manifest['console_record']['index'] == 5846
    terminal = manifest['console_record']['sha256']
    code = f'''import hashlib,io,json,pathlib,sys,tarfile
records=pathlib.Path({records!r})
def raw(path):
    assert path.is_file() and not path.is_symlink() and path.stat().st_size<32*1024**2
    return path.read_bytes()
def digest(document):return hashlib.sha256(json.dumps(document,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
end=json.loads(raw(records/'00000000000000005846.json'))
assert end['sha256']=={terminal!r} and end['sha256']==digest({{key:value for key,value in end.items() if key!='sha256'}})
inbox_hashes={manifest['inbox_hashes']!r}
with tarfile.open(fileobj=sys.stdout.buffer,mode='w|gz') as archive:
    for index in range(5129,5847):
        for ending in ('.json','.intent.json'):
            filename=f'{{index:020d}}'+ending
            payload=raw(records/filename)
            info=tarfile.TarInfo('records/'+filename);info.size=len(payload);info.mode=0o600
            archive.addfile(info,io.BytesIO(payload))
    for filename,expected in inbox_hashes.items():
        assert pathlib.Path(filename).name==filename
        payload=raw(records.parent/'inbox'/filename)
        assert hashlib.sha256(payload).hexdigest()==expected
        info=tarfile.TarInfo('inbox/'+filename);info.size=len(payload);info.mode=0o600
        archive.addfile(info,io.BytesIO(payload))
'''
    target = Path('/tmp/r201_node2_fixed_prefix_5129_5846.tar.gz')
    with target.open('xb') as output:
        result = subprocess.run(['bash', 'gpu/ovx3_ssh.sh', '/usr/bin/python3 -B -c ' + shlex.quote(code)],
                                cwd=REPO, stdout=output, stderr=subprocess.PIPE, timeout=240)
    if result.returncode:
        raise RuntimeError(result.stderr.decode()[-1200:])
    with target.open('rb') as handle:
        archive_sha = hashlib.file_digest(handle, 'sha256').hexdigest()
    receive = f'''import hashlib,pathlib,sys
root=pathlib.Path({REMOTE!r})/'math_d1'
path=root/'FIXED_PREFIX_SUFFIX.tar.gz'
with path.open('xb') as output:
    while chunk:=sys.stdin.buffer.read(1024*1024):output.write(chunk)
with path.open('rb') as handle:assert hashlib.file_digest(handle,'sha256').hexdigest()=={archive_sha!r}
print('FIXED_PREFIX_RECEIVED_NO_SOURCE_WRITE')
'''
    with target.open('rb') as incoming:
        result = subprocess.run(['bash', 'gpu/ovx_ssh.sh', '/usr/bin/python3 -B -c ' + shlex.quote(receive)],
                                cwd=REPO, stdin=incoming, capture_output=True, timeout=240)
    if result.returncode:
        raise RuntimeError(result.stderr.decode()[-1200:])
    receipt = dict(status='FIXED_PREFIX_SUFFIX_COPIED_NOT_LAUNCHED',
        remote_archive=REMOTE+'/math_d1/FIXED_PREFIX_SUFFIX.tar.gz',sha256=archive_sha,
        bytes=target.stat().st_size,first_record=5129,last_record=5846,
        terminal_sha256=terminal,source_records=records,source_writes=0,
        inbox_policy='Capture-bounded hash-matched bytes; receiver keeps only registrations through5846')
    patch='*** Begin Patch\n*** Add File: '+str(OWN/'FIXED_PREFIX_COPY.json')+'\n'
    patch+=''.join('+'+line+'\n' for line in json.dumps(receipt,indent=2).splitlines())+'*** End Patch\n'
    subprocess.run(['apply_patch'],input=patch,text=True,check=True,capture_output=True)
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
