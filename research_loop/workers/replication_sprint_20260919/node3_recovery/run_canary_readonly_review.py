"""Rehash the proposed canary on its original node; never execute coalescing."""

import base64
import hashlib
import json
from pathlib import Path
import shlex
import subprocess


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
REMOTE = '''
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from assess_hardlinks import ROOT, require
from retired_coalescer import digest, owned_retired_path, verify_path_fd, readable_writer_fds

require(os.uname().nodename == 'ipp2-ovx-p6-09' and os.getuid() == 2524, 'original_node_and_owner')
require(digest(batch) == expected_sha256 and batch['root'] == str(ROOT), 'exact_proposed_canary')
require(batch['execution_status'] == 'REQUIRES_SEPARATE_MAIN_REVIEW', 'not_an_execution_command')
paths = [entry['path'] for group in batch['groups']
    for inode in [group['canonical'], *group['replacement_inodes']] for entry in inode['paths']]
require(len(paths) == len(set(paths)) <= batch['max_paths'] <= 40, 'bounded_explicit_paths')
verified = []
for group in batch['groups']:
    for inode in [group['canonical'], *group['replacement_inodes']]:
        require(inode['links_outside_eligible_set'] == 0, 'no_reviewed_external_links')
        for entry in inode['paths']:
            path = owned_retired_path(entry['path'], ROOT)
            descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NOATIME)
            try:
                verify_path_fd(path, descriptor, group['metadata'], inode)
                current = os.fstat(descriptor)
                require(current.st_ctime_ns == entry['source_ctime_ns']
                    and current.st_nlink == len(inode['paths'])
                    and current.st_blocks * 512 == entry['allocated_bytes'], 'fresh_metadata_and_link_counts')
                verified.append(dict(path=str(path), sha256=group['metadata']['sha256'],
                    device=current.st_dev, inode=current.st_ino, nlink=current.st_nlink,
                    ctime_ns=current.st_ctime_ns, allocated_bytes=current.st_blocks * 512))
            finally:
                os.close(descriptor)
require(len({entry['device'] for entry in verified}) == 1, 'same_device')
scan = readable_writer_fds(paths)
require(not scan['writers'], 'readable_writer_present')
capacity = os.statvfs(ROOT)
print(json.dumps(dict(status='READONLY_EXACT_CANARY_REHASH_AND_METADATA_VERIFIED',
    utc=datetime.now(timezone.utc).isoformat(), host=os.uname().nodename,
    batch_sha256=expected_sha256, verified_paths=verified, writer_scan=scan,
    owner_available_bytes=capacity.f_bavail * capacity.f_frsize,
    free_bytes_including_reserved=capacity.f_bfree * capacity.f_frsize,
    source_mutations=0, execution_approval=False,
    must_recheck_again_immediately_before_any_authorized_mutation=True), sort_keys=True, indent=2))
'''


def main():
    proposal = (HERE / 'HARDLINK_CANARY_PROPOSAL.json').read_bytes()
    batch = json.loads(proposal)
    checksum = hashlib.sha256(proposal).hexdigest()
    pins = {entry['path']: entry['sha256'] for entry in batch['source_code_and_tests']}
    sources = {}
    for name in ['assess_hardlinks.py', 'retired_coalescer.py']:
        payload = (HERE / name).read_bytes()
        if hashlib.sha256(payload).hexdigest() != pins[name]:
            raise ValueError('proposed_source_hash_changed')
        sources[Path(name).stem] = base64.b64encode(payload).decode()
    program = 'import base64,sys,types,json\n'
    for name, payload in sources.items():
        program += f'module=types.ModuleType({name!r});sys.modules[{name!r}]=module\n'
        program += f'exec(compile(base64.b64decode({payload!r}),{name!r},"exec"),module.__dict__)\n'
    program += f'batch=json.loads(base64.b64decode({base64.b64encode(proposal).decode()!r}))\n'
    program += f'expected_sha256={checksum!r}\n' + REMOTE
    expression = 'import base64;exec(compile(base64.b64decode(' + repr(base64.b64encode(program.encode()).decode())
    expression += '),"readonly_canary_review","exec"))'
    with (HERE / 'HARDLINK_CANARY_READONLY_RECHECK.json').open('x') as output, \
            (HERE / 'HARDLINK_CANARY_READONLY_RECHECK.stderr').open('x') as errors:
        result = subprocess.run(['bash', str(REPO / 'gpu/ovx2_ssh.sh'),
            'python3 -B -c ' + shlex.quote(expression)], stdout=output, stderr=errors, timeout=120)
    if result.returncode:
        raise RuntimeError('read-only recheck failed; preserve receipts and do not retry automatically')


if __name__ == '__main__':
    main()
