# Static teacher-present competency check: independent watcher design audit

Date: 2026-09-12. Status: **prospective watcher audit; no model or GPU result
inspected**. This reviews builder commit
`b39e92381a848b19f8a9578aca79fee20de24894` and does not edit builder code,
launch or stop a job, train an adapter, or authorize a parenting claim.

## Bottom line

**GO for one cheap static-instruction manipulation scout. NO-GO for calling a
two-arm result useful parenting by itself.** The implementation cleanly asks
whether one fixed answer-free `FORM_CHECK -> CONSTRAINT_LEDGER` note changes a
frozen child's first action relative to a same-position, same-opportunity,
Qwen-token-matched sham. It does not contain a parent model, adaptation,
feedback-conditioned advice, child learning, persistence, DREAM, or SLEEP.

The essential third observation is a **no-teacher anchor on the same tasks and
seeds**. Without it, `process > sham` can again mean only that sham was more
harmful. The anchor need not be token matched and is not part of the causal
process-versus-sham contrast; it locates both treatments relative to ordinary
behavior. It should be frozen before either treatment outcome is inspected.

## Exact minimal geometry

Use the already selected first 16 mini-Sudoku train IDs,
`rg/mini_sudoku/1850000` through `1850015`, in that order. These are a DEV
panel, not held-out transfer. They offer a deterministic public verifier,
partial credit, large base headroom, and visible form/row/column/box
constraints that make both proposed process moves testable.

For every condition:

- start the same locally pinned frozen Qwen2.5-7B-Instruct base with no
  adapter, retrieval, prior ledger, parent state, or write;
- use one fresh worker process, one wake call per question, one tick, batch
  size eight, temperature 0.7, 400 generated-token cap, and per-question seed
  derived from generation seed 7101;
- preserve the full rendered prompt, raw output, parsed ACT sequence, public
  verifier result, tokenizer counts, loader identity, and cleanup receipt;
- retain missing or malformed first ACTs as zero and never replace them or use
  a later ACT as the primary.

The two causal packages enter once at the same location immediately after the
common birth prompt. The native tokenizer must show 97 versus 97 package
tokens **and exact equality of complete rendered-prompt token counts for every
paired question**. Each arm gets exactly 16 presentations and 6,400 reserved
output tokens. Realized output length is an outcome to report, not something
to equalize post hoc.

The no-teacher anchor uses the identical base, tasks, order, generation seeds,
temperature and output cap but omits the entire teacher-note block. Its shorter
input means it is an absolute descriptive anchor, not a third token-matched
treatment. If a second panel is warranted, freeze IDs `1850016` through
`1850031` before reading this panel's result and reverse/counterbalance the
process/sham execution order.

## Visibility and answer-leakage boundary

No parent model runs in this diagnostic. “Teacher” means immutable generic
text authored before outcomes:

- the child sees the fixed package, its current puzzle question and givens,
  the ordinary interface instructions, and no previous action outcome;
- the process package does not see or encode the puzzle instance, reference
  solution, score, action, apply item, or any result-selected information;
- the hidden answer remains confined to the strict native verifier after the
  ACT is dispatched; it is never serialized into the prompt, package, model
  input, or output-selection logic;
- package bytes, question IDs, order, request seeds and all endpoints freeze
  before generation. No retry, answer-aware rewrite, question replacement or
  text tuning follows the result.

The process note is intentionally more task-relevant than the sham; that is
the semantic treatment. Token matching controls dose and position, not
meaning, naturalness or attention. The common birth prompt already tells the
child to read rules, judge itself and investigate, so a result estimates the
incremental value of these two concrete procedures on top of that bootstrap,
not the value of teaching from scratch.

## Useful-behavior endpoints

The primary world endpoint remains the **native score of the first ACT**, with
malformed/missing first ACTs zero-filled. Report its paired task vector, mean
and exact-solve count. Exact solve is valuable but too coarse to be the sole
readout on 16 boards.

Add answer-free structural diagnostics computed only from the submitted grid
and visible givens:

1. first ACT present;
2. canonical 4-by-4 grid with values 1--4 and no extra field;
3. fraction of visible givens preserved;
4. valid rows out of four, valid columns out of four, and valid 2-by-2 boxes
   out of four.

These localize `FORM_CHECK` and `CONSTRAINT_LEDGER`; they are not substitutes
for public verifier score. Thought length, lexical overlap with the card,
marker count, plan-like prose and teacher imitation are diagnostics only and
can never constitute success.

For each outcome `Y`, report paired task differences
`D_PS = mean(Y_process - Y_sham)`, `D_P0 = mean(Y_process - Y_none)` and
`D_S0 = mean(Y_sham - Y_none)`. Interpret results in this order:

- `D_PS > 0` but `D_P0 <= 0`: relative contrast only; sham harmed more;
- positive structural diagnostics without positive native score: compliance
  or format shift, not useful action improvement;
- positive native score versus both sham and none, no availability/format
  regression, and non-worse exact solves: immediate useful effect of this
  fixed process package, worth an outcome-blind second-panel replication;
- null/negative process contrast: inspect first-ACT format and visible
  constraint failures, then revise teaching before collecting any corpus.

No p-value over 16 boards licenses a learner-population claim. The scientific
unit for repeatability requires a new task panel and generation seed; future
adaptive-parent evidence additionally requires new parent decisions.

## Audit of the landed implementation

The current code already enforces the main two-arm mechanics: fixed packages,
fresh no-adapter base identity, strict native verifier, same 16 tasks and
seeds, exact native token/prompt-length preflight, one presentation and equal
reserved budget per task, raw-output preservation, first-ACT scoring, no NOTE
gate, no optimizer/lineage call, sealed inputs and fresh outputs. I reran its
synthetic suite locally: **18/18 tests passed**.

Before treating a run as a fully bound DEV result, verify four remaining
items in the actual preparation/capture:

1. the caller supplied exactly `TRAIN_IDS[:16]`; the function currently
   permits any 16-member subset even though the prose fixes the first 16;
2. reasoning-gym is exactly version 0.1.25 and the captured dependency
   inventory includes the imported mini-Sudoku parser/material module and
   prompt/state path, not only the top-level driver files;
3. the actual cached Qwen tokenizer, not the synthetic test tokenizer,
   produces the declared 97/97 package and per-question rendered-prompt match;
4. add or pre-freeze the no-teacher same-task anchor before interpreting
   `process > sham` as absolute utility.

## Claim ceiling

A replicated positive can support only:

> A fixed, answer-free process note caused the frozen model to produce better
> first actions on these matched puzzle panels than a token- and
> opportunity-matched sham, with an ordinary no-teacher anchor ruling out a
> sham-only degradation explanation.

It cannot support adaptive parenting, learning how to learn, metacognition,
internalization, parent removal, LoRA transport, continual learning, DREAM,
SLEEP, or a whole-organism claim. Its value is diagnostic: if the advice does
not help while visible, another write experiment cannot reveal whether the
writer or the lesson failed. If it does help, only then should child actions
and outcomes under the helpful package enter a separately controlled
amortization experiment.
