# PPC5r10 fixture proposal — independent static audit v1

Date: 2026-09-06  
Scope: fresh audit of the stable
`chg_20260906_public_pathway_consolidation_v5r10/fixture_specs` namespace against
the PPC5r9 blocker advisory. I ran only the proposal authors, CPU
static/semantic validators, and read-only in-memory counterfactuals. I did not
materialize or execute a scientific fixture, call a model, or use a GPU. This
note grants no authority.

## Verdict

**BLOCKED at fixture-proposal closure.** The vector identity, closed structural
schemas, T08 pairwise derivation, current T13 package/Kahn result, current
schema/inventory edge relation, and current source-pointer hashes are repaired.
However, DREAM still consumes an answer-selecting boolean; T14's replays share
their semantic implementation and its final reduction is not bound to concrete
six-source facts; the machine author has an unrecorded PPC5r9-law dependency;
and the quarantine validator enforces old basenames rather than excluded byte
identities.

## Stable snapshot and passing evidence

All handoff hashes matched the fresh snapshot:

| artifact | SHA-256 |
|---|---|
| `HANDOFF.md` | `9f5776ab8df1aef0bb6c638e93a5893f819e3e76ddeff50143d5d259fc5b3e56` |
| `PROPOSAL_CONTEXT_RFC.json` | `897d27e6a194ac172fbd8b7bf68b278ed1503c8fe01a06c867e2051379719a7a` |
| `QUARANTINE_RFC.json` | `40c27a57ba23fc6011827361e7559e83ba772ff732205e0fbff1a7789fbde1c2` |
| `VECTOR_FIXTURE_RFC.json` | `b55b59fb8a0ab785de2162595cc9736836aee6e3925856025f63fc09e2145566` |
| `REDUCER_INPUT_ROWS_RFC.json` | `e3dbd33fd3d478635aa5580f44342b7b22566029822d642ed29f9ffcf9f76fe1` |
| `REDUCER_PROGRAMS_RFC.json` | `80e3919f8b04bc39b71b0ee28a6fc0328d8daa34ba69ae9d8744d60148664ffe` |
| `REDUCER_SOURCE_SNAPSHOTS.json` | `7d22db7336ad67996f21a96a1b297f2f9afddf3d9dc75145435dba7f21534973` |
| `REDUCER_EXACT_SOURCE_BINDINGS_RFC.json` | `b123b7c9864a6e7f73e10dfaab0365a867a099f22af2e31cd5906c82654b0af1` |
| `REDUCER_MACHINE_RFC.json` | `fa1b92a670b9edec00d84f67cd42e3c694ed82786f4566c0501d43bf1f0cec00` |
| `author_vector_fixture_specs.py` | `a5394c3267808a8b08c30594458e0e8b76399a72a9d3b10f7cb7aefc38cafe8a` |
| `author_machine_rfc.py` | `39ba3ce6718218869fa23d2db4890dc8fe3507e0cd01144592c5b943344f6bce` |
| `validate_reducer_semantics.py` | `8dc53673ce99f771d8f2756df066678b397b29746ed831768f6bfb063e8525b5` |
| `validate_machine_rfc.py` | `79aa8e41c9e683ff4aeee7446b49b640ce4f2f2164f8e32c9e903c38d5db724d` |
| `validate_quarantine.py` | `f1248e23b185d64eef4b53a5abf51d2fd14d78c143062b31a9e96d4210481af1` |
| `t14_replay_a.py` | `83e757dd9b1142a7b3d47eddbb0b42ecc87c603c9ff5cf4b5009e49497380250` |
| `t14_replay_b.py` | `444b52d6f9e66446e0a68afa9b95b83a39576f49fdae9409ee94a565ee6af04f` |

The supplied validators all report PASS. The vector author reproduces
`P=465`, `N=2467`, `Q=55`, 2,987 logical cases and 5,974 planned executions.
The machine author reproduces `REDUCER_MACHINE_RFC.json` byte-for-byte at
`fa1b92...`. Independent JSON-pointer recomputation matched all 19 snapshots
and 110 bindings. The semantic validator reports 58 laws, 1,113 rows, graph
manifest `118293962252dd8b3d0df945127471d26cf54f61d2c80b2e783108e96ba27768`,
and output `33eb6dae96346fb3c88465402314fd1ed530d8a48700645d654d91f6686120b8`.

The 58 actual expanded inputs match their machine schemas, which reject extra
and missing properties; program operators/columns and closed output tuple
schemas also match. T08 has only `left_upstream`/`right_upstream` and derives
the changed leaf from their one-field diff. The T13 package resolves 12 unique,
same-run, passing typed ingresses and ordered T02--T12 PASS facts; its result is
`3db47556d0cd72ff82c044e7374c410611aa8f118e234db82266172960a83fc7,
12,12,true,0,true,null`. The 14-stage Kahn order is source-derived and rejects
the supplied alias/backedge probes. Independently extracted schema and
inventory relations are equal and contain 11 cold, 6 final, and 1 outbound
T14 edges. The external edge is exactly
`T14_FINAL_REPLAY_RESULT -> PRECLAIM_AUTHORITY_RECEIPT`, role
`FINAL_T14_RESULT`, ordinal 0, cardinality `ONE`.

The four quarantined PPC5r9 artifacts also match their recorded hashes,
including the 7,629-case universe at
`cf3cbc6b970d650b3fd2f4c5a51a85ca9ae29c182c4ae6ce47ebe3f83c349dfa`.
No current v5r10 context entry names one of them, and no materialized v5r10
universe exists.

## Blocking findings

### F1 — DREAM still receives an answer-selecting render verdict

`REDUCER_INPUT_ROWS_RFC.json:20-29` includes `rendered_matches` but no actual
rendered and reference bytes from which equality can be derived. The reducer
uses that boolean directly to select `CONTEXT_RENDER`
(`validate_reducer_semantics.py:564-583`), while the machine validator only
checks that DREAM lacks an ordinal (`validate_machine_rfc.py:85-87`). A
read-only counterfactual kept every first-row fact fixed and changed only
`rendered_matches:true -> false`; the row remained machine-schema-valid, but
the answer changed from `INSTALLED/.../null` to
`INVALID/.../CONTEXT_RENDER`. Removing ordinal decoding did not remove this
expected-result channel.

### F2 — T14 does not provide two independent semantic replays or a concrete final binding

The two checked-in modules implement different traversal order, but both take
the same externally supplied `reduce_value` callback
(`t14_replay_a.py:8-18`, `t14_replay_b.py:8-19`). The wrapper supplies the same
`t14_value` lambda to both (`validate_reducer_semantics.py:494-501`). Thus every
relation-value rule is shared; equality cannot detect a defect in that shared
semantic implementation.

The six `final_result_source_facts` carry only
`{artifact_type,ordinal,origin,role,run_id}` and their carrier hash
(`REDUCER_INPUT_ROWS_RFC.json:2349-2373`), not the referenced artifacts,
self-hashes, replay decisions/status, manifest facts, or set-equality fact.
The reducer synthesizes `status:"PASS"` and relation hashes for the two replay
roles, computes a digest, and never supplies those six facts to
`t14_final_status`; PASS depends only on two strings, an implementation-id
inequality, 11/6/1 counts, and the release flag
(`validate_reducer_semantics.py:842-863`, `:483-491`). A schema-valid mutation
of `COLD_REPLAY_A.origin` from `REDUCER_OUTPUT` to `FORGED`, with its carrier
hash recomputed, still returned T14 PASS.

Release exclusion is also incomplete: `contains_release_input` searches only
dictionary key names, never string values (`validate_reducer_semantics.py:475-480`).
A schema-valid predecessor mutation changing `context_policy` to
`RELEASE_BYTES`, with canonical artifact hash recomputed, returned
`release_bytes_consumed=false` and T14 PASS. The checked negative probe covers
only an added key literally named `release_bytes` (`:1008-1010`).

The committed positive row does produce equal relation hashes
`e5bebd323e4f236b84c07b2a7dc16b774a7544457183e8a881e9eb6cb38a1d74`
and final-input digest
`fcebbf7e0405247bbbad959bf929f88fd7affa8141a6c441ecc64254622993a3`;
those hashes do not close the semantics above.

### F3 — machine reproduction depends on an unrecorded source

`author_machine_rfc.py` reads the PPC5r9
`fixture_specs/REDUCER_LAW_RFC.json` and copies both `test_failure_orders` and
every law's source-binding selection (`author_machine_rfc.py:13,88-115`). Its
current SHA-256 is
`f453c2b0d526ff1ac32acbbc07c68a279ae73a86006716d82bb9a6d742d7b46d`,
but that file/hash appears in neither `PROPOSAL_CONTEXT_RFC.json:7-18` nor the
machine's `source_files` emitted at `author_machine_rfc.py:125-130`.
Byte-for-byte reproduction succeeds only against an ambient, unbound PPC5r9
file, so the claimed v5r10 source ancestry is incomplete and future
reproduction is not freshness-protected.

### F4 — stale-universe quarantine is declared, but not enforced by byte identity

The hard rule forbids the four excluded *bytes* anywhere in v5r10 ancestry
(`QUARANTINE_RFC.json:7-21`). `validate_quarantine.py`, however, constructs a
set of excluded basenames, checks only basename intersection with
`context_files`, then scans only top-level text for those names
(`validate_quarantine.py:18-42`). An excluded artifact copied under a different
name (or placed below a subdirectory) is not rejected; no current/context file
hash is compared with the four excluded SHA-256 values. The present context is
clean, but the stated quarantine is not an enforceable byte-identity gate.

## Minimal remaining repair

1. Replace DREAM's `rendered_matches` with the actual closed, hash-bound render
   operands and derive equality in the reducer; add a negative probe proving no
   boolean verdict can select the failure.
2. Put the full relation-value semantics in two separately hashed replay
   implementations. Bind six concrete final source objects/references and make
   final PASS consume and validate each object's hash, run, type, role, ordinal,
   status/content and replay relation hash. Detect forbidden release artifacts
   and bytes by typed artifact/value semantics, not key spelling.
3. Vendor the needed failure/source-binding declarations into v5r10 or add the
   PPC5r9 law file and exact SHA to both context ancestry and machine
   `source_files`; make the machine validator itself perform byte reproduction.
4. Make quarantine validation recursive and compare every reachable/context
   artifact's raw SHA-256 (and any embedded source artifact identity) against
   all excluded hashes, independent of filename. Add renamed and nested-copy
   negative probes.

Regenerate affected hashes and obtain another independent static audit before
fixture materialization or execution.
