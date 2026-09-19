# Empty intent reconciliation — candidate coordination note

September 19, 2026. For Main and Mc; all implementation/tests stay in node2's
`evidence/node2_recovery/partial_intent/`. No node3 changes or live operations.
This file is the shared protocol handoff, not a claim of Mc review or approval.

## Proposed exact mutation semantics, pending Main review

The only allowed artifact is Astra7's uncommitted
`records/00000000000000007808.intent.json.partial`, empty, regular, singly linked,
at the exact pinned old head7807. Committed record7808 and canonical intent7808
must both be absent. Other partials, missing history pairs, an occupied evidence
target, changed bindings or a busy/missing/replaced WRITER lock reject.

1. Acquire the **existing** WRITER.lock exclusively and nonblockingly; never
   create/replace the lock. Hold the same lock across inspection, reconciliation
   and the original auditor. No cooperating original writer can enter.
2. Bind journal/root/lock/records identities, manifest, exact old-head record and
   its canonical intent, partial identity/metadata, and the complete committed
   filename/stat snapshot. Original strict audit must still reject the partial.
3. Exclusively create a same-filesystem evidence directory outside the journal.
   Fsync a PREPARED receipt before changing any source name. It identifies the
   original absolute pathname, inode/device, stat metadata, xattrs, empty-byte
   hash, head and intended mutation. No original history record is edited.
4. Hard-link the partial into that evidence directory **without overwrite**.
   Verify it is the same inode/empty bytes; fsync inode and evidence directory,
   then write/fsync LINKED. Revalidate lock, manifest, prefix and both links.
5. Only then unlink the original **temporary name**. The inode/data remain at
   the evidence pathname. Fsync source directory and archived inode. Preserve
   pre/post metadata, including the expected link-count/ctime changes. This is
   an explicit archived-name reconciliation, not an ignored/skipped partial or
   deletion of its evidence. This unlink is part of the exact semantics Main
   must review; the candidate never silently substitutes a prefix journal.
6. In the CPU fixture, run the unchanged original full auditor on the same journal under the held
   lock. Require the identical old head, record count and expected saved-state
   hash; no synthetic record7808, sleep completion or native restart is created.
   Only after success fsync RECONCILED. Return a non-authorizing receipt.

All committed files remain in place with unchanged identity/bytes. The candidate
does not modify the original auditor, suppress partial checks, synthesize an
intent, change deadlines or alter pending-sleep state. It uses the actual pinned
auditor with an explicitly held-lock adapter because its normal constructor
refuses a partial before returning an object; production driver integration is
still separate work. Tests also require normal constructor/audit success after
reconciliation and normal constructor rejection beforehand.

**Main's production constraint:** do not turn step6's CPU full semantic replay
into a live recovery path. Receiving integration must reuse the existing
source-bound raw-prefix hash plus COMPLETE semantic-tail auditor, retaining the
entire pending state. That seam is **not implemented here**: it must attest the
same raw prefix, exact old head, untouched pending state and archived-name
receipt under the receiving lock, without replaying all historical JSON. No
bounded replay implementation or alternate auditor is introduced by this task.
Full-fixture audit success is not receiving readiness.

## Crash and trust boundaries

- Before PREPARED is durable: no source mutation. Before LINKED is durable: no
  source unlink. A failure can leave both links; neither is auto-cleaned.
- After unlink but before RECONCILED: artifact plus durable PREPARED/LINKED
  remain; status is failed/unknown and needs explicit reconciliation review.
  No automatic rollback or retry, even if the strict auditor now succeeds.
- Full prefix semantic validation happens **after** the archived-name change;
  before it, the externally pinned head/intent and stable namespace are checked.
  A corrupt older record makes the final audit fail, never grants continuation.
- Flock excludes cooperating original writers. It is not protection against a
  hostile same-UID process ignoring the lock; live owner/process/capacity and
  guard/admission checks remain required at integration.
- CPU entry points are confined to fresh local test fixtures under this scope.
  No remote filesystem, real journal scan, model, GPU, staging or launch.

## Reuse boundary for Mc

Reusable approach: externally pinned empty next-intent + existing exclusive
writer lock + durable same-inode archival evidence + no-overwrite link/unlink +
unchanged strict post-audit. The node2 candidate intentionally hard-limits life
and index to Astra7/7808; it is not a general cleanup routine. Other lives or
nonempty partials require separately bound evidence and review. Do not use this
as a way to drop an UPDATE, mask a journal gap, or claim unsaved RNG recovery.
