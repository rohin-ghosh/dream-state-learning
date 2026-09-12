# Text-memory baseline readiness for the Dream--LoRA--Think ladder

Date: 2026-09-12 UTC

Role: independent watcher-side design audit. This note changes no builder
source, benchmark, model, adapter, job, node, or scientific claim. It
authorizes no implementation or execution.

## Verdict

Do not build one giant "RAG baseline." The evidence ladder needs two different
text systems because they answer two different questions:

1. **`TEXT_SAME_SEMANTICS`** is a tiny exact-row carrier used in W0, W1, S,
   and M. It asks whether the already-admitted information is usable when it
   is present as text rather than fitted into a LoRA. It must not rank,
   summarize, infer, or traverse for the actor.
2. **`ACTIVE_TEXT_NATIVE`** is the strong lifetime opponent in L. It starts
   empty, keeps its own on-policy public experience, updates a lossless
   raw-plus-typed text store, and performs candidate-blind lexical plus graph
   retrieval. It is a whole external-memory agent, not a carrier control.

The legacy `Ledger.recall`, static parent/child brief, and historical RAG arms
do not fill either role. The nine-life static-brief 2x2 was essentially null
(`F=.2528`, adapter `=.2382`, text `=.2570`, adapter+text `=.2424`), used a
short fixed prefix rather than evolving retrieval, and had large action-count
differences. It is useful history, not a strong memory baseline.

The smallest efficient path is therefore:

- implement one canonical row store, causal-frontier/citation certificate,
  tokenizer-counted memory slot, and store-intervention harness;
- give W0/W1/S automatic exact lookup and M its already-designed four-read
  one-hop machine;
- reuse the same store/certificate for a separately sealed graph-assisted L
  baseline; and
- spend no training GPU on text. Text adds only actor evaluations and CPU
  retrieval. W0/W1/S/M writer work should not wait for `ACTIVE_TEXT_NATIVE`,
  but L superiority and plateau language must.

## The fairness rule: match information, not optimizer repetition

"Same dose" cannot mean the same number of visible copies across a weight
carrier and a text carrier. Repeating a text row sixteen times to imitate two
epochs would hand the text actor an artificial rehearsal prompt. Instead bind:

- one immutable set of **unique source meanings** before the carrier fork;
- the same public chronology and availability frontier;
- the exact LoRA rendering and optimizer exposure separately;
- one insertion of each unique canonical text record;
- a fixed number of charged reads and returned tokens; and
- the same actor generation budget, task form, seeds, parser, and scoring.

Report all of these quantities rather than collapsing them into "equal
compute." LoRA steps, supervised target tokens, input tokens, text insertions,
read calls, returned tokens, index operations, storage, latency, and GPU time
are different resources.

## One common actor surface

Every comparison should reserve a fixed memory partition in the same prompt
location, after public task/state and before child history. Use the pinned
child tokenizer. Generation space is reserved first; memory can never evict
task/state or silently reduce the actor output budget.

For a text read, the partition contains complete canonical **actor renderings**
of rows and citation IDs; full source hashes and envelopes remain in the
machine receipt and are not wasted as actor tokens.
For LoRA/OFF, it contains a presealed target-independent sham block with the
same wrapper and token count. Also run a native-empty sensitivity without the
sham. If sham versus native-empty changes legal syntax or value by more than
`.05`, the carrier comparison is invalid. Every render receipts original,
kept, dropped, padded, and returned token counts. Backend truncation, borrowing
from another partition, and hidden retry are failures.

This controls position and context occupancy. It does not pretend semantic
text and neutral padding are identical inputs; the semantic difference is the
carrier treatment.

## Exact `TEXT_SAME_SEMANTICS` contract

### Shared record and reader law

Canonical stored records are NFKC-normalized UTF-8 JSONL with one final LF, immutable
`record_id`, source identity set, source-envelope hashes, public chronology,
scope, payload, and record hash. A duplicate live key with different bytes,
missing source, future source, wrong root, or post-seal mutation fails the
carrier certificate. The audit ledger is append-only; a live store can
supersede a row but cannot erase its history. The separately hashed compact
actor renderer exposes the full semantic payload plus citation IDs, not hash
boilerplate.

The reader can validate an exact public key, check causal visibility, retrieve
the exact stored row, and render it. It cannot rank, shortlist, semantically
validate, infer a relation, follow a link automatically, expand a graph, run
PPR, or retry. Misses are explicit and charged.

The existing finite-reader design source already defines the M form: up to
four actor-selected adaptive attempts, one exact row of at most 256 tokens per
attempt, 1,024 logical returned tokens total, and one terminal action. W0,
W1, and S need narrower stage-specific request schemas; the existing source
explicitly excludes W endpoints and cannot simply be cited as their contract.

### Stage table

| stage | fixed unique information | LoRA dose | text store/read | actor memory partition |
|---|---|---|---|---|
| **W0** | 16 bindings per root-map, keyed only by public `(tool, mode)`, value `ACT: a0` or `ACT: a1` | 16 keys x 8 train renderings = 128 material rows; 2 epochs/batch 1 = 256 optimizer steps, 16 target exposures/key | insert 16 canonical binding rows once; one automatic target-blind exact lookup/request; one row; each binding is read on the same four held forms | 128 tokens/request; overlength row fails preflight |
| **W1 NEW-only** | 16 identity-disjoint NEW bindings/root-map | same as W0: 128 rows, 256 steps | separate 16-row NEW store, one lookup/request | 128 tokens |
| **W1 cumulative** | exact OLD union NEW: 32 bindings/root-map | 32 x 8 = 256 material rows; 2 epochs = 512 steps, still 16 target exposures/binding | one 32-row store; exact same OLD/NEW row bytes as the single stores; one lookup/request | 128 tokens |
| **S** | 32 authentic child events: 8 situations x 2 actions x 2 occurrences, each with the public outcome and immutable event ID | compiler makes 2 forward + 2 inverse views/event = 128 rows; 2 epochs = 256 steps, 8 supervised views/event | insert each authentic event once; query uses **situation only** and returns exactly its four events in event-ordinal order with citations; requested outcome and candidate action are unavailable to retrieval | one 256-token block; all four complete rows must fit or S is not run |
| **M-E2/E4/E5** | the exact separately admitted canonical atom/link/old/new row deck for that endpoint | endpoint-specific qualified writer dose; report it, do not mimic it in text | use the bound `READ_V1`: actor explicitly chooses public anchor+candidate; up to four charged one-hop exact reads, one row/read, adaptive after each response | maximum 4 x 256 = 1,024 returned tokens; every attempted miss/repeat is charged, but stopping before four is permitted; one terminal action |

W0/W1 text rows are deterministic canonicalizations of the sealed relation
source, not new model-written summaries. S text deliberately returns the four
authentic events rather than an answer row: this preserves the same underlying
outcome information while requiring the actor to use the binding. In M, exact
text may reach the carrier ceiling; LoRA is not required to beat it for an M
mechanism result.

### Stage validity and falsification gates

All model-free construction, visibility, hash, citation, restart/rebuild,
insertion-order, store isolation, tokenizer packing, and resource accounting
tests must be 100% exact before actor calls.

**W0**

- retrieval and citation recall `=1.00`;
- strict generated legal-ACT rate `>=.95` and balanced accuracy `>=.90` per
  root-map, with each registered stratum `>=.80`;
- the complementary map/store swap redirects the preferred action on `>=.90`
  of held requests;
- deleting the necessary row reduces correct-action probability or balanced
  accuracy by at least `.20`;
- wrong-root and irrelevant rows stay within `.05` of empty/sham on value and
  legality; and
- the existing in-context GOLD must pass before interpreting either carrier.

**W1**

- exact recall `=1.00` on all 32 cumulative relations;
- OLD and NEW balanced accuracy each `>=.90`;
- neither bank loses more than `.05` versus its corresponding 16-row single
  store; and
- OLD-cut, NEW-cut, cyclic store swap, wrong-root, sham, and interface gates
  behave directionally. This is a text coexistence ceiling, not retention.

**S**

- every lookup returns the exact four authentic event IDs and nothing else;
- TRUE text reaches forward and inverse balanced accuracy `>=.90`;
- TRUE minus within-situation OUTCOME_SHUFFLED is `>=.20` in both directions;
- swapping outcome bindings redirects the inverse action; deleting one
  action-family's necessary rows drops value by `>=.20`;
- strict legality `>=.95`; wrong-root/new-situation/spill gates pass; and
- GOLD/TEXT failure labels the assay invalid, not the LoRA ineffective.

**M**

Use the M endpoint's existing causal controls rather than inventing one generic
accuracy gate: authentic link versus truthful null and derangement, exact
first-read/citation traces, goal swap, bridge cut and truthful twin, old/new
cuts, outcome-value twin, adapter/text off, cyclic wrong-life donor, and zero
cross-phase spill. A text pass shows the theorem is exposed by the reader. It
does not show the LoRA traversed internally, and PPR must remain absent from
these cells.

For every stage, mutate the hidden answer, candidate order, future rows, and
arm label while holding visible bytes fixed. Retrieval and packing must remain
byte-identical. A paired store swap must return donor IDs only and redirect the
read/action in the donor direction. These controls distinguish using memory
from merely benefiting from another prompt.

## Exact `ACTIVE_TEXT_NATIVE` proposal for lifetime L

### Scientific unit and state

Fork one sealed, parent-deleted child byte-identically into `DLT_NATIVE` and
`ACTIVE_TEXT_NATIVE`. The inherited childhood adapter stays mounted in both;
only the active-text branch freezes it after the fork. Both deployment memory
roots, indexes, caches, and query states start empty. Each branch then follows
its own on-policy public history. Their later evidence sets are not required
to stay identical; this is a total recursive systems comparison, not a
same-source carrier contrast.

### Updater

At each causal frontier:

1. append every eligible public action/outcome event exactly once to a
   lossless raw store;
2. expose same-continuation self events only on the next continuation;
3. expose sibling events only after the whole batched round commits, never in
   Python consume order;
4. at the same registered SLEEP boundaries as DLT, run the same public
   child-authored compile/admission surface on that branch's own history;
5. insert each provenance-valid atom, link, contrast, scope, or new-relation
   record into a typed store; and
6. apply deterministic semantic-key supersession transactionally while
   retaining every prior version in the audit ledger.

The updater may not use parent text after deletion, hidden world truth,
evaluation output, co-occurrence-only edges, another root/arm, or a stronger
teacher. It does no parameter update. Invalid or overlength derived rows remain
audited but unsearchable; there is no repair retry selected by task outcome.

This gives active text the same broad memory-formation opportunity as DLT but
lets its native carrier preserve both raw evidence and explicit typed
structure. It is stronger and cleaner than `Ledger.recall`, yet does not add a
second learned updater before the deadline.

### Frozen retriever, version 1

Use a PCFL-specific deterministic graph-assisted retriever. A dense encoder is
not required for v1: PCFL identifiers are opaque, a new encoder adds a second
model and leakage surface, and graph-assisted typed retrieval is already the
relevant strong capability. The claim remains about this exact baseline.

1. Normalize every opaque handle to its presealed registered public-slot
   ordinal before ranking; restore original public bytes only after selection.
2. Lexical tokens are Unicode-NFKC lowercase matches of
   `[a-z0-9_./:-]+`; no stopword list or stemming.
3. Rank all live raw and typed rows with BM25 using `k1=1.2`, `b=.75`, and
   `idf(t)=ln(1+(N-df(t)+.5)/(df(t)+.5))`.
4. Normalize positive BM25 scores by the maximum positive score for that
   query. The top 16 positive typed rows seed PPR in normalized score
   proportion; if none score positively, typed PPR is zero.
5. The typed graph uses declared directed links only. Add a reverse edge only
   when the public relation schema itself says symmetric. Parallel identical
   edges collapse. Run float64 PPR for exactly 20 iterations:
   `p[n+1]=.20*s+.80*(P^T p[n]+dangling_mass*s)`, starting at `p[0]=s`.
6. Typed relevance is `.5*BM25_norm + .5*PPR`; raw rows use `BM25_norm`.
7. Pack complete rows greedily by MMR
   `.8*relevance-.2*max_selected_Jaccard`, where Jaccard is over the exact
   lexical tokens above. Ties use public-slot ordinal then immutable event or
   record ordinal. Never truncate a row to make it fit.

Each decision episode has four charged retrieval opportunities and one
terminal public action. The first query is constructed automatically from the
public goal/state. After each response the child may emit a maximum 64-token
public query modifier for the next read. Every read ranks the whole eligible
store; it does not receive candidate answers. Each response returns at most
256 child-tokenizer tokens, for 1,024 total. Misses, repeats, and unused reads
are charged. DLT receives the same 1,024-token reserved context partition but
not this graph retriever. Both get the same generous registered
actor-generated-token budget and action opportunities; input/retrieval/training
costs are reported rather than falsely equalized.

The store is uncapped. Only the active-context read budget is capped. A fixed
budget sensitivity uses the same four query opportunities at 512 returned
tokens each (2,048 total), so it changes return bandwidth without adding more
adaptive search steps.

### Native-baseline certificate

Before scientific L roots, require:

- zero future, hidden, parent, probe, wrong-root, or arm-crossing rows;
- source and citation fidelity `=1.00` on a sealed retrieval suite;
- byte-identical restart/cache rebuild and insertion-order invariance;
- retrieval invariance to hidden-answer, candidate, future-goal, and arm
  mutations at fixed visible bytes;
- paired store swap returning donor IDs only and redirecting path/action;
- necessary-row/bridge deletion taking normalized value from at least `.75`
  to at most `.25`, or a preregistered drop of at least `.20` when the endpoint
  cannot use those absolute anchors;
- truthful binding-twin redirection `>=.75`;
- irrelevant-store value and legal syntax within `.05` of empty;
- strict legal terminal action `>=.95`;
- explicit oracle headroom `>=.10`; and
- PPR-off, bridge-cut, deranged-link, expanded-node, path-distance, returned
  row, query, and packing receipts.

Failure blocks claims of superiority to strong external memory and any text
plateau claim. It does not erase a separately valid W/S/M carrier result.

## Plateau and saturation rule

Never use CompilerGym repetition to claim text-memory saturation. Only
mechanically novelty-certified PCFL information cohorts can support the word
"plateau."

Use eight disjoint DEV roots to freeze seven lifetime cuts, the candidate
anchor, confirmation N, and the exact equivalence band. Keep the already
proposed PCFL SESOI: `epsilon=.020` normalized utility per information cohort.
The anchor is the earliest eligible cut with at least two observed increments
before it and at least three fixed cuts after it.

For each root, fit the registered late-window slope over the anchor and later
cuts. In independent confirmation roots, plateau requires all of:

1. the ordinary two-sided 90% Student-t interval over root slopes lies wholly
   in `[-.020,+.020]`;
2. each of the last two root-mean interval gains has a 90% interval wholly in
   `[-.020,+.020]`;
3. scheduled new eligible evidence was actually acquired in every interval;
4. oracle headroom remains at least `.10`;
5. old-cohort retention remains within its frozen noninferiority margin;
6. no certificate/failure exclusion occurred; and
7. the 2,048-token sensitivity also fails to improve on 1,024 tokens by more
   than `+.020`, using the same root-level equivalence rule.

A negative late slope is degradation, not plateau. If the 1,024-token curve is
flat but the 2,048-token arm improves, the result is **budget-limited at 1,024
tokens**, not saturation. If any condition fails, report two finite curves and
omit "saturated" and "beyond saturation."

Even a pass warrants only:

> This exact updater/retriever met the preregistered late-life equivalence rule
> over the tested novelty-certified PCFL horizon while oracle headroom
> remained; doubling its returned-text budget did not resolve the plateau.

DLT can be said to improve beyond that point only if its separate LATE
conjunction passes: positive absolute post-anchor slope, positive
anchor-to-terminal gain, positive root-paired slope advantage over active
text, old/early retention noninferiority, and a terminal practical margin.

## What exists and what must be built

### Exists or is directly reusable

- W0's sealed 16-key source geometry, 128-row/256-step fits, held forms,
  GOLD/oracle, strict ACT parser, and locality/interface measures.
- The W1 design for 16 NEW plus 32 cumulative OLD+NEW relations, equal
  per-bank exposure, and bank-specific coexistence gates. No W1 source exists.
- S's repaired authentic 32-event TRUE/OUTCOME_SHUFFLED design, forward and
  inverse forms, exact gate arithmetic, and proposed text validity condition.
- M's detailed causal controls and the self-contained `READ_V1` finite-reader
  **design**.
- `rml_stage_b/memory.py` patterns for immutable snapshots, exact row hashes,
  and isolated stores.
- The legacy ledger, recall parser, static brief launchers, and historical RAG
  outputs as negative/legacy comparators only.

### Missing and required

- No shared canonical carrier-store/citation/visibility implementation.
- No W0/W1/S exact-reader request schemas or matched memory-slot renderer.
- No same-semantics text execution for W0, W1, or S.
- No W1 implementation at all.
- No S implementation or real roots.
- No M V5 implementation; its current proposal remains REWORK and has a
  reviewed-byte mismatch/baseline-precedence conflict.
- No `ACTIVE_TEXT_NATIVE-PCFL` updater, ranker, graph, query machine, packer,
  certificate, lineage fork, or runtime.
- `Ledger.recall` is token-set overlap (`k=6`) across heterogeneous ledger
  rows. It lacks immutable citations, causal visibility, target blindness,
  fixed token accounting, store swaps, and graph/path receipts.
- `state.render_context` uses a 22,000-character cap and 300-character recall
  slices rather than pinned-tokenizer partitions.
- `batch_loop.py` consumes sibling outputs sequentially; a later same-round
  `RECALL` can observe a prior sibling's newly written row. The active-text
  runtime needs a true round commit barrier.
- The static-brief scripts only prepend one fixed brief; they are not an
  evolving updater/retriever.

## Minimum build and execution order

1. **CPU shared substrate:** canonical row/store, chronology, tokenizer slot,
   exact readers, citations, swap/cut/twin mutations, and golden fixtures.
2. **W0 text companion:** piggyback its already-sealed source and held deck.
   It costs no fit and immediately validates whether the W0 interface exposes
   the theorem.
3. **W1/S text companions:** build with their source generators, before fits.
   GOLD/TEXT failure stops GPU spending on an invalid assay.
4. **M exact text canary:** run E2+E4 text first on four DEV roots, as the
   existing M audit recommends; only then spend LoRA fits.
5. **L active-text implementation:** build and certificate in parallel, but do
   not place its PPR reader inside M or the four-cell parenting-by-SLEEP
   factorial. Preseal it before P-RUN confirmation outcomes are opened; launch
   saved `P-TEXT` descendants only under the already-registered L gate.

This ordering maximizes information per GPU-hour: invalid source/read surfaces
fail on CPU, text baselines require zero training, M reuses one adapter for E2
and E4, and the expensive standalone lifetime opponent runs only when the
core promoted-SLEEP effect warrants the superiority question.

## Claim firewall

- `TEXT_SAME_SEMANTICS` passing licenses an assay/carrier statement, not a
  strong-RAG or autonomous-memory claim.
- W/S/M LoRA does not have to beat exact text to establish its bounded causal
  mechanism.
- `ACTIVE_TEXT_NATIVE` is a whole-system opponent; its graph work is part of
  its computation. DLT-versus-text is not a byte-matched carrier effect.
- No current result establishes strong external-memory superiority, text
  plateau, lifetime improvement, connected knowledge, or compression.
