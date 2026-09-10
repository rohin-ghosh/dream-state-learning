# Descendant visibility, taint, reset, and sterility contract

Status: proposal only; no executable boundary or authority is created here.

## 1. Information classes

| Class | Contents | Positive cognition eligibility |
|---|---|---|
| `PUBLIC_OPPORTUNITY` | current ordinary goal/state, legal actions, public costs, budgets | wake only |
| `PUBLIC_LIVED_EVENT` | action actually executed and ordinary public observation/outcome | wake, Dream, sleep |
| `PUBLIC_WITNESS_ATOM` | deterministic extraction from a public lived event | memory eligible |
| `SELF_SEMANTIC` | model-owned prospective/revision claim and append-only lifecycle | memory eligible under declared status |
| `EXPLORATION_ASSIGNMENT_METADATA` | opaque branch/treatment registry identity, capability/object handles, lifecycle and removal flags; no semantic memory bytes | fork assigner; resetter read-only for destruction proof; terminal analysis after seal |
| `EXPLORATION_MEMORY_CONTENT` | AUTH/TWIN/NULL assigned semantic memory object and reader-visible returns | fork installer only; diagnostic actor derived through reads; forbidden after probe |
| `BRANCH_PUBLIC_EVENT` | fork diagnostic action and ordinary outcome | post-unmount compiler eligible |
| `BRANCH_DELTA` | target-blind descendants of branch public event under common prior | later evaluation eligible |
| `EVAL_GOAL` | sterile held-out goal/state/target handle | evaluator actor only |
| `EVAL_OUTCOME` | target action, environment outcome, score | scorer/audit only; never life |
| `HIDDEN_TRUTH` | mappings, twins, proofs, optimal actions, exceptions, target allocation certificates | generator/certifier/scorer only |
| `ARM_AND_CAPACITY` | method, substrate, rank, reader, treatment and cut assignments | trusted installer/analysis only |
| `PRIOR_RESULTS` | prior arm scores, support/compiler success, thresholds and aggregate statistics outside the registered DEV transition | terminal analysis only |
| `RESOURCE_AUDIT` | bytes, scores, latency, retries, errors, costs, receipts | audit/analysis; trusted DEV selector receives only registered aggregates after all DEV cells seal |
| `DEV_FROZEN_CONFIGURATION` | one AS-EXT identity; hash echoes of immutable Stage-A2 cognition bytes including `SELF_AGGREGATION_V1` unique-instance/equivalence/Dream-2-addition semantics, `ORDINARY_SLEEP_CADENCE_V1` fixed scheduling slots plus minimal unpadded payload/dual-clock/checkpoint rules, `SELF_LIFECYCLE_READER_V1` lifecycle/cursor/exhaustion/constant shapes and their blindness goldens; frozen B3 resource/defer/stop disposition | trusted selector output; downstream B3 installers receive only the frozen configuration they require, never source scores; no Stage-C authority |

Taint propagates to the most restrictive ancestor. `EVAL_OUTCOME`,
`HIDDEN_TRUTH`, `PRIOR_RESULTS`, scorer-derived data, and assignment-derived
metadata can never become positive memory, a candidate, a retrieval key, a
prompt hint, a retry decision, or a later-life event. `EVAL_GOAL` is the sole
bounded exception: sterile evaluation cognition may derive an ephemeral typed
query from the current goal/state and send those query bytes to the reader.
The query and return live only inside that target process; neither may persist,
flow upstream, modify an index/catalog, become a memory record, affect another
target, or enter the ordinary life.

## 2. Component-level visibility

The later executable design must instantiate these exact boundaries:

| Component | May read | Must not read | Permitted output/consumer |
|---|---|---|---|
| world-root generator | hidden distribution seed, fixed protocol | arm/results/compiler success | private root to certifier; public projection to renderer |
| opportunity allocator | private root, frozen allocation RNG | arm/results/support/compiler output | total opportunity manifest before outcomes |
| target allocator/certifier | private root, opportunity manifest | arm/results/model/compiler output | private target/proof manifest to scorer; public target projection only after memory freeze |
| public renderer | declared public projection, frozen finite reachable packet catalog | hidden fields, arm, proof, target descendants before target phase | minimal unpadded agent-visible public payload plus a separate fixed-shape scheduling envelope; neutral envelope bytes never enter cognition |
| ordinary wake actor | current public opportunity/events, assigned arm memory interface | truth/proofs/future targets/results/audit metadata | one legal cognitive/action operation |
| environment executor | private engine state, parsed action | memory contents, scores, other arms | ordinary public result plus private scorer transition |
| deterministic extractor | one public before/action/after event | hidden mapping, future target, arm result | canonical public witness atom |
| Dream-1 | unpadded agent-visible public payload replay by presealed event-slot ID, eligible prior SELF memory, fixed budgets, exact opportunity-block/event-slot trigger | neutral envelope/header/padding bytes, later outcome, realized-length-derived boundary, target, truth, arm/result/DEV output | bounded prospective claims/predictions in uniquely identified preallocated sample slots |
| Dream-2 | exact Dream-1 bytes, ordered unpadded agent-visible public payloads, eligible common prior, exact presealed block-close trigger | neutral envelope/header/padding bytes, comparator verdict, realized-length-derived boundary, target/truth/result/DEV output, exploration assignment after unmount | lineage-local model-owned retain/revise/abstain/add decisions in uniquely identified preallocated slots |
| sleeper/compiler | eligible public/SELF bytes and provenance, exact frozen multi-sample reducer/admission and lifecycle policies | target/truth/scorer/arm/result/DEV output or any correctness selector | syntax-valid target-blind fixed-slot semantic snapshot/delta |
| text index/reader | assigned frozen native snapshot, checkpoint-specific active/readable status, pre-output allocation order, literal match keys, deterministic cursor/exhaustion and constant-shape policy, model query bytes including sterile goal-derived query bytes at target time | raw goal/state outside query bytes, truth/scorer/arm name/status reason/confidence/recency/support/utility | one fixed-shape native record, padded `SELF_SLOT_UNAVAILABLE`, or padded `NOT_FOUND_EXHAUSTED`; no query/cursor persistence |
| fork assigner | sealed state, AUTH/TWIN/NULL schedule, opaque registry | future outcome/score | exactly three opaque branch capabilities and treatment-hidden labels/order |
| diagnostic actor | public fork opportunity, opaque assigned reader | assignment label, truth/future target/results | exactly one probe action |
| post-fork resetter | read-only assignment-registry metadata, capability/object handles, process/cache registries, sealed public branch-event handle | assigned semantic memory bytes, semantic interpretation, score/target/truth | destruction/absence receipt only; no content reaches compiler |
| delta compiler | common authentic prior, common Dream-1, branch public event, pre-fork assignment-independent P1 seed manifest | assigned fork memory/object/metadata or any assignment-derived seed, future target/truth | branch delta |
| evaluation installer | common authentic prior, sealed branch delta | fork assigned memory, truth/score | `M_k^- + D_z` only |
| evaluation actor | sterile goal/state, installed read interface | life stores, branch assignment, truth/results | legal action trajectory |
| scorer | truth, targets, frozen actions, assignments | ability to write any cognitive/life object | terminal scores to analysis store |
| resource auditor | receipts and public IDs | ability to influence prompts/retries/selection | terminal resource ledger |
| trusted DEV selector | only frozen aggregate DEV metrics and resource vectors after all eight roots/cells seal | raw target text, hidden truth, per-target artifacts, any live cognition, population-test or Stage-C inputs | one-way `DEV_FROZEN_OUTPUT`; no semantic memory, retrospective cell change, or successor authority |
| terminal analyst | all sealed artifacts after completion | any live cognitive channel | registered root-level estimands only |

The trusted DEV selector's exact allowed input vector is: mean DEV cross-era
AUC and fully counted resource vector for the two AS-EXT candidates; their
failure counts; parser/compiler/read fidelity aggregates used by the Stage-B
gate; the eight descriptive root summaries; the measured per-root
call/token/device-or-dollar/storage/transfer ledger; and binary results of
predeclared leakage/reset tests. It may apply only the frozen AS-EXT tie rule,
B3 resource rule, and defer/stop rule. It may echo but never select or rewrite the
generic/class-informed prompts, compiler, DSL/parser,
`SELF_AGGREGATION_V1` unique-instance/equivalence/addition rules,
`ORDINARY_SLEEP_CADENCE_V1` fixed-slot renderer/cutoff/tie rules,
`SELF_LIFECYCLE_READER_V1` lifecycle/cursor/exhaustion/shape rules, their
blindness goldens, native reader,
semantic-cut, or failure-rule hashes frozen at Stage A2. It cannot add/drop a
root, target, arm, checkpoint, branch, lane, failure, threshold, or retry. Its
single sealed `DEV_FROZEN_CONFIGURATION` output is consumed one-way after DEV and contains no raw score or
target-specific information.

## 3. Metadata closure

Forbidden information may not be encoded through:

- filenames, paths, handles, IDs, hashes exposed to cognition, directory order,
  object count, omission, padding, serialized length, candidate count/order,
  rank, score, confidence, provenance count, error text, exception type,
  retry count, timeout, latency, scheduling, cache hit, process identity,
  environment variable, RNG stream, model seed, prompt variant, adapter name,
  index namespace, optimizer state, temporary directory, log tail, or resource
  abort behavior;
- candidates, negatives, synthetic views, training order, retrieval keys,
  summary headings, or supposedly diagnostic prompts; or
- DEV outcomes changing any later targets, arms, root inclusion, checkpoint
  positions, thresholds, branches, lanes, or failures; the
  only permitted transition is the trusted selector applying its prospectively
  frozen candidate/tie/cap grid and emitting `DEV_FROZEN_OUTPUT` once.

Every component uses constant-shape behavior where a failure/omission would
otherwise reveal a forbidden class. Backend errors are failures, never
`NOT_FOUND_EXHAUSTED`. Raw outputs and failures are sealed before parsing; no
hidden repair or content-dependent retry exists. Identical catalogs and native
returns are required only within explicitly matched interventions and the
WITNESS-KV-NA/REC pair. Cross-representation conditions share the frozen query
grammar and online budgets but retain and report their native records,
catalogs, indexes, serializers, readers, and complete resource surfaces.

## 4. Fork unmount invariant

After the diagnostic action, the resetter must prove that no descendant of
`EXPLORATION_ASSIGNMENT` remains except the ordinary public action/outcome:

```text
allowed surviving causal descendants:
  diagnostic_action -> public_environment_outcome

forbidden survivors:
  assigned text/adapter/index/candidate object
  actor conversation/workspace/KV/prefix cache
  reader cursor/rank/order/latency/error state
  assignment label/hash/path/seed
  target-conditioned or scorer-derived object
```

The resetter may observe that a registry entry/capability/process/cache object
exists and may verify its deletion. It may not read, hash for cognition,
serialize, compare, or forward the assigned semantic content. The delta
compiler starts only after a signed absence receipt and receives neither the
registry nor that receipt as model-visible input.

At A1, the boundary certifier must permute AUTH/TWIN/NULL treatment-to-opaque-
label maps, execution orders, assigned capability handles, registry hashes,
and lane names while holding `(protocol_hash,root,side,checkpoint,pair_group,
sample_index)` fixed. Every P1 compiler seed and every nonintervened Dream-2
input byte must remain identical. It must also assert seed equality index by
index across AUTH/TWIN/NULL, intact SELF versus same-probe twin-outcome, and
every stochastic common-history condition entering `r_6,w`; cut/sham must show
zero compiler calls and the same intact-delta source hash. Changing only the
public outcome intervention must change only its input bytes, never the paired
seed. A2 freezes the assertion code, golden vectors, RNG implementation, pair-
group manifest, sample numbering, and mutation fixtures. Any assignment-
dependent seed, unequal paired seed, hidden resample, or non-public branch-
varying compiler input is `STOP_ASSIGNMENT_DESCENDANT_RNG` before B0.

The evaluation installer independently reconstructs the common authentic
prior and branch delta from sealed hashes. Byte equality tests compare all
non-delta inputs across branches. Any unexplained difference invalidates the
causal-cascade estimand.

## 5. Evaluation sterility

Each target starts in a fresh process with clean workspace, prompt history,
reader cursor, candidate state, RNG, and KV/prefix cache. Evaluation has
read-only access to the installed snapshot. The actor may form bounded
ephemeral typed queries from the current sterile goal/state; the query, return,
and goal-derived workspace are destroyed at item end. Evaluation cannot access or mutate the
ordinary life, future opportunities, semantic store, compiler, adapter,
optimizer, index source, or another target. Pre/post hashes of every life
object must be identical. Evaluation outcomes never become lived events.

## 6. Fresh-life reset

Before each life or twin side, reset and canary-check:

- episodic, witness, semantic, status, provenance, opportunity, target,
  branch, agenda, corpus, evaluation, scorer, and audit stores;
- text indexes, embedding stores, candidate catalogs, adapters, optimizer and
  scheduler state;
- model conversation, prompt history, workspace, KV/prefix/provider cache,
  parser and retry state;
- RNG namespaces for world, opportunity, target, arm, model, training,
  evaluation, and statistics;
- temporary paths, file descriptors, processes, environment handles, locks,
  queues, monitors, and network/provider sessions.

Inject prior-life canaries into public text, semantic atoms, candidate values,
index keys, adapter cues, optimizer slots, cache keys, paths, errors, and
process handles. The new life must return `NOT_FOUND`, show clean hashes, and
hold no old descriptor or live handle.

## 7. Required mutation tests

Before any later scientific call, mutate each forbidden class separately and
prove either byte-identical cognitive inputs or fail-closed rejection:

- target/truth/arm/result swaps;
- scorer/comparator/DEV-result swaps against reducer admission, ordinary
  cadence/triggers, checkpoint snapshot choice, and SELF status readability;
- valid/disagreeing/semantically identical/abstained/malformed/failed
  multi-sample mixtures and Dream-2 additions, asserting unique instance IDs
  and forbidding equivalence merging, lifecycle voting, majority, confidence,
  support, correctness, utility, or top-k selection;
- contradiction/content/result/action-outcome-length-triggered extra, skipped,
  or shifted Dream/snapshot/checkpoint calls, including fixed-slot overflow and
  exact cutoff/tie cases;
- provisional/superseded/contradicted/abstained/malformed/failed status swaps
  and multiple matching/conflicting records that alter pre-output cursor order,
  exhaustion, slot count, length, padding, candidate position, returned bytes,
  or expose the audit-only reason;
- filename/order/length/count/latency/error channels;
- candidate and index smuggling;
- scorer/comparator write attempts;
- post-fork assigned-memory residue;
- assignment/treatment/opaque-label/lane mutations changing a P1 compiler
  seed, paired P1 lanes receiving unequal compiler draws, cut/sham resampling,
  or descriptive independent draws entering P1;
- evaluation-to-life write attempts;
- cross-target and cross-life cache residue;
- any B3-to-successor prompt/target/threshold flow or automatic promotion; and
- DEV-selector input/output expansion, raw/per-target metric access, repeated
  selection, and reverse flow from frozen outputs to DEV cognition; and
- crash/restart before and after every sealed transition.

Passing these tests demonstrates boundary conformance only, not scientific
success.
