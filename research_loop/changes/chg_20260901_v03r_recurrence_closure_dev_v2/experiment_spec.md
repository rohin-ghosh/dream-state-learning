# v0.3-R recurrence-closure development transition v2

Date: 2026-09-01 PT. Status: **replacement proposal only; unratified**.
Change ID: `chg_20260901_v03r_recurrence_closure_dev_v2`.

This spec implements option C from the exact v1 rework consensus. It asks one
question only: after a shared recurrent lifetime and one bounded thinker pass,
does query-guided allocation of later public evidence change whether a live
model writes the predeclared local connection? It does **not** ask or reveal a
final task question, run a final thinker, emit an answer, use `RELEASE`, train
or mount a LoRA, or recommend a next experiment.

## Development claim and unit of observation

The strongest allowed result is descriptive:

> On these six aligned v0.3-R development lives, own-query-guided view
> allocation changed later provisional proposal closure relative to both a
> no-feedback selector and a precommitted matched-distractor selector, after
> the frozen exchangeability, exact-byte shortcut, compiler, and query-copy
> controls.

Every life and collision pair is reported. Three pairs are calibration units,
not an inferential sample. No reliability, robustness, scaling, memory
advantage, independent discovery, autonomous learning, action improvement,
parametric-memory, beyond-context, or headline claim is permitted.

## Frozen population and model

- Generator: exact reviewed `CounterfactualConfluenceV03R` implementation.
- Skin: `aligned` only.
- Development seeds: 0, 1, and 2; both collision twins for each seed: six
  logical lives total. Heldout, additional skins, and replication seeds remain
  unopened.
- Dream and thinker model: `Qwen/Qwen2.5-32B-Instruct`, exact revision
  `5ede1c97bbab6ce5cda5812749b4c0bdf79b18dd`, clean bf16 base, no adapter.
- Every model operation uses a fresh isolated provider session. Prompt,
  config, response, receipt, reset, exact token evidence, timestamps, parser
  outcome, and physical/attributed call identity are immutable.
- DREAM: temperature 0.2, top-p 0.95, maximum 128 generated tokens. THINK:
  temperature 0, top-p 1, maximum 128 generated tokens per operation. Seeds
  are deterministic digests of the frozen run/life/stage/round/call slot.
- Invalid, truncated, or schema-invalid output consumes its scheduled slot and
  is recorded. It is never repaired, retried, silently parsed, or fed a truth
  outcome.

## Exact prompt-local alias boundary

Long content hashes and internal handles are never copied by the model.
Before each call, the trusted renderer creates a call-local alias table:

- public experiences: `E0`, `E1`, ...;
- pre-existing memory items: `M0`, `M1`, ...;
- endpoints present in that bounded view: `X0`, `X1`, ...;
- new proposal-local objects: `N0` only.

Each alias is mechanically bound outside provider bytes to the SHA-256 of its
canonical source object. Assignment is a deterministic permutation derived
from the frozen call seed, not semantic rank. The provider sees the aliases,
the public content necessary to reason, and the exact operation schema; it
does not see hashes, global semantic IDs, life IDs, arm IDs, query IDs, or the
alias ledger. Parser output is resolved through the immutable ledger. Unknown,
duplicate, cross-call, or type-wrong aliases reject. Citation and endpoint
copying therefore uses short prompt-local handles rather than brittle
64-character digests, while provenance remains exact.

The alias ledger, rendered prompt, and provider receipt are private/final-
truth invariant. A permutation control rerenders the same view under new
aliases and must preserve the offline semantic result.

## Prompt-complete DREAM contract

Every DREAM prompt contains the full generic instruction below, one selected
public trigger, at most six recipient-local pre-existing memory neighbors, the
call-local alias table as visible handles, and no game answer or requested
connection tuple:

> Inspect only the visible public event and bounded memory. Emit exactly one
> JSON operation from the schema. A useful operation records one local concept,
> relation, reinforcement, or replacement that follows from the visible
> material. Cite only visible `E*`/`M*` handles and use only visible `X*`/`M*`
> endpoints. Do not assume that any prior proposal is true. If no bounded local
> update is warranted, emit `PASS`. You do not grade, verify, or support your
> own output.

The only accepted bare JSON objects, with exact fields and no extra keys, are:

```text
{"op":"PASS","reason_code":"NO_BOUNDED_UPDATE"}
{"op":"CREATE_CONCEPT","new_alias":"N0","entity_alias":"X0","concept_type":"<1..64 chars>","canonical_text":"<1..512 chars>","citations":["E0"|"M0",...]}
{"op":"CREATE_EDGE","left_alias":"X0"|"M0","relation_label":"<1..64 chars>","right_alias":"X1"|"M1","polarity":"POSITIVE"|"NEGATIVE"|"UNKNOWN","canonical_text":"<1..512 chars>","citations":["E0"|"M0",...]}
{"op":"REINFORCE","memory_alias":"M0","canonical_text":"<1..512 chars>","citations":["E0"|"M0",...]}
{"op":"SUPERSEDE","memory_alias":"M0","replacement_kind":"CONCEPT"|"EDGE","left_or_entity_alias":"X0"|"M0","relation_label":"<0..64 chars; empty only for CONCEPT>","right_alias":"X1"|"M1"|null,"polarity":"POSITIVE"|"NEGATIVE"|"UNKNOWN","canonical_text":"<1..512 chars>","citations":["E0"|"M0",...]}
```

Citation arrays contain 1--7 distinct visible handles in prompt order. Each
non-PASS output becomes a new harness-assigned content-addressed proposal row.
All parsed writes remain `provisional`; reinforcement and supersession create
append-only events and never mutate or delete earlier rows during cognition.
Parser rejection and PASS are also append-only artifacts. There is no online
truth check, admission, support flag, contradiction flag, reason code,
precision signal, or accept/reject response visible to any later model call.

## Prompt-complete THINK_0 contract

After the shared `MEMORY_0` checkpoint freezes, one fresh goal-conditioned
thinker runs per life for at most 12 one-operation provider calls. It sees the
public non-answer operational probe and immutable provisional memory. It is
instructed to retrieve, follow, hypothesize, predict, revise, or backtrack in
order to identify **one missing or conflicting dependency**; it must terminate
with `REQUEST_DREAM` for exactly one mechanically created confusion or `DEFER`.
It cannot answer a final task and `RELEASE` is absent from the allowed schema.

The exact allowed bare JSON operations are the current typed-thinker v1.1
schemas with these fields:

```text
FORM_SUBGOAL(op,subgoal_id,parent_subgoal_id,description)
QUERY(op,subgoal_id,query_key,subject_entity_id,relation_id,object_entity_id)
FOLLOW(op,subgoal_id,from_semantic_id,to_semantic_id)
HYPOTHESIZE(op,subgoal_id,hypothesis_id,claim,cited_semantic_ids,parent_hypothesis_ids)
PREDICT(op,subgoal_id,hypothesis_id,prediction_entity_id)
REVISE(op,subgoal_id,hypothesis_id,new_hypothesis_id,revised_claim,cited_semantic_ids,revision_kind)
BACKTRACK(op,subgoal_id,reason_code,promote_hypothesis_id)
REQUEST_DREAM(op,confusion_ids)
DEFER(op,reason_code,confusion_ids)
```

Every listed name denotes a JSON string except nullable
`parent_subgoal_id`, `object_entity_id`, and `promote_hypothesis_id`, and the
three `*_ids` fields, which are arrays of distinct strings. Allowed enum values
and handle syntax are emitted in the prompt from the frozen typed-thinker
contract. No operation may invent a checkpoint handle. The trusted scheduler
replays raw operations and mechanically projects at most one typed frontier.
Scratch hypotheses, predicted answers, free rationale, citations, and model
confidence cannot enter that frontier. A failed/DEFER thinker yields no own
frontier and remains a reported outcome; it is not repaired.

## Selector-only treatment and three arms

The full own or precommitted matched frontier tuple is consumed only by the
trusted selector. The tuple, query key, source goal, vocabulary hash, life,
arm, own/distractor identity, selection score, target tuple, and closure label
are absent from every provider request/config/parser/memory/receipt field.

The selector deterministically enumerates recipient-local candidates and
selects one public trigger plus at most six pre-existing neighbors. Provider
bytes contain only the generic DREAM contract and that bounded view rendered
with prompt-local aliases. All selection metadata stays in an outside-
cognition ledger. The exact three experimental arms are:

1. `no_feedback`: ignores the thinker frontier and applies the frozen
   target-blind intrinsic view schedule.
2. `own_selector`: uses the mechanically projected own frontier only to rank
   bounded views.
3. `matched_distractor`: uses a precommitted distinct recipient-local,
   same-kind frontier only to rank bounded views.

The physical shared prefix and THINK_0 are executed once per life, then
cloned byte-identically before arm selection. A frontier is never evidence,
a citation, a premise, a proposal, a memory item, or an endpoint supplied to
the model. Positive results are called query-guided view allocation, never
independent discovery.

Before any provider call, an independently generated exchangeability manifest
enumerates own and distractor candidate sets and binds witness count, endpoint
frequency, route/effect position, initial concept availability, bounded-memory
rank, lexical overlap, view count, and mechanical closure opportunity. The
pair must satisfy the predeclared equality/stratification rule; otherwise the
life is invalidated without choosing a replacement from its outcome.

## Exact recurrent schedule and accounting

Per life, independently generated immutable schedules are:

- seed-0/2 life: 46 WAKE, 22 periodic REACTIVATE, 16 target-blind SLEEP,
  then 16 RETURN_SLEEP calls in each of the three arms: 132 DREAM calls;
- seed-1 life: 49 WAKE, 24 periodic REACTIVATE, 16 target-blind SLEEP,
  then 16 RETURN_SLEEP calls in each arm: 137 DREAM calls.

Across four seed-0/2 lives and two seed-1 lives this is exactly **802 physical
recurrent DREAM calls**: 514 in six physically shared prefixes and 288 after
the three-way branch. THINK_0 uses at most 12 physical one-operation calls per
life, hence at most **72 physical THINK calls**. Early DEFER is not padded.

The complete six-life schedule is generated independently of execution. The
experiment ledger reconciles every scheduled call with exactly one provider
receipt, response, parser outcome, proposal/PASS/rejection row, alias ledger,
life, stage, and arm attribution. Shared prefix calls are physical once but
attributed to all three arms. No cache, KV state, index, workspace, provider
session, or hidden memory crosses physical calls or lives.

## Separately frozen closure baselines and controls

Baseline compute is outside the 802/72 recurrent totals unless explicitly
marked shared. No baseline sees a final question or answer.

| condition | physical model calls | input ceiling | output ceiling | notes |
|---|---:|---:|---:|---|
| full-context one-shot closure | 6 DREAM | 8192 tokens/call | 128/call | one complete 46/49-event public transcript per life; fail, never truncate, over ceiling |
| iterative episodic RAG | 96 DREAM | 2048 tokens/call | 128/call | 16 fresh calls/life, one trigger + top-6 public/semantic neighbors, frozen retriever |
| wake-only checkpoint | 0 additional; 282 shared WAKE calls attributed | exact shared ledger | exact shared ledger | score append-only provisional rows immediately after WAKE |
| target-blind recurrent checkpoint | 0 additional; 514 shared prefix calls attributed | exact shared ledger | exact shared ledger | score `MEMORY_0` before THINK/selection |
| no-feedback recurrence | 0 additional beyond its 96 RETURN_SLEEP calls already in 802 | exact recurrent ledger | exact recurrent ledger | one of the three primary arms |
| deterministic retrieval only | 0 | n/a | n/a | selected-view opportunity and lexical/rank ceiling |
| no-model tuple copier | 0 | n/a | n/a | target tuple is unavailable to provider; expected closure zero |
| query-copy / canonical-string compiler | 0 | n/a | n/a | scorer-side agenda and canonical route/effect feature ceilings, labeled compiler assistance |
| public witness oracle | 0 | n/a | n/a | postcommit closure-opportunity ceiling only |

Actual prompt/generated tokens, physical and attributed calls, resets, early
terminals, top-k/read counts, and wall time are reported separately for every
condition. Full-context, RAG, and recurrent prompts use the same generic DREAM
operation schema. Compiler/query-copy controls do not count as model reasoning.

The exact-byte shortcut audit covers rendered text, order/position, public
IDs, scorer-side agenda coordinates, canonical route/effect strings, status
fields, combined compiler features, and every provider-visible byte family.
Controls include masked content, alias/citation permutation, wrong connector,
near miss, deterministic retrieval, canonical string, query copy, and
compiler-only. Survivors are reported rather than silently removed.

## MEMORY_1 and blinded offline closure scoring

After all 16 RETURN_SLEEP slots, each arm freezes `MEMORY_1` plus the complete
raw proposal/PASS/rejection stream and alias ledgers. This is an irreversible
cognition barrier. Only then may an isolated scorer load public witness data,
the predeclared target registry, and the frozen artifacts. The scorer has no
provider and cannot alter memory, route a retry, trigger repair, launch another
run, or promote a status.

For each proposal it reports separately:

1. **raw exact closure**: resolved left endpoint, normalized relation, right
   endpoint, and polarity equal the predeclared connection;
2. **witness-bound exact closure**: raw exact closure plus cited public route
   and effect records that share the same connector and bind the exact source,
   target, direction, and effect polarity;
3. connector/effect-polarized correctness, citation coverage, duplicate and
   near-miss counts, false/unsupported proposal counts, and first closure slot;
4. own-minus-no-feedback and own-minus-distractor life/pair deltas;
5. residual model closure over every deterministic/query-copy/compiler
   control, with compiler contribution labeled separately.

Every cognition-time proposal remains `provisional` forever in the raw
artifact. Offline labels live only in a separate score table. Adaptive
repeated, permuted, contradicted, and near-miss attacks across all sixteen
RETURN_SLEEP slots must prove that proposal absence, score, status, or scorer
rationale never changes a later selection or provider byte.

## Independently derived required-artifact inventory

Completeness is derived from the frozen schedule/baseline manifests, never
from producer-declared `done.json`. The required graph includes:

- one exact intake/ratification binding, workflow/spec lock, two immutable
  independent pre-GPU reviews, environment/model/decoding manifest, global
  schedule manifest, baseline manifest, exchangeability manifest, shortcut
  audit, and required-artifact inventory;
- six public-life packets, six per-life schedules, six shared-prefix states,
  six THINK_0 machine/replay/frontier packets, six `MEMORY_0` checkpoints,
  eighteen branch packets and eighteen `MEMORY_1` checkpoints;
- exactly 802 recurrent DREAM slots/materials/responses/receipts/parsers/alias
  ledgers and matching PASS/rejection/proposal linkage; zero or one proposal
  row per DREAM slot; at most 72 THINK slots with matching operation/replay
  linkage and no synthetic padding;
- 288 RETURN_SLEEP selector traces and candidate-set/ranking/view bindings;
  102 additional baseline model calls (6 full-context + 96 RAG), each with the
  same complete call boundary; wake-only and target-blind shared-call
  attribution without duplicate physical receipts;
- eighteen blinded scorer packets and per-proposal score tables, six
  life-level and three pair-level descriptive summaries, all baseline/control
  traces and actual compute, and sanitized trajectory exports with scorer,
  private, and final-task fields absent;
- exactly one atomic `started.json`, monotonic atomic `progress.json` updates
  with schedule counters and heartbeat, and exactly one terminal
  `done.json` or `failed.json`; `done.json` may appear only after independent
  artifact verification passes. A complete SHA-256 manifest covers every
  required node and referential-integrity edge.

The verifier rejects missing, duplicate, reordered, rewritten, unreferenced,
or orphaned calls, aliases, selectors, views, proposals, checkpoints, scores,
baselines, reviews, markers, or trajectory rows even if all producer hashes
are internally consistent.

## GPU workflow, durability, and unconditional stop

Before sync or provider execution: all option-C implementation modules and
tests exist; population/shortcut, visibility, exchangeability, provider,
schedule/accounting, alias, provisional-only, scorer-isolation, artifact,
remote-recovery, and exact-scope gates pass; the full closure is hash-frozen;
fresh Fable and fresh Sol reviewers independently approve identical bytes;
and Rohin has ratified the exact consensus, paused state, and only the two
requested scopes.

The remote job uses idempotent start/status commands. It atomically creates
`started.json`, updates schedule-indexed `progress.json` and heartbeat, resumes
only from verified phase barriers, and creates exactly one `done.json` or
`failed.json`. A 12-hour watchdog may observe, restart an infrastructure poll,
or report a verified remote state; it may not change science bytes, infer
success, skip calls, rerun a failed science job, or launch a new experiment.

Every valid result, null, control win, integrity failure, timeout, or model
failure stops unconditionally at a human boundary after artifacts are pulled
and verified. Follow-up, repair, replication, LoRA, heldout access, external
action, claim promotion, lease/spend change, or a second GPU run requires a
new intake and exact human ratification.

This proposal intentionally names future implementation modules in its
workflow. Until this replacement intake is independently interpreted,
criticized, adjudicated, and ratified, the supervisor authorization gate and
the missing implementation/preflight modules both fail closed. No provider or
GPU operation is authorized by these proposal bytes.
