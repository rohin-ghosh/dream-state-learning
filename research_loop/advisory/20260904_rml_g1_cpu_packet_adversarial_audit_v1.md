# RML G1 CPU packet adversarial audit v1

Date: 2026-09-04  
Scope: read-only audit of the current RML G1 CPU implementation and evidence packet  
Disposition: **REJECT as GPU-ready; advisory only; no approval is claimed**

## Executive judgment

The CPU packet is a useful partial implementation of the ratified G1 design. The four-READ/nine-ENV machine, public target equality, exact-key memory service, 18-condition roster, supplied-gold scripted positive control, basic CUT closure, and narrow claim strings are materially real. The recent repair that retains complete prior emitted operations and READ keys in model-visible history is present and its regression passes.

It is not a closable pre-GPU packet. There are three independent classes of blockers:

1. **Governance/design closure is absent.** The ratified G1 requires an impossible P-ATOMS structural value of 0/2, while the current code correctly exposes a fixed-policy witness for 1/2. G1A proposes a repair but remains `human_required` and `implementation_authorized: false`. The current implementation cannot silently inherit it. The original G1 context also binds a missing `rml_d0/stage_a_report.json` byte hash.
2. **The scientific reducer and ledger accept invalid evidence.** A successful trace can cite the decisive rows only at the final COMMIT and still pass; a forged machine success is trusted without independent D0 replay; and a registered ENV opportunity can dispatch a READ-state call. These are original-scope implementation bugs, not G1A niceties.
3. **There is no actual GPU gate runner.** The repository has a provider-free oracle script and a one-slot `dispatch_one` seam, but no frozen 18-trajectory orchestrator that loads the model, renders the hashed chat prompt, enforces clean-process isolation and exact tokenizer accounting, creates child interventions from frozen parent citations, persists all 234 dispositions, aborts globally on infrastructure/resource failure, seals outputs, or verifies the full runtime/resource envelope.

The six CPU test functions pass, but that means only that the currently asserted unit/scripted checks pass. It does not satisfy the six ratified replacement tests as scientifically defined.

## Audit basis and execution

I read `AGENTS.md`; the original G1 change, both interpretations, critique, consensus, ratification, authorization, scope, and intake state; the full G1A change, both interpretations, critique, consensus, constructibility audit, policy-certifier design, and intake state; every file under `rml_stage_b`; the Stage-B prompt, operation schema, and workflow; the directly relevant D0 world, target, source, and planner code; and every generated G1 artifact currently present.

`pytest` is not installed. I imported and invoked all six `test_RML_G1_*` functions directly under Python: **6/6 passed in 8.0 seconds**, with no model, network, or GPU calls.

I also ran three read-only adversarial probes. They produced:

```text
late_commit_citation_passes True True True True
forged_state_credited True True actions_same_as_gold False
env_registry_dispatched_as_read ENV READ False
```

Those results are reproducible counterexamples to the intended citation, D0-authority, and opportunity-ledger semantics.

## Original ratified-scope blockers

### O1 — The binding T03/R07 precondition is false, and the only repair is unratified

Severity: blocking governance and construct-validity defect.

The ratified G1 consensus requires the selected P `ATOMS_REC` slice to have exact structural capacity 0/2. Current code finds capacity 1/2 and exposes a witness (`fixtures.py`, `build_slice_certificate`, lines 321–374). The CPU test explicitly asserts `atoms_best_policy_success_capacity == 1` and `not ratified_atoms_zero_capacity_consistent` (`test_g1_cpu_preflight.py`, lines 257–268). The generated `cpu_end_to_end.json` correctly calls this a blocking consensus inconsistency.

This is not a passing implementation of ratified T03. The current open-loop/fixed-signature calculation is also not the exact full visible-history policy certificate demanded by original R07: it intersects shortest complete action signatures (`fixtures.py`, lines 213–247, 321–348), while a permitted deterministic controller may branch after authorized visible histories diverge. `planner_enumerator_agree` is merely the conjunction of depth-nine and 12-shortest-path checks, not an independent upper-bound checker.

G1A addresses the category error and specifies the complete shared-history policy class, independent upper bound, selection commitment, and capacity branches. But its intake is still `human_required`; its consensus says implementation is forbidden. Therefore:

- the original exact G1 gate is not satisfiable as ratified;
- the G1A semantics cannot yet be used as authority;
- no canary or scientific dispatch is permitted.

Required regression/evidence:

1. Ratify an exact amendment before implementation is treated as binding.
2. Emit a complete history-dependent capacity certificate plus independently checked upper bound, not `_best_fixed_capacity` alone.
3. Mutation-test visible-history split/merge, side swap, hidden-bit injection, adaptive public-feedback branching, fourth-return visibility, ninth-action application, and corrupted witnesses/certificates.
4. Fail preflight if any ratified structural predicate is false; never label the corresponding test “passed” while merely recording the contradiction.

### O2 — The exact G1 deliberation context is not reconstructible

Severity: blocking pre-GPU provenance defect; not by itself evidence that D0 science changed.

The original change and both interpretations bind `rml_d0/stage_a_report.json` at SHA-256 `346bd091…`. The sole clean HEAD version hashes to `e36be91f…`; `git log --all` exposes only that committed version, and no repository JSON matches `346bd091…`. The current preflight detects the mismatch (`run_cpu_preflight.py`, lines 43–49, 150–159) and includes it as a blocker.

The likely cause is generated receipt drift: the Stage-A report transitively carries a `resource_hash`, and the resource record includes runtime wall/RSS values. That makes this more plausibly a lost generated-context byte artifact than a semantic D0 change. Nonetheless, the ratified architecture change explicitly incorporates the old context hash. A reviewer cannot reconstruct the exact deliberation input or honestly approve a byte-bound packet from the current repository.

Narrow disposition:

- First preference: recover the `346bd091…` bytes.
- Otherwise, use governance to bind a stable semantic projection of the Stage-A report (gate values, source/world/oracle commitments, predecessor hashes, pass/failure fields) separately from volatile runtime receipts; compare that projection against a regenerated report; and ratify the replacement reference.
- Do not silently substitute `e36be91f…`, and do not characterize the mismatch itself as a scientific failure.

Exact regression: generate Stage A twice with intentionally different elapsed/RSS receipts and assert that the ratified semantic-manifest hash remains equal while receipt hashes remain separately preserved.

### O3 — No scientific GPU runner or runtime closure exists

Severity: blocking implementation gap.

`runner.py` ends with `run_scripted_cpu_gate`, which uses host-known plans and decisive handles. `machine.py` exposes `dispatch_one`, a single provider call. There is no code that performs the registered gate.

Missing executable behavior includes:

- construction and immutable persistence of all 234 opportunity identities before dispatch;
- target/condition dispatch order and one clean process/KV/cache/workspace reset per trajectory;
- model/tokenizer loading at the pinned revision and actual chat-template/system-prompt/user-renderer composition;
- constrained deterministic generation, stop/finish reason, and truncation detection;
- exact tokenizer counts for prompt, history, scratch, returned rows, and output;
- per-call, trajectory, whole-gate, wall-time, GPU-hour, artifact-byte, and spend enforcement;
- global fail-closed cancellation on infrastructure or resource failure;
- dependency cancellation for intervention children;
- construction of CUT/SHAM from the frozen parent's actual cited handles, not oracle handles;
- immutable trace/output sealing and post-run review binding.

The prompt file and JSON schema exist, but `dispatch_one` sends only `machine.model_visible_bytes()` to an abstract provider (`machine.py`, lines 466–530). No implemented provider composes the prompt/chat template/schema, and no runtime closure contains real hashes. `model_canary.json` truthfully says `actual_canary_run: false`, `runtime_hashes_bound: false`, and `gpu_dispatch_ready: false`.

Required regression: a CPU fake-provider integration test must run the exact 18-trajectory orchestrator, verify 234 precommitted identities, exercise success/early-terminal/provider-failure/resource-failure/dependency cancellation, assert zero retries or transfers, seal a replayable ledger, and prove the same rendering path is used by canary and scientific calls.

### O4 — Citation credit can be laundered at final COMMIT

Severity: blocking scientific-scoring bug.

`score_frozen_trace` records the first slot at which each handle is cited and checks only that its row was returned before that citation (`reducer.py`, lines 69–106). It never associates a citation with the action the row allegedly supports or checks that the citation precedes the decisive action.

Counterexample: start from the successful scripted `GOLD_REC:J_H` trace, remove citations from every ENV record, and place the exact pair/valve handles only on slot 12 COMMIT. The reducer returns all four of:

```text
citations_returned_before_use = true
citation_semantic_entailment = true
decisive_citations_minimal = true
legal_commit_success = true
```

The pair and valve decisions were already made. This defeats ratified R05/R06's temporal causal-use predicate and makes `gold_minimal_paths_4_of_4` overcredit post-hoc citation.

Exact regression tests:

- pair handle first cited after the first pair-dependent ACQUIRE/APPLY decision → fail;
- valve handle first cited after CONFIGURE → fail;
- both first cited at RUN or COMMIT → fail;
- correct handle cited on/before its mechanically declared support boundary, after exact return → pass;
- citation returned after support boundary, even if cited later → fail.

The reducer should define predeclared action-support boundaries and score each decisive fact against its boundary, not merely citation occurrence.

### O5 — The offline reducer trusts the machine artifact instead of independently replaying D0

Severity: blocking D0-authority and artifact-integrity bug.

The reducer copies `machine.outcome_state` and `machine.state.success` directly into the score (`reducer.py`, lines 117–130). It does not replay canonical action records from `initial_state(case.spec)`, verify every record/raw-operation transition, check contiguous slots/phases, or compare the recomputed terminal state and result codes with the artifact.

Counterexample: take a failed `NONE_REC:J_TWIN` machine, replace only its terminal `state` with the successful GOLD state and set `outcome_state` to `SCIENTIFIC_VALID_SUCCESS`. `score_frozen_trace` credits both `d0_terminal_success` and `legal_commit_success`, even though its action signature differs from the valid GOLD action trace.

That violates the required separation in R06: D0 must remain the authority for world transitions and legal terminal success, and the Stage-B reducer must independently agree on D0-owned fields.

Exact regression suite:

- mutate terminal state, outcome label, one action, result code/text, slot index, phase, raw output, returned row/status, or record order independently; every mutation must be rejected or recomputed to nonsuccess;
- replay the exact public actions through unchanged D0 and require byte/field agreement at every transition;
- verify that a successful state without a legal ninth-slot COMMIT is never credited;
- verify the reducer consumes serialized immutable artifacts rather than trusted live dataclasses.

### O6 — Opportunity identities are not bound to the machine state, trajectory, or order

Severity: blocking accounting/state-machine bug.

`OpportunityLedger.append` verifies that an event repeats the fields encoded in its registration, but `dispatch_one` never checks that the registration matches the machine's current slot/phase or target/trajectory (`machine.py`, lines 72–88 and 466–530).

Counterexample: pass slot-4 ENV registration for `GOLD_REC:J_H` with a fresh slot-0 READ machine and a provider that emits a legal READ. The call is accepted; the ledger records phase `ENV`; the machine records phase `READ`; the machine remains nonterminal.

The ledger also permits out-of-order event append and has no machine/trajectory binding. Therefore 234 registered IDs do not yet guarantee 234 phase-correct scientific opportunities.

Exact regressions:

- reject any registration whose trajectory, target, slot, or phase differs from the active machine;
- reject slot `k+1` before slot `k` is disposed;
- reject events after terminal except typed zero-attempt suffix cancellation;
- reject whole-child dispatch unless its parent dependency is frozen and eligible;
- require exact equality among registry phase, machine phase, parsed operation phase, and event phase.

### O7 — Resource overflow can occur after a call without a durable typed terminal event

Severity: blocking fail-closed accounting bug.

`OpportunityLedger.append` creates a candidate ledger and then raises if trajectory/gate totals exceed a ceiling (`machine.py`, lines 86–113). A call may already have occurred, but the over-ceiling event is not returned or durably persisted. `dispatch_one` checks some per-call limits but does not predict/check aggregate limits before dispatch and has no global cancellation path.

Additional closure defects:

- history and scratch/row checks use `conservative_cpu_token_count`, not exact pinned-tokenizer IDs (`machine.py`, lines 475–509; `runtime.py`, lines 146–159);
- provider output has no finish reason/truncation flag, so max-token truncation cannot be classified as required;
- provider accounting types, nonnegative wall time, and exact input-token agreement are not validated robustly;
- `GateResourceUsage.validate` is detached from any runner;
- zero-attempt resource failures are counted by `reconcile` as generic “cancelled”, collapsing the typed current failure into suffix cancellation;
- generated `call_accounting.json` contains only counts and the trajectory roster, not the 234 immutable opportunity IDs or dispositions.

Exact regressions:

- one call crosses each per-call, per-trajectory, and whole-gate token/byte bound by one unit; the current opportunity must be persisted as `RESOURCE_CEILING_EXCEEDED`, every undispatched identity must receive the right cancellation reason, and reconciliation must remain exact;
- exact tokenizer counts must be independently recomputed from saved bytes and compared with provider counts;
- `finish_reason=length` or generation exactly at an unfinished max-token boundary must become `MODEL_INVALID:TRUNCATED_OUTPUT` (or the ratified typed equivalent), never schema-valid;
- wall/GPU/storage/cost overflow must trigger the prescribed global uninterpretable-run state.

### O8 — Pretarget ordering and deterministic selection are asserted, not enforced

Severity: blocking R03/R07 evidence gap.

`build_selected_cases` directly hard-codes one D11/module/mode construction (`fixtures.py`, lines 139–210). It does not materialize the complete candidate universe, eligibility predicates, ordered comparator, rejected predecessors, or first-eligible selection trace. The returned `selection_rule` is a string inside a later certificate, not replayable selection evidence.

The provider-free runner also calls `build_selected_cases()` before `build_pretarget_snapshot_universe()` (`runner.py`, lines 111–115), contrary to R03's required store/index/query seal before pair, target, side, or parent selection. The top-level preflight happens to build snapshots first, but the evidence-producing runner reconstructs its own targets and snapshots in the wrong order and consumes neither a seal token nor an immutable manifest.

Current functions are target-free in their explicit signatures, so I found no direct target-field leak in the existing path. The defect is that the required causal ordering and first-eligible rule are not capabilities enforced by the API or recorded in evidence.

Exact regressions:

- a selector cannot run without a verified pretarget store/index/query seal object;
- emit the entire ordered candidate manifest, eligibility results, tie keys, selected index, and target manifest hash;
- mutation of candidate order/tie break/eligibility/selected identity must fail closure;
- running the scripted or fake-provider gate with selection before store seal must be impossible by construction.

### O9 — CPU artifacts contain misleading local pass flags

Severity: material review hazard.

`interface_audit.json` says `passed: true` while `stage_a_context_hash_matches: false`. `fast_gate_report.json` says `passed: true`, but it is an oracle-scripted harness whose GOLD actions, citations, CUT behavior, and twin plan are host-selected. The summary more carefully says `gpu_dispatch_ready: false` and lists blockers, but consumers can easily ingest the individual local pass booleans without the summary.

The scripted gate is valuable as a transition/reducer fixture; it is not evidence that a model can operate the interface or that interventions will be generated correctly from actual parent traces.

Required regression/evidence:

- every artifact must distinguish `local_check_passed`, `acceptance_test_satisfied`, and `gpu_prerequisite_satisfied`;
- any bound-context mismatch must make the corresponding acceptance artifact false;
- machine-readable dependencies must prevent a local scripted pass from being promoted without the packet summary and reviews.

## Scientific meaning of the control/intervention design

### What is currently sound in principle

- All four public target byte strings are identical; the model is not handed a side label.
- NONE uses the same four READ slots with empty exact-key returns.
- P ATOMS mounts the same H atomic snapshot on both P sides.
- GOLD returns direct source-derived pair and valve relations, making the resolver task model-facing and feasible: the public target maps conditioner families to cartridge handles, the pair row selects two families, and the valve row supplies the mode.
- AUTH replay, byte/token-matched SHAM, equivalence-closed CUT, and actual-world/twin-world directional replay are the right families of controls for this small construct diagnostic.
- Nine actions are necessary, so explicit diagnostic ENV detours cannot be free.

These facts support a narrow integration/construct falsifier only. The four sides are nested exposures from one deterministic fixture and cannot support reliability, generalization, learning, memory-superiority, or paper claims.

### P-ATOMS 0/2 is a brittle false-stop once capacity is 1/2

The empirical 0/2 rule remains ratified and G1A explicitly proposes to preserve it. It is scientifically defensible only as a deliberately stringent operational observation: “this exact deterministic model did not realize either atom-only side.” It is not defensible as a construct-validity requirement or information ceiling.

With exact shared-policy structural capacity 1/2, a competent deterministic resolver can deliberately realize one fixed H-side policy from atomic conditioner mappings. A 1/2 outcome can occur with no leakage, no nondeterminism, and no failure of connected memory. Stopping G1 as scientifically failed in that case would be a false stop. The design already tolerates the analogous lucky-policy capacity in NONE with `<=1/4`; P's stricter zero rule has no coherent structural justification.

The narrowest better gate is:

```text
P ATOMS registered denominator = 2
both outcomes must be SCIENTIFIC_VALID
observed success count <= 1
at byte-identical visible histories, the two runs must implement the same deterministic policy/output
no hidden-side-dependent branch is permitted
0/2 = strict-control clean
1/2 = capacity-attaining qualified control, not G1 failure
2/2 = blocking capacity/determinism/leak contradiction
```

Keep P GOLD at 2/2 and all AUTH/SHAM/CUT/TWIN predicates unchanged. Report GOLD-versus-ATOMS as a nested diagnostic contrast without inferential statistics.

This threshold change is a genuine benchmark-taste decision. It changes a ratified empirical predicate, and neither original G1 nor current G1A authorizes it. It requires a fresh exact architecture amendment and human ratification; it must not be slipped into a bug fix.

## Unratified G1A requirements (advisory, not original-scope authority)

Even after the original-scope bugs above are repaired, current code does not implement G1A's proposed additions:

1. **Complete capacity proof:** no shared byte-history policy forest, lower-bound policy table, independently checked upper-bound certificate, or mutation suite exists. The fixed-signature calculation is insufficient.
2. **Affirmative source-only provenance:** rows carry only the generic visible support `SRC_PUBLIC` (`memory.py`, lines 237–305). There is no closed dependency DAG, row-level lineage to exact public source events, hermetic ambient-capability denial, or independent source-entailment checker.
3. **Byte partition/firewall:** there is no explicit `STORE_BUILD_SERVE_DERIVED` versus `AUTHORIZED_PUBLIC_TARGET_INTERFACE` artifact or side-channel equality proof.
4. **Selection commitment:** there is no full candidate order/eligibility/tie trace sealed before capacity, nor fail-closed handling of unexpected capacity branches.
5. **Amendment allowlist:** no machine-readable exact diff against the ratified consensus/packet exists.
6. **Evaluator-only placement:** capacity witnesses, policy tables, hidden side states, scores, and certificates do not yet have an executable one-way visibility/capability artifact.
7. **Additive evidence files:** the proposed `selected_slice_capacity.json`, `source_only_snapshot_audit.json`, and `amendment_scope_audit.json` are absent, appropriately so while implementation is unauthorized.

These are requirements only if G1A (or a successor amendment) is ratified. They must not be used to imply that the present G1A consensus approved implementation.

## Lower-priority robustness issues

These should be closed in the runner/reducer repair but are secondary to the blockers above.

- `RmlActionMachine.advance` accepts a `next_key` from returned payload and adds it to `allowed_keys` without proving membership in the sealed query universe (`machine.py`, lines 331–363). Current production rows do not emit `next_key`, but a mutation can expand the language. Reject or seal-authorize every expansion.
- Runtime closure validation checks that component values look like SHA-256 strings, not that they equal hashes independently recomputed from the files/container/runtime they name.
- Review approvals are plain in-memory strings with no persisted packet manifest, actor evidence, or immutable approval artifact. This is harmless while reviews are absent but insufficient for actual release.
- `SHAM_REC` matching is based on relation, serialized byte length, and CPU token count. The GPU path must rematch with exact pinned-tokenizer counts and persist the selected equivalence classes and proof that they were unopened/nondecisive.
- The operation JSON Schema leaves `ENV.action` structurally open. The Python world parser closes it after generation, which is safe for scoring, but constrained generation/canary claims must not imply the schema itself closes the 23-action grammar.

## Recommended order of work

1. Resolve the genuine benchmark choice: ratify a successor amendment that repairs capacity/source provenance and adopts either the scientifically preferable P-ATOMS `<=1/2` qualified rule or an explicit taste decision to retain brittle 0/2.
2. Recover or governance-rebind the missing Stage-A context using a stable semantic manifest plus separate volatile receipt.
3. Repair reducer replay and citation-to-decision timing; add the counterexample tests above.
4. Repair opportunity/machine binding, ordering, resource-failure durability, exact tokenizer accounting, and truncation handling.
5. Implement and fake-provider-test the full 18-trajectory orchestrator, including parent-derived interventions and global cancellation.
6. Implement the ratified capacity/provenance/selection artifacts and verify every original plus amended pre-GPU test.
7. Freeze exact bytes and runtime hashes, then obtain a fresh independent implementation review and a distinct author-side scientific-advocate review.
8. Only after those approvals may a target-disjoint canary be considered. No GPU scientific dispatch is currently authorized by this packet state.

## Final disposition

**Not approved. Do not run the GPU canary or scientific gate from the current packet.**

The strongest positive conclusion is that the CPU scaffold captures much of the intended interface and that the world/memory construct is likely repairable. The current packet still has falsifiable scoring/accounting bugs, an unreconstructible bound context artifact, an unresolved and unratified benchmark correction, and no runnable GPU experiment. A fresh binding pre-GPU review must occur only after the exact authorized repair is complete and frozen.
