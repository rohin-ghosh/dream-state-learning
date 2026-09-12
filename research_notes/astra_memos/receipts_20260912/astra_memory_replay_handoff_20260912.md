# Memory replay pair — EDIT-STOP

2026-09-12. Implements Main's confirmed19:52UTC design. **Ready for Main's native validation/preparation; not launched.** Only the three assigned runner/test/handoff files were written. No repository/Git/network/GPU/model actions; existing helpers and artifacts remain unchanged. This is an author-side implementation/test handoff, not an independent scientific audit.

## Files and CPU result

- `/tmp/astra_memory_replay_20260912.py` — SHA256 `1586ddf7d690ce8bc55d680bd926439fbd597236ea8e76394f88a3bdf023c8bc`.
- `/tmp/test_astra_memory_replay_20260912.py` — SHA256 `25f659b9a9dec1c1304f44468155b0ae7f6a173782395ac4d0dece60698e8729`.
- Local AST parse passed; **22 CPU fixture tests PASS**, including actual native pure-Python encoding/config parsing with a synthetic tokenizer. Fixtures mock filesystem writes, model/state loading, worker supervision, signals and GPU occupancy; they do not certify actual native tokenizer counts or GPU completion.

Read-only dependencies: accepted `/tmp/astra_memory_only_20260912.py` SHA256 `ac7a110bc74724fc592407ced854ad162da275d3de9d9eeeb40c19788416afdb`; accepted `/tmp/astra_fading_sentinel_20260912.py` SHA256 `7b0686de7b66fcad27a665c0b30054a893af3ee33d053c26fae903fc1ed8af20`. Both pins are enforced transitively. Main's native source is `~/astra_sources/3a12807f88747bafd0aada1d4a09ba88b915f903`; preparation seals actual imported source hashes, then execution checks them. No helper modifications or new collector are required.

## Fixed execution and accounting

One pair = **MIXED then ALL_MEMORY**, sequentially on one sealed device. Both independently fork the same original teach adapter; never mixed→all-memory and never SEQ105→child. Fresh seed-matched optimizer, one full loaded adapter, r8/alpha16/dropout.05, LR3e-4/batch4/grad_accum1, no packing, max_len512, unchanged native masks/EOS/rendering. Original parent80 + new160 = **240 cumulative** per child.

| Arm | Rows | Epochs | New updates | Native input/epoch | Native target/epoch | Input presentations | Target presentations |
|---|---:|---:|---:|---:|---:|---:|---:|
| MIXED |32|20|160|1,654|250|33,080|5,000|
| ALL_MEMORY |16|40|160|704|32|28,160|1,280|

Arithmetic selection is exactly the first16 addition IDs in source-list order: `011,039,055,029,048,000,052,017,036,046,063,019,057,030,012,015` (prefix `train-addition-`). Selected union with all16 memory rows preserves the original overall order and complete records, including spans/meta/order/source IDs. Preparation checks original pinned corpus/parent provenance and reproduces per-row native input/target counts and original nested-batch label hashes. No new facts or readout-derived training material.

Every completed arm runs **dev48 then exact16**, using the existing separate modules/capture directories. Scores do not control either panel or the second arm. Inherited generation settings remain temperature0, seed20260912, max64 output tokens/call; no new OFF/HF/confirmation. Two arms produce128 calls, 8,192 maximum output tokens; actual outputs and token use must be reported. Technical failure stops with partial evidence, not a fabricated zero score or a retry.

Controller1200s includes import/startup, in-controller CPU work, six workers and cleanup, with140s reserved for cleanup; existing workers retain600s maximum each, further limited by the remaining pair window. Standalone prepare time/external allocation and final full-release observation are **not** counted as controller runtime and belong in Main's aggregate occupancy ledger. Three1200s pair ceilings =60 A40 minutes, leaving30 minutes of the confirmed90-minute envelope for external overhead/margin. Neither completion nor the external90-minute cap is guaranteed/enforced by this one-pair script. It seals the envelope for provenance; Main owns allocation/ledger/full release.

## Main-only commands

Run tests from the frozen source directory so imports bind to that source (the test uses `Path.cwd()`). These commands are instructions only; no native command was executed here.

```bash
SOURCE="$HOME/astra_sources/3a12807f88747bafd0aada1d4a09ba88b915f903"
# With current directory set to "$SOURCE":
PYTHONDONTWRITEBYTECODE=1 python3 -B /tmp/test_astra_memory_replay_20260912.py

# Main sets DEVICE (single ID), DEADLINE and LEASE_END (Unix seconds),
# and a fresh absolute ROOT; DEADLINE must cover launch +1200s,
# LEASE_END must cover launch +1210s. Prepare does not reserve/launch.
PARENT="$HOME/astra_diagnostics/astra_fundamental_teaching_20260912_attempt1"
PYTHONDONTWRITEBYTECODE=1 python3 -B /tmp/astra_memory_replay_20260912.py prepare \
  --source-root "$SOURCE" --parentroot "$PARENT" --seed 0 --device "$DEVICE" \
  --deadline "$DEADLINE" --lease-end "$LEASE_END" --runroot "$ROOT"

# Only after Main's native acceptance/provenance/budget log and allocation:
CUDA_VISIBLE_DEVICES="$DEVICE" PYTHONDONTWRITEBYTECODE=1 \
  python3 -B /tmp/astra_memory_replay_20260912.py run \
  --source-root "$SOURCE" --runroot "$ROOT" --allow-gpu

PYTHONDONTWRITEBYTECODE=1 python3 -B /tmp/astra_memory_replay_20260912.py status \
  --source-root "$SOURCE" --runroot "$ROOT"
```

Later eligible seed1/2 parents are `~/astra_diagnostics/astra_fundamental_replications_20260912_attempt1/seed1` and `/seed2`, with their matching seed and a new root/device/deadline selected by Main. This script does not discover devices, schedule seeds, or authorize progression. `status` reads sealed plan/terminal without scoring or resuming; a nonterminal root is not proof that its controller is still alive.

## Minimal native acceptance

1. Main runs22 tests under frozen source and native CPU prepare. Inspect sealed original parent identity/baseline, masks/counts, two distinct output paths from that same parent, seed/device, both readout templates and source/material pins. Native counts must exactly match the table; no patching/tuning to force agreement.
2. Both child manifests must report160 steps/microbatches,20/40 epochs,240 cumulative, exact input/target accounting, no split/truncation/nonfinite/empty fit, fresh optimizer and full float32 initialized-state equality. Preserve all serialized state receipts and unchanged original parent/base inventories.
3. Expect `ROOT/run/{mixed,all_memory}/adapter`, `fit-worker/supervision.json`, `fit-result.json`, `dev/run/data/calls`, `exact/run/data/calls`, separate reductions and `arm-result.json`. Pair reservation/terminal live at `ROOT/run/reservation.json` and `terminal.json`. COMPLETE requires both arms, six successful worker receipts, accounted owned processes, verified GPU process absence and deadline compliance. Main separately performs full-device release/lease checks and preserves evidence; controller process absence is not a substitute for fullcheck_free.
4. Never re-run an existing `run` root or overwrite evidence. A failed/abandoned pair is `FAILED_PARTIAL_NO_RETRY` (or nonterminal after an uncatchable kill); retain any first-arm result, second-arm partial files and all raw captures. Do not skip the comparator because MIXED scores are poor, shorten epochs, alter generation caps or retry selectively.
5. **ROOT0 first; Main decides only after BOTH arms are terminal and technically valid.** Progress to BOTH roots1/2 only if seed0 MIXED dev memory≥15/16, exact memory≥15/16, adherence≥30/32 and ACT≥31/32. No comparator gate; no seed1-based decision to skip seed2. Retain/report all attempted arms and unrun roots. Technical failure is not a scientific zero.

## Claim boundary

Primary comparison: fixed-update allocation to arithmetic replay versus all-memory practice, **not** a pure replay effect at equal memory exposure or equal compute/loss mass. SEQ105 memory-only80 is only an inherited equal-memory-exposure anchor for MIXED160, with a different update-budget estimand. Native input/target presentations, actual generation lengths, fit/worker/controller times and full-device occupancy remain separate quantities. No inference about latent arithmetic loss, necessity of separate adapters, general G1 or selected best seeds.

**EDIT-STOP. Main owns native validation, preparation, logging, allocation, launch, progression and final release/evidence collection.**
