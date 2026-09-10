# Public Pathway Consolidation v2 — identification amendment

Status: rework proposal only. The complete proposed architecture is the v1
protocol at SHA-256
`fca9eac73b91c511682bc5f7dd6c010063ec85ae07f91b588782ea41f290aafc`
plus this amendment. This file supersedes every conflicting v1 clause. It
disposes the v1 adjudicated rework at SHA-256
`6d72e6177139a5373572ad8983f284168a83101139f3f82c3109eafc42722215`.

Parenting/Stage D is removed from the current implementation and experiment
scope. It remains a separately deliberated future study. ENDPOINT is fully
defined here and receives no authority from the unratified v9 proposal.

## A1. Visibility is split at the finite boundary

Replace `sealed_target_results` with three disjoint items:

1. `current_item_public_transition`: the ordinary result and next public state
   from the immediately preceding action. It is visible only to later calls in
   that same target item and is never visible to another item or SLEEP.
2. `quarantined_item_score`: normalized return, regret, success labels, hidden
   evaluator values, and aggregate metrics. These are invisible to all model,
   DREAM, SLEEP, retrieval, and later-target processes until audit.
3. `prior_item_result`: every public or hidden result from an already completed
   target item. It is forbidden to all later target calls and every writer.

The complete visibility taxonomy additionally names:

```text
source public state/events             model-visible where causally prior
public THINK/DREAM workspace           visible only within its life/item scope
source action outcome                  visible after commit in the source life
target goal/current public state       visible in that target only
hidden truth/oracle/proof graph         forbidden outside isolated CPU/audit
scorer/evaluator/offline verdict        forbidden outside quarantine/audit
condition/trainer/adapter identity      derived effect only; prompt-forbidden
writer eligibility/support status       writer/audit only; model-confidence blind
target manifest membership/order        harness only; prompt-forbidden
paths, filenames, environment variables normalized; no condition/answer encoding
timing, cache, batching, and error text  fixed or normalized across conditions
```

Every prompt builder takes an allowlist, not a redact-afterward object. A
counterfactual visibility test mutates each forbidden item independently and
requires byte-identical model-visible inputs and writer rows.

## A2. Causal prefixes and answer-laundering closure

A `DECIDE` row for operation `o_t` contains only the exact allowlisted public
state committed strictly before `o_t`. A `READ` row contains only the exact
query and target-blind candidate domain committed before its return. Future
state, future action/outcome, terminal best, offline score, hidden truth,
evaluation target, answer key, proof graph, condition label, trainer state,
and subsequent DREAM/SLEEP artifacts are denied by field schema and byte scan.

For every row, mutate or replace the complete future suffix, target truth,
offline scores, and other conditions' state; the serialized input and target
must remain byte-identical. The row records a causal-prefix hash and the exact
root event-equivalence classes it depends on.

`REQUEST_DREAM` is the eleventh charged THINK operation. Its only payload is:

```text
active_subgoal_id
reason in {CONTEXT_PRESSURE, CONFLICT, STALLED, SURPRISE, REORGANIZE}
ordered unresolved_record_ids already visible on the current active branch
```

It contains no free text, candidate object, proposed answer, action, hypothesis,
confidence, goal paraphrase, or query text. DREAM receives those requested
records, their complete public ancestor closure, and then the most recent
causally prior public outcomes until the fixed token allowance is full. Ordering
is ancestor-topological then chronological; if mandatory closure exceeds the
allowance the request fails charged rather than truncating evidence. No
retrieval ranker, model guess, future suffix, or target field fills the slice.

DREAM output may influence the next public workspace as provisional state. For
SLEEP, its text and the originating query/goal/hypothesis are selection-only.
Any positive semantic row is regenerated mechanically from cited public root
events; any positive policy row uses its exact causal prefix. Agenda bytes can
never serve as evidence or be copied into a factual target.

## A3. Normative THINK/DREAM state machine

The public state freezes these fields:

```text
scope/life/item IDs; current open branch; branch parent/status;
open subgoal stack; hypothesis DAG/status/citations; opened memory IDs;
pending prediction and bound next action; unresolved surprises;
last current-item public transition; operation/read/action/token budgets;
per-operation repeat counters; schema/prompt/parser/model/adapter hashes
```

Legal transitions are:

* `OPEN_SUBGOAL`: add one child of the active open branch.
* `QUERY_LEDGER`: issue one typed bounded query from active-branch public bytes.
* `FOLLOW`: open one link from a record returned on the active branch.
* `HYPOTHESIZE`: add one provisional node citing only visible active-branch
  records/hypotheses.
* `PREDICT`: bind one direction/value range and one proposed next action to the
  active branch.
* `ACT`: requires a live bound prediction and citations whose complete branch
  ancestry is open; it executes one environment action and consumes one action.
* `REVISE`: append one replacement for a live active-branch hypothesis.
* `BACKTRACK`: mark the current branch abandoned and activate its nearest open
  ancestor or sibling. Abandoned descendants cannot support `ACT`, `STOP`, or
  later positive rows unless a separately charged `REOPEN` operation is added
  in a future protocol; v2 has none.
* `REQUEST_DREAM`: follow A2 and consume one ordinary model-call allowance plus
  the declared dream allowance.
* `DEFER` or `STOP`: terminate without releasing material from an abandoned or
  unsupported branch.

One call yields at most one operation. Parse failure, illegal transition,
invalid environment action, repeated operation, and provider failure consume
their declared budgets and never receive an invisible retry. Repeat counters
are rendered in the next prompt. Three identical normalized operations from an
unchanged state force charged `DEFER(REPEAT_LIMIT)`.

DREAM has its own strict parser and one replacement-workspace publication. It
may retain/drop visible IDs, add provisional cited links/questions, or revise a
working hypothesis; it may not act, read hidden state, change evidence status,
publish an adapter, or release a final answer. Prompt, schema, parser, and
operation enum hashes are part of every trace and T01.

## A4. Restricted credit and root-provenance algebra

CompilerGym deletion replay is defined exactly. Reset the same program, replay
the same fixed pass-ID sequence open-loop, omit exactly action `i`, and apply
every later pass to the counterfactual state without policy reselection. If a
later pass is unavailable or the replay/state hash is non-reproducible, the
deletion result is `UNDEFINED` and supplies no positive row. Otherwise action
`i` is `sequence_essential_for_this_trace` only when the full-sequence terminal
score exceeds the deletion score by the predeclared exact rational margin.

That label supports the action target only. It does not validate a hypothesis,
query, prediction, semantic claim, alternative sequence, or unique causal
explanation. Non-action operations on a successful/recovery path are labeled
`outcome_associated`; PATH may train them, but the paper attributes their value
only through PATH-SHUFFLE, COGNITIVE_NO_ACT, recurrence removal, and downstream
action/path interventions.

Every raw public action/outcome event defines one root equivalence class.
Paraphrases, reverse cues, multi-view rows, copied DREAM links, replayed text,
and descendants retain the union of their root classes and never create new
support. Independent support requires disjoint root classes from distinct
source tasks. The semantic/path graph may contain diamonds; a topological
cycle test runs on node IDs, while root-set union prevents two diamond branches
from masquerading as independent. Descendants can never support their ancestor.

## A5. Self-contained writer conditions and factorization

ENDPOINT is now fully specified: from the sealed source life, select only
actions whose immediate committed source transition improved the exact metric.
Render the exact causally prior conscious state as input and one runtime-format
`ACT(pass_id)` or domain-equivalent action as target. No future result, rationale,
READ, hypothesis, dream, terminal-best label, or target byte enters. Deduplicate
by input/target/root-set identity and use the same adapter-arm sampler and
training recipe as the other trained conditions.

Stage B contains these common-source conditions:

```text
STANDARD          current item + scratch only; no lifetime state
FULL_CONTEXT      exact raw source while it fits, then registered recency truncation
TARGET_STATE_ONLY current public target bytes; no lifetime state or model history
RAW_RAG           bounded raw-event retrieval; no adapter
EXPLICIT_GRAPH    independent atomic graph over the permitted accepted corpus
LINKED_TEXT       accepted authentic pathway DAG via bounded linked retrieval
ENDPOINT          immediate-improvement action-only LoRA
READ_LORA         supported local READ rows only; frozen base THINK policy
DECIDE_LORA       outcome-associated public DECIDE rows, excluding ACT targets
PATH              joint READ + complete authentic DECIDE/action pathway LoRA
PATH_SHUFFLE      PATH marginals with parent/order links shuffled within root/outcome strata
PATH_ONE_SHOT     PATH memory/corpus with queries committed before returns and no FOLLOW
```

The fixed-corpus transport assay separately freezes one accepted semantic corpus
and one recurrent thinker. `TEXT_READ` and `READ_LORA` expose the same one-record
return schema and target-blind candidate domain. Exact, reverse, paraphrase, and
partial-cue probes measure read fidelity. This assay alone identifies transport;
the end-to-end PATH versus LINKED_TEXT contrast remains a coupled systems test.

The row factorial is `READ_LORA`, `DECIDE_LORA`, and `PATH`. The adapter remains
one coupled learned object; separate function credit is made only where this
factorial and fixed-corpus transport assay identify it.

## A6. Matching uses meaningful resource classes

All behavioral conditions match model revision, public goal/state, inference
prompt/interface, maximum model calls, reads, environment actions, input/output
tokens, decoding, clock policy, and cold-process/cache policy.

All trained adapter conditions additionally match rank/modules, optimizer,
trained output tokens, update count, effective touches, sampling seed, clean-base
rebuild, and publication/mount lifecycle. No-adapter conditions are not padded
with meaningless training.

Every condition reports construction calls/tokens/time; retained payload,
metadata, index, adapter, and manifest bytes; training FLOPs/time; reader
candidate work and index scans; inference calls/tokens/latency; cache/KV bytes;
and environment actions/time. Cross-substrate conclusions are stated against
both equal inference resources and the fully reported substrate-specific costs.

## A7. Executed recurrence, bypass, and construct scorecard

`PATH_ONE_SHOT` is an executed treatment ablation, not an oracle substitute. It
uses the identical PATH accepted content and candidate domain, but commits all
queries before any return, forbids FOLLOW/value-dependent query, and receives
the same maximum calls, reads, tokens, and actions. Unused allowances are
charged. PATH receives constructive credit only when it beats PATH_ONE_SHOT and
shows a mechanically valid adaptive dependency path.

The independent target sealer must establish that target-only/state-only
classifiers, passive signatures, identifier/order features, standard prompted
agents, and non-adaptive readers remain below registered ceilings. FULL_CONTEXT,
RAW_RAG, EXPLICIT_GRAPH, and LINKED_TEXT are mandatory strong memory baselines,
not optional diagnostics.

The preregistered scorecard reports and gates separately:

1. exact/reverse/paraphrase/partial-cue local recall;
2. adaptive dependency and cited path depth;
3. fresh-handle and prospective-schema generalization;
4. prediction calibration and revision after contradiction;
5. ordered planning validity and setup->payoff completion;
6. final action value/regret and information gain;
7. authentic path/twin/binding/memory-cut sensitivity;
8. false-memory use, unsupported claims, and abstention.

Aggregate action improvement cannot substitute for a failed construct gate.

## A8. Correct promotion rule

PATH can establish a pathway-over-ENDPOINT mechanism only if it beats ENDPOINT,
PATH_SHUFFLE, and PATH_ONE_SHOT; has a same-state mounted-over-unmounted effect;
passes the relevant construct scorecard; and loses the registered portion of
its advantage under authentic path/twin/binding cuts.

A LoRA-specific treatment or claim additionally requires PATH to beat the
strongest registered external-memory baseline, including LINKED_TEXT and
EXPLICIT_GRAPH, under the declared resource view. If authentic linked/graph
memory matches or wins, Stage B may report pathway evidence but Stage C must
carry that winning external treatment alongside PATH; it may not call LoRA a
moat or select LoRA as the unique learning system.

## A9. Stage C identifies the complete mediated flywheel

The final Stage-C estimand is not merely a bounded performance curve. Each life
contains predeclared epistemic actions whose immediate purpose is to reduce a
typed uncertainty. Compiler pass trials may count only when a pre-action public
prediction names the uncertainty; PCFL supplies explicit survey/assay actions.

For registered mediation episodes preserve:

```text
assigned prior memory
 -> selected epistemic action
 -> new public observation
 -> exact later SLEEP admission/row or rejection
 -> later goal-conditioned read/path
 -> later action value
```

Run same-state/wrong-memory or memory-cut intervention at the epistemic choice;
run an observation-removal intervention at the next sleep; and run the existing
path/binding cut at the later action. Full-flywheel credit requires all three
links in the registered direction. A yoked fixed-deck acquisition control gets
the same observation multiset without policy selection. CompilerGym may support
agency/action improvement; the full semantic mediation claim requires PCFL.

The paper-scale design freezes before execution:

* one pre-native checkpoint and at least three checkpoints strictly beyond the
  measured native full-context capacity `C`;
* genuinely new root-equivalence classes and unique mappings at every point;
* new-acquisition, old-retention, and cross-era-composition panels;
* adapter ranks `{4,16,64}` at registered response-surface checkpoints and
  matched retained-byte caps for text/graph memory;
* common fixed base plus one selected primary rank for the longitudinal curve;
* independent life roots as the sampling unit, targets nested within root;
* co-primary root-level contrasts, estimator, multiplicity correction, effect
  threshold, confidence interval, missing-root rule, and stop/futility rule;
* sample size fixed from disjoint development variance before sealed evaluation,
  with no post-hoc root/target/checkpoint addition;
* AUC and finite differences as secondary longitudinal summaries, never noisy
  per-target derivatives treated as independent samples.

Compression requires improving or preserved new/old/cross-era value while the
minimal sufficient statistic grows, under fixed adapter bytes; a rank that must
grow linearly with new information is storage, not fixed-substrate compression.
Saturation/crossover language requires the registered strong baseline's curve
to actually flatten or degrade while the treatment continues improving over
the declared interval.

## A10. Independent seals and durable lifecycle

The two sealers must be independently implemented: one uses the production
enumerator and one is authored from the protocol without importing production
selection code. They compare canonical URIs, bitcode/content hashes, complete
serialized model-visible bytes, target ordering, generator seeds, complementarity
replays, PCFL twins, direct-record closure, passive-signature/classifier results,
and shortcut ceilings. Shared byte identity alone is insufficient.

The exact run manifest freezes a lifecycle transition table covering source
reset/call/parse/action/commit; DREAM request/slice/call/publication; SLEEP
selection/admission/serialization/training/publication/mount; each condition
fork; target reset/call/read/action/current-item transition/quarantine; each cut,
shuffle, and same-state mount; and final audit/release.

At every boundary, tests inject ordinary failure and integrity failure. Ordinary
failure may resume only from the last exact hash-bound committed boundary using
the same artifacts; it cannot regenerate, reseed, substitute, skip, or repair.
Integrity failure stops all remaining work and suppresses numeric release. A
target-cell ordinary failure seals that cell missing and follows the predeclared
panel policy; no cell retries. Postrun audit compares the actual ordered event
suffix with the frozen table and rejects any forbidden continuation.

## A11. Acceptance-test replacement

Replace v1 T01--T06 with:

* `PPC2_T01_VISIBILITY_CAUSAL_PREFIX_GOLDENS`
* `PPC2_T02_THINK_DREAM_STATE_MACHINE_GOLDENS`
* `PPC2_T03_CREDIT_PROVENANCE_GOLDENS`
* `PPC2_T04_WRITER_FACTORIAL_RESOURCE_GOLDENS`
* `PPC2_T05_INDEPENDENT_DUAL_SEAL_AND_SHORTCUT_AUDIT`
* `PPC2_T06_CONSTRUCT_RECURRENCE_BASELINE_GATE`
* `PPC2_T07_MEDIATION_CAPACITY_STATISTICS_MANIFEST`
* `PPC2_T08_PRE_GPU_INDEPENDENT_REVIEW`
* `PPC2_T09_POSTRUN_CAUSAL_LIFECYCLE_AUDIT`

T01 mutates every forbidden visibility class and future suffix and requires
byte-invariant prompts/rows. T02 exhausts every legal/illegal transition,
repeat, abandoned-branch, DREAM slice, budget, prompt/schema/parser hash, and
failure boundary. T03 covers exact deletion replay, undefined counterfactuals,
root equivalence, diamonds, cycles, descendants, support, and restricted row
labels. T04 reconstructs all conditions, row families, transport probes,
meaningful budget classes, full resource ledgers, trainer lifecycle, and mounts.
T05 runs the two independent sealers and all identity/signature/shortcut/twin/
closure audits. T06 requires each construct score and executed baseline/
recurrence/cut gate separately. T07 binds Stage C's mediation interventions,
capacity/byte grid, genuine-information schedule, estimand, power/sample size,
missingness, multiplicity, effect threshold, and futility rule. T08 binds exact
implementation, T01--T07, lifecycle, quantitative compute manifest, canary, and
one exact run for a fresh reviewer and non-overriding advocate. T09 recomputes
every actual artifact, intervention, statistic, ordered lifecycle suffix, and
claim boundary before releasing any value.

## A12. Human and scope boundary

Current ratification may authorize only isolated PPC2 contracts, independent
CPU fixtures, and the two no-model environment sealers. Parenting, model calls,
training, GPU science, Stage-B execution, and Stage-C execution remain forbidden.
After T01--T08, the exact model/GPU manifest requires a separate human
ratification. Parenting requires its own future directive, task-channel tests,
wrong-lineage controls, deliberation, and ratification.
