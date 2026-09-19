# C2 epoch3: completed handoff, saved checkpoint verified, prefix latency BLOCKED

Prepared September 19, 2026, 02:03:55 UTC; independently archive/portability
verified at 02:05:10 UTC. This is a non-material performance repair, not a
new retention design, scientific claim, receiving authorization or deployment.

## Final report — real C2 prefix cost exceeds the guard

Main's actual C2 historical COMPLETE12902 + LEARN12903 cost receipt is
`../post_recovery_pair_receiving_checks_20260919/C2_COMPLETE_COST_1789784124.json`,
SHA256 `7bac3b3cd0f55d47bf4a6eabdf7d352b51046d9318877c4388afa231b6416702`.

| Actual C2 measurement | Result |
| --- | ---: |
| Retained prefix bytes hashed | 23,122,506,020 bytes (23.12 decimal GB) |
| Prefix hashing | 40.713863531 s |
| History restoration | 0.218709940 s |
| COMPLETE + one matching LEARN total | 41.689540984 s |
| Outer operation | 42.121742264 s |
| Required guard budget, supplied by Main | 30 s |
| Real saved history serialization | Exact-byte-equivalent |

**Latency is now measured and fails the 30-second budget, not merely pending.**
Prefix hashing alone exceeds the budget, despite the optimized restore taking
only0.219s and the tail containing only one LEARN record. The cache's real C2
history-byte equivalence is confirmed; it does not eliminate retained-prefix I/O.
This is a measured historical-cost comparison with the guard budget, not a claim
that an actual live guard dispatch was attempted or timed out.

The receipt ignores live head, does not verify current sidecars or acquire the
writer lock, and explicitly does not authorize handoff. Native remains unchanged;
no journal writes, GPU calls, signals or live adoption occurred. Saved checkpoint
12902 remains verified; the old-wall11502 refusal remains preserved.

**This C2 epoch3 closure/report task is complete; epoch3 is NOT dispatchable.**
Main is assigning a separate worker to prepare an immutable-prefix proof before
the handoff boundary, validate its fingerprints and read only the tail during
resume. That work is a separate source/authority/test change, not implemented,
approved or certified by this report. No prefix hashes or integrity checks are
waived, no timeout is raised, and current epoch3 source/tools are not edited.

## Completed handoff — September 19, 2026

Main has staged epoch3 on node5, passed actual-node `source`, `source_checks`
and `frontier_checks`, and now verified a current-wall-compatible **saved** C2
checkpoint with explicit selection:

- COMPLETE **12902**, SHA256
  `4dbee358fe5cfd59b6440633e07142bd1d82ce70572c00602910a52e74d857ed`.
- Optimizer steps **8588**; checkpoint checker elapsed **2.924733274 s**
  (outer operation **3.324284159 s**).
- Saved adapter, optimizer, working state and RNG payload checks pass. Saved
  CUDA RNG is validated as CPU tensor bytes, not by GPU restoration.
- Receipt: `../post_recovery_pair_receiving_checks_20260919/C2_CURRENT_CHECKPOINT_CPU_1789783807.json`,
  SHA256 `37f757a96774dbbe69c5a028418c074c263e25d849d1e59b04a496bfa41c2851`.
- Receipt status: `ACTUAL_C2_CHECKPOINT_CPU_VERIFIED_NOT_CURRENT_HANDOFF`.
  Its observed head was **12961, UPDATE**, not the selected COMPLETE boundary.
  Main reports native1139778 unchanged; receipt confirms native unchanged,
  no GPU calls, signals or live adoption.

Thus saved-checkpoint CPU validation is complete; **current-tail stability,
full-prefix/history timing and live handoff are not validated by this receipt**.
The separate cost receipt in the final report now measures actual C2 timing
and establishes the prefix-latency blocker. Main owns the separate prefix-proof
work and operational receiving gates; this worker performs no redundant remote
checks. Exact handoff status and artifact pins are in `EPOCH3_HANDOFF_COMPLETE.json`.

The original default COMPLETE11502 failure remains preserved and unverified.
Epoch2 and sealed epoch3 source/tools/controls/archive are unchanged. Historical
bundled default commands are not silently rewritten: any checkpoint invocation
must explicitly select the intended authentic index and hash.

## Historical failed default — September 19, 2026, 02:09:15 UTC

Main reports successful node5 epoch3 staging with the same 184 source pins and
native1139778 unchanged. Actual-node `source`, `source_checks` and
`frontier_checks` pass in
`../post_recovery_pair_receiving_checks_20260919/C2_EPOCH3_CPU_1789783755.json`
(SHA256 `e6a6323568102c2a6f0ef5c0c5119fe178fa6cc7cd22e0e8154bdbe5e91d1d1d`).

**Default historical COMPLETE11502 is NOT current-wall-compatible and is NOT
a verified checkpoint.** The checkpoint command returns1 with
`same_deadline_no_wall_extension` in `boundary.validate_records`, before the
saved adapter/optimizer/RNG validation. Main identifies its saved deadline as
predating the authorized wall bound1789927200. The outer diagnostic wrapper's
returncode0 does not mean the checkpoint check passed.

At that observation Main was selecting a saved COMPLETE with the current bound
for an explicit `--complete-index` / `--complete-sha256` check. The successful
12902 result is recorded above; the 11502 failure is not erased or reclassified.
No invariant is relaxed and this worker performs no duplicate remote action.
The exact original wall receipt, current-boundary/latency proof and downstream
guard/r188/parent/bridge gates remain required. The historical failure-only
observation remains in `EPOCH3_NODE_CHECKPOINT_STATUS.json`.
The node receipt reports no live adoption, GPU calls or native signals.
Epoch2 and sealed epoch3 source/tools/controls/archive remain unchanged;
bundled default11502 commands are preserved historical artifacts, not a
recommended or verified current-wall checkpoint invocation.

## Main integration artifacts

All paths in this section are relative to this worker directory.

- Immutable source: `prepared_epoch3_v1/C2/epoch3/source/` — 184 Python files
  plus original `context/R153_STARTUP.md`; files0444/directories0555.
- Exact staging declaration: `prepared_epoch3_v1/C2/epoch3/EPOCH3_SOURCE.json`.
  Contains every old-live/epoch1/epoch2/epoch3 pin, exact per-file origins, delta
  maps, unchanged historical life identity, helper/test pins and plan hash.
- Minimal patch: `prepared_epoch3_v1/C2/epoch3/FRONTIER.patch`.
- Portable archive: `prepared_epoch3_v1/C2_EPOCH3_BUNDLE.tar.gz` (786119 bytes).
- Source-specific node argv: `prepared_epoch3_v1/C2/epoch3/CPU_INVOCATIONS.json`.
- Results: `prepared_epoch3_v1/C2/epoch3/cpu/LOCAL_SOURCE_CPU.json`,
  `prepared_epoch3_v1/C2/epoch3/cpu/FRONTIER_CPU.json`,
  `prepared_epoch3_v1/C2/epoch3/cpu/SOURCE_VERIFY.json`.
- Final verification: `EPOCH3_VALIDATION.json`; preparation tests:
  `epoch3_tools/TESTS.log`; selected summary: `prepared_epoch3_v1/READY.json`.
- Reproducible builder: `epoch3_tools/prepare_epoch3.py`; archive/portable
  verifier: `epoch3_tools/verify_bundle.py`. Both refuse existing output paths.

Manifest SHA256:
`b3cd913e0254c98eb5eb90d77f75e61b91c2fb591c9b9b5efcb15255fffdd5c8`

Archive SHA256:
`c5b3f00293ca9cac28f534d8057d58a906e44b90bfc61584b7afe892b7d94f7e`

Final verification SHA256:
`1b0f28042be0eb801e6bfea0824fed5aa2e3e894e6bde847e4d784ea1a50e815`

## Exact change and preservation

Only `organism_v6/orch_r124_train_history.py` differs from sealed epoch2:

- Before: `ec7ecd7ebf395885606e7b500a47baedd11172a4c46e23b8d05d569dc8fac1d3`.
- After: `8d44b45941228b229340a1546d3bf984965b0f9d2acfab12967c829d48f16315`.
- Main's exact `frontier_port.py::port(bytes)`, four seams, source hash
  `551aaf3eabcc1aef13c44830d3790b63a1ad0ce043c7b39b41e051b6d21cea79`.
  Applied using `apply_patch`; reversing all four seams reproduces epoch2 bytes.

Five changed filenames versus old live; three deltas versus epoch1; one versus
epoch2. The historical two-entry epoch1-to-epoch2 map is retained separately.
The entire local `prepared_epoch2_v2` tree, including archive, tools, controls,
receipts and permissions, was hashed before and after and is unchanged.
Epoch1, current native, old r188, bridge, guard, journal and checkpoint-tail
reader were not edited. No Main-owned root history or pair source was edited.

## CPU evidence: source-specific, not live-checkpoint evidence

### Subsequent Main CLI-only helper fix

At 02:06:47 UTC Main's mutable `frontier_port.py` hash became
`a40e239403f9f426e86c364a075486281cf6c5b7986f6df1877faef21d7a1fb5`.
Epoch3 already preserves the original `551aaf...` helper bytes at
`prepared_epoch3_v1/C2/epoch3/tools/frontier_port.py`, mode0444, with a full
`helper_pins` entry and the same bytes inside the verified archive.
`frontier_port_origin` is the historical input location, not a runtime dependency.
The two versions' `port` function ASTs and exact C2 output bytes were compared
and match. Only the CLI output-opening order changed.

The original CLI is a provenance snapshot, not a supported bundle entry point:
do not use it to write an output. This builder invokes `port(bytes)` in memory,
validates its exact output/inverse, then uses `apply_patch`; it never invoked
that CLI. The builder rejects a changed mutable helper before creating output;
any rebuild must use the pinned snapshot, not silently accept a new helper hash.
No sealed epoch2/epoch3 source, helper, manifest or archive was rewritten.

**176 tests pass**: 36 exact-source retention/receiving checks (17 retention,
5 existing, 14 integration), 124 pinned history/stream/journal regressions,
4 additional actual-epoch2-preimage parity checks, and 12 preparer checks.
The frontier suite reports 199 subtests. There are no skips or failures.
Both actual-source suites (36 + 128) pass again from a separately extracted
bundle; these repeated runs are not added to the unique test count.

The parity checks cover exact serialized checkpoint bytes, compaction,
retained parents, evictions, restoration in both directions, every prefix
digest, tamper refusal and independent deepcopy. Loaded source-module origins
are pinned to C2, not the working repository. Synthetic tests do not prove
the actual C2 checkpoint, optimizer/RNG, current sidecars or real latency.

Main's additional receipt is
`../post_recovery_pair_receiving_checks_20260919/TEST_RECEIPT_1789783461.json`,
SHA256 `e46ba08937aa0194fe8ae937423c58f88680f93beec2c944415fb57115f78521`.
It reports 9 worker + 124 core tests passing, no live adoption, and binds the
same port hash and history-test snapshot. Its root history hash is `c6e241...`,
not this C2-specific `8d44b4...` postimage: it supports the port provenance but
does not replace the source-specific C2 receipts. Its known broad-suite
`native.sleep` mock failure is identified as preexisting there; no unrelated
test or native source was changed by this worker.

## Original checkpoint-tail latency risk

The original pair current-tail scans timed out at 90 seconds. Profiling found
two separate costs: hashing every retained journal-prefix byte, then repeatedly
restoring history and recomputing canonical frontiers for subsequent tail
transitions. A historical COMPLETE with 159 later records amplified the latter.
Choosing COMPLETE plus its matching LEARN avoided that long transition replay,
but still paid the prefix-hash and history-restore costs.

Main's **historical pair-only** measurements:

| Life | Original COMPLETE+LEARN total | Cached total | Cached prefix hashing |
| --- | ---: | ---: | ---: |
| Frozen sibling | 37.0822 s | 18.9989 s | 18.3873 s |
| Learner | 14.7683 s | 8.0650 s | 7.7989 s |

Exact receipts and their hashes are in `EPOCH3_SUPPORTING_RECEIPTS.json`.
Both accelerated receipts explicitly ignore live head, do not verify current
sidecars, do not acquire the writer lock, and do not authorize native handoff.
**These are not C2 measurements.** Epoch3 removes the repeated frontier
serialization, not full-prefix I/O; the unchanged reader is still not O(tail).
A live writer can leave the selected COMPLETE boundary while verification is
running. C2 saved checkpoint12902 passes CPU validation, but current-boundary
stability remains unproven. The later real C2 full-prefix cost is41.690s,
exceeding Main's30s guard budget; its earlier2.925s checkpoint probe was not a
full-prefix/history timing result. No timeout bypass, integrity relaxation or
scanner replacement is included. Main owns the separately assigned repair.

## Concrete remaining preflight blockers

1. Main reports completed staging at
   `/localhome/local-rohing/orch_retention_20260919/C2/epoch3/source`; actual-node
   source verification and synthetic suites pass. Exact receiving source
   authority, fresh native boot/PID/start/UID/argv and uid2524 access evidence
   are still separate preflight obligations, not implied by the CPU suites.
2. Supply the exact original WALL_EXTENDED record and intent. Authorization
   in a plan is insufficient. Hard end **1789927200** and lease1789948800 stay
   fixed; neither local readiness nor the expired eval lease permits dispatch.
3. **Reader-latency gate fails:** measured C2 COMPLETE12902 + one LEARN cost
   41.690s against30s; prefix hashing alone took40.714s. Main's separately
   assigned immutable-prefix proof/fingerprint/tail-read work must satisfy its
   own integrity and latency tests before any new receiving closure is used.
   Saved checkpoint12902 has passed adapter/optimizer/RNG/state CPU validation;
   still bind a current COMPLETE+matching LEARN and verify current sidecars and
   checkpoint/tail/guard evidence. The successful saved-checkpoint probe observed
   UPDATE head12961, not a reserved current COMPLETE boundary.
   The helper's default COMPLETE11502 failed the current-wall invariant and is
   NOT verified. Explicit selections need both authentic index and SHA256;
   hard end1789927200 remains unchanged.
4. Main must provide its actual source-bound receiving guard/route receipt,
   parent delivery fence, zero in-flight work, preserved owner ledgers, old
   bridge/parent rebinding readiness and post-LOADED explicit owner adoption.
5. Only the unchanged original r188 route is supported:
   `/localhome/local-rohing/v2/venv/bin/python -B -m gpu.r188_node5_confinement dispatch --config <Main actual receiving GUARD>`.
   It still requires full-source RECEIVING_CPU.json, once-only outer claim,
   confinement probe and fresh privileged admission; uid/gid2524,
   NoNewPrivileges, empty capabilities and GPU1/control-device restriction.
   A direct guard dispatch or service-policy change is not equivalent.

This worker performed no remote staging, live activation, service-manager
invocation, signal, dispatch, parent delivery, git commit or push. Main's later
node staging/CPU observation is recorded separately above.
