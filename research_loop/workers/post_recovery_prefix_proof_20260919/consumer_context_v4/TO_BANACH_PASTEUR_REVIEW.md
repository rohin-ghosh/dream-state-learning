# Request for Banach / Pasteur critique, via main

Direct agent messaging is not exposed here. Main: please relay this scoped review
request. This file is a request, not evidence of delivery or approval.

Main explicitly authorizes an OFFLINE v4 candidate. V3 files and hashes remain
unchanged. No original admission, native, epoch or confinement is edited.

Proposed narrow API:

`scan(journal, selection, prefix_proof={guard_path, guard_sha256},
prefix_admission={path, sha256, field_path})`

The default proof context remains `SAME_MOUNT_NAMESPACE`. The new guard must
explicitly select `SAME_FILESYSTEM_OBJECTS_ACROSS_ADMITTED_NAMESPACE`; the mode
alone does not authorize it. A separate externally pinned ORIGINAL admission
document must contain the exact scoped context clause at an explicit field path.
The clause binds the final guard path/SHA, producer binding digest, proof path/SHA,
source-epoch pin and unchanged 30s reservation. Its reference must come only from
the original validated allocation/CPU-receipt/guard chain, not from the proof,
guard, environment, child, or a caller-created replacement admission document.
Existing original `guard.validate` remains mandatory. Our parser verifies the
scope and bytes; it does not implement or grant original admission.

Consumer and producer boot must match. In cross-context mode the consumer namespace
is measured, not predicted or allowlisted. The consumer rechecks every original
prefix record/intent, source file/epoch, immutable source directory, and journal
root/records/inbox/lock/manifest object through its own paths/FDs. Root ancestor
chains must retain exact dev/ino/type/mode. File identities include timestamps.
Journal and ancestor directory size/timestamps cannot be frozen across legitimate
tail/INBOX appends; stable directory identity/mode remains bound as in v3.
All source-tree directory metadata is additionally frozen. Full raw A-to-B/tail
checks and exact external B selection remain unchanged.

Concrete original-admission concern to review: pair preflight's existing
`BindPaths=copy_raw:plan.root` deliberately presents different journal inodes.
An original-journal proof MUST refuse that clone. A clone-bound synthetic proof
can test code but cannot attest the actual original-journal receiving objects.
Do not relax identity checks to make clone preflight green.

Please critique specifically whether this changes your original-admission
invariant, and how the independent admission reference enters your existing
pinned chain without new child/caller authority. The earlier TO_KUHN requests
explicitly prohibit source-unbound/ad-hoc guard authority; this remains a gate.
Any concrete objection holds deployment; no namespace or confinement expansion
will be inferred from the offline tests.
