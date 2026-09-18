"""Read only Leibniz's immutable retained prefix; never contact original C2."""

import hashlib
import json
from pathlib import Path
import shlex
import subprocess


OWN = Path(__file__).resolve().parent
REPO = OWN.parents[4]
REMOTE = '/localhome/local-rohing/rohin174_parenting_20260917/node1/R195_FLEET/creative_b1'
PACKET = '/localhome/local-rohing/orch_r153_r184_staging_20260917/orch_r184_C2_sleep41_1789684294308387719'


def sha(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def main():
    target = OWN / 'RETAINED_PREFIX_0_5128.tar.gz'
    code = f'''import hashlib,pathlib,sys,tarfile
root=pathlib.Path({PACKET!r})
receipt=root/'PRESERVATION_RECEIPT.json'
assert hashlib.sha256(receipt.read_bytes()).hexdigest()=='cc7d7f07ed29c952d8f57f17f679f0fdd2084d85711a763ddebba1a2f518f91e'
paths=[root/'stream/JOURNAL.json',receipt]
for index in range(5129):
 for ending in ('.json','.intent.json'):paths.append(root/'stream/records'/(f'{{index:020d}}'+ending))
assert all(path.is_file() and not path.is_symlink() and path.stat().st_size<32*1024**2 for path in paths)
with tarfile.open(fileobj=sys.stdout.buffer,mode='w|gz') as archive:
 for path in paths:archive.add(path,arcname=str(path.relative_to(root)),recursive=False)
'''
    with target.open('xb') as output:
        result = subprocess.run(['bash', 'gpu/ovx_ssh.sh', '/usr/bin/python3 -B -c ' + shlex.quote(code)],
                                cwd=REPO, stdout=output, stderr=subprocess.PIPE, timeout=240)
    if result.returncode:
        raise RuntimeError(result.stderr.decode()[-1200:])
    suffix = Path('/tmp/r201_node2_fixed_prefix_5129_5846.tar.gz')
    if sha(suffix) != '271a13510cb0d9b14d8696efac9eb19d6ac5e29ba549a6a4d368b3ac27307aa0':
        raise ValueError('Leibniz_fixed_suffix_bytes')
    receipt = dict(source_host='node2_immutable_archive_only', original_C2_calls=0, source_writes=0,
                   prefix_sha256=sha(target), suffix_sha256=sha(suffix), source_checkpoint_used=51,
                   source41_weights_used=False, terminal_record=5846)
    for path, name in ((target, target.name), (suffix, 'FIXED_PREFIX_SUFFIX.tar.gz')):
        expected = sha(path)
        receive = f'''import hashlib,pathlib,sys
path=pathlib.Path({REMOTE!r})/{name!r}
with path.open('xb') as output:
 while chunk:=sys.stdin.buffer.read(1024*1024):output.write(chunk)
with path.open('rb') as handle:assert hashlib.file_digest(handle,'sha256').hexdigest()=={expected!r}
print('FIXED_PREFIX_BYTES_RECEIVED')
'''
        with path.open('rb') as incoming:
            subprocess.run(['bash', 'gpu/a100_ssh.sh', '/usr/bin/python3 -B -c ' + shlex.quote(receive)],
                           cwd=REPO, stdin=incoming, check=True, timeout=240)
    with (OWN / 'FIXED_PREFIX_TRANSPORT.json').open('x') as output:
        json.dump(receipt, output, sort_keys=True, indent=2)
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
