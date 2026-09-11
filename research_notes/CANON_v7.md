# CANON v7 — the hard shell (2026-09-11, draft for Rohin's ratification)

## 0. What this is

v7's fixed boundaries under "hard shell, soft centre". Ratified as exact bytes, it supersedes SYSTEMS_BRIEF §4, CHILD_MECHANISM_v7 §9, Astra v2 §10 and BLEND §8; IDEAS.md rulings override it. Only this manifest controls; no transitive reference adds a rule. Run manifests cite this file's SHA-256 and bytes.

|input|bytes|SHA-256|
|---|---:|---|
|research_notes/SYSTEMS_BRIEF.md|19,764|090a5de76bf179fedfee112baac1087b19d7222936ab183da785b3e88c482ad0|
|research_notes/CHILD_MECHANISM_v7.md|91,511|36dcc552d5f3854de424728408e6fad4f2c93c752d86edf3dde18c52202406f0|
|research_notes/PARENTING_SCIENCE_SURVEY_v1.md|183,198|69a172bcd8654bc346d9a8984202fa26d4d95131f9dcc9d597956ea1c9001d31|
|research_notes/NEXT_EXPERIMENT_DESIGN_v2_ASTRA.md|83,487|9b9aafa3b15595a690cae2baae942d91c1f786017eb649bdd0bd1df4e0c55c36|
|research_notes/COLLABORATOR_BRIEF_v2.md|11,320|33fd4da132f6015b6e00942c462e94b3026e22c58826acd5185386b6329430c3|
|research_loop/plans/pcfl_c11_canonical_guard_spec_v12.md|11,394|2c1fd41aae8c851faf1a75142a955895c76720a26849c052fef1ba63c477ddd2|

## 1. Glossary (mechanical meanings, defined once)

- **Child**: frozen Qwen2.5-7B-Instruct plus trainable LoRA adapter(s). **Birth**: the lineage's first problem. **Life**: run from an empty ledger until stopped from outside.
- **Problem**: one gym task, ≤ 16 turns, ending only when solved or at turn 16 — no end word (IDEAS 09-10). **Turn**: one model call ≤ 400 tokens.
- **Interface**: the harness parses one `ACT:` line, no other marker; predicting, noting, recalling, perceiving are learned behaviours the instruments count.
- **Sleep / write**: training the adapter on the child's own text every 32 problems; cumulative from base (phase A), incremental with replay (phase B) only if P9 qualifies (conflict iii). **Writer**: the trainer. **Blocks** (8 + 32): pending conflict (i), P1b.
- **Canary**: 4 train-split problems × 6 turns, ≥ 3 scoreable. **Committed**: passed the brake.
- **Floor F_g**: best gate-exam score of any committed adapter, per gym, never lowered. **tol_g**: one noise width. **Strike**: confirmed score < F_g − tol_g. **Hold**: committed, not activated. **Fresh check**: re-exam at next probe.
- **Gate**: brake (canary; collapse = median tokens per unsolved exam problem < 0.5 × frozen) plus patience (three strikes → roll back).
- **Brief**: birth brief, own sleep summary, parents' ≤ 10 lines, read at **wake** (batch boundary).
- **Parent**: frozen external agent reading redacted records, writing briefs. **Room parents**: two Astra (inference-hub model) agents per gym, proposer and verifier. **Central parent**: Fable (this Claude session) and Codex (OpenAI CLI); advises, never blocks.
- **Clone**: one copy per GPU; never waits on a sleep or parent; writer one round behind; new adapter swaps in at the next batch boundary. **Lineage**: one adapter line and its clones; mechanism change = new lineage.
- **Gym**: exact-scoring environment. **Classroom**: trait-teaching gym; persistence first, its gym first (09-10 late). **Final test**: compiler gym, withheld from the lineage.
- **Guard** (Codex fix 2, defined once here): leak scan + provenance check before any training and before any clean or parented life; fails closed. Leak: hard parent markers refused anywhere, verbatim parent lines refused in target spans, brief echoes counted, parent text stripped. Provenance (Codex STOP): birth hash, parent-state hash, source set, mechanism version, exposure domains, no `QUARANTINE_TASK_EXPOSED` or unknown ancestor (guard spec v12 binds C11 only).
- **I_d_frame**: ON−OFF gain at the owner's completion frame minus that at a similar unseen id (**spill**). **Struggle test**: one write after hundreds of exposures to a failed family; ON vs OFF on new instances, sentence completion.

## 2. Boundary tables

### 2a. INFORMATION

|Actor|Boundary (sources: IDEAS 09-10 pin 3, 09-11 early; SURVEY rule 26; Codex fixes 3, 5)|
|---|---|
|Child|Own per-problem scores, outcomes, briefs, last 3 turns; never a parent metric, the structure reading, or that reflection is read.|
|Room parents|Redacted ledgers; reflections read, never quoted or graded; instruments as trends (counts until calibrated); gate decisions, reason codes, training outcomes yes; report and final-test scores never; gate-exam scalars open (§4).|
|Central parent|Same wall; notes only from a fresh context holding `agentic_parent.py`'s allow-listed read-only tools; the scheduling/analysis session never writes parental text; forbidden reads raise.|
|Fable / Codex|Fable sees everything, bound by the row above when parenting; Codex independently checks guard and evidence-to-claim.|

### 2b. AUTHORITY

|Actor|Boundary (sources: SYSTEMS_BRIEF §4.1–4.2; IDEAS 09-10 late, 09-11 early, 09-11 §2; SURVEY §3.2; Codex STOP ~857)|
|---|---|
|Write weights|Writer only, child-authored spans only; every child row kept, repeats included, no dedup or frequency cap; polarity tag open (§4); refuses on missing or failed scan; merges this lineage's clones only (birth manifest).|
|Block a clone or sleep|Nobody (lag-one asynchronous rounds).|
|Gate / roll back|Harness, automatically; never on report or test scores.|
|Curriculum|Room parents order and pace within the classroom set fixed at birth (reasoning-gym families; adding a gym = new lineage label); central parent re-ranks, advises; mechanism frozen.|
|Propose and launch|Central parent and Fable propose without asking; Fable launches within BLEND §6; no clean or parented life before the guard passes.|
|Kill; rent; ratify|Rohin kills any time, rents nodes, ratifies canon, guard, birth brief. Fable kills under 2d: default yes ("never ask permission"), Rohin to confirm.|

### 2c. EVIDENCE

|Claim|Decisive measurement, threshold, receipt (sources: IDEAS 09-10 late, 09-11; Astra §6, §9; v7 §8.15; Codex STOP; guard spec §2)|
|---|---|
|Existence|One lineage, internal controls (paired probes, repeated checkpoints, ON/OFF, untaught comparator); +0.020, interval excluding zero, permits "demonstration".|
|(a) Use memory|Prior [COORDINATION 09-11 06:50 (a); SEQ-034]: 19 lives, brief ≥ adapter 12; adapter > brief 0.034 at 512, one life. v7: frozen + own brief at 128/256/512 vs adapter, within node, ruler 0.027, proposed +0.020.|
|(b) Produce memory|Primary: ON−OFF slope 128→512, taught minus untaught ≥ +0.020, interval excluding zero, ruler 0.027 [SEQ-011]; secondary: entry level, tokens-to-target ≥ 10 % lower; receipt: probe files.|
|(c) Carry in weights|Primary: final adapter ON vs OFF, unseen gym, 128 problems, writes off, +0.020. Mechanism checks: I_d_frame > 0, interval excluding zero, spill ≤ 0.03; struggle test.|
|Persistence|Turns per problem and attempts after a non-improving outcome vs frozen; the brake is its floor.|
|TMEM delta|Page 1: TMEM = within-episode fast weights; ours = lifetime timescale, gated offline write, failure study, development.|
|Noise rulers|Replicate SD 0.0065, between-life SD 0.027 [SEQ-011]; ±0.015 band [SEQ-022/E:72]; reasoning-gym rep SD 0.06 [SEQ-027]; comparisons within one node.|
|NOT evidence / not claimed|Clean or parented children without a passed guard; one pair as population claim or "learns faster"; likelihood gain; echo counts; private reflection; 0.4878 / 0.5291 [SEQ-003], 0.2731 [SEQ-009; node 1]; anything beyond this lineage, horizon, gyms, base; C11 beyond supplied memory.|

### 2d. STOPPING

|Item|Boundary (sources: COORDINATION 09-11 02:50; IDEAS 09-10 late, 09-11; ruling 8 via v7 §3.3; v7 §5.11, §8.6; BLEND §6)|
|---|---|
|Deadlines|Machine 1's rental ends 09-14 16:14 PDT / 23:14 UTC, not extendable; parenting ends at the freeze (BLEND §7); GPUs, abstract 09-18; paper 09-25.|
|Preparation (Stage 0)|Format plus six moves on easy material; variants (a) brief, (b) brief + own-words rehearsal, (c) 60–100 content-free `ACT:` rows; P3 chooses; exit when each move is unprompted in ≥ 3 of last 8 problems, cap 160; others' thoughts out unless demonstrably strong; rows pass the guard.|
|Patience|Three consecutive confirmed strikes → roll back to best committed; parents told by reason code. Severe deficit committed and activated like any adapter; hold-and-fresh-check is D6 (§4). Mood-lock (repeated appraisal, actions unchanged) at ritual share ≥ 0.7 flags Rohin (0.7 *proposed*).|
|Horizons; pretests|Test lives to 512, censored at equal age; frozen read 128; pass rules per pretest in BLEND §6; missing support = inconclusive.|

## 3. Left to intelligence

- **Child**: everything inside a turn — what to think, predict, note, perceive, appraise; which hypothesis; its recall cue; when to act; how far to take advice; private reflection.
- **Room parents**: which mode, move, incident; when to fade; when to change the gym, not the sentence — within score-blindness and rules 20–26 as revised by no-nevers.
- **Central parent**: which experiments to propose; what to flag as "a script"; never blocks.
- **Fable**: scheduling, GPU allocation, analyses, pretest order — inside the tables; keeps every GPU and Astra busy, analysing rather than waiting.

## 4. Open decisions for Rohin (default if silent)

- **Parenting modes**: question, suggestion, demonstration, worked pattern, offered recipe (as opinion, never enforced, never verbatim across briefs, never the only option), varied (IDEAS 09-11 "no nevers"); V5 stems one mode; guard stays hard.
- **D6 severe-deficit hold** (≥ 5 × tol below floor: hold, fresh check): OFF until P8.
- **Polarity tag**: tag "this was wrong" rows, never exclude (no-cap), vs train all equally; decided in the struggle write (BLEND item 5).
- **Variant (c)**: not run; no result under the STOP until the guard passes (conflict vi).
- **Two children?** Two lineages if a third node is tested by 09-13 12:00 UTC, else one, "no replication".
- **Appraisal gym**: not this run; item 9 done, not above the topical-word control [AFFECT_LANGUAGE_PROBE_2026-09-11].
- Other decisions (v7 D1–D5, D7, D10 incl. stripped parent text; Astra §10; rule 21; panel v2 exploratory): defaults stand.

**Conflicts between rulings, unresolved:** (i) rank 32 from birth vs grow from 8 (09-11 early); (ii) gate decisions only (pin 3) vs parents see scores (09-11 early) — default no scalars; (iii) keep every thought, cumulative from base vs stop replaying everything; (iv) floor best-committed-ever (ruling 8) vs Astra's anchor; (v) moves by question only (IDEAS line 1514; rules 20–26) vs no nevers, recipe offered (line 1547) — confirm the later governs, rule 24 rewritten; (vi) no bootstrap (Decision 3) vs prepared first child with interface rows; (vii) keep every thought vs Codex fix 6; (viii) guard spec §7 human grant vs never ask permission — C11 only, or v7.
