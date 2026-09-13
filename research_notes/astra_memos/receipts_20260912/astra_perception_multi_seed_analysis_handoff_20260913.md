# Three-learner-seed perception analysis handoff

Ready for Main's post-collection review. CPU-only implementation and fixtures;
no actual run results, live roots, native/model/GPU/NVML/network/Git operations
were read or executed. Existing frozen scripts and repository files are unchanged.
Only the three assigned persistent `/tmp` files were created.

Before finalization, read only the newly supplied result-blind watcher audit
`research_notes/analysis/2026-09-13_perception_fit_result_blind_audit.md`
(Main-reported commit `76c2af24`), SHA-256
`56107132afda12926d0b708915c7bfddac412daf037e93eb5d23af61516000b6`.
The report binds that digest as `interpretation_audit_sha256`; no result file
was opened. Its engineering classifications are not automated acceptance gates.

## Entry point and explicit input

```text
python3 -B /tmp/astra_perception_multi_seed_analysis_20260913.py --manifest /COLLECTED/manifest.json --output /ANALYSIS/new-report.json
```

The output must not exist. No output is created unless all three inputs pass;
an incomplete/failed/mismatched seed rejects the aggregate, never disappears
from its denominator. There is no discovery, live-root monitoring, partial
report mode, training, model import, native replay, selection or tuning.

Manifest shape (replace every placeholder with Main's explicit paths/pins):

```json
{
  "schema": "perception_three_seed_collected_analysis_v1",
  "corpus": {
    "path": "/PINNED_PUBLIC_SOURCE/organism_v6/birth_skill_corpus.py",
    "sha256": "MAIN_EXPECTED_CORPUS_SHA256",
    "parser_sha256": "MAIN_EXPECTED_PUBLIC_PARSER_SHA256"
  },
  "runs": [
    {
      "learner_seed": 0,
      "collected_snapshot": true,
      "root": "/COLLECTED/seed0/root",
      "scores": "/COLLECTED/seed0/scores/scores.json",
      "plan_sha256": "MAIN_EXTERNAL_EXPECTED_PLAN0_SHA256",
      "completion_sha256": "MAIN_EXTERNAL_EXPECTED_COMPLETION0_SHA256",
      "scores_sha256": "MAIN_EXTERNAL_EXPECTED_SCORES0_SHA256"
    },
    {
      "learner_seed": 1,
      "collected_snapshot": true,
      "root": "/COLLECTED/seed1/root",
      "scores": "/COLLECTED/seed1/scores/scores.json",
      "plan_sha256": "MAIN_EXTERNAL_EXPECTED_PLAN1_SHA256",
      "completion_sha256": "MAIN_EXTERNAL_EXPECTED_COMPLETION1_SHA256",
      "scores_sha256": "MAIN_EXTERNAL_EXPECTED_SCORES1_SHA256"
    },
    {
      "learner_seed": 2,
      "collected_snapshot": true,
      "root": "/COLLECTED/seed2/root",
      "scores": "/COLLECTED/seed2/scores/scores.json",
      "plan_sha256": "MAIN_EXTERNAL_EXPECTED_PLAN2_SHA256",
      "completion_sha256": "MAIN_EXTERNAL_EXPECTED_COMPLETION2_SHA256",
      "scores_sha256": "MAIN_EXTERNAL_EXPECTED_SCORES2_SHA256"
    }
  ]
}
```

Exactly integer seeds 0, 1, 2 and distinct absolute collected root/scores paths
are required. Use relocated snapshots, not original/live roots. Preserve the
original JSON bytes and their recorded original paths; do not rewrite a plan
to the collected location. Original plan source/model/probe/adapter paths are
metadata only, never opened or resolved by the analyzer. The explicit pinned
public source path is the sole code input. The scorer is loaded directly from
that file, not from `sys.path` or an existing `organism_v6` module cache; its
sibling `rulegame_parenting_diagnostic.py` must match the parser hash. The corpus
uses its existing AST-selected standard-library public parser interface.

CPU fixtures used these public source hashes (Main must supply the accepted
matching source for the actual collections):

- Corpus: `078ceba07141b5f6fb2159a12e21f1eccc0901ba9f51f52d1793d988927812f6`
- Public parser: `e6055da48b2c6fa1bd294c9d991e07f32f05dc6630fe8973373977bdfe977526`

## Validation boundary

External hashes bind each `plan.json`, `capture_complete.json` and scores file.
The analyzer then checks the plan-bound `dev.json` and `calls.json`, all six
readout identities/closed files/12 requests/12 responses, original row/source
identifiers, token/request pairing, LoRA routes, termination metadata, original
score decisions and counts. Every original primary score is recomputed on the
unmodified raw text using the accepted corpus scorer; its full decision dict,
response hash and finish reason must exactly match the collected score row.
Duplicate JSON keys and nonfinite JSON constants are rejected throughout.

The completion must contain both fits and all six cells, 72 responses per seed
(216 total). Fit receipts bind arm and 12 updates/48 presentations. Seed 0's
accepted files lack later `learner_seed` fields: the analyzer explicitly permits
that historical schema only for seed 0, while requiring `config.seed == 0`.
Replication metadata and configuration must bind seeds 1 and 2 strictly.

Plan/source pins, DEV source/proof/target rows, anchor, call order, rendered
input/token audits, full effective config except learner seed, engine, sampling,
model files, chat template and probe hash are matched across seeds. The exact
existing corpus default ordering is reused; it is not reseeded. Generation and
engine seed remain 0, max output tokens 192, LoRA enabled with max rank 32 for
every cell, OFF route null. No tokenizer/model is loaded to regenerate tokens.

This is not archive custody or native requalification. Only analysis-consumed
completion-bound files are rehashed, not all weights, logs, optimizer manifests
or native release evidence. Main retains whole-archive custody, approved recipe,
actual masks/token decode, native environment/GPU release and launch acceptance.
Snapshot attestation and relocation checks prevent routine accidental original
root use, but are not a security sandbox against deliberately misleading paths.
Invalid schema/path/hash/score/count errors terminate nonzero with no new report;
there is no repair, fallback scorer, omitted seed or automatic retry.

## Primary output and paired contrasts

`per_seed` is ordered 0, 1, 2. Each has raw primary `correct/total` for all six
cells: OFF/fitAbsent/fitPresent crossed with absent/present readout anchor.
All primary denominators stay 12. Row outputs retain original primary decision
dicts, call/row/source IDs and response hashes for linking back to raw evidence.

- `gain_over_matched_OFF`: within-seed, same-readout-anchor paired gains,
  losses, both-correct, both-wrong and net count for each fit.
- `withdrawal_absent_minus_present`: for each training condition, pairs the
  same 12 sources at readout absent minus present. Negative net means worse
  without the readout anchor. `off_adjusted_net` is
  `(fit_absent_readout - OFF_absent) - (fit_present_readout - OFF_present)`.
- `training_anchor_present_minus_absent`: paired fitPresent minus fitAbsent
  for each fixed readout anchor, within the same learner seed.
- `readout_present_minus_absent`: paired gains/losses/both-correct/both-wrong
  for OFF, fitAbsent and fitPresent separately, in the watcher's orientation.
  This explicitly includes OFF prompt elicitation; existing withdrawal keys
  retain their clearly named opposite orientation.
- `across_seed`: arithmetic mean/minimum/maximum across exactly three learner
  seeds for cell counts, descriptive errors, paired transitions/effects, token
  totals and grounded timing. Counts are not pooled episode replications.

`prespecified_contrasts` additionally names all six watcher contrast groups,
using O0/O1 = OFF absent/present, N0/N1 = fitAbsent absent/present and P0/P1 =
fitPresent absent/present:

1. `prompt_elicitation_O1_minus_O0`;
2. `ordinary_transfer_N0_minus_O0`;
3. `ordinary_prompted_N1_minus_O1`;
4. `anchor_training_withdrawn_P0_minus_N0`;
5. `anchor_training_prompted_P1_minus_N1`;
6. `residual_readout_prompt_dependence`, separately OFF O1-O0, fitAbsent N1-N0,
   and fitPresent P1-P0 (OFF is deliberately the same pair as group 1).

Every pair reports `x_cell`, `y_cell`, `x_only`, `y_only`, `both`, `neither`,
`net_count`, `net_fraction = (x_only-y_only)/12`, and the explicit row-ID lists
in all four directional categories. No net-zero contrast hides bidirectional
flips. Across-seed summaries include mean/range for each directional count and
net, without treating the repeated group-1/6 OFF pair as extra evidence.

`descriptive_training_anchor_interaction` explicitly reports `(P0-N0)-(P1-N1)`
as a count and fraction, with each matched row's signed contribution and an
across-seed mean/range. This is different from the retained per-fit
`off_adjusted_net`, which adjusts readout withdrawal for OFF prompt effects;
neither is an inferential difference-in-differences claim.

No significance, uncertainty intervals, best seed/checkpoint, automatic pass,
H1/H2, L2 or persistence inference. Repeated OFF cells are matched numerical
controls, not additional independent learner seeds. This remains authored
development record fidelity, not teacher distillation or sleep.

## Predeclared SECONDARY descriptive view

This implements the narrow fence/field view requested with SEQ127, before
reading any actual captures. It never changes primary text/scorer/target or
denominators. Only an entire single lowercase `json` Markdown fence is stripped:
opening ` ```json ` on its own line, newline-delimited body, closing ` ``` ` on
its own line, with optional surrounding whitespace. Multiple/nested fences,
prose before/after, unlabeled/uppercase/inline fences and partial extraction are
not repaired. CRLF is accepted; nested triple backticks prevent stripping.

- `primary.raw_format_errors`: raw text cannot decode to a JSON object;
  independent diagnostic, not a replacement primary pass rule. An object with
  missing/wrong fields can have zero format errors and still fail primary.
- `primary.field_errors` and `primary.schema_errors` report independent
  strict-raw diagnostics with no fence removal, alongside the original scorer's
  exact (first-failure) `failure_counts`. Per-row strict field/schema errors are
  retained as `strict_field_errors` / `strict_schema_error` in the diagnostic
  view. A whole fenced record therefore fails strict-raw parsing/fields even
  when the separately labeled secondary view recovers correct fields. None of
  these diagnostics replaces the accepted primary decision.
- Secondary separately reports fences stripped, remaining view-format errors,
  exact-key schema errors and complete-record count.
- Field errors for `try`, `observed`, `predicted`, `relation` are independently
  evaluated against the same source-backed target. A valid triple is exactly
  three integers (not booleans/floats); observed is a strict boolean; predicted
  is an explicitly present boolean or null; relation is the exact supported
  string. No coercion, inference, filling or target alteration.
- Missing/invalid fields count as errors; malformed/nonobject/duplicate-key
  JSON counts as errors for all fields. Empty captured text remains a failure
  in denominator 12. Extra keys fail schema/complete-record checks even if
  individual fields match. Error categories overlap and must not be summed as
  mutually exclusive events. A missing response *artifact* rejects the whole
  aggregate rather than being fabricated as a scored row.

## Termination, tokens and timing

Per-row/cell stop-versus-length and exact stop-reason counts, prompt/output
token counts, and generation-call intervals are retained. A length finish must
have exactly 192 output tokens; malformed content still contributes all tokens.
Stop reasons are JSON-encoded dictionary keys, distinguishing null/string/int.

`started_receipt_to_release_seconds` uses completion-bound `started.json.time`
and `released.json.time` for each fit/readout. It includes activity after the
start receipt through cleanup/release, not a pure training/inference duration;
the receipt occurs after some worker validation. Its per-seed sum excludes
pre-receipt initialization, controller gaps, collection and unrecorded time.
Generation intervals use each response's monotonic `ended-started`, excluding
engine initialization. No wall-clock subtraction across machines and no
ungrounded fit-only/total-controller runtime estimate.

## Fixtures and final pins

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s /tmp -p test_astra_perception_multi_seed_analysis_20260913.py -v
```

Final run: **36 CPU fixtures PASS, 7.729s** (quiet form of the same discovery
command). Supports `PERCEPTION_ANALYSIS_DRIVER` for a frozen script copy and
`PERCEPTION_PUBLIC_SOURCE` for the explicit public source tree used by fixtures.
Fixtures synthesize all captures/receipts; their example values are not model
results. Tests cover complete/missing/failed seeds, external pins, primary
decisions/counts/types, paired gains/losses/withdrawal, secondary fences and
strict field types, original-path avoidance, token/timing checks, module-cache
isolation, deterministic seed order and no partial output/overwrite.
The final additions test every prespecified pair's orientation and row-ID
partition, bidirectional OFF flips at zero net, all three readout-prompt pairs,
the named interaction and strict-versus-secondary independent field errors.

- Driver SHA-256: `5df41ad7ed78bca49789a6412207dbb8292913e68664960b245f61a66af8013c`
- Tests SHA-256: `a1dcc3303b42dcd4cc7db959fbfa44959ba6f01b003a4d8367d74a35dd89a827`
- Handoff hash is reported externally at EDITSTOP. The output's
  `manifest_sha256` hashes sorted canonical JSON without a trailing newline,
  not the supplied manifest file's whitespace; all external artifact pins
  remain raw-file SHA-256 values.
