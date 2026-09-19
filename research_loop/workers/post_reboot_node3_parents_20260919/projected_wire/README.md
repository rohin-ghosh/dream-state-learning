# Offline authenticated projected wire

Owner: Main. Scope: the five existing node3 caption sessions, including the
historically named unparented fork, which remains R233 parented. This is an
offline, source-changing transport repair, not a new judge, experiment, source
deployment, service launch or authorization to restart anything.

## Authority and data flow

1. The existing VM operator receives the unchanged native `{origin,metrics}`
   request. It selects a pinned **owner** binding, not a binding supplied by the
   child, then calls `relay.prepare`.
2. The original `gpu/ovx2_ssh.sh` authenticated operator channel runs `cli collect`
   in a new, pinned source namespace. The collector checks the exact native
   PID/start/boot/command/UID and owner-pinned source anchors before and after
   validation. It reads the original records locally, including all checkpoint
   bytes, verifies each complete canonical record hash, file hash, source journal,
   contiguous ancestry, committed response and ACT/THINK stage. It rereads the
   validated window to reject source changes during collection.
3. It returns exact raw ACT and latest own THINK strings, their original origins
   and source hashes, original record references and COMMITTED/stage identities.
   No normalization, caption extraction, offset rewriting, row selection,
   THINK replacement or historical ACT resubmission occurs. The original
   no-THINK boundary is attested rather than filled from older text.
4. The VM verifies its binding/request, then uses the original `gpu/ovx4_ssh.sh`
   operator channel to run `cli install`. This creates an immutable receipt in
   an existing owner-only scorer-side custody directory. **Only this trusted
   owner channel may install receipts; no child-facing install endpoint exists.**
5. The projected socket envelope contains only schema, session, transport epoch,
   the unchanged request and an opaque receipt digest. `ProjectedHub` opens the
   corresponding **owner** file and checks permissions, UID, link count, bytes,
   request, source/session/epoch binding and expiry. Wire text or a digest without
   that owner file is not authority.
6. The wrapper calls the **existing session object's** `process_verified`, with
   the exact raw ACT and a resolver for the exact own-THINK structure. The
   existing parser, salvage, offsets, policy, token accounting, game, weights,
   ledger and `EpochSessionMixin` execute unchanged. Original and projected
   native requests and base calls share one serialization lock and the original
   single-threaded `shared_scorer.serve` loop. No model is constructed here.

## Bounds and freshness

- Per original record:32MiB; at most289 original records; original32-record
  stage and256-record ancestry searches. Source files and every directory
  component reject symlinks; bounded regular files reject extra hard links.
- Maximum transferred/installed projected document remains **67,108,864 bytes**.
  No existing constant or original exporter is edited. The original full-byte
  export still rejects the oversized regression fixture.
- The new explicit wire epoch transports a different authenticated
  representation: its **locally validated** original bytes can exceed64MiB, but
  those raw records do not cross the wire. This is the owner-requested projection
  contract, not an increased old export limit or unaccounted split transfer.
- A prepared receipt expires after at most the original110-second forwarding
  budget, or the unchanged source deadline if sooner. SSH collect/install retain
  the existing30-second command limits. No expiry, timeout, unknown dispatch or
  scoring failure triggers automatic replay. The ordinary native/bridge request
  timeouts remain unchanged when Main integrates the caller.
- Current source deadline to retain at activation: September24 2026,
  **17:59:20UTC (1790272760)**. The binding requires equality to the prior deadline
  and the existing six-hour lease margin; it cannot extend either.

## Explicit security assumptions

This deliberately reuses the original **trusted operator SSH custody**, not a
new public key or child-asserted provenance. SHA256 references are integrity and
lookup identifiers, not signatures.

Main must verify before activation that the child cannot execute code under the
scorer custody owner, write the custody/binding directories, access operator SSH
credentials, or modify the pinned collector source/configuration. Receipt
directories are0700, files0600, expected-UID checked, opened without symlink
traversal, and persisted before acknowledgement. These modes **do not isolate
two unrestricted processes sharing the same UID**. If a child can act as that
owner on the scorer host, this design is not secure: use actual OS/account or
namespace separation before activation, not another hash field. Likewise a
compromised trusted node/SSH operator can lie, as with the prior raw-byte import.

The collector runs from Main's hash-verified immutable snapshot. Its module
digest also binds all new runtime modules. Production boot verification must
include those files, the unchanged parser/session/epoch modules, Python import
environment and the original judge assets. Remote clocks must not make a future
validation time or expired deadline appear valid; skew currently fails closed.

## Runnable CPU checks and CLI

From the repository root:

```sh
python3 -B -m unittest discover -s research_loop/workers/post_reboot_node3_parents_20260919/projected_wire -p 'test_*.py' -v
python3 -B -m research_loop.workers.post_reboot_node3_parents_20260919.projected_wire.cli source-digest
python3 -B -m research_loop.workers.post_reboot_node3_parents_20260919.projected_wire.cli --help
```

`cli collect --binding OWNER_FILE --binding-sha256 PIN` reads the unchanged
request on stdin and writes a bounded projection. `cli install` takes that
projection on stdin with the same pinned binding plus `--store OWNER_DIRECTORY`.
Binding files and their immediate directory must already be0600/0700 and owned
by the SSH user. Neither command creates a listener or a model. These commands
are implemented but **have not been run against a live node** in this task.

The CPU suite actually runs collect -> install -> the original serialized Unix
socket server -> existing NativeEpoch parser/salvage/dedup path, using an
explicit synthetic CPU game in temporary directories. It compares complete
result documents (excluding timestamps), character offsets, attributed origins,
game/policy snapshots and token accounting against direct original-journal
processing, including Unicode, CRLF, partial ACTs and duplicate THINK captions.

## Binding construction

Do not invent production identities/frontiers. Each strict-owner binding uses
`R233_PROJECTED_TRANSPORT_BINDING_V1` with the exact original registry row,
session, native PID/start/boot/command/UID, source-anchor path/file hashes, stable
mirror root, original judge-epoch digest and deadline/lease values. Add the
explicit new transport-epoch digest, owner-authority digest and `source-digest`
output. The exact JSON file bytes and its digest are installed independently on
node3 and scorer and pinned in the trusted VM caller. Existing native bindings
and aliases are not generated or altered by this package.

For queue, seen, epoch and source-continuation requirements, see
`CONTINUATION.md`. The integration gate is an offline check, not deployment
approval or evidence of fresh natural scoring.
