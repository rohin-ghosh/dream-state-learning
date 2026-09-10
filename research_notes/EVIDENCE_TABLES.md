# Evidence tables (numbers a paper may use), compiled 2026-09-10 by Fable

All values are cell counts / measured means from `research_loop/COORDINATION.md` (dated entries). Raw probe/gate JSON lives on the GPU nodes under `~/v6_out/`, not in the repo. Anything not in this file or COORDINATION.md must be marked "not measured".

## Setup constants
- Child: Qwen2.5-7B base (frozen) + LoRA rank 8 (r16 tested, no difference). Sleep every 32 episodes; probes every 64 (8 sealed CompilerGym programs, seeded 777, adapter ON vs OFF at the same episode).
- Gym: CompilerGym llvm-v0, IrInstructionCount reduction (0.487 = programs shrink 48.7% on average). Base panel 0.4936 ± 0.0113 (9 reps).
- Rule game (teaching classroom): hidden rule over 3 numbers, probe then quiz. Exam noise SD: 0.067–0.072 at 8 episodes; 0.030–0.044 at 40; 0.033 at 80 (noise floor is run-to-run, not episode sampling).
- Writers: v1 frozen (bare-text LM loss, lr 1e-4, 3 epochs, cumulative from clean base) for all long lives; v2.1 (chat-masked, response-only loss, lr 3e-5, 2 epochs) for classrooms, rank cells, bootstrap.
- Parents: Qwen2.5-14B-Instruct (vLLM server); Qwen2.5-32B-Instruct-AWQ single-GPU (TP=2 bf16 hung 3× on A40s). Parent weights never learn; answer-aware-but-withholding; leak scan on every utterance.

## Writer recipe (write-swarm, fixed 130-row corpus, n=2): plain 0.466 / +paraphrase 0.496 / +replay-mix 0.494 / +both 0.489 (base ≈ 0.485–0.494).

## Rank × dose (probe mean; base ≈ 0.494)
| rows | r8 | r16 |
|---|---|---|
| 300 | 0.485 | 0.488 |
| 1,200 | 0.492, 0.506 (2 nodes) | 0.456, 0.515 |
| 12,031 | 0.413, 0.440, 0.468, 0.491, 0.343 (mean 0.431) | 0.473, 0.504, 0.453, 0.502, 0.434 (mean 0.473) |
Large one-shot writes land below base (r8 5/5, r16 4/5). Same-config replicate gaps up to 0.078 (trainer had no seed; added). Decision: r8; DOSE_HARM is the primary finding.

## Fixed-writer lives, ungated (R2, 9 lives, 82 paired probes)
69/82 positive; 9/82 harmful (< −0.03), all after episode 384, in 3 lives (seed5 −0.186 at 448; seed6 −0.089; seed2 −0.051). Every harmful sleep passed the format canary. Early life (≤320): 0 harmful in 9/9. Mechanisms: behavioural collapse with perfect format (1–2 chunks/episode vs base 13); degraded adapter admitted at canary 0.67 then frozen by later rejections.

## Gated lives (R3, probe gate: candidate ≥ max(base, previous) − 0.02 and chunks/episode ≥ 0.5 × base)
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
