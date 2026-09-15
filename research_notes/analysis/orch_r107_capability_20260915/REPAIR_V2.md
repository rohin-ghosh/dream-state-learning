# Native layer-state assertion repair

September 15, 2026, Builder non-material repair. The first native process
loaded the correct MATH764 FULL adapter, then failed before inference at the
LoRA-ON assertion. One reservation, zero generated responses, zero updates.
The original PLAN/READY/LAUNCH/REQUEST/LOADED/CALL/FAILED/native.log remain
untouched under the original node3 diagnostic root.

Root cause: the checker selected every module with an attribute named
`disable_adapters`, including callable methods on base-model containers, not
just boolean activation state on actual LoRA layers. The repair selects layers
with `lora_A` and `lora_B`, then requires their boolean state to match ON/OFF.
It does not weaken the required active/disabled state, alter model weights,
change task prompts or scoring, or permit training. Regression now includes a
container with a callable `disable_adapters` alongside a real LoRA-like layer.
124 local suite/runner tests pass, including complete and failed workflows.

Prospective repair root: original node3 root plus `/repair_v2`. It must bind
new exact source hashes and READY, preserve the original suite/checkpoint and
both original deadlines, and receive fresh privileged admission/publication.
The new explicit allowance is64 calls; preserve the old failed reservation
separately, aggregate reservation ceiling65, at most64 actual generations.
This is an explicitly logged repair attempt, not an invisible retry or reset.
No repair launch claimed until the new receipt exists.
