# The Felt Agent — Super Design Document
*(v1.0, 2026-08-16 — synthesis of research notes 25–31, VISION_ROADMAP, and session-1 evidence)*

---

## 0. Thesis

**The difference between a cache and a memory is a policy.** Transformers have a
perfect cache (KV: every entry kept, none chosen, none learned) and no policy.
Every architecture community — memory substrates, global-workspace, robotics,
neuroscience — independently lists the same open problem: *deciding what to
preserve, trained on outcomes.* This project builds that organ and the agent
around it.

One sentence for the whole system: **the engine thinks; the felt system learns
how to run a mind around a thinker.**

---

## 1. The architecture at rest

```
                     inputs (user, tools, world)
                              │
                              ▼
              ┌────────── FELT ATTENTION ──────────┐
              │   (salience: admission + curation) │
              ▼                                    │
        ┌───────────── WORKSPACE / PROMPT ENGINE ──┴───┐
        │  iterative composer: state + I/O in context   │
        │  → GENERATES memory queries (tokens)          │
        │  → gist returns geometries → loop until       │
        │    ignition (satisfied) or saturation (full)  │
        │  → attention over accumulated window          │
        │    reconstructs the injection prompt          │
        └──────┬─────────────────────────┬─────────────┘
               │ prompt                  │ queries
               ▼                         ▼
     ┌──── FROZEN REASONER ────┐   ┌── GIST MEMORY (LTM) ──┐
     │ pretrained LLM;          │   │ LoRA on a small base  │
     │ pure deduction; never    │   │ model; generative;    │
     │ contaminated by wanting  │   │ the LIVED SUBSPACE    │
     └──────────┬───────────────┘   └───────────┬───────────┘
                │ outputs / actions             │
                ▼                               │
        output space → environment       ┌──────┴────────┐
                │                        │ EPISODIC LOG  │
                └── event outcomes ──►   │ (a TOOL, not  │
                     POLICY (loss fn,    │ architecture: │
                     backward passes     │ append-only + │
                     only, at super-EOS) │ search;       │
                                         │ verification) │
                                         └───────────────┘
        DREAM (offline): felt-curated replay trains gist;
        reads-repress; renormalization; generative replay
        folds old gist into base weights (hibernation).
```

**Components and their one-line contracts**

| Component | Contract | Learned? |
|---|---|---|
| Frozen reasoner | deduction only; desire never touches it | No (pretrained) |
| Prompt engine (composer) | the outer transformer whose *tokens are prompts*; iterative query-reconstruct loop | Yes (BC → RL) |
| Felt attention | the priced doorman: what enters prompts, what gets dreamed about | Yes (outcome credit) |
| Gist LTM | generative lived-subspace (see §3) | Yes (dream-trained LoRA) |
| Episodic log | append-only + search; a *tool*; verification layer against confabulation | No |
| Policy | the loss function; exists only in backward passes; judges events at super-EOS | Later (frozen first) |
| Dream | the backward pass of life: replay curation, re-pressing, renormalization, generative replay | Consequence of felt |

**Loop mechanics (hard rules, all evidence-backed)**
- **Event-driven cadence:** the outer loop ticks on events (inner EOS, new input,
  ignition), never per-token. Continual learning lives off the serving path →
  ~zero marginal inference cost.
- **Never-block:** the fast loop always acts on the last slow output (every
  shipped robot stack does this).
- **Ignition/saturation stops:** commit thresholds are workspace-enforced, not
  model-emitted.
- **Hysteresis:** any arbitration carries persistence bias (deadlock-at-equal-
  salience is a documented failure we reproduced ourselves).
- **The workspace never owns the clock** (LIDA's fatal lesson).

---

## 2. The person-hierarchy (what stores what)

| Person | Store | Content | Size class | Clock |
|---|---|---|---|---|
| **First** | context window | *now* — working state | ~1M tokens | tokens |
| **Second** | gist LTM (LoRA) | *the world as it has responded to you* — action→outcome patterns, paths, habits-of-situation | ~100M-token life, compressed | sleep |
| **Third** | base weights | *the world as everyone describes it* | pretraining | hibernation |

**The cascade:** context → (dream, felt-curated) → gist → (hibernation,
generative replay) → base. Forgetting is graceful at every tier: anything
important is either re-generable from gist or already folded into base by its
own retellings. **Reads re-press, gated by verification** (retrieval strengthens ONLY when
the read is subsequently supported by tools, outcomes, or the episodic log —
otherwise vivid confabulations would compound by being recalled): vividness
tracks recency-of-VERIFIED-use.

---

## 3. What LTM really means

**Not a database.** A smart database is *fundamentally a tool* — we keep one
(the episodic log) and it is deliberately boring: append-only, exact,
searchable, and outside the cognitive architecture.

**The LTM is a lived subspace of a world model.** Mechanically: a small
pretrained LM (third-person world geometry) carrying a LoRA trained during
sleep on felt-curated replay of the agent's own experience. What the LoRA
learns is *which paths through the world are yours* — action patterns,
failure→repair structures, what-mattered-when.

**Reads are generative completions, not lookups.** Query "attempted a→b→c,
failed—" and the gist continues with the nearest lived pattern — including the
repair (we call this the *xyz→xzy property*: analogical sequence completion,
which LMs do natively when fine-tuned on an autobiographical corpus).
Different queries expose different geometries; the composer's iterative loop
harvests several geometries per prompt.

**Its failure mode is designed-for:** generative memory confabulates. The
episodic tool is the verification layer — intuition first, notes to check.
This split is the hallucination control, not redundancy.

**Training data for gist is self-labeling:** dependency-credit machinery
(built and validated in session 1) mines failure→fix pairs and load-bearing
episodes from logs automatically.

---

## 4. The three escalations

### 4a. Memory escalation
1. **M0** — context only (baseline agent).
2. **M1** — + episodic tool (commodity RAG; every arm gets this).
3. **M2** — + gist LoRA, dream-trained, felt-curated *(session-2/3 target)*.
4. **M3** — + hibernation: generative replay folds gist into base weights.
5. **M4 (v3+)** — reconstruction dynamics (Hopfield-style blending), latent
   payloads (o-vectors), analogical cross-domain transfer.

### 4b. Agency escalation
1. **A0** — fixed prompts (the S0 gate agent).
2. **A1** — hand-wired composition: goal header + top-k + inputs *(v0; built)*.
3. **A2** — trained composer, behavior-cloned on logged trajectories
   (next-prompt prediction — prompts are tokens).
4. **A3** — RL composer: event-level policy loss at super-EOS; gap-aware,
   exploration-aware reads.
5. **A4** — self-prompting and goal-drift: policy holds/switches goals; the
   composer reasons its own subgoal changes.
6. **A5 (far)** — unfrozen value function; multi-head desires; the full
   continual agent.

### 4c. Horizon escalation (training-sequence length)
1. **H0** — single prompts (no memory dependence).
2. **H1** — short multi-prompt episodes; millions in parallel (*parallel
   lives*: many agents, shared consolidation — how a serial-life problem
   trains in parallel).
3. **H2** — full events with event-level loss.
4. **H3** — multi-event sequences with *stage shifts* (value drift:
   materials→building→trading) — tests memory adaptation + return-to-origin.
5. **H4** — beyond-context lifetimes: the conjecture-style loss (context =
   a domain's literature; targets = post-cutoff outcomes; backprop through
   the slow pathway only, cache-most/refresh-selective).

**The escalation law (applies to all three):** *amortize-then-integrate.*
Prove each rung with the dumb version of everything else; swap one dummy for
one learned component per stage; a rung's ceiling licenses the next rung.
Greedy composition is the bet — long-horizon competence built from validated
short-horizon blocks — and its failure mode (structures that must be relearned
at scale) is monitored by the curriculum-transfer curve.

---

## 5. Training proposal (three phases)

**Phase A — pretraining (done by the world):** the reasoner and the gist-base
are off-the-shelf pretrained models. We never train them from scratch.
*Evolution, not learning.*

**Phase B — agentic training (generalizable learning-to-learn):**
1. **B1 Behavior cloning:** next-prompt prediction on logged successful agent
   trajectories (ours + public traces). Teacher-forcing at prompt granularity.
2. **B2 Felt distillation:** salience head(s) trained on outcome-derived
   dependency credit (validated mechanism; leakage gate ≤ ~0.7 enforced on
   any training environment *before* training).
3. **B3 RL:** event-level loss (critic-as-loss; no external reward machinery)
   over H1→H3 curriculum, massively parallel short first.

**Phase C — deployment (continual learning):**
- **Wake:** act; episodic tool logs everything (no write policy — storage is
  cheap); reads re-press gist; composer runs the iterative loop.
- **Dream (nightly):** felt-curated replay updates the gist LoRA;
  renormalization (global downscale — SHY); repair-pair emphasis; optional
  synthetic rehearsals for weak areas.
- **Hibernation (rare):** generative replay distills stable old gist into the
  GIST MODEL'S base — never the frozen reasoner (desire/deduction law holds
  at every tier); LoRA budget freed.
- **What is NOT online-trained initially:** the reasoner (competence-CL is a
  separate loop, later), the policy (frozen critic first), the composer
  (frozen after Phase B; light online updates are an A4+ experiment).

**The deployment story:** you ship a *slightly dumber baby* — empty LTM,
generalized meta-decisions — and it grows into its field. Second month on
your problem better than the first. That property is the product.

---

## 6. Continual learning: what it means here

- **Two loops, one doorman:** knowledge-CL (memory systems — this project) vs
  competence-CL (weight plasticity in the engine — three-factor/e-prop line,
  robotics' need). Felt salience prices experience for both.
- **Policy = loss function.** No reward in any forward pass. "Dopamine" is
  what the policy's gradient looks like from inside; at scale, importance-
  seeking is *emergent* from broad outcome training — the explicit felt head
  is the amortized, attributable form we can publish, and it dissolves into
  the composer when instruments permit.
- **Salience is a learned bid estimator** (robotics' 40-year lesson: price
  estimation is the whole game). Its **calibration**, not just its ranking,
  is the core research risk — measured henceforth.
- **Cost shape:** all plasticity off the serving path. Inference cost ≈
  a stateless agent + a few reads per event.

---

## 7. Evidence base (session 1, honest)

**Validated:** the instrument (gates, typed probes, canaries, leakage meter);
capability ladder (1.5B 0.03 → 3B 0.17 → Phi-3.8B 0.40 → 7B 0.90, monotone,
two families, bounded both ends by too-weak and too-strong rejections); the
write mechanism trains (AUC 0.97–0.99, config-invariant across unseen
generators); the substrate converts signal quality into retention
(uniform→reference gap); **surprise is an actively bad write signal**
(below uniform; behaviorally toxic: 0.03–0.15 win vs 0.26 amnesia); the
scarcity curve (selection matters only when capacity binds).

**Retracted/unproven:** the v1 headline (credit≡type world-design flaw —
reversal #6 of six, all caught by our own adversarial process); the thesis
(felt > type-detection) is *untested, not false* — its preconditions are now
measured requirements (below).

**Convergence validations (4):** neuroscience (three-factor writes, replay,
SHY), GWT (learned admission + LTM coupling are the field's named open
problems), robotics (salience-bid arbitration, never-block, calibration),
memory substrates (Hopfield community's list ends at "deciding what to
preserve").

---

## 8. Session-2 requirements (all measured, not assumed)

1. **Environment leakage:** AP(credit→type) ≤ ~0.7 *before any training run*
   (v1.1 was 0.91 — the regex wins by right above that). Co-designed with
   Rohin; six independently load-bearing content channels (facts, negative
   knowledge/dead-ends+traps, procedures, episodic anchors, attempt history,
   gap map).
2. **Probe tier at capacity pressure** (memory-poverty regime; dose-response
   validated) + **head calibration curves**.
3. **Behavioral tier requires the exploration-aware read** (fixed naive reads
   made *every* memory worse than amnesia at small k — measured); gap-aware
   injection is a precondition, not an enhancement.
4. **Headline candidate:** the xyz test — novel structurally-similar failures;
   does gist-guided repair-finding beat tool-RAG-only, behaviorally.
5. **Gist capacity measurement:** LoRA rank/size vs life-length (run-2).

---

## 9. Papers and sequencing

1. **Foundation paper (now):** the benchmark + instrument + negative-control
   ledger + toxic-memory and scarcity findings + measured requirements.
   ICLR abstract Sep 18; preprint regardless.
2. **LTM + policy paper (session 2–3):** the organ under honest conditions;
   xyz headline; retrieval profile; gist-tier behavioral lanes.
3. **Architecture/position paper (parallel, cheap):** this document, argued —
   the prompt-transformer, the person-hierarchy, the escalation law.
4. **Startup terminus (pressure test, not plan):** the agentic field
   adventurer — continual-learning research agent at a domain frontier;
   moat = "second month better than the first"; deploy where verifiers are
   fast.

---

## 10. Design laws (the collected rules, each paid for)

1. Design components for the **system**; design **instruments around** them.
   Never let probeability drive architecture. No stored dials — properties
   live in the physics (press depth, basin depth).
2. **Amortize, then integrate.** External and dumb first; learned when the
   interface measurably binds; integrated when instruments can attribute it.
3. **Desire and deduction never share weights.** The reasoner stays clean;
   agency lives in inspectable external organs (also the safety-legibility
   argument: continual learners have more to preserve — keep their wanting
   visible).
4. **Every scaffold is an instrument or an amortization target.** Neither →
   barnacle → cut.
5. **Three-check maxim** for any new component: parallelizable in training /
   one-sentence simple / composable without special cases.
6. **Pre-register readings; adversarially audit positives AND negatives**
   (a false STOP kills a true paper). No result is real until a code-level
   adversary fails to kill it.
7. **The gates rule.** Calibrate floor and ceiling before measuring anything
   between them; cheap audit before every expensive run.

---

*Current state: v0 organ validated and honest; environment for the real test
specified with numbers; architecture converged from four independent
directions; next artifact = session-2 design doc for co-editing, then worlds,
then the organ's fair fight.*

---

## 11. The fourth escalation: population (added 2026-08-16)

Dreaming is the inheritance operator at three scales: individual (nightly
gist), cultural (reconciliation across parallel lives), evolutionary
(hibernation into shared bases). Enabled ONLY by separable transmissible
state: frozen reasoner (intellectual inheritance) / shared composer+felt
(cognitive-cultural inheritance) / personal LoRA + episodic log (individual
life). Inheritance moves VERIFIED EXPERIENCE (replayed, distilled, tested),
never averaged weights.

**P-escalation:** P0 one agent, one life → P1 parallel lives, shared
consolidation (the serial-lifetime escape) → P2 reconciliation stages with
the TRANSFER-MATRIX decision rule (merge iff cross-agent transfer broadly
positive; preserve lineages if specialist/interfering; share only routing
meta-knowledge as the third option — reconciliation itself outcome-trained)
→ P3 age-structured fleets (maturation funnel: explorers → lineages →
experts → frozen elders; functional age = improvement-per-dream-FLOP, not
elapsed time; novelty archives + canary populations against monoculture).

New scaling axes unavailable to static models: performance vs agent age;
generation-over-generation start quality and learning rate; reconciliation
frequency; branch-vs-merge value; marginal agent vs extended life; dream
compute vs retained experience.

**Added risks (measured curves, not demonstrations):** surface imitation vs
structural transfer (xyz held-out sets must break vocabulary/domain/action
identity, preserve only structure); reconstruction vs confabulation (score
memory by MARGINAL DOWNSTREAM SUCCESS PER READ, never text similarity);
replay collapse (verification-gated re-pressing, above); long-horizon
credit; composer-gist nonstationarity (the composer's environment changes
nightly); gist capacity vs lifetime; open-ended value (satisfying its own
critic vs the world); hibernation stability (rare-but-important experience).

**Decisive evaluation:** at equal base model and inference compute, learned
harness + lived gist progressively outperforms fixed harness + long context
+ episodic RAG, while retaining old competence. Plots: performance vs
accumulated lifetime; structural transfer; retention after stage shifts;
benefit per memory query; gist capacity vs rank; improvement vs sleep
compute; return-to-origin; tool-verified success only.

Scope anchor: P-escalation is position-paper material and v5+ engineering.
It changes nothing about session 2. The organ first; the population is
where the organ goes.
