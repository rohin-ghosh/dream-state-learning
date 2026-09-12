# Actual-record path: measured costs — 2026-09-12

**Measured total: 20.933 A40-minutes of launch-to-observed-full-release reservation, not ~13 minutes.** The latter is the **12.729-minute supervised-worker subtotal**. This is one P/A formation comparison, two independently written recipients, and three fresh readout cells—not a measured adult sequential learning cycle. Advisory cost synthesis only; no outcomes re-scored, models loaded, native code executed, or resource availability inferred.

## Executed work and tokens

Frozen Qwen2.5-7B-Instruct; source `610c6edd05ce9c85720ee6e992889badecc2c158`. Each write trains **20,185,088 LoRA parameters**: rank8/alpha16/dropout0.05, seven projections across28 layers, fresh base/seed2/AdamW LR1e-4, batch2,12epochs/12updates, no packing/splits/drops. Training config bf16; saved adapters F32. Formation/readout have no parameter updates.

| Phase/cell | Actual calls / ceiling | Native input / output tokens | Actual update-target presentations | Generation / training-loop seconds |
|---|---:|---:|---:|---:|
| SEQ110 formation P+A | 60/60 | 23,811 / 1,379 | 0 | 41.373 / — |
| SEQ111 P write | 0; 12/12 updates | 7,656 input presentations / no generation | 888 | — / 8.3 |
| SEQ111 A write | 0; 12/12 updates | 7,632 input presentations / no generation | 888 | — / 8.4 |
| SEQ112 OFF | 32/32 | 11,296 / 677 | 0 | 20.350 / — |
| SEQ112 P_ON | 29/32 | 10,107 / 634 | 0 | 26.643 / — |
| SEQ112 A_ON | 29/32 | 10,107 / 634 | 0 | 26.556 / — |

Formation:40wake+12record+4parent+4restate calls;18,480 allowed output tokens. Readout:56wake+34record=**90, not96**,25,800 executed-call output allowance versus27,600 all-slot ceiling. These are allowances, not token consumption. Combined generations:150calls,55,321input/3,324output tokens. No missing calls imputed.

Each fit uses two original rows: P lengths320/318, A319/317. Per epoch P638input/74target, A636/74; targets include EOS. Pair totals:15,288 unpadded input and1,776 target presentations over24updates;15,336 padded input positions. These are repeated training exposures, not new generation tokens. Rounded trainer-function walls8.9/9.0s exceed the8.3/8.4s loops; no per-update latency distribution is archived.

## Clocks, latency and storage

| Phase | Workers s | Controller s | Full reservation s (A40-min) | Collection wall s |
|---|---:|---:|---:|---:|
| Formation | 116.096 | unavailable | 251.917 (4.199) | 26.147 |
| Paired writes | 153.654 | 230.666 | 361.168 (6.019) | 22.495 |
| Three readouts | 493.982 | 595.137 | 642.894 (10.715) | 53.983 |

Worker intervals nest inside controllers/full reservation; generation nests inside workers. **Do not add columns.** Collection overlaps reservation and includes post-release work. Full reservation includes CPU gaps, cleanup and waiting for observation; it is not device-active time. All three recorded full releases pass; UTC21:16:18.781,21:36:38.820,21:50:03.514. Interphase calendar gaps are not automatically charged. P/A workers73.852/79.803s; OFF/P/A161.670/169.067/163.245s. Caps:600s/worker; writes1200s/readout1800s controller including140s cleanup. Formation's legacy1800s aggregate-worker allowance **is not a full-controller guarantee**.

Empirical request-start→response-end latency, seconds; type-7 linear p50/p95, not run-level or future percentiles:

| Calls | n | p50 / p95 |
|---|---:|---:|
| Formation pooled; wake | 60;40 | 0.483/1.622; 0.351/0.495 |
| Formation record; parent; restate | 12;4;4 | 1.088/1.123; 1.868/2.548; 1.090/2.435 |
| Readout pooled | 90 | 0.679/1.531 |
| Readout OFF; P_ON; A_ON | 32;29;29 | 0.484/1.103; 0.687/1.556; 0.682/1.531 |

Fresh process→backend-ready: formation37.926s; OFF/P/A76.170/79.738/74.496s. These include imports/checks/load, not just loading or demonstrably cold filesystem cache. vLLM model-loading substage3.121–3.166s, engine init/profile/KV/warmup3.46–3.74s; do not double-count components. Fit HF progress displays ~3s loading, not complete fit startup. No prefill/decode split or HF scoring profile here.

Each adapter:392tensors, **80,740,352 payload bytes (77MiB)**; pair154MiB. Full safetensors file bytes including headers are not established by these receipts. Base checkpoint log14.19GiB is rounded; exact bytes unavailable here. Logged14.29–14.44GiB model GPU memory is not disk size. Metadata capsules:141/47/232files,62,478/101,579/90,126compressed bytes, respectively; weights excluded. Separate saved-weight CPU audit12.853s is not GPU reservation.

## Conditional next-work forecast—not a scaling claim

- **Three additional paired seeds**, fixed archived material, fresh OFF/P/A per pair:6fits/72updates/9readout processes. Linear observed-charge proxy **50.20 A40-min**. If each also requires fresh formation, add12.60→**62.80min**. Those are analogs, not lower guarantees or empirical p95s. For fit+readout only, reusing1200+1800s controller ceilings and prospectively allocating300s external collection per stage yields a **180min three-pair ceiling**, conditional on enforced bounds/cleanup; no formation-controller bound is established.
- **One process-distillation pair**, if archived examples qualify:2fresh fits/24updates plus fresh OFF/P/A; no formation calls. Native transformed input/target lengths remain unknown. Record-path analog16.73min; more honestly **16.456min + new paired training-loop seconds/60**, holding other observed costs fixed. Longer contexts/targets can also change nontraining and readout costs. A prospective1200+1800+2×300s envelope is60min, not a success prediction; do not claim token/compute matching or invented batching speedups.

Dominant observed costs are outside generation/training loops:114.922s generation+16.7s training versus1,255.979s full charge. Readout startup alone230.404s; remaining worker time beyond startup/generation190.029s is unseparated. Write workers exceed trainer-function wall by135.754s. Next minimal profile: monotonic spans for verification, imports, load, encode, train/prefill/decode, save, cleanup and collection wait, plus native process-row lengths/padding. No evidence here that current parents learn more; the question remains **actual process write and subsequent use**.

Custody: cost-only script rechecked all420 extracted inventory hashes and capsule SHAs: SEQ110 `05b9177bb83e800f4f9c10bbc5e34c27c7dd68e2fabe9c18c006c12e6971f90e`; SEQ111 `26243e9a6436a859f7ed7a6ec1250a9e3a06496ec61c8eb3f85afe4d1ea308b4`; SEQ112 `f8f2bb688da189ebb8f70c67725f1c008db49d6c5b2800abdc58a0dd4fcb7458`. Exact costs/call rows/role percentiles in sibling `.json`; readout costs agree with prior raw analysis and Main's memo. Authored earlier formation/write collectors and weight audit; not a fresh-author audit. **EDIT-STOP.**
