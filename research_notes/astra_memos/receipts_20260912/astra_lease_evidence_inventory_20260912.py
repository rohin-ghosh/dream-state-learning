"""Bounded read-only node1/node2 metadata inventory; no transfer or weight reads."""
import json
from pathlib import Path
import subprocess


REPO = Path('/data/home/rohing/dream-state')
REMOTE = r'''
import datetime, hashlib, json, os, stat
from pathlib import Path

home = Path.home()
node = NODE_ARGUMENT
root = home / ('v6_out' if node == 'node1' else 'mirror/node1_adapters_2026-09-12')
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
visits = 0

def children(path):
    global visits
    if not path.is_dir() or path.is_symlink():
        return []
    result = []
    with os.scandir(path) as entries:
        for entry in entries:
            visits += 1
            if visits > 30000 or len(result) >= 3000:
                raise ValueError('metadata entry budget exceeded')
            result.append(entry)
    return sorted(result, key=lambda entry: entry.name)

def names(path):
    return [entry.name for entry in children(path) if entry.is_dir(follow_symlinks=False)]

def info(path):
    try:
        value = path.lstat()
    except FileNotFoundError:
        return None
    return dict(bytes=value.st_size, mtime_ns=value.st_mtime_ns,
                mtime_utc=datetime.datetime.fromtimestamp(value.st_mtime, datetime.timezone.utc).isoformat(),
                regular=stat.S_ISREG(value.st_mode), symlink=stat.S_ISLNK(value.st_mode))

def metadata_counts(path):
    rows = []
    for entry in children(path):
        if entry.is_file(follow_symlinks=False) and Path(entry.name).suffix not in ('.safetensors', '.bin', '.pt', '.pth'):
            value = entry.stat(follow_symlinks=False)
            rows.append((entry.name, value.st_size, value.st_mtime_ns))
    return dict(files=len(rows), apparent_bytes=sum(row[1] for row in rows),
        newest_mtime_ns=max((row[2] for row in rows), default=None),
        after_archive_files=sum(row[2] > 1789169441042387061 for row in rows),
        after_adapter_mirror_files=sum(row[2] > 1789183020000000000 for row in rows))

top = names(root)
result = dict(node=node, started_utc=started, root=str(root.relative_to(home)), top_dirs=top,
              root_nonweight_files=metadata_counts(root), nonweight_files_depth2={}, pretests={}, selected={}, archive_manifests={})
for name in top:
    result['nonweight_files_depth2'][name] = metadata_counts(root/name)
for name in ('pretest_write_ab', 'pretest_write_ab_AC'):
    groups = names(root/name)
    result['pretests'][name] = {group: dict(adapters=names(root/name/group/'adapters'),
        metadata_dirs=names(root/name/group), metadata_at_group=metadata_counts(root/name/group)) for group in groups}
for name in ('RP_B_seed402', 'R3_B_seed500', 'R3_B_seed501', 'R4_B_seed605', 'R4_B_seed606',
             'astra_B0_slot_A_seed9100_20260912_attempt2', 'astra_B0_slot_B_seed9100_20260912_attempt2'):
    sleeps = [value for value in names(root/name) if value.startswith('sleep_')]
    selected = result['selected'][name] = dict(exists=(root/name).is_dir(), sleep_dirs=len(sleeps),
        last_sleep=sleeps[-1] if sleeps else None, ledger=info(root/name/'ledger.jsonl'))
    if sleeps:
        selected['last_adapter_weight_stat_only'] = info(root/name/sleeps[-1]/'adapter/adapter_model.safetensors')
        selected['last_adapter_done_stat_only'] = info(root/name/sleeps[-1]/'adapter/DONE')
for date in ('2026-09-11', '2026-09-12'):
    base = home/'archive' if node == 'node1' else home/'mirror'/('node1_receipts_'+date)
    filename = 'v6_out_receipts_'+date+'.tgz'
    manifest = base/(filename+'.sha256')
    if manifest.is_file() and not manifest.is_symlink():
        value = manifest.stat()
        if value.st_size > 65536:
            raise ValueError('hash-manifest size budget exceeded')
        payload = manifest.read_bytes()
        result['archive_manifests'][date] = dict(manifest_sha256=hashlib.sha256(payload).hexdigest(),
            records=payload.decode().splitlines(), archive_stat=info(base/filename), part_stat=info(base/(filename+'.part_aa')))
result['source_tree_dirs'] = names(home/'astra_sources')
result['native_v6_dirs'] = names(home/'v6_out') if node == 'node2' else top
result['finished_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
result['directory_entries_inspected'] = visits
print(json.dumps(result, sort_keys=True))
'''


def collect(node, wrapper):
    program = REMOTE.replace('NODE_ARGUMENT', repr(node))
    completed = subprocess.run(
        ['timeout', '70', 'bash', str(REPO/'gpu'/wrapper), '-o', 'StrictHostKeyChecking=yes',
         '-o', 'UpdateHostKeys=no', 'timeout 50 python3 -B -'],
        input=program, text=True, capture_output=True, timeout=75, check=True)
    if len(completed.stdout) > 1024 * 1024:
        raise ValueError('receipt output budget exceeded')
    return json.loads(completed.stdout)


def main():
    source = collect('node1', 'a40_ssh.sh')
    mirror = collect('node2', 'ovx_ssh.sh')
    missing = sorted(set(source['top_dirs']) - set(mirror['top_dirs']))
    summary = dict(receipt='N12-D', source=source, mirror=mirror,
        missing_mirror_top_dirs=missing, extra_mirror_top_dirs=sorted(set(mirror['top_dirs']) - set(source['top_dirs'])),
        missing_mirror_names_present_in_node2_native_v6=sorted(set(missing) & set(mirror['native_v6_dirs'])),
        note='Same basename in node2 native v6 is not verified node1 custody; no recursive weight traversal or payload hashing.')
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
