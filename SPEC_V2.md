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
  · **Stratum G (geometric)** — rules generated from a hidden meta-pattern
    (essence classes on a hidden cycle/lattice; outcome = function of
    distance; grade arithmetic). A learner that finds the representation can
    predict rules NEVER OBSERVED IN ANY FORM — extrapolation beyond the
    observational ceiling. Retrieval cannot in principle. 🔴 include in v2?
    (my rec: yes — it is the induced-regularities claim at its purest)
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

## 5. Scaling axes
x-axis is always **episodes**: measure at 960 / 1920 / 3840 / 7680 / 15360 —
all prefixes of ONE frozen life stream (same experience, growing exposure):
four points in accrual, the last deep in repetition. Plus two EARLY
calibration points, 120 (~24k tok, fits 32k ctx) and 480 (~95k tok, fits
128k ctx), where long-context is still alive — its early win must be
MEASURED and printed, not assumed (the crossover needs both ends).
Life generation is LLM-free (scripted explorer) → episodes are free; the cost
driver is eval play (~1 A100-hr/seed total; Part II §6). Secondary: LoRA rank {8, 32} — if the parametric
ceiling moves with rank, saturation is capacity, not mechanism. LoRA retrained
from full curated corpus at each measurement point; checkpoint frozen per point
(drift allowed by design, never inside a measurement).

## 6. Mechanism (all amortized; per-box info-set gate)
- **State** (trivial v2): goal, inventory, last outcome, game value. Logged.
- **Sleep cadence (Rohin):** a dream cycle fires every time ~one context
  window of experience has accumulated (~32k tok ≈ 160 eps): dump STM → dream
  → retrain LoRA from full corpus → resume. Measurement checkpoints align
  with dream boundaries. (~96 cycles over a 15,360-ep life; minutes each.)
- **Value function:** exact, from ground truth — BFS distance over the true
  crafting graph from holdings to target. No learned VF needed at this scale;
  logged per step into state (the dream's hindsight signal).
- **Dreamer = one prompted LLM call** per log chunk: sees episodes + outcomes +
  value logs (episode hindsight OK, eval set never). Emits **cross-episode
  pattern memories as text** (2nd person), not per-episode summaries.
  Dumb-dreamer arm = raw log transcription. **Memory text format (signed off):
  a MIX** — (a) declarative recipe facts, (b) cross-episode pattern/analogy
  lines, (c) a QA-format slice (matches the eval's register), (d) negative
  knowledge (nothing/ruin pairs). All strata leakage-scanned.
- **Read:** LoRA arms = just generate from the adapted model (no tool call);
  RAG arms = top-k (k tuned honestly for the baseline) into the same prompt slot.
- **Salience:** encoding-time = state (no hindsight); consolidation-time = dream
  (episode outcomes). Both hand-built; the pair is what paper 2 learns.

## 7. Metrics, gates, falsifier
- **Primary:** held-out pair prediction accuracy (ground truth known — we set the
  latent), **confabulation priced**: "unknown" allowed; confident-wrong scored
  below abstain. **Secondary:** task success on fresh targets. Report both.
- **Gates before any headline:** (G1) seen-pair recall ≥0.9 in LoRA arms (else
  training is broken, not the thesis); (G2) zero essence-vocabulary leakage in
  any emitted text; (G3) no_memory stays flat across scale.
- **Falsifier:** if LoRA-dreamed never beats both RAG arms on composition/chain
  queries at ANY experience scale while G1 passes — the substrate claim is dead
  in this form. Pre-registered: RAG wins exact recall; we print that loss.

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
**What the ceiling number means (and Rohin's perfect-reasoner challenge):**
the rules are i.i.d. random BY DESIGN, so unobserved rules are independent
coin flips — no reasoner can derive the unseen from the seen. That
incompressibility is the point: it makes experienced data the only winning
resource (the thesis). But the learner's evidence model matters, so we report
TWO ceilings:
- **conservative** (product-evidence only): asymptote ≈0.46;
- **perfect-reasoner** (v2: any observed outcome transfers across proven
  same-class pairs): asymptote ≈0.77. The residual ~23% = pairs involving
  inert ingredients (1−(7/8)² — unclassable without elimination logic).
Headline normalizer = the perfect-reasoner ceiling. Remaining conservative
bias: no elimination logic, and the ScriptedExplorer is coverage-maximal (a
real LLM player accrues slower) — both stretch true accrual RIGHT. Safe
direction. NOTE: a Stratum-G latent (Part I §2) has NO observational ceiling
— a perfect representation-learner can exceed it; that is measured as
extrapolation-beyond-ceiling, the strongest possible win condition.

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
| N=256 K=24 | .00 | .33 | .47 | .47 | .47 | accrual → ~700 |
| **N=256 K=32 (LOCKED)** | **.00** | **.20** | **.46** | **.46** | **.46** | **accrual → ~800** |
(*at 30 eps. Asymptote ≈0.46-0.47 everywhere = product-rule share × reactive-
pair share — a property of the rule mix, not of scale.)

**Locked config:** 256 ingredients (32 inert), 32 essence classes (528 rules),
inventory 6, ≤12 steps, 30% structural holdout (never co-present in an
inventory). Measurement points **60 / 240 / 960 / 3840** episodes:
three points inside accrual, one deep in repetition.

## 4a. The 5–10× requirement (Rohin)
Beating context by ~40% is not the regime — at +100% the LTM barely holds
representation the STM couldn't, and long-context+RAG hybrids plausibly tie.
Requirement: the ACCRUAL PHASE ALONE (info still arriving) must span
**5–10× the reasoner's context window**. Levers, in order of honesty:
(1) latent size — RESOLVED: N=1024/K=96 gives accrual to ~6k eps ≈ 1.2M
tokens ≈ 8–11× of 128k (N=2048/K=128 reaches 12× but wastes its first 2k
episodes at ceiling≈0.01; rejected); (2) honest window choice — Qwen2.5-7B
native = 32k (30×+ without rope tricks; 128k variants reported too);
(3) Stratum-G depth multiplies information without token cost (🔴 pending).

## 4. Context-budget table (the honest long-context arm)
Log ≈ 200 tokens/episode (measured from generated logs, chars/4).
| episodes | log tokens | 8k ctx | 32k | 128k | 1M |
|---|---|---|---|---|---|
| 960 | ~190k | broken | BROKEN | ok | ok |
| 1920 | ~380k | broken | broken | **BREAKS HERE** | ok |
| 3840 | ~770k | broken | broken | broken | ok |
| 7680 | ~1.5M | broken | broken | broken | **BREAKS HERE** |
| 15360 | ~3.1M | broken | broken | broken | broken |
Even a 1M-token window breaks INSIDE the accrual phase — no context length
that exists holds this life. That is the regime definition.
The long-context arm uses the reasoner's real window; each break row is a
reported result ("N/A beyond E episodes"), not a handicap. Info is still
ARRIVING at the 128k break point (ceiling .20→.46) — the regime is genuinely
beyond-context, which answers "isn't this just in-context learning": past
240 episodes it physically cannot be.

## 5. Memory-capacity estimate (why LoRA size is NOT the binding constraint)
To master the world: 256 class memberships (~8 bits each) + 528 rules +
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
  recipe-map caching fix; was minutes). 3840-episode lives are trivial.
  All arms share ONE life stream per seed; points are prefixes of it.
- **LLM costs, per seed:** dreams: ~3840 eps in ~384 chunks × ~1.5k tok ≈
  0.6M tok (minutes on vLLM). LoRA trains: 2 substrate arms × 4 points ×
  minutes. Task-success eval play: 6 arms × 4 points × 40 eps × 12 steps
  × ~700 tok ≈ 8M tok ≈ 45 min A100. Held-out prediction eval: 6 arms × 4
  points × 200 questions × ~200 tok ≈ 1M tok.
- **Total ≈ 10M LLM tokens/seed ≈ 1 A100-hour/seed → 5 seeds ≈ half a day
  on one A100.** Doubling everything still fits inside the 30-day quota
  many times over. Episode count is NOT the cost driver; eval play is.

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
- KILL: if LoRA-dreamed never beats both RAG arms on held-out composition
  at any point while G1 (seen-pair recall ≥0.9) passes.

## 8. Parameter ledger — tested vs derived vs guessed (kept honest, updated per change)
**TESTED (MC against real env code):** N=1024/K=96/128-inert lock (+ all
rejected configs 24→2048); three ceiling tiers + full accrual curves
(5 seeds at lock); accrual ≈770k log-tokens under tier-3; context-break
points; structural holdout (assert-verified, 0 contamination); inert
elimination 127–128/128; life-gen throughput (0.1s/960 eps); smoke
pipeline end-to-end on 0.5B (timed).
**DERIVED (arithmetic on tested numbers):** ~200 tok/episode (chars/4 —
NOT real tokenizer counts yet; re-measure); sleep cadence ~160 eps;
elimination threshold T=8 (0.4^8).
**GUESSED (defaults / literature-anchored; sensitivity untested):** rule
mix 60/25/15 (directly sets ceiling asymptotes — sensitivity sweep TODO);
inventory 6; ≤12 steps; holdout 30%; grades {1,2}; seeds 5; LoRA rank
{8,32}; ALL GPU costs at scale (never benchmarked); whether a LoRA learns
this at all (= the experiment, not a parameter).
**SPEC-AHEAD-OF-CODE (flagged):** chain targets depth 1–3 are claimed in
§2 but generate_life only issues depth-1 targets today; chains exist in
the physics, no episode pursues one, MC doesn't measure chain
deducibility. Next generator milestone (10–20-ingredient chains, Rohin).
