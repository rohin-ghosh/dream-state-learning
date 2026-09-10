# Experience Model v6: identifiable conscious-context/state contract (candidate)

**Status:** design input only; not an implementation or GPU authorization.

## Decision

Use one pinned model in one recurrent decision loop.  A decision consists of
`ORIENT -> fixed retrieval -> THINK_ACT -> public result`; `ORIENT` and
`THINK_ACT` are invocation states of that *same* model, with the same base,
tokenizer, bootstrap, sampling family, and (in treatment) mounted life LoRA.
There is no learned router, critic, retriever, planner, sleeper, or hidden
prefix/KV state.

**Recommendation: call ORIENT before every THINK_ACT.**  It may return
`KEEP` and zero queries, but is not event-triggered.  An event-triggered
ORIENT needs an additional trigger/scheduler policy and makes missed
re-orientations a hidden causal difference.  Calling it on every decision is
the small, auditable version of “think what to think, then think/act”; both
arms pay the same call/token budget.  A later cadence ablation may replace
this only with a frozen deterministic rule.

SLEEP is a non-cognitive write boundary in v6: deterministic selection,
rendering, clean-base training, and atomic adapter publication.  It does not
call a second model or grant truth to a self-authored thought.

## Authoritative state and exact packet

All state below is structured, canonical-serialized, size-bounded, and
assembled afresh for every model call.  Values ending in `_CAP` are frozen,
hashed run-manifest constants, counted with the pinned tokenizer, and include
their field labels.  Omitted fields and free-form extras are invalid.

```text
ContextPacket {
  packet_version, invocation_id, invocation_state: ORIENT | THINK_ACT,

  anchor: {
    experiment_id, life_policy_hash, base_model_hash, tokenizer_hash,
    bootstrap_hash, action_grammar_hash, tool_registry_hash,
    context_caps, public-feedback-schema_hash
  },

  life: {
    paired_life_id, task_id, task_ordinal, task_state_version, sleep_index,
    life_progress: {completed_tasks, valid_actions, best_valid_score}
  },

  clock_budget: {
    life_environment_cost_ms, task_environment_cost_ms,
    model_calls: {used, remaining}, model_tokens: {input_used, output_used,
      remaining}, tool_calls: {used, remaining}, environment_steps: {used,
      remaining}, retrieval: {queries_used, queries_remaining,
      tokens_remaining}, notebook: {tokens_used, tokens_remaining},
    next_sleep_rule, next_sleep_distance,
    last_operation_cost: {environment_cost_ms, input_tokens, output_tokens,
      tool_calls, environment_steps}
  },

  focus: {
    focus_revision, objective_ref, subgoal, active_question, strategy,
    success_or_stop_condition, reason, open_uncertainties[]
  },

  environment: {
    public_problem, public_observation, public_legal_actions,
    task_best_valid_score, task_outcomes_summary, task_workspace_manifest
  },

  recalled_experience: {
    prior_context_record_ids[], query_results[]
    # each result is {record_id, source: LEDGER | NOTEBOOK, payload,
    #                 provenance_ids[]}; canonical order and per-result/total
    #                 caps are frozen.  No retrieval score or hidden metadata.
  },

  recent_tail: [
    {event_id, state, parsed_output_or_public_result, resource_cost}
    # chronological, complete events only, suffix selected by a fixed token cap
  ],

  response_contract: {required_schema, one_operation_only, malformed_cost}
}
```

`ANCHOR` is immutable.  `CLOCK_BUDGET` is owned by the harness, never by the
model; it exposes logical environment cost and remaining resources, not future
tasks, target scores, or hidden evaluator data.  It never exposes provider
latency, adapter loading, training duration, cache warmth, retries, or a
condition marker.  This supplies the requested time intuition: slow-correct
and fast-correct outcomes are both public records with their measured resource
cost.  The model cannot alter a clock field to buy itself time.

`FOCUS` is the small explicit working-state bridge between the two invocation
states.  Only a schema-valid ORIENT output may replace it.  It is not a second
memory: it is capped, task-local, visible in the event ledger, and reset at a
task boundary.  `RECENT_TAIL` is an auditably selected suffix, never a
provider-maintained chat history.

`paired_life_id` is the same arm-blind identifier in paired conditions.
Neither an arm label, adapter status/hash, training receipt, or sham-write
marker is model-visible; adapter selection happens below prompt assembly.

For ORIENT, `query_results` contains only the prior packet's carried record
IDs/payloads (or is empty); it cannot smuggle a fresh full retrieval into the
context-selection step.  ORIENT emits a bounded `ContextPlan`, the harness
runs the plan through the common retriever, and the resulting THINK_ACT packet
contains the new results.  For THINK_ACT, the packet is otherwise identical.

```text
ContextPlan (ORIENT output) {
  focus: {subgoal, active_question, strategy, success_or_stop_condition,
          reason, open_uncertainties[]},
  recall: [{source: LEDGER | NOTEBOOK, query, kind, limit}] <= RETRIEVAL_CAP,
  handoff: THINK_ACT
}

Operation (THINK_ACT output) {
  type: INSPECT | TOOL_CALL | ENV_ACT | NOTE_APPEND | FOCUS_REVISE | STOP,
  args: canonical arguments for the frozen tool/environment registry,
  expected_public_effect: bounded text
}
```

`TOOL_CALL` includes only registered task operations (including bounded
task-workspace file read/write); `ENV_ACT` is a legal CompilerGym action;
`NOTE_APPEND` is the only life-persistent user-authored external write;
`FOCUS_REVISE` performs no tool/environment action; `STOP` closes the task.
An operation is one atomic call, even if malformed; malformed output consumes
the declared call/token budget and creates a public event.  “Reflection” is
therefore ordinary `ORIENT`/`FOCUS_REVISE`, not an uncounted operation.

## Persistence and reset map

| Boundary | Persists | Resets / prohibited carry |
|---|---|---|
| Token / model call | Parsed output and its sealed event only. | Activations, KV/prefix cache, hidden reasoning scratchpad, provider conversation, sampling/RNG stream, and unparsed output. A fresh call uses the packet above. |
| Within task | `FOCUS`, bounded recent tail, current public environment state, task workspace, task-local tool results, and the declared budget counters. | No raw chat transcript beyond `RECENT_TAIL`; no undeclared cache, shell history, model-server session, or mutable prompt prefix. |
| Task boundary | Immutable `ANCHOR`; append-only life ledger; declared bounded notebook; frozen retrieval index over those sources; treatment adapter checkpoint; life/global budgets. | `FOCUS`, tail, task workspace, CompilerGym instance, task tools/files, task RNG, task best score, task-specific retrieval cache, and all process/KV/compiler/autotune caches. |
| Sleep boundary (at a frozen task-boundary schedule) | Sealed ledger/notebook prefix; shared static retrieval index; adapter checkpoint in LORA only; immutable sleep receipt. | Trainer process, optimizer moments, gradients, data-loader/cache, temporary corpus, and all inference processes/KV.  The adapter is rebuilt from clean base plus the sealed cumulative corpus using a fresh optimizer, then atomically mounted only after success. |
| Life boundary | Pinned base/anchor and global experiment configuration only. | Adapter (null), ledger, notebook, retrieval/index state, task/sleep counters, prompt-derived state, trainer state, files, caches, RNG lineage, and all progress.  No cross-life or cross-arm reads. |
| Sterile evaluation fork | Read-only base + one declared adapter checkpoint + sealed target packet. | On exit, every target outcome, generated artifact, cache, notebook write, retrieval state, and process is destroyed/quarantined; nothing returns to acquisition or SLEEP. |

## Full-harness parity without a hidden second life

The primary pair is deliberately not `LoRA` versus a memoryless prompt.  Both
arms have the same:

- base/bootstrap, packet assembler, ORIENT and THINK_ACT calls, sampling,
  clock, task order, action/tool budget, CompilerGym feedback, and task-local
  files/tools;
- append-only public `LEDGER` of complete thought-plan-operation-result events;
- bounded, auditable `NOTEBOOK` and fixed `LEDGER/NOTEBOOK` retriever,
  including the same query count, result cap, token cap, and write cap; and
- SLEEP schedule and deterministic compiler/training computation.  HARNESS
  performs a sham write but keeps resulting adapter bytes in a model-invisible
  quarantine; LORA atomically mounts its corresponding bytes.

Given the same authoritative history (the adapter-on/off and common-history
tests), the only model-visible causal difference is the mounted LoRA weights
(a null adapter in HARNESS); the packet itself contains no arm or checkpoint
marker.  In paired on-policy lives, later public histories may diverge only as
downstream consequences of that intervention and must never cross arms.  The
external notebook makes the harness a credible modern agent, but it is
*declared* rather than hidden: it is bounded, append-only, exposed only through
the common retriever, its writes are typed operations, and it resets with the
life.  Arbitrary durable paths, shell history, self-modified prompts, learned
retrieval embeddings, semantic databases, optimizer state, and server caches
are forbidden.  If a future baseline needs a richer external-memory organizer,
make it a separately named arm with the same declared interface and budget; do
not silently add it to HARNESS.

The audit requirement is a cold-load replay: in a fresh process with only the
pinned base, one serialized adapter (or NULL), `ANCHOR`, and the current task
packet, reproducing the adapter-on/off difference.  The ledger, notebook,
training corpus, optimizer, task workspace, retrieval index, and all caches
must be absent.  This tests adapter necessity; the on-policy paired lives test
the complete organism under the shared external-memory channel.

## Minimal recurrence

```python
while not task.closed and budget.allows_decision():
    orient = call(base_plus(life.adapter), packet(state, ORIENT))
    plan = parse_or_charge(orient, ContextPlan)
    state.focus = plan.focus
    recalled = common_retrieve(plan.recall, state.ledger, state.notebook)
    act = call(base_plus(life.adapter), packet(state, THINK_ACT, recalled))
    op = parse_or_charge(act, Operation)
    result = execute_one_registered_operation(op, task, state)
    append_sealed_public_event(state.ledger, orient, plan, act, op, result)
    charge_authoritative_clock(state, result)

if task_boundary_and_sleep_due(state):
    corpus = deterministic_compile(sealed_prefix(state.ledger))
    candidate = train_clean_base_with_fresh_optimizer(corpus)  # treatment bytes
    atomically_publish_or_record_sham(candidate)
    cold_reset_runtime_state()
```

The compiler can select only sealed public records; any hypothesis/rationale
is input/audit text unless a frozen later public outcome rule makes its paired
operation loss-bearing.  This context contract does not itself choose the row
objective, LoRA recipe, score, or CompilerGym pin; those remain separate
ratification bytes.

## Invariants

1. **One recurrent model:** every cognitive token in both states is generated
   by the same frozen model family and one bootstrap.  `ORIENT` can select
   context but cannot act; `THINK_ACT` can act but cannot bypass the packet.
2. **One treatment-only learned inference object:** within a life, only the
   mounted LoRA may carry adaptive parameter state.  Fresh-optimizer
   cumulative rebuild means optimizer moments never survive sleep.
3. **Explicit nonparametric memory:** ledger, notebook, and retrieval are
   allowed only as declared common channels; no arbitrary persistent artifact
   is model-readable.  Their existence is reported, not attributed to LoRA.
4. **Reconstruction:** every call prompt is a pure function of canonical
   authoritative state, frozen constants, and (for LORA) serialized adapter
   bytes.  No hidden conversation/prefix state may affect output.
5. **Time/budget truthfulness:** only the harness updates costs and remaining
   budgets.  Each model/tool/environment call has a receipt and one charge.
6. **Boundary isolation:** a life/fork reset removes every state listed in the
   map; evaluation is not experience.  A stale process/cache is a test failure,
   not an optimization.
7. **Parity:** any model-visible file, tool, retrieval result, cap, or sleep
   call visible to LORA is visible under the same rule to HARNESS, except the
   mounted adapter bytes.  Any exception defines a new arm.
8. **No private-thought endpoint:** raw thought and focus may be diagnostic or
   training provenance, never correctness labels or headline evidence.

## Open tradeoffs and recommendation

| Choice | Tradeoff | Recommendation |
|---|---|---|
| ORIENT every decision vs event-triggered | Always costs a call; events require a scheduler and make the conscious-state transition less identifiable. | Always; ablate only later with a frozen cadence. |
| Shared notebook vs ledger-only | Notebook gives HARNESS realistic external-memory strength but can shrink a LoRA advantage and adds a declared carrier. | Keep a small capped notebook in both arms; report adapter-on/off and external-memory comparisons separately. |
| Fresh prompt reconstruction vs KV persistence | Reconstruction costs tokens/latency; KV persistence is uninspectable state. | Reconstruct for v6; cache reuse only after a cache-equivalence/isolation ablation. |
| Deterministic SLEEP vs model-generated sleep thinking | Deterministic SLEEP is less expressive but avoids a new, poorly credited cognitive path. | Deterministic v6 SLEEP; study same-model sleep cognition only as a separately controlled extension. |
| Task-local focus vs cross-task agenda | Cross-task agenda may help planning but becomes another durable behavioral memory. | Reset focus at task boundaries; persist only typed ledger/notebook records and adapter. |

This contract supports a narrow causal statement about outcome-grounded adapter
state under matched full-harness resources.  It does not by itself establish
consciousness, general intelligence, a long-life growth curve, or superiority
to all external-memory agents.
