# Reflection/correction uptake CPU handoff — September 13, 2026

**EDITSTOP. Stable CPU corpus/export/scoring interface for Main's separate native
runner.** Only the two assigned new repository files and this handoff were
created. No existing source/tests, manuscripts, receipts, or original handoffs
were changed. No Git, network, native tokenizer/model/GPU operations or training.
The application table and focused tests were written and passed before Main's
perception-closure message; no retuning followed that information. This remains
a separately preselected authored diagnostic, not a claim or teacher distillation.

## Pre-execution construct repair

Main identified a missing referent in the old withdrawn restatement prompt.
Before any native run, the **same** `nondeictic_event_procedure_v1` transform
now removes `Your parent said:` framing and replaces the deictic restatement
request in both present and withdrawn arms. The new task is:
`Summarize the selected public event and state a reusable recording procedure in 2-3 sentences.`
All public-event bytes, authored response targets, source proofs, loss contract,
historical exact metric labels, ordering, and DEV exclusion are preserved.
Application rows and request digests are unchanged. This is a prospective
construct-validity repair requested by Main, not outcome-based retuning.

API/schema names and payload keys are unchanged. Restatement `manifest.audit`
now explicitly records `prompt_transform='nondeictic_event_procedure_v1'`,
`historical_prompt_bytes_preserved=false`, and an explanation in
`identical_across_parent_conditions`. Historical **prompt** byte preservation
is no longer claimed. Re-export both training arms and restatement DEV requests;
do not reuse the previous prompt exports under the repaired source identity.

## Changed paths and final SHA256

```text
b69dfe4ab39e60fab826e67758d21e708c87d538f3fcd2b8a579bb778b0ace80  organism_v6/birth_reflection_probe.py
9b8aff58e3bb58df7de813e4319340e1966b1f6b3b1a1d412bc62d181a91e860  tests/test_birth_reflection_probe.py
```

Handoff path: `/tmp/astra_birth_reflection_probe_handoff_20260913.md`.
Its own SHA256 is returned separately, not recursively embedded here.

The module verifies these historical dependency bytes before construction:

```text
078ceba07141b5f6fb2159a12e21f1eccc0901ba9f51f52d1793d988927812f6  organism_v6/birth_skill_corpus.py
e6055da48b2c6fa1bd294c9d991e07f32f05dc6630fe8973373977bdfe977526  organism_v6/rulegame_parenting_diagnostic.py
```

These are required in Main's immutable source snapshot alongside the new
module and package initialization. No import of torch, transformers, peft or
vllm is required or made by this module. The existing parser is accessed through
the historical corpus's bounded AST definition loader.

## Stable construction and export API

```python
from organism_v6 import birth_reflection_probe as probe

train_present = probe.build_panel(
    'restatement', split='train', parent_condition='present')
train_withdrawn = probe.build_panel(
    'restatement', split='train', parent_condition='withdrawn')
present_export = probe.export_training(train_present)
withdrawn_export = probe.export_training(train_withdrawn)

restatement_dev = probe.build_panel(
    'restatement', split='dev', parent_condition='withdrawn')
application_dev = probe.build_panel(
    'application', split='dev', parent_condition='withdrawn')
restatement_requests = probe.export_development(restatement_dev)
application_requests = probe.export_development(application_dev)
```

Use `present` instead of `withdrawn` for the paired readout condition. No model
states or six-cell runtime are constructed here. There is no seed-selection
parameter, model path, training call or write method. Ordering uses the existing
corpus order seed20260913 and does not set the native optimizer/engine seed.

### Parent withdrawal — precise treatment

- Generic system is explicitly fixed to **`You are a helpful assistant.`** in
  every row, both conditions and both panels. The native runner must render
  those explicit roles rather than rely on tokenizer-inserted defaults.
- Historical public-event bytes and all authored targets are preserved from
  `build_slice('reflection', ..., system_anchor=GENERIC_SYSTEM)`. The same
  nondeictic task replacement and parent-framing removal are applied to **both**
  arms before withdrawing the correction. This is a labeled prompt transform,
  not historical prompt-byte preservation.
- `withdraw_parent_correction(user_text)` requires exactly one standalone
  `\nPUBLIC_CORRECTION\n` and replaces it with one newline. No public event,
  generic system message, transformed task text or application choice differs
  across arms. Neither restatement arm contains `Your parent said:` or a request
  to restate absent content. The correction remains a standalone paragraph when
  present; no dangling parent label is introduced when it is withdrawn.
- `system_anchor=None` in the historical builder is explicitly regression-tested
  as insufficient: it does not remove the user-message correction.
- Both TRAIN conditions have exactly12 rows in identical order, identical
  targets, and **2,838 target UTF-8 bytes**. These are bytes, not token counts.
  Both DEV panels have12 rows per condition. Application has no TRAIN mode.

### Exact schemas

JSON normalization for object digests is UTF-8
`json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False)` with
default separators and **no trailing newline**. Text hashes use exact UTF-8
bytes. CLI printing appends a newline; its whole-file SHA is therefore distinct
from the exported object/records digest.

**Panel bundle**, schema `birth_reflection_probe_v1`:

- Top-level keys: `schema`, `manifest`, `rows`.
- Common row keys: `row_id`, `panel`, `split`, `parent_condition`, `source`,
  `source_proof`, `input_messages`, `response_target`, `input_sha256`,
  `target_sha256`, `score_kind`.
- Restatement adds `historical_row_id`. Application adds `choices` (structured
  proof-side claims keyed A/B) and `option_texts` (the displayed choices).
- `input_messages` is exactly a two-item list of `{role, content}` dictionaries,
  with roles `system`, `user`. No IDs, hashes, proof annotations, answer metadata
  or case labels are rendered. Application A/B alternatives necessarily occur
  in the prompt; the supported-choice annotation does not.
- `response_target` is a whole historical authored prose string for restatement,
  or one bare letter `A`/`B` for application. It contains no assistant prefix/EOS.
- `manifest` keys: `origin`, `panel`, `split`, `parent_condition`, `generic_system`,
  `parent_correction_sha256`, `historical_source_sha256`, `order_seed`, `row_count`,
  `rows_sha256`, `audit`, `training_export_allowed`, `native_ready`,
  `scientific_claim`, `auto_promotion`, `curriculum`, `claim_limit`.
- `validate_panel` reconstructs the exact canonical panel and compares the whole
  value, not merely a supplied digest. `score_response` similarly validates its
  row. Corrupt metadata/material raises `ValueError`; it is not a scientific miss.

**Training export**, schema `birth_reflection_probe_v1/training_export`:

```text
{
  schema,
  records: [{input_messages: [{role, content}, {role, content}],
             response_target: "entire authored assistant response"}, ...],
  report: {
    panel_manifest, record_count, application_rows: 0, dev_rows: 0,
    records_sha256, row_ids_in_order, targets_sha256, target_utf8_bytes,
    mask_contract, six_model_readout_cells
  }
}
```

Only `records` supplies training input/target data. Keep `report` out of model
input. `export_training` accepts only validated historical restatement TRAIN;
DEV relabeling, appended application rows, altered targets and recomputed
tamper hashes are rejected. One group per row can be assigned using its index
or the report's corresponding row ID, without rendering that ID.

**Development export**, schema `birth_reflection_probe_v1/development_export`:

```text
{
  schema,
  requests: [{input_messages: [{role, content}, {role, content}]}, ...],
  scoring_rows: [complete private-to-scorer rows, ...],
  report: {panel_manifest, row_ids_in_order,
           scoring_rows_are_model_input: false, training_allowed: false}
}
```

Pass only `request['input_messages']` to the model. `scoring_rows` and the report
remain outside requests. Align results by the supplied row order/IDs; do not
send the whole export object as chat content. Training and scoring payloads are
deep-copied to avoid cross-payload mutation.

### Scoring API and raw preservation

`score_response(row, raw_response)`:

- Restatement returns historical `passed` and
  `score_kind='exact_authored_restatement_only'`, plus unchanged `raw_response`
  and `semantic_prose_score=None`. A different truthful paraphrase is not an
  exact-fixture pass; this does not label it semantically wrong. No substring,
  suffix-only or permissive free-prose heuristic exists. Descriptive manual
  review can be separate later.
- Application returns `score_kind='strict_application_choice'`, `syntax_valid`,
  `passed`, `failure`, and unchanged `raw_response`. Only exact Python strings
  `A` or `B` are syntactically valid. Wrong bare choice is `wrong_choice`;
  whitespace, fences, explanations, punctuation, JSON strings, Unicode lookalikes
  or non-string inputs are `invalid_choice_syntax`. No trimming/normalization.
- `semantic_choice_proof(source, choices)` proves which of the **frozen structured
  alternatives** agrees with public evidence. It does not interpret generated
  prose. Exactly one supported choice is required; bool/int type drift, invalid
  sources, false origins, and ambiguous pairs are covered by fixtures.

`score_panel(bundle, responses)` takes a complete dictionary `{row_id: raw}`
with exactly the expected12 keys. It returns schema
`birth_reflection_probe_v1/scores`, `panel`, `parent_condition`, `passed_count`,
`total`, per-row `results`, `scientific_claim=false`, `auto_promotion=false`.
It keeps raw invalid responses in the returned results. A missing/extra/list
inventory raises `ValueError`; Main's capture layer must retain partial/raw
artifacts and must not call this a completed panel or a measured zero. Duplicate
capture IDs must be detected before constructing the dictionary; a dictionary
cannot preserve two values for one ID. Keep restatement and application
reductions separate; no mixed composite success metric is supplied.

## Application panel, proofs and shortcut limits

There are12 authored hypothetical public situations: six cases × two selected
triples, with two visible events per situation. Selected triples are
`(31,-17,8)` and `(-23,19,6)`; distractor triples are `(41,42,43)` and
`(-31,-32,-33)`. Both selected and distractor triples/events are checked disjoint
from **all events** in the historical train/dev sources. Opposite outcomes for
the same triple belong to different hypothetical boxes, not one inferred world
rule. The six cases are matched true/false, mismatched true/false, and absent
prediction with true/false observation; each occurs twice.

The public parser derives the selected event's TRY, observation, prior prediction
and relation. The supported candidate includes those values and the corresponding
authored reusable procedure. Foils flip prior prediction in the first box,
observation in the second box, or invent a prediction when absent. Derived
relation/procedure fields follow each foil consistently, so truth is established
against the public source, not by an internal contradiction or a marked answer.
Correct A/B order is frozen,6/6 overall,1/1 within each semantic case and3/3
within each selected triple. Option rendering uses the same template for both
choices. Source proofs bind e1, never the distracting e0.

**Do not oversell shortcut resistance.** The audit explicitly reports in-sample
label-lookup baselines, not measured model accuracy:

- Constant, case-only, triple-only, prediction-only, outcome-only and relation-only:
  **6/12 each**.
- Triple+prediction: **10/12**; triple+outcome: **8/12**;
  triple+relation: **6/12**.
- Ordered choice texts with no event: **10/12** maximum in-sample lookup. Two
  identical ordered choice pairs require opposite answers from different source
  events; the other rows still permit option-only memorization.
- Case+triple uniquely identifies the authored row and memorizes **12/12**.

These residual composite/lexical shortcuts are disclosed and tested, not hidden
behind a universal omission-factor guarantee. This tiny frozen DEV panel is
near transfer on a shared semantic substrate, not general reflection, independent
learner replication, persistence, parenting efficacy, L2 or H1/H2 evidence.
No thresholds, mixture training or automatic promotion were added.

## Minimal native adapter guidance (Main-owned)

1. Snapshot the new module and exact historical helper bytes; retain the CPU
   reports/digests below. Export two12-row training arms and both12-row DEV
   panels for each parent condition. Do not include application or any DEV
   row in fitting; do not warm-start from a perception adapter.
2. Render `input_messages` with the bound native chat template and assistant
   generation prefix **once**, preserving the explicit generic system. Mask all
   context/prefix tokens. Supervise **every response_target token plus exactly
   one assistant EOS**. If the runner supplies EOS manually, disable any trainer
   auto-add path; if the trainer adds it, do not put an EOS in the target first.
   Check native EOS identity, whole-response boundaries, zero truncation/drop/
   nonfinite skips and actual label counts. Do not supervise only the reusable
   final sentence or call the byte-mask fixture native tokenization proof.
3. Reuse Main's existing full-assistant mask and fresh-process engine patterns.
   One fresh base/optimizer/adapter per arm; identical authored targets/order,
   chosen dose and seeds. Expose differing prompt/padded tokens rather than
   asserting compute equality. This module selects no optimizer recipe.
4. Build the six states separately: matched OFF, trained-present and
   trained-withdrawn × correction-present/withdrawn. Each readout cell has
   **12 restatement +12 application requests**:144 calls total. The model-state
   labels are runtime metadata, not prompt fields. Use LoRA-enabled matched OFF
   without an adapter request, not a prior disabled-LoRA control.
5. Preserve all captures and finish/truncation/work metadata before reducing.
   Reducer inputs must be unchanged raw response strings; never remove fences
   or trailing whitespace. Keep two primary metrics separate. Native launcher,
   budget, EOS/tokenizer acceptance, output custody and model source binding are
   Main's next work; none was executed here.

No reason to wait for this sidecar before analyzing the completed perception
fits. No conclusions or favorable seed/recipe choices were taken from them.

## CPU commands and exact results

Run from `/data/home/rohing/dream-state` (no bytecode/cache output):

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -p test_birth_reflection_probe.py -v
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -p test_birth_skill_corpus.py -v
```

- Post-repair focused suite: **40 tests PASS in1.566s**, zero failures/errors/skips.
- Unmodified historical corpus regression: **22 tests PASS in0.178s**, zero
  failures/errors/skips. **62 tests total**. Earlier pre-repair acceptance was
  38 focused tests plus22 historical; it does not pin the repaired prompt bytes.
- Additional standard-library construction/export/self-score check: both TRAIN
  arms have12 records and matching target digest; all four DEV panel/condition
  exports have12 requests; fixture targets self-score12/12 in each. These are
  target self-consistency checks, **not model scores or native proof**.
- Focused coverage includes full historical target/event-byte preservation;
  the identical labeled nondeictic transform and absence of missing referents
  in both arms; rejection of unexpected historical framing/task drift; explicit
  user-message withdrawal; generic/task/event parity; application case/order
  balance and literal isolation; source-derived candidate truth/type checks;
  residual shortcuts; strict syntax/no score rescue; exact prose/no suffix score;
  no DEV/application training; anti-relabel/tamper validation; full-response+EOS
  **byte-token reference fixture only**; clean request/export separation;
  raw failures/inventory checks; stdout CLI and no native-library imports.

CLI (JSON to stdout, no file writes or native execution):

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B -m organism_v6.birth_reflection_probe training --panel restatement --parent present
PYTHONDONTWRITEBYTECODE=1 python3 -B -m organism_v6.birth_reflection_probe training --panel restatement --parent withdrawn
PYTHONDONTWRITEBYTECODE=1 python3 -B -m organism_v6.birth_reflection_probe development --panel restatement --parent withdrawn
PYTHONDONTWRITEBYTECODE=1 python3 -B -m organism_v6.birth_reflection_probe development --panel application --parent withdrawn
```

Use `--parent present` for the other DEV condition. Application training is a
CLI error, not an empty or silently filtered export.

### Exact frozen export digests

```text
TRAIN present records:    b7ce09ba00fb1c95bcdffd641b14d0d40178fa8ad4c9d47efc0cc59922ae2f21
TRAIN withdrawn records:  cf610fe611a92ef57ec869e0f2d20b9458ef169420c421be5a38034dbe1df42d
Both ordered target lists:60b2b0a94bc0b4fdb8b9eda3cd6ff30c59ed969a992cd58863b2970f8dcfc6ac
DEV present restatement requests:   c5bf73cb2b899e7924348238e724ce13b3bb02e0dc2ec98abaeb3a4c1a4a12d5
DEV withdrawn restatement requests: bbe940759df8114fce677239db772ad9102d3a272f2b0be40e03f918a0f78cac
DEV present application requests:   2055f1365271d498c97814a348799b05ff43b963feb521b1a911bb3a9d5526e9
DEV withdrawn application requests: 672b61954088ed48ef6381de617d9ebca8ab09de344a3749183ae86cddb44409
```

Six complete row-list hashes (TRAIN/DEV variants, **not six model cells**) are
also fixed by `test_frozen_rows_have_exact_output_blind_digests`.

## Remaining gaps

No native chat-template/token-count/mask/EOS verification, model loading,
fresh-fit execution, six-cell runtime, resource control, learning measurement or
manual semantic prose review was done. The byte-mask reference and source-pin
mock are CPU fixtures, never native proof. Application residual shortcuts and
historical exact-prose limitations remain explicit; no claim is rescued by a
second scorer. Main can build the bounded runtime now against this frozen API.

EDITSTOP
