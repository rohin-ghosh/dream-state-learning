# Astra contrastive full-dose: independent terminal audit

**Date:** 2026-09-13  
**Role:** independent read-only outcome auditor  
**Disposition:** complete negative/mixed authored-curriculum result; do not add
more dose to this fixture

## Bottom line

The six fits and all readouts completed cleanly. Contrastive presentation beat
PLAIN on held strict record rendering by `+2`, `+6`, and `0` of 24 across the
three independent learner seeds. Pooled descriptively, that is `58/72` versus
`50/72`, but the learner-level result is only two positive pairs and one tie.
No seed passed the preregistered screen, and the advantage was entirely in one
of the two wrappers: `D1` improved `26/36 -> 34/36`, while `D2` tied at `24/36`.

This supports only a narrow statement: at this extreme dose, the exact authored
contrastive input bundle sometimes improves execution of this fixed fixture
relative to the exact PLAIN bundle. It does **not** show robust source selection,
keyed memory, child-authored sleep, parenting, or learning from action-outcome
experience. The current fixture has a perfect `negate-earlier-observation`
shortcut aligned with the contrastive instruction, so even perfect performance
would not identify selected-outcome reading.

The useful decision is therefore negative: **dose was not the missing
ingredient**. On seed 0, increasing the same fit from four to 112 epochs left
aggregate held totals exactly unchanged (`PLAIN 17/24`, `CONTRASTIVE 19/24`).
The next test should change the information structure, not add epochs: fresh
source families, independently varying event relations, and a withheld value
that truly requires keyed retrieval.

## Authoritative terminal artifacts

At audit time, all three roots had `capture_complete.json`, no matching live
process remained, and Astra's once-only collectors had already produced the
following reports:

| seed | plan SHA-256 | capture SHA-256 | scores SHA-256 |
|---:|---|---|---|
| 0 | `4742d9fbafe70d5f5bc97ef15d3712e0ad52bd20ae0887ab6e81b5e73359ffb8` | `2986cfe42f5b9c0fc748d677992d10dec2a3354c3c0f0dca6e6cc2267de71b97` | `0ed0d948d342335ec20067b3acbcea1abf7892e5890bf0f1e1f18a68108c4358` |
| 1 | `d19c72e6153549f2ea9a6bd218a1f2380aaedb64e0f563eed8b3a57982e28551` | `a4594ad4ebf2a1354b7059a91121f7df24f7e75e21e597a7193db01545f17b19` | `8e9993e3cef1ba5bcef1dd89d6a638c6c1b16d64d02afee3b0ed77a0b4210922` |
| 2 | `b22af588a1be9549807c140dc594fda523a573b6de5f81a3ff23cb2520720e71` | `ee5b63d91062ef7e873f4cca3b9bdb6bfd88702e5d1d37d86f4e71d00a1da4f1` | `5e351431841f2743922861defdd71617b56794edade755982034424fa4f9bef2` |

Paths are
`/localhome/local-rohing/astra_diagnostics/contrastive_full_dose_seed{0,1,2}_20260913_attempt2_collected/scores.json`.
Each collection claim says `retry=false` and binds its exact completion hash.

The task premise that seed 0 remained uncollected was stale by the time of this
audit. Before collection, its complete raw requests/responses, fit receipts,
material, calls, historical OFF import, and `capture_complete.json` were
sufficient inputs for the frozen deterministic reducer. However, an ad-hoc
manual reduction would not have closed the runner's custody checks. The
protocol-required once-only collector has now run, so seed 0 is authoritative
and must not be recollected.

## Registered results

Strict credit requires one exact, complete four-field JSON record.

| seed | arm | D1 | D2 | held | C-record | C-general |
|---:|---|---:|---:|---:|---:|---:|
| 0 | historical OFF | 0/12 | 2/12 | 2/24 | 0/12 | 11/12 |
| 0 | PLAIN | 9/12 | 8/12 | 17/24 | 6/12 | 12/12 |
| 0 | CONTRASTIVE | 11/12 | 8/12 | 19/24 | 11/12 | 12/12 |
| 1 | PLAIN | 7/12 | 7/12 | 14/24 | 7/12 | 12/12 |
| 1 | CONTRASTIVE | 12/12 | 8/12 | 20/24 | 11/12 | 12/12 |
| 2 | PLAIN | 10/12 | 9/12 | 19/24 | 7/12 | 12/12 |
| 2 | CONTRASTIVE | 11/12 | 8/12 | 19/24 | 11/12 | 12/12 |
| **sum** | **PLAIN** | **26/36** | **24/36** | **50/72** | **20/36** | **36/36** |
| **sum** | **CONTRASTIVE** | **34/36** | **24/36** | **58/72** | **33/36** | **36/36** |

The historical OFF responses are one pinned, noncontemporaneous baseline reused
for all three reports, not three independent OFF learners.

The frozen per-seed screen required CONTRASTIVE `>=20/24`, both wrappers
`>=9/12`, a `>=4/24` advantage over both PLAIN and OFF, no loss on any
OFF-correct canary, and complete captures. Every report correctly records
`exploratory_screen_pass=false`:

- seed 0 misses held total (`19`), D2 (`8`), and PLAIN advantage (`+2`);
- seed 1 reaches `20` and beats PLAIN by `+6`, but D2 is only `8/12`;
- seed 2 misses held total (`19`), D2 (`8`), and has no PLAIN advantage.

`automatic_pass=false` is not a runner failure. The collector deliberately
hard-codes it, with `scientific_pass=null`, because this is exposed exploratory
DEV evidence and must never promote a scientific claim automatically. The
actual frozen threshold calculation lives separately in
`material_scores.exploratory_screen_pass`, which is also false for all seeds.

## Formatting versus semantic content

The deep fits largely eliminated the earlier Markdown-fence problem: every
CONTRASTIVE held response and 71/72 PLAIN held responses were syntactically and
schema valid. On the 71 mutually format-valid wrapper renderings,
CONTRASTIVE had eight strict content-only wins and one loss over PLAIN. One
additional seed-1 D1 strict gain was formatting/schema rather than a mutually
valid content comparison.

The field pattern does not support selected-outcome attention:

| held wrapper | arm | action | prediction | observation | relation |
|---|---|---:|---:|---:|---:|
| D1 (36 renders) | PLAIN | 35 | 26 | 35 | 26 |
| D1 | CONTRASTIVE | 36 | 34 | 36 | 34 |
| D2 (36 renders) | PLAIN | 28 | 28 | 30 | 28 |
| D2 | CONTRASTIVE | 30 | 25 | 32 | 25 |

In D1, the seven mutually valid strict gains were driven by prediction and its
derived relation; observation had no itemwise gain. In D2, mutually valid
strict transitions tied `1:1`, while prediction and relation were worse in
aggregate under CONTRASTIVE. This is wrapper-specific execution and is fully
compatible with the registered polarity shortcut; it is not robust evidence
that the adapter learned to attend to the selected outcome.

## Fit integrity, dose, and locality

All six adapters were fresh all-layer attention+MLP rank-8 LoRAs with alpha 16,
dropout 0.05, LR `1e-4`, batch 4, and the same target bytes and epoch order
within each paired seed. Each arm used only 12 authored rows but repeated them
for 112 epochs: 1,344 presentations and 336 optimizer updates. There were zero
nonfinite batches and zero truncated items/tokens.

The fits memorized the supervised distribution almost immediately. Across
seeds, epoch-one loss was about `1.05-1.07`, epoch-two `0.27-0.30`, and
epoch-three `0.0011-0.0017`; terminal loss was `5.1e-6` to `6.0e-6`. Continuing
for roughly 109 more epochs produced no seed-0 aggregate held improvement over
the original four-epoch screen. This is a deliberately extreme fixed-material
dose, not a realistic SLEEP recipe and not evidence that high-dose writing is
safe.

The arms were target matched but not exactly compute matched. Per epoch PLAIN
used 4,806 tokens versus 4,914 for CONTRASTIVE; over 112 epochs that is 538,272
versus 550,368 train tokens (`+2.25%`). Thus the treatment remains a bundle of
grouping, explicit instruction, wording/order, extra context, and a slightly
different optimization trajectory.

The registered strict canary reports no regressions. Both trained arms scored
`36/36` on `C-general`, versus the single historical OFF baseline's `11/12`.
But this establishes only no harm on that tiny arithmetic/copy panel. Historical
OFF had `0/12` strict C-record solely because it used fenced JSON, so its strict
C-record no-harm denominator is empty. CONTRASTIVE's `33/36` versus PLAIN's
`20/36` on C-record shows better execution/rehearsal of an exposed record
family, not retention of unrelated prior capability. No broad retention or
writer-safety claim is available.

## Scientific disposition

Treat this as a complete, useful **negative/mixed curriculum diagnostic**:

1. The writer can absorb 12 authored targets to effectively zero training loss.
2. More repetition does not repair the fixture's identification problem or
   produce wrapper-general improvement.
3. The contrastive bundle has a real descriptive advantage in D1 and exposed
   C-record execution, but no aggregate D2 advantage and no registered pass.
4. Do not spend another fit increasing dose on these bytes.
5. Preserve contrastive grouping as a candidate compiler ingredient, but test
   it next only in a shortcut-resistant, value-withheld keyed task. This result
   neither establishes nor falsifies the larger Dream-LoRA-Think mechanism.
