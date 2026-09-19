# Independent diagnosis: first real custody proof failed

**Cut: September 19, 2026, 13:41:51 UTC. No GPU/model dispatch is cleared.**
Sources: Main's `operations/SAMPLING_CUSTODY_PROOF1_ADMIN_LOGS.txt`, the bound
REPAIR_V1 source, the original pinned encoder source, and this reviewer's fresh
read-only `CUSTODY_HOST_METADATA.json`. The metadata read used the existing ovx4
SSH route, verified each staged config against `PREPARED.json`, and performed
no model/device/service calls, remote writes, or private-content reads.

## Player failures: exact implicated paths

All three staged job views now contain these **three zero-byte, root-owned,
0644 regular files**:

- `view/judge/REFERENCE_PANELS.private.json`
- `view/epoch/PRIMARY_PANELS.private.json`
- `view/epoch/JUDGE_EPOCH.json`

Thus all **nine** player-private target paths have ordinary readable file
entries in the shared host view. Their exact full paths, inode numbers, modes
and config hashes are in `CUSTODY_HOST_METADATA.json`; no file contents were
read. These are precisely the additional paths checked for players but not
judges. The logs show all judges got past custody to dependency imports, while
all players stopped at the combined private-path predicate.

**Likely mechanism:** the judge's file bind-mount target placeholders were
created in the shared writable view and are visible as empty underlying files
in the player view. This is strongly supported by the three corresponding
read-only file mounts, the empty 0644 targets, and the role-specific failures.
The failed processes have exited, so host metadata is not a reconstruction of
their entire former mount namespaces; the logs did not record individual
`checks` values. Do not claim a proven private-caption payload leak or prove
absence of one from these observations alone.

The guard is **not wrong** under its declared contract: it requires that these
paths cannot be opened, and `denial()` deliberately returns false even for a
readable empty file. Do not accept empty files as denials, drop paths from the
check, or ignore this exception. Repair the namespace layout instead: private
mount targets must be contained in a judge-only directory/view, not created
as readable files in shared writable storage. Preserve the exact same private
file hashes and scorer access; give the player no new access.

For the next explicitly authorized CPU incarnation, record every private-path
open result/errno **before** raising, without reading or exporting payloads.
Prove all paths inaccessible from the actual player namespace after judge
mount setup, along with the original GPU/host-proc/canary controls. Add a
regression that a readable zero-byte private file is still rejected.

## Judge failures: an extraneous dependency probe

All three judge logs fail at the proof-only import of `sentence_transformers`.
The original `FrozenCPUEncoder` does **not** import that package. It implements
the pinned MiniLM encoder using `torch`, `transformers.AutoModel` and
`AutoTokenizer`, verifies the exact embedding/tokenizer inventory and pooling,
and uses the same original frozen assets.

The original encoder file `gpu/ny_caption_similarity.py` matches its receiving
source-manifest pin:
`2484202b333818fc3d7ae25d0a41ccbd5ac8410431a6a930ee1fe40f3751f552`.
The model ID `sentence-transformers/all-MiniLM-L6-v2` is not evidence that the
Python `sentence_transformers` distribution is needed by this implementation.

Replace the proof's invented dependency requirement with imports of the actual
pinned runtime dependencies. Do not install/switch an encoder or environment
to make this extraneous check green. Keep tokenizer/decoder/library-identity
checks and all visibility checks intact. This fixes a proof bug, not the
scoring method.

## Failed attempt stays failed

REPAIR_V1 is now an attempted CPU custody execution, not merely an unlaunched
staging tree. Keep its `BLOCK_FAILED`, unit logs/statuses, role-start/failure
records and shared claims. The `preserve_unlaunched` path must continue to
reject it. Main has explicitly requested a new repaired CPU execution
incarnation; that incarnation needs distinct execution identity, a link to
this preserved failure, unchanged scientific diagnostic identity, and proper
reconciliation of the old units/claims through the original ownership rules.
Do not erase or rename away its attempt guards to rerun the same attempt.

No model run is authorized before the real repaired custody proofs succeed.
The new proof must observe actual namespaces; CPU mocks and source review are
not substitutes. The separate partial-cell reporting defect remains recorded
in `FINAL_DELTA_REVIEW.md` and should not be mistaken for either custody cause.

## Independent receiving verification — September 19, 13:44:13 UTC

`FAILED_EXECUTION_READ_ONLY.json` records the following without any remote
writes, device opens, model calls, service submissions or private-content reads:

| Evidence | Observed result |
| --- | --- |
| `BLOCK_LAUNCH.json` | `CPU_CUSTODY_PROOF_ONLY`; `model_dispatch_authorized=false` |
| `BLOCK_FAILED.json` | `TERMINAL_NO_RETRY_NO_FALLBACK`; `own_unit_failure_terminal_no_retry` |
| Role proof receipts | STARTED and FAILED present for all six units; each failure is `INCOMPLETE_NOT_ZERO_NO_RETRY` |
| Role model-run receipts | All twelve possible run STARTED/FAILED paths absent |
| Queue and science receipts | Empty in each of base, sleep51 and sleep117 |
| Completion/review | `PROOFS_COMPLETE.json`, `GPU_REVIEW.json`, `BLOCK_COMPLETE.json` absent |
| Original metadata | All twelve CONFIG/CONDITION/SOURCE_MANIFEST/GAME_MANIFEST hashes unchanged |
| Original V4 no-retry history | Unchanged SHA-256 `5115656143caa617c455054acbbad8117e0231823a49cd3758fb23774dbcd647` |
| Receiving source freeze | Preserved REPAIR_V1 SHA-256 `b85c15d598010712af0fe32505285b79b63c8daf4a85565e300f0b940080e0ab` |
| Original shared GPU claims | Both retained under failed block `65d113ba39d7a2ea0953dd290e64d1c4b9daeb607f2bc97029fd1e162a9114cf` |

This attempt is **failed CPU custody, with no scientific outcome**. It cannot
be counted as completed science, zero performance or a training replication.
The preserved failure is not undone by later source repairs or CPU tests.
Main's separate, ownership-checked reconciliation may archive the dead proof's
claims; it must leave the terminal attempt and source/no-retry history intact.
The new proof must have its own execution identity and must not inherit a
success classification, silently reuse this root, or load models.

## Receiving no-retry source recheck — recorded September 19, 13:48:13 UTC

Read-only hashes and source lines on the failed receiving root confirm:

- Dispatcher SHA-256 remains
  `598c09058d939477d23013918c1c1c5a8f8c3b3f3761a1dcfacad906f0d8ed40`.
  Its CLI rejects an existing `BLOCK_FAILED.json` before dispatch; its proof
  stage rejects an existing `BLOCK_LAUNCH.json`; its run stage requires the
  exact successful `PROOFS_COMPLETE.json`.
- Preparer SHA-256 remains
  `0b8ffe6270840da33a0fcbb2d4c0928f364d608eade8198ef4a721e0a6df7919`.
  The unlaunched-staging continuation rejects `PREPARED`, `BLOCK_LAUNCH`,
  `BLOCK_FAILED`, `PROOFS_COMPLETE`, other execution evidence and own claims.
- `BLOCK_FAILED.json` remains
  `4b874d58530f9cd59156fed24bbf7aa76e9766bbf737e006d01812f4e579de75`,
  and the receiving REPAIR_V1 freeze remains unchanged.

These observations are recorded in `FAILED_EXECUTION_GUARD_RECHECK.json`.
The supported CLI cannot convert this failed attempt to science while retaining
these guards. Claim disposition does not constitute successful custody or model
execution. A later proof or science result must have its own correctly bound
execution record and must continue to identify this attempt as failed.
