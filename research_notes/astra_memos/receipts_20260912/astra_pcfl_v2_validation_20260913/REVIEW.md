# Main CPU validation reconciliation

September13 18:50UTC. Final production runtime matches commit71adf462;
only outer test expectations changed after that commit. No native GPU
outcome is included in these CPU receipts.

- `fit.log`:20testsPASS168.645s.
- `acquisition.log`:13testsPASS190.671s.
- `readout_campaign_material.log`:27testsPASS75.299s.
- `outer_corrected.log`:21testsPASS14.677s.

Total81tests pass in these terminal groups. Original `outer.log` and the
batch `completed.json` remain preserved as FAILED: three tests still expected
the temporary blanket descendant prohibition, or reused an output directory
after the new fail-closed path correctly created its failure receipt. Tests
now check failed collections/no spawned children and use distinct roots.
No production relaxation was made to satisfy them. Earlier timeout-only
invocations have no terminal count and are not counted as successful tests.

Bounded review fixed two actual pre-launch gaps: entry/seed/GPU/budget joins,
and clean-C0/actual-corpus binding at readout. Re-pinned adversarial cases now
fail without model calls. Raw native acquisition still must be measured.

Native source package additionally needs the registered own-write scope
Markdown. Full source archive SHA256:
`21936c7acdd2fe846fb4ce78de2b5b2f86f13df8cdbf4c0be3211b887c28fc1b`.
Local/native archive hashes match. No frozen code was changed on the node.
