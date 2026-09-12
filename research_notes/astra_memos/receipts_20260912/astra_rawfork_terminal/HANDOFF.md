# Raw-wake fork terminal handoff — 2026-09-12

## Immediate result

All four first-ACT solve counts are **0/16**. Both trained packages have lower
native partial-score means than their matching no-write/OFF baselines. The
positive continuous difference-of-gains says lesson degrades less than sham,
not that either package improves on the original model.

| Cell | First-ACT solves | First-ACT native mean | ACTs | Native-best solves |
|---|---:|---:|---:|---:|
| lesson OFF | 0/16 | 0.1125 | 16 | 0/16 |
| lesson ON | 0/16 | 0.0475 | 16 | 0/16 |
| sham OFF | 0/16 | 0.1125 | 16 | 0/16 |
| sham ON | 0/16 | 0.010546875 | 16 | 0/16 |

- Solve-count difference-of-gains: **0/16**.
- Continuous ON-minus-OFF: lesson **−0.065**, sham **−0.101953125**.
- Continuous difference-of-gains / direct ON contrast: **+0.036953125**.
- All 64 first ACTs are measured; exactly one ACT per episode, zero later ACTs.
  Native-best means equal first-ACT means. No invalid/missing-first rescue or
  best-of-many rescue is involved.
- OFF first scores and complete raw generation output hashes agree per board.

This is one recipient initialization, unequal historical packages and a reused
development panel. No significance, parenting/G5/H1/H2/clean-lineage pass, or
general claim against parenting follows. It does not test a proposed no-write
parenting intervention; it supplies this raw-material write comparison only.

## Paths and immutable artifacts

All new local work is under `/tmp/astra_rawfork_terminal_20260912/`.

- `capsule.tgz`: all 137 captured nonweight run files, plus terminal observation,
  remote adapter rehash and run-file hash receipts. Weights excluded.
- Run root: `astra_P0_raw_wake_fork_seed0_20260912_attempt1/`.
- `analysis.json`: unchanged existing `organism_v6.parent_wake_fork_analysis`
  output, `OFFLINE_CAPTURE_BINDINGS_VALIDATED`, with remote rehash bound.
- `raw_endpoint_prompt_review.json`: separate raw trace/endpoint/prompt check.
- `terminal_receipt.json`: controller absence and cleanup evidence immediately
  before/after streaming capture.
- `remote_adapter_rehash.json`: exact lesson/sham adapter inventory rehashes.
- `run_file_sha256.json`: all captured run files match these remote digests.
- `remote_capture.py`, `inspect_raw.py`: exact local capture/check scripts;
  `capture.stderr.log` and status JSONs preserve capture/progress observations.

The separate, already-exported material remains at
`/tmp/astra_raw_wake_export_capture_20260912/astra_P0_raw_wake_export_20260912_attempt1`.
It is not duplicated into this terminal capsule; its bytes were bound through
plan/PREPARED and export inventory by the existing analyzer.

SHA256:

| Artifact | SHA256 |
|---|---|
| capsule.tgz | `3508c27cf9832f25c059d96b990ff285cf6011bad2714aa8e2d175ad8a368fd6` |
| analysis.json | `a5a9d752c39a22cd3edc2ba3de2d33d79e436b85b7a5885452cebb085bb0ecba` |
| remote_adapter_rehash.json | `565070cbc1f0eeb27f88345f2f980f3a754d4f6f8c52d2e028a0b77fdc3f8af5` |
| terminal_receipt.json | `9bd381819743d7f3cf7a93b8b851cbe79d30f1e69de2557c3c1f527d202c653d` |
| raw_endpoint_prompt_review.json | `07e500afab242e897ec182c496f2e234f513f2085db593771ad586e71975b99a` |

Analyzer SHA256 remains
`0c26b0d0d2b19fdc945727748d3bfa57f8060facb02f6d66b50bc050b1a47bb5`.
The original analyzer and native reducer were not modified.

## Raw endpoint and prompt binding checks

For all 64 canary observations, located the unique first wake request by native
episode/tick seed and paired its raw generation output by request index. Parsed
ACT text agrees exactly and in order with all raw ledger ACTs; their generation
receipts bind the same prompt/output SHA256, seed and 400-token wake budget.
First recorded ACT index, later-ACT list and zero-fill rules agree with the
existing analyzer output.

- **0/64** planned canary question-hash mismatches.
- **0/64** original-birth-prefix mismatches.
- **0/64** exact full-user-prompt mismatches against the saved native prompts
  for this panel in the earlier mini-Sudoku oracle source map. This is a prompt
  comparison reference only, not a claim that oracle targets trained these forks.
- No clock normalization or mismatch tolerance was applied.
- All wake calls use the recorded native 400-token / temperature 0.7 setup.

This is a raw trace/parser/ledger and prompt check, not new model inference,
retokenization, native-answer rescoring, independent puzzle enumeration or a
repeat source-formation judgment. Existing plan overlap metadata is retained:
source `rg/mini_sudoku/1189872` shares a solution with canary
`rg/mini_sudoku/1900061`; the earlier oracle dataset's four solution overlaps
must not be substituted for this raw-fork source overlap.

## Fits and dose limitations

| Arm | Steps | Input token passes | Supervised target passes | Historical teacher tokens | Fit seconds |
|---|---:|---:|---:|---:|---:|
| lesson | 96 | 95,241 | 12,867 | 203 | 87.1 |
| sham | 96 | 94,581 | 16,080 | 158 | 86.0 |

The existing analyzer binds plan, PREPARED, source export hashes, two actual
train manifests, adapter inventories, probe specs, native pair custody and
root/arm completion. Targets, masks and unequal token accounting remain as
declared. Both remote adapter payloads were freshly CPU-rehashed against their
exact probe inventories; local payloads remain absent:

- lesson `adapter_model.safetensors`:
  `62579058941c32296fd1cd204c0b72448dff29cde000777233677f4d4257f1b4`
- sham `adapter_model.safetensors`:
  `b14c451f31048d54623f0394fd2fb8a2d25dfa0596efed381cf68949a89c9b94`

The analysis correctly retains `REMOTE_WEIGHT_HASH_NOT_REHASHED_LOCALLY` while
binding the remote rehash receipt. Neither this receipt nor local pins claims
official model origin or historical GPU-loaded-state authentication.

## Completion, cleanup and reservation

- Controller 77998 launched **11:21:00.305540 UTC** on node3 GPU1.
- Root `COMPLETED.json`: **11:43:29.137797 UTC**, both lesson/sham arms complete;
  `FAILED.json` absent. Launch-to-terminal duration **22.4805376167 minutes**.
- Controller `/proc/77998` absent at **11:43:37.699556 UTC**, and again during
  capture at **11:43:38.728541** and **11:43:38.972302 UTC**.
- All four train/pair and all four native worker cleanup receipts have matching
  process PID, device1, `cleanup_error=null`, `owned_group_empty=true`,
  `gpu_processes_absent=true`, `reservation_release_verified=true`.

| Arm | Train PID | Pair PID | OFF worker PID | ON worker PID |
|---|---:|---:|---:|---:|
| lesson | 78120 | 78617 | 78620 | 79828 |
| sham | 81249 | 81724 | 81749 | 83013 |

Raw logs retain backend shutdown escalation and leaked-semaphore warnings.
Engine PID / logged SIGTERM-initiation UTC: lesson OFF 78938 / 11:27:22,
lesson ON 80140 / 11:31:13, sham OFF 82157 / 11:38:19,
sham ON 83337 / 11:42:33. Each reports
`[close_backend] escalated: killed 1 engine procs, freed=True`.
These are recorded backend cleanup events, not actions taken by this task.

No remaining capture/binding flags were found. Primary solves remain null and
both continuous absolute effects are negative, with the above package/dose
limitations. **No reservation release, launch or kill was performed.** Main
retains authority over GPU1 scheduling and any notebook/Git update. All remote
operations were read-only SSH; capture streamed over stdout without remote
staging files. No curl/wget, repo edits or Git commands were used.
