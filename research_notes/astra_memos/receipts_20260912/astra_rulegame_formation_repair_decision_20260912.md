# RuleGame formation repair — Main decision proposal, 2026-09-12

**Recommend a NEW paired formation: shared explicit relation definition; process parent versus non-strategic, fact-grounded conversational parent; no acknowledgment-only restriction on child thinking.** This is a proposal, not implementation, launch authority, or a claim change. SEQ095 remains `MAIN_DECLINED_MATERIAL`; neither its outputs nor SEQ096's diagnostic replacements become training material.

## Evidence key / exact bindings

Archives below are under `research_notes/astra_memos/receipts_20260912/`. `V` means member prefix `astra_rulegame_interaction_v2_20260912_attempt1/formation/data/` in `astra_rulegame_v2_formation_terminal_20260912.tgz`; `S` means `astra_relation_surface_20260912_attempt1/run/data/` in `astra_relation_surface_terminal_20260912.tgz`. Call citations refer to single-line JSON receipts, `.response.text` or `.request.prompt`, not generated paraphrases.

- **V archive SHA256:** `d3433cc22e398343bee59f755f2d2ac9dc5308347eba4ef421abdd76ae969ef8`; all 126 manifest-listed files verified; inspected local capture equals archive bytes.
- **S archive SHA256:** `acf05efb84c336b9afd3d495a81f37e43627d551dc4dd3999d5f8533353de2e0`; all 21 manifest-listed files verified.
- **Old decision archive SHA256:** `31c6483cf197777768a319ac7cbb2f9fd90a912f9128c4fd56af2acb59d1f27c`, `astra_rulegame_v2_material_decision_20260912.tgz!material/result.json:1`: `"status": "MAIN_DECLINED_MATERIAL"`.

## Four distinct findings

**1. Incorrect relations, not fabricated measured fields.** All 12 raw records preserve the actual TRY triple, observed Boolean and prior prediction/null. Eight nevertheless assert the wrong relation under the registered semantics:

| Actual prediction/observation | Wrong record calls, all emitting `matched` | Required label |
|---|---|---|
| false/true | P `0008,0023,0025`; A `0053` | `mismatched` |
| null/true | P `0012,0027`; A `0042,0057` | `unavailable` |

Raw citations: `V/calls/{listed ID}.response.json:1`; source execution/record pairs in `V/events.jsonl:7`, `:11`, `:22`, `:24`, `:26`, `:41`, `:52`, `:56`. Correct calls are P0010, A0038/A0040/A0055: P1/6 versus A3/6, first-two eligibility P1/A2. These wrong records remain unusable. Separately, P restatement0006 says **“if the task was to find the sum”** and gives 2+3+4=9: explicitly hypothetical, mathematically true, but not RuleGame evidence; not a fabricated observed result or a sleep target. P0005/0020's prediction-before-action guidance addresses actual omissions, not the relation-label definition (`V/calls/0005,0006,0020,0021.response.json:1`; omitted predictions at events:2/:18).

**2. Ambiguous instructions versus inability.** Original RECORD lists the labels only **“accordingly”** (`organism_v6/rulegame_parenting_diagnostic.py:73`). S supplies exactly:

> Explicit mapping: no prediction (null) => unavailable; prediction equal to observation => matched; prediction different from observation => mismatched.

`S/calls/0001,0004,0007.request.json:1` append this identical definition to the original actual-context prompts. Their raw full-JSON relations are respectively mismatched/matched/unavailable: **3/3**, versus fresh original-condition calls0000/0003/0006 **1/3**. Seed20260912, temperature0, JSON format and cap are matched within S. Token-only calls0002/0005/0008 score2/3, failing null again. This is bounded definition/interface evidence, not learning; it does not guarantee success at formation temperature0.7 or repair the historical responses. All three cases have positive observations.

**3. A parent summary is not automatically new strategy.** A0050 says **“You tried different combinations and got a quiz score of 0.83.”** Both facts appear in its input. A0035 reports predictions/combinations and score0.50, also already visible. Neither introduces a new prediction policy, probe, hidden rule or future answer (`V/calls/0035,0050.request.json:1` and `.response.json:1`). Its **“quiz ... needed more answers”** is a misleading summary of the earlier quiz-reveal `INVALID` message despite the subsequent scored quiz, not demonstrated new strategic teaching. These messages violate the *registered acknowledgment-only contract*; that historical rejection stands. Public training scores here are not sealed evaluation scores. Grounded recap could be admissible under a prospectively different active-control contract, but remains an attentional/recall intervention, not “no task information.”

**4. Do not conflate child reflection with parent instruction.** A0036 closely repeats A0035; A0051 says **“Your parent tried different combinations”**, a genuine actor-attribution error. These two traces do **not** demonstrate novel spontaneous child strategy; they show echoed recap and role confusion (`V/calls/0036,0051.response.json:1`). More generally, excluding A because its child independently reflects conditions acceptance on a post-intervention response. That is post-treatment purity selection, not necessary for an ordinary no-added-strategy parent control. Preserve spontaneous reasoning as behavior; still reject false/unsupported *training records* and prohibited copied parent/restatement prose in exported context/target. These are different criteria.

## Minimum NEW paired protocol / decision needed

1. **Keep task and exposure fixed:** existing RuleGame, paired P/A schedules, pinned base/lineage, two parent exchanges per arm, call/token budgets and preregistered seed/temperature schedule. No seed hunt, extra tasks, retries for nicer children, or replay-generated substitutes. First endpoint is paired material feasibility, not parenting efficacy.
2. **Share the exact S full-JSON definition** in every actual record request for both arms; retain emitted child action/output and public world outcome. No case-specific gold relation, future action, hidden map, record correction or token-only format search. Relation transcription is not the taught behavior.
3. **Prospective control contrast:** retain P process guidance. Let A acknowledge and, optionally, accurately recap already-visible experience, but prohibit new strategy, hypotheses, recommendations, evaluated corrections and invented facts. Use the same ordinary restatement request in both arms; remove A-only “no reflection/what you learned” restrictions. Audit what the parent supplied separately from what the child generates. Main must explicitly accept this active-control estimand before implementation; it is not a relabeling of old A.
4. **Preserve eligibility/export:** unchanged first-two eligible distinct records per arm; report every failure. After that fixed selection, exporter failure/shortage rejects the pair—never search later for exportable replacements. Main's explicit context/target assessment remains required. Sleep only the complete own raw record+EOS under its actual masked request, never lesson/restatement prose, even in masked context. Any later write/readout retains matched P_ON/A_ON and shared OFF, fresh parent-free reload and existing sealed-score blindness.

**Concrete integration blocker:** the current replay and exporter reconstruct the old literal RECORD prompt (`rulegame_parenting_diagnostic.py:444`; `rulegame_record_material.py:119`, `:172`). Simply appending S's mapping will fail them. Main must commission a small, explicitly versioned prompt/replay/export-context integration that preserves old protocol replay and all byte/selection/faithfulness checks; no global replacement, synthetic fallback or relaxed equality. It has NOT been implemented or tested here. Current exporter SHA256: `83e8c264c81578b13da82366a2c1dbb8c92cf29792338c02bc68da41440c8b6d`.

**Main decision requested:** accept/reject the new A-parent contract and unrestricted child-restatement criterion, plus the common mapping/versioned integration scope. No new reviewer/human launch gate is proposed. Only this note was written; no code, Git, network, native/model/GPU run or training occurred. **EDITSTOP / no repository ownership.**
