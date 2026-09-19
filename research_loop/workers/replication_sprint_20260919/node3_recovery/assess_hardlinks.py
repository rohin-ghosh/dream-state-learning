"""Bounded read-only eligibility; never links, renames, deletes or writes source."""

from collections import defaultdict
import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import stat
import sys


ROOT = Path('/localhome/local-rohing/orch_r205_node3_20260918')
DIRECTORIES = {'r225_siege_retirement_20260918', 'r233_retirement_20260918T1144Z',
    'r224_challenger_retirement_20260918'}
FIELDS = ('size', 'sha256', 'uid', 'gid', 'mode', 'mtime_ns', 'xattrs')


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def analyze(lines, root=ROOT):
    groups = defaultdict(list)
    manifest_hasher = hashlib.sha256()
    total_rows = 0
    for line in lines:
        manifest_hasher.update(line)
        item = json.loads(line)
        name = Path(item['path'])
        require(not name.is_absolute() and '..' not in name.parts and name.parts[0] in DIRECTORIES,
            'exact_three_retired_directory_scope')
        total_rows += 1
        if item['kind'] != 'file' or item['size'] < 1024**2:
            continue
        key = json.dumps({field: item[field] for field in FIELDS}, sort_keys=True)
        groups[key].append(item)
    eligible = []
    rejected = []
    allocated_savings = 0
    logical_savings = 0
    preexisting_hardlinks = 0
    external_link_inodes = 0
    for encoded_metadata, items in groups.items():
        if len({(item['device'], item['inode']) for item in items}) < 2:
            continue
        identities = defaultdict(list)
        problem = None
        for item in items:
            path = root / item['path']
            observed = path.lstat()
            expected = (item['device'], item['inode'], item['size'], item['uid'], item['gid'],
                item['mode'], item['mtime_ns'], item['ctime_ns'], item['nlink'])
            actual = (observed.st_dev, observed.st_ino, observed.st_size, observed.st_uid, observed.st_gid,
                stat.S_IMODE(observed.st_mode), observed.st_mtime_ns, observed.st_ctime_ns, observed.st_nlink)
            attributes = {name: base64.b64encode(os.getxattr(path, name, follow_symlinks=False)).decode()
                for name in os.listxattr(path, follow_symlinks=False)}
            if not stat.S_ISREG(observed.st_mode) or path.resolve() != path or actual != expected \
                    or attributes != item['xattrs']:
                problem = dict(path=str(path), reason='source_changed_or_redirected_since_hashed_manifest')
                break
            identities[(observed.st_dev, observed.st_ino)].append(dict(path=str(path),
                allocated_bytes=observed.st_blocks * 512, nlink=observed.st_nlink,
                current_atime_ns=observed.st_atime_ns, source_ctime_ns=observed.st_ctime_ns))
        if problem:
            rejected.append(problem)
            continue
        require(len({identity[0] for identity in identities}) == 1, 'hardlinks_require_same_filesystem')
        inodes = []
        for identity, paths in identities.items():
            require(len(paths) <= paths[0]['nlink'], 'manifest_path_count_exceeds_link_count')
            outside = paths[0]['nlink'] - len(paths)
            external_link_inodes += int(outside > 0)
            preexisting_hardlinks += len(paths) - 1
            inodes.append(dict(device=identity[0], inode=identity[1], paths=paths,
                links_outside_eligible_set=outside, allocated_bytes=paths[0]['allocated_bytes']))
        keep = min(inodes, key=lambda item: (item['links_outside_eligible_set'] == 0,
            item['allocated_bytes'], item['paths'][0]['path']))
        replace = [item for item in inodes if item is not keep]
        freed = sum(item['allocated_bytes'] for item in replace if item['links_outside_eligible_set'] == 0)
        logical = sum(items[0]['size'] for item in replace if item['links_outside_eligible_set'] == 0)
        allocated_savings += freed
        logical_savings += logical
        atimes = {path['current_atime_ns'] for inode in inodes for path in inode['paths']}
        eligible.append(dict(metadata=json.loads(encoded_metadata), canonical=keep,
            replacement_inodes=replace, potential_allocated_bytes_freed=freed,
            potential_logical_bytes_coalesced=logical, all_current_atimes_identical=len(atimes) == 1,
            would_change_inode_identity_ctime_and_link_count=True,
            mutation_authorized=False))
    filesystem = os.statvfs(root)
    available = filesystem.f_bavail * filesystem.f_frsize
    free = filesystem.f_bfree * filesystem.f_frsize
    reserve_gap = max(0, free - available)
    return dict(schema='NODE3_RETIRED_HARDLINK_READONLY_ASSESSMENT_V1',
        utc=datetime.now(timezone.utc).isoformat(), manifest_sha256=manifest_hasher.hexdigest(),
        manifest_rows=total_rows, exact_matching_fields=list(FIELDS), threshold_bytes=1024**2,
        eligible_groups=len(eligible), rejected_groups=rejected,
        eligible_allocated_bytes_potential=allocated_savings,
        eligible_logical_bytes_potential=logical_savings,
        existing_hardlinked_extra_paths=preexisting_hardlinks,
        inodes_with_external_links=external_link_inodes,
        current_owner_available_bytes=available, current_free_bytes_including_reserved=free,
        current_free_minus_available_bytes=reserve_gap,
        root_filesystem_type='ext4_per_read_only_mount_census',
        inode_ctime_link_count_preservation_possible=False,
        hash_revalidation_required_immediately_before_any_future_replacement=True,
        source_mutations=0, bytes_actually_reclaimed=0, groups=eligible)


if __name__ == '__main__':
    require(os.uname().nodename == 'ipp2-ovx-p6-09', 'original_node3_only')
    print(json.dumps(analyze(sys.stdin.buffer), sort_keys=True, indent=2))
