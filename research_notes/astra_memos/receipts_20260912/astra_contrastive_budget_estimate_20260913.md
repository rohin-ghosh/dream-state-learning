# Contrastive controller budget estimate — 2026-09-13

## Bottom line

Prior completed perception receipts support a **1752–2105 second (29.2–35.1
minute)** estimate for two fits plus twelve cold twelve-call readouts, including
the historical full native verification, cold startup, vacancy checks and normal
release overhead. Mean of the three run-derived projections: **1878 seconds
(31.3 minutes)**. A deliberately slower sensitivity case—slowest observed fit
pair plus twelve copies of the slowest observed readout slot—is **2279 seconds
(38.0 minutes)**.

Thus the existing **2700-second limit looks plausible from completed historical
evidence**, not intrinsically infeasible merely because stage ceilings add to
more than 2700. This is an estimate, not a new permission gate or native node2
measurement. No reduced panel count, timeout increase, helper substitution or
additional profiling code is proposed. Main owns native preparation/execution.

The wrapper arms its main work timer at 2660 seconds, reserving 40 seconds for
cleanup within the 2700-second controller bound. Historical normal cleanup is
already included in the projections; do not add it a second time as measured
work. Headroom to that earlier 2660-second work limit is **555–908 seconds**
for the run-derived projections and **381 seconds** for the slow-slot case.
The separate collection allowance remains 180 seconds, not part of controller
fit/readout time; total declared controller-plus-collection allowance is 2880
seconds, followed by the existing six-hour lease margin.

## Local evidence and custody

Discovery manifest: `/tmp/astra_perception_three_seed_manifest_20260913_attempt2.json`,
SHA256 `63c2a65b17887d163a3c07128b2f87be08c4c0f465813de9cc02001a48fec448`.
All three entries explicitly identify collected local snapshots. Root prefix:
`/data/home/rohing/dream-state/gpu_artifacts_local/perception_fit_20260913/`.

| Seed | Relative snapshot root | Plan SHA256 | Completion SHA256 |
| --- | --- | --- | --- |
| 0 | `seed0_capsule1/perception_fit_20260913_attempt1` | `f5f2315d5fa35029249f77b075943fa2c0a36b2691037a7700b50cefbe48c837` | `fa95be7a6c90b6907260631d77e2161ab93a786ce2f2fe268c71bd2b74aee7d1` |
| 1 | `seed1_capsule1/perception_fit_seed1_20260913_attempt1` | `159a317e546be2981e8ed993b549050b3eda580ae8728c00774736e3cb7d10f9` | `86807587e364602e063fc66578fc7432753f7e4ad7a85f9356952a5beb5036e5` |
| 2 | `seed2_capsule1/perception_fit_seed2_20260913_attempt1` | `96027fc25822e078002d89a5c2ceb78b7f110cfab254f3e4f1958e0c3431a3f6` | `f31854b913275bfca85c1262b43cd576a0a98e7bc5947dfab6b69d2cb457d394` |

The local plan/completion bytes were rehashed against these pins. Stage
`started.json`, `launch.json` and `released.json` receipts were checked against
their available entries in the pinned completion inventory. Controller-start
receipts, which are outside that per-stage inventory, have these observed hashes:

- Seed0: `2f19dddbb053b67d82fa4c7c7198bd2c2dfe8040ee97f25ef7eaf396423688a9`.
- Seed1: `2ada80885f80aca3a249e2543172299428cd06e33c60daaaa6b52d574be2be2b`.
- Seed2: `3402d80df88b99421c856f49940590140aef814e2f2dd028296ac208005bfd77`.

Recovered total durations also agree with
`/tmp/astra_perception_three_seed_custody_20260913.json`, SHA256
`97937e0c290f6123a247061ffc8bd25a23b3aa8d935116fb111ce69467357684`.
No score files, generated response text or training losses were used. This is
timing/custody extraction, not another scientific collection or outcome review.

## Definitions: full verification is included, not wished away

Use **plan stage order**, not the alphabetically sorted completion dictionary.
Let C be `controller_started.json.time`, S_i be each worker's
`started.json.time`, R_i be `released.json.time`, and F be
`capture_complete.json.time`. Set R_0=C.

- Full stage slot: R_i − R_(i−1).
- Pre-start portion: S_i − R_(i−1).
- Worker-through-release portion: R_i − S_i.
- Final parent validation/completion tail: F − R_last.
- Exact reconciliation: sum(full slots) + tail = F − C.

The archived runner executes `verify(..., native=True)` **before** writing each
worker-start receipt. This includes source/prepared-file checks, environment
checks and `probe.model_hashes(model)`, not just a cheap identity check. Therefore
using only worker-start-to-release would omit meaningful work. The pre-start
portion also contains vacancy query, subprocess/Python startup and scheduling;
it is not an isolated measurement of hashing time. The first fit slot additionally
includes the controller's initial full native verification.

Release timestamps occur after owned-group cleanup and the original all-process
GPU query. Worker-through-release includes model loading, actual work, shutdown
and these release costs; it is not a pure training/inference kernel measurement.
`launch.json` has no wall timestamp, so no launch time or pure verification
duration was fabricated from file mtimes. Timestamps are wall-clock receipts,
not a monotonic profiling trace; all observed intervals reconcile positively.

## Recovered completed timings

All times below are seconds, rounded to three decimals. Each old controller had
two cold fits and six independent cold twelve-call readouts: 72 calls total.

| Stage: full slot including verification/release | Seed0 | Seed1 | Seed2 |
| --- | ---: | ---: | ---: |
| fit_absent | 93.287 | 95.936 | 113.350 |
| fit_present | 80.773 | 93.629 | 94.566 |
| OFF__absent | 151.699 | 127.646 | 141.292 |
| OFF__present | 151.575 | 151.759 | 134.593 |
| fitAbsent__absent | 152.727 | 128.959 | 132.458 |
| fitAbsent__present | 172.498 | 134.038 | 128.266 |
| fitPresent__absent | 165.249 | 118.710 | 134.397 |
| fitPresent__present | 171.414 | 119.769 | 113.430 |
| Two-fit subtotal, including initial controller verification | 174.060 | 189.566 | 207.916 |
| Six-readout subtotal | 965.162 | 780.881 | 784.436 |
| Final validation/completion tail | 0.793 | 0.817 | 0.875 |
| Actual controller wall | **1140.015** | **971.265** | **993.227** |

UTC observation windows on September 13, 2026:

- Seed0: 04:06:15.137–04:25:15.153.
- Seed1: 04:18:06.497–04:34:17.762.
- Seed2: 04:18:36.891–04:35:10.118.

They overlap; this is not three measurements of an otherwise identical idle
machine. They are operational samples, not independent statistical uncertainty
bounds or learner-outcome evidence.

Across six fit slots, worker-start-through-release ranged **51.626–83.732 s**
(mean 65.205 s); full fit slots ranged **80.773–113.350 s** (mean 95.257 s).
Across eighteen readouts:

| Component | Minimum | Mean | Maximum |
| --- | ---: | ---: | ---: |
| Pre-start: query + startup + full verification | 15.760 | 20.344 | 34.917 |
| Worker-start through final release | 97.316 | 120.238 | 147.806 |
| Full twelve-call cold readout slot | 113.430 | 140.582 | 172.498 |

## Projection to the unchanged contrastive grid

For each old run use:

`estimated_new = old_two_fit_slots + 2 * old_six_readout_slots + old_final_tail`.

This keeps the two cold fits, doubles OFF readouts from two to four and each
fitted state's readouts from two to four, and carries the repeated verification
and normal cleanup costs with the readouts. It does not assume a shared/warm
engine. There are fourteen workers rather than eight, with 144 calls rather than
72. No concurrency speedup is assumed.

| Timing basis | Projected controller | Minutes | Headroom to 2660 s | Headroom to 2700 s |
| --- | ---: | ---: | ---: | ---: |
| Seed0 observed costs | 2105.178 | 35.09 | 554.822 | 594.822 |
| Seed1 observed costs | 1752.146 | 29.20 | 907.854 | 947.854 |
| Seed2 observed costs | 1777.662 | 29.63 | 882.338 | 922.338 |
| Cross-sample slow-slot sensitivity | 2278.770 | 37.98 | 381.230 | 421.230 |

Slow-slot sensitivity = 207.916 + 12×172.498 + 0.875 seconds. This is deliberately
slow relative to the observed sample, but **not a guaranteed worst-case bound**.
It leaves about 27.2 seconds of additional average overhead per worker across
fourteen workers before the 2660-second work timer. Fit cost inflation matters:
doubling its historical fit-pair allowance gives **2486.686 s**, leaving
173.314 s to 2660; tripling it gives **2694.602 s**, beyond the work timer even
though just below the nominal 2700-second outer bound.

## Transfer limits and existing query evidence

The old seed0 plan binds runner
`f62da57d1a66cd287b72ac8ad8b8724601062813653a63d3dcd6cd8a3b69cd51`;
seed1/2 bind the seed-parameterized runner
`5d646e993408cbf91fd4e2a0657f59b87c0197281d9e451e578a45263bbd09f8`.
All retain 2700/180-second controller/collection bounds and the same pinned
trainer `7bbf165fcb4b8ae3a1180328bcd19f57382c30516daddc95fd61e8a2c749fad7`.
The contrastive wrapper adds helper/source checks and larger authored contexts;
new verification/data/fit cost is not directly measured by the old receipts.
Native cache/storage, hardware, concurrency, CPU startup and query latency on
node2 need not match these prior runs. Different arithmetic/copy panels do not
justify assuming faster generation without timing evidence.

Existing local query profile `/tmp/astra_nvml_xml_profile_20260913.json`, SHA256
`961fd1f78fd18e3ed3f4a55ac1869d6262ab18b70bdb8420008c7c9b1a7ed0ce`,
records one successful original XML query in **4.345 s**, under its unchanged
30-second timeout. It is only one successful query, not a bound. Main separately
reports two L2 stage-boundary 30-second XML timeouts; those operational failures
remain relevant even with ample total controller headroom. No failed-root output
was inspected here. The new grid normally requires 28 pre/post-stage vacancy
queries versus the old grid's 16. Historical query costs are already included
in the slot projection; do not add the one-query measurement again. More query
opportunities can still increase exposure to a rare timeout. No compute-only
replacement or weakening of all-process vacancy is implied.

## Scope and current binding

Wrapper remains frozen at
`aea1b5d84d6d79efa7dbdd43ab8e93bf0483fd4383531eae363cdbb4b7583d55`.
Main's updated protocol was observed at
`cc7e92d8aa3999c2ee619893cf830f2687347a39175149708886c1bf0d820ef5`;
Main should use that current pin in its new native spec, not the older example
pin in the already-frozen wrapper handoff. Neither file was edited here.

Only this memo was created. No new code, permission gate, native/GPU query,
network/Git/repository change, live-root read or scientific outcome analysis.
The smaller **actually observed** envelope is two fits plus six cold readouts
in 971–1140 seconds; it is historical evidence, not a substitute experiment.
Main can retain the declared full grid and use this operational estimate without
mistaking it for guaranteed completion or silently changing the protocol.
