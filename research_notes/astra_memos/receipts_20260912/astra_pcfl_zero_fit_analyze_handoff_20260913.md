# Bounded independent C0 archive analyzer — EDITSTOP

Frozen 2026-09-13T13:37:17Z, without inspecting any active/native run output.
This is a non-material offline audit addition: no architecture, prompts, task
IDs, scorers, denominators, thresholds, collection, or process-release changes.
Only the following three owned files were written. No commits, GPU/remote/
network/model/tokenizer calls, or changes to another owner's files were made.
Main retains all collection and process-release ownership. This timestamp does
not assert when Main did or will inspect outcomes; this worker inspected none.

## Frozen files and SHA-256

```text
a84f677e1b41512c0eabfd3865eafb55ec85584e53e99796175334e1bf1db00e  gpu/astra_pcfl_zero_fit_analyze.py
f4021ab77420fa07b9bcbc1443bf973670a856e51a59f1ba8e82acbd6e066d01  tests/test_astra_pcfl_zero_fit_analyze.py
```

Analyzer: 297 physical lines. Tests: 323 physical lines, tiny explicitly
synthetic receipt fixtures (one task, up to thirteen conditional calls).
This handoff's own hash is reported separately after writing, not recursively
embedded in itself. Its exact path is
`/tmp/astra_pcfl_zero_fit_analyze_handoff_20260913.md`.

## API and required archive layout

```python
from gpu.astra_pcfl_zero_fit_analyze import analyze, write_analysis

result = analyze(
    diagnostic_dir,
    outer_dir,
    manifest_sha256=main_pinned_manifest_file_sha256,
    collection_sha256=main_pinned_collection_file_sha256,
)
write_analysis(result, fresh_output_dir)
```

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B gpu/astra_pcfl_zero_fit_analyze.py \
  --diagnostic /ARCHIVE/diagnostic \
  --outer /ARCHIVE/outer \
  --manifest-sha256 MAIN_PINNED_MANIFEST_FILE_SHA256 \
  --collection-sha256 MAIN_PINNED_COLLECTION_FILE_SHA256 \
  --output /ANALYSES/FRESH_DIRECTORY
```

Paths and uppercase hash strings above are placeholders, not existing run
locations or hashes. Do not use them literally. Main must first complete its
existing collection/finalization and preserve the two byte hashes independently
of these relocated archives. They are SHA-256 of entire file bytes, not the
JSON objects' internal `sha256` seals. No new archive-envelope schema is needed.

Provide two separate, relocated, unaliased directories, retaining every relative
filename and exact byte from the completed diagnostic and outer output trees:

- Diagnostic: `manifest.json`, `report.json`, all `task_NNN.json`, all
  `call_NNNN_request.json`/`call_NNNN_response.json`, and the complete `actor/`
  subtree (`config`, `identity`, `load`, `close`, per-call request/render/raw/
  response receipts, and all `count_NNNN.json` READ receipts).
- Outer: the complete successful output tree, including `collection.json`,
  `capture_complete.json`, `context.json`, worker/queue/GPU/CVD observations,
  release attestation/receipt and `final.json`, plus all other inventoried files
  and stdout/stderr logs. Do not omit logs merely because they are not parsed.
- Do not add a README, checksum file, analysis, or other unregistered file inside
  either archive. Outer collection hashes bind its full inventory; capture binds
  the diagnostic full inventory. Symlinks, extras, missing files and byte drift
  reject. The original native absolute paths inside receipts remain unchanged;
  the analyzer never follows them to reopen native outputs/model files.

`analyze` is read-only. The CLI creates `analysis.json` and `analysis.md` only
after successful evidence audit, in a new directory whose parent already
exists. Reusing an output directory fails; there is no force/overwrite switch.
The CLI forbids nesting analysis inside either archive. Missing/inconsistent
evidence raises an exception/nonzero exit and produces no success analysis.
An interrupted write leaves its fresh directory for preservation, not reuse.

## What is independently replayed

- Exact driver task expansion and seals: 800 fixed tasks, 640 delayed/160
  reachout, four excluded roots, 1952 maximum conditional C0 call slots.
  No task/root substitutions, denominator shrinkage, retries or new thresholds.
- All per-task raw final outputs, READ service histories and scores are replayed
  through the existing runtime `_task` and core route/probe/memory scorers;
  task files and ordered report rows must match type-sensitively. No model runs.
- Manifested prompts/IDs/seeds and exact continuation messages must match the
  driver and native request receipts. Native C0/no-LoRA identity, frozen Qwen
  revision, source/environment/config/model-file receipts, tokenizer file pins,
  render hashes, raw prompt/output IDs and response byte/hex/decoded receipts
  are cross-bound. Token/read/context/time caps and sampling remain unchanged.
- Existing tokenizer measurement seals and within-group checks are replayed;
  exact initial-task coverage is required. Every RA/RB mate must retain the
  declared RA-minus-RB length difference of one token. Service-token receipts
  must agree with the measured exact block/MISS surfaces.
- Declared panels are recomputed with the existing driver `_panels`, including
  original minimum/maximum counts and false-row checks. A complete negative or
  partial-performance result remains negative/partial, never retried or relabeled
  as threshold success. Execution-incomplete evidence is rejected, not imputed.
- Termination `length` is counted, not turned into a new scoring penalty. Invalid
  final syntax and invalid READs are separately counted; syntactically valid but
  wrong routes remain ordinary scored failures. READ attempts, served READs,
  service token-count operations, attempted counted service tokens, accepted
  returned tokens, all prompt/output tokens and truncation counts are retained.
- Aggregate, per-root, panel/projection, render, and root/panel/projection/render
  counts are emitted, with all 800 initial prompt lengths retained in JSON.
  Markdown includes unchanged panel results and stratified count tables.
- All manifest/report/final/collection/capture and release-evidence crosslinks
  are checked. Outer failure artifacts cannot be masked by a successful final
  JSON. Worker success, queue match, GPU compute-vacancy and both final CVD
  observations must be present. Explicit unreadable-service exceptions and
  incomplete CVD visibility remain explicit, not silently upgraded.

## Elapsed costs and scientific boundaries

Seven explicitly named, overlapping elapsed intervals are reported, not summed
into GPU-active time: raw generation wall; actor call-operation wall; all actor
operation wall; cold model-load wall; diagnostic start through close; diagnostic
start through release; original outer entry through finalization. Outer and
diagnostic clock/budget bindings are checked, including cold load and release.

Only excluded-root researcher-authored interface ceilings/failures are in scope.
Zero fits/updates/parents; frozen Qwen2.5-7B-Instruct. RA is one token longer
than RB: no causal order-only contrast or full RA/RB mate qualification.
No learning, H1/H2, clean-ancestry, C11, parenting, or original full-assay claim.

Limits: this audits bounded archived native attestations, not independent model
weight hashing, tokenizer encoding/decoding, or fresh process/GPU queries. The
native decoder's text/token correspondence is cross-receipt verified, not
recomputed by loading a tokenizer. Main's separate allocation/lease authority
is not reissued or independently reconstructed. No native archive was available
or read by this worker; tests establish CPU audit behavior, not native outcomes.
The full 800-task native success path has intentionally not been exercised on
actual outputs. Tiny synthetic fixtures cannot pass production analysis.

## CPU tests and checks

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -p test_astra_pcfl_zero_fit_analyze.py -v
# 26 tests PASS, 0.206 seconds (final frozen analyzer/test bytes).

PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -p test_astra_pcfl_zero_fit_dev.py -q
# 20 tests PASS, 35.236 seconds (unchanged adjacent driver; earlier audit revision).

PYTHONDONTWRITEBYTECODE=1 python3 -B gpu/astra_pcfl_zero_fit_analyze.py --help
# PASS; import/help only, no evidence reads or native initialization.

git diff --no-index --check /dev/null gpu/astra_pcfl_zero_fit_analyze.py
git diff --no-index --check /dev/null tests/test_astra_pcfl_zero_fit_analyze.py
# PASS, no whitespace findings.
```

Tests cover frozen scorer replay, valid and malformed probes/routes, WRONG_ROOT
false rows, exact READ/MISS continuations, the thirteenth READ stop, over-cap
service counts, length-stop scoring preservation, prompt/seed/request/token/
sampling/LoRA/clock/raw-byte mutations, archive changes/symlinks/missing files,
duplicate JSON keys/NaN, externally pinned lineage, negative panel preservation,
fixed-denominator rejection, failure evidence, visibility limits, and fresh-only
output. No fixture is native or an actual tokenizer qualification.

## Source bytes inspected and reused

```text
7bcc99f89b661f2f77202c3cc5aa61533bad2daff25f5b548ed8e1ecd1c1b5d5  gpu/astra_pcfl_zero_fit_dev.py
f6aae63e79213c24523201452e7f7de880167c4fb273db18de83f93a3a4f7a26  gpu/astra_pcfl_native_actor.py
026c6a8c50f551d874a605e1975f5fe2189643fcbd5e6694c0ad2d2fea0544b1  gpu/astra_pcfl_vertical_dev.py
ed1b8c5f1d866e8e036a33c3fbeb278551021413cb63e5b3a35bb72934dae04e  organism_v6/pcfl_vertical_dev.py
c674b152b6147f6f8a698af065c33648eaeea7a309bbb531e2b59d022c19f29c  research_notes/astra_memos/ASTRA_PCFL_ZERO_FIT_SCOPE_2026-09-13.md
e8dce95a44526c0b9560876a34aef47d717019d07aa8437de97d32ebfef4c0ed  research_notes/astra_memos/ASTRA_PCFL_C0_RENDER_SCOPE_2026-09-13.md
```

Outer driver and its implementation handoffs were read for schema guidance only.
At analysis time, all seven existing diagnostic `source_snapshot` file hashes
must match the archived manifest by unique basename, allowing native/local path
relocation but no scorer/source drift. Restore matching archived source bytes
in a separate Main-managed checkout if necessary; do not adapt scorers to
observed outcomes. The pre-existing modification to `gpu/codex/dream_state.rules`
was neither read for content nor edited; it remains another owner's work.
