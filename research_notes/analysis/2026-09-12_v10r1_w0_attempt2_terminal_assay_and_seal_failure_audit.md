# V10R1 W0 attempt-2 terminal assay and seal-failure audit

Date: 2026-09-12 UTC. Audit observation window: 07:47--08:22 UTC.

This was an independent, read-only watch of Astra's bounded conditional
native-action writer gateway on node 3. No source, preparation, run artifact,
adapter, process, GPU reservation, package, or job was changed or stopped by
this audit.

## Verdict

Attempt 2 completed four real clean-base fits and all ten fresh-process
evaluation stages, but it does **not** close W0. Two terminal failures are
first-class and separate:

1. **Scientific assay failure.** All four clean-base oracle cells have
   `oracle_BA = 0.0`. All 256 oracle generations used the full 32-token cap,
   none emitted EOS, and all were therefore sealed as `truncated:true`. The
   strict parser makes every truncated output invalid, so all 256 parsed
   actions are `None`. The reducer's precedence correctly returns
   `ASSAY_INVALID`.
2. **Evidence-seal failure.** The official deployed `replay-real` command
   exits 2 with `NONREPORTABLE_ABORT: sealed bytes changed`. Exactly one of
   3,161 sealed files differs: `launcher.out`. The seal recorded its empty-file
   hash, then `main()` serialized the returned 6,099-byte report to stdout,
   which the launcher had redirected to that same in-root file.

The fitted cells also descriptively fail their optimization, binding, spill,
and aggregate interface gates. Those are real observations below the seal
layer, not a claim that the oracle failure caused every gate failure. However,
because the positive oracle control is invalid **and** official terminal replay
fails, none of those cell values can be promoted to the frozen W0 scientific
label. This is neither `MULTIKEY_BINDING_PASS` nor a promotable
`GATEWAY_NEGATIVE`. It supports no W0 carriage, locality, reliability,
retention, parenting, H1, or H2 claim.

## Exact prospective source and preparation

The native-build repair was frozen and pushed before attempt 2:

- commit: `27743d0a99b827450f794dbe0c1ab45f0b07bd51`
- module SHA-256:
  `99abab2c78dc06756b0bbbeb86d5717c5baf430af2cbafdab206f4fc8af4cafc`
- CPU tests SHA-256:
  `874ca3984471694724c365d1efc98e04187afb3ddf997a173993eda7d2188f37`
- launcher SHA-256:
  `3994bf389e63ac790b3eb500c74a974ed57b88fd8fd02d494ae6fecc0ab33665`
- source archive:
  `/tmp/astra_w0_source_27743d0a_20260912.tgz`, SHA-256
  `1ab02b37357daa27b7df900ecc6ec820adc9b57d55f3e04d245502a0286ea61b`

For all three owned files, commit bytes, archive members, deployed node-3
bytes, and manifest source hashes agree exactly. The fresh root was
`/localhome/local-rohing/astra_diagnostics/astra_W0_v10r1_20260912_attempt2`.
The VM rebase conflict was cleared before the source commit and archive.

Preparation identity:

- manifest SHA-256:
  `dfc673049af280e0897112b15812aca56e389bca3fd9fb7ad7d5f6151c1d5244`
- raw `PREPARED_SEAL.json` SHA-256:
  `22bec9b3f191504135d96c957b07a91959d2d3b09d7a42ef00c73e1dd15fa906`
- external config SHA-256:
  `f0fc7f2cea6e3251eb5ebd44718e2e2577d346514aef64a84f24076d8066044b`;
  its parsed object equals the manifest config exactly
- native-build receipt SHA-256:
  `589bf591fb1cc48d03460e948100a5f5bd32db53eabb0aa46db699da49b9bfa6`
- prepared/launch capsule SHA-256:
  `e66cbaa8867c3410e9c0d30b7ab3e57d4671e3ac4b0ad0bb5de509f05314fbfa`
- node CPU suite: 60/60 passed; receipt SHA-256
  `7bf25b5fb2f93f2bfa84a75bc6a18ceef1b93b9825979d0154de04ac7e637f46`

The exact deployed `validate_prepared` passed. An independent rerun of the
native preflight produced the identical receipt hash. It binds:

- CPython 3.12.3 at resolved `/usr/bin/python3.12`
- Triton 3.7.1
- compiler `/usr/bin/x86_64-linux-gnu-gcc-13`, SHA-256
  `1b99826121ae6682a634e5efe09bd3e3df58ce58e0b28f849114ab5b89139c26`,
  version `13.3.0-6ubuntu2~24.04.1`
- 218 headers under `/usr/include/python3.12`
- `Python.h` SHA-256
  `729ef157f6026e6e1b3104593f87dddc597c3b83b60c7c2965878c62a56c6f7d`
- `pyconfig.h` SHA-256
  `dcda0cfa3f4971db195817881c58025db6c76f19ae45f26d3dda0a43001253e8`
- exact minimal `gcc -std=c11 -fPIC -c` argv and successful object creation

Independent package queries returned `python3.12-dev` and
`libpython3.12-dev` 3.12.3-1ubuntu0.16, `libexpat1-dev`
2.6.1-2ubuntu0.4, `gcc-13` 13.3.0-6ubuntu2~24.04.1, and `ninja-build`
1.11.1-2.

The model/tokenizer remained the local-only Qwen2.5-7B-Instruct snapshot at
revision `a09a35458c702b33eeacc393d103063234e8bc28`, with the same 14-file
inventory SHA-256
`1b248450cd087dad8956a8b77ccc4829040d614133f3c0aba834729af8075422`.
The evidence boundary remained `official_model_authentication =
UNRESOLVED_LOCAL_HASHES_ONLY`, `material_origin =
synthetic_researcher_authored`, and `clean_lineage = false`.

The node hash, A40 UUID, driver, package map, protected roots, model/tokenizer
paths, seeds, recipe, and four-fit cap were unchanged. Relative to attempt 1,
the only config changes were the new builder-preflight reference and a
**stricter** cutoff: `1789209422.503231`, the first controller's original
three-hour deadline. Material and all four fit inputs were byte-identical to
attempt 1:

| Fit | Input SHA-256 | Encoded SHA-256 |
|---|---|---|
| root0 W+ / seed 0 | `c2dad0761455209091b2e7d4da61c44d63bfd0eea3fd0e0d00a0ccfdf63a8716` | `248efc0271ce1aafd4c7963f56ed105c293b4fae733af9ed3b3fee53dc117d83` |
| root0 W- / seed 0 | `99d5fd12a8756fc2a65817bd29f4fc779b028d2314b403b1f394090e41cd7eeb` | `9c0dd6b697258faa8a93593351f0438e8587aaef0ffdbfd00b39eac6b145a421` |
| root1 W+ / seed 1 | `3cf3d0b5c27b860eb88a21f4b6ffc893eb592c3465fbe706c61b19aa06673f44` | `985ce0f87d8a67c5b4d5854ee97494510cd9e00f7692fb8b413d24ea9be9fe16` |
| root1 W- / seed 1 | `b6b3efe2bcca429f78fa700b2aaec71e365c40e9e12b1a89491677dae934643a` | `98c723cd593ac631b6d7b6bcd82346a8822ea183f1b4157033161b2c5260325a` |

`infrastructure_attempt_lineage.json` correctly names the predecessor
manifest and abort hashes and has SHA-256
`7413f461c40fb442ea7e0145a621899273a4df8fd10976ad03afb0040e037583`.
It was written after the prepared seal and therefore was not prepared-sealed;
its initial bytes were captured by the pre-launch capsule, and it appears in
the later real seal. This distinction does not repair the real-seal failure.

## Launch and four clean-base fits

The controller PID was 25106. `EXECUTION_STARTED.json` was written at
07:49:10 UTC and has SHA-256
`70bf512a0552d6c5057570b3358658c659924a6f4b3e3bda85e6c6f628bf268b`.
It binds the manifest, environment, node, driver, original deadline, and A40
UUID `GPU-71e5a3e2-e9c8-5caf-70d8-73794ac34821`. The launch receipt SHA-256 is
`a4c7cd3bf04ce6c11aa3e01e186426fa125f1e7c4ad17526d8bc1f169fb5a432`.
The launcher saw an empty full NVIDIA compute table and no readable CUDA
reservation, while explicitly recording 1,367 unreadable service
environments.

All four fits used separate workers, loaded `OFF_CLEAN_BASE`, exposed exactly
392 LoRA tensors, recorded 256 contiguous optimizer steps and 1,536 target
tokens, and returned process code 0. The paired maps within each root have the
same deterministic initial LoRA digest; no fitted adapter seeded another fit.

| Fit | Worker | Profile: projected 256-step seconds | Process seconds | Mean loss | Update norm | Adapter SHA-256 |
|---|---:|---:|---:|---:|---:|---|
| root0 W+ | 25414 | 109.7243 | 113.5107 | 1.1476466 | 2.9262064 | `51c0a628b28f2e821b723f94088e29e1787ff33d495ea38254029984cb53a339` |
| root0 W- | 26060 | 89.9115 | 121.9183 | 1.1533119 | 2.9619865 | `9cba7803c83366fc6a8ce79ec1bf01b5ce892ed00852b4dc19b27b7b6e189809` |
| root1 W+ | 26691 | 88.2994 | 106.0795 | 1.2333303 | 3.0809378 | `1f56b73aa1bf82d08e6b430e40776a55116b1733f5ee1236954f4fd01a25969a` |
| root1 W- | 27189 | 84.2966 | 110.9052 | 1.2180835 | 3.1091380 | `c38e3491ccce9efcf6fb43b1aad33a40caebfbe38867a3be48192e55b60e7fcf` |

The root0 initial LoRA digest was `e8290b734317aa4eefa66fdceb5863bcdf80e5acbb723b36227f40c08cadd232`;
the root1 seed-1 digest was
`49b7cb33546dafe7b7bc40a079c5ca18e69e4293b41593451fcbca9730290565`.
The four DONE SHA-256 values, in table order, are
`54319252366489dc87fe348e75d67e4dd4aa05e9fd77ca4fd89c61bb6bf6c37f`,
`2629e91456d9c7661ccf77f8c5e469afdb5fa712bca5de92b9ea04b9b939ee98`,
`48d235ac2d52f1e241586d8c9fba92f637e5c2253616f2355aff2230a9e9826c`,
and `f98b7cc76e08010f1fa8aa002b485fef2a2cb0c743777a9c6394a83fa8e1073f`.

## Evaluation and resource arithmetic

`requests.json` has SHA-256
`fd1c26dee6a20a48f344659f53525d4a387db0f02381c02d24e7418549b327e4`
and exactly 1,504 unique requests. Fresh process counts were:

- OFF: 464 generate + 208 score;
- each of four fitted adapters: 104 generate + 104 score;
- four fit workers plus ten evaluation workers = 14 distinct worker PIDs.

Every evaluation DONE/process receipt returned code 0 and bound the expected
manifest, source, model, tokenizer, environment, hardware, adapter, typed
request subset, and raw-tree hash. The exact lower-layer validator confirmed
all 3,008 raw record/trace files, full candidate+EOS token scoring, prompt
encodings, log hashes, stage order, and fresh loads.

`RESOURCE_RECEIPT.json` has SHA-256
`1e45e59b0874397475b3232794bea7e5f8b0595217b0ef36e0bc70b3045cb618`.
It records four fits, 1,024 optimizer steps, one GPU, all fourteen ordered
stages, and 1,698.4112215180012 reserved GPU-seconds. The arithmetic is exact:

```text
1698.4112215180012 / 3600 = 0.47178089486611147 A40-hours
```

The sum of stage-process seconds is 1,698.0466152510016, not greater than the
reserved duration. Wall end preceded the inherited deadline by
8,373.725402593613 seconds.

## Failure 1: oracle assay invalid, with separate descriptive cell failures

The oracle distribution is unambiguous:

| Cell | Oracle outputs | 32 tokens | no EOS | `truncated:true` | parsed `action=None` |
|---|---:|---:|---:|---:|---:|
| root0 W+ | 64 | 64 | 64 | 64 | 64 |
| root0 W- | 64 | 64 | 64 | 64 | 64 |
| root1 W+ | 64 | 64 | 64 | 64 | 64 |
| root1 W- | 64 | 64 | 64 | 64 | 64 |

Across all 256 outputs, zero were exactly stripped `ACT: a0` or `ACT: a1`,
zero contained a line-aligned ACT marker, ten contained `ACT:` only somewhere
non-line-aligned, and there were 210 distinct text hashes. The generator marks
an output truncated when it consumes all 32 new tokens without terminal EOS.
The parser independently requires the entire stripped output to be exactly one
ACT line and also forces `action=None` whenever `truncated` is true. Thus the
sealed `oracle_BA=0.0` in all four cells follows exactly; it is not an
ambiguous counting artifact.

The fitted-cell values fail additional gates on their own terms:

| Cell | BA | BA - opposite BA | keys NLL gain >=.50 | key margins >=.50 | validity / multiple ACT | max spill TV | unrelated native exact |
|---|---:|---:|---:|---:|---:|---:|---:|
| root0 W+ | .3125 | -.09375 | 7/16 | 7/16 | .71875 / .03125 | .62228 | 0/8 |
| root0 W- | .421875 | -.078125 | 4/16 | 0/16 | .921875 / .046875 | .41598 | 0/8 |
| root1 W+ | .5000 | .015625 | 5/16 | 5/16 | .984375 / 0 | .26550 | 0/8 |
| root1 W- | .40625 | -.15625 | 8/16 | 1/16 | .96875 / 0 | .56990 | 0/8 |

Every BA is below `.80`; every own-minus-opposite BA is below `.50`; no cell
has all 16 per-key NLL gains at least `.50`; and every maximum binary-TV spill
is above `.05`. Signed legal-ACT-rate change reaches 1 for non-owner families.
Root0 also fails fitted-output interface validity/multiple-ACT constraints.
Although both root1 cell-level interface predicates pass, all four fitted
adapter/root cells score 0/8 on exact unrelated native outputs, so the
aggregate interface gate fails in both roots. Root mean-gain asymmetries
`.042922` and `.216505` are within `.25`, but that cannot compensate for the
per-key optimization failures.

These observations show that oracle failure did not cause all five gate
failures. They remain descriptive because a failed positive control prevents
scientific interpretation, and the seal defect prevents official replay.

## Failure 2: terminal self-seal invalid

Terminal hashes:

- `report_real.json`:
  `407af1ff9ab3ca2865744e64155431cb00be8e21ab4025eb2fc4ac4d56bfb999`
- raw `REAL_EXECUTION_SEAL.json`:
  `f75999b705adc3443a7ca5d964a24fb3ae76606c0dfbda87949da78141ca4fd1`
- `adapter_hashes.json`:
  `b7af632a09129b82932a5d35b94de64545a95a5f1cf83b5085d4c0a35720f610`

The seal names the correct report hash and has no missing or extra files. Its
only byte mismatch is:

```text
file: launcher.out
sealed expected: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
current actual:  407af1ff9ab3ca2865744e64155431cb00be8e21ab4025eb2fc4ac4d56bfb999
current size:    6099 bytes
```

The current file is byte-for-byte the canonical report. Its mtime is
08:17:32.841 UTC, after `report_real.json` at 08:17:30.221 and the real seal at
08:17:30.839. The failure is therefore deterministic self-invalidation, not a
scientific-record ambiguity.

Calling the exact lower evidence validator directly, below the real-seal
inventory check, validates every fit, request, raw tree, trace, process, and
resource receipt and recomputes report digest
`407af1ff9ab3ca2865744e64155431cb00be8e21ab4025eb2fc4ac4d56bfb999`.
That is useful diagnosis but does **not** override `replay-real`'s fail-closed
result.

## Original-root immutability

The first root remained terminal and untouched through attempt-2 completion.
Its critical hashes are unchanged:

- manifest `5ec0ee13fefeff6bae79a9b73fbd35c27506a1864b08497e1336b9bcdb129894`
- prepared seal `6d09ffadb5ffc10445ab756d58f221752e2840415c2c43b201cf3d0102b8b1b1`
- execution start `73ef075fb13939efa84288d4004d4db48d68bc977e6c171c7aaddd88d045b771`
- abort `1f818b236d57a649fc8e5811bfb6c0f0e6ef49c4ea0989d1cd9d3bf0f9c277c8`
- empty step file `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`

No fit profile, DONE, adapter, request, resource, report, or real seal was
added there. Attempt 2 was a genuinely new root, not an in-root replacement
fit or same-run rescue.

## Smallest prospective V10R2 repair

Preserve both V10R1 roots exactly. Do not rewrite the seal, delete or truncate
`launcher.out`, relax the strict parser, reinterpret truncated outputs, or
promote the descriptive fitted-cell metrics.

The smallest prospective V10R2 should change only the two failed assay/evidence
interfaces:

1. Append a frozen, explicit oracle instruction requiring exactly one line,
   `ACT: a0` or `ACT: a1`, and nothing else. Keep the 32-token cap initially,
   keep `truncated` fail-closed, and keep the exact parser. Before any fit,
   execute the clean-base oracle-only control over the frozen four cells and
   require `oracle_BA >= .90` in each. If it fails, terminate without fitting;
   do not tune and retry inside the same run.
2. Redirect controller stdout to a path **outside** the run root, leaving only
   immutable evidence files under the root when `REAL_EXECUTION_SEAL.json` is
   created. After controller exit, custody the external stdout together with
   the untouched root in a post-exit capsule. Add an actual CLI regression
   that runs the execute/return-output path and proves `replay-real` remains
   valid after stdout closes.

Keep all scientific material, fit seeds, recipe, request panels, thresholds,
label precedence, model/tokenizer identity, and resource bounds unchanged.
Because attempt-2 outcomes are now known, label V10R2 as a prospective
assay/evidence repair and do not use these observed cell values to change its
training or acceptance rules.
