# New-seed C2 sampling results — September 19, 2026

**Block complete at14:24:35 UTC. Independent raw-outcome recount complete:
all240 metric comparisons agree.** Do not replace unfavorable cells or rerun a seed
because of its outcome. All18 preregistered cells completed.

## Fixed comparison

Sources: frozen Qwen2.5-7B-Instruct base, preserved C2sleep51, preserved
C2sleep117. Each is evaluated without a parent, parameter updates, historical
working context, optimizer or historical RNG. Generation seeds23301/23302,
the original three DEV scenes, original decoder/extractor/novelty mechanism,
and adopted rank8/step15625 judge are unchanged.

Each scene/seed/source spends1,024 actual generated tokens. A source/seed row
therefore spends3,072; each source spends6,144; the whole block spends18,432.
This is an inference budget, not total compute. Historical training costs are
different and are not represented by the equal probe budgets.

| Source | Seed | ACT attempts | THINK events | Distinct scored | Distinct accepted | New pixels | ACTs with no result |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Base | 23301 | 12 | 14 | 55 | 42 | 23 | 0 |
| Base | 23302 | 12 | 12 | 50 | 39 | 25 | 0 |
| C2sleep51 | 23301 | 14 | 16 | 67 | 44 | 28 | 5 |
| C2sleep51 | 23302 | 16 | 19 | 84 | 35 | 29 | 5 |
| C2sleep117 | 23301 | 34 | 35 | 74 | 37 | 15 | 6 |
| C2sleep117 | 23302 | 41 | 42 | 94 | 44 | 23 | 2 |

Zero unique rankless outcomes are reported in all rows. An ACT with no result
is not a rankless scored string or a killed run; it remains an attempt. THINK
and ACT can both contribute strings under the unchanged extraction contract.
The counts deduplicate `(scene, caption_sha256)` within a source/seed and do
not count cached/replayed statuses again. Novelty resets between seeds, so
source totals are sums of seed-local counts, not cross-seed distinct ideas.

## Interpretation, including the negative result

- Sleep51 minus base new pixels: **+5 / +4** in the two new seeds. The direction
  repeats the earlier selected-checkpoint comparison on new sampling seeds.
- Sleep117 minus base: **−8 / −2**. Sleep117 minus sleep51: **−13 / −6**.
- Sleep51 yields79 accepted strings versus base's81, but57 versus48 seed-local
  pixels in total. The improvement is in the operational novelty count, not a
  blanket improvement across every metric.
- Sleep117 yields81 accepted strings and38 seed-local pixels despite168 scored
  strings; base yields81 and48 from105 scored strings. More emitted/scored
  strings do not imply more new accepted ideas.
- Selected historical checkpoints, two new decoding seeds and three exposed
  development scenes are not independent training-lineage replication, held-out
  transfer, a tapering test, or proof that parenting or reflection caused the
  difference. Judge acceptance/semantic novelty is not certified human humor.

## Completion and source evidence

Controller1989482 launched14:04:39 UTC on original ovx4 GPUs2/7. All six
player/judge role units exited with status0; three LOADED and COMPLETE pairs
were validated before BLOCK_COMPLETE. The prior failed CPU-only custody
incarnations remain preserved, and no model ran in them.

- Diagnostic epoch: `4df129caf0a0377ba91feec83923bc972e00b10dab13b5b198594db567689d95`.
- Judge epoch: `216f34224e27a2ced6671026c482041c3e6024aecbabd105341a365d2935268a`.
- Execution: `21df1fcbff9c54358c2474541bd399a2ab2572c58aa73046a255d1d851517d8f`.
- `../operations/SAMPLING_V3_BLOCK_COMPLETE.json`, SHA256
  `eca313b093aa2cfa78a0db0b66eede274444664fbf9d65fe060b42e77f89abc4`.
- `../operations/SAMPLING_V3_FINAL_REPORT.json`, SHA256
  `ef5e514e408a7e28c154bbd74da4fa9e3efe85a203335842709bdc9513d46a03`.
- Preregistration: `../C2_SAMPLING_PREREGISTRATION.md`.
- Independent source/custody review: `../replication_review/V3_FINAL_REVIEW.json`.

The independent accounting workstream reconciled public individual outcomes,
pixel identities, source-state and completion receipts from its14:29:40 UTC
snapshot. All240 comparisons agree;46 CPU tests pass, including authentic-block
checks, and Main independently reran the46 tests. There are99 replayed caption
returns across sources; those remain in the evidence but never count as fresh
discoveries. Raw returned `new_pixel` statuses would incorrectly yield92/61/39
instead of the properly deduplicated48/57/38 seed-local sums. See
`../replication_accounting/README.md` and `../replication_accounting/ACCOUNTING.md`.
Provenance validation checks recorded tensor hashes, not a new tensor reread.
