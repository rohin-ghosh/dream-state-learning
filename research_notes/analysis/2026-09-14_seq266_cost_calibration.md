# Measured writer calibration and conditional scale scenarios

September 14, 2026. Supplementary analysis of completed SEQ266; **zero new
model calls, fits or GPU reservations**. This supplies the sprint's cost
forecast with current writer measurements. It does not amend the new
orchestrator's protocols or change existing row, exposure or success targets.

## What was measured

Frozen Qwen2.5-7B, rank8 LoRA, batch4, the SEQ266 source
`7f9d4251ae1ff4c5ff9138adf267d081fffa6331`, two A40s on node3. Same1674 input
rows and2928-update schedule in FULL and loss-off; two trajectory slots plus
one old-memory and one cue/audit slot per update. Trajectory slots include
both12 old and1452 new rows. Numbers below come from saved REFERENCE_MASKS,
DOSE, LOSSES and native RESULT files, without retokenization or model loading.

| Quantity | FULL | Loss-off |
|---|---:|---:|
| Optimizer-loop seconds | 5463.162 | 5478.447 |
| Loop seconds/update | 1.8658 | 1.8711 |
| Whole TRAIN phase seconds | 5585.312 | 5600.709 |
| Phase minus loop seconds | 122.150 | 122.262 |
| Nonpadding input-token presentations | 4,477,997 | 4,477,997 |
| Padded token slots, actual batches | 6,636,656 | 6,636,656 |
| Sequence length min/median/max | 137/418/677 | 137/418/677 |
| Batch padded width min/median/max | 326/565/677 | 326/565/677 |
| Fresh AFTER seconds / calls | 647.024 /960 | 645.363 /932 |

The observed padding fraction is32.53%; FULL's effective nonpadding rate is
819.7tokens/loop-second. These are accounting measures, not kernel throughput
or evidence that changing batching preserves the experiment. Removing new
target labels did not make the control materially cheaper in this pair.
The122.2-second average residual includes non-loop work, not an independently
measured pure model-load time. Baseline costs639.992seconds/944calls. Total
observed native phase allocation is3.644GPU-hours, including the shared
baseline and both readouts; prior collection and external staging are excluded.

## Conditional forecast: keep sequence mix and batch layout unchanged

For N new targets,12 old trajectories, P presentations of every trajectory,
and two trajectory slots per update, the cases below require
`updates = (N + 12) * P / 2`. All listed cases divide exactly; the formula is
not a claim that another writer uses this layout. One memory plus one
cue/audit presentation occurs every update, so their exposure also scales.

Nominal TRAIN seconds = `122.206 + updates * 1.868444`.
Nominal pair GPU-hours = `[2 * (TRAIN seconds + 646.194) + 639.992] / 3600`.
The mean of two observed arm rates is a calibration, **not a confidence
interval, p50/p95 prediction or guaranteed bound**.

| New targets | Presentations | Updates/fit | Nominal hours/fit | Pair GPU-hours | Three paired seeds GPU-hours |
|---|---:|---:|---:|---:|---:|
| 1,000 | 4 | 2,024 | 1.08 | 2.71 | 8.12 |
| 1,000 | 16 | 8,096 | 4.24 | 9.01 | 27.03 |
| 1,452 | 4 | 2,928 | 1.55 | 3.64 | 10.93 |
| 1,452 | 16 | 11,712 | 6.11 | 12.76 | 38.29 |
| 5,000 | 4 | 10,024 | 5.24 | 11.01 | 33.03 |
| 5,000 | 16 | 40,096 | 20.84 | 42.23 | 126.68 |

The three-seed column includes one baseline per pair; reuse across seeds is
not assumed. The1,452×4 row reproduces the completed pair by construction,
not independent forecast validation. With two simultaneous fit GPUs and a
third for baseline, zero queue delay and this same readout, the5,000×16 pair
has an idealized21.02-hour critical path. That is not42.23 hours of elapsed
wall time. Sequential sleeps of one learner cannot be parallelized like
independent seeds. Availability and lease margins come from the current
orchestrator's resource ledger, not this table.

The published launch pack correctly calls5,000 updates a sizing example.
It cannot simultaneously mean16 presentations of5,000 targets under this
inherited two-trajectory-slot schedule. This is arithmetic clarification,
not a request to shrink the corpus or change the chosen exposure.

## Do not extrapolate this to token-rich data without qualification

The largest observed training sequence is677 tokens, even though runtime
context ceilings are larger. The new math/code trajectories can have a very
different length distribution. No A100 writer timing,2048-token fit timing,
new padding layout or corresponding memory envelope was measured here.

For illustration only, replacing every observed batch width with1024 gives
1.81× the padded-token count and3.19× the sum-of-squared-width proxy;2048 gives
3.61× and12.78× respectively. **Neither proxy predicts latency or bounds it**:
implementation, memory, kernels and mixed costs matter. The20.84-hour scenario
must not be quoted as the expected duration for rich2048-token targets.

Use the first authorized representative new fit's measured timing and memory
to refresh the calibration while other W1 collection continues. No additional
serial admission gate is introduced. Historical guards/budgets are not
silently extended to fit the longer forecast. Preserve equivalent schedules
across comparison arms and explicitly budget save/readout, collection and
recovery. The September12 micro-diagnostic forecast remains historical; its
81–95-token training cases do not calibrate this writer or the rich successor.

## Reproduction and validation

Script `2026-09-14_seq266_cost_calibration.py` and selected output
`2026-09-14_seq266_cost_calibration.v2.json` are colocated with this note.
The original `.json` is retained: its slot field was misleadingly called
`new_trajectory_slots_per_update`; V2 correctly calls it
`trajectory_slots_per_update` and adds the executed source ID. Numerical
measurements and scenarios are unchanged. Neither file describes a new run.

```bash
python3 -B research_notes/analysis/2026-09-14_seq266_cost_calibration.py \
  --root gpu_artifacts_local/astra_goal_quality_train_terminal_20260914_attempt2/extracted/astra_goal_quality_train_20260914_attempt2 \
  --output /tmp/seq266_cost_calibration_replay.json
```

Output creation is exclusive; use a new path on rerun. Saved inputs are
SHA-bound. Row/batch counts, four-slot batches, input-token totals, update
counts and exact exposure arithmetic are asserted. The underlying SEQ266
native totals have the released independent result review; this supplementary
forecast is Builder's mechanical calculation, not a separately measured scale
experiment or independent review of new outcomes.
