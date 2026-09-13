# Own-source replay repair: independent terminal audit

**Date:** 2026-09-13 UTC  
**Disposition:** all-seed writer-repair screen **FAIL** (`REPLAY` passes `2/3` roots)  
**Scope:** read-only audit of the six fresh fits and three once-collected node-2
score artifacts. No source, model, tokenizer, adapter, job, or GPU state was
changed.

## Verdict

Replaying the child's prior correct perception outputs moved the
acquisition/retention tradeoff in the intended direction, but it did not repair
the writer across all three seeds.

- `REPLAY` preserved every originally correct Level-1 held item: `143/143`,
  versus `135/143` for `EXTRA_MEMORY`; both arms retained all `36/36`
  canaries.
- The price was weaker new-memory access: exact recall was `21/30` for
  `REPLAY` versus `27/30` for `EXTRA_MEMORY`; paraphrase recall was `19/30`
  versus `23/30`.
- The noncompensatory screen passed `REPLAY` on seeds 0 and 2. Seed 1 retained
  perfectly but recalled only `6/8`, below its frozen `7/8` floor. Therefore
  the required all-seed decision is **false**.
- Relative to the historical low-rate write, `REPLAY` improved exact recall
  `18/30 -> 21/30`, paraphrase recall `18/30 -> 19/30`, and restored the three
  previously lost held items. This comparison is noncontemporaneous and uses
  `816` rather than `240` updates, although both give each new memory the same
  eight presentations.

This is evidence that old-skill rehearsal can protect an existing adapter
while it learns a small memory bank. It is not evidence for a generally safe
SLEEP writer, autonomous replay selection, connected memory, or lifetime
learning.

## Direct results

Semantic source-faithful recall is reported below. `robust` counts a distinct
within-seed target only if every occurrence of that target was correct.

| seed | arm | exact | paraphrase | exact robust | paraphrase robust | old held | generic canary | frozen screen |
|---:|---|---:|---:|---:|---:|---:|---:|---|
| 0 | REPLAY | 10/14 | 10/14 | 3/4 | 3/4 | 47/48 | 12/12 | PASS |
| 0 | EXTRA_MEMORY | 13/14 | 10/14 | 3/4 | 3/4 | 47/48 | 12/12 | PASS |
| 1 | REPLAY | 6/8 | 6/8 | 3/5 | 3/5 | 48/48 | 12/12 | FAIL: recall `<7` |
| 1 | EXTRA_MEMORY | 7/8 | 6/8 | 4/5 | 3/5 | 46/48 | 12/12 | FAIL: 2 held losses |
| 2 | REPLAY | 5/8 | 3/8 | 2/5 | 1/5 | 48/48 | 12/12 | PASS |
| 2 | EXTRA_MEMORY | 7/8 | 7/8 | 4/5 | 4/5 | 42/48 | 12/12 | FAIL: 6 held losses |
| **pooled** | **REPLAY** | **21/30** | **19/30** | **8/14** | **7/14** | **143/144** | **36/36** | **2/3; FAIL** |
| **pooled** | **EXTRA_MEMORY** | **27/30** | **23/30** | **11/14** | **10/14** | **135/144** | **36/36** | **1/3; FAIL** |

For context, the bound historical endpoints were:

| endpoint | exact | paraphrase | exact robust | paraphrase robust | old held | canary |
|---|---:|---:|---:|---:|---:|---:|
| LOWER (`3e-5`) | 18/30 | 18/30 | 5/14 | 6/14 | 140/144 | 36/36 |
| HIGH (`1e-4`) | 20/30 | 16/30 | 7/14 | 6/14 | 98/144 | 36/36 |
| LR0 | 0/30 | 0/30 | 0/14 | 0/14 | 143/144 | 36/36 |

`REPLAY` lost zero of the `143` items LR0 got right. `EXTRA_MEMORY` lost eight.
Both fresh arms remained perfect on the generic canary, again showing that the
generic canary alone cannot detect task-skill interference.

## Terminal receipt audit

Six of the seven requested terminal checks are clean:

1. **Native raw rejoin — PASS.** I directly rejoined all `72` replay rows to
   the original native request/response files. Request hashes, response hashes,
   request IDs, exact response text, and target hashes match the admission and
   repair mixtures.
2. **Per-arm manifests — PASS.** Each frozen training-file hash agrees across
   the pre-output plan, fit receipt, adapter manifest, and collected score
   artifact. Both arms have `38/32/32` rows and `304/256/256` updates.
3. **Original bindings — PASS.** Each mixture uses the original `14/8/8`
   memory rows byte-for-byte. Both arms initialize from the same corresponding
   original perception parent, not a LOW/HIGH/memory descendant. Parent,
   memory-history, lower-history, capture, model, and source hashes agree.
4. **Seed-0 duplicate schedule balance — FAIL.** The preflight required the
   `192` additional memory presentations to be spread `13--14` times over each
   of 14 source rows. The executed materializer instead made 24 static cyclic
   duplicates and repeated them for eight epochs: ten source rows received 16
   extra presentations and four received 8 (range `8`). Seeds 1 and 2 are
   balanced. This weakens seed 0's `REPLAY`-versus-`EXTRA_MEMORY` content
   contrast, but it does not rescue the failed direct all-seed `REPLAY` screen.
5. **Direct all-seed result — PASS as a reduction; result FAIL.** The
   prespecified conjunction is `2/3`, because seed 1 misses its recall floor.
   No pooled gain or selected seed can override it.
6. **Numerics/runtime — PASS.** All six fits report zero nonfinite batches,
   zero target/context truncation, zero splits, changed LoRA weights, frozen
   base weights, and a LoRA-only trainable set. Every fit/readout has an owned
   release receipt.
7. **Once-only collection — PASS.** Each root has exactly one `retry=false`
   collection claim, one collected directory, and matching plan, completion,
   score, and collection hashes; no failure artifact or second collection is
   present.

One additional preflight requirement was not implemented: there is no
separately named `qualified_for=OWN_SOURCE_REPLAY_REPAIR_ONLY` qualification
receipt. The executed plans nevertheless bind the protocol, capture, native
joins, original parents, histories, material, and runner, and the collected
artifacts preserve the capture's intentional `false/null` sentinels. This is a
formal conformance omission, not evidence that the native rows were fabricated.

## Dose and cost

All fresh fits used rank 8, alpha 16, dropout `.05`, all attention and MLP
projections, LR `3e-5`, batch 1, eight passes, and the original learner seed.

| seed | arm | steps | final loss | parameter-delta L2 | train / fit-wall seconds |
|---:|---|---:|---:|---:|---:|
| 0 | REPLAY | 304 | 0.00000779 | 1.946 | 90.2 / 95.9 |
| 0 | EXTRA_MEMORY | 304 | 0.005188 | 2.188 | 70.9 / 76.6 |
| 1 | REPLAY | 256 | 0.073592 | 1.629 | 78.8 / 85.0 |
| 1 | EXTRA_MEMORY | 256 | 0.074396 | 2.049 | 60.2 / 65.7 |
| 2 | REPLAY | 256 | 0.00000853 | 1.461 | 80.3 / 86.7 |
| 2 | EXTRA_MEMORY | 256 | 0.003048 | 2.014 | 63.3 / 68.8 |

Total incremental work was `6` fits, `1,632` updates, and `480` cold calls.
Training processed `381,528` token presentations (`46,728` supervised and
`334,800` context); readout used `111,598` prompt and `10,297` output tokens.
Summed fit train/wall time was `443.7/478.7` seconds, summed generation time
was `435.6` seconds, and summed controller time was `1,512.2` seconds. The
earlier 72-call source capture and all historical endpoints incurred zero new
cost in this repair run.

The arms are deliberately not token- or memory-exposure-matched. `REPLAY`
processed `240,160` training-token presentations versus `141,368` for
`EXTRA_MEMORY`, largely because observation-reading contexts are longer;
`EXTRA_MEMORY` gave the new records much more supervision. The only supported
causal reading is therefore a **fixed-step practical data-allocation test**.

## Consequence

Do not promote this replay mixture as the writer repair. It cleanly shows the
tradeoff the next writer must solve: `REPLAY` restores retention but leaves one
seed below the memory floor; `EXTRA_MEMORY` raises recall but damages retained
skill in two seeds. PCFL should keep replay and task-specific retention in its
writer gate, but must establish its own all-root acquisition, locality, and
use results under its separately frozen batch construction.
