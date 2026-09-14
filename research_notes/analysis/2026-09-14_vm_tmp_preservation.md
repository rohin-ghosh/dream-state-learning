# VM /tmp preservation — BLOCKED, sources unchanged

Inspection: 2026-09-14 19:17:27–19:19:04 UTC. No migration performed.
Only this memo is written. No git/notebook, network, GPU, model, archive,
deletion, overwrite, process termination, or other /tmp operation occurred.

## Safety result

Both nominated sources are real directories, not source symlinks. The proposed
destination `gpu_artifacts_local/vm_tmp_preserved_20260914` was absent before
and after inspection and remains uncreated. Its parent resolves to
`/data/home/rohing/dream-state/gpu_artifacts_local` on the /data filesystem,
distinct from root-backed /tmp. Space was sufficient for the proposed move.

The unprivileged /proc scan covered 524 processes, excluding its own five
inspection ancestors to avoid matching the command containing the path names.
It found **zero visible references** in command lines, cwd, exe, or open fds.
However, that is NOT a complete inactivity certificate: cwd/exe/fd access was
denied for many protected processes, including four processes with this user's
UID 158984. For that UID alone, there were four cwd denials, four exe denials,
35 individual fd-link denials and three fd-directory denials. There were also
394 root-owned processes with denied cwd/exe/fd-directory inspection, plus
other service and user processes. No cmdline permission denial was reported.

A requested privileged read-only retry (`sudo -n python3 -B - ...`) was
rejected by the execution policy: **"Block privilege-escalation utilities
outright"**. It did not execute. No alternative privilege route was attempted.
The user explicitly required process-reference inspection and fail-closed
behavior, so both migrations were skipped. This is uncertainty about activity,
not evidence that either directory is active.

To resume, an appropriately authorized operator must establish complete
process-reference visibility and repeat the activity check immediately before
each move. Existing destination/source-symlink exclusions and before/after
inventory verification remain required. This memo is not approval to skip
protected processes or to copy/delete first and investigate later.

## Source inventories

Inventories were computed read-only after the move was blocked. They include
the root directory as `.`; regular-file SHA256/size; literal symlink target;
and each entry's permission mode, uid, gid and nanosecond mtime. Paths are
sorted relative to the source root. Each canonical compact sorted-key JSON
record ends in LF; the inventory SHA256 covers their concatenation. Atime,
inode/device and ctime are not included in the portable digest. Per-entry
mode/size/mtime/ctime were checked for drift while reading. These are source
snapshot fingerprints, not a claim of an atomic snapshot or completed transfer.
The complete inventory records were computed in memory, not stored separately;
the exact reproducible inventory command is retained below.

| Source | Directories including root | Regular files | Symlinks | Regular-file bytes | Allocated bytes (`du -sx -B1`) |
|---|---:|---:|---:|---:|---:|
| `/tmp/astra_preservation_cpu_20260912` | 1,065 | 15,220 | 4 | 732,781,580 | 776,298,496 |
| `/tmp/astra_additive_replay_native_20260913_attempt1` | 59 | 1,308 | 0 | 522,957,245 | 526,974,976 |

Inventory SHA256:

- preservation: `0229e2dd6667c4578671f7cc63b99ea2c82f838133d8d609bdab7fa4da53a0d1`
- additive replay: `9995f67dd4af1ff8c80db249410f055a990b1306abbc92fb52ccbea1709413e6`

The preservation environment's links are unchanged:

| Relative link | Literal target | Observed resolution |
|---|---|---|
| `bin/python` | `/usr/bin/python3` | `/usr/bin/python3.12` |
| `bin/python3` | `python` | `/usr/bin/python3.12` |
| `bin/python3.12` | `python` | `/usr/bin/python3.12` |
| `lib64` | `lib` | `/tmp/astra_preservation_cpu_20260912/lib` |

No special files or multiply linked regular files were found in the initial
walk. Both original logical paths still resolve to their original directories;
no replacement /tmp symlink was created. **After-migration inventories and
path-equivalence verification are not applicable: there was no migration.**

## Disk observations, not freed-space claims

| UTC | Filesystem | Used bytes | Available bytes | Use |
|---|---|---:|---:|---:|
| 19:17:27 | root / /tmp | 36,275,838,976 | 1,004,789,760 | 98% |
| 19:17:27 | /data | 234,704,076,800 | 30,920,409,088 | 89% |
| 19:19:04 | root / /tmp | 36,290,015,232 | 990,613,504 | 98% |
| 19:19:04 | /data | 235,866,554,368 | 29,758,062,592 | 89% |

Potential source allocation is 1,303,273,472 bytes combined. **Bytes freed by
this task: zero.** Concurrent system/worker changes prevent attributing the
disk deltas to this read-only inspection; they are not migration measurements.

## Commands executed

Working directory: `/data/home/rohing/dream-state`. Initial checks included:

```bash
date -u '+%Y-%m-%dT%H:%M:%SZ'
df -B1 / /tmp /data gpu_artifacts_local
ls -ld /tmp/astra_preservation_cpu_20260912 /tmp/astra_additive_replay_native_20260913_attempt1 gpu_artifacts_local
test ! -e gpu_artifacts_local/vm_tmp_preserved_20260914 && test ! -L gpu_artifacts_local/vm_tmp_preserved_20260914
find gpu_artifacts_local -maxdepth 1 -name AGENTS.md -print
readlink -f gpu_artifacts_local
du -sx -B1 /tmp/astra_preservation_cpu_20260912 /tmp/astra_additive_replay_native_20260913_attempt1
id
```

Executed process-reference scan (its subsequent directory-shape inspection is
summarized in the inventory and symlink tables):

```bash
python3 -B - <<'PY'
import os, pathlib, collections, json
roots = ('/tmp/astra_preservation_cpu_20260912','/tmp/astra_additive_replay_native_20260913_attempt1')
ancestors = set()
pid = os.getpid()
while pid > 1 and pid not in ancestors:
    ancestors.add(pid)
    try: pid = int(pathlib.Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()[1])
    except (OSError, ValueError): break
hits=[]; denied=collections.Counter(); processes=0
for process in pathlib.Path('/proc').iterdir():
    if not process.name.isdecimal() or int(process.name) in ancestors: continue
    processes += 1
    try: uid=process.stat().st_uid
    except FileNotFoundError: continue
    def check(kind, value):
        if any(root in value for root in roots): hits.append({'pid':process.name,'uid':uid,'kind':kind,'value':value[:1200]})
    for name in ('cwd','exe'):
        try: check(name, os.readlink(process/name))
        except PermissionError: denied[f'{uid}:{name}'] += 1
        except OSError: pass
    try: check('cmdline', (process/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace'))
    except PermissionError: denied[f'{uid}:cmdline'] += 1
    except OSError: pass
    try:
        for entry in (process/'fd').iterdir():
            try: check('fd', os.readlink(entry))
            except PermissionError: denied[f'{uid}:fd-link'] += 1
            except OSError: pass
    except PermissionError: denied[f'{uid}:fd-list'] += 1
    except OSError: pass
print(json.dumps({'processes':processes,'excluded_inspection_ancestor_pids':sorted(ancestors),'references':hits,'unreadable':dict(denied)},indent=2))
PY
```

Executed inventory command:

```bash
python3 -B - <<'PY'
import hashlib, json, os, pathlib, stat
for root_name in ('/tmp/astra_preservation_cpu_20260912','/tmp/astra_additive_replay_native_20260913_attempt1'):
    root=pathlib.Path(root_name)
    assert root.is_dir() and not root.is_symlink()
    paths=[root]
    for directory, subdirs, names in os.walk(root, followlinks=False):
        paths.extend(pathlib.Path(directory)/name for name in subdirs+names)
    records=[]; total_bytes=0; counts={'directory':0,'file':0,'symlink':0}; links=[]
    for path in sorted(paths, key=lambda value:value.relative_to(root).as_posix()):
        before=path.lstat()
        record={'path':path.relative_to(root).as_posix(),'mode':stat.S_IMODE(before.st_mode),'uid':before.st_uid,'gid':before.st_gid,'mtime_ns':before.st_mtime_ns}
        if stat.S_ISLNK(before.st_mode):
            record.update(type='symlink',target=os.readlink(path)); links.append({'path':record['path'],'target':record['target']})
        elif stat.S_ISDIR(before.st_mode): record.update(type='directory')
        elif stat.S_ISREG(before.st_mode):
            digest=hashlib.sha256()
            with path.open('rb') as stream:
                for chunk in iter(lambda:stream.read(1048576),b''): digest.update(chunk)
            record.update(type='file',size=before.st_size,sha256=digest.hexdigest())
            total_bytes+=before.st_size
        else: raise RuntimeError(f'Special file: {path}')
        after=path.lstat()
        assert (before.st_mode,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==(after.st_mode,after.st_size,after.st_mtime_ns,after.st_ctime_ns), str(path)
        counts[record['type']]+=1; records.append(record)
    inventory_bytes=''.join(json.dumps(record,sort_keys=True,separators=(',',':'))+'\n' for record in records).encode()
    print(json.dumps({'root':root_name,'entries':len(records),'counts':counts,'regular_file_bytes':total_bytes,'inventory_sha256':hashlib.sha256(inventory_bytes).hexdigest(),'symlinks':links},sort_keys=True))
PY
```

Final `date -u`, `df -B1 / /data`, destination-absence tests and `ls -ld` on
both sources confirmed the final observations above. No move/copy/link/remove
command was executed. The denied privileged attempt is deliberately not
presented as an executed scan or a successful safety check.
