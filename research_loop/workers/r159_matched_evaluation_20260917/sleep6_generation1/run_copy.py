import hashlib
import json
from pathlib import Path
import subprocess
import tarfile


directory = Path(__file__).resolve().parent
worker = directory.parent
repository = worker.parents[2]
authority = worker/'MAIN_SLEEP6_SOURCE_COPY_AUTHORITY_20260917.json'
assert hashlib.sha256(authority.read_bytes()).hexdigest() == 'c55f64ad16f62e76fe7e4d584e85692e841d29a0ea541fdbbf85178cee9f3cd3'
payload = dict(authority_raw=authority.read_text(),
    original_observation_raw=(worker/'sleep_inventory1/OBSERVATION.json').read_text())
sources = {'base':worker/'observation_20260917_generation2/observe.py',
           'inventory':worker/'sleep_inventory1/inventory.py',
           'previous_copy':worker/'initial3_generation1/capture_initial3.py'}
program = 'import sys\n'
for name,path in sources.items():
    program += name+"={'__name__':'metadata_definitions'}\nexec("+repr(path.read_text())+','+name+')\n'
program += (directory/'copy_sleep6.py').read_text()
program += '\ncapture('+repr(payload)+",base,inventory,previous_copy['checked_bytes'],sys.stdout.buffer)\n"
archive = directory/'SLEEP6.private.tar'
with archive.open('xb') as output, (directory/'CAPTURE.stderr').open('xb') as errors:
    subprocess.run(['bash',str(repository/'gpu/a40r_ssh.sh'),'python3 -B -'], input=program.encode(),
        stdout=output, stderr=errors, timeout=300, check=True)
archive.chmod(0o400)
assert archive.stat().st_size*2 <= 1073741824
with tarfile.open(archive) as stream:
    members = stream.getmembers()
    assert len(members) == 25 and all(member.isfile() for member in members)
    receipt_raw = stream.extractfile('R159_CAPTURE_RECEIPT.json').read()
    receipt = json.loads(receipt_raw)
    expected = set(receipt['allowlist']) | {'R159_CAPTURE_RECEIPT.json'}
    assert len({member.name for member in members}) == len(members) and {member.name for member in members} == expected
    for name,item in receipt['allowlist'].items():
        raw = stream.extractfile(name).read()
        assert len(raw) == item['bytes'] and hashlib.sha256(raw).hexdigest() == item['sha256']
with (directory/'CAPTURE_RECEIPT.json').open('xb') as output:
    output.write(receipt_raw)
summary = dict(status='FIRST_HOP_HASH_VERIFIED_NO_ENROLLMENT', archive_sha256=hashlib.file_digest(archive.open('rb'),'sha256').hexdigest(),
    archive_bytes=archive.stat().st_size, all_two_hop_bytes=2*archive.stat().st_size,
    source_adapter_bytes=receipt['source_adapter_bytes_read'], source_metadata_bytes=receipt['source_metadata_bytes_read'],
    receipt_sha256=hashlib.sha256(receipt_raw).hexdigest(), captured_unix=receipt['captured_unix'], files=24)
with (directory/'COPY_SUMMARY.json').open('x') as output:
    json.dump(summary, output, sort_keys=True, indent=2)
    output.write('\n')
print(json.dumps(summary,sort_keys=True))
