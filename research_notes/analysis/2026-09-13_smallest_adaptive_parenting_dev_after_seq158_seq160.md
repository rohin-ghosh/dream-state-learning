# Smallest staged adaptive-parenting DEV after SEQ158/160

**Date:** 2026-09-13 PT  
**Status:** design only; no source, fixture, model, tokenizer, fit, GPU, remote,
or scientific execution authorized or performed  
**Question:** can one adaptive fixed-weight parent produce a useful child
strategy that (1) helps while taught, (2) is actually absorbed by the writer,
and (3) improves fresh world outcomes after the parent and all childhood
context are gone?

## Recommendation in one paragraph

Run one small three-gate DEV, not another record-format assay and not the full
v5 developmental campaign. Use a deterministic black-box diagnosis game with
simple `PROBE` and `CHOOSE` actions. The Qwen2.5-7B-Instruct child first
struggles independently. The strongest bound parent then gives one adaptive
process correction; a sibling attempt gets an active correction written for a
different matched child. Compare their outcomes immediately. Only if aligned
coaching helps do we train two matched LoRAs on the resulting **child**
thought/action continuations, with all parent text loss-masked. Only if both
writers demonstrably absorb their assigned continuations without breaking the
action interface do we run a parent-absent, context-cleared, 32-task delayed
exam. This cleanly separates teacher efficacy, writer absorption, and durable
incremental parenting.

## Why this is the next experiment

SEQ158 already established two useful facts:

- the fixed reminder changed the named in-context fields (`48/48` versus
  `38/48` for prediction and relation); and
- either arm's child-authored record write taught the narrow record behavior
  (`45/48` P and `45/48` N versus `27/48` before writing).

It could not measure durable parenting: P and N were identical after writing,
the endpoint had only three errors of headroom, the doses differed, and both
corpora reduced to the same correct record habit.

SEQ160 moved toward richer process content but placed the measurement behind
a brittle schema. `143/144` NOTE sources failed normalization, so the intended
process contrast was not measurable. The lesson is not to add another output
contract. Use a behavior the base can already physically perform, score its
consequence in the world, and reserve prose for unconstrained thought.

## The unsaturated world task

Call the DEV family **Diagnostic Panels**. It is deliberately disjoint from
PCFL, CompilerGym, RuleGame triples, and every final deployment namespace.

Each task publicly shows a table of candidate hidden devices and the binary
result each possible diagnostic probe would return for each device. One device
is secretly active. The child may make at most three irreversible queries:

```text
PROBE Q_<nonce>
CHOOSE H_<nonce>
```

After each valid `PROBE`, the world returns the actual `0/1` result. `CHOOSE`
ends the task and is scored against the hidden device. Free prose THINK is
allowed before either action, but no NOTE/JSON/named-field schema is required.
The primary endpoint is exact final choice; repeated probes, invalid actions,
number of probes, and consistency of the final choice with observed outcomes
are diagnostics.

The prospective task constructor must ensure before any child output:

1. all candidate rows are distinguishable within three adaptive probes;
2. no single probe identifies the answer;
3. labels, row order, and column order are independently permuted;
4. the correct row and optimal first-probe position are balanced;
5. fixed-first, fixed-last, repeat, majority-outcome, and order-only policies
   remain below `1/2`; and
6. childhood, calibration, writer-localizer, filler, and delayed-exam instances
   have disjoint task IDs, labels, tables, and hidden answers.

This is meta-cognition made behavioral, not another required record: keep a
live hypothesis set, choose an informative question, update after reality
answers, notice when uncertainty remains, and stop when the evidence warrants
a commitment.

## One child and one improving parent

The sole child identity is the exact pinned
`Qwen/Qwen2.5-7B-Instruct` checkpoint. Experimental arms are disposable tensor-
identical copies of that child, never independently initialized models.

The parent is the strongest reproducibly bound model available at launch. Its
model weights, revision, system prompt, tools, and decoding stay fixed. It may
improve its teaching through a bounded, model-visible notebook; this is the
adaptive-parent policy ratified in v5, not a second learned model.

For this small DEV, cap the notebook at 8 KiB. It may contain at most four
active teaching hypotheses and four recent lesson summaries. Each hypothesis
records: the child's recurring process error, the proposed intervention, its
predicted behavioral effect, and the actual later outcome. The append-only
experiment log remains outside model-visible state. After each two-lesson
round, one parent call proposes a checked notebook replacement. The notebook
never sees delayed-exam material.

The parent is answer-aware as v5 specifies, but direct-answer-withholding. It
may use the hidden answer to diagnose the completed struggle. Its child-facing
message may not name any hypothesis ID, probe ID, table cell, answer bit,
concrete next action, or solved path. It can say, for example, “you did not
remove candidates contradicted by the second result” or “choose a question
that splits the candidates you still consider possible.” Literal leakage,
answer-swap, and independent semantic checks are ordinary hygiene gates; they
do not make answer-aware advice information-free.

## The 16 paired teaching lessons

Run eight rounds of two matched lessons. Within each lesson:

1. **Independent struggle.** A fresh-context child gets one source task and
   acts until `CHOOSE` or the three-probe limit. Only the world answers it.
2. **Adaptive diagnosis.** The parent sees that public trajectory, actual
   outcome, hidden answer, and its bounded notebook, then writes one short
   process correction.
3. **Exact active/yoked control.** Generate both corrections in a two-lesson
   round before either application. On apply task A, ALIGNED receives A's
   correction and YOKED receives B's correction; on task B the assignment is
   reversed. Strip or prohibit concrete IDs rather than editing semantics.
   Thus both arms receive the exact same parent-message multiset and contact
   budget; only child/message alignment changes.
4. **Fresh application.** The two tensor-identical child copies receive the
   same fresh homologous apply task, fixed sampling seed, and different
   assigned correction. Each first says in its own free prose what it will do
   differently, then acts. The parent does not intervene again.
5. **World judgment.** Exact choice and probe behavior come only from the
   deterministic environment. Failed and successful valid trajectories are
   both preserved.
6. **Parent learning.** After the pair completes, the parent sees only the
   aligned applications and proposes one bounded notebook update. No weight
   update occurs in the parent.

YOKED is stronger than generic encouragement: it controls for contact,
teacher style, process language, message distribution, and token exposure.
Because another child's correction can accidentally help, it is conservative.
The same message may not be regenerated separately for the control.

## What enters SLEEP

Make two matched child corpora from the same fixed child checkpoint:

- **P corpus:** the 16 aligned apply continuations;
- **N corpus:** the 16 yoked apply continuations.

Both also contain the identical 16 independent-struggle trajectories as a
common replay anchor. Each application target includes the child's own
restatement, free thought, `PROBE`/`CHOOSE` actions, and public outcomes in
chronological order. Parent/yoked messages may be visible conditioning text
during childhood, but receive zero loss. Only committed child continuations
are targets. Do not convert them into an evaluator-authored “ideal” trace, do
not train the parent's correction, and do not filter evidence merely because
the child failed.

The crossed yoking makes the parent-message multiset identical between the two
fits. Use the same source checkpoint, LoRA topology, optimizer recipe, number
of examples, presentations, updates, batch construction, and writer canaries.
Report realized target tokens; no favorable-row admission may create a dose
imbalance. Train one P and one N adapter only. This is **two fits**, not three:
the no-write comparator is their common unchanged child.

## Four stopping gates for three separate questions

These are DEV stopping rules, not paper-level power claims. No failed gate may
be rescued by changing the task, dose, prompt, rank, or scorer inside this
version.

### Gate 0 — usable task, neither ceiling nor schema floor

Before parent calls, run the unchanged child on 12 calibration tasks.

- valid `PROBE`/`CHOOSE` histories: at least `11/12`;
- exact success: `3/12` through `8/12`, inclusive; and
- no shallow policy from the frozen control set exceeds `6/12`.

Above `8/12` is `TASK_SATURATED`; below `3/12` or below `11/12` valid is
`TASK_OR_INTERFACE_FLOOR`. Either stops this version before teaching. Do not
substitute a harder/easier stratum after seeing the result.

### Gate 1 — immediate teacher efficacy

This gate is evaluated before any fit.

- both ALIGNED and YOKED produce at least `15/16` valid complete applications;
- `success(ALIGNED) - success(YOKED) >= 4/16` on the paired tasks;
- the aligned-minus-yoked difference is nonnegative in both prebound
  eight-item halves and positive in each half;
- ALIGNED has no more repeated probes or outcome-inconsistent final choices
  than YOKED; and
- all 16 corrections pass the no-direct-answer hygiene checks.

Failure is `ADAPTIVE_TEACHER_EFFICACY_NOT_SHOWN`; stop before LoRA training.
This prevents a writer result from being used to rescue a teacher who did not
help in context.

### Gate 2 — writer absorption and interface preservation

After the two matched fits, use 12 exact source-prefix next-decision localizers
per adapter. The original parent/yoked message remains in its arm's prefix but
is still loss-masked; the scored target is that arm's own previously committed
next action. Compare each adapter ON versus the unchanged child on those exact
same token IDs. This deliberately tests storage before asking whether the
stored behavior survives source withdrawal.

For **each** adapter:

- its target action's normalized log-odds relative to the unchanged child must
  improve on at least `9/12` localizers;
- median target log-odds change must be at least `+0.5` nat;
- native exact next-action recovery must improve on at least `6/12`; and
- on 12 fresh interface canaries, validity must be at least `11/12` and no
  more than one item below the unchanged child.

Also require finite training throughout, exact source/target accounting, and
successful candidate commit/rollback receipts. If P fails, durable parenting
is untestable. If N fails, P-minus-N is confounded by unequal writer success.
Either case stops before the delayed exam as
`WRITER_ABSORPTION_OR_INTERFACE_FAIL`.

This gate asks only whether the writer captured what it was given. It does not
call the captured policy good. Repeat the localizers once with the parent text
removed as a reported bridge diagnostic, but do not use that harder result to
relabel failed exact-prefix acquisition; Gate 3 is the actual parent-withdrawn
behavioral test.

### Gate 3 — durable incremental parenting

Run eight identical, target-disjoint filler tasks per state with no parent and
no write, then destroy every conversation/KV state. This is a context-removal
delay, not a subsequent-write retention test. Run a prebound 32-task delayed
Diagnostic Panels exam on three disposable states: unchanged child, P adapter,
and N adapter. The parent, notebook, childhood transcript, restatement, RAG,
and retrieval tools are absent. Each task starts from an empty context and is
scored only by actual world outcome.

The exam is interpretable only if the unchanged child has at least `30/32`
valid histories and scores from `8/32` through `22/32` exact. Then call durable
incremental parenting positive only if:

- paired `P-only successes - N-only successes >= 6`;
- total `success(P) - success(unchanged) >= 4/32`;
- P is not below N in any of four prebound eight-item blocks and is strictly
  above N in at least two blocks;
- P has no more invalid or repeated actions than N; and
- P does not lose more than `1/12` relative to the unchanged child on the
  separate interface canary.

If `success(P) - success(N) <= -3/32` or P introduces more than one additional
invalid action, label the version `ADVERSE_PARENT_WRITE` and stop the lineage.
Any other miss is `DURABLE_INCREMENT_NOT_SHOWN`. No seed selection, extra
sleep, dose increase, or new prompt is allowed inside the version.

Passing all gates supports only this bounded statement:

> An adaptive answer-aware process teacher improved immediate behavior in this
> target-disjoint diagnosis game; matched SLEEP writes absorbed both children's
> continuations; and the aligned child's write produced a larger parent-absent
> improvement on fresh deterministic outcomes than equally dosed yoked
> coaching and no write.

It does not establish general parenting, connected memory, PCFL traversal,
continual improvement, recurrence, or the whole organism.

## Minimum work and cost

The maximum call arithmetic is intentionally small:

| stage | child calls | parent calls | fits |
|---|---:|---:|---:|
| Gate 0: 12 calibration tasks, four turns max | 48 | 0 | 0 |
| 16 struggles + two apply branches, four turns max | 192 | 16 | 0 |
| notebook update once per two-lesson round | 0 | 8 | 0 |
| Gate 2: exact/withdrawn localizers + canaries | 108 | 0 | 2 |
| context-delay fillers, eight per state | 24 | 0 | 0 |
| Gate 3: 32 tasks x three states x four turns max | 384 | 0 | 0 |
| **hard call total** | **756** | **24** | **2** |

With a 256-token child output cap and a 384-token parent output cap, forecast
roughly `1.5–2.5` aggregate A40-hours for the 7B work including two
certified-dose fits; use `4.0 A40-hours` as the DEV hard cap. The 24 strongest-
parent calls should be budgeted separately (API cost, or no more than `0.5`
aggregate H100/A100-hour if locally served). The exact fit update count should
be inherited from the writer recipe that passes the retention screen, not
invented in this parenting memo; current evidence says a 40-update screen is
too small and the known positive envelope is about 200–320 updates.

The stage order preserves most of that budget on a null: Gate 0 costs at most
48 child calls; a failed immediate teacher costs no fit; and a failed writer
costs no 32-task exam.

## Ordering relative to retention and composition

Split the execution decision:

1. **Run Gate 0 and Gate 1 before or in parallel with retention work.** They
   use no LoRA and answer the independent question of whether the adaptive
   parent can teach this child at all.
2. **Do not run the two fits or delayed exam until the EVENT retention
   successor establishes an acquisition-capable, non-destructive writer dose.**
   SEQ188's 40-update state acquired `0/4`; a parenting null behind that writer
   would be uninterpretable.
3. **Do not wait for the PCFL composition/READ-to-STEP mechanism.** Diagnostic
   Panels keeps all within-episode evidence in visible context and tests a
   learned experimental policy, not retrieval from personal parametric memory.
   Composition birth-skill work can proceed independently. Never stack its
   adapter with P or N in this DEV.

Thus the smallest useful next move is immediate adaptive teaching now,
followed by exactly two writer fits after retention is mechanically qualified,
with the composition branch remaining orthogonal.

## Ordinary hygiene only

Before any later implementation, bind the exact child and parent revisions,
task roots, task splits, action grammar, prompts, seeds, notebook cap, corpus
membership, masks, dose, and gates. Keep raw messages and world receipts;
verify P/N start from the same tensors; delete all parent/notebook/context state
before Gate 3; prevent every DEV task and output from entering the continuing
child or deployment gym; and archive failed stages without retry. The deferred
C11 formal guard is unnecessary for this DEV and should not block it.
