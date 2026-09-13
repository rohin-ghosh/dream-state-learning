# Q0 tar custody sidecar — September 13, 2026

**EDITSTOP. Actual R1 verdict: PASS_CUSTODY. Custody only, not native replay,
scientific acceptance, promotion, or reclassification. Main owns further
collection and all native/remote work.**

Only these four new durable `/tmp` artifacts are owned by this sidecar:

```text
eaffff4a235986ac4ff1f43768ec7bee58a640dd3ec77c9db76057bdd6e4969b  /tmp/astra_q0_tar_custody_20260913.py
8a805d14f09a580c3a2434d94870f94d4370e717f0b7d9b6f38dd187ee248a6a  /tmp/test_astra_q0_tar_custody_20260913.py
9e32dbc7f40778af0a6338a563a4b9c149ef5a8d987408ce2a971e6001a462f3  /tmp/astra_q0_R1_tar_verification_20260913.json
```

This handoff is `/tmp/astra_q0_tar_custody_handoff_20260913.md`; its hash is
returned separately to avoid recursive self-hashing. No source, test, receipt,
or input edits are pending.

## Actual R1 custody verification

The verifier streamed the complete existing archive once, without extraction,
from **2026-09-13 05:38:46.171860 UTC** through
**2026-09-13 05:38:53.326146 UTC**: **7.154370 seconds**, exit status **0**,
zero verification errors.

- Archive: `/data/home/rohing/dream-state/gpu_artifacts_local/q0_fulldose_20260913/R1_attempt1.tar`.
- Bytes streamed: **4,010,106,880**; all bytes, including tar headers and padding,
  contribute to the archive hash.
- Archive SHA256 matches Main's exact supplied expected value:
  `fa079949411b4e8da95ff3670d1f1bc1bea0594c6c999814cf4143168180ecab`.
- Single top directory: `q0_fulldose_R1_20260913_attempt1`.
- **17,565 sealed files** match their standalone-SEAL path-to-SHA256 entries;
  no missing sealed file and no additional unapproved regular file.
- **17,567 total regular files**: the sealed files plus exact `SEAL.json` and
  `FINALIZED.json`; no `FINALIZATION_ABORT.json` in this archive.
- Also observed: **41 directories**, **15,245 GNU long-name metadata headers**,
  zero PAX headers. Long-name metadata headers are not filesystem members.
- Regular payload bytes: **3,985,308,850**.
- Archive `SEAL.json` matches every supplied standalone byte, not just parsed
  JSON equivalence. Standalone input:
  `/tmp/astra_q0_fulldose_R1_seal_20260913.json`, **2,499,056 bytes**, SHA256
  `d3a7fa5b18b74821955d06c5e4b28c88fd92586479fbd6d284e6c2ba8885ab87`.
- `FINALIZED.json`: **232 bytes**, SHA256
  `ec1c4212ff93b5bfb4b20963a83dfc61c9ffa731944968b6f77568762d5e3eb0`;
  its `seal_sha256` binds the exact supplied/archive seal bytes.
- Complete-root sorted checksum stream: **2,481,506 bytes**, SHA256
  **`006c21d38b763953e5a59ef5641d3fe7683e3e32f71a84bb879c7de667a9db87`**,
  matching Fable's independent **17,567-file** expected value exactly.
- Open-file and pathname device/inode/size/mtime/ctime fingerprints match before
  and after for both inputs. Neither input was deleted, replaced, or written.

The independently supplied complete-root record was read locally from
`research_notes/analysis/2026-09-13_q0_fulldose_external_terminal_custody.md`:
R1 terminal/controller-absent observation **2026-09-13 05:30:34Z**. This sidecar
does not re-establish that remote observation; it verifies that the local
archive reproduces its exact published full-root digest. This includes the
later terminal eligibility files excluded by the older internal seal.

Actual command, run from `/data/home/rohing/dream-state`:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B /tmp/astra_q0_tar_custody_20260913.py \
  --archive /data/home/rohing/dream-state/gpu_artifacts_local/q0_fulldose_20260913/R1_attempt1.tar \
  --archive-sha256 fa079949411b4e8da95ff3670d1f1bc1bea0594c6c999814cf4143168180ecab \
  --seal /tmp/astra_q0_fulldose_R1_seal_20260913.json \
  --expected-root-stream 006c21d38b763953e5a59ef5641d3fe7683e3e32f71a84bb879c7de667a9db87 \
  --out /tmp/astra_q0_R1_tar_verification_20260913.json
```

The actual output path now exists and is intentionally exclusive; do not reuse
it. Rerunning against it refuses to overwrite, rather than replacing evidence.

## Full-root stream semantics

The local implementation reconstructs the bytes produced by this command inside
the terminal root, without extracting the archive or invoking that command on R1:

```sh
find . -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum
```

It strips the one archive top-directory component, sorts regular relative
pathnames in ASCII byte order, and feeds this exact line for every regular file
to the outer SHA256:

```text
<64-character lowercase payload SHA256><two spaces>./<relative pathname><LF>
```

The inventory includes `SEAL.json`, `FINALIZED.json`, and optional
`FINALIZATION_ABORT.json`, not only the sealed payload map. Printable ASCII
spaces, quotes, punctuation and leading hyphens are supported without shell
quoting. Backslashes, controls/newlines, and non-ASCII names are rejected rather
than guessing GNU `sha256sum` escaping or locale collation. All actual R1 names
satisfy these constraints, and its expected stream matches exactly. Synthetic
testing independently checks the real GNU pipeline with `LC_ALL=C`.

## Reusable CLI for Main's R0/R2 collections

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B /tmp/astra_q0_tar_custody_20260913.py \
  --archive "$ARCHIVE" \
  --archive-sha256 "$EXPECTED_ARCHIVE_SHA256" \
  --seal "$STANDALONE_SEAL" \
  --expected-root-stream "$INDEPENDENT_EXPECTED_ROOT_STREAM_SHA256" \
  --out "$NEW_EXCLUSIVE_RECEIPT"
```

`--archive`, `--archive-sha256` and `--seal` are required.
`--expected-root-stream` (alias `--expected-root-stream-sha256`) is optional for
reuse, but **was required and supplied for the actual R1 check**. Without it,
the complete-root digest is still computed but no independent full-root match
is claimed (`full_root_stream_matches_expected` is null).
Optional `--seal-sha256` additionally pins the standalone input. Omit `--out`
for JSON on stdout only. CLI exit is 0 for custody pass, 1 for verification
failure; malformed arguments or an existing/output-input collision are refused.

The verifier requires `SEAL.json` and `FINALIZED.json`, verifies the latter's
seal binding, and permits optional `FINALIZATION_ABORT.json`; if present, its
seal binding and any supplied `finalized_sha256` binding must also match.
The presence of FAILED/FINALIZED/ABORT never changes scientific classification.

## Synthetic CPU tests and validation

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B /tmp/test_astra_q0_tar_custody_20260913.py -v
```

**44 tests PASS in 0.208 seconds**, zero failures/errors/skips; exit 0.
Both Python files also compiled in memory in **0.007214 seconds** without
bytecode; `--help` was checked. No dependency installation was needed.

Coverage includes correct archive and payload hashes; full-root GNU pipeline
equivalence; changed terminal bytes detected by the external root digest;
missing/additional files; exact seal bytes versus equivalent JSON; required
FINALIZED and optional ABORT bindings; duplicate members and duplicate JSON
keys; unsafe/absolute/traversal/escaped paths; multiple roots; regular-file
parent conflicts; directory payloads; symlink/hardlink/device/FIFO/sparse and
unsupported members; GNU/PAX long names and USTAR prefixes; forbidden PAX size
overrides; bad checksum; truncation; missing end blocks; hidden concatenated
archives/nonzero trailers; unaligned trailers; chunked reads without extraction;
input symlinks/mutation detection; and exclusive output preservation.

Synthetic tests create and clean disposable `/tmp/q0_tar_custody_cpu_*`
fixtures. They do not extract the real archive. The only durable new files are
the four declared sidecar artifacts. No earlier custody test failure or real
verification failure occurred in this implementation sequence.

## Bounds and exclusions

- Raw uncompressed GNU/USTAR tar, GNU long-name extensions and bounded local
  PAX path/time/owner metadata are supported. Global PAX, sparse metadata, size
  overrides, chained metadata extensions and other unsupported types fail
  closed. Additional safe directories are allowed; extra regular files are not.
- Reads are at most 1 MiB per payload chunk; seal input is bounded to 64 MiB;
  terminal/path-extension metadata to 1 MiB. Path/hash maps remain in memory.
  No 4 GB payload buffer or extraction directory is created.
- Tar checksums, zero padding, two end blocks, and zero/aligned remainder are
  checked; archive SHA covers the complete byte stream, including the trailer.
- Normal filesystem read-atime effects are outside the unchanged-input
  fingerprint. Complete-root content hashing does not bind permissions,
  ownership, empty directories, or other filesystem metadata; the externally
  expected archive SHA separately binds the actual tar bytes.
- No remote/network/GPU/Git operations, source imports/execution, native replay,
  outcome scoring, collection, mutation, promotion, or reclassification. No
  repository edits. Main's R1 failure diagnosis remains Main's diagnosis; this
  successful custody check does not turn a failed readout into a success.

**EDITSTOP — final bytes pinned; R1 independent full-root custody verified.**
