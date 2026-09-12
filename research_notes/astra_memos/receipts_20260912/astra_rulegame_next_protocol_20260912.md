# Next RuleGame integration protocol — bounded design only

Date: 2026-09-12. Status: PROPOSED INTERFACE, NOT IMPLEMENTED OR AUTHORIZED TO LAUNCH.

This document answers the read-only request. Only this `/tmp` file was written; no project modules, tests, GPU commands, network operations, or Git commands were run. Source inspection was restricted to the named loop and its direct dependencies, targeted Astra receipts, and relevant coordination entries. Source statements below describe inspected bytes, not runtime validation.

## 1. Decision and immediate handoff

**Next substantive path: one small RuleGame dialogue scout, using the existing episode/parent/world interfaces, an explicitly sourced Boolean post-outcome record, and the current `train_adapter` child-body-only writer used by `run_life_v2`.** Do not launch the old `nursery_dialogue --phase sleep`, pretend RuleGame is a registered modern Gym, or reuse a reasoning-gym formation certificate for RuleGame.

Main's immediate work remains cumulative terminal capture and evidence synthesis. SEQ091 single-citation writing is already owned/implementing: do not duplicate its code, write, inference, source hunt, or exposed-board evaluation. This proposal is the next interactive parenting → genuinely new child action → actual world response → child record → sleep → fresh parent-free task path, not another replay of t02 or a citation variant.

Use simple hygiene now. `research_loop/COORDINATION.md:2597` records Rohin's instruction to defer completion/enforcement of the formal C11 guard to the final paper-grade run. No new custody service, formal C11 gate, or independent-review prerequisite is proposed here. Source links, actual control costs, absence of teacher bytes, frozen base, isolated adapters, preserved failures, resource ownership, and lease cutoffs still matter. This request grants **no implementation or launch permission**, irrespective of the broader standing authorization.

## 2. What existing evidence does and does not say

These are attributed local receipts, not freshly recomputed results:

- `research_notes/astra_memos/ASTRA_P0_MATERIAL_TERMINAL_2026-09-12.md:1`: original lesson/sham P0 produced zero strict faithful records in both arms, zero selected material, and no fits/probes. Its 203 versus 158 teacher tokens per presentation and differing presentation counts were not matched parent exposure.
- `research_notes/astra_memos/ASTRA_COACHED_REPLAY_TERMINAL_2026-09-12.md:1`: SEQ070 completed 512 recorded-source note requests, still zero strict qualifying records in either arm; paired write skipped. It performed no new world actions. That is not evidence for the new experience path.
- `research_notes/astra_memos/ASTRA_FRESH_CORRECTION_TERMINAL_2026-09-12.md:1`: SEQ082's same-episode path executed, but primary first/second-opportunity solves tied at 1/32 and 2/32; qualifying corrections were process 1 versus sham 2. Fixed 97-token packages did not match realized total exposure because numbers of ACT-triggered calls differed. There was no training or parent-removal test.
- `research_loop/COORDINATION.md:4216`: SEQ091's sole valid transfer t02 followed invalid s02; neither valid source transferred. No verified correct lesson chain or approved free-prose lesson was established. The following timestamp correction places that entry at approximately 15:52 UTC, despite its 15:55 header. Its selected single-citation diagnostic is separate work, not positive parenting evidence.
- `research_notes/astra_memos/ASTRA_SIMPLE_HYGIENE_CUMULATIVE_PATH_2026-09-12.md:1` distinguishes a narrow persisted memory association and separate externally verified useful-versus-corrupt behavioral material from selective writing, child-authored useful extraction, parenting, and G3. Do not transfer those positives to RuleGame.
- `research_notes/astra_memos/ASTRA_CUMULATIVE_READONLY_AUDIT_2026-09-12.md:1` is a validity audit, explicitly not a terminal success certificate. Its source cut reported `LAUNCHED_NOT_COMPLETED`; the later coordination entry reports fit progress, not completed readouts. No live status was checked here.

**No prior positive RuleGame parenting → faithful child material → sleep → new-task result is established by these inspected receipts.** The proposed scout must produce its own evidence. Failure of an earlier frozen judge stays failure; a prospective Boolean record predicate must not relabel old results.

## 3. Exact reusable interfaces and traps

| Existing interface | Reuse | Do not assume |
| --- | --- | --- |
| `nursery_dialogue.play_task(model, game, eid, ledger, boot, budget=10, prefix=None)` (`:48`) | `Episode` construction and single-task dialogue shape; returns `(driver.summary(), driver)` with a transcript tail. | It has no post-outcome slot parameter, explicit generation seed, active-control branch, or admission-enforcing compiler. The bounded wrapper below is needed. |
| `nursery_dialogue.parent_turn(model, transcript)` (`:58`) | Local parent request, transcript suffix at most 4,000 characters, one process mistake, no answer, under 120 words; generation ceiling 200, temperature .5. | Parent and child use the same engine under different prompts. A distinct stronger teacher or enforced answer blindness is not supplied. There is no matched active-parent helper. |
| `RuleGame._rule(eid)`, `quiz_triples(eid, k=6)`, `evaluate(episode, action)` (`rulegame.py:36`, `:46`, `:60`) | Deterministic world, `ruleN/...` forcing, six shuffled balanced quiz labels, actual `TRY` response text. | `_rule`/truth labels are private evaluator information. `TRY` always returns scalar reward **0**, even when the Boolean observation is True. `QUIZ ?` reveals triples through an INVALID-format response, not a scored quiz. |
| `EpisodeDriver`, `run_episodes_batch(model, gym, episodes, bootstrap, ledger, budget_ticks=24, log=print, gen_seed=None, driver_cls=EpisodeDriver, note_after=None)` (`batch_loop.py:21`, `:147`) | Real action execution, raw thought/ACT ledgers, per-episode/tick seeds, custom driver/slot extension points. Pass one episode per call for the smallest serial dialogue adapter. | Native `consume` executes multiple ACT lines in one generation; ticks alone do not cap ACTs. PREDICT parses numbers, so `PREDICT: T/F` becomes None. `best_score` can reflect repeated quizzes. |
| `PostOutcomeSlot.execution_id`, `reserve_occurrences`, `run_round` (`preschool.py:160`) | Occurrence reservation, ACT identity joins, one separate post-outcome round and accounting pattern. | Existing `parse_outcome`, `block`, `execution_facts`, `judge_record`, and `gate_sleep` are compiler-numeric, not Boolean RuleGame validators. A real `the box says: True/False` is currently treated as failure. The stock note prompt uses the pre-ACT prompt, not the actual latest emitted chunk; note outputs lack the wake generation's full identity/hash receipt. |
| `Ledger.append/rows/recall` (`ledger.py:18`) | Append-only raw evidence. | `recall` searches arbitrary note-bearing row kinds, including parent rows. A shared ledger is not parent-free memory isolation. |
| `compile_native(rows, out_dir, prior_corpus, recall_mix=.3, model=None)` (`sleep_compile.py:285`) | Historical interface reference only. | Selects thought `win OR had_note`, reflections, and note recall. It can admit restatements and teacher-bearing prompt bytes. No lesson admission argument exists. Do not use here. |
| `compile_sleep(model, rows, out_dir, prior_corpus, vocab=None, vocab_by_gym=None)` (`sleep_compile.py:260`) | Shows modern cumulative corpus convention. | Generates transformed exemplars/principles/brief; it is not a strict child-output-only selector. Default vocabulary is compiler-specific. Do not run the generic transform for this scout. |
| `train_adapter.child_record_prefix_length`, `child_target_mask`, `child_label_counts`; `train_adapter.main` (`:25`, `:37`, `:47`, `:124`) | Existing modern writer with `recipe="preschool_records_v1"`, prefix/child boundary, prefix/padding masking, causal-shift token checks, seeded fresh-base rank-8 training. | Missing recipe silently chooses ordinary LM supervision; dict `{q,a}` input discards q and trains a, not a native paired-chat objective. `DONE` means training completed, not scientific success. |
| `run_life_v2.existing_adapter_verdict`, `validate_adapter_states`, `promote_trained_adapter` (`:84`, `:103`, `:131`) | Staged immutable adapter lifecycle; training subprocess pattern at `:1184`. | These are not a drop-in RuleGame runner. `gym_backend.py:308` registers compiler/reasoning_gym only. The clean-nursery route is reasoning-specific. Do not invent `--gym rulegame`. |
| `run_life_v2.format_canary(model, gym, threshold=.5, selection=None)` (`:153`) | Actual-context canonical ACT check, fixed 3-tick structure and .5 threshold. | Requires `birth_prompt`, `canary_set`, `episode_from_id` and a Gym-like name for driver selection. Bare RuleGame lacks these. Use only a narrow delegating facade for this check, not a new full Gym integration. A canary is motor-format evidence, not quiz or process competence. |
| `VLLMBackend.batch`, `generation_identity`, `close_backend` (`model_backend.py`) | Existing local generation/backend lifecycle and configured identity receipts. | Loader paths/hashes do not authenticate previously unknown base ancestry; default wake ceiling is 400 tokens, temperature .7. |

### Admission flag is not enforcement

`nursery_dialogue.py:158` computes `admitted = post["best_score"] >= pre["best_score"]`; rejection executes `pass`. It does not remove apply streams or block training. `0 >= 0` can be true without a valid quiz. Native `win` flags track score improvement within an episode, not lesson admission, and `had_note` bypasses any win requirement in the old compiler. The sleep branch calls `train_adapter_v21` and exits with its return code; its documentation's format-canary wording is not an enforced sleep gate.

Keep the old `admitted` value as a historical diagnostic if desired, but name the actual prospective predicate separately and enforce it before constructing corpus bytes. Never reinterpret old flags as already-enforced certificates.

## 4. Smallest prospective adapter — no new learning architecture

Use a bounded dialogue wrapper around the existing `Episode`/`RuleGame`/`run_episodes_batch` seams. Reuse the parent prompt/request shape, replacing the old solo branch with an equally present active parent. Reuse the current writer directly. Do **not** modify global driver behavior, the rule functions, quiz labels/scoring, base model, trainer objective, or historical receipt predicates.

The following are **proposed non-material interface repairs/harness constraints**, not existing helpers or edits performed here:

1. **Bound the protocol, not just ticks.** A RuleGame-scoped driver validates the raw generation before execution: at most one ACT, at most four TRYs, at most one quiz reveal and one scored quiz per task. Preserve every raw invalid/multi-ACT output; terminate that task as protocol-invalid rather than execute a convenient first line, regenerate, or hide extra actions. Valid TRY must have exactly three integers; valid final quiz exactly six literal T/F labels. This prevents the existing parser's silent truncation/permissive labels from turning malformed output into successful work. Valid world outcomes and scoring remain unchanged. Log this as a bounded protocol variant, not byte-identical legacy performance.
2. **Record Boolean prediction separately from scalar reward.** Bind the last explicit T/F prediction before the executed ACT in that same raw output to that execution. Missing/ambiguous prediction is missing, not synthesized. Never compute Boolean prediction correctness from reward zero. No need to change the global numeric-surprise implementation for other gyms.
3. **RuleGame-specific post-outcome slot.** At each valid executed TRY, issue at most one 100-token child record request. Reuse occurrence/execution reservations, but use Boolean action/outcome facts and include the actual source output plus the exact returned observation. Persist the complete prompt/output, hashes, generation identity, seed, token counts, action-row join and ordering. Enforce output cardinality/types instead of relying on truncating `zip`. No note request for quiz reveal, quiz score, unexecuted ACT, or synthetic/replayed source. The common slot instruction asks for the submitted triple, prior prediction if any, observed Boolean and appropriately limited conclusion; it does not provide a worked answer or parent lesson.
4. **Explicit record admission and child-only export.** Reject unlinked, duplicate-execution, reordered, forged, unsupported, teacher-echo and evaluation records; admit actual child text only. Maintain an append-only rejection table. Do not run compiler-specific `preschool.gate_sleep` over RuleGame and call its output grounded. The output schema may reuse the writer's child-only recipe without forging a compiler/clean-lineage gate receipt.
5. **Visibility/control adapter.** Keep parent transcripts/restatements in a separate audit stream; give each task a new driver and task-local retrieval view. No cross-task `RECALL`, parent-row lookup, prior brief, or ledger access in readout. A canary-only facade delegates `evaluate` to the same RuleGame and supplies the three missing canary methods and a non-minisudoku name; no registry change is necessary.

These repairs preserve the frozen thesis and rules while making the chosen experimental contract executable. If implementation instead requires changing the world/benchmark semantics, a scientific claim, invariant, or base, stop this proposal's scope; do not label that expansion a repair. Add focused regression tests when/if Main authorizes implementation, preserving original artifacts. None were added or executed now.

## 5. Fixed formation, control, and task budget

One exploratory generation seed **20260912**; one training seed **2**; two formation arms: **process parent P** and **active non-process parent A**. Frozen locally pinned Qwen2.5-7B-Instruct, no incoming adapter. Parent generation also uses that unchanged base. No optimizer-seed replication, curriculum expansion, dose sweep, or second sleep in this scout.

### Task identities

- Eight lessons per arm, lesson index 0..7; rule index `lesson % 4` (rules 0..3 only).
- Pre/apply IDs: `rule{rule_index}/astra-next-20260912/lesson{lesson}/pre` and `/apply`. IDs, tasks, generation seeds and ordering are **identical across arms**; arm identity belongs in the output directory, not the eid. The old `.../{arm}-{les}-a` naming changes quiz draws across arms and is unsuitable for exact pairing.
- New-task readout: eight tasks, two per unused rule index 4..7: `rule{rule_index}/astra-next-20260912/readout{0|1}`. This tests new rule classes within the existing ten-rule library, not novel environments or a held-out population. Both models see exactly the same IDs.
- Canary only: `rule8/astra-next-20260912/canary` and `rule9/astra-next-20260912/canary`; never corpus material or readout endpoints.
- Before formation, check these prospective IDs against the locally available exposure receipts and freeze the exact quiz triples/manifest evaluator-side. Do not claim global historical novelty without evidence. Collisions or malformed six-item panels stop preparation; do not choose replacements after observing results.

### One lesson in each arm

1. Child plays pre-task, no parent prefix, new task state.
2. Exactly one parent request sees only that child's pre-task transcript (no apply/readout scores or hidden rule). P names one process mistake. A provides neutral acknowledgment of participation with no strategy, hypothesis, answer, evaluated correction, or action recommendation. Both requests use the same engine, 200-token ceiling and .5 temperature.
3. Exactly one child restatement request in each arm, 120-token ceiling and .5 temperature. Keep the old prefix/restatement shape for temporary apply-task context. The A arm restates its equally present neutral interaction; it is **not** the old no-parent solo arm. Preserve the original lesson and restatement bytes in receipts only.
4. Child plays apply-task under that temporary restatement prefix, executing its own TRYs and seeing new world responses. The parent cannot intervene during apply or select its probes, outcomes, notes or quiz answers. Generate a sourced post-outcome record after each valid TRY.
5. Compute the valid first-quiz score for both tasks. Record all eight lesson outcomes, including failures, irrespective of future admission. Parent/restatement goes away before sleep and before every readout task.

Each full task has at most **six wake generations at 400 tokens**: intended four TRY opportunities, one `QUIZ ?` reveal, one scored quiz; at most four post-outcome note generations at 100 tokens. Early DONE or first quiz ends opportunity to acquire more evidence; invalid outputs and unused slots remain visible. The limit is a maximum, not permission to fabricate missing calls. Notes are ledger-only, as in the existing slot; feeding them back into later wake prompts is not part of this minimal change.

### Parent-cost matching, explicitly

Match task IDs, maximum world actions, wake/note opportunities, parent request count, restatement count, model, settings and delivery schedule. Before generation/delivery, native-tokenize the **actual backend-rendered** inputs: use fixed parent-request input length 2,048 tokens, restatement-request length 1,024 tokens, and delivered apply-restatement block length 256 tokens, using the same marked neutral-padding convention in both arms. These lengths are proposed caps/targets, not measured facts. Preserve meaningful text verbatim; if it cannot fit or exact native padding cannot be achieved, stop preparation, not truncate a lesson differently by arm. The process/control instructions and padding are all auditable exposure, never training material.

Parent and child output ceilings are matched, but actual generated tokens, note-call counts, later context lengths and wall time may differ. Record these separately by role and phase, including repeated presentations of the lesson/restatement in prompts. **Equal maxima, equal words, or equal package tokens do not establish equal realized compute.** No invisible dummy calls, retrospective resampling, or token top-ups. If realized costs differ, report an opportunity/input-dose-matched exploratory comparison with residual cost differences, not an exact total-compute-matched parenting effect. An exact realized-cost causal claim would require a separately specified control, not a silent assertion here.

### Hard totals, including controls

| Work | Maximum |
| --- | ---: |
| Formation full tasks | 2 arms × 8 lessons × 2 = 32 |
| Parent requests / child restatements | 16 / 16 |
| Readout full tasks | 4 cells × 8 = 32 |
| Canary tasks | 4 cells × 2 = 8, three wake ticks each, no extra note round |
| Full-task wake requests | 64 × 6 = 384 |
| Canary wake requests | 24 |
| Post-outcome note requests | 64 × 4 = 256 |
| All generated responses | **696 maximum**, counting roles individually, not batch calls |
| Output-token ceiling | **193,920** = 408×400 + 256×100 + 16×200 + 16×120 |
| Sleep | At most two fresh fits, 16 selected unique records each, rank 8, 3 epochs, lr 1e-4, seed 2, native batch 4: 12 steps each, **24 total** |

There are at most 72 task executions, of which eight are short canaries. All four readout cells are fresh processes/contexts: P/OFF, P/ON, A/OFF, A/ON. If either formation arm lacks material, skip both fits and both ON readouts; retain the two OFF diagnostics within their original caps. No extra deficit-filling tasks or retries. Proposed reservation ceiling, if later scheduled by Main: **60 aggregate reserved GPU minutes**, including load, parent, wake, fits, reads and cleanup, and always the earlier actual lease deadline. This is a stop cap, not a measured runtime forecast or resource reservation.

## 6. Grounding predicate and exact writer boundary

### Two distinct endpoints

**Quiz accuracy:** six-label correctness on the first valid scored quiz, obtained from the evaluator's exact correct-count/6, not rounded response text. Require one quiz only; missing/invalid quiz is zero in the all-task primary denominator, with validity counts reported separately. Native `best_score` is supplementary. A TRY reward of zero is neither an incorrect prediction nor a failed action. Predicting the Boolean correctly and choosing useful discriminating tests are also different endpoints.

**Faithful process record:** text produced by the child *after its own executed TRY*, correctly describing its actual triple, any pre-ACT T/F prediction, and the returned True/False, with no invented observation or universal rule claim unsupported by its evidence. A record can faithfully describe a disproven prediction. A correct quiz can coexist with zero faithful records. A faithful record can coexist with a wrong quiz. Native `NOTE` markers, first-person wording, restating the parent's advice, or high quiz score alone do not qualify.

For this small prospective predicate, require exact recoverable submitted triple and observed Boolean, correct treatment of the raw prediction (including explicit absence), and no additional factual/process claim beyond the linked evidence. Ambiguous free prose is rejected, not model-rewritten. Record alternative descriptive quality judgments separately; never loosen the inclusion predicate after seeing shortage. Claims of contrast/discrimination require actual linked prior TRYs, not merely the parent's recommendation to compare. Keep the predicate and fixtures fixed before formation.

### Real admission, not an annotation

- Eligible lesson: pre and apply each have a valid scored quiz and apply accuracy is at least pre accuracy. Record the legacy raw comparison separately. Missing quizzes cannot qualify through 0>=0.
- Eligible corpus record: apply-task valid TRY from an eligible lesson, one unique action identity → one later raw note output, source generation and actual outcome verified, faithful predicate passed, no teacher/other-task contamination. Pre-task notes and all evaluation/canary notes stay audit-only.
- Select the first **16 distinct child-note texts** in physical eligible-record order independently in each arm; no score ranking, best-example hunt, post hoc padding, duplicates disguised by wrappers, or cross-arm borrowing. Each arm has at most 32 apply TRY records to supply them. If either has fewer than 16, emit a paired material-shortage result, not a smaller fit. Sixteen is a prospective small RuleGame diagnostic budget, **not** a lowering/reinterpretation of the old P0 64-record gate.
- Equal selected row counts/optimizer steps do not mean equal supervised-token mass. Record native counts and rejection/selection reasons in both arms. Selection conditional on post-treatment admission is part of this mechanism diagnostic; the selected-corpus contrast is not an unconditional causal effect of parenting.

### Bytes presented to the existing writer

Create a fresh JSON document with `recipe: "preschool_records_v1"` and a `corpus` list of 16 strings. Each string has this already-supported boundary:

```text
Situation <apply-eid>; execution <execution-id>.
My measured action record: <verbatim admitted child output>
```

Use `train_adapter.child_record_prefix_length` and the **native tokenizer's** offsets with `child_target_mask`/`child_label_counts` to verify every encoded row. Existing trainer max length is 512; stop if any target is truncated, if prefix/padding receives a label, or if no causally supervised child token survives. Retain row-order/hash/source mappings and actual supervised counts. Exact action/outcome facts and parent ancestry belong in the side receipt; do not manufacture an improved target or add a supplied correct rule/quiz answer to the wrapper.

**No parent lesson bytes anywhere in corpus, even masked prefixes.** Exclude original parent messages, process/control packages, restatements, coached instructions, full parent-bearing prompts, generated parent briefs, and copied content-bearing lesson clauses inside child text. Merely excluding `kind="parent"` is insufficient. Check both full delivered payloads and substantive copied spans after whitespace normalization; audit clause-level echoes and reject ambiguous parent-derived restatements. Shared unavoidable syntax such as `TRY` is not itself a lesson. Exact scans cannot certify absence of semantic paraphrase; source timing and conservative content/claim checks must also establish that the admitted text is a record of an observed event, not advice rewritten as autobiography. Preserve rejected text unmodified.

Training interface: existing `organism_v6.train_adapter` with corpus, fresh staging out, rank 8, epochs 3, lr 1e-4 and seed 2, under the same pinned local `V6_MODEL`. This is **fresh-base fitting**, not adapter continuation or optimizer-state resumption. Do not pass v2.2 q/a corpora, invoke `train_adapter_v21`, switch to `train_adapter_v3`, or duplicate the SEQ091 objective. Omit the all-or-none formal gate-binding CLI quartet rather than fabricate a clean-lineage manifest; perform ordinary source and mask checks independently. In unbound mode the caller must reject every preexisting output path. Reuse staged promotion/lifecycle semantics and retain actual fit metadata, corpus/adapter hashes and DONE/failure artifacts. No base-weight changes.

The generic compiler and a waking brief are deliberately absent. The modern writer can train this schema already; the missing implementation is the small RuleGame record producer/selector and bounded orchestration, not a new learner.

## 7. No-write controls, visibility, and readout

- Both arms get the complete wake/parent/restatement experience. OFF cells skip all optimizer updates and load the exact same frozen base in fresh processes; they are genuine no-write baselines, not ON adapters with a nominal flag. Verify adapter absence. Because no other state survives, paired deterministic OFF outputs should match; a mismatch triggers identity/randomness/context diagnosis rather than a parenting interpretation.
- ON cells load only their own saved adapter on the same base after backend teardown. No parent prefix, restatement, wake ledger, recall store, sleep corpus, brief, inherited process state or model cache is available. Use the same neutral task instructions and post-outcome record instruction in all cells. Only within-current-task public TRY observations and the learner's own outputs may enter its next prompt.
- Before readout, use two disjoint actual-context canaries per cell, three ticks each, canonical ACT rate threshold .5 as in `format_canary`. Record the limited motor metric separately. If either ON canary fails, retain the failed adapter and canary outputs but do not promote it or run either ON scientific readout; record paired canary failure, not a zero-scored fabricated readout. OFF canary failure is an interface stop, not negative sleep evidence.
- Eight novel-rule readout tasks per completed cell; same IDs/seeds/order/action ceilings. Their TRY outcomes are legitimate online experience inside that task. Hidden rules/truth arrays, other tasks' outputs, aggregate sealed scores and evaluator notes are not learner/parent inputs. Evaluation post-outcome notes are readout measurements only, never a second sleep corpus.
- Report every task: valid quiz indicator; exact correct labels/6; valid/missing T/F predictions and Boolean agreement; protocol violations; unique TRYs; faithful notes per executed TRY and per allotted four opportunities; actual input/output tokens and durations. Prediction agreement is not a test of probe informativeness. Report source admission/formation separately from transfer.
- Primary exploratory transfer contrast: `(P_ON - P_OFF) - (A_ON - A_OFF)` on mean quiz accuracy over the same eight tasks. Also show both within-arm write contrasts and the raw four-cell table. A process-parent route requires supporting faithful-source and faithful-readout evidence, not quiz gain alone. No significance/population claim from eight tasks and one learner/training seed; no H1/H2, G3, retention, selective-writing or final-paper promotion from this scout.

## 8. Pre-implementation checks and stop criteria

When separately authorized, write focused CPU regression fixtures at these seams, without broad refactoring:

1. T and F actual world observations remain valid executions with reward zero; Boolean predictions come from the real pre-ACT output, not that reward. Strict malformed/multi-ACT handling prevents budget overruns while preserving raw output.
2. Arm-independent IDs give identical hidden rules/quizzes/seeds; training/readout/canary memberships are disjoint; six quiz labels are present. Quiz reveal is not scored; repeated quiz attempts cannot raise the endpoint.
3. Unique occurrence/execution/output joins, order, raw generation cardinality and identity; reject an orphan, reordered note, mismatched action/Boolean, copied lesson, unsupported rule, or evaluation-row sentinel.
4. A fake `admitted=True` cannot admit a failed/missing-quiz lesson or unfaithful note. Native `had_note`/`win` cannot bypass the new selector. Both arms must qualify before either fit.
5. Actual corpus bytes contain only the permitted wrapper plus raw child record; native-token loss-mask checks pass; rejected/teacher/quiz-label sentinels are absent even from masked input. New artifact paths and source/adapter hashes are immutable.
6. No-write adapter absence, ON identity, task-local retrieval, fresh process reset, parent/request/input-dose accounting, canary/readout separation, and all ceilings include control work.

Stop preparation on an unverifiable required source link, task-exposure collision, unavailable local model/tokenizer pin, unmatched declared parent input dose, malformed panel, teacher-answer/strategy leak in the active control, answer leak from P, ambiguous corpus echo, target truncation/mask failure, artifact conflict or missing control. No parent regeneration to obtain a better lesson; preserve the first result and stop the pair if its package violates the contract. Do not use global base authentication uncertainty to invent clean ancestry or secretly expand C11 work.

During any later authorized execution, stop at the earliest declared call/action/token/step/reservation/lease limit; a task-local malformed response ends that task, not a replacement opportunity. Stop the affected pipeline on identity mismatch, failed backend cleanup, trainer failure, nonfinite loss, corpus mutation or missing required artifact. Preserve partial work and both-arm status. No extra tasks, retries, rank/lr/epoch changes, one-sided fit, regenerated notes, amended labels, reinterpretation of failed gates or automatic extensions.

Normal negative outcomes are legitimate terminal results: paired material shortage; format failure; no quiz improvement; faithful records without transfer; transfer without faithful process evidence. Each localizes a different break in the chain. None authorizes another unbounded run.

## 9. What Main receives, and what remains to do

Integration choice is resolved: **dialogue skeleton + RuleGame evaluator + bounded batch-driver/Boolean-note adapter + explicit child-record JSON + current `train_adapter` + fresh four-cell readout**. No full `run_life_v2` Gym registration, generic sleep rewriting, new objective, replay shortcut, or new claim is required.

Main should first finish the current cumulative evidence cut and SEQ091's already-owned work. If Main later selects this scout, the implementation handoff is the five scoped seams in §4 and the regression cases in §8, with precisely the budgets and admission rules here. This document supplies no launch command and makes no readiness, GPU vacancy, completed-test, fit, or positive-result claim.

### Inspected source-byte anchors (SHA-256, no Git access)

```text
organism_v6/nursery_dialogue.py ca8da87a8b1b1980afcb95d97b36305cb2082612ca139565bb88ee6ee11cbb5c
organism_v6/rulegame.py 88304996b00837ad1855e8a6661aad39e64f3beb0c0ab4491b63119e797226f3
organism_v6/batch_loop.py 821471f4ddd136f64c7151a5fa0a4b1c2cc0d5be00c9febb73d5b215dccb7605
organism_v6/preschool.py 169168d6705514eb548a975de0f3d119b84194ce252089092983079d31af0303
organism_v6/run_life_v2.py 4d950036ce723b55e4e254bc1660944c111e7685992c11bad30ef526a4b90d03
organism_v6/train_adapter.py 9e39b6b6816f00ce2a78476f16e784daf31d7b26c673cbcddaf6ab508cf09caf
organism_v6/sleep_compile.py 73879a6c7da41be11cb9419182d8ca52ca07071b3b7a34b02ce5f793c163cb18
```
