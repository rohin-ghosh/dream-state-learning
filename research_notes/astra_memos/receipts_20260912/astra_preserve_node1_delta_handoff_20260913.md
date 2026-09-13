# Node1 delta custody helper — CPU-only handoff

Prepared 2026-09-13 UTC. Main owns native invocation, source staging, archive transfer, and custody acceptance. **No remote actions, GPU actions, Git operations, repo edits, real archive creation, or source transfer were performed for this implementation.** Only the three requested implementation/handoff files persist; synthetic tests used and cleaned their own temporary fixture directories.

## Delivered files and validation

| File | SHA256 |
|---|---|
| `/tmp/astra_preserve_node1_delta_20260913.py` | `71779e4530b5d6a1ae2844f9e791a549c5f8e44c5b70e2363c4b252c09ad1a26` |
| `/tmp/test_astra_preserve_node1_delta_20260913.py` | `c96414a58c738f639125a701382c5080da330a23fca5aa6418aee107194752c3` |

Command actually executed locally:

```bash
python3 -B /tmp/test_astra_preserve_node1_delta_20260913.py -v
```

**38 tests PASS, 0.211s.** Production roster validation, without reading any native source, also passed at **2026-09-13T04:42:51.651964Z**. No third-party packages, tensor deserialization, extraction, GPU access, or model imports. Linux/Python 3.12 is the tested environment; the helper uses standard-library APIs and Linux `O_NOFOLLOW`/directory file descriptors. Keep `-B` to avoid bytecode writes.

The suite covers exact-member round trip; exact embedded roster bytes; production count enforcement; wrong roster/archive SHA pins; size, nanosecond mtime, content and mode changes; same-size/same-mtime content changes; changed inode; symlink leaf/parent/home/input/output paths; FIFO rejection without blocking; traversal/absolute/noncanonical paths; duplicate roster/tar members; corrupted snapshot manifest digest; missing members; archive symlink/hardlink entries; payload corruption; truncation; trailing nonzero bytes; exclusive-create races; old archive/receipt preservation; mutation during/after packing; and injected archive write failure retaining the partial file and error receipt.

## Exact scope and fixed input

Externally pinned input, unchanged:

```text
/tmp/astra_node1_preservation_delta_20260913.json
SHA256 5e7ad05a3f1714d13f8977abb6b1e15c0d862733255f06b914a6b37424b48ffb
433009 bytes
```

Use this literal accepted pin; **do not replace it with a newly computed pin merely to accommodate changed input**. The CLI validates the pin before parsing the roster. It checks schema/status, source-stat bindings, stable-read flags, unique normalized paths, the two snapshot member-manifest hashes, summary counts, and exact production counts.

- Exactly **348 `v6_out/` files**: 346 missing plus 2 changed files from the accepted inventory.
- Exactly **419 `astra_sources/` files**, under the two inventoried source identities.
- **767 payload files**, totaling **2,412,686,907 bytes**.
- Plus the **unchanged 433,009-byte roster** at `custody/astra_node1_preservation_delta_20260913.json`.
- **768 logical regular tar members**. PAX headers may represent long paths; they are metadata, not extra payload files. There are no directory entries, external receipt entries, unlisted files, or source discovery/globbing at pack time.
- Plain, **uncompressed `.tar`**, not gzip. Estimated production archive size with this helper: **2,413,762,560 bytes**; use the actual successful pack receipt as authoritative.

This is **delta custody only**, not a restore or bytewise certification of the 96 GB source tree, the 94.6 GB full mirror, or any old receipt archive. The 7 previously missing adapter files are included as opaque bytes, alongside the other selected files. No model/public-binding receipt is implicitly added to the archive; its only roster is this explicitly pinned delta inventory.

## Pack behavior

Source roots are resolved from an **explicit `--home`** using only the roster's checked relative paths. The absolute historical `root` fields in the JSON do not redirect source reads.

1. Validate roster and require both output names to be new. Output parent directories must already exist; the helper never creates directories.
2. Read and hash every source payload before opening the archive. Require exact pinned size, mtime in nanoseconds, SHA256 and permission mode. Reject nonregular files and symlinks at all path components. Capture device/inode/ctime/mode/size/mtime identity for each source.
3. Open the new archive and compact external receipt using `O_CREAT|O_EXCL|O_NOFOLLOW`, mode0600. No overwrite, append-to-old-archive, rename, unlink, or cleanup of previous files.
4. Stream roster and selected payloads into the tar. Hash source bytes again as they enter each member; compare file identity before and after each stream.
5. Flush/fsync the archive, then re-read/hash **every source payload again**, retaining the pre-pack identity binding. A changed earlier member therefore fails the postcheck even if its already-packed bytes are intact.
6. Write/fsync a compact external `DELTA_PACKED` receipt containing the literal roster pin, archive SHA256 and byte size, counts, scope, UTC times, and the three successful source-check stages.

Pack performs about **three full reads of the selected 2.413 GB payload**, not a full-mirror scan. It uses bounded streaming buffers plus the small roster. Tar headers retain whole-second mtimes; the embedded exact roster preserves the authoritative nanosecond mtimes. Source mode and full nanosecond mtime are checked, not rounded, during packing.

The helper does not intentionally write source contents or source-tree entries. OS-managed read-atime behavior is filesystem policy. Archive and receipt outputs must be outside the two source trees; receipt paths containing `v6_out` or `astra_sources` components are rejected even during off-node verification. All opened parent paths must be real directories, not symlinks.

## Invocation templates — Main only; not executed

After Main stages the hash-bound helper and unchanged roster to node1, choose genuinely unused archive/receipt names and an already-existing destination parent outside the source trees. Example using the existing home directory:

```bash
python3 -B /tmp/astra_preserve_node1_delta_20260913.py pack \
  --home /localhome/local-rohing \
  --roster /tmp/astra_node1_preservation_delta_20260913.json \
  --roster-sha256 5e7ad05a3f1714d13f8977abb6b1e15c0d862733255f06b914a6b37424b48ffb \
  --archive /localhome/local-rohing/astra_node1_delta_20260913_attempt1.tar \
  --receipt /localhome/local-rohing/astra_node1_delta_20260913_attempt1.pack.json
```

This template names new outputs, not a reservation or proof that those names remain unused. The helper enforces exclusivity at open time. A failed attempt is never overwritten on retry: Main chooses another new name. Do not auto-refresh source timestamps, rewrite the roster, or change the accepted roster pin to make an inconsistency pass.

Before transfer, Main records the successful pack receipt from the producing node. Accept only `status=DELTA_PACKED`, the exact accepted roster pin, `payload_files=767`, `tar_members=768`, and successful source pre/stream/post checks. Record its **archive SHA256** through the trusted handoff; do not derive the expected transfer pin from the received archive itself.

After Main transfers the archive, unchanged roster, and helper to the VM/node2, verification uses **no source home or original source files**:

```bash
python3 -B /tmp/astra_preserve_node1_delta_20260913.py verify \
  --roster /tmp/astra_node1_preservation_delta_20260913.json \
  --roster-sha256 5e7ad05a3f1714d13f8977abb6b1e15c0d862733255f06b914a6b37424b48ffb \
  --archive /tmp/astra_node1_delta_20260913_attempt1.tar \
  --archive-sha256 '<exact archive_sha256 from trusted DELTA_PACKED receipt>' \
  --receipt /tmp/astra_node1_delta_20260913_attempt1.verify.json
```

Replace the archive location if Main transfers elsewhere and replace the explicit SHA placeholder. **`--receipt` on verify is a NEW output receipt**, not the pack receipt. Do not reuse or overwrite the producing receipt or a prior verify receipt.

Verify streams the complete tar, validates all member names/types/sizes/modes/whole-second header mtimes, checks every full payload SHA256 against the externally pinned roster, checks the exact embedded roster bytes by its accepted SHA256, rejects duplicate/missing/unexpected members and nonzero trailing data, checks archive stability while reading, and compares the complete raw archive SHA256 with Main's supplied transfer pin. No filesystem extraction is performed: the `tarfile.extractfile` API is used only as a read stream. It never calls filesystem `extract`/`extractall` or loads tensor formats.

Successful verification produces `status=DELTA_VERIFIED`, `full_member_bytes_verified=true`, `extraction_performed=false`, `source_accessed=false`, and matching archive/roster pins. Stdout returns the same compact result; CLI exit0 means success, exit1 means an operational/integrity error (argparse usage errors use exit2).

## Failure preservation and boundaries

- Preflight failure creates no archive or receipt. Existing artifacts remain untouched.
- Failure after archive/receipt creation retains the archive, even when partial or structurally complete but rejected by the postcheck. When the new receipt is writable, it records `ERROR_PARTIAL_ARCHIVE_PRESERVED`. Verification failures record `ERROR_ARCHIVE_PRESERVED` and never modify the archive.
- An exclusive-create race for the receipt after the archive was opened can leave an empty archive plus a stderr error, without a new error receipt. It cannot overwrite the competing receipt. This is preferable to deleting evidence or overwriting another actor's file.
- Storage failure may also prevent an error receipt from being written; abrupt process death cannot guarantee any receipt. Empty/missing/error receipts are **not success**, even if the archive can be listed. The CLI surfaces errors and never deletes partial archives. Only successful pins/receipts plus independent off-node streaming verification establish this bounded custody result.
- Pre/stream/post checks are not an atomic filesystem snapshot or a writer lock. They detect changed size/mtime/hash and changed source identity during observed reads; they cannot guarantee the source stays unchanged after the final check or defeat a privileged adversarial writer. Main controls concurrent source writers and separately handles any subsequent deltas.
- The CLI always requires exactly348+419 payloads. Synthetic tests call the Python API with reduced fixture counts; there is **no CLI count-relaxation flag**.
- No native pack, transfer, off-node verification, recovery/extraction, full-mirror certification, lease change, or GPU-slot reservation has happened as part of this implementation. Main performs those separately. No formal C11 machinery is introduced.
