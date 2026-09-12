# Compiler as real DREAM: a matched-dose view protocol

Date: 2026-09-12 UTC  
Status: independent design memo only. No builder source, benchmark, model,
adapter, job, process, or GPU state was changed. This memo authorizes no
execution or claim.

## Bottom line

Rohin's idea becomes precise if **DREAM is the search over useful ways to
re-index grounded experience**, while SLEEP is the ordinary write of the
accepted views into LoRA.

One event can be revisited many times, but those quantities must never be
collapsed:

```text
evidence count       = independent public events that happened
view count           = distinct supported transformations of those events
optimization dose    = effective optimizer encounters with each target
```

Twenty renderings of one event are one piece of evidence, up to twenty views,
and twenty training encounters. They are not twenty corroborating memories.

The smallest useful experiment has three arms at the same dose:

1. `V1-REPEAT`: one canonical question repeated;
2. `V4-LEX`: four wordings of the same question; and
3. `V4-REL`: four grounded access operations on the same relation.

`V4-LEX - V1` measures lexical cue diversity. `V4-REL - V4-LEX` is the first
bounded test of structural re-perception. A later identical-write stage over
new facts tests whether the initial representation remains more extractable,
not merely easier to fit.

## What “real dream” should mean in this paper

The current compiler should stay explicit, fixed, and auditable:

```text
public episode
  -> choose an evidence root
  -> apply a fixed grounded view operator
  -> reject unsupported or duplicate propositions
  -> preserve immutable source IDs
  -> serialize accepted views as child-language training records
  -> conservative LoRA write + interface/locality gate
```

This is a **supplied compiler ceiling**. The experimenter chooses the view
operators and schedule. It can show that dream-shaped compilation helps the
write, but it cannot show that the child knows how to dream.

The later learned/parented compiler keeps the same evidence boundary but moves
three choices to the child:

- which episode or unresolved belief deserves replay;
- which view, contrast, or connection is worth expanding next; and
- when another replay is redundant and it should stop or seek new evidence.

The parent may teach those dispositions. Downstream utility can train the
selection policy. The world alone creates new evidence and admits truth. A
child-generated view can reorganize support; it cannot manufacture support.

That is the defensible version of **“varied perceptions as MCTS for memory.”**
The correspondence is:

| search term | DREAM analogue |
|---|---|
| root/state | evidence node, current goal, uncertainty, remaining budget |
| action | recall, reframe, contrast, connect, backtrack, seek evidence, stop |
| expansion | a new supported proposition or a new public observation |
| visit count | replay/optimizer encounters, not evidence count |
| exploration term | penalize duplicate proposition identities; try a new lens |
| value | later decision gain or information gain minus token/action cost |
| backup | later outcomes update which view operators were useful |

Until selection, expansion, later utility, and backup are actually measured,
the accurate phrase is **MCTS-like prioritized branching**, not MCTS.

## Language artifacts now; latent transforms later

For this paper, DREAM should remain in token space. Text gives four things the
latent proposal does not yet have: exact source receipts, mechanical support
checks, inspectable false memories, and an ordinary response-masked LoRA
trainer. The child can still generate the text offline with no interlocutor;
“not in the conversational workspace” does not require hidden-state training.

A latent replay system could later transform activations or intermediate
representations without serializing language. That would be a different
learning algorithm. It needs a latent readout, interventions showing what was
transformed, a provenance analogue, and a way to reject unsupported changes.
No result from the present text compiler establishes it.

## The important distinction: lexical versus structural views

### Lexical view

A lexical view preserves the same query operation and answer while changing
wording or order:

```text
What colour was recorded for DEVICE?
Which colour belongs to DEVICE in the record?
Recall DEVICE's logged colour.
The recorded colour of DEVICE is what?
```

All four implement `key -> value`. This can improve access under new wording,
which is valuable post-training science. It does not form another relation.

### Structural/relational view

A structural view changes how a grounded relation is used while preserving
its answer and full key. For a sealed one-colour-per-device record
`DEVICE -> COLOUR`, use four audited operators:

1. **forward recall:** `DEVICE -> ?`;
2. **record completion:** complete the typed relation `DEVICE / colour / ?`;
3. **correction:** a balanced wrong candidate is supplied; return the recorded
   value instead; and
4. **contrast:** distinguish `DEVICE` from a sealed paired device with a
   different value, while still returning `DEVICE`'s value.

The output is always the same one-native-token colour. The correction is
entailed by the closed one-colour ontology. The contrast cites the immutable
roots for both devices; it gains no extra evidence count. These operators are
still supplied scaffolding, but they expose the same relation through recall,
completion, error repair, and discrimination rather than four synonyms.

## What Astra's current `SINGLE_VIEW` versus `FOUR_VIEW` can establish

If Astra uses one fixed direct question twenty times versus four fixed direct
question phrasings five times each, with the presentations scattered across
separate matched optimizer steps, the result is a clean narrow test:

> At the same evidence and effective training dose, do four lexical cues make
> an opaque binding more accessible under unseen wording than one repeated
> cue?

It can establish:

- diversity-assisted acquisition if only `FOUR_VIEW` acquires even the exact
  canonical relation;
- lexical extraction robustness if both acquire exactly and `FOUR_VIEW`
  improves truly held-out phrasings; or
- a useful null if one repeated cue is already sufficient at this dose.

It cannot establish structural perception, cross-event connection, a learned
compiler, intelligent view selection, MCTS, DREAM, parented improvement,
latent transformation, downstream action use, or retention. It also cannot
establish repeated replay if all four same-source presentations are averaged
inside one optimizer update: in that case it measures within-update gradient
geometry. Report presentations and distinct source-specific optimizer updates
separately.

Thus Astra's pair is worth finishing as the **lexical sentinel**. It is not the
full test in this memo.

## `VIEW-R0`: smallest matched-dose structural-view experiment

### Material

- 16 opaque devices and 4 balanced one-token colours;
- exactly one immutable public source record per device;
- a prospectively sealed pair for each device whose colour differs, used only
  by the contrast operator;
- two complementary label maps so every prompt byte can remain fixed while
  the answer changes;
- one common canonical direct-query form in every arm; and
- no model-written explanation, parent text, hidden answer table, or semantic
  addition.

Receipts must record, per arm:

```text
n_source_events                 = 16
n_supported_bindings            = 16
n_view_operators_per_binding     = 1 or 4
n_presentations_per_binding      = 20
n_optimizer_encounters_binding   = 20
n_supervised_answer_tokens       = identical
n_updates                        = 80
```

The 16 source events—not the 320 rows—are the evidence denominator.

### Three acquisition arms

| arm | schedule per binding | estimand |
|---|---|---|
| `V1-REPEAT` | canonical direct form x20 | effective repetition ceiling |
| `V4-LEX` | four lexical direct-query forms x5 | lexical cue diversity |
| `V4-REL` | four grounded operators above x5 | supplied structural access diversity |

Every source's 20 rows occur in 20 distinct, seed-paired optimizer encounters.
Use batch size 4 with different source IDs per batch, or batch size 1; never
place repeated views of one source in the same averaged update. The ordered
source IDs, labels, target+EOS count, update count, root adapter, optimizer
seed, rank, LR, dropout stream, and preservation microbatch are shared.

Recommended frozen dose, because SEQ-105 already acquires it:

- rank 8, alpha 16, dropout `.05`;
- LR `3e-4`, fresh AdamW optimizer;
- 20 encounters per binding = 320 memory rows = 80 four-source updates;
- response-only/context-masked loss; and
- the qualified preservation objective, if the clean replay successor has
  selected one, added as a separately mean-normalized term rather than by
  diluting memory tokens.

All answers are the same one-token colour surface. Choose fixed templates
whose native context lengths match where possible; otherwise pad all rows to
the same audited length with a common loss-masked neutral prefix and report
both target-token equality and total-token cost. Equality of target dose is
mandatory; equality of context compute is a useful secondary control.

### Acquisition readout

Freeze before fitting:

1. the common canonical trained form;
2. four lexical phrasings used by no arm;
3. fresh instantiations of the four structural operator families, using
   unseen wording and unseen wrong candidates/pairs;
4. swapped-key and wrong-candidate specificity probes;
5. the inherited behavior/action interface panel; and
6. adapter-OFF readout on every item.

For each key and surface, report exact top-1 and the margin

```text
M = log P(correct colour) - log mean P(the three wrong colours).
```

Also report full candidate mass. An arm that merely makes all colour tokens
more likely has learned an answer dialect, not a selective memory.

The primary contrasts are:

```text
D_lex    = M(V4-LEX) - M(V1-REPEAT) on sealed lexical cues
D_rel    = M(V4-REL) - M(V4-LEX)    on sealed structural cues
D_total  = M(V4-REL) - M(V1-REPEAT) on sealed structural cues
```

`D_rel` is the critical comparison. Without it, structural and lexical
diversity remain conflated.

### Matched retention stage

Retention needs another write; immediate post-fit recall is acquisition.
From each acquired branch, train an identical fresh bank B:

- 16 new opaque bindings;
- the canonical one-view format only;
- 20 encounters per new binding over 80 updates;
- exactly 4 canonical replay encounters per old-A binding, scheduled on the
  same 16 registered updates in every branch; and
- the same preservation microbatch/objective.

Each loss is separately token-mean normalized:

```text
J_t = L_B + L_preserve + I_old_replay(t) * L_A
```

The later replay of A is byte-identical across arms. Re-probe old A and new B.
The retained old-A structural margin is the primary retention endpoint; the
change from pre-B to post-B is reported, but a ratio is avoided because
near-zero margins make ratios unstable.

This asks whether diverse initial access routes leave A more recoverable after
the same subsequent learning and the same maintenance dose. It still does not
show lifelong retention.

## Gates and stopping rules

### Pre-fit gates

No GPU fit if any of these fails:

- every row is entailed by its cited root set;
- source, view, and encounter counts reconstruct exactly;
- labels and nuisance fields are balanced and shortcut accuracy is at chance;
- answer target-token mass and optimizer encounters are identical;
- no evaluation template appears in training; or
- the common response/interface carrier fails its existing canary.

### Seed-0 gate

Run only the three acquisition arms at root/optimizer seed 0 first.

- If any arm is below `14/16` on the common canonical read, label the result
  `ACQUISITION_NOT_COMPARABLE`; do not interpret a view effect or run stage B.
- If the preserved interface falls below `30/32`, or valid action formatting
  below `31/32`, label `INTERFACE_FAIL`; do not trade behavior for recall.
- At least `14/16` keys must have positive owner-specific correct-versus-wrong
  margins, and mean probability change on out-of-scope/non-key prompts must be
  `<= .05`; otherwise label a global colour habit/spill.
- If both `D_lex` and `D_total` are smaller than `.50` nat and fewer than two
  additional keys become correct, stop the view-scale branch as practically
  null at this dose. Do not add more views.
- If `D_total > 0`, `D_rel > 0`, the practical threshold above is crossed, and
  all gates pass, run the matched retention stage, then roots 1 and 2.
- If only `D_lex` is positive, replicate only the lexical result and call it
  lexical augmentation. Do not call it structural DREAM.

### Replication claim gate

A bounded varied-view effect requires:

- the relevant paired contrast positive in all three roots;
- mean paired margin improvement `>= .50` nat;
- at least `+2/16` exact top-1 keys on the corresponding sealed panel;
- a root-and-key clustered bootstrap lower bound above zero, reported as a
  sensitivity analysis rather than pretending the 16 views are learners; and
- no failed acquisition, interface, specificity, or locality gate.

A retention benefit additionally requires post-B new-bank acquisition
`>=14/16` in every branch, a positive final old-A `V4-REL - V1` margin in all
three roots, mean `>=.50` nat, and no worse old-A exact-key loss in `V4-REL`.

No hyperparameter, template, or threshold is tuned after opening seed 0. The
only optional scale point is `V20-REL` (twenty presealed grounded forms x1 at
the same 20 encounters), and it launches only if `V4-REL` passes all gates but
remains below the practical effect threshold. It tests diminishing returns;
it is not a rescue arm.

## GPU budget

SEQ-105 used about `27.8` A40-minutes for three 80-update acquisition fits and
their exact/dev readouts, approximately `9.3` minutes per branch. On that
anchor:

- seed-0 acquisition, 3 arms: about 28 A40-minutes;
- seed-0 matched retention, 3 continuations plus readout: cap 45 A40-minutes;
- full 3-root acquisition + retention: conservative cap **225 A40-minutes
  (3.75 A40-hours)** including reload/readout overhead;
- conditional `V20-REL` across acquisition + retention: at most another 75
  A40-minutes.

Hard total cap: **300 A40-minutes (5 A40-hours)**. Parallelism changes wall
time, not this budget. This is a writer/representation assay and should not
displace the main H1/H2 run if GPUs are scarce.

## Exact claim bounds

If `V4-LEX > V1`, the maximum claim is:

> At matched effective dose, fixed lexical cue diversity improved fresh-cue
> extraction of supplied opaque bindings in a rank-8 LoRA writer.

If `V4-REL > V4-LEX` and the matched retention stage passes:

> At matched evidence and optimizer dose, fixed grounded transformations of
> supplied relations improved structural-cue extraction and short-horizon
> retention over lexical paraphrase and identical replay.

Neither result establishes child-authored dreaming, learning-to-remember,
cross-episode intelligence, MCTS, parenting, latent sleep, compression,
continual improvement, or downstream agent performance.

The larger paper becomes stronger because this separates its mechanisms:

```text
fixed VIEW-R0       qualifies a dream-shaped writer representation
learned DREAM       chooses useful views and links under a budget
SLEEP               writes accepted grounded transformations to LoRA
THINK               later uses them during state-to-state action
parenting           teaches the child how to allocate DREAM and THINK
```

## Amortization is a later test, not an inference from `VIEW-R0`

Rohin's stronger prediction is that a model trained to store bank A through
many views will later store bank B from fewer views. Test it separately:

```text
A-heavy-view -> B-one-view
A-one-view   -> B-one-view
no-A         -> B-one-view
```

Match B dose, optimizer state policy, total updates, and preservation. A B
advantage would be a representation-priming or learning-to-store effect. With
one continuously trained adapter it may still be ordinary shared-feature
priming, not a learned compiler policy; the child must later author better
views or allocate replay better before calling it learning to dream.

## Evidence used

- Rohin raw message 21 in
  `research_notes/THESIS_RAW_ROHIN_2026-09-11.md`;
- `research_loop/COORDINATION.md`, SEQ-098--107;
- `research_notes/CHILD_MECHANISM_v7.md`;
- `organism_v6/sleep_compile.py` and `organism_v6/sleep_compile_v3.py` as
  read-only descriptions of current fixed compilers;
- `research_notes/52_public_pathway_consolidation_mechanism.md`;
- `research_notes/WHAT_TO_PARENT_FROM_THE_LITERATURE_2026-09-12.md`;
- `research_notes/analysis/2026-09-12_knowledge_storage_extraction_paper_implications.md`;
- `research_notes/analysis/2026-09-12_high_dose_memory_habit_replay_successor.md`;
- `research_notes/analysis/2026-09-12_varied_perception_real_dream_compiler_adversarial_audit.md`;
- `research_notes/analysis/2026-09-12_post_v10r2_writer_recipe_factorial.md`;
- Allen-Zhu and Li, *Physics of Language Models: Part 3.1, Knowledge Storage
  and Extraction* (local summary and arXiv:2309.14316); and
- the earlier F-series fixed-template form-count results recorded in
  `research_loop/COORDINATION.md`.

