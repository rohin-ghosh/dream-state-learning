# SPEC v2 — Dreamed Parametric Memory vs Retrieval
*(2026-08-19. Co-design draft for Rohin's red pen. 🔴 = open decision for you;
everything else is a granular default I'll build unless overruled.
PART I = the one-page overview + locked constants. PART II = the in-depth
sizing pre-registration: sweep evidence, context-budget math, throughput,
predictions. One document, two altitudes.)*

# PART I — Overview (one page)

## 1. Claim
An agent whose experience is consolidated into weights (dream → LoRA) has a
**different scaling curve** than one that retrieves it: retrieval and long-context
flatten or bend as accumulated experience grows, parametric keeps climbing —
because it acquires **induced regularities** (cross-episode structure present in
no single episode). We measure the crossover; we report where retrieval wins.

## 2. Environment — AlchemyWorld
- **1024 ingredients** (128 inert), nonce names (contamination-proof), each with
  a hidden **essence** ∈ **96 classes** (4,656 rules) + hidden **grade** ∈ {1,2}.
  Essences NEVER appear in any text (leakage is grep-able = property in the
  physics). Sized by Monte Carlo (Part II §3): small latents saturate in
  tens of episodes; the accrual phase must also OUTRUN the context window
  (info still arriving when 128k breaks — see Part II §4).
- **Rule table (per-run randomized):** unordered essence-pair → outcome family
  {product, nothing, ruin}. Product identity = f(essence pair, max grade) —
  compositional: knowing essences predicts **never-tried pairs**.
- **Chain depth:** products have derived essences → recipes chain (depth 1–3
  targets). **Distractors:** (a) inert-essence ingredients that never react;
  (b) visible surface features (color/smell) randomized independently of essence
  — a tempting false correlate.
- **CONNECTED-DATA PRINCIPLE (Rohin, core design law for this experiment):**
  the data must be structural — the memory's job is to learn high-dimensional
  patterns that extrapolate to unseen positions, so the latent must be
  INTELLIGENTLY GENERATED as a spectrum of structure, and eval reports per
  stratum:
  · **Stratum R (random core)** — i.i.d. rules; incompressible; must be
    experienced; tests raw retention at scale. (Implemented.)
  · **Stratum G (geometric) — PROMOTED TO REQUIRED (load-bearing):** rules
    generated from a hidden function over essence properties (cycle/lattice
    distance; grade arithmetic). A learner that finds the representation can
    predict rules NEVER OBSERVED IN ANY FORM — extrapolation beyond the
    observational ceiling; retrieval cannot in principle. Without it the
    only induced regularity is class membership — true but modest; G carries
    the headline claim. Generalized as the **pattern-spectrum mixture**
    (ρ_iid / ρ_fn / ρ_analog — Rohin): sweep the mixture ⇒ performance vs
    world-compressibility curve (Part II §1).
  · **Stratum D (distractor)** — inert ingredients + false-correlate surface
    features; tests not-learning noise.
- **Episode:** goal "craft ⟨target⟩", inventory = random subset of 6 ingredients
  (forces pair coverage to accrue only in aggregate), ≤12 combine steps,
  game value = depth-distance-to-target, logged per step (this is "state").
- 523,776 base pairs; **held-out split enforced by construction**: 30% of pairs
  are never co-present in any episode inventory (physics, not luck — a coverage-
  maximizing explorer would otherwise see everything; smoke-test find).
- **Pre-registered oracle ceilings — THREE tiers of reasoner** (Part II §1):
  · retrieval-evidence only: →0.46 (lookup bound)
  · + class-transfer inference: →0.77
  · + statistical inert elimination (T=8 distinct classes, P(err)<0.4^8):
    0.05 @960 eps → 0.61 @1920 → 0.99 @3840 → **1.00** @7680.
  The world is FULLY compositional — a perfect reasoner eventually deduces
  everything (Rohin's ≥90% requirement: met at 100%). Regimes: **accrual**
  (≤~3.8k eps ≈ 770k log-tokens ≈ 6× a 128k window, 24× native 32k) and
  **repetition** (beyond). Headline normalizer = tier-3 ceiling. The
  measurement zone is HIGH CEILING / LOW ACHIEVED / WIDE GAP — both failure
  modes (ceiling too low; everything fits in context) collapse the gap.

## 3. Complexity types (each scored separately → the map, not one number)
| type | what it tests | expected winner |
|---|---|---|
| exact recall (seen pair) | retrieval | **RAG wins — reported as calibration** |
| attribute composition (unseen pair) | induced regularity | LoRA-dreamed |
| chain planning (depth 2–3 target) | composing regularities | LoRA-dreamed |
| distractor resistance | not latching onto false correlates | open — the honest test |

## 4. Arms (2×2 + rails; SAME reasoner + SAME prompter everywhere = compute parity)
no_memory · long_context (full history until the real window breaks — the break
IS a result) · RAG-raw · RAG-dreamed · LoRA-raw · LoRA-dreamed.
A-Mem added later as the strong published baseline. 🔴 approve arm list.
**Eval sizes per arm-point:** held-out prediction 200 questions (primary,
properly powered); task-success play **200 fresh episodes** (raised from 40:
binary outcome at n=40 gives ±15pt CIs — blind to small gaps; n=200 × 5
seeds ⇒ ±3–4pt). Headlines never rest on task success alone.
**Scripted-explorer factorization (stated limitation, not a bug):** the life
stream is generated by a scripted explorer, so v2 tests whether memory can
HOLD AND GENERALIZE experience, isolated from whether an agent can GENERATE
good experience (the explore policy — paper 3). This also gives every arm an
IDENTICAL life stream, so the substrate is the only variable; an LLM-
generated life would differ per arm and confound the comparison.

## 5. Scaling axes
x-axis is always **episodes**: measure at 60 / 320 / 960 / 1920 / 3840 /
7680 / 15360 — all prefixes of ONE frozen life stream (same experience,
growing exposure). 60 (~20k tok, fits 32k ctx) and 320 (~106k tok, fits
128k ctx) are EARLY calibration points where long-context is still alive —
its early win must be MEASURED and printed, not assumed (the crossover needs
both ends). NOTE: tier-3 ceiling ≈0 at these points, so there is nothing
composable yet — the early-point metric is **seen-pair recall + task
success**, not held-out composition (which starts being informative at 960).
Then four points in accrual, the last deep in repetition.
(Real-tokenizer count: 332 tok/episode.)
Life generation is LLM-free (scripted explorer) → episodes are free; the cost
driver is eval play (~1 A100-hr/seed total; Part II §6). Secondary: LoRA rank {8, 32} — if the parametric
ceiling moves with rank, saturation is capacity, not mechanism. LoRA retrained
from full curated corpus at each measurement point; checkpoint frozen per point
(drift allowed by design, never inside a measurement).

## 6. Mechanism (all amortized; per-box info-set gate)
- **State** (trivial v2): goal, inventory, last outcome, game value. Logged.
- **Sleep cadence (Rohin):** a dream cycle fires every time ~one context
  window of experience has accumulated (~32k tok ≈ 96 eps at 332 tok/ep):
  dump STM → dream → retrain LoRA from full corpus → resume. Measurement
  checkpoints align with dream boundaries (~160 cycles over a 15,360-ep
  life; minutes each).
- **Value function:** exact, from ground truth — BFS distance over the true
  crafting graph from holdings to target. No learned VF needed at this scale;
  logged per step into state (the dream's hindsight signal).
- **Dreamer = one prompted LLM call** per log chunk: sees episodes + outcomes +
  value logs (episode hindsight OK, eval set never). Emits **cross-episode
  pattern memories as text** (2nd person), not per-episode summaries.
  Dumb-dreamer arm = raw log transcription. **Memory text format (signed off):
  a MIX** — (a) declarative recipe facts, (b) cross-episode pattern/analogy
  lines, (c) a QA-format slice (matches the eval's register), (d) negative
  knowledge (nothing/ruin pairs), (e) **goal-conditioned action lines**
  ("To craft Z, combine X and Y") — the memory-as-policy-prior read (below).
  All strata leakage-scanned. **Two format REQUIREMENTS (not options):**
  (i) REVERSAL CURSE: rules are unordered pairs but "A+B→C" trained one way
  often fails queried as "B+A" — every pair fact is emitted in BOTH
  orderings (and eval questions randomize order to measure it honestly);
  (ii) PARAPHRASE DIVERSITY: knowledge is only extractable if seen in
  multiple phrasings (Physics of LMs 3.1) — the dreamer manufactures
  varied paraphrases of the same regularity; corpus mixing is a
  requirement, not an optimization.
- **Anti-forgetting is corpus-level, not gradient-level:** dreams are
  incremental (new episodes only), the corpus is cumulative (all raw + all
  dreamed lines ever), and each cycle retrains the LoRA from scratch on the
  full shuffled corpus — every retrain sees everything, so forgetting is
  structurally impossible. (Dreamer re-reading OLD memories and reconciling
  them — true generative replay / renormalization of the past — is deferred
  to v2.1+ with its own gate: it trains on synthesized reinterpretation.)
- **Read:** LoRA arms = just generate from the adapted model (no tool call);
  RAG arms = top-k (k tuned honestly for the baseline) into the same prompt slot.
  **What the memory IS (Rohin's formalization, post-Nemotron):** a POLICY
  PRIOR, not a knowledge store — the read interface is "given current state
  + target state, what has worked", i.e. input + goal in, action prompt out.
  The memory captures pattern→action pathways; the environment tests exactly
  this (extrapolating action patterns across structured latents). Format
  stratum (e) and the task-success eval are this read made measurable.
- **Salience:** encoding-time = state (no hindsight); consolidation-time = dream
  (episode outcomes). Both hand-built; the pair is what paper 2 learns.
- **Division of labor (structural argument, goes in the paper):** the dreamer
  is context-bounded too — it fires per ~window and can only induce patterns
  visible within one chunk; regularities whose evidence spans hundreds of
  episodes are invisible to any single dream call. The dreamer does LOCAL
  work (dedup, salience filtering, orderings, paraphrases, goal-conditioning);
  the LoRA is the only component that spans all chunks — complementary by
  construction, not competing. RAG-dreamed is the built-in control: both
  dreamed arms share the identical corpus, so LoRA-dreamed minus RAG-dreamed
  isolates the substrate, not the dreamer.
- **Dreamer ladder (ablation axis; variants are just prompts):** raw
  transcription → per-episode summary → cross-episode patterns (current) →
  + prior-memory access (renormalizing; where cross-chunk induction first
  becomes possible — the SCALABLE form: the dreamer runs on the ADAPTED
  model, dreaming WITH everything consolidated so far at O(1) context cost,
  rather than pulling the store into context) → action-conditioned emission. The curve measures
  how much local processing the memory needs — v2 runs rungs 1 and 3; the
  full ladder is the first follow-up ablation.

## 7. Metrics, gates, falsifier
- **Primary:** held-out pair prediction accuracy (ground truth known — we set the
  latent), **confabulation priced**: "unknown" allowed; confident-wrong scored
  below abstain. **Secondary:** task success on fresh targets. Report both.
- **Gates before any headline:** (G1) seen-pair recall ≥0.9 in LoRA arms (else
  training is broken, not the thesis); (G2) zero essence-vocabulary leakage in
  any emitted text; (G3) no_memory stays flat across scale.
- **Falsifier (named point, metric, margin — no escape hatch):** at the
  **3840-episode point**, on **tier-3-normalized held-out composition score**
  (confabulation-priced, 200 questions/arm), LoRA-dreamed must exceed the
  best RAG arm by **≥0.05 absolute** AND be significant across 5 seeds
  (paired t, p<0.05) — while G1 passes. Fail ⇒ the substrate claim is dead
  in this form. Supporting (not substitute): LoRA-dreamed slope 960→3840
  positive while best-RAG slope ≤0. Pre-registered losses we print: RAG wins
  exact recall at every scale; long-context wins at 60/320.

**Sequence:** smoke test (6 ingredients, 20 eps, one arm, no measurement — plumbing
only, on Qwen2.5-0.5B local) → time one episode → real run on leased GPU (7B).

---

# PART II — In-depth sizing pre-registration
*(Everything below is reproducible:
`PYTHONPATH=. .venv/bin/python alchemy/sizing_mc.py` → alchemy/sizing_mc.json.)*

## 0. Why this document exists
Session-1 postmortem: we did not scope experiment size before running, and
paid for it in reversals. This time every scale number is either (a) computed
by Monte Carlo against the actual environment code, or (b) an explicit
literature-anchored estimate, BEFORE any GPU hour is spent.

## 1. The instrument: information-availability ceiling
For a life of E episodes, an IDEAL learner (union-find constraint propagation
over product-family evidence; provably-correct class links, purity 1.00 in all
runs) deduces some fraction of held-out pairs from the log alone. **No memory
system can beat this ceiling** — it is what the log contains, independent of
any substrate. It gives us:
- the episode scale where the experiment is winnable (ceiling must still be
  RISING across the x-axis, else there is nothing to accumulate);
- an oracle line for the paper's main figure;
- a normalizer (report arm score / ceiling).
**What the ceiling number means (Rohin's perfect-reasoner challenge —
resolved in three tiers, same evidence, increasingly smart reasoner):**
- **tier 1, retrieval-evidence** (directly observed rules only): →0.46;
- **tier 2, + class-transfer inference** (observed outcomes propagate across
  proven same-class ingredients): →0.77;
- **tier 3, + statistical elimination** (never product/ruin AND 'nothing' vs
  ≥8 distinct proven classes ⇒ inert; P(err)<0.4^8): →**1.00** — the world is
  fully compositional, no fact islands (Rohin's ≥90% intuition confirmed).
Headline normalizer = tier 3. The tier ladder is itself a figure: what each
increment of REASONING is worth on identical evidence. Remaining conservative
bias: the ScriptedExplorer is coverage-maximal (a real LLM player accrues
slower) — stretches true accrual RIGHT. Safe direction.
**On i.i.d. rules vs the induced-regularities claim (advisor tension, Rohin
resolution):** a purely i.i.d. table makes ingredient→class membership the
ONLY induced regularity — true but modest. Resolution = the **pattern-
spectrum mixture** (Part I §2): the rule table is generated from a mixture of
(ρ_iid) incompressible i.i.d. rules (must be experienced; where retrieval
holds its own — printing that loss is what makes the wins credible),
(ρ_fn) rules from a hidden function over essence properties (learnable
representation ⇒ predicts rules NEVER observed in any form — beyond the
observational ceiling), and (ρ_analog) functionally-analogous rules
(structurally similar pairs share outcomes). **Sweep the mixture ⇒
performance as a function of world compressibility** — answers "WHEN does
this substrate win", the map-not-victory form. Caution (advisor): do NOT try
to estimate reality's true pattern distribution — parameterize, sweep,
report the curve; reality-matching is a discussion claim, not a design
dependency.

## 2. The two failures the MC caught before they cost GPU time
1. **Latent too small.** 24 ingredients / 4 essences = 10 rules: ceiling
   saturates by 30 episodes. There is no scaling curve to measure. (Sweep:
   4→8→12 essences at N=48–96 all saturate by ~240 eps.)
2. **"Learnable" must mean "learnable BEYOND context", not "learnable from
   the log."** (Rohin's catch.) With N=64/K=12 the accrual phase ends at
   ~120 eps ≈ 42k log-tokens — a 128k-context baseline holds ALL informative
   experience in-window and the regime is not hard. The accrual phase itself
   must outrun the context window.

## 3. Sweep evidence (3 seeds; ceiling = deducible fraction of held-out pairs)
| config | 60 eps | 240 | 960 | 1920 | 3840 | verdict |
|---|---|---|---|---|---|---|
| N=24 K=4 (v0) | .36* | .39 | .39 | — | — | dead by 30 eps |
| N=64 K=12 | .39 | .47 | .47 | — | — | dead by 120 eps |
| N=128 K=16 | .10 | .43 | .43 | .43 | .43 | dead by ~240 |
| N=192 K=20 | .02 | .40 | .46 | .46 | .46 | dead by ~500 |
| N=256 K=24 | .00 | .33 | .47 | .47 | .47 | dead by ~700 |
| N=256 K=32 | .00 | .20 | .46 | .46 | .46 | dead by ~800 |
| N=512 K=64 | — | — | .37 | .46 | .46 | dead by ~1900 |
| **N=1024 K=96 (LOCKED)** | — | — | **.03** | **.42** | **.76** | **accrual → ~3.8k eps** |
| N=2048 K=128 | — | — | .00 | .01 | .20 | rejected: first 2k eps dead |
(*at 30 eps. Tier-1 asymptote ≈0.46 everywhere = product-rule share ×
reactive-pair share — a property of the rule mix, not of scale. Tier-3
ceiling at the lock: 0.05 @960 → 0.61 @1920 → 0.99 @3840 → 1.00 @7680.)

**Locked config (single source of truth, matches Part I §2):** 1024
ingredients (128 inert), 96 essence classes (4,656 rules), inventory 6,
≤12 steps, 30% structural holdout (never co-present in an inventory).
Measurement points **60 / 320 / 960 / 1920 / 3840 / 7680 / 15360** episodes
(same list as Part I §5): two early calibration points where context still
fits, four in accrual, one deep in repetition.

## 4a. The 5–10× requirement (Rohin)
Beating context by ~40% is not the regime — at +100% the LTM barely holds
representation the STM couldn't, and long-context+RAG hybrids plausibly tie.
Requirement: the ACCRUAL PHASE ALONE (info still arriving) must span
**5–10× the reasoner's context window**. Levers, in order of honesty:
(1) latent size — RESOLVED: N=1024/K=96 gives accrual to ~3.8k eps ≈ 1.27M
tokens ≈ 10× of 128k (N=2048/K=128 stretches further but wastes its first 2k
episodes at ceiling≈0.01; rejected); (2) honest window choice — Qwen2.5-7B
native = 32k (40× without rope tricks; 128k variants reported too);
(3) pattern-spectrum mixture depth multiplies information without token cost
(PROMOTED — see §1 and Part I §2).

## 4. Context-budget table (the honest long-context arm)
Log = **332 tokens/episode** (MEASURED with the real Qwen tokenizer over a
generated 500-episode life; the earlier chars/4 estimate of ~200 was 66% low).
| episodes | log tokens | 8k ctx | 32k | 128k | 1M |
|---|---|---|---|---|---|
| 60 | ~20k | broken | ok (calib.) | ok | ok |
| 320 | ~106k | broken | broken | ok (calib.) | ok |
| 960 | ~319k | broken | broken | **BREAKS HERE** | ok |
| 1920 | ~638k | broken | broken | broken | ok |
| 3840 | ~1.27M | broken | broken | broken | **BREAKS HERE** |
| 7680 | ~2.5M | broken | broken | broken | broken |
| 15360 | ~5.1M | broken | broken | broken | broken |
Accrual alone (to ~3840 eps) ≈ 1.27M tokens = **10× a 128k window**, 40× of
Qwen native 32k. Even a 1M window breaks INSIDE accrual — no context length
that exists holds this life. That is the regime definition.
The long-context arm uses the reasoner's real window; each break row is a
reported result ("N/A beyond E episodes"), not a handicap. Info is still
ARRIVING at every break point — the regime is genuinely beyond-context,
which answers "isn't this just in-context learning": past ~960 episodes it
physically cannot be.

## 5. Memory-capacity estimate (why LoRA size is NOT the binding constraint)
To master the world: 1024 class memberships + 4,656 rules +
~317 product families ≈ 10–20 kB of structure; dreamed corpus at 3840 eps
≈ 5–15k unique text lines ≈ 0.3M tokens. LoRA r=16 on a 7B (q,k,v,o) ≈ 30M
params; knowledge-capacity literature (~2 bits/param, Allen-Zhu & Li
"Physics of LMs 3.3") puts usable capacity orders of magnitude above need.
The binding constraint is **exposure** (facts stick with repetition +
paraphrase diversity — which is what the dreamer manufactures), not space.
Rank sweep {8, 32} stays: if the plateau moves with rank we've shown a
capacity limit; if not, a mechanism limit. Either is a finding.

## 6. Throughput plan (Rohin: "efficiency is paramount")
- **Life generation is FREE.** The experience stream is generated by the
  ScriptedExplorer — zero LLM tokens, 0.1s per 960-episode life (after the
  recipe-map caching fix; was minutes). 15,360-episode lives are trivial.
  All arms share ONE life stream per seed; points are prefixes of it.
- **LLM costs, per seed (at the CURRENT eval sizes — 7 points, 200/200):**
  task-success eval play: 6 arms × 7 points × 200 eps × 12 steps × ~700 tok
  ≈ **70M tok** (the dominant cost). Held-out prediction: 6 × 7 × 200
  questions × ~200 tok ≈ 1.7M tok. Dreams: ~160 cycles (96-ep cadence) over
  a 5.1M-token log ≈ 6–8M tok. LoRA trains: 2 substrate arms × 7 points,
  late-point corpora ~2M tok × 4 epochs ⇒ ~3–4 A100-hr/seed.
- **Total ≈ 73M LLM tokens ≈ 8–10 A100-hr/seed → 5 seeds ≈ 2 days on one
  A100, ~1 day on two** (or a few hours on Blackwell-class). Episode count
  is NOT the cost driver; eval play is. (History: this section originally
  said ~10M tok/half-day at 4 points × 40 eps — superseded when the audit
  raised eval sizes; kept honest here because this is the number that
  justifies the lease.)

## 6b. Game generation is a first-class research problem (Rohin)
The real world ties ideas/outcomes together naturally; we must AMORTIZE that
structure in a generator — enough nondeterminism that answers are not
literally retrievable, enough connectedness that composition pays. This is a
parameter-search problem run through the sizing MC (episodes, ingredients,
essence count, chain depth 10–20 at 10k-episode scale, rule-structure mix,
repetition rate), accepted only inside the target zone: tier-3 ceiling ≥0.9,
accrual ≥5× context, early points alive, achieved-vs-ceiling gap wide.
Prior art to mine for split methodology: compositional-generalization
literature — SCAN, COGS, gSCAN — which constructs train/test splits where
answers are derivable ONLY by composing, never by recall. Their split
discipline transfers directly; procedural-content-generation lit less so.

## 7. Pre-registered predictions (falsifiable, written before the run)
- long_context ≥ everything at 60 eps (all info in-window); N/A by 960.
- RAG arms: rise through accrual, then FLAT-TO-FALLING 960→3840 (index
  grows, k fixed, redundancy floods similarity).
- LoRA-dreamed: below RAG at 60 (few exposures — injection needs
  repetition), crosses during accrual, keeps rising 960→3840 (repetition
  is consolidation fuel), tracks nearest to ceiling at 3840.
- LoRA-raw vs LoRA-dreamed gap = the curation claim; if ~0, substrate-only
  paper (still a paper — and redirects paper 2).
- RAG wins exact-recall (seen pairs) at every scale. Printed, not hidden.
- **Forgetting-as-capacity-gauge (pre-registered):** forgetting is allowed
  (graceful, by design); EXCESS forgetting is a capacity diagnosis. The G1
  seen-pair-recall curve across checkpoints, per rank: degrading at rank 8
  while holding at rank 32 locates the capacity ceiling directly.
- **Rank×mixture interaction (free second result, pre-registered):** if
  memorization favors parameters and representation-finding favors data,
  optimal LoRA rank shifts with the mixture — high ρ_iid worlds want rank
  32 over 8; high ρ_fn worlds shouldn't care. Both sweeps already run.
- **Named headwind (goes in related work, not discovered in review):** the
  literature consistently finds fine-tuning UNDERPERFORMS RAG for injecting
  atomic new facts and can raise hallucination elsewhere. Our claim is not
  fact injection — it is induced regularities, the thing retrieval
  structurally cannot produce; the ρ_iid stratum is where that literature
  applies and where we pre-register our loss.
- KILL: if LoRA-dreamed never beats both RAG arms on held-out composition
  at any point while G1 (seen-pair recall ≥0.9) passes.

## 8. Parameter ledger — tested vs derived vs guessed (kept honest, updated per change)
**TESTED (MC against real env code):** N=1024/K=96/128-inert lock (+ all
rejected configs 24→2048); three ceiling tiers + full accrual curves
(5 seeds at lock); accrual ≈1.27M log-tokens under tier-3 (332 tok/ep measured); context-break
points; structural holdout (assert-verified, 0 contamination); inert
elimination 127–128/128; life-gen throughput (0.1s/960 eps); smoke
pipeline end-to-end on 0.5B (timed).
**DERIVED (arithmetic on tested numbers):** sleep cadence ~96 eps
(32k / 332); elimination threshold T=8 (0.4^8).
**PROMOTED TO TESTED:** 332 tok/episode (real Qwen tokenizer over a
generated 500-ep life; replaced the chars/4 ≈200 estimate, which was 66%
low — context table rebuilt on the measured number).
**GUESSED (defaults / literature-anchored; sensitivity untested):** rule
mix 60/25/15 (directly sets ceiling asymptotes — sensitivity sweep TODO);
inventory 6; ≤12 steps; holdout 30%; grades {1,2}; seeds 5; LoRA rank
{8,32}; ALL GPU costs at scale (never benchmarked); whether a LoRA learns
this at all (= the experiment, not a parameter).
**SPEC-AHEAD-OF-CODE (flagged):** (a) chain targets depth 1–3 claimed in
§2 but generate_life only issues depth-1 targets today; chains exist in
the physics, no episode pursues one, MC doesn't measure chain deducibility.
Next generator milestone (10–20-ingredient chains, Rohin). (b) the
pattern-spectrum mixture (ρ_iid/ρ_fn/ρ_analog) is specified and PROMOTED
but not yet implemented in world.py — today's rule table is 100% ρ_iid;
implementing the mixture + its ceiling semantics is generator milestone 2.
(c) eval sizes (200/200) and the tightened falsifier are spec'd, harness
not yet built.


---
# PART III — V3 GAME SPECIFICATION (accumulating; near-complete)
*(Every ruling from the v2 diagnosis era, consolidated. Rohin gates each
stage. Updated as patterns are discovered.)*

## World structure
- INDUCIBLE STRATUM = one-hop, SET-SCOPED regularities only: same-class
  ingredients behave identically; learning one class-pair rule covers all
  member pairs (pattern propagates across the set, never one-off x~x').
  The circle geometry is DEAD (IMO-puzzle-grade; unrealistic).
- Candidate config (pathway-sweep-locked, pending induction ladder):
  N=192 ingredients / K=12 classes / tiers 4 / rho_fn 0.7 —
  analogy goals 42%, lookup 38%, novel 21% (ceiling check), 149 goals,
  median solution-shape practiced 15x, ~6.3k observations per class.
- Structure size must fit MEASURED memory capacity: 78 rules + 192
  memberships ~= 270 items (capacity curve: fine at rank>=64).
- iid stratum stays at ~30% AS CONTROL (equal improvement on inducible
  and lookup-only content = general improvement, not induction — the
  gap is the evidence).
- Induction difficulty LADDER — rung 1 MEASURED (one-hop, curated
  evidence, n=300): with abstention available the model refuses (98%
  abstain); FORCED commitment unlocks kind 0.58 / family 0.20; a schema
  hint adds NOTHING (the leap is known, unvolunteered). Oracle with
  explicit structure = 0.91. ⇒ two priced routes: thinker-elicited
  in-context induction ~0.20 one-shot; dreamer-precomputed structure
  ~0.91. PLAY-LOOP RULE: no abstention in games — retries are the
  safety valve; k-try-with-feedback climb from 0.20 is the last number
  gating the game lock. Rungs 2-4 (chain/compositional/set-level) after.
  (alchemy/v2_out/induction_variants.json)

## Metric (headline)
Paired per-goal TRIES-TO-GOAL, k attempts with outcome feedback, capped
with censoring reported; identical goal set across arms; split =
analogy-goals vs lookup-goals (procedure induction vs recall); one-shot
task success secondary; fact quiz demoted to probe (family credit).

## Dream / Think (amortized as agent calls, co-designed)
- DREAMER-AGENT: consumes context-window batches of memories (+ prior
  cycles), instructed to hunt known pattern types ("what behaves
  similarly; keep looking until dry; guess; test guesses"), emits
  multi-perspective memories. VOYAGER RULE: every dream engine-verified
  before entering the corpus. Dream types: symmetry/substitution,
  generalization, procedural abstraction, counterfactual.
- THINKER-AGENT: query = goal + inventory (state, not quiz); retrieves
  plan fragments in two reported channels (exact-material / analogous-
  shape); builds prompter context; drives the retry loop.
- Perspectives micro-test feeds dream sizing: constant gradient steps,
  vary distinct framings (1x200 / 10x20 / 40x5), 3 seeds.

## Eval-engineering rules (learned the hard way)
- NO tiny generation caps on eval calls (24-token cap = corrupted
  measurement; batched inference is cheap).
- Family-level credit primary where hidden state (grades) makes exact
  names underdetermined.
- Per-kind-within-stratum decomposition on any stratified metric
  (kind-mix differences manufacture fake gaps).
- Every reported number from a repo script; controls must be able to
  fail; n>=3 seeds on anything called a recipe.

---

# Part IV — LANDS (v0 CPU instrument implemented on `semantic-world-v0`)

Canonical frozen v0 contract:
[`research_notes/34_semantic_world_v0_spec.md`](research_notes/34_semantic_world_v0_spec.md).
Implementation and CPU gates: [`lands/`](lands/).  The material below is
the originating draft; where it differs, note 33 and executable tests win.

The prior-anchored main experiment (nonce L0 kept as zero-prior control).

## World
- K lands: candyland, mandyland, dandyland, randyland, ... (known words —
  the ontology rides the base image).
- N animals (cow, monkey, fox, ...) and C colors on a color wheel.
- HIDDEN LAW (random per seed, priors can't shortcut): each animal has a
  latent base index b(a); each land a latent shift s(l);
  color(a, l) = wheel[(b(a) + s(l)) mod C].
  Cross-land regularity: knowing cow's color in 2 lands + another
  animal's colors pins down both latents -> predict cow in randyland.
- SALIENT-DIFF layer (surprise stratum): a few per-land exceptions
  ("in dandyland, exactly one animal is colorless") to test
  prior-contrast dreaming.
- Episodes = land visits with small goals (find/feed the <color> <animal>);
  observations carry provenance implicitly ("In mandyland you see the cow.
  It is red."). One visit fits a context window; the LAW spans visits.

## Why context can't just learn it
Per-visit evidence underdetermines the law; the induction needs
observations from >=3 lands that never co-occur in one window at target
scale (dial: K x N x C, plus visit sparsity).

## Evals (each stratum measurable)
1. Situated recall: "what color was the cow in mandyland?" (provenance)
2. Cross-land composition: unseen (animal, land) cells — the headline
   (analogy split), with iid holdout as control ("the gap is the evidence")
3. Prior-contrast probes: "are cows usually red?" (must keep the base
   image intact — oracle-in-weights gate)
4. Second-order: "which colors recur across lands?" / secondary-color
   inference — connections dreamed over accumulated memories
5. Grouping/projection: "which animals share the cow's base color?" (F1)
6. Tries-to-goal with feedback across visits (pass@k capability curve)

## Method (unchanged G-series ladder, now proven on nonce L0)
Component oracles first (context oracle; storage oracle with ideal dream
statements at 200 touches; resolved atomic reads; clean-base compose),
then real dreamer (verified-claim graph + daydreaming rounds + coined
names e.g. "the sunset-shifted lands"), then end-to-end vs context/RAG
arms. Identifier-vividness A/B: same latent structure, nonce skin vs
lands skin — the paper's prior-scaffolding section.

## V0 locks
- two three-color palettes (primary and secondary), with a randomized
  rotation per land and randomized invariant role per animal;
- one uniquely identifiable three-parent meta-land using associative paint-
  pigment union (Blendyland in the aligned skin);
- aligned, neutral, and prior-conflicting skins over identical latent data;
- no exceptions or behaviors until factor transport passes;
- D0 situated lookup / D1 local projection / D2 cross-palette composition /
  D3 meta-rule composition, each backed by a canonical dependency DAG.
- a priced post-dream reachout stage for structural evidence gaps, with exact
  evaluation-target visits blocked and every action counted as experience.
