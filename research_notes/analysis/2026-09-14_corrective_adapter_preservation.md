# Corrective adapter preservation — 2026-09-14

## Outcome

**PASS.** Both complete train directories were copied from node2 using
`bash gpu/ovx_ssh.sh`, with every regular file verified against independent
pre-copy and post-copy remote SHA-256 manifests. No failures occurred.
Preservation ran from **2026-09-14 11:52:34 UTC to 11:52:40 UTC**; a subsequent
local archive checksum check also passed.

Source root:
`/tmp/astra_adult_cycle2_20260914_attempt1/CUE_REPLAY/corrective_sleep/`

Destination root:
`/data/home/rohing/dream-state/gpu_artifacts_local/astra_corrective_saved_adapters_20260914/`

The destination resolves onto the `/data` filesystem. No VM archives or
staging files were written under `/tmp`.

## Complete payload

| Arm | Files | Exact file bytes | Preserved train directory, relative to destination |
| --- | ---: | ---: | --- |
| CHILD_CORRECTIVE | 9 | 81,054,438 | `files/CHILD_CORRECTIVE/train/` |
| UNIFORM_REPLAY | 9 | 81,052,972 | `files/UNIFORM_REPLAY/train/` |
| Total | 18 | 162,107,410 | `files/` |

Each train directory contains `RESULT.json`, `REQUEST.json`,
`ADAPTER_PROVENANCE.json`, `LOSSES.jsonl`, `MASKS.json`,
`SELECTION_LAYOUT.json`, and the entire `adapter/` directory:
`README.md`, `adapter_config.json`, and `adapter_model.safetensors`.
Each adapter directory contains **80,798,775 bytes**; each model file contains
**80,792,096 bytes**. All source files and directory entries were included,
not just the explicitly requested metadata files.

The retained uncompressed archive `corrective_train_adapters.tar` contains
**162,129,920 bytes**. Extracted payload plus archive totals **324,237,330
logical bytes**, excluding manifests, verification logs, and the preservation
script. Logical byte counts are not filesystem allocated-block usage.

Archive SHA-256:
`d7b466ffc9e0a37907f10801d599887481b317c26d3c0afe0df681c6adfb2344`

## Exact adapter SHA-256 values

| Arm | Adapter file | SHA-256 |
| --- | --- | --- |
| CHILD_CORRECTIVE | `adapter_model.safetensors` | `0808585011b357f710f8d65d69e56d9b3be38ca6b465271b1e913cb66e0f760a` |
| CHILD_CORRECTIVE | `adapter_config.json` | `803a4af1b75a5ad648642b04d1950354e5e83d0981df5fcc05c2fc8b4ae8fd6c` |
| CHILD_CORRECTIVE | `README.md` | `1b1a685a0798f66ef71e870c1b87713d92814d912c47297127c119e751d3ea33` |
| UNIFORM_REPLAY | `adapter_model.safetensors` | `9c9a62f8fbf840081cc57cc0eab36e9c43d619f0df9ecad6d923572b672aa4ba` |
| UNIFORM_REPLAY | `adapter_config.json` | `f3d9febbe2424fdf7af5cb054aa49377c7f581be0da3b059670dbfa11b4e542d` |
| UNIFORM_REPLAY | `README.md` | `1b1a685a0798f66ef71e870c1b87713d92814d912c47297127c119e751d3ea33` |

## Verification evidence

All evidence paths below are relative to the destination root.

- `remote_before.json` and `remote_after.json`: complete sorted remote file
  inventories, per-file byte sizes and SHA-256 values, directory inventories,
  and file modification/change timestamps. The two snapshots are identical.
  Each hash operation also checked for size/timestamp changes during reading.
- `remote_before.sha256` and `remote_after.sha256`: complete 18-file remote
  SHA-256 manifests, suitable for `sha256sum --check --strict` from `files/`.
- `local_manifest.json` and `local_manifest.sha256`: independently computed
  local sizes and SHA-256 values for every extracted file. Exact relative file
  inventory, sizes, and hashes match the remote inventories. All three
  `.sha256` per-file manifests are byte-identical.
- `remote_before_local_check.txt` and `remote_after_local_check.txt`: each
  records **18/18 OK**, from two successful strict local checks against the
  corresponding remote manifests.
- `archive.sha256` and `archive_local_check.txt`: archive checksum and a
  successful local checksum check.
- `verification.json`: dated machine-readable PASS receipt, byte counts,
  archive hash, adapter hashes, and verification outcomes.
- `preserve.py`: the one-shot foreground preservation procedure used here.
  Outputs are created exclusively; rerunning is not a resume operation and
  must not be used to overwrite this evidence.

The archive was streamed directly from remote `tar` into a newly created
destination archive. Extraction rejected unexpected, duplicate, incorrectly
sized, or non-regular/non-directory entries; exact file and directory sets
matched the remote snapshot. Required RESULT, REQUEST, ADAPTER_PROVENANCE,
and adapter configuration JSON files parsed successfully without printing
their contents. No adapter loading or GPU execution was performed.

To recheck preserved file bytes without changing evidence, run these commands
from the destination root:

```bash
sha256sum --check --strict archive.sha256
(cd files && sha256sum --check --strict ../remote_before.sha256)
(cd files && sha256sum --check --strict ../remote_after.sha256)
diff -q remote_before.sha256 remote_after.sha256
diff -q remote_before.sha256 local_manifest.sha256
```

## Scope and handoff

Read repository `AGENTS.md` and `CLAUDE.md`; no nested files with those names
were found under the relevant local subtrees. This was bounded evidence
preservation, not a scientific or architectural change. Writes were confined
to the new destination directory and this new note. No existing files or
notebook entries were edited, deleted, overwritten, or reverted; no GPU
commands, experiment jobs, background jobs, or commits were initiated. Remote
commands only inspected, hashed, and streamed the requested evidence: no
remote archives, manifests, or other files were created. Transport stderr was
suppressed to avoid recording internal hosts or credentials; all transport
exit codes were checked. No curl, wget, or WebFetch was used.

Main owns the next experiment and integration. These checks establish
copy integrity and snapshot consistency only; they make no new scientific
claim and do not authorize or validate a future experiment.
