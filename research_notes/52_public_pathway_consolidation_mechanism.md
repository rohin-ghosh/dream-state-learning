# 52 — Public Pathway Consolidation mechanism

**Date:** 2026-09-05  
**Status:** NONNORMATIVE, PROPOSAL-ONLY research design. This note does not
authorize implementation, change PPC5r4, modify an ongoing experiment, or
launch CPU/model/GPU work. Any adoption must enter the repository's durable
architecture-deliberation and human-ratification path.

## Purpose

Public Pathway Consolidation (PPC) is the smallest concrete rung between the
v9 successful-action clone and an unconstrained free-form organism. It tests
whether one frozen language model plus one per-life LoRA can learn from its
own public cognitive-and-action trajectories without claiming access to hidden
chain-of-thought.

The central loop is:

```text
public conscious state
  -> same base+life-LoRA selects one typed cognitive/action operation
  -> tool, memory, or environment returns a public result
  -> public state changes
  -> repeat
  -> SLEEP replays eligible pathways and proposes writes
  -> public evidence admits or rejects them
  -> deterministic serialization trains the next life-LoRA
```

There is no separately learned thinker, dreamer, planner, verifier, or sleeper.
The same model thinks during wake and replay. SLEEP is the proposal/admission/
serialization/write process; only the per-life LoRA learns.

## 1. Context as conscious state

Each model call receives a newly rendered `ConsciousState`. The harness owns
canonical state and the model chooses how to change it through public
operations.

```json
{
  "schema_version": "ppc-think-v0",
  "life_id": "opaque-life-id",
  "step_index": 17,
  "goal": {"task": "...", "metric": "..."},
  "clock": {"calls_left": 11, "reads_left": 3, "actions_left": 2},
  "active_stack": ["root", "g2"],
  "workspace": [
    {
      "node_id": "h4",
      "kind": "HYPOTHESIS",
      "content": "...",
      "cited_semantic_ids": ["m12", "m31"],
      "status": "TENTATIVE"
    }
  ],
  "open_surprises": [
    {"prediction_id": "p3", "expected": "...", "observed": "..."}
  ],
  "recalled": [
    {"semantic_id": "m31", "kind": "EDGE", "public_value": "..."}
  ],
  "recent_transitions": ["public bounded transition projections"],
  "last_result": {"kind": "ENV_RESULT", "public_value": "..."}
}
```

Admission to the prompt is deterministic:

1. the goal, clock, active subgoal path, latest result, and unresolved
   surprises are mandatory;
2. memory and hypothesis nodes attached to the active path follow;
3. the newest public transitions fill the remaining token budget;
4. inactive material leaves the window but remains in the append-only ledger;
5. only an explicit model-selected query can bring evicted material back.

This provides bounded ephemerality without a learned context manager. The
model controls attention by choosing subgoals, queries, follows, revisions,
and backtracks; the harness only enforces the disclosed token budget.

## 2. One typed public THINK loop

At each step, the same model emits exactly one bare JSON operation:

```text
OPEN_SUBGOAL | QUERY_MEMORY | FOLLOW | HYPOTHESIZE | PREDICT |
ACT | REVISE | BACKTRACK | DEFER | STOP
```

Minimum shared envelope:

```json
{
  "op": "OPERATION_KIND",
  "active_subgoal_id": "g2",
  "operation_fields": {}
}
```

The operation-specific payloads are:

```text
OPEN_SUBGOAL: new_subgoal_id, public_description, parent_subgoal_id
QUERY_MEMORY: query_key, public_subject, public_relation, optional_object
FOLLOW: from_semantic_id, to_semantic_id
HYPOTHESIZE: hypothesis_id, public_claim, cited_semantic_ids,
             parent_hypothesis_ids
PREDICT: prediction_id, hypothesis_id, public_expected_outcome
ACT: action object from the frozen environment action schema
REVISE: old_hypothesis_id, new_hypothesis_id, public_revised_claim,
        cited_semantic_ids, revision_kind
BACKTRACK: reason_code, optional_promoted_hypothesis_id
DEFER: reason_code, unresolved_public_ids
STOP: released hypothesis/action plus cited support path
```

`PREDICT` must precede a claim-bearing `ACT`. `HYPOTHESIZE` and `REVISE` may
cite only records already retrieved into the public workspace. `STOP` is
legal only when its cited records form a valid public support path. Invalid
or multi-operation outputs consume their call and are never silently retried.

Thinking-about-what-to-think and task reasoning are not separate modules:

```text
OPEN_SUBGOAL / QUERY_MEMORY / BACKTRACK = choose where thought goes
FOLLOW / HYPOTHESIZE / PREDICT / REVISE = work within that direction
ACT / STOP / DEFER = expose the current result to the world
```

Breadth and depth emerge from the model's operation sequence. The harness does
not impose a conscious/subconscious alternation or a BFS/DFS label.

## 3. Auditable thought trajectories

The system does not expose, request, score, or train private chain-of-thought.
A scientifically visible thought is a typed, falsifiable update to the public
workspace. For example:

```json
{
  "op": "HYPOTHESIZE",
  "active_subgoal_id": "g2",
  "operation_fields": {
    "hypothesis_id": "h7",
    "public_claim": "X before Y may improve condition C",
    "cited_semantic_ids": ["m12", "m31"],
    "parent_hypothesis_ids": ["h4"]
  }
}
```

Every call appends this causal tuple:

```text
PUBLIC_STATE_t
  -> ASSISTANT_OPERATION_t
  -> TOOL/MEMORY/ENV_RESULT_t
  -> PUBLIC_STATE_t+1
```

The audit record includes exact visible bytes, raw response bytes and token
IDs, parser result, state-before/state-after hashes, decoding seed, model and
adapter hashes, budgets, and provenance. A pathway is an ordered list of these
records, not a prose retrospective.

## 4. Connection and hop representation

PPC separates epistemic structure from use structure:

```text
ATOM:       one directly witnessed public relation
EDGE:       subject --relation/condition--> object/action/outcome
USE_LINK:   two semantic IDs were cited or traversed in one pathway
SHORTCUT:   a supported multi-edge path materialized as a one-hop record
POLICY_PATH: ordered public operations associated with a measured outcome
```

`USE_LINK` is operational metadata, not evidence that a factual relation is
true. Co-use can affect future retrieval adjacency but cannot grant semantic
support.

The LoRA need not solve a whole graph in one forward pass. It learns one-hop
recognition and next-operation tendencies. Hops remain explicit:

```text
goal -> QUERY -> one local record -> FOLLOW/QUERY -> another record
     -> cited hypothesis -> prediction/action
```

A shortcut is eligible only when all constituent edges are already supported
and the path has succeeded in at least two independent situations. It retains
the ordered constituent IDs as provenance. This allows repeated paths to be
amortized without converting unsupported co-occurrence into truth.

## 5. SLEEP: proposal, admission, serialization

### 5.1 Deterministic eligibility pool

At a fixed checkpoint in the first assay, select a bounded, target-blind pool
from public history:

- successful or efficient terminal pathways;
- failure -> public feedback -> recovery pathways;
- large committed-prediction/observed-outcome residuals;
- paths repeatedly used across independent tasks;
- contradictions that resulted in a valid revision;
- unresolved surprises that warrant a future test.

Outcome and chronology determine eligibility; model confidence does not.

### 5.2 Same-model replay and proposals

The current `base + LoRA_t` receives bounded replay bundles and uses the same
typed loop, with write-proposal permissions replacing environment actions. It
may emit:

```text
PROPOSE_ATOM | PROPOSE_EDGE | PROPOSE_SHORTCUT |
PROPOSE_POLICY_CASE | PROPOSE_TEST | PASS
```

Each proposal cites public event, semantic, and pathway IDs. The model chooses
the content and connections; a mechanical compiler does not invent them.

### 5.3 Admission

- A directly witnessed atom is supported by the exact public event.
- A policy path is `REWARDED` only when its terminal outcome is a measured
  improvement, efficient success, or verified recovery. This does not assert
  that every step was necessary.
- A generalized edge/schema stays `PROVISIONAL` until a prediction committed
  before a later ordinary outcome is confirmed.
- A shortcut requires supported component edges plus successful repeated use.
- Contradicted proposals remain append-only and generate future revision
  examples.
- A model cannot assign its own support status.
- Hidden truth and offline target scoring never steer proposal or admission.

A provisional proposal may emit a non-evidentiary waking test agenda. It does
not enter positive LoRA data until later experience supports it.

### 5.4 Runtime-matched serialization

Accepted records become only two training-row families:

```text
READ:
  exact runtime one-hop query + target-blind candidate domain
  -> supported local value or NOT_FOUND

DECIDE:
  exact runtime public ConsciousState
  -> next public cognitive/action operation from an eligible pathway
```

All input, environment-result, and memory-return tokens are loss-masked. Loss
applies only to the exact assistant value or operation. Failed actions are not
positive targets; their public outcomes occur in inputs whose correct target
is a recovery operation such as `REVISE`, `BACKTRACK`, or `QUERY_MEMORY`.

The first proposed fixed mixture is:

```text
25% directly witnessed anchors
25% supported abstractions/shortcuts
50% public decision/pathway rows
```

Rows are canonically deduplicated and old/new rows are interleaved. Every
checkpoint rebuilds the cumulative per-life adapter from the clean base. This
avoids Fable v6's free-prose/all-token format interference while preserving
both episode-specific anchors and compressed structure.

## 6. LoRA read and recurrent decompression

For a minimal 7B implementation, a `QUERY_MEMORY` operation triggers a
same-model recognition call using the per-life LoRA. The candidate domain is
frozen from public ontology or produced by a target-blind, arm-matched
shortlister. The LoRA selects a local value; the immutable semantic audit
snapshot supplies its provenance and rejects outputs outside the declared
domain. The shortlister and audit lookup are never credited as adapter
intelligence.

The returned one-hop record enters `ConsciousState`. The next ordinary THINK
call chooses whether to follow it, ask another question, revise, or act. Thus:

```text
LoRA = compressed associative experience + operation bias
context = current conscious workspace
recurrent calls = decompression and multi-hop traversal
```

The identical semantic snapshot must also be served as explicit text through
the same read interface. This separates compiler quality from LoRA transport.

## 7. Minimal causal ablation matrix

All evaluation conditions receive identical model-call, read, action, output-
token, context, and clock budgets. One call emits at most one operation.

| Condition | Training from the same frozen life | Identifies |
|---|---|---|
| `NO_SLEEP` | none | recurrent frozen-loop floor |
| `SLEEP_DISCARDED` | same replay calls, outputs discarded | extra sleep inference |
| `ENDPOINT` | successful `state -> ACT` rows only | v9 action-cloning floor |
| `SEMANTIC_ONLY` | READ rows only | experiential content without policy learning |
| `COGNITIVE_NO_ACT` | successful DECIDE rows excluding every `ACT` target | reasoning-policy transfer without answer/action cloning |
| `JOINT` | READ plus complete eligible DECIDE pathways | proposed full mechanism |
| `PATH_SHUFFLED` | JOINT rows with within-path cognitive order shuffled | ordered pathway value |
| `OUTCOME_SHUFFLED` | JOINT with action/outcome or world bindings shuffled | authentic experience causality |
| `ATOMS_ONLY` | witnessed records, no use links/shortcuts | unconnected-memory control |
| `LINKED` | atoms plus admitted edges/use links/shortcuts | connected-experience contribution |
| `TEXT_SAME_CORPUS` | identical admitted semantics in explicit text | compiler versus LoRA transport |

At final evaluation, additionally compare the exact same public state under
adapter on, adapter off, wrong-life adapter, twin/binding-swapped adapter, and
complete cited-memory cuts.

The strongest reasoning-policy sentinel is:

> `COGNITIVE_NO_ACT` improves held-out action although it never trained on a
> successful final action target.

The strongest connected-experience sentinel is:

> `LINKED` or `JOINT` beats endpoint/atoms-only on fresh compositions, and the
> credited gain disappears under path-order shuffle, cited cuts, or authentic
> binding/twin substitution.

Targets must be sealed before sleep, use whole-program/world splits and fresh
handles, contain no target-derived training bytes, and require a new
composition rather than reproduction of a stored terminal answer.

## 8. Claim-to-assay map

| Potential claim | Required assay/evidence | Insufficient evidence |
|---|---|---|
| The adapter changes later decisions | same-state `JOINT on - off`, plus wrong-life/twin swap | arm-level score difference alone |
| Public reasoning policy was learned | `COGNITIVE_NO_ACT > NO_SLEEP` with fixed evaluation compute | endpoint action cloning |
| Ordered pathways matter | `JOINT > PATH_SHUFFLED` | more training tokens or prose quality |
| Authentic outcomes select learning | authentic `JOINT > OUTCOME_SHUFFLED` | model self-confidence |
| Connected experience matters | `LINKED > ATOMS_ONLY`, fresh composition, cited cut/twin redirection | exact fact recall |
| LoRA transports useful compiled experience | LoRA within registered margin of `TEXT_SAME_CORPUS`, adapter cut/swap sensitivity | candidate construction or explicit graph success |
| Compression supports development | fixed adapter capacity, new/old/cross-era value across at least three post-context checkpoints | one small checkpoint or growing replay text alone |
| Full flywheel works | memory changes information action, which changes evidence, next sleep, and later action | fixed common-deck attribution |

## 9. CompilerGym versus controlled-world boundary

CompilerGym is a strong external agency assay: outcomes are cheap and
objective, actions can hill-climb, and `COGNITIVE_NO_ACT`, endpoint, joint, and
path-shuffle conditions can reveal learned search dispositions. It cannot by
itself prove higher-order connected experiential knowledge because generic
pass preferences or state-pattern imitation may explain transfer.

Use a paired controlled world such as RML/PCFL for the semantic claim. It can
seal new compositions, force one- through multi-hop dependencies, create
counterfactual twins with identical superficial marginals, remove cited
connections, and require prospective confirmation of schemas. The paper needs
both roles:

```text
CompilerGym: real hill-climbing utility and reasoning-policy transfer
RML/PCFL: causal connected-memory, shortcut, schema, and twin/cut attribution
```

## 10. Proposed 7B implementation order

1. Reuse the existing typed thinker transition machine and causal trajectory
   contract; replace domain-specific actions/queries without weakening their
   one-operation, citation, hash-chain, and failure semantics.
2. Build a no-model CPU fixture proving context rendering, eviction/recall,
   operation parsing, state transitions, prediction-before-action, provenance,
   and exact replay.
3. Build deterministic eligibility and admission over synthetic public traces;
   prove that false, post-outcome, cross-life, unsupported, and self-supported
   proposals cannot reach training rows.
4. Render runtime-identical READ/DECIDE rows and verify loss masks token by
   token. Do not train free-form principles or raw thoughts.
5. Run a Qwen2.5-7B marker/operation and one-hop-read canary before LoRA.
6. Train `ENDPOINT`, `COGNITIVE_NO_ACT`, `SEMANTIC_ONLY`, `JOINT`, and the two
   shuffled adapters from one frozen development life. Proposed starting
   recipe: rank 16, alpha 16, `q_proj/v_proj`, bf16, AdamW `5e-5`, eight fixed
   effective touches per accepted row, cumulative clean-base rebuild.
7. Execute a small CompilerGym held-out scout under fixed operation and action
   counts. Promote only if joint/pathway behavior is measurable and parser/
   action validity remains healthy.
8. Transfer the unchanged public THINK/SLEEP interfaces to the paired
   controlled-world assay before making connected-experience claims.
9. Only after fixed-deck attribution passes, run the on-policy two-arm life and
   measure whether learned policy changes information acquisition, subsequent
   accepted experience, and later action.

This ordering answers the immediate scientific question with the fewest GPU
hours while keeping the mechanism capable of growing into the full Experience
Model thesis.
