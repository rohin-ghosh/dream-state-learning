# PARENTING MENU — v6 nursery variants (literature-mined, 2026-09-07)

A menu of teaching methods from human learning science and ML, each translated
into a concrete variant of the Phase-1 lesson cycle
(`nursery_dialogue.py`: play → parent corrects PROCESS → child restates →
apply on a fresh task → world admits iff post ≥ pre → sleep-compile → LoRA).

**Ordering**: by expected value ÷ cost for a first parallel screen.
**Contamination rule (all variants)**: target-blind. Parents teach only on
rule-games / curriculum readings; no compiler content, pass names, or scores
anywhere in teaching material. The existing curator grep firewall applies to
every new prompt and reading introduced by a variant.

**Shared instruments** (what "sticking" means):
- **probe-Δ**: parent-absent held-out rule-game panel, adapter ON−OFF mean quiz score
- **admit-rate**: world-admission rate trend across lessons (learning-to-learn signal)
- **calib**: |PREDICT − actual| on probe streams (Brier-style, from ledger)
- **notes-q**: scoped-note fraction + `behave` assay (predict-before-act, n_scoped)
- **canary**: canonical-marker density on probe streams (format integrity gate)

Cost is GPU-hours relative to the current 12-lesson scout (≈ one A40 for a
few hours): **cheap** ≈ ≤1.2×, **medium** ≈ 1.5–3×, **expensive** ≈ >3×.

---

## 1. Contingent scaffolding / ZPD (Wood, Bruner & Ross 1976, J. Child Psychol.; van de Pol et al. 2010 review)
- Core finding: tutoring works best when help is *contingent* — more directive
  after child failure, less after success, fading as competence grows. One of
  the best-replicated results in tutoring research; the human ITS analogue
  (step-based tutors ≈ human tutors, VanLehn 2011) is solid. No direct LLM test.
- Nursery variant: `parent_turn` receives the child's recent admit history and
  a 3-level directive ladder: after an admitted lesson → ask one question only;
  after one failure → name the mistake category; after two consecutive
  failures → state the correction plainly with the reason. Ladder position is
  harness-computed from `results[]`; parent prompt is otherwise unchanged.
- Sticking metric: admit-rate slope (contingency should bend it up mid-run);
  probe-Δ; notes-q.
- Cost: cheap (prompt + a few lines of harness state; same lesson count).

## 2. Retrieval practice / testing effect (Roediger & Karpicke 2006, Psych. Science)
- Core finding: being *tested* on material beats re-studying it for long-term
  retention; large, extremely well-replicated human effect. ML analogue is
  weaker but consistent with why win-flagged self-generated text trains well.
- Nursery variant: before each apply-task, instead of injecting the restated
  lesson verbatim into the prefix ("Remember your parent's lesson: …"), the
  harness asks the child to RECALL it cold: "Before this box: what did your
  parent teach you last time, in your own words?" The retrieved (not re-shown)
  restatement becomes the prefix. Failed retrievals get one parent re-teach.
- Sticking metric: probe-Δ is the direct test (retrieval-practiced lessons
  should survive parent absence better); notes-q.
- Cost: cheap (one extra 120-token child call per lesson).

## 3. Self-explanation effect (Chi et al. 1989, Cog. Science; Bisra et al. 2018 meta-analysis)
- Core finding: learners who explain *why* a step works learn far more than
  those who just see or restate it; meta-analytic g ≈ 0.55 in humans. Directly
  echoed in ML by rationale-augmented training (STaR).
- Nursery variant: change step 3. Instead of restating the parent's
  correction, the child must explain, citing its own transcript: "which of my
  probes was wasted and WHY; which belief did the evidence actually rule out?"
  Parent grades the explanation's specificity (one line), and only
  explanation+apply pairs where the apply-task is admitted enter the sleep
  corpus.
- Sticking metric: probe-Δ; notes-q (explanations should raise scoped-note
  fraction); calib.
- Cost: cheap (same call count, longer restate turn).

## 4. Process-level formative feedback (Shute 2008, "Focus on Formative Feedback", RER; Hattie & Timperley 2007)
- Core finding: feedback aimed at process and self-regulation beats feedback
  about the self or the bare outcome; specificity and actionability matter
  more than valence. Strong review-level human evidence (Hattie d ≈ 0.7 for
  good feedback, with huge variance — honesty: the variance is the finding).
- Nursery variant: restructure the parent's 120-word turn into Hattie's three
  questions, filled from the transcript: (a) where were you going (the child's
  own stated goal/prediction), (b) how did it go (one concrete gap),
  (c) where next (one process move for the apply-task). Forbid praise/blame
  words; require quoting one line of the child's stream.
- Sticking metric: admit-rate (better-targeted feedback should convert more
  lessons); probe-Δ; canary (structured feedback shouldn't bleed format).
- Cost: cheap (prompt-only).

## 5. Calibration drill (Lichtenstein & Fischhoff 1980; ML: process-reward findings that calibrated stepwise confidence predicts success)
- Core finding: explicit outcome feedback on probability judgments improves
  human calibration; in LLMs, verbalized-confidence calibration is trainable.
  The child already emits PREDICT — this is the cheapest lever we haven't pulled.
- Nursery variant: parent's correction must always include a calibration
  audit computed by the harness: "you said T on 6 probes and were right on 2 —
  what does that tell you about your rule?" Child's restatement must include a
  confidence policy note ("only QUIZ when my last 3 PREDICTs were right").
  Sleep corpus tags each stream with its realized calibration; only
  well-calibrated admitted streams are compiled.
- Sticking metric: calib is the primary instrument (rare: a variant with a
  dedicated metric); probe-Δ secondary.
- Cost: cheap (harness computes hit-rates from the ledger; prompt change).

## 6. Spaced repetition + interleaving (Cepeda et al. 2006 meta; Rohrer & Taylor 2007)
- Core finding: expanding-interval revisits and mixing problem types beat
  blocked practice for retention/transfer; among the most robust effects in
  human learning. ML echo: the sleep compiler's own CLS interleaving law.
- Nursery variant: scheduler-only change. Replace `ridx = les % 10` with an
  expanding-interval scheme: each rule family is revisited at lesson gaps
  1, 3, 7…, and consecutive lessons never share a family (interleave). The
  parent additionally opens each revisit with "you have seen this family
  before — RECALL first."
- Sticking metric: probe-Δ on *revisited* vs fresh rule families
  (per-eid split already in `probe_*.json`); admit-rate on revisits.
- Cost: cheap (pure scheduling; identical lesson count).

## 7. Socratic-only parent (VanLehn 2011, Educ. Psychologist tutoring review; Socratic ITS tradition)
- Core finding: human tutors and step-based ITS achieve d ≈ 0.76 largely via
  prompted self-repair, not telling. But VanLehn also found *telling isn't
  worse* when content is right — so this is a genuine A/B, not a sure win.
  LLM-side: Socratic tutoring prompts help student models in several 2024-25
  studies, effect size unclear.
- Nursery variant: parent hard rule becomes "never state the mistake; ask the
  ONE question whose answer forces the child to find it." Child answers the
  question, then self-states the lesson (step 3 becomes self-diagnosis).
  Everything else identical. This is the pure-discovery pole; pairs with #1
  (contingent) as the interesting contrast.
- Sticking metric: probe-Δ vs the current direct-correction baseline;
  notes-q (self-found lessons may be better scoped).
- Cost: cheap (prompt-only).

## 8. Error-management training (Frese et al. 1991; Keith & Frese 2008 meta-analysis, JAP)
- Core finding: training that *encourages* errors plus explicit "errors inform
  you" framing beats error-avoidant training, especially for transfer
  (meta d ≈ 0.56 on transfer tasks). Human evidence strong; untested in LLMs
  but rhymes with the surprise-ledger design.
- Nursery variant: (a) add two sentences of error-framing to CHILD_BOOT
  ("errors are data; when the box surprises you, you just learned the most");
  (b) parent's correction must never mark an error as bad — it must convert
  each wrong PREDICT into the belief it falsified; (c) sleep SELECT
  up-weights failure→diagnosis→recovery triples over clean wins.
- Sticking metric: probe attempts-to-first-improvement (error-managers should
  probe more informatively); calib; probe-Δ.
- Cost: cheap (prompts + one selector weight).

## 9. Productive failure (Kapur 2008, Cognition & Instruction; Sinha & Kapur 2021 meta, d ≈ 0.87 for PF designs; ML: StratL, arXiv:2410.03781)
- Core finding: unguided struggle *before* instruction beats
  instruction-first, provided a consolidation phase contrasts the learner's
  own failed attempts with the canonical approach. Meta-analytic support is
  strong though design-sensitive. Already piloted for LLM tutoring (StratL).
- Nursery variant: restructure the cycle to struggle-first blocks: child
  plays TWO tasks from a family with no parent; then one consolidation turn
  where the parent explicitly contrasts the child's two attempts ("in box A
  you did X, in box B you did Y — which probe pattern earned more
  information, and why?"); then apply-task; world admits. Halves the number
  of parent turns per lesson but doubles pre-tasks.
- Sticking metric: probe-Δ (PF's signature is delayed/transfer advantage —
  exactly what parent-absent probing measures); admit-rate may *lag* early —
  expected, report the curve not the mean.
- Cost: medium (≈1.5× child rollouts, fewer parent calls).

## 10. STaR-style verified rationalization (Zelikman et al. 2022, "STaR", NeurIPS)
- Core finding: train on self-generated rationales for problems the model got
  right, plus *rationalized* retries of failures given the answer; strong,
  replicated ML result for bootstrapping reasoning.
- Nursery variant: sleep-side change. For each NON-admitted apply-task, the
  world (not the parent) reveals only the outcome the child already saw, and
  the child regenerates one corrected stream for the same box; the harness
  replays it against the game, and only regenerations that actually pass are
  win-flagged into the compile. Parent uninvolved — this recycles failures
  that currently contribute nothing to training.
- Sticking metric: probe-Δ per compiled token (the corpus gets bigger —
  normalize); canary (regenerated streams must keep dialect).
- Cost: medium (one extra rollout + replay per failed lesson).

## 11. Reflexion-style self-critique first (Shinn et al. 2023, arXiv:2303.11366; already noted in research_notes/related_work/)
- Core finding: verbal self-reflection stored in memory improves later
  attempts without weight updates; robust in ML for episodic settings. Open
  question is whether it *compiles* into weights — which is exactly our rig.
- Nursery variant: insert step 1.5 — before the parent speaks, the child
  writes its own critique ("what would I do differently?"). The parent then
  critiques the critique (meta-feedback), not the transcript. Restate + apply
  unchanged. Tests whether teaching self-assessment beats teaching the task
  process.
- Sticking metric: notes-q and the `behave` assay (self-assessment
  dispositions); probe-Δ.
- Cost: cheap (one extra 150-token child call per lesson).

## 12. Mastery gating (Bloom 1984 "2-sigma"; Kulik, Kulik & Bangert-Drowns 1990 meta on mastery learning, d ≈ 0.5)
- Core finding: requiring a mastery criterion before advancing, with
  corrective re-teaching, reliably beats fixed-pacing; the mastery component
  of Bloom's 2-sigma is well supported even though the full 2σ isn't.
- Nursery variant: scheduler + loop change. A rule family isn't left until
  the child gets an admitted lesson on it (cap: 3 attempts, then park and
  revisit later — avoids infinite loops on hard families). Re-teaches use a
  *variant* box from the same family, and the parent must vary its angle.
- Sticking metric: probe-Δ per family (mastered families should stick
  hardest); admit-rate is partially confounded (gating raises it by
  construction — use the probe, not the admit-rate, as headline).
- Cost: medium (lesson count becomes variable, ≈1.5–2×).

## 13. Worked examples with fading (Renkl & Atkinson 2003; Sweller's worked-example effect + Kalyuga's expertise reversal)
- Core finding: novices learn more from studying worked solutions than from
  problem solving; the advantage *reverses* with expertise, so examples must
  fade. Very strong human evidence; phi-series is arguably the ML analogue.
- Nursery variant: lessons 0–3 open with a parent-narrated worked example of
  the *process* on a spent rule-game box (a family already used, rule then
  revealed by the world, so the parent still never sources answers itself):
  "watch: PREDICT, probe to falsify, scope the note." Lessons 4–7 give
  half-worked openings (child completes); lessons 8+ none. Contamination
  note: worked examples are rule-game-only and drawn from world-verified
  transcripts, never hand-authored solutions.
- Sticking metric: probe-Δ; canary is critical (parent-voiced exemplars are
  the highest dialect-bleed risk on the menu); admit-rate early vs late
  (expertise reversal predicts fading beats not-fading late).
- Cost: medium (parent example turns + curation of spent boxes).

## 14. Chunk-level process win-flagging (Lightman et al. 2023, "Let's Verify Step by Step" — process reward > outcome reward)
- Core finding: supervising *steps* beats supervising outcomes for math
  reasoning; strong ML evidence at scale, unknown at 7B-with-LoRA scale.
- Nursery variant: sleep-side. On admitted lessons, the parent additionally
  labels each chunk of the winning stream sound/unsound (process labels,
  no answers — "this probe repeated known information"). Compile only sound
  chunks; unsound chunks from admitted streams are dropped rather than
  trained. The world's admission remains the gate; the parent only refines
  granularity *within* world-admitted material (keeps the v5 support law).
- Sticking metric: probe-Δ per compiled token vs baseline compile; calib.
- Cost: medium (one parent labeling pass per admitted lesson; compile change).

## 15. Textbook-quality sleep corpus (Gunasekar et al. 2023, "Textbooks Are All You Need", phi-1)
- Core finding: small models trained on cleaner, more pedagogical data beat
  much larger raw-data budgets; among the most consequential ML data results.
- Nursery variant: sleep-side. After SELECT, the parent rewrites each
  admitted exemplar into a clean canonical version *in the child's dialect*
  (tighten, keep markers, keep the child's own numbers/evidence, fix nothing
  factual) before TRANSFORM. Train on rewritten + a held ratio of raw to
  hedge distribution shift.
- Sticking metric: probe-Δ; canary is the primary risk gate (parent rewrite
  is a direct dialect-contamination vector — run canary per checkpoint).
- Cost: medium (one rewrite call per compiled exemplar).

## 16. ZPD-bandit curriculum (Bengio et al. 2009 curriculum learning; Self-Evolving Curriculum, arXiv:2505.14970; caveat: easy-to-hard gains are inconsistent in 2025 post-training studies)
- Core finding: ordering by difficulty helps sometimes; the more robust ML
  version targets tasks at intermediate success probability (the RL/auto-
  curriculum "learning progress" family) — the ZPD, operationalized.
- Nursery variant: replace the fixed rule rotation with a per-family bandit
  that samples the family whose recent child success rate is closest to 0.6
  (needs per-family difficulty stats; RuleGame families give this for free).
  Parent behavior unchanged.
- Sticking metric: admit-rate trajectory + probe-Δ; per-family probe split
  shows whether mid-difficulty targeting sacrificed easy-family retention.
- Cost: medium (stats plumbing; possibly more lessons to see the effect).

## 17. Deliberate-practice drills (Ericsson, Krampe & Tesch-Römer 1993, Psych. Review)
- Core finding: expert skill comes from effortful practice targeted at
  *diagnosed weaknesses* with immediate feedback — not from accumulated
  playing time. Hugely influential; effect-size estimates contested
  (Macnamara et al. 2014 meta says smaller than legend), so honest EV is
  moderate.
- Nursery variant: every 4 lessons the harness computes the child's weakest
  measured sub-skill from the ledger (lowest of: predict-before-act rate,
  probe diversity, scoped-note rate, calibration) and the parent assigns one
  drill lesson targeting only that sub-skill on a fresh box ("this box, your
  only goal: no repeated probes"). World still admits by score.
- Sticking metric: the targeted sub-skill's own instrument (notes-q, calib,
  attempts-to-first-improvement) moving specifically after its drill;
  probe-Δ overall.
- Cost: medium (diagnostic plumbing + 25% more lessons).

---

# FIRST WAVE — 6 variants + 2 anchors, one GPU each, a few hours each

All are prompt/scheduler-level changes to `nursery_dialogue.py` (no new
training machinery), 12 lessons + sleep + on/off probes, ≥1 seed now and
replicate the winners. Anchors: the existing **parent** and **solo** arms
rerun under the same seeds so every variant has a same-day baseline.

1. **W1 contingent-scaffold** (#1) — best-evidenced tutoring result in
   humans; pure prompt ladder; directly tests whether *adaptive* directiveness
   beats the current fixed 120-word correction.
2. **W2 retrieval-practice** (#2) — the strongest human retention effect,
   mapped onto the exact step (prefix injection) most likely to be creating
   parent-dependence; probe-Δ is its native metric.
3. **W3 self-explanation** (#3) — same call budget as baseline; converts the
   restate step from parroting to explaining, the highest-leverage single-step
   swap on the menu.
4. **W4 socratic-only** (#7) — the pure-discovery pole; with W1 it brackets
   the tell↔ask axis so the screen localizes where the value is.
5. **W5 productive-failure** (#9) — biggest meta-analytic transfer effect we
   can implement without new machinery; predicted signature (early admit lag,
   late probe gain) is falsifiable with existing instruments.
6. **W6 calibration-drill** (#5) — the only variant whose primary metric
   (calib) is currently unimproved by anything; cheap and mechanistically
   independent of W1–W5, so it can stack with any winner.
7. **A1 baseline-parent rerun** — anchor.
8. **A2 solo rerun** — anchor.

Held for wave 2 (need compile changes or extra rollouts, run after the screen
picks a champion cycle shape): #6 spacing/interleaving, #8 error-management,
#10 STaR recycle, #14 chunk win-flagging, #15 textbook rewrite (canary-gated).

Report per variant: probe-Δ (headline), admit-rate curve, calib, notes-q,
canary — as cell counts per lesson/probe, not narratives.
