# Root0 varied-memory pair — EDIT-STOP

Owned only this handoff, `/tmp/astra_varied_memory_pair_20260912.py`, and `/tmp/test_astra_varied_memory_pair_20260912.py`. **27/27 local CPU stub tests PASS, zero skips.** No GPU/native execution, network, Git, repository edits, or material recreation. This assistant authored the material and wrapper; these tests are not independent scientific review.

## Main commands

Run from the immutable source CWD. Main supplies actual Unix-float DEADLINE/LEASE_END; six hours remaining never extends the1500s pair. GPU1 is Main's proposed allocation, not allocation performed by this script.

```bash
SOURCE="$HOME/astra_sources/dc2e9a3c11ccd9a3f10ea28513723bbfb8420247"
MATERIAL="$HOME/astra_diagnostics/astra_varied_memory_replay_20260912_attempt1/material"
RUNROOT="${MATERIAL%/material}/fits_root0_attempt1"
PY="$HOME/v2/venv/bin/python"
SCRIPT=/tmp/astra_varied_memory_pair_20260912.py
cd "$SOURCE"
PYTHONDONTWRITEBYTECODE=1 "$PY" -B /tmp/test_astra_varied_memory_pair_20260912.py -v

# CPU plan preparation ONLY; reads/re-audits existing material, never recreates it.
"$PY" -B "$SCRIPT" prepare --source-root "$SOURCE" --materialroot "$MATERIAL" \
  --runroot "$RUNROOT" --device 1 --deadline "$DEADLINE" --lease-end "$LEASE_END"
"$PY" -B "$SCRIPT" verify --source-root "$SOURCE" --runroot "$RUNROOT"

# MAIN ONLY: after full check_free GPU1, UUID reconciliation, and ledger reservation.
# Spawn the controller with this environment from the outset; preserve launch/log receipts.
CUDA_VISIBLE_DEVICES=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1 \
  "$PY" -B "$SCRIPT" run --source-root "$SOURCE" --runroot "$RUNROOT" --allow-gpu
"$PY" -B "$SCRIPT" status --source-root "$SOURCE" --runroot "$RUNROOT"
```

Required unchanged helpers: `/tmp/astra_memory_only_20260912.py` and `/tmp/astra_fading_sentinel_20260912.py`. Alternative locations accepted through `--helper`/`--fading-helper`, but their hashes are enforced. There is no `--seed` flag: root0 only, no later-seed plans/queues or automatic progression.

## Guarantees / boundaries

- Existing material manifest pin `9c6c4bcf00f19e02a62b1939d8f669a16475483b4b74d8718f884830d3118a9c`; adjacent `native_prepare.json` is mandatory. Parent/base paths come from these actual receipts and the original seed0 plan, never guessed. Existing helper pins original plan/fit/dev provenance; full original LoRA state and file inventories are bound. Native callback re-audits the existing128 rows and actual V3 schedules for0/1/2 without writing material.
- SINGLE_VIEW then FOUR_VIEW, each independently warmstarting the SAME original seed0 teaching adapter; fresh optimizer seed0. LR3e-4/r8/alpha16/dropout.05,10epochs/batch4/accum1,320 new/400 cumulative updates. Prepared spans/group/order unchanged, no packing, no actual truncation/splitting. Overflow selector is explicitly `truncate`, matching the material audit; any drops fail.
- Native totals10epochs: SINGLE66160 input/56160 context/10000 target; FOUR67120/57120/10000. Targets/exposure matched, **input compute not matched**; changed batch layout versus SEQ107 forbids a direct dose-only claim.
- Six fresh supervised workers: fit+dev48+exact16 for each arm. **Both arms finish all four raw readout panels before any reduction.** All four capture inventories are rechecked before the first reducer. No outcome-conditioned skip. Reducers audit existing native raw text/tokens; no extra OFF/HF/confirmation calls. Total128 generation calls.
- Pair1500s includes controller CPU, gaps and cleanup; global alarm at effective deadline minus140s. Per-worker ceiling600s (may be shortened by remaining time); no future phase with <=150s remaining. Real lease end separately recorded; effective deadline must equal start+1500 and be <= supplied deadline and real lease end minus10. No internal full-vacancy check that would reject the controller's own reservation: existing native occupancy/supervision is reused. Main maintains continuous CUDA/ledger reservation and performs final full release check externally.
- Fresh output root beside material; only plan+seal written at preparation. `run/` must not exist. Partial failures preserve receipts/artifacts and are `FAILED_PARTIAL_NO_RETRY`, never zeros or automatic resume. COMPLETE requires both reduced arms, all six successful worker receipts, cleanup/accounting and deadline. A reducer failure can leave earlier arm-result files even when terminal arms is empty; they are preserved, not promoted.
- `run/reservation.json`, per-arm `fit-result.json`, `capture-result.json`, `arm-result.json`, native `dev/` and `exact/` trees, and `run/terminal.json` preserve evidence. Terminal reports worker-summed and controller-reserved seconds separately; don't add these overlapping windows. Monetary cost null. Full external launch-to-release accounting remains Main's responsibility.
- Main gate only after BOTH technical COMPLETE: FOUR memory>=15/16 on both dev/exact, dev habit>=30/32 and ACT>=31/32. Then BOTH parent seeds1/2 eligible regardless of SINGLE scores. Gate is declared but not evaluated here. Global ceiling declared3pairs/5400A40seconds (90min), enforced across runs by Main; three1500s bounds consume75min before external audit/release overhead. This root0 script never autoqueues anything.

## Timing plausibility — not completion guarantee

Read selectively from `/tmp/astra_memory_replay_seed0_terminal_20260912/astra_diagnostics/astra_memory_replay_20260912_attempt1/seed0/run/`; eight selected receipts matched the adjacent capsule validation inventory. No old outputs rescored.

- Prior SEQ107 COMPLETE full launch→release **1062.131771s**; controller954.336828s; supervised workers722.441552s. Two160-update fits91.192894s and86.406707s; four readouts544.841951s; controller nonworker overhead231.895276s.
- Release receipt SHA256 `fe1e7d05d77ac719a5d3d1a6d76b5397bca7c734d21a6293b532c81141f353a8`; terminal SHA256 `1cc5a4fadd65a2db1eb8f62552adfb48b445d73480c0facb5bb1daf0fdeea6ba`; prior plan `70405bfa50486feaa2b000ee8102a1cdf30265bccaf102958d7e3ea17035bbb9`. Full release2026-09-12T20:20:11.129284+00:00.
- Simple2×fit-step scaling forecasts1132s controller /1240s full release. Scaling the old all-memory fit by new input exposure instead forecasts1165s /1273s. Assumptions: comparable readout/load/CPU overhead and approximately linear fit work; different targets/layout/padding, caches and contention can invalidate these forecasts. These are **not measured new timings or guaranteed completion**. No extension/retry/score-dependent skipping if the1500s cap is insufficient.

## Coverage / hashes

Tests explicitly cover both captures before reduction, all four capture rechecks before first reduction, zero-score completion without gating, six-hour versus1500s lease/deadline bounds,140s alarm reserve, <=150s no-worker cutoff, original independent forks,320/400-step/fresh-optimizer/state receipts, native counts/provenance mutations, immutable material preservation, stale paths, partial arm/reducer failure, missing receipts/release, and no seed1/2 autoqueue. Native tests/preparation remain Main's next step.

| File | SHA256 |
|---|---|
| Runner | `b58f65cd482bbd2d762edc030c7967a1ecd004829cf8271c74c15d3ca54bc8c7` |
| Tests | `8c173a2aa18b51d97703e4b806ae5c1c797563b89271ee45c8f572dd8f16648c` |
| Memory helper | `ac7a110bc74724fc592407ced854ad162da275d3de9d9eeeb40c19788416afdb` |
| Fading helper | `7b0686de7b66fcad27a665c0b30054a893af3ee33d053c26fae903fc1ed8af20` |
| Native preparer receipt pin | `d4df1ac1ef1a600d2d4e712b9522b50563e080a640dbe9fed176211e9941f6df` |

Authored diagnostic; `UNRESOLVED_LOCAL_HASHES_ONLY`, not child experience/brain proof/clean lineage. **EDIT-STOP.**
