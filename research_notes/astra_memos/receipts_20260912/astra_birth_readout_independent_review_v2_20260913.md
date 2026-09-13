# Initial birth independent review v2 — terminal handoff / EDITSTOP

**FINAL_BOUNDED_COMPARISON_COMPLETE**. Exactly the requested NEXT/comparison gap; v1 preserved.
One stdlib 384-output recount completed after targeted parser regressions. No frozen scorer was executed.

## Recount and stored comparison

| Cell | Assigned PROSPECT | Assigned REVISE | Belief/goal twins | Each revision family | Addition | Copy | Token-limit calls |
|---|---:|---:|---:|---:|---:|---:|---:|
| OFF | 0/32 | 0/64 | 0/16, 0/16 | 0/32, 0/32, 0/32 | 8/16 | 8/16 | 96/128 |
| AUTH | 32/32 | 58/64 | 16/16, 16/16 | 26/32, 26/32, 26/32 | 15/16 | 16/16 | 0/128 |
| DERANGED | 32/32 | 56/64 | 16/16, 16/16 | 24/32, 24/32, 24/32 | 15/16 | 16/16 | 0/128 |

DERANGED joint AUTH-truth counts remain 0/32 PROSPECT and 0/64 REVISE; assigned-map success is not AUTH truth.
**Both registered conjunctions FAIL**: revision families require 29/32 and addition 16/16; DERANGED also misses REVISE 58/64.
No headline/registered floor was relaxed. The shared addition error remains call 0097: **31+48=79, raw ACT: 89**.

## Unique NEXT fix and explicit metric differences

NEXT now requires one complete line value (anchored start/end, optional horizontal whitespace/CR), plus exactly one tag.
`NEXT: dax, wug` cannot be prefix-parsed as dax; repeated NEXT tags are rejected even if their values agree.
Regressions: seven single/dual/repeated NEXT cases, repeated COMPARE/POLICY cases, and inherited fixture assertions passed.
DERANGED calls **0007 and 0055** both emit `COMPARE: MATCH\nPOLICY: KEEP\nNEXT: dax, wug`.
The independent parsed fields now omit NEXT. DERANGED AUTH-NEXT correctness is **6/64**, matching frozen (v1 incorrectly reported 8).
The independent parser retains valid assigned COMPARE/POLICY tags on those two invalid rows; frozen parsing clears the entire field object.
Consequently those two assigned-field totals are **64/64 independent versus 62/64 frozen**. Both rows still fail strict and joint scoring.
This explicitly documented field-retention definition difference is not a repaired success or a scorer allegation.

Comparison coverage (scalar checks): `{"aggregate_field_counts": 48, "headline_counts": 120, "parsed_fields": 654, "registered_counts": 62, "row_field_correctness": 1920, "row_headlines": 4224, "twin_counts": 75, "twin_edge_scores": 1920}`.
Difference ledger: **10** entries; unexplained: **0**. Entries are in JSON `comparison.differences`.
Aggregate field totals, per-row field flags and parsed-field entries repeat the same two-row definition distinction; these are not distinct failed model cases.
Parsed ADDITION integer/string representations were normalized for comparison only. All strict/joint headlines, twin counts/edges and registered counts match if no unexplained entries are listed.

## Scope, disclosure and raw trust limits

Reviewer authored downstream /tmp/astra_born_process_readout_20260912.py, but did not author this original birth runner/corpus. Algorithmically independent recount, not a blinded reviewer: Main supplied expected counts and reviewer previously inspected scorer interfaces. No frozen scoring function is imported or invoked; stored results are compared only after all 384 recounts.

This completes only the bounded raw-count/parser comparison, not a full scientific/native audit or approval.
One authored root, exploratory exposed dev diagnostic: **SOURCE_AUTHORED_BIRTH_NOT_CLEAN / UNRESOLVED_LOCAL_HASHES_ONLY**.
No L1/G3/P1/G5/H1/H2 or birth-impact promotion. No native tokenizer, full weight rehash, network, Git, launches or helper edits.
Pinned local metadata, raw token IDs and saved renderings establish artifact consistency, not independently authenticated weights, token decoding or model origin.
v1 documents the existing arithmetic, failure examples and nested cost findings; v2 does not expand that audit.

## Exact hashes

```text
e988772186478818d67adbef16ad9d8b6d77fbe9de46a0971e11f2211525e8ab  /tmp/astra_birth_readout_independent_review_v2_20260913.py
2b70eb7fb3cae1554d445599caf13ba0b972631644bf8a12ea785d09a247afcb  /tmp/astra_birth_readout_independent_review_v2_20260913.json
788ac4bbad3a417fafeec6706cdbaf3ab502656a6bece7814295eb46365c4a56  capsule::metadata/run/run/result.json
```

Input capsule/validation hashes and all 384 rows remain in the JSON. Markdown final-byte hash is returned separately.

**EDITSTOP. No further edits or checks under this bounded assignment.**
