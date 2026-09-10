# v0.3-R standalone recurrence-closure interface calibration v2d

Date: 2026-09-01 PT. Status: **standalone proposal only; unratified**.
Change ID: `chg_20260901_v03r_recurrence_closure_dev_v2d`.

Rohin's latest directive is quoted verbatim:

> keep it goign nd get it done on the gpu once youve finsiehd the deisgn

The directive asks for persistence, not bypass. This package must complete new
interpretations, critique, consensus, exact ratification, implementation,
tests, closure, and independent review before its zero-science GPU preflight
or one bounded science run. Nothing in v2, v2a, or v2b is inherited.

Ratification must match, in exact sorted order, all and only these four atoms:
`analysis:bound_postcommit_v03r_closure_v2d`,
`gpu:v03r_recurrence_closure_dev_v2d`,
`implementation:v03r_recurrence_closure_dev_v2d`, and
`testing:pre_gpu_v03r_recurrence_closure_dev_v2d`; its forbidden scope must
also exactly equal the sorted canonical proposal. Extra, omitted, reordered,
or overlapping atoms fail. Human approval first releases only scoped v2d
implementation and local pre-GPU testing. The analysis atom is usable only by
the sealed postcommit scorer/result path. The GPU atom is dormant until
implementation, tests, transitive closure, fresh independent approval, and
author-side scientific-advocate approval all pass; it first permits only the
zero-science preflight, which must pass before public input or science.

## Question, unit, and exclusions

This is an exact six-life interface calibration. It asks whether, among the
predeclared lives whose post-prefix primary branch is defined, a trusted
`THINK_0` coordinate used only to allocate sixteen later public views changes
the same base model's provisional local-connection proposals relative to an
exact target-blind no-feedback selector and a fixed distractor selector.

The six units are aligned-skin development seeds 0, 1, and 2 with both
collision twins. They are named calibration cases, not a random sample. Every
life, including `PRIMARY_UNDEFINED`, is reported. There is no final question,
final thinker, answer, `RELEASE`, answer valve, paired-answer score, LoRA,
adapter, transport, online truth/admission/support/normalization, automatic
pool, automatic go, or automatic next experiment.

## Static integrity before any provider call

Before sync or provider activity, local static preflight freezes and verifies:

- exact `CounterfactualConfluenceV03R` code and the six public packet schemas,
  with heldout and other skins unopened;
- all per-life WAKE/REACTIVATE/SLEEP schedules and global shared-prefix count;
- exact model/tokenizer identifier `Qwen/Qwen2.5-32B-Instruct`, revision
  `5ede1c97bbab6ce5cda5812749b4c0bdf79b18dd`, clean bf16 base, no adapter;
- exact ASCII schemas, alias/redaction rules, target-blind and q-guided
  selector algorithms, measured-balance formulas, arm order, logical seeds,
  phase-A/phase-B inventory schemas, controls, scorer, allowlist, workflow,
  tests, transitive imports/resources, and exact authorized scope.

Malformed public bytes, duplicate IDs, schedule mismatch, unresolved import or
resource, model/tokenizer hash mismatch, nonfinite static arithmetic, or
nondeterminism is `STATIC_INTEGRITY_FAILURE`. It stops before sync and before
every provider call. Measured balance is deliberately not computed here: it
requires model-produced `MEMORY_0` and `THINK_0`.

## Reviewed sync and exact zero-science H100/provider preflight

Only after exact ratification, completed implementation, static gates, a full
lock, fresh independent approval, and author-side scientific-advocate approval
over identical inspectable bytes may the workflow sync reviewed bytes. The
advocate cannot override or substitute for the independent verdict. It then
runs one lock-bound **zero-science** remote preflight before loading any public
life packet or making a provider science call.

The preflight requires exactly one `NVIDIA H100 NVL` with
`total_memory_mib >= 95000` and records the actual total (known device: 95,830
MiB), UUID, driver/CUDA/runtime, bf16 capability, package lock, and allocator
telemetry. It loads the exact clean resident base-weight engine, with prefix
caching and request truncation disabled, and exercises the exact immutable
`research_loop/schemas/v03r_zero_science_envelopes_v2d.json` resource. That
resource deterministically generates exact 2048-token DREAM, 8192-token THINK,
8192-token full-context, and 2048-token RAG ASCII inputs under pinned tokenizer
file hashes, requests exact 256/128/256/256 output maxima, and requires exactly
two calls per class in its frozen order. The resource binds all eight byte and
token-ID hashes, logical seeds, provider settings, and peak/reset thresholds.
For every call preflight records unique session and receipt IDs, peak allocated
and reserved MiB, zero active sequences before and after each call, empty
conversation/KV/prefix-cache/request/tool/adapter/workspace state, and exact
reset telemetry. One immutable engine may remain resident; call-derived state
may not. The synthetic bytes contain no public-life, target, witness, or final
task material and are never scientific observations.

Any device, capacity, allocation, cache, truncation, active-sequence, reset,
session, receipt, tokenizer, model, or envelope mismatch creates
`ZERO_SCIENCE_PREFLIGHT_FAILURE` and stops before public life inputs and all
provider science calls.

## Science provider boundary and ASCII JSON

Every science operation has a unique physical call ID, session ID, and receipt.
Requests, configs, responses, exact tokenizer IDs, resets, timestamps, parser
outcomes, and physical/attributed slots are immutable. Prefix caching and
request truncation remain disabled. No conversation, KV, cache, request,
workspace, adapter, index, or hidden state crosses calls or lives.

DREAM uses temperature `0.2`, top-p `0.95`, `max_new_tokens=256`. THINK uses
temperature `0`, top-p `1`, `max_new_tokens=128`. All outputs are bare canonical
ASCII JSON: UTF-8/ASCII, no BOM or surrounding whitespace, separators `,` and
`:`, schema field order, unique exact keys, no terminal newline. Free text uses
bytes `0x20..0x7e` except quote and backslash; controls, DEL, non-ASCII, quote,
and backslash reject. `canonical_text` is 1..192 bytes; concept/relation text
is 1..64 bytes. The raw response must equal canonical reserialization and the
whole DREAM operation must tokenize to `<=256` IDs with
`add_special_tokens=false`. Over-cap, noncanonical, truncated, or malformed
output consumes its one scheduled slot as rejection without repair or retry.

Exact DREAM shapes, in field order, are:

```text
PASS(op,reason_code="NO_BOUNDED_UPDATE")
CREATE_CONCEPT(op,new_alias="N0",entity_alias,concept_type,canonical_text,citations)
CREATE_EDGE(op,left_alias,relation_label,right_alias,connector_alias,polarity,canonical_text,citations)
REINFORCE(op,memory_alias,canonical_text,citations)
SUPERSEDE(op,memory_alias,replacement_kind,left_or_entity_alias,relation_label,right_alias,connector_alias,polarity,canonical_text,citations)
```

Aliases are visible call-local `E*`, `M*`, `X*`, `C*`, and `N0`; citations are
1..7 distinct `E*`/`M*` handles in visible item order. Polarity is `POSITIVE`,
`NEGATIVE`, or `UNKNOWN`. All parsed writes are harness-addressed, append-only,
and forever `provisional`; reinforce/supersede append events and never mutate.

## Connector aliases and redaction

Each namespace is a bijection over visible objects. For namespace `T` and
object hash `h`, sort by
`SHA256("v2d-alias\0"||T||"\0"||view_sha256||"\0"||stage||"\0"||logical_round||"\0"||h)`
then `h`, and assign `T0,T1,...`. The derivation excludes arm, physical order,
target, q, stratum, semantic rank, and source order. Repeated occurrences of
one connector reuse one `C*`; distinct connectors never do. The external C
ledger binds only `SHA256("connector\0"||raw_connector_ascii)`.

Rendering starts from typed structure, replaces every connector-bearing value
and connector-derived text with C aliases, and only then generates text. Exact
provider/cognition bytes must contain none of the canonical raw-ID set, hashes,
ledger, selector metadata, target/q, or sentinel
`V2D_RAW_CONNECTOR_SENTINEL_7Q9X`. Any occurrence rejects before its provider
call. Unknown, duplicate, cross-call, non-bijective, or type-wrong aliases
reject without repair. Shared C equality remains visible public structure and
is explicitly controlled; it is not discovery.

## Shared prefix and THINK_0

All six shared prefixes execute before any branch:

- each of four seed-0/2 lives: 46 WAKE + 22 REACTIVATE + 16 target-blind SLEEP;
- each of two seed-1 lives: 49 WAKE + 24 REACTIVATE + 16 target-blind SLEEP.

This is exactly 514 physical shared recurrent DREAM calls. Each has one receipt
and is attributed to all three potential arms. Every output is provisional.
Each life then freezes `MEMORY_0` and runs one fresh `THINK_0` for a terminal-
justified prefix of 0..12 operations, so the global observed THINK count is
0..72 with no padding.

THINK shapes are `FORM_SUBGOAL`, `QUERY`, `FOLLOW`, `HYPOTHESIZE`, `PREDICT`,
`REVISE`, `BACKTRACK`, `REQUEST_DREAM`, and `DEFER` under exact frozen field
orders and typed-handle schemas. It sees only the non-answer public operational
probe and provisional `MEMORY_0`. There is no `RELEASE` or final thinker.

The public probe provides exact own fields `source_entity_id` and
`target_entity_id`. A valid primary request must terminate in one mechanically
projected `REQUEST_DREAM` whose sole q is exactly
`q_own=(source_entity_id,"causal_join",target_entity_id)`. DEFER, failure,
exhaustion, malformed output, no sole q, or a different q makes that life
`PRIMARY_UNDEFINED`; it is a model/interface outcome, not integrity failure.

The distractor is never searched or matched adaptively. Freeze exactly
`q_dist=(matched_distractor_source_entity_id,"causal_join",
matched_distractor_target_entity_id)` from that same life's
`CounterfactualConfluenceV03R.render_operational_probe("aligned")` public
fields. Missing, duplicate, malformed, or equal-to-own distractor fields are
post-prefix integrity failure, not a target-search opportunity. No resampling,
replacement, optimization, reuse from another life, or outcome access exists.

## Complete candidates and the exact target-blind no-feedback policy

For every life, `PUBLIC` is every public episode sorted by
`(sequence_index,public_id)` and `MEMORY` is every provisional `MEMORY_0` row
sorted by `(creation_slot,semantic_sha256)`. One candidate exists per public
trigger. Duplicate IDs/order or nondeterminism is integrity failure.

The **target-blind no-feedback** neighborhood for trigger `r` ranks each memory
row `m` by the descending tuple:

```text
(
  exact_public_citation_hashes_shared_by(m,r),
  exact_typed_endpoint_values_shared_by(m,r),
  tokenizer_id_set_jaccard(canonical_trigger_bytes(r),canonical_memory_bytes(m)),
  -creation_slot
)
```

and ascending `semantic_sha256` as final tie. It takes the first six rows. A
no-feedback candidate ranks by descending:

```text
(
  number_of_valid_public_citations_in_view,
  number_of_distinct_typed_endpoint_values_in_view,
  tokenizer_id_set_jaccard(canonical_trigger_bytes,canonical_neighborhood_bytes),
  -trigger_sequence_index
)
```

with ascending `SHA256(canonical_view_bytes)` final tie. It selects the first
sixteen distinct candidates in rank order into logical rounds 0..15. The
algorithm reads no q, target, THINK state, arm identity, scorer, truth, or
closure predicate. Its complete ranks and components are frozen outside
cognition.

For q-guided own/distractor selection, the complete candidate universe is the
same one-trigger-per-public-record set. Relative to one q, the four exact
witness kinds are `SOURCE_ENDPOINT_MEMORY` (a typed memory row binding q's
source), `TARGET_ENDPOINT_MEMORY` (a typed memory row binding q's target),
`ROUTE_PUBLIC_RECORD` (a `valve_route` record whose structured `source_id`
equals q's source), and `EFFECT_PUBLIC_RECORD` (an `intervention_effect`
record whose structured `target_id` equals q's target). Text-only matches are
not witnesses. For memory row `m` and trigger `r`, sort by the descending tuple

```text
(
  exact_q_endpoint_hits(m),
  exact_typed_endpoint_values_shared_by(m,r),
  exact_public_citation_hashes_shared_by(m,r),
  tokenizer_id_set_jaccard(q_bytes,canonical_memory_bytes(m))
)
```

and ascending `(creation_slot,semantic_sha256)` as the complete tie key; take
the first six rows. Rank every resulting candidate by the descending tuple

```text
(
  candidate_structural_opportunity,
  number_of_distinct_required_witness_kinds_in_view,
  exact_q_endpoint_hits_in_view,
  tokenizer_id_set_jaccard(q_bytes,canonical_view_bytes),
  -trigger_sequence_index
)
```

and ascending `SHA256(canonical_view_bytes)` as the final tie. Booleans are
integers 0/1; counts are exact base-10 integers. Freeze the full rank,
components, and tie disposition before selecting the first sixteen distinct
candidates. No pruning occurs before the complete rank is recorded.

`q_bytes` is exactly
`source_entity_id + "\ncausal_join\n" + target_entity_id`, encoded as ASCII
without a trailing newline. Canonical memory/view bytes use the serializer
above. The one own selector uses `q_own`; the one distractor selector uses the
fixed `q_dist`. Neither selector reads proposals, outcomes, scores, or the
other selector's ranks.

Token set-Jaccard uses the pinned tokenizer with
`add_special_tokens=false`: `|A intersect B|/|A union B|`, exact reduced
rationals, both-empty=`1`, one-empty=`0`, compared by integer cross
multiplication.

If `q_own` is invalid or any of no-feedback, own, or distractor complete
universes has fewer than sixteen distinct candidates, the life is
`PRIMARY_UNDEFINED`. It receives no branch, selector trace, MEMORY_1, scorer,
full-context, or RAG call. Its shared prefix/THINK artifacts and exact terminal
reason remain required. There is no duplicate view, padding, target change,
or replacement.

## Post-prefix measured balance and defined lives

Only after all six `MEMORY_0` and `THINK_0` artifacts freeze, and before every
branch/exploratory call, trusted prebranch code computes measured balance for
each otherwise defined life. It compares own and fixed-distractor selectors;
no-feedback is not a matching target.

The exact witness enum is `SOURCE_ENDPOINT_MEMORY`, `TARGET_ENDPOINT_MEMORY`,
`ROUTE_PUBLIC_RECORD`, `EFFECT_PUBLIC_RECORD`. For each own/distractor side the
manifest contains:

- candidate-set size `len(PUBLIC)`;
- four witness counts, each the number of complete-universe candidate views
  containing that exact witness, and four availability booleans `count>0`;
- selected-view count, exactly sixteen;
- source and target endpoint frequencies, each the number of complete-universe
  candidate views containing the exact typed endpoint;
- route/effect provider positions: concatenate the sixteen selected prompts in
  logical-slot order, with trigger at item 1 and frozen neighbors at items
  2..7; the one-based global position is `7*slot_index+item_position`, and the
  metric is the minimum position containing the exact structured witness;
- four full-selector required-item ranks: the minimum one-based complete-rank
  candidate containing each exact witness, using the fully specified selector
  and ties above;
- q-to-selected-union lexical overlap: tokenizer-ID set-Jaccard between exact
  `q_bytes` and the concatenation of the sixteen canonical selected-view byte
  strings separated by one ASCII line feed and no terminal separator;
- `selected_union_mechanical_opportunity` as defined below.

An absent provider position or full-selector rank is the literal enum
`MISSING`, never an integer or infinity. Every raw value, exact reduced
rational numerator/denominator, absolute difference, input hash, selector-code
hash, tie disposition, and state is recorded.

`candidate_structural_opportunity` is a **per-candidate selector feature**:
that one rendered candidate view contains endpoint, route, and effect evidence
with a shared canonical connector. `selected_union_mechanical_opportunity` is
the **measured-balance field**: the union of all sixteen selected views contains
the four exact required witnesses with one shared connector, correct direction,
and effect polarity. The two names, scopes, and artifacts never alias.

Compare own with fixed distractor. Exact equality is required separately for
candidate-set size, all four witness counts, all four availability booleans,
selected-view count, and selected-union opportunity. The endpoint-frequency
difference is the maximum of the absolute source and target differences. The
provider-position difference is the maximum of the absolute route and effect
differences. The full-selector-rank difference is the maximum absolute
difference over all four witnesses. The lexical difference is the exact
absolute rational difference. Tolerances are endpoint frequency `<=1`,
provider position `<=1`, full-selector rank `<=1`, and lexical difference
`<=1/10`, all compared by integer cross multiplication.

`EXACT_MEASURED_BALANCE` means every equality passes, no value is `MISSING`,
and all four numeric differences are zero. `NEAR_MEASURED_BALANCE` means every
equality and tolerance passes, no value is `MISSING`, and at least one numeric
difference is nonzero. `OUT_OF_MEASURED_BALANCE` is a legitimate deterministic
finite equality/tolerance failure or any explicit `MISSING` required item.
These states are descriptive interface diagnostics and confer no population-
balance or identification property.

Malformed/unavailable inputs, tokenizer mismatch, duplicate fields,
nondeterminism, exception, NaN/infinity, or failure to recompute is
`POST_PREFIX_INTEGRITY_FAILURE`. Because all measured-balance rows are computed
before any branch, one such failure stops every remaining branch/exploratory
call globally and reports all sunk 514 shared DREAM and observed THINK artifacts.
It never erases or relabels sunk calls and is not `PRIMARY_UNDEFINED` or OUT.

A life with valid q and at least sixteen candidates in all arms is a defined
life regardless of EXACT/NEAR/OUT balance. Let `D` be the count of defined lives
after a successful global measured-balance gate; `0<=D<=6`.

## Three arms, same target, common randomness, and exact order

Each defined life has `no_feedback`, `own_selector`, and `matched_distractor`
arms, sixteen RETURN_SLEEP rounds each. All arm outcomes are scored against the
same `q_own`. `q_dist` affects trusted view selection only and never changes a
scorer target, proposal target, provider instruction, or outcome definition.

For life `l` and logical round `r`, all three corresponding calls use decoding
seed `SHA256("v2d-return-seed\0"||frozen_run_seed||"\0"||l||"\0"||r)`.
It excludes arm, view, physical slot, physical order, and session/receipt ID.
The sampling config is otherwise byte-identical; provider requests differ only
through exact rendered selected-view bytes and their content-derived aliases.
Physical call/session/receipt IDs remain unique and never determine decoding.

Physical execution is interleaved per life and round. Sort the six life IDs;
the life rank modulo three is its order offset. Base arms are
`[no_feedback,own_selector,matched_distractor]`; at round `r`, execute the cyclic
rotation by `(r+offset) mod 3`. Each arm receives 16 calls; within a life its
three physical-position frequencies differ by at most one, and across six
predeclared lives offsets occur twice each. The entire order is frozen before
science. A resettable fake/provider test replays all three cyclic starting
orders and requires identical semantic results per `(life,arm,round)` under
the common logical seed.

## Exact dynamic schedule

After successful static/zero-science/global post-prefix integrity gates:

- shared recurrent DREAM calls: exactly `514`;
- branch recurrent DREAM calls: exactly `48*D`;
- total recurrent DREAM calls: exactly `514+48*D` (range 514..802);
- observed THINK_0 calls: exact terminal-justified prefix `0..72`;
- exploratory DREAM calls: exactly `17*D` (range 0..102), consisting of one
  full-context and sixteen RAG calls per defined life;
- selector traces: exactly `48*D`;
- MEMORY_1 checkpoints and branch scorer packets: exactly `3*D`.

Undefined lives add zero to every D-scaled class. Exploratory calls execute only
for defined lives after their branches; full-context/RAG are
`EXPLORATORY_CEILING`, never matched causal, memory, efficiency, or architecture
baselines. Full-context input ceiling is 8192 tokens; RAG is 2048; both use the
same DREAM ASCII/256-token/192-byte contract and fresh sessions.

## Phase A raw cognition seal

After all scheduled science calls for D defined lives, a scorer-inaccessible,
independent phase-A verifier derives requirements from the frozen terminal and
schedule manifests and verifies:

- 514 shared plus `48*D` branch DREAM calls, `0..72` terminal-justified THINK,
  `17*D` exploratory calls, `48*D` selectors, `3*D` MEMORY_1;
- every exact request/config/response/receipt/reset/token/parser/alias/outcome
  edge; zero-or-one schema outcome per DREAM slot; unique sessions/receipts;
- every raw provisional proposal, PASS, rejection, checkpoint, candidate rank,
  measured-balance row, arm order, common logical seed, undefined-life terminal,
  and sunk prefix artifact;
- absence of scorer/allowlist/target-registry imports, deserialization, fields,
  status, or routing in every cognition process and serialized trajectory.

The verifier writes one content-addressed `phase_a_raw_seal.json` over the exact
raw graph. Missing, duplicate, reorder, rewrite, orphan, forbidden import, or
cardinality error creates `failed.json` and human stop. Only a valid raw seal
unlocks the no-provider scorer. Score/control artifacts are not phase-A inputs.

## Comparable controls, privileged bounds, and four offline metrics

After the phase-A seal, comparable deterministic controls run per exact
selected slot for each defined life/arm. Each reads exactly the provider-visible
trigger, bounded memory, aliases, schema, and slot history available at that
slot; it reads no q, target registry, canonical connector ID, raw alias ledger,
truth, allowlist, future slot, or other arm. Each deterministically emits at
most one canonical schema-legal proposal or one explicit rejection/PASS under
the same alias and ASCII/token parser:

- `visible_byte_constructor`;
- `visible_shared_c_join`;
- `visible_literal_relation_constructor`.

Masked-content, wrong-connector, citation-permutation, and order-permutation
are separately labeled input ablations, not comparable ceilings. `query_copy`
and `public_witness_oracle` may read privileged scorer-side q/truth and remain
separate `PRIVILEGED_BOUND` rows. No control maximum, subtraction, adjusted
residual, or latent-reasoning quantity is computed.

For the model and every comparable control, report the same per-slot rows and
aggregates under identical denominators: legal proposal/PASS/rejection; each of
four closure booleans; any closure over sixteen slots; number of unique semantic
closures (content-addressed endpoint/relation/connector/polarity identity);
first closure logical round or `NONE`; duplicate proposal count; rejection
count; legal-proposal opportunity count; and closure per legal proposal. Raw
model-control differences may be shown only beside the two exact common units
and are not called compiler-adjusted reasoning.

The frozen ASCII allowlist maps each verbatim relation to one label or `null`;
duplicate keys, arrays, fallback, case folding, stripping, regex, or one-to-many
mapping rejects. It is imported only after phase A. For every raw model/control
proposal, phase B reports four independent booleans, always against `q_own`:

1. `verbatim_exact_closure`: exact own endpoints/connector/direction/polarity
   and verbatim relation bytes `causal_join`;
2. `witness_bound_structural_closure`: metric 1 plus cited route/effect public
   witnesses with the exact shared connector and own binding;
3. `allowlist_normalized_closure`: exact own structural fields and allowlist
   label `causal_join` without witness requirement;
4. `witness_bound_normalized_closure`: metric 3 plus metric-2 witness binding.

Report unmatched strings, normalization-only proposal IDs/counts
`metric3 AND NOT metric1`, witness-normalization-only IDs/counts
`metric4 AND NOT metric2`, near misses, citations, and all common aggregates.
Raw proposal bytes remain provisional and unchanged forever. The scorer has no
provider and no retry, memory, schedule, repair, run, or promotion edge.

## Phase B final scored graph and done

An independent phase-B verifier takes the immutable phase-A seal plus expected
score/control/summary schemas. It verifies four score rows per proposal,
comparable per-slot controls and metrics, ablations, privileged bounds,
normalization gains, `3*D` scorer packets, six life rows, three pair rows,
exploratory-ceiling rows, actual compute, sanitized trajectories, review/lock/
ratification bindings, and all referential edges. It rejects omissions,
duplicates, rewrites, reorders, or orphans even when hashes are self-consistent.
Only phase-B success may atomically create `done.json`; otherwise exactly one
`failed.json` appears. `done.json` never unlocks another scientific action.

## Claim and report boundary

Report all six lives, D, every undefined reason, sunk call, measured-balance
row, view/order/alias/shared-C shortcut survivor, model/control/privileged-bound
metric, normalization gain, exploratory ceiling, actual compute, null, and
failure. Own-minus-no-feedback is descriptive within each defined life.
Own-minus-distractor is a coordinate-specific allocation description, always
for the own target, and EXACT/NEAR/OUT measured-balance rows remain separate.
There is no automatic pool, confidence interval, p-value, threshold, or go.

The strongest permitted claim is cautious:

> In this exact six-life interface calibration, D predeclared development lives
> had a defined post-prefix branch. Within those named lives and frozen common
> random numbers, own-query allocation produced the reported provisional
> own-target closure differences from target-blind no feedback and fixed
> distractor selection, alongside comparable visible-input controls and
> separately reported offline-normalization contribution.

This is no population inference. It supports no reliability, robustness,
general recurrence, memory, learning, discovery, final behavior, efficiency,
architecture superiority, scaling, transport, replication, publication, or
next-experiment claim.

## Closure, reviews, authority, durability, and stop

All implementation entrypoints, static/dynamic dependencies, resources,
prompts, schemas, tokenizer/model manifests, selectors, measured-balance code,
tests, two-phase verifiers, workflow, architecture bytes, GPU scripts, and
review materials enter a transitive full lock. The fresh independent reviewer
and author-side scientific advocate receive identical inspectable lock/
closure/resource/evidence bytes. The frozen
resource set includes the current repaired `architecture_intake.py`, its
`test_architecture_intake.py`, and the concrete v2d zero-science envelope.
Mutable
`intake.state.json` is not an interpretation context file and is not in the
identical reviewer evidence bundle. The supervisor still validates the final
authorized intake and exact four sorted v2d scopes at workflow initialization
and again immediately before sync; the canonical proposal forces the human
ratification's authorized and forbidden lists to match exactly. An immutable
ratification binding hash is in the lock and review evidence, but mutable
authority state is validated separately and never becomes reviewer context.

The remote job uses idempotent start/status, atomic `started.json`, monotonic
schedule-indexed `progress.json`, heartbeat, phase barriers, and exactly one
terminal marker. A 12-hour watchdog may observe or restart infrastructure
polling only. It cannot regenerate seeds/order/aliases/views/calls, change
science, infer success, skip calls, or rerun a failed experiment.

Every static/zero-science/post-prefix integrity failure, `PRIMARY_UNDEFINED`
configuration, null, all-OUT balance, control win, normalization-only win,
phase-A/B failure, timeout, model failure, or valid result stops at Rohin.
Repair, rerun, replication, LoRA, heldout access, claim promotion, external
action, spend change, or a second run requires a new exact intake and human
ratification. This draft creates no intake.
