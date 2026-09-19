"""Stage unused caption source/operator paths and run only read-only CPU checks."""

import io
import json
from pathlib import Path
import shlex
import subprocess
import tarfile

from prepare import HERE, NEW_SOURCE, checksum
from verify_saved import BASE, require


REMOTE_OPERATOR = BASE / 'caption_checkpoint_tail_cpu_20260919_v2'
STAGER = '''
import hashlib,io,json,os,sys,tarfile
from pathlib import Path
namespace={'__name__':'readonly_binding_verification'}
exec(VERIFY, namespace)
namespace['main']()
source=Path(SOURCE)
operator=Path(OPERATOR)
if source.exists() or operator.exists():
    raise ValueError('declared_source_or_operator_path_already_exists_never_overwrite')
with tarfile.open(fileobj=io.BytesIO(sys.stdin.buffer.read())) as archive:
    members=archive.getmembers()
    for member in members:
        relative=Path(member.name)
        if not member.isfile() or relative.is_absolute() or '..' in relative.parts or relative.parts[0] not in ('source','operator'):
            raise ValueError('unsafe_archive_member')
    for member in members:
        relative=Path(member.name)
        root=source if relative.parts[0]=='source' else operator
        path=root.joinpath(*relative.parts[1:])
        path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb') as stream:
            stream.write(archive.extractfile(member).read())
            stream.flush()
            os.fsync(stream.fileno())
        path.chmod(0o444)
manifest=json.loads((operator/'prepared_v2/MANIFEST.json').read_bytes())
actual={str(path.relative_to(source)):hashlib.sha256(path.read_bytes()).hexdigest() for path in source.rglob('*') if path.is_file()}
if actual!=manifest['all_files']:
    raise ValueError('staged_closure_mismatch')
for root in (source,operator):
    for path in sorted([root]+[path for path in root.rglob('*') if path.is_dir()],key=lambda path:len(path.parts),reverse=True):
        descriptor=os.open(path,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
        os.fsync(descriptor)
        os.close(descriptor)
        path.chmod(0o555)
namespace['main']()
print(json.dumps(dict(staged=True,source=str(source),operator=str(operator),files=len(actual),native_launches=0)))
'''


def remote(command, payload=None, timeout=300):
    result = subprocess.run(['bash', 'gpu/ovx_ssh.sh', command], input=payload,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    return result


def main():
    require('Ran 23 tests' in (HERE / 'TESTS_LOCAL_V2.txt').read_text()
        and (HERE / 'TESTS_LOCAL_V2.txt').read_text().rstrip().endswith('OK'), 'local_CPU_tests_first')
    archive_bytes = io.BytesIO()
    blobs = {str(path.relative_to(HERE / 'prepared_v2')): path.read_bytes()
        for path in (HERE / 'prepared_v2/source').rglob('*') if path.is_file()}
    for name in ('verify_saved.py', 'node_probe.py', 'test_caption_tail.py'):
        blobs['operator/' + name] = (HERE / name).read_bytes()
    for name in ('MANIFEST.json', 'PLAN_CANDIDATE.json', 'GUARD_REQUIREMENTS.json'):
        blobs['operator/prepared_v2/' + name] = (HERE / 'prepared_v2' / name).read_bytes()
    blobs['operator/original/PLAN.json'] = (HERE / 'original/PLAN.json').read_bytes()
    with tarfile.open(fileobj=archive_bytes, mode='w') as archive:
        for name, content in sorted(blobs.items()):
            member = tarfile.TarInfo(name)
            member.size = len(content)
            archive.addfile(member, io.BytesIO(content))
    payload = archive_bytes.getvalue()
    program = 'SOURCE=' + repr(str(NEW_SOURCE)) + '\nOPERATOR=' + repr(str(REMOTE_OPERATOR)) + '\nVERIFY=' + repr((HERE / 'verify_saved.py').read_text()) + '\n' + STAGER
    result = remote('python3 -B -c ' + shlex.quote(program), payload)
    receipt = dict(returncode=result.returncode, stdout=result.stdout.decode(), stderr=result.stderr.decode(),
        archive_sha256=checksum(payload), archive_bytes=len(payload),
        operator_files={name:checksum(content) for name,content in blobs.items() if name.startswith('operator/')})
    with (HERE / 'STAGED_V2.json').open('x') as stream:
        json.dump(receipt, stream, sort_keys=True, indent=2)
    require(result.returncode == 0, result.stderr.decode())
    environment = 'env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 CAPTION_TEST_SOURCE=' + shlex.quote(str(NEW_SOURCE))
    python = '/localhome/local-rohing/v2/venv/bin/python -B '
    result = remote(environment + ' ' + python + shlex.quote(str(REMOTE_OPERATOR / 'test_caption_tail.py')))
    (HERE / 'TESTS_NODE_V2.txt').write_bytes(result.stdout + result.stderr)
    require(result.returncode == 0, result.stderr.decode())
    result = remote(environment + ' ' + python + shlex.quote(str(REMOTE_OPERATOR / 'node_probe.py'))
        + ' --prepared ' + shlex.quote(str(REMOTE_OPERATOR / 'prepared_v2')), timeout=600)
    with (HERE / 'ACTUAL_CPU_V2.json').open('x') as stream:
        json.dump(dict(returncode=result.returncode, stderr=result.stderr.decode(),
            result=json.loads(result.stdout) if result.returncode == 0 else None), stream, sort_keys=True, indent=2)
    require(result.returncode == 0, result.stderr.decode())
    report = json.loads(result.stdout)
    print(json.dumps({key:report[key] for key in ('passed','raw_scan_seconds','boundary_and_binary_seconds',
        'optimizer_payload_seconds','rows','sleep_frontier','sleep_count','optimizer_steps','launch_ready')}))


if __name__ == '__main__':
    main()
