# Public Pathway Consolidation v3 — causally separated experience model

Status: proposal only. The complete architecture is PPC v1 protocol SHA-256
`fca9eac73b91c511682bc5f7dd6c010063ec85ae07f91b588782ea41f290aafc`,
then PPC v2 amendment SHA-256
`2a711e9d37783339bd1b0b87781446c946a81eb8d9219a5d0a53ea265038fb4e`,
then this amendment. This file supersedes every conflicting earlier clause and
disposes PPC v2 consensus SHA-256
`e101aca30a40ae79037933f7e93d4b3fa93c30a61d38280f61fb74fb41b2ca07`.

The thesis remains deliberately small:

```text
THINK  = one recurrent public operation that searches, predicts, or acts.
DREAM  = the same frozen model provisionally reconciles the causally available
         working set; it cannot create evidence or durable weights.
SLEEP  = a public-evidence gate renders runtime-format training rows and alone
         updates the per-life LoRA.
```

Parenting is a future experiment about learning acceleration and outgrowing a
starting prior. It is not part of PPC3.

## B1. Complete byte-visibility contract

The formal change artifact contains one cell for every stage and each of these
independent byte classes: source public bytes; current-item public transition;
prior-item result; target public bytes; target manifest membership/order;
hidden truth/oracle/proof; quarantined scorer metrics; public THINK/DREAM
workspace; opaque harness identifiers; writer eligibility/support; retrieval
candidate/rank/index internals; condition/trainer/adapter identity; filesystem,
environment, process and error channels; timing/cache/batching/provider
metadata. No grouped catch-all substitutes for a class.

Prompt construction is allowlist-only. All maps use canonical JSON: UTF-8,
sorted keys, no insignificant whitespace, arrays in declared order. Tests
independently mutate each forbidden class and require byte-identical model
inputs, retrieval requests, writer rows, and DREAM slices.

Identifiers are harness-assigned after a legal operation is accepted. They
match `^(br|sg|hy|rec|ev)-[0-9]{8}$`, are monotonically allocated within one
life, contain no model-proposed substring, and are remapped to a fresh opaque
namespace before target evaluation. The model may refer only to allocated IDs.
`REQUEST_DREAM` may cite only visible `rec` unresolved-surprise or root-event
records on the active branch. Subgoal/hypothesis IDs cannot choose DREAM input.

Target manifest membership, order, complement, condition, score, target-derived
repair signal, filenames, environment, cache, timing, provider and process
differences never reach model or writer bytes. Current-item action results may
recur only inside that item. No completed item contributes to any later target
item or writer.

## B2. Exact THINK/DREAM state machine and charges

PPC3 has no automatic DREAM trigger. Context pressure is a visible mechanical
counter; the model may spend a normal call on typed `REQUEST_DREAM`. This makes
the current experiment identify requested reconciliation rather than mixing it
with a hidden scheduler.

One THINK call emits exactly one of:

```text
OPEN_SUBGOAL, QUERY_LEDGER, FOLLOW, HYPOTHESIZE, PREDICT, ACT,
REVISE, BACKTRACK, REQUEST_DREAM, DEFER, STOP
```

The state freezes: life/item IDs; ordered branch stack and statuses; ordered
subgoal stack; hypothesis DAG and citations; opened record IDs; live prediction
bound to one next action; unresolved surprises; last same-item transition;
call/read/action/dream/token balances; normalized-operation repeat counts; and
all prompt/schema/parser/model/adapter hashes.

The canonical operation fingerprint is SHA-256 of `(prestate_hash,
operation_enum, schema-normalized_arguments)`. Three equal fingerprints force
`DEFER(REPEAT_LIMIT)`. `BACKTRACK` closes the active branch and activates the
most recently opened still-open sibling; if none, its parent; if none, STOP.
Closed/abandoned descendants cannot be cited or reopened in PPC3.

Every dispatched model call consumes one call allowance. A legal query also
consumes one read; ACT, including an invalid environment action, consumes one
action; REQUEST_DREAM consumes one call and one dream. Parse or illegal-state
failure publishes a normalized public error, consumes the call, and permits at
most two later calls; the third forces DEFER. Mandatory DREAM-closure overflow
consumes its call/dream and publishes no workspace. Provider failure after
dispatch terminates the item as missing with no retry. Failure before dispatch
consumes nothing and invalidates the cell. No invisible retry exists.

DREAM receives only the requested visible records, complete ancestor closure,
and the most recent causal public outcomes fitting the residual fixed budget.
Mandatory closure is topological then chronological and is never truncated.
Its strict output may retain/drop visible IDs, propose cited links/questions,
and replace one provisional workspace. It cannot act, issue retrieval, change
support, emit a final answer, publish weights, or create writer evidence.

## B3. Canonical roots and support

Compiler roots are canonical transition classes:

```text
(normalized_program_family, initial_IR_hash, prestate_hash,
 canonical_pass_id, poststate_hash, public_metric_version)
```

Repeated execution, replay, restatement, multi-view rendering, and multiple
measurements of that transition share the root. Near-duplicate programs share
`normalized_program_family`, defined before sealing by exact stripped-bitcode
hash or the registered source-family/MinHash rule. Independent semantic support
requires distinct program families and acquisition items, not merely distinct
events.

PCFL roots are generator-issued latent-event IDs. Chronological confirmations,
paired twins, paraphrases, and regenerated views of one event share its root
family. Independent support requires distinct generated worlds/items whose root
families are disjoint. Every derived node carries the union of ancestral roots.
Diamonds are allowed, cycles rejected, descendants never support ancestors, and
support counts root-family sets rather than rows or exposures.

## B4. Local atoms, paths, and forbidden shortcuts

The mechanism assay admits only witnessed local semantic atoms and exact public
operation transitions. It forbids as positive memory targets:

* composite relation shortcuts not directly witnessed;
* final answers, target-sufficient mappings, or target identifiers;
* a terminal action paired with a state earlier than its exact causal prefix;
* DREAM prose, hypotheses, confidence, agendas, synthetic outcomes, or scorer
  labels as evidence.

Composite shortcut materialization is scientifically interesting but belongs
to a later registered scaling treatment. PPC3 first asks whether recurrent
traversal over local records matters. A sealed decisive path must contain at
least two local edges. Its bridge cut removes an actually traversed local edge;
its binding twin swaps the sealed relation endpoint; its memory cut returns a
typed null for the decisive record. Expected action changes are bound before
results open.

Action deletion resets the same program and open-loop replays the same pass
sequence with exactly one pass omitted and no reselection. Unreproducible or
unavailable suffixes are UNDEFINED. A defined difference labels only
`sequence_essential_for_this_trace` for that action. Cognitive operations are
only outcome-associated until behavioral component, recurrence, shuffle, and
cut contrasts establish value.

## B5. Component matrix and reader isolation

The component assay uses one frozen eligible source-row universe and executes
the full `2 x 2 x 2` matrix over row families:

```text
READ in {off,on} x DECIDE_NONACT in {off,on} x ACT in {off,on}
```

`COGNITIVE_NO_ACT` is READ+DECIDE with ACT off. `PATH` is all three on. Every
cell uses the same eligible root/path sample, causal prefixes, sampler seed,
effective output-token budget per enabled family, clean-base rebuild, rank,
optimizer, update count, publication lifecycle, and inference budget. Empty
families are absent rather than padded with meaningless training. Main effects
and interactions are reported only from this matrix.

ENDPOINT is a separate strong baseline: immediate-improvement action rows only.
It is never used as the ACT-only factorial cell.

For fixed-corpus transport, READ-LoRA lives in a separate reader process. It is
mounted only for the typed one-record READ call and returns the same schema and
candidate domain as TEXT_READ. The recurrent thinker is an unmodified frozen
base process, receives the exact returned bytes, and is hash/byte checked
against the text-reader condition. The reader adapter is absent during every
THINK and ACT call. Exact, reverse, paraphrase and partial-cue probes identify
transport separately from policy learning.

## B6. Recurrence and strong baselines

Two different ablations are retained and named literally:

* `PATH_ONE_SHOT_QUERY`: all queries commit before any return; FOLLOW and
  value-dependent retrieval are forbidden. This removes adaptive retrieval,
  not recurrent thought.
* `PATH_OPEN_LOOP`: one initial model call commits the complete ordered sequence
  of queries, follows, predictions and actions before any return or outcome;
  the harness executes it open-loop with no further model call. This removes
  recurrent THINK. Unused calls/tokens/actions are charged.

Required baselines are STANDARD_AGENT, TARGET_STATE_ONLY, FULL_CONTEXT,
RAW_RAG, EXPLICIT_GRAPH, LINKED_TEXT, REFLECTION_LESSON_TEXT, ENDPOINT,
DIRECT_QA_LORA, and SAME_LIFETIME_BATCH_POSTTRAIN, plus the component matrix,
shuffle, one-shot-query, and open-loop arms.

STANDARD_AGENT receives the birth/system instructions, target goal/current
public state, clock/budgets, last same-item transition, and a registered recency
window of its own same-item public scratch; it has no cross-item store.
TARGET_STATE_ONLY receives only birth/system instructions, target goal/current
public state, clock/budgets, and output schema; it receives no earlier model
output or lifetime state. All interfaces are byte specified before sealing.

REFLECTION_LESSON_TEXT stores evidence-linked source lessons in external text;
DIRECT_QA_LORA renders direct source state-to-action/answer rows without paths;
SAME_LIFETIME_BATCH_POSTTRAIN trains on the registered batch of raw public
trajectory rows at the same sleep boundaries. Their claims remain literal.

## B7. Canonical shuffle, twins, cuts, and split sealing

PATH_SHUFFLE starts from the authentic DAG. Within predeclared strata
`(row_family, root_count, outcome_stratum, token_length_bin, in_degree,
out_degree)`, a fixed manifest-seeded degree-preserving double-edge-swap
deranges parent bindings. A candidate is accepted only if it is acyclic, keeps
all node bytes/root/outcome marginals and degree sequence, preserves token and
candidate load, destroys every registered decisive path, and creates no valid
replacement path under the independent oracle. At most 1,000 deterministic
candidates are tried; failure invalidates the cell without fallback.

PCFL twin manifests freeze: byte-identical target prompt/current-state bytes;
equal candidate domains and budgets; one declared relation-binding permutation
inside treatment memory; canonical renaming maps; and the predeclared expected
action swap. Compiler splits forbid exact stripped-bitcode duplicates, same
source families, and registered near-duplicate pairs across acquisition/target.
Both independent sealers implement these transformations without importing
production selection code and record their own source hashes.

## B8. Resource views and promotion

Primary cross-substrate comparison matches active retained experience bytes and
all inference calls, reads, actions, input/output tokens, decoding, candidate
work, and cold-cache policy. Active bytes are exact serialized inference-time
payload + required metadata/index + adapter tensors at declared dtype; they
exclude filesystem padding, optimizer, and checkpoints. Caps and deterministic
source-only truncation are frozen before outcomes.

Secondary accounting reports total construction tokens/time, training FLOPs,
optimizer/checkpoint bytes, all stored copies, indexing, cache/KV, latency, and
environment cost. A LoRA-specific claim requires PATH to beat the strongest
LINKED_TEXT/EXPLICIT_GRAPH treatment in the primary matched-active-byte view.
Secondary costs cannot be hidden and may qualify efficiency claims. If external
memory wins, it remains a first-class Stage-C treatment and no LoRA moat is
claimed.

## B9. Full Stage-C flywheel and schema rung

One developmental cycle is exactly:

```text
N_ACQ sealed source roots -> requested DREAM opportunities -> SLEEP selection
-> cumulative clean-base training -> atomic adapter validation/publication
-> cold remount -> next sealed evaluation/acquisition cohort
```

`N_ACQ`, sleep/dream/call/action budgets, and cohort order are run-manifest
bytes fixed before execution. Each life has one pre-native checkpoint and at
least four post-native checkpoints. Full-flywheel language requires at least
three successive completed cycles showing the registered directional chain.

The mediation chain is:

```text
assigned prior memory -> epistemic action -> public new observation
-> later admitted sleep row -> later retrieved path -> later action/value
```

Interventions are separate: correct vs wrong/null memory at epistemic choice;
new observation included vs replaced by an equal-token/equal-row sham at sleep;
later decisive path intact vs cut; adapter mounted vs unmounted at later action.
The sham never supplies positive semantics. Lives, not targets, are independent
units. Every life resets base process, adapter, accepted corpus, workspace,
ledger, external store, reader/index/KV caches, RNG streams, and output paths.

PCFL-Stream tests continual acquisition, old retention, cross-era composition,
capacity, and storage efficiency over rank `{4,16,64}` and matched byte caps.
It does not authorize learned-compression language.

PCFL-Schema is a separate prospective rung. Acquisition exposes only local
episodes and their public outcomes, never the latent schema statement or target
combinations. Evaluation uses fresh symbols and held-out compositions requiring
the latent regularity. Compression requires, jointly: fixed adapter bytes;
growing independent sufficient-statistic information; schema/action utility on
held-out combinations; decreasing or bounded reconstruction of irrelevant
episodic detail; and superiority to matched text/graph and shuffled controls.
If rank/bytes grow linearly, or episodic lookup explains the gain, report
storage/transfer, not learned lossy compression.

## B10. Statistics, lifecycle, and negative results

Before any model run, a quantitative adequacy gate freezes co-primary outcomes,
effect thresholds, development-variance source, independent-life count, power
or simulation calculation, estimator, confidence intervals, multiplicity,
missingness, outliers, futility, and maximum extension. A complete manifest is
not itself evidence of power; an independent reviewer must verify the numeric
criterion. Baseline saturation/crossover is reportable only when the registered
baseline slope interval meets the prospective flattening rule.

Item lifecycle is:

```text
CREATED -> INPUT_HASHED -> DISPATCHED -> PARSED -> COMMITTED -> CLOSED
```

Any pre-dispatch integrity failure gives INVALID_CELL. Any post-dispatch
provider failure gives MISSING_NO_RETRY. Parse/illegal failures follow B2.
Sleep lifecycle is:

```text
ROWS_SEALED -> TRAINING -> VALIDATED -> ATOMICALLY_PUBLISHED -> COLD_MOUNTED
```

Partial/non-finite/hash-mismatched training gives FAILED_SLEEP and preserves the
previous adapter; no partial artifact mounts. Exact resume is allowed only from
the same commit, manifests, event-prefix hash, RNG states, and previous adapter.

A failed sealed construct/science gate remains a registered negative result.
Changing writer, metric, threshold, target, treatment, split, or analysis after
results open requires a new change ID, new targets/seals, fresh review, and new
ratification. Revealed targets never become development data for the same claim.

## B11. Current authority boundary

Current ratification, if granted, authorizes only isolated contracts,
deterministic CPU/no-model fixtures, and two independently implemented no-model
sealers. All preflight semantics are scripted/stubbed; they establish byte
contracts, transition uniqueness, metric sensitivity, and constructibility—not
scientific effects. No model call, canary, LoRA training, or GPU work is inside
this scope. After implementation and independent review, one exact model/GPU
manifest may be proposed for a separate human ratification.

