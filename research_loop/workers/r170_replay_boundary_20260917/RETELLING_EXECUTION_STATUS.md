# R159(c): corrected-retelling execution, not merely deployment

Operational observation: **2026-09-17 14:33:59.018816 UTC / 07:33:59.018816 PDT**.
Scope: the R166 native invitation handoff, distinct from the asynchronous parent-policy rollout.
All timeline dates below are September 17, 2026; PDT is UTC−07:00.

## Result

**C5 and C2 are beyond staged/deployed/exposed: their first documented post-adoption
own responses passed TRAIN target eligibility, received 16 recorded finished NEW
updates each, and are included unchanged in a completed, checkpoint-bound sleep.**
The invitation itself stayed masked context; the training target was the child's
own response, not parent/environment text. This establishes execution, not that
the response was a correct retelling, semantic adoption, retention, or benefit.

| Life / event | Exact recorded UTC | PDT | Journal / sleep identity |
| --- | --- | --- | --- |
| C5: invitation actually rendered | 08:57:02.931694 | 01:57:02.931694 | REQUEST 2908 after invitation marker 2907, cycle 29 |
| C5: own response finished | 08:57:44.236639 | 01:57:44.236639 | RESPONSE 2909 → COMMITTED 2910; segment 86 |
| C5: first finished update of that row | 09:00:27.357584 | 02:00:27.357584 | UPDATE 2917; optimizer step 2481 |
| C5: completed sleep's checkpoint created | 09:49:47.733695 | 02:49:47.733695 | sleep_000029/COMMIT.json; SLEEP_COMPLETE 3047 |
| C2: invitation actually rendered | 09:14:06.328222 | 02:14:06.328222 | REQUEST 3590 after invitation marker 3588, cycle 33 |
| C2: own response finished | 09:14:43.150427 | 02:14:43.150427 | RESPONSE 3591 → COMMITTED 3592; segment 98 |
| C2: first finished update of that row | 09:17:19.771190 | 02:17:19.771190 | UPDATE 3599; optimizer step 3027 |
| C2: completed sleep's checkpoint created | 10:08:06.291886 | 03:08:06.291886 | sleep_000033/COMMIT.json; SLEEP_COMPLETE 3741 |

**Clock limitation:** REQUEST uses `started_unix`, RESPONSE/UPDATE use
`finished_unix`, and checkpoint time uses COMMIT's `created_unix`. Journal
SLEEP_COMPLETE has no publication timestamp: its exact wall-clock publication
time is **missing**, not interchangeable with checkpoint creation. The completed
records and matching COMMIT bytes were present at the operational observation.
UTC/PDT conversions display six fractional digits; original epochs remain in
the metadata receipt. “First” means first proven for the documented R166 adoption,
not an exhaustive search of every earlier life record or a later-policy census.

## Training joins and limits

- **C5:** REQUEST 2908 → RESPONSE 2909 → COMMITTED 2910 matches original prefix,
  raw target and token IDs. Target eligibility 2913 admits the unchanged row as
  NEW. Its source hash is `f0c0a5cff2a13e63195fb641591595dc01735a152f03a65e78880e5c9fd2b626`.
  Sixteen NEW updates run from 2917 through 2962, totaling **8,192 own-target
  token exposures**; SLEEP_COMPLETE 3047 records 16 presentations of this source,
  132 total sleep updates and total optimizer step 2610. The saved row is
  unchanged, frontier/rows both 87, pending null. The response is **512 tokens,
  truncated=true, terminal=false**: trained does not mean a complete retelling.
- **C2:** REQUEST 3590 → RESPONSE 3591 → COMMITTED 3592 passes the same exact
  joins. Eligibility 3595 admits source
  `514e311200b0ab4f80afb2128576bfb814cb3b6fcbc8a9045694d2bd6780ddba` as NEW.
  Sixteen NEW updates run from 3599 through 3644, totaling **6,576 own-target
  token exposures**. SLEEP_COMPLETE 3741 records 16 presentations, 144 total
  sleep updates and total step 3168; frontier/rows both 99, pending null. Response:
  **411 tokens, terminal=true, truncated=false**; semantics not adjudicated.
- Both actual rendered user messages hash to the effective invitation
  `c3d2e219e024baff2e2bde638d0caa303fb408d89afd8b305deaf4187839d56f`.
  Both request receipts mask all history tokens; both committed own rows retain
  `prefix_loss=false`, `target_loss=true`; eligibility reports `raw_modified=false`.
- Record hashes, consecutive chain links and paired intents were checked from
  invitation through completion; completed snapshots hash correctly and their
  checkpoint documents exactly match the saved COMMIT metadata. **No adapter,
  optimizer or RNG payload was opened**, so this is not an independent restore,
  saved-state ownership, or numerical-learning verification.

## Other lives / missingness

| Life | What the inspected R166 receipts establish | What is not established |
| --- | --- | --- |
| C1, C4 | Candidates staged; activation4 safely timed out. Activation5 dispatcher finished at 09:42:22.717708 UTC / 02:42:22.717708 PDT with `attempted=[]`, `no_event=[C1,C4]`. | No proven R166 native adoption, rendered invitation, own response or trained retelling in these receipts. No claim about later uninspected activity. |
| C3 | `R154_ALL_FIVE_RECEIPT.json` says staged/verified, not activated; later inspected activation attempts exclude C3. | No proven R166 native adoption or invitation-to-sleep chain. Current C3 journal was not scanned. |

Deployment, readiness/GO, parent delivery and LOADED alone are not training
evidence. C5's earlier exposure handoff explicitly stopped short of claiming a
subsequent sleep; the bounded 14:33 UTC read now closes that execution gap.

## Provenance and bounded read

Local rollout directory: `research_loop/workers/r166_retelling_handoff_20260917/`.
Starting receipts: `C5_RECOVERY2_EXPOSURE_HANDOFF.md`,
`C5_RECOVERY2_EXPOSURE_OBSERVATION.jsonl`,
`C5_RECOVERY2_RETELLING_RESPONSE_STATUS.json` (SHA256
`31b2635007e607419e21c5cec0cb8de10460653200cb6a82b46530602490e93e`),
`ACTIVATION4_EXECUTION_HANDOFF.md`, `ACTIVATION4_C2_EXPOSURE.json` (SHA256
`42e0b210145dc96c2a3e64995afcc51d5fb7179e6067cb27a7bf2c42b7fc6559`),
`R154_ALL_FIVE_RECEIPT.json`, and `ACTIVATION5_EVENT_DISPATCHER.jsonl`.

Remote life roots: `/localhome/local-rohing/orch_r153_community_C5_20260916_attempt1/life`
and `/localhome/local-rohing/orch_r153_community_C2_20260916_attempt1/life`.
Journal references below resolve under the corresponding root's `stream/records/`;
checkpoint references resolve under its `checkpoints/`.

| Life | Relative provenance path | File SHA256 |
| --- | --- | --- |
| C5 | stream/records/00000000000000002908.json | `1d1687f762770be7a750e25748b34ec1c3cacdbbb214959d6749eb9956b6bfc8` |
| C5 | stream/records/00000000000000002910.json | `2cc3ba4a1b7b44c2137e9bf4f66326f514e3c6f3ee88a51f581e39afc2550d21` |
| C5 | stream/records/00000000000000003047.json | `64a7cd7dff00c5137f18423000be67ea5fbcb6c6f5099575150f6806c6a27379` |
| C5 | checkpoints/sleep_000029/COMMIT.json | `1c8706984fb76c62a085268e12224a6a163098bf8d79e2d1e52b855770477f42` |
| C2 | stream/records/00000000000000003590.json | `3907a8d6364f9538581f1d634ecc814742c9f39a86e8f44f4245d4c436b5e561` |
| C2 | stream/records/00000000000000003592.json | `91bc83297dac51efc323e4891347c109f0a35aedd0d36449e23b8dd6c998253a` |
| C2 | stream/records/00000000000000003741.json | `9414fd58eae837f06363983f82e0f8930534343d89752a7c546161985248684c` |
| C2 | checkpoints/sleep_000033/COMMIT.json | `38067e8619851f556e49b3e3c26f307fd1b4abfd700fcb64d4cdde18a91dc70f` |

The sanctioned `gpu/ovx3_ssh.sh` wrapper ran a stdlib-only read-only script via
stdin, with CUDA hidden, bytecode disabled and model hubs offline. Successful
pass: **295 journal records plus paired intents and two COMMIT metadata files,
18,692,673 bytes**, scanning only C5 2907–3047 and C2 3588–3741; no polling.
Caps: 384 records/life, 96 MiB total, 16 MiB/file, 100 seconds. An earlier bounded
pass stopped at the recognized TRAIN `CHECKPOINT_METADATA` kind (14,628,276 bytes);
its refusal receipt was preserved before adding that kind and rerunning. Total
reads across both passes: 33,320,949 bytes. No raw TRAIN text was emitted.

Local metadata-only observation: `/tmp/r170_retelling_execution_20260917_1434.json`,
SHA256 `ab98ea8cb6c646846ee0b3f25ebb7fa422f2b07b8cd496358e6dbe7633b64ac2`;
Main preserved an identical durable copy at
`research_loop/workers/r170_replay_boundary_20260917/RETELLING_EXECUTION_METADATA.json`
and verified the same SHA256.
observer `/tmp/r170_retelling_execution_20260917_1432.py`, SHA256
`f3365fb5eb7a70f610bc7aceb7ef5f1d8e9130ee7c2edb2f77526dca29977c19`.
The durable path/hash joins and conclusions are preserved here even if `/tmp`
is cleaned. No evaluator artifacts/readout files, scores, answers or maps were
queried for this analysis; no remote writes, signals, workload launches or
provider/model calls. ASSEMBLY and COORDINATION were not edited.
