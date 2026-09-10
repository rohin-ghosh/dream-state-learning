# 49 — RML paper architecture and next experiment

**Date:** 2026-09-03

**Status:** adjudicated research synthesis, not implementation or GPU
authorization. It reconciles the independent benchmark, learning-architecture,
prior-art, Stage-A, reuse, and cross-critique audits dated 2026-09-03. Exact
runtime bytes still require the repository's architecture-intake path.

## Decision

The paper direction remains viable, but the result must be built as an evidence
ladder rather than one giant organism run.

The primary benchmark family is **Rendered Maintenance Lifetimes (RML)**. The
existing `rml_d0` package is retained as a deterministic one-pack micro-fixture
and CPU regression base. It is not yet a model benchmark or an independent
world-life sample. The immediate model experiment is a small supplied-gold
text-memory action gate on that fixture. Learned DREAM text follows only if the
agent can use the supplied memory. LoRA follows only if learned text changes
action. Lifetime scaling and randomized on-policy evidence acquisition follow
only after the fixed-deck mechanism works.

This ordering tests the causal chain from the outcome backward:

```text
G1: known-good local memory -> recurrent reads -> executed action
G2: public action/outcome history -> DREAM proposals -> SLEEP text -> G1 path
G3: same frozen G2 corpus -> LoRA recognition -> G1 path
G4: growing independent lives/cuts -> acquisition + retention + cross-era action
G5: randomized memory -> information action -> new evidence -> sleep -> later action
```

Failure at a rung stops spending on later rungs. A negative is localized rather
than repaired by adding intelligence downstream.

## Paper claim, if the complete ladder passes

The defensible target is:

> Across prospectively sealed causal world-lives, a frozen language agent used
> target-blind, provenance-conditioned consolidation of its own public
> action--outcome history to improve held-out multi-step action. The same
> semantic memory retained action value when transported into isolated
> per-life LoRA weights, and the system continued to acquire, retain, and
> combine useful causal knowledge across post-context lifetimes after named
> external-memory baselines were measured to plateau.

The final flywheel clause—memory improves evidence acquisition, which improves
later memory and action—requires G5. It cannot be inferred from a scripted life.
The words `compression`, `saturation`, `continued`, and `self-learning` each
remain behind their separate gates below.

## Organism: one resolver, two regimes, one compiler

```text
                         immutable public ledger
                                  |
                 +----------------+----------------+
                 |                                 |
          THINK (goal driven)               DREAM (replay driven)
        narrow DFS/backtracking              broad local expansion
        read -> path -> action              propose edge/schema/test
                 |                                 |
                 +---------- typed traces --------+
                                  |
                    SLEEP (deterministic compiler)
          status -> dedup -> multi-view rows -> old/new replay mix
                         |                    |
                   explicit text        per-life LoRA
                         +---------+----------+
                                   |
                          one-hop memory read
                                   |
                         clean-base composition
```

The epistemic authority is the append-only public ledger plus explicit semantic
snapshot, not the LoRA. DREAM proposes target-independent local relations or
prospective schemas; it never certifies itself. Support comes only from later
ordinary public outcomes under rules frozen before the proposal. SLEEP invents
no facts: it admits, types, deduplicates, balances old/new items, and renders
fixed forward/reverse/partial/QA views. The LoRA is a lossy one-hop recognition
transport. The explicit graph retains provenance and supports causal audit.

THINK and DREAM share the operation family—query, follow/update, backtrack,
predict, act/propose, defer/stop—but not their objective or permissions. THINK
performs goal-conditioned depth. DREAM spends breadth on locally testable
connections. The LoRA response surface may make relevant neighbors easy to
access, but multi-hop reasoning is externalized into the recurrent token loop.
This is the operational version of breadth-first consolidation plus depth-first
goal resolution; it does not require DREAM to enumerate a literal global graph.

Paper 1 keeps the resolver prompted and frozen. Its successful and failed
operation trajectories are saved for later cross-life LOOP-adapter training.
The lifetime MEMORY adapter and shared LOOP adapter are distinct; no per-life
facts enter the shared controller during evaluation.

## What is already established

1. The atomic substrate can work. In the L0/G2f family, coined names, one-hop
   facts, sufficient touches, recognition reads, and clean-base composition
   transported useful structure through LoRA; the strongest oracle-statement
   condition reached about 0.95.
2. At small memory, text and LoRA can tie when both use the same recognition
   protocol. This means the reader/resolver supplies much of the intelligence,
   and LoRA's value must be tested beyond the honest context budget.
3. V5 is a valid write-quality negative: extra proposal samples increased
   candidates while bad selection poisoned the retained corpus and downstream
   action. Proposal rate without a sufficiently strong evidence rule is not
   useful dreaming.
4. `rml_d0` now passes 16 local tests and its Stage-A CPU report. It contains a
   996-event / 285-mapping source schedule, exact nine-action targets, target-
   byte twins whose correct actions differ, J deletion witnesses, and a P
   atoms-only ceiling. These are subject-package self-consistency fixtures,
   not independent model evidence.
5. The generic trace/checkpoint machinery is extensively tested (103 selected
   plain tests pass), but its scientific adapters are v03-specific and its
   thinker does not yet execute RML environment actions.

## Immediate experiment: RML-G1 fast falsifier

### Question

Can the frozen 32B resolver use target-independent supplied-gold local memory,
through adaptive one-hop reads, to execute one connected J target and one
prospective P target in both members of their counterfactual twin pairs?

This is a model-facing construct/integration gate. The two target pairs are
nested inside the same deterministic micro-fixture and are **not** independent
world replications. A pass licenses learned-memory work; it is not a paper
result.

### Conditions

| ID | Memory and access | Purpose |
|---|---|---|
| `NONE_REC` | Four call-matched `NOT_FOUND` reads | Frozen agent/prior floor |
| `GOLD_OPEN` | Gold connected rows; four keys fixed before any return | Tests fixed query dumping |
| `GOLD_REC` | Same rows; each return may determine the next key | Positive recurrent-use gate |
| `ATOMS_REC` | P local witnessed atoms, prospective schema removed | Tests connected/schema necessity |
| `CUT_REC` | Fresh rerun with all decisive rows cited by `GOLD_REC` masked | Causal-use intervention |
| `TWIN_REC` | Fresh rerun with twin memory behind unchanged target bytes | Binding/redirection intervention |
| `GOLD_TYPED` | Optional typed-query diagnostic | Interface ceiling only |

Each trajectory has at most four memory reads followed/interleaved with the
nine necessary public environment actions: **13 resolver calls total**. A model
call emits one operation. There are no hidden planning or retry calls. Invalid,
multi-operation, illegal, truncated, deferred, or over-budget trajectories
score zero and are not replaced.

The fast gate is 18 trajectories / 234 calls (286 with the typed diagnostic):
core three conditions on four sides, `ATOMS_REC` on the two P sides, and cut/
twin interventions on the canonical H side of J and P. The stronger four-pair
DEV is 44 trajectories / 572 calls (676 with typed diagnostics). Batch parallel
execution may reduce wall time but cannot change within-trajectory ordering.

### Gate

- `GOLD_REC >= .85` action success and `>= .80` valid cited-path rate.
- `NONE_REC <= .35`.
- `GOLD_OPEN <= .45` and `ATOMS_REC <= .35` on P.
- At least 80% of credited `GOLD_REC` successes lose validity under complete
  cited cuts and redirect in the predicted twin-memory direction.
- Unsupported decisive release, hidden-field exposure, state leakage, corpus
  mutation, retry, and cross-life residue must all equal zero.

With only two nested target pairs, thresholds are engineering gates rather than
population estimates. If typed gold works but generic recurrence fails, repair
the controller before testing DREAM. If no-memory/open/atoms work, the task
lacks constructive headroom. If even typed gold fails, stop RML model work.

## G2: learned text before weights

Only after G1 passes, generate a new multi-root development panel and replace
gold rows with target-blind, experience-derived text. Hold the public lifetime,
writer model/calls, resolver, and budgets fixed. Compare:

- deterministic witnessed-atom compilation;
- raw DREAM proposals without outcome admission;
- blind model self-check as a diagnostic;
- precommitted prediction plus later public-outcome admission;
- matched reflection/lesson text;
- raw episodic RAG;
- uncrippled explicit witnessed graph;
- generator-aware program induction;
- the full admitted compiled text snapshot.

The required DREAM contribution is primarily higher-order: local witnessed
atoms may be mechanically extractable, while a P schema must be proposed before
the withheld outcome and later supported. J tests whether the resolver composes
separate old and recent local memories. DREAM is credited only when its
proposal/admission frontier improves prospective precision/coverage and later
action over deterministic witnessed atoms, raw proposals, and matched
reflection.

G2 passes when compiled text recovers at least 70% of the gold-memory gain,
lies within 0.10 of the stronger explicit graph/program reference, beats raw
RAG/reflection directionally in both DEV roots, and loses its credited behavior
under binding/twin/cut interventions. The exact program learner is a ceiling-
like adversarial reference and is allowed to win; demanding that a learned
memory beat an exact generator-aware solver in a two-root DEV gate would be an
invalid stopping rule.

## G3: same-corpus LoRA transport

Freeze the admitted G2 semantic snapshot before any LoRA target is rendered.
Train freshly reset per-life adapters from the clean base. Compare identical
semantics as text, recognition-assisted LoRA, unaided generative LoRA, direct-
QA/raw-event LoRA, candidate-only clean base, binding shuffle, wrong-life, and
whole-twin adapter swap.

Proceed only if fixed-query LoRA read fidelity is at least 0.90, LoRA action is
within 0.10 of identical-corpus text, authentic LoRA beats direct-QA/raw LoRA
directionally, and binding/twin swaps change behavior in the registered
direction. A text win with failed LoRA is a valid compiler/external-memory
result. A small-memory tie does not establish a LoRA advantage.

## G4 and G5: paper-bearing evidence

G4 uses independently sampled world-life pairs and at least one pre-native plus
three strictly post-native checkpoints. Every interval adds new causal roots,
unique mappings, an old/new bridge, and a prospective prediction. Report new
acquisition, old retention, cross-era J/P action, supported causal coverage,
reader work, retained bytes, adapter rank/bytes, and all write/train/read costs.
Run a small preregistered rank/capacity grid. `Saturation` is allowed only when
a named baseline's simultaneous later-interval slopes lie inside a practical
plateau band while oracle headroom remains and the proposed system's lower
growth bound is positive.

G5 randomizes authentic/null/binding-shuffled/twin memory before an ordinary
information-gathering block, then performs one fixed sleep/reconsolidation and
scores a target sealed before collection. The flywheel needs all four links:
memory changes information action; information gain/coverage rises; later
supported memory improves; later action improves. A one-pair relay sentinel may
check wiring after G2, but cannot establish an effect.

## Baseline policy

The minimum final comparison includes no memory, honest native context then
truncation, raw episodic RAG, native linked/A-MEM-like memory, matched reflected
text, explicit graph/program induction, raw/direct-QA LoRA, compiled text, and
identical-corpus LoRA. TMEM, Auto-Dreamer, PEAM, DECKARD, Voyager, A-MEM, and
fast-weight/nested-learning work remove any broad novelty claim about dreaming,
linked memory, parametric memory, learned writing, sleep, or lifelong agents.
The contribution is the prospective action/lifetime causal comparison and,
only if measured, its connected parametric transport and growth behavior.

Pilot baselines are intentionally staged. G1 needs no-memory/open/atoms/cut/
twin because it tests the controller. G2 must include raw RAG, reflection,
graph, and program induction. G3 adds direct/raw LoRA. Native A-MEM and
procedural-skill controls are mandatory before confirmation but should not be
rushed into the first falsifier as weak imitations.

## Resource and launch decision

The 8xA40 node is reachable, idle, has the pinned Qwen2.5-32B checkpoint cached,
and has an existing vLLM runtime. The GH200 is also reachable and idle. Hardware
provisioning is therefore complete.

After exact ratification, the remaining G1 implementation is an isolated RML
adapter package: model-facing fixture projection, target-independent memory
rows/reader, action-capable recurrent machine, trace reducer, prompt/schema,
runner, tests, and workflow. Existing checkpoint, call-ledger, canonicalization,
world, target, and trace-test patterns should be reused; v03-specific scientific
adapters must not be renamed as RML support.

Expected time after ratification:

- 4--8 hours: implement and CPU-test the fast G1 adapter/runner.
- 1--3 hours: independent review, remote sync, first-call canary, and 234-call
  GPU fast gate, depending on observed batching/throughput.
- 4--12 GPU-hours: text-first G2 after G1 and a real multi-root generator are
  green.
- 0.8--7.1 adapter GPU-hours: conditional G3 transport, never before G2.

The old all-in 8,192-call estimate is retired. The corrected G1 fast gate is
234 calls; the four-pair strengthened DEV is 572.

## Immediate stop rules

- Do not treat v03r/v1f or RML-D0 as paper evidence.
- Do not train LoRA to repair a failed text compiler or failed recurrent
  controller.
- Do not count target pairs nested in one deterministic fixture as independent
  world-life replications.
- Do not call a fixed-deck result a flywheel.
- Do not weaken explicit graph/program baselines if they win.
- Do not attribute recognition candidate construction or clean-base composition
  to the adapter.
- Do not grow protocol/governance machinery unless it protects a causal path
  whose violation would change the paper conclusion.

## Inputs reconciled

- `research_notes/42_system_thesis_and_experiment_map.md`
- `research_notes/46_pcfl_constructive_assay_v1.md`
- `research_notes/47_pcfl_execution_bundle_v1.md`
- `research_notes/48_pcfl_stream_and_schema_design_v0.md`
- `research_loop/plans/rml_pilot_v1.md`
- `rml_d0/` and `rml_d0/stage_a_report.json`
- `research_loop/advisory/20260903_paper_benchmark_architect.md`
- `research_loop/advisory/20260903_paper_learning_architect.md`
- `research_loop/advisory/20260903_paper_prior_baseline_audit.md`
- `research_loop/advisory/20260903_rml_d0_to_stage_b_audit.md`
- `research_loop/advisory/20260903_rml_stage_b_reuse_map.md`
- `research_loop/advisory/20260903_paper_design_crosscritique.md`
