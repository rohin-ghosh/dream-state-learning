# Receiving commands — NOT executed, pending Main review and storage

These commands preserve original source/PLAN/GUARD/lease and all failed artifacts.
They **must not be executed while the owner-space budget is unmet**. Do not rerun
into an occupied staging directory; preserve any incomplete preparation and review.

## 1. Main's exact CPU-staging review, on the VM

Set `S=research_loop/workers/replication_sprint_20260919/evidence/node2_recovery/c0_startup`.
Review `SOURCE_DELTA.json`, including preparer/cut hashes. In Main's own receipt
directory (not this worker's originals), create `REVIEWED_STAGING.json` with:

```json
{
  "reviewed_for_staging": true,
  "GPU_launch_authorized": false,
  "additions": "COPY the runtime_additions OBJECT from SOURCE_DELTA.json",
  "preparer_sha256": "COPY preparer_sha256 from SOURCE_DELTA.json",
  "cut_sha256": "COPY cut_sha256 from SOURCE_DELTA.json"
}
```

The strings above are instructions, not a valid runnable approval. Do not invent
hashes. The preparer checks them against actual transferred bytes.

After storage is addressed and staging is reviewed, transfer the sub-MB code/CPU
payload via the original route into a **new** directory (no journal/weights transfer):

```bash
tar -C "$S" -cf - . | bash gpu/ovx_ssh.sh \
  'mkdir -m 700 /localhome/local-rohing/c0_pending_cpu_payload_20260919_v1 && tar -xf - -C /localhome/local-rohing/c0_pending_cpu_payload_20260919_v1'
cat "$MAIN_REVIEWED_STAGING_RECEIPT" | bash gpu/ovx_ssh.sh \
  'set -C; cat > /localhome/local-rohing/c0_pending_cpu_payload_20260919_v1/REVIEWED_STAGING.json'
```

## 2. CPU preparation on node2

```bash
bash gpu/ovx_ssh.sh 'cd /localhome/local-rohing/c0_pending_cpu_payload_20260919_v1 && \
  CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 /localhome/local-rohing/v2/venv/bin/python -B prepare_receiving.py \
  --reviewed-source-delta REVIEWED_STAGING.json'
```

This creates only:

- `/localhome/local-rohing/orch_r216_C0_20260918_attempt2/source_c0_pending_v1`
- `/localhome/local-rohing/orch_r216_C0_20260918_attempt2/control_c0_pending_v1`

It validates original closure/PLAN/GUARD, checks space, copies unchanged source,
relocates identical startup text, acquires exclusive WRITER only to audit the
raw prefix plus COMPLETE6631 semantic tail through6710, hashes durable checkpoint
payloads, and writes CANDIDATE/STARTUP/SOURCE_DELTA/PRESERVED_STATE_AUDIT. No record
is appended and no failed artifact is moved. Full candidate state stays on node2.
The original driver and wrapper are copied verbatim. Native admission is not run.

## 3. Actual receiving CPU tests

```bash
bash gpu/ovx_ssh.sh 'cd /localhome/local-rohing/c0_pending_cpu_payload_20260919_v1 && \
  CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 \
  C0_TEST_SOURCE_ROOT=/localhome/local-rohing/orch_r216_C0_20260918_attempt2/source_c0_pending_v1 \
  /localhome/local-rohing/v2/venv/bin/python -B run_cpu_tests.py'
```

Save the **actual returned** `TEST_RECEIPT_<stamp>.json` path. Do not use the VM
receipt as receiving proof. The runner checks the staged source closure and the
unchanged original closure/PLAN/GUARD, and emits a synthetic CPU trace. It does not
touch the real journal. Host admission remains separate.

## 4. Truthful publication and final CPU binding

Main must supply an existing publication receipt with `builder_entry_pushed: true`,
the actual40-hex `commit_sha`, and `runtime_additions` equal to the reviewed six
source hashes. This worker does not commit, push or fabricate that claim. Transfer
the receipt to a new filename under the payload; never replace originals.

Using the exact receiving receipt and publication receipt paths:

```bash
bash gpu/ovx_ssh.sh 'cd /localhome/local-rohing/c0_pending_cpu_payload_20260919_v1 && \
  CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 /localhome/local-rohing/v2/venv/bin/python -B finalize_receiving.py \
  --cpu-receipt /ABSOLUTE/RETURNED/TEST_RECEIPT_stamp.json \
  --publication-receipt /ABSOLUTE/MAIN/PUBLICATION.json'
```

Replace the displayed placeholders with real returned paths. This binds a fresh
ALLOCATION/GUARD/RECEIVING_CPU in the **new** control tree and executes the original
`guard.validate`: entire source closure, actual host, unchanged lease receipt and
reservation, exact PLAN and allocation. It has no dispatch/model option.

## 5. Live action is Main's next review, NOT this handoff

After a fresh capacity check, truthful receiving/publication proofs, review of
the preserved-state audit, and explicit live go-ahead, the existing confined route
would be:

```bash
bash gpu/ovx_ssh.sh 'cd /localhome/local-rohing/orch_r216_C0_20260918_attempt2/source_c0_pending_v1 && \
  CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 \
  PYTHONPATH=/localhome/local-rohing/orch_r216_C0_20260918_attempt2/source_c0_pending_v1 \
  /localhome/local-rohing/v2/venv/bin/python -B -m gpu.c0_pending_entry dispatch \
  --config /localhome/local-rohing/orch_r216_C0_20260918_attempt2/control_c0_pending_v1/GUARD.json'
```

The original source-bound probe, privileged scan, finite same-deadline systemd
confinement, LAUNCH handshake, device check, exclusive WRITER and exact head checks
still apply. No authorization/privilege bypass or timer extension is added.
Do not pre-fill PRE_SERVICE_ADMISSION/ADMISSION/LAUNCH or fake a WRITER receipt.
On any failure preserve the newly created artifacts as well, and do not auto-retry.
