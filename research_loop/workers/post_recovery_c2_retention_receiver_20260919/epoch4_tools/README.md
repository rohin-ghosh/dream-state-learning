# C2 epoch4 offline proposal and bounded integration

Write scope: new files/new epoch in this worker only. No current source, old
epoch, root history, shared coordinator, peer source, GPU, native or parent work.

This is an offline candidate, NOT approval to change a trust invariant. The
optional prefix path substitutes authenticated earlier byte hashing plus
filesystem identity rechecks for repeated prefix hashing. That adds reliance
on same-boot local filesystem metadata, no rollback and no concurrent mutation
of previously authenticated prefix objects. It is NOT silently called a
non-material optimization; trust review and original admission are gates.

Kuhn's v4 ABI preserves the exact same-namespace default and adds the explicit
`SAME_FILESYSTEM_OBJECTS_ACROSS_ADMITTED_NAMESPACE` mode. Main approved bounded
derivation of the final B guard/admission clause only. C2 uses the exact v4 helper
and reader, NOT a separate namespace shim. Main's host4026531832/native4026536303
observations do not prove startup; same-boot own-view checks of EVERY object,
original r188 admission, and real total-path timing remain necessary. No namespace
allowlist, entry, environment spoof or new service route is implemented.

The native seam carries authority from original validated guard -> pinned
allocation -> pinned passed CPU receipt -> `c2_prefix_authority`. The handoff
token contains `receiver.prefix_binding` with the exact authority reference and
derived bounded selection guard. Both CPU preflight and native consume the
same reference. Main's original source CPU receipt is preserved; its receiving
copy adds only the deterministically derived clause, pinned by the original
allocation/guard before CPU scan. Native compares the same derivation. Mere
proof-file existence or self-signed candidate is not approval. `copy_raw` must
remain the original journal root; identical-byte clones are rejected.

`prefix_preflight.py` requires externally pinned source/life/epoch/consumer
context and measured full reserved-cost evidence before budget activation.
One monotonic budget is at most30s minus commit margin; subprocess callers must
use its remaining timeout and no proof producer/full-prefix fallback is allowed
after stopping. Source CPU checks cannot synthesize a real timing or admission
receipt. Main owns real node benchmarking and final review.

The C2 `MainRoute` is still an injected capability contract, NOT an implemented
owner fence/rebind transport. In particular it does not authenticate the actual
C2 service/publisher locks, drain provider/publication queues, disable only C2's
registry admission or perform actual post-LOADED source-bound parent rebinding.
No readiness booleans are synthesized. Pair sidecars are not C2 evidence.

`TO_KUHN_EPOCH4.md` and `TO_BANACH_EPOCH4.md` are coordination requests via Main,
not acknowledgements. Peer handoff files are evidence of the ABI being consumed,
not cross-namespace approval or permission to dispatch.
