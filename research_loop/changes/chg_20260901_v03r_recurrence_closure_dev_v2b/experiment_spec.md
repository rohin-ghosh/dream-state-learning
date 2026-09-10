# v0.3-R standalone recurrence-closure development transition v2b

Date: 2026-09-01 PT. Status: **standalone proposal only; unratified**.
Change ID: `chg_20260901_v03r_recurrence_closure_dev_v2b`.

Rohin's latest directive is quoted verbatim:

> keep it goign nd get it done on the gpu once youve finsiehd the deisgn

That directive asks for persistence through design and, only after every gate
below, one bounded GPU run. It does not waive architecture deliberation,
independent review, exact human ratification, or the unconditional stop.

This document is complete in itself. No v2 or v2a prose, workflow, test, or
implicit default is normative. Those artifacts are review evidence only.

## One question and absolute exclusions

The experiment asks one development question: after one physically shared
recurrent lifetime and one bounded `THINK_0`, does the thinker's trusted,
selector-only allocation of later bounded public evidence change whether the
same live model writes a predeclared local connection?

There is no final question, final task, final thinker, answer, `RELEASE`,
answer valve, paired-answer score, LoRA training or mount, parametric
transport, online truth check, online admission, online support status,
online normalization, automatic go decision, or automatic next experiment.

## Population, hardware, model, and calls

- Generator: the exact implementation of `CounterfactualConfluenceV03R`
  frozen in the full-closure lock.
- Population: aligned skin only; development seeds 0, 1, and 2; both collision
  twins per seed; exactly six logical lives. Heldout data, other skins,
  replication seeds, and target replacement remain unopened.
- Hardware: exactly one `NVIDIA H100 NVL` GPU. Preflight requires
  `total_memory_mib >= 95000`, records the actual total (the known device
  reports 95,830 MiB), and records device name, UUID, CUDA/driver/runtime,
  bf16 capability, package lock, and model-file hashes. A different device,
  lower memory, or multi-GPU execution fails before a provider call.
- DREAM and THINK model: `Qwen/Qwen2.5-32B-Instruct`, exact revision
  `5ede1c97bbab6ce5cda5812749b4c0bdf79b18dd`, exact tokenizer at that same
  revision, clean bf16 base weights, no adapter.
- One immutable base-weight engine may remain GPU-resident across calls; model
  reload is not required. Every operation nevertheless has a unique session ID
  and receipt and starts with empty conversation, KV, prefix-cache, request,
  adapter, sampling, tool, and workspace state. Prefix caching and request
  truncation are explicitly disabled. Request bytes, config bytes, response
  bytes, receipt bytes, reset evidence, tokenizer IDs, timestamps, parser
  outcome, physical slot, and arm attribution are immutable. No call-derived
  state, cache entry, index, session object, or hidden memory may cross calls or
  lives.
- DREAM decoding is temperature `0.2`, top-p `0.95`, and
  `max_new_tokens=256`. THINK decoding is temperature `0`, top-p `1`, and
  `max_new_tokens=128`. Seeds are SHA-256 digests of the frozen run, life,
  stage, round, and physical call slot.
- Invalid, noncanonical, truncated, over-budget, or schema-invalid output
  consumes the scheduled slot and appends one rejection artifact. It is never
  truncated by the harness, repaired, retried, silently normalized, or shown a
  truth result.

## Exact public objects and candidate universe

All precommit algorithms operate on frozen structured public packets and the
frozen `MEMORY_0`; they never inspect outcomes, model responses, the final
task, or private truth.

For a life and a frozen frontier coordinate
`q=(source_endpoint, "causal_join", target_endpoint)`, define:

1. `PUBLIC(q)` as every public episode in increasing
   `(sequence_index, public_id)` order. Duplicate indices or IDs are an
   integrity failure.
2. `MEMORY(q)` as every immutable provisional `MEMORY_0` concept or edge in
   increasing `(creation_slot, semantic_sha256)` order. Mutable, malformed,
   or duplicate rows are an integrity failure.
3. The exact witness-kind enum is
   `SOURCE_ENDPOINT_MEMORY`, `TARGET_ENDPOINT_MEMORY`,
   `ROUTE_PUBLIC_RECORD`, and `EFFECT_PUBLIC_RECORD`. A source endpoint memory
   row binds the exact typed source endpoint. A target endpoint memory row
   binds the exact typed target endpoint. A route record has kind
   `valve_route` and exact structured `source_id`. An effect record has kind
   `intervention_effect` and exact structured `target_id`. Text-only matches
   do not create witnesses.
4. One selector candidate exists for every public trigger. Its neighbor list
   is the first six `MEMORY(q)` rows under the neighbor key below; fewer than
   six is legal and recorded. Therefore the candidate universe is complete,
   finite, and has exactly `len(PUBLIC(q))` candidates; no top-k pruning occurs
   before the full rank is recorded.

For memory row `m` and trigger `r`, the descending neighbor relevance tuple is:

```text
(
  exact_q_endpoint_hits(m),
  exact_typed_endpoint_hits_shared_by(m,r),
  exact_public_citation_hashes_shared_by(m,r),
  tokenizer_id_set_jaccard(q_bytes, canonical_memory_bytes(m))
)
```

Ties use ascending `(creation_slot, semantic_sha256)`. Booleans are integers
`0/1`; counts are base-10 integers; Jaccard is retained as an exact reduced
rational pair and compared by integer cross multiplication.

A candidate's descending full-selector key is:

```text
(
  has_witness_bound_structural_opportunity,
  number_of_distinct_required_witness_kinds_visible,
  exact_q_endpoint_hits_in_view,
  tokenizer_id_set_jaccard(q_bytes, canonical_view_bytes),
  -trigger_sequence_index
)
```

The final tie key is ascending `SHA256(canonical_view_bytes)`. The entire
ranked universe, every component, and every tie disposition are frozen before
selection. The selector chooses the first sixteen distinct candidates, or all
candidates if fewer than sixteen; a six-life preflight requires exactly
sixteen selected candidates for both own and distractor or classifies the
legitimate shortage `OUT_OF_STRATUM`. The originally precommitted target still
runs; no replacement or resampling occurs.

`q_bytes` is the exact ASCII sequence
`source_endpoint + "\ncausal_join\n" + target_endpoint`, without a trailing
newline. `canonical_memory_bytes` and `canonical_view_bytes` use the serializer
defined below. Tokenization uses the pinned tokenizer with
`add_special_tokens=False`. Convert each token-ID sequence to a mathematical
set. Set-Jaccard is `|A intersect B| / |A union B|`; if both sets are empty it
is exactly `1`, and if only one is empty it is `0`.

## Exact exchangeability metrics and states

Own and precommitted matched-distractor coordinates are evaluated independently
before any provider call. The manifest contains the raw values, exact rational
numerators/denominators, differences, decision, module hash, and input hashes.

- Candidate-set size: size of the complete universe.
- Witness counts: four separate integer counts, one per exact witness kind.
- Initial availability: four booleans, one per witness kind.
- Selected view count: number selected by the frozen selector.
- Mechanical closure opportunity: true iff at least one selected view contains
  source and target endpoint rows plus route and effect public records whose
  external canonical connector is identical and whose direction and effect
  polarity bind `q`.
- Source endpoint frequency: number of complete-universe views containing the
  exact typed source endpoint. Target endpoint frequency is defined analogously.
  The endpoint difference is the maximum of the own/distractor source and
  target absolute differences.
- Provider position: render the sixteen selected views in slot order. Within
  each prompt, the trigger is item 1 and memory neighbors follow in frozen
  neighbor order as items 2 through 7. The global one-based position is
  `7 * slot_index + item_position`, where `slot_index` is zero-based. Route
  position and effect position are the minimum global positions containing
  the exact required structured witness. Absence is the explicit `MISSING`
  enum, never a number. The position difference is the maximum of the two
  own/distractor absolute differences.
- Full-selector required-item rank: for each of the four witness kinds, take
  the one-based rank of the first complete-universe candidate containing that
  exact witness. Absence is `MISSING`. The rank difference is the maximum
  absolute own/distractor difference across all four kinds.
- Lexical overlap: set-Jaccard between `q_bytes` token IDs and the token-ID set
  of the exact concatenation of all sixteen canonical selected-view bytes,
  separated by one ASCII line feed. The lexical difference is the absolute
  difference of the two exact rationals.

Exact equality is required for candidate-set size, all four witness counts,
all four availability booleans, selected view count, and mechanical closure
opportunity. Numeric tolerances are endpoint difference `<=1`, provider
position difference `<=1`, full-selector rank difference `<=1`, and lexical
difference `<=1/10`.

Precommit produces exactly one of four states:

- `EXACT`: every equality passes and all four numeric differences equal zero.
- `NEAR`: every equality passes, every tolerance passes, and at least one
  numeric difference is nonzero.
- `OUT_OF_STRATUM`: a legitimate public or MEMORY_0 absence produces
  `MISSING`, or a complete finite computation fails an equality/tolerance.
  The precommitted life and target still run and are fully reported; its
  distractor delta is secondary.
- `INTEGRITY_FAILURE`: malformed/duplicate inputs, unavailable or mismatched
  tokenizer/model bytes, nondeterministic enumeration, arithmetic overflow,
  NaN/infinity, exception, hash mismatch, or inability to recompute a metric.
  The whole job stops before every provider call. This state is never recast as
  `OUT_OF_STRATUM`.

Own-minus-distractor is primary only as separate descriptive rows for `EXACT`
and `NEAR`. `OUT_OF_STRATUM` is never pooled into eligibility. If either
eligible stratum is empty, its row says `NO_ELIGIBLE_LIVES`; if both are empty,
there is no primary distractor estimand. There is no combined automatic go
row, significance test, confidence interval, threshold, favorable-direction
gate, target adaptation, or post-outcome reclassification.

## Exact aliases and connector redaction

Every DREAM call has disjoint local namespaces: public experiences `E0...`,
memory rows `M0...`, endpoints `X0...`, connectors `C0...`, and new object
`N0` only. Each alias namespace is a bijection over objects visible in that
call and resolves only through an immutable external ledger.

For namespace `T`, compute each object's canonical SHA-256 `h`. Compute the
call-local ordering key
`SHA256("v2b-alias\0" || T || "\0" || view_sha256 || "\0" ||
stage || "\0" || round_index || "\0" || call_index || "\0" || h)` and sort
ascending by `(ordering_key,h)`. Assign `T0,T1,...`. The derivation excludes
arm, target, query, own/distractor identity, semantic rank, and source order;
identical canonical views at the same logical call position receive identical
aliases across arms. Different occurrences of the same canonical connector
share exactly one `C*`; distinct connectors cannot share an alias. C ledger
entries bind to `SHA256("connector\0" || canonical_connector_ascii_bytes)`.

Rendering is structural, never a post-hoc regex. The trusted renderer replaces
every connector-bearing typed value, including `connector_id`, `valve_id`,
route/effect fields, structured memory provenance, and text derived from those
fields, with its `C*` before text is generated. Provider-visible text is
generated only from the redacted structure. It is forbidden to copy any raw
connector value, connector hash, alias ledger, global semantic hash, life/arm/
query/stratum ID, frontier tuple, ranking component, target registry value, or
the fixed test sentinel `V2B_RAW_CONNECTOR_SENTINEL_7Q9X` into request, config,
parser input, provider receipt extensions, memory text, or trajectory bytes.
Preflight scans exact bytes for the entire canonical raw-ID set and the
sentinel. Any hit stops before provider execution. Unknown, duplicate,
cross-call, non-bijective, or type-wrong aliases reject without repair.

Equal `C*` handles intentionally expose connector equality in the selected
public evidence. That is treatment-mediated public structure, not independent
discovery; deterministic shared-C controls below quantify it.

## Exact ASCII JSON and provider contracts

All model outputs are bare ASCII JSON. Free-text values (`concept_type`,
`relation_label`, `canonical_text`, and THINK descriptions/claims) contain
only ASCII bytes `0x20..0x7e` except quote `0x22` and backslash `0x5c`.
Controls, DEL, tabs, carriage returns, line feeds, non-ASCII, quotes, and
backslashes in free text reject. `canonical_text` is 1..192 bytes;
`concept_type` and nonempty `relation_label` are 1..64 bytes. No Unicode
normalization is needed because non-ASCII is illegal.

The canonical serializer is UTF-8 (therefore ASCII), `ensure_ascii=true`, no
byte-order mark, no leading/trailing whitespace, separators exactly `,` and
`:`, schema-declared field order, arrays in declared order, JSON literals
`null`, `true`, and `false`, and no terminal newline. Object keys are unique;
the parser requires exact keys and requires the raw response bytes to equal the
canonical reserialization. Citation arrays contain 1..7 distinct visible
`E*`/`M*` aliases in prompt-item order.

The only DREAM shapes and exact schema field orders are:

```text
PASS(op,reason_code="NO_BOUNDED_UPDATE")
CREATE_CONCEPT(op,new_alias="N0",entity_alias,concept_type,canonical_text,citations)
CREATE_EDGE(op,left_alias,relation_label,right_alias,connector_alias,polarity,canonical_text,citations)
REINFORCE(op,memory_alias,canonical_text,citations)
SUPERSEDE(op,memory_alias,replacement_kind,left_or_entity_alias,relation_label,right_alias,connector_alias,polarity,canonical_text,citations)
```

`entity_alias` is one visible `X*`; left/right aliases are visible `X*` or
`M*`; `memory_alias` is visible `M*`; `connector_alias` is visible `C*` or
`null`; `polarity` is `POSITIVE`, `NEGATIVE`, or `UNKNOWN`; and
`replacement_kind` is `CONCEPT` or `EDGE`. For a concept replacement,
`relation_label` is the empty string and `right_alias` and `connector_alias`
are `null`; otherwise relation is nonempty and `right_alias` is non-null. No
other null or empty field is legal. No extra field is accepted. All non-PASS
writes are harness-addressed, append-only, and `provisional`;
reinforce/supersede append events and never mutate prior rows.

An output is legal only if its raw canonical bytes tokenize to at most 256 IDs
under the pinned tokenizer with `add_special_tokens=false`. The renderer and
parser both compute and ledger that count. The schema never promises that all
192-byte texts fit: the 192-byte cap and the hard whole-operation 256-token cap
both apply. Preflight exercises every operation shape at every maximum array
cardinality, each field boundary, every printable allowed ASCII byte, and
operation-specific adversarial high-fragmentation strings. A 193-byte field,
257th token, noncanonical whitespace/order, truncation, or repair rejects. The
provider's `max_new_tokens=256` may yield an incomplete response; that consumes
one slot as rejection and is never silently truncated by the harness.

`THINK_0` runs once per life for at most twelve fresh operations after
`MEMORY_0`. It sees only the public non-answer operational probe, provisional
memory, and the frozen typed schema. Its exact operation field orders are:

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

Every named scalar is an ASCII JSON string except nullable
`parent_subgoal_id`, `object_entity_id`, and `promote_hypothesis_id`; each
`*_ids` field is an array of distinct visible typed handles. Enum values and
handle regexes are exact frozen schema bytes, no operation invents a checkpoint
handle, and no extra key is legal. `THINK_0` must terminate with one
`REQUEST_DREAM` for one mechanically projected confusion or `DEFER`; failure
also terminates. There is no `RELEASE`, final question, or final thinker.
Scratch text, predictions, rationale, citations, and confidence cannot enter
the selector frontier.

## Selector-only treatment and recurrent schedule

The full frontier, query key, source goal, vocabulary hash, life, arm,
own/distractor identity, rank components, target tuple, stratum, and closure
label are trusted-selector inputs only and are absent from provider-visible
or cognition-time bytes. Provider requests contain the generic schema plus one
selected public trigger, up to six `MEMORY_0` neighbors, and local aliases.

The exact arms are `no_feedback` (frozen target-blind intrinsic schedule),
`own_selector` (own projected frontier), and `matched_distractor` (one distinct
precommitted recipient-local same-kind coordinate). The shared prefix and
`THINK_0` execute physically once per life and are cloned byte-identically
before selection. A frontier is never evidence, a memory row, an endpoint, a
citation, or a premise.

- Each seed-0/2 life: 46 WAKE + 22 REACTIVATE + 16 target-blind SLEEP +
  16 RETURN_SLEEP in each arm = 132 DREAM calls.
- Each seed-1 life: 49 WAKE + 24 REACTIVATE + 16 target-blind SLEEP +
  16 RETURN_SLEEP in each arm = 137 DREAM calls.
- Four seed-0/2 lives and two seed-1 lives total exactly 802 physical recurrent
  DREAM calls: 514 physically shared prefix calls and 288 post-branch calls.
- Exactly 288 selector traces exist. Each arm freezes one `MEMORY_1` per life,
  giving exactly eighteen branch packets and eighteen `MEMORY_1` checkpoints.
- `THINK_0` is at most 12 calls/life and at most 72 physical calls total. The
  observed count must equal the exact scheduled prefix through the first
  terminal/error; each omitted suffix has one terminal proof. There is no
  synthetic padding.

Every scheduled provider slot has exactly one response/receipt/parser outcome,
alias ledger, and PASS/rejection/proposal linkage. Shared physical calls have
one receipt and three arm attributions, never three physical receipts.

## Exploratory ceilings and deterministic controls

There are exactly 102 additional DREAM calls, all with the same ASCII schema,
256-token hard ceiling, 192-byte canonical-text ceiling, model, revision, and
fresh-session boundary:

- six full-context one-shot calls, one per life, input ceiling 8192 tokens;
- ninety-six iterative episodic-RAG calls, sixteen per life, input ceiling
  2048 tokens, one trigger plus top-six neighbors under one frozen retriever.

Full-context and RAG differ in calls, context, retrieval, state, and
opportunity. They are labeled `EXPLORATORY_CEILING`, never matched baselines.
They cannot support recurrence, memory, efficiency, compute-fairness, or
architecture-superiority claims. Wake-only, `MEMORY_0`, and no-feedback
checkpoints use shared-call attribution and add no physical calls.

The following frozen deterministic zero-provider-call controls run only in the
isolated postcommit analysis process, once per life and arm, on exact selected
view bytes. Their algorithms, output order, and tie keys are lock-bound:

1. `selected_view_byte_constructor`: emit the first schema-valid endpoint edge
   mechanically recoverable from typed visible fields.
2. `shared_c_join_compiler`: join the first route/effect witnesses sharing one
   `C*`, with ascending `(slot,position,C*)` ties.
3. `canonical_string_compiler`: emit only when exact literal `causal_join` is
   present in visible bytes.
4. `query_copy_ceiling`: scorer-side construction from the precommitted tuple,
   explicitly labeled unavailable to cognition.
5. `masked_content_control`: replace every allowed free-text byte with `#`
   while preserving schemas, aliases, and order.
6. `wrong_connector_control`: rotate distinct `C*` labels by one in ascending
   alias order; one-connector views yield no output.
7. `citation_permutation_control`: reverse citations while preserving content.
8. `deterministic_retrieval_only`: report opportunity/rank without proposing.
9. `public_witness_oracle`: postcommit opportunity ceiling from public truth.

All controls are scored with the same four metrics below and appear before
model rows in analysis. Per life/arm/metric, the signed model-associated
residual is `model_count - max(deterministic_control_count)`; it is descriptive,
not clipped, pooled, thresholded, or called proof of latent reasoning. Exact
rendered-text/order/ID/alias/shared-C/endpoint/scorer-coordinate/joined-feature
audits run on 1000 collision pairs and report every surviving predictor.

## Irreversible MEMORY_1 barrier and four closure metrics

All 802 recurrent calls, all 102 exploratory calls, eighteen `MEMORY_1`
checkpoints, raw proposals/PASS/rejections, aliases, selector traces, and their
independent completeness graph must freeze and verify before the scoring
process may import the target registry, public witness oracle, relation
allowlist, or any score code. Scorer imports are forbidden in runner, renderer,
parser, selector, memory, provider, and trajectory modules. The scorer has no
provider and no edge to memory, retry, repair, scheduling, another run, or
status promotion.

The relation allowlist is a frozen ASCII JSON object from exact verbatim input
strings to either one ASCII scorer label or `null`. Duplicate keys, arrays,
case folding, whitespace stripping, regexes, fallback, and one-to-many mappings
reject. Unlisted and `null` strings are `UNMATCHED`. Raw proposal bytes never
change.

For each proposal, with endpoints, connector, direction, polarity, and
citations resolved only through frozen external ledgers, report four independent
booleans:

1. `verbatim_exact_closure`: exact target endpoints/connector/direction/
   polarity and verbatim relation bytes exactly equal ASCII `causal_join`.
2. `witness_bound_structural_closure`: metric 1 plus cited public route and
   effect records sharing the exact connector and binding the target source,
   target, direction, and effect polarity.
3. `allowlist_normalized_closure`: exact target endpoints/connector/direction/
   polarity and the one allowlist label equals `causal_join`, without requiring
   witness citations.
4. `witness_bound_normalized_closure`: metric 3 plus the exact witness binding
   required by metric 2.

Also report proposal IDs and counts for normalization-only gain:
`metric3 AND NOT metric1`, and witness-bound normalization-only gain:
`metric4 AND NOT metric2`. Report unmatched strings verbatim, duplicates,
near misses, unsupported proposals, first closure slot, model-minus-control
residuals, and arm deltas. No metric rewrites a proposal or becomes a status.

## Reporting and claim boundary

Report every life, collision pair, arm, stratum, metric, control, exploratory
ceiling, null, control win, unmatched string, integrity failure, actual token/
call/read/wall-time cost, and signed delta. Own-minus-no-feedback is descriptive
for all completed lives. Own-minus-distractor is reported separately for
`EXACT`, `NEAR`, and `OUT_OF_STRATUM`; only the first two are eligible primary
descriptions, never pooled automatically. There is no automatic go criterion.

The strongest permitted sentence is:

> On these six named aligned v0.3-R development lives, own query-guided bounded
> public-view allocation changed later provisional connection proposals relative
> to no feedback and, within separately reported precommit EXACT or NEAR lives,
> a fixed matched distractor, after deterministic compiler and offline
> normalization contributions were reported separately.

This is an interface-development observation from three selected calibration
pairs. It is not statistical inference and supports no reliability,
robustness, scaling, memory, beyond-context, independent discovery, autonomous
learning, final behavior, action improvement, compute efficiency, architecture
superiority, transport, replication, paper headline, or next-experiment claim.

## Required artifact graph and transitive review closure

Completeness derives from frozen schedules and manifests, never `done.json`.
The required graph includes:

- exact directive/spec/scope/change/workflow/intake/ratification bindings;
  environment, H100/model/tokenizer/decoding manifests; global/per-life
  schedules; exchangeability and candidate-universe manifests; selector,
  exploratory-ceiling, deterministic-control, shortcut, and inventory manifests;
- six public-life packets, six schedules, six shared prefixes, six THINK_0
  replay/frontier packets, six `MEMORY_0`, eighteen branch packets, eighteen
  `MEMORY_1`, and eighteen scorer packets;
- exactly 802 recurrent and 102 exploratory call slots with complete immutable
  request/config/response/receipt/token/parser/alias/outcome linkage; exactly
  288 selector traces; zero-or-one proposal per DREAM slot; exact terminal-
  justified THINK prefix `<=72`;
- four score booleans per proposal, normalization-only IDs/counts, all nine
  deterministic control rows per life/arm, six life and three pair summaries,
  exploratory rows, actual compute, and sanitized trajectories with forbidden
  fields absent;
- one `started.json`, monotonic atomic `progress.json` and heartbeat, and exactly
  one terminal `done.json` or `failed.json`. `done.json` appears only after an
  independent verifier accepts the complete graph.

The workflow declares every frozen implementation, test, prompt, schema,
architecture, workflow, GPU script, and resource in `freeze_inputs`. Before
lock creation, `freeze_closure` must prove the complete repository-local static
Python import closure. V2b preflight additionally rejects unresolved dynamic
imports/resources and emits a resource-edge manifest. A reviewed evidence
bundle contains exact inspectable bytes, path, SHA-256, length, and encoding for
every locked text input; binary model/environment artifacts use hashes and
provider receipts. Both independent reviewers receive the identical lock,
closure/resource manifests, evidence bundle, architecture bytes, and tests.
Each review binding includes all of their hashes; either rejection/escalation,
missing byte, or post-review mutation stops before GPU sync.

The verifier independently rejects missing, duplicate, reordered, rewritten,
unreferenced, or orphaned calls, aliases, views, proposals, checkpoints,
scores, controls, exploratory rows, reviews, markers, or trajectories even if
producer hashes are internally consistent.

## Workflow, durability, authority, and stop

The proposal intentionally names missing future v2b implementation files.
Until fresh v2b interpretations, critique, consensus, exact Rohin ratification,
scoped implementation, all individually declared CPU/preflight tests,
transitive freeze, identical fresh Fable and Sol approvals, and exact scope
verification complete, the workflow fails closed before sync or a provider
call. No intake is initialized by this package draft.

The H100 job uses idempotent start/status commands, atomic markers, monotonic
schedule counters, heartbeat, and verified phase barriers. A 12-hour watchdog
may observe or restart an infrastructure poll; it cannot change bytes, skip a
call, infer completion, rerun failed science, or launch another experiment.

Every valid result, null, all-OUT result, control win, normalization-only win,
review failure, integrity failure, artifact failure, timeout, or model failure
stops unconditionally at Rohin after artifact pull and verification. Repair,
rerun, replication, LoRA, heldout access, external action, claim promotion,
lease/spend change, and a second GPU run require a new exact intake and human
ratification.
