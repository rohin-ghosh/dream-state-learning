# Prospective Q0 revision: measure the registered dose, not just its first step

Date: 2026-09-13. **DESIGN ONLY / EDITSTOP.** Main owns implementation, source snapshots, resource selection and launch. No experiment, source or existing evidence was modified. This is a project-involved recommendation, not independent replication: I previously assisted downstream/helper/probe tests, manuscript consistency reviews and the bounded Q0 metadata review; I did not author or numerically reproduce Q0 here.

## Recommendation and authority

Declare a new contract, provisionally **Q0-FULLDOSE-v2**: a three-root, paired **P_AUTH versus P_DERANGED**, contemporary OFF-controlled comparison at **128 updates per fitted arm**. Change the first-step **efficacy stopping policy**, not the optimizer or final behavioral thresholds. Keep the original first-step measurements and their pass/fail arithmetic; a finite, correctly replayed miss no longer terminates a fit. Remove the outcome-dependent third V/unary fit from this bounded comparison. This is a new endpoint-based contract, **not a repair that retroactively makes v1 pass**.

Why this first: SEQ126 measured only one update in each of three fits. An AdamW update on an averaged quartet need not improve every row's signed margin; dropout-active training and the dropout-off canary also measure different surfaces. That does not make the old canary wrong. It makes requiring all directional checks after update1 a distinct criterion from whether the specified 128-update training dose can acquire the conditional map. Test the latter before simultaneously changing rank, LR, objective, material semantics or representation. There is **no guarantee** more steps will help; they can preserve failure or increase spill.

Rohin's raw message30 and the September13 **04:21 UTC** coordination direction explicitly request a revised prospective recipe, three roots, and birth/Q0 work in parallel. The coordination reference `c39f3b53` is user-supplied and was **not Git-verified**. The older E0 watcher memo says to end rank/LR/dose/seed/objective search on this supplied family, but expressly disclaims launch authority. Newer Rohin authority supersedes that recommendation to stop this campaign branch. Retain E0's valid cautions: preserve the rejection, make adaptation explicit, do not search for a passing seed/quartet, and do not lower thresholds after observing outcomes. E0's addressed endogenous representation remains a separate proposal, not a prerequisite or a substitute control for this comparison. Rohin's optimism is campaign direction, not evidence or permission to suppress failures. No new formal C11 process is proposed.

## What stays frozen; what changes

| Field | Prospective choice |
| --- | --- |
| Base/learning locus | Same frozen Qwen2.5-7B-Instruct public revision `a09a35458c702b33eeacc393d103063234e8bc28`; only LoRA learns; no birth/old fitted adapter initialization. |
| LoRA | rank8, alpha16, dropout0.05; q/k/v/o/gate/up/down projections. |
| Optimizer | LR3e-5, AdamW betas(0.9,0.999), eps1e-8, weight decay0.01; fresh empty state per arm; no scheduler/clipping, fused/foreach false. |
| Numerics/objective | Existing pairwise common-prefix objective; BF16 base/forwards, FP32 trainables/gradients/loss/optimizer; eager attention, no TF32/checkpointing; unchanged numerical bounds and raw canary replay. |
| Dose | Same 32 target-balanced quartets, four sweeps, 128 uninterrupted updates; average four row losses per update; no truncation, packing, gradient accumulation change or checkpoint restart. |
| First-step policy — NEW | Store unchanged raw gradients, parameter delta, projections, margin changes and pass flags. Finite/replay-valid misses are diagnostic only, not an early efficacy stop or an endpoint veto. |
| Arm allocation — NEW | Exactly two planned fresh fits per root, AUTH then DERANGED, independent initializations with matched initial bytes/RNG within the root. No conditional diagnostic-only DERANGED; no V/unary third fit. |
| Root allocation — NEW | Three new sealed opaque-ID instances with seeds fixed below, not old root1 resumed or relabeled. |
| Administrative ceiling — NEW | 10,800 seconds per root, two attempted fits, 256 updates; immutable before launch. This is a proposed ceiling, not a measured runtime estimate. |

The statistical comparison is map-conditioned writing against the matched opposite map and OFF. There is **no separately randomized stop-versus-continue arm** and no objective/rank/LR contrast. Retaining the actual update1 canary provides the within-fit diagnostic, not a causal estimate against v1's historical stopped run. A second identical one-update fit would add cost without answering the missing endpoint question; omit it. Do not claim a pure stopping-policy treatment effect across changed roots/seeds.

## Prospective roots and material boundary

Seal all three allocations before seeing any new fitted response:

| Replica | Identifier allocation seed | LoRA/optimizer RNG seed shared by its two arms |
| --- | ---: | ---: |
| R0 | 501 | 1 |
| R1 | 502 | 2 |
| R2 | 503 | 3 |

These are arbitrary proposed allocations, **not generated or selected by outcome here**. They jointly vary identity and optimizer seed: report **root/seed confounding**, three paired instances, not three isolated estimates of seed variance or architecture-level replication. All roots have the same orientation `(0,1,1,0,1,0,0,1)`, templates, panel topology and deterministic scheduling algorithm. New opaque names necessarily change tokenization and may change hash-derived quartet order; preserve and report each actual order, never choose the first quartet by gradient/result. Both arms within a root must use identical order and pre-forward RNG receipts for all512 training-row forwards.

Smallest material construction seam: project the already pinned original **material only**, as `source_rows` does, then alpha-rename both the trained root's tools and its separate wrong-root tools in a new material contract. Retain original indices1/0 as template-role coordinates and carry R0/R1/R2 separately in custody metadata. Example deterministic naming prescription: `sq0_` plus the first24 hexadecimal characters of the existing canonical `digest(["Q0-FULLDOSE-v2", identifier_seed, role, slot])`, with `role` fixed to `trained` or `wrong_root`. Derive neighbours by the existing last-character toggle. Record exact substitution tables and original source-row hashes; substitute only the declared identifier occurrences. No global request ID, arm name, replica label, seed or target enters prompts. Copy prompts remain byte-identical.

Recompute native rendering, IDs and prefix hashes under the new manifest. Validate no unintended text changes, no tool/neighbour collisions across allocations or with the old tools, all original balance tests, and unchanged exact128/held64/spill32/wrong-root64/copy8 topology. Train only exact128 rows. The held, wrong-root and copy rows never enter losses. Shared copy text is intentional, not an opaque-ID collision. Public snapshot binding is prospective and machine-specific; node3's accepted binding is not evidence about another node or historical clean ancestry.

**Actual integration limitation:** v1 hardcodes `ROOT=1`, orientation and the archive, rejects `material != original`, and leaves `confirmation_allocation=None`; its semantic helper also constructs fixed two-root identifiers. Three command invocations against v1 do not create three new roots. A small versioned preparation/allocation path is necessary. Do not monkeypatch globals, relabel existing artifacts, import old fit outputs, or silently relax v1's validator. Collision/native-tokenizer incompatibility is a disclosed preparation failure, not permission to try seed504 until something looks favorable.

## Execution, stopping and interpretation

Reuse the existing ten-stage serial lifecycle **within each root**:

`audit -> OFF/0 -> AUTH fit128 -> AUTH/32 -> AUTH/64 -> AUTH/128 -> DERANGED fit128 -> DERANGED/32 -> DERANGED/64 -> DERANGED/128 -> terminal reduce/release`

Each stage has its existing fresh process/load and adapter-custody checks. A fit trains uninterrupted; snapshot callbacks cannot change model/optimizer/RNG. The two fits start from the same root initialization, not from one another. Evaluators reload the exact snapshot frozen, without a live parent or training context. Keep root-local arm order fixed; do not make claims that require randomized temporal ordering.

- **Unchanged pre-fit exclusions:** failed source/model/material/custody checks, contemporary OFF copy failure, and the existing audited both-objectives-zero-tangent terminal branch. Preserve the latter as an explicitly incomplete-dose outcome, not a resource error or full-dose failure. Nondegeneracy versus near-degeneracy alone must not allocate a third fit.
- **Safety/integrity stops remain mandatory:** nonfinite loss/gradient/parameters/state, invalid/raw-unreplayable audit or canary, initialization/RNG/snapshot mismatch, failed actual forward counters, worker/process/release failure, resource/lease deadline. Abort without retry, preserve partial evidence, and mark endpoints unexecuted rather than zero-correct. A pure directional miss is not in this category.
- **No efficacy stopping after admission:** AUTH canary failure, AUTH endpoint failure, flat/worse margins at32/64, or one root's failure cannot truncate DERANGED or cancel other prospectively allocated roots. Diagnostic flags survive unchanged. No extra sweep, seed replacement, best-checkpoint selection or extension after the cap.
- **Endpoint128 is primary:** both arm `cell_gates` and the existing exact/held complementarity and wrong-root conditions must pass. Keep exact correct>=116/128, per-class>=56/64, valid>=122/128, zero multiple actions, >=14/16 keys with>=7/8 correct, positive per-class median signed gain over OFF; held correct>=52/64, recalls>=24/32, valid>=61/64, zero multiple actions, >=12/16 keys with positive median signed margin. Keep copy8/8; locality mean absolute q/M change<=0.05 and each<=0.10, identity/action-category changes zero except wrong-root<=3. Keep correct complementary pairs>=112/128 exact and>=48/64 held; wrong-root opposites<=3/64.
- New terminal namespace: e.g. `Q0_V2_FULL_DOSE_ENDPOINT_PASS`, `Q0_V2_FULL_DOSE_ENDPOINT_FAIL`, or explicit incomplete/precheck/runtime status. Expose every failed component and first-step flags; do not emit the old first-step-qualified pass or an old `EARLY_*` label for a completed128 fit. Report all3 planned roots, completed endpoints separately, and failure-inclusive rootwise results; do not pool away one failed root. A prospective all-three-endpoint criterion may be reported only if all3 complete and pass; no success-conditioned confirmation root.

SEQ125 remains nonreportable. SEQ126 remains `EARLY_XOR_QUARTET_STOP_AUTH`, qualifiers `BOTH_MAP_FIRST_STEP_MISS`, `EARLY_UNARY_TOOL_STOP`, `OPAQUE_TOOL_WRITE_FAILURE_THIS_RECIPE`: three total updates, no ON snapshots/readouts, **not zero final accuracy and not general impossibility**. Its report SHA is `250e67b36c16325f5b8042e7731dd71c615cd0387c1f1f6d092b68e8188c87e5`. Even a v2 endpoint pass after a first-step miss does not satisfy v1's conjunction or automatically open a dependent endogenous relay. No H1/H2, generalG3, P1/G5, retention, clean-origin or mechanism-freeze promotion.

## Full-dose accounting and three-root feasibility

For roots that clear the preserved pre-fit exclusions and complete every stage:

| Work | One root | Three roots |
| --- | ---: | ---: |
| Fits / optimizer updates | 2 / 256 | 6 / 768 |
| Training-row forwards | 1,024 | 3,072 |
| Snapshot adapters | 6 | 18 |
| Fresh worker stages | 10 | 30 |
| Evaluation prefix readouts | 1,632 | 4,896 |
| Greedy generation requests | 888 | 2,664 |
| Maximum generated tokens (32/request) | 28,416 | 85,248 |
| Natural-prefix forwards including audit/training/canary/evaluation | 3,072 | 9,216 |
| Maximum counted model forwards | 31,488 | 94,464 |

Derivation: OFF/final AUTH/final DERANGED each have288 prefix readouts and296 generations. Four intermediate32/64 readouts contribute192 prefixes each. Audit uses128 natural forwards; each fit uses128 initial +512 training +16 canary forwards. Total model forwards equals natural forwards **plus actual generated tokens**, not generation requests. These maxima retain all existing panels; do not quietly spend only one-step budgets or replace missing readouts with zeros.

Proposed resource contract: per-root10,800s inclusive of source verification, all10 stages, cleanup and durable terminal publication; reserve the existing45s cleanup interval in worker deadlines. Two attempts/256 updates are hard caps with no retry. Allocate a separate **1,800s post-terminal CPU replay/collection window per root**, not charged invisibly to model execution. Preserve the native **six-hour lease buffer**: an uninterrupted slot should have at least12,600s before `lease_end - 21,600s`, or declare the proposed schedule infeasible; do not start a predictably underfunded root and call that scientific failure. A post-terminal replay/collection overrun leaves verification unresolved, not a passed replay.

At most three root workers run concurrently on **three separately reserved suitable GPUs** (one worker per root at a time): up to9 GPU-slot hours, roughly3h execution wall time plus post-terminal work if parallel,9h if serial. The old ~23min run completed only one-step fits plus audit/OFF and does **not** establish that these full-dose roots fit3h. Max-length generation, full-logit/tensor storage, CPU replay, disk capacity and actual device compatibility remain practical uncertainties; no resources or live perception outputs were inspected. Main must confirm slots and existing local public-model/environment receipts, especially on nodes1/2. CPU code acceptance alone is not a throughput or hardware guarantee. Birth work is logically independent and should not be serialized behind this comparison; neither does this memo authorize sharing another job's GPU or killing it.

## Exact implementation seams and bounded CPU acceptance

Implement a **new versioned recipe path** using existing low-level supervision, serialization, numerical and release utilities; preserve the pinned v1 snapshot and replay route. Do not change constants globally underneath a v1 capsule. These are the scientific seams, not a request to build another execution framework:

1. `gpu/astra_pairwise_q0.py:162` `read_original_capsule`, `:194` `source_rows`, `:263` `schedule`, `:289` `build_prepared`, `:321` `validate_prepared`: separate new allocation/renaming/prepared binding from legacy exact-archive validation. Carry root identity, recipe/version and seed through preparation and request custody; regenerate rather than relabel token IDs.
2. `:844` `train_fit`, especially `:916` break and expected-count checks: new policy keeps update1 audit but runs128 after finite canary misses. `:1163` `validate_fit` must replay the same numerical canary yet expect128/512 and snapshots32/64/128. Keep numeric safety checks, actual optimizer state and neutral diagnostics untouched.
3. `:1140` `next_fit`, `:1181` `Lifecycle`: fixed AUTH/DERANGED full fits independent of efficacy; no third branch. `:1282` `primary_label`, `:1297` `reduce_evidence`: endpoint qualification and incomplete denominators under the new version, no first-step veto. Reuse `acquisition_gates`, `locality_gates`, `cell_gates` and complementary-map arithmetic without threshold changes.
4. `:815` `Budget`, `:1487` native config, `:1582` preparation, `:1730` worker, `:1846` controller, `:2003` reducer and `:2078` replay: bind versioned seeds/caps/allocation consistently in launcher, manifest, tickets, reports and replay. Catch the controller's literal `fit_cap=3, seconds_cap=2700` near1932; editing only module constants is insufficient. Preserve raw counters, fresh load identities, deadline/lease math and actual cleanup queries. No silent new-node portability assumption.

Required small CPU additions beside, not in place of, frozen v1 regressions:

- Extend real CPU toy/autograd tests around `tests/test_astra_pairwise_q0.py:431`: constant/mode/tool fixtures with failing finite canaries still emit128 steps,512 row forwards and three snapshots under v2. They can still fail final binding. Legacy `:454` one-step-stop tests remain unchanged and pass under v1. Show canary measurement/snapshot callbacks leave uninterrupted model/optimizer/RNG trajectories unchanged.
- Extend release-table/lifecycle tests (`:541`, `:853`): all four AUTH/DERANGED canary combinations and failed AUTH endpoint yield the fixed ten-stage plan; no diagnostic-only arm, V/unary, third attempt, result-based cancellation or retry. Preserve zero-tangent/OFF-copy branches distinctly. Nonfinite/corrupt/release/timeout failures still stop.
- Material fixtures: three deterministic disjoint allocations; exact renaming roundtrip to original public prompts; no hidden target/mapping/replica/call-marker text, held leakage or control substitutions; all quartet and shortcut balances, native prompt/branch receipt binding. Test actual local public-binding validation with CPU fixture bytes rather than bypassing it wholesale; defer real tokenizer/native checks to Main, not this design task.
- Reducer fixtures (`:571`, `:601`, `:615`, `:639`, `:715` onward): an endpoint-passing fixture with a failed first canary is a **v2** endpoint pass with diagnostic preserved, never a v1 pass; no one-step fixture can masquerade as complete. Mutated initial/RNG/raw canary/snapshot, wrong replica/seed/version, extra/missing readout and threshold-adjacent failures reject. Verify the exact full-dose counts above and no accuracy inferred from absent endpoints.
- Native-controller **mocks** (`:892` onward), not native runs: all10 stages, per-root cap10,800, two attempts, aggregate counts, actual ownership receipt contract, failure/no-retry,45s cleanup, six-hour lease cutoff and terminal-write overrun; v1 config/caps/replay still isolated. Keep existing decoder-hook counter regressions; fixture mocks are not numerical replay evidence.

No CPU suite was executed for this design-only memo. I inspected the relevant tests and used local integer arithmetic for budgets; Main's implementation needs its own recorded test count/log and immutable source/preparation bindings. The recipe above is intentionally just one prospective candidate. If it fails, preserve that result and make any subsequent change another explicit contract rather than tuning these roots.

## Reviewed custody and limitations

Exact SHA256 of inspected files (whole-file hashes do not imply whole-file review):

| File | SHA256 |
| --- | --- |
| `gpu/astra_pairwise_q0.py` | `1459c037cccf2f043bc02f40fb9957f38c5620a4d0bcfc8cbb4ebf30fd31182a` |
| `tests/test_astra_pairwise_q0.py` | `bc08064301721157fa353247559105a31b11ee3e0c3b14d5dbbbfa255b9d42e3` |
| `research_notes/THESIS_RAW_ROHIN_2026-09-11.md` (message30 only read) | `b22c37b4590aff9c479a1bf2dedb7fb755d7b83522f9f2252ab50c6223b88e0e` |
| `research_notes/astra_memos/ASTRA_Q0_FIRST_UPDATE_STOP_2026-09-13.md` | `e8fa45555718b643d74a078405dd342ceef5b4d9f0c2ef14014bb400b6b17901` |
| `research_notes/analysis/2026-09-13_post_q0_failure_endogenous_event_row_gate.md` | `f506ff6ea9c8f3787dfc18dc5027393c5945dbd0bfa7bdb3af1a9c57da4c4949` |
| `organism_v6/semantic_writer_diagnostic.py` (material seams) | `d6ea45ac6bfb5cabe6cbd1224f4cf101e96cbd0e07c029e934c2aa3e03e1ddb0` |
| `organism_v6/multikey_writer_gateway_simple.py` (material seams) | `b9fd33c7c11b2f57395f08d609bb1df004d9663eeefd143060bb1a24a34f10c8` |

Stable byte-section pins, because coordination is concurrently maintained:

- Message30: from `## Message 30` up to but excluding the newline before `## Message 31` (EOF if absent),6,742 bytes, SHA256 `a5c67799902e3167bbafbbc9ba0038ca09bf5707be25fa3f90a58976faa5a46d`.
- Coordination: from `## [Rohin — decisions and steers, relayed by Fable] 2026-09-13T04:21Z` up to but excluding the newline before `## [Builder] 2026-09-13T04:27Z`; includes Fable's04:21 explanation,3,812 bytes, SHA256 `f4a3ca0a274a91c0e7698e1dcc1a8a1af9c6555d7082dc796ef4fda1584a9ada`.

Checks used: targeted `sed`/`rg` source/test/memo reads; `sha256sum`; a standard-library-only Python byte-section hash and integer-count calculation. No Git, network, model/tokenizer imports, numerical tensor replay, GPU/native execution, resource polling or live perception outcome reads. Historical stop/custody facts are attributed to the canonical memo and earlier bounded metadata review, not revalidated from full tensors here. Only this design file was written. **EDITSTOP.**
