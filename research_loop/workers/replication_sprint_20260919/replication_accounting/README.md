# Final independent accounting — September 19, 2026

**COMPLETE; independent counters match the deployed runtime report.**
Block completed at **14:24:35 UTC**. The one bounded original-route snapshot
was captured at **14:29:40 UTC**, after Main notified us of early completion.
The interrupted pre-end wait was confirmed absent; it made no remote request.
No experiment was rerun. All work and generated artifacts stay in this directory.

## Result

| Source | Seed | Distinct scored | Distinct accepted | New pixels | Generated tokens |
|---|---:|---:|---:|---:|---:|
| Frozen base | 23301 | 55 | 42 | 23 | 3,072 |
| Frozen base | 23302 | 50 | 39 | 25 | 3,072 |
| C2 sleep51 | 23301 | 67 | 44 | 28 | 3,072 |
| C2 sleep51 | 23302 | 84 | 35 | 29 | 3,072 |
| C2 sleep117 | 23301 | 74 | 37 | 15 | 3,072 |
| C2 sleep117 | 23302 | 94 | 44 | 23 | 3,072 |

All **18 cells** complete at **1,024 tokens each**; **18,432 generated tokens**
overall. No missing, partial, invalid, rankless, or error outcomes in this cut.
`ACCOUNTING.md` reports every scene/seed/source cell, not only aggregate winners.

Every preregistered new-pixel contrast, in seed order 23301 / 23302:

- **sleep51 − base: +5 / +4** (positive in both seeds).
- **sleep117 − base: −8 / −2** (negative in both seeds).
- **sleep51 − sleep117: +13 / +6** (positive in both seeds).

Across-seed sums are **48 / 57 / 38** new pixels for base / sleep51 / sleep117.
These sums combine separate seed-local novelty archives; they are **not** the
cardinality of a cross-seed union. Sleep51 produces more operational new pixels
despite lower acceptance rates than base; later sleep117 does not improve
this endpoint. This is a descriptive result for these selected checkpoints.

## Replay inflation and reconciliation

| Source | Returned scored statuses | Unique scored | Replayed returns | Raw `new_pixel` statuses | Counted new pixels |
|---|---:|---:|---:|---:|---:|
| base | 183 | 105 | 78 | 92 | 48 |
| sleep51 | 161 | 151 | 10 | 61 | 57 |
| sleep117 | 179 | 168 | 11 | 39 | 38 |

No cached-only returns, orphan replays, conflicting records, or duplicated
event copies were observed. **99 replayed caption returns** remain preserved
in the snapshot, but are not counted as fresh discoveries. These are analytic
deduplication decisions, not exclusions from training or changes to raw data.

The independent code does not import the code it checks. It reconciles
**240 numeric/metric comparisons** (10 metrics × 18 cells plus 6 seed rows),
plus source hashes, cell/seed statuses and accounting joins, with **zero
discrepancies** against the deployed `runtime/report_sampling.py`. Its captured
output also equals Main's `operations/SAMPLING_V3_FINAL_REPORT.json` exactly.

## Completion and source provenance

All three arms pass recorded-provenance checks: prepared config hashes,
predeclared registry and source freeze, job identities, LOADED/COMPLETE/
COMPLETION_VERIFIED/block joins, all six cell-object hashes per arm, exact
source checkpoint, and pre/post base/adapter tensor hashes. The recorded
decoder/tokenizer/template/library identity is unchanged. Receipts confirm
frozen parameters, no optimizer, zero parent tokens, zero training updates,
no loaded source context, and the same adopted rank8/step15625 judge epoch.
All six recorded player/judge role exits are successful with exit status zero.

Common base tensor SHA:
`a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992`.

| Source | Adapter tensor-state SHA-256 | Adapter file SHA-256 |
|---|---|---|
| base | none | none |
| sleep51 | `82a988a0ded69ce85723192b366251d21f8ec5fe8466e9ca98202fb09b57ce92` | `3c0622810dd279fb7e3a59be9fcff691585c5b1acaeb5053ae21e26571ed8d30` |
| sleep117 | `351b8148f815b77d6d193c1a44477cec2be03a90296a118584bade3db60099fc` | `740a732dde0ac7f9f2c61ce9e64b4a9e0db118cdb18be46694088fd36dc56f86` |

`ACCOUNTING.json` retains full source sleep/commit commitments. This is
verification of **recorded provenance**, not an independent reread of model
tensors, hardware attestation, or reexecution of the judge.

## Limits

- Selected-checkpoint sampling with two new generation seeds is **not**
  independent training-lineage replication, held-out transfer, a tapering test,
  or evidence isolating LoRA learning from parenting/history.
- These are the same three development scenes and operational judge/novelty
  rule. Acceptance is not certified literal humor; there was no semantic review.
- THINK candidates as well as ACT candidates can score. At the same token
  budget, ACT counts differ: base 24, sleep51 30, sleep117 75; those are not
  equal numbers of opportunities or equal wall/total-compute budgets.
- Generated-token totals exclude prompt, judge, embedding and training compute.
- The 928,515-byte public snapshot projects accounting fields from small source
  receipts; hashes bind the original files, which remain untouched on the node.
  No private panels, raw scalar scores, caption text, keys, journals or weights
  were exported. Nothing was sent to parents.

## Files and reproduction

- `PLAN.json`, `METHOD.md`: pre-outcome selection and independent counting rules.
- `export_public.py`: bounded read-only stdout exporter; original SSH route only.
- `account.py`, `test_account.py`: standalone standard-library audit and CPU tests.
- `PUBLIC_SNAPSHOT_1429.json`, `SOURCE_MANIFEST.json`: public input projection and
  45 source references with raw-file/object/projection hashes.
- `ACCOUNTING.json`, `ACCOUNTING.md`: full results, diagnostics, all cells/signs.
- `TESTS.txt`: final regression and authentic-snapshot test log.

**46 CPU tests pass**, including four checks of this authentic captured block.

From the repository root, all offline:

```bash
python3 -B -m unittest discover -s research_loop/workers/replication_sprint_20260919/replication_accounting -p 'test_*.py' -v
python3 -B research_loop/workers/replication_sprint_20260919/replication_accounting/account.py --snapshot research_loop/workers/replication_sprint_20260919/replication_accounting/PUBLIC_SNAPSHOT_1429.json
```

No runtime/source/service mutation, messages, signals, model calls, launches,
training changes, git commits or pushes were performed by this workstream.
