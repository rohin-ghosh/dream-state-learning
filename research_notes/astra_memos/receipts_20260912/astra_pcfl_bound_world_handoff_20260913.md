# PCFL bound-world core — EDITSTOP, September 13, 2026

Manuscript review completed before reopening core ownership. Scope is only
`organism_v6/pcfl_vertical_dev.py`, `tests/test_pcfl_vertical_dev.py`, and this
new handoff. Old handoff and all other workers' files remain untouched.

Authority: prospective Main decision at commit `0418cb53`,
`research_notes/astra_memos/ASTRA_PCFL_PRODUCTION_WORLD_BINDING_2026-09-13.md`,
byte SHA256 `ac2013fe44c3f9bdfdca43defca0d8b19baa39209fab443b74abc128391fea91`.
This newly binds definitions; it does not assert the old documents bound them.

## API notice for preparer/runtime/qualification owners

`SLOTS`, `opaque_candidate`, `build_root`, and root/cell serialized schemas
remain unchanged. r9/r10 are now bound as private PROBE-only observations.
`WorldCell.edges` remains the nine registered potential witnessed EVENT edges.
New `WorldCell.full_transitions` adds X --q_D--> Z with no EVENT or receipt
address; both graph search and complete-route/cut execution use this full
private transition set. Rendered witnessed/formation banks continue using only
the registered edges/actual admitted spans.

`production_binding_status()` reports `WORLD_DEFINITION_BOUND`, with
`definition_bound=true` but `execution_contract_valid=false` and incomplete
tokenizer/shortcut/runtime/time gates. Its source pin becomes the explicit Main
binding; it records X/Z, existing q ports, role-neutral result wire, r9/r10
private custody, G_ private metadata and N_ route endpoints. `registries()` keeps
its top-level/world-registry key sets, replacing the prior unresolved values.
Consumers must update exact core/registry pins; this is not a release override.

`WorldSession(...,'NEW')` can execute the bound pure CPU state machine.
`probe()` returns coordinator-only `terminal` plus `public`; the ONLY
model-visible bytes are `public`. Relevant returns the specified result and
enables one EXPLORE. Distractor returns its own result and terminates; malformed
or unlisted output returns empty public bytes and terminates. No retry,
subsequent EVENT/LINK prompt, or R reveal is allowed after terminal status.
Existing `fixture_only` keywords remain accepted for caller compatibility but
never bypass these terminal rules or select a different topology.

No model/tokenizer/native/GPU/network activity; no commit. Neither full native
readiness nor all shortcut or tokenizer gates are marked complete.

## Exact final pins

SHA256 of actual file bytes:

| File | SHA256 |
| --- | --- |
| `organism_v6/pcfl_vertical_dev.py` | `ed1b8c5f1d866e8e036a33c3fbeb278551021413cb63e5b3a35bb72934dae04e` |
| `tests/test_pcfl_vertical_dev.py` | `d4e621dc766967aec7ddf959106fd8fe2a401fbf8e6529526f1d8965b636647a` |
| Main production-world binding | `ac2013fe44c3f9bdfdca43defca0d8b19baa39209fab443b74abc128391fea91` |

Deterministic canonical-object digests, not file-byte hashes:

- `digest(registries())`: `cf8dd4b26388676dc2466139f49252c39a537f7d6383b3ef0b4fb48468354825` (golden-pinned in test).
- `digest(audit_construct([build_root(f"excluded/{index}") for index in range(4)]))`: `9c6db88040dd1951ba20c83b02eeef645071e1fcb987f815915e82f7b9afde9b`.
- Unchanged excluded/0 root serialization: `823754da5823bbcef0d00852d3c1160d5e012b6e8c236eb7555acdd906d6d186`.
- Unchanged ten-view snapshot: `ca87f40f3c78ac9885a071297408d08b40b1401a31454a1c6d5af1b16b02b5bc`.

The handoff's own byte hash is reported separately after writing; no recursive
self-hash is embedded.

## Validation actually performed

Final local stdlib-only command:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_pcfl_vertical_dev.py' -q
Ran 47 tests in 1.809s — OK
```

This includes the unchanged earlier construct tests plus bound-world checks:

- Actual CPU-issued R/D PROBE results, exact public wire and private r9/r10
  custody; public wire carries neither receipt IDs nor role/root labels.
- Four excluded roots / 32 worlds / 64 delayed tasks / 192 route-cut checks,
  all using ten full private transitions. Both cuts remain fatal; latent
  X->Z enters only the dead-end detour. No alternate delayed-goal route.
- Sixteen executed result quartets: balanced binary actual result hashes,
  independent R/D outcomes; independently calculated Shannon values
  H(R)=H(D)=1 bit, I(R;route)=1 bit, I(D;route)=0 within each fixed O/goal.
- Byte-identical RA/RB pre-outcome surfaces across R/D quartets, opposite
  display ordering and balanced relevant positions. Thirty-two D-neutrality
  pairs cover targets, queries, non-WRONG_ROOT projections and private cuts.
- D terminates after its ordinary result. Missing/malformed/unlisted probes
  terminate with empty public bytes and no receipt; repeat PROBE, EXPLORE,
  EVENT/LINK prompts and admissions cannot continue a terminal lineage.
  Neither branch exposes a subsequent R result.
- Relevant PROBE enables one EXPLORE using r8, one EVENT and two LINK
  opportunities; r8 custody binds its prior r9 observation. PROBE receipts
  cannot be substituted as EVENT or LINK executed evidence.
- Latent transition has no EVENT/receipt address and is absent from witnessed
  banks, ideal rows, raw experience and materialized queries. G_ remains
  private goal metadata; rendered endpoints use N_.
- Chronological live handles remain distinct from structural edge indices:
  e5 is the Z observation and e7 the second B observation. Existing required
  bank mismatch/missing-authentic-row failures remain tested; no oracle
  substitution or post-output resealing.

Audit reports `route_construct_passed=true`, `full_construct_passed=false`,
`ready_for_model_calls=false`, and scope
`CPU_BOUND_WORLD_DEFINITION_NOT_NATIVE_READINESS`. Its 48 old receipt/atom/link
decisions and 32 successor-support checks remain included.

## Integration and limits

`require_production_bindings()` now checks the bound world definition only;
its success is NOT launch authorization. Consumers must use the separate
execution-contract/readiness gates, not treat this predicate as qualification.
`probe()`'s receipt, error, and terminal metadata are coordinator-private;
forward only `public` to a child. Stop without further model calls after D or
malformed choice. No fixed terminal message or automatic R continuation.

Preparer/runtime/qualification owners must rebind their exact source/registry
pins independently. No files in their ownership were modified. The old core
handoff is preserved unchanged; prior source remains in the existing commit.

Pending: real tokenizer-qualified inventories, complete rendered shortcut
certificate, prepared execution contract and actual inventory/time profiles,
native/runtime/custody binding, and model ceiling evidence. These CPU fixture
results are not child experience, a native assay, C11 completion, or full
campaign readiness. PCFL does not replace still-required parented, matched,
parent-removal, H1/H2 or scientific-promotion evidence.

## Earlier task completion and changed files

Manuscript review completed first, verdict ACCEPT for the exact reviewed six
versions; manuscript was not edited. Review:
`/tmp/astra_manuscript_seq161_independent_review_20260913.md`, SHA256
`f6cee0ef4c5858946022dddd7d91bf20046155e6aa77b585e458a65a3df8e1bd`.

Bound-world task changes only the two owned source/test files and this new
handoff. No commits, native operations, network access, or other worker edits.
**EDITSTOP: core and matching tests frozen at the hashes above.**
