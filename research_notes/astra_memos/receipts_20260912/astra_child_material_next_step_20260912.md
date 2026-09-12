# Child-authored behavior material: smallest existing next path

2026-09-12. Read-only follow-up; no source/test edits, Git, remote/GPU operations, corpus creation or launch. Main owns both the venv-interpreter repair and any next experimental design. Original P0/NOTE criteria remain unchanged; this report does not promote their failures into passes.

## Recommendation

After the current oracle useful/corrupt writer comparison is actually evaluated, reuse **P0 raw wake generations → source-linked native V3 local spans → the existing V3 trainer → fresh parent-free native evaluation**. Do not go through `preschool_records_v1`, `prepare_write`, or the failed NOTE replay writer. The new glue needed is a small source-linked event exporter, not a new compiler, parenting framework or C11 guard.

Crucial wording: P0's child outputs were generated **with** the fixed teacher/sham present. Removing those bytes from training context and later evaluation tests carriage after parent removal; it does not make historical generation parent-free. Existing P0 is also not adaptive parenting.

## What actually exists in the P0 capsule

Read roots:
`/tmp/astra_P0_material_terminal_capsule_20260912/node3/astra_diagnostics/astra_P0_material_6101_20260912_attempt1/{lesson,sham}`.

I recomputed every file digest listed in each capsule arm's `artifact_hashes.json`: no mismatches. I also checked request/output text hashes and uniquely joined each thought's `(prompt_sha256, output_sha256, seed)` to generation events, and ran existing `facts_from_act`, V3 instance/transcript construction, and teacher-echo helpers in memory. No corpus was emitted.

| Observed local capsule property | Lesson | Sham |
|---|---:|---:|
| Wake thought rows / unique generation joins | 1024 / 1024 | 1024 / 1024 |
| Act rows / measured feedback rows | 1913 / 1903 | 1632 / 1627 |
| V3 episode instances / missing task heads | 64 / 0 | 64 / 0 |
| Thought text equals stripped complete raw output | 1024 | 1023 |
| Complete teacher-sentence/line echoes in thought targets, replay helper normalization | 10 | 0 |
| Default V3 target leak hits with actual teacher supplied | 0 | 0 |

One sham `thought.note` is clipped relative to its full raw generation. Recover its exact original output from `generations.jsonl` if selected, not by completing or rewriting text. Other leading/trailing whitespace differences still mean ledger text is not literally the entire raw output.

Accepted stored actions are highly repetitive. Distinct accepted episodes by family: lesson knights_knaves 7, mini_sudoku 1, arc_1d 1, countdown 1; sham knights_knaves 6, mini_sudoku 1. Both mini_sudoku arms' sixteen accepted actions all refer to **the same single puzzle `rg/mini_sudoku/1271272`**. This is not a ready 32-board successful child-solution corpus. These are ledger acceptance counts, not a new native-verifier rerun or a usefulness certificate.

The capsule is relocated. Full existing source validators require original absolute producer/model paths and matching bytes; those are on node3, not validated by this local digest/count inspection. Do not edit config paths in the capsule or claim that current changed producers authenticated historical material.

## Exact reuse and gaps

**Source/event binding:** `organism_v6/parent_material_write.py:108` `_formation_snapshot` validates completed artifacts, historical producer bytes/local pins, schedule, and original result recomputation; zero eligible records can still be a valid completed snapshot. Its later `_select` requires strict NOTE eligibility and must NOT be used for this new event route.

`organism_v6/parent_material_analysis.py:123` `_arm` already distinguishes a valid measured ACT from a rejected record: unique execution, actual 400-token wake association, and `preschool_reasoning.facts_from_act` (`:198`). Its nested join is not an exported standalone event validator. Reuse this logic in the small exporter: bind occurrence, tick, execution, exact ledger line/hash, request/output line/hash, model identity and actual action occurrence. Handle multiple/repeated ACTs by physical order/count, not just membership of the action string. Never fabricate feedback from a note or output text.

`parent_note_replay_diagnostic.py:101` `inspect_source` demonstrates provenance validation despite bad old NOTE content, but it is specialized to exactly first-four measured ACTs/64 schedules and coaching replay. It is NOT a drop-in general behavior exporter. `_judge_source` (`preschool_reasoning.py:798`) still calls `judge_record`; do not monkeypatch it to force an event through the old record gate.

**Teacher exclusion:** reuse actual `lesson_deliveries.jsonl`, `_lesson_rows`/`_teacher_row` (`preschool_reasoning.py:644`, `:684`) and normalized complete-sentence exclusion from `parent_note_replay_diagnostic._payloads`/`_echo` (`:81`, `:90`). The measured 10-versus-0 discrepancy above shows that V3's default longer-line leak scan alone is insufficient for these P0 teachers. Reject a selected echo-bearing target; do not delete phrases from the child target or replace it with synthesized prose. Explicitly provide teacher bytes to exclusion checks; P0 `parent_turn` is not V3's recognized `parent` row kind and lesson deliveries are not automatically the usual parent-brief files.

**Compiler:** `sleep_compile_v3.build_instances` (`:236`, explicit `acts_first`) already handles these rows: 64 instances, no orphan counter in this inspection. `transcript` (`:410`) gives real GOAL/METRIC → child text → zero-loss measured feedback. `local_view_items` (`:619`, window mode) and `compile_two_scale` (`:840`, local-only view) give task plus actual antecedent context, with one child chunk as target. No first-person predicate and no prerequisite accepted NOTE. B does NOT select useful behavior: it includes erroneous/unexecuted/repeated output too. Outcome tokens remain context, not child targets or direct memory supervision.

Use raw-generation text as the source of truth when constructing selected spans; log the exporter-to-source relation rather than editing original ledgers. Existing compiler canonicalization/strip operations are not an exact raw-byte carrier; `--no-canonicalize` only removes one normalization. The small exporter can use existing V3 context assembly while putting the original raw output directly into the target span. Reject teacher echoes in included antecedent context as well if declaring parent-free training context. Do not silently retain teacher-bearing stored prompts or delete outcome evidence.

**Writer:** `train_adapter_v3.normalize_items` (`:125`), plain `encode_item`/`encode_item_segments` (`:151`, `:233`) and `collate` (`:368`) already support explicit zero-loss context/child-target spans. Use actual-tokenizer preflight, no lost target tokens, and an explicit choice of context renderer. The current oracle preparer's pre-rendered native-context/plain-span solution avoids `.rstrip("\n")` and double templating; do not silently switch back to `--chat-template`. Child authorship is established by the source join, not by a loss mask. Never label this external event corpus as a clean-nursery certificate.

## One bounded next comparison, for main to choose

If the oracle control shows useful conditional behavior rather than just ACT formatting, the smallest useful follow-on is **one seed-0 child-stream lesson-versus-sham write, then the same parent-free OFF/ON action evaluation**. No new parenting calls or wake rerun. A concrete bounded design option is the first 32 prebound P0 schedules, each arm's first measured-action wake chunk, one example per schedule. Freeze that source rule before fitting; require source/teacher checks and exact count in both arms or emit paired skip, with no backfill. These are candidate behavior traces, not pre-certified useful solutions. The design/count is a recommendation for main, not a change to frozen P0 criteria or an implemented selector.

The small exporter above is the only missing executable step. Once it emits the two span corpora, existing `python -m organism_v6.train_adapter_v3 --corpus <arm.json> --out <fresh-adapter> --model <local-base> --rank 8 --lr 1e-4 --epochs 3 --seed 0 --batch-size 1 --grad-accum 1 --no-pack --max-len 4096` supplies 96 steps/arm **if** each example preflights as one segment. Use shell-free argv and the preserved venv interpreter path. Main's existing neutral runner/reducer supplies actual fresh-process parent-free evaluation; primary first-ACT solves, missing/invalid zero, secondary first-ACT score/native best/nACTs. No teacher, corpus retrieval, child history or parent brief in probe prompts. Verify evaluation board identities against P0 sources before reusing a panel; already examined canary results are exploratory, not untouched confirmation.

If main instead requires success-only mini_sudoku targets, **stop at the one-puzzle shortage**: P0 cannot honestly supply 32 distinct solved boards. Do not pad repetitions into independent examples. A later fixed parent-free child rollout on the current training boards would be a separate data-collection decision, not already available P0 material. If oracle training fails to carry useful behavior, park this follow-on rather than change text filters or run a larger parenting study.

Two competencies already named in `research_notes/analysis/2026-09-12_coached_source_replay_value_and_p0_coach_audit.md:109` are `FORM_CHECK` and `CONSTRAINT_LEDGER`: produce a usable action form, then satisfy actual task constraints. Score their consequences by parser validity and verifier outcomes, not by claiming a child “used a plan.” P0's fixed record lesson did not specifically teach or isolate these competencies. The proposed lesson/sham difference remains a whole-package comparison, confounded by 203 versus 158 teacher tokens and different realized trajectories; no adaptive-parent, semantic-isolation, H1 or durable-learning claim.

## Existing tests to retain; no new tests run here

- `tests/test_parent_material_analysis.py:338`: first-person form is not inferred from arbitrary slot response; `:397`: duplicate generation identifiers rejected.
- `tests/test_parent_note_replay_diagnostic.py:162`, `:179`, `:191`: complete teacher-sentence echoes, corrupt provenance despite bad old content, wake trace tampering.
- `tests/test_sleep_compile_v3.py:37`, `:91`, `:141`, `:230`, `:298`, `:478`: ACT joins/orphans, chronology and masked harness, child targets, antecedent context, parent leaks.
- `tests/test_train_adapter_v3.py:63`, `:97`, `:202`: context masks, target preservation and collate isolation.

Exporter-specific regressions still needed if main authorizes it: repeated ACT ordinal binding, clipped-thought recovery from raw trace, P0 teacher sentence echoes missed by default V3, fixed paired selection/no backfill, no teacher in training/probe contexts, actual label/token checks. No new corpus has been prepared by this review.
