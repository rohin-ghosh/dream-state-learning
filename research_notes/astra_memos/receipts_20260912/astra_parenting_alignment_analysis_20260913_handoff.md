# Parenting alignment independent reducer — pre-outcome EDITSTOP

September 13, 2026. Final sources bound, CPU fixtures complete; no assay outcomes
retrieved. Only this analyzer, its test and this handoff were edited. No native
commands, tokenizer/model/GPU work, lifecycle API, collection, network, Git,
repository, core, runner or old-artifact edits.

## Final pins and tests

- Analyzer `/tmp/astra_parenting_alignment_analysis_20260913.py`
  SHA256 `bfb91300b4d9e3c7abdd3c12a1b61541321db323ed96b7d49cc240a95cb6085d`.
- Tests `/tmp/test_astra_parenting_alignment_analysis_20260913.py`
  SHA256 `845a3c041dc4efa40004e7bfdc97e057b79f580efa9626f79d447ce459649bfa`.
- Final core `71311d3d9add1f485289c6ee6824ef758393193ee05bcc088674d12697b11010`.
- Final runner `712248f1fc86b026e68e9cfbc791d3b441c6ded53db82f7622f8f2cd2b8b8c2a`.
- Protocol `5c53d6aa850b3a3a409c255ab9b28ce3b090f7325f35688437e42a86b1cccce5`.

**13 CPU tests PASS, 6.674 seconds.** CLI help passes. Tests use scripted CPU
world captures; synthetic file-roundtrip tests mock only original parent plan
pins inside a private test module, never production CLI source checks. Includes
all312calls/zero fits, all-invalid56calls/root retaining16slots, receipt-splicing
as an actual child error versus harness tampering, public-world tampering,
re-signed prompt leakage, rendered-prefix leakage, route/token/cell mismatch,
bad restatement/noncanonical content separation, zero/partial/duplicate roots,
missing contacts/stages/uncalled slots, bool/NaN/JSON duplicates, custody/exit/
release failures, exact vector boundaries, file pins and write-once outputs.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tmp python3 -m unittest -v test_astra_parenting_alignment_analysis_20260913
```

## Locked interface and manifest

`load_sources(module_dir, source_root, protocol_path) -> apis`
loads the exact core/dependencies and AST-extracts only the original native
`validate_response` function. It does not import runner lifecycle code.
`load_bundle(entry) -> bundle` reads only the supplied local mirror/receipts.
`reduce_seed(bundle, apis) -> result`, `reduce_cohort(bundles, apis) -> result`
perform CPU replay and independent tallying. `feasibility(cells)` independently
implements the authoritative complete nine-cell vector and checks agreement
with the frozen core. Missing seeds are errors, not a reduced-denominator gate.
`run(manifest_path, manifest_sha256, out, module_dir, source_root, protocol_path)`
writes fresh `analysis.json` and `analysis.md` only after all three roots pass
validation; returns both file hashes. No retry/overwrite/partial-result option.

Input schema `astra_parenting_alignment_analysis_20260913_v1_inputs`;
result schema `astra_parenting_alignment_analysis_20260913_v1`.
Top level has exactly `schema,seeds`. Each seed entry has exactly the fields
shown below; repeat for integer seed0/1/2, using Main's actual full hashes.
This is a template only, not an outcome manifest or guessed artifact pin.

```json
{
  "schema": "astra_parenting_alignment_analysis_20260913_v1_inputs",
  "seeds": [
    {
      "seed": 0,
      "root": "/absolute/local/mirror/parenting_alignment_seed0_20260913_attempt1",
      "plan_sha256": "MAIN_FULL_PLAN_SHA256",
      "completion_sha256": "MAIN_FULL_COMPLETION_SHA256",
      "report": {
        "path": "/absolute/local/mirror/parenting_alignment_seed0_20260913_attempt1_collected/alignment_report.json",
        "sha256": "MAIN_FULL_REPORT_SHA256"
      },
      "collection": {
        "path": "/absolute/local/mirror/parenting_alignment_seed0_20260913_attempt1_collected/collection.json",
        "sha256": "MAIN_FULL_COLLECTION_SHA256"
      },
      "claim": {
        "path": "/absolute/local/mirror/parenting_alignment_seed0_20260913_attempt1.collection_claim.json",
        "sha256": "MAIN_FULL_CLAIM_SHA256"
      },
      "holder_span": null
    }
  ]
}
```

Mirror preserves collected-directory basename so the claim's native output
basename joins. Do not rewrite original absolute native paths inside evidence.
Native run pattern is
`/localhome/local-rohing/astra_diagnostics/parenting_alignment_seedN_20260913_attempt1`;
reducer never follows that path. Every planned input snapshot and complete-stage
JSON/log is hash checked under the explicitly supplied local mirror. Preserve
original plan, sources, prior-task IDs, preflight, manifest, raw calls, launch/
started/done/exit/released/closed receipts, prepare/controller entry receipts.

Optional `holder_span` is null (reported unavailable, not zero), or exactly:
`{"start":{"path":"...","sha256":"..."},"end":{"path":"...","sha256":"..."},"start_field":"actual_start_field","end_field":"actual_end_field"}`.
Fields must be actual nonnegative numeric timestamps in Main-supplied pinned
receipts, in the same clock domain. Result labels this a supplied holder span,
not an independent process-ownership or GPU-active-time measurement. No holder
start/end is inferred from unrelated file timestamps. Prepare, controller,
collection and nested generation/capture spans are reported separately.

Run only after Main authorizes and supplies complete mirrors:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 /tmp/astra_parenting_alignment_analysis_20260913.py \
  --manifest /tmp/MAIN_ALIGNMENT_INPUTS.json \
  --manifest-sha256 MAIN_FULL_MANIFEST_SHA256 \
  --source-root /tmp/astra_level1_real_record_source_20260913_attempt1 \
  --protocol-path /data/home/rohing/dream-state/research_notes/astra_memos/ASTRA_PARENTING_ALIGNMENT_DEV_2026-09-13.md \
  --module-dir /tmp \
  --out /tmp/MAIN_FRESH_ALIGNMENT_ANALYSIS
```

`module-dir` contains final alignment core/runner and frozen
`astra_level1_real_record_run_20260913.py` SHA256
`3c03304ee5309517ce34f91b121594f0070b37bfb14f31f429f915d8310cc20e`.
Core transitively loads its already pinned parented/v2/memory definitions at
their unchanged `/tmp` paths. Source root supplies pinned rulegame/parser bytes;
no native deployment or extra package installation is needed for this reducer.

## Checks and interpretation limits

Core replay regenerates every fixed contact, request, public CPU world event,
fresh child execution, source parser result and failure from exact saved raw
responses. Independent tallying checks all16tasks/arm, delivered-lesson RESTATE
(4contacts, N/A for NO_PARENT), PROCESS_USE, EXECUTED, RECORD_FAITHFUL and their
FULL_MATERIAL conjunction **without RESTATE**. No invalid/uncalled slot drops.
Core replay enforces task-local reset, only the current raw restatement, no
separate lesson in application, same task bytes/order and twice-each lesson
multiset. Child repetition of lesson bytes remains legal raw restatement;
it is not confused with harness-injected lesson leakage.

Native request/response/route/prompt-vector joins and exact Qwen text serialization
are checked against replayed messages and recorded preflight system segment.
This is not retokenization or verification against model tensor contents.
Recorded original parent/model inventories and release assertions are checked,
not live GPU/process state. CPU source/world/parser replay is not native replay.

Output includes absolute A/S/N masks/counts, all-item A-minus-S and A-minus-N
paired labels, family/delivery strata (8vs8 and each family's4vs4), field-level
public-note/own-event results, format/canonical counts, raw diversity and
restatement overlap/lexical scores, per-arm/root call/token/time costs and the
full seven-component vector/root masks. No pooling or task-as-learner inference.
At least2roots must satisfy each positive criterion; SWAPPED no-large-harm is
strictly >-4 on all3roots; NO_PARENT no-large-harm is >=-2 on all3roots.

The2:1family-order schedule is confounded with learner seed. Restatement checking
is lexical operational evidence, not semantic proof. The contrast concerns
immediate lesson-to-raw-restatement alignment, not mediation, persistence,
parenting amortization, equal total compute, H1/H2 or writer authorization.
NO_PARENT is not token matched; SWAPPED may help or interfere. A positive vector
does not change `automatic_pass=False` or `fit_authorized=False`.

## Preserved pre-execution coordination history

Initial note to Main / Beauvoir / Parfit: protocol SHA256
`5c53d6aa850b3a3a409c255ab9b28ce3b090f7325f35688437e42a86b1cccce5`
is authoritative. No outcomes read; CPU fixtures only. At the time of this
initial note, core/runner source pins remained unset awaiting EDITSTOP.

## Interface question requiring resolution before freeze

**RESOLVED before native execution, no protocol amendment.** Final core
`71311d3d9add1f485289c6ee6824ef758393193ee05bcc088674d12697b11010`
has `>= -2` in both vector and root masks. The independent boundary fixture
passes and matches that final core. The initial finding below is retained as
pre-execution history, not an outstanding concern. Runner is now pinned above.

Protocol feasibility anchor condition: "no root worse than NO_PARENT by more
than 2/16" means ALIGNED-minus-NO_PARENT **>= -2**. Current in-progress core
`threshold_vector` uses **> -2** in both vector and root masks, rejecting the
allowed equality. Independent reducer will implement >= -2 and regression-test
the boundary. Please repair core before pinning, or obtain an explicit protocol
amendment; this reducer does not change protocol or core. SWAPPED condition is
different: "no root at or below -4/16" requires strictly > -4.

## Planned compatible seam

Read explicitly supplied local complete mirrors and pinned
`plan.json`, `capture_complete.json`, `alignment_report.json`, `collection.json`
plus external collection claim. Never follow preserved native absolute paths.
Replay each capture through core `replay_validate` / `run_phase` using only
captured responses and CPU world, compare every generated request including
task-local/current-raw-restatement context. Independently tally all16tasks,
four contacts per lesson arm, per-family/delivery strata, masks, fixed vector,
and itemwise A/S/N pairs. Join native requests/responses to the replayed callback
events and archived release receipts without tokenization or lifecycle APIs.
All3seed/9arm cohort is required; no positive gate for partial/zero attempts.
Malformed outputs remain outcomes with uncalled record slots, not dropped rows.

Only this handoff plus new analyzer/test files are owned by this worker.

EDITSTOP
