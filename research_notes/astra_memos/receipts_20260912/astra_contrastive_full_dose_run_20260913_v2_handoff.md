# EDITSTOP — v2 material serialization regression tests

2026-09-13. Non-material repair coverage only; no scientific protocol change.
Main owns and edits the v2 runner and outer launcher. This sidecar owns only
the new test file and this handoff. Original files remain unchanged.

## Frozen test artifact

`/tmp/test_astra_contrastive_full_dose_run_20260913_v2.py`

SHA256 `b680d2123f496e405e203fe7a9859deb9b55a3ca177e3d5f766008695fd0333e`

Runner bytes tested, read only (Main-owned):
`/tmp/astra_contrastive_full_dose_run_20260913_v2.py`

SHA256 `ddd36b16e188a2c2bfa11e61e8fbed66fed67d93f81b1d4fa6384c04dd43c025`

This handoff's final SHA256 is reported separately, not embedded in itself.

## Exact regression and retained coverage

Cloned the 32 original CPU tests, changing the imported runner path/module name
to v2, and added two tests using the actual frozen material generator and archive:

1. `test_actual_in_memory_build_roundtrip_fails_v1_passes_v2` calls the original
   `material.load_corpus(SOURCE)` and `material.build_dataset(corpus)` directly.
   The unroundtripped object is not Python-equal to archived JSON because of
   provenance tuple/list representation. Its complete canonical serialized
   bytes equal the archived member bytes exactly, and hash to the frozen
   `7f9045242e98dc05b85f814574a1eb87cacebf463af88dcca60729c4aa5ebd66`.
   JSON-roundtripped values also equal the archive, including all provenance.
   Calling the pinned, unchanged v1 importer rejects this object with
   `historical dataset differs`; calling Main's v2 importer accepts it, preserves
   its canonical bytes without mutating the input, preserves archived member
   values/hash, imports exactly 48 OFF responses and makes zero new calls.
2. `test_modified_generated_values_still_rejected` separately changes a training
   target, source ID, input prompt and provenance. Each has different canonical
   bytes and is rejected by v2. This is not a lossy normalization or source check
   exception. Existing native-prompt/row and base-binding rejection tests remain.

The original 32 tests retain source/mask/seed/dose checks, toy-tokenizer encoding,
mocked fit/readout/process lifecycle, exact historical OFF custody joins, original
strict scorer replay, once-only collection, and individual canary-loss reporting.

## Commands and results

`python3 -B /tmp/test_astra_contrastive_full_dose_run_20260913_v2.py`

**34 tests PASS, 12.493s.** AST parsing and trailing-whitespace checks also PASS.
Runner hash was checked before and after the test run and was unchanged.

Preserved original runtime SHA256:
`663879c3ccec0c0543a6de5eff60e2e92f7482d9f0c1db3879722aa988452bd0`

Preserved original tests SHA256:
`a2e39fe41b4b55c210c4b12f9701c77205d36288ede49097d4a77b0b3ab2341b`

## Limits / Main handoff

No native preparation, model, native tokenizer, GPU, network, Git, fit or
collection calls were performed. Tests use the real archived responses as
read-only evidence, not a new endpoint. Main's reported three failed native
preparations (0 fits / 0 calls) are not modified or reopened by these tests.
Use only Main's fresh attempt2 roots and v2 runner/spec/launcher pins. Main owns
all native prechecks and preparation after this EDITSTOP. Passing CPU regression
tests is not native feasibility evidence or a scientific result.
