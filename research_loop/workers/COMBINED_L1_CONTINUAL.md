# COMBINED_L1_CONTINUAL — Laplace

## 2026-09-15T03:38Z — Rohin96 migration and allocation estimate

Scope supersession: persistent evolving FULL/control children, append qualified
batches with rehearsal; no reset on arrival and no fixed presentation stopping
knob. Prior combined2394 terminal16-presentation design is preserved, NOT launched.
Main owns BOARD and is publishing Git; no shared COORDINATION append during lock.

Actual math764 observation03:37:03Z: FULL PID338105 update903/6208,
OFF PID338106 update915/6208; guardian338092. Last measured128-update rates
at03:34:23Z were0.960/0.946seconds/update. Approximately85minutes remain
(uncertain: sequence lengths, competing GPU traffic, final verification/save).
Neither adapter is saved yet. DO NOT terminate these processes: their immutable
legacy loop has no checkpoint hook and only saves the adapter at completion.
Exact old optimizer/RNG/cursor migration is not available. A successor may recover
the final adapter, but must explicitly record a fresh optimizer at this one-time
legacy migration boundary; it cannot claim exact legacy-state recovery.

Planned persistent topology after safe migration: FULL ranks on physical0+2,
masked-control ranks on1+3, one visible GPU per native rank, synchronous LoRA
gradient sum, two examples/rank from the same four-row global replay batch.
FULL/control have exactly matched global batches/reference-token normalization.
Four training GPUs, not two training plus two idle/readout reservations.
Projected combined2394 traversal:1203global updates; ~10–20minutes per traversal
is only an unmeasured planning range, NOT observed four-GPU throughput. Calibrate
on the first128actual updates. Training repeats until the bounded inherited
deadline, not a16-presentation terminal fit. No claim of completion ETA for an
open-ended continual child. First valid FULL checkpoint is handed to Anscombe
without waiting for held scores.

Frozen initial corpus2394: manifest
b1dde49fe8b424ec6bc7ee4eafbeef44a0f4f8e6c08f7d5c749fde82b81cb852;
packet deb5d65cab3b8ae56d63b4b302030f096fa519689b0dfb8bc9281cb9180d683b.
This includes exact SEQ2661452, entire MATH764, MATH_RICH19,
MATH_RECORD92, INTENSITY56, TWO_PASS8nonduplicate of9, FULL_RICH3.
No admission/new targets/outcomes inspection. Native tokenizer checks for the
combined packet remain pending. Prepared code is not native training progress.

Hubble's current selective LAPLACE_RELEASE_REQUEST interface will be used ONLY
when launch-ready, never the obsolete bulk release request. Hubble keeps filling
2/3 meanwhile; fresh privileged UUID-to-kernel-minor scans are required later.
