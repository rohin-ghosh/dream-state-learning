# Own-write offline reducer — EDITSTOP

Source/test freeze reverified against policy v5 **2026-09-13T14:47:20Z**.
Reducer and test bytes are unchanged from the prior EDITSTOP. Main owns integration,
archive transfer, process/GPU lifecycle and any subsequent execution. No native
formation/fit/readout artifact was opened; only source, scope documents and
synthetic test fixtures were read. Main supplied formation failure/policy-v5
context in conversation; no fit/readout outcomes informed this implementation.

## Exact files and acceptance

```text
60d7a3d4bdd69eef804173ce937028e3c1c169fb96b59b8d6772a442824bf1a1  gpu/astra_pcfl_own_write_analyze.py
023280a41a069738f1d3e3bfc6b568bc242a55017357a83798fdd6d5112d92eb  tests/test_astra_pcfl_own_write_analyze.py
```

**23/23 synthetic tests PASS, no skips, 23.007s** against current v5 source;
previous CLI help and AST/whitespace checks PASS. No dependency
installation, model/tokenizer loading, numerical training, GPU/remote/network
calls, commits, or other-owner edits. Full-roster fixtures use153 tiny synthetic
responses per arm and fabricated200-update/state/checkpoint receipts, not real
training or native evidence. Boundary tests also use isolated17-address data.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B tests/test_astra_pcfl_own_write_analyze.py -q
PYTHONDONTWRITEBYTECODE=1 python3 -B gpu/astra_pcfl_own_write_analyze.py --help
```

## Concrete API / archived directory shape

```python
from gpu.astra_pcfl_own_write_analyze import analyze, markdown
result = analyze(relocated_archive_root, independent_manifest_file_sha256, pins)
text = markdown(result)
```

`pins` has exactly four keys: `formation`, `fit`, `readout_AUTH_WRITE`,
`readout_NO_WRITE_C0`. Each value has exactly:

```json
{
  "completed_sha256": "<independently retained stage completed.json FILE hash>",
  "outer_path": "/ABSOLUTE/RELOCATED/that-stage-outer",
  "collection_sha256": "<independently retained outer collection.json FILE hash>"
}
```

The main archive retains the existing command-root layout: `manifest.json`,
`spec.json`, `measurements.json`, and the four named stage subdirectories,
including complete actor sidecars, formation records/service, writer receipts,
update log, and saved adapter files. Each outer archive is the existing
single-stage outer directory, including collection, input snapshots,
stage_completed copy, binding/context, worker start/exit/release and pre/post
queue/GPU/CVD observations. No reconstructed receipts or partial-arm fills.

CLI saves JSON and Markdown only to a fresh directory outside all archives:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B gpu/astra_pcfl_own_write_analyze.py \
  --archive /ABSOLUTE/RELOCATED/command-root \
  --manifest-sha256 INDEPENDENT_MANIFEST_FILE_SHA256 \
  --completion-pins /ABSOLUTE/completion-pins.json \
  --output /ABSOLUTE/FRESH/analysis
```

All pin values are complete file-byte hashes, not object seals. API performs
no writes; CLI validates before export. Do not point at active outputs or
calculate supposedly independent pins solely from the archive under review.
The main archive must differ from its recorded original root. Original outer
directory locations are not stored by the outer schema, so caller-supplied
outer relocation/authenticity remains Main's responsibility.

## Frozen endpoint and reporting

- Primary: ordered17-address W8 strict_stop vectors for AUTH_WRITE and
  NO_WRITE_C0. Exact-service17/17 AND AUTH>=15/17 AND C0<=2/17 AND paired
  AUTH-minus-C0 difference>=13/17 yields only
  `SCOPED_OWN_WRITE_ACQUISITION_PASS`; otherwise the narrow endpoint is FAIL.
- Missing/failed arms, missing receipts, changed sources or inconsistent joins
  are evidence errors, not scored zeros. A present malformed/nonexact/truncated
  response is a primary zero. Even byte-exact text with finish_reason=length
  is strict_stop zero. Semantic scores never replace strict_stop.
- W8 vectors split EVENT8 / EVENTS_AT6 / LINKS_FROM3. W0–W7 retain ordered
  strict/semantic vectors as repeated trained-surface diagnostics only.
- Every raw string and authentic target is retained without normalization;
  exact bytes, strict_stop, semantic/semantic_stop, refusal, usable false-row,
  finish/truncation, changed strings, and token counts are reported. Strata:
  all, each wrapper, each query kind, each wrapper×kind.
- Exposes12 source rows,17 address blocks,20 scheduled blocks,160 unique
  encodings,800 presentations,200 recorded updates, one life/root/fit/init,
  exact adapter inventory, initial/final LoRA/optimizer hashes and lineage.
- Costs explicitly separate stage elapsed, cold-load elapsed, actor-operation
  elapsed, response-operation sum, generation-wall sum, and outer elapsed.
  None is labeled GPU-active; no-write is not compute-matched.

## Provenance and policy boundary

Reuses the existing archive reader, scoped writer/formation provenance
validators, core authentic-query compiler/service and unchanged memory scorer.
Verifies current loaded source pins, original prepared input pins, sealed
manifest/config/report/fit/encoding, native formation capture file hashes,
exact200-update schedule/source joins, saved checkpoint files and cold route
identity, all153 raw/render/token/response/score joins per arm, stage inventories
and independent completion hashes. Existing outer collection inventories and
release observations are checked read-only; no lifecycle controller is run or
re-engineered. This is recorded evidence verification, not a fresh hardware
observation or tensor/numerical rerun. Retain the recorded source tree/path
layout for existing source validators; source drift fails rather than silently
accepting a newer implementation.

Current formation policy is
`public_session_history_whole_response_stop_only_format_public_pair_semantics_v5`.
Its unchanged pair policy `requested_preselected_already_admitted_event_handles_v1`
is copied from the validated report/config and exported. The generic VIA and
EVIDENCE-order explanation changes no reducer schema or endpoint. Result/Markdown explicitly say
**controlled curriculum record task**, no autonomy/discovery. Formation
`format_scaffold` is preserved and labeled **external format assistance**.
The bounded claim is controlled own-record cold address-to-block reproduction
only: no selectivity, preservation, generalization, causal/population inference,
significance, learning/H1/H2/C11, full-assay qualification or route repair.
The failed previous formation is not admitted to this reducer or relabeled.
Main's reported19-call failure remains ineligible: missing complete formation,
fit or either readout is an evidence error, not a zero-filled scored endpoint.
No attempted prompt run or failure receipt was inspected here.

Current formation source used for the v5 synthetic compatibility rerun:
`gpu/astra_pcfl_own_write_dev.py`, SHA256
`81afdfb6e176c68aa66a96d70c2ab03378392a683c7beca05cede3af8a8ef7ed`.

Adopted scope-document pins:

```text
923353789811390724ea47f43d18685b25c4d9618e22a9616249039e738a2439  research_notes/analysis/2026-09-13_pcfl_own_write_reducer_freeze.md
0c72969569bae19ed8e16b46baa90d17934dc2d28fd5c1161733200e6e0dc84e  research_notes/analysis/2026-09-13_pcfl_own_write_prelaunch_audit.md
```

The old prelaunch audit's outer HOLD is not reissued here; Main reports that
controller already committed/tested. This handoff freezes only the reducer
and its tests, and does not authorize or perform a launch. **EDITSTOP.**
