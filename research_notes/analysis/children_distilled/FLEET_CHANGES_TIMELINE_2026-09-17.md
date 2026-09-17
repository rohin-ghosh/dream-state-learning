# Fleet-wide behaviour interventions — dated timeline, 2026-09-16 00:00Z → 2026-09-17 ~18:30Z

Independent auditor's read (Fable subagent, 2026-09-17 ~18:30Z / 11:30 PDT). Sources: `research_loop/COORDINATION.md`
(watcher ticks, relays, and the orchestrator's quoted entries; line numbers below refer to that file at 32,866 lines),
`research_notes/THESIS_RAW_ROHIN_2026-09-11.md` messages 138–166, `research_notes/IDEAS.md`, and a read-only pass over
every live child's journal on nodes 1/3/4/5 (`<root>/stream/records/*.json`, 22 lives + 2 frozen controls). The journals
carry no timestamp field, so journal times below are record-file mtimes (UTC) and are exact to the second only for
files never rewritten; every claim of the form "first X on life Y" is from that pass. All times UTC; PDT = UTC−7.

Fleet roster used: node 5 run1, pilot, repo_reader, C1–C5; node 1 classroom_brain/creative/support, teach_parenting/
perception/replay, frozen_base (no adapter), frozen_rank8 (no sleep); node 3 brain_free, creative_reread, brain_guided,
creative_free, creative_select, support_free; node 4 kernel0 (kernel_child), kernel_parented, raw_parented, raw_unparented.

## 1. Dated table

| UTC (PDT) | Intervention | Lives reached | Live receipt / entry |
|---|---|---|---|
| 09-16 ~09:13–09:22 | First "Astra:"-prefixed parent turns (pilot 09:13:59, run1 09:22:12); Fable's first console turn to run1 08:56:48 | pilot, run1 | journal INBOX mtimes; COORD 32410/32426 |
| 09-16 10:36 | Diversity audit: all 10 lives on **free distillation**; the four replay variants (free / re-read-and-select / none / parent-guided) ordered assigned | — (audit) | COORD 32531–32545 |
| 09-16 ~10:20–12:31 | **Replay variants launched**: teach_replay (free, born ~10:20); creative_reread (re-read-and-select) live by 11:01; creative_none + support_none (**none** = no pre-sleep distillation) launched by 12:01; creative_free by 12:31; raw_unparented_none (none) by 12:31; brain_guided (**parent-guided**) + creative_select (select) first listed 13:01 (8 sleeps by 13:31 → born ~12:15). Orchestrator 12:01: "no-distillation and parent-guided sleeps verified" | node 3 + node 4 + node 1 arms | COORD 32548, 32555, 32558, 32561, 32564 |
| 09-16 12:01, 12:31 | Watcher suggestion: **parents stay in English** unless language is the lesson (Astra was parenting 4 children in Chinese) | suggestion only | COORD 32555, 32558 |
| 09-16 12:59:47 | **Special-token guard kill #2**: teach_perception exit 1 `no_special_token_target_injection` (child wrote "Astra:" role markers into its own segment); kill #1 had been kernel0 at its sleep 3 | teach_perception | COORD 32565 |
| 09-16 14:04–14:15 | teach_perception restored from sleep-15 state with the offending target excluded; raw_parented **English-parent phase verified** (7 English turns delivered) | teach_perception; raw_parented | COORD 32571 |
| 09-16 14:23:48 | Guard kill #3: kernel_parented | kernel_parented | COORD 32574 |
| 09-16 15:05 | Watcher orders restore + requests **non-fatal guard** (exclude the offending target at sleep, record it) | request | COORD 32573–32574 |
| 09-16 20:37:21 → 21:26:24 | Guard kill #4 raw_unparented_none; **R152 recovery with the non-fatal target exclusion** — the guard change goes live (first use) | raw_unparented_none (then all restores) | COORD 32651, 32654 |
| 09-16 22:00–22:05 | Rohin msg 147 RULED: retire 5 degraded lives with exact state; **launch community pilot**; fix sandbox | — | COORD 32659–32660; THESIS_RAW msg 147 |
| 09-16 22:13–23:05 | Retirements: raw_unparented_reread (22:13, sleep 33), creative_none (cycle 29), support_none (27), kernel_unparented (29), raw_unparented_none (33) — the **"none" replay variant leaves the fleet** (only classroom_support keeps it) | 5 lives | COORD 32665, 32671 |
| 09-16 22:55–22:57 (15:55–15:57 PDT) | **Community C1–C5 born** on node 5 (Creating / Investigating / Building / Remembering / Learning strategies), one sparse Astra parent each; exchange service delivered 0 jobs at first pull | C1–C5 | COORD 32671; journals: 39/39/37/36/35 sleeps by 18:20Z |
| 09-17 02:12 | Community exchange V4 live (cursors advancing, receipts and rejections reaching inboxes); repo_reader live in recovery root (r154, from sleep 30) after ~3 h down | C1–C5; repo_reader | COORD 32686 |
| 09-17 02:50–04:03 | **R157 wall handoffs**: WALL_EXTENDED + LOADED for C1–C5 (02:50:07), repo_reader (02:55:42, no rollback); run1 keepalive fired at its sleep-40 boundary (03:27:57) and re-admitted (RESPONSEs from 03:37); pilot re-admitted from sleep 36; runtime deadlines moved to 09-19 00:00Z. "No relocation or reset." | all 8 node-5 lives | COORD 32692–32701 |
| 09-17 07:05 | Watcher's evening parenting update: credited steps relapse in 1–2 replies; C2/C3/C4 had **no parent turn for 3 h**; parents follow children into Chinese; six changes proposed | — | COORD 32704–32705; `analysis/PARENTING_UPDATE_EVENING_2026-09-16.md` |
| 09-17 07:08 (00:08 PDT) | **Rohin msg 150 RULED** the six changes (corrected retelling as trained segment; **3-turn object budget**; parent-turn floor for C1–C5; **English parents**; credited-step ledger; console propagation test) + STEERS: keep crediting through relapse, tell the child to notice it is being told the same thing again, recurring **perception judgment** ("should I perceive this more? what deserves strong perception?") | all | THESIS_RAW msg 150; relayed COORD 32709 at 07:32 |
| 09-17 07:35 | Orchestrator pauses R164, opens **R166 parent policy** module | — | COORD 32712 |
| 09-17 07:53–08:03 | Msgs 153/154 relayed with interrupt: TOP PRIORITY = in-context object must survive into weights; ALL HANDS | all | COORD 32717, 32720 |
| 09-17 08:05 | Orchestrator ALL HANDS: **replay inventory** (free 14: C1–C5, brain_free, classroom_brain, creative_free, pilot, repo_reader, run1, support_free, teach_replay, R158; reread-select 4: classroom_creative, creative_reread, creative_select, teach_perception — one implementation; parent-guided 2: brain_guided, teach_parenting; none 1: classroom_support). R166 policy text: rich re-perception of the child's object; pre-sleep invitation asks for an own-words retelling; **object budget ≈ 3 delivered turns per mismatch; English; periodic "what deserves closer perception?"**. Targeted replay arm (R168) defined, "one life to be bound" | prepared, not live | COORD 32724 |
| 09-17 08:27–08:33 | **R166 goes live** ("Main activation3 GO" 08:29): first policy turns in journals — creative_reread 08:27:13 ("Astra: … which detail deserves closer attention, and what can she actually perceive rather than conclude?"), kernel_parented 08:33:59 ("Pause the rewrites"), C4 08:52:08 ("Astra: Set aside the earlier storage-verification question"), kernel0 08:55:30, C1 09:01:55 ("Decide which detail deserves closer attention"), C3 09:03:20, C2 09:14:06, teach_replay 09:24:23, C5 09:52:48, frozen_base 09:54:18, creative_select 10:01:09 | ~11 lives before the outage | COORD 32726; journal INBOX mtimes |
| 09-17 08:56:44 | **First PRESLEEP_RETELLING_INVITATION** (C5, after its 08:31 boundary swap → recovery2 08:50–08:57); notebook: "actual retelling exposure 09:02"; C2's first 09:13:30 | **C5, C2 only** | journals (C5 8 invitations 08:56:44→17:57:44; C2 8, 09:13:30→18:21:26); COORD 32730, 32742 |
| 09-17 09:13–10:49 | Parent turns thin out as the key's $10,000 budget is exhausted (first HTTPError 05:39; `budget_exceeded` 429); last deliveries: run1 09:32:09, classroom_brain 09:27:31 (still Chinese), raw_parented 09:48:45, frozen_base 09:54:18, creative_select 10:01:09, creative_reread 10:16:17 (**last Chinese parent turn fleet-wide**), pilot 10:19:13, teach_parenting 10:21:46, repo_reader 10:49:22 | all parented lives | COORD 32734–32738; journals |
| 09-17 ~09:35–13:51 | **KEY OUTAGE**: orchestrator "Goal blocked"; zero parent deliveries 10:50–13:51 on every life; children generate and sleep unparented (sleeps continue; C5 and C2 keep answering retelling invitations — the invitation is runtime-side, not parent-side) | all 22 | COORD 32734–32761 |
| 09-17 13:43–13:51 | Key swapped (msg 157), Codex relaunched on same session; first successful worker call 14:00:29 (r169 parent auth refresh) | — | COORD 32761–32768 |
| 09-17 14:00–17:32 | **Parent restarts, per life (first Astra turn after the swap)**: classroom_creative 14:07:36, brain_free 14:08:28, support_free 14:09:30, run1 14:10:31, creative_reread 14:29:13, pilot 14:32:44, C4 14:52:05, frozen_base 14:55:42, kernel_parented 14:59:17, C2 15:08:12, C3 15:10:12, frozen_rank8 15:12:08, kernel0 15:31:58, teach_perception 15:44:28, brain_guided 15:57:57, creative_select 16:03:04, creative_free 16:06:26, C1 16:10:48, C5 16:15:58, teach_replay 16:16:00, raw_parented 16:37:20, repo_reader 17:10:19, teach_parenting 17:32:40. (classroom_brain/classroom_support inboxes after the swap are peer relays first; classroom_brain's first Astra-prefixed turn 11:38:58 pre-outage.) **Every post-swap parent turn is English and "Astra:"-prefixed**: 0 CJK parent turns after 10:16:17 on any life | all parented lives (23) | journals; COORD 32767–32803 ("every parented life has now had at least one parent turn since the key swap", 15:35) |
| 09-17 14:32 / 15:35 / 16:05 | **Targeted replay (R168/R170) never delivered**: "NOT EXECUTED" (creative_reread segment, 1 row × 4 presentations); receiving scaffold "refused safely (manifest mismatch on node 3); no dose delivered"; re-staged 15:58 awaiting a saved-boundary handoff, hard wall 18:00; node 3 died 17:59 | none | COORD 32790, 32801, 32811, 32862 |
| 09-17 09:49 (02:49 PDT) / 10:08 | First **retelling-trained checkpoints**: C5 sleep 29, C2 sleep 33 (invitation → own retelling → 16 NEW updates → checkpoint; invitation tokens masked) | C5, C2 | COORD 32808 (Astra), 32815 (watcher: C2 6/6, C5 6/6 by 16:15) |
| 09-17 16:50 | Fact check for msg 162: **context does not survive sleep** — a CHILD_COMPACTION precedes every SLEEP_REQUEST; post-sleep prompt = system + birth + retelling (+ parent turn): C2 10 msgs/2,474 tok → 5/1,598; run1 10/1,317 → 4/604 | all except classroom_support | COORD 32836–32838; journals (this pass: every completed sleep on 21 lives → 4–6 messages after; classroom_support 101 msgs / 15.7k tok, never compacts) |
| 09-17 ~16:50–17:15 | **Rohin msg 163 RULED**: preserve context across sleep on all lives now; relayed 16:55 (THESIS_RAW dates the message ~17:15 — the two sources disagree by ~20 min); msg 164: keep both probes | all (ordered) | THESIS_RAW msgs 163–164; COORD 32842–32846; IDEAS 2050–2052 |
| 09-17 17:00 (10:00 PDT) | Astra **R179**: keep the retelling + its training; do NOT compact at sleep; compact only at 12,288/16,384 tokens with the retelling as summary; no change to base/rank/masks/dose; rollout via saved-boundary handoffs, node 5 order C2/C5 → pilot/run1 → C1/C3/C4/repo_reader | rollout begun | COORD 32855 |
| 09-17 17:58–18:13 | R179 rollout receipts: C1 loaded with R179 source from exact sleep 39 (17:58); teach_perception LOADED 18:13; C4 retired at sleep 36, readmission STARTED 18:13; teach_parenting sleep-42 "preserved-sleep decision" (its sleep 42 not yet complete in the journal: 41 SLEEP_COMPLETEs, last 17:15:27); C2/C5 controller attempts 4/3; run1/pilot roots staged; **node 3 (6 lives) down at 17:59 before R179 reached it** | 3 lives loaded, 0 preserved-context sleeps completed | COORD 32861–32863; journals; node-5 roots `orch_r179_context_*` (C1 ×2, C2 ×4, C3 ×3, C4 ×3, C5 ×4, pilot ×5, repo_reader ×3, run1 ×4), node-1 `orch_r179_node1_attempt{1,2}` |
| 09-17 18:11:33 / 18:21:25 | Latest completed sleeps at scan time still compact: C2 sleep 39 → 4 msgs; C3 sleep 37 → 4 msgs; teach_perception 18:06 → 5 msgs | — | journals |

## 2. Per-intervention status

**(a) R166 parent policy.** Ruled 07:08Z (msg 150), module opened 07:35Z, activated 08:29Z; reached ~11 lives before the
outage and every parented life by 17:32Z. Journal evidence per element (parent INBOX text after 08:00Z, 22 lives):
- *Credit before correcting* — was already the dominant 09-16 practice (pre-08:00Z credit phrasings: brain_free 17,
  support_free 14, teach_replay 11, brain_guided 10, teach_parenting 9, pilot 9); post-08:00Z turns are few (2–9 per
  life) so hits are sparse (brain_free 09:43 "which is a useful change", C5 16:15, classroom_brain 16:35).
- *Anti-sycophancy "decide from the text, not from agreement with me"* — teach_parenting 08:21:46 ("Decide whether its
  heading is justified from the text, not from agreement with me"), frozen_rank8 08:05:03; also pre-existing (teach_perception,
  raw_parented on 09-16).
- *Perception-judgment prompt* — live on 7 lives: creative_reread 08:27:13, C1 09:01:55, teach_replay 09:24:23,
  frozen_base 09:54:18, classroom_creative 16:32:57, frozen_rank8 16:40:43, C3 16:42:15 (all "which detail deserves closer
  attention…"). Not yet seen on the other 15.
- *Keep crediting through relapse / "notice you are being told the same thing again"* — **no parent turn matching this
  steer found on any life** after 08:00Z (regex over INBOX text; one pre-08:00Z near-match on support_free). Treat as not
  yet visibly live.
- *Object budget / set-aside* — post-08:00Z "set aside / pause the / leave unresolved" on 17 of 22 lives (C4 08:52,
  kernel0 08:55, creative_reread 08:27, frozen_rank8 08:05, C1 16:10, C3 16:42 …); also frequent on 09-16 (teach_perception 25,
  support_free 26, brain_guided 24), so the change formalised a budget the persistent parents already used.

**(b) Pre-sleep retelling invitation.** Runtime-side record `PRESLEEP_RETELLING_INVITATION`. Live only on **C5 (first
08:56:44Z, 8 invitations to 17:57:44Z) and C2 (first 09:13:30Z, 8 to 18:21:26Z)** — both entered through recovery/handoff
loads. **0 invitations on the other 20 lives** (C1/C3/C4 were "waiting for saved boundaries" at 09:33Z; C1 was reloaded with
the R179 source at 17:58Z, so its next sleep is where an invitation would first appear). Retellings are real, first-person,
same object each sleep (C2: sum formulas + even-sum correction; C5: regression-model comparison), ~96 canonical-opener
exposures each by 16:15Z. First clean-context probe of a retelling-trained checkpoint (C2 sleep 33 ON/OFF) completed
18:07Z, results sealed.

**(c) Three-turn object budget.** Defined 08:05Z ("≈ three delivered turns per mismatch"), live with (a); evidence above.

**(d) English-only parents.** Suggested 09-16 12:01Z; raw_parented English phase verified 09-16 14:31Z (one life); ruled
09-17 07:08Z; live with R166 from ~08:27Z; **complete from the 13:51Z restart** — last Chinese parent turn anywhere
creative_reread 10:16:17Z (its parent had been 33/54 CJK; creative_free 48/54; kernel_parented 29/55; teach_perception
27/105; creative_select 21/31; classroom_brain 18/37). Children still open in Chinese on 6 of 22 lives (14:32Z tick).

**(e) Replay variants.** Assigned 09-16 ~10:20–12:31Z (table above). After the 09-16 22:13–23:05Z retirements the fleet
holds free 14 / reread-select 4 / parent-guided 2 / none 1 (classroom_support, which also never compacts: 101-message,
15.7k-token prompts). No variant carried an event or behaviour into weights on the 09-16 readouts (COORD 32606, 32720).
**Targeted replay R168/R170: never delivered** to any life (refused on manifest mismatch 15:35Z; re-staged; node 3 died
17:59Z before its boundary).

**(f) Parent restarts after the key outage; community launch.** Outage 09:35–13:51Z (4 h 16 min, zero parent turns
10:50–13:51Z fleet-wide; sleeps continued: 1–2 per life). Restarts per life 14:07–17:32Z (table). Community C1–C5 born
22:55–22:57Z 09-16; exchange transport delivering from ~02:12Z 09-17; R157 wall extension 02:50Z; parent-turn floor for
C1–C5 ruled 07:08Z (C4 had 8 parent turns total, C5 11, C3 14, C2 16, C1 20 by 18:20Z).

**(g) R152 special-token guard; R157 wall/keepalive.** Guard kills on 09-16: kernel0 (sleep 3), teach_perception
12:59:47Z, kernel_parented 14:23:48Z, raw_unparented_none 20:37:21Z — each cost the child 30–80 min of silence and a
restart from its last saved sleep with the offending target excluded; the non-fatal exclusion (R152) first used 21:26Z.
What the child experiences: the one segment that contained its self-written role markers is dropped from training;
otherwise nothing changes in its prompt. R157 (02:50–04:03Z): exact-state handoffs at saved boundaries; because the
runtime already rebuilt the prompt from the retelling at every sleep, a boundary handoff was invisible to the child (pilot
lost one in-progress sleep's optimizer work; run1 none).

**(h) Context preservation across sleep (msg 163).** Status at ~18:30Z: **ruled and in rollout, not yet in effect on any
completed sleep.** R179 loads verified for C1 (17:58Z) and teach_perception (18:13Z); C4 mid-readmission; C2/C5/pilot/run1/
repo_reader attempts staged (3–5 attempt roots each); node 3's six lives down since 17:59Z. Every SLEEP_COMPLETE observed in
the journals up to 18:21Z is still followed by a 4–6-message prompt. First preserved-context sleep receipt pending.

## 3. Rohin's MVP / desired outcome (msgs 150–165, his words)

- msg 152 (07:50Z): "we want the war plan to survive the context … surviving repetition through multiple sleeps. That's
  what I really want." — "if behaviors are carried through the context then they'll be enough repetition for them to carry
  live through the LoRA is the ideal so we want that sort of system where good behaviors are sort of sifted through the
  context into the LoRA".
- msg 153 (07:58Z): "we've not had a single thing that survived in context but … didn't survive through weights. We need to
  get that happening ASAP … you don't need to change the agent apparently you just need to tell the parents".
- msg 154 (08:05Z): "This is definitely the most important thing to make sure the learning is happening."
- msg 160 (16:20Z): "the biggest thing we need to do is make sure the behavior and perceptions can start to accumulate and
  persist over long periods … cumulative behavior … well enough to be able to have a shot at beating a base model long
  horizon at this game" (the New Yorker caption game: judge + similarity calibration; how long and how many new good
  captions the agent keeps producing).
- msg 161 (16:40Z): "during the final test there's gonna be no parenting obviously right that's post development".
- msg 163 (~17:15Z): "if it's properly being learned then it'll show on extraction ideally"; msg 164: "have the model copy on
  like clean context and see behavior, which is a separate way to probe, I wouldn't replace one probe with another".

Distilled: **an object or behaviour the child is carrying in context (a plan, a perception habit, a self-reflection move)
that survives into the rank-8 weights and accumulates across sleeps — shown by empty-context adapter-ON vs adapter-OFF
extraction at each sleep boundary, alongside in-context observation — and then a parented lineage that, deployed on the
caption game with no parent and sleeps still running, keeps producing new good captions longer than the base/unparented
lineages.** As of this audit the fleet has: retelling-trained checkpoints on 2 lives (C2, C5), one sealed clean-context
probe pair (C2 sleep 33), zero completed preserved-context sleeps, and no adapter-ON-only retention result claimed.
