# Paper-1 v03r end-to-end canary v1

**Status:** proposal for deliberation only. No implementation, provider, GPU,
LoRA, result-analysis, or claim authority is implied.

## Question

Can the frozen Paper-1 organism turn one dispersed public action--outcome life
into locally connected memories, use a non-answer goal to request one useful
return-dream, preserve the resulting corpus through a fresh per-life LoRA, and
use it after a clean context reset to change a paired held-out decision?

This is a mechanism/existence canary on v03r. It is not the lifetime-growth,
baseline-saturation, learned-LOOP, rank-pyramid, or self-training experiment.

## One frozen causal graph

```text
paired public v03r life; final goal embargoed
  -> deterministic witnessed-episode atoms (the disclosed common episodic base)
  -> shared target-blind recurrent PROPOSE calls
  -> later model-authored REINFORCE/SUPERSEDE over newly available local evidence
  -> append-only M0 with supported/provisional/contradicted status
  -> reveal only the public non-answer operational probe
  -> prompted THINK0: query local atoms, then REQUEST_DREAM one typed frontier
  -> fork from identical M0:
       NO_RETURN | OWN_RETURN | matched DISTRACTOR_RETURN
  -> bounded return PROPOSE/REINFORCE/SUPERSEDE calls
  -> append-only M1, then deterministic dedup/multi-view compilation
  -> freeze one exact eligible semantic corpus per branch
  -> fresh final-goal context and prompted adaptive THINK1
  -> exact paired counterfactual-decision score plus offline path-use interventions
  -> only if OWN_RETURN text passes: train the exact OWN_RETURN corpus into a
     fresh per-life MEMORY LoRA and rerun the frozen read/THINK1 contract
```

The deterministic witnessed layer losslessly converts each public action or
observation into one typed atom with its public provenance. It is supplied to
every arm, is never credited as dreaming, and contains no cross-record join,
latent role, shortcut, counterfactual conclusion, or final answer. This is the
mechanical episodic base already allowed by the frozen Paper-1 goalposts.

Hidden truth, the paired answer, proof graph, offline scorer, and any exact
route/effect join are absent from every model call and admission decision.
Self-checking is performed by the same frozen reasoning mechanism during a
later recurrent call: a new claim starts provisional; a later
`REINFORCE`/`SUPERSEDE` operation may support, contradict, or replace it only
from newly visible public evidence or a separately derived prior memory. This
is model reflection over lived evidence, not a mechanical verifier. False
self-approved claims remain in the supported corpus and count against the
system. The deterministic compiler may validate schema/provenance, deduplicate,
render views, and preserve status; it may not infer, repair, accept, reject, or
relabel semantic truth.

## Stage 0: construct and reader headroom

Develop prompts and interfaces on aligned seeds 0--2 only, then freeze them.
Use the first 46-episode held-out collision pair, aligned seed 5, latent bits
0/1, as the canary's sole scored unit. Keep the existing population/shortcut/
local-window/edge-removal tests and add a fail-closed complete public-feature
shortcut gate. Before exposing seed 5 to a model, run a small model-facing gold
control on development only using public-derived local atoms:

- `NO_MEMORY`: fresh THINK1 with no past-life memory;
- `RAW_RAG`: native bounded iterative retrieval over public episodes;
- `GOLD_TEXT`: every public-derived proof-local atom and required local
  connection (including the role equivalence and causal join), but no stored
  final answer or complete proof;
- `GOLD_OPEN_LOOP`: identical gold atoms exposed once with all reads fixed
  before reasoning.

The paired unit passes headroom only if `GOLD_TEXT` solves both twins,
`NO_MEMORY` fails at least one, the output changes correctly under twin atom
substitution, and the adaptive trace uses every registered necessary edge.
`RAW_RAG` and `GOLD_OPEN_LOOP` are reported regardless of sign. A failure stops
before learned dreaming; more dream calls or LoRA cannot repair a bad reader or
task.

### Frozen memory and thinker interface

The witnessed layer and dreamed layer share one typed tuple grammar. Public
environment nouns may be used as type names; no tuple may encode a final-goal
answer or a complete proof. The minimum registered kinds are:

```text
ROUTE(connector, source)                         witnessed
EFFECT(connector, target, CHANGE|STABLE)        witnessed action outcome
SOURCE_VALUE(anchor, source, public_label)      witnessed
ANIMAL_VALUE(animal, source, public_label)      witnessed
TARGET_BASELINE(anchor, target, public_ratio, public_label) witnessed
RECIPE(public_ratio, public_label)              witnessed
ROLE_EQUIV(animal, anchor)                      dreamed connection
CAUSAL_JOIN(source, target, CHANGE|STABLE)      dreamed connection
TRANSFERRED_VALUE(animal, location, value)      optional dreamed shortcut
```

`ROLE_EQUIV`, `CAUSAL_JOIN`, and `TRANSFERRED_VALUE` must cite at least two
local rows; a depth-2 row must cite an earlier dreamed row. The parser checks
only type, local handles, byte bounds, and citation existence. It never checks
whether values are true.

THINK0 and THINK1 expose the same four generic operations:

```text
QUERY(kind, bound fields) -> bounded immutable matching tuples or NOT_FOUND
THINK(claim, cited returned tuple ids) -> scratch only
REQUEST_DREAM(one missing typed tuple pattern) -> terminal in THINK0 only
ANSWER(one public label, cited tuple ids) | DEFER(reason)
```

The reader performs no transitive closure, arithmetic, answer search, or
query planning. THINK1 must explicitly infer role transfer, retrieve the route
and observed effect, retrieve the applicable baseline/source value/recipe, and
perform any ratio subtraction in its scratch trace. This makes a successful
answer the model's composition, not an external factor solver.

## Stage 1: learned text organism

Process each held-out twin independently. The only shared bytes across arms are the
target-blind M0 prefix and its model-call artifacts. Preserve the existing
episode-level cadence; a grouped 12-block schedule is permitted only as a
non-scientific plumbing smoke test and can never substitute for the canary.
The scientific canary envelope is:

- deterministic witnessed atoms cover all 46 public episodes; 46 chronological
  WAKE proposal opportunities receive one current event plus a bounded local
  neighborhood, with no single view containing the final proof;
- 22 precommitted REACTIVATE opportunities sample a balanced frontier of
  unresolved, recently supported, contradicted, and under-linked nodes rather
  than always selecting the newest node;
- 16 target-blind SLEEP proposal opportunities over bounded M0 neighborhoods;
- THINK0 budget at most 12 operations and exactly one valid typed frontier;
- `NO_RETURN` performs zero post-THINK0 dream calls and freezes the literal M0;
  `OWN_RETURN` receives 16 proposal/review opportunities selected by the one
  THINK0 focus; `DISTRACTOR_RETURN` receives 16 calls selected by the frozen
  matched irrelevant focus. OWN and DIST have identical decoding seeds, view
  counts, and budgets; M0 is intentionally the zero-return rather than a
  compute-matched control;
- THINK1 budget at most 12 operations per branch and twin.

Budgets are maxima, not padding targets. Every malformed, repeated, deferred,
unsupported, contradicted, and exhausted call remains in the denominator.
Every created node starts `PROVISIONAL`. A later `REINFORCE` may mark it
`SUPPORTED` only if it cites at least one visible public/memory premise outside
the original creation derivation; repeated wording is not independent support.
`UNRESOLVED` nodes remain in the live provisional frontier and may be
reactivated; `CONTRADICTED` and superseded nodes remain explicit conflict
history. False model-supported nodes remain active and are scored offline. No
status or row is silently deleted.

The final goal is revealed only after each M1 corpus is sealed. THINK1 may issue
typed memory queries, keep a bounded scratch state, perform explicit public
workshop arithmetic, revise/backtrack, answer one public label, or defer. It
may not scan hidden candidates, query the final question verbatim, receive
answer choices not already public, or write durable memory during evaluation.

Stage 1 is a pipeline gate and a separate recurrence attribution. Its text
conditions are `T-M0`, `T-OWN`, `T-DIST`, and `T-TWIN` (the other twin's
corpus, with no extra dreaming). It advances to same-corpus transport when the
earliest corpus in the predeclared order `M0`, then `OWN_RETURN M1` achieves
paired final success, contains every registered necessary connected memory,
and passes path-use/visibility tests.
That earliest passing corpus is frozen for transport; the experiment may not
choose a later or higher-scoring corpus post hoc. If M0 passes, the transport
result concerns target-blind recurrent construction and earns no return-dream
credit.

The stronger goal-conditioned recurrence claim is earned only if OWN_RETURN,
on both twins:

1. produces the exact requested own causal join more often than both controls;
2. contains at least one offline-correct depth-2-or-greater memory citing an
   earlier memory plus public evidence;
3. solves the final paired goal while both controls fail at least one twin;
4. loses the credited outcome when decisive returned atoms are removed, and
   maps to the opposite twin-valid answer when those atoms are twin-swapped;
5. contains no final-goal, answer, proof, scorer, or hidden-truth descendant in
   any pre-seal model-visible or training byte; and
6. is not rescued by offline normalization or parser repair.

If M0 already passes, the result supports target-blind recurrent construction
but not a benefit from THINK0-guided return. If NO_RETURN or DISTRACTOR also
passes, the complete pipeline may advance while the return-dream causal claim
is explicitly withheld. This one-pair result is only an existence/mechanism
gate. It cannot support a population or headline claim.

Before this stage can run, replace v03r's current `precheckpoint_export`
model boundary with a skin-correct public projection. Internal pigment ratios
must be stripped from source/animal outcome rows because their rendered public
episodes expose only opaque labels; workshop and passive-gauge quantities may
remain only where the rendered episode states them. Mutation tests must prove
that latent ratios, answers, scorer fields, and hidden pair metadata are
unreachable from every model-facing byte.

## Stage 2: exact-corpus MEMORY-LoRA transport

Run only after Stage 1 passes and freezes the exact earliest-passing semantic
corpus and realization views. Train exactly one fresh rank-64 MEMORY LoRA per
twin from the same clean Qwen2.5-7B base, using the already measured transport
configuration. There is no rank sweep and no fallback selected from scientific
performance.
Use the measured exposure recipe by fact shape, with fixed training tokens and
all training manifests preserved. Never train on final goals, answers, THINK
traces, hidden truth, or offline scores.

Arms:

- clean base / no memory;
- bounded structured earliest-passing corpus text;
- frozen dreamed-corpus MEMORY LoRA with recognition-style atomic reads;
- wrong-twin dreamed MEMORY LoRA, reusing the other twin's adapter;
- raw public-life RAG from Stage 0.

The no-memory, raw-RAG, direct witnessed-QA LoRA, batch-SFT, native linked
memory, and explicit program/graph learners remain mandatory in replication.
Only no-memory and raw-RAG are used here as development headroom checks; this
canary does not have the scale to adjudicate them.

The adapter is mounted only for atomic memory reads. It is unmounted while the
clean base performs scratch composition and answers. The text and LoRA arms
must use the same query contract, candidate vocabulary derived only from
public/admitted memory, operation budget, and final-goal bytes.

Stage 2 passes the transport gate only if varied-cue path-local atomic read
fidelity is at least 0.90, the own LoRA solves both twins under the identical
THINK1 budget, the wrong-twin adapter loses paired success and changes or
defers at least one member, and final traces cite the transported atoms. Text
success plus LoRA failure is a valid negative that removes the parametric-
transport clause.

## Stage 3: later confirmation, not authorized here

After prompts, budgets, corpus rules, and rank choice freeze on development,
replicate on three seeds by three skins with collision twins scored as one
world unit. Run the frozen prompt ladder and stronger external-memory/batch
training baselines. Then extend lifetime beyond the native prompt budget. No
replication, scale, saturation, or Paper-1 claim is part of this canary scope.

## Attribution outcomes

| Observation | Maximum interpretation |
|---|---|
| Gold adaptive reader fails | v03r/controller is not model-usable; stop. |
| M1 closure does not improve | goal-conditioned return recurrence did not construct the missing relation; an independently successful M0 can still establish target-blind construction. |
| Closure improves but behavior does not | construction improved; actionable reconstruction failed. |
| Text works, LoRA reads fail | explicit constructive memory works; parametric transport fails. |
| LoRA reads work, THINK1 fails | storage works; prompted traversal/composition fails. |
| Wrong/twin memory retains gain | experiential attribution is invalid. |
| Raw RAG matches | no constructive-memory advantage at this scale. |
| All canary gates pass | the frozen organism has one end-to-end paired inference existence proof; environment action, replication, and post-context scaling remain open. |

## Resource estimate and stop policy

The implementation must report an exact envelope before provider use. The
scientific text canary has a hard ceiling of 352 short 32B generations:
168 target-absent prefix calls, 64 OWN/DIST return calls, 24 THINK0 operations,
and 96 final text-arm THINK1 operations. The gold reader canary should be below
50 development calls. A cheap grouped smoke test may run first but supplies no
scientific evidence. Conditional transport adds 48 THINK1 operations, at most
48 online 7B reads, and exactly two fresh rank-64 7B adapter fits; wrong-twin
evaluation reuses those fits. Approximate full cost is 3--6 GPU-hours, to be
replaced by tokenizer- and manifest-exact bounds before authorization.

Stop after the first failed stage. Do not increase model size, dream budget,
rank, prompt specificity, or candidate enumeration to rescue the same frozen
cell. Preserve artifacts and deliberate a repair separately.
