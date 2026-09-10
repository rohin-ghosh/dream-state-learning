# RML-D0 Stage-A to Stage-B audit

**Date:** 2026-09-03  
**Status:** read-only advisory. This does not ratify Stage B, model calls,
GPU work, or changes to `rml_d0/`.

## Executive verdict

The checked-in RML-D0 code and green `stage_a_report.json` certify a useful
**self-consistency preflight for a finite deterministic CPU fixture**. They do
not certify an independently verified benchmark, a model-facing causal
instrument, an experiential-memory mechanism, or a Paper-1 result.

Its best next use is not the 64-pair production gate or the 1,036-row
governance/rework program. It is a separately authorized text-only **four
twin-pair G1 gold-memory pilot**:

> Can one frozen resolver use target-independent connected local memory through
> recurrent reads to execute the RML J/P action tasks, while no-memory,
> non-adaptive/open-read, atoms-only, cut, and twin-memory controls remain low?

This pilot is an interface and constructivity gate only. A positive result
earns a frozen minimal causal instrument and a later experience-derived text
memory experiment—not DREAM, LoRA, consolidation, or paper language. A
negative result with a viable typed-gold ceiling is reason to stop this RML
text-reader path.

## What the existing Stage-A report actually certifies

The report is internally coherent with its explicit firewall
`CPU_STAGE_A_INSTRUMENT_CONFORMANCE`: it records `passed: true`, zero
model/GPU/network calls, no recorded failures, 32 literal target sides, 16
target pairs, eight bridge rows, four P completions, and 64 J-cut variants. Its
resource record reports one worker, 30,451 ms, 66.5 MB peak RSS, 1.23M
transitions, and 110,675 sealed bytes. These are engineering observations of
the CPU program, not model statistics.

| Certified within the checked-in implementation | Evidence | Paper relevance |
|---|---|---|
| Canonical record rendering has small positive/negative coverage. | `canonical.py`; report `canonical_*` gates. | Necessary serialization hygiene only. |
| A finite fluid/thermal world has registered nine-action plans for 16 H/twin target pairs. | `world.py`, `targets.py`, `planner.py`; 32 literal target-side vectors. | A symbolic solver can solve this game. No language-model parse or plan result follows. |
| H/twin targets collide in target-public bytes while useful conditioner pairs and valve modes differ. | `targets.target_goldens()` and 16-pair target table. | A promising anti-target-decoder control for this exact fixture. |
| J has old/current provenance roles and registered deletion variants fail for the exact program. | `targets.j_cut_goldens()`, 64 cut variants, replay certificates. | Candidate old-to-new dependency construct, not model memory necessity. |
| P atoms-only has four equal visible completions; gold/program information resolves one. | `p_atoms_only.optimal_value = 1/4`; `targets.evaluate_p_atoms`. | A good formal contrast between atom retrieval and a connected/schema relation. |
| Symbolic source chronology grows mappings/statuses and commits before later status records. | `source.py`, `schema_reference.py`, report chronology. | CPU reference timing; no learned proposal/commitment. |
| Selected local regressions are rejected by in-package mutation probes. | `probes.mutation_kills()`. | Regression coverage, not an independently run mutation campaign. |
| A subprocess leaves a temporary source descriptor unchanged and selected imports/writes are denied. | `isolation.py`, `isolation_worker.py`. | Synthetic Stage-A micro-evaluator check, not OS-enforced Stage-B isolation. |

This is useful preparation: it turns a vague RML concept into executable
target/twin/J/P examples and preserves an exact reference for a later small
causal instrument.

## What it does not certify

### It is not an independent Stage-A oracle

The report's `oracle_vectors` are subject-package checks. `probes.py` imports
`targets`, `source`, `planner`, `bayes`, `canonical`, and `rng`; the CPU gate
imports both the expected digest dictionary and the functions that generate the
actual value from `rml_d0`. M1--M9 are in-process synthetic calculations, not
patched subject copies assessed by an external oracle.

The hardened Stage-A plan requires a separate oracle package, frozen
subject/oracle manifests, literal vectors, OS boundary, schema artifact,
subject/evaluator CLIs, and workflow manifest. All are absent:

```text
research_loop/oracles/rml_d0_stage_a_v1/
research_loop/schemas/rml_d0_objects.schema.json
research_loop/goldens/rml_d0/
research_loop/manifests/rml_d0_stage_a_subject_v1.jcs
research_loop/manifests/rml_d0_stage_a_oracle_v1.jcs
research_loop/workflows/rml_d0_cpu_gate_v1.json
rml_d0/subject_cli.py
rml_d0/evaluator_cli.py
```

The honest evidence label is therefore **subject-package self-consistency
against hard-coded expected digests**, not independent instrument conformance.

### Its isolation result is synthetic and Stage-A-local

`isolation_worker.py` monkeypatches Python imports and `open` in a temporary
directory. It does not use the Linux namespace/cgroup or macOS sandbox required
by the rework, does not run a production controller/evaluator, and does not
bind a full source/oracle closure. It cannot establish that a later model
process lacks source, scorer, cache, or cross-life channels.

### It has no model-facing semantic task contract

There is no pinned model/tokenizer, natural-language event renderer, prompt,
action parser, memory-reader API, context budget, seed policy, or model-visible
versus scorer-visible contract. The exact planner receives Python `Action`
objects and `TargetSpec`s. No claim about parsing, atomic read fidelity,
recurrent query selection, language planning, or counterfactual memory use is
identified.

### It has no memory, learning, or fair baseline comparison

There is no model-visible raw history, text memory, RAG, A-MEM/graph baseline,
reflection memory, direct-QA LoRA, per-life adapter, DREAM proposal, support
admission, or outcome-driven update. The symbolic schema is correctly a gold
reference, not DREAM credit. No arrow in the central chain is tested:

```text
agent action/outcome -> experience -> memory formation -> recurrent use
-> different held-out action
```

### It is not a lifelong-action benchmark result

The source is fixed and outcome-blind; even a later fixed-deck pass cannot
prove policy-selected evidence acquisition or the complete flywheel. D0 has no
post-native-context, across-life growth axis. Notes 42 and 48 reserve those
claims for PCFL-Stream/Schema and on-policy work.

## Construct-identification matrix

| Construct | Stage A identifies it? | Missing condition |
|---|---|---|
| Deterministic finite-environment correctness | **Partly** | The exact fixture has internal checks; independent-oracle conformance is unearned. |
| Target-byte collision/opposite twin action | **Yes, for registered micro-fixtures** | Preserve it in G1. |
| Target-only headroom | **Symbolically only** | Need a model-facing no-memory/Bayes controller value. |
| Old/current/prospective information necessity | **For exact program only** | Need cut and twin-memory interventions on model trajectories. |
| Connected memory versus atoms | **No** | Need identical memory under recurrent versus nonadaptive reading, including P-atoms. |
| Recurrent goal-conditioned reconstruction | **No** | Need logged adaptive query chains. |
| Experience-derived memory formation | **No** | Need public source history plus target-independent support/compiler. |
| Parametric transport / LoRA | **No** | Need same-corpus text/LoRA and direct-QA controls after text passes. |
| Continued learning/compression/saturation | **No** | Need fresh relation cohorts and three post-native checkpoints. |
| On-policy experiential flywheel | **No** | Need information-seeking actions that alter later memory/return. |

## Recommended smallest Stage-B: G1 connected-gold text pilot

Create a new DEV-only protocol rather than retrospectively presenting a
simplification as Candidate-B conformance. Reuse just the causal spine.

### Fixture

- Freeze **four counterfactual twin pairs**, two J and two P, before any model
  call; evaluate both H and twin target sides.
- Retain only public target state, legal `MOVE/ACQUIRE/APPLY/CONFIGURE/RUN/
  COMMIT` actions, ordinary outcomes, target-byte collision, and irreversible
  failure. The registered nine-action target path is adequate for this gate.
- Provide a short faithful model renderer for public source events and target
  state. It must not render hidden transforms, twin side, useful pair, valve
  truth, target identifier, or any full solution.
- Provide **gold target-independent one-edge records** containing public source
  IDs and old/current provenance. For J, success needs separately sourced old
  and current records. For P, local atoms alone leave four completions; the
  connected gold record is a precommitted grammar/schema relation that resolves
  the missing edge. Gold is a reader/interface ceiling, not learned memory.
- Keep exact target/twin checking scorer-only. The model sees public action
  outcomes and reader returns only.

### Common reader/controller

Use one pinned frozen resolver for every condition, preferably the already
planned high-headroom resolver rather than a cheap model that cannot use known
facts. The PCFL plan's 32B resolver is a sensible G1 choice: this is
inference-only and at most 56 short trajectories, while mixing a 7B reader
with a 32B control would make a negative uninterpretable.

Per decision, give the model its public state and append-only workspace. It may
make at most four `READ(key)` calls, eight resolver operations total, and nine
environment actions. `READ` returns one immutable atom plus provenance or
`NOT_FOUND`; it never receives latent truth, target identity, whole-life scan
results, or an action candidate list. A recurrent trace is valid only when a
later query contains a canonical value first returned by an earlier query.

### Minimum conditions

| ID | Memory/query policy | Scientific role |
|---|---|---|
| `N` | No lifetime memory; current public target/state only. | Frozen-agent action floor. |
| `O-open` | Connected gold, but every read key commits before any return. | Non-adaptive closure control. |
| `O-rec` | Same connected gold with generic recurrent reads. | Connected-memory use ceiling. |
| `P-atoms` | P only: all local atoms but no grammar/schema relation, recurrent reader. | Tests that atom retrieval cannot impersonate prospective structure. |
| `O-cut` | Replay `O-rec` successes after masking every cited decisive atom. | Causal-use intervention. |
| `O-twin` | Replay against unchanged target/state with twin gold memory. | Memory-assignment intervention; the predicted twin-valid action should be selected and fail in the actual world. |

`O-cut` and `O-twin` are intervention replays, not new writer baselines. This
keeps the pilot small without granting memory credit to an answer that survives
its alleged cause being removed.

### Predeclare G1 gates

Use the RML ROI appendix thresholds before outcomes are viewed:

- typed connected-gold API diagnostic (if used) `>= .80`;
- generic `O-rec` action success `>= .85` on the four-pair mean;
- `N`, `O-open`, target-only/current-state-only probes, and `P-atoms` `<= .35`;
- at least `.80` of `O-rec` successes lose required action/return under cited
  atom masking and show predicted direction under twin-memory substitution;
- every credited `O-rec` success contains a mechanically valid dependency
  trace. Correct action without that trace is action-only success, not G1
  constructivity.

Interpret negatives asymmetrically. Low typed gold means stop: the task/model
interface is unusable. High typed gold but low generic `O-rec` localizes the
failure to reader/controller, not DREAM or LoRA. If `O-open`, `P-atoms`, or
`N` also pass, the fixture lacks constructive headroom. Only the clean pattern
licenses replacing gold records with experience-derived text.

## Fairness and leakage rules

1. Same resolver, prompt shell, action parser, output cap, workspace, seed
   policy, read/action budgets, and retry rule in every condition.
2. `O-open` and `O-rec` have identical atoms; only adaptivity changes.
   `P-atoms` has every local atom except the schema relation by definition.
3. Memory construction sees only frozen public source events. Target/twin
   roles, held-out plan, solver output, and target handles remain scorer-only.
   Establish this with an input manifest and serialization/grep checks.
4. Mask all semantically equivalent records and indexes in `O-cut`; later this
   becomes whole-adapter swapping for LoRA.
5. Freeze pairs, prompts, record set, query grammar, and thresholds before the
   first dispatch. Four pairs are DEV-only—never retrospective confirmation.
6. Record input/output tokens, model/reader calls, wall time, action steps,
   failures, deferrals, and malformed outputs. There is no training cost.

## What remains deferred

G1 must not become a stealth paper experiment. It defers learned DREAM,
self-check, admission/compiler quality, raw RAG/A-MEM/reflection/direct-QA
LoRA baselines, text-to-LoRA transport, revision, on-policy exploration,
locked inference, post-context retention, growth curves, schema discovery, and
external-gym validation.

If G1 passes, the next useful evidence is a frozen text-only G2: replace gold
records with target-independent, chronologically supported experience-derived
atoms and compare `E-text` with raw episodic RAG and native linked memory under
the same reader. Do not train LoRA until that text gate passes.

## Decision

Archive Stage A as a valuable CPU fixture preflight. Do not spend GPU time as
though it has already hardened the benchmark, and do not spend 20--35 days on
the full rework before G1. A separately ratified minimal J/P G1 answers the
highest-value question at far lower cost.

## CORRECTION (2026-09-03): exact G1 operation and resource accounting

The initial G1 wording was inconsistent: it allowed up to four reads *per
decision*, only eight resolver operations total, and a nine-action target.
Those cannot all be true when one model call emits one operation. This section
supersedes the reader/controller budget above.

### Correct operation semantics

One model call emits exactly one of two operations:

```text
READ(key)                         # one immutable atom or NOT_FOUND
ENV(action)                       # one legal public environment action
```

Every RML J/P target has a nine-action minimum path. The whole trajectory,
not each environment decision, has a fixed maximum of **four `READ` calls plus
nine `ENV` calls = 13 model calls**. There are no additional planning, tool,
reflection, retry, or hidden resolver calls. A malformed/illegal/over-budget
operation terminates the trajectory with value zero.

For `O-rec`, each read result is appended before the next model call, so only
this condition can adapt a later key to an earlier return. For `O-open`, the
model makes four `READ` calls but the host buffers all four returns and exposes
them together after the fourth call; hence all keys are chosen without a
memory return. For `N`, issue four mandatory `READ(NULL)` operations returning
`NOT_FOUND`, so it receives the same 13-call envelope without an artificial
extra thinking budget. `P-atoms`, `O-cut`, and `O-twin` follow `O-rec` timing
and the identical 13-call envelope.

The reader must return at most one bounded atom per `READ`; the input to each
model call is public current state, full public action history, prior reader
returns allowed by the condition, and the append-only workspace. Reader lookup
and environment stepping are host tool calls and must be logged separately;
they are not hidden LLM calls.

### Per-target resource table

Each table row below means **one pair x one side x one target x one condition**.
There is one target per side in this pilot.

| Condition | Model calls | READ ops | ENV ops | Read-return timing | Notes |
|---|---:|---:|---:|---|---|
| `N` | 13 | 4 null | 9 | immediate `NOT_FOUND` | Exact call-matched no-memory floor. |
| `O-open` | 13 | 4 | 9 | all four buffered until read 4 | Exact call-matched nonadaptive control. |
| `O-rec` | 13 | 4 | 9 | immediately after each read | Connected-gold recurrent ceiling. |
| `P-atoms` | 13 | 4 | 9 | immediate | P only; no schema/grammar record. |
| `O-cut` | 13 | 4 | 9 | immediate | Fresh replay with all cited decisive records masked. |
| `O-twin` | 13 | 4 | 9 | immediate | Fresh replay with the twin memory behind unchanged target bytes. |
| `O-typed` (diagnostic) | 13 | 4 | 9 | immediate | Optional only as a pre-G1 API ceiling; never mix it into generic-G1 results. |

`O-cut` must use the cited set from the original frozen `O-rec` trace, but the
fresh replay receives no original action trace or answer. The model starts from
the same public target state and must act again. `O-twin` similarly starts
fresh; its expected twin-valid action direction is scored, while real-world
success is expected to fall.

### Fast-gate option: two twin pairs

Use one preselected J pair and one preselected P pair, both H/twin sides. Run
the three core conditions on all four sides, `P-atoms` on the two P sides, and
cut/twin replays on the canonical H side of each pair. This is explicitly a
fast falsifier, not a balanced scientific estimate.

| Work item | Pair count | Sides/pair | Targets/side | Conditions | Trajectories | Model calls | READ ops | ENV ops |
|---|---:|---:|---:|---|---:|---:|---:|---:|
| Core `N`, `O-open`, `O-rec` | 2 | 2 | 1 | 3 | 12 | 156 | 48 | 108 |
| `P-atoms` | 1 P pair | 2 | 1 | 1 | 2 | 26 | 8 | 18 |
| `O-cut`, `O-twin` interventions | 2 | canonical H only | 1 | 2 | 4 | 52 | 16 | 36 |
| **Fast-gate total** | **2** |  |  |  | **18** | **234** | **72** | **162** |

If the typed API ceiling is needed, add `O-typed` on all four fast-gate sides:
four trajectories, 52 model calls, 16 reads, and 36 actions, for a maximum of
286 model calls. Run it before generic G1 and keep its output separate.

### Stronger DEV option: four twin pairs

Use two frozen J pairs and two frozen P pairs, evaluate both sides, run the
three core conditions everywhere, `P-atoms` on every P side, and both cut/twin
interventions on every successful `O-rec` side. The resource total below is a
worst-case reservation: failed `O-rec` sides remain recorded but do not cause
replacement pairs or new dispatches.

| Work item | Pair count | Sides/pair | Targets/side | Conditions | Trajectories | Model calls | READ ops | ENV ops |
|---|---:|---:|---:|---|---:|---:|---:|---:|
| Core `N`, `O-open`, `O-rec` | 4 | 2 | 1 | 3 | 24 | 312 | 96 | 216 |
| `P-atoms` | 2 P pairs | 2 | 1 | 1 | 4 | 52 | 16 | 36 |
| `O-cut`, `O-twin` interventions | 4 | 2 | 1 | 2 | 16 | 208 | 64 | 144 |
| **Four-pair total** | **4** |  |  |  | **44** | **572** | **176** | **396** |

Add the optional typed ceiling on all eight sides only if needed to interpret a
generic failure: eight trajectories, 104 calls, 32 reads, and 72 environment
actions, making the maximum reservation 676 calls, 208 reads, and 468 actions.

### Accounting and fairness consequences

- The earlier claim of "four reads per decision" is withdrawn. Four reads are
  the maximum **per target trajectory**.
- `O-open` is now exactly call-matched to `O-rec`; buffering returns, rather
  than fewer calls, is what removes adaptive closure.
- `N` is call-matched through null reads. Report its calls separately so a
  reader-free floor is not misrepresented as an efficient agent.
- Quote both total model calls and completed trajectories. A method that
  exhausts its four reads early is not entitled to extra action calls.
- The stronger design has 44 actual trajectories under the worst-case
  reservation, not 56. The previous informal 56 estimate is withdrawn.
- Neither option has a meaningful training/GPU-hour cost beyond inference. Any
  model/provider batch parallelism must preserve the per-trajectory sequential
  read-return order and be reported; it may not change the 13-call envelope.

## Local evidence inspected

- `/Users/rohing/dream-state/rml_d0/stage_a_report.json`
- `/Users/rohing/dream-state/rml_d0/{run_cpu_gate.py,world.py,targets.py,source.py,planner.py,probes.py,certificates.py,isolation.py,isolation_worker.py,bayes.py}`
- `/Users/rohing/dream-state/rml_d0/tests/`
- `/Users/rohing/dream-state/research_loop/plans/rml_d0_world_candidate_A.md`
- `/Users/rohing/dream-state/research_loop/plans/rml_d0_stage_a_rework_v1.md`
- `/Users/rohing/dream-state/research_loop/plans/rml_d0_stage_a_rework_v1_paper_roi_appendix.md`
- `/Users/rohing/dream-state/research_loop/plans/rml_d0_stage_a_independent_oracle.md`
- `/Users/rohing/dream-state/research_notes/42_system_thesis_and_experiment_map.md`
- `/Users/rohing/dream-state/research_notes/46_pcfl_constructive_assay_v1.md`
- `/Users/rohing/dream-state/research_notes/47_pcfl_execution_bundle_v1.md`
- `/Users/rohing/dream-state/research_notes/48_pcfl_stream_and_schema_design_v0.md`
