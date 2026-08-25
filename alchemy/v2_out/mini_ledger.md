# L0 iteration ledger (overnight 2026-08-25/26)
Rule: every recalibration cites the result's decomposition + which design
principle drives the change. Bar: memory_think matches context player.

| run | config delta | context | rag | mem_plain | mem_think | diagnosis -> next |
|---|---|---|---|---|---|---|
| L0-a (50ep) | initial | kind .43 | .55 | .34 | .27 | ALL <= NOTHING-prior (.58); join-names echo question => both metrics contaminated. FIX INSTRUMENT: balanced eval, nonce names, per-kind, grouping-F1 |
| L0-b (200ep) | eps x4 | .24 | .57 | .54 | .54 | same contamination; context DEGRADES with length (lost-in-context redux) |
