# Deep-Dive Guide (for Rohin's morning read)

**Status: DRAFT — being finalized during tonight's hardening pass. Sections marked
⏳ fill in after the red-team reports + fix pass.**

## How to read this repo in one sitting (order matters)

1. **This file** — the map + what changed overnight.
2. **`SIZING.md`** — every GPU-run decision and its recalibration rule. (~10 min)
3. **`IMPLEMENTATION_SPEC.md`** — the architecture harness; every [DECIDE]/[LOGIC]
   tag is a place your judgment is wanted. (~15 min)
4. **The code, in dependency order** (~900 lines numpy total):
   - `game/dag.py` (~120 ln) — procedural crafting DAG + the oracle. The oracle IS
     the value function for Stage 1; verify you believe `oracle_value`'s cost model.
   - `game/engine.py` (~200 ln) — the game + script-before-text fact labelling.
     The Fact taxonomy (recipe/location = structural; decor/count = detail) is a
     DESIGN CALL you should own.
   - `game/generator.py` (~90 ln) — worlds, curriculum, JSONL schema.
   - `felt/head.py` (~130 ln) — the scorer head + distillation + all-budgets
     regret. This is the paper's new object in miniature.
   - `felt/fastweight.py` (~100 ln) — the memory + w = surprise×(1+β·a).
   - `felt/baselines.py` / `felt/harness.py` — the zoo + the resumable runner.
5. **`experiments/REPORT_exp6.md`** — the integration result + its caveats.
6. **Red-team reports** `research_notes/redteam_4/5/6_*.md` — where the bodies
   were buried; read AFTER the code so you can judge the fixes.

## ⏳ What the overnight audit found & what was fixed
(filled in after reconciliation)

## ⏳ What was deliberately simplified
(filled in)

## ⏳ Known limitations we are CARRYING into the GPU tier (not hiding)
(filled in)

## ⏳ The lease spec
(filled in — pool, node type, duration, count)

## Design calls that are YOURS to overturn (agents can't adjudicate these)
- The Fact taxonomy (what counts as gist vs detail in the game).
- β's role: modulation strength is swept, but the FORM (multiplicative on
  surprise) is a spec decision (§3.1) — alternatives: additive, replace-surprise.
- The calibration gate thresholds (0.85 / 0.35) — SIZING §1.
- Curriculum shape (deepening goals) and world-interleave count.
- Whether S4 (closed-loop winnability) belongs in lease 1 or lease 2.
