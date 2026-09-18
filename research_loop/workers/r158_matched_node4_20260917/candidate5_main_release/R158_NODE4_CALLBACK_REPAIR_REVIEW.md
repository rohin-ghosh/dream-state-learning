# R158 node4 capacity callback routing — independent narrow repair review

## Verdict — September 17, 2026, 04:55 UTC

**APPROVE the narrow callback-routing repair at the two exact hashes below.**
No concrete blocker was found in `initializer_profile` or its integration
into `validate_environment`. This verdict does not approve saved-initializer
restoration, another cohort, source staging, admission, a GPU launch, or
scientific claims. A later combined review remains necessary for the separate
restoration changes when ready.

Main reports attempt3 saved COMMIT and then failed the old
`designated_node5_initializer_only` check before measurements. That is
consistent with the old source guard, but this reviewer did not inspect live
attempt3 data or independently attest its model/checkpoint state. This repair
does not turn that failed callback into successful capacity evidence and does
not permit overwriting or recreating the saved initializer.

## Exact reviewed bytes

| File | SHA-256 |
| --- | --- |
| `gpu/orch_r151_memory_probe.py` | `bca194706e6f758f4384a70e0597d8357f583e3098456ef7b5f6832b8e69c075` |
| `tests/test_orch_r151_memory_probe.py` | `2b172a0e95dc6f8211f4ab8fe9790fe7d7b924d92db17fbc47dc08d42cf6f43b` |

Both hashes were checked before and after CPU validation and remained stable.
No moving R150 native/restoration tests or node4 helper were reviewed. No
source edits, GPUs, remote actions, hidden data reads, or coordination/staging
writes were performed. The only authored repository artifact is this report;
existing reports and concurrent work remain untouched.

## Delta verification

An independent in-memory reconstruction removed only `import socket`, the
new `initializer_profile` function, and its call in `validate_environment`,
restoring the previous node5 guard. The resulting **whole-file SHA-256** is
exactly the previously reviewed source:

`6c47e9f49b696f036e2ab8d990bcdb5872c9ad3dcdf02c09913aefce0762b619`.

Likewise, removing only the added profile/environment test block and restoring
the prior expected error label recovers the prior test whole-file SHA-256:

`68a15210f8d0bfeacf2af0202603d46b61637acf238a98e6170d4713dc2bf734`.

These are byte-identity checks, not merely a claim that a diff looked small.
No files were rewritten to perform them. They establish that the remaining
allocator, admission, numerical, timing and cleanup code is unchanged.

## Routing correctness and retained guards

`gpu/orch_r151_memory_probe.py:34` now accepts precisely the following
host/physical/UUID combinations, always with `matched_arm=parented_learning`
and an integer physical index (booleans/floats are not accepted):

| Profile | Exact hostname | Physical | Exact GPU UUID | Additional source constraint |
| --- | --- | --- | --- | --- |
| `R151_NODE5` | `[REDACTED_HOST]` | 0 | `GPU-f237c5b5-c2a3-b377-92ee-46cf2658db9a` | No new source namespace restriction; prior device/arm route retained with explicit host restriction. |
| `R158_NODE4` | `[REDACTED_HOST]` | 5 | `GPU-2e7eb3b8-9b0b-3729-f5ff-2bbdad6a4a30` | `source` directly below an `orch_r158_matched_node4_*` directory directly under `/localhome/local-rohing`. |

Cross-host combinations, other hosts, wrong node4 device/UUID, frozen or
unparented arms and wrong source namespaces are refused. Node4's namespace
check is lexical routing, not a replacement for source provenance/canonical
path validation or admission. This review does not independently re-audit
those upstream mechanisms or attest any live hostname/device mapping.

`validate_environment` obtains the hostname from `socket.gethostname()` and
then continues through the same guards, with no early successful return:

- Exact plan-file hash in `R125_ADMISSION_PLAN_SHA256` and exact cohort hash
  in `R150_COHORT_SHA256`.
- Exact UUID-valued CUDA visibility, exactly one visible CUDA device,
  `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`, and absence of the
  alternative `PYTORCH_ALLOC_CONF` variable.
- Context 16384, segment 512, zero optimizer steps and empty optimizer state.
- Bound runtime and prior-proof file reads with unchanged expected hashes,
  prior-proof validation, model/runtime verification and actual AdamW type.

The entire `initial_capacity` body is byte-identical to the previous reviewed
body: full/suffix shapes, loss/gradient tolerances and assertions, paired RNG,
four-anchor objective, headroom floor, deadline acceptance, cleanup and
failure receipts are unchanged. There is no optimizer step, generated data,
numerical bypass, restored-state relaxation, or new capacity evidence in this
routing repair.

## Independent CPU evidence

Focused checked-in regressions: **18 passed, 422 deselected in 0.80s**:

```bash
CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tmp/r136-pytest-support:$PWD python3 -B -m pytest -q -rs -p no:cacheprovider tests/test_orch_r151_memory_probe.py -k 'initializer_profile or initializer_host or actual_node4_environment or only_designated'
```

No broad capacity/restoration suite was rerun against moving parallel work.

Additionally, an inline CPU harness compiled the **exact AST function bodies**
of `initializer_profile` and `validate_environment` from the reviewed file,
with synthetic native/OS/socket/runtime services, without importing model or
CUDA runtimes. **32 cases passed**, 16 for each admitted profile:

- Valid configuration reaches both bound-file checks, prior-proof validation
  and model verification with unchanged runtime/prior-proof identities.
- Wrong plan/cohort hashes are rejected.
- Wrong CUDA UUID, absent/wrong allocator, conflicting allocator alias and
  multiple visible devices are rejected.
- Wrong context/segment, nonzero steps, nonempty state and non-AdamW optimizer
  are rejected.
- Injected runtime-bound read, prior-proof validation and model verification
  failures propagate instead of being bypassed by either profile.

This is control-flow/guard evidence, not actual hardware capacity or runtime
numerical equivalence. The 32 inline cases are not extra pytest passes.

Main's supplied
`research_loop/workers/r158_matched_node4_20260917/NODE4_CALLBACK_REPAIR_CPU.log`
reports **591 passed in 9.16s**. Its independently computed SHA-256 is
`0643a4b27cb98e78b4eeff4ce1bececf11024f3f1b80c330441566eb129ddde9`.
That count is Main-provided broader evidence, not an independent rerun or
approval of every file involved in that suite.

## Explicit exclusions / next boundary

Bernoulli's saved-initializer restoration hook in R150 native/tests and the
node4 helper are outside this review. No claim is made about exact attempt3
COMMIT adoption, checkpoint/optimizer/RNG joins, avoiding adapter
regeneration during that future path, or its combined interaction with this
callback. Those moving bytes require their later scoped combined recheck.
No failed artifact is cleared and no automatic retry is authorized here.

No measured optimizer reserve, successful initialization, GPU readiness,
learning improvement or other scientific claim follows from this approval.
The final whole-file hash of this report is emitted separately.
