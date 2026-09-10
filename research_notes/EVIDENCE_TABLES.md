# Evidence tables (numbers a paper may use), compiled 2026-09-10 by Fable

All values are cell counts / measured means from `research_loop/COORDINATION.md` (dated entries). Raw probe/gate JSON lives on the GPU nodes under `~/v6_out/`, not in the repo. Anything not in this file or COORDINATION.md must be marked "not measured".

## Setup constants
- Child: Qwen2.5-7B-Instruct (frozen; snapshot a09a35458c702b33eeacc393d103063234e8bc28; "base"/"OFF" below means adapter OFF) + LoRA rank 8 (rank unresolved at n ≤ 5; see rank table). Environment (both nodes): torch 2.13.0+cu130, vLLM 0.27.1, PEFT 0.20.0, transformers 5.5.3, driver 580.173.02. Sleep every 32 episodes; probes every 64 (8 CompilerGym programs held out BY IDENTIFIER; the curriculum contains same-source siblings of 4–6 of them; seeded 777 for batch generation only — sleep THINK-calls and single calls are unseeded; adapter ON vs OFF at the same episode). In gated lives (R3/R4) the gate uses this same panel and seed, so their ON numbers are post-selection.
- Gym: CompilerGym llvm-v0, IrInstructionCount reduction (0.487 = programs shrink 48.7% on average). Base panel 0.4936 ± 0.0113 (9 reps).
- Rule game (teaching classroom): hidden rule over 3 numbers, probe then quiz. Exam noise SD: 0.067–0.072 at 8 episodes; 0.030–0.044 at 40; 0.033 at 80 (noise floor is run-to-run, not episode sampling).
- Writers: v1 frozen (bare-text LM loss, lr 1e-4, 3 epochs, cumulative from clean base) for all long lives; v2.1 (chat-masked, response-only loss, lr 3e-5, 2 epochs) for classrooms, rank cells, bootstrap.
- Parents: two different parents share the name — the CLASSROOM parent (answer-aware critic, fires every lesson, rule game; leak scan blocked 1/32 exact-phrase, word-level scanner leaves 5/32 delivered utterances with rule-descriptor words; 32B: 21/96 replaced by fallback) and the PATTERN parent (ritual-triggered brief in the gym; six-pass regex with a quote-back exemption since 09-10; 4/16 and 6/14 v3 briefs fell back before the fix). Qwen2.5-14B-Instruct and Qwen2.5-32B-Instruct-AWQ (TP=2 bf16 hung 3× on A40s). Parent weights never learn.

## Write-swarm (OFFLINE SCREEN, n=2, third trainer lr 5e-5, dose-confounded per Codex; NOT the writer used in any life): plain 0.466 / +paraphrase 0.496 / +replay-mix 0.494 / +both 0.489 (base ≈ 0.485–0.494).

## Rank × dose (probe mean; base ≈ 0.494)
| rows | r8 | r16 |
|---|---|---|
| 300 | 0.485 | 0.488 |
| 1,200 | 0.492, 0.506 (2 nodes) | 0.456, 0.515 |
| 12,031 | 0.413, 0.440, 0.468, 0.491, 0.343 (mean 0.431) | 0.473, 0.504, 0.453, 0.502, 0.434 (mean 0.473) |
Recount vs the unseeded 0.494 panel: r8 5/5 below, r16 3/5 below (0.473, 0.453, 0.434). Confounds: trainer (v2.1 for cells vs v1 for lives), corpus provenance (pooled from early lives; contains 51 rows of the probe programs — NOT sealed), base reference (unseeded single-stream panel at budget 24 vs cells at budget 16). Frequency is not isolated (every sleep retrains from the frozen model). Rank: r16 > r8 in 4/5 seeded pairs at 12k, mean +0.042, SD 0.043, 90% CI [+0.001, +0.083] — not resolvable. Same-config replicate gaps up to 0.078; v2.1 trainer had no seed (added 09-07); v1 trainer still unseeded.

## Fixed-writer lives, ungated (R2, 9 lives, 82 paired probes)
69/82 positive; 9/82 harmful (< −0.03), all after episode 384, in 3 lives (seed5 −0.186 at 448; seed6 −0.089; seed2 −0.051). Every harmful sleep passed the format canary. Early life (≤320): 0 harmful in 9/9. Mechanisms: behavioural collapse with perfect format (1–2 chunks/episode vs base 13); degraded adapter admitted at canary 0.67 then frozen by later rejections.

## Gated lives (R3, probe gate: candidate ≥ max(base, previous) − 0.02 and chunks/episode ≥ 0.5 × base) — GATE AND REPORT PANEL ARE THE SAME 8 PROGRAMS AND SEED: these ON numbers are post-selection statistics; disjoint-panel re-probe pending. Same-adapter same-seed replicates swing up to ±0.019–0.045 (recipe-choice variance).
As of 2026-09-11: 500: 9 pairs mean +0.039, 5 rejections (incl. a 0.270 candidate vs 0.527 floor); 501: +0.016, 0 rej; 502: +0.055, 10 rej; 503: 11 pairs +0.022, 4 rej; 504/505 young. 0 harmful in all gated pairs.

## Parented lives (RP, ungated, briefs v1→v3)
400 (14B): 16 pairs, min +0.006, max +0.063, mean +0.038, 0 harmful, full life. 401 (14B): 16 pairs, mean +0.016, 0 harmful, full life. 402 (32B-AWQ): 12+ pairs, mean +0.014, 0 harmful. Rehearsal rate (episodes whose first NOTE restates the brief): 0.50–1.00.

## Ritual onset (≥2 of: same recipe, flat predictions, templated notes, same recall; 32-episode windows)
Unparented: first flag at 160–224 episodes in 8/9 lives with ≥320 episodes; persists (R in ~80–100% of later windows); one life (seed3) never sustained and is the best scorer (+0.065). Parented: onset 288 (400), 192 then 4-window remission then 352+ (401), 256 (402); persists afterwards despite 3–9 briefs.

## Absorption / retention (base NLL − adapter NLL, nats; 8 sleeps, 2 lives)
Own rows: 3.3 → 2.5 across the life. Unrelated life's rows (control): 1.6 → 1.95, plateau by sleep 3. Row-specific excess: 1.7 → 0.6. Retention flat (cumulative training; "still trained on"). Behaviour moves ~+0.02 while storage is ~3 nats: storage ≠ extraction.

## Classroom lineages (rule game, 3 rounds, 40-episode exams, ON−OFF per write)
14B-parented, 9 lineages / 27 writes: > +0.03 in 8, < −0.03 in 8; lineage means ≥ 0 in 4/9. Best round-0 writes: +0.167, +0.121, +0.100, +0.100. Self-taught, 8 lineages / 24 writes: > +0.03 in 4, < −0.03 in 11; means ≥ 0 in 3/8. Seed-to-seed variance exceeds the arm difference. Commit rule defect found: 5 writes committed below the adapter they replaced; 2 collapses (ON 0.071, 0.100) rejected by HARM. Single-round writes (n=8 cells at 40 eids): 1/8 positive.

## Bootstrap corpora (2026-09-11)
v3 target-blind (rule-game classrooms): 470 rows (metaflow 206, opening 94, contrast 70, review 65, full 35), no ritual flags. v2/v1 from a CompilerGym-exposed child: 370 / 552 rows, QUARANTINED development-only. Adapters: training queued.

## Infra facts worth one sentence each
Dialect bifurcation cured by canonicalization + real-context paired canary; trainer nondeterminism measured; 32B TP=2 hangs on A40s (use AWQ single-GPU); marker-file resume for lives.

## Addendum 2026-09-10 (SEQ-001; source: COORDINATION.md entry "SEQ-001"; JSON in research_notes/analysis/)
- **Unit of analysis = life.** Full 1024-episode lives: ungated R2 (9): life means +0.037, +0.050, −0.000, +0.045, +0.022, −0.051, −0.005, +0.050, +0.028; lives with ≥1 harmful pair 4/9 (seeds 2, 3, 5, 6), with ≥2 harmful 3/9. Parented RP (3): +0.038, +0.016, +0.011; 1/3 with a harmful pair (402, −0.039). Gated R3 (6, none at 1024 yet): +0.042, +0.016, +0.056, +0.021, +0.037, +0.028; 0 harmful — POST-SELECTION (F1). Restarts per life recorded (RP 3–4; R2 seeds 0/1/5 one each).
- **Noise from disk:** SD(adapter-OFF probe mean) = 0.0092 / 0.0087 (n=157 / 153); SD(paired ON−OFF) ≈ 0.013 under independence; same-adapter same-seed replicate SD = 0.0064 / 0.0067 (n=33 / 37). Mean OFF on the life probes is 0.471–0.474, not the 0.494 of the unseeded panel (budget/seeding differ).
- **Per-program:** the gain is carried by patricia (+0.11 / +0.16) and gsm (+0.03 / +0.04), with dijkstra ~0 to +0.02; susan, sha, jpeg-c, tiff2bw, stringsearch average slightly negative (−0.03 to 0). Twin-free programs: patricia positive, sha negative.
- **Fixed-recipe reference (M5):** birth recipe alone, no model = 0.4878 mean on the 8 probes (per program 0.538, 0.537, 0.389, 0.521, 0.508, 0.471, 0.439, 0.499) — identical to the adapter-ON plateau. -Oz/-O3: not yet computed.
- **Ritual is in the weights (M12):** probe ledgers with identical BOOTSTRAP-only context — adapter ON: modal first-action share 0.90 / 0.86, fully locked in 68% / 52% of checkpoints, note Jaccard 0.62 / 0.59; adapter OFF: 0.50, 0%, 0.105.
- **Disjoint panel v1** defined (12 out-of-curriculum programs; research_notes/disjoint_panel_v1.json); re-probe pending GPU.
- **Echo metric (M7, SEQ-003):** RP first-note overlap with the brief: 0.454 after a brief vs 0.322 before the life's first brief vs 0.354 for unbriefed control lives against the same briefs (47 briefs, 8 controls). "Rehearsal 0.50–1.00" is withdrawn.
- **Compiler references (M5, SEQ-003):** 8-probe means — -Oz 0.522, -O3 0.341, birth recipe once 0.4878; adapter plateaus 0.4878 and 0.5291; exploring frozen model 0.463–0.488.
- **Efficiency over cycles (SEQ-005):** chunks-to-best per episode roughly doubles from early (cycles 2–4: 3–4) to late life (6–9) in every arm, taught or not; contrast phrases and backtracks per episode fall to ~0; first-ACT distribution shift between consecutive cycles is small everywhere (JS 0.02–0.13). No taught-vs-untaught separation on efficiency. Source: SEQ-005; JSON in research_notes/analysis/.

## Addendum 2026-09-10 (erratum and life-level cells; source: COORDINATION.md entry "[Fable meta-review] 2026-09-10 — ERRATUM to SEQ-001 prose", recomputed from the SEQ-001 JSON)
- **Correction to the SEQ-001 sentence "7/9 ≥ +0.02, 2/9 negative":** R2 life means are 6/9 at or above +0.02 and 3/9 below zero (the nine values in the addendum above are correct; the count was not). Mean of life means +0.019 (SD 0.033, SE 0.011, n = 9). Early-life (episodes 64–320) means positive in 9/9; late-life (384–1024) means negative in 3/9.
- **Per-pair harm episodes (R2):** seed 5 at 384–704 (every probe), 896, 1024; seed 6 at 448, 576; seed 2 at 640, 704, 768, 832, 1024 (one pair rounds to −0.030); seed 3 at 1024. First harm 384, last 1024; last probe pair harmful in 3/9 lives. Pair count 17 / 16 / 14 at thresholds −0.025 / −0.03 / −0.031; lives with harm 4/9 at every threshold from −0.025 to −0.04.
- **Old writer seed 0:** full life, 16/16 positive pairs, mean +0.027.
- **Pool composition:** the per-program and M12 ritual numbers pool all arms per node (node 1: R2 64, R3 37, R4 9, RP 16, old writer 31 pairs; node 2: R2 80, R3 23, R4 18, RP 32). **R2-only ritual in the weights (ON):** modal share 0.914 / 0.804, fully locked 0.61 / 0.39, note Jaccard 0.619 / 0.583 (OFF: 0.50 / 0 / 0.105, constant across checkpoints).
- **Disjoint panel v1, interim (SEQ-009, 17 cells, ungated):** base 0.257/0.254; birth recipe = 0.2495 on this panel (below base); six-pass routine = 0.2731 (+0.016…+0.019). Mid-life adapters 4/8 above base; final adapters 1/9 above base, 4/9 with a collapsed rep (0.18–0.21). Gated adapters pending.

## Addendum 2026-09-10 (SEQ-011; the next experiment's F1 ruler and section-2 cell counts; source: COORDINATION.md entry "SEQ-011", computed by `research_notes/analysis/seq011_from_json.py` from the SEQ-001 and SEQ-005 JSON)
- **Cycle-16 estimator per life** (mean of the paired ON−OFF at episodes 448 and 512): gated R3 500/501/502/503 = +0.051 / +0.016 / +0.066 / +0.011 (mean +0.036; **between-life SD 0.0266, n = 4** — the ruler for the D-vs-B null); R2 seeds 0–8 = +0.052, +0.045, +0.022, +0.065, +0.024, −0.152, −0.056, +0.060, +0.052 (**SD 0.0717, n = 9**; the six with < 2 harmful pairs, seeds 0/1/3/4/7/8: **SD 0.0143**; the five with none: 0.0136); RP 400/401/402 = +0.039 / +0.012 / +0.022; old writer R seed0 +0.023, R seed2 −0.452.
- **Same-adapter replicate SD, pooled:** 0.0066 at n = 70 (0.0064 at n = 33 and 0.0067 at n = 37, pooled variance).
- **Windows with undefined chunks-to-best** (SEQ-005 instrument; None when no `[OUTCOME]` echo in the window): R2 seed6 27/32, seed4 13/32, seed5 11/32, seed2 9/32, seed3 6/32, seeds 7/8 4/32, seed0 2/32, seed1 0/32; R3 500 12/32, 501 7/28, 502 4/32, 503 9/32; RP 401 3/32, 402 1/32; R4 0–4 undefined of 9–19 windows. The early→late "doubling" of chunks-to-best is confounded with the child ceasing to echo outcomes.
- **Late-life chunks per situation** (mean of the last three windows; budget 16): 15.4–16.0 in R2 seeds 0/1/2/4/7/8, R3 503, R4 604/605/606, RP 402; below the band: R2 seed3 12.8, seed5 5.4, seed6 1.0; R3 500 6.6, 501 12.8, 502 9.7, 504 14.4, 505 2.5; R4 600 13.9, 602 13.1, 603 15.3; RP 401 7.8.
- **Instrument defect:** efficiency_markers has no cells for RP 400 (parser error on an elided `[OUTCOME]` score).

## Addendum 2026-09-10 (SEQ-012; disjoint panel v1 at 24 cells; source: COORDINATION.md entry "SEQ-012")
- **R2 final adapters (9):** Δ vs node base −0.043, +0.016, −0.005, −0.018, −0.005, −0.038, −0.036, −0.026, −0.003 (seeds 0–8); mean −0.017; 1/9 above +0.015 (seed 1 = routine 0.2731), 5/9 below −0.015 (all with a collapsed rep 0.18–0.21).
- **R2 mid-life adapters (sleep 416, 9):** +0.016, +0.016, −0.005, +0.019, −0.005, −0.014, −0.008, +0.017, +0.010; mean +0.005; 4/9 above +0.015, 0/9 below −0.015. Final − mid: 0.000 ×3, negative ×6 (−0.013 to −0.059); positive ×0.
- **Above-base cells are the routine:** all above-base cells but two (R2 seed7 mid 0.2712, RP 400 final 0.2713) equal 0.2731 to four decimals, the six-pass routine applied to every program.
- **RP:** 400 final +0.017, mid −0.002; 402 final −0.009, mid −0.008. **R3 500 (gated):** committed final (sleep 608) +0.005; mid +0.016. Bases: node 1 0.2574 (reps 0.2506/0.2542/0.2675), node 2 0.2541 (0.2463/0.2601/0.2559).
- **Gate catches to date with a passing score (brevity rule):** R3 500@64, 501@704, 505@288, 505@832. Score catches: R4 606@576 (0.307), R4 603@640 (0.421), R3 500@960/992/1024 (0.337/0.347/0.210).
- **Disjoint-panel gate (R5 700):** gate base 0.2589; first two candidates 0.2565 / 0.2566 accepted inside the 0.02 tolerance (proposal: 0.01 for seeds 701+).
