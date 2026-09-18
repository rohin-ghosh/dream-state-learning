# Tesla six-original receiving assignments — September 17, 2026, 16:44 PDT

## Superseding reconciliation — 16:45 PDT

Before any transfer/dispatch, found Tesla's already-persisted16:43
`node3/r188/REHOME_ALLOCATIONS_V1.json`. Adopt that mapping to avoid competing
assignments: creative_reread1→node2GPU0, creative_free4→node2GPU7,
creative_select7→first finished LR5/6; brain_free2→node4GPU5,
brain_guided3→node4GPU6, support_free0→node4GPU7. Ampere owns node2, Gauss node4.
Node2 transport subdirectories therefore use original physical1/4/7.
The original proposed table below is preserved but SUPERSEDED, never executed.
Authority is Main/worker scheduling under standing user directives; the
allocation file's original human-attribution wording is corrected by Main's
16:45 coordination addendum, not treated as new human ratification.

## Superseded proposal — not executed

Operational update16:46: initial archives for original1/4/7 are hash-verified on
node2 under the staging base's `transport/` directory. Per-archive evidence is
`REHOME_PHYSICAL{1,4,7}_TRANSPORT.RESULT.json`. No extraction/dispatch has occurred;
Tesla's final stopped-state packet remains required. The four local transport
tests passed. Neither LR slot is released as of16:46:32.

| Original node3 life | Receiver | Receiving owner | State |
|---|---|---|---|
| physical0 / support_free | node2 GPU0, minor0 | Ampere | P4 exited0; clear16:43 |
| physical1 / creative_reread | node2 GPU7, minor7 | Ampere | clear16:43 |
| physical2 / brain_free | node4 GPU5, minor6 | Gauss | Gauss confirmed free + device proof |
| physical3 / brain_guided | node4 GPU6, minor5 | Gauss | Gauss confirmed free + device proof |
| physical4 / creative_free | node4 GPU7, minor4 | Gauss | Gauss confirmed free + device proof |
| physical7 / creative_select | first naturally finished LR: node2 GPU5 OR6 | Ampere | pending44 + exit + fresh clear; bind once |

Node2 staging base: `/localhome/local-rohing/orch_r188_node2_rehome_20260917t2344z`.
Subdirectories retain original `physical0`, `physical1`, `physical7` identities;
`packet.tar.gz` is transport only, not a live root. Node4 base is Gauss's existing
`/localhome/local-rohing/orch_r188_node4_rehome_20260917t2341z`; Gauss controls its
per-original extraction/launch paths.

Tesla retains source stop/final-state/inbox/parent-transport ownership. Receiving
owners stage in parallel; do not claim the16:41 packets include subsequent work.
Preserve each original logical root with a private namespace bind, exact frozen
effective source and saved state. Reuse per-node strict device launcher mechanics,
not C2 copy source/config/treatment or a new parent. Fresh receiver CPU/source and
device admission plus explicit target deadline binding must precede continuation;
the node3 saved16:50 deadline is not silently rewritten. No new machine lease.

The sixth mapping is exclusive: first LR terminal44 AND native/outer exit AND
fresh clear wins. Do not dispatch both, stop either early, or occupy a baseline.
Chandra probes and optional R187 copies remain held. Baseline3/4 and P32 remain
running unchanged. Node2 repoGPU2 and node4 judgeGPU2 are not receiving capacity.

Exact packet hashes: Tesla's existing
`node3/r188/relocation_20260917t2341z/physicalN.VERIFIED.json` and `INDEX.json`.
No launch, stop, parent switch, or successful relocation is claimed here.
