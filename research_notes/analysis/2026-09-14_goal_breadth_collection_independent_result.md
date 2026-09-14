# SEQ257 — independent terminal collection review

2026-09-14. **Released; retrospective and nonblocking.** Scope is this collection only, not its successor fits, campaign, or manuscript. No discrepancy found against the notebook's 17:45 admission and 18:00 SEQ257 terminal accounting. This review owns only this memo.

## Evidence binding and method

Evidence root `C` = `gpu_artifacts_local/astra_goal_breadth_collection_terminal_20260914_attempt1/extracted`. Its sibling archive is `astra_goal_breadth_collection_terminal_20260914_attempt1.tar.gz` (not `terminal.tar.gz`), SHA256 `a7ee0b69d392b7d078072c1685f12ffced60346052c6751f4e8eed078375f7de`. Read-only archive comparison verified all **6,455 regular files** against extracted inventory and bytes, with no duplicate, unsafe-path, or nonregular payloads.

Twelve bounded source/helper/test/design files matched local Git objects at **`3ddb8a2f168a03c9f19252358fc429bb6f526230`**. Frozen recipe `research_notes/analysis/2026-09-14_goal_breadth_recipe_design.md` matches commit **`b960e20b4e226bf6fbaf6426289936c711df9175`** and the local design; file SHA256 `3f2e4307dab0ad7aa2d8cf62accf14203da1b6ac32fd58779c62840929640ed7`.

Primary replay used only frozen `source/gpu/astra_goal_breadth_collection.py` and its frozen helpers, calling `read_stage` for expose → teach → baseline with recorded dependency hashes. Breadth APIs retain their private FunctionType-bound goal-pair/hop globals; no old unbound hop defaults were substituted. Separate standard-library JSON reductions checked calls, prompts, responses, transitions, and counters without the helper scorer. Replay validated **95 expose, 198 teach, and 336 baseline output JSONs**, including native-call and state/dependency joins.

## Actual accounting and state

Durations below are independently subtracted `finished_unix - started_unix` in each phase's `RESULT.json`, not admission limits.

| Phase | Actual model calls | Call cap | Seconds |
|---|---:|---:|---:|
| prepare, no model | 0 | 0 | 28.782292 |
| expose | 80 | 80 | 191.979104 |
| teach | 192 | 192 | 203.651261 |
| baseline | 283 | 288 | 235.639773 |

Native phases total **555/560 calls, 631.270138 seconds = 0.175352816 allocated A40-hours**; this is elapsed allocation accounting, not measured GPU utilization. Preparation is separate. Launch files record guardian **410134**, **17:45:05–17:55:40 UTC**, a **635-second** interval; notebook identifies node2 GPU0. Neither elapsed quantity is the **11,280-second maximum guard** (three 3,660-second phase allowances plus 300 seconds admission).

All three native stages are COMPLETE, read-only, training disabled, with **zero fits/updates**. Every recorded before/after state joins to:

`37ec37884e4b0b679edd1dba1be1dec3474589e992649f3a33e7e3b1ec78b8c0`

These are **recorded hash/state joins, not actual tensor authentication**.

## Exposure, teaching, and visibility

The closed inventory is ten worlds: eight TRAIN across four blocks, plus block0 PROBE-A/B; identifiers are disjoint from 174 prior identifiers. Only the bounded prior SEQ255 exposure RESULT/DATA was read to bind exclusions, not its full history.

**80 exposure calls → 40 actual child EVENTs**, four per world. Action/native response/committed receipt/raw EVENT joins and raw/canonical hashes agree. Pre-action prompts omit the outcome, receipt, and EVENT ID; recording prompts receive the actual committed receipt.

**192 coached responses → 192 rows**, four complete 48-row blocks, 24 rows per TRAIN world. Global/block/world indexes and hashes agree. Each target is the actual recorded response, not a substituted ideal answer. Each student prefix equals the uncoached episode history: parent guidance and `CAPTURED SOURCE EVENT (raw)` hint sections are absent. Guided prompts remain explicitly in provenance. Teacher witness/next-command hints derive from actual TRAIN source; this is intentional coaching, not blind autonomous acquisition. No current PROBE identifier appears anywhere in the lessons bundle, including provenance; prior SEQ255 identifiers serve exclusions rather than reused targets.

All **32 guided episodes / 16 pairs** succeed. No actual source or coaching failures occurred here, so there is no empirical failed-source subset to inspect for dropping. Negative CPU tests separately check retained failures and all-or-none row admission. This is guided target collection, **not training or new amortization**.

## Baseline: pairs, failures, and missing-call explanation

Direct reductions verified **283 raw actor calls and all 48 episodes**, including prompts, responses, metadata, literal memory replies, legal transitions, and same-display opposite-goal pair counters.

| Panel | Goals | Strict pairs | Calls | READs | ROUTEs | Terminal outcomes |
|---|---:|---:|---:|---:|---:|---|
| TRAIN OWN_TEXT | 18/32 | 2/16 | 187 | 124 | 62 | 18 reached; 13 dead_end; 1 invalid_route |
| PROBE OWN_TEXT | 4/8 | 0/4 | 48 | 32 | 16 | 4 reached; 4 dead_end |
| PROBE UNAVAILABLE | **2/8** | **0/4** | 48 | 32 | 11 | 2 reached; 1 dead_end; 5 duplicate_address |

Successful TRAIN task indexes (zero-based) are block0 A/B `[0,1]`/`[0,1]`; block1 A/B `[1,2]`/`[0,1,2]`; block2 A/B `[0,3]`/`[0,1,2]`; block3 A/B `[0,3]`/`[1,2]`. Only block1 B and block2 B pass pair `(0,2)`. All TRAIN failures are wrong-first-port dead ends except **block3 B task3**, invalid route before its first commit. ROUTE counts exclude that malformed response.

The five-call shortfall from 288 is explained, not dropped cases: **block1 B task2** and **block3 B task2** each finish in four calls (two reads/two routes), while **block3 B task3** fails at call five.

PROBE OWN_TEXT A succeeds at `[0,3]`, B at `[1,2]`; remaining tasks take wrong branches to dead ends. UNAVAILABLE A fails all four by duplicate address; B succeeds at **tasks1/2 after four literal unavailable replies and two legal routes**, fails task0 by dead end and task3 by duplicate address. Reporting unavailable success as zero would be wrong; no strict PROBE pair succeeds.

A separate **review-only CPU reference**, always selecting the first displayed root port then the sole next port without goal inspection or memory, produces exactly the same successful PROBE OWN_TEXT identities. It is not a native emitted arm or proof that the actor implements that policy. It demonstrates why marginal success alone does not establish robust goal-sensitive composition. Different namespaces from SEQ255 also prevent treating changed pair counts as a same-instance longitudinal regression.

## Commands, tests, and limits

- Local `sha256sum`, `git show <commit>:<path>`, and read-only Python `tarfile`/`hashlib` comparisons bound archive, selected source, and recipe; `sed`/`rg` checked the two notebook entries.
- Inline `python3 -B` replay used capsule source first on `sys.path` and an import guard denying `torch`, `transformers`, `tokenizers`, `peft`, `safetensors`, `requests`, and `httpx`. No runner `main`, model loading, or encoder execution.
- Separate inline standard-library reductions checked source/call/response/row joins, student-prefix stripping, phase durations, native transitions, episode failure identities, and strict pairs. No new framework or harness files were created.
- **11 frozen `GoalBreadthTests` passed**: split/exclusions; private concurrent bindings; public dispatch; complete192 joins; first-port pairs; invalid source before calls; failed-source retention; malformed-child continuation; wrong-goal nonrepair; late errors/bounds; resealed tampering. The subprocess-import and encoder tests were excluded; this is not the full suite.

No GPU, remote/network calls, model/tokenizer/torch loading, live tensor/base authentication, or new launches. String-level prefix checks do not authenticate tokenization or trained label masks. Visibility findings concern the recorded capsule inputs, not an unseen live runtime. No ancestor inventory, successor-fit outcome, manuscript approval, or broader H1/H2 claim is supplied. No notebook, manuscript, production source, or other agent-owned file was edited. **Ownership released.**
