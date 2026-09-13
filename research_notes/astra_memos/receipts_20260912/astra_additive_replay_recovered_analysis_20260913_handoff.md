# Recovery-aware additive reducer — EDITSTOP, PRE-OUTCOME

2026-09-13. Runnable collection-recovery adapter ready for Main CPU review.
The verified current mirror and archive have NOT been opened by this author.
No real cohort reduction, native/model/network work, collection, Git or repo edits.
Await Main CPU tests and explicit authorization before the one local reduction.

## Owned files and validation

- `/tmp/astra_additive_replay_recovered_analysis_20260913.py`
  SHA256 `8a35836aa22267d6199feed676a162c7018e5960a396370cd4f83bb2cc45e63d`
- `/tmp/test_astra_additive_replay_recovered_analysis_20260913.py`
  SHA256 `880252d41bee39865cd562d3b5e407b8d4b5b2214859880add34a9a1647555bc`
- This handoff's final byte hash is in the author's EDITSTOP response.

**13 synthetic CPU tests PASS,17.777s**; CLI `--help` passes.

```bash
PYTHONDONTWRITEBYTECODE=1 timeout 180s python3 -B -m unittest discover \
  -s /tmp -p 'test_astra_additive_replay_recovered_analysis_20260913.py' -q
```

Tests cover complete recovered cohorts, rc0/1/1 preservation plus optional
BrokenPipe, missing/duplicate seeds, nonzero/bool rc, failure/claim/source hash
substitution, changed scientific costs/order/parents/raw output/thresholds,
nonzero recovery work, malformed failures, byte-preserving failure reads,
directory separation/inventories, and write-once CLI. Tests explicitly forbid
calls to the old success-only reduction/launcher branch. Only those forbidden
entrypoints are mocked in tests; production never patches any old globals.

All new native/recovery outputs and receipts in tests are synthetic. Full source
fixtures reuse the byte-pinned prospective test helper
`/tmp/test_astra_additive_replay_analysis_20260913.py` SHA
`cb59676941df9a4fbc13679c5b910333accd1edc5f7cd153ca73d6c163d38047`,
which reads only pre-additive own-repair material/history. No present additive
outputs are used. Synthetic adapter bytes are not tensor-computation evidence.

## Exact stable API / manifest

`load_apis(module_dir="/tmp",source_root=...,protocol_path=...,legacy_protocol_path=...)`
loads pinned CPU helpers. `load_bundle(entry,apis)` hashes local files;
`validate_recovery(bundle)` audits the explicit failure/recovery branch;
`reduce_seed(bundle,apis)` and `reduce_cohort(bundles,apis)` audit all scientific
evidence; `run(manifest_path,manifest_sha256,out,...)` writes a fresh report.
Always use the byte-validating loader before reduction, not handcrafted bundles.

Top-level manifest has exactly `schema,seeds`, schema
`astra_additive_replay_recovered_analysis_20260913_v1_inputs`; exactly three
unique strict integer seeds0/1/2. Each entry has EXACTLY these eleven fields:

```text
seed                  strict integer 0|1|2
root                  complete absolute LOCAL original root mirror
plan_sha256           actual original plan.json byte hash
completion_sha256     actual original capture_complete.json byte hash
scores                {path,sha256} for REPAIRED scores.json
collection            {path,sha256} for REPAIRED collection.json
collection_claim      {path,sha256} for ORIGINAL .collection_claim.json
launcher              {root: LOCAL original .launcher directory,
                       files: {relative_filename: actual file hash, ...}}
original_failure      {path,sha256} for ORIGINAL collected/collection_failure.json
recovery              {path,sha256} for REPAIRED recovery.json
recovery_claim        {path,sha256} for NEW .collection_repair1_claim.json
```

All path bindings are explicit LOCAL nonsymlink files. Preserve native absolute
paths inside JSON exactly; never replace them with local paths. The original
collected directory must contain ONLY `collection_failure.json`. The separate
repaired directory must contain ONLY `scores.json,collection.json,recovery.json`.
The original launcher full inventory remains required, including stdout.log and
optional transport failure.json. No holder-failure/extra launch/retry artifacts
are silently ignored. Both original and new claims are retained and distinct.
The native new-claim `out` must equal original root + `_collected_repair1`.

The complete original four-stage raw inventory, all adapter/steps bytes, source
snapshots, prepared encodings/calls, and original prepare/controller receipts
remain required exactly as in the original reducer. No filters or reduced banks.

CLI after Main authorizes real reduction:

```bash
python3 -B /tmp/astra_additive_replay_recovered_analysis_20260913.py \
  --manifest /tmp/MAIN_RECOVERED_ADDITIVE_MANIFEST.json \
  --manifest-sha256 EXACT_MANIFEST_BYTE_SHA256 \
  --out /tmp/FRESH_RECOVERED_ADDITIVE_ANALYSIS
```

Optional flags `--module-dir,--source-root,--protocol-path,--legacy-protocol-path`
have the same defaults as the frozen reducer. Outputs `analysis.json` and
`analysis.md`; schema `astra_additive_replay_recovered_analysis_20260913_v1`.
No reports are written until full three-seed validation succeeds. No discovery,
native collection or retry CLI; existing output/evidence directories are protected.

## Explicit recovered branch, not fake success

Original native controller **must be strict integer rc0**. Original collector
and holder-written terminal status **must remain strict integer rc1**. The exact
known failure is `error_type="AttributeError"`,
`error="'dict' object has no attribute 'score_row'"`, with `retry=false,time`.
The Python exception repr is not the failure writer's stored `error` value.
Original error text, raw UTF-8 file bytes, hashes and optional separate launcher
BrokenPipe are all reported. No original receipt is rewritten on disk or in memory.

Main repair API is bound to `/tmp/astra_additive_replay_collection_repair_20260913.py`
SHA `9b67256c42b7f7c18e79a10f9bc6201140833e8d6c339a7e192ca18de67c854a`.
Its exact schema `astra_additive_replay_collection_repair1_v1` is required for
both the new claim and recovery receipt. Validate exact fields/source pins,
plan/completion/claim/scores/collection hashes and the five original failure-file
hashes (old claim, collection failure, controller_exit, collector_exit, exit).
Require `collection_attempt=2,scientific_retry=false`, strict integer recorded
recovery rc0, zero generation/fits/updates, equal collection/recovery elapsed time
and <=180s. Receipt/source declarations are NOT interpreted as a second fit.

Frozen `load_bundle` is reused ONLY as the file loader: it reads the true original
failed claim/launcher alongside new separately bound score/collection files and
does not evaluate their terminal rc. New explicit `audit_original_attempt` and
`validate_recovery` then handle the changed custody branch. The old success-only
`reduce_seed`, `reduce_cohort`, `validate_launcher` and `run` are NEVER called.
No AST rewriting, dynamic code patch, fake rc0 receipt or teacher repair.

The scientific assembly/checks retain the original explicit plan/limit checks
and reuse its unchanged `validate_sources`, `validate_custody`, `item_changes`,
frozen raw scorer/metrics/constants/source helpers. Full original encoding FILE
byte pins, original parents not descendants, native raw/token/route/finish joins,
loss/order/token accounting, frozen masks/EOS and all4stage release receipts remain
mandatory. A native controller failure cannot be excused by a collection repair.

## Reporting and limits

All3seeds, both arms, original denominators14/8/8 exact and paraphrase,48held,
12canary,16possible records. Original exact floors8/7/5 AND no lost LR0-correct
held/canary are unchanged. Gains do not offset losses. Historical LOWER/HIGH/LR0/
REPLAY/EXTRA_MEMORY remain noncontemporaneous with zero incremental cost.
Per-item contrasts/restoration/drift, constants, losses/norm receipts, separate
memory/replay tokens, full occurrence order and timings remain in the output.

Scientific totals stay6fits1632updates480coldcalls; recovery adds zero scientific
work and reports separate CPU elapsed time. Original holder span still includes
the failed collector; do not sum nested spans. Original preparation+holder logged
time remains bounded by8aggregate hours, controller7200s; each recovery<=180s.
Elapsed/reservation idle gaps and actual GPU-active time are not independently metered.

The repair's before/after checks attest preservation of the five bound original
failure files and original stage inventory. The reducer independently rehashes
the copied evidence and rescores raw bytes. Full original launcher logs are pinned
locally; their pre-repair historical equality is not independently time-traveled.
Repair recovery.json and holder exit.json are written before their CLI/process
returns; neither is an independent OS wait/reap receipt. Main's rc0 execution
confirmation is separate. No live native identity/absence, kernel/tensor-norm
recomputation or proof against unrelated other-root launches is claimed.

`automatic_promotion=false,scientific_pass=null,fit_authorized=false` always.
Only a scoring implementation recovery: not retention evidence selected after
new results, not a new science attempt, not H1/H2/parenting/clean-lineage promotion.

## Frozen and not read

Original reducer remains SHA
`df38efd210929ec21523d19daa8b65f98d50fef435b3fa23b719929bca6dc472`.
Original runner/core/trainer/launcher/source/thresholds are untouched; original
dependency pins remain enforced. Main reported verified current mirror
`/tmp/astra_additive_replay_native_20260913_attempt1` and archive SHA
`1faf1f6a6482a3834f7aa4c98c34b71c29644acdc4dfec9ac7c0b3cd7c3b1d16`
(1366members,523970560bytes,6adapters). These are Main-provided provenance only:
this author did NOT read that mirror, archive or archive receipt before EDITSTOP.
