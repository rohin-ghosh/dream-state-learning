> ⚠️ **RETRACTED (2026-08-12, red-team redteam_4).** The result below was an
> artifact stack: (1) the "felt effect" was carried by a HARDCODED fallback
> constant (decor facts bypassed the head; corr(felt, has-step gate)=0.999);
> (2) in the original game, fact type ≡ action type, so a zero-training keyword
> gate BEAT the trained head and was byte-identical to a label leak; (3) the
> probe metric had a cosine-floor confound (never-written fakes scored 0.595);
> (4) salted hash() made runs irreproducible. ALL FIXED (deterministic hashlib,
> decor-on-visit steps, detour rollouts breaking type≡salience, floor-corrected
> random probes, online surprise, keyword-gate canary). POST-FIX honest state:
> all realistic policies ≈ 0 differentiation on the corrected metric; the
> oracle-weight CEILING expresses only at hidden≥128 (+0.11 soft / +0.22 hard
> filter). Whether a trained head can approach that ceiling with REAL LLM hidden
> states is the GPU tier's open question. The CPU tier's validated role:
> plumbing, canaries, gates, and the measured ceiling — NOT a head-works claim.

# Report — Exp 6: Stage-1 miniature (full Felt-Attention pipeline, CPU)

**Date:** 2026-08-12 · **Code:** `experiments/exp6_stage1_miniature.py` (8 seeds,
held-out worlds) · The go/no-go rehearsal for the GPU tier.

## Pipeline (firewall intact)
Real FeltCraft rollouts → FeltHead trained by distillation on ORACLE TD-salience
(train worlds only; never sees probes/labels) → head salience attached to each
experienced fact's event → value-modulated writes into the fast-weight MLP memory
(w = surprise × (1+β·salience)) → gist/verbatim retrieval probes on HELD-OUT worlds.

## Results

Head transfer to held-out episodes: all-budgets regret **0.025**, salience corr 0.54.

| write policy | gist retrieval | detail retrieval | dissociation | AP(gist) |
|---|---:|---:|---:|---:|
| uniform | 0.481 | 0.607 | **−0.126** | 0.509 |
| surprise-only (β=0, stock substrate) | 0.478 | 0.603 | **−0.125** | 0.506 |
| felt (β=4) | 0.545 | 0.515 | +0.029 | 0.644 |
| felt (β=12) | 0.562 | 0.442 | **+0.121** | **0.707** |

Paired felt(β=4) − surprise-only on dissociation: **+0.154 (t=5.9, SIG)**. Monotone in β.

## The headline finding
**Surprise-only and uniform retain DETAIL over GIST (negative dissociation)** — the
stock substrate actively favors novel-but-useless episodic detail over recurring
relational structure. The trained head flips the sign. That is the paper's
hypothesized failure mode ("surprise keeps the wrong things"), now measured in a
real MLP memory on a real (toy) game, with the fix demonstrated by a head that
never saw a probe.

## Caveats
- Mock event embeddings (hash bag-of-words), not frozen-LLM hidden states — the GPU
  tier's central question is whether real hidden states carry the salience signal
  as well as (or better than) these mocks.
- Scripted optimal agent, not an LLM player; toy scale (30 eps/world, 48-hidden
  memory); salience→fact attachment is by step co-occurrence (coarse).
- β swept only at {0,4,12}; no tuning beyond defaults anywhere.

## Verdict
CPU-tier GO. Every component of Stage 1 now exists, is tested, and composes:
game + oracle + head + memory + probes, with the value-modulation effect
significant and in the predicted direction on held-out worlds.
