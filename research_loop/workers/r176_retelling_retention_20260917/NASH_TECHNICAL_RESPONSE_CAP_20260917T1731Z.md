# Author response: actual receiving validator metadata cap

Confirmed from Nash's read-only diagnostic at **17:29:23 UTC**:

- `VALIDATOR_REFUSED`, reason `delegated_read_cap`.
- Configured phase cap: **25,165,824 bytes (24 MiB)**.
- Successfully charged metadata before the interpreter: **17,568,725 bytes**.
- Actual interpreter read: **8,025,024 bytes**.
- Attempted total at that point: **25,593,749 bytes**, exceeding the cap by
  **427,925 bytes**. Further validation/runtime reads still need headroom.
- Adapter reads, scanner invocations, model/provider calls and receiving writes
  in that diagnostic were all **zero**. The authorization inputs were explicitly
  synthetic/in-memory, not a Main GO or actual execution attempt.

This is an author-side read-budget integration defect. The seven standalone
receiving runner tests did not exercise the full actual-config validator and
therefore did not expose the interpreter/source footprint. Their pass remains
true but is not an end-to-end validation pass; no scientific failure is relabelled.

Nash's separate actual-byte checks establish the original custody/empty-context
joins, pair equality, private config permissions, exact source/CPU/runtime pins,
and clear old-release receipt. I have not edited the reviewed runner, common
helper, deployed source/configs or existing reservation documents.

## Repair boundary

Do not raise `bytes` in an existing reservation or silently edit an actual config.
The repair must use a new immutable allowance/config binding with honestly
charged additional metadata inside the same R176 global/per-life ceilings; all
existing reservations remain preserved. Adapter passes/cells/calls/prompts,
original source and independent empty history remain unchanged. A larger metadata
allowance is not a larger scientific call budget or new admission gate.

For the technical question of sufficiency, a diagnostic using a larger cap in
memory can distinguish this first shortfall from later validator blockers;
32 MiB is a candidate for diagnosis, **not yet a proven sufficient runtime cap**
or a changed source authority. The actual reviewer read allowance still governs
any additional read-only diagnostic. The author is not treating this suggestion
as permission to manufacture a real GO or to rerun the science.

New disjoint capture work does not consume these reserved execution phases.
C2 sleeps34,35,37,38 have separately charged source captures; sleep36 remains
missing a bound completion pointer. The first reviewed sleep33 tranche is still
exactly two condition configs /six future calls and has made no model calls.
