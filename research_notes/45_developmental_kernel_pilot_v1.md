# Developmental kernel pilot v1

**Status:** proposed GPU calibration only. This is not a paper protocol and
does not authorize implementation or compute until exact ratification.

## 1. Single purpose

Test the smallest whole flow that the prior work has not tested:

```text
scripted action/outcome life
-> fixed wake resolver produces evidence-only traversal traces
-> recurrent sleep/dream proposes local supported structure
-> compiler makes multi-view training data
-> per-life LoRA
-> fixed goal-directed thinker performs bounded local reads
-> held-out compositional action
```

The pilot asks:

1. Does sleep compilation add useful action structure beyond raw/direct-QA
   LoRA and independent external-memory builders?
2. Does the same compiled corpus survive in LoRA without losing the action
   value available from text?
3. Does recurrent sleep add value over one final matched batch?

It does not test on-policy experience acquisition, a full self-improvement
flywheel, learned loop adapters, external-benchmark generality, baseline
saturation, or an asymptotic developmental law.

## 2. Frozen learning objects

```text
base/controller: Qwen2.5-32B-Instruct, pinned and frozen
memory model:    Qwen2.5-7B-Instruct, pinned and frozen except per-life LoRA
loop policy:     one fixed prompt/schema/state machine across every arm/life
per-life state:  events, accepted semantics, backend, adapter, bounded workspace
```

No thinker or dreamer parameters change. Only the per-life memory LoRA changes.

## 3. Controlled action life

Use a CPU-generated semantic field-expedition world with paired
counterfactual twins. Each life has sites, organisms/materials, equipment and
seed-specific causal exceptions. Public actions are:

```text
SURVEY, ASSAY, PREPARE, TRAVERSE, INTERVENE, COMMIT
```

The common life is produced once by a fixed scripted information-gathering
policy and replayed byte-for-byte to every memory arm. Each event is labelled
`COMMON_DECK_REPLAY`; it is action/outcome experience but not evidence of
on-policy learning. That later claim is explicitly out of scope.

The generator freezes the held-out target deck only after the source-life
world is sampled but before any model or memory method runs. Targets are
derived from hidden causal templates and receive fresh handles never present
in the source stream.

Capability families:

- `A0`: witnessed transition recall; installation diagnostic only.
- `A1`: one-relation role transfer to a fresh entity.
- `A2`: combine two relations from different source episodes to select a
  preparation/action.
- `A3`: combine two or three relations into a four- to six-action plan.

The primary pilot score is mean A2/A3 normalized action value. A0/A1 are
reported separately.

### Environment gates

- hidden-graph oracle scores at least `0.85` on every locked world;
- strongest no-lifetime-memory adaptive experimenter scores at most `0.35`
  on A2/A3 under the full think/action budget;
- target-only, state-only, identifier-only, passive-signature and action-prior
  probes each score at most `0.35`;
- shuffling source action--outcome bindings reduces exact-memory oracle value
  by at least `0.30`;
- paired twins share public names, descriptions and marginal action counts but
  have different correct A2/A3 actions;
- from an A2/A3 evaluation start, reacquiring all decisive relations requires
  at least seven actions while the evaluation cap is six.

Composing several supported local records is intended, not cheating. Cheating
is prevented by construction: no memory record may contain a held-out target
handle; each derived record must cover at least two source situations; and
held-out goals are new compositions. No record may contain a complete ordered
plan or terminal target answer.

## 4. Common wake trace

Run the fixed 32B resolver once over the common source deck. The scripted
environment action remains authoritative; the resolver may emit one of:

```text
NOTICE | QUERY | HYPOTHESIZE | BACKTRACK | DEFER
```

Its free-form workspace is never a sleep input. Sleep receives only this
fixed-schema projection:

```text
TraceProjection:
  projection_id
  source_event_ids[]          # sorted, maximum 4
  operation_kind
  query_kind
  public_subject_handles[]    # sorted, maximum 3
  public_condition_handles[]  # sorted, maximum 3
  observed_action_handle | NONE
  observed_outcome_handle | NONE
```

There is no agenda, rationale, candidate answer, expected outcome, target ID,
confidence, ordering freedom, variable free text, or hidden score. Projection
fields are deterministic functions of sealed public events and parsed
operations. Counterfactual answer swaps with identical public events must
produce byte-identical projections.

## 5. Semantic writers and support

Writer authority is exclusive:

| Record/event | Only writer |
|---|---|
| public ExperienceEvent | environment ingestor |
| directly witnessed atom | deterministic witness ingestor |
| derived PROPOSED claim | dream resolver |
| PROVISIONAL/RETRACTED schema status | deterministic status engine |
| SUPPORTED/CONTRADICTED status | chronological public-outcome comparator |
| corpus realization | compiler after status check |
| adapter checkpoint | trainer from sealed corpus manifest |

Wake cannot write semantic claims or statuses. Dream cannot promote itself.
The compiler cannot alter support.

Evidence units are intervention episodes, not individual event IDs. Events,
views and derivations from one intervention share one evidence-equivalence
class.

Promotion rules:

- witnessed atom: one direct public observation;
- relation/causal rule: either three independent intervention episodes, or two
  independent episodes including a matched contrast where one condition
  changes and the predicted outcome changes;
- procedure: two independent successful episodes plus one public failure or
  boundary case;
- exception: two independent exception episodes plus two default-rule episodes;
- shortcut: two independent successful wake paths whose every local edge is
  already supported, followed by one later ordinary successful use.

All derived predictions commit before their confirming outcome. Synthetic
views and repeat exposure never add support. Provisional claims are excluded
from positive LoRA data.

## 6. Sleep and compiler

Primary working budget is `C = 8192` tokens, counted with the pinned 32B
tokenizer over canonical public events. Recurrent sleep fires after the first
terminal source episode that makes cumulative source tokens reach or exceed
`0.5C`, `1C`, and `2C`. An episode is capped below `0.25C`, so one episode
cannot cross multiple sleep boundaries.

At each sleep:

- select at most 64 new intervention episodes, chronologically then
  type-balanced;
- include their public events, eligible prior supported semantics and
  evidence-only trace projections;
- dream may propose at most four local claims per selected episode;
- preserve every raw proposal and failure; no repair/retry based on content;
- compile at most 512 cumulative supported claims, with deterministic
  type-balanced then chronological truncation;
- emit six fixed views per claim;
- train every retained claim for exactly 24 effective touches at that
  checkpoint.

LoRA recipe:

```text
rank=64, alpha=128, dropout=0.05
targets=q_proj,k_proj,v_proj,o_proj
AdamW, lr=2e-4, batch=32, max_len=192
six fixed views x four epochs = 24 touches per retained claim
cumulative rebuild from the clean base at every checkpoint
no early stopping and no content-dependent retry
```

The final-batch arm receives the complete `0..2C` source life once, the same
maximum number of dream proposals, the same final corpus cap, the same 24
touches/claim and no intermediate usable memory. Total dream input/output token
caps and adapter training tokens are matched to the recurrent arm by
predeclared padding calls whose outputs are discarded.

## 7. Reader and thinker

Every arm receives at most three memory queries and six total resolver
operations per evaluation action. One query returns one local record or
`NOT_FOUND`; it never returns a chain or plan.

Model-visible read:

```text
FOUND | canonical_value | support_handles<=2
NOT_FOUND
CONFLICT | canonical_value_1 | canonical_value_2
```

No confidence, token count, backend identifier, receipt hash, retrieval score,
status history or corpus metadata reaches cognition. Audit receipts are stored
out of process.

All legal candidate values plus `NOT_FOUND` are frozen from the public
ontology before target generation. Candidate order is canonical and invariant
to target answer/hidden truth. The exact same query schema, candidate policy,
top-k and thinker budget are used for common-interface text and LoRA arms.

Each evaluation item starts in a new process with clean KV/prefix caches,
prompt history, workspace and RNG. Only public outcomes within the current item
remain visible to that item. No outcome, memory or cache crosses to another
held-out item or back into source life.

## 8. Arms

Mandatory six-world calibration arms:

- `K0`: no persistent memory / recent context only.
- `K1`: raw episodic BM25/embedding RAG.
- `K2`: frozen independent A-MEM-style linked-memory builder over the raw life.
- `K3`: direct trajectory-to-atomic-QA LoRA, matched to K6 training tokens.
- `K4`: recurrent sleep-compiled text memory through the common reader.
- `K5`: the identical K4 corpus in recurrent LoRA.
- `K6`: recurrent sleep-LoRA with source outcomes shuffled within world.
- `K7`: final-batch sleep-LoRA matched as in section 6.

Diagnostic factorial:

- known-good supported memory x `{no reader, common reader}` x thinker budgets
  `{0, 3, 6}`;
- degraded memory with 25% bindings shuffled under the same grid;
- identical compiled corpus in text and LoRA;
- K5 atoms only versus atoms plus legal shortcuts.

The independent A-MEM-style builder operates from raw public episodes and does
not consume our accepted semantic corpus. Its prompt, linking policy and
resource cap freeze before locked worlds. A reflection/lesson builder is added
only in the later paper protocol; this calibration makes no SOTA claim.

## 9. Pilot split, estimator and promotion

- two development worlds for parser/runtime/format bugs and no scientific
  conclusions;
- six locked paired world-lives, never used to change prompt, world, reader,
  hyperparameters, thresholds or arm implementations;
- read-only evaluations at `1C` and `2C`;
- report every world, arm, capability family, failure, token, call, adapter
  byte, training step and wall-clock value;
- no p-value or paper claim from six worlds.

The primary pilot contrast is the paired per-world K5 minus K3 A2/A3 value.
Secondary contrasts are K5-K2 (independent organized text memory), K5-K4
(same-corpus transport loss), K5-K6 (action/outcome causality), and K5-K7
(recurrent versus batch cadence).

Promotion to a separately designed scale protocol is allowed only if:

1. known-good memory plus six-step thinker scores at least `0.75` A2/A3;
2. K5 exceeds K3 in at least four of six locked worlds and mean difference is
   at least `0.10`;
3. K6 loses at least half of the K5 gain over K0;
4. K5 is no more than `0.10` below K4 on the same corpus;
5. no leakage/reset/environment gate fails.

K5-K2 and K5-K7 are reported but are not promotion requirements. They decide
which mechanism is worth scaling.

## 10. Runtime and crash semantics

Operation identity is the hash of branch, public-state version, operation type,
normalized arguments and memory checkpoint. A repeat counter resets only after
new public evidence, a new memory checkpoint, or an explicit BACKTRACK to a
new branch. Three identical operations without state change force a
policy-visible `BUDGET_EXHAUSTED`; repeated `NOT_FOUND` must BACKTRACK, DEFER or
terminate and cannot be reformatted to bypass identity.

Every prompt has a golden prompt/schema/parser/attention-mask compatibility
fixture. Unknown fields, prose, multiple operations, truncation or wrong
directionality are malformed and consume budget.

A sealed provider output is reused byte-for-byte on resume. An unsealed model
call interrupted after provider dispatch is `INDETERMINATE` and the entire
world/arm cell is preserved as failed; it is never regenerated under the same
scientific identity. Deterministic resume refers to deterministic state from
sealed bytes, not bitwise regeneration by GPU kernels.

## 11. Required pre-GPU tests

- environment oracle, adaptive no-memory, leakage, twin and shuffle gates;
- exclusive semantic-writer matrix;
- causal evidence-equivalence and promotion fixtures;
- byte-identical trace projection under answer/target swaps;
- complete-plan/target-handle rejection for individual records;
- fresh-process isolation between evaluation items;
- reader metadata and candidate-order noninterference;
- known-good/degraded reader x thinker factorial smoke;
- recurrent/final-batch budget equivalence;
- common-deck byte identity and event-source receipts;
- prompt/schema/parser/attention-mask golden fixtures;
- repeat-state adversarial fixtures;
- cross-life canaries and scorer/evaluator write denial;
- crash-before/after-seal resume fixtures;
- fresh independent implementation review plus author-side advocate.

Passing tests licenses only the six-world exploratory GPU calibration. It does
not license an external, on-policy, scaling or paper claim.

