# PPC5r12 fixture proposal: fresh independent static reaudit v1

Date: 2026-09-06

Decision: **ACCEPT**, narrowly for proposal-source closure.

Scope: read-only audit of
`research_loop/changes/chg_20260906_public_pathway_consolidation_v5r12/fixture_specs/`
only. The prior PPC5r11 BLOCK advisory was used as an attack plan, not as
evidence that PPC5r12 was repaired. This advisory is outside the proposal
namespace and grants no architecture ratification, fixture materialization or
execution, model, tokenizer, task, trainer, adapter, token, GPU, conformance,
seal, claim, or release authority.

## Executive finding

PPC5r12 repairs all three PPC5r11 blockers in the frozen proposal bytes.
Both source-distinct T14 replays now consume all 24 predecessor roles. Each of
the eight formerly ignored `present` carriers independently changes both
replay hashes and fails closed when false. T07 consumes its declared scope and
the complete local dispatch-registry identity and semantics; scope plus six
coordinated registry mutations all change both replay hashes and fail closed.
The 19 source preimages are vendored, raw-hash bound, and sufficient to
reproduce the authors and validators in an isolated copy while the original
repository and all older change namespaces are denied.

The preserved positive surfaces also passed fresh attacks: DREAM byte/hash
binding, replay A/B separation, typed release exclusion, all six final carrier
origins/statuses/self-hashes, recursive exact-byte quarantine, author byte
reproduction, source provenance, and proposal-context closure. I found no
static proposal-integrity blocker within the declared scope.

This is not a runtime or scientific result. The 2,987 logical cases remain
unmaterialized and the 5,974 planned independent executions remain unrun.

## Frozen anchors and namespace inventory

The three requested anchors reproduced exactly:

| File | Verified SHA-256 |
|---|---|
| `HANDOFF.md` | `d9b5adda0646d73ada618a18ee19f8f40d256a0b30e4e5b6c9ba159e6c3629fc` |
| `PROPOSAL_CONTEXT_RFC.json` | `10b647c9933b39b07d34af28c2ec4faed2a8ee9457b062764f578c97d0878997` |
| `REDUCER_MACHINE_RFC.json` | `f62888ea8943b39a256f050a81e7711f69ae68ccf1c19ec47d5d3baf4b003737` |

`PROPOSAL_CONTEXT_RFC.json` contains exactly 38 distinct relative paths. I
recomputed every listed raw SHA-256 and found no mismatch. Its file set equals
the actual regular-file set after excluding only the context manifest itself
and downstream `HANDOFF.md`, as declared. The namespace contains 40 regular
files total, no symlinks, and no `__pycache__` directory. The 19-entry source
manifest is exact and is a subset of the context closure. The 20-entry source
snapshot table and 111-entry exact-pointer table also validate without a
missing or duplicate source identity.

Stable proposal hashes used directly in this audit include:

| File | Verified SHA-256 |
|---|---|
| `VECTOR_FIXTURE_RFC.json` | `ac9ff5da98c552fa67a02460ca5f6cc6514ca448271f6df0c1ed49851c630310` |
| `REDUCER_INPUT_ROWS_RFC.json` | `5e8128de88d54f1a004e4b35fd42045257b4f2cab0607f3ab41b9987976796fd` |
| `REDUCER_PROGRAMS_RFC.json` | `9c0af34f6ba18093bc3efd2e1816b336335e8e4ee8e64c911cdfa4c1f7520053` |
| `REDUCER_SOURCE_SNAPSHOTS.json` | `1a1f2a367ec63b149e5a02f3e98a6b09fede4609b1c80f3ab3a4901c8232b63f` |
| `REDUCER_EXACT_SOURCE_BINDINGS_RFC.json` | `5a813fad0d7b1ddbf48a9f13c2c7e7a62446c1d9466f6acb59b1cd65bdb48212` |
| `REDUCER_LAW_BINDINGS_RFC.json` | `71368cbaab9578838ad0b2302407a823b978afc59f91c09a0073782b64aafa08` |
| `SOURCE_INPUT_MANIFEST_RFC.json` | `02bf00936fc72cbcd1d0c9df3a73111fe7bb810b3cfd38d00c85b5c08f03ec16` |
| `QUARANTINE_RFC.json` | `f68d41f3290eb0c1e84c06b5895422184b58aade2b902f2ef7e43f783b2849a4` |
| `t14_replay_a.py` | `ca555cd9d8374a960b2fcdbfb7484cac0b3a598df2d6abd7d283187093e39e50` |
| `t14_replay_b.py` | `06de8f58b1cfe41a4aaf3236d1758bc03e5d32798b797d53f2c4c6b5612c60dc` |
| `validate_reducer_semantics.py` | `2d38d9fdebdb3094828f2c454e209c45f30519c6071dc4340ebd73de4777b6e8` |
| `validate_machine_rfc.py` | `74f375b3108fb5f7dd60a055c0e05c1591b21fbe89c8cae001a4ad0324d2ac75` |
| `validate_quarantine.py` | `e1f25abb55f65720de336ef5ec5cf05f97a22de98a7fb5b64213c6d7cfa1a3aa` |
| `validate_local_closure.py` | `99fe141da1172bd4f9f7fb77ebd0186f4e584f616c207ec2b11a52b0cac61362` |

## Independent author and validator reproduction

I invoked the proposal-only scripts directly with
`PYTHONDONTWRITEBYTECODE=1`; no model, tokenizer, task, materializer, or GPU
entry point was invoked.

```text
python3 fixture_specs/author_vector_fixture_specs.py
python3 fixture_specs/author_machine_rfc.py
python3 fixture_specs/author_context_rfc.py
python3 fixture_specs/validate_reducer_semantics.py
python3 fixture_specs/validate_machine_rfc.py
python3 fixture_specs/validate_quarantine.py
python3 fixture_specs/validate_local_closure.py
```

Observed results:

- vector author: `P=465`, `N=2467`, `Q=55`, logical `2987`, planned
  executions `5974`, vector hash
  `ac9ff5da98c552fa67a02460ca5f6cc6514ca448271f6df0c1ed49851c630310`;
- machine author: stdout was byte-identical to `REDUCER_MACHINE_RFC.json`;
- context author: stdout was byte-identical to `PROPOSAL_CONTEXT_RFC.json`;
- reducer validator: `PASS`, 58 laws, 1,113 input rows, 20 source
  snapshots, input-graph manifest
  `ae0465d817324fe7771bcfc8d1987593096db79e1b671b8091c1705058132bb4`,
  semantic output
  `9eba9f7da6d959ab7361ecb2fd9ff997b6e033089d85d567e54ea7adbba781dd`;
- machine validator: `PASS`, 58 laws, 1,113 rows, machine hash
  `f62888ea8943b39a256f050a81e7711f69ae68ccf1c19ec47d5d3baf4b003737`;
- quarantine validator: `PASS`, four excluded identities, 38 context files,
  two rename probes, replacement count 2,987;
- local-closure validator: `PASS`, 19 local sources, 38 context files, nine
  Python files, three isolated authors, three isolated validators, original
  repository open guard active and probed.

## Former blockers: fresh adversarial results

### T14 complete 24-role semantic replay: PASS

Baseline replay A and B each produced 24 semantic rows with the identical
relation SHA-256
`b4fec8409d562f658a0303c6ed7d7f9c917a4dcf6c60016b51cf30ee47729c2e`;
the terminal row was `PASS/null`.

I independently changed `present:true` to `present:false` in each of the
following predecessor carriers, one at a time:

1. `ADVOCATE_RECEIPT`
2. `ANALYSIS_BUNDLE`
3. `COMPLETE_MODEL_VIEW_MANIFEST`
4. `COMPLETE_RUN_MANIFEST`
5. `D1A_CONTROL_SET_MANIFEST`
6. `PROVIDER_AUDIT`
7. `REVIEW_RECEIPT`
8. `ROUTE_LINEAGE_AUDIT`

For every mutation I canonically re-encoded the current artifact, recomputed
its artifact SHA-256, regenerated the bound T14 parameters and all six final
source carriers, and reran the reducer. All eight changed both replay
relation hashes and terminated at
`FAIL/T02_T13_PREDECESSORS`. This directly repairs PPC5r11 B1; the
predecessor-vector hash is no longer the only changed output.

### T07 dispatch scope and complete registry semantics: PASS

The current T07 carrier contains `dispatch_scope=ALL_REGISTERED_ROWS`. I
replaced it independently with `FORGED_VENDOR`, `ALL_ROWS`, the empty string,
and lowercase `all_registered_rows`, re-encoded and rehashed the artifact,
and regenerated downstream parameters. Every value changed both independent
relations and terminated at `FAIL/SEED_VIEW_DISPATCH_CLOSURE`.

I then changed the locally supplied dispatch registry in six coordinated,
otherwise self-hash-correct ways:

- source identity (`architecture_id=FORGED_VENDOR`);
- row count and ordered-key count;
- first-two row and ordered-key order;
- first-row role;
- first-row consumer stages;
- first-row content hash.

For each probe I recomputed the registry self-hash before replay. Both replay
relations changed, both semantic checks named
`SEED_VIEW_DISPATCH_CLOSURE`, and the terminal reducer produced the same
failure. This repairs PPC5r11 B2 rather than merely binding a byte hash.

Dispatch provenance is closed at three levels: the vendored raw file hash is
`a391f25b4adfcd44b1a65a2c7d7f3a1d810efca0cf111928fe00cab347fc7ea4`;
the canonical full-registry value hash is
`da50392428b1403836a4bbeefe3c53774f46e71f52e141af69e4c4b09ab248e9`;
and the canonical row-array hash is
`9a3b3eab7119ef5a9ce896da1a060534784f02e81bc8bd30d77681536377fbba`.
Those identities agree across the local source manifest, proposal context,
source snapshots, exact source bindings, law bindings, and both replay
implementations.

### Local vendor closure with denied legacy access: PASS

All 19 vendored source files are byte-identical to the claimed v5r9 source
preimages, and every raw hash equals its source-manifest and context entry.
Runtime reproduction, however, uses only the v5r12 copies.

In addition to the packaged local-closure validator, I made a fresh temporary
copy containing only the v5r12 `fixture_specs` tree and installed an
independent inherited Python audit hook. The hook rejected every open below
`/Users/rohing/dream-state` except the isolated copy and rejected module names
containing the v5r9, v5r10, or v5r11 change namespaces. Before trusting it, I
proved denial against both the original repository README and the v5r11
handoff. Under that guard, all three authors and all three proposal validators
completed; machine and context author bytes still matched their RFCs exactly.

A separate static scan found no executable proposal path token for v5r9,
v5r10, or v5r11. Documentary legacy references and stable architecture/test
identifiers remain, but no author, validator, or replay resolved them as a
runtime file or import. This repairs PPC5r11 B3.

## Preserved positive surfaces

### DREAM answer leak and byte/hash binding: PASS

The DREAM input schema rejects an added answer-like `rendered_matches` field.
For an otherwise valid row:

- changed rendered bytes with stale hash produced
  `INVALID/DREAM_INPUT_BINDING`;
- recomputing that hash while leaving reference bytes unequal produced
  `INVALID/CONTEXT_RENDER`;
- making rendered and reference bytes equal and binding both hashes produced
  `INSTALLED/null`.

The decision is derived from the bound byte relation, not an executor-visible
answer bit.

### Replay implementation and source separation: PASS

Replay A and B have distinct source hashes, separate role tables, different
control structure and function sets, and import only `__future__`,
`fractions`, `hashlib`, and `json`. Neither imports the other or the validator,
and neither accepts a semantic callback. Replacing replay A's
`controller_transition` value in memory while leaving B untouched terminated
at `FAIL/REPLAY_AGREEMENT`.

This establishes source separation and one-sided-defect detection for the
declared static replay. It does not claim formal algorithmic independence.

### Semantic release exclusion: PASS

The release predicate ignores an ordinary benign key/value such as
`{"release_bytes":"ordinary-data"}`, but recognizes typed values such as
`RELEASE_BYTES` and nested forbidden `artifact_type` values. A current T08
carrier changed to `context_policy=RELEASE_BYTES`, canonically rehashed and
regenerated downstream, produced `release_bytes_consumed=true` and
`FAIL/RELEASE_BYTES_FORBIDDEN`.

### Six final carriers: PASS

I swept all six current final carriers independently. For each carrier:

- recomputed `origin=FORGED` failed `SINGLE_FINAL_T14_EDGE`;
- recomputed `status=FAIL` failed `SINGLE_FINAL_T14_EDGE`;
- `status=FAIL` with a stale inner self-hash but a recomputed outer source
  hash failed `SINGLE_FINAL_T14_EDGE`.

That is 18/18 adversarial failures across the two replay results, two
execution manifests, set-equality carrier, and fixture-spec carrier.

### Exact-byte quarantine: PASS within its declared semantics

The four excluded hashes exactly match the four v5r9 source bytes advertised
by `QUARANTINE_RFC.json`. In a separate temporary tree I copied all four under
unrelated names, two at the root and two under different nested directories.
The recursive byte scanner found all four solely by SHA-256 identity.

The scope is intentionally exact-byte identity. It is not arbitrary
substring, archive, transcoding, symlink-target, or generic-key data-loss
prevention. This is consistent with the proposal's narrow quarantine claim.

## Limitations and disposition

**ACCEPT** means only that the frozen PPC5r12 proposal/source package passed
this fresh static audit and may be presented to the next explicit governance
stage. It does not itself authorize that next stage or any execution.

This audit did not materialize the vector, invoke an executor, compare actual
executor sets, establish conformance, inspect a model/tokenizer/task, train or
load an adapter, spend model tokens, use a GPU, create a seal, or support a
scientific claim. The two replay implementations still share the same written
specification and constants, so equality is evidence against isolated coding
errors, not proof against correlated semantic error. Vendored sources are
proposal preimages, not replacements for authoritative registries. Any byte
change after the anchor hashes above requires a new audit.
