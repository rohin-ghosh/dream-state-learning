# Overnight report — 2026-09-11

Run: `20260911T022751Z`. Inspection-only audit; no GPU launch, no preemption, no modifications of existing modules. Findings below distinguish observed outputs, static code defects, design differences, and unmeasured endpoints. Budget is approaching the harness token limit; this is an early evidence handoff, not six hours of monitoring.

## Fable: first actions

1. **Do not qualify B as an exact-state v7 writer.** It restores GOAL/METRIC but synthesizes a reduced context. Preserve this running experiment as a legacy-ledger organizational diagnostic. Build exact recorded-token prefixes and source eligibility before collecting qualification traces.
2. **Leave GPU 6's existing job alone.** Read its latest markers and `train_B.out`; no duplicate launch. GPUs 2/3 remain outside this agent's launch authority, including the separately chained car test.
3. Reprice the entire enabled script, not its **7.26 GPU-h subtotal**. Probe completed cells incrementally in a future runbook; current script trains every cell before any probe. Do not infer behavioral success from falling training loss.
4. Implement a separate asynchronous writer and transactional active-version pointer; a zero barrier timeout alone does not remove synchronous training from clone 0.
5. Treat the car test as a synthetic diagnostic, not qualification of the production renderer. Resolve factorial confounds and probability-versus-accuracy gate semantics before claiming the memo's engineering gates passed.

## 1. CPU tests and guard observations

Required command: `<venv312>/bin/python tests/run_all.py` (step 3), **exit 1, 82.9 seconds, 157/158 reported checks**. The failing check was `test_dry_run_cli_prints_the_decision_without_running` in `test_astra_agent.py`; its nested CLI denial fixture was blocked by the local guard before subprocess creation. This is an integration failure under the guarded environment, not evidence that the intended forbidden command ran. No bypass or weakened guard was attempted. Suite counts include optional-dependency skips; CPU passage is not GPU isolation, SVD, or full-life acceptance.

Additional helper check: `python3 tools/astra_sandbox/overnight_read.py support` exited 1: Python 3.9 pathlib reached the guard's `os_open` wrapper with incompatible arguments (`TypeError: unsupported operand type(s) for &: 'PosixPath' and 'int'`). The same read-only helper under `<venv312>/bin/python` exited 0. This is a reproducible guard compatibility issue, not a research-module failure. The helper only prints explicitly listed repository excerpts; it never writes research data.

No source fixes were applied. Earlier coordination's 158/158 is a separate run, not a replacement for this observed 157/158.

## 2. Live pretest — observed cells and timing

Evidence: read-only node calls, steps 16–18, 40–42 and 50, all exit 0. Root below means the mission-provided `v6_out/pretest_write_ab/R2_B_seed0` output directory.

`nvidia-smi -i 6` at node timestamp **02:30:29 UTC**: **100% utilization, 35,171 MiB / 46,068 MiB**. This GPU was occupied; no smoke launched.

| Cell | Compile items | Target tokens | Context + target tokens | Latest observed status |
|---|---:|---:|---:|---|
| A | 856 | 159,583 | 159,583 | train marker; 420 s, rc 0 |
| A_v3 | same A input | 160,439 encoded incl. EOS | 160,439 encoded | train marker; 275 s, rc 0; 856 steps |
| B | 7,415 | 5,144,158 | 10,339,599 | training; latest step 1,170 |
| Bs | 635 | 2,572,079 | 3,055,434 | compiled; no train marker |
| B_match | 236 | 159,512 | 332,096 | compiled; no train marker |
| C | 23,352 | 449,474 | 1,905,777 | compiled; no train marker |
| C_tmem | C pairs, different training recipe | unmeasured | unmeasured | no completion observed |

Directory existence does not establish successful training: B and C directories existed but their train markers did not. Timings included an earlier `compile` **rc 2 / 15 s**, followed by a successful **rc 0 / 17 s**; successful Bs compile 14 s, B_match 13 s. A prior failure must not be hidden by reporting only the successful markers.

Latest B log: **1,627,780 processed tokens at 1,105 tok/s**, step 1,170, instantaneous batch loss **0.0031**. This is roughly **15.7%** of the compile input-token total, not 15.7% behavioral qualification. Using constant measured speed, B alone needs about **2.60 h** total versus estimate **2.39 h**, with approximately **2.19 h training remaining** at that snapshot, excluding checkpoint/reload. Speed is about **7.9% below 1,200 tok/s**; projected time is about **8.6% above** that throughput ruler. These projections assume subsequent groups have the same cost and are not completion promises.

`estimate.json`: train **3.66 h**, probe **3.60 h**, total **7.26 h** for listed A/B/B_match/Bs/C at one epoch. The live log explicitly says extras are omitted. A actually uses three epochs; A_v3, C_tmem's five epochs/SVD initialization and extra probe conditions are not completely represented in that subtotal. Therefore **on schedule for a 7.3 h end-to-end completion is not established; that is an incomplete schedule**. All-cell completion requires a revised ledger.

### Endpoint availability and decision rule

At step 50, **0 probe outputs**, `table.md` absent, `summary.json` absent. A and A_v3 adapters existed, but there were no paired scores or ritual/text-fit readouts. `gpu/write_ab.sh:140-175` trains all enabled adapters before `177-193` runs probes; summary is generated at `203-208`. Absence of early probes follows script order, not evidence of evaluator failure.

| Required endpoint | Value this audit can report |
|---|---|
| A/B/Bs/C ON vs OFF, 8-panel and disjoint | unavailable |
| collapsed reps, per-rep scores | unavailable |
| modal first-action share, first-note Jaccard | unavailable |
| held-out conditional text fit ON vs OFF | unavailable |
| B training loss | batch value only; not held-out fit |
| current decision | **inconclusive / no adoption verdict** |

Operative legacy P1 rule (`research_notes/PRETESTS_2026-09-11.md:59-60`): require disjoint B−A ≥ −0.0065 and at least one of disjoint ritual share down ≥0.10, disjoint score gain ≥0.013, or 8-panel gain ≥0.013. Reject under its stated both-panel harm/collapsed-rep conditions. Bs may qualify if within 0.0065 of B on disjoint and no collapsed rep. Rank/epoch/second-seed decisions require cells not supplied by this one initial script. Do not borrow historic seed-777 OFF as the new seed-4242 OFF. Midlife brief is the horizon-matched control; final brief is descriptive, not exposure-matched.

The stricter exact-renderer/source-policy acceptance in `NEXT_EXPERIMENT_DESIGN_v2_ASTRA.md:543-567,724-728` is a different qualification requirement. Legacy P1 passage would not override it.

## 3. Rendered-sequence audit — ranked violations and checks

Normative references: memo 3 `2026-09-11_q3_memo.md:66-98`; memo 5 `2026-09-11_q5_oneshot_design.md:11-105`; corrected design `NEXT_EXPERIMENT_DESIGN_v2_ASTRA.md:541-634`.

### P0 — reduced antecedents are not exact inference states

- Live B manifest: **512 instances, 6,780 child rows, 0 reflection rows; 0 missing heads/intros**. Corpus scan: **7,415 / 7,415** begin with masked `GOAL:`; **67 groups**. Thus the original complete loss of goal is repaired.
- `sleep_compile_v3.py:344-362` extracts GOAL/METRIC and a single-line intro, not CLOCK/current state. `424-450` uses the first prompt's head and reconstructs outcomes. Later stored prompts are not the episode stream's exact prefixes. No assertion verifies token-for-token runtime correspondence.
- Local windows (`619-681`) use this reconstructed head and up to 768 context tokens. **5,596 / 6,780 = 82.5%** local items drop context; **75,183 elements dropped**. In `654-660`, failure to fit a recent element does not stop traversal: older smaller elements can be retained. Example 31 retains older outcome lines while preceding thought text is missing. This is not a contiguous actual prefix.
- A literal CLOCK scan found **2,104 masked-context spans** containing `CLOCK:`. This does **not** repair the state invariant: earlier child text is reused as context and may itself echo CLOCK. Source provenance, not marker presence, must distinguish a real current state from a child's copied state.
- Stored mode is not a repair: `636-647` strips the YOU block and left-truncates the remainder. Corrected design forbids deleting parent-bearing context to manufacture an eligible prefix (`557`). Collect genuinely parent-free continuation windows instead.
- Reflection handling retains extracted summary plus targets, not the full actual prompt/previous reflection (`321-337,365-374,685-705`). Live data has zero reflections, so this branch has no real-example validation here.

### P1 — loss identity and exposure accounting

- B explicitly masks harness outcomes and contexts and attaches thought targets to ledger indices (`534-593,664-681`). Multi-action thoughts have one target per view, not one per action. Silent/failed thoughts remain eligible.
- This is **child-origin supervision**, not exact generated-token identity: canonicalization and stripping rewrite text (`443-446,696-697`). The corrected design prohibits canonicalization (`545`). Audit rendered tokens against immutable generated IDs.
- Trainer adds a supervised EOS (`train_adapter_v3.py:187-190`); first token of each segment is masked for shifted loss (`368-388`). Encoded target totals are counted before collator masking (`524-538`). For A_v3, the 856-token increase from compile count matches one EOS per item; effective loss count is not the unqualified encoded count. EOS is synthetic training structure, not a ledger child span.
- Compile B: **6,780 rows targeted exactly twice**; episode **2,572,079** targets and local **2,572,079** targets. This establishes view multiplicity only, not cumulative optimizer exposure or context exposure per occurrence. Bs targets each row once. C has unequal row multiplicities; its 0.175 mean exposure field must not be read as a simple mean of its occurrence histogram.
- `select_under_budget` (`716-743`) budgets target tokens only, samples newest items then shuffled remainder. It neither budgets all input processing nor retains a pending-fresh occurrence queue. B_match is **target-budget matched**, not compute matched: **332,096 vs A 159,583** processed tokens, about **2.08×**. B's episode share of processed tokens is about **29.6%**, not the specified newer 70%; 50:50 here is target mass.
- Child harness-shaped echo mass is **1,801,466 / 5,144,158 = 35.0%**. Boilerplate target mass **1,749,122**, repeat **1,543,386**. These are descriptive overlapping classifications, not a reason to erase legitimate child restatements. Live leak hits were zero; substring scanning alone does not prove source eligibility.

### P1 — packing is safely bypassed, not validated

`train_adapter_v3.py:326-365` groups by family/program and preserves order within group blocks. This is batching/order, not evidence of transferable neighborhood learning. `368-417` defines segment-first label masking and block-causal masks.

A_v3 isolation output: tolerance **0.25**, first/second max logit difference **1.27344 / 1.27344**, negative-control difference **21.17188**, verdict **NOT_ISOLATED**. Actual trained mode is **fallback_one_item_per_sequence**, mean segments **1**, 856 sequences, 68 groups. Fallback is safe with respect to cross-example attention; do **not** claim actual training leaked between examples merely because the attempted mask failed. It is nevertheless not proof of packed attention correctness. `580-604` implements fallback. `434-475` checks short forward logits, not full-length gradients or perturbation invariance. New v7 should ship unpacked until positive and negative controls pass on its actual model/backend.

### Ten distinct real examples inspected

Steps 41/42 initially selected duplicates; those did not count as ten examples. The corrected cumulative unique set is below; step 50 supplied item 100. Excerpts were bounded, not full token dumps.

| B item index | Case | Target-row evidence |
|---:|---|---|
| 414 | one-turn episode | 1106; outcome score 0.6149 masked |
| 6314 | long 16-turn episode | 20843 … 21145; includes silent target tail |
| 99 | second long-episode window | 415, 432; previous outcomes masked |
| 16 | local multi-action | 29; 3 actions, one target |
| 31 | silent/no executed action | 122; target retained, selective context |
| 7414 | last local item | 24088; prior INVALID outcome masked |
| 0 | first 16-turn episode | 2 … 425; GOAL/intro masked |
| 1 | initial local thought | 2; same row is a second view exposure |
| 28 | local following failed action | 109; INVALID score 0 context |
| 100 | late multi-action local | 415, tick 15; 3 actions, 11 context elements |

Rows are the compiler's filtered-list indices, not asserted raw-ledger line numbers. The ledger hash and exclusion/frontier mapping must accompany any provenance reconstruction. Exact tokenizer-mask comparison against live original generation IDs remains unperformed.

## 4. Memory-dose review against memo 2 §2

### Implemented design components

- `memory_dose.py:94-113,534-562,656-709`: three default banks; 64 owners per bank, 16 per dose **0/1/4/16**; 16 lessons/bank; **within/across** arms; **two interference sleeps**; A/B/C/D and Dshuf factorial.
- OFF measured before assignment (`450-503,674-685`), balanced colors and counterbalancing; explicit opt-in prior-matching is labeled, not default. Shared owners across banks are default, so this is counterbalanced remapping, not three independent owner samples.
- Raw and normalized probability plus candidate mass (`506-524`), ON/OFF × absent/present observation, three paraphrases, distant and adjacent contexts, explicit repaint, similar-owner/unexposed/wrong-property/generic/swapped-owner controls (`1704-1821`). Synthetic targets are explicitly quarantined (`3-6,88-92`).
- Primary I_d arithmetic is sound at the stated level: matching-cue ON−OFF log odds minus similar-ID ON−OFF using the **same a,b per paraphrase** (`1900-1918,1978-2010`); both terms are retained. Reversed conditional lessons score a fixed A vs B (`2082-2102`).

### Deviations / risks needing explicit labels

1. **Factorial confound (major):** `748-769` changes bare text/full-header loss to chat template/masked observation at the same time as adding antecedent. Memo 2 says keep loss coverage fixed at this first stage. Add a matched-template/matched-mask comparison or call current result a compound representation treatment. `antecedent_bare` exists, but A/B/C/D do not isolate it.
2. **Dshuf is not target-frequency-preserving context shuffle:** `796-807,839-877` deliberately rewrites observation AND target bindings. This prevents the target itself retaining owner→color, a defensible inconsistent-binding control, but not the originally described same-target antecedent shuffle. Report those distinct estimands; do not silently rename one into the other.
3. **Accuracy replaced by teacher-forced mean probability:** no generation (`48-59`); in-context/repaint gates use normalized probability ≥0.90 and probability degradation ≤0.03 (`2217-2222`), not ≥90% correctly answered queries. These do not imply each other. Report probability gates as such; add registered answer decisions/generated accuracy for the literal accuracy claim.
4. **`guide` is an interpretation, not pass:** `2242-2296` can return `guide` and list failed gates. G7 retention may be None (`2223-2224`); `failed` excludes unevaluable gates (`2237-2238`). Require explicit pass/inconclusive/fail overall status and per-bank gate tables before selection.
5. **Bootstrap independence:** default shared owners (`656-685`) and pooled `(bank,owner)` bootstrap units (`2110-2135`) do not provide three independent bank replications. Retain owner clusters across mappings/checkpoints and report bank-specific intervals. Newer design asks 10,000 resamples and per-bank acceptance; current helper defaults 2,000. This newer requirement must not be attributed to memo 2 as if it were already implemented.
6. **Cumulative resets constrain interpretation:** all historical events replay (`728-744`); matching final item sets with chronological ordering is an order/history diagnostic, not persistence in an incrementally evolving optimizer state. `gpu/memory_dose.sh:80-99` stages across-sleep endpoint fits for all candidates then trajectories/within/interference for finalist and selected controls. It is not every cell × every checkpoint.
7. **Budget enforcement:** `938-948` pads after assembling content; `980` flags over-budget content rather than proving a hard cap. Target presentation counters use epochs×weight (`961-978`); dedup-weighted loss and separate optimizer presentations are not equivalent (`108-110`). Reconcile actual encoded/masked token counts and padding before a compute-matched claim.
8. **Control averaging can conceal strata:** `2065-2073` averages four unrelated-shift families; `2225-2229` uses a dose trend heuristic. Publish all dose/control cell values, not just pooled pass. The bicycle diagnostic uses the first paraphrase's alternative against mean trigger log odds (`2014`); primary similar-ID I_d avoids this mismatch.
9. **Not the complete newer PC qualification:** corrected design `679-722` additionally requires generated conditional-action/rare-exception tests and an eight-write gap including incremental replay. Current two-interference-sleep synthetic test is a memo-2 diagnostic, not that full suite.

No real car-test ON/OFF measurements were collected by this agent. No claim of successful memory or conditional action follows from its mock tests or static implementation.

## 5. Clone forever-loop audit and concrete v7 change list

### Observed current behavior

- Barrier (`clone_coordinator.py:431-464`) polls/sleeps awaiting all non-finished clones; verdict wait (`544-555`) also polls. Caller defaults locate at `run_life_v2.py:310,315` (7,200 s barrier; 10,800 s verdict).
- `run_life_v2.py:635-707`: clone 0 compiles through legacy `compile_sleep`, closes its inference backend, trains synchronously, gates, then reloads. Other clones wait for verdict. This is **not no-wait asynchronous writing**.
- Good pieces to preserve: atomic slice+DONE (`398-425`), pooled ledger dedup by cursor (`466-511`), candidate staged before gate and gate stats before publication marker (`638-708`). These are foundations, not a fully transactional asynchronous system.
- Mid-problem: no publication polling or hot swap shown in this path. `attach_missed_rounds` occurs only on entering `clone_sleep`; reloading occurs after training/verdict (`641,699-706`). A late adapter waits until a later sleep, not the next ordinary batch boundary. This avoids a shown mid-problem swap, but incurs excessive adoption lag.
- Recovery risk (static, not injected): append is fsynced then cursor advances before POOLING→POOLED rename (`505-511`). If crash occurs after cursor update but before marker rename, restart truncates appended data (`476-486`) while retaining the advanced cursor; retry can skip those rows. Test this exact cut point before claiming restart-safe pooling.

### Proposed build, in dependency order — no edits made

| Priority | New contract/change | Acceptance count/invariant |
|---|---|---|
| P0 | Dedicated writer service; collectors seal slices and immediately resume inference. Remove calls to both waits from collector hot path; do not merely set timeout zero. | 0 clone waits on compile/train/gate; delayed writer does not reduce issued collector batches to zero |
| P0 | Versioned immutable slice IDs with clone incarnation, start/end ledger indices, hash, serving adapter and source-policy namespace. Writer snapshots all available complete unseen slices when beginning a write. | unique pooled IDs = sum of admitted unique source IDs; duplicate delivery adds 0 |
| P0 | Separate submitted, pooled, considered, supervised and active-ancestry exposure cursors. Global transactional pool journal/one-writer lock; commit cursor and append frontier together. | recovery at each append/cursor/marker cut preserves all rows exactly once |
| P0 | Merge completed data one round behind while collectors proceed; log per-clone round age and wall age. One-round lag is a service target, not an all-clone barrier. | measured p50/p95/max lag; overload explicitly marked, never hidden by stalling children |
| P0 | Immutable adapter version with base/tokenizer/config/sample/gate hashes; validated load before atomic ACTIVE pointer. Distinguish candidate, provisional, confirmed, rejected, stale and rolled-back. | 0 partially visible versions; 0 candidate loads before authorization |
| P0 | Poll ACTIVE at batch boundary; pin every active problem and already-started reflection to old version. Load new version before dropping old; keep monotonic load IDs and log acknowledgement. | 0 mid-problem/mid-reflection changes; every generation has adapter+brief version |
| P1 | Implement patience/floor/confirmation state machine separately from train completion; floor tied to best eligible committed record and serving ancestry. Rollback atomically invalidates descendants and restores replay state. | stale candidates cannot reactivate invalid ancestry; no silently decayed immutable floor |
| P1 | Compile exact child-token/source-policy windows, not `compile_sleep` with model-written restatement; use pending-fresh and processed-token budgets. | no foreign targets, no context rewriting, exposure reconciliation exact |
| P1 | Parenting separate from writer and collector; brief applies at next allowed boundary, reflection anti-quotation respected. | parent delay causes 0 collector pauses; private-reflection audits retained |
| P1 | Extend runtime version registry beyond current legacy list (`clone_coordinator.py:88-98`) to exact renderer, trainer, gate, sampler, model-backend and manifest schemas. | frozen manifest covers every behavior-affecting source |
| P1 | Read-only rehearsal plan first, then authorized integration/fault fixtures on reserved resources; do not perform destructive fault injection in this session. | duplicate slices, late final slice, writer restart, failed load, rollback and stale publish all pass |

A timeout only addresses waiting for others; it cannot keep clone 0 thinking while clone 0's model is closed for training. Likewise a DONE directory plus late symlinks is not a globally served-version pointer.

## 6. Scope, remaining gaps and handoff

- Read required guidance, selected required memo/code sections and runbooks; some large outputs were truncated. Do not treat this as an exhaustive line-by-line review of every listed module. The available file titled memo 6 is named `2026-09-11_q7_paper_review.md`; coordination identifies the paper review as memo 6.
- At the coordination snapshot only one heading followed SEQ-022 (`1157`), with two body topics (builds/harness/paper through `1160`). A second later heading was not present. No second entry was invented.
- No adapter behavioral probes were available before this budget-constrained handoff. No six-hour unattended watcher was installed. Continue read-only polling externally; do not launch another write on GPU 6.
- No exact live token-mask/gradient audit, same-prefix teacher-forced behavioral comparison, independent training-seed replication, or real asynchronous soak was completed. These remain release blockers for their respective claims.
- No historical baseline/crossed scores were promoted to this pretest's current ON/OFF cells. Coordination's negative interaction remains background evidence, not newly audited output.

## Evidence locator

- Tool steps 3, 44–46,49: required test output and helper interpreter/read checks (exit statuses stated above).
- Steps 16–18: GPU occupancy, requested B manifest and initial live log.
- Step 40: marker/timing/adapters/probe inventory.
- Steps 41–42,50: rendered corpus scans and ten distinct bounded examples; step 50 additionally latest B progress, full estimate fields and A_v3 isolation result.
- Repository file:line references accompany each static finding. Node values are command-output observations, not repository line citations. No masked internal identifier is required to reproduce the relative-path inspections.
