# R142 training-memory repair and recovery scope

## Operator decision — September 16, 2026, 07:04 PDT

The watcher requests restoration of support_none from sleep10 with expandable
CUDA allocator segments. Main authorizes that allocator-only runtime change;
no smaller context, dropped rehearsal, altered anchor weight or reduced
presentations is authorized by this repair. The existing training microbatch
already contains one sequence, so a smaller microbatch is not an available
fix in this implementation.

The original child crashed during **sleep11**, not while creating sleep10.
Sleep10 is its last complete checkpoint, with 410 optimizer steps. The journal
retains two subsequent generations and one UPDATE at step411. Recovery must
preserve that partial update as abandoned computation, restore the saved
adapter/AdamW/RNG, reconstruct RNG through verified replay of both generations,
and recompute the pending sleep. Replacement updates must not be added to the
abandoned update as if both survived in the final weights. Exact unavailable
post-step411 weights are not claimed. Parent/history/carry/raw records remain
preserved; this is checkpoint recovery, not fresh initialization.

Confucius owns this support recovery and its new contained launcher. Mencius
owns teach-perception's separate exact-target exclusion and sleep15 recovery.
Neither edits the other's files or running children. CPU tests and the existing
provenance/device checks remain required before each launch; no further
conversational approval is needed inside this acknowledged scope.

## Memory evidence and implementation constraint

The original support log reports 31.15 GiB allocated and 7.44 GiB reserved but
unallocated, with 5.49 GiB free while requesting 7.08 GiB. Fragmentation is a
plausible contributor, not a demonstrated exclusive cause. The native code
processes one child sequence and four anchor sequences with separate backward
calls. A longer rehearsal list increases total sleep work; it does not batch
all rehearsal rows into a single forward pass. Long retained prefixes can
increase individual forward/backward memory requirements.

The original systemd launcher uses `/usr/bin/env -i`. An outer shell export
therefore does not install the repair. The new contained command must include
`PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` explicitly, and the running
native process must verify its received value. Preserve its single GPU UUID,
actual device minor, non-root execution and denial of seven foreign devices.

Installed Torch is 2.13.0+cu130. Its installed primary-source header
`torch/include/c10/cuda/CUDAAllocatorConfig.h` checks
`PYTORCH_CUDA_ALLOC_CONF` before the `PYTORCH_ALLOC_CONF` alias. The retrieved
PyTorch 2.13 CUDA memory-management documentation describes expandable segments
as experimental and intended to handle changing allocation sizes. Enabling
it is not proof of adequate capacity. The acceptance evidence is actual
advancement through the formerly failing sleep, saved checkpoint integrity,
and observed allocated/reserved/peak memory—not just a successfully loaded model.

Retrieved primary source: `https://docs.pytorch.org/docs/2.13/notes/cuda.html`.
The unversioned stable URL redirected in HTML to 2.14; the version-matched 2.13
document was fetched separately rather than substituting newer documentation.

## Other children

Do not restart all live children merely to export an allocator variable.
After validating the support repair, apply the same runtime-only setting at
verified saved boundaries, retaining exact child state and parent ownership.
Record each applied environment and source binding separately; until then the
other children must not be reported as having received this repair. If the
allocator alone is insufficient, diagnose the actual live tensor peak before
proposing another memory implementation change. Do not silently shorten
history, drop old rows, or change the training objective.
