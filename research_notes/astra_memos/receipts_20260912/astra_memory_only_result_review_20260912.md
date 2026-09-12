# Memory-only continuation: raw result review

2026-09-12. **Raw recount PASS; scientific outcome is seed-dependent acquisition with selective retention, not uniform joint success.**

**Authorship disclosure:** I authored the memory-only runner and collector. This is a separate raw-data recount with independently written CPU scoring/arithmetic checks, not a fresh-author independent audit of my implementation. I did not invoke the runner, collector, existing reducers, GPU, network or Git. Only this report was written for this review.

## Main results

Recounted all **192 new generation calls**: three seeds × (48 dev +16 exact-prefix). Original teach baselines were additionally recounted from their local original raw dev captures, with all original readout-file hashes matched to the new plan's inherited inventories.

| Parent / continuation seed | Prior dev memory | New dev memory | New exact memory | New correct ACT | New PREDICT-before-ACT adherence |
|---|---:|---:|---:|---:|---:|
| 0 | 4/16 | 14/16 | 14/16 | 0/32 | 0/32 |
| 1 | 7/16 | 16/16 | 16/16 | 0/32 | 0/32 |
| 2 | 3/16 | 16/16 | 16/16 | 32/32 | 32/32 |

All96 new memory answers are valid single colors. Dev memory gains over the corresponding original parent are +10, +9 and +13 cases, with no previously correct dev memory case lost. All original parents had correct ACT32/32 and adherence32/32. Seed2's32 new arithmetic response strings are exactly identical to its original parent's strings; seeds0/1 have no valid ACT declarations on any arithmetic case.

The preliminary aggregate counts are correct. Two refinements matter: seed0's equal dev/exact counts do **not** mean identical answers, and seed1 does **not** produce a64-token repetition on every arithmetic case.

### Seed0: two unresolved facts, answer contamination on arithmetic

The two memory mistakes concern the same yellow facts, but their wrong colors swap across prompt surfaces:

| Device / source | Correct source color | Dev answer | Exact-training-prefix answer |
|---|---|---|---|
| device-000 / source-memory-000 | yellow | green | blue |
| device-005 / source-memory-005 | yellow | blue | green |

All other14 facts are correct on both panels. Each panel's answer distribution is red4, blue5, green5, yellow2. On arithmetic prompts, outputs are exactly `green` on16 cases and `blue` on16, each followed by EOS. These are invalid arithmetic-interface responses, not32 valid but numerically incorrect sums. Example: the request to add5 and19 receives `green` rather than the required ACT response.

### Seed1: full measured memory recall, arithmetic interface failure with capped repetition

Both memory panels reproduce all16 source labels, four of each color. Arithmetic outputs are dominated by color sequences, sometimes concatenated or separated by newlines rather than spaces. All32 lack valid ACT/PREDICT declarations.

- **23/32 arithmetic calls end with `finish_reason="length"`, exactly64 output tokens.** The observed output is censored at the configured generation limit; its unbounded continuation is unknown.
- The other9 terminate normally: six output `red\ngreen` (4 tokens), two `red\ngreen\nblue\ngreen` (8 tokens), and one `red 23` (5 tokens).
- The `red 23` response is to “Add9 and14,” whose correct sum is23. It remains an invalid ACT response and is not rescued in scoring. It also illustrates why failed interface adherence does not establish absence of arithmetic information.

There are12 distinct arithmetic output strings. “Color spill/repetition under arithmetic prompts” describes the observed outputs; it is not a diagnosed internal mechanism.

### Seed2: joint success on these fixed panels

All16 memory facts are correct on both surfaces, and all32 arithmetic responses retain the original correct `PREDICT: n\nACT: n` habit. This is a bounded existence demonstration that **one continued adapter** can jointly express these memorized associations and this previously measured behavior at this endpoint. It does not make the recipe reliably successful across seeds: the other two full outcomes remain part of the result.

## What the memory panels actually test

Gold labels were checked against the actual16 source-linked training records; exact-panel source records independently carry the same source IDs/colors. The new subset equals the original seed0/1/2 memory records, including spans, metadata and relative order, not merely an equivalent regenerated corpus.

- Exact panel: `train-memory-000`…`015`, the actual training question prefixes; e.g. “Which color does the log assign to device-000?” (42 native prefix tokens).
- Dev memory panel: `eval-memory-000-0`…`015-0`, the same devices/facts with the existing alternate wording; e.g. “Recall the logged color of device-000.” (41 native prefix tokens in that example).
- Thus dev performance measures transfer across these fixed prompt wordings, **not new facts, new devices, a new fact bank, or held-out factual acquisition**. The two panels are not32 independent facts, and the three optimizer seeds share one16-fact assignment.
- The dev48 panel separately contains32 arithmetic cases. Expected sums were recomputed from the two integers in each raw request, not merely trusted from the stored scorer. Scoring retained strict ACT validity and PREDICT-order requirements.

Original seed0 exact-prefix baseline was4/16. Original seed1/2 exact-prefix baselines were not collected here and must remain unmeasured, not imputed from their dev scores. The new plan also preserves original control dev memory4/16 each and the single OFF dev memory0/16 with16 invalid outputs; these are inherited context, not new matched continuation arms. No new OFF/HF/confirmation calls are present in the192-call workload.

## Training and native-mask receipt audit

All three actual training manifests show rank8/alpha16/dropout0.05, lr3e-4,20 epochs, batch4/grad_accum1, matching parent/optimizer seed, no packing and no second chat wrapper. Each completed80 optimizer steps and80 microbatches, with zero nonfinite batches, zero skipped/no-target items, and zero truncated/split/dropped-token items. There are20 recorded epoch means per seed.

The16 native audit records contain44 input IDs each:42 ignored context positions, then color and EOS. Independently enumerating shifted nonignored labels gives predictor indices41/42 for target positions42/43. Counts are704 input/32 supervised tokens per epoch, hence **14,080 input and640 supervised-token presentations per child**, including320 color and320 EOS targets. The source subset SHA-256 is `758960c4bbfe1ae5328e30a25ebcf767f9d5ab9c3e968fe6c31e5470adca61fd`.

Warm-start receipts show one adapter, a fresh AdamW optimizer with zero initial state entries, no optimizer-state restoration/saving, frozen base and matching phase seed. All392 source-state tensor inventory records equal their initialized records without dtype conversion; all392 final tensor records differ from the corresponding source record. Parent file inventories before/after match the pinned original parent inventories. Parent cumulative80 plus phase80 equals160 in every receipt. Both readout plans bind the same child adapter inventory used in that child's fit result; all included physical adapter metadata hashes match those inventories.

These are independent checks of **stored inventories and native execution receipts**, not a new tensor reload or independent base-freezing measurement. Weight files are excluded from the downloaded capsule, so actual on-node tensor-byte verification remains attributed to native runner/collector checks. No new tokenizer invocation was performed in this review.

Final reported microbatch losses are0.1420638561,0.3040495515 and0.0000849734206; final epoch means are0.4194,0.33124 and0.00011. These losses cover memory color+EOS targets, not arithmetic retention, and are not used to select or reclassify seeds.

## Generation limits and observed token cost

Every raw request uses temperature0, seed20260912 and max_tokens64. Actual token arrays respect the limit. All96 memory responses contain exactly one color token plus EOS; none is capped. The only capped calls are the23 seed1 arithmetic outputs above.

| Seed | Dev output tokens | Exact output tokens | Capped calls /64 |
|---|---:|---:|---:|
| 0 | 96 | 32 | 0 |
| 1 | 1,549 | 32 | 23 |
| 2 | 472 | 32 | 0 |

Raw totals: **8,409 input tokens,2,213 output tokens,192 calls**, against a12,288-token output ceiling. Summed request-to-response generation duration is94.730957894s. These totals independently match stored usage receipts. Token counts, wall/reservation time and billed compute are distinct quantities.

## Release and time accounting

All nine worker supervision receipts report success, exit0, no error and verified owned-group/GPU release. All three controller terminals are COMPLETE within their900s bounds. Launch/terminal/release/XML hashes were checked, and each archived `main_release.xml` contains an empty GPU process list with the launch-bound GPU UUID. This is a historical receipt/XML check, not a live GPU inspection.

| Seed / GPU | Worker-window sum (s) | Whole controller (s) | Launch→observed full release (s) | Full release UTC |
|---|---:|---:|---:|---|
| 0 /3 | 236.004016417 | 345.920862556 | 547.337413 | 19:43:16.859523 |
| 1 /4 | 294.989674357 | 400.144028326 | 555.496743 | 19:43:25.023787 |
| 2 /5 | 254.159410936 | 355.712008997 | 563.758259 | 19:43:33.289955 |
| Aggregate | 785.153101710 | 1,101.776899879 | 1,666.592415 | September12,2026 |

The aggregate observed full reservation is **27.77654025 A40 device-minutes**, below the selected45-minute envelope. Controller time is18.36294833 device-minutes; worker windows total13.08588503. Do not report the worker sum as total reservation. Full-release intervals were independently reproduced by subtracting each launch timestamp from its release timestamp and include the wait for collection/release observation. They are not measurements of continuous GPU busy time. Dollar cost is not established.

Main reports an SSH timeout during collection and no retry. This review verifies the resulting complete receipts/capsule, not the SSH transport incident itself; nothing here turns that timeout into an additional scientific trial.

## Custody and claim disposition

Archive `/tmp/astra_memory_only_terminal_20260912.tgz` independently hashes to `8400de86e541573a73803b8ee821e753d3ba644e8346a13f85f6a26a691b1a0a`. **All501 file hashes** agree among archive contents, `.validation.json`, and extracted files. Prepared plan hash is `0f8d1a3042b92c3c940309f0b909f7ee535c295e3c3fb6197a8d45c4c137ac90`. All six current raw-capture manifests, request/response value seals, plan/reduction bindings and row-level independently recomputed scores match. The original teach baseline readout inventories also match their inherited pins.

**Accept:** greatly improved measured device–color binding under memory-focused continuation, complete on seeds1/2 and14/16 on seed0; seed-dependent loss of the arithmetic response interface on seeds0/1; joint memory/habit retention on seed2 only. Report all three, not only seed2.

**Do not infer:** latent arithmetic loss, a necessary separate adapter, general G1, universal memory/behavior coexistence, a unique interference mechanism, causal isolation of dose versus mixture, new-fact generalization, or H1/H2. The observed color spill motivates a bounded replay question but does not answer it. This review proposes no score changes, retries, new selection rule or implementation change.
