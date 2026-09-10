# PPC5r9 repaired fixture proposal — independent static audit v1

Date: 2026-09-06  
Scope: fresh read-only/static audit of the stable PPC5r9 proposal bytes. I ran
only `drafts/audit_r9_proposal.py`, `validate_reducer_law_rfc.py`, and
`validate_reducer_semantics.py`. I did not author, materialize, or execute a
scientific fixture and did not invoke any model, tokenizer, trainer, behavioral,
or GPU path. No prior PPC5r9 advisory was present. This note grants no authority.

## Verdict

**BLOCKED at fixture-proposal closure.** The content-addressed identity repair,
fresh source bindings, and current T13/T14 edge membership are real improvements,
and all supplied validators pass. They are not sufficient: the executor input
is not closed per law, the declarative laws disagree with the normative programs,
several reducers select answers from ordinal/mnemonic labels, and T13/T14 do not
execute the semantics claimed by their laws. `VECTOR_FIXTURE_RFC.json` also
still declares these items unresolved.

## Stable snapshot and passing evidence

| artifact | SHA-256 |
|---|---|
| `protocol.md` | `9bf73ceb0b4467d961f76538d112448ff88988997fee32a9ec8c8410d0c16751` |
| `VECTOR_FIXTURE_RFC.json` | `4a170fc6679dd018cb5c91ef5ea97356f8ab795e01ddeab9bae224bf5f5b5655` |
| `REDUCER_LAW_RFC.json` | `f453c2b0d526ff1ac32acbbc07c68a279ae73a86006716d82bb9a6d742d7b46d` |
| `REDUCER_INPUT_ROWS_RFC.json` | `304a8386f15d5ac420df805d59a2f5c42018eb15f3228094a905693da09548f3` |
| `REDUCER_PROGRAMS_RFC.json` | `57b703dd1914dd00bf50cbda20e8b3a89625d5655a6d89cc39d66a54c2daccc7` |
| `REDUCER_SOURCE_SNAPSHOTS.json` | `2f1ead9ded98f4fb1f6d7b2d3958fd129d5e84e4ce65998358d336402aa507b5` |
| `REDUCER_EXACT_SOURCE_BINDINGS_RFC.json` | `3c3f2e11c8f5205844e30468737ac19c228fed6935159289b508e1a9aa260771` |
| `validate_reducer_law_rfc.py` | `33caf20cfe12170fea64c85ee3adf03428220976d285e1b45208bb42bee6142b` |
| `validate_reducer_semantics.py` | `3251a45d9a4e4a0dec049a4e753990f97e5d3bf59c046a13a6f18bc82c498c09` |

The three validators report PASS: 17 structural files/84 artifact types/195
visibility cells; 58 laws and 1,113 input rows; reducer-law hash `f453c2...`;
input-graph-manifest hash
`e9ad39e17dfcd8013f197bd34043f1d7cc261bf7bf9a104b408d80742d961233`;
and semantic-output hash
`890756a29e8176683373acd728b95a28ac92ee7f73cca900c0fe9c975a9e8438`.
An independent JSON-pointer recomputation also matched all 19 source snapshots
and all 110 exact law bindings.

The identity/projection itself is internally consistent: node IDs are
`SHA256(artifact_type || NUL || canonical_json_bytes)`, case IDs are hashes of
canonical `{test_id,suite_id,law_id,input_graph}`, all source bytes are carried
in companion nodes, and the 58 constructed case IDs are unique. The current
source-derived authority relation also contains the exact external edge
`T14_FINAL_REPLAY_RESULT -> PRECLAIM_AUTHORITY_RECEIPT` with role
`FINAL_T14_RESULT`, and the inventory currently yields exactly 11 cold-replay
ingress edges, 6 final-T14 ingress edges, and 1 outbound preclaim edge.

## Blocking findings

### F1 — the input/output machine contract is not a closed, consistent schema

`REDUCER_INPUT_ROWS_RFC.json` supplies fixed builders but no per-law property
schemas or scalar types. `rows_from_builder` uses `dict(zip(columns, row))`,
which silently discards surplus values, and neither validator rejects extra
input properties. The graph schema closes only the outer node envelope; each
row remains opaque JSON inside `canonical_json_bytes`.

More decisively, an independent expansion found that **57 of 58** law
`input_table.columns` lists differ from the actual expanded row keys, and **58
of 58** law `output_shape` field lists differ from the supposedly normative
`REDUCER_PROGRAMS_RFC.json` columns. For example, T08 ROUTE declares
`matching_route_rows`, `intervention_public_bytes`, and `queue_slots` but the
builder provides `matching_route_ids` and `intervention_payload_bytes`; its law
declares `public_bytes_sha256`, while the program returns raw `public_bytes`.
T14 declares actual run/predecessor/artifact/replay fields, while its builder
instead provides `{ordinal, role, artifact_type, cardinality,
reconstruction_kind, upstream_facts}`. Passing tuple-width/type checks cannot
resolve these contradictory contracts.

### F2 — expected semantics still leak through order and mnemonic labels

The vector RFC says mutation/axis/mnemonic labels never enter executor input,
reducer selection, or output (`VECTOR_FIXTURE_RFC.json:8-15`). In contrast:

- T08 INFLUENCE places `perturbation` in executor input
  (`REDUCER_INPUT_ROWS_RFC.json:33`), copies it to output, and uses it to choose
  the permitted result (`validate_reducer_semantics.py:437-446`). The changed
  leaf can be derived from the pair; this label is mutation provenance.
- T14 places `reconstruction_kind` in executor input
  (`REDUCER_INPUT_ROWS_RFC.json:75`) and copies it directly to output
  `relation_kind` (`validate_reducer_semantics.py:593-627`). It therefore does
  not reconstruct that relation from predecessor bytes.
- DREAM failures are a literal list indexed by input-row ordinal rather than
  predicates over row facts (`validate_reducer_semantics.py:362-371`). This is
  author-order decoding even though the case ID itself is now a content hash.

The absence of fields literally named `expected_output` is not enough to
establish the no-leakage requirement.

### F3 — T13 has the right current sources and edge counts, but not the claimed authority semantics

The fixed source bytes correctly encode 14 ordered stages, 12 T13 inbound
edges, 2 T13 outbound edges, and the external T14 predecessor. However,
`T13_TECHNICAL_REDUCE` declares technical PASS from `inbound_count == 12` and
does not validate the supplied technical-package facts
(`validate_reducer_semantics.py:570-575`). `AUTHORITY_DAG_REDUCE` calls a graph
acyclic when it has 13 non-self edges; it performs neither the promised Kahn
sort nor a real cycle/backedge/reachability test (`:576-588`). Thus a cyclic
multi-node graph can pass, and forbidden-future/package semantics are not
exercised. The source snapshot is fresh; the reducer is incomplete.

### F4 — T14 proves membership counts, not a closed predecessor-only replay

The frozen arrays and inventory agree on 24 ordered predecessor roles and the
required 11/6/1 edge counts. But the machine input contains no run ID,
predecessor refs, artifact table, self hashes, or replay implementation hashes,
and `T14_REPLAY_GRAPH_REDUCE` consumes synthetic `upstream_facts`. It never
resolves same-run typed predecessors, executes two distinct cold replays,
compares their relation bytes, checks replay status/runtime integrity, or builds
the six-input final result. Its output schema contains none of the claimed
independence, equality, T14 status, or final-edge-count fields. The resulting
16-row toy relation is not the law's claimed full reconstructed relation.

### F5 — the replacement RFC is not the sole coherent fixture universe

The vector itself retains five `unresolved_release_blockers`, including missing
concrete graph/output bytes, missing T08/T13 closure, an unrevised independent
oracle, and a ban on materializing the 13-spec universe
(`VECTOR_FIXTURE_RFC.json:190-195`). Those statements remain true of the
directory as a whole. The existing proposal-only
`ppc5r9_fixture_universe.json` (SHA-256
`cf3cbc6b970d650b3fd2f4c5a51a85ca9ae29c182c4ae6ce47ebe3f83c349dfa`)
uses the superseded branch-key representation and freezes 7,629 logical cases,
whereas the replacement vector freezes 2,987. Its recorded author/enumerator/
oracle source hashes are also stale: for example it records
`author_fixture_universe.py=60a821...` and
`independent_fixture_oracle.py=d82ce7...`, while current bytes are respectively
`c3ee04...` and `74b73d...`. The current oracle still hard-codes the old counts
(`independent_fixture_oracle.py:17-24`). The repaired reducer snapshot hashes
are fresh; the older universe's source ancestry is not.

## Minimal remaining repair

1. Choose and hash-bind one authoritative replacement universe. Rewrite the
   author/enumerator/independent oracle for node/graph/case/mutation tables and
   both carrier modes, and explicitly retire or quarantine the 7,629-case
   branch-key artifact from this proposal.
2. Add a closed, typed input-row schema per law; make every law input/output
   declaration byte-consistent with its builder/program; make validators reject
   extra/missing columns and wrong row widths.
3. Remove `perturbation`, `reconstruction_kind`, ordinal failure tables, and
   equivalent answer-selecting metadata from executor-visible rows. Derive
   changed leaves, failures, and relation kinds from facts plus the hash-bound
   reducer law.
4. Implement the claimed T13 Kahn/forbidden-future/package checks and T14
   same-run 24-predecessor resolution, two independent 11-ingress replays,
   6-ingress final reduction, and unique outbound edge. Add negative semantic
   cases that fail on alias, backedge, missing/extra/reordered ingress, equal
   implementation hashes, release input, and relation mismatch.
5. Regenerate all raw/pointer/graph/output hashes and rerun a fresh independent
   static audit before any fixture materialization or execution.
