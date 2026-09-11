# CANON v7 — the hard shell (2026-09-11, draft for Rohin's ratification)

## 0. What this is

Ratified as exact bytes, it supersedes SYSTEMS_BRIEF §4, CHILD_MECHANISM_v7 §9, Astra v2 §10 and BLEND §8; IDEAS.md rulings override it. Only this manifest controls; no transitive reference adds a rule. Run manifests cite its SHA-256 and bytes; the input table is regenerated at ratification.

|input|bytes|SHA-256|
|---|---:|---|
|research_notes/SYSTEMS_BRIEF.md|19,764|090a5de76bf179fedfee112baac1087b19d7222936ab183da785b3e88c482ad0|
|research_notes/CHILD_MECHANISM_v7.md|91,511|36dcc552d5f3854de424728408e6fad4f2c93c752d86edf3dde18c52202406f0|
|research_notes/PARENTING_SCIENCE_SURVEY_v1.md|205,427|f49a3ef4e6e3ecb394aca147d40786a9fe91fa0609c2f7551542a39c5ca85ad6|
|research_notes/NEXT_EXPERIMENT_DESIGN_v2_ASTRA.md|83,487|9b9aafa3b15595a690cae2baae942d91c1f786017eb649bdd0bd1df4e0c55c36|
|research_notes/COLLABORATOR_BRIEF_v2.md|11,320|33fd4da132f6015b6e00942c462e94b3026e22c58826acd5185386b6329430c3|
|research_loop/plans/pcfl_c11_canonical_guard_spec_v12.md|11,394|2c1fd41aae8c851faf1a75142a955895c76720a26849c052fef1ba63c477ddd2|

## 1. Glossary (mechanical meanings, defined once)

- **Child**: frozen Qwen2.5-7B-Instruct plus trainable LoRA adapter(s). **Birth**: the lineage's first problem. **Life**: run from an empty ledger until stopped from outside.
- **Problem**: one gym task, ≤ 16 turns (xii), ending when solved or at turn 16, no end word (IDEAS 09-10). **Turn**: one call ≤ 400 tokens.
- **Interface**: the harness parses one `ACT:` line only; predicting, noting, recalling, perceiving are learned, counted behaviours.
- **Sleep / write**: the writer trains the adapter on the child's own text once per writer round (T_round, BLEND §7), lag one; phase A cumulative from base; phase B incremental with replay only via P9 (iii). **Blocks** (8 + 32): pending (i).
- **Canary**: 4 train-split problems × 6 turns, ≥ 3 scoreable. **Committed**: passed the brake.
- **Floor F_g**: best gate-exam score of any committed adapter, per gym, never lowered. **tol_g**: one noise width. **Strike**: confirmed score < F_g − tol_g.
- **Gate**: brake (canary; collapse = median tokens per unsolved exam problem < 0.5 × frozen) plus patience (three strikes → roll back).
- **Brief**: birth brief, own sleep summary, parents' ≤ 10 lines (SURVEY rule 28), read at the next batch boundary after arrival.
- **Parent**: frozen external agent reading redacted records, writing briefs. **Room parents**: two Astra agents per gym, proposer and verifier. **Central parent**: Fable and Codex; advises, never blocks.
- **Clone**: one copy per GPU; never waits; adapter swaps at the next batch boundary. **Lineage**: one adapter line and its clones; mechanism change = new lineage.
- **Gym**: exact-scoring environment. **Classroom**: trait-teaching gym; persistence first (09-10 late). **Final test**: compiler gym, withheld.
- **Guard**: row scan + provenance check before training and admission (2b); fails closed. **Row scan**: parent markers refused anywhere, verbatim parent lines refused in target spans (xi), brief echoes counted, parent text stripped. Provenance (Codex STOP): source receipts, parent-state hash, writer/compiler path, mechanism version, exposure domains, no task-exposed or unknown ancestor (guard spec v12: C11 only). **Leak rule** (parent moves): 2a.
- **I_d_frame**: ON−OFF gain at the owner's completion frame minus that at a similar unseen id (**spill**). **Struggle test**: one write after hundreds of exposures to a failed family; ON vs OFF on new instances, sentence completion.

## 2. Boundary tables

### 2a. INFORMATION

|Actor|Boundary [IDEAS 09-10 pin 3, 09-11 early; SURVEY 3.2 rule 7, rule 31; Codex fixes 3, 5]|
|---|---|
|Child|Own per-problem scores, outcomes, briefs, last 3 turns [v7 §1.1]; never a parent metric, the structure reading, or that reflection is read (ix, x).|
|Parent moves|No move that would score on an instance the child will act on; no scalar scores — scored-panel scores (gate exam, report, final test), instrument numbers (structure readings, Brier, meta-d′); not the child's own outcomes; verifier-checked (SURVEY 3.1 rule 11); the one absolute.|
|Room parents|Redacted ledgers; reflections read, never quoted or graded (x); instruments as counts until calibrated (BLEND 6b), then trends; gate decisions, reason codes, training outcomes, parental ledgers, rule-24 dependence trend yes; report and final-test scores never; gate-exam scalars (ii); calibration feedback (ix).|
|Central parent|Same wall; parental notes only from a fresh context with `agentic_parent.py`'s allow-listed read-only tools.|
|Fable / Codex|Fable sees everything, bound by the row above when parenting; Codex independently checks guard and evidence-to-claim.|

### 2b. AUTHORITY

|Actor|Boundary [SYSTEMS_BRIEF §4.1–4.2; IDEAS 09-10 late, 09-11; SURVEY §3.2; Codex STOP ~857]|
|---|---|
|Write weights|Writer only, child-authored spans only; every child row kept, no dedup or cap (xi); polarity tag (§4); refuses on missing or failed scan; merges this lineage's clones only (birth manifest).|
|Block a clone or sleep|Nobody (lag-one asynchronous rounds).|
|Gate / roll back|Harness, automatically; never on report or test scores.|
|Curriculum|Room parents order and pace the classroom set fixed at birth; a new gym enters the provenance record, not a new lineage [IDEAS 09-10]; central parent re-ranks. Six moves from Stage 0 (IDEAS 09-11 outranks Astra q8 §4); gym recipes: one bounded distinction until the carrier test reads (2c). No component gyms (a capacity drilled outside a scored problem [CONSTITUENTS §1]).|
|Propose and launch|Central parent and Fable propose without asking; Fable launches within BLEND §6; no life enters the lineage or counts as a result before the guard passes on its manifest; earlier lives are development (Codex STOP) until admitted (xiv).|
|Kill; rent; ratify|Rohin kills any time, rents nodes, ratifies canon, guard, birth brief. Fable kills under 2d: default yes.|

### 2c. EVIDENCE

|Claim|Measurement, threshold, receipt [IDEAS 09-10 late, 09-11; Astra §6, §9; v7 §8.15; Codex STOP; guard spec §2]|
|---|---|
|Existence|One lineage (two = first replication, §4), internal controls (paired probes, repeated checkpoints, ON/OFF, untaught comparator); +0.020, interval excluding zero.|
|(a) Use memory|Frozen+own brief at 128/256/512 vs adapter, within node, ruler 0.027 [SEQ-011], +0.020.|
|(b) Produce memory|Primary: ON−OFF slope 128→512, taught minus untaught ≥ +0.020, interval excluding zero, ruler 0.027 [SEQ-011]; secondary: tokens-to-target ≥ 10 % lower.|
|(c) Carry in weights|Primary: final adapter ON vs OFF, unseen gym, 128 problems, writes off, +0.020. Mechanism checks: cell F frozen gate (BLEND item 3 [COORDINATION 09-11 09:15], confirmation only); struggle test.|
|Carrier test|Precedes broad curriculum (BLEND §6 C): adapter-added benefit, lesson text absent, vs recipe-transmitting, neutral, OFF, frozen+own-text controls; lower CI > 5 pp (planning), harm ≤ 2 pp; interference/stability before widening; text-only = "contextual teaching".|
|Persistence|Turns per problem, attempts after a non-improving outcome, vs frozen; brake = floor. Grain of salt: uptake conditional on track record; disagreement then test (BLEND 6a).|
|Noise rulers|Replicate SD 0.0066, between-life SD 0.027 [SEQ-011]; ±0.015 band [SEQ-022/E:72]; reasoning-gym rep SD 0.06 [SEQ-027]; within one node.|
|NOT evidence / not claimed|Children without a passed guard; population claims; likelihood gain; echo counts; private reflection; 0.4878 / 0.5291 [SEQ-003], 0.2731 [SEQ-009]; TMEM-style fast weights [page 1]; anything beyond this lineage, horizon, gyms, base; C11 beyond supplied memory.|

### 2d. STOPPING

|Item|Boundary [COORDINATION 09-11 02:50; IDEAS 09-10 late, 09-11; ruling 8 via v7 §3.3; v7 §5.11, §8.6; BLEND §6]|
|---|---|
|Deadlines|Node 1 ends 09-14 23:14 UTC, not extendable; parenting ends at the freeze (BLEND §7); GPUs, abstract 09-18; paper 09-25.|
|Preparation (Stage 0)|Format plus six moves on easy material, stated then asked; variants (a) brief, (b) brief + rehearsal; (c) 60–100 content-free `ACT:` rows [v7 §4 (c)] not run (§4); exit when each move is unprompted in ≥ 3 of last 8 problems (provisional detector, BLEND 6b), cap 160; others' thoughts out of the rows unless demonstrably strong.|
|Patience|Three confirmed strikes → roll back to best committed; parents told by reason code. Severe deficit treated like any adapter; hold = D6 (§4). Mood-lock at ritual share ≥ 0.7 (*proposed*) flags Rohin.|
|Horizons; pretests|Test lives to 512, censored at equal age; frozen read 128; pass and admission rules per pretest in BLEND §6; missing support = inconclusive.|

## 3. Left to intelligence

- **Child**: everything inside a turn; recall cue; when to act; how far to take advice; private reflection.
- **Room parents**: mode, move, incident, fade; change the gym, not the sentence; within 2a and SURVEY 3.3 rules 20–32.
- **Central parent**: which experiments; flagging "a script"; never blocks.
- **Fable**: scheduling, GPUs, analyses, pretest order.

## 4. Open decisions for Rohin (default if silent)

- **Parenting modes**: SURVEY 3.3 rules 20–32; question default from Stage 1, stated-then-asked in Stage 0; modes varied, tagged; recipe as opinion, never enforced, not verbatim twice; leak rule the only absolute (2a).
- **D6 severe-deficit hold** (≥ 5 × tol below floor; re-exam at next probe): OFF until P8.
- **Polarity tag**: tag "this was wrong" rows vs train all equally; default tag; struggle write (BLEND 5) decides, else default.
- **Variant (c)**: not run under the STOP until the guard passes (vi).
- **Two children?** Two if a third node is tested by 09-13 12:00 UTC, else one, "no replication".
- **Stage 0 moves**: all six (default) vs four first (CONSTITUENTS §4).
- **Retrieval move** (start the canonical sentence): under "look again" (default) vs seventh named move.
- **Appraisal gym**: not this run (item 9 [AFFECT_LANGUAGE_PROBE_2026-09-11]).
- Other decisions (v7 D1–D5, D7, D10; Astra §10; rule 21; panel v2 exploratory; dependence trend; component gyms none): defaults stand.

**Conflicts, unresolved** (register; BLEND §8 mirrors):

|#|ruling vs ruling|default|BLEND|
|---|---|---|---|
|i|rank 32 vs grow from 8|two fixed blocks|C1|
|ii|parents see gate decisions only vs scores|no scalars|C4|
|iii|keep every thought vs stop replaying everything|phase A; B via P9|C15|
|iv|floor best-committed-ever vs Astra's anchor|the ruling|C10|
|v|question-only moves vs no nevers|the later (rule 24 v2)|C11|
|vi|no bootstrap vs prepared first child|(a)/(b); (c) not run|C3|
|vii|no-cap vs Codex fix 6|tag, never exclude|C2|
|viii|guard spec §7 human grant vs never ask permission|C11 only|C16|
|ix|no metric to the child vs no nevers|calibration feedback from own confidences and outcomes, no instrument number; structure readings hidden (information boundary)|C12, C9|
|x|private reflection never mentioned (09-10 night) vs no nevers (09-11)|keep: an information boundary (not knowing makes it private), not a mode|C17|
|xi|adopted recipe verbatim vs verbatim-line refusal vs no-cap|refuse only lines ≥ N tokens matching a parent brief; exempt the child's `ACT:` line with its outcome row; Codex tests|C13|
|xii|16 × 400 vs structured lengthening (IDEAS 1516, 1533)|16 × 400; brake reads length downward only|C8|
|xiii|freeze dated 09-11 vs the 09-11 rulings|re-dated to birth|C5|
|xiv|guard before any parented life vs pre-guard preparation (item 7)|2b's wording: development lives until admitted|C18|
