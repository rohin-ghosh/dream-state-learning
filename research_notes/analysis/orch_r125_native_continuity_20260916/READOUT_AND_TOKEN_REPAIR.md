# First native cycle and bounded repairs

September 16, 2026. `STATUS_0623.json` contains the inspected node receipts.

The resident loaded at06:12:28 UTC, generated its first segment at06:13:12 UTC,
completed one real sleep with48 optimizer updates and a changed LoRA while
verifying the frozen base, then generated three more segments. Across both
cycles:6 generated segments,1557 generated tokens,1 cap hit. First-sleep
exposures:8816 child target tokens and2815 anchor target tokens; anchor objective
weight0.25. This demonstrates one native generation–sleep–continuation cycle,
not retained improvement or stable unattended operation.

Two native problems remain visible rather than being counted as success:

1. Both fresh-process readouts failed before any model call: torch's `_CUuuid`
   string omits the `GPU-` display prefix. Repair normalizes only that prefix
   and still rejects a different UUID. Corrected readouts use a new `_r2`
   artifact namespace; old failures are never overwritten or counted complete.
2. The second sleep exited at06:17:03 UTC before optimizer updates because one
   genuine generated token was Qwen's `<|endoftext|>` (pad ID151643). The prior
   encoder treated it as role-control injection. The scoped repair accepts this
   exact end-of-text token as an actual child target, preserving native IDs and
   all prefix masking; role-control tokens remain forbidden. No row is silently
   shortened, relabelled or dropped.

The child is currently stopped, not claimed live. A checkpoint-pause observer
found its process already gone and sent no signal. The earlier manual boundary
check did not find a completed sleep and immediately resumed the same actor.
Checkpoint1, all raw responses, history, AdamW and saved RNG are preserved.

Recovery must not silently rewind or reset the child: the three post-sleep1
generations are already committed, but their RNG frontier was not separately
saved. The proposed bounded repair restores checkpoint1, reconstructs RNG by
replaying those exact completed local generation calls, and requires identical
native token IDs/text/termination flags under the unchanged generation method.
These are explicitly reconstruction calls, not new TRAIN rows or parenting.
Any mismatch stops recovery. Only after proof that the failed sleep made no
update may the original pending sleep complete. No uncertain request replay,
historical deletion, adapter reset or parent-refusal retry is authorized.

This limitation is an engineering finding: current exact recovery is narrower
than arbitrary crash recovery. The full goal remains active and unproven.
