# Main-owned source-changing continuation — OFFLINE ONLY

No service was started/restarted, no native or scorer was signalled, no live
source/alias was edited, no existing immutable deployment was modified, and no
new independent judge was instantiated. Existing parent330973, CPU
transport425470, operational-error reporter459421 and node-local children are
outside this patch. This document does not claim a fresh process-health audit.

## 1. Pin a distinct transport epoch without changing the judge epoch

Main selects a new immutable continuation namespace and a new transport-epoch
digest bound to its authority, this package's sealed source, original registry,
original scorer source/asset manifest, and the eventual handoff cut. Do not
reuse the old immutable source directory or silently change its manifest.

Keep the original serialized scorer route, exact frozen primary/shadow model
assets, reference panels, scene IDs, relevance/rank/novelty policy, optimizer-free
judge configuration, token budgets, clocks and lease deadline. This package
contains no model loader, alternative judge or score substitution.

Verify the security assumptions in README: child access to an unrestricted
scorer-owner UID, custody store or SSH credentials blocks activation. File modes
alone do not remedy a shared unrestricted UID. Pin collector dependencies and
new module hashes on both nodes through the existing trusted owner channel.

## 2. Close new admission; preserve every pending request

Keep children and parents running. Main's CPU admission route must return and
publish explicit **no judgment / scorer unavailable / no rank or zero score**
during the gap, using an authenticated operational Tool path. The existing live
64MiB reporter is not claimed to support every new outage cause automatically;
Main must connect and test that failure path before cutting over. No synthetic
ACT is sent as a readiness probe.

Do not infer an empty queue from `ps`, quiet logs or elapsed time. Record the
old VM transport's accepted requests, source receipts, dispatch flags, Unix
bridge in-flight requests, original scorer attempts, response hashes and native
ACT receipts. Stop admitting new scorer calls, then let already admitted
serialized work finish and flush. Capture every outstanding item and its exact
identity/bytes before any old process transition. Required gate: explicit
admission-closed evidence and **inflight=0**.

Classify each captured request without rewriting its original evidence:

- COMPLETE: preserve original result, ledger and dispatch receipt; never score
  again, even if publication/delivery acknowledgement is absent.
- UNKNOWN_NO_REPLAY: preserve intent, partial attempt, seen status, phase and
  any exception; do not infer that a missing acknowledgement means no dispatch.
- PREPARED_NEVER_DISPATCHED: preserve the owner receipt and original request,
  age/deadline and custody status. Merely preserving a queue entry is not
  permission to replay it later.
- NO_JUDGMENT_EXPIRED: preserve the source and operational failure receipt; do
  not convert it into a deferred historical ACT submission.

Resolve an original PENDING session using actual saved attempt evidence before
continuation. Do not mark PENDING as COMPLETE to satisfy the gate. There is no
automatic repair of an unknown external result in this patch. A live native may
make its normal next ACT; the continuation never fabricates one.

## 3. Preserve exact session and epoch state

With the old sole writer quiescent, snapshot each complete original session:
`game`, `policy`, `seen`, phase, source mode, session binding, life root, scene IDs
and format policy. Preserve every attempt directory, raw receipt, in-progress
intent and original ledger file. Produce a manifest covering all files, not
only the most recent result. Do not copy just a counter or cached summary.

Keep the original `BINDING.json`, `ACTIVE.json`, all admissions/completions and
ACT epoch receipts byte-for-byte. In particular, do **not** call the old
`attach_epoch(session, ..., new_handoff_reference, ...)`: it incorporates the
new reference into a different epoch binding and can reset the one-hour shadow
window. Use `reattach_existing_epoch` against the complete original file
manifest and original epoch digest instead. It reattaches the existing ledger
without activating or creating a new epoch. The original shadow end is retained.

Preserve the new owner-custody store across any subsequent continuation. Its
`receipt-*` files are authenticated preparation evidence, `claim-*` files are
durable one-attempt dispatch intents, and `complete-*` files bind actual returned
responses. A claim survives exceptions and process restarts. The receiver never
automatically retries a claimed origin, even if the original session's seen set
was not yet persisted. No cleanup operation deletes these artifacts.

## 4. Restore only the original serialized service

Main owns the later process transition. Do not overlap independent judge
writers; the model-source continuation uses the original sessions/outputs and
original epoch ledgers. Preserve original assets/configurations exactly, changing
only the validated transport receiver and its explicit transport epoch.

In the **new source snapshot**, after original NativeEpoch sessions are restored
and their original epoch ledgers reattached, wrap the existing Hub:

```python
store = OwnerStore(existing_private_custody_directory, expected_owner_uid)
hub = ProjectedHub(original_hub, store, independently_loaded_owner_bindings)
serve(hub, original_config['deadline_unix'])
```

Use the original `shared_scorer.serve`, not an additional GPU listener/model.
`ProjectedHub` retains the exact original session instances and registry; its
lock also covers legacy native and base calls. The projected handler resolves
the owner receipt and calls the existing `NativeEpoch.process_verified` once.
It does not call the standalone-generation path, rewrite the native journal,
import altered records, or reinterpret original source IDs.

On the existing CPU proxy's new source snapshot, replace only the export/stage
steps with `relay.prepare`. It returns the projected envelope. Preserve the
original durable transport log, set dispatch intent before the **single**
existing `forward` call, and retain the distinction between confirmed
pre-dispatch failure and an ambiguous post-dispatch failure. No retry loop is
added. Preserve all original deadlines, locks and supervisor ownership.

## 5. Gate and reopen

`continuation.gate(previous, candidate)` requires both admission-closed snapshots
and zero in-flight calls; the exact full session set; original game/policy/seen
and visibility; byte-equal deadline, weights, panels, judge config, complete
ledger-file manifest, custody-file manifest and captured queue; a different
explicit transport epoch and source manifest. It rejects PENDING sessions or
missing/changed queue items. Caller-produced manifests must first be bound to
the actual stopped-writer files; this pure gate is not a filesystem attestation
or permission to launch. Its schema fields are demonstrated in the CPU tests.

After Main binds the receiving snapshot/manifest, revalidates actual loaded
weights and runs receiving-host CPU checks, reopen only future natural
admission. Do not lower the original source frontier or consume old prepared
receipts automatically. Preserve both transport epochs and failed attempts.
Verification must distinguish authentic scorer receipt, caption actually scored,
Tool INBOX publication, masked REQUEST delivery and subsequent ACT uptake. No
operational error or format-only reply is counted as a caption judgment.

If any original in-flight outcome, PENDING state or trusted-owner custody
assumption cannot be established, keep the explicit no-judgment route rather
than replay, reset state, widen a bound or silently create a new judge epoch.
