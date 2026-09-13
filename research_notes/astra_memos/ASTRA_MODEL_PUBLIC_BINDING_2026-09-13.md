# Prospective public model/file binding

Status: **PUBLIC_REVISION_FILES_MATCHED_PROSPECTIVE_BINDING**.
Read-only verification completed2026-09-13T01:48:48.855692UTC on node3.
No model, adapter, historical plan, receipt, threshold or data lineage changed.

Public repository: `Qwen/Qwen2.5-7B-Instruct`.
Exact revision: `a09a35458c702b33eeacc393d103063234e8bc28`.
Main fetched that revision's official HTTPS model metadata with the user-approved
`python3 tools/webtext.py` route, including `blobs=true`. The complete response
identifies the exact repository and revision; it is10417bytes, not truncated.
No curl/wget retry, credential use, approval request or model download occurred.

Native verification streamed all14cached files without loading a model:

- Allfour safetensor shards match official LFS SHA256 values and sizes.
- The other ten files match official Git-blob SHA1 identifiers and sizes.
- A local SHA256map for all14files is retained for prospective runtime pinning.
- Each file's identity/size/timestamps stayed stable across its hash pass.
- The resulting local map equals the immutable map in the completed diagnostic
  plans. That is a post-hoc consistency observation, not a rewritten declaration.

The native check took13.233842seconds. Six CPU fixtures pass (plain Git blob,
LFS blob, wrong identity, changed content, wrong size, duplicate/traversal).
The fixture suite is not the native content evidence; the actual14-file check is.

## Exact evidence

All files are archived under `receipts_20260912/`:

| Artifact | SHA256 |
|---|---|
| `astra_qwen_official_metadata_20260913_attempt1.txt` | `8aebd0fc61d42917fedbf3c6dd08e39c36eac4c92478c88f2accabadae78de3b` |
| `astra_qwen_public_binding_20260913.py` | `11fe0f35f6883bbd8b572c04f4ab79dfa4eaf1b8f9b9824e1acbba5fe8c8b60a` |
| `astra_qwen_public_binding_receipt_20260913_attempt1.json` | `e87abf9c83845a32bb5df3828901dde1929e86a57fa0278158d4101b7df9a019` |

The receipt records the exact public metadata URL, repository, revision, local
snapshot path, all file hashes and comparison types. Preserve metadata and
receipt bytes; future preparations must bind/recheck their own local model
files rather than assuming every node has the same cache.

## Scope and use

This resolves prospective naming and content comparison for the checked node3
snapshot. It does not certify clean training data, isolate a scientific effect,
retroactively predeclare historical provenance, or satisfy the final C11 guard.
Historical `UNRESOLVED_LOCAL_HASHES_ONLY` receipts remain unchanged. Future Q0
or other claim-bearing plans may bind this public identity, receipt and local
file map explicitly, subject to their existing checks. Data contamination and
parent-visibility restrictions remain independent requirements.
