# Q0 collection-reserve relay: historical custody and prospective boundary

Builder, September 14, 2026, 02:58 UTC (September 13 Pacific).

## Disposition

The reported 180 versus 1,800-second difference is real. Do not silently change
the historical executor, launcher, manifests, resource receipts or roots. The
three roots are already terminal, not waiting for a pre-training stop. Preserve
them as excluded diagnostic DEV evidence under their actual 180-second
implementation; do not describe them as satisfying a 1,800-second contract.
No new protocol-validity promotion is made in this continuation.

The available frozen documents do not establish the alleged violation of the
selected v2 protocol. They establish a difference between an earlier proposed
resource contract and the selected implementation. This distinction was already
explicitly adjudicated by the archived static independent audit. It must remain
visible, not be erased because the leases had ample time.

Q0 remains closed under the current durable campaign decision. No launch, kill,
source patch, new model forward, re-preparation, or post-outcome repeat is made
to repair historical bookkeeping. Corrected repeated roots are NOT launched or
claimed ready. The selected developmental continuation remains the v6 typed
boundary and reduced BASE/D1 screen, not another Q0 dose campaign.

## Exact conflicting bindings

1. `research_notes/astra_memos/receipts_20260912/astra_q0_revision_design_20260913.md:81`
   proposes 1,800 seconds for post-terminal collection/replay and 12,600 seconds
   before the six-hour cutoff. Its SHA256 is
   `287fbd868a662f9a19045a8e207a2073c75f2511ef6630b8ff5a90dc3bd7fac8`.
2. `research_notes/astra_memos/ASTRA_Q0_FULLDOSE_PROTOCOL_2026-09-13.md:17`
   incorporates that memo's endpoint gates, material construction and CPU
   acceptance checks. Its budget at line66 specifies 10,800 seconds plus
   separately bounded collection, without selecting the collection duration.
   SHA256 `58463922037e8c29b1ce8d5b2cffa3aff3bc1f9b7277ae3ee5600cd2059f353a`.
3. The implementation handoff at
   `research_notes/astra_memos/receipts_20260912/astra_q0_fulldose_implementation_handoff_20260913.md:51`
   explicitly selects 180 seconds and distinguishes a reservation margin from
   a collection daemon/timer. SHA256
   `c5957457b39931aa3d66d03db2a2676e462ef6b9e94f53d71e9eab78d47b8bf3`.
4. The exact executor remains SHA256
   `f63c77f9c371433442a204d6bd7bb10e3769a3bb709ae1d728648d765ee8ceca`.
   `gpu/astra_pairwise_q0_fulldose.py:58` declares180; line1935 checks admission;
   line1992 receipts it; line2071 verifies it. The archived launcher at
   `research_notes/astra_memos/receipts_20260912/astra_launch_q0_fulldose_20260913.py:37`
   also checks10,800+180. None of those bytes was changed.
5. `research_notes/analysis/2026-09-13_q0_fulldose_v2_static_independent_audit.md:144`
   already records the difference and its no-frozen-violation interpretation.
   Its line134 separately flags absent internal protocol/design/sidecar hash
   binding. Audit SHA256
   `8cfb2310c20edc14ca450cfc5628456bf8070aa8a859b35b45da2ab766cdaf2e`;
   commit4233c7aa has commit time September13,05:32:46UTC. This is a substantive
   resolution in the recovered record, not proof of when this relay was sent.

## Fresh read-only node2 observations

At September14,02:54:13UTC, nvidia-smi reported all eight devices at0MiB and no
compute applications. The same-user process listing showed no Q0 controller or
worker. At02:55:02UTC a separate /proc scan found no same-user
CUDA_VISIBLE_DEVICES reservations. These are snapshots, not reservations or
future availability guarantees. The initial combined listing exited2 because it
also requested absent optional marker paths; the subsequent direct JSON read
exited0 and established the following actual receipts.

All roots are under
`/localhome/local-rohing/astra_diagnostics/q0_fulldose_R{0,1,2}_20260913_attempt1`.
All RESOURCE.json files record collection_reserve_seconds180 and GPU release
true. All have lease_cutoff_unix1789958580 and lease_end_unix1789980180, exactly
21,600 seconds apart. Start-time headroom before that cutoff is:

| Root | Headroom seconds | Fresh FINALIZED.json SHA256 |
| --- | ---: | --- |
| R0 | 682932.1623175144 | `5cecfd81ef81b5d72179c11ff681356ae95b19dd24931fb22b96c83fdf9bcdf8` |
| R1 | 682908.0252566338 | `ec1c4212ff93b5bfb4b20963a83dfc61c9ffa731944968b6f77568762d5e3eb0` |
| R2 | 682893.6063354015 | `c2882a24e36ff4826e85b9997acec9b6bdf68753eef7e55cb75a178bf901ac78` |

Fresh manifest and finalized hashes match the independent terminal reduction's
table. This is a selected-file check, NOT a fresh whole-root rehash or scientific
reduction. The prior external custody record dates termination/absence to
September13,05:30:34UTC(R1),05:37:04UTC(R0),05:39:23UTC(R2).
R0/R2 retain their recorded endpoint failures; R1 retains its nonreportable
runtime abort. Do not convert R1's missing endpoint to zero or three-root
failure-rate evidence. Ample headroom does not retroactively change bindings or
prove that collection was independently timed. No H1/H2 evidence is promoted.

## Fresh independent review and successor requirements

Read-only agent Singer the2nd independently inspected the frozen documents and
streamed all three archived prepared manifests. It confirmed the executor pins
and agreed with preserving closure rather than changing historical replay code.
Its live-resource facts were supplied by Main, not independently remeasured.
No disagreement is concealed: the incoming relay treats the earlier proposal
as mandatory; the later audit and this review read the selected incorporation
more narrowly. The conservative boundary is diagnostic custody only, with no
claim of1,800-second compliance.

If Q0 is independently selected again, bind a NEW prospective protocol and
versioned source/launcher/manifest to all of the following before any launch:

- A10,800-second root cap, distinct1,800-second collection/replay allowance,
  and at least12,600seconds before lease_end minus21,600seconds.
- One explicit equality convention across launcher and executor, tested at
  12,599/12,600/12,601seconds; test the obsolete10,980-second window rejects.
- Actual collection start/end/deadline supervision, not only a reservation
  constant; overrun leaves verification unresolved rather than accepted.
- Exact protocol/design/source/launcher pins in prospective custody, pinned
  single-thread replay, fresh immutable root and attempt IDs, and unchanged
  three-root allocations, controls, dose and denominators unless separately
  declared. Preserve all old roots and failure-inclusive reports.
- New native readiness/provenance tests and fresh device/lease checks. A
  bookkeeping correction is not evidence of improved efficacy; explicitly label
  any repeat as selected after inspecting the old outcomes.

These are prospective requirements, not implemented checks or launch clearance.
No tests were rerun: this increment changes documentation only and preserves
the exact scientific executor/test bytes. The full research mission is incomplete.
