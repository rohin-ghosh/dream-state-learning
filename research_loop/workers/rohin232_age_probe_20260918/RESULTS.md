# R232 first fixed-token age probe — completed September18,2026

Final observation: **10:43:18.430207UTC**. All18 scene/seed/model cells completed;
each model generated exactly6144 tokens. Original lives were neither stopped
nor written to. These were separate frozen inference probes, not new learners.

## Matched primary comparison and base reference

| Frozen condition | Absolute sleep / optimizer steps | Actual child tokens | Newly scored strings | Accepted strings | New-pixel events | Accepted repeats | Pixels by paired seed |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| C2 source51 | 51 / 4908 | 6144 | 215 | 71 | 40 | 31 | 24,16 |
| C2 current capture | 87 / 6348 | 6144 | 179 | 50 | 25 | 25 | 14,11 |
| Plain frozen base | no adapter / no optimizer | 6144 | 144 | 79 | 58 | 21 | 25,33 |

The primary source51/current-C2 comparison is36 completed sleeps and1440
optimizer updates apart. Absolute training token exposure and training duration
are unknown here, explicitly null in the source metadata. Source51 is relative
age0 for this comparison, not a claim of zero prior learning.

**Observed result:** current C2 produced fewer raw accepted strings and new-pixel
events than source51 at this fixed generated-token budget. This small diagnostic
does not show improvement on that metric. It is not a causal age-only result,
retention claim, H2 result, or evidence that the base is objectively funnier.

Denominators: three fresh agent-DEVELOPMENT cartoons × two paired stochastic
seeds ×1024 actual generated tokens. Each seed totals3072 tokens across scenes.
Pixel totals sum events in two independent seed archives; they are **not** a
globally deduplicated count of novel ideas. All scored strings above were new
score requests; cache counts were0. Accepted repeats meet rank/relevance but
do not increase novelty. Rank is within64 private development references plus
the candidate, not a global contest rank or vote probability.

## Controlled inputs and token accounting

- All six initial scene/seed context hashes match across the three conditions.
  No source working state, Rohin transcript, seed examples, parent, or prior
  probe history enters those fresh contexts. Within a cell, only that model's
  own generated responses and actual public scoring feedback accumulate.
- Common decoder: temperature0.8, top_p0.95, top_k0, repetition_penalty1.0;
  paired seeds23201/23202. EOS counts as an actual generated token. Early EOS
  permits further attempts within the remaining budget; the last request is
  capped exactly at the remaining tokens. No early-stopped cells or pending
  score requests remain.
- Source51: THINK3322 + ACT2822. Current C2: THINK3224 + ACT2920.
  Base: THINK2995 + ACT3149. LEARN and other reply generation are0 because
  this evaluation has no such stages. Parent tokens and optimizer updates are0.
- Input/prompt tokens are separately92306,194560,61931 respectively. Thus this
  is matched **generated-token** budget, not matched total inference compute,
  prompt-token count, number of turns, or number of proposed strings. Variable
  early EOS and feedback lengths explain different invocation/input costs;
  no input tokens are silently counted as child generation.
- `RESULTS.json` retains response-bound cumulative coverage and marginal
  discovery in256-token bins for each seed. Every response's full generated
  token count is charged before any score from that response is credited.
  Final base and adapter tensor hashes match actual LOADED hashes for all arms.

## Freshness, scorer, and claim limits

Scenes564/654/703 were chosen in original packet order after excluding known
exposures, the existing game scenes, and their entire near-duplicate scene
groups. Eligibility is agent-development only, disjoint from sealed/FINAL and
judge pools. Source exposure checks covered300 lifetime REQUESTs and both
inherited completed-source contexts: zero selected identifiers/image hashes
and zero shared description fivegrams. This is recorded-exposure evidence,
not proof of unseen base pretraining or exhaustive semantic-paraphrase detection.

All conditions use the same factual descriptions from pinned local Qwen2.5-VL,
same frozen widegap6250 scorer, top50, relevance threshold and embedding-pixel
rules. The fixed new-scene reference-panel hash is
`4adab198a81f2492fff5471d0a7a20de41c06f59c7a492d7ef35746f84d346aa`.
Reference caption bytes/ratings remain private to the scorer and are not pushed.
Model-generated factual descriptions and the provisional judge can be wrong.

Raw acceptance remains a scoring statistic, not literal-caption or humor
certification. A deterministic prefix spot-check inspected3 accepted spans per
condition:9/200 accepted strings are verified literal caption attempts;191/200
remain unreviewed. None is certified funny. Hash-bound review is
`SPOT_REVIEW.json`; `SPOT_REVIEW_BINDINGS.json` verifies exact generation hashes,
raw character spans, and immutable scorer receipts for all9. It does not rescore
or alter eligibility. Parser behavior,
small scene count, stochastic seeds, source training history/policies and the
provisional novelty model limit generalization.

## Actual runtime and preservation

| Process | GPU | PID | Actual LOADED UTC | Completed UTC |
| --- | --- | ---: | --- | --- |
| Source51 frozen probe | ovx4:4 | 91249 | 10:36:32.553400 | 10:42:05.295099 |
| Current-C2 frozen probe | ovx4:5 | 91298 | 10:36:33.269329 | 10:42:44.371515 |
| Plain-base frozen probe | ovx4:6 | 91387 | 10:36:34.186530 | 10:41:06.752595 |
| Shared finite judge | ovx4:7 | 91158 | 10:35:57.816430 | 10:42:44.473259 |

First measured finish estimate was10:42–10:43UTC; actual matched completion is
10:42:44UTC including final tensor verification. At10:43:19UTC all four assigned
GPUs were empty after normal finite completion, not crashes. Existing scorer
PIDs47039/60494 on2/3 remained present. This worker never controlled Cicero's0/1.
Source C2 PID3624513 was reverified alive at10:38:41UTC, with both captured source
checkpoints still unchanged. No source-life or existing-scorer signals occurred.

Hourly reporter218252 and publisher356029 remained live at the final check.
Main owns the armed P3 renewal supervisor2002133; renewal activation at11:07
is not claimed by this earlier cut. C0 coherent sleep81/5660 handoff68514151a
is acknowledged and remains undispatched. Fresh-birth/C0 age slots0,1,2,4,8,16,32
remain planned extensions, not completed measurements.

Nine focused CPU tests pass. Receiving import/decoder smoke passed; receiving
pytest is absent and is not claimed. Runtime source/Builder receipts were
pushed before probes; `SOURCE_REVERIFIED.json` binds the native record encoding
and original immutable file hashes. No live cached source was hotpatched.
