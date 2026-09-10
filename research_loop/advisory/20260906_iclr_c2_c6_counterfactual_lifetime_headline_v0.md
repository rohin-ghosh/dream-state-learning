# ICLR C2--C6 headline experiment: Counterfactual Lifetime v0

Date: 2026-09-06

Status: **design advisory only**. This file does not authorize an architecture
change, implementation, benchmark or target enumeration, model call, training
run, GPU use, external export, or scientific claim. Any adoption must enter the
complete `AGENTS.md` deliberation, exact-byte human ratification, implementation
review, and pre-GPU gate. No target identity, seed, answer, action tuple, or
model output is selected here.

## Executive decision

The smallest experiment that can still carry the intended ICLR paper is one
prospective, paired, long-life study on **Counterfactual Confluence v0.3-R**
(`lands/v03r.py`), followed by one deliberately subordinate parent-absent
CompilerGym transfer study.

Do not make CompilerGym the C2--C5 benchmark. It can measure useful procedural
adaptation, but a generic pass prior or action imitation can explain a gain; it
cannot identify connected experiential knowledge. Do not build RTCW or full
PCFL before September 16. Those are stronger future populations, but neither
paper-bearing generator/agent loop exists today. Do not return to Semantic
World v0.2 D3: v0.3-R was created precisely because passive target signatures
and complementary controls made earlier D3 interpretations unsafe.

The proposed broad arc is:

```text
same agent's prospectively recorded public action/outcome life
  -> recurrent target-blind model proposals
  -> later public outcomes admit or reject local links
  -> exact native response-only per-life LoRA writes
  -> fresh post-context multi-edge actions at 0.75C, 1.5C, 3C, 6C
  -> paired twin/binding/link/adapter interventions
  -> parent teaches one process correction at a time
  -> parent and all nursery text disappear
  -> parented child versus regular agent in a fresh compiler gym
```

The main confirmation uses 20 independent paired super-life roots. It has the
seven requested causal conditions: frozen, strong active textual memory, raw
periodic LoRA, final-batch LEAFE-style recovery distillation, periodic native
consolidation, action/outcome derangement, and exact adapter-off replay. A
terminal, three-cell carrier panel is the minimum extra mechanism work needed
for C5: compact linked records, the same links left unshortened, and
token/dose-matched witnessed atoms only.

If C2--C5 do not all survive the registered gates by September 16, the broad
Experience Models abstract is killed. CompilerGym cannot rescue it. C6 is the
final bridge, not a prerequisite: if its parenting-by-online-learning
interaction misses, move the complete C6 panel to the appendix or omit it and
delete “meta-intelligence” from the paper.

## Why this benchmark, and why not the alternatives

### Use v0.3-R as the controlled primary

The current repository already gives v0.3-R several properties that would take
most of the remaining calendar to recreate elsewhere:

- its paired twins require both latent sides to be correct;
- target-visible bytes and passive signatures can be identical while the
  decisive intervention binding and correct action differ;
- route and intervention-effect evidence is separated by more than the working
  context;
- the final goal is revealed only after an operational probe and pre-goal
  checkpoint;
- a parent-free oracle solves through public atomic edges, rather than a hidden
  parent-set object; and
- development/held-out grouping is derived from a passive-feature hash.

This directly answers the two defects that demoted Semantic World v0 D3. The
v0.2 repair established identifiability and a useful controller ceiling, but
its successful 32B path exhaustively enumerated 57 subsets and 114 proof leaves
per target, retained the relevant memories in text, and never established a
LoRA lifetime result. The v0.3-R causal path is a better small microscope for
the present claim.

The exact target action in v0.3-R requires joining public relations of the
following *kinds*, not copying one record: an intervention control to a source,
the intervention's target effect, an entity's latent functional role, that
role's source contribution, a passive target state, and a public workshop
mapping. The model and writer never see the hidden proof or target answer.
This is sufficient structure for a causal connected-memory test without
scoring prose rationales.

### Add only a thin long-life relay

One v0.3-R life is too short for C4. Construct a `super_life_root` by
namespacing and chronologically concatenating independently generated v0.3-R
component lives. The wrapper changes no component-world law. Each successive
era adds new handles, causal bindings, and goal opportunities; it may not add
filler or repeat a prior component. A paired side flips the sealed latent
bindings while retaining the component's permitted twin-equal surfaces.

Let `C` be the measured usable native context after the exact system prompt,
tool schema, workspace, operation history, and output reserve are tokenized.
The four checkpoints are the first complete era boundaries reaching at least
`0.75C`, `1.5C`, `3C`, and `6C` cumulative public source tokens. All arms use
the same boundaries. If the generated source population cannot reach all four
without invalid worlds, repeats, or filler, C4 is unavailable and the broad
run stops.

### Reject an off-the-shelf primary for this deadline

ALFWorld, ScienceWorld, WebShop, BabyAI, and related agent benchmarks provide
external recognition, but adopting one now adds environment integration and
validity work while weakening the C5 intervention. They generally do not offer
paired, byte-matched causal twins; exact necessary-edge cuts; a public local
solution oracle; or a target-blind semantic rate measure. They are also where
LEAFE and the strongest textual-memory systems already have mature results.
A rushed small reproduction would be both weaker and easier to dismiss.

CompilerGym remains useful for the C6 bridge because its metric is objective,
dense, and externally recognizable. The existing Fable run also proves it can
separate useful action content from broken action routing. It must be described
as an external procedural-learning transfer, never as the connected-memory
evidence.

### Defer RTCW/PCFL rather than pretending they are ready

The RTCW/RML and PPC/PCFL designs contain the right future population,
interactive proof, and causal-memory contracts. Their own audits require a new
generator, a validated recurrent controller, and tens of pair roots. Current
RML code is a D0/G1 controller fixture; current PPC artifacts are extensive
proposal and static-fixture infrastructure, not the required C2--C5 runtime.
Starting either paper benchmark now would spend the September 9 protocol-freeze
deadline on benchmark construction.

## Exact scientific questions

The confirmation tests these ordered claims and no stronger ones:

- **C2:** under common source experience and equal generated-token budgets,
  periodic personal native LoRA writes improve post-context held-out action AUC
  over the same frozen agent loop;
- **C3:** at the terminal lifetime, the periodic native system beats strong
  active textual memory, raw periodic response distillation, and one final
  matched LEAFE-style recovery write;
- **C4:** the periodic-native advantage grows across the registered context
  multiples while earlier-era competence is retained and new-era competence is
  acquired;
- **C5:** a shorter, connected, model-authored and public-outcome-admitted code
  exists before target reveal, and breaking its bindings or connected carrier
  removes the corresponding action gain; and
- **C6:** after a single fixed parent has taught process corrections and then
  disappeared, the resulting child learns a disjoint fresh gym faster under
  the same Think--Dream--Sleep architecture than the regular agent does.

C2--C5 are mandatory for the ambitious paper. C6 is mandatory only for the
“parented meta-intelligence” clause.

## Frozen agent architecture for the study

Use one pinned Qwen2.5-7B-Instruct checkpoint and tokenizer for the acting
agent, DREAM calls, memory reads, and native response targets. The parent in C6
is the same pinned engine under a frozen parent role prompt. This is one model
wearing roles, not a separately trained teacher or a population architecture.
The only learned state is one rank-8 per-life LoRA; the base remains frozen.

Every model turn receives a tokenizer-bounded public `ConsciousState` and one
closed structured-operation schema. It emits exactly one native tool call:

```text
QUERY | FOLLOW | HYPOTHESIZE | PREDICT | ACT | REVISE | BACKTRACK | STOP
```

Assistant prose is inert. An invalid, missing, or multiple call consumes the
opportunity and receives the registered no-action value. No regex fallback or
permissive parsing can rescue a primary endpoint. A typed-forced generation of
the same action object is run separately as a proposal-quality guard; it is an
upper-bound diagnostic and never substitutes for free native action.

The append-only private ledger records exact message arrays, rendered bytes,
input IDs, full native response envelope, assistant text bytes, structured
channel bytes, output IDs, parser decision, dispatch authorization, public
outcome, state hashes, generation seed, adapter hash, source hash, and resource
use before any downstream consumer runs. Each evaluation item starts in a
fresh process/cache/ledger. Evaluation outputs never feed sleep.

### Wake/source contract

Create one prospective base-policy source life for each root and twin side,
then clone its sealed public action--outcome chronology into every C2--C5 arm.
The frozen source actor uses the same typed operation interface and a
target-blind, coverage-oriented exploration goal. It is permitted generic
operation guidance, not a target answer, hidden edge, or benchmark-specific
plan. All attempted actions, failures, predictions, public outcomes, and
recoveries remain in the chronology. A root is usable only if the public
source path contains the predeclared minimum support for its later targets;
eligibility is decided before any target goal is revealed, every attempted
root remains in the funnel, and failed roots are never silently replaced.

This common-deck construction is deliberately conservative. It identifies the
memory/consolidation system under the same self-generated experience; it does
not claim that C2--C5 are an on-policy flywheel. C6 supplies the bounded
on-policy bridge.

### DREAM and world admission

At fixed pre-goal sleep opportunities, the current base plus permitted
per-life adapter receives only public replay bundles. It may propose one local
typed record at a time:

```text
WITNESSED_ATOM | CAUSAL_EDGE | USE_LINK | PROCEDURE_SHORTCUT |
POLICY_CASE | FUTURE_TEST | PASS
```

Every non-atom proposal names public event/record parents. A model cannot mark
its own proposal supported. Admission follows these rules:

1. a witnessed atom is supported only by the exact public event;
2. a causal edge is positive training data only when it committed a public
   prediction before a later ordinary outcome and that outcome agrees;
3. a use link records co-traversal but never grants factual support;
4. a procedure shortcut is eligible only after its full constituent path has
   succeeded in at least two provenance-distinct component lives; and
5. contradictions remain append-only and yield native `REVISE` or
   `BACKTRACK` targets, never a repaired positive fact.

The hidden generator may score committed records offline after sealing, but no
hidden verdict, proof, answer, or error explanation returns to DREAM, SLEEP,
the actor, the textual updater, or the trainer.

### Native SLEEP/write contract

SLEEP deterministically serializes only two response-target families:

- `READ`: exact runtime local query and target-blind candidate domain to one
  supported local value or `NOT_FOUND`;
- `DECIDE`: exact runtime public state to the agent's own successful or
  verified-recovery structured operation.

Inputs, public outcomes, parent text, restatements, ledgers, and memory returns
are loss-masked. Loss covers the complete native assistant response suffix,
including structured-channel control tokens and EOS. No bare prose, whole-
sequence loss, reconstructed prompt, normalized replacement JSON, or hidden
answer is a target.

Every trained arm receives the same prebound source/target-disjoint native
success rehearsal packet. Rehearsal occupies 20% of effective supervised
target tokens and is interleaved across age. At each periodic cut, rebuild the
cumulative adapter from the clean base; later DREAM calls may use that adapter,
so recurrent consolidation can change the next set of model-authored links
without changing the common public source deck.

Before any scientific task identity is available, choose one writer heat with
a treatment-neutral native writer canary containing ordinary successful typed
responses and matched rehearsal only. Test rank 8 at learning rates
`1e-6`, `3e-5`, and `1e-4`; freeze the lowest rate that passes native
absorption, free tool compliance, typed-forced non-erasure, generic behavior,
and deterministic-replication gates. No treatment arm selects its own heat. If
none passes, stop. Rank, modules, alpha, dropout, optimizer, precision, epochs,
and replay law then remain fixed.

## Seven main causal conditions

Every condition gets the same sealed source chronology, acting model, public
state, operation/action/read budgets, generated-token allocation, evaluation
panel, and target reveal time.

| Condition | Persistent state and exact implementation obligation | What it identifies |
|---|---|---|
| `FROZEN` | Base agent; scheduled DREAM/SLEEP calls consume their token allotment but their outputs are sealed and discarded. No text memory or adapter enters action. | No-learning loop and sleep-inference control. |
| `TEXT_ACTIVE` | Append-only raw ledger plus an actively refined identification/maintenance/action-guidance store. Hybrid exact/entity-relation and semantic retrieval, bounded graph expansion, contradiction handling, and one-record-per-read output. The updater receives the same writer-call/generated-token budget as native SLEEP; storage is not artificially capped. | Strong ReMem/MemoPilot/A-Mem-class external-memory competitor, not raw RAG. |
| `RAW_PERIODIC` | At each cut, response-only rank-8 LoRA on exact native successful and failure-to-recovery action continuations directly from raw public trajectories; no cross-event semantic records or shortcuts. Same rehearsal/effective supervised tokens/updates as `NATIVE_PERIODIC`. | Direct experience/action distillation and raw periodic weight-write control. |
| `LEAFE_FINAL` | No mounted learning state before the terminal cut. At the end, run the registered LEAFE procedure over the complete source: reflect on failure points, roll back, generate revised branches, retain improved post-rollback native actions, add successful-behavior rehearsal, remove reflection text from training inputs, and make one rank-8 response-only fit. Total reflection generation, effective supervised target tokens, optimizer updates, rank, and rehearsal equal the cumulative periodic allocation. | Strong matched final-batch reflective recovery distillation. It is an adaptation of LEAFE to per-life LoRA, not a claim against LEAFE's published full-SFT numbers. |
| `NATIVE_PERIODIC` | Repeated public-outcome admission plus cumulative native `READ`/`DECIDE` writes at every cut. No explicit semantic text, source ledger, waking brief, parent message, or source transcript is present at held-out evaluation. | Proposed recurrent per-life parametric system. |
| `DERANGED_PERIODIC` | Exact native row roles, statuses, response-token multiset, lengths, rehearsal, and update schedule, but action/outcome bindings and relation endpoints are permuted within type/age/root with no fixed points. Every target remains schema-legal. | Authentic action--outcome and endpoint binding, rather than syntax/action priors. |
| `NATIVE_ADAPTER_OFF` | The exact `NATIVE_PERIODIC` checkpoint and evaluation state, re-served fresh with the adapter absent. No retraining. | Localizes behavior to parametric state rather than context, ledger, cache, or harness. |

The outcome permutation must move complete normalized action--outcome bindings;
the current `shuffle_corpus.py` tail-only shuffle is expressly invalid because
it leaves programs and actions in their original training heads.

### Strong-baseline minimums

`TEXT_ACTIVE` must be able to preserve all raw history, revise its own compact
records, follow stored links, and fall back to raw search. It receives the same
acting calls and returned-memory token budget as the LoRA reader. Report its
total stored bytes/tokens and index work; do not constrain storage to make
weights win.

`RAW_PERIODIC` trains through the exact native template and response mask. A
bare action string or all-token trajectory LM is not an acceptable baseline.

`LEAFE_FINAL` must actually perform reflection, rollback, improved-branch
generation, and behavior rehearsal. Relabeling the native corpus as LEAFE is
not acceptable. Its published full-parameter SFT is not feasible per life in
this confirmation, so the paper must say that the data-generation/objective is
reproduced under the common rank-8 parameter budget.

All deterministic or low-cost baselines disclose their lower cost. Matching
scientific budget does not require burning dummy wall time, but every method
must receive the same usable generated-token and action opportunity budget.

## Common randomness and exact budget matching

### Randomization keys

For each `super_life_root`, derive independent, domain-separated keys for:

- component-world generation and twin side;
- source-actor sampling;
- sleep opportunity and replay selection;
- writer/reflector generation;
- LoRA initialization and minibatch order; and
- each evaluation item and stochastic replicate.

Equivalent calls across arms use the same sampling key and candidate order.
Greedy primary decoding is permitted, but the keys must still be logged and a
small common-random stochastic robustness panel must be predeclared. Technical
seeds, target tasks, sides, writer samples, and checkpoints are repeated
measurements nested within the root.

### Generated tokens

Each arm receives the same exact number of usable generated response tokens in
source, update, and evaluation phases separately. A method that stops early may
spend the remainder on another legal refinement/reflection opportunity of the
same phase; the last response is capped to the remaining token count. Tokens
after the exact cap are neither generated nor stored. Do not count fixed
`max_tokens` as if it were consumed output. Input tokens, cache hits, calls,
latency, and FLOPs are also reported, but generated response tokens are the
primary common budget.

### Supervised tokens and optimizer exposure

All trained main cells share:

- identical rank/target modules/initialization bytes where shapes permit;
- identical optimizer/update count, scheduler, precision, and rehearsal share;
- equal masked-input token counts through target-blind neutral padding; and
- equal **effective** supervised native-response tokens.

Full response envelopes and EOS remain labeled. Exact effective-token equality
is achieved with prebound per-row scalar loss weights whose weighted labeled-
token sum equals the arm budget; never truncate or partially relabel a native
response to hit the budget. Report unique rows/tokens and weighted exposure
separately so duplication cannot masquerade as epistemic support.

### Action and inference budgets

At every target, every arm gets the same number of structured model operations,
memory reads, environment actions, generated response tokens, and wall-clock
ceiling. Text retrieval is one public operation just as LoRA recognition is.
A missing/malformed call consumes budget. Primary task value is reported both
under equal generated tokens and under a fixed number of executed actions so a
“more actions” artifact cannot explain the result.

## Target-blind split and leakage firewall

Before any model output, freeze and hash the generic architecture, world
version, root-selection algorithm, context measurement, checkpoint rule,
source-eligibility rule, source action schema, DREAM grammar, admission law,
compiler, baselines, derangement, statistics, kill rules, and maximum claim.

Use only fresh master roots. Group by latent tuple, passive fingerprint,
renderer, and twin pair before assigning development, pilot, and confirmation.
Every seed/root/world/task/output previously present in Fable, nursery,
Semantic-World/G-series development artifacts, current conversations, or any
prompt-tuning run enters a contamination denylist. Whole groups, not individual
questions, are assigned to partitions.

Within a confirmation root, source events and pre-goal semantic probes seal
before target goals are revealed. Target identities, target message bytes,
answers, hidden proof paths, decisive-cut identities, and scores are forbidden
to the source actor, parent, DREAM, textual updater, compiler, heat selector,
trainer, and candidate builder. Candidate domains may contain only the public
ontology available before target reveal; they cannot be a target-specific
answer shortlist.

Two independent no-model sealers must agree on root membership, twin equality,
content/action hashes, chronology, context cuts, exclusions, and target counts.
The scorer executes only after all raw responses commit. Any target byte that
reaches a training input invalidates the complete root, not just one row.

## Independent unit, sample, and analysis

The independent unit is one **paired `super_life_root`**, including both latent
twin sides, all component eras, its source-actor realization, per-cell writer
and training realizations, and target panel. A side, component world, task,
checkpoint, writer sample, decoding seed, or optimizer step is not an
independent observation.

Use:

- development roots for code, prompts, thresholds, and heat;
- a disjoint four-root locked spending pilot, excluded from confirmation; and
- exactly 20 fresh confirmation roots.

The count may not be reduced after a bad result. There is no outcome-driven
sample extension. If the measured canary cost makes 20 roots infeasible by the
predeclared deadline, stop before target enumeration rather than relabeling a
small calibration as confirmation.

For each root, first average target outcomes within capability/age stratum and
require both twins when a target is pair-scored. Then compute paired arm
contrasts. Use a cluster bootstrap or randomization interval that resamples
only whole roots. Report all 20 root values, mean, median, range, and 95%
interval. A hierarchical gate tests C2, then C3, then C4, then C5; a failed
earlier rung prevents a later mechanism diagnostic from restoring the broad
claim. Within a rung, use a simultaneous max-contrast interval rather than
separate uncorrected task-level p-values.

The registered practical value margin is `0.05` on the normalized `[0,1]`
target score unless development-only oracle/no-memory variance establishes a
larger margin before confirmation. A margin may never shrink after pilot or
target inspection.

## Endpoints and exact claim gates

### Primary lifetime score

At every checkpoint, evaluate fresh, isolated target panels:

- **forward/new:** fresh-handle goals supported by the newly added eras;
- **backward/old:** the same sealed early-era goals re-evaluated without their
  source history;
- **mixed-age joint:** one old and one recent target must both succeed under one
  shared operation budget; this measures coexistence, not a new causal edge;
- **twin-pair:** both counterfactual sides must produce their side-correct
  action; and
- **proposal/routing guards:** free native compliance and typed-forced action
  value are scored separately.

The primary `Y[r,a,k]` is the equal-weight mean of forward, backward, and
twin-pair normalized action value within root; mixed-age joint success is a
required secondary guard. `AUC[r,a]` is trapezoidal area against `log2` public
source tokens over the four frozen cuts. No checkpoint is a replicate.

### C2 gate

Require:

1. the 95% root-bootstrap lower bound for
   `AUC(NATIVE_PERIODIC) - AUC(FROZEN)` is above zero;
2. the mean contrast is at least `0.05`; and
3. free native compliance is at least `0.95` and typed-forced proposal value is
   not more than `0.05` below frozen or adapter-off.

This is prospective periodic-write efficacy under common experience.

### C3 gate

At `6C`, require simultaneous 95% lower bounds above zero for
`NATIVE_PERIODIC` against each of `TEXT_ACTIVE`, `RAW_PERIODIC`, and
`LEAFE_FINAL`, and require at least `0.05` mean advantage over the strongest
of their root-level means. Also report AUC contrasts, but do not let weak early
LEAFE checkpoints (where it intentionally has no adapter) manufacture the
terminal claim.

The maximum comparison is “better under the registered operation, generation,
and rank-8 training budget,” not universal superiority to retrieval or LEAFE.

### C4 gate

Require all of:

1. a positive simultaneous lower bound on the change in native advantage over
   the strongest comparator from `1.5C` to `6C`;
2. terminal backward value no more than `0.05` below the native arm's earlier
   old-target peak;
3. positive new-era value at every post-native cut; and
4. mixed-age joint success at `6C` above the registered no-memory floor.

This establishes finite growth plus retention. Do not say a baseline
“saturated” unless a separately registered equivalence interval places both of
its last two slopes inside a practical plateau band. With 20 roots, the safe
default wording is that native advantage **grew across 0.75C--6C**, not that
other methods reached an asymptotic wall.

### C5: connected and compressed knowledge without expected-thought scoring

Yes, C5 can be measured without judging whether the model wrote the theory the
researchers hoped to see. The experiment must use behavioral and intervention
criteria only.

Before every target reveal, seal these quantities from model-authored typed
records:

- prospective public-outcome precision and coverage of admitted edges;
- size and depth of the cited public dependency graph;
- fixed-query recognition fidelity for admitted links under a target-blind
  candidate domain;
- canonical tokenizer code length of the admitted semantic records; and
- number of local reads needed to execute the public path.

No natural-language rationale, rubric score, semantic similarity to a reference
thought, or expected chain-of-thought enters an endpoint. Hidden structure may
score a committed relation after the fact; it cannot select or repair it.

At the terminal cut, derive three independently trained, dose-matched adapters
from the same native source:

| Carrier cell | Contents | Purpose |
|---|---|---|
| `COMPACT_LINKED` | Full admitted atoms, cross-event links, successful decision paths, and only shortcuts that met the two-independent-use rule. This is the terminal `NATIVE_PERIODIC` adapter. | Proposed carrier. |
| `EXPANDED_LINKED` | Same supported information and decisions, but every shortcut is replaced by its complete constituent local-edge path. | Rate/read-depth comparator. |
| `ATOMS_ONLY` | Direct witnessed atoms plus single-event decision rows; all cross-event links, shortcuts, and multi-parent decision targets are replaced by token/dose-matched atom rehearsal. | Connected-knowledge ablation. |

The C5 joint gate requires:

1. admitted link fidelity is above its registered floor at the pre-goal seal,
   before the corresponding action is generated;
2. `COMPACT_LINKED - ATOMS_ONLY` has a positive 95% lower bound and mean at
   least `0.05` on multi-edge target value;
3. authentic `COMPACT_LINKED` beats `DERANGED_PERIODIC`, and adapter-off loses
   at least half of the authentic gain over frozen;
4. removing the target's scorer-hidden necessary public bridge from the
   available recognition carrier redirects or destroys the target action at
   the registered rate; the cut is fixed before response generation and never
   shown to a model;
5. at an unrestricted registered read budget, `COMPACT_LINKED` is non-inferior
   to `EXPANDED_LINKED` within `0.05`, while using at most half as many local
   reads and no more than half its canonical semantic-code tokens; and
6. at the tight read budget, `COMPACT_LINKED` exceeds `EXPANDED_LINKED`.

Additionally require the compact semantic code to be no more than 35% of the
raw public-ledger tokenizer length at `3C` and `6C`, with false-memory rate and
backward value inside their registered bounds. This supports **behavior-
preserving semantic rate reduction**. It does not show that the adapter file is
smaller than the raw ledger, does not reveal the transform inside its weights,
and does not license “optimal compression.” LoRA rank or fixed byte size alone
is never compression evidence.

If connectedness passes but the rate/read gate fails, use “connected compiled
experience,” not “compressed knowledge.” If only the adapter-on/off contrast
passes, C5 fails; weight perturbation is not a semantic mechanism.

### Resource and failure endpoints

At root, cut, and arm level report:

- accepted/provisional/contradicted records by kind and age;
- source, writer, supervised, prompt, retrieved, and generated tokens;
- model calls, operations, reads, actions, invalid calls, and no-action values;
- unique/effective training rows, optimizer steps, loss, nonfinite batches,
  adapter bytes/hash, and fit time;
- raw/text/semantic/index bytes and semantic code length;
- latency, occupied GPU time, wall time, crashes, retries, and missing cells;
- action histograms, first-improvement latency, false-memory use, and negative
  transfer by difficulty/age.

Failed, malformed, timed-out, or unserved assigned cells remain in the root
score at their predeclared failure value. A fresh retry is a new technical
identity and cannot replace a scientific cell.

## C6 final bridge: one parent, one child, then a fresh gym

### Architecture and causal question

Within each independent replication, one fixed parent teaches one child one
process correction at a time through assigned practice tasks. There are no
classrooms, teacher ensembles, peer agents, voting, cross-dyad communication,
or population-level learning mechanism. Multiple dyads are statistical
replications of the same isolated one-parent/one-child intervention, never a
mechanism by which children or parents share learning.

The parenting cycle is:

1. child acts and thinks through a target-blind controlled task using public
   typed operations;
2. parent sees only the child's public trace and public world outcomes;
3. parent names one belief-to-test or thought-to-action process mistake and
   proposes credit assignment, without an answer, action argument, hidden
   score, or compiler content;
4. child restates the correction in a closed process object;
5. from one identical pre-apply state, a no-correction branch and corrected
   branch act on the same transfer task under common randomness;
6. the public world, not the parent, admits the lesson only if the corrected
   branch improves by the registered margin without changing to parent-supplied
   action content;
7. accepted native response rows are written through the same rank-8 writer
   with parent, restatement, neutral cue, and state-only scaffold fading; and
8. the next cycle starts with the resulting child adapter.

Use a small fixed number of cycles and one predeclared process vocabulary:
prediction before action, surprise-to-belief revision, choosing a
discriminating cheap test, evidence scope, and routing a chosen thought into
one executable action. The parent may choose among those process corrections
from the trace; it may not invent domain content. This is taught procedural
transport, not novel discovery by the child.

The unparented child receives byte-identical practice tasks, public outcomes,
calls, generated-token budget, rehearsal, and effective training exposure.
Parent-role slots contain target-blind, role- and token-length-matched sham
messages; during practice it still performs its ordinary unparented
Think--Dream--Sleep writes. The resulting matched unparented checkpoint is the
regular agent at deployment.

After parenting, destroy the parent context, correction messages, restatements,
nursery ledger, textual memory, notes, and KV/prefix caches. Retain only the
permitted child adapter and frozen base. The fresh gym is CompilerGym, using a
new neutral bootstrap that contains no pass names or example pass sequence and
a canonical train/probe split disjoint from every prior Fable artifact.

### Headline pair and necessary diagnostics

The visible headline is exactly two deployed agents:

- `PARENTED_CONTINUAL`: resulting child, then the same periodic native
  Think--Dream--Sleep loop in CompilerGym;
- `UNPARENTED_FROZEN`: regular agent from matched unparented practice, with no
  CompilerGym weight writes.

Add only the two diagnostics required to identify parenting by online-write
interaction:

- `PARENTED_FROZEN`: same parented child adapter, no CompilerGym writes;
- `UNPARENTED_CONTINUAL`: same regular checkpoint, with the identical online
  Think--Dream--Sleep loop.

This 2x2 distinguishes a static taught prior from an improvement in later
learning. Use 12 independent dyad roots, with exactly one fixed parent and one
child in each root, the same frozen parent engine and prompt across roots,
common paired practice/gym assignments, common sampling keys, and root-level
inference. Each dyad is sealed from every other dyad. These are replications of
a one-parent/one-child intervention, not a classroom, cohort, or population
learning claim.

Use only unique CompilerGym training programs and probe at 0, 16, 32, and 48
programs (or the equivalent exact generated-token cuts frozen after the runtime
canary). Never repeat the 67-program deck for hundreds of nominal episodes.
Each probe has an isolated ledger and clean reset.

Primary C6 endpoints are held-out equal-token value AUC and early learning
slope. Secondary endpoints are improvement per executed action/generated
token, surprise-to-discriminating-experiment latency, time to first
improvement, fixed-action value, typed compliance, and proposal diversity.

The meta-learning estimand is the root-level interaction:

```text
[AUC(PARENTED_CONTINUAL) - AUC(PARENTED_FROZEN)]
- [AUC(UNPARENTED_CONTINUAL) - AUC(UNPARENTED_FROZEN)].
```

C6 requires its 95% root-level lower bound above zero, a mean interaction of at
least `0.03`, and non-inferior typed compliance/proposal quality. A higher
parented score at gym entry with parallel later slopes is useful static process
transfer, not learned learning efficiency. A parented-continuous win without a
positive interaction remains descriptive and moves to the appendix. Leakage,
unmatched starting information, compiler content in parenting, or parent
presence at deployment invalidates C6 entirely.

## Current plumbing is insufficient

No current `organism_v6` run can execute or support this protocol without a
new ratified implementation. The material gaps are specific:

1. `model_backend.py` ignores the caller's `seed`, returns only decoded text,
   exposes no exact native tool envelope or token IDs, and supports one adapter
   choice per engine instance. It cannot supply common-random paired native
   actions or efficient multi-adapter evaluation.
2. `loop.py` and `batch_loop.py` parse free-text line markers, permit multiple
   operations in one completion, and let assistant prose become an action.
   Thought text and prompts are truncated before logging; exact response bytes,
   schemas, IDs, parser/dispatch receipts, and state hashes are absent.
3. `state.py` uses character budgets and silently slices tail/recalled text.
   It is not tokenizer-exact and its wall-clock fields make otherwise matched
   contexts differ.
4. `ledger.py` is an ordinary mutable JSONL append with no hash chain, fsync,
   source ancestry, visibility type, or isolation guard. Keyword recall can
   cross tasks through a shared ledger.
5. `sleep_compile.py` admits wins and model-written principles without later
   prospective support. Its `since_tick_by_ep` is unused; cumulative selection
   can repeatedly re-admit old events. `compile_native` accepts substring-level
   `had_note`, deduplicates on the first 120 answer characters, and emits
   generic QA text rather than an exact native structured response.
6. `train_adapter_v21.py` encodes a user/assistant text pair, not the actual
   offered-tool response envelope. It may truncate response/EOS, skips
   nonfinite batches without failing, has no deterministic seed or per-row
   mask receipt, and reports attended rather than supervised tokens. It cannot
   prove cross-arm target-ID equality or effective-token matching.
7. `run_life_v2.py` has only A/B arms. B alone receives the waking brief,
   generations are unseeded, probe programs share a ledger, the 67-program
   source deck repeats 15--16 times, loaded source/model/tokenizer hashes are
   absent, and adapter-on/off panels are not common-random.
8. `bootstrap.txt` contains the exact four-pass opening that dominated Fable's
   early apparent gain. It is unusable for discovery or C6 and must be replaced
   by target-neutral bytes.
9. `shuffle_corpus.py` permutes outcome tails while leaving program and action
   strings fixed. It does not implement an action--outcome or relation-endpoint
   derangement.
10. `nursery_dialogue.py` compares scores on different tasks, logs parent and
    restatement rows even when `admitted` is false, lacks a matched sham and
    wrong-child/adapter-off contract, uses unseeded free text, and counts a
    format canary without enforcing it. Its parent sees a clipped tail, not an
    exact public provenance trace.
11. `rulegame.py` samples from ten fixed hand-written rules by episode string.
    It is a useful smoke toy, not a target-blind parenting task generator or a
    C6 efficacy benchmark.
12. `lands/v03r.py` is CPU acceptance infrastructure, not an agent loop. It
    supplies the right causal fixture but still needs the thin super-life,
    typed-action, chronological-goal, common-deck, and target-sealing wrapper.
13. The private typed-action provenance canary is deliberately a deterministic
    stub and pure mock. It is a schema precedent only; it grants no live model,
    real tool, recurrent state, or learning evidence.
14. No current code implements the strong active textual updater, the
    LEAFE-style final-batch branch collector, root-clustered analysis, semantic
    rate/distortion panel, or parenting-by-online-learning interaction.

The Fable long run cannot be recycled as a confirmation source: its generation
was unseeded, B had a different context policy, loaded-source ancestry is
unknown, exact prompts are missing, and the supplied bootstrap already
contained the dominant learned action.

## CPU, writer, and promotion gates

Before target enumeration or scientific GPU calls, require:

### World/relay gates

- deterministic replay and hash equality for every public byte;
- twin target-visible equality with distinct correct actions;
- public-edge oracle at least `0.90` twin-pair value in every retained root;
- exact no-life adaptive and target/passive/identifier/action-frequency
  controls at most `0.35`;
- deranged and necessary-bridge cuts remove at least half of oracle gain;
- every target needs at least one edge older than `C`, one recent edge, and the
  registered multi-edge dependency depth;
- all four checkpoint cuts contain new causal information and no filler; and
- source/root eligibility is independent of target result.

### Native interface/writer gates

- exact response-envelope round trip and one-operation parsing;
- prompt-before-dispatch persistence and loaded-source/model/tokenizer hashes;
- response IDs, masks, EOS, padding, rehearsal, target-token weights, update
  order, and adapter initialization equality across causal cells;
- zero empty/truncated/zero-label rows and fail-closed nonfinite behavior;
- common-seed native action equality in repeated canaries;
- selected rank-8 heat absorbs a neutral native response, free typed-call
  compliance remains at least `0.95`, and typed-forced/generic sentinels lose
  no more than `0.05`; and
- one adapter fit and one full evaluation panel fit the registered wall-time
  estimate before scaling.

### Development and spending gates

On development only, known-good public text plus the common recurrent actor
must reach at least `0.80` target value. The active text implementation must
retrieve every oracle-inserted local record in its interface test. A native
same-semantics LoRA canary must reach at least `0.85` fixed-query link fidelity
and stay within `0.10` of text under the common reader.

Then run the disjoint four-root spending pilot once. Promote only if native
minus frozen has mean at least `0.05` and is positive in at least three roots,
typed compliance/proposal guards pass, authentic exceeds deranged
directionally, and no provenance/resource cell is invalid. Pilot outcomes may
decide whether to spend; they may not change prompts, margins, writer heat,
worlds, arms, or analysis before confirmation.

## Resource envelope

These are planning estimates, not authorization. Replace them with one measured
rank-8 native fit, writer batch, and multi-adapter evaluation canary before the
run manifest is ratified.

For 20 main roots, two twin sides, and four cuts:

- `RAW_PERIODIC`, `NATIVE_PERIODIC`, and `DERANGED_PERIODIC` require 480
  checkpoint fits;
- terminal `LEAFE_FINAL`, `EXPANDED_LINKED`, and `ATOMS_ONLY` require 120 more;
- `FROZEN`, `TEXT_ACTIVE`, and adapter-off require no additional fit;
- total main adapter fits: 600.

A rank-8 adapter should be roughly one eighth of the existing 154 MB rank-64
artifact before metadata, about 20 MB, so terminal/checkpoint weights are on
the order of 12 GB. Preserve at least 50 GB for prompts, ledgers, corpora,
optimizer receipts, and immutable manifests.

Using the repository's measured 7B range as a deliberately broad anchor:

| Work | Estimated occupied GPU-hours |
|---|---:|
| 600 small rank-8 fits, 3--10 minutes each | 30--100 |
| source/DREAM/text/LEAFE generation, batched across roots | 15--35 |
| all main target/read/action panels and robustness samples | 20--45 |
| C6 parenting, 96 additional fits, and four-arm fresh-gym curves | 20--50 |
| failure/setup/review slack, approximately 25% | 20--55 |
| **Total planning envelope** | **105--285 GPU-hours** |

With five actually available 48 GB-class GPUs, ideal occupied time is roughly
21--57 hours; process startup, serial sleep boundaries, audits, and failed
canaries make **three to five calendar days** the realistic floor. Do not assume
the previously described H100/GH200 fleet without a fresh inventory. Use one
resident base engine with independently addressed LoRA requests for batched
evaluation; loading a new base engine for every adapter makes the deadline
implausible.

The hard resource gate is a measured per-fit median no greater than 10 minutes,
an end-to-end root-side wall time consistent with completion by September 15,
and enough verified GPU-hours to finish all 20 roots without denominator
reduction. If any fails, kill the broad run before confirmation rather than
dropping baselines or roots.

## September 6--16 execution schedule

This schedule assumes immediate exact ratification after the mandatory
deliberation. It authorizes nothing by itself.

### September 6--7: freeze the experiment

- adjudicate this benchmark/architecture/visibility/claim delta;
- freeze C2--C6 wording, seven arms, C5 terminal panel, unit, margins, and
  target-blind selection algorithms;
- freeze a neutral bootstrap and one-parent process-only contract;
- inventory GPUs and pin model/tokenizer/dependency/source revisions.

**Kill:** no exactly ratified headline protocol by end of September 7 leaves
too little time for the ambitious confirmation.

### September 7--9: CPU spine and native writer

- build only the v0.3-R super-life wrapper and typed public operation/ledger;
- implement both strong baselines, derangement, rate/cut reducer, target
  sealers, and root-level report before any confirmation identity is exposed;
- pass world/twin/shortcut/source/provenance/token/statistics fixtures;
- run the treatment-neutral rank-8 heat canary and one native process-
  correction floor.

**Kill:** no valid native writer, text ceiling, four context cuts, or exact
budget accounting by September 9 means no C2--C5 run.

### September 9--10: development only

- run development roots end to end;
- repair only predeclared implementation defects, rerun all affected fixtures,
  and refreeze once;
- time one complete root side, all fits, and all evaluation panels;
- obtain fresh independent science/runtime review and author-side response.

**Kill:** writer/interface non-erasure, LoRA link-read floor, strong-text
retrieval, or measured resource gate failure stops promotion.

### September 10--11: locked spending pilot

- seal four disjoint pilot roots;
- execute the complete seven-arm and terminal mechanism surface once;
- apply only the frozen spending rule; never tune from these outcomes.

**Kill:** no prospective native-over-frozen direction, no authentic-over-
deranged direction, or any leakage/twin/root invalidity stops the broad run.

### September 11--14: main confirmation and parenting source in parallel

- fan the 20 confirmation roots across four GPUs;
- reserve one GPU for the target-blind parent/unparented source cycles and
  neutral CompilerGym baseline canaries;
- pull and hash complete root artifacts incrementally;
- no prompt, arm, margin, rank, target, or stop-rule change after first
  confirmation dispatch.

### September 14--15: terminal C5 and C6 bridge

- finish the LEAFE final fits and compact/expanded/atoms carrier panel;
- run sealed adapter-off/bridge-cut/twin panels;
- deploy the parented-continual child and regular frozen agent, with the
  parented-frozen and unparented-continual diagnostics, to the fresh
  CompilerGym sequence;
- reproduce every number from one immutable result manifest.

If GPU availability tightens, C6 yields first. Do not sacrifice a C2--C5 arm,
root, or mechanism gate for parenting.

### September 16: hard scientific gate

- close all registered missing/failed cells at their frozen failure values;
- run root-level intervals, claim ladder, leakage and resource audits;
- freeze the lifetime, mechanism, and optional parenting figures.

**Kill:** C2--C5 must all be prospectively positive with no unresolved
source/seed/routing/leakage/twin/baseline confound by end of September 16. If
not, the broad ICLR abstract is false and must not be submitted as a promised
flywheel. If C2--C5 pass but C6 misses, submit the per-life experiential-
consolidation paper and remove the meta-intelligence clause.

## Maximum permitted claims

If and only if C2--C5 pass exactly as registered, the maximum core statement is:

> In a prespecified finite population of paired Counterfactual Confluence
> super-lives, a frozen 7B language agent repeatedly converted a shared,
> prospectively recorded stream of its own public actions and outcomes into a
> fixed-rank personal adapter. Under matched operation, generation, and
> training budgets, native periodic consolidation improved post-context
> held-out multi-edge action across 0.75--6 usable context lengths, outperformed
> a frozen loop, strong active textual memory, raw periodic response
> distillation, and matched final-batch reflective recovery distillation, and
> retained earlier-era competence. The gain required authentic bindings and a
> model-authored, public-outcome-admitted connected carrier.

Only if the full C5 rate/read gate passes may add:

> The connected carrier preserved action value while reducing canonical
> semantic code length and read depth relative to its expanded public paths.

This means semantic rate reduction, not that the LoRA file is a smaller byte
encoding than the ledger and not that an internal human-readable graph has
been recovered from weights.

Only if the C6 interaction passes may add:

> Within each isolated dyad, a fixed process-only parent taught one child a
> parent-absent disposition that increased the child's subsequent learning
> rate in a disjoint CompilerGym deployment under the same online architecture.

No result licenses open-ended continual self-improvement, general
meta-intelligence, first learning from experience, first reflection
internalization, universal memory superiority, autonomous discovery of the
benchmark's laws, hidden chain-of-thought claims, or a population/classroom
parenting mechanism.

## Evidence this decision absorbs

- `research_notes/ICLR_2027_READINESS_20260906.md`: C2--C6 ladder and the
  September 9/12/16 gates.
- `research_notes/abstract_experience_models_v2_positioning.md`: per-life
  parametric-learning boundary and required textual/batch comparisons.
- `research_loop/advisory/20260906_fable_v61_longrun_independent_audit_v1.md`:
  unseeded early transport, supplied four-pass action, B2 proposal/routing
  separation, invalid tail-only shuffle, and missing source ancestry.
- `research_loop/advisory/20260906_process_correction_native_writer_microassay_v0_design.md`
  and its main review: exact native response targets, scaffold fading,
  treatment-neutral heat, conditional selection funnel, and parent-absent
  routing/proposal separation.
- `research_notes/related_work/20260906_experience_learning_neighbors.md`:
  LEAFE, Early Experience, MemoPilot, Evo-Memory, and continual-memory baseline
  obligations.
- `alchemy/v2_out/mini_ledger.md`, `research_notes/33_semantic_world_gpu_constraints.md`,
  and `research_notes/39_v02_branch_depth_results.md`: one-hop recognition,
  protocol/substrate 2x2, coverage bottleneck, public blind verification,
  v0 D3 shortcut correction, and the 32B exhaustive controller ceiling.
- `research_notes/50_rml_paper_design_adjudication.md` and
  `research_notes/52_public_pathway_consolidation_mechanism.md`: root-level
  statistics, public epistemic authority, common-experience separation,
  connected carrier interventions, and precise compression boundary.
