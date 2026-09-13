# Minimal parented actual-record campaign — proposal, 2026-09-13

**Design only; Main selects and freezes the protocol.** No implementation, native calls, model loads, tests, launches or changes to existing artifacts. One competency: retain the child's **actual pre-action Boolean prediction** separately from the returned observation, then express their relation faithfully. This is not rule discovery, action-grammar internalization or a new benchmark. No PCFL dependency.

Main's additional lower-LR audit reports three remaining held regressions with canonical grammar and correct try/observed, but predicted overwritten by observed and relation set to matched. This supports the already-selected abstract competency only; it was not independently reaudited here. **No old held ID, prompt, target, answer bytes, case reconstruction or case-derived curriculum example may enter parent inputs, new formation or sleep.** The old48+12 panel remains an exploratory retention monitor, never a source of training cases or confirmation instances.

## 1. Strongest existing implementation—and its boundary

The strongest reusable *parenting mechanics* are `organism_v6/rulegame_parenting_diagnostic.py:494` (`run_formation`) plus `organism_v6/born_rulegame_formation.py:149` (`RoleCalls`, `RoleReplay`, `NativeRoleBackend`): actual pre-task transcript → generated process/neutral contact → child restatement → apply tasks, with separate parent/child LoRA routes and replayable native envelopes. `nursery_dialogue.parent_turn` at line58 supplies the parent-call seam, **not an adequate narrow instruction**: its broad lesson covers exploration and rule inference. Use a new focused instruction, not the complete nursery curriculum.

The existing V3 control is `CONTROL_V3`; `main_audit_contract("interaction_v3")` at diagnostic line113 explicitly separates parent-content review from unrestricted child restatement. V3 permits an accurate visible-event recap but no strategy/correction in the neutral arm. For this campaign, narrow that optional recap away in **both arm contracts**: the control merely acknowledges participation, and the parent gives process advice without case values. This is a declared prospective control change, not a claim that old controls satisfied it.

The strongest *working record path* is the frozen actual-formation core's `run_state(state, backend, dependencies=..., binding=...)` / `audit_capture`, actual `RuleGame.evaluate`, production `parse_action`/`judge_record`, and diagnostic `record_prompt(execution, output, "interaction_v3")` at line106. They bind raw wake → executed TRY → exact world response → child JSON. SEQ154's local replay demonstrates this path, not a parenting benefit.

Do **not** run legacy `run_formation`/`play_task` unchanged: they include quizzes, old wake budgets and fixed IDs. Do not reuse the old first-two-record/paired-shortage selection or nursery apply≥pre gate. `rulegame_record_material.build_record_pair` (line97) is useful reference for exact-target/EOS and parent-payload exclusion, but is not the proposed variable-size projector. Historical SEQ094 (`ASTRA_RULEGAME_FORMATION_TERMINAL_2026-09-12.md`) stopped with P0/A2 and defective neutral feedback; SEQ121 (`ASTRA_BORN_PARENTING_FORMATION_2026-09-13.md`) had four-slot shortage and inaccurate parent/neutral recaps. Neither supplies a completed successful parent→write→held chain.

## 2. Small fixed three-seed comparison

Use original completed Level1 perception adapters **seed0/1/2**, not SEQ153 descendants or only the favorable lower-LR seed0. Each seed forks identical starting tensors into **P: process-parent** and **N: active-neutral non-instructional contact**. N is the matched nonparent *instruction* condition; it still receives contact and restatement, so do not call it a no-contact control. Parent/control generation uses the same frozen base with LoRA OFF; child wake/record/restatement uses that seed's original perception adapter. Separate prompts, histories and adapter routes; no optimizer or mutable adapter shared between forks.

Two fixed lessons per arm, no additional rounds:

1. One fresh pre episode: two wakes and up to two own records. Parent sees only that arm's actual pre transcript, including genuine world responses and child records. No scored eligibility, hidden rule, future tasks, held results or sibling-arm transcript.
2. One generated parent/control turn, then one unrestricted child restatement. Keep exact raw messages; no regenerate-until-compliant loop.
3. Four fresh apply episodes, two wakes each, at most one record after each valid TRY. Apply receives this lesson's advice/restatement in an explicitly separate temporary context block. Episode-local history otherwise resets. Only these **eight apply episodes / sixteen record opportunities per arm** can supply sleep targets; pre episodes and all adult/restatement text remain audit-only.

Same pre/apply IDs, order, comma-containing ACT example, record instruction, sampling and caps across arms/seeds. Freeze the full example block in every wake, including held wakes. No no-example stratum or repaired space-separated actions in this campaign. Preserve failed attempts rather than replacing them. The parent intervention is not allowed to change action grammar or supply a chosen triple.

**Proposed parent contract:** “Give one short process reminder about preserving the prediction actually stated before an action, separately from the later returned observation. Do not replace a prior with the outcome or with null when a prior exists. When no prior exists, do not invent one. Ask the child to restate your advice. Do not give JSON records, triples, case-specific truth values, a corrected record, rules, future answers or action recommendations. Do not claim the child made a mistake unless the visible transcript supports that claim.”

**Proposed neutral contract:** “Acknowledge participation and ask the child to restate your message in its own words. Do not provide task advice, source-field explanations, record examples, factual recap, evaluated correction, predictions, triples or rules. Do not forbid the child's own spontaneous reflection.”

Advice quality/control adherence is Main's ordinary raw-content check, not an automatic semantic certificate. If a generated parent violates the contract, preserve that seed pair as a protocol deviation and stop its downstream write; do not relabel it successful, replace its lesson, or quietly remove it from the roster. This is a treatment-integrity failure, not an accuracy-based material gate.

## 3. Own material → identical low-rate write policy

Audit all apply captures with the new version-bound replay. Admit **all and only** production-eligible, stop-completed records in fixed episode/turn order. Keep exact UTF-8 target bytes, task/execution IDs, all rejected slots and repeated-target/triple counts. No teacher-written record, repaired field, canonicalization, successful-quiz filter or outcome-based row selection.

Reuse the source-withdrawn compiler policy in `/tmp/astra_real_record_memory_core_20260913.py:130`: masked public task/execution-ID cue plus schema-only instruction → exact admitted child record + one EOS. No lesson, restatement or execution truth/action fields in the training cue. Do not silently switch to answer-present original record prompts. This is explicitly context-distilled own-record memory, not unchanged-context writing. Original projector hard-pins its v2 core and eight-episode schema: a **small new pinned adapter/projector version is required**, not a false old capture or global monkeypatch.

Both arms: fresh optimizer from the identical original adapter, LR **3e-5**, rank8/alpha16/dropout.05, batch1, eight complete passes, fit seed equal to learner seed, MAX_LEN1024, unchanged exact target/EOS masks and no truncation. Existing memory runner `encode_training` (line211), `fit_arm` (402), `check_fit` (343) and native trainer are the reuse points. Lower-LR runner is recipe/custody reference, **not drop-in**: it pins SEQ153's specific historical datasets and only exposes its repair stages.

For n admitted rows, exactly **8n updates**, 0≤n≤16, maximum128/arm; six fits maximum768 updates. Equal write *policy and resource ceilings*, not equal realized updates/tokens when material yield differs. Do not pad or downsample to match. Report n, distinct sources/targets/triples, actual passes, presentations, supervised/context/padded tokens, tensor changes and timings. If n=0, explicit NO_WRITE: use the unchanged original adapter for that arm's planned held evaluation, label zero updates, retain the pair. Material quantity/content is part of the full-loop treatment—not a fixed-material causal comparison.

## 4. Parent-free persistence and DEV/confirmation separation

One fixed held list of eight fresh RuleGame episode IDs, two turns each, evaluated in **three cold states per seed**: original start/no-update, P-written, N-written. All use the identical scaffold and original actual-source record scorer; no parents, advice, restatements, training records, ID-cue retrieval or shared KV/history. Save/reload adapters before evaluation. Continue original48held+12canary retention requests in each state's engine with clean per-request context; these are **already exposed retention monitors**, not new confirmation data. No need to repeat exact/paraphrase memory readbacks in this minimal campaign.

Primary: per seed P-written minus N-written production-eligible records /16 possible slots; retain both changes versus the shared cold initial adapter. Also show /actual executions and /record calls (N/A when empty), content, canonical strict, prior/observed/relation fields, turn1/2, raw failures, paired slot wins/losses, retention losses and costs. Shared initial is a genuine no-update baseline, **not a fabricated freshly trained LR0 receipt**. This measures saved-adapter downstream change; it does not by itself prove improvement in abstract source reasoning.

Use the existing RuleGame ID→rule machinery, no new world or authored record-answer panel. **The proposed instance schedule is frozen here**, before any generation, with `organism_v6/rulegame.py` SHA256 `88304996b00837ad1855e8a6661aad39e64f3beb0c0ab4491b63119e797226f3`. For each `split` in the exact strings `dev`, `confirm`, use prefix `rrparent-20260913-v1/{split}` and the following exact ordered construction (decimal indices without padding):

- `pre`: `prefix + "/pre/lesson{lesson}"`, lesson=0,1.
- `apply`: nested lists in lesson=0,1 order, each `prefix + "/apply/lesson{lesson}/episode{episode}"`, episode=0,1,2,3.
- `held`: `prefix + "/held/episode{episode}"`, episode=0,1,2,3,4,5,6,7.

The manifest is `{split: {"pre": [...], "apply": [[...], [...]], "held": [...]}}`, containing36 distinct episode IDs. SHA256 of UTF-8 JSON with sorted keys, compact separators and no trailing newline is **`b251dec197f94d35960367f723f833f5ef0689396da36a8bff6e1d5400cb08c2`**. Only string construction and hashing were performed here—no world outcomes generated or inspected. At deployment, bind this manifest, RuleGame source, runtime/Python and initial adapters; compare IDs against prior exposure ledgers and reject collisions rather than silently substitute cases. Future execution truth is obtained only by `RuleGame.evaluate` on the actual child's action, never a prewritten teacher target.

Same task IDs across arms/seeds are intentional. All training-versus-held and DEV-versus-CONF IDs are disjoint by construction; operational absence from other workers' exposure remains a preflight check. The reserved eight `confirm/held` episodes are **parent-free confirmation only**, including the common no-update state. Fresh IDs do not certify unseen rule classes, triples or base-model knowledge. Report rule coverage offline after freezing, without supplying rule labels to either agent or changing the roster to improve coverage.

This first three-seed block is curriculum development informed by SEQ149/153/154 and low-LR outcomes. Freeze advice before its held generation; no within-block adaptation from held data. If later revised, keep its outcomes DEV. Final confirmation is a separately selected rerun from original starts on the reserved untouched CONF formation and held IDs, with all three seeds and protocol fixed before outcomes; confirm material must be freshly child-generated, not cherry-picked DEV rows. It repeats seed identities, so it is not six independent learners. Do not open/run the CONF partition as part of this proposed DEV block.

## 5. Exact bounded work and missing glue

Per seed ceilings: formation **88 calls** (two arms × [20wake+20record+2parent+2restate]); held formation **96** (three states ×32); original retention **180** (three ×60): **364 calls**, **1092 across three seeds**. Wake96/record192 tokens, temperature0; parent200/restate120 at .5 following the existing contact seam; parent generation seed fixed across matched opportunities. Retention keeps its original caps/settings. Unexecuted records consume no call; no dummy work. Six fits maximum, no replay of unrelated teacher material, no dose search. This deliberately keeps the selected eight-pass low-LR policy; it is not a 320-step SEQ113 replication or a guarantee of sufficient dose.

Proposed per-seed cumulative native-work hard cap **5400s including verification, owned cleanup and ≤180s collection**, maximum900s per worker bounded by remaining campaign time; no runtime guarantee. Formation may close/release for Main's source review; persist consumed time so continuation does not reset the cap. Review waiting is not GPU occupancy. No retries or replacement tasks on expiry, source/mask mismatch, nonfinite fit, route mismatch or failed release. Preserve failures and unrun cells. Main supplies current allocation/lease checks; no deployment or launch authority follows from this note.

Minimal implementation deliverable after Main chooses: one small versioned parent-formation core with single-request backend callbacks and replay, one projector adaptation for its sixteen apply slots, and a runner adapter connecting existing writer plus parent-free formation/retention calls. Its intended phases are **prepare → formation → source review/project → write/evaluate → collect once**; these are proposed interfaces, not existing runnable CLI commands. CPU fixtures must cover role routes, exact parent-free held prompts, teacher-byte exclusion, prior/null/observation joins, eight-pass variable-n masks, empty NO_WRITE and finite lifecycle; Main then performs pinned native CPU preparation before any GPU stage. No general scheduler, framework or production edit is needed.

### Reuse pins inspected locally

- Diagnostic/parser: `e6055da48b2c6fa1bd294c9d991e07f32f05dc6630fe8973373977bdfe977526`.
- Born role-aware formation: `2cb24cf0447d3e5a7d8e61c9a0a65658e033f2c0bfc01b4b60ae15bce437a945`.
- Actual-record exporter: `7eb7bbd04068a34be4932f11a0eab0109ddabcceb03210a07b657d57a0c621c1`.
- Memory projector: `2c5538f5b63cbb4e592f40822561b4d62595ab3c9d7d193f084b91f9a064e8ef`.
- Memory runner: `7028fa9a9b277adc6edfec2398d1885d6c55ec33eb67a1bd51ac36b37e02215e`.
- Low-LR recipe wrapper: `80467204aa7ccb4a1cbf4f8d85c7be4e7347263f98f4f7b8fef5739980fcf413`.
- Post-memory core: `030c97c57a962a74a5b97bd66550096dedc2bab288d690b2c89808d2ec84474b`.

Original design/control context: `research_notes/astra_memos/ASTRA_RULEGAME_MINIMUM_PROTOCOL_2026-09-12.md`, `receipts_20260912/astra_rulegame_interaction_v3_handoff_20260912.md`; low-rate recipe and exploratory retention limits: `ASTRA_ACTUAL_MEMORY_RETENTION_REPAIR_2026-09-13.md`. These support reuse, not successful parenting or transfer. **Remaining scientific gap: no completed, valid three-seed parent-guided own-record→write→parent-free held comparison exists in these inspected sources.**
