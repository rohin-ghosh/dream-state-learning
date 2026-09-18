# R171 registered text-only scalar ranker — September 17, 2026

Rohin170/171 via Main/Astra supersedes the soft3class humor contrast. No new
human ratification is inferred. Existing V6 remains non-usable with null tau;
V7 failed CPU setup, V9/V10 ran CPU-only and will never launch humor training.
Their source/plans/receipts remain preserved. Image-judge training is HOLD.

## First bounded strong-text proof

Use cached **Qwen/Qwen2.5-7B-Instruct** revision
`a09a35458c702b33eeacc393d103063234e8bc28`, ten hash-bound runtime files,
15,242,787,925bytes. This is not the authors' reward checkpoint and not a claim
of pretrained humor competence. Frozen backbone, new scalar score head and
rank8 LoRA on q_proj/v_proj, alpha16/dropout0.05; only LoRA and score train.
No child, parent, learner base, provider or local-vision operation changes.

Labels are **empirical (somewhat+funny)/votes**, NOT mean rating; those orderings
can disagree and the CPU regression tests explicitly demonstrate that case.
Sample a contest uniformly and two distinct captions uniformly from its full
available fitting corpus. Captions can participate in multiple comparisons.
Skip exact q ties. Pair loss is genuine Bradley–Terry negative log-likelihood:
`softplus(-(2*winner-1)*(scalar_left-scalar_right))`, weighted by the minimum
capped vote fraction times min(1, absolute empirical q gap / combined Jeffreys
posterior standard error). Cap=100 votes; no softCE humor or q-difference MSE.

CPU preparation fixes the actual pair plan before launch. Original<=50word and
512token input constraints stay unchanged, without truncation. Candidate pairs
exceeding token length are rejected before model I/O and counted, never silently
claimed as trained; they are not filtered by held outcomes. All held rows must
fit unchanged or the gate fails. The earlier all-row legacy CPU warnings do not
authorize truncation or a positive receipt.

Up to1000 optimizer updates, two pairs/microbatch and four gradient-accumulation
microbatches: at most8000 comparisons/16000 caption draws from the available
180-contest fitting corpus. Reuse is permitted, not a full corpus/epoch claim.
AdamW LR1e-4, gradient norm cap1.0, BF16 frozen backbone, SDPA, nonreentrant
gradient checkpointing. Actual throughput and completed comparisons are receipts,
not a promised duration. Save first optimizer event and throughput every10steps.

Select adapters only by macro within-contest scalar Spearman (pairwise concordance
tie-breaker) on registered model-selection19×64 rows; evaluate at step1 and every100
updates. Report sampled per-contest top5 vote mass and sample counts. This is NOT
literal full-contest top200 performance; that remains unmeasured in this bounded
proof. No retrospective V6 checkpoint promotion or author-release substitution.

Calibrate scalar scores using monotone, unweighted isotonic regression to real
positive-vote mass on the13×64 natural probability-calibration rows. q retains
that vote-mass meaning, NOT Bradley–Terry pairwise win probability. Choose tau on
the7×64 threshold rows using the unchanged mean-mass>=0.30/coverage>=0.05 objective;
retain null if infeasible. Calibrated-q Brier is binary vote-mass Brier, not V6's
three-class Brier. Frozen corrected V6 scene-fit head/threshold remains separate,
explicitly step100 and weak/synthetic; no old humor head is loaded or optimized.
Report combined coverage, null tau, vote-mass proxies and signed/absolute changes
for scene swaps, broken punchlines and prompt attacks on registered reused dev.

The6×64 dev audit is disjoint from fitting/selection within this run but reused
across development: PROVISIONAL, not fresh locked-test evidence. Locked validation
and FINAL are not read. No human-validation/top200-precision claim; second blind
comparator incomplete. Main receives only aggregate results and artifact refs.

## Execution boundary

Only node4 physical2 UUID `GPU-35dcea35-12bc-f2f3-d5d2-d2eaa8bacdd8`, kernel minor1,
with strict systemd policy, actual target open/close and seven foreign-minor
denials, fresh clear capacity and own bound CPU/provenance receipt. At most2400s
including load/calibration/audit; reserve600s for calibration before the fixed end.
The allocation still ends September17 13:59:35.272466PDT. No lease extension, new
review queue, retry, multimodal comparator or another device. Failure is preserved.
