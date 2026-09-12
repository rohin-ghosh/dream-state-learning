# Two habits, one adapter: smallest next level-zero test

**September 12, 2026 — DESIGN ONLY; not implemented, launched or allocated.**

## Recommendation in brief

**Add an input-reporting habit to the already learned prediction-order habit.**
Fork each original teaching checkpoint into two equal-content continuations:
one learns **INPUT → PREDICT → ACT**, the control learns
**PREDICT → ACT → INPUT**. Ask whether the second habit appears while the first
remains usable. Use all three existing trainer seeds, one fixed learning rate,
one adapter per state, and the unchanged dev questions. No simultaneous-write
grid, compiler, adapter split, new memory-dose sweep or broader curriculum.

This complements, rather than duplicates or interrupts, Main's running
competing-update/plasticity work. It tests **adding a compatible habit with
explicit rehearsal of the first**, not how long an unrehearsed habit survives.

## 1. Directive and current evidence

Actual message19 is in `research_notes/THESIS_RAW_ROHIN_2026-09-11.md`, headed
approximately18:45UTC; its relay in `research_loop/COORDINATION.md` is stamped
18:39UTC. Preserve that metadata difference rather than inventing one exact
utterance time. Operative words include:

> adherence to form is actually a pretty big success

> Try it on two behaviors try it on maybe like two behaviors that are intertwined

Rohin also says not to maximize adherence indiscriminately: contrasting new
behaviors must remain learnable. This proposal does not require intelligent
prediction, biological forgetting, a projection layer or a completed level-1
curriculum. His behavior-versus-memory question is not authorization for a split.

SEQ098/099 establish one order habit across trainer seeds0/1/2: teaching32/32,
controls0/32, with ACT correctness32/32 throughout. SEQ100's original seed0
adapters answer constant red even on training-form memory questions. SEQ101's
four repetition/context cells likewise retain the habit but score4/16 memory
with constant red; do not attribute SEQ100's training-prompt readout to these
different repetition adapters. None of this identifies a neural behavior/memory
dissociation or requires separate adapters. Main owns repetition integration.

The earlier fading design's “no warm-start interface” limitation is superseded
by the supported V3 weight-only `--init-adapter` path and native21/21CPU receipt.
It still creates a **fresh optimizer**, not resumed optimizer state. Main's
18:50UTC continuation plan uses rates0/3e-5/1e-4 and competing ACT-only updates;
this note neither predicts its outcome nor changes its allocation.

## 2. Exactly two observable conventions

- **A — forecast before acting:** one syntactically valid numeric PREDICT before
  the first and only ACT. Prediction accuracy is reported separately; Rohin's
  target is the convention, not improved arithmetic.
- **B — report given inputs before acting:** one INPUT line faithfully copies
  the two operands in their displayed order before ACT. No invented observation
  or claim to have seen an environment response. This is a small input-copying
  convention, not selective perception or memory acquisition.

For a source row with operands `left,right` and independently computed `sum`:

| Branch | Authored arithmetic response, one line per step |
|---|---|
| T: intertwined addition | `INPUT: left, right` → `PREDICT: sum` → `ACT: sum` |
| C: order-matched active control | `PREDICT: sum` → `ACT: sum` → `INPUT: left, right` |

Both branches contain the **same three lines, values and supervised information**;
only placement of INPUT changes. C is deliberately not “no second line” or a
shorter task-only corpus. Both rehearse A. Repetition of a fixed three-line
template is a possible explanation even if this works; ordered co-expression
does not show that the model internally uses its INPUT report to predict.

## 3. Smallest controlled schedule

For each original trainer seed0/1/2, take its immutable **original SEQ098/099
teaching adapter**, not a repetition adapter, a continuation descendant, the
best-memory seed or the current live worker's checkpoint.

| State | Starting weights | New training | Role |
|---|---|---|---|
| H | Original A checkpoint | None | Actual inherited A-only hold/reference |
| T | Exact same H bytes | Intertwined response order | Add B while rehearsing A |
| C | Exact same H bytes | Matched after-action INPUT order | Control for added content, dose and more A rehearsal |

T/C each receive one80-update continuation:80rows ×4epochs, batch4,
accumulation1; rank8, alpha16, dropout.05 and the existing all-projection V3
configuration. **Fix LR1e-4 now**, not the winner of the running rate sentinel.
Use fresh AdamW with paired continuation seed equal to the originating trainer
seed. Bind resolved optimizer settings, base/parent hashes and exact loaded
LoRA tensors before writing; carry weights, never optimizer moments. One
ordinary adapter contains both conventions and the unchanged memory material.

Use the existing64arithmetic training cases and16memory rows in their original
order. Add INPUT only to arithmetic targets; memory contexts/targets are unchanged
background in both branches. Keep native user-context rendering, loss masking,
EOS and no-packing/zero-truncation behavior. No new compiler or live parent.

**Why sequential, not simultaneous?** A is already demonstrated in all three
checkpoints, so two matched descendants per seed directly test adding B. A
fresh joint fit would change prior A dose and optimizer history; adding that
cell alone would not isolate schedule. Defer a genuine simultaneous/sequential
comparison with matched cumulative exposures and resets. No schedule-superiority
claim follows from this smaller experiment.

## 4. Frozen readout and decision

Use the existing48case requests:32arithmetic operand pairs disjoint from the
64training pairs even under operand reversal, plus16memory paraphrases.
These are **repeatedly exposed development cases**, not fresh confirmation.
The other64candidate confirmation cases stay unrequested. No INPUT instruction,
example, reminder, target answer or prior generated text is added to prompts.
Use temperature0, seed20260912, max64tokens and fresh-process state readouts.

Prospectively freeze a small additional raw-output analysis, without changing
the original readout or its scorer:

- **Primary J:** exactly one valid INPUT, PREDICT and ACT, in
  `INPUT < PREDICT < ACT` order; INPUT equals the two source operands. Require
  exactly these three nonblank lines: case-sensitive labels, signed decimal
  integers, optional surrounding/colon/comma horizontal whitespace, no prose
  or fences. No later-action rescue, semantic normalization or dropping failures.
  PREDICT need not be correct for J; keep that distinction explicit.
- Report A's form-only ordering, B's source-faithful before-ACT reporting, and
  the original **correct** PREDICT-before-ACT score separately. Also preserve
  original ACT correctness, memory, invalidity, raw outputs and cap hits.
- For every seed, show `J(T)−J(C)`, new B versus H, and A/ACT changes versus H.
  The three parent lineages share data/panel; branches and32probes are not
  independent learners. Report all three counts and differences, not a pooled
  “96 independent” success rate or a selected best seed.

Descriptive advancement rule, **not a scientific gate or automatic launch**:
J(T)≥28/32 and J(C)≤4/32 in each seed, form-A loss≤2/32 and correct-ACT
loss≤1/32 versus H. Missing artifacts mean incomplete, not zero. Show failures
even when marginal A or B looks good. These predeclared tolerances only decide
whether this exact two-habit scaffold merits another bounded design; they
neither demand permanent maximal adherence nor qualify the broader curriculum.
Changing them after outcomes creates a new exploratory analysis, not a rescue.

## 5. Provenance, counts and budget

Source INPUT values from the existing operand records; derive both numeric
training targets by ordinary integer addition, never a generated answer.
Preserve case/source IDs, original context bytes and memory color keys. No
evaluation output enters training. Native CPU preflight must check all80paired
rows, one chat prefix, target+EOS masks, no lost tokens, paired batching and
actual per-row input/target counts. Same line inventory **does not prove native
token equality after permutation**. If counts differ, stop/report the mismatch
for Main's pre-outcome decision; do not pad silently or claim matched dose.
The original4517input/912target per epoch are NOT the augmented corpus's counts.

| Maximum planned content work | Exact count |
|---|---:|
| Parent seeds × trained branches | 3 × 2 = 6 new fits |
| Updates | 80/fit;480total |
| Training row presentations | 320/fit;1920total |
| New readout states/calls | 6 ×48 =288calls |
| Requested output ceiling, not usage | 288 ×64 =18432tokens |

Reuse the actual three H readouts and actual base OFF only after exact
checkpoint/model/request/native-input/decoder bindings pass. Their192existing
responses (three48-call H panels plus one48-call OFF) are **not new calls**.
If reuse cannot be established, do not proceed with an invented baseline;
Main must prospectively choose a refresh budget. Refreshing all three H and
one OFF adds192calls, making480new calls/30720cap tokens instead of288/18432.

Propose a **separate60aggregate reserved A40-minute ceiling**,20per seed for
the288-call package, only if Main elects to allocate it; no lease or allocation
is requested by this note. This is a stop bound, not a measured duration or a
guarantee that all workers finish. Preserve existing per-worker600-second and
cleanup guards inside that aggregate bound; four workers per seed can exceed
20minutes at their individual maxima. Admit a stage only with remaining lease
and cleanup reserve, count loading/CPU gaps/audit/release in the outer budget,
and report partial work if exhausted. Never omit C, reuse a failed root, or
convert timeout into a scientific failure score. No new teacher calls, rank
sweep, confirmation calls or memory-dose escalation are budgeted. Native token
mass awaits preflight; no throughput or dollar rate is inferred.

## 6. Interpretation and handoff

A positive result means one previously installed output habit can acquire a
second source-faithful output convention under this compatible, rehearsed
continuation recipe. If A survives but B does not appear, that is not successful
plasticity. If J improves but ACT collapses, it is not a useful positive control.
If both arms show B, report the failed ordering contrast rather than teaching
efficacy. Unrehearsed replacement/revisability is Main's separate current test;
preservation here does not require that A should never be dissolved.

This is not parenting, child-authored sleep, cognitive prediction, arithmetic
gain, memory repair, latent-mechanism identification, H1/H2, P1/G5, or proof of
simultaneous-versus-sequential superiority. It changes no project invariant or
scientific claim. Main retains design selection, implementation and launch.

Read sources: raw message19 and its coordination relay; the18:50UTC continuation
entry; `research_notes/analysis/2026-09-12_level_zero_repetition_and_update_persistence_protocol.md`;
`/tmp/astra_level1_fading_sequence_design_20260912.md` (its warm-start absence
is historical); SEQ098–101 terminal memos; existing fundamental corpus/readout
and V3 interface. No literature discovery or biological analogy is imported.

**Author-side checks:** pure local corpus generation verified64unique training
pairs,32unique dev pairs, disjoint under reversal,80training rows,48dev cases,
64untouched confirmation cases,6fits/480updates/1920presentations and288calls/
18432cap tokens. In-memory target/scoring fixtures passed on all96source pairs
(64train+32dev): equal line inventory, original A scoring, joint-order and
source-copy checks, duplicate/wrong-source rejection, and separation of form
from prediction accuracy. The baseline-refresh arithmetic also passed. These
are design sanity checks, not native token matching or new model outcomes.
No tokenizer, model, GPU, network, Git or repository write.
Only this design file was written. **DESIGN-ONLY EDIT-STOP.**
