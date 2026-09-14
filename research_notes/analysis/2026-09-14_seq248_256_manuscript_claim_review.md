# SEQ248–256 independent result-to-prose review — 2026-09-14

**Disposition: no high- or moderate-severity claim/evidence discrepancy found in the assigned reporting cut; two low-severity precision edits recommended. Ownership released.** This is not fresh whole-paper approval, permission to send the collaborator message, or a TeX/build verdict.

Reviewed immutable writing commit **`fa0fc2c0279089132a8f0e550586dabb26e26ada`**, committed **September 14, 2026, 17:42:31 UTC**, in exactly the six assigned manuscript/README/UNSENT/claim-map files. Applicable AGENTS/CLAUDE rules were checked. Only this memo was written.

## Severity findings and minimal fixes

### Low — repeated presentations are called “new targets” in four Markdown copies

Locations at the reviewed commit:

- `paper_prototype/astra_sprint_abstract_20260912.md:375`
- `paper_prototype/README.md:356`
- `research_notes/astra_memos/ASTRA_COLLABORATOR_DRAFT_2026-09-12.md:364`
- `research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md:5839`

“FULL presents800 new targets” can imply 800 distinct collected targets. There are **48 actual new targets and 800 presentations**, with 16–17 presentations per target. Surrounding text supplies the right counts, so this is a unit ambiguity rather than an inflated dataset result. The TeX wording at `paper_prototype/main.tex:701` already says “800 new-target presentations.”

**Minimal replacement:** “FULL makes 800 supervised presentations of the 48 new targets; control sees the same inputs with zero supervised new-target presentations.” No dose, result or recipe change is needed.

### Low — expand the compressed SEQ256 target clause once

Locations: `paper_prototype/main.tex:692`, `paper_prototype/astra_sprint_draft_20260912.tex:930`, companion abstract supporting notes `:367`, README `:348`, collaborator supporting notes `:356`, and claim map `:5831` (same paths as above).

The “at-least3/4 PROBE-pair and taught-graph requirements” clause gives the **correct failure verdict**, but compresses separate denominators and does not restate the complete conjunctive target. This is a clarity issue, not evidence that the target changed or either arm passed.

**Minimal clarification:** “FULL misses both separate thresholds: at least 3 of 4 PROBE pairs and at least 3 of 4 original-taught tasks.” For a self-contained target statement, add once in the detailed section: “The target requires at least 3/4 PROBE pairs, including at least one pair in each world; at least 15/16 old recall separately at W0 and W8 and at least 15/16 held audit; and at least 3/4 on each original-taught and previous-fresh graph.”

This matches `research_notes/analysis/2026-09-14_goal_pair_incremental_fit_design.md` and the released SEQ256 review. FULL fails PROBE pairs and original-taught tasks; control additionally fails both old wrappers and previous-fresh tasks. Both satisfy the per-world pair minimum and audit threshold. The existing “neither meets the target” conclusion needs no change.

## Result-to-prose mapping

Evidence filenames below are under `research_notes/analysis/`, prefixed `2026-09-14_`; `first_result` is the primary account and `independent_result` its released review. No raw-source audit was repeated.

| Claim | Evidence records | Finding |
|---|---|---|
| 248/249 remain failed connected readouts | `event_two_hop_first_result.md`, `event_two_hop_turnbound_first_result.md`, documenting their released independent reductions | All four conditions remain 0/4. 248 never exercises memory; 249 executes reads but has no goal arrival. Wrong argument typing is retained as an alternative to path-inference failure. |
| 250/251 support partial contextual goals, not robust composition | `event_two_hop_lesson_{first,independent}_result.md`; `event_two_hop_transfer_{first,independent}_result.md` | 3/4 taught and 3/4 fresh-identifier goals, versus no-write/original 0/4. Original receives third-party supplied context in 251; topology is unchanged. 250 task 3 wrong-goal dead end is correctly distinguished from 251 task 3 premature second-edge/no-commit failure. |
| 252 is a label ablation with unequal achieved retention | `event_two_hop_lesson_control_{first,independent}_result.md` | Old/fresh text goals 0/4 versus reused 3/4; old recall 11/16 per wrapper and audit 15/16 versus 16/16. Matching common labels and normalization is not equated with matching retention, optimizer trajectories or a purely isolated planning mechanism. |
| 253 connects exact parametric retrieval to action without beating the goal-blind counterexample | `event_two_hop_memory_{first,independent}_result.md` | Four facts, 16 repeated in-loop returns, 2/4 parametric/text goals. The primary records the CPU-executed first-port reference winning the same tasks 1/2. Post-hoc pairs decline from 1/2 at 251 to 0/2; they are not substituted for the original primary denominator. |
| 254 closes one failed repair, not all replay | `event_two_hop_memory_replay_{first,independent}_result.md` | Commands/outcomes remain unchanged; audit falls 16/16→15/16. Both writes fork from 37ec. Increased labels and changed six-row normalization are disclosed; no isolated additive-gradient or successful repair claim appears. |
| 255 is collection plus a partially goal-conditioned unchanged baseline | `goal_pair_collection_{first,independent}_result.md` | Zero fits; 48 coached targets are not new learned competence. Baseline 5/8 tasks and 2/4 strict pairs; no-memory 0/8. Prior opposite-goal teaching already existed in 250, explicitly acknowledged. |
| 256 separates TRAIN endpoints but ties PROBE with unequal retention | `goal_pair_incremental_fit_{first,independent}_result.md` | FULL 8/8 tasks, 4/4 TRAIN pairs versus control 3/8, 0/4; both PROBE 5/8, 2/4, matching baseline successful cases. No unassisted pre-fit TRAIN measurement is invented. Mixed retention and both target failures remain explicit. |

## Numeric and scope checks

- **Dose/state:** 250's 222 rows, 100 updates, 8,245 labels and 200 trajectory presentations agree with its review. 252 masks rows 210–221, with 5,977 active / 8,245 reference labels. 253 uses 254 rows and 16,175 labels; 254 adds 200 trajectory presentations, reaching 212 total and 18,443 labels. 256 uses 270 rows, masks only 222–269 in control, retains the original 12 trajectory targets, and reports 33,019 versus 23,885 active labels with the common 33,019 reference total. Its 4 presentations per legacy target versus 16–17 per new target are correctly described as a hypothesis, not a proved forgetting cause.
- **State lineage:** 207ad→37ec at 250; unchanged snapshots at 251; 252 starts 207ad; 253/254 start 37ec and end 9d36/52658b; 255 stays 37ec; 256 forks 37ec to fa3dec/2a8076. Prose does not claim these independent reviews reauthenticated live tensors.
- **Calls/cost:** stated counts agree with the released records: 248 has 8 collection plus 16 actor calls; 249 has 70 actor plus 16 native reader calls; 250 AFTER 147; 251 total 93; 255 32+48+96=176. SEQ256 reference totals are 239+232=471 AFTER calls. Its printed phase-wall sum is independently recomputed from the primary's rounded durations: 837.661+261.779+837.942+257.382 = **2,194.764 seconds**, or **0.609657≈0.610 A40-hours**. The text correctly labels this summed two-GPU phase time including overhead, not elapsed parallel wall or kernel utilization.
- **Cross-surface consistency:** main's SEQ248–256 section (`:352`) and sprint TeX's (`:590`) are byte-identical. All three active abstracts (`main.tex:246`, sprint `:373`, companion `:3`) are identical. The four detailed Markdown sections are identical after normalizing their relative evidence-link prefixes. All 16 linked primary/review Markdown records exist at the writing commit.
- **Claims/UNSENT:** active abstracts and collaborator message preserve the primary tie, retention differences, exposed-lineage/topology limitation and open H1/H2 status. No robust semantic goal-use, generic-planning, whole-life parenting or completed learning-efficiency claim was found in scope. Claim-map closing distinctions also preserve these limits. The b960/eight-world successor is proposal/implementation language **at this writing cut**, not an outcome; no later collection result is imported. The collaborator message remains explicitly **UNSENT**. This checks the prose label, not outbound-communication history.

## Review limits and release

Checks used local `git show fa0fc2c0:PATH`, line-numbered reads, comparison/regex scripts, local evidence-note reads, `git cat-file -e` for cited paths, and decimal arithmetic. No raw capsule inventory, source replay, ancestor reconstruction, model/tokenizer/torch load, GPU/remote/network call, experiment or current-collection inspection occurred. No TeX engine, PDF/layout, bibliography or whole-paper scientific review was performed. Earlier historical sections and unrelated claim families are outside scope. The result approves neither future outcomes nor a message send; it reports bounded result-to-prose consistency with the two small wording improvements above. **Only this memo was edited; ownership released.**
