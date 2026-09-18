# R201 caption clone readiness — NOT USABLE for real acceptance

Bounded sidecar report to Main. Candidate: `bt_widegap_v2`, node4 physical2,
owned by `research_loop/workers/r177_caption_game_stage1_20260917/data_judge`.
Direct read-only node4 observation: **2026-09-17 19:28:49.496589 PDT**
(`2026-09-18T02:28:49.496589Z`). Local checks ended at
`2026-09-18T02:29:51.999110Z`. This is completed evidence, not an ETA.

## Decision and actual completed evidence

- The public scoring report completed at **2026-09-17 18:30:36.967922 PDT**;
  `COMPLETED.json` followed at **18:30:37.388718 PDT**. This supersedes the
  18:22:12.854018 PDT observation in which the report was absent.
- Fitting completed **100,000 comparisons / 200,000 caption draws / 6,250
  updates**; the selected checkpoint is step 6,250. Training completion is
  **not** acceptance readiness.
- Vote-mass **tau is `null`**, status `NO_FEASIBLE_HELDOUT_THRESHOLD`.
  Calibration used 3,328 examples; no usable acceptance operating point was
  found. `q` means `EXPECTED_SOMEWHAT_OR_FUNNY_VOTE_MASS`, not rank200 quality
  or human acceptance precision.
- The separate rank200-quality threshold is also **`null`**, status
  `BLOCKED_NO_REGISTERED_RANK200_QUALITY_OPERATING_POINT`; its public audit
  says `BLOCKED_RANK200_QUALITY_POINT` and `full_judge_usable=false`.
- Public development audit: **0 accepted / 1,536 examples, coverage 0**.
  Rank200-quality audit likewise accepted 0. Do not turn these into a
  positive precision claim. Report status is
  `PROVISIONAL_REUSED_DEVELOPMENT_ONLY`; locked validation and FINAL were not
  used, and human validation / second blind comparator are not complete.

## Loader and game roundtrip

- `gpu/ny_caption_judge.py:920` requires legacy
  `NY_TRAINED_JUDGE_CONFIG_V1`; `load_cpu_judge` at line 943 calls this gate
  before importing model libraries. The candidate producer declares
  `NY_WIDEGAP100K_SCALAR_JUDGE_CONFIG_V2` at
  `research_loop/workers/r177_caption_game_stage1_20260917/data_judge/bt_widegap_v2.py:355`.
  The actual private config body was **not read**. A synthetic schema-only
  probe reproduces `provisional_trained_judge_only` before model loading.
- The legacy loader expects three-class humor plus separate two-class scene
  fit and temperature calibration, not a scalar BT adapter with isotonic
  calibration. `GameConfig(tau=None)` rejects with
  `tau must be an explicit numeric threshold`. A synthetic legacy judge with
  missing tau also refuses acceptance.
- **Synthetic game submit → JSON restore → cached replay → continue passes
  for PARENTED and UNPARENTED.** Restore/replay invokes no injected callbacks;
  continued submissions preserve accounting. These fixtures use invented
  scenes, captions and a fixture-only tau of 0.7, never the real candidate.
  Actual scalar model loading and real scorer→game roundtrip are **not
  demonstrated and not usable for this candidate**.
- The focused pytest attempt could not run because `/usr/bin/python3` has no
  `pytest`; direct standard-library assertion checks above passed. No
  dependencies were installed, and neither torch nor transformers was loaded
  by the direct checks.

## Disposition to Main

**The blocker is not loader-only.** The prerequisite for proposing an
acceptance-unblocking scalar-loader patch is false: neither registered
threshold exists. Keep this candidate out of real acceptance. Do not invent
tau, reuse a legacy tau, substitute rank200 quality for vote-mass q, or relax
the acceptance gate. A future scalar-loader compatibility repair would still
need a separately usable, bound threshold before enabling this arm.
**No implementation patch made or queued; report to Main before any edit.**

## Receipts and boundary

Remote root:
`/localhome/local-rohing/orch_r177_ampere_judge_20260917/bt_widegap_v2`.

| Receipt relative to remote root | Bytes | SHA-256 |
| --- | ---: | --- |
| `training/PUBLIC_SCORING_REPORT.json` | 5397 | `11f0daccc968e6c453638c89be97a0360bfa5685f25e1a74a0e5be608f9ae896` |
| `COMPLETED.json` | 331 | `95e4f84bc591a0856d6271ad13efe784ca87aea09c2d3207fa307c6270f71f4c` |
| `training/FULL_POOL_SELECTION_REPORT.json` | 714 | `ee0fecf39fdc58ae7df6b4e08ebbb20f0f6a7e373fa27259c83dff56ed7e4ab3` |
| `training/throughput/006250.json` | 341 | `3da7e3e5d004fcd50762af70929e1bd9c8a69b033442808ba0280b6fdcb54f30` |

`COMPLETED.json` binds a 11,791-byte `training/judge_config.json` with hash
`5c3fb5fd35a26fb0585c09ee91ebc457c31871f591aabfb7a9f53fb05dbc86a8`.
Its existence/size were checked by stat only; its contents and digest were
not independently read/recomputed. The completion reference supplies that
digest. Machine-readable receipts and local source hashes are in `STATUS.json`.

Only public aggregate scoring/operational metadata and source/synthetic
fixtures were inspected. No private contest rows, sealed/FINAL content,
calibration curves, reference-panel scores or adapter weights were read;
nothing was provided to a child or parent. No training, model inference,
GPU calls, process stops, credential output, subagents, judge-task changes,
or COORDINATION edits. Writes are confined to these two status reports.
