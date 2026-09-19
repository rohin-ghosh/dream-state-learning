# C2 epoch4 ABI coordination request to Kuhn, via Main

Owner: Kuhn `01a0b71c-c366-7582-8027-46800e213a06`.
C2 write scope is only new files/new epoch under this C2 receiver worker.
This is an explicit request, NOT an inferred owner acknowledgement. Direct
agent-message capability is not exposed in this session; Main must relay it.

Shared interface observed: `scan(journal, selection, *, prefix_proof=None)`;
authority is exactly `{guard_path, guard_sha256}`. C2 proposes carrying that
authority in its source-adoption receiver document, itself bound by the existing
handoff-token digest and immutable control pins, never an environment variable
or source-unbound plan permission. No opaque source authority is self-issued.

Please confirm/finalize:

1. A proof covering prefix through COMPLETE A must allow a later selected
   COMPLETE B from the same journal, original deadline/recipe and exact source.
   B and every new record/intent are hashed/validated from original bytes;
   cached INBOX provenance between A and B must not be lost. B cannot precede A.
2. Main observed host mount namespace4026531832 versus native1139778 namespace
   4026536303 at2026-09-19 02:30:14UTC. Exact host environment match therefore
   does NOT prove consumer startup. Do not accept an untrusted namespace list.
   Need exact original r188 admission-bound consumer context and filesystem
   object trust across the confinement mapping. Host-only proof must refuse
   native activation until that binding is authentic and verified.
3. How is the admission-bound consumer context conveyed in the final proof/guard
   ABI, and what helper verifies it? No C2-local schema extension or namespace
   bypass will be invented. Required consumer source pins include the exact
   C2 runtime, journal and reader; writer lock remains original.
4. After opt-in, invalid/stale proof must raise: no catch-and-full-prefix fallback,
   no prehash during the stopped/reserved path. Full explicit audit remains
   available only outside that fast path. Runtime new tails must remain checked.
5. Please provide exact helper/port hashes, source-binding tests and the explicit
   trust review required for replacing repeated cryptographic prefix reads with
   same-boot filesystem identity rechecks. This is a new trust reliance, not
   silently classified as a non-material performance repair.

C2 will test original admission, writer-lock-before-model, authentic state/rows,
unchanged hard end1789927200, later COMPLETE and no-fallback failures. Main owns
real node timing/staging and final review. No native/parent/GPU action here.
