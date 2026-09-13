# Stage2A scanner/checkpoint integration — September 13, 2026

Builder engineering checkpoint, 23:03 UTC. Mission remains active/incomplete.

## Verified increment

Main ran the integrated VM suite from 22:59:14 to 23:02:30 UTC:
506 tests, 491 passed, 15 native-only skips, 194.606 seconds. All 46 source
and test hashes were unchanged before/after the suite. The filename's 2301Z
is an attempt label, not the observed start time.

Receipt: research_notes/astra_memos/receipts_20260912/astra_stage2a_scanner_checkpoint_integration_20260913T2301Z_attempt1.log

SHA-256: 7b2755216ed7e84f5fbf7b84cba8bb86eb436b51902f958d96eb647b29af520a

The nine trainer native tests and six checkpoint native tests already passed
separately on node2 with CUDA hidden, using tiny synthetic CPU models. Their
receipts remain distinct; they were not rerun as a combined native suite.
The fresh-process checkpoint receipt and durable source-bundle location are
in 2026-09-13_stage2a_checkpoint_fresh_process_receipt.md. Main also reran the
16 filesystem tests successfully during this continuation.

## Scanner scope

The input bridge derives exact content spans and chronology from authentic
retained birth traces. All 512 synthetic CLOSED/ATOM_LOCAL projections pass
with the explicitly supplied synthetic inventories. This is not complete
semantic/future/route inventory validation or native chat-byte certification.

V1 and V2 causal-occurrence notes are preserved. V2 removes only the extra
selected-EVENT-owner constraint on a historical GOT that equals latest observed
CURRENT. Its owner must still be a well-typed EVENT, and its original service
provenance is retained. This handles the authentic p21/m1 shared-destination
case without deleting history or admitting an unseen destination. No full
action, future-identifier, semantic-alias or registered-route exception is
added. Wrong/missing CURRENT, malformed/missing owner and forged observation
tests remain. Lorentz reports 84 targeted tests passing in 19.508 seconds;
Main's integrated receipt above independently includes those tests.

| File | SHA-256 |
|---|---|
| organism_v6/composition_birth_stage2a_scan_inputs.py | 0819959770d1f89b1f38572c9bcc78a7dfab9eea8ff6034d064a774d81855c0a |
| organism_v6/composition_birth_stage2a_scanner.py | 350359d58153364af732d45a7e1d88e85b5f98bfec26cabad9c3a7c666e997be |
| tests/test_composition_birth_stage2a_scan_inputs.py | 292aed7a8caee550ca2ed714141138c8190fd098f817066047f966b547c43b84 |
| tests/test_composition_birth_stage2a_scanner.py | 0bda6a3d3229975ea64157a377fc947a8100d2e668aaa47fe162e720b63196b1 |

## Concrete remaining source gap

A fresh read-only gap audit identifies the missing source-derived inventory
producer. The existing bridge still accepts caller-supplied semantic bytes,
future identifiers and registered routes. Clear toy inputs cannot close that
gap. The audit also identifies choices not fully bound in the inspected
contracts: complete birth semantic-object schema, future-universe/disclosure
boundary, registered multi-step route membership/serialization, and some
birth-core derivation rules. These need an explicit source disposition before
canonical material preparation; do not invent an empty inventory or silently
choose a visibility rule in code.

The scanner's 4096 ledger-entry bound is another concrete integration risk:
a family-A world has 2400 ordinary EVENT IDs and 2400 ordinary ports before
queries. Whole-world future semantics would exceed it at early boundaries.
Do not truncate or sample the forbidden ledger to pass the bound. Resolve
the intended universe and use a measured adequate resource bound.

Unambiguous work can proceed on full constructor reconstruction and exact
source/record cross-checking while those narrow choices are reviewed. This
is training-data hygiene for the selected experiment, not a reopening of
the deferred general C11 guard. A fresh source audit remains required before
the separate materialization/tokenizer/runtime preparation gates.

## Operational limits

No Qwen/tokenizer instantiated, GPU science launched/killed, curl/wget retried
or approval requested in this continuation. No node1 writes. Its bounded
21:33 preservation audit still reports no demonstrated missing Builder-owned
payload; this is not universal custody coverage for other owners or later
writes. Preservation deadline remains September 13, 23:14 UTC; lease end
September 14, 23:14 UTC. Existing independent results and SEQ-195 stay intact.

Next scientific target remains reduced BASE/D1 ATOM_LOCAL (560 reserved calls)
then a qualified same-adapter two-SLEEP junction, not the full matrix or a
repeat of completed retention experiments. No mechanism freeze, general G3,
H1/H2, parenting or paper-grade claim is promoted.
