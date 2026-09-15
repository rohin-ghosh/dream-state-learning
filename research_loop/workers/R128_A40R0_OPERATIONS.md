# R128 a40r physical0 operational slice

## Scope — September 15, 2026, 20:43 UTC

Main/user assigns only a40r physical0 lifecycle diagnosis and existing-tested
bounded recovery if available. No node5/provider changes, no other GPU
operations, no credential work or safeguarded-call retries. Main owns Git.

## Actual lifecycle and failure

Wrapper-only observation **20:44:33 UTC**: physical0 UUID
`GPU-5b370d4d-bdcc-21d5-cf06-e9bea52e602d`, 0MiB, 0% instantaneous utilization,
no nvidia-smi compute processes. This is NOT a fresh admission or availability
claim. Original actor774742 and guardian774733 absent.

Exact original route owner/lane is Poincare's `node1_7` BASE-context lineage,
relocated to a40r0 at17:26, not a CODE model or an L1 training actor:

`/localhome/local-rohing/orch_r109_route_20260915_node1_7_attempt2/lease_r120_v2/campaign_node1_7`

`FAILED.json` records **19:41:17.880 UTC**, ValueError `uncropped_context_fit`.
`GUARDIAN_FAILED.json` records19:41:20.152, `native_failure_no_replay`;
`TERMINAL.json` is FAILED. Existing RELEASE receipt is preserved. Thus the
20:14 empty slot was a crashed/ended actor, not a normal readout reload or
successful bounded completion. No current reservation for a replacement was
established by this inspection.

Last committed context checkpoint C51 SHA
`5d3f9376329e6074c1af1a8de937a6027853ca7e1223f9f68fe6d60a17a16968`.
Failure counters: 2005 native completed,78 parent completed,30 parent missing,
104 TRAIN episodes,711 TRAIN segments,196 held episodes,49 context sleeps,
**0 optimizer updates**. Ledger ends at native2005 and parent110, cycle52.
Adapter is null: no optimizer state exists to restore; checkpoint contains no
RNG snapshot. Existing generation source is greedy; no RNG-restoration claim.
Held response contents were not read.

## CPU-only exact context proof

Reconstructed the unissued cycle52 reflection turn2 from already captured
TRAIN parent110 request messages plus its already COMPLETE, hash-verified
parent plan, using the frozen parent formatting. Offline native tokenizer only:
**32,965 prompt tokens versus32,768 configured context**. The guard executes
before reserve(); there is no CALL_002006 and no native2006 reservation.
Last actual child output is CALL_002005, first C52 reflection. Parent110 was
completed but has no subsequent child call; it must not be retried or falsely
labelled consumed. All raw messages/plans remain node-local.

Exact reconstructed-message SHA
`8febea24661df7079332b12f35a5e4e39774600db41c67bd07ed374d66e05561`.
`CONTEXT_CPU_PROOF.json` contains tokenizer pins and exact request/response/
parent-plan/call references. Command ran through `gpu/a40r_ssh.sh` with
`CUDA_VISIBLE_DEVICES='' TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1` and
`/localhome/local-rohing/v2/venv/bin/python -B -`; AutoTokenizer only,
local_files_only=True, trust_remote_code=False. Zero model loads, GPU calls,
provider calls or retries; no production code/test change.

## Disposition and concrete recovery handoff

**Not relaunched.** No existing tested same-cursor context-overflow recovery
was found in the scoped route lifecycle/recovery sources. Repeating the
unmodified context deterministically fails the guard. The old R120 prepare
path targets recovery_r113/C39 and computes max-reserved-cycle+1; blindly
reusing it cannot restore this C52 turn2 boundary and latest memory. The
existing output/one-shot launch records must not be overwritten.

`RECOVERY_ARGUMENTS.json` supplies exact root/lane/UUID/frozen source/PLAN
equivalents/checkpoint/latest reflection/settled parent/ledger/deadline refs.
Required unresolved choice is a tested explicit context-overflow disposition
preserving C52 episodes, reflection1 and parent110. Silent cropping, increasing
model/rope/context, replaying C52 or parent110, or silently skipping its pending
reflection are NOT performed. A labelled next-C53 continuation would require
that pending C52 disposition, exact carry/counters and immutable new namespace,
then fresh exclusive privileged admission. Original caps remain native16384,
parent640,cycles256; hard wall September18 18:00UTC, TRAIN120seconds earlier.

No actor signals, native edits, provider or shared-service changes, other-slot
access, GPU launch, Git mutation or credential work. Main has the concrete
failure/carry refs to assign the scoped recovery rather than an unexplained
empty snapshot. Ready manifest: `STAGE_READY.json` in this sidecar analysis root.
