# PCFL-Compose sparse-factor construct and text-pilot specification

**Date:** 2026-09-02  
**Status:** read-only proposed specification. This document is not architecture
consensus, human ratification, implementation authorization, model-call
authorization, GPU authorization, or a scientific result.

## 0. Decision and claim boundary

This is the smallest proposed assay of the following causal chain:

```text
public action--outcome experience
  -> target-blind prospective Dream-1 hypotheses and predictions
  -> later raw public validation experience
  -> Dream-2 self RETAIN / REVISE / ABSTAIN
  -> representational-only sleep compilation
  -> bounded local text-memory reads
  -> goal-conditioned public actions on never-executed compounds
```

It tests one fixed-source, one-sleep-cycle instance of the intended organism.
It does **not** test an on-policy experience flywheel, learned dream/think
control, learned sleep scheduling, trace-conditioned shortcut formation,
open-ended autonomy, or an information-theoretic compression advantage. The
factor grammar has a linear exact sufficient statistic and an exact public
program can solve it. Those limitations are controls and paper boundaries,
not implementation defects.

The CPU construct and text pilot precede any LoRA transport experiment. A text
failure means the content-generation or resolution contract is not yet good
enough to interpret a LoRA result. A text success permits, but does not
authorize, a separately ratified LoRA transport stage.

## 1. Exact algebra and public action semantics

### 1.1 Permutation convention

The public tray has six ordered slots numbered `0..5`, each containing one
fresh unique object handle. A permutation `g in S_6` is serialized as the
six-tuple

```text
[g(0), g(1), g(2), g(3), g(4), g(5)]
```

and maps an object formerly in slot `s` to slot `g(s)`. Thus applying `g` to a
tray `x` produces `y` satisfying `y[g(s)] = x[s]`. Group multiplication is
function composition with the rightmost factor acting first:

```text
(g h)(s) = g(h(s)).
```

All generator, renderer, extraction, dream scoring, exact-program, target
simulation, and analysis code must use this convention. Unit tests must check
identity, inverse, associativity exhaustively over a deterministic sample, and
before/after recovery on fresh handles. No prompt receives the tuple notation,
group name, multiplication equations, hidden factors, or orientation labels.

### 1.2 Hidden factor family

There are nine public stem labels and five public suffix labels:

```text
I = {u0, u1, v1, u2, v2, u3, v3, u4, v4}
J = {j0, j1, j2, j3, j4}.
```

A root life samples private factors `a_i,b_j in S_6` and one private fair bit
`h`. The compound public action `USE(i,j)` applies

```text
h = BA:  t_ij = b_j a_i
h = AB:  t_ij = a_i b_j.
```

The public labels are nonce strings generated independently of factors,
orientation, root seed, orbit bit, target role, and arm. Every action is shown
through a fresh before/after tray, so a public event identifies only that
compound positional operator, never a hidden factor directly.

For either fixed orientation, factors are gauge-nonidentifiable but all
compound transformations in a connected component are identifiable. The
private certifier therefore uses a deterministic gauge-fixed representation;
it never exposes generator factors. For general tree propagation it uses the
alternating group product along the unique tree path.

## 2. The `r=9,c=5` tree-first source construct

### 2.1 Pre-validation source tree

Before any validation outcome exists, execute exactly these 13 source edges on
fresh reset trays:

```text
(u0,j0)
(u1,j0), (v1,j0)
(u2,j0), (v2,j0)
(u3,j0), (v3,j0)
(u4,j0), (v4,j0)
(u0,j1), (u0,j2), (u0,j3), (u0,j4).
```

This is a spanning tree on 14 bipartite vertices. Its public order is sealed
before factors are sampled and is pair-symmetric: within each paired role the
order is counterbalanced by a root-level public schedule bit that is
independent of every hidden variable. The schedule never changes in response
to outcomes, dreams, targets, model outputs, or arm results.

This graph is an unlabeled **double star**. Its degree sequence makes `u0` and
`j0` recognizable as central hubs even if no prompt calls them anchors. It is
therefore a supplied structural scaffold, not a discovery-neutral sparse
graph, and this specification makes no claim that it removes anchor leakage or
tests open-ended graph induction. What remains genuinely prospective is the
choice of a predictive relation/order and its use on omitted compounds. The
matched independent-table family, exact public program, and a generic-versus-
class-informed prompt ablation are mandatory for interpreting specificity. A
bounded-degree alternative would be a new construct requiring a fresh math
audit; it is not silently substituted here.

Conditional on either orientation, this tree supports every target endpoint
and predicts every missing compound. It cannot identify orientation because a
tree has no cycle constraint.

### 2.2 Prospective, non-target validation chord orbit

The two later validation actions are

```text
(u1,j2), (v1,j2).
```

They are not target pairs. The two-edge orbit, rather than a single chord, is
required to preserve the paired-label equivariance used by the hidden orbit.
Both fresh reset trays and action order are sealed before source realization.

Dream-1 sees the 13 raw tree events and is told only that these two public
actions will occur later on the displayed fresh reset trays. It must commit
its reusable hypotheses and its exact predicted post-action trays before
either chord outcome is produced. The commitment is content-hashed and
timestamped. Only then are both actions executed and their raw public
before/after events released.

The private construct certifier must establish, for every orbit member, that:

1. the true orientation's tree completion predicts both chord outcomes;
2. at least one chord rejects the wrong orientation;
3. exchanging `u1` and `v1` maps the ordered chord data equivariantly; and
4. neither validation pair equals a D1 or D4 target pair.

No comparator label (`MATCH`, `MISMATCH`, `SUPPORTED`, truth value, distance,
or corrected prediction) is shown to the headline Dream-2. It receives the
raw committed prediction text and the raw later public outcomes.

## 3. D1 and D4 targets

### 3.1 Never-executed decisive pairs

At D4 stage `l`, the fixed-order menu is

```text
USE(u_l,j_l)  or  USE(v_l,j_l),   l=1..4.
```

All eight compounds are absent from the source tree, validation orbit,
compiler input, dream prompt indexes, and every derived closure exposed to a
model. In a base root (`z=0000`), the canonical correct choice is `u_l` at
every stage. Starting from a fresh tray `x`, the goal is the result of applying
those four canonical transformations in stage order. Every stage menu is
visible before the first action; only the current public tray changes after an
action.

D1 uses one presealed stage `l*` per root, selected independently of factors
and rotated evenly across roots. It presents a fresh start, the corresponding
one-action goal, and the same fixed-order pair menu. Its target-only Bayes
value is `1/2`.

D1, D4, arms, authentic-memory, and memory-swap evaluations run from isolated
clones of the same frozen pre-target state. No target action or outcome from
one evaluation may enter another target, corpus, reader index, model context,
or retry. Otherwise D1 can teach a stage bit to D4 and the orbit bound is
invalid.

### 3.2 Exhaustive path and no-shortcut certificate

For D4, the CPU certifier enumerates all 16 complete menu sequences and every
prefix of lengths zero through three. In every hidden orbit member it must
prove:

- exactly one length-four sequence reaches the goal;
- its four labels are the member's registered bit sequence;
- no length-zero-to-three prefix reaches the goal, so early `LOCK` fails;
- after any wrong prefix at any stage, no legal continuation recovers the
  goal;
- substituting the wrong orientation's prediction changes at least one
  decisive transformation and its registered plan fails;
- each stage's paired transformations are distinct on every tray reachable at
  that stage; and
- no source or validation action is offered in an evaluation menu.

For D1, exactly one menu action reaches the goal and early `LOCK` fails. Any
seed that violates a certificate is rejected before model-visible bytes are
rendered. Rejected seeds and reasons remain in the construct ledger.

This is four environment-action depth, not four-hop memory depth. No graph-
reasoning claim may be inferred from D4 alone.

## 4. The independently swappable `2^4` target orbit

### 4.1 Full private orbit

For root factors `H_0000`, construct 16 hidden lives `H_z`,
`z in {0,1}^4`. At bit `l`, swap the complete stem-factor assignments of
`u_l` and `v_l` and leave all other factors and the orientation fixed:

```text
z_l=1:  a^z_u_l = a^0_v_l,  a^z_v_l = a^0_u_l.
```

The swap applies to every source, validation, and target suffix. It therefore
changes the public life evidence equivariantly rather than hiding the life
difference. It changes no target-visible byte. Because the transformation
needed at stage `l` is carried by `u_l` when `z_l=0` and by `v_l` when
`z_l=1`, all 16 correct D4 label sequences are distinct while the start, goal,
menus, budgets, rendering, and target order are byte-identical.

Because each bit swaps only its own disjoint stem pair, a public target outcome
at stage `l` cannot reveal an unacted future-stage bit. Together with the
no-wrong-prefix-recovery certificate, this makes target-only full success a
four-bit decision rather than a retry/search opportunity.

The root generator must hash and compare the complete **pre-action** target-
visible packet across all 16 variants. Post-choice public tray outcomes may
differ and are logged as environment feedback. It must separately certify
source/validation schedule equivariance under every single-bit swap, including
the paired event-slot and fresh-handle-renaming bijection. There may be no orbit-dependent file
name, public identifier, token length, source-order imbalance, handle pattern,
RNG continuation, cache state, error text, latency field, or arm ordering.

With a sealed uniform prior over all 16 orbit members:

```text
Bayes(target-only D1 action)          = 1/2
Bayes(target-only D4 first action)    = 1/2
Bayes(target-only D4 full trajectory) = 1/16.
```

A single global twin pair would establish only a `1/2` D4 full-trajectory
bound. It must never be described as establishing `1/16`.

### 4.2 Feasible materialization plan

The full 16-member orbit is mandatory for CPU certification, but it need not
create 16 model corpora or adapters per independent root.

For model experiments, sample one `z` uniformly from `{0,1}^4` using a sealed
root-independent RNG, then materialize `H_z` and the predeclared antipode
`H_(z xor 1111)`. Each marginal life is uniform over the full orbit, so the
population target-only D4 theorem remains `1/16`. The antipode has identical
target bytes and flips all four correct actions, giving a strong whole-memory
swap intervention with two life corpora/adapters per root.

This two-realization design does **not** empirically exercise all 16 correct
sequences within one root and does not estimate four separate stage-level
memory effects. Those require a full orbit or additional single-bit
counterparts. Claims must distinguish:

- the exact CPU theorem over the certified 16-state prior;
- empirical model performance under uniformly sampled orbit members; and
- the two-life antipodal whole-memory causal contrast.

One full 16-life model orbit may be run as a leakage/position-bias diagnostic,
but it is not the default confirmation unit. The independent root, not a
target, stage, orbit member, or adapter seed, is the replication unit.

## 5. Prospective Dream--validation--Dream protocol

### 5.1 Fixed generic Dream-1

Dream-1 is one frozen-model call per materialized life. It receives only the
13 raw public tree events, public action syntax, the two announced future
validation actions and their fresh initial trays, a fixed candidate budget
`K`, and a generic research-memory instruction. It is not told `S_6`, factor,
row, column, anchor, stem effect, suffix effect, composition, orientation,
tree, chord, group, target, D1, D4, or the two-law hypothesis class. This does
not hide the public two-part tool morphology or double-star degree pattern;
those are explicitly acknowledged scaffolds.

The instruction asks it to propose up to `K` reusable target-independent
explanatory **packages** and to attach an exact prospective prediction for
each announced future action. It may abstain. Each package has a stable ID,
one concise explanation, up to `R` already-atomic standalone memory records,
public evidence citations for every record, both predicted post-action trays,
and uncertainty. `K`, `R`, and all byte caps are frozen before generation.
The package is the competing world model; the records are what may later be
read. This separation lets a generic dream propose a connected account without
requiring every local record to predict both chords by itself. Package and
record order are randomized by a sealed presentation seed and canonicalized
only after commitment.

There is one call, no propose/filter retry, no enumerated hypothesis menu, and
no target-conditioned daydreaming. Malformed, missing, or abstained candidates
remain in the denominator.

### 5.2 Fixed generic Dream-2 self-review (headline)

After the commitment, Dream-2 receives:

- the same raw tree events;
- the exact unedited Dream-1 candidates and predictions; and
- the two raw public validation before/after events.

It receives no mechanical comparison, score, hidden truth, exact factor fit,
candidate rank, or corrected claim. In one call, it must assign each existing
candidate exactly one terminal operation:

```text
RETAIN(package_id, unchanged_records, citations)
REVISE(package_id, replacement_records, citations, reason)
ABSTAIN(package_id, reason).
```

`REVISE` may repair that candidate once from the newly observed public events;
it may not create additional candidates, ask for more actions, or retry after
an offline score. False self-approved claims remain in memory and count
against downstream action. This raw-evidence self-revision arm is the primary
headline condition.

### 5.3 Required comparison arms

All arms share the same committed Dream-1 output.

1. **No gate:** compile every well-formed Dream-1 package without exposing
   validation outcomes or Dream-2 decisions.
2. **Self-revision headline:** compile exactly Dream-2's retained and revised
   content. No external admission decision is allowed.
3. **Perfect public-prediction gate ceiling:** a mechanical comparator admits
   a precommitted package iff both exact predicted validation trays match
   both later public outcomes. It cannot repair content, use hidden factors,
   judge target correctness, generate candidates, or trigger retries.
4. **Optional MATCH/MISMATCH-assisted ceiling:** Dream-2 receives only the two
   exact comparison bits in addition to raw outcomes. This is not the
   headline and must be labeled assisted.

The perfect public gate is only a public-evidence filtering ceiling. Passing
two chord predictions is not an oracle proof that every sentence in a package is
true. Offline hidden-truth scoring never routes memory.

### 5.4 Representational-only sleeper

The sleeper receives only the selected packages' textual records and their
public citations. It may:

- validate syntax and cited public-event existence;
- assign content-independent stable IDs;
- preserve RETAIN/REVISE/ABSTAIN and uncertainty fields;
- flatten a package's already-delimited records without rewriting them;
- exact-deduplicate byte-identical claims while merging citations;
- create deterministic entity, relation-word, and time indexes that point to
  the same unchanged claim; and
- serialize the same record grammar for the common reader.

It may not infer factors, solve equations, propagate the tree, select an
orientation, compare predicted and actual outcomes in the headline, alter a
claim's semantics, paraphrase missing content, enumerate omitted compounds,
invent shortcuts, rank by hidden correctness, delete a false retained claim,
or see targets/certificates. A revised record preserves the superseded text as
a negative/superseded ledger entry; an abstention remains in the audit ledger
but not in active memory.

The primary schema-neutral record contract permits one unchanged standalone
claim, typed only as `GENERAL_RULE`, `LOCAL_RELATION`, `EXCEPTION`, or
`UNRESOLVED`, with a fixed byte cap and public citations. It does not request
stem factors, suffix factors, orientation, or an equation. A record may not
contain a completed target compound, target-specific plan, full compound
table, or an enumeration of local bindings. Dream-2, not the sleeper, must
emit content that already satisfies this generic contract.

A separate **class-informed ceiling** may request one global composition-law
record and one gauge-fixed local effect per public stem or suffix. That ceiling
diagnoses whether failure is hypothesis generation, memory format, or use,
but it supplies the relevant factorization and cannot support the headline
Dream claim. The exact generic record byte cap and whether even the four broad
`KIND` labels are acceptable scaffolding require ratification.

## 6. Text-memory reader and thinker contract

### 6.1 Common local reader

The text pilot uses the same query/response protocol intended for later LoRA
transport. A query is generated by the thinker from current target state and
workspace. The reader returns at most one immutable atomic record or
`NOT_FOUND`, with stable ID and provenance; it never returns a completed
compound, target-assembled bundle, plan, solver output, or full table.

Reader calls, `NOT_FOUND`, repeated queries, workspace revisions, actions,
and stopping decisions are logged. Repeating an identical query consumes
budget. Retrieval code may match indexes; it may not infer the answer.

Under the canonical gauge-fixed exact-schema control, selecting one D1 action requires
at most two candidate-stem records, one suffix record, and one orientation-law
record: cap `4`. D4 generally requires eight candidate-stem records, four
suffix records, and one orientation-law record: cap `13`. Environment actions
and `LOCK` are separate from memory-read budget. A lower cap is reader
starvation for that declared interface. The generic headline also receives at
most 4/13 record reads, but every returned byte and claim width is reported;
if its learned records package more information than the exact atoms, that is
a measured representation difference rather than a free compression claim.
The raw episodic arm may read all 15 eligible public events because imposing a
13-item cap on 15 event atoms would mechanically starve it. Increasing any cap
after seeing results is a new DEV version.

### 6.2 Minimum-read and no-solution-packet certificates

For each generated root, the exact certifier emits the 13-record canonical
schema and a necessity witness for every declared D4 record. For each record,
it searches legal alternative factor values while holding target-visible bytes
and all other accessible records fixed, and requires an alternative under
which the unique correct first action changes. It emits the paired private
world hashes and exact plans. If no such alternative exists for a record, that
record is not counted as necessary and the declared minimum is recomputed.

The certifier additionally scans every reader record and response fixture to
ensure no response contains two entity bindings, a completed target
transformation, target label sequence, target goal annotation, or hidden
certificate. The exact program must solve from the same itemwise records under
the declared cap before model evaluation.

The thinker is a fixed generic goal-state loop. On each step it may `READ`,
update a cited `THINK` workspace, issue the next public `USE`, `LOCK`, or
abstain. It receives no algebra recipe, parent/factor menu, hidden truth, or
external verifier. All menus are visible from the beginning, but action
outcomes are revealed only after issue. A one-shot full-schema planner at the
same information and approximate output-token budget is a mandatory control;
an iterative-thinker advantage cannot be claimed without it.

## 7. Independent-table matched negative

For every factorized root, construct a negative-law root with the same public
label generator, tree/chord roles, action counts, ordering, reset trays,
renderer, target menus, orbit prior, target depths, permutation marginals, and
target-byte checks. Instead of factors, sample every base compound
transformation `t_ij` independently and uniformly from `S_6`, subject only to
the same target uniqueness and nondegeneracy rejection tests.

Create its `2^4` orbit by swapping the complete independent transformation
rows of each `(u_l,v_l)` pair. Choose the fixed target goal from the base
canonical `u_1..u_4` path, so the correct label sequence still follows the
orbit bits and all target bytes remain fixed. Because each never-executed
target transformation is independent of eligible source and validation
events, source experience cannot identify the correct target sequence.

The full 16-state CPU theorem and the sampled-`z` plus antipode materialization
rules are identical to the factorized family. Any above-prior unseen-compound
action value, systematic non-abstaining law claim, or orbit-bit prediction in
this family is evidence of leakage, unmatched marginals, or evaluation noise;
it is not evidence for a more powerful dreamer.

## 8. Target/oracle firewall and chronology

Every root is split into immutable private and public artifact trees.

**Private scorer-only:** hidden factors/table, orientation, orbit bit, complete
closure, gauge schema, wrong-law predictions, target identities, correct
sequences, alternative-world read certificates, uniqueness/no-shortcut
certificates, and offline truth labels.

**Public eligible:** raw source events; announced validation action/reset
packets; later raw validation events; model commitments; selected textual
memory; and, only after memory freeze, target start/goal/menu packets.

The required chronology is:

```text
T0  seal generator version, root seed, 16-state orbit, schedules, targets,
    prompts, parser, budgets, arms, retries, and all private certificates
T1  expose the 13 raw tree events
T2  run and hash Dream-1 commitment
T3  execute/release the two raw validation chord events
T4  run and hash Dream-2 self-review; derive no-gate/public-gate arms
T5  run representational sleeper; freeze and hash every corpus/index
T6  render target-visible packets and start thinker evaluation
T7  perform offline scoring and causal memory/cut analyses
```

The public build process must be unable to import or open the private artifact
tree. Prompt builders, readers, sleeper, trainer inputs, model-visible logs,
parsers, errors, caches, and retry messages are scanned for private tokens and
target labels. Targets cannot affect source selection, candidate admission,
corpus size, record order, model sampling, or retry. A tainted process is
destroyed and restarted from frozen public artifacts before evaluation.

## 9. CPU construct acceptance suite

No model call is justified until every item below is green for both the
factorized and independent-table families.

1. **Algebra:** serialization, action, inverse, composition direction, and
   before/after extraction agree exactly.
2. **Graph:** exactly 14 vertices, 13 tree edges, connected and acyclic before
   validation; exactly the two registered non-target chords afterward; the
   double-star hubs and supplied-scaffold limitation are present in manifests
   and report language.
3. **Identifiability:** both laws fit the tree; true law fits chords; wrong law
   fails at least one chord; commuting/observationally-equivalent roots reject.
4. **Target causality:** wrong-law and each decisive-factor cut change the
   registered target plan or make it fail.
5. **Orbit:** all 16 target packets hash identically, all 16 correct D4
   sequences are distinct, and source/chord schedules are equivariant.
6. **Targets:** D1 and D4 uniqueness, no early lock, no wrong-prefix recovery,
   never-executed pairs, and fresh handles hold in every orbit member.
7. **Reader:** exact program succeeds itemwise under caps 4/13; each declared
   necessary record has a legal decision-fork witness; no record is a solution
   packet.
8. **Negative law:** rendering and target distribution match, all target pairs
   are conditionally independent of eligible evidence, and exact factor-law
   code abstains or scores at the registered prior.
9. **Firewall:** public code cannot address private files; byte/taint scans,
   clean-process replay, and target-after-corpus chronology pass.
10. **Totality:** every attempted and rejected root, parse error, timeout, and
    missing artifact is accounted for; no silent regeneration or denominator
    removal occurs.

The CPU report is hash-bound to generator code, seeds, public/private
manifests, prompt bytes, parser, reader grammar, and expected denominators.

## 10. Minimal text-pilot arm roster and metrics

The smallest scientifically interpretable DEV text pilot uses one complete
16-life orbit from one root as a leakage/position diagnostic **or** at least
two independently sampled roots with their antipodes as a plumbing canary.
Neither is confirmation evidence. The former diagnoses every target label
sequence; the latter exercises the cost-feasible future sampling design.

Required arms are:

1. target-only frozen thinker (bias/prior measurement);
2. raw episodic text reader with all 15 eligible public events available and
   an explicitly reported event/byte budget;
3. no-gate compiled Dream-1 text;
4. self-revised compiled text (headline);
5. perfect-public-gate compiled text (ceiling);
6. exact public factor-program planner (non-LLM ceiling); and
7. class-informed Dream/self-revision compiled text, whose prompt states the
   two-factor/two-order hypothesis class but supplies no factors, order, chord
   result, or target (structural-scaffolding ceiling); and
8. one-shot exact-schema text planner at equal information/work (resolution
   control).

The exact program must score 100% on all factorized D1/D4 constructs and the
registered prior/abstention behavior on the independent-table family. If it
does not, the construct is invalid and model scores are uninterpretable.

Report, without conditional denominator deletion:

- Dream-1 candidate count, parse rate, prospective exact-prediction rate,
  hidden-truth precision/recall, and abstention;
- Dream-2 RETAIN/REVISE/ABSTAIN confusion against offline truth, false-retain
  rate, correction rate, and coverage change;
- active-corpus atomic coverage, truth precision, bytes, and provenance;
- unconditional D1 success, D4 full-trajectory success, first-action success,
  early/wrong action rate, abstention, and public action cost;
- read count, `NOT_FOUND`, repeated reads, cited-item use, workspace revisions,
  and one-shot versus iterative performance;
- authentic versus antipodal whole-memory swap, wrong-law cut, decisive-factor
  cut, and equal-size sham cut; and
- factorized versus independent-table performance under identical observable
  envelopes.

Prospective tray predictions and public actions are scored mechanically and
exactly. Free-text record truth is secondary: an executable record may be
checked by a predeclared offline parser; a non-executable interpretation must
be independently coded under a frozen blinded rubric with disagreements
reported. Neither route can affect admission, retry, corpus bytes, or thinker
input. Downstream public action remains the primary semantic-use outcome.

All root-generation failures, Dream parse failures, empty corpora, sleeper
failures, reader failures, model timeouts, wrong actions, and abstentions stay
in the original root/life denominator. A predeclared infrastructure retry may
replay identical frozen public bytes once in a clean process; the first failure
remains reported, and a retry never changes a scientific record.

### Recommended promotion rule (requires ratification)

A text pilot should permit a LoRA proposal only if all exact construct tests
pass, the headline has nonzero prospective true-schema coverage before target
release, self-revision does not increase false-retained content, compiled-text
D4 exceeds the target-only arm on paired roots, the authentic memory beats its
antipodal swap and decisive cuts, and the independent-table family remains at
its registered prior or abstains. Exact numerical margins and the number of
independent roots must be ratified before model outputs; a one-root DEV orbit
cannot establish a paper claim.

## 11. Cost and replication accounting

### 11.1 CPU estimate (planning estimate, not measured)

One root requires 16 orbit variants, fewer than 1,000 direct target trajectory
simulations for path/short-cut checks, and at most roughly
`13 * 719` legal single-record alternatives before target-plan enumeration for
the minimum-read witnesses. Straightforward optimized Python should be on the
order of seconds to a few CPU minutes per accepted root; rejection sampling
and exhaustive read-fork searches dominate. Budget `<30 CPU-min/root` with a
hard attempt cap and preserve failed seeds. A 20-root construct suite should
fit comfortably within one CPU-day and requires no model or GPU.

### 11.2 Full-orbit DEV text pilot

For one 16-life orbit:

- Generic Dream: `16 Dream-1 + 16 Dream-2 = 32` large-model calls, shared by
  the three generic dream arms. The class-informed ceiling adds another 32.
- One iterative text arm: D1 cap 4 plus action/lock and D4 cap 13 plus four
  actions/lock, at most about `23 calls/life`, or `368 calls/orbit` if one
  resolver operation is one call.
- The three generic dream-corpus arms therefore cost at most about `1,104`
  thinker calls. The class-informed arm adds `368`. Raw-text and exact-schema
  LLM controls can add up to `736`; target-only can add up to `96`, depending
  on whether public actions share a call.
- Total planning envelope: about `64` dream calls and `1,500--2,400` short
  thinker calls. Batching or allowing several local ops per call may lower the
  count but changes the controller contract and must be frozen in advance.

Using the repository's prior 32B measurements only as rough anchors (53 dream
calls in 29m29s; 44 short thinker calls in 3m01s), this is roughly `3--8`
32B GPU-hours. It is not a measured PCFL runtime and no run is authorized here.

### 11.3 Cost-feasible root-pair design and future LoRA implication

With sampled `z` plus antipode, one root materializes two lives: four generic
dream calls (eight if the class-informed ceiling is also run) and at most `46`
thinker calls per iterative arm. At four future memory
checkpoints, one LoRA condition would require `2 lives * 4 = 8` adapters/root.
Sixteen independent roots would therefore require 128 adapters per LoRA arm;
at the repository's very broad `0.1--0.883 GPU-h/adapter` anchor, training
alone is approximately `13--113 GPU-h/arm`, before dream and evaluation.

Materializing the full orbit would require 64 adapters/root/arm at four
checkpoints, or 1,024 adapters/arm for 16 roots (`102--904` GPU-hours of
training alone). Therefore the old small twin-pair budget cannot silently be
applied to this corrected orbit. Full-orbit LoRA is a diagnostic luxury;
sampled uniform members plus a predeclared antipode is the proposed default.
Any LoRA roster, checkpoint count, adapter count, or powered sample size needs
fresh cost review and exact ratification.

## 12. Design choices still requiring exact human ratification

The following are not settled by this advisory:

1. adopting sparse-factor PCFL-Compose rather than PCFL-Stream or another
   paper construct;
2. accepting the `r=9,c=5` tree and exact two-chord schedule as Paper-1's
   primary world;
3. accepting the full CPU orbit plus sampled-`z`/antipode model design instead
   of materializing all 16 lives;
4. the exact root count, DEV/confirmation split, seed list, and replication
   unit;
5. exact Dream-1/Dream-2 prompt bytes, `K`, temperatures, token budgets, pinned
   model/revision, parser, retry policy, and whether the proposed atomic output
   grammar is permissible scaffolding;
6. the sleeper's exact normalization/index operations and record byte caps;
7. reader query grammar, one-item response contract, caps `4/13`, thinker
   operation grammar, and one-shot work matching;
8. the required arm roster, whether the class-informed Dream ceiling is run
   on the full DEV orbit, negative-law allocation, causal cuts, and exact
   promotion/falsification margins;
9. whether one full-orbit text diagnostic is worth its model-call cost;
10. any LoRA stage, corpus rendering multiplicity, training recipe, model
    split, GPU roster, checkpoint schedule, or confirmation claim; and
11. paper wording beyond the narrow fixed-source prospective factor-law
    compilation/action claim in Section 0.

Until those bytes and scope complete the repository's architecture-
deliberation path and receive explicit human ratification, the authorized next
work is limited to further read-only design review.

## 13. Required interpretation of a positive result

The strongest warranted positive statement from this construct would be:

> In a sealed noncommutative compound-action family, a frozen generic resolver
> proposed and self-revised a prospective factorized representation from its
> own public action outcomes; a representational compiler preserved it; and a
> bounded generic resolver used local text-memory reads to execute
> never-executed compounds above target-only and matched independent-law
> controls.

Only a later same-corpus LoRA experiment could add that the selected per-life
content survived weight-space transport. Neither result alone establishes a
self-improving lifelong agent, an advantage beyond context saturation, or a
learned reasoning policy.

## Provenance

This specification integrates the mathematical corrections and construct
requirements in:

- `research_loop/advisory/20260902_sparse_factor_graph_math_audit.md`;
- `research_loop/advisory/20260902_pcfl_compose_paper_world.md`;
- `research_loop/advisory/20260902_pcfl_architecture_mapping_audit.md`;
- `research_loop/advisory/20260902_pcfl_compute_feasibility.md`; and
- the project-level governance contract in `AGENTS.md`.
