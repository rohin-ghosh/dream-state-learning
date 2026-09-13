# Reflection three-seed analysis sidecar — source-only / CPU-fixture handoff

September 13, 2026, 05:24 UTC. Manuscript remains EDITSTOP pending Carver;
this assignment did not read or edit manuscript files. Main owns integration,
Git and operations. No experimental result, live output, native/model/tensor,
remote or network access occurred. No repository or other writer's files were
modified. No Git commands, WebFetch, curl, wget, launches or external sends.

## Owned files and hashes

Only these three persistent files were authored, using `apply_patch`:

| File | SHA256 |
| --- | --- |
| `/tmp/astra_reflection_multi_seed_analysis_20260913.py` | `6d84b3ed8c983a7702ad9d5a5165cf1cca97c3c92f8353eef7ed1a8bc790a515` |
| `/tmp/test_astra_reflection_multi_seed_analysis_20260913.py` | `2e3e8705ae5ba11568dab3fa42c658a6b6136962aac05995270b144dfdb81d47` |
| `/tmp/astra_reflection_analysis_handoff_20260913.md` | Self-hash returned separately; not recursively embedded. |

Tests create clearly synthetic files in automatically removed temporary
directories. No fixture uses captured experimental responses, native tokenizers,
real adapters, model weights or real fit outputs. Their fabricated adapter byte
files are custody fixtures, not valid tensors. No fixture report is scientific
evidence; no real analysis output was generated or inspected.

## Source schema compatibility

Read scripts only. The final reflection corpus is pinned to
`b69dfe4ab39e60fab826e67758d21e708c87d538f3fcd2b8a579bb778b0ace80`;
seed0 runtime to
`0f79efa1f4e4da6a9d1ec245c09e665f7c2b7d8bce31f7e01fe01b00f95a72fc`.
Plato's replication source became available during this task and its exact
fields were read; no inferred replica schema remains. The accepted source is
`/tmp/astra_reflection_fit_replication_run_20260913.py`, SHA256
`d1f572d094507f85245af2edd95608daffa8322a2d5dbae01ae31957e40ac6c9`.

The initially read replica source had prefix `4be19c48`; its concurrent revision
caused the initial test setup to stop on a source-hash mismatch, with zero tests
run. After source/schema reinspection, the analyzer was bound to `d1f572d0`.
The subsequent 26-test run passed; the final expanded 34-test run passed.
If the producer source changes again, do not silently swap pins or normalize
receipts. Review the source/schema change and update this sidecar explicitly.

Seed0 uses scope `authored_reflection_12train_24dev_twofits_sixreadouts_v1` and
has no required `learner_seed` field. Replicas use
`authored_reflection_12train_24dev_learner_seed_replication_v1`, bind
`parent_driver_sha256` to seed0, and require integer learner seed1/2 in the
plan, prepared training audits, completion, scores, collection receipt, fit,
identity, closed, launch, started and released receipts. `config.seed` must
match the manifest learner seed; engine and sampling seeds remain unchanged.
All per-seed native path strings remain untouched; only declared relocated
paths are accessed. PID identity is compared within a seed, not across hosts.

## API and invocation

Python API: `analyze(manifest: dict) -> dict`. It performs reads/computation
only and returns the report; it writes nothing. CLI:

```text
python3 -B /tmp/astra_reflection_multi_seed_analysis_20260913.py --manifest /ABS/manifest.json --output /ABS/new_reflection_analysis.json
```

This is a future **post-COLLECTION** invocation, not an instruction to run on
current work. The output must not exist and must be outside all supplied source,
runtime, snapshot, log and collection inputs. It is created exclusively only
after validation/recomputation succeeds. Failure during validation creates no
output. File hash pins refer to SHA256 of file bytes; the returned manifest hash
is separately labeled canonical JSON UTF-8 with no trailing newline.

Manifest shape below is documentation, not a populated manifest or a real
collection identity. Replace every `/ABS/...` path and every `*_FILE_SHA256`
placeholder with independently established completed-snapshot bindings. Keep
the source/runtime hashes exactly as shown; paths may relocate those same bytes.

```json
{
  "schema": "reflection_three_seed_collected_analysis_v1",
  "preselected_learner_seeds": [0, 1, 2],
  "selection_before_outcomes": true,
  "source": {
    "root": "/ABS/pinned-source-root",
    "sha256": {
      "organism_v6/__init__.py": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "organism_v6/birth_skill_corpus.py": "078ceba07141b5f6fb2159a12e21f1eccc0901ba9f51f52d1793d988927812f6",
      "organism_v6/rulegame_parenting_diagnostic.py": "e6055da48b2c6fa1bd294c9d991e07f32f05dc6630fe8973373977bdfe977526",
      "organism_v6/train_adapter_v3.py": "7bbf165fcb4b8ae3a1180328bcd19f57382c30516daddc95fd61e8a2c749fad7",
      "organism_v6/birth_reflection_probe.py": "b69dfe4ab39e60fab826e67758d21e708c87d538f3fcd2b8a579bb778b0ace80"
    }
  },
  "runtimes": {
    "seed0": {
      "path": "/ABS/astra_reflection_fit_run_20260913.py",
      "sha256": "0f79efa1f4e4da6a9d1ec245c09e665f7c2b7d8bce31f7e01fe01b00f95a72fc"
    },
    "replication": {
      "path": "/ABS/astra_reflection_fit_replication_run_20260913.py",
      "sha256": "d1f572d094507f85245af2edd95608daffa8322a2d5dbae01ae31957e40ac6c9"
    }
  },
  "runs": [
    {
      "learner_seed": 0,
      "collected_snapshot": true,
      "root": "/ABS/seed0-relocated-root",
      "logs": "/ABS/seed0-relocated-worker-logs",
      "scores": "/ABS/seed0-collected/scores.json",
      "plan_sha256": "SEED0_PLAN_FILE_SHA256",
      "completion_sha256": "SEED0_COMPLETION_FILE_SHA256",
      "scores_sha256": "SEED0_SCORES_FILE_SHA256",
      "collection_sha256": "SEED0_COLLECTION_FILE_SHA256"
    },
    {
      "learner_seed": 1,
      "collected_snapshot": true,
      "root": "/ABS/seed1-relocated-root",
      "logs": "/ABS/seed1-relocated-worker-logs",
      "scores": "/ABS/seed1-collected/scores.json",
      "plan_sha256": "SEED1_PLAN_FILE_SHA256",
      "completion_sha256": "SEED1_COMPLETION_FILE_SHA256",
      "scores_sha256": "SEED1_SCORES_FILE_SHA256",
      "collection_sha256": "SEED1_COLLECTION_FILE_SHA256"
    },
    {
      "learner_seed": 2,
      "collected_snapshot": true,
      "root": "/ABS/seed2-relocated-root",
      "logs": "/ABS/seed2-relocated-worker-logs",
      "scores": "/ABS/seed2-collected/scores.json",
      "plan_sha256": "SEED2_PLAN_FILE_SHA256",
      "completion_sha256": "SEED2_COMPLETION_FILE_SHA256",
      "scores_sha256": "SEED2_SCORES_FILE_SHA256",
      "collection_sha256": "SEED2_COLLECTION_FILE_SHA256"
    }
  ]
}
```

`root` contains `plan.json`, `capture_complete.json`, the seven plan-pinned
prepared inputs and `run/<stage>/...`. `logs` contains the eight stage
directories, each with `stdout.log` and `stderr.log`. Completion uses the actual
reflection layout `stages[stage].artifacts` and `.logs`, not the older flattened
perception layout. `collection.json` must sit beside the supplied scores file
and bind its SHA256 and the completion SHA256. Original native root/log/source/
model paths are never followed. All three seeds are required, with distinct
supplied paths; there is no seed selection, partial-run pooling or live fallback.

## Returned report contract

- `tables.restatement`: six cell rows of `exact_authored_fixture_matches`,
  separate seed0/1/2 counts and denominator12 per seed, descriptive mean/range,
  length finishes and prompt/output tokens/generation seconds. Prose syntax
  is not scored: `syntax_valid` is `[null, null, null]`.
- `tables.application`: six cell rows of `strict_application_correct` out of12
  per seed, with the same separate cost/termination columns plus strict A/B
  syntax-valid counts. No stripping, punctuation removal or semantic rescue.
- `per_seed[].cells[cell][panel]`: unchanged corpus decisions plus source IDs,
  call IDs, exact raw response text, authored target, input messages, public
  source/proof, response hash, termination and token/timing fields. Raw prose
  remains available for a later manual review; no review labels are invented.
- `per_seed[].paired_flips[panel]`: gains, losses, both-correct and both-wrong
  counts **and row IDs**, with oriented `x_cell`/`y_cell` and net count. Includes
  OFF parent elicitation, ordinary withdrawn transfer, parent-trained versus
  ordinary under each readout, each fitted cell versus matched OFF, and
  residual parent dependence. Panels and learner seeds never get merged.
- `per_seed[].training_exposure`: per-epoch and full-fit prompt, authored target,
  supervised target-plus-EOS and total input token exposure, with prompt and
  authored-target UTF-8 bytes reported separately; padded
  tokens, actual recorded epoch order and batch exposure remain explicit.
  Targets/order are checked as matched across arms within each seed, while
  input exposure is allowed to differ. Native tokenization is not reproduced.
- `per_seed[].timing`: eight start/release wall intervals, their sum and first
  stage-start to last-release span. Generation monotonic intervals are nested
  within these windows, not additive training time. Collection, transfer and
  model-verification time are excluded.
- Top-level `total_responses=432` is a work/capture count, **not** a combined
  performance denominator. `semantic_prose_score` and `composite_metric` are
  null; `automatic_pass` and `clean_ancestry_certified` remain false. No p-values,
  significance, scientific promotion or generalization claim is emitted.

## Validation boundary

The analyzer verifies declared source/runtime pins, plan/prepared-input pins,
completion/scores/collection binding, exact stage and raw inventories, each
completion-bound artifact and log hash, eight fresh worker identities per seed,
stage order/release timing, fitted adapter byte/config custody and recorded fit
completion/exposure. It rejects failure artifacts, stale/missing scores,
symlinks, unsafe members, route swaps, prompt-token audit mismatches, invalid
termination/token budgets, replica seed drift and cross-seed data/readout/config
drift. It retains original native path strings to compare adapter routes without
trying to open those paths.

The frozen corpus is loaded as CPU source; its unchanged `score_response` is
used for every raw response and compared with every stored row/count. The public
parser interface is the corpus's existing AST-selected CPU interface. Panel
construction is cached without changing metrics. Only the pinned runtime's
static constants and pure `check_fit_manifest` function are selected from its
AST; no runtime driver, trainer, tokenizer or GPU module is imported/executed.
Binary adapter files in future completed snapshots are hash-checked only, never
deserialized. Source and runtime pins are checked again before report return.

This is custody and CPU reconstruction, not native execution, tokenizer
reencoding, actual epoch-RNG replay, raw tensor verification, process liveness,
official model-origin recertification or independent scientific review. The
explicit preselection declaration records the supplied pre-outcome selection;
this sidecar does not independently timestamp-certify it. No compressed capsule
is unpacked or verified by this API: Main must supply intact relocated roots,
logs, collection receipts and independently obtained pins. No actual completed
reflection snapshots have been used to validate this sidecar yet.

## Checks completed

```text
python3 -B /tmp/test_astra_reflection_multi_seed_analysis_20260913.py
Ran 34 tests in 20.261s
OK

python3 -B /tmp/astra_reflection_multi_seed_analysis_20260913.py --help
PASS
```

Both Python files also pass in-memory syntax compilation, terminal-newline and
trailing-whitespace checks without writing bytecode. Fixtures cover valid
seed0/replica schemas, exact-versus-prose distinction, strict whitespace and
length behavior, flip memberships, tokens/exposure, identity/route/custody
tampering, collection/claim boundaries, source pin failures, cross-seed drift,
bad paths/symlinks, exclusive CLI output, failure without output and input-byte
preservation. An import guard verifies no native or repository-package imports
during analysis. Tests use public source scripts and synthetic data only.

Default test source locations are the current repository's source files and
the two `/tmp` runtime scripts above; to relocate the same pinned bytes set
`REFLECTION_SOURCE_ROOT`, `REFLECTION_SEED0_RUNTIME` and
`REFLECTION_REPLICA_RUNTIME`. No packages, formatters or network access needed.

EDITSTOP
