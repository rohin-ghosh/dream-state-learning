# 41 — Capacity/compression map and long-sequence loop training

Date: 2026-08-31. Status: future experiment, behind the current amortized
dream -> lifetime-memory -> think organism gates. This note does not authorize
replication-seed tuning or GPU work by itself.

## Why these are two experiments

The lifetime MEMORY adapter and reusable LOOP adapter solve different learning
problems and must never be conflated:

- MEMORY adapter: per-life fast state; stores what happened and what structure
  this lifetime supports; reset for every world.
- LOOP adapter: cross-life slow skill; learns which retrieval, hypothesis,
  revision, plan, action, and stopping operations work; shared across worlds
  and frozen during an evaluation life.

The current prompted controller is a teacher/ceiling. Its full trajectories are
training data for the later loop adapter, not evidence that the loop is already
learned.

## A. Capacity x compression phase diagram

Question: at a fixed reasoner, where is the boundary between remembering
experiential leaves, constructing held-out structure, and improving a novel
action? Do not assume fewer parameters generalize better; measure a response
surface.

### Frozen life deck

Prepare identical per-seed decks for every arm:

- Semantic World v0.2 public lifetime plus verified one-hop operator, parent,
  role, source, and rule leaves;
- Action World public action/outcome traces represented as TRANSITION,
  CAUSAL_RULE, ACTION_SCHEMA, and FAILURE_MODE memories.

For the first capacity map, use a perfect-gated gold corpus to isolate
representation from dream proposal noise. Replicate selected points with the
real self-check/drift corpus only after the map is interpretable. Fix episode
order, tokenizer, corpus content, recognition reads, training updates, task
budget, and evaluation checkpoints. Erase context at evaluation; mount the
memory LoRA only for atomic recognition reads and unmount for clean-base
composition/action.

### Axes

1. Effective memory capacity C: LoRA rank {4, 8, 16, 32, 64} on one frozen
   base and fixed target modules. Log trainable parameters, adapter bytes,
   tokens, steps, and optimizer. Include byte/slot-capped corpus controls so
   rank does not silently change available information.
2. Compression kappa, holding semantic information and token/exposure budgets
   as closely as possible:
   - k0: verbatim episodic/trajectory text;
   - k1: deduplicated witnessed atomic leaves;
   - k2: verified typed abstractions plus atomic support (current grammar);
   - k3: aggressively schema/procedure-only, removing episode details.

Report actual bytes/tokens, unique claims, support per claim, order templates,
and engine-recoverable facts. If a tiny rank fails atomic installation, first
raise/fix exposure; do not call ordinary underfitting "compression."

### Three separate readouts

1. Exact experiential memory: held-in atomic QA plus reverse, paraphrase, and
   partial cues; per-kind precision/recall and calibration.
2. Constructive generalization: v0.2 D3 operator, parent success@k, recipe
   gauge, and final hidden-role answer. A final answer cannot substitute for a
   failed parent-stage measurement.
3. Action value: Action World A2/A3 success, return, regret/actions, first-
   attempt success on held-out thresholds, and recovery after a wrong guard.
   A0 is recall; A1 is procedure-transfer control.

### Splits and controls

- Split by whole world seed, never individual cells. Tune formats/exposure on
  development worlds; freeze; use 5–8 unseen worlds for a headline estimate.
- Keep aligned/neutral/conflicting skins separate and do not pool them.
- Baselines at selected cells: no memory, honest full-context until it breaks,
  iterative episodic RAG, A-MEM-like linked text memory under a matched
  retrieved-token budget, direct trajectory-to-QA LoRA (TMEM-style), and
  end-of-life batch SFT on the same life.
- Main map uses one base. Cross-base replication uses both fixed adapter bytes
  and fixed adapter/base fraction, normalized to each base's context-oracle and
  no-memory scores. A raw base-size sweep confounds prior reasoning with memory.

### Compute-first pilot and falsifier

Pilot C={8,16,32} x kappa={0,2,3}, one aligned development world plus one
untouched smoke-test world, initially v0.2 construction and A2 action. Stop any
cell with atomic leaf recall <.85 or malformed reads >.05 before expensive
composition/action. Expand only if a surface/ridge is visible.

A Goldilocks regime is a hypothesis: low C may lose evidence; high C/low
compression may keep exact details without improving construction; an
intermediate cell may best support action. Reject this interpretation if rank
and compression effects are flat/non-identifiable, are fully explained by
atomic write fidelity/exposure, or vanish against strong matched baselines.

## B. Long-sequence dream/think LOOP-adapter pilot

Objective: amortize the expensive v0.2 branch/revisit ceiling into a reusable
operation policy without teaching test-world facts or final answers.

### Teacher data and serialization

Preserve every exhaustive 57-subset x two-proof-leaf trace, including failed
branches, public evidence IDs, prompts, raw outputs, query costs, revisit
decisions, final outcome, efficiency, world fingerprint, and skin. Serialize
causal transcripts:

```text
PUBLIC STATE -> ASSISTANT OPERATION -> TOOL/ENV RESULT -> NEXT STATE
```

Train only controller tokens: candidate frontier, QUERY(kind,args), REVISIT,
DEFER, ACT, RELEASE/STOP. Mask user/goals, public observations, tool/environment
results, and evaluator verdicts from loss. Never serialize hidden parents,
roles, answers, proof graphs, Action World threat bits/parity solver, or
FactorSolver outputs as model-visible state/targets.

### Two-stage pilot

1. Semantic proposal/revisit behavior cloning: Qwen 7B loop QLoRA r=8/16,
   2–3 epochs, train on whole development worlds and test on whole unseen
   worlds. Target ranked frontier and next operation, not a direct parent
   answer. Measure success@1/2/4/8/12, exact parents, atomic calls/tokens,
   revisit quality, stop calibration, and final D3 against the generic prompt
   and 57x2 ceiling.
2. Cross-world Action World transfer: freeze the loop adapter; initially give
   it fixed ephemeral text memory or no memory adapter. Train only on training
   worlds and test A1/A2/A3 on unseen hidden-law seeds with real runtime
   feedback. Only after this passes may a freshly reset per-world memory LoRA
   provide typed memories.

Chunk long streams causally at 8–32k with overlap plus explicit state
snapshots, but score full open-loop test trajectories without teacher forcing.
Curriculum: parent ranking -> check/revisit -> 8–16 operation loops -> full
multi-target/world streams.

### Controls, promotion, failure

Controls: frozen generic loop, prompt-only controller, random ranking with the
same checker, proposal-only SFT (no revise/stop), direct trajectory-to-answer
SFT as a leakage-positive diagnostic, shuffled candidate-result/action order,
and the exhaustive teacher ceiling. Action controls include generic-cautious
and parity-context oracle.

First promotion gate: on an unseen world, proposal success@12 improves at least
.15 absolute over the frozen top-k/generic loop, uses no more than half the
exhaustive atomic calls, and does not reduce D3. Then expand to five held-out
seeds and action transfer; only afterward try rejection-sampling SFT on
successful/efficient self-trajectories. Preference optimization or GRPO is a
later remedy for exploration, not the starting loss.

Fail the reusable-loop hypothesis if gains disappear on whole-world/skin
splits, rely on seen names/order, exist only under teacher forcing or higher
compute, or cannot beat a generic policy at the same operation budget. Assert
at evaluation that `loop_adapter_id` is shared/frozen,
`memory_adapter_id` is null or newly initialized per world, no gradient occurs
after evaluation-world construction, and no KV/memory state crosses worlds.
