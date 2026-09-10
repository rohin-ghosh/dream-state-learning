# Fixed-writer certification report — DRAFT (Fable, 2026-09-08 06:45; for Codex audit)

> **CODE/PATH AUDIT HOLD — Codex, 2026-09-08 18:49 PDT.** Do not use this
> draft to certify `compile_native` or the v2.1 response-masked writer. The
> exact `run_life_v2.py` used by the R2 lives imports and calls
> `compile_sleep`, then launches `organism_v6.train_adapter`. Direct
> `train_meta.json` receipts on both GPU nodes identify that trainer as
> `recipe="v1_frozen"`, `lr=1e-4`, `epochs=3`, `rank=8`; sampled R2
> `corpus.json` rows are bare strings from the older sleep compiler. The
> newer `train_adapter_v21.py` (`lr=3e-5`, two epochs, chat-template,
> response-only loss) was not on this runner path. Local and remote source
> hashes agree for the relevant files (`run_life_v2.py`
> `b67b5a90f89f2f5241805f853163eaecb29ef876307dbff83ee1bb7e5dd98ad7`,
> `sleep_compile.py`
> `fad78e7e8199d9b5975089871b554365ddc88b12a8c3e066fb9e574acbee7403`,
> `train_adapter.py`
> `234d8a93b8fb9f79e2daef11b4b2b5c0eda860c3a096b5222a252be5019d2f1b`,
> `train_adapter_v21.py`
> `1df83da2f2660654bbaec92a4cf2c783111aa8692fd690f5b7e87c4fa7e0616b`).
> Therefore the behavioral cells below remain observations about the
> **old compiler + v1-frozen trainer + rank-8 + canary/gating system**.
> They are not evidence that the intended native v2.1 writer is safe,
> extractable, or freeze-ready. The freeze recommendation remains withdrawn
> until that exact intended writer passes a source-bound matched assay.

Scope actually run: the v6 R2 life path (`compile_sleep` with dialect
canonicalization inside emitted pathways, `train_adapter` recipe
`v1_frozen`, rank 8, sleep every 32 episodes, real-context format canary;
later R3 lives optionally add probe gating). Gym = CompilerGym llvm
IrInstructionCount, sealed probe split, probes seeded 777, adapter ON vs OFF
at the same episode. Base panel: 0.4936 ± 0.0113 (9 reps).

Certification bar (Rohin, 2026-09-07): absorption + retention + interface preservation + no-harm. Parent-absent transfer is judged only on the 7-day horizon and is NOT claimed here.

## Cell counts (6 lives, seeds 300–305; two nodes)

| life | node | ep0 base | paired ON−OFF by episode | sleeps (DONE / rejected) | canary min / mean |
|---|---|---|---|---|---|
| seed0 | 1 | 0.467 | 64 +0.019 · 128 +0.013 · 192 +0.011 · 256 +0.015 | 8 / 0 | 0.83 / 0.97 |
| seed1 | 1 | 0.463 | 64 +0.003 · 128 +0.007 · 192 +0.050 · 256 +0.048 | 8 / 0 | 1.00 / 1.00 |
| seed5 | 1 | 0.482 | 64 +0.025 · 128 +0.010 | 4 / 0 | 1.00 / 1.00 |
| seed2 | 2 | 0.482 | 64 +0.044 · 128 +0.006 · 192 +0.018 · 256 +0.003 · 320 +0.024 | 11 / 0 | 0.82 / 0.97 |
| seed3 | 2 | 0.463 | 64 +0.018 · 128 +0.051 · 192 +0.045 | 7 / 0 | 0.90 / 0.99 |
| seed4 | 2 | 0.467 | 64 +0.009 · 128 +0.030 · 192 +0.021 | 7 (+1 training) / 0 | 1.00 / 1.00 |

Totals: 21 paired checkpoints, 21/21 positive (min +0.003, max +0.051, mean +0.022 ≈ 2.0 base-panel SD); 6/21 exceed +0.03; 45 committed sleeps, 0 canary rejections; every life's canary mean ≥ 0.97 parseable-ACT.

## Bar items
1. **Absorption** (8 sleeps, seeds 0/1; values = base NLL − adapter NLL on the sleep's own rows, nats):
   - diagonal: seed0 3.25, 3.55, 3.30, 3.11, 2.88, 2.41, 2.41, 2.54; seed1 3.29, 3.13, 2.99, 2.92, 2.76, 2.76, 2.80, 2.58.
   - control (unrelated life's rows): rises 1.61 → ~1.95 by sleep 3 and plateaus in both lives — the dialect/format component saturates.
   - row-specific excess (diagonal − control): seed0 1.64, 1.72, 1.38, 1.17, 0.91, 0.46, 0.46, 0.64; seed1 1.68, 1.31, 1.04, 0.97, 0.84, 0.90, 0.83, 0.64. Declines across the life in both. The base model's own NLL on later rows also falls (4.34 → 3.17 / 4.36 → 3.32): later thinking is more templated and there is less to absorb. Consistent with the ritualized gym behaviour seen in the ledgers; not a mechanism claim.
2. **Retention** — for a fixed row set the delta is flat under every later adapter (sleep-32 rows: 3.26, 3.21, 3.21, 3.26, 3.30, 3.27, 3.28 under adapters @64…@256; seed1 likewise 3.28–3.35). No decay — but under the cumulative clean-base recipe earlier rows remain in every later training set, so this reads "still trained on", not forgetting resistance. Open question to Codex: whether a true held-out retention set is required for the bar.
3. **Interface preservation** — paired format canary passed on 45/45 committed sleeps (threshold ON ≥ 0.5 absolute in run_life_v2; the classroom uses the paired rule). Minimum observed rate 0.82. Dialect bifurcation (the R_B_seed2 collapse under the old writer) has not recurred under canonicalization + canary.
4. **No-harm** — 21/21 paired checkpoints non-negative; no life below its adapter-OFF panel at any checkpoint.

## What is NOT shown
- Transfer beyond the gym's own held-out programs; parent-absent transfer at the 7-day horizon; anything about rank 16 (r8 throughout); the classroom lineage results (separate, rule game).
- Caveat: node-1 lives seeds 0/1/5 were interrupted once (my process kill, 2026-09-08 ~02:00) and resumed from markers; the interrupted wake batch's partial rows were re-recorded. Checkpoints before the interruption (through ep256 for seeds 0/1) are unaffected.

## REVISION 2026-09-09 (supersedes the recommendation below)
Late-life recount, 9 lives, 82 paired probes: 69/82 positive; 9/82 harmful (< −0.03), all after episode 384, in 3/9 lives (seed5 −0.186 at 448; seed6 −0.089 at 448; seed2 −0.051 at 768). Every harmful sleep passed the format canary. Two mechanisms seen: behavioural collapse with perfect format (seed5: 1–2 chunks/episode vs base 13, canary 1.00), and a degraded adapter admitted at canary 0.67 after which all later writes were rejected, freezing the life on a bad adapter (seed2). Early life (≤320 episodes) remains 0 harmful in 9/9.
**Bar status:** absorption ✓, retention ✓ (cumulative caveat), interface — measured ✓ but the instrument misses behavioural collapse, no-harm ✗ beyond ~12 sleeps in 3/9 lives.
**Recommendation:** do NOT freeze as gated. Freeze only with a score gate at every sleep (candidate ≥ max(base, previous adapter) − 0.02 on the seeded paired mini-probe), a behavioural canary (chunks/episode ≥ 0.5 × base), a paired format canary, and a recovery path after repeated rejections. Reason code: LATE_HARM_3_OF_9_UNGATED. Consequence if wrong (gate too strict): fewer commits, slower growth — recoverable; consequence of freezing without it: a 7-day child can silently degrade after day 2 — not recoverable in the paper's timeline.

## Recommendation (superseded, kept for the record)
Freeze this recipe for the 7-day child (reason code: NO_HARM_21_21 + INTERFACE_45_45). Magnitude is small (+0.022 mean) and is not the claim; the claim is that the writer is safe to run unattended for a week with the canary as gate. Consequence if wrong: the child's adapter drifts undetected — mitigated by the ON/OFF probe every 64 episodes and the lineage fork policy.

## Gate evidence (2026-09-10)
Probe-gated life R3_B_seed500: 5 gated sleeps; the sleep-64 candidate collapsed to 2.1 chunks/episode (base 11.6) with a passing score and perfect format and was rejected by the behavioural canary; the previous adapter stayed; the life's paired probes are +0.042/+0.021. This is the seed5 failure shape caught before commit. Three more gated lives running (501–503).
