# Final audit: EVENT-retention-v2 seed-0 attempt 6

Date: 2026-09-13 PT  
Auditor: independent Codex subagent (`warmfix_followup_audit`)  
Audited commits: `3f4c03bc80298d5fd1062db49fbe26174fdc1b34` and
`71ae5bfed01d4a42960e90440633f640c2f60f25`  
Prior audits: `4daee9fb`, `8342d4de`  
I launched no model or GPU work.

## Verdict

**The exact seed-0 attempt-6 protocol and manifest pass the scientific gate:
GO.** The new code accounts for attempt 5's completed B200 fit plus its
preworker readout failure, makes that checkpoint explicitly ineligible, and
runs four new fit/readout branches from the original A200/C0 inputs. The
revised all-in cap is exactly **20 fits / 6,400 updates / 25,600 presentations /
288 readout calls**.

This is not a prelaunch approval. Astra launched attempt 6 at
`2026-09-13T20:51:56.741871Z`, before this audit verdict. At my first live
inspection the B200 fit was active; at `20:58:28Z` the fresh B200 fit/readout
had finished and the fresh B400 fit was active. The launch-order violation is
recorded. Because the running operator and manifest are byte-identical to the
audited artifacts, the runtime may continue under this retrospective GO, but
it remains `CAPTURED_NOT_PROMOTED` until a terminal completion and reduction by
the exact committed reducer. Any new stop remains terminal: no retry, resume,
checkpoint reuse, or manual continuation is authorized.

## Exact source and native receipts

The committed tested-interface hashes match the objects in `3f4c03bc`:

- fit: `563354304444b306b7d1ba210c3dce42a4d9e6c1b1322f239e5256341210c45f`
- outer: `c9f01d41872fc3a890826eff1a5367c847c8e93d02be9d0fa274feb19424f319`
- follow-up operator:
  `bc4125bbc982be155623c0c96792a3386f41a91ace76c4eebc1f64ff178108ae`
- warm overlay:
  `7c69c44bf9253a536ceec9ebe5b081e38dd7e4d421a48563797fccd463ecfaaa`
- reducer:
  `afee815b34ea30bbd156491055cc2fac95047360404f0edbfaa2df7335688dfd`
- reducer tests:
  `4fe111768a56fb7d9df4eb8f4e2eaf27303c033cad7df9b1cb1136901cf09cc1`

The committed operator log
(`dcdd9a9b17a4eeb2c49a3c5f9c7d42c8cf8a8d00d35bae41a18474429c1aa132`)
records 61/61 tests passing in 6.743 seconds. The exact changed-path reducer log
(`808066db88d46684c9c5b0555758918ea23656c830a02686ec54a544d42ad58d`)
records 3/3 tests passing in 137.023 seconds: complete raw reduction, exact
prior-failure reconstruction, and rejection of worker bytes/raw drift in the
failed reader. These extend the prior 12/12 terminal reducer suite from
`6caffa15`; static inspection confirms the new reducer delta is confined to
the new failure shape, no-resume checks, and revised work cap.

The committed node-native receipts are:

- preflight:
  `ae93be8794fd5b39e0becb71f4b12ad34920853de0cb0ce7c18191b607a65472`
- native prior-failure reduction:
  `daed65fd0225f37f707023ed5b18e2c431f8cc6f0c0b106d17573f2d9eecbea1`

Both report zero fits and zero model calls. The preparation helper omitted one
`replay_receipt` argument only after it had written the manifest; it executed
no science stage. A separate read-only preflight re-opened that unstarted
manifest, found an empty runs directory, reconstructed identical material,
and passed all four phase inputs.

The exact prepared/running manifest is:

`/localhome/local-rohing/astra_diagnostics/pcfl_sequence_v2_followup_seed0_20260913_attempt6/manifest.json`  
SHA-256:
`a1d541f2c9d9f7ed5416700885f790b3d7e2a91d4990bc7788d1c8a7ee26f211`

Direct node-2 hashing matched the operator, fit, outer, repair receipt, and
manifest pins. Warmfix4 still records `original_modified=false` and
`material_reexported=false`; its repair receipt remains
`c79dff53330905c553a6ca0e276888055f5fc270d4c1124e5fe507f9c75213e4`.
The collision-rejecting PEFT canonical join and complete tensor
shape/dtype/hash/coverage checks are unchanged from the audited warmfix4
boundary.

## Exact attempt-5 failure and ancestry

Attempt 5 seed 0 did real B200 fit work and then stopped before any readout
worker existed:

- B200 fit collection `866015aae0208d16ed267ad0277c078c0c9c85e861d275fc78406aee2260de78`
  is `COMPLETED`, return code 0, released, with completion
  `f0cd392fcc67aa6db814ed15f8c3df89ab1a83dbe6e08f9f931243511f924de5`;
- its adapter bytes are retained only as failed-history evidence, not as an
  eligible parent or attempt-6 input;
- B200 readout collection
  `059b93dad0f03175133df9e2a859e74e44d03a75b404b804092cfbfddd05a71a`
  is `FAILED`, with no worker identity, return code, stage directory,
  completion, or model call;
- its only errors are `pre_cvd: resource not released/matched` and
  `controller: preflight failed`, caused by unreadable transient PID 258553.

The new operator and reducer both reconstruct the full chain rather than
accepting a caller-supplied cost:

| attempt | terminal condition | physical failed work |
|---|---|---:|
| 2 | preworker | 0 fits / 0 updates / 0 presentations |
| 3 | warm-prefix validation after fit | 1 / 200 / 800 |
| 4 | collector freshness validation after fit | 1 / 200 / 800 |
| 5 | readout preworker after completed fit | 1 / 200 / 800 |

The native reducer receipt reconstructs cumulative seed-0 failed work as
3 fits / 600 updates / 2,400 presentations / 0 readout calls and cumulative
failed-attempt elapsed time as 576.1522025248269 seconds. Adding the three
original acquisition collections gives `initial_outer_seconds` =
894.9595694087911 and `remaining_seconds` = 6305.040430591209 under the
original two-hour cap.

No generic recovery route was introduced. The parser admits only the exact
seed-0 attempt-5 root, exact stopped-readout shape, exact attempt-2/3/4
ancestry, exact two run directories, exact evidence inventories, and the exact
fresh attempt-6 root name. It rejects `manual_continuation`, `recovered_b200`,
altered costs, another failed-reader shape, worker/readout bytes, checkpoint
drift, input/source drift, overlap, and any repinned attempt that skips an
ancestor.

## Fresh scientific run and fixed arithmetic

The manifest has `carried_primary_stages=0` and schedules all eight new stages
in fixed order. The three warm branches all point to the original measured
A200 completion
`337e503482430f38be681b45a5676eca7ea1287925f911b70679dd923264d5e5`;
`CLEAN_CUM600` alone has no predecessor and starts from C0. Every readout is
constructed only after its corresponding fresh attempt-6 fit and must point to
that fit's completion under the fresh root.

| branch | parent | new updates | new presentations | readout calls |
|---|---|---:|---:|---:|
| `B200_NEW_DOSE` | original measured A200 | 200 | 800 B | 16 |
| `B400_FIXED_WORK` | original measured A200 | 400 | 1,600 B | 16 |
| `REPLAY400` | original measured A200 | 400 | 1,600 mixed A/B | 16 |
| `CLEAN_CUM600` | original C0 | 600 | 2,400 cumulative A/B | 16 |

The attempt-6 B200 input and attempt-5 B200 input, after removing only the
new provenance/source pin fields, have the same canonical SHA-256
`f461a198e0b24468516087a72ddddd4fb9f6aba1eeabd48bed01b6afe2623117`.
The material pin remains
`39555fece842bd2d3aa3573dcb6805116ad06e3010ca1913b6a0ea0a1f8bdf9f`;
learner seed, model/base binding, archive, replay receipt, environment, dose,
phase topology, and readout counts are unchanged.

After a successful attempt 6, physical work is:

- seed 0: 8 fits / 2,400 updates / 9,600 presentations / 96 calls;
- seeds 1 and 2: 6 / 2,000 / 8,000 / 96 each;
- all seeds: **20 / 6,400 / 25,600 / 288**.

The reducer recomputes these from physical artifacts and refuses the pooled
receipt if any cap is exceeded.

## Resource boundary and final admission condition

Attempt 5's arbitrary unreadable PID remained a hard `pre_cvd` failure. The
attempt-6 launch and first stage instead recorded an empty target GPU, matched
empty queue, no CVD owners/unexpected/unresolved processes, and only the
already approved systemd user-manager/PAM helper pair (PIDs 36935/36938) under
the narrow `EXPLICIT_MAIN_APPROVED_NON_WORKER_INIT_PAIR` exception. Thus the
new failure accounting does not weaken pre-CVD freshness or visibility.

Final evidence admission still requires the exact manifest above to reach a
fresh `completed.json` with eight completed/released collections and no
`stopped.json`, followed by reduction with committed reducer
`afee815b...`. The reducer must re-open all raw responses, validate each fresh
checkpoint/readout, reconstruct the complete failed-work ancestry, and join
seeds 0/1/2 under the unchanged descriptive claim boundary. Until then there
is no result, promotion, or scientific claim.
