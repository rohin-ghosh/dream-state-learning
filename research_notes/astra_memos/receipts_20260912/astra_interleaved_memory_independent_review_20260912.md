# Root0 interleaved memory — independent raw review, September 12, 2026

**PASS: raw recount, local custody/technical-receipt audit, and all prespecified FOUR_VIEW progression criteria.** Both arms have complete captures; no missing cases, score contradictions, invalid answers, or length-cap hits. This establishes eligibility for **Main's** next-seed decision, not automatic execution or scientific promotion.

## Independent counts

Recomputed **224 raw calls**: SINGLE_VIEW112 and FOUR_VIEW112, each dev48 + exact16 + lexical48. Expected memory answers come from the hash-pinned original80 teaching rows; arithmetic answers are independently summed from request operands. Existing reducers were not executed. Every recomputed row field/count agrees with the six sealed reductions.

| Endpoint | SINGLE_VIEW | FOUR_VIEW | Prespecified FOUR minimum | Result |
|---|---:|---:|---:|---|
| Dev memory | 16/16 | 16/16 | 15/16 | PASS |
| Exact original training prefix | 16/16 | 16/16 | 15/16 | PASS |
| Dev arithmetic habit | 32/32 | 32/32 | 30/32 | PASS |
| Dev correct ACT | 32/32 | 32/32 | 31/32 | PASS |
| Lexical family0 | 16/16 | 16/16 | 15/16 | PASS |
| Lexical family1 | 16/16 | 16/16 | 15/16 | PASS |
| Lexical family2 | 16/16 | 16/16 | 15/16 | PASS |
| Technical completion/custody | PASS | PASS | PASS | PASS |

Habit requires one valid, correct PREDICT preceding one valid, correct ACT; ACT correctness is scored separately. Memory accepts a single case-normalized color, optionally one trailing period—not substring matches. All outputs here satisfy the exact rules. Each16-fact panel returns four each of blue/green/red/yellow. All224 finishes are `stop`, none reaches64 tokens; no arithmetic color spill, repeated-color failure, or cross-panel error mismatch exists. Direct pairing additionally confirms identical raw text **and output-token sequences** for all112 aligned calls across arms; equal aggregates alone were not used to infer this.

Lexical families are, respectively, “Look up {device} in the log and give its color.”; “Consult the log: {device} has which color?”; “In the log entry for {device}, what color is listed?” All48 normalized cues are distinct and excluded from original train/control/eval wording and all four training templates. They query **the same16 facts**, not48 new facts or independent observations. Dev is the old recall wording; exact is the original training wording. Original-parent dev4/16 memory and32/32 habit/ACT are **inherited, provenance-bound baseline counts**, not newly recounted here. No new OFF or confirmation calls occurred.

## Training, source schedule and isolation

Both128-row corpora were independently reconstructed from original source order, spans and metadata, and match the sealed native corpus SHA256s exactly. This verifies the same16 memories + fixed first16 arithmetic sources, four copies each, original targets/masks, and the SINGLE/FOUR context difference without a tokenizer. Source order and target bytes are not inferred from performance.

For copy round r and block b, the reconstructed batch is M[2b], A[(2b+2r)%16], M[2b+1], A[(2b+2r+1)%16]. Thirty-two four-row groups are shuffled per epoch using the seed0 V3 schedule; ten epochs give **320 new updates/400 cumulative** per arm,40 presentations and40 distinct source-bearing steps per source. Both arms share the schedule; each batch has two distinct memories and two distinct additions. There is no promise of minimum temporal spacing.

| Native accounting per child | SINGLE_VIEW | FOUR_VIEW |
|---|---:|---:|
| Input / context / target per epoch | 6,616 / 5,616 / 1,000 | 6,712 / 5,712 / 1,000 |
| Input / context presentations | 66,160 / 56,160 | 67,120 / 57,120 |
| Target presentations, including EOS | 10,000 | 10,000 |
| Memory / addition target presentations | 1,280 / 8,720 | 1,280 / 8,720 |
| Padded input slots | 76,960 | 76,960 |
| Train loop / trainer-function wall seconds | 78.3 / 83.0 | 78.1 / 82.8 |

SINGLE padding is independently recomputed from original native row lengths; FOUR padding and its changed prefix lengths are checked against native receipts. Using original target lengths gives200 batches with32 targets and120 with30; every batch has4 memory targets. Thus memory's **aggregate12.8%** target mass is not a constant per-batch fraction: batches are12.5% or13⅓%. This is not a pure source-spacing comparison with old grouped replay, nor equal unpadded-input compute; observed padded totals happen to match.

Receipts bind both independent forks to the original seed0 teach adapter, not a replay descendant or the other arm. Each initializes all392 tensor hashes exactly equal to the parent, with no dtype conversions, one rank8 adapter,20,185,088 trainable parameters, frozen base, fresh AdamW state0, seed0/LR3e-4/batch4/accum1/10epochs. Parent inventories before/after agree. All392 final tensor hashes change per arm; saved child hashes differ. Both manifests record320 updates, zero nonfinite batches,128 encoded rows,32 groups, and no truncation/splitting/dropped targets. This is receipt evidence of writes, not a numerical update-size audit.

Each of six readouts uses a fresh supervised process, the same pinned base and that arm's saved adapter; request identities, native rendered-prefix/token IDs and immutable capture manifests agree. Generation is greedy temperature0, seed20260912, cap64. No parent conversation, cross-case history, training-time updates, or answer key is inserted into the raw requests. The exact native tokenizer and model were **not** rerun. Full per-row native mask/ID and schedule-audit files are hash-bound but not included as standalone material files in this capsule; actual per-step execution is not traced. These limits do not constitute a score contradiction.

## Custody and overlapping costs

In-memory verification passes all**548** inventory hashes: unique, safe relative regular-file members, no traversal/links/duplicates/weight payloads. Six original-parent provenance files also match pinned hashes. All eight unique sequential workers report success, owned cleanup and release. Controller238349/device1 and release UUID `GPU-71e5a3e2-e9c8-5caf-70d8-73794ac34821` match launch. External watch receipts bind the launch/plan/reservation: the watch observes controller exit as `ZOMBIE`, sends no signals and **does not attest GPU cleanup**; the separate full-release JSON/XML supplies that evidence. Watch start/terminal are external to the capsule and separately hashed in the analysis JSON.

- Generation:9,798 input/1,200 output tokens,57.916751s;14,336 allowed output tokens are a ceiling, not usage.
- Workers:1,074.210888s; controller:1,308.918702s; launch→full-release observation:1,395.898451s (**23.264974 A40-min**), release22:18:27.750796UTC.
- Final collection observation:1,396.315843s (**23.271931min**). Its0.417392s difference is a later observation, not contradictory clocks. Do not add nested generation/worker/controller/reservation intervals.1800s controller including140s cleanup, plus300s custody; no extension/overrun. Monetary cost unavailable.

**Claim boundary:** both arms saturate this exposed root0 diagnostic, so no observed FOUR-over-SINGLE advantage. This supports acquiring these authored facts while retaining this arithmetic interface under the tested interleaved recipe—not child-experience learning, parenting efficacy, broad transfer, latent-capacity claims, or freeze/G3/P1/H2 promotion. Source/base origin remains `UNRESOLVED_LOCAL_HASHES_ONLY`. No outcome-selective skips or automatic progression occurred.

Capsule SHA256: `9aa7fb67b3f68afa3d4520e1f4b7cfcc41322367ef1cf6ee83396a7c60cdbf64`.
Plan: `4cad487a53d0e992b896eb4324ff2de1adb24ccc176856de7043d1132c0ee388`; source `22b7e528f6f62358981ed2264d30ee7242926160`.
Parent weight: `d73e8578f62de68ed657474c70fc09c09aaad50a4ff11a66773e50fc702163b2`.
SINGLE weight: `416f0f1dcc8f7dd6d37f6a8844d5e14786f0f54b970122e492e7b2f55f608bba`; FOUR: `60a8bd8c132308499621d77df31c1738e1444c976fe5d8b20f879bd94c49df2f`.

Disclosure: I authored older related replay code; this is an independent raw reduction, **not a fresh-author audit**. No Main outcomes were supplied; some sealed reductions became visible during schema inspection before completing the independent recount. Native weight bytes remain unexamined; no tokenizer/model/native/GPU/SSH/Git actions or other-owner edits. Reproducible code, all224 raw scored rows,320-step reconstructed schedules, receipt hashes and empty contradiction list are in same-stem `.py`/`.json`. **EDIT-STOP.**
