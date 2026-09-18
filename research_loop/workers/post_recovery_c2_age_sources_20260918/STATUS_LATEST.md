# C2 age sources ready — September18,2026

**Two immutable adapter-only sources are CPU-ready on ovx4 for a later,
separately admitted batch. Neither was enrolled, loaded or evaluated here.**
Main's attempt3 batch/source/epoch/results and all lives were left untouched.

Selection was at **21:58:47.608UTC**, with original C2 journal head11833.
The latest durable COMPLETE at that cut was **11831 / sleep117**; later mutable
live adapter state is not used. Receiving staging finished **22:02:52.412UTC**.

| Source | COMPLETE | Absolute sleep | Optimizer steps | Adapter state SHA256 |
|---|---|---|---|---|
|C2-now|11831|117|7948|`351b8148f815b77d6d193c1a44477cec2be03a90296a118584bade3db60099fc`|
|Preserved C2 baseline|5823|51|4908|`82a988a0ded69ce85723192b366251d21f8ec5fe8466e9ca98202fb09b57ce92`|

Both source records belong to original journal
`260be8b8710a42559b291797c6e14983` and retain frozen-base identity
`a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992`.
Sleep51 is the existing eligible R232 archive, not a new live-adapter export.
Its model file remains
`3c0622810dd279fb7e3a59be9fcff691585c5b1acaeb5053ae21e26571ed8d30`;
the current model file is
`740a732dde0ac7f9f2c61ce9e64b4a9e0db118cdb18be46694088fd36dc56f86`.
File hashes and adapter-state hashes are distinct and are not interchanged.

## Exact receiving paths

On **ovx4**, source directories (each has `SOURCE.json`, `EXPOSURE.json`,
`COMMIT.json` and the three adapter files):

```text
/localhome/local-rohing/orch_post_recovery_c2_age_sources_20260918/sources/C2_NOW_sleep_000117_e6ae76769b29b2ae
/localhome/local-rohing/orch_post_recovery_c2_age_sources_20260918/sources/C2_SLEEP51_sleep_000051_7c6cf68593c1d1f6
```

Append `/adapter` for the evaluator's adapter-only input. Receiving readiness:

```text
/localhome/local-rohing/orch_post_recovery_c2_age_sources_20260918/READY.json
```

The live-node capture remains separately preserved on node5 under this new
worker's receiving root. No checkpoint/journal was modified. Exact existing
`capture_retained.py` performed COMPLETE/COMMIT/base/counter joins and
before-copy/after-copy hash equality. ovx4 reverified both source allowlists and
COMMIT/counter/adapter-file joins. Only adapter files and provenance metadata
were staged: **no optimizer/RNG, parent text, source working context, raw journal
records, images or reference panels were copied into these evaluation sources**.
No evaluation model of any kind was loaded by this task.

## Exposure eligibility and exact coverage

The same original R232 DEVELOPMENT scenes **564,654,703** and their original
image identities were retained. Original/template game and selection hashes
match; original image files were rehashed. Both sources are **eligible under
the recorded-exposure audit**: zero identifier/image-hash matches, zero
fivegram overlap matches, and no unresolved REQUEST content.

Coverage is explicit, not a new full16GB semantic replay:

- Reused the hash-bound original eligible audit through record8875:300 REQUESTs,
  plus its two completed inherited states. Original capture and exposure
  artifact hashes are retained and their source-cut record was canonically
  reverified against the live original journal.
- For C2-now, checked contiguous bounded headers8876–11831 and fully verified
  canonical bodies for **120 REQUESTs,95 INBOXs,2 LOADEDs and30 COMPLETEs**,
  including original LOADED1 and the selected COMPLETE's inherited state.
  Full-body read volume was **2,728,750,773 bytes**, plus5,324,550 bounded-header
  bytes. The2,710 other tail records received header-chain checks, not a false
  claim of full semantic/body replay.
- For sleep51, reused the archive's existing eligible prefix audit, then freshly
  checked canonical LOADED1 and COMPLETE5823/inherited state:3,411,563 bytes.
  That old audit extends beyond sleep51, a conservative coverage surplus—not
  younger state loaded into the baseline evaluation.
- Same conservative overlap rule: at least3 shared fivegrams **OR** shared
  fraction≥0.15. Maximum observed overlap was0 for each selected scene.

**Caveats:** eligibility concerns recorded source-life and retained inherited
context under the original audit plus the new tail checks. The prefix audit is
reused, not independently replayed from all old bodies. This is not a guarantee
about base pretraining, unrecorded ancestral experience, or every semantic
paraphrase. No held-out/generalization/scoring result is claimed.

## Fixed future evaluation binding

Prepared for the same adopted `judge15625-base-v1`, rank8/step15625:

- Judge adapter SHA256:
  `a070b28ef0bf1f57ad994e5bd715db77e2649d196960cea422971523696be3c4`.
- Primary config SHA256:
  `382cff58b32ca9fca80534e776809fa78735f5521502a654a55dbf648076a418`.
- Config and actual judge adapter files were rehashed; no judge process,
  benchmark, epoch or panels were changed/read for scores.
- Future contract remains6144 tokens, seeds23201/23202, three original scenes,
  zero parent/source-context/optimizer/RNG input, zero training updates.
  Main must separately enroll/admit a **new** batch; do not insert these into or
  mutate the existing attempt3 block. No runtime epoch adoption is claimed here.

Authority is bounded by node5 **September20 18:00UTC** and a conservative
ovx4 preparation cutoff **September30 00:00UTC** from the supplied date-only
lease statement. Neither is an extension; this sidecar did not change any
running component's existing deadline or infer a new provider expiry.

## Tests and publication

```text
python3 -m unittest discover -s research_loop/workers/post_recovery_c2_age_sources_20260918 -p 'test_*.py' -v
```

**11 PASS** locally and on final ovx4 receiving source; node5 pre-capture suite
**10 PASS**. Tests cover stale/wrong scene selection, prior ineligibility,
unknown content, inherited/identifier exposure, header gaps, partial COMPLETE,
immutable capture/hash tampering, adapter-only staging and adopted judge pins.
`INITIAL_SOURCE_PINS.json` records initial uploads; `RECEIVING_RECHECK.json`
records final receiver pins and independent file/COMMIT verification.
`MANIFEST.json` lists the exact sanitized publication paths/hashes. Raw input
records, image descriptions, panels, hostnames, credentials and binaries are
excluded from publication.
