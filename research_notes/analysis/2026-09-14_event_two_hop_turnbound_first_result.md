# SEQ-249: executable reads, but no connected goal arrival

September14,2026. Revised `turnbound` readout is COMPLETE at14:53:25UTC,
node2GPU0 guardian391196, source5dd5625fbefb6ea4915c5eeb2a471f58bc898ffc.
Same SEQ245 parent and SEQ248 actual child EVENTs; no recollection or fit.

| Condition | Goal /4 | Actor calls | Service reads | Actual legal routes |
|---|---:|---:|---:|---:|
| ON_PARAMETRIC | 0 | 21 | 16 | 1 |
| ON_OWN_TEXT | 0 | 14 | 10 | 0 |
| ON_UNAVAILABLE | 0 | 24 | 16 | 4 |
| OFF_OWN_TEXT | 0 | 11 | 3 | 5 |

There are86 native calls (70actor,16parametric-reader); text/unavailable returns
are not native forwards. The clarified turn rule enables real service use.
All four own-text episodes ultimately emit `ROUTE <goal-node>` instead of a
port. They read1,4,3,2 exact stored records, respectively; none commits an action.
Parametric outcomes:3invalid_command,1duplicate_address. Those graph facts have
not been trained as memories, and all16 parametric answers are retained.
Unavailable:4duplicate_address. OFF:2invalid_route,1dead_end,1duplicate_address;
one episode makes two legal moves but ends at the wrong goal. No physical arrival
is hidden by a secondary scoring rule. All errors remain failed observations.

The result separates a working memory-service call from a usable next-action
decision. It does not establish that the model cannot infer a path: wrong
argument typing remains an alternative explanation. The single-hop learned
interface does not reliably transfer to this new continuation protocol. There
is no H1/H2, independent-world or parenting-efficiency result here.

Native wall130.987seconds, approximately0.0364 dedicatedA40h; both adapter
state and frozen base unchanged. Full source/terminal root includes an exact
post-terminal custody copy of the original collection in `collection_source/`:
`gpu_artifacts_local/astra_event_two_hop_turnbound_terminal_20260914_attempt1/extracted`.
Archive local/remote SHA256:
`80b411ce668b9c2f5db0eadaac0b0ab5a3bedc0a9debcb7166ce491c4ecb61e2`.
Independent CPU replay/reduction COMPLETE with Kant: counts, captured-source
episodes, protocol, native calls, recorded readonly joins and all14 reused
collection files agree. Permanent receipt `SEQ249_independent_reduction_20260914.json`
beside extracted has SHA256
`270b1e08a52371b6a79aa95c16953c741cd63242b806c1e88d54a6a33c535249`.
This is recorded-state verification, not new tensor authentication. Next recipe is actual coached trajectory
collection and response-only SFT, not another prompt rewrite or an unchanged
memory fit that leaves the action-interface failure unaddressed.
