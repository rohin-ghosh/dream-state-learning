# Competitive Verdict — Parametric Memory Landscape (2026-08-10)

Synthesis of 6 deep-read agents (notes 12–17) + earlier surveys (00–11). One agent
(PEAM cluster follow-ups) died on an API error; PEAM itself is covered in notes
03/09/11/12.

## The landscape is one of the hottest sub-areas in ML right now
Six+ parametric-memory papers in ~3 months (May–Aug 2026). EVERY axis of the
original "dream-state value-gated parametric memory" idea is now occupied:

| Axis | Occupied by |
|---|---|
| Parametric fast-weight memory | Titans, ATLAS/2505.23735, MIRAS, HOPE, TMEM, EVAF |
| Value/reward-gated writes | D-MEM (RPE), TMEM (RL extraction), EVAF (valence) |
| Offline cross-episode consolidation | COVE, ATLAS-b/2608.04334 |
| What-to-internalize / anti-recitation forgetting | COVE |
| CLS hippocampus/neocortex framing | User-as-Engram |
| Parametric embodied-agent skill internalization | PEAM (heuristic) |

Nearest single papers: **D-MEM** (dopamine-gated memory writes, RPE-trained, frozen
backbone — ~90% of our "value gate" axis); **TMEM** (RL-shaped LoRA writes, but
online within-episode — cousin, not collision); **COVE** (offline cross-episode
what-to-internalize + anti-recitation forgetting — HIGH collision, but per-item and
surface-form).

## What NO competitor has (the surviving novelty)
Collapsed onto essentially ONE axis + its combination:
1. **RELATIONAL value** (per-dependency, not per-item) — unseen anywhere. [exp3]
2. **RELATIONAL-structure-vs-episodic-detail forgetting** — distinct from COVE's
   surface-form/volatility partition and everyone's per-item.
3. The specific 4-way combination + rigorous, honestly-measured execution.

Every competitor uses PER-ITEM value and forgets on surface-form/volatility/recency
axes. The relational axis is the one clean thing.

## Honest verdict
The "value-gated parametric memory / dream-state" framing AS A WHOLE is occupied.
An independent researcher (no lab) being the 7th method paper at this exact
intersection, racing funded labs (Google, Alibaba) who execute faster, is a
structurally weak position. The defensible core is narrow: **relational
value/structure consolidation.**

## Options (ranked by honest expected value)
1. **Benchmark + relational method (RECOMMENDED).** Nobody has a ground-truth
   structure-vs-detail retention benchmark (we half-built it — the crafting sim
   with dependency graphs). Build it; evaluate the CROWD (COVE, TMEM, PEAM, D-MEM,
   EVAF) on relational-structure retention; show they all miss it; show
   relational-value consolidation fills it. In a crowded field, the referee with
   the ruler beats the 7th runner. Turns the crowd into an asset.
2. **Pure benchmark/analysis paper.** Just the measurement + evaluation of the
   field. Safest, least contested, still citable; smaller claim.
3. **Pivot to a less-crowded cell** of the cognitive-stack program map (JOURNAL).
   The relational-memory insight is real but the surrounding apparatus is saturated.
4. **Race the narrow lane** (relational value method paper). Highest risk; requires
   speed we may not have vs funded labs.

## Recommendation
Lead with **the benchmark** (Option 1/2). It is the one thing here that is (a)
genuinely unowned, (b) already half-built, (c) immune to being scooped by another
method paper (a benchmark gains value as the field grows), and (d) the natural home
for the relational-structure insight that IS our surviving novelty. The method
(relational-value consolidation) becomes the benchmark's headline result, not a
standalone claim competing with D-MEM/TMEM/COVE on their turf.

## Caveats
Fast-moving area; 2606–2608 IDs at moderate confidence; re-sweep before any
submission. COVE's exact substrate (fast-weights?) and any implicit reward-shaping
under-read — verify before drawing the fast-weight distinction in print.
