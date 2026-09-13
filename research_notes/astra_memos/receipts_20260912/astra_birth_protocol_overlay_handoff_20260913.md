# Candidate A overlay — contingent CPU data, EDITSTOP

Only owned module, tests and this handoff changed. No original corpus/probe/runtime,
trainer or source edits; no native tokenizer/model/GPU/network/Git/fit execution.
Main selected a prompt-clarified diagnostic BEFORE considering a fit. This overlay
is NOT selected for fitting and does NOT repair or train around harness ambiguity.
It retains the proposed frozen practice renderer, including the competing unrevealed
QUIZ reminder in TRY prompts. No cases were changed using newly reported outcomes.

## Stable public API (in-memory JSON, no runtime or filesystem exporter)

Module: `/tmp/astra_birth_protocol_overlay_20260913.py` (301lines).
Arms: `BRIDGE_AUTH`, `BRIDGE_DERANGED`; old AUTH/DERANGED arm names are rejected.

```python
import astra_birth_protocol_overlay_20260913 as overlay
candidate = overlay.build_candidate()
cpu_audit = overlay.audit_candidate(candidate)
recipe = overlay.training_recipe()
raw_items = overlay.train_items(candidate, 'BRIDGE_AUTH')
```

- `build_candidate()` takes no selection/configuration arguments; fixed root0 bank.
- `audit_candidate(candidate)` checks this NEW specification by exact regeneration,
  unchanged background, group/target maps and all raw positive/negative controls.
- `training_recipe()` returns the original recipe at LR1e-4, seed0, epochs4.
- `train_items(candidate, arm, render_context=None)` returns v3 span items, optionally
  using a supplied context renderer. Unrendered items are NOT native-ready exports.
- `audit_tokenizer(candidate, tokenizer, *, recipe=None)` uses the real v3 normalization,
  encoding, group ordering and collator with a supplied tokenizer callback.
- `audit_native(candidate, model_path, expected_file_hashes, *, recipe=None)` loads
  ONLY a pinned local tokenizer with local_files_only=True/trust_remote_code=False.
- `export_native(candidate, native_report, arm)` returns `{'corpus': [...]}` only
  from this candidate's matching native-overlay audit; callback/old/partial/mismatched
  reports are rejected. It does not save files, run a trainer, or authorize fitting.
- `digest(value)` uses birth's canonical JSON + newline SHA256 (not file hashes and
  not the frozen probe's no-newline digest convention).

Future native invocation shape, NOT run or authorized here:

```python
report = overlay.audit_native(candidate, LOCAL_MODEL, TOKENIZER_FILE_HASHES)
auth_export = overlay.export_native(candidate, report, 'BRIDGE_AUTH')
deranged_export = overlay.export_native(candidate, report, 'BRIDGE_DERANGED')
```

Pin the unchanged candidate/report bytes in Main's integration; a report is an audit
artifact, not independently authenticated model provenance. Candidate source_sha256
includes this module, frozen probe, original birth/conditional/spec/process/generator
modules and trainer. Main must preserve those exact bytes in any source snapshot.

## Exact256-row inventory and controls

All240 retained rows are byte-equivalent dictionaries to original root0 AUTH in BOTH
arms, including all64 PROSPECT +64 REVISE. Original DERANGED conditional targets are
NOT used. Original128dev rows and dev twins are preserved separately, unchanged.

For k=0..7, group g=4*k replaces orders4+(k%2),6+(k%2). Absolute row indices:
`4,6,37,39,68,70,101,103,132,134,165,167,196,198,229,231`.
Removed ADDITION/COPY indices in each family: `0,9,16,25,32,41,48,57`.

| New rows | Counts and exact source/label contract |
| --- | --- |
| TRY pairs k0..3 | 8rows: triples (0,0,0),(0,0,1),(0,0,2),(0,0,3), supplied T/F each; canonical preceding PREDICT then ACT TRY |
| Record pair k4 | 2rows: (0,0,5), prior T, rule6 outcome T /rule7 F; matched/mismatched |
| Record pair k5 | 2rows: (0,7,9), prior absent, rule8 outcome F /rule9 T; predicted=null and unavailable in BOTH |
| Quiz answer pair k6 | 2rows: rule6/7 generated reveal instances, explicitly supplied TTFFTF /FFTTFT; no hidden quiz-accuracy claim |
| Reveal pair k7 | 2rows: distinct authored public IDs, zero TRY budget, unrevealed; both targets ACT QUIZ ? |

The first seven pairs swap COMPLETE targets between their two existing group slots:
14 changed rows, seven nontrivial pair swaps. The two reveal rows remain common.
Each group's full target multiset is identical across arms. New counts per arm:
64PROSPECT,64REVISE,56ADDITION,56COPY,8TRY,4RECORD,2QUIZ,2REVEAL.
Each retained anchor family has28 examples of each of its two train templates.

Recipe: fresh frozen base, single rank8/alpha16/dropout.05 LoRA, LR1e-4, seed0,
epochs4, batch8/accum1, AdamW, max_len512, group shuffle, no packing/warmstart.
256rows/32groups/128updates;512conditional and64bridge presentations/fit.
Each anchor family has224presentations instead of256 (12.5% reduction).
Equal conditional examples/updates is NOT equal token mass, padding or gradient
contribution; no preserved behavioral performance or equivalence to old fit is claimed.

## Source/partition custody and target truth

Exact original generators/specs are reused; probe private renderer/target helpers are
loaded from its pinned raw bytes, without modifying the probe. No directory-glob
corpus import. Hidden rule functions choose the predeclared authored contrast sources;
output target truth for records is derived only from the resulting PUBLIC execution.

The exclusions contain all21 distinct frozen-probe TRY/record/revision/quiz triples.
First lexicographic unused triples from0..9 generate TRY rows; the first remaining
rule6/7 and rule8/9 disagreement triples generate the records. Sources never use
formation0–1 or evaluation2–5, current captures, recaps or descendant writes.
Actual new quiz component tuples ALSO have zero overlap with the fixed probe.
Quiz EIDs remain exactly `rule6/birth-protocol-next-A-v1/quiz-0` and
`rule7/birth-protocol-next-A-v1/quiz-1`; no resampling. The rule7 six-item quiz has a
repeated triple: preserve all six ordered items, not a deduplicated quiz.

candidate.replacements records each removed row plus its bridge_case (public input,
example target, complete source action/outcome/reward/quiz triples and derivation).
candidate.source_records includes active original provenance plus16new authored
events. These metadata/example fields are outside model context; only the rendered
context is the false-loss span and the assigned complete target the true-loss span.
All source IDs/rule EIDs remain outside bridge prompts. New rows are explicitly
authored NOT_CLEAN/not own-wake; original background provenance is unchanged.
Record inputs explicitly supply observed fields: this is scaffolded faithful
serialization, not unaided extraction. Supplied forecasts/quiz labels are not induction.

## Token audit and mismatch behavior

Actual v3 segments must equal rendered-prefix + target + exactly one supervised EOS;
context and actual batch padding are -100, positions/segment IDs are checked, and
every row is one isolated sequence. Any overflow, empty target, drop/split/truncation,
special target token or encoder/collator mismatch raises before an export.
No change to the trainer's exposed overflow='truncate' recipe: audit rejects anything
that would actually truncate. No dose/prompt/source substitutions are performed.

Reports retain both arms'256 encoded rows (rendered context/input IDs/labels/lengths),
all128 actual optimizer batch index lists, per-arm128 batch costs and fit totals.
Costs include context/full input, target INCLUDING EOS, padding, padded input and EOS.
Whole-target sequences swap exactly; same-row prefixes match across arms. Cross-swap
prefix lengths and per-batch length/position/token multisets/padded widths are compared.
If these exposure comparisons differ, report actual exposure_mismatches and totals;
do not rerender/reselect rows. Callback status is always
`OVERLAY_CALLBACK_AUDITED_NOT_NATIVE`, never native certification.

Native wrapper returns `NATIVE_OVERLAY_TOKEN_MATCH_VERIFIED` only with equal audited
exposure, otherwise `NATIVE_OVERLAY_EXPOSURE_MISMATCH_NOT_READY`; the latter is NOT
exportable by export_native. Neither status authorizes fitting. Required local pins:
config.json/tokenizer.json/tokenizer_config.json plus present vocab/merges/special/
added-token/standalone-template files; external chat_templates directories rejected.
Pins rechecked after audit. No actual native compatibility or totals known yet.

Original birth audit/export functions reject an overlay by design and are NOT
monkeypatched. To assess original conditional preservation later, use the original
birth candidate/readout/scorer with assigned_arm='AUTH' for BOTH new arms. Keep the
fixed16/32-call probe unchanged; Main's separate prompt amendment is not imported.
The old formatting-sensitive probe metric is not relabeled pure semantic correctness.

## CPU tests, commands, hashes

From the repo root, with `/tmp` helper files present:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B /tmp/test_astra_birth_protocol_overlay_20260913.py -v
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tmp:. python3 -B -c 'import astra_birth_protocol_overlay_20260913 as p; print(p.audit_candidate(p.build_candidate()))'
```

25 CPU tests PASS in5.947s; tests403lines. Includes independently checked generator
arithmetic, lexicographic selection, every fixed-probe exclusion,14swap/two-common
mapping, unchanged240/background exports, dev preservation, wrong/null controls,
actual v3 schedule/collator masks/EOS/exposure, mismatch/overflow/partial rejection,
and mocked offline native-loader/hash/export paths. No tokenizer/model files were
created or loaded; native tests use virtual paths and a fixture tokenizer only.
Fixture example totals/arm:47128full input,8896target,79136padded input,32008padding,
1024EOS across128updates. These are NOT native measurements or comparable old-fit dose.

- Module SHA256: `0ff24737771837eb567771b5f13362e537b3e085d26c0b5740e90a1e5fda1ea8`
- Tests SHA256: `25f2ff1bf2f3062dcab1d7e87d993d68773766d9681df2149c659a6296721c7c`
- Candidate digest: `ea8a90b1e358032f409434e101557a973c5c11e1879af382177df6d3fd0967da`
- Raw BRIDGE_AUTH corpus digest: `0293f12741993723a6d2bc6dc799f900598d6ca42e006303232b30b85ee12e7e`
- Raw BRIDGE_DERANGED corpus digest: `28fb113ba7f8cb562e6f965378e768f65cdf4b34620c79a06c26eb78105cfeaf`
- Frozen probe candidate remains `9c680f2010cd11b0116517383281764432f4351628f23059b1c9ee69a283e300`;
  call map remains `9f960c825d02a04fad40e86afd2e822ee52e7ea376a4fd198c0c1b74f5c064a6`.

EDITSTOP. Ready-queue data only. Prompt ambiguity, native exposure compatibility and
Main's prospective selection remain unresolved; no teacher, child-learning, efficacy,
useful-write, persistence, full birth, deployment-gym, H1/H2 or clean-lineage claim.
