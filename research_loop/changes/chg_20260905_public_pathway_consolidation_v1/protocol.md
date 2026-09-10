# Public Pathway Consolidation v1

Status: architecture proposal only. It authorizes nothing until the complete
fresh-context deliberation and exact human ratification required by `AGENTS.md`.
It does not modify or consume Fable's exploratory `organism_v6` runs. The v9
endpoint writer is preserved as a control inside this stronger successor; a
separate v9-only science run is not proposed.

## 1. Question and causal chain

The first paper-relevant question is:

> Can outcome-gated consolidation of an agent's own public recurrent cognitive
> pathways improve later action beyond direct successful-action cloning and
> strong external memory, and is any gain caused by authentic connections?

The proposed chain is:

```text
public state + goal + bounded recalled experience
  -> one recurrent model chooses public cognitive operations and actions
  -> action/outcome trajectory with predictions, citations, and revisions
  -> dream reconciles the bounded working context without certifying truth
  -> sleep outcome-gates pathways and local semantic records
  -> exact runtime-format rows train one cumulative per-life LoRA
  -> the same recurrent model traverses/reconstructs under a new goal
  -> held-out action and lifetime growth
```

This proposal deliberately separates two instruments:

1. **PPC-CompilerGym:** unchanged off-the-shelf LLVM phase ordering measures
   useful search/decision improvement and delayed action credit.
2. **PPC-PCFL:** the controlled paired causal world measures connected local
   knowledge, multi-hop use, binding, prospective structure, and memory cuts.

CompilerGym alone cannot establish connected semantic knowledge because generic
pass preferences may suffice. PCFL alone cannot establish external usefulness.

## 2. One recurrent THINK loop

There is one base model, one current per-life LoRA, and one operation loop. No
separate thinker, dreamer, planner, critic, verifier, or state-policy parameters
are trained.

At model call `t`, the exact public conscious state is:

```text
permanent goal and environment interface
+ public environment state
+ clock and remaining model-call/read/action budgets
+ active subgoals/branch
+ public hypotheses with status and citations
+ unresolved prediction/outcome residuals
+ bounded records currently opened on the active branch
+ recent public operations and environment outcomes
```

The model emits exactly one typed operation:

```text
OPEN_SUBGOAL | QUERY_LEDGER | FOLLOW | HYPOTHESIZE | PREDICT
| ACT | REVISE | BACKTRACK | DEFER | STOP
```

Each operation either changes the public workspace or invokes one deterministic
reader/environment transition. The next call receives the resulting state.
Broad search and deep pursuit are not hardcoded modes: they emerge through the
model's use of subgoals, queries, follows, and backtracks.

Private computation within one forward pass is neither exposed nor scored.
The learnable thought object is a public workspace transition. Every call logs
the exact visible state, raw completion/token IDs, parsed operation or parse
failure, returned public result, next-state hash, model revision, seed, and
adapter hash.

Context admission is intentionally simple and non-learned in v1. Goal, clock,
budget, active branch, latest outcome, and unresolved surprises are mandatory.
Active-branch records remain visible. Closed branches and old events leave the
window but remain in the append-only ledger and can return only through an
explicit query/follow. The harness enforces the measured token cap; it does not
assign semantic importance or summarize evidence.

The initial model is not treated as an unstructured baby. Pretraining and
agentic post-training provide general intelligence and schooling. A portable
**parenting pack** supplies only a starting prior for learning behavior:
maintain goals, inspect outcomes, notice surprise, preserve evidence, explore
before committing when useful, manage time, and revise beliefs. It contains no
gym identities, action answers, target records, or environment-specific rules.
It is ordinary visible context, not a learned module, and later public evidence
may cause the model to revise or reject it.

Every evaluation item receives the same maximum model calls, reads, environment
actions, input tokens, output tokens, and wall-clock policy in every condition.
One parsed operation is the maximum per call. Unused budget is charged and
reported; no condition gains extra actions by emitting several markers in one
completion.

## 2.1 DREAM reconciles context

THINK, DREAM, and SLEEP are separated by what they operate on:

```text
THINK  operates on world-facing conscious state and may act.
DREAM  operates on the conscious state itself and proposes a smaller coherent
       working set, branches, unresolved questions, and links.
SLEEP  operates on durable learned state by writing admitted rows into LoRA.
```

DREAM uses the same current model and LoRA as THINK. It is invoked either by an
explicit `REQUEST_DREAM` operation or by a deterministic overflow safety
threshold. The latter is a pressure gauge, not a semantic selector. Its exact
input is the current public workspace plus a bounded cited ledger slice. Its
typed output is:

```text
RETAIN(record IDs) | OPEN_QUESTION(citations) | LINK(citations)
| REVISE_WORKING_HYPOTHESIS(citations) | DROP_FROM_WINDOW(record IDs)
```

The result replaces only the model-visible working set. All source records stay
append-only in the ledger. A dream-created link or revision is provisional and
cannot enter positive sleep training merely because the model proposed it.
Later public action/outcome evidence must support it under Section 4.3. This
turns dreaming into model-directed context reconciliation without turning it
into a truth oracle.

## 3. Public pathway record

A trajectory is the already-supported repository sequence:

```text
PUBLIC_STATE -> ASSISTANT_OPERATION -> TOOL/ENV_RESULT -> NEXT_STATE
```

A hypothesis operation is a typed state mutation rather than trusted prose:

```json
{
  "op": "HYPOTHESIZE",
  "subgoal_id": "g3",
  "hypothesis_id": "h7",
  "claim": "condition C makes operation X a setup for operation Y",
  "cited_record_ids": ["m12", "m31"],
  "parent_hypothesis_ids": ["h4"],
  "status": "provisional"
}
```

Co-citation or co-traversal creates an operational link; it never makes a
factual claim supported. Direct observations, semantic claims, operational
links, and shortcuts retain distinct types and provenance.

## 4. SLEEP is write, not a second intelligence

At a frozen checkpoint, sleep consumes public THINK trajectories, DREAM working
state transitions, and their later outcomes. It selects, admits, serializes,
and trains. Sleep may use the same model for bounded restatement into a declared
runtime schema, but no separately learned sleeper exists and model prose cannot
grant support. Sleep has four stages.

### 4.1 Deterministic eligibility

The selector exposes only public source-life material:

* terminal-best and efficient pathways;
* failure -> feedback -> recovery paths;
* large committed prediction/outcome residuals;
* repeated co-traversals across provenance-distinct tasks;
* explicit contradictions and revisions.

Selection determines what may be reconsidered, never what is true.

### 4.2 Candidate organization

The same model may organize each eligible bundle by emitting one
target-independent proposal per call:

```text
PROPOSE_ATOM | PROPOSE_LINK | PROPOSE_SHORTCUT
| PROPOSE_POLICY_CASE | PROPOSE_TEST | PASS
```

The model supplies candidate organization; no hand-written compiler invents
claims or free-form principles. Prior DREAM links are candidates with citations,
not privileged inputs.

### 4.3 Non-generative admission

The gate applies only checks grounded in public source-life evidence:

* a witnessed atom is positive only when an exact public outcome supports it;
* an action is `immediate_improvement` when it improves the measured state;
* for a terminal-best action sequence, replay the exact sequence while deleting
  each action once; an action is `sequence_essential` only when its deletion
  worsens the terminal result;
* a pathway is outcome-associated when it terminates in a measured improvement
  or verified recovery; this does not declare every cognitive operation true;
* a generalized edge remains provisional until a prediction committed before
  a later provenance-distinct outcome is confirmed;
* a shortcut is positive only when every component edge is supported and the
  complete path succeeds in at least two provenance-distinct situations;
* confidence and repeated wording never create support;
* contradicted/provisional material stays append-only but outside positive
  training, and may generate later REVISE/BACKTRACK or test-agenda examples.

CompilerGym deletion replay supplies delayed credit for non-improving setup
passes without a verifier model. PCFL uses its public chronological/twin rules
for semantic support. Neither scorer becomes model-visible.

### 4.4 Runtime-matched serialization and LoRA update

The compiler canonicalizes, deduplicates, attaches provenance, and renders only
exact inference-time formats:

```text
READ:   exact bounded memory query -> one supported local record or NOT_FOUND
DECIDE: exact public conscious state -> next typed cognitive/action operation
```

Loss is applied only to assistant-operation or memory-return tokens. Failed
actions are never positive targets; their public outcomes may appear in the
input to a positive recovery operation. No unconstrained principle prose and
no all-token loss are permitted.

At each sleep, rebuild one cumulative LoRA from the pinned clean base with old
and new rows interleaved. All adapter conditions use the same rank/modules,
optimizer, number of trained output tokens, effective row touches, and update
budget. Sampling/downsampling/repetition rules are frozen before targets open.
The initial recipe candidate is rank 16, q/v projections, alpha 16, bf16,
learning rate `5e-5`, and eight effective touches per admitted row; development
can falsify this recipe but cannot tune it on sealed targets.

The LoRA therefore learns two related things: supported local experiential
associations and a distribution over useful next public operations. It is not
credited with executing an implicit multi-hop proof in one forward pass.
Traversal remains recurrent and visible in tokens.

## 5. Mechanism experiment from one sealed source life

All conditions are derived from the exact same source trajectory/checkpoint;
they never recollect experience. Evaluation begins from the same public state
and raw ledger.

| Condition | Learned/external state | Isolates |
|---|---|---|
| `RAW` | frozen model + bounded raw-event RAG; no adapter | strong same-state no-write floor and `PATH_OFF` |
| `ENDPOINT` | v9 immediate-improvement state->ACT rows | direct successful-action imitation |
| `PATH` | authentic supported READ + public pathway DECIDE rows | proposed consolidation |
| `PATH_SHUFFLE` | same row/token/update marginals, but parent/path links permuted within matched outcome strata | authentic pathway connections |
| `LINKED_TEXT` | authentic accepted pathway DAG through bounded linked-text retrieval; no adapter | strong A-MEM-like external representation and LoRA moat |

One registered secondary adapter, `COGNITIVE_NO_ACT`, removes every `ACT`
target while retaining supported non-action cognitive-operation rows. It runs
only in the mechanism assay and directly tests whether learned cognitive
decisions can improve action without cloning the terminal action.

Every final item also compares the same `PATH` public state with its correct
adapter mounted and absent. PCFL additionally mounts the wrong-life adapter,
performs a binding/twin swap, and cuts cited path edges.

Primary causal contrasts are:

```text
PATH - ENDPOINT       trajectory value beyond action cloning
PATH - PATH_SHUFFLE   authentic connection/order value
PATH - RAW            same-state realized adapter value
PATH - LINKED_TEXT    LoRA value beyond the same organized external memory
```

`COGNITIVE_NO_ACT - RAW` is the strongest direct reasoning-policy diagnostic.

A registered context-reconciliation sub-assay compares, at the same visible
token budget, deterministic recency truncation, DREAM reconciliation, and an
oracle sufficient-state ceiling. It measures later task value, decisive-record
retention, unsupported-claim rate, and compression ratio. This sub-assay may
show that DREAM preserves useful conscious state; it cannot by itself show a
durable LoRA effect.

## 6. PPC-CompilerGym external agency instrument

Use the unchanged installed CompilerGym LLVM environment and instruction-count
reward. Source and targets use disjoint canonical URIs and bitcode hashes; the
paper panel should be suite/family-disjoint when the installed catalog permits.

Before any model/source-life call, exactly two CPU/no-model sealers produce:

1. a broad random held-out panel for general hill-climbing value; and
2. a delayed-credit panel whose programs satisfy a frozen complementarity
   predicate for public pass pair `A,B`: `A` alone is non-improving, `B` alone
   is insufficient, `A->B` improves, and deleting either from the sequence
   worsens the final result.

The complementarity panel is a selected mechanism diagnostic, not an unbiased
estimate of all LLVM programs. The broad panel prevents success on that panel
from becoming the entire external claim.

At each held-out item the recurrent controller receives a fixed call/read/action
budget and executes passes one at a time. Target outcomes never enter a later
target, source life, writer, prompt revision, hyperparameter choice, or corpus.

Report terminal normalized instruction reduction, setup->payoff completion,
path-cut sensitivity where defined, prediction calibration, legal and unique
actions, first-improvement action, invalid rate, calls/tokens/actions/time, and
score-vs-source-lifetime curves.

## 7. PPC-PCFL connected-knowledge instrument

Reuse the controlled PCFL paired causal world and its public action/semantic
interfaces rather than inventing a second ontology. Source lives, held-out
handles, counterfactual twins, chronological support, exact finite inference,
and target quarantine follow notes 46 and 48.

Held-out tasks require multiple one-hop memories whose values are unavailable
from any single source record. The recurrent controller must issue adaptive
queries, cite the resulting dependency path, and execute actions one at a time.

Report atomic read fidelity, adaptive dependency rate, supported edge
precision/recall, constructive proof/path completion and depth, twin-consistent
action, path-cut effect, ordered plan validity, mission value/regret, revision
after contradiction, false-memory use, and text-to-LoRA transport loss.

Only PCFL may support a connected-semantic-knowledge statement, and only when
authentic `PATH` beats `ENDPOINT` and `PATH_SHUFFLE`, survives direct-record
closure audits, and loses its advantage under the registered twin/path cut.

## 8. Staged compute plan

The protocol is deliberately sequential to maximize information per GPU-hour.

### Stage A: CPU closure and tiny model canary

Freeze operation/state contracts, deletion replay, independent target panels,
row masks/budgets, and failure behavior. A tiny non-science canary proves model
format compliance, adapter mount, and train/reload only. Canary results cannot
choose targets or support a claim.

### Stage B: common-source writer mechanism

Run paired independent source-life roots at multiple source-length checkpoints.
The exact number of roots/checkpoints is frozen in the later run manifest after
a development-only variance/cost pilot. Root, not program or target, is the
independent experimental unit. Greedy held-out inference and seeded shared
source sampling remove Fable's stochastic on/off ambiguity.

The mechanism gate requires all of:

* positive `PATH-ENDPOINT` and `PATH-PATH_SHUFFLE` on the registered primary
  metric with uncertainty computed across roots;
* same-state `PATH_ON-PATH_OFF` is nonzero in the same direction;
* the relevant setup/path-completion diagnostic improves;
* the authentic gain is reduced by PCFL twin/path cuts;
* no target feedback, identity overlap, or unequal budget violation.

Failure stops a long on-policy run and redirects work to writer diagnosis.

### Stage C: on-policy developmental study

Only a Stage-B-passing writer becomes the frozen treatment. Compare identical
agents with and without periodic PPC LoRA consolidation, while both retain the
same permitted raw RAG/files/tools. Include the strongest linked external-memory
baseline and the endpoint-writer control. Lives now diverge naturally; common
sealed panels measure later capability at each checkpoint.

The paper-scale axis includes at least three checkpoints strictly past measured
native context capacity (provisionally `2C,4C,8C`) with fixed adapter bytes and
genuinely new knowledge/tasks. Report new-task acquisition, old retention,
cross-era composition, total compute/storage/retrieval work, action-value AUC,
and first/second finite differences with root-clustered uncertainty.

No saturation/crossover claim is allowed unless a registered strong baseline
is actually observed to flatten or degrade while PPC continues improving.

### Stage D: parenting and adolescence transfer

Parenting is a later, separately gated meta-learning condition. Derive a
versioned parenting pack only from training-gym lives and remove task identities,
answers, environment rules, and model-specific token artifacts. Deploy it to a
fresh child life in a held-out gym or suite and compare:

```text
schooling only (base agent)
static parenting pack, no sleep
parenting pack + PPC sleep
matched shuffled or wrong-lineage parenting pack + PPC sleep
```

Primary evidence is change in the child's learning slope/AUC, not an immediate
zero-shot boost. The pack must be portable visible text and explicitly
outgrowable; success across a second base-model family is a transfer diagnostic,
not required for the first paper result.

## 9. Hard falsifiers and claim boundary

Hard falsifiers:

* `PATH <= ENDPOINT`: public trajectory consolidation adds no value beyond
  successful-action imitation.
* `PATH <= PATH_SHUFFLE`: authentic connections/order are not responsible.
* Score rises without setup/path-completion or cut sensitivity: likely shortcut,
  not connected learning.
* `PATH <= LINKED_TEXT`: no LoRA advantage over organized external memory.
* `PATH_ON == PATH_OFF`: no realized adapter contribution.
* Any unequal call/read/action/training-token budget, target feedback, or
  source/target identity overlap invalidates causal attribution.
* Fixed-rank value does not persist through three post-native checkpoints: no
  fixed-substrate compression or continuing-learning claim.
* DREAM reduces context bytes but loses decisive records or raises unsupported
  working claims enough to reduce later value: reconciliation failed.
* Parenting changes only initial score, embeds task-specific answers, or does
  not improve held-out learning slope: no inherited learn-to-learn claim.

A successful Stage B permits only:

> Outcome-gated consolidation of public recurrent pathways improved held-out
> decisions beyond immediate successful-action cloning in the registered
> instruments, with authentic-path causality supported where the controlled
> path/twin interventions passed.

It does not establish an autonomous lifelong flywheel, learned private thought,
general creativity, or baseline saturation. Those require Stage C. A successful
Stage C permits the narrower observed lifetime/crossover statement actually
supported by its registered curves; it never licenses unbounded improvement.

## 10. Required pre-implementation and pre-GPU evidence

Before implementation ratification, two fresh-context interpretations and one
adversarial cross-critique must dispose of at least:

1. whether deletion replay validly identifies sequence-essential setup actions;
2. whether public operation rows test reasoning or merely formatting;
3. whether PATH/SHUFFLE/TEXT budgets are truly matched;
4. whether CompilerGym panels leak identity or selected-target structure;
5. whether PCFL tasks have direct-record or public-signature shortcuts;
6. whether the operation loop lets the treatment obtain more actions/reads;
7. whether any sleep proposal can self-certify support;
8. whether `C` and post-native checkpoints add genuinely new knowledge.

After architecture ratification, scoped implementation must provide:

* strict state/operation/trajectory and lifecycle goldens;
* independent deletion-replay and delayed-credit fixtures;
* exact corpus/mask/token/update-budget goldens for every writer arm;
* exactly two CPU/no-model environment sealers;
* target-feedback, URI/bitcode identity, PCFL closure, twin, shuffle, and path-cut
  audits;
* a quantitative GPU/storage/time manifest;
* a fresh independent reviewer and non-overriding scientific advocate.

No model science or GPU run occurs until those artifacts pass and Rohin
separately ratifies the exact run manifest required by the repository contract.
