# Q0 archive custody sidecar handoff — 2026-09-13

**EDITSTOP.** This sidecar checks archive byte custody only. Main must wait for the controller to exit, separately perform authoritative `native_replay`, and create the archive once. No live root, live outcome, or eventual native archive was read during this task.

## Owned files and identities

Only these three deliverable files were created/edited:

| File | SHA256 |
|---|---|
| `/tmp/astra_q0_archive_check_20260913.py` | `6535be1dbef4214168f79e773c1549cc3f3d1f7ff67cf0c17e99a655972f5d56` |
| `/tmp/test_astra_q0_archive_check_20260913.py` | `6914c41ccaabf311fca0fb3c22ead6f5a71e86fec8d9ca65f85a2a9363cf70ce` |
| `/tmp/astra_q0_archive_check_handoff_20260913.md` | Reported separately after writing; no self-referential hash. |

The frozen executor's `native_replay` was read only to align seal exclusions and witness bindings. There were no executor/test-source edits, Git operations, network requests, model/tokenizer/GPU operations, native operations, or live-outcome reads. Applicable `/tmp`/ancestor AGENTS paths were checked. Synthetic tests create and clean their own temporary archives; no native archive is extracted or accessed.

## CLI and API

```bash
python3 -B /tmp/astra_q0_archive_check_20260913.py /absolute/closed-root.tgz \
  --archive-sha256 CALLER_PINNED_ARCHIVE_SHA256 \
  --manifest-sha256 CALLER_PINNED_ROOT_MANIFEST_SHA256
```

Both hashes are required external expectations. The manifest pin is for the archived root's `manifest.json`, not `prepared.json` or a newly inferred value. `.tar`, `.tgz`, and `.tar.gz` are supported through magic-based gzip detection. Standard `tar -C ROOT -czf OUT .` names, including the root `./` directory and leading `./` file names, are supported.

Python API:

```python
validate_archive(path, archive_sha256=expected_archive, manifest_sha256=expected_manifest)
```

The API returns a custody summary or raises `CustodyError`. CLI success writes JSON to stdout and returns0; invalid/malformed custody writes error JSON to stderr and returns2. Missing arguments use argparse's exit2. A nonreportable failed native root can validly return custody success; custody success is not a scientific result.

## Checks and output

- Streams and hashes the complete archive bytes from the same open file used for parsing, checks the caller's archive SHA256, and checks descriptor size/identity/timestamps for changes during the read.
- Reads regular-file payloads in1MiB blocks, hashes every file, and counts file bytes without tensor deserialization or on-disk extraction. `TarFile.extractfile` is used only as an in-memory read stream; `extract` and `extractall` are never called.
- Rejects symbolic/hard links, special/sparse members, unsafe absolute/traversal/Windows/backslash/control-character paths, duplicate normalized members, and file/directory collisions. Duplicate directory entries are rejected too.
- Requires the caller-pinned `manifest.json` hash and the fixed native SEAL version/evidence kind/pending-finalization classification.
- Verifies exact `SEAL.files` equality against all observed regular-file hashes excluding only root `SEAL.json`, `FINALIZED.json`, and `FINALIZATION_ABORT.json`, as in frozen `native_replay`. Extra empty directories are not seal inventory entries, consistent with native file-only inventory.
- Validates `FINALIZED.seal_sha256` when present. When a finalization-abort witness exists, requires FINALIZED and verifies both its `seal_sha256` and `finalized_sha256` bindings. No witness completion is invented.
- Without FINALIZED, intact inventory custody may succeed but explicitly reports `NOT_SCIENTIFIC_READY_MISSING_FINAL_WITNESS`, a missing witness status, and a null finalization hash. An abort witness without FINALIZED fails custody because its hash chain cannot be checked.
- Returns archive/manifest/seal/witness hashes, canonical full and sealed file-inventory digests, file/sealed-file/directory counts, total regular-file bytes, archive bytes, compression, and presence flags for failure/abort evidence.
- Always returns `scientific_replay:false` and `scientific_ready:false`. With a bound witness, readiness is still `NOT_ASSESSED_AUTHORITATIVE_NATIVE_REPLAY_REQUIRED`.

Only the three custody JSON documents are deserialized. Duplicate JSON keys/nonfinite constants are rejected. Each captured custody JSON document is limited to32MiB as a parser-memory bound, not a scientific threshold. Hash maps/member names require memory proportional to inventory size; regular payloads are not retained. Concatenated tar/gzip streams are scanned rather than allowing appended files to hide after tar padding; gzip EOF/CRC validation is exercised.

## Explicit non-goals

This validator does not import Q0 or Torch, deserialize tensor contents, inspect raw scientific outputs, rerun numerical gates, check witness clock ordering/deadlines, verify model provenance, validate release/cleanup, authenticate a signer, or establish scientific eligibility. It does not replace `native_replay`. Caller-supplied pins must come from Main's custody workflow. It does not create, extract, repair, reseal, or alter the archive or root. No C11 or broader framework was added.

## Exact tests

Final command:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B /tmp/test_astra_q0_archive_check_20260913.py -v
```

**PASS:25 tests,0.105 seconds, zero failures/errors/skips; Python3.12.3, standard library only.** No packages were installed.

Coverage: normal tar/tgz and leading `./`; exact counts/bytes; failed root and finalization abort; missing witness; abort without completion; extra/missing members and missing seal/manifest; duplicate/normalized aliases; unsafe paths; links/special files; file/directory collisions in both orders; caller archive/manifest pin drift; sealed payload drift; seal identity/path/hash errors; final/abort witness binding drift; malformed/duplicate/nonfinite JSON; metadata bound; opaque multi-megabyte streaming with disk-extraction methods forbidden; truncated raw tar, truncated gzip, gzip CRC and compressed-stream corruption; concatenated archives hiding extra files; and CLI exit/JSON behavior.

These are synthetic custody fixtures only, not native replay, live-output review, numerical proof, or scientific acceptance.

**EDITSTOP — no further sidecar edits after this handoff.**
