# v6 Sleep compiler candidate: outcome-grounded action replay

Status: **candidate for deliberation only**. It neither ratifies an
implementation nor authorizes a CompilerGym install, a model run, or a
scientific claim. It deliberately keeps SLEEP non-cognitive: the frozen wake
loop produces public typed records; SLEEP only hashes, partitions, credits,
deduplicates, renders, and trains.

## Scope and invariant

There is one frozen model/bootstrap/action grammar and, in the treatment, one
life-local LoRA mounted on that same forward pass. `ORIENT`, `ACT`, and
`REVISE` are prompt states of that one loop. The public ledger, task workspace,
retrieval index, compiler cache, trainer checkpoint, RNG stream, and model/KV
cache are not a second learned life state: they are erased at their declared
task/sleep/evaluation boundaries. At inference the only adaptive bytes that
cross a sleep are the serialized LoRA.

The narrow first question is: from one sealed acquisition prefix, do the
authentic adapter bytes improve *held-out, correctness-gated CompilerGym
actions* relative to the same checkpoint with the adapter removed, and does
breaking the action--outcome binding remove that effect? It is not a test of
private thought quality, consciousness, a universal learning law, or LoRA
superiority to a strong external-memory agent.

## Canonical public ledger

The ingestor appends one canonical JSON record per model decision and one
terminal record per task. All IDs are SHA-256 hashes of canonical JSON; arrays
are sorted where their order is not causal. `*_hash` fields are audit keys, not
model-visible fields. No hidden test, reference score, target-panel metadata,
compiler cache path, adapter identity, or evaluator artifact enters a record.

```text
DecisionRecord v1
  schema_version: "em6cg-decision-v1"
  life_id, acquisition_task_id, task_ordinal, episode_id, decision_ordinal
  parent_decision_id | null                 # previous public decision
  state_before: {
    anchor_version, clock: {calls, env_steps, token_budget_left,
                            action_budget_left, sleep_index},
    public_observation, legal_action_projection,
    public_current_best, recent_event_ids, recalled_record_ids,
    focus_before                              # typed bounded packet
  }
  orient_output: {focus_after, reason_tag} | null
  thought_projection: {hypothesis_id?, prediction?, uncertainty_tag?,
                       requested_evidence_ids[]} # bounded public typed fields
  action: {kind, canonical_arguments} | null
  action_parse: VALID | MALFORMED | NONE
  official_outcome: {
    dispatch: NOT_SENT | SENT,
    result: PENDING | VALID | INVALID | TIMEOUT | ERROR,
    public_reward, public_metric, public_best_after,
    resource_cost: {wall_ms, model_tokens, env_steps},
    public_observation_after
  }
  state_after_hash, record_id

TaskTerminalRecord v1
  life_id, acquisition_task_id, episode_id, ordered_decision_ids,
  terminal_status, best_metric, total_resource_cost, terminal_record_id
```

`public_metric` is the pinned gym's public deterministic objective (expected
to be LLVM-IR instruction-count reward after the unmodified-gym fit gate),
not a private runtime measurement. The public ledger retains every malformed,
invalid, failed, and successful call. The compiler cannot repair an unsealed
or indeterminate dispatch; that task/life cell is failed rather than
regenerated.

### Derived, target-blind objects

For each sealed task, the compiler derives the ordered best-so-far series
`B[-1], B[0] ... B[n]`, where invalid/timeout/error leaves `B` unchanged and
valid outcomes set `B[i] = max(B[i-1], public_best_after[i])`. A **candidate
unit** exists for every parse-valid ORIENT, action, and observed-failure
transition. Its `candidate_id`, static feature bucket, and dedup key use only
pre-decision public state, typed output/action, task ordinal, and canonical
observation/action hashes--never an outcome, best score, or later record.

The outcome-bearing **binding bundle** for a task is separately:

```text
{ordered official outcomes, B series, terminal metric, resource costs}
```

This separation is intentional: it makes outcome binding, outcome-conditioned
selection, and generic self-imitation independently testable.

## Credit contract

All credit is a mechanical label computed after a task is sealed.

1. **Immediate gain.** A valid action at `i` has `d_i = B[i] - B[i-1]`.
   It is an immediate improvement iff `d_i > epsilon`; `epsilon` is the
   public-metric resolution established by the gym canary.
2. **Delayed pass interaction.** Whenever `B[j] > B[p]`, with `p < j` the
   preceding index at which the old best was set, form segment `(p+1..j)`. For
   each parse-valid, valid action `i` in that segment, assign
   `segment_credit(i,j) = (B[j]-B[p]) * gamma^(j-i) / Z`, where `Z` normalizes
   over the valid actions in the segment. The last action receives most credit;
   setup passes receive nonzero, explicitly discounted credit. An invalid call
   never receives positive ACT credit.
3. **Failure then recovery.** A failure is `INVALID`, `TIMEOUT`, `ERROR`, or a
   valid action with no subsequent best improvement before the task ends. If a
   later segment achieves a new best, take the first action `k` after the
   failed record that belongs to that improving segment. The REVISE unit is
   `(state_before failure, official failure outcome) -> focus/action at k`.
   The failed action is quoted in input and is never its own positive target.
   Recovery credit uses the same segment formula, multiplied by `rho=0.5` in
   the scout so recovery does not swamp direct improvement.
4. **No invented counterfactual credit.** SLEEP does not rerun the compiler,
   infer causal necessity, write a theory, or label a non-improving action
   negative. Delayed credit is temporal eligibility, not a causal claim.

For the recommended scout, freeze `gamma=0.7` and `rho=0.5`; only `epsilon`
comes from the pinned gym's pre-run metric-resolution canary.

This admits temporary but valid setup passes while avoiding imitation of calls
known to be invalid or unrecovered. The temporal-credit window is task-bounded
and starts after the previous best, so it cannot reach into another task.

## Three loss-bearing views

Every rendered row has a frozen `SYSTEM/ANCHOR` prefix and a canonical public
state input. The loss mask is **zero** on system, clock, observation, recalled
IDs, prior thoughts, official outcome text, and delimiters; it is **one only**
on the typed assistant object named below. Free-form rationale is neither
required nor loss-bearing.

| View | Input | Assistant loss target | Eligibility |
|---|---|---|---|
| `ORIENT` | `state_before` at a focus change | `{"focus": focus_after, "reason_tag": ...}` | focus immediately precedes an ACT-credited segment or a REVISE target |
| `ACT` | `state_before` plus the fixed `focus_after` | `{"action": kind, "arguments": canonical_arguments}` | valid action with positive immediate or delayed segment credit |
| `REVISE` | pre-failure state, failed action, official public failure, and bounded intervening public events | corrected `focus_after` plus the first recovered valid action | failure has a later improving segment |

Each row carries `credit_bucket` only in the compiler manifest, never in the
model prompt. Sampling uses buckets `{high, medium, low}` derived from the
numeric credit; the target remains the original emitted operation. Thus the
model is trained to choose a useful operation from a state, not to parrot an
outcome description that will be unavailable when acting.

### Hypotheses and theories

A hypothesis/prediction emitted before an action may be quoted in the input as
provenance-bearing context. It is audit metadata by default and has zero loss.
It is never rendered as a positive target in this scout. The only permissible
way to make it loss-bearing in a later revision is a separately ratified view
whose target is a pre-outcome prediction and whose support is a predeclared
later public intervention--not wording judged persuasive after the fact.

This is deliberately conservative. The first assay should test whether a
life's public action experience improves future action, not whether it can
teach itself a preferred explanatory style.

## Deterministic compile and replay

For every sleep, the sealed ledger prefix and configuration hash uniquely
determine a manifest, rendered-token hashes, train order, and adapter receipt.

```text
compile(prefix, config, binding):
  assert prefix is sealed; validate schema, monotone record order, and no future IDs
  candidates = target_blind_candidates(prefix)
  labels = credit(candidates, binding, epsilon, gamma, rho)
  rows = render_only_eligible_views(candidates, labels)
  rows = exact_dedup(rows, key=(view, normalized_state, typed_target))
  # retain highest credit; break ties by earliest (task_ordinal, decision_ordinal)
  rows = stratified_top_k(rows, by=(view, operation_kind, static_feature_bucket),
                          quota=config.quotas, rank=(credit, novelty_hash, -time))
  corpus = replay_mix(previous_corpus, rows, config)
  return canonical_manifest(corpus, labels, all_candidate_ids, config_hash)

sleep(prefix):
  manifest = compile(prefix, config, authentic_binding(prefix))
  adapter = train_from_clean_base(manifest, reset_optimizer(config))
  atomically_publish(adapter, manifest, tokenizer_hash, trainer_receipt)
```

`static_feature_bucket` is computed only from public LLVM observation/action
features frozen before target sealing (for example, legal-action family and
public IR-shape bin); it is not a hand-labelled optimal motif. `novelty_hash`
is a deterministic hash tie-breaker, not an embedding or learned selector.

Recommended scout replay policy:

- Corpus cap: 192 total rows, at most 64 per view and 24 per exact static
  bucket; lossless manifest retains rejected rows and the reason.
- At sleep `s`, reserve 50% of capacity for retained old rows and 50% for new
  rows. If either side underfills, fill in canonical rank order from the other.
  Within old rows retain at least one row from each prior sleep before filling
  by credit. This is a preservation rule, not an adaptive priority.
- Deduplicate only identical normalized `(input,target,view)` rows. Do not
  collapse independently lived repeats: they remain as one row with a
  `support_count` capped at 3 and training multiplicity `min(3,support_count)`.
- The train order is a hash-sorted permutation seeded by
  `(life_id, sleep_index, manifest_hash)`. Token truncation is fixed by the
  tokenizer and recorded before training; no content-dependent retry,
  early-stop, or hyperparameter change is allowed.

## One recommended first-scout write recipe

This is a deliberately low-capacity, behavior-preserving mechanism recipe,
not a claim that rank 16 is intrinsically optimal.

```text
sleeps: after acquisition tasks 8, 16, and 24
adapter: LoRA r=16, alpha=16, dropout=0
targets: q_proj and v_proj in every transformer block only
precision: bf16; fixed deterministic implementation settings where available
optimizer: AdamW(lr=1e-4, betas=(0.9,0.95), weight_decay=0.01,
                 grad_clip=1.0), reset at every sleep
training: cumulative clean-base rebuild; 24 target-token touches per retained
          row (multiplicity applies before the 24-touch cap); batch/token
          packing, sequence cap, and update count fixed in the manifest
preservation: fixed pre-birth anchor prompts receive KL-to-frozen-base weight
              0.05; anchor prompts contain no life/task/target data and are
              identical in every adapter condition
publish: only base pin + serialized adapter + immutable manifest/receipt;
         optimizer, gradients, packed batches, and trainer cache are deleted
```

Clean-base cumulative rebuild is preferred over incremental updating because
it makes the current adapter a reproducible function of the selected lifetime
corpus, avoids hidden Adam moments, and lets later support/recovery evidence
change older replay selection. Its cost grows with corpus size; the 192-row cap
is the explicit first-scout tradeoff. Incremental adapter updates are a later
ablation, not a substitute: even with optimizer reset they have different
exposure and forgetting dynamics.

The small rank and `q/v` target set reduce actor/style drift. The exact capacity
response surface (rank, targets, retention) comes only after this recipe either
passes or fails under fixed controls; it must not be tuned on the two scout
lives. Historical evidence makes both under-exposure and overtraining plausible,
so every report must disclose effective touches, train tokens, rank, bytes,
KL, schema validity, and adapter-off performance.

## Outcome and transport controls

One generic shuffled adapter is insufficient. Derangements happen at the
**task binding-bundle level before credit, recovery eligibility, ranking,
quota filling, or row rendering**. Within each frozen stratum
`(sleep, view, action-kind, static-feature-bucket)`, deterministically cyclically
derange task bundles; use a larger declared parent stratum if fewer than two
exist. The same candidate superset, corpus cap, row quotas, tokenizer, train
updates, anchors, and seeds apply. A run fails its control construction if a
stratum cannot be deranged without a fixed point.

The minimum checkpoint fork set is:

| Condition | What it isolates |
|---|---|
| authentic adapter | full outcome-grounded compiler effect |
| authentic adapter-off | necessity of current adapter bytes, holding acquisition history fixed |
| binding+selection shuffled adapter | whether correct outcome-to-trajectory binding drives compilation; selection is intentionally recomputed under the wrong binding |
| authentic-selected self-imitation adapter | same selected action rows with outcome/recovery fields ignored after authentic selection; exposes useful code/style imitation leaked by selection |
| direct raw trajectory-to-action LoRA | whether compiler views/credit help beyond generic domain action SFT |
| identical compiled corpus as bounded text retrieval | transport diagnostic, not an ordinary-agent baseline |
| reciprocal wrong-life adapter | life specificity rather than generic kernel/style fine-tuning |

The binding-shuffled and self-imitation controls answer different questions;
neither may be described as the other. All are read-only cold-load forks from
the authentic sealed acquisition checkpoint. They do not answer the separate
on-policy question, for which treatment and harness lives must be independently
run with the same declared persistence policy.

## Recommended first scout

After an unchanged official CompilerGym LLVM pin passes installation,
semantics, deterministic-metric, and related-but-nonduplicate split canaries:

1. Run two *development-only* on-policy lives, 24 acquisition programs each,
   six public actions per task, and sleeps at 8/16/24. The harness has the same
   bootstrap, clock, recent-tail/retrieval budgets, tools, and public ledger
   projection but no write. Neither arm may retain task files/notes/caches
   across tasks; a separate later baseline may use declared bounded text memory.
2. Before any model call, seal a target panel built only from public static
   metadata: near-family nonduplicates, opposite-condition tasks, and
   compositions of acquisition-visible motifs. Enforce code/IR/shape/graph
   near-neighbor audits and keep target outcomes invisible to life, compiler,
   trainer, and split constructor.
3. At every sleep, cold-load the seven conditions above into sterile evaluator
   processes. Each target permits the identical action/call/token budget;
   evaluator outcomes are discarded. The final check includes base+adapter-only
   reproduction from a file allowlist and reciprocal wrong-life swaps.
4. Primary per-target score is public reward conditional on validity; report
   invalid/timeout as zero, first-action score, best-of-budget score,
   actions-to-best, early-panel retention, and checkpoint AUC separately.
   The unit is a life or target-within-life paired contrast for diagnosis, not
   a token/action as an independent sample. Two lives are wiring replications,
   not population evidence or a derivative estimate.

The scout is a pass-worthy mechanism observation only if both lives show an
authentic-minus-off held-out gain on the frozen primary score, the
binding+selection shuffle loses a preregistered material fraction of that gain,
and the decomposition below does not attribute the result to validity/style or
near-copy reuse. Exact margins must be chosen with the pinned gym's score
resolution and baseline variance, before launch.

## Diagnostics that separate learning from imitation

At every checkpoint, report the following alongside reward:

- validity/parse/compile rate before conditional speed; output length, action
  frequency, pass-family distribution, stopping/timeout rate, and KL to base
  on the fixed anchors;
- reward gains conditional on *matched valid actions*, first action, and
  actions-to-best, so fewer malformed outputs cannot masquerade as learning;
- target action/code nearest-neighbor similarity against the acquisition
  ledger, exact IR/code-hash exclusion, and a globally repeated-edit analysis;
- performance on sealed opposite-condition and composite targets versus
  near-family targets; a gain confined to nearest neighbors is reuse, not
  evidence of compositional transfer;
- an unrelated instruction/action-format preservation panel and adapter-off
  regression; a global style/grammar improvement or erosion is reported as
  such, not as experience learning;
- no-hypothesis-input and no-REVISE-view analysis on held-out forks, treated
  as mechanism localization rather than thought-quality scoring;
- adapter-only cold-load, wrong-life redirection, and same-corpus text results.

No metric scores rationale wording, agreement with a human theory, or a
self-report. A useful action effect can still be procedural policy learning;
the diagnostics only rule out simpler style, syntax, and memorization stories.

## Falsifiers and stop points

- Reject CompilerGym for this change if the unchanged pin cannot meet the
  fit/semantics canary, has unresolved timing/reward noise at the required
  resolution, or cannot produce both relation and nonduplicate target panels.
- Reject this exact write recipe if adapter-off matches/exceeds authentic on
  held-out action, if authentic is below the full harness, or if the gain
  survives the binding+selection shuffle.
- Diagnose self-imitation/style rather than outcome learning if the
  authentic-selected self-imitation arm explains the gain, or if gain vanishes
  conditional on valid actions / appears on the unrelated preservation panel.
- Diagnose direct generic domain SFT rather than compiler value if raw
  trajectory-to-action LoRA matches the authentic compiler and the compiled
  text arm offers no corresponding benefit.
- Diagnose template reuse rather than transfer if the effect is restricted to
  code/IR neighbors, fails opposite/composite tasks, or does not redirect under
  wrong-life swaps.
- Do not call a two-life, pre-context-overflow scout a lifetime slope,
  saturation result, flywheel, or paper result. A later protocol needs multiple
  independent lives, post-context checkpoints, a strong natural external-memory
  baseline, retention/interference measures, and a predeclared slope model.

## Unresolved taste choices for human ratification

1. Whether the first target modules should be `q/v` rank 16 (conservative) or
   a larger `q/k/v/o` rank 32/64 write with a stronger preservation penalty.
2. Whether 24 touches/row and a 192-row cap under-drive sparse CompilerGym
   experience; the alternative is a fixed total-token budget, which changes
   old/new retention as the life grows.
3. Whether temporal segment credit should use `gamma=0.7, rho=0.5` as above,
   or a shorter all-or-nothing suffix rule. The former learns setup passes; the
   latter is cleaner but can miss pass interactions.
4. Whether fixed anchor KL is acceptable as pre-birth preservation support, or
   whether the stricter first cell should omit it and risk actor erosion. It
   must be declared either way and never be added after a bad result.
5. Whether the first scout needs the self-imitation and raw-action LoRA forks
   immediately (more decisive, more expensive) or only authentic/off/shuffle/
   wrong-life plus text (cheaper, but a positive result is less interpretable).
6. The exact official CompilerGym release/commit, model/bootstrap bytes,
   public observation/action projection, metric epsilon, split algorithm,
   token/action budgets, score margin, and seed policy. These are execution-
   defining bytes deliberately not guessed here.
