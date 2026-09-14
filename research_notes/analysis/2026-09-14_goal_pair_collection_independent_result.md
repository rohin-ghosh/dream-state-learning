# SEQ255 independent terminal evidence review — 2026-09-14

**Disposition: recorded collection/baseline evidence passes bounded independent replay; no training or new amortization demonstrated. Ownership released after this memo.** Review performed locally, independently of the primary memo, under the applicable AGENTS/CLAUDE rules and the user's narrower read-only authorization.

## Bound evidence

Capsule root: `gpu_artifacts_local/astra_goal_pair_collection_terminal_20260914_attempt1/extracted` (paths below are relative to it unless stated otherwise).

- Sibling `terminal.tar.gz` SHA256 independently matches `e66d7d7e1dd3a01189cd454ea7ad9a53970685fcf46de30b1a6732a564585e7e`. All **6,020 regular files** match extracted bytes and exact file inventory; no duplicate file members, unsafe paths or nonregular payloads found. This was a byte-integrity pass, not semantic reopening of archived ancestors.
- Both source-commit records name `a0fdc9a7dda2d84e5f535b3b54e31741ce753c7a`. Fourteen bounded core/helper/test files match that local Git object's bytes; all 15 recorded helper-hash leaves match frozen helper files. Primary replay imports exclusively from `source/`, using the goal helper's private `FunctionType`-bound namespaces, **not unbound hop defaults**.
- Launch records: guardian **404781**, **16:48:58–16:55:36 UTC**, September 14; recorded GPU UUID `GPU-c70cba10-6ab6-a287-e2db-51dccd617ab0` maps to GPU0 in the archived resource report (user-designated node2; no live host authentication).
- EXPOSE, TEACH and BASELINE have matching recorded before/after state `37ec37884e4b0b679edd1dba1be1dec3474589e992649f3a33e7e3b1ec78b8c0`; all report zero fits/updates and disabled training. Stage result dependencies, output inventories/hashes, and state records replay exactly. These are **recorded hash joins, not actual tensor authentication**.

## Independent results

| PROBE world / condition | Individual goals | Strict opposite-goal pairs | Retained terminals |
|---|---:|---:|---|
| A / OWN_TEXT | 2/4 | 1/2: tasks (0,2) | 2 reached_goal; 2 dead_end |
| B / OWN_TEXT | 3/4 | 1/2: tasks (1,3) | 3 reached_goal; 1 dead_end |
| A / UNAVAILABLE | 0/4 | 0/2 | 4 duplicate_address |
| B / UNAVAILABLE | 0/4 | 0/2 | 4 duplicate_address |

Paired tasks have identical CURRENT, PORTS and EVENTS/order, with only GOAL changed. A strict pair requires both final goals, distinct source-correct first ports, and two legal committed routes per episode. Thus there is **genuine but incomplete paired success on these fixed instances**, not merely favorable individual counts. Each OWN_TEXT episode commits two legal routes; the three failures reach the wrong terminal node. Each UNAVAILABLE episode makes four reads and one legal route, then repeats an address on actor call six; none completes two routes. B/UNAVAILABLE's (1,3) pair even selects distinct correct first ports, but still fails the endpoint criterion.

All **176 recorded native calls** join: EXPOSE **32 calls → 16 accepted source EVENTs** (four/world, two TRAIN plus two PROBE); TEACH **48 actual coached responses → 48 rows**, 24/world, all TRAIN; BASELINE **96 actor calls → 16 episodes**, six calls each. Eight coached TRAIN episodes complete four reads and two routes each. No source failures occurred in the 16 recorded attempts; none of the fixed attempts or the 11 failed baseline episodes is dropped. Failure-preservation tests also reject incomplete sources/lessons rather than fabricate missing events or emit a successful row subset.

## Visibility and interpretation

- No unintended evaluator-oracle or PROBE-to-teacher input was found. Offered exposure actions omit destination/receipt; EVENT-generation prompts receive the receipt only after the offered action commits. All stored EVENT strings join actual recorded child responses and receipts, with raw/canonical hashes checked; OWN_TEXT returns those raw strings without repair.
- Teaching is **intentionally source-informed**: the algorithmic parent supplies captured TRAIN EVENT witnesses and the exact next command. This is not unassisted planning. All 48 native guided prompts/responses join lesson captures and row targets. Student prefixes equal the native episode history without parent guidance; source text already obtained through actual memory feedback remains legitimately visible. Guided prompts remain in evidence/first-row provenance, not student prefixes.
- TRAIN/PROBE identifiers are disjoint; no PROBE identifier occurs anywhere in `teach/LESSONS.json`, including evidence/provenance. The outer stage binding contains all four worlds, but prompt-by-prompt replay finds no PROBE cases, scores or witnesses in teaching. Baseline actor histories contain only the public task, their own commands, literal memory returns and post-commit environment feedback—not parent plans or offline scores.
- This is a fresh baseline process at the **unchanged, already-taught 37ec state**, despite running after target collection. SEQ250 already supplied opposite-goal/order-0 lessons: frozen `experienced_event_two_hop_lesson.py` declares tasks `(0,2)` and 12 rows; the frozen collection design explicitly acknowledges that history. New goal-sensitive behavior was not absent before these 48 targets, and no gain can be attributed to them here.

## Tests, commands and limits

Executed locally without creating a review harness:

1. `sha256sum .../terminal.tar.gz`; `python3 -B` with `tarfile`/SHA256 for complete archive/extracted byte comparison; `git show a0fdc9a7dda2d84e5f535b3b54e31741ce753c7a:PATH` for 14 core comparisons (goal driver/guard/helper, hop/lesson/microloop/read-route helpers, memory/transfer/lesson/fresh-reader/native drivers, and both goal-pair tests).
2. Frozen `gpu.astra_goal_pair_collection.read_stage` for EXPOSE → TEACH → BASELINE, passing recorded binding/old IDs/worlds and exact predecessor-result hashes, **without calling `load_inputs` or `main`**. Passed inventories of 41/54/117 output JSON files, native-call joins, collection/lesson/episode replay and pair summaries.
3. Separate standard-library-only JSON reductions verified action→receipt→EVENT joins, 48 response→row/prefix joins, TRAIN-only guidance, all TRAIN/baseline transitions and conversation prefixes, 64 baseline memory returns, denominators and paired endpoints independently of helper scoring.
4. **Nine frozen `GoalPairTests` passed**: private-runtime isolation; same-display/opposite-port source replay; goal-independent first-port reference (2/4 individuals but 0/2 pairs); wrong-goal/dead-end retention; malformed-second-world retention; incomplete-source retention; PROBE/reorder/duplicate/source-drift rejection; native-error/prompt/token-bound retention; tampered-prompt/response/transition/row/missing-call rejection. These synthetic regression checks supplement, not replace, capsule replay.

Replay/test imports used an explicit deny-list for torch/transformers/tokenizers/peft/safetensors and HTTP clients; no model or tokenizer was loaded. Encoder tests and native-driver execution were excluded. No GPU, remote/network call, launch, production edit, fit, ancestor-chain reconstruction or live tensor/tokenization authentication occurred. Results establish internal consistency of this terminal capsule, not proof against omitted activity outside it, clean lineage, robust unseen-world generalization, new learning, or H1/H2. Only this assigned memo was written; other agents' files remain untouched.
