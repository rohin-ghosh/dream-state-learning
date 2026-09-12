# Strong evolving active-text comparator for Dream--LoRA--Think

Date: 2026-09-11

Status: **fresh independent design candidate only.** This note authorizes no
source edit, model or tokenizer call, benchmark generation, training, adapter
work, GPU use, scientific claim, release, or submission. It does not amend the
parked C11 guard. Any implementation is a material experiment change and must
take the repository's architecture-deliberation and exact-ratification path.

## Verdict

The current waking brief is not the baseline the paper needs. It is one static,
small summary and the historical comparison is post hoc. The strongest
feasible comparator is a frozen actor with an **evolving, lossless public-event
store plus a verified derived-memory lane**, queried before every decision
under a fixed active-context budget. It should receive memory immediately,
not be artificially delayed to the LoRA's sleep cadence. It should preserve
raw evidence even when a derived summary is wrong or stale.

Call this candidate `ACTIVE_TEXT_EVOLVING` (`ATE`). It combines the strongest
auditable parts of the lines already surveyed in the repository:

- MemGPT/Letta: a bounded active window over a larger external store;
- Generative Agents: relevance plus recency and reflection;
- ExpeL/CLIN: success/failure contrast and reusable procedural abstraction;
- Mem0/A-MEM: typed updates, provenance, links, supersession, and evolution;
- HippoRAG: graph-assisted retrieval for the later PCFL benchmark.

This is an in-project strong baseline, not a claim to reproduce any one of
those systems. Static brief, recency, and raw BM25 remain cheap ablations.

There are two deliberately different versions:

1. `ATE-CG`, the deadline-feasible CompilerGym comparator. It uses public
   action--outcome records, deterministic cross-program action summaries, and
   indexed child-authored compiled text. It can support a bounded carrier or
   finite-life comparison, not the full connected-knowledge claim.
2. `ATE-PCFL`, the later full-objective comparator. It stores exact admitted
   atom/link rows and performs candidate-blind hybrid retrieval plus graph
   expansion. It is the comparator whose prospective plateau is required
   before any claim that Dream--LoRA--Think keeps improving after active text
   saturates.

The primary longitudinal experiment should give `ATE` to **every** arm. The
incremental comparison is therefore `frozen actor + ATE + promoted LoRA`
versus `the same frozen actor + the same ATE policy + shadow LoRA`. This avoids
handicapping the text system and asks whether weights add value after a strong
external memory is already available. A separate same-source carrier probe
compares LoRA-only and text-only reads over byte-identical admitted evidence.

## 1. Common evidence contract

### 1.1 Eligible evidence

An item may enter `ATE` only if all of the following are true:

1. It occurred strictly before the current retrieval query in the same
   scientific life/root.
2. It came from an ordinary wake/deployment task, not a gate, canary, probe,
   report panel, certificate, or evaluator call.
3. An action item names an action the harness actually dispatched. Text that
   merely resembles an `ACT` is ineligible as an action.
4. Its outcome and score are the exact public tool return associated with that
   dispatch. Invalid actions are retained as negative evidence rather than
   dropped.
5. Its objective, public state/features, action, outcome, score, occurrence
   index, and clock are actor-visible or mechanically derived from public
   bytes. Hidden world state, reference answers, oracle paths, future goals,
   evaluator labels, and later outcomes are forbidden.
6. A child thought/review is eligible only as `SELF_INTERPRETATION`, never as
   an established fact. It must be a verbatim child continuation after its
   cited public event(s). Parent words, nursery instructions, compiler-written
   prose, and repaired child endpoints are excluded.
7. A DREAM/SLEEP training item is eligible in the compiled-text lane only when
   its source event IDs and exact source hashes are mechanically recoverable.
   The target bytes may still be a fallible child interpretation; its type
   says so. Failure to validate provenance excludes the item from both ATE and
   a matched carrier comparison.
8. Records from another life/root never enter, except in an explicit
   `WRONG_LIFE` control.

All eligible items enter an append-only evidence ledger. Success filtering is
forbidden at this layer. The raw ledger is never summarized away, overwritten,
or deleted. Probe processes are read-only and their pre/post store root hashes
must match.

### 1.2 Stable identity and receipts

Each public dispatch creates one canonical event block:

```text
event_id, life_id, episode_instance_id, occurrence_index, decision_index,
objective, public_features, action_bytes, public_outcome_bytes,
score_before, score_after, validity, source_envelope_sha256, event_sha256
```

`event_sha256` is the SHA-256 of canonical UTF-8 JSON excluding that field.
Every derived document contains:

```text
document_id, document_type, created_at_event, source_event_ids,
source_set_sha256, scope, status, payload, document_sha256
```

The full sorted source list lives in an immutable sidecar when it is too
large for the actor block. Model-visible documents carry at least two
representative source IDs when two exist, the total support count, and the
support-set digest. A returned document is inserted by the harness with its
ID and digest; the model is never trusted to invent a citation. Model-emitted
`USED_MEMORY` IDs are logged only as a diagnostic and never determine
admission or correctness.

### 1.3 Visibility timing

- Raw event blocks become searchable on the next continuation after the
  public outcome. This is the native advantage of active text and must not be
  artificially delayed until SLEEP.
- Deterministic aggregate cards and validated compiled-text documents refresh
  at the same 32-episode boundary used by SLEEP.
- A failed refresh leaves the prior derived index active while the append-only
  raw store remains available. It is not silently retried after seeing task
  performance.
- In an incremental LoRA experiment, every arm receives the same ATE policy
  and timing. LoRA promotion remains the only treatment difference.

## 2. `ATE-CG`: deadline-feasible CompilerGym baseline

### 2.1 Stored document lanes

`ATE-CG` indexes three lanes.

**Raw lane.** One document per authoritative action/outcome block. The
rendering includes program ID, public dataset prefix, exact normalized pass
sequence, validity, instruction-count reduction, score, and event citation.

**Grounded aggregate lane.** At each 32-episode boundary, recompute from the
complete raw ledger rather than incrementally editing summaries:

- exact-program best valid action and most recent contradiction;
- exact-action-sequence performance over distinct programs;
- matched action-sequence contrasts on programs where both were tried; and
- invalid-action warnings.

For a cross-program exact-sequence card, reduce repeats to one observation per
program before aggregation. Report distinct-program count, median, mean,
lower quartile, invalid rate, and support digest. Rank its conservative value
by

```text
LCB = mean_score - sqrt(log(20) / (2 * n_distinct_programs)).
```

This is an association, not a causal statement about an individual pass.
No pass-level causal effect is inferred from a whole-sequence score.

**Compiled/self lane.** Index every provenance-valid child-authored
post-outcome review and every exact response-target span that the paired LoRA
writer actually trains on. These remain explicitly tagged
`SELF_INTERPRETATION`; retrieval never upgrades their truth status. This lane
gives the textual system access to the same articulated material that weights
receive while the raw/aggregate lanes make it stronger than a static brief.

The persistent store is not capped within a registered life. Its complete
canonical bytes are reported. Only the actor-visible retrieved block is
capped. An arbitrary store cap would manufacture a text plateau and is
therefore forbidden in the lifetime claim.

### 2.2 Query and candidate blindness

There is exactly one automatic query immediately before every actor
continuation. Query bytes contain only:

```text
objective
metric
current public program ID and dataset prefix
last two already-dispatched action sequences
last two public outcome classes/scores
latest child NOTE or explicit RECALL query from a prior continuation
generated-token and action counters
```

The query contains no hidden best pass sequence, candidate action list,
current continuation, unexecuted action from that continuation, evaluator
score, report identity, arm/adapter label, future outcome, or future task. A
free-text hypothesis written in an earlier child continuation may appear in a
later query; that is ordinary agent-controlled memory use, not evaluator
candidate access.

Candidate blindness is tested causally: mutating the hidden reference action,
held-out outcome, candidate ordering, carrier arm name, or future goal while
holding all actor-visible bytes fixed must leave query bytes, returned IDs,
order, and rendering byte-identical.

### 2.3 Frozen retrieval policy

The index uses a pinned lexical tokenizer and a pinned
`BAAI/bge-small-en-v1.5` encoder revision. The eventual implementation packet
must bind the exact model revision and file hashes; an unpinned download is a
failed prerequisite.

For every query:

1. Rank all searchable documents by BM25 and dense cosine similarity.
2. Fuse ranks using reciprocal-rank fusion
   `RRF(d)=1/(60+r_bm25(d))+1/(60+r_dense(d))`; a missing rank contributes
   zero.
3. Pack one 1,024-token block in three reservations:
   - up to 256 tokens: exact-current-program raw/aggregate records, best score
     first and then newest contradiction;
   - up to 256 tokens: cross-program action cards by `LCB`, with greedy pass-
     token diversity;
   - at least 512 tokens: remaining fused results using maximal marginal
     relevance with `lambda=0.8`.
4. Unused reserved capacity flows to the next reservation and finally to the
   fused lane. Documents are indivisible; one that does not fit is skipped.
   Tie-break is `(higher fused score, newer event, lexicographically smaller
   document_id)`.
5. Exact duplicates are returned once. Superseded derived cards are not
   searchable; raw evidence remains searchable. Zero hits yields a canonical
   empty memory block, not a generated fallback.

The encoder and BM25 see the same canonical query. Dense-document embeddings
are cached by document hash. The actor sees no physical latency, cache status,
embedding score, rank score, index size, or miss reason.

### 2.4 Development selection without confirmation leakage

Three fixed candidates run on development lives only:

1. raw hybrid retrieval;
2. raw plus grounded aggregates; and
3. all three lanes above.

Choose once by mean development AUC. A difference below `0.01` selects the
candidate with lower measured retrieval latency; a remaining tie selects the
smaller actor-visible byte count. Freeze the winner, encoder, all ranking
constants, prompts, and certificate thresholds before generating any
confirmation/report bytes. The other two remain disclosed ablations. No
per-program or per-checkpoint winner selection is legal.

### 2.5 Deadline use and claim limit

The lowest-cost deadline test is a **same-source carrier comparison**. From a
sealed eligible source ledger, construct ATE and the LoRA corpus at fixed ages,
then evaluate disposable clones on a fresh source-disjoint panel. This avoids
paying for an additional text-only lifetime and asks whether the two carriers
use the same accumulated evidence differently.

Because the source behavior produced the ledger, this test is a carrier
diagnostic, not an autonomous active-text life and not a continual-learning
claim. A paper-facing system superiority claim needs new independent lives in
which the ATE-only agent gathers its own experience. CompilerGym can support
only a bounded finite-horizon comparison: it repeats about 67 programs, lacks
an identifiable relation graph, and cannot establish connectedness,
goal-conditioned traversal, expansion, or open-ended lifetime growth.

## 3. `ATE-PCFL`: later full-objective baseline

### 3.1 Store and update

The raw lane contains every eligible public action/outcome event. The typed
lane contains only benchmark-compiler-admitted `ATOM_ROW`, `USE_LINK_ROW`, and
new-relation rows with exact public citations. An edge exists only when an
authentic admitted link row says it exists; the baseline may not infer an
edge from hidden PCFL truth or mere co-occurrence. Contradicted/superseded
typed rows stay in the audit ledger but leave the live retrieval graph.

Raw events become visible on the next continuation. Admitted atom/link rows
become visible immediately after their public admission transaction. No
future goal or D-phase target may influence update, indexing, or link
formation. The graph is rebuilt transactionally from the complete live typed
store after every admitted change.

This is separate from `TEXT_SAME_SEMANTICS`. That carrier performs exact slot
lookups and is a mechanism/accessibility ceiling. `ATE-PCFL` must find useful
records from public state and goal without being handed the correct slot.

### 3.2 Read interface and retrieval

Each PCFL decision episode has exactly four retrieval opportunities and one
terminal public action. Each retrieval returns at most 256 tokenizer tokens;
unused calls are charged, so total memory-return allowance is exactly 1,024
tokens. The first query is automatic from public goal/state. On later calls
the actor may supply at most 64 generated tokens of search text based only on
its current public history and previous returned rows.

For each query:

1. Compute BM25 and dense ranks over live raw and typed rows and fuse with the
   same `k=60` RRF rule.
2. Use the top 16 typed rows as seed mass, normalized by positive RRF score.
3. Run personalized PageRank over the public typed atom/link graph with
   restart probability `0.20` for exactly 20 power iterations.
4. Final typed score is `0.5 * normalized_RRF + 0.5 * PPR`; raw rows use
   normalized RRF alone.
5. Pack complete rows by score using MMR `lambda=0.8`, with exact citations,
   until the 256-token cap. No hidden retry, answer-aware rerank, automatic
   solver, or catalog-value lookup exists.

Opaque-handle renaming that preserves public equality/type/ordinal relations
must rename returned bytes equivariantly. Hidden truth, future target, correct
candidate, twin bit, root seed, carrier arm, and evaluator outcome are absent
from the query/ranker. Binding twins alter retrieval only after the altered
public record exists.

### 3.3 Why this is the necessary strong comparator

PCFL is designed so graph-structured active text may be excellent. That is a
feature. If ATE solves the connected/traversal/expansion sequence and LoRA
does not add value, the correct result is that external memory remains the
better substrate at this scale. `TEXT_SAME_SEMANTICS` passing cannot replace
ATE: exact lookup proves row accessibility, whereas ATE tests whether a
frozen actor can maintain and find its own memory under ordinary public cues.

## 4. Fair resource contract

### 4.1 What is equal

Across ATE-only, ATE+LoRA, promoted, shadow, parented, and sham arms:

- byte-identical actor base/checkpoint at the relevant fork;
- identical public task roots, opportunities, action interface, sampling
  tapes, temperature, top-p, and stop rules;
- identical ATE eligibility, update, retrieval, render, and activation policy;
- identical maximum generated actor tokens;
- identical memory-return token allowance;
- identical environment/tool opportunities; and
- invalid/missing actions retained in the denominator.

The active-text block is not subtracted from the actor's generated-token
budget. Every arm has enough model context reserved so its 1,024-token memory
block does not evict more current-state text than another arm. ATE+LoRA and
ATE-only therefore see identical active-context construction.

### 4.2 Generated-token and action budgets

For CompilerGym, the final wake budget is selected once on development tasks
from exactly `{16,32,64}` continuations of at most 400 new tokens each. Choose
the smallest value for which the next doubling improves mean best score by
less than `0.007` and increases valid distinct actions by less than 10%; if no
candidate satisfies both, ship 64. Thus the final exact generated-token cap
is one of `{6,400,12,800,25,600}` per episode and is shared by all arms.
This is the already-ruled token-sufficient policy expressed as a complete
selection rule; it does not reward one system for stopping early.

The budget pilot uses exactly 16 development situations and two common-random
generation seeds for each budget, for both the frozen ATE actor and the
development LoRA+ATE actor. A budget qualifies only if the plateau condition
holds for both actors; otherwise advance to the next value. Pilot situations,
outputs, and summaries are barred from certification and report stores.

There is no lower thought-token target and no scientific cap on how the child
allocates generated tokens between thought and action. All actions written
inside the generated-token envelope are dispatched under the same runner.
To prevent best-of-action volume from masquerading as intelligence, report
score after the first `K in {1,2,4,8,16}` valid dispatches, plus terminal
score, invalid-action rate, distinct valid actions per 1,000 generated tokens,
and generated tokens to first/best score. No cell disappears for producing
too many, too few, or invalid actions. `score@K` is the best score among the
first `min(K,n_valid)` dispatches and is zero when `n_valid=0`; a concise agent
is not penalized merely for stopping before K.

For PCFL, the benchmark itself fixes four memory reads, at most 256 returned
tokens per read, at most 64 actor-generated query tokens on each optional
read, and one terminal environment action. Missing/invalid terminal action is
zero. Other thinking uses the same predeclared token-sufficient actor budget
in every arm.

### 4.3 What is reported rather than falsely matched

For every root, checkpoint, and arm report:

- actor calls, input tokens, output tokens, and occupied-device latency;
- retrieval calls, query/document embedding tokens, BM25 comparisons, graph
  nodes/edges visited, cache hits, CPU time, and latency percentiles;
- public environment dispatches and wall time;
- raw, derived, index, embedding-cache, and total persistent bytes;
- DREAM/updater calls and input/output tokens;
- LoRA training examples, supervised tokens, optimizer steps, GPU-hours,
  energy where available, adapter bytes, and mount overhead; and
- amortized cost per later task at each lifetime cut.

ATE is allowed to be cheaper or more expensive. Equal generated tokens do not
make compute, latency, storage, or input context equal. Accuracy superiority
is reported first under each system's frozen native resources, followed by a
cost--utility Pareto curve. The words `compute matched`, `memory matched`, or
`latency matched` are forbidden unless a separate budget sweep actually
matches that scalar.

## 5. Certification before comparison

Development/tuning cases, certification cases, and scientific roots use
disjoint generator seeds/IDs. After candidate selection, run the fixed system
once on the sealed certificate. A failure yields `BASELINE_INVALID`; it never
becomes evidence that LoRA is superior.

The actor/access certificate has exactly 100 independently generated sealed
cases. Every condition uses the same 100 case IDs and common generation seeds;
empty, malformed, timed-out, or missing outputs remain failures. Mechanical
mutation fixtures are separate and exhaustive over their named mutation
classes.

### 5.1 Model-free gates

All must be exact:

1. Canonical event/document round trip and hash identity: 100%.
2. Raw update coverage over valid and invalid dispatched actions: 100%.
3. No probe/report write and unchanged store/index root across evaluation.
4. No future row before its visibility boundary; availability immediately
   after the bound boundary.
5. Citation identity, source-envelope hash, life/root identity, and support-
   set digest: 100%.
6. Restart, index rebuild, insertion-order permutation, and cache-state tests
   return byte-identical ranked documents.
7. Hidden answer/candidate/future-goal/arm mutations leave retrieval
   byte-identical when actor-visible bytes are fixed.
8. Store swap returns zero old-root IDs and only new-root IDs; empty store
   returns the canonical miss.
9. Budget packing, indivisible-document skip, overflow, tie-break, and
   supersession mutation goldens all match exactly.
10. Resource totals reconcile from per-call rows to root totals with no
    unaccounted call, token, write, or index mutation.

### 5.2 Actor/access gates

Use opposing-memory fixtures under common generation seeds. Thresholds are
prospective and failure-inclusive:

- exact-key retrieval recall within the active budget `=1.00`;
- semantic/public-feature relevant-row recall `>=0.95` where the generator
  supplies a unique public relevance relation;
- harness citation validity `=1.00`;
- GOLD correct-action rate `>=0.85`;
- ATE correct-action rate in each opposing store `>=0.85` and no more than
  `0.05` below its same-sign GOLD condition;
- store-swap redirection contrast `>=0.50`;
- necessary-row cut reduces correct action by at least `0.20`;
- irrelevant-store action-distribution total-variation shift from empty store
  `<=0.05` and task value no worse than empty by more than `0.05`;
- strict action syntax no worse than empty-store actor by more than `0.05`;
  zero-action and DONE-first cases remain failures; and
- an explicit oracle/reference-search condition exceeds the best registered
  fixed routine/no-memory policy by at least `0.10`, proving task headroom.

`ATE-CG` also must be no worse than the best frozen raw-BM25, recency, and
static-brief comparator by more than `0.01` on the sealed certificate, using
a one-sided 95% lower confidence bound on the paired difference. The
store-swap contrast is

```text
0.5 * [(acc(store A under mapping A)-acc(store B under mapping A))
     + (acc(store B under mapping B)-acc(store A under mapping B))].
```

`ATE-PCFL` additionally
must pass authentic-link versus truthful-null/deranged memory, necessary
bridge cut, binding-twin redirection, old+new row cuts, and the complete
end-to-end text relay before it may be called strong. Exact-text slot access is
reported separately and cannot satisfy these active-retrieval gates.

## 6. Plateau and superiority rules

### 6.1 Prospective plateau

Never define a plateau from the learner curve or after seeing which horizon
favors LoRA. Use ATE-only development roots to select one anchor from a fixed
lifetime grid, then freeze it before confirmation LoRA outputs are opened.

At a candidate anchor, use four consecutive fixed cuts ending at that anchor
and the independent-root ATE scores. The anchor is the earliest cut for which
the 90% confidence interval for the root-level linear slope lies wholly in
`[-epsilon,+epsilon]`, and neither of the last two mean interval gains exceeds
`epsilon`. Use:

```text
epsilon_CG   = 0.007 score per 64 deployment episodes
epsilon_PCFL = 0.020 normalized utility per registered information cohort.
```

The anchor is invalid if the store did not acquire the scheduled new public
evidence, any ATE certificate failed, or the explicit oracle has less than
`0.10` value headroom over ATE. If no fixed candidate anchor qualifies, there
is no plateau and no `beyond saturation` claim. A materially negative slope is
degradation, not a plateau.

Confirmation uses the frozen anchor and at least three later fixed cuts. The
ATE confirmation curve must again satisfy the same 90% equivalence test over
the anchor-plus-late window. Checkpoints are repeated measures; separately
initialized lives are the units.

For every slope, first fit ordinary least squares against registered lifetime
units within each independent root, producing one slope per root. Across roots,
the plateau equivalence interval is the ordinary two-sided 90% Student-t
interval (equivalently two one-sided tests at alpha `0.05`). Positive learner
and paired-advantage gates use one-sided 95% Student-t lower bounds over the
corresponding root-level slopes; retention uses the one-sided 95% upper bound;
terminal superiority uses root-paired differences. There is no checkpoint-
level pseudoreplication, outlier removal, bootstrap switch, or alternate test
after outcomes are opened. Raw root distributions and a sensitivity interval
from a predeclared sign-flip permutation are reported; if gross slope
pathology makes the registered t analysis uninterpretable, the confirmatory
claim is `NOT_ESTABLISHED`, not rescued by the sensitivity analysis.

### 6.2 Estimands

There are two and they must not be conflated.

**Same-source carrier estimand.** At fixed age `t`, fork one immutable admitted
evidence set into an ATE-only read and a LoRA-only read:

```text
Delta_carrier(t) = Y_LoRA(same evidence,t) - Y_ATE(same evidence,t).
```

This localizes representation/access. Because it fixes the source experience,
it is not an autonomous learning-life comparison.

**Longitudinal incremental estimand.** Within independent paired life roots,
compare ATE plus promoted SLEEP with ATE plus true shadow SLEEP. At the fork,
both sides have byte-identical ATE state. Shadow SLEEP performs the identical
compile/train transaction but never promotes the candidate adapter. After the
fork, each side applies the same frozen ATE update law to its own eligible
events; later ATE bytes need not remain identical because adapter promotion
may change actions and hence future experience:

```text
Delta_AUC  = AUC(ATE+LoRA) - AUC(ATE+shadow)
Delta_late = slope_late(ATE+LoRA) - slope_late(ATE+shadow).
```

For parenting, retain the root-level difference in differences:

```text
[AUC(parented, promoted)-AUC(parented, shadow)]
- [AUC(sham, promoted)-AUC(sham, shadow)].
```

The primary late-lifetime claim requires, in fixed order:

1. all ATE certification and headroom gates pass;
2. ATE's confirmation late slope is equivalent to zero;
3. the learner's late slope has a one-sided 95% lower bound above zero;
4. the paired slope advantage has a one-sided 95% lower bound above zero;
5. old-cohort competence loss has a one-sided 95% upper bound below `0.05`;
   and
6. the terminal learner-minus-ATE mean is at least `0.05` with its one-sided
   95% lower bound above zero.

Failure at any step blocks the higher claim but preserves lower descriptive
results. ATE winning is a valid result. It localizes the bottleneck to
parametric writing/access rather than invalidating the benchmark.

## 7. Information-efficient execution order

1. **CPU only:** implement canonical events, three CompilerGym candidate
   stores, ranker, blindness mutants, packing goldens, and resource ledger.
2. **Small actor certificate:** opposing-store/GOLD/empty/irrelevant canaries.
   Stop if the frozen actor cannot use correctly retrieved text.
3. **Deadline carrier read:** run the frozen ATE winner over already sealed
   eligible source ledgers and a fresh source-disjoint panel. This gives a
   legitimate carrier diagnostic for far less cost than a new 1,024-episode
   text life.
4. **Only after writer and carrier gates:** put ATE into every clean
   promoted/shadow parenting or deployment arm. Do not run a historical
   RP-versus-R2 pseudo-factorial.
5. **PCFL CPU theorem and exact-text relay first.** Implement ATE-PCFL only
   after the task generator, authentic row compiler, cuts, and twins are
   fixed. Run its text certificate before a LoRA fit.
6. **Prospective ATE plateau DEV, then confirmation.** Never infer plateau
   from CompilerGym's 67-program repetition or an arbitrary store cap.

ATE requires no training GPU. Its incremental scientific cost is actor
inference plus CPU indexing/embedding. This is the correct place to be
generous: a weak retrieval baseline would make any LoRA advantage
unpublishable, while a passing/strong ATE can falsify an expensive downstream
experiment before hundreds of training GPU-hours are spent.

## 8. Claim boundary

- ATE-CG beating a static brief says the earlier brief was weak, not that text
  memory is solved.
- LoRA beating ATE on a same-source carrier probe says only that the tested
  parametric read used that fixed evidence better.
- ATE+LoRA beating ATE+shadow over independent lives supports bounded
  incremental value from promoted parametric consolidation.
- Only ATE-PCFL plus the prospective plateau and late-window design can support
  `continued improvement after a strong active-text memory plateau`.
- Neither baseline licenses connectedness, traversal, expansion, compression,
  parenting, recurrence, or a whole-organism claim. Those require their own
  interventions in the full closure ladder.
- Store bytes, adapter bytes, input context, and utility must be measured
  before using `compressed`. A fixed 1,024-token active window does not make
  the persistent text store compressed.

## 9. Relation to existing repository artifacts

- `research_loop/plans/active_text_fixed_contract_v1.md` is a useful exactness
  inventory, but its two model calls, 866-line transition language, and 4,400
  query-embedding budget per root are too heavy for the deadline comparator.
  It should not be silently implemented as ATE.
- `TEXT_SAME_SEMANTICS` in the PCFL relay is retained as an exact-carrier
  ceiling, not relabeled as active memory.
- `gpu/brief_baseline*.sh` and the matched nine-life audit remain historical
  diagnostics; they do not certify ATE.
- The full C11 custody guard stays parked until the final paper-grade C11 run,
  per the current human ruling.

The next architecture packet should bind this note only after an independent
scientific critic attacks the candidate-blind query, common-ATE treatment,
plateau test, and cost claims. Until then it is a proposed comparator, not a
run plan.
