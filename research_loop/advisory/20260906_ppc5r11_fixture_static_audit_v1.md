# PPC5r11 repaired fixture proposal: fresh independent static audit v1

Date: 2026-09-06

Decision: **BLOCK**

Scope: read-only audit of
`research_loop/changes/chg_20260906_public_pathway_consolidation_v5r11/fixture_specs/`
only. This advisory was written outside the proposal namespace. It grants no
architecture ratification, fixture materialization or execution, model,
tokenizer, trainer, adapter, GPU, seal, claim, or release authority.

## Executive finding

PPC5r11 genuinely repairs most of the v5r10 defects. Every advertised file
hash reproduced, all proposal validators returned the advertised values, DREAM
now derives rendered equality from bound bytes, replay A and B have distinct
self-contained source, final T14 carrier checks reject forged/failed/stale
rows, semantic release detection works, quarantine catches exact renamed and
nested legacy copies, and the machine author reproduces byte-identically.

The proposal is nevertheless not closed. The advertised "complete" T14 replay
accepts only 16 semantic relation rows from 24 required predecessor carriers.
Eight current-artifact payloads are ignored by both replay implementations;
schema-valid, canonically re-encoded, fully rehashed changes to any of them
leave both replay relations unchanged and terminal T14 status `PASS`. The T07
dispatch carrier is nominally replayed but its only payload field is also
ignored: changing `dispatch_scope` from `ALL_REGISTERED_ROWS` to
`FORGED_VENDOR` likewise passes. Finally, authoring and validation are not
closed over the advertised local v5r11 context: they read 15 live source files
from v5r9, while the machine validator also reads the old reducer-law file that
the vendored RFC calls provenance-only.

These are proposal-integrity blockers, not runtime results. Repair in a new
namespace and obtain another fresh audit; do not materialize or execute v5r11.

## Frozen bytes and advertised-hash verification

The reviewed handoff SHA-256 is
`2b447fcec1dac8fe469d6c55b44677395013cdd9d1b351b52bde8e73a351b9a8`.
The context RFC SHA-256 is
`36ad85aa20cf7d52105d572534a2a31e1303a8a406a5ec18abe302bdc6f3ee11`.

Every stable hash advertised in `HANDOFF.md` matched the on-disk file:

| File | Verified SHA-256 |
|---|---|
| `README.md` | `8de411412511bbafa418c852e0e70163f8231a9279f0d3c8cd0413a50c0cc24e` |
| `VECTOR_FIXTURE_RFC.json` | `371c95f84833e0cb37c73616c27e26b22be3f790ce10deb7f6781366898902ae` |
| `REDUCER_INPUT_ROWS_RFC.json` | `b758974f153382b83350f4ae748ad9f4196e5406137002c8592fb953a83f5e62` |
| `REDUCER_PROGRAMS_RFC.json` | `6a931bd7df4090494c65e50e79b9bc15247f701d463a74881d1b2c36c259e62b` |
| `REDUCER_SOURCE_SNAPSHOTS.json` | `830f02cfc60f3a70244f07bbd7fc0c5efe926f7266fae947690e4e7e7010a884` |
| `REDUCER_EXACT_SOURCE_BINDINGS_RFC.json` | `174b7e913d5164e5d9a04d091df762ae750b792dac364c2f8c2e137ebcefd91e` |
| `REDUCER_LAW_BINDINGS_RFC.json` | `619dead63484b961c346e3d797905605ad5619be3957743d21c7425b7ecc3ee7` |
| `REDUCER_MACHINE_RFC.json` | `b13d5a553d14ddad0c6e0279902d173690cb4c19b9841026aed64d4ead65a8c9` |
| `QUARANTINE_RFC.json` | `e7b6662ad9790cc7b958cebee368cdff65bc4d275b2cbfb9b71a18b9dca7b713` |
| `PROPOSAL_CONTEXT_RFC.json` | `36ad85aa20cf7d52105d572534a2a31e1303a8a406a5ec18abe302bdc6f3ee11` |
| `author_vector_fixture_specs.py` | `8bedb34780464c84005ccd7245b0cb56af78dbcc0866ef68603f2d2b32f60445` |
| `author_machine_rfc.py` | `049c23fe66aeae6f712b2e047c4599f184b2209286c90df0def81922436721ad` |
| `validate_reducer_semantics.py` | `ed7a8cbd324a291200aabcc8cfb419f83ba719aac929d01fbd45e3a85bf4e469` |
| `validate_machine_rfc.py` | `006ee2521dd3f99bb12dbdb31e8a20e6bce9daa0e3609d6eb0b5882dd41a6521` |
| `validate_quarantine.py` | `e1dd65397d0fe80fa30366978d61dbc5f7a532b54cab92da2c7c33112fe35bbb` |
| `t14_replay_a.py` | `bd1be672c9a0557f42010bf4c3ae1c9ba50a8f1b100fa072ebeee57b92fbaa15` |
| `t14_replay_b.py` | `a2705bda1457975d5fd0a68eacb023dc2c0dd7aeccdecebbd9458b389b41cd3b` |

The namespace still contained exactly the original 18 files after audit and
no `__pycache__`; the audit did not edit it.

## Independent validator reproduction

All executions used `PYTHONDONTWRITEBYTECODE=1` and proposal-only scripts:

- vector author: `P=465`, `N=2467`, `Q=55`, logical `2987`, planned
  executions `5974`, RFC hash
  `371c95f84833e0cb37c73616c27e26b22be3f790ce10deb7f6781366898902ae`;
- machine author stdout SHA-256:
  `b13d5a553d14ddad0c6e0279902d173690cb4c19b9841026aed64d4ead65a8c9`,
  byte-identical to `REDUCER_MACHINE_RFC.json`;
- semantic validator: `PASS`, 58 laws, 1,113 input rows, 19 source
  snapshots, input-graph manifest
  `67973bd4bc477b66ebcc4a9abb380f5d47354b366657c8b2e15208793f24ef7c`,
  semantic output
  `c69e083ea1e51bc128396b4033ce54405ae764791c486832c280422528449b0a`;
- machine validator: `PASS`, 58 laws, 1,113 rows, machine hash
  `b13d5a553d14ddad0c6e0279902d173690cb4c19b9841026aed64d4ead65a8c9`;
- quarantine validator: `PASS`, four excluded identities, 16 local context
  files, two rename/nesting probes, replacement count 2,987;
- independent AST parsing: all seven Python files parse.

These internal passes are reproduced facts, not closure evidence: the negative
mutations below expose missing semantic coverage.

## Positive repaired areas

### DREAM byte/hash binding: PASS

`T04_DREAM_REDUCER_V1` has no `rendered_matches` or input/output ordinal in its
executor input. Both rendered and reference bytes and SHA-256 values are
present. An independently selected installed row gave:

- adding the old answer-selecting `rendered_matches` field: closed-schema
  rejection;
- changing rendered bytes without its hash: `INVALID/DREAM_INPUT_BINDING`;
- recomputing the rendered hash while leaving unequal reference bytes:
  `INVALID/CONTEXT_RENDER`;
- changing both byte strings to equal new bytes with both hashes recomputed:
  `INSTALLED/null`.

This is the intended derivation: equality follows from bound bytes rather than
an executor-visible answer bit.

### Replay implementation separation: PASS, with coverage blocker below

Replay A and B have distinct raw hashes and each imports only Python standard
library modules (`__future__`, `fractions`, `hashlib`, `json`). Neither imports
the other, the validator, or a semantic callback. A one-sided in-memory defect
in A's provider-audit result produced
`FAIL/REPLAY_AGREEMENT` while B stayed unchanged. Thus source separation is
real. It does not cure both implementations omitting the same roles/fields.

### Final six carriers: PASS

All six concrete fixture-local final carriers are decoded, self-hash checked,
and compared to exact role/type/ordinal/run/cardinality/origin/status/content.
Independent sweeps over every carrier showed:

- recomputed `origin=FORGED`: all six `FAIL/SINGLE_FINAL_T14_EDGE`;
- recomputed `status=FAIL`: all six `FAIL/SINGLE_FINAL_T14_EDGE`;
- `status=FAIL` with stale self-hash but recomputed outer source hash: all six
  `FAIL/SINGLE_FINAL_T14_EDGE`.

The two replay outputs, two execution manifests, set-equality carrier, and
fixture-spec carrier are actually consumed by `t14_final_status`.

### Semantic release exclusion: PASS for its declared exact-token semantics

Recursive typed values `RELEASE_BYTES`, `RELEASED`, `CLAIM_RELEASE`,
`CLAIM_RELEASE_PACKAGE`, `EXPORT_PACKAGE`, and `AUDIT_PACKAGE` are rejected
case-insensitively, including a forbidden `artifact_type`. An ordinary key
named `release_bytes` with benign value is inert. The registered predecessor
mutation `context_policy=RELEASE_BYTES` yields
`FAIL/RELEASE_BYTES_FORBIDDEN`. A prose substring such as
`"do not release_bytes here"` is intentionally not interpreted as a typed
release value.

### Quarantine: PASS for exact copied bytes

All four legacy identities resolve to the advertised v5r9 bytes. The validator
finds exact excluded file hashes recursively, independent of basename and
nesting. A separate temporary test copied all four byte strings under four
unrelated names at depths zero through three; all four were detected. JSON
fields whose key ends in `sha256` are also scanned recursively for excluded
identity hashes.

Limitation: this is exact-file-hash quarantine, not substring, archive,
encoding, symlink-target, or arbitrary-key data-loss prevention. A legacy hash
stored under a generic key such as `digest` is not detected. That limitation is
acceptable only while the proposal continues to make the narrow exact-copy
and source-identity claim stated in its validator.

## Blocking findings

### B1 — T14 claims 24-role replay but both relations contain only 16 roles

`decode_t14_artifacts` correctly requires 24 ordered, canonical, same-run
carriers. The actual replay relations each contain only 16 rows. Both
`ROLE_KIND` tables omit these eight required predecessors:

1. `REVIEW_RECEIPT`
2. `ADVOCATE_RECEIPT`
3. `COMPLETE_RUN_MANIFEST`
4. `ANALYSIS_BUNDLE`
5. `D1A_CONTROL_SET_MANIFEST`
6. `COMPLETE_MODEL_VIEW_MANIFEST`
7. `ROUTE_LINEAGE_AUDIT`
8. `PROVIDER_AUDIT`

Their input schema permits exactly `payload:{"present":boolean}`. For each of
the eight roles independently, the audit changed `present:true` to
`present:false`, canonically re-encoded the artifact, recomputed its SHA-256,
rederived the T14 parameter carriers, and reran the reducer. Every mutation:

- changed `predecessor_vector_sha256`;
- left both replay relation hashes unchanged;
- returned `t14_status=PASS` and `first_failure=null`.

The vector hash therefore records that bytes changed but is not consumed by
the final decision. Requiring carrier presence while ignoring its current
semantic state is not full predecessor replay. Two implementations agreeing
on the same omission does not establish completeness.

Required repair: both source-distinct replays must emit and independently
derive a relation row for all 24 required roles, with each registered payload
field used in the role's semantic decision. Add a schema-valid, canonically
rehashed per-role/per-field mutation grid and require the appropriate relation
or failure to change. The final status must bind the complete 24-row semantic
relation, not merely return the predecessor byte hash as an unused output.

### B2 — T07 dispatch provenance ignores its bound current-artifact payload

The T14 `PPC5R9_T07_RESULT` carrier has exactly one payload field:
`dispatch_scope`, whose registered value is `ALL_REGISTERED_ROWS`. Both replay
implementations label this role `dispatch_binding`, but compute only the count
and canonical hash of the separately supplied `DISPATCH` source. They never
read `f["dispatch_scope"]`.

The audit changed this field to the schema-valid string `FORGED_VENDOR`,
canonically re-encoded and rehashed the predecessor, rederived parameters, and
reran T14. The predecessor-vector hash changed; both replay relation hashes
were unchanged; terminal status remained `PASS/null`.

This breaks the claimed binding between the current T07 receipt and the
vendored dispatch registry. Required repair: the replay must validate and bind
the carrier's exact declared scope and the complete source identity/content,
and a scope/vendor mutation must fail or alter the relation. Register negative
cases for valid-but-wrong scope, source identity, row count/order, role,
consumer stages, and content hash.

### B3 — the advertised local source/context closure still depends on v5r9

The reducer-law precedence and source-binding rows are now genuinely vendored
in v5r11, and `author_machine_rfc.py` reads that local table. However, the
complete author/validator path is not locally closed:

- `REDUCER_SOURCE_SNAPSHOTS.json` declares
  `research_loop/changes/chg_20260905_public_pathway_consolidation_v5r9` as its
  live source root;
- `validate_reducer_semantics.py` sets the same v5r9 `ROOT` and reads 19
  snapshots across 15 external files;
- `validate_machine_rfc.py` sets the same `SOURCE_ROOT`, rereads all 110 exact
  pointer bindings, and separately opens the old v5r9
  `fixture_specs/REDUCER_LAW_RFC.json` to check its provenance hash;
- none of those 15 upstream source files appears in the 16-entry local
  `PROPOSAL_CONTEXT_RFC.json` context list;
- no v5r10 source is read, but v5r9 availability is required for authoring and
  validation.

Pointer-value hashes detect drift when those legacy files are available, but
hashes alone are not source preimages and cannot reproduce the machine if the
files disappear. The statement in `REDUCER_LAW_BINDINGS_RFC.json` that
"PPC5r11 reproduction reads only this vendored closed table" is true for law
selection inside the author, but not for the full advertised reproduction and
validation process.

Required repair: either vendor the exact canonical values for all 19 source
snapshots plus the provenance record into the new namespace, or explicitly
include every upstream source file with raw SHA-256 in the frozen proposal
context and narrow the local-closure claim. If the old reducer-law file is
provenance-only, validation should consume a frozen provenance record rather
than require the live old file. Add a test that copies only the complete new
namespace to an isolated root and reproduces every advertised author and
validator output without v5r9/v5r10 access.

## Disposition and limitations

The positive repairs should be preserved unchanged in a new namespace. The
smallest acceptable successor closes B1--B3 and adds the exact mutation and
isolated-copy tests above. A new static audit must begin from its new handoff
and verify all hashes afresh.

This audit did not materialize the 2,987-case universe, perform either planned
executor run, establish executor-set equality or conformance, inspect a model
or tokenizer, run a benchmark, train an adapter, use a GPU, create a seal, or
support a scientific claim. Internal proposal validators and this advisory
cannot authorize any of those actions.
