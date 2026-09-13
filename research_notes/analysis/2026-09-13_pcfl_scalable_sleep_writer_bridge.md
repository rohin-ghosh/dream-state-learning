# PCFL scalable SLEEP writer bridge: minimum qualification after DEV v2.2

**Date:** 2026-09-13 UTC  
**Status:** prospective protocol memo only; no source, fixture, model, tokenizer,
adapter, job, or GPU execution  
**Entry condition:** both untouched PCFL DEV v2.2 roots pass the frozen
connected-service gate and all writer, locality, native, retention, and
integrity gates

This design uses the project's current simple prospective hygiene. It neither
activates nor waits for the formal C11 guard; that guard is completed and
enforced only if this path reaches the final paper-grade C11 run.

## Ruling

The smallest presently admissible lifetime writer is
`V2.2_ONE_EPOCH_SCALE`:

- preserve the exact qualified v2.2 writer at the 17- and 19-block entry
  writes;
- for cumulative writes of 157, 295, 433, and 571 semantic blocks, start from
  the same clean C0 tensors, retain every semantic block and all eight frozen
  wrappers, but present each wrapper once rather than for five epochs; and
- within each large-size FULL/SCALE pair, differ only in the four additional
  FULL epochs. Selected LOW/HIGH learning rate, rank 8, target modules,
  masking, replay allocation, generalized source-diverse batching, optimizer,
  initialization, final-checkpoint rule, canaries, and read interfaces remain
  identical.

Corpus scale, final-packet replay count, and generalized schedule geometry are
themselves extensions beyond the 20-slot DEV writer. FULL's absolute pass at
157 and 571 qualifies those common scale extensions. Only after that pass does
the paired FULL/SCALE comparison isolate the epoch reduction.

It is only released after a four-fit excluded-history qualification against
`V2.2_FULL` at 157 and 571 blocks. This qualification is a deterministic
compatibility screen, **not** a statistical noninferiority result. Population
evidence comes from the subsequent preallocated lifetime lineages, where every
unsafe or failed write remains an intention-to-treat failure.

This is the minimum defensible bridge because it preserves every memory and
every already-qualified request surface. A reservoir would omit memories; a
warm-start delta writer changes the write architecture; fewer wrappers change
extractability; changing rank or heat reopens the writer. Removing the final
partial packet would save only 48 updates per lineage and is not worth adding
a second unqualified change.

## 1. Exact exposure arithmetic

Let `n` be the number of first-occurrence semantic query-response blocks and
let

```text
p(n) = 20 * ceil(n / 20)
```

be the loss-active slot count after the frozen truthful, output-blind replay
fills only the last partial packet. Each slot has eight wrapper views. Batch
size is four. If `l_j` is the fixed-tokenizer supervised response length of
semantic slot appearance `j`, including terminal EOS and excluding the masked
request, wrapper, and tensor padding, then:

```text
ONE_EPOCH_SCALE:
  examples = 8 p(n)
  updates  = 2 p(n)
  target-token presentations = 8 * sum_j l_j

FULL:
  examples = 40 p(n)
  updates  = 10 p(n)
  target-token presentations = 40 * sum_j l_j
```

An ordinary semantic block receives eight presentations in a scale write and
40 in a FULL write. A source selected once as truthful replay receives one
additional slot: another eight or 40 presentations respectively. First-
occurrence and replay exposures are reported separately. Exact
nonpadding input tokens, supervised target tokens, padded tokens, and
per-source presentations must be materialized and reported; update count is
not a substitute for token or wall-clock cost.

| promoted write | semantic blocks | packet slots | replay slots | FULL updates | scale updates |
|---|---:|---:|---:|---:|---:|
| entry S1 | 17 | 20 | 3 | 200 | **200 (FULL retained)** |
| entry S2 | 19 | 20 | 1 | 200 | **200 (FULL retained)** |
| cut 1 | 157 | 160 | 3 | 1,600 | 320 |
| cut 2 | 295 | 300 | 5 | 3,000 | 600 |
| cut 3 | 433 | 440 | 7 | 4,400 | 880 |
| cut 4 | 571 | 580 | 9 | 5,800 | 1,160 |
| **periodic total / lineage** | | | | **15,200** | **3,360** |

The terminal cut's adapter is a clean-C0 cumulative rebuild. Earlier
presentations affect the experiences collected by earlier mounted adapters,
but they do not remain as optimizer state or parameter updates in the final
adapter. Under the scale law, every ordinary row in the terminal adapter has
exactly eight presentations, regardless of age; only the registered replay
fillers have an additional eight.

With entry `S1_ATOMS` on all 16 initial lineages:

```text
FULL:  16 * 15,200 + 16 * 200 = 246,400 updates
SCALE: 16 *  3,360 + 16 * 200 =  56,960 updates
```

At the unprofiled DEV ceiling of nine seconds/update, these are 616.0 and
142.4 aggregate A40-hours before inference. The scale law uses 23.1% of the
FULL updates. These are ceilings for planning, not runtime claims; actual
200-, 320-, and 1,160-update fits must be profiled before the main launch.

## 2. Excluded-history qualification

Use two preallocated, permanently excluded authentic PCFL histories: one with
157 scheduled semantic opportunities and one with 571. They use different
world-root and writer seeds. They never enter DEV, confirmation, parenting,
paper-test lineages, or a later corpus.

Both histories are collected under one predeclared `SLEEP_FROZEN_SCALE_CAL`
policy. The child may mount only the already-qualified common v2.2 entry state;
no 157+-block FULL or SCALE candidate is mounted while its qualification
history is generated. The action-contingent opportunity tape, module and
panel-goal identities, renderers, strata, structurally identified critical
LINKs, replay-selection domains, and generalized batching algorithm are bound
from the pre-native root skeleton before the first child output. No task is
kept, discarded, extended, or replaced based on child text. If a required
scheduled EVENT/LINK span is absent, malformed, unsupported, or late, the
history is invalid; generation does not continue until 157 or 571 admitted
rows appear. Thus FULL and SCALE receive identical histories that neither
candidate helped create.

Every fitted target must retain the ordinary PCFL chronology receipt from
committed child action to public outcome to later exact child EVENT/LINK span
to compiler inclusion. Panel bytes may be materialized only as the
deterministic rendering of the already-bound structural identities plus
admitted child spans.

Before either fit, freeze for each history:

- the exact first-occurrence and replay occurrence ledger;
- all eight wrappers, response spans, masks, and source-diverse batches;
- a complete supported-address local-read roster plus 32 absent-address and
  32 wrong-root requests;
- 64 service tasks and the same 64 native tasks, stratified prospectively into
  16 oldest, 16 newest, 16 old--new, and 16 expansion/relay cases;
- the service critical-LINK cut for those tasks;
- the unchanged 64-request v2.2 PCFL task-skill retention panel; and
- the generic canary.

The generalized batch solver is frozen by source hash before child output.
For every epoch at both sizes it proves: no two views of one slot in a batch;
no repeated source-span hash in a batch; at most one LINK view per batch;
every NEW view in a distinct batch alongside three OLD/replay views; and
output-blind final-packet replay selected by the v2.2 balanced structural
algorithm. The manifest records the exact LINK and NEW counts and proves the
schedule feasible. Solver failure is assay-invalid; random shuffling or
softening a constraint is forbidden. SCALE uses exactly FULL's first
schedule; FULL alone adds the other four presealed epoch schedules.

Exact graph, full child text, active linked text, and native-context ceilings
must first pass their inherited gates. A failed ceiling invalidates that
history; it does not authorize a new model prompt or favorable replacement.
Under both service and native interfaces, C0/OFF and wrong-root controls must
remain at or below 5/16 exact routes in **each** oldest, newest, old--new, and
expansion/relay stratum as well as 20/64 overall. The `.3125` stratum cap is
the inherited PCFL null allowance applied at the 16-case resolution; it is
bound before output.

Wrong-root service for one history exposes only the other preallocated
history's rows. Native wrong-root cross-mounts each completed SCALE adapter on
the other history's tasks in both directions and likewise cross-mounts each
FULL adapter in both directions. History identities, direction, task bytes,
and seeds are bound in the pre-native skeleton. Because the paired histories
have different sizes, this is only a root-specificity null, never a matched-
capacity comparison. Native cross-mount interpretation waits until both
same-writer adapters exist. Wrong-root service returns must contain zero usable
false rows. All controls use the same frozen task and token budgets.

At each size use byte-identical corpus contents, initialization tensors,
optimizer seed, first-epoch order, inference requests, decode settings, and
per-request seeds for the paired writers. `FULL` adds only its four separately
presealed epochs. Final checkpoints are the only checkpoints scored.

Execute sequentially to stop cheaply:

1. `SCALE_157` (320 updates). If it misses an absolute gate, stop at the scale
   barrier; FULL may be run later only as a labelled diagnostic.
2. `FULL_157` (1,600). If it misses an absolute gate, stop: there is no valid
   medium-scale reference.
3. `SCALE_571` (1,160). If it misses, stop at the scale barrier.
4. `FULL_571` (5,800). If it misses, stop: there is no valid terminal-scale
   reference.

The **training** maximum is 8,880 updates: 1,480 scale plus 7,400 FULL, or
22.2 aggregate A40-hours at nine seconds/update. This is not the qualification
maximum. Before launch, a readout manifest must enumerate every C0, SCALE, and
FULL generation/scoring request, including the adaptive service's hard maximum
of 12 reads per task, and bind a separate inference A40-hour ceiling. The
sequential failure costs before readout are 0.8, 4.8, 7.7, and 22.2 training
hours respectively.

## 3. Noncompensatory gates at both sizes

Both SCALE and FULL must independently pass all gates below. Passing one size
cannot rescue the other, and a high aggregate cannot hide an oldest, newest,
EVENT, or LINK failure.

### 3.1 Carrier and locality

- Score every registered supported address, not a favorable sample.
- In every presealed age-by-type stratum, EVENT semantic exactness is at least
  `.9375`, EVENT strict exactness at least `.875`, and LINK semantic and strict
  exactness at least `.875`, using ceiling-rounded integer thresholds.
- Of the 64 absent/wrong-root requests, at least 60 return exact MISS or a
  registered non-row refusal, with zero usable false rows.
- Candidate-free confusion, unique-output counts, correct-versus-best-wrong
  block margin, grammar/content NLL, and the unseen ninth wrapper are reported
  as diagnostics. They cannot rescue a gate.

### 3.2 Service and native use

- Exact route success is at least 14/16 in **each** of the four task strata
  under both the clean-actor memory service and the mounted native child.
- Native strict legality is at least 60/64.
- The same-evidence/different-goal query-trace gate inherited from PCFL passes;
  final-route accuracy alone is insufficient.
- Replacing each task's prospectively registered critical LINK by MISS reduces
  service success by at least 24/64. This is a writer-compatibility check for
  usable LINK carriage, not a new connected-memory scientific result.

The LINK intervention is service-side causal evidence only. The four-fit
qualification treats the native endpoint as an absolute use/safety gate; it
does not establish native LINK mediation. That stronger claim would require a
native `LINK_PERMUTE` or equivalent parameter-side intervention, which is not
part of this minimum bridge.

### 3.3 Preservation

- The unchanged task-specific `NATIVE_CONTEXT` panel scores at least 60/64.
- Relative to its frozen C0 item results, there are at most two losses total
  and at most one loss in any source root; gains never cancel losses.
- The generic canary passes.
- Oldest and newest task strata each pass 14/16 at both service and native
  endpoints.
- Any task-skill retention failure rejects that candidate. Damage in FULL
  cannot make SCALE look acceptable, and damage in SCALE cannot be averaged
  away by acquisition.

### 3.4 Compatibility with FULL

After both absolute passes, compare the paired final outputs. At each size and
for each endpoint separately:

- SCALE may lose at most three of the 64 cases FULL answered exactly;
- no 16-case task stratum may contain more than one such loss;
- among supported addresses FULL answered correctly, SCALE may lose at most
  `floor(.05 * m)` in each age-by-type stratum of size `m`; SCALE-only gains
  never offset these losses, so a stratum smaller than 20 permits zero losses;
  and
- locality, false-row, task-retention, legality, and critical-LINK-cut gates
  remain noncompensatory.

This implements the proposed `-.05` compatibility margin at the available
resolution while refusing gain-for-loss cancellation. Do not attach a
confidence interval or call this population noninferiority: there is one
excluded history at each size. The later multi-lineage campaign is the
generalization test.

## 4. Release and main-campaign stopping rules

Release `V2.2_ONE_EPOCH_SCALE` only if the complete conjunction passes at both
sizes with zero custody, masking, truncation, nonfinite-update, or final-state
failure. Freeze the exact scale-law code/hash, histories, occurrence ledgers,
readout manifests, and selected DEV writer fields before any confirmation
root is generated.

Possible terminal outcomes are:

- **SCALE PASS:** use it unchanged through the 571-block core campaign.
- **SCALE underfits while FULL passes:** no reduced writer is qualified. Do
  not silently increase epochs, learning rate, rank, replay, or choose a best
  checkpoint. Either fund FULL or develop a separately named bridge.
- **FULL fails:** the five-epoch DEV recipe did not scale safely; SCALE cannot
  be certified by comparison even if it looks better. Return to writer
  development.
- **both fail:** stop the lifetime campaign.

During the lifetime campaign, every promoted write still runs local/locality,
generic-canary, PCFL task-retention, oldest/newest, service, and native gates
at its registered cut. An unsafe write is rolled back for operation, but the
lineage remains a failed intention-to-treat unit. At least 14/16 initial
lineages must complete the full authentic two-SLEEP seam before lifetime
promotion; there is no root replacement. In particular, a cut-2 or cut-3
failure is a main-campaign failure, not retrospective evidence that the
157/571 qualification had validated the untested 295/433 sizes.

Qualification at 571 blocks authorizes only the five-cut core. The optional
709/847-block plateau extension requires a new predeclared terminal-size
compatibility qualification or must remain unrun. It cannot inherit the 571
certificate by extrapolation.

## 5. Independent attack

1. **The scale law is still a dose change.** Preserving rows and wrappers does
   not make five epochs and one epoch equivalent. The paired FULL anchor and
   service/native gates are therefore mandatory.
2. **FULL is not automatically a gold standard at scale.** It was qualified at
   20 slots, not 571. Requiring FULL to pass absolute retention and use gates
   prevents an overfit or destructive reference from blessing SCALE.
3. **Local recall can hide useless memory.** A one-epoch writer could reproduce
   addressed rows yet fail goal-conditioned traversal. Both service and native
   task panels are mandatory. The LINK cut prevents an EVENT-only success from
   masquerading as connected **service** use; native use remains noncausal in
   this four-fit bridge and is labelled accordingly.
4. **Aggregate acquisition can hide forgetting.** The actual-child assay
   retained a generic canary at 36/36 while erasing 45/143 prior skill items.
   The PCFL-specific C0-paired gate and oldest/newest strata are therefore
   noncompensatory.
5. **Two excluded histories do not establish robustness.** This protocol does
   not claim they do. Writer-seed sensitivity and lineage reliability are
   estimated in the preallocated confirmation cohort, with every failure kept.
6. **Replay fillers distort per-row dose.** Exact occurrence ledgers and
   output-blind balanced selection expose the extra eight or 40 presentations;
   no result may be described as uniform-per-row without that qualifier.
7. **Update arithmetic is not compute arithmetic.** Wrapper and response
   lengths determine token work. Measured profiles can invalidate the 142-hour
   planning estimate and trigger a resource stop before N=16.
8. **The cheaper architectures remain real future options.** Warm incremental
   writes with bounded stratified replay could reduce the quadratic lifetime
   cost further, but they change initialization, forgetting dynamics, and the
   recurrence estimand. They require a separate development comparison to the
   qualified clean-base writer and are not an emergency substitution.

## Bottom line

After a complete PCFL DEV v2.2 pass, the four-fit 157/571 qualification above
is the minimum honest bridge from the proven small writer to a five-cut
lifetime campaign. It cuts planned N=16 training from 616.0 to 142.4 A40-hours
without dropping a memory or wrapper. FULL's absolute gates test whether the
shared large-corpus/replay/scheduler extension works; the paired contrast then
makes the additional change—the large-corpus epoch reduction—explicit and
falsifiable. If either layer fails, the paper does not yet have a scalable
SLEEP writer; the correct response is to stop or open a separately named
writer-development program, not to tune inside the confirmation run.

## Inputs inspected

- `AGENTS.md`
- `research_loop/COORDINATION.md` through the 2026-09-13T09:27Z Laptop Codex
  entry
- `research_notes/analysis/2026-09-13_pcfl_vertical_dev_v2_2_writer_repair.md`
- `research_notes/analysis/2026-09-13_actual_child_real_record_memory_pair_terminal_audit.md`
- `research_notes/analysis/2026-09-13_pcfl_dev_to_paper_grade_successor.md`
- `research_notes/analysis/2026-09-13_pcfl_stream16_successor_objective_redteam.md`
- `research_notes/analysis/2026-09-13_pcfl_vertical_dev_v2_synthesis.md`
