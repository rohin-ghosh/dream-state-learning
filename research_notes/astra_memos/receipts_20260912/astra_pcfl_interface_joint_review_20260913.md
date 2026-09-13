# Interface component diagnostic review — 2026-09-13

Advisory, non-blocking source review for the next excluded-root A1_READ_DISCLOSED and independent A2/A3 diagnostics. Not full-assay qualification or a launch authorization. No GPU, model, tokenizer, tests, remote access, or native outcome inspection performed. No repository files edited. Future confirmation infrastructure and formal C11 are outside this review and must not block these bounded diagnostics.

## Reviewed snapshot

- `gpu/astra_pcfl_interface_dev.py`: SHA256 `77d088d9d72bfd7fc6cf5bae478f03c2333821d4fbd2a16697ccc2db256b2917` (unchanged across two source-hash reads).
- `tests/test_astra_pcfl_interface_dev.py`: SHA256 `1298fe2ec390b0564407113d022f53a95871f2e5c6d7b2cdf8c78dc6c3c38b25`; source inspection only, no test-pass claim.
- `research_notes/analysis/2026-09-13_pcfl_c0_dev_interface_repair_v2_closure.md`: SHA256 `d4777fe86a444e6231da895a7d1f7cafd21f4f18111911260800c5c94fb0e62b`.
- `research_notes/analysis/2026-09-13_pcfl_c0_dev_interface_repair_redteam.md`: SHA256 `5dd0b25e009c986b228881008b8c1dbb7c95e80051c44b3b577094dbcc3a48dc`.
- Supporting source reads: NativeActor.generate and core parse_read/read_query/score_route. Findings concern these current bytes, not an assumed checkout revision or historical prose.

## Concrete findings and smallest corrections

### 1. Medium — whitespace-only THINK satisfies the required-THINK condition

Evidence: interface lines 269–274 accept `re.fullmatch(r"THINK [^\r\n]+", raw)` and increment `thinks`. Thus `THINK ` followed only by spaces, tabs, or non-CR/LF Unicode whitespace counts. Closure lines 49–56 explicitly require a non-whitespace code point. A later correct route can therefore become an A3 success without a valid THINK under the declared grammar.

Smallest correction: retain the whole-response/no-CR/LF match and additionally require at least one payload character with `not character.isspace()`. Reject the invalid turn immediately, without trimming or salvaging. Add tiny fixtures for spaces, tabs, Unicode whitespace, and a valid payload containing action-looking inert text. This is a byte-contract repair, not a new reasoning-quality threshold.

### 2. Medium — report joint and independent components explicitly; do not repeat the obsolete A3 overlap allegation

Evidence: summarize at lines 212–226 exposes marginal thought/read counts and `route_successes = sum(row['success'])`. However lines 297–304 already require THINK before setting A3 `success`. Consequently A3's success count is already THINK-plus-strict-graph-success, subject to finding 1. The red-team 60/60-but-56-joint counterexample does NOT apply to actual A3 executor-produced successes. The existing `test_think_required_and_disabled_and_no_semantic_route_rescue` explicitly preserves `score.graph_success=True` while `success=False` on a no-THINK route.

The reporting defect is that `route_successes` conceals this conjunction and omits the independent graph component. It cannot distinguish traversal success without required THINK from actual wrong routes using the summary alone. ACTIVE_THINK genuinely retains the read overlap defect: 60 successful tasks and 60 served-read tasks may intersect in only 56, yet lines 222–223 accept the marginals.

Smallest correction for the next diagnostics: expose ordered per-case flags/counts for strict terminal syntax, recorded graph success, valid THINK use, non-MISS served READ, and task-level no-invalid/no-cap completion; name the THINK+route and READ+route (and, where applicable, THINK+READ+route) intersections explicitly. Retain raw component counts alongside them. Preserve 64 cases, grouped into four ordered 16-case root vectors, with A2/A3 paired by `case_id`, not stage-specific task ID. Derive from existing records; no new guard framework or extra model calls. For a later ACTIVE_THINK result, do not describe the existing marginal gate as joint success.

A1 remains a READ handshake diagnostic: its served-read criterion does not require route success. Do not silently replace that endpoint with a route requirement. Report READ+route and subsequent failures descriptively, alongside the declared handshake count.

### 3. Medium reporting risk — COMPLETE does not mean answered, correct, or even called

Evidence: lines 239–248 can end a task with ACTOR_TOKEN_CAP or INPUT_TOKEN_CAP; lines 266–307 similarly preserve length, invalid-turn and service-budget failures. All receive status SCORED. Lines 316–319 call the stage COMPLETE when every task reaches this terminal bookkeeping state and no infrastructure exception occurred. The input-cap regression explicitly expects COMPLETE with zero calls. A1 can also count an earlier served read on a task that later ends malformed or capped, since its summary excludes only invalid READ tasks.

Smallest correction: keep execution completion distinct from diagnostic outcomes; add reason/family counts and explicit generated/uncalled/capped task counts to the descriptive summary. Report per-task generation counts from attempted slots, valid THINK counts, parsed enabled READ attempts (including MISS and over-return-budget lookups), delivered non-MISS reads, actor-output tokens, and delivered service tokens as separate units. Do not convert incomplete-stage uncalled rows' initialized false values into observed wrong answers. Backend/capture exceptions already produce FAILED/ABORTED and should remain distinct from valid-but-wrong ROUTEs and controller failures. No stronger stage qualification is requested.

### 4. Low — service delivery flag does not establish subsequent model consumption

Evidence: lines 288–295 mark a service delivered and increment served_reads using only returned-token capacity, then append it. Context capacity is checked on the next loop at lines 244–248. A non-MISS can therefore count as served even when the next generation never occurs because its rendered context is too long. This is not fabricated service content, but it is insufficient evidence that the actor used or even processed the returned block.

Smallest correction: describe `delivered` as inserted into conversation, and separately expose whether a subsequent generation containing it occurred. If matching closure controller step 7 exactly, pre-render/check the prospective next context before marking delivery. Preserve offered service bytes and the INPUT_TOKEN_CAP reason either way; do not infer service-mediated route use from the marginal served count.

## Dispositions that do not require repairs or new gates

- Main's current CONTINUE is `CONTINUE: follow the declared turn budgets and commit the final action when ready.` It does not suggest READ. Explicit READ-disabled text is present at line 79. The closure's older CONTINUE wording is superseded; freeze the adopted current bytes rather than restoring old prose.
- All three READ forms and directed EVENT semantics are disclosed. Lookup uses the exact frozen query registry and source hashes; MISS does not increment served_reads. No useful address list is introduced by READ_API.
- Valid THINK is retained verbatim as assistant history, followed only by fixed CONTINUE. Action-looking text inside THINK is not dispatched. Terminal raw responses go whole to the unchanged scorer, with no route feedback, retry, normalization, or final-line extraction. Length termination is not rescued.
- Roster construction preserves four supplied excluded roots, the eight cube cells and two goals per root: 64 cases. A1/A2/A3 reserve respectively 832/64/448 calls; actual use may be lower. A2/A3 share task bytes, case IDs and seeds, but differ in THINK instructions and available turns. Any comparison concerns this interface package, not isolated state retention or an equal-compute intervention.
- NativeActor cold startup occurs inside generate after its operation timestamp. Current interface chronology does not incorrectly require operation_started after load.ready_at. Capture verification checks generation joins/default sampling; outer native identity, load/close and process-release receipt remain Main's integration responsibility. The report correctly retains native_custody_verified=False and outer_release_required=True; do not present local replay as native qualification.

No confirmation-root preparation, full-panel implementation, A4 gate, C11 mechanism, or learned-organism claim is a prerequisite imposed by this review. Smallest immediate owner work: correct THINK whitespace, then make component/joint/reason counters explicit before interpreting the next diagnostic.
