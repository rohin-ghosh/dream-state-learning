# ACTIVE_TEXT_NATIVE-v2 adversarial audit: strong baseline not yet closed

**Date:** 2026-09-13 PT

**Role:** fresh adversarial scientific reviewer

**Verdict:** **REWORK; do not implement or call strong/fair as written**

**Scope:** documentation only; no source, runtime, builder, model, tokenizer,
adapter, benchmark, GPU, or remote action

## Bottom line

`ACTIVE_TEXT_NATIVE-v2` (ATN-v2) gets several important things right: it
separates the v2.2 exact-address service ceiling from an evolving opponent,
keeps a lossless branch-local ledger, distinguishes on-policy from same-history
comparisons, treats roots rather than tasks as the unit, and forbids a universal
saturation claim.

It is nevertheless not yet the strong fair opponent needed for the full
Dream--LoRA--Think claim. The current bytes combine an unqualified actor-driven
tool loop, a potentially informative identifier remapping, a graph whose
topology contradicts its “declared-link only” label, an underspecified common
raw-recall lane, a small-store certificate for a large-store lifetime, and a
new RS8 record/interface that ATN-v2 does not implement. The same-history view
also does not isolate a pure carrier effect, and the resource cap is extrapolated
from call count rather than the long prompts that dominate this system.

The smallest strong repair is a new frozen version,
`ACTIVE_TEXT_NATIVE-v2.1-AUTO`: deterministic retrieval is automatically run
from only the currently visible task/state and accepted prior THINK text, the
graph is mechanically built from public witnessed events, and the model never
has to learn a `RECALL` dialect. This makes the text baseline stronger, cheaper
to interpret, and exactly equal in actor-generation opportunities. If it wins,
that is the scientific result.

## Fatal attacks and exact dispositions

| severity | attack | why the current design fails | exact repair |
|---|---|---|---|
| **P0** | The retrieval policy is not executable evidence. | ATN-v2 requires the ordinary frozen child to author adaptive `RECALL` commands. The newest exposed-root evidence is 0/64 READ attempts in A1 and 0 accepted recurrent THINK turns in A3. A certificate failure would therefore conflate memory quality with a known tool/framing failure. Sixteen possible reads are not a strong baseline if the actor never calls one. | Retrieve automatically before actor calls 1--16. Query 1 is a frozen projection of public task/state bytes; query `k>1` adds only accepted prior THINK bytes. Retrieval consumes no generation turn. Every arm must use the same LF stop, exclude LF from returned bytes, fullmatch one typed physical turn, and append an accepted THINK verbatim before its next call. Keep 16 nonterminal opportunities, one final opportunity, and 2,048 generated tokens for every neural condition. No hidden query rewriter, solver, retry, answer address, or final-action text enters a query. |
| **P0** | Public-slot normalization can leak structure and collapse identities. | `NORM/<PUBLIC_TYPE>/<ZERO_PADDED_SLOT>` exposes type and ordinal and is ambiguous about whether slots are globally unique. If slots repeat across modules, unrelated opaque identifiers collide; even if global, ordinal/future inventory can be a side channel. The retriever should know equality, not a privileged world address. | Replace it with `OID/<128-bit SHA256(root_salt || exact_public_id)>`, where `root_salt` is sampled independently of world contents before the root, tokens are collision-checked, and no type, role, module, order, answer, or future-inventory bit appears. Mapping is created online on first public appearance. Render original public bytes back to the actor. |
| **P0** | “Declared-link graph” is false under the stated topology. | Two EVENT documents that share `first.destination == second.source` already meet at one symbol vertex. The graph therefore composes the chain without a child LINK; LINK documents are topologically redundant. A LINK cut can fail while retrieval still uses the inferred shared-symbol path. | For the **strong** opponent, embrace and rename this capability: build an `AUTO_WITNESSED_GRAPH` deterministically from every valid public action--outcome envelope. It may compose only actually observed directed edges and may never use a hidden route/answer. Child EVENT/LINK/MODEL texts remain cited interpretation documents, not prerequisites for truthful topology. Then remove ATN LINK-dependence as a certificate claim; causal LINK use remains a separate LoRA mechanism-M test. The weaker alternative is role-split symbol vertices joined only by admitted LINK, but that is not the strongest fair baseline. |
| **P0** | Store eligibility leaks validator feedback and has no exact parity law. | Rejected child rows and “their reason” are searchable, but the design does not require that those exact reason bytes were visible to every ordinary actor. A private rejection label can diagnose the row. Accepted raw and typed copies are legitimate distinct artifacts, but they must not silently multiply into updater-created evidence. | The retriever may index only exact bytes already visible to the corresponding ordinary branch. Preserve rejected child output, but index a status/reason only if that exact status/reason was publicly returned at that frontier. Private validator codes remain audit-only. Each raw envelope and each child-authored interpretation occurs once; wrappers, replay views, scores, cut registries, and evaluator metadata never enter the store. |
| **P0** | The common raw-memory capability is undefined. | ATN receives q16/B8192 raw+typed retrieval, while DLT and SLEEP_FROZEN “retain” a lexical episodic RECALL path whose query, visibility, packing, returned-token, and call budgets are not specified. `RAW_RAG` then appears again as a diagnostic. This permits unequal input bandwidth or duplicate conditions. | Freeze one `RAW_PUBLIC` lexical lane and give it to all three on-policy systems under the same automatic-query and B8192 envelope. ATN uses that same envelope to rank raw plus auto-graph/interpretation documents; it gets no additional tokens. `SLEEP_FROZEN + RAW_PUBLIC` is the on-policy raw-RAG comparator. Do not run another identically configured `RAW_RAG` arm. If the architecture instead removes raw retrieval from DLT, say so and version that material change; do not leave it implicit. |
| **P0** | The reusable-structure stratum is not integrated. | RS8 adds authenticated `MODEL <series> ...` text, but ATN-v2's validator, live-document law, fixed-history law, graph, and packing specify only EVENT/LINK. RS8 also gives ATN up to 128 extra query generations/root before immediate candidate scoring while the LoRA conditions receive no THINK turn. That is not an equal inference protocol. | Add one `MODEL_INTERPRETATION` lexical document type: exact child bytes, eight public evidence citations, visible at the common SLEEP barrier, searchable by SERIES, and never converted into a graph edge or affine solver feature. For candidate scoring, run query-1 automatic retrieval once for every carrier and then score all four candidates with **zero** condition-specific generation calls. For behavior, all carriers retain the same 16+1 actor calls. The existing v2 bytes cannot silently ingest MODEL: either freeze an explicit `ACTIVE_TEXT_NATIVE-v2-RS8` extension, or include this lane in the new v2.1 schema, with its own source/config hash before the shared excluded roots. |
| **P0** | A four-root small store does not certify a 571-block lifetime store. | BM25/PPR can pass on 15--36 records and fail once hundreds of same-grammar rows and identifiers enter the store. The planned lifetime “required-row retrieval” then turns scalability failure into an observed DLT win instead of a precondition on a strong opponent. | Before confirmation, pad every certificate store with prospectively generated, eligible public distractors to the exact cut-4 cardinality and token/type marginals (`571` semantic blocks plus the registered raw envelopes). Certify q16/B8192 there. Before any 709/847 plateau extension, repeat a model-free and actor-visible maximum-load check at 847 blocks. Failure is `BASELINE_INVALID`; it cannot support superiority. |
| **P1** | “Equal actor-token opportunities” hides unequal inference work. | The current 2,048 number covers generated text, not ATN's additional 8,192 returned tokens or growing input sequence. Conversely, a `RECALL` command consumes one of ATN's reasoning turns while LoRA access is free. Compute, context, and usable deliberation are unequal in different directions. | The automatic protocol removes the turn tax. Report generated tokens, input tokens, returned memory tokens, actor forward calls, occupied accelerator seconds, retrieval CPU/RAM, persistent bytes, and LoRA fit work separately. Use “equal actor-generation/action envelope,” never “token matched” or “compute matched.” Run the target-independent sham only as a context-position sensitivity, not as a scored replacement baseline. |
| **P1** | Same-DLT-history is overinterpreted. | A disposable ATN rebuilt from DLT history controls raw experience, but it also receives DLT-authored interpretations whose formation was caused by earlier DLT state, while its own auto graph supplies a different access/composition algorithm. This is not a pure substrate or carrier contrast. | Name it **same-history conditional system/access contrast**. A pure carrier statement still needs the finite `TEXT_SAME_SEMANTICS` diagnostic with identical admitted semantic records. Do not infer DREAM value from either: that still requires matched `RAW_CHRONOLOGY_LORA`. |
| **P1** | The root definition changes across plans. | ATN-v2 defines a root as one sealed child plus world/learner seeds; the paper core speaks of independently raised paired child lineages. Reusing one child snapshot supports inference conditional on that child, not a population claim about children. Fixed-history, on-policy, cuts, twins, tasks, and decodes are repeated measures, never extra `n`. | Freeze one of two labels before allocation: independently raised child lineage per root, or independent world/writer roots conditional on one fixed child. Use whole-root sign flips/bootstrap and the already preallocated N rule; retain every failed/rejected/unsafe lineage in intention-to-treat. Do not combine RS8, certificate, DEV, or same-history roots with lifetime `n`. |

## Conditions that should not be duplicated

Use one name for one scientific role:

| retained condition | disposition |
|---|---|
| `ACTIVE_LINKED_TEXT_SUPPLIED` | v2.2 exact-address service ceiling only. It is not a lifetime arm. |
| `TEXT_SAME_SEMANTICS` | finite identical-semantic carrier diagnostic only. Do not rerun the same exact-row service under an `ACTIVE_*` alias. |
| `ACTIVE_TEXT_NATIVE-v2.1-AUTO` | the sole claim-bearing evolving external-memory system. |
| `RAW_PUBLIC` | common lexical lane / raw-only ablation. In on-policy work, `SLEEP_FROZEN + RAW_PUBLIC` already fills this role. |
| `FULL_PUBLIC_HISTORY` | actor headroom ceiling on certificate roots only. |
| exact graph oracle | CPU construct check only. Once ATN itself uses `AUTO_WITNESSED_GRAPH`, a second neural `EXACT_WITNESSED_GRAPH` condition is duplicative. |

`NATIVE_CONTEXT` can remain an early-life diagnostic when the full history
fits, but it is neither a separate longitudinal competitor nor a claim gate.
Truthful twins, necessary cuts, and wrong-root stores are paired mutations of
ATN, not three new baseline systems.

## Smallest strong version

### Frozen system

`ACTIVE_TEXT_NATIVE-v2.1-AUTO` consists of exactly:

1. a frozen child actor;
2. one append-only, branch-local ledger of eligible public raw envelopes and
   exact actor-visible child interpretations;
3. `RAW_PUBLIC` BM25 plus an automatic witnessed-event graph, fixed float64
   PPR/MMR/complete-row packing, and equality-only opaque-ID tokens;
4. automatic retrieval before actor calls 1--16, at most 512 complete-row
   tokens/call and 8,192 cumulative, followed by at most one unassisted final
   call; and
5. immutable citations and restartable derived indexes.

Raw action--outcome envelopes become eligible on the next continuation; sibling
episodes wait for the canonical batch barrier. Child interpretations, including
RS8 MODEL, become eligible only at the common authenticated SLEEP frontier.
Queries/THINK text are task-local and are **not** written into lifelong memory.
Exam/certificate descendants are read-only and never write back.

The LF-framed typed-turn protocol is common infrastructure, not an ATN feature:
DLT, SLEEP_FROZEN, ATN, FULL, RAW, and sham conditions use the identical stop
bytes, parser, conversation append rule, 16+1 call ceiling, and cumulative
generated-token counter. The only carrier-specific operation is what memory
text, if any, is inserted between accepted turns.

The retriever process receives only the frozen config, the eligible ledger, and
the current public task/state/accepted-THINK bytes. It has no filesystem/API
access to answer, route, necessary-bundle, cut, candidate, null-label, future,
or evaluator registries. Byte-taint tests must prove mutations of those private
objects cannot change retrieval.

### One shared certificate, not two

Use the same four permanently excluded roots for ATN and RS8 qualification.
Each has 16 candidate-free tasks: eight maximum-load opaque PCFL cases and
eight RS8 fresh-target cases with no identical target answer row. Run:

```text
FULL_PUBLIC_HISTORY     64 tasks
ATN-v2.1-AUTO           64
RAW_PUBLIC              64
NONE_SHAM               64
ATN truthful twin       64
ATN necessary cut       64
ATN wrong-root          64
                       ---
total                   448 tasks
```

The exact solver remains CPU-only. Retain the current strict floors: FULL and
ATN each `>=60/64`, no root below `14/16`, legal finals `>=61/64`, exact
citations, required evidence returned in `>=60/64`, reusable success `>=30/32`,
twin redirection `>=12/16` per root, registered cut-family loss, and wrong-root
equivalence to NONE with zero false-root citation. Among cases FULL solves, ATN
may lose at most `3/64` pooled and at most `1/16` in any root; gains do not
cancel losses. Also require the same gates at the sealed 571-block distractor
load. RAW has no pass threshold; it measures the value of graph/typed access.

`q16/B8192` is sufficiently strong only in this conditional, named sense: the
maximum-load certificate passes, every necessary bundle is reachable, FULL
still has no material headroom over ATN beyond the registered bound, and no
larger-access result has yet contradicted it. It is not intrinsically
“saturated.” Under automatic retrieval it grants no additional model
generation or THINK opportunity, so it is memory bandwidth rather than an
extra reasoning budget. Returned/input tokens and retrieval compute remain an
intentional resource advantage of the external-memory system and are reported,
not falsely matched. The RS8 predictive panel may not add 128 ATN-only model
calls on top.

At 17 actor calls/task this certificate is at most `7,616` logical calls and
`917,504` generated tokens. Only the five retrieval-bearing rows above
(`ATN`, `RAW`, twin, cut, wrong-root) can return memory, for at most
`2,621,440` returned tokens. This replaces the generic 512-task ATN certificate
and the separate RS8 text certificate; it must not be run twice.

### Lifetime and stopping order

After v2.2 DEV, writer-scale qualification, and the shared certificate:

1. run ATN on-policy with the first 16 paired lifetime roots at all five cuts;
2. test DLT versus SLEEP_FROZEN and DLT versus on-policy ATN with root-level
   AUC/terminal/retention gates;
3. only if the DLT mechanism and lifetime gates pass, spend the 3,200
   fixed-DLT-history ATN tasks; and
4. use that already-run terminal fixed-history endpoint for FINAL_BATCH.

The certificate plus on-policy stage is `3,648` tasks and at most `62,016`
actor calls. The conditional fixed-history stage adds `3,200` tasks and
`54,400` calls. Neither view creates new independent roots. Broad reusable
language additionally requires the RS8 root-level gate; opaque PCFL alone can
support only an exact-binding result.

## Resource feasibility ruling

The current `85.5 A40-hour` planning estimate divides a short C0 reference by
logical calls. ATN cost is dominated by input length and repeated attention to
up to 8,192 accumulated returned tokens, so a `160 A40-hour` post hoc cap is
not a feasibility proof. The full minimum path already reserves `142.4`
A40-hours for N=16 ONE_EPOCH_SCALE training plus `22.2` hours for scale
qualification and up to `160` for ATN: **324.6 A40-hours before v2.2 DEV,
non-ATN lifetime inference, or RS8**. Adding the current v2.2 DEV planning
ceiling makes it roughly **343.6--344.6 A40-hours**, still excluding those
items.

Before allocating confirmation roots, profile cold/warm ATN at empty, 157-,
571-block stores using the exact 1/8/16-turn prompt shapes and bind a stagewise
token-bucket/device-second ledger. A resource stop may occur only before a
presealed stage/root block; already incomplete roots remain failures. If the
profile cannot fund the complete 448-task certificate plus first-16 on-policy
stage, defer the superiority claim. Do not reduce retrieval, drop tasks, or
call an exceeded cap a LoRA win.

## Claim boundary

Even a complete pass permits only:

> On independently randomized PCFL roots [or: conditional on one fixed child],
> the periodic DLT system exceeded the frozen, automatically retrieving
> ACTIVE_TEXT_NATIVE-v2.1-AUTO(q16,B8192) system on-policy; the corresponding
> same-DLT-history conditional system/access contrast also favored DLT.

It does not establish superiority to external memory generally, a pure carrier
effect, DREAM compiler value, recurrence, parenting, physical compression, or
saturation. A text win or match is a valid result and leaves a bounded LoRA
reuse result intact if its own causal gates pass.

## Final disposition

**REWORK.** Accept a claim-bearing evolving-text baseline only after all of the
following are frozen together: automatic target-blind retrieval; shared
LF-framed typed turns; equality-only identifier normalization; public-envelope
auto graph; exact common RAW lane and lifecycle; explicit RS8 MODEL extension;
571-block shared certificate; root-unit wording; and prompt-length-based
resource profiles. Until then, ATN-v2 is a promising design memo, not an
implemented, strong, fair comparator and not a gate the LoRA can claim to beat.

## Evidence inspected

- `AGENTS.md`
- `research_loop/COORDINATION.md` through the latest ATN/RS8/interface entries
- `research_notes/analysis/2026-09-13_active_text_native_v2_executable_design.md`
- `research_notes/analysis/2026-09-13_full_objective_paper_claim_coverage_audit.md`
- `research_notes/64_iclr_paper_core_and_benchmark_v2.md`
- `research_notes/analysis/2026-09-13_pcfl_dev_to_paper_grade_successor.md`
- `research_notes/analysis/2026-09-13_pcfl_scalable_sleep_writer_bridge.md`
- `research_notes/analysis/2026-09-13_pcfl_v22_minimum_execution_closure_contract.md`
- `research_notes/analysis/2026-09-13_pcfl_vertical_dev_v2_synthesis.md`
- `research_notes/analysis/2026-09-13_pcfl_strong_external_memory_fairness_audit.md`
- `research_notes/analysis/2026-09-13_pcfl_reusable_affine_gate_stratum.md`
- `research_notes/analysis/2026-09-13_pcfl_exploratory_a1_read_interface_result_audit.md`
- `research_notes/analysis/2026-09-13_pcfl_exploratory_a2_a3_result_addendum.md`
