# Long-sequence dream/think LOOP-adapter pilot (inactive contract)

Status: design-only. This file does not authorize a run, GPU allocation,
remote sync, workflow edit, or modification of any active research-loop state.
It translates research notes 35, 41, and 42 plus the v0.2 thinker traces into
the input contract for a later, separately reviewed pilot.

## Scientific boundary

The lifetime MEMORY adapter stores what happened and what structure one life
supports; it is fast state and resets for every `(world_id, skin_id, life_id)`.
The LOOP adapter learns reusable operations—retrieve/query, hypothesize,
revise/revisit, plan, act, defer, release, and stop—across lives. It is shared
across training worlds and frozen before each evaluation life. A model-visible
trajectory may contain public observations and tool/environment results, but
never the hidden answer, hidden parent/role truth, proof graph, FactorSolver,
or evaluator labels/verdicts.

## Record format

Every JSONL trajectory has `schema_version`, `trace_id`, a required whole-world
`split` and `split_id`, `world_id`, `skin_id`, `life_id`, both adapter IDs, and
delayed scorer-side outcome (`success`, `efficiency`, and optional return/cost).
Its `records` list is append-only and consists of complete four-record causal
transitions:

```text
PUBLIC_STATE -> ASSISTANT_OPERATION -> TOOL/ENV_RESULT -> NEXT_STATE
```

Each record carries a unique `record_id`, `transition_id`, `prev_record_id`,
the same world/skin/life identity, provenance (`source_ids` and optional
parent IDs), `model_visible`, `tokens`, and a same-length binary `loss_mask`.
Only `ASSISTANT_OPERATION` tokens may have mask `1`; state, user/goal, tool,
environment, and scorer tokens are context with mask `0`. Operations are
typed and auditable: `QUERY`/`RETRIEVE`/`REVISIT` carry a query object and
`ACT` carries an action object. Direct `ANSWER` is not a loop target.

The validator in `research_loop/trajectory_contract.py` enforces this causal
shape, identity/provenance scope, leakage denylist, required split IDs, and
adapter lifecycle. `training_tokens()` is the sole intended extraction path
for the controller loss.

## Source curriculum and provenance

Preserve every v0.2 exhaustive 57-branch × two-proof-leaf trace, including
failed branches, public evidence IDs, prompts/raw completions, query costs,
revisit choices, delayed outcome, efficiency, world fingerprint, and skin.
Convert compact legacy tuples such as `("MEMORY", query, result)` into the
four phases without inventing hidden labels. Keep raw legacy artifacts in a
scorer-side archive; never copy their final answer, hidden parent/role,
FactorSolver result, or proof graph into `PUBLIC_STATE`, operation targets,
or any masked model input. Depth-2+ memories must cite earlier public memory
IDs. Provenance is for audit and attribution, not an oracle read plan.

## Learning ladder and gates

1. **Behavior cloning (BC).** Start with scripted/exhaustive teacher traces;
   curriculum is parent ranking, then check/revisit, then 8–16 operation
   loops, then multi-target/multi-world streams. Train on complete development
   worlds for QLoRA ranks under review (the notes suggest 8/16), with whole
   held-out worlds for evaluation and no teacher forcing at test time.
2. **Rejection-SFT.** Only after BC beats the frozen generic/top-k loop on
   unseen worlds at a matched operation budget, sample the untrained or BC
   policy, retain successful and efficient traces using an offline scorer,
   and SFT only the cognitive/action tokens. The scorer's success/efficiency
   is delayed metadata and never a model-visible label.
3. **Preference training (optional).** If rejection-SFT has useful diversity
   but poor ranking, compare successful/efficient versus failed/wasteful
   trajectories at equal public state and operation budget. Do not train on
   evaluator verdict strings.
4. **RL/GRPO or actor-critic (optional, later).** Use only if supervised
   distillation fails to explore. Its critic estimates delayed progress and
   compute cost; it is not a thought verifier. Any on-policy change requires
   a new reviewed plan and leakage audit.

## Held-out-world criteria and promotion gates

Split by complete world seed/family, never cells or individual goals. A world
ID may belong to exactly one split; aligned, neutral, and conflicting skins
remain separately reported. Tune prompts, formats, and exposure on development
worlds, then freeze them. Evaluation keeps the LOOP adapter shared/frozen and
creates a newly initialized or null MEMORY adapter per life; no gradient, KV
cache, or episodic state may cross an evaluation world.

The first promotion gate is an unseen-world proposal success@12 improvement
of at least 0.15 absolute over the frozen generic/top-k loop, with no more than
half the exhaustive atomic calls and no D3 regression. Report success@1/2/4/8/12,
exact parent/revisit quality, atomic calls/tokens, stop calibration, delayed
efficiency, and final D3 separately. Expand only after this gate to five
held-out seeds and Action World A1/A2/A3 transfer with real feedback.

Required controls include prompt-only generic loop, random ranking at matched
checker/call budget, proposal-only SFT, shuffled candidate/result order,
exhaustive teacher ceiling, and a direct trajectory-to-answer SFT leakage-positive
diagnostic that is never a headline condition. Fail the reusable-loop claim if
the gain disappears under whole-world/skin splits, depends on seen names/order,
teacher forcing, extra compute, or a non-reset memory adapter.
