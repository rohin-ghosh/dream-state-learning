# SPEC v2 — Dreamed Parametric Memory vs Retrieval (one page)
*(2026-08-19. Co-design draft for Rohin's red pen. 🔴 = open decision for you;
everything else is a granular default I'll build unless overruled.)*

## 1. Claim
An agent whose experience is consolidated into weights (dream → LoRA) has a
**different scaling curve** than one that retrieves it: retrieval and long-context
flatten or bend as accumulated experience grows, parametric keeps climbing —
because it acquires **induced regularities** (cross-episode structure present in
no single episode). We measure the crossover; we report where retrieval wins.

## 2. Environment — AlchemyWorld
- **64 ingredients** (8 inert), nonce names (contamination-proof), each with a
  hidden **essence** ∈ **12 classes** + hidden **grade** ∈ {1,2}. Essences NEVER
  appear in any text (leakage is grep-able = property in the physics). Sized by
  Monte Carlo (alchemy/sizing_mc.py): 4 classes saturates by 30 episodes — the
  latent must carry enough information to accrue across the whole x-axis.
- **Rule table (per-run randomized):** unordered essence-pair → outcome family
  {product, nothing, ruin}. Product identity = f(essence pair, max grade) —
  compositional: knowing essences predicts **never-tried pairs**.
- **Chain depth:** products have derived essences → recipes chain (depth 1–3
  targets). **Distractors:** (a) inert-essence ingredients that never react;
  (b) visible surface features (color/smell) randomized independently of essence
  — a tempting false correlate.
- **Episode:** goal "craft ⟨target⟩", inventory = random subset of 6 ingredients
  (forces pair coverage to accrue only in aggregate), ≤12 combine steps,
  game value = depth-distance-to-target, logged per step (this is "state").
- 2016 base pairs; **held-out split enforced by construction**: 30% of pairs are
  never co-present in any episode inventory (physics, not luck — a coverage-
  maximizing explorer would otherwise see everything; smoke-test find).
- **Pre-registered oracle ceiling** (sizing MC, conservative ideal learner):
  deducible fraction of held-out pairs = 0.13 @30 eps → 0.39 @60 → 0.47 @120 →
  flat. Two named regimes: **accrual** (≤~120 eps, information arriving) and
  **repetition** (>120 eps, information constant, exposure growing) — repetition
  is where consolidation should shine and retrieval should drown. All arm
  scores reported alongside (and normalized by) this ceiling.

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
x-axis is always **episodes**: measure at 60 / 240 / 960 — all three are
prefixes of ONE frozen life stream (same experience, growing exposure). Secondary: LoRA rank {8, 32} — if the parametric
ceiling moves with rank, saturation is capacity, not mechanism. LoRA retrained
from full curated corpus at each measurement point; checkpoint frozen per point
(drift allowed by design, never inside a measurement).

## 6. Mechanism (all amortized; per-box info-set gate)
- **State** (trivial v2): goal, inventory, last outcome, game value. Logged.
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
