# R127 route transfer reducer contract — 2026-09-15

## Scope and integration

CPU-only descriptive sidecar. No model, GPU, provider, network, Git, source-store
generation, checkpoint selection, learning, FINAL access, or recursive file discovery.
This implements the requested analysis boundary, not a new scientific claim.
Main owns production, provenance verification, capture persistence and COMPLETE
receipts. Existing canonical tasks, prompts and episode behavior are unchanged.

Use `from gpu.orch_r127_route_transfer_reduce import compare, document_sha256`;
then `result = compare(plan, groups)` with JSON-compatible dictionaries.
`groups` maps each condition to a list of normalized original episode dictionaries.
Optional keyword-only `bootstrap_samples=2000, seed=0` controls CPU uncertainty
calculation (at least 100 resamples). The pure API performs no file IO. Main may
load `root/<condition>/EPISODE_*.json` after checking COMPLETE hashrefs and write
the returned result to an exclusive new output file. There is no reducer-owned
filesystem format or extra live SEED evaluation.

Production panel: 16 prospectively deterministic fresh public held worlds, exactly
two tasks/world (32 episodes/condition); seven conditions: `SEED`, `GUIDED_C2`,
`GUIDED_C4`, `GUIDED_C6`, `UNPARENTED_C2`, `UNPARENTED_C4`, `UNPARENTED_C6`.
One fixed initial-generated event store is shared by every condition. Main owns
the **128-call source cap** (16 worlds × 4 edges × ROUTE+EVENT), 1344-call
evaluation cap (7 × 32 × 6), **1472 total-call cap**, generation cap 512, fresh
evaluation processes, and no parent/optimizer/sleep rules. Accepted child-written
raw event text is shared; failed source records remain unavailable and worlds
are never filtered. No reasoning demand is added: use original `rich.SYSTEM`
with `guided.episode(..., parent=None, rich_contract=False)`.
The reducer permits smaller complete two-task/world panels for standalone tests;
production should set `world_count: 16`, which is checked exactly.

## Plan fields

```json
{
  "evaluation_split": "fresh_public_held",
  "prospective": true,
  "world_count": 16,
  "initial_state_sha256": "<64 lowercase hexadecimal characters>",
  "source_store_sha256": "<64 lowercase hexadecimal characters>",
  "source_ready": true,
  "store_size": 64,
  "conditions": {
    "SEED": {"checkpoint_state_sha256": "<initial state hash>", "cycle": 0, "updates": 0},
    "GUIDED_C2": {"checkpoint_state_sha256": "<state hash>", "cycle": 2, "updates": 112}
  },
  "tasks": [
    {"world_id": "<fresh world ID>", "task_id": "<ID unique within world>",
     "task_sha256": "<task object digest>",
     "initial_prompt_sha256": "<initial messages digest>"}
  ]
}
```

The example abbreviates `conditions` and `tasks`; all seven conditions and the
full task panel are mandatory. Each checkpoint entry contains its fixed cycle
index and **actual cumulative historical update count**, not a nominal matched
dose. Additional provenance/dose fields (such as experienced episodes, fits,
parent calls and original receipts) are preserved in the output checkpoint
metadata. SEED must match `initial_state_sha256` with cycle/update count zero.
Cycle indices are fixed 2/4/6, never selected by observed scores.

`source_ready` is the producer's boolean readiness/completion attestation for
the frozen shared store, **not** a claim that every source event succeeded.
`store_size` is the actual nonnegative number of accepted event-address entries
(including zero). Both are mandatory and explicitly reported in the reduction.
A ready but sparse/empty store does not justify filtering worlds or attributing
unavailable-memory failures to learning. These are producer-verified metadata;
the pure reducer does not reconstruct store contents or infer failed-source counts.

Every normalized episode is the original episode dictionary with these fields
added: `condition`, `world_id`, `task_id`, `task_sha256`,
`checkpoint_state_sha256`, `initial_prompt_sha256`, `source_store_sha256`,
`trainingAllowed: false`. Retain `task`, **every ordered capture** (including
failed calls), `reads`, `routes`, final `messages`, `parent_messages: []`,
`actor_calls`, `terminal_reason`, and `correct`. Captures retain `messages`,
`response` (possibly null), `command` (possibly null), and `error` if recorded.
Original `turn`, `student_prefix`, `prior_reads` and other fields can remain.
Missing `error` telemetry is UNKNOWN, not a successful action.

Digest convention for task and prompt objects matches the **prospective R127**
producer `gpu/orch_r127_route_transfer.py` (also R124): SHA-256 over UTF-8
`json.dumps(value, sort_keys=True, separators=(',', ':'))`, with compact
separators and default ASCII escaping. This deliberately differs from historical
R118's spaced JSON convention; no historical captures are altered. The reducer
rejects NaN/Infinity. Initial prompt means
the complete first call's `captures[0].messages`, including system and user
messages. Only this initial prompt must match across conditions: later messages
naturally depend on the action trace. Source-store and checkpoint hashes are
opaque preverified identity hashes, not recomputed from local artifacts here.

The reducer rejects absent/malformed/mismatched task, checkpoint, initial-prompt
or source-store hashes; recomputes actual task and first-message digests; checks
all records against the common plan panel and condition checkpoint; rejects
missing/duplicate/extra episodes, repeated task content, inconsistent world
counts, wrong cycles, parents or `trainingAllowed != false`. Full capture length
must equal `actor_calls` and be 1–6. If error flags are complete, native accepted
`reads` must exactly match successful READ commands in the capture trace.

**Trust boundary:** Main verifies COMPLETE file hashrefs, loaded adapter identity,
actual event-store bytes and initial-generation provenance, exclusion/freshness
receipts, public-only information visibility, fixed decoding settings, task/world
construction and absence of training. Hash agreement and producer attestations
alone do not independently prove these facts. No reading of historical results
or FINAL data is needed or permitted by this interface.

## Measures and missingness

All counts are per episode unless explicitly labeled otherwise. Every capture
is considered, not just admitted actions or successful tasks.

- `reads_before_first_route`: number of READ attempts before the first ROUTE
  attempt, including any rejected reads; null if no ROUTE was attempted.
  `any_read_before_first_route` is 0/1 on the same opportunity denominator.
- `read_attempts`, `repeated_read_attempts`: all READ commands; repeats count
  occurrences after an address's first occurrence within the episode, including
  rejected repeats. `accepted_reads` requires observed error flags and matches
  the native accepted-read list. These are **evidence-access proxies**, not
  evidence quality, availability, semantic use or latent metacognition.
- `unavailable_memory_reads` and `supplied_memory_reads`: successful READ feedback
  identified in the exact public conversation prefix, assistant raw reply, and
  following user message. Literal canonical `MEMORY UNAVAILABLE` counts as
  unavailable; other delivered text counts as supplied, not semantically used
  or correct. Missing/unjoinable feedback makes these counts null; zero accepted
  reads yields zero. This keeps source availability visible alongside outcomes.
- `route_attempts`, `action_calls`, `rejected_action_calls`, `missing_responses`:
  literal trace/validity counts, not judgments of reasoning quality.
- `prompt_tokens`, `generated_tokens_including_eos`, `generated_text_tokens`,
  `truncated_responses`, `terminal_responses`: sums over the full trace. EOS-
  inclusive length uses actual `token_ids`; text count requires the producer's
  `generated_text_tokens`. No missing token or truncation value is imputed as
  zero. If any call lacks a field, that episode's aggregate is null, with
  observed/missing/total call coverage retained. Prompt tokens are repeated
  model-input processing counts, not distinct context tokens.
- **SECONDARY** `task_completed`: natural environment terminal (`reached_goal`
  or `dead_end`) versus call cap/error; not equivalent to success. **SECONDARY**
  `correct`: exact native boolean success. Missing terminal/outcome is null.
- `supplied_evidence_content_use`: UNKNOWN/null. Reading an address, mentioning
  evidence, or a successful outcome does not establish semantic evidence use.
- `environment_feedback_reaction`: UNKNOWN/null, not zero. The original
  canonical episode ends on invalid command/capture error; there is no subsequent
  learner recovery opportunity. No post-error behavior or correction is inferred.

## Pairing, uncertainty and claim boundary

All seven conditions must cover identical `(world_id, task_id)` keys. For each
metric average the two tasks **within each world first**. A world is eligible
only if both tasks have observed values. For a contrast, keep only worlds with
complete metric coverage on both sides, then calculate left-minus-right world
differences. Report every world difference, paired/excluded world counts, mean,
sample-SE over world differences and pointwise 95% percentile bootstrap intervals
resampling whole paired worlds. Fewer than two eligible worlds gives null SE/CI;
no eligible worlds also gives null mean. Never treat 32 episodes as 32 independent
units. For counts, condition means are world-balanced mean episode counts, not
total counts. Per-episode metrics and telemetry coverage remain available.

Report nine fixed contrasts: GUIDED minus UNPARENTED at each of C2/C4/C6, and
each of those six historical checkpoints minus the single SEED condition. SEED
episodes are reused, not counted as additional independent observations.
No pooling of checkpoint contrasts or selection of the best checkpoint. Repeated
checkpoint observations and contrasts are correlated. Intervals describe fresh
world variability conditional on these fixed trained systems and shared store,
not independent training-seed or source-store-generation uncertainty; they are
not multiplicity-corrected hypothesis tests.

Historical unequal GUIDED/UNPARENTED doses remain an
**observational systems comparison, not an isolated parenting-content effect**.
This is **fresh-world same-family generalization, not a new task family**.
Outcomes are secondary. Validity, repetition and evidence-access counters are
operational behavior proxies, not latent metacognition or measured reasoning
quality. The reducer sets `causal_claim: false` and makes no promotion decision.

## Schema sources inspected (source only)

- `gpu/orch_r118_frozen_seed_reference.py`: fixed initial-adapter identity,
  historical task JSON hashing, per-group EPISODE/COMPLETE records and parent-free
  `rich_contract=False` evaluation.
- `gpu/orch_route_parent_campaign_run.py`: generation token telemetry and native
  learner capture serialization.
- `organism_v6/orch_route_parent_campaign_canonical.py`: two sequential tasks per
  world, historical dose metadata and proxy interpretation boundary.
- `organism_v6/orch_l2_guided.py`, `organism_v6/orch_l2_shared.py`,
  `organism_v6/orch_replication.py`: actual ordered capture/error/read behavior,
  task schema, and error termination rather than recoverable feedback.
