# R133 bounded pre-GPU source review

Reviewed 2026-09-15, through 21:57:16 UTC. **Residual implementation blocker: startup receipt race.** This is a review of the exact source bytes below, not launch authorization or evidence of native success. Main owns guard/staging; Ptolemy owns producer. Only this review file was edited; no Git/shared-ledger edits, model/GPU calls, real admission scans, weight reads, or fixed32/FINAL task-data reads occurred.

## Residual blocker

**R1 — Native can outrun publication of its mandatory LAUNCH receipt.** In `gpu/orch_r133_code_feedback_guard.py:186`, `Popen` makes the child runnable before `LAUNCH.json` is created at line 189. Native calls `validate_native_entry`, which immediately reads that file at line 80. The shared `write` helper exclusive-creates JSON but does not atomically publish complete bytes. Neither a startup barrier nor a bounded wait protects this read. Thus a valid scheduler interleaving produces `FileNotFoundError`, or `JSONDecodeError` on partial bytes; native exits without collection and the already-created `DISPATCH_ONCE` prevents retry. Hashing sources first may make this unlikely, but provides no ordering guarantee.

**Actually reproduced with CPU mocks:** the `Popen` mock invokes `validate_native_entry` before returning to the supervisor, simulating a fast child. Child sees missing `LAUNCH.json`; supervisor subsequently writes the receipt, observes unsuccessful termination, and records failure with dispatch consumed. A separate partial-JSON receipt reproduces decode failure. No subprocess was started. Required repair: an atomic receipt publication plus a bounded parent-to-child startup barrier, constrained by the native deadline and failing closed on parent failure. This is startup synchronization, not permission to retry generation. Add an integration regression that forces child-before-publication and incomplete/failed publication interleavings.

**Staging condition, not an established slot failure:** `validate_native_entry` at line 90 requires kernel `device_minor == physical index`. These are distinct identifiers; the reused minor scanner explicitly handles their remapping. A synthetic otherwise-valid receipt with minor 3 and configured index 7 is rejected. Main must establish that the actual slot has minor 7, or bind admission to its independently verified UUID/index/minor mapping. No live mapping was read here.

## Earlier findings and provenance checks

- UUID forwarding is fixed: native passes independently pinned `GPU_UUID` to the producer's mandatory keyword argument. Timer binding now uses exactly `morning_unix` and constrains lease end against the referenced timer's hard end.
- Direct native entry now requires dispatch, timeout-parent PID/start ticks, config hash, launch deadline, a 0–120-second admission age, and the exact hashed clear root-scanner receipt. Positive and negative CPU receipt probes passed. This is not an OS-level custody attestation or real watchdog exercise.
- Allocation now validates scope, plan, checkpoint, zero optimizer/parent calls, UTC date, and a hash-bound Builder entry containing date and plan hash. R130 terminal conditions are the exact three expected labels, with zero optimizer/parent calls. The prior Boolean-only publication and unchecked-allocation findings are addressed at this source boundary; actual published entry/custody artifacts were not inspected.
- Supervisor exceptions now call owned-session TERM/wait/KILL cleanup. CPU escalation tests and additional TERM/KILL `ProcessLookupError` race probes pass. No real process tree was signalled; a failure receipt alone still must not be treated as proof of slot release.
- Checkpoint checks bind FULL/update 18404, adapter state/base/file manifest equality, and actual adapter bytes to the referenced checkpoint file hashes. Projection checks bind declared ref/hash pairs and exact sorted spec/task-ID/used-seed unions. Source unit tests pass. These checks do not independently establish that staged COMMIT metadata or projection inputs have the claimed provenance; Main's real staging checks remain necessary.

## Producer and scientific boundary

No concrete feedback-versus-gold leakage or FULL/base-isolation blocker found in the unchanged producer/protocol. Feedback is recomputed execution of the attempted expression on the public input, not expected output or verification success. Neutral review receives no receipt; both continuations bind the identical original draft. The reference scorer and verification inputs stay out of constructed messages; source tests check forbidden-field/sentinel exclusion and prohibit reference-scorer access during feedback construction.

FULL uses the fixed adapter; BASE uses the same frozen model under `disable_adapter()` with LoRA-disable flag checks. The reused loader checks mounted base/adapter state and file hashes, frozen parameters, a single default adapter, and unchanged state after collection. Producer tests use CPU doubles, **not real PEFT/CUDA validation**. No independent proof of live OFF-state equivalence, successful loading, or unchanged live weights is claimed. Interpretation remains a 16-task public-TRAIN immediate-revision probe, not learning, persistence, metacognition, held-evaluation, or H1/H2 promotion evidence. Exclusions cover only the declared hash inventories.

## Validation actually executed

Commands run against the final hashed source set, with bytecode disabled and CUDA visibility empty:

```bash
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES= PYTHONPATH=. python3 -B tests/test_orch_r133_code_feedback_guard.py -v
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES= PYTHONPATH=. python3 -B tests/test_orch_r133_code_feedback_collection.py -v
```

Results: **10 guard tests PASS** (0.003s); **22 producer tests PASS** (3.783s). Separately executed stdin CPU probes reproduced R1 and partial JSON; accepted a valid native-entry fixture; rejected wrong parent PID, start ticks, config hash, deadline, stale/future admission times, and admission hash; reproduced the minor/index restriction; and exercised disappearing-group handling at TERM and KILL. Process creation, process identity, clock and signals were mocked as needed. These probes are not committed source regression tests. Main's reported **33 dependency tests were not independently rerun** in this review. Neither production `validate` nor production preparation/verification was run against staged artifacts.

## Exact SHA-256 binding

The five hashes matched before/after the final CPU work, through 21:57:16 UTC. Later source changes require a new bound review; passing tests do not transfer automatically.

```text
208edc66aeae32e14b824d8b583bc28392bb53bd7c3b9fae98e0f93d961dd5f0  gpu/orch_r133_code_feedback_guard.py
cede6f152dab0fffd546a31496377b3f3244ec4893fc143dfc4a1ee722970b67  tests/test_orch_r133_code_feedback_guard.py
1b382863fe2c13addce6693e12b6f77d4ee70afaace79a945d0c57620ccb3085  gpu/orch_r133_code_feedback_collection.py
71e61bd82b7c411a035e1a5f90daa5ce387bfbd4c931b5832b11f76610739d8f  tests/test_orch_r133_code_feedback_collection.py
5b6934536b1de82001619b464d81193b15040f102dd43c36eef2409ace1118fe  research_notes/analysis/orch_r133_code_feedback_20260915/PROTOCOL.md
```

Supporting source sections reviewed (not a complete staged dependency audit):

```text
c109057608b66879f11f3661a6b17d2fc479fd10acc03f4dfea65cedd15743ba  gpu/orch_r119_public_feedback.py
7460e322ddf5b09a96f1fb4a9dde78f4c0d21fb48109eac1810dcb6791abea82  gpu/orch_r109_l1_public_feedback.py
2f4a15f4538f707391716cb89d594a292278ed036572386a5dbed340a2db81a2  organism_v6/orch_persist_code.py
559d8e6ea7002f2651748ba192a57c5cf627381f6a3994d93cb02d63011a3157  gpu/orch_guided_native.py
f7915100d7c9e5b171b8e3bc9af23e6cee00fc09612bb947d5e3c1ea777ee652  organism_v6/orch_guided_bridge.py
a9fc096b66a1fe185f84c15d50f049ce9da8e146fa8dab014c85f2bdda36b28e  gpu/orch_rich_hot_node2_exhaustion_v3.py
8e57909a6c4f2d988a434423a33e7a663c23696ffdb2ce402c2bb03b2fccbb70  gpu/astra_experienced_event_microloop.py
c79f08d18eb2dd989b13555b90ad289d98937c8662b9c01cc1899d80429228b1  gpu/orch_r111_route_admission.py
91027037bf98aa391afe5d89da9814502da57d6b15ad16574b2a7cdef9976c3f  gpu/orch_r110_admission.py
f7136608f4b3fca051b3852a006abf86b704dbf1cfe882f6b8c3b43704ec387e  gpu/orch_rich_hot_a100_minor_scan.py
9902c38ecadeaa06bc02abf184f6a04025a289868f809b63aace5148cd95575e  gpu/orch_rich_hot_a100_scan.py
```

## R136 future-source addendum — 2026-09-15 22:09:15 UTC

**Disposition: no remaining source-level blocker identified in the startup and frozen-flag repairs for FUTURE R136 only, at the exact hashes below.** This closes historical R1 for these new bytes, not for the rejected/previously staged bytes. It is bounded CPU/source review, not live validation, custody confirmation, or a scientific-success claim.

**Historical R133 remains FAILED.** Main reports that the immutable archived run passed startup/minor-7 checks and loaded, then failed with `all_weights_frozen` after four completed calls/five intents. This reviewer did not reopen the native archive or independently verify those counts. The original rejection above is preserved unchanged; neither that run nor its calls are retrospectively approved, repaired, resumed, or retried by this addendum.

### Repair findings

- **Startup race addressed:** `gpu/orch_r133_code_feedback_guard.py:94` writes and fsyncs complete JSON to an exclusive `.pending` file, then publishes through a non-replacing hard link. `supervise` opens an actual stdin pipe and sends/closes the readiness token only after publication returns. Native calls `await_startup` before `validate_native_entry` reads the receipt. The barrier uses deadline-bounded `select` and one bounded `os.read`, not a potentially hanging partial `readline`. EOF, partial/wrong token and silence fail closed; dispatch and generation remain non-retryable. Atomic non-replacement and real pipe/thread child-before-publication regressions pass. This removes the previously reproduced interleaving without claiming an actual process launch was tested.
- **PEFT exit flag repair addressed at the CPU seam:** `gpu/orch_r133_code_feedback_collection.py:340` snapshots already-frozen flags, checks frozen/disable state during the body, and restores the original false flags in an outer `finally` after the adapter context exits. It then asserts exact flag and adapter-enable-state restoration. Body trainability drift and failed enable restoration still reject; context-exit exceptions still propagate after cleanup. Tests reproduce exit-time flag changes, repeated FULL/BASE transitions, body drift, exit errors and previously disabled state. They use CPU doubles, not installed PEFT, real weights or CUDA. Loaded-state/file hashing remains a required native check, not something this repair's tests prove.
- **Future-run separation remains a staging requirement:** Main declares an entirely fresh R136 seed/tasks excluding all 16 R133 specs, with no historical-input retry. A synthetic 16-spec projection/union and fresh-seed probe passed and rejected its old seed. Actual R136 exclusions, seed, prepared task bytes, checkpoint provenance, allocation, publication, lease and staged source manifest were not opened or attested here. Main must bind them to the new source hashes and preserve the old archive. The earlier minor/index mapping caveat remains for any future allocation; Main's report of minor 7 on R133 is not a new live scan.

### Independently executed validation

```bash
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES= PYTHONPATH=. python3 -B tests/test_orch_r133_code_feedback_guard.py -v
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES= PYTHONPATH=. python3 -B tests/test_orch_r133_code_feedback_collection.py -v
```

**13 guard tests PASS (0.015s), 27 producer tests PASS (3.660s).** Additional stdin CPU probes used real pipes: closed-writer EOF and a partial token with writer still open rejected immediately; a silent open writer rejected after 0.150s under a shortened deadline. The synthetic prior-16 exclusion union produced 16 disjoint new specs and rejected the used seed. These additional probes are not committed source regression tests. No model/GPU calls, live scans/signals, actual subprocess launches, native archive/task reads, or fixed32/FINAL data reads were performed. No Main/Ptolemy source, Git, or shared-ledger files were edited.

### New exact SHA-256 binding

Hashes matched before and after this addendum's CPU validation. These replace the earlier source binding **only for the future-source repair disposition**, not for the historical review.

```text
094fe8dfc80f51d0048bf12d3b998f9393d1b5ef981a9082cdf28af5523d8261  gpu/orch_r133_code_feedback_guard.py
16e87c840dfd97dd6b1a7ca58a3243da723c0ae70f9b560ab4fdb75eb0db3f22  tests/test_orch_r133_code_feedback_guard.py
79b93767ed022c4aebb91f3d6aada480998effe2a07331e86ad59c5ad56dd4dd  gpu/orch_r133_code_feedback_collection.py
139db9ad31f3ab387d72bcbeafd5fd07705d7f44dc75d93a302422176c58157b  tests/test_orch_r133_code_feedback_collection.py
5b6934536b1de82001619b464d81193b15040f102dd43c36eef2409ace1118fe  research_notes/analysis/orch_r133_code_feedback_20260915/PROTOCOL.md
```

Pre-addendum historical review SHA-256: `34ae97b4144d101ec463a0a6bf8c2ac69c3642441e1f4109e0f813127ed29324`. New changes after these hashes require fresh review; source tests never imply that R133 or R136 passed natively.
