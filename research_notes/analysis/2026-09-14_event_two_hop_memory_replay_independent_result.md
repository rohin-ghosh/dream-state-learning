# Independent result: strengthened trajectory replay during memory writing

Reviewed September 14, 2026. This bounded local review compares the terminal replay capsule directly with run 253, using `research_notes/analysis/2026-09-14_event_two_hop_memory_independent_result.md` as the already-reviewed source context. Only this new memo is edited. No model loading, GPU/remote action, framework construction, or full ancestry audit is performed.

## Finding and recipe disposition

**No observed action improvement from this exact increased-budget replay recipe.** The replay starts from the same `37ec…8c0` parent, preserves the original four scheduled rows at every update, and appends two saved actual trajectory rows. It produces a different adapter, but all fresh-task read-address sequences, actor commands, committed transitions, and terminal outcomes match run 253 in PARAMETRIC, OWN_TEXT, and UNAVAILABLE. Taught-graph actor commands and outcomes also match.

Parametric retrieval remains exact and its actual returned text reaches the actor without fallback. The controller still succeeds on only tasks 1 and 2. New and old recall are unchanged, while held audit drops from 16/16 to 15/16 through one false positive on a true case.

**Close this specific six-row, 100-update replay variant as a negative engineering result on the tested graph.** It does not establish that trajectory replay generally cannot help, nor provide an equal-token causal comparison or H1/H2 evidence.

## Capsule, source, and state joins

Replay artifact root, abbreviated **R** below:

`gpu_artifacts_local/astra_event_two_hop_memory_replay_terminal_20260914_attempt1/extracted`

Reference root, abbreviated **253**:

`gpu_artifacts_local/astra_event_two_hop_memory_terminal_20260914_attempt1/extracted`

- Independently hashed R's sibling `terminal.tar.gz`: `f23f71a11e991563ee017fbfc14a467b6c88ad711729bfb8ea07ca51676607b5`, matching the supplied digest.
- Source marker: `28b44b19a050bbd431bad884f830d05ef0762f64`; guardian `402364`; guardian interval **2026-09-14 16:25:50–16:35:43 UTC**.
- Native TRAIN interval: 16:25:50.278–16:31:37.640 UTC; AFTER: 16:31:38.697–16:35:42.638 UTC.
- TRAIN/AFTER are COMPLETE, fits 1/0, with no phase FAILED artifact. Their replay bindings match, and the embedded memory binding equals 253's binding.
- Verified all four training-file hashes, three adapter-file hashes, and 231 AFTER output-file hashes; native CALL inventory, indices, error fields, and role totals agree with the receipt. Entry hashes match the archived replay driver.
- The archived underlying memory driver and two-hop helper are byte-identical to 253's copies. R reuses that memory evaluator; it does not replace the parametric reader with the text service.

The same parent is loaded anew, **not** the `9d3674…9c86` adapter written by 253:

| Join | Independently checked value |
| --- | --- |
| Initial state | `37ec37884e4b0b679edd1dba1be1dec3474589e992649f3a33e7e3b1ec78b8c0` |
| Replay saved and AFTER-loaded/final state | `52658b3efe743409ef69ef67986b77e3d21f0a3ba28552d8bfb5b7471637786d` |
| Reused 253 BEFORE receipt | `4f6d9ecdccd941f5a7f1090bad051ac8adffba8e95c6296951ec56803a025520` |
| Referenced 253 TRAIN receipt | `35fdd06530f68a8e2555fb72c4a212741a089f3f15298bcd5bd769e0136632c3` |
| Referenced 253 AFTER receipt | `9df89e6f1c2f808fa4ce9199dc405df28e1e8a7ca1afecdce9cabd48d08017a5` |
| Replay TRAIN receipt | `06065336ddf25c63b304fafa6a8867dc32c763d86cbac1da07816018cc50877a` |
| Replay AFTER receipt | `8cba60e65e76417ed4d3854ed7eb810fd8c885e143575cb21f87905072e820ea` |

R has no newly generated BEFORE directory: both phases bind the exact prior BEFORE hash. Its 0/4 parametric task and 0/4 W0/W8 recall results are **reused observations**, not additional samples. AFTER binds R's own TRAIN receipt, and both `STATES.json` files agree with their receipts. The saved adapter weight file hashes to `abc8a2dc1532f172498f4b64338476a0d675cb52aac4dd03b4f7c99d91de0122`.

Frozen-base and live tensor-state checks are native-receipt claims whose joins are consistent. This review independently verifies saved files and state receipts, not the underlying model/base tensor hashes.

## Exact intervention and dose

R and 253 have **byte-identical** `train/TRAINING_ROWS.json`, `MASKS.json`, `NEW_ROWS.json`, `COLLECTION_SOURCE.json`, `WORLD.json`, and `TASKS.json`. The same 254 encoded rows retain their input tokens, labels, and EOTs. The 12 trajectory rows' assistants and student prefixes match the actual response/student-prefix fields in their carried captures; teacher command hints are absent from those student prefixes. No new trajectory or fact was synthesized for this variant.

For zero-based update offset `u`, all 100 logged and saved schedule entries are exactly:

`[u % 128, 128 + u % 94, 222 + (2*u) % 32, 222 + (2*u+1) % 32, 210 + (2*u) % 12, 210 + (2*u+1) % 12]`.

The first four indices equal the corresponding 253 schedule/log entries. The last two select the saved trajectory rows. Independent sums of causally shifted unmasked labels match every update log, the saved row-presentation vector, and the final receipt:

| Group | 253 presentations | Replay presentations | 253 labels | Replay labels |
| --- | ---: | ---: | ---: | ---: |
| Old memory | 100 | 100 | 5,143 | 5,143 |
| Cue | 26 | 26 | 296 | 296 |
| Audit | 62 | 62 | 400 | 400 |
| Trajectory | 12 | **212** | 136 | **2,404** |
| New memory | 200 | 200 | 10,200 | 10,200 |
| **Total** | **400** | **600** | **16,175** | **18,443** |

Exactly **200 extra actual trajectory presentations add 2,268 labels**, a 14.02% label-budget increase. New-fact dose remains 50 presentations per fact. Recipe: fresh AdamW, `3e-5`, seed 0, rank 8, 100 updates, batch six, mean causal CE.

**Same original rows does not mean unchanged original loss weight.** The mean now uses all six rows' active labels; this recipe does not preserve 253's denominator. From the saved per-batch counts, an existing label's averaging coefficient is 86.86–88.71% of its former coefficient. That is a statement about normalization, not equality or scaling of the realized gradients across diverging models. This is appropriately labeled an increased-budget engineering variant, not an isolated additive-gradient or equal-token comparison.

## Actual parametric reads and commands

Direct JSON reduction checked native CALL/episode-trace equality, actor-message construction, episode seals, and legal committed transitions against world edges without executing the author's evaluator.

All four PARAMETRIC tasks again read all four addresses: **16/16 native returns exactly match the canonical source records**. Each address-only native memory response matches its memory trace and is inserted unchanged after `MEMORY RESULT\n` in the actor conversation. There is no source table or replacement intermediate goal in the reader request, and no captured-text fallback in the unchanged PARAMETRIC branch.

As in 253, exact parametric output has the declared single final LF, whereas captured OWN_TEXT has none. This serialization difference remains; no read-time repair is needed or observed. The two services nevertheless produce identical taskwise read sequences, actor commands, and commits. Sixteen returns cover four unique records, not sixteen independent facts.

The following is identical in R and 253 for both PARAMETRIC and OWN_TEXT:

| Task | Goal / order | ROUTE commands after four reads | Committed routes | Result |
| --- | --- | --- | ---: | --- |
| 0 | `N_JHDSMLVMTV` / forward | `P_AYK4AJ3M7N`, `P_OSJB7PXJ7E` | 2 | Wrong legal branch; reaches `N_44AN3UAXYD`, `dead_end` |
| 1 | `N_JHDSMLVMTV` / reversed | `P_YW4FRYEBND`, `P_T6RLPFRTVW` | 2 | `reached_goal` |
| 2 | `N_44AN3UAXYD` / forward | `P_AYK4AJ3M7N`, `P_OSJB7PXJ7E` | 2 | `reached_goal` |
| 3 | `N_44AN3UAXYD` / reversed | Premature `P_OSJB7PXJ7E` at the root | **0** | `invalid_route` |

Each condition uses 23 actor calls and 16 reads; PARAMETRIC adds 16 native reader calls, while OWN_TEXT supplies captured strings. UNAVAILABLE again uses 24 actor calls, one committed root route per task, and terminates on a duplicate-address attempt in all four tasks. Those commands/outcomes also match 253 exactly.

AFTER totals **166 error-free native captures**: 94 actor, 16 memory, 8 new-recall, 32 old-recall, and 16 held-audit calls. Task failures are retained and are not native exceptions.

## Comparison and the new audit error

| Saved outcome | 253 | Replay |
| --- | ---: | ---: |
| Fresh PARAMETRIC | 2/4 | 2/4 |
| Fresh OWN_TEXT | 2/4 | 2/4 |
| Fresh UNAVAILABLE | 0/4 | 0/4 |
| New recall W0 / W8 | 4/4 / 4/4 | 4/4 / 4/4 |
| Old recall W0 / W8 | 16/16 / 16/16 | 16/16 / 16/16 |
| Taught OWN_TEXT | 3/4 | 3/4 |
| Held audit | 16/16 | **15/16** |

Recall artifacts match their native responses and saved expectations. The taught graph retains exactly the same actor-command sequences and commits, including its task-3 wrong dead end.

The held cases are identical between capsules. Case **10**, kind **true**, skin **1**, event **`E_VEEAOY3IIH`**, expects **`NONE`**. Replay instead returns **`E_VEEAOY3IIH`**; 253 returned `NONE`. The replay response is terminal and not truncated, and the case/capture/native-call joins agree. This is a **false positive against a valid reply**, recorded as `WRONG_OUTPUT`, not a formatting error or a failure to detect a fault. The split is 7/8 true and 8/8 fault cases. This is one observed regression on a fixed diagnostic, not a statistical estimate of general degradation. The audit supplies a source table and remains separate from autonomous route-loop memory checking.

## Conclusion

The extra replay dose did not change the observed route policy on either graph and did not repair either fresh-task failure, despite maintaining perfect factual retrieval. It also introduced one audit false positive. The narrow parametric-memory-to-action result from 253 survives; a successful controller repair does not. This closes the specified recipe without expanding the search or making a general claim against replay, whole-life learning, or H1/H2.
