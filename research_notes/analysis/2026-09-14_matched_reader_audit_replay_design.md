# Matched actual-reader replay diagnostic

Prospectively declared September 14, 2026, after SEQ-245 and before new model
calls. Main owns execution. This diagnostic follows an observed success; it is
not a prerequisite for accepting or continuing that finite learning loop.

## Question

Does the original SEQ-239 taught auditor outperform its matched audit-loss-off
sibling on identical, newly captured A3 reader stimuli? SEQ-240 compared their
own differing stimuli. SEQ-241 subsequently supplied the 62 audit lessons to
both states. Therefore neither comparison alone isolates original teaching on
these fresh reader failures. Use the ORIGINAL SEQ-239 adapters, not descendants.

## Frozen comparison

- Input root: `/tmp/astra_fresh_reader_cycle_20260914_attempt2` on node2.
- Packets, in order: BEFORE (all eight faulty reads), SELECTED AFTER (all six
  true reads). Exactly 14 neutral audit prompts per arm, 28 total. No additional
  generation, parent, training, corrected answers or selected-row filtering.
- Source actor is the later A3 lineage; evaluated auditor is an original
  SEQ-239 sibling. Record both identities. This is third-party captured replay,
  NOT a claim that either evaluated auditor produced or experienced these reads.
- Both see identical grounded source tables and actual raw replies, in identical
  order, using the existing scorer and prompt bytes. Evaluation expected labels
  must not be passed separately to generation. Each call has a fresh context.
- Original adapters: `/tmp/astra_reader_audit_lesson_20260914_attempt1/`
  `{AUDIT_SFT,AUDIT_LOSS_OFF}/train/adapter`. Validate their original training,
  lesson and base receipts with existing native functions. Frozen base/rank.
- All wrong, malformed, truncated and errored outputs remain in denominators.
  Record exact response/case pairs and source-valid choices independently of
  correctness; no material from this diagnostic is written into learner weights.

Metrics: exact correctness and source-pointer admission, separately for 8 fault
and 6 true cases; false positive/negative counts; source-index confusion;
format failures. Report paired case differences, not a population p-value.
Prediction: SFT preserves the taught distinction better than loss-off. Equality
or reversal contradicts that narrow transfer advantage; do not tune this panel.
Neither outcome establishes downstream selection utility or H2.

These stimuli were selected AFTER inspecting A3 results, not an unopened
confirmatory panel. The two strata are state-dependent captures of four facts,
with repeated addresses. Report all 14 cases and four unique facts; do not call
them 14 independent environments. The eight BEFORE cases contain four unique
exact prompts; the six AFTER cases contain four unique exact prompts. These
eight unique stimuli, not their repeated copies, bound the distinct evidence.
SELECTED AFTER is chosen once for both arms;
do not search the uniform sibling for a favorable alternative.

## Execution and stop

New immutable run directory and source snapshot. CPU source replay before
launch; independent review proceeds in parallel. Node2 GPUs0/1 only after
physical plus CVD scan, with reservations preserved during model loading.
At most 1920 seconds/arm including teardown, 1.067 reserved A40-hours total;
no fits, tokenizer-only exploration or extra seeds in this diagnostic. Normal
six-hour lease margin. Technical failure preserves captures, permits only a
new explicit repair attempt, and never triggers a repeat fit. Successful or
negative results inform the next data/learning experiment; no efficacy sweep.
