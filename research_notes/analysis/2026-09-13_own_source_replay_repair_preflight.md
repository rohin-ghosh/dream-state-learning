# Own-source replay repair: fresh preflight audit

**Date:** 2026-09-13 UTC  
**Disposition:** **REWORK BEFORE GPU; no recapture required**  
**Scope:** the narrow `REPLAY` versus `EXTRA_MEMORY` substrate-repair cell
only. No C11, parenting, lifetime, or whole-organism claim is added.

## Bottom line

The capture succeeded. All three original perception parents produced an
admissible response on every prospectively selected source: `24/24` per
parent, `72/72` submitted rows overall, with zero rejects, missing responses,
or completion failures. The collected bytes and the independent custody audit
are sufficient candidate material for a separately qualified replay fit.

The experiment is nevertheless **not executable yet**. The only implemented
own-source code is a capture/admission path. It deliberately emits no training
export and no fit decision, and the inherited memory runner cannot accept the
`32--38` mixed rows or the `256--304` updates per arm. A new, bounded mixed-
corpus materializer/runner and its CPU tests are still required.

Scientifically, the two fresh arms are a useful and economical comparison if
the claim stays exact:

> At fixed initialization, optimizer-step count, and low-LR recipe, replace
> extra rehearsal of the new memory records with rehearsal of the child's own
> previously correct perception outputs, then measure the old-skill/new-memory
> tradeoff.

It does **not** isolate replay semantics from token length/compute, prove
general SLEEP, or use new autonomous experience.

## Why the report says `false` and `null`

These values are intentional sentinels, not failed checks.

- The frozen core has no model backend. `build()` explicitly writes
  `native_identity_verified=false` and `training_export_ready=false`; its
  binding decisions say native identity and fit choice belong to the caller.
- `admit()` verifies source/prompt/producer declarations and preserves the raw
  supplied child bytes, but again returns `native_identity_verified=false`,
  `training_export_ready=false`, and `fit_decision=null` unconditionally.
- The native capture wrapper separately checks the actual tokenizer prompt,
  model/adapter route, native response, three distinct sequential child
  processes, unchanged adapter inventories, and owned release. Its collector
  intentionally copies the core's limitation into the summary as
  `core_native_identity_verified=false`, `automatic_pass=false`, and
  `fit_decision=null`.

Therefore `core_native_identity_verified=false` means **the source-only core
cannot attest native execution**. It does not negate the wrapper's native
custody evidence. Likewise, `fit_decision=null` means **capture did not grant a
fit**, exactly as prospectively specified.

Do not alter those collected fields to `true`. The fit implementation should
write a new immutable qualification receipt that binds the capture evidence
and authorizes only this prespecified comparison.

## Candidate-material audit

The authoritative collected hashes are:

| artifact | SHA-256 |
|---|---|
| replay report | `6648c0bc85589dea4e2a7ea498bf547f5313bd38efcd14c15a7d3eee228124c4` |
| seed 0 admission | `cd53aa016c09b5d2d1f81b0a27d1c303ffc92961631c6b5d983462263f47b7ae` |
| seed 1 admission | `3d14ef303276c14469469a0b63468401776eb75fd27fb42f85eda9117b39916d` |
| seed 2 admission | `f9ec4394b59a54c65d2a962675c7ba97a1d57e42add9df1a90115f82b572c631` |
| independent custody audit JSON | `38435b38985f8b2b40bf8e0a7c183f6be76bbbf318ffcfc7d14baa7a1f7f6621` |
| native evidence archive | `94e313ee069cc402eba18c515558ae649244b2036b17b430e4a5b29bd51698fb` |

Fresh local reductions agree with the archived audit:

- each seed has 24 distinct row IDs, request IDs, prompts, and raw targets;
- each seed is bound to the correct original learner and distinct original
  perception-adapter weight hash;
- no literal held, canary, teacher, or parent field occurs in an admitted row;
- all 24 input/target semantic pairs are byte-identical across the three
  parents; and
- there are only **24 distinct sources and targets overall**, each observed
  three times, not 72 independent replay facts.

The last point is important. The three parents are replications over different
learned adapters/training seeds, but source breadth is 24. The prompts were
externally authored TRAIN observations already used in the parents' birth
training, and the greedy children all rendered the same correct records. This
is truthful own-output rehearsal of an inherited perception skill, not novel
TRY experience or independent evidence acquisition.

## Is `REPLAY` versus `EXTRA_MEMORY` causal?

**Yes, for a narrow allocation estimand.** Within each seed, both arms can
share the exact original perception adapter, frozen base, rank 8 topology,
fresh optimizer, LR `3e-5`, batch 1, fit seed, eight passes, greedy readout,
and total optimizer steps. The only intended allocation difference is:

- `REPLAY`: `m` actual-event memories plus 24 old-skill own-output rows;
- `EXTRA_MEMORY`: the same `m` memories plus 24 extra presentations drawn
  from those same memories.

The arithmetic is correct:

| seed | `m` | rows/arm | updates/arm | calls/arm |
|---:|---:|---:|---:|---:|
| 0 | 14 | 38 | 304 | 88 |
| 1 | 8 | 32 | 256 | 76 |
| 2 | 8 | 32 | 256 | 76 |
| **total, two arms** |  |  | **1,632** | **480** |

This is the cheapest valid current design for asking whether the extra write
budget is better spent on old-skill replay than on more new-memory rehearsal:
three `REPLAY` fits alone would confound replay content with 24 extra updates
per pass, while rerunning HIGH/LR0 or recollecting sources adds no necessary
identification. Severe seed variation in the lower-LR result makes retaining
all three original parents necessary.

The interpretation must remain limited. Step count is matched, but prompt and
target token counts, FLOPs, gradient content, and memory exposure are not.
`EXTRA_MEMORY` deliberately gives the new memories more supervision. Thus a
difference is a **practical data-allocation effect**, not a pure semantic-
replay mechanism. Historical LOWER is useful only as the labeled,
noncontemporaneous no-extra-material reference.

## Exact must-fix items before launch

1. **Add a separate qualification receipt; preserve the capture.** Bind the
   six hashes above, all three producer/adapter identities, the native
   request/response joins, and the independent audit status. State
   `qualified_for=OWN_SOURCE_REPLAY_REPAIR_ONLY`. Never rewrite the core's
   `false/null` fields and never infer general training-export approval.

2. **Verify native bytes, not only copied admissions.** Preparation must read
   the pinned native evidence archive or original immutable capture root and
   rejoin every admitted raw target to its native request/response hash. The
   four collected JSON files alone cannot independently prove which model
   emitted the text.

3. **Implement the missing mixed-corpus path.** Emit separately pinned
   `REPLAY` and `EXTRA_MEMORY` training files and token/mask/epoch-order
   manifests. Check both schemas independently; supervise the exact raw target
   plus one EOS, mask all context/padding, require one unsplit sequence, zero
   target/context truncation, and deterministic row/presentation identities.
   Do not loosen the old memory helper. The inherited encoder's `<=16`-row and
   `<=128`-update checks make direct reuse invalid here.

4. **Bind the original memory side exactly.** For each seed, import the same
   `14/8/8` source-withdrawn memory rows, cues, raw targets, original parent
   weights, LR0 retention roster, fit seed, and readout calls used by the
   lower-LR audit. Reject a LOW/HIGH/memory descendant as initialization and
   reject any cross-seed replay report swap even though its semantic bytes are
   identical.

5. **Repair seed-0 control-dose imbalance.** A static pool made by cycling 14
   rows to create 24 duplicates and then replaying that pool for eight epochs
   gives ten memories twice the extra exposure of four others. Materialize the
   full 192 extra presentations with a deterministic rotating offset so the 14
   memory IDs differ by at most one extra presentation over the whole fit.
   Seeds 1/2 divide evenly already. Preserve 304 total updates for seed 0.

6. **Freeze the direct result rule.** The unambiguous repair gate is the
   inherited all-seed screen: `REPLAY` reaches exact source-faithful floors
   `8/14, 7/8, 5/8` and loses zero LR0-correct held/canary items. Report the
   full paired table for both arms. Content-specific support is strongest if
   `REPLAY` passes while `EXTRA_MEMORY` does not; do not invent a post-result
   meaning for “comparable recall” or select a winning seed.

7. **Close the ordinary runtime checks.** Fresh private roots; paired arm
   initialization and optimizer receipts; exact LoRA-only trainable set;
   finite losses/gradients/weights; changed weights; frozen parent before and
   after; full token and wall-time accounting; cold source-free readout; strict
   itemwise scorer plus best-constant diagnostic; owned release; exclusive
   collection; no automatic retry or dose change. CPU fixtures must cover
   cross-seed swaps, target normalization, mixed-schema confusion, the
   rotating seed-0 schedule, truncation, nonfinite failure, and partial-arm
   collection refusal.

## Launch and claim decision

After those seven repairs pass CPU preparation, **launch is scientifically
reasonable and no new capture is warranted**. Six fits and 480 cold calls are
small relative to a PCFL DEV or lifetime run and directly test the remaining
failure exposed by LOW: three inherited-skill items were still lost and only
one of three learners met the strict screen.

A positive result would justify only:

> In this three-parent exploratory DEV comparison, allocating additional
> low-rate updates to exact rehearsal of the child's prior correct perception
> outputs repaired the prespecified memory/retention screen more reliably than
> allocating the same number of updates to additional new-memory rehearsal.

It would not establish autonomous replay selection, connected experiential
knowledge, recurrence, parenting, general retention, PCFL, H1/H2, or a safe
paper-grade SLEEP mechanism. A negative result is equally decisive for this
recipe: stop treating this 24-row own-source mixture as the retention repair
and move to the smallest data/optimizer change supported by the itemwise
failures.
