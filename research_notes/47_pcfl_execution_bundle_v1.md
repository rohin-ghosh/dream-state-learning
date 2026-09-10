# 47 — PCFL exact execution bundle v1

**Date:** 2026-09-01

**Status:** exact proposal for fresh architecture deliberation. These bytes do
not authorize implementation, GPU work, or a scientific claim. This bundle
repairs the accepted concerns in the PCFL v1 critique while preserving the full
architecture in notes 42, 44, and 46.

**Requested ratifiable scope:** `D0` only—implement the CPU reference world,
exact Bayes/no-memory controllers, canonical schemas, visibility/firewall,
snapshot/provenance machinery, deterministic compiler fixtures, estimators, and
property tests. Explicitly exclude model calls, LoRA training, remote sync, GPU
execution, locked calibration/confirmation, and all scientific claims. Later
stages must bind any remaining model prompts, upstream baseline source tree,
LoRA recipe, sealed splits, and compute budget in new reviewed artifacts.

## 1. Scientific question and unit of claim

The complete project asks whether an agent can turn action--outcome experience
into a compressed per-life world approximation that improves later action and,
eventually, changes which future experience it acquires. This bundle isolates
the representation-and-use link under a common scripted life:

```text
ordinary public action/outcome events
-> target-independent one-edge proposals
-> later public prediction checks
-> deterministic multi-view compilation
-> text or per-life LoRA memory
-> recurrent goal-conditioned reconstruction
-> held-out sequential action
```

The experimental unit is a counterfactual twin pair. Targets, episodes,
queries, dream samples, compiler views, training examples, and adapter seeds
are not replication units.

The strongest result eligible from **PCFL-13 alone** is deliberately bounded:

> Under byte-identical scripted PCFL experience and a frozen recurrent
> controller, provenance-supported compiled causal memory improved held-out
> A2/A3 action at the registered post-working-window retention point versus direct-QA LoRA and
> a native linked external-memory baseline; the identical semantic corpus
> retained action value in a per-life LoRA within the registered margin, and
> binding perturbations reduced the gain.

That sentence is legal only if all co-primary confirmation gates pass. Here,
"post-working-window" refers only to the imposed 8,192-token resolver budget;
it is not a native-context or developmental scaling claim. The result says
nothing about on-policy learning, a continual flywheel, a learned controller,
recurrent sleep superiority, a scaling curve, external validity, or general
intelligence.

## 2. Architecture held fixed

```text
theta_0  frozen pretrained prior
phi      one frozen resolver policy, invoked in THINK and DREAM modes
psi_l    cumulative per-life memory LoRA, rebuilt from theta_0 at sleep cuts

THINK    goal/state -> retrieve one local atom -> update/backtrack path -> act
DREAM    replay/prior memory -> traverse -> propose one falsifiable local atom
SLEEP    deterministic admission, deduplication, views, replay mix, LoRA rebuild
STORE    exact public events, provenance, and statuses outside model context
```

The LoRA is not a literal graph. The explicit audit graph exists outside the
model. A LoRA read is a lossy, recognition-assisted reconstruction of a local
atom. THINK and DREAM share the same retrieval/traversal operation family; only
their inputs and output permissions differ. SLEEP v1 has no model call and
cannot invent truth.

The first registered cell has no replay selector and no materialized shortcut.
Those mechanisms remain architectural hypotheses for later, separately
ratified experiments.

## 3. PCFL finite causal world

### 3.1 Latent family

Each PCFL sector has four binary traits `t0..t3`. `t3` is immutable context;
`t0..t2` are preparable. The current trait panel is public.

Six transform templates are
`SET(t0,0)`, `SET(t0,1)`, `SET(t1,0)`, `SET(t1,1)`, `SET(t2,0)`, and
`SET(t2,1)`. The six persistent public preparation-family labels are assigned
uniformly by a permutation (`6! = 720`).

Four site predicates are:

```text
F0 = t0 AND t3
F1 = t0 OR t3
F2 = t1 XOR t3
F3 = (NOT t0) AND (NOT t3)
```

Four public site-family labels are assigned uniformly (`4! = 24`). Three route
requirements are `t0=1`, `t1=0`, and `t2=1`; three route-family labels are
assigned uniformly (`3! = 6`). The nonexception latent universe per sector is
therefore `103,680` worlds.

Eight semantic specimen classes and the natural-language skin are sampled
independently of these mappings. They may make interaction readable but carry
zero mutual information about the causal assignment. Two dormant A4 exception
families exist but are mechanically excluded from every A0--A3 source claim and
target in this assay.

### 3.2 Counterfactual twins

For hidden world `H`, twin `H_dagger` applies fixed involutions:

```text
preparations: swap t0-setters with corresponding t1-setters; leave t2-setters
sites:        swap F0 with F3; leave F1 and F2
routes:       swap (t0=1) with (t2=1); leave (t1=0)
```

Names, skins, handles, public initial states, source schedule, action counts,
and marginal outcome counts are identical. Target acceptance jointly requires
different correct preparation assignments in the two twins. Before an action
touches a swapped mapping, all model-visible bytes are identical.

### 3.3 Public actions

At most one typed action occurs per step, under a six-action cap:

- `SURVEY(site)` reveals the preassigned public route instance/family.
- `ASSAY(specimen, trait)` returns the already-public trait bit and consumes an
  action; it is an active reacquisition diagnostic, not hidden truth.
- `PREPARE(specimen, preparation)` applies the hidden stable transformation and
  returns the new public trait panel.
- `TRAVERSE(route, specimen)` passes under the hidden route requirement or
  causes an irreversible terminal failure.
- `INTERVENE(specimen, site)` returns accepted/rejected under the hidden site
  predicate; rejection is terminal.
- `COMMIT(mission)` succeeds only after an accepted intervention and terminates.

Illegal, malformed, or multi-action model output is a scientific failure with
value zero. Outcomes expose observations, costs, and public result codes only;
they never expose a rule, proof, answer, or memory label.

### 3.4 Target ladder

- `A0`: one witnessed transition; diagnostic only.
- `A1`: transfer one supported preparation relation to a fresh handle/class;
  diagnostic only.
- `A2`: exactly one kit preparation makes a local intervention succeed; zero
  preparation and every other single preparation fail; minimal path is three
  actions including commit.
- `A3`: exactly one unordered pair of preparations is jointly necessary and
  sufficient for route and site; neither alone nor another pair works; the
  minimal path is survey, two preparations, traverse, intervene, commit.

Each world/checkpoint has exactly eight A2 and eight A3 targets. Target handles,
goals, and state tuples never occur in the source deck. Every target requires
distinct source clusters; A2 combines an old and recent root, and A3 also uses
a third block. Twin targets have differing A2 preparations and disjoint A3
pairs. Rejection sampling uses only these structural predicates and is logged.
It never observes a model/controller score. Exhaustion at 100,000 proposals
invalidates the generator version; it never relaxes a rule.

## 4. Source life and developmental scope

The source policy is scripted, outcome-blind, and target-blind. It uses fresh
reset specimens to run balanced preparation panels, direct test-rig site
interventions, and route trials. Source actions do not depend on any memory arm.
Every arm receives byte-identical event bytes.

`C = 8,192` tokens under the pinned resolver tokenizer, including the exact
canonical event renderer. A prefix contains only complete events whose
`token_end <= cut`; crossing events belong to the later snapshot.

The mechanism calibration uses `0.5C`, `1C`, and `2C`. Early claim families are
proposed at `0.5C` and confirmed by `0.75C`; recent families are not confirmed
until `1.5C..2C`. A proposal at terminal `2C` has no future evidence and cannot
enter positive training data. The interval between confirmations contains
predeclared causal boundary and non-target experiments, never padding.

This finite-sector mechanism assay may establish composition, retention, and
transport. Its entire reusable causal backbone is 13 mappings, only about 16.7
bits before exceptions, and by 2C all 13 can be supported. Repetition past that
point cannot establish developmental scaling. It may only be called
post-**working-window** retention under the imposed 8,192-token resolver budget;
it is not beyond Qwen's pinned native context, and a 16C repetition is not a
capacity curve. A scaling claim requires a factorized multi-sector extension,
at least three strictly post-native checkpoints with increasing unique causal
coverage, and a separately ratified slope/onset estimand. It cannot be inferred
from this bundle.

## 5. Canonical cognitive information contract

Every cognitive object is RFC-8785/JCS UTF-8 with NFC strings and exactly one
trailing LF. Duplicate keys, floats, unknown keys, invalid/null fields, and
noncanonical handles fail closed. Class/family handles have fixed typed
eight-byte formats; episode handles match `[MXSREBP][0-9A-Z]{7}`.

The public goal contains only schema, mission handle, objective, site handle,
and specimen handle. It contains no route, preparation, family rule, terminal
action, predicate, answer, candidate, or suggested subgoal. The public state
contains current handles/classes, public descriptors and traits, surveyed route
state, inventory, preparations, last public outcome, and remaining budgets.

The resolver sees only:

```text
static mode prompt
current public goal/state (THINK only)
eligible public replay events (DREAM only)
bounded semantic workspace
last one-atom memory return
repeat state and budgets
```

It never sees world/twin/seed, hidden mappings, proof/action oracle, scorer,
source/target manifests, held-out goals, claim IDs/status/provenance/support
counts, selector receipts, corpus/backend/candidate metadata, other items or
lives, wall time, retry state, provider caches, or audit forks.

The only permitted target transformation is exact copying of a handle/enum
already visible in goal, state, outcome, prior read, or path. Every query anchor
has an audit-only origin slot. Goal-derived search strings, hidden family
lookups, target-conditioned candidates, and concatenated aliases are illegal.

## 6. Resolver operations

The exact prompts are separate hash-bound files:

- `research_loop/changes/chg_20260901_pcfl_execution_bundle_v1/prompts/think_v1.txt`
- `research_loop/changes/chg_20260901_pcfl_execution_bundle_v1/prompts/dream_v1.txt`
- `research_loop/changes/chg_20260901_pcfl_execution_bundle_v1/prompts/memory_recognizer_v1.txt`

THINK decoding is greedy with at most 256 new tokens. DREAM has exactly four
preallocated samples per replay bundle, temperature `0.7`, top-p `0.9`, at most
384 new tokens, and independently derived frozen seeds. Malformed samples are
not replaced.

Legal primary operations are:

```text
QUERY_LOCAL(anchor)                  # generic, one NodeRef only
UPDATE_PATH(source_slot,orientation) # runtime copies the cited atom
BACKTRACK(to_edge_slot)
EXECUTE_ACTION(one typed world action)
DEFER
STOP
PROPOSE_CLAIM(atom, roots, parents, prediction_template)  # DREAM only
```

`QUERY_TYPED(anchor, relation, direction)` exists only in a separately reported
scaffold ceiling. The primary path is generic anchor-only retrieval. If the
typed condition works and generic retrieval does not, the conclusion is that a
task-specific query scaffold works; it is not credited as generic constructive
memory.

The workspace contains only up to four one-atom memory slots, six public
outcome slots, sixteen typed nodes, eight one-edge path entries, and discarded
edge slots. It has no free notes, rationale, confidence, hidden IDs, agenda, or
chain of thought. Runtime copies cited atoms into path slots; the model cannot
invent a path edge by text.

## 7. DREAM, support, and deterministic SLEEP

DREAM proposes exactly one target-independent `subject--relation--object` atom
at a time. It cites at most four public replay slots and two already-supported
parent-memory slots and commits a relation-specific executable future
prediction. It cannot label a claim true/supported/important, and proposal
multiplicity adds no evidence.

Claim identity is the SHA-256 of its canonical semantic atom. Proposal,
status-event, revision, alias, reverse-view, and training-realization identities
are distinct. Status is append-only by snapshot:

```text
PROPOSED -> PROVISIONAL -> SUPPORTED | CONTRADICTED
SUPPORTED -> REVOKED only in a later snapshot
```

Public evidence is deduplicated at an intervention-cluster root. Views,
paraphrases, repeated touches, proposal samples, and parent claims add zero
support. Every supported claim needs pre-proposal fit and a preregistered
post-proposal prediction from a distinct root/source block, no contradiction,
and relation-specific separating contrasts:

- preparation transform: two distinct fitted reset clusters plus a matched
  negative preparation and later states separating remaining transforms;
- site predicate: pass/fail fit plus a fixed four-state separating panel;
- route requirement: pass/fail fit plus a three-state separating panel;
- exceptions: unavailable in A0--A3.

Provenance points only to earlier supported canonical claims or public root
classes. Alias collapse precedes cycle detection. Shared-root diamonds are
legal and count the root once. Self/equivalent citations, descendant cycles,
terminal/evaluation descendants, realization citations, and confirmation
selected using the claim are illegal.

SLEEP makes no model call. At a sealed cut it sorts supported atom IDs,
deduplicates them, mixes old/new claims by frozen round-robin claim type, and
emits exactly four one-edge canonical views: forward completion, reverse
completion, incident-edge recall, and one-memory statement. Every view contains
one atom and no status, confidence, plan, proof, or provenance. Provisional,
contradicted, and revoked claims produce no positive data. Exposure count is a
frozen training recipe, not epistemic support. Each checkpoint rebuilds the
cumulative per-life adapter from `theta_0`, never the prior optimizer state.

## 8. Immutable snapshots and runtime durability

Every cut seals source prefix, event/status logs, eligible atoms, compiler
input, candidate catalog, prompts/schemas, model revisions, RNG ledger, code
commit, corpus, and adapter hash in a content-addressed manifest. Temporary
directories are fsynced, validated, atomically renamed, and made read-only.
Later status events create a new snapshot and never rewrite an earlier cut.
Suffix perturbation must leave every earlier byte, cache, index, corpus, and
adapter unchanged.

Each model call follows:

```text
CREATED -> INPUTS_SEALED -> CALL_INTENT_SEALED -> DISPATCH_ACKED
        -> RESPONSE_SEALED -> TRANSITION_SEALED -> ITEM_SEALED
```

A crash before dispatch resumes the same call ID. After dispatch, only exact
provider response recovery is legal; otherwise the cell is `INDETERMINATE` and
is never regenerated. A sealed response can be reparsed deterministically.
Malformed THINK output ends the item at failure; malformed DREAM output consumes
the sample. No hidden repair or reprompt exists.

Every call sees repeat fingerprints, counts, reset reason, and remaining
budgets. Repeating after `FOUND` may advance to the next unseen incident atom;
repeating after `NOT_FOUND` is blocked. Blocked output consumes an operation;
a second blocked output ends the item.

Cross-life 128-bit canaries are scanned across event/corpus/index/adapter/prompt,
cache, optimizer, temp paths, processes, and file descriptors. Evaluation
outcome channels are write-denied; pre/post source, status, corpus, and adapter
hashes must match.

## 9. Common reader and causal trace credit

A target-blind candidate catalog is frozen before target generation and
contains all syntactically legal true and false one-edge atoms over public
reusable vocabulary. The reader receives only snapshot handle, canonical query,
and already-returned candidate IDs. It receives no goal/state/scorer data.

The model-visible return is exactly one `FOUND` atom or `NOT_FOUND`. It never
contains candidates, rank, score, provenance, confidence, backend identity,
count, token count, truncation, latency, or alternative. A barrier hides timing.
Backend errors are failures, never `NOT_FOUND`.

Text/graph membership, A-MEM retrieval, and adapted-minus-clean LoRA recognition
may use different hidden computations and must report them. Equal return bytes
equalize the cognitive channel, not compute or capacity. The recognition LoRA
is therefore named **recognition-assisted parametric memory**. A strict-parser
generative-LoRA read is a mandatory unaided-read ablation.

Action correctness and a valid-looking path are not enough for constructive
credit. Before a decisive action, seal the resolver input, compute the minimal
cut of cited memory slots connecting public goal/state to action arguments, and
rerun isolated no-action audit forks with (a) all cut atoms masked and (b)
type-matched counterfactual-twin atoms. Composition credit requires masking to
change the decisive operation and twin substitution to produce the registered
twin-valid action/set. All redundant paths are cut. Uncited/prior-driven correct
actions remain behavioral successes only.

## 10. Arms and attribution

All mandatory arms use the same source life and frozen 32B resolver. Differences
in visible interfaces/resources are explicit rather than described as equal.

Diagnostics:

- `L`: leaked complete-answer ceiling.
- `N`: no lifetime memory, frozen prompted controller.
- `Bayes-N`: exact accepted-deck Bayes-optimal no-lifetime controller.
- `CTX-C`: honest chronological transcript while it fits native context.
- `CTX-H`: hierarchical/context-summary baseline with its extra resources.
- `O-open`: oracle atoms, all queries committed before reads.
- `O-rec`: oracle atoms, generic recurrent reads.
- `O-typed`: oracle atoms, typed-query scaffold ceiling.

Paper-facing memory controls:

- `R-rec`: raw episodic retrieval through the common one-atom channel.
- `X-text`: frozen reflection/lesson memory baseline.
- `A-common`: A-MEM organized memory forced through the common channel; protocol
  attribution only.
- `A-native`: official A-MEM linked-memory implementation and native retrieval
  interface, with native resources reported. Paper-reproduction code is pinned
  to `WujiangXu/A-mem@0c8039f28fdcc08189a23c07a3437d9d2482f9c2`; the production
  implementation is pinned to
  `WujiangXu/A-mem-sys@f303dfc71e07bdc787f4bc135d4cea328ae30e99`.
- `E-text`: supported compiled experiential atoms through the common reader.
- `D-LoRA`: direct-QA/episodic LoRA with the matched training envelope.
- `Raw-LoRA`: raw event-text LoRA diagnostic.
- `E-LoRA`: identical `E-text` semantic atom set in the per-life LoRA.
- `O-LoRA`: oracle-atom transport ceiling.
- `E-gen-LoRA`: unaided generative-read ablation.

Causal/binding controls:

- `S-life`: outcome derangement before proposal/admission; a whole-pipeline
  authentic-history falsifier whose corpus may change.
- `S-bind`: fixed-point-free within-stratum object-binding derangement of the
  already frozen E corpus, preserving claim/type/status/root bins, token lengths,
  six view counts, answer marginals, and training envelope.
- `T-swap`: authentic compiled text or adapter cross-assigned between twins.

`S-life`, `S-bind`, and `T-swap` answer different questions and are never
collapsed into one “shuffle.” A binding claim requires E to exceed `S-bind`
and same-direction effects versus `S-life` and `T-swap`.

## 11. Models and transport

The frozen resolver/writer model is
`Qwen/Qwen2.5-32B-Instruct` at Hugging Face revision
`5ede1c97bbab6ce5cda5812749b4c0bdf79b18dd`.

The memory base is `Qwen/Qwen2.5-7B-Instruct` at revision
`a09a35458c702b33eeacc393d103063234e8bc28`.

Tokenizer and model revisions are identical to those strings. Runtime captures
library/CUDA/kernel/environment hashes. No fallback model is legal in a locked
cell. Resolver temperature/seed settings are as defined above. A-MEM uses the
same frozen 32B generation backend when its native implementation calls an LLM;
its upstream prompt/graph/retrieval behavior otherwise remains native and is
hash-bound after vendoring.

The E semantic corpus is frozen before either text or LoRA evaluation. Text and
LoRA arms contain the same canonical atom set, not the same physical
representation. The compiler's four views are deterministic. The LoRA training
recipe, including rank, target modules, optimizer, schedule, dtype, gradient
tokens, examples, steps, and touches, must be byte-bound after development and
before calibration; `D`, `E`, `S-bind`, and `T` match that full envelope.
No arm is padded with another arm's semantic data merely to equalize examples;
differences are recorded in the resource ledger.

## 12. Exact no-lifetime controller

The Bayes controller has a uniform prior over all generator-legal hidden worlds
conditioned on the target having passed the frozen structural joint-twin
acceptance rule. It sees current public item state/outcomes only and no source
life. It enumerates all legal actions under the six-step horizon and uses
memoized Bellman recursion with lexicographic canonical-action tie breaking.

For a target, worlds are exactly bisimilar when they agree on the visible kit's
preparation assignments, target site predicate, and (A3) surveyed route
requirement. The exact quotient has at most 480 A2 or 4,320 A3 hypotheses.
The quotient must be property-tested against the full 103,680-world family;
otherwise it cannot be called Bayes-optimal.

The CPU environment gate uses 64 preselected twin pairs with no
performance-conditioned replacement. It requires mean `Bayes-N <= .35`, its
90th percentile pair value `<= .45`, exact-memory mean `>= .85`, and exact
memory gain over Bayes-N `>= .30`. Failure invalidates the generator version;
individual difficult/easy worlds are not curated away.

## 13. Score, estimand, splits, and multiplicity

Per item, failure/defer/malformed/illegal/cap has value zero. A3 minimal success
has value one. A2 success has value one at its minimal path and loses at most
0.10 for avoidable actions. Success and censored regret are reported separately.
Within a world average its eight locked targets; average two adapter seeds
inside world; average A2/A3 equally; then average counterfactual twins to obtain
one independent pair score `Y[p,arm]`.

Frozen splits are:

- 8 DEV twin pairs, the only place prompts/thresholds/builders may change;
- 64 CPU-gate twin pairs, generator/oracle/controllers only;
- 6 locked calibration twin pairs, descriptive, with two paired adapter seeds;
- 16 locked confirmation twin pairs, fixed from the outset, with two paired
  adapter seeds;
- 16 ordered reserve streams for generator structural exhaustion or
  pre-science infrastructure loss only.

World, order, target, model-call, statistics, and adapter RNG streams are
independent SHA-256 counter namespaces derived from the frozen protocol hash.
After first scientific dispatch there is no world/seed/cell replacement.
Failures remain zero-valued scientific outcomes. A whole-platform failure
before any science dispatch may resume the identical hash-bound cell. No
complete-case deletion or favorable-seed selection is legal.

At confirmation, define three co-primary pair differences:

```text
d1 = E-LoRA - D-LoRA
d2 = E-LoRA - A-native
d3 = E-LoRA - E-text
```

For `d1` and `d2`, require observed mean `>= .10` and a simultaneous one-sided
lower bound `> 0`. For `d3`, require the simultaneous lower bound `> -.10`
(non-inferiority). Use all `2^16` paired sign flips with a studentized statistic
and Romano--Wolf max-T stepdown over the three co-primary hypotheses at family-
wise alpha `.05`; invert on a fixed `1e-4` grid for the bounds. Paired-cluster
bootstrap with 100,000 frozen resamples is robustness only. Secondary mechanism
contrasts use Holm `.05`; A2/A3-specific superiority forms another Holm family.
Other arms/checkpoints/resources are descriptive, without opportunistic tests.

Confirmation is always 16 pairs. The first 12 may be run operationally but are
masked and cannot stop or expand the study. If calibration predicts inadequate
power even at 16, no positive confirmation claim is attempted; a larger study
requires a new ratification before any confirmation outcome is unsealed.

## 14. Binding and gain gates

For exact memory gain `G_exact = mean(A_exact - A_N)`, the CPU gate requires
`G_exact >= .30`. For a bad assignment `B`, require

```text
mean(A_exact - A_B) >= max(.15, .5 * G_exact).
```

For learned calibration, `G_E = mean(E-LoRA - N)`. If `G_E <= 0`, promotion
fails and the half-gain ratio is undefined. `E-LoRA - S-bind-LoRA` must be at
least `max(.15, .5*G_E)`, and `E-S-life` and `E-T-swap` must have the same sign.

`S-life` logs proposal/admission/status/corpus changes. `S-bind` preserves
relation kind, claim type, status, provenance-count bin, answer-token-length
bin, candidate counts, answer marginals, all compiler views, and training
envelope. If a stratum has fewer than two members, only a predeclared adjacent
length-bin merge is legal; otherwise the generator version is invalid before
model calls. `T-swap` uses the already-built authentic twin corpus/adapter.

## 15. Resource ledger

Every pair/world/checkpoint/arm/adapter seed reports:

- source events, actions, and tokens;
- writer/compiler calls and tokens;
- proposals and admitted/provisional/contradicted/revoked claims;
- records, edges, roots, views, active/retained/index/adapter bytes;
- candidate universe and enumeration count;
- retrieval, reader, resolver operations/tokens/FLOPs/wall time/energy;
- training examples/tokens/steps/rank/modules/dtype/FLOPs/wall time/energy;
- retries, indeterminate states, failures, and action costs.

Only source deck, controller bytes, action/query/operation caps, and the
applicable visible reader schema are equated. The paper reports a resource
vector/Pareto view; it never claims fixed memory or fixed compute across native
graph, text, context, and LoRA substrates.

## 16. Authority and promotion graph

No stage implies the next:

1. `D0`: human ratification may authorize only CPU reference
   generator/oracle/schema/test implementation.
2. `D1`: CPU reference bytes and all property-test evidence are frozen and
   independently reviewed.
3. `D2`: a new human-bound authorization may release exact scientific
   implementation and DEV-only tuning.
4. `G-TEXT`: separate authorization may run text-only DEV then six locked
   calibration pairs.
5. `G-CAL`: only mechanically reachable if text gates pass; separate
   authorization may train the paired LoRA roster.
6. `G-CONF`: confirmation requires a new exact authorization after calibration
   is frozen and reviewed.

Each authority artifact binds predecessor hashes, permitted nodes, exact model,
max wall/compute budget, and forbidden transitions. No dormant future node may
contain executable credentials/imports. No GPU gate permits a scale/model sweep
or on-policy run.

Text-to-LoRA promotion requires leaked ceiling `>=.95`, `O-rec>=.85`, oracle
constructive-proof rate `>=.80`, `O-open<=.35`, direct closure zero, and
`E-text - max(R-rec,X-text,A-common) >= .10`, with no visibility/provenance/reset
failure. LoRA-to-confirmation requires per-seed fidelity `>=.90`, RMS adapter
seed spread `<=.10`, mean and at least four-of-six pair pipeline gain `>=.10`,
transport `E-LoRA >= E-text-.10`, the S-bind half-gain gate, and same-direction
S-life/T-swap effects.

## 17. CPU and review gates

Before any scientific GPU call, the frozen CPU implementation must pass:

- deterministic generation/replay and namespace independence over 64 pairs;
- exact twin public-byte collision and matched marginal tests;
- target uniqueness, minimality, disjoint twin answers, chronology, and no
  source-goal match;
- full-vs-quotient Bayes equivalence, Bellman residual/mass/symmetry/tie tests;
- exact-memory/Bayes/shortcut/necessity gates on the uncurated CPU suite;
- immutable suffix-noninterference at every cut;
- claim-type support, prediction, contradiction, root-equivalence, identity,
  alias/revision/diamond/cycle property tests;
- generic/typed/open/native/generative query factorial fixtures;
- one-edge/direct-closure and causal mask/twin-swap trace tests;
- goal/query/candidate/reader collision and backend-channel tests;
- S-life/S-bind/twin assignment and composition/resource invariants;
- strict parser/repeat-state golden tests and fault injection at every seal;
- cross-life canary, cache/process/file-descriptor, and eval-write isolation;
- split/replacement, estimator/multiplicity, missing-cell, and claim-linter
  golden tests;
- 1,000 simulator steps under five CPU minutes and the full exact CPU oracle
  inside a separately measured pre-GPU budget.

Then freeze code, prompts, schemas, manifests, and environment. A fresh
independent reviewer and a separate author-side scientific advocate inspect the
same hashes. The advocate cannot override rejection; repairs require a new
review and bound approval.

## 18. Claim firewall and failure value

Reports must include `fixed-deck`, `post-working-window retention` where
applicable, and
the resource-ledger qualifier. The following claims/tags are mechanically
forbidden for this assay:

```text
online learning
self-improving or action-experience flywheel
memory-improved evidence acquisition
continual-learning success
scaling, crossover, saturation, or keeps improving with lifetime
recurrent-sleep superiority
autonomous structure discovery
dream necessity
A4 durable revision
external validity
LoRA efficiency or superiority
fixed-memory or fixed-compute
literal graph in weights
learned THINK/DREAM policy
```

Runtime binds `experience_mode=fixed_deck`, `evaluation_writes=false`,
`on_policy=false`, `cadence_claim=false`, and `scaling_claim=false`.

If the oracle/nonadaptive factorial fails, the instrument is invalid. If text
structure fails, the architecture has not earned LoRA training. If text works
and LoRA transport fails, the result becomes an explicit-memory/compiler paper
or negative parametric-transport study. If the native linked baseline matches
or wins, the LoRA moat disappears. If binding controls do not reduce gain, the
result is not attributable to learned causal content. If calibration passes but
confirmation fails, all locked worlds remain reported and the positive claim is
withdrawn.

## 19. What this design deliberately leaves next

This bundle does not finish the full research program. It creates an honest
mechanism microscope. The next separately ratified studies are:

1. `PCFL-Stream`: a factorized multi-sector life with genuinely new causal
   mappings at every scale, old/new/cross-era target cohorts, target-local exact
   Bayes inference, and at least three post-native-context points;
2. A4 evaluation-time backtracking and later analogous improvement;
3. on-policy source actions where memory changes evidence acquisition and later
   reconsolidation;
4. learning `phi` from successful long trajectories;
5. external validation in a standard interactive environment.

The engineering is successful only if it makes these scientific distinctions
measurable. Passing software tests without those distinctions is not progress.
