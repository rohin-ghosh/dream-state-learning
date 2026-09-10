# PPC5r12 fixture proposal repair handoff

Date: 2026-09-06  
Upstream audit:
`research_loop/advisory/20260906_ppc5r11_fixture_static_audit_v1.md`,
SHA-256
`29e84b7adf48f40c363eba6a3170c95221e04d05c1d4ae7baa38e409fbb89238`.

Scope: proposal bytes and proposal-source validators only. This handoff grants
no architecture ratification, fixture materialization or execution, model or
GPU authority, conformance result, seal, scientific claim, or release
authority.

## Outcome

PPC5r12 is a new namespace. PPC5r9, PPC5r10, PPC5r11, the audit, and existing
normative documents were not edited. No materialized PPC5r12 fixture universe
exists. The proposal retains the 2,987-case content-addressed vector and 58
T04--T14 reducer laws over 1,113 exact input rows.

The three PPC5r11 blockers are repaired in these proposal bytes:

1. **Complete T14 semantic replay.** Replay A and replay B are distinct,
   self-contained implementations and each now emits exactly 24 semantic
   predecessor rows. The eight formerly ignored `present` carriers are
   consumed. For every one of those roles, an isolated `present:false`
   mutation is canonically re-encoded, rehashed, rederived through both
   replay relations, and required to terminate at
   `FAIL/T02_T13_PREDECESSORS`.
2. **T07 dispatch binding.** Both replays consume the predecessor's exact
   `dispatch_scope` and require `ALL_REGISTERED_ROWS`. The complete local
   dispatch registry is independently checked for canonical identity,
   self-hash, eight-row count, exact row/key order, role/cardinality and
   producer-role binding, consumer stages, and row content hashes. Four
   undeclared scope strings and separate source-identity, row-count,
   row-order, role, consumer-stage, and content-hash mutations change both
   replay relations and terminate at `FAIL/SEED_VIEW_DISPATCH_CLOSURE`.
3. **True local source closure.** Nineteen source files are vendored under
   `source_inputs/`; `SOURCE_INPUT_MANIFEST_RFC.json` binds every raw hash,
   and `PROPOSAL_CONTEXT_RFC.json` binds every consumed proposal/source file.
   No author, validator, or replay implementation contains a runtime path to
   PPC5r9, PPC5r10, or PPC5r11. `validate_local_closure.py` copies only this
   namespace to a temporary root, activates an inherited Python open guard
   that denies the original repository, proves the guard with a forbidden
   read, and then reproduces all three authors and all three independent
   proposal validators.

Already-confirmed PPC5r11 repairs remain intact: DREAM derives equality from
bound bytes; T08 derives its causal and noninterference relations from paired
upstream facts; T13 validates its concrete package and Kahn authority graph;
the T14 final decision consumes six exact self-hashed final carriers; release
exclusion is typed/value semantic; and legacy fixture bytes are quarantined
recursively by exact SHA-256 identity.

## Exact proposal counts and semantic hashes

- P = 465
- N = 2,467
- Q = 55
- logical proposal cases = 2,987
- planned independent executions = 5,974 (not executed)
- reducer laws = 58
- expanded reducer input rows = 1,113
- local source files = 19
- upstream source snapshots = 20
- exact upstream pointer bindings = 111
- proposal context files = 38
- input graph manifest SHA-256 =
  `ae0465d817324fe7771bcfc8d1987593096db79e1b671b8091c1705058132bb4`
- semantic output SHA-256 =
  `9eba9f7da6d959ab7361ecb2fd9ff997b6e033089d85d567e54ea7adbba781dd`
- T14 replay-A relation SHA-256 =
  `b4fec8409d562f658a0303c6ed7d7f9c917a4dcf6c60016b51cf30ee47729c2e`
- T14 replay-B relation SHA-256 =
  `b4fec8409d562f658a0303c6ed7d7f9c917a4dcf6c60016b51cf30ee47729c2e`
- each T14 relation contains 24 semantic rows

## Stable proposal file hashes

`PROPOSAL_CONTEXT_RFC.json` binds all 38 non-handoff proposal/source files,
including all 19 vendored source inputs. Its SHA-256 is
`10b647c9933b39b07d34af28c2ec4faed2a8ee9457b062764f578c97d0878997`.

| File | SHA-256 |
|---|---|
| `README.md` | `8eb04e58da752dfda107fc88b7a25415926a05bd37c10b567909e6ceec35aab1` |
| `VECTOR_FIXTURE_RFC.json` | `ac9ff5da98c552fa67a02460ca5f6cc6514ca448271f6df0c1ed49851c630310` |
| `REDUCER_INPUT_ROWS_RFC.json` | `5e8128de88d54f1a004e4b35fd42045257b4f2cab0607f3ab41b9987976796fd` |
| `REDUCER_PROGRAMS_RFC.json` | `9c0af34f6ba18093bc3efd2e1816b336335e8e4ee8e64c911cdfa4c1f7520053` |
| `REDUCER_SOURCE_SNAPSHOTS.json` | `1a1f2a367ec63b149e5a02f3e98a6b09fede4609b1c80f3ab3a4901c8232b63f` |
| `REDUCER_EXACT_SOURCE_BINDINGS_RFC.json` | `5a813fad0d7b1ddbf48a9f13c2c7e7a62446c1d9466f6acb59b1cd65bdb48212` |
| `REDUCER_LAW_BINDINGS_RFC.json` | `71368cbaab9578838ad0b2302407a823b978afc59f91c09a0073782b64aafa08` |
| `REDUCER_MACHINE_RFC.json` | `f62888ea8943b39a256f050a81e7711f69ae68ccf1c19ec47d5d3baf4b003737` |
| `SOURCE_INPUT_MANIFEST_RFC.json` | `02bf00936fc72cbcd1d0c9df3a73111fe7bb810b3cfd38d00c85b5c08f03ec16` |
| `QUARANTINE_RFC.json` | `f68d41f3290eb0c1e84c06b5895422184b58aade2b902f2ef7e43f783b2849a4` |
| `author_context_rfc.py` | `b054c4527d57b75551eab45e03b48cb3953270cec7260fdceb7852a344929317` |
| `author_machine_rfc.py` | `a12f9f68224161f69c5eda96e1bc9b5c89d9af0aa35e337afa4dce6c544763e2` |
| `author_vector_fixture_specs.py` | `1d1d1a3e72bd11d8351035e673a1a0bfe6cc003d3b29f629427df2b893e94369` |
| `t14_replay_a.py` | `ca555cd9d8374a960b2fcdbfb7484cac0b3a598df2d6abd7d283187093e39e50` |
| `t14_replay_b.py` | `06de8f58b1cfe41a4aaf3236d1758bc03e5d32798b797d53f2c4c6b5612c60dc` |
| `validate_reducer_semantics.py` | `2d38d9fdebdb3094828f2c454e209c45f30519c6071dc4340ebd73de4777b6e8` |
| `validate_machine_rfc.py` | `74f375b3108fb5f7dd60a055c0e05c1591b21fbe89c8cae001a4ad0324d2ac75` |
| `validate_quarantine.py` | `e1f25abb55f65720de336ef5ec5cf05f97a22de98a7fb5b64213c6d7cfa1a3aa` |
| `validate_local_closure.py` | `99fe141da1172bd4f9f7fb77ebd0186f4e584f616c207ec2b11a52b0cac61362` |
| `PROPOSAL_CONTEXT_RFC.json` | `10b647c9933b39b07d34af28c2ec4faed2a8ee9457b062764f578c97d0878997` |

## Validator results

- `author_vector_fixture_specs.py`: exact P/N/Q/logical/planned counts above.
- `author_machine_rfc.py`: byte-identical reproduction of
  `REDUCER_MACHINE_RFC.json`.
- `author_context_rfc.py`: byte-identical reproduction of
  `PROPOSAL_CONTEXT_RFC.json`.
- `validate_reducer_semantics.py`: PASS, 58 laws / 1,113 rows / 20 source
  snapshots, including all T14 presence and T07 dispatch adversarial probes.
- `validate_machine_rfc.py`: PASS, machine SHA-256
  `f62888ea8943b39a256f050a81e7711f69ae68ccf1c19ec47d5d3baf4b003737`.
- `validate_quarantine.py`: PASS, four excluded identities, 38 bound context
  files, two renamed/nested adversarial probes.
- `validate_local_closure.py`: PASS, 19 local source files, 38 context files,
  nine Python files, three isolated authors, three isolated validators, and an
  active/probed original-repository open guard.
- all Python proposal sources parse; all JSON proposal/source files parse.

## Remaining gate

A fresh independent static audit is required. Internal PASS is not proposal
closure and creates no authority. The 2,987-case vector remains intentionally
unmaterialized and unexecuted; no executor-set equality, conformance receipt,
runtime result, seal, or claim exists.
