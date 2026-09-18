# Disjoint R176 integration handoff

Ownership update: Main now assigns the shared receive-admission race repair to
Bernoulli exclusively (`transfer.py`, plus `prep_common.py` if necessary).
The suggested Ampere slice below was not assigned; do not infer a second writer.
Concurrent transfer use remains held until the race fix and bound review pass.

Priority: C2 fixed sleep33 alone; no C5 or generalized-scheduler barrier.
Suggested Ampere slice, pending Main's assignment: own `r176_transfer.py` and its
tests, integrating a complete exact closure with explicit R176 allowances.
Do not change frozen R172 controls or R176 proposal/slots/scope.

Author owns `preparation_io.py`, `c2_capture.py`, local launcher, receiving CPU
and narrow runner. The source capture produces `source_capture1/capture/COMPLETE.json`
under `/localhome/local-rohing/orch_r176_retelling_retention_20260917_generation1`.
Its files closure includes original COMMIT, native MANIFEST, birth, child-only
private witness, exact source evidence and boundary. Preserve all bytes privately.
No optimizer/RNG, journals outside this closure, model/provider calls or signals.

`preparation_io.Ledger` is the separate local campaign authority. Each global
reservation is returned as `{document, reference}` and charged without refunds.
Adapter passes are unique per life/sleep/pass, max128MiB; per-life metadata1GiB,
adapter8GiB. Global metadata2GiB (discovery32MiB included), adapter16GiB,
receiver storage2GiB. Stream directly through sanctioned wrappers, no local
archive. Source export, receiver stream and CPU verification have distinct
advance reservations; no reusing R172 allowances. Preparation is not execution GO.
