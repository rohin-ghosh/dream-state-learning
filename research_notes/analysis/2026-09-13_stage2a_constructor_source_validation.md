# Full constructor/source-record validation

Builder, September 13, 2026, 23:13 UTC. Engineering source consistency only.

Implemented pure validate_birth_source in
organism_v6/composition_birth_stage2a_source_inputs.py. It rebuilds the complete
birth pair from copied role bindings and explicit display master, compares
every field of the selected case, and matches the exact rendered arm record.
This detects off-trace hidden registry/world-edge changes even when the old
oracle replay still passes. Returned case/record/maps are newly constructed
immutable snapshots; structured fingerprints bind their exact contents.

The fingerprint encoding is internal source metadata, NOT the outstanding
scientific birth semantic-object schema. It does not decide future-ID or
registered-route semantics, certify original input authority or independently
prove constructor correctness. It invokes no scanner, tokenizer/model,
filesystem/network operation or GPU; every readiness/science flag stays false.

## Main validation

Command: python3 -m unittest discover -s tests -p test_composition_birth_stage2a_source_inputs.py -v

Observed start23:11:38/end23:12:20UTC. All15tests PASS in41.108s. The48source
and test hashes, including previously accepted files, are unchanged across
the run. Tests cover64cases/both arms, all eight records for a selected
case, off-trace mutation, forged/rehashed records, type drift, mapping/master
errors and post-validation caller-map mutation. They use synthetic bindings.

| Artifact | SHA-256 |
|---|---|
| organism_v6/composition_birth_stage2a_source_inputs.py | c0034ecbe08061157eb8525a2898de4a9c0ea3a445d40981b8b6a1c62d5a0323 |
| tests/test_composition_birth_stage2a_source_inputs.py | 758490ca5c0a1c1d2dcbffe4100cb34a6a4ba5479baa9deeb7f9a5bb967d14b2 |
| research_notes/astra_memos/receipts_20260912/astra_stage2a_constructor_inputs_20260913T2312Z_attempt1.log | 11189ffed83ff17262172498b0181a3e35b87a297cb7ee48451097644d78d15e |

Lorentz separately reports15PASS in40.430s. Mendel independently reviewed
these exact frozen source/test hashes read-only and found no concrete flaw.
His scoped PASS covers complete selected-case comparison, snapshot isolation,
and fingerprint/authority boundaries. He ran no duplicate tests and made no
edits. This is not full Stage2A GO or independent constructor correctness.

The previous506-test integrated suite remains a separate receipt (491PASS,
15native-only skips); no combined521-test run is claimed. The new module
does not modify any previously accepted source. Scoped scanner/checkpoint
review is preserved in stage2a_scanner_checkpoint_scoped_review.md.

## Remaining preparation blocker and next action

The23:04UTC notebook request remains unanswered as of the latest local
checkout read: bind complete birth semantic schema, future-universe and
disclosure chronology, multi-step route serialization/membership, and core
derivation. Do not replace these with empty inventories or treat constructor
consistency as inventory completeness. Implement the resulting source-derived
inventory adapter and adequate bounds, test it, then obtain the full source
audit before the separately recorded material/tokenizer/runtime opening.
No formal C11 work is required for this continuation; it remains deferred.

Next experiment remains reduced BASE/D1ATOM_LOCAL560reserved calls followed
by the qualified authentic same-adapter two-SLEEP junction. No Qwen/tokenizer
execution, GPU science launch/kill or scientific promotion occurred here.
No new node1 writes; prior bounded preservation evidence unchanged. No active
CPU test or GPU experiment from this continuation remains running. The whole
research mission and mechanism freeze remain incomplete.
