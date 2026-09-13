# Q0 final fix verification — bounded advisory

**Date:** 2026-09-13, final identity check 02:36:27 UTC.
**Disposition:** All five previously reported cases are **closed on static inspection of the supplied final bytes**. No concrete residual defect was identified within this bounded recheck. This is advisory closure of these findings only, not governance ratification, complete executor certification, CPU acceptance, or native/scientific qualification.

## Verified identities

Both source/test hashes matched Main's EDITSTOP identities at the beginning and end of inspection:

```text
gpu/astra_pairwise_q0.py
596071780b961031ef8ef5e352898391df47038db70e2acb68b5c3dbe15c201b

tests/test_astra_pairwise_q0.py
5e4eb5cb9926403319480b4bf8fc5d2225dd1768bb049909da604c1edb634afe

/tmp/astra_pairwise_q0_implementation_handoff_20260913.md
846d2100dbaefb07044323e74c2e90112444a530e27ad043f9cbe8404769a792
```

## Finding dispositions

### 1. Final release/raw-reduction exceptions bypassed abort finalization — CLOSED

`gpu/astra_pairwise_q0.py:1891` initializes release as unverified and catches final release-query failures. `gpu/astra_pairwise_q0.py:1903` separately catches native raw-reduction exceptions; accumulated failures are persisted before constructing `native_abort` at line 1909.

Crucially, `gpu/astra_pairwise_q0.py:1978` now selects the abort **before** reconstructing rejected stages. Replay also takes the failure path without native verification/tokenizer loading at line 2061. `native_abort` at line 1956 preserves failure information and explicitly withholds unvalidated partial counters. This addresses both the original raw-counter rejection and release-query exception cases without mislabeling them scientific nulls.

Matching regression cases are present at `tests/test_astra_pairwise_q0.py:1119`, `tests/test_astra_pairwise_q0.py:1126`, and `tests/test_astra_pairwise_q0.py:1147`. They were read, not run by this reviewer.

### 2. Late final writes left a sealed scientific report that could not replay — CLOSED

`gpu/astra_pairwise_q0.py:1917` writes provisional resource/reduction evidence, not a native scientific `report.json`. `provisional_reduction` at line 1966 removes the candidate's claim flag and explicitly marks the stored wrapper non-scientific. The seal remains pending durable finalization.

Durable inventory/seal synchronization precedes the completion observation at `gpu/astra_pairwise_q0.py:1919`. A publication overrun creates a bound abort marker at line 1928. Replay derives a nonreportable result for late evidence completion, a missing witness, or late publication at lines 2076, 2080, and 2081. Thus the original ordinary late-write path no longer strands an immutable scientific terminal that replay must reject.

`tests/test_astra_pairwise_q0.py:1132` contains deadline-crossing cases for RESOURCE, reduction, SEAL, and FINALIZED writes. This is source-level verification of the implemented disposition, not a crash/media-failure durability guarantee or new process-guard review.

### 3. Execute-time verification received an uncounted interval — CLOSED

`gpu/astra_pairwise_q0.py:1809` captures wall and monotonic starts at execute entry and passes them into the controller. The deadline at line 1825 and budget at line 1839 reuse that start. Post-verification checks at line 1844 account for both elapsed clocks before releasing work. Slow verification no longer receives a fresh 2700 seconds.

The corresponding no-worker timeout regression is present at `tests/test_astra_pairwise_q0.py:1141`.

### 4. Accepted one-ULP supplied q/M drift could change locality gates — CLOSED

`gpu/astra_pairwise_q0.py:995` checks raw supplied values against canonical reconstruction, but `gpu/astra_pairwise_q0.py:1030` now puts **reconstructed**, not supplied, q/M into the gate-bearing readout. Consequently accepted serialization drift cannot choose a different gate result for identical primitives. Raw evidence remains preserved, and this fix does not widen scientific locality thresholds.

`tests/test_astra_pairwise_q0.py:661` exercises accepted nextafter mutations of both q and M through `indexed_readout`, checks canonical readout equality, and compares actual locality outputs.

### 5. Common-offset M producer/validator algebra disagreed — CLOSED

`gpu/astra_pairwise_q0.py:932` routes the producer through `canonical_prefix`; the validator and reducer use the same function. At line 948 the legal-pair log normalizer is reconstructed consistently, with bounded normalizer-rounding handling and M constrained to at most one. The previous separately exponentiated sum in validation is gone. In particular, the earlier equal-branch `1000 + log(2)` scalar case no longer follows two inconsistent M formulas.

`tests/test_astra_pairwise_q0.py:651` covers producer-to-validator round trips at offsets 0, +1000, and -1000, including negligible and non-negligible outside mass.

## Scope and evidence limits

Read only the final executor/tests and the explicitly requested handoff for this turn. No later scientific source, experimental result, model, tokenizer, GPU, network, or Git operation was consulted or executed. No tests or project-code probes were run; Main owns final native-environment CPU acceptance. Handoff test-pass statements remain author-reported evidence, not independently reproduced results here.

Only this report was written. No source edits, reversions, changes to frozen constants, new guard scope, or operational launch/stop recommendation were made. No further repair is requested for these five cases on these hashes.
