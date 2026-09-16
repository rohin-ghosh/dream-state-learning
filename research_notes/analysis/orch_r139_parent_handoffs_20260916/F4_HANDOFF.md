# F4 R139 — staged saved-cycle consumer and Astra broker adapters

**STAGED, NOT LAUNCHED.** The no-reset clarification is bound to
`bb2f2eb9716c97f13697dadb804fdedc6626f470`, COORDINATION02:35Z.
No signal, provider request, child restart, training, admission scan, lease
change, Git action or shared-ledger write was performed by this sidecar.

## Concrete seam

The existing source-pinned R119 `release_at_boundary` watches an atomic CARRY
publication and uses a PID-identity-bound stop only to inspect a **completed
two-episode cycle**, rejecting any unfinished native call. A rejected boundary
resumes the original actor; a valid boundary preserves the ledger, carry and
TRAIN_COMPLETE references before terminating that exact actor. R139 reuses this
implementation with an immediate, publication-bounded600-second window. It does
not stop or serialize a partial episode and does not replay completed inputs.

The successor uses the existing frozen-gen1 LoRA loader and the same TRAIN
roster, carry, cumulative native/parent caps, physical GPU and source-checked
checkpoint. Only its **in-memory** `parent_model` changes to truthful Astra;
the original CONFIG and `F4_FABLE` lineage ID remain unchanged. The original
nonblocking mailbox remains in `independent_r119_v1`, but starts at actual
boundary `after_parent + 1`. Historical missing, pending, refused or completed
requests are not readmitted. New requests must belong to a new cycle and the
existing A4 experience-only cadence; expired requests are skipped.

The broker reuses the pinned existing A4 HTTP transport, prompt construction,
full TRAIN provenance validation, bounded shared HTTP slots, low effort,
1024 output cap and570-second bounded timeout. It does not rephrase prompts or
retry failures. Its claim ledger is **new** `parent_astra_r139`; all298 old
`parent_claude` claims and the old cap298 remain intact. Every new result retains
truthful actual-model metadata and gains a separate archived SEGMENT receipt.

## State precision

Current F4 is `GEN1_FROZEN_LORA_ELICITATION_ONLY`, **not an active AdamW learner**.
The archive `optimizer_rng.pt` remains byte-identical and is not loaded/reset.
The same frozen adapter is reloaded and identity-verified; no optimizer is
created. Decoding remains greedy/no-sampling. **This is not a claim that live
CPU/CUDA RNG bytes are captured/restored:** the original resident exposes no
live RNG checkpoint. That limitation is explicit in PLAN and RESUMED receipts.
Do not apply this adapter to a training lane or claim it restores an active
optimizer/RNG stream. Such a lane would need a different saved-state seam.

## Snapshot and caps

Read-only stage at **2026-09-16 02:46:43 UTC**: N4233, P0320, cycle106.
These are observations, **not the release cursor**. The actual cursor is taken
after a newly completed cycle. The existing lease budget remains
NATIVE1615314/PARENT404430. The Astra segment allocation is exactly404430 minus
the actual release high-water (at this snapshot it would be404110), never an
extension or reset. TRAIN end remains22:02 UTC and hard wall22:04 UTC on
September16. Future native reservations still use the same cumulative ledger.

## Main-owned prerequisites — do not skip

1. Publish the exact staged plan and this scope. A false publication template
   is provided; no publication has been fabricated by the sidecar.
2. Supply a **real live successor-aware timer-custody receipt**, with the bound
   controller identity/source hash. The current06:00 UTC FINAL timer and lease
   wall are pinned to the old PID. Simply killing that PID without transferring
   custody would lose the morning capture and leave the successor untracked.
   Preserve the same8-call FINAL quota, zero added calls, no sealed-to-parent
   visibility, and R139's truthful parent binding after any morning resumption.
   Timer-controller implementation/replacement is not performed by this sidecar.
3. Run the authorized release command. Only an actual BOUNDARY/RELEASED pair
   permits resume. Source/input hashes, old actor exit and all298 old claims
   are checked. No old request is resubmitted.
4. Obtain fresh strict root-scanned admission for the same GPU after release;
   bind its exact receipt and observation time in the resume publication.
5. Start the successor under the unchanged hard wall. After actual RESUMED,
   publish its hash in the VM broker publication. Only then start the broker.

The implementation intentionally fails closed without timer custody, Main
publication, release or admission. CPU testing is not a GPU launch approval.
Live release/resume/model execution remains untested and was not attempted.

## Exact staged files and commands

Node staging: `/tmp/orch_r139_F4_handoff_v1`.
VM staging: `/tmp/orch_r139_F4_vm_v1`.
Both contain the new script/tests; both have the identical F4_PLAN.json.

Script SHA256: `adc2598e89e3917840129c319a58de122ebda832af7e1acae3dce77562c3c778`.
Plan SHA256: `21cdcf5ce41403176b1a46d12c05fdf5c877f0bd89b82890780444509291a546`.

Safe read-only stage command (already run; a new timestamp changes plan bytes):

```bash
bash gpu/ovx3_ssh.sh 'PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/localhome/local-rohing/orch_r118_grid_shared_source_20260915_attempt2 python3 -B /tmp/orch_r139_F4_handoff_v1/gpu/orch_r139_grid_astra_handoff.py stage --expected-self-sha256 adc2598e89e3917840129c319a58de122ebda832af7e1acae3dce77562c3c778'
```

**Following commands are NOT executed.** Main must first create the distinct
phase-publication files at the paths named here, with the required live receipts.

Release on node5, CPU only:

```bash
bash gpu/ovx3_ssh.sh 'CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 python3 -B /tmp/orch_r139_F4_handoff_v1/gpu/orch_r139_grid_astra_handoff.py release --expected-self-sha256 adc2598e89e3917840129c319a58de122ebda832af7e1acae3dce77562c3c778 --plan /tmp/orch_r139_F4_handoff_v1/F4_PLAN.json --plan-sha256 21cdcf5ce41403176b1a46d12c05fdf5c877f0bd89b82890780444509291a546 --publication /tmp/orch_r139_F4_handoff_v1/F4_RELEASE_PUBLICATION.json'
```

Resume on node5 in a Main-managed resident session after release/admission:

```bash
bash gpu/ovx3_ssh.sh 'GPU_UUID=$(python3 -c '\''import json; print(json.load(open("/localhome/local-rohing/orch_r115_grid_pair_20260915/F4/CONFIG.json"))["uuid"])'\''); REMAINING=$((1789596240-$(date +%s)-4)); test "$REMAINING" -gt 0 && CUDA_VISIBLE_DEVICES="$GPU_UUID" PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 timeout --signal=TERM --kill-after=3s "${REMAINING}s" /localhome/local-rohing/v2/venv/bin/python -B /tmp/orch_r139_F4_handoff_v1/gpu/orch_r139_grid_astra_handoff.py resume --expected-self-sha256 adc2598e89e3917840129c319a58de122ebda832af7e1acae3dce77562c3c778 --plan /tmp/orch_r139_F4_handoff_v1/F4_PLAN.json --plan-sha256 21cdcf5ce41403176b1a46d12c05fdf5c877f0bd89b82890780444509291a546 --publication /tmp/orch_r139_F4_handoff_v1/F4_RESUME_PUBLICATION.json'
```

Broker on VM only after actual successor readiness and separate Main publication:

```bash
CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 python3 -B /tmp/orch_r139_F4_vm_v1/gpu/orch_r139_grid_astra_handoff.py broker --expected-self-sha256 adc2598e89e3917840129c319a58de122ebda832af7e1acae3dce77562c3c778 --plan /tmp/orch_r139_F4_vm_v1/F4_PLAN.json --plan-sha256 21cdcf5ce41403176b1a46d12c05fdf5c877f0bd89b82890780444509291a546 --publication /tmp/orch_r139_F4_vm_v1/F4_BROKER_PUBLICATION.json
```

Tests:15 local passed,14 native passed and1 skipped (the VM-only A4 runtime
is not installed on the node). The actual pinned VM broker adapter also compiled
without provider/queue calls. Existing release code was reused, not signalled
against any real process during this work.
