# R127 route transfer reducer contract — 2026-09-15

## Scope and integration

CPU-only descriptive sidecar. No model, GPU, provider, network, Git, source-store
generation, checkpoint selection, learning, FINAL access, or recursive file discovery.
This implements the requested analysis boundary, not a new scientific claim.
Main owns production, capture persistence and COMPLETE receipts. The separate
offline IO verifier below now verifies producer artifacts before invoking the
pure reducer. Existing canonical tasks, prompts and episode behavior are unchanged.

Use `from gpu.orch_r127_route_transfer_reduce import compare, document_sha256`;
then `result = compare(plan, groups)` with JSON-compatible dictionaries.
`groups` maps each condition to a list of normalized original episode dictionaries.
Optional keyword-only `bootstrap_samples=2000, seed=0` controls CPU uncertainty
calculation (at least 100 resamples). The pure API performs no file IO. The
separate results module reads the frozen producer's existing filesystem format;
it does not change that format or create an extra live SEED evaluation.

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

This section describes the **pure reducer's normalized plan**. The offline
results wrapper consumes the actual frozen producer PLAN/EXPORT/COHORT and
constructs this normalized plan only after every stage has verified.

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

## Bounded offline IO integration

`gpu/orch_r127_route_transfer_results.py` provides:

```python
from gpu.orch_r127_route_transfer_results import reduce

snapshot = reduce(plan_path, output, bootstrap_samples=2000, seed=0)
```

`plan_path` is an absolute path to the actual frozen producer PLAN. `output` is
a new JSON file in an existing directory, opened exclusively (never overwritten).
Pass `output=None` for a read-only in-memory progress snapshot. Repeated live
snapshots need distinct output filenames. The CLI accepts `--plan` and `--output`
and prints only status and output path. No current-time/deadline check is made:
an expired launch wall does **not** invalidate read-only offline reduction.
The producer's validation/launch functions are never invoked or imported by
the IO module; no model, tensor loader, GPU, provider, SSH or FINAL-data access
occurs. Local scripted canonical episodes in tests use fake responses only.

### Verification boundary

- Read exactly the supplied PLAN, its registered source files, bundle EXPORT,
  COHORT, copied historical sleep receipts, and seven exported adapter manifests.
  Check source hashes, historical runtime hashes, export-file hashes, exact fixed
  C2/C4/C6 selection, cumulative updates and copied checkpoint lineage. Adapter
  files are byte-hashed without loading tensors. Historical origin/exclusion
  paths are provenance references, **not opened** by this wrapper.
- Bind START to the PLAN hash. For SOURCE and each of seven evaluation conditions,
  verify LOADED and BINDING adapter state/base/file/path identity against the
  export, plan binding, parent-free/fresh-process flags, optimizer zero, LAUNCH
  PID, EXIT returncode zero/complete/no-retry, and COMPLETE unchanged/zero optimizer,
  parent calls and training rows. Process identities must be distinct and cannot
  reuse the supervisor PID. If TERMINAL is present at full completion, its status,
  zero-update flags and complete ordered EXIT list must also agree.
- Validate every COMPLETE call/episode hashref against its exact canonical local
  path and file bytes. Bound call and episode inventories must be exhaustive, not
  filtered subsets. Each call binds its claim, condition, message digest, cap512,
  no-retry and training prohibition. Require inference status COMPLETE and a full
  response whose embedded messages match the call messages. Flatten all ordered
  episode captures (or SOURCE-world captures) and join **full messages and full
  responses**, including token metadata, one-to-one to the call sequence.
- SOURCE COMPLETE.store must point to the exact `SOURCE/STORE.json` wrapper, not
  a bare-store assumption. Recompute the compact JSON hash of its `store`. Read
  all 16 SOURCE WORLD files; check collection self-hashes and planned world/edge
  bindings, every action/EVENT response join, and accepted child raw-text hashes.
  Reconstruct the store from accepted records and require exact equality. Verify
  accepted/offered event counts and complete-world counts. Rejected source records
  remain present and unavailable; readiness does not require all worlds complete.
  Every evaluation COMPLETE uses that same exact store file hashref, and every
  episode uses its recomputed content digest. No regeneration or world filtering.
- Enforce the full 16-world/32-task panel and all seven conditions. At full
  completion require globally contiguous charged claims, exact call/claim union,
  per-stage caps (SOURCE128, evaluation192) and total1472 cap. Rehash every read
  input before publishing complete analysis to catch mutation during reduction.
- Paths are confined to the declared source/bundle or exact producer artifact
  locations; reject traversal, substituted hashref paths and symlinked artifacts.
  Only bounded known-name directory inventories are used, not recursive discovery
  of experiment data. Outputs cannot overwrite inputs or be placed in the frozen
  bundle/source, stage or claim directories.

### Partial results and output

Every snapshot contains `status`, `stages` (SOURCE plus all seven conditions),
`source_ready`, `store_size`, `analysis`, safe error codes and input hashes/paths.
Stage status is `NOT_STARTED`, `INCOMPLETE`, or `VERIFIED`. Partial directories
report call/episode file counts; verified stages report counts and core receipt
hashrefs. A missing condition, missing receipt, nonzero exit, **failed inference**,
invalid hash or inconsistent join leaves global `status: INCOMPLETE` and
`analysis: null`. No subset contrasts are computed. A completed inference with
an invalid command or a truncated/nonterminal response is a retained behavioral
failure, not a failed inference. SOURCE validation may reject a response before
assigning the record's action/EVENT field; its full response is still retained
and joined through the collection capture, and that source record stays unavailable.

`source_ready: true` means the entire SOURCE stage and reconstructed store
verified, even if sparse; `store_size`, accepted/offered events and complete-world
count remain explicit. Analysis is invoked only after SOURCE and all seven
conditions verify. The compact output drops raw episodes, messages, responses,
token IDs, source text, per-episode rows and repeated per-world values; it retains
condition metrics, aggregate telemetry missingness coverage, paired-world counts,
uncertainty, dose metadata, provenance digests and claim limitations. Raw error
strings from artifact contents are never echoed. Missingness and uncertain
evidence-use/feedback measures retain the pure reducer's semantics.

This is receipt-and-file verification, not an independent rerun of checkpoint
training, tensor-state recomputation, namespace exclusion construction or model
execution. It does not turn historical observational comparisons into causal
parenting effects. The producer remains frozen and unmodified.
