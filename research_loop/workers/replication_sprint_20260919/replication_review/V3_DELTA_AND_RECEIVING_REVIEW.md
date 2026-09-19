# V3: exact source and actual receiving custody review

**Verdict at September 19, 2026, 14:05:04 UTC: PASS for the reviewed custody
repair and explicitly scoped transition to the same preregistered diagnostic.**
This is an independent review of Main's primary exported artifacts, not a
second receiving proof, independent dispatch or a new human-ratification gate.
Only `replication_review/` was written.

## Exact identities

| Item | SHA-256 / identity |
| --- | --- |
| `SAMPLING_SOURCE_FREEZE_V3.json` | `d6c99489e68497af4dbbfd4f3c347ac73d09cdfb592c57341b7103db713b283b` |
| Actual joined `PROOFS_COMPLETE.json` | `af813b207130fe637676bda10576c3e6d4f4a27bfe400b7b0151cd60fb5312ed` |
| Execution incarnation | `21df1fcbff9c54358c2474541bd399a2ab2572c58aa73046a255d1d851517d8f` |
| Scientific diagnostic | `4df129caf0a0377ba91feec83923bc972e00b10dab13b5b198594db567689d95` |
| Execution authorization file | `326ec3136ad193c10c05f510ae12af0d891020a34074b753f16f3505f4a7a802` |
| Main's actual custody export | `378c20b3a9eab6670cb586c187f91b147a24c5fc539c4a854190a3f49cbfa2e1` |

`CPU_REVIEW_RECEIPT.json` at 14:03:40 UTC records **83 passing offline tests**:
72 candidate tests and 11 independent checks. Runtime closure, candidate/input
hashes, authorization and incarnation, preregistration, and Main's final test
log match the seal. Before/after source pins are unchanged. All temporary test
directories, including the V3 tests' default temporary directories, were
redirected into this review scope; no remote operations or model calls ran.

## Actual custody: verified rather than inferred

`review_v3_receiving.py` checks Main's
`operations/SAMPLING_V3_CUSTODY_EVIDENCE.json` against the seal, registry,
preparation, proof summary, old-claim disposition and dated Builder decision.
It reproduces the original writer's JSON encoding to verify the joined proof
and every embedded role receipt against their exact recorded SHA-256 values.

| Arm | Player proof PID | Player denials | Judge proof PID | Judge denials | Devices |
| --- | --- | --- | --- | --- | --- |
| base | 1986399 | 9/9 | 1986394 | 6/6 | player2 only; judge7 only |
| sleep51 | 1986407 | 9/9 | 1986403 | 6/6 | player2 only; judge7 only |
| sleep117 | 1986413 | 9/9 | 1986410 | 6/6 | player2 only; judge7 only |

For each of the six roles: all eight device outcomes are present, seven are
denied, successful unit exit/PID matches the role receipt, UID1352 and original
boot identity match, and `model_loaded=false`. Each player's exact required
path set includes all three formerly exposed private targets plus the original
host-private paths, canary, host proc, shared claims and queue-input paths.
No path was dropped to obtain a pass. Config, source/preparation, launch and
scientific-epoch joins all pass; evidence remained stable during validation.

Machine-readable result: `V3_RECEIVING_REVIEW.json`.

## What the repair does, and what was not measured

V3 does not rely on V2's ineffective `InaccessiblePaths` strings. It adds
read-only bind overlays for the player's `view/judge`, `view/epoch` and
`view/assets`, backed by separate empty directories outside the shared view.
Underlying private-file placeholders are deliberately created by sealed
preparation before CONFIG/PREPARED and before any role submission. Therefore a
passing denial is not explained by a player running before the judge creates
those file targets. The sources of the empty overlays do not gain those files
when the shared view is populated.

This is a different structural implementation than moving the original judge
paths: the judge retains its original mappings, while the player sees isolated
empty overlays. The actual cannot-open receipts support this implementation.
The original judge functions, asset/panel identity, public request/result
transport and extraction behavior remain intact. No exact kernel mount table
or effective-unit-property export was provided; no measured mount ordering or
blanket proof against every conceivable escape is claimed.

## Scientific identity and model-mode guard

- Still base/sleep51/sleep117 with generation seeds23301/23302, three original
  development scenes, 1024 actual generated tokens/cell, 6144/source and 18432
  total. Same selected source weights, 64-caption reference panels, adopted
  judge, tokenizer/decoder and extraction. No parent tokens, training updates
  or historical working-context load.
- This remains sampling variation for selected ages, not new independent
  training lineages, held-out transfer or pooled independent base replications.
  All source/seed rows and incomplete-cell outcomes remain accounted for.
- Explicit V3 schema binds the same preregistration and requires successful
  custody before model execution. The registry and role config bind
  `proof_only` to that authorization. Flipping the old V2 authorization or
  registry to enable models is rejected by tests; V3 is not a permanent
  proof-only dead end.
- Dispatcher model mode requires the exact completed proof and each referenced
  role file, matches the launch hash, checks the original shared claims and
  fresh host/device/protected-process/lease admission, and uses the existing
  fixed block. At review, 2241 seconds remained; the mode requires at least
  1500 seconds. This is an as-of observation, not permission to reset time.
- Main's dated **14:03 UTC** Builder decision binds the same freeze/proof/root
  and scientific scope. No additional reviewer or human gate is invented.

## Failed-history preservation

The V3 authorization binds the V2 failed source/registry/preparation/launch/
failure receipts; receiving validation recursively checks V2's preserved V1
chain. Neither failed root is reused. Main's V2 claim-release receipt identifies
six terminated proof invocations (three failed players, three completed judges),
empty cgroups/no remaining processes, and archives exactly the two owned claims
with preserved hashes. Failed guards remain terminal; claim release neither
reclassifies the failure nor counts it as executed science.

No new scientific outcome is claimed here. Model LOADED, cell/output and final
COMPLETE receipts remain necessary to report execution or results. Main owns
dispatch; this reviewer performed no receiving commands or mutations.

## Finalization — September 19, 14:10:21 UTC

**Independent review is complete and remains PASS.**
`finalize_v3_review.py` reran the local receiving-artifact validator, rechecked
every source/test pin in the 83-test review receipt, and verified Main's sealed
72-test final log plus the exact launch receipt. Source, authorization,
preparation and six-role proof hashes remain unchanged. Final machine receipt:
`V3_FINAL_REVIEW.json`.

Main's exported progress snapshot, observed **14:06:58.919244 UTC**, supplies
the actual base LOADED payloads. Their hashes were recomputed using the original
runtime's canonical writer, and their paths/job/epochs joined to the V3 registry:

| Receipt | Time, September 19 UTC | PID | SHA-256 |
| --- | --- | --- | --- |
| Controller launch | 14:04:39 | 1989482 | `40e115bb308835889881c9d2728734d6a73659ae2473d9a5680f3c45933c4c89` |
| Base judge LOADED | 14:04:48.324347 | 1989497 | `43b1d97dc5836e2376554461e50018fb2f83a95e015c8b274145496b75cfa754` |
| Base player LOADED | 14:05:30.901855 | 1989501 | `bc7dcb09d8da4437b24b392f49c03cc1563f59d2bb7622de61943009534242b0` |

The loaded base identity matches the original weight hash, frozen/no-optimizer
status, decoder, tokenizer, chat template and library versions exactly. The
adopted judge binding retains its original epoch hash and private-panel
selection; the new diagnostic remains seeds23301/23302. Historical seeds in
the immutable judge reference binding are not new generation-cell seeds.

At that progress cut, `block_failed=false` and `block_complete=false`; the two
later arms had no LOADED payload yet. This establishes that actual execution
started, **not** that all three arms ran, succeeded or produced scientific
results. Completion and per-cell outcomes remain Main's running experiment,
not unfinished work in this bounded source/custody review. No receiving command,
dispatch, claim operation or write outside `replication_review/` was performed.
