# Red-team 5 — code & statistics audit of `game/` + `felt/` (+ exp6)

Audited at HEAD `1907bb5` (code state = `70b5015`, i.e. AFTER the redteam_4 fixes
landed mid-audit: md5 hash_embed, 0.05-fallback ban, online surprise, floor-corrected
probes, keyword_gate/oracle_weight). Findings below are what remains at HEAD;
overlap with redteam_4 is noted, not re-reported. All probes verified by execution
(`cd /Users/rohing/dream-state && PYTHONPATH=. python3 ...`; no PYTHONHASHSEED
pinning needed post-md5-fix). Test suites: 20/20 pass at HEAD, stable across
PYTHONHASHSEED ∈ {1, 7, 1234, unset}.

---

## F1 — HIGH: duplicate-ingredient recipes break engine/oracle agreement (negative inventory, phantom salience 15)

`gen_dag` draws the two ingredients independently (`a = prev[...]`,
`other = below[...]`, `dag.py:49-51`), so `a == b` recipes are common:
**284 in 200 seeds (~1.4 per world)**. The two sides then disagree:

- `requirements()`/`oracle_value` treat `(a, a)` as a multiset: **2 units of `a`
  needed** (correct).
- `FeltCraft._exec` craft (`engine.py:174-180`) checks
  `inventory.get(a) < 1 or inventory.get(b) < 1` — with `a == b` this passes with
  **1 unit** — then decrements the same key twice → **inventory goes to −1**.

Probe (world seed 0, recipe `c4_1 = (c3_0, c3_0)`):

```python
from game.dag import gen_dag
from game.engine import World, FeltCraft
w = World.generate("w", seed=0)
env = FeltCraft(w, max_steps=50); env.reset("c4_1", 0, known_locations=set(w.locations))
env.inventory = {"c3_0": 1}; env._V = env._value()
r = env.step("craft c4_1")
# -> success=True, inventory={'c3_0': -1, 'c4_1': 1}, V 15.0 -> 0.0, salience = 15.0
```

One illegal craft collapses V from 15 to 0 → a **salience spike of 15** enters the
trajectory (max legitimate observed spike is 5). Latent on the CPU tier only
because `_solve` over-provisions (it gathers for 2 units before crafting, so
scripted datasets never hit it — verified: 0/240 full-knowledge episodes finish
faster than V0). It goes **live at the LLM tier**: `llm_player` (or any suboptimal
agent) that issues `craft` with 1 unit gets free items, negative inventory, and
poisons the distillation targets with phantom TD spikes.

**Minimal fix** (engine, keeps oracle as-is — oracle is already correct):

```python
from collections import Counter
need = Counter(w.dag.recipes[item])
if any(self.inventory.get(i, 0) < n for i, n in need.items()):
    ...lack message...
for i, n in need.items(): self.inventory[i] -= n
```

and the same `Counter` check in `_solve`'s `craftable` filter (engine.py:266).

## F2 — HIGH: `oracle_value` is neither "exact" nor "monotone non-increasing" — and `td_salience` clipping hides it

The docstring (`dag.py:81-84`) claims "Exact remaining action-cost … monotone
non-increasing under optimal play". Three verified violations:

**(a) Explore cost charged per-raw, not per-unknown-location** (`dag.py:91-99`).
Two needed raws at the same unknown site are charged 2+2:

```python
from game.dag import CraftDAG, oracle_value
dag = CraftDAG(recipes={"c1": ("raw_0","raw_1")}, raws=("raw_0","raw_1"),
               depth_of={"raw_0":0,"raw_1":0,"c1":1})
v = oracle_value(dag, "c1", {}, {"raw_0":"s0","raw_1":"s0"}, set(), None)
# v = 8.0 ; true minimum is 4 (explore, gather, gather, craft)
```

Consequence: a single lucky explore drops V by up to 5 (observed max/p99 salience
= 5.0 across 8 worlds × all goals) — the head's target over-weights shared-site
discoveries by construction.

**(b) V increases mid-episode under the repo's own solver** — 138/240
scripted-optimal episodes, 186/240 with detour_rate=1.0 (probe: scan
`t["oracle_V"]` for increases across 20 worlds × all goals). Cause: explore/move
relocates the agent away from a still-needed site (+1 move re-charged).
`td_salience` clips these regressions to 0, so (i) the docstring's invariant is
silently false, (ii) the *recovery* step earns salience it didn't create, and
(iii) Σ salience > V0 (the test `test_salience_fires_...` asserts `>=`, i.e. it
codifies the leak rather than bounding it).

**(c) The cost model no longer matches the action set.** Since `70b5015`, `move`
works on ANY site name and reveals contents on first visit — so directed
site-scanning (1 action per chosen site) is the real discovery mechanic. The
oracle still models a flat "+2 explore" per unknown raw; the true expected
discovery cost is ~(u+1)/2 scans over unvisited sites (and 0 extra move, since the
reveal relocates you). "Exact" was already heuristic before the move change; now
the modeled action ("explore, cost 2") isn't even the optimal policy's action.

**Minimal fixes:** (1) charge explore per *distinct* unknown needed location
(collect unknown locs into a set exactly like `locs_needed` already does for
moves); (2) rewrite the docstring: V is a deterministic admissible-ish heuristic
potential, not exact remaining cost; (3) log signed TD alongside the clipped
value so oracle regressions are visible in datasets (`rec["td_raw"] = v_before -
v_after`), and add a monotonicity canary that measures — not asserts away — the
violation rate.

## F3 — HIGH: harness resume can lose everything (non-atomic `_save`) and silently mixes configs

Kill-resume *equivalence* is now exact (verified at HEAD: full run vs
kill-after-1-probe-unit + resume → byte-identical summaries, no PYTHONHASHSEED
pinning needed; the pre-md5 code failed this — under salted hash, resumed
metrics differed materially, e.g. felt_b12 dissociation 0.022 vs 0.097).
Dict ordering is not an issue (insertion-ordered, unit loop deterministic,
summary is order-insensitive means). Two real defects remain:

**(a) `_save` is not atomic** (`harness.py:64-65`, `write_text`). A kill mid-write
truncates `state.json`; resume then throws `json.JSONDecodeError` and ALL
progress (rollouts/head/probe units) is unreachable — contradicting the module
docstring "a killed run loses at most one stage-chunk". Verified by truncating
state.json to half length → resume crashes.

```python
# fix: atomic replace
tmp = self.state_path.with_suffix(".json.tmp")
tmp.write_text(json.dumps(self.state, indent=1))
os.replace(tmp, self.state_path)
```

**(b) No config-drift guard + no done-guard on `stage_probe_eval`.** The stored
`state["config"]` is never compared to the live cfg. Verified: resuming a
completed workdir with `policies=("uniform",)`, `eval_worlds=1` happily reports
`felt_b12` and `surprise_only` results from the OLD config with no warning
(`probe_eval` also re-summarizes and re-marks on every `run()` because it lacks
the `if self._done(...)` early-return the other stages have). Fix: assert
`asdict(self.cfg) == state["config"]` on load (or hash it into the workdir), and
add the done-guard.

## F4 — MEDIUM: `np.seterr(all="ignore")` at import time mutates global numpy state for every importer

`felt/head.py:20` and `felt/fastweight.py:18` run at import. Verified:
`np.geterr()` flips from `{'divide':'warn','over':'warn','invalid':'warn'}` to
all-ignore for the *entire process* — including `structmem_bench`, experiment
scripts, and any future GPU-tier code that imports `felt`. Stress testing found
nothing currently broken — fast-weight memory stays finite at T=5000/hidden=4,
weight scales 1e±8..1e-12, β=1e6, correlated keys (the `w / w.mean()`
normalization makes writes scale-free), and the head's manual gradients match
numerical gradients to ~1e-11 — but any future divergence (e.g. torch-port lr
mismatch, degenerate normalize) will now be *silent garbage* instead of a
warning. Minimal fix: delete the module-level calls; wrap only the known-spurious
matmuls in `with np.errstate(over="ignore", invalid="ignore"):`, and add a
finiteness assert in `write_batch`/`train_batch` (cheap, CPU tier).

## F5 — MEDIUM: firewall (spec §2.5) — intact at HEAD, but two soft spots

Traced every path: the head trains on `records[i]["trajectory"]` (obs/action
text) + normalized oracle TD only (`head.py:81-94`); `fact.structural` never
reaches the head or any non-declared policy; probe outcomes feed no loss.
Post-redteam_4 the salience→fact attachment is also clean: decor and location
facts are now emitted at the SAME first-visit step (shared salience — the
structural/detail pair is no longer separable by step index), and detours give
craft/gather steps within-type salience variance. The residual correlation
(structural facts cluster at high-TD steps; the action word is in the embedded
text) is legitimate environment structure, not label flow — but it is exactly the
channel a trivial detector exploits, which is why the `keyword_gate` canary
exists. Soft spots:

- **`keyword_gate` and `oracle_weight` are not in `RunConfig.policies` defaults**
  (`harness.py:45-46`) — the "PERMANENT CANARY" only runs in one test. Add both
  to the default tuple so every reported table carries its canary and ceiling.
- **`_weights` receives `structural` for every policy** (`baselines.py:140`) —
  only the declared-oracle branch uses it, but it's a one-line edit away from an
  invisible leak. Pass it only when `policy == "oracle_weight"`, or
  `assert structural is None or policy == "oracle_weight"`.
- `context_fifo` sets its budget `B = |gist|` from the label-derived gist count —
  acceptable for a declared reference row, but document it as label-informed.

## F6 — MEDIUM: head is trained on optimal rollouts but deployed on noisy ones

`stage_head` trains on `generate_dataset` traces (scripted_**optimal**_play,
`generator.py:76`), while `collect_stream` computes deployment salience on
scripted_**noisy**_play streams (detour_rate=0.25, `baselines.py:38`). The head
never sees a detour step in training, yet detours are precisely the events whose
salience is supposed to distinguish felt from the keyword gate (near-zero-TD
crafts/gathers). Also note detours are only *mostly* near-zero-TD: the detour
"psychically" moves to `w.raw_locations[raw]` even when unknown
(`engine.py:230-234` — legal under move-anywhere, but ground-truth-informed), and
when the detour raw's site is goal-needed-and-unknown that move carries salience
up to 3, contradicting the "~ZERO oracle salience" docstring. Minimal fix:
generate the head's training data with the same noisy player (or add
`detour_rate` to `generate_dataset`), and restrict detour raws to
already-known / goal-irrelevant sites.

## F7 — LOW: deprecated exp6 still misreports "held-out eps"

`exp6_stage1_miniature.py:94-97` trains on ALL `recs` then prints
`head quality (held-out eps)` for `recs[-15:]` ⊂ the training set. The file is
DEPRECATED/retracted (redteam_4) and kept for provenance, but this specific
mislabel isn't in the retraction note; add one line to the header. (Its paired
design was otherwise sound: identical K/V/S and identically-seeded memory across
conditions per seed — pairing verified. The harness inherits the correct
pattern: same `seed = c.seed*31 + w_i` and deterministic stream per (world,
seed) across policies.)

## F8 — LOW: `context_fifo` metric quirks (reference row only)

`baselines.py:117-128`: (i) `g_hit` is dead code — a single-element `np.mean`
over one `any(...)` bool, never used; delete. (ii) `gist_kept` counts structural
*instances* (duplicates included) among the last B against `n_g` — repeated
recipe facts inflate it (only bounded by 1 because B == n_g); dedupe by text
before counting. (iii) `gist_kept` and `det_kept` use different denominators
(n_g vs B) — same number here, different semantics; comment or unify.

## F9 — LOW: minor robustness / hygiene

- `_floor_corrected_probe` / detail sampling: `det_pool` empty (tiny
  `n_episodes`) → `np.stack([])` crash; guard with early return.
- `curriculum_goals` gets the same `seed` for every world in `generate_dataset`
  (`generator.py:72`) → identical goal-name sequences across worlds (item names
  are shared) — reduces stream diversity; use `seed*10007+i`-style per world.
- `World.generate` seeds its location rng and `gen_dag`'s rng from the same
  integer → deterministic correlation between recipe topology and location
  assignment; harmless now, cleaner to offset.
- Stats note: `paired_diff` uses a fixed |t| > 3 cutoff (n=8 seeds → df=7,
  ≈ p<0.02 two-sided) — conservative but undocumented; state it (or use a real
  t CDF) wherever "SIG" is printed. Test thresholds (0.7×, +0.03, <0.15) are
  empirically calibrated canaries, now deterministic post-md5 (no flake risk),
  but expect them to need recalibration whenever the engine/probe changes.

---

## Verified clean (checks that passed)

- **Firewall:** head/policies never observe `fact.structural`, benchmark labels,
  or probe outcomes (except declared `oracle_weight` ceiling).
- **`requirements()`:** shared-`have` recursion consumes inventory exactly once;
  duplicate ingredients correctly need 2 units; closure bottoms out in raws.
  V ≥ 0 always (sum of non-negatives), never NaN; goal-deeper-than-max_steps
  terminates with V > 0.
- **Engine:** craft consumes correctly for a≠b; explore rng draws are consumed
  only by explore (interleaved non-explore actions don't shift the stream);
  episode determinism holds (same world/episode_seed/known_locations/actions).
- **Cross-episode carry:** no double emission — each location fact appears
  exactly once per world in `generate_dataset(carry_locations=True)`; decor
  facts once per (episode, visited site).
- **Resume:** kill-resume == fresh run, byte-identical, at HEAD (the md5
  hash_embed fix removed the only nondeterminism; pre-fix, resumed results
  differed materially, and even repeat runs were "different experiments").
- **Numerics:** fast-weight memory finite under stress (large T, tiny hidden,
  extreme β/weight scales, correlated keys); head gradients match numerical
  differentiation to ~1e-11; `all_budgets_regret` bounded in [0,1] with guarded
  degenerate cases.
- **Tests:** 20/20 pass, stable across PYTHONHASHSEED values.

## Fix priority

1. F1 engine multiset craft (one `Counter`, blocks the LLM tier).
2. F3a atomic `_save` + F3b config guard (blocks the 48h lease story).
3. F2a per-location explore charge + F2 docstring/logging honesty (distillation
   target quality; do before the GPU head is trained on these traces).
4. F5 defaults: add `keyword_gate` + `oracle_weight` to `RunConfig.policies`;
   fence `structural` out of `_weights` for non-oracle policies.
5. F4 scoped errstate; F6 noisy training data for the head; F7–F9 as touched.
