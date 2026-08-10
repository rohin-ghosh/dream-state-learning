# Red-team response — what broke, what got fixed, honest corrected results

Three adversarial agents + my own review attacked StructMem-Bench v0.1 (two agents
also died on API errors mid-run; findings below come from redteam_1_gameability,
redteam_3_code_stats, and self-review; config-robustness was done directly).

## CRITICAL bug (found 3× independently) — position leak via tie-breaking
Facts were laid out contiguously by type (structural at low indices) and every
ranking metric used a STABLE argsort → ties broke by ascending index → structural
facts ranked first for free. A **zero-information index-ranking method scored
AP=1.000** (tied the oracle), and the canaries could not catch it. It also
contaminated real methods: "surprise recovers rare structure" (rare_ret 0.530) was
**pure layout artifact** — now 0.023.

**Fixed by (defense in depth):**
1. Seeded column-permutation in `tasks.generate` → fact index ⊥ type on every path.
2. Tie-safe ranking (`metrics._order_desc`): ties broken by a fixed RANDOM order, not
   index.
3. New **constant-scorer canary** + `worst_positional_ap` probe + regression tests.
Verified: blind index-ranking AP 1.000 → 0.033 (≈ chance); surprise AP 0.277 → 0.015.

## Other fixes
- **Canary gap:** the permutation canary was only run on `frequency`; now the rigor
  suite runs a constant-scorer canary (catches position leaks) every run.
- **Relational candidate explosion:** one-shot details created spurious pairs; now
  restrict candidates to co-occurrence ≥ 3, and recipes are drawn from FREQUENT
  structural facts (a relation seen once isn't a fair test).
- **Budget artifact:** report a recipe/data sweep, not one cherry-picked budget.

## Honest corrected results (30 seeds, hardened)
Rigor: all canaries at chance (~0.03 vs base rate 0.024); blind index AP 0.033;
frequency uninformative on matched facts (dP −0.06); frequency fails hard cases by
construction (rare_kept 0.000, recurring_detail_kept 0.703).

Relational tier (the surviving novelty) — **advantage is REAL but REGIME-SPECIFIC:**

| episodes | recipes | relational | item_lifted | advantage |
|---:|---:|---:|---:|---:|
| 200 | 8 | 0.399 | 0.388 | +0.011 (n.s.) |
| 200 | 4 | 0.521 | 0.343 | **+0.178 (t=3.6)** |
| 300 | 4 | 0.622 | 0.415 | **+0.206 (t=3.9)** |
| 300 | 2 | 0.556 | 0.393 | +0.163 (t=2.6) |
| 400 | 1 | 0.695 | 0.709 | −0.013 (n.s.) |

Relational value beats per-item **significantly in the middle regime** (a few
critical dependencies + adequate data) but NOT when dependencies are many-and-diffuse
(data-starved) or a single pivotal pair (per-item product suffices).

## What this means (honestly)
- exp3's "relational AP 1.0" was a favorable-small-universe artifact — the same
  species of self-deception as exp2's matched model class. Hardening deflated it to a
  regime-specific significant effect.
- The benchmark is now an adversarially-hardened, honest instrument. Its value is NOT
  "our method wins everywhere" — it's a rigorous ruler that shows (a) frequency/
  surprise fail structurally, (b) per-item value is limited under relational outcomes,
  (c) relational value helps in the regime that matters (concentrated dependencies)
  and honestly does not elsewhere.
- Contribution posture: this strengthens the BENCHMARK-as-contribution and tempers
  the METHOD claim. Exactly what a benchmark should do to its own method.
