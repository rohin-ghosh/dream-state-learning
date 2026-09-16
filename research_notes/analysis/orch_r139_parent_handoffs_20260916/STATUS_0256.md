# R139 Main status and F2 allocation — September 16, 2026, 02:56 UTC

F1 controller is **armed**, not yet released/reloaded: node5 PID2542861,
stage2 `/localhome/local-rohing/orch_r139_F1_astra_handoff_20260916_attempt2`.
Main GO SHA256 `29f945f59da585abf77477960b8629b23e678629e46c6a6fbe64ac87a1a4b58b`
binds publication b28bfa75 and READY e95b496b.... The old child continues training
while the controller waits for a safe boundary. At02:50:54 it was C55 with463
current-sleep updates and a fresh update timestamp; at02:55 controller alive,
no release/launch and no error log.

F1 Astra dispatcher on the VM is waiting for the verified restored consumer:
PID2147783/start163398254, command SHA256
`f7178e1cd50f450feecd4935fff7dd2ec33c096d302ac422baf4c9f6fc5e6777`.
Runtime `/data/home/rohing/courier/runtime/r139_f1_dispatch_20260916_attempt1`;
published source de78af6e3a175fb9f2843649709a865a2f0952e5.14 local CPU tests
passed. Its future-only cutoff is the actual saved handoff boundary, so natural
new-consumer requests queued during broker preparation are not mistaken for old
history. It cannot process old claims/responses/refusals. No F1 Astra call yet.

## F2: authorize the corresponding exact-state transition after publication

Allocate existing node5 physical1 to the same F2 child. This is the same
non-material R121 model-choice repair and no-reset interpretation as F1; frozen
base, saved adapter/AdamW/CPU+CUDA RNG, ordered rows/history, carry, task sets,
anchor mix, quotas, deadlines and original dispositions remain preserved.
Source/tasks/visibility and claims are not broadened. No old readout or parent
request is replayed. The new immutable segment uses truthful Astra identity.

Main reran26 local tests and the actual staged CPU broker/native check PASS.
Worker native26 tests plus10 frozen R124 regressions PASS. Original actor
3953966/start3542788 remains live; staging observed committedC44,
native1140,parent130,optimizer15508. This is not the actual release cursor.
Exact source/manifest hashes and commands are in `F2_HANDOFF.md` / `F2_READY.json`.
After this publication Main may authorize the existing request b1302fc8... and
its7af97488... source manifest, start its safe release, verify READY, remove only
the identity-checked empty stale queue lock, start its prospective Astra broker,
and then the original-venv successor guard with fresh strict admission.

Native root `/localhome/local-rohing/orch_r139_math_astra_handoff_20260916_v1/F2`;
controller `/data/home/rohing/courier/runtime/r139_f2_astra_handoff_v1`.
Broker manifest428713960d2bb44ed804228f0a133861a486e8598c250703d6fc8fbc8a0eeddc.
F2 retains original384-call/8192-output caps, not A2's larger call allocation.
No F2 release/broker/child launch is claimed by this allocation.

## F4 and scientific evidence

F4 source/tests and plan are staged only; Main reran15 CPU tests PASS. It is a
frozen-gen1-adapter elicitation lane, not an active AdamW learner. Its existing
06:00 FINAL timer is old-PID-bound: successor-aware custody is being implemented
before release, preserving the same8-call quota and lease wall. No F4 signal,
timer replacement, release, resume or new provider call yet.

R138 public-code interface audit is complete: canonical FULL4/16, BASE0/16 at
every stage remain unchanged. All48 complete BASE outputs omit quotes around
the expression value; diagnostic extraction of that existing expression yields
BASE4/16 draft,6/16 feedback,5/16 neutral, versus FULL4/16 throughout. Only one
feedback-exclusive diagnostic pass; no retained-learning claim.19 Main CPU
tests PASS. This explains an interface confound, not permission to replace the
benchmark scorer or train on held cases. Details are in
`../orch_r138_code_interface_20260916/RESULTS.md` with bound raw hashes.
For a future four-condition skill-acquisition comparison, predeclare a common
output interface before new data collection; do not attribute quote-format
differences to semantic skill acquisition. No new benchmark is launched here.

Independent review of R132's matched19428→24036 audit passed the narrow claims;
it independently verified256 capability captures and the checkpoint/scorer
bindings. A suggested future hardening is an explicit equal-cap assertion;
the inspected actual caps were all512. Current scored gains remain zero.
