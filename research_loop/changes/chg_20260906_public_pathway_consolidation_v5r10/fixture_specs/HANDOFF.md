# PPC5r10 proposal fixture repair handoff

Date: 2026-09-06  
Scope: proposal bytes and static/semantic validators only. This handoff grants
no architecture ratification, fixture materialization or execution, model or
GPU authority, conformance result, seal, scientific claim, or release authority.

## Outcome

PPC5r10 is a new namespace; no PPC5r9 byte was overwritten. The replacement
keeps the 2,987-case content-addressed vector as the sole proposal universe and
hard-quarantines the stale 7,629-case branch-key universe and its author/oracle.
No materialized PPC5r10 fixture universe exists.

The 58 T04--T14 positive reducer vectors now have facts-only identities,
closed per-law input schemas, closed output tuple schemas, closed schemas for
embedded canonical JSON, exact executable proposal reducers, and exact
source-pointer hashes. Expected results are not present in executor inputs.

Repairs corresponding to the independent audit:

1. T08 derives its changed leaf from the actual one-field pair. There is no
   executor-visible perturbation label.
2. DREAM failure/status is predicate-derived from input facts. The DREAM
   reducer carries no input or output ordinal.
3. T13 resolves a concrete same-run 12-ingress package, requires all ingress
   facts and T02--T12 results to PASS, excludes future/model authority, checks
   the exact registry rows, and performs a genuine Kahn traversal of the exact
   14-stage source graph. Alias, backedge/cycle, missing, duplicate, future,
   and failed-ingress probes are rejected.
4. T14 consumes an ordered 24-row same-run predecessor fact vector with exact
   canonical bytes and hashes. It derives the 11 cold-replay ingresses, six
   final-result ingresses, and one outbound edge independently from both the
   current schema and inventory and requires those relations to be equal. Two
   distinct checked-in replay implementations are code-byte/hash bound and
   must produce byte-identical canonical relations. The six final-result source
   facts are type/role/ordinal/run bound. Missing, extra, reordered, identical
   implementation, release-input, and relation-disagreement probes fail.
5. `QUARANTINE_RFC.json` names the four superseded PPC5r9 bytes and hashes,
   excludes them from all PPC5r10 source ancestry and executor/oracle inputs,
   and records that no replacement universe is materialized.

The T13/T14 canonical artifacts are fixture-local proposal fact carriers, not
claims that authoritative runtime receipts have been executed. Their purpose is
to close reducer inputs before ratification while respecting the prohibition on
fixture execution.

## Exact counts and stable semantic hashes

- P = 465
- N = 2,467
- Q = 55
- logical proposal cases = 2,987
- planned independent executions = 5,974 (not executed)
- reducer laws = 58
- expanded reducer input entries = 1,113
- upstream source snapshots = 19
- exact upstream pointer bindings = 110
- input graph manifest SHA-256 = `118293962252dd8b3d0df945127471d26cf54f61d2c80b2e783108e96ba27768`
- semantic output SHA-256 = `33eb6dae96346fb3c88465402314fd1ed530d8a48700645d654d91f6686120b8`

## Stable proposal file hashes

| File | SHA-256 |
|---|---|
| `README.md` | `efc3ba1970ee9388e735361ddd5069c32c5eb578afd63941b68d1647d5cd1d3e` |
| `VECTOR_FIXTURE_RFC.json` | `b55b59fb8a0ab785de2162595cc9736836aee6e3925856025f63fc09e2145566` |
| `REDUCER_INPUT_ROWS_RFC.json` | `e3dbd33fd3d478635aa5580f44342b7b22566029822d642ed29f9ffcf9f76fe1` |
| `REDUCER_PROGRAMS_RFC.json` | `80e3919f8b04bc39b71b0ee28a6fc0328d8daa34ba69ae9d8744d60148664ffe` |
| `REDUCER_SOURCE_SNAPSHOTS.json` | `7d22db7336ad67996f21a96a1b297f2f9afddf3d9dc75145435dba7f21534973` |
| `REDUCER_EXACT_SOURCE_BINDINGS_RFC.json` | `b123b7c9864a6e7f73e10dfaab0365a867a099f22af2e31cd5906c82654b0af1` |
| `REDUCER_MACHINE_RFC.json` | `fa1b92a670b9edec00d84f67cd42e3c694ed82786f4566c0501d43bf1f0cec00` |
| `QUARANTINE_RFC.json` | `40c27a57ba23fc6011827361e7559e83ba772ff732205e0fbff1a7789fbde1c2` |
| `PROPOSAL_CONTEXT_RFC.json` | `897d27e6a194ac172fbd8b7bf68b278ed1503c8fe01a06c867e2051379719a7a` |
| `author_vector_fixture_specs.py` | `a5394c3267808a8b08c30594458e0e8b76399a72a9d3b10f7cb7aefc38cafe8a` |
| `author_machine_rfc.py` | `39ba3ce6718218869fa23d2db4890dc8fe3507e0cd01144592c5b943344f6bce` |
| `validate_reducer_semantics.py` | `8dc53673ce99f771d8f2756df066678b397b29746ed831768f6bfb063e8525b5` |
| `validate_machine_rfc.py` | `79aa8e41c9e683ff4aeee7446b49b640ce4f2f2164f8e32c9e903c38d5db724d` |
| `validate_quarantine.py` | `f1248e23b185d64eef4b53a5abf51d2fd14d78c143062b31a9e96d4210481af1` |
| `t14_replay_a.py` | `83e757dd9b1142a7b3d47eddbb0b42ecc87c603c9ff5cf4b5009e49497380250` |
| `t14_replay_b.py` | `444b52d6f9e66446e0a68afa9b95b83a39576f49fdae9409ee94a565ee6af04f` |

## Validator results

`author_vector_fixture_specs.py` reproduced the fixed P/N/Q/logical counts.
`author_machine_rfc.py` reproduced `REDUCER_MACHINE_RFC.json` byte-for-byte.
`validate_reducer_semantics.py`, `validate_machine_rfc.py`, and
`validate_quarantine.py` all returned `status=PASS`. All Python sources also
passed bytecode compilation.

## Remaining gates

- A fresh independent static audit is still required before any proposal
  closure claim.
- The 2,987-case vector is intentionally not materialized; therefore no
  executor-set equality, conformance receipt, or runtime result exists.
- No generator/schema/registry/normative PPC5r9 file was changed. If later
  ratification requires a top-level durable fixture artifact schema, that is a
  separate architecture change and is not proposed here.
