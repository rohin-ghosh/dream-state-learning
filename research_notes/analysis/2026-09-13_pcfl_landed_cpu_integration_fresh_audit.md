# Fresh audit: landed PCFL CPU integration

**Date:** 2026-09-13  
**Role:** independent CPU/static audit after the first PCFL implementation landed  
**Decision:** **REJECT native zero-fit release. ACCEPT the code as fail-closed CPU scaffolding and a useful scripted fixture. No scientific result exists yet.**

## Scope and immutable snapshot

This audit inspected, without editing, the current worktree versions of:

| component | SHA-256 |
|---|---|
| `organism_v6/pcfl_vertical_dev.py` | `03cc4fea5f606f223c15289b4cc86db9f9534bcddb5d3f298b39a0b06b09ab4f` |
| `organism_v6/pcfl_vertical_prepare.py` | `e80266c4241116dc5701f8a394590645229ca089318903545ad064a1835e26a4` |
| `organism_v6/pcfl_vertical_train.py` | `b8d033566574967e6f579c6b1451e65c1bb15a99fce554ba71ced0c270ad39c3` |
| `gpu/astra_pcfl_vertical_dev.py` | `026c6a8c50f551d874a605e1975f5fe2189643fcbd5e6694c0ad2d2fea0544b1` |
| `organism_v6/pcfl_tokenizer_qualification.py` | `da30eb90a8655ec0707dd8c83c22ed08f1032dadb7a663edd7102774e0e84d3a` |

I also read the current tests and the two currently relevant prospective D-binding texts:

- `research_notes/astra_memos/ASTRA_PCFL_PRODUCTION_WORLD_BINDING_2026-09-13.md`, SHA-256 `ac2013fe44c3f9bdfdca43defca0d8b19baa39209fab443b74abc128391fea91`;
- `research_notes/analysis/2026-09-13_pcfl_distractor_execution_contract_candidate.md`, SHA-256 `7c2f21756b93b36ceea20cb837d5df9f990c03ed1d4a049872e2e59ce1dfbe71`.

No model, tokenizer, native backend, training job, remote host, or GPU was used. No runtime file was changed.

## Tests run

| command | result | evidentiary scope |
|---|---:|---|
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_pcfl_vertical_*.py' -v` | 102 run: 100 passed, 2 skipped | core, preparer, writer unit/synthetic behavior; skips were local Torch and opt-in tiny lifecycle |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_astra_pcfl_vertical_dev tests.test_astra_pcfl_cpu_smoke tests.test_pcfl_tokenizer_qualification -v` | 51 passed | scripted runtime and synthetic opaque-ID qualifier |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m compileall -q` over the four requested modules plus qualifier | passed | syntax/import compilation only |

Total: **153 run: 151 passed and 2 skipped**. This is strong evidence that the intended fixture and fail-closed boundaries are internally consistent. It is not evidence that the native assay is prepared or executable. The code generally labels this limitation honestly.

I also built a synthetic contract and inspected its accepted registries. The validator reported:

- `bridge_invariants_valid = true`;
- `execution_contract_valid = false`;
- `static_contract_complete = false`;
- `ready_for_model_calls = false`;
- 12 missing interfaces.

That is the correct top-level outcome.

## Executive findings

1. **The production D binding is not implemented.** The core still exposes an explicitly invalid production binding, and its fixture uses the old `Z --qD--> Y` distractor with a successful nonterminal probe. Both newer texts instead choose `X --qD--> Z` with shared `q0/q1` semantics and a terminal distractor.
2. **There are two incompatible prospective byte contracts.** Both choose the same high-level X-to-Z topology, but they disagree on exact public `PROBE RESULT` bytes/final LF and on whether r9/r10 private probe-observation receipt objects exist. Native work must not begin until one source wins, is hash-pinned, and the other is explicitly superseded.
3. **The 800-task runtime is only a scripted oracle-backed fixture.** It constructs 800 tasks, but does not join the 800 presealed work rows to real prompts, token receipts, native generations, process identity, or once-only collection.
4. **The preparer validates a strong schedule shape and the full CAL Boolean decision table, but accepts semantically degenerate synthetic inventories.** Counts can pass while every single-actor work item points to the same root, prompt, and state; diagnostic and cut registries can be tiny placeholders.
5. **The writer has a good response-only loss implementation and exact replay semantics, but native custody is deliberately false.** Its training entry point correctly refuses the current contract. There is an additional full-generation-versus-extracted-span identity seam that native formation must close.
6. **Opaque-ID qualification is structurally promising but not production-qualified.** It has not run the pinned tokenizer, and its caller-provided slot manifest is not checked against the canonical core slot names/cardinalities.

## Requirement matrix

### 1. Real `X -> Z` D binding and shared q

**Status: BLOCKED / not landed.**

- `pcfl_vertical_dev.production_binding_status()` returns `VS_ASSAY_INVALID`, null D endpoints and outcomes, and `production_inventory_complete=False` (`pcfl_vertical_dev.py:114-122`).
- `require_production_bindings()` unconditionally raises (`:125-126`). This is an appropriate fail-closed behavior.
- The current fixture graph instead contains `("Z", "u", "Y")`, while the relevant edge is `H --qR--> S_R` (`:167-175`).
- Fixture probing maps the distractor to source `Z`, destination `Y`, and a q port, issues an r10-like internal receipt, and stores that result as the next exploration affordance (`:522-540`, with `_affordances` at `:510-512`). Therefore the fixture distractor is a successful continuation, not a terminal X-to-Z result.
- `render_reachout` also exposes Z/Y for the distractor (`:407-416`).

The two prospective replacement texts agree on `X --qD--> Z` and on choosing D from the same q0/q1 namespace as R. They do **not** agree on exact bytes or custody:

- the Astra memo specifies a one-line result ending in exactly one LF and private r9/r10 probe-observation receipts;
- the laptop consensus candidate specifies a four-line result with no terminal LF and no D receipt or probe-result receipt ID.

These are not editorial differences: they change the public byte string, tokenizer inventory, root skeleton, receipt schema, join records, and negative tests. One exact contract must be selected before materialization.

### 2. Opaque-ID contract

**Status: PARTIAL; algorithm tested, real inventory absent.**

The qualifier checks namespace prefixes, fixed alphabet/width, uniqueness, forbidden substrings, substitution classes, required training sequences, deterministic traversal, and receipt replay. Its result is nevertheless explicit: `full_production_qualified=False` and `ready_for_model_calls=False` (`pcfl_tokenizer_qualification.py:362-368`).

Two gaps remain:

1. No pinned real tokenizer run and full transcript exists in this worktree.
2. In production mode `_validate_bindings` requires all namespaces, but it accepts caller-supplied names and counts for each namespace rather than requiring equality with the canonical core `SLOTS` inventory (`:123-140`). Thus a complete-looking but structurally wrong production slot manifest could be qualified.

The qualifier must be driven by the adopted D/render schema and must itself compare the exact root/namespace/slot names, order, and cardinalities to that schema.

### 3. All ten renders

**Status: fixture snapshots only.**

The core exposes ten named projections and `render_task` enforces row counts/type-specific views (`pcfl_vertical_dev.py:419-464`). Tests snapshot the collective fixture output. However:

- the snapshots are generated from the unresolved fixture topology and salt-0 synthetic IDs;
- there are no adopted exact R/D result joins, terminal D render, or real-tokenizer receipts;
- `root_skeleton_digest` hashes roots, slots, interventions, diagnostics, environment, and work, but not the render registry (`pcfl_vertical_prepare.py:191-213`). The current test deliberately confirms that mutating a render leaves the skeleton hash unchanged.

That last property conflicts with the new prospective D contract, which requires exact render/join/LF mutations to alter the sealed pre-output root. The production root seal needs to commit to the complete adopted render/parser registry.

### 4. 800 zero-fit work inventory

**Status: numerical count present; native inventory absent.**

The scripted runtime expands exactly 640 delayed and 160 reachout tasks and asserts 800 unique IDs (`gpu/astra_pcfl_vertical_dev.py:60-112`). This is useful controller/scorer coverage.

It is not the production inventory:

- the function explicitly says it is not a native manifest (`:60-64`);
- every task uses `fixture_only=True`, ideal rows, and `runtime-test/...` seeds (`:73-106`);
- it is constructed separately from, and never one-to-one joined to, `work_registry`;
- ACTIVE_LINKED_TEXT adds a system instruction dynamically rather than consuming a fully presealed public render (`:98-103`).

The synthetic `work_registry` has 3,402 rows with expected aggregate purposes, but a direct audit found all 1,106 `single_actor` rows share one root, one prompt hash, and one state. `_work` validates schema, aggregate counts, caps, fit coverage, and reuse references (`pcfl_vertical_prepare.py:562-607`), not one-to-one task identity. It therefore cannot establish an 800-task native work closure.

### 5. Source pins and stale-v2.1 rejection

**Status: PARTIAL.**

Good:

- core/source pins are exact literals;
- writer `verify_sources` rehashes actually imported writer/shared/core/preparer modules before training (`pcfl_vertical_train.py:237-245`);
- tests reject recipe-level stale v2.1 fields such as loss-active PAD, equal-target rules, and the old 14-fit campaign.

Missing:

- preparer source pins permit only the six older protocol pins, optionally plus the older closure pin (`pcfl_vertical_prepare.py:727-733`); neither current D-binding text is pinned;
- preparer implementation pins are checked only for hash syntax, not against the files on disk (`:731-733`);
- there is no single adopted-source precedence record resolving the two D texts;
- stale-v2.1 rejection is not global. I changed a synthetic work row's `denominator` to `PAD_S1_00`; `build_execution_contract` and `validate_execution_contract` still accepted the bridge invariants. The current stale test injects recipe/slot fields only. The old string `PCFL-V2.1-PREP\0` in the seed derivation is explicitly retained and is not itself a defect; the defect is incomplete nested-field rejection.

After the D ruling, bumping the schema/seed domain would make accidental mixing easier to detect.

### 6. Support-overlap schedules

**Status: STRONG structural validation; production materialization missing.**

This is one of the best-closed pieces. The preparer checks:

- 20 slots and exact first/replay rosters;
- replay source identity and replay request/support/bank reuse;
- five epochs, 40 batches, four examples;
- each slot/view exactly once per epoch;
- no underlying-support overlap inside a batch;
- at most one LINK and at most one NEW item per batch;
- same-position counterpart mappings and complete S1/S2 counterpart families.

The writer independently repeats the 5 x 40 x 4, coverage, support collision, LINK, NEW, and W0-W7 checks (`pcfl_vertical_train.py:133-156`). Replay rows reuse the exact source query/target rather than being re-rendered.

What is not established is that a production first-solution joint backtracker created the schedule from real admitted banks. The synthetic helper can fabricate a structurally valid schedule. The contract itself lists the joint-backtracker proof as missing (`pcfl_vertical_prepare.py:755-764`).

### 7. CAL truth table

**Status: Boolean policy complete; measurement-to-Boolean execution absent.**

`_calibration_table` enumerates all 2^3 combinations of `valid`, `safe`, and `acquired` for LOW and HIGH (`pcfl_vertical_prepare.py:182-188`). The tests exhaust all 32,768 possible whole-table Boolean assignments/mutations. The intended policy is correctly represented:

- invalid assay -> invalid;
- unsafe writer -> writer failure;
- LOW safe and acquired -> select LOW;
- LOW safe but not acquired -> run HIGH;
- HIGH selects only if safe and acquired.

No native readout currently derives these Booleans from executed metrics, and the runtime marks CAL and later stages `NOT_IMPLEMENTED` (`gpu/astra_pcfl_vertical_dev.py:324-343`). Diagnostic outputs correctly do not trigger selection by themselves.

### 8. Cuts and causal necessity

**Status: fixture oracle checks exist; prepared coverage/certification insufficient.**

The core fixture checks OLD and NEW cuts against two route oracles (`pcfl_vertical_dev.py:1011-1018`) and validates old EVENT/LINK reconstructability. It does not establish the production D contract.

The prepared synthetic cut registry can pass with only four entries, all on `dev/0`, each referring to eight task IDs. Validation establishes registered kind, disjoint changed/unchanged hashes, local support overlap, and attainable thresholds, but not complete root/state/task coverage or independently reproduced oracle outcomes. The current core registry also reports `link_information_necessary=False`; therefore the assay does not yet causally establish that the critical S1 LINK information is necessary.

### 9. Child EVENT/LINK custody

**Status: good local byte checks; native origin not authenticated.**

Positive controls:

- core admission validates grammar, roots, chronology, receipts, and exact byte provenance;
- formation bridge rejects ideal/ceiling rows, binds rows to exact expected banks, and keeps `native_custody_verified=False` (`pcfl_vertical_prepare.py:662-704`);
- writer requires `origin=CHILD_NATIVE`, exact full-generation SHA, exact byte spans, CHILD_SUBMISSION taint, and derives registered controls itself (`pcfl_vertical_train.py:82-130`).

The unresolved seam is identity across layers. Runtime `audit_formation` may extract an admitted span from a larger generation. Core row provenance currently uses the extracted row's hash as `generation_sha256`, whereas writer lineage indexes the full raw generation hash. Existing tests use `raw == admitted span`, so they do not expose the mismatch. Native formation needs one explicit capture record that binds:

`full raw generation hash -> byte offsets -> exact child span hash -> admitted EVENT/LINK row -> query target -> fit slot`.

`capture_sha256` is currently only syntax-checked by the writer and is not dereferenced to a sealed capture artifact.

### 10. Writer response masking and replay

**Status: strong implementation, non-native evidence.**

`encode_fit` constructs the pinned chat prompt, trains only on exact target bytes plus EOS, masks every prompt token with `-100`, forbids truncation, and uses W0-W7 only (`pcfl_vertical_train.py:200-234`). Training does four unpadded forwards per batch, forms a response-token-weighted mean, performs one backward/update, clips gradients, and emits per-update receipts (`:301-406`). The local tests exercise all 200 updates with mocked tiny models; an opt-in tiny Qwen/Torch test is skipped in the current environment.

Remaining native issues:

- `_require_execution_contract` correctly blocks unless all three release flags are true and no interface is missing (`:317-323`), so current training cannot run legitimately;
- fit authority/custody/selection hashes are mostly format-checked rather than dereferenced to immutable external records;
- DEV can name LOW or HIGH learning rate without a native join to the selected CAL outcome;
- there is no enforcement of the work registry's 1,800-second wall-time cap inside `train_fit`;
- save/release does not verify an owned process group or GPU vacancy;
- the final receipt remains `native_custody_verified=False`.

### 11. Lifecycle and isolation

**Status: scripted assertions only; native controller absent.**

`Runtime.__init__` requires both `scripted=True` and a scripted backend and raises `NATIVE_BINDING_UNIMPLEMENTED` otherwise, even if a validator is mocked green (`gpu/astra_pcfl_vertical_dev.py:207-233`). This is the correct fail-closed guard.

Missing native lifecycle machinery includes:

- sealed request expansion from the work registry;
- pinned model/tokenizer/chat-template file verification at load;
- GPU UUID binding and device-time measurement;
- cold C0 loads and no warm-adapter reuse;
- owned process group creation/termination and independent vacancy check;
- durable raw capture before parsing;
- hard wall-clock interruption of a hung generation (checks before/after a synchronous call do not interrupt it);
- once-only collection/reduction and terminal failure preservation;
- CAL, fit/readout, DEV, retention, interventions, and final reduction stages.

The scripted backend's `close()` merely reports two Boolean fields, and the runtime trusts them (`:393-408`). That is appropriate only for the explicitly scripted test mode.

## Passing tests that are easy to overread

The tests themselves are usually candid. The following names or aggregate green count become misleading only if quoted without their scope:

1. **`test_full_800_unmocked_public_cpu_scorer_path`**: the scorers are real CPU code, but the generation backend is scripted/oracle-backed and contract validation is patched. It proves 800-call controller/scorer traversal, not a native model ceiling.
2. **`test_preoutput_root_registry_and_ten_render_snapshots`**: snapshots the unresolved fixture and intentionally permits render changes without changing `root_skeleton_hash`; it is not the production ten-render seal.
3. **`test_locality_cut_and_work_fail_closed`**: validates syntactic locality, aggregate work counts, and mutation rejection on synthetic data. It does not prove complete cut coverage or a one-to-one 800-task manifest.
4. **`test_five_forty_four_and_w8_never_trains`**: proves that a supplied schedule has the required combinatorics, not that the prescribed production solver was used or that the schedule is the first valid solution.
5. **`test_mocked_full_200_updates_final_only` and the tiny numerical tests**: validate optimizer mechanics and receipts on mocks/tiny random CPU models, not a pinned 7B C0/LoRA lifecycle.

No test covertly promotes these to release evidence: production flags remain false, native mode remains blocked, and the runtime report says `scientific_pass=False`.

## Exact blockers to native zero-fit, in dependency order

Native **zero-fit** does not require the LoRA writer or parenting. It requires these closures, in order:

1. **Adopt one exact D contract.** Select one X-to-Z/shared-q source; resolve one-line-plus-LF versus four-line-no-LF, and r9/r10 private observation objects versus no probe-result receipt. Record explicit supersession and hash-pin the winner.
2. **Implement the adopted production world.** Replace fixture Z-to-Y behavior with the exact X-to-Z terminal transition, exact R/D public messages, parser, private custody, and post-probe state machine. Bump the schema/seed domain. Keep fixture mode separately labeled if useful.
3. **Regenerate and seal the full production registries.** Exact canonical root slot manifest, opaque-ID inputs, all ten renders, parser/join templates, diagnostic addresses, cuts, and render-sensitive root skeleton.
4. **Produce the real CPU construct/shortcut certificate.** Recompute D/R cube truth, terminal behavior, public-byte equality/inequality, route oracles, cuts, and negative mutations from the adopted world—not hardcoded `[1,1,1,0]` fixture labels.
5. **Run real tokenizer qualification.** Use pinned local tokenizer files/template; cover every complete public render, result/join, target, wrapper, substitution mate, negative mate, and response-mask sequence. Preserve the complete first-solution receipt chain.
6. **Materialize the full work contract.** Create exact one-to-one rows for all 800 zero-fit tasks and every required load/continuation/service action, with unique prompt hashes, roots, states, seeds, caps, denominators, cut membership, and profile references. Reject semantic degeneracy, not merely wrong totals.
7. **Make the validator capable of a true result.** Verify actual source hashes, adopted D source, implementation hashes, full profile receipts, complete tokenizer evidence, construct/cut certificates, work joins, and absence of synthetic evidence. Only then may its three release flags become true.
8. **Implement the native controller.** Consume only the sealed work rows, capture raw generations before parsing, enforce token/time/process/GPU bounds, run scorers without oracle leakage to the backend, release owned processes, verify vacancy independently, and reduce exactly once.

Only after those eight steps is a native zero-fit run meaningful. Writer/CAL work can remain downstream and blocked while zero-fit is established.

## Recommended disposition

- Preserve the landed code and tests: they are valuable scaffolding and mostly fail closed correctly.
- Do not run a tokenizer, model, or native backend against this contract yet.
- Treat the X-to-Z source selection as the immediate governance/engineering gate.
- After adoption, implement production bindings in a schema successor rather than silently changing `pcfl_vertical_cpu_v1` fixture semantics.
- Add adversarial semantic tests before release: render mutation must alter the root seal; degenerate work/diagnostic/cut registries must fail; stale PAD markers must fail anywhere in the contract; full-generation-to-child-span custody must replay end-to-end.

The clean claim today is: **PCFL now has a substantial, internally tested CPU scaffold for world mechanics, scheduling, response-masked writing, and scripted 800-task traversal. It deliberately lacks the adopted D binding, production materialization, real tokenizer qualification, native execution, and native custody required for zero-fit evidence.**
