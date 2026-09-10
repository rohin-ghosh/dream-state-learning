# Experience Model v6: design synthesis for exact intake

Status: root synthesis of three independent candidate designs. This is a
proposal input, not ratification, implementation authority, package-install
authority, GPU authority, or evidence.

## 1. The minimal experiment

There are exactly two primary on-policy systems:

- `HARNESS`: a strong ordinary agent with the frozen base, bootstrap,
  context-state loop, bounded notebook, target-blind ledger retrieval,
  task-local files/tools, clock/budgets, and public CompilerGym feedback.
- `EXPERIENTIAL`: the byte-identical harness plus one null-initialized,
  life-local LoRA on the same model. At fixed sleeps, its own sealed public
  experience is compiled into a cumulative LoRA rebuild; the adapter remains
  mounted for later context selection, thought, and action.

The notebook, retrieval interface, tools, context caps, and persistence rules
are identical. They are declared nonparametric capabilities, not hidden
channels and not attributed to the LoRA. The primary system result is the
on-policy lifetime contrast. `ADAPTER_OFF` and `BINDING_SHUFFLED` are sterile
evaluation forks from the treatment checkpoint, not extra agents collecting
different lives.

The first hardware pilot is one paired development life. It is a wiring and
mechanism falsifier. Only after a directional signal may a separately frozen
scout use three paired lives; paper-level slope evidence requires a later
powered confirmation with fresh lives and tasks.

## 2. Context is the conscious state

One recurrent state machine uses the same model for both invocation states:

```text
authoritative state
  -> ORIENT: choose focus and bounded retrieval queries
  -> harness materializes the requested common evidence
  -> THINK_ACT: reason and emit one typed operation
  -> public tool/environment outcome
  -> append event and update authoritative state
  -> repeat
```

These are two phases of one loop, not separately learned agents. In the
treatment the same LoRA is mounted for both. Thus experience may improve both
`what should occupy working consciousness?` and `what action follows?`.

V6 rebuilds every prompt from explicit structured state. Persistent provider
chat, hidden chain-of-thought, and KV/prefix cache are excluded. KV reuse is a
later efficiency optimization only.

Every call contains bounded canonical sections:

1. `ANCHOR`: immutable bootstrap, objective, rules, action/tool grammar.
2. `CLOCK_BUDGET`: logical task/life progress and remaining model-token,
   decision, environment-action, tool, retrieval, and notebook budgets.
   Infrastructure latency, arm name, adapter status, sleep duration, cache
   warmth, and evaluation identity are never visible.
3. `LIFE`: opaque life/task IDs, task ordinal, sleep index, public cumulative
   progress, and current best public score.
4. `FOCUS`: bounded subgoal, active question, strategy, uncertainty, and stop
   condition produced by ORIENT.
5. `ENVIRONMENT`: current public LLVM observation, legal actions, current-task
   public outcomes, and task-workspace manifest.
6. `RECALLED_EXPERIENCE`: at most two bounded results from the common
   notebook/ledger retriever requested by ORIENT.
7. `RECENT_TAIL`: fixed-token chronological suffix of complete public events.

ORIENT is called before every THINK_ACT in the first design. It may return
`KEEP` and request zero retrievals. This spends more inference but avoids a
hand-built or learned orientation scheduler. Both systems have exactly the
same call and token caps.

The only life-persistent external stores are an append-only public event
ledger and a small capped notebook written through a typed `NOTE_APPEND`
operation. Both reset between independent lives. Task workspaces, focus,
recent tail, CompilerGym process, tool processes, shell history, compilation
caches, provider state, and task RNG reset at every task boundary. Evaluation
forks return no state to the life.

THINK_ACT emits exactly one operation:

```text
INSPECT | APPLY_PASS | NOTE_APPEND | FOCUS_REVISE | STOP
```

Malformed operations consume the decision budget. `APPLY_PASS` is the only
operation that changes the CompilerGym state. No hidden retry occurs.

## 3. Experience record and sleep compiler

Every decision appends a canonical public record containing the reconstructible
pre-decision packet; retrieved record IDs; structured focus; bounded public
hypothesis/prediction fields when emitted; typed operation; official public
outcome and deterministic score; logical resource cost; successor-state hash;
and links to any later recovery. Hidden evaluator data and private reasoning
never enter the ledger.

SLEEP is not a second intelligence. At a fixed task-boundary cadence it runs a
pure compiler over a sealed ledger prefix, renders loss-masked rows, rebuilds
the cumulative adapter from the clean base with a fresh optimizer, atomically
publishes the adapter, and destroys trainer state. The adapter is the only
learned parameter state that crosses sleep.

The first compiler uses three views:

- `ORIENT`: pre-decision state -> structured focus that immediately preceded
  an outcome-improving trajectory segment.
- `ACT`: focused pre-decision state -> valid pass/action on an
  outcome-improving segment.
- `REVISE`: failed state + public failure/non-improvement -> the later focus
  and first valid action that recovered to a new best.

Loss is zero on anchors, observations, retrieved evidence, outcomes, prior
thought, and delimiters. It is one only on the structured focus or operation
target. Free-form rationale is never loss-bearing. A pre-outcome hypothesis
may be quoted as input/provenance; it becomes an ORIENT target only when its
following public action segment crosses the frozen improvement rule. No model
or human judges whether the wording is insightful.

For immediate reward, the action that creates a new best receives credit. For
delayed pass interaction, all valid actions since the previous best receive
fixed geometrically discounted eligibility when a later action creates a new
best. Invalid actions never receive positive ACT credit. A recovery row quotes
the failure as input and targets the first later action on the recovering
segment. This is temporal credit, not a claim of causal necessity.

Selection, deduplication, view quotas, delayed-credit discount, old/new replay,
corpus cap, multiplicity, tokenizer truncation, row order, effective target
token touches, LoRA recipe, and preservation rows are immutable run-manifest
bytes. Rejected rows and reasons remain in the audit manifest.

Recommended first writer recipe, subject to fit review rather than target
tuning:

```text
base: existing pinned Qwen2.5-32B-Instruct revision
LoRA: rank 16, alpha 16, dropout 0
targets: q_proj and v_proj in every block
optimizer: AdamW, lr 1e-4, reset every sleep
write: cumulative clean-base rebuild, no early stopping
corpus: <=192 selected rows, <=64/view, fixed 50:50 retained/new capacity
exposure: 24 target-token touches per retained row
preservation: small fixed task-free anchor set, identical for authentic and
              shuffled training; report separately
```

This is a plausible conservative mechanism point, not a claim that rank 16 or
attention-only adaptation is optimal. Rank/module response surfaces wait until
the mechanism exists. If the model fit canary shows a floor, base/model scope
must be re-ratified rather than silently changed.

`BINDING_SHUFFLED` uses exactly the authentic selected input rows and target
operation multiset, but deterministically deranges target focus/action objects
across compatible public-state strata before rendering. It preserves row,
view, token, and update budgets while breaking the state-to-useful-operation
binding. It does not claim to isolate outcome-conditioned selection; a later
`NO_OUTCOME_SELECTION` control may do that. The first pilot needs only:

1. on-policy HARNESS;
2. on-policy EXPERIENTIAL;
3. sterile treatment ADAPTER_OFF at checkpoints; and
4. sterile final-checkpoint BINDING_SHUFFLED.

Same-corpus text, raw-trajectory LoRA, wrong-life swaps, broader style panels,
and richer memory baselines become mandatory for confirmation, not for the
first wiring pilot.

## 4. CompilerGym fit

Candidate pin: official CompilerGym 0.2.5 LLVM environment and official
`IrInstructionCount`/normalized baseline reward. This objective is
deterministic and platform-independent; wall-clock runtime is logged only as
resource use. The official repository is archived and tied to LLVM 10, so an
unchanged installation and semantics canary is a hard rejection gate.

Preferred dataset if the official catalog is intact: `poj104-v1`, because it
contains many independent implementations grouped by 104 algorithms. This
supplies natural related-but-nonidentical program families without inventing a
new gym. The split constructor uses only public source/IR and family metadata,
never observed reward or model output. It excludes exact source/IR hashes and
near-identical normalized CFG/call-graph/opcode/type/loop-shape signatures.
The pilot needs at least two families with acquisition and sealed examples; a
larger scout adds opposite-feature and cross-family diagnostic panels. If the
package, dataset, LLVM 10 runtime, deterministic replay, or nonduplicate split
cannot be used unchanged, CompilerGym is rejected for this change.

## 5. Minimal staged execution

### Stage A: CPU/static fit

- Hash the official package/dependency/model artifacts already available.
- Verify installability in a disposable environment and exact official reward
  semantics without editing upstream bytes.
- Reset/replay fixed pass traces twice and require byte-identical observations
  and rewards.
- Build and seal a related/nonduplicate POJ104 catalog using only public static
  information.
- Unit-test context assembly, persistence/reset boundaries, sleep row masks,
  delayed credit, cumulative rebuild receipts, and sterile evaluation.

### Stage B: non-claim hardware/model canary

- Use a few acquisition-only programs to show the pinned model can emit valid
  pass operations, react to reward, and improve above its initial state under
  the fixed loop.
- Train one tiny synthetic/cached adapter to prove assistant-only loss masks,
  adapter mount/off, and cold-load reproduction.
- Reject the recipe on floor, schema collapse, numerical failure, or no
  measurable opportunity; do not inspect sealed pilot targets.

### Stage C: paired one-life pilot

- 8 acquisition programs, two sleeps after 4 and 8.
- 4 sealed related/nonduplicate targets evaluated at checkpoints 0, 4, and 8.
- 6 ORIENT/THINK_ACT decisions per program/target.
- One HARNESS and one EXPERIENTIAL on-policy life with counterbalanced task
  order; ADAPTER_OFF at every checkpoint; BINDING_SHUFFLED at the final
  checkpoint.
- Stop after the frozen report. No same-target repair or automatic scale.

Stage C is only a mechanism signal if the authentic adapter improves from its
own checkpoint zero, exceeds adapter-off on objective held-out action, and the
binding shuffle loses a material part of that gain without reduced schema
validity. Exact practical margins come from acquisition-only canary variance
and are frozen before targets open.

### Stage D: scout/confirmation after signal

Use fresh tasks and at least three paired lives for a directional scout; use a
powered number of independent lives and multiple checkpoints beyond the common
context capacity for a paper claim. Add same-corpus text, raw LoRA, organized
external-memory baselines, wrong-life swaps, rank/module brackets, retention,
condition changes, and predeclared hierarchical slope estimates. No result in
Stage C is a baseline-saturation or lifelong-growth claim.

## 6. Evidence and estimands

No private thought string or human-expected theory is scored. Primary public
quantities are deterministic instruction-count improvement, held-out
checkpoint AUC, final held-out score, first-action gain, decisions to best,
valid-operation rate, retention, and treatment-minus-harness / adapter-off /
binding-shuffle contrasts. Report model/tool/environment calls, tokens,
training steps/FLOPs, adapter bytes, wall time, failures, and retries.

The pilot reports paired target curves only. A paper-level derivative uses
life as the replication unit, a preregistered hierarchical or piecewise model,
and whole-life uncertainty. Raw first differences are diagnostic; raw second
differences are not evidence. Baseline saturation is claimable only when the
control's post-context slope is practically near zero with remaining oracle or
search headroom while the experiential slope remains positive.

## 7. Exact human taste surface

The architecture follows the latest directive without another conceptual
choice. Before implementation, the owner should only need to accept or change
these consequential defaults:

1. CompilerGym/POJ104 as a conditional fit-gated v6 scout rather than
   KernelBench-Verified.
2. Mandatory ORIENT before every THINK_ACT, with both phases using the same
   model and treatment LoRA.
3. A bounded notebook and ledger retriever in both systems, so HARNESS is a
   strong contemporary baseline.
4. Deterministic three-view sleep compilation and cumulative clean-base LoRA
   rebuild.
5. The conservative Qwen2.5-32B rank-16 q/v recipe above for the first fixed
   point.
6. One paired life as the first non-claim pilot; replication and full baselines
   only after it shows a causal adapter signal.
