# Downstream compression and strong-memory gate for the authentic PCFL line

**Date:** 2026-09-13 UTC  
**Role:** independent downstream benchmark design  
**Status:** analysis only. This memo changes no builder source, benchmark,
model, tokenizer, adapter, lineage, job, GPU state, threshold, or scientific
claim.

## Executive ruling

Do not put compression or memory-system superiority upstream of authentic
formation. The current critical path remains:

```text
authentic child EVENT/LINK formation
  -> two-SLEEP M vertical slice
  -> frozen novelty-growing lifetime L
```

The smallest honest downstream addition is:

```text
M zero-fit closure:
    FULL_CHILD_TEXT + ACTIVE_LINKED_TEXT + EXACT_WITNESSED_GRAPH must work

L core, same confirmation lineages:
    on-policy DLT_PERIODIC vs SLEEP_FROZEN vs ACTIVE_LINKED_TEXT
    + same-history CONTEXT / RAW_RAG / LINKED_TEXT / GRAPH at every cut
    + one FINAL_BATCH fit at the terminal cut

optional C sidecar after connected utility:
    one prospective child schema choice per lineage
    + deterministic exact residual coding
    + zero new LoRA fits
```

This design makes three separable claims possible:

1. **lifetime:** periodic authentic SLEEP improves later action;
2. **strong-memory comparison:** the complete DLT system beats one exact,
   independently certified linked-text system, with a same-history analysis
   locating whether the advantage is in the carrier or in the history it
   causes; and
3. **compression, only if it passes:** a child prospectively selected a
   bounded semantic code that is shorter than a packed exact graph at zero
   semantic distortion and noninferior downstream utility.

The current rank-8 adapter is about `80.8 MB`. At M/L scale it is not a
physical compressor. Always report that rate. Do not call the LoRA itself
compressed unless the complete life-specific adapter package crosses the
packed-graph boundary. Until the optional semantic-code sidecar passes, use
`compiled`, `consolidated`, and `connected`, not `compressed`.

The legacy `Ledger.recall` token-overlap helper and static waking brief are
not strong baselines. `rml_stage_b/memory.py` provides useful immutable-row,
hash, exact-read, mask, and restart patterns, but it is a pretarget exact
service, not the evolving lifetime opponent specified here. No current source
implements `ACTIVE_LINKED_TEXT` end to end.

## 1. One scientific unit and one lifetime clock

### 1.1 Independent unit

One independent scientific unit is one prospectively allocated
`(child initialization, learner/training seed, world root)` lineage. Prompt
variants, decode seeds, questions, counterfactual twins, optimizer repeats,
memory reads, and checkpoints are nested measurements, never independent
`n`.

All paper-facing comparisons are paired within that lineage. Failed writes,
malformed actions, missing outputs, failed retrievals, and incomplete
formation remain in the denominator. No root is replaced.

### 1.2 Lifetime unit

The lifetime coordinate is cumulative **unique eligible semantic
assignments**, not episodes, paraphrases, supervised tokens, optimizer steps,
or repeated visits. Let

```text
m[r,t] = number of unique, public, causally available EVENT assignments
         plus unique admitted child LINK assignments at cut t.
```

Every cohort must add the same predeclared number and type mixture of fresh
assignments. An absent, malformed, late, or unsupported opportunity occupies
its presealed slot and remains a failure; it does not disappear from the
clock. Replaying or paraphrasing an old assignment does not advance `m`.

This makes rate, utility, and slope share one denominator and prevents a
writer from manufacturing a longer life by repeating data.

## 2. Exact semantic object, rate, distortion, and utility

### 2.1 Denotation being carried

At lineage `r`, cut `t`, freeze two canonical objects:

```text
D_pub[r,t]
  = every preallocated public opportunity slot through t, in public order,
    including status {PARSED, ABSENT, MALFORMED, LATE, UNSUPPORTED}; for a
    parsed slot, the exact (event_id, source, port, destination, occurrence,
    public evidence hash).

D_conn[r,t]
  = D_pub[r,t] plus every exact admitted child LINK span through t, including
    its endpoints, chronology, evidence IDs, and admission status.
```

`D_conn` is the primary same-denotation object. It records the child's
fallible but provenance-valid organization; it does not silently replace it
with hidden graph truth. The exact witnessed graph is built separately from
public events and is a task-native reference.

The byte-normalized form is a prospectively frozen prefix-free binary
serialization using public symbol-table ordinals, fixed-width status fields,
enumerative IDs, and exact evidence digests. JSON, prose wrappers, repeated
witnesses, chat templates, paraphrases, audit logs, and optimizer exposure are
reported but cannot serve as the compression denominator.

Two independent decoders must reconstruct identical canonical bytes before
any rate result is opened.

### 2.2 Three rates, never one ambiguous “memory size”

Report all three:

1. **Semantic description rate**

   ```text
   bpa_sem(c,r,t) = 8 * B_sem(c,r,t) / m[r,t]
   ```

   where `B_sem` is every root-specific byte needed to decode `D_conn` under
   the frozen common decoder: schema selection, codebook/catalog entries,
   statuses, residual bitmap and values, ordering/index metadata, checksums,
   and provenance bindings. Shared benchmark/base-model/tool code is common
   and excluded; every carrier-specific or root-specific choice is charged.

2. **Persistent deployed state**

   ```text
   B_persist(c,r,t)
   ```

   includes the complete live raw store, typed store, index/graph, embedding
   cache if any, adapter tensors, adapter config, added vocabulary, and all
   state required for a cold restart. The frozen base model is common and
   excluded. Report an ordinary lossless archive of this package as a
   secondary number, never as the primary semantic denominator.

3. **Read bandwidth**

   ```text
   B_read_tokens(c,r,t,q) = child-tokenizer memory tokens returned before
                            decision q.
   ```

   This measures active-context pressure, not physical storage. A LoRA may
   use zero returned memory tokens while occupying many persistent bytes. That
   supports an active-context-bandwidth statement, not physical compression.

For the M/L rate audit, the denotation in the equations below is `D_conn`.
For the optional supplied-schema assay in Section 8, substitute its separately
sealed `D_code` (defined there). Results from the two denotations are never
pooled.

For every semantic package, also apply one pinned ordinary lossless codec
(zstd, exact version/level/hash bound before DEV, no trained dictionary) to
both the candidate and the normalized reference.

### 2.3 Compression ratios

Let `PACKED` be the normalized packed `D_conn` package and `GRAPH` the smallest
complete public witnessed-graph package with native adjacency/index state.
Let `CODEC(x)` apply the frozen ordinary codec. Define:

```text
R_plain = B_sem(CHILD_CODE) /
          min(B_sem(PACKED), B_sem(GRAPH))

R_codec = B_sem(CODEC(CHILD_CODE)) /
          min(B_sem(CODEC(PACKED)), B_sem(CODEC(GRAPH)))

R_phys_lora = B_persist(DLT adapter) /
              min(B_persist(ACTIVE_LINKED_TEXT), B_persist(GRAPH)).
```

Beating expanded prose, raw chat, or repeated paraphrases is ordinary
normalization and earns no compression claim. A semantic-code claim requires
both `R_plain < .80` and `R_codec < .80` at two registered nontrivial loads.
A physical LoRA claim requires `R_phys_lora < .80` at the same loads. The
semantic result cannot rescue the physical one.

### 2.4 Distortion

Compression has two noncompensatory distortion terms:

```text
D_sem = incorrect canonical fields / all canonical fields in D_conn
D_false = usable false rows / all sealed unseen- and wrong-root read probes.
```

For the semantic-code sidecar, require `D_sem = 0` and `D_false = 0` after a
cold restart. Residuals may guarantee exactness, but every residual byte is
charged. A lossy generated LoRA read is reported on a separate empirical
rate--distortion curve and cannot be called lossless.

### 2.5 Utility and normalization

At each lifetime cut, use a fixed balanced held-out deck and compute four
failure-inclusive components:

```text
u_old     = correct legal actions on the earliest acquired cohort
u_new     = correct legal actions on the newly available cohort
u_route   = correct complete action on unseen goal-swapped/recombined routes
u_expand  = .5 * (target-relevant experiment choice
                  + correct delayed OLD+NEW action)

U_raw[r,t,c] = (u_old + u_new + u_route + u_expand) / 4.
```

Each component first averages its fixed task items within root. Invalid,
missing, or illegal actions are zero. No task-count imbalance may change the
quarter weights. Candidate-free EVENT/LINK fidelity, false-memory use,
formation yield, and legality remain separate gates and cannot be averaged
away by `U_raw`.

For cross-root plots only, define an unclipped headroom normalization:

```text
U_norm[r,t,c] = (U_raw[r,t,c] - U_raw[r,t,NONE]) /
                (U_raw[r,t,EXACT_GRAPH] - U_raw[r,t,NONE]).
```

Use it only where the denominator is at least `.10`; otherwise that root/cut
fails the headroom gate. Report `U_raw` beside it. All superiority,
noninferiority, and adverse bounds are tested in raw `[0,1]` utility units,
not on a clipped or selectively normalized score.

Normalized lifetime AUC is the trapezoidal integral against `m`, not an
unweighted average over checkpoints:

```text
AUC[r,c] = sum_j ((m_j-m_{j-1}) * (U_j+U_{j-1}) / 2) /
           (m_last-m_0).
```

## 3. Minimum paper-facing memory systems

### 3.1 `SLEEP_FROZEN / NONE`

Same sealed child, THINK interface, task schedule, random-address tape,
generated-token allowance, and action opportunities. It receives no promoted
deployment memory. In a causal SLEEP comparison it performs the complete
shadow compile/train/check transaction but never mounts the candidate.

This is the no-persistence counterfactual, not the strong memory opponent.

### 3.2 `NATIVE_CONTEXT`

Append the raw public chronology verbatim in causal order. Determine usable
capacity with the pinned tokenizer after reserving the entire system/task/
current-state region and full output allowance. Before the first overflow,
show all complete events. After overflow, retain the newest complete events
only; never summarize, rank, retrieve, or split a record. Report the first
truncation cut and visible-source fraction at every cut.

This is a common-history reference. It does not need its own on-policy branch.

### 3.3 `RAW_RAG`

Store each eligible public action--outcome episode once, losslessly, with
immutable event IDs. Retrieval uses exact typed handle matching plus BM25
(`k1=1.2`, `b=.75`, the bound tokenizer and IDF law). Opaque handles are
normalized to presealed public-slot ordinals before ranking and restored only
in returned bytes. The actor writes every query inside its ordinary thought
budget. Return only complete cited source episodes; no summary, inferred
edge, query-rewriter model, answer-aware reranker, hidden retry, or future row.

Use the same charged read count and return-token budget as linked text. This
is the strong raw episodic baseline. The legacy six-item keyword-overlap
`Ledger.recall` does not satisfy it.

### 3.4 `ACTIVE_LINKED_TEXT` -- primary strong opponent

Start from the same byte-identical parent-deleted child and an empty,
branch-local store. Keep its inherited birth adapter mounted but frozen during
deployment. The store contains:

- every eligible raw public event, immediately visible on the next
  continuation; and
- the exact same kinds of provenance-valid child-authored `EVENT` and `LINK`
  rows admitted for DLT, refreshed at the same SLEEP boundaries on that
  branch's own history.

No hidden graph truth or compiler-inferred edge may enter the typed store.
Superseded rows stay in the audit ledger. The updater and retriever never
change after DEV.

The frozen retriever is the already designed deterministic typed/graph route:

1. normalized-handle BM25 over raw and typed rows;
2. the top 16 positive typed rows seed a declared-link graph walk/PPR;
3. float64 PPR uses restart `.20` for exactly 20 iterations;
4. typed relevance is `.5 * BM25_normalized + .5 * PPR`, raw relevance is
   BM25 normalized;
5. complete rows are packed with MMR `.8`, deterministic public-ordinal
   tie-breaks, and no row truncation; and
6. later queries may depend only on the goal, current public state, earlier
   actor thoughts, and earlier returned rows.

The baseline may traverse its explicit graph. Preventing this would compare
compilers rather than carriers. It receives the child's admitted organization
and is allowed to win.

### 3.5 `EXACT_WITNESSED_GRAPH`

Build a lossless graph only from public executed transitions and their causal
availability. Give it an exact native planner and unrestricted use of its own
public adjacency. It may not add an unwitnessed edge or hidden generator fact.
This is a task-native reference, not the primary deployable comparator, and
is allowed to win. A separate hidden/legal `GOLD_HISTORY` condition establishes
headroom only and is never ranked as a deployable system.

### 3.6 `FINAL_BATCH`

At the terminal cut only, train one fresh LoRA from the exact clean entry
child over the DLT branch's final admitted corpus. Match the periodic writer's
cumulative supervised target-token passes, target modules, rank, optimizer
family, preservation material, and technical-seed law. Reload cleanly before
evaluation.

This is a same-history temporal control: it asks whether periodic writes
matter beyond one equally exposed terminal write. It is not LEAFE unless the
data construction actually implements LEAFE's counterfactual recovery pairs.
It costs one fit per lineage and no separate lifetime branch.

### 3.7 `FULL_CHILD_TEXT`

At M scale, put every exact admitted child EVENT and LINK row with citations
directly in context. It is a zero-fit lossless ceiling and assay-validity
check, not a deployable long-lifetime competitor. It must be included in M
closure even though it need not appear as a separate lifetime branch.

## 4. Zero-fit baseline certificate before any claim-bearing fit

Use four excluded world roots. This certificate may be built in parallel, but
its failure does not block child formation work; it blocks interpretation of
M/L carrier and superiority endpoints.

Model-free gates are exact:

- canonical store/row round trip, hashes, citations, causal visibility,
  source/root identity, and occurrence coverage are `1.00`;
- restart, cache rebuild, and insertion-order permutation return byte-identical
  ranked rows;
- mutating hidden answers, future goals, candidate order, arm labels, or
  evaluator outputs at fixed visible bytes changes no query or returned byte;
- store swaps return only donor IDs and empty stores return the canonical
  miss;
- link, OLD, and NEW cuts delete every alias/index/cache/derived path to the
  target; and
- prompt packing preserves fixed system/task/state/output partitions with no
  backend truncation.

Actor/access gates, failure-inclusive and rootwise:

- `FULL_CHILD_TEXT`, `ACTIVE_LINKED_TEXT`, and `EXACT_WITNESSED_GRAPH` each
  solve at least `15/16` route, reachout, and delayed endpoints on at least
  three of four roots;
- exact source and citation fidelity is `1.00`;
- a binding/store twin redirects at least `12/16` relevant actions;
- deleting the necessary link, OLD row, or NEW row drops its endpoint by at
  least `6/16`;
- irrelevant and wrong-root stores change raw utility and legality by at most
  `.05` versus empty;
- strict legal action rate is at least `.95`; and
- the exact graph exceeds the best fixed/no-memory policy by at least `.10`.

If the exact text or graph cannot solve, the assay is invalid. Repair the
reader/world on excluded roots; never train around it. If active linked text
fails its own certificate, no result may call it a strong baseline or use its
failure as LoRA superiority.

## 5. Smallest resource-response calibration

The persistent text store is never capped. Calibrate only what the actor may
retrieve into active context.

On the same four excluded roots, evaluate at most seven nested configurations:

```text
read-count curve at 4096 total returned tokens: q = {1,2,4,8}
token curve at the selected q:                B = {1024,2048,4096}
```

The duplicate `(q,4096)` point is run once. Every configuration uses the same
frozen updater/index, common-random actor seeds, task deck, and generated-token
allowance. Retrieval misses, repeated reads, and unused opportunities are
charged. A point that cannot fit after reserving task/state/output is
unavailable, not silently truncated.

Choose the smallest `q` whose paired gain on doubling to `2q` has a one-sided
90% upper confidence bound below `.05` raw utility and whose necessary-row
recall gain is below `.02`; if none qualifies, choose `q=8`. At that `q`,
choose the smallest `B` under the analogous rule; if none qualifies, choose
`B=4096`. This conservative rule tends to choose the largest setting when
four DEV roots are noisy, which is appropriate for a strong opponent.

Freeze the chosen configuration before any confirmation result exists. Show
the full finite response curve. This selection is not evidence of lifetime
saturation.

For any later saturation claim, reserve one simultaneous doubled-access
sensitivity `(min(16,2q), min(8192,2B))`. If either true doubling cannot fit,
the exact-configuration comparison remains valid but the word `saturated` is
unavailable.

## 6. Same-history versus on-policy comparisons

### 6.1 On-policy total-system comparison

From one byte-identical sealed entry child per lineage, fork only three native
deployment branches:

```text
DLT_PERIODIC       branch-local action/outcome history; cumulative promoted SLEEP
SLEEP_FROZEN       same opportunities and shadow SLEEP; no promoted write
ACTIVE_LINKED_TEXT frozen child weights; branch-local evolving raw+linked store
```

All begin with empty deployment memory and share presealed world roots,
opportunity schedules, potential-outcome tapes, generated-token/action
budgets, and arm-independent RNG addressing. Each branch owns the consequences
of its actions. Its later public evidence may differ; that is the feedback
loop, not a fairness defect.

Primary total-system estimands are root-paired `AUC` and terminal `U_raw`:

```text
Delta_life = DLT_PERIODIC - SLEEP_FROZEN
Delta_system = DLT_PERIODIC - ACTIVE_LINKED_TEXT.
```

An on-policy advantage alone may be caused by better early actions creating a
better later history. It supports a system result, not carrier superiority.

### 6.2 Same-history carrier table

At every cut, seal the DLT branch's exact public ledger and admitted child
rows. Without changing any lineage, evaluate disposable inference-only clones:

```text
DLT adapter at that cut
NATIVE_CONTEXT over the same DLT chronology
RAW_RAG over the same DLT chronology
ACTIVE_LINKED_TEXT over the same DLT events and admitted links
EXACT_WITNESSED_GRAPH over the same public events
NONE / wrong-root controls
FINAL_BATCH at terminal only.
```

The actor, task deck, common-random seeds, output allowance, action interface,
parser, and causal frontier are identical. Text systems receive the frozen
qualified read budget. DLT uses its native no-returned-text surface. Report
input/context tokens rather than pretending they are equal.

As a context-occupancy sensitivity, place a target-independent tokenizer-
matched sham memory block in DLT/NONE and compare it with native empty. If its
utility or legality effect exceeds `.05`, the carrier attribution is invalid;
the native system comparison remains descriptive.

Claim **system superiority** only from the on-policy table. Claim **carrier
superiority at matched information** only when the same-history paired effect
also favors DLT with its 95% lower confidence bound above zero. If the
on-policy result passes but same-history does not, say the DLT life produced a
better history, not that weights are a better carrier.

## 7. Lifetime, baseline-superiority, and saturation gates

### 7.1 Core four-cohort lifetime

Use the area-chair plan's entry plus four novelty cohorts (`5` cuts). This is
enough for a finite lifetime/AUC comparison but **not enough for an honest
saturation claim**: a plateau rule requiring two increments before an anchor
and three cuts after it cannot fit into five cuts.

The ordered core release is:

1. the integrated M conjunction passes its frozen mechanism gate;
2. DLT has positive absolute post-entry slope and anchor-to-terminal gain;
3. `Delta_life` has point estimate at least `.05` on registered AUC or
   terminal utility and a one-sided 95% root-level lower bound above zero;
4. old/early competence loss has a one-sided 95% upper bound below `.05`;
5. action/interface failure does not rise with lifetime and every scheduled
   novelty cohort was available; and
6. oracle headroom remains at least `.10`.

Only then test strong-memory superiority in the fixed order:

1. `ACTIVE_LINKED_TEXT` certificate passed unchanged;
2. `Delta_system` is at least `.05` on the predeclared primary AUC/terminal
   endpoint with a one-sided 95% paired lower bound above zero;
3. the same-history DLT-minus-linked-text effect has a positive point estimate
   and one-sided 95% lower bound above zero;
4. RAW_RAG, NATIVE_CONTEXT, EXACT_GRAPH, and FINAL_BATCH finite results and
   all resource curves are disclosed; and
5. retention, headroom, sterility, legality, and adverse filling pass.

If exact graph or active linked text wins, report it. M and an absolute
lifetime result can still stand; strong-memory superiority cannot.

### 7.2 Optional saturation extension

Add exactly two further novelty cohorts only after the four-cohort core is
positive, yielding seven cuts. Freeze an anchor from `{cut 2, cut 3}` using
only linked-text DEV roots before confirmation DLT outcomes are opened. Each
eligible anchor has at least two prior increments and at least three later
cuts.

For the exact frozen linked-text configuration, `practical plateau at the
tested resource setting` requires all of:

- new unique eligible evidence enters every late interval;
- the two-sided 90% root-level interval for its late slope lies wholly in
  `[-.05,+.05]` raw utility per cohort;
- each of the last two interval gains has a 90% interval wholly inside the
  same band;
- there is no material negative decline, old retention passes, and oracle
  headroom is at least `.10`;
- the doubled-access configuration's late slope and last two gains satisfy
  the same equivalence rule; and
- doubled access improves terminal utility and late AUC over the native
  configuration by no more than `.05`, again with a 90% equivalence interval.

DLT improves beyond this practical plateau only if its own late slope and
anchor-to-terminal gain are positive, its paired slope advantage has a
one-sided 95% lower bound above zero, retention passes, and terminal advantage
is at least `.05` with a one-sided 95% lower bound above zero.

Without all clauses, say only that DLT beat (or did not beat) the exact frozen
configuration over a finite tested horizon. Never say RAG, text memory, or
external memory generally saturated.

## 8. Smallest honest compression sidecar

### 8.1 Why it is separate

The authentic M grammar stores one EVENT per event and one LINK per declared
connection. By construction, it need not be shorter than a packed graph.
Neither a rank number, short DREAM prose, nor zero returned context tokens is
evidence that the child's experiential denotation was compressed.

Therefore the default no-new-work rate audit over M/L should simply print
`bpa_sem`, `B_persist`, `B_read_tokens`, `R_plain`, `R_codec`, and
`R_phys_lora`. A failed crossover removes the word `compressed` and changes
nothing upstream.

If a positive compression clause is still desired, attach the following
disjoint post-terminal sidecar to disposable clones. It never returns to a
life and adds no LoRA fit.

### 8.2 Prospective supplied-schema assay

Reuse PCFL's exact three-permutation cohort denotation. One cohort's `6`, `4`,
and `3` relation permutations have enumerative rank

```text
y in {0,...,6! * 4! * 3! - 1} = {0,...,103679},
```

so a packed exact assignment needs `17` bits. Preseal
`K_max=16384` unique public descriptors `x_i` and status slots per compression
root. Define `D_code[r,K]` as the ordered descriptor/status roster through
`K`, the exact public `y_i` for every parsed slot, its deterministic thirteen-
relation expansion, and all public evidence identities. The child deliberately
executes the first eight ordinary mapping actions and observes their public
outcomes, then makes exactly one typed schema commitment from a frozen language:

```text
NO_SCHEMA
AFFINE_MOD_103680(a,b): y = (a*x+b) mod 103680,
                       gcd(a,103680)=1.
```

Each root contains eight presealed candidate `(a,b)` pairs in balanced order;
the first eight mappings identify one candidate. There is no retry, repair,
or post-outcome reselection.

Fork two continuations that are byte-identical through the commitment:

- `STRUCTURED`: later mappings follow the chosen affine instance;
- `INDEPENDENT`: the same descriptors, statuses, lengths, marginals, and
  first eight mappings are followed by a presealed independent permutation of
  the remaining `y` multiset.

The child-authored commitment plus a fixed status/exception bitmap and exact
residual `y` values forms `CHILD_CODE`. All descriptor keys, candidate-list
bytes, chosen index, residuals, ordering, index, provenance, and checksum
bytes are charged. The packed graph and ordinary codec retain native exact
lookup and route composition.

Use nested loads

```text
K = {256, 1024, 4096, 16384};
```

the first two are diagnostics, the last two are claim loads. The child gets
one schema call, not one call per load.

### 8.3 Compression release

On each confirmation lineage require:

1. both independent decoders reproduce `D_code` exactly at every load;
2. exhaustive one-relation and fixed 2/4/8-edge route answers agree exactly;
3. schema-only post-commit mapping accuracy is at least `.99` in STRUCTURED;
4. `R_plain < .80` and `R_codec < .80` at both `4096` and `16384`;
5. the incremental child-code bytes from `4096` to `16384` are below `.80`
   of the packed-reference increment, plain and codec;
6. after decoding into the same linked-text interface, the one-sided 95%
   upper bound on `U_raw(PACKED)-U_raw(CHILD_CODE)` is below `.05` and false
   memory remains zero;
7. on INDEPENDENT, schema-only accuracy is at most `.01` and both rate ratios
   are at least `.95` at `16384`; and
8. wrong-root and fixed-point-free schema-index swaps have accuracy at most
   `.01` and no rate below `.80`.

This supports only: **the child prospectively selected an exact semantic code
from a supplied schema language**. It does not show that the LoRA compressed
the life, that the child invented the schema family, or that the whole
organism is smaller.

## 9. Minimum roots, power, and compute

### 9.1 M and L

- Baseline/world closure: `4` excluded roots, zero fits.
- Authentic vertical development: `2` roots, as already specified; no
  baseline or compression endpoint may delay their formation.
- Integrated mechanism/lifetime confirmation: minimum `16` independently
  initialized child/world lineages, no replacement. Require at least `14/16`
  to meet the complete M conjunction before promoting the general mechanism
  language. Keep all 16 in lifetime intention-to-treat analyses.

For continuous lifetime and strong-memory endpoints, choose total
confirmation `N` from `{16,24,32,48}` using only a blinded, mean-free estimate
of the root-paired standard deviation and the fixed `.05` SESOI. Select the
smallest `N` giving at least `.80` power for a one-sided alpha `.05` paired
test under a noncentral-t calculation. If none qualifies, cap at `48`; the
confidence bound, not the spending, decides the claim. Freeze `N` before arm
labels or confirmation means are opened.

Technical fit/decode repeats are averaged inside each lineage. They never
increase `N`.

The core four-cohort roster adds only:

```text
4 periodic DLT fits + 1 terminal FINAL_BATCH fit per lineage.
```

NATIVE_CONTEXT, RAW_RAG, ACTIVE_LINKED_TEXT, and EXACT_GRAPH require no
training fits. Their cost is actor inference and CPU retrieval. The optional
two-cohort saturation extension adds two periodic fits per DLT lineage and no
new baseline fit. Profile one real S1 and one cumulative S2 fit before binding
wall/GPU caps; do not extrapolate from Q0.

### 9.2 Compression

Use `4` excluded compression DEV roots to freeze the serializer, codec,
candidate rendering, and exact decoder; at least `3/4` must pass the entire
structured/independent conjunction before confirmation. Then attach one
preallocated compression root to each of the first `16` confirmation
lineages. Require at least `12/16` complete successes; the exact one-sided
tail under success probability `.5` is
`2517/65536 = .0384063720703125`. Also require root-level one-sided 95% upper
bounds for mean `R_plain` and `R_codec`, with failed roots filled as `1`, below
`.80` at both claim loads.

This costs one bounded schema-generation call per root, deterministic CPU
coding, and zero LoRA fits. Bind a hard inference cap from one timing sentinel;
the prior design ceiling of `1 aggregate A40-hour` for all `20` calls is ample
and must not preempt M/L.

## 10. Claim matrix and stop rules

| evidence | strongest language |
|---|---|
| M exact text/graph closure | the assay exposes the intended theorem; no learned-memory claim |
| authentic M pass | scaffolded child-authored events/connections were written, traversed, expanded, and reused across two sleeps |
| L versus frozen pass | periodic authentic consolidation improved later action across the tested novelty-growing lifetime |
| L versus linked text, on-policy only | the complete DLT system beat this exact frozen active-linked-text system |
| same-history also passes | at matched accumulated evidence, the tested parametric carrier outperformed the tested linked-text carrier |
| four-cohort finite curve | finite-horizon comparison only; never saturation |
| six-cohort plateau conjunction | this exact linked-text configuration reached a practical plateau at its tested resource setting while DLT continued improving |
| child schema sidecar | prospective exact semantic compression within the supplied PCFL schema language |
| physical package crossover | physical parametric compression, only if the complete adapter package actually crosses the packed reference |

Failure dispositions are local:

- baseline certificate failure blocks only baseline-superiority/plateau
  language and triggers a repair on excluded roots;
- active linked text winning blocks superiority but not M or absolute L;
- same-history disagreement narrows a native win to an on-policy system
  advantage;
- insufficient cuts or failed equivalence removes `saturation`;
- rate/fidelity/utility failure removes `compressed`;
- none of these failures retroactively weakens authentic child formation,
  event/link carriage, traversal, expansion, or a separately valid lifetime
  result.

## 11. Information-per-GPU-hour order

1. Continue authentic formation and M source/reader implementation now.
2. In parallel, build only the shared canonical CPU store, exact graph, cuts,
   receipts, and four-root text certificate. Do not launch baseline training.
3. Run two-root M DEV. If it fails, use its seam label; do not spend on L or C.
4. If M DEV passes, freeze the linked-text resource curve on excluded roots
   and integrate the three on-policy branches into the same confirmation
   lineage object.
5. Run four-cohort L with the common-history table piggybacked at existing
   cuts and one terminal FINAL_BATCH fit. This is the core paper result.
6. Add the two saturation cohorts only if the core result is positive and the
   baseline shows a plausible flat late window with headroom.
7. Run the one-call, zero-fit compression sidecar only after connected utility
   passes and only if `compressed` remains in the paper.

This spends optimizer GPU-hours only on the proposed system and its necessary
temporal control. Every external-memory comparator is CPU state plus actor
inference, and every extra claim is conditional on a lower claim already
being established.

## Evidence inspected

- `AGENTS.md`; `CLAUDE.md`
- `research_notes/analysis/2026-09-13_claim_ladder_area_chair_audit.md`
- `research_notes/analysis/2026-09-13_minimum_authentic_child_authored_m_bridge.md`
- `research_notes/analysis/2026-09-13_post_relay_minimum_decisive_benchmark_ladder.md`
- `research_notes/analysis/2026-09-12_baseline_compression_full_paper_watcher_audit.md`
- `research_notes/analysis/2026-09-12_minimum_strong_agent_memory_baseline_route.md`
- `research_notes/analysis/2026-09-12_text_memory_baseline_readiness_audit.md`
- `research_notes/analysis/2026-09-12_smallest_honest_compression_claim_route.md`
- `research_notes/2026-09-11_strong_evolving_active_text_baseline_candidate.md`
- `research_notes/2026-09-11_strong_evolving_active_text_baseline_closure_review.md`
- `research_notes/03_agent_memory_benchmarks.md`
- `research_notes/08_memory_substrates.md`
- `research_notes/11_baselines_benchmarks.md`
- `organism_v6/ledger.py`; `organism_v6/state.py`
- `rml_stage_b/memory.py`
- `alchemy/report.py`
