# ACTIVE_TEXT_NATIVE v2: smallest strong evolving PCFL text-memory opponent

**Date:** 2026-09-13 PT  
**Role:** fresh design synthesis for the full Dream--LoRA--Think objective  
**Evidence cut:** repository through `1f4dd6fa`  
**Scope:** documentation only; no source, model, tokenizer, benchmark, fit,
adapter, GPU, remote, or scientific execution

## Verdict

Build exactly one new external-memory system for the lifetime comparison:
`ACTIVE_TEXT_NATIVE-v2` (`ATN-v2`). It is a frozen child whose only
post-deployment learning is an unlimited, lossless, branch-local textual store
plus deterministic BM25 and typed-graph retrieval. It starts empty, sees the
same public action--outcome frontier as Dream--LoRA--Think, admits the same
*kinds* of child-authored `EVENT` and `LINK` records on its own branch, and
must find useful evidence from the current goal/state rather than receiving an
answer address.

This is not the current v2.2 `ACTIVE_LINKED_TEXT`. That condition is an exact
address-to-row **supplied-memory service ceiling**. Keep it, but never call it
the strong baseline. Use these names without aliases:

| name | role |
|---|---|
| `ACTIVE_LINKED_TEXT_SUPPLIED` | corrected C0/v2.2 exact-address service ceiling |
| `TEXT_SAME_SEMANTICS` | finite exact-row carrier diagnostic; no ranking or graph expansion |
| `RAW_RAG` | lexical-only ablation over chronological public events |
| **`ACTIVE_TEXT_NATIVE-v2`** | standalone evolving strong external-memory opponent |

The smallest credible ATN implementation does **not** need a dense encoder or
an LLM memory updater. PCFL already provides public typed records. Use exact
BM25 over raw plus typed rows and PageRank only over graph structure explicitly
present in authenticated child rows. This is executable, deterministic,
restartable, target-blind, and strong enough to win. If it wins, that is a
valid scientific result.

The paper needs two ATN evaluations, not two different systems:

1. **On-policy opponent:** ATN grows from its own branch's experience and is
   compared with `DLT_PERIODIC` and `SLEEP_FROZEN` as a total system.
2. **Same-DLT-history read:** a disposable ATN index is rebuilt from the exact
   eligible DLT history at every cut. This distinguishes carrier/access from
   differences in the experiences the systems chose to collect.

One frozen updater, ranker, interface, and budget serves both. No baseline
training fit is required.

## 1. Scientific unit and branch contract

One independent lifetime root is one sealed, parent-deleted child state plus
one world-root/learner-seed tuple, copied before branch policy is mounted:

```text
SEALED_CHILD
  -> DLT_PERIODIC        personal LoRA writes; registered raw episodic RECALL
  -> SLEEP_FROZEN        same wake/formation opportunities; no promoted write
  -> ACTIVE_TEXT_NATIVE  frozen weights; evolving raw+typed text memory
```

The branches share a precommitted action-contingent opportunity/outcome tape,
task schedule, decode tape, actor grammar, cumulative generated-token cap,
nonterminal-turn cap, final-action cap, parser, and scorer. Each branch sees
only the public results of actions it actually dispatches. Once policies
diverge, their histories may diverge; that is the whole-system estimand, not a
matching failure.

At each registered cut, create a read-only disposable index from DLT's exact
history and evaluate `ACTIVE_TEXT_NATIVE-v2/FIXED_DLT_HISTORY` on the identical
exam tasks and common decode addresses. It receives no DLT latent state,
private DREAM prose, repeated wrapper exposure, or evaluator result.

The paired root, not a task, goal, decode, row, checkpoint, optimizer seed, or
surface twin, is the replication unit.

## 2. Data lifecycle

### 2.1 Immutable evidence lane

Every ordinary dispatched action creates one canonical event envelope:

```text
schema_version
scientific_root
branch
module_id
episode_instance
occurrence_index
decision_index
objective_public
state_public
action_raw
outcome_public_raw
validity
score_before_public
score_after_public
source_envelope_sha256
event_id
```

`event_id` is the SHA-256 of JCS-canonical UTF-8 bytes excluding `event_id`,
followed by exactly one LF in the persisted JSONL record. Invalid actions and
negative outcomes remain evidence. Probe, canary, certificate, report, and
exam events never enter a scientific store. Parent/nursery text, hidden world
state, oracle routes, future goals, reference answers, evaluator labels, and
other-root records are forbidden.

Raw events become searchable on the **next continuation in the same episode**.
Events from sibling episodes in a batched round become visible only at the
complete batch barrier in canonical order
`(cohort,module,episode_instance,occurrence_index,decision_index)`. Process
completion order, device, cache, and branch label cannot change visibility.

### 2.2 Child-record lane

The ordinary child receives the same bounded PCFL formation opportunities as
the DLT branch. Its exact emitted bytes are preserved. A mechanical public
validator may authenticate, but never propose, repair, complete, rank, or
select, either:

```text
EVENT <event> AT <source> DID <port> GOT <destination> EVIDENCE <receipt>
LINK <link> FROM <event1> THEN <event2> VIA <shared> EVIDENCE <r1>,<r2>
```

Any publicly valid direct `LINK` pair may be admitted in child-chosen order;
there is no hidden or disclosed preselected pair. Accepted rows enter the live
typed store at the common authenticated admission frontier. Rejected rows and
their reason remain in the append-only self-interpretation/audit lane and are
searchable as fallible child history, but cannot create graph edges.

Every stored document has immutable `document_id`, creator/type, creation
frontier, ordered source-event IDs, support-set digest, root, live/superseded
status, payload bytes, and document hash. Every actor-visible result carries
harness-inserted citations. Model-invented citations confer no authority.

The persistent store is unlimited within the registered lifetime. Nothing is
evicted, summarized away, or duplicated to mimic LoRA epochs. Indexes and
caches are rebuildable derivatives; the append-only ledger is authoritative.

### 2.3 Exact same-history law

At each cut, the fixed-history ATN store contains exactly once:

- every eligible unique DLT public event visible by that frontier;
- every exact DLT child-authored accepted `EVENT`/`LINK` row;
- every rejected child-row attempt and status; and
- no compiler paraphrase, replay copy, answer, inferred edge, or DLT-only
  latent proposition.

This is the strongest information-faithful text comparison (`ALT_FULL` in
older notes). Optimizer views are exposures, not new experiences; the text
system is not weakened or strengthened by copying a row eight or forty times.

## 3. One actor interface and sufficient budgets

All three lifetime branches use the same recurrent actor command surface:

```text
THINK <one child continuation>
RECALL <one query of at most 64 child-tokenizer tokens>
ROUTE <exact PCFL route grammar>
PROBE <exact PCFL probe grammar>
```

Exactly one command is allowed per model call. `THINK` is returned as ordinary
conversation state on the next call. `RECALL` is charged as generated actor
text. A final `ROUTE` or `PROBE` ends the task; malformed, multiple, missing,
or late final actions score zero. There is no retry or generated fallback.

Per task, every branch receives:

- at most **16 nonterminal turns** and then one final opportunity;
- at most **2,048 cumulative generated child tokens**, including `THINK` and
  `RECALL` text;
- exactly the same terminal environment-action allowance; and
- the same reserved task/state/history partitions and output reserve.

ATN may execute at most 16 charged retrievals and receive at most 512 complete
row-rendering tokens per retrieval, **8,192 returned tokens cumulative**.
Misses, repeated queries, skipped overlength rows, and unused reads are
charged and never replaced. `DLT_PERIODIC` and `SLEEP_FROZEN` retain only the
same registered lexical raw-episodic `RECALL` capability already part of the
organism; they receive no typed graph, inferred neighbor, ATN aggregate, or
PPR result. The interface and opportunity count are identical; the memory
policy is the treatment.

The pinned child tokenizer must prove before any actor call that the maximum
task/state, 16 query/return turns, 8,192 returned tokens, child state, and
reserved output all fit without backend truncation. Every prompt receipts
kept/dropped token IDs. If the maximum does not fit, q16/B8192 is invalid; do
not silently shrink it and call the result strong.

## 4. Frozen retrieval and graph arithmetic

### 4.1 Identifier normalization and BM25

Both query and documents replace every opaque public identifier with its
sealed registered-public-slot token:
`NORM/<PUBLIC_TYPE>/<ZERO_PADDED_SLOT>`. Original bytes are restored only in
actor rendering. Missing/duplicate/mutable slots fail certification.

After NFKC and lowercase conversion, tokenize on maximal ASCII alphanumeric,
underscore, and slash runs. Use term frequency over the complete canonical
actor rendering. BM25 is exact float64 with:

```text
k1 = 1.2
b  = 0.75
idf(t) = ln(1 + (N - df(t) + 0.5) / (df(t) + 0.5))
```

All query term frequencies are one. Zero-score documents are absent from the
lexical candidate set. Ties use immutable public event ordinal, then
`document_id` ascending. Raw and typed live rows share one document-frequency
universe. Superseded typed rows and rejected interpretations remain in the
audit ledger but not the live typed index.

### 4.2 Typed public graph

The retrieval graph contains only authenticated public typed records. It is
an undirected, unit-weight bipartite graph with document and public-symbol
vertices:

- an `EVENT` document connects to its public `source`, `port`, and
  `destination` symbol vertices;
- a `LINK` document connects to its two referenced live `EVENT` document
  vertices and its public `VIA` symbol vertex; and
- no receipt, goal, answer, hidden family, compiler inference, rejected row,
  or raw co-occurrence creates an edge.

Take the top 16 positive-BM25 live typed documents as restart seeds, weighted
by their positive BM25 scores normalized to sum one. If no typed seed exists,
graph mass is zero. Run exactly 20 float64 power iterations with restart
probability `0.20`, starting at the restart vector. A dangling vertex returns
all of its mass to the restart vector.

Let `L(d)` be positive BM25 normalized over all positive live documents and
`G(d)` be final PageRank mass renormalized over typed document vertices. Rank:

```text
typed document: S(d) = 0.5 * L(d) + 0.5 * G(d)
raw document:   S(d) = L(d)
```

This intentionally lets raw exact evidence remain competitive while giving
declared connections an explicit retrieval path. PPR is part of the baseline,
not evidence that the child or LoRA traversed a graph.

### 4.3 Complete-row packing

For each retrieval, reserve the first 128 tokens for the highest lexical
exact-hit raw or `EVENT` row. Unused space flows to the general pool. Fill the
remaining 512-token return with complete rows chosen greedily by:

```text
MMR(d) = 0.8*S(d) - 0.2*max_jaccard(retrieval_tokens(d), selected_rows)
```

The empty selected-set similarity is zero. A row that does not fit is skipped;
rows are never truncated. Ties use higher `S`, newer causal frontier, then
smaller `document_id`. Exact document IDs occur at most once per return. The
actor sees the original opaque identifiers and compact canonical payload plus
citation IDs, not scores, ranks, cache state, or hidden metadata.

All numeric constants, float byte representations, token counts, graph
construction, tie cases, empty/miss behavior, and restart behavior require
byte-exact goldens. There is no dense encoder, query rewriter, answer-aware
reranker, automatic solver, hidden retry, or library default left normative.

## 5. Controls and certification

Development, certificate, and scientific roots are disjoint. There is no
retriever winner selection: q16/B8192 and the arithmetic above are frozen
before the four certificate roots exist. Lower-access points are descriptive
only. Certificate failure is `BASELINE_INVALID`, never evidence for LoRA.

### 5.1 Model-free gates -- all exact

1. Event/document round trip, hashes, citations, source/root identity: 100%.
2. Every valid/invalid ordinary dispatch enters raw storage exactly once.
3. Visibility frontier and sibling-batch barrier are exact.
4. Restart, insertion-order permutation, cache-cold/warm rebuild, and process
   placement return byte-identical rankings and renderings.
5. Future answer, hidden route, candidate order, goal suffix, carrier label,
   and later outcome mutations leave retrieval identical when public bytes are
   fixed.
6. Public-ID renaming changes rendered identifiers equivariantly and leaves
   ranks/ties unchanged.
7. Store swap yields no old-root ID; empty store yields canonical `MISS`.
8. Graph edges equal the authenticated live typed rows exactly; rejected,
   cut, superseded, and wrong-root rows have zero live edges.
9. Packing, overflow, max-turn, cumulative-token, terminal action, and no-
   backend-truncation goldens are exact.
10. Evaluation run-versus-skip leaves store/index/cache/query-state roots
    byte-identical; all per-call resource totals reconcile.

### 5.2 Four-root actor/access certificate

Use four fresh baseline-only roots, 16 fixed tasks/root:

```text
2 information strata (opaque binding, reusable structure)
x 4 endpoint types (route, same-evidence/different-goal,
                    delayed OLD+NEW, expansion)
x 2 surface/order twins
= 16/root = 64 cases
```

No identical answer row exists in the reusable stratum. The exact public
evidence must nevertheless identify the needed relation.

Run the same 64 cases under exactly eight memory conditions:

1. `FULL_CHILD_TEXT`
2. `EXACT_WITNESSED_GRAPH`
3. `ACTIVE_TEXT_NATIVE-v2`
4. `NONE`
5. `TRUTHFUL_BINDING_TWIN`
6. `REGISTERED_NECESSARY_CUT`
7. `IRRELEVANT_STORE`
8. `WRONG_ROOT_STORE`

Each case's necessary cut is preassigned so every root has four atom cuts,
four LINK cuts, four OLD cuts, and four NEW cuts. All 512 results remain in the
denominator. Pass is noncompensatory:

- `FULL_CHILD_TEXT`, `EXACT_WITNESSED_GRAPH`, and ATN each `>=60/64`, no root
  below `14/16`;
- legal final actions `>=61/64` in each of those three conditions;
- exact harness citations `=1.00`;
- an exact-address atomic fixture returns its required `EVENT` in `64/64`;
- ATN retrieves the complete registered necessary EVENT/LINK bundle somewhere
  within B8192 in `>=60/64`, no root below `14/16`;
- truthful twin memory redirects the registered action in `>=12/16` on every
  root;
- each cut family loses at least `3/4` designated cases on every root
  (`>=12/16` pooled per family);
- irrelevant and wrong-root stores each change pooled utility and legality
  from `NONE` by at most `3/64`, with zero valid false-root citation;
- `EXACT_WITNESSED_GRAPH - NONE >=0.10`; and
- reusable-structure ATN success `>=30/32`.

If exact/full ceilings fail, repair the actor interface or benchmark. If only
ATN fails, repair/review ATN on excluded roots and issue a new frozen version;
do not spend lifetime roots. Never loosen a threshold after seeing which arm
wins.

### 5.3 Context-position sensitivity

At certificate time, compare DLT native-empty memory position against an
equal-wrapper, equal-position, equal-token target-independent sham on the same
64 cases. A legality or utility difference greater than `.05` blocks a pure
carrier statement. It does not erase a transparently reported whole-system
comparison.

## 6. Integration with the five-cut lifetime and terminal batch

At each of five registered cuts, each root's exam has exactly 40 terminal
decisions:

- 8 earliest-cohort retention;
- 8 newest-cohort acquisition;
- 8 unseen old--new recombination;
- 8 expansion probe choices; and
- 8 delayed post-expansion OLD+NEW actions.

For `N=16`, run the one ATN on-policy branch and the one fixed-DLT-history ATN
read at all five cuts. The baseline therefore contributes exactly:

```text
on-policy:         16 roots * 5 cuts * 40 tasks = 3,200 tasks
fixed DLT history: 16 roots * 5 cuts * 40 tasks = 3,200 tasks
total:                                              6,400 tasks
```

Primary summaries are root-first normalized lifetime AUC, terminal utility,
old/new/cross/expansion components, legality, required-row retrieval,
citations, and native-resource cost. On-policy DLT--ATN is a total recursive
system effect. Same-DLT-history DLT--ATN is a carrier/access effect. Both are
required before saying the tested parametric system beat the named strong
text system. `RAW_RAG`, `TEXT_SAME_SEMANTICS`, and the supplied exact graph are
diagnostics and do not replace ATN.

Spend is staged without changing the frozen design: run the on-policy ATN
branch as part of every lifetime root, but keep fixed-DLT-history indexes
materialized and read-only until the DLT mechanism and DLT-versus-frozen
lifetime gates pass. If either fails, do not spend the 54,400 fixed-history
actor calls. If both pass, fill all five fixed-history cuts exactly as
registered; do not select favorable cuts.

The terminal `FINAL_BATCH` control reuses these artifacts:

- every cut already seals the unique public evidence frontier, child rows,
  ATN root, and exact SLEEP target-occurrence manifest;
- `DLT_HISTORY_BATCH` is trained once from the concatenated DLT periodic
  target occurrences under one presealed global permutation;
- `FROZEN_HISTORY_BATCH` does the same for the frozen branch history;
- periodic and DLT-history-batch adapters are both compared against the
  **same already-run fixed-DLT-history ATN terminal endpoint**, because their
  source history is byte-identical; and
- no text row is repeated to imitate batch optimizer work.

Thus ATN adds **zero new training fits** and no duplicate text lifetime for the
terminal timing control. If a claim about frozen-branch data quality is needed,
add one terminal fixed-frozen-history ATN read (16*40 tasks) as a named
conditional diagnostic; it is not part of the core.

`DLT_PERIODIC - FINAL_BATCH` is a timing/recurrence estimand only when response
target bytes, supervised tokens, update count, rank, initialization, and total
optimizer work match exactly. ATN cannot repair a mismatched batch control.

## 7. Exact logical cost and hard resource boundary

ATN performs **zero fits, zero optimizer updates, and zero training GPU-hours**.
Its GPU cost is frozen-child actor inference; its indexing/retrieval is CPU.

With at most 16 nonterminal calls plus one final call per task:

| stage | tasks | max actor calls | max generated tokens | max returned-memory tokens |
|---|---:|---:|---:|---:|
| certificate, 8*64 | 512 | 8,704 | 1,048,576 | 4,194,304 |
| five-cut ATN on-policy | 3,200 | 54,400 | 6,553,600 | 26,214,400 |
| five-cut fixed-DLT-history ATN | 3,200 | 54,400 | 6,553,600 | 26,214,400 |
| **core total** | **6,912** | **117,504** | **14,155,776** | **56,623,104** |

These are logical maxima, not expected usage; early legal final actions reduce
them but never remove cases. The currently measured C0 planning reference is
`13,056 calls <=9.5 A40-hours`, or about `2.62 occupied device-seconds/call`.
Applying that reference gives **about 85.5 A40-hours** for the full core ATN
program. Because later ATN prompts are longer, freeze a conservative hard
reservation of **160 A40-hours** for ATN actor inference. Crossing it yields
`RESOURCE_INVALID`; no task is dropped and no budget is reduced. Actual input,
output, occupied-device seconds, wall time, and retrieval CPU time replace the
planning estimate in the paper.

The certificate alone is capped at **12 A40-hours**. The N=16 five-cut ATN
campaign is capped at the remaining **148 A40-hours**. Batched vLLM execution
may reduce wall time but not logical call/token accounting.

For arbitrary roots `N` and cuts `C`, the baseline's two required lifetime
views cost:

```text
tasks_ATN(N,C) = 2*N*C*40
calls_ATN(N,C) <= 2*N*C*40*17
```

The optional seven-cut extension adds `43,520` q16 actor calls at N=16. A
single terminal doubled-access sensitivity (`q=32`, `B=16,384`, 40 tasks/root)
adds at most `21,120` calls. If the doubled prompt cannot fit or the paired
utility gain is not equivalent within the frozen `.05` band, use
`MAX_TESTED_ACCESS`; do not say saturation.

For every root/cut report actor calls, input/output tokens, returned tokens,
retrieval calls, BM25 documents/comparisons, PageRank vertices/edges/iterations,
MMR candidates, cache hits, CPU/RAM time, prompt latency, persistent raw/audit/
typed/index/cache bytes, adapter bytes, SLEEP target tokens/updates, training
device time, and total wall time. Equal actor opportunities are not equal
compute, latency, storage, or energy.

## 8. Claim and stopping boundaries

The evidence hierarchy is strict:

1. Failed model-free gates: instrument invalid; no actor call.
2. Failed exact/full text ceiling: actor interface or world invalid; no fit.
3. Failed ATN certificate: strong opponent absent; no text-superiority claim.
4. Valid ATN but failed DLT mechanism: baseline result does not rescue DLT.
5. DLT beats ATN on-policy only: total system advantage over this exact
   q16/B8192 configuration, possibly due to better histories.
6. DLT also beats fixed-DLT-history ATN: evidence for a carrier/access
   advantage on identical unique experience.
7. Flat q16 curve alone: no saturation claim.
8. Seven novelty-growing cuts plus doubled-access equivalence: only a
   **practical local plateau of ATN-v2 under the registered PCFL regime**.

ATN success belongs to the complete graph-retrieval system; its PPR path is
not evidence of actor-native traversal. DLT connectedness still requires AUTH
over ATOMS plus LINK cuts/permutations in the finite-reader mechanism cells.
ATN does not establish DREAM compiler value; that requires the same-history
`RAW_CHRONOLOGICAL` LoRA. It does not establish recurrence; that requires the
matched terminal batch. It does not establish parenting, open-world discovery,
universal continual improvement, physical compression, or superiority to all
external-memory systems.

The maximum baseline sentence after the core passes is:

> Over independently randomized finite PCFL lives, the periodic parametric
> system exceeded a frozen q16/B8192 BM25-plus-declared-link PageRank memory
> agent both as an on-policy system and when the text agent was rebuilt from
> the periodic system's identical unique experience, under equal actor-token
> and action opportunities and separately reported memory/training costs.

If only opaque bindings exist, append: **“on independent exact bindings.”**
Broad reuse language additionally requires the predeclared reusable-structure
stratum and its separate positive gate.

## 9. Minimal implementation boundary for Astra

After PCFL v2.2 DEV passes and the builder chooses to implement within its
standing scope, the smallest source surface is:

1. one pure canonical store/index module (`pcfl_active_text_native.py`);
2. one model-free golden suite for lifecycle, BM25, graph, PPR, MMR, packing,
   blindness, renaming, restart, and resource accounting;
3. one eight-condition four-root certificate driver;
4. one policy adapter in the PCFL lifetime runner; and
5. one read-only fixed-history index constructor reused by terminal batch.

Do not import the 866-line historical `active_text_fixed_contract_v1` updater,
add a second LLM curator, or reuse the legacy exact-address service under a new
name. Those are larger systems answering different questions.

## Evidence reconciled

- `organism_v6/pcfl_vertical_dev.py`
- `organism_v6/pcfl_vertical_prepare.py`
- `gpu/astra_pcfl_vertical_dev.py`
- `research_notes/64_iclr_paper_core_and_benchmark_v2.md`
- `research_notes/2026-09-11_strong_evolving_active_text_baseline_candidate.md`
- `research_notes/2026-09-11_strong_evolving_active_text_baseline_adversarial_critique.md`
- `research_notes/2026-09-11_strong_evolving_active_text_baseline_cross_critique.md`
- `research_notes/2026-09-11_strong_evolving_active_text_baseline_closure_review.md`
- `research_notes/2026-09-11_active_text_role_closure_amendment_v1.md`
- `research_notes/2026-09-11_active_text_compression_design_adjudication.md`
- `research_notes/analysis/2026-09-12_text_memory_baseline_readiness_audit.md`
- `research_notes/analysis/2026-09-13_pcfl_strong_external_memory_fairness_audit.md`
- `research_notes/analysis/2026-09-13_pcfl_dev_to_paper_grade_successor.md`
- `research_notes/analysis/2026-09-13_pcfl_full_thesis_construct_validity_audit.md`
- `research_notes/analysis/2026-09-13_full_objective_paper_claim_coverage_audit.md`
