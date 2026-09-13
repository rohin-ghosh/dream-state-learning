# Actual-child lower-LR memory repair: independent terminal audit

**Date:** 2026-09-13 UTC  
**Role:** independent terminal auditor  
**Disposition:** strict exploratory screen **FAIL** (`1/3` seeds pass)  
**Scope:** read-only reduction of three finalized node-2 candidate collections
and their hash-bound historical HIGH/LR0 endpoints. No source, fixture, model,
tokenizer, adapter, job, or GPU state was changed.

## Verdict

Lowering the write learning rate from `1e-4` to `3e-5` removed most, but not
all, of the observed skill interference while retaining substantial direct
memory carriage.

- LOW retained `140/143` items that its historical LR0 parent answered
  correctly. HIGH retained only `98/143`. Thus LOW reduced itemwise losses
  from `45/143` to `3/143` and restored `42/45` items lost by HIGH.
- LOW exact-cue source-faithful recall was `18/30`, versus HIGH `20/30` and
  LR0 `0/30`.
- LOW paraphrase source-faithful recall was `18/30`, versus HIGH `16/30` and
  LR0 `0/30`.
- The generic canary remained `36/36` for LOW, HIGH, and LR0. As before, it
  did not reveal task-skill damage.

This is a favorable retention/acquisition tradeoff, not a successful repair.
Only seed 0 met the frozen screen. Seeds 1 and 2 both missed their exact-memory
floors and respectively lost two and one LR0-correct held items. The complete
three-seed screen is therefore false.

For PCFL v2.2, the result independently supports the already-prospective
choice to try `CAL_LOW` (`3e-5`) first. It does **not** qualify that writer,
select a rate for DEV, or make replay optional. Truthful replay, source-diverse
batches, task-specific retention, and the full PCFL writer gate remain
mandatory.

## 1. Frozen question and custody

The frozen protocol was:

```text
research_notes/astra_memos/
  ASTRA_ACTUAL_MEMORY_RETENTION_REPAIR_2026-09-13.md
SHA-256 122965224f6a72d1fb852a40dd24c02b78c733751337f37513712f0f3b45bbce
```

It required each candidate to restart from the same original Level-1 parent
as its historical pair, reuse the same `14/8/8` admitted child records, run
the same eight passes and fit seed/order, and change only WRITE LR from
`1e-4` to `3e-5`. It permitted comparison only to the named, reused,
noncontemporaneous HIGH and LR0 artifacts.

The three audited collections were:

```text
/localhome/local-rohing/astra_diagnostics/
  memory_lower_lr_seed{0,1,2}_20260913_attempt1_collected/
```

| seed | candidate plan SHA-256 | completion SHA-256 | scores SHA-256 | collection-file SHA-256 |
|---:|---|---|---|---|
| 0 | `898bed1d787bd58a2fa45b98a1ff719652d1f29cc903dd53480768e6d297b500` | `a8e52619d987cb5f4c9c06e9ec6c1782dd51876ce1d31b6bff247840c1aaf2f1` | `03288439ddb4d31db5bdc49bec0e64dd4de3fa22fa1dd8cf18315ab5707234e3` | `dfede87b7036a2ce591784b18d30d4c48993aa2d3c680b6d609e68fbe805b7db` |
| 1 | `b0ad752559d04781d090d3042888d51f8a0ddd2250f509ffa85b512f78f55889` | `bf72001932e8f1568d86b46beb74110280b64ea1bc6e7146ca7c2cd30ac68ca9` | `25fbfafced9e00799efeb16cd7f90d97d35837f3ae44bb90c3c8b37fc01d0ce9` | `38c03d6061c8114a6fc4374f506ea3bb960e98a9a62dbe29e76c4f695e211983` |
| 2 | `597095536f3d23de7bd1833c65ffe516293e6936ebedc5c5a9321580a2d868e7` | `d1b3245cfc51651959c221a6f40a6eea8e5e9c9b0032ddbbd42cf2e3ad67379c` | `511acb2c3a48d21887a2b81cd52d7f2136ca2b7459b79759a901571ebcb145ea` | `354234a88269f6f6f1068bdf603b945d646df95a3499d495f96285c000a5ba5e` |

Direct in-place hashing verified for every seed:

- candidate plan and completion hashes;
- every immutable input snapshot named by the candidate plan;
- every candidate raw response file against its stored response hash;
- the historical plan, completion, collection, and score bindings;
- equality of the original parent identity between candidate and historical
  artifacts; and
- equality of every memory row's source object and target hash across LOW,
  HIGH, and LR0.

The archived candidate runner has SHA-256
`80467204aa7ccb4a1cbf4f8d85c7be4e7347263f98f4f7b8fef5739980fcf413`.
All three score artifacts record native capture custody checked. The manifests
show identical writer configurations and input hashes except for
`lr: 1e-4 -> 3e-5`. Readout was greedy (`temperature=0`, fixed seed `0`).

These checks authenticate the captured comparison. They do not independently
rerun the scorer, inspect the semantic correctness of the upstream world, or
turn a reused historical endpoint into a fresh replication.

After the direct row reduction was complete, its totals were cross-checked
against the separately archived stored-result reducer at
`research_notes/astra_memos/receipts_20260912/`
`astra_memory_lower_lr_analysis_20260913_results.json` (SHA-256
`9fc8b149f78fafebb860be35db9adfb0b2114179e0f9a3075f776d43bba98bfd`).
The panel totals, itemwise losses, screens, and costs agree.

## 2. Memory acquisition

`Source-faithful` below is the artifact's `production_eligible` conjunction,
which equals semantic content correctness in these captures. Target-byte and
strict-canonical results remain separate.

| seed | endpoint | exact source-faithful | exact bytes | exact strict | paraphrase source-faithful | paraphrase bytes | paraphrase strict |
|---:|---|---:|---:|---:|---:|---:|---:|
| 0 | LOW | 10/14 | 8/14 | 8/14 | 10/14 | 8/14 | 2/14 |
| 0 | HIGH | 8/14 | 7/14 | 3/14 | 6/14 | 4/14 | 0/14 |
| 0 | LR0 | 0/14 | 0/14 | 0/14 | 0/14 | 0/14 | 0/14 |
| 1 | LOW | 4/8 | 4/8 | 0/8 | 5/8 | 5/8 | 0/8 |
| 1 | HIGH | 7/8 | 7/8 | 0/8 | 5/8 | 5/8 | 0/8 |
| 1 | LR0 | 0/8 | 0/8 | 0/8 | 0/8 | 0/8 | 0/8 |
| 2 | LOW | 4/8 | 4/8 | 0/8 | 3/8 | 3/8 | 0/8 |
| 2 | HIGH | 5/8 | 5/8 | 0/8 | 5/8 | 5/8 | 0/8 |
| 2 | LR0 | 0/8 | 0/8 | 0/8 | 0/8 | 0/8 | 0/8 |
| **pooled** | **LOW** | **18/30** | **16/30** | **8/30** | **18/30** | **16/30** | **2/30** |
| **pooled** | **HIGH** | **20/30** | **19/30** | **3/30** | **16/30** | **14/30** | **0/30** |
| **pooled** | **LR0** | **0/30** | **0/30** | **0/30** | **0/30** | **0/30** | **0/30** |

LOW is not merely a uniformly weaker version of HIGH. Itemwise, exact recall
has 16 shared successes, two LOW-only successes, and four HIGH-only successes.
Paraphrase recall has 12 shared, six LOW-only, and four HIGH-only successes.
Changing heat changed which records were accessible, not only their aggregate
strength.

The 30 rows are not 30 independent memories. They contain only 14 distinct
within-seed target strings, with repeated occurrences. Requiring every
occurrence of a target to be correct gives:

| endpoint | exact robust target types | paraphrase robust target types |
|---|---:|---:|
| LOW | 5/14 | 6/14 |
| HIGH | 7/14 | 6/14 |
| LR0 | 0/14 | 0/14 |

LOW exact generations also had only `3/2/1` unique raw outputs across seeds
0/1/2 despite `4/5/5` target types. Seed 2 therefore emitted one exact output
for five addressed targets. Lower heat preserved more of the inherited skill,
but it did not produce a complete conditional episodic map.

## 3. Itemwise retention

| seed | LR0 held | HIGH held | LOW held | HIGH losses among LR0-correct | LOW losses among LR0-correct | canary, all endpoints |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 47/48 | 44/48 | 47/48 | 3/47 | 0/47 | 12/12 |
| 1 | 48/48 | 37/48 | 46/48 | 11/48 | 2/48 | 12/12 |
| 2 | 48/48 | 17/48 | 47/48 | 31/48 | 1/48 | 12/12 |
| **pooled** | **143/144** | **98/144** | **140/144** | **45/143** | **3/143** | **36/36** |

There were no gains over LR0 to offset losses. LOW restored every HIGH-lost
item except these three:

```text
seed1 perception:a3487a82a4eba508a231505ebda20e8d3b8b26a2ef4bafeea5c404f8596a32ac
seed1 perception:3168de3a2773da0af3a9c7a43586a1838565eb04d29b6add6ce43cab4e29cb65
seed2 perception:7a60a5144c25523d53a4b484937897020d9639c96cbad37c44601f15b36b5ca4
```

The generic canary again provides no evidence of skill preservation: it is
perfect for both a writer that loses `45/143` skill items and one that loses
`3/143`.

## 4. Frozen exploratory screen

The protocol required, **for every seed**:

1. exact source-faithful recall at least the corresponding HIGH result
   (`8/14`, `7/8`, `5/8`); and
2. zero losses among every LR0-correct held or canary item.

| seed | exact requirement | LOW exact | held losses | canary losses | result |
|---:|---:|---:|---:|---:|---|
| 0 | >=8/14 | 10/14 | 0 | 0 | **MET** |
| 1 | >=7/8 | 4/8 | 2 | 0 | **NOT MET** |
| 2 | >=5/8 | 4/8 | 1 | 0 | **NOT MET** |

The all-seed screen fails. Paraphrase improvement, aggregate retention, and
restoring 42 old failures cannot compensate for either noncompensatory
condition. The artifacts correctly record `automatic_pass=false` and
`scientific_pass=null`; this audit does not override them.

## 5. Dose and measured cost

All candidates used the original rank-8, alpha-16, dropout-`.05`, all-layer
adapter, one admitted row per batch, eight passes, the original fit seed, and
the exact source-withdrawn child-record targets.

| seed | rows | updates | LOW final loss | LOW parameter-delta L2 | HIGH parameter-delta L2 | fit train / wall seconds | calls |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 14 | 112 | .044026 | 1.811951 | 3.920665 | 43.0 / 48.9 | 88 |
| 1 | 8 | 64 | .131284 | 1.573681 | 3.589591 | 23.6 / 37.4 | 76 |
| 2 | 8 | 64 | .028906 | 1.419358 | 3.179680 | 18.7 / 29.4 | 76 |

Total new candidate work was:

- `240` optimizer updates and `240` cold calls;
- `6,776` supervised target-token presentations and `41,608` total padded
  training-token presentations;
- `55,799` readout prompt tokens and `5,052` output tokens;
- `85.3` summed fit-training seconds, `115.7` summed fit wall seconds, and
  `211.406` summed generation seconds; and
- `714.615` summed controller elapsed seconds.

Time totals are sums across independently scheduled jobs, not concurrent
makespan. The historical HIGH/LR0 artifacts added zero new calls or updates to
this candidate experiment.

LOW's parameter displacement is smaller in all three seeds and retention is
better in all three. That is consistent with lower heat reducing interference.
It does not establish parameter-delta norm as the mediator: learning rate
changes the entire optimization path, and final loss is not monotone with
either recall or retention.

## 6. Consequence for PCFL v2.2

The correct update to the PCFL decision is narrow:

1. **Keep LOW first.** This is the first direct own-record comparison showing
   that `3e-5` can retain much of the acquisition while sharply reducing
   interference. It strengthens, but does not retrospectively select, the
   prospective `CAL_LOW` ordering.
2. **Do not qualify LOW from this assay.** PCFL uses a different parent state,
   corpus (`20` slots with eight wrappers), batch construction, `200` updates,
   source-diverse scheduling, addressed EVENT/LINK semantics, and native task
   endpoint. Its own writer gate must decide.
3. **Replay remains mandatory.** LOW alone failed two of three strict screens,
   lost three inherited-skill items, and retained exact robust access to only
   `5/14` distinct target types. The result rules out “lower LR alone is the
   repair.” It does not prove that replay will repair the failure or choose a
   replay ratio; that remains a prospective PCFL test.
4. **Keep task-specific retention noncompensatory.** The generic canary was
   perfect throughout. PCFL's frozen 64-request `NATIVE_CONTEXT` retention
   panel and itemwise loss limits are required before accepting a write.
5. **Keep HIGH conditional and conceptually distinct.** PCFL's fallback is
   `3e-4`; the historical endpoint here is `1e-4`. This assay neither validates
   nor invalidates that fallback.

## 7. Causal self-attack and claim boundary

The narrow heat comparison is unusually clean for an exploratory diagnostic:
same parent, rows, masks, steps, fit seed/order, adapter topology, and greedy
readout; only the learning rate differs. Still, the following prevent a
broader causal or paper claim:

- HIGH and LR0 are reused, noncontemporaneous observations rather than fresh
  replications. Their hashes and environment identities are bound, but this
  remains three learner/optimizer seeds.
- The held panel was inspected to define and judge the repair; it is no longer
  fresh confirmation evidence.
- Row totals overstate independent breadth because 30 admitted rows contain
  only 14 within-seed target strings.
- The test asks for direct source-withdrawn records. It does not test whether
  an agent spontaneously retrieves them, traverses a connected graph, chooses
  a better experiment, or improves later action.
- The candidates warm-start from a researcher-authored Level-1 skill adapter.
  They are not a complete SLEEP cycle, a clean-base PCFL write, recurrence,
  retention across multiple sleeps, or an autonomous lifetime.
- No replay arm was run. “Replay remains mandatory” is a design consequence
  of incomplete repair plus the already-frozen PCFL protocol, not an empirical
  claim that the chosen replay mechanism works.

The defensible conclusion is therefore:

> On these three bound actual-child record fits, reducing LR from `1e-4` to
> `3e-5` preserved 42 of the 45 LR0-correct skill items erased by the higher
> rate while retaining partial exact and paraphrased parametric recall. It
> failed the preregistered all-seed repair screen, so lower heat is a promising
> first writer setting, not a sufficient safe-write mechanism.
