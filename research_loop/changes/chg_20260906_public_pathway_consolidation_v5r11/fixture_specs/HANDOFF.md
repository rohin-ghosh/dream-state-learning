# PPC5r11 fixture proposal repair handoff

Date: 2026-09-06  
Scope: proposal bytes and proposal-source validators only. This handoff grants
no architecture ratification, fixture materialization or execution, model or
GPU authority, conformance result, seal, scientific claim, or release authority.

## Outcome

PPC5r11 is a new namespace; no PPC5r9 or PPC5r10 byte was overwritten. No
materialized PPC5r11 fixture universe exists. The proposal retains the
2,987-case content-addressed vector and closes 58 T04--T14 reducer laws over
1,113 exact input rows with generated closed input/parameter/output schemas.
Executor graphs contain only concrete input facts and source companions;
expected outputs remain post-execution oracle material.

Repairs for the v5r10 independent-audit blockers:

1. DREAM no longer consumes `rendered_matches`. Each row binds actual rendered
   and reference bytes and SHA-256 values. The reducer recomputes both hashes,
   then derives equality. Adversarial checks reject the old boolean, stale
   byte/hash pairs, and correctly bound unequal renders.
2. T14 replay A and replay B are separate, self-contained implementations.
   Each module owns its traversal and complete value semantics; neither takes a
   callback or imports the other. Their distinct source bytes and semantic
   hashes are executor inputs. Injecting a defect into A alone produces
   `REPLAY_AGREEMENT` against unchanged B.
3. The final T14 gate consumes six canonical fixture-local carrier objects.
   Every carrier binds contract/version/lifecycle, type, role, ordinal,
   cardinality, run, origin, status, typed content, and a self-hash. The final
   reducer checks both replay relations, both execution-manifest carriers, the
   set-equality carrier, and the fixture-spec carrier. Recomputed `FORGED`
   origin, failed status, and stale-self-hash probes all fail.
4. Release exclusion traverses typed values and artifact types. A predecessor
   whose existing `context_policy` value becomes `RELEASE_BYTES` fails with
   `RELEASE_BYTES_FORBIDDEN`; merely spelling `release_bytes` as an ordinary
   dictionary key cannot select the answer.
5. Machine reproduction no longer reads the PPC5r9 reducer-law file. The 58
   needed precedence/source-binding rows are vendored in
   `REDUCER_LAW_BINDINGS_RFC.json`; the old file's exact SHA-256 is retained and
   checked only as provenance. The local vendored catalog is present in both
   machine and context source ancestry. The machine validator reruns the author
   and requires byte identity.
6. Quarantine is enforced by SHA-256 over every file recursively, independent
   of basename or nesting. JSON source identities are also scanned for excluded
   hashes. Temporary renamed and nested copies of excluded bytes are detected
   by adversarial probes.

The T13 package/Kahn and T08 paired-world repairs inherited from v5r10 remain
intact: T13 derives current package and authority relations from bound source
facts, and T08 derives outputs from upstream pairs without perturbation labels
or downstream answers in its input.

## Exact proposal counts and semantic hashes

- P = 465
- N = 2,467
- Q = 55
- logical proposal cases = 2,987
- planned independent executions = 5,974 (not executed)
- reducer laws = 58
- expanded reducer input rows = 1,113
- upstream source snapshots = 19
- exact upstream pointer bindings = 110
- input graph manifest SHA-256 = `67973bd4bc477b66ebcc4a9abb380f5d47354b366657c8b2e15208793f24ef7c`
- semantic output SHA-256 = `c69e083ea1e51bc128396b4033ce54405ae764791c486832c280422528449b0a`
- T14 canonical replay relation SHA-256 = `e5bebd323e4f236b84c07b2a7dc16b774a7544457183e8a881e9eb6cb38a1d74`

## Stable proposal file hashes

| File | SHA-256 |
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

## Validator results

- `author_vector_fixture_specs.py`: exact P/N/Q/logical/planned counts above.
- `author_machine_rfc.py`: byte-identical reproduction of
  `REDUCER_MACHINE_RFC.json`.
- `validate_reducer_semantics.py`: PASS, 58 laws / 1,113 rows, graph and
  semantic hashes above, including all named adversarial probes.
- `validate_machine_rfc.py`: PASS; machine SHA-256
  `b13d5a553d14ddad0c6e0279902d173690cb4c19b9841026aed64d4ead65a8c9`.
- `validate_quarantine.py`: PASS; four excluded identities, 16 bound context
  files, two renamed/nested adversarial probes.
- all Python proposal sources compile.

## Remaining gates

- A fresh independent static audit is required. Internal PASS is not proposal
  closure and creates no authority.
- The 2,987-case vector remains intentionally unmaterialized and unexecuted;
  no executor-set equality, conformance receipt, runtime result, seal, or claim
  exists.
- No generator, schema, registry, or existing normative document was changed.
