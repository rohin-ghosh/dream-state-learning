# Node2 — C0 / Astra7 recoverability inventory

**Read-only cut: 2026-09-19 13:38:36 UTC. No restart, reset, tail dropping, remote mutation or large VM copy.**

## Bottom line

Both recorded natives remain down, and both **actually failed with ENOSPC (errno28)**, not a planned withdrawal. C0 failed saving its optimizer/RNG checkpoint; Astra7 failed publishing an UPDATE intent. A durable previous checkpoint exists for each, with all three pending rows still represented in the retained journal evidence. **An honest checkpoint-plus-retained-state restart is plausible but is not installed or launch-ready. Exact unsaved resident/RNG continuity is not established.**

**New concrete integration blocker:** both exact receiving PLAN files contain non-null `authorized_wall_extension` dictionaries. The unchanged tested candidate rejects either plan at `interrupted_sleep.py:32` (`neither_deadline_extension_nor_preupdate_spoof`). Do not silently remove this field or change the wall to make a test pass.

## What failed and what survives

| Life | Last durable checkpoint | Unfinished sleep | Persisted stage/source linkage | Unsaved UPDATE receipts |
|---|---|---|---|---|
| C0 | sleep145; COMPLETE 6631; optimizer 8412 | cycle146; SLEEP_REQUEST 6660; 3 rows | THINK 6640 / ACT 6647 / LEARN 6656 | 48 recorded, through 8460 |
| Astra7 | sleep146; COMPLETE 7750; optimizer 9644 | cycle147; SLEEP_REQUEST 7776; 3 rows | THINK 7756 / ACT 7763 / LEARN 7772 | 29 recorded, through 9673 |

- **C0:** current native log contains OSError/errno28 in `torch.save`, followed by a serialization-position RuntimeError. Exit code1 / `no_retry=true` is recorded at 2026-09-19 02:44:27 UTC. Failed `sleep_000146` has an 80,792,096-byte adapter and **86,966,272-byte truncated optimizer/RNG file**, but **no COMMIT**. Neither is an approved restore substitute for the durable pair. Journal head6710 is unchanged.
- **Astra7:** current native log contains OSError/errno28 in journal `_publish`, reached from the UPDATE callback. Head7807 is unchanged; **`00000000000000007808.intent.json.partial` is zero bytes**, and `sleep_000147` does not exist. EXIT/FAILED/OUTER_EXIT receipts are also zero-byte files; their numeric exit status is unknown. The log still establishes ENOSPC directly.
- C0's three rows each have16 recorded presentations. Astra7's rows have **10 / 10 / 9** recorded presentations, not a checkpointed partially trained model. All77 selected UPDATE records were canonically hash-verified in this read.
- Last successful R184_LEARN_COMPLETE records are C0 **6632** and Astra7 **7751**. The later LEARN-stage records above are child-stage outputs, **not successful sleep completion**. Recovery must complete that pending sleep before treating either life as being at a fresh THINK boundary.
- Prior authenticated pending-state projections retain **444 rows / frontier441** for C0 and **453 / frontier450** for Astra7. Current eligibility records confirm the same three row hashes and no semantic exclusions. Full row hashes, stage record hashes and saved-state digests are in `INVENTORY.json`; no child text is copied here.

## Checkpoint and RNG evidence

Previous full binary verification was at **2026-09-19 03:53:57 UTC**. This cut recomputed both small COMMIT hashes, matched them to that receipt, and checked current payload paths/sizes. **It did not rehash or deserialize the roughly485 MB of adapter/optimizer payloads**, so these are the last binary-verified durable checkpoints, not a new tensor-restore proof.

### C0
- Checkpoint directory: `/localhome/local-rohing/orch_r216_C0_20260918_attempt2/raw/checkpoints/sleep_000145`.
- COMMIT file SHA-256, recomputed now: `3d5b50c9b740733bdc3fcea0537c7c4079066013475733b407c9c2b53ed71347`.
- Adapter file SHA-256, prior binary audit: `2bfe611993e9a7189f8d93736b3e75d613e7572cfcd01f85c4d7ba6652f01f20`.
- Optimizer/RNG file SHA-256, prior binary audit: `6e554cdf084ac3a9141f587e594361befb6bedae41ab50d0a9ce8e49a56f4ac4`.

### Astra7
- Checkpoint directory: `/localhome/local-rohing/orch_r229_Astra7_20260918/raw/checkpoints/sleep_000146`.
- COMMIT file SHA-256, recomputed now: `38bd10c74ba850703e9d033c193e106d511353d6c76c59c37671235a28084ee7`.
- Adapter file SHA-256, prior binary audit: `1012b3e4c15257de9d9033cca0265993f3a03b05310f926d6d680456fe8af415`.
- Optimizer/RNG file SHA-256, prior binary audit: `a52a7b1723650eff309216fe7e5dd67fcc08819e4f229d0e45841641035d3104`.

The bound original `NativeChild` restores parameter-ordered optimizer state/count plus Python RNG, CPU torch RNG and all CUDA RNG states from `optimizer_rng.pt` (`gpu/orch_r125_continual_native.py:356`). Those states are from the durable checkpoint, **before intervening generation/learning work**. UPDATE receipts contain scalars/source identities, not replacement tensor/RNG state. The original optimizer mutates before UPDATE publication (`:632`–`:635`), so Astra7's29 logged updates do not prove the exact amount of lost resident work.

An epoch-labelled whole-pending-sleep restart would therefore do **48 new updates** from the saved state: C0 **8412 → 8460**, Astra7 **9644 → 9692**. These are **unexecuted expectations**, not outcomes. C0's equal nominal final step would not establish identical weights. Do not run just Astra7's19 nominal remaining updates, seed a new optimizer, reconstruct RNG from a counter, replay historical tools/generations, or discard pending rows.

## Existing candidate: evidence versus integration

- Candidate: `research_loop/workers/post_recovery_node2_sleep_20260919/runtime_candidate/interrupted_sleep.py`. Its source still matches the79-test receipt: **39 candidate +18 contract +22 strict-replay tests passed previously**. All recorded local source pins matched during this audit; the tests were not rerun.
- Those tests use synthetic training children. They do **not** prove actual checkpoint tensor restoration, authentic full-journal replay, a GPU continuation, or compatibility with these exact receiving plans.
- The candidate delegates saved-state restore to the original loader, trains all three pending rows under the original16-presentation NEW-only/all-authentic-rows recipe, and requires a new verified COMMIT before SLEEP_COMPLETE. It preserves failed-attempt artifacts and has no automatic retry.
- The four relevant installed receiving sources per life still match their original guard pins; no candidate hook is present in those sources. The kernel is not a continuing original dispatcher/Think–Act–Learn integration. Current original startup rejects unresolved pending sleep.
- **Astra7's partial intent is an additional hard blocker:** the original journal reader and candidate audit reject it. The current candidate has no preserve-and-reconcile mechanism. Deleting/renaming/skipping it, inventing a7808 payload, or silently copying only a prefix is not a continuation plan.

## Smallest safe continuation plan — for Main, not executed

1. **Stabilize capacity and preservation first.** At this cut node2 reports100% used, with **4,660,117,504 bytes (4.34 GiB) available**. Bind a capacity/preservation receipt covering durable checkpoint pairs, complete retained journals, the failed C0 checkpoint and Astra7's partial intent. Do not use the VM for bulk extractions. Both known native PIDs are absent and no writer-lock holder was visible, but exclusive ownership and an unchanged head need fresh verification at execution time.
2. **Resolve the two concrete format/contract mismatches in scoped integration.** Preserve and explicitly account for Astra7's partial publication in a bound recovery epoch without losing history. Handle the already-applied wall-extension history while retaining the exact final bound and provenance; the current candidate's null-only predicate is incompatible with the live plans. Neither issue is fixed by this audit.
3. **Attach the candidate to the original confined receiving driver.** Bind actual full COMPLETE/pending-state bodies, recipe and eligibility, original source/plan/checkpoint/base/lease/CPU/allocation and fresh exact admission. Validate the whole retained chain on-node; this bounded header read is not that validation. Original consumed guards/DISPATCH_ONCE must not be reused. Preserve UID/GID2524, GPU binding, life-specific virtual-root BindPaths and original confinement; no standalone NativeChild launcher.
4. **Restart precisely one whole pending sleep from the durable checkpoint plus retained pending stream.** Use an unambiguous new checkpoint namespace such as the candidate's `sleep_<cycle>_restart_<attempt-key>`; preserve C0's failed `sleep_000146`. Record saved-RNG origin and duplicate/lost compute explicitly. Emit exactly one new SLEEP_COMPLETE and exactly one paired R184_LEARN_COMPLETE, then hand the completed state back to the original loop. Bind receiving parent/readout/checkpoint-lookup compatibility before doing so.
5. **Verify before claiming recovery.** Fresh checkpoint binary verification, original-loader restore, all three rows ×16 presentations with no exclusions, unchanged base, new adapter/checkpoint, valid journal continuation, correct next-stage transition, and parent REQUEST→ACT delivery are the needed receipts. No idle native or successful CPU fixture can substitute for them.

The current original node2 hard end is **2026-09-20 18:00 UTC**. This inventory neither extends it nor changes lease/admission policy. The plan is a checkpoint-origin recovery with all retained state, **not a claim of byte-identical resumption of unsaved resident computation**.

## Audit boundaries and ready artifacts

- `research_loop/workers/replication_sprint_20260919/evidence/node2_recovery/INVENTORY.json` contains fresh failure/traceback metadata, checkpoint/file hashes, original guard/plan/source bindings, row/stage evidence, candidate-test bindings and explicit limitations.
- Fresh remote read: **1,345,441 bytes**, at most128 record headers per life, 4 KiB record tails, 64 KiB small bodies, 512 KiB guard cap, 128 KiB selected-source cap and 8 KiB log cap. Large COMPLETE/SLEEP_REQUEST bodies were not reread; the earlier authenticated state projection is tied here to unchanged stored boundary hashes/head.
- No weights/journals copied to the VM, no credential reads, no full-journal audit, no test execution, no runtime/source changes, no node3/other-node access, no launch/signals/reset/tail drop, no git commit/push. Only this evidence subdirectory is written.
