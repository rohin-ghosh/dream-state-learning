# R158 candidate4 saved-initializer recovery — independent bounded review

## Verdict — September 17, 2026, 05:10 UTC

**APPROVE the bounded saved-initializer recovery implementation at the exact
four source/test hashes below. No concrete blocking defect found.**

Scope: recovery of the specifically pinned, failed attempt3 premeasurement
initializer into a new matched cohort; exact checkpoint payload preservation,
loaded adapter/AdamW/RNG checks before and after capacity, fail-closed source
and consumer joins, and preservation of the no-recovery construction path.
This is **not GPU launch authority**, successful live restoration/capacity
evidence, approval of scientific claims, or a general recovery mechanism.

Only this new review was authored. No source/test/coordination edits, reverts,
old artifact mutation, source freezing, preparation, remote execution,
GPU/model calls, hidden-data inspection, or package installation occurred.
CPU probes used temporary synthetic artifacts with bytecode/cache writes
disabled. Existing reviews and parallel work remain untouched.

## Exact reviewed bytes

| File | SHA-256 |
| --- | --- |
| `gpu/orch_r150_matched_native.py` | `f8919b47e63c759d2a15a89eaaa1e28b4c16a7c1d4dcf0fd5efa320227e3fed9` |
| `gpu/orch_r158_matched_node4.py` | `5b2b295215cc5ae8537059fdd20a9e178d56a59fd10dc511030bb9fa3d9102e1` |
| `tests/test_orch_r150_matched_native.py` | `3460cbc1ecfb85bb783719645d4e10db701f6e42f0f1b31b853d7f9e3efb841a` |
| `tests/test_orch_r158_matched_node4.py` | `00c2156383476ac2cd08ccf350d2b8e166e7e34e882f11e9591f37cbcc62ce6a` |

These hashes match local files, candidate4 status and receiving CPU source
inventory. They remained unchanged across the review's source/hash checks.
Approval does not transfer to changed bytes or an arbitrary checkpoint.

The callback remains at its previously approved routing-repair hash:
`gpu/orch_r151_memory_probe.py` =
`bca194706e6f758f4384a70e0597d8357f583e3098456ef7b5f6832b8e69c075`.
Its prior scoped review is preserved at
`research_loop/workers/R158_NODE4_CALLBACK_REPAIR_REVIEW.md`, SHA-256
`94b03bd9665f7663c9925f77ea6e60930eaa92b56a18ac424f9de27467406024`.
That routing approval is not expanded into measured capacity here.

## Source binding — fail closed

`gpu/orch_r150_matched_native.py:45` requires exact reference fields,
absolute resolved nonsymlink regular files, and byte hashes before parsing.
`validate_initialization_source` at line 55 then permits only the fixed
attempt3 namespace and these hard-coded source identities:

Root: `/localhome/local-rohing/orch_r158_matched_node4_20260917_attempt3`.

| Relative original artifact | SHA-256 |
| --- | --- |
| `common_initial/COMMIT.json` | `f1fdb87d92e3e2efc401583faa02f2d6c5a8de07f5dcd20866215c8cb54a332c` |
| `parented_learning.PLAN.json` | `7ec0fc2375b7ca1f691cb158bfd361474c2ba23810b8ee925e9af2eea3dfeb56` |
| `common_initial/capacity_validation/RESULT.json` | `630f3e54febf7da680d1f5eb34340a0b2bb2cbfa26418387fe059c60a49f1eb9` |
| `attempts/initialize-parented_learning-attempt1/LIFECYCLE.json` | `9dcbcc3922f19a07c99d211af463d4e4a7bccb21d605e40bdce0a9e2afb5ed65` |

The code rejects chained recovery, wrong original arm/device/cohort, an old
INITIALIZED file, any original arm root/birth, or a different failure class.
The allowed failure must be the exact old node5 routing refusal with FAIL,
zero recorded updates/generation, no stream/scientific evaluation, unverified
restoration and no bounded/maximum capacity result. The pinned lifecycle
requires verified service exit, empty cgroup and return code 1. This does not
generalize to OOM, partially measured, updated, or still-running initializers.

The original checkpoint verifier checks its payload hashes and zero steps;
adapter/optimizer paths must belong to the pinned common-initial directory.
The original plan is validated against its cohort. The new common recipe
must equal the original, except relocated source/startup file paths; startup
content identity remains, as do seed, base/model, objective, context, decoder,
boundaries and deadlines. New arm devices must match the original cohort.
Recovery requires the capacity schema, a different R158 node4 cohort root,
the prescribed per-arm roots and its new `common_initial` namespace.

`initialization_source` is included only when present in common configuration,
so it is bound identically into all three plans and the cohort. Missing it
from one arm, altered recipe, tampered original receipt, wrong failure,
symlink/null reference and evidence of original admission/birth are covered
by passing regressions. Synthetic rehashed negatives alter fixture pins only;
the production pins are not relaxed.

## Restoration and publication ordering

At `gpu/orch_r150_matched_native.py:400`, the admitted designated initializer
requires a nonexistent destination and a capacity callback before copying or
constructing the recovery child. The recovery branch:

1. Revalidates the pinned original references and checkpoint.
2. Uses the existing exact-file copy routine to a new common-initial directory.
3. Checks copied checkpoint payload hashes against the original checkpoint.
4. Constructs `MatchedChild(plan, checkpoint)`, not `MatchedChild(plan)`.
5. Calls actual `verify_loaded_initial` before capacity validation.
6. Requires a PASS callback, calls loaded-state verification again, and
   requires before/after observation equality.
7. Runs the actual semantic initialization-validation consumer before writing
   INITIALIZED with source reference and pre-capacity observation.

**Payload identity, not identical relocated COMMIT bytes:** adapter files
and `optimizer_rng.pt` are copied byte-for-byte. New COMMIT metadata rewrites
their destination paths; CLONE_PROVENANCE retains the original COMMIT path/hash
and new COMMIT hash. The original COMMIT and payloads are not rewritten.
Do not describe the two path-bearing COMMIT documents as byte-identical.

The supporting existing `NativeChild.__init__` checkpoint branch loads the
saved adapter directory, exact optimizer state and parameter order, optimizer
steps, CPU/CUDA/Python RNG, and verifies adapter state. It skips the fresh
`initialize_adapter` and `seed_rng` branch. Its Engine uses the saved PEFT
adapter rather than treating a fresh seed as equivalent evidence.

The unchanged `verify_loaded_initial` checks the actual checkpoint files,
empty AdamW state and zero steps, exact optimizer groups, ordered adapter
parameter names, adapter hash, CPU RNG, exactly one CUDA RNG state and Python
RNG against the saved payload. The observation includes checkpoint-file and
RNG hashes. This is more than equality of two self-reported scalar counters.

Before-verification, callback, after-verification, or consumer failure blocks
INITIALIZED. Copied COMMIT/partial evidence remains, and destination reuse is
refused rather than silently retrying. There is no new history, inbox or
training-row copy, optimizer step, or generated child data in this path.

## Capacity consumer and fresh path

`verify_initialization_validation` at line 172 adds recovery provenance checks
before the existing capacity-proof checks: exact initialization-source ref,
before/after observation equality, a structured observed-state record, and
checkpoint payload hashes matching the pinned source. It then still requires
the new initializer's bound PASS capacity receipt, restoration, numerical
evidence, runtime/prior-proof pins, shapes, headroom and deadline evidence.
The original FAIL receipt cannot serve as the new capacity PASS.

All-arm `run` acceptance remains before arm-root/model construction. Recovery
provenance does not bypass the existing consumer. The independent combined
probe below verified successful consumption for all three arms and rejection
of a rehashed inadequate maximum-shape receipt before INITIALIZED publication.

With no `initialization_source`, the original fresh-construction/checkpoint-
save branch remains; it does not invoke the recovery copier or source reader.
Common configuration does not acquire an implicit recovery field. There is
one deliberate strengthening to publication: the semantic capacity consumer
now runs before INITIALIZED for both branches. With no capacity schema it
remains a no-op; with a required schema, inadequate callback evidence cannot
be published as successful initialization. Thus the fresh construction path
is preserved, not a claim that the whole initialize function is byte-identical.

## Node4 integration / receiving binding

`gpu/orch_r158_matched_node4.py:250` accepts an optional initialization-source
reference, binds it into each plan and validates it for each arm. CLI prepare
passes that option through. CPU initializer-profile preflight runs before
creating control/attempt directories. Existing exact host, empty CUDA
visibility, source, intake, publication, lease, CPU and Main-freeze gates remain.

REPAIR_FILES now includes this helper and its regression file, in addition to
the callback/core and TRAIN assets. `verify_repairs` still compares all pinned
source bytes and test-log hashes; freeze requires bound Main dispositions.
`verify_cpu` still requires the actual receiving host and whole source
inventory/log joins. No automatic prepare, freeze or Main GO was performed.

The supplied receiving CPU inventory records staged R125 native as
`bcd716db469665d6c2070ed46d4b910d619b7366b66af2891c9ed71a5e069af6`,
not the local unpatched supporting source
`cdb54252763472fd21ea12fd7694b208d968422c375dbf0647088cde736e6d48`.
This distinction is retained: the existing staging suffix transform is
sleep-only and enforces preservation outside sleep. This review inspected
the checkpoint constructor in the local supporting source and does not
mislabel local tests as execution of the staged model runtime. Engine source
inspected: `gpu/astra_experienced_event_microloop.py`, SHA-256
`8e57909a6c4f2d988a434423a33e7a663c23696ffdb2ce402c2bb03b2fccbb70`.

## Independent CPU validation

**185 passed, 1 skipped in 4.98 seconds**:

```bash
CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tmp/r136-pytest-support:$PWD python3 -B -m pytest -q -rs -p no:cacheprovider tests/test_orch_r150_matched_native.py tests/test_orch_r158_matched_node4.py
```

The one skip is the actual receiving staged-source/original-path fixture at
`tests/test_orch_r158_matched_node4.py:247`; it is separately exercised by the
receiving four-test evidence, not counted as a local pass.

An additional independent inline synthetic harness exercised **real**
`initialize`, source validation, checkpoint copying, `verify_loaded_initial`
and `verify_initialization_validation` without mocking either verification
gate. Only child tensor/model services and the capacity producer were
synthetic. Five combined cases passed:

| Case | Observed result |
| --- | --- |
| Valid copied payload plus complete bound capacity proof | INITIALIZED published; actual before/after observations equal; all three arm consumers accept. |
| Wrong adapter on restore | Refused by `actual_shared_initial_adapter` before callback. |
| CPU RNG changed during callback | Refused by `actual_common_CPU_RNG`; no INITIALIZED. |
| Optimizer groups changed during callback | Refused by `actual_initial_optimizer_groups`; no INITIALIZED. |
| Callback returns PASS but rehashed proof lacks required headroom | Refused by `actual_maximum_shape_capacity_headroom`; no INITIALIZED. |

Every case retained identical original temporary artifact bytes, preserved
the copied COMMIT and created no arm histories. These are five extra synthetic
control-flow checks, not extra pytest passes, actual model restoration or
real numerical/GPU capacity results.

## Supplied evidence / preserved fixture failure

Status: `research_loop/workers/r158_matched_node4_20260917/CANDIDATE4_RECEIVING_STATUS.json`,
SHA-256 `50dd0e258bc529dcd705dbf5e6cb48b8148863a653aa4d5b4bd46ba3405e75bf`.
It records an unfrozen/unprepared candidate, no GPU calls, no original-state
mutation or checkpoint copy, and pending review. I independently checked all
four owned-file hashes, its local log and all five receiving artifact hashes,
the receiving CPU inventory's four reviewed-file joins and both log joins.

| Artifact under the candidate4 worker directory | SHA-256 | Evidence |
| --- | --- | --- |
| `RECOVERY_COMBINED_CPU_FINAL.log` | `905a2954393356f25918be6873ddee1dcdf807300a091d7804b2b3aed0540f76` | Author-side 938 passed, 4 skipped, 24.97s. |
| `candidate4_inputs/CPU.json` | `fabaab0f7ad0d306cb7377d2dc502f93343c459bfecdc0fd86cb16dc0ee038b6` | Receiving host `[REDACTED_HOST]`, PASS/exit 0, source inventory and logs. |
| `candidate4_inputs/CPU_TESTS.log` | `32c1d43cbb972786d82863b6a6cb4591b65d3283aac7b3c947828a4f88894e3d` | Receiving 800 passed, 5 unpatched-native-fixture skips, 15.08s. |
| `candidate4_inputs/ACTUAL_PROFILE_AND_INSTALLED_TESTS.log` | `68d662c6a85c67397691a31db63087b1d850ad4867d59336ae46efd3f7f8d0c1` | Actual source/original-reference/profile test plus three installed adapter tests: 4 passed, 1.77s. |
| `candidate4_inputs/ACTUAL_PROFILE_PREFLIGHT.json` | `6277a559c9f630b6246aa237ce52f7a774eaead5f2bc0d556564343bf4ad7817` | R158_NODE4 profile; zero GPU/model calls; no numerical capacity claim. |
| `candidate4_inputs/INITIALIZATION_SOURCE.json` | `07f92a934f895a84d88e9ef2e6d28a37bb2dabd01024c84fd81dfeae3b3361a1` | Exact attempt3 reference document matching the four hard-coded pins. |

Worker directory in that table:
`research_loop/workers/r158_matched_node4_20260917/`.
These supplied runs were not independently re-executed on node4 by this
reviewer. The actual receiving-plan test calls `plans` without replacing
source validation, so its recorded pass covers reading/validating the real
original references and checkpoint file hashes. It does not load an actual
child model or establish restoration of live optimizer/RNG tensors.

The earlier `RECOVERY_COMBINED_CPU_COMPLETE.log` is preserved at SHA-256
`e8253353982bcec2feaba8184f8deae0cfac6cb06d6f858471fdb10d556b9f25`:
**937 passed, 1 failed, 4 skipped**. I inspected its failure and the latest
COORDINATION disposition: the test overwrote the newly pinned helper with
`helper = True` after computing source hashes, correctly triggering
`actual_repaired_source_bytes`. The final fixture removes that redundant
overwrite. The source gate remains enforced; the regression now passes in
the independent focused run. The original failure is neither erased nor
relabeled as a pass.

## Remaining limits

No blocker is carried for this exact bounded implementation. Actual
saved-tensor restoration, pre/post probe equality, a valid new capacity result
and lifecycle completion still must succeed on the admitted execution path;
CPU success is not a substitute. The old failure and original saved state
must remain preserved. New source/receipt bytes or a different failure/source
checkpoint require a newly scoped review, not reuse of this approval.

No parent-helper, unrelated TRAIN/evaluation, lease, generalized recovery,
measured reserve, scientific-improvement or GPU-readiness conclusion is made.
Main owns any subsequent release/admission decision. This report grants no
GPU launch authority. Its final whole-file SHA-256 is emitted separately.
