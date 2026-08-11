# Red-team 4 — artifacts in the exp6 / felt result

Target: `experiments/exp6_stage1_miniature.py` + `felt/baselines.py` claim that
felt(β=12) flips the gist/detail dissociation (≈ +0.12, AP ≈ 0.707) while
surprise-only/uniform stay negative (≈ −0.12).

Probe code (all runnable):

```
cd /Users/rohing/dream-state
PYTHONHASHSEED=0 PYTHONPATH=.:research_notes/probes python3 research_notes/probes/redteam4_probes.py
PYTHONHASHSEED=0 PYTHONPATH=.:research_notes/probes python3 research_notes/probes/redteam4_followup.py
PYTHONHASHSEED=0 PYTHONPATH=.:research_notes/probes python3 research_notes/probes/redteam4_perkind.py
```

All numbers below are from `PYTHONHASHSEED=0` runs (see F4 for why that matters);
the canonical exp6 reference under that seed is: uniform −0.099, surprise_only
−0.115, felt(b=4) +0.038, felt(b=12) +0.121 / AP 0.695.

Summary verdict: **the claimed effect direction (value-modulated writes beat
surprise-only at gist retention) is real inside this tier, but the trained head
contributes nothing** — the effect is carried by a hardcoded fallback constant
and matched or beaten by several zero-training gates — **and the gist/detail
"dissociation" metric itself is invalid** because the two probe classes sit on
different cosine floors.

---

## F1 — CRITICAL: felt(β=12) is the hardcoded `step=-1` fallback, not the head

In `exp6:collect_fact_stream` (and `baselines.py:collect_stream`):

```python
s = float(sal[f.step - 1]) if 0 <= f.step - 1 < len(sal) else 0.05
```

Decor facts are emitted at `reset()` with `step=-1`, so **every decor fact gets
salience 0.05 by fallback, never touching the head**. On real trajectory steps
the head is nearly type-uniform:

| fact kind | action at fact step | head salience (mean) |
|---|---|---|
| recipe (gist) | craft | 0.854 |
| location (gist) | explore | 0.834 |
| **count (DETAIL)** | gather | **0.847** |
| decor (detail) | — (setup, fallback) | 0.050 |

The head boosts detail `count` facts exactly as hard as gist. The only thing the
"salience" vector discriminates is *on-trajectory vs episode-setup*.

Direct tests (8 seeds, `redteam4_followup.py`):

| condition | gist | det | dissoc | AP |
|---|---|---|---|---|
| felt_b12 | 0.533 | 0.412 | **+0.121** | 0.695 |
| `has_step` gate: `w = surprise·(1+12·[fact has a step])` — zero training, zero oracle | 0.545 | 0.353 | **+0.192** | 0.725 |
| felt_b12 with the 0.05 fallback replaced by the head's own mean on-step salience | 0.433 | 0.548 | **−0.114** | 0.549 |

- corr(felt_b12 weights, has_step weights) = **0.999** (min 0.998 across seeds).
- has_step beats felt: paired t = **+8.0** on dissociation.
- Neutralizing the fallback collapses felt to surprise_only (−0.115/0.549):
  paired t = **−4.8**. The entire headline effect is the fallback constant.

**The trained head is not just replaceable — removing its only hardcoded input
kills the result.**

## F2 — CRITICAL (attack 1 CONFIRMED): a keyword gate matches/beats felt, and the gate IS the label

`redteam4_probes.py`, 8 seeds, exp6 pipeline, trivial gate
`g = [action startswith craft|explore]`:

| policy | gist | det | dissoc | AP |
|---|---|---|---|---|
| felt_b12 | 0.533 | 0.412 | +0.121 | 0.695 |
| kw_gate_b12 = `surprise·(1+12g)` | 0.593 | 0.424 | **+0.169** | **0.797** |
| kw_gate_pure = `1+12g` (no surprise, no training) | 0.596 | 0.412 | **+0.184** | **0.821** |
| kind_leak = `1+12·[kind∈{recipe,location}]` (explicit label leak) | 0.596 | 0.412 | +0.184 | 0.821 |

- kw_gate_b12 − felt_b12 paired dissociation: +0.048 (t=2.1); pure gate is
  clearly better on AP (0.821 vs 0.695).
- **kw_gate_pure and kind_leak produce byte-identical results**: in this game,
  recipe facts are emitted only on `craft` steps and location facts only on
  `explore` steps, so the craft/explore keyword gate *is* the structural label
  (fact-level corr(head salience, gate) = corr(head salience, structural) =
  0.550 — the same vector). The "salience → structure" mapping is an identity
  of the environment's fact-emission code, not a discovered regularity.
- Head-vs-gate agreement: fact-level AUC(gate | head salience) = 0.947.
- The trained head is strictly *worse* than the keyword gate because the oracle
  target itself doesn't separate action types the useful way: train-set mean
  normalized TD-salience is craft 0.926, **gather 0.93**, explore 0.429, move
  0.574 — so faithful distillation necessarily boosts detail `count` facts too.

Verdict on attack 1: confirmed, and stronger than posed. The head adds nothing
beyond (in fact less than) keyword detection, and in this tier keyword
detection is label leakage by construction.

## F3 — CRITICAL (attack 2): uniform's negative dissociation is a probe-floor artifact

Mechanism found (`redteam4_probes.py` ATTACK B block + `redteam4_perkind.py`):

**(a) The two probe classes sit on different cosine floors.** Detail texts share
most of their words ("site_N looked X during episode E", "gathered raw_N at
step S of this episode"): mean pairwise cosine among detail values 0.537 vs
0.279 for gist; cosine with the stream-mean value 0.642 vs 0.214. Details are
356/448 of the write stream, so any memory trained on it outputs roughly the
detail-value centroid. Never-written controls on the uniform-trained memory:

| probe | cosine |
|---|---|
| real detail probes | 0.705 |
| **fake (never-written) detail-shaped probes** | **0.595** |
| real gist probes | 0.342 |
| fake gist-shaped probes | 0.283 |

~85% of "detail retention" is generic similarity, not retention. (Untrained
memory floor is ≈0 for both, so the floor is *learned from the class imbalance*,
which is why it doesn't show up in a fresh-memory sanity check.)

**(b) Per-kind decomposition under uniform** (`redteam4_perkind.py`):
recipe 0.585 vs fake-recipe 0.338 (real retention ≈ +0.25); **location 0.180**
(each binding is written exactly once, early — recurrence 1.0, genuinely
overwritten; drags the gist mean down); decor-probed 0.529 vs fake-decor 0.516
(true retention ≈ 0.01); **count-probed 0.706** — count fact text has *no
episode id* ("gathered raw_2 at step 7 of this episode"), so the same text
recurs across episodes (up to 24×) and is genuinely reinforced.

**(c) Probe-set composition makes it worse, not better.** `det_idx = first
len(gist) details` = 16 decor + 2 count from episodes 0–1 (last write chunk
0.39/7 vs 4.22/7 for gist) — maximally recency-disadvantaged, and detail still
"wins", because the floor difference dominates recency.

**(d) The felt flip is probe-set dependent.** Choosing the detail probes
differently (8 seeds):

| det probe set | uniform dissoc | felt_b12 dissoc |
|---|---|---|
| first N (paper's choice) | −0.099 | **+0.121** |
| random N | −0.181 | **−0.039** |
| last N | −0.208 | −0.036 |

felt's *relative* improvement over uniform survives (~+0.14 under random), but
the headline **sign flip disappears with random detail probes** — positive
dissociation only occurs when the detail probes are dominated by early decor
(the very kind the 0.05 fallback suppresses; F1 and F3 are the same coin).

Verdict on attack 2: **benchmark artifact**, with two real minor components.
The dissociation metric compares classes whose cosine floors differ by ~0.3;
it is uninterpretable without never-written matched controls. The real
retention story hiding underneath: recipes (repeated writes) genuinely
retained, one-shot locations genuinely forgotten, counts genuinely reinforced
via a text-collision bug, decor retention ≈ zero for everyone.

## F4 — HIGH: the experiment is not reproducible run-to-run (salted `hash()`)

`felt/head.py:hash_embed` uses Python's builtin `hash(w)`, which is salted per
process. Its docstring claims "Deterministic". Four unsalted runs of exp6:

| run | felt(b=12) dissoc | AP | paired felt(b4)−surprise t |
|---|---|---|---|
| 1 | +0.074 | 0.665 | 6.0 |
| 2 | +0.186 | 0.735 | 7.2 |
| 3 | **+0.003** | 0.628 | 3.3 |
| 4 | +0.158 | 0.724 | 5.9 |

The claimed +0.12 / 0.707 / t=5.9 is one draw from this distribution; the
headline dissociation ranges 0.003–0.186 across identical invocations. The
*direction* (felt > surprise_only) held in every draw observed. Fix: hash via
`hashlib` or run under `PYTHONHASHSEED`. Every seed-controlled comparison in
the repo that uses hash_embed shares this issue.

## F5 — MEDIUM (attack 5 CONFIRMED): head "transfer" = a 4-number action-type table

`redteam4_probes.py` ATTACK E: fit only the per-action-type mean of the
normalized oracle salience on train records (4 numbers: craft 0.926, gather
0.93, move 0.574, explore 0.429), predict on the same held-out episodes exp6
uses:

| predictor | all-budgets regret | corr(target) |
|---|---|---|
| trained head | 0.020 | 0.595 |
| action-type table (no embeddings, no training) | 0.024 | 0.590 |

corr(head salience, action-type prediction) on held-out episodes = **0.944**.
The head's "transfer to held-out worlds" is unremarkable: action words are
identical across worlds by construction, and hash bag-of-words makes the first
word of the action linearly dominant. regret 0.02 is not evidence of learned
content beyond the action verb.

## F6 — MEDIUM (attack 4): other trivial winners / near-winners

From the policy zoo (8 seeds, same pipeline): besides has_step (+0.192/0.725)
and kw_gate_pure (+0.184/0.821), **frequency** — `w = recurrence count of the
exact fact text`, zero training, zero oracle — gets dissoc **+0.091, AP 0.670**
vs felt's +0.121/0.695: statistically adjacent to the headline condition.
Nulls behaving as nulls: recency (−0.101), early (−0.102), short_text (−0.088),
no_digit (−0.099 — inert because every fact text contains digits).

## F7 — LOW (attack 3): write budget is matched; "surprise" is not surprise

`write_batch` renormalizes `w /= w.mean()` per chunk, so every policy injects
the same total weighted-loss mass (Σw = n per chunk, verified: 56.0 for all
policies). dmem_style's zeroing concentrates ×3.7 energy on survivors — that is
the intended meaning of "allocation at matched budget", not an artifact.
Real (small) issue: `surprise` is computed on the **fresh** memory before any
writes (exp6 `run_condition` and `baselines._weights` both call
`mem.surprise(K,V)` pre-write), so it is a static function of value geometry
vs the random init, not online novelty — its correlation with the structural
label flips sign across hash draws (+0.38 / −0.35). This is why surprise_only
≈ uniform everywhere. Calling it a "surprise" baseline overstates what was
compared against.

---

## Ranked severity

1. **F1** — the felt effect is the hardcoded `step=-1 → 0.05` fallback; head weights corr 0.999 with a "has a step index" gate; neutralizing the fallback kills the result (t=−4.8).
2. **F2** — attack 1 confirmed: craft/explore keyword gate (= the structural label, verbatim, in this environment) beats felt_b12 (AP 0.821 vs 0.695). The trained head adds negative value over keyword detection.
3. **F3** — attack 2 resolved: negative uniform dissociation is a cosine-floor artifact (fake never-written detail probes score 0.595); the felt sign-flip only exists for the decor-heavy "first N details" probe set and disappears under random detail probes.
4. **F4** — salted `hash()` makes every run a different experiment; headline dissociation spans 0.003–0.186 across reruns.
5. **F5** — attack 5 confirmed: head eval regret/corr matched by a 4-number action-type lookup table (corr with head 0.944).
6. **F6** — frequency (text recurrence count) nearly matches the headline condition with zero information.
7. **F7** — budget matching is fine; but "surprise" is pre-write static noise, so the surprise_only baseline is effectively a second uniform.

## What survives

- felt_b12 > surprise_only/uniform *within this pipeline* replicates in every
  hash draw (direction robust).
- But the mechanism is: (fallback constant ∨ action keyword) → suppress decor
  writes → decor-heavy early detail probes drop toward their (high) generic
  floor while repeated recipe writes rise above theirs. No component of the
  causal chain involves anything the head *learned*, and the metric the chain
  moves is class-floor-confounded. The Stage-1 "go signal" as evidence for
  *trained value-modulated writing* is not supported; as evidence that
  *down-weighting one fact kind changes what an MLP memory retains*, it is
  trivially true.

## Recommended fixes before the GPU tier

1. Give decor facts a real trajectory step (or score them with the head) — no fallback constants in the salience path.
2. Report never-written matched controls next to every probe class; define retention as cosine-above-matched-fake-floor.
3. Sample detail probes randomly (stratified by kind), not "first N".
4. Add episode id to count-fact text (kill cross-episode text collisions).
5. Replace `hash()` with a seeded stable hash (hashlib) in `hash_embed`.
6. Report the keyword-gate and has_step baselines in every table; the head must beat them to claim learning matters.
7. If "surprise" is meant to be online novelty, compute it against the current memory state per chunk, not the fresh init.
