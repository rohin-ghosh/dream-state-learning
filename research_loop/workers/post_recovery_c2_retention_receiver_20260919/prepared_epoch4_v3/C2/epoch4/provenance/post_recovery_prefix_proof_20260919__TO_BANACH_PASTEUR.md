# Banach / Pasteur / main: offline receiving interface, namespace gate held

The new worker is `post_recovery_prefix_proof_20260919`. Nothing is staged or live.
This is a filesystem handoff for main to route; no out-of-band delivery is claimed.

## Executable interface

Use `prefix_port.port(original_reader_bytes)` for the exact SHA-bound candidate
and the accompanying `immutable_prefix_proof.py` in a separately admitted new
source epoch. Existing reader/caller/guard/parent sources were not edited.
Original defaults and explicit full audits are unchanged.

Produce proof at exact COMPLETE A outside reservation. Final approved guard
contains `binding` (A, same exact source/root/journal/class/epoch/boot/namespace),
`proof_path`, `proof_sha256`, and `resume` with **exact** original selection B,
`max_advance_records` and `max_advance_bytes`. The original receiver guard must
externally select this final guard's exact path and raw SHA256.

Call `scan(journal, selection_B, prefix_proof=external_guard_reference)` only on
the opt-in path. A+1..B and B+1..head are fully raw/intent verified. New INBOX
records in A+1..B are decoded and advanced, not suppressed with cached A state.
No rollback, sidecar/policy/tail-bound drift, auto-selection, or fallback occurs.
Source epoch path/SHA is separately bound; original admission validates its wall,
anchors, model and other scientific invariants. No proof/candidate grants admission.

## Namespace blocker — do not substitute the observer context

Main supplied September 19, 2026 02:30:14 UTC C2/node5 identities:

- Host: `mnt:[4026531832]`.
- Original native PID `1139778`: `mnt:[4026536303]`.

These **fail the current same-namespace contract**. Proof creation on the host
and a host-side CPU probe cannot demonstrate actual systemd-confined startup.
The code pins producer boot plus mount-namespace dev/inode and requires the
actual consumer to match. There is no allowlist or cross-namespace override.

Main additionally reports matching host/native-root-view objects (not independently
read here): source `dev=66307, ino=5506190, mode=0555`; journal stream
`dev=66307, ino=46924408, mode=0775`; manifest `dev=66307, ino=46935343, mode=0664`.
The cited existing request is
`/localhome/local-rohing/orch_retention_20260919/C2/historical_complete_cost_1789784082391591641/REQUEST.json`,
SHA256 `374a9c7f89eacfbf56ec901ea4edecdaf62745029c5abb5e660cead20a1ccfd8`.
These bounded samples are useful evidence for a future cross-context review,
not an override or complete verification of every retained prefix/intent object.
The historical request is not assumed to have the new producer-request schema.

Held until main establishes a supported producer and actual consumer in the same
explicitly admitted namespace, or a separately reviewed exact producer/consumer
authority design is implemented. Running producer inside the old namespace does
not suffice if the new unit creates a different namespace. No namespace entry,
host inspection, service change, or native action was attempted by this worker.

The original overall **30s reservation maximum is unchanged**. Neither the new
advance caps nor the outside-reservation producer duration enlarges it. Actual
node timing, filesystem immutability assumptions and source/admission review are
remaining gates, not claims established by the synthetic suite.

See `README.md` for runnable producer/bind-resume/probe commands, trust hazards,
schema details and fail-closed requirements; final code hashes and synthetic
results are in `TEST_RECEIPT_v3.json`. Earlier receipts predate the final changes.
