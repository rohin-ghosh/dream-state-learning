# Smallest generic bootstrap test after the alignment null

**Date:** 2026-09-13 UTC  
**Scope:** design audit only; no source, model, tokenizer, training, GPU, child,
or scientific execution changed  
**Priority:** useful parallel diagnostic, explicitly **not** on the PCFL critical
path

## Decision in one paragraph

The terminal alignment assay did not show that the child ignored advice. Manual
review found all `24/24` lesson restatements semantically faithful. It showed a
later break: `0/48` exact process uses and `0/48` faithful records in every arm.
Part of that zero came from an underdisclosed and overly lexical expression
interface; part was genuine failure to turn an understood lesson into the
required state, action, and complete own record. The smallest clean follow-up is
therefore a staged test: first disclose and calibrate one neutral output contract
equally for every child, with no fit; then compare a **generic operational birth
adapter**, a form-matched copying adapter, and no adapter under the same new
ALIGNED-versus-SWAPPED parenting test. The primary result is the interaction:
does the true bootstrap increase the benefit of *relevant* advice, rather than
merely improving formatting or globally changing behavior?

## What is being tested

The bootstrap is a one-time, researcher-prepared post-training stage before
parenting. It is not DREAM, SLEEP, lived experience, or self-learning. It asks a
narrow question:

> Can generic practice converting answer-free process advice into an
> operational state, an action, and a grounded own record make a later unseen
> piece of parenting advice more usable?

THINK/DREAM/SLEEP remain simple and unchanged. This assay ends before SLEEP. If
it succeeds, its grounded child continuations may later be used in a separately
qualified SLEEP test. Parent words themselves do not become SLEEP targets.

## Stage 0: fix the interface without calling it learning

Freeze one task-independent envelope and give it to **every** later arm:

```text
STATE  = selected public identifiers + named operation + operation result
ACTION = one value from the task's public action grammar
RECORD = address + source + event
```

The prompt specifies the exact keys, value types, and serialization, but never
says which evidence to select, which operation is appropriate, or which action
is correct. Run `16` trivial copy fixtures per root in which every field value is
explicitly supplied. Require at least `15/16` parseable, structurally complete
outputs in each of three roots before any fit.

This is an interface calibration, not a behavioral result. Exact syntax and
semantic correctness remain separate scores. If it fails, repair the common
contract and stop; changing rank, corpus, parent, or plasticity cannot diagnose
an interface the child cannot reliably express.

## Stage 1: two matched birth fits plus an unchanged anchor

Use three fresh, disposable, task-naive roots. For each root create:

1. **TRUE birth.** Target-blind examples in unrelated microdomains show a new
   process instruction, a public state, the child's own concise operational
   state and action, the real world response, and the child's faithful record.
2. **FORM birth.** The same situations, assistant targets, supervised response
   tokens, update count, and replay dose, but the correct operational state is
   supplied in the input. This trains the interface/copying route without
   requiring the model to infer and apply the instruction.
3. **OFF.** The unchanged root. This prevents a harmful FORM adapter from
   manufacturing a false TRUE advantage.

For TRUE, the answer-free **process instruction remains in the training
input**. An additional fixed elicitation scaffold may initially help generate a
successful continuation, but that extra scaffold is removed from the stored
input. Only the child's world-checked assistant turns receive loss: first
`STATE+ACTION`, then, after the immutable world response, `RECORD`.
Instruction/scaffold text, world text, and rejected drafts are loss-masked.
FORM receives the same process instruction and assistant targets but retains
the filled operational state in its prompt. Match prompt length with
content-neutral padding and report any residual difference.

Train on generic operations different from the later parenting skills—for
example, choosing one discriminating experiment, recognizing that a subgoal is
complete, and revising one belief while preserving an unrelated belief. Use at
least three unrelated task families and hold out a fourth whole family. Do not
use P/C lesson examples, PCFL material, CompilerGym programs or passes, final
task identities, repo solutions, or any descendant of a task-exposed child.

Keep the writer fixed across TRUE and FORM: fresh clean base, rank `8`, and one
predeclared response-masked SFT dose. Inherit whichever preservation-replay
recipe has independently qualified before launch; do not make this bootstrap
test choose, tune, or delay that writer. This is a data comparison, not a
rank/heat/replay sweep. Both fitted children and all descendants remain
DEV-only.

Before parenting, the held-family birth screen must show that TRUE produces
more complete state-to-action-to-record chains than FORM and OFF, not merely
more parseable JSON. A practical DEV screen is `16` cases/root, TRUE at least
`+4/16` over both anchors in two roots, no root worse by more than `2/16`, and
no generic-interface or action-validity loss. If this fails, the bootstrap did
not install the proposed habit; do not interpret a later parenting difference.

## Stage 2: the minimum parenting-receptivity factorial

Fork every saved TRUE, FORM, and OFF birth into two inference-only arms:

| birth | relevant lesson | yoked wrong lesson |
|---|---|---|
| TRUE | TRUE-ALIGNED | TRUE-SWAPPED |
| FORM | FORM-ALIGNED | FORM-SWAPPED |
| OFF | OFF-ALIGNED | OFF-SWAPPED |

Use fresh target-blind P/C-like operations that were completely held out from
birth. Each fixed answer-free lesson is delivered twice. The child restates it
in its own words; on the measured task, only that child restatement and the
common neutral envelope remain. The parent lesson itself, source transcript,
hidden answer, and previous task outcome are absent. ALIGNED and SWAPPED use
the same lesson bytes, task bytes, order, and token opportunity; only the
lesson-to-task correspondence changes.

Score a strict, world-checkable chain on `16` tasks/root:

```text
FULL_CHAIN = correct operational state
             AND valid executed action
             AND faithful address+source+event record
```

Also report every component. Restatement is a manipulation check using a
prospectively frozen semantic predicate or blinded judge; it is not the primary
endpoint and must not reuse the terminal lexical matcher.

For birth `b`, define lesson usability as:

```text
A_b = FULL_CHAIN(b, ALIGNED) - FULL_CHAIN(b, SWAPPED)
```

The bootstrap earns further work only if, in at least two of three roots:

- `A_TRUE >= +4/16` and no TRUE root has `A_TRUE < 0`;
- `A_TRUE - A_FORM >= +3/16`;
- `A_TRUE - A_OFF >= +3/16`; and
- TRUE-ALIGNED does not reduce action validity or the generic canary by more
  than `1/16` relative to its own anchors.

These are screening thresholds, not population significance claims. Preserve
all tasks and paired counts. Do not select roots, later rows, rank, or dose from
the outcomes.

## How to read every result

- **Stage 0 fails:** expression interface is still broken; nothing about
  learning or parenting follows.
- **TRUE beats FORM/OFF before parenting, but all `A_b` are equal:** the birth
  taught a useful generic routine, not increased receptivity to advice.
- **All ALIGNED arms beat SWAPPED equally:** the base model already uses the
  lessons once the interface is clear; bootstrap is unnecessary.
- **TRUE has the uniquely larger aligned-minus-swapped effect:** generic birth
  post-training made new parenting advice more operationally usable.
- **TRUE helps prose/state but not action or record:** the thought-to-action or
  action-to-own-record link remains the bottleneck; do not blame SLEEP.
- **TRUE and FORM both beat OFF but not each other:** the gain is output
  practice/interface automatization, not the proposed advice-use habit.

Even a full pass establishes only immediate, target-blind parenting
receptivity after source-prepared birth post-training. It does not establish
SLEEP, persistence, adaptive-parent improvement, continual learning, connected
memory, recurrence, PCFL, or the whole organism.

## Priority and stop ruling

This should remain parallel/deferred. PCFL v2.2 is the shortest route to the
paper's core own-action/outcome, connected-memory, and lifetime claims; its
current blocker is executable integration, not a missing parenting proxy. This
bootstrap experiment cannot rescue or qualify PCFL, and another interface
assay must not take the builder off that path.

Prepare it only after the PCFL zero-fit runtime exists, and execute it on truly
idle capacity or after the PCFL DEV decision. Stop after Stage 0 on interface
failure and after Stage 1 on no conditional-habit gain. That keeps the possible
cost to six small birth fits plus inference, while preventing another writer or
parenting run from being asked to solve a measurement interface it was never
given.

## Evidence boundary

This design responds specifically to:

- `research_notes/analysis/2026-09-13_parenting_alignment_terminal_audit.md`;
- `research_notes/analysis/2026-09-13_modular_birth_posttraining_evidence_and_protocol.md`;
- `research_loop/coordination/20260910_compilergym_bootstrap_quarantine.md`;
- `research_loop/coordination/20260910_bootstrap_v3_unverified_provenance_quarantine.md`; and
- the current PCFL critical-path ordering in `research_loop/COORDINATION.md`.
