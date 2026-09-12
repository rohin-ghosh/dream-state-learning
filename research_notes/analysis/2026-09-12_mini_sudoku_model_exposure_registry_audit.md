# Mini-Sudoku model-exposure registry audit

Date: 2026-09-12  
Cut: the fresh-behavior protocol selection at `2026-09-12T16:40:00Z`, bound
eight minutes later by commit
`7277a520a4129cf6d9ec5cfc9aaec4a16435b214` (`2026-09-12T16:48:19Z`).  
Scope: committed evidence reachable immediately before that cut. This audit
read no attempt-2 scientific outcomes, invoked no model or tokenizer, used no
GPU, and changed no builder source or job.

## Bottom line

The authoritative pre-cut **model-exposure exclusion union contains 153 exact
`rg/mini_sudoku` episode IDs**.

- **137 IDs have committed evidence of actual model generation**: the puzzle
  was supplied to a child, parent, base, or adapter-backed inference call.
- The remaining **16 IDs (`1850016..1850031`) have committed LoRA-fit exposure
  only**. They must still be excluded: their puzzle/action pairs were training
  inputs or targets even though no committed generation is evidenced for those
  16.
- A separate **75 IDs were CPU-inspected only** in the bounded evidence. They
  were put in the earlier “historical exposure” registry, but the originating
  receipt explicitly says `prior_qwen_outcomes=false`; their presence is not
  evidence that a model saw them.
- A further **8 IDs occur only as configuration or prior-registry metadata**.
  No committed generation or fit record was found for them.

The defect that contaminated fresh-behavior attempt 2 is therefore exact and
not ambiguous: **`rg/mini_sudoku/1900070` through
`rg/mini_sudoku/1900075` were already model-generated before the cut**. The
committed correction-utility analysis contains their OFF/ON wake records.

## Authoritative exact union

Ranges below are inclusive. The sets are disjoint as written.

| Exposure event | Exact episode IDs | Count | Exposure class |
|---|---:|---:|---|
| P0 lesson/sham lived schedules | `1001696`, `1060428`, `1062212`, `1104374`, `1189872`, `1271272`, `1733970`, `1822954`, `1868637` | 9 | generation |
| External-oracle useful/corrupt material | `1850000..1850031` | 32 | LoRA fit; `1850000..1850015` also generation |
| Fresh parent-correction capture | `1850100..1850131` | 32 | child/parent generation; later fit reuse also occurred |
| Initial process/format constraint diagnostic | `1851000..1851007` | 8 | generation |
| Seeded process/format constraint diagnostic | `1851100..1851107` | 8 | generation |
| Worked-demonstration source cases | `1851200..1851207` | 8 | generation |
| Worked-demonstration transfer cases | `1851300..1851307` | 8 | generation; selected cases later reused by citation-sleep fit/probe |
| Correction-utility recipient panel | `1900000`, `1900001`, `1900003..1900019`, `1900043..1900049`, `1900070..1900075` | 32 | OFF/ON generation across recipient fits |
| Useful/corrupt behavior canary panel | `1900050..1900065` | 16 | OFF/ON generation across optimizer seeds |
| **Union** | all rows above | **153** | mandatory model-exposure exclusion |

The generation-bearing subset is the same table except that
`1850016..1850031` is removed, giving **137**. The model-exposed union retains
those 16 because training exposure is fatal to a fresh evaluation even when an
inference transcript is absent.

## Why each row is model exposure

The test was not “does an ID string occur in a file?” It was whether committed
custody connects the ID to a completed generation or fit:

1. The P0 split capsule contains identical lesson/sham schedules (inner
   schedule SHA-256
   `8c8b061cbeb30e34679e0bb1843607cb41cbb9e043684d3dc859e1fd804137cf`)
   containing the nine Mini-Sudoku IDs. Both results are `COMPLETE`; lesson
   records 2,937 generation requests and sham records 2,656. Raw-wake and
   raw-fork receipts corroborate
   subsets; the schedule, not those smaller exports, supplies the complete
   nine-ID set.
2. The Mini-Sudoku useful/corrupt terminal binds 32 training items and 16
   canary items. Completed fits consumed all 32 training prompt/target pairs;
   completed OFF/ON probes generated on all 16 canaries. Seed-1/2 terminal
   replication repeats the same identities.
3. Parent-correction native replay contains generation metadata and output
   hashes for all 32 IDs `1850100..1850131` in both process/sham capture.
4. Constraint terminal results contain eight output SHA-256 records per arm;
   their preparation configs map `c01..c08` to `1851000..1851007`. The v2
   terminal repeats the same structure under seeds 7101/7102/7103 for
   `1851100..1851107`.
5. Demonstration terminal results contain 16 output captures per arm, ordered
   source/transfer; its preparation config binds source IDs `1851200..1851207`
   and transfer IDs `1851300..1851307`.
6. Correction-utility terminal raw pair records and the committed analysis
   bind actual OFF/ON output hashes to exactly the 32 recipient IDs in the
   table. This is the direct evidence for `1900070..1900075`.

## Evidence files and hashes

All terminal artifacts in this table were committed before the protocol cut.
An archive hash authenticates its inner configs, results, raw generations,
fit receipts, and manifests together.

| Committed evidence | SHA-256 | Binding commit | Coverage |
|---|---|---|---|
| `research_notes/astra_memos/receipts_20260912/astra_P0_material_terminal_20260912.tgz.part00` | `88ca268c1f2912319f3c6f31c7e4e522a3433d07adb30bcd13c8524f6f01c4d8` | `983733389794fe957adc4a1246c0773c93819971` | first transport part of P0 generation capsule |
| `research_notes/astra_memos/receipts_20260912/astra_P0_material_terminal_20260912.tgz.part01` | `54c514597e29c209843d1c4ddfaf054c264e8eb4d71589a61301156eef753a26` | `983733389794fe957adc4a1246c0773c93819971` | second transport part; ordered reconstruction SHA-256 `13ca1bcefa98d2c4336197f46093abe807f141b937aa5d3d78876ac58122c208` |
| `research_notes/astra_memos/receipts_20260912/astra_mini_sudoku_terminal_20260912.tgz` | `cfe1ca3f319c82a6e118a42449ae24607c8db8270961bc7ca76af9db4d55e16e` | `0ef7ddca446122b65d6ca5492e1e98310314ceef` | 32 fit IDs; 16 generation canaries |
| `research_notes/astra_memos/receipts_20260912/astra_behavior_replications_terminal_20260912.tgz` | `e45c272e3781583f3ac1bae80d600ac35449b68e183b3b499d6b34d182ddd39b` | `9f6586116aa2bf5480c12b63becdaaeb98e0c020` | repeated fits/probes, optimizer seeds 1/2 |
| `research_notes/astra_memos/receipts_20260912/astra_static_competency_terminal_20260912.tgz` | `339620c7ad406d3d155b6007a8bf82c4415c7e3bcf3702159285143ab6efbaeb` | `d7e011ff81a15c350604fbe162e386b97892e592` | generation corroboration for `1850000..1850015` |
| `research_notes/astra_memos/receipts_20260912/astra_no_teacher_terminal_20260912.tgz` | `9574db1e566685923fbeee0d0900e0975a8a2569325fc50079f8143742fdbc95` | `d277670024c756ad53b2a83100164d90295be444` | generation corroboration for `1850000..1850015` |
| `research_notes/astra_memos/receipts_20260912/astra_parent_correction_terminal_20260912.tgz` | `bd4f7c5d035f423f27c262efbb17cc90bcab57cb30a45d894f7b3c98db65dd5b` | `b006eaabbabf9fe62da4e2e79b411dc8d497715d` | `1850100..1850131` generation |
| `research_notes/astra_memos/receipts_20260912/astra_parent_correction_native_replay_20260912.jsonl` | `711cc079da813c8e2631c8d7ebba90ef287ae54ffc453632bfac9025160af390` | committed before cut | projected generation records for same 32 IDs |
| `research_notes/astra_memos/receipts_20260912/astra_correction_utility_terminal_20260912.tgz` | `dfbb71fb9ea07bbff5dc990ca5c2028796d173bc0c51520b2f45c53cad87e3a4` | `4c73685b5200bcfde8e189f2e0e8ad15b5690122` | 32-ID recipient panel raw OFF/ON records |
| `research_notes/astra_memos/receipts_20260912/astra_correction_utility_analysis_20260912_main.json` | `29b6cf3ca3de9b4d9f6fe643fc769dbaed3a3cbc710d6e69bb1f6e53ec8dd7b0` | `e4013594c4e455ed1cc11129098b064e57450057` | committed analysis including actual `1900070..1900075` outputs |
| `research_notes/astra_memos/receipts_20260912/astra_constraint_verified_terminal_20260912.tgz` | `7935c254ac16cfbf33c8cbf9386e9a947ec9b02e50d28e9f03987efb3bbbda89` | `05d79df84c8ecc2e45f9edddb950543cbb75ff53` | `1851000..1851007` generation |
| `research_notes/astra_memos/receipts_20260912/astra_constraint_v2_terminal_20260912.tgz` | `476788fb5204ab45dfcc22644382f1519493ce6224ccbce8298616c0d1073692` | `e4ecbf86f10517cc3c5fb8bcea67bfc0be6ffb1e` | `1851100..1851107` generation under three seeds |
| `research_notes/astra_memos/receipts_20260912/astra_demonstration_terminal_20260912.tgz` | `b2d03d6b41c7211ac0c87ff177e590badb137cb2a9624abca4bc5749ac1d1417` | `e34074a03d1262ad2e620886f42ba035b3cc992c` | `1851200..1851207` and `1851300..1851307` generation |
| `research_notes/astra_memos/receipts_20260912/astra_citation_sleep_terminal_20260912.tgz` | `c33d6001a12ddd0c737af8bebe7d43384aba84a21c5f101c6d5ecd10b1ba1192` | `88185ddc20683dfd2935dc8f132f96075047c901` | later fit/probe reuse of demonstration cases; no new IDs |
| `research_notes/astra_memos/receipts_20260912/astra_rawfork_terminal/capsule.tgz` | `3508c27cf9832f25c059d96b990ff285cf6011bad2714aa8e2d175ad8a368fd6` | `acd71d6b73c3203e957b26d97900ecdd45474351` | corroborates P0/canary generation; no new IDs |

The protocol itself is SHA-256
`d2f2f552a413965dd4968332279f6fedc6ffad0102d65dee2ad89d926d4f2c4b`.
The old mixed registry
`astra_constraint_prior_ids_20260912.json` is SHA-256
`a93b5d4a1d1ad365f116ec688979c38b1c1481bbcc21f18df09d2832df481097`
and contains 204 IDs, but must not be described as a model-exposure registry.

## CPU-only and metadata-only IDs

### CPU-inspected, without committed model exposure: 75

These ranges are inclusive and disjoint from the 153-ID model-exposure union:

- `1001000..1001031` (32)
- `1002000..1002015` (16)
- `1900020..1900042` (23)
- `1900066..1900069` (4)

Their source is the material builder's `CPU_EXAMINED_IDS`. The material
`ids.json` (inner SHA-256
`6468cb882e64145c0529b7765df2956c3e04426060f4243d447f4d5abf3b76a2`)
labels the source “Popper handoff 2026-09-12, CPU native validation only” and
sets `prior_qwen_outcomes` to false. The earlier audit correctly says this was
a conservative declared-historical list, **not proof of specific model
consumption**.

This is a bounded negative: no generation/fit receipt was found in committed
evidence. It is not proof that no inaccessible, uncommitted, or deleted run
ever used these IDs.

### Configuration/registry only, without committed model exposure: 8

- `10001`
- `1000000..1000003`
- `1000999`
- `1100000`
- `1900002`

The first seven occur only in inherited prior-ID objects. `1900002` is the
configured Mini-Sudoku canary and appears as
`selection_used_episode_ids` in the P0 pipeline. The implementation uses that
field as a selection-disjointness receipt; the completed P0 probe episode IDs
were N-Queens/Tower-of-Hanoi, and no committed Mini-Sudoku output or fit row was
found for `1900002`. It is therefore metadata-only in this bounded audit, not
proven model exposure. Because it is a standing canary with unaudited earlier
history, it should remain in the conservative do-not-select projection.

`1900099` is merely the inclusive upper bound of the later candidate range. It
is neither pre-cut model exposure nor a prior exclusion.

## Audit coverage and ambiguity boundary

I searched every textual `rg/mini_sudoku/<integer>` occurrence in the parent
of `7277a520`, decompressed all 57 committed `.tgz`/`.tar.gz` files under the
2026-09-12 receipt tree, and decompressed the two-part P0 capsule. All 237
distinct IDs named anywhere before the cut reduce exactly to:

- 153 verified model-exposed;
- 75 CPU-inspected only;
- 8 metadata-only; and
- 1 candidate-range upper bound (`1900099`).

Compressed archives commonly embed a full prior-ID registry beside real
outputs. Mere archive-string presence was never promoted to exposure: an ID
entered the 153 only through a completed generation record, a completed fit
corpus/receipt, or a completed schedule whose result records generation
requests.

The conclusion is authoritative only for committed evidence. The old material
receipt itself calls historical exposure “not audited”; inaccessible node
state and uncommitted/deleted experiments cannot be reconstructed from this
checkout. That uncertainty argues for keeping the conservative projection,
not for mislabeling CPU inspection as model exposure.

## Minimal immutable registry for a repaired panel

Use two hash-bound artifacts, because one list cannot remain semantically
honest and satisfy the current selector interface at the same time.

### 1. Authoritative ledger object

Canonical RFC 8785/JCS JSON plus exactly one LF:

```json
{
  "schema": "rg-mini-sudoku-model-exposure-v1",
  "cutoff_utc": "2026-09-12T16:40:00Z",
  "cutoff_binding_commit": "7277a520a4129cf6d9ec5cfc9aaec4a16435b214",
  "verified_model_exposed_episode_ids": ["153 exact sorted unique IDs"],
  "verified_generation_episode_ids": ["137 exact sorted unique IDs"],
  "verified_training_only_episode_ids": ["rg/mini_sudoku/1850016", "...", "rg/mini_sudoku/1850031"],
  "cpu_examined_only_episode_ids": ["75 exact sorted unique IDs"],
  "metadata_only_unresolved_episode_ids": ["8 exact sorted unique IDs"],
  "evidence": [{"path": "repo-relative path", "sha256": "64 lowercase hex"}]
}
```

Runtime files must enumerate IDs individually, not encode ranges. Preparation
must verify schema, exact SHA-256, sortedness, uniqueness, namespace, and the
declared counts before generating any candidate.

### 2. Selector projection

The current helper expects a bare JSON array. Produce a derived, canonical,
read-only array named as a **selection exclusion**, not a model-exposure list:

`verified_model_exposed_episode_ids` union
`cpu_examined_only_episode_ids` union
`metadata_only_unresolved_episode_ids`.

For the pre-cut snapshot this is **236 exact IDs**. Its intersection with the
frozen `1900070..1900099` candidate range must be asserted to equal exactly
`1900070..1900075`. The selector projection's SHA-256 and the ledger object's
SHA-256 must be written into every preflight/spec/manifest. Missing registry,
hash mismatch, unexpected candidate-range intersection, or empty/default list
must fail preparation.

This two-file shape preserves the conservative selection policy without
repeating the original category error.

## Post-cut append required before any successor panel

Attempt-2 selection metadata (panel JSON SHA-256
`8e6e9c6d0e589b0509f61935d198ffe556aec3dc45dc5f5e3d7f527a1c7d5a9d`)
lists:

`1900071`, `1900072`, `1900073`, `1900075`, and `1900076..1900087`.

The first four were already in the pre-cut union. Main reports attempt 2 is
terminal; therefore **`1900076..1900087` are 12 new model exposures** for any
successor panel. I did not inspect their outputs. The current checkout contains
the committed prepared selection metadata but not a committed terminal capsule
for that execution, so the append should be bound as soon as its terminal
receipt lands. Until then, any new preparation must fail closed and exclude
all 16 selected IDs. Once appended, the model-exposure union becomes **165**,
and the candidate-range exclusion becomes `1900070..1900087`.

## Required repaired-panel assertion

Before a new model load, an independent checker should be able to establish
from bytes alone:

1. the registry cutoff/event and evidence hashes are bound;
2. all 153 pre-cut verified IDs are present;
3. all terminal attempt-2 selection IDs are appended without reading outcomes;
4. no candidate is generated or selected before registry validation;
5. selected episode IDs are disjoint from the resulting selection exclusion;
6. the exact exclusion registry digest is copied into every immutable spec and
   final receipt.

That repairs the freshness defect without changing the scientific endpoint or
using CPU-only inspection as evidence of a model outcome.
