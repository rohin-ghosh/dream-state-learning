# When Should Experience Become Weights? — proposal v1

**Change ID:** `chg_20260901_feltcraft_lifetimes_v1`  
**Status:** proposal only; unratified; no implementation or GPU authority.  
**Purpose:** replace a small finite memory puzzle as the paper's center with a
causal lifetime benchmark and an exactly attributable Dream--LoRA--Think
reference architecture.

## 1. Paper question and contribution boundary

The paper asks:

> When can a fixed pretrained agent convert its own public action--outcome
> history into connected, lossy experiential knowledge that improves unseen
> later actions as its life grows beyond native context, and when should that
> history remain explicit text or graph memory instead of becoming weights?

The contribution is a **causal lifetime phase diagram plus a reference
system**, not priority on dreaming, agent memory, LoRA memory, reflection, or
continual-learning loops. TMEM, PEAM, OEL, Auto-Dreamer, A-MEM, and related
systems occupy those broad claims.

The distinctive experimental object is the interaction among:

1. lifetime length and genuinely new causal information;
2. environmental compressibility;
3. memory representation and access;
4. held-out constructive action, not memory QA;
5. causal assignment/intervention on the actual decision path.

The preregistered qualitative prediction is deliberately asymmetric:

- an authentic explicit graph should win or tie arbitrary exact lookup in an
  independent-random world;
- connected consolidation is useful only if reusable structure exists;
- LoRA earns credit only for transporting/amortizing that structure without
  destroying later action, not for discovering or reasoning by itself.

If the graph wins everywhere, the benchmark and negative phase diagram remain
the scientifically honest result. If compiled text wins but LoRA loses, the
paper becomes experiential compilation rather than parametric memory.

## 2. Claim ladder

Claims are earned independently.

| ID | Required evidence | Permitted conclusion |
|---|---|---|
| C0 | PCFL-13 CPU/model gates, causal twins, reader and binding audits | the component assay is valid |
| C1 | common-deck FeltCraft-Lifetimes fixed-experience result | the representation/use pipeline improves later action under identical experience |
| C2 | at least three strictly post-native checkpoints with growing unique structure | continued acquisition/retention/composition over the tested lifetime range |
| C3a | a schema committed before a sparse future cohort improves action beyond all local atoms | useful prospective schema generalization |
| C3b | C3a plus a frozen code/active-memory budget shorter than enumerated atoms at matched action loss | tested compression over the measured range |
| C4 | authentic memory changes information-seeking actions, later evidence, later memory, and a sealed later action | the action--experience--memory--action flywheel |
| C5 | a cross-life LOOP adapter improves unseen-life operation policies | the controller itself was learned |

No lower rung inherits a higher claim. Paper 1 targets C1--C3. C4 is a
confirmation extension. C5 is later work.

## 3. Reference architecture

### 3.1 State objects

- `theta_0`: frozen action/reasoning model.
- `theta_m`: frozen auxiliary memory-reader model.
- `psi[life,cut]`: reset-per-life MEMORY LoRA, cumulatively rebuilt from the
  clean reader base at a sealed sleep cut.
- `phi`: one fixed recurrent operation policy, invoked in THINK and DREAM
  modes. In Paper 1 it is prompted/amortized, not learned within the life.
- `E`: immutable public action--observation--outcome log.
- `G`: append-only semantic/provenance audit shadow. It is not exposed as a
  global graph to the model.
- `Z`: bounded token-space working state and cited path.

### 3.2 Wake / THINK

THINK is narrow and goal-conditioned. Each call emits one typed operation:

```text
QUERY_LOCAL | UPDATE_PATH | BACKTRACK | EXECUTE | DEFER | STOP
```

The reader receives one public anchor copied from the current state, goal, a
previous read, or a public outcome. It returns at most one local semantic atom
or `NOT_FOUND`. Its candidate constructor is frozen before authentic memory is
revealed, depends only on public type/anchor information, and is identical
across substrates. THINK explicitly assembles a short path in `Z`, executes at
most one world action, observes the ordinary outcome, and may backtrack.

Wake traces record visible query origins, returned slots, path edges used by
the decisive action, public outcomes, unresolved dependencies, repeats, and
stop reason. These traces supply audit and replay priority. Co-traversal does
not make a proposition true and does not directly write semantic truth.

### 3.3 DREAM

DREAM uses the same resolver operation family with broader episode-conditioned
replay and durable-proposal permission. One operation may propose one
target-independent local relation, exception, procedure, schema prediction, or
two-edge shortcut; revise one proposal; open one question; or pass.

DREAM never receives held-out goals, hidden truth, proof graphs, scorer output,
complete plans, or final answers. It cannot self-promote a proposal to true.
Model self-check can reject or leave a proposal provisional, but cannot confer
support.

### 3.4 Chronological grounding

A proposal commits a local claim, scope, observable prediction, and roots
available at time `t`. A later ordinary public outcome, hidden at commitment,
is mechanically compared with the prediction. The comparator can append
`SUPPORTED` or `CONTRADICTED`; it cannot propose, repair, rank, normalize, or
enumerate claims. Evaluation outcomes are permanently write-denied.

### 3.5 SLEEP compiler

SLEEP is the enclosing offline phase:

```text
select replay -> DREAM -> chronological status update
-> deterministic compile -> LoRA rebuild
```

The deterministic compiler admits supported nonrevoked atoms, canonicalizes,
deduplicates, interleaves old and new content, preserves provenance outside
training text, and emits a frozen number of one-edge access views. It cannot
create semantic content: every predicate in an emitted realization must be a
syntactic view of exactly one admitted predicate. Repetitions/views are write
strength, not evidence. All field-level provenance and taint are auditable.

Eligible materialized shortcuts require supported constituent edges, at least
two provenance-distinct successful wake traversals, a later ordinary outcome,
target independence, and retained `via` provenance. Atom-only precedes
shortcut experiments.

### 3.6 MEMORY LoRA and read

The LoRA stores lossy local associations, not a literal graph. The operation is
goal-conditioned path reconstruction, not invertible decompression.

At each cut, the adapter is rebuilt cumulatively from the clean reader base.
Rank, target modules, precision, serialization, optimizer disposition, local
candidate-set size, and read budget are selected once on DEV and frozen across
all lifetime cuts and endpoint regimes. Train exactly one adapter per
`(method, life, cut, adapter_seed)` and mount serialized read-only clones per
target. A descriptive rank sweep cannot choose a different winner per cut.
The primary scientific arm must include both:

- **headline scalable condition:** generative one-atom reads; and
- **assisted diagnostic:** recognition reads over a frozen, public,
  constant-size local candidate set constructed before authentic memory is
  revealed.

Candidate work, hidden scans, output vocabulary, tokens, latency, and bytes are
reported. A reader whose work is linear in lifetime memory cannot support a
scalable parametric-read claim. The adapter is unmounted while the clean action
model composes and acts.

### 3.7 Later LOOP adapter

A distinct cross-life LOOP adapter may learn `phi` from complete typed
state--operation--environment trajectories. Train only operation tokens;
mask world observations, environment outputs, hidden truth, proof graphs, and
offline scores. This object is frozen inside every evaluation life and is not
part of the Paper-1 claim.

## 4. Primary benchmark: FeltCraft-Lifetimes

Create a new package. The frozen `archive/session1` code is lineage, not
scientific authority. The exact CPU world is defined in `world_contract.md`;
where this overview is less specific, that contract controls.

### 4.1 Action world

A life is an append-only sequence of eras. CPU v0 uses the registered four-edge
template and state/transition kernel in `world_contract.md`; later template
families require new review. Old objects, locations, and learned rules remain
valid. Every checkpoint adds genuinely new publicly identifiable recipe or
location information; replay and paraphrase do not count as growth.

The public action interface is exactly:

```text
MOVE(site)
GATHER(resource)
TRY_CRAFT(output, ingredient_a, ingredient_b)
STOP
```

Failed crafting emits only a frozen public failure class such as
`INCOMPATIBLE`, never the hidden ingredients. Object handles are randomized
independently of graph depth, role, recipe, outcome, goal, and split. Public
state contains only actually observed information.

The fixed source deck is generated by a pure public policy whose next action is
a function only of canonical public history, a predeclared schedule, and
private counter RNG. Coupled hidden worlds with identical public histories
must induce identical next-action distributions. The on-policy condition later
permits the agent to choose experiments. Hidden engine structure is used only
inside transitions, symmetric quadruplet generation/rejection, exact reference
controllers, and sealed offline scoring.

### 4.2 Paired compressibility regimes

The replication block is the matched SCM quadruplet
`super_seed x {RANDOM,MOTIF} x {twin0,twin1}`. Renderer, handles,
descriptors, source schedule, target templates, budgets, and nuisance draws are
shared. Only the registered descriptor--role persistence and twin involution
differ. Acceptance is joint and symmetric for the entire quadruplet. Node
counts, degree/depth distributions, action opportunities, descriptor counts,
exposure schedules, UTF-8 lengths, goal lengths, and shortest-path difficulty
are therefore coupled rather than merely matched in expectation.

**RANDOM.** Each era independently permutes descriptor classes onto the same
registered motif roles. Public descriptors contain no cross-era predictive
information about an unobserved edge. This is the exact-retention negative
control.

**MOTIF.** One descriptor-to-role permutation persists for the whole life.
Fresh opaque handles instantiate the same registered role template every era.
The permutation is randomized per life, so pretraining cannot know the answer.
Complete early instances support a target-independent schema; later sparse
instances omit one decisive local edge that the schema prospectively predicts.
CPU v0 contains no exceptions; exceptions and A4 require a later change.

The endpoint confirmation uses `rho in {0,1}`. A later descriptive phase
sweeps `rho in {0,.5,1}`.

Twin side 1 composes the hidden role binding with a frozen involutive role
derangement. Applying the involution twice restores side 0. Twins have
byte-identical target goal, public pre-action state, handles, descriptors,
budgets, and target marginals. Their earlier public lifetimes establish
different bindings, so registered decisive action sets differ. A quadruplet
failing byte collision, involution, action-set, nuisance, or headroom gates is
rejected before any model call and its full rejection receipt is retained.

### 4.3 Lifetime checkpoints

Let `L_native` be the pinned action model's exact usable native input after the
frozen prompt, state, workspace, operation history, and output reserve.
Checkpoints occur at complete-event cuts near:

```text
0.5L_native, 1L_native, 2L_native, 4L_native, 8L_native
```

The final three are strictly post-native. Unique public-prefix-identified
relations and their frozen enumerative code length must grow by at least `1.8x`
from one reported post-native checkpoint to the next. Report schema-conditioned
MDL separately; it is expected to grow more slowly in MOTIF. If fewer than
three post-native points are feasible, scaling/saturation/crossover language
is prohibited.

### 4.4 Target strata

- `A0`: witnessed atom recall; diagnostic only.
- `A1`: one-edge near transfer.
- `A2`: constructive join of relations dispersed across episodes.
- `A3`: four-to-six-action cross-era plan using at least one early and one
  recent dependency.
- `S`: matched sparse-cohort action whose decisive edge was never observed. It
  is implied by a legal prospective schema in MOTIF and deliberately
  nonidentifiable beyond the Bayes floor in RANDOM.
- `A4`: later extension only; a scoped exception/change requiring a
  discriminating action, backtracking, revision, and recovery.

At each checkpoint, score new acquisition, earliest-quartile old retention,
and cross-era targets separately. No source episode may match a target state,
goal, complete plan, or decisive action sequence.

An exact target-local no-lifetime/brute-force controller must score at most
`.35`; an authentic exact-memory controller must score at least `.85`. These
and every nuisance/difficulty condition are applied to predeclared target
cohorts jointly across the matched quadruplet, never to retain favorable
individual targets.

## 5. Experiments

### 5.1 Common-deck attribution

Every method receives the same ordered public event bytes. At each cut:

1. consolidate using only the legal prefix;
2. clear context, caches, workspace, and process state;
3. freeze the life memory;
4. clone a disposable evaluation process from the frozen cut;
5. run one target in the clone and destroy it;
6. verify later source/compiler/memory hashes equal a run where evaluation was
   skipped.

No evaluation byte—including goals, queries, reads, paths, actions, outcomes,
RNG, caches, or replay priority—may reach later life state. This identifies
representation/use, not online exploration.

### 5.2 On-policy flywheel

Only after common-deck success, clone paired source states and randomly assign
memory conditions. Agents choose information-seeking and crafting actions
under equal action budgets. Ordinary outcomes may feed later sleep; evaluation
outcomes may not.

Independently randomize memory during collection blocks and cross experience
collector and compiler:

```text
Y[collector, compiler]
```

This estimates intention-to-treat collection, representation/use, and
interaction effects. A mediated flywheel analysis needs a separately frozen
interventional mediation design; sequential correlations alone are
insufficient. A flywheel claim additionally requires:

```text
authentic assigned memory
-> better next-block information gain per action
-> better subsequent compiled memory
-> better sealed later action
```

## 6. Comparison set

All systems use the same action model and public action budget. Return-channel
and resolver budgets are matched where interfaces permit; total lifecycle
resources are reported rather than falsely declared equal.

Minimum confirmation arms:

1. no persistent memory;
2. recent context and strongest honest native-long-context control;
3. hybrid BM25+dense iterative episodic RAG;
4. native A-MEM-style linked memory;
5. authentic observed-edge DAG with bounded graph traversal;
6. explicit MDL/Bayesian motif learner plus graph;
7. reflection/procedural text memory;
8. Auto-Dreamer-like consolidated external text;
9. raw-trajectory LoRA;
10. direct trajectory-to-QA LoRA (TMEM-like write baseline);
11. identical DREAM-compiled corpus in text;
12. identical DREAM-compiled corpus in LoRA, with generative and recognition
    reads;
13. atom-only, atom+shortcut, and atom+schema ablations;
14. end-of-life batch SFT on the same history as an upward resource reference.

PCFL-13 remains the causal/component microscope for reader noninterference,
support chronology, binding shuffles, counterfactual twins, and actual
decision-path cuts. It cannot support lifetime or compression claims.

## 7. Causal and leakage controls

Mandatory before confirmation:

- complete target pre-action visible-byte collision across twins;
- target-only, state-only, identifier, descriptor-only, action-frequency, and
  passive-signature probes no higher than `.35`;
- sealed whole-life/split generation and fresh handles;
- no recipe-bearing failure or manual;
- no depth/role/goal encoded names;
- one adapter per `(method,life,cut,adapter_seed)`, cloned read-only into a
  fresh process/cache/workspace for every target;
- evaluation write denial;
- globally coherent action--outcome binding shuffle;
- randomized whole-memory null, cross-life, and twin assignment before any
  target read;
- schema-descriptor shuffle preserving local atoms;
- post-target schema as a labeled leaked ceiling;
- same-corpus text-versus-LoRA comparison;
- generic, native, and oracle reader factorial;
- machine-derived transitive cited-root masking and coherent twin substitution
  under coupled randomness as secondary mechanistic certification.

Primary causal attribution comes from whole-memory randomized assignment and
coherent full-memory twin swaps. Constructive-path certification additionally
requires that masking the transitive cited-memory closure changes the decisive
operation and cited twin substitution changes it to a registered twin-valid
action/set; negative-control masks must not. Correct behavior surviving these
is behavioral success, not certified memory-mediated composition.

## 8. Estimands and statistics

Let `Ybar[m,q,r,l,s]` be mean binary success within the action budget for
method `m`, matched super-seed `q`, regime `r`, lifetime cut `l`, and stratum
`s`. Each stratum has a frozen equal number of accepted targets; average both
twin sides, target repetitions, `K=2` adapter seeds, and execution seeds inside
`q`. Crashes, timeouts, malformed outputs, and missing cells are zero. The
matched super-seed is the replication unit.

The phase diagram is estimand zero and does not require Dream--LoRA--Think to
win. Method efficacy in MOTIF is:

```text
Delta_min = min over b in B of {
  mean_q Ybar[full,q,MOTIF,8L,mean_equal(A2,A3,S)]
  - mean_q Ybar[b,q,MOTIF,8L,mean_equal(A2,A3,S)]
}
```

`B` is a named primary baseline set frozen before confirmation; oracle ceilings
and upward batch-SFT references are excluded and reported separately. A
headline superiority claim requires simultaneous one-sided lower bounds above
zero for every `b` and observed differences of at least `.10`. Hyperparameter
search budgets and the final configuration of every method are frozen on DEV.

The schema estimand is the paired difference-in-differences on `S`:

```text
I_schema = (full_schema - identical_atoms_only)[MOTIF]
           - (full_schema - identical_atoms_only)[RANDOM]
```

Compiler, reader, action, and substrate budgets are identical within this
contrast. A lower bound above zero plus at least `.10` MOTIF action gain earns
prospective schema generalization. Compression additionally requires the
frozen MDL/active-memory criterion. Same-corpus LoRA--text is a separate
transport estimand.

For a comparator to be called saturated, simultaneous upper bounds for both
`Y(4L)-Y(2L)` and `Y(8L)-Y(4L)` must be at most `.02`, while oracle headroom is
at least `.10` and unique public information grows in both intervals. The full
system continues improving only if both corresponding lower bounds exceed
`.02`, or a separately frozen monotone repeated-measures slope test passes.
Stable old panels and difficulty-matched parallel new panels prevent target
population drift. Failure to reject growth is never called saturation.

Additional locked contrasts:

- old-retention noninferiority margin `-.05`;
- schema value `full - atoms_only >= .10` on `S`;
- LoRA transport `compiled_LoRA - identical_compiled_text`, margin `-.10`;
- shortcut query/operation reduction at matched action accuracy;
- prospective schema precision/recall and frozen MDL bits for schema,
  bindings, provenance, and numeric precision versus enumerated atoms;
- root/binding intervention removes at least half the gain or `.15` absolute.

Start with a preregistered minimum of 24 matched super-seeds and maximum of 48.
Before confirmation, use disposable pilots only to estimate blinded variance
components; freeze sample size by simulation of the complete outer-unit
analysis, with a variance-only resizing rule that never sees method outcomes.
Adapter/execution seeds are nested, use common random numbers where legal, and
are never replicates. Use an outer-cluster studentized multiplier/bootstrap
procedure with the same resample across each named family and Romano--Wolf
simultaneous correction. Calibration and engineering pairs are disposable and
never recycled.

Multiplicity is hierarchical: C1 efficacy; C2 two-interval growth and old
retention; C3 schema difference-in-differences; transport (generative and
recognition separately); then causal interventions. A later family is not
promoted when its prerequisite fails. Every superiority/noninferiority claim
uses matching simultaneous one-sided bounds.

## 9. Resource accounting

For every item and lifetime report:

- source and evaluation actions;
- raw/unique/supporting event tokens;
- unique public-prefix atoms, enumerative bits, schema-conditioned MDL, and
  exact target conditional entropy;
- dreamer/compiler/model calls and tokens;
- training examples/tokens/FLOPs;
- adapter rank, target modules, precision, serialized bytes, and optimizer
  disposition;
- retained and active external-memory bytes;
- query count, hidden candidate work, scans, retrieval/model tokens, latency;
- wall time, GPU/CPU hours, peak memory, failures, retries, and energy where
  measurable.

Plot quality--resource Pareto fronts and compute break-even. Do not call
interfaces fixed-memory or fixed-compute merely because visible bytes match.

## 10. Promotion ladder

1. **CPU negative-only instrument falsification.** Build a minimal new
   FeltCraft-Lifetimes
   generator over 100--1000 seeds. Test entropy growth, twins, shortest paths,
   motif utility, oracle/no-memory headroom, leakage probes, and target
   acceptance. Compare the evidence analytically with the already specified
   PCFL-Stream contract in note 48; do not implement PCFL-Stream unless the new
   world fails and a separately reviewed fallback is warranted. A pass means
   only eligible for known-good text/model testing. No tokenizer, model, or GPU.
2. **Disposable known-good text engineering gate.** Two DEV pairs. Oracle atoms/schema plus the generic
   recurrent thinker must reach `.85`; no-memory and nonadaptive access remain
   at most `.35`.
3. **Disposable text-only engineering assay.** Two DEV plus six pairs at `1L/2L`. Compiled text
   must beat raw RAG and A-MEM by `.10` on motif targets and show no spurious
   schema gain in RANDOM.
4. **Disposable transport engineering assay.** Freeze the corpus. LoRA atomic fidelity at least `.90`,
   action no worse than `.10` below compiled text, and improvement over
   direct-QA in at least four of six pairs.
5. **Disposable learned DREAM pilot.** Recover at least 70% of the gold-compiler gain,
   unsupported committed atom rate below 5%, and causal interventions remove
   at least half the gain.
6. **Disposable growth/variance pilot.** Eight fresh pairs, endpoint regimes, essential arms, and
   `2L/4L/8L`.
7. **Confirmation.** Fresh matched super-seeds at the variance-frozen sample
   size, five checkpoints, frozen implementation and baseline set.
8. **On-policy flywheel.** Only after common-deck confirmation.

No stage promotes itself. Every model/GPU transition requires predecessor
artifacts, exact frozen bytes, independent review, and human authorization.

## 11. Kill and pivot criteria

- Growth in tokens without growth in unique edges/entropy: not developmental.
- Fewer than three post-native points: no scaling claim.
- Oracle/manual thinker below `.85` or no-memory above `.35`: reject world.
- RANDOM and MOTIF show equal schema gains: suspect leakage/general compute.
- Prospective schema adds no action value over atoms: no schema-generalization
  or compression claim; action gain without shorter frozen code is
  generalization only.
- Compiled text fails to beat raw RAG/A-MEM: kill the proposed compiler.
- LoRA fails same-corpus noninferiority or direct-QA: remove LoRA from headline.
- Fixed rank/modules/precision/reader budget fails across cuts, or adapter
  bytes/rank must grow linearly with unique mappings: parametric
  storage, not fixed-capacity compression.
- Binding/twin/root interventions remove less than half the gain: no
  experiential attribution.
- Exact graph or explicit motif learner dominates: report the phase diagram;
  do not claim a parametric moat.
- No comparator meets the saturation definition: prohibit saturation/crossover.
- On-policy memory improves neither information gain nor later action: no
  flywheel claim.
- False memories grow faster than corrections or old retention collapses:
  reject continual viability at that scale.

## 12. Proposed authority scope

This proposal requests no present implementation authority. After independent
interpretation, critique, adjudication, and explicit human ratification, the
first requested implementation scope should be **CPU instrument bakeoff only**:

- new non-archive generator and deterministic controllers;
- paired RANDOM/MOTIF/twin construction;
- source/target deck construction;
- leakage, entropy, oracle, path, and resource tests;
- CPU evidence artifacts and a retain/rework/reject decision for
  FeltCraft-Lifetimes against the already specified PCFL-Stream fallback.

Forbidden under that first scope: model/provider calls, tokenizer-derived
scientific cuts, LoRA, GPU/remote actions, locked calibration/confirmation,
paper claims, or promotion to later gates.
