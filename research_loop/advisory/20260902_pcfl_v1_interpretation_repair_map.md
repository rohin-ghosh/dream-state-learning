# PCFL-Compose v1 interpretation repair map

**Status:** advisory only.  This document neither ratifies nor edits v1, and
does not authorize implementation, model calls, GPU work, LoRA, or a lifetime
study.

## Sources and recommendation

This reconciliation uses the canonical v1 proposal with SHA-256
`b6464058e7a2b522fb8b7f13835cd8f4c961f8b946f6019d562dbf9bca22e37e`, the
benchmark interpretation `chg_20260902_pcfl_compose_self_revision_text_dev_v1.benchmark`,
and the systems interpretation
`chg_20260902_pcfl_compose_self_revision_text_dev_v1.systems`.  It is a repair
plan for a new, fully re-bound v2 change; v1 remains untouched.

The recommended v2 preserves one narrow causal assay:

```text
shared public tree + one immutable Dream-1
  -> randomized/certified h continuation changes raw public A only
  -> fresh, seed-coupled Dream-2 produces B commitments and one corpus
  -> target-time whole-corpus intervention changes physical target actions.
```

It does not add a parameter update, LoRA, a second life, cross-life memory,
compression, a learned scheduler, adaptive evidence collection, or any
lifetime/scaling claim.  The required changes divide into (1) blocking protocol
repairs needed for a valid causal DEV result and (2) claim-boundary repairs that
must accompany any v2 report.  A claim-boundary repair is still binding text;
it is simply not a reason to enlarge the roster.

| Disposition | Meaning |
|---|---|
| **Blocking** | Must be frozen and independently reviewed before v2 can be ratified or executed. A failure returns `HUMAN_REQUIRED`/`NOT_RUN`, not a prompt or seed repair. |
| **Claim boundary** | Does not add a treatment. It removes an inference that the retained data cannot identify. |

## Reconciled issue-by-issue map

| Interpretation issue(s) | Disposition | Exact v2 repair | v2 files and acceptance tests affected |
|---|---|---|---|
| `BENCHMARK_A01_OPAQUE_PACKET_BOUNDARY`; `BENCHMARK_D01_OPAQUE_NO_SOLUTION_PACKET` | **Blocking** for T11 as written; retain opaque lane only with a narrower interface assertion. | Delete every opaque-lane assertion that an audit can prove “no completed target/path/table/plan,” “no hidden closure,” or an itemwise semantic minimum. An opaque `READ` may be certified only to return `NOTE | NOT_FOUND`, preserve the selected canonical envelope byte-for-byte, use the frozen target-blind lexical ranking, and have a bounded response. No target-aware, model, or human semantic inspection of an opaque note or response is permitted. Keep no-solution-packet/minimum-read certification exclusively for `OPERATOR_AST`, oracle, and class-informed structured packets, where the closed grammar makes the property decidable. In the generic Dream prompts, retain “do not emit a table/plan” only as an instruction and append: “This instruction is not semantically audited and supplies no no-solution-packet guarantee.” | Amend `experiment_spec.md` §§4, 6, 8; `semantic_contract.md` (exact query/read section); `visibility_contract.md`; `prompts/generic_dream1.txt`, `generic_dream2.txt`; and `change.json`. Split **T11** into `T11A` opaque surface/interface conservation and `T11B` structured no-solution/minimum witnesses; retain its single ID in the v2 acceptance list if IDs must remain stable. Also revise **T09** wording that cross-refers to an opaque packet audit. No model-call arithmetic changes. |
| `BENCHMARK_D02_OPAQUE_FALSE_SYMMETRY`; `AMB_SYS_06_OFFLINE_OPAQUE_SCORING_WORDING` | **Blocking** for T09 and scorer ownership. | Make semantic true/false shape symmetry an AST-only test. Rename the opaque half `content-blind footprint symmetry`: a presealed, target-manifest-independent arbitrary NOTE corpus with the same permitted envelope count, IDs, references, byte-length bucket, and index shape must have the same admission/index mechanics as its paired corpus. It is not called false. For opaque artifacts the offline scorer may inspect hashes, provenance, parses, predictions, actions, intervention identity, and terminal outcomes; it must not inspect or label note semantics, truth, corruption, explanation, or target solution content. Whole-corpus opposite-life/wrong-life/sham action experiments remain behavioral counterfactuals, not note-truth tests. | Amend `experiment_spec.md` §§4, 8; `semantic_contract.md` (Sleep and terminal-scoring boundary); `visibility_contract.md`; and `change.json`. Update **T09** and **T08**. No resource change. |
| `BENCHMARK_A02_COUNTERFACTUAL_SEED_MAP`; `BENCHMARK_D03_ARM_RANDOMNESS_IDENTIFIABILITY` | **Blocking** for causal counterfactual language. | Add a canonical, content-addressed `rng_contract.json` and one row per invocation. Required row fields: `root_id`, `family`, `z_side`, `h_or_q`, `lane`, `phase`, `condition_id`, `memory_variant_or_cut`, `target_id`, `goal_twin`, `resolver_step_or_invocation`, `coupling_group`, `seed_derivation_version`, `seed_digest`, and `scientific_or_diagnostic`. Derive each seed from a domain-separated hash of the fixed fields *and* `coupling_group`; never derive it from outputs. The manifest, rather than the arm name, determines coupling. Dream-1 runs once and is cloned across h/q. The two fresh Dream-2 continuation calls share a coupling group/seed at matched step ordinal. Each target-time authentic/EMPTY/wrong-life/antipode/sham comparison shares a coupling group at the same target, goal, and step ordinal; an explicitly independent draw gets a distinct declared group. Renderer, reader, actor, cache, and error RNGs are deterministic and separately namespaced. A backend that cannot honor this per-invocation policy blocks the causal contrast rather than silently turning it into sampling noise. | Add `rng_contract.json`; amend `visibility_contract.md`, `experiment_spec.md` §§2–3 and 8, `resource_manifest.md`, and `change.json`. Update **T02**, **T06**, **T10**, **T14**, **T15**, **T16**. Call count is unchanged, but the T16 ledger must include the manifest and at most two infrastructure replays separately. |
| `AMB_SYS_01_PUBLIC_EVENT_CATALOG_CONTENT` | **Blocking** oracle-firewall repair. | Freeze a typed handle-catalog contract. Before a charged `READ`, Dream-1 and Dream-2 catalogs may expose only fixed `handle_id`, `handle_kind`, `phase`, `ordinal`, and `readable`; none may expose payload bytes, payload hash, byte count, dynamic timing, error class, outcome-derived shape, comparator value, or target-derived metadata. In particular, A after-tray bytes, their hash, their size, and any derived statistic are available only in the charged reader result. Candidate catalog entries likewise use opaque IDs and fixed ordinal, not candidate hash/size. A read receipt may then contain `handle_id`, canonical payload bytes, payload digest, and byte count. These fields must be logged but never be pre-READ catalog fields. | Add a small `event_catalog.schema.json` (or equivalent definitions in `semantic_dsl.schema.json`); amend `semantic_contract.md`, `visibility_contract.md`, the four Dream prompt renderers as applicable, and `change.json`. Update **T05**, **T06**, **T07**, **T08**, **T14**. No model-call change. |
| `BENCHMARK_A03_MUTATION_FIELD_REGISTRY` | **Blocking** comparator-mutation repair. | Add `private_field_registry.json` with each field’s owner, phase, consumers, taint class, mutation class, and permitted digest exposure. Separate: (a) sealed public-life transition bytes required for actor trays and therefore never changed by an offline-comparator test; (b) target manifests, closure certificates, scorer truth labels, comparator ranks/match bits, and analysis fields which are mutable after the appropriate freeze; and (c) target-render input, which may be mutated only in the dedicated target-manifest firewall test. Replace “every private/offline truth and comparison field” with two receipts: **offline comparator mutation** leaves Dream-2/corpus/index/action bytes identical, and **target-manifest mutation** leaves all pre-target Dream/Sleep/index bytes identical while target rendering is handled as a separate downstream test. | Add `private_field_registry.json`; amend `visibility_contract.md`, `experiment_spec.md` §§3, 8, `resource_manifest.md` artifacts, and `change.json`. Update **T05**, **T08**, **T14**, **T16**. No roster change. |
| `AMB_SYS_02_S1_METRIC_AGGREGATION`; `AMB_SYS_03_INDEPENDENT_Q_CONTROL_MATCHING` | **Blocking** identifiability/endpoint repair. | Add `analysis_contract.md` with a failure-inclusive long-form row keyed by `(root, family, z_side, h_or_q, lane, condition, corpus_variant, target_kind, target_id, goal_twin)`. Define every endpoint as `0` on malformed, timeout, illegal, early-lock, unavailable read, or abstention. For an ordinary factor branch (b), define its D4 mean as the unweighted mean over its two sealed z sides and two goal twins; every authentic-minus-control contrast is the mean of *within-identical-(z, branch, target, goal)* differences, never a difference of differently weighted summaries. Define first-action redirection before inspection as an authentic/counterfactual pair with different first legal actions, and report it separately from exact D4 success. For the independent root, every q has its own EMPTY and OBSERVED executions on the identical `(q,z_side,target,goal)` packet. Thus each q-specific contrast averages its four `(z_side, goal_twin)` pairs; no control is reused across q, and no q branches are pooled for a positive effect. `SPECIFICITY_CONCERN` is exactly: for either q, at least three of four failure-inclusive SELF D4 rows succeed, or for both q values both q-specific SELF-minus-EMPTY and SELF-minus-OBSERVED means are strictly positive. These are deterministic alarm rules, not p-values, intervals, or population estimands. | Add `analysis_contract.md`; amend `experiment_spec.md` §§7–8, `resource_manifest.md` required artifacts, and `change.json`. Update **T04**, **T15**, **T18**, **T19** (and cross-reference **T02** for nested-orbit language). No calls change; the ledger gains rows, pairing IDs, denominators, and tie/availability codes. |
| `AMB_SYS_04_CPU_ENVELOPE` | **Blocking** completion-envelope repair. | Replace competing, non-completable Stage-0 maxima with a jointly satisfiable envelope. If all 128 roots must be certified, set the per-root CPU cap to **10.5 CPU-minutes** and retain the aggregate **24 CPU-hours**: `128 × 10.5 = 1,344 CPU-minutes = 22.4 CPU-hours`. Count all worker CPU time in the root accounting. A root reaching its cap, aggregate exhaustion, or a missing certified root stops Stage 0; partial certification cannot supply a sampled S1 root. If a preliminary non-model timing certificate cannot show this envelope, v2 is `NOT_RUN` rather than revised after inspection. Worker count affects wall time only. | Amend `resource_manifest.md` CPU section, `experiment_spec.md` §§2 and 7, `scope_proposal.json`, and `change.json`. Update **T01**, **T02**, **T04**, **T16**. This changes CPU arithmetic only, not GPU/model calls. |
| `AMB_SYS_05_EXACT_PROGRAM_CALL_ACCOUNTING` | **Blocking** resource-ledger repair. | Declare `EXACT_PROGRAM`/`EXACT_ABSTAIN` as non-LLM direct evaluators: zero recurrent-Think forward passes and zero one-shot forward passes. Remove their three ordinary z+antipode slots from the recurrent-Think sum: `7,216 - 3×164 = 6,724` model Think calls. Preserve a distinct exact-program CPU/action ledger: 24 direct target solves (three exact rows × two z sides × two D1 plus two D4 goal twins), 60 physical target-action applications (two D1 one-step plus two D4 four-step twins per life), and four S1A h-branch B-prediction solver checks. These are not model calls. The model-call scientific maximum is `968 Dream + 6,724 recurrent Think + 24 structured one-shot Think + 512 conditional A-MEM = 8,228`; at most two permitted exact-byte infrastructure replays make a process maximum of **8,230**. Set a 8,300 total model-call stop, and report `7,716` if A-MEM is `NOT_RUN`. Recompute every displayed token/time estimate from this actual ledger; the old 9,000 stop is not an arithmetic maximum. | Amend `resource_manifest.md`, `experiment_spec.md` §§5–7, `scope_proposal.json`, and `change.json`. Update **T12**, **T15**, **T16**, **T18**, **T19**. This is the resource-arithmetic change above; it must not be disguised as a compute concession by the exact program. |
| `DIS_SYS_01_PRIMARY_CLAIM_TEMPORAL_CAUSATION` | **Blocking** wording/causal-graph repair. | Replace the v1 Section-1 sentence with the exact v2 DEV descriptor below. It separates (i) pre-Sleep A/B prediction commitments, (ii) raw-A’s effect on fresh Dream-2 revision in the shared-prefix h instrument, and (iii) frozen-corpus effects on later actions. Do not say that the target-time corpus caused earlier prospective predictions, or that predictions and later actions share one undifferentiated causal effect. | Amend `experiment_spec.md` §§1, 7–8, `scope_proposal.json`, and `change.json`. Update **T02**, **T05**, **T10**, **T18**, **T19**. No resource change. |
| `DIS_SYS_02_OPAQUE_THINK_ONESHOT_SCOPE` | **Claim boundary**; preserves the current roster rather than adding an unplanned opaque treatment. | Rename arm 14 **STRUCTURED_ONE_SHOT_THINK versus ITERATIVE_THINK**. It applies only to `ORACLE_SCHEMA_TEXT` and `OPERATOR_AST_SELF` cells already registered. Add `memory_representation` to `ONE_SHOT_PLAN`, constrained to `ORACLE_SCHEMA_TEXT` or `OPERATOR_AST`; assignment construction rejects `OPAQUE_NOTE`. The one-shot thinker prompt must state the same restriction. State explicitly that primary opaque SELF has no one-shot Think comparator and hence v2 makes no claim that recurrence is necessary, advantageous, or compute-fair for opaque target-time Think. The 24-call count remains exactly structured-only. | Amend `experiment_spec.md` §§1 and 5–6, `semantic_dsl.schema.json`, `prompts/one_shot_thinker.txt`, `resource_manifest.md`, and `change.json`. Update **T06**, **T07**, **T12**, **T16**. No call-count change. |
| `BENCHMARK_D04_DEV_ENDPOINT_SCOPE`; `BENCHMARK_A05_DEV_CLAIM_WORDING` | **Claim boundary**. | Rename “maximum positive primary-lane sentence” to “maximum internal DEV result descriptor.” Bind every report to the three named registered roots and frozen interface. State that sides, h/q continuations, z/antipodes, targets, twins, calls, and model samples are nested records; the 1/16 fact is a constructor theorem under a uniform z prior, not sixteen model replicates. Prohibit p-values, confidence intervals, prevalence, rankings, benchmark superiority, paper efficacy, abstracts/headlines, and any generalized causal-performance statement. S1B remains a specificity sentinel ending in `HUMAN_REQUIRED_FOR_ANY_NEXT_STAGE`; a separately designed root-level confirmation sample is necessary before a paper claim is even considered. | Amend `experiment_spec.md` §§1, 7–8; `scope_proposal.json`; `resource_manifest.md` artifacts; and `change.json`. Update **T02**, **T15**, **T18**, **T19**. No resource expansion. |
| `BENCHMARK_A04_BASELINE_CONCLUSION`; `BENCHMARK_D05_BASELINE_COMPLETENESS` | **Claim boundary** plus a blocking report rule for a missing baseline. | Keep faithful native A-MEM as optional only. If preflight fails, emit root-wide `NOT_RUN`, do not substitute another linked store, remove all A-MEM comparison cells from numerical contrasts, and state “no A-MEM comparison was performed.” RAW_RAG, EMPTY, and OBSERVED are within-interface diagnostic controls on a 15-event construct, not external-memory, persistence, compilation, or context-overflow baselines. A result may not call any available arm superior to A-MEM/external memory when A-MEM is `NOT_RUN`. | Amend `experiment_spec.md` §§5, 8; `resource_manifest.md`; `scope_proposal.json`; `change.json`; and `analysis_contract.md`. Update **T13**, **T15**, **T16**, **T18**, **T19**. A-MEM remains a conditional ≤512-call reserve; its absence reduces actual usage to 7,716 scientific model calls. |
| `BENCHMARK_D06_RECURRENCE_COMPUTE_LANGUAGE` | **Claim boundary**. | Use this exact phrase everywhere: **“eligible-information and output-capacity matched; interaction, input trajectory, call count, latency, and FLOPs intentionally unmatched and reported.”** Apply it to recurrent versus one-shot Dream. For structured one-shot Think, say the same plus “structured-only diagnostic.” Delete “compute matched,” “fair recurrence test,” and any efficiency/necessity implication. A one-shot Dream result within 0.05 only removes a recurrent-Dream advantage claim at this resource point; it does not prove equality. | Amend `experiment_spec.md` §§3, 5, 8; `resource_manifest.md`; prompt headers where they claim matching; and `change.json`. Update **T07**, **T13**, **T16**, **T18**. No new calls; T16 reports costs by arm/cell rather than treating the design as compute matched. |

## Exact replacement text for the v2 result boundary

The following replaces the frozen v1 “maximum positive primary-lane sentence”
and its first explanatory paragraph.  It is intentionally not paper copy.

> **Maximum internal DEV result descriptor.** On the three registered roots and
> frozen interface only, a resolver committed prospective A and B tray
> predictions from public events; in a CPU-certified public-prefix h fork in
> which only later raw A evidence differed, fresh Dream-2 made the registered
> branch-appropriate B commitments and selected the corresponding life corpus;
> and target-time interventions on that already-frozen whole corpus changed
> later physically executed actions on never-executed compounds. Each clause is
> reportable only when its own predeclared construct, chronology, seed-coupling,
> mutation, and failure-inclusive endpoint gate passes.

> “Self-revised from raw evidence” may be used only for the middle clause after
> both h branches satisfy the shared-prefix test. “Causally improved” is not
> used for prospective predictions; the later action effect is reported as a
> paired corpus-intervention contrast. This is descriptive root-level DEV
> evidence, not a paper result, benchmark ranking, population estimate,
> recurrence-efficiency result, semantic explanation, persistence result, or
> evidence about LoRA, lifetime learning, compression, or learned control.

## Coherent v2 contract

### 1. Opaque and structured lanes have different decidable assertions

The primary lane remains `OPAQUE_NOTE_SELF`.  Its causal object is a frozen
model-selected byte corpus read through target-blind literal lexical retrieval.
The permitted opaque assertions are byte/provenance conservation, catalog and
reader type totality, target blindness, bounded reads/responses, corpus
intervention identity, prediction commitments, and executed action endpoints.
Neither v2 nor an offline audit decides what the note “means.”

`OPERATOR_AST_SELF`, oracle schema, and class-informed arms remain separately
reported structure-assisted diagnostics.  Only their closed representation can
support semantic true/false substitutions, no-solution-packet witnesses,
itemwise read lower bounds, denotation scores, and record-level cuts.  AST
success never translates, repairs, selects, explains, or upgrades opaque SELF.

### 2. Catalog, visibility, and mutation contracts are literal

The v2 event-catalog schema makes the pre-READ interface auditable rather than
relying on prose.  It also prevents a hash, length, elapsed-time field, or
exception shape from becoming a raw-A branch label.  Read receipts reveal
content only after budget charge and must appear in the append-only ledger.

The field registry makes the comparator-mutation experiment meaningful.  The
actor’s sealed public-life transition implementation is not an “offline truth
field,” so mutation cannot accidentally create a new public environment.  By
contrast, target certificates, comparator matches, scorer labels, and analysis
artifacts are explicit offline fields and can be replaced with legal arbitrary
values after the relevant causal object freezes.  A target-manifest mutation is
a separate upstream-firewall test, with an explicitly limited invariant surface.

### 3. Seeds identify counterfactuals without claiming deterministic sampling

`rng_contract.json` is a pre-model artifact, hash-bound with the assignment
roster.  It makes the desired comparison unit explicit rather than treating
all calls that happen to share a root seed as paired.  Coupling is used only to
remove declared sampling noise from a same-step counterfactual; it does not
make h, q, corpus, or arm labels visible to a model.  All unmatched or
independent draws are named and their comparisons are descriptive.

This policy also fixes the public-prefix test: cloning Dream-1 proves shared
pre-A history; paired Dream-2 seeds make the only intended pre-invocation
difference the registered raw-A continuation and its mechanical descendants.
It does not require Dream-2 outputs to be byte-identical, because their input
evidence intentionally differs.

### 4. Analysis is paired within, never inferred across, roots

`analysis_contract.md` is the sole source for denominators, row inclusion,
weights, ties, unavailable rows, and gate expressions.  It includes the exact
long-form table and emits a paired-row receipt for every reported contrast.
No cell is discarded after an error.  The independent q control repair is
important: its q continuations may have independently coupled B/target blocks,
so each control must share that same q-specific target packet.  This makes a
positive independent result a clear specificity alarm rather than a mixture of
branch and target differences.

### 5. Resource accounting distinguishes models, programs, and CPU work

The v2 manifest reports three noninterchangeable ledgers:

| Ledger | v2 maximum | Notes |
|---|---:|---|
| Dream model calls | 968 | Unchanged. |
| Recurrent Think model calls | 6,724 | `7,216 - 492` exact-program slots. |
| Structured one-shot Think model calls | 24 | No opaque one-shot Think cell. |
| Conditional native A-MEM model calls | ≤512 | `NOT_RUN` contributes zero. |
| Scientific model-call total | 8,228 | 7,716 when A-MEM is `NOT_RUN`. |
| Process model-call total | 8,230 | Includes at most two diagnostic exact-byte replays. |
| Exact-program work | 28 direct CPU solver evaluations; 60 actor applications | Separate from all model calls. |
| Stage-0 CPU certification | ≤22.4 CPU-hours | 128 roots × 10.5 CPU-minutes/root. |

The last row is a jointly satisfiable ceiling, not a claim that a 30-minute
per-root maximum can coexist with a 24-hour global total.  The v2 hard
model-call stop is 8,300, which covers the 8,228 scientific maximum and no more
than two replay diagnostics.  Token, wall-time, and device-hour estimates must
be recomputed from actual model calls and retained as estimates; no linear
extrapolation is treated as a hard certificate.

### 6. One-shot and baseline language stays honest

The existing opaque one-shot **Dream** control is kept.  It is a comparison of
the disclosed recurrent interface bundle against a one-shot bundle with matched
eligible information and generated-output entitlement, not equal interaction
or compute.  The v2 one-shot **Think** control stays structured-only, which is
scientifically cleaner than adding an opaque full-packet intervention whose
relation to lexical target-time reading is otherwise ambiguous.  It therefore
does not identify a target-time recurrent-Think benefit for primary opaque
SELF.

A-MEM is not “lost” if unavailable: it is explicitly absent.  The v2 report
must distinguish a missing faithful comparator from a negative outcome and
must not present the tiny history as a persistence or context-limit challenge.

## Acceptance-test reconciliation checklist

All existing IDs remain present in v2, but their exact v2 text must make the
following obligations executable.

| Test | Required v2 change |
|---|---|
| T01 | 128-root Stage-0 totality and the jointly satisfiable CPU receipt. |
| T02 | Nested-orbit wording, all pre-A byte equality, and h/q seed coupling receipt. |
| T03 | No change to target uniqueness; keep it distinct from a semantic-memory claim. |
| T04 | q-specific target/control pairing and conditional-null certificate. |
| T05 | Typed pre-READ catalog field allowlist and field-registry taint receipt. |
| T06 | Runtime validation of catalog schema, RNG manifest, structured-only one-shot representation, and prompt/schema hashes. |
| T07 | Retain Dream matched-eligibility wording; label Think one-shot structured-only and interaction/compute-unmatched. |
| T08 | Separate offline-comparator and target-manifest mutation receipts. |
| T09 | AST semantic false symmetry; opaque content-blind footprint symmetry only. |
| T10 | Common Dream-1 clone, raw-A-only fork, and matched invocation coupling groups. |
| T11 | Opaque surface-interface test only; structured no-solution/minimum-read witnesses only. |
| T12 | Exact program zero-model-call ledger and direct-program abstention ceiling. |
| T13 | Faithful-only A-MEM and explicit no-comparison conclusion when `NOT_RUN`. |
| T14 | End-to-end fresh namespaces including each RNG/coupling and catalog/field-registry audit. |
| T15 | Failure-inclusive long-form rows, exact pairing keys, and unavailable/tie codes. |
| T16 | 10.5-minute/root and 24-hour CPU receipt; 6,724 Think / 8,228 scientific / 8,230 process-call arithmetic. |
| T17 | Fresh reviewer/advocate check of every new v2 byte, including new contracts and this repair’s claim boundary. |
| T18 | Use the separated prediction/revision/action descriptor and defined paired aggregates; retain open-root stop/go status only. |
| T19 | q-specific four-row pairings, deterministic specificity concern, root-level description only, then `HUMAN_REQUIRED`. |

## Required v2 file set and authority boundary

The v2 change should copy and revise, rather than mutate, at minimum:

- `experiment_spec.md`, `visibility_contract.md`, `semantic_contract.md`,
  `semantic_dsl.schema.json`, `resource_manifest.md`, `scope_proposal.json`,
  and both generic Dream prompts plus `one_shot_thinker.txt`;
- new `rng_contract.json`, `event_catalog.schema.json`,
  `private_field_registry.json`, and `analysis_contract.md`; and
- `change.json`, with a new proposal SHA and context-file hash array binding
  every carried and new artifact.

The v2 scope must continue to say: inference-only, frozen
`Qwen/Qwen2.5-32B-Instruct` revision, no fallback, no network/model/GPU action
until a separate ratification, no optimizer/weights/adapters/LoRA, no lifetime
or post-context run, no confirmation roster, no paper/public release, and no
automatic successor.  Fresh independent interpretations and a new human
ratification are required after v2 bytes are frozen.  This advisory is not that
ratification.
