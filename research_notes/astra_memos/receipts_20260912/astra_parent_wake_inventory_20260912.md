# P0 raw wake material — preliminary CPU inventory

2026-09-12. Status: **PRELIMINARY_CAPSULE_CPU_INVENTORY_NOT_EXPORT_VALIDATION**.

Exporter is implemented and frozen. This additional inspection changed no source/test files, emitted no training corpus, ran no models, and made no remote/GPU/Git calls. It does not select main's next comparison or interpret pending seed-replication outcomes.

## Available capsule and checks

Read `/tmp/astra_P0_material_terminal_capsule_20260912/node3/astra_diagnostics/astra_P0_material_6101_20260912_attempt1/{lesson,sham}`.

Recomputed every listed artifact digest: **zero mismatches in either arm**. Checked actual request/output text hashes, uniquely joined all wake thoughts through prompt/output hash and seed, checked ordered raw ACT lists against associated ledger events, and used existing `facts_from_act` for measured feedback. Used existing exporter prompt-envelope removal and replay normalized teacher-sentence checks without any NOTE/first-person content judge. This is an inventory, not all checks of `source_arm` or token preflight.

| Source inventory | Lesson | Sham |
|---|---:|---:|
| Uniquely joined raw wake chunks | 1024 | 1024 |
| ACT rows | 1913 | 1632 |
| Measured events | 1903 | 1627 |
| Clipped ledger chunks recoverable from full stored generation | 0 | 1 |
| Raw target chunks containing normalized teacher echoes | 10 | 0 |

## Candidate counts before actual tokenizer preflight

Applied the exporter's two available **explicit** selection rules independently for inventory: first qualifying wake per episode, no fallback to a later wake if the first is excluded; then shared eligible episode IDs. This does not approve either comparison.

| Rule | Lesson eligible | Sham eligible | Shared paired episodes |
|---|---:|---:|---:|
| `measured` | 63 | 64 | **63** |
| `accepted` (at least one stored measured score1 in chunk) | 10 | 7 | **6** |

For `measured`, all 64 episodes have a qualifying event in each arm; one lesson first-qualifying chunk is excluded for teacher-target echo. Other teacher-echo chunks are not the first qualifying candidates. Shared eligible counts by family: countdown 10; mini_sudoku 9; futoshiki 8; knights_knaves 9; arc_1d 9; sokoban 9; kakurasu 9.

For `accepted`, 54 lesson and 57 sham episodes have no qualifying accepted event. There are no teacher exclusions among the first accepted candidates in this inspection. The six shared candidates, in original schedule order, are:

1. `rg/knights_knaves/1323938`
2. `rg/knights_knaves/1183480`
3. `rg/knights_knaves/1675862`
4. `rg/mini_sudoku/1271272`
5. `rg/knights_knaves/1202953`
6. `rg/knights_knaves/1537774`

Thus **32 paired accepted source episodes are unavailable even before token checks**. Accepted mini-sudoku yields exactly one common episode, `rg/mini_sudoku/1271272`; repeated successful ACTs do not supply distinct source episodes. A request for more than one accepted mini-sudoku example must remain a shortage, not be padded. Episode counts are not a new independent board-identity validation.

Measured-event material is numerically much larger, but measured does not mean successful/useful. Even `accepted` preserves the full raw chunk, potentially including other failed actions or unsupported child prose. No whole-target truth certification is implied.

## Outstanding local availability / token checks

The original recorded roots are `/localhome/local-rohing/astra_diagnostics/astra_P0_material_6101_20260912_attempt1/{lesson,sham}`. Neither original root, the recorded model directory, nor the four original producer files under `/localhome/local-rohing/astra_sources/911e08877bac83613a62ca58bdb032f22cc61681/` is available on this local machine. The files are the batch loop, formation producer, preschool reasoning policy, and reasoning-gym families JSON. Their remote existence has NOT been checked in this task.

Therefore the strict exporter was not run against the relocated capsule and no missing-path bypass was added. Actual export needs the existing original paths/model/source bytes on main's node and the local tokenizer. The inventory is still useful: source success-count shortages do not require a fit or tokenizer to establish.

Recorded historical original prompt lengths range 937–5695 tokens (lesson) and 892–5785 (sham), across all wakes. These are retained historical counts, **not** measured cleaned-context-plus-target lengths or selected-example sizing. Tokenizer/render consistency, zero truncation, full-target labels and final paired availability under the chosen cap remain untested on real material; the 63/6 counts are upper bounds before those checks.

## Freeze / validation status

- Exporter SHA256 remains `b24b90766f43be7ecdb7ba1a3d20754103fa970ad1c9ccd8f5bffd092b5a6d4f`.
- Test SHA256 remains `6d082f4327235dfeef1b07f7fe96d95811b703907d5094f9a55cfff031f1034b`.
- Prior completed CPU tests: 17 exporter + 13 formation + 12 replay passed; V3 trainer test script exited0 with three disclosed dependency skips.
- Full invocation/artifact/test handoff: `/tmp/astra_parent_wake_material_20260912.md`.

No further source edits planned. No fit-ready real child corpus or scientific promotion claimed.
