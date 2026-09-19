# Reader-source handoff for Pasteur, via main

September 19, 2026. Pair epoch2 uses the unchanged tested reader at
`research_loop/workers/rohin233_recovery_node4_20260918/checkpoint_tail_runtime.py`:

`972456b7d6cb026cc922e067114701d4f157fa6ed775e4406ecb52c86eef7d3e`

The preparation runner verifies this against
`CHECKPOINT_TAIL_SOURCE_MANIFEST.json`'s exact final source pin and snapshots the
manifest/log hashes in `prepared_epoch2_v2/INPUTS.json`. The existing reader log
records 18 passing tests; those are historical evidence, not a newly run suite.
Fresh pair tests run the actual reader against both original learner/frozen
journal classes and pass 14 tests per exact prepared closure.

No trusted/O(tail) reader, native-wide journal constructor port, or C2 receiving
policy was silently substituted. The pair-specific addition is
`gpu/pair_retention_runtime.py`, installed through the one exact existing
`r232_recovery.py` journal-binding seam. Original writer locking, confinement,
control classes, saved state, journal/INBOX, and deadlines remain unchanged.
The wrapper preserves full explicit journal audit and initialization checks.
Source adoption is distinct from wall authorization. No live activation occurs.

Please review/confirm that this pinned hash-prefix scanner is the intended
shared reader source; do not change either immutable source in place. Main owns
delivery of this handoff. `reader_owner_ack_pending=true` is intentional: no
Pasteur reply or agreement has been inferred from writing this file. The complete
hash delta and CPU evidence are in `EPOCH2_HANDOFF.md` and `prepared_epoch2_v2`.
